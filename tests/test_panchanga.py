"""Unit tests for core panchanga computations.

Extracted from the inline ``_tests()`` functions that used to live at the
bottom of ``panchanga.py``.
"""

import os
import unittest
from unittest import mock
import swisseph as swe

import panchanga
from panchanga import (Date, Place, gregorian_to_jd, from_dms,
    sunrise, sunset, moonrise, moonrise_jd, moonset, tithi, nakshatra, nakshatra_pada,
    nakshatra_end_point, yoga, karana, vaara, masa, varjyam, ascendant, navamsa,
    navamsa_from_long, planetary_positions, day_duration, gauri_chogadiya,
    trikalam, rahu_kalam, yamaganda_kalam, gulika_kalam, durmuhurtam,
    abhijit_muhurta, elapsed_year, samvatsara, samvatsara_north, samvatsara_north_modern,
    ritu, drik_ritu, drik_ritu_at, lunar_masa,
    raasi, lunar_phase,
    new_moon, full_moon, local_time_to_jdut1, sweph_version,
    default_se_ephe_path, get_planet_name, to_dms, to_dms_prec, unwrap_angles,
    lon_relative_to_base, inverse_lagrange, bisection_search,
    sidereal_saptarshi_nakshatra, saptarshi_nakshatra_traditional,
    set_nakshatra_system, set_chosen_ayanamsa, set_ayanamsa_mode,
    set_coordinate_mode, set_coordinate_selection, reset_ayanamsa_mode,
    solar_longitude)


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

    def test_purnimanta_matches_amanta_on_shukla(self):
        """Śukla pakṣa month names must agree in both systems."""
        from datetime import date, timedelta
        day = date(2023, 1, 1)
        for _ in range(365):
            jd = gregorian_to_jd(Date(day.year, day.month, day.day))
            ti = tithi(jd, bangalore)[0]
            if ti <= 15:
                amanta_masa, amanta_adhika = masa(jd, bangalore, amanta=True)
                purni_masa, purni_adhika = masa(jd, bangalore, amanta=False)
                self.assertEqual(
                    (purni_masa, purni_adhika), (amanta_masa, amanta_adhika),
                    msg=f"{day} ti={ti}")
            day += timedelta(days=1)

    def test_purnimanta_is_next_month_on_ordinary_krishna(self):
        """Ordinary kṛṣṇa: pūrṇimānta is the month after amānta."""
        from datetime import date, timedelta
        day = date(2023, 1, 1)
        for _ in range(365):
            jd = gregorian_to_jd(Date(day.year, day.month, day.day))
            ti = tithi(jd, bangalore)[0]
            if ti >= 16:
                amanta_masa, amanta_adhika = masa(jd, bangalore, amanta=True)
                purni_masa, purni_adhika = masa(jd, bangalore, amanta=False)
                self.assertEqual(purni_adhika, amanta_adhika, msg=f"{day} ti={ti}")
                if amanta_adhika:
                    self.assertEqual(purni_masa, amanta_masa, msg=f"{day} ti={ti}")
                else:
                    self.assertEqual(purni_masa, amanta_masa % 12 + 1, msg=f"{day} ti={ti}")
            day += timedelta(days=1)

    def test_purnimanta_magha_krishna_is_phalguna(self):
        """Amānta Māgha-kṛṣṇa must be pūrṇimānta Phālguna (not Chaitra)."""
        feb10 = gregorian_to_jd(Date(2023, 2, 10))
        self.assertEqual(masa(feb10, bangalore, amanta=True), [11, False])
        self.assertEqual(masa(feb10, bangalore, amanta=False), [12, False])

    def test_purnimanta_adhika_keeps_amanta_name(self):
        """Drik/MyPanchang: one NM-based Adhika-X for both systems, no kṛṣṇa +1."""
        # 2023 Adhika Śrāvaṇa (amānta): 18 Jul – 16 Aug.
        jul25 = gregorian_to_jd(Date(2023, 7, 25))  # śukla in adhika
        self.assertEqual(masa(jul25, bangalore, amanta=True), [5, True])
        self.assertEqual(masa(jul25, bangalore, amanta=False), [5, True])

        aug10 = gregorian_to_jd(Date(2023, 8, 10))  # kṛṣṇa in adhika
        self.assertEqual(masa(aug10, bangalore, amanta=True), [5, True])
        self.assertEqual(masa(aug10, bangalore, amanta=False), [5, True])

        # 2012 Adhika Bhādrapada (amānta): 18 Aug – 16 Sep.
        aug20 = gregorian_to_jd(Date(2012, 8, 20))
        self.assertEqual(masa(aug20, bangalore, amanta=True), [6, True])
        self.assertEqual(masa(aug20, bangalore, amanta=False), [6, True])
        sep5 = gregorian_to_jd(Date(2012, 9, 5))
        self.assertEqual(masa(sep5, bangalore, amanta=True), [6, True])
        self.assertEqual(masa(sep5, bangalore, amanta=False), [6, True])

    def test_purnimanta_no_false_fm_adhika_in_2022(self):
        """2022 has no NM-adhika; sites do not mark Adhika Jyeṣṭha."""
        may20 = gregorian_to_jd(Date(2022, 5, 20))
        self.assertEqual(masa(may20, bangalore, amanta=True), [2, False])
        self.assertEqual(masa(may20, bangalore, amanta=False), [3, False])

        jun5 = gregorian_to_jd(Date(2022, 6, 5))
        self.assertEqual(masa(jun5, bangalore, amanta=True), [3, False])
        self.assertEqual(masa(jun5, bangalore, amanta=False), [3, False])

    def test_full_moon_on_purnima_is_current_not_next_month(self):
        """opt=+1 on tithi 15 must return today's full moon."""
        jd = gregorian_to_jd(Date(2023, 1, 6))
        ti = tithi(jd, bangalore)[0]
        self.assertEqual(ti, 15)
        crit = sunrise(jd, bangalore)[0]
        current = full_moon(crit, ti, +1)
        previous = full_moon(crit, ti, -1)
        self.assertLess(abs(current - crit), 2)
        self.assertGreater(current - previous, 25)
        self.assertLess(current - previous, 35)


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

    def test_navamsa_from_long(self):
        self.assertEqual(navamsa_from_long(0), 0)
        self.assertEqual(navamsa_from_long(40), 0)
        self.assertEqual(navamsa_from_long(3 + 20 / 60), 1)


class HelperMathTests(PanchangaTestCase):
    """Pure helpers that do not need Swiss Ephemeris data."""

    def test_from_dms_and_to_dms(self):
        self.assertAlmostEqual(from_dms(23, 30, 30), 23.508333, places=5)
        self.assertEqual(to_dms(12.5), [12, 30, 0])
        degrees, minutes, seconds = to_dms_prec(12.5)
        self.assertEqual([degrees, minutes], [12, 30])
        self.assertAlmostEqual(seconds, 0, places=5)

    def test_unwrap_angles(self):
        self.assertEqual(unwrap_angles([350, 10, 20]), [350, 370, 380])

    def test_lon_relative_to_base(self):
        self.assertEqual(lon_relative_to_base(10, 350), 370)
        self.assertEqual(lon_relative_to_base(350, 10), -10)

    def test_inverse_lagrange_linear(self):
        self.assertAlmostEqual(inverse_lagrange([0, 1], [0, 10], 5), 0.5)

    def test_bisection_search(self):
        self.assertAlmostEqual(bisection_search(lambda x: x - 2, 0, 5), 2, places=6)

    def test_get_planet_name(self):
        self.assertEqual(get_planet_name(swe.SUN), "Surya")
        self.assertEqual(get_planet_name(swe.MOON), "Candra")
        self.assertEqual(get_planet_name(swe.MARS), "Mangala")
        self.assertEqual(get_planet_name(swe.RAHU), "Rahu")
        self.assertEqual(get_planet_name(swe.KETU), "Ketu")

    def test_sweph_version_format(self):
        version = sweph_version()
        self.assertRegex(version, r"^\d+\.\d+\.\d+ \(\d{8}\)$")

    def test_ritu(self):
        self.assertEqual(ritu(1), 0)
        self.assertEqual(ritu(2), 0)
        self.assertEqual(ritu(12), 5)

    def test_lunar_masa_matches_amanta_masa(self):
        jd = gregorian_to_jd(Date(2023, 7, 25))
        ti, last_nm, masa_num, is_adhika = lunar_masa(jd, bangalore)
        self.assertEqual(ti, tithi(jd, bangalore)[0])
        self.assertEqual([masa_num, is_adhika], masa(jd, bangalore, True))
        self.assertLess(last_nm, sunrise(jd, bangalore)[0])

        # Optional tithi_number avoids recomputing tithi.
        again = lunar_masa(jd, bangalore, tithi_number=ti)
        self.assertEqual(again[2:], (masa_num, is_adhika))

    def test_masa_with_tithi_number_matches_full_call(self):
        jd = gregorian_to_jd(Date(2023, 7, 25))
        ti = tithi(jd, bangalore)[0]
        self.assertEqual(
            masa(jd, bangalore, True),
            masa(jd, bangalore, True, tithi_number=ti))
        self.assertEqual(
            masa(jd, bangalore, False),
            masa(jd, bangalore, False, tithi_number=ti))

    def test_drik_ritu_ordinary_pairing(self):
        """Away from adhika, Drik ṛtu follows Phālguna–Chaitra, … pairing."""
        # 2022 has no NM-adhika; sample each pair.
        cases = [
            (Date(2022, 3, 10), 0),   # Phālguna/Chaitra → Vasanta
            (Date(2022, 5, 10), 1),   # Vaiśākha/Jyeṣṭha → Grīṣma
            (Date(2022, 7, 10), 2),   # Āṣāḍha/Śrāvaṇa → Varṣā
            (Date(2022, 9, 10), 3),   # Bhādrapada/Āśvina → Śarad
            (Date(2022, 11, 10), 4),  # Kārtika/Mārgaśīrṣa → Hemanta
            (Date(2022, 1, 20), 5),   # Pauṣa/Māgha → Śiśira
        ]
        for civil, expect in cases:
            jd = gregorian_to_jd(civil)
            self.assertEqual(drik_ritu_at(jd, bangalore), expect, msg=str(civil))

    def test_drik_ritu_immune_to_purnimanta_label(self):
        """Ordinary kṛṣṇa: pūrṇimānta renames māsa, but Drik ṛtu stays put."""
        feb10 = gregorian_to_jd(Date(2023, 2, 10))  # amānta Māgha-kṛṣṇa
        self.assertEqual(masa(feb10, bangalore, True), [11, False])
        self.assertEqual(masa(feb10, bangalore, False), [12, False])
        # Śiśira = 10, 11 — not Vasanta from pūrṇimānta Phālguna.
        self.assertEqual(drik_ritu_at(feb10, bangalore), 5)
        self.assertEqual(ritu(masa(feb10, bangalore, True)[0]), 5)

    def test_drik_ritu_splits_nija_when_adhika_is_pair_second(self):
        """2023 Adhika Śrāvaṇa: first 15 nija tithis stay; next 15 → next ṛtu."""
        jul25 = gregorian_to_jd(Date(2023, 7, 25))  # adhika, tithis 1–15
        self.assertEqual(masa(jul25, bangalore, True), [5, True])
        self.assertEqual(drik_ritu_at(jul25, bangalore), 2)

        aug20 = gregorian_to_jd(Date(2023, 8, 20))  # nija, first 15
        self.assertEqual(masa(aug20, bangalore, True), [5, False])
        self.assertEqual(drik_ritu_at(aug20, bangalore), 2)

        sep1 = gregorian_to_jd(Date(2023, 9, 1))  # nija, next 15
        self.assertEqual(masa(sep1, bangalore, True), [5, False])
        self.assertGreaterEqual(tithi(sep1, bangalore)[0], 16)
        self.assertEqual(drik_ritu_at(sep1, bangalore), 3)

    def test_drik_ritu_splits_adhika_when_adhika_is_pair_first(self):
        """2012 Adhika Bhādrapada: first 15 adhika → prev; next 15 → current."""
        aug20 = gregorian_to_jd(Date(2012, 8, 20))  # adhika, first 15
        self.assertEqual(masa(aug20, bangalore, True), [6, True])
        self.assertLessEqual(tithi(aug20, bangalore)[0], 15)
        self.assertEqual(drik_ritu_at(aug20, bangalore), 2)

        sep1 = gregorian_to_jd(Date(2012, 9, 1))  # adhika, next 15
        self.assertEqual(masa(sep1, bangalore, True), [6, True])
        self.assertGreaterEqual(tithi(sep1, bangalore)[0], 16)
        self.assertEqual(drik_ritu_at(sep1, bangalore), 3)

        sep17 = gregorian_to_jd(Date(2012, 9, 17))  # nija — stays
        self.assertEqual(masa(sep17, bangalore, True), [6, False])
        self.assertEqual(drik_ritu_at(sep17, bangalore), 3)

        oct20 = gregorian_to_jd(Date(2012, 10, 20))
        self.assertEqual(masa(oct20, bangalore, True), [7, False])
        self.assertEqual(drik_ritu_at(oct20, bangalore), 3)
        oct30 = gregorian_to_jd(Date(2012, 10, 30))
        self.assertEqual(masa(oct30, bangalore, True), [7, False])
        self.assertEqual(drik_ritu_at(oct30, bangalore), 3)

    def test_drik_ritu_pure_from_masa_args(self):
        """Pure form: same rules without jd/place."""
        # Base pairs, including Phālguna wrap.
        self.assertEqual(drik_ritu(12), 0)
        self.assertEqual(drik_ritu(1), 0)
        self.assertEqual(drik_ritu(11), 5)

        # Adhika second of pair: entire adhika stays in current ṛtu.
        self.assertEqual(drik_ritu(5, True, 10), 2)
        self.assertEqual(drik_ritu(5, True, 20), 2)

        # Nija after that adhika.
        self.assertEqual(drik_ritu(5, False, 10, True), 2)  # first 15
        self.assertEqual(drik_ritu(5, False, 20, True), 3)  # next 15
        self.assertEqual(drik_ritu(5, False, 20, False), 2)  # ordinary: no shift

        # Adhika first of pair.
        self.assertEqual(drik_ritu(6, True, 10), 2)   # first 15 → prev
        self.assertEqual(drik_ritu(6, True, 20), 3)   # next 15 → current
        self.assertEqual(drik_ritu(12, True, 5), 5)   # Phālguna adhika first 15 → Śiśira
        self.assertEqual(drik_ritu(12, True, 20), 0)  # next 15 → Vasanta


class PathAndModeTests(PanchangaTestCase):
    """Ephemeris path helpers and coordinate / ayanamsa mode setters."""

    def test_default_se_ephe_path_unix(self):
        with mock.patch.object(panchanga.sys, "platform", "linux"):
            with mock.patch.dict(os.environ, {"XDG_DATA_HOME": "/tmp/xdg"}, clear=False):
                self.assertEqual(default_se_ephe_path(), os.path.join("/tmp/xdg", "swisseph"))
            with mock.patch.dict(os.environ, {}, clear=True):
                with mock.patch.object(panchanga.os.path, "expanduser", return_value="/home/u"):
                    path = default_se_ephe_path()
        self.assertTrue(path.endswith(os.path.join(".local", "share", "swisseph")))

    def test_default_se_ephe_path_windows(self):
        with mock.patch.object(panchanga.sys, "platform", "win32"):
            with mock.patch.dict(os.environ, {"LOCALAPPDATA": r"C:\Users\u\AppData\Local"}, clear=False):
                self.assertEqual(
                    default_se_ephe_path(),
                    os.path.join(r"C:\Users\u\AppData\Local", "swisseph"),
                )
            env = {key: value for key, value in os.environ.items() if key != "LOCALAPPDATA"}
            with mock.patch.dict(os.environ, env, clear=True):
                with mock.patch.object(panchanga.os.path, "expanduser", return_value=r"C:\Users\u"):
                    path = default_se_ephe_path()
        self.assertTrue(path.endswith(os.path.join("AppData", "Local", "swisseph")))

    def test_set_coordinate_mode(self):
        set_coordinate_mode("tropical")
        self.addCleanup(set_coordinate_mode, "sidereal")
        self.assertEqual(panchanga.coordinate_flag, swe.FLG_TROPICAL)
        set_coordinate_mode("sidereal")
        self.assertEqual(panchanga.coordinate_flag, swe.FLG_SIDEREAL)
        with mock.patch("builtins.print"):
            set_coordinate_mode("bogus")
        self.assertEqual(panchanga.coordinate_flag, swe.FLG_SIDEREAL)

    def test_set_coordinate_selection_restores_sidereal_mode(self):
        self.addCleanup(set_coordinate_selection, "citra")
        set_coordinate_selection("tropical")
        self.assertEqual(panchanga.coordinate_flag, swe.FLG_TROPICAL)
        set_coordinate_selection("raman")
        self.assertEqual(panchanga.coordinate_flag, swe.FLG_SIDEREAL)
        self.assertEqual(panchanga.chosen_ayanamsa, "raman")

    def test_set_coordinate_selection_rejects_unknown_selection(self):
        with self.assertRaisesRegex(ValueError, "Unknown coordinate selection"):
            set_coordinate_selection("not-a-coordinate")

    def test_set_nakshatra_system_unknown(self):
        with mock.patch("builtins.print"):
            set_nakshatra_system("bogus")
        self.assertEqual(panchanga.nakshatra_system, "equal")

    def test_unknown_ayanamsa_falls_back_to_fagan_bradley(self):
        set_chosen_ayanamsa("not-a-real-ayanamsa")
        self.addCleanup(set_chosen_ayanamsa, "citra")
        set_ayanamsa_mode()
        reset_ayanamsa_mode()


class CalendarUtilityTests(PanchangaTestCase):
    """Elapsed year, samvatsara, moon phases, and local-time conversion."""

    def test_elapsed_year_and_samvatsara(self):
        kali, saka, vikrama = elapsed_year(date2, 10)
        self.assertIsInstance(kali, int)
        self.assertEqual(saka, kali - 3179)
        self.assertEqual(vikrama, saka + 135)
        self.assertGreater(kali, 5000)
        year_index = samvatsara(date2, 10)
        self.assertGreaterEqual(year_index, 0)
        self.assertLess(year_index, 60)

    def test_samvatsara_north_anchors(self):
        # CRC Appendix 5-E: śaka 1876 (1954-55) = North Plavaṅga / South Jaya.
        # North = full-Kali Sūrya-Siddhānta Bārhaspatya (Sewell Art. 59a);
        # South applies the post–Śaka 905 stop-expunging remap.
        jd_crc = gregorian_to_jd(Date(1954, 4, 21))
        self.assertEqual(samvatsara(jd_crc, 4), 28)       # Jaya
        self.assertEqual(samvatsara_north(jd_crc, 4), 41)  # Plavaṅga

        # Modern: North ≠ South (accumulated kṣaya gap since Śaka 905).
        # 2026-08-01 amānta māsa 4: Kali 5127 → SS North 54; South 40.
        # Also a kṣaya divergence vs the old (vikrama + 10) % 60 shortcut (53).
        jd_modern = gregorian_to_jd(Date(2026, 8, 1))
        kali, _saka, vikrama = elapsed_year(jd_modern, 4)
        expected_north = (kali + 27 + int((kali * 211 - 108) / 18000)) % 60
        self.assertEqual(expected_north, 54)
        self.assertEqual(samvatsara_north(jd_modern, 4), expected_north)
        self.assertEqual(samvatsara(jd_modern, 4), 40)  # Parābhava
        self.assertNotEqual(samvatsara_north(jd_modern, 4), (vikrama + 10) % 60)
        self.assertNotEqual(samvatsara(jd_modern, 4), samvatsara_north(jd_modern, 4))

        self.assertGreaterEqual(samvatsara_north(date2, 10), 0)
        self.assertLess(samvatsara_north(date2, 10), 60)
        self.assertNotEqual(samvatsara(date2, 10), samvatsara_north(date2, 10))

    def test_samvatsara_north_modern(self):
        # Integer modern rate 209/18000 (SS uses 211/18000). CRC 1954 and 2026
        # each fall one name behind SS North for these Kali years.
        jd_crc = gregorian_to_jd(Date(1954, 4, 21))
        self.assertEqual(samvatsara_north(jd_crc, 4), 41)
        self.assertEqual(samvatsara_north_modern(jd_crc, 4), 40)

        jd_modern = gregorian_to_jd(Date(2026, 8, 1))
        self.assertEqual(samvatsara_north(jd_modern, 4), 54)
        self.assertEqual(samvatsara_north_modern(jd_modern, 4), 53)
        self.assertGreaterEqual(samvatsara_north_modern(jd_modern, 4), 0)
        self.assertLess(samvatsara_north_modern(jd_modern, 4), 60)

    def test_raasi_and_lunar_phase(self):
        sign = raasi(date2)
        self.assertGreaterEqual(sign, 1)
        self.assertLessEqual(sign, 12)
        phase = lunar_phase(date2)
        self.assertGreaterEqual(phase, 0)
        self.assertLess(phase, 360)

    def test_new_and_full_moon(self):
        ti = tithi(date2, bangalore)[0]
        previous_new = new_moon(date2, ti, opt=-1)
        next_new = new_moon(date2, ti, opt=+1)
        self.assertLess(previous_new, date2)
        self.assertGreaterEqual(next_new, date2)
        previous_full = full_moon(date2, ti, opt=-1)
        next_full = full_moon(date2, ti, opt=+1)
        self.assertLess(previous_full, next_full)
        self.assertAlmostEqual(min(lunar_phase(previous_new) % 360, 360 - (lunar_phase(previous_new) % 360)), 0, delta=1.0)
        self.assertAlmostEqual(lunar_phase(previous_full), 180, delta=1.0)

    def test_local_time_to_jdut1(self):
        jd = local_time_to_jdut1(2013, 1, 18, 12, 0, 0, timezone=5.5)
        self.assertIsInstance(jd, float)
        self.assertGreater(jd, date2)
        self.assertLess(jd, date2 + 1)

    def test_moonrise_jd_matches_moonrise(self):
        rise_jd = moonrise_jd(date2, bangalore)
        self.assertEqual(moonrise(date2, bangalore), to_dms((rise_jd - date2) * 24))

    def test_nakshatra_end_point_equal_and_unequal(self):
        self.assertAlmostEqual(nakshatra_end_point(1), 360 / 27)
        set_nakshatra_system("unequal")
        self.addCleanup(set_nakshatra_system, "equal")
        self.assertAlmostEqual(nakshatra_end_point(1), 13 + 20 / 60)


class EphemerisCacheTests(PanchangaTestCase):
    """LRU memoization on longitudes, rise/set, and day-bucketed syzygies."""

    def setUp(self):
        super().setUp()
        panchanga._planet_longitude_cached.cache_clear()
        panchanga._new_moon_cached.cache_clear()
        panchanga._full_moon_cached.cache_clear()
        sunrise.cache_clear()
        sunset.cache_clear()
        moonrise_jd.cache_clear()

    def test_planet_longitude_cache_is_ayanamsa_aware(self):
        jd = gregorian_to_jd(Date(2023, 7, 25))
        set_chosen_ayanamsa("citra")
        citra = solar_longitude(jd)
        set_chosen_ayanamsa("lahiri")
        lahiri = solar_longitude(jd)
        set_chosen_ayanamsa("citra")
        self.assertNotEqual(citra, lahiri)
        self.assertEqual(citra, solar_longitude(jd))

    def test_sunrise_and_sunset_cache_hit_on_repeat(self):
        first_rise = sunrise(date2, bangalore)
        first_set = sunset(date2, bangalore)
        rise_hits = sunrise.cache_info().hits
        set_hits = sunset.cache_info().hits
        self.assertEqual(sunrise(date2, bangalore), first_rise)
        self.assertEqual(sunset(date2, bangalore), first_set)
        self.assertEqual(sunrise.cache_info().hits, rise_hits + 1)
        self.assertEqual(sunset.cache_info().hits, set_hits + 1)

    def test_moonrise_jd_cache_hit_on_repeat(self):
        first = moonrise_jd(date2, bangalore)
        hits = moonrise_jd.cache_info().hits
        self.assertEqual(moonrise_jd(date2, bangalore), first)
        self.assertEqual(moonrise_jd.cache_info().hits, hits + 1)

    def test_new_moon_day_bucket_shared_across_adjacent_days(self):
        """Nearest-day search centres must collide within one synodic span."""
        jd_a = gregorian_to_jd(Date(2026, 1, 10))
        jd_b = gregorian_to_jd(Date(2026, 1, 11))
        crit_a = sunrise(jd_a, bangalore)[0]
        crit_b = sunrise(jd_b, bangalore)[0]
        ti_a = tithi(jd_a, bangalore)[0]
        ti_b = tithi(jd_b, bangalore)[0]
        panchanga._new_moon_cached.cache_clear()
        last_a = new_moon(crit_a, ti_a, -1)
        next_a = new_moon(crit_a, ti_a, +1)
        misses_after_first_day = panchanga._new_moon_cached.cache_info().misses
        last_b = new_moon(crit_b, ti_b, -1)
        next_b = new_moon(crit_b, ti_b, +1)
        self.assertEqual(last_a, last_b)
        self.assertEqual(next_a, next_b)
        # Second civil day should reuse both day-buckets (prev + next).
        self.assertEqual(panchanga._new_moon_cached.cache_info().misses, misses_after_first_day)
        self.assertGreaterEqual(panchanga._new_moon_cached.cache_info().hits, 2)

    def test_full_moon_day_bucket_shared_across_adjacent_days(self):
        jd_a = gregorian_to_jd(Date(2026, 1, 10))
        jd_b = gregorian_to_jd(Date(2026, 1, 11))
        crit_a = sunrise(jd_a, bangalore)[0]
        crit_b = sunrise(jd_b, bangalore)[0]
        ti_a = tithi(jd_a, bangalore)[0]
        ti_b = tithi(jd_b, bangalore)[0]
        panchanga._full_moon_cached.cache_clear()
        prev_a = full_moon(crit_a, ti_a, -1)
        next_a = full_moon(crit_a, ti_a, +1)
        misses = panchanga._full_moon_cached.cache_info().misses
        self.assertEqual(prev_a, full_moon(crit_b, ti_b, -1))
        self.assertEqual(next_a, full_moon(crit_b, ti_b, +1))
        self.assertEqual(panchanga._full_moon_cached.cache_info().misses, misses)


class MuhurtaTests(PanchangaTestCase):
    """Day parts: duration, chogadiya, trikalam, durmuhurtam, abhijit."""

    def test_day_duration(self):
        hours, as_dms = day_duration(date2, bangalore)
        self.assertGreater(hours, 10)
        self.assertLess(hours, 14)
        self.assertEqual(as_dms, to_dms(hours))

    def test_gauri_chogadiya(self):
        ends = gauri_chogadiya(date2, bangalore)
        self.assertEqual(len(ends), 16)
        self.assertEqual(len(ends[0]), 3)

    def test_trikalam_aliases(self):
        rahu = rahu_kalam(date2, bangalore)
        yama = yamaganda_kalam(date2, bangalore)
        gulika = gulika_kalam(date2, bangalore)
        for window in (rahu, yama, gulika):
            self.assertEqual(len(window), 2)
            self.assertEqual(len(window[0]), 3)
            self.assertEqual(len(window[1]), 3)
        self.assertEqual(trikalam(date2, bangalore, "rahu"), rahu)

    def test_durmuhurtam_and_abhijit(self):
        starts, ends = durmuhurtam(date2, bangalore)
        self.assertEqual(len(starts), 2)
        self.assertEqual(len(ends), 2)
        abhijit = abhijit_muhurta(date2, bangalore)
        self.assertEqual(len(abhijit), 2)
        self.assertLess(abhijit[0], abhijit[1])


class PlanetaryPositionTests(PanchangaTestCase):
    """Instantaneous planetary positions and Saptarshi helpers."""

    def test_planetary_positions(self):
        jd = swe.julday(2015, 9, 25, 13 + 29 / 60. + 13 / 3600.)
        positions = planetary_positions(jd, bangalore)
        self.assertEqual(len(positions), len(panchanga.planet_list))
        for planet, constellation, coordinates, pada in positions:
            self.assertIn(planet, panchanga.planet_list)
            self.assertGreaterEqual(constellation, 0)
            self.assertLessEqual(constellation, 11)
            self.assertEqual(len(coordinates), 3)
            self.assertEqual(len(pada), 2)

    def test_sidereal_saptarshi_nakshatra(self):
        result = sidereal_saptarshi_nakshatra(date2)
        self.assertGreaterEqual(result["mean_nakshatra"], 1)
        self.assertLessEqual(result["mean_nakshatra"], 27)
        self.assertGreaterEqual(result["mean_pada"], 1)
        self.assertLessEqual(result["mean_pada"], 4)
        self.assertEqual(len(result["individual"]), 7)
        self.assertGreaterEqual(result["mean_longitude"], 0)
        self.assertLess(result["mean_longitude"], 360)

    def test_saptarshi_nakshatra_traditional(self):
        nak = saptarshi_nakshatra_traditional(date2)
        self.assertGreaterEqual(nak, 1)
        self.assertLessEqual(nak, 27)


if __name__ == "__main__":
    unittest.main()
