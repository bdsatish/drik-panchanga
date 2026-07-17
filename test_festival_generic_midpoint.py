"""Tests for the Generic Midpoint festival policy."""

from datetime import date
import unittest
from unittest.mock import patch

from festival_rules import (
    GENERIC_MIDPOINT_FESTIVAL_POLICY,
    resolve_festivals,
    select_generic_midpoint_festival_dates,
)
from festival_test_helpers import festival_rule


class GenericMidpointPolicyTests(unittest.TestCase):
    def setUp(self):
        self.days = [
            (
                date(2030, 4, 10 + offset),
                "S9",
                "1",
                False,
                1.0,
                9.0 + offset,
                9.5 + offset,
            )
            for offset in range(3)
        ]

    def select(
        self,
        rule,
        interval,
        *,
        is_adhika=False,
        masa=None,
        records=None,
    ):
        with patch(
            "festival_rules.generic_udaya_occurrences",
            return_value=[
                (
                    date(2030, 4, 11),
                    str(rule.masa) if masa is None else masa,
                    is_adhika,
                )
            ],
        ), patch(
            "festival_rules.tithi_intervals",
            return_value=[interval],
        ):
            return select_generic_midpoint_festival_dates(
                self.days if records is None else records,
                rule,
            )

    def test_sunrise_present_tithi_can_belong_to_previous_day(self):
        self.assertEqual(
            self.select(festival_rule("Rama Navami"), (9.0, 10.2)),
            [date(2030, 4, 10)],
        )

    def test_vriddhi_occurrence_uses_one_tithi_midpoint(self):
        self.assertEqual(
            self.select(festival_rule("Rama Navami"), (9.8, 10.8)),
            [date(2030, 4, 11)],
        )

    def test_kshaya_occurrence_uses_containing_sunrise_day(self):
        self.assertEqual(
            self.select(festival_rule("Rama Navami"), (10.1, 10.5)),
            [date(2030, 4, 11)],
        )

    def test_exact_sunrise_midpoint_belongs_to_new_day(self):
        self.assertEqual(
            self.select(festival_rule("Rama Navami"), (9.0, 11.0)),
            [date(2030, 4, 11)],
        )

    def test_non_ugadi_adhika_occurrence_is_excluded(self):
        self.assertEqual(
            self.select(
                festival_rule("Rama Navami"),
                (10.1, 10.5),
                is_adhika=True,
            ),
            [],
        )

    def test_ugadi_adhika_occurrence_is_retained(self):
        self.assertEqual(
            self.select(
                festival_rule("Ugadi"),
                (10.1, 10.5),
                is_adhika=True,
            ),
            [date(2030, 4, 11)],
        )

    def test_wrong_masa_occurrence_is_excluded(self):
        self.assertEqual(
            self.select(
                festival_rule("Rama Navami"),
                (10.1, 10.5),
                masa="2",
            ),
            [],
        )

    def test_following_context_sunrise_is_required_for_ownership(self):
        rule = festival_rule("Rama Navami")
        interval = (10.1, 10.9)
        self.assertEqual(
            self.select(rule, interval, records=self.days[:2]),
            [],
        )
        self.assertEqual(
            self.select(rule, interval, records=self.days),
            [date(2030, 4, 11)],
        )

    def test_policy_uses_context_records_without_kala_overlay(self):
        rule = festival_rule("Yajur Upakarma")
        selected_date = self.days[1][0]
        with patch(
            "festival_rules.FESTIVAL_RULES",
            (rule,),
        ), patch(
            "festival_rules.collect_records",
            side_effect=[[self.days[1]], self.days],
        ), patch(
            "festival_rules.collect_moonrise_jds",
            return_value={},
        ), patch(
            "festival_rules.select_generic_midpoint_festival_dates",
            return_value=[selected_date],
        ) as selector, patch(
            "festival_rules.generic_kala_date_is_valid",
            side_effect=AssertionError("Generic Kala overlay called"),
        ):
            _, entries = resolve_festivals(
                [],
                {},
                GENERIC_MIDPOINT_FESTIVAL_POLICY,
                context_months=[(2030, 4)],
                context_data={(2030, 4): []},
            )

        selector.assert_called_once_with(self.days, rule)
        entry = next(item for item in entries if item[0] == rule.number)
        self.assertEqual(entry[1], "Apr 11")


if __name__ == "__main__":
    unittest.main()
