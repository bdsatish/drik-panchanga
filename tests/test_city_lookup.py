"""City key lookup accepts Name, ISO with or without a space after the comma."""

import unittest

from generate_panchanga_calendar import city_locations, load_location, normalize_city_query


class CityLookupTests(unittest.TestCase):

    def setUp(self):
        city_locations.cache_clear()

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

    def test_city_locations_cached_across_load_location(self):
        """Fresh requests must not re-parse the 1.3 MB cities.json."""
        city_locations.cache_clear()
        load_location("Bengaluru, IN")
        self.assertEqual(city_locations.cache_info().misses, 1)
        load_location("Helsinki, FI")
        load_location("Bengaluru, IN")
        self.assertEqual(city_locations.cache_info().misses, 1)
        self.assertEqual(city_locations.cache_info().hits, 2)
