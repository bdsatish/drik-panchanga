"""Tests for tropical fixed-star nakshatra calculations."""

import unittest
from unittest import mock

import vedic
from datetime_helper import Date, gregorian_to_jd
from panchanga import Place


class TropicalFixedStarTests(unittest.TestCase):

  def setUp(self):
    vedic._tropical_nakshatra_boundaries.cache_clear()

  def tearDown(self):
    vedic._tropical_nakshatra_boundaries.cache_clear()

  def test_same_jd_reuses_fixed_star_boundaries(self):
    with mock.patch("vedic.swe.fixstar_ut", return_value=((200.0, ), None)) as lookup:
      first = vedic.tropical_long_fixed_stars(2450000.5, 25.0)
      second = vedic.tropical_long_fixed_stars(2450000.5, 30.0)

    boundaries = vedic._tropical_nakshatra_boundaries(2450000.5)
    self.assertEqual(lookup.call_count, 1)
    self.assertEqual(first, (1, 33.333333333333336))
    self.assertEqual(second, first)
    self.assertIsInstance(boundaries, tuple)
    self.assertEqual(len(boundaries), 27)
    self.assertTrue(all(isinstance(boundary, tuple) and len(boundary) == 2 for boundary in boundaries))

  def test_boundary_rule_remains_strict(self):
    with mock.patch("vedic.swe.fixstar_ut", return_value=((200.0, ), None)):
      self.assertEqual(vedic.tropical_long_fixed_stars(2450000.5, 20.0), (27, 20.0))


class FindNakshatraGargaTests(unittest.TestCase):
  """Garga unequal-spacing lookup returns 1..27 (it used to be 0-based)."""

  def test_returns_one_based_nakshatra(self):
    # Ashvini spans 0°–13°20', Rohini 33°20'–53°20' (20° wide), Revati ends 360°.
    self.assertEqual(vedic.find_nakshatra_garga(5)[0], 1)
    self.assertEqual(vedic.find_nakshatra_garga(0)[0], 1)
    self.assertEqual(vedic.find_nakshatra_garga(50)[0], 4)
    self.assertEqual(vedic.find_nakshatra_garga(350)[0], 27)

  def test_end_point_matches_containing_nakshatra(self):
    # The returned end is the first Garga end-point at or above the longitude;
    # the boundary itself belongs to the next nakshatra.
    nak, end = vedic.find_nakshatra_garga(13 + 20 / 60 - 1e-9)
    self.assertEqual((nak, end), (1, 13 + 20 / 60))
    nak, end = vedic.find_nakshatra_garga(13 + 20 / 60)
    self.assertEqual((nak, end), (2, 20.0))

  def test_seasonal_ritu_helpers_run(self):
    # ritu_names was undefined, so both helpers raised NameError.
    rit, name, offset = vedic.ritu_seasonal_simple(2026, 1)
    self.assertEqual(name, vedic.ritu_names[rit])
    self.assertEqual(rit, (1 - 1 + offset) // 2 % 6)


class TropicalNakshatraEndTests(unittest.TestCase):
  """tropical_nakshatra end times land where the Moon crosses the boundary."""

  bangalore = Place(12.972, 77.594, 5.5)
  jan1 = gregorian_to_jd(Date(2024, 1, 1))

  def setUp(self):
    vedic._tropical_nakshatra_boundaries.cache_clear()

  def assert_ends_on_boundaries(self, equal, boundary_of, days=45):
    skipped = 0
    for day in range(days):
      result = vedic.tropical_nakshatra(self.jan1 + day, self.bangalore, equal=equal)
      skipped += len(result) > 2
      for nak, end in zip(result[::2], result[1::2]):
        moon = vedic.tropical_lunar_longitude(end)
        miss = abs((moon - boundary_of(nak) + 180) % 360 - 180)
        self.assertLess(miss, 0.01, f"day {day} nakshatra {nak}")
    return skipped

  def test_garga_spacing_is_honoured(self):
    # `equal` used to be ignored, so equal=False returned equal-width results.
    skipped = self.assert_ends_on_boundaries(False, lambda nak: vedic._GARGA_END_POINTS[nak - 1] % 360)
    self.assertGreater(skipped, 0)  # exercises the skipped-nakshatra branch too

  def test_equal_spacing_ends_at_next_start(self):
    starts = dict(vedic._tropical_nakshatra_boundaries(self.jan1))
    # Equal boundaries move with precession (~0.00004°/day), well inside tolerance.
    self.assert_ends_on_boundaries(True, lambda nak: starts[nak % 27 + 1])

  def test_unequal_differs_from_equal(self):
    equal = vedic.tropical_nakshatra(self.jan1, self.bangalore)
    unequal = vedic.tropical_nakshatra(self.jan1, self.bangalore, equal=False)
    self.assertNotEqual(equal, unequal)

  def test_polar_sunrise_drift_stays_accurate(self):
    # Near the polar circles sunrise moves by far more than the old fixed
    # [rise, rise + 1] window assumed; the window now runs to the next sunrise.
    sodankyla = Place(67.42, 26.6, 2)
    for day in range(0, 365, 7):
      jd = self.jan1 + day
      vedic._tropical_nakshatra_boundaries.cache_clear()
      starts = dict(vedic._tropical_nakshatra_boundaries(jd))
      result = vedic.tropical_nakshatra(jd, sodankyla)
      for nak, end in zip(result[::2], result[1::2]):
        miss = abs((vedic.tropical_lunar_longitude(end) - starts[nak % 27 + 1] + 180) % 360 - 180)
        self.assertLess(miss, 0.01, f"day {day} nakshatra {nak}")
