"""Shared Flask/CGI PDF generation tests."""

import io
import os
from pathlib import Path
import sys
import unittest
from unittest import mock

from webapp import cgi_handlers
from webapp.app import app
from webapp.ics_service import generate_ics
from webapp.pdf_service import generate_pdf
from generate_panchanga_calendar import load_location


class PdfServiceTests(unittest.TestCase):

  def test_validates_required_fields(self):
    with self.assertRaisesRegex(ValueError, "City is required"):
      generate_pdf({})
    with self.assertRaisesRegex(ValueError, "start month must use YYYY-MM"):
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
    self.assertEqual(filename, "helsinki-fi_panchanga_2026-03_to_2027-04.pdf")
    self.assertEqual(build.call_args.kwargs["month_system"], "amanta")
    self.assertEqual(build.call_args.kwargs["coordinate_selection"], "citra")


class FlaskGenerationTests(unittest.TestCase):

  def test_adapter_returns_shared_pdf(self):
    with mock.patch("webapp.app.generate_pdf", return_value=(b"%PDF-flask", "calendar.pdf")) as generate:
      response = app.test_client().post("/generate", data={
        "city": "Helsinki",
        "start": "2026-03",
      })

    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.data, b"%PDF-flask")
    self.assertIn("calendar.pdf", response.headers["Content-Disposition"])
    self.assertEqual(generate.call_args.args[0]["city"], "Helsinki")

  def test_adapter_keeps_validation_errors_as_bad_requests(self):
    with mock.patch("webapp.app.generate_pdf", side_effect=ValueError("Invalid request")):
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


class IcsServiceTests(unittest.TestCase):

  def test_generates_valid_ics_structure(self):
    ics = generate_ics(load_location("Helsinki"), 2026, 1)
    self.assertTrue(ics.startswith("BEGIN:VCALENDAR\r\n"))
    self.assertIn("VERSION:2.0", ics)
    self.assertIn("CALSCALE:GREGORIAN", ics)
    self.assertIn("METHOD:PUBLISH", ics)
    self.assertIn("PRODID:-//Drik Panchanga//EN", ics)
    self.assertIn("X-WR-CALNAME:Panchanga", ics)
    self.assertIn("BEGIN:VEVENT", ics)
    self.assertIn("DTSTART;VALUE=DATE:", ics)
    self.assertIn("DTEND;VALUE=DATE:", ics)
    self.assertIn("SUMMARY:", ics)
    self.assertIn("DESCRIPTION:", ics)
    self.assertIn("UID:panchanga-", ics)
    self.assertIn("DTSTAMP:", ics)
    self.assertTrue(ics.endswith("END:VCALENDAR\r\n"))

    physical_lines = [line for line in ics.split("\r\n") if line]
    self.assertTrue(all(len(line.encode("utf-8")) <= 75 for line in physical_lines))

  def test_ics_respects_tropical_mode(self):
    loc = load_location("Tirupati")
    sid = generate_ics(loc, 2026, 1, coordinate_selection="citra")
    trop = generate_ics(loc, 2026, 1, coordinate_selection="tropical")
    self.assertEqual(sid.count("BEGIN:VEVENT"), trop.count("BEGIN:VEVENT"))
    self.assertEqual(sid.count("BEGIN:VEVENT"), 424)

    def first_description(text):
      lines = text.split("\r\n")
      chunks = []
      in_description = False
      for line in lines:
        if line.startswith("DESCRIPTION:"):
          in_description = True
          chunks.append(line[len("DESCRIPTION:"):])
        elif in_description and line.startswith(" "):
          chunks.append(line[1:])
        elif in_description:
          break
      return "".join(chunks)

    self.assertNotEqual(first_description(sid), first_description(trop))

  def test_ics_event_count_matches_month_span(self):
    ics = generate_ics(load_location("Tirupati"), 2026, 6)
    self.assertGreater(ics.count("BEGIN:VEVENT"), 400)
    self.assertLessEqual(ics.count("BEGIN:VEVENT"), 435)

  def test_ics_metadata_is_selection_aware(self):
    loc = load_location("Tirupati")
    sid = generate_ics(loc, 2026, 1, coordinate_selection="citra")
    trop = generate_ics(loc, 2026, 1, coordinate_selection="tropical")
    self.assertIn("X-WR-CALDESC:Chitra-paksha · Amānta", sid)
    self.assertIn("X-WR-CALDESC:Tropical (Sāyana) · Amānta", trop)

  def test_ics_uid_differs_by_selection_and_month_system(self):
    loc = load_location("Tirupati")
    sid = generate_ics(loc, 2026, 1, coordinate_selection="citra")
    trop = generate_ics(loc, 2026, 1, coordinate_selection="tropical")
    purni = generate_ics(loc, 2026, 1, coordinate_selection="citra", month_system="purnimanta")

    def first_uid(text):
      return next(line for line in text.split("\r\n") if line.startswith("UID:"))

    self.assertNotEqual(first_uid(sid), first_uid(trop))
    self.assertNotEqual(first_uid(sid), first_uid(purni))

  def test_ics_flask_filename_is_selection_aware(self):
    response = app.test_client().get("/api/panchanga.ics?city=Helsinki&start=2026-03&ayanamsa=tropical")
    self.assertEqual(response.status_code, 200)
    disposition = response.headers["Content-Disposition"]
    self.assertIn("tropical", disposition)
    self.assertIn("amanta", disposition)

  def test_ics_flask_endpoint_returns_calendar(self):
    response = app.test_client().get("/api/panchanga.ics?city=Helsinki&start=2026-03")
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.mimetype, "text/calendar")
    self.assertIn(b"BEGIN:VCALENDAR", response.data)
    self.assertIn(b"BEGIN:VEVENT", response.data)

  def test_ics_flask_endpoint_rejects_bad_city(self):
    response = app.test_client().get("/api/panchanga.ics?city=NoSuchPlace&start=2026-03")
    self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
  unittest.main()
