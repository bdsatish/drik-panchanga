"""ICS export: daily all-day events for a 14-month panchanga span."""

from datetime import date, timedelta
from zoneinfo import ZoneInfo

from generate_panchanga_calendar import (
    daily_records, display_masa, month_range, parse_coordinate_selection,
    parse_month_system,
    timezone_hours,
)
from webapp.day_panchanga import (
    ayana_label, drik_ayana_label, format_time, probe_moon_event, sanskrit_names,
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


def _tithi_index(code: str) -> int:
    n = int(code[1:])
    return n if code[0] == "S" else n + 15


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


def _karana_text(jd, place, names) -> str:
    kar = panchanga.karana(jd, place)
    name = names["karanas"][str(kar[0])]
    return f"{name} (ends {format_time(kar[1])})"


def generate_ics(location, start_year, start_month, *, month_system="amanta",
                 ayanamsa=None):
    amanta = parse_month_system(month_system)
    coordinate_selection = parse_coordinate_selection(ayanamsa)
    tropical = coordinate_selection == "tropical"
    if tropical:
        panchanga.set_coordinate_mode("tropical")
    else:
        panchanga.set_chosen_ayanamsa(coordinate_selection)

    names = sanskrit_names()
    zone = ZoneInfo(location.timezone_name)
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
        jd = panchanga.gregorian_to_jd(panchanga.Date(civil.year, civil.month, civil.day))
        place = panchanga.Place(
            location.latitude, location.longitude,
            timezone_hours(zone, civil.year, civil.month, civil.day))

        sunrise = panchanga.sunrise(jd, place)
        sunset = panchanga.sunset(jd, place)
        sunrise_jd_ut = sunrise[0] - place.timezone / 24.0
        day_dur = panchanga.day_duration(jd, place)

        ti = panchanga.tithi(jd, place)
        nak = panchanga.nakshatra(jd, place)
        yog = panchanga.yoga(jd, place)
        ti_num, last_nm, lunar_num, is_adhika = panchanga.lunar_masa(
            jd, place, tithi_number=ti[0])
        masa_num = lunar_num
        if not amanta and not is_adhika and ti_num >= 16:
            masa_num = masa_num % 12 + 1

        rtu_num = panchanga.ritu(lunar_num)
        prev_was_adhika = False
        if not is_adhika:
            prev_nm = panchanga.new_moon(last_nm - 1, 29, -1)
            prev_was_adhika = (
                panchanga.raasi(prev_nm) == panchanga.raasi(last_nm))
        drik_rtu_num = panchanga.drik_ritu(
            lunar_num, is_adhika, ti_num, prev_was_adhika)

        samvat_num = panchanga.samvatsara(jd, masa_num)
        samvat_north_num = panchanga.samvatsara_north_modern(jd, masa_num)
        kali_year, saka_year, vikrama_year = panchanga.elapsed_year(jd, masa_num)
        kali_day = int(panchanga.ahargana(jd))
        sun_raasi = int(panchanga.raasi(sunrise_jd_ut))

        tithi_name = names["tithis"][str(_tithi_index(rec.tithi))]
        nak_name = names["nakshatras"][str(rec.nakshatra)]
        yoga_name = names["yogas"][str(rec.yoga)]
        masa_name = names["masas"][str(masa_num)]
        if is_adhika:
            masa_name = f"Adhika {masa_name}"
        masa_label = f"{masa_name} māsa"
        vara_name = names["varas"][str(panchanga.vaara(jd))]
        rtu_label = f"{names['ritus'][str(rtu_num)]} ṛtu"
        drik_rtu_label = f"{names['ritus'][str(drik_rtu_num)]} ṛtu"
        ayana = ayana_label(sun_raasi)
        drik_ayana = drik_ayana_label(drik_rtu_num)

        cdate = panchanga.Date(civil.year, civil.month, civil.day)
        moonrise, mr_status = probe_moon_event(jd, place, cdate, rise=True)
        moonset, ms_status = probe_moon_event(jd, place, cdate, rise=False)
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
            f"Karaṇa: {_karana_text(jd, place, names)}\\n"
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
