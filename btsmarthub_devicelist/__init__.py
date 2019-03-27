import requests
from urllib.parse import quote
import json
import math
import random
import hashlib
import logging
import re

_LOGGER = logging.getLogger(__name__)


def compute_md5hash(hashstring):
    """Return the MD5 Hash of a given string"""
    m = hashlib.md5()
    m.update(hashstring.encode('utf-8'))
    return m.hexdigest()


def update_label(source, labels):
    # sort so we do larges matches first removing issues on things like 'ip' used in longer strings
    labels.sort(key=len, reverse=True)
    for label in labels:
        source = source.replace(label + ":", "\"" + label + "\":")

    return source


DEFAULT_IP = '192.168.1.254'


class BTSmartHub(object):
    """ Represents a session to a BT SmartHub Router."""

    def __init__(self, router_ip=None, smarthub_model=None):
        """ Initialize the router and if no router model is passed, try to determine model"""

        if router_ip:
            self.router_ip = router_ip
        else:
            self.router_ip = DEFAULT_IP

        if not smarthub_model:
            self.smarthub_model = self.autodetect_smarthub_model()
        else:
            self.smarthub_model = smarthub_model

    def get_devicelist(self, only_active_devices=None):

        if only_active_devices is None:
            only_active_devices = True
        elif only_active_devices:
            only_active_devices = True
        else:
            only_active_devices = False

        if self.smarthub_model == 1:
            devicelist = self.get_devicelist_smarthub_1(only_active_devices=only_active_devices)
            return devicelist
        elif self.smarthub_model == 2:
            devicelist = self.get_devicelist_smarthub_2(only_active_devices=only_active_devices)
            return devicelist
        else:
            _LOGGER.error("Not sure which smarthub to query...")

    def get_devicelist_smarthub_1(self, only_active_devices):
        """ Query as Smarthub 1 for list of devices """

        auth_cookie_obj = {"req_id": 1,
                           "sess_id": 0,
                           "basic": False,
                           "user": "guest",
                           "dataModel": {
                               "name": "Internal",
                               "nss": [
                                   {
                                       "name": "gtw",
                                       "uri": "http://sagemcom.com/gateway-data"
                                   }
                               ]
                           },
                           "ha1": "ca6e4940afd41d8cd98f00b204e9800998ecf8427e830e7a046fd8d92ecec8e4",
                           "nonce": ""
                           }

        auth_request_obj = {
            "request": {
                "id": 0,
                "session-id": 0,
                "priority": True,
                "actions": [
                    {"id": 0,
                     "method": "logIn",
                     "parameters": {
                         "user": "guest",
                         "persistent": True,
                         "session-options": {
                             "nss": [
                                 {
                                     "name": "gtw",
                                     "uri": "http://sagemcom.com/gateway-data"
                                 }
                             ],
                             "language": "ident",
                             "context-flags": {
                                 "get-content-name": True,
                                 "local-time": True
                             },
                             "capability-depth": 2,
                             "capability-flags": {
                                 "name": True,
                                 "default-value": False,
                                 "restriction": True,
                                 "description": False
                             },
                             "time-format": "ISO_8601"
                         }
                     }
                     }
                ],
                "cnonce": 745670196,
                "auth-key": "06a19e589dc848a89675748aa2d509b3"
            }
        }

        try:
            response = requests.post("http://" + self.router_ip + "/cgi/json-req",
                                     headers={
                                         "Cookie": "lang=en; session=%s" % quote(
                                             json.dumps(auth_cookie_obj, separators=(',', ':')), safe="/~"),
                                     },
                                     data="req=%s" % quote(json.dumps(auth_request_obj, separators=(',', ':')),
                                                           safe="/~"))
        except requests.exceptions.Timeout:
            _LOGGER.exception("Connection to the router times out")
            return
        if response.status_code == 200:
            body = response.json()
        else:
            _LOGGER.error("Invalid response from Smart Hub: %s", response)

        client_nonce = math.floor(4294967295 * (random.random() % 1))
        request_id = 1
        server_nonce = body['reply']['actions'][0]['callbacks'][0]['parameters']['nonce']
        user = "guest"
        password = "d41d8cd98f00b204e9800998ecf8427e"  # MD5 of an empty string

        auth_hash = compute_md5hash(user + ":" + server_nonce + ":" + password)
        auth_key = compute_md5hash(auth_hash + ":" + str(request_id) + ":" + str(client_nonce) + ":JSON:/cgi/json-req")

        list_cookie_obj = {"req_id": request_id,
                           "sess_id": body['reply']['actions'][0]['callbacks'][0]['parameters']['id'],
                           "basic": False,
                           "user": "guest",
                           "dataModel": {
                               "name": "Internal",
                               "nss": [
                                   {
                                       "name": "gtw",
                                       "uri": "http://sagemcom.com/gateway-data"
                                   }
                               ]
                           },
                           "ha1": "2d9a6f39b6d41d8cd98f00b204e9800998ecf8427eba8d73fbd3de28879da7dd",
                           "nonce": body['reply']['actions'][0]['callbacks'][0]['parameters']['nonce']
                           }
        list_req_obj = {
            "request": {
                "id": request_id,
                "session-id": body['reply']['actions'][0]['callbacks'][0]['parameters']['id'],
                "priority": False,
                "actions": [
                    {
                        "id": 1,
                        "method": "getValue",
                        "xpath": "Device/Hosts/Hosts",
                        "options": {
                            "capability-flags": {
                                "interface": True
                            }
                        }
                    }
                ],
                "cnonce": client_nonce,
                "auth-key": auth_key
            }
        }

        try:
            device_response = requests.post("http://" + self.router_ip + "/cgi/json-req",
                                            headers={
                                                "Cookie": "lang=en; session=%s" % quote(
                                                    json.dumps(list_cookie_obj, separators=(',', ':')),
                                                    safe="/~"),
                                            },
                                            data="req=%s" % quote(json.dumps(list_req_obj, separators=(',', ':')),
                                                                  safe="/~"))
        except requests.exceptions.Timeout:
            _LOGGER.exception("Connection to the router timed out at second stage")
            return
        if device_response.status_code == 200 and only_active_devices is False:
            try:
                devicelist = device_response.json()['reply']['actions'][0]['callbacks'][0]['parameters']['value']
                return self.parse_devicelist(devicelist)
            except IndexError:
                pass
        elif device_response.status_code == 200 and only_active_devices is True:
            try:
                devicelist = device_response.json()['reply']['actions'][0]['callbacks'][0]['parameters']['value']
                return self.parse_activedevicelist(devicelist)
            except IndexError:
                pass
        else:
            _LOGGER.error("Invalid response from Smart Hub at second stage: %s", device_response)

    def get_devicelist_smarthub_2(self, only_active_devices):
        """ Query a Smarthub 2 for list of devices"""

        # Url that returns js with variable in it showing all the device status
        request_url = 'http://' + self.router_ip + '/cgi/cgi_basicMyDevice.js'

        # list of labels that the device returns in the javascript style declaration
        device_labels = [
            "mac",
            "hostname",
            "ip",
            "ipv6",
            "name",
            "activity",
            "os",
            "device",
            "time_first_seen",
            "time_last_active",
            "dhcp_option",
            "port",
            "ipv6_ll",
            "activity_ip",
            "activity_ipv6_ll",
            "activity_ipv6",
            "device_oui",
            "device_serial",
            "device_class",
            "reconnected"
        ]

        # make request to the server
        try:
            response = requests.get(request_url)
        except requests.exceptions.Timeout:
            _LOGGER.exception("Connection to the router times out")
            return
        if response.status_code == 200:
            body = response.content.decode('utf-8')
            # body strings are URI encoded
            body = requests.utils.unquote(body)
        else:
            _LOGGER.error("Invalid response from Smart Hub: %s", response)
            _LOGGER.debug("It is likely that %s is the wrong router model", str(self.smarthub_model))

        # and remove all newlines
        body = body.replace("\n", "")

        # pull out the javascript line from the whole file
        search_expression = re.search(r'known_device_list=(.+?),null', body)

        # my regexx strips the close of the list
        initial_jscript_array = search_expression.group(1) + ']'

        # to allow json to read this, add quotes around the item labels.
        initial_jscript_array = update_label(initial_jscript_array, device_labels)

        # change the strings to boolean for '0' and '1'
        initial_jscript_array = initial_jscript_array.replace("'1'", "true")
        initial_jscript_array = initial_jscript_array.replace("'0'", "false")

        # json likes double not single quotes
        cleaned_jscript_array = initial_jscript_array.replace("'", "\"")

        # map to the old field names to keep compatibility with hub v1
        cleaned_jscript_array = cleaned_jscript_array.replace("\"mac\"", "\"PhysAddress\"")
        cleaned_jscript_array = cleaned_jscript_array.replace("\"activity\"", "\"Active\"")
        cleaned_jscript_array = cleaned_jscript_array.replace("\"hostname\"", "\"UserHostName\"")
        cleaned_jscript_array = cleaned_jscript_array.replace("\"ip\"", "\"IPAddress\"")

        # read into obj model using json
        devices = json.loads(cleaned_jscript_array)

        # shrink them down
        if only_active_devices is False:
            return self.parse_devicelist(devices)
        else:
            return [device for device in devices if device.get('Active')]

    @staticmethod
    def parse_devicelist(device_list):
        """Returns relevant keys for devices in the router memory"""

        keys = {'UserHostName', 'PhysAddress', 'IPAddress', 'Active'}
        devices = [{k: v for k, v in i.items() if k in keys} for i in device_list]

        return devices

    @staticmethod
    def parse_activedevicelist(device_list):
        """Returns relevant keys for devices currently connected to the router"""

        keys = {'UserHostName', 'PhysAddress', 'IPAddress', 'Active'}
        devices = [{k: v for k, v in i.items() if k in keys} for i in device_list]
        devices = list(filter(lambda d: d['Active'] in [True], devices))
        return devices

    def autodetect_smarthub_model(self):
        """Trys to autodetect the smarthub model, beginning with smarthub 2"""

        wait_time = 1
        _LOGGER.info("Trying to determine router model at %s", self.router_ip)

        # First try to determine if router is Smarthub 2
        try:
            request_url = 'http://' + self.router_ip + '/cgi/cgi_basicMyDevice.js'
            response = requests.get(request_url, timeout=wait_time)
            response.raise_for_status()
            if response.status_code == 200:
                _LOGGER.info("Router (%s) appears to be a Smart Hub 2 ", self.router_ip)
                return 2
        # On failure, determine if router is Smarthub 1
        except (requests.exceptions.HTTPError, requests.exceptions.Timeout) as e:
            _LOGGER.debug("Router (%s) does not appear to be a Smart Hub 2", self.router_ip)
            _LOGGER.debug("Connection to the router (%s) failed because of %fs ", self.router_ip,
                          e.response.status_code)
            try:
                request_url = 'http://' + self.router_ip + '/gui/#/home/myNetwork/devices'
                response = requests.get(request_url)
                response.raise_for_status()
                if response.status_code == 200:
                    _LOGGER.info("Router (%s) appears to be a Smart Hub 1 ", self.router_ip)
                    return 1
            # I both fail, assume that router is not a Smarthub
            except requests.exceptions.HTTPError:
                _LOGGER.error("Could not autodetect Smart Hub model at %s", self.router_ip)
                _LOGGER.error("Please see the Readme for supported models")
                pass
