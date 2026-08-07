"""ICS export: daily all-day events for a 14-month panchanga span."""

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
  _compute_day_details_unlocked,
  _valid_durmuhurta_intervals,
  ayana_label,
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
    folded = line
  else:
    parts = []
    cut = _utf8_cut(data, 75)
    parts.append(data[:cut].decode("utf-8"))
    data = data[cut:]
    while data:
      cut = _utf8_cut(data, 74)
      parts.append(" " + data[:cut].decode("utf-8"))
      data = data[cut:]
    folded = "\r\n".join(parts)
  return folded


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


def _fmt_interval(start_hms, end_hms):
  return f"{format_time(start_hms)}–{format_time(end_hms)}"


def generate_ics(location, start_year, start_month, month_system="amanta", coordinate_selection="citra"):
  """Generate a feed while holding coordinate state for the full span."""
  with panchanga.coordinate_calculation_lock:
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
    for year, month in month_range(start_year, start_month):
      for day in range(1, monthrange(year, month)[1] + 1):
        civil = panchanga.Date(year, month, day)
        d = _ics_date(civil)
        days_in_month = monthrange(civil.year, civil.month)[1]
        if civil.day < days_in_month:
          next_civil = panchanga.Date(civil.year, civil.month, civil.day + 1)
        elif civil.month < 12:
          next_civil = panchanga.Date(civil.year, civil.month + 1, 1)
        else:
          next_civil = panchanga.Date(civil.year + 1, 1, 1)
        nxt = _ics_date(next_civil)
        details = _compute_day_details_unlocked(location, civil, amanta=amanta,
                                                coordinate_selection=coordinate_selection)
        names = details["names"]
        tithi_name = names["tithis"][str(details["ti"][0])]
        nak_name = names["nakshatras"][str(details["nak"][0])]
        yoga_name = names["yogas"][str(details["yog"][0])]
        masa_name = format_masa_name(names, details["masa_num"], details["is_adhika"])
        masa_label = format_masa_label(names, details["masa_num"], details["is_adhika"])
        vara_name = names["varas"][str(details["vara_num"])]
        rtu_label = names["ritus"][str(details["rtu_num"])] + " ṛtu"
        drik_rtu_label = names["ritus"][str(details["drik_rtu_num"])] + " ṛtu"
        ayana = ayana_label(details["sun_raasi"])
        drik_ayana = drik_ayana_label(details["drik_rtu_num"])

        moon_rise_text = details["moonrise"] if details["moonrise"] else "—"
        moon_set_text = details["moonset"] if details["moonset"] else "—"
        moon_line = "Moon*: " + moon_rise_text + " – " + moon_set_text
        if details["moonrise_status"] != "ok" or details["moonset_status"] != "ok":
          moon_line = moon_line + " (" + details["moonrise_status"] + " / " + details["moonset_status"] + ")"

        summary = _escape_text(tithi_name + " · " + nak_name + " · " + masa_name)

        durmuhurta_parts = []
        for start, end in _valid_durmuhurta_intervals(details["durmuhurta"]):
          durmuhurta_parts.append(_fmt_interval(panchanga.to_dms(start), panchanga.to_dms(end)))
        durmuhurta_text = ", ".join(durmuhurta_parts) if durmuhurta_parts else "—"

        varjyam_parts = []
        for start, end in details["varjyam"]:
          varjyam_parts.append(_fmt_interval(start, end))
        varjyam_text = ", ".join(varjyam_parts) if varjyam_parts else "—"

        desc_lines = []
        desc_lines.append("Samvatsara: " + names["samvats"][str(details["samvat_num"])] + " " +
                          str(details["saka_year"]) + ", " + names["samvats"][str(details["samvat_north_num"])] + " " +
                          str(details["vikrama_year"]) + ", " + "Kali (elapsed) " + str(details["kali_year"]))
        desc_lines.append("Ayana: " + drik_ayana + " (drik) · " + ayana + " (siddhantic)")
        desc_lines.append("Ṛtu: " + drik_rtu_label + " (drik) · " + rtu_label + " (siddhantic)")
        desc_lines.append("Māsa: " + masa_label)
        desc_lines.append("Tithi: " + tithi_name + " (ends " + format_time(details["ti"][1]) + ")")
        desc_lines.append("Nakṣatra: " + nak_name + " (ends " + format_time(details["nak"][1]) + ")")
        desc_lines.append("Vāra: " + vara_name)
        desc_lines.append("Yoga: " + yoga_name + " (ends " + format_time(details["yog"][1]) + ")")
        desc_lines.append("Karaṇa: " + names["karanas"][str(details["kar"][0])] + " (ends " +
                          format_time(details["kar"][1]) + ")")
        desc_lines.append("Sun*: " + format_time(details["sunrise"][1]) + " – " + format_time(details["sunset"][1]))
        desc_lines.append(moon_line)
        desc_lines.append("Day duration: " + format_time(details["day_dur"][1]))
        desc_lines.append("Rāhukāla: " + _fmt_interval(*details["rahu_kala"]))
        desc_lines.append("Durmuhūrta: " + durmuhurta_text)
        desc_lines.append("Varjyam: " + varjyam_text)
        desc_lines.append("Kali Day: " + str(details["kali_day"]))
        desc_lines.append("Julian day: " + f"{details['jd']:.1f}")
        desc_lines.append("Sunrise JD (UT): " + f"{details['sunrise_jd_ut']:.6f}")
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
