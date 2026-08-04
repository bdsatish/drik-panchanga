"""Festival API consumed by the PDF calendar generator."""

import calendar
import configparser
import logging
from collections import namedtuple as struct
from datetime import date as CivilDate
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import panchanga

SECONDS_PER_DAY = 24 * 60 * 60
JULIAN_DAY_AT_UNIX_EPOCH = 2440587.5
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


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


DayRecord = struct('DayRecord', ['civil_date', 'tithi', 'nakshatra', 'yoga', 'masa', 'is_adhika', 'sunrise_jd'])

FestivalRule = struct('FestivalRule',
                      ['name', 'masa', 'tithi', 'selector', 'allow_adhika', 'allow_empty', 'location_aware'],
                      defaults=(None, None, None, False, False, False))

HASTA_NAKSHATRA = 13
SRAVANA_NAKSHATRA = 22


def all_festival_names():
  """Catalog festival names in fixed seasonal order."""
  return tuple(rule.name for rule in FESTIVAL_RULES)


def load_festival_selection(path):
  """Enabled festival names from the ``[festivals]`` section of an INI cfg."""
  parser = configparser.ConfigParser(strict=True)
  parser.optionxform = str  # preserve festival name case
  parser.read_string(Path(path).read_text(encoding="utf-8"))
  enabled = []
  for name, raw in parser.items("festivals"):
    if raw.strip().casefold() in ("yes", "true", "1", "on"):
      enabled.append(name)
  return enabled


def format_festival_dates(dates):
  dates = sorted(dates)
  if not dates:
    return "None"

  # Consecutive days in one month → "Mar 19-21"; otherwise list each date.
  same_month = all(value.year == dates[0].year and value.month == dates[0].month for value in dates)
  consecutive = all(dates[i] == dates[i - 1] + timedelta(days=1) for i in range(1, len(dates)))
  if len(dates) > 1 and same_month and consecutive:
    return (f"{calendar.month_abbr[dates[0].month]} "
            f"{dates[0].day:02d}-{dates[-1].day:02d}")
  return ",".join(f"{calendar.month_abbr[value.month]} {value.day:02d}" for value in dates)


def plain_tithi_number(tithi):
  """Convert ``S1``..``S15`` or ``K1``..``K15`` to 1..30."""
  number = int(tithi[1:])
  if tithi.startswith("S"):
    return number
  return number + 15


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


def select_kshaya_dates(records, tithi, masa=None, allow_adhika=False):
  """Later civil day when the tithi is skipped between sunrises.

    With ``masa``, check the later sunrise for Shukla and the earlier for Krishna.
    """
  target_tithi = plain_tithi_number(tithi)
  masa_codes = masa_codes_for(masa, allow_adhika)
  matches = []
  ordered = sorted(records, key=lambda record: record.civil_date)
  for record, following in zip(ordered, ordered[1:]):
    civil_date, day_tithi, day_masa = record.civil_date, record.tithi, record.masa
    next_date, next_tithi, next_masa = following.civil_date, following.tithi, following.masa
    if next_date != civil_date + timedelta(days=1):
      continue
    start_tithi = plain_tithi_number(day_tithi)
    end_tithi = plain_tithi_number(next_tithi)
    skipped = [(start_tithi + offset - 1) % 30 + 1 for offset in range(1, (end_tithi - start_tithi) % 30)]
    if target_tithi not in skipped:
      continue
    if masa_codes is not None:
      check_masa = next_masa if target_tithi <= 15 else day_masa
      if check_masa not in masa_codes:
        continue
    matches.append(next_date)
  return matches


def select_tithi_dates(records, tithi, masa=None, allow_adhika=False):
  """Civil days for a tithi using sunrise, vriddhi, and kshaya rules.

    Vriddhi keeps the former date; kshaya keeps the later civil date.
    """
  masa_codes = masa_codes_for(masa, allow_adhika)
  sunrise_dates = []
  for record in records:
    if record.tithi != tithi:
      continue
    if masa_codes is not None and record.masa not in masa_codes:
      continue
    sunrise_dates.append(record.civil_date)
  sunrise_matches = resolve_vriddhi_dates(sunrise_dates)
  sunrise_set = set(sunrise_matches)

  kshaya_matches = []
  for civil_date in select_kshaya_dates(records, tithi, masa=masa, allow_adhika=allow_adhika):
    if civil_date not in sunrise_set:
      kshaya_matches.append(civil_date)
  return sorted(set(sunrise_matches) | set(kshaya_matches))


def select_plain_tithi_dates(records, masa, tithi, allow_adhika=False):
  """Civil days for a plain masa+tithi festival (adhika-preferring when allowed)."""
  matches = select_tithi_dates(records, tithi, masa=masa, allow_adhika=allow_adhika)
  if not allow_adhika or not matches:
    return matches
  records_by_date = {record.civil_date: record for record in records}
  adhika_matches = []
  for civil_date in matches:
    record = records_by_date[civil_date]
    if record.is_adhika or record.masa.startswith("A"):
      adhika_matches.append(civil_date)
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

  searches = (("Lunar", panchanga.swe.lun_eclipse_when_loc), ("Solar", panchanga.swe.sol_eclipse_when_loc))
  found = []
  for kind, finder in searches:
    search_jd = start_jd - 1.0
    while search_jd < end_jd + 2.0:
      try:
        flags, times, _ = finder(search_jd, geopos)
      except Exception as error:
        log.error("Eclipse search for %s failed at JD %s: %s", kind, search_jd, error)
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
    log.error("Upakarma eclipse check skipped: no timezone name")
    return list(primary)
  if geopos is not None and any(civil_day_has_eclipse(civil_date, geopos, timezone_name) for civil_date in primary):
    return list(fallback) if fallback else list(primary)
  return list(primary)


def select_yajur_upakarma_dates(records, geopos=None, timezone_name=None):
  """Nija Sravana Purnima (S15), postponed to Bhadrapada S15 on eclipse."""
  primary = select_plain_tithi_dates(records, 5, "S15")
  fallback = select_plain_tithi_dates(records, 6, "S15")
  return postpone_upakarma_if_eclipse(primary, fallback, geopos, timezone_name)


def _nija_nakshatra_dates(records, masa, nakshatra):
  """Non-adhika civil dates with ``nakshatra`` in lunar ``masa``, vriddhi-resolved."""
  dates = []
  masa_code = str(masa)
  for record in records:
    if record.masa != masa_code:
      continue
    if record.is_adhika:
      continue
    if record.nakshatra != nakshatra:
      continue
    dates.append(record.civil_date)
  return resolve_vriddhi_dates(dates)


def _sravana_nakshatra_in_raasi_dates(records, raasi):
  """Sravana-nakshatra sunrises in solar ``raasi``, vriddhi-resolved."""
  dates = []
  for record in records:
    if record.nakshatra != SRAVANA_NAKSHATRA:
      continue
    if panchanga.raasi(record.sunrise_jd) != raasi:
      continue
    dates.append(record.civil_date)
  return resolve_vriddhi_dates(dates)


def select_rig_upakarma_dates(records, geopos=None, timezone_name=None):
  """Nija Sravana-nakshatra day, postponed to Bhadrapada on kshaya/eclipse."""
  # For kshaya nakshatra / eclipse:
  # TTD/Sri-Vaishnava rule: Sravana masa = 5. If unavailable or eclipsed,
  # use Bhadrapada masa = 6 for Sravana Nakshatra.
  # Madhwas use Sravana-S05 instead (e.g. SRS Mutt: 03-08-2022)
  # Smartas use the former civil date when there is Kshaya nakshatra
  # (e.g. Sringeri: 11-08-2022)
  primary = _nija_nakshatra_dates(records, 5, SRAVANA_NAKSHATRA)
  fallback = _nija_nakshatra_dates(records, 6, SRAVANA_NAKSHATRA)
  return postpone_upakarma_if_eclipse(primary, fallback, geopos, timezone_name)


def select_sama_upakarma_dates(records, geopos=None, timezone_name=None):
  """Nija Bhadrapada Hasta, postponed to Sravana Hasta on kshaya / local lunar eclipse."""
  primary = _nija_nakshatra_dates(records, 6, HASTA_NAKSHATRA)
  fallback = _nija_nakshatra_dates(records, 5, HASTA_NAKSHATRA)
  return postpone_upakarma_if_eclipse(primary, fallback, geopos, timezone_name)


def select_onam_dates(records):
  """Sravana-nakshatra sunrise in Simha; if none, try Kanya. Vriddhi keeps former.

    Same sunrise/vriddhi/kshaya-fallback pattern as Rig Upakarma, but keyed on
    solar rasi (Simha then Kanya) rather than lunar masa, with no eclipse test.
    """
  SIMHA_RAASI = 5
  KANYA_RAASI = 6

  primary = _sravana_nakshatra_in_raasi_dates(records, SIMHA_RAASI)
  if primary:
    return primary
  return _sravana_nakshatra_in_raasi_dates(records, KANYA_RAASI)


def select_vaikuntha_ekadashi_dates(records):
  """Margasira/Pausha Shukla Ekadashi upavasa while the Sun is in Dhanur."""
  records_by_date = {record.civil_date: record for record in records}
  selected = []
  for civil_date in select_tithi_dates(records, "S11"):
    record = records_by_date[civil_date]
    if record.masa not in {"9", "10"}:
      continue
    if panchanga.raasi(record.sunrise_jd) == 9:
      selected.append(civil_date)
  return selected


def sankranti_raasi_by_date(records):
  """Map civil date → rāśi (1–12) for each first sunrise into a new solar sign.

    Uses the same rule as Mesha/Makara festival selectors: the civil day of the
    first local sunrise at which the Sun is already in the new rāśi.
    """
  selected = {}
  previous_raasi = None
  for record in sorted(records, key=lambda record: record.civil_date):
    raasi = int(panchanga.raasi(record.sunrise_jd))
    if previous_raasi is not None and raasi != previous_raasi:
      selected[record.civil_date] = raasi
    previous_raasi = raasi
  return selected


def select_sankranti_dates(records, target_raasi):
  """First civil sunrise after each transition into ``target_raasi``."""
  target = int(target_raasi)
  dates = []
  for civil_date, raasi in sankranti_raasi_by_date(records).items():
    if raasi == target:
      dates.append(civil_date)
  return dates


def select_mesha_sankranti_dates(records):
  """First civil sunrise after each transition into Mesha (raasi 1)."""
  return select_sankranti_dates(records, 1)


def select_makara_sankranti_dates(records):
  """First civil sunrise after each transition into Makara (raasi 10)."""
  return select_sankranti_dates(records, 10)


def select_solstice_dates(records, solstice_longitude, timezone_name=None):
  """First civil sunrise after each tropical solstice moment.

    Swiss Ephemeris finds the tropical Sun longitude crossing at 90° (June
    solstice) or 270° (December solstice). The search is limited to a narrow
    local-date window around the event; sunrise JDs are UT, so comparing them
    directly with the UT event moment preserves the local sunrise rule.
    """
  records_by_date = {record.civil_date: record for record in records}
  years = sorted({civil_date.year for civil_date in records_by_date})
  local_timezone = timezone_name or "UTC"
  selected = []
  for year in years:
    start_jd = panchanga.gregorian_to_jd(panchanga.Date(year, 1, 1))
    flags = panchanga.swe.FLG_SWIEPH | panchanga.swe.FLG_TROPICAL
    solstice_jd = panchanga.swe.solcross_ut(float(solstice_longitude), start_jd, flags)
    solstice_date = jd_to_local_civil_date(solstice_jd, local_timezone)
    for offset in range(-2, 2):
      # Timezones can shift the displayed solstice date; the exact UT
      # comparison below determines which nearby sunrise qualifies.
      civil_date = solstice_date + timedelta(days=offset)
      record = records_by_date.get(civil_date)
      if record is not None and record.sunrise_jd > solstice_jd:
        selected.append(civil_date)
        break
  return sorted(set(selected))


def _is_southern_hemisphere(geopos):
  return geopos is not None and float(geopos[1]) < 0.0


def select_uttarayana_dates(records, geopos=None, timezone_name=None):
  """First sunrise after the local winter solstice.

    The local winter solstice is the June solstice south of the equator and
    the December solstice at or north of the equator.
    """
  longitude = 90.0 if _is_southern_hemisphere(geopos) else 270.0
  return select_solstice_dates(records, longitude, timezone_name=timezone_name)


def select_dakshinayana_dates(records, geopos=None, timezone_name=None):
  """First sunrise after the local summer solstice.

    The local summer solstice is the December solstice south of the equator
    and the June solstice at or north of the equator.
    """
  longitude = 270.0 if _is_southern_hemisphere(geopos) else 90.0
  return select_solstice_dates(records, longitude, timezone_name=timezone_name)


# Seasonal catalog and each entry's complete resolution policy.
# Plain entries use masa+tithi; ``selector`` is a custom date-finder function
# for festivals that need extra rules (sankranti, upakarma, solstice, …).
FESTIVAL_RULES = [
  FestivalRule("Ugadi", masa=1, tithi="S1", allow_adhika=True),
  FestivalRule("Rama Navami", masa=1, tithi="S9"),
  FestivalRule("Hanuman Jayanti", masa=1, tithi="S15"),
  FestivalRule("Mesha Sankranti", selector=select_mesha_sankranti_dates),
  FestivalRule("Akshaya Tritiya", masa=2, tithi="S3"),
  FestivalRule("Vasavi Jayanti", masa=2, tithi="S10"),
  FestivalRule("Narasimha Jayanti", masa=2, tithi="S14"),
  FestivalRule("Vata Savitri Purnima", masa=3, tithi="S15"),
  FestivalRule("Dakshinayana", selector=select_dakshinayana_dates, location_aware=True),
  FestivalRule("Guru Purnima", masa=4, tithi="S15"),
  FestivalRule("Naga Panchami", masa=5, tithi="S5"),
  FestivalRule("Varamahalakshmi Vrata", selector=select_varamahalakshmi_dates),
  FestivalRule("Rig Upakarma", selector=select_rig_upakarma_dates, location_aware=True),
  FestivalRule("Yajur Upakarma", selector=select_yajur_upakarma_dates, location_aware=True),
  FestivalRule("Raksha Bandhan", masa=5, tithi="S15"),
  FestivalRule("Sama Upakarma", selector=select_sama_upakarma_dates, location_aware=True),
  FestivalRule("Onam", selector=select_onam_dates),
  FestivalRule("Janmashtami", masa=5, tithi="K8"),
  FestivalRule("Swarna Gowri Vrata", masa=6, tithi="S3"),
  FestivalRule("Ganesha Chaturthi", masa=6, tithi="S4"),
  FestivalRule("Rishi Panchami", masa=6, tithi="S5"),
  FestivalRule("Ananta Chaturdashi", masa=6, tithi="S14"),
  FestivalRule("Mahalaya Amavasya", masa=6, tithi="K15"),
  FestivalRule("Durga Ashtami", masa=7, tithi="S8"),
  FestivalRule("Ayudha Puja", masa=7, tithi="S9"),
  FestivalRule("Vijayadashami", masa=7, tithi="S10"),
  FestivalRule("Karwa Chauth", masa=7, tithi="K4"),
  FestivalRule("Dhana Trayodashi", masa=7, tithi="K13"),
  FestivalRule("Naraka Chaturdashi", masa=7, tithi="K14"),
  FestivalRule("Deepavali", masa=7, tithi="K15"),
  FestivalRule("Bali Padyami", masa=8, tithi="S1"),
  FestivalRule("Surya Shashthi / Chhath", masa=8, tithi="S6"),
  FestivalRule("Gita Jayanti", masa=9, tithi="S11"),
  FestivalRule("Uttarayana", selector=select_uttarayana_dates, location_aware=True),
  FestivalRule("Vaikuntha Ekadashi", selector=select_vaikuntha_ekadashi_dates, allow_empty=True),
  FestivalRule("Makara Sankranti", selector=select_makara_sankranti_dates),
  FestivalRule("Vasavi Atmarpana", masa=11, tithi="S2"),
  FestivalRule("Vasanta Panchami", masa=11, tithi="S5"),
  FestivalRule("Ratha Saptami", masa=11, tithi="S7"),
  FestivalRule("VSN Jayanti", masa=11, tithi="S11"),
  FestivalRule("Maha Shivaratri", masa=11, tithi="K14"),
  FestivalRule("Kama Dahana (Holi)", masa=12, tithi="S15")
]


def select_dates_for_rule(rule, records, geopos=None, timezone_name=None):
  """Run a custom selector or the standard māsa+tithi selector."""
  if not rule.selector:
    return select_plain_tithi_dates(records, rule.masa, rule.tithi, allow_adhika=rule.allow_adhika)
  if rule.location_aware:
    return rule.selector(records, geopos=geopos, timezone_name=timezone_name)
  return rule.selector(records)


def resolve_festivals(records, target_dates, geopos=None, timezone_name=None, enabled_names=None):
  """Return PDF day markers and footer entries for enabled festivals.

    ``markers_by_date`` looks like ``{date: [1, 3]}``; ``entries`` looks like
    ``[(1, "Mar 19", "Ugadi")]``. Selectors may inspect boundary records, but
    only dates in ``target_dates`` are printed.
    """
  target_dates = set(target_dates)
  markers_by_date = {}
  entries = []
  enabled_rules = []
  for rule in FESTIVAL_RULES:
    if enabled_names is None or rule.name in enabled_names:
      enabled_rules.append(rule)

  for marker, rule in enumerate(enabled_rules, start=1):
    candidates = select_dates_for_rule(rule, records, geopos, timezone_name)
    dates = []
    for civil_date in candidates:
      if civil_date in target_dates:
        dates.append(civil_date)
    if not dates and not rule.allow_empty:
      log.error("No calendar date found for %s; omitting day markers", rule.name)
    for civil_date in dates:
      markers_by_date.setdefault(civil_date, []).append(marker)
    entries.append((marker, format_festival_dates(dates), rule.name))
  return markers_by_date, entries


def ekadashi_dates_from_records(records):
  """Civil days for S11 and K11 using sunrise, vriddhi, and kshaya rules."""
  selected = set()
  for tithi in ("S11", "K11"):
    selected.update(select_tithi_dates(records, tithi))
  return sorted(selected)
