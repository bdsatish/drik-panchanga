"""Regression tests for the generated one-page calendar layout."""

from datetime import date
from io import BytesIO
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

from reportlab.pdfgen.canvas import Canvas

from festival_rules import DayRecord
from generate_panchanga_calendar import (
    ACCENT,
    ADHIKA_INK,
    DEFAULT_FESTIVALS_PATH,
    EKADASHI_MARK,
    FOOTER_FESTIVAL_SLOTS,
    KRSNA_INK,
    LAYOUT_VERSION,
    MASA_START_INK,
    PDF_FONT_BOLD,
    PDF_FONT_BOLD_ITALIC,
    PDF_FONT_TTC,
    RULESET_VERSION,
    SANKRANTI_INK,
    argument_parser,
    build_pdf,
    calendar_year_label,
    daily_records,
    default_output_path,
    display_masa,
    draw_page_footer,
    draw_page_header,
    draw_eclipse_mark,
    draw_sankranti_mark,
    draw_solar_day_mark,
    draw_tithi_underline,
    ensure_pdf_fonts,
    fitted_font_size,
    kali_ahargana_range,
    load_location,
    month_range,
    sankranti_key_line,
    solar_dates_by_date,
    tithi_display_parts,
    tithi_font,
    tithi_ink,
)


class PdfLayoutTests(unittest.TestCase):

    def test_generated_calendar_has_exactly_one_page(self):
        import generate_panchanga_calendar as calendar_module

        with TemporaryDirectory() as directory:
            output = Path(directory) / "calendar.pdf"
            with mock.patch("generate_panchanga_calendar.find_local_eclipses", return_value=[
                ("Lunar", "Partial", 2461103.0419131187),
            ]), mock.patch("generate_panchanga_calendar.draw_page_footer",
                           wraps=calendar_module.draw_page_footer) as footer:
                build_pdf(load_location("Helsinki"), 2026, 6, output)
            document = output.read_bytes()

        page_objects = re.findall(rb"/Type\s*/Page\b", document)
        self.assertEqual(len(page_objects), 1)
        self.assertIn(RULESET_VERSION.encode("ascii"), document)
        self.assertIn(LAYOUT_VERSION.encode("ascii"), document)
        self.assertEqual(footer.call_count, 1)
        self.assertIn("Eclipses:", footer.call_args.kwargs["eclipse_line"])
        self.assertNotIn(b"/BaseFont /Helvetica", document)
        self.assertIn(b"IndUni-H", document)

    def test_cli_defaults_festivals_path(self):
        parser = argument_parser()
        arguments = parser.parse_args(["--city", "Helsinki", "--start", "2026-03"])
        self.assertFalse(hasattr(arguments, "festival_policy"))
        self.assertEqual(arguments.festivals, DEFAULT_FESTIVALS_PATH)

    def test_default_filename_has_no_policy_suffix(self):
        path = default_output_path(load_location("Helsinki"), 2026, 3)
        self.assertEqual(path.name, "helsinki-fi_panchanga_2026-03_to_2027-04.pdf")

    def test_purnimanta_filename_suffix(self):
        path = default_output_path(load_location("Helsinki"), 2026, 3, month_system="purnimanta")
        self.assertEqual(path.name, "helsinki-fi_panchanga_2026-03_to_2027-04_purnimanta.pdf")

    def test_ayanamsa_filename_suffix(self):
        path = default_output_path(
            load_location("Helsinki"), 2026, 3, ayanamsa="raman")
        self.assertEqual(path.name, "helsinki-fi_panchanga_2026-03_to_2027-04_raman.pdf")

    def test_tropical_filename_suffix(self):
        path = default_output_path(
            load_location("Helsinki"), 2026, 3, ayanamsa="tropical")
        self.assertEqual(path.name, "helsinki-fi_panchanga_2026-03_to_2027-04_tropical.pdf")

    def test_cli_accepts_month_system(self):
        parser = argument_parser()
        arguments = parser.parse_args(
            ["--city", "Helsinki", "--start", "2026-03", "--month", "purnimanta"])
        self.assertEqual(arguments.month, "purnimanta")

    def test_cli_accepts_ayanamsa(self):
        parser = argument_parser()
        arguments = parser.parse_args(
            ["--city", "Helsinki", "--start", "2026-03", "--ayanamsa", "revati"])
        self.assertEqual(arguments.ayanamsa, "revati")

    def test_cli_accepts_tropical_ayanamsa(self):
        parser = argument_parser()
        arguments = parser.parse_args(
            ["--city", "Helsinki", "--start", "2026-03", "--ayanamsa", "tropical"])
        self.assertEqual(arguments.ayanamsa, "tropical")

    def test_parse_coordinate_selection_accepts_sidereal_and_tropical_modes(self):
        from generate_panchanga_calendar import (
            ayanamsa_label, coordinate_selection_label, parse_coordinate_selection,
        )
        self.assertEqual(parse_coordinate_selection("rohini"), "rohini")
        self.assertEqual(parse_coordinate_selection("rohini-paksha"), "rohini")
        self.assertEqual(parse_coordinate_selection("pushya"), "pushya")
        self.assertEqual(parse_coordinate_selection("true_mula"), "mula")
        self.assertEqual(parse_coordinate_selection("tropical"), "tropical")
        self.assertEqual(parse_coordinate_selection("sayana"), "tropical")
        self.assertEqual(parse_coordinate_selection("kp"), "krishnamurti")
        self.assertEqual(parse_coordinate_selection(None), "citra")
        self.assertEqual(ayanamsa_label("citra"), "Chitra-paksha")
        self.assertEqual(ayanamsa_label("revati"), "Revati-paksha")
        self.assertEqual(ayanamsa_label("rohini"), "Rohini-paksha")
        self.assertEqual(ayanamsa_label("pushya"), "Pushya-paksha")
        self.assertEqual(ayanamsa_label("mula"), "Mula-paksha")
        self.assertEqual(
            coordinate_selection_label("tropical"), "Tropical (Sāyana)")
        with self.assertRaisesRegex(ValueError, "Coordinate selection must be one of"):
            parse_coordinate_selection("lahiri")

    def test_purnimanta_header_uses_single_daily_records_pass(self):
        import generate_panchanga_calendar as calendar_module

        with TemporaryDirectory() as directory:
            output = Path(directory) / "calendar.pdf"
            with mock.patch("generate_panchanga_calendar.find_local_eclipses", return_value=[]), \
                    mock.patch(
                        "generate_panchanga_calendar.daily_records",
                        wraps=calendar_module.daily_records) as records_mock:
                build_pdf(
                    load_location("Bengaluru"), 2023, 3, output, month_system="purnimanta")
            document = output.read_bytes()
        self.assertEqual(records_mock.call_count, 1)
        # Subject is uncompressed in the Info dict; page content streams are flate-encoded.
        self.assertIn(b"purnimanta masa", document)
        self.assertNotIn(b"and amanta masa", document)

    def test_calendar_year_label_uses_both_samvatsara_conventions(self):
        records = [
            DayRecord(date(2026, 8, 15), "S1", 1, 1, "A4", True, 0.0),
        ]
        self.assertEqual(
            calendar_year_label(records),
            "1948 Parābhava | 2083 Siddhārthī | 5127 Kali (elapsed)")

    def test_pdf_subtitle_has_kali_ahargana_range(self):
        months = list(month_range(2026, 6))
        self.assertEqual(kali_ahargana_range(months), (1872727, 1873152))

        pdf = mock.Mock()
        with mock.patch("generate_panchanga_calendar.fitted_font_size", return_value=7.5):
            draw_page_header(
                pdf, load_location("Helsinki"), months, RULESET_VERSION,
                kali_ahargana=kali_ahargana_range(months))

        subtitle = pdf.drawString.call_args_list[1].args[2]
        self.assertNotIn("Equal nakshatras", subtitle)
        self.assertTrue(subtitle.endswith("Kali Ahargana: 1872727 - 1873152"))

    def test_long_labels_are_fitted_without_overflow(self):
        ensure_pdf_fonts()
        pdf = Canvas(BytesIO())
        text = ("A Particularly Long Location Name Panchanga: "
                "September 2026 - September 2027")
        available_width = 300
        size = fitted_font_size(pdf, text, PDF_FONT_BOLD, 11, 5, available_width, "test title")
        self.assertLessEqual(pdf.stringWidth(text, PDF_FONT_BOLD, size), available_width + 0.01)

    def test_footer_rejects_more_entries_than_slots(self):
        pdf = Canvas(BytesIO())
        entries = [(index, "Jan 01", f"Festival {index}")
                   for index in range(1, FOOTER_FESTIVAL_SLOTS + 2)]
        with self.assertRaisesRegex(ValueError, str(FOOTER_FESTIVAL_SLOTS)):
            draw_page_footer(pdf, entries)

    def test_footer_accepts_full_slot_count(self):
        ensure_pdf_fonts()
        pdf = Canvas(BytesIO())
        entries = [(index, "Jan 01", f"Festival {index}")
                   for index in range(1, FOOTER_FESTIVAL_SLOTS + 1)]
        draw_page_footer(pdf, entries)

    def test_footer_key_lines_use_iast_names(self):
        from generate_panchanga_calendar import (
            masa_key_line, nakshatra_key_line, sankranti_key_line, tithi_key_line,
            yoga_key_line,
        )
        self.assertTrue(tithi_key_line().startswith("T:"))
        self.assertTrue(nakshatra_key_line().startswith("N:"))
        self.assertTrue(yoga_key_line().startswith("Y:"))
        self.assertIn("Vaiśākha", masa_key_line())
        self.assertIn("amānta or pūrṇimānta", masa_key_line())
        self.assertIn("Meṣa", sankranti_key_line())
        self.assertIn("1 Meṣa", sankranti_key_line())
        self.assertIn("10 Makara", sankranti_key_line())
        self.assertIn("rolling solar-day count resets", sankranti_key_line())
        self.assertIn("7, 14, 21, and 28", sankranti_key_line())
        self.assertIn("Aśvinī", nakshatra_key_line())
        self.assertIn("Viṣkumbha", yoga_key_line())
        self.assertEqual(PDF_FONT_TTC.name, "IndUni-H.ttc")
        self.assertTrue(PDF_FONT_TTC.is_file())
        ensure_pdf_fonts()
        self.assertEqual(tithi_font(True), PDF_FONT_BOLD)


class TithiDisplayTests(unittest.TestCase):

    def test_sukla_and_krsna_drop_letters(self):
        self.assertEqual(tithi_display_parts("S1"), ("01", True))
        self.assertEqual(tithi_display_parts("S15"), ("15", True))
        self.assertEqual(tithi_display_parts("K1"), ("01", False))
        self.assertEqual(tithi_display_parts("K11"), ("11", False))

    def test_ink_uses_paksha_unless_masa_start(self):
        self.assertEqual(tithi_ink(True), ACCENT)
        self.assertEqual(tithi_ink(False), KRSNA_INK)
        self.assertEqual(tithi_ink(False, is_masa_start=True), MASA_START_INK)
        self.assertEqual(tithi_ink(True, is_masa_start=True, is_adhika=True), ADHIKA_INK)

    def test_font_uses_italic_for_krishna(self):
        ensure_pdf_fonts()
        self.assertEqual(tithi_font(True), PDF_FONT_BOLD)
        self.assertEqual(tithi_font(False), PDF_FONT_BOLD_ITALIC)


class DisplayMasaTests(unittest.TestCase):

    def test_amanta_is_unchanged(self):
        record = DayRecord(date(2030, 1, 1), "K1", 1, 1, "5", False, 0.0)
        self.assertEqual(display_masa(record, amanta=True), "5")

    def test_purnimanta_advances_ordinary_krishna(self):
        record = DayRecord(date(2030, 1, 1), "K1", 1, 1, "5", False, 0.0)
        self.assertEqual(display_masa(record, amanta=False), "6")

    def test_purnimanta_leaves_sukla_unchanged(self):
        record = DayRecord(date(2030, 1, 1), "S1", 1, 1, "5", False, 0.0)
        self.assertEqual(display_masa(record, amanta=False), "5")

    def test_purnimanta_leaves_adhika_krishna_unchanged(self):
        record = DayRecord(date(2030, 1, 1), "K1", 1, 1, "A5", True, 0.0)
        self.assertEqual(display_masa(record, amanta=False), "A5")

    def test_purnimanta_wraps_phalguna_krishna_to_chaitra(self):
        record = DayRecord(date(2030, 1, 1), "K1", 1, 1, "12", False, 0.0)
        self.assertEqual(display_masa(record, amanta=False), "1")


class SolarDateTests(unittest.TestCase):

    def test_solar_day_resets_at_sankranti(self):
        records = [
            DayRecord(date(2026, 1, 13), "S1", 1, 1, "10", False, 1.0),
            DayRecord(date(2026, 1, 14), "S2", 1, 1, "10", False, 2.0),
            DayRecord(date(2026, 1, 15), "S3", 1, 1, "10", False, 3.0),
        ]
        with mock.patch(
            "generate_panchanga_calendar.panchanga.raasi",
            side_effect=[10, 10, 11],
        ):
            self.assertEqual(
                solar_dates_by_date(records),
                {
                    date(2026, 1, 13): (10, 1, False),
                    date(2026, 1, 14): (10, 2, False),
                    date(2026, 1, 15): (11, 1, True),
                },
            )


class SolarMarkerTests(unittest.TestCase):

    def test_solar_markers_are_right_aligned(self):
        pdf = mock.Mock()
        draw_sankranti_mark(pdf, 20.0, 100.0, 10, 30.0)
        draw_solar_day_mark(pdf, 20.0, 100.0, 14, 30.0)
        self.assertEqual(
            pdf.drawRightString.call_args_list,
            [
                mock.call(49.0, 108.2, "10"),
                mock.call(49.0, 108.2, "14"),
            ],
        )
        self.assertEqual(
            pdf.setFont.call_args_list,
            [
                mock.call(PDF_FONT_BOLD, 5.0),
                mock.call(PDF_FONT_BOLD, 5.0),
            ],
        )
        self.assertEqual(
            pdf.setFillColor.call_args_list,
            [
                mock.call(SANKRANTI_INK),
                mock.call(ACCENT),
            ],
        )

    def test_eclipse_marker_is_half_width_wave(self):
        pdf = mock.Mock()
        draw_eclipse_mark(pdf, 20.0, 100.0, 30.0)
        self.assertEqual(pdf.beginPath.call_count, 1)
        pdf.beginPath.return_value.moveTo.assert_called_once_with(23.0, 101.7)
        self.assertEqual(pdf.beginPath.return_value.curveTo.call_count, 6)
        self.assertAlmostEqual(
            pdf.beginPath.return_value.curveTo.call_args.args[4], 38.0)
        pdf.drawPath.assert_called_once_with(
            pdf.beginPath.return_value, stroke=1, fill=0)
        pdf.line.assert_not_called()

    def test_ekadashi_and_eclipse_underlines_share_geometry(self):
        pdf = mock.Mock()
        draw_tithi_underline(pdf, 20.0, 100.0, 30.0, EKADASHI_MARK)
        pdf.rect.assert_called_once_with(
            23.0, 100.6, 15.0, 1.2, stroke=0, fill=1)

        pdf.reset_mock()
        draw_eclipse_mark(pdf, 20.0, 100.0, 30.0)
        pdf.beginPath.return_value.moveTo.assert_called_once_with(23.0, 101.7)
        self.assertAlmostEqual(
            pdf.beginPath.return_value.curveTo.call_args.args[4], 38.0)


class DailyRecordsCacheHookTests(unittest.TestCase):
    """``daily_records`` must forward sunrise tithi into ``masa``."""

    def test_passes_tithi_number_to_masa(self):
        import generate_panchanga_calendar as calendar_module
        import panchanga

        location = load_location("Bengaluru")
        panchanga.set_chosen_ayanamsa("citra")
        with mock.patch.object(
                calendar_module.panchanga, "masa", return_value=[1, False]) as masa_mock:
            daily_records([(2026, 1)], location)
        self.assertTrue(masa_mock.called)
        for _args, kwargs in masa_mock.call_args_list:
            self.assertIn("tithi_number", kwargs)
            self.assertIsInstance(kwargs["tithi_number"], int)
            self.assertGreaterEqual(kwargs["tithi_number"], 1)
            self.assertLessEqual(kwargs["tithi_number"], 30)


if __name__ == "__main__":
    unittest.main()
