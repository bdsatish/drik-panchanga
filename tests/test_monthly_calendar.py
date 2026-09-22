"""Regression tests for the 12-month wall-grid panchanga PDF."""

from datetime import date, timedelta
from io import BytesIO
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

from generate_monthly_calendar import (
  MONTHLY_LAYOUT_VERSION,
  RULESET_VERSION,
  argument_parser,
  build_monthly_pdf,
  collect_context,
  context_months,
  day_details,
  default_monthly_output_path,
  draw_cell,
  draw_header,
  ekadashi_name,
  ensure_pdf_fonts,
  format_hms,
  load_location,
  sun_moon_lines,
  tithi_name,
)
from generate_panchanga_calendar import DEFAULT_FESTIVALS_PATH, _month_sequence as month_sequence


class MonthSequenceTests(unittest.TestCase):

  def test_month_sequence_spans_year_boundary(self):
    months = month_sequence(2026, 11, 4)
    self.assertEqual(months, [(2026, 11), (2026, 12), (2027, 1), (2027, 2)])

  def test_context_months_adds_buffer(self):
    ctx = context_months(2026, 3)
    self.assertEqual(len(ctx), 14)
    self.assertEqual(ctx[0], (2026, 2))
    self.assertEqual(ctx[-1], (2027, 3))


class BuildPdfTests(unittest.TestCase):

  def test_generates_exactly_twelve_pages(self):
    with TemporaryDirectory() as directory:
      output = Path(directory) / "calendar.pdf"
      with mock.patch("generate_monthly_calendar.find_local_eclipses", return_value=[]):
        build_monthly_pdf(load_location("Helsinki"), 2026, 6, output)
      document = output.read_bytes()
    page_objects = re.findall(rb"/Type\s*/Page\b", document)
    self.assertEqual(len(page_objects), 12)
    self.assertIn(RULESET_VERSION.encode("ascii"), document)

  def test_pdf_metadata_contains_title(self):
    with TemporaryDirectory() as directory:
      output = Path(directory) / "calendar.pdf"
      with mock.patch("generate_monthly_calendar.find_local_eclipses", return_value=[]):
        build_monthly_pdf(load_location("Ujjain"), 2026, 6, output)
      document = output.read_bytes()
    # Title/subject live in the uncompressed Info dict; page streams are flate-encoded.
    self.assertIn(b"Ujjain, IN Panchanga June 2026 to May 2027", document)
    self.assertIn(RULESET_VERSION.encode("ascii"), document)

  def test_default_output_path(self):
    path = default_monthly_output_path(load_location("Helsinki"), 2026, 3)
    self.assertEqual(path.name, "helsinki-fi_panchanga_wall_2026-03_to_2027-02.pdf")

  def test_purnimanta_filename_suffix(self):
    path = default_monthly_output_path(load_location("Helsinki"), 2026, 3, month_system="purnimanta")
    self.assertEqual(path.name, "helsinki-fi_panchanga_wall_2026-03_to_2027-02_purnimanta.pdf")

  def test_ayanamsa_filename_suffix(self):
    path = default_monthly_output_path(load_location("Helsinki"), 2026, 3, coordinate_selection="raman")
    self.assertEqual(path.name, "helsinki-fi_panchanga_wall_2026-03_to_2027-02_raman.pdf")

  def test_tropical_filename_suffix(self):
    path = default_monthly_output_path(load_location("Helsinki"), 2026, 3, coordinate_selection="tropical")
    self.assertEqual(path.name, "helsinki-fi_panchanga_wall_2026-03_to_2027-02_tropical.pdf")


class CliTests(unittest.TestCase):

  def test_cli_defaults(self):
    parser = argument_parser()
    arguments = parser.parse_args(["--city", "Helsinki", "--start", "2026-03"])
    self.assertEqual(arguments.month, "amanta")
    self.assertEqual(arguments.ayanamsa, "citra")

  def test_cli_accepts_purnimanta(self):
    parser = argument_parser()
    arguments = parser.parse_args(["--city", "Helsinki", "--start", "2026-03", "--month", "purnimanta"])
    self.assertEqual(arguments.month, "purnimanta")

  def test_cli_accepts_ayanamsa(self):
    parser = argument_parser()
    arguments = parser.parse_args(["--city", "Helsinki", "--start", "2026-03", "--ayanamsa", "revati"])
    self.assertEqual(arguments.ayanamsa, "revati")


class DayDetailsTests(unittest.TestCase):

  def test_tithi_name_mapping(self):
    self.assertEqual(tithi_name(1), "Pratipadā")
    self.assertEqual(tithi_name(15), "Pūrṇimā")
    self.assertEqual(tithi_name(30), "Amāvāsyā")

  def test_format_hms_past_midnight(self):
    self.assertEqual(format_hms([25.5, 30, 0]), "26:00")
    self.assertEqual(format_hms([5.0, 44.0, 30.0]), "05:44")

  def test_day_details_returns_leap_tithi(self):
    location = load_location("Ujjain")
    # 2026-06-15 has a leap tithi (Amavasya + Pratipada)
    tithi_lines, _naks_lines, _yoga_names = day_details(location, date(2026, 6, 15))
    self.assertEqual(len(tithi_lines), 2)
    self.assertEqual(tithi_lines[0][0], "K15")
    self.assertEqual(tithi_lines[1][0], "S1")

  def test_day_details_returns_leap_nakshatra(self):
    location = load_location("Ujjain")
    # 2026-06-12 has a leap nakshatra
    tithi_lines, naks_lines, _yoga_names = day_details(location, date(2026, 6, 12))
    self.assertEqual(len(naks_lines), 2)

  def test_day_details_returns_skipped_yoga_names(self):
    location = load_location("Ujjain")
    # 2026-06-10: Ayushman ends 06:27, Saubhagya is entirely skipped within the day
    _tithi_lines, _naks_lines, yoga_names = day_details(location, date(2026, 6, 10))
    self.assertEqual(yoga_names, ["Āyuṣmān", "Saubhāgya"])

  def test_day_details_returns_none_without_sunrise(self):
    # Regression: a polar day/night has no sunrise, so every sunrise-based
    # quantity is undefined. Before the guard this returned garbage end times
    # such as ('K7', '-59069077:35').
    location = load_location("Murmansk, RU")
    self.assertIsNone(day_details(location, date(2026, 6, 21)))
    self.assertIsNone(day_details(location, date(2026, 12, 21)))

  def test_day_details_still_computes_at_polar_shoulder(self):
    # Murmansk does see a sunrise outside the polar day/night window.
    location = load_location("Murmansk, RU")
    tithi_lines, naks_lines, yoga_names = day_details(location, date(2026, 3, 15))
    self.assertTrue(tithi_lines and naks_lines and yoga_names)


class SunMoonTests(unittest.TestCase):

  def test_sun_moon_lines_for_known_day(self):
    location = load_location("Ujjain")
    lines = sun_moon_lines(location, date(2026, 6, 1))
    self.assertEqual(len(lines), 2)
    self.assertTrue(lines[0].startswith("Sun:"))
    self.assertTrue(lines[1].startswith("Moon:"))
    self.assertIn(" – ", lines[0])
    self.assertIn(" – ", lines[1])

  def test_sun_moon_lines_omit_sun_without_sunrise(self):
    # Regression: the Sun line used to render the 0.0 rise sentinel as
    # ``Sun: -59069097:00 – -59069097:00`` at polar locations.
    location = load_location("Murmansk, RU")
    for day in (date(2026, 6, 21), date(2026, 12, 21)):
      with self.subTest(day=day):
        lines = sun_moon_lines(location, day)
        self.assertFalse([line for line in lines if line.startswith("Sun:")])
        self.assertTrue(all("-59" not in line for line in lines))

  def test_sun_moon_lines_keep_the_half_that_exists(self):
    # Regression: sunrise and sunset were range-checked with a single ``and``,
    # so one missing event dropped the whole line. Near the polar circle the
    # two go missing on different days; Norilsk on 20 May 2026 has a sunrise
    # but no sunset (and the reverse before/after).
    location = load_location("Norilsk, RU")
    lines = sun_moon_lines(location, date(2026, 5, 20))
    sun_lines = [line for line in lines if line.startswith("Sun:")]
    self.assertEqual(len(sun_lines), 1)
    self.assertRegex(sun_lines[0], r"^Sun: \(\d\d:\d\d –\) \d\d:\d\d – --$")
    self.assertTrue(all("-59" not in line for line in lines))

  def test_sun_moon_lines_render_sunset_only(self):
    # The mirror case: no sunrise, but a sunset worth printing.
    with mock.patch("generate_monthly_calendar.panchanga.sunrise", return_value=[0.0, [-59069097, 0, 0]]):
      lines = sun_moon_lines(load_location("Ujjain"), date(2026, 6, 1))
    sun_lines = [line for line in lines if line.startswith("Sun:")]
    self.assertEqual(len(sun_lines), 1)
    self.assertRegex(sun_lines[0], r"^Sun: -- – \d\d:\d\d$")

  def test_sun_moon_lines_omit_sun_when_both_are_missing(self):
    with mock.patch("generate_monthly_calendar.panchanga.sunrise", return_value=[0.0, [-1, 0, 0]]), mock.patch(
        "generate_monthly_calendar.panchanga.sunset", return_value=[0.0, [-1, 0, 0]]):
      lines = sun_moon_lines(load_location("Ujjain"), date(2026, 6, 1))
    self.assertFalse([line for line in lines if line.startswith("Sun:")])


class CellDrawTests(unittest.TestCase):

  def test_solar_day_line_is_drawn(self):
    ensure_pdf_fonts()
    pdf = mock.Mock()
    pdf.stringWidth = lambda text, font, size: len(text) * size * 0.5
    from festival_rules import DayRecord
    context = {
      "records_by_date": {
        date(2026, 6, 16): DayRecord(date(2026, 6, 16), "S2", 1, 1, "5", False, 0.0)
      },
      "festival_names_by_date": {},
      "eclipse_dates": set(),
      "eclipse_details_by_date": {},
      "masa_badges": {},
      "solar_by_date": {
        date(2026, 6, 16): (3, 1, True)
      },
      "shraddha_tithis": {
        date(2026, 6, 16): 7
      },
      "ekadashi": set(),
      "pradosham": set(),
      "sankashti": set(),
    }
    draw_cell(pdf, 20.0, 500.0, 100.0, 75.0, 16, date(2026, 6, 16), load_location("Ujjain"), context, col=0)
    solar_calls = [c for c in pdf.drawString.call_args_list if c.args[2] in ("Mithuna 1", " / [S7]")]
    self.assertEqual(len(solar_calls), 2)
    self.assertEqual(solar_calls[0].args[2], "Mithuna 1")
    self.assertEqual(solar_calls[1].args[2], " / [S7]")

  def test_tithi_paksha_prefix_is_drawn(self):
    ensure_pdf_fonts()
    pdf = mock.Mock()
    from festival_rules import DayRecord
    context = {
      "records_by_date": {
        date(2026, 6, 15): DayRecord(date(2026, 6, 15), "K15", 1, 1, "5", False, 0.0)
      },
      "festival_names_by_date": {},
      "eclipse_dates": set(),
      "eclipse_details_by_date": {},
      "masa_badges": {},
      "solar_by_date": {},
      "ekadashi": set(),
      "pradosham": set(),
      "sankashti": set(),
    }
    with mock.patch("generate_monthly_calendar.day_details", return_value=([("K15", "08:24"),
                                                                            ("S1", "28:31")], [], ["Śūla"])):
      draw_cell(pdf, 20.0, 500.0, 100.0, 75.0, 15, date(2026, 6, 15), load_location("Ujjain"), context, col=0)
    drawn_text = [c.args[2] for c in pdf.drawString.call_args_list]
    self.assertIn("Śrāvaṇa K15 08:24", drawn_text)
    self.assertIn("Śrāvaṇa S1 28:31", drawn_text)

  def test_no_sunrise_cell_renders_marker_and_no_end_times(self):
    # day_details returns None at a polar day/night; the cell must show a
    # marker instead of garbage end times like '-59069077:35'.
    ensure_pdf_fonts()
    pdf = mock.Mock()
    from festival_rules import DayRecord
    context = {
      "records_by_date": {
        date(2026, 6, 21): DayRecord(date(2026, 6, 21), "K7", 1, 1, "5", False, 0.0)
      },
      "festival_names_by_date": {},
      "eclipse_dates": set(),
      "eclipse_details_by_date": {},
      "masa_badges": {},
      "solar_by_date": {},
      "ekadashi": set(),
      "pradosham": set(),
      "sankashti": set(),
    }
    with mock.patch("generate_monthly_calendar.day_details", return_value=None):
      draw_cell(pdf, 20.0, 500.0, 100.0, 75.0, 21, date(2026, 6, 21), load_location("Ujjain"), context, col=0)
    drawn_text = [c.args[2] for c in pdf.drawString.call_args_list]
    self.assertIn("no sunrise", drawn_text)
    self.assertFalse([text for text in drawn_text if "-59" in text])

  def test_masa_start_fill_is_drawn(self):
    ensure_pdf_fonts()
    pdf = mock.Mock()
    from festival_rules import DayRecord
    context = {
      "records_by_date": {
        date(2026, 6, 16): DayRecord(date(2026, 6, 16), "S2", 1, 1, "5", False, 0.0)
      },
      "festival_names_by_date": {},
      "eclipse_dates": set(),
      "eclipse_details_by_date": {},
      "masa_badges": {
        date(2026, 6, 16): "5"
      },
      "solar_by_date": {},
      "ekadashi": set(),
      "pradosham": set(),
      "sankashti": set(),
    }
    draw_cell(pdf, 20.0, 500.0, 100.0, 75.0, 16, date(2026, 6, 16), load_location("Ujjain"), context, col=0)
    fill_colors = [c.args[0] for c in pdf.setFillColor.call_args_list]
    from generate_panchanga_calendar import MASA_START_ROW
    self.assertIn(MASA_START_ROW, fill_colors)


class VarjyamTests(unittest.TestCase):

  def test_varjyam_lines_two_windows_on_nakshatra_change_day(self):
    from generate_monthly_calendar import varjyam_lines
    location = load_location("Ujjain")
    lines = varjyam_lines(location, date(2026, 6, 14))
    self.assertEqual(len(lines), 2)
    for line in lines:
      self.assertTrue(line.startswith("Varjyam: "))

  def test_varjyam_line_is_drawn_in_cell(self):
    ensure_pdf_fonts()
    pdf = mock.Mock()
    from festival_rules import DayRecord
    civil = date(2026, 6, 14)
    context = {
      "records_by_date": {
        civil: DayRecord(civil, "S30", 1, 1, "5", False, 0.0)
      },
      "festival_names_by_date": {},
      "eclipse_dates": set(),
      "eclipse_details_by_date": {},
      "masa_badges": {},
      "solar_by_date": {},
      "ekadashi": set(),
      "pradosham": set(),
      "sankashti": set(),
    }
    with mock.patch("generate_monthly_calendar.panchanga.varjyam", return_value=[[[15.22, 13, 0], [16.63, 37, 0]]]):
      draw_cell(pdf, 20.0, 500.0, 100.0, 75.0, 14, civil, load_location("Ujjain"), context, col=0)
    drawn_text = [c.args[2] for c in pdf.drawString.call_args_list]
    self.assertIn("Varjyam: 15:26 – 17:15", drawn_text)


class RahuKalaTableTests(unittest.TestCase):

  def test_table_lines_cover_all_weekdays_sunday_first(self):
    from generate_monthly_calendar import rahu_kala_table_lines
    lines = rahu_kala_table_lines(load_location("Ujjain"), 2026, 6)
    self.assertEqual([line.split()[0] for line in lines], ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"])
    import re
    for line in lines:
      self.assertRegex(line, r"^(Su|Mo|Tu|We|Th|Fr|Sa) \d{2}:\d{2}-\d{2}:\d{2}$")

  def test_table_is_drawn_with_header_and_seven_rows(self):
    from generate_monthly_calendar import draw_rahu_kala_table
    pdf = mock.Mock()
    draw_rahu_kala_table(pdf, 20.0, 500.0, load_location("Ujjain"), 2026, 6)
    drawn = [c.args[2] for c in pdf.drawString.call_args_list]
    self.assertEqual(drawn[0], "Rahu kala")
    self.assertEqual(len(drawn), 8)

  def test_table_envelopes_whole_month_not_first_week(self):
    from generate_monthly_calendar import rahu_kala_table_lines
    lines = dict(line.split() for line in rahu_kala_table_lines(load_location("Ujjain"), 2026, 6))
    self.assertEqual(lines["Mo"], "07:25-09:09")

  def test_table_envelope_spans_dst_transition(self):
    from generate_monthly_calendar import rahu_kala_table_lines
    lines = dict(line.split() for line in rahu_kala_table_lines(load_location("Helsinki"), 2026, 3))
    self.assertEqual(lines["Mo"], "07:52-10:12")


class TithiIndexCellTests(unittest.TestCase):

  def test_first_cell_lists_tithis_one_to_eight(self):
    from generate_monthly_calendar import draw_tithi_index_cell
    pdf = mock.Mock()
    draw_tithi_index_cell(pdf, 20.0, 500.0, 1, 8)
    drawn = [c.args[2] for c in pdf.drawString.call_args_list]
    self.assertEqual(drawn[0], "S Śukla / K Kṛṣṇa")
    self.assertEqual(len(drawn), 9)
    self.assertIn(" 1 Pratipadā", drawn)
    self.assertIn(" 8 Aṣṭamī", drawn)

  def test_second_cell_lists_tithis_nine_to_fifteen(self):
    from generate_monthly_calendar import draw_tithi_index_cell
    pdf = mock.Mock()
    draw_tithi_index_cell(pdf, 20.0, 500.0, 9, 15)
    drawn = [c.args[2] for c in pdf.drawString.call_args_list]
    self.assertEqual(drawn[0], "S Śukla / K Kṛṣṇa")
    self.assertEqual(len(drawn), 8)
    self.assertIn("15 Pūrṇimā / Amāvāsyā", drawn)


class YearLabelTests(unittest.TestCase):

  def test_year_label_matches_webapp_format(self):
    import panchanga
    from festival_rules import DayRecord
    from generate_monthly_calendar import year_label_for_month

    panchanga.set_coordinate_selection("citra")
    civil = date(2026, 6, 15)
    records_by_date = {civil: DayRecord(civil, "K15", 5, 7, "3", False, 0.0)}
    label = year_label_for_month(True, 2026, 6, records_by_date)
    self.assertEqual(label, "Parābhava 1948, Siddhārthī 2083, Kali (elapsed) 5127")

  def test_year_label_is_none_without_record(self):
    from generate_monthly_calendar import year_label_for_month
    self.assertIsNone(year_label_for_month(True, 2026, 6, {}))

  def test_year_label_uses_underlying_month_for_purnimanta(self):
    from festival_rules import DayRecord
    from generate_monthly_calendar import year_label_for_month
    import panchanga
    # Underlying month 1 (Caitra), Krsna paksha -> purnimanta displays as 2 (Vaisakha).
    # Year label must use the underlying month, not the display month.
    civil = date(2026, 4, 15)
    records_by_date = {civil: DayRecord(civil, "K20", 1, 1, "1", False, 0.0)}
    with mock.patch.object(panchanga, "elapsed_year", return_value=(5127, 1948, 2083)) as mock_elapsed, \
         mock.patch.object(panchanga, "samvatsara", return_value=1) as mock_samvatsara, \
         mock.patch.object(panchanga, "samvatsara_north_modern", return_value=1) as mock_north:
      label = year_label_for_month(False, 2026, 4, records_by_date)
      mock_elapsed.assert_called_with(mock.ANY, 1)
      mock_samvatsara.assert_called_with(mock.ANY, 1)
      mock_north.assert_called_with(mock.ANY, 1)


class ContextTests(unittest.TestCase):

  def test_collect_context_includes_masa_badges(self):
    location = load_location("Ujjain")
    months = [(2026, 5), (2026, 6)]
    ctx = collect_context(months, location, DEFAULT_FESTIVALS_PATH, amanta=True)
    self.assertIn("masa_badges", ctx)
    self.assertIn("solar_by_date", ctx)
    self.assertIn("ekadashi", ctx)

  def test_collect_context_includes_pradosham_and_sankashti(self):
    """Context must include pradosham and sankashti sets populated from selectors."""
    location = load_location("Ujjain")
    months = [(2026, 1), (2026, 2)]
    ctx = collect_context(months, location, DEFAULT_FESTIVALS_PATH, amanta=True)
    self.assertIn("pradosham", ctx)
    self.assertIn("sankashti", ctx)
    # Both should be sets of civil dates
    self.assertIsInstance(ctx["pradosham"], set)
    self.assertIsInstance(ctx["sankashti"], set)
    # For a real location, both should be non-empty across two months
    self.assertGreater(len(ctx["pradosham"]), 0)
    self.assertGreater(len(ctx["sankashti"]), 0)


class MonthlyHeaderTimezoneTests(unittest.TestCase):
  """Monthly header must show UTC offset next to the place name."""

  def test_header_includes_timezone(self):
    location = load_location("Ujjain")
    pdf = mock.Mock()
    pdf.stringWidth = lambda text, font, size: len(text) * size * 0.5
    draw_header(pdf, location, 2026, 3, True, "citra", None)
    place_calls = [c for c in pdf.drawString.call_args_list if "Ujjain" in str(c.args[2])]
    self.assertEqual(len(place_calls), 1)
    self.assertIn("UTC+5:30 (IST)", place_calls[0].args[2])

  def test_header_timezone_respects_dst(self):
    location = load_location("Helsinki")
    pdf = mock.Mock()
    pdf.stringWidth = lambda text, font, size: len(text) * size * 0.5
    draw_header(pdf, location, 2026, 6, True, "citra", None)
    place_calls = [c for c in pdf.drawString.call_args_list if "Helsinki" in str(c.args[2])]
    self.assertEqual(len(place_calls), 1)
    self.assertIn("UTC+3 (EEST)", place_calls[0].args[2])

  def test_header_timezone_winter_no_dst(self):
    location = load_location("Helsinki")
    pdf = mock.Mock()
    pdf.stringWidth = lambda text, font, size: len(text) * size * 0.5
    draw_header(pdf, location, 2026, 12, True, "citra", None)
    place_calls = [c for c in pdf.drawString.call_args_list if "Helsinki" in str(c.args[2])]
    self.assertEqual(len(place_calls), 1)
    self.assertIn("UTC+2 (EET)", place_calls[0].args[2])


class DstLabelInjectionTests(unittest.TestCase):
  """DST transition labels must be injected as dst_labels_by_date."""

  def test_collect_context_includes_dst_start(self):
    from generate_monthly_calendar import collect_context
    location = load_location("Helsinki")
    months = [(2026, 3), (2026, 4)]
    ctx = collect_context(months, location, DEFAULT_FESTIVALS_PATH, amanta=True)
    dst_labels = ctx["dst_labels_by_date"]
    # Mar 29, 2026 is DST start for Helsinki
    from datetime import date
    self.assertIn("DST starts", dst_labels.get(date(2026, 3, 29), []))

  def test_collect_context_includes_dst_end(self):
    from generate_monthly_calendar import collect_context
    location = load_location("Helsinki")
    months = [(2026, 10), (2026, 11)]
    ctx = collect_context(months, location, DEFAULT_FESTIVALS_PATH, amanta=True)
    dst_labels = ctx["dst_labels_by_date"]
    # Oct 25, 2026 is DST end for Helsinki
    from datetime import date
    self.assertIn("DST ends", dst_labels.get(date(2026, 10, 25), []))

  def test_collect_context_no_dst_for_non_dst_zone(self):
    from generate_monthly_calendar import collect_context
    location = load_location("Ujjain")
    months = [(2026, 3), (2026, 4)]
    ctx = collect_context(months, location, DEFAULT_FESTIVALS_PATH, amanta=True)
    dst_labels = ctx["dst_labels_by_date"]
    # Ujjain has no DST - no DST labels should appear
    all_labels = [label for labels in dst_labels.values() for label in labels]
    self.assertNotIn("DST starts", all_labels)
    self.assertNotIn("DST ends", all_labels)


class IsoWeekNumberTests(unittest.TestCase):
  """Sunday cell shows the ISO week of the Monday in its row."""

  def test_sunday_shows_monday_week(self):
    from generate_monthly_calendar import draw_cell, ensure_pdf_fonts
    ensure_pdf_fonts()
    location = load_location("Ujjain")
    # Sunday Jan 4, 2026 is in ISO week 1, but Monday Jan 5 is week 2.
    # The Sunday cell must show W2 to match Mon–Sat in its row.
    from festival_rules import DayRecord
    civil = date(2026, 1, 4)
    record = DayRecord(civil, "S1", 1, 1, "5", False, 0.0)
    context = {
      "records_by_date": {
        civil: record
      },
      "festival_names_by_date": {},
      "eclipse_dates": set(),
      "eclipse_details_by_date": {},
      "masa_badges": {},
      "solar_by_date": {},
      "ekadashi": set(),
      "pradosham": set(),
      "sankashti": set(),
    }
    pdf = mock.Mock()
    draw_cell(pdf, 20.0, 500.0, 100.0, 75.0, 4, civil, location, context, col=0)
    drawn = [c.args[2] for c in pdf.drawString.call_args_list]
    self.assertIn("W2", drawn)

  def test_year_boundary_sunday(self):
    from generate_monthly_calendar import draw_cell, ensure_pdf_fonts
    ensure_pdf_fonts()
    location = load_location("Ujjain")
    # Sunday Dec 28, 2025 is ISO week 52, but Monday Dec 29 is week 1.
    from festival_rules import DayRecord
    civil = date(2025, 12, 28)
    record = DayRecord(civil, "S1", 1, 1, "5", False, 0.0)
    context = {
      "records_by_date": {
        civil: record
      },
      "festival_names_by_date": {},
      "eclipse_dates": set(),
      "eclipse_details_by_date": {},
      "masa_badges": {},
      "solar_by_date": {},
      "ekadashi": set(),
      "pradosham": set(),
      "sankashti": set(),
    }
    pdf = mock.Mock()
    draw_cell(pdf, 20.0, 500.0, 100.0, 75.0, 28, civil, location, context, col=0)
    drawn = [c.args[2] for c in pdf.drawString.call_args_list]
    self.assertIn("W1", drawn)

  def test_jan_2027_year_boundary(self):
    from generate_monthly_calendar import draw_cell, ensure_pdf_fonts
    ensure_pdf_fonts()
    location = load_location("Ujjain")
    # Sunday Jan 3, 2027 is ISO week 53 of 2026, but Mon Jan 4 is week 1.
    # The Sunday cell must show W1 (the week containing the Thursday).
    from festival_rules import DayRecord
    civil = date(2027, 1, 3)
    record = DayRecord(civil, "S1", 1, 1, "5", False, 0.0)
    context = {
      "records_by_date": {
        civil: record
      },
      "festival_names_by_date": {},
      "eclipse_dates": set(),
      "eclipse_details_by_date": {},
      "masa_badges": {},
      "solar_by_date": {},
      "ekadashi": set(),
      "pradosham": set(),
      "sankashti": set(),
    }
    pdf = mock.Mock()
    draw_cell(pdf, 20.0, 500.0, 100.0, 75.0, 3, civil, location, context, col=0)
    drawn = [c.args[2] for c in pdf.drawString.call_args_list]
    self.assertIn("W1", drawn)
    self.assertNotIn("W53", drawn)


class EkadashiNameTests(unittest.TestCase):

  def _record(self, civil, tithi, masa, is_adhika=False):
    from festival_rules import DayRecord
    return DayRecord(civil, tithi, 1, 1, masa, is_adhika, 0.0)

  def test_amanta_sukla_uses_same_month(self):
    record = self._record(date(2026, 3, 29), "S11", "1")
    self.assertEqual(ekadashi_name(record, amanta=True), "Kāmadā Ekādaśī")

  def test_amanta_krsna_names_from_same_month_entry(self):
    record = self._record(date(2026, 4, 13), "K11", "1")
    self.assertEqual(ekadashi_name(record, amanta=True), "Varūthinī Ekādaśī")

  def test_purnimanta_krsna_shifts_back_one_month(self):
    record = self._record(date(2026, 4, 13), "K11", "1")
    self.assertEqual(ekadashi_name(record, amanta=False), "Varūthinī Ekādaśī")

  def test_year_boundary_krsna_wraps_to_phalguna(self):
    record = self._record(date(2026, 3, 15), "K11", "12")
    self.assertEqual(ekadashi_name(record, amanta=False), "Pāpamocanī Ekādaśī")

  def test_adhika_sukla_is_padmini_and_krsna_is_parama(self):
    sukla = self._record(date(2026, 5, 26), "S11", "A3", True)
    krsna = self._record(date(2026, 6, 11), "K11", "A3", True)
    self.assertEqual(ekadashi_name(sukla, amanta=True), "Padminī Ekādaśī")
    self.assertEqual(ekadashi_name(krsna, amanta=True), "Paramā Ekādaśī")

  def test_kshaya_dvadasi_sunrise_keeps_ekadashi_name(self):
    record = self._record(date(2026, 7, 11), "K12", "3")
    self.assertEqual(ekadashi_name(record, amanta=True), "Yoginī Ekādaśī")

  def test_ekadashi_name_drawn_only_in_teal_cells(self):
    from festival_rules import DayRecord
    ensure_pdf_fonts()
    location = load_location("Ujjain")
    civil = date(2026, 8, 9)
    record = DayRecord(civil, "K11", 1, 1, "4", False, 0.0)
    base_context = {
      "records_by_date": {
        civil: record
      },
      "festival_names_by_date": {},
      "eclipse_dates": set(),
      "eclipse_details_by_date": {},
      "masa_badges": {},
      "solar_by_date": {},
      "ekadashi": set(),
      "pradosham": set(),
      "sankashti": set(),
      "amanta": True,
    }
    teal_context = dict(base_context, ekadashi={civil})
    pdf = mock.Mock()
    pdf.stringWidth = lambda text, font, size: len(text) * size * 0.5
    with mock.patch("generate_monthly_calendar.day_details", return_value=([("K11", "11:05")], [], [])):
      draw_cell(pdf, 20.0, 500.0, 100.0, 75.0, 9, civil, location, teal_context, col=0)
    drawn = [c.args[2] for c in pdf.drawString.call_args_list]
    self.assertIn("Kāmikā Ekādaśī", drawn)

    plain_context = dict(base_context, ekadashi=set())
    pdf = mock.Mock()
    pdf.stringWidth = lambda text, font, size: len(text) * size * 0.5
    with mock.patch("generate_monthly_calendar.day_details", return_value=([("K11", "11:05")], [], [])):
      draw_cell(pdf, 20.0, 500.0, 100.0, 75.0, 9, civil, location, plain_context, col=0)
    drawn = [c.args[2] for c in pdf.drawString.call_args_list]
    self.assertNotIn("Kāmikā Ekādaśī", drawn)

  def test_shraddha_line_drawn_at_aparahna_tithi(self):
    from festival_rules import DayRecord
    ensure_pdf_fonts()
    location = load_location("Ujjain")
    civil = date(2026, 6, 26)
    record = DayRecord(civil, "S12", 1, 1, "3", False, 2461217.5)
    context = {
      "records_by_date": {
        civil: record
      },
      "festival_names_by_date": {},
      "eclipse_dates": set(),
      "eclipse_details_by_date": {},
      "masa_badges": {},
      "solar_by_date": {
        civil: (3, 1, True)
      },
      "ekadashi": set(),
      "shraddha_tithis": {
        civil: 7
      },
      "pradosham": set(),
      "sankashti": set(),
      "amanta": True,
    }
    pdf = mock.Mock()
    pdf.stringWidth = lambda text, font, size: len(text) * size * 0.5
    with mock.patch("generate_monthly_calendar.day_details", return_value=([("S12", "20:00")], [], [])):
      draw_cell(pdf, 20.0, 500.0, 100.0, 75.0, 26, civil, location, context, col=0)
    drawn = [c.args[2] for c in pdf.drawString.call_args_list]
    self.assertIn(" / [S7]", drawn)

  def test_parana_line_drawn_on_parana_day(self):
    from festival_rules import DayRecord, EkadashiParana
    ensure_pdf_fonts()
    location = load_location("Ujjain")
    civil = date(2026, 6, 26)
    record = DayRecord(civil, "S12", 1, 1, "3", False, 2461217.5)
    parana = EkadashiParana(date(2026, 6, 25), civil, 2461217.5, 2461217.5 + 4 / 60.0, "normal")
    context = {
      "records_by_date": {
        civil: record
      },
      "festival_names_by_date": {},
      "eclipse_dates": set(),
      "eclipse_details_by_date": {},
      "masa_badges": {},
      "solar_by_date": {},
      "ekadashi": set(),
      "ekadashi_parana": {
        civil: parana
      },
      "pradosham": set(),
      "sankashti": set(),
      "amanta": True,
    }
    pdf = mock.Mock()
    pdf.stringWidth = lambda text, font, size: len(text) * size * 0.5
    with mock.patch("generate_monthly_calendar.day_details", return_value=([("S12", "20:00")], [], [])), \
         mock.patch("generate_monthly_calendar.format_local_hm", side_effect=["05:47", "07:23"]):
      draw_cell(pdf, 20.0, 500.0, 100.0, 75.0, 26, civil, location, context, col=0)
    drawn = [c.args[2] for c in pdf.drawString.call_args_list]
    self.assertIn("Pāraṇā: 05:47 – 07:23", drawn)


class FestivalBarColorTests(unittest.TestCase):
  """Verify the correct color bars are drawn for each festival."""

  def _base_context(self, **overrides):
    context = {
      "records_by_date": {},
      "festival_names_by_date": {},
      "eclipse_dates": set(),
      "eclipse_details_by_date": {},
      "masa_badges": {},
      "solar_by_date": {},
      "ekadashi": set(),
      "pradosham": set(),
      "sankashti": set(),
      "amanta": True,
    }
    context.update(overrides)
    return context

  def _fill_colors(self, pdf):
    return [c.args[0] for c in pdf.setFillColor.call_args_list]

  def test_pradosham_bar_is_purple(self):
    from generate_monthly_calendar import PURPLE
    pdf = mock.Mock()
    civil = date(2026, 6, 11)
    context = self._base_context(pradosham={civil})
    draw_cell(pdf, 20.0, 500.0, 100.0, 75.0, 11, civil, load_location("Ujjain"), context, col=0)
    self.assertIn(PURPLE, self._fill_colors(pdf))

  def test_sankashti_bar_is_indigo(self):
    from generate_monthly_calendar import INDIGO
    pdf = mock.Mock()
    civil = date(2026, 6, 11)
    context = self._base_context(sankashti={civil})
    draw_cell(pdf, 20.0, 500.0, 100.0, 75.0, 11, civil, load_location("Ujjain"), context, col=0)
    self.assertIn(INDIGO, self._fill_colors(pdf))

  def test_ekadashi_bar_is_teal(self):
    from generate_monthly_calendar import TEAL
    pdf = mock.Mock()
    civil = date(2026, 6, 11)
    context = self._base_context(ekadashi={civil})
    draw_cell(pdf, 20.0, 500.0, 100.0, 75.0, 11, civil, load_location("Ujjain"), context, col=0)
    self.assertIn(TEAL, self._fill_colors(pdf))


class FooterLegendTests(unittest.TestCase):
  """Verify the footer legend includes all festival markers."""

  def test_footer_omits_parana_legend(self):
    from generate_monthly_calendar import draw_footer
    pdf = mock.Mock()
    draw_footer(pdf, load_location("Ujjain"), "citra", 1, 12)
    notes = " ".join(c.args[2] for c in pdf.drawString.call_args_list if len(c.args) >= 3)
    self.assertNotIn("Pāraṇā", notes)
    self.assertIn("śrāddha tithi (aparāhṇa)", notes)

  def test_footer_mentions_sankashti(self):
    from generate_monthly_calendar import draw_footer
    pdf = mock.Mock()
    location = load_location("Ujjain")
    draw_footer(pdf, location, "citra", 1, 12)
    drawn_text = [c.args[2] for c in pdf.drawString.call_args_list]
    footer_note = [t for t in drawn_text if "saṅkaṣṭahara" in t]
    self.assertEqual(len(footer_note), 1)
    self.assertIn("indigo: saṅkaṣṭahara caturthī", footer_note[0])

  def test_footer_mentions_pradosham(self):
    from generate_monthly_calendar import draw_footer
    pdf = mock.Mock()
    location = load_location("Ujjain")
    draw_footer(pdf, location, "citra", 1, 12)
    drawn_text = [c.args[2] for c in pdf.drawString.call_args_list]
    footer_note = [t for t in drawn_text if "pradoṣam" in t]
    self.assertEqual(len(footer_note), 1)
    self.assertIn("purple: pradoṣam", footer_note[0])

  def test_footer_uses_compact_marker_wording(self):
    from generate_monthly_calendar import draw_footer
    pdf = mock.Mock()
    location = load_location("Ujjain")
    draw_footer(pdf, location, "citra", 1, 12)
    drawn_text = [c.args[2] for c in pdf.drawString.call_args_list]
    footer_note = [t for t in drawn_text if "After 24:00" in t]
    self.assertEqual(len(footer_note), 1)
    self.assertIn("Green: māsa", footer_note[0])
    self.assertIn("brown [S/K]: śrāddha tithi (aparāhṇa)", footer_note[0])
    self.assertNotIn("Teal Pāraṇā", footer_note[0])


if __name__ == "__main__":
  unittest.main()
