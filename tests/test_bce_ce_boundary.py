"""BCE/CE boundary locks for the proleptic-Gregorian year-0 path.

``panchanga.Date`` uses astronomical year numbering on the proleptic
Gregorian calendar: year 0 is 1 BCE, year -1 is 2 BCE, and there is no
missing "year zero" in the Julian Day sequence. Python ``datetime``
rejects year <= 0, so calendar code substitutes a CE proxy year
(``place_for_date`` in ``generate_panchanga_calendar.py``); these tests
pin that substitution and the underlying ephemeris continuity so neither
regresses silently.

Conventions assumed here (not asserted as history): dates are proleptic
Gregorian, not the historical Julian calendar actually in civil use in
1 BCE / 1 CE.

The ephemeris goldens require Swiss Ephemeris ``.se1`` files (present in
CI via ``scripts/ensure_ephe.sh``). They skip -- rather than pass
against the coarse built-in Moshier fallback -- when ``.se1`` data is
absent, checked via the ``FLG_SWIEPH`` return flag.
"""

import unittest

import swisseph as swe

import panchanga
from panchanga import (Date, Place, elapsed_year, gregorian_to_jd, local_time_to_jdut1, lunar_longitude,
                       reset_ayanamsa_mode, set_ayanamsa_mode, set_chosen_ayanamsa, set_nakshatra_system,
                       solar_longitude, vaara)
from generate_panchanga_calendar import Location, place_for_date

UJJAIN = Place(23.1765, 75.7864, +5.5)
KOLKATA = Location("Ujjain", 23.1765, 75.7864, "Asia/Kolkata")
GOLDEN_TOLERANCE_DEG = 0.01  # 36 arcsec: tight vs Moshier drift, loose vs swe version noise


class BoundaryTestCase(unittest.TestCase):
  """Pin library globals so order vs other test modules cannot leak in."""

  def setUp(self):
    set_chosen_ayanamsa("citra")
    set_nakshatra_system("equal")

  def tearDown(self):
    set_nakshatra_system("equal")
    reset_ayanamsa_mode()


def require_swieph(jd):
  """Skip the test unless ``.se1`` ephemeris data backs this Julian Day.

  Without ``.se1`` files, pyswisseph either flags the Moshier fallback in
  the retflag or raises outright for far-past dates (the built-in Moshier
  ephemeris is only valid for the modern era); both mean "skip", not pass.
  """
  set_ayanamsa_mode()
  try:
    retflag = swe.calc_ut(jd, swe.SUN, flags=swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[1]
  except swe.Error as err:
    raise unittest.SkipTest(f"Swiss Ephemeris .se1 files not available; skipping .se1 golden ({err})")
  finally:
    reset_ayanamsa_mode()
  if not retflag & swe.FLG_SWIEPH:
    raise unittest.SkipTest("Swiss Ephemeris .se1 files not available; skipping .se1 golden")


class JulianDayContinuityTests(BoundaryTestCase):
  """The JD sequence has no gap or overlap at year 0 / year 1."""

  def test_midnight_steps_exactly_one_day(self):
    self.assertEqual(gregorian_to_jd(Date(0, 12, 31)) + 1.0, gregorian_to_jd(Date(1, 1, 1)))

  def test_revjul_roundtrips_year_zero(self):
    self.assertEqual(swe.revjul(gregorian_to_jd(Date(0, 6, 15)), swe.GREG_CAL), (0, 6, 15, 0.0))

  def test_year_zero_is_a_leap_year(self):
    # Proleptic Gregorian leap rule: 0 divisible by 400 -> 366 days;
    # year -1 (2 BCE) is a common year.
    self.assertEqual(gregorian_to_jd(Date(1, 1, 1)) - gregorian_to_jd(Date(0, 1, 1)), 366.0)
    self.assertEqual(gregorian_to_jd(Date(0, 1, 1)) - gregorian_to_jd(Date(-1, 1, 1)), 365.0)

  def test_jd_paths_agree_across_boundary(self):
    # gregorian_to_jd (swe.julday) and local_time_to_jdut1 (swe.utc_to_jd)
    # must differ by exactly the timezone offset, even for year <= 0.
    for year in (1, 0, -1, -100):
      with self.subTest(year=year):
        jd_midnight_utc = gregorian_to_jd(Date(year, 1, 1))
        jd_local_midnight = local_time_to_jdut1(year, 1, 1, 0, 0, 0, timezone=5.5)
        self.assertAlmostEqual((jd_midnight_utc - jd_local_midnight) * 24, 5.5, places=6)


class WeekdayContinuityTests(BoundaryTestCase):
  """Vaara runs unbroken across 31 Dec 1 BCE -> 1 Jan 1 CE (Sat -> Sun -> Mon)."""

  def test_vaara_sequence(self):
    expected = [6, 0, 1, 2]  # Saturday, Sunday, Monday, Tuesday
    for (year, month, day), want in zip([(0, 12, 30), (0, 12, 31), (1, 1, 1), (1, 1, 2)], expected):
      with self.subTest(year=year, month=month, day=day):
        self.assertEqual(vaara(gregorian_to_jd(Date(year, month, day))), want)


class ElapsedYearTests(BoundaryTestCase):
  """Kali-year reckoning is monotonic across the boundary, gaining one year."""

  def test_kali_increments_by_one(self):
    kali_bce = elapsed_year(gregorian_to_jd(Date(0, 1, 1)), 1)[0]
    kali_ce = elapsed_year(gregorian_to_jd(Date(1, 1, 1)), 1)[0]
    self.assertEqual(kali_ce - kali_bce, 1)

  def test_kali_non_decreasing_day_by_day(self):
    kalis = [
      elapsed_year(gregorian_to_jd(Date(y, m, d)), 1)[0] for y, m, d in [(0, 12, 30), (0, 12, 31), (1, 1, 1), (1, 1, 2)]
    ]
    self.assertEqual(sorted(kalis), kalis)


class Se1GoldenTests(BoundaryTestCase):
  """Sidereal longitudes at local noon, 1 Jan 1 CE, Ujjain (citra ayanamsa)."""

  # gregorian_to_jd(Date(1, 1, 1), 12 - 5.5): noon IST as a JD(UT).
  NOON_JD = 1721425.7708333333

  def test_solar_longitude(self):
    require_swieph(self.NOON_JD)
    self.assertAlmostEqual(solar_longitude(self.NOON_JD), 285.6243, delta=GOLDEN_TOLERANCE_DEG)

  def test_lunar_longitude(self):
    require_swieph(self.NOON_JD)
    self.assertAlmostEqual(lunar_longitude(self.NOON_JD), 169.8393, delta=GOLDEN_TOLERANCE_DEG)

  def test_golden_jd_matches_constructor(self):
    # The hardcoded golden JD above must stay in sync with gregorian_to_jd.
    self.assertAlmostEqual(gregorian_to_jd(Date(1, 1, 1), 12 - 5.5), self.NOON_JD, places=6)


class TithiNakshatraBceTests(BoundaryTestCase):
  """Tithi and nakshatra for year < 0, pinned to real .se1 ephemeris values.

  tithi/nakshatra take only a Julian Day, so a regression here would have
to come from the JD/celestial pipeline itself, not from civil-date code.
  These goldens still matter: they lock the whole chain (JD -> rise_trans
  -> longitudes -> interpolation) at negative-year JDNs.
  """

  def test_nakshatra_at_june_15_100_bce(self):
    jd = gregorian_to_jd(Date(-100, 6, 15))
    require_swieph(jd)
    # Krittika, ends 15:09:38 local.
    self.assertEqual(panchanga.nakshatra(jd, UJJAIN), [8, [15, 9, 38]])

  def test_tithi_at_june_15_1_ce(self):
    jd = gregorian_to_jd(Date(-1, 6, 15))
    require_swieph(jd)
    # Pournima (15), ends 21:21:56 local.
    self.assertEqual(panchanga.tithi(jd, UJJAIN), [15, [21, 21, 56]])

  def test_skipped_tithi_on_boundary_day(self):
    # 15 Jun 1 BCE (year 0): tithi 26 ends 05:59:42 and the skipped
    # tithi 27 ends 26:59:49 (past midnight) the same day, so the answer
    # carries the leap tithi. A one-day JD jump would land on another tithi.
    jd = gregorian_to_jd(Date(0, 6, 15))
    require_swieph(jd)
    self.assertEqual(panchanga.tithi(jd, UJJAIN), [26, [5, 59, 42], 27, [26, 59, 49]])

  def test_deep_bce_sanity(self):
    # Range/shape checks only (no minute-precision goldens this far back,
    # where pyswisseph version changes are most likely to shift seconds).
    for year in (-1000, -3000, -5000):
      with self.subTest(year=year):
        jd = gregorian_to_jd(Date(year, 6, 15))
        require_swieph(jd)
        tithi_answer = panchanga.tithi(jd, UJJAIN)
        self.assertTrue(1 <= tithi_answer[0] <= 30)
        self.assertEqual(len(tithi_answer) % 2, 0)
        nakshatra_answer = panchanga.nakshatra(jd, UJJAIN)
        self.assertTrue(1 <= nakshatra_answer[0] <= 27)
        hours = panchanga.sunrise(jd, UJJAIN)[1][0]
        self.assertTrue(4 <= hours <= 9)


class PlaceForDateProxyTests(BoundaryTestCase):
  """BCE dates reuse the year-1 tzdb offset (historical LMT), not a modern one."""

  def test_bce_proxy_matches_year_one(self):
    bce = place_for_date(KOLKATA, Date(0, 6, 15))
    ce = place_for_date(KOLKATA, Date(1, 6, 15))
    self.assertEqual(bce.latitude, ce.latitude)
    self.assertEqual(bce.longitude, ce.longitude)
    self.assertAlmostEqual(bce.timezone, ce.timezone, places=9)

  def test_bce_proxy_is_not_modern_offset(self):
    # Year 1 Asia/Kolkata keeps the pre-standardisation local mean time
    # offset (~+5:53); the year-2000 proxy would give standard-time +5:30.
    self.assertNotAlmostEqual(place_for_date(KOLKATA, Date(0, 6, 15)).timezone, 5.5, places=2)

  def test_negative_year_does_not_raise(self):
    place = place_for_date(KOLKATA, Date(-100, 6, 15))
    self.assertAlmostEqual(place.timezone, place_for_date(KOLKATA, Date(1, 6, 15)).timezone, places=9)


if __name__ == "__main__":
  unittest.main()
