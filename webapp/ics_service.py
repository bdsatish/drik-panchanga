"""ICS export: daily all-day events for a 14-month panchanga span.

``generate_ics`` takes the coordinate lock, then ``_generate_ics_unlocked``
builds the feed so ayanāṃśa / tropical mode stays stable for every day.
"""

from calendar import monthrange
from datetime import datetime, timezone

from generate_panchanga_calendar import (
  coordinate_selection_label,
  location_slug,
  month_range,
  month_system_label,
  require_month_system,
)
from webapp.day_panchanga import (
  ayana_label,
  compute_day_details,
  drik_ayana_label,
  format_masa_label,
  format_masa_name,
  format_time,
)
import panchanga


def _utf8_cut(data, limit):
  cut = min(limit, len(data))
  while cut:
    try:
      data[:cut].decode("utf-8")
      return cut
    except UnicodeDecodeError:
      cut -= 1
  raise ValueError("Cannot fold invalid UTF-8 content")


def _fold(line):
  """Fold content lines to at most 75 octets, including continuation spaces."""
  data = line.encode("utf-8")
  if len(data) <= 75:
    return line
  parts = []
  cut = _utf8_cut(data, 75)
  parts.append(data[:cut].decode("utf-8"))
  data = data[cut:]
  while data:
    cut = _utf8_cut(data, 74)
    parts.append(" " + data[:cut].decode("utf-8"))
    data = data[cut:]
  return "\r\n".join(parts)


def _escape_text(text):
  text = text.replace("\\", "\\\\")
  text = text.replace(";", "\\;")
  text = text.replace(",", "\\,")
  text = text.replace("\r\n", "\n")
  text = text.replace("\r", "\n")
  text = text.replace("\n", "\\n")
  return text


def _ics_date(civil):
  return f"{civil.year:04d}{civil.month:02d}{civil.day:02d}"


def _next_civil_date(civil):
  days = monthrange(civil.year, civil.month)[1]
  if civil.day < days:
    return panchanga.Date(civil.year, civil.month, civil.day + 1)
  if civil.month < 12:
    return panchanga.Date(civil.year, civil.month + 1, 1)
  return panchanga.Date(civil.year + 1, 1, 1)


def _civil_dates(months):
  dates = []
  for year, month in months:
    for day in range(1, monthrange(year, month)[1] + 1):
      dates.append(panchanga.Date(year, month, day))
  return dates


def _fmt_interval(start_hms, end_hms):
  return f"{format_time(start_hms)}–{format_time(end_hms)}"


def _rahu_kala_text(values):
  start, end = values
  return _fmt_interval(start, end)


def _durmuhurta_text(values):
  starts, ends = values
  parts = []
  for s, e in zip(starts, ends):
    if s == 0 and e == 0:
      continue
    parts.append(_fmt_interval(panchanga.to_dms(s), panchanga.to_dms(e)))
  return ", ".join(parts) if parts else "—"


def _karana_text(kar, names):
  name = names["karanas"][str(kar[0])]
  return f"{name} (ends {format_time(kar[1])})"


def generate_ics(location, start_year, start_month, month_system="amanta", coordinate_selection="citra"):
  """Generate a feed while holding coordinate state for the full span.

    Lock here, then ``_generate_ics_unlocked`` writes every VEVENT.
    """
  with panchanga.coordinate_calculation_lock:
    return _generate_ics_unlocked(location, start_year, start_month, month_system=month_system,
                                  coordinate_selection=coordinate_selection)


def _generate_ics_unlocked(location, start_year, start_month, month_system="amanta", coordinate_selection="citra"):
  amanta = require_month_system(month_system)
  month_key = "amanta" if amanta else "purnimanta"
  dtstamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
  loc_slug = location_slug(location.name)
  cal_name = _escape_text("Panchanga · " + location.name)
  cal_desc = _escape_text(coordinate_selection_label(coordinate_selection) + " · " + month_system_label(amanta))
  out = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Drik Panchanga//EN",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    "X-WR-CALNAME:" + cal_name,
    "X-WR-CALDESC:" + cal_desc,
  ]
  for civil in _civil_dates(month_range(start_year, start_month)):
    d = _ics_date(civil)
    nxt = _ics_date(_next_civil_date(civil))
    details = compute_day_details(location, civil, amanta=amanta, coordinate_selection=coordinate_selection)
    names = details["names"]
    jd = details["jd"]
    sunrise = details["sunrise"]
    sunset = details["sunset"]
    day_dur = details["day_dur"]
    sunrise_jd_ut = details["sunrise_jd_ut"]
    ti = details["ti"]
    nak = details["nak"]
    yog = details["yog"]
    kar = details["kar"]
    masa_num = details["masa_num"]
    is_adhika = details["is_adhika"]
    rtu_num = details["rtu_num"]
    drik_rtu_num = details["drik_rtu_num"]
    samvat_num = details["samvat_num"]
    samvat_north_num = details["samvat_north_num"]
    kali_year = details["kali_year"]
    saka_year = details["saka_year"]
    vikrama_year = details["vikrama_year"]
    kali_day = details["kali_day"]
    sun_raasi = details["sun_raasi"]
    vara_num = details["vara_num"]
    moonrise = details["moonrise"]
    mr_status = details["moonrise_status"]
    moonset = details["moonset"]
    ms_status = details["moonset_status"]
    rahu_kala = details["rahu_kala"]
    durmuhurta = details["durmuhurta"]

    tithi_name = names["tithis"][str(ti[0])]
    nak_name = names["nakshatras"][str(nak[0])]
    yoga_name = names["yogas"][str(yog[0])]
    masa_name = format_masa_name(names, masa_num, is_adhika)
    masa_label = format_masa_label(names, masa_num, is_adhika)
    vara_name = names["varas"][str(vara_num)]
    rtu_label = names["ritus"][str(rtu_num)] + " ṛtu"
    drik_rtu_label = names["ritus"][str(drik_rtu_num)] + " ṛtu"
    ayana = ayana_label(sun_raasi)
    drik_ayana = drik_ayana_label(drik_rtu_num)

    moon_rise_text = moonrise if moonrise else "—"
    moon_set_text = moonset if moonset else "—"
    moon_line = "Moon*: " + moon_rise_text + " – " + moon_set_text
    if mr_status != "ok" or ms_status != "ok":
      moon_line = moon_line + " (" + mr_status + " / " + ms_status + ")"

    summary = _escape_text(tithi_name + " · " + nak_name + " · " + masa_name)

    desc_lines = []
    desc_lines.append("Samvatsara: " + names["samvats"][str(samvat_num)] + " " + str(saka_year) + ", " +
                      names["samvats"][str(samvat_north_num)] + " " + str(vikrama_year) + ", " + "Kali (elapsed) " +
                      str(kali_year))
    desc_lines.append("Ayana: " + drik_ayana + " (drik) · " + ayana + " (siddhantic)")
    desc_lines.append("Ṛtu: " + drik_rtu_label + " (drik) · " + rtu_label + " (siddhantic)")
    desc_lines.append("Māsa: " + masa_label)
    desc_lines.append("Tithi: " + tithi_name + " (ends " + format_time(ti[1]) + ")")
    desc_lines.append("Nakṣatra: " + nak_name + " (ends " + format_time(nak[1]) + ")")
    desc_lines.append("Vāra: " + vara_name)
    desc_lines.append("Yoga: " + yoga_name + " (ends " + format_time(yog[1]) + ")")
    desc_lines.append("Karaṇa: " + _karana_text(kar, names))
    desc_lines.append("Sun*: " + format_time(sunrise[1]) + " – " + format_time(sunset[1]))
    desc_lines.append(moon_line)
    desc_lines.append("Day duration: " + format_time(day_dur[1]))
    desc_lines.append("Rāhukāla: " + _rahu_kala_text(rahu_kala))
    desc_lines.append("Durmuhūrta: " + _durmuhurta_text(durmuhurta))
    desc_lines.append("Kali Day: " + str(kali_day))
    desc_lines.append("Julian day: " + f"{jd:.1f}")
    desc_lines.append("Sunrise JD (UT): " + f"{sunrise_jd_ut:.6f}")
    description = _escape_text("\n".join(desc_lines))

    out.append("BEGIN:VEVENT")
    out.append("DTSTART;VALUE=DATE:" + d)
    out.append("DTEND;VALUE=DATE:" + nxt)
    out.append("DTSTAMP:" + dtstamp)
    out.append("SUMMARY:" + summary)
    out.append("DESCRIPTION:" + description)
    out.append("UID:panchanga-" + coordinate_selection + "-" + month_key + "-" + d + "@" + loc_slug)
    out.append("END:VEVENT")
  out.append("END:VCALENDAR")
  folded = []
  for line in out:
    folded.append(_fold(line))
  return "\r\n".join(folded) + "\r\n"
