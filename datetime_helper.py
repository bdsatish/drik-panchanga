"""Julian day, civil date and IANA time-zone helpers, and the hours-past-midnight clock."""

import calendar
from collections import namedtuple as struct
from datetime import datetime, timedelta, timezone
from math import floor
from zoneinfo import ZoneInfo

import swisseph as swe

# Julian Day number as on (year, month, day) at 00:00 UTC
gregorian_to_jd = lambda date, hours=0.0: swe.julday(date.year, date.month, date.day, hours)
jd_to_gregorian = lambda jd: swe.revjul(jd, swe.GREG_CAL)  # returns (y, m, d, h, min, s)


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

  def isoformat(self):
    return f"{self.year:04d}-{self.month:02d}-{self.day:02d}"


def local_time_to_jdut1(year, month, day, hour=0, minutes=0, seconds=0, timezone=0.0):
  """Converts local time to JD(UT1)"""
  y, m, d, h, mnt, s = swe.utc_time_zone(year, month, day, hour, minutes, seconds, timezone)
  jd_et, jd_ut1 = swe.utc_to_jd(y, m, d, h, mnt, s, cal=swe.GREG_CAL)
  return jd_ut1


# Julian day <-> civil/local datetime (IANA time zones, DST-aware)
_SECONDS_PER_DAY = 24 * 60 * 60
_JULIAN_DAY_AT_UNIX_EPOCH = 2440587.5
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


def julian_day_from_datetime(value):
  """Convert a timezone-aware ``datetime`` to a UT Julian day."""
  return value.timestamp() / _SECONDS_PER_DAY + _JULIAN_DAY_AT_UNIX_EPOCH


def jd_to_local_datetime(jd, timezone_name):
  """Convert a UT Julian day to local ``datetime`` in ``timezone_name``."""
  utc = datetime.fromtimestamp((jd - _JULIAN_DAY_AT_UNIX_EPOCH) * _SECONDS_PER_DAY, tz=timezone.utc)
  return utc.astimezone(tzinfo_for(timezone_name))


def jd_to_local_civil_date(jd, timezone_name):
  """Convert a UT Julian day to the civil ``Date`` in ``timezone_name``."""
  local = jd_to_local_datetime(jd, timezone_name)
  return Date(local.year, local.month, local.day)


def utc_offset_hours(timezone_name, civil):
  """UTC offset in hours (DST included) at local noon of ``civil``, for the whole civil day.

  Python ``datetime`` does not support year 0 or negative years, and early CE
  dates are clamped to year 4: the tzdb rules there preserve the historical
  local mean time offsets that modern standardized offsets obscure, and year 4
  is the earliest leap year, so a 29 February needs no special case.
  """
  noon = datetime(max(4, civil.year), civil.month, civil.day, 12, tzinfo=tzinfo_for(timezone_name))
  return noon.utcoffset().total_seconds() / 3600


def local_range_jds(start_year, start_month, end_year, end_month, timezone_name):
  """UT Julian days covering the printed Gregorian months in local civil time.

  Fixed ``UTC±H[:MM]`` offsets are plain ``datetime.timezone`` values."""
  timezone_info = tzinfo_for(timezone_name)
  last_day = calendar.monthrange(end_year, end_month)[1]
  start_local = datetime(start_year, start_month, 1, 0, 0, 0, tzinfo=timezone_info)
  end_local = datetime(end_year, end_month, last_day, 23, 59, 59, tzinfo=timezone_info)
  return julian_day_from_datetime(start_local), julian_day_from_datetime(end_local)


def format_utc_offset(timezone_name, year, month, day=15):
  """Return 'UTC+5:30 (IST)' style label for a timezone on a given date."""
  zone = tzinfo_for(timezone_name)
  local = datetime(year, month, day, 12, tzinfo=zone)
  offset = local.utcoffset()
  if offset is None:
    return ""
  total_seconds = int(offset.total_seconds())
  sign = "+" if total_seconds >= 0 else "-"
  total_seconds = abs(total_seconds)
  hours, remainder = divmod(total_seconds, 3600)
  minutes = remainder // 60
  offset_str = f"UTC{sign}{hours}" if minutes == 0 else f"UTC{sign}{hours}:{minutes:02d}"
  abbr = local.strftime("%Z") or timezone_name
  return f"{offset_str} ({abbr})"


def dst_transitions(timezone_name, year, month):
  """Return a dict of {day: 'DST starts'|'DST ends'} for transitions in a given month.

  Scans the month day-by-day comparing UTC offset; when the offset changes,
  the transition day is recorded with the appropriate label. The previous
  month's last day is used to detect transitions on the 1st of the month.
  """
  last_day = calendar.monthrange(year, month)[1]
  # Initialize from the last day of the previous month to catch transitions on the 1st
  prev_month_year, prev_month = (year, month - 1) if month > 1 else (year - 1, 12)
  prev_day = calendar.monthrange(prev_month_year, prev_month)[1]
  prev_offset = utc_offset_hours(timezone_name, Date(prev_month_year, prev_month, prev_day))
  transitions = {}
  for day in range(1, last_day + 1):
    hours = utc_offset_hours(timezone_name, Date(year, month, day))
    if hours != prev_offset:
      transitions[day] = "DST starts" if hours > prev_offset else "DST ends"
    prev_offset = hours
  return transitions


def to_hms(decimal_hours):
  """For durations and local civil times: split decimal hours to ``[h, m, s]``.

  Rounds to the nearest second with a full carry cascade: the result always
  satisfies ``0 <= m < 60`` and ``0 <= s < 60``, while ``h`` may be negative
  or exceed 24 (the callers' "hours past midnight" convention).
  """
  sign = -1 if decimal_hours < 0 else 1
  a = abs(decimal_hours)
  total_seconds = int(round(a * 3600))
  hours, rem = divmod(total_seconds, 3600)
  minutes, seconds = divmod(rem, 60)
  return [sign * hours, minutes, seconds]


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
  """Format a UT Julian day as local hours past ``civil_jd`` midnight.

  Pass the sunrise day's civil JD for Hindu-day endpoints, or the event's
  civil JD when a date label sits beside the time. Same 24:00+ rules as
  ``format_hms``.
  """
  return format_hms((jd_ut - civil_jd) * 24 + timezone_hours, show_seconds=show_seconds)


def format_local_hm(jd, timezone_name, anchor_civil=None, show_seconds=False):
  """Format UT ``jd`` as local ``HH:MM`` / ``HH:MM:SS`` past ``anchor_civil`` midnight.

  Default ``anchor_civil`` is the event's own local civil date. Pass a calendar
  cell's date so a next-morning event stays ``24:00+`` on that row.
  """
  if anchor_civil is None:
    anchor_civil = jd_to_local_civil_date(jd, timezone_name)
  civil_jd = gregorian_to_jd(anchor_civil)
  # datetime stops at year 1; earlier instants read the year-4 zone rules, as utc_offset_hours does.
  local = jd_to_local_datetime(max(jd, _JULIAN_DAY_AT_YEAR_4), timezone_name)
  tz_hours = local.utcoffset().total_seconds() / 3600.0
  return format_hms_from_jd(jd, civil_jd, tz_hours, show_seconds=show_seconds)


def hindu_day_civil(jd, timezone_name, sunrise_jd=None):
  """Civil date whose midnight is the 24:00+ origin for ``jd``.

  If ``sunrise_jd`` is given and ``jd`` is before it, return the previous
  civil date (``00:05`` formats as ``24:05``). Else the event's own civil date.
  """
  civil = jd_to_local_civil_date(jd, timezone_name)
  if sunrise_jd is not None and jd < sunrise_jd:
    return civil - 1
  return civil
