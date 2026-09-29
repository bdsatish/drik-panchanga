"""Lunar-year bounds for the PDF calendars: parser, resolver, pad, edge cases.

The rules under test (docs/PLAN.LUNAR-YEAR-CALENDARS.md):

* ``--start YYYY`` names the Gregorian year holding the year's Ugadi; the
  span runs from Ugadi's month through the month holding the last Phālguna
  day (12–14 whole months).
* PDFs and ICS accept years ``-3300 ... 3300``; a year with zero or two
  Ugadis is refused by name.
* The builders read a 32-day lead-in and one day past the span, not
  context months.
"""

import calendar
import unittest

from datetime_helper import Date
from generate_panchanga_calendar import (
  DEFAULT_FESTIVALS_PATH,
  PDF_YEAR_MAX,
  PDF_YEAR_MIN,
  lunar_year_boundaries,
  lunar_year_months,
  load_location,
  record_span,
  require_start_year,
)
from generate_monthly_calendar import collect_context

UJJAIN = "Ujjain, IN"

# Measured at Ujjain, Citra-paksha (plan §2).
FIXTURES = {
  2026: (Date(2026, 3, 20), Date(2027, 4, 6), (2026, 3), (2027, 4), 14),
  2027: (Date(2027, 4, 7), Date(2028, 3, 26), (2027, 4), (2028, 3), 12),
  2028: (Date(2028, 3, 27), Date(2029, 3, 15), (2028, 3), (2029, 3), 13),
  2029: (Date(2029, 3, 16), Date(2030, 4, 2), (2029, 3), (2030, 4), 14),
  2030: (Date(2030, 4, 3), Date(2031, 3, 23), (2030, 4), (2031, 3), 12),
}


class StartYearParserTests(unittest.TestCase):
  """Grammar cases for ``--start YYYY``."""

  def test_accepts_plain_and_bce_years(self):
    for text, expected in (("2026", 2026), ("0000", 0), ("0500", 500), ("-0500", -500), ("-500", -500),
                           ("-3300", -3300), ("3300", 3300)):
      with self.subTest(text=text):
        self.assertEqual(require_start_year(text), expected)

  def test_rejects_a_start_month(self):
    for text in ("2026-03", "-500-03", "0000-01"):
      with self.subTest(text=text), self.assertRaisesRegex(ValueError, "not YYYY-MM"):
        require_start_year(text)

  def test_rejects_years_outside_the_range(self):
    for text in ("-3301", "3301", "-5000", "9999"):
      with self.subTest(text=text), self.assertRaisesRegex(ValueError, r"-3300 to 3300"):
        require_start_year(text)


class ResolverFixtureTests(unittest.TestCase):
  """The five measured lunar years from the plan's table."""

  @classmethod
  def setUpClass(cls):
    cls.location = load_location(UJJAIN)

  def test_measured_spans(self):
    for year, (ugadi, last, first_month, end_month, count) in FIXTURES.items():
      with self.subTest(year=year):
        got_ugadi, got_last = lunar_year_boundaries(year, self.location, "citra")
        self.assertEqual(got_ugadi, ugadi)
        self.assertEqual(got_last, last)
        months = lunar_year_months(year, self.location)
        self.assertEqual(months[0], first_month)
        self.assertEqual(months[-1], end_month)
        self.assertEqual(len(months), count)

  def test_2029_starts_on_the_adhika_chaitra_ugadi(self):
    # Citra explicitly: a leaked global mode must not decide the answer.
    ugadi, _last = lunar_year_boundaries(2029, self.location, "citra")
    self.assertEqual(ugadi, Date(2029, 3, 16))

  def test_boundaries_do_not_depend_on_the_global_mode(self):
    # Regression: the resolver used to read whatever mode the previous test
    # left set, so a tropical leak made Citra fixtures resolve tropical dates.
    # Both windows are now scanned under one mode.
    import panchanga
    self.addCleanup(panchanga.set_coordinate_selection, "citra")
    panchanga.set_coordinate_selection("tropical")
    ugadi, last = lunar_year_boundaries(2029, self.location, "citra")
    self.assertEqual(ugadi, Date(2029, 3, 16))
    self.assertEqual(last, Date(2030, 4, 2))  # tropical's year ends 2030-03-04
    self.assertEqual(lunar_year_months(2029, self.location, "citra")[0], (2029, 3))

  def test_consecutive_years_share_the_ugadi_month(self):
    # Plan §2.2: the month of Ugadi YYYY+1 is the last month of year YYYY
    # and the first month of year YYYY+1.
    this = lunar_year_months(2026, self.location)
    nxt = lunar_year_months(2027, self.location)
    self.assertEqual(this[-1], nxt[0])

  def test_every_fixture_covers_ugadi_and_stops_before_next_ugadi(self):
    for year, (ugadi, last, _f, _e, _c) in FIXTURES.items():
      months = lunar_year_months(year, self.location)
      first_day = Date(months[0][0], months[0][1], 1)
      end_year, end_month = months[-1]
      last_day = Date(end_year, end_month, calendar.monthrange(end_year, end_month)[1])
      self.assertLessEqual(first_day, ugadi)
      self.assertLessEqual(last, last_day)
      # The whole printed span is 12–14 months and under 385 + pad days.
      self.assertTrue(12 <= len(months) <= 14)
      self.assertLessEqual(last_day - first_day, 365 + 31 + 31 + 3)
      self.assertLess(ugadi, last)


class RangeEdgeTests(unittest.TestCase):
  """-3300 and 3300 resolve; the first failing year at Ujjain is -3298."""

  MODES = ("citra", "revati", "rohini", "pushya", "mula", "krishnamurti", "raman", "tropical")

  def test_edges_resolve_for_every_mode(self):
    location = load_location(UJJAIN)
    for year in (PDF_YEAR_MIN, PDF_YEAR_MAX):
      for mode in self.MODES:
        with self.subTest(year=year, mode=mode):
          months = lunar_year_months(year, location, mode)
          self.assertTrue(12 <= len(months) <= 14)

  def test_revati_minus_3298_names_both_ugadis(self):
    location = load_location(UJJAIN)
    with self.assertRaises(ValueError) as caught:
      lunar_year_months(-3298, location, "revati")
    message = str(caught.exception)
    self.assertIn("two Ugadis", message)
    self.assertIn("-3298-01-11", message)
    self.assertIn("-3298-12-31", message)

  def test_revati_minus_3297_names_no_ugadi(self):
    location = load_location(UJJAIN)
    with self.assertRaises(ValueError) as caught:
      lunar_year_months(-3297, location, "revati")
    self.assertIn("no Ugadi", str(caught.exception))

  def test_tropical_never_fails_in_range(self):
    location = load_location(UJJAIN)
    for year in (-3300, -1500, 0, 1500, 3300):
      with self.subTest(year=year):
        months = lunar_year_months(year, location, "tropical")
        self.assertTrue(12 <= len(months) <= 14)


class PadTests(unittest.TestCase):
  """The 32/1-day pad replaces the old three-month context margin."""

  def test_solar_day_at_the_first_printed_day(self):
    # Kumbha saṅkrānti falls on 2026-02-12, so 2026-03-01 is solar day 17 —
    # right only because the records start 32 days earlier.
    location = load_location(UJJAIN)
    months = lunar_year_months(2026, location)
    context = collect_context(months, location, DEFAULT_FESTIVALS_PATH)
    raasi, solar_day, is_sankranti = context["solar_by_date"][Date(2026, 3, 1)]
    self.assertEqual((raasi, solar_day, is_sankranti), (11, 17, False))

  def test_parana_on_the_first_printed_day_keeps_its_upavasa(self):
    # 1905 prints April first: the pāraṇā on 1905-04-01 belongs to the
    # Ekādaśī upavāsa of 1905-03-31, two days before the printed span.
    location = load_location(UJJAIN)
    months = lunar_year_months(1905, location)
    self.assertEqual(months[0], (1905, 4))
    context = collect_context(months, location, DEFAULT_FESTIVALS_PATH)
    parana = context["ekadashi_parana"][Date(1905, 4, 1)]
    self.assertEqual(parana.upavasa_date, Date(1905, 3, 31))

  def test_record_span_width(self):
    # 32 days before the first printed day, one after the last.
    first, last = record_span([(2026, 3)])
    self.assertEqual(first, Date(2026, 1, 28))
    self.assertEqual(last, Date(2026, 4, 1))


class FooterFestivalTests(unittest.TestCase):
  """Printed days outside the lunar year still show their festivals (plan §2.2)."""

  def test_ugadi_prints_in_the_edge_months_of_the_2026_span(self):
    location = load_location(UJJAIN)
    months = lunar_year_months(2026, location)
    context = collect_context(months, location, DEFAULT_FESTIVALS_PATH)
    names = context["festival_names_by_date"]
    # 2026-03-20 is the year's own Ugadi; 2027-04-07 is next year's Ugadi,
    # printed because the span ends on a whole month boundary.
    self.assertIn("Ugadi", names.get(Date(2026, 3, 20), []))
    self.assertIn("Ugadi", names.get(Date(2027, 4, 7), []))


if __name__ == "__main__":
  unittest.main()
