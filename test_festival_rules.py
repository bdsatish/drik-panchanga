"""Regression tests for Dharma Sindhu festival-date decisions."""

from datetime import date
import unittest
from unittest.mock import patch

from festival_test_helpers import festival_rule, record
from festival_rules import (
    FESTIVAL_RULES,
    VARAMAHALAKSHMI_RULE,
    nakshatra_overlaps,
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
    select_ugadi_dates,
    select_vasavi_atmarpana_dates,
    select_vasavi_jayanti_dates,
    select_varamahalakshmi_dates,
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
)


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
