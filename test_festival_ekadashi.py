"""Tests for Ekadashi resolution engines."""

from datetime import date, timedelta
import unittest
from unittest.mock import patch

from festival_rules import (
    format_festival_dates,
    resolve_festivals,
    resolve_generic_udaya_ekadashi_dates,
    select_vaikuntha_ekadashi_dates,
)
from festival_test_helpers import festival_rule, record


class VaikunthaEkadashiRuleTests(unittest.TestCase):
    rule = festival_rule("Vaikuntha Ekadashi")

    def test_rule_is_regional_with_dharma_sindhu_ekadashi_mechanics(self):
        self.assertEqual(self.rule.status, "regional")
        self.assertIn("drikpanchang.com", self.rule.source)

    def test_rule_allows_a_dhanur_season_without_an_occurrence(self):
        self.assertTrue(self.rule.allow_empty)

    def test_empty_occurrence_is_rendered_as_none(self):
        with patch(
            "festival_rules.FESTIVAL_RULES",
            (self.rule,),
        ), patch(
            "festival_rules.select_vaikuntha_ekadashi_dates",
            return_value=[],
        ):
            festivals_by_date, entries = resolve_festivals([], {})

        entry = next(item for item in entries if item[0] == self.rule.number)
        self.assertEqual(festivals_by_date, {})
        self.assertEqual(entry[1], "None")
        self.assertEqual(format_festival_dates([]), "None")

    def test_empty_nonoptional_festival_remains_an_error(self):
        janmashtami = festival_rule("Janmashtami")
        with patch(
            "festival_rules.FESTIVAL_RULES",
            (janmashtami,),
        ), patch(
            "festival_rules.select_janmashtami_dates",
            return_value=[],
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "No calendar date found for Janmashtami",
            ):
                resolve_festivals([], {})

    def test_chooses_margasirsa_or_pusya_candidate_in_dhanur(self):
        margasirsa = date(2030, 12, 10)
        pusya = date(2031, 1, 8)
        records = [
            (margasirsa, "S11", "9", False, 3.0, 10.0, 10.5),
            (pusya, "S11", "10", False, 3.0, 20.0, 20.5),
        ]
        with patch(
            "festival_rules.resolve_dharma_sindhu_vaishnava_ekadashi_dates",
            return_value=[margasirsa, pusya],
        ), patch(
            "festival_rules.panchanga.raasi",
            side_effect=[8, 9],
        ):
            self.assertEqual(
                select_vaikuntha_ekadashi_dates([], {}, records),
                [pusya],
            )

    def test_keeps_vaishnava_fast_shifted_to_dvadashi(self):
        fast_date = date(2030, 12, 20)
        records = [
            (fast_date, "S12", "9", False, 3.0, 10.0, 10.5),
        ]
        with patch(
            "festival_rules.resolve_dharma_sindhu_vaishnava_ekadashi_dates",
            return_value=[fast_date],
        ), patch(
            "festival_rules.panchanga.raasi",
            return_value=9,
        ):
            self.assertEqual(
                select_vaikuntha_ekadashi_dates([], {}, records),
                [fast_date],
            )

    def test_rejects_krishna_ekadashi_in_dhanur(self):
        fast_date = date(2030, 12, 5)
        records = [
            (fast_date, "K11", "9", False, 3.0, 10.0, 10.5),
        ]
        with patch(
            "festival_rules.resolve_dharma_sindhu_vaishnava_ekadashi_dates",
            return_value=[fast_date],
        ), patch(
            "festival_rules.panchanga.raasi",
            return_value=9,
        ):
            self.assertEqual(
                select_vaikuntha_ekadashi_dates([], {}, records),
                [],
            )

    def test_accepts_adhika_lunar_masa_when_solar_month_is_dhanur(self):
        fast_date = date(2030, 12, 20)
        records = [
            (fast_date, "S11", "10", True, 3.0, 10.0, 10.5),
        ]
        with patch(
            "festival_rules.resolve_dharma_sindhu_vaishnava_ekadashi_dates",
            return_value=[fast_date],
        ), patch(
            "festival_rules.panchanga.raasi",
            return_value=9,
        ):
            self.assertEqual(
                select_vaikuntha_ekadashi_dates([], {}, records),
                [fast_date],
            )

    def test_retains_multiple_dhanur_occurrences_in_supplied_range(self):
        first = date(2025, 1, 10)
        second = date(2025, 12, 30)
        records = [
            (first, "S11", "10", False, 3.0, 10.0, 10.5),
            (second, "S11", "9", False, 3.0, 20.0, 20.5),
        ]
        with patch(
            "festival_rules.resolve_dharma_sindhu_vaishnava_ekadashi_dates",
            return_value=[first, second],
        ), patch(
            "festival_rules.panchanga.raasi",
            return_value=9,
        ):
            self.assertEqual(
                select_vaikuntha_ekadashi_dates([], {}, records),
                [first, second],
            )


class GenericUdayaEkadashiTests(unittest.TestCase):
    """resolve_generic_udaya_ekadashi_dates uses vriddhi→first, kshaya→next."""

    def _call(self, records):
        with patch(
            "festival_rules.collect_records",
            return_value=records,
        ):
            return resolve_generic_udaya_ekadashi_dates([({}, {})], {})

    def test_normal_single_ekadashi_at_sunrise(self):
        records = [
            record(date(2030, 3, 20), "S11"),
            record(date(2030, 3, 21), "S12"),
            record(date(2030, 3, 22), "S13"),
        ]
        self.assertEqual(self._call(records), [date(2030, 3, 20)])

    def test_vriddhi_ekadashi_uses_first_day(self):
        records = [
            record(date(2030, 3, 20), "S11"),
            record(date(2030, 3, 21), "S11"),
            record(date(2030, 3, 22), "S12"),
        ]
        self.assertEqual(self._call(records), [date(2030, 3, 20)])

    def test_kshaya_ekadashi_uses_next_day(self):
        records = [
            (date(2030, 8, 4), "S10", "5", False, 1.0, 10.0, 10.5),
            (date(2030, 8, 5), "S12", "5", False, 1.0, 11.0, 11.5),
        ]
        with patch(
            "festival_rules.tithi_intervals",
            return_value=[(10.1, 10.9)],
        ):
            self.assertEqual(self._call(records), [date(2030, 8, 5)])

    def test_both_pakshas_are_resolved(self):
        records = [
            record(date(2030, 3, 6), "S11"),
            record(date(2030, 3, 20), "K11"),
        ]
        self.assertEqual(
            self._call(records),
            [date(2030, 3, 6), date(2030, 3, 20)],
        )


if __name__ == "__main__":
    unittest.main()
