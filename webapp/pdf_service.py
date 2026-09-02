"""Transport-neutral calendar PDF generation."""

from pathlib import Path
from tempfile import TemporaryDirectory

from generate_panchanga_calendar import (
  DEFAULT_FESTIVALS_PATH,
  load_location,
  require_coordinate_selection,
  require_month_system,
  require_start_month,
)

# Layout builders: form field ``layout`` ("one-page" default or "monthly").
_LAYOUT_BUILDERS = {}
_LAYOUT_FILENAME = {}


def _register_layouts():
  """Populate layout maps lazily to keep imports cheap for tests."""
  global _LAYOUT_BUILDERS, _LAYOUT_FILENAME
  if _LAYOUT_BUILDERS:
    return
  from generate_monthly_calendar import build_monthly_pdf, default_monthly_output_path
  from generate_panchanga_calendar import build_pdf as one_page_build, default_output_path
  _LAYOUT_BUILDERS = {
    "one-page": one_page_build,
    "monthly": build_monthly_pdf,
  }
  _LAYOUT_FILENAME = {
    "one-page": default_output_path,
    "monthly": default_monthly_output_path,
  }


def build_pdf(location, start_year, start_month, output_path, **kwargs):
  """Dispatch to the appropriate builder; mockable for tests."""
  _register_layouts()
  layout = kwargs.pop("layout", "one-page")
  return _LAYOUT_BUILDERS[layout](location, start_year, start_month, output_path, **kwargs)


def _default_filename(location, start_year, start_month, layout="one-page", **kwargs):
  _register_layouts()
  return _LAYOUT_FILENAME[layout](location, start_year, start_month, **kwargs)


def generate_pdf(fields):
  """Validate shared form fields and generate the requested PDF."""
  layout = (fields.get("layout") or "one-page").strip().casefold()
  _register_layouts()
  if layout not in _LAYOUT_BUILDERS:
    raise ValueError("Layout must be 'one-page' or 'monthly'.")
  city = (fields.get("city") or "").strip()
  start = (fields.get("start") or "").strip()
  location = load_location(city)
  start_year, start_month = require_start_month(start)
  month_system = (fields.get("month") or "amanta").strip()
  require_month_system(month_system)
  coordinate_selection = require_coordinate_selection((fields.get("ayanamsa") or "").strip() or None)
  filename = _default_filename(
    location,
    start_year,
    start_month,
    layout=layout,
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
      layout=layout,
    )
    return generated.read_bytes(), filename
