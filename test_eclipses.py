"""Unit tests for locally visible eclipse discovery."""

import unittest
from unittest import mock

import panchanga

from festival_rules import find_local_eclipses
from generate_panchanga_calendar import (
    eclipse_civil_dates,
    format_eclipse_line,
    jd_to_local_civil_date,
)


def _times(*, maximum, start, end, rise=0.0, setting=0.0, solar=False):
    times = [0.0] * 10
    times[0] = maximum
    if solar:
        times[1], times[4] = start, end
        times[5], times[6] = rise, setting
    else:
        times[2], times[3] = start, end
        times[8], times[9] = rise, setting
    return tuple(times)


class FindLocalEclipsesTests(unittest.TestCase):
    geopos = (77.6, 13.0, 0.0)

    def test_purely_penumbral_lunar_is_omitted(self):
        with mock.patch(
                "festival_rules.panchanga.swe.lun_eclipse_when_loc",
                side_effect=[
                    (panchanga.swe.ECL_PENUMBRAL | panchanga.swe.ECL_VISIBLE, _times(
                        maximum=10.5, start=10.2, end=10.8), None),
                    (0, _times(maximum=100.0, start=0.0, end=0.0), None),
                ],
        ), mock.patch(
                "festival_rules.panchanga.swe.sol_eclipse_when_loc",
                return_value=(0, _times(maximum=100.0, start=0.0, end=0.0, solar=True), None),
        ):
            self.assertEqual(find_local_eclipses(10.0, 11.0, self.geopos), [])

    def test_partial_lunar_is_included(self):
        with mock.patch(
                "festival_rules.panchanga.swe.lun_eclipse_when_loc",
                side_effect=[
                    (panchanga.swe.ECL_PARTIAL | panchanga.swe.ECL_VISIBLE, _times(maximum=10.5, start=10.2,
                                                                                   end=10.8), None),
                    (0, _times(maximum=100.0, start=0.0, end=0.0), None),
                ],
        ), mock.patch(
                "festival_rules.panchanga.swe.sol_eclipse_when_loc",
                return_value=(0, _times(maximum=100.0, start=0.0, end=0.0, solar=True), None),
        ):
            self.assertEqual(
                find_local_eclipses(10.0, 11.0, self.geopos),
                [("Lunar", "Partial", 10.5, 10.2, 10.8)],
            )

    def test_total_and_annular_solar_phases(self):
        with mock.patch(
                "festival_rules.panchanga.swe.lun_eclipse_when_loc",
                return_value=(0, _times(maximum=100.0, start=0.0, end=0.0), None),
        ), mock.patch(
                "festival_rules.panchanga.swe.sol_eclipse_when_loc",
                side_effect=[
                    (panchanga.swe.ECL_TOTAL | panchanga.swe.ECL_VISIBLE,
                     _times(maximum=10.4, start=10.1, end=10.6, solar=True), None),
                    (panchanga.swe.ECL_ANNULAR | panchanga.swe.ECL_VISIBLE,
                     _times(maximum=20.4, start=20.1, end=20.6, solar=True), None),
                    (0, _times(maximum=100.0, start=0.0, end=0.0, solar=True), None),
                ],
        ):
            self.assertEqual(
                find_local_eclipses(10.0, 21.0, self.geopos),
                [
                    ("Solar", "Total", 10.4, 10.1, 10.6),
                    ("Solar", "Annular", 20.4, 20.1, 20.6),
                ],
            )

    def test_event_outside_range_is_omitted(self):
        with mock.patch(
                "festival_rules.panchanga.swe.lun_eclipse_when_loc",
                side_effect=[
                    (panchanga.swe.ECL_PARTIAL | panchanga.swe.ECL_VISIBLE, _times(maximum=12.5, start=12.2,
                                                                                   end=12.8), None),
                    (0, _times(maximum=100.0, start=0.0, end=0.0), None),
                ],
        ), mock.patch(
                "festival_rules.panchanga.swe.sol_eclipse_when_loc",
                return_value=(0, _times(maximum=100.0, start=0.0, end=0.0, solar=True), None),
        ):
            self.assertEqual(find_local_eclipses(10.0, 11.0, self.geopos), [])

    def test_empty_clipped_visibility_window_is_omitted(self):
        with mock.patch(
                "festival_rules.panchanga.swe.lun_eclipse_when_loc",
                side_effect=[
                    (panchanga.swe.ECL_PARTIAL | panchanga.swe.ECL_VISIBLE, _times(maximum=10.5, start=0.0,
                                                                                   end=0.0), None),
                    (0, _times(maximum=100.0, start=0.0, end=0.0), None),
                ],
        ), mock.patch(
                "festival_rules.panchanga.swe.sol_eclipse_when_loc",
                return_value=(0, _times(maximum=100.0, start=0.0, end=0.0, solar=True), None),
        ):
            self.assertEqual(find_local_eclipses(10.0, 11.0, self.geopos), [])

    def test_moonset_fills_missing_geometric_end(self):
        # Helsinki 2026-08-28 style: partial end is zeroed; moonset bounds visibility.
        with mock.patch(
                "festival_rules.panchanga.swe.lun_eclipse_when_loc",
                side_effect=[
                    (panchanga.swe.ECL_PARTIAL | panchanga.swe.ECL_VISIBLE,
                     _times(maximum=10.5, start=10.2, end=0.0, setting=10.5), None),
                    (0, _times(maximum=100.0, start=0.0, end=0.0), None),
                ],
        ), mock.patch(
                "festival_rules.panchanga.swe.sol_eclipse_when_loc",
                return_value=(0, _times(maximum=100.0, start=0.0, end=0.0, solar=True), None),
        ):
            self.assertEqual(
                find_local_eclipses(10.0, 11.0, self.geopos),
                [("Lunar", "Partial", 10.5, 10.2, 10.5)],
            )

    def test_search_continues_after_skipped_penumbral(self):
        # Helsinki 2025-03 style: a tiny search step re-returns the same
        # penumbral maximum and used to stall before later eclipses.
        def lun_finder(search_jd, _geopos):
            if search_jd < 11.0:
                return (
                    panchanga.swe.ECL_PENUMBRAL | panchanga.swe.ECL_VISIBLE,
                    _times(maximum=10.5, start=10.2, end=10.8),
                    None,
                )
            if search_jd < 21.0:
                return (
                    panchanga.swe.ECL_PARTIAL | panchanga.swe.ECL_VISIBLE,
                    _times(maximum=20.5, start=20.2, end=20.8),
                    None,
                )
            return (0, _times(maximum=100.0, start=0.0, end=0.0), None)

        with mock.patch(
                "festival_rules.panchanga.swe.lun_eclipse_when_loc",
                side_effect=lun_finder,
        ), mock.patch(
                "festival_rules.panchanga.swe.sol_eclipse_when_loc",
                return_value=(0, _times(maximum=100.0, start=0.0, end=0.0, solar=True), None),
        ):
            self.assertEqual(
                find_local_eclipses(10.0, 21.0, self.geopos),
                [("Lunar", "Partial", 20.5, 20.2, 20.8)],
            )

    def test_moonrise_clip_keeps_visible_remainder(self):
        with mock.patch(
                "festival_rules.panchanga.swe.lun_eclipse_when_loc",
                side_effect=[
                    (panchanga.swe.ECL_PARTIAL | panchanga.swe.ECL_VISIBLE,
                     _times(maximum=10.5, start=10.0, end=10.8, rise=10.3), None),
                    (0, _times(maximum=100.0, start=0.0, end=0.0), None),
                ],
        ), mock.patch(
                "festival_rules.panchanga.swe.sol_eclipse_when_loc",
                return_value=(0, _times(maximum=100.0, start=0.0, end=0.0, solar=True), None),
        ):
            self.assertEqual(
                find_local_eclipses(10.0, 11.0, self.geopos),
                [("Lunar", "Partial", 10.5, 10.3, 10.8)],
            )


class FormatEclipseLineTests(unittest.TestCase):

    def test_none_when_empty(self):
        self.assertEqual(format_eclipse_line([], "Asia/Kolkata"), "Eclipses: None")

    def test_formats_local_civil_dates_and_times(self):
        from datetime import datetime
        from zoneinfo import ZoneInfo

        ist = ZoneInfo("Asia/Kolkata")

        def to_jd(local_dt):
            return local_dt.timestamp() / 86400.0 + 2440587.5

        maximum = to_jd(datetime(2026, 3, 3, 10, 0, tzinfo=ist))
        start = to_jd(datetime(2026, 3, 3, 9, 30, tzinfo=ist))
        end = to_jd(datetime(2026, 3, 3, 11, 30, tzinfo=ist))
        line = format_eclipse_line(
            [("Lunar", "Partial", maximum, start, end)],
            "Asia/Kolkata",
        )
        self.assertEqual(line, "Eclipses: Lunar Mar 03 (Partial) 09:30-11:30")
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
        start = to_jd(datetime(2026, 3, 3, 9, 30, tzinfo=ist))
        end = to_jd(datetime(2026, 3, 3, 11, 30, tzinfo=ist))
        sunrise = to_jd(datetime(2026, 3, 3, 6, 45, tzinfo=ist))
        line = format_eclipse_line(
            [("Lunar", "Partial", maximum, start, end)],
            "Asia/Kolkata",
            sunrise_by_date={date(2026, 3, 3): sunrise},
        )
        self.assertEqual(
            line,
            "Eclipses: Lunar Mar 03 (Partial) 09:30-11:30, sunrise 06:45",
        )


class EclipseCivilDatesTests(unittest.TestCase):

    def test_marks_local_dates_covering_visibility(self):
        from datetime import datetime
        from zoneinfo import ZoneInfo

        ist = ZoneInfo("Asia/Kolkata")

        def to_jd(local_dt):
            return local_dt.timestamp() / 86400.0 + 2440587.5

        start = to_jd(datetime(2026, 3, 3, 23, 30, tzinfo=ist))
        end = to_jd(datetime(2026, 3, 4, 1, 0, tzinfo=ist))
        dates = eclipse_civil_dates(
            [("Lunar", "Partial", start, start, end)],
            "Asia/Kolkata",
        )
        self.assertEqual(
            {d.isoformat()
             for d in dates},
            {"2026-03-03", "2026-03-04"},
        )


if __name__ == "__main__":
    unittest.main()
