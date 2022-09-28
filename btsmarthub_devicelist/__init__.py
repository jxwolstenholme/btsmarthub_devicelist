import requests
from urllib.parse import quote
import json
import math
import random
import hashlib
import logging

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

        self.referer = "http://{}/basic_-_my_devices.htm".format(self.router_ip)

        if not smarthub_model:
            self.smarthub_model = self.autodetect_smarthub_model()
        else:
            self.smarthub_model = smarthub_model

    def get_devicelist(self, only_active_devices=None,include_connections=None):

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
            devicelist = self.get_devicelist_smarthub_2(only_active_devices=only_active_devices,
                                                        include_connections=include_connections)
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

    def get_body_content(self,  url_to_read):
        """
        common code to read url an return the read body
        :param url_to_read: url to load.
        :return: body content (with newlines stripped).
        """
        # make request to the server
        try:
            response = requests.get(url_to_read, headers={'Referer': self.referer})
        except requests.exceptions.Timeout:
            _LOGGER.exception("Connection to the router times out")
            return
        if response.status_code == 200:
            body = response.content.decode('utf-8')
        else:
            _LOGGER.error("Invalid response from Smart Hub: %s", response)
            _LOGGER.debug("It is likely that %s is the wrong router model", str(self.smarthub_model))

        # and remove all newlines
        body = body.replace("\n", "")

        return body

    def extract_js_variable_to_json_string(self, body, js_marker, labels):
        """ Pull out the variable we are looking for, mangle the js into json string by replacing
        labels/booleans/str types etc. Then return json string.
        :param body: content of overall js page.
        :param js_marker: variable marker to look for in form 'myvar='
        :param labels: labels to id from javascript and add quotes around
        :return: json string representing the javascript.
        """
        # search for our var start.....and grab substring out....
        start_pos = body.find(js_marker)
        end_pos = body.find(';', start_pos)
        sub_body = body[start_pos + len(js_marker):end_pos]

        # do basic js->json conversion.
        # to allow json to read this, add quotes around the item labels.
        initial_jscript_array = update_label(sub_body, labels)

        # change the strings to boolean for '0' and '1'
        initial_jscript_array = initial_jscript_array.replace("'1'", "true")
        initial_jscript_array = initial_jscript_array.replace("'0'", "false")

        # json likes double not single quotes
        cleaned_jscript_array = initial_jscript_array.replace("'", "\"")
        cleaned_jscript_array = requests.utils.unquote(cleaned_jscript_array)

        return cleaned_jscript_array

    def get_stations(self, owl_body):
        """
        Get the dict of stations (devices connected and info pertaining to how they connect)
        :param owl_body: The contents of the owl url - if not set we will look it up.
        :return: dictionary of stations mac -> station info.
        """

        # labels in the extensions jscript
        extension_labels = [
            "station_mac", "station_name", "alias_name", "station_ip",
            "parent_id", "connect_type", "link_rate", "link_rate_max",
            "mode", "signal_strength", "signal_strength_max",
            "signal_strength_min", "pid", "online",
            "last_connect", "ipv6_ip", "note", "as",
            "ldur", "lddr", "rt", "bs", "br",
            "txc", "rxc", "es", "rtc", "frc", "rc", "mrc", "it"]


        # convert to json str
        json_data = self.extract_js_variable_to_json_string(owl_body, 'owl_station=', extension_labels)

        # read into obj model using json
        stations = json.loads(json_data)

        # last item is null....remove it
        stations.pop()

        station_dictionary = {}

        for station in stations:
            station_dictionary[station.get("station_mac")] = station

        return station_dictionary


    def get_disks(self, owl_body):
        """
        Get the set of disks (extenders) and the info on the router.
        Used to figure out who is connected to what.
        :param owl_body: if not set we will read from URL.
        :return: dict of mac address -> extender name.
        """

        # labels in the extensions jscript
        extension_labels = [
            "ordering", "hw_ver", "sw_ver",
            "fw_ver", "sn", "device_mac",
            "device_name", "device_id", "device_ip",
            "device_netmask", "eth_mac", "bssid_2g", "essid_2g", "bssid_5g",
            "essid_5g", "parent_id", "child_id", "child_num",
            "sta_num", "connect_type", "connect_rssi", "model_name", "product_id",
            "node_lvid", "uptime", "connected_role", "connected_rootap", "linkrate", "node_num",
            "node_num_max", "linkmode", "sta_num_max", "cpuU", "cpuS", "cpuI", "memT", "memF", "memU", "proc_n",
            "hub_status", "fud", "type", "lsd", "ether_speed", "ether_name"]

        # convert to json str
        json_data = self.extract_js_variable_to_json_string(owl_body, 'owl_tplg=', extension_labels)

        # read into obj model using json
        disks = json.loads(json_data)

        # last item is null....remove it
        disks.pop()

        # we want to return a dictionary of mac -> name
        disk_dictionary = {}
        for disk in disks:
            disk_dictionary[disk.get("device_id")] = disk.get("device_name")

        return disk_dictionary

    def get_devicelist_smarthub_2(self, only_active_devices, include_connections):
        """
        Query a Smarthub 2 for list of devices.
        :param only_active_devices: if set, only recently active devices will be returned.
        :param include_connections: if set we additionally grab the disk/AP clients connect through.
        :return:
        """

        # Url that returns js with variable in it showing all the device status
        device_request_url = 'http://' + self.router_ip + '/cgi/cgi_basicMyDevice.js'
        body = self.get_body_content(device_request_url)

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

        # convert to json str
        cleaned_jscript_array = self.extract_js_variable_to_json_string(body, 'known_device_list=', device_labels)

        # map to the old field names to keep compatibility with hub v1
        cleaned_jscript_array = cleaned_jscript_array.replace("\"mac\"", "\"PhysAddress\"")
        cleaned_jscript_array = cleaned_jscript_array.replace("\"activity\"", "\"Active\"")
        cleaned_jscript_array = cleaned_jscript_array.replace("\"hostname\"", "\"UserHostName\"")
        cleaned_jscript_array = cleaned_jscript_array.replace("\"ip\"", "\"IPAddress\"")

        # read into obj model using json
        devices = json.loads(cleaned_jscript_array)

        # last device is null - pop it
        devices.pop()

        # # we want to add how things are connected, and the parent info of what they connect through.
        # for device in devices:
        if include_connections is True:
            # load the disks and stations...so we can enrich data.
            request_url = 'http://' + self.router_ip + '/cgi/cgi_owl.js'
            # use common method to pull body data for our url
            owl_body = self.get_body_content(request_url)
            disks = self.get_disks(owl_body)
            stations = self.get_stations(owl_body)

            for device in devices:
                device_mac = device.get("PhysAddress")
                if device_mac in stations:
                    station = stations[device_mac]
                    connection_type = station.get('connect_type')
                    parent_mac = station.get('parent_id')
                    if parent_mac in disks:
                        parent_name = disks[parent_mac]
                    else:
                        parent_name = "Unknown"
                else:
                    connection_type = "Unknown"
                    parent_mac = "Unknown"
                    parent_name = "Unknown"

                device['ConnectionType'] = connection_type
                device['ParentPhysAddress'] = parent_mac
                device['ParentName'] = parent_name

        # shrink them down
        devices = self.parse_devicelist(devices)
        if only_active_devices is True:
            return [device for device in devices if device.get('Active')]

        return devices

    @staticmethod
    def parse_devicelist(device_list):
        """Returns relevant keys for devices in the router memory"""

        keys = {'name', 'UserHostName', 'PhysAddress', 'IPAddress', 'Active',
                'ConnectionType', 'ParentPhysAddress', 'ParentName'}

        # keys = {'UserHostName', 'PhysAddress', 'IPAddress', 'Active'}
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
            response = requests.get(request_url, timeout=wait_time, headers={'Referer': self.referer})
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
