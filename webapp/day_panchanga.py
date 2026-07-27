"""Compute sunrise panchanga for one civil date and city (GUI-compatible)."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

import panchanga
from generate_panchanga_calendar import load_location, timezone_hours

_REPO_ROOT = Path(__file__).resolve().parent.parent
_NAMES_PATH = _REPO_ROOT / "sanskrit_names.json"


def _load_json_file(path: Path) -> dict:
    """Load JSON, stripping ``//`` and ``/* ... */`` comments (sanskrit_names.json)."""
    content = path.read_text(encoding="utf-8")
    content = re.sub(r"//.*", "", content)
    content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    return json.loads(content)


@lru_cache(maxsize=1)
def sanskrit_names() -> dict:
    return _load_json_file(_NAMES_PATH)


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


def compute_day_panchanga(city: str, date_text: str) -> dict:
    """Return named panchanga fields for ``city`` on ``date_text`` (DD/MM/YYYY)."""
    city = (city or "").strip()
    if not city:
        raise ValueError("City is required.")
    civil = parse_civil_date(date_text)
    location = load_location(city)
    place = place_for_date(location, civil)

    panchanga.set_chosen_ayanamsa("citra")
    jd = panchanga.gregorian_to_jd(civil)

    try:
        sunrise_jd = panchanga.sunrise(jd, place)[0]
        if not jd - 1 <= sunrise_jd <= jd + 2:
            raise RuntimeError("no local sunrise")
    except Exception as error:
        raise ValueError(f"Cannot compute sunrise panchanga for {location.name} "
                         f"on {civil.day:02d}/{civil.month:02d}/{civil.year}: {error}") from error

    names = sanskrit_names()
    ti = panchanga.tithi(jd, place)
    nak = panchanga.nakshatra(jd, place)
    yog = panchanga.yoga(jd, place)
    kar = panchanga.karana(jd, place)
    masa_num, is_adhika = panchanga.masa(jd, place)
    rtu_num = panchanga.ritu(masa_num)
    samvat_num = panchanga.samvatsara(jd, masa_num)
    vara_num = panchanga.vaara(jd)

    masa_name = names["masas"][str(masa_num)]
    if is_adhika:
        masa_label = f"Adhika {masa_name} māsa"
    else:
        masa_label = f"{masa_name} māsa"

    return {
        "city": location.name,
        "date": f"{civil.day:02d}/{civil.month:02d}/{civil.year}",
        "timezone": location.timezone_name,
        "ayanamsa": "True Citra",
        "samvatsara": names["samvats"][str(samvat_num)],
        "masa": masa_label,
        "masa_number": masa_num,
        "is_adhika": bool(is_adhika),
        "rtu": f"{names['ritus'][str(rtu_num)]} ṛtu",
        "vaara": names["varas"][str(vara_num)],
        "tithi": _named_segments(ti, names["tithis"]),
        "nakshatra": _named_segments(nak, names["nakshatras"]),
        "yoga": _named_segments(yog, names["yogas"]),
        "karana": _named_segments(kar, names["karanas"]),
    }
