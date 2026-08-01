#!/usr/bin/env bash
# HTTP smoke checks against a running panchanga web server.
# Usage: ci_smoke_http.sh [base_url]
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8765}"
BASE_URL="${BASE_URL%/}"
TIMEOUT_SECS="${SMOKE_WAIT_SECS:-60}"

echo "smoke: waiting for ${BASE_URL}/ (up to ${TIMEOUT_SECS}s)"
deadline=$((SECONDS + TIMEOUT_SECS))
until curl -fsS --max-time 2 "${BASE_URL}/" >/dev/null 2>&1; do
  if (( SECONDS >= deadline )); then
    echo "error: server did not become ready at ${BASE_URL}/" >&2
    exit 1
  fi
  sleep 1
done

echo "smoke: GET /"
html="$(curl -fsS --max-time 10 "${BASE_URL}/")"
grep -qi 'panchanga' <<<"${html}"

echo "smoke: GET /api/cities"
cities_json="$(curl -fsS --max-time 10 "${BASE_URL}/api/cities?q=Bengaluru")"
python3 - "${cities_json}" <<'PY'
import json, sys
data = json.loads(sys.argv[1])
cities = data.get("cities") or []
assert isinstance(cities, list) and cities, data
assert any(c.casefold() == "bengaluru, in" for c in cities), cities
print("cities ok:", cities[:5])
PY

echo "smoke: GET /api/panchanga"
panchanga_json="$(curl -fsS --max-time 30 \
  --get "${BASE_URL}/api/panchanga" \
  --data-urlencode "city=Bengaluru, IN" \
  --data-urlencode "date=15/01/2026")"
python3 - "${panchanga_json}" <<'PY'
import json, sys
data = json.loads(sys.argv[1])
for key in (
    "city", "date", "samvatsara", "ayana", "masa", "rtu", "vaara",
    "kali_day", "saka_year", "kali_year", "vikrama_year",
    "jd", "sunrise_jd", "ayanamsa_degrees",
    "sunrise", "sunset", "day_duration",
    "rahu_kala", "durmuhurta",
    "tithi", "nakshatra", "yoga", "karana",
):
    assert key in data and data[key] not in (None, ""), (key, data)
assert data["city"] == "Bengaluru, IN", data["city"]
assert data["date"] == "15/01/2026", data["date"]
assert data.get("month_system", "amanta") == "amanta", data.get("month_system")
assert data.get("ayanamsa") == "True Citra", data.get("ayanamsa")
assert data.get("ayanamsa_key", "citra") == "citra", data.get("ayanamsa_key")
assert isinstance(data["tithi"], list) and data["tithi"], data["tithi"]
assert data["rahu_kala"].get("start") and data["rahu_kala"].get("end"), data["rahu_kala"]
assert isinstance(data["durmuhurta"], list) and data["durmuhurta"], data["durmuhurta"]
assert float(data["jd"]) > 0 and float(data["ayanamsa_degrees"]) > 0
print("panchanga ok:", data["vaara"], data["masa"], f"JD {data['jd']}", f"ayan {data['ayanamsa_degrees']}°")
PY

echo "smoke: GET /api/panchanga (purnimanta)"
purni_json="$(curl -fsS --max-time 30 \
  --get "${BASE_URL}/api/panchanga" \
  --data-urlencode "city=Bengaluru, IN" \
  --data-urlencode "date=15/03/2023" \
  --data-urlencode "month=purnimanta")"
python3 - "${purni_json}" <<'PY'
import json, sys
data = json.loads(sys.argv[1])
assert data["month_system"] == "purnimanta", data["month_system"]
assert data["masa_number"] == 1, data
print("purnimanta ok:", data["masa"])
PY

echo "smoke: GET /api/panchanga (raman ayanamsa)"
raman_json="$(curl -fsS --max-time 30 \
  --get "${BASE_URL}/api/panchanga" \
  --data-urlencode "city=Bengaluru, IN" \
  --data-urlencode "date=15/01/2026" \
  --data-urlencode "ayanamsa=raman")"
python3 - "${raman_json}" <<'PY'
import json, sys
data = json.loads(sys.argv[1])
assert data["ayanamsa"] == "Raman", data["ayanamsa"]
assert data["ayanamsa_key"] == "raman", data["ayanamsa_key"]
assert float(data["ayanamsa_degrees"]) > 0
print("raman ok:", data["ayanamsa"], f"{data['ayanamsa_degrees']}°")
PY

echo "smoke: POST /generate"
pdf_tmp="$(mktemp --suffix=.pdf)"
cleanup() { rm -f "${pdf_tmp}"; }
trap cleanup EXIT
curl -fsS --max-time 120 \
  -X POST \
  -F "city=Bengaluru, IN" \
  -F "start=2026-03" \
  -F "month=amanta" \
  -o "${pdf_tmp}" \
  "${BASE_URL}/generate"
python3 - "${pdf_tmp}" <<'PY'
import sys
from pathlib import Path
path = Path(sys.argv[1])
data = path.read_bytes()
assert data.startswith(b"%PDF"), data[:20]
assert len(data) > 1000, len(data)
assert b"amanta masa" in data, "expected amanta masa in PDF metadata"
print("pdf ok:", len(data), "bytes")
PY

echo "smoke: POST /generate (purnimanta)"
curl -fsS --max-time 180 \
  -X POST \
  -F "city=Bengaluru, IN" \
  -F "start=2023-03" \
  -F "month=purnimanta" \
  -o "${pdf_tmp}" \
  "${BASE_URL}/generate"
python3 - "${pdf_tmp}" <<'PY'
import sys
from pathlib import Path
data = Path(sys.argv[1]).read_bytes()
assert data.startswith(b"%PDF"), data[:20]
assert b"purnimanta masa" in data, "expected purnimanta masa in PDF metadata"
print("purnimanta pdf ok:", len(data), "bytes")
PY

echo "smoke: all checks passed"
