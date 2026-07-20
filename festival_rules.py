"""Festival API consumed by the PDF calendar generator.

The previous multi-policy implementation lives under ``experimental/`` for
reference. This module is a clean-slate rebuild.
"""

import calendar
from datetime import date as CivilDate
from datetime import timedelta

import panchanga


# Tithi festivals: (number, name, masa, tithi).
TITHI_FESTIVAL_RULES = (
    (1, "Ugadi", 1, "S1"),
    (2, "Rama Navami", 1, "S9"),
    (3, "Akshaya Tritiya", 2, "S3"),
    (4, "Vasavi Jayanti", 2, "S10"),
    (5, "Narasimha Jayanti", 2, "S14"),
    (6, "Guru Purnima", 4, "S15"),
    (7, "Naga Panchami", 5, "S5"),
    (10, "Yajur Upakarma", 5, "S15"),
    (11, "Janmashtami", 5, "K8"),
    (12, "Swarna Gowri Vrata", 6, "S3"),
    (13, "Ganesha Chaturthi", 6, "S4"),
    (14, "Mahalaya Amavasya", 6, "K15"),
    (15, "Durga Ashtami", 7, "S8"),
    (16, "Ayudha Puja", 7, "S9"),
    (17, "Vijayadashami", 7, "S10"),
    (18, "Dhana Trayodashi", 7, "K13"),
    (19, "Naraka Chaturdashi", 7, "K14"),
    (20, "Deepavali", 7, "K15"),
    (21, "Bali Padyami", 8, "S1"),
    (24, "Vasavi Atmarpana", 11, "S2"),
    (25, "Vasanta Panchami", 11, "S5"),
    (26, "Ratha Saptami", 11, "S7"),
    (27, "VSN Jayanti", 11, "S11"),
    (28, "Maha Shivaratri", 11, "K14"),
    (29, "Kama Dahana (Holi)", 12, "S15"),
)

# Non-tithi festivals: (number, name). Selectors dispatch on name/number.
NON_TITHI_FESTIVAL_RULES = (
    (8, "Varamahalakshmi Vrata"),
    (9, "Rig Upakarma"),
    (22, "Vaikuntha Ekadashi"),
    (23, "Makara Sankranti"),
)


def collect_records(months, month_data):
    """Flatten daily panchanga rows into civil-date records.

    Each source row from ``generate_panchanga_calendar.daily_values`` is:
    day, tithi, nakshatra, yoga, masa, is_adhika, sunrise_jd.

    Festival records keep:
    ``(civil_date, tithi, nakshatra, masa, is_adhika, sunrise_jd)``.
    """
    records = []
    for year, month in months:
        for (
            day,
            tithi,
            nakshatra,
            _yoga,
            masa,
            is_adhika,
            sunrise_jd,
        ) in month_data[(year, month)]:
            records.append(
                (
                    CivilDate(year, month, day),
                    tithi,
                    nakshatra,
                    masa,
                    is_adhika,
                    sunrise_jd,
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
            if masa_record[3] not in masa_codes:
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
            for civil_date, day_tithi, _nakshatra, day_masa, _is_adhika, _sunrise_jd in records
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
    """Civil days for a plain masa+tithi festival.

    When ``allow_adhika`` is true (Ugadi), adhika and shuddha masas both
    match, but if any adhika occurrence exists only the adhika dates are
    kept — matching the generic-udaya policy.
    """
    matches = select_tithi_dates(
        records,
        tithi,
        masa=masa,
        allow_adhika=allow_adhika,
    )
    if not allow_adhika or not matches:
        return matches
    records_by_date = {record[0]: record for record in records}
    adhika_matches = [
        civil_date
        for civil_date in matches
        if records_by_date[civil_date][4]
        or str(records_by_date[civil_date][3]).startswith("A")
    ]
    return adhika_matches if adhika_matches else matches


def select_varamahalakshmi_dates(records):
    """Friday strictly before non-adhika Sravana Purnima (S15).

    Uses the same Sravana-S15 sunrise/vriddhi/kshaya anchor as tithi
    rules. If that Purnima falls on Friday, the previous week's Friday is kept.
    """
    selected = []
    for purnima_date in select_plain_tithi_dates(records, 5, "S15"):
        vrata_date = purnima_date - timedelta(days=1)
        while vrata_date.weekday() != calendar.FRIDAY:
            vrata_date -= timedelta(days=1)
        selected.append(vrata_date)
    return selected


def select_rig_upakarma_dates(records):
    """Nija Sravana day whose sunrise nakshatra is Sravana (22).

    Consecutive sunrise matches keep the former date (vriddhi).
    """
    SRAVANA_NAKSHATRA = 22
    matches = [
        civil_date
        for civil_date, _tithi, nakshatra, masa, is_adhika, _sunrise_jd in records
        if masa == "5" and not is_adhika and nakshatra == SRAVANA_NAKSHATRA
    ]
    return resolve_vriddhi_dates(matches)


def select_vaikuntha_ekadashi_dates(records):
    """Margasira or Pausha Shukla Ekadashi while the Sun is in Dhanur.

    Candidates are ordinary S11 dates in lunar masas 9 and 10 (with the same
    sunrise/vriddhi/kshaya rules). ``panchanga.raasi`` at local sunrise must
    be 9 (Dhanur). Returns an empty list when no such sunrise exists in the
    supplied records (acceptable; the PDF prints ``None``).
    """
    candidates = set(select_plain_tithi_dates(records, 9, "S11"))
    candidates.update(select_plain_tithi_dates(records, 10, "S11"))
    records_by_date = {record[0]: record for record in records}
    selected = []
    for civil_date in sorted(candidates):
        record = records_by_date.get(civil_date)
        if record is None:
            continue
        sunrise_jd = record[5]
        if panchanga.raasi(sunrise_jd) == 9:
            selected.append(civil_date)
    return selected


def select_makara_sankranti_dates(records):
    """First civil sunrise at which the Sun is in Makara (raasi 10).

    Each transition into Makara yields one date (the first sunrise with
    ``panchanga.raasi(sunrise_jd) == 10`` after a non-Makara sunrise).
    """
    MAKARA_RAASI = 10
    selected = []
    previous_raasi = None
    for civil_date, _tithi, _nakshatra, _masa, _is_adhika, sunrise_jd in sorted(
        records
    ):
        raasi = panchanga.raasi(sunrise_jd)
        if raasi == MAKARA_RAASI and previous_raasi != MAKARA_RAASI:
            if previous_raasi is not None:
                selected.append(civil_date)
        previous_raasi = raasi
    return selected


def select_non_tithi_dates(records, number, name):
    """Dispatch a non-tithi festival to its selector."""
    if name == "Varamahalakshmi Vrata" or number == 8:
        return select_varamahalakshmi_dates(records)
    if name == "Rig Upakarma" or number == 9:
        return select_rig_upakarma_dates(records)
    if name == "Vaikuntha Ekadashi" or number == 22:
        return select_vaikuntha_ekadashi_dates(records)
    if name == "Makara Sankranti" or number == 23:
        return select_makara_sankranti_dates(records)
    raise ValueError(f"No selector for non-tithi festival {number} {name!r}")


def resolve_festivals(
    months,
    month_data,
    *,
    context_months=None,
    context_data=None,
):
    """Resolve tithi and non-tithi festivals for the PDF calendar."""
    if (context_months is None) != (context_data is None):
        raise ValueError("context_months and context_data must be supplied together")

    target_records = collect_records(months, month_data)
    target_dates = {record[0] for record in target_records}
    if context_months is not None:
        records = collect_records(context_months, context_data)
    else:
        records = target_records

    dates_by_number = {}
    names_by_number = {}

    for number, name, masa, tithi in TITHI_FESTIVAL_RULES:
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
        dates_by_number[number] = matches
        names_by_number[number] = name

    VAIKUNTHA_EKADASI = 22 # index in NON_TITHI_FESTIVAL_RULES
    for number, name in NON_TITHI_FESTIVAL_RULES:
        matches = [
            civil_date
            for civil_date in select_non_tithi_dates(records, number, name)
            if civil_date in target_dates
        ]
        # Vaikuntha Ekadashi may be absent when no Margasira/Pausha S11 falls
        # while the Sun is in Dhanur; E.g. yr 2086
        if not matches and number != VAIKUNTHA_EKADASI:
            raise RuntimeError(f"No calendar date found for {name}")
        dates_by_number[number] = matches
        names_by_number[number] = name

    numbers_by_date = {}
    entries = []
    for number in sorted(names_by_number):
        dates = dates_by_number[number]
        for civil_date in dates:
            numbers_by_date.setdefault(civil_date, []).append(number)
        entries.append(
            (number, format_festival_dates(dates), names_by_number[number])
        )
    return numbers_by_date, entries


def resolve_ekadashi_dates(months, month_data):
    """Resolve Ekadashi upavasa dates with the same sunrise/vriddhi/kshaya rules."""
    records = collect_records(months, month_data)
    selected = set()
    for tithi in ("S11", "K11"):
        selected.update(select_tithi_dates(records, tithi))
    return sorted(selected)
