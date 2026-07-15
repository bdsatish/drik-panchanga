"""Regression tests for Dharma Sindhu festival-date decisions."""

from datetime import date
import unittest
from unittest.mock import patch

from festival_rules import (
    FESTIVAL_RULES,
    VARAMAHALAKSHMI_RULE,
    select_aksaya_trtiya_dates,
    select_ayudha_puja_dates,
    select_bali_padyami_dates,
    select_guru_purnima_dates,
    select_holi_dates,
    select_janmashtami_dates,
    select_maha_shivaratri_dates,
    select_naga_panchami_dates,
    select_narasimha_jayanthi_dates,
    select_raksha_bandhan_dates,
    select_rama_navami_dates,
    select_ratha_saptami_dates,
    select_rigveda_upakarma_dates,
    select_taittiriya_apastamba_upakarma_dates,
    select_ugadi_dates,
    select_vasanta_panchami_dates,
    select_vijaya_dasami_dates,
)


def record(day, tithi, masa="1", is_adhika=False):
    """Build the compact record shape consumed by festival selectors."""
    return (day, tithi, masa, is_adhika, 1.0, 0.0, 0.5)


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
            record(date(2030, 3, 20), "S1", is_adhika=True),
            record(date(2030, 4, 19), "S1"),
        ]
        self.assertEqual(
            select_ugadi_dates(records, self.rule),
            [date(2030, 3, 20)],
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


class AksayaTrtiyaRuleTests(unittest.TestCase):
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


class RuleStatusTests(unittest.TestCase):
    def test_vasavi_jayanthi_is_not_attributed_to_dharma_sindhu(self):
        rule = FESTIVAL_RULES[3]
        self.assertEqual(rule.status, "unresolved")
        self.assertIsNone(rule.source)

    def test_varamahalakshmi_is_not_attributed_to_dharma_sindhu(self):
        self.assertEqual(VARAMAHALAKSHMI_RULE.status, "unresolved")
        self.assertIsNone(VARAMAHALAKSHMI_RULE.source)

    def test_ayudha_puja_is_documented_as_a_regional_rule(self):
        rule = next(rule for rule in FESTIVAL_RULES if rule.number == 15)
        self.assertEqual(rule.status, "regional")
        self.assertIn("drikpanchang.com", rule.source)

    def test_gita_jayanti_is_not_attributed_to_dharma_sindhu(self):
        rule = next(rule for rule in FESTIVAL_RULES if rule.number == 20)
        self.assertEqual(rule.status, "unresolved")
        self.assertIsNone(rule.source)

    def test_vasavi_atmarpana_is_not_attributed_to_dharma_sindhu(self):
        rule = next(rule for rule in FESTIVAL_RULES if rule.number == 21)
        self.assertEqual(rule.status, "unresolved")
        self.assertIsNone(rule.source)

    def test_vsn_jayanthi_is_not_attributed_to_dharma_sindhu(self):
        rule = next(rule for rule in FESTIVAL_RULES if rule.number == 24)
        self.assertEqual(rule.status, "unresolved")
        self.assertIsNone(rule.source)


class NarasimhaJayanthiRuleTests(unittest.TestCase):
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
                select_narasimha_jayanthi_dates(self.records, self.rule),
                [date(2030, 5, 19)],
            )

    def test_uses_only_sunset_with_caturdashi(self):
        with patch(
            "festival_rules.tithi_number_at",
            side_effect=[14, 15],
        ):
            self.assertEqual(
                select_narasimha_jayanthi_dates(self.records, self.rule),
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


class RigUpakarmaRuleTests(unittest.TestCase):
    rule = next(rule for rule in FESTIVAL_RULES if rule.number == 9)

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
                select_rigveda_upakarma_dates(records, self.rule),
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
                select_rigveda_upakarma_dates(records, self.rule),
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
                select_rigveda_upakarma_dates(records, self.rule),
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
                select_rigveda_upakarma_dates(records, self.rule),
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
                select_rigveda_upakarma_dates(records, self.rule),
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
                select_rigveda_upakarma_dates(records, self.rule),
                [date(2030, 9, 15)],
            )


class YajurUpakarmaRuleTests(unittest.TestCase):
    rule = next(rule for rule in FESTIVAL_RULES if rule.number == 10)

    @staticmethod
    def records(remainder=2.0):
        return [
            (date(2030, 8, 14), "S14", "5", False, 1.0, 10.0, 10.5),
            (date(2030, 8, 15), "S15", "5", False, remainder, 11.0, 11.5),
            (date(2030, 8, 16), "K1", "5", False, 1.0, 12.0, 12.5),
        ]

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
                ),
                [date(2030, 8, 14)],
            )


class RakshaBandhanRuleTests(unittest.TestCase):
    rule = next(rule for rule in FESTIVAL_RULES if rule.number == 11)

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


class JanmashtamiRuleTests(unittest.TestCase):
    rule = next(rule for rule in FESTIVAL_RULES if rule.number == 12)
    records = [
        (date(2030, 9, 1), "K8", "5", False, 1.0, 10.0, 10.5),
        (date(2030, 9, 2), "K8", "5", False, 1.0, 11.0, 11.5),
        (date(2030, 9, 3), "K9", "5", False, 1.0, 12.0, 12.5),
    ]

    def test_two_nishitha_ashtamis_use_later_day(self):
        with patch(
            "festival_rules.tithi_overlap_hours",
            side_effect=[1.0, 1.0],
        ), patch(
            "festival_rules.has_tithi_nakshatra",
            side_effect=[False, False],
        ):
            self.assertEqual(
                select_janmashtami_dates(self.records, self.rule),
                [date(2030, 9, 2)],
            )

    def test_nishitha_rohini_yoga_has_priority(self):
        with patch(
            "festival_rules.tithi_overlap_hours",
            side_effect=[1.0, 1.0],
        ), patch(
            "festival_rules.has_tithi_nakshatra",
            side_effect=[True, False],
        ):
            self.assertEqual(
                select_janmashtami_dates(self.records, self.rule),
                [date(2030, 9, 1)],
            )


class VijayaDasamiRuleTests(unittest.TestCase):
    rule = next(rule for rule in FESTIVAL_RULES if rule.number == 16)
    records = [
        (date(2030, 10, 5), "S10", "7", False, 3.0, 10.0, 10.5),
        (date(2030, 10, 6), "S10", "7", False, 3.0, 11.0, 11.5),
    ]

    def test_both_aparahnas_use_earlier_day_without_shravana(self):
        with patch(
            "festival_rules.tithi_overlap_hours",
            side_effect=[1.0, 1.0],
        ), patch(
            "festival_rules.has_nakshatra",
            side_effect=[False, False],
        ):
            self.assertEqual(
                select_vijaya_dasami_dates(self.records, self.rule),
                [date(2030, 10, 5)],
            )

    def test_only_later_aparahna_uses_later_day(self):
        with patch(
            "festival_rules.tithi_overlap_hours",
            side_effect=[0.0, 1.0],
        ), patch(
            "festival_rules.has_nakshatra",
            side_effect=[False, False],
        ):
            self.assertEqual(
                select_vijaya_dasami_dates(self.records, self.rule),
                [date(2030, 10, 6)],
            )


class AyudhaPujaRuleTests(unittest.TestCase):
    rule = next(rule for rule in FESTIVAL_RULES if rule.number == 15)

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

    def test_does_not_guess_when_navami_is_skipped_at_sunrise(self):
        records = [
            record(date(2030, 10, 4), "S8", masa="7"),
            record(date(2030, 10, 5), "S10", masa="7"),
        ]
        self.assertEqual(select_ayudha_puja_dates(records, self.rule), [])

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
    rule = next(rule for rule in FESTIVAL_RULES if rule.number == 19)
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
    rule = next(rule for rule in FESTIVAL_RULES if rule.number == 22)
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
    rule = next(rule for rule in FESTIVAL_RULES if rule.number == 23)
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


class HoliRuleTests(unittest.TestCase):
    rule = next(rule for rule in FESTIVAL_RULES if rule.number == 26)
    records = [
        (date(2030, 3, 20), "K1", "12", False, 3.0, 10.0, 10.5),
        (date(2030, 3, 21), "K1", "12", False, 3.0, 11.0, 11.5),
    ]

    def test_two_pratipada_mornings_use_earlier_day(self):
        with patch(
            "festival_rules.tithi_overlap_hours",
            side_effect=[1.0, 1.0],
        ):
            self.assertEqual(
                select_holi_dates(self.records, self.rule),
                [date(2030, 3, 20)],
            )

    def test_only_later_morning_uses_later_day(self):
        with patch(
            "festival_rules.tithi_overlap_hours",
            side_effect=[0.0, 1.0],
        ):
            self.assertEqual(
                select_holi_dates(self.records, self.rule),
                [date(2030, 3, 21)],
            )


class MahaShivaratriRuleTests(unittest.TestCase):
    rule = next(rule for rule in FESTIVAL_RULES if rule.number == 25)
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


if __name__ == "__main__":
    unittest.main()
