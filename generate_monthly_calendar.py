#!/usr/bin/env python3
"""12-month panchanga wall calendar: one A4 portrait grid page per month.

Distinct from ``generate_panchanga_calendar.py`` (14 months on a single
landscape sheet). Each page is a classic Sunday-first month grid. Every
day cell shows the tithi and nakshatra at sunrise with their end times;
when a tithi or nakshatra is skipped (leap), both names and both end
times are printed. Saṅkrānti days carry the rāśi name, festivals are
listed inline, and locally visible eclipses get a wavy underline.

Timings above 24:00 denote hours past midnight (the Hindu day runs
sunrise to sunrise).
"""

import argparse
import calendar
import logging
import sys
from datetime import date as CivilDate
from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from festival_rules import (
  ekadashi_dates_from_records,
  find_local_eclipses,
  jd_to_local_civil_date,
)
import panchanga

from generate_panchanga_calendar import (
  ADHIKA_ROW,
  DEFAULT_CITIES_PATH,
  DEFAULT_FESTIVALS_PATH,
  MASA_START_ROW,
  PDF_FONT,
  PDF_FONT_BOLD,
  PDF_FONT_BOLD_ITALIC,
  PDF_FONT_ITALIC,
  RULESET_VERSION,
  coordinate_selection_label,
  daily_records,
  display_masa,
  embed_pdf_metadata,
  ensure_pdf_fonts,
  format_local_hm,
  load_location,
  location_slug,
  masa_badges_by_date,
  month_system_label,
  place_for_date,
  require_coordinate_selection,
  require_month_system,
  require_start_month,
  resolve_festivals,
  sanskrit_names,
  solar_dates_by_date,
)
from panchanga import Date as PanDate
from panchanga import gregorian_to_jd

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

MONTHLY_LAYOUT_VERSION = "Wall-Grid-1.0"
MONTHLY_MONTH_COUNT = 12
CONTEXT_MONTH_COUNT = MONTHLY_MONTH_COUNT + 2

PAGE_W, PAGE_H = A4
MARGIN = 34
HEADER_H = 92
WEEKDAY_ROW_H = 20
GRID_ROWS = 6
FOOTER_H = 34

INK = HexColor("#1A1A1A")
GREY = HexColor("#9A9A9A")
LIGHT = HexColor("#E3E3E3")
GRID_LINE = HexColor("#A8A8A8")
RED = HexColor("#A8321F")
TEAL = HexColor("#0E6E62")
SAFFRON = HexColor("#F3D9A9")
SAFFRON_INK = HexColor("#9A6A1F")
CRIMSON = HexColor("#8E1F3D")
BROWN = HexColor("#5C2E1B")
NAKS_INK = HexColor("#5B3A29")
YOGA_INK = HexColor("#2F4F4F")

_MONTH_NAMES_EN = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
]

_TITHI_NAMES = {
  1: "Prātipadā",
  2: "Dvītīyā",
  3: "Tṛtīyā",
  4: "Caturthī",
  5: "Pañcamī",
  6: "Ṣaṣṭhī",
  7: "Saptamī",
  8: "Aṣṭamī",
  9: "Navamī",
  10: "Daśamī",
  11: "Ekādaśī",
  12: "Dvādaśī",
  13: "Trayodaśī",
  14: "Caturdaśī",
  15: "Pūrṇimā",
  16: "Prātipadā",
  17: "Dvītīyā",
  18: "Tṛtīyā",
  19: "Caturthī",
  20: "Pañcamī",
  21: "Ṣaṣṭhī",
  22: "Saptamī",
  23: "Aṣṭamī",
  24: "Navamī",
  25: "Daśamī",
  26: "Ekādaśī",
  27: "Dvādaśī",
  28: "Trayodaśī",
  29: "Caturdaśī",
  30: "Amāvāsyā",
}


def month_sequence(start_year, start_month, count):
  months = []
  year, month = start_year, start_month
  for _ in range(count):
    months.append((year, month))
    if month == 12:
      year, month = year + 1, 1
    else:
      month += 1
  return months


def context_months(start_year, start_month):
  if start_month == 1:
    year, month = start_year - 1, 12
  else:
    year, month = start_year, start_month - 1
  return month_sequence(year, month, CONTEXT_MONTH_COUNT)


def tithi_name(number):
  return _TITHI_NAMES.get(int(number), str(number))


def nakshatra_name(number):
  return sanskrit_names().get("nakshatras", {}).get(str(int(number)), str(number))


def yoga_name(number):
  return sanskrit_names().get("yogas", {}).get(str(int(number)), str(number))


def format_hms(hms):
  """``[h, m, s]`` local decimal hours to ``HH:MM``; hours may exceed 24."""
  hours, minutes, seconds = hms
  total = int(round(hours * 60 + minutes + seconds / 60.0))
  return f"{total // 60:02d}:{total % 60:02d}"


def tithi_code(number):
  number = int(number)
  return f"S{number}" if number <= 15 else f"K{number - 15}"


def day_details(location, civil):
  place = place_for_date(location, civil)
  jd = gregorian_to_jd(civil)
  tithi_lines = []
  t = panchanga.tithi(jd, place)
  tithi_lines.append((tithi_code(t[0]), format_hms(t[1])))
  if len(t) >= 4:
    tithi_lines.append((tithi_code(t[2]), format_hms(t[3])))
  naks_lines = []
  n = panchanga.nakshatra(jd, place)
  naks_lines.append((nakshatra_name(n[0]), format_hms(n[1])))
  if len(n) >= 4:
    naks_lines.append((nakshatra_name(n[2]), format_hms(n[3])))
  yoga_names = []
  y = panchanga.yoga(jd, place)
  yoga_names.append(yoga_name(y[0]))
  if len(y) >= 4:
    yoga_names.append(yoga_name(y[2]))
  return tithi_lines, naks_lines, yoga_names


def sun_moon_lines(location, civil):
  """``Sun: rise-set`` and ``Moon: rise-set`` lines for one civil day."""
  place = place_for_date(location, civil)
  jd = gregorian_to_jd(civil)
  lines = []
  try:
    rise = panchanga.sunrise(jd, place)[1]
    set_ = panchanga.sunset(jd, place)[1]
    lines.append(f"Sun: {format_hms(rise)}-{format_hms(set_)}")
  except Exception as exc:
    log.debug("sun times unavailable %s: %s", civil, exc)
  try:
    parts = []
    for event in (panchanga.moonrise(jd, place), panchanga.moonset(jd, place)):
      if 0 <= event[0] < 48:
        parts.append(format_hms(event))
    if parts:
      lines.append("Moon: " + "-".join(parts))
  except Exception as exc:
    log.debug("moon times unavailable %s: %s", civil, exc)
  return lines


def varjyam_lines(location, civil):
  """Varjyam (Vishaghati) windows for one civil day, sunrise to next sunrise."""
  place = place_for_date(location, civil)
  jd = gregorian_to_jd(civil)
  lines = []
  try:
    for start, end in panchanga.varjyam(jd, place):
      lines.append(f"Varjyam: {format_hms(start)}-{format_hms(end)}")
  except Exception as exc:
    log.debug("varjyam unavailable %s: %s", civil, exc)
  return lines


def _wrap_lines(pdf, text, font, size, max_width):
  words = text.split()
  lines = []
  current = ""
  for word in words:
    test = current + (" " if current else "") + word
    if pdf.stringWidth(test, font, size) <= max_width:
      current = test
    else:
      if current:
        lines.append(current)
      current = word
  if current:
    lines.append(current)
  return lines if lines else [text]


def year_label_for_month(amanta, year, month, records_by_date):
  """Webapp-style era label for mid-month: ``Parābhava 1948, Siddhārthī 2083, Kali (elapsed) 5127``."""
  days = calendar.monthrange(year, month)[1]
  civil = CivilDate(year, month, min(15, days))
  record = records_by_date.get(civil)
  if record is None:
    return None
  masa_num = int(display_masa(record, amanta=amanta).lstrip("A"))
  jd = gregorian_to_jd(PanDate(year, month, civil.day))
  kali_year, saka_year, vikrama_year = panchanga.elapsed_year(jd, masa_num)
  names = sanskrit_names()["samvats"]
  saka_name = names[str(panchanga.samvatsara(jd, masa_num))]
  vikrama_name = names[str(panchanga.samvatsara_north_modern(jd, masa_num))]
  return (f"{saka_name} {saka_year}, {vikrama_name} {vikrama_year}, "
          f"Kali (elapsed) {kali_year}")


def draw_header(pdf, location, year, month, amanta, coordinate_selection, year_label):
  top = PAGE_H - MARGIN
  pdf.setFillColor(INK)
  pdf.setFont(PDF_FONT_BOLD, 30)
  pdf.drawString(MARGIN, top - 28, f"{_MONTH_NAMES_EN[month - 1]} {year}")

  pdf.setFillColor(GREY)
  pdf.setFont(PDF_FONT_ITALIC, 11)
  pdf.drawString(MARGIN, top - 46, location.name)

  if year_label:
    pdf.setFillColor(INK)
    pdf.setFont(PDF_FONT, 9)
    pdf.drawRightString(PAGE_W - MARGIN, top - 28, year_label)
  pdf.setFillColor(GREY)
  pdf.setFont(PDF_FONT, 7)
  pdf.drawRightString(
    PAGE_W - MARGIN, top - 42, f"{month_system_label(amanta)}, {coordinate_selection_label(coordinate_selection)}, "
    f"Ruleset {RULESET_VERSION}, layout {MONTHLY_LAYOUT_VERSION}")

  pdf.setStrokeColor(INK)
  pdf.setLineWidth(1.2)
  pdf.line(MARGIN, top - HEADER_H, PAGE_W - MARGIN, top - HEADER_H)


def draw_weekday_row(pdf, grid_top):
  labels = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
  cell_w = (PAGE_W - 2 * MARGIN) / 7
  pdf.setFont(PDF_FONT_BOLD, 8)
  for col, label in enumerate(labels):
    x = MARGIN + col * cell_w
    pdf.setFillColor(RED if col == 0 else GREY)
    pdf.drawCentredString(x + cell_w / 2, grid_top + 6, label)


def draw_cell(pdf, x, y_top, row_h, cell_w, day, civil, location, context):
  y_bottom = y_top - row_h
  record = context["records_by_date"].get(civil)
  raasi_num, solar_day, is_sankranti = context["solar_by_date"].get(civil, (None, None, False))
  is_ekadashi = civil in context["ekadashi"]
  festivals = context["festival_names_by_date"].get(civil, [])
  is_sunday = civil.weekday() == 6

  if is_sankranti:
    pdf.setFillColor(SAFFRON)
    pdf.rect(x, y_bottom, cell_w, row_h, stroke=0, fill=1)

  masa_badge = context.get("masa_badges", {}).get(civil)
  is_masa_start = masa_badge is not None
  if is_masa_start:
    is_adhika_masa = masa_badge.startswith("A")
    pdf.setFillColor(ADHIKA_ROW if is_adhika_masa else MASA_START_ROW)
    pdf.rect(x, y_bottom, cell_w, row_h, stroke=0, fill=1)
  if is_ekadashi:
    pdf.setFillColor(TEAL)
    pdf.rect(x, y_bottom, 2.2, row_h, stroke=0, fill=1)
  pdf.setStrokeColor(GRID_LINE)
  pdf.setLineWidth(0.5)
  pdf.rect(x, y_bottom, cell_w, row_h, stroke=1, fill=0)

  pdf.setFillColor(RED if is_sunday else INK)
  pdf.setFont(PDF_FONT_BOLD, 15)
  pdf.drawRightString(x + cell_w - 5, y_top - 15, str(day))

  if record is None:
    return
  line_y = y_top - 25

  if raasi_num is not None:
    zodiac_index = (int(raasi_num) - 1) % 12
    raasi_name = sanskrit_names().get("zodiac", {}).get(str(zodiac_index), str(raasi_num)).capitalize()
    pdf.setFillColor(INK)
    pdf.setFont(PDF_FONT, 6.8)
    pdf.drawString(x + 4, line_y, f"{raasi_name} {solar_day}")
    line_y -= 8.0

  masa_display = display_masa(record, amanta=context.get("amanta", True))
  masa_name = sanskrit_names().get("masas", {}).get(masa_display.lstrip("A"), masa_display.lstrip("A"))
  masa_prefix = f"A.{masa_name}" if masa_display.startswith("A") else masa_name
  tithi_lines, naks_lines, yoga_names = day_details(location, civil)
  for code, end_hm in tithi_lines:
    pdf.setFillColor(INK)
    pdf.setFont(PDF_FONT, 6.8)
    pdf.drawString(x + 4, line_y, f"{masa_prefix} {code} {end_hm}")
    line_y -= 8.0
  for name, end_hm in naks_lines:
    pdf.setFillColor(NAKS_INK)
    pdf.setFont(PDF_FONT, 6.5)
    pdf.drawString(x + 4, line_y, f"{name} {end_hm}")
    line_y -= 8.0
  for name in yoga_names:
    pdf.setFillColor(YOGA_INK)
    pdf.setFont(PDF_FONT_ITALIC, 6.5)
    pdf.drawString(x + 4, line_y, name)
    line_y -= 8.0
  max_text_w = cell_w - 10
  for name in festivals:
    pdf.setFillColor(CRIMSON)
    pdf.setFont(PDF_FONT_ITALIC, 6.8)
    for wrapped in _wrap_lines(pdf, name, PDF_FONT_ITALIC, 6.8, max_text_w):
      pdf.drawString(x + 4, line_y, wrapped)
      line_y -= 8.0

  for kind, _phase, max_jd in context.get("eclipse_details_by_date", {}).get(civil, []):
    pdf.setFillColor(BROWN)
    pdf.setFont(PDF_FONT_ITALIC, 6.5)
    hm = format_local_hm(max_jd, location.timezone_name)
    pdf.drawString(x + 4, line_y, f"{kind} eclipse")
    line_y -= 8.0
    pdf.drawString(x + 4, line_y, f"max {hm}")
    line_y -= 8.0

  bottom_y = y_bottom + 4
  bottom_lines = sun_moon_lines(location, civil) + varjyam_lines(location, civil)
  for i, text in enumerate(bottom_lines):
    pdf.setFillColor(RED if text.startswith("Varjyam") else GREY)
    pdf.setFont(PDF_FONT, 5.8)
    pdf.drawString(x + 4, bottom_y + i * 8.0, text)


def rahu_kala_table_lines(location, year, month):
  """Weekday rahu kala sampled from the first seven days of the month, Sunday first."""
  labels = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
  by_weekday = {}
  for day in range(1, 8):
    civil = CivilDate(year, month, day)
    place = place_for_date(location, civil)
    jd = gregorian_to_jd(civil)
    start, end = panchanga.trikalam(jd, place, option="rahu")
    by_weekday[civil.weekday()] = f"{labels[civil.weekday()]} {format_hms(start)}-{format_hms(end)}"
  return [by_weekday[d] for d in (6, 0, 1, 2, 3, 4, 5)]


def draw_rahu_kala_table(pdf, x, y_top, location, year, month):
  pdf.setFillColor(INK)
  pdf.setFont(PDF_FONT_BOLD, 6.5)
  pdf.drawString(x + 4, y_top - 14, "Rahu kala")
  line_y = y_top - 14 - 8.0
  pdf.setFillColor(GREY)
  pdf.setFont(PDF_FONT, 5.8)
  for line in rahu_kala_table_lines(location, year, month):
    pdf.drawString(x + 4, line_y, line)
    line_y -= 8.0


def draw_grid(pdf, year, month, location, context):
  grid_top = PAGE_H - MARGIN - HEADER_H - WEEKDAY_ROW_H
  grid_bottom = MARGIN + FOOTER_H
  row_h = (grid_top - grid_bottom) / GRID_ROWS
  cell_w = (PAGE_W - 2 * MARGIN) / 7

  draw_weekday_row(pdf, grid_top)

  days = calendar.monthrange(year, month)[1]
  first_weekday = calendar.weekday(year, month, 1)
  first_col = (first_weekday + 1) % 7

  prev_month = month - 1 if month > 1 else 12
  prev_year = year if month > 1 else year - 1
  prev_days = calendar.monthrange(prev_year, prev_month)[1]

  for row in range(GRID_ROWS):
    for col in range(7):
      x = MARGIN + col * cell_w
      y_top = grid_top - row * row_h
      slot = row * 7 + col - first_col
      day = slot + 1
      if day < 1 or day > days:
        other = prev_days + day if day < 1 else day - days
        pdf.setStrokeColor(GRID_LINE)
        pdf.setLineWidth(0.5)
        pdf.rect(x, y_top - row_h, cell_w, row_h, stroke=1, fill=0)
        if row == GRID_ROWS - 1 and col == 6:
          draw_rahu_kala_table(pdf, x, y_top, location, year, month)
        else:
          pdf.setFillColor(LIGHT)
          pdf.setFont(PDF_FONT, 9)
          pdf.drawRightString(x + cell_w - 5, y_top - 13, str(other))
        continue
      civil = CivilDate(year, month, day)
      draw_cell(pdf, x, y_top, row_h, cell_w, day, civil, location, context)


def draw_footer(pdf, location, coordinate_selection, page_index, total):
  pdf.setFillColor(GREY)
  pdf.setFont(PDF_FONT_ITALIC, 7.5)
  note = ("Sunrise-based. Timings above 24:00 are hours past midnight. "
          "Teal bar = Ekādaśī upavasa. Green = māsa start. "
          "Gold = adhika māsa. Saffron = saṅkrānti.")
  pdf.drawString(MARGIN, MARGIN + 18, note)
  pdf.setFillColor(GREY)
  pdf.drawRightString(PAGE_W - MARGIN, MARGIN + 6, f"page {page_index} of {total}")


def collect_context(months, location, festivals_path, amanta=True):
  records = daily_records(months, location)
  geopos = (location.longitude, location.latitude, 0.0)
  from generate_panchanga_calendar import load_festival_selection
  enabled_names = load_festival_selection(festivals_path)
  target_dates = {record.civil_date for record in records}
  festivals_by_date, festival_entries = resolve_festivals(
    records, target_dates, geopos=geopos, timezone_name=location.timezone_name, enabled_names=enabled_names)
  lookup = {marker: name for marker, _label, name in festival_entries}
  festival_names_by_date = {}
  for civil, markers in festivals_by_date.items():
    festival_names_by_date[civil] = [lookup.get(m, str(m)) for m in markers]
  eclipses = find_local_eclipses(records[0].sunrise_jd, records[-1].sunrise_jd + 1, geopos)
  eclipse_dates = {jd_to_local_civil_date(entry[2], location.timezone_name) for entry in eclipses}
  eclipse_details_by_date = {}
  for kind, phase, max_jd in eclipses:
    civil = jd_to_local_civil_date(max_jd, location.timezone_name)
    eclipse_details_by_date.setdefault(civil, []).append((kind, phase, max_jd))
  return {
    "records_by_date": {
      record.civil_date: record
      for record in records
    },
    "festival_names_by_date": festival_names_by_date,
    "eclipse_dates": eclipse_dates,
    "eclipse_details_by_date": eclipse_details_by_date,
    "masa_badges": masa_badges_by_date(records, amanta=amanta),
    "amanta": amanta,
    "solar_by_date": solar_dates_by_date(records),
    "ekadashi": {d
                 for d in ekadashi_dates_from_records(records)},
  }


def build_monthly_pdf(location, start_year, start_month, output_path, festivals_path=None, month_system="amanta",
                      coordinate_selection="citra"):
  with panchanga.coordinate_calculation_lock:
    return _build_monthly_pdf_unlocked(location, start_year, start_month, output_path, festivals_path=festivals_path,
                                       month_system=month_system, coordinate_selection=coordinate_selection)


def _build_monthly_pdf_unlocked(location, start_year, start_month, output_path, festivals_path=None,
                                month_system="amanta", coordinate_selection="citra"):
  ensure_pdf_fonts()
  amanta = require_month_system(month_system)
  if festivals_path is None:
    festivals_path = DEFAULT_FESTIVALS_PATH
  panchanga.set_coordinate_selection(coordinate_selection)

  months = month_sequence(start_year, start_month, MONTHLY_MONTH_COUNT)
  context = collect_context(context_months(start_year, start_month), location, Path(festivals_path), amanta=amanta)

  output_path = Path(output_path)
  pdf = canvas.Canvas(str(output_path), pagesize=A4, initialFontName=PDF_FONT)
  end_year, end_month = months[-1]
  embed_pdf_metadata(
    pdf,
    title=(f"{location.name} Panchanga {_MONTH_NAMES_EN[start_month - 1]} {start_year} to "
           f"{_MONTH_NAMES_EN[end_month - 1]} {end_year}"),
    subject=(f"Monthly wall-grid panchanga with sunrise tithi and nakshatra end times at "
             f"{location.name}; {month_system_label(amanta)} month system"),
    ruleset_version=RULESET_VERSION,
    coordinate_selection=coordinate_selection,
  )
  for index, (year, month) in enumerate(months, start=1):
    pdf.setFillColor(white)
    pdf.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    year_label = year_label_for_month(amanta, year, month, context["records_by_date"])
    draw_header(pdf, location, year, month, amanta, coordinate_selection, year_label)
    draw_grid(pdf, year, month, location, context)
    draw_footer(pdf, location, coordinate_selection, index, MONTHLY_MONTH_COUNT)
    pdf.showPage()
  pdf.save()
  return output_path


def default_monthly_output_path(location, start_year, start_month, month_system="amanta", coordinate_selection="citra"):
  amanta = require_month_system(month_system)
  months = month_sequence(start_year, start_month, MONTHLY_MONTH_COUNT)
  end_year, end_month = months[-1]
  parts = []
  if not amanta:
    parts.append("purnimanta")
  if coordinate_selection == "tropical":
    parts.append("tropical")
  elif coordinate_selection != "citra":
    parts.append(coordinate_selection)
  suffix = ("_" + "_".join(parts)) if parts else ""
  return Path(f"{location_slug(location.name)}_panchanga_wall_"
              f"{start_year:04d}-{start_month:02d}_to_"
              f"{end_year:04d}-{end_month:02d}{suffix}.pdf")


def argument_parser():
  parser = argparse.ArgumentParser(description=("Generate a 12-month wall-calendar panchanga PDF "
                                                "(one A4 portrait grid page per month)."))
  parser.add_argument("--city", required=True, help=(f'city as listed in {DEFAULT_CITIES_PATH.name} '
                                                     '(e.g. "Helsinki, FI" or Helsinki,FI)'))
  parser.add_argument("--start", required=True, help="first month of the 12-month span, e.g. 2026-06")
  parser.add_argument("--month", choices=("amanta", "purnimanta"), default="amanta",
                      help="amānta (default) or pūrṇimānta month labels")
  parser.add_argument(
    "--ayanamsa", "--coordinate-selection", dest="ayanamsa", default="citra",
    help=("ayanamsa key (citra / true_chitrapaksha / revati / krishnamurti / "
          "raman / pushya / mula / tropical)"))
  parser.add_argument("--output", help="output PDF path")
  parser.add_argument("--festivals", help=f"path to a festivals.cfg (default: {DEFAULT_FESTIVALS_PATH.name})")
  return parser


def main(argv=None):
  parser = argument_parser()
  args = parser.parse_args(argv)
  coordinate_selection = require_coordinate_selection(args.ayanamsa)
  start_year, start_month = require_start_month(args.start)
  location = load_location(args.city)
  if args.output:
    output_path = Path(args.output)
  else:
    output_path = default_monthly_output_path(location, start_year, start_month, month_system=args.month,
                                              coordinate_selection=coordinate_selection)
  result = build_monthly_pdf(location, start_year, start_month, output_path, festivals_path=args.festivals,
                             month_system=args.month, coordinate_selection=coordinate_selection)
  print(f"Wrote {result}")
  return 0


if __name__ == "__main__":
  sys.exit(main())
