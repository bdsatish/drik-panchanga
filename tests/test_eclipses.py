"""Unit tests for locally visible eclipse discovery."""

import unittest
from unittest import mock

import panchanga

from datetime_helper import (Date, format_hms, format_local_hm, gregorian_to_jd, hindu_day_civil,
                             jd_to_local_civil_date, utc_offset_hours)
from festival_rules import hindu_day_has_eclipse, find_local_eclipses
from generate_panchanga_calendar import eclipse_civil_dates, format_eclipse_line, load_location, place_for_date


def _wall_jd(year, month, day, hour, minute, second=0, timezone_name="Asia/Kolkata"):
  """UT Julian day of a wall-clock reading (replaces datetime-built JDs in tests)."""
  civil = Date(year, month, day)
  return gregorian_to_jd(civil) + (hour + minute / 60 + second / 3600 - utc_offset_hours(timezone_name, civil)) / 24


def _times(maximum):
  times = [0.0] * 10
  times[0] = maximum
  return tuple(times)


class FindLocalEclipsesTests(unittest.TestCase):
  geopos = (77.6, 13.0, 0.0)

  def test_purely_penumbral_lunar_is_omitted(self):
    with mock.patch(
        "festival_rules.panchanga.swe.lun_eclipse_when_loc", side_effect=[
          (panchanga.swe.ECL_PENUMBRAL | panchanga.swe.ECL_VISIBLE, _times(10.5), None),
          (0, _times(100.0), None),
        ]), mock.patch("festival_rules.panchanga.swe.sol_eclipse_when_loc", return_value=(0, _times(100.0), None)):
      self.assertEqual(find_local_eclipses(10.0, 11.0, self.geopos), [])

  def test_invisible_partial_is_omitted(self):
    with mock.patch("festival_rules.panchanga.swe.lun_eclipse_when_loc", side_effect=[
      (panchanga.swe.ECL_PARTIAL, _times(10.5), None),
      (0, _times(100.0), None),
    ]), mock.patch("festival_rules.panchanga.swe.sol_eclipse_when_loc", return_value=(0, _times(100.0), None)):
      self.assertEqual(find_local_eclipses(10.0, 11.0, self.geopos), [])

  def test_partial_lunar_is_included_without_max_visible(self):
    # Helsinki-style: visible contacts, but maximum may fall at moonset.
    flags = panchanga.swe.ECL_PARTIAL | panchanga.swe.ECL_VISIBLE
    self.assertFalse(flags & panchanga.swe.ECL_MAX_VISIBLE)
    with mock.patch("festival_rules.panchanga.swe.lun_eclipse_when_loc", side_effect=[
      (flags, _times(10.5), None),
      (0, _times(100.0), None),
    ]), mock.patch("festival_rules.panchanga.swe.sol_eclipse_when_loc", return_value=(0, _times(100.0), None)):
      self.assertEqual(find_local_eclipses(10.0, 11.0, self.geopos), [("Lunar", "Partial", 10.5)])

  def test_total_and_annular_solar_phases(self):
    with mock.patch("festival_rules.panchanga.swe.lun_eclipse_when_loc",
                    return_value=(0, _times(100.0), None)), mock.patch(
                      "festival_rules.panchanga.swe.sol_eclipse_when_loc", side_effect=[
                        (panchanga.swe.ECL_TOTAL | panchanga.swe.ECL_VISIBLE, _times(10.4), None),
                        (panchanga.swe.ECL_ANNULAR | panchanga.swe.ECL_VISIBLE, _times(20.4), None),
                        (0, _times(100.0), None),
                      ]):
      self.assertEqual(find_local_eclipses(10.0, 21.0, self.geopos), [
        ("Solar", "Total", 10.4),
        ("Solar", "Annular", 20.4),
      ])

  def test_event_outside_range_is_omitted(self):
    with mock.patch(
        "festival_rules.panchanga.swe.lun_eclipse_when_loc", side_effect=[
          (panchanga.swe.ECL_PARTIAL | panchanga.swe.ECL_VISIBLE, _times(12.5), None),
          (0, _times(100.0), None),
        ]), mock.patch("festival_rules.panchanga.swe.sol_eclipse_when_loc", return_value=(0, _times(100.0), None)):
      self.assertEqual(find_local_eclipses(10.0, 11.0, self.geopos), [])

  def test_search_continues_after_skipped_penumbral(self):
    # Helsinki 2025-03 style: a tiny search step re-returns the same
    # penumbral maximum and used to stall before later eclipses.
    lun_finder = lambda search_jd, _geopos: (
      (panchanga.swe.ECL_PENUMBRAL | panchanga.swe.ECL_VISIBLE, _times(10.5), None)
      if search_jd < 11.0 else (panchanga.swe.ECL_PARTIAL | panchanga.swe.ECL_VISIBLE, _times(20.5), None)
      if search_jd < 21.0 else (0, _times(100.0), None))

    with mock.patch("festival_rules.panchanga.swe.lun_eclipse_when_loc", side_effect=lun_finder), mock.patch(
        "festival_rules.panchanga.swe.sol_eclipse_when_loc", return_value=(0, _times(100.0), None)):
      self.assertEqual(find_local_eclipses(10.0, 21.0, self.geopos), [("Lunar", "Partial", 20.5)])


class FormatEclipseLineTests(unittest.TestCase):

  def test_none_when_empty(self):
    self.assertEqual(format_eclipse_line([], "Asia/Kolkata"), "Eclipses: None")

  def test_formats_local_civil_dates_and_maximum_time(self):
    maximum = _wall_jd(2026, 3, 3, 10, 0)
    line = format_eclipse_line([("Lunar", "Partial", maximum)], "Asia/Kolkata")
    self.assertEqual(
      line,
      "Eclipses: Lunar Mar 03 (Partial) maximum phase at 10:00. "
      "Eclipses have a brown wavy underline below Tithi.",
    )
    self.assertEqual(jd_to_local_civil_date(maximum, "Asia/Kolkata"), Date(2026, 3, 3))

  def test_includes_sunrise_when_provided(self):
    maximum = _wall_jd(2026, 3, 3, 10, 0)
    sunrise = _wall_jd(2026, 3, 3, 6, 45)
    line = format_eclipse_line([("Lunar", "Partial", maximum)], "Asia/Kolkata",
                               sunrise_by_date={Date(2026, 3, 3): sunrise})
    self.assertEqual(
      line,
      "Eclipses: Lunar Mar 03 (Partial) maximum phase at 10:00, sunrise 06:45. "
      "Eclipses have a brown wavy underline below Tithi.",
    )

  def test_pre_sunrise_maximum_uses_24_plus_on_previous_civil_day(self):
    # 00:05 on Mar 4 is still the previous Hindu day when sunrise is 06:30.
    maximum = _wall_jd(2026, 3, 4, 0, 5)
    sunrise = _wall_jd(2026, 3, 4, 6, 30)
    line = format_eclipse_line([("Lunar", "Partial", maximum)], "Asia/Kolkata",
                               sunrise_by_date={Date(2026, 3, 4): sunrise})
    self.assertEqual(
      line,
      "Eclipses: Lunar Mar 03 (Partial) maximum phase at 24:05, sunrise 06:30. "
      "Eclipses have a brown wavy underline below Tithi.",
    )


class FormatLocalHmTests(unittest.TestCase):
  """``format_local_hm`` rounds to the nearest minute, without wrapping 24:00.

  Hours are past the anchor civil midnight (default: event's own civil day).
  With a previous-day anchor (Hindu-day pre-sunrise), ``00:05`` becomes ``24:05``.
  """

  TZ = "Asia/Kolkata"

  def _jd(self, hour, minute, second=0, day=3):
    return _wall_jd(2026, 3, day, hour, minute, second, self.TZ)

  def test_truncates_below_half_minute(self):
    self.assertEqual(format_local_hm(self._jd(23, 59, 29), self.TZ), "23:59")

  def test_ordinary_times(self):
    self.assertEqual(format_local_hm(self._jd(6, 45), self.TZ), "06:45")
    # Default anchor = event civil day: early morning stays 00:xx.
    self.assertEqual(format_local_hm(self._jd(0, 5), self.TZ), "00:05")

  def test_anchor_civil_past_midnight_is_24_plus(self):
    jd = self._jd(0, 5, day=4)
    # Hours past Mar 3 midnight -> 24:05 (Hindu-day scale).
    self.assertEqual(format_local_hm(jd, self.TZ, anchor_civil=Date(2026, 3, 3)), "24:05")
    self.assertEqual(format_local_hm(jd, self.TZ, anchor_civil=Date(2026, 3, 4)), "00:05")

  def test_hindu_day_civil_rolls_before_sunrise(self):
    jd = self._jd(0, 5, day=4)
    sunrise = self._jd(6, 30, day=4)
    self.assertEqual(hindu_day_civil(jd, self.TZ, sunrise), Date(2026, 3, 3))
    self.assertEqual(hindu_day_civil(sunrise, self.TZ, sunrise), Date(2026, 3, 4))
    self.assertEqual(format_local_hm(jd, self.TZ, anchor_civil=hindu_day_civil(jd, self.TZ, sunrise)), "24:05")

  def test_rounds_up_to_24_00_not_00_00(self):
    # Regression: a modulo by 24h used to wrap 23:59:30+ back to 00:00, which
    # contradicted the documented hours-past-midnight convention and read as
    # the start of a day rather than the end of the current one.
    self.assertEqual(format_local_hm(self._jd(23, 59, 30), self.TZ), "24:00")
    self.assertEqual(format_local_hm(self._jd(23, 59, 50), self.TZ), "24:00")
    self.assertEqual(format_local_hm(self._jd(23, 59, 59), self.TZ), "24:00")

  def test_never_exceeds_24_00_on_event_civil_day(self):
    # With the default event-day anchor, hour is 0-23 so the largest rounded
    # value is 24:00.
    for second in (0, 30, 59):
      with self.subTest(second=second):
        hours, minutes = format_local_hm(self._jd(23, 59, second), self.TZ).split(":")
        self.assertLessEqual(int(hours), 24)
        if int(hours) == 24:
          self.assertEqual(int(minutes), 0)

  def test_24_00_keeps_the_current_civil_date(self):
    # The date label beside this time must stay on the event's own civil day.
    jd = self._jd(23, 59, 50)
    self.assertEqual(format_local_hm(jd, self.TZ), "24:00")
    self.assertEqual(jd_to_local_civil_date(jd, self.TZ), Date(2026, 3, 3))


class DstRowTailTests(unittest.TestCase):
  """A UT instant on a DST-spanning row reads the offset in force at that instant.

  The row keeps its civil date's 24:00+ scale (``anchor_civil``); only the
  offset changes after the transition.
  """

  HELSINKI = "Europe/Helsinki"

  def _read(self, ut_hours_past_jd, anchor):
    anchor_date = Date(*anchor)
    return format_local_hm(
      gregorian_to_jd(anchor_date) + ut_hours_past_jd / 24, self.HELSINKI, anchor_civil=anchor_date)

  def test_tail_after_dst_start_reads_the_new_offset(self):
    # 28 Mar 2026 row, event at 02:17 UT on the 29th (after the 03:00
    # EET->EEST change): the day's +2 would read 28:17, the clock says 29:17.
    self.assertEqual(self._read(26 + 17 / 60, (2026, 3, 28)), "29:17")

  def test_tail_after_dst_end_reads_the_new_offset(self):
    # 24 Oct 2026 row, event at 04:05 UT on the 25th (after the 04:00
    # EEST->EET change): the day's +3 would read 31:05, the clock says 30:05.
    self.assertEqual(self._read(28 + 5 / 60, (2026, 10, 24)), "30:05")

  def test_tail_before_the_change_keeps_the_old_reading(self):
    # Same row, event at 22:15 UT on the 28th: no transition in between, so
    # the day's +2 applies (24:15).
    self.assertEqual(self._read(22 + 15 / 60, (2026, 3, 28)), format_hms(22 + 15 / 60 + 2.0))
    self.assertEqual(self._read(22 + 15 / 60, (2026, 3, 28)), "24:15")

  def test_bce_instant_uses_the_year_4_offset(self):
    # datetime cannot hold year -500; the year-4 tzdb era applies, where the
    # offset is the observer's longitude/15 (Ujjain meridian), not the seat's LMT.
    kolkata = "Asia/Kolkata"
    early = Date(-500, 1, 30)
    ujjain_longitude = 75.7864
    offset = utc_offset_hours(kolkata, Date(4, 1, 30), longitude=ujjain_longitude)
    jd = gregorian_to_jd(early)
    self.assertEqual(format_local_hm(jd + (6 - offset) / 24, kolkata, anchor_civil=early, longitude=ujjain_longitude),
                     "06:00")


class EclipseCivilDatesTests(unittest.TestCase):

  def test_marks_only_local_date_of_maximum(self):
    maximum = _wall_jd(2026, 3, 4, 0, 5)
    eclipse = ("Lunar", "Partial", maximum)
    # Without sunrise: civil date of the maximum itself.
    dates = eclipse_civil_dates([eclipse], "Asia/Kolkata")
    self.assertEqual(dates, {Date(2026, 3, 4)})
    # With sunrise after the maximum: previous Hindu day.
    sunrise = _wall_jd(2026, 3, 4, 6, 30)
    dates = eclipse_civil_dates([eclipse], "Asia/Kolkata", sunrise_by_date={Date(2026, 3, 4): sunrise})
    self.assertEqual(dates, {Date(2026, 3, 3)})

  def test_lmt_era_reads_the_observers_mean_time_throughout(self):
    # 23:30 Ujjain mean time on 10 Mar 1800 is already 00:20 on the 11th at
    # Kolkata's (tzdb) LMT. Looking up "that morning's sunrise" at Kolkata time
    # and the Hindu day at Ujjain time used to print "Mar 09 ... 47:30".
    ujjain = load_location("Ujjain")
    day = Date(1800, 3, 10)
    maximum = gregorian_to_jd(day) + (23.5 - ujjain.longitude / 15) / 24
    sunrise_by_date = {d: panchanga.sunrise(gregorian_to_jd(d), place_for_date(ujjain, d)) for d in (day, day + 1)}
    eclipse = ("Lunar", "Total", maximum)
    kwargs = {"sunrise_by_date": sunrise_by_date, "longitude": ujjain.longitude}
    self.assertEqual(eclipse_civil_dates([eclipse], ujjain.timezone_name, **kwargs), {day})
    self.assertIn("Lunar Mar 10 (Total) maximum phase at 23:30",
                  format_eclipse_line([eclipse], ujjain.timezone_name, **kwargs))


class HinduDayHasEclipseTests(unittest.TestCase):
  """The eclipse test uses [sunrise, next sunrise), like the printed mark."""

  geopos = (75.0, 23.0, 0.0)  # Ujjain-ish

  def _maximum_jd(self, year, month, day, hour, minute):
    return _wall_jd(year, month, day, hour, minute)

  def _lunar_at(self, maximum):
    return mock.patch("festival_rules.panchanga.swe.lun_eclipse_when_loc", return_value=(
      panchanga.swe.ECL_PARTIAL | panchanga.swe.ECL_VISIBLE,
      _times(maximum),
      None,
    ))

  def test_maximum_before_sunrise_belongs_to_the_previous_date(self):
    # Hypothetical maximum 02:00 on 12-Oct-2026; that morning's sunrise ~06:30,
    # so the maximum falls in the Hindu day that began on 11-Oct.
    with self._lunar_at(self._maximum_jd(2026, 10, 12, 2, 0)), mock.patch(
        "festival_rules.panchanga.swe.sol_eclipse_when_loc", return_value=(0, _times(100.0), None)):
      self.assertTrue(hindu_day_has_eclipse(Date(2026, 10, 11), self.geopos, "Asia/Kolkata"))
      self.assertFalse(hindu_day_has_eclipse(Date(2026, 10, 12), self.geopos, "Asia/Kolkata"))

  def test_maximum_after_sunrise_stays_on_its_own_date(self):
    with self._lunar_at(self._maximum_jd(2026, 10, 12, 7, 0)), mock.patch(
        "festival_rules.panchanga.swe.sol_eclipse_when_loc", return_value=(0, _times(100.0), None)):
      self.assertFalse(hindu_day_has_eclipse(Date(2026, 10, 11), self.geopos, "Asia/Kolkata"))
      self.assertTrue(hindu_day_has_eclipse(Date(2026, 10, 12), self.geopos, "Asia/Kolkata"))


if __name__ == "__main__":
  unittest.main()
