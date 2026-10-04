"""IP-based city suggestion for the WebUI."""

import json
import unittest
from unittest import mock

import generate_panchanga_calendar as calendar_module
from webapp.app import app, suggest_city_for_ip


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


class SuggestCityEndpointTests(unittest.TestCase):

  def setUp(self):
    calendar_module._CITY_LOCATIONS = None

  def _success_body(self):
    return json.dumps({"success": True, "city": "Moscow", "country_code": "RU"}).encode()

  # A documentation-range RFC 5737 address (203.0.113.0/24) is not "global"
  # per ipaddress.is_global, so the tests use a real-world public IP.
  CLIENT_PUBLIC_IP = "8.8.8.8"
  PROXY_PRIVATE_IP = "172.17.0.1"

  def test_one_trusted_hop_restores_city_suggestion(self):
    """Railway/container deployments: peer is the edge proxy, XFF holds the client."""
    with mock.patch.dict("os.environ", {"PANCHANGA_TRUSTED_PROXY_HOPS": "1"}), \
         mock.patch("webapp.app.urlopen", return_value=_fake_response(self._success_body())):
      response = app.test_client().get(
        "/api/suggest-city",
        headers={"X-Forwarded-For": self.CLIENT_PUBLIC_IP},
        environ_base={"REMOTE_ADDR": self.PROXY_PRIVATE_IP},
      )
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.json, {"city": "Moscow, RU"})

  def test_default_hops_ignore_xff_and_skip_private_peer(self):
    """Without trusted hops the XFF header is ignored and the private peer yields no city."""
    with mock.patch.dict("os.environ", {"PANCHANGA_TRUSTED_PROXY_HOPS": "0"}), \
         mock.patch("webapp.app.urlopen", return_value=_fake_response(self._success_body())):
      response = app.test_client().get(
        "/api/suggest-city",
        headers={"X-Forwarded-For": self.CLIENT_PUBLIC_IP},
        environ_base={"REMOTE_ADDR": self.PROXY_PRIVATE_IP},
      )
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.json, {"city": None})


if __name__ == "__main__":
  unittest.main()
