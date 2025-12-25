from datetime import date
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Query

import panchanga  # this is ../panchanga.py


app = FastAPI(
    title="Drik Panchanga API",
    version="1.0.0",
    description="FastAPI wrapper around webresh/drik-panchanga (Swiss Ephemeris).",
)


def _fmt_time(dms):
    """Convert [h, m, s] list to 'HH:MM:SS' string; hours may be > 24."""
    if not dms or len(dms) != 3:
        return None
    h, m, s = [int(x) for x in dms]
    return f"{h:02d}:{m:02d}:{s:02d}"


def compute_panchanga(
    year: int,
    month: int,
    day: int,
    latitude: float,
    longitude: float,
    tz_offset_hours: float,
) -> Dict[str, Any]:
    # Build Date and Place from panchanga.py
    dt = panchanga.Date(year, month, day)
    jd = panchanga.gregorian_to_jd(dt)
    place = panchanga.Place(latitude, longitude, tz_offset_hours)

    # Core angas
    tithi_raw = panchanga.tithi(jd, place)
    nak_raw = panchanga.nakshatra(jd, place)
    yoga_raw = panchanga.yoga(jd, place)
    kar_raw = panchanga.karana(jd, place)
    vaara_raw = panchanga.vaara(jd)
    masa_raw = panchanga.masa(jd, place)
    ritu_raw = panchanga.ritu(masa_raw[0] if isinstance(masa_raw, (list, tuple)) else masa_raw)
    samvatsara_raw = panchanga.samvatsara(jd, masa_raw[0] if isinstance(masa_raw, (list, tuple)) else masa_raw)

    # Sun / Moon data
    sunrise_raw = panchanga.sunrise(jd, place)    # [jd_local, [h,m,s]]
    sunset_raw = panchanga.sunset(jd, place)      # [jd_local, [h,m,s]]
    moonrise_raw = panchanga.moonrise(jd, place)  # [h,m,s]
    moonset_raw = panchanga.moonset(jd, place)    # [h,m,s]

    day_dur_raw = panchanga.day_duration(jd, place)  # [hours_float, [h,m,s]]

    # Normalize to a clean JSON structure
    tithi_dict = {
        "current_number": int(tithi_raw[0]),
        "current_ends_at": _fmt_time(tithi_raw[1]),
    }
    if len(tithi_raw) > 2:
        tithi_dict["leap_number"] = int(tithi_raw[2])
        tithi_dict["leap_ends_at"] = _fmt_time(tithi_raw[3])

    nak_dict = {
        "current_number": int(nak_raw[0]),
        "current_ends_at": _fmt_time(nak_raw[1]),
    }
    if len(nak_raw) > 2:
        nak_dict["leap_number"] = int(nak_raw[2])
        nak_dict["leap_ends_at"] = _fmt_time(nak_raw[3])

    yoga_dict = {
        "current_number": int(yoga_raw[0]),
        "current_ends_at": _fmt_time(yoga_raw[1]),
    }
    if len(yoga_raw) > 2:
        yoga_dict["leap_number"] = int(yoga_raw[2])
        yoga_dict["leap_ends_at"] = _fmt_time(yoga_raw[3])

    karana_list = (
        [int(k) for k in kar_raw] if isinstance(kar_raw, (list, tuple)) else [int(kar_raw)]
    )

    # Masa: [masa_num] or [masa_num, is_adhika]
    masa_dict: Dict[str, Any] = {}
    if isinstance(masa_raw, (list, tuple)) and len(masa_raw) > 0:
        masa_dict["number"] = int(masa_raw[0])
        if len(masa_raw) > 1:
            masa_dict["is_adhika_masa"] = bool(masa_raw[1])
    else:
        masa_dict["number"] = int(masa_raw)

    return {
        "sun_moon": {
            "sunrise": _fmt_time(sunrise_raw[1]),
            "sunset": _fmt_time(sunset_raw[1]),
            "moonrise": _fmt_time(moonrise_raw),
            "moonset": _fmt_time(moonset_raw),
            "day_duration_hours": day_dur_raw[0],
            "day_duration_hms": _fmt_time(day_dur_raw[1]),
        },
        "angams": {
            "tithi": tithi_dict,
            "nakshatra": nak_dict,
            "yoga": yoga_dict,
            "karana_numbers": karana_list,
            "vaara_number": int(vaara_raw),
        },
        "month_year": {
            "masa_number": masa_dict["number"],
            "is_adhika_masa": masa_dict.get("is_adhika_masa", False),
            "ritu_number": int(ritu_raw),
            "samvatsara_number": int(samvatsara_raw),
        },
        "raw": {
            "tithi": tithi_raw,
            "nakshatra": nak_raw,
            "yoga": yoga_raw,
            "karana": kar_raw,
            "masa": masa_raw,
        },
    }


@app.get("/")
def root():
    return {"message": "Drik Panchanga API. Use /panchanga with query params."}


@app.get("/panchanga")
def get_panchanga(
    year: int = Query(...),
    month: int = Query(...),
    day: int = Query(...),
    latitude: float = Query(...),
    longitude: float = Query(...),
    tz_offset_hours: float = Query(..., description="UTC offset in hours (IST = 5.5)"),
):
    try:
        d = date(year, month, day)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    data = compute_panchanga(year, month, day, latitude, longitude, tz_offset_hours)

    return {
        "input": {
            "date": d.isoformat(),
            "latitude": latitude,
            "longitude": longitude,
            "tz_offset_hours": tz_offset_hours,
        },
        "panchanga": data,
    }
