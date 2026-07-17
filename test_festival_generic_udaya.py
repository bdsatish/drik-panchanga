"""Tests for the Generic Udaya festival policy."""

from datetime import date
import unittest
from unittest.mock import patch

from festival_rules import (
    FestivalRule,
    GENERIC_UDAYA_FESTIVAL_POLICY,
    generic_udaya_occurrences,
    plain_tithi_number,
    resolve_festivals,
    select_generic_udaya_festival_dates,
)
from festival_test_helpers import festival_rule, record


class GenericUdayaPolicyTests(unittest.TestCase):
    def test_plain_tithi_parser_rejects_conditional_rules(self):
        self.assertEqual(plain_tithi_number("S15"), 15)
        self.assertEqual(plain_tithi_number("K15"), 30)
        self.assertIsNone(plain_tithi_number("Dhanur-masa S11"))
        self.assertIsNone(plain_tithi_number("Solar"))

    def test_vriddhi_tithi_uses_first_sunrise(self):
        records = [
            record(date(2030, 8, 4), "S5", masa="5"),
            record(date(2030, 8, 5), "S5", masa="5"),
            record(date(2030, 8, 6), "S6", masa="5"),
        ]
        self.assertEqual(
            generic_udaya_occurrences(records, 5),
            [(date(2030, 8, 4), "5", False)],
        )

    def test_kshaya_tithi_uses_preceding_sunrise_date(self):
        records = [
            (date(2030, 8, 4), "S4", "5", False, 1.0, 10.0, 10.5),
            (date(2030, 8, 5), "S6", "5", False, 1.0, 11.0, 11.5),
        ]
        with patch(
            "festival_rules.tithi_intervals",
            return_value=[(10.1, 10.9)],
        ):
            self.assertEqual(
                generic_udaya_occurrences(records, 5),
                [(date(2030, 8, 4), "5", False)],
            )

    def test_kshaya_shukla_pratipada_uses_following_masa_metadata(self):
        rule = FestivalRule(999, "Boundary Festival", 2, "S1")
        records = [
            (date(2030, 5, 1), "K15", "1", False, 1.0, 10.0, 10.5),
            (date(2030, 5, 2), "S2", "2", False, 1.0, 11.0, 11.5),
        ]
        with patch(
            "festival_rules.tithi_intervals",
            return_value=[(10.1, 10.9)],
        ):
            self.assertEqual(
                select_generic_udaya_festival_dates(records, rule),
                [date(2030, 5, 1)],
            )

    def test_default_month_policy_excludes_adhika_occurrence(self):
        rule = FestivalRule(999, "Nija Festival", 2, "S3")
        records = [
            (date(2030, 5, 3), "S3", "A2", True, 1.0, 10.0, 10.5),
            (date(2030, 6, 2), "S3", "2", False, 1.0, 40.0, 40.5),
        ]
        self.assertEqual(
            select_generic_udaya_festival_dates(records, rule),
            [date(2030, 6, 2)],
        )

    def test_ugadi_preserves_adhika_chaitra_preference(self):
        rule = festival_rule("Ugadi")
        records = [
            (date(2030, 3, 5), "S1", "A1", True, 1.0, 10.0, 10.5),
            (date(2030, 4, 4), "S1", "1", False, 1.0, 40.0, 40.5),
        ]
        self.assertEqual(
            select_generic_udaya_festival_dates(records, rule),
            [date(2030, 3, 5)],
        )

    def test_generic_policy_keeps_non_tithi_selector(self):
        rule = festival_rule("Makara Sankranti")
        selected_date = date(2030, 1, 15)
        records = [
            (
                selected_date,
                "S1",
                "10",
                False,
                1.0,
                10.0,
                10.5,
            ),
        ]
        with patch(
            "festival_rules.FESTIVAL_RULES",
            (rule,),
        ), patch(
            "festival_rules.collect_records",
            return_value=records,
        ), patch(
            "festival_rules.collect_moonrise_jds",
            return_value={},
        ), patch(
            "festival_rules.select_makara_sankranti_dates",
            return_value=[selected_date],
        ) as selector:
            _, entries = resolve_festivals(
                [],
                {},
                GENERIC_UDAYA_FESTIVAL_POLICY,
            )

        selector.assert_called_once_with(records, rule)
        entry = next(item for item in entries if item[0] == rule.number)
        self.assertEqual(entry[1], "Jan 15")

    def test_generic_policy_bypasses_traditional_tithi_selector(self):
        rule = festival_rule("Rama Navami")
        selected_date = date(2030, 4, 11)
        records = [
            (
                selected_date,
                "S9",
                "1",
                False,
                1.0,
                10.0,
                10.5,
            ),
        ]
        with patch(
            "festival_rules.FESTIVAL_RULES",
            (rule,),
        ), patch(
            "festival_rules.collect_records",
            return_value=records,
        ), patch(
            "festival_rules.collect_moonrise_jds",
            return_value={},
        ), patch(
            "festival_rules.select_rama_navami_dates",
            side_effect=AssertionError("traditional selector called"),
        ):
            _, entries = resolve_festivals(
                [],
                {},
                GENERIC_UDAYA_FESTIVAL_POLICY,
            )

        entry = next(item for item in entries if item[0] == rule.number)
        self.assertEqual(entry[1], "Apr 11")


if __name__ == "__main__":
    unittest.main()
