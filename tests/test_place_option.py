"""--place LAT,LON,TZ option for the generate*.py CLIs."""

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from generate_monthly_calendar import argument_parser as monthly_argument_parser
from generate_panchanga_calendar import (Location, argument_parser as annual_argument_parser, attach_place_values,
                                         load_location, parse_place_spec, resolve_cli_location)


class AttachPlaceValuesTests(unittest.TestCase):

  def test_glues_negative_value_to_flag(self):
    self.assertEqual(attach_place_values(["--place", "-13.4,70,5.5", "--start", "2026-03"]),
                     ["--place=-13.4,70,5.5", "--start", "2026-03"])

  def test_leaves_positive_values_alone(self):
    argv = ["--place", "12.97,77.59,5.5"]
    self.assertEqual(attach_place_values(argv), ["--place=12.97,77.59,5.5"])

  def test_no_place_flag(self):
    argv = ["--city", "Helsinki", "--start", "2026-03"]
    self.assertEqual(attach_place_values(argv), argv)


class ParsePlaceSpecTests(unittest.TestCase):

  def test_parses_three_floats(self):
    self.assertEqual(parse_place_spec("-13.4,70,5.5"), (-13.4, 70.0, 5.5))

  def test_negative_longitude_west(self):
    self.assertEqual(parse_place_spec("40.71,-74.0,-5"), (40.71, -74.0, -5.0))
    self.assertEqual(parse_place_spec("40.71,-74,-5"), (40.71, -74.0, -5.0))

  def test_whitespace_around_numbers_is_tolerated(self):
    self.assertEqual(parse_place_spec(" 12.97 , 77.59 , 5.5 "), (12.97, 77.59, 5.5))

  def test_blank_returns_none(self):
    self.assertIsNone(parse_place_spec(None))
    self.assertIsNone(parse_place_spec(""))
    self.assertIsNone(parse_place_spec("  "))

  def test_rejects_wrong_field_count(self):
    for text in ("12.97,77.59", "12.97", "12.97,77.59,5.5,9"):
      with self.subTest(text=text), self.assertRaisesRegex(ValueError, "exactly three"):
        parse_place_spec(text)

  def test_rejects_empty_field(self):
    with self.assertRaisesRegex(ValueError, "Timezone '' must be a number"):
      parse_place_spec("12.97,77.59,")

  def test_rejects_non_numeric(self):
    with self.assertRaisesRegex(ValueError, "Latitude 'abc' must be a number"):
      parse_place_spec("abc,77.59,5.5")

  def test_range_validation(self):
    for text, kind in (("95,0,5.5", "Latitude"), ("0,200,5.5", "Longitude"), ("0,0,15", "Timezone")):
      with self.subTest(text=text), self.assertRaisesRegex(ValueError, f"{kind} .* out of range"):
        parse_place_spec(text)


class NumericFormsTests(unittest.TestCase):
  """LAT,LON,TZ accept every float() spelling: integers, x.0, +sign, zero."""

  def test_pure_integers(self):
    self.assertEqual(parse_place_spec("13,77,5"), (13.0, 77.0, 5.0))

  def test_trailing_point_zero(self):
    self.assertEqual(parse_place_spec("13.0,-74.0,-5.0"), (13.0, -74.0, -5.0))

  def test_explicit_plus_sign(self):
    self.assertEqual(parse_place_spec("+13.4,+70,+5.5"), (13.4, 70.0, 5.5))

  def test_zeroes(self):
    self.assertEqual(parse_place_spec("0,0,0"), (0.0, 0.0, 0.0))

  def test_mixed_forms_in_one_spec(self):
    self.assertEqual(parse_place_spec("-33.87,+151.2,10"), (-33.87, 151.2, 10.0))

  def test_integer_and_negative_timezone_offset_names(self):
    from datetime_helper import fixed_offset_name, tzinfo_for
    self.assertEqual(fixed_offset_name(-5.0), "UTC-5")
    self.assertEqual(fixed_offset_name(10.0), "UTC+10")
    self.assertEqual(fixed_offset_name(0.0), "UTC+0")
    self.assertEqual(fixed_offset_name(-5.5), "UTC-5:30")
    # The generated names must parse back into real tzinfo objects.
    for name, hours in (("UTC-5", -5), ("UTC+10", 10), ("UTC+0", 0)):
      self.assertEqual(int(tzinfo_for(name).utcoffset(None).total_seconds()) // 3600, hours)

  def test_integer_spec_resolves_like_float_spec(self):
    from_integers = resolve_cli_location(place="13,77,-5")
    from_floats = resolve_cli_location(place="13.0,77.0,-5.0")
    self.assertEqual(from_integers, from_floats)


class ResolveCliLocationTests(unittest.TestCase):

  def test_place_wins_over_city(self):
    location = resolve_cli_location("Ujjain", place="-13.4,70,5.5")
    self.assertEqual((location.latitude, location.longitude, location.timezone_name), (-13.4, 70.0, "UTC+5:30"))

  def test_place_name_is_human_readable(self):
    location = resolve_cli_location(place="-13.4,70,5.5")
    self.assertEqual(location.name, "13.40S, 70.00E (UTC+5:30)")

  def test_city_fallback(self):
    self.assertEqual(resolve_cli_location("Ujjain"), load_location("Ujjain"))
    self.assertEqual(resolve_cli_location("Ujjain", place=None), load_location("Ujjain"))

  def test_requires_city_or_place(self):
    with self.assertRaisesRegex(ValueError, "City is required"):
      resolve_cli_location(None)


class AnnualCliTests(unittest.TestCase):

  def test_place_and_start_parse(self):
    parser = annual_argument_parser()
    arguments = parser.parse_args(attach_place_values(["--place", "-13.4,70,5.5", "--start", "2026-03"]))
    self.assertEqual(arguments.place, "-13.4,70,5.5")
    self.assertIsNone(arguments.city)

  def test_city_remains_accepted_without_place(self):
    parser = annual_argument_parser()
    arguments = parser.parse_args(["--city", "Helsinki", "--start", "2026-03"])
    self.assertEqual(arguments.city, "Helsinki")
    self.assertIsNone(arguments.place)


class MonthlyCliTests(unittest.TestCase):

  def test_place_and_start_parse(self):
    parser = monthly_argument_parser()
    arguments = parser.parse_args(attach_place_values(["--place", "-13.4,70,5.5", "--start", "2026-03"]))
    self.assertEqual(arguments.place, "-13.4,70,5.5")
    self.assertIsNone(arguments.city)

  def test_city_remains_accepted_without_place(self):
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
