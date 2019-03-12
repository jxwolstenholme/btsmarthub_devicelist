import btsmarthub_devicelist

def test_devicelist():
    devicelist = btsmarthub_devicelist.get_devicelist(
        router_ip='192.168.1.254', only_active_devices=True
    )
    assert len(devicelist) > 0
