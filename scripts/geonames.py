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

import csv
import json
import os
import urllib.request
import zipfile

URL = "http://download.geonames.org/export/dump/cities15000.zip"
ZIP_PATH = "/tmp/cities15000.zip"
TXT_PATH = "/tmp/cities15000.txt"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MIN_POPULATION = 60000


def build_cities(txt_path: str = TXT_PATH, min_population: int = MIN_POPULATION) -> dict[str, dict]:
  """Parse the GeoNames dump into ``{Name, ISO}`` record."""
  cities: dict[str, dict] = {}
  with open(txt_path, "r", encoding="utf-8") as fin:
    reader = csv.reader(fin, dialect="excel-tab")
    for record in reader:
      asciiname = record[2]
      latitude, longitude = record[4], record[5]
      countrycode = record[8]
      population = int(record[14])
      timezone = record[17]

      if not asciiname or not countrycode or population <= min_population:
        continue

      place = asciiname.split(",", 1)[0].strip()
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
        cities[key] = entry
  return cities


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
  cities = build_cities()
  out_path = os.path.join(SCRIPT_DIR, "..", "data", "cities.json")
  with open(out_path, "w", encoding="utf-8") as fjson:
    json.dump(cities, fjson, ensure_ascii=False, sort_keys=True)
    fjson.write("\n")

  print(f"Wrote {len(cities)} cities to {out_path}")


if __name__ == "__main__":
  main()
