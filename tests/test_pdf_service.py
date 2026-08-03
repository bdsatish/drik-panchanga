"""Shared Flask/CGI PDF generation tests."""

import io
import os
from pathlib import Path
import sys
import unittest
from unittest import mock

from webapp import cgi_handlers
from webapp.app import app
from webapp.pdf_service import generate_pdf


class PdfServiceTests(unittest.TestCase):

    def test_validates_required_fields(self):
        with self.assertRaisesRegex(ValueError, "City is required"):
            generate_pdf({})
        with self.assertRaisesRegex(ValueError, "Start month is required"):
            generate_pdf({"city": "Helsinki"})

    def test_generates_bytes_with_shared_defaults(self):
        def fake_build(_location, _year, _month, output_path, **_kwargs):
            Path(output_path).write_bytes(b"%PDF-shared")
            return Path(output_path)

        with mock.patch("webapp.pdf_service.build_pdf", side_effect=fake_build) as build:
            content, filename = generate_pdf({
                "city": "Helsinki",
                "start": "2026-03",
            })

        self.assertEqual(content, b"%PDF-shared")
        self.assertEqual(
            filename, "helsinki-fi_panchanga_2026-03_to_2027-04.pdf")
        self.assertEqual(build.call_args.kwargs["month_system"], "amanta")
        self.assertEqual(build.call_args.kwargs["ayanamsa"], "citra")


class FlaskGenerationTests(unittest.TestCase):

    def test_adapter_returns_shared_pdf(self):
        with mock.patch(
                "webapp.app.generate_pdf",
                return_value=(b"%PDF-flask", "calendar.pdf")) as generate:
            response = app.test_client().post("/generate", data={
                "city": "Helsinki",
                "start": "2026-03",
            })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"%PDF-flask")
        self.assertIn("calendar.pdf", response.headers["Content-Disposition"])
        self.assertEqual(generate.call_args.args[0]["city"], "Helsinki")

    def test_adapter_keeps_validation_errors_as_bad_requests(self):
        with mock.patch(
                "webapp.app.generate_pdf",
                side_effect=ValueError("Invalid request")):
            response = app.test_client().post("/generate")
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Invalid request", response.data)


class CgiGenerationTests(unittest.TestCase):

    def test_adapter_returns_shared_pdf(self):
        stdout = mock.Mock(buffer=io.BytesIO())
        with mock.patch.dict(os.environ, {"REQUEST_METHOD": "POST"}, clear=True), \
                mock.patch.object(
                    cgi_handlers, "_parse_urlencoded_post",
                    return_value={"city": "Helsinki", "start": "2026-03"}), \
                mock.patch.object(
                    cgi_handlers, "generate_pdf",
                    return_value=(b"%PDF-cgi", "calendar.pdf")) as generate, \
                mock.patch.object(sys, "stdout", stdout):
            cgi_handlers.handle_generate()

        output = stdout.buffer.getvalue()
        self.assertIn(b'filename="calendar.pdf"', output)
        self.assertTrue(output.endswith(b"%PDF-cgi"))
        self.assertEqual(generate.call_args.args[0]["city"], "Helsinki")


if __name__ == "__main__":
    unittest.main()
