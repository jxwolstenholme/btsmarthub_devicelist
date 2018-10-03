# BT Smarthub Device List v.0.1

Python package allowing for a [BT Smart Hub](https://www.productsandservices.bt.com/broadband/smart-hub/) router to be queried for devices.
The package will output either all devices stored in the router's memory or just the devices connected at present
as a list of dicts with the following keys:
  - UserHostName (Device Name)
  - PhysAddress (MAC Address)
  - IPAddress (Last Known IP of Device)
  - Active (Boolean for if the Device is Connected to the Router)

### Installation
```sh
$ pip install bt_smarthub_devicelist
```

### Example

```sh
import bt_smarthub_devicelist
devicelist = get_devicelist(router_ip='192.168.1.254', only_active_devices=True)
print(devicelist)
```

