import requests
from urllib.parse import quote
import json
import math
import random
import hashlib
import logging
from bt_smarthub_devicelist import btsmarthub2_devicelist

_LOGGER = logging.getLogger(__name__)

# constant used for timeout on trying to detect hub type
_SMARTHUB2_WAIT_TIME=0.5

def computeMD5hash(hashstring):
    m = hashlib.md5()
    m.update(hashstring.encode('utf-8'))
    return m.hexdigest()


def get_devicelist(router_ip='192.168.1.254', only_active_devices=False, is_smarthub2=None):

    # if we are not told if this is sm1 or sm2 then do detection
    # Not happy with this as no concept of state - would be good to do this first time only
    if is_smarthub2 is None:
        is_smarthub2=btsmarthub2_devicelist.detect_smart_hub2(router_ip, _SMARTHUB2_WAIT_TIME)

    if is_smarthub2:
        return btsmarthub2_devicelist.get_devicelist_smarthub2(router_ip, only_active_devices)
    else:
        return get_devicelist_smarthub1(router_ip, only_active_devices)


def get_devicelist_smarthub1(router_ip='192.168.1.254', only_active_devices=False):
    parse_active_devices_only = only_active_devices
    authCookieObj = {"req_id": 1,
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

    authRequestObj = {
        "request":{
            "id": 0,
            "session-id": 0,
            "priority": True,
            "actions": [
                {"id": 0,
                 "method": "logIn",
                 "parameters": {
                     "user": "guest",
                     "persistent": True,
                     "session-options":{
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
        response = requests.post("http://" + router_ip + "/cgi/json-req",
                        headers = {
                            "Cookie": "lang=en; session=%s" % quote(json.dumps(authCookieObj, separators=(',',':')), safe="/~"),
                        },
                        data="req=%s" % quote(json.dumps(authRequestObj, separators=(',',':')), safe="/~"))
    except requests.exceptions.Timeout:
        _LOGGER.exception("Connection to the router times out")
        return
    if response.status_code == 200:
        body = response.json()
    else:
        _LOGGER.error("Invalid response from Smart Hub: %s", response)

    clientNonce = math.floor(4294967295 * (random.random() % 1))
    requestId = 1
    serverNonce = body['reply']['actions'][0]['callbacks'][0]['parameters']['nonce']
    user = "guest"
    password = "d41d8cd98f00b204e9800998ecf8427e" #MD5 of an empty string

    authHash = computeMD5hash(user + ":" + serverNonce + ":" + password)
    authKey = computeMD5hash(authHash + ":" + str(requestId) + ":" + str(clientNonce) + ":JSON:/cgi/json-req")


    listCookieObj = {"req_id": requestId,
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
    listReqObj = {
        "request": {
            "id": requestId,
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
            "cnonce": clientNonce,
            "auth-key": authKey
        }
    }

    try:
        deviceresponse = requests.post("http://" + router_ip + "/cgi/json-req",
                             headers={
                                 "Cookie": "lang=en; session=%s" % quote(json.dumps(listCookieObj, separators=(',', ':')),
                                                                         safe="/~"),
                             },
                             data="req=%s" % quote(json.dumps(listReqObj, separators=(',', ':')), safe="/~"))
    except requests.exceptions.Timeout:
        _LOGGER.exception("Connection to the router timed out at second stage")
        return
    if deviceresponse.status_code == 200 and parse_active_devices_only==False:
        try:
            devicelist = deviceresponse.json()['reply']['actions'][0]['callbacks'][0]['parameters']['value']
            return parse_devicelist(devicelist)
        except IndexError:
            pass
    elif deviceresponse.status_code == 200 and parse_active_devices_only==True:
        try:
            devicelist = deviceresponse.json()['reply']['actions'][0]['callbacks'][0]['parameters']['value']
            return parse_activedevicelist(devicelist)
        except IndexError:
            pass
    else:
        _LOGGER.error("Invalid response from Smart Hub at second stage: %s", deviceresponse)


def parse_devicelist(device_list):
    keys = {'UserHostName', 'PhysAddress', 'IPAddress', 'Active'}
    devices = [{k: v for k, v in i.items() if k in keys} for i in device_list]

    return devices


def parse_activedevicelist(device_list):
    keys = {'UserHostName', 'PhysAddress', 'IPAddress', 'Active'}
    devices = [{k: v for k, v in i.items() if k in keys} for i in device_list]
    devices = list(filter(lambda d:d['Active'] in [True], devices))
    return devices


