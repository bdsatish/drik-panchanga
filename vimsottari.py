#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# vimsottari.py -- routines for computing time periods of vimsottari dasha
#
# Copyright (C) 2015 Satish BD  <bdsatish@gmail.com>
# Downloaded from https://github.com/bdsatish/drik-panchanga
#
# This file is part of the "drik-panchanga" Python library
# for computing Hindu luni-solar calendar based on the Swiss ephemeris
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Calculates Vimshottari (=120) Dasha-bhukti-antara-sukshma
"""

from __future__ import division
from math import ceil
import swisseph as swe
from collections import OrderedDict as Dict
from panchanga import sidereal_longitude, sidereal_year, get_planet_name

swe.KETU = swe.PLUTO  # I've mapped Pluto to Ketu
vimsottari_year = sidereal_year  # assume 365.25 days

# Nakshatra lords, order matters. See https://en.wikipedia.org/wiki/Dasha_(astrology)
adhipati_list = [ swe.KETU, swe.SUKRA, swe.SURYA, swe.CHANDRA, swe.KUJA,
                  swe.RAHU, swe.GURU, swe.SANI, swe.BUDHA ]

# (Maha-)dasha periods (in years)
mahadasa = { swe.KETU: 7, swe.SUKRA: 20, swe.SURYA: 6, swe.CHANDRA: 10, swe.KUJA: 7,
             swe.RAHU: 18, swe.GURU: 16, swe.SANI: 19, swe.BUDHA: 17 }

# assert(0 <= nak <= 26)
# Return nakshatra lord (adhipati)
adhipati = lambda nak: adhipati_list[nak % 9]  # 9 because len(adhipati_list)

def next_adhipati(lord):
    """Returns next guy in the adhipati_list"""
    # TODO: Use modulo arithmetic
    if lord == swe.KETU:    return swe.SUKRA
    if lord == swe.SUKRA:   return swe.SURYA
    if lord == swe.SURYA:   return swe.CHANDRA
    if lord == swe.CHANDRA: return swe.KUJA
    if lord == swe.KUJA:    return swe.RAHU
    if lord == swe.RAHU:    return swe.GURU
    if lord == swe.GURU:    return swe.SANI
    if lord == swe.SANI:    return swe.BUDHA
    if lord == swe.BUDHA:   return swe.KETU    # wrap around to Ketu

def nakshatra_position(jdut1):
    """Get the Nakshatra index and degrees traversed at a given JD(UT1) """
    moon = sidereal_longitude(jdut1, swe.MOON)
    one_star = (360 / 27.)        # 27 nakshatras span 360°
    nak = int(moon / one_star)    # 0..26
    rem = (moon - nak * one_star) # degrees traversed in given nakshatra

    return [nak, rem]

def dasha_start_date(jdut1):
    """Returns the start date (UT1) of the mahadasa which occured on or before `jd(UT1)`"""
    nak, rem = nakshatra_position(jdut1)
    one_star = (360 / 27.)        # 27 nakshatras span 360°
    lord = adhipati(nak)          # ruler of current nakshatra
    period = mahadasa[lord]       # total years of nakshatra lord
    period_elapsed = rem / one_star * period # years
    period_elapsed *= vimsottari_year        # days
    start_date = jdut1 - period_elapsed      # so many days before current day

    return [lord, start_date]

def vimsottari_mahadasa(jdut1):
    """List all mahadashas and their start dates"""
    lord, start_date = dasha_start_date(jdut1)
    retval = Dict()
    for i in range(9):
        retval[lord] = start_date
        start_date += mahadasa[lord] * vimsottari_year
        lord = next_adhipati(lord)

    return retval

def vimsottari_bhukti(maha_lord, start_date):
    """Compute all bhuktis of given nakshatra-lord of Mahadasa
    and its start date"""
    lord = maha_lord
    retval = Dict()
    for i in range(9):
        retval[lord] = start_date
        start_date += (mahadasa[lord] * mahadasa[maha_lord] / 120.) * vimsottari_year
        lord = next_adhipati(lord)

    return retval

# ---------------------- ALL TESTS ------------------------------
def adhipati_tests():
    # nakshatra indexes counted from 0
    satabhisha, citta, aslesha = 23, 13, 8
    assert(adhipati(satabhisha) == swe.RAHU)
    assert(mahadasa[adhipati(satabhisha)] == 18)
    assert(adhipati(citta) == swe.MARS)
    assert(mahadasa[adhipati(citta)] == 7)
    assert(adhipati(aslesha) == swe.MERCURY)
    assert(mahadasa[adhipati(aslesha)] == 17)


if __name__ == "__main__":
    adhipati_tests()
    # YYYY-MM-DD 09:40 IST = 04:10 UTC
    jdut1 = swe.utc_to_jd(1985, 6, 9, 4, 10, 0, flag = swe.GREG_CAL)[1]
    print("jdut1", jdut1)
    dashas = vimsottari_mahadasa(jdut1)
    for i in dashas:
        print(' ---------- ' + get_planet_name(i) + ' Dasa ---------- ')
        bhuktis = vimsottari_bhukti(i, dashas[i])
        for j in bhuktis:
            y, m, d, h = swe.revjul(bhuktis[j])
            print('%8s: %04d-%02d-%02d' % (get_planet_name(j), y, m, d))
