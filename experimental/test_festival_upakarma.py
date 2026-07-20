"""Tests for Rig and Yajur Upakarma resolution."""

from datetime import date
import unittest
from unittest.mock import patch

import panchanga

from experimental.festival_rules import (
    eclipse_or_sankranti_in_window,
    select_rigveda_upakarma_dates,
    select_taittiriya_apastamba_upakarma_dates,
    select_taittiriya_purnima_dates,
)
from experimental.festival_test_helpers import festival_rule


class RigUpakarmaRuleTests(unittest.TestCase):
    rule = festival_rule("Rig Upakarma")

    def test_rule_is_attributed_to_dharma_sindhu(self):
        self.assertEqual(self.rule.status, "dharmasindhu")
        self.assertIn("transliteral.org", self.rule.source)

    def test_selects_shravana_at_sunrise_with_two_muhurtas(self):
        records = [
            (date(2026, 8, 25), "S13", "5", False, 3.0, 10.0, 10.5),
            (date(2026, 8, 26), "S14", "5", False, 3.0, 11.0, 11.5),
            (date(2026, 8, 27), "S15", "5", False, 3.0, 12.0, 12.5),
        ]
        with patch(
            "experimental.festival_rules.nakshatra_number_at",
            side_effect=lambda jd: 22 if 10.9 < jd < 11.1 else 21,
        ), patch(
            "experimental.festival_rules.nakshatra_overlap_hours",
            return_value=2.0,
        ), patch(
            "experimental.festival_rules.upakarma_date_is_contaminated",
            return_value=False,
        ):
            self.assertEqual(
                select_rigveda_upakarma_dates(
                    records,
                    self.rule,
                    (0.0, 0.0, 0.0),
                ),
                [date(2026, 8, 26)],
            )

    def test_two_sunrise_shravanas_use_later_with_three_muhurtas(self):
        records = [
            (date(2030, 8, 20), "S14", "5", False, 3.0, 10.0, 10.5),
            (date(2030, 8, 21), "S15", "5", False, 3.0, 11.0, 11.5),
        ]
        with patch(
            "experimental.festival_rules.nakshatra_number_at",
            return_value=22,
        ), patch(
            "experimental.festival_rules.nakshatra_overlap_hours",
            side_effect=[3.0, 2.4],
        ), patch(
            "experimental.festival_rules.upakarma_date_is_contaminated",
            return_value=False,
        ):
            self.assertEqual(
                select_rigveda_upakarma_dates(
                    records,
                    self.rule,
                    (0.0, 0.0, 0.0),
                ),
                [date(2030, 8, 21)],
            )

    def test_two_sunrise_shravanas_reject_short_later_remainder(self):
        records = [
            (date(2030, 8, 20), "S14", "5", False, 3.0, 10.0, 10.5),
            (date(2030, 8, 21), "S15", "5", False, 3.0, 11.0, 11.5),
        ]
        with patch(
            "experimental.festival_rules.nakshatra_number_at",
            return_value=22,
        ), patch(
            "experimental.festival_rules.nakshatra_overlap_hours",
            side_effect=[3.0, 2.0],
        ), patch(
            "experimental.festival_rules.upakarma_date_is_contaminated",
            return_value=False,
        ):
            self.assertEqual(
                select_rigveda_upakarma_dates(
                    records,
                    self.rule,
                    (0.0, 0.0, 0.0),
                ),
                [date(2030, 8, 20)],
            )

    def test_contaminated_shravana_falls_back_to_panchami(self):
        records = [
            (date(2030, 8, 5), "S4", "5", False, 3.0, 10.0, 10.5),
            (date(2030, 8, 6), "S5", "5", False, 3.0, 11.0, 11.5),
            (date(2030, 8, 20), "S14", "5", False, 3.0, 30.0, 30.5),
        ]
        with patch(
            "experimental.festival_rules.nakshatra_number_at",
            side_effect=lambda jd: 22 if 29.9 < jd < 30.1 else 1,
        ), patch(
            "experimental.festival_rules.nakshatra_overlap_hours",
            return_value=2.0,
        ), patch(
            "experimental.festival_rules.upakarma_date_is_contaminated",
            side_effect=[True, False],
        ):
            self.assertEqual(
                select_rigveda_upakarma_dates(
                    records,
                    self.rule,
                    (0.0, 0.0, 0.0),
                ),
                [date(2030, 8, 6)],
            )

    def test_short_sunrise_panchami_uses_previous_day(self):
        records = [
            (date(2030, 8, 5), "S4", "5", False, 3.0, 10.0, 10.5),
            (date(2030, 8, 6), "S5", "5", False, 2.0, 11.0, 11.5),
        ]
        with patch(
            "experimental.festival_rules.nakshatra_number_at",
            return_value=1,
        ), patch(
            "experimental.festival_rules.upakarma_date_is_contaminated",
            return_value=False,
        ):
            self.assertEqual(
                select_rigveda_upakarma_dates(
                    records,
                    self.rule,
                    (0.0, 0.0, 0.0),
                ),
                [date(2030, 8, 5)],
            )

    def test_uses_bhadrapada_shravana_when_shravana_month_fails(self):
        records = [
            (date(2030, 9, 15), "S14", "6", False, 3.0, 50.0, 50.5),
        ]
        with patch(
            "experimental.festival_rules.nakshatra_number_at",
            return_value=22,
        ), patch(
            "experimental.festival_rules.nakshatra_overlap_hours",
            return_value=2.0,
        ), patch(
            "experimental.festival_rules.upakarma_date_is_contaminated",
            return_value=False,
        ):
            self.assertEqual(
                select_rigveda_upakarma_dates(
                    records,
                    self.rule,
                    (0.0, 0.0, 0.0),
                ),
                [date(2030, 9, 15)],
            )

class UpakarmaContaminationTests(unittest.TestCase):
    geopos = (24.94, 60.17, 0.0)

    @staticmethod
    def eclipse_times(maximum, start, end, rise=0.0, setting=0.0):
        times = [0.0] * 10
        times[0] = maximum
        times[2] = start
        times[3] = end
        times[8] = rise
        times[9] = setting
        return tuple(times)

    @staticmethod
    def solar_times(start, end):
        times = [0.0] * 10
        times[0] = (start + end) / 2
        times[1] = start
        times[4] = end
        return tuple(times)

    def test_ignores_eclipse_not_visible_at_location(self):
        with patch(
            "experimental.festival_rules.panchanga.solar_longitude",
            return_value=10.0,
        ), patch(
            "experimental.festival_rules.panchanga.swe.lun_eclipse_when_loc",
            return_value=(
                panchanga.swe.ECL_PARTIAL,
                self.eclipse_times(50.0, 49.9, 50.1),
                (),
            ),
        ), patch(
            "experimental.festival_rules.panchanga.swe.sol_eclipse_when_loc",
            return_value=(0, self.solar_times(60.0, 60.1), ()),
        ):
            self.assertFalse(
                eclipse_or_sankranti_in_window(10.0, 11.0, self.geopos)
            )

    def test_visible_contacts_count_when_maximum_precedes_window(self):
        with patch(
            "experimental.festival_rules.panchanga.solar_longitude",
            return_value=10.0,
        ), patch(
            "experimental.festival_rules.panchanga.swe.lun_eclipse_when_loc",
            return_value=(
                panchanga.swe.ECL_PARTIAL,
                self.eclipse_times(9.95, 9.9, 10.1),
                (),
            ),
        ):
            self.assertTrue(
                eclipse_or_sankranti_in_window(10.0, 11.0, self.geopos)
            )

    def test_purely_penumbral_lunar_eclipse_is_ignored(self):
        with patch(
            "experimental.festival_rules.panchanga.solar_longitude",
            return_value=10.0,
        ), patch(
            "experimental.festival_rules.panchanga.swe.lun_eclipse_when_loc",
            return_value=(
                panchanga.swe.ECL_PENUMBRAL,
                self.eclipse_times(10.2, 10.1, 10.3),
                (),
            ),
        ), patch(
            "experimental.festival_rules.panchanga.swe.sol_eclipse_when_loc",
            return_value=(0, self.solar_times(60.0, 60.1), ()),
        ):
            self.assertFalse(
                eclipse_or_sankranti_in_window(10.0, 11.0, self.geopos)
            )

class YajurUpakarmaRuleTests(unittest.TestCase):
    rule = festival_rule("Yajur Upakarma")

    @staticmethod
    def records(remainder=2.0):
        return [
            (date(2030, 8, 14), "S14", "5", False, 1.0, 10.0, 10.5),
            (date(2030, 8, 15), "S15", "5", False, remainder, 11.0, 11.5),
            (date(2030, 8, 16), "K1", "5", False, 1.0, 12.0, 12.5),
        ]

    @staticmethod
    def records_with_bhadrapada_fallback():
        return [
            (date(2030, 8, 14), "S14", "5", False, 1.0, 10.0, 10.5),
            (date(2030, 8, 15), "S15", "5", False, 2.0, 11.0, 11.5),
            (date(2030, 8, 16), "K1", "5", False, 1.0, 12.0, 12.5),
            (date(2030, 9, 13), "S14", "6", False, 1.0, 40.0, 40.5),
            (date(2030, 9, 14), "S15", "6", False, 1.0, 41.0, 41.5),
            (date(2030, 9, 15), "K1", "6", False, 1.0, 42.0, 42.5),
        ]

    def test_first_muhurta_is_fixed_at_two_ghatis(self):
        records = [
            (date(2030, 8, 14), "S14", "5", False, 1.0, 10.0, 10.75),
            (date(2030, 8, 15), "S15", "5", False, 2.0, 11.0, 11.5),
            (date(2030, 8, 16), "K1", "5", False, 1.0, 12.0, 12.5),
        ]
        with patch(
            "experimental.festival_rules.tithi_intervals",
            return_value=[(10.04, 11.08)],
        ):
            self.assertEqual(
                select_taittiriya_purnima_dates(records, 5),
                [date(2030, 8, 15)],
            )

    def test_taittiriyas_use_later_day_with_two_muhurtas(self):
        with patch(
            "experimental.festival_rules.tithi_intervals",
            return_value=[(10.1, 11.2)],
        ), patch(
            "experimental.festival_rules.eclipse_or_sankranti_in_window",
            return_value=False,
        ):
            self.assertEqual(
                select_taittiriya_apastamba_upakarma_dates(
                    self.records(),
                    self.rule,
                    (0.0, 0.0, 0.0),
                ),
                [date(2030, 8, 15)],
            )

    def test_short_later_purnima_uses_earlier_day(self):
        with patch(
            "experimental.festival_rules.tithi_intervals",
            return_value=[(10.1, 11.05)],
        ), patch(
            "experimental.festival_rules.eclipse_or_sankranti_in_window",
            return_value=False,
        ):
            self.assertEqual(
                select_taittiriya_apastamba_upakarma_dates(
                    self.records(remainder=1.0),
                    self.rule,
                    (0.0, 0.0, 0.0),
                ),
                [date(2030, 8, 14)],
            )

    def test_kshaya_purnima_uses_civil_day_containing_purnima(self):
        records = [
            (date(2031, 8, 2), "S14", "5", False, 1.0, 10.0, 10.5),
            (date(2031, 8, 3), "K1", "5", False, 1.0, 11.0, 11.5),
        ]
        with patch(
            "experimental.festival_rules.tithi_intervals",
            return_value=[(10.1, 10.9)],
        ), patch(
            "experimental.festival_rules.eclipse_or_sankranti_in_window",
            return_value=False,
        ):
            self.assertEqual(
                select_taittiriya_apastamba_upakarma_dates(
                    records,
                    self.rule,
                    (0.0, 0.0, 0.0),
                ),
                [date(2031, 8, 2)],
            )

    def test_bhadrapada_fallback_reuses_short_remnant_rule(self):
        with patch(
            "experimental.festival_rules.tithi_intervals",
            side_effect=[
                [(10.1, 11.2)],
                [(40.1, 41.05)],
            ],
        ), patch(
            "experimental.festival_rules.upakarma_date_is_contaminated",
            side_effect=[True, False],
        ):
            self.assertEqual(
                select_taittiriya_apastamba_upakarma_dates(
                    self.records_with_bhadrapada_fallback(),
                    self.rule,
                    (0.0, 0.0, 0.0),
                ),
                [date(2030, 9, 13)],
            )

    def test_contaminated_bhadrapada_fallback_returns_no_date(self):
        with patch(
            "experimental.festival_rules.tithi_intervals",
            side_effect=[
                [(10.1, 11.2)],
                [(40.1, 41.2)],
            ],
        ), patch(
            "experimental.festival_rules.upakarma_date_is_contaminated",
            side_effect=[True, True],
        ):
            self.assertEqual(
                select_taittiriya_apastamba_upakarma_dates(
                    self.records_with_bhadrapada_fallback(),
                    self.rule,
                    (0.0, 0.0, 0.0),
                ),
                [],
            )

    def test_kshaya_bhadrapada_purnima_can_be_fallback(self):
        records = [
            (date(2030, 9, 13), "S14", "6", False, 1.0, 40.0, 40.5),
            (date(2030, 9, 14), "K1", "6", False, 1.0, 41.0, 41.5),
        ]
        with patch(
            "experimental.festival_rules.tithi_intervals",
            return_value=[(40.1, 40.9)],
        ):
            self.assertEqual(
                select_taittiriya_purnima_dates(records, 6),
                [date(2030, 9, 13)],
            )

    def test_rule_allows_both_branch_dates_to_be_defective(self):
        self.assertTrue(self.rule.allow_empty)


if __name__ == "__main__":
    unittest.main()
