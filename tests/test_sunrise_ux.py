"""Tests for polar-region behaviour and moon event gaps."""

import unittest

from generate_panchanga_calendar import load_location
from webapp.day_panchanga import compute_day_panchanga, place_for_date, parse_civil_date, probe_moon_event
import panchanga


class PolarDayTests(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    cls.murmansk = load_location("Murmansk")

  def test_sunrise_falls_back_to_upper_transit_in_polar_night(self):
    """Murmansk Jan 1 has no real rise: anchor = solar noon, rise == set."""
    civil = parse_civil_date("01/01/2025")
    place = place_for_date(self.murmansk, civil)
    jd = panchanga.gregorian_to_jd(civil)
    sunrise = panchanga.sunrise(jd, place)
    sunset = panchanga.sunset(jd, place)
    self.assertEqual(sunrise[0], sunset[0])  # day length 0
    self.assertTrue(jd <= sunrise[0] < jd + 1)

  def test_sunrise_falls_back_to_lower_transit_in_midnight_sun(self):
    """Murmansk Jul 1 has no real rise: day length 24 h (anchor at solar
    midnight, sunset at the next day's lower transit)."""
    civil = parse_civil_date("01/07/2025")
    place = place_for_date(self.murmansk, civil)
    jd = panchanga.gregorian_to_jd(civil)
    sunrise = panchanga.sunrise(jd, place)
    sunset = panchanga.sunset(jd, place)
    self.assertAlmostEqual((sunset[0] - sunrise[0]) * 24, 24.0, delta=0.01)

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
