"""Tests for tropical fixed-star nakshatra calculations."""

import unittest
from unittest import mock

import vedic


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
