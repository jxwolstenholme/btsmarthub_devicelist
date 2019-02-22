import logging
import requests
import re
import json

_LOGGER = logging.getLogger(__name__)

# attempt to detect if we have a smart hub 2 router
def detect_smart_hub2( router_ip, wait_time):
    request_url = 'http://' + router_ip + '/cgi/cgi_basicMyDevice.js'
    _LOGGER.error("Scanning for home hub2 at %s", router_ip)
    try:
        response = requests.get(request_url, timeout=wait_time)
    except requests.exceptions.Timeout:
        _LOGGER.error("Connection to the router (%s) times out after %fs ", router_ip, wait_time)
        return False

    if response.status_code == 200:
        _LOGGER.error("Router (%s) appears to be a Smart Hub 2 ", router_ip)
        return True
    else:
        _LOGGER.error("Router (%s) doesn't seem to be a Smart Hub 2 ", router_ip)
        return False


# string replace to quote all the labels to make it json compliant
def update_label(source, labels):
    # sort so we do larges matches first removing issues on things like 'ip' used in longer strings
    labels.sort(key=len, reverse=True)
    for label in labels:
        source = source.replace(label + ":", "\"" + label + "\":")

    return source


# Filter down to just the same fields as the original library
def parse_devicelist(device_list):
    keys = {'UserHostName', 'PhysAddress', 'IPAddress', 'Active'}
    devices = [{k: v for k, v in i.items() if k in keys} for i in device_list]

    return devices


def get_devicelist_smarthub2(router_ip='192.168.1.254', only_active_devices=False):
    # Url that returns js with variable in it showing all the device status
    request_url = 'http://' + router_ip + '/cgi/cgi_basicMyDevice.js'

    # list of labels that the device returns in the javascript style declaration
    DEVICE_LABELS = [
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

    # and remove all newlines
    body = body.replace("\n", "")

    # pull out the javascript line from the whole file
    search_expression = re.search(r'known_device_list=(.+?),null', body);

    # my regexx strips the close of the list
    initial_jscript_array = search_expression.group(1) + ']';

    # to allow json to read this, add quotes around the item labels.
    initial_jscript_array = update_label(initial_jscript_array, DEVICE_LABELS);

    # change the strings to boolean for '0' and '1'
    initial_jscript_array = initial_jscript_array.replace("'1'", "true")
    initial_jscript_array = initial_jscript_array.replace("'0'", "false");

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
    devices = parse_devicelist(devices)

    # filter when asked
    if only_active_devices:
        return [device for device in devices if device.get('Active')]

    return devices
