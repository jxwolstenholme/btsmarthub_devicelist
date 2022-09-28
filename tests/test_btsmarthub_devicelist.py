"""The tests for the btsmarthub devicelist."""
import unittest
import logging

import responses
import requests
from responses import matchers

from btsmarthub_devicelist import BTSmartHub

_LOGGER = logging.getLogger(__name__)


class TestBTSmartHub(unittest.TestCase):

    # example bodies from smart hub 2 requests so we can test away from physical/network devices
    smarthubb2_cgi_owl_body = ""
    smarthubb2_cgi_basicMyDevice = ""

    maxDiff = None

    @classmethod
    def setUpClass(cls):
        """ Read some faked data into body strings so we can test without a router present"""
        with open('tests/fixtures/smarthub2/cgi_owl.js', 'r') as file:
            cls.smarthubb2_cgi_owl_body = file.read()
        with open('tests/fixtures/smarthub2/cgi_basicMyDevice.js', 'r') as file:
            cls.smarthubb2_cgi_basicMyDevice = file.read()

    def setup_fake_smarthub2(self):
        # initialise mock - make sure smarthub 2 is ok....
        responses.add(
            responses.GET,
            'http://smarthub2fakedrouter/cgi/cgi_basicMyDevice.js',
            status=200,
            match=[matchers.header_matcher({'Referer':
                'http://smarthub2fakedrouter/basic_-_my_devices.htm'})],
        )
        responses.add(
            responses.GET,
            'http://smarthub2fakedrouter/cgi/cgi_owl.js', 
            body=self.smarthubb2_cgi_owl_body,
            status=200,
            match=[matchers.header_matcher({'Referer':
                'http://smarthub2fakedrouter/basic_-_my_devices.htm'})],
        )
        responses.add(
            responses.GET,
            'http://smarthub2fakedrouter/cgi/cgi_basicMyDevice.js',
            body=self.smarthubb2_cgi_basicMyDevice, 
            status=200,
            match=[matchers.header_matcher({'Referer':
                'http://smarthub2fakedrouter/basic_-_my_devices.htm'})],
        )

    @responses.activate
    def test_btsmarthub2_getdevicelist__returns_correct_values(self):
        self.setup_fake_smarthub2()

        devices = BTSmartHub(router_ip='smarthub2fakedrouter').get_devicelist()

        expected = {
            'name': 'TV Panasonic Lounge ',
            'UserHostName': 'PaulGousiPadPro',
            'PhysAddress': 'DC:A4:FF:FF:FF:FF',
            'IPAddress': '10.1.8.201',
            'Active': True,
        }

        self.assertEqual(devices[0], expected)

    @responses.activate
    def test_btsmarthub2_getdevicelist__no_active_flag_returns_only_active(self):
        self.setup_fake_smarthub2()

        devices = BTSmartHub(router_ip='smarthub2fakedrouter').get_devicelist()

        for device in devices:
            self.assertTrue( device.get("Active"))


    @responses.activate
    def test_btsmarthub2_getdevicelist_no_connection_details(self):
        self.setup_fake_smarthub2()

        connected_devices = BTSmartHub(router_ip='smarthub2fakedrouter').get_devicelist(only_active_devices=True)
        all_devices = BTSmartHub(router_ip='smarthub2fakedrouter').get_devicelist(only_active_devices=False)
        self.assertGreaterEqual(len(all_devices), len(connected_devices))

        self.assertEqual(8, len(connected_devices))
        self.assertEqual(13, len(all_devices))

        # Confirm we didn't look up the addional connection information when include_connections not set
        for device in all_devices:
            self.assertTrue(None is device.get("ParentName"))
            self.assertTrue(None is device.get("ConnectionType"))
            self.assertTrue(None is device.get("ParentPhysAddress"))

    @responses.activate
    def test_btsmarthub2_getdevicelist_with_connection_details(self):
        self.setup_fake_smarthub2()

        connected_devices = BTSmartHub(router_ip='smarthub2fakedrouter').get_devicelist(only_active_devices=True,
                                                                                        include_connections=True)
        all_devices = BTSmartHub(router_ip='smarthub2fakedrouter').get_devicelist(only_active_devices=False,
                                                                                  include_connections=True)
        self.assertGreaterEqual(len(all_devices), len(connected_devices))

        self.assertEqual(8, len(connected_devices))
        self.assertEqual(13, len(all_devices))

        # client with name 'FAKEDDISKPAR' has parent disk that doesn't exist, so should be unknown.
        for device in all_devices:
            if device.get("UserHostName") == "FAKEDDISKPAR":
                self.assertEqual("Unknown", device.get("ParentName"))

        expected = {
            'name': 'TV Panasonic Lounge ',
            'UserHostName': 'PaulGousiPadPro',
            'PhysAddress': 'DC:A4:FF:FF:FF:FF',
            'IPAddress': '10.1.8.201',
            'Active': True,
            'ConnectionType': '5G',
            'ParentPhysAddress': '4C:1B:FF:FF:D9:FF',
            'ParentName': 'Living room',
        }

        self.assertEqual(all_devices[0], expected)


    @responses.activate
    def test_btsmarthub2_getdevicelist_with_connection_details_special_characters(self):
        with open('tests/fixtures/smarthub2/cgi_owl.special_chars.js', 'r') as file:
            self.smarthubb2_cgi_owl_body = file.read()
        with open('tests/fixtures/smarthub2/cgi_basicMyDevice.special_chars.js', 'r') as file:
            self.smarthubb2_cgi_basicMyDevice = file.read()
        self.setup_fake_smarthub2()

        devices = BTSmartHub(router_ip='smarthub2fakedrouter').get_devicelist(include_connections=True)

        expected = {
            'name': 'Paul\'s TV',
            'UserHostName': 'PaulGousiPadPro',
            'PhysAddress': 'DC:A4:FF:FF:FF:FF',
            'IPAddress': '10.1.8.201',
            'Active': True,
            'ConnectionType': '5G',
            'ParentPhysAddress': '4C:1B:FF:FF:D9:FF',
            'ParentName': 'Living room',
        }

        self.assertEqual(devices[0], expected)



    @responses.activate
    def test_disk_dictionary(self):
        self.setup_fake_smarthub2()

        disks = BTSmartHub(router_ip='smarthub2fakedrouter').get_disks(self.smarthubb2_cgi_owl_body)
        # test data has 2 disks and a router.
        self.assertEqual(3, len(disks))

    @responses.activate
    def test_stations_load(self):
        self.setup_fake_smarthub2()

        stations = BTSmartHub(router_ip='smarthub2fakedrouter').get_stations(self.smarthubb2_cgi_owl_body)

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
        self.assertTrue(None == BTSmartHub(router_ip="www.google.com").autodetect_smarthub_model())


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBTSmartHub)
    unittest.TextTestRunner(verbosity=2).run(suite)
