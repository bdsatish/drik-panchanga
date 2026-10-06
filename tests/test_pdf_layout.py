"""Regression tests for the generated one-page calendar layout."""

import calendar
from io import BytesIO
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

from reportlab.pdfgen.canvas import Canvas

import panchanga
from datetime_helper import Date, dst_transitions, format_utc_offset
from festival_rules import DayRecord
from generate_panchanga_calendar import (
  ACCENT,
  ADHIKA_INK,
  DEFAULT_FESTIVALS_PATH,
  EKADASHI_MARK,
  FOOTER_FESTIVAL_SLOTS,
  KRSNA_INK,
  MASA_START_INK,
  PDF_FONT_BOLD,
  PDF_FONT_BOLD_ITALIC,
  PDF_FONT_TTC,
  RULESET_VERSION,
  SANKRANTI_INK,
  TITHI_COLUMN_RATIO,
  _month_sequence,
  argument_parser,
  build_pdf,
  calendar_year_label,
  daily_records,
  daily_records_between,
  default_output_path,
  display_masa,
  draw_month,
  draw_page_footer,
  draw_page_header,
  draw_eclipse_mark,
  draw_sankranti_mark,
  draw_solar_day_mark,
  draw_tithi_underline,
  ensure_pdf_fonts,
  fitted_font_size,
  kali_ahargana_range,
  load_location,
  lunar_year_months,
  month_header_label,
  record_span,
  solar_dates_by_date,
  tithi_display_parts,
  tithi_font,
  tithi_ink,
)


class PdfLayoutTests(unittest.TestCase):

  def test_record_span_pads_the_printed_months(self):
    # 32 days lead in for the solar day count (a solar month can be 32
    # sunrises); one day out catches a pre-sunrise eclipse on the last day.
    months = [(2026, 3), (2026, 4)]
    first, last = record_span(months)
    self.assertEqual(first, Date(2026, 1, 28))
    self.assertEqual(last, Date(2026, 5, 1))

  def test_lunar_year_span_is_whole_months_with_a_day_pad(self):
    # The resolver picks the months; the pad is what the builders read.
    months = lunar_year_months(2026, load_location("Ujjain"))
    self.assertEqual(months[0], (2026, 3))
    self.assertEqual(months[-1], (2027, 4))
    self.assertEqual(len(months), 14)
    first, last = record_span(months)
    self.assertLess(first, Date(2026, 3, 1))
    self.assertGreater(last, Date(2027, 4, 30))

  def test_daily_records_between_matches_the_month_form(self):
    location = load_location("Bengaluru")
    months = [(2026, 1), (2026, 2)]
    from_date = Date(2026, 1, 1)
    to_date = Date(2026, 2, 28)
    self.assertEqual([r.civil_date for r in daily_records(months, location)],
                     [r.civil_date for r in daily_records_between(from_date, to_date, location)])

  def test_month_header_shows_the_full_year_before_1000_ce(self):
    # ``str(year)[2:]`` printed "Mar '" for year 50 and "Mar '00" for -500.
    cases = {2026: "Mar '26", 1000: "Mar '00", 999: "Mar 999", 50: "Mar 50", 0: "Mar 0", -500: "Mar -500"}
    for year, label in cases.items():
      with self.subTest(year=year):
        self.assertEqual(month_header_label(year, 3), label)

  def test_generated_calendar_has_exactly_one_page(self):
    import generate_panchanga_calendar as calendar_module

    with TemporaryDirectory() as directory:
      output = Path(directory) / "calendar.pdf"
      with mock.patch("generate_panchanga_calendar.find_local_eclipses", return_value=[
        ("Lunar", "Partial", 2461103.0419131187),
      ]), mock.patch("generate_panchanga_calendar.draw_page_footer", wraps=calendar_module.draw_page_footer) as footer:
        build_pdf(load_location("Helsinki"), _month_sequence(2026, 6, 3), output)
      document = output.read_bytes()

    page_objects = re.findall(rb"/Type\s*/Page\b", document)
    self.assertEqual(len(page_objects), 1)
    self.assertIn(RULESET_VERSION.encode("ascii"), document)
    self.assertEqual(footer.call_count, 1)
    self.assertIn("Eclipses:", footer.call_args.kwargs["eclipse_line"])
    self.assertNotIn(b"/BaseFont /Helvetica", document)
    self.assertIn(b"IndUni-H", document)

  def test_eclipses_before_sunrise_follow_the_printed_hindu_days(self):
    import generate_panchanga_calendar as calendar_module
    from datetime_helper import Date as CivilDate
    from datetime_helper import gregorian_to_jd, utc_offset_hours

    def _wall_jd(year, month, day, hour, timezone_name="Europe/Helsinki"):
      civil = CivilDate(year, month, day)
      return gregorian_to_jd(civil) + (hour - utc_offset_hours(timezone_name, civil)) / 24

    helsinki_tz = "Europe/Helsinki"
    # Printed span is Jun 2026 - Jul 2027; both maxima are at 02:00, before sunrise.
    before_first_day = _wall_jd(2026, 6, 1, 2, helsinki_tz)
    after_last_day = _wall_jd(2027, 8, 1, 2, helsinki_tz)
    with TemporaryDirectory() as directory:
      with mock.patch("generate_panchanga_calendar.find_local_eclipses",
                      return_value=[("Lunar", "Partial", before_first_day), ("Lunar", "Total", after_last_day)]), \
           mock.patch("generate_panchanga_calendar.draw_page_footer",
                      wraps=calendar_module.draw_page_footer) as footer:
        build_pdf(load_location("Helsinki"), _month_sequence(2026, 6, 14), Path(directory) / "calendar.pdf")
    eclipse_line = footer.call_args.kwargs["eclipse_line"]
    self.assertIn("Lunar Jul 31 (Total) maximum phase at 26:00", eclipse_line)
    self.assertNotIn("May 31", eclipse_line)
    self.assertNotIn("Partial", eclipse_line)

  def test_cli_defaults_festivals_path(self):
    parser = argument_parser()
    arguments = parser.parse_args(["--city", "Helsinki", "--year", "2026"])
    self.assertFalse(hasattr(arguments, "festival_policy"))
    self.assertEqual(arguments.festivals, DEFAULT_FESTIVALS_PATH)

  def test_default_output_path_suffixes(self):
    location = load_location("Helsinki")
    self.assertEqual(default_output_path(location, lunar_year_months(2026, location)).name,
                     "helsinki-fi_panchanga_2026-03_to_2027-04.pdf")
    months = lunar_year_months(2026, location)
    self.assertEqual(default_output_path(location, months, month_system="purnimanta").name,
                     "helsinki-fi_panchanga_2026-03_to_2027-04_purnimanta.pdf")
    self.assertEqual(default_output_path(location, months, coordinate_selection="raman").name,
                     "helsinki-fi_panchanga_2026-03_to_2027-04_raman.pdf")
    tropical_months = lunar_year_months(2026, location, "tropical")
    self.assertTrue(default_output_path(location, tropical_months, coordinate_selection="tropical").name
                    .startswith("helsinki-fi_panchanga_"))

  def test_tropical_resolver_restores_the_caller_mode(self):
    # The ICS feed and both PDF builders resolve the lunar year first; a
    # tropical request must not leave a sidereal process tropical.
    panchanga.set_coordinate_selection("raman")
    try:
      lunar_year_months(2026, load_location("Helsinki"), "tropical")
      self.assertEqual((panchanga.chosen_ayanamsa, panchanga.coordinate_flag), ("raman", panchanga.swe.FLG_SIDEREAL))
    finally:
      panchanga.set_coordinate_selection("citra")

  def test_cli_accepts_month_system_and_ayanamsa(self):
    parser = argument_parser()
    arguments = parser.parse_args(["--city", "Helsinki", "--year", "2026", "--month", "purnimanta"])
    self.assertEqual(arguments.month, "purnimanta")
    arguments = parser.parse_args(["--city", "Helsinki", "--year", "2026", "--ayanamsa", "revati"])
    self.assertEqual(arguments.ayanamsa, "revati")
    arguments = parser.parse_args(["--city", "Helsinki", "--year", "2026", "--ayanamsa", "tropical"])
    self.assertEqual(arguments.ayanamsa, "tropical")

  def test_cli_rejects_a_start_month(self):
    # Old scripts must fail loudly, not read 2026-03 as the year 2026.
    import sys
    from generate_panchanga_calendar import main
    with mock.patch.object(sys, "stderr", mock.Mock()), self.assertRaises(SystemExit):
      main(["--city", "Helsinki", "--year", "2026-03"])

  def test_parse_coordinate_selection_accepts_sidereal_and_tropical_modes(self):
    from generate_panchanga_calendar import (
      ayanamsa_label,
      coordinate_selection_label,
      parse_coordinate_selection,
    )
    self.assertEqual(parse_coordinate_selection("rohini"), "rohini")
    self.assertEqual(parse_coordinate_selection("rohini-paksha"), "rohini")
    self.assertEqual(parse_coordinate_selection("pushya"), "pushya")
    self.assertEqual(parse_coordinate_selection("true_mula"), "mula")
    self.assertEqual(parse_coordinate_selection("tropical"), "tropical")
    self.assertEqual(parse_coordinate_selection("sayana"), "tropical")
    self.assertEqual(parse_coordinate_selection("kp"), "krishnamurti")
    self.assertEqual(parse_coordinate_selection(None), "citra")
    self.assertEqual(ayanamsa_label("citra"), "Chitra-paksha")
    self.assertEqual(ayanamsa_label("revati"), "Revati-paksha")
    self.assertEqual(ayanamsa_label("rohini"), "Rohini-paksha")
    self.assertEqual(ayanamsa_label("pushya"), "Pushya-paksha")
    self.assertEqual(ayanamsa_label("mula"), "Mula-paksha")
    self.assertEqual(coordinate_selection_label("tropical"), "Tropical (Sāyana)")
    self.assertIsNone(parse_coordinate_selection("lahiri"))

  def test_purnimanta_header_uses_single_daily_records_pass(self):
    import generate_panchanga_calendar as calendar_module

    with TemporaryDirectory() as directory:
      output = Path(directory) / "calendar.pdf"
      with mock.patch("generate_panchanga_calendar.find_local_eclipses", return_value=[]), \
              mock.patch(
                  "generate_panchanga_calendar.daily_records_between",
                  wraps=calendar_module.daily_records_between) as records_mock:
        build_pdf(load_location("Bengaluru"), _month_sequence(2023, 3, 14), output, month_system="purnimanta")
      document = output.read_bytes()
    self.assertEqual(records_mock.call_count, 1)
    # Subject is uncompressed in the Info dict; page content streams are flate-encoded.
    self.assertIn(b"purnimanta masa", document)
    self.assertNotIn(b"and amanta masa", document)

  def test_calendar_year_label(self):
    # An adhika record shows the samvatsara conventions of both calendars.
    records = [
      DayRecord(Date(2026, 8, 15), "S1", 1, 1, "A4", True, 0.0),
    ]
    self.assertEqual(calendar_year_label(records),
                     "1948 Par\u0101bhava | 2083 Siddh\u0101rth\u012b | 5127 Kali (elapsed)")

  def test_calendar_year_label_uses_underlying_month(self):
    # The record carries the canonical am\u0101nta month 1 (Caitra); the label
    # uses it whatever the display system would show.
    records = [
      DayRecord(Date(2026, 4, 15), "K20", 1, 1, "1", False, 0.0),
    ]
    with mock.patch("generate_panchanga_calendar.panchanga") as mock_panchanga, \
         mock.patch("generate_panchanga_calendar.gregorian_to_jd", return_value=2450000.0):
      mock_panchanga.elapsed_year.return_value = (5127, 1948, 2083)
      mock_panchanga.samvatsara.return_value = 1
      mock_panchanga.samvatsara_north_modern.return_value = 1
      calendar_year_label(records)
      mock_panchanga.elapsed_year.assert_called_with(2450000.0, 1)
      mock_panchanga.samvatsara.assert_called_with(2450000.0, 1)
      mock_panchanga.samvatsara_north_modern.assert_called_with(2450000.0, 1)

  def test_pdf_subtitle_has_kali_ahargana_range(self):
    months = list(_month_sequence(2026, 6, 14))
    self.assertEqual(kali_ahargana_range(months), (1872727, 1873152))

    pdf = mock.Mock()
    pdf.stringWidth.return_value = 60.0
    with mock.patch("generate_panchanga_calendar.fitted_font_size", return_value=7.5):
      draw_page_header(pdf, load_location("Helsinki"), months, RULESET_VERSION,
                       kali_ahargana=kali_ahargana_range(months))

    subtitle = pdf.drawString.call_args_list[1].args[2]
    self.assertNotIn("Equal nakshatras", subtitle)
    self.assertTrue(subtitle.endswith("Kali Ahargana: 1872727 - 1873152"))

  def test_long_labels_are_fitted_without_overflow(self):
    ensure_pdf_fonts()
    pdf = Canvas(BytesIO())
    text = ("A Particularly Long Location Name Panchanga: "
            "September 2026 - September 2027")
    available_width = 300
    size = fitted_font_size(pdf, text, PDF_FONT_BOLD, 11, 5, available_width, "test title")
    self.assertLessEqual(pdf.stringWidth(text, PDF_FONT_BOLD, size), available_width + 0.01)

  def test_footer_accepts_full_slot_count(self):
    ensure_pdf_fonts()
    pdf = Canvas(BytesIO())
    entries = [(index, "Jan 01", f"Festival {index}") for index in range(1, FOOTER_FESTIVAL_SLOTS + 1)]
    draw_page_footer(pdf, entries)

  def test_footer_overflow_names_festivals_and_cfg(self):
    ensure_pdf_fonts()
    pdf = Canvas(BytesIO())
    entries = [(index, "Jan 01", f"Festival {index}") for index in range(1, FOOTER_FESTIVAL_SLOTS + 2)]
    with self.assertRaisesRegex(RuntimeError, "Too many enabled festivals.*Festival 1.*festivals.cfg"):
      draw_page_footer(pdf, entries)

  def test_footer_key_lines_use_iast_names(self):
    from generate_panchanga_calendar import (
      masa_key_line,
      nakshatra_key_line,
      sankranti_key_line,
      timing_key_line,
      tithi_key_line,
      yoga_key_line,
    )
    self.assertIn("After 24:00", timing_key_line())
    self.assertIn("00:xx only if", timing_key_line())
    self.assertIn("polar", timing_key_line())
    self.assertTrue(tithi_key_line().startswith("T:"))
    self.assertIn("teal Ekadashi", tithi_key_line())
    self.assertIn("purple Pradosham (Mon/Sat)", tithi_key_line())
    self.assertIn("indigo Sankashtahara (Tue)", tithi_key_line())
    self.assertIn("purple Pradosham, indigo Sankashtahara Chaturthi", tithi_key_line("all"))
    self.assertTrue(nakshatra_key_line().startswith("N:"))
    self.assertTrue(yoga_key_line().startswith("Y:"))
    self.assertIn("Vaiśākha", masa_key_line())
    self.assertIn("amānta or pūrṇimānta", masa_key_line())
    self.assertIn("Meṣa", sankranti_key_line())
    self.assertIn("1 Meṣa", sankranti_key_line())
    self.assertIn("10 Makara", sankranti_key_line())
    self.assertIn("rolling solar-day count resets", sankranti_key_line())
    self.assertIn("7, 14, 21, and 28", sankranti_key_line())
    self.assertIn("Aśvinī", nakshatra_key_line())
    self.assertIn("Viṣkambha", yoga_key_line())
    self.assertEqual(PDF_FONT_TTC.name, "IndUni-H.ttc")
    self.assertTrue(PDF_FONT_TTC.is_file())
    ensure_pdf_fonts()
    self.assertEqual(tithi_font(True), PDF_FONT_BOLD)


class TithiDisplayTests(unittest.TestCase):

  def test_sukla_and_krsna_drop_letters(self):
    self.assertEqual(tithi_display_parts("S1"), ("01", True))
    self.assertEqual(tithi_display_parts("S15"), ("15", True))
    self.assertEqual(tithi_display_parts("K1"), ("01", False))
    self.assertEqual(tithi_display_parts("K11"), ("11", False))

  def test_ink_uses_paksha_unless_masa_start(self):
    self.assertEqual(tithi_ink(True), ACCENT)
    self.assertEqual(tithi_ink(False), KRSNA_INK)
    self.assertEqual(tithi_ink(False, is_masa_start=True), MASA_START_INK)
    self.assertEqual(tithi_ink(True, is_masa_start=True, is_adhika=True), ADHIKA_INK)

  def test_font_uses_italic_for_krishna(self):
    ensure_pdf_fonts()
    self.assertEqual(tithi_font(True), PDF_FONT_BOLD)
    self.assertEqual(tithi_font(False), PDF_FONT_BOLD_ITALIC)


class MasaBadgeTests(unittest.TestCase):
  """T-cell badge: adhika keeps its ``A`` and never overruns the cell."""

  MONTH_WIDTH = (842.0 - 2 * 18 - 24) / 14

  def draw_badge(self, badge, is_adhika):
    """Draw one badge-bearing day and return ``(badge_text, font_size)``."""
    ensure_pdf_fonts()
    pdf = Canvas(BytesIO())
    civil = Date(2026, 5, 17)
    record = DayRecord(civil, "S1", 5, 7, badge, is_adhika, 0.0)
    drawn = []
    active_size = []
    original_set_font = pdf.setFont

    def spy_set_font(name, size, *rest):
      del active_size[:]
      active_size.append(size)
      return original_set_font(name, size, *rest)

    pdf.setFont = spy_set_font
    pdf.drawRightString = lambda x, y, text: drawn.append((text, active_size[-1]))
    draw_month(pdf, 2026, 5, {civil: record}, {civil: badge}, {}, set(), set(), {civil: (2, 10, False)}, 40.0, 500.0,
               self.MONTH_WIDTH)
    return drawn[-1]

  def test_adhika_badge_keeps_its_prefix(self):
    self.assertEqual(self.draw_badge("A3", True)[0], "A3")
    self.assertEqual(self.draw_badge("3", False)[0], "3")

  def test_wide_badge_shrinks_instead_of_overrunning_the_tithi(self):
    _plain, plain_size = self.draw_badge("3", False)
    wide_text, wide_size = self.draw_badge("A12", True)
    self.assertEqual(wide_text, "A12")
    self.assertLess(wide_size, plain_size)
    cell_width = self.MONTH_WIDTH * TITHI_COLUMN_RATIO
    tithi_width = Canvas(BytesIO()).stringWidth("01", tithi_font(True), 7.4)
    badge_width = Canvas(BytesIO()).stringWidth(wide_text, PDF_FONT_BOLD, wide_size)
    self.assertLessEqual(3.0 + tithi_width + badge_width, cell_width - 1.0)


class SpecialWeekdayTests(unittest.TestCase):
  """Weekday-special split: Pradosham (Mon/Sat), Sankashtahara (Tue)."""

  def test_special_weekday_dates(self):
    from generate_panchanga_calendar import special_weekday_dates
    monday = Date(2026, 1, 5)
    tuesday = Date(2026, 1, 6)
    friday = Date(2026, 1, 16)
    saturday = Date(2026, 1, 10)
    self.assertEqual(monday.weekday(), 0)
    self.assertEqual(tuesday.weekday(), 1)
    self.assertEqual(friday.weekday(), 4)
    self.assertEqual(saturday.weekday(), 5)
    pradosham, sankashti = special_weekday_dates({monday, friday, saturday}, {monday, tuesday})
    self.assertEqual(pradosham, {monday, saturday})
    self.assertEqual(sankashti, {tuesday})

  def test_require_recurring(self):
    from generate_panchanga_calendar import require_recurring
    self.assertEqual(require_recurring(None), "specials")
    self.assertEqual(require_recurring("ALL"), "all")
    with self.assertRaises(ValueError):
      require_recurring("everything")


class RecurringUnderlineTests(unittest.TestCase):
  """Annual T-cell underlines use Ekadashi/Pradosham/Sankashtahara Chaturthi colours."""
  MONTH_WIDTH = (842.0 - 2 * 18 - 24) / 14

  def underline_colours(self, ekadashi, pradosham, sankashti):
    from generate_panchanga_calendar import draw_month
    ensure_pdf_fonts()
    pdf = Canvas(BytesIO())
    civil = Date(2026, 5, 17)
    record = DayRecord(civil, "S11", 5, 7, "3", False, 0.0)
    colours = []
    original_set_fill = pdf.setFillColor
    pdf.setFillColor = lambda colour, *rest: (colours.append(colour), original_set_fill(colour, *rest))
    draw_month(pdf, 2026, 5, {civil: record}, {}, {}, ekadashi, set(), {civil: (2, 10, False)}, 40.0, 500.0,
               self.MONTH_WIDTH, pradosham, sankashti)
    return colours

  def test_each_recurring_observance_has_its_own_underline_colour(self):
    from generate_panchanga_calendar import EKADASHI_MARK, PRADOSHAM_MARK, SANKASHTI_MARK
    civil = Date(2026, 5, 17)
    colours = self.underline_colours({civil}, {civil}, {civil})
    self.assertIn(EKADASHI_MARK, colours)
    self.assertIn(PRADOSHAM_MARK, colours)
    self.assertIn(SANKASHTI_MARK, colours)

  def test_no_underline_without_observance(self):
    from generate_panchanga_calendar import EKADASHI_MARK, PRADOSHAM_MARK, SANKASHTI_MARK
    colours = self.underline_colours(set(), set(), set())
    self.assertNotIn(EKADASHI_MARK, colours)
    self.assertNotIn(PRADOSHAM_MARK, colours)
    self.assertNotIn(SANKASHTI_MARK, colours)


class DisplayMasaTests(unittest.TestCase):

  CASES = [
    ("amanta masa number is unchanged", "K1", "5", False, True, "5"),
    ("ordinary krishna advances under purnimanta", "K1", "5", False, False, "6"),
    ("sukla is unchanged under purnimanta", "S1", "5", False, False, "5"),
    ("adhika krishna is unchanged under purnimanta", "K1", "A5", True, False, "A5"),
    ("phalguna krishna wraps to chaitra under purnimanta", "K1", "12", False, False, "1"),
  ]

  def test_display_masa(self):
    for label, tithi, masa, is_adhika, amanta, expected in self.CASES:
      with self.subTest(label):
        record = DayRecord(Date(2030, 1, 1), tithi, 1, 1, masa, is_adhika, 0.0)
        self.assertEqual(display_masa(record, amanta=amanta), expected)


class SolarDateTests(unittest.TestCase):

  def test_solar_day_resets_at_sankranti(self):
    records = [
      DayRecord(Date(2026, 1, 13), "S1", 1, 1, "10", False, 1.0),
      DayRecord(Date(2026, 1, 14), "S2", 1, 1, "10", False, 2.0),
      DayRecord(Date(2026, 1, 15), "S3", 1, 1, "10", False, 3.0),
    ]
    with mock.patch(
        "generate_panchanga_calendar.panchanga.raasi",
        side_effect=[10, 10, 11],
    ):
      self.assertEqual(
        solar_dates_by_date(records),
        {
          Date(2026, 1, 13): (10, 1, False),
          Date(2026, 1, 14): (10, 2, False),
          Date(2026, 1, 15): (11, 1, True),
        },
      )


class SolarDaySeedTests(unittest.TestCase):
  """The first printed day must carry a real solar-day count, not a seeded 1.

  ``solar_dates_by_date`` starts its count at 1 for the first record it sees,
  so the printed number is only right because ``build_pdf`` feeds it the
  pad-extended ``context_records``. Shrinking ``RECORD_PAD_DAYS_BEFORE`` below
  a solar month would silently print an under-count with no test failing, so
  the pad-seeded path is pinned here through the real record helpers.
  """

  # Each start month begins mid-solar-month, so the first day is never 1.
  START_MONTHS = [(2026, 1), (2026, 3), (2026, 4), (1905, 4)]

  def _solar_day_from_raasi(self, records, first):
    """Count back from ``first`` while the rāśi holds: an independent day count."""
    raasi_by_date = {record.civil_date: int(panchanga.raasi(record.sunrise_jd)) for record in records}
    raasi = raasi_by_date[first]
    solar_day = 0
    day = first
    while raasi_by_date.get(day) == raasi:
      solar_day += 1
      day = day - 1
    return raasi, solar_day

  def test_first_printed_day_is_not_seeded_to_one(self):
    location = load_location("Ujjain")
    for year, month in self.START_MONTHS:
      months = [(year, month)]
      first = Date(year, month, 1)
      pad_start, pad_end = record_span(months)
      records = daily_records_between(pad_start, pad_end, location)
      raasi, solar_day, _is_sankranti = solar_dates_by_date(records)[first]
      expected_raasi, expected_day = self._solar_day_from_raasi(records, first)
      with self.subTest(year=year, month=month):
        # Non-vacuous: a seeded count would be 1 and would contradict the count.
        self.assertGreater(solar_day, 1)
        self.assertEqual((raasi, solar_day), (expected_raasi, expected_day))

  def test_a_truncated_pad_would_break_the_count(self):
    """Shrinking the pad below one solar month must be caught, not pass quietly."""
    location = load_location("Ujjain")
    year, month = self.START_MONTHS[1]
    first = Date(year, month, 1)
    full_start, full_end = record_span([(year, month)])
    padded = daily_records_between(full_start, full_end, location)
    _raasi, padded_day, _sk = solar_dates_by_date(padded)[first]

    # An unpadded read starts mid-solar-month, so the seed can only report 1.
    unpadded = daily_records_between(first, Date(year, month, calendar.monthrange(year, month)[1]), location)
    _raasi, unpadded_day, _sk = solar_dates_by_date(unpadded)[first]
    self.assertNotEqual(padded_day, unpadded_day)
    self.assertEqual(unpadded_day, 1)


class SolarMarkerTests(unittest.TestCase):

  def test_solar_markers_are_right_aligned(self):
    pdf = mock.Mock()
    draw_sankranti_mark(pdf, 20.0, 100.0, 10, 30.0)
    draw_solar_day_mark(pdf, 20.0, 100.0, 14, 30.0)
    self.assertEqual(
      pdf.drawRightString.call_args_list,
      [
        mock.call(49.0, 108.2, "10"),
        mock.call(49.0, 108.2, "14"),
      ],
    )
    self.assertEqual(
      pdf.setFont.call_args_list,
      [
        mock.call(PDF_FONT_BOLD, 5.0),
        mock.call(PDF_FONT_BOLD, 5.0),
      ],
    )
    self.assertEqual(
      pdf.setFillColor.call_args_list,
      [
        mock.call(SANKRANTI_INK),
        mock.call(ACCENT),
      ],
    )

  def test_eclipse_marker_is_half_width_wave(self):
    pdf = mock.Mock()
    draw_eclipse_mark(pdf, 20.0, 100.0, 30.0)
    self.assertEqual(pdf.beginPath.call_count, 1)
    pdf.beginPath.return_value.moveTo.assert_called_once_with(23.0, 101.7)
    self.assertEqual(pdf.beginPath.return_value.curveTo.call_count, 6)
    self.assertAlmostEqual(pdf.beginPath.return_value.curveTo.call_args.args[4], 38.0)
    pdf.drawPath.assert_called_once_with(pdf.beginPath.return_value, stroke=1, fill=0)
    pdf.line.assert_not_called()

  def test_ekadashi_and_eclipse_underlines_share_geometry(self):
    pdf = mock.Mock()
    draw_tithi_underline(pdf, 20.0, 100.0, 30.0, EKADASHI_MARK)
    pdf.rect.assert_called_once_with(23.0, 100.6, 15.0, 1.2, stroke=0, fill=1)

    pdf.reset_mock()
    draw_eclipse_mark(pdf, 20.0, 100.0, 30.0)
    pdf.beginPath.return_value.moveTo.assert_called_once_with(23.0, 101.7)
    self.assertAlmostEqual(pdf.beginPath.return_value.curveTo.call_args.args[4], 38.0)


class DailyRecordsCacheHookTests(unittest.TestCase):
  """``daily_records`` must forward sunrise tithi into ``masa``."""

  def test_passes_tithi_number_to_masa(self):
    import generate_panchanga_calendar as calendar_module
    import panchanga

    location = load_location("Bengaluru")
    panchanga.set_chosen_ayanamsa("citra")
    with mock.patch.object(calendar_module.panchanga, "masa", return_value=[1, False]) as masa_mock:
      daily_records([(2026, 1)], location)
    self.assertTrue(masa_mock.called)
    for _args, kwargs in masa_mock.call_args_list:
      self.assertIn("tithi_number", kwargs)
      self.assertIsInstance(kwargs["tithi_number"], int)
      self.assertGreaterEqual(kwargs["tithi_number"], 1)
      self.assertLessEqual(kwargs["tithi_number"], 30)


class FormatUtcOffsetTests(unittest.TestCase):
  """``format_utc_offset`` renders UTC offset with timezone abbreviation."""

  CASES = [
    ("ist has no dst", "Asia/Kolkata", 2026, 3, "UTC+5:30 (IST)"),
    ("helsinki summer dst", "Europe/Helsinki", 2026, 6, "UTC+3 (EEST)"),
    ("helsinki winter no dst", "Europe/Helsinki", 2026, 12, "UTC+2 (EET)"),
    ("us eastern summer dst", "America/New_York", 2026, 7, "UTC-4 (EDT)"),
    ("us eastern winter no dst", "America/New_York", 2026, 1, "UTC-5 (EST)"),
    ("utc zero", "UTC", 2026, 6, "UTC+0 (UTC)"),
    ("whole hour offset", "Europe/London", 2026, 1, "UTC+0 (GMT)"),
    ("nepal unusual offset", "Asia/Kathmandu", 2026, 6, "UTC+5:45 (+0545)"),
  ]

  def test_format_utc_offset(self):
    for label, zone, year, month, expected in self.CASES:
      with self.subTest(label):
        self.assertEqual(format_utc_offset(zone, year, month), expected)


class TimezoneInHeaderTests(unittest.TestCase):
  """Page subtitle must show UTC offset; title stays tz-free."""

  def test_annual_header_timezones(self):
    for location_name, month, subtitle_offset in (("Ujjain", 3, "UTC+5:30 (IST)"),
                                                  ("Helsinki", 6, "UTC+3 (EEST)")):
      with self.subTest(location_name=location_name):
        location = load_location(location_name)
        months = list(_month_sequence(2026, month, 14))
        pdf = mock.Mock()
        pdf.stringWidth.return_value = 60.0
        with mock.patch("generate_panchanga_calendar.fitted_font_size", return_value=10):
          draw_page_header(pdf, location, months, RULESET_VERSION)
        title = pdf.drawString.call_args_list[0].args[2]
        subtitle = pdf.drawString.call_args_list[1].args[2]
        self.assertTrue(title.startswith(location_name) and "Panchanga:" in title)
        self.assertNotIn("UTC", title)
        self.assertIn(f"{subtitle_offset} civil time", subtitle)


class DstTransitionsTests(unittest.TestCase):
  """``dst_transitions`` detects DST start/end dates."""

  CASES = [
    ("helsinki spring forward", ("Europe/Helsinki", 2026, 3), {29: "DST starts"}),
    ("helsinki fall back", ("Europe/Helsinki", 2026, 10), {25: "DST ends"}),
    ("new york spring forward", ("America/New_York", 2026, 3), {8: "DST starts"}),
    ("new york fall back", ("America/New_York", 2026, 11), {1: "DST ends"}),
    ("no dst zone", ("Asia/Kolkata", 2026, 3), {}),
    ("no dst zone summer", ("Asia/Kolkata", 2026, 6), {}),
    ("month without transition", ("Europe/Helsinki", 2026, 6), {}),
    ("month without transition summer", ("America/New_York", 2026, 7), {}),
  ]

  def test_dst_transitions(self):
    for label, arguments, expected in self.CASES:
      with self.subTest(label):
        self.assertEqual(dst_transitions(*arguments), expected)


if __name__ == "__main__":
  unittest.main()
