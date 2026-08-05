"""Transport-neutral calendar PDF generation."""

from pathlib import Path
from tempfile import TemporaryDirectory

from generate_panchanga_calendar import (
  DEFAULT_FESTIVALS_PATH,
  build_pdf,
  default_output_path,
  load_location,
  parse_start_month,
  require_coordinate_selection,
  require_month_system,
)


def generate_pdf(fields):
  """Validate shared form fields and generate the requested PDF."""
  city = (fields.get("city") or "").strip()
  start = (fields.get("start") or "").strip()
  if not city:
    raise ValueError("City is required.")
  if not start:
    raise ValueError("Start month is required (YYYY-MM).")

  parsed_start = parse_start_month(start)
  if parsed_start is None:
    raise ValueError("start month must use YYYY-MM format")
  start_year, start_month = parsed_start
  month_system = (fields.get("month") or "amanta").strip()
  require_month_system(month_system)
  coordinate_selection = require_coordinate_selection((fields.get("ayanamsa") or "").strip() or None)
  location = load_location(city)
  filename = default_output_path(
    location,
    start_year,
    start_month,
    month_system=month_system,
    coordinate_selection=coordinate_selection,
  ).name
  with TemporaryDirectory(prefix="panchanga-web-") as directory:
    output_path = Path(directory) / filename
    generated = build_pdf(
      location,
      start_year,
      start_month,
      output_path,
      festivals_path=DEFAULT_FESTIVALS_PATH,
      month_system=month_system,
      coordinate_selection=coordinate_selection,
    )
    return generated.read_bytes(), filename
