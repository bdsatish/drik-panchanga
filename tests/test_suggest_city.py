"""IP-based city suggestion for the WebUI."""

import json
import unittest
from unittest import mock

import generate_panchanga_calendar as calendar_module
from webapp.app import suggest_city_for_ip


class SuggestCityTests(unittest.TestCase):

    def setUp(self):
        calendar_module._CITY_LOCATIONS = None

    def test_private_ip(self):
        self.assertIsNone(suggest_city_for_ip("127.0.0.1"))

    def test_maps_geoip_city(self):
        body = json.dumps({
            "status": "success", "city": "Bengaluru", "countryCode": "IN",
        }).encode()
        resp = mock.MagicMock()
        resp.__enter__.return_value = resp
        resp.read.return_value = body
        with mock.patch("webapp.app.urlopen", return_value=resp):
            self.assertEqual(suggest_city_for_ip("8.8.8.8"), "Bengaluru, IN")

    def test_geoip_or_catalog_miss(self):
        body = json.dumps({"status": "fail"}).encode()
        resp = mock.MagicMock()
        resp.__enter__.return_value = resp
        resp.read.return_value = body
        with mock.patch("webapp.app.urlopen", return_value=resp):
            self.assertIsNone(suggest_city_for_ip("8.8.8.8"))


if __name__ == "__main__":
    unittest.main()
