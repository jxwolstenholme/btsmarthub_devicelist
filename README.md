# BT Smarthub Device List v.0.2.0

Python package allowing for a [BT Smart Hub or BT Smart Hub 2](https://www.productsandservices.bt.com/broadband/smart-hub/) router to be queried for devices.
The package will output either all devices stored in the router's memory or just the devices connected at present
as a list of dicts with the following keys:
  - UserHostName (Device Name)
  - PhysAddress (MAC Address)
  - IPAddress (Last Known IP of Device)
  - Active (Boolean for if the Device is Connected to the Router)
  
For use with a BT Smart Hub 2, set the smarthub_model flag to 2, for a BT Smart Hub 1 set the smarthub_model flag to 1. If you are not sure, leave the flag blank and it will attempt to determine the hub type.

Seeking PR for the following devices:

BT Smart Hub (Home Hub 6B)

### Installation
```sh
$ pip install btsmarthub_devicelist
```

### Example

```sh
from btsmarthub_devicelist import BTSmartHub
smarthub = BTSmartHub(router_ip='192.168.1.254', router_model=1)
device_list = smarthub.get_devicelist(only_active_devices=True)
print(devicelist)
```

