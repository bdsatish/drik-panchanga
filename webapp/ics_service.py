"""ICS export: daily all-day events for a 14-month panchanga span."""

from datetime import date, timedelta

from generate_panchanga_calendar import (
    daily_records, month_range, parse_month_system,
)
from webapp.day_panchanga import (
    ayana_label, compute_day_details, drik_ayana_label, format_time,
    sanskrit_names,
)
import panchanga


def _fold(line: str) -> str:
    """RFC 5545 line fold at 75 octets without splitting a UTF-8 code unit."""
    data = line.encode("utf-8")
    if len(data) <= 75:
        return line
    cut = 75
    while cut > 1 and (data[cut] & 0xC0) == 0x80:
        cut -= 1
    return data[:cut].decode("utf-8") + "\r\n " + _fold(data[cut:].decode("utf-8"))


def _fmt_interval(start_hms, end_hms) -> str:
    return f"{format_time(start_hms)}–{format_time(end_hms)}"


def _rahu_kala_text(jd, place) -> str:
    start, end = panchanga.rahu_kalam(jd, place)
    return _fmt_interval(start, end)


def _durmuhurta_text(jd, place) -> str:
    starts, ends = panchanga.durmuhurtam(jd, place)
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
    amanta = parse_month_system(month_system)
    names = sanskrit_names()
    records = daily_records(list(month_range(start_year, start_month)), location)
    out = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Drik Panchanga//EN",
        "CALSCALE:GREGORIAN",
        f"X-WR-CALNAME:Panchanga · {location.name}",
    ]
    for rec in records:
        civil = rec.civil_date
        d = date(civil.year, civil.month, civil.day)
        nxt = d + timedelta(days=1)
        details = compute_day_details(
            location, civil, amanta=amanta, coordinate_selection=coordinate_selection)
        jd = details["jd"]
        place = details["place"]
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

        summary = f"{tithi_name} · {nak_name} · {masa_name}".replace(",", "\\,")
        desc = (
            f"Samvatsara: {names['samvats'][str(samvat_num)]} {saka_year}"
            f", {names['samvats'][str(samvat_north_num)]} {vikrama_year}"
            f", Kali (elapsed) {kali_year}\\n"
            f"Ayana: {drik_ayana} (drik) · {ayana} (siddhantic)\\n"
            f"Ṛtu: {drik_rtu_label} (drik) · {rtu_label} (siddhantic)\\n"
            f"Māsa: {masa_label}\\n"
            f"Tithi: {tithi_name} (ends {format_time(ti[1])})\\n"
            f"Nakṣatra: {nak_name} (ends {format_time(nak[1])})\\n"
            f"Vāra: {vara_name}\\n"
            f"Yoga: {yoga_name} (ends {format_time(yog[1])})\\n"
            f"Karaṇa: {_karana_text(kar, names)}\\n"
            f"Sun*: {format_time(sunrise[1])} – {format_time(sunset[1])}\\n"
            f"{moon_line}\\n"
            f"Day duration: {format_time(day_dur[1])}\\n"
            f"Rāhukāla: {_rahu_kala_text(jd, place)}\\n"
            f"Durmuhūrta: {_durmuhurta_text(jd, place)}\\n"
            f"Kali Day: {kali_day}\\n"
            f"Julian day: {jd:.1f}\\n"
            f"Sunrise JD (UT): {sunrise_jd_ut:.6f}"
        ).replace(",", "\\,")
        ymd, ymd_n = d.strftime("%Y%m%d"), nxt.strftime("%Y%m%d")
        out += [
            "BEGIN:VEVENT",
            f"DTSTART;VALUE=DATE:{ymd}",
            f"DTEND;VALUE=DATE:{ymd_n}",
            f"SUMMARY:{summary}",
            f"DESCRIPTION:{desc}",
            f"UID:panchanga-{ymd}@{location.name}",
            "END:VEVENT",
        ]
    out.append("END:VCALENDAR")
    return "\r\n".join(_fold(line) for line in out) + "\r\n"
