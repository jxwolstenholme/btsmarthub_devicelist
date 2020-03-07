"""The tests for the btsmarthub devicelist."""
import unittest
import logging

import responses
import requests

from btsmarthub_devicelist import BTSmartHub

_LOGGER = logging.getLogger(__name__)


class TestBTSmartHub(unittest.TestCase):

    # example bodies from smart hub 2 requests so we can test away from physical/network devices
    smarthubb2_cgi_owl_body = ""
    smarthubb2_cgi_basicMyDevice = ""

    @classmethod
    def setUpClass(cls):
        """ Read some faked data into body strings so we can test without a router present"""
        with open('fixtures/smarthub2/cgi_owl.js', 'r') as file:
            cls.smarthubb2_cgi_owl_body = file.read()
        with open('fixtures/smarthub2/cgi_basicMyDevice.js', 'r') as file:
            cls.smarthubb2_cgi_basicMyDevice = file.read()

    def setup_fake_smarthub2(self):
        # initialise mock - make sure smarthub 2 is ok....
        responses.add(responses.GET, 'http://smarthub2fakedrouter/cgi/cgi_basicMyDevice.js', status=200)
        responses.add(responses.GET, 'http://smarthub2fakedrouter/cgi/cgi_owl.js', body=self.smarthubb2_cgi_owl_body,
                      status=200)
        responses.add(responses.GET, 'http://smarthub2fakedrouter/cgi/cgi_basicMyDevice.js',
                      body=self.smarthubb2_cgi_basicMyDevice, status=200)

    @responses.activate
    def test_btsmarthub2_getdevicelist(self):
        self.setup_fake_smarthub2()

        connected_devices = BTSmartHub(router_ip='smarthub2fakedrouter').get_devicelist(only_active_devices=True)
        all_devices = BTSmartHub(router_ip='smarthub2fakedrouter').get_devicelist(only_active_devices=False)
        self.assertGreaterEqual(len(all_devices), len(connected_devices))

        self.assertEqual(8, len(connected_devices))
        self.assertEqual(12, len(all_devices))

        # for device in connected_devices:
        #     _LOGGER.error(
        #                   device.get("UserHostName")+"("+device.get("PhysAddress")+") on "+
        #                   device.get("IPAddress")+" via "+device.get("ConnectionType")+" through parent "+
        #                   device.get("ParentName")+"("+device.get("ParentPhysAddress")+")")

    @responses.activate
    def test_disk_dictionary(self):
        self.setup_fake_smarthub2()

        disks = BTSmartHub(router_ip='smarthub2fakedrouter').get_disks()
        # test data has 2 disks and a router.
        self.assertEqual(3, len(disks))

    @responses.activate
    def test_stations_load(self):
        self.setup_fake_smarthub2()

        stations = BTSmartHub(router_ip='smarthub2fakedrouter').get_stations()

        # test data has known count of stations...
        self.assertEqual(25, len(stations))

        # grab sone counts to test connection detection
        ether_count = 0
        g2_count = 0
        g5_count = 0

        # for key in stations:
        #     _LOGGER.error("Name "+stations[key].get("station_name")+
        #                  "("+stations[key].get("station_mac")+
        #                  ") via "+stations[key].get("connect_type")+
        #                  " ("+stations[key].get("parent_id")+")")

        for key in stations:
            if stations[key].get("connect_type") == "Ether":
                ether_count = ether_count+1
            elif stations[key].get("connect_type") == "2.4G":
                g2_count = g2_count+1
            elif stations[key].get("connect_type") == "5G":
                g5_count = g5_count+1

        self.assertEqual(8, ether_count)
        self.assertEqual(7, g2_count)
        self.assertEqual(10, g5_count)

    @responses.activate
    def test_btsmarthub2_with_mocked_smarthub2_present(self):
        self.setup_fake_smarthub2()
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
        self.assertRaises(requests.exceptions.HTTPError,
                          BTSmartHub(router_ip="www.google.com").autodetect_smarthub_model())


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBTSmartHub)
    unittest.TextTestRunner(verbosity=2).run(suite)
