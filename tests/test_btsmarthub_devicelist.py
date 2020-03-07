"""The tests for the btsmarthub devicelist."""
import unittest
import logging

import responses
import requests

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


    def test_disk_dictionary(self):
        disks = BTSmartHub(router_ip='192.168.1.254').get_disks();
        for disk in disks:
            _LOGGER.error(disk + " - " + disks[disk])

    def test_stations_load(self):
        stations=BTSmartHub(router_ip='192.168.1.254').get_stations();
        for key in stations:
            _LOGGER.error("Name "+stations[key].get("station_name")+"("+stations[key].get("station_mac")+") via "+stations[key].get("connect_type")+" ("+stations[key].get("parent_id")+")")

    @responses.activate
    def test_btsmarthub2_with_mocked_smarthub2_present(self):
        # initialise mock - make sure smarthub 2 is ok....
        responses.add(responses.GET, 'http://smarthub2fakedrouter/cgi/cgi_basicMyDevice.js', status=200)
        # initialise mock - make sure smarthub 2 fails
        responses.add(responses.GET, 'http://smarthub2fakedrouter/gui/#/home/myNetwork/devices', status=400)

        self.assertTrue(2 == BTSmartHub(router_ip="smarthub2fakedrouter").autodetect_smarthub_model())

    @responses.activate
    def test_btsmarthub1_with_mocked_smarthub1_present(self):
        # initialise mock - make sure smarthub 2 fails....
        responses.add(responses.GET, 'http://smarthub1fakedrouter/cgi/cgi_basicMyDevice.js', status=400)
        # initialise mock - make sure smarthub 1 doesn't fail
        responses.add(responses.GET, 'http://smarthub1fakedrouter/gui/#/home/myNetwork/devices', status=200)

        self.assertTrue(1 == BTSmartHub(router_ip="smarthub1fakedrouter").autodetect_smarthub_model())


    def test_btsmarthub2_detection_neither_router_present(self):
       self.assertRaises(requests.exceptions.HTTPError, BTSmartHub(router_ip="www.google.com").autodetect_smarthub_model())



if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBTSmartHub)
    unittest.TextTestRunner(verbosity=2).run(suite)
