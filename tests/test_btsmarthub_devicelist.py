"""The tests for the btsmarthub devicelist."""
import unittest

from bt_smarthub_devicelist import btsmarthub_devicelist
from bt_smarthub_devicelist import btsmarthub2_devicelist


class TestBTSmartHub(unittest.TestCase):

    def test_btsmarthub2_getdevicelist(self):
    # self.asserttrue(btsmarthub2_devicelist.detect_smart_hub2('192.168.1.254', 0.5))
        connected_devices = btsmarthub_devicelist.get_devicelist('192.168.1.254', True)
        all_devices = btsmarthub_devicelist.get_devicelist('192.168.1.254', False)
        self.assertGreaterEqual(len(all_devices), len(connected_devices))

    def test_btsmarthub2_detection_google(self):
        self.assertFalse(btsmarthub2_devicelist.detect_smart_hub2('www.google.com', 0.5))

    def test_btsmarthub2_detection_google_short_timeout(self):
        self.assertFalse(btsmarthub2_devicelist.detect_smart_hub2('www.google.com', 0.001))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBTSmartHub)
    unittest.TextTestRunner(verbosity=2).run(suite)
