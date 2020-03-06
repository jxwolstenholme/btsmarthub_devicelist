"""The tests for the btsmarthub devicelist."""
import unittest
import logging

from btsmarthub_devicelist import BTSmartHub

_LOGGER = logging.getLogger(__name__)


class TestBTSmartHub(unittest.TestCase):

    def test_btsmarthub2_getdevicelist(self):
    # self.asserttrue(btsmarthub2_devicelist.detect_smart_hub2('192.168.1.254', 0.5))
        connected_devices = BTSmartHub(router_ip='192.168.1.254').get_devicelist(only_active_devices=True)
        all_devices = BTSmartHub(router_ip='192.168.1.254').get_devicelist(only_active_devices=False)
        self.assertGreaterEqual(len(all_devices), len(connected_devices))
        for device in connected_devices:
            _LOGGER.error(
                          device.get("UserHostName")+"("+device.get("PhysAddress")+") on "+
                          device.get("IPAddress")+" via "+device.get("ConnectionType")+" through parent "+
                          device.get("ParentName")+"("+device.get("ParentPhysAddress")+")")

        # for device in all_devices:
        #     _LOGGER.error(
        #                   device.get("UserHostName")+"("+device.get("PhysAddress")+") on "+
        #                   device.get("IPAddress")+" via "+device.get("ConnectionType")+" through parent "+
        #                   device.get("ParentName")+"("+device.get("ParentPhysAddress")+")")

    def test_disk_dictionary(self):
        disks = BTSmartHub(router_ip='192.168.1.254').get_disks();
        for disk in disks:
            _LOGGER.error(disk + " - " + disks[disk])

    def test_stations_load(self):
        stations=BTSmartHub(router_ip='192.168.1.254').get_stations();
        for key in stations:
            _LOGGER.error("Name "+stations[key].get("station_name")+"("+stations[key].get("station_mac")+") via "+stations[key].get("connect_type")+" ("+stations[key].get("parent_id")+")")

    def test_btsmarthub2_detection_google(self):
        self.assertFalse(BTSmartHub(router_ip="www.google.com"))



if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBTSmartHub)
    unittest.TextTestRunner(verbosity=2).run(suite)
