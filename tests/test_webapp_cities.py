"""City-search limit handling shared by Flask and CGI."""

import io
import sys
import unittest
from unittest import mock

from webapp import cgi_handlers
from webapp.app import app, city_search_limit


class CitySearchLimitTests(unittest.TestCase):

  def test_normalizes_invalid_and_out_of_range_values(self):
    cases = {
      "invalid": 20,
      "0": 1,
      "51": 50,
      "7": 7,
    }
    for raw_limit, expected in cases.items():
      with self.subTest(raw_limit=raw_limit):
        self.assertEqual(city_search_limit(raw_limit), expected)

  def test_flask_cities_uses_shared_limit_normalization(self):
    cases = {
      "invalid": 20,
      "0": 1,
      "51": 50,
      "7": 7,
    }
    for raw_limit, expected in cases.items():
      with self.subTest(raw_limit=raw_limit), \
              mock.patch("webapp.app.search_cities", return_value=[]) as search:
        response = app.test_client().get(f"/api/cities?q=test&limit={raw_limit}")
        self.assertEqual(response.status_code, 200)
        search.assert_called_once_with("test", limit=expected)

  def test_cgi_cities_uses_shared_limit_normalization(self):
    cases = {
      "invalid": 20,
      "0": 1,
      "51": 50,
      "7": 7,
    }
    for raw_limit, expected in cases.items():
      stdout = mock.Mock(buffer=io.BytesIO())
      with self.subTest(raw_limit=raw_limit), \
              mock.patch.object(cgi_handlers, "_query_params",
                                return_value={"q": ["test"], "limit": [raw_limit]}), \
              mock.patch.object(cgi_handlers, "search_cities", return_value=[]) as search, \
              mock.patch.object(sys, "stdout", stdout):
        cgi_handlers.handle_cities()
        search.assert_called_once_with("test", limit=expected)
