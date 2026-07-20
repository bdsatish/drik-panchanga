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


def plain_tithi_number(tithi):
    """Convert a plain S1..S15 or K1..K15 code to 1..30."""
    if not isinstance(tithi, str) or len(tithi) < 2:
        return None
    paksha = tithi[0]
    if paksha not in {"S", "K"}:
        return None
    try:
        paksha_tithi = int(tithi[1:])
    except ValueError:
        return None
    if not 1 <= paksha_tithi <= 15:
        return None
    return paksha_tithi if paksha == "S" else paksha_tithi + 15


def masa_codes_for(masa, allow_adhika=False):
    """Accepted masa codes for a rule, or ``None`` to accept any masa."""
    if masa is None:
        return None
    return {str(masa), f"A{masa}"} if allow_adhika else {str(masa)}


def resolve_vriddhi_dates(dates):
    """Keep the earlier day when a festival prevails at consecutive sunrises."""
    resolved = []
    previous = None
    for civil_date in sorted(dates):
        if previous is not None and civil_date == previous + timedelta(days=1):
            previous = civil_date
            continue
        resolved.append(civil_date)
        previous = civil_date
    return resolved


def select_kshaya_dates(records, tithi, *, masa=None, allow_adhika=False):
    """Later civil day when the tithi is skipped between sunrises.

    When ``masa`` is set, it is read from the later sunrise for Shukla tithis
    and from the earlier sunrise for Krishna tithis. That covers mid-masa
    kshaya and paksha-boundary cases such as Ugadi between Phalguna-K15 and
    Caitra-S2. When ``masa`` is ``None``, any masa is accepted.
    """
    target_tithi = plain_tithi_number(tithi)
    if target_tithi is None:
        return []
    masa_codes = masa_codes_for(masa, allow_adhika)
    matches = []
    ordered = sorted(records)
    for record, following in zip(ordered, ordered[1:]):
        if following[0] != record[0] + timedelta(days=1):
            continue
        start_tithi = plain_tithi_number(record[1])
        end_tithi = plain_tithi_number(following[1])
        if start_tithi is None or end_tithi is None:
            continue
        skipped = [
            (start_tithi + offset - 1) % 30 + 1
            for offset in range(1, (end_tithi - start_tithi) % 30)
        ]
        if target_tithi not in skipped:
            continue
        if masa_codes is not None:
            masa_record = following if target_tithi <= 15 else record
            if masa_record[2] not in masa_codes:
                continue
        matches.append(following[0])
    return matches


def select_tithi_dates(records, tithi, *, masa=None, allow_adhika=False):
    """Civil days for a tithi using sunrise, vriddhi, and kshaya rules.

    Vriddhi (same tithi at consecutive sunrises) keeps the former date.
    Kshaya (tithi missed entirely at sunrise) keeps the later civil date.
    """
    masa_codes = masa_codes_for(masa, allow_adhika)
    sunrise_matches = resolve_vriddhi_dates(
        [
            civil_date
            for civil_date, day_tithi, day_masa, _is_adhika in records
            if day_tithi == tithi
            and (masa_codes is None or day_masa in masa_codes)
        ]
    )
    sunrise_dates = set(sunrise_matches)
    kshaya_matches = [
        civil_date
        for civil_date in select_kshaya_dates(
            records,
            tithi,
            masa=masa,
            allow_adhika=allow_adhika,
        )
        if civil_date not in sunrise_dates
    ]
    return sorted(set(sunrise_matches) | set(kshaya_matches))


def select_plain_tithi_dates(records, masa, tithi, *, allow_adhika=False):
    """Civil days for a plain masa+tithi festival."""
    return select_tithi_dates(
        records,
        tithi,
        masa=masa,
        allow_adhika=allow_adhika,
    )


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
    """Resolve Ekadashi upavasa dates with the same sunrise/vriddhi/kshaya rules."""
    records = collect_records(months, month_data)
    selected = set()
    for tithi in ("S11", "K11"):
        selected.update(select_tithi_dates(records, tithi))
    return sorted(selected)
