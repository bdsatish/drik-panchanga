"""Manual ``LAT,LON,TZ`` place across the CLI and web stack."""

import unittest

from datetime_helper import format_utc_offset
from generate_panchanga_calendar import argument_parser, attach_place_values, load_custom_location, resolve_location
from webapp.app import app
from webapp.day_panchanga import compute_day_panchanga


class CustomLocationTests(unittest.TestCase):

  def test_place_wins_over_city(self):
    location = resolve_location("Bengaluru, IN", "12.97,77.59,5.5")
    self.assertEqual(location.name, "12.97N, 77.59E (UTC+5:30)")
    self.assertEqual(location.timezone_name, "UTC+5:30")
    self.assertEqual(format_utc_offset("UTC+5:30", 2026, 3), "UTC+5:30 (UTC+05:30)")
    self.assertEqual(resolve_location("Bengaluru, IN", " ").name, "Bengaluru, IN")

  def test_southern_western_place(self):
    location = resolve_location(place=" -33.87 , -70.5 , -3.5 ")
    self.assertEqual(location.name, "33.87S, 70.50W (UTC-3:30)")

  def test_custom_day_matches_equivalent_city(self):
    city = compute_day_panchanga("Bengaluru", "21/04/2023")
    custom = compute_day_panchanga("", "21/04/2023", place="12.97194,77.59369,5.5")
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

  def test_rejects_bad_place(self):
    for place in ("12.97,77.59", "1,2,3,4", "a,2,3", "95,2,3", "1,2,15", "12.97,,5.5"):
      with self.subTest(place=place), self.assertRaises(ValueError):
        resolve_location(place=place)

  def test_cli_accepts_negative_latitude(self):
    argv = attach_place_values(["--place", "-13.4,70,5.5", "--start", "2026-06"])
    arguments = argument_parser().parse_args(argv)
    self.assertEqual(resolve_location(arguments.city, arguments.place).name, "13.40S, 70.00E (UTC+5:30)")


class CustomLocationWebTests(unittest.TestCase):

  def test_day_api(self):
    response = app.test_client().get("/api/panchanga?place=12.97194,77.59369,5.5&date=21/04/2023")
    self.assertEqual(response.status_code, 200)
    data = response.get_json()
    self.assertEqual(data["timezone"], "UTC+5:30")
    self.assertEqual(data["sunrise"], compute_day_panchanga("Bengaluru", "21/04/2023")["sunrise"])

  def test_day_api_rejects_partial_input(self):
    response = app.test_client().get("/api/panchanga?place=12.97&date=21/04/2023")
    self.assertEqual(response.status_code, 400)

  def test_ics(self):
    response = app.test_client().get("/api/panchanga.ics?place=12.97,77.59,5.5&start=2026-03")
    self.assertEqual(response.status_code, 200)
    self.assertIn(b"BEGIN:VCALENDAR", response.data)

  def test_pdf(self):
    response = app.test_client().post("/generate", data={
      "place": "12.97,77.59,5.5",
      "start": "2026-03",
    })
    self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
  unittest.main()
