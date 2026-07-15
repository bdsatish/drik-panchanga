"""Regression tests for the generated one-page calendar layout."""

from io import BytesIO
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest

from reportlab.pdfgen.canvas import Canvas

from generate_panchanga_calendar import (
    build_pdf,
    ensure_text_fits,
    fitted_font_size,
    load_location,
)


class PdfLayoutTests(unittest.TestCase):
    def test_generated_calendar_has_exactly_one_page(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "calendar.pdf"
            build_pdf(load_location("Helsinki"), 2026, 6, output)
            document = output.read_bytes()

        page_objects = re.findall(rb"/Type\s*/Page\b", document)
        self.assertEqual(len(page_objects), 1)

    def test_long_labels_are_fitted_without_overflow(self):
        pdf = Canvas(BytesIO())
        text = (
            "A Particularly Long Location Name Panchanga: "
            "September 2026 - September 2027"
        )
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
