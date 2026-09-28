"""Manual ``LAT,LON,TZ`` place across the CLI and web stack."""

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from datetime_helper import format_utc_offset
from generate_monthly_calendar import argument_parser as monthly_argument_parser
from generate_panchanga_calendar import (Location, argument_parser as annual_argument_parser, attach_option_values,
                                         load_custom_location, load_location, require_start_month, resolve_location)
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
    argv = attach_option_values(["--place", "-13.4,70,5.5", "--start", "2026-06"])
    arguments = annual_argument_parser().parse_args(argv)
    self.assertEqual(resolve_location(arguments.city, arguments.place).name, "13.40S, 70.00E (UTC+5:30)")


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
    response = app.test_client().get("/api/panchanga.ics?place=12.97,77.59,5.5&start=2026-03")
    self.assertEqual(response.status_code, 200)
    self.assertIn(b"BEGIN:VCALENDAR", response.data)

  def test_pdf(self):
    response = app.test_client().post("/generate", data={
      "place": "12.97,77.59,5.5",
      "start": "2026-03",
    })
    self.assertEqual(response.status_code, 200)


class AttachOptionValuesTests(unittest.TestCase):
  """A value that starts with a minus must survive argparse."""

  def test_glues_negative_value_to_flag(self):
    self.assertEqual(attach_option_values(["--place", "-13.4,70,5.5", "--start", "2026-03"]),
                     ["--place=-13.4,70,5.5", "--start", "2026-03"])

  def test_leaves_positive_values_alone(self):
    # A value that does not start with '-' needs no glue: argparse is happy
    # with a split flag and value, so argv is left byte-identical.
    argv = ["--place", "12.97,77.59,5.5", "--start", "2026-03"]
    self.assertEqual(attach_option_values(argv), argv)

  def test_no_place_flag(self):
    argv = ["--city", "Helsinki", "--start", "2026-03"]
    self.assertEqual(attach_option_values(argv), argv)

  def test_glues_a_bce_start_year(self):
    # argparse would read the leading '-' of -500-03 as another option.
    self.assertEqual(attach_option_values(["--city", "Ujjain", "--start", "-500-03"]),
                     ["--city", "Ujjain", "--start=-500-03"])

  def test_leaves_a_flag_after_a_flag_alone(self):
    # --start with no value must error as a missing value, not as
    # "--start=--city" plus "unrecognized arguments: Ujjain".
    argv = ["--start", "--city", "Ujjain"]
    self.assertEqual(attach_option_values(argv), argv)


class BceStartMonthTests(unittest.TestCase):
  """``--start`` accepts astronomical years, as the day view and the API already do."""

  def test_parses_ce_bce_year_zero_and_padded_forms(self):
    self.assertEqual(require_start_month("2026-03"), (2026, 3))
    self.assertEqual(require_start_month("-500-03"), (-500, 3))
    self.assertEqual(require_start_month("-0500-03"), (-500, 3))  # same year, zero-padded
    self.assertEqual(require_start_month("-5000-12"), (-5000, 12))  # oldest supported year
    self.assertEqual(require_start_month("0000-01"), (0, 1))  # zero still works

  def test_rejects_malformed_and_out_of_range(self):
    for text in ("2026-3", "2026-13", "2026-00", "-50000-03", "-03", "abc-03", "", None, "2026", "202603", "26-06",
                 "500-03", "0-01"):
      with self.subTest(text=text), self.assertRaisesRegex(ValueError, "YYYY-MM"):
        require_start_month(text)

  def test_filename_round_trips_through_the_parser(self):
    # default_output_path formats with {:04d}; the result must parse back.
    for year in (2026, 500, 0, -500, -5000, -1):
      with self.subTest(year=year):
        formatted = f"{year:04d}-03"
        self.assertEqual(require_start_month(formatted), (year, 3))

  def test_both_parsers_accept_a_bce_start(self):
    for parser in (annual_argument_parser(), monthly_argument_parser()):
      arguments = parser.parse_args(attach_option_values(["--city", "Ujjain", "--start", "-500-03"]))
      self.assertEqual(arguments.start, "-500-03")
      self.assertEqual(require_start_month(arguments.start), (-500, 3))

  def test_cli_builds_a_bce_pdf(self):
    import generate_panchanga_calendar as annual
    with TemporaryDirectory() as directory:
      output = Path(directory) / "bce.pdf"
      with mock.patch.object(sys, "stdout", mock.Mock()):
        annual.main(["--city", "Ujjain", "--start=-500-03", "--output", str(output)])
      self.assertTrue(output.stat().st_size > 0)

  def test_ics_endpoint_rejects_a_bce_start(self):
    # iCalendar DATE values allow only four-digit years, so a BCE span
    # cannot be exported. The endpoint must say so (400), not emit
    # DTSTART;VALUE=DATE:-5000301 that calendar apps reject.
    from webapp.ics_service import generate_ics
    with self.assertRaisesRegex(ValueError, "four-digit years"):
      generate_ics(load_location("Ujjain"), -500, 3)
    response = app.test_client().get("/api/panchanga.ics?city=Ujjain&start=-500-03")
    self.assertEqual(response.status_code, 400)
    self.assertIn(b"four-digit years", response.data)

  def test_pdf_endpoint_accepts_a_bce_start(self):
    response = app.test_client().post("/generate", data={
      "city": "Ujjain",
      "start": "-500-03",
    })
    self.assertEqual(response.status_code, 200)


class PlaceSpecFormsTests(unittest.TestCase):
  """LAT,LON,TZ accept every float() spelling: integers, x.0, +sign, zero."""

  def test_three_floats(self):
    location = resolve_location(place="-13.4,70,5.5")
    self.assertEqual((location.latitude, location.longitude, location.timezone_name), (-13.4, 70.0, "UTC+5:30"))
    self.assertEqual(location.name, "13.40S, 70.00E (UTC+5:30)")

  def test_negative_longitude_west(self):
    location = resolve_location(place="40.71,-74.0,-5")
    self.assertEqual((location.latitude, location.longitude, location.timezone_name), (40.71, -74.0, "UTC-5"))

  def test_pure_integers(self):
    location = resolve_location(place="13,77,5")
    self.assertEqual((location.latitude, location.longitude, location.timezone_name), (13.0, 77.0, "UTC+5"))

  def test_explicit_plus_sign(self):
    location = resolve_location(place="+13.4,+70,+5.5")
    self.assertEqual((location.latitude, location.longitude, location.timezone_name), (13.4, 70.0, "UTC+5:30"))

  def test_zeroes(self):
    location = resolve_location(place="0,0,0")
    self.assertEqual((location.latitude, location.longitude, location.timezone_name), (0.0, 0.0, "UTC+0"))

  def test_mixed_forms_in_one_spec(self):
    location = resolve_location(place="-33.87,+151.2,10")
    self.assertEqual((location.latitude, location.longitude, location.timezone_name), (-33.87, 151.2, "UTC+10"))

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


class PlaceCliTests(unittest.TestCase):
  """Both PDF CLIs accept --place instead of --city."""

  def test_annual_place_and_start_parse(self):
    parser = annual_argument_parser()
    arguments = parser.parse_args(attach_option_values(["--place", "-13.4,70,5.5", "--start", "2026-03"]))
    self.assertEqual(arguments.place, "-13.4,70,5.5")
    self.assertIsNone(arguments.city)

  def test_annual_city_remains_accepted_without_place(self):
    parser = annual_argument_parser()
    arguments = parser.parse_args(["--city", "Helsinki", "--start", "2026-03"])
    self.assertEqual(arguments.city, "Helsinki")
    self.assertIsNone(arguments.place)

  def test_monthly_place_and_start_parse(self):
    parser = monthly_argument_parser()
    arguments = parser.parse_args(attach_option_values(["--place", "-13.4,70,5.5", "--start", "2026-03"]))
    self.assertEqual(arguments.place, "-13.4,70,5.5")
    self.assertIsNone(arguments.city)

  def test_monthly_city_remains_accepted_without_place(self):
    parser = monthly_argument_parser()
    arguments = parser.parse_args(["--city", "Helsinki", "--start", "2026-03"])
    self.assertEqual(arguments.city, "Helsinki")
    self.assertIsNone(arguments.place)


class MainIntegrationTests(unittest.TestCase):
  """main() must resolve --place into the Location used for PDF generation."""

  def test_monthly_main_uses_place(self):
    import generate_monthly_calendar as monthly
    captured = {}
    with TemporaryDirectory() as directory:
      output = Path(directory) / "out.pdf"

      def fake_build(location, *args, **kwargs):
        captured["location"] = location
        return output

      with mock.patch.object(monthly, "build_monthly_pdf", side_effect=fake_build), \
           mock.patch.object(monthly, "default_monthly_output_path", return_value=output), \
           mock.patch.object(sys, "stdout", mock.Mock()):
        self.assertEqual(monthly.main(["--place", "-13.4,70,5.5", "--start", "2026-03"]), 0)
    location = captured["location"]
    self.assertIsInstance(location, Location)
    self.assertEqual((location.latitude, location.longitude, location.timezone_name), (-13.4, 70.0, "UTC+5:30"))

  def test_monthly_main_errors_without_city_or_place(self):
    import generate_monthly_calendar as monthly
    with mock.patch.object(sys, "stderr", mock.Mock()), self.assertRaises(SystemExit):
      monthly.main(["--start", "2026-03"])

  def test_annual_main_uses_place(self):
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
           mock.patch.object(annual, "build_pdf", side_effect=fake_build), \
           mock.patch.object(sys, "stdout", mock.Mock()):
        annual.main(["--place", "-13.4,70,5.5", "--start", "2026-03"])
    location = location_holder["location"]
    self.assertEqual((location.latitude, location.longitude, location.timezone_name), (-13.4, 70.0, "UTC+5:30"))
    self.assertIs(location_holder.get("built"), location)

  def test_annual_main_errors_without_city_or_place(self):
    import generate_panchanga_calendar as annual
    with mock.patch.object(sys, "stderr", mock.Mock()), self.assertRaises(SystemExit):
      annual.main(["--start", "2026-03"])


if __name__ == "__main__":
  unittest.main()
