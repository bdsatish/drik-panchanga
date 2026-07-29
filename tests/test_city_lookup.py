"""City key lookup accepts Name, ISO with or without a space after the comma."""

import unittest

from generate_panchanga_calendar import load_location, normalize_city_query


class CityLookupTests(unittest.TestCase):

    def test_normalize_inserts_space_and_uppercases_iso(self):
        self.assertEqual(normalize_city_query("helsinki,fi"), "helsinki, FI")
        self.assertEqual(normalize_city_query("Helsinki,  fi"), "Helsinki, FI")
        self.assertEqual(normalize_city_query("Bengaluru, IN"), "Bengaluru, IN")

    def test_load_location_accepts_missing_space(self):
        self.assertEqual(load_location("Helsinki,FI").name, "Helsinki, FI")
        self.assertEqual(load_location("bengaluru,in").name, "Bengaluru, IN")

    def test_ambiguous_bare_name_still_requires_country(self):
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            load_location("Sydney")
        self.assertEqual(load_location("Sydney,AU").name, "Sydney, AU")

    def test_former_multi_comma_geonames_are_plain_keys(self):
        # GeoNames AsciiNames used to embed commas (admin composites); geonames.py
        # stores only the leading place name so keys stay ``Name, ISO``.
        self.assertEqual(load_location("Mianzhu").name, "Mianzhu, CN")
        self.assertEqual(load_location("Misato").name, "Misato, JP")
        self.assertEqual(load_location("Misato,JP").name, "Misato, JP")


if __name__ == "__main__":
    unittest.main()
