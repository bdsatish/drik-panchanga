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
