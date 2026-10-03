#!/usr/bin/env python3
"""Minimal web UI for generating one-page panchanga calendar PDFs."""

import io
import ipaddress
import json
import logging
import os
import sys
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

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
  load_location,
  location_slug,
  require_coordinate_selection,
  require_month_system,
  require_start_year,
  resolve_location,
  _format_year,
)
from panchanga import sweph_version
from webapp.day_panchanga import compute_day_panchanga
from webapp.pdf_service import PDF_UNAVAILABLE, generate_pdf
from webapp.ics_service import generate_ics

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


def city_search_limit(raw_limit):
  """Parse a city-search limit, defaulting invalid input to 20 and capping at 50."""
  try:
    limit = int(raw_limit)
  except (TypeError, ValueError):
    limit = 20
  return min(max(limit, 1), 50)


def suggest_city_for_ip(ip):
  """Public IP → ipwho.is city → cities.json key, or None.
  Non-https URL leaks user's IP address to any other provider on the path.
  """
  try:
    if not ip or not ipaddress.ip_address(ip.strip()).is_global:
      return None
    url = "https://ipwho.is/" + quote(ip.strip())
    req = urlopen(Request(url, headers={"User-Agent": "drik-panchanga/2.0"}), timeout=1.5)
    with req as resp:
      data = json.loads(resp.read().decode())
    if not data.get("success"):
      return None
    return load_location(f"{data['city']}, {data['country_code']}").name
  except (ValueError, KeyError, TypeError, OSError, TimeoutError, json.JSONDecodeError) as error:
    log.error("City suggestion failed for IP %r: %s", ip, error)
    return None


@app.get("/")
def index():
  return render_template("index.html")


@app.get("/api/cities")
def api_cities():
  query = request.args.get("q", "")
  limit = city_search_limit(request.args.get("limit", 20))
  return jsonify({"cities": search_cities(query, limit=limit)})


def _trusted_proxy_hops():
  """How many leading X-Forwarded-For hops to trust, from ``PANCHANGA_TRUSTED_PROXY_HOPS``.

  0 (default) ignores X-Forwarded-For entirely and uses the socket peer
  address: without a trusted reverse proxy, that header is client-controlled.
  Deployments behind exactly N trusted proxies set N, and the client IP is
  then taken N entries from the right of the X-Forwarded-For list (proxies
  append, so the leftmost entries are the ones a client can spoof).
  """
  raw = os.environ.get("PANCHANGA_TRUSTED_PROXY_HOPS", "0")
  try:
    return max(0, int(raw))
  except ValueError:
    log.warning("Invalid PANCHANGA_TRUSTED_PROXY_HOPS %r, ignoring X-Forwarded-For", raw)
    return 0


def client_ip(xff, remote, trusted_hops=None):
  """Client IP honoring the ``PANCHANGA_TRUSTED_PROXY_HOPS`` trust model.

  With 0 trusted hops (the default) this is the socket peer address; with N
  it is the entry N positions from the right of a comma-separated
  X-Forwarded-For list, falling back to the peer address when the header is
  missing or shorter than N.
  """
  remote = (remote or "").strip()
  if trusted_hops is None:
    trusted_hops = _trusted_proxy_hops()
  if not trusted_hops or not xff:
    return remote
  hops = [hop.strip() for hop in xff.split(",")]
  if len(hops) < trusted_hops:
    return remote
  return hops[-trusted_hops]


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
  place = request.args.get("place")
  try:
    if ayanamsa:
      ayanamsa = ayanamsa.strip()
    coordinate_selection = require_coordinate_selection(ayanamsa)
    if month:
      month = month.strip()
    return jsonify(
      compute_day_panchanga(city, date, month_system=month, coordinate_selection=coordinate_selection, place=place))
  except ValueError as error:
    abort(400, description=str(error))


@app.post("/generate")
def generate():
  try:
    pdf_bytes, filename = generate_pdf(request.form)
  except (ValueError, RuntimeError) as error:
    abort(400, description=str(error))
  except ImportError as error:
    # A missing module (check_reportlab's [pdf] extra hint) is the server's fault.
    abort(503, description=str(error))
  except OSError as error:
    # Missing fonts or data files; the message carries server paths.
    log.error("PDF generation failed: %s", error)
    abort(503, description=PDF_UNAVAILABLE)
  return send_file(io.BytesIO(pdf_bytes), mimetype="application/pdf", as_attachment=True, download_name=filename,
                   max_age=0)


@app.get("/api/panchanga.ics")
def ics_calendar():
  city = (request.args.get("city") or "").strip()
  start = (request.args.get("start") or "").strip()
  try:
    location = resolve_location(city, request.args.get("place"))
    start_year = require_start_year(start)
    month = (request.args.get("month") or "amanta").strip()
    amanta = require_month_system(month)
    month_key = "amanta" if amanta else "purnimanta"
    coordinate_selection = require_coordinate_selection((request.args.get("ayanamsa") or "").strip() or None)
    ics_text = generate_ics(location, start_year, month_system=month, coordinate_selection=coordinate_selection)
  except (OSError, ValueError, RuntimeError) as error:
    abort(400, description=str(error))
  # The lunar year is what ``start`` names, so the resolved months add nothing
  # here; the coordinate and month system are already in the name.
  name = (f"panchanga-{location_slug(location.name)}-{coordinate_selection}-{month_key}-"
          f"{_format_year(start_year)}.ics")
  return send_file(io.BytesIO(ics_text.encode("utf-8")), mimetype="text/calendar", as_attachment=True,
                   download_name=name, max_age=0)


@app.errorhandler(400)
@app.errorhandler(503)
def bad_request(error):
  message = getattr(error, "description", None) or "Bad request"
  # Browsers also send ``*/*``, which matches JSON; a failed PDF form must still
  # show the page with its error, so JSON only when preferred over HTML.
  wants_json = request.accept_mimetypes.best_match(["text/html", "application/json"]) == "application/json"
  if wants_json or request.path.startswith("/api/"):
    return jsonify({"error": message}), error.code
  return render_template("index.html", error=message), error.code


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
