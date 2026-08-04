"""Compute sunrise panchanga for one civil date and city (GUI-compatible)."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

import panchanga
from generate_panchanga_calendar import (
    ayanamsa_label,
    coordinate_selection_label,
    load_location,
    month_system_label,
    parse_month_system,
    require_local_sunrise,
    timezone_hours,
)

_REPO_ROOT = Path(__file__).resolve().parent.parent
_NAMES_PATH = _REPO_ROOT / "sanskrit_names.json"


def _load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as source:
        return json.load(source)


@lru_cache(maxsize=1)
def sanskrit_names() -> dict:
    return _load_json(_NAMES_PATH)


def parse_civil_date(text: str) -> panchanga.Date:
    """Parse ``DD/MM/YYYY``; negative years are proleptic Gregorian."""
    text = (text or "").strip()
    if not text:
        raise ValueError("Date is required (DD/MM/YYYY).")
    try:
        day_s, month_s, year_s = text.split("/")
        day, month, year = int(day_s), int(month_s), int(year_s)
    except ValueError as error:
        raise ValueError("Date must be DD/MM/YYYY (negative years allowed).") from error
    if year == 0:
        raise ValueError("Year 0 is not used; use negative years for BCE.")
    if not 1 <= month <= 12 or not 1 <= day <= 31:
        raise ValueError(f"Invalid date {text!r}.")
    return panchanga.Date(year, month, day)


def format_time(hms) -> str:
    hours, minutes, seconds = hms
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"


def _named_segments(nhms, lookup: dict) -> list[dict]:
    """Map ``[index, [h,m,s]]`` or skipped ``[..., next_index, next_hms]`` to names."""
    segments = [{
        "number": int(nhms[0]),
        "name": lookup[str(nhms[0])],
        "ends": format_time(nhms[1]),
    }]
    if len(nhms) == 4:
        segments.append({
            "number": int(nhms[2]),
            "name": lookup[str(nhms[2])],
            "ends": format_time(nhms[3]),
        })
    return segments


def place_for_date(location, civil: panchanga.Date) -> panchanga.Place:
    """Build a Place with the city's UTC offset on the given civil date."""
    zone = ZoneInfo(location.timezone_name)
    year = civil.year if civil.year > 0 else 2000
    offset = timezone_hours(zone, year, civil.month, civil.day)
    return panchanga.Place(location.latitude, location.longitude, offset)


def _moon_altitude_at_local_noon(year: int, month: int, day: int, place) -> float:
    swe = panchanga.swe
    noon_ut = swe.julday(year, month, day, 12.0) - place.timezone / 24.0
    xx, _retflag = swe.calc_ut(noon_ut, swe.MOON)
    _azimuth, true_altitude, _apparent = swe.azalt(
        noon_ut, swe.ECL2HOR, (place.longitude, place.latitude, 0.0), 0, 0,
        [xx[0], xx[1], xx[2]])
    return true_altitude


def probe_moon_event(jd, place, civil: panchanga.Date, *, rise: bool) -> tuple[str | None, str]:
    """Return ``(time_or_None, status)`` for moonrise/moonset on a civil day.

    Status is ``ok``, ``none_today`` (next event is after local midnight+24h),
    ``always_below``, ``always_above``, or ``unavailable``.
    """
    swe = panchanga.swe
    t0 = jd - place.timezone / 24.0
    flag = swe.CALC_RISE if rise else swe.CALC_SET
    try:
        rc, times = swe.rise_trans(
            t0, swe.MOON, geopos=(place.longitude, place.latitude, 0.0),
            rsmi=panchanga._rise_flags + flag)
    except Exception:
        return None, "unavailable"
    if rc != 0:
        altitude = _moon_altitude_at_local_noon(civil.year, civil.month, civil.day, place)
        if altitude > 0.5:
            return None, "always_above"
        if altitude < -0.5:
            return None, "always_below"
        return None, "unavailable"
    local_hours = (times[0] - t0) * 24.0
    if not 0.0 <= local_hours < 24.0:
        return None, "none_today"
    return format_time(panchanga.to_dms(local_hours)), "ok"


def _interval_from_hms(start_hms, end_hms) -> dict:
    return {"start": format_time(start_hms), "end": format_time(end_hms)}


def _durmuhurta_intervals_from_values(values) -> list[dict]:
    starts, ends = values
    intervals = []
    for start, end in zip(starts, ends):
        # Unused slots stay at the 0 sentinel from panchanga.durmuhurtam.
        if start == 0 and end == 0:
            continue
        intervals.append(_interval_from_hms(panchanga.to_dms(start), panchanga.to_dms(end)))
    return intervals


def _varjyam_intervals(jd, place) -> list[dict]:
    return [
        _interval_from_hms(start, end)
        for start, end in panchanga.varjyam(jd, place)
    ]


def ayana_label(raasi_num: int) -> str:
    """Uttarāyaṇa from Makara–Mithuna (10–12, 1–3); else Dakṣiṇāyana."""
    if raasi_num >= 10 or raasi_num <= 3:
        return "Uttarāyaṇa"
    return "Dakṣiṇāyana"


def drik_ayana_label(ritu_num: int) -> str:
    """Ayana from Drik ṛtu: Śiśira–Vasanta–Grīṣma = Uttara; Varṣā–Śarad–Hemanta = Dakṣiṇa."""
    if ritu_num in (0, 1, 5):  # Vasanta, Grīṣma, Śiśira
        return "Uttarāyaṇa"
    return "Dakṣiṇāyana"


def compute_day_details(location, civil, *, amanta, coordinate_selection):
    """Compute one day while holding the shared coordinate-state lock."""
    with panchanga.coordinate_calculation_lock:
        return _compute_day_details_unlocked(
            location, civil, amanta=amanta, coordinate_selection=coordinate_selection)


def _compute_day_details_unlocked(location, civil, *, amanta, coordinate_selection):
    """Compute all mode-sensitive panchanga fields for one civil day.

    Shared by the JSON day API and the ICS generator so both consume the
    same normalized day record.  ``civil`` has ``year``/``month``/``day``
    attributes (``panchanga.Date`` or ``datetime.date``).

    Raises ``ValueError`` when sunrise cannot be computed for the date/location.
    """
    panchanga.set_coordinate_selection(coordinate_selection)
    place = place_for_date(location, civil)
    jd = panchanga.gregorian_to_jd(civil)

    try:
        sunrise = require_local_sunrise(
            jd, place, location.name, civil.year, civil.month, civil.day)
        sunset = panchanga.sunset(jd, place)
        sunset_jd = sunset[0]
        if not jd - 1 <= sunset_jd <= jd + 2:
            raise RuntimeError("no local sunset")
        day_dur = panchanga.day_duration(jd, place)
    except RuntimeError as error:
        raise ValueError(str(error)) from error
    except Exception as error:
        raise ValueError(
            f"Cannot compute sunrise panchanga for {location.name} "
            f"on {civil.day:02d}/{civil.month:02d}/{civil.year}: {error}") from error

    names = sanskrit_names()
    ti = panchanga.tithi(jd, place)
    nak = panchanga.nakshatra(jd, place)
    yog = panchanga.yoga(jd, place)
    kar = panchanga.karana(jd, place)
    ti_num, last_nm, lunar_num, is_adhika = panchanga.lunar_masa(
        jd, place, tithi_number=ti[0])
    # Display māsa follows amānta/pūrṇimānta; ṛtus use lunar_num only.
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
    vara_num = panchanga.vaara(jd)
    kali_year, saka_year, vikrama_year = panchanga.elapsed_year(jd, masa_num)
    kali_day = int(panchanga.ahargana(jd))
    sunrise_jd_ut = sunrise[0] - place.timezone / 24.0
    if coordinate_selection == "tropical":
        ayanamsa_degrees = None
    else:
        panchanga.set_ayanamsa_mode()
        try:
            ayanamsa_degrees = float(panchanga.swe.get_ayanamsa_ut(sunrise_jd_ut))
        finally:
            panchanga.reset_ayanamsa_mode()
    sun_raasi = int(panchanga.raasi(sunrise_jd_ut))
    moonrise, moonrise_status = probe_moon_event(jd, place, civil, rise=True)
    moonset, moonset_status = probe_moon_event(jd, place, civil, rise=False)
    rahu_kala = panchanga.rahu_kalam(jd, place)
    durmuhurta = panchanga.durmuhurtam(jd, place)

    return {
        "civil": civil,
        "place": place,
        "jd": jd,
        "sunrise_jd_ut": sunrise_jd_ut,
        "sunrise": sunrise,
        "sunset": sunset,
        "day_dur": day_dur,
        "names": names,
        "ti": ti,
        "nak": nak,
        "yog": yog,
        "kar": kar,
        "ti_num": ti_num,
        "lunar_num": lunar_num,
        "is_adhika": bool(is_adhika),
        "masa_num": masa_num,
        "rtu_num": rtu_num,
        "drik_rtu_num": drik_rtu_num,
        "samvat_num": samvat_num,
        "samvat_north_num": samvat_north_num,
        "vara_num": vara_num,
        "kali_year": int(kali_year),
        "saka_year": int(saka_year),
        "vikrama_year": int(vikrama_year),
        "kali_day": kali_day,
        "ayanamsa_degrees": ayanamsa_degrees,
        "sun_raasi": sun_raasi,
        "moonrise": moonrise,
        "moonrise_status": moonrise_status,
        "moonset": moonset,
        "moonset_status": moonset_status,
        "rahu_kala": rahu_kala,
        "durmuhurta": durmuhurta,
    }


def compute_day_panchanga(city: str, date_text: str, month_system: str | None = "amanta",
                          coordinate_selection: str = "citra") -> dict:
    """Return one city's day panchanga while holding coordinate state stable."""
    with panchanga.coordinate_calculation_lock:
        return _compute_day_panchanga_unlocked(
            city, date_text, month_system=month_system,
            coordinate_selection=coordinate_selection)


def _compute_day_panchanga_unlocked(
        city: str, date_text: str, month_system: str | None = "amanta",
        coordinate_selection: str = "citra") -> dict:
    """Return named panchanga fields for ``city`` on ``date_text`` (DD/MM/YYYY).

    ``month_system`` is ``amanta`` (default) or ``purnimanta``; it affects the
    displayed māsa name (and samvatsara / year counters derived from that name).
    Vedic and Drik ṛtu always use the shared new-moon–bounded māsa identity.

    ``coordinate_selection`` is a sidereal ayanāṃśa key (``citra`` default,
    ``revati``, ``rohini``, ``pushya``, ``mula``, ``krishnamurti``, ``raman``)
    or ``"tropical"`` for tropical (sāyana) longitudes.
    """
    city = (city or "").strip()
    if not city:
        raise ValueError("City is required.")
    amanta = parse_month_system(month_system)
    civil = parse_civil_date(date_text)
    location = load_location(city)

    details = compute_day_details(
        location, civil, amanta=amanta, coordinate_selection=coordinate_selection)
    names = details["names"]
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
    vara_num = details["vara_num"]
    kali_day = details["kali_day"]
    saka_year = details["saka_year"]
    kali_year = details["kali_year"]
    vikrama_year = details["vikrama_year"]
    ayanamsa_degrees = details["ayanamsa_degrees"]
    sun_raasi = details["sun_raasi"]
    moonrise = details["moonrise"]
    moonrise_status = details["moonrise_status"]
    moonset = details["moonset"]
    moonset_status = details["moonset_status"]
    rahu_kala = details["rahu_kala"]
    durmuhurta = details["durmuhurta"]

    use_tropical = coordinate_selection == "tropical"
    masa_name = names["masas"][str(masa_num)]
    if is_adhika:
        masa_label = f"Adhika {masa_name} māsa"
    else:
        masa_label = f"{masa_name} māsa"
    month_label = month_system_label(amanta)
    ayan_label = None if use_tropical else ayanamsa_label(coordinate_selection)
    ayana = ayana_label(sun_raasi)
    drik_ayana = drik_ayana_label(drik_rtu_num)

    return {
        "city": location.name,
        "date": f"{civil.day:02d}/{civil.month:02d}/{civil.year}",
        "timezone": location.timezone_name,
        "jd": jd,
        "sunrise_jd": sunrise_jd_ut,
        "coordinate_mode": "tropical" if use_tropical else "sidereal",
        "coordinate_label": coordinate_selection_label(coordinate_selection),
        "ayanamsa": ayan_label,
        "ayanamsa_key": None if use_tropical else coordinate_selection,
        "ayanamsa_degrees": None if use_tropical else round(ayanamsa_degrees, 8),
        "month_system": "amanta" if amanta else "purnimanta",
        "month_system_label": month_label,
        "samvatsara": names["samvats"][str(samvat_num)],
        "samvatsara_north": names["samvats"][str(samvat_north_num)],
        "ayana": ayana,
        "drik_ayana": drik_ayana,
        "masa": masa_label,
        "masa_number": masa_num,
        "is_adhika": is_adhika,
        "rtu": f"{names['ritus'][str(rtu_num)]} ṛtu",
        "drik_rtu": f"{names['ritus'][str(drik_rtu_num)]} ṛtu",
        "vaara": names["varas"][str(vara_num)],
        "kali_day": kali_day,
        "saka_year": saka_year,
        "kali_year": kali_year,
        "vikrama_year": vikrama_year,
        "sunrise": format_time(sunrise[1]),
        "sunset": format_time(sunset[1]),
        "moonrise": moonrise,
        "moonrise_status": moonrise_status,
        "moonset": moonset,
        "moonset_status": moonset_status,
        "day_duration": format_time(day_dur[1]),
        "rahu_kala": _interval_from_hms(*rahu_kala),
        "durmuhurta": _durmuhurta_intervals_from_values(durmuhurta),
        "varjyam": _varjyam_intervals(jd, place),
        "tithi": _named_segments(ti, names["tithis"]),
        "nakshatra": _named_segments(nak, names["nakshatras"]),
        "yoga": _named_segments(yog, names["yogas"]),
        "karana": _named_segments(kar, names["karanas"]),
    }
