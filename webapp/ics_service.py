"""ICS export: daily all-day events for a 14-month panchanga span."""

from calendar import monthrange
from datetime import datetime, timezone
import re

from generate_panchanga_calendar import (
    coordinate_selection_label,
    month_range,
    month_system_label,
    parse_month_system,
)
from webapp.day_panchanga import (
    ayana_label,
    compute_day_details,
    drik_ayana_label,
    format_time,
)
import panchanga


def _utf8_cut(data: bytes, limit: int) -> int:
    cut = min(limit, len(data))
    while cut:
        try:
            data[:cut].decode("utf-8")
            return cut
        except UnicodeDecodeError:
            cut -= 1
    raise ValueError("Cannot fold invalid UTF-8 content")


def _fold(line: str) -> str:
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


def _escape_text(text: str) -> str:
    return (text.replace("\\", "\\\\").replace(";", "\\;")
            .replace(",", "\\,").replace("\r\n", "\n")
            .replace("\r", "\n").replace("\n", "\\n"))


def _location_slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.casefold()).strip("-") or "location"


def _ics_date(civil) -> str:
    return f"{civil.year:04d}{civil.month:02d}{civil.day:02d}"


def _next_civil_date(civil):
    days = monthrange(civil.year, civil.month)[1]
    if civil.day < days:
        return panchanga.Date(civil.year, civil.month, civil.day + 1)
    if civil.month < 12:
        return panchanga.Date(civil.year, civil.month + 1, 1)
    return panchanga.Date(civil.year + 1, 1, 1)


def _civil_dates(months):
    for year, month in months:
        for day in range(1, monthrange(year, month)[1] + 1):
            yield panchanga.Date(year, month, day)


def _fmt_interval(start_hms, end_hms) -> str:
    return f"{format_time(start_hms)}–{format_time(end_hms)}"


def _rahu_kala_text(values) -> str:
    start, end = values
    return _fmt_interval(start, end)


def _durmuhurta_text(values) -> str:
    starts, ends = values
    parts = []
    for s, e in zip(starts, ends):
        if s == 0 and e == 0:
            continue
        parts.append(_fmt_interval(panchanga.to_dms(s), panchanga.to_dms(e)))
    return ", ".join(parts) if parts else "—"


def _karana_text(kar, names) -> str:
    name = names["karanas"][str(kar[0])]
    return f"{name} (ends {format_time(kar[1])})"


def generate_ics(location, start_year, start_month, *, month_system="amanta",
                 coordinate_selection="citra"):
    """Generate a feed while holding coordinate state for the full span."""
    with panchanga.coordinate_calculation_lock:
        return _generate_ics_unlocked(
            location, start_year, start_month,
            month_system=month_system, coordinate_selection=coordinate_selection)


def _generate_ics_unlocked(location, start_year, start_month, *, month_system="amanta",
                           coordinate_selection="citra"):
    amanta = parse_month_system(month_system)
    month_key = "amanta" if amanta else "purnimanta"
    dtstamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    location_slug = _location_slug(location.name)
    out = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Drik Panchanga//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_escape_text(f'Panchanga · {location.name}')}",
        f"X-WR-CALDESC:{_escape_text(coordinate_selection_label(coordinate_selection) + ' · ' + month_system_label(amanta))}",
    ]
    for civil in _civil_dates(list(month_range(start_year, start_month))):
        d = _ics_date(civil)
        nxt = _ics_date(_next_civil_date(civil))
        details = compute_day_details(
            location, civil, amanta=amanta, coordinate_selection=coordinate_selection)
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
        masa_name = names["masas"][str(masa_num)]
        if is_adhika:
            masa_name = f"Adhika {masa_name}"
        masa_label = f"{masa_name} māsa"
        vara_name = names["varas"][str(vara_num)]
        rtu_label = f"{names['ritus'][str(rtu_num)]} ṛtu"
        drik_rtu_label = f"{names['ritus'][str(drik_rtu_num)]} ṛtu"
        ayana = ayana_label(sun_raasi)
        drik_ayana = drik_ayana_label(drik_rtu_num)

        moon_line = f"Moon*: {moonrise or '—'} – {moonset or '—'}"
        if mr_status != "ok" or ms_status != "ok":
            moon_line += f" ({mr_status} / {ms_status})"

        summary = _escape_text(f"{tithi_name} · {nak_name} · {masa_name}")
        description = _escape_text("\n".join((
            f"Samvatsara: {names['samvats'][str(samvat_num)]} {saka_year}, "
            f"{names['samvats'][str(samvat_north_num)]} {vikrama_year}, "
            f"Kali (elapsed) {kali_year}",
            f"Ayana: {drik_ayana} (drik) · {ayana} (siddhantic)",
            f"Ṛtu: {drik_rtu_label} (drik) · {rtu_label} (siddhantic)",
            f"Māsa: {masa_label}",
            f"Tithi: {tithi_name} (ends {format_time(ti[1])})",
            f"Nakṣatra: {nak_name} (ends {format_time(nak[1])})",
            f"Vāra: {vara_name}",
            f"Yoga: {yoga_name} (ends {format_time(yog[1])})",
            f"Karaṇa: {_karana_text(kar, names)}",
            f"Sun*: {format_time(sunrise[1])} – {format_time(sunset[1])}",
            moon_line,
            f"Day duration: {format_time(day_dur[1])}",
            f"Rāhukāla: {_rahu_kala_text(rahu_kala)}",
            f"Durmuhūrta: {_durmuhurta_text(durmuhurta)}",
            f"Kali Day: {kali_day}",
            f"Julian day: {jd:.1f}",
            f"Sunrise JD (UT): {sunrise_jd_ut:.6f}",
        )))
        out += [
            "BEGIN:VEVENT",
            f"DTSTART;VALUE=DATE:{d}",
            f"DTEND;VALUE=DATE:{nxt}",
            f"DTSTAMP:{dtstamp}",
            f"SUMMARY:{summary}",
            f"DESCRIPTION:{description}",
            f"UID:panchanga-{coordinate_selection}-{month_key}-{d}@{location_slug}",
            "END:VEVENT",
        ]
    out.append("END:VCALENDAR")
    return "\r\n".join(_fold(line) for line in out) + "\r\n"
