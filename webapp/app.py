#!/usr/bin/env python3
"""Minimal web UI for generating one-page panchanga calendar PDFs."""

from __future__ import annotations

import io
import json
import re
import shutil
import sys
import tempfile
from functools import lru_cache
from pathlib import Path

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

from generate_panchanga_calendar import (  # noqa: E402
    DEFAULT_CITIES_PATH, DEFAULT_FESTIVALS_PATH, build_pdf, default_output_path, load_location, parse_start_month,
)

app = Flask(__name__)


@lru_cache(maxsize=1)
def city_names() -> tuple[str, ...]:
    with DEFAULT_CITIES_PATH.open(encoding="utf-8") as source:
        data = json.load(source)
    if not isinstance(data, dict):
        raise RuntimeError("cities.json must contain an object keyed by city")
    return tuple(sorted(data.keys(), key=str.casefold))


def search_cities(query: str, limit: int = 20) -> list[str]:
    query = query.strip()
    if not query:
        return []
    folded = query.casefold()
    starts = []
    contains = []
    for name in city_names():
        name_folded = name.casefold()
        if name_folded.startswith(folded):
            starts.append(name)
        elif folded in name_folded:
            contains.append(name)
        if len(starts) >= limit:
            break
    if len(starts) >= limit:
        return starts[:limit]
    return (starts + contains)[:limit]


def safe_download_name(path: Path) -> str:
    """Keep only ASCII-safe characters for Content-Disposition filenames."""
    name = path.name
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    return cleaned or "panchanga.pdf"


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


@app.post("/generate")
def generate():
    city = (request.form.get("city") or "").strip()
    start = (request.form.get("start") or "").strip()
    if not city:
        abort(400, description="City is required.")
    if not start:
        abort(400, description="Start month is required (YYYY-MM).")

    try:
        start_year, start_month = parse_start_month(start)
        location = load_location(city)
    except ValueError as error:
        abort(400, description=str(error))

    output_name = default_output_path(location, start_year, start_month).name
    tmp_dir = Path(tempfile.mkdtemp(prefix="panchanga-web-"))
    output_path = tmp_dir / output_name
    try:
        try:
            generated = build_pdf(location, start_year, start_month, output_path, festivals_path=DEFAULT_FESTIVALS_PATH)
        except (OSError, ValueError, RuntimeError) as error:
            abort(400, description=str(error))
        # Load into memory so the temp directory can be removed immediately.
        pdf_bytes = generated.read_bytes()
        download_name = safe_download_name(generated)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return send_file(io.BytesIO(pdf_bytes), mimetype="application/pdf", as_attachment=True, download_name=download_name,
                     max_age=0)


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
