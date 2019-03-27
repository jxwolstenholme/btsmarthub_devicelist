"""The tests for the btsmarthub devicelist."""
import unittest

from btsmarthub_devicelist import BTSmartHub


class TestBTSmartHub(unittest.TestCase):

    def test_btsmarthub2_getdevicelist(self):
    # self.asserttrue(btsmarthub2_devicelist.detect_smart_hub2('192.168.1.254', 0.5))
        connected_devices = BTSmartHub(router_ip='192.168.1.254').get_devicelist(only_active_devices=True)
        all_devices = BTSmartHub(router_ip='192.168.1.254').get_devicelist(only_active_devices=False)
        self.assertGreaterEqual(len(all_devices), len(connected_devices))

    def test_btsmarthub2_detection_google(self):
        self.assertFalse(BTSmartHub(router_ip="www.google.com"))

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBTSmartHub)
    unittest.TextTestRunner(verbosity=2).run(suite)
