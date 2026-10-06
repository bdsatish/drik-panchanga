"""Manual ``LAT,LON,TZ`` place across the CLI and web stack."""

import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from datetime_helper import format_utc_offset
from generate_monthly_calendar import argument_parser as monthly_argument_parser
from generate_panchanga_calendar import (Location, argument_parser as annual_argument_parser, attach_option_values,
                                         load_custom_location, load_location, require_start_year, resolve_location)
from webapp.app import app
from webapp.day_panchanga import compute_day_panchanga


class CustomLocationTests(unittest.TestCase):

  def test_place_wins_over_city(self):
    location = resolve_location("Bengaluru, IN", "12.97,77.59,5.5")
    self.assertEqual(location.name, "12.97N, 77.59E (UTC+5:30)")
    self.assertEqual(location.timezone_name, "UTC+5:30")
    self.assertEqual(format_utc_offset("UTC+5:30", 2026, 3), "UTC+5:30 (UTC+05:30)")
    self.assertEqual(resolve_location("Bengaluru, IN", " ").name, "Bengaluru, IN")
    self.assertEqual(resolve_location("Bengaluru, IN", None).name, "Bengaluru, IN")

  def test_southern_western_place(self):
    location = resolve_location(place=" -33.87 , -70.5 , -3.5 ")
    self.assertEqual(location.name, "33.87S, 70.50W (UTC-3:30)")

  def test_custom_day_matches_equivalent_city(self):
    city = compute_day_panchanga("Bengaluru", "21/04/2023")
    custom = compute_day_panchanga("", "21/04/2023", place="12.97194,77.59369,5.5")
    self.assertEqual(custom["timezone"], "UTC+5:30")
    self.assertEqual(custom["sunrise"], city["sunrise"])
    self.assertEqual([seg["name"] for seg in custom["tithi"]], [seg["name"] for seg in city["tithi"]])

  def test_rejects_bad_floats(self):
    for fields in ({
        "latitude": "abc"
    }, {
        "longitude": "200"
    }, {
        "timezone": "15"
    }, {
        "latitude": "12.97",
        "longitude": "77.59",
        "start": "2026-03"
    }):
      with self.subTest(fields=fields), self.assertRaises(ValueError):
        load_custom_location(fields.get("latitude"), fields.get("longitude"), fields.get("timezone"))
    with self.assertRaisesRegex(ValueError, "City is required"):
      compute_day_panchanga("", "21/04/2023")

  def test_rejects_bad_place(self):
    for place in ("12.97", "12.97,77.59", "1,2,3,4"):
      with self.subTest(place=place), self.assertRaisesRegex(ValueError, "three comma-separated"):
        resolve_location(place=place)
    bad_values = (("a,2,3", "Latitude 'a' must be a number"), ("12.97,,5.5", "Longitude '' must be a number"),
                  ("95,2,3", "Latitude '95' is out of range"), ("1,200,3", "Longitude '200' is out of range"),
                  ("1,2,15", "Timezone '15' is out of range"))
    for place, message in bad_values:
      with self.subTest(place=place), self.assertRaisesRegex(ValueError, message):
        resolve_location(place=place)

  def test_requires_city_or_place(self):
    with self.assertRaisesRegex(ValueError, "City is required"):
      resolve_location(None)

  def test_cli_accepts_negative_latitude(self):
    argv = attach_option_values(["--city", "-13.4,70,5.5", "--year", "2026"])
    arguments = annual_argument_parser().parse_args(argv)
    self.assertEqual(resolve_location(arguments.city).name, "13.40S, 70.00E (UTC+5:30)")


class CustomLocationWebTests(unittest.TestCase):

  def test_day_api(self):
    response = app.test_client().get("/api/panchanga?place=12.97194,77.59369,5.5&date=21/04/2023")
    self.assertEqual(response.status_code, 200)
    data = response.get_json()
    self.assertEqual(data["timezone"], "UTC+5:30")
    self.assertEqual(data["sunrise"], compute_day_panchanga("Bengaluru", "21/04/2023")["sunrise"])

  def test_day_api_rejects_partial_input(self):
    response = app.test_client().get("/api/panchanga?place=12.97&date=21/04/2023")
    self.assertEqual(response.status_code, 400)

  def test_ics(self):
    response = app.test_client().get("/api/panchanga.ics?place=12.97,77.59,5.5&start=2026")
    self.assertEqual(response.status_code, 200)
    self.assertIn(b"BEGIN:VCALENDAR", response.data)

  def test_pdf(self):
    response = app.test_client().post("/generate", data={
      "place": "12.97,77.59,5.5",
      "start": "2026",
    })
    self.assertEqual(response.status_code, 200)


class AttachOptionValuesTests(unittest.TestCase):
  """A value that starts with a minus must survive argparse."""

  GLUE_CASES = [
    ("glues a negative city spec", ["--city", "-13.4,70,5.5", "--year", "2026"],
     ["--city=-13.4,70,5.5", "--year", "2026"]),
    ("glues a negative bce start year", ["--city", "Ujjain", "--year", "-500"],
     ["--city", "Ujjain", "--year=-500"]),
  ]

  def test_glues_negative_values_to_flags(self):
    for label, argv, expected in self.GLUE_CASES:
      with self.subTest(label):
        self.assertEqual(attach_option_values(argv), expected)

  def test_leaves_happy_argvs_alone(self):
    # A value that does not start with '-' needs no glue: argparse is happy
    # with a split flag and value, so argv is left byte-identical. --year
    # with no value must stay split too: it should error as a missing value,
    # not as "--year=--city" plus "unrecognized arguments: Ujjain".
    for argv in (["--city", "12.97,77.59,5.5", "--year", "2026"],
                 ["--city", "Helsinki", "--year", "2026"],
                 ["--year", "--city", "Ujjain"]):
      with self.subTest(argv=argv):
        self.assertEqual(attach_option_values(argv), argv)


class BceStartYearTests(unittest.TestCase):
  """``--year`` takes an astronomical lunar year, as the day view and the API already do."""

  def test_parses_ce_bce_year_zero_and_padded_forms(self):
    self.assertEqual(require_start_year("2026"), 2026)
    self.assertEqual(require_start_year("-500"), -500)
    self.assertEqual(require_start_year("-0500"), -500)  # same year, zero-padded
    self.assertEqual(require_start_year("-3300"), -3300)  # oldest supported year
    self.assertEqual(require_start_year("0000"), 0)  # zero still works
    self.assertEqual(require_start_year("3300"), 3300)  # newest supported year

  def test_rejects_malformed_and_out_of_range(self):
    # A negative year may keep 1–4 digits (-3 = 4 BCE); a positive year must
    # carry four digits, so 26 cannot be read as 26 CE or 2026.
    for text in ("2026-3", "abc", "", None, "202603", "26", "500", "0", "+500"):
      with self.subTest(text=text), self.assertRaises(ValueError):
        require_start_year(text)

  def test_rejects_a_start_month_with_a_hint(self):
    # Scripts that still pass 2026-03 must fail loudly, pointing at the year.
    for text in ("2026-03", "-500-03", "0000-01"):
      with self.subTest(text=text), self.assertRaisesRegex(ValueError, "not YYYY-MM"):
        require_start_year(text)

  def test_rejects_years_outside_the_pdf_range(self):
    # The ephemeris and the day view reach further; the PDF/ICS products do not.
    for text in ("3301", "-3301", "-5000", "9999"):
      with self.subTest(text=text), self.assertRaisesRegex(ValueError, "out of range.*-3300 to 3300"):
        require_start_year(text)

  def test_filename_round_trips_through_the_parser(self):
    # The names default_output_path builds carry months in the same grammar;
    # their year part must parse back through require_start_year.
    from generate_panchanga_calendar import _format_month
    for year in (2026, 500, 0, -500, -3300, -1):
      with self.subTest(year=year):
        formatted = _format_month(year, 3)
        self.assertEqual(require_start_year(formatted.rsplit("-", 1)[0]), year)

  def test_both_parsers_accept_a_bce_start(self):
    for parser in (annual_argument_parser(), monthly_argument_parser()):
      arguments = parser.parse_args(attach_option_values(["--city", "Ujjain", "--year", "-500"]))
      self.assertEqual(arguments.year, "-500")
      self.assertEqual(require_start_year(arguments.year), -500)

  def test_cli_builds_a_bce_pdf(self):
    import generate_panchanga_calendar as annual
    with TemporaryDirectory() as directory:
      output = Path(directory) / "bce.pdf"
      # main() builds an ArgumentParser at call time. Since Python 3.14,
      # argparse eagerly probes stdout color support at construction, so a
      # bare stdout Mock trips `os.isatty(file.fileno())`. A StringIO keeps
      # the path capture without stdout's fileno semantics.
      with redirect_stdout(io.StringIO()):
        annual.main(["--city", "Ujjain", "--year=-500", "--output", str(output)])
      self.assertTrue(output.stat().st_size > 0)

  def test_ics_endpoint_rejects_a_bce_start(self):
    # iCalendar DATE values allow only four-digit years, so a BCE span
    # cannot be exported. The endpoint must say so (400), not emit
    # DTSTART;VALUE=DATE:-5000301 that calendar apps reject.
    from webapp.ics_service import generate_ics
    with self.assertRaisesRegex(ValueError, "four-digit years"):
      generate_ics(load_location("Ujjain"), -500)
    response = app.test_client().get("/api/panchanga.ics?city=Ujjain&start=-500")
    self.assertEqual(response.status_code, 400)
    self.assertIn(b"four-digit years", response.data)

  def test_pdf_endpoint_accepts_a_bce_start(self):
    response = app.test_client().post("/generate", data={
      "city": "Ujjain",
      "start": "-500",
    })
    self.assertEqual(response.status_code, 200)


class PlaceSpecFormsTests(unittest.TestCase):
  """LAT,LON,TZ accept every float() spelling: integers, x.0, +sign, zero."""

  SPEC_CASES = [
    ("three floats", "-13.4,70,5.5", (-13.4, 70.0, "UTC+5:30"), "13.40S, 70.00E (UTC+5:30)"),
    ("negative longitude is west", "40.71,-74.0,-5", (40.71, -74.0, "UTC-5"), None),
    ("pure integers", "13,77,5", (13.0, 77.0, "UTC+5"), None),
    ("explicit plus sign", "+13.4,+70,+5.5", (13.4, 70.0, "UTC+5:30"), None),
    ("zeroes", "0,0,0", (0.0, 0.0, "UTC+0"), None),
    ("mixed forms in one spec", "-33.87,+151.2,10", (-33.87, 151.2, "UTC+10"), None),
  ]

  def test_loc_spec_forms(self):
    for label, place, expected, name in self.SPEC_CASES:
      with self.subTest(label):
        location = resolve_location(place=place)
        self.assertEqual((location.latitude, location.longitude, location.timezone_name), expected)
        if name is not None:
          self.assertEqual(location.name, name)

  def test_integer_spec_resolves_like_float_spec(self):
    self.assertEqual(resolve_location(place="13,77,-5"), resolve_location(place="13.0,77.0,-5.0"))

  def test_offset_names_parse_back(self):
    from datetime_helper import fixed_offset_name, tzinfo_for
    self.assertEqual(fixed_offset_name(-5.0), "UTC-5")
    self.assertEqual(fixed_offset_name(10.0), "UTC+10")
    self.assertEqual(fixed_offset_name(0.0), "UTC+0")
    self.assertEqual(fixed_offset_name(-5.5), "UTC-5:30")
    # The generated names must parse back into real tzinfo objects.
    for name, hours in (("UTC-5", -5), ("UTC+10", 10), ("UTC+0", 0)):
      self.assertEqual(int(tzinfo_for(name).utcoffset(None).total_seconds()) // 3600, hours)


class CityCliTests(unittest.TestCase):
  """Both PDF CLIs take the LAT,LON,TZ spec through --city itself."""

  def test_city_accepts_spec_and_name_without_place(self):
    for parser_for in (annual_argument_parser, monthly_argument_parser):
      with self.subTest(parser=parser_for.__name__):
        arguments = parser_for().parse_args(attach_option_values(["--city", "-13.4,70,5.5", "--year", "2026"]))
        self.assertEqual(arguments.city, "-13.4,70,5.5")
        self.assertFalse(hasattr(arguments, "place"))
        arguments = parser_for().parse_args(["--city", "Helsinki", "--year", "2026"])
        self.assertEqual(arguments.city, "Helsinki")
        self.assertFalse(hasattr(arguments, "place"))


class MainIntegrationTests(unittest.TestCase):
  """main() must resolve --city as a LAT,LON,TZ spec into the PDF Location."""

  def test_monthly_main_uses_city_spec(self):
    import generate_monthly_calendar as monthly
    captured = {}
    with TemporaryDirectory() as directory:
      output = Path(directory) / "out.pdf"

      def fake_build(location, *args, **kwargs):
        captured["location"] = location
        return output

      with mock.patch.object(monthly, "build_monthly_pdf", side_effect=fake_build), \
           mock.patch.object(monthly, "lunar_year_months", return_value=[(2026, 3)] * 14), \
           mock.patch.object(monthly, "default_monthly_output_path", return_value=output), \
           redirect_stdout(io.StringIO()):
        self.assertEqual(monthly.main(["--city", "-13.4,70,5.5", "--year", "2026"]), 0)
    location = captured["location"]
    self.assertIsInstance(location, Location)
    self.assertEqual((location.latitude, location.longitude, location.timezone_name), (-13.4, 70.0, "UTC+5:30"))

  def test_main_errors_without_city_or_place(self):
    import importlib
    for module_name in ("generate_monthly_calendar", "generate_panchanga_calendar"):
      with self.subTest(module=module_name):
        module = importlib.import_module(module_name)
        with mock.patch.object(sys, "stderr", mock.Mock()), self.assertRaises(SystemExit):
          module.main(["--year", "2026"])

  def test_annual_main_uses_city_spec(self):
    import generate_panchanga_calendar as annual
    location_holder = {}
    real_load = annual.load_custom_location

    with TemporaryDirectory() as directory:
      output = Path(directory) / "out.pdf"

      def spy_load(latitude, longitude, timezone):
        location = real_load(latitude, longitude, timezone)
        location_holder["location"] = location
        return location

      def fake_build(location, *args, **kwargs):
        location_holder["built"] = location
        return output

      with mock.patch.object(annual, "load_custom_location", side_effect=spy_load), \
           mock.patch.object(annual, "lunar_year_months", return_value=[(2026, 3)] * 14), \
           mock.patch.object(annual, "build_pdf", side_effect=fake_build), \
           redirect_stdout(io.StringIO()):
        annual.main(["--city", "-13.4,70,5.5", "--year", "2026"])
    location = location_holder["location"]
    self.assertEqual((location.latitude, location.longitude, location.timezone_name), (-13.4, 70.0, "UTC+5:30"))
    self.assertIs(location_holder.get("built"), location)


if __name__ == "__main__":
  unittest.main()
