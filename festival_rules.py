"""Festival API consumed by the PDF calendar generator.

The previous multi-policy implementation lives under ``experimental/`` for
reference. This module is a clean-slate rebuild.
"""

import calendar
import configparser
from datetime import date as CivilDate
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import panchanga

SECONDS_PER_DAY = 24 * 60 * 60
JULIAN_DAY_AT_UNIX_EPOCH = 2440587.5


def julian_day_from_datetime(value):
    """Convert a timezone-aware ``datetime`` to a UT Julian day."""
    return value.timestamp() / SECONDS_PER_DAY + JULIAN_DAY_AT_UNIX_EPOCH


def jd_to_local_datetime(jd, timezone_name):
    """Convert a UT Julian day to local ``datetime`` in ``timezone_name``."""
    utc = datetime.fromtimestamp((jd - JULIAN_DAY_AT_UNIX_EPOCH) * SECONDS_PER_DAY, tz=timezone.utc)
    return utc.astimezone(ZoneInfo(timezone_name))


def jd_to_local_civil_date(jd, timezone_name):
    """Convert a UT Julian day to the civil date in ``timezone_name``."""
    return jd_to_local_datetime(jd, timezone_name).date()


# Tithi festivals: (number, name, masa, tithi).
TITHI_FESTIVAL_RULES = (
    (1, "Ugadi", 1, "S1"),
    (2, "Rama Navami", 1, "S9"),
    (3, "Akshaya Tritiya", 2, "S3"),
    (4, "Vasavi Jayanti", 2, "S10"),
    (5, "Narasimha Jayanti", 2, "S14"),
    (6, "Guru Purnima", 4, "S15"),
    (7, "Naga Panchami", 5, "S5"),
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
    (10, "Yajur Upakarma"),
    (22, "Vaikuntha Ekadashi"),
    (23, "Makara Sankranti"),
)

# Festival record: (civil_date, tithi, nakshatra, masa, is_adhika, sunrise_jd).
# Prefer unpacking at call sites; use these only for single-field peeks.
CIVIL_DATE, TITHI, NAKSHATRA, MASA, IS_ADHIKA, SUNRISE_JD = range(6)

_TRUTHY = frozenset({"yes", "true", "1", "on"})
_FALSY = frozenset({"no", "false", "0", "off"})


def all_festival_rules():
    """Catalog entries as ``(number, name)`` sorted by festival number."""
    rules = [(number, name) for number, name, _masa, _tithi in TITHI_FESTIVAL_RULES]
    rules.extend(NON_TITHI_FESTIVAL_RULES)
    return tuple(sorted(rules, key=lambda item: item[0]))


def all_festival_names():
    """Catalog festival names in ascending number order."""
    return tuple(name for _number, name in all_festival_rules())


def _parse_bool(raw, *, key):
    value = raw.strip().casefold()
    if value in _TRUTHY:
        return True
    if value in _FALSY:
        return False
    raise ValueError(f"Invalid value for festival {key!r}: {raw!r} "
                     "(use yes/no, true/false, 1/0, or on/off)")


def load_festival_selection(path):
    """Return the frozenset of enabled festival names from an INI cfg.

    The ``[festivals]`` section must list every catalog name exactly once.
    """
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    seen_keys = []
    in_festivals = False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith(";"):
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            in_festivals = stripped[1:-1].strip().casefold() == "festivals"
            continue
        if not in_festivals or "=" not in stripped:
            continue
        key = stripped.split("=", 1)[0].strip()
        seen_keys.append(key)

    duplicates = sorted({key for key in seen_keys if seen_keys.count(key) > 1})
    if duplicates:
        raise ValueError(f"Duplicate festival entries in {path}: {', '.join(duplicates)}")

    parser = configparser.ConfigParser()
    parser.optionxform = str  # preserve festival name case
    parser.read_string(text)
    if not parser.has_section("festivals"):
        raise ValueError(f"{path} must contain a [festivals] section")

    configured = dict(parser.items("festivals"))
    catalog = all_festival_names()
    catalog_set = set(catalog)
    configured_names = set(configured)

    unknown = sorted(configured_names - catalog_set)
    if unknown:
        raise ValueError(f"Unknown festival names in {path}: {', '.join(unknown)}")
    missing = [name for name in catalog if name not in configured_names]
    if missing:
        raise ValueError(f"Missing festival names in {path}: {', '.join(missing)}")

    enabled = frozenset(name for name, raw in configured.items() if _parse_bool(raw, key=name))
    return enabled


def collect_records(months, month_data):
    """Flatten daily panchanga rows into civil-date records.

    Each source row from ``generate_panchanga_calendar.daily_values`` is:
    day, tithi, nakshatra, yoga, masa, is_adhika, sunrise_jd.

    Festival records keep:
    ``(civil_date, tithi, nakshatra, masa, is_adhika, sunrise_jd)``.
    """
    records = []
    for year, month in months:
        for day, tithi, nakshatra, _yoga, masa, is_adhika, sunrise_jd in month_data[(year, month)]:
            records.append((
                CivilDate(year, month, day),
                tithi,
                nakshatra,
                masa,
                is_adhika,
                sunrise_jd,
            ))
    return records


def format_festival_dates(dates):
    dates = sorted(dates)
    if not dates:
        return "None"
    if (len(dates) > 1 and len({(value.year, value.month)
                                for value in dates}) == 1 and all(right == left + timedelta(days=1)
                                                                  for left, right in zip(dates, dates[1:]))):
        return (f"{calendar.month_abbr[dates[0].month]} "
                f"{dates[0].day:02d}-{dates[-1].day:02d}")
    return ",".join(f"{calendar.month_abbr[value.month]} {value.day:02d}" for value in dates)


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
        civil_date, day_tithi, _nak, day_masa, _adhika, _jd = record
        next_date, next_tithi, _nak, next_masa, _adhika, _jd = following
        if next_date != civil_date + timedelta(days=1):
            continue
        start_tithi = plain_tithi_number(day_tithi)
        end_tithi = plain_tithi_number(next_tithi)
        if start_tithi is None or end_tithi is None:
            continue
        skipped = [(start_tithi + offset - 1) % 30 + 1 for offset in range(1, (end_tithi - start_tithi) % 30)]
        if target_tithi not in skipped:
            continue
        if masa_codes is not None:
            check_masa = next_masa if target_tithi <= 15 else day_masa
            if check_masa not in masa_codes:
                continue
        matches.append(next_date)
    return matches


def select_tithi_dates(records, tithi, *, masa=None, allow_adhika=False):
    """Civil days for a tithi using sunrise, vriddhi, and kshaya rules.

    Vriddhi (same tithi at consecutive sunrises) keeps the former date.
    Kshaya (tithi missed entirely at sunrise) keeps the later civil date.
    """
    masa_codes = masa_codes_for(masa, allow_adhika)
    sunrise_matches = resolve_vriddhi_dates([
        civil_date for civil_date, day_tithi, _nakshatra, day_masa, _is_adhika, _sunrise_jd in records
        if day_tithi == tithi and (masa_codes is None or day_masa in masa_codes)
    ])
    sunrise_dates = set(sunrise_matches)
    kshaya_matches = [
        civil_date for civil_date in select_kshaya_dates(records, tithi, masa=masa, allow_adhika=allow_adhika)
        if civil_date not in sunrise_dates
    ]
    return sorted(set(sunrise_matches) | set(kshaya_matches))


def select_plain_tithi_dates(records, masa, tithi, *, allow_adhika=False):
    """Civil days for a plain masa+tithi festival.

    When ``allow_adhika`` is true (Ugadi), adhika and shuddha masas both
    match, but if any adhika occurrence exists only the adhika dates are
    kept — matching the generic-udaya policy.
    """
    matches = select_tithi_dates(records, tithi, masa=masa, allow_adhika=allow_adhika)
    if not allow_adhika or not matches:
        return matches
    records_by_date = {record[CIVIL_DATE]: record for record in records}
    adhika_matches = [
        civil_date for civil_date in matches
        if (records_by_date[civil_date][IS_ADHIKA] or str(records_by_date[civil_date][MASA]).startswith("A"))
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


def _eclipse_phase(flags):
    """Return Partial/Total/Annular, or None if not locally usable.

    ``*_eclipse_when_loc`` already searches for events observable at the
    place. Require ``ECL_VISIBLE`` but not ``ECL_MAX_VISIBLE`` (maximum may
    fall at rise/set). Purely penumbral lunar eclipses are omitted.
    """
    if not (flags & panchanga.swe.ECL_VISIBLE):
        return None
    if flags & panchanga.swe.ECL_TOTAL:
        return "Total"
    if flags & (panchanga.swe.ECL_ANNULAR | panchanga.swe.ECL_ANNULAR_TOTAL):
        return "Annular"
    if flags & panchanga.swe.ECL_PARTIAL:
        return "Partial"
    return None


def find_local_eclipses(start_jd, end_jd, geopos):
    """Locally visible partial/total/annular eclipses with maximum in ``[start_jd, end_jd)``.

    Returns a sorted list of ``(kind, phase, maximum_jd)`` where ``kind`` is
    ``\"Lunar\"`` or ``\"Solar\"`` and ``phase`` is Partial, Total, or Annular.
    Purely penumbral lunar eclipses are omitted. Membership uses the maximum
    only; contact intervals are not consulted.
    """
    if end_jd <= start_jd:
        return []

    searches = (
        ("Lunar", panchanga.swe.lun_eclipse_when_loc),
        ("Solar", panchanga.swe.sol_eclipse_when_loc),
    )
    found = []
    for kind, finder in searches:
        search_jd = start_jd - 1.0
        while search_jd < end_jd + 2.0:
            try:
                flags, times, _ = finder(search_jd, geopos)
            except Exception:
                break
            maximum = times[0]
            if not maximum or maximum <= search_jd:
                break
            phase = _eclipse_phase(flags)
            if phase is not None and start_jd <= maximum < end_jd:
                found.append((kind, phase, maximum))
            # Advance by a full day. A tiny epsilon can make swe return the same
            # eclipse again (e.g. a skipped penumbral), which would stall the loop.
            search_jd = maximum + 1.0

    found.sort(key=lambda item: item[2])
    return found


def civil_day_has_eclipse(civil_date, geopos, timezone_name):
    """True when a visible non-penumbral lunar eclipse peaks locally on date."""
    if geopos is None:
        return False
    timezone_info = ZoneInfo(timezone_name)
    day_start = datetime(civil_date.year, civil_date.month, civil_date.day, tzinfo=timezone_info)
    day_end = day_start + timedelta(days=1)
    start_jd = julian_day_from_datetime(day_start)
    end_jd = julian_day_from_datetime(day_end)
    return any(kind == "Lunar" for kind, _phase, _maximum_jd in find_local_eclipses(start_jd, end_jd, geopos))


def postpone_upakarma_if_eclipse(primary, fallback, geopos, timezone_name):
    """Use fallback when a visible lunar eclipse peaks on a primary date."""
    if not primary:
        return list(fallback)
    if geopos is not None and timezone_name is None:
        raise ValueError("Upakarma eclipse handling requires a timezone name")
    if geopos is not None and any(civil_day_has_eclipse(civil_date, geopos, timezone_name) for civil_date in primary):
        return list(fallback) if fallback else list(primary)
    return list(primary)


def select_yajur_upakarma_dates(records, geopos=None, timezone_name=None):
    """Nija Sravana Purnima (S15), postponed to Bhadrapada S15 on eclipse.

    Uses the ordinary sunrise/vriddhi/kshaya S15 selection in each masa. A
    locally visible non-penumbral lunar eclipse whose maximum falls on the
    selected local civil date triggers the fallback.
    """
    primary = select_plain_tithi_dates(records, 5, "S15")
    fallback = select_plain_tithi_dates(records, 6, "S15")
    return postpone_upakarma_if_eclipse(primary, fallback, geopos, timezone_name)


def select_rig_upakarma_dates(records, geopos=None, timezone_name=None):
    """Nija day whose sunrise nakshatra is Sravana (22).

    Prefer nija Sravana masa. When that nakshatra is kshaya at sunrise
    (no nija-Sravana match), or when the Sravana-masa day has a local
    eclipse whose maximum falls on that local civil date, postpone to nija
    Bhadrapada's Sravana-nakshatra day. Consecutive sunrise matches keep the
    former date (vriddhi).
    """
    SRAVANA_NAKSHATRA = 22

    def matches_for_masa(masa):
        return resolve_vriddhi_dates([
            civil_date for civil_date, _tithi, nakshatra, day_masa, is_adhika, _sunrise_jd in records
            if day_masa == masa and not is_adhika and nakshatra == SRAVANA_NAKSHATRA
        ])

    # For kshaya nakshatra / eclipse:
    # TTD/Sri-Vaishnava rule: Sravana masa = 5. If unavailable or eclipsed,
    # use Bhadrapada masa = 6 for Sravana Nakshatra.
    # Madhwas use Sravana-S05 instead (e.g. SRS Mutt: 03-08-2022)
    # Smartas use the former civil date when there is Kshaya nakshatra
    # (e.g. Sringeri: 11-08-2022)
    primary = matches_for_masa("5")
    fallback = matches_for_masa("6")
    return postpone_upakarma_if_eclipse(primary, fallback, geopos, timezone_name)


def select_vaikuntha_ekadashi_dates(records):
    """Margasira or Pausha Shukla Ekadashi upavasa while the Sun is in Dhanur.

    Candidates are the shared Ekadashi upavasa dates (same sunrise/vriddhi/
    kshaya rules as ``resolve_ekadashi_dates``), kept only when the civil day
    falls in lunar masa 9 or 10, remains Shukla, and ``panchanga.raasi`` at
    sunrise is 9 (Dhanur). Returns an empty list when none qualify (the PDF
    prints ``None``).
    """
    records_by_date = {record[CIVIL_DATE]: record for record in records}
    selected = []
    for civil_date in ekadashi_dates_from_records(records):
        record = records_by_date.get(civil_date)
        if record is None:
            continue
        _date, tithi, _nakshatra, masa, _is_adhika, sunrise_jd = record
        if masa not in {"9", "10"} or not str(tithi).startswith("S"):
            continue
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
    for civil_date, _tithi, _nakshatra, _masa, _is_adhika, sunrise_jd in sorted(records):
        raasi = panchanga.raasi(sunrise_jd)
        if raasi == MAKARA_RAASI and previous_raasi != MAKARA_RAASI:
            if previous_raasi is not None:
                selected.append(civil_date)
        previous_raasi = raasi
    return selected


def select_non_tithi_dates(records, name, geopos=None, timezone_name=None):
    """Dispatch a non-tithi festival to its selector by catalog name."""
    if name == "Varamahalakshmi Vrata":
        return select_varamahalakshmi_dates(records)
    if name == "Rig Upakarma":
        return select_rig_upakarma_dates(records, geopos=geopos, timezone_name=timezone_name)
    if name == "Yajur Upakarma":
        return select_yajur_upakarma_dates(records, geopos=geopos, timezone_name=timezone_name)
    if name == "Vaikuntha Ekadashi":
        return select_vaikuntha_ekadashi_dates(records)
    if name == "Makara Sankranti":
        return select_makara_sankranti_dates(records)
    raise ValueError(f"No selector for non-tithi festival {name!r}")


def resolve_festivals(months, month_data, *, context_months=None, context_data=None, geopos=None, timezone_name=None,
                      enabled_names=None):
    """Resolve tithi and non-tithi festivals for the PDF calendar.

    When ``enabled_names`` is set, only those catalog festivals are resolved
    and returned. ``None`` includes the full catalog (unit-test default).
    """
    if (context_months is None) != (context_data is None):
        raise ValueError("context_months and context_data must be supplied together")

    target_records = collect_records(months, month_data)
    target_dates = {civil_date for civil_date, *_ in target_records}
    if context_months is not None:
        records = collect_records(context_months, context_data)
    else:
        records = target_records

    dates_by_number = {}
    names_by_number = {}

    for number, name, masa, tithi in TITHI_FESTIVAL_RULES:
        if enabled_names is not None and name not in enabled_names:
            continue
        candidates = select_plain_tithi_dates(
            records,
            masa,
            tithi,
            allow_adhika=(number == 1),  # Ugadi
        )
        matches = [civil_date for civil_date in candidates if civil_date in target_dates]
        if not matches:
            raise RuntimeError(f"No calendar date found for {name}")
        dates_by_number[number] = matches
        names_by_number[number] = name

    VAIKUNTHA_EKADASI = 22  # 'number' in array NON_TITHI_FESTIVAL_RULES
    for number, name in NON_TITHI_FESTIVAL_RULES:
        if enabled_names is not None and name not in enabled_names:
            continue
        matches = [
            civil_date
            for civil_date in select_non_tithi_dates(records, name, geopos=geopos, timezone_name=timezone_name)
            if civil_date in target_dates
        ]
        # Vaikuntha Ekadashi may be absent when no Margasira/Pausha S11 falls
        # while the Sun is in Dhanur; e.g. year 2086.
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
        entries.append((number, format_festival_dates(dates), names_by_number[number]))
    return numbers_by_date, entries


def resolve_ekadashi_dates(months, month_data):
    """Resolve Ekadashi upavasa dates with the same sunrise/vriddhi/kshaya rules."""
    return ekadashi_dates_from_records(collect_records(months, month_data))


def ekadashi_dates_from_records(records):
    """Civil days for S11 and K11 using sunrise, vriddhi, and kshaya rules."""
    selected = set()
    for tithi in ("S11", "K11"):
        selected.update(select_tithi_dates(records, tithi))
    return sorted(selected)
