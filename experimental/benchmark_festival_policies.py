#!/usr/bin/env python3
"""Benchmark a generic festival policy's dates against the traditional policy.

Compares observance dates over a range of calendar years (Jan-Dec windows).
Reports per-festival and overall match/mismatch percentages vs traditional.

Only plain-tithi festivals are compared (the ones a generic policy can affect).
Use --all to include PDF-excluded festivals (Gita Jayanti etc.); default limits
to the PDF-visible subset.

Special case: Janmashtami in the "traditional" reference always uses the
Smarta/Dharma-sindhu Nishitha variant (select_smarta_janmashtami_dates),
not the default Vaishnava variant from resolve_festivals. This matches the
benchmark methodology in FESTIVALS.md.

This script does not depend on reportlab (PDF generation is optional).
"""

import argparse
import calendar
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import panchanga

from experimental.festival_rules import (
    TRADITIONAL_FESTIVAL_POLICY,
    FESTIVAL_POLICIES,
    resolve_festivals,
    plain_tithi_number,
    FESTIVAL_RULES,
    collect_records,
    select_smarta_janmashtami_dates,
    JANMASHTAMI_NUMBER,
    GITA_JAYANTI_NUMBER,
    DHANVANTARI_JAYANTI_NUMBER,
    AYUDHA_PUJA_NUMBER,
    DASARA_NUMBER,
    DURGA_ASHTAMI_NUMBER,
    RAKSHA_BANDHAN_NUMBER,
)

DEFAULT_CITIES_PATH = Path(__file__).with_name("cities.json")


@dataclass(frozen=True)
class Location:
    name: str
    latitude: float
    longitude: float
    timezone_name: str


def make_location(name, latitude, longitude, timezone_name):
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (TypeError, ValueError) as error:
        raise ValueError(f"Invalid coordinates for city {name!r}") from error
    if not -90 <= latitude <= 90:
        raise ValueError(f"Latitude for city {name!r} is outside [-90, 90]")
    if not -180 <= longitude <= 180:
        raise ValueError(f"Longitude for city {name!r} is outside [-180, 180]")
    try:
        ZoneInfo(timezone_name)
    except Exception as error:
        raise ValueError(
            f"Unknown IANA timezone {timezone_name!r} for city {name!r}"
        ) from error
    return Location(name, latitude, longitude, timezone_name)


def location_from_mapping(name, record):
    if not isinstance(record, dict):
        raise ValueError(f"Location record for {name!r} must be an object")
    location_name = record.get("city", record.get("name", name))
    latitude = record.get("latitude", record.get("lat"))
    longitude = record.get("longitude", record.get("lon"))
    timezone_name = record.get(
        "timezone",
        record.get("timezone_name", record.get("tz")),
    )
    if latitude is None or longitude is None or timezone_name is None:
        raise ValueError(
            f"Location record for {location_name!r} needs latitude, "
            "longitude, and timezone"
        )
    return make_location(
        str(location_name),
        latitude,
        longitude,
        str(timezone_name),
    )


def load_location(city):
    path = DEFAULT_CITIES_PATH
    if not path.exists():
        raise ValueError(f"Cities file does not exist: {path}")
    with path.open(encoding="utf-8") as source:
        locations = json.load(source)
    if not isinstance(locations, dict):
        raise ValueError("cities.json must contain an object keyed by city")

    matching_names = [
        name
        for name in locations
        if name.casefold() == city.casefold()
    ]
    if not matching_names:
        import difflib

        suggestions = difflib.get_close_matches(
            city,
            list(locations),
            n=5,
            cutoff=0.6,
        )
        message = f"City {city!r} was not found in {path}"
        if suggestions:
            message += f". Close matches: {', '.join(suggestions)}"
        raise ValueError(message)
    name = matching_names[0]
    return location_from_mapping(name, locations[name])


def timezone_hours(timezone, year, month, day):
    """Return the location's UTC offset, including daylight-saving time."""
    local_noon = datetime(year, month, day, 12, tzinfo=timezone)
    return local_noon.utcoffset().total_seconds() / 3600


def tithi_code(tithi_number):
    if tithi_number <= 15:
        return f"S{tithi_number}"
    return f"K{tithi_number - 15}"


def masa_code(masa_number, is_adhika):
    return f"A{masa_number}" if is_adhika else str(masa_number)


def dms_to_hours(dms):
    hours, minutes, seconds = dms
    return hours + minutes / 60 + seconds / 3600


def daily_values(year, month, location):
    result = []
    timezone = ZoneInfo(location.timezone_name)
    days = calendar.monthrange(year, month)[1]
    for day in range(1, days + 1):
        date = panchanga.Date(year, month, day)
        place = panchanga.Place(
            location.latitude,
            location.longitude,
            timezone_hours(timezone, year, month, day),
        )
        jd = panchanga.gregorian_to_jd(date)
        try:
            sunrise_result = panchanga.sunrise(jd, place)
            sunrise_jd = sunrise_result[0]
            if not jd - 1 <= sunrise_jd <= jd + 2:
                raise RuntimeError("no local sunrise")
            sunset_result = panchanga.sunset(jd, place)
            sunset_jd = sunset_result[0]
            if not jd - 1 <= sunset_jd <= jd + 2:
                raise RuntimeError("no local sunset")
            try:
                moonrise_jd = panchanga.moonrise_jd(jd, place)
                if not jd - 1 <= moonrise_jd <= jd + 2:
                    moonrise_jd = None
            except Exception:
                moonrise_jd = None
            tithi_result = panchanga.tithi(jd, place)
            tithi_number = tithi_result[0]
            tithi_hours_after_sunrise = (
                dms_to_hours(tithi_result[1])
                - dms_to_hours(sunrise_result[1])
            )
            nakshatra_number = panchanga.nakshatra(jd, place)[0]
            yoga_number = panchanga.yoga(jd, place)[0]
            masa_number, is_adhika = panchanga.masa(jd, place)
        except Exception as error:
            raise RuntimeError(
                f"Cannot calculate sunrise panchanga for {location.name} "
                f"on {year:04d}-{month:02d}-{day:02d}: {error}"
            ) from error
        result.append(
            (
                day,
                tithi_code(tithi_number),
                nakshatra_number,
                masa_code(masa_number, is_adhika),
                is_adhika,
                tithi_hours_after_sunrise,
                sunrise_jd - place.timezone / 24,
                sunset_jd - place.timezone / 24,
                yoga_number,
                (
                    moonrise_jd - place.timezone / 24
                    if moonrise_jd is not None
                    else None
                ),
            )
        )
    return result


PDF_EXCLUDED = {
    GITA_JAYANTI_NUMBER,
    DHANVANTARI_JAYANTI_NUMBER,
    AYUDHA_PUJA_NUMBER,
    DASARA_NUMBER,
    DURGA_ASHTAMI_NUMBER,
    RAKSHA_BANDHAN_NUMBER,
}


def invert(festivals_by_date):
    """Invert date->nums to num->sorted unique dates."""
    dbn = defaultdict(list)
    for d, nums in festivals_by_date.items():
        for n in nums:
            dbn[n].append(d)
    for n in list(dbn.keys()):
        dbn[n] = sorted(set(dbn[n]))
    return dbn


def main():
    parser = argparse.ArgumentParser(
        description="Compare policy festival dates vs traditional over years."
    )
    parser.add_argument(
        "--policy",
        choices=FESTIVAL_POLICIES,
        default="generic-anchor",
        help="festival policy to benchmark (default: generic-anchor)",
    )
    parser.add_argument(
        "--city",
        default="Bengaluru",
        help="city name from cities.json (default: Bengaluru)",
    )
    parser.add_argument("--start-year", type=int, default=2026, help="first year")
    parser.add_argument("--end-year", type=int, default=None, help="last year (inclusive)")
    parser.add_argument(
        "--years",
        type=int,
        default=10,
        help="number of years (used if --end-year omitted)",
    )
    parser.add_argument(
        "--all",
        dest="pdf_only",
        action="store_false",
        default=True,
        help="include all plain-tithi festivals (default: PDF-visible subset only)",
    )
    args = parser.parse_args()

    if args.end_year is None:
        args.end_year = args.start_year + args.years - 1
    if args.end_year < args.start_year:
        parser.error("--end-year must be >= --start-year")

    years = list(range(args.start_year, args.end_year + 1))

    try:
        location = load_location(args.city)
    except Exception as exc:
        parser.error(str(exc))

    geopos = (location.longitude, location.latitude, 0.0)

    print(f"Policy: {args.policy}")
    print(f"Location: {location.name}")
    print(f"Period: {args.start_year}-{args.end_year} ({len(years)} years)")
    scope_desc = "PDF-visible plain-tithi" if args.pdf_only else "all plain-tithi"
    print(f"Scope: {scope_desc}")
    print()

    # Precompute daily data for target years + context margins
    miny = min(years) - 1
    maxy = max(years) + 1
    needed = [(y, m) for y in range(miny, maxy + 1) for m in range(1, 13)]
    print(f"Precomputing panchanga for {len(needed)} month(s)...")
    all_data = {}
    for ym in needed:
        all_data[ym] = daily_values(ym[0], ym[1], location)

    trad_per = defaultdict(list)
    pol_per = defaultdict(list)
    successful = []
    name_map = {r.number: r.name for r in FESTIVAL_RULES}

    for y in years:
        target = [(y, m) for m in range(1, 13)]
        ctx = [(y - 1, 12)] + target + [(y + 1, 1)]
        mdata = {k: all_data[k] for k in target if k in all_data}
        cdata = {k: all_data[k] for k in ctx if k in all_data}
        try:
            tbd, _ = resolve_festivals(
                target,
                mdata,
                TRADITIONAL_FESTIVAL_POLICY,
                context_months=ctx,
                context_data=cdata,
                geopos=geopos,
            )

            # Use Smarta / Dharma-sindhu Nishitha variant for Janmashtami as the
            # traditional reference (instead of the Vaishnava variant that the
            # default resolve_festivals selects for traditional policy).
            # This matches the benchmark methodology described in FESTIVALS.md.
            janma_rule = next(
                (r for r in FESTIVAL_RULES if r.number == JANMASHTAMI_NUMBER), None
            )
            if janma_rule is not None:
                trad_records = collect_records(target, mdata)
                smarta_dates = select_smarta_janmashtami_dates(trad_records, janma_rule)
                # Remove any Vaishnava Janmashtami dates that resolve_festivals added
                for d in list(tbd.keys()):
                    if JANMASHTAMI_NUMBER in tbd[d]:
                        tbd[d] = [n for n in tbd[d] if n != JANMASHTAMI_NUMBER]
                        if not tbd[d]:
                            del tbd[d]
                # Insert the Smarta dates
                for d in smarta_dates:
                    if d.year == y:
                        tbd.setdefault(d, []).append(JANMASHTAMI_NUMBER)

            pbd, _ = resolve_festivals(
                target,
                mdata,
                args.policy,
                context_months=ctx,
                context_data=cdata,
                geopos=geopos,
            )
            successful.append(y)
            tdbn = invert(tbd)
            pdbn = invert(pbd)
            for num, ds in tdbn.items():
                for d in ds:
                    if d.year == y:
                        trad_per[num].append(d)
            for num, ds in pdbn.items():
                for d in ds:
                    if d.year == y:
                        pol_per[num].append(d)
        except Exception as exc:
            print(f"  Skipping {y}: {exc}")

    print(f"Successful reference years: {len(successful)}")
    print()

    # Relevant festivals: plain-tithi, optionally PDF-excluded
    relevant = []
    for r in FESTIVAL_RULES:
        if plain_tithi_number(r.tithi) is None:
            continue
        if args.pdf_only and r.number in PDF_EXCLUDED:
            continue
        relevant.append(r.number)
    relevant = sorted(set(relevant))

    total_pol = 0
    total_match = 0
    rows = []
    for num in relevant:
        tds = trad_per.get(num, [])
        pds = pol_per.get(num, [])
        tset = set(tds)
        n_match = sum(1 for d in pds if d in tset)
        n_pol = len(pds)
        total_pol += n_pol
        total_match += n_match
        pct = (100.0 * n_match / n_pol) if n_pol > 0 else 0.0
        rows.append((num, name_map.get(num, f"#{num}"), n_match, n_pol, pct))

    # Table
    print(f"{'#':>3}  {'Festival':<32}  {'match / pol':>11}   {'%':>6}")
    print("-" * 58)
    for num, nm, m, tot, p in rows:
        print(f"{num:>3}  {nm:<32}  {m:>4}/{tot:<4}   {p:6.2f}")
    print("-" * 58)

    if total_pol > 0:
        overall_pct = 100.0 * total_match / total_pol
    else:
        overall_pct = 0.0
    mismatch_pct = 100.0 - overall_pct if total_pol > 0 else 0.0

    print(
        f"OVERALL: {total_match}/{total_pol}  "
        f"match={overall_pct:.2f}%  mismatch={mismatch_pct:.2f}%"
    )
    print()


if __name__ == "__main__":
    main()
