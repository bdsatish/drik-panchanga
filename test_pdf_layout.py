"""Regression tests for the generated one-page calendar layout."""

from io import BytesIO
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

from reportlab.pdfgen.canvas import Canvas

from generate_panchanga_calendar import (
    DEFAULT_FESTIVALS_PATH,
    LAYOUT_VERSION,
    RULESET_VERSION,
    argument_parser,
    build_pdf,
    default_output_path,
    ensure_text_fits,
    fitted_font_size,
    load_location,
)


class PdfLayoutTests(unittest.TestCase):

    def test_generated_calendar_has_exactly_one_page(self):
        import generate_panchanga_calendar as calendar_module

        with TemporaryDirectory() as directory:
            output = Path(directory) / "calendar.pdf"
            with mock.patch(
                    "generate_panchanga_calendar.find_local_eclipses",
                    return_value=[
                        ("Lunar", "Partial", 2461103.0419131187, 2461103.0, 2461103.1),
                    ],
            ), mock.patch(
                    "generate_panchanga_calendar.draw_page_footer",
                    wraps=calendar_module.draw_page_footer,
            ) as footer:
                build_pdf(load_location("Helsinki"), 2026, 6, output)
            document = output.read_bytes()

        page_objects = re.findall(rb"/Type\s*/Page\b", document)
        self.assertEqual(len(page_objects), 1)
        self.assertIn(RULESET_VERSION.encode("ascii"), document)
        self.assertIn(LAYOUT_VERSION.encode("ascii"), document)
        self.assertEqual(footer.call_count, 1)
        self.assertIn("Eclipses:", footer.call_args.kwargs["eclipse_line"])

    def test_cli_defaults_festivals_path(self):
        parser = argument_parser()
        arguments = parser.parse_args(["--city", "Helsinki", "--start", "2026-03"])
        self.assertFalse(hasattr(arguments, "festival_policy"))
        self.assertEqual(arguments.festivals, DEFAULT_FESTIVALS_PATH)

    def test_default_filename_has_no_policy_suffix(self):
        path = default_output_path(load_location("Helsinki"), 2026, 3)
        self.assertEqual(
            path.name,
            "helsinki_panchanga_2026-03_to_2027-03.pdf",
        )

    def test_long_labels_are_fitted_without_overflow(self):
        pdf = Canvas(BytesIO())
        text = ("A Particularly Long Location Name Panchanga: "
                "September 2026 - September 2027")
        available_width = 300
        size = fitted_font_size(
            pdf,
            text,
            "Helvetica-Bold",
            11,
            5,
            available_width,
        )

        ensure_text_fits(
            pdf,
            text,
            "Helvetica-Bold",
            size,
            available_width,
            "test title",
        )
        self.assertLessEqual(
            pdf.stringWidth(text, "Helvetica-Bold", size),
            available_width + 0.01,
        )


if __name__ == "__main__":
    unittest.main()
