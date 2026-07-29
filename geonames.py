#!/usr/bin/env python3
"""Build cities.json from the GeoNames cities15000 dump.

Keys are always ``AsciiName, ISO`` (ISO 3166-1 alpha-2 country code), e.g.
``Sydney, AU`` and ``Sydney, CA``. That avoids silent overwrites when several
countries share a city name. AsciiNames that contain commas (rare GeoNames
admin composites) are reduced to the segment before the first comma so each
key has exactly one comma — the separator before the country code.

If the same name+country appears more than once (duplicate admin entries),
the row with the larger population is kept.

Download source: http://download.geonames.org/export/dump/cities15000.zip
"""

from __future__ import annotations

import csv
import json
import os
import re
import urllib.request
import zipfile

URL = "http://download.geonames.org/export/dump/cities15000.zip"
ZIP_PATH = "/tmp/cities15000.zip"
TXT_PATH = "/tmp/cities15000.txt"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MIN_POPULATION = 60000

# Key shape: place name, then ", ", then a 2-letter ISO country code.
_KEY_RE = re.compile(r"^(.+),\s*([A-Za-z]{2})$")


def asciiname_without_commas(asciiname: str) -> str:
    """Drop GeoNames composite suffixes so the place name has no commas."""
    return asciiname.split(",", 1)[0].strip()


def strip_commas_from_city_keys(cities: dict[str, dict]) -> tuple[dict[str, dict], int]:
    """Rename keys whose place name still contains commas (post-generation pass).

    Returns ``(cleaned_cities, rename_count)``. When two keys collapse to the
    same ``Name, ISO``, the higher-population entry wins.
    """
    cleaned: dict[str, dict] = {}
    renamed = 0
    for key, entry in cities.items():
        match = _KEY_RE.fullmatch(key.strip())
        if not match:
            cleaned[key] = entry
            continue
        place, country = match.group(1).rstrip(), match.group(2).upper()
        if "," not in place:
            new_key = f"{place}, {country}"
        else:
            new_key = f"{asciiname_without_commas(place)}, {country}"
            renamed += 1
        previous = cleaned.get(new_key)
        if previous is None or entry["population"] > previous["population"]:
            cleaned[new_key] = entry
    return cleaned, renamed


def build_cities(txt_path: str = TXT_PATH, min_population: int = MIN_POPULATION) -> tuple[dict[str, dict], int]:
    """Parse the GeoNames dump into ``{Name, ISO: record}`` (commas already stripped)."""
    cities: dict[str, dict] = {}
    replaced_same_key = 0
    with open(txt_path, "r", encoding="utf-8") as fin:
        reader = csv.reader(fin, dialect="excel-tab")
        for record in reader:
            (
                _geonameid,
                _name,
                asciiname,
                _alternatenames,
                latitude,
                longitude,
                _featureclass,
                _featurecode,
                countrycode,
                _cc2,
                _admin1code,
                _admin2code,
                _admin3code,
                _admin4code,
                population,
                _elevation,
                _dem,
                timezone,
                _modificationdate,
            ) = record

            if not asciiname or not countrycode:
                continue
            population = int(population)
            if population <= min_population:
                continue

            place = asciiname_without_commas(asciiname)
            if not place:
                continue
            key = f"{place}, {countrycode.upper()}"
            entry = {
                "latitude": float(latitude),
                "longitude": float(longitude),
                "timezone": timezone,
                "country": countrycode.upper(),
                "population": population,
            }
            previous = cities.get(key)
            if previous is None or population > previous["population"]:
                if previous is not None:
                    replaced_same_key += 1
                cities[key] = entry
    return cities, replaced_same_key


def ensure_dump(txt_path: str = TXT_PATH, zip_path: str = ZIP_PATH, url: str = URL) -> None:
    if os.path.exists(txt_path):
        return
    print("Downloading cities15000.zip ...")
    urllib.request.urlretrieve(url, zip_path)
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(os.path.dirname(txt_path) or ".")
    os.remove(zip_path)
    print("Done.")


def main() -> None:
    ensure_dump()
    cities, replaced_same_key = build_cities()
    cities, comma_renames = strip_commas_from_city_keys(cities)

    out_path = os.path.join(SCRIPT_DIR, "cities.json")
    with open(out_path, "w", encoding="utf-8") as fjson:
        json.dump(cities, fjson, ensure_ascii=False, sort_keys=True)
        fjson.write("\n")

    print(f"Wrote {len(cities)} cities to {out_path}")
    print(f"Same-key population replacements: {replaced_same_key}")
    print(f"Comma-stripped place-name renames: {comma_renames}")


if __name__ == "__main__":
    main()
