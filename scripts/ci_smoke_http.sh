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
assert any(c.casefold() == "bengaluru" for c in cities), cities
print("cities ok:", cities[:5])
PY

echo "smoke: GET /api/panchanga"
panchanga_json="$(curl -fsS --max-time 30 \
  "${BASE_URL}/api/panchanga?city=Bengaluru&date=15/01/2026")"
python3 - "${panchanga_json}" <<'PY'
import json, sys
data = json.loads(sys.argv[1])
for key in (
    "city", "date", "samvatsara", "masa", "rtu", "vaara",
    "kali_day", "saka_year", "kali_year",
    "sunrise", "sunset", "day_duration",
    "tithi", "nakshatra", "yoga", "karana",
):
    assert key in data and data[key] not in (None, ""), (key, data)
assert data["city"] == "Bengaluru", data["city"]
assert data["date"] == "15/01/2026", data["date"]
assert isinstance(data["tithi"], list) and data["tithi"], data["tithi"]
print("panchanga ok:", data["vaara"], data["masa"])
PY

echo "smoke: POST /generate"
pdf_tmp="$(mktemp --suffix=.pdf)"
cleanup() { rm -f "${pdf_tmp}"; }
trap cleanup EXIT
curl -fsS --max-time 120 \
  -X POST \
  -F "city=Bengaluru" \
  -F "start=2026-03" \
  -o "${pdf_tmp}" \
  "${BASE_URL}/generate"
python3 - "${pdf_tmp}" <<'PY'
import sys
from pathlib import Path
path = Path(sys.argv[1])
data = path.read_bytes()
assert data.startswith(b"%PDF"), data[:20]
assert len(data) > 1000, len(data)
print("pdf ok:", len(data), "bytes")
PY

echo "smoke: all checks passed"
