"""Manual latitude/longitude/timezone floats across the web stack."""

import unittest

from generate_panchanga_calendar import (
  format_utc_offset,
  load_custom_location,
  resolve_location,
)
from webapp.app import app
from webapp.day_panchanga import compute_day_panchanga


class CustomLocationTests(unittest.TestCase):

  def test_manual_wins_over_city(self):
    location = resolve_location("Bengaluru, IN", "12.97", "77.59", "5.5")
    self.assertEqual(location.name, "12.97N, 77.59E (UTC+5:30)")
    self.assertEqual(location.timezone_name, "UTC+5:30")
    self.assertEqual(format_utc_offset("UTC+5:30", 2026, 3), "UTC+5:30 (UTC+05:30)")

  def test_custom_day_matches_equivalent_city(self):
    city = compute_day_panchanga("Bengaluru", "21/04/2023")
    custom = compute_day_panchanga("", "21/04/2023", latitude="12.97194", longitude="77.59369", timezone="5.5")
    self.assertEqual(custom["timezone"], "UTC+5:30")
    self.assertEqual(custom["sunrise"], city["sunrise"])
    self.assertEqual([seg["name"] for seg in custom["tithi"]], [seg["name"] for seg in city["tithi"]])

  def test_rejects_bad_floats(self):
    for fields in ({
        "latitude": "abc"
    }, {
        "longitude": "200"
    }, {
        "timezone": "15"
    }, {
        "latitude": "12.97",
        "longitude": "77.59",
        "start": "2026-03"
    }):
      with self.subTest(fields=fields), self.assertRaises(ValueError):
        load_custom_location(fields.get("latitude"), fields.get("longitude"), fields.get("timezone"))
    with self.assertRaisesRegex(ValueError, "City is required"):
      compute_day_panchanga("", "21/04/2023")


class CustomLocationWebTests(unittest.TestCase):

  def test_day_api(self):
    response = app.test_client().get("/api/panchanga?latitude=12.97194&longitude=77.59369"
                                     "&timezone=5.5&date=21/04/2023")
    self.assertEqual(response.status_code, 200)
    data = response.get_json()
    self.assertEqual(data["timezone"], "UTC+5:30")
    self.assertEqual(data["sunrise"], compute_day_panchanga("Bengaluru", "21/04/2023")["sunrise"])

  def test_day_api_rejects_partial_input(self):
    response = app.test_client().get("/api/panchanga?latitude=12.97&date=21/04/2023")
    self.assertEqual(response.status_code, 400)

  def test_ics(self):
    response = app.test_client().get("/api/panchanga.ics?latitude=12.97&longitude=77.59"
                                     "&timezone=5.5&start=2026-03")
    self.assertEqual(response.status_code, 200)
    self.assertIn(b"BEGIN:VCALENDAR", response.data)

  def test_pdf(self):
    response = app.test_client().post(
      "/generate", data={
        "latitude": "12.97",
        "longitude": "77.59",
        "timezone": "5.5",
        "start": "2026-03",
      })
    self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
  unittest.main()
