"""Contracts the shipped data files must keep.

Some code paths assume these properties instead of guarding against their
absence: ``resolve_city_key`` returns the one exact match it finds, and
``ekadashi_name`` indexes its lookup directly. These tests fail before a
data edit can silently change a calendar.
"""

import unittest

from generate_panchanga_calendar import city_locations, sanskrit_names


class CitiesJsonTests(unittest.TestCase):

  def test_no_keys_differ_only_by_case(self):
    folded = {}
    for key in city_locations():
      folded.setdefault(key.casefold(), []).append(key)
    clashes = {fold: names for fold, names in folded.items() if len(names) > 1}
    self.assertEqual(clashes, {}, "case-only duplicate keys make the exact city match ambiguous")


class SanskritNamesTests(unittest.TestCase):

  def test_every_month_has_both_ekadashi_names(self):
    ekadashis = sanskrit_names()["ekadashis"]
    for month in [str(number) for number in range(1, 13)] + ["adhika"]:
      self.assertIn(month, ekadashis, msg=month)
      for paksha in ("S", "K"):
        self.assertTrue(ekadashis[month].get(paksha), msg=f"{month}/{paksha}")


if __name__ == "__main__":
  unittest.main()
