"""IP-based city suggestion for the WebUI."""

import json
import unittest
from unittest import mock

import generate_panchanga_calendar as calendar_module
from webapp.app import suggest_city_for_ip


def _fake_response(body):
  resp = mock.MagicMock()
  resp.__enter__.return_value = resp
  resp.read.return_value = body
  return resp


class SuggestCityTests(unittest.TestCase):

  def setUp(self):
    calendar_module._CITY_LOCATIONS = None

  def test_private_ip(self):
    self.assertIsNone(suggest_city_for_ip("127.0.0.1"))

  def test_maps_geoip_city(self):
    body = json.dumps({
      "success": True,
      "city": "Bengaluru",
      "country_code": "IN",
    }).encode()
    with mock.patch("webapp.app.urlopen", return_value=_fake_response(body)):
      self.assertEqual(suggest_city_for_ip("8.8.8.8"), "Bengaluru, IN")

  def test_geoip_or_catalog_miss(self):
    body = json.dumps({"success": False}).encode()
    with mock.patch("webapp.app.urlopen", return_value=_fake_response(body)):
      self.assertIsNone(suggest_city_for_ip("8.8.8.8"))


if __name__ == "__main__":
  unittest.main()
