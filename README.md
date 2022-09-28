# BT Smarthub Device List v.0.2.3

Python package allowing for a [BT Smart Hub or BT Smart Hub 2](https://www.productsandservices.bt.com/broadband/smart-hub/) router to be queried for devices.
The package will output either all devices stored in the router's memory or just the devices connected at present
as a list of dicts with the following keys:
  - `name` (Device Name as defined on the Smart Hub ie the name you can manually edit)
  - `UserHostName` (Device Name)
  - `PhysAddress` (MAC Address)
  - `IPAddress` (Last Known IP of Device)
  - `Active` (Boolean for if the Device is Connected to the Router)
  
For use with a BT Smart Hub 2, set the smarthub_model flag to 2, for a BT Smart Hub 1 set the smarthub_model flag to 1. If you are not sure, leave the flag blank and it will attempt to determine the hub type.


If the router is a BT Smart Hub 2 and you set the include_connections flag to True then the additional keys will additionally be populated:
 - `ConnectionType` (Ether | 2G | 5G  fixed/wifi 2.4Ghz/wifi 5Ghz)
 - `ParentName` (Name of parent device is connecting through - e.g. wifi disks name)
 - `ParentPhysAddress` ( MAC Address of the parent)
 
 NB. If a device hasn't been connected for a while, is a disk or the router itself then the additional fields may be set to 'Unknown'
 
 

Seeking PR for the following devices:

BT Smart Hub (Home Hub 6B)

### Installation
```sh
$ pip install btsmarthub_devicelist
```

### Example

```sh
from btsmarthub_devicelist import BTSmartHub
smarthub = BTSmartHub(router_ip='192.168.1.254', smarthub_model=2)
device_list = smarthub.get_devicelist(only_active_devices=True, include_connections=True)
print(device_list)
```

