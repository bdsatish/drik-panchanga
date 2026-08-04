"""Day WebUI panchanga API: māsa labels and convention-free ṛtus."""

import unittest
from threading import Event, Lock, Thread
from unittest.mock import patch

import panchanga
from webapp.day_panchanga import compute_day_panchanga


class DayPanchangaMasaRituTests(unittest.TestCase):

    def setUp(self):
        panchanga.set_coordinate_selection("citra")

    def tearDown(self):
        panchanga.reset_ayanamsa_mode()

    def test_coordinate_metadata_is_structured(self):
        sidereal = compute_day_panchanga(
            "Bengaluru", "21/04/2023", coordinate_selection="citra")
        self.assertEqual(sidereal["coordinate_mode"], "sidereal")
        self.assertEqual(sidereal["coordinate_label"], "Chitra-paksha")
        self.assertEqual(sidereal["ayanamsa_key"], "citra")
        self.assertIsNotNone(sidereal["ayanamsa"])
        self.assertIsNotNone(sidereal["ayanamsa_degrees"])

        tropical = compute_day_panchanga(
            "Bengaluru", "21/04/2023", coordinate_selection="tropical")
        self.assertEqual(tropical["coordinate_mode"], "tropical")
        self.assertEqual(tropical["coordinate_label"], "Tropical (Sāyana)")
        self.assertIsNone(tropical["ayanamsa_key"])
        self.assertIsNone(tropical["ayanamsa"])
        self.assertIsNone(tropical["ayanamsa_degrees"])

    def test_shared_day_details_contains_common_intervals(self):
        from generate_panchanga_calendar import load_location
        from webapp.day_panchanga import compute_day_details, parse_civil_date

        details = compute_day_details(
            load_location("Bengaluru"), parse_civil_date("21/04/2023"),
            amanta=True, coordinate_selection="citra")
        self.assertEqual(len(details["rahu_kala"]), 2)
        self.assertEqual(len(details["durmuhurta"]), 2)

    def test_coordinate_lock_covers_the_full_day_calculation(self):
        first_selected = Event()
        second_started = Event()
        release_first = Event()
        calls = []
        calls_lock = Lock()
        errors = []
        original_set_selection = panchanga.set_coordinate_selection

        def blocking_set_selection(selection):
            with calls_lock:
                calls.append(selection)
                first_call = len(calls) == 1
            if first_call:
                first_selected.set()
                if not release_first.wait(5):
                    raise AssertionError("timed out waiting for first calculation")
            return original_set_selection(selection)

        def run(selection, started=None):
            if started is not None:
                started.set()
            try:
                compute_day_panchanga(
                    "Bengaluru", "21/04/2023", coordinate_selection=selection)
            except BaseException as error:  # pragma: no cover - assertion below reports it
                errors.append(error)

        with patch.object(
                panchanga, "set_coordinate_selection", side_effect=blocking_set_selection):
            first = Thread(target=run, args=("tropical",))
            second = Thread(target=run, args=("citra", second_started))
            first.start()
            self.assertTrue(first_selected.wait(5))
            second.start()
            self.assertTrue(second_started.wait(5))
            self.assertEqual(calls, ["tropical"])
            release_first.set()
            first.join(10)
            second.join(10)

        self.assertFalse(first.is_alive() or second.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(calls, ["tropical", "citra"])

    def test_purnimanta_renames_ordinary_krishna_masa(self):
        amanta = compute_day_panchanga(
            "Bengaluru", "10/02/2023", month_system="amanta")
        purni = compute_day_panchanga(
            "Bengaluru", "10/02/2023", month_system="purnimanta")
        self.assertEqual(amanta["masa_number"], 11)
        self.assertEqual(purni["masa_number"], 12)
        self.assertIn("Māgha", amanta["masa"])
        self.assertIn("Phālguṇa", purni["masa"])
        # Ṛtus ignore the pūrṇimānta rename.
        self.assertEqual(amanta["rtu"], purni["rtu"])
        self.assertEqual(amanta["drik_rtu"], purni["drik_rtu"])
        self.assertEqual(amanta["rtu"], amanta["drik_rtu"])
        self.assertTrue(amanta["rtu"].endswith("ṛtu"))

    def test_adhika_masa_label_and_shared_name(self):
        amanta = compute_day_panchanga(
            "Bengaluru", "25/07/2023", month_system="amanta")
        purni = compute_day_panchanga(
            "Bengaluru", "25/07/2023", month_system="purnimanta")
        self.assertTrue(amanta["is_adhika"])
        self.assertTrue(purni["is_adhika"])
        self.assertEqual(amanta["masa"], purni["masa"])
        self.assertTrue(amanta["masa"].startswith("Adhika"))
        self.assertIn("Śrāvaṇa", amanta["masa"])
        self.assertEqual(amanta["drik_rtu"], purni["drik_rtu"])
        self.assertIn("Varṣā", amanta["drik_rtu"])
        self.assertEqual(amanta["drik_ayana"], "Dakṣiṇāyana")
        self.assertEqual(amanta["drik_ayana"], purni["drik_ayana"])

    def test_vedic_and_drik_rtu_both_present(self):
        data = compute_day_panchanga("Bengaluru", "21/04/2023")
        self.assertIn("ṛtu", data["rtu"])
        self.assertIn("ṛtu", data["drik_rtu"])
        # Vaiśākha: Vedic Vasanta (1–2), Drik Grīṣma (2–3).
        self.assertIn("Vasanta", data["rtu"])
        self.assertIn("Grīṣma", data["drik_rtu"])
        self.assertEqual(data["drik_ayana"], "Uttarāyaṇa")

    def test_drik_ayana_from_ritu(self):
        from webapp.day_panchanga import drik_ayana_label
        # Śiśira, Vasanta, Grīṣma → Uttara; Varṣā, Śarad, Hemanta → Dakṣiṇa.
        for ritu_num in (5, 0, 1):
            self.assertEqual(drik_ayana_label(ritu_num), "Uttarāyaṇa")
        for ritu_num in (2, 3, 4):
            self.assertEqual(drik_ayana_label(ritu_num), "Dakṣiṇāyana")
