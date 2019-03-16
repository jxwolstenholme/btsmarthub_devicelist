# BT Smarthub Device List v.0.1.4

Python package allowing for a [BT Smart Hub or BT Smart Hub 2](https://www.productsandservices.bt.com/broadband/smart-hub/) router to be queried for devices.
The package will output either all devices stored in the router's memory or just the devices connected at present
as a list of dicts with the following keys:
  - UserHostName (Device Name)
  - PhysAddress (MAC Address)
  - IPAddress (Last Known IP of Device)
  - Active (Boolean for if the Device is Connected to the Router)

For use with BT Smart Hub 2 set the is_smart_hub2 flag to True, for a Smart Hub 1 set the flag as False. If you are not sure, leave the flag blank and it will attempt to determine the hub type.

### Installation
```sh
$ pip install btsmarthub_devicelist
```

### Example

```sh
import btsmarthub_devicelist
devicelist = btsmarthub_devicelist.get_devicelist(
    router_ip='192.168.1.254',
    only_active_devices=True,
    is_smarthub2=None,
)

print(devicelist)
```

