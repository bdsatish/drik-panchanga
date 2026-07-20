"""Festival API consumed by the PDF calendar generator.

The previous multi-policy implementation lives under ``experimental/`` for
reference. This module is a clean-slate rebuild.
"""

import calendar
from datetime import date as CivilDate
from datetime import timedelta


# Plain tithi festivals: (number, name, masa, tithi).
# Civil day whose sunrise owns masa + tithi (non-adhika).
FESTIVAL_RULES = (
    (1, "Ugadi", 1, "S1"),
    (2, "Rama Navami", 1, "S9"),
    (3, "Akshaya Tritiya", 2, "S3"),
    (4, "Vasavi Jayanti", 2, "S10"),
    (5, "Narasimha Jayanti", 2, "S14"),
    (6, "Guru Purnima", 4, "S15"),
    (7, "Naga Panchami", 5, "S5"),
    (8, "Yajur Upakarma", 5, "S15"),
    (9, "Janmashtami", 5, "K8"),
    (10, "Swarna Gowri Vrata", 6, "S3"),
    (11, "Ganesha Chaturthi", 6, "S4"),
    (12, "Mahalaya Amavasya", 6, "K15"),
    (13, "Durga Ashtami", 7, "S8"),
    (14, "Mahanavami", 7, "S9"),
    (15, "Vijayadashami", 7, "S10"),
    (16, "Dhana Trayodashi", 7, "K13"),
    (17, "Naraka Chaturdashi", 7, "K14"),
    (18, "Deepavali", 7, "K15"),
    (19, "Bali Padyami", 8, "S1"),
    (20, "Vasavi Atmarpana", 11, "S2"),
    (21, "Vasanta Panchami", 11, "S5"),
    (22, "Ratha Saptami", 11, "S7"),
    (23, "VSN Jayanti", 11, "S11"),
    (24, "Maha Shivaratri", 11, "K14"),
    (25, "Kama Dahana (Holi)", 12, "S15"),
)


def collect_records(months, month_data):
    """Flatten daily panchanga rows into civil-date records.

    Each source row from ``generate_panchanga_calendar.daily_values`` is:
    day, tithi, nakshatra, masa, is_adhika, tithi_hours_after_sunrise,
    sunrise_jd, sunset_jd, yoga, moonrise_jd.

    Festival records keep only the sunrise identity fields:
    ``(civil_date, tithi, masa, is_adhika)``.
    """
    records = []
    for year, month in months:
        for (
            day,
            tithi,
            _nakshatra,
            masa,
            is_adhika,
            _tithi_hours_after_sunrise,
            _sunrise_jd,
            _sunset_jd,
            _yoga,
            _moonrise_jd,
        ) in month_data[(year, month)]:
            records.append(
                (
                    CivilDate(year, month, day),
                    tithi,
                    masa,
                    is_adhika,
                )
            )
    return records


def format_festival_dates(dates):
    dates = sorted(dates)
    if not dates:
        return "None"
    if (
        len(dates) > 1
        and len({(value.year, value.month) for value in dates}) == 1
        and all(
            right == left + timedelta(days=1)
            for left, right in zip(dates, dates[1:])
        )
    ):
        return (
            f"{calendar.month_abbr[dates[0].month]} "
            f"{dates[0].day:02d}-{dates[-1].day:02d}"
        )
    return ",".join(
        f"{calendar.month_abbr[value.month]} {value.day:02d}"
        for value in dates
    )


def select_plain_tithi_dates(records, masa, tithi, *, allow_adhika=False):
    """Civil days whose sunrise tithi matches the rule masa.

    By default only non-adhika months match. When ``allow_adhika`` is true
    (Ugadi), both shuddha and adhika forms of the masa are accepted.
    """
    masa_codes = {str(masa), f"A{masa}"} if allow_adhika else {str(masa)}
    return [
        civil_date
        for civil_date, day_tithi, day_masa, _is_adhika in records
        if day_tithi == tithi and day_masa in masa_codes
    ]


def resolve_festivals(
    months,
    month_data,
    *,
    context_months=None,
    context_data=None,
    geopos=None,
):
    """Resolve plain tithi festivals against sunrise masa and tithi."""
    del geopos  # reserved for later astronomy-dependent rules
    if (context_months is None) != (context_data is None):
        raise ValueError("context_months and context_data must be supplied together")

    target_records = collect_records(months, month_data)
    target_dates = {record[0] for record in target_records}
    if context_months is not None:
        records = collect_records(context_months, context_data)
    else:
        records = target_records

    numbers_by_date = {}
    entries = []
    for number, name, masa, tithi in FESTIVAL_RULES:
        matches = [
            civil_date
            for civil_date in select_plain_tithi_dates(
                records,
                masa,
                tithi,
                allow_adhika=(number == 1),  # Ugadi
            )
            if civil_date in target_dates
        ]
        if not matches:
            raise RuntimeError(f"No calendar date found for {name}")
        for civil_date in matches:
            numbers_by_date.setdefault(civil_date, []).append(number)
        entries.append((number, format_festival_dates(matches), name))
    return numbers_by_date, entries


def resolve_ekadashi_dates(months, month_data):
    """Return no Ekadashi dates until the clean-slate algorithm is implemented."""
    return []
