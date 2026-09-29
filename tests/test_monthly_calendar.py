"""Regression tests for the lunar-year wall-grid panchanga PDF."""

from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

from datetime_helper import Date, gregorian_to_jd
from generate_monthly_calendar import (
  RULESET_VERSION,
  argument_parser,
  build_monthly_pdf,
  collect_context,
  day_details,
  default_monthly_output_path,
  draw_cell,
  draw_header,
  ekadashi_name,
  ensure_pdf_fonts,
  sun_moon_lines,
  tithi_name,
)
from generate_panchanga_calendar import (
  DEFAULT_FESTIVALS_PATH,
  _month_sequence as month_sequence,
  load_location,
  lunar_year_months,
)


class MonthSequenceTests(unittest.TestCase):

  def test_month_sequence_spans_year_boundary(self):
    months = month_sequence(2026, 11, 4)
    self.assertEqual(months, [(2026, 11), (2026, 12), (2027, 1), (2027, 2)])


class BuildPdfTests(unittest.TestCase):

  def test_generates_one_page_per_printed_month(self):
    months = lunar_year_months(2026, load_location("Helsinki"))
    self.assertEqual(len(months), 14)
    with TemporaryDirectory() as directory:
      output = Path(directory) / "calendar.pdf"
      with mock.patch("generate_monthly_calendar.find_local_eclipses", return_value=[]):
        build_monthly_pdf(load_location("Helsinki"), months, output)
      document = output.read_bytes()
    page_objects = re.findall(rb"/Type\s*/Page\b", document)
    self.assertEqual(len(page_objects), len(months))
    self.assertIn(RULESET_VERSION.encode("ascii"), document)

  def test_purnimanta_prints_the_same_months(self):
    # The span comes from amānta records; ``--month`` only changes display.
    location = load_location("Helsinki")
    months = lunar_year_months(2026, location)
    with TemporaryDirectory() as directory:
      output = Path(directory) / "calendar.pdf"
      with mock.patch("generate_monthly_calendar.find_local_eclipses", return_value=[]):
        build_monthly_pdf(location, months, output, month_system="purnimanta")
      document = output.read_bytes()
    self.assertEqual(len(re.findall(rb"/Type\s*/Page\b", document)), len(months))

  def test_pdf_metadata_contains_title(self):
    location = load_location("Ujjain")
    months = lunar_year_months(2026, location)
    with TemporaryDirectory() as directory:
      output = Path(directory) / "calendar.pdf"
      with mock.patch("generate_monthly_calendar.find_local_eclipses", return_value=[]):
        build_monthly_pdf(location, months, output)
      document = output.read_bytes()
    # Title/subject live in the uncompressed Info dict; page streams are flate-encoded.
    self.assertIn(b"Ujjain, IN Panchanga March 2026 to April 2027", document)
    self.assertIn(RULESET_VERSION.encode("ascii"), document)

  def test_default_output_path(self):
    location = load_location("Helsinki")
    path = default_monthly_output_path(location, lunar_year_months(2026, location))
    self.assertEqual(path.name, "helsinki-fi_panchanga_wall_2026-03_to_2027-04.pdf")

  def test_purnimanta_filename_suffix(self):
    location = load_location("Helsinki")
    months = lunar_year_months(2026, location)
    path = default_monthly_output_path(location, months, month_system="purnimanta")
    self.assertEqual(path.name, "helsinki-fi_panchanga_wall_2026-03_to_2027-04_purnimanta.pdf")

  def test_ayanamsa_filename_suffix(self):
    location = load_location("Helsinki")
    months = lunar_year_months(2026, location)
    path = default_monthly_output_path(location, months, coordinate_selection="raman")
    self.assertEqual(path.name, "helsinki-fi_panchanga_wall_2026-03_to_2027-04_raman.pdf")

  def test_tropical_filename_suffix(self):
    # lunar_year_months sets the global coordinate selection; restore it so a
    # tropical resolve here cannot leak into later date-computation tests.
    import panchanga
    self.addCleanup(panchanga.set_coordinate_selection, "citra")
    location = load_location("Helsinki")
    months = lunar_year_months(2026, location, "tropical")
    path = default_monthly_output_path(location, months, coordinate_selection="tropical")
    self.assertEqual(path.name, "helsinki-fi_panchanga_wall_2026-03_to_2027-03_tropical.pdf")


class CliTests(unittest.TestCase):

  def test_cli_defaults(self):
    parser = argument_parser()
    arguments = parser.parse_args(["--city", "Helsinki", "--start", "2026"])
    self.assertEqual(arguments.month, "amanta")
    self.assertEqual(arguments.ayanamsa, "citra")

  def test_cli_accepts_purnimanta(self):
    parser = argument_parser()
    arguments = parser.parse_args(["--city", "Helsinki", "--start", "2026", "--month", "purnimanta"])
    self.assertEqual(arguments.month, "purnimanta")

  def test_cli_accepts_ayanamsa(self):
    parser = argument_parser()
    arguments = parser.parse_args(["--city", "Helsinki", "--start", "2026", "--ayanamsa", "revati"])
    self.assertEqual(arguments.ayanamsa, "revati")


class DayDetailsTests(unittest.TestCase):

  def test_tithi_name_mapping(self):
    self.assertEqual(tithi_name(1), "Pratipadā")
    self.assertEqual(tithi_name(15), "Pūrṇimā")
    self.assertEqual(tithi_name(30), "Amāvāsyā")

  def test_day_details_returns_leap_tithi(self):
    location = load_location("Ujjain")
    # 2026-06-15 has a leap tithi (Amavasya + Pratipada)
    tithi_lines, _naks_lines, _yoga_names = day_details(location, Date(2026, 6, 15))
    self.assertEqual(len(tithi_lines), 2)
    self.assertEqual(tithi_lines[0][0], "K15")
    self.assertEqual(tithi_lines[1][0], "S1")

  def test_day_details_returns_leap_nakshatra(self):
    location = load_location("Ujjain")
    # 2026-06-12 has a leap nakshatra
    tithi_lines, naks_lines, _yoga_names = day_details(location, Date(2026, 6, 12))
    self.assertEqual(len(naks_lines), 2)

  def test_day_details_returns_skipped_yoga_names(self):
    location = load_location("Ujjain")
    # 2026-06-10: Ayushman ends 06:27, Saubhagya is entirely skipped within the day
    _tithi_lines, _naks_lines, yoga_names = day_details(location, Date(2026, 6, 10))
    self.assertEqual(yoga_names, ["Āyuṣmān", "Saubhāgya"])

  def test_day_details_computes_at_polar_day_and_night(self):
    # Regression (old contract): a polar day/night used to return None because
    # every sunrise-based quantity was undefined. The core sunrise() transit
    # fallback now anchors these days, so real end times render instead.
    location = load_location("Murmansk, RU")
    for day in (Date(2026, 6, 21), Date(2026, 12, 21)):
      with self.subTest(day=day):
        details = day_details(location, day)
        self.assertIsNotNone(details)
        tithi_lines, naks_lines, _yoga_names = details
        self.assertTrue(tithi_lines and naks_lines)
        rendered = f"{tithi_lines}{naks_lines}"
        self.assertNotIn("-59", rendered)  # no Swe failure sentinel

  def test_day_details_still_computes_at_polar_shoulder(self):
    # Murmansk does see a sunrise outside the polar day/night window.
    location = load_location("Murmansk, RU")
    tithi_lines, naks_lines, yoga_names = day_details(location, Date(2026, 3, 15))
    self.assertTrue(tithi_lines and naks_lines and yoga_names)


class SunMoonTests(unittest.TestCase):

  def test_sun_moon_lines_for_known_day(self):
    location = load_location("Ujjain")
    lines = sun_moon_lines(location, Date(2026, 6, 1))
    self.assertEqual(len(lines), 2)
    self.assertTrue(lines[0].startswith("Sun:"))
    self.assertTrue(lines[1].startswith("Moon:"))
    self.assertIn(" – ", lines[0])
    self.assertIn(" – ", lines[1])

  def test_sun_moon_lines_render_transit_anchors_at_polar_days(self):
    # Regression (old contract): the Sun line used to be omitted entirely at
    # polar locations. The sunrise()/sunset() transit fallback now supplies
    # anchors: solar-noon pair in polar night (day length 0), solar-midnight
    # pair in midnight sun (day length 24 h).
    location = load_location("Murmansk, RU")
    for day, expected_set_hour in ((Date(2026, 12, 21), 12), (Date(2026, 6, 21), 24)):
      with self.subTest(day=day):
        lines = sun_moon_lines(location, day)
        sun_lines = [line for line in lines if line.startswith("Sun:")]
        self.assertEqual(len(sun_lines), 1)
        match = re.search(r"Sun: (?:\(\d\d:\d\d –\) )?\d\d:\d\d – (\d\d):\d\d$", sun_lines[0])
        self.assertIsNotNone(match)
        self.assertEqual(int(match.group(1)), expected_set_hour)
        self.assertTrue(all("-59" not in line for line in lines))

  def test_sun_moon_lines_render_both_ends_at_polar_shoulder(self):
    # Regression (old contract): near the polar circle sunrise and sunset used
    # to go missing on different days (Norilsk, 20 May 2026, had a sunrise but
    # no sunset, rendered as ``--``). The transit fallback now supplies both,
    # so the full ``rise – set`` line renders.
    location = load_location("Norilsk, RU")
    lines = sun_moon_lines(location, Date(2026, 5, 20))
    sun_lines = [line for line in lines if line.startswith("Sun:")]
    self.assertEqual(len(sun_lines), 1)
    self.assertRegex(sun_lines[0], r"^Sun: \(\d\d:\d\d –\) \d\d:\d\d – \d\d:\d\d$")
    self.assertTrue(all("-59" not in line for line in lines))

  def test_sun_moon_lines_render_the_out_of_band_sunset(self):
    # Live case at extreme latitude (82.5N, 62.3W, UTC-5): the sun first dips
    # below the horizon late on 3 Sep 1500, so that day's sunset sits past the
    # band check and prints --.
    from generate_panchanga_calendar import resolve_location
    lines = sun_moon_lines(resolve_location(place="82.5,-62.3,-5"), Date(1500, 9, 3))
    self.assertEqual([line for line in lines if line.startswith("Sun:")], ["Sun: (21:49 –) 23:22 – --"])

  def test_sun_moon_lines_always_render_a_sun_line(self):
    # sunrise() and sunset() always return an anchor (the transit fallback),
    # so the Sun line is never dropped, even on a polar day or night.
    lines = sun_moon_lines(load_location("Murmansk, RU"), Date(2026, 12, 21))
    self.assertEqual(len([line for line in lines if line.startswith("Sun:")]), 1)


class DstClockTests(unittest.TestCase):
  """A Hindu-day tail crossing a DST change reads the clock at the event.

  Cell times are baked as hours past the row's midnight with the one UTC
  offset of that civil date (its local-noon offset). The tail must re-read
  the offset in force when the event happened. Helsinki 2026: DST starts
  29 Mar 03:00 and ends 25 Oct 04:00 (01:00 UT at both changes).
  """

  def test_tithi_end_after_dst_start(self):
    tithi_lines, _naks_lines, _yoga_names = day_details(load_location("Helsinki"), Date(2026, 3, 28))
    # S11 ends 02:17 UT on the 29th, after the change: the stale +2 read
    # 28:17, the clock says 29:17.
    self.assertEqual(tithi_lines[0], ("S11", "29:17"))

  def test_moonset_after_dst_start(self):
    lines = sun_moon_lines(load_location("Helsinki"), Date(2026, 3, 28))
    moon_line = [line for line in lines if line.startswith("Moon:")][0]
    # Was 29:15 with the stale +2; after the change the clock reads 30:15.
    self.assertTrue(moon_line.endswith("– 30:15"))

  def test_moonset_after_dst_end(self):
    lines = sun_moon_lines(load_location("Helsinki"), Date(2026, 10, 24))
    moon_line = [line for line in lines if line.startswith("Moon:")][0]
    # Was 31:05 with the stale +3; after the change the clock reads 30:05.
    self.assertTrue(moon_line.endswith("– 30:05"))


class CellDrawTests(unittest.TestCase):

  def test_solar_day_line_is_drawn(self):
    ensure_pdf_fonts()
    pdf = mock.Mock()
    pdf.stringWidth = lambda text, font, size: len(text) * size * 0.5
    from festival_rules import DayRecord
    context = {
      "records_by_date": {
        Date(2026, 6, 16): DayRecord(Date(2026, 6, 16), "S2", 1, 1, "5", False, 0.0)
      },
      "festival_names_by_date": {},
      "eclipse_dates": set(),
      "eclipse_details_by_date": {},
      "masa_badges": {},
      "solar_by_date": {
        Date(2026, 6, 16): (3, 1, True)
      },
      "shraddha_tithis": {
        Date(2026, 6, 16): 7
      },
      "ekadashi": set(),
      "pradosham": set(),
      "sankashti": set(),
    }
    draw_cell(pdf, 20.0, 500.0, 100.0, 75.0, 16, Date(2026, 6, 16), load_location("Ujjain"), context, col=0)
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
        Date(2026, 6, 15): DayRecord(Date(2026, 6, 15), "K15", 1, 1, "5", False, 0.0)
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
      draw_cell(pdf, 20.0, 500.0, 100.0, 75.0, 15, Date(2026, 6, 15), load_location("Ujjain"), context, col=0)
    drawn_text = [c.args[2] for c in pdf.drawString.call_args_list]
    self.assertIn("Śrāvaṇa K15 08:24", drawn_text)
    self.assertIn("Śrāvaṇa S1 28:31", drawn_text)

  def test_day_details_polar_day_yields_lines_not_none(self):
    # day_details never returns None: panchanga.sunrise() anchors every day,
    # so draw_cell can unpack its 3-tuple directly. At a polar winter day the
    # lines still carry real end times, never sentinel garbage.
    ensure_pdf_fonts()
    pdf = mock.Mock()
    from festival_rules import DayRecord
    context = {
      "records_by_date": {
        Date(2026, 6, 21): DayRecord(Date(2026, 6, 21), "K7", 1, 1, "5", False, 0.0)
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
    details = day_details(load_location("Murmansk, RU"), Date(2026, 6, 21))
    self.assertTrue(all(part is not None for part in details))
    draw_cell(pdf, 20.0, 500.0, 100.0, 75.0, 21, Date(2026, 6, 21), load_location("Murmansk, RU"), context, col=0)
    drawn_text = [c.args[2] for c in pdf.drawString.call_args_list]
    self.assertFalse([text for text in drawn_text if "-59" in text])

  def test_masa_start_fill_is_drawn(self):
    ensure_pdf_fonts()
    pdf = mock.Mock()
    from festival_rules import DayRecord
    context = {
      "records_by_date": {
        Date(2026, 6, 16): DayRecord(Date(2026, 6, 16), "S2", 1, 1, "5", False, 0.0)
      },
      "festival_names_by_date": {},
      "eclipse_dates": set(),
      "eclipse_details_by_date": {},
      "masa_badges": {
        Date(2026, 6, 16): "5"
      },
      "solar_by_date": {},
      "ekadashi": set(),
      "pradosham": set(),
      "sankashti": set(),
    }
    draw_cell(pdf, 20.0, 500.0, 100.0, 75.0, 16, Date(2026, 6, 16), load_location("Ujjain"), context, col=0)
    fill_colors = [c.args[0] for c in pdf.setFillColor.call_args_list]
    from generate_panchanga_calendar import MASA_START_ROW
    self.assertIn(MASA_START_ROW, fill_colors)


class VarjyamTests(unittest.TestCase):

  def test_varjyam_lines_two_windows_on_nakshatra_change_day(self):
    from generate_monthly_calendar import varjyam_lines
    location = load_location("Ujjain")
    lines = varjyam_lines(location, Date(2026, 6, 14))
    self.assertEqual(len(lines), 2)
    for line in lines:
      self.assertTrue(line.startswith("Varjyam: "))

  def test_varjyam_line_is_drawn_in_cell(self):
    ensure_pdf_fonts()
    pdf = mock.Mock()
    from festival_rules import DayRecord
    civil = Date(2026, 6, 14)
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
    jd = gregorian_to_jd(civil)
    ist = lambda hours: jd + (hours - 5.5) / 24
    with mock.patch("generate_monthly_calendar.panchanga.varjyam", return_value=[[ist(15.4367), ist(17.2467)]]):
      draw_cell(pdf, 20.0, 500.0, 100.0, 75.0, 14, civil, load_location("Ujjain"), context, col=0)
    drawn_text = [c.args[2] for c in pdf.drawString.call_args_list]
    self.assertIn("Varjyam: 15:26 – 17:15", drawn_text)


class RahuKalaTableTests(unittest.TestCase):

  def test_table_lines_cover_all_weekdays_sunday_first(self):
    from generate_monthly_calendar import rahu_kala_table_lines
    lines = rahu_kala_table_lines(load_location("Ujjain"), 2026, 6)
    self.assertEqual([line.split()[0] for line in lines], ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"])
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
    civil = Date(2026, 6, 15)
    records_by_date = {civil: DayRecord(civil, "K15", 5, 7, "3", False, 0.0)}
    label = year_label_for_month(2026, 6, records_by_date)
    self.assertEqual(label, "Parābhava 1948, Siddhārthī 2083, Kali (elapsed) 5127")

  def test_year_label_is_none_without_record(self):
    from generate_monthly_calendar import year_label_for_month
    self.assertIsNone(year_label_for_month(2026, 6, {}))

  def test_year_label_uses_underlying_month(self):
    from festival_rules import DayRecord
    from generate_monthly_calendar import year_label_for_month
    import panchanga
    # The record carries the canonical amānta month 1 (Caitra); the label
    # must use it, whatever the display system would show.
    civil = Date(2026, 4, 15)
    records_by_date = {civil: DayRecord(civil, "K20", 1, 1, "1", False, 0.0)}
    with mock.patch.object(panchanga, "elapsed_year", return_value=(5127, 1948, 2083)) as mock_elapsed, \
         mock.patch.object(panchanga, "samvatsara", return_value=1) as mock_samvatsara, \
         mock.patch.object(panchanga, "samvatsara_north_modern", return_value=1) as mock_north:
      year_label_for_month(2026, 4, records_by_date)
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
    self.assertIn("DST starts", dst_labels.get(Date(2026, 3, 29), []))

  def test_collect_context_includes_dst_end(self):
    from generate_monthly_calendar import collect_context
    location = load_location("Helsinki")
    months = [(2026, 10), (2026, 11)]
    ctx = collect_context(months, location, DEFAULT_FESTIVALS_PATH, amanta=True)
    dst_labels = ctx["dst_labels_by_date"]
    # Oct 25, 2026 is DST end for Helsinki
    self.assertIn("DST ends", dst_labels.get(Date(2026, 10, 25), []))

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
    civil = Date(2026, 1, 4)
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
    civil = Date(2025, 12, 28)
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
    civil = Date(2027, 1, 3)
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
    record = self._record(Date(2026, 3, 29), "S11", "1")
    self.assertEqual(ekadashi_name(record, amanta=True), "Kāmadā Ekādaśī")

  def test_amanta_krsna_names_from_same_month_entry(self):
    record = self._record(Date(2026, 4, 13), "K11", "1")
    self.assertEqual(ekadashi_name(record, amanta=True), "Varūthinī Ekādaśī")

  def test_purnimanta_krsna_shifts_back_one_month(self):
    record = self._record(Date(2026, 4, 13), "K11", "1")
    self.assertEqual(ekadashi_name(record, amanta=False), "Varūthinī Ekādaśī")

  def test_year_boundary_krsna_wraps_to_phalguna(self):
    record = self._record(Date(2026, 3, 15), "K11", "12")
    self.assertEqual(ekadashi_name(record, amanta=False), "Pāpamocanī Ekādaśī")

  def test_adhika_sukla_is_padmini_and_krsna_is_parama(self):
    sukla = self._record(Date(2026, 5, 26), "S11", "A3", True)
    krsna = self._record(Date(2026, 6, 11), "K11", "A3", True)
    self.assertEqual(ekadashi_name(sukla, amanta=True), "Padminī Ekādaśī")
    self.assertEqual(ekadashi_name(krsna, amanta=True), "Paramā Ekādaśī")

  def test_kshaya_dvadasi_sunrise_keeps_ekadashi_name(self):
    record = self._record(Date(2026, 7, 11), "K12", "3")
    self.assertEqual(ekadashi_name(record, amanta=True), "Yoginī Ekādaśī")

  def test_ekadashi_name_drawn_only_in_teal_cells(self):
    from festival_rules import DayRecord
    ensure_pdf_fonts()
    location = load_location("Ujjain")
    civil = Date(2026, 8, 9)
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
    civil = Date(2026, 6, 26)
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
    civil = Date(2026, 6, 26)
    record = DayRecord(civil, "S12", 1, 1, "3", False, 2461217.5)
    parana = EkadashiParana(Date(2026, 6, 25), civil, 2461217.5, 2461217.5 + 4 / 60.0, "normal")
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
    parana_start, parana_end = parana.parana_jd, parana.parana_end_jd

    def fake_local_hm(jd, timezone_name, **kwargs):
      # The parana window is the only call whose result is asserted; the
      # sun/moon/varjyam lines format through the same helper.
      if jd == parana_start:
        return "05:47"
      if jd == parana_end:
        return "07:23"
      return "00:00"

    with mock.patch("generate_monthly_calendar.day_details", return_value=([("S12", "20:00")], [], [])), \
         mock.patch("generate_monthly_calendar.format_local_hm", side_effect=fake_local_hm):
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
    civil = Date(2026, 6, 11)
    context = self._base_context(pradosham={civil})
    draw_cell(pdf, 20.0, 500.0, 100.0, 75.0, 11, civil, load_location("Ujjain"), context, col=0)
    self.assertIn(PURPLE, self._fill_colors(pdf))

  def test_sankashti_bar_is_indigo(self):
    from generate_monthly_calendar import INDIGO
    pdf = mock.Mock()
    civil = Date(2026, 6, 11)
    context = self._base_context(sankashti={civil})
    draw_cell(pdf, 20.0, 500.0, 100.0, 75.0, 11, civil, load_location("Ujjain"), context, col=0)
    self.assertIn(INDIGO, self._fill_colors(pdf))

  def test_ekadashi_bar_is_teal(self):
    from generate_monthly_calendar import TEAL
    pdf = mock.Mock()
    civil = Date(2026, 6, 11)
    context = self._base_context(ekadashi={civil})
    draw_cell(pdf, 20.0, 500.0, 100.0, 75.0, 11, civil, load_location("Ujjain"), context, col=0)
    self.assertIn(TEAL, self._fill_colors(pdf))


class FooterLegendTests(unittest.TestCase):
  """Verify the footer legend includes all festival markers."""

  def test_footer_omits_parana_legend(self):
    from generate_monthly_calendar import draw_footer
    pdf = mock.Mock()
    draw_footer(pdf, 1, 12)
    notes = " ".join(c.args[2] for c in pdf.drawString.call_args_list if len(c.args) >= 3)
    self.assertNotIn("Pāraṇā", notes)
    self.assertIn("śrāddha tithi (aparāhṇa)", notes)

  def test_footer_mentions_sankashti(self):
    from generate_monthly_calendar import draw_footer
    pdf = mock.Mock()
    draw_footer(pdf, 1, 12)
    drawn_text = [c.args[2] for c in pdf.drawString.call_args_list]
    footer_note = [t for t in drawn_text if "saṅkaṣṭahara" in t]
    self.assertEqual(len(footer_note), 1)
    self.assertIn("indigo: saṅkaṣṭahara caturthī", footer_note[0])

  def test_footer_mentions_pradosham(self):
    from generate_monthly_calendar import draw_footer
    pdf = mock.Mock()
    draw_footer(pdf, 1, 12)
    drawn_text = [c.args[2] for c in pdf.drawString.call_args_list]
    footer_note = [t for t in drawn_text if "pradoṣam" in t]
    self.assertEqual(len(footer_note), 1)
    self.assertIn("purple: pradoṣam", footer_note[0])

  def test_footer_uses_compact_marker_wording(self):
    from generate_monthly_calendar import draw_footer
    pdf = mock.Mock()
    draw_footer(pdf, 1, 12)
    drawn_text = [c.args[2] for c in pdf.drawString.call_args_list]
    time_note = [t for t in drawn_text if "After 24:00" in t]
    mark_note = [t for t in drawn_text if "Green: māsa" in t]
    self.assertEqual(len(time_note), 1)
    self.assertEqual(len(mark_note), 1)
    self.assertIn("00:xx only if", time_note[0])
    self.assertIn("polar", time_note[0])
    self.assertIn("brown [S/K]: śrāddha tithi (aparāhṇa)", mark_note[0])
    self.assertNotIn("Teal Pāraṇā", mark_note[0])


if __name__ == "__main__":
  unittest.main()
