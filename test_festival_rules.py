"""Regression tests for Dharma Sindhu festival-date decisions."""

from datetime import date
import unittest
from unittest.mock import patch

import panchanga

from festival_rules import (
    APARAHNA_KALA,
    ARUNODAYA_HOURS,
    DAY_MIDPOINT_ANCHOR,
    FESTIVAL_RULES,
    GENERIC_ANCHOR_FESTIVAL_POLICY,
    GENERIC_KALA_FESTIVAL_POLICY,
    GENERIC_KALA_VALIDITY_BY_FESTIVAL,
    GENERIC_UDAYA_FESTIVAL_POLICY,
    ARUNODAYA_KALA,
    GADHARATRI_KALA,
    MADHYAHNA_KALA,
    MADHYARATRI_KALA,
    NIGHT_MIDPOINT_ANCHOR,
    PREDAWN_ANCHOR,
    PRADOSHA_KALA,
    PRATAH_KALA,
    PURVAHNA_KALA,
    PURVARATRI_KALA,
    SANGAVA_KALA,
    SAYAHNA_KALA,
    SUNRISE_ANCHOR,
    SUNRISE_KALA,
    SUNSET_ANCHOR,
    SUNSET_KALA,
    FestivalRule,
    VARAMAHALAKSHMI_RULE,
    eclipse_or_sankranti_in_window,
    format_festival_dates,
    generic_anchor_for_rule,
    generic_anchor_jd,
    generic_udaya_occurrences,
    generic_kala_for_rule,
    generic_kala_date_is_valid,
    generic_kala_window,
    nakshatra_overlaps,
    plain_tithi_number,
    resolve_festivals,
    select_aksaya_trtiya_dates,
    select_ayudha_puja_dates,
    select_bali_padyami_dates,
    select_gowri_habba_dates,
    select_guru_purnima_dates,
    select_kama_dahana_dates,
    select_janmashtami_dates,
    select_maha_shivaratri_dates,
    select_naga_panchami_dates,
    select_narasimha_jayanti_dates,
    select_raksha_bandhan_dates,
    select_rama_navami_dates,
    select_ratha_saptami_dates,
    select_rigveda_upakarma_dates,
    select_taittiriya_apastamba_upakarma_dates,
    select_taittiriya_purnima_dates,
    select_ugadi_dates,
    select_vasavi_atmarpana_dates,
    select_vasavi_jayanti_dates,
    select_varamahalakshmi_dates,
    select_vaikuntha_ekadashi_dates,
    select_vasanta_panchami_dates,
    select_vijaya_dasami_dates,
    select_vsn_jayanti_dates,
    select_dhana_trayodashi_dates,
    select_makara_sankranti_dates,
    select_smarta_janmashtami_dates,
    select_dhanvantari_jayanti_dates,
    select_durga_ashtami_observance_dates,
    select_durga_ashtami_puja_dates,
    select_mahalaya_amavasya_dates,
    select_mahanavami_puja_dates,
    select_naraka_chaturdashi_dates,
    select_dasara_dates,
    select_deepavali_dates,
    select_gita_jayanti_dates,
    select_generic_udaya_festival_dates,
    select_generic_anchor_festival_dates,
    select_generic_kala_festival_dates,
    select_valid_generic_kala_festival_dates,
    select_kama_dahana_dates,
)


def record(day, tithi, masa="1", is_adhika=False):
    """Build the compact record shape consumed by festival selectors."""
    return (day, tithi, masa, is_adhika, 1.0, 0.0, 0.5)


def festival_rule(name):
    return next(rule for rule in FESTIVAL_RULES if rule.name == name)


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
            "festival_rules.generic_udaya_occurrences",
            return_value=[(date(2030, 4, 11), "1", False)],
        ), patch(
            "festival_rules.tithi_intervals",
            return_value=[(10.30, 11.25)],
        ):
            self.assertEqual(
                select_generic_kala_festival_dates(self.days, rule),
                [date(2030, 4, 12)],
            )

    def test_midpoint_distance_resolves_missing_window(self):
        rule = festival_rule("Rama Navami")
        with patch(
            "festival_rules.generic_udaya_occurrences",
            return_value=[(date(2030, 4, 11), "1", False)],
        ), patch(
            "festival_rules.tithi_intervals",
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
            "festival_rules.select_generic_kala_festival_dates",
            side_effect=[[shravana_date], [bhadrapada_date]],
        ) as selector, patch(
            "festival_rules.generic_kala_date_is_valid",
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
            "festival_rules.select_generic_kala_festival_dates",
            side_effect=[
                [date(2030, 8, 15)],
                [date(2030, 9, 14)],
            ],
        ), patch(
            "festival_rules.generic_kala_date_is_valid",
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
            "festival_rules.FESTIVAL_RULES",
            (rule,),
        ), patch(
            "festival_rules.collect_records",
            return_value=[self.days[1]],
        ), patch(
            "festival_rules.collect_moonrise_jds",
            return_value={},
        ), patch(
            "festival_rules.select_generic_kala_festival_dates",
            return_value=[selected_date],
        ) as selector, patch(
            "festival_rules.select_rama_navami_dates",
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
            "festival_rules.FESTIVAL_RULES",
            (rule,),
        ), patch(
            "festival_rules.collect_records",
            return_value=[self.days[1]],
        ), patch(
            "festival_rules.collect_moonrise_jds",
            return_value={},
        ), patch(
            "festival_rules.select_generic_kala_festival_dates",
            return_value=[selected_date],
        ):
            _, entries = resolve_festivals(
                [],
                {},
                GENERIC_KALA_FESTIVAL_POLICY,
            )

        entry = next(item for item in entries if item[0] == rule.number)
        self.assertEqual(entry[2], "Janmashtami (Madhyaratri Kala)")


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
            "festival_rules.generic_udaya_occurrences",
            return_value=[
                (
                    date(2030, 4, 11),
                    str(rule.masa),
                    is_adhika,
                )
            ],
        ), patch(
            "festival_rules.tithi_intervals",
            return_value=[interval],
        ):
            return select_generic_anchor_festival_dates(self.days, rule)

    def test_five_exact_anchor_calculations(self):
        first, second = self.days[:2]
        self.assertEqual(
            generic_anchor_jd(first, second, SUNRISE_ANCHOR),
            9.0,
        )
        self.assertEqual(
            generic_anchor_jd(first, second, DAY_MIDPOINT_ANCHOR),
            9.25,
        )
        self.assertEqual(
            generic_anchor_jd(first, second, SUNSET_ANCHOR),
            9.5,
        )
        self.assertEqual(
            generic_anchor_jd(first, second, NIGHT_MIDPOINT_ANCHOR),
            9.75,
        )
        self.assertEqual(
            generic_anchor_jd(first, second, PREDAWN_ANCHOR),
            9.0 - ARUNODAYA_HOURS / 24,
        )

    def test_night_midpoint_requires_following_sunrise(self):
        with self.assertRaisesRegex(
            ValueError,
            "requires the following sunrise",
        ):
            generic_anchor_jd(
                self.days[0],
                None,
                NIGHT_MIDPOINT_ANCHOR,
            )

    def test_kala_groups_collapse_to_reduced_anchor_vocabulary(self):
        expected = {
            "Ugadi": SUNRISE_ANCHOR,
            "Yajur Upakarma": SUNRISE_ANCHOR,
            "Vasanta Panchami": DAY_MIDPOINT_ANCHOR,
            "Rama Navami": DAY_MIDPOINT_ANCHOR,
            "Mahanavami (Puja)": DAY_MIDPOINT_ANCHOR,
            "Narasimha Jayanti": SUNSET_ANCHOR,
            "Dhana Trayodashi": SUNSET_ANCHOR,
            "Janmashtami": NIGHT_MIDPOINT_ANCHOR,
            "Naraka Chaturdashi": PREDAWN_ANCHOR,
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
            "festival_rules.FESTIVAL_RULES",
            (rule,),
        ), patch(
            "festival_rules.collect_records",
            side_effect=[[self.days[1]], self.days],
        ), patch(
            "festival_rules.collect_moonrise_jds",
            return_value={},
        ), patch(
            "festival_rules.select_generic_anchor_festival_dates",
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
        self.assertEqual(entry[2], "Janmashtami (Night-Midpoint Anchor)")

    def test_context_date_outside_target_range_is_filtered(self):
        rule = festival_rule("Yajur Upakarma")
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
            "festival_rules.select_generic_anchor_festival_dates",
            return_value=[self.days[0][0]],
        ):
            _, entries = resolve_festivals(
                [],
                {},
                GENERIC_ANCHOR_FESTIVAL_POLICY,
                context_months=[(2030, 4)],
                context_data={(2030, 4): []},
            )

        entry = next(item for item in entries if item[0] == rule.number)
        self.assertEqual(entry[1], "None")


class UgadiRuleTests(unittest.TestCase):
    rule = FESTIVAL_RULES[0]

    def test_prefers_earlier_of_two_sunrise_pratipadas(self):
        records = [
            record(date(2030, 3, 20), "S1"),
            record(date(2030, 3, 21), "S1"),
        ]
        self.assertEqual(
            select_ugadi_dates(records, self.rule),
            [date(2030, 3, 20)],
        )

    def test_uses_earlier_day_when_pratipada_is_skipped_at_sunrise(self):
        records = [record(date(2030, 3, 21), "S2")]
        self.assertEqual(
            select_ugadi_dates(records, self.rule),
            [date(2030, 3, 20)],
        )

    def test_prefers_adhika_chaitra_year_opening(self):
        records = [
            record(
                date(2030, 3, 20),
                "S1",
                masa="A1",
                is_adhika=True,
            ),
            record(date(2030, 4, 19), "S1"),
        ]
        self.assertEqual(
            select_ugadi_dates(records, self.rule),
            [date(2030, 3, 20)],
        )

    def test_returns_each_ugadi_in_a_multi_year_display_range(self):
        records = [
            record(date(2030, 3, 20), "S1"),
            record(date(2031, 3, 9), "S1"),
        ]
        self.assertEqual(
            select_ugadi_dates(records, self.rule),
            [date(2030, 3, 20), date(2031, 3, 9)],
        )


class RamaNavamiRuleTests(unittest.TestCase):
    rule = FESTIVAL_RULES[1]
    records = [
        record(date(2030, 4, 10), "S8"),
        record(date(2030, 4, 11), "S9"),
    ]

    def test_prefers_later_day_when_both_madhyahnas_have_navami(self):
        with patch(
            "festival_rules.tithi_overlap_hours",
            side_effect=[1.0, 1.0],
        ):
            self.assertEqual(
                select_rama_navami_dates(self.records, self.rule),
                [date(2030, 4, 11)],
            )

    def test_uses_only_day_whose_madhyahna_has_navami(self):
        with patch(
            "festival_rules.tithi_overlap_hours",
            side_effect=[1.0, 0.0],
        ):
            self.assertEqual(
                select_rama_navami_dates(self.records, self.rule),
                [date(2030, 4, 10)],
            )


class AkshayaTritiyaRuleTests(unittest.TestCase):
    rule = FESTIVAL_RULES[2]
    records = [
        record(date(2030, 5, 5), "S2", masa="2"),
        record(date(2030, 5, 6), "S3", masa="2"),
    ]

    def test_prefers_later_day_when_both_yugadi_windows_qualify(self):
        with patch(
            "festival_rules.tithi_overlap_hours",
            side_effect=[1.0, 1.0],
        ):
            self.assertEqual(
                select_aksaya_trtiya_dates(self.records, self.rule),
                [date(2030, 5, 6)],
            )

    def test_uses_earlier_day_when_later_window_has_no_tritiya(self):
        with patch(
            "festival_rules.tithi_overlap_hours",
            side_effect=[1.0, 0.0],
        ):
            self.assertEqual(
                select_aksaya_trtiya_dates(self.records, self.rule),
                [date(2030, 5, 5)],
            )

    def test_excludes_adhika_vaishakha_from_public_festival_marker(self):
        records = [
            record(
                date(2030, 4, 6),
                "S3",
                masa="2",
                is_adhika=True,
            ),
            record(date(2030, 5, 6), "S3", masa="2"),
        ]
        with patch(
            "festival_rules.tithi_overlap_hours",
            return_value=1.0,
        ):
            self.assertEqual(
                select_aksaya_trtiya_dates(records, self.rule),
                [date(2030, 5, 6)],
            )


class RuleStatusTests(unittest.TestCase):
    def test_festival_markers_remain_sequential(self):
        numbers = sorted(
            [rule.number for rule in FESTIVAL_RULES]
            + [VARAMAHALAKSHMI_RULE.number]
        )
        self.assertEqual(numbers, list(range(1, len(numbers) + 1)))

    def test_vasavi_jayanti_uses_documented_generic_udaya_policy(self):
        rule = FESTIVAL_RULES[3]
        self.assertEqual(rule.status, "generic-udaya")
        self.assertIsNone(rule.source)

    def test_varamahalakshmi_uses_ttd_regional_rule(self):
        self.assertEqual(VARAMAHALAKSHMI_RULE.status, "regional")
        self.assertIsNone(VARAMAHALAKSHMI_RULE.source)

    def test_ayudha_puja_is_documented_as_a_regional_rule(self):
        rule = festival_rule("Ayudha Puja")
        self.assertEqual(rule.status, "regional")
        self.assertIn("drikpanchang.com", rule.source)

    def test_gita_jayanti_uses_documented_generic_udaya_policy(self):
        rule = festival_rule("Gita Jayanti")
        self.assertEqual(rule.status, "generic-udaya")
        self.assertIsNone(rule.source)

    def test_vasavi_atmarpana_uses_documented_generic_udaya_policy(self):
        rule = festival_rule("Vasavi Atmarpana")
        self.assertEqual(rule.status, "generic-udaya")
        self.assertIsNone(rule.source)

    def test_vsn_jayanti_uses_documented_generic_udaya_policy(self):
        rule = festival_rule("VSN Jayanti")
        self.assertEqual(rule.status, "generic-udaya")
        self.assertIsNone(rule.source)

    def test_implemented_rules_are_not_left_provisional(self):
        for name in (
            "Ganesha Chaturthi",
            "Durga Ashtami",
            "Naraka Chaturdashi",
            "Deepavali",
        ):
            with self.subTest(name=name):
                rule = festival_rule(name)
                self.assertEqual(rule.status, "dharmasindhu")
                self.assertIsNotNone(rule.source)


class VasaviJayantiRuleTests(unittest.TestCase):
    rule = festival_rule("Vasavi Jayanti")

    def test_selects_single_sunrise_vyapini_dashami(self):
        records = [
            record(date(2030, 5, 4), "S9", masa="2"),
            record(date(2030, 5, 5), "S10", masa="2"),
            record(date(2030, 5, 6), "S11", masa="2"),
        ]
        self.assertEqual(
            select_vasavi_jayanti_dates(records, self.rule),
            [date(2030, 5, 5)],
        )

    def test_vriddhi_dashami_uses_first_sunrise(self):
        records = [
            record(date(2030, 5, 4), "S10", masa="2"),
            record(date(2030, 5, 5), "S10", masa="2"),
            record(date(2030, 5, 6), "S11", masa="2"),
        ]
        self.assertEqual(
            select_vasavi_jayanti_dates(records, self.rule),
            [date(2030, 5, 4)],
        )

    def test_kshaya_dashami_uses_civil_day_containing_dashami(self):
        records = [
            record(date(2030, 5, 4), "S9", masa="2"),
            record(date(2030, 5, 5), "S11", masa="2"),
        ]
        with patch(
            "festival_rules.tithi_intervals",
            return_value=[(0.1, 0.9)],
        ):
            self.assertEqual(
                select_vasavi_jayanti_dates(records, self.rule),
                [date(2030, 5, 4)],
            )


class VasaviAtmarpanaRuleTests(unittest.TestCase):
    rule = festival_rule("Vasavi Atmarpana")

    def test_selects_single_sunrise_vyapini_dwitiya(self):
        records = [
            record(date(2030, 2, 4), "S1", masa="11"),
            record(date(2030, 2, 5), "S2", masa="11"),
            record(date(2030, 2, 6), "S3", masa="11"),
        ]
        self.assertEqual(
            select_vasavi_atmarpana_dates(records, self.rule),
            [date(2030, 2, 5)],
        )

    def test_vriddhi_dwitiya_uses_first_sunrise(self):
        records = [
            record(date(2030, 2, 4), "S2", masa="11"),
            record(date(2030, 2, 5), "S2", masa="11"),
            record(date(2030, 2, 6), "S3", masa="11"),
        ]
        self.assertEqual(
            select_vasavi_atmarpana_dates(records, self.rule),
            [date(2030, 2, 4)],
        )

    def test_kshaya_dwitiya_uses_civil_day_containing_dwitiya(self):
        records = [
            record(date(2030, 2, 4), "S1", masa="11"),
            record(date(2030, 2, 5), "S3", masa="11"),
        ]
        with patch(
            "festival_rules.tithi_intervals",
            return_value=[(0.1, 0.9)],
        ):
            self.assertEqual(
                select_vasavi_atmarpana_dates(records, self.rule),
                [date(2030, 2, 4)],
            )


class VsnJayantiRuleTests(unittest.TestCase):
    rule = festival_rule("VSN Jayanti")

    def test_selects_single_sunrise_vyapini_ekadashi(self):
        records = [
            record(date(2030, 2, 4), "S10", masa="11"),
            record(date(2030, 2, 5), "S11", masa="11"),
            record(date(2030, 2, 6), "S12", masa="11"),
        ]
        self.assertEqual(
            select_vsn_jayanti_dates(records, self.rule),
            [date(2030, 2, 5)],
        )

    def test_vriddhi_ekadashi_marker_uses_first_sunrise(self):
        records = [
            record(date(2030, 2, 4), "S11", masa="11"),
            record(date(2030, 2, 5), "S11", masa="11"),
            record(date(2030, 2, 6), "S12", masa="11"),
        ]
        self.assertEqual(
            select_vsn_jayanti_dates(records, self.rule),
            [date(2030, 2, 4)],
        )

    def test_kshaya_ekadashi_uses_civil_day_containing_ekadashi(self):
        records = [
            record(date(2030, 2, 4), "S10", masa="11"),
            record(date(2030, 2, 5), "S12", masa="11"),
        ]
        with patch(
            "festival_rules.tithi_intervals",
            return_value=[(0.1, 0.9)],
        ):
            self.assertEqual(
                select_vsn_jayanti_dates(records, self.rule),
                [date(2030, 2, 4)],
            )


class GitaJayantiRuleTests(unittest.TestCase):
    rule = festival_rule("Gita Jayanti")

    def test_selects_single_sunrise_vyapini_ekadashi(self):
        records = [
            record(date(2030, 12, 4), "S10", masa="9"),
            record(date(2030, 12, 5), "S11", masa="9"),
            record(date(2030, 12, 6), "S12", masa="9"),
        ]
        self.assertEqual(
            select_gita_jayanti_dates(records, self.rule),
            [date(2030, 12, 5)],
        )

    def test_vriddhi_ekadashi_marker_uses_first_sunrise(self):
        records = [
            record(date(2030, 12, 4), "S11", masa="9"),
            record(date(2030, 12, 5), "S11", masa="9"),
            record(date(2030, 12, 6), "S12", masa="9"),
        ]
        self.assertEqual(
            select_gita_jayanti_dates(records, self.rule),
            [date(2030, 12, 4)],
        )

    def test_kshaya_ekadashi_uses_civil_day_containing_ekadashi(self):
        records = [
            record(date(2030, 12, 4), "S10", masa="9"),
            record(date(2030, 12, 5), "S12", masa="9"),
        ]
        with patch(
            "festival_rules.tithi_intervals",
            return_value=[(0.1, 0.9)],
        ):
            self.assertEqual(
                select_gita_jayanti_dates(records, self.rule),
                [date(2030, 12, 4)],
            )


class VaramahalakshmiRuleTests(unittest.TestCase):
    def test_uses_immediately_preceding_friday(self):
        records = [
            record(date(2030, 8, 9), "S14", masa="5"),
            record(date(2030, 8, 10), "S15", masa="5"),
            record(date(2030, 8, 11), "K1", masa="5"),
        ]
        self.assertEqual(
            select_varamahalakshmi_dates(records),
            [date(2030, 8, 9)],
        )

    def test_friday_purnima_moves_seven_days_earlier(self):
        records = [
            record(date(2030, 8, 15), "S14", masa="5"),
            record(date(2030, 8, 16), "S15", masa="5"),
            record(date(2030, 8, 17), "K1", masa="5"),
        ]
        self.assertEqual(
            select_varamahalakshmi_dates(records),
            [date(2030, 8, 9)],
        )

    def test_vriddhi_purnima_uses_first_sunrise_as_anchor(self):
        records = [
            record(date(2030, 8, 8), "S14", masa="5"),
            record(date(2030, 8, 9), "S15", masa="5"),
            record(date(2030, 8, 10), "S15", masa="5"),
        ]
        self.assertEqual(
            select_varamahalakshmi_dates(records),
            [date(2030, 8, 2)],
        )

    def test_kshaya_purnima_uses_containing_day_as_anchor(self):
        records = [
            record(date(2030, 8, 10), "S14", masa="5"),
            record(date(2030, 8, 11), "K1", masa="6"),
        ]
        with patch(
            "festival_rules.tithi_intervals",
            return_value=[(0.1, 0.9)],
        ):
            self.assertEqual(
                select_varamahalakshmi_dates(records),
                [date(2030, 8, 9)],
            )


class NarasimhaJayantiRuleTests(unittest.TestCase):
    rule = FESTIVAL_RULES[4]
    records = [
        record(date(2030, 5, 18), "S14", masa="2"),
        record(date(2030, 5, 19), "S14", masa="2"),
    ]

    def test_prefers_later_day_when_both_sunsets_have_caturdashi(self):
        with patch(
            "festival_rules.tithi_number_at",
            side_effect=[14, 14],
        ):
            self.assertEqual(
                select_narasimha_jayanti_dates(self.records, self.rule),
                [date(2030, 5, 19)],
            )

    def test_uses_only_sunset_with_caturdashi(self):
        with patch(
            "festival_rules.tithi_number_at",
            side_effect=[14, 15],
        ):
            self.assertEqual(
                select_narasimha_jayanti_dates(self.records, self.rule),
                [date(2030, 5, 18)],
            )


class GuruPurnimaRuleTests(unittest.TestCase):
    rule = FESTIVAL_RULES[5]

    def test_uses_later_day_with_six_ghatis_of_purnima(self):
        records = [
            record(date(2030, 7, 15), "S15", masa="4"),
            (
                date(2030, 7, 16),
                "S15",
                "4",
                False,
                2.5,
                0.0,
                0.5,
            ),
        ]
        self.assertEqual(
            select_guru_purnima_dates(records, self.rule),
            [date(2030, 7, 16)],
        )

    def test_rejects_short_later_purnima(self):
        records = [
            record(date(2030, 7, 15), "S15", masa="4"),
            (
                date(2030, 7, 16),
                "S15",
                "4",
                False,
                2.0,
                0.0,
                0.5,
            ),
        ]
        self.assertEqual(
            select_guru_purnima_dates(records, self.rule),
            [date(2030, 7, 15)],
        )

    def test_kshaya_purnima_uses_civil_day_containing_purnima(self):
        records = [
            (date(2083, 7, 28), "S14", "4", False, 1.0, 10.0, 10.5),
            (date(2083, 7, 29), "K1", "4", False, 1.0, 11.0, 11.5),
        ]
        with patch(
            "festival_rules.tithi_intervals",
            return_value=[(10.1, 10.9)],
        ):
            self.assertEqual(
                select_guru_purnima_dates(records, self.rule),
                [date(2083, 7, 28)],
            )


class NagaPanchamiRuleTests(unittest.TestCase):
    rule = FESTIVAL_RULES[6]

    def test_uses_later_panchami_with_three_muhurtas(self):
        records = [
            record(date(2030, 8, 4), "S5", masa="5"),
            (date(2030, 8, 5), "S5", "5", False, 2.5, 0.0, 0.5),
        ]
        self.assertEqual(
            select_naga_panchami_dates(records, self.rule),
            [date(2030, 8, 5)],
        )

    def test_rejects_short_later_panchami(self):
        records = [
            record(date(2030, 8, 4), "S5", masa="5"),
            (date(2030, 8, 5), "S5", "5", False, 2.0, 0.0, 0.5),
        ]
        self.assertEqual(
            select_naga_panchami_dates(records, self.rule),
            [date(2030, 8, 4)],
        )

    def test_kshaya_panchami_uses_civil_day_containing_panchami(self):
        records = [
            (date(2045, 8, 16), "S4", "5", False, 1.0, 10.0, 10.5),
            (date(2045, 8, 17), "S6", "5", False, 1.0, 11.0, 11.5),
        ]
        with patch(
            "festival_rules.tithi_intervals",
            return_value=[(10.1, 10.9)],
        ):
            self.assertEqual(
                select_naga_panchami_dates(records, self.rule),
                [date(2045, 8, 16)],
            )


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
            "festival_rules.nakshatra_number_at",
            side_effect=lambda jd: 22 if 10.9 < jd < 11.1 else 21,
        ), patch(
            "festival_rules.nakshatra_overlap_hours",
            return_value=2.0,
        ), patch(
            "festival_rules.upakarma_date_is_contaminated",
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
            "festival_rules.nakshatra_number_at",
            return_value=22,
        ), patch(
            "festival_rules.nakshatra_overlap_hours",
            side_effect=[3.0, 2.4],
        ), patch(
            "festival_rules.upakarma_date_is_contaminated",
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
            "festival_rules.nakshatra_number_at",
            return_value=22,
        ), patch(
            "festival_rules.nakshatra_overlap_hours",
            side_effect=[3.0, 2.0],
        ), patch(
            "festival_rules.upakarma_date_is_contaminated",
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
            "festival_rules.nakshatra_number_at",
            side_effect=lambda jd: 22 if 29.9 < jd < 30.1 else 1,
        ), patch(
            "festival_rules.nakshatra_overlap_hours",
            return_value=2.0,
        ), patch(
            "festival_rules.upakarma_date_is_contaminated",
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
            "festival_rules.nakshatra_number_at",
            return_value=1,
        ), patch(
            "festival_rules.upakarma_date_is_contaminated",
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
            "festival_rules.nakshatra_number_at",
            return_value=22,
        ), patch(
            "festival_rules.nakshatra_overlap_hours",
            return_value=2.0,
        ), patch(
            "festival_rules.upakarma_date_is_contaminated",
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
            "festival_rules.panchanga.solar_longitude",
            return_value=10.0,
        ), patch(
            "festival_rules.panchanga.swe.lun_eclipse_when_loc",
            return_value=(
                panchanga.swe.ECL_PARTIAL,
                self.eclipse_times(50.0, 49.9, 50.1),
                (),
            ),
        ), patch(
            "festival_rules.panchanga.swe.sol_eclipse_when_loc",
            return_value=(0, self.solar_times(60.0, 60.1), ()),
        ):
            self.assertFalse(
                eclipse_or_sankranti_in_window(10.0, 11.0, self.geopos)
            )

    def test_visible_contacts_count_when_maximum_precedes_window(self):
        with patch(
            "festival_rules.panchanga.solar_longitude",
            return_value=10.0,
        ), patch(
            "festival_rules.panchanga.swe.lun_eclipse_when_loc",
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
            "festival_rules.panchanga.solar_longitude",
            return_value=10.0,
        ), patch(
            "festival_rules.panchanga.swe.lun_eclipse_when_loc",
            return_value=(
                panchanga.swe.ECL_PENUMBRAL,
                self.eclipse_times(10.2, 10.1, 10.3),
                (),
            ),
        ), patch(
            "festival_rules.panchanga.swe.sol_eclipse_when_loc",
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
            "festival_rules.tithi_intervals",
            return_value=[(10.04, 11.08)],
        ):
            self.assertEqual(
                select_taittiriya_purnima_dates(records, 5),
                [date(2030, 8, 15)],
            )

    def test_taittiriyas_use_later_day_with_two_muhurtas(self):
        with patch(
            "festival_rules.tithi_intervals",
            return_value=[(10.1, 11.2)],
        ), patch(
            "festival_rules.eclipse_or_sankranti_in_window",
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
            "festival_rules.tithi_intervals",
            return_value=[(10.1, 11.05)],
        ), patch(
            "festival_rules.eclipse_or_sankranti_in_window",
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
            "festival_rules.tithi_intervals",
            return_value=[(10.1, 10.9)],
        ), patch(
            "festival_rules.eclipse_or_sankranti_in_window",
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
            "festival_rules.tithi_intervals",
            side_effect=[
                [(10.1, 11.2)],
                [(40.1, 41.05)],
            ],
        ), patch(
            "festival_rules.upakarma_date_is_contaminated",
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
            "festival_rules.tithi_intervals",
            side_effect=[
                [(10.1, 11.2)],
                [(40.1, 41.2)],
            ],
        ), patch(
            "festival_rules.upakarma_date_is_contaminated",
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
            "festival_rules.tithi_intervals",
            return_value=[(40.1, 40.9)],
        ):
            self.assertEqual(
                select_taittiriya_purnima_dates(records, 6),
                [date(2030, 9, 13)],
            )

    def test_rule_allows_both_branch_dates_to_be_defective(self):
        self.assertTrue(self.rule.allow_empty)


class RakshaBandhanRuleTests(unittest.TestCase):
    rule = festival_rule("Raksha Bandhan")

    @staticmethod
    def records(remainder):
        return [
            (date(2030, 8, 14), "S14", "5", False, 1.0, 10.0, 10.5),
            (date(2030, 8, 15), "S15", "5", False, remainder, 11.0, 11.5),
            (date(2030, 8, 16), "K1", "5", False, 1.0, 12.0, 12.5),
        ]

    def test_short_later_purnima_uses_previous_pradosha(self):
        with patch(
            "festival_rules.has_bhadra_free_purnima",
            return_value=True,
        ):
            self.assertEqual(
                select_raksha_bandhan_dates(
                    self.records(1.0),
                    self.rule,
                ),
                [date(2030, 8, 14)],
            )

    def test_long_later_purnima_uses_later_day(self):
        with patch(
            "festival_rules.has_bhadra_free_purnima",
            return_value=True,
        ):
            self.assertEqual(
                select_raksha_bandhan_dates(
                    self.records(3.0),
                    self.rule,
                ),
                [date(2030, 8, 15)],
            )

    def test_kshaya_purnima_uses_bhadra_free_pradosha_day(self):
        records = [
            (date(2031, 8, 2), "S14", "5", False, 1.0, 10.0, 10.5),
            (date(2031, 8, 3), "K1", "5", False, 1.0, 11.0, 11.5),
        ]
        with patch(
            "festival_rules.tithi_intervals",
            return_value=[(10.1, 10.9)],
        ), patch(
            "festival_rules.has_bhadra_free_purnima",
            side_effect=[False, True],
        ):
            self.assertEqual(
                select_raksha_bandhan_dates(records, self.rule),
                [date(2031, 8, 2)],
            )


class JanmashtamiRuleTests(unittest.TestCase):
    rule = festival_rule("Janmashtami")
    records = [
        (date(2030, 9, 1), "K8", "5", False, 1.0, 10.0, 10.5),
        (date(2030, 9, 2), "K8", "5", False, 1.0, 11.0, 11.5),
        (date(2030, 9, 3), "K9", "5", False, 1.0, 12.0, 12.5),
    ]

    def test_saptami_viddha_rejected(self):
        # 22 is Saptami, 23 is Ashtami
        with patch(
            "festival_rules.tithi_intervals",
            side_effect=[[(10.0, 11.0)], [(11.0, 12.0)]],
        ), patch(
            "festival_rules.tithi_number_at",
            side_effect=[22, 23], # Day 1 is Saptami at sunrise, Day 2 is Ashtami at sunrise
        ):
            self.assertEqual(
                select_janmashtami_dates(self.records, self.rule),
                [date(2030, 9, 2)],
            )

    def test_shuddha_ashtami_accepted(self):
        with patch(
            "festival_rules.tithi_intervals",
            side_effect=[[(10.0, 11.0)], [(11.0, 12.0)]],
        ), patch(
            "festival_rules.tithi_number_at",
            side_effect=[23, 23], # Both days have Ashtami at sunrise
        ):
            self.assertEqual(
                select_janmashtami_dates(self.records, self.rule),
                [date(2030, 9, 1)],
            )

    def test_kshaya_ashtami_uses_following_navami_day(self):
        records = [
            (date(2052, 8, 17), "K7", "5", False, 1.0, 10.0, 10.5),
            (date(2052, 8, 18), "K9", "5", False, 1.0, 11.0, 11.5),
            (date(2052, 8, 19), "K10", "5", False, 1.0, 12.0, 12.5),
        ]
        with patch(
            "festival_rules.tithi_intervals",
            side_effect=[[(10.1, 10.9)], []],
        ), patch(
            "festival_rules.tithi_number_at",
            return_value=22,
        ):
            self.assertEqual(
                select_janmashtami_dates(records, self.rule),
                [date(2052, 8, 18)],
            )


class SmartaJanmashtamiRuleTests(unittest.TestCase):
    rule = festival_rule("Janmashtami")
    records = [
        (date(2030, 8, 31), "K7", "5", False, 1.0, 9.0, 9.5),
        (date(2030, 9, 1), "K8", "5", False, 1.0, 10.0, 10.5),
        (date(2030, 9, 2), "K8", "5", False, 1.0, 11.0, 11.5),
        (date(2030, 9, 3), "K9", "5", False, 1.0, 12.0, 12.5),
    ]

    def test_two_nishitha_ashtamis_use_later_day(self):
        with patch(
            "festival_rules.tithi_overlap_hours",
            side_effect=[0.0, 1.0, 1.0, 0.0],
        ), patch(
            "festival_rules.has_tithi_nakshatra",
            side_effect=[False, False],
        ):
            self.assertEqual(
                select_smarta_janmashtami_dates(self.records, self.rule),
                [date(2030, 9, 2)],
            )

    def test_nishitha_rohini_yoga_has_priority(self):
        with patch(
            "festival_rules.tithi_overlap_hours",
            side_effect=[0.0, 1.0, 1.0, 0.0],
        ), patch(
            "festival_rules.has_tithi_nakshatra",
            side_effect=[True, False],
        ):
            self.assertEqual(
                select_smarta_janmashtami_dates(self.records, self.rule),
                [date(2030, 9, 1)],
            )


class SwarnaGowriVrataRuleTests(unittest.TestCase):
    rule = festival_rule("Swarna Gowri Vrata")

    def test_rule_is_attributed_to_dharma_sindhu(self):
        self.assertEqual(self.rule.status, "dharmasindhu")
        self.assertIn("transliteral.org", self.rule.source)

    def test_selects_single_sunrise_tritiya(self):
        records = [
            record(date(2026, 9, 12), "S2", masa="6"),
            record(date(2026, 9, 13), "S3", masa="6"),
            record(date(2026, 9, 14), "S4", masa="6"),
        ]
        self.assertEqual(
            select_gowri_habba_dates(records, self.rule),
            [date(2026, 9, 13)],
        )

    def test_vriddhi_tritiya_uses_later_chaturthi_yukta_day(self):
        records = [
            record(date(2030, 9, 1), "S3", masa="6"),
            (
                date(2030, 9, 2),
                "S3",
                "6",
                False,
                0.01,
                0.0,
                0.5,
            ),
        ]
        self.assertEqual(
            select_gowri_habba_dates(records, self.rule),
            [date(2030, 9, 2)],
        )

    def test_kshaya_tritiya_uses_earlier_dvitiya_yukta_day(self):
        records = [
            record(date(2030, 9, 1), "S2", masa="6"),
            record(date(2030, 9, 2), "S4", masa="6"),
        ]
        self.assertEqual(
            select_gowri_habba_dates(records, self.rule),
            [date(2030, 9, 1)],
        )

    def test_excludes_adhika_bhadrapada(self):
        records = [
            record(
                date(2030, 8, 2),
                "S3",
                masa="6",
                is_adhika=True,
            ),
            record(date(2030, 9, 1), "S3", masa="6"),
        ]
        self.assertEqual(
            select_gowri_habba_dates(records, self.rule),
            [date(2030, 9, 1)],
        )


class VijayaDasamiRuleTests(unittest.TestCase):
    rule = festival_rule("Vijayadashami (Puja)")
    records = [
        (date(2030, 10, 5), "S10", "7", False, 3.0, 10.0, 10.5),
        (date(2030, 10, 6), "S10", "7", False, 3.0, 11.0, 11.5),
    ]

    def test_shravana_boundary_overlap_is_detected_without_sampling(self):
        with patch(
            "festival_rules.nakshatra_number_at",
            side_effect=[21, 22],
        ):
            self.assertTrue(nakshatra_overlaps(10.0, 10.1, 22))

    def test_both_aparahnas_use_earlier_day_without_shravana(self):
        with patch(
            "festival_rules.tithi_overlap_hours",
            side_effect=[1.0, 1.0, 1.0, 1.0],
        ), patch(
            "festival_rules.nakshatra_overlaps",
            side_effect=[False, False],
        ):
            self.assertEqual(
                select_vijaya_dasami_dates(self.records, self.rule),
                [date(2030, 10, 5)],
            )

    def test_only_later_aparahna_uses_later_day(self):
        with patch(
            "festival_rules.tithi_overlap_hours",
            side_effect=[1.0, 0.0, 1.0, 1.0],
        ), patch(
            "festival_rules.nakshatra_overlaps",
            side_effect=[False, False],
        ):
            self.assertEqual(
                select_vijaya_dasami_dates(self.records, self.rule),
                [date(2030, 10, 6)],
            )

    def test_both_aparahnas_use_only_shravana_day(self):
        with patch(
            "festival_rules.tithi_overlap_hours",
            side_effect=[1.0, 1.0, 1.0, 1.0],
        ), patch(
            "festival_rules.nakshatra_overlaps",
            side_effect=[False, True],
        ):
            self.assertEqual(
                select_vijaya_dasami_dates(self.records, self.rule),
                [date(2030, 10, 6)],
            )

    def test_neither_aparahna_uses_only_shravana_day(self):
        with patch(
            "festival_rules.tithi_overlap_hours",
            side_effect=[1.0, 0.0, 1.0, 0.0],
        ), patch(
            "festival_rules.nakshatra_overlaps",
            side_effect=[False, True],
        ):
            self.assertEqual(
                select_vijaya_dasami_dates(self.records, self.rule),
                [date(2030, 10, 6)],
            )

    def test_neither_aparahna_without_shravana_uses_earlier_day(self):
        with patch(
            "festival_rules.tithi_overlap_hours",
            side_effect=[1.0, 0.0, 1.0, 0.0],
        ), patch(
            "festival_rules.nakshatra_overlaps",
            side_effect=[False, False],
        ):
            self.assertEqual(
                select_vijaya_dasami_dates(self.records, self.rule),
                [date(2030, 10, 5)],
            )

    def test_later_three_muhurta_dashami_with_shravana_overrides_earlier(self):
        records = [
            (date(2030, 10, 5), "S9", "7", False, 3.0, 10.0, 10.5),
            (date(2030, 10, 6), "S10", "7", False, 3.0, 11.0, 11.5),
        ]
        with patch(
            "festival_rules.tithi_overlap_hours",
            side_effect=[1.0, 1.0, 1.0, 0.0],
        ), patch(
            "festival_rules.nakshatra_overlaps",
            side_effect=[False, True],
        ):
            self.assertEqual(
                select_vijaya_dasami_dates(records, self.rule),
                [date(2030, 10, 6)],
            )

    def test_later_non_dashami_remainder_does_not_trigger_exception(self):
        records = [
            (date(2030, 10, 5), "S9", "7", False, 3.0, 10.0, 10.5),
            (date(2030, 10, 6), "S9", "7", False, 3.0, 11.0, 11.5),
        ]
        with patch(
            "festival_rules.tithi_overlap_hours",
            side_effect=[1.0, 1.0, 1.0, 0.0],
        ), patch(
            "festival_rules.nakshatra_overlaps",
            side_effect=[False, True],
        ):
            self.assertEqual(
                select_vijaya_dasami_dates(records, self.rule),
                [date(2030, 10, 5)],
            )

    def test_later_short_dashami_does_not_trigger_exception(self):
        records = [
            (date(2030, 10, 5), "S9", "7", False, 3.0, 10.0, 10.5),
            (date(2030, 10, 6), "S10", "7", False, 2.0, 11.0, 11.5),
        ]
        with patch(
            "festival_rules.tithi_overlap_hours",
            side_effect=[1.0, 1.0, 1.0, 0.0],
        ), patch(
            "festival_rules.nakshatra_overlaps",
            side_effect=[False, True],
        ):
            self.assertEqual(
                select_vijaya_dasami_dates(records, self.rule),
                [date(2030, 10, 5)],
            )


class AyudhaPujaRuleTests(unittest.TestCase):
    rule = festival_rule("Ayudha Puja")

    def test_selects_single_sunrise_vyapini_navami(self):
        records = [
            record(date(2026, 10, 19), "S8", masa="7"),
            record(date(2026, 10, 20), "S9", masa="7"),
        ]
        self.assertEqual(
            select_ayudha_puja_dates(records, self.rule),
            [date(2026, 10, 20)],
        )

    def test_2000_vriddhi_navami_uses_first_sunrise(self):
        records = [
            record(date(2000, 10, 6), "S9", masa="7"),
            record(date(2000, 10, 7), "S9", masa="7"),
        ]
        self.assertEqual(
            select_ayudha_puja_dates(records, self.rule),
            [date(2000, 10, 6)],
        )

    def test_2034_vriddhi_navami_uses_first_sunrise(self):
        records = [
            record(date(2034, 10, 21), "S9", masa="7"),
            record(date(2034, 10, 22), "S9", masa="7"),
        ]
        self.assertEqual(
            select_ayudha_puja_dates(records, self.rule),
            [date(2034, 10, 21)],
        )

    def test_kshaya_navami_uses_the_civil_day_containing_navami(self):
        records = [
            record(date(2030, 10, 4), "S8", masa="7"),
            record(date(2030, 10, 5), "S10", masa="7"),
        ]
        with patch(
            "festival_rules.tithi_intervals",
            return_value=[(0.1, 0.9)],
        ):
            self.assertEqual(
                select_ayudha_puja_dates(records, self.rule),
                [date(2030, 10, 4)],
            )

    def test_2005_helsinki_kshaya_navami_uses_october_11(self):
        records = [
            (date(2005, 10, 11), "S8", "7", False, 1.0, 10.0, 10.5),
            (date(2005, 10, 12), "S10", "7", False, 1.0, 11.0, 11.5),
        ]
        with patch(
            "festival_rules.tithi_intervals",
            return_value=[(10.1, 10.9)],
        ):
            self.assertEqual(
                select_ayudha_puja_dates(records, self.rule),
                [date(2005, 10, 11)],
            )

    def test_excludes_adhika_asvina(self):
        records = [
            record(
                date(2030, 9, 5),
                "S9",
                masa="7",
                is_adhika=True,
            ),
            record(date(2030, 10, 5), "S9", masa="7"),
        ]
        self.assertEqual(
            select_ayudha_puja_dates(records, self.rule),
            [date(2030, 10, 5)],
        )


class BaliPadyamiRuleTests(unittest.TestCase):
    rule = festival_rule("Bali Padyami")
    records = [
        (date(2030, 11, 1), "K15", "8", False, 1.0, 10.0, 10.5),
        (date(2030, 11, 2), "S1", "8", False, 4.0, 11.0, 11.5),
    ]

    def test_pratipada_reaching_ninth_muhurta_uses_sunrise_day(self):
        with patch("festival_rules.tithi_number_at", return_value=1):
            self.assertEqual(
                select_bali_padyami_dates(self.records, self.rule),
                [date(2030, 11, 2)],
            )

    def test_short_pratipada_uses_previous_day(self):
        with patch("festival_rules.tithi_number_at", return_value=2):
            self.assertEqual(
                select_bali_padyami_dates(self.records, self.rule),
                [date(2030, 11, 1)],
            )


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


class VasantaPanchamiRuleTests(unittest.TestCase):
    rule = festival_rule("Vasanta Panchami")
    records = [
        (date(2030, 2, 1), "S5", "11", False, 3.0, 10.0, 10.5),
        (date(2030, 2, 2), "S5", "11", False, 3.0, 11.0, 11.5),
    ]

    def test_both_purvahnas_use_earlier_day(self):
        with patch(
            "festival_rules.tithi_overlap_hours",
            side_effect=[1.0, 1.0],
        ):
            self.assertEqual(
                select_vasanta_panchami_dates(self.records, self.rule),
                [date(2030, 2, 1)],
            )

    def test_only_later_purvahna_uses_later_day(self):
        with patch(
            "festival_rules.tithi_overlap_hours",
            side_effect=[0.0, 1.0],
        ):
            self.assertEqual(
                select_vasanta_panchami_dates(self.records, self.rule),
                [date(2030, 2, 2)],
            )


class RathaSaptamiRuleTests(unittest.TestCase):
    rule = festival_rule("Ratha Saptami")
    records = [
        (date(2030, 2, 3), "S7", "11", False, 3.0, 10.0, 10.5),
        (date(2030, 2, 4), "S7", "11", False, 3.0, 11.0, 11.5),
    ]

    def test_two_arunodayas_use_earlier_day(self):
        with patch(
            "festival_rules.tithi_overlap_hours",
            side_effect=[1.0, 1.0],
        ):
            self.assertEqual(
                select_ratha_saptami_dates(self.records, self.rule),
                [date(2030, 2, 3)],
            )

    def test_only_later_arunodaya_uses_later_day(self):
        with patch(
            "festival_rules.tithi_overlap_hours",
            side_effect=[0.0, 1.0],
        ):
            self.assertEqual(
                select_ratha_saptami_dates(self.records, self.rule),
                [date(2030, 2, 4)],
            )


class KamaDahanaRuleTests(unittest.TestCase):
    rule = festival_rule("Kama Dahana (Holi)")
    records = [
        (date(2030, 3, 20), "S15", "12", False, 3.0, 10.0, 10.5),
        (date(2030, 3, 21), "S15", "12", False, 3.0, 11.0, 11.5),
    ]

    def test_two_pradosha_purnimas_use_later_day(self):
        with patch(
            "festival_rules.tithi_overlap_hours",
            side_effect=[1.0, 1.0],
        ):
            self.assertEqual(
                select_kama_dahana_dates(self.records, self.rule),
                [date(2030, 3, 21)],
            )

    def test_only_earlier_pradosha_uses_earlier_day(self):
        with patch(
            "festival_rules.tithi_overlap_hours",
            side_effect=[1.0, 0.0],
        ):
            self.assertEqual(
                select_kama_dahana_dates(self.records, self.rule),
                [date(2030, 3, 20)],
            )


class MahaShivaratriRuleTests(unittest.TestCase):
    rule = festival_rule("Maha Shivaratri")
    records = [
        (date(2030, 3, 5), "K14", "11", False, 3.0, 10.0, 10.5),
        (date(2030, 3, 6), "K14", "11", False, 3.0, 11.0, 11.5),
        (date(2030, 3, 7), "K15", "11", False, 3.0, 12.0, 12.5),
    ]

    def test_two_full_nishithas_use_recorded_majority_later_day(self):
        with patch(
            "festival_rules.tithi_overlap_hours",
            side_effect=[0.8, 0.8],
        ):
            self.assertEqual(
                select_maha_shivaratri_dates(self.records, self.rule),
                [date(2030, 3, 6)],
            )

    def test_full_first_nishitha_beats_partial_later_nishitha(self):
        with patch(
            "festival_rules.tithi_overlap_hours",
            side_effect=[0.8, 0.2],
        ):
            self.assertEqual(
                select_maha_shivaratri_dates(self.records, self.rule),
                [date(2030, 3, 5)],
            )


class DhanaTrayodashiRuleTests(unittest.TestCase):
    rule = festival_rule("Dhana Trayodashi")
    records = [
        (date(2030, 11, 5), "K12", "7", False, 1.0, 10.0, 10.5),
        (date(2030, 11, 6), "K13", "7", False, 1.0, 11.0, 11.5),
        (date(2030, 11, 7), "K13", "7", False, 1.0, 12.0, 12.5),
    ]

    def test_two_pradoshas_use_later_day(self):
        with patch(
            "festival_rules.tithi_overlap_hours",
            side_effect=[0.0, 1.0, 1.0],
        ):
            self.assertEqual(
                select_dhana_trayodashi_dates(self.records, self.rule),
                [date(2030, 11, 7)],
            )

    def test_one_pradosha_uses_that_day(self):
        with patch(
            "festival_rules.tithi_overlap_hours",
            side_effect=[0.0, 1.0, 0.0],
        ):
            self.assertEqual(
                select_dhana_trayodashi_dates(self.records, self.rule),
                [date(2030, 11, 6)],
            )

    def test_neither_pradosha_uses_later_sunrise_date(self):
        records = [
            (date(2030, 11, 5), "K12", "7", False, 1.0, 10.0, 10.5),
            (date(2030, 11, 6), "K13", "7", False, 1.0, 11.0, 11.5),
            (date(2030, 11, 7), "K14", "7", False, 1.0, 12.0, 12.5),
        ]
        with patch(
            "festival_rules.tithi_overlap_hours",
            return_value=0.0,
        ):
            self.assertEqual(
                select_dhana_trayodashi_dates(records, self.rule),
                [date(2030, 11, 6)],
            )

    def test_neither_pradosha_handles_skipped_trayodashi(self):
        records = [
            (date(2030, 11, 5), "K12", "7", False, 1.0, 10.0, 10.5),
            (date(2030, 11, 6), "K14", "7", False, 1.0, 11.0, 11.5),
        ]
        with (
            patch(
                "festival_rules.tithi_overlap_hours",
                return_value=0.0,
            ),
            patch(
                "festival_rules.tithi_intervals",
                return_value=[(10.6, 10.9)],
            ),
        ):
            self.assertEqual(
                select_dhana_trayodashi_dates(records, self.rule),
                [date(2030, 11, 6)],
            )


class NarakaChaturdashiRuleTests(unittest.TestCase):
    rule = festival_rule("Naraka Chaturdashi")
    records = [
        (date(2030, 11, 6), "K13", "7", False, 1.0, 10.0, 10.5),
        (date(2030, 11, 7), "K14", "7", False, 1.0, 11.0, 11.5),
        (date(2030, 11, 8), "K15", "7", False, 1.0, 12.0, 12.5),
    ]
    moonrises = {
        date(2030, 11, 6): 9.8,
        date(2030, 11, 7): 10.8,
        date(2030, 11, 8): 11.8,
    }

    def test_two_moonrise_vyapini_dates_use_earlier_day(self):
        with patch(
            "festival_rules.tithi_number_at",
            side_effect=[29, 29, 30],
        ):
            self.assertEqual(
                select_naraka_chaturdashi_dates(
                    self.records,
                    self.rule,
                    self.moonrises,
                ),
                [date(2030, 11, 6)],
            )

    def test_only_later_moonrise_vyapini_uses_later_day(self):
        with patch(
            "festival_rules.tithi_number_at",
            side_effect=[28, 29, 30],
        ):
            self.assertEqual(
                select_naraka_chaturdashi_dates(
                    self.records,
                    self.rule,
                    self.moonrises,
                ),
                [date(2030, 11, 7)],
            )

    def test_neither_moonrise_uses_actual_predawn_chaturdashi(self):
        with (
            patch(
                "festival_rules.tithi_number_at",
                side_effect=[28, 30, 30],
            ),
            patch(
                "festival_rules.tithi_intervals",
                return_value=[(9.9, 10.7)],
            ),
            patch(
                "festival_rules.tithi_overlap_hours",
                return_value=0.1,
            ),
        ):
            self.assertEqual(
                select_naraka_chaturdashi_dates(
                    self.records,
                    self.rule,
                    self.moonrises,
                ),
                [date(2030, 11, 6)],
            )

    def test_neither_moonrise_without_predawn_overlap_uses_later_day(self):
        with (
            patch(
                "festival_rules.tithi_number_at",
                side_effect=[28, 30, 30],
            ),
            patch(
                "festival_rules.tithi_intervals",
                return_value=[(10.1, 10.7)],
            ),
            patch(
                "festival_rules.tithi_overlap_hours",
                return_value=0.0,
            ),
        ):
            self.assertEqual(
                select_naraka_chaturdashi_dates(
                    self.records,
                    self.rule,
                    self.moonrises,
                ),
                [date(2030, 11, 7)],
            )


class DeepavaliRuleTests(unittest.TestCase):
    rule = festival_rule("Deepavali")

    def test_neither_pradosha_uses_later_sunrise_date(self):
        records = [
            (date(2030, 11, 7), "K14", "7", False, 1.0, 10.0, 10.5),
            (date(2030, 11, 8), "K15", "7", False, 1.0, 11.0, 11.5),
            (date(2030, 11, 9), "S1", "8", False, 1.0, 12.0, 12.5),
        ]
        with patch(
            "festival_rules.tithi_overlap_hours",
            return_value=0.0,
        ):
            self.assertEqual(
                select_deepavali_dates(records, self.rule),
                [date(2030, 11, 8)],
            )

    def test_neither_pradosha_handles_skipped_amavasya(self):
        records = [
            (date(2030, 11, 7), "K14", "7", False, 1.0, 10.0, 10.5),
            (date(2030, 11, 8), "S1", "8", False, 1.0, 11.0, 11.5),
        ]
        with (
            patch(
                "festival_rules.tithi_overlap_hours",
                return_value=0.0,
            ),
            patch(
                "festival_rules.tithi_intervals",
                return_value=[(10.6, 10.9)],
            ),
        ):
            self.assertEqual(
                select_deepavali_dates(records, self.rule),
                [date(2030, 11, 8)],
            )


class DhanvantariJayantiRuleTests(unittest.TestCase):
    rule = festival_rule("Dhanvantari Jayanti")
    records = [
        (date(2030, 11, 5), "K12", "7", False, 1.0, 10.0, 10.5),
        (date(2030, 11, 6), "K13", "7", False, 1.0, 11.0, 11.5),
        (date(2030, 11, 7), "K14", "7", False, 1.0, 12.0, 12.5),
    ]

    def test_selects_sunrise_vyapini_trayodashi(self):
        self.assertEqual(
            select_dhanvantari_jayanti_dates(self.records, self.rule),
            [date(2030, 11, 6)],
        )

    def test_vriddhi_trayodashi_uses_first_sunrise(self):
        records = [
            record(date(2030, 11, 6), "K13", masa="7"),
            record(date(2030, 11, 7), "K13", masa="7"),
        ]
        self.assertEqual(
            select_dhanvantari_jayanti_dates(records, self.rule),
            [date(2030, 11, 6)],
        )

    def test_kshaya_trayodashi_uses_civil_day_containing_trayodashi(self):
        records = [
            (date(2064, 11, 4), "K12", "7", False, 1.0, 10.0, 10.5),
            (date(2064, 11, 5), "K14", "7", False, 1.0, 11.0, 11.5),
        ]
        with patch(
            "festival_rules.tithi_intervals",
            return_value=[(10.1, 10.9)],
        ):
            self.assertEqual(
                select_dhanvantari_jayanti_dates(records, self.rule),
                [date(2064, 11, 4)],
            )


class MakaraSankrantiRuleTests(unittest.TestCase):
    rule = festival_rule("Makara Sankranti")
    records = [
        (date(2030, 1, 13), "S1", "0", False, 1.0, 2462510.0, 2462510.5),
        (date(2030, 1, 14), "S2", "0", False, 1.0, 2462511.0, 2462511.5),
        (date(2030, 1, 15), "S3", "0", False, 1.0, 2462512.0, 2462512.5),
    ]

    def test_sankranti_before_sunset_uses_same_day(self):
        with patch(
            "panchanga.solar_longitude",
            side_effect=lambda jd: 270.0 if jd >= 2462511.2 else 269.0, # Sankranti at 11.2, which is before sunset 11.5
        ), patch(
            "panchanga.gregorian_to_jd",
            side_effect=lambda d: 2462510.0 if d.day == 13 else 2462513.0,
        ):
            self.assertEqual(
                select_makara_sankranti_dates(self.records, self.rule),
                [date(2030, 1, 14)],
            )

    def test_sankranti_after_sunset_uses_next_day(self):
        with patch(
            "panchanga.solar_longitude",
            side_effect=lambda jd: 270.0 if jd >= 2462511.6 else 269.0, # Sankranti at 11.6, which is after sunset 11.5
        ), patch(
            "panchanga.gregorian_to_jd",
            side_effect=lambda d: 2462510.0 if d.day == 13 else 2462513.0,
        ):
            self.assertEqual(
                select_makara_sankranti_dates(self.records, self.rule),
                [date(2030, 1, 15)],
            )


class MahalayaAmavasyaRuleTests(unittest.TestCase):
    rule = festival_rule("Mahalaya Amavasya")
    records = [
        (date(2030, 9, 26), "K14", "6", False, 1.0, 10.0, 10.5),
        (date(2030, 9, 27), "K15", "6", False, 1.0, 11.0, 11.5),
        (date(2030, 9, 28), "K15", "6", False, 1.0, 12.0, 12.5),
    ]

    def test_two_aparahnas_use_greater_overlap(self):
        with patch(
            "festival_rules.tithi_overlap_hours",
            side_effect=[0.5, 1.0, 0.0],
        ):
            self.assertEqual(
                select_mahalaya_amavasya_dates(self.records, self.rule),
                [date(2030, 9, 27)],
            )

    def test_one_aparahna_uses_that_day(self):
        with patch(
            "festival_rules.tithi_overlap_hours",
            side_effect=[0.0, 1.0, 0.0],
        ):
            self.assertEqual(
                select_mahalaya_amavasya_dates(self.records, self.rule),
                [date(2030, 9, 27)],
            )

    def test_neither_aparahna_uses_previous_day_containing_amavasya(self):
        records = [
            (date(2045, 10, 9), "K14", "6", False, 1.0, 10.0, 10.5),
            (date(2045, 10, 10), "K15", "6", False, 1.0, 11.0, 11.5),
            (date(2045, 10, 11), "S1", "7", False, 1.0, 12.0, 12.5),
        ]
        with patch(
            "festival_rules.tithi_overlap_hours",
            side_effect=[0.0, 0.0],
        ), patch(
            "festival_rules.tithi_intervals",
            return_value=[(10.4, 11.0)],
        ):
            self.assertEqual(
                select_mahalaya_amavasya_dates(records, self.rule),
                [date(2045, 10, 9)],
            )


class DurgaAshtamiObservanceRuleTests(unittest.TestCase):
    rule = festival_rule("Durga Ashtami")

    def test_selects_sunrise_vyapini_ashtami(self):
        records = [
            record(date(2030, 10, 4), "S7", masa="7"),
            record(date(2030, 10, 5), "S8", masa="7"),
            record(date(2030, 10, 6), "S9", masa="7"),
        ]
        self.assertEqual(
            select_durga_ashtami_observance_dates(records, self.rule),
            [date(2030, 10, 5)],
        )

    def test_kshaya_ashtami_uses_civil_day_containing_ashtami(self):
        records = [
            (date(2058, 10, 24), "S7", "7", False, 1.0, 10.0, 10.5),
            (date(2058, 10, 25), "S9", "7", False, 1.0, 11.0, 11.5),
        ]
        with patch(
            "festival_rules.tithi_intervals",
            return_value=[(10.1, 10.9)],
        ):
            self.assertEqual(
                select_durga_ashtami_observance_dates(records, self.rule),
                [date(2058, 10, 24)],
            )


class DurgaAshtamiPujaRuleTests(unittest.TestCase):
    rule = festival_rule("Durga Ashtami (Puja)")

    def test_navami_yukta_ashtami_with_one_ghati_uses_later_day(self):
        records = [
            (date(2030, 10, 4), "S7", "7", False, 1.0, 10.0, 10.5),
            (date(2030, 10, 5), "S8", "7", False, 1.0, 11.0, 11.5),
            (date(2030, 10, 6), "S9", "7", False, 1.0, 12.0, 12.5),
            (date(2030, 10, 7), "S10", "7", False, 1.0, 13.0, 13.5),
        ]
        with (
            patch(
                "festival_rules.tithi_intervals",
                side_effect=[
                    [(10.8, 11.0)],
                    [(11.0, 11.5)],
                    [],
                ],
            ),
            patch(
                "festival_rules.tithi_number_at",
                return_value=8,
            ),
        ):
            self.assertEqual(
                select_durga_ashtami_puja_dates(records, self.rule),
                [date(2030, 10, 5)],
            )

    def test_short_later_ashtami_uses_saptami_yukta_day(self):
        records = [
            (date(2030, 10, 4), "S7", "7", False, 1.0, 10.0, 10.5),
            (date(2030, 10, 5), "S8", "7", False, 0.2, 11.0, 11.5),
            (date(2030, 10, 6), "S9", "7", False, 1.0, 12.0, 12.5),
        ]
        with (
            patch(
                "festival_rules.tithi_intervals",
                side_effect=[
                    [(10.8, 11.0)],
                    [(11.0, 11.01)],
                ],
            ),
            patch(
                "festival_rules.tithi_number_at",
                return_value=9,
            ),
        ):
            self.assertEqual(
                select_durga_ashtami_puja_dates(records, self.rule),
                [date(2030, 10, 4)],
            )

    def test_complete_ashtami_uses_full_previous_day(self):
        records = [
            (date(2030, 10, 4), "S7", "7", False, 1.0, 10.0, 10.5),
            (date(2030, 10, 5), "S8", "7", False, 24.0, 11.0, 11.5),
            (date(2030, 10, 6), "S8", "7", False, 2.0, 12.0, 12.5),
            (date(2030, 10, 7), "S9", "7", False, 1.0, 13.0, 13.5),
        ]
        with patch(
            "festival_rules.tithi_intervals",
            side_effect=[
                [(10.8, 11.0)],
                [(11.0, 12.0)],
                [(12.0, 12.1)],
            ],
        ):
            self.assertEqual(
                select_durga_ashtami_puja_dates(records, self.rule),
                [date(2030, 10, 5)],
            )

    def test_navami_kshaya_uses_saptami_yukta_day(self):
        records = [
            (date(2030, 10, 4), "S7", "7", False, 1.0, 10.0, 10.5),
            (date(2030, 10, 5), "S8", "7", False, 3.0, 11.0, 11.5),
            (date(2030, 10, 6), "S10", "7", False, 1.0, 12.0, 12.5),
        ]
        with patch(
            "festival_rules.tithi_intervals",
            side_effect=[
                [(10.8, 11.0)],
                [(11.0, 11.3)],
            ],
        ):
            self.assertEqual(
                select_durga_ashtami_puja_dates(records, self.rule),
                [date(2030, 10, 4)],
            )

    def test_ashtami_kshaya_uses_saptami_yukta_day(self):
        records = [
            (date(2030, 10, 4), "S7", "7", False, 1.0, 10.0, 10.5),
            (date(2030, 10, 5), "S9", "7", False, 1.0, 11.0, 11.5),
            (date(2030, 10, 6), "S10", "7", False, 1.0, 12.0, 12.5),
        ]
        with patch(
            "festival_rules.tithi_intervals",
            side_effect=[
                [(10.2, 10.8)],
                [],
            ],
        ):
            self.assertEqual(
                select_durga_ashtami_puja_dates(records, self.rule),
                [date(2030, 10, 4)],
            )


class MahanavamiPujaRuleTests(unittest.TestCase):
    rule = festival_rule("Mahanavami (Puja)")

    def test_purva_viddha_navami_uses_previous_day(self):
        records = [
            (date(2024, 10, 10), "S7", "7", False, 1.0, 10.0, 10.5),
            (date(2024, 10, 11), "S8", "7", False, 1.0, 11.0, 11.5),
            (date(2024, 10, 12), "S9", "7", False, 1.0, 12.0, 12.5),
        ]
        with patch(
            "festival_rules.tithi_overlap_hours",
            side_effect=[0.0, 2.4, 0.0],
        ):
            self.assertEqual(
                select_mahanavami_puja_dates(records, self.rule),
                [date(2024, 10, 11)],
            )

    def test_short_navami_uses_sunrise_day(self):
        records = [
            (date(2024, 10, 10), "S7", "7", False, 1.0, 10.0, 10.5),
            (date(2024, 10, 11), "S8", "7", False, 1.0, 11.0, 11.5),
            (date(2024, 10, 12), "S9", "7", False, 1.0, 12.0, 12.5),
        ]
        with patch(
            "festival_rules.tithi_overlap_hours",
            side_effect=[0.0, 0.5, 0.0],
        ):
            self.assertEqual(
                select_mahanavami_puja_dates(records, self.rule),
                [date(2024, 10, 12)],
            )

    def test_six_fixed_ghatis_are_required_at_high_latitude(self):
        records = [
            (date(2037, 10, 16), "S8", "7", False, 1.0, 10.0, 10.4),
            (date(2037, 10, 17), "S9", "7", False, 1.0, 11.0, 11.4),
        ]
        with patch(
            "festival_rules.tithi_overlap_hours",
            side_effect=[2.17, 0.0],
        ):
            self.assertEqual(
                select_mahanavami_puja_dates(records, self.rule),
                [date(2037, 10, 17)],
            )

    def test_skipped_short_navami_uses_following_day(self):
        records = [
            (date(2030, 10, 5), "S8", "7", False, 1.0, 10.0, 10.5),
            (date(2030, 10, 6), "S10", "7", False, 1.0, 11.0, 11.5),
        ]
        with (
            patch(
                "festival_rules.tithi_overlap_hours",
                side_effect=[0.5, 0.0],
            ),
            patch(
                "festival_rules.tithi_intervals",
                return_value=[(10.3, 10.8)],
            ),
        ):
            self.assertEqual(
                select_mahanavami_puja_dates(records, self.rule),
                [date(2030, 10, 6)],
            )

    def test_vriddhi_navami_uses_first_sunrise_day(self):
        records = [
            (date(2030, 10, 5), "S9", "7", False, 24.0, 10.0, 10.5),
            (date(2030, 10, 6), "S9", "7", False, 2.0, 11.0, 11.5),
        ]
        with patch(
            "festival_rules.tithi_overlap_hours",
            return_value=0.0,
        ):
            self.assertEqual(
                select_mahanavami_puja_dates(records, self.rule),
                [date(2030, 10, 5)],
            )


class DasaraRuleTests(unittest.TestCase):
    rule = festival_rule("Dasara")

    def test_selects_sunrise_vyapini_dashami(self):
        records = [
            (date(2024, 10, 12), "S9", "7", False, 1.0, 10.0, 10.5),
            (date(2024, 10, 13), "S10", "7", False, 1.0, 11.0, 11.5),
        ]
        self.assertEqual(
            select_dasara_dates(records, self.rule),
            [date(2024, 10, 13)],
        )

    def test_vriddhi_dashami_uses_first_sunrise(self):
        records = [
            record(date(2030, 10, 5), "S10", masa="7"),
            record(date(2030, 10, 6), "S10", masa="7"),
        ]
        self.assertEqual(
            select_dasara_dates(records, self.rule),
            [date(2030, 10, 5)],
        )

    def test_kshaya_dashami_uses_civil_day_containing_dashami(self):
        records = [
            (date(2075, 10, 18), "S9", "7", False, 1.0, 10.0, 10.5),
            (date(2075, 10, 19), "S11", "7", False, 1.0, 11.0, 11.5),
        ]
        with patch(
            "festival_rules.tithi_intervals",
            return_value=[(10.1, 10.9)],
        ):
            self.assertEqual(
                select_dasara_dates(records, self.rule),
                [date(2075, 10, 18)],
            )


if __name__ == "__main__":
    unittest.main()
