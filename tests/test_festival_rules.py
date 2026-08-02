"""Unit tests for the clean-slate plain-tithi festival rules."""

from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
import calendar
import unittest
from unittest import mock

import panchanga

from festival_rules import (
    CIVIL_DATE,
    FESTIVAL_RULES,
    SUNRISE_JD,
    all_festival_names,
    collect_records,
    format_festival_dates,
    load_festival_selection,
    plain_tithi_number,
    resolve_ekadashi_dates,
    resolve_festivals,
    resolve_vriddhi_dates,
    select_kshaya_dates,
    select_makara_sankranti_dates,
    select_mesha_sankranti_dates,
    select_non_tithi_dates,
    select_onam_dates,
    select_plain_tithi_dates,
    select_rig_upakarma_dates,
    select_sama_upakarma_dates,
    select_vaikuntha_ekadashi_dates,
    select_varamahalakshmi_dates,
    select_yajur_upakarma_dates,
    sankranti_raasi_by_date,
)
from generate_panchanga_calendar import (
    DEFAULT_FESTIVALS_PATH,
    MONTH_COUNT,
    daily_values,
    load_location,
    month_range,
)


def day_row(day, tithi, masa, is_adhika=False, sunrise_jd=0.0, nakshatra=1, yoga=1):
    """One ``daily_values`` row: day, tithi, nakshatra, yoga, masa, is_adhika, sunrise_jd."""
    return (day, tithi, nakshatra, yoga, masa, is_adhika, sunrise_jd)


def fake_raasi(jd):
    """Test double for solar rasi: Simha/Dhanur/Makara/Mesha via sunrise_jd."""
    if jd >= 2000:
        return 1
    if jd >= 1000:
        return 10
    if jd >= 900:
        return 9
    if jd >= 700:
        return 5
    if 0 < jd < 700:
        return 8
    return 9


def festival_record(civil_date, tithi, masa="1", is_adhika=False, nakshatra=1, sunrise_jd=0.0):
    """One festival record: civil_date, tithi, nakshatra, masa, is_adhika, sunrise_jd."""
    return (civil_date, tithi, nakshatra, masa, is_adhika, sunrise_jd)


def append_solar_coverage_rows(rows):
    """Append synthetic rows for Upakarma, solar, and Vaikuntha coverage."""
    # Bhadrapada Hasta primary and Sravana Hasta eclipse fallback for Sama.
    rows.append(day_row(len(rows) + 1, "K2", "5", nakshatra=13, sunrise_jd=600.0))
    rows.append(day_row(len(rows) + 1, "K3", "6", nakshatra=13, sunrise_jd=650.0))
    # Sravana nakshatra while Sun is in Simha (jd 700 → raasi 5 in tests).
    # Neutral lunar masa/tithi so Rig/Bali/etc. do not also match this row.
    rows.append(day_row(len(rows) + 1, "K1", "3", nakshatra=22, sunrise_jd=700.0))
    # Pausha S11 (not Margasira) so this row does not also match Gita Jayanti.
    rows.append(day_row(len(rows) + 1, "S11", "10", sunrise_jd=900.0))
    rows.append(day_row(len(rows) + 1, "S12", "9", sunrise_jd=1000.0))
    rows.append(day_row(len(rows) + 1, "S13", "9", sunrise_jd=2000.0))
    return rows


def covering_tithi_rows():
    """Synthetic day rows for every plain-tithi festival, plus Sravana Purnima."""
    rows = []
    for name, masa, tithi in FESTIVAL_RULES:
        if masa is None:
            continue
        nakshatra = 22 if name == "Naga Panchami" else 1
        # Keep Gita Jayanti out of Dhanur so Vaikuntha coverage stays on its own row.
        sunrise_jd = 400.0 if name == "Gita Jayanti" else 0.0
        rows.append(day_row(len(rows) + 1, tithi, str(masa), nakshatra=nakshatra, sunrise_jd=sunrise_jd))
        if name == "Naga Panchami":
            rows.append(day_row(len(rows) + 1, "S15", "5"))
    return rows


def covering_months_and_data(year=2030, start_month=1):
    """Synthetic months containing every catalog festival once."""
    return sequential_month_data(append_solar_coverage_rows(covering_tithi_rows()), year, start_month)


def covering_month_data(year=2030, month=1):
    """Synthetic month_data containing every catalog festival once."""
    _months, month_data = covering_months_and_data(year, month)
    return month_data


def sequential_month_data(row_specs, year=2030, start_month=1):
    """Pack ``day_row``-like specs into valid civil months (day field ignored)."""
    month_data = {}
    months = []
    y, month = year, start_month
    day = 1
    bucket = []
    for _ignored_day, tithi, nakshatra, yoga, masa, is_adhika, sunrise_jd in row_specs:
        last = calendar.monthrange(y, month)[1]
        if day > last:
            month_data[(y, month)] = bucket
            months.append((y, month))
            bucket = []
            day = 1
            month += 1
            if month > 12:
                month = 1
                y += 1
        bucket.append((day, tithi, nakshatra, yoga, masa, is_adhika, sunrise_jd))
        day += 1
    if bucket:
        month_data[(y, month)] = bucket
        months.append((y, month))
    return months, month_data


def entries_by_name(entries):
    """Map festival name → ``(marker, date_text)`` from resolve_festivals entries."""
    return {name: (marker, date_text) for marker, date_text, name in entries}


def dates_for_marker(by_date, marker):
    """Civil dates that carry ``marker`` in resolve_festivals output."""
    return sorted(civil_date for civil_date, markers in by_date.items() if marker in markers)


class FestivalCatalogTests(unittest.TestCase):

    def test_catalog_is_seasonal_and_complete(self):
        self.assertEqual(len(FESTIVAL_RULES), 38)
        self.assertEqual(FESTIVAL_RULES[0], ("Ugadi", 1, "S1"))
        self.assertEqual(FESTIVAL_RULES[-1], ("Kama Dahana (Holi)", 12, "S15"))
        self.assertIn(("Ananta Chaturdashi", 6, "S14"), FESTIVAL_RULES)
        self.assertIn(("Surya Shashthi / Chhath", 8, "S6"), FESTIVAL_RULES)
        self.assertIn(("Gita Jayanti", 9, "S11"), FESTIVAL_RULES)
        self.assertIn(("Hanuman Jayanti", 1, "S15"), FESTIVAL_RULES)
        self.assertIn(("Karwa Chauth", 7, "K4"), FESTIVAL_RULES)
        self.assertIn(("Sama Upakarma", None, None), FESTIVAL_RULES)
        self.assertIn(("Raksha Bandhan", 5, "S15"), FESTIVAL_RULES)
        self.assertIn(("Onam", None, None), FESTIVAL_RULES)
        self.assertIn(("Mesha Sankranti", None, None), FESTIVAL_RULES)
        self.assertEqual(FESTIVAL_RULES[FESTIVAL_RULES.index(("Rama Navami", 1, "S9")) + 1],
                         ("Hanuman Jayanti", 1, "S15"))
        self.assertEqual(FESTIVAL_RULES[FESTIVAL_RULES.index(("Hanuman Jayanti", 1, "S15")) + 1],
                         ("Mesha Sankranti", None, None))
        self.assertEqual(FESTIVAL_RULES[FESTIVAL_RULES.index(("Yajur Upakarma", None, None)) + 1],
                         ("Raksha Bandhan", 5, "S15"))
        self.assertEqual(FESTIVAL_RULES[FESTIVAL_RULES.index(("Raksha Bandhan", 5, "S15")) + 1],
                         ("Sama Upakarma", None, None))
        self.assertEqual(FESTIVAL_RULES[FESTIVAL_RULES.index(("Sama Upakarma", None, None)) + 1],
                         ("Onam", None, None))
        self.assertEqual(FESTIVAL_RULES[FESTIVAL_RULES.index(("Vijayadashami", 7, "S10")) + 1],
                         ("Karwa Chauth", 7, "K4"))
        self.assertEqual(FESTIVAL_RULES[FESTIVAL_RULES.index(("Surya Shashthi / Chhath", 8, "S6")) + 1],
                         ("Gita Jayanti", 9, "S11"))
        self.assertEqual(FESTIVAL_RULES[FESTIVAL_RULES.index(("Ganesha Chaturthi", 6, "S4")) + 1],
                         ("Ananta Chaturdashi", 6, "S14"))
        names = [name for name, _masa, _tithi in FESTIVAL_RULES]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(all_festival_names(), tuple(names))
        self.assertEqual(sum(1 for _name, masa, _tithi in FESTIVAL_RULES if masa is None), 8)


class FestivalSelectionTests(unittest.TestCase):

    def test_shipped_cfg_enables_full_catalog_except_disabled(self):
        enabled = load_festival_selection(DEFAULT_FESTIVALS_PATH)
        self.assertEqual(enabled, frozenset(all_festival_names()) - {
            "Surya Shashthi / Chhath", "Gita Jayanti", "Vasavi Jayanti", "Vasavi Atmarpana",
            "Karwa Chauth", "VSN Jayanti", "Mesha Sankranti", "Makara Sankranti",
            "Raksha Bandhan", "Sama Upakarma",
        })

    def test_disable_one_festival_uses_dense_markers(self):
        lines = ["[festivals]"]
        for name in all_festival_names():
            value = "no" if name == "Ugadi" else "yes"
            lines.append(f"{name} = {value}")
        with TemporaryDirectory() as directory:
            path = Path(directory) / "festivals.cfg"
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            enabled = load_festival_selection(path)

        months, month_data = covering_months_and_data()
        with mock.patch("festival_rules.panchanga.raasi", side_effect=fake_raasi):
            by_date, entries = resolve_festivals(months, month_data, enabled_names=enabled)
        self.assertNotIn("Ugadi", [name for _marker, _dates, name in entries])
        self.assertEqual(entries[0], (1, "Jan 02", "Rama Navami"))
        self.assertEqual([marker for marker, _dates, _name in entries], list(range(1, len(entries) + 1)))
        self.assertIn(1, [n for nums in by_date.values() for n in nums])

    def test_unknown_name_raises(self):
        body = "[festivals]\n" + "\n".join(f"{name} = yes" for name in all_festival_names())
        body += "\nExtra Festival = yes\n"
        with TemporaryDirectory() as directory:
            path = Path(directory) / "festivals.cfg"
            path.write_text(body, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Unknown festival"):
                load_festival_selection(path)

    def test_missing_name_raises(self):
        names = list(all_festival_names())
        body = "[festivals]\n" + "\n".join(f"{name} = yes" for name in names[1:])
        with TemporaryDirectory() as directory:
            path = Path(directory) / "festivals.cfg"
            path.write_text(body + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Missing festival"):
                load_festival_selection(path)

    def test_duplicate_name_raises(self):
        body = "[festivals]\n" + "\n".join(f"{name} = yes" for name in all_festival_names())
        body += "\nUgadi = no\n"
        with TemporaryDirectory() as directory:
            path = Path(directory) / "festivals.cfg"
            path.write_text(body, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Duplicate festival"):
                load_festival_selection(path)


class CollectRecordsTests(unittest.TestCase):

    def test_keeps_sunrise_identity_fields(self):
        months = [(2026, 6)]
        month_data = {
            (2026, 6): [day_row(1, "S1", "3", nakshatra=5)],
        }
        self.assertEqual(collect_records(months, month_data), [(date(2026, 6, 1), "S1", 5, "3", False, 0.0)])


class ResolveVriddhiTests(unittest.TestCase):

    def test_keeps_former_date_of_consecutive_sunrises(self):
        self.assertEqual(
            resolve_vriddhi_dates([
                date(2030, 5, 6),
                date(2030, 5, 5),
                date(2030, 5, 7),
                date(2030, 8, 10),
                date(2030, 8, 11),
            ]), [date(2030, 5, 5), date(2030, 8, 10)])

    def test_leaves_isolated_dates_unchanged(self):
        self.assertEqual(resolve_vriddhi_dates([date(2030, 3, 10), date(2030, 4, 9)]),
                         [date(2030, 3, 10), date(2030, 4, 9)])


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
        self.assertEqual(select_plain_tithi_dates(self.records, 1, "S9"), [date(2030, 3, 18)])
        self.assertEqual(select_plain_tithi_dates(self.records, 2, "S3"), [date(2030, 5, 2)])

    def test_skips_adhika_by_default(self):
        self.assertEqual(select_plain_tithi_dates(self.records, 1, "S1"), [date(2030, 4, 9)])

    def test_ugadi_prefers_adhika_chaitra(self):
        self.assertEqual(select_plain_tithi_dates(self.records, 1, "S1", allow_adhika=True), [date(2030, 3, 10)])

    def test_ugadi_keeps_nija_when_no_adhika(self):
        records = [
            festival_record(date(2030, 4, 9), "S1", masa="1"),
        ]
        self.assertEqual(select_plain_tithi_dates(records, 1, "S1", allow_adhika=True), [date(2030, 4, 9)])

    def test_vriddhi_keeps_former_of_consecutive_matches(self):
        records = [
            (date(2030, 8, 14), "K8", 1, "5", False, 0.0),
            (date(2030, 8, 15), "K8", 1, "5", False, 0.0),
            (date(2030, 8, 16), "K9", 1, "5", False, 0.0),
        ]
        self.assertEqual(select_plain_tithi_dates(records, 5, "K8"), [date(2030, 8, 14)])

    def test_kshaya_marks_later_civil_date(self):
        records = [
            (date(2030, 5, 4), "S2", 1, "2", False, 0.0),
            (date(2030, 5, 5), "S4", 1, "2", False, 0.0),
        ]
        self.assertEqual(select_plain_tithi_dates(records, 2, "S3"), [date(2030, 5, 5)])

    def test_kshaya_ugadi_across_masa_boundary(self):
        records = [
            (date(2030, 3, 25), "K15", 1, "12", False, 0.0),
            (date(2030, 3, 26), "S2", 1, "1", False, 0.0),
        ]
        self.assertEqual(select_plain_tithi_dates(records, 1, "S1", allow_adhika=True), [date(2030, 3, 26)])

    def test_kshaya_krishna_across_masa_boundary(self):
        records = [
            (date(2030, 10, 20), "K14", 1, "7", False, 0.0),
            (date(2030, 10, 21), "S1", 1, "8", False, 0.0),
        ]
        self.assertEqual(select_plain_tithi_dates(records, 7, "K15"), [date(2030, 10, 21)])
        self.assertEqual(select_plain_tithi_dates(records, 8, "K15"), [])


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
        self.assertEqual(select_kshaya_dates(records, "S3", masa=2), [date(2030, 5, 5)])

    def test_ugadi_between_phalguna_amavasya_and_caitra_dvitiya(self):
        records = [
            (date(2030, 3, 25), "K15", 1, "12", False, 0.0),
            (date(2030, 3, 26), "S2", 1, "1", False, 0.0),
        ]
        self.assertEqual(select_kshaya_dates(records, "S1", masa=1, allow_adhika=True), [date(2030, 3, 26)])

    def test_ignores_non_consecutive_civil_days(self):
        records = [
            (date(2030, 5, 4), "S2", 1, "2", False, 0.0),
            (date(2030, 5, 6), "S4", 1, "2", False, 0.0),
        ]
        self.assertEqual(select_kshaya_dates(records, "S3", masa=2), [])


class FormatFestivalDatesTests(unittest.TestCase):

    def test_formats_empty_single_range_and_scattered(self):
        self.assertEqual(format_festival_dates([]), "None")
        self.assertEqual(format_festival_dates([date(2026, 3, 19)]), "Mar 19")
        self.assertEqual(format_festival_dates([date(2026, 3, 19), date(2026, 3, 20)]), "Mar 19-20")
        self.assertEqual(format_festival_dates([date(2026, 3, 19), date(2026, 4, 1)]), "Mar 19,Apr 01")


class ResolveFestivalsTests(unittest.TestCase):

    def setUp(self):
        self.raasi_patcher = mock.patch("festival_rules.panchanga.raasi", side_effect=fake_raasi)
        self.raasi_patcher.start()
        self.addCleanup(self.raasi_patcher.stop)

    def test_resolves_markers_and_footer_entries(self):
        months, month_data = covering_months_and_data()
        by_date, entries = resolve_festivals(months, month_data)
        by_name = entries_by_name(entries)

        self.assertEqual([name for _marker, _dates, name in entries], list(all_festival_names()))
        self.assertEqual([marker for marker, _dates, _name in entries], list(range(1, len(FESTIVAL_RULES) + 1)))

        # Seasonal order among mixed tithi / non-tithi neighbors.
        self.assertLess(by_name["Yajur Upakarma"][0], by_name["Onam"][0])
        self.assertLess(by_name["Yajur Upakarma"][0], by_name["Raksha Bandhan"][0])
        self.assertLess(by_name["Raksha Bandhan"][0], by_name["Onam"][0])
        self.assertLess(by_name["Raksha Bandhan"][0], by_name["Sama Upakarma"][0])
        self.assertLess(by_name["Sama Upakarma"][0], by_name["Onam"][0])
        self.assertLess(by_name["Onam"][0], by_name["Janmashtami"][0])
        self.assertLess(by_name["Vijayadashami"][0], by_name["Karwa Chauth"][0])
        self.assertLess(by_name["Vaikuntha Ekadashi"][0], by_name["Makara Sankranti"][0])
        self.assertLess(by_name["Hanuman Jayanti"][0], by_name["Mesha Sankranti"][0])

        # Every resolved festival has a footer date string and matching day markers.
        for marker, date_text, name in entries:
            self.assertNotEqual(date_text, "None", name)
            marked = dates_for_marker(by_date, marker)
            self.assertTrue(marked, name)
            self.assertEqual(by_name[name][0], marker)

        # Covering fixture co-locations that the solar/nakshatra stubs must preserve.
        naga = dates_for_marker(by_date, by_name["Naga Panchami"][0])
        rig = dates_for_marker(by_date, by_name["Rig Upakarma"][0])
        self.assertTrue(set(naga) & set(rig), "Rig shares the Sravana-nakshatra covering day with Naga")
        onam = dates_for_marker(by_date, by_name["Onam"][0])
        self.assertEqual(len(onam), 1)
        self.assertNotIn(onam[0], rig)

    def test_ugadi_marks_adhika_chaitra_s1(self):
        rows = []
        for name, masa, tithi in FESTIVAL_RULES:
            if masa is None:
                continue
            nakshatra = 22 if name == "Naga Panchami" else 1
            if name == "Ugadi":
                rows.append(day_row(len(rows) + 1, "S1", "A1", is_adhika=True, nakshatra=nakshatra))
            else:
                rows.append(day_row(len(rows) + 1, tithi, str(masa), nakshatra=nakshatra))
            if name == "Naga Panchami":
                rows.append(day_row(len(rows) + 1, "S15", "5"))
        append_solar_coverage_rows(rows)
        months, month_data = sequential_month_data(rows, year=2030, start_month=3)

        by_date, entries = resolve_festivals(months, month_data)
        ugadi_marker, ugadi_dates = entries_by_name(entries)["Ugadi"]
        self.assertEqual(ugadi_marker, 1)
        self.assertEqual(ugadi_dates, "Mar 01")
        self.assertEqual(dates_for_marker(by_date, 1), [date(2030, 3, 1)])

    def test_non_ugadi_festivals_skip_adhika_masa(self):
        months, month_data = covering_months_and_data()
        records = collect_records(months, month_data)
        akshaya_dates = select_plain_tithi_dates(records, 2, "S3")
        self.assertEqual(len(akshaya_dates), 1)
        civil = akshaya_dates[0]
        rows = month_data[(civil.year, civil.month)]
        rows[civil.day - 1] = day_row(civil.day, "S3", "A2", is_adhika=True)

        with self.assertRaisesRegex(RuntimeError, "Akshaya Tritiya"):
            resolve_festivals(months, month_data)

    def test_context_matches_are_clipped_to_target_months(self):
        target_months, target_data = covering_months_and_data(2030, 3)
        context_months = [(2030, 2)] + target_months
        context_data = {
            (2030, 2): [day_row(1, "S1", "1")],
            **target_data,
        }
        target_data[(2030, 3)][0] = day_row(1, "S1", "1")

        by_date, entries = resolve_festivals(target_months, target_data, context_months=context_months,
                                             context_data=context_data)
        ugadi_marker, ugadi_dates = entries_by_name(entries)["Ugadi"]
        self.assertEqual((ugadi_marker, ugadi_dates), (1, "Mar 01"))
        self.assertNotIn(date(2030, 2, 1), by_date)

    def test_context_arguments_must_be_paired(self):
        with self.assertRaisesRegex(ValueError, "context_months"):
            resolve_festivals([(2030, 1)], covering_month_data(), context_months=[])

    def test_raises_when_a_festival_has_no_date(self):
        months, month_data = covering_months_and_data()
        month_data[(2030, 1)][0] = day_row(1, "S2", "1")

        with self.assertRaisesRegex(RuntimeError, "Ugadi"):
            resolve_festivals(months, month_data)

    def test_vriddhi_marks_only_the_former_date(self):
        rows = []
        day = 1
        for name, masa, tithi in FESTIVAL_RULES:
            if masa is None:
                continue
            nakshatra = 22 if name == "Naga Panchami" else 1
            rows.append(day_row(day, tithi, str(masa), nakshatra=nakshatra))
            if name == "Naga Panchami":
                day += 1
                rows.append(day_row(day, "S15", "5"))
            if name == "Janmashtami":
                day += 1
                rows.append(day_row(day, tithi, str(masa)))
            day += 1
        append_solar_coverage_rows(rows)
        months, month_data = sequential_month_data(rows)

        by_date, entries = resolve_festivals(months, month_data)
        marker, _date_text = entries_by_name(entries)["Janmashtami"]
        marked = dates_for_marker(by_date, marker)
        self.assertEqual(len(marked), 1)
        former = marked[0]
        latter = former + timedelta(days=1)
        self.assertNotIn(marker, by_date.get(latter, []))

    def test_kshaya_marks_later_date_in_calendar(self):
        rows = []
        day = 1
        for name, masa, tithi in FESTIVAL_RULES:
            if masa is None:
                continue
            nakshatra = 22 if name == "Naga Panchami" else 1
            if name == "Akshaya Tritiya":
                rows.append(day_row(day, "S2", "2"))
                day += 1
                rows.append(day_row(day, "S4", "2"))
            else:
                rows.append(day_row(day, tithi, str(masa), nakshatra=nakshatra))
            if name == "Naga Panchami":
                day += 1
                rows.append(day_row(day, "S15", "5"))
            day += 1
        append_solar_coverage_rows(rows)
        months, month_data = sequential_month_data(rows)

        by_date, entries = resolve_festivals(months, month_data)
        marker, _date_text = entries_by_name(entries)["Akshaya Tritiya"]
        marked = dates_for_marker(by_date, marker)
        self.assertEqual(len(marked), 1)
        # Kshaya S2→S4 keeps the later civil day (the S4 sunrise).
        records = collect_records(months, month_data)
        self.assertEqual(
            next(tithi for civil, tithi, *_ in records if civil == marked[0]),
            "S4")


class VaramahalakshmiTests(unittest.TestCase):

    def test_uses_friday_immediately_before_sravana_purnima(self):
        # 2030-08-10 is Saturday, so preceding Friday is 08-09.
        records = [
            (date(2030, 8, 9), "S14", 1, "5", False, 0.0),
            (date(2030, 8, 10), "S15", 1, "5", False, 0.0),
            (date(2030, 8, 11), "K1", 1, "5", False, 0.0),
        ]
        self.assertEqual(select_varamahalakshmi_dates(records), [date(2030, 8, 9)])

    def test_friday_purnima_uses_previous_week_friday(self):
        # 2030-08-16 is Friday; rule still chooses the prior Friday.
        records = [
            (date(2030, 8, 15), "S14", 1, "5", False, 0.0),
            (date(2030, 8, 16), "S15", 1, "5", False, 0.0),
            (date(2030, 8, 17), "K1", 1, "5", False, 0.0),
        ]
        self.assertEqual(select_varamahalakshmi_dates(records), [date(2030, 8, 9)])

    def test_vriddhi_purnima_anchors_on_former_sunrise(self):
        # 2030-08-09 is Friday; former S15 sunrise is 08-09, so prior Friday
        # is 08-02.
        records = [
            (date(2030, 8, 8), "S14", 1, "5", False, 0.0),
            (date(2030, 8, 9), "S15", 1, "5", False, 0.0),
            (date(2030, 8, 10), "S15", 1, "5", False, 0.0),
        ]
        self.assertEqual(select_varamahalakshmi_dates(records), [date(2030, 8, 2)])

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
        self.assertEqual(select_non_tithi_dates(records, "Varamahalakshmi Vrata"), [date(2030, 8, 9)])

    def test_dispatcher_rejects_unknown_festival(self):
        with self.assertRaisesRegex(ValueError, "No selector"):
            select_non_tithi_dates([], "Unknown Vrata")


class RigUpakarmaTests(unittest.TestCase):

    def test_selects_nija_sravana_with_sravana_nakshatra(self):
        records = [
            (date(2030, 8, 10), "S12", 22, "5", False, 0.0),
            (date(2030, 8, 11), "S13", 23, "5", False, 0.0),
        ]
        self.assertEqual(select_rig_upakarma_dates(records), [date(2030, 8, 10)])

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
        self.assertEqual(select_rig_upakarma_dates(records), [date(2030, 8, 10)])

    def test_kshaya_sravana_postpones_to_bhadrapada(self):
        # Sravana masa skips nakshatra 22 between sunrises (21 -> 23).
        records = [
            (date(2022, 8, 11), "S14", 21, "5", False, 0.0),
            (date(2022, 8, 12), "S15", 23, "5", False, 0.0),
            (date(2022, 9, 8), "S11", 22, "6", False, 0.0),
            (date(2022, 9, 9), "S12", 23, "6", False, 0.0),
        ]
        self.assertEqual(select_rig_upakarma_dates(records), [date(2022, 9, 8)])

    def test_prefers_sravana_masa_over_bhadrapada(self):
        records = [
            (date(2030, 8, 10), "S12", 22, "5", False, 0.0),
            (date(2030, 9, 8), "S11", 22, "6", False, 0.0),
        ]
        self.assertEqual(select_rig_upakarma_dates(records), [date(2030, 8, 10)])

    def test_eclipse_on_sravana_day_postpones_to_bhadrapada(self):
        records = [
            (date(2030, 8, 9), "S11", 21, "5", False, 10.0),
            (date(2030, 8, 10), "S12", 22, "5", False, 11.0),
            (date(2030, 8, 11), "S13", 23, "5", False, 12.0),
            (date(2030, 9, 7), "S10", 21, "6", False, 40.0),
            (date(2030, 9, 8), "S11", 22, "6", False, 41.0),
            (date(2030, 9, 9), "S12", 23, "6", False, 42.0),
        ]
        geopos = (79.42, 13.65, 0.0)
        with mock.patch("festival_rules.civil_day_has_eclipse",
                        side_effect=lambda civil_date, geopos, timezone_name: civil_date == date(2030, 8, 10)):
            self.assertEqual(select_rig_upakarma_dates(records, geopos=geopos, timezone_name="Asia/Kolkata"),
                             [date(2030, 9, 8)])


class SamaUpakarmaTests(unittest.TestCase):

    def test_selects_bhadrapada_hasta(self):
        records = [
            (date(2030, 9, 8), "S12", 13, "6", False, 0.0),
            (date(2030, 9, 9), "S13", 14, "6", False, 0.0),
        ]
        self.assertEqual(select_sama_upakarma_dates(records), [date(2030, 9, 8)])

    def test_prefers_bhadrapada_hasta_over_sravana(self):
        records = [
            (date(2030, 8, 10), "S12", 13, "5", False, 0.0),
            (date(2030, 9, 8), "S11", 13, "6", False, 0.0),
        ]
        self.assertEqual(select_sama_upakarma_dates(records), [date(2030, 9, 8)])

    def test_eclipse_on_bhadrapada_hasta_postpones_to_sravana_hasta(self):
        records = [
            (date(2030, 8, 9), "S11", 12, "5", False, 10.0),
            (date(2030, 8, 10), "S12", 13, "5", False, 11.0),
            (date(2030, 8, 11), "S13", 14, "5", False, 12.0),
            (date(2030, 9, 7), "S10", 12, "6", False, 40.0),
            (date(2030, 9, 8), "S11", 13, "6", False, 41.0),
            (date(2030, 9, 9), "S12", 14, "6", False, 42.0),
        ]
        geopos = (79.42, 13.65, 0.0)
        with mock.patch(
                "festival_rules.civil_day_has_eclipse",
                side_effect=lambda civil_date, geopos, timezone_name: civil_date == date(2030, 9, 8)):
            self.assertEqual(
                select_sama_upakarma_dates(
                    records, geopos=geopos, timezone_name="Asia/Kolkata"),
                [date(2030, 8, 10)])

    def test_dispatcher_routes_by_name(self):
        records = [
            (date(2030, 9, 8), "S12", 13, "6", False, 0.0),
        ]
        self.assertEqual(
            select_non_tithi_dates(records, "Sama Upakarma"),
            [date(2030, 9, 8)])


class OnamTests(unittest.TestCase):

    def test_selects_sravana_nakshatra_in_simha(self):
        records = [
            (date(2030, 8, 20), "S5", 22, "5", False, 10.0),
            (date(2030, 8, 21), "S6", 23, "5", False, 11.0),
        ]
        with mock.patch("festival_rules.panchanga.raasi", side_effect=lambda jd: 5 if jd >= 10.0 else 4):
            self.assertEqual(select_onam_dates(records), [date(2030, 8, 20)])

    def test_vriddhi_keeps_former_sunrise(self):
        records = [
            (date(2030, 8, 20), "S5", 22, "5", False, 10.0),
            (date(2030, 8, 21), "S6", 22, "5", False, 11.0),
        ]
        with mock.patch("festival_rules.panchanga.raasi", return_value=5):
            self.assertEqual(select_onam_dates(records), [date(2030, 8, 20)])

    def test_missing_simha_falls_back_to_kanya(self):
        records = [
            (date(2030, 8, 20), "S5", 21, "5", False, 10.0),
            (date(2030, 8, 21), "S6", 23, "5", False, 11.0),
            (date(2030, 9, 16), "S10", 22, "6", False, 20.0),
        ]
        with mock.patch("festival_rules.panchanga.raasi",
                        side_effect=lambda jd: 5 if jd < 20.0 else 6):
            self.assertEqual(select_onam_dates(records), [date(2030, 9, 16)])

    def test_prefers_simha_over_kanya(self):
        records = [
            (date(2030, 8, 20), "S5", 22, "5", False, 10.0),
            (date(2030, 9, 16), "S10", 22, "6", False, 20.0),
        ]
        with mock.patch("festival_rules.panchanga.raasi",
                        side_effect=lambda jd: 5 if jd < 20.0 else 6):
            self.assertEqual(select_onam_dates(records), [date(2030, 8, 20)])

    def test_dispatcher_routes_by_name(self):
        records = [
            (date(2030, 8, 20), "S5", 22, "5", False, 10.0),
        ]
        with mock.patch("festival_rules.panchanga.raasi", return_value=5):
            self.assertEqual(select_non_tithi_dates(records, "Onam"), [date(2030, 8, 20)])


class YajurUpakarmaTests(unittest.TestCase):

    def test_selects_sravana_purnima(self):
        records = [
            (date(2030, 8, 14), "S14", 1, "5", False, 0.0),
            (date(2030, 8, 15), "S15", 1, "5", False, 0.0),
            (date(2030, 8, 16), "K1", 1, "5", False, 0.0),
        ]
        self.assertEqual(select_yajur_upakarma_dates(records), [date(2030, 8, 15)])

    def test_eclipse_on_sravana_purnima_postpones_to_bhadrapada(self):
        records = [
            (date(2030, 8, 14), "S14", 1, "5", False, 10.0),
            (date(2030, 8, 15), "S15", 1, "5", False, 11.0),
            (date(2030, 8, 16), "K1", 1, "5", False, 12.0),
            (date(2030, 9, 13), "S14", 1, "6", False, 40.0),
            (date(2030, 9, 14), "S15", 1, "6", False, 41.0),
            (date(2030, 9, 15), "K1", 1, "6", False, 42.0),
        ]
        geopos = (79.42, 13.65, 0.0)
        with mock.patch("festival_rules.civil_day_has_eclipse",
                        side_effect=lambda civil_date, geopos, timezone_name: civil_date == date(2030, 8, 15)):
            self.assertEqual(select_yajur_upakarma_dates(records, geopos=geopos, timezone_name="Asia/Kolkata"),
                             [date(2030, 9, 14)])

    def test_helsinki_pre_sunrise_eclipse_postpones_to_bhadrapada(self):
        location = load_location("Helsinki")
        panchanga.set_chosen_ayanamsa("citra")
        months = list(month_range(2026, 5, count=6))
        month_data = {(year, month): daily_values(year, month, location) for year, month in months}
        records = collect_records(months, month_data)
        geopos = (location.longitude, location.latitude, 0.0)

        self.assertEqual(select_yajur_upakarma_dates(records, geopos=geopos, timezone_name=location.timezone_name),
                         [date(2026, 9, 26)])


class VaikunthaEkadashiTests(unittest.TestCase):

    def test_keeps_margasira_s11_in_dhanur(self):
        records = [
            (date(2030, 12, 5), "S11", 1, "9", False, 10.0),
            (date(2030, 12, 20), "S11", 1, "10", False, 20.0),
        ]
        with mock.patch("festival_rules.panchanga.raasi", side_effect=lambda jd: 9 if jd == 10.0 else 10):
            self.assertEqual(select_vaikuntha_ekadashi_dates(records), [date(2030, 12, 5)])

    def test_keeps_pausha_s11_in_dhanur(self):
        records = [
            (date(2030, 12, 5), "S11", 1, "9", False, 10.0),
            (date(2030, 12, 20), "S11", 1, "10", False, 20.0),
        ]
        with mock.patch("festival_rules.panchanga.raasi", side_effect=lambda jd: 9 if jd == 20.0 else 8):
            self.assertEqual(select_vaikuntha_ekadashi_dates(records), [date(2030, 12, 20)])

    def test_rejects_non_dhanur_candidates(self):
        records = [
            (date(2030, 12, 5), "S11", 1, "9", False, 10.0),
        ]
        with mock.patch("festival_rules.panchanga.raasi", return_value=8):
            self.assertEqual(select_vaikuntha_ekadashi_dates(records), [])

    def test_uses_shared_ekadashi_kshaya_day(self):
        # S11 skipped between sunrises; upavasa is the following (S12) day.
        records = [
            (date(2030, 12, 4), "S10", 1, "9", False, 10.0),
            (date(2030, 12, 5), "S12", 1, "9", False, 11.0),
            (date(2030, 12, 6), "S13", 1, "9", False, 12.0),
        ]
        with mock.patch("festival_rules.panchanga.raasi", return_value=9):
            self.assertEqual(select_vaikuntha_ekadashi_dates(records), [date(2030, 12, 5)])

    def test_vaikuntha_ekadashi_may_print_none(self):
        """Tirupati 2086: no Margasira/Pausha S11 while the Sun is in Dhanur."""
        location = load_location("Tirupati")
        panchanga.set_chosen_ayanamsa("citra")
        months = list(month_range(2086, 3))
        context_months = list(month_range(2086, 2, count=MONTH_COUNT + 2))
        context_data = {(year, month): daily_values(year, month, location) for year, month in context_months}
        month_data = {(year, month): context_data[(year, month)] for year, month in months}

        by_date, entries = resolve_festivals(months, month_data, context_months=context_months,
                                             context_data=context_data)

        vaikuntha_marker, vaikuntha_dates = entries_by_name(entries)["Vaikuntha Ekadashi"]
        self.assertEqual(vaikuntha_dates, "None")
        self.assertNotIn(vaikuntha_marker, [n for nums in by_date.values() for n in nums])
        records = collect_records(context_months, context_data)
        self.assertEqual(select_vaikuntha_ekadashi_dates(records), [])
        margasira = select_plain_tithi_dates(records, 9, "S11")
        pausha = select_plain_tithi_dates(records, 10, "S11")
        self.assertEqual(margasira, [date(2086, 12, 16)])
        self.assertEqual(pausha, [date(2087, 1, 15)])
        records_by_date = {record[CIVIL_DATE]: record for record in records}
        self.assertEqual(panchanga.raasi(records_by_date[margasira[0]][SUNRISE_JD]), 8)
        self.assertEqual(panchanga.raasi(records_by_date[pausha[0]][SUNRISE_JD]), 10)


class MakaraSankrantiTests(unittest.TestCase):

    def test_marks_first_sunrise_in_makara(self):
        records = [
            (date(2030, 1, 13), "S10", 1, "10", False, 10.0),
            (date(2030, 1, 14), "S11", 1, "10", False, 20.0),
            (date(2030, 1, 15), "S12", 1, "10", False, 30.0),
        ]
        with mock.patch("festival_rules.panchanga.raasi", side_effect=lambda jd: 10 if jd >= 20.0 else 9):
            self.assertEqual(select_makara_sankranti_dates(records), [date(2030, 1, 14)])

    def test_ignores_range_that_opens_already_in_makara(self):
        records = [
            (date(2030, 1, 14), "S11", 1, "10", False, 20.0),
            (date(2030, 1, 15), "S12", 1, "10", False, 30.0),
        ]
        with mock.patch("festival_rules.panchanga.raasi", return_value=10):
            self.assertEqual(select_makara_sankranti_dates(records), [])


class MeshaSankrantiTests(unittest.TestCase):

    def test_marks_first_sunrise_in_mesha(self):
        records = [
            (date(2030, 4, 13), "S10", 1, "1", False, 10.0),
            (date(2030, 4, 14), "S11", 1, "1", False, 20.0),
            (date(2030, 4, 15), "S12", 1, "1", False, 30.0),
        ]
        with mock.patch("festival_rules.panchanga.raasi", side_effect=lambda jd: 1 if jd >= 20.0 else 12):
            self.assertEqual(select_mesha_sankranti_dates(records), [date(2030, 4, 14)])

    def test_ignores_range_that_opens_already_in_mesha(self):
        records = [
            (date(2030, 4, 14), "S11", 1, "1", False, 20.0),
            (date(2030, 4, 15), "S12", 1, "1", False, 30.0),
        ]
        with mock.patch("festival_rules.panchanga.raasi", return_value=1):
            self.assertEqual(select_mesha_sankranti_dates(records), [])


class AllSankrantiTests(unittest.TestCase):

    def test_maps_each_raasi_transition(self):
        records = [
            (date(2030, 1, 13), "S10", 1, "10", False, 10.0),
            (date(2030, 1, 14), "S11", 1, "10", False, 20.0),
            (date(2030, 2, 12), "S10", 1, "11", False, 30.0),
            (date(2030, 2, 13), "S11", 1, "11", False, 40.0),
            (date(2030, 4, 13), "S10", 1, "1", False, 50.0),
            (date(2030, 4, 14), "S11", 1, "1", False, 60.0),
        ]

        def raasi_for(jd):
            if jd < 20.0:
                return 9
            if jd < 40.0:
                return 10
            if jd < 60.0:
                return 12
            return 1

        with mock.patch("festival_rules.panchanga.raasi", side_effect=raasi_for):
            self.assertEqual(
                sankranti_raasi_by_date(records),
                {
                    date(2030, 1, 14): 10,
                    date(2030, 2, 13): 12,
                    date(2030, 4, 14): 1,
                },
            )
            self.assertEqual(select_makara_sankranti_dates(records), [date(2030, 1, 14)])
            self.assertEqual(select_mesha_sankranti_dates(records), [date(2030, 4, 14)])

    def test_ignores_opening_raasi_without_prior_day(self):
        records = [
            (date(2030, 1, 14), "S11", 1, "10", False, 20.0),
            (date(2030, 1, 15), "S12", 1, "10", False, 30.0),
        ]
        with mock.patch("festival_rules.panchanga.raasi", return_value=10):
            self.assertEqual(sankranti_raasi_by_date(records), {})


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
        self.assertEqual(resolve_ekadashi_dates(months, month_data), [
            date(2030, 6, 2),
            date(2030, 6, 10),
            date(2030, 6, 21),
        ])


class GenericUdayaParityTests(unittest.TestCase):
    """Parity with generic-udaya sunrise/vriddhi/kshaya behaviour."""

    def test_plain_tithi_parser_rejects_conditional_rules(self):
        self.assertEqual(plain_tithi_number("S15"), 15)
        self.assertEqual(plain_tithi_number("K15"), 30)
        self.assertIsNone(plain_tithi_number("Dhanur-masa S11"))
        self.assertIsNone(plain_tithi_number("Solar"))

    def test_vriddhi_tithi_uses_first_sunrise(self):
        records = [
            festival_record(date(2030, 8, 4), "S5", masa="5"),
            festival_record(date(2030, 8, 5), "S5", masa="5"),
            festival_record(date(2030, 8, 6), "S6", masa="5"),
        ]
        self.assertEqual(select_plain_tithi_dates(records, 5, "S5"), [date(2030, 8, 4)])

    def test_kshaya_tithi_uses_following_sunrise_date(self):
        records = [
            festival_record(date(2030, 8, 4), "S4", masa="5"),
            festival_record(date(2030, 8, 5), "S6", masa="5"),
        ]
        self.assertEqual(select_plain_tithi_dates(records, 5, "S5"), [date(2030, 8, 5)])

    def test_kshaya_shukla_pratipada_uses_following_masa_metadata(self):
        records = [
            festival_record(date(2030, 5, 1), "K15", masa="1"),
            festival_record(date(2030, 5, 2), "S2", masa="2"),
        ]
        self.assertEqual(select_plain_tithi_dates(records, 2, "S1"), [date(2030, 5, 2)])

    def test_default_month_policy_excludes_adhika_occurrence(self):
        records = [
            festival_record(date(2030, 5, 3), "S3", masa="A2", is_adhika=True),
            festival_record(date(2030, 6, 2), "S3", masa="2"),
        ]
        self.assertEqual(select_plain_tithi_dates(records, 2, "S3"), [date(2030, 6, 2)])

    def test_ugadi_preserves_adhika_chaitra_preference(self):
        records = [
            festival_record(date(2030, 3, 5), "S1", masa="A1", is_adhika=True),
            festival_record(date(2030, 4, 4), "S1", masa="1"),
        ]
        self.assertEqual(select_plain_tithi_dates(records, 1, "S1", allow_adhika=True), [date(2030, 3, 5)])

    def test_rama_navami_uses_plain_tithi_not_a_special_selector(self):
        records = [
            festival_record(date(2030, 4, 11), "S9", masa="1"),
        ]
        self.assertEqual(select_plain_tithi_dates(records, 1, "S9"), [date(2030, 4, 11)])
        self.assertEqual(next(rule for rule in FESTIVAL_RULES if rule[0] == "Rama Navami"), ("Rama Navami", 1, "S9"))

    def test_raksha_bandhan_uses_plain_sravana_purnima(self):
        records = [
            festival_record(date(2030, 8, 15), "S15", masa="5"),
        ]
        self.assertEqual(select_plain_tithi_dates(records, 5, "S15"), [date(2030, 8, 15)])
        self.assertEqual(
            next(rule for rule in FESTIVAL_RULES if rule[0] == "Raksha Bandhan"),
            ("Raksha Bandhan", 5, "S15"))

    def test_normal_single_ekadashi_at_sunrise(self):
        months = [(2030, 3)]
        month_data = {
            (2030, 3): [
                day_row(20, "S11", "1"),
                day_row(21, "S12", "1"),
                day_row(22, "S13", "1"),
            ]
        }
        self.assertEqual(resolve_ekadashi_dates(months, month_data), [date(2030, 3, 20)])

    def test_vriddhi_ekadashi_uses_first_day(self):
        months = [(2030, 3)]
        month_data = {
            (2030, 3): [
                day_row(20, "S11", "1"),
                day_row(21, "S11", "1"),
                day_row(22, "S12", "1"),
            ]
        }
        self.assertEqual(resolve_ekadashi_dates(months, month_data), [date(2030, 3, 20)])

    def test_kshaya_ekadashi_uses_next_day(self):
        months = [(2030, 8)]
        month_data = {
            (2030, 8): [
                day_row(4, "S10", "5"),
                day_row(5, "S12", "5"),
            ]
        }
        self.assertEqual(resolve_ekadashi_dates(months, month_data), [date(2030, 8, 5)])

    def test_both_pakshas_are_resolved(self):
        months = [(2030, 3)]
        month_data = {
            (2030, 3): [
                day_row(6, "S11", "1"),
                day_row(20, "K11", "1"),
            ]
        }
        self.assertEqual(resolve_ekadashi_dates(months, month_data), [date(2030, 3, 6), date(2030, 3, 20)])


if __name__ == "__main__":
    unittest.main()
