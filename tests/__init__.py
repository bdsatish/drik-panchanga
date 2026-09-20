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
