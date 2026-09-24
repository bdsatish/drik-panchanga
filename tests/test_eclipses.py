"""Unit tests for locally visible eclipse discovery."""

import unittest
from unittest import mock

import panchanga

from festival_rules import (
  civil_day_has_eclipse,
  find_local_eclipses,
  jd_to_local_civil_date,
  julian_day_from_datetime,
)
from generate_panchanga_calendar import eclipse_civil_dates, format_eclipse_line, format_local_hm


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
    from datetime import datetime
    from zoneinfo import ZoneInfo

    ist = ZoneInfo("Asia/Kolkata")

    maximum = julian_day_from_datetime(datetime(2026, 3, 3, 10, 0, tzinfo=ist))
    line = format_eclipse_line([("Lunar", "Partial", maximum)], "Asia/Kolkata")
    self.assertEqual(
      line,
      "Eclipses: Lunar Mar 03 (Partial) maximum phase at 10:00. "
      "Eclipses have a brown wavy underline below Tithi.",
    )
    self.assertEqual(jd_to_local_civil_date(maximum, "Asia/Kolkata").isoformat(), "2026-03-03")

  def test_includes_sunrise_when_provided(self):
    from datetime import date, datetime
    from zoneinfo import ZoneInfo

    ist = ZoneInfo("Asia/Kolkata")

    maximum = julian_day_from_datetime(datetime(2026, 3, 3, 10, 0, tzinfo=ist))
    sunrise = julian_day_from_datetime(datetime(2026, 3, 3, 6, 45, tzinfo=ist))
    line = format_eclipse_line([("Lunar", "Partial", maximum)], "Asia/Kolkata",
                               sunrise_by_date={date(2026, 3, 3): sunrise})
    self.assertEqual(
      line,
      "Eclipses: Lunar Mar 03 (Partial) maximum phase at 10:00, sunrise 06:45. "
      "Eclipses have a brown wavy underline below Tithi.",
    )


class FormatLocalHmTests(unittest.TestCase):
  """``format_local_hm`` rounds to the nearest minute, without wrapping 24:00.

  The library convention (README) is that times past midnight are hours past
  24:00, matching ``panchanga.format_hms`` (grids and day view).
  """

  TZ = "Asia/Kolkata"

  def _jd(self, hour, minute, second=0, day=3):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    return julian_day_from_datetime(datetime(2026, 3, day, hour, minute, second, tzinfo=ZoneInfo(self.TZ)))

  def test_truncates_below_half_minute(self):
    self.assertEqual(format_local_hm(self._jd(23, 59, 29), self.TZ), "23:59")

  def test_ordinary_times(self):
    self.assertEqual(format_local_hm(self._jd(6, 45), self.TZ), "06:45")
    self.assertEqual(format_local_hm(self._jd(0, 5), self.TZ), "00:05")

  def test_rounds_up_to_24_00_not_00_00(self):
    # Regression: a modulo by 24h used to wrap 23:59:30+ back to 00:00, which
    # contradicted the documented hours-past-midnight convention and read as
    # the start of a day rather than the end of the current one.
    self.assertEqual(format_local_hm(self._jd(23, 59, 30), self.TZ), "24:00")
    self.assertEqual(format_local_hm(self._jd(23, 59, 50), self.TZ), "24:00")
    self.assertEqual(format_local_hm(self._jd(23, 59, 59), self.TZ), "24:00")

  def test_never_exceeds_24_00(self):
    # hour is 0-23, so the largest raw value is 1439.999..., i.e. 24:00 at most.
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
    self.assertEqual(jd_to_local_civil_date(jd, self.TZ).isoformat(), "2026-03-03")


class EclipseCivilDatesTests(unittest.TestCase):

  def test_marks_only_local_date_of_maximum(self):
    from datetime import date, datetime
    from zoneinfo import ZoneInfo

    ist = ZoneInfo("Asia/Kolkata")

    maximum = julian_day_from_datetime(datetime(2026, 3, 4, 0, 5, tzinfo=ist))
    eclipse = ("Lunar", "Partial", maximum)
    dates = eclipse_civil_dates([eclipse], "Asia/Kolkata")
    self.assertEqual(dates, {date(2026, 3, 4)})

    with mock.patch("festival_rules.panchanga.swe.lun_eclipse_when_loc", return_value=(
        panchanga.swe.ECL_PARTIAL | panchanga.swe.ECL_VISIBLE,
        _times(maximum),
        None,
    )), mock.patch("festival_rules.panchanga.swe.sol_eclipse_when_loc", return_value=(0, _times(100.0), None)):
      geopos = (77.6, 13.0, 0.0)
      self.assertFalse(civil_day_has_eclipse(date(2026, 3, 3), geopos, "Asia/Kolkata"))
      self.assertTrue(civil_day_has_eclipse(date(2026, 3, 4), geopos, "Asia/Kolkata"))


if __name__ == "__main__":
  unittest.main()
