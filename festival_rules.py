"""Festival API consumed by the PDF calendar generator."""

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


# Seasonal catalog for PDF markers. ``(name, masa, tithi)``; ``masa``/``tithi``
# are ``None`` for non-tithi festivals (selector dispatch is by name).
FESTIVAL_RULES = (
    ("Ugadi", 1, "S1"),
    ("Rama Navami", 1, "S9"),
    ("Hanuman Jayanti", 1, "S15"),
    ("Mesha Sankranti", None, None),
    ("Akshaya Tritiya", 2, "S3"),
    ("Vasavi Jayanti", 2, "S10"),
    ("Narasimha Jayanti", 2, "S14"),
    ("Vata Savitri Purnima", 3, "S15"),
    ("Guru Purnima", 4, "S15"),
    ("Naga Panchami", 5, "S5"),
    ("Varamahalakshmi Vrata", None, None),
    ("Rig Upakarma", None, None),
    ("Yajur Upakarma", None, None),
    ("Raksha Bandhan", 5, "S15"),
    ("Sama Upakarma", None, None),
    ("Onam", None, None),
    ("Janmashtami", 5, "K8"),
    ("Swarna Gowri Vrata", 6, "S3"),
    ("Ganesha Chaturthi", 6, "S4"),
    ("Rishi Panchami", 6, "S5"),
    ("Ananta Chaturdashi", 6, "S14"),
    ("Mahalaya Amavasya", 6, "K15"),
    ("Durga Ashtami", 7, "S8"),
    ("Ayudha Puja", 7, "S9"),
    ("Vijayadashami", 7, "S10"),
    ("Karwa Chauth", 7, "K4"),
    ("Dhana Trayodashi", 7, "K13"),
    ("Naraka Chaturdashi", 7, "K14"),
    ("Deepavali", 7, "K15"),
    ("Bali Padyami", 8, "S1"),
    ("Surya Shashthi / Chhath", 8, "S6"),
    ("Gita Jayanti", 9, "S11"),
    ("Vaikuntha Ekadashi", None, None),
    ("Makara Sankranti", None, None),
    ("Vasavi Atmarpana", 11, "S2"),
    ("Vasanta Panchami", 11, "S5"),
    ("Ratha Saptami", 11, "S7"),
    ("VSN Jayanti", 11, "S11"),
    ("Maha Shivaratri", 11, "K14"),
    ("Kama Dahana (Holi)", 12, "S15"),
)

# Festival record: (civil_date, tithi, nakshatra, masa, is_adhika, sunrise_jd).
# Prefer unpacking at call sites; use these only for single-field peeks.
CIVIL_DATE, TITHI, NAKSHATRA, MASA, IS_ADHIKA, SUNRISE_JD = range(6)

_TRUTHY = frozenset({"yes", "true", "1", "on"})
_FALSY = frozenset({"no", "false", "0", "off"})
HASTA_NAKSHATRA = 13
SRAVANA_NAKSHATRA = 22


def all_festival_names():
    """Catalog festival names in fixed seasonal order."""
    return tuple(name for name, _masa, _tithi in FESTIVAL_RULES)


def _parse_bool(raw, *, key):
    value = raw.strip().casefold()
    if value in _TRUTHY:
        return True
    if value in _FALSY:
        return False
    raise ValueError(f"Invalid value for festival {key!r}: {raw!r} "
                     "(use yes/no, true/false, 1/0, or on/off)")


def load_festival_selection(path):
    """Enabled festival names from an INI cfg with a complete ``[festivals]`` section."""
    path = Path(path)
    parser = configparser.ConfigParser(strict=True)
    parser.optionxform = str  # preserve festival name case
    try:
        parser.read_string(path.read_text(encoding="utf-8"))
    except configparser.DuplicateOptionError as error:
        raise ValueError(f"Duplicate festival entries in {path}: {error.option}") from error
    except configparser.DuplicateSectionError as error:
        raise ValueError(f"Duplicate section in {path}: [{error.section}]") from error

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

    return frozenset(name for name, raw in configured.items() if _parse_bool(raw, key=name))


def collect_records(months, month_data):
    """Flatten ``daily_values`` rows into festival records.

    Output: ``(civil_date, tithi, nakshatra, masa, is_adhika, sunrise_jd)``.
    """
    records = []
    for year, month in months:
        for row in month_data[(year, month)]:
            records.append((
                CivilDate(year, month, row[0]),
                row[1],   # tithi
                row[2],   # nakshatra
                row[4],   # masa
                row[5],   # is_adhika
                row[6],   # sunrise_jd
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

    With ``masa``, check the later sunrise for Shukla and the earlier for Krishna.
    """
    target_tithi = plain_tithi_number(tithi)
    if target_tithi is None:
        return []
    masa_codes = masa_codes_for(masa, allow_adhika)
    matches = []
    ordered = sorted(records)
    for record, following in zip(ordered, ordered[1:]):
        civil_date, day_tithi, _, day_masa, _, _ = record
        next_date, next_tithi, _, next_masa, _, _ = following
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

    Vriddhi keeps the former date; kshaya keeps the later civil date.
    """
    masa_codes = masa_codes_for(masa, allow_adhika)
    sunrise_matches = resolve_vriddhi_dates([
        civil_date for civil_date, day_tithi, _, day_masa, _, _ in records
        if day_tithi == tithi and (masa_codes is None or day_masa in masa_codes)
    ])
    sunrise_dates = set(sunrise_matches)
    kshaya_matches = [
        civil_date for civil_date in select_kshaya_dates(records, tithi, masa=masa, allow_adhika=allow_adhika)
        if civil_date not in sunrise_dates
    ]
    return sorted(set(sunrise_matches) | set(kshaya_matches))


def select_plain_tithi_dates(records, masa, tithi, *, allow_adhika=False):
    """Civil days for a plain masa+tithi festival (adhika-preferring when allowed)."""
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
    """Friday strictly before non-adhika Sravana Purnima (S15)."""
    selected = []
    for purnima_date in select_plain_tithi_dates(records, 5, "S15"):
        vrata_date = purnima_date - timedelta(days=1)
        while vrata_date.weekday() != calendar.FRIDAY:
            vrata_date -= timedelta(days=1)
        selected.append(vrata_date)
    return selected


def _eclipse_phase(flags):
    """Return Partial/Total/Annular, or None if not locally usable."""
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
    """Locally visible partial/total/annular eclipses with maximum in ``[start_jd, end_jd)``."""
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
    """Nija Sravana Purnima (S15), postponed to Bhadrapada S15 on eclipse."""
    primary = select_plain_tithi_dates(records, 5, "S15")
    fallback = select_plain_tithi_dates(records, 6, "S15")
    return postpone_upakarma_if_eclipse(primary, fallback, geopos, timezone_name)


def select_rig_upakarma_dates(records, geopos=None, timezone_name=None):
    """Nija Sravana-nakshatra day, postponed to Bhadrapada on kshaya/eclipse."""
    # For kshaya nakshatra / eclipse:
    # TTD/Sri-Vaishnava rule: Sravana masa = 5. If unavailable or eclipsed,
    # use Bhadrapada masa = 6 for Sravana Nakshatra.
    # Madhwas use Sravana-S05 instead (e.g. SRS Mutt: 03-08-2022)
    # Smartas use the former civil date when there is Kshaya nakshatra
    # (e.g. Sringeri: 11-08-2022)
    primary = resolve_vriddhi_dates([
        civil_date for civil_date, _, nakshatra, day_masa, is_adhika, _ in records
        if day_masa == "5" and not is_adhika and nakshatra == SRAVANA_NAKSHATRA
    ])
    fallback = resolve_vriddhi_dates([
        civil_date for civil_date, _, nakshatra, day_masa, is_adhika, _ in records
        if day_masa == "6" and not is_adhika and nakshatra == SRAVANA_NAKSHATRA
    ])
    return postpone_upakarma_if_eclipse(primary, fallback, geopos, timezone_name)


def select_sama_upakarma_dates(records, geopos=None, timezone_name=None):
    """Nija Bhadrapada Hasta, postponed to Sravana Hasta on kshaya / local lunar eclipse."""
    primary = resolve_vriddhi_dates([
        civil_date for civil_date, _, nakshatra, day_masa, is_adhika, _ in records
        if day_masa == "6" and not is_adhika and nakshatra == HASTA_NAKSHATRA
    ])
    fallback = resolve_vriddhi_dates([
        civil_date for civil_date, _, nakshatra, day_masa, is_adhika, _ in records
        if day_masa == "5" and not is_adhika and nakshatra == HASTA_NAKSHATRA
    ])
    return postpone_upakarma_if_eclipse(primary, fallback, geopos, timezone_name)


def select_onam_dates(records):
    """Sravana-nakshatra sunrise in Simha; if none, try Kanya. Vriddhi keeps former.

    Same sunrise/vriddhi/kshaya-fallback pattern as Rig Upakarma, but keyed on
    solar rasi (Simha then Kanya) rather than lunar masa, with no eclipse test.
    """
    SIMHA_RAASI = 5
    KANYA_RAASI = 6

    primary = resolve_vriddhi_dates([
        civil_date for civil_date, _, nakshatra, _, _, sunrise_jd in records
        if nakshatra == SRAVANA_NAKSHATRA and panchanga.raasi(sunrise_jd) == SIMHA_RAASI
    ])
    if primary:
        return primary
    return resolve_vriddhi_dates([
        civil_date for civil_date, _, nakshatra, _, _, sunrise_jd in records
        if nakshatra == SRAVANA_NAKSHATRA and panchanga.raasi(sunrise_jd) == KANYA_RAASI
    ])


def select_vaikuntha_ekadashi_dates(records):
    """Margasira/Pausha Shukla Ekadashi upavasa while the Sun is in Dhanur."""
    records_by_date = {record[CIVIL_DATE]: record for record in records}
    selected = []
    for civil_date in ekadashi_dates_from_records(records):
        record = records_by_date.get(civil_date)
        if record is None:
            continue
        _date, tithi, _, masa, _, sunrise_jd = record
        if masa not in {"9", "10"} or not str(tithi).startswith("S"):
            continue
        if panchanga.raasi(sunrise_jd) == 9:
            selected.append(civil_date)
    return selected


def sankranti_raasi_by_date(records):
    """Map civil date → rāśi (1–12) for each first sunrise into a new solar sign.

    Uses the same rule as Mesha/Makara festival selectors: the civil day of the
    first local sunrise at which the Sun is already in the new rāśi.
    """
    selected = {}
    previous_raasi = None
    for civil_date, _, _, _, _, sunrise_jd in sorted(records):
        raasi = int(panchanga.raasi(sunrise_jd))
        if previous_raasi is not None and raasi != previous_raasi:
            selected[civil_date] = raasi
        previous_raasi = raasi
    return selected


def select_sankranti_dates(records, target_raasi):
    """First civil sunrise after each transition into ``target_raasi``."""
    target = int(target_raasi)
    return [
        civil_date
        for civil_date, raasi in sankranti_raasi_by_date(records).items()
        if raasi == target
    ]


def select_mesha_sankranti_dates(records):
    """First civil sunrise after each transition into Mesha (raasi 1)."""
    return select_sankranti_dates(records, 1)


def select_makara_sankranti_dates(records):
    """First civil sunrise after each transition into Makara (raasi 10)."""
    return select_sankranti_dates(records, 10)


def select_non_tithi_dates(records, name, geopos=None, timezone_name=None):
    """Dispatch a non-tithi festival to its selector by catalog name."""
    if name == "Varamahalakshmi Vrata":
        return select_varamahalakshmi_dates(records)
    if name == "Rig Upakarma":
        return select_rig_upakarma_dates(records, geopos=geopos, timezone_name=timezone_name)
    if name == "Sama Upakarma":
        return select_sama_upakarma_dates(records, geopos=geopos, timezone_name=timezone_name)
    if name == "Yajur Upakarma":
        return select_yajur_upakarma_dates(records, geopos=geopos, timezone_name=timezone_name)
    if name == "Onam":
        return select_onam_dates(records)
    if name == "Vaikuntha Ekadashi":
        return select_vaikuntha_ekadashi_dates(records)
    if name == "Mesha Sankranti":
        return select_mesha_sankranti_dates(records)
    if name == "Makara Sankranti":
        return select_makara_sankranti_dates(records)
    raise ValueError(f"No selector for non-tithi festival {name!r}")


def resolve_festivals(months, month_data, *, context_months=None, context_data=None, geopos=None, timezone_name=None,
                      enabled_names=None):
    """Resolve festivals for the PDF calendar.

    Returns ``(markers_by_date, entries)`` where markers are dense ``1..N`` in
    ``FESTIVAL_RULES`` order among enabled festivals, and each entry is
    ``(marker, date_text, name)``.
    """
    if (context_months is None) != (context_data is None):
        raise ValueError("context_months and context_data must be supplied together")

    target_records = collect_records(months, month_data)
    target_dates = {civil_date for civil_date, *_ in target_records}
    if context_months is not None:
        records = collect_records(context_months, context_data)
    else:
        records = target_records

    dates_by_name = {}

    def store(name, candidates, *, allow_empty=False):
        matches = [civil_date for civil_date in candidates if civil_date in target_dates]
        if not matches and not allow_empty:
            raise RuntimeError(f"No calendar date found for {name}")
        dates_by_name[name] = matches

    for name, masa, tithi in FESTIVAL_RULES:
        if enabled_names is not None and name not in enabled_names:
            continue
        if masa is None:
            # Vaikuntha Ekadashi may be absent when no Margasira/Pausha S11 falls
            # while the Sun is in Dhanur; e.g. year 2086.
            store(name, select_non_tithi_dates(records, name, geopos=geopos, timezone_name=timezone_name),
                  allow_empty=(name == "Vaikuntha Ekadashi"))
        else:
            store(name, select_plain_tithi_dates(records, masa, tithi, allow_adhika=(name == "Ugadi")))

    markers_by_date = {}
    entries = []
    marker = 0
    for name, _masa, _tithi in FESTIVAL_RULES:
        if name not in dates_by_name:
            continue
        marker += 1
        dates = dates_by_name[name]
        for civil_date in dates:
            markers_by_date.setdefault(civil_date, []).append(marker)
        entries.append((marker, format_festival_dates(dates), name))
    return markers_by_date, entries


def resolve_ekadashi_dates(months, month_data):
    """Resolve Ekadashi upavasa dates with the same sunrise/vriddhi/kshaya rules."""
    return ekadashi_dates_from_records(collect_records(months, month_data))


def ekadashi_dates_from_records(records):
    """Civil days for S11 and K11 using sunrise, vriddhi, and kshaya rules."""
    selected = set()
    for tithi in ("S11", "K11"):
        selected.update(select_tithi_dates(records, tithi))
    return sorted(selected)
