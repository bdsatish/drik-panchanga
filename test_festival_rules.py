"""Regression tests for Dharma Sindhu festival-date decisions."""

from datetime import date
import unittest
from unittest.mock import patch

from festival_rules import (
    FESTIVAL_RULES,
    VARAMAHALAKSHMI_RULE,
    select_aksaya_trtiya_dates,
    select_guru_purnima_dates,
    select_naga_panchami_dates,
    select_narasimha_jayanthi_dates,
    select_raksha_bandhan_dates,
    select_rama_navami_dates,
    select_taittiriya_apastamba_upakarma_dates,
    select_ugadi_dates,
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


class UnresolvedRuleTests(unittest.TestCase):
    def test_vasavi_jayanthi_is_not_attributed_to_dharma_sindhu(self):
        rule = FESTIVAL_RULES[3]
        self.assertEqual(rule.status, "unresolved")
        self.assertIsNone(rule.source)

    def test_varamahalakshmi_is_not_attributed_to_dharma_sindhu(self):
        self.assertEqual(VARAMAHALAKSHMI_RULE.status, "unresolved")
        self.assertIsNone(VARAMAHALAKSHMI_RULE.source)


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


class YajurUpakarmaRuleTests(unittest.TestCase):
    rule = FESTIVAL_RULES[7]

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
    rule = next(rule for rule in FESTIVAL_RULES if rule.number == 25)

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


if __name__ == "__main__":
    unittest.main()
