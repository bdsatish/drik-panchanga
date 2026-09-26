"""Deep-BCE regression locks, back to 3300 BCE (astronomical year -3299).

Years are astronomical, as in ``Date``: year 0 is 1 BCE and -3299 is 3300 BCE.

Exact end times this far back move with the Swiss Ephemeris Delta T model
(about 23.6 h at 3300 BCE, and revised between releases), so these tests pin
what holds under any model: calendar arithmetic, the pre-standard clock,
Hindu-day invariants, and tithi / nakshatra / māsa numbers only on days whose
boundaries sit at least six hours from sunrise.
"""

import calendar
import re
import unittest

import panchanga
from datetime_helper import Date, format_hms_from_jd, format_local_hm, gregorian_to_jd
from generate_panchanga_calendar import load_location, place_for_date
from tests import require_swieph
from webapp.day_panchanga import compute_day_panchanga, parse_civil_date

DEEPEST = Date(-3299, 1, 1)
CITIES = ("Ujjain", "Helsinki", "New York City", "Sydney, AU", "Murmansk, RU")
TIME = re.compile(r"^-?\d{2,}:\d{2}:\d{2}$")


def sample_years():
  return range(DEEPEST.year, 1, 97)


class BceCalendarArithmeticTests(unittest.TestCase):
  """Date arithmetic and weekdays; no ephemeris needed."""

  def test_leap_days_follow_the_proleptic_gregorian_rule(self):
    for year in range(DEEPEST.year, 1):
      self.assertEqual(Date(year, 2, 28) + 1 == Date(year, 2, 29), calendar.isleap(year), msg=year)
    self.assertEqual(Date(-3200, 2, 28) + 1, Date(-3200, 2, 29))  # divisible by 400
    self.assertEqual(Date(-3100, 2, 28) + 1, Date(-3100, 3, 1))  # century, not by 400

  def test_year_lengths_match_julian_day_counts(self):
    for year in sample_years():
      start, end = Date(year, 1, 1), Date(year + 1, 1, 1)
      days = end - start
      self.assertEqual(days, gregorian_to_jd(end) - gregorian_to_jd(start), msg=year)
      self.assertEqual(days, 366 if calendar.isleap(year) else 365, msg=year)
      self.assertEqual(start + days, end, msg=year)

  def test_weekday_matches_vaara_and_runs_unbroken(self):
    for year in sample_years():
      day = Date(year, 12, 30)
      for _ in range(4):  # across the 31 Dec -> 1 Jan boundary
        self.assertEqual(day.weekday(), (panchanga.vaara(gregorian_to_jd(day)) + 6) % 7, msg=day)
        self.assertEqual((day + 1).weekday(), (day.weekday() + 1) % 7, msg=day)
        day += 1

  def test_kali_yuga_epoch(self):
    # 18 Feb 3102 BCE (Julian) = 23 Jan -3101 proleptic Gregorian, a Friday.
    epoch = Date(-3101, 1, 23)
    jd = gregorian_to_jd(epoch)
    self.assertEqual(jd, 588465.5)
    self.assertEqual(panchanga.ahargana(jd), 0)
    self.assertEqual(panchanga.vaara(jd), 5)
    self.assertEqual(epoch.weekday(), 4)
    self.assertEqual(panchanga.elapsed_year(jd, 1)[0], 0)

  def test_day_view_parses_deep_bce_dates(self):
    self.assertEqual(parse_civil_date("01/01/-3299"), Date(-3299, 1, 1))
    self.assertEqual(parse_civil_date("29/02/-3200"), Date(-3200, 2, 29))
    with self.assertRaises(ValueError):
      parse_civil_date("29/02/-3100")


class BceClockTests(unittest.TestCase):
  """Pre-standard clock: each place's own local mean time; no ephemeris needed."""

  def test_every_zone_reads_its_own_mean_time(self):
    for city in CITIES:
      location = load_location(city)
      for civil in (DEEPEST, Date(-3101, 1, 23), Date(-1, 12, 31)):
        with self.subTest(city=city, civil=civil):
          self.assertAlmostEqual(place_for_date(location, civil).timezone, location.longitude / 15, places=9)

  def test_local_mean_noon_formats_as_noon(self):
    for city in CITIES:
      location = load_location(city)
      for year in sample_years():
        civil = Date(year, 6, 15)
        noon_ut = gregorian_to_jd(civil) + (12 - location.longitude / 15) / 24
        with self.subTest(city=city, civil=civil):
          self.assertEqual(
            format_local_hm(noon_ut, location.timezone_name, anchor_civil=civil, show_seconds=True,
                            longitude=location.longitude), "12:00:00")


class BceHinduDayInvariantTests(unittest.TestCase):
  """Sunrise-anchored days stay well-formed back to 3300 BCE, polar days included."""

  CASES = (
    ("Ujjain", Date(-3299, 6, 1)),
    ("Helsinki", Date(-3101, 1, 1)),
    ("New York City", Date(-1500, 9, 1)),
    ("Sydney, AU", Date(-500, 1, 1)),
    ("Murmansk, RU", Date(-3299, 6, 1)),  # midnight sun
    ("Murmansk, RU", Date(-3299, 12, 1)),  # polar night
  )

  @classmethod
  def setUpClass(cls):
    require_swieph(gregorian_to_jd(DEEPEST))
    panchanga.set_coordinate_selection("citra")

  def test_a_month_of_days(self):
    for city, first in self.CASES:
      location = load_location(city)
      previous = None
      for offset in range(30):
        civil = first + offset
        place = place_for_date(location, civil)
        jd = gregorian_to_jd(civil)
        midnight = jd - place.timezone / 24
        rise = panchanga.sunrise(jd, place)
        tithi = panchanga.tithi(jd, place)
        nakshatra = panchanga.nakshatra(jd, place)
        karana = panchanga.karana(jd, place)
        with self.subTest(city=city, civil=civil):
          self.assertTrue(midnight <= rise < midnight + 1)
          self.assertTrue(1 <= tithi[0] <= 30 and 1 <= nakshatra[0] <= 27)
          self.assertTrue(rise < tithi[1] < rise + 2 and rise < nakshatra[1] < rise + 2)
          if len(tithi) == 4:
            self.assertLess(tithi[1], tithi[3])
          self.assertIn(karana[0], (2 * tithi[0] - 1, 2 * tithi[0]))
          if previous is not None:
            prev_rise, prev_tithi, prev_nakshatra = previous
            self.assertAlmostEqual((rise - prev_rise) * 24, 24, delta=2)
            self.assertIn((tithi[0] - prev_tithi) % 30, (0, 1, 2))
            self.assertIn((nakshatra[0] - prev_nakshatra) % 27, (0, 1, 2))
        previous = rise, tithi[0], nakshatra[0]

  def test_lunar_months_advance_in_order_through_a_year(self):
    location = load_location("Ujjain")
    months = []
    for offset in range(0, 400, 7):  # weekly: a lunar month cannot be skipped
      civil = DEEPEST + offset
      place = place_for_date(location, civil)
      months.append(tuple(panchanga.masa(gregorian_to_jd(civil), place, amanta=True)))
    changes = 0
    for (masa, adhika), (next_masa, next_adhika) in zip(months, months[1:]):
      if (masa, adhika) == (next_masa, next_adhika):
        continue
      changes += 1
      if adhika:  # adhika is followed by its nija month of the same name
        self.assertEqual((next_masa, next_adhika), (masa, False))
      else:
        self.assertEqual(next_masa, masa % 12 + 1)
    self.assertGreaterEqual(changes, 12)


class BceGoldenNumberTests(unittest.TestCase):
  """Numbers at Ujjain sunrise on days chosen far from every boundary.

  On each day both tithi and nakshatra boundaries sit at least 6.4 h from
  sunrise, and the flanking new moons at least 2 degrees inside a solar sign,
  so a Delta T revision of an hour or two cannot flip them.
  """

  GOLDENS = (
    # date, tithi, nakshatra, amānta māsa, adhika, samvatsara, vaara
    (Date(-3299, 1, 3), 12, 9, 12, False, 6, 4),
    (Date(-3101, 2, 1), 10, 9, 1, False, 27, 0),
    (Date(-2500, 5, 15), 4, 10, 4, False, 35, 2),
    (Date(-1499, 3, 5), 11, 11, 1, False, 27, 6),
    (Date(-1000, 10, 19), 27, 14, 8, False, 52, 0),
    (Date(-500, 1, 4), 8, 2, 11, False, 17, 4),
    (Date(-1, 6, 12), 12, 17, 4, False, 43, 6),
  )

  @classmethod
  def setUpClass(cls):
    require_swieph(gregorian_to_jd(DEEPEST))

  def setUp(self):
    panchanga.set_coordinate_selection("citra")
    panchanga.set_nakshatra_system("equal")

  def test_numbers(self):
    location = load_location("Ujjain")
    for civil, tithi, nakshatra, masa, adhika, samvatsara, vaara in self.GOLDENS:
      place = place_for_date(location, civil)
      jd = gregorian_to_jd(civil)
      with self.subTest(civil=civil):
        self.assertEqual(panchanga.tithi(jd, place)[0], tithi)
        self.assertEqual(panchanga.nakshatra(jd, place)[0], nakshatra)
        self.assertEqual(panchanga.masa(jd, place, amanta=True), [masa, adhika])
        self.assertEqual(panchanga.samvatsara(jd, masa), samvatsara)
        self.assertEqual(panchanga.vaara(jd), vaara)


class BceDayViewSweepTests(unittest.TestCase):
  """The web day view answers every BCE day in full (it once raised on year < 1)."""

  DATES = ("15/06/-3299", "15/12/-3299", "23/01/-3101", "29/02/-3200", "21/03/-2500", "22/12/-1500", "30/01/-500",
           "31/12/-1", "29/02/0")

  @classmethod
  def setUpClass(cls):
    require_swieph(gregorian_to_jd(DEEPEST))

  def assertDayIsComplete(self, data, city, text):
    location = load_location(city)
    civil = parse_civil_date(text)
    jd = gregorian_to_jd(civil)
    sunrise = panchanga.sunrise(jd, place_for_date(location, civil))
    self.assertEqual(data["sunrise"], format_hms_from_jd(sunrise, jd, location.longitude / 15, show_seconds=True))
    for key in ("sunrise", "sunset", "day_duration"):
      self.assertRegex(data[key], TIME)
    for key in ("tithi", "nakshatra", "yoga", "karana"):
      self.assertTrue(data[key])
      for segment in data[key]:
        self.assertTrue(segment["name"])
        self.assertRegex(segment["ends"], TIME)
    for interval in [data["rahu_kala"], data["pratah_sandhya"], *data["durmuhurta"], *data["varjyam"]]:
      self.assertRegex(interval["start"], TIME)
      self.assertRegex(interval["end"], TIME)
    for key in ("moonrise", "moonset"):
      if data[key] is not None:
        self.assertRegex(data[key], TIME)
    for key in ("masa", "samvatsara", "samvatsara_north", "vaara", "rtu", "drik_rtu"):
      self.assertTrue(data[key])

  def test_every_city_and_date(self):
    for city in CITIES:
      for text in self.DATES:
        with self.subTest(city=city, date=text):
          self.assertDayIsComplete(compute_day_panchanga(city, text), city, text)

  def test_other_modes(self):
    purnimanta = compute_day_panchanga("Ujjain", "23/01/-3101", month_system="purnimanta")
    self.assertDayIsComplete(purnimanta, "Ujjain", "23/01/-3101")
    tropical = compute_day_panchanga("Ujjain", "23/01/-3101", coordinate_selection="tropical")
    self.assertDayIsComplete(tropical, "Ujjain", "23/01/-3101")
    self.assertIsNone(tropical["ayanamsa_degrees"])


if __name__ == "__main__":
  unittest.main()
