"""Transport-neutral calendar PDF generation."""

from pathlib import Path
from tempfile import TemporaryDirectory

from generate_monthly_calendar import build_monthly_pdf, default_monthly_output_path
from generate_panchanga_calendar import (
  DEFAULT_FESTIVALS_PATH,
  build_pdf as build_one_page_pdf,
  check_reportlab,
  default_output_path as default_one_page_path,
  lunar_year_months,
  require_coordinate_selection,
  require_month_system,
  require_start_year,
  resolve_location,
)


def build_pdf(location, months, output_path, **kwargs):
  """Dispatch to the appropriate builder; mockable for tests."""
  layout = kwargs.pop("layout", "one-page")
  if layout == "monthly":
    return build_monthly_pdf(location, months, output_path, **kwargs)
  return build_one_page_pdf(location, months, output_path, **kwargs)


def generate_pdf(fields):
  """Validate shared form fields and generate the requested PDF."""
  check_reportlab()
  layout = (fields.get("layout") or "one-page").strip().casefold()
  if layout not in ("one-page", "monthly"):
    raise ValueError("Layout must be 'one-page' or 'monthly'.")
  location = resolve_location(fields.get("city"), fields.get("place"))
  start_year = require_start_year((fields.get("start") or "").strip())
  month_system = (fields.get("month") or "amanta").strip()
  require_month_system(month_system)
  coordinate_selection = require_coordinate_selection((fields.get("ayanamsa") or "").strip() or None)
  # Resolve once: the filename and the builder must print the same months.
  months = lunar_year_months(start_year, location, coordinate_selection)
  if layout == "monthly":
    filename = default_monthly_output_path(location, months, month_system=month_system,
                                           coordinate_selection=coordinate_selection).name
  else:
    filename = default_one_page_path(location, months, month_system=month_system,
                                     coordinate_selection=coordinate_selection).name
  with TemporaryDirectory(prefix="panchanga-web-") as directory:
    output_path = Path(directory) / filename
    generated = build_pdf(
      location,
      months,
      output_path,
      festivals_path=DEFAULT_FESTIVALS_PATH,
      month_system=month_system,
      coordinate_selection=coordinate_selection,
      layout=layout,
    )
    return generated.read_bytes(), filename
