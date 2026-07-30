"""Regression tests for the generated one-page calendar layout."""

from io import BytesIO
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

from reportlab.pdfgen.canvas import Canvas

from generate_panchanga_calendar import (
    ACCENT,
    ADHIKA_INK,
    DEFAULT_FESTIVALS_PATH,
    FOOTER_FESTIVAL_SLOTS,
    KRSNA_INK,
    LAYOUT_VERSION,
    MASA_START_INK,
    PDF_FONT,
    PDF_FONT_BOLD,
    PDF_FONT_BOLD_ITALIC,
    RULESET_VERSION,
    argument_parser,
    build_pdf,
    default_output_path,
    draw_page_footer,
    ensure_pdf_fonts,
    fitted_font_size,
    load_location,
    pdf_font_ttc,
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

    def test_purnimanta_header_is_embedded(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "calendar.pdf"
            with mock.patch("generate_panchanga_calendar.find_local_eclipses", return_value=[]):
                build_pdf(
                    load_location("Bengaluru"), 2023, 3, output, month_system="purnimanta")
            document = output.read_bytes()
        # Subject is uncompressed in the Info dict; page content streams are flate-encoded.
        self.assertIn(b"purnimanta masa", document)
        self.assertNotIn(b"and amanta masa", document)

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
        pdf = Canvas(BytesIO())
        entries = [(index, "Jan 01", f"Festival {index}")
                   for index in range(1, FOOTER_FESTIVAL_SLOTS + 1)]
        draw_page_footer(pdf, entries)

    def test_footer_key_lines_use_iast_names(self):
        from generate_panchanga_calendar import (
            masa_key_line, nakshatra_key_line, yoga_key_line,
        )
        self.assertIn("Vaiśākha", masa_key_line())
        self.assertIn("Aśvinī", nakshatra_key_line())
        self.assertIn("Viṣkumbha", yoga_key_line())
        self.assertEqual(pdf_font_ttc().name, "IndUni-H.ttc")
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


if __name__ == "__main__":
    unittest.main()
