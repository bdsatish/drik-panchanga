#!/usr/bin/env python3
"""Generate a compact one-page panchanga calendar for any listed city."""

import argparse
import calendar
import json
import re
from collections import namedtuple as struct
from datetime import date as CivilDate
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

from festival_rules import (DayRecord, ekadashi_dates_from_records, find_local_eclipses, jd_to_local_civil_date,
                            jd_to_local_datetime, julian_day_from_datetime, load_festival_selection, resolve_festivals,
                            sankranti_raasi_by_date)
import panchanga

MONTH_COUNT = 14
DEFAULT_CITIES_PATH = Path(__file__).with_name("cities.json")
DEFAULT_FESTIVALS_PATH = Path(__file__).with_name("festivals.cfg")
DEFAULT_NAMES_PATH = Path(__file__).with_name("sanskrit_names.json")
FOOTER_FESTIVAL_SLOTS = 30  # 6 columns x 5 rows in draw_page_footer
FOOTER_KEY_FONT_MAX = 5.5
FOOTER_KEY_FONT_MIN = 3.8
FOOTER_KEY_LINE_HEIGHT = 6.5  # line spacing
FOOTER_KEY_TOP = 44.0  # baseline of first muted key line below festivals
RULESET_VERSION = "Udaya-Vyapini-1.1"
LAYOUT_VERSION = "A4-1.20"
PDF_AUTHOR = "Satish BD"
PDF_AUTHOR_EMAIL = "bdsatish@gmail.com"
PDF_COPYRIGHT = ("Copyright © Satish BD. Licensed under the GNU Affero GPL "
                 "version 3 (or later).")
PDF_SOURCE_URL = "https://github.com/bdsatish/drik-panchanga"

# ReportLab font names after ensure_pdf_fonts() registers IndUni-H.
PDF_FONT = "Panchanga"
PDF_FONT_BOLD = "Panchanga-Bold"
PDF_FONT_ITALIC = "Panchanga-Italic"
PDF_FONT_BOLD_ITALIC = "Panchanga-BoldItalic"
# Vendored TrueType Collection: Regular / Bold / Oblique / BoldOblique.
PDF_FONT_TTC = Path(__file__).resolve().parent / "fonts" / "IndUni-H.ttc"
PDF_FONT_TTC_INDICES = (0, 1, 2, 3)
_pdf_fonts_registered = False

# PDF layout proportions. Tweak these together.
MONTH_HEADER_HEIGHT = 20
COLUMN_HEADER_HEIGHT = 15
ROW_HEIGHT = 13.7
TITHI_COLUMN_RATIO = 0.34
NAKSHATRA_COLUMN_RATIO = 0.34
YOGA_COLUMN_RATIO = 0.32
TITHI_UNDERLINE_RATIO = 0.50
TITHI_UNDERLINE_LEFT_PADDING = 3.0
EKADASHI_UNDERLINE_RATIO = TITHI_UNDERLINE_RATIO  # Backward-compatible alias.

Location = struct('Location', ['name', 'latitude', 'longitude', 'timezone_name'])

INK = HexColor("#172033")
MUTED = HexColor("#465466")
ACCENT = HexColor("#263F73")
KRSNA_INK = HexColor("#2A303C")
GRID = HexColor("#CBD3DF")
MONTH_DIVIDER = HexColor("#AAB5C4")
ALT_ROW = HexColor("#F4F7FA")
SUNDAY_MARK = HexColor("#C94B40")
MISSING_ROW = HexColor("#ECEFF3")
ADHIKA_ROW = HexColor("#FFF0C7")
ADHIKA_INK = HexColor("#875A00")
MASA_START_ROW = HexColor("#C7E8CF")
MASA_START_INK = HexColor("#185C2A")
SANKRANTI_ROW = HexColor("#FDE8D4")
SANKRANTI_INK = HexColor("#9A4E12")
FESTIVAL_INK = HexColor("#9A3154")
EKADASHI_MARK = HexColor("#168078")
ECLIPSE_MARK = HexColor("#8B4518")


def _load_json(path):
  with path.open(encoding="utf-8") as source:
    return json.load(source)


_SANSKRIT_NAMES = None
_CITY_LOCATIONS = None


def sanskrit_names():
  global _SANSKRIT_NAMES
  if _SANSKRIT_NAMES is None:
    _SANSKRIT_NAMES = _load_json(DEFAULT_NAMES_PATH)
  return _SANSKRIT_NAMES


def city_locations():
  """Parsed ``cities.json``; cached so web/CLI requests do not re-read 1.3 MB."""
  global _CITY_LOCATIONS
  if _CITY_LOCATIONS is not None:
    return _CITY_LOCATIONS
  path = DEFAULT_CITIES_PATH
  if not path.exists():
    raise ValueError(f"Cities file does not exist: {path}")
  with path.open(encoding="utf-8") as source:
    locations = json.load(source)
  if not isinstance(locations, dict):
    raise ValueError("cities.json must contain an object keyed by city")
  _CITY_LOCATIONS = locations
  return _CITY_LOCATIONS


def _numbered_iast_names(mapping, width=None):
  items = sorted(mapping.items(), key=lambda item: int(item[0]))
  if width is None:
    return [f"{key} {name}" for key, name in items]
  return [f"{int(key):0{width}d} {name}" for key, name in items]


def tithi_key_line():
  """Footer key for the T column and related T-cell marks."""
  return ("T: 01-15; Sukla = upright bold, Krsna = bold italic. Tiny red numbers "
          "refer to the festival key. Sundays have a red right edge; Ekadashi "
          "upavasa has a teal T-cell underline.")


def masa_key_line():
  names = ", ".join(_numbered_iast_names(sanskrit_names()["masas"]))
  return ("Māsa: green T-cell with upper-left badge marks its first visible tithi; "
          f"gold fill denotes adhika. {names}. "
          "Display māsa follows amānta or pūrṇimānta; festival dates internally use amānta rules.")


def sankranti_key_line():
  """Footer key for solar saṅkrānti markers (rāśi 1–12)."""
  zodiac = sanskrit_names()["zodiac"]
  names = ", ".join(f"{index} {zodiac[str(index - 1)].capitalize()}" for index in range(1, 13))
  return ("Saṅkrānti: peach N-cell top-right number is the new solar rāśi; "
          "the rolling solar-day count resets at each saṅkrānti, with N-cell "
          "markers at 7, 14, 21, and 28. "
          f"{names}.")


def nakshatra_key_line():
  names = _numbered_iast_names(sanskrit_names()["nakshatras"])
  return "N: " + ", ".join(names)


def yoga_key_line():
  names = _numbered_iast_names(sanskrit_names()["yogas"], width=2)
  return "Y: " + ", ".join(names)


def ensure_pdf_fonts():
  """Register IndUni-H faces from the vendored ``.ttc`` for all PDF text."""
  global _pdf_fonts_registered
  if _pdf_fonts_registered:
    return
  from reportlab.pdfbase import pdfmetrics
  from reportlab.pdfbase.ttfonts import TTFont

  if not PDF_FONT_TTC.is_file():
    raise FileNotFoundError(f"Missing PDF font collection: {PDF_FONT_TTC}")
  ttc = str(PDF_FONT_TTC)
  names = (PDF_FONT, PDF_FONT_BOLD, PDF_FONT_ITALIC, PDF_FONT_BOLD_ITALIC)
  for name, index in zip(names, PDF_FONT_TTC_INDICES):
    pdfmetrics.registerFont(TTFont(name, ttc, subfontIndex=index))
  pdfmetrics.registerFontFamily(PDF_FONT, normal=PDF_FONT, bold=PDF_FONT_BOLD, italic=PDF_FONT_ITALIC,
                                boldItalic=PDF_FONT_BOLD_ITALIC)
  _pdf_fonts_registered = True


def embed_pdf_metadata(pdf, title, subject, ruleset_version, coordinate_selection="citra"):
  """Set Info dictionary fields, including custom copyright/email/URL keys."""
  from reportlab.pdfbase.pdfdoc import (PDFDate, PDFDictionary, PDFName, PDFString)

  coord_label = coordinate_selection_label(coordinate_selection)
  pdf.setTitle(title)
  pdf.setAuthor(PDF_AUTHOR)
  pdf.setSubject(subject)
  pdf.setCreator(PDF_SOURCE_URL)
  pdf.setKeywords(f"ruleset={ruleset_version}; layout={LAYOUT_VERSION}; "
                  f"ayanamsa={coord_label}; sweph={panchanga.sweph_version()}; "
                  f"author-email={PDF_AUTHOR_EMAIL}; "
                  f"copyright={PDF_COPYRIGHT}; url={PDF_SOURCE_URL}")

  info = pdf._doc.info
  info.author_email = PDF_AUTHOR_EMAIL
  info.copyright = PDF_COPYRIGHT
  info.url = PDF_SOURCE_URL

  # ReportLab has no public API for custom Info keys (AuthorEmail, Copyright,
  # URL). Replace info.format so those fields are written into the PDF.
  def format_info(document):
    return PDFDictionary({
      "Title": PDFString(info.title),
      "Author": PDFString(info.author),
      "AuthorEmail": PDFString(info.author_email),
      "Copyright": PDFString(info.copyright),
      "URL": PDFString(info.url),
      "ModDate": PDFDate(ts=document._timeStamp, dateFormatter=info._dateFormatter),
      "CreationDate": PDFDate(ts=document._timeStamp, dateFormatter=info._dateFormatter),
      "Producer": PDFString(info.producer),
      "Creator": PDFString(info.creator),
      "Subject": PDFString(info.subject),
      "Keywords": PDFString(info.keywords),
      "Trapped": PDFName(info.trapped)
    }).format(document)

  info.format = format_info


def month_range(start_year, start_month, count=MONTH_COUNT):
  months = []
  year, month = start_year, start_month
  for _ in range(count):
    months.append((year, month))
    if month == 12:
      year, month = year + 1, 1
    else:
      month += 1
  return months


def parse_start_month(value):
  match = re.fullmatch(r"(\d{4})-(\d{2})", value)
  if not match:
    raise ValueError("start month must use YYYY-MM format")
  year, month = (int(part) for part in match.groups())
  if not 1 <= month <= 12:
    raise ValueError("start month must be between 01 and 12")
  return year, month


def parse_month_system(text):
  """Return ``True`` for amānta, ``False`` for pūrṇimānta.

    Accepts ``amanta`` / ``purnimanta``. Also ``true``/``false`` and ``1``/``0``
    for the amānta flag. Both systems are first-class for display; omit or pass
    ``amanta`` when unspecified.
    """
  value = (text or "amanta").strip().casefold()
  if value in {"amanta", "āmānta", "amaanta", "true", "1", "yes", "on"}:
    return True
  if value in {"purnimanta", "pūrṇimānta", "poornimanta", "false", "0", "no", "off"}:
    return False
  raise ValueError("Month system must be 'amanta' or 'purnimanta'.")


def month_system_label(amanta):
  return "Amānta" if amanta else "Pūrṇimānta"


# Web/CLI sidereal ayanāṃśa choices → panchanga.set_chosen_ayanamsa() keys.
AYANAMSA_OPTIONS = {
  "citra": "Chitra-paksha",
  "revati": "Revati-paksha",
  "rohini": "Rohini-paksha",
  "pushya": "Pushya-paksha",
  "mula": "Mula-paksha",
  "krishnamurti": "Krishnamurti",
  "raman": "Raman"
}

COORDINATE_OPTIONS = {
  **AYANAMSA_OPTIONS,
  "tropical": "Tropical (Sāyana)",
}


def parse_coordinate_selection(text):
  """Return a canonical sidereal ayanāṃśa key or ``tropical``."""
  value = (text or "citra").strip().casefold().replace(" ", "_").replace("-", "_")
  aliases = {
    "citra": "citra",
    "citra_paksha": "citra",
    "citrapaksha": "citra",
    "chitra_paksha": "citra",
    "chitrapaksha": "citra",
    "true_citra": "citra",
    "truecitra": "citra",
    "revati": "revati",
    "revati_paksha": "revati",
    "revatipaksha": "revati",
    "true_revati": "revati",
    "truerevati": "revati",
    "rohini": "rohini",
    "true_rohini": "rohini",
    "truerohini": "rohini",
    "rohini_paksha": "rohini",
    "rohinipaksha": "rohini",
    "pushya": "pushya",
    "pushya_paksha": "pushya",
    "pushyapaksha": "pushya",
    "true_pushya": "pushya",
    "truepushya": "pushya",
    "mula": "mula",
    "true_mula": "mula",
    "truemula": "mula",
    "krishnamurti": "krishnamurti",
    "kp": "krishnamurti",
    "raman": "raman",
    "tropical": "tropical",
    "sayana": "tropical",
  }
  if value not in aliases:
    allowed = ", ".join(COORDINATE_OPTIONS)
    raise ValueError(f"Coordinate selection must be one of: {allowed}.")
  return aliases[value]


def ayanamsa_label(key):
  if key == "tropical":
    raise ValueError("Tropical mode has no ayanāṃśa label.")
  return AYANAMSA_OPTIONS[key]


def coordinate_selection_label(selection):
  return COORDINATE_OPTIONS[selection]


def sun_altitude_at_local_noon(year, month, day, place):
  """True solar altitude in degrees at local civil noon."""
  swe = panchanga.swe
  noon_ut = swe.julday(year, month, day, 12.0) - place.timezone / 24.0
  xx, _retflag = swe.calc_ut(noon_ut, swe.SUN)
  _azimuth, true_altitude, _apparent = swe.azalt(noon_ut, swe.ECL2HOR, (place.longitude, place.latitude, 0.0), 0, 0,
                                                 [xx[0], xx[1], xx[2]])
  return true_altitude


def classify_missing_sunrise(year, month, day, place):
  """Why local sunrise is unavailable: ``polar_night``, ``polar_day``, or ``no_sunrise``."""
  altitude = sun_altitude_at_local_noon(year, month, day, place)
  if altitude > 0.5:
    return "polar_day"
  if altitude < -0.5:
    return "polar_night"
  return "no_sunrise"


def format_sunrise_unavailable_message(location_name, year, month, day, place):
  """Human-readable error when Hindu sunrise-day reckoning cannot start."""
  kind = classify_missing_sunrise(year, month, day, place)
  date_label = f"{day:02d}/{month:02d}/{year}"
  lat = abs(place.latitude)
  hemisphere = "N" if place.latitude >= 0 else "S"
  if kind == "polar_night":
    detail = (f"polar night — the Sun stays below the horizon "
              f"(about {lat:.1f}°{hemisphere})")
  elif kind == "polar_day":
    detail = (f"midnight sun — the Sun stays above the horizon "
              f"(about {lat:.1f}°{hemisphere})")
  else:
    detail = (f"no local sunrise/sunset "
              f"(about {lat:.1f}°{hemisphere}; common near the polar circles)")
  return (f"Cannot compute sunrise panchanga for {location_name} on {date_label}: "
          f"{detail}. Hindu civil days begin at local sunrise — choose a date with a "
          f"sunrise, or a city at lower latitude.")


def require_local_sunrise(jd, place, location_name, year, month, day):
  """Return ``panchanga.sunrise`` result, or raise ``RuntimeError`` with context."""
  try:
    sunrise = panchanga.sunrise(jd, place)
    sunrise_jd = sunrise[0]
    if not jd - 1 <= sunrise_jd <= jd + 2:
      raise RuntimeError("no local sunrise")
    return sunrise
  except Exception as error:
    message = format_sunrise_unavailable_message(location_name, year, month, day, place)
    raise RuntimeError(message) from error


def city_base_name(key):
  """Return the place name from a ``Name, ISO`` cities.json key.

    Keys always use a single comma (before the country code); place names
    themselves never contain commas.
    """
  name, sep, _country = (key or "").rpartition(", ")
  return name if sep else key


def normalize_city_query(city):
  """Canonicalize user input toward ``Name, ISO`` (space after comma, upper ISO).

    Accepts ``Helsinki, FI``, ``Helsinki,FI``, and mixed whitespace/case.
    Place names never contain commas, so the last ``, XX`` is always the country.
    """
  query = " ".join((city or "").split())
  match = re.fullmatch(r"([^,]+),\s*([A-Za-z]{2})", query)
  if match:
    return f"{match.group(1).rstrip()}, {match.group(2).upper()}"
  return query


def resolve_city_key(city, locations):
  """Resolve a user city string to a cities.json key.

    Accepts full keys (``Sydney, AU`` or ``Sydney,AU``) or a bare name when
    it is unique.
    """
  query = normalize_city_query(city)
  if not query:
    raise ValueError("City is required.")

  folded = query.casefold()
  exact = [name for name in locations if name.casefold() == folded]
  if len(exact) == 1:
    return exact[0]
  if len(exact) > 1:
    raise ValueError(f"City {city!r} matches multiple keys: {', '.join(sorted(exact))}")

  bare = [name for name in locations if city_base_name(name).casefold() == folded]
  if len(bare) == 1:
    return bare[0]
  if len(bare) > 1:
    options = ", ".join(sorted(bare, key=str.casefold))
    raise ValueError(f"City {city!r} is ambiguous; use a country code, e.g. one of: {options}")

  import difflib

  suggestions = difflib.get_close_matches(query, list(locations), n=5, cutoff=0.6)
  if not suggestions:
    # Also suggest by bare-name similarity against unique bases.
    bases = sorted({city_base_name(name) for name in locations}, key=str.casefold)
    near = difflib.get_close_matches(query, bases, n=5, cutoff=0.6)
    expanded = []
    for base in near:
      matches = []
      for name in locations:
        if city_base_name(name).casefold() == base.casefold():
          matches.append(name)
      matches.sort(key=str.casefold)
      expanded.extend(matches)
    suggestions = expanded[:8]
  message = f"City {city!r} was not found in {DEFAULT_CITIES_PATH.name}"
  if suggestions:
    message += f". Close matches: {', '.join(suggestions)}"
  raise ValueError(message)


def load_location(city):
  """Resolve ``city`` against ``cities.json`` and return a ``Location``."""
  locations = city_locations()
  name = resolve_city_key(city, locations)
  record = locations[name]
  return Location(name, record["latitude"], record["longitude"], record["timezone"])


def format_local_hm(jd, timezone_name):
  """Format a UT Julian day as local ``HH:MM``, rounded to the nearest minute."""
  local = jd_to_local_datetime(jd, timezone_name)
  total_minutes = int(round(local.hour * 60 + local.minute + local.second / 60.0))
  total_minutes %= 24 * 60
  return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"


def format_eclipse_line(eclipses, timezone_name, sunrise_by_date=None):
  """Compact footer line for eclipses at maximum time.

    Optional ``sunrise_by_date`` adds that date's local sunrise to each entry.
    """
  if not eclipses:
    return "Eclipses: None"
  sunrise_by_date = sunrise_by_date or {}
  parts = []
  for kind, phase, maximum_jd in eclipses:
    civil = jd_to_local_civil_date(maximum_jd, timezone_name)
    part = (f"{kind} {calendar.month_abbr[civil.month]} {civil.day:02d} "
            f"({phase}) maximum phase at {format_local_hm(maximum_jd, timezone_name)}")
    sunrise_jd = sunrise_by_date.get(civil)
    if sunrise_jd is not None:
      part += f", sunrise {format_local_hm(sunrise_jd, timezone_name)}"
    parts.append(part)
  return "Eclipses: " + "; ".join(parts) + ". Eclipses have a brown wavy underline below Tithi."


def eclipse_civil_dates(eclipses, timezone_name):
  """Local civil date of each eclipse maximum."""
  return {jd_to_local_civil_date(maximum_jd, timezone_name) for _kind, _phase, maximum_jd in eclipses}


def tithi_underline_bounds(x, tithi_column_width):
  """Return the shared left edge and width for T-cell underlines."""
  width = tithi_column_width * TITHI_UNDERLINE_RATIO
  return x + TITHI_UNDERLINE_LEFT_PADDING, width


def draw_tithi_underline(pdf, x, row_y, tithi_column_width, color, wavy=False):
  """Draw a shared-geometry solid or wavy T-cell underline."""
  left, underline_width = tithi_underline_bounds(x, tithi_column_width)
  if not wavy:
    pdf.setFillColor(color)
    pdf.rect(left, row_y + 0.6, underline_width, 1.2, stroke=0, fill=1)
    return

  pdf.setStrokeColor(color)
  pdf.setLineWidth(0.65)
  right = left + underline_width
  baseline = row_y + 1.7
  step = underline_width / 6
  amplitude = 0.8
  path = pdf.beginPath()
  path.moveTo(left, baseline)
  for index in range(6):
    x0 = left + index * step
    direction = amplitude if index % 2 == 0 else -amplitude
    path.curveTo(x0 + step / 3, baseline + direction, x0 + 2 * step / 3, baseline + direction, x0 + step, baseline)
  pdf.drawPath(path, stroke=1, fill=0)


def draw_eclipse_mark(pdf, x, row_y, tithi_column_width):
  """Half-width wavy underline below Tithi for a locally visible eclipse."""
  draw_tithi_underline(pdf, x, row_y, tithi_column_width, ECLIPSE_MARK, wavy=True)


def draw_sankranti_mark(pdf, x, row_y, raasi, cell_width):
  """Solar rāśi number in a cell's top-right corner."""
  pdf.setFillColor(SANKRANTI_INK)
  pdf.setFont(PDF_FONT_BOLD, 5.0)
  pdf.drawRightString(x + cell_width - 1.0, row_y + 8.2, str(int(raasi)))


def draw_solar_day_mark(pdf, x, row_y, solar_day, cell_width):
  """Solar week-boundary day in a cell's top-right corner."""
  pdf.setFillColor(ACCENT)
  pdf.setFont(PDF_FONT_BOLD, 5.0)
  pdf.drawRightString(x + cell_width - 1.0, row_y + 8.2, str(int(solar_day)))


def solar_dates_by_date(records):
  """Map civil date → (solar rāśi, solar day, is-saṅkrānti)."""
  result = {}
  previous_raasi = None
  solar_day = 0
  for record in sorted(records, key=lambda record: record.civil_date):
    raasi = int(panchanga.raasi(record.sunrise_jd))
    is_sankranti = previous_raasi is not None and raasi != previous_raasi
    solar_day = 1 if is_sankranti else solar_day + 1
    result[record.civil_date] = (raasi, solar_day, is_sankranti)
    previous_raasi = raasi
  return result


def local_range_jds(start_year, start_month, end_year, end_month, timezone_name):
  """UT Julian days covering the printed Gregorian months in local civil time."""
  timezone_info = ZoneInfo(timezone_name)
  last_day = calendar.monthrange(end_year, end_month)[1]
  start_local = datetime(start_year, start_month, 1, 0, 0, 0, tzinfo=timezone_info)
  end_local = datetime(end_year, end_month, last_day, 23, 59, 59, tzinfo=timezone_info)
  return julian_day_from_datetime(start_local), julian_day_from_datetime(end_local)


def timezone_hours(timezone, year, month, day):
  """Return the location's UTC offset, including daylight-saving time."""
  local_noon = datetime(year, month, day, 12, tzinfo=timezone)
  return local_noon.utcoffset().total_seconds() / 3600


def tithi_code(tithi_number):
  if tithi_number <= 15:
    return f"S{tithi_number}"
  return f"K{tithi_number - 15}"


def masa_code(masa_number, is_adhika):
  return f"A{masa_number}" if is_adhika else str(masa_number)


def tithi_display_parts(tithi):
  """Return ``(number_text, is_sukla)`` for a single ``S*`` / ``K*`` code."""
  return f"{int(tithi[1:]):02d}", tithi.startswith("S")


def tithi_ink(is_sukla, is_masa_start=False, is_adhika=False):
  """Ink for the T cell: masa-start overrides, else Sukla blue / Krsna dark."""
  if is_masa_start and is_adhika:
    return ADHIKA_INK
  if is_masa_start:
    return MASA_START_INK
  return ACCENT if is_sukla else KRSNA_INK


def tithi_font(is_sukla):
  """Font for the T cell: upright bold for Sukla, bold italic for Krsna."""
  return PDF_FONT_BOLD if is_sukla else PDF_FONT_BOLD_ITALIC


def daily_records(months, location):
  """Canonical amānta sunrise records for ordered Gregorian ``months``."""
  result = []
  timezone = ZoneInfo(location.timezone_name)
  for year, month in months:
    for day in range(1, calendar.monthrange(year, month)[1] + 1):
      date = panchanga.Date(year, month, day)
      place = panchanga.Place(location.latitude, location.longitude, timezone_hours(timezone, year, month, day))
      jd = panchanga.gregorian_to_jd(date)
      try:
        sunrise_jd = require_local_sunrise(jd, place, location.name, year, month, day)[0]
        tithi_number = panchanga.tithi(jd, place)[0]
        nakshatra_number = panchanga.nakshatra(jd, place)[0]
        yoga_number = panchanga.yoga(jd, place)[0]
        masa_number, is_adhika = panchanga.masa(jd, place, amanta=True, tithi_number=tithi_number)
      except RuntimeError:
        raise
      except Exception as error:
        raise RuntimeError(format_sunrise_unavailable_message(location.name, year, month, day, place) +
                           f" ({error})") from error
      result.append(
        DayRecord(CivilDate(year, month, day), tithi_code(tithi_number), nakshatra_number, yoga_number,
                  masa_code(masa_number, is_adhika), is_adhika, sunrise_jd - place.timezone / 24))
  return result


def display_masa(record, amanta=True):
  """Māsa code displayed for a canonical amānta record."""
  masa_number = int(record.masa.lstrip("A"))
  if not amanta and not record.is_adhika and record.tithi.startswith("K"):
    masa_number = masa_number % 12 + 1
  return masa_code(masa_number, record.is_adhika)


def masa_badges_by_date(records, amanta=True):
  """Map each first visible date of a display māsa to its badge code."""
  badges = {}
  previous_masa = None
  for record in records:
    masa = display_masa(record, amanta=amanta)
    if masa != previous_masa:
      badges[record.civil_date] = masa
    previous_masa = masa
  return badges


def draw_centered(pdf, text, center_x, baseline_y, font, size, color=INK):
  pdf.setFont(font, size)
  pdf.setFillColor(color)
  pdf.drawCentredString(center_x, baseline_y, text)


def fitted_font_size(pdf, text, font, maximum, minimum, available_width, context):
  """Shrink text to fit; raise if it still overflows at ``minimum``."""
  natural_width = pdf.stringWidth(text, font, maximum)
  if natural_width <= available_width:
    size = maximum
  else:
    size = max(minimum, maximum * available_width / natural_width)
  if pdf.stringWidth(text, font, size) > available_width + 0.01:
    raise ValueError(f"{context} is too long to fit: {text!r}")
  return size


def draw_day_column(pdf, x, top, width):
  header_height = MONTH_HEADER_HEIGHT + COLUMN_HEADER_HEIGHT

  pdf.setFillColor(ACCENT)
  pdf.rect(x, top - header_height, width, header_height, stroke=0, fill=1)
  draw_centered(pdf, "DAY", x + width / 2, top - 21, PDF_FONT_BOLD, 7.2, white)

  rows_top = top - header_height
  for index in range(31):
    row_y = rows_top - (index + 1) * ROW_HEIGHT
    pdf.setFillColor(ALT_ROW if index % 2 else white)
    pdf.rect(x, row_y, width, ROW_HEIGHT, stroke=0, fill=1)
    draw_centered(pdf, str(index + 1), x + width / 2, row_y + 4.1, PDF_FONT, 7.4, INK)

  bottom = rows_top - 31 * ROW_HEIGHT
  pdf.setStrokeColor(GRID)
  pdf.setLineWidth(0.4)
  pdf.rect(x, bottom, width, top - bottom, stroke=1, fill=0)
  for index in range(32):
    y = rows_top - index * ROW_HEIGHT
    pdf.line(x, y, x + width, y)


def draw_month(pdf, year, month, records_by_date, masa_badges, festivals_by_date, ekadashi_dates, eclipse_dates,
               sankranti_by_date, solar_by_date, x, top, width):
  tithi_column_width = width * TITHI_COLUMN_RATIO
  nakshatra_column_width = width * NAKSHATRA_COLUMN_RATIO
  yoga_column_width = width * YOGA_COLUMN_RATIO

  pdf.setFillColor(ACCENT)
  pdf.rect(x, top - MONTH_HEADER_HEIGHT, width, MONTH_HEADER_HEIGHT, stroke=0, fill=1)
  draw_centered(pdf, f"{calendar.month_abbr[month]} '{str(year)[2:]}", x + width / 2, top - 14, PDF_FONT_BOLD, 8.0,
                white)

  header_top = top - MONTH_HEADER_HEIGHT
  pdf.setFillColor(HexColor("#E2E7EF"))
  pdf.rect(x, header_top - COLUMN_HEADER_HEIGHT, width, COLUMN_HEADER_HEIGHT, stroke=0, fill=1)

  centers = (x + tithi_column_width / 2, x + tithi_column_width + nakshatra_column_width / 2,
             x + tithi_column_width + nakshatra_column_width + yoga_column_width / 2)
  for label, center in zip(("T", "N", "Y"), centers):
    draw_centered(pdf, label, center, header_top - 10.5, PDF_FONT_BOLD, 7.0, MUTED)

  rows_top = header_top - COLUMN_HEADER_HEIGHT
  for index in range(31):
    day = index + 1
    civil_date = (CivilDate(year, month, day) if day <= calendar.monthrange(year, month)[1] else None)
    record = records_by_date.get(civil_date)
    row_y = rows_top - (index + 1) * ROW_HEIGHT
    is_sunday = False
    if record is None:
      pdf.setFillColor(MISSING_ROW)
    else:
      weekday = datetime(year, month, day).weekday()
      is_sunday = weekday == calendar.SUNDAY
      if index % 2:
        pdf.setFillColor(ALT_ROW)
      else:
        pdf.setFillColor(white)
    pdf.rect(x, row_y, width, ROW_HEIGHT, stroke=0, fill=1)

    if record is None:
      continue

    tithi = record.tithi
    nakshatra = record.nakshatra
    yoga = record.yoga
    masa_badge = masa_badges.get(civil_date)
    is_masa_start = masa_badge is not None
    is_adhika = record.is_adhika
    tithi_display, is_sukla = tithi_display_parts(tithi)
    sankranti_raasi = sankranti_by_date.get(civil_date)
    solar_info = solar_by_date.get(civil_date)
    solar_day = solar_info[1] if solar_info is not None else None
    if is_masa_start:
      pdf.setFillColor(ADHIKA_ROW if is_adhika else MASA_START_ROW)
      pdf.rect(x, row_y, tithi_column_width, ROW_HEIGHT, stroke=0, fill=1)
      pdf.setFillColor(ADHIKA_INK if is_adhika else MASA_START_INK)
      pdf.setFont(PDF_FONT_BOLD, 5.2)
      pdf.drawRightString(x + tithi_column_width - 1.0, row_y + 8.2, masa_badge.removeprefix("A"))
    if sankranti_raasi is not None:
      # Solar markers use the N-cell so the T-cell stays clear for lunar marks.
      pdf.setFillColor(SANKRANTI_ROW)
      pdf.rect(x + tithi_column_width, row_y, nakshatra_column_width, ROW_HEIGHT, stroke=0, fill=1)
    if is_sunday:
      pdf.setFillColor(SUNDAY_MARK)
      pdf.rect(x + width - 1.6, row_y, 1.6, ROW_HEIGHT, stroke=0, fill=1)
    if civil_date in ekadashi_dates:
      draw_tithi_underline(pdf, x, row_y, tithi_column_width, EKADASHI_MARK)
    if sankranti_raasi is not None:
      draw_sankranti_mark(pdf, x + tithi_column_width, row_y, sankranti_raasi, nakshatra_column_width)
    if solar_day is not None:
      if sankranti_raasi is None and solar_day % 7 == 0:
        draw_solar_day_mark(pdf, x + tithi_column_width, row_y, solar_day, nakshatra_column_width)
    if civil_date in eclipse_dates:
      draw_eclipse_mark(pdf, x, row_y, tithi_column_width)
    festival_numbers = festivals_by_date.get(civil_date, ())
    baseline = row_y + (3.0 if festival_numbers else 4.1)
    pdf.setFont(tithi_font(is_sukla), 7.4)
    pdf.setFillColor(tithi_ink(is_sukla, is_masa_start, is_adhika))
    pdf.drawString(x + 3.0, baseline, tithi_display)
    pdf.setFont(PDF_FONT, 7.3)
    pdf.setFillColor(INK)
    pdf.drawString(x + tithi_column_width + 3.0, baseline, f"{nakshatra:02d}")
    pdf.drawString(x + tithi_column_width + nakshatra_column_width + 3.0, baseline, f"{yoga:02d}")
    if festival_numbers:
      pdf.setFillColor(FESTIVAL_INK)
      marker_size = 5.0 if len(festival_numbers) <= 2 else 4.0
      marker_spacing = 4.8 if len(festival_numbers) <= 2 else 3.5
      marker_bottom = row_y + 1.8
      pdf.setFont(PDF_FONT_BOLD, marker_size)
      for marker_index, number in enumerate(festival_numbers):
        pdf.drawRightString(x + tithi_column_width - 1.0, marker_bottom + marker_index * marker_spacing, str(number))

  bottom = rows_top - 31 * ROW_HEIGHT
  pdf.setStrokeColor(GRID)
  pdf.setLineWidth(0.4)
  pdf.rect(x, bottom, width, top - bottom, stroke=1, fill=0)
  pdf.line(x + tithi_column_width, bottom, x + tithi_column_width, header_top)
  pdf.line(x + tithi_column_width + nakshatra_column_width, bottom, x + tithi_column_width + nakshatra_column_width,
           header_top)
  for index in range(32):
    y = rows_top - index * ROW_HEIGHT
    pdf.line(x, y, x + width, y)
  pdf.setStrokeColor(MONTH_DIVIDER)
  pdf.setLineWidth(0.9)
  pdf.line(x, bottom, x, top)


def month_span_label(months):
  start_year, start_month = months[0]
  end_year, end_month = months[-1]
  return (f"{calendar.month_name[start_month]} {start_year} - "
          f"{calendar.month_name[end_month]} {end_year}")


def kali_ahargana_range(months):
  """Return Kali Ahargana values for the first and last printed civil dates."""
  start_year, start_month = months[0]
  end_year, end_month = months[-1]
  start_jd = panchanga.gregorian_to_jd(panchanga.Date(start_year, start_month, 1))
  end_day = calendar.monthrange(end_year, end_month)[1]
  end_jd = panchanga.gregorian_to_jd(panchanga.Date(end_year, end_month, end_day))
  return int(panchanga.ahargana(start_jd)), int(panchanga.ahargana(end_jd))


def calendar_year_label(records, amanta=True):
  """Return era and samvatsara labels for a representative calendar month."""
  representative = records[len(records) // 2]
  civil = representative.civil_date
  masa_num = int(display_masa(representative, amanta=amanta).lstrip("A"))
  jd = panchanga.gregorian_to_jd(panchanga.Date(civil.year, civil.month, civil.day))
  kali_year, saka_year, vikrama_year = panchanga.elapsed_year(jd, masa_num)
  names = sanskrit_names()["samvats"]
  saka_name = names[str(panchanga.samvatsara(jd, masa_num))]
  vikrama_name = names[str(panchanga.samvatsara_north_modern(jd, masa_num))]
  return (f"{saka_year} {saka_name} | "
          f"{vikrama_year} {vikrama_name} | "
          f"{kali_year} Kali (elapsed)")


def coordinate_label(value, positive, negative):
  direction = positive if value >= 0 else negative
  return f"{abs(value):.5f} {direction}"


def draw_page_header(pdf, location, months, ruleset_version, amanta=True, coordinate_selection="citra",
                     calendar_years=None, kali_ahargana=None):
  page_width, page_height = landscape(A4)
  title = f"{location.name} Panchanga: {month_span_label(months)}"
  pdf.setFillColor(INK)
  title_size = fitted_font_size(pdf, title, PDF_FONT_BOLD, 11, 8, page_width - 36, "page title")
  pdf.setFont(PDF_FONT_BOLD, title_size)
  pdf.drawString(18, page_height - 20, title)
  pdf.setFillColor(MUTED)
  subtitle_parts = ["At local sunrise"]
  if calendar_years:
    subtitle_parts.append(calendar_years)
  masa_label = "Amanta" if amanta else "Purnimanta"
  if coordinate_selection == "tropical":
    subtitle_parts.append("Tropical (Sāyana)")
  else:
    ayan_label = ayanamsa_label(coordinate_selection)
    subtitle_parts.append(f"{ayan_label} ayanamsa")
  subtitle_parts.extend((f"{masa_label} masa", f"{coordinate_label(location.latitude, 'N', 'S')}, "
                         f"{coordinate_label(location.longitude, 'E', 'W')}", f"{location.timezone_name} civil time"))
  if kali_ahargana is not None:
    start_ahargana, end_ahargana = kali_ahargana
    subtitle_parts.append(f"Kali Ahargana: {start_ahargana} - {end_ahargana}")
  subtitle = " | ".join(subtitle_parts)
  subtitle_size = fitted_font_size(pdf, subtitle, PDF_FONT, 7.5, 5.0, page_width - 36, "page subtitle")
  pdf.setFont(PDF_FONT, subtitle_size)
  pdf.drawString(18, page_height - 31, subtitle)
  pdf.setFont(PDF_FONT, 4.7)
  pdf.drawRightString(page_width - 18, page_height - 19,
                      f"SwEph {panchanga.sweph_version()} | Ruleset: {ruleset_version} | Layout: {LAYOUT_VERSION}")


def draw_page_footer(pdf, festival_entries, eclipse_line="Eclipses: None"):
  if len(festival_entries) > FOOTER_FESTIVAL_SLOTS:
    raise ValueError(f"Festival footer holds at most {FOOTER_FESTIVAL_SLOTS} entries "
                     f"(6x5); got {len(festival_entries)}. Disable some festivals in "
                     "festivals.cfg or pass a smaller --festivals file.")

  pdf.setFillColor(FESTIVAL_INK)

  columns = 6
  rows = 5
  column_width = (landscape(A4)[0] - 36) / columns
  for index, (number, festival_date, name) in enumerate(festival_entries):
    column = index // rows
    row = index % rows
    marker = str(number)
    entry = f"{name}: {festival_date}"
    marker_size = 5.0
    marker_width = pdf.stringWidth(marker, PDF_FONT_BOLD, marker_size)
    marker_gap = 2.0
    entry_width = column_width - 4 - marker_width - marker_gap
    entry_size = fitted_font_size(pdf, entry, PDF_FONT, 7.5, 5.5, entry_width, f"festival entry {number}")
    entry_x = 18 + column * column_width
    entry_y = 86 - row * 8
    pdf.setFont(PDF_FONT_BOLD, marker_size)
    pdf.drawString(entry_x, entry_y + 2.0, marker)
    pdf.setFont(PDF_FONT, entry_size)
    pdf.drawString(entry_x + marker_width + marker_gap, entry_y, entry)

  pdf.setFillColor(MUTED)
  # Column order matches the grid (T, N, Y), then lunar māsa, then solar saṅkrānti.
  # Eclipse stays first; bold face works with MUTED (colour and weight are independent).
  key_lines = (tithi_key_line(), nakshatra_key_line(), yoga_key_line(), masa_key_line(), sankranti_key_line())
  page_width = landscape(A4)[0]
  available_width = page_width - 36
  eclipse_size = fitted_font_size(pdf, eclipse_line, PDF_FONT_BOLD, FOOTER_KEY_FONT_MAX, FOOTER_KEY_FONT_MIN,
                                  available_width, "eclipse footer")
  key_sizes = [eclipse_size]
  for index, line in enumerate(key_lines):
    key_sizes.append(
      fitted_font_size(pdf, line, PDF_FONT, FOOTER_KEY_FONT_MAX, FOOTER_KEY_FONT_MIN, available_width,
                       f"footer key line {index + 1}"))
  key_size = min(key_sizes)
  pdf.setFont(PDF_FONT_BOLD, key_size)
  pdf.drawString(18, FOOTER_KEY_TOP, eclipse_line)
  pdf.setFont(PDF_FONT, key_size)
  for index, line in enumerate(key_lines):
    pdf.drawString(18, FOOTER_KEY_TOP - (index + 1) * FOOTER_KEY_LINE_HEIGHT, line)


def build_pdf(location, start_year, start_month, output_path, festivals_path=None, month_system="amanta",
              coordinate_selection="citra"):
  """Build a calendar while holding coordinate state for the full document.

  Pattern: take ``coordinate_calculation_lock``, then call ``_build_pdf_unlocked``.
  The lock keeps ayanāṃśa / tropical mode stable for the whole PDF; the
  ``_unlocked`` helper holds the real work and must not be called alone from
  other threads.
  """
  with panchanga.coordinate_calculation_lock:
    return _build_pdf_unlocked(location, start_year, start_month, output_path, festivals_path=festivals_path,
                               month_system=month_system, coordinate_selection=coordinate_selection)


def _build_pdf_unlocked(location, start_year, start_month, output_path, festivals_path=None, month_system="amanta",
                        coordinate_selection="citra"):
  ensure_pdf_fonts()
  amanta = parse_month_system(month_system)
  panchanga.set_coordinate_selection(coordinate_selection)
  months = month_range(start_year, start_month)
  if start_month == 1:
    context_start = (start_year - 1, 12)
  else:
    context_start = (start_year, start_month - 1)
  context_months = month_range(*context_start, count=MONTH_COUNT + 2)
  context_records = daily_records(context_months, location)
  records_by_date = {record.civil_date: record for record in context_records}
  range_start = CivilDate(start_year, start_month, 1)
  end_year, end_month = months[-1]
  range_end = CivilDate(end_year, end_month, calendar.monthrange(end_year, end_month)[1])
  target_records = []
  for record in context_records:
    if range_start <= record.civil_date <= range_end:
      target_records.append(record)
  target_dates = {record.civil_date for record in target_records}
  festivals_path = Path(festivals_path) if festivals_path is not None else DEFAULT_FESTIVALS_PATH
  enabled_names = load_festival_selection(festivals_path)
  geopos = (location.longitude, location.latitude, 0.0)
  festivals_by_date, festival_entries = resolve_festivals(
    context_records, target_dates, geopos=geopos, timezone_name=location.timezone_name, enabled_names=enabled_names)

  eclipse_start_jd, eclipse_end_jd = local_range_jds(start_year, start_month, end_year, end_month,
                                                     location.timezone_name)
  eclipses = find_local_eclipses(eclipse_start_jd, eclipse_end_jd, geopos)
  sunrise_by_date = {record.civil_date: record.sunrise_jd for record in target_records}
  eclipse_line = format_eclipse_line(eclipses, location.timezone_name, sunrise_by_date=sunrise_by_date)
  eclipse_dates = eclipse_civil_dates(eclipses, location.timezone_name)
  # Saṅkrānti markers use the same sunrise-in-new-rāśi rule as Mesha/Makara
  # festivals; scan context months so a transition at the print-range start
  # is not missed.
  sankranti_by_date = sankranti_raasi_by_date(context_records)
  solar_by_date = solar_dates_by_date(context_records)
  ekadashi_dates = set()
  for value in ekadashi_dates_from_records(context_records):
    if range_start <= value <= range_end:
      ekadashi_dates.add(value)
  header_year, header_month = months[len(months) // 2]
  header_records = []
  for record in target_records:
    if (record.civil_date.year, record.civil_date.month) == (header_year, header_month):
      header_records.append(record)
  calendar_years = calendar_year_label(header_records, amanta=amanta)
  kali_ahargana = kali_ahargana_range(months)
  masa_badges = masa_badges_by_date(target_records, amanta=amanta)

  page_width, page_height = landscape(A4)
  output_path = Path(output_path)
  # ReportLab defaults the canvas to Helvetica; pin IndUni-H so it never appears.
  pdf = canvas.Canvas(str(output_path), pagesize=(page_width, page_height), initialFontName=PDF_FONT)
  masa_label = "amanta" if amanta else "purnimanta"
  if coordinate_selection == "tropical":
    coordinate_desc = coordinate_selection_label(coordinate_selection)
  else:
    coordinate_desc = f"{ayanamsa_label(coordinate_selection)} nakshatra"
  embed_pdf_metadata(
    pdf, title=f"{location.name} Panchanga {month_span_label(months)}",
    subject=(f"Daily tithi, {coordinate_desc}, yoga, and {masa_label} masa at "
             f"{location.name} sunrise"), ruleset_version=RULESET_VERSION, coordinate_selection=coordinate_selection)

  draw_page_header(pdf, location, months, RULESET_VERSION, amanta=amanta, coordinate_selection=coordinate_selection,
                   calendar_years=calendar_years, kali_ahargana=kali_ahargana)

  margin = 18
  day_column_width = 24
  usable_width = page_width - 2 * margin
  month_width = (usable_width - day_column_width) / len(months)
  top = page_height - 37

  draw_day_column(pdf, margin, top, day_column_width)
  for index, (year, month) in enumerate(months):
    x = margin + day_column_width + index * month_width
    draw_month(pdf, year, month, records_by_date, masa_badges, festivals_by_date, ekadashi_dates, eclipse_dates,
               sankranti_by_date, solar_by_date, x, top, month_width)

  draw_page_footer(pdf, festival_entries, eclipse_line=eclipse_line)
  pdf.showPage()

  pdf.save()
  return output_path


def default_output_path(location, start_year, start_month, month_system="amanta", coordinate_selection="citra"):
  months = month_range(start_year, start_month)
  end_year, end_month = months[-1]
  city_slug = re.sub(r"[^a-z0-9]+", "-", location.name.casefold()).strip("-") or "location"
  parts = []
  if not parse_month_system(month_system):
    parts.append("purnimanta")
  if coordinate_selection == "tropical":
    parts.append("tropical")
  elif coordinate_selection != "citra":
    parts.append(coordinate_selection)
  suffix = ("_" + "_".join(parts)) if parts else ""
  return Path(f"{city_slug}_panchanga_"
              f"{start_year:04d}-{start_month:02d}_to_"
              f"{end_year:04d}-{end_month:02d}{suffix}.pdf")


def argument_parser():
  parser = argparse.ArgumentParser(description=("Generate a one-page A4 panchanga for 14 consecutive months."))
  parser.add_argument("--city", required=True, help=(f"city as listed in {DEFAULT_CITIES_PATH.name} "
                                                     f'(e.g. "Helsinki, FI" or Helsinki,FI)'))
  parser.add_argument("--start", required=True, metavar="YYYY-MM", help="first of the 14 consecutive calendar months")
  parser.add_argument("-o", "--output", type=Path, help="output PDF path (default: generated from city and range)")
  parser.add_argument("--month", default="amanta", metavar="SYSTEM",
                      help=("lunar month reckoning for display: amanta (default) or purnimanta "))
  parser.add_argument(
    "--ayanamsa", default="citra", metavar="NAME", help=("ayanamsa: citra (default), revati, rohini, pushya, mula, "
                                                         "krishnamurti, raman or tropical"))
  parser.add_argument(
    "--festivals", type=Path, default=DEFAULT_FESTIVALS_PATH, help=(f"INI file selecting which festivals to include "
                                                                    f"(default: {DEFAULT_FESTIVALS_PATH.name})"))
  return parser


def main(argv=None):
  parser = argument_parser()
  arguments = parser.parse_args(argv)
  try:
    start_year, start_month = parse_start_month(arguments.start)
    location = load_location(arguments.city)
    month_system = arguments.month
    coordinate_selection = parse_coordinate_selection(arguments.ayanamsa)
    parse_month_system(month_system)  # validate early
    output_path = arguments.output or default_output_path(location, start_year, start_month, month_system=month_system,
                                                          coordinate_selection=coordinate_selection)
    generated = build_pdf(location, start_year, start_month, output_path, festivals_path=arguments.festivals,
                          month_system=month_system, coordinate_selection=coordinate_selection)
  except (OSError, ValueError, RuntimeError) as error:
    parser.error(str(error))
  print(generated.resolve())


if __name__ == "__main__":
  main()
