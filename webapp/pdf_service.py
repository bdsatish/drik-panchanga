"""Transport-neutral calendar PDF generation."""

from pathlib import Path
from tempfile import TemporaryDirectory

from generate_panchanga_calendar import (
    DEFAULT_FESTIVALS_PATH,
    build_pdf,
    default_output_path,
    load_location,
    parse_coordinate_selection,
    parse_start_month,
)


def generate_pdf(fields):
    """Validate shared form fields and generate the requested PDF."""
    city = (fields.get("city") or "").strip()
    start = (fields.get("start") or "").strip()
    if not city:
        raise ValueError("City is required.")
    if not start:
        raise ValueError("Start month is required (YYYY-MM).")

    start_year, start_month = parse_start_month(start)
    month_system = (fields.get("month") or "amanta").strip()
    coordinate_selection = parse_coordinate_selection(
        (fields.get("ayanamsa") or "").strip() or None)
    location = load_location(city)
    filename = default_output_path(
        location, start_year, start_month,
        month_system=month_system, coordinate_selection=coordinate_selection,
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
