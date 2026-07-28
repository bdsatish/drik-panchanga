#!/usr/bin/env python3
"""Build cities.json from the GeoNames cities15000 dump.

Keys are always ``AsciiName, ISO`` (ISO 3166-1 alpha-2 country code), e.g.
``Sydney, AU`` and ``Sydney, CA``. That avoids silent overwrites when several
countries share a city name.

If the same name+country appears more than once (duplicate admin entries),
the row with the larger population is kept.

Download source: http://download.geonames.org/export/dump/cities15000.zip
"""

from __future__ import annotations

import csv
import json
import os
import urllib.request
import zipfile

url = "http://download.geonames.org/export/dump/cities15000.zip"
zip_path = "/tmp/cities15000.zip"
txt_path = "/tmp/cities15000.txt"
script_dir = os.path.dirname(os.path.abspath(__file__))
min_population = 60000

if not os.path.exists(txt_path):
    print("Downloading cities15000.zip ...")
    urllib.request.urlretrieve(url, zip_path)
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall("/tmp")
    os.remove(zip_path)
    print("Done.")

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

        key = f"{asciiname}, {countrycode.upper()}"
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

out_path = os.path.join(script_dir, "cities.json")
with open(out_path, "w", encoding="utf-8") as fjson:
    json.dump(cities, fjson, ensure_ascii=False, sort_keys=True)
    fjson.write("\n")

print(f"Wrote {len(cities)} cities to {out_path}")
print(f"Same-key population replacements: {replaced_same_key}")
