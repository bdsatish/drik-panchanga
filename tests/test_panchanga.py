"""Unit tests for core panchanga computations.

Extracted from the inline ``_tests()`` functions that used to live at the
bottom of ``panchanga.py``.
"""

import unittest
import swisseph as swe

from panchanga import (Date, Place, gregorian_to_jd, from_dms,
    sunrise, sunset, moonrise, moonset, tithi, nakshatra, nakshatra_pada,
    yoga, karana, vaara, masa, varjyam, ascendant, navamsa,
    set_nakshatra_system, set_chosen_ayanamsa, reset_ayanamsa_mode)


bangalore = Place(12.972, 77.594, +5.5)
shillong = Place(25.569, 91.883, +5.5)
helsinki = Place(60.17, 24.935, +2.0)

date1 = gregorian_to_jd(Date(2009, 7, 15))
date2 = gregorian_to_jd(Date(2013, 1, 18))
date3 = gregorian_to_jd(Date(1985, 6, 9))
date4 = gregorian_to_jd(Date(2009, 6, 21))


class PanchangaTestCase(unittest.TestCase):
    """Pin library globals so order vs other test modules cannot leak in."""

    def setUp(self):
        set_chosen_ayanamsa("citra")
        set_nakshatra_system("equal")

    def tearDown(self):
        set_nakshatra_system("equal")
        reset_ayanamsa_mode()


class SunriseSetTests(PanchangaTestCase):
    """Sunrise, sunset, moonrise, moonset, vaara, karana."""

    def test_moonrise(self):
        self.assertEqual(moonrise(date2, bangalore), [11, 35, 6])

    def test_moonset(self):
        self.assertEqual(moonset(date2, bangalore), [24, 14, 11])

    def test_sunrise(self):
        self.assertEqual(sunrise(date2, bangalore)[1], [6, 49, 46])

    def test_sunset(self):
        self.assertEqual(sunset(date2, bangalore)[1], [18, 10, 25])

    def test_vaara(self):
        self.assertEqual(vaara(date2), 5)

    def test_karana_helsinki(self):
        self.assertEqual(karana(date2, helsinki), [14, [12, 54, 20]])

    def test_sunrise_shillong(self):
        sunrise(date4, shillong)


class VarjyamTests(PanchangaTestCase):
    """Varjyam computation."""

    def test_varjyam_delhi(self):
        jd = gregorian_to_jd(Date(2026, 7, 17))
        delhi = Place(28.6139, 77.2090, 5.5)
        v = varjyam(jd, delhi)
        self.assertEqual(len(v), 2)
        self.assertEqual(v, [[[7, 12, 6], [8, 42, 56]], [[26, 21, 48], [27, 55, 30]]])


class TithiTests(PanchangaTestCase):
    """Tithi computation with various dates and locations."""

    def test_krishna_ashtami(self):
        result = tithi(date1, bangalore)
        self.assertEqual(result[0], 23)

    def test_saptami(self):
        result = tithi(date2, bangalore)
        self.assertEqual(result[0], 7)

    def test_krishna_saptami(self):
        result = tithi(date3, bangalore)
        self.assertEqual(result[0], 22)

    def test_shukla_saptami_helsinki(self):
        result = tithi(date2, helsinki)
        self.assertEqual(result[0], 7)

    def test_apr24_bangalore(self):
        apr24 = gregorian_to_jd(Date(2010, 4, 24))
        result = tithi(apr24, bangalore)
        self.assertEqual(result, [10, [6, 9, 29], 11, [27, 33, 58]])

    def test_feb3_bangalore(self):
        feb3 = gregorian_to_jd(Date(2013, 2, 3))
        result = tithi(feb3, bangalore)
        self.assertEqual(result, [22, [8, 14, 6], 23, [30, 33, 17]])

    def test_apr19_helsinki(self):
        apr19 = gregorian_to_jd(Date(2013, 4, 19))
        result = tithi(apr19, helsinki)
        self.assertEqual(result[0], 9)

    def test_apr20_helsinki(self):
        apr20 = gregorian_to_jd(Date(2013, 4, 20))
        result = tithi(apr20, helsinki)
        self.assertEqual(result[0], 10)

    def test_apr21_helsinki(self):
        apr21 = gregorian_to_jd(Date(2013, 4, 21))
        result = tithi(apr21, helsinki)
        self.assertEqual(result[0], 10)


class NakshatraTests(PanchangaTestCase):
    """Nakshatra and nakshatra_pada."""

    def test_nakshatra_date1_bangalore(self):
        result = nakshatra(date1, bangalore)
        self.assertEqual(result[0], 27)

    def test_nakshatra_date2_bangalore(self):
        result = nakshatra(date2, bangalore)
        self.assertEqual(result[0], 27)

    def test_nakshatra_date3_bangalore(self):
        result = nakshatra(date3, bangalore)
        self.assertEqual(result[0], 24)

    def test_nakshatra_date4_shillong(self):
        result = nakshatra(date4, shillong)
        self.assertEqual(result[0], 3)

    def test_nakshatra_pada_unequal(self):
        set_nakshatra_system('unequal')
        self.addCleanup(set_nakshatra_system)
        self.assertEqual(nakshatra_pada(from_dms(5, 30)), [1, 2])
        self.assertEqual(nakshatra_pada(from_dms(73, 19)), [6, 4])
        self.assertEqual(nakshatra_pada(from_dms(93, 20)), [8, 1])
        self.assertEqual(nakshatra_pada(from_dms(274, 0)), [21, 3])
        self.assertEqual(nakshatra_pada(from_dms(347, 0)), [27, 1])
        self.assertEqual(nakshatra_pada(from_dms(359, 59)), [27, 4])

    def test_equal_vs_unequal_contrast(self):
        set_nakshatra_system('unequal')
        self.addCleanup(set_nakshatra_system)
        self.assertEqual(nakshatra_pada(from_dms(23, 0)), [3, 1])

        set_nakshatra_system('equal')
        self.assertEqual(nakshatra_pada(from_dms(23, 0)), [2, 3])


class YogaTests(PanchangaTestCase):
    """Yoga computation."""

    def test_yoga_date3(self):
        result = yoga(date3, bangalore)
        self.assertEqual(result[0], 1)

    def test_yoga_date2(self):
        result = yoga(date2, bangalore)
        self.assertEqual(result[0], 21)

    def test_yoga_may22_helsinki(self):
        may22 = gregorian_to_jd(Date(2013, 5, 22))
        result = yoga(may22, helsinki)
        self.assertEqual(result[0], 16)


class MasaTests(PanchangaTestCase):
    """Masa computation with amanta and purnimanta systems."""

    def test_feb10_bangalore(self):
        jd = gregorian_to_jd(Date(2013, 2, 10))
        self.assertEqual(masa(jd, bangalore)[0], 10)

    def test_aug17_bangalore(self):
        aug17 = gregorian_to_jd(Date(2012, 8, 17))
        self.assertEqual(masa(aug17, bangalore)[0], 5)

    def test_aug18_bangalore(self):
        aug18 = gregorian_to_jd(Date(2012, 8, 18))
        result = masa(aug18, bangalore)
        self.assertEqual(result[0], 6)
        self.assertTrue(result[1])

    def test_sep19_bangalore(self):
        sep19 = gregorian_to_jd(Date(2012, 9, 18))
        result = masa(sep19, bangalore)
        self.assertEqual(result[0], 6)
        self.assertFalse(result[1])

    def test_may20_helsinki(self):
        may20 = gregorian_to_jd(Date(2012, 5, 20))
        result = masa(may20, helsinki)
        self.assertEqual(result[0], 2)

    def test_may21_helsinki(self):
        may21 = gregorian_to_jd(Date(2012, 5, 21))
        result = masa(may21, helsinki)
        self.assertEqual(result[0], 3)

    def test_purnimanta_amanta_contrast(self):
        apr17 = gregorian_to_jd(Date(2023, 4, 17))
        self.assertEqual(masa(apr17, bangalore, amanta=False), [2, False])
        self.assertEqual(masa(apr17, bangalore, amanta=True), [1, False])

        may21 = gregorian_to_jd(Date(2023, 5, 21))
        self.assertEqual(masa(may21, bangalore, amanta=False), [3, False])
        self.assertEqual(masa(may21, bangalore, amanta=True), [3, False])

        feb21 = gregorian_to_jd(Date(2023, 2, 21))
        self.assertEqual(masa(feb21, bangalore, amanta=False), [12, False])
        self.assertEqual(masa(feb21, bangalore, amanta=True), [12, False])

        mar15 = gregorian_to_jd(Date(2023, 3, 15))
        self.assertEqual(masa(mar15, bangalore, amanta=True), [12, False])
        self.assertEqual(masa(mar15, bangalore, amanta=False), [1, False])


class AscendantTests(PanchangaTestCase):
    """Ascendant computation."""

    def test_ascendant_sep24(self):
        jd = swe.julday(2015, 9, 24, 23 + 38 / 60.)
        result = ascendant(jd, bangalore)
        self.assertEqual(result, [2, [4, 38, 27], [5, 4]])

    def test_ascendant_sep25(self):
        jd = swe.julday(2015, 9, 25, 13 + 29 / 60. + 13 / 3600.)
        result = ascendant(jd, bangalore)
        self.assertEqual(result, [8, [20, 24, 47], [20, 3]])


class NavamsaTests(PanchangaTestCase):
    """Navamsa computation."""

    def test_navamsa(self):
        jd = swe.julday(2015, 9, 25, 13 + 29 / 60. + 13 / 3600.)
        result = navamsa(jd, bangalore)
        expected = [
            [0, 11], [1, 5], [4, 1], [2, 2], [5, 4], [3, 10],
            [6, 4], [10, 11], [9, 5], [7, 10], [8, 10],
        ]
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
