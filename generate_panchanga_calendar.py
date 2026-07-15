#!/usr/bin/env python3
"""Generate a compact one-page panchanga calendar for any listed city."""

import argparse
import calendar
import json
import re
from dataclasses import dataclass
from datetime import date as CivilDate
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

from festival_rules import (
    resolve_dharma_sindhu_vaishnava_ekadashi_dates,
    resolve_festivals,
)
import panchanga


MONTH_COUNT = 13
DEFAULT_CITIES_PATH = Path(__file__).with_name("cities.json")
RULESET_VERSION = "Dharma-sindhu DS-1.0"
LAYOUT_VERSION = "A4-1.0"


@dataclass(frozen=True)
class Location:
    name: str
    latitude: float
    longitude: float
    timezone_name: str

INK = HexColor("#172033")
MUTED = HexColor("#465466")
ACCENT = HexColor("#263F73")
GRID = HexColor("#CBD3DF")
MONTH_DIVIDER = HexColor("#AAB5C4")
ALT_ROW = HexColor("#F4F7FA")
SUNDAY_MARK = HexColor("#C94B40")
MISSING_ROW = HexColor("#ECEFF3")
ADHIKA_ROW = HexColor("#FFF0C7")
ADHIKA_INK = HexColor("#875A00")
MASA_START_ROW = HexColor("#E4F1E7")
MASA_START_INK = HexColor("#356846")
FESTIVAL_INK = HexColor("#9A3154")
EKADASHI_MARK = HexColor("#168078")

NAKSHATRA_KEY_LINES = (
    "N: 1 Asvini, 2 Bharani, 3 Krittika, 4 Rohini, 5 Mrgasira, 6 Ardra, "
    "7 Punarvasu, 8 Pusya, 9 Aslesa, 10 Magha, 11 Purvaphalguni, "
    "12 Uttaraphalguni, 13 Hasta, 14 Citra",
    "15 Svati, 16 Visakha, 17 Anuradha, 18 Jyestha, 19 Mula, 20 Purvasadha, "
    "21 Uttarasadha, 22 Sravana, 23 Dhanistha, 24 Satabhisa, "
    "25 Purvabhadra, 26 Uttarabhadra, 27 Revati",
)
YOGA_KEY_LINE = (
    "Y: 01 Viskumbha, 02 Priti, 03 Ayusman, 04 Saubhagya, 05 Sobhana, "
    "06 Atiganda, 07 Sukarma, 08 Dhrti, 09 Sula, 10 Ganda, 11 Vrddhi, "
    "12 Dhruva, 13 Vyaghata, 14 Harsana, 15 Vajra, 16 Siddhi, "
    "17 Vyatipata, 18 Variyana, 19 Parigha, 20 Siva, 21 Siddha, "
    "22 Sadhya, 23 Subha, 24 Sukla, 25 Brahma, 26 Aindra, 27 Vaidhrti"
)


def month_range(start_year, start_month, count=MONTH_COUNT):
    year, month = start_year, start_month
    for _ in range(count):
        yield year, month
        if month == 12:
            year, month = year + 1, 1
        else:
            month += 1


def parse_start_month(value):
    match = re.fullmatch(r"(\d{4})-(\d{2})", value)
    if not match:
        raise ValueError("start month must use YYYY-MM format")
    year, month = (int(part) for part in match.groups())
    if not 1 <= month <= 12:
        raise ValueError("start month must be between 01 and 12")
    return year, month


def make_location(name, latitude, longitude, timezone_name):
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (TypeError, ValueError) as error:
        raise ValueError(f"Invalid coordinates for city {name!r}") from error
    if not -90 <= latitude <= 90:
        raise ValueError(f"Latitude for city {name!r} is outside [-90, 90]")
    if not -180 <= longitude <= 180:
        raise ValueError(f"Longitude for city {name!r} is outside [-180, 180]")
    try:
        ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as error:
        raise ValueError(
            f"Unknown IANA timezone {timezone_name!r} for city {name!r}"
        ) from error
    return Location(name, latitude, longitude, timezone_name)


def location_from_mapping(name, record):
    if not isinstance(record, dict):
        raise ValueError(f"Location record for {name!r} must be an object")
    location_name = record.get("city", record.get("name", name))
    latitude = record.get("latitude", record.get("lat"))
    longitude = record.get("longitude", record.get("lon"))
    timezone_name = record.get(
        "timezone",
        record.get("timezone_name", record.get("tz")),
    )
    if latitude is None or longitude is None or timezone_name is None:
        raise ValueError(
            f"Location record for {location_name!r} needs latitude, "
            "longitude, and timezone"
        )
    return make_location(
        str(location_name),
        latitude,
        longitude,
        str(timezone_name),
    )


def load_location(city):
    path = DEFAULT_CITIES_PATH
    if not path.exists():
        raise ValueError(f"Cities file does not exist: {path}")
    with path.open(encoding="utf-8") as source:
        locations = json.load(source)
    if not isinstance(locations, dict):
        raise ValueError("cities.json must contain an object keyed by city")

    matching_names = [
        name
        for name in locations
        if name.casefold() == city.casefold()
    ]
    if not matching_names:
        import difflib

        suggestions = difflib.get_close_matches(
            city,
            list(locations),
            n=5,
            cutoff=0.6,
        )
        message = f"City {city!r} was not found in {path}"
        if suggestions:
            message += f". Close matches: {', '.join(suggestions)}"
        raise ValueError(message)
    name = matching_names[0]
    return location_from_mapping(name, locations[name])


def timezone_hours(timezone, year, month, day):
    """Return the location's UTC offset, including daylight-saving time."""
    local_noon = datetime(
        year, month, day, 12, tzinfo=timezone
    )
    return local_noon.utcoffset().total_seconds() / 3600


def tithi_code(tithi_number):
    if tithi_number <= 15:
        return f"S{tithi_number}"
    return f"K{tithi_number - 15}"


def masa_code(masa_number, is_adhika):
    return f"A{masa_number}" if is_adhika else str(masa_number)


def zero_pad_calendar_value(value):
    """Zero-pad masa and tithi numbers for fixed-width calendar display."""
    formatted = []
    for part in value.split("/"):
        if part.startswith("A"):
            formatted.append(f"A{int(part[1:]):02d}")
        elif part.startswith(("S", "K")):
            formatted.append(f"{part[0]}{int(part[1:]):02d}")
        else:
            formatted.append(f"{int(part):02d}")
    return "/".join(formatted)


def dms_to_hours(dms):
    hours, minutes, seconds = dms
    return hours + minutes / 60 + seconds / 3600


def daily_values(year, month, location):
    result = []
    timezone = ZoneInfo(location.timezone_name)
    days = calendar.monthrange(year, month)[1]
    for day in range(1, days + 1):
        date = panchanga.Date(year, month, day)
        place = panchanga.Place(
            location.latitude,
            location.longitude,
            timezone_hours(timezone, year, month, day),
        )
        jd = panchanga.gregorian_to_jd(date)
        try:
            sunrise_result = panchanga.sunrise(jd, place)
            sunrise_jd = sunrise_result[0]
            if not jd - 1 <= sunrise_jd <= jd + 2:
                raise RuntimeError("no local sunrise")
            sunset_result = panchanga.sunset(jd, place)
            sunset_jd = sunset_result[0]
            if not jd - 1 <= sunset_jd <= jd + 2:
                raise RuntimeError("no local sunset")
            tithi_result = panchanga.tithi(jd, place)
            tithi_number = tithi_result[0]
            tithi_hours_after_sunrise = (
                dms_to_hours(tithi_result[1])
                - dms_to_hours(sunrise_result[1])
            )
            nakshatra_number = panchanga.nakshatra(jd, place)[0]
            yoga_number = panchanga.yoga(jd, place)[0]
            masa_number, is_adhika = panchanga.masa(jd, place)
        except Exception as error:
            raise RuntimeError(
                f"Cannot calculate sunrise panchanga for {location.name} "
                f"on {year:04d}-{month:02d}-{day:02d}: {error}"
            ) from error
        result.append(
            (
                day,
                tithi_code(tithi_number),
                nakshatra_number,
                masa_code(masa_number, is_adhika),
                is_adhika,
                tithi_hours_after_sunrise,
                sunrise_jd - place.timezone / 24,
                sunset_jd - place.timezone / 24,
                yoga_number,
            )
        )
    return result


def mark_masa_starts(months, month_data):
    """Attach masa badges where a new masa first appears at sunrise."""
    previous_masa = None
    for year, month in months:
        marked_values = []
        for (
            day,
            tithi,
            nakshatra,
            masa,
            is_adhika,
            _,
            _,
            _,
            yoga,
        ) in month_data[(year, month)]:
            is_masa_start = masa != previous_masa
            marked_values.append(
                (
                    day,
                    tithi,
                    nakshatra,
                    yoga,
                    is_masa_start,
                    is_adhika,
                    masa if is_masa_start else None,
                )
            )
            previous_masa = masa
        month_data[(year, month)] = marked_values


def draw_centered(pdf, text, center_x, baseline_y, font, size, color=INK):
    pdf.setFont(font, size)
    pdf.setFillColor(color)
    pdf.drawCentredString(center_x, baseline_y, text)


def fitted_font_size(pdf, text, font, maximum, minimum, available_width):
    """Shrink text only when it would exceed its available width."""
    natural_width = pdf.stringWidth(text, font, maximum)
    if natural_width <= available_width:
        return maximum
    return max(minimum, maximum * available_width / natural_width)


def ensure_text_fits(pdf, text, font, size, available_width, context):
    """Fail generation rather than silently clipping an important label."""
    if pdf.stringWidth(text, font, size) > available_width + 0.01:
        raise ValueError(f"{context} is too long to fit: {text!r}")


def draw_day_column(pdf, x, top, width):
    month_header_height = 20
    column_header_height = 15
    row_height = 13.7
    header_height = month_header_height + column_header_height

    pdf.setFillColor(ACCENT)
    pdf.rect(x, top - header_height, width, header_height, stroke=0, fill=1)
    draw_centered(
        pdf,
        "DAY",
        x + width / 2,
        top - 21,
        "Helvetica-Bold",
        7.2,
        white,
    )

    rows_top = top - header_height
    for index in range(31):
        row_y = rows_top - (index + 1) * row_height
        pdf.setFillColor(ALT_ROW if index % 2 else white)
        pdf.rect(x, row_y, width, row_height, stroke=0, fill=1)
        draw_centered(
            pdf,
            str(index + 1),
            x + width / 2,
            row_y + 4.1,
            "Helvetica",
            7.4,
            INK,
        )


    bottom = rows_top - 31 * row_height
    pdf.setStrokeColor(GRID)
    pdf.setLineWidth(0.4)
    pdf.rect(x, bottom, width, top - bottom, stroke=1, fill=0)
    for index in range(32):
        y = rows_top - index * row_height
        pdf.line(x, y, x + width, y)


def draw_month(
    pdf,
    year,
    month,
    values,
    festivals_by_date,
    ekadashi_dates,
    x,
    top,
    width,
):
    month_header_height = 20
    column_header_height = 15
    row_height = 13.7

    pdf.setFillColor(ACCENT)
    pdf.rect(
        x,
        top - month_header_height,
        width,
        month_header_height,
        stroke=0,
        fill=1,
    )
    draw_centered(
        pdf,
        f"{calendar.month_abbr[month]} '{str(year)[2:]}",
        x + width / 2,
        top - 14,
        "Helvetica-Bold",
        8.0,
        white,
    )

    header_top = top - month_header_height
    pdf.setFillColor(HexColor("#E2E7EF"))
    pdf.rect(
        x,
        header_top - column_header_height,
        width,
        column_header_height,
        stroke=0,
        fill=1,
    )

    centers = (
        x + width * 0.25,
        x + width * 0.625,
        x + width * 0.875,
    )
    for label, center in zip(("T", "N", "Y"), centers):
        draw_centered(
            pdf,
            label,
            center,
            header_top - 10.5,
            "Helvetica-Bold",
            7.0,
            MUTED,
        )

    rows_top = header_top - column_header_height
    values_by_day = {
        day: (
            tithi,
            nakshatra,
            yoga,
            is_masa_start,
            is_adhika,
            masa_badge,
        )
        for (
            day,
            tithi,
            nakshatra,
            yoga,
            is_masa_start,
            is_adhika,
            masa_badge,
        ) in values
    }
    for index in range(31):
        day = index + 1
        row_y = rows_top - (index + 1) * row_height
        is_sunday = False
        if day not in values_by_day:
            pdf.setFillColor(MISSING_ROW)
        else:
            weekday = datetime(year, month, day).weekday()
            is_sunday = weekday == calendar.SUNDAY
            if index % 2:
                pdf.setFillColor(ALT_ROW)
            else:
                pdf.setFillColor(white)
        pdf.rect(x, row_y, width, row_height, stroke=0, fill=1)

        if day not in values_by_day:
            continue

        (
            tithi,
            nakshatra,
            yoga,
            is_masa_start,
            is_adhika,
            masa_badge,
        ) = values_by_day[day]
        tithi_display = zero_pad_calendar_value(tithi)
        if is_masa_start:
            pdf.setFillColor(ADHIKA_ROW if is_adhika else MASA_START_ROW)
            pdf.rect(
                x,
                row_y,
                width * 0.5,
                row_height,
                stroke=0,
                fill=1,
            )
            pdf.setFillColor(ADHIKA_INK if is_adhika else MASA_START_INK)
            pdf.setFont("Helvetica-Bold", 5.2)
            pdf.drawString(
                x + 2.4,
                row_y + 8.2,
                masa_badge.removeprefix("A"),
            )
        if is_sunday:
            pdf.setFillColor(SUNDAY_MARK)
            pdf.rect(
                x + width - 1.6,
                row_y,
                1.6,
                row_height,
                stroke=0,
                fill=1,
            )
        civil_date = CivilDate(year, month, day)
        if civil_date in ekadashi_dates:
            pdf.setFillColor(EKADASHI_MARK)
            pdf.rect(
                x + width * 0.08,
                row_y + 0.6,
                width * 0.34,
                1.2,
                stroke=0,
                fill=1,
            )
        festival_numbers = festivals_by_date.get(
            civil_date,
            (),
        )
        baseline = row_y + (3.0 if festival_numbers else 4.1)
        draw_centered(
            pdf,
            tithi_display,
            centers[0],
            baseline,
            "Helvetica-Bold",
            7.4,
            (
                ADHIKA_INK
                if is_masa_start and is_adhika
                else MASA_START_INK if is_masa_start else ACCENT
            ),
        )
        draw_centered(
            pdf, f"{nakshatra:02d}", centers[1], baseline, "Helvetica", 7.3, INK
        )
        draw_centered(
            pdf, f"{yoga:02d}", centers[2], baseline, "Helvetica", 7.3, INK
        )
        if festival_numbers:
            pdf.setFillColor(FESTIVAL_INK)
            marker_size = 5.0 if len(festival_numbers) <= 2 else 4.0
            marker_spacing = 4.8 if len(festival_numbers) <= 2 else 3.5
            marker_top = row_y + (8.8 if len(festival_numbers) <= 2 else 9.5)
            pdf.setFont("Helvetica-Bold", marker_size)
            for marker_index, number in enumerate(festival_numbers):
                pdf.drawRightString(
                    x + width * 0.47,
                    marker_top - marker_index * marker_spacing,
                    str(number),
                )

    bottom = rows_top - 31 * row_height
    pdf.setStrokeColor(GRID)
    pdf.setLineWidth(0.4)
    pdf.rect(x, bottom, width, top - bottom, stroke=1, fill=0)
    pdf.line(x + width * 0.5, bottom, x + width * 0.5, header_top)
    pdf.line(x + width * 0.75, bottom, x + width * 0.75, header_top)
    for index in range(32):
        y = rows_top - index * row_height
        pdf.line(x, y, x + width, y)
    pdf.setStrokeColor(MONTH_DIVIDER)
    pdf.setLineWidth(0.9)
    pdf.line(x, bottom, x, top)


def month_span_label(months):
    start_year, start_month = months[0]
    end_year, end_month = months[-1]
    return (
        f"{calendar.month_name[start_month]} {start_year} - "
        f"{calendar.month_name[end_month]} {end_year}"
    )


def coordinate_label(value, positive, negative):
    direction = positive if value >= 0 else negative
    return f"{abs(value):.5f} {direction}"


def draw_page_header(pdf, location, months):
    page_width, page_height = landscape(A4)
    title = f"{location.name} Panchanga: {month_span_label(months)}"
    pdf.setFillColor(INK)
    title_size = fitted_font_size(
        pdf,
        title,
        "Helvetica-Bold",
        11,
        8,
        page_width - 36,
    )
    ensure_text_fits(
        pdf,
        title,
        "Helvetica-Bold",
        title_size,
        page_width - 36,
        "page title",
    )
    pdf.setFont("Helvetica-Bold", title_size)
    pdf.drawString(
        18,
        page_height - 20,
        title,
    )
    pdf.setFillColor(MUTED)
    pdf.setFont("Helvetica", 7.5)
    pdf.drawString(
        18,
        page_height - 31,
        "At local sunrise | True Citra ayanamsa | Equal nakshatras | Amanta masa | "
        f"{coordinate_label(location.latitude, 'N', 'S')}, "
        f"{coordinate_label(location.longitude, 'E', 'W')} | "
        f"{location.timezone_name} civil time",
    )
    pdf.setFont("Helvetica", 4.7)
    pdf.drawRightString(
        page_width - 18,
        page_height - 19,
        f"Ruleset: {RULESET_VERSION} | Layout: {LAYOUT_VERSION}",
    )


def draw_page_footer(pdf, festival_entries):
    pdf.setFillColor(FESTIVAL_INK)

    columns = 6
    rows = 5
    column_width = (landscape(A4)[0] - 36) / columns
    for index, (number, festival_date, name) in enumerate(festival_entries):
        column = index // rows
        row = index % rows
        entry = f"{number:02d}  {festival_date}  {name}"
        entry_size = fitted_font_size(
            pdf,
            entry,
            "Helvetica",
            7.5,
            5.5,
            column_width - 4,
        )
        ensure_text_fits(
            pdf,
            entry,
            "Helvetica",
            entry_size,
            column_width - 4,
            f"festival entry {number}",
        )
        pdf.setFont("Helvetica", entry_size)
        pdf.drawString(
            18 + column * column_width,
            88 - row * 8,
            entry,
        )

    pdf.setFillColor(MUTED)
    pdf.setFont("Helvetica", 5.4)
    pdf.drawString(
        18,
        44,
        "T: S01-S15 = Sukla; K01-K15 = Krsna. N = nakshatra; Y = yoga. "
        "Tiny red numbers refer to the festival key. Sundays have a red right "
        "edge; Dharma-sindhu Vaishnava Ekadashi upavasa has a teal T-cell "
        "underline.",
    )
    pdf.setFont("Helvetica", 5.3)
    pdf.drawString(
        18,
        36,
        "Masa: a small upper-left badge marks its first visible tithi; "
        "gold fill denotes adhika. 1 Caitra, 2 Vaisakha, 3 Jyestha, "
        "4 Asadha, 5 Sravana, 6 Bhadrapada, 7 Asvina, 8 Kartika, "
        "9 Margasirsa, 10 Pusya, 11 Magha, 12 Phalguna.",
    )
    pdf.drawString(
        18,
        28,
        f"{NAKSHATRA_KEY_LINES[0]}, {NAKSHATRA_KEY_LINES[1]}",
    )
    pdf.drawString(18, 20, YOGA_KEY_LINE)


def build_pdf(location, start_year, start_month, output_path):
    panchanga.set_chosen_ayanamsa("citra")
    months = list(month_range(start_year, start_month))
    if start_month == 1:
        context_start = (start_year - 1, 12)
    else:
        context_start = (start_year, start_month - 1)
    context_months = list(
        month_range(*context_start, count=MONTH_COUNT + 2)
    )
    context_data = {
        (year, month): daily_values(year, month, location)
        for year, month in context_months
    }
    month_data = {
        (year, month): context_data[(year, month)]
        for year, month in months
    }
    festivals_by_date, festival_entries = resolve_festivals(
        months,
        month_data,
    )
    range_start = CivilDate(start_year, start_month, 1)
    end_year, end_month = months[-1]
    range_end = CivilDate(
        end_year,
        end_month,
        calendar.monthrange(end_year, end_month)[1],
    )
    ekadashi_dates = {
        value
        for value in resolve_dharma_sindhu_vaishnava_ekadashi_dates(
            context_months,
            context_data,
        )
        if range_start <= value <= range_end
    }
    mark_masa_starts(months, month_data)

    page_width, page_height = landscape(A4)
    output_path = Path(output_path)
    pdf = canvas.Canvas(str(output_path), pagesize=(page_width, page_height))
    pdf.setTitle(
        f"{location.name} Panchanga {month_span_label(months)}"
    )
    pdf.setAuthor("drik-panchanga")
    pdf.setKeywords(
        f"ruleset={RULESET_VERSION}; layout={LAYOUT_VERSION}; "
        "ayanamsa=True Citra"
    )
    pdf.setSubject(
        f"Daily tithi, True Citra nakshatra, yoga, and amanta masa at "
        f"{location.name} sunrise"
    )

    draw_page_header(pdf, location, months)

    margin = 18
    day_column_width = 24
    usable_width = page_width - 2 * margin
    month_width = (usable_width - day_column_width) / len(months)
    top = page_height - 37

    draw_day_column(pdf, margin, top, day_column_width)
    for index, (year, month) in enumerate(months):
        x = margin + day_column_width + index * month_width
        draw_month(
            pdf,
            year,
            month,
            month_data[(year, month)],
            festivals_by_date,
            ekadashi_dates,
            x,
            top,
            month_width,
        )

    draw_page_footer(pdf, festival_entries)
    pdf.showPage()

    pdf.save()
    return output_path


def default_output_path(location, start_year, start_month):
    months = list(month_range(start_year, start_month))
    end_year, end_month = months[-1]
    city_slug = re.sub(
        r"[^a-z0-9]+",
        "-",
        location.name.casefold(),
    ).strip("-") or "location"
    return Path(
        f"{city_slug}_panchanga_"
        f"{start_year:04d}-{start_month:02d}_to_"
        f"{end_year:04d}-{end_month:02d}.pdf"
    )


def argument_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Generate a one-page A4 panchanga for 13 consecutive months."
        )
    )
    parser.add_argument(
        "--city",
        required=True,
        help=f"city name as listed in {DEFAULT_CITIES_PATH.name}",
    )
    parser.add_argument(
        "--start",
        required=True,
        metavar="YYYY-MM",
        help="first of the 13 consecutive calendar months",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="output PDF path (default: generated from city and range)",
    )
    return parser


def main(argv=None):
    parser = argument_parser()
    arguments = parser.parse_args(argv)
    try:
        start_year, start_month = parse_start_month(arguments.start)
        location = load_location(arguments.city)
        output_path = arguments.output or default_output_path(
            location,
            start_year,
            start_month,
        )
        generated = build_pdf(
            location,
            start_year,
            start_month,
            output_path,
        )
    except (OSError, ValueError, RuntimeError) as error:
        parser.error(str(error))
    print(generated.resolve())


if __name__ == "__main__":
    main()
