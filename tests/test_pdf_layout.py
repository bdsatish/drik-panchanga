"""Regression tests for the generated one-page calendar layout."""

from datetime import date
from io import BytesIO
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

from reportlab.pdfgen.canvas import Canvas

from festival_rules import DayRecord
from generate_panchanga_calendar import (
  ACCENT,
  ADHIKA_INK,
  DEFAULT_FESTIVALS_PATH,
  EKADASHI_MARK,
  FOOTER_FESTIVAL_SLOTS,
  KRSNA_INK,
  LAYOUT_VERSION,
  MASA_START_INK,
  PDF_FONT_BOLD,
  PDF_FONT_BOLD_ITALIC,
  PDF_FONT_TTC,
  RULESET_VERSION,
  SANKRANTI_INK,
  TITHI_COLUMN_RATIO,
  argument_parser,
  build_pdf,
  calendar_year_label,
  context_month_range,
  daily_records,
  default_output_path,
  display_masa,
  draw_month,
  draw_page_footer,
  draw_page_header,
  draw_eclipse_mark,
  draw_sankranti_mark,
  draw_solar_day_mark,
  draw_tithi_underline,
  dst_transitions,
  ensure_pdf_fonts,
  fitted_font_size,
  format_utc_offset,
  kali_ahargana_range,
  load_location,
  month_range,
  sankranti_key_line,
  solar_dates_by_date,
  tithi_display_parts,
  tithi_font,
  tithi_ink,
)


class PdfLayoutTests(unittest.TestCase):

  def test_month_ranges_cross_january_and_december(self):
    cases = {
      (2026, 1): ((2027, 2), (2025, 12), (2027, 3)),
      (2026, 12): ((2028, 1), (2026, 11), (2028, 2)),
    }
    for start, expected in cases.items():
      with self.subTest(start=start):
        months = month_range(*start)
        context = context_month_range(*start)
        last_month, first_context, last_context = expected
        self.assertEqual(len(months), 14)
        self.assertEqual(months[0], start)
        self.assertEqual(months[-1], last_month)
        self.assertEqual(len(context), 16)
        self.assertEqual(context[0], first_context)
        self.assertEqual(context[1:-1], months)
        self.assertEqual(context[-1], last_context)

  def test_generated_calendar_has_exactly_one_page(self):
    import generate_panchanga_calendar as calendar_module

    with TemporaryDirectory() as directory:
      output = Path(directory) / "calendar.pdf"
      with mock.patch("generate_panchanga_calendar.find_local_eclipses", return_value=[
        ("Lunar", "Partial", 2461103.0419131187),
      ]), mock.patch("generate_panchanga_calendar.draw_page_footer", wraps=calendar_module.draw_page_footer) as footer:
        build_pdf(load_location("Helsinki"), 2026, 6, output)
      document = output.read_bytes()

    page_objects = re.findall(rb"/Type\s*/Page\b", document)
    self.assertEqual(len(page_objects), 1)
    self.assertIn(RULESET_VERSION.encode("ascii"), document)
    self.assertIn(LAYOUT_VERSION.encode("ascii"), document)
    self.assertEqual(footer.call_count, 1)
    self.assertIn("Eclipses:", footer.call_args.kwargs["eclipse_line"])
    self.assertNotIn(b"/BaseFont /Helvetica", document)
    self.assertIn(b"IndUni-H", document)

  def test_cli_defaults_festivals_path(self):
    parser = argument_parser()
    arguments = parser.parse_args(["--city", "Helsinki", "--start", "2026-03"])
    self.assertFalse(hasattr(arguments, "festival_policy"))
    self.assertEqual(arguments.festivals, DEFAULT_FESTIVALS_PATH)

  def test_default_filename_has_no_policy_suffix(self):
    path = default_output_path(load_location("Helsinki"), 2026, 3)
    self.assertEqual(path.name, "helsinki-fi_panchanga_2026-03_to_2027-04.pdf")

  def test_purnimanta_filename_suffix(self):
    path = default_output_path(load_location("Helsinki"), 2026, 3, month_system="purnimanta")
    self.assertEqual(path.name, "helsinki-fi_panchanga_2026-03_to_2027-04_purnimanta.pdf")

  def test_ayanamsa_filename_suffix(self):
    path = default_output_path(load_location("Helsinki"), 2026, 3, coordinate_selection="raman")
    self.assertEqual(path.name, "helsinki-fi_panchanga_2026-03_to_2027-04_raman.pdf")

  def test_tropical_filename_suffix(self):
    path = default_output_path(load_location("Helsinki"), 2026, 3, coordinate_selection="tropical")
    self.assertEqual(path.name, "helsinki-fi_panchanga_2026-03_to_2027-04_tropical.pdf")

  def test_cli_accepts_month_system(self):
    parser = argument_parser()
    arguments = parser.parse_args(["--city", "Helsinki", "--start", "2026-03", "--month", "purnimanta"])
    self.assertEqual(arguments.month, "purnimanta")

  def test_cli_accepts_ayanamsa(self):
    parser = argument_parser()
    arguments = parser.parse_args(["--city", "Helsinki", "--start", "2026-03", "--ayanamsa", "revati"])
    self.assertEqual(arguments.ayanamsa, "revati")

  def test_cli_accepts_tropical_ayanamsa(self):
    parser = argument_parser()
    arguments = parser.parse_args(["--city", "Helsinki", "--start", "2026-03", "--ayanamsa", "tropical"])
    self.assertEqual(arguments.ayanamsa, "tropical")

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
                  "generate_panchanga_calendar.daily_records",
                  wraps=calendar_module.daily_records) as records_mock:
        build_pdf(load_location("Bengaluru"), 2023, 3, output, month_system="purnimanta")
      document = output.read_bytes()
    self.assertEqual(records_mock.call_count, 1)
    # Subject is uncompressed in the Info dict; page content streams are flate-encoded.
    self.assertIn(b"purnimanta masa", document)
    self.assertNotIn(b"and amanta masa", document)

  def test_calendar_year_label_uses_both_samvatsara_conventions(self):
    records = [
      DayRecord(date(2026, 8, 15), "S1", 1, 1, "A4", True, 0.0),
    ]
    self.assertEqual(calendar_year_label(records), "1948 Parābhava | 2083 Siddhārthī | 5127 Kali (elapsed)")

  def test_pdf_subtitle_has_kali_ahargana_range(self):
    months = list(month_range(2026, 6))
    self.assertEqual(kali_ahargana_range(months), (1872727, 1873152))

    pdf = mock.Mock()
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

  def test_footer_key_lines_use_iast_names(self):
    from generate_panchanga_calendar import (
      masa_key_line,
      nakshatra_key_line,
      sankranti_key_line,
      tithi_key_line,
      yoga_key_line,
    )
    self.assertTrue(tithi_key_line().startswith("T:"))
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
    self.assertIn("Viṣkumbha", yoga_key_line())
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
    civil = date(2026, 5, 17)
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
    plain_text, plain_size = self.draw_badge("3", False)
    wide_text, wide_size = self.draw_badge("A12", True)
    self.assertEqual(wide_text, "A12")
    self.assertLess(wide_size, plain_size)
    cell_width = self.MONTH_WIDTH * TITHI_COLUMN_RATIO
    tithi_width = Canvas(BytesIO()).stringWidth("01", tithi_font(True), 7.4)
    badge_width = Canvas(BytesIO()).stringWidth(wide_text, PDF_FONT_BOLD, wide_size)
    self.assertLessEqual(3.0 + tithi_width + badge_width, cell_width - 1.0)


class DisplayMasaTests(unittest.TestCase):

  def test_amanta_is_unchanged(self):
    record = DayRecord(date(2030, 1, 1), "K1", 1, 1, "5", False, 0.0)
    self.assertEqual(display_masa(record, amanta=True), "5")

  def test_purnimanta_advances_ordinary_krishna(self):
    record = DayRecord(date(2030, 1, 1), "K1", 1, 1, "5", False, 0.0)
    self.assertEqual(display_masa(record, amanta=False), "6")

  def test_purnimanta_leaves_sukla_unchanged(self):
    record = DayRecord(date(2030, 1, 1), "S1", 1, 1, "5", False, 0.0)
    self.assertEqual(display_masa(record, amanta=False), "5")

  def test_purnimanta_leaves_adhika_krishna_unchanged(self):
    record = DayRecord(date(2030, 1, 1), "K1", 1, 1, "A5", True, 0.0)
    self.assertEqual(display_masa(record, amanta=False), "A5")

  def test_purnimanta_wraps_phalguna_krishna_to_chaitra(self):
    record = DayRecord(date(2030, 1, 1), "K1", 1, 1, "12", False, 0.0)
    self.assertEqual(display_masa(record, amanta=False), "1")


class SolarDateTests(unittest.TestCase):

  def test_solar_day_resets_at_sankranti(self):
    records = [
      DayRecord(date(2026, 1, 13), "S1", 1, 1, "10", False, 1.0),
      DayRecord(date(2026, 1, 14), "S2", 1, 1, "10", False, 2.0),
      DayRecord(date(2026, 1, 15), "S3", 1, 1, "10", False, 3.0),
    ]
    with mock.patch(
        "generate_panchanga_calendar.panchanga.raasi",
        side_effect=[10, 10, 11],
    ):
      self.assertEqual(
        solar_dates_by_date(records),
        {
          date(2026, 1, 13): (10, 1, False),
          date(2026, 1, 14): (10, 2, False),
          date(2026, 1, 15): (11, 1, True),
        },
      )


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

  def test_ist_no_dst(self):
    self.assertEqual(format_utc_offset("Asia/Kolkata", 2026, 3), "UTC+5:30 (IST)")

  def test_helsinki_summer_dst(self):
    self.assertEqual(format_utc_offset("Europe/Helsinki", 2026, 6), "UTC+3 (EEST)")

  def test_helsinki_winter_no_dst(self):
    self.assertEqual(format_utc_offset("Europe/Helsinki", 2026, 12), "UTC+2 (EET)")

  def test_us_eastern_summer_dst(self):
    self.assertEqual(format_utc_offset("America/New_York", 2026, 7), "UTC-4 (EDT)")

  def test_us_eastern_winter_no_dst(self):
    self.assertEqual(format_utc_offset("America/New_York", 2026, 1), "UTC-5 (EST)")

  def test_utc_zero(self):
    self.assertEqual(format_utc_offset("UTC", 2026, 6), "UTC+0 (UTC)")

  def test_whole_hour_offset(self):
    self.assertEqual(format_utc_offset("Europe/London", 2026, 1), "UTC+0 (GMT)")

  def test_nepal_unusual_offset(self):
    self.assertEqual(format_utc_offset("Asia/Kathmandu", 2026, 6), "UTC+5:45 (+0545)")


class TimezoneInHeaderTests(unittest.TestCase):
  """Page header must show UTC offset next to the place name."""

  def test_annual_header_includes_timezone(self):
    location = load_location("Ujjain")
    months = list(month_range(2026, 3))
    pdf = mock.Mock()
    with mock.patch("generate_panchanga_calendar.fitted_font_size", return_value=10):
      draw_page_header(pdf, location, months, RULESET_VERSION)
    title = pdf.drawString.call_args_list[0].args[2]
    self.assertTrue(title.startswith("Ujjain, IN, UTC+5:30 (IST) Panchanga:"))

  def test_annual_header_timezone_respects_dst(self):
    location = load_location("Helsinki")
    months = list(month_range(2026, 6))
    pdf = mock.Mock()
    with mock.patch("generate_panchanga_calendar.fitted_font_size", return_value=10):
      draw_page_header(pdf, location, months, RULESET_VERSION)
    title = pdf.drawString.call_args_list[0].args[2]
    self.assertTrue(title.startswith("Helsinki, FI, UTC+3 (EEST) Panchanga:"))


class DstTransitionsTests(unittest.TestCase):
  """``dst_transitions`` detects DST start/end dates."""

  def test_helsinki_spring_forward(self):
    self.assertEqual(dst_transitions("Europe/Helsinki", 2026, 3), {29: "DST starts"})

  def test_helsinki_fall_back(self):
    self.assertEqual(dst_transitions("Europe/Helsinki", 2026, 10), {25: "DST ends"})

  def test_new_york_spring_forward(self):
    self.assertEqual(dst_transitions("America/New_York", 2026, 3), {8: "DST starts"})

  def test_new_york_fall_back(self):
    self.assertEqual(dst_transitions("America/New_York", 2026, 11), {1: "DST ends"})

  def test_no_dst_zone_returns_empty(self):
    self.assertEqual(dst_transitions("Asia/Kolkata", 2026, 3), {})
    self.assertEqual(dst_transitions("Asia/Kolkata", 2026, 6), {})

  def test_month_without_transition_returns_empty(self):
    self.assertEqual(dst_transitions("Europe/Helsinki", 2026, 6), {})
    self.assertEqual(dst_transitions("America/New_York", 2026, 7), {})


if __name__ == "__main__":
  unittest.main()
