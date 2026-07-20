"""Tests for the Generic Anchor festival policy."""

from datetime import date
import unittest
from unittest.mock import patch

from experimental.festival_rules import (
    DAY_FIRST_QUARTER_ANCHOR,
    DAY_MIDPOINT_ANCHOR,
    DAY_THIRD_QUARTER_ANCHOR,
    GENERIC_ANCHOR_FESTIVAL_POLICY,
    NIGHT_FIRST_QUARTER_ANCHOR,
    NIGHT_MIDPOINT_ANCHOR,
    NIGHT_THIRD_QUARTER_ANCHOR,
    SUNRISE_ANCHOR,
    SUNSET_ANCHOR,
    generic_anchor_for_rule,
    generic_anchor_jd,
    resolve_festivals,
    select_generic_anchor_festival_dates,
)
from experimental.festival_test_helpers import festival_rule


class GenericAnchorPolicyTests(unittest.TestCase):
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

    def select(self, rule, interval, *, is_adhika=False):
        with patch(
            "experimental.festival_rules.generic_udaya_occurrences",
            return_value=[
                (
                    date(2030, 4, 11),
                    str(rule.masa),
                    is_adhika,
                )
            ],
        ), patch(
            "experimental.festival_rules.tithi_intervals",
            return_value=[interval],
        ):
            return select_generic_anchor_festival_dates(self.days, rule)

    def test_exact_anchor_calculations(self):
        first, second = self.days[:2]
        self.assertEqual(
            generic_anchor_jd(first, second, SUNRISE_ANCHOR),
            9.0,
        )
        self.assertEqual(
            generic_anchor_jd(first, second, DAY_FIRST_QUARTER_ANCHOR),
            9.125,
        )
        self.assertEqual(
            generic_anchor_jd(first, second, DAY_MIDPOINT_ANCHOR),
            9.25,
        )
        self.assertEqual(
            generic_anchor_jd(first, second, DAY_THIRD_QUARTER_ANCHOR),
            9.375,
        )
        self.assertEqual(
            generic_anchor_jd(first, second, SUNSET_ANCHOR),
            9.5,
        )
        self.assertEqual(
            generic_anchor_jd(first, second, NIGHT_FIRST_QUARTER_ANCHOR),
            9.625,
        )
        self.assertEqual(
            generic_anchor_jd(first, second, NIGHT_MIDPOINT_ANCHOR),
            9.75,
        )
        self.assertEqual(
            generic_anchor_jd(first, second, NIGHT_THIRD_QUARTER_ANCHOR),
            9.875,
        )

    def test_night_quarter_requires_following_sunrise(self):
        with self.assertRaisesRegex(
            ValueError,
            "requires the following sunrise",
        ):
            generic_anchor_jd(
                self.days[0],
                None,
                NIGHT_FIRST_QUARTER_ANCHOR,
            )

    def test_anchor_mapping(self):
        expected = {
            "Ugadi": SUNRISE_ANCHOR,
            "Yajur Upakarma": SUNRISE_ANCHOR,
            "Vasanta Panchami": DAY_FIRST_QUARTER_ANCHOR,
            "Rama Navami": DAY_MIDPOINT_ANCHOR,
            "Mahanavami (Puja)": DAY_THIRD_QUARTER_ANCHOR,
            "Narasimha Jayanti": SUNSET_ANCHOR,
            "Deepavali": NIGHT_FIRST_QUARTER_ANCHOR,
            "Kama Dahana (Holi)": NIGHT_FIRST_QUARTER_ANCHOR,
            "Dhana Trayodashi": NIGHT_FIRST_QUARTER_ANCHOR,
            "Janmashtami": NIGHT_MIDPOINT_ANCHOR,
            "Naraka Chaturdashi": NIGHT_THIRD_QUARTER_ANCHOR,
        }
        for name, anchor in expected.items():
            with self.subTest(name=name):
                self.assertEqual(
                    generic_anchor_for_rule(festival_rule(name)),
                    anchor,
                )

    def test_contained_anchor_selects_its_date(self):
        self.assertEqual(
            self.select(festival_rule("Rama Navami"), (10.2, 10.3)),
            [date(2030, 4, 11)],
        )

    def test_multiple_contained_anchors_prefer_nearest_to_tithi_midpoint(self):
        self.assertEqual(
            self.select(festival_rule("Vasavi Jayanti"), (9.0, 10.8)),
            [date(2030, 4, 11)],
        )

    def test_missing_anchor_uses_nearest_then_earlier_date(self):
        self.assertEqual(
            self.select(festival_rule("Rama Navami"), (9.7, 9.8)),
            [date(2030, 4, 10)],
        )

    def test_tithi_end_at_anchor_is_excluded(self):
        self.assertEqual(
            self.select(festival_rule("Rama Navami"), (9.25, 10.25)),
            [date(2030, 4, 10)],
        )

    def test_non_ugadi_adhika_occurrence_is_excluded(self):
        self.assertEqual(
            self.select(
                festival_rule("Rama Navami"),
                (10.2, 10.3),
                is_adhika=True,
            ),
            [],
        )

    def test_policy_uses_context_records_and_anchor_specific_label(self):
        rule = festival_rule("Janmashtami")
        selected_date = self.days[1][0]
        with patch(
            "experimental.festival_rules.FESTIVAL_RULES",
            (rule,),
        ), patch(
            "experimental.festival_rules.collect_records",
            side_effect=[[self.days[1]], self.days],
        ), patch(
            "experimental.festival_rules.collect_moonrise_jds",
            return_value={},
        ), patch(
            "experimental.festival_rules.select_generic_anchor_festival_dates",
            return_value=[selected_date],
        ) as selector:
            _, entries = resolve_festivals(
                [],
                {},
                GENERIC_ANCHOR_FESTIVAL_POLICY,
                context_months=[(2030, 4)],
                context_data={(2030, 4): []},
            )

        selector.assert_called_once_with(self.days, rule)
        entry = next(item for item in entries if item[0] == rule.number)
        self.assertEqual(entry[2], "Janmashtami (Ratri Anchor)")

    def test_context_date_outside_target_range_is_filtered(self):
        rule = festival_rule("Yajur Upakarma")
        geopos = (77.0, 13.0, 0.0)
        with patch(
            "experimental.festival_rules.FESTIVAL_RULES",
            (rule,),
        ), patch(
            "experimental.festival_rules.collect_records",
            side_effect=[[self.days[1]], self.days],
        ), patch(
            "experimental.festival_rules.collect_moonrise_jds",
            return_value={},
        ), patch(
            "experimental.festival_rules.select_valid_generic_festival_dates",
            return_value=[self.days[0][0]],
        ) as selector:
            _, entries = resolve_festivals(
                [],
                {},
                GENERIC_ANCHOR_FESTIVAL_POLICY,
                context_months=[(2030, 4)],
                context_data={(2030, 4): []},
                geopos=geopos,
            )

        selector.assert_called_once_with(
            self.days,
            rule,
            geopos,
            selector=select_generic_anchor_festival_dates,
        )
        entry = next(item for item in entries if item[0] == rule.number)
        self.assertEqual(entry[1], "None")


if __name__ == "__main__":
    unittest.main()
