"""Regression tests for the generated one-page calendar layout."""

from io import BytesIO
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest

from reportlab.pdfgen.canvas import Canvas

from generate_panchanga_calendar import (
    GENERIC_ANCHOR_RULESET_VERSION,
    GENERIC_KALA_RULESET_VERSION,
    GENERIC_MIDPOINT_RULESET_VERSION,
    GENERIC_UDAYA_RULESET_VERSION,
    LAYOUT_VERSION,
    RULESET_VERSION,
    argument_parser,
    build_pdf,
    default_output_path,
    ensure_text_fits,
    fitted_font_size,
    load_location,
)
from festival_rules import (
    GENERIC_ANCHOR_FESTIVAL_POLICY,
    GENERIC_KALA_FESTIVAL_POLICY,
    GENERIC_MIDPOINT_FESTIVAL_POLICY,
    GENERIC_UDAYA_FESTIVAL_POLICY,
    TRADITIONAL_FESTIVAL_POLICY,
)


class PdfLayoutTests(unittest.TestCase):
    def test_generated_calendar_has_exactly_one_page(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "calendar.pdf"
            build_pdf(load_location("Helsinki"), 2026, 6, output)
            document = output.read_bytes()

        page_objects = re.findall(rb"/Type\s*/Page\b", document)
        self.assertEqual(len(page_objects), 1)
        self.assertIn(RULESET_VERSION.encode("ascii"), document)
        self.assertIn(LAYOUT_VERSION.encode("ascii"), document)

    def test_generic_calendar_labels_experimental_ruleset(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "calendar.pdf"
            build_pdf(
                load_location("Helsinki"),
                2026,
                6,
                output,
                GENERIC_UDAYA_FESTIVAL_POLICY,
            )
            document = output.read_bytes()

        self.assertIn(
            GENERIC_UDAYA_RULESET_VERSION.encode("ascii"),
            document,
        )
        self.assertNotIn(RULESET_VERSION.encode("ascii"), document)

    def test_generic_kala_calendar_labels_experimental_ruleset(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "calendar.pdf"
            build_pdf(
                load_location("Helsinki"),
                2026,
                6,
                output,
                GENERIC_KALA_FESTIVAL_POLICY,
            )
            document = output.read_bytes()

        self.assertIn(
            GENERIC_KALA_RULESET_VERSION.encode("ascii"),
            document,
        )
        self.assertNotIn(RULESET_VERSION.encode("ascii"), document)

    def test_generic_anchor_calendar_labels_experimental_ruleset(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "calendar.pdf"
            build_pdf(
                load_location("Helsinki"),
                2026,
                6,
                output,
                GENERIC_ANCHOR_FESTIVAL_POLICY,
            )
            document = output.read_bytes()

        self.assertIn(
            GENERIC_ANCHOR_RULESET_VERSION.encode("ascii"),
            document,
        )
        self.assertNotIn(RULESET_VERSION.encode("ascii"), document)

    def test_generic_midpoint_calendar_labels_experimental_ruleset(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "calendar.pdf"
            build_pdf(
                load_location("Helsinki"),
                2026,
                6,
                output,
                GENERIC_MIDPOINT_FESTIVAL_POLICY,
            )
            document = output.read_bytes()

        self.assertIn(
            GENERIC_MIDPOINT_RULESET_VERSION.encode("ascii"),
            document,
        )
        self.assertNotIn(RULESET_VERSION.encode("ascii"), document)

    def test_cli_defaults_to_traditional_policy(self):
        arguments = argument_parser().parse_args(
            ["--city", "Helsinki", "--start", "2026-03"]
        )
        self.assertEqual(
            arguments.festival_policy,
            TRADITIONAL_FESTIVAL_POLICY,
        )

    def test_cli_accepts_generic_udaya_policy(self):
        arguments = argument_parser().parse_args(
            [
                "--city",
                "Helsinki",
                "--start",
                "2026-03",
                "--festival-policy",
                GENERIC_UDAYA_FESTIVAL_POLICY,
            ]
        )
        self.assertEqual(
            arguments.festival_policy,
            GENERIC_UDAYA_FESTIVAL_POLICY,
        )

    def test_cli_accepts_generic_kala_policy(self):
        arguments = argument_parser().parse_args(
            [
                "--city",
                "Helsinki",
                "--start",
                "2026-03",
                "--festival-policy",
                GENERIC_KALA_FESTIVAL_POLICY,
            ]
        )
        self.assertEqual(
            arguments.festival_policy,
            GENERIC_KALA_FESTIVAL_POLICY,
        )

    def test_cli_accepts_generic_anchor_policy(self):
        arguments = argument_parser().parse_args(
            [
                "--city",
                "Helsinki",
                "--start",
                "2026-03",
                "--festival-policy",
                GENERIC_ANCHOR_FESTIVAL_POLICY,
            ]
        )
        self.assertEqual(
            arguments.festival_policy,
            GENERIC_ANCHOR_FESTIVAL_POLICY,
        )

    def test_cli_accepts_generic_midpoint_policy(self):
        arguments = argument_parser().parse_args(
            [
                "--city",
                "Helsinki",
                "--start",
                "2026-03",
                "--festival-policy",
                GENERIC_MIDPOINT_FESTIVAL_POLICY,
            ]
        )
        self.assertEqual(
            arguments.festival_policy,
            GENERIC_MIDPOINT_FESTIVAL_POLICY,
        )

    def test_generic_default_filename_has_policy_suffix(self):
        path = default_output_path(
            load_location("Helsinki"),
            2026,
            3,
            GENERIC_UDAYA_FESTIVAL_POLICY,
        )
        self.assertEqual(
            path.name,
            (
                "helsinki_panchanga_generic-udaya_"
                "2026-03_to_2027-03.pdf"
            ),
        )

    def test_generic_kala_default_filename_has_policy_suffix(self):
        path = default_output_path(
            load_location("Helsinki"),
            2026,
            3,
            GENERIC_KALA_FESTIVAL_POLICY,
        )
        self.assertEqual(
            path.name,
            (
                "helsinki_panchanga_generic-kala_"
                "2026-03_to_2027-03.pdf"
            ),
        )

    def test_generic_anchor_default_filename_has_policy_suffix(self):
        path = default_output_path(
            load_location("Helsinki"),
            2026,
            3,
            GENERIC_ANCHOR_FESTIVAL_POLICY,
        )
        self.assertEqual(
            path.name,
            (
                "helsinki_panchanga_generic-anchor_"
                "2026-03_to_2027-03.pdf"
            ),
        )

    def test_generic_midpoint_default_filename_has_policy_suffix(self):
        path = default_output_path(
            load_location("Helsinki"),
            2026,
            3,
            GENERIC_MIDPOINT_FESTIVAL_POLICY,
        )
        self.assertEqual(
            path.name,
            (
                "helsinki_panchanga_generic-midpoint_"
                "2026-03_to_2027-03.pdf"
            ),
        )

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
