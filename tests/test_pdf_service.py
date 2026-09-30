"""Shared Flask/CGI PDF generation tests."""

import io
import os
from pathlib import Path
import sys
import unittest
from unittest import mock

from datetime_helper import Date, format_hms, gregorian_to_jd
from webapp import cgi_handlers
from webapp.app import app, client_ip
from webapp.day_panchanga import _interval, compute_day_panchanga
from webapp.ics_service import generate_ics
from webapp.day_panchanga import _interval_str as _fmt_interval
from webapp.pdf_service import generate_pdf
from generate_panchanga_calendar import load_location
import panchanga


class PdfServiceTests(unittest.TestCase):

  def test_validates_required_fields(self):
    with self.assertRaisesRegex(ValueError, "City is required"):
      generate_pdf({})
    with self.assertRaisesRegex(ValueError, "start year must be YYYY"):
      generate_pdf({"city": "Helsinki"})

  def test_generates_bytes_with_shared_defaults(self):

    def fake_build(_location, _months, output_path, **_kwargs):
      Path(output_path).write_bytes(b"%PDF-shared")
      return Path(output_path)

    with mock.patch("webapp.pdf_service.build_pdf", side_effect=fake_build) as build:
      content, filename = generate_pdf({
        "city": "Helsinki",
        "start": "2026",
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
        "start": "2026",
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

  def test_form_error_answers_html_to_a_browser(self):
    # A browser's ``*/*;q=0.8`` also matches JSON; the failed form must still
    # render the page with its error, and only a JSON-preferring client or an
    # /api/ path gets JSON.
    browser = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    cases = {
      browser: "text/html",
      "*/*": "text/html",
      "application/json": "application/json",
      "application/json;q=0": "text/html"
    }
    for accept, mimetype in cases.items():
      with self.subTest(accept=accept):
        with mock.patch("webapp.app.generate_pdf", side_effect=ValueError("Invalid request")):
          response = app.test_client().post("/generate", headers={"Accept": accept})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.mimetype, mimetype)
        self.assertIn(b"Invalid request", response.data)


class CgiGenerationTests(unittest.TestCase):

  def test_adapter_returns_shared_pdf(self):
    stdout = mock.Mock(buffer=io.BytesIO())
    with mock.patch.dict(os.environ, {"REQUEST_METHOD": "POST"}, clear=True), \
            mock.patch.object(
                cgi_handlers, "_parse_urlencoded_post",
                return_value={"city": "Helsinki", "start": "2026"}), \
            mock.patch.object(
                cgi_handlers, "generate_pdf",
                return_value=(b"%PDF-cgi", "calendar.pdf")) as generate, \
            mock.patch.object(sys, "stdout", stdout):
      cgi_handlers.handle_generate()

    output = stdout.buffer.getvalue()
    self.assertIn(b'filename="calendar.pdf"', output)
    self.assertTrue(output.endswith(b"%PDF-cgi"))
    self.assertEqual(generate.call_args.args[0]["city"], "Helsinki")
    self.assertEqual(output.count(b"Content-Type:"), 1)

  def test_emits_no_partial_header_block_when_a_write_fails(self):
    # Regression: the body write happened inside the same try as the headers,
    # so a failed write re-entered the error path and emitted a second header
    # block after the first. The whole response is now built and written in
    # one call, so a failed write emits nothing rather than a duplicate.
    class FailingBody(io.BytesIO):

      def write(self, data):
        if b"%PDF" in data:
          raise OSError("client disconnected")
        return super().write(data)

    stdout = mock.Mock(buffer=FailingBody())
    with mock.patch.dict(os.environ, {"REQUEST_METHOD": "POST"}, clear=True), \
            mock.patch.object(
                cgi_handlers, "_parse_urlencoded_post",
                return_value={"city": "Helsinki", "start": "2026"}), \
            mock.patch.object(
                cgi_handlers, "generate_pdf",
                return_value=(b"%PDF-cgi", "calendar.pdf")), \
            mock.patch.object(sys, "stdout", stdout):
      with self.assertRaises(OSError):
        cgi_handlers.handle_generate()

    output = stdout.buffer.getvalue()
    self.assertEqual(output.count(b"Content-Type:"), 0)
    self.assertNotIn(b"Status:", output)

  def test_error_response_carries_a_single_header_block(self):
    stdout = mock.Mock(buffer=io.BytesIO())
    with mock.patch.dict(os.environ, {"REQUEST_METHOD": "POST"}, clear=True), \
            mock.patch.object(cgi_handlers, "_parse_urlencoded_post", return_value={}), \
            mock.patch.object(
                cgi_handlers, "generate_pdf",
                side_effect=ValueError("City is required.")), \
            mock.patch.object(sys, "stdout", stdout):
      cgi_handlers.handle_generate()

    output = stdout.buffer.getvalue()
    self.assertEqual(output.count(b"Content-Type:"), 1)
    self.assertEqual(output.count(b"Status:"), 1)
    self.assertIn(b"City is required.", output)


class DurmuhurtaRenderingTests(unittest.TestCase):

  def test_json_and_ics_share_one_clock(self):
    clock = lambda jd_ut, show_seconds: format_hms(jd_ut * 24, show_seconds=show_seconds)
    self.assertEqual(_interval(10.5 / 24, 11.25 / 24, clock), {"start": "10:30:00", "end": "11:15:00"})
    self.assertEqual(_fmt_interval(10.5 / 24, 11.25 / 24, clock), "10:30:00–11:15:00")

  def test_one_interval_on_sunday_two_on_friday(self):
    self.assertEqual(len(compute_day_panchanga("Bengaluru", "18/01/2026")["durmuhurta"]), 1)
    self.assertEqual(len(compute_day_panchanga("Bengaluru", "16/01/2026")["durmuhurta"]), 2)


def unfold_ics(text):
  """Undo RFC 5545 line folding so description content can be matched whole."""
  return text.replace("\r\n ", "")


class IcsServiceTests(unittest.TestCase):

  def test_describes_varjyam_for_every_day(self):
    ics = unfold_ics(generate_ics(load_location("Tirupati"), 2026))
    self.assertEqual(ics.count("Varjyam:"), ics.count("BEGIN:VEVENT"))
    # 01:02:03 and 04:05:06 IST on 1 March 2026, the first printed row
    # (the lunar year starts in Ugadi's month).
    anchor = gregorian_to_jd(Date(2026, 3, 1))
    stub = [(anchor + (1 + 2 / 60 + 3 / 3600 - 5.5) / 24, anchor + (4 + 5 / 60 + 6 / 3600 - 5.5) / 24)]
    with mock.patch.object(panchanga, "varjyam", return_value=stub):
      stubbed = unfold_ics(generate_ics(load_location("Tirupati"), 2026))
    self.assertIn("Varjyam: 01:02:03–04:05:06", stubbed)
    with mock.patch.object(panchanga, "varjyam", return_value=[]):
      empty = unfold_ics(generate_ics(load_location("Tirupati"), 2026))
    self.assertIn("Varjyam: —", empty)

  def test_generates_valid_ics_structure(self):
    ics = generate_ics(load_location("Helsinki"), 2026)
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
    sid = generate_ics(loc, 2026, coordinate_selection="citra")
    trop = generate_ics(loc, 2026, coordinate_selection="tropical")
    # Sidereal Ugadi 2026 sits in March and the next one in April: 14 months,
    # 426 days. Tropical Ugadi stays in March and the next falls in March
    # too: 13 months, 396 days.
    self.assertEqual(sid.count("BEGIN:VEVENT"), 426)
    self.assertEqual(trop.count("BEGIN:VEVENT"), 396)

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
    ics = generate_ics(load_location("Tirupati"), 2026)
    self.assertGreater(ics.count("BEGIN:VEVENT"), 400)
    self.assertLessEqual(ics.count("BEGIN:VEVENT"), 426)

  def test_ics_metadata_is_selection_aware(self):
    loc = load_location("Tirupati")
    sid = generate_ics(loc, 2026, coordinate_selection="citra")
    trop = generate_ics(loc, 2026, coordinate_selection="tropical")
    self.assertIn("X-WR-CALDESC:Chitra-paksha · Amānta", sid)
    self.assertIn("X-WR-CALDESC:Tropical (Sāyana) · Amānta", trop)

  def test_ics_uid_differs_by_selection_and_month_system(self):
    loc = load_location("Tirupati")
    sid = generate_ics(loc, 2026, coordinate_selection="citra")
    trop = generate_ics(loc, 2026, coordinate_selection="tropical")
    purni = generate_ics(loc, 2026, coordinate_selection="citra", month_system="purnimanta")

    def first_uid(text):
      return next(line for line in text.split("\r\n") if line.startswith("UID:"))

    self.assertNotEqual(first_uid(sid), first_uid(trop))
    self.assertNotEqual(first_uid(sid), first_uid(purni))

  def test_ics_flask_filename_is_selection_aware(self):
    response = app.test_client().get("/api/panchanga.ics?city=Helsinki&start=2026&ayanamsa=tropical")
    self.assertEqual(response.status_code, 200)
    disposition = response.headers["Content-Disposition"]
    self.assertIn("tropical", disposition)
    self.assertIn("amanta", disposition)

  def test_ics_flask_filename_uses_the_resolved_city(self):
    # Regression: the filename slugged the raw ``city`` argument, so the same
    # calendar downloaded under different names -- and an un-normalised input
    # like "helsinki,fi" kept a literal comma, because location_slug only
    # rewrites the canonical ", " form.
    client = app.test_client()
    spellings = ["Helsinki", "Helsinki, FI", "helsinki,fi", " Helsinki , fi "]
    names = set()
    for spelling in spellings:
      with self.subTest(city=spelling):
        response = client.get(f"/api/panchanga.ics?city={spelling}&start=2026")
        self.assertEqual(response.status_code, 200)
        disposition = response.headers["Content-Disposition"]
        self.assertIn("panchanga-helsinki-fi-citra-amanta-2026.ics", disposition)
        self.assertNotIn(",", disposition.split("filename=")[-1])  # no raw comma
        names.add(disposition)
    self.assertEqual(len(names), 1)

  def test_ics_flask_filename_matches_the_uid_slug(self):
    # The download name and the calendar's own UID must agree.
    import re
    response = app.test_client().get("/api/panchanga.ics?city=helsinki,fi&start=2026")
    disposition = response.headers["Content-Disposition"]
    uid = re.search(r"@([A-Za-z0-9._-]+)", response.data.decode())
    self.assertIn(f"-{uid.group(1)}-", disposition)

  def test_ics_flask_endpoint_returns_calendar(self):
    response = app.test_client().get("/api/panchanga.ics?city=Helsinki&start=2026")
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.mimetype, "text/calendar")
    self.assertIn(b"BEGIN:VCALENDAR", response.data)
    self.assertIn(b"BEGIN:VEVENT", response.data)

  def test_ics_flask_endpoint_rejects_bad_city(self):
    response = app.test_client().get("/api/panchanga.ics?city=NoSuchPlace&start=2026")
    self.assertEqual(response.status_code, 400)


class ClientIpTrustTests(unittest.TestCase):
  """The X-Forwarded-For trust model behind ``PANCHANGA_TRUSTED_PROXY_HOPS``."""

  def test_default_ignores_forwarded_for(self):
    # 0 trusted hops: the header is client-controlled, so only the peer counts.
    self.assertEqual(client_ip("9.9.9.9, 8.8.8.8", "10.0.0.1"), "10.0.0.1")
    self.assertEqual(client_ip("", "10.0.0.1"), "10.0.0.1")

  def test_trusted_hops_count_from_the_right(self):
    self.assertEqual(client_ip("9.9.9.9, 8.8.8.8", "10.0.0.1", trusted_hops=1), "8.8.8.8")
    self.assertEqual(client_ip("9.9.9.9, 8.8.8.8", "10.0.0.1", trusted_hops=2), "9.9.9.9")

  def test_short_header_falls_back_to_peer(self):
    self.assertEqual(client_ip("9.9.9.9", "10.0.0.1", trusted_hops=3), "10.0.0.1")

  def test_env_var_reaches_client_ip(self):
    with mock.patch.dict(os.environ, {"PANCHANGA_TRUSTED_PROXY_HOPS": "1"}):
      self.assertEqual(client_ip("9.9.9.9, 8.8.8.8", "10.0.0.1"), "8.8.8.8")
    with mock.patch.dict(os.environ, {"PANCHANGA_TRUSTED_PROXY_HOPS": "bogus"}):
      self.assertEqual(client_ip("9.9.9.9, 8.8.8.8", "10.0.0.1"), "10.0.0.1")


if __name__ == "__main__":
  unittest.main()
