"""Unit tests for locally visible eclipse discovery."""

import unittest
from unittest import mock

import panchanga

from festival_rules import civil_day_has_eclipse, find_local_eclipses
from generate_panchanga_calendar import (
    eclipse_civil_dates,
    format_eclipse_line,
    jd_to_local_civil_date,
)


def _times(maximum):
    times = [0.0] * 10
    times[0] = maximum
    return tuple(times)


class FindLocalEclipsesTests(unittest.TestCase):
    geopos = (77.6, 13.0, 0.0)

    def test_purely_penumbral_lunar_is_omitted(self):
        with mock.patch(
                "festival_rules.panchanga.swe.lun_eclipse_when_loc",
                side_effect=[
                    (panchanga.swe.ECL_PENUMBRAL | panchanga.swe.ECL_VISIBLE, _times(10.5), None),
                    (0, _times(100.0), None),
                ],
        ), mock.patch(
                "festival_rules.panchanga.swe.sol_eclipse_when_loc",
                return_value=(0, _times(100.0), None),
        ):
            self.assertEqual(find_local_eclipses(10.0, 11.0, self.geopos), [])

    def test_invisible_partial_is_omitted(self):
        with mock.patch(
                "festival_rules.panchanga.swe.lun_eclipse_when_loc",
                side_effect=[
                    (panchanga.swe.ECL_PARTIAL, _times(10.5), None),
                    (0, _times(100.0), None),
                ],
        ), mock.patch(
                "festival_rules.panchanga.swe.sol_eclipse_when_loc",
                return_value=(0, _times(100.0), None),
        ):
            self.assertEqual(find_local_eclipses(10.0, 11.0, self.geopos), [])

    def test_partial_lunar_is_included_without_max_visible(self):
        # Helsinki-style: visible contacts, but maximum may fall at moonset.
        flags = panchanga.swe.ECL_PARTIAL | panchanga.swe.ECL_VISIBLE
        self.assertFalse(flags & panchanga.swe.ECL_MAX_VISIBLE)
        with mock.patch(
                "festival_rules.panchanga.swe.lun_eclipse_when_loc",
                side_effect=[
                    (flags, _times(10.5), None),
                    (0, _times(100.0), None),
                ],
        ), mock.patch(
                "festival_rules.panchanga.swe.sol_eclipse_when_loc",
                return_value=(0, _times(100.0), None),
        ):
            self.assertEqual(
                find_local_eclipses(10.0, 11.0, self.geopos),
                [("Lunar", "Partial", 10.5)],
            )

    def test_total_and_annular_solar_phases(self):
        with mock.patch(
                "festival_rules.panchanga.swe.lun_eclipse_when_loc",
                return_value=(0, _times(100.0), None),
        ), mock.patch(
                "festival_rules.panchanga.swe.sol_eclipse_when_loc",
                side_effect=[
                    (panchanga.swe.ECL_TOTAL | panchanga.swe.ECL_VISIBLE, _times(10.4), None),
                    (panchanga.swe.ECL_ANNULAR | panchanga.swe.ECL_VISIBLE, _times(20.4), None),
                    (0, _times(100.0), None),
                ],
        ):
            self.assertEqual(
                find_local_eclipses(10.0, 21.0, self.geopos),
                [
                    ("Solar", "Total", 10.4),
                    ("Solar", "Annular", 20.4),
                ],
            )

    def test_event_outside_range_is_omitted(self):
        with mock.patch(
                "festival_rules.panchanga.swe.lun_eclipse_when_loc",
                side_effect=[
                    (panchanga.swe.ECL_PARTIAL | panchanga.swe.ECL_VISIBLE, _times(12.5), None),
                    (0, _times(100.0), None),
                ],
        ), mock.patch(
                "festival_rules.panchanga.swe.sol_eclipse_when_loc",
                return_value=(0, _times(100.0), None),
        ):
            self.assertEqual(find_local_eclipses(10.0, 11.0, self.geopos), [])

    def test_search_continues_after_skipped_penumbral(self):
        # Helsinki 2025-03 style: a tiny search step re-returns the same
        # penumbral maximum and used to stall before later eclipses.
        def lun_finder(search_jd, _geopos):
            if search_jd < 11.0:
                return (
                    panchanga.swe.ECL_PENUMBRAL | panchanga.swe.ECL_VISIBLE,
                    _times(10.5),
                    None,
                )
            if search_jd < 21.0:
                return (
                    panchanga.swe.ECL_PARTIAL | panchanga.swe.ECL_VISIBLE,
                    _times(20.5),
                    None,
                )
            return (0, _times(100.0), None)

        with mock.patch(
                "festival_rules.panchanga.swe.lun_eclipse_when_loc",
                side_effect=lun_finder,
        ), mock.patch(
                "festival_rules.panchanga.swe.sol_eclipse_when_loc",
                return_value=(0, _times(100.0), None),
        ):
            self.assertEqual(
                find_local_eclipses(10.0, 21.0, self.geopos),
                [("Lunar", "Partial", 20.5)],
            )


class FormatEclipseLineTests(unittest.TestCase):

    def test_none_when_empty(self):
        self.assertEqual(format_eclipse_line([], "Asia/Kolkata"), "Eclipses: None")

    def test_formats_local_civil_dates_and_maximum_time(self):
        from datetime import datetime
        from zoneinfo import ZoneInfo

        ist = ZoneInfo("Asia/Kolkata")

        def to_jd(local_dt):
            return local_dt.timestamp() / 86400.0 + 2440587.5

        maximum = to_jd(datetime(2026, 3, 3, 10, 0, tzinfo=ist))
        line = format_eclipse_line(
            [("Lunar", "Partial", maximum)],
            "Asia/Kolkata",
        )
        self.assertEqual(line, "Eclipses: Lunar Mar 03 (Partial) max 10:00")
        self.assertEqual(
            jd_to_local_civil_date(maximum, "Asia/Kolkata").isoformat(),
            "2026-03-03",
        )

    def test_includes_sunrise_when_provided(self):
        from datetime import date, datetime
        from zoneinfo import ZoneInfo

        ist = ZoneInfo("Asia/Kolkata")

        def to_jd(local_dt):
            return local_dt.timestamp() / 86400.0 + 2440587.5

        maximum = to_jd(datetime(2026, 3, 3, 10, 0, tzinfo=ist))
        sunrise = to_jd(datetime(2026, 3, 3, 6, 45, tzinfo=ist))
        line = format_eclipse_line(
            [("Lunar", "Partial", maximum)],
            "Asia/Kolkata",
            sunrise_by_date={date(2026, 3, 3): sunrise},
        )
        self.assertEqual(
            line,
            "Eclipses: Lunar Mar 03 (Partial) max 10:00, sunrise 06:45",
        )


class EclipseCivilDatesTests(unittest.TestCase):

    def test_marks_only_local_date_of_maximum(self):
        from datetime import date, datetime
        from zoneinfo import ZoneInfo

        ist = ZoneInfo("Asia/Kolkata")

        def to_jd(local_dt):
            return local_dt.timestamp() / 86400.0 + 2440587.5

        maximum = to_jd(datetime(2026, 3, 4, 0, 5, tzinfo=ist))
        eclipse = ("Lunar", "Partial", maximum)
        dates = eclipse_civil_dates(
            [eclipse],
            "Asia/Kolkata",
        )
        self.assertEqual(dates, {date(2026, 3, 4)})

        with mock.patch(
                "festival_rules.panchanga.swe.lun_eclipse_when_loc",
                return_value=(
                    panchanga.swe.ECL_PARTIAL | panchanga.swe.ECL_VISIBLE,
                    _times(maximum),
                    None,
                ),
        ), mock.patch(
                "festival_rules.panchanga.swe.sol_eclipse_when_loc",
                return_value=(0, _times(100.0), None),
        ):
            geopos = (77.6, 13.0, 0.0)
            self.assertFalse(civil_day_has_eclipse(date(2026, 3, 3), geopos, "Asia/Kolkata"))
            self.assertTrue(civil_day_has_eclipse(date(2026, 3, 4), geopos, "Asia/Kolkata"))


if __name__ == "__main__":
    unittest.main()
