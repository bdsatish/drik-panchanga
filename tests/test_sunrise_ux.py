"""Tests for polar / no-sunrise user-facing messages and moon event gaps."""

import unittest

from generate_panchanga_calendar import (
  classify_missing_sunrise,
  format_sunrise_unavailable_message,
  load_location,
  require_local_sunrise,
)
from webapp.day_panchanga import compute_day_panchanga, place_for_date, parse_civil_date, probe_moon_event
import panchanga


class SunriseUnavailableTests(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    cls.murmansk = load_location("Murmansk")

  def test_classifies_polar_night_and_midnight_sun(self):
    place_winter = place_for_date(self.murmansk, parse_civil_date("01/01/2025"))
    place_summer = place_for_date(self.murmansk, parse_civil_date("01/07/2025"))
    self.assertEqual(classify_missing_sunrise(2025, 1, 1, place_winter), "polar_night")
    self.assertEqual(classify_missing_sunrise(2025, 7, 1, place_summer), "polar_day")

  def test_message_mentions_polar_night(self):
    place = place_for_date(self.murmansk, parse_civil_date("01/01/2025"))
    message = format_sunrise_unavailable_message("Murmansk", 2025, 1, 1, place)
    self.assertIn("polar night", message)
    self.assertIn("01/01/2025", message)
    self.assertIn("sunrise", message.casefold())

  def test_message_mentions_midnight_sun(self):
    place = place_for_date(self.murmansk, parse_civil_date("01/07/2025"))
    message = format_sunrise_unavailable_message("Murmansk", 2025, 7, 1, place)
    self.assertIn("midnight sun", message)
    self.assertIn("01/07/2025", message)

  def test_require_local_sunrise_uses_transit_fallback(self):
    """The legacy gate no longer trips: the core sunrise() fallback always
    supplies an anchor (upper/lower transit) at circumpolar latitudes."""
    civil = parse_civil_date("01/01/2025")
    place = place_for_date(self.murmansk, civil)
    jd = panchanga.gregorian_to_jd(civil)
    sunrise = require_local_sunrise(jd, place, "Murmansk", 2025, 1, 1)
    self.assertIsNotNone(sunrise)
    self.assertTrue(jd - 1 <= sunrise[0] <= jd + 2)

  def test_day_api_serves_polar_night(self):
    """Polar night no longer errors: sunrise/sunset anchor at solar noon."""
    data = compute_day_panchanga("Murmansk", "01/01/2025")
    self.assertEqual(data["sunrise"], data["sunset"])  # day length 0
    self.assertTrue(data["tithi"])

  def test_day_api_serves_midnight_sun(self):
    """Midnight sun no longer errors: day length 24 h (sunset next midnight)."""
    data = compute_day_panchanga("Murmansk", "01/07/2025")
    self.assertTrue(data["tithi"])
    sunrise_hour = int(data["sunrise"].split(":")[0])
    sunset_hour = int(data["sunset"].split(":")[0])
    # virtual sunrise just past local midnight, virtual sunset ~24 h later
    self.assertGreaterEqual(sunrise_hour, 0)
    self.assertLess(sunrise_hour, 2)
    self.assertGreater(sunset_hour, 22)


class MoonEventGapTests(unittest.TestCase):

  def test_none_today_when_event_falls_after_midnight(self):
    data = compute_day_panchanga("Bengaluru", "21/01/2025")
    self.assertIsNone(data["moonrise"])
    self.assertEqual(data["moonrise_status"], "none_today")
    self.assertIsNotNone(data["moonset"])
    self.assertEqual(data["moonset_status"], "ok")

    data = compute_day_panchanga("Bengaluru", "06/01/2025")
    self.assertIsNotNone(data["moonrise"])
    self.assertEqual(data["moonrise_status"], "ok")
    self.assertIsNone(data["moonset"])
    self.assertEqual(data["moonset_status"], "none_today")

  def test_always_below_and_above_at_high_latitude(self):
    below = compute_day_panchanga("Murmansk", "21/03/2025")
    self.assertIsNone(below["moonrise"])
    self.assertEqual(below["moonrise_status"], "always_below")
    self.assertIsNone(below["moonset"])
    self.assertEqual(below["moonset_status"], "always_below")

    above = compute_day_panchanga("Murmansk", "01/05/2025")
    self.assertIsNone(above["moonrise"])
    self.assertEqual(above["moonrise_status"], "always_above")
    self.assertIsNone(above["moonset"])
    self.assertEqual(above["moonset_status"], "always_above")

  def test_probe_rejects_bogus_hours(self):
    location = load_location("Bengaluru")
    civil = parse_civil_date("15/01/2025")
    place = place_for_date(location, civil)
    jd = panchanga.gregorian_to_jd(civil)
    time, status = probe_moon_event(jd, place, civil, rise=True)
    self.assertEqual(status, "ok")
    self.assertRegex(time, r"^\d{2}:\d{2}:\d{2}$")
    hour = int(time.split(":")[0])
    self.assertLess(hour, 24)


if __name__ == "__main__":
  unittest.main()
