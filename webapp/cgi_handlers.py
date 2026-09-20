"""CGI request handlers for freesshell.de public_html deployment."""

import html
import json
import logging
import os
import sys
import traceback
from pathlib import Path
from urllib.parse import parse_qs

# Repo root is the parent of the webapp/ package.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(_REPO_ROOT))

from webapp.app import (
  city_search_limit,
  city_names,
  client_ip,
  search_cities,
  suggest_city_for_ip,
)
from webapp.day_panchanga import compute_day_panchanga
from webapp.pdf_service import generate_pdf
from generate_panchanga_calendar import configure_logging, require_coordinate_selection

configure_logging()
PROJECT_ROOT = _REPO_ROOT
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


def _query_params():
  return parse_qs(os.environ.get("QUERY_STRING", ""), keep_blank_values=False)


def _parse_urlencoded_post():
  """Parse a classic HTML form POST (not multipart)."""
  try:
    length = int(os.environ.get("CONTENT_LENGTH") or "0")
  except ValueError:
    length = 0
  raw = sys.stdin.buffer.read(length) if length > 0 else b""
  content_type = os.environ.get("CONTENT_TYPE", "")
  if content_type and "application/x-www-form-urlencoded" not in content_type:
    raise ValueError("Unsupported Content-Type for generate: "
                     f"{content_type!r} (expected application/x-www-form-urlencoded)")
  parsed = parse_qs(raw.decode("utf-8", errors="replace"), keep_blank_values=True)
  fields = {}
  for key, values in parsed.items():
    if values:
      fields[key] = values[-1]
    else:
      fields[key] = ""
  return fields


def _emit(headers, body=b"", status=None):
  """Write a complete CGI response in a single call.

  Building the header block and body together means a partial write cannot
  leave headers without a body, or a body after a failed header write.
  """
  chunks = []
  if status:
    # CGI status header (Apache converts this to the HTTP status line).
    chunks.append(f"Status: {status}\r\n".encode("ascii", errors="replace"))
  for name, value in headers:
    chunks.append(f"{name}: {value}\r\n".encode("utf-8", errors="replace"))
  chunks.append(b"\r\n")
  chunks.append(body)
  sys.stdout.buffer.write(b"".join(chunks))


def write_headers(headers, status=None):
  _emit(headers, status=status)


def write_text(body, content_type="text/plain; charset=utf-8", status=None):
  data = body.encode("utf-8")
  _emit([
    ("Content-Type", content_type),
    ("Content-Length", str(len(data))),
    ("Cache-Control", "no-store"),
  ], body=data, status=status)


def write_json(payload, status=None):
  data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
  _emit([
    ("Content-Type", "application/json; charset=utf-8"),
    ("Content-Length", str(len(data))),
    ("Cache-Control", "no-store"),
  ], body=data, status=status)


def write_error(message, status="400 Bad Request", as_json=False):
  if as_json:
    write_json({"error": message}, status=status)
    return
  safe = html.escape(message)
  body = ("<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
          f"<title>Error</title></head><body><h1>Error</h1><p>{safe}</p>"
          "<p><a href='./'>Back</a></p></body></html>")
  write_text(body, content_type="text/html; charset=utf-8", status=status)


def handle_cities():
  """GET cities.py?q=...&limit=... → JSON city name list."""
  try:
    params = _query_params()
    query = (params.get("q") or [""])[0]
    limit = city_search_limit((params.get("limit") or ["20"])[0])
    payload = {"cities": search_cities(query, limit=limit)}
  except Exception as error:  # catch-all so CGI still returns a response
    log.error("CGI cities failed: %s", error)
    write_error(str(error) or traceback.format_exc(), status="500 Internal Server Error", as_json=True)
    return
  write_json(payload)


def handle_suggest_city():
  """GET suggest_city.py → JSON ``{\"city\": ...}`` from client IP."""
  try:
    ip = client_ip(os.environ.get("HTTP_X_FORWARDED_FOR", ""), os.environ.get("REMOTE_ADDR"))
    payload = {"city": suggest_city_for_ip(ip)}
  except Exception as error:  # catch-all so CGI still returns a response
    log.error("CGI suggest_city failed: %s", error)
    write_error(str(error) or traceback.format_exc(), status="500 Internal Server Error", as_json=True)
    return
  write_json(payload)


def handle_panchanga():
  """GET panchanga.py?city=...&date=...[&month=...][&ayanamsa=...] → JSON."""
  try:
    params = _query_params()
    city = (params.get("city") or [""])[0]
    date = (params.get("date") or [""])[0]
    month = (params.get("month") or ["amanta"])[0]
    a = params.get("ayanamsa")
    if a:
      ayanamsa = a[0]
    else:
      ayanamsa = None
    coordinate_selection = require_coordinate_selection(ayanamsa)
    payload = compute_day_panchanga(city, date, month_system=month, coordinate_selection=coordinate_selection)
  except ValueError as error:
    write_error(str(error), as_json=True)
    return
  except Exception as error:  # catch-all so CGI still returns a response
    log.error("CGI panchanga failed: %s", error)
    write_error(str(error) or traceback.format_exc(), status="500 Internal Server Error", as_json=True)
    return
  write_json(payload)


def handle_generate():
  """POST generate.py with city + start + optional month → PDF attachment."""
  method = os.environ.get("REQUEST_METHOD", "GET").upper()
  if method != "POST":
    write_error("Use POST with form fields city and start (YYYY-MM).", status="405 Method Not Allowed")
    return

  # Build the whole response before emitting anything: once headers are on the
  # wire a later failure cannot replace them, so the error path must never run
  # after output has started (that emitted a second header block).
  try:
    form = _parse_urlencoded_post()
    pdf_bytes, filename = generate_pdf(form)
  except (OSError, ValueError, RuntimeError) as error:
    write_error(str(error))
    return
  except Exception as error:  # catch-all so CGI still returns a response
    log.error("CGI generate failed: %s", error)
    write_error(f"Internal error: {error}", status="500 Internal Server Error")
    return

  _emit([
    ("Content-Type", "application/pdf"),
    ("Content-Disposition", f'attachment; filename="{filename}"'),
    ("Content-Length", str(len(pdf_bytes))),
    ("Cache-Control", "no-store"),
  ], body=pdf_bytes)


def handle_status():
  """GET status.py — tiny health / version probe."""
  try:
    n_cities = len(city_names())
    payload = {
      "ok": True,
      "cities": n_cities,
      "project": str(PROJECT_ROOT),
    }
  except Exception as error:  # catch-all so CGI still returns a response
    log.error("CGI status failed: %s", error)
    write_error(str(error), status="500 Internal Server Error", as_json=True)
    return
  write_json(payload)
