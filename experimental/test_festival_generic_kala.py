"""Tests for the Generic Kala festival policy."""

from datetime import date
import unittest
from unittest.mock import patch

from experimental.festival_rules import (
    APARAHNA_KALA,
    ARUNODAYA_KALA,
    GADHARATRI_KALA,
    GENERIC_KALA_FESTIVAL_POLICY,
    GENERIC_KALA_VALIDITY_BY_FESTIVAL,
    MADHYAHNA_KALA,
    MADHYARATRI_KALA,
    PRADOSHA_KALA,
    PRATAH_KALA,
    PURVAHNA_KALA,
    PURVARATRI_KALA,
    SANGAVA_KALA,
    SAYAHNA_KALA,
    SUNRISE_KALA,
    SUNSET_KALA,
    generic_kala_date_is_valid,
    generic_kala_for_rule,
    generic_kala_window,
    resolve_festivals,
    select_generic_kala_festival_dates,
    select_valid_generic_kala_festival_dates,
)
from experimental.festival_test_helpers import festival_rule, record


class GenericKalaPolicyTests(unittest.TestCase):
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

    def test_day_and_night_use_uniform_five_part_grid(self):
        first, second = self.days[:2]
        self.assertEqual(
            generic_kala_window(first, second, PRATAH_KALA),
            (9.0, 9.0 + 1 / 10),
        )
        self.assertEqual(
            generic_kala_window(first, second, SANGAVA_KALA),
            (9.0 + 1 / 10, 9.0 + 2 / 10),
        )
        self.assertEqual(
            generic_kala_window(first, second, PURVAHNA_KALA),
            (9.0, 9.0 + 2 / 10),
        )
        self.assertEqual(
            generic_kala_window(first, second, MADHYAHNA_KALA),
            (9.0 + 2 / 10, 9.0 + 3 / 10),
        )
        self.assertEqual(
            generic_kala_window(first, second, APARAHNA_KALA),
            (9.0 + 3 / 10, 9.0 + 4 / 10),
        )
        self.assertEqual(
            generic_kala_window(first, second, SAYAHNA_KALA),
            (9.0 + 4 / 10, 9.5),
        )
        self.assertEqual(
            generic_kala_window(first, second, PRADOSHA_KALA),
            (9.5, 9.5 + 1 / 10),
        )
        self.assertEqual(
            generic_kala_window(first, second, PURVARATRI_KALA),
            (9.5 + 1 / 10, 9.5 + 2 / 10),
        )
        self.assertEqual(
            generic_kala_window(first, second, MADHYARATRI_KALA),
            (9.5 + 2 / 10, 9.5 + 3 / 10),
        )
        self.assertEqual(
            generic_kala_window(first, second, GADHARATRI_KALA),
            (9.5 + 3 / 10, 9.5 + 4 / 10),
        )
        self.assertEqual(
            generic_kala_window(
                second,
                self.days[2],
                ARUNODAYA_KALA,
                first,
            ),
            (9.5 + 4 / 10, 10.0),
        )

    def test_agreed_festival_kala_assignments(self):
        self.assertEqual(
            generic_kala_for_rule(festival_rule("Ugadi")),
            SUNRISE_KALA,
        )
        self.assertEqual(
            generic_kala_for_rule(festival_rule("Rama Navami")),
            MADHYAHNA_KALA,
        )
        self.assertEqual(
            generic_kala_for_rule(festival_rule("Mahanavami (Puja)")),
            APARAHNA_KALA,
        )
        self.assertEqual(
            generic_kala_for_rule(festival_rule("Yajur Upakarma")),
            SUNRISE_KALA,
        )
        self.assertEqual(
            generic_kala_for_rule(festival_rule("Narasimha Jayanti")),
            SUNSET_KALA,
        )
        self.assertEqual(
            generic_kala_for_rule(festival_rule("Naraka Chaturdashi")),
            ARUNODAYA_KALA,
        )
        self.assertEqual(
            generic_kala_for_rule(festival_rule("Dhana Trayodashi")),
            PRADOSHA_KALA,
        )
        self.assertEqual(
            generic_kala_for_rule(festival_rule("Janmashtami")),
            MADHYARATRI_KALA,
        )

    def test_greater_kala_overlap_wins_competing_date(self):
        rule = festival_rule("Rama Navami")
        with patch(
            "experimental.festival_rules.generic_udaya_occurrences",
            return_value=[(date(2030, 4, 11), "1", False)],
        ), patch(
            "experimental.festival_rules.tithi_intervals",
            return_value=[(10.30, 11.25)],
        ):
            self.assertEqual(
                select_generic_kala_festival_dates(self.days, rule),
                [date(2030, 4, 12)],
            )

    def test_midpoint_distance_resolves_missing_window(self):
        rule = festival_rule("Rama Navami")
        with patch(
            "experimental.festival_rules.generic_udaya_occurrences",
            return_value=[(date(2030, 4, 11), "1", False)],
        ), patch(
            "experimental.festival_rules.tithi_intervals",
            return_value=[(10.85, 10.95)],
        ):
            self.assertEqual(
                select_generic_kala_festival_dates(self.days, rule),
                [date(2030, 4, 12)],
            )

    def test_sunrise_kala_uses_first_sunrise_for_vriddhi_tithi(self):
        rule = festival_rule("Ugadi")
        records = [
            record(date(2030, 3, 20), "S1"),
            record(date(2030, 3, 21), "S1"),
            record(date(2030, 3, 22), "S2"),
        ]
        self.assertEqual(
            select_generic_kala_festival_dates(records, rule),
            [date(2030, 3, 20)],
        )

    def test_yajur_defect_retries_bhadrapada_with_same_kala(self):
        rule = festival_rule("Yajur Upakarma")
        shravana_date = date(2030, 8, 15)
        bhadrapada_date = date(2030, 9, 14)
        with patch(
            "experimental.festival_rules.select_generic_kala_festival_dates",
            side_effect=[[shravana_date], [bhadrapada_date]],
        ) as selector, patch(
            "experimental.festival_rules.generic_kala_date_is_valid",
            side_effect=[False, True],
        ):
            self.assertEqual(
                select_valid_generic_kala_festival_dates(
                    [],
                    rule,
                    (0.0, 0.0, 0.0),
                ),
                [bhadrapada_date],
            )

        fallback_rule = selector.call_args_list[1].args[1]
        self.assertEqual(fallback_rule.masa, rule.masa + 1)
        self.assertEqual(
            generic_kala_for_rule(fallback_rule),
            SUNRISE_KALA,
        )

    def test_yajur_returns_none_when_fallback_is_also_defective(self):
        rule = festival_rule("Yajur Upakarma")
        with patch(
            "experimental.festival_rules.select_generic_kala_festival_dates",
            side_effect=[
                [date(2030, 8, 15)],
                [date(2030, 9, 14)],
            ],
        ), patch(
            "experimental.festival_rules.generic_kala_date_is_valid",
            side_effect=[False, False],
        ):
            self.assertEqual(
                select_valid_generic_kala_festival_dates(
                    [],
                    rule,
                    (0.0, 0.0, 0.0),
                ),
                [],
            )

    def test_upakarma_overlay_requires_geographic_position(self):
        rule = festival_rule("Yajur Upakarma")
        overlay = GENERIC_KALA_VALIDITY_BY_FESTIVAL[rule.number]
        with self.assertRaisesRegex(
            ValueError,
            "requires a geographic position",
        ):
            generic_kala_date_is_valid(
                {},
                date(2030, 8, 15),
                overlay,
                None,
            )

    def test_policy_bypasses_traditional_plain_tithi_selector(self):
        rule = festival_rule("Rama Navami")
        selected_date = date(2030, 4, 11)
        with patch(
            "experimental.festival_rules.FESTIVAL_RULES",
            (rule,),
        ), patch(
            "experimental.festival_rules.collect_records",
            return_value=[self.days[1]],
        ), patch(
            "experimental.festival_rules.collect_moonrise_jds",
            return_value={},
        ), patch(
            "experimental.festival_rules.select_generic_kala_festival_dates",
            return_value=[selected_date],
        ) as selector, patch(
            "experimental.festival_rules.select_rama_navami_dates",
            side_effect=AssertionError("traditional selector called"),
        ):
            _, entries = resolve_festivals(
                [],
                {},
                GENERIC_KALA_FESTIVAL_POLICY,
            )

        selector.assert_called_once_with([self.days[1]], rule)
        entry = next(item for item in entries if item[0] == rule.number)
        self.assertEqual(entry[1], "Apr 11")

    def test_janmashtami_label_describes_madhyaratri_window(self):
        rule = festival_rule("Janmashtami")
        selected_date = self.days[1][0]
        with patch(
            "experimental.festival_rules.FESTIVAL_RULES",
            (rule,),
        ), patch(
            "experimental.festival_rules.collect_records",
            return_value=[self.days[1]],
        ), patch(
            "experimental.festival_rules.collect_moonrise_jds",
            return_value={},
        ), patch(
            "experimental.festival_rules.select_generic_kala_festival_dates",
            return_value=[selected_date],
        ):
            _, entries = resolve_festivals(
                [],
                {},
                GENERIC_KALA_FESTIVAL_POLICY,
            )

        entry = next(item for item in entries if item[0] == rule.number)
        self.assertEqual(entry[2], "Janmashtami (Madhyaratri Kala)")


if __name__ == "__main__":
    unittest.main()
