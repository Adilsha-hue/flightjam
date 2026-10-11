import unittest
from bench_check import parse, summarize

class CaptureTests(unittest.TestCase):
    def test_valid_rx(self):
        e=parse("RX,OK,2,3,lat_e7=-123,lon_e7=456,alt_mm=100,rssi=-88.5")
        self.assertEqual((e["boot"],e["lat_e7"],e["rssi"]),(2,-123,-88.5))
    def test_truncated_line_is_not_success(self):
        self.assertEqual(parse("RX,OK,2,3,lat_e7=123")["kind"],"other")
    def test_delivery_excludes_failed_transmits_and_unmatched_receives(self):
        rx="RX,OK,1,1,lat_e7=1,lon_e7=2,alt_mm=3,rssi=-70"
        result=summarize([parse("TX,1,1,0"),parse("TX,1,2,-1"),parse(rx),parse(rx),parse(rx.replace(",1,1,",",1,9,"))])
        self.assertEqual(result["observed_delivery_percent"],100)
        self.assertEqual(result["matched"],1)
        self.assertEqual(result["tx_errors"],1)
        self.assertEqual(result["rx_duplicate_logs"],1)
    def test_no_transmitter_observations(self):
        self.assertIsNone(summarize([])["observed_delivery_percent"])

if __name__ == "__main__":
    unittest.main()
