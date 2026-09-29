"""BCE/CE boundary locks for the proleptic-Gregorian year-0 path.

``datetime_helper.Date`` uses astronomical year numbering on the proleptic
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
from pathlib import Path
from tempfile import TemporaryDirectory

import swisseph as swe

import panchanga
from datetime_helper import (Date, dst_transitions, format_local_hm, format_utc_offset, gregorian_to_jd,
                             jd_to_local_civil_date, local_range_jds, utc_offset_hours)
from tests import local_hms, require_swieph
from panchanga import (Place, ahargana, elapsed_year, lunar_longitude, reset_ayanamsa_mode, set_chosen_ayanamsa,
                       set_nakshatra_system, solar_longitude, vaara)
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

  def test_pre_epoch_uses_floor_not_truncation(self):
    # Regression for int() truncation toward zero: before the epoch
    # (-0.5 < x < 0) must be -1, not 0. 588465.5 is the Kali epoch
    # (ahar == 0); a half-day before it, ahar == -0.5 and with
    # maasa 12 the fractional year x is in (-1, 0).
    jd_before = 588465.0
    jd_epoch = 588465.5
    # Raw elapsed-year fraction with a late-year masa is negative just
    # before the epoch; floor and int differ exactly there.
    self.assertEqual(elapsed_year(jd_before, 12)[0], -1)
    self.assertEqual(elapsed_year(jd_epoch, 1)[0], 0)
    self.assertLess(elapsed_year(jd_before, 12)[0], elapsed_year(jd_epoch, 1)[0])
    # Ahargana day count is the same expired-day idea; -0.5 days is
    # day -1, not day 0, so floor is required as well.
    import math
    self.assertEqual(math.floor(ahargana(jd_before)), -1)
    self.assertEqual(math.floor(ahargana(jd_epoch)), 0)
    self.assertEqual(math.floor(ahargana(jd_epoch + 1.0)), 1)
    # Sanity: deep-BCE rows from the sweep must also use floor.
    self.assertEqual(elapsed_year(gregorian_to_jd(Date(-3102, 3, 22)), 2)[0], -1)
    self.assertEqual(elapsed_year(gregorian_to_jd(Date(-3104, 4, 1)), 3)[0], -3)


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

  The tithi/nakshatra NUMBER is asserted exactly; the end TIME is asserted
  within ``TIME_TOLERANCE_SECONDS``. Delta-T is a model, and its coefficient
  tables differ between ephemeris file sets (a fresh ``ensure_ephe.sh``
  download carries 185 .se1 files against a stale local 150), which shifts
  these BCE end times by a few seconds. At year 1 CE delta-T is ~10550 s, so
  a small model difference moves the interpolated end time directly. A
  tolerance well under a minute still catches a real regression, which would
  move minutes or change the number.
  """

  TIME_TOLERANCE_SECONDS = 30

  def assertTiming(self, actual, jd, expected_number, expected_hms, label):
    """Assert a ``[number, end_ut]`` answer: number exact, local end time within tolerance."""
    self.assertEqual(actual[0], expected_number, f"{label} number changed")
    hms = local_hms(actual[1], jd, UJJAIN)
    actual_seconds = hms[0] * 3600 + hms[1] * 60 + hms[2]
    expected_seconds = expected_hms[0] * 3600 + expected_hms[1] * 60 + expected_hms[2]
    self.assertLessEqual(abs(actual_seconds - expected_seconds), self.TIME_TOLERANCE_SECONDS,
                         f"{label} end time moved: {hms} vs {expected_hms} (>{self.TIME_TOLERANCE_SECONDS}s)")

  def test_nakshatra_at_june_15_100_bce(self):
    jd = gregorian_to_jd(Date(-100, 6, 15))
    require_swieph(jd)
    # Krittika, ends ~15:09:38 local.
    self.assertTiming(panchanga.nakshatra(jd, UJJAIN), jd, 8, [15, 9, 38], "100 BCE nakshatra")

  def test_tithi_at_june_15_1_ce(self):
    jd = gregorian_to_jd(Date(-1, 6, 15))
    require_swieph(jd)
    # Pournima (15), ends ~21:21:56 local.
    self.assertTiming(panchanga.tithi(jd, UJJAIN), jd, 15, [21, 21, 56], "1 BCE tithi")

  def test_skipped_tithi_on_boundary_day(self):
    # 15 Jun 1 BCE (year 0): tithi 26 ends ~05:59:42 and the skipped
    # tithi 27 ends ~26:59:49 (past midnight) the same day, so the answer
    # carries the leap tithi. A one-day JD jump would land on another tithi.
    jd = gregorian_to_jd(Date(0, 6, 15))
    require_swieph(jd)
    answer = panchanga.tithi(jd, UJJAIN)
    self.assertEqual(len(answer), 4, f"expected a skipped tithi, got {answer}")
    self.assertTiming(answer[:2], jd, 26, [5, 59, 42], "1 BCE tithi 26")
    self.assertTiming([answer[2], answer[3]], jd, 27, [26, 59, 49], "1 BCE skipped tithi 27")

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
        hours = local_hms(panchanga.sunrise(jd, UJJAIN), jd, UJJAIN)[0]
        self.assertTrue(4 <= hours <= 9)


class PlaceForDateProxyTests(BoundaryTestCase):
  """BCE dates reuse the year-4 tzdb era, where longitude/15 replaces the seat's LMT."""

  def test_bce_proxy_matches_year_four(self):
    bce = place_for_date(KOLKATA, Date(0, 6, 15))
    ce = place_for_date(KOLKATA, Date(4, 6, 15))
    self.assertEqual(bce.latitude, ce.latitude)
    self.assertEqual(bce.longitude, ce.longitude)
    self.assertAlmostEqual(bce.timezone, ce.timezone, places=9)

  def test_bce_proxy_is_not_modern_offset(self):
    # Year 4 Asia/Kolkata is the pre-standardisation LMT era; the year-2000
    # proxy would give standard-time +5:30.
    self.assertNotAlmostEqual(place_for_date(KOLKATA, Date(0, 6, 15)).timezone, 5.5, places=2)

  def test_pre_modern_uses_longitude_meridian(self):
    # In the LMT era the tzdb offset is the seat city's (+5:53:28 for
    # Asia/Kolkata), not the observer's; place_for_date substitutes the
    # observer's own local mean solar time, longitude/15.
    place = place_for_date(KOLKATA, Date(0, 6, 15))
    self.assertAlmostEqual(place.timezone, 75.7864 / 15.0, places=9)

  def test_negative_year_does_not_raise(self):
    place = place_for_date(KOLKATA, Date(-100, 6, 15))
    self.assertAlmostEqual(place.timezone, place_for_date(KOLKATA, Date(4, 6, 15)).timezone, places=9)

  def test_bce_leap_day_does_not_raise(self):
    # Regression: the proxy year was 1, which is not a leap year, so any BCE
    # 29 February hit datetime(1, 2, 29) -> ValueError. Proleptic-Gregorian
    # BCE leap years (year 0 = 1 BCE, -4, -8, -400, ...) are valid dates that
    # swe.julday accepts. Year 4 is the earliest leap year and fixes this.
    for year in (0, -4, -8, -400):
      with self.subTest(year=year):
        place = place_for_date(KOLKATA, Date(year, 2, 29))
        self.assertAlmostEqual(place.timezone, place_for_date(KOLKATA, Date(4, 6, 15)).timezone, places=9)
        self.assertAlmostEqual(place.timezone, 75.7864 / 15.0, places=9)  # longitude/15, not modern +5:30

  def test_bce_leap_day_matches_its_own_year_offset(self):
    # The proxy year shifts the tz lookup date, but within early-CE tzdb rules
    # the offset is flat, so a BCE leap day gets the same LMT as any other day.
    feb = place_for_date(KOLKATA, Date(-4, 2, 29))
    jun = place_for_date(KOLKATA, Date(-4, 6, 15))
    self.assertAlmostEqual(feb.timezone, jun.timezone, places=9)

  def test_early_ce_years_are_clamped_to_year_four(self):
    # The clamp is max(4, year), not a year > 0 branch, so whatever the reason
    # for the floor it applies uniformly. Years 1-3 give the same tzdb offset
    # as year 4 in every zone, so this changes no output, but it pins the
    # intent: no year is special-cased.
    reference = place_for_date(KOLKATA, Date(4, 6, 15)).timezone
    for year in (1, 2, 3, 4):
      with self.subTest(year=year):
        self.assertAlmostEqual(place_for_date(KOLKATA, Date(year, 6, 15)).timezone, reference, places=9)

  def test_ce_years_after_the_floor_are_not_clamped(self):
    # Year 5 onwards uses its own year, so real tz history is still honoured.
    self.assertEqual(place_for_date(KOLKATA, Date(2026, 6, 15)).timezone, 5.5)

  def test_pre_standard_ce_uses_longitude_meridian(self):
    # The LMT era is not only BCE: Asia/Kolkata stays LMT until 1854.
    self.assertAlmostEqual(place_for_date(KOLKATA, Date(1800, 6, 15)).timezone, 75.7864 / 15.0, places=9)

  def test_standard_time_history_is_untouched(self):
    # Only tzdb's LMT era moves to the observer: Howrah and Madras Mean Time
    # (HMT 1854-1870, MMT 1870-1941) were real civil time and stay as they are.
    self.assertAlmostEqual(place_for_date(KOLKATA, Date(1860, 6, 15)).timezone, 5 + 53 / 60 + 20 / 3600, places=9)
    self.assertAlmostEqual(place_for_date(KOLKATA, Date(1900, 6, 15)).timezone, 5 + 21 / 60 + 10 / 3600, places=9)


class LongitudeMeridianHelperTests(unittest.TestCase):
  """``longitude=`` on the datetime_helper conversions: LMT eras read longitude/15."""

  LONGITUDE = 75.7864  # Ujjain

  def test_round_trip_in_the_lmt_era(self):
    jd = gregorian_to_jd(Date(1800, 3, 1)) + (23 + 50 / 60 - self.LONGITUDE / 15) / 24
    self.assertEqual(
      format_local_hm(jd, "Asia/Kolkata", anchor_civil=Date(1800, 3, 1), show_seconds=True, longitude=self.LONGITUDE),
      "23:50:00")
    self.assertEqual(jd_to_local_civil_date(jd, "Asia/Kolkata", self.LONGITUDE), Date(1800, 3, 1))

  def test_month_range_starts_at_local_mean_midnight(self):
    start, _end = local_range_jds(1800, 3, 1800, 3, "Asia/Kolkata", self.LONGITUDE)
    self.assertAlmostEqual(start, gregorian_to_jd(Date(1800, 3, 1)) - self.LONGITUDE / 15 / 24, places=9)
    self.assertEqual(local_range_jds(2026, 3, 2026, 3, "Asia/Kolkata", self.LONGITUDE),
                     local_range_jds(2026, 3, 2026, 3, "Asia/Kolkata"))

  def test_label_names_lmt_at_the_observer_offset(self):
    self.assertEqual(format_utc_offset("Asia/Kolkata", 1800, 6, longitude=self.LONGITUDE), "UTC+5:03 (LMT)")
    self.assertEqual(format_utc_offset("Asia/Kolkata", 2026, 6, longitude=self.LONGITUDE), "UTC+5:30 (IST)")

  def test_dst_label_follows_the_observers_clock(self):
    # 28 Jun 1854, LMT -> HMT: Kolkata's clock moves back 8 s, Ujjain's forward 50 min.
    self.assertEqual(dst_transitions("Asia/Kolkata", 1854, 6), {28: "DST ends"})
    self.assertEqual(dst_transitions("Asia/Kolkata", 1854, 6, self.LONGITUDE), {28: "DST starts"})

  def test_dst_zones_keep_their_rules_after_lmt(self):
    self.assertEqual(utc_offset_hours("Europe/Helsinki", Date(2026, 7, 15), longitude=24.94), 3.0)
    self.assertEqual(utc_offset_hours("Europe/Helsinki", Date(2026, 1, 15), longitude=24.94), 2.0)
    self.assertAlmostEqual(utc_offset_hours("Europe/Helsinki", Date(1800, 7, 15), longitude=24.94), 24.94 / 15,
                           places=9)

  def test_fixed_offsets_ignore_longitude(self):
    self.assertEqual(utc_offset_hours("UTC+5:30", Date(-500, 1, 30), longitude=75.78), 5.5)


class BcePdfSmokeTests(BoundaryTestCase):
  """Both PDFs build for a deep-BCE lunar year (regression: datetime year floor)."""

  def test_annual_pdf_builds_at_year_minus_500(self):
    import generate_panchanga_calendar as annual
    from generate_panchanga_calendar import load_location, lunar_year_months
    location = load_location("Ujjain")
    months = lunar_year_months(-500, location)
    with TemporaryDirectory() as directory:
      output = Path(directory) / "bce.pdf"
      annual.build_pdf(location, months, output)
      self.assertTrue(output.stat().st_size > 0)

  def test_monthly_pdf_builds_at_year_minus_500(self):
    import generate_monthly_calendar as monthly
    from generate_panchanga_calendar import load_location, lunar_year_months
    location = load_location("Ujjain")
    months = lunar_year_months(-500, location)
    with TemporaryDirectory() as directory:
      output = Path(directory) / "bce.pdf"
      monthly.build_monthly_pdf(location, months, output)
      self.assertTrue(output.stat().st_size > 0)

  def test_civil_date_conversion_reaches_deep_bce(self):
    # The festival solstice path converts a -500 solstice JD straight to a
    # civil Date; datetime.fromtimestamp cannot represent that instant.
    solstice_jd = gregorian_to_jd(Date(-500, 12, 1)) + 20
    civil = jd_to_local_civil_date(solstice_jd, "Asia/Kolkata")
    self.assertEqual((civil.year, civil.month), (-500, 12))

  def test_local_range_reaches_deep_bce(self):
    start, end = local_range_jds(-500, 3, -499, 4, "Asia/Kolkata", 75.7864)
    self.assertAlmostEqual(start, gregorian_to_jd(Date(-500, 3, 1)) - 75.7864 / 15 / 24, places=9)
    self.assertGreater(end, start)


if __name__ == "__main__":
  unittest.main()
