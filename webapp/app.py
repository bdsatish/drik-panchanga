#!/usr/bin/env python3
"""Minimal web UI for generating one-page panchanga calendar PDFs."""

import io
import ipaddress
import json
import logging
import sys
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen

from flask import (
  Flask,
  abort,
  jsonify,
  render_template,
  request,
  send_file,
)

# Repo root (parent of this package) so core modules import cleanly when
# launched as ``python -m webapp.app`` or via gunicorn ``webapp.app:app``.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(_REPO_ROOT))

from generate_panchanga_calendar import (
  city_locations,
  configure_logging,
  load_location,
  location_slug,
  require_coordinate_selection,
  require_month_system,
  require_start_month,
)
from panchanga import sweph_version
from webapp.day_panchanga import compute_day_panchanga
from webapp.pdf_service import generate_pdf
from webapp.ics_service import generate_ics

configure_logging()
app = Flask(__name__)
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

_CITY_NAMES = None


@app.context_processor
def inject_sweph_version():
  return {"sweph_version": sweph_version()}


def city_names():
  global _CITY_NAMES
  if _CITY_NAMES is None:
    _CITY_NAMES = tuple(sorted(city_locations().keys(), key=str.casefold))
  return _CITY_NAMES


def search_cities(query, limit=20):
  query = query.strip()
  if not query:
    return []
  folded = query.casefold()
  records = city_locations()
  starts = []
  contains = []
  for name in city_names():
    name_folded = name.casefold()
    base_folded = name_folded.rsplit(", ", 1)[0]
    if name_folded.startswith(folded) or base_folded.startswith(folded):
      starts.append(name)
    elif folded in name_folded:
      contains.append(name)
  sort_key = lambda name: (-int(records[name].get("population") or 0), name.casefold())
  starts.sort(key=sort_key)
  contains.sort(key=sort_key)
  return (starts + contains)[:limit]


def suggest_city_for_ip(ip):
  """Public IP → ip-api.com city → cities.json key, or None."""
  try:
    if not ip or not ipaddress.ip_address(ip.strip()).is_global:
      return None
    url = ("http://ip-api.com/json/" + quote(ip.strip()) + "?fields=status,city,countryCode")
    with urlopen(url, timeout=1.5) as resp:
      data = json.loads(resp.read().decode())
    if data.get("status") != "success":
      return None
    return load_location(f"{data['city']}, {data['countryCode']}").name
  except (ValueError, KeyError, TypeError, OSError, TimeoutError, json.JSONDecodeError) as error:
    log.error("City suggestion failed for IP %r: %s", ip, error)
    return None


@app.get("/")
def index():
  return render_template("index.html")


@app.get("/api/cities")
def api_cities():
  query = request.args.get("q", "")
  try:
    limit = min(max(int(request.args.get("limit", 20)), 1), 50)
  except ValueError:
    limit = 20
  return jsonify({"cities": search_cities(query, limit=limit)})


def client_ip(xff, remote):
  """First X-Forwarded-For hop, else direct remote address."""
  ip = xff.split(",")[0].strip() if xff else (remote or "").strip()
  return ip


@app.get("/api/suggest-city")
def api_suggest_city():
  ip = client_ip(request.headers.get("X-Forwarded-For", ""), request.remote_addr)
  return jsonify({"city": suggest_city_for_ip(ip)})


@app.get("/api/panchanga")
def api_panchanga():
  city = (request.args.get("city") or "").strip()
  date = (request.args.get("date") or "").strip()
  month = request.args.get("month")
  ayanamsa = request.args.get("ayanamsa")
  try:
    if ayanamsa:
      ayanamsa = ayanamsa.strip()
    coordinate_selection = require_coordinate_selection(ayanamsa)
    if month:
      month = month.strip()
    return jsonify(compute_day_panchanga(city, date, month_system=month, coordinate_selection=coordinate_selection))
  except ValueError as error:
    abort(400, description=str(error))


@app.post("/generate")
def generate():
  try:
    pdf_bytes, filename = generate_pdf(request.form)
  except (OSError, ValueError, RuntimeError) as error:
    abort(400, description=str(error))
  return send_file(io.BytesIO(pdf_bytes), mimetype="application/pdf", as_attachment=True, download_name=filename,
                   max_age=0)


@app.get("/api/panchanga.ics")
def ics_calendar():
  city = (request.args.get("city") or "").strip()
  start = (request.args.get("start") or "").strip()
  try:
    location = load_location(city)
    start_year, start_month = require_start_month(start)
    month = (request.args.get("month") or "amanta").strip()
    amanta = require_month_system(month)
    month_key = "amanta" if amanta else "purnimanta"
    coordinate_selection = require_coordinate_selection((request.args.get("ayanamsa") or "").strip() or None)
    ics_text = generate_ics(location, start_year, start_month, month_system=month,
                            coordinate_selection=coordinate_selection)
  except (OSError, ValueError, RuntimeError) as error:
    abort(400, description=str(error))
  name = (f"panchanga-{location_slug(city)}-{coordinate_selection}-{month_key}-"
          f"{start_year:04d}-{start_month:02d}.ics")
  return send_file(io.BytesIO(ics_text.encode("utf-8")), mimetype="text/calendar; charset=utf-8", as_attachment=True,
                   download_name=name, max_age=0)


@app.errorhandler(400)
def bad_request(error):
  message = getattr(error, "description", None) or "Bad request"
  if request.accept_mimetypes.best == "application/json" or request.path.startswith("/api/"):
    return jsonify({"error": message}), 400
  return render_template("index.html", error=message), 400


def main():
  import argparse
  import os

  parser = argparse.ArgumentParser(description="Serve the panchanga PDF web UI.")
  parser.add_argument("--host", default=os.environ.get("PANCHANGA_HOST", "0.0.0.0"),
                      help="bind address (default: 0.0.0.0, or PANCHANGA_HOST)")
  parser.add_argument(
    "--port",
    type=int,
    # Railway/Heroku set PORT; local default remains 8765.
    default=int(os.environ.get("PORT") or os.environ.get("PANCHANGA_PORT") or "8765"),
    help="TCP port (default: PORT / PANCHANGA_PORT / 8765)")
  parser.add_argument("--debug", action="store_true", help="enable Flask debug reloader")
  args = parser.parse_args()
  # 0.0.0.0 so the UI is reachable from other devices on the LAN.
  app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
  main()
