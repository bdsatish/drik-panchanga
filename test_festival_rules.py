"""Unit tests for the clean-slate plain-tithi festival rules."""

from datetime import date
import unittest
from unittest import mock

from festival_rules import (
    NON_TITHI_FESTIVAL_RULES,
    TITHI_FESTIVAL_RULES,
    collect_records,
    format_festival_dates,
    plain_tithi_number,
    resolve_ekadashi_dates,
    resolve_festivals,
    resolve_vriddhi_dates,
    select_kshaya_dates,
    select_makara_sankranti_dates,
    select_non_tithi_dates,
    select_plain_tithi_dates,
    select_rig_upakarma_dates,
    select_vaikuntha_ekadashi_dates,
    select_varamahalakshmi_dates,
)


def day_row(day, tithi, masa, is_adhika=False, yoga=1, sunrise_jd=0.0, nakshatra=1):
    """One ``daily_values`` row with unused timing fields zeroed."""
    return (
        day,
        tithi,
        nakshatra,
        masa,
        is_adhika,
        0.0,
        sunrise_jd,
        0.0,
        yoga,
        None,
    )


def append_solar_coverage_rows(rows):
    """Append synthetic rows for Vaikuntha and Makara Sankranti coverage."""
    rows.append(day_row(len(rows) + 1, "K1", "12"))
    rows.append(day_row(len(rows) + 1, "S11", "9", sunrise_jd=900.0))
    rows.append(day_row(len(rows) + 1, "S12", "9", sunrise_jd=999.0))
    rows.append(day_row(len(rows) + 1, "S13", "9", sunrise_jd=1000.0))
    return rows


def covering_month_data(year=2030, month=1):
    """Synthetic month containing every tithi festival once."""
    rows = []
    for index, (number, _name, masa, tithi) in enumerate(
        TITHI_FESTIVAL_RULES, start=1
    ):
        # Naga Panchami day also carries Sravana nakshatra for Rig Upakarma.
        nakshatra = 22 if number == 7 else 1
        rows.append(day_row(index, tithi, str(masa), nakshatra=nakshatra))
    return {(year, month): append_solar_coverage_rows(rows)}


class FestivalCatalogTests(unittest.TestCase):
    def test_catalogs_partition_tithi_and_non_tithi(self):
        self.assertEqual(len(TITHI_FESTIVAL_RULES), 25)
        self.assertEqual(TITHI_FESTIVAL_RULES[0], (1, "Ugadi", 1, "S1"))
        self.assertEqual(
            TITHI_FESTIVAL_RULES[-1],
            (29, "Kama Dahana (Holi)", 12, "S15"),
        )
        self.assertEqual(
            NON_TITHI_FESTIVAL_RULES,
            (
                (8, "Varamahalakshmi Vrata"),
                (9, "Rig Upakarma"),
                (22, "Vaikuntha Ekadashi"),
                (23, "Makara Sankranti"),
            ),
        )
        numbers = sorted(
            [number for number, *_ in TITHI_FESTIVAL_RULES]
            + [number for number, _ in NON_TITHI_FESTIVAL_RULES]
        )
        self.assertEqual(numbers, list(range(1, 30)))


class CollectRecordsTests(unittest.TestCase):
    def test_keeps_sunrise_identity_fields(self):
        months = [(2026, 6)]
        month_data = {
            (2026, 6): [day_row(1, "S1", "3", nakshatra=5)],
        }
        self.assertEqual(
            collect_records(months, month_data),
            [(date(2026, 6, 1), "S1", 5, "3", False, 0.0)],
        )


class ResolveVriddhiTests(unittest.TestCase):
    def test_keeps_former_date_of_consecutive_sunrises(self):
        self.assertEqual(
            resolve_vriddhi_dates(
                [
                    date(2030, 5, 6),
                    date(2030, 5, 5),
                    date(2030, 5, 7),
                    date(2030, 8, 10),
                    date(2030, 8, 11),
                ]
            ),
            [date(2030, 5, 5), date(2030, 8, 10)],
        )

    def test_leaves_isolated_dates_unchanged(self):
        self.assertEqual(
            resolve_vriddhi_dates([date(2030, 3, 10), date(2030, 4, 9)]),
            [date(2030, 3, 10), date(2030, 4, 9)],
        )


class SelectPlainTithiTests(unittest.TestCase):
    def setUp(self):
        self.records = [
            (date(2030, 3, 10), "S1", 1, "A1", True, 0.0),
            (date(2030, 3, 18), "S9", 1, "1", False, 0.0),
            (date(2030, 4, 9), "S1", 1, "1", False, 0.0),
            (date(2030, 5, 1), "S3", 1, "A2", True, 0.0),
            (date(2030, 5, 2), "S3", 1, "2", False, 0.0),
        ]

    def test_matches_non_adhika_masa_and_tithi(self):
        self.assertEqual(
            select_plain_tithi_dates(self.records, 1, "S9"),
            [date(2030, 3, 18)],
        )
        self.assertEqual(
            select_plain_tithi_dates(self.records, 2, "S3"),
            [date(2030, 5, 2)],
        )

    def test_skips_adhika_by_default(self):
        self.assertEqual(
            select_plain_tithi_dates(self.records, 1, "S1"),
            [date(2030, 4, 9)],
        )

    def test_ugadi_allows_adhika_chaitra(self):
        self.assertEqual(
            select_plain_tithi_dates(self.records, 1, "S1", allow_adhika=True),
            [date(2030, 3, 10), date(2030, 4, 9)],
        )

    def test_vriddhi_keeps_former_of_consecutive_matches(self):
        records = [
            (date(2030, 8, 14), "K8", 1, "5", False, 0.0),
            (date(2030, 8, 15), "K8", 1, "5", False, 0.0),
            (date(2030, 8, 16), "K9", 1, "5", False, 0.0),
        ]
        self.assertEqual(
            select_plain_tithi_dates(records, 5, "K8"),
            [date(2030, 8, 14)],
        )

    def test_kshaya_marks_later_civil_date(self):
        records = [
            (date(2030, 5, 4), "S2", 1, "2", False, 0.0),
            (date(2030, 5, 5), "S4", 1, "2", False, 0.0),
        ]
        self.assertEqual(
            select_plain_tithi_dates(records, 2, "S3"),
            [date(2030, 5, 5)],
        )

    def test_kshaya_ugadi_across_masa_boundary(self):
        records = [
            (date(2030, 3, 25), "K15", 1, "12", False, 0.0),
            (date(2030, 3, 26), "S2", 1, "1", False, 0.0),
        ]
        self.assertEqual(
            select_plain_tithi_dates(records, 1, "S1", allow_adhika=True),
            [date(2030, 3, 26)],
        )

    def test_kshaya_krishna_across_masa_boundary(self):
        records = [
            (date(2030, 10, 20), "K14", 1, "7", False, 0.0),
            (date(2030, 10, 21), "S1", 1, "8", False, 0.0),
        ]
        self.assertEqual(
            select_plain_tithi_dates(records, 7, "K15"),
            [date(2030, 10, 21)],
        )
        self.assertEqual(
            select_plain_tithi_dates(records, 8, "K15"),
            [],
        )


class PlainTithiNumberTests(unittest.TestCase):
    def test_converts_sukla_and_krishna_codes(self):
        self.assertEqual(plain_tithi_number("S1"), 1)
        self.assertEqual(plain_tithi_number("S15"), 15)
        self.assertEqual(plain_tithi_number("K1"), 16)
        self.assertEqual(plain_tithi_number("K15"), 30)
        self.assertIsNone(plain_tithi_number("Solar"))


class SelectKshayaTests(unittest.TestCase):
    def test_detects_skipped_tithi_between_consecutive_sunrises(self):
        records = [
            (date(2030, 5, 4), "S2", 1, "2", False, 0.0),
            (date(2030, 5, 5), "S4", 1, "2", False, 0.0),
            (date(2030, 5, 6), "S5", 1, "2", False, 0.0),
        ]
        self.assertEqual(
            select_kshaya_dates(records, "S3", masa=2),
            [date(2030, 5, 5)],
        )

    def test_ugadi_between_phalguna_amavasya_and_caitra_dvitiya(self):
        records = [
            (date(2030, 3, 25), "K15", 1, "12", False, 0.0),
            (date(2030, 3, 26), "S2", 1, "1", False, 0.0),
        ]
        self.assertEqual(
            select_kshaya_dates(records, "S1", masa=1, allow_adhika=True),
            [date(2030, 3, 26)],
        )

    def test_ignores_non_consecutive_civil_days(self):
        records = [
            (date(2030, 5, 4), "S2", 1, "2", False, 0.0),
            (date(2030, 5, 6), "S4", 1, "2", False, 0.0),
        ]
        self.assertEqual(select_kshaya_dates(records, "S3", masa=2), [])


class FormatFestivalDatesTests(unittest.TestCase):
    def test_formats_empty_single_range_and_scattered(self):
        self.assertEqual(format_festival_dates([]), "None")
        self.assertEqual(
            format_festival_dates([date(2026, 3, 19)]),
            "Mar 19",
        )
        self.assertEqual(
            format_festival_dates([date(2026, 3, 19), date(2026, 3, 20)]),
            "Mar 19-20",
        )
        self.assertEqual(
            format_festival_dates([date(2026, 3, 19), date(2026, 4, 1)]),
            "Mar 19,Apr 01",
        )


class ResolveFestivalsTests(unittest.TestCase):
    def setUp(self):
        def fake_raasi(jd):
            return 10 if jd >= 1000 else 9

        self.raasi_patcher = mock.patch(
            "festival_rules.panchanga.raasi",
            side_effect=fake_raasi,
        )
        self.raasi_patcher.start()
        self.addCleanup(self.raasi_patcher.stop)

    def test_resolves_markers_and_footer_entries(self):
        months = [(2030, 1)]
        month_data = covering_month_data()
        by_date, entries = resolve_festivals(months, month_data)

        self.assertEqual(len(entries), 29)
        self.assertEqual(entries[0], (1, "Jan 01", "Ugadi"))
        self.assertEqual(entries[7], (8, "Jan 04", "Varamahalakshmi Vrata"))
        self.assertEqual(entries[8], (9, "Jan 07", "Rig Upakarma"))
        self.assertEqual(entries[10], (11, "Jan 09", "Janmashtami"))
        self.assertEqual(entries[21], (22, "Jan 27", "Vaikuntha Ekadashi"))
        self.assertEqual(entries[22], (23, "Jan 29", "Makara Sankranti"))
        self.assertEqual(by_date[date(2030, 1, 1)], [1])
        self.assertEqual(by_date[date(2030, 1, 4)], [4, 8])
        self.assertEqual(by_date[date(2030, 1, 7)], [7, 9])
        self.assertEqual(by_date[date(2030, 1, 9)], [11])
        self.assertEqual(by_date[date(2030, 1, 27)], [22])
        self.assertEqual(by_date[date(2030, 1, 29)], [23])

    def test_ugadi_marks_adhika_chaitra_s1(self):
        months = [(2030, 3)]
        rows = []
        for index, (number, _name, masa, tithi) in enumerate(
            TITHI_FESTIVAL_RULES, start=1
        ):
            nakshatra = 22 if number == 7 else 1
            if number == 1:
                rows.append(
                    day_row(index, "S1", "A1", is_adhika=True, nakshatra=nakshatra)
                )
            else:
                rows.append(
                    day_row(index, tithi, str(masa), nakshatra=nakshatra)
                )
        append_solar_coverage_rows(rows)
        month_data = {(2030, 3): rows}

        by_date, entries = resolve_festivals(months, month_data)
        self.assertIn(1, by_date[date(2030, 3, 1)])
        self.assertEqual(entries[0][1], "Mar 01")

    def test_non_ugadi_festivals_skip_adhika_masa(self):
        months = [(2030, 1)]
        month_data = covering_month_data()
        # Replace Akshaya Tritiya day with adhika Vaisakha S3 only.
        month_data[(2030, 1)][2] = day_row(3, "S3", "A2", is_adhika=True)

        with self.assertRaisesRegex(RuntimeError, "Akshaya Tritiya"):
            resolve_festivals(months, month_data)

    def test_context_matches_are_clipped_to_target_months(self):
        target_months = [(2030, 3)]
        target_data = covering_month_data(2030, 3)
        context_months = [(2030, 2), (2030, 3)]
        context_data = {
            (2030, 2): [day_row(1, "S1", "1")],
            **target_data,
        }
        target_data[(2030, 3)][0] = day_row(1, "S1", "1")

        by_date, entries = resolve_festivals(
            target_months,
            target_data,
            context_months=context_months,
            context_data=context_data,
        )
        self.assertEqual(entries[0], (1, "Mar 01", "Ugadi"))
        self.assertNotIn(date(2030, 2, 1), by_date)

    def test_context_arguments_must_be_paired(self):
        with self.assertRaisesRegex(ValueError, "context_months"):
            resolve_festivals([(2030, 1)], covering_month_data(), context_months=[])

    def test_raises_when_a_festival_has_no_date(self):
        months = [(2030, 1)]
        month_data = covering_month_data()
        month_data[(2030, 1)][0] = day_row(1, "S2", "1")

        with self.assertRaisesRegex(RuntimeError, "Ugadi"):
            resolve_festivals(months, month_data)

    def test_vriddhi_marks_only_the_former_date(self):
        months = [(2030, 1)]
        rows = []
        day = 1
        for number, _name, masa, tithi in TITHI_FESTIVAL_RULES:
            nakshatra = 22 if number == 7 else 1
            rows.append(day_row(day, tithi, str(masa), nakshatra=nakshatra))
            if number == 11:
                day += 1
                rows.append(day_row(day, tithi, str(masa)))
            day += 1
        rows.append(day_row(day, "K1", "12"))
        rows.append(day_row(day + 1, "S11", "9", sunrise_jd=900.0))
        rows.append(day_row(day + 2, "S12", "9", sunrise_jd=999.0))
        rows.append(day_row(day + 3, "S13", "9", sunrise_jd=1000.0))
        month_data = {(2030, 1): rows}

        by_date, entries = resolve_festivals(months, month_data)
        self.assertEqual(by_date[date(2030, 1, 9)], [11])
        self.assertNotIn(date(2030, 1, 10), by_date)
        self.assertEqual(entries[10], (11, "Jan 09", "Janmashtami"))

    def test_kshaya_marks_later_date_in_calendar(self):
        months = [(2030, 1)]
        rows = []
        day = 1
        for number, _name, masa, tithi in TITHI_FESTIVAL_RULES:
            nakshatra = 22 if number == 7 else 1
            if number == 3:
                rows.append(day_row(day, "S2", "2"))
                day += 1
                rows.append(day_row(day, "S4", "2"))
            else:
                rows.append(day_row(day, tithi, str(masa), nakshatra=nakshatra))
            day += 1
        rows.append(day_row(day, "K1", "12"))
        rows.append(day_row(day + 1, "S11", "9", sunrise_jd=900.0))
        rows.append(day_row(day + 2, "S12", "9", sunrise_jd=999.0))
        rows.append(day_row(day + 3, "S13", "9", sunrise_jd=1000.0))
        month_data = {(2030, 1): rows}

        by_date, entries = resolve_festivals(months, month_data)
        self.assertIn(3, by_date[date(2030, 1, 4)])
        self.assertEqual(entries[2], (3, "Jan 04", "Akshaya Tritiya"))


class VaramahalakshmiTests(unittest.TestCase):
    def test_uses_friday_immediately_before_sravana_purnima(self):
        # 2030-08-10 is Saturday, so preceding Friday is 08-09.
        records = [
            (date(2030, 8, 9), "S14", 1, "5", False, 0.0),
            (date(2030, 8, 10), "S15", 1, "5", False, 0.0),
            (date(2030, 8, 11), "K1", 1, "5", False, 0.0),
        ]
        self.assertEqual(
            select_varamahalakshmi_dates(records),
            [date(2030, 8, 9)],
        )

    def test_friday_purnima_uses_previous_week_friday(self):
        # 2030-08-16 is Friday; rule still chooses the prior Friday.
        records = [
            (date(2030, 8, 15), "S14", 1, "5", False, 0.0),
            (date(2030, 8, 16), "S15", 1, "5", False, 0.0),
            (date(2030, 8, 17), "K1", 1, "5", False, 0.0),
        ]
        self.assertEqual(
            select_varamahalakshmi_dates(records),
            [date(2030, 8, 9)],
        )

    def test_vriddhi_purnima_anchors_on_former_sunrise(self):
        # 2030-08-09 is Friday; former S15 sunrise is 08-09, so prior Friday
        # is 08-02.
        records = [
            (date(2030, 8, 8), "S14", 1, "5", False, 0.0),
            (date(2030, 8, 9), "S15", 1, "5", False, 0.0),
            (date(2030, 8, 10), "S15", 1, "5", False, 0.0),
        ]
        self.assertEqual(
            select_varamahalakshmi_dates(records),
            [date(2030, 8, 2)],
        )

    def test_skips_adhika_sravana_purnima(self):
        records = [
            (date(2030, 8, 10), "S15", 1, "A5", True, 0.0),
            (date(2030, 8, 11), "K1", 1, "A5", True, 0.0),
        ]
        self.assertEqual(select_varamahalakshmi_dates(records), [])

    def test_dispatcher_routes_by_name(self):
        records = [
            (date(2030, 8, 9), "S14", 1, "5", False, 0.0),
            (date(2030, 8, 10), "S15", 1, "5", False, 0.0),
        ]
        self.assertEqual(
            select_non_tithi_dates(records, 8, "Varamahalakshmi Vrata"),
            [date(2030, 8, 9)],
        )

    def test_dispatcher_rejects_unknown_festival(self):
        with self.assertRaisesRegex(ValueError, "No selector"):
            select_non_tithi_dates([], 99, "Unknown Vrata")


class RigUpakarmaTests(unittest.TestCase):
    def test_selects_nija_sravana_with_sravana_nakshatra(self):
        records = [
            (date(2030, 8, 10), "S12", 22, "5", False, 0.0),
            (date(2030, 8, 11), "S13", 23, "5", False, 0.0),
        ]
        self.assertEqual(
            select_rig_upakarma_dates(records),
            [date(2030, 8, 10)],
        )

    def test_skips_adhika_sravana(self):
        records = [
            (date(2030, 8, 10), "S12", 22, "A5", True, 0.0),
        ]
        self.assertEqual(select_rig_upakarma_dates(records), [])

    def test_vriddhi_keeps_former_sunrise(self):
        records = [
            (date(2030, 8, 10), "S12", 22, "5", False, 0.0),
            (date(2030, 8, 11), "S13", 22, "5", False, 0.0),
        ]
        self.assertEqual(
            select_rig_upakarma_dates(records),
            [date(2030, 8, 10)],
        )


class VaikunthaEkadashiTests(unittest.TestCase):
    def test_keeps_margasira_s11_in_dhanur(self):
        records = [
            (date(2030, 12, 5), "S11", 1, "9", False, 10.0),
            (date(2030, 12, 20), "S11", 1, "10", False, 20.0),
        ]
        with mock.patch(
            "festival_rules.panchanga.raasi",
            side_effect=lambda jd: 9 if jd == 10.0 else 10,
        ):
            self.assertEqual(
                select_vaikuntha_ekadashi_dates(records),
                [date(2030, 12, 5)],
            )

    def test_keeps_pausha_s11_in_dhanur(self):
        records = [
            (date(2030, 12, 5), "S11", 1, "9", False, 10.0),
            (date(2030, 12, 20), "S11", 1, "10", False, 20.0),
        ]
        with mock.patch(
            "festival_rules.panchanga.raasi",
            side_effect=lambda jd: 9 if jd == 20.0 else 8,
        ):
            self.assertEqual(
                select_vaikuntha_ekadashi_dates(records),
                [date(2030, 12, 20)],
            )

    def test_rejects_non_dhanur_candidates(self):
        records = [
            (date(2030, 12, 5), "S11", 1, "9", False, 10.0),
        ]
        with mock.patch("festival_rules.panchanga.raasi", return_value=8):
            self.assertEqual(select_vaikuntha_ekadashi_dates(records), [])


class MakaraSankrantiTests(unittest.TestCase):
    def test_marks_first_sunrise_in_makara(self):
        records = [
            (date(2030, 1, 13), "S10", 1, "10", False, 10.0),
            (date(2030, 1, 14), "S11", 1, "10", False, 20.0),
            (date(2030, 1, 15), "S12", 1, "10", False, 30.0),
        ]
        with mock.patch(
            "festival_rules.panchanga.raasi",
            side_effect=lambda jd: 10 if jd >= 20.0 else 9,
        ):
            self.assertEqual(
                select_makara_sankranti_dates(records),
                [date(2030, 1, 14)],
            )

    def test_ignores_range_that_opens_already_in_makara(self):
        records = [
            (date(2030, 1, 14), "S11", 1, "10", False, 20.0),
            (date(2030, 1, 15), "S12", 1, "10", False, 30.0),
        ]
        with mock.patch("festival_rules.panchanga.raasi", return_value=10):
            self.assertEqual(select_makara_sankranti_dates(records), [])


class ResolveEkadashiTests(unittest.TestCase):
    def test_empty_input_returns_no_dates(self):
        self.assertEqual(resolve_ekadashi_dates([], {}), [])

    def test_sunrise_vriddhi_and_kshaya_for_both_pakshas(self):
        months = [(2030, 6)]
        month_data = {
            (2030, 6): [
                day_row(1, "S10", "3"),
                day_row(2, "S11", "3"),  # sukla sunrise
                day_row(3, "S12", "3"),
                day_row(10, "K11", "3"),  # krishna sunrise day 1
                day_row(11, "K11", "3"),  # vriddhi -> keep day 10
                day_row(12, "K12", "3"),
                day_row(20, "S10", "4"),
                day_row(21, "S12", "4"),  # sukla kshaya -> day 21
            ]
        }
        self.assertEqual(
            resolve_ekadashi_dates(months, month_data),
            [
                date(2030, 6, 2),
                date(2030, 6, 10),
                date(2030, 6, 21),
            ],
        )


if __name__ == "__main__":
    unittest.main()
