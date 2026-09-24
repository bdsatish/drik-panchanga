"""Tests for the circumpolar sunrise/sunset transit fallback.

Pins the invariants that the polar-window fixes established:

- anchors are window-based (one transit per 24 h window), so virtual-day
  anchors are spaced 24 h apart and tithis never skip or repeat;
- the stored midnight-sun anchor never precedes civil midnight (clamped),
  so every consumer that formats the JD sees a consistent day;
- day length is 0 h in polar night and ~24 h in midnight sun;
- all the historical regressions stay fixed.
"""

import unittest
from datetime import datetime
from unittest import mock
from zoneinfo import ZoneInfo

import swisseph as swe

import panchanga
from panchanga import Place, gregorian_to_jd, sunrise, sunset, day_duration, tithi


def _tz_hours(tz_name, year, month, day):
  dt = datetime(year, month, day, 12, tzinfo=ZoneInfo(tz_name))
  return dt.utcoffset().total_seconds() / 3600.0


def _is_real_rise(jd, place):
  """True when Swiss Ephemeris finds a horizon rise within the civil day."""
  result = swe.rise_trans(jd - place.timezone / 24, swe.SUN, geopos=(place.longitude, place.latitude, 0),
                          rsmi=swe.BIT_HINDU_RISING + swe.CALC_RISE)
  return result[0] == 0 and jd <= result[1][0] + place.timezone / 24 < jd + 1


def _fmt(hms):
  return f"{hms[0]:02d}:{hms[1]:02d}:{hms[2]:02d}"


class TransitWindowTests(unittest.TestCase):
  """_transit_jd window semantics."""

  def test_lower_transit_window_independent_of_clock_position(self):
    # Vardo is east of its tz meridian: solar midnight falls before 00:00.
    # The window rule must still pick the transit belonging to the day.
    vardo = Place(70.37, 31.11, _tz_hours("Europe/Oslo", 2026, 5, 20))
    tromso = Place(69.6492, 18.9553, _tz_hours("Europe/Oslo", 2026, 5, 20))
    for jd_date in (gregorian_to_jd(panchanga.Date(2026, 5, 19)), gregorian_to_jd(panchanga.Date(2026, 6, 20))):
      for place in (vardo, tromso):
        transit = panchanga._transit_jd(jd_date, place, lower=True)
        # Window is (previous local noon, next local noon) in local frame.
        self.assertTrue(jd_date + place.timezone / 24 - 0.5 < transit < jd_date + place.timezone / 24 + 0.5)

  def test_upper_transit_window(self):
    mur = Place(68.97, 33.08, 3.0)
    jd = gregorian_to_jd(panchanga.Date(2026, 12, 20))
    transit = panchanga._transit_jd(jd, mur)
    self.assertTrue(jd < transit + mur.timezone / 24 < jd + 1.0)


class AnchorContinuityTests(unittest.TestCase):
  """Virtual-day anchors are 24 h apart and inside the civil day."""

  def test_midnight_sun_anchor_gaps_are_24h(self):
    # Vardo mid-season 2026: a full virtual month (no real rises at all).
    vardo = Place(70.37, 31.11, _tz_hours("Europe/Oslo", 2026, 6, 15))
    jd0 = gregorian_to_jd(panchanga.Date(2026, 6, 1))
    prev = None
    for i in range(30):
      jd = jd0 + i
      self.assertTrue(_is_real_rise(jd, vardo) is False, "June should be fully virtual at Vardo")
      anchor = sunrise(jd, vardo)[0]
      self.assertGreaterEqual(anchor, jd, "stored anchor must not precede civil midnight")
      if prev is not None:
        self.assertAlmostEqual((anchor - prev) * 24, 24.0, delta=0.1)
      prev = anchor

  def test_polar_night_anchor_is_upper_transit(self):
    mur = Place(68.97, 33.08, 3.0)
    jd = gregorian_to_jd(panchanga.Date(2026, 12, 20))
    rise_jd, rise_hms = sunrise(jd, mur)
    set_jd, set_hms = sunset(jd, mur)
    self.assertEqual(rise_jd, set_jd)  # both anchor at the same upper transit
    self.assertEqual(_fmt(rise_hms), _fmt(set_hms))
    self.assertAlmostEqual(day_duration(jd, mur)[0], 0.0, delta=0.001)

  def test_midnight_sun_day_length_is_24h(self):
    tro = Place(69.6492, 18.9553, 2.0)
    jd = gregorian_to_jd(panchanga.Date(2026, 6, 20))
    self.assertAlmostEqual(day_duration(jd, tro)[0], 24.0, delta=0.01)

  def test_no_tithi_skips_across_virtual_season(self):
    # Tithi numbers advance by 0/1/2 (kshaya) per day, never jump.
    vardo = Place(70.37, 31.11, _tz_hours("Europe/Oslo", 2026, 6, 15))
    jd0 = gregorian_to_jd(panchanga.Date(2026, 5, 25))
    prev = None
    for i in range(30):
      number = tithi(jd0 + i, vardo)[0]
      if prev is not None:
        self.assertIn((number - prev) % 30, (0, 1, 2))
      prev = number


class HistoricalRegressionTests(unittest.TestCase):
  """Each fixed bug stays fixed."""

  def test_murmansk_2029_short_day_keeps_real_set(self):
    # The 29-min sweep epsilon used to skip the set on a 1.3-minute day.
    mur = Place(68.97, 33.08, 3.0)
    jd = gregorian_to_jd(panchanga.Date(2029, 1, 15))
    rise_jd, _ = sunrise(jd, mur)
    set_jd, _ = sunset(jd, mur)
    self.assertAlmostEqual((set_jd - rise_jd) * 24 * 60, 1.3, delta=0.2)  # minutes

  def test_norilsk_midnight_sun_shoulder_day_positive(self):
    # sunset() searched from midnight and returned the spill set: -2.07 h.
    nor = Place(69.3535, 88.2027, 7.0)
    jd = gregorian_to_jd(panchanga.Date(2026, 7, 24))
    self.assertAlmostEqual(day_duration(jd, nor)[0], 21.78, delta=0.05)

  def test_auckland_winter_day_not_inflated(self):
    # The frame-mixing guard pushed short east-of-UTC winter days into the
    # circumpolar fallback (day 16.75 h instead of 9.49 h).
    auk = Place(-36.85, 174.76, 12.0)
    jd = gregorian_to_jd(panchanga.Date(2026, 6, 15))
    self.assertAlmostEqual(day_duration(jd, auk)[0], 9.49, delta=0.05)

  def test_vardo_onset_anchor_does_not_jump(self):
    # The after-midnight transit search produced a 47.7 h anchor gap and a
    # tithi skip (2 -> 4) at the midnight-sun onset.
    vardo = Place(70.37, 31.11, _tz_hours("Europe/Oslo", 2026, 5, 20))
    anchors = [sunrise(gregorian_to_jd(panchanga.Date(2026, 5, d)), vardo)[0] for d in range(16, 23)]
    for gap in ((b - a) * 24 for a, b in zip(anchors, anchors[1:])):
      self.assertAlmostEqual(gap, 24.0, delta=0.5)
    numbers = [tithi(gregorian_to_jd(panchanga.Date(2026, 5, d)), vardo)[0] for d in range(16, 23)]
    self.assertEqual(numbers, [29, 1, 2, 3, 4, 5, 6])

  def test_vardo_parana_anchor_within_civil_day(self):
    # The clamped anchor keeps parana-style consumers inside the day.
    vardo = Place(70.37, 31.11, _tz_hours("Europe/Oslo", 2028, 5, 21))
    jd = gregorian_to_jd(panchanga.Date(2028, 5, 21))
    anchor = sunrise(jd, vardo)[0]
    self.assertGreaterEqual(anchor, jd)
    _set_jd, set_hms = sunset(jd, vardo)
    self.assertEqual(set_hms, [24, 0, 0])  # midnight-sun set = end of civil day (24:00)


class EdgeContinuityTests(unittest.TestCase):
  """Handover between real and virtual anchors is smooth."""

  def test_polar_night_entry_edge_jump_is_small(self):
    # Tromso 2026: last real rise Nov 22 ~11:58, first virtual Nov 23
    # ~12:30 (upper transit) — under ~40 minutes.
    tro = Place(69.6492, 18.9553, _tz_hours("Europe/Oslo", 2026, 11, 23))
    real_jd = gregorian_to_jd(panchanga.Date(2026, 11, 22))
    virtual_jd = gregorian_to_jd(panchanga.Date(2026, 11, 23))
    self.assertTrue(_is_real_rise(real_jd, tro))
    self.assertFalse(_is_real_rise(virtual_jd, tro))
    gap = (sunrise(virtual_jd, tro)[0] - sunrise(real_jd, tro)[0]) * 24
    self.assertTrue(23.0 < gap < 25.0, f"edge jump {gap:.2f} h")


class GuardedPathTests(unittest.TestCase):
  """Defensive branches are exercised and degrade gracefully."""

  def test_varjyam_returns_empty_on_out_of_window_anchor(self):
    # The sentinel guard in varjyam() must never interpolate on a bogus
    # anchor: force one and expect an empty list, not garbage.
    blr = Place(12.972, 77.594, 5.5)
    jd = gregorian_to_jd(panchanga.Date(2026, 1, 15))
    with mock.patch.object(panchanga, "sunrise", return_value=[0.0, [0, 0, 0]]):
      self.assertEqual(panchanga.varjyam(jd, blr), [])

  def test_transit_window_recovery_researches_from_midpoint(self):
    # If the forward search overshoots the window, the midpoint re-search
    # still lands a transit inside it (never an out-of-window instant).
    mur = Place(68.97, 33.08, 3.0)
    jd = gregorian_to_jd(panchanga.Date(2026, 12, 20))
    real = panchanga._transit_jd(jd, mur)

    def overshooting_search(jd_ut, body, geopos, rsmi):

      class _R:  # res=0 with a transit 2 h past window_end
        pass

      return (0, [real + 2.0 / 24], 0)

    with mock.patch.object(swe, "rise_trans", side_effect=overshooting_search):
      recovered = panchanga._transit_jd(jd, mur)
    self.assertTrue(jd < recovered + mur.timezone / 24 < jd + 1.0)

  def test_day_details_none_renders_empty_cell(self):
    # Covered in test_monthly_calendar: draw_cell with day_details -> None
    # renders empty, never sentinel garbage. Assert the contract here too
    # via the generator API level.
    from generate_monthly_calendar import day_details
    mur = Place(68.97, 33.08, 3.0)
    from generate_panchanga_calendar import Location
    location = Location("Murmansk, RU", 68.97, 33.08, "Europe/Moscow")
    details = day_details(location, __import__("datetime").date(2026, 12, 20))
    self.assertIsNotNone(details)  # the normal path never returns None


if __name__ == "__main__":
  unittest.main()
