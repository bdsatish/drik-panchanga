"""Julian day, civil date and IANA time-zone helpers, and the hours-past-midnight clock."""

import calendar
from collections import namedtuple as struct
from datetime import datetime, timedelta, timezone
from math import floor
from zoneinfo import ZoneInfo

import swisseph as swe

# Julian Day number as on (year, month, day) at 00:00 UTC
gregorian_to_jd = lambda date, hours=0.0: swe.julday(date.year, date.month, date.day, hours)
jd_to_gregorian = lambda jd: swe.revjul(jd, swe.GREG_CAL)  # returns (y, m, d, h) with h in [0, 24)


class Date(struct('Date', ['year', 'month', 'day'])):
  """Proleptic Gregorian civil date; unlike ``datetime.date``, years <= 0 work (year 0 = 1 BCE).

  ``date + n`` / ``date - n`` shift by whole days; ``date - other`` is the day count between them.
  """
  __slots__ = ()

  def _noon_jd(self):
    # Noon keeps day arithmetic clear of the midnight boundary.
    return swe.julday(self.year, self.month, self.day, 12.0)

  def __add__(self, days):
    return Date(*jd_to_gregorian(self._noon_jd() + days)[:3])

  def __sub__(self, other):
    if isinstance(other, Date):
      return round(self._noon_jd() - other._noon_jd())
    return self + -other

  def weekday(self):
    """Monday = 0 ... Sunday = 6, as ``datetime.date.weekday``."""
    return floor(self._noon_jd()) % 7


# Julian day <-> civil/local time (IANA time zones, DST-aware).
#
# One code path for every year: Julian-day arithmetic via swe.julday/revjul,
# with ``datetime``/``zoneinfo`` used only as the tzdb query layer (the offset
# at an instant or a civil noon). ``Date`` carries proleptic Gregorian years
# <= 0, which ``datetime`` cannot represent, so nothing here builds a
# ``datetime`` for a BCE instant.
_SECONDS_PER_DAY = 24 * 60 * 60
_JULIAN_DAY_AT_YEAR_1 = swe.julday(1, 1, 1)
_JULIAN_DAY_AT_YEAR_4 = swe.julday(4, 1, 1)


def tzinfo_for(timezone_name):
  """tzinfo for an IANA key, or a fixed offset name like ``UTC+5:30``."""
  if timezone_name.startswith(("UTC+", "UTC-")):
    sign = -1 if timezone_name[3] == "-" else 1
    hours, _, minutes = timezone_name[4:].partition(":")
    return timezone(sign * timedelta(hours=int(hours), minutes=int(minutes or 0)))
  return ZoneInfo(timezone_name)


def fixed_offset_name(hours):
  """Display name for a fixed UTC offset in hours: ``5.5`` → ``UTC+5:30``."""
  total = round(hours * 60)
  magnitude = abs(total)
  suffix = f":{magnitude % 60:02d}" if magnitude % 60 else ""
  return f"UTC{'+' if total >= 0 else '-'}{magnitude // 60}{suffix}"


def utc_offset_hours(timezone_name, civil, longitude=None):
  """UTC offset in hours (DST included) at local noon of ``civil``, for the whole civil day.

  Day-granular: one offset per civil date, as the calendar cells bake their
  times. For the offset in force at a specific instant (a row's DST-crossing
  tail) ``format_local_hm`` resolves it per instant.

  The tzdb lookup runs on the year-4 proxy for BCE dates: the rules there
  preserve the historical local mean time offsets that modern standardized
  offsets obscure, and year 4 is the earliest leap year, so a 29 February
  needs no special case. In that LMT era the offset is the tzdb seat's, not
  the observer's: with ``longitude`` given, ``longitude / 15`` (local mean
  solar time) is used instead. Modern standardized offsets ignore
  ``longitude`` entirely.
  """
  zone = tzinfo_for(timezone_name)
  if isinstance(zone, timezone):  # fixed offset: utcoffset ignores the date
    return zone.utcoffset(None).total_seconds() / 3600
  noon = datetime(max(4, civil.year), civil.month, civil.day, 12, tzinfo=zone)
  if longitude is not None and noon.tzname() == "LMT":
    return longitude / 15.0
  return noon.utcoffset().total_seconds() / 3600


def _proxy_civil(jd):
  """A year >= 1 ``Date`` near ``jd`` for tz lookups: the clamped instant itself."""
  return Date(*jd_to_gregorian(max(jd, _JULIAN_DAY_AT_YEAR_4))[:3])


def _instant_offset_hours(jd, timezone_name, longitude=None):
  """UTC offset in hours in force at UT ``jd`` (DST resolved at the instant).

  BCE instants have no ``datetime`` and no DST in the tzdb, so they fall back
  to the flat year-4 era via ``utc_offset_hours``.
  """
  if jd < _JULIAN_DAY_AT_YEAR_1:
    return utc_offset_hours(timezone_name, _proxy_civil(jd), longitude)
  year, month, day, hours = jd_to_gregorian(jd)
  utc = datetime(year, month, day, tzinfo=timezone.utc) + timedelta(seconds=round(hours * 3600))
  try:
    local = utc.astimezone(tzinfo_for(timezone_name))
  except OverflowError:  # the local time falls in year 10000
    raise ValueError(f"Time {utc:%Y-%m-%d %H:%M} UTC is past the last supported local date, 9999-12-31.") from None
  if longitude is not None and local.tzname() == "LMT":
    return longitude / 15.0
  return local.utcoffset().total_seconds() / 3600


def jd_to_local_civil_date(jd, timezone_name, longitude=None):
  """Convert a UT Julian day to the civil ``Date`` in ``timezone_name``.

  Pure Julian-day arithmetic (via ``swe.revjul``) at the instant's own
  offset, so proleptic Gregorian years <= 0 work and DST-transition days
  cannot land a day off.
  """
  local = jd + _instant_offset_hours(jd, timezone_name, longitude) / 24
  return Date(*jd_to_gregorian(local)[:3])


def local_range_jds(start_year, start_month, end_year, end_month, timezone_name, longitude=None):
  """UT Julian days covering the printed Gregorian months in local civil time.

  Pure Julian-day arithmetic (via ``utc_offset_hours``), so proleptic
  Gregorian years <= 0 work. Fixed ``UTC±H[:MM]`` offsets are plain
  ``datetime.timezone`` values."""
  last_day = calendar.monthrange(end_year, end_month)[1]
  start_civil = Date(start_year, start_month, 1)
  end_civil = Date(end_year, end_month, last_day)
  # gregorian_to_jd is the UT JD of 00:00 UT, half a day after local midnight.
  start_jd = gregorian_to_jd(start_civil) - utc_offset_hours(timezone_name, start_civil, longitude) / 24
  end_jd = (gregorian_to_jd(end_civil) + 1 - 1 / _SECONDS_PER_DAY -
            utc_offset_hours(timezone_name, end_civil, longitude) / 24)
  return start_jd, end_jd


def format_utc_offset(timezone_name, year, month, day=15, longitude=None):
  """Return 'UTC+5:30 (IST)' style label for a timezone on a given date.

  The abbreviation comes from the year-4 proxy (as in ``utc_offset_hours``),
  so proleptic Gregorian years <= 0 work."""
  civil = Date(year, month, day)
  total_seconds = int(round(utc_offset_hours(timezone_name, civil, longitude) * 3600))
  sign = "+" if total_seconds >= 0 else "-"
  total_seconds = abs(total_seconds)
  hours, remainder = divmod(total_seconds, 3600)
  minutes = remainder // 60
  offset_str = f"UTC{sign}{hours}" if minutes == 0 else f"UTC{sign}{hours}:{minutes:02d}"
  proxy = datetime(max(4, year), month, day, 12, tzinfo=tzinfo_for(timezone_name))
  abbr = proxy.strftime("%Z") or timezone_name
  return f"{offset_str} ({abbr})"


def dst_transitions(timezone_name, year, month, longitude=None):
  """Return a dict of {day: 'DST starts'|'DST ends'} for transitions in a given month.

  Scans the month day-by-day comparing UTC offset; when the offset changes,
  the transition day is recorded with the appropriate label. The previous
  month's last day is used to detect transitions on the 1st of the month.
  """
  last_day = calendar.monthrange(year, month)[1]
  # Initialize from the last day of the previous month to catch transitions on the 1st
  prev_month_year, prev_month = (year, month - 1) if month > 1 else (year - 1, 12)
  prev_day = calendar.monthrange(prev_month_year, prev_month)[1]
  prev_offset = utc_offset_hours(timezone_name, Date(prev_month_year, prev_month, prev_day), longitude)
  transitions = {}
  for day in range(1, last_day + 1):
    hours = utc_offset_hours(timezone_name, Date(year, month, day), longitude)
    if hours != prev_offset:
      transitions[day] = "DST starts" if hours > prev_offset else "DST ends"
    prev_offset = hours
  return transitions


def to_hms(decimal_hours):
  """For durations and local civil times: split decimal hours to ``[h, m, s]``.

  Rounds to the nearest second with a full carry cascade: ``abs(m) < 60`` and
  ``abs(s) < 60``, and all three components carry the sign of the input, so
  ``format_hms`` reads a negative value back unchanged (``-1.5`` gives
  ``[-1, -30, 0]``, shown as ``-01:30``). ``h`` may exceed 24 (the callers'
  "hours past midnight" convention).
  """
  total_seconds = int(round(decimal_hours * 3600))
  sign = -1 if total_seconds < 0 else 1
  total_seconds = abs(total_seconds)
  hours, rem = divmod(total_seconds, 3600)
  minutes, seconds = divmod(rem, 60)
  return [sign * hours, sign * minutes, sign * seconds]


def format_hms(hms, *, show_seconds=False):
  """``[h, m, s]`` or decimal hours to a display string.

  Hindu-day clocks are hours past the sunrise day's civil midnight: hours
  may exceed 24 (e.g. ``27:00``). Never wrap with ``% 24`` — rounding
  ``23:59:30`` yields ``24:00``, not ``00:00``. The same helper formats
  durations (day/night length); a zero span is ``00:00``, not a midnight flag.

  ``show_seconds`` false -> ``HH:MM`` (grid endpoints); true -> ``HH:MM:SS``
  (day view, sunrise/sunset columns). A time before that midnight (a window
  opening the previous evening) reads ``-00:26``.

  Halves round up. Decimal hours are rounded once, straight to the shown
  unit: rounding to whole seconds first would turn 12:35:29.6 into 12:36.
  """
  if isinstance(hms, (int, float)):  # convenience: decimal hours
    hms = [float(hms), 0, 0]
  hours, minutes, seconds = hms
  if show_seconds:
    total_seconds = floor(hours * 3600 + minutes * 60 + seconds + 0.5)
    sign = "-" if total_seconds < 0 else ""
    h, rem = divmod(abs(total_seconds), 3600)
    m, s = divmod(rem, 60)
    return f"{sign}{h:02d}:{m:02d}:{s:02d}"
  total_minutes = floor(hours * 60 + minutes + seconds / 60.0 + 0.5)
  sign = "-" if total_minutes < 0 else ""
  return f"{sign}{abs(total_minutes) // 60:02d}:{abs(total_minutes) % 60:02d}"


def format_hms_from_jd(jd_ut, civil_jd, timezone_hours, *, show_seconds=False):
  """Format a UT Julian day as local hours past ``civil_jd`` midnight at a known offset.

  Pass the sunrise day's civil JD for Hindu-day endpoints, or the event's
  civil JD when a date label sits beside the time. Same 24:00+ rules as
  ``format_hms``. Use ``format_local_hm`` when the zone name (not the offset)
  is at hand.
  """
  return format_hms((jd_ut - civil_jd) * 24 + timezone_hours, show_seconds=show_seconds)


def format_local_hm(jd, timezone_name, anchor_civil=None, show_seconds=False, longitude=None):
  """Format UT ``jd`` as local ``HH:MM`` / ``HH:MM:SS`` past ``anchor_civil`` midnight.

  Default ``anchor_civil`` is the event's own local civil date. Pass a calendar
  cell's date so a next-morning event stays ``24:00+`` on that row.

  The offset is the one in force at the event's own instant, so a row's tail
  across a DST change reads the clock that actually applied. Pre-modern dates
  (the zone's LMT era) read ``longitude/15`` local mean time, as in
  ``utc_offset_hours``.
  """
  if anchor_civil is None:
    anchor_civil = jd_to_local_civil_date(jd, timezone_name, longitude)
  return format_hms_from_jd(jd, gregorian_to_jd(anchor_civil), _instant_offset_hours(jd, timezone_name, longitude),
                            show_seconds=show_seconds)


def hindu_day_civil(jd, timezone_name, sunrise_jd=None, longitude=None):
  """Civil date whose midnight is the 24:00+ origin for ``jd``.

  If ``sunrise_jd`` is given and ``jd`` is before it, return the previous
  civil date (``00:05`` formats as ``24:05``). Else the event's own civil date.
  """
  civil = jd_to_local_civil_date(jd, timezone_name, longitude)
  if sunrise_jd is not None and jd < sunrise_jd:
    return civil - 1
  return civil