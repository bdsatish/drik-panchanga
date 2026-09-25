# Unit tests for the calendar library and web helpers.
"""Test package.

Print an ephemeris fingerprint once per session so CI logs record which
``.se1`` data set produced the numbers. Swiss Ephemeris values depend on the
data files as well as the library, and upstream re-cuts them periodically: a
2026-05 revision changed every shipped file and moved a year-1 CE longitude by
0.0004 degrees, which shifted BCE tithi end times by seconds between a stale
local set and CI. Recording the fingerprint makes that kind of drift
diagnosable instead of mysterious.
"""

import sys

import panchanga
from datetime_helper import to_hms


def local_hms(jd_ut, jd, place):
  """``[h, m, s]`` of UT ``jd_ut`` past ``jd``'s civil midnight at ``place.timezone``."""
  return to_hms((jd_ut - jd) * 24 + place.timezone)


def local_ends(result, jd, place):
  """``tithi``-style ``[n, end, ...]`` with each UT end as ``local_hms``."""
  return [local_hms(value, jd, place) if index % 2 else value for index, value in enumerate(result)]


def local_intervals(intervals, jd, place):
  """``[[start, end], ...]`` UT pairs as ``local_hms`` pairs."""
  return [[local_hms(start, jd, place), local_hms(end, jd, place)] for start, end in intervals]


def _report_ephemeris():
  """Print the ephemeris fingerprint to stderr; never raise."""
  try:
    fingerprint = panchanga.ephemeris_fingerprint()
  except Exception as error:  # pragma: no cover - diagnostics must not break tests
    print(f"ephemeris: unavailable ({error})", file=sys.stderr)
    return
  print(
    "ephemeris: {version} | {se1_files} .se1 in {data_dir} | "
    "delta-T year 1 CE {deltat_seconds_year_1_ce}s".format(**fingerprint),
    file=sys.stderr,
  )


_report_ephemeris()
