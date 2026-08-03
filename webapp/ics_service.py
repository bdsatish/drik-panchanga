"""ICS (iCalendar) export for the Drik Panchanga calendar.

Generates an ICS file with daily all-day VEVENT entries for a 14-month
calendrical span.  No dependencies beyond the standard library and the
existing project modules.
"""

from __future__ import annotations

import uuid
from calendar import monthrange

from generate_panchanga_calendar import (
    daily_records,
    month_range,
    parse_ayanamsa,
    parse_month_system,
    tithi_display_parts,
    tithi_code,
)
from webapp.day_panchanga import sanskrit_names
import panchanga


def _fold_lines(text: str) -> str:
    """Fold ICS content lines to 75 octets max (RFC 5545 §3.1)."""
    result = []
    for line in text.split("\r\n"):
        result.append(_fold_line(line))
    return "\r\n".join(result)


def _fold_line(line: str) -> str:
    encoded = line.encode("utf-8")
    if len(encoded) <= 75:
        return line
    cutoff = 75
    while True:
        try:
            encoded[:cutoff].decode("utf-8")
            break
        except UnicodeDecodeError:
            cutoff -= 1
    first = encoded[:cutoff].decode("utf-8")
    rest = encoded[cutoff:].decode("utf-8")
    return first + "\r\n " + _fold_line(rest)


def _escape_ics(text: str) -> str:
    """Escape special ICS characters: \\n , ; \\."""
    return text.replace("\\", "\\\\").replace("\n", "\\n").replace(",", "\\,").replace(";", "\\;")


def _date_str(civil: panchanga.Date) -> str:
    return f"{civil.year:04d}{civil.month:02d}{civil.day:02d}"


def _vaara_name(jd: float, names: dict) -> str:
    return names["varas"][str(panchanga.vaara(jd))]


def generate_ics(
    location,
    start_year: int,
    start_month: int,
    *,
    month_system: str = "amanta",
    ayanamsa: str = "citra",
    tropical: str = "0",
) -> str:
    """Return ICS calendar text for the 14-month span starting at *start_year*-*start_month*.

    One all-day VEVENT per day.  The summary line shows tithi + nakshatra;
    the description includes full panchanga details.
    """
    amanta = parse_month_system(month_system)
    ayanamsa_key = parse_ayanamsa(ayanamsa)
    use_tropical = (tropical or "0").strip() in {"1", "true", "yes", "on"}
    panchanga.set_chosen_ayanamsa(ayanamsa_key)
    panchanga.set_coordinate_mode("tropical" if use_tropical else "sidereal")

    months = list(month_range(start_year, start_month))
    records = daily_records(months, location)
    names = sanskrit_names()

    coord_label = "Tropical (Sāyana)" if use_tropical else f"{ayanamsa_key}"
    masa_label = "Amānta" if amanta else "Pūrṇimānta"

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Drik Panchanga//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:Panchanga · {location.name}",
        f"X-WR-CALDESC:{coord_label} · {masa_label}",
        "X-PUBLISHED-TTL:PT12H",
    ]

    for record in records:
        civil = record.civil_date
        dt_str = _date_str(civil)
        next_day = _date_str(_next_date(civil))
        uid = uuid.uuid5(uuid.NAMESPACE_URL, f"panchanga-{dt_str}@{location.name}")

        number, is_sukla = tithi_display_parts(record.tithi)
        tithi_label = names["tithis"][str(_tithi_index(record.tithi))]
        nak_label = names["nakshatras"][str(record.nakshatra)]
        yoga_label = names["yogas"][str(record.yoga)]
        vaara = _vaara_name(record.sunrise_jd, names)

        masa_num = int(record.masa.lstrip("A"))
        masa_name = names["masas"][str(masa_num)]
        if record.is_adhika:
            masa_display = f"Adhika {masa_name}"
        else:
            masa_display = masa_name

        sukla_krsna = "Śukla-pakṣa" if is_sukla else "Kṛṣṇa-pakṣa"
        summary = f"{tithi_label} · {nak_label}"
        description = (
            f"Tithi: {tithi_label} ({sukla_krsna} {number})\\n"
            f"Nakṣatra: {nak_label} (№{record.nakshatra})\\n"
            f"Yoga: {yoga_label}\\n"
            f"Māsa: {masa_display}\\n"
            f"Vāra: {vaara}\\n"
        )
        if record.is_adhika:
            description += "Adhika māsa (intercalary month)\\n"

        lines.append("BEGIN:VEVENT")
        lines.append(f"DTSTART;VALUE=DATE:{dt_str}")
        lines.append(f"DTEND;VALUE=DATE:{next_day}")
        lines.append(f"SUMMARY:{_escape_ics(summary)}")
        lines.append(f"UID:{uid}")
        lines.append(f"DESCRIPTION:{_escape_ics(description)}")
        lines.append("TRANSP:TRANSPARENT")
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    raw = "\r\n".join(lines) + "\r\n"
    return _fold_lines(raw)


def _next_date(civil: panchanga.Date) -> panchanga.Date:
    year, month, day = civil.year, civil.month, civil.day
    _, days_in_month = monthrange(year, month)
    if day < days_in_month:
        return panchanga.Date(year, month, day + 1)
    if month < 12:
        return panchanga.Date(year, month + 1, 1)
    return panchanga.Date(year + 1, 1, 1)


def _tithi_index(tithi: str) -> int:
    """Convert S1..S15 / K1..K15 to the 1..30 index used by sanskrit_names."""
    code = tithi[0]
    num = int(tithi[1:])
    if code == "S":
        return num
    return num + 15
