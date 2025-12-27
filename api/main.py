from datetime import date, timedelta
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


# --- Helper functions for tithi/maasikam ---
def _paksha_from_tithi_num(tithi_num: int) -> str:
    # Drik tithi numbers are typically 1..30
    return "Shukla" if 1 <= tithi_num <= 15 else "Krishna"


def _tithi_in_paksha(tithi_num: int) -> int:
    # Converts 1..30 into 1..15 within its paksha
    return ((tithi_num - 1) % 15) + 1


def _tithi_at_sunrise(
    year: int,
    month: int,
    day: int,
    latitude: float,
    longitude: float,
    tz_offset_hours: float,
) -> Dict[str, Any]:
    """Return tithi (number + ends_at) computed at local sunrise for the given date."""
    dt = panchanga.Date(year, month, day)
    jd0 = panchanga.gregorian_to_jd(dt)
    place = panchanga.Place(latitude, longitude, tz_offset_hours)

    sunrise_raw = panchanga.sunrise(jd0, place)  # [jd_local, [h,m,s]]
    jd_sunrise = sunrise_raw[0]
    tithi_raw = panchanga.tithi(jd_sunrise, place)

    tithi_dict = {
        "current_number": int(tithi_raw[0]),
        "current_ends_at": _fmt_time(tithi_raw[1]),
    }
    if len(tithi_raw) > 2:
        tithi_dict["leap_number"] = int(tithi_raw[2])
        tithi_dict["leap_ends_at"] = _fmt_time(tithi_raw[3])

    return {
        "sunrise": _fmt_time(sunrise_raw[1]),
        "tithi": tithi_dict,
        "raw": {"tithi": tithi_raw},
    }


def _find_next_matching_tithi_at_sunrise(
    death_tithi_num: int,
    death_paksha: str,
    from_dt: date,
    latitude: float,
    longitude: float,
    tz_offset_hours: float,
    max_search_days: int = 400,
) -> Dict[str, Any]:
    """Brute-force search forward day-by-day for the next date whose sunrise tithi matches.

    Maasikam is typically observed on the same paksha+tithi (at sunrise) as the death tithi.
    This function returns the first next matching occurrence after from_dt.
    """
    target_in_paksha = _tithi_in_paksha(death_tithi_num)

    cur = from_dt
    for _ in range(max_search_days):
        cur = cur + timedelta(days=1)
        info = _tithi_at_sunrise(cur.year, cur.month, cur.day, latitude, longitude, tz_offset_hours)
        cur_tithi_num = int(info["tithi"]["current_number"])
        cur_paksha = _paksha_from_tithi_num(cur_tithi_num)
        cur_in_paksha = _tithi_in_paksha(cur_tithi_num)

        if cur_paksha == death_paksha and cur_in_paksha == target_in_paksha:
            return {
                "date": cur.isoformat(),
                "sunrise": info["sunrise"],
                "tithi": info["tithi"],
                "paksha": cur_paksha,
                "tithi_in_paksha": cur_in_paksha,
            }

    raise HTTPException(
        status_code=500,
        detail=f"Could not find next matching tithi within {max_search_days} days. Check inputs.",
    )


def _find_next_annual_matching_tithi_at_sunrise(
    death_tithi_num: int,
    death_paksha: str,
    from_dt: date,
    latitude: float,
    longitude: float,
    tz_offset_hours: float,
    min_days_after: int = 300,
    max_search_days: int = 800,
) -> Dict[str, Any]:
    """Find next *annual* occurrence (Samvatsareekam) of the same paksha+tithi at sunrise.

    Practical rule used here:
    - Match same paksha + same tithi-in-paksha (at sunrise)
    - Ensure the returned date is at least `min_days_after` days after `from_dt`
      (prevents returning a Maasikam-like monthly match when from_dt is the death date)
    """
    target_in_paksha = _tithi_in_paksha(death_tithi_num)

    # Start searching after a minimum gap
    cur = from_dt + timedelta(days=max(min_days_after, 1) - 1)

    for _ in range(max_search_days):
        cur = cur + timedelta(days=1)
        info = _tithi_at_sunrise(cur.year, cur.month, cur.day, latitude, longitude, tz_offset_hours)
        cur_tithi_num = int(info["tithi"]["current_number"])
        cur_paksha = _paksha_from_tithi_num(cur_tithi_num)
        cur_in_paksha = _tithi_in_paksha(cur_tithi_num)

        if cur_paksha == death_paksha and cur_in_paksha == target_in_paksha:
            return {
                "date": cur.isoformat(),
                "sunrise": info["sunrise"],
                "tithi": info["tithi"],
                "paksha": cur_paksha,
                "tithi_in_paksha": cur_in_paksha,
            }

    raise HTTPException(
        status_code=500,
        detail=f"Could not find next samvatsareekam within {max_search_days} days. Check inputs.",
    )


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
    return {
        "message": "Drik Panchanga API",
        "endpoints": {
            "/panchanga": "Daily panchanga for a given date/place",
            "/next-maasikam": "Next maasikam date(s) based on death tithi at sunrise",
            "/next-samvatsareekam": "Next samvatsareekam date based on death tithi at sunrise",
        },
    }


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


# --- Next Maasikam endpoint ---
@app.get("/next-maasikam")
def get_next_maasikam(
    death_year: int = Query(...),
    death_month: int = Query(...),
    death_day: int = Query(...),
    latitude: float = Query(...),
    longitude: float = Query(...),
    tz_offset_hours: float = Query(..., description="UTC offset in hours (IST = 5.5)"),
    from_year: int = Query(None),
    from_month: int = Query(None),
    from_day: int = Query(None),
    count: int = Query(1, ge=1, le=24, description="How many upcoming maasikams to return"),
):
    """Compute next Maasikam date(s) based on death tithi+paksha at sunrise.

    - First compute death tithi at sunrise on the death date (location-specific)
    - Then find the next date(s) after `from_date` where sunrise tithi matches (same paksha + same tithi-in-paksha)

    NOTE: This is a practical implementation and matches common usage. If you need a stricter
    sampradaya-specific rule (e.g., handling special cases around amavasya/poornima, etc.),
    we can add a "rule" parameter later.
    """
    try:
        death_dt = date(death_year, death_month, death_day)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid death date: {e}")

    if from_year and from_month and from_day:
        try:
            from_dt = date(from_year, from_month, from_day)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid from date: {e}")
    else:
        from_dt = death_dt

    # Death tithi at sunrise
    death_info = _tithi_at_sunrise(death_dt.year, death_dt.month, death_dt.day, latitude, longitude, tz_offset_hours)
    death_tithi_num = int(death_info["tithi"]["current_number"])
    death_paksha = _paksha_from_tithi_num(death_tithi_num)

    results = []
    cursor = from_dt
    for _ in range(count):
        nxt = _find_next_matching_tithi_at_sunrise(
            death_tithi_num=death_tithi_num,
            death_paksha=death_paksha,
            from_dt=cursor,
            latitude=latitude,
            longitude=longitude,
            tz_offset_hours=tz_offset_hours,
        )
        results.append(nxt)
        cursor = date.fromisoformat(nxt["date"])  # next search starts from the found date

    return {
        "input": {
            "death_date": death_dt.isoformat(),
            "from_date": from_dt.isoformat(),
            "latitude": latitude,
            "longitude": longitude,
            "tz_offset_hours": tz_offset_hours,
            "count": count,
        },
        "death": {
            "sunrise": death_info["sunrise"],
            "tithi": death_info["tithi"],
            "paksha": death_paksha,
            "tithi_in_paksha": _tithi_in_paksha(death_tithi_num),
        },
        "next_maasikam": results[0] if count == 1 else None,
        "next_maasikams": results,
    }

@app.get("/next-samvatsareekam")
def get_next_samvatsareekam(
    death_year: int = Query(...),
    death_month: int = Query(...),
    death_day: int = Query(...),
    latitude: float = Query(...),
    longitude: float = Query(...),
    tz_offset_hours: float = Query(..., description="UTC offset in hours (IST = 5.5)"),
    from_year: int = Query(None),
    from_month: int = Query(None),
    from_day: int = Query(None),
    min_days_after: int = Query(300, ge=1, le=370, description="Minimum days after from_date before searching (default 300)"),
):
    """Compute next Samvatsareekam date based on death tithi+paksha at sunrise.

    Practical approach:
    - Determine the death tithi at local sunrise for the death date
    - Find the next date whose sunrise tithi matches the same paksha + same tithi-in-paksha
    - Enforce a minimum gap (`min_days_after`) so we don't accidentally return a monthly match

    NOTE: Many traditions also consider additional rules (masa, etc.). We can extend later.
    """
    try:
        death_dt = date(death_year, death_month, death_day)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid death date: {e}")

    if from_year and from_month and from_day:
        try:
            from_dt = date(from_year, from_month, from_day)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid from date: {e}")
    else:
        from_dt = death_dt

    # Death tithi at sunrise
    death_info = _tithi_at_sunrise(death_dt.year, death_dt.month, death_dt.day, latitude, longitude, tz_offset_hours)
    death_tithi_num = int(death_info["tithi"]["current_number"])
    death_paksha = _paksha_from_tithi_num(death_tithi_num)

    nxt = _find_next_annual_matching_tithi_at_sunrise(
        death_tithi_num=death_tithi_num,
        death_paksha=death_paksha,
        from_dt=from_dt,
        latitude=latitude,
        longitude=longitude,
        tz_offset_hours=tz_offset_hours,
        min_days_after=min_days_after,
    )

    return {
        "input": {
            "death_date": death_dt.isoformat(),
            "from_date": from_dt.isoformat(),
            "latitude": latitude,
            "longitude": longitude,
            "tz_offset_hours": tz_offset_hours,
            "min_days_after": min_days_after,
        },
        "death": {
            "sunrise": death_info["sunrise"],
            "tithi": death_info["tithi"],
            "paksha": death_paksha,
            "tithi_in_paksha": _tithi_in_paksha(death_tithi_num),
        },
        "next_samvatsareekam": nxt,
    }
