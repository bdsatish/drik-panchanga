"""CGI request handlers for freesshell.de public_html deployment."""

from __future__ import annotations

import html
import json
import os
import shutil
import sys
import tempfile
import traceback
from pathlib import Path
from urllib.parse import parse_qs

# Repo root is the parent of the webapp/ package.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from generate_panchanga_calendar import (  # noqa: E402
    DEFAULT_FESTIVALS_PATH, build_pdf, default_output_path, load_location, parse_start_month,
)
from webapp.app import (  # noqa: E402
    city_names, safe_download_name, search_cities,
)
from webapp.day_panchanga import compute_day_panchanga  # noqa: E402

PROJECT_ROOT = _REPO_ROOT


def _query_params() -> dict[str, list[str]]:
    return parse_qs(os.environ.get("QUERY_STRING", ""), keep_blank_values=False)


def _parse_urlencoded_post() -> dict[str, str]:
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
    return {key: (values[-1] if values else "") for key, values in parsed.items()}


def write_headers(headers: list[tuple[str, str]], *, status: str | None = None) -> None:
    out = sys.stdout.buffer
    if status:
        # CGI status header (Apache converts this to the HTTP status line).
        out.write(f"Status: {status}\r\n".encode("ascii", errors="replace"))
    for name, value in headers:
        out.write(f"{name}: {value}\r\n".encode("utf-8", errors="replace"))
    out.write(b"\r\n")


def write_text(body: str, *, content_type: str = "text/plain; charset=utf-8", status: str | None = None) -> None:
    data = body.encode("utf-8")
    write_headers([
        ("Content-Type", content_type),
        ("Content-Length", str(len(data))),
        ("Cache-Control", "no-store"),
    ], status=status)
    sys.stdout.buffer.write(data)


def write_json(payload: object, *, status: str | None = None) -> None:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    write_headers([
        ("Content-Type", "application/json; charset=utf-8"),
        ("Content-Length", str(len(data))),
        ("Cache-Control", "no-store"),
    ], status=status)
    sys.stdout.buffer.write(data)


def write_error(message: str, *, status: str = "400 Bad Request", as_json: bool = False) -> None:
    if as_json:
        write_json({"error": message}, status=status)
        return
    safe = html.escape(message)
    body = ("<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
            f"<title>Error</title></head><body><h1>Error</h1><p>{safe}</p>"
            "<p><a href='./'>Back</a></p></body></html>")
    write_text(body, content_type="text/html; charset=utf-8", status=status)


def handle_cities() -> None:
    """GET cities.py?q=...&limit=... → JSON city name list."""
    try:
        params = _query_params()
        query = (params.get("q") or [""])[0]
        try:
            limit = int((params.get("limit") or ["20"])[0])
        except ValueError:
            limit = 20
        limit = min(max(limit, 1), 50)
        city_names()  # fail fast if cities.json is missing
        write_json({"cities": search_cities(query, limit=limit)})
    except Exception as error:  # noqa: BLE001 — surface to the browser for CGI
        write_error(str(error) or traceback.format_exc(), status="500 Internal Server Error", as_json=True)


def handle_panchanga() -> None:
    """GET panchanga.py?city=...&date=DD/MM/YYYY[&month=amanta|purnimanta] → JSON."""
    try:
        params = _query_params()
        city = (params.get("city") or [""])[0]
        date = (params.get("date") or [""])[0]
        month = (params.get("month") or ["amanta"])[0]
        write_json(compute_day_panchanga(city, date, month_system=month))
    except ValueError as error:
        write_error(str(error), as_json=True)
    except Exception as error:  # noqa: BLE001
        write_error(str(error) or traceback.format_exc(), status="500 Internal Server Error", as_json=True)


def handle_generate() -> None:
    """POST generate.py with city + start → PDF attachment."""
    method = os.environ.get("REQUEST_METHOD", "GET").upper()
    if method != "POST":
        write_error("Use POST with form fields city and start (YYYY-MM).", status="405 Method Not Allowed")
        return

    try:
        form = _parse_urlencoded_post()
        city = (form.get("city") or "").strip()
        start = (form.get("start") or "").strip()
        if not city:
            write_error("City is required.")
            return
        if not start:
            write_error("Start month is required (YYYY-MM).")
            return

        start_year, start_month = parse_start_month(start)
        location = load_location(city)
        output_name = default_output_path(location, start_year, start_month).name
        tmp_dir = Path(tempfile.mkdtemp(prefix="panchanga-cgi-"))
        output_path = tmp_dir / output_name
        try:
            generated = build_pdf(location, start_year, start_month, output_path, festivals_path=DEFAULT_FESTIVALS_PATH)
            pdf_bytes = generated.read_bytes()
            download_name = safe_download_name(generated)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

        write_headers([
            ("Content-Type", "application/pdf"),
            ("Content-Disposition", f'attachment; filename="{download_name}"'),
            ("Content-Length", str(len(pdf_bytes))),
            ("Cache-Control", "no-store"),
        ])
        sys.stdout.buffer.write(pdf_bytes)
    except (OSError, ValueError, RuntimeError) as error:
        write_error(str(error))
    except Exception as error:  # noqa: BLE001
        write_error(f"Internal error: {error}", status="500 Internal Server Error")


def handle_status() -> None:
    """GET status.py — tiny health / version probe."""
    try:
        n_cities = len(city_names())
        write_json({
            "ok": True,
            "cities": n_cities,
            "project": str(PROJECT_ROOT),
        })
    except Exception as error:  # noqa: BLE001
        write_error(str(error), status="500 Internal Server Error", as_json=True)
