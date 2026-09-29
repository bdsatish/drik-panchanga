"""Day WebUI panchanga API: māsa labels and convention-free ṛtus."""

import unittest
from threading import Event, Lock, Thread
from unittest.mock import patch

import panchanga
from datetime_helper import Date, format_local_hm, gregorian_to_jd
from webapp.day_panchanga import compute_day_panchanga


def _ist(hours, minutes, seconds):
  """UT JD of an IST clock time on 21 April 2023."""
  return gregorian_to_jd(Date(2023, 4, 21)) + (hours + minutes / 60 + seconds / 3600 - 5.5) / 24


class DayPanchangaMasaRituTests(unittest.TestCase):

  def setUp(self):
    panchanga.set_coordinate_selection("citra")

  def tearDown(self):
    panchanga.reset_ayanamsa_mode()

  def test_coordinate_metadata_is_structured(self):
    sidereal = compute_day_panchanga("Bengaluru", "21/04/2023", coordinate_selection="citra")
    self.assertEqual(sidereal["coordinate_mode"], "sidereal")
    self.assertEqual(sidereal["coordinate_label"], "Chitra-paksha")
    self.assertEqual(sidereal["ayanamsa_key"], "citra")
    self.assertIsNotNone(sidereal["ayanamsa"])
    self.assertIsNotNone(sidereal["ayanamsa_degrees"])

    tropical = compute_day_panchanga("Bengaluru", "21/04/2023", coordinate_selection="tropical")
    self.assertEqual(tropical["coordinate_mode"], "tropical")
    self.assertEqual(tropical["coordinate_label"], "Tropical (Sāyana)")
    self.assertIsNone(tropical["ayanamsa_key"])
    self.assertIsNone(tropical["ayanamsa"])
    self.assertIsNone(tropical["ayanamsa_degrees"])

  def test_shared_day_details_contains_common_intervals(self):
    from generate_panchanga_calendar import load_location
    from webapp.day_panchanga import _compute_day_details_unlocked, parse_civil_date

    with panchanga.coordinate_calculation_lock:
      details = _compute_day_details_unlocked(load_location("Bengaluru"), parse_civil_date("21/04/2023"), amanta=True,
                                              coordinate_selection="citra")
    self.assertEqual(len(details["rahu_kala"]), 2)
    self.assertEqual(len(details["durmuhurta"]), 2)
    self.assertEqual(details["varjyam"], panchanga.varjyam(details["jd"], details["place"]))

  def test_json_varjyam_reuses_the_shared_day_details(self):
    day = compute_day_panchanga("Bengaluru", "21/04/2023", coordinate_selection="citra")
    for interval in day["varjyam"]:
      self.assertRegex(interval["start"], r"^\d{2}:\d{2}:\d{2}$")
      self.assertRegex(interval["end"], r"^\d{2}:\d{2}:\d{2}$")
    with patch.object(panchanga, "varjyam", return_value=[(_ist(1, 2, 3), _ist(4, 5, 6))]) as stub:
      stubbed = compute_day_panchanga("Bengaluru", "21/04/2023", coordinate_selection="citra")
    self.assertEqual(stub.call_count, 1)
    self.assertEqual(stubbed["varjyam"], [{"start": "01:02:03", "end": "04:05:06"}])

  def test_json_pratah_sandhya_reuses_the_shared_day_details(self):
    day = compute_day_panchanga("Bengaluru", "21/04/2023", coordinate_selection="citra")
    self.assertRegex(day["pratah_sandhya"]["start"], r"^\d{2}:\d{2}:\d{2}$")
    self.assertRegex(day["pratah_sandhya"]["end"], r"^\d{2}:\d{2}:\d{2}$")
    with patch.object(panchanga, "pratah_sandhya", return_value=[_ist(5, 59, 7), _ist(6, 49, 46)]) as stub:
      stubbed = compute_day_panchanga("Bengaluru", "21/04/2023", coordinate_selection="citra")
    self.assertEqual(stub.call_count, 1)
    self.assertEqual(stubbed["pratah_sandhya"], {"start": "05:59:07", "end": "06:49:46"})

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
        compute_day_panchanga("Bengaluru", "21/04/2023", coordinate_selection=selection)
      except BaseException as error:  # pragma: no cover - assertion below reports it
        errors.append(error)

    with patch.object(panchanga, "set_coordinate_selection", side_effect=blocking_set_selection):
      first = Thread(target=run, args=("tropical", ))
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
    amanta = compute_day_panchanga("Bengaluru", "10/02/2023", month_system="amanta")
    purni = compute_day_panchanga("Bengaluru", "10/02/2023", month_system="purnimanta")
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
    amanta = compute_day_panchanga("Bengaluru", "25/07/2023", month_system="amanta")
    purni = compute_day_panchanga("Bengaluru", "25/07/2023", month_system="purnimanta")
    self.assertTrue(amanta["is_adhika"])
    self.assertTrue(purni["is_adhika"])
    self.assertEqual(amanta["masa"], purni["masa"])
    self.assertTrue(amanta["masa"].startswith("Adhika"))
    self.assertIn("Śrāvaṇa", amanta["masa"])
    self.assertEqual(amanta["drik_rtu"], purni["drik_rtu"])
    self.assertIn("Varṣā", amanta["drik_rtu"])
    self.assertEqual(amanta["drik_ayana"], "Dakṣiṇāyana")
    self.assertEqual(amanta["drik_ayana"], purni["drik_ayana"])

  def test_samvatsara_unchanged_by_purnimanta_label(self):
    # 10/02/2023 is Krsna paksha of underlying month 11 (Magha).
    # In purnimanta this displays as 12 (Phalguna), but samvatsara must follow
    # the underlying lunar month, not the display month.
    amanta = compute_day_panchanga("Bengaluru", "10/02/2023", month_system="amanta")
    purni = compute_day_panchanga("Bengaluru", "10/02/2023", month_system="purnimanta")
    self.assertEqual(amanta["samvatsara"], purni["samvatsara"])
    self.assertEqual(amanta["samvatsara_north"], purni["samvatsara_north"])
    self.assertEqual(amanta["kali_year"], purni["kali_year"])
    self.assertEqual(amanta["saka_year"], purni["saka_year"])
    self.assertEqual(amanta["vikrama_year"], purni["vikrama_year"])

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

  def test_parse_civil_date_rejects_impossible_days(self):
    # swe.julday silently rolls 31/4 or 30/2 into the next month; the API
    # must reject them instead of answering a different date.
    from webapp.day_panchanga import parse_civil_date
    for bad in ("31/04/2026", "30/02/2026", "29/02/2023", "00/01/2026", "32/01/2026", "01/13/2026"):
      with self.assertRaises(ValueError):
        parse_civil_date(bad)
    self.assertEqual(parse_civil_date("29/02/2024"), Date(2024, 2, 29))
    self.assertEqual(parse_civil_date("18/01/-3101"), Date(-3101, 1, 18))
    # Astronomical numbering: year 0 is 1 BCE, and a leap year.
    self.assertEqual(parse_civil_date("18/01/0"), Date(0, 1, 18))
    self.assertEqual(parse_civil_date("29/02/0"), Date(0, 2, 29))

  def test_out_of_range_years_are_client_errors(self):
    # Past the ephemeris (-13000) raised swisseph.Error, and a time in year
    # 10000 raised OverflowError: both answered 500 instead of 400.
    from webapp.app import app
    client = app.test_client()
    for date in ("01/01/-13000", "01/01/10000", "31/12/9999"):
      with self.subTest(date=date):
        response = client.get(f"/api/panchanga?city=Ujjain&date={date}")
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())
    # ICS keeps the PDF range: a year beyond 3300 is a 400 from the range
    # check, and the old YYYY-MM spelling is a 400 from the parser.
    response = client.get("/api/panchanga.ics?city=Ujjain&start=9999")
    self.assertEqual(response.status_code, 400)
    self.assertIn(b"out of range", response.data)


class DstClockTests(unittest.TestCase):
  """Day view: a Hindu-day tail crossing a DST change reads the clock."""

  def test_tithi_end_and_moonset_after_dst_start(self):
    # Helsinki 28 Mar 2026: the tithi ends 02:17 UT and the moon sets 03:15 UT
    # on the 29th, both after the 03:00 EET->EEST change. The stale +2 read
    # 28:17:xx and 29:15:xx; the clock says 29:17:xx and 30:15:xx.
    data = compute_day_panchanga("Helsinki", "28/03/2026")
    self.assertTrue(data["tithi"][0]["ends"].startswith("29:"))
    self.assertTrue(data["moonset"].startswith("30:"))


class PreStandardClockTests(unittest.TestCase):
  """Day view: before standard time, times read the place's own local mean time."""

  def test_bce_ujjain_sunrise_is_on_ujjain_mean_time(self):
    from generate_panchanga_calendar import load_location, place_for_date
    ujjain = load_location("Ujjain")
    civil = Date(-500, 6, 15)
    jd = gregorian_to_jd(civil)
    sunrise = panchanga.sunrise(jd, place_for_date(ujjain, civil))
    expected = format_local_hm(sunrise, ujjain.timezone_name, anchor_civil=civil, show_seconds=True,
                               longitude=ujjain.longitude)
    self.assertEqual(compute_day_panchanga("Ujjain", "15/06/-500")["sunrise"], expected)
