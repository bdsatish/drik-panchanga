#!/usr/bin/env python
# -*- coding: utf-8 -*-

# panchanga.py -- routines for computing tithi, vara, etc.
#
# Copyright (C) 2013 Satish Bysany
# Downloaded from https://bitbucket.org/satbyy/drik-panchanga
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
Use Swiss ephemeris to calculate tithi, nakshatra, etc.
"""

from __future__ import division
from math import ceil
from collections import namedtuple as struct
import swisseph as swe

Date = struct('Date', ['year', 'month', 'day'])
Place = struct('Place', ['latitude', 'longitude', 'timezone'])

sidereal_year = 365.256360417   # From WolframAlpha

# Hindu sunrise/sunset is calculated w.r.t middle of the sun's disk
# They are geometric, i.e. "true sunrise/set", so refraction is not considered
_rise_flags = swe.BIT_DISC_CENTER + swe.BIT_NO_REFRACTION

# namah suryaya chandraya mangalaya ... rahuve ketuve namah
swe.RAHU = swe.MEAN_NODE # Rahu = either MEAN_NODE or swe.TRUE_NODE
swe.KETU = swe.PLUTO  # I've mapped Pluto to Ketu
planet_list = [swe.SUN, swe.MOON, swe.MARS, swe.MERCURY, swe.JUPITER,
               swe.VENUS, swe.SATURN, swe.MEAN_NODE, # Rahu = MEAN_NODE
               swe.KETU, swe.URANUS, swe.NEPTUNE ]

revati_359_50 = lambda: swe.set_sid_mode(swe.SIDM_USER, 1926892.343164331, 0)
galc_cent_mid_mula = lambda: swe.set_sid_mode(swe.SIDM_USER, 1922011.128853056, 0)

# Possible ayanamas
# swe.SIDM_ALDEBARAN_15TAU     swe.SIDM_BABYL_HUBER         swe.SIDM_DJWHAL_KHUL         swe.SIDM_J2000               swe.SIDM_SASSANIAN             swe.SIDM_TRUE_CITRA
# swe.SIDM_ARYABHATA           swe.SIDM_BABYL_KUGLER1       swe.SIDM_FAGAN_BRADLEY       swe.SIDM_JN_BHASIN           swe.SIDM_SS_CITRA              swe.SIDM_TRUE_REVATI
# swe.SIDM_ARYABHATA_MSUN      swe.SIDM_BABYL_KUGLER2       swe.SIDM_GALCENT_0SAG        swe.SIDM_KRISHNAMURTI        swe.SIDM_SS_REVATI             swe.SIDM_USER
# swe.SIDM_B1950               swe.SIDM_BABYL_KUGLER3       swe.SIDM_HIPPARCHOS          swe.SIDM_LAHIRI              swe.SIDM_SURYASIDDHANTA        swe.SIDM_USHASHASHI
# swe.SIDM_BABYL_ETPSC         swe.SIDM_DELUCE              swe.SIDM_J1900               swe.SIDM_RAMAN               swe.SIDM_SURYASIDDHANTA_MSUN   swe.SIDM_YUKTESHWAR
set_ayanamsa_mode = lambda: swe.set_sid_mode(swe.SIDM_LAHIRI)
reset_ayanamsa_mode = lambda: swe.set_sid_mode(swe.SIDM_FAGAN_BRADLEY)

# Temporary function
def get_planet_name(planet):
  names = { swe.SUN: 'Surya', swe.MOON: 'Candra', swe.KUJA: 'Mangala',
            swe.MERCURY: 'Budha', swe.JUPITER: 'Guru', swe.VENUS: 'Sukra',
            swe.SATURN: 'Sani', swe.RAHU: 'Rahu', swe.KETU: 'Ketu', swe.PLUTO: 'Ketu'}
  return names[planet]

# Convert 23d 30' 30" to 23.508333 degrees
from_dms = lambda degs, mins, secs = 0: degs + mins/60 + secs/3600

# the inverse
def to_dms_prec(deg):
  d = int(deg)
  mins = (deg - d) * 60
  m = int(mins)
  s = round((mins - m) * 60, 6)
  return [d, m, s]

def to_dms(deg):
  d, m, s = to_dms_prec(deg)
  return [d, m, int(s)]

def unwrap_angles(angles):
  """Add 360 to those elements in the input list so that
     all elements are sorted in ascending order."""
  result = angles
  for i in range(1, len(angles)):
    if result[i] < result[i-1]: result[i] += 360

  assert(result == sorted(result))
  return result

# Make angle lie between [-180, 180) instead of [0, 360)
norm180 = lambda angle: (angle - 360) if angle >= 180 else angle;

# Make angle lie between [0, 360)
norm360 = lambda angle: angle % 360

# Ketu is always 180° after Rahu, so same coordinates but different constellations
# i.e if Rahu is in Pisces, Ketu is in Virgo etc
ketu = lambda rahu: (rahu + 180) % 360

# Set env variable SE_EPHE_PATH to /usr/share/libswe/ephe
swe.set_ephe_path('/usr/share/libswe/ephe')
init_swisseph = lambda: None

def function(point):
    swe.set_sid_mode(swe.SIDM_USER, point, 0.0)
    #swe.set_sid_mode(swe.SIDM_LAHIRI)
    # Place Revati at 359°50'
    #fval = norm180(swe.fixstar_ut("Revati", point, flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0][0]) - ((359 + 49/60 + 59/3600) - 360)
    # Place Revati at 0°0'0"
    #fval = norm180(swe.fixstar_ut("Revati", point, flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0][0])
    # Place Aldebaran in middle of Rohini (Rohini paksha ayanamsha)
    #fval = norm180(swe.fixstar_ut("Aldebaran", jd,  swe.FLG_SIDEREAL)[0][0] - (46+40/60))
    # Place Citra at 180°
    fval = swe.fixstar_ut("Citra", point, flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0][0] - (180)
    # Place Pushya (delta Cancri) at 106°
    # fval = swe.fixstar_ut(",deCnc", point, flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0][0] - (106)
    return fval

def bisection_search(func, start, stop):
  left = start
  right = stop
  epsilon = 5E-10   # Anything better than this puts the loop below infinite

  while True:
    middle = (left + right) / 2
    midval =  func(middle)
    rtval = func(right)
    if midval * rtval >= 0:
      right = middle
    else:
      left = middle

    if (right - left) <= epsilon: break

  return (right + left) / 2

def inverse_lagrange(x, y, ya):
  """Given two lists x and y, find the value of x = xa when y = ya, i.e., f(xa) = ya"""
  assert(len(x) == len(y))
  total = 0
  for i in range(len(x)):
    numer = 1
    denom = 1
    for j in range(len(x)):
      if j != i:
        numer *= (ya - y[j])
        denom *= (y[i] - y[j])

    total += numer * x[i] / denom

  return total

# Julian Day number as on (year, month, day) at 00:00 UTC
gregorian_to_jd = lambda date, hours = 0.0: swe.julday(date.year, date.month, date.day, hours)
jd_to_gregorian = lambda jd: swe.revjul(jd, swe.GREG_CAL)   # returns (y, m, d, h, min, s)

def local_time_to_jdut1(year, month, day, hour = 0, minutes = 0, seconds = 0, timezone = 0.0):
  """Converts local time to JD(UT1)"""
  y, m, d, h, mnt, s = swe.utc_time_zone(year, month, day, hour, minutes, seconds, timezone)
  # BUG in pyswisseph: replace 0 by s
  jd_et, jd_ut1 = swe.utc_to_jd(y, m, d, h, mnt, 0, cal = swe.GREG_CAL)
  return jd_ut1

def nakshatra_pada(longitude):
  """Gives nakshatra (1..27) and paada (1..4) in which given longitude lies"""
  # 27 nakshatras span 360°
  one_star = (360 / 27)  # = 13°20'
  # Each nakshatra has 4 padas, so 27 x 4 = 108 padas in 360°
  one_pada = (360 / 108) # = 3°20'
  quotient = int(longitude / one_star)
  reminder = (longitude - quotient * one_star)
  pada = int(reminder / one_pada)
  # convert 0..26 to 1..27 and 0..3 to 1..4
  return [1 + quotient, 1 + pada]

def sidereal_longitude(jd, planet, tropical = False):
  """Computes nirayana (sidereal) longitude of given planet on jd"""
  set_ayanamsa_mode()
  is_tropical = swe.FLG_TROPICAL if tropical else swe.FLG_SIDEREAL
  longi = swe.calc_ut(jd, planet, flags = swe.FLG_SWIEPH | is_tropical)
  reset_ayanamsa_mode()
  return norm360(longi[0][0]) # degrees

solar_longitude = lambda jd, tropical = False: sidereal_longitude(jd, swe.SUN, tropical)
lunar_longitude = lambda jd, tropical = False: sidereal_longitude(jd, swe.MOON, tropical)

def sunrise(jd, place):
  """Sunrise when centre of disc is at horizon for given date and place"""
  lat, lon, tz = place
  result = swe.rise_trans(jd - tz/24, swe.SUN, geopos = (lon, lat, 0), rsmi = _rise_flags + swe.CALC_RISE)
  rise = result[1][0]  # julian-day number
  # Convert to local time
  return [rise + tz/24., to_dms((rise - jd) * 24 + tz)]

def sunset(jd, place):
  """Sunset when centre of disc is at horizon for given date and place"""
  lat, lon, tz = place
  result = swe.rise_trans(jd - tz/24, swe.SUN, geopos = (lon, lat, 0), rsmi = _rise_flags + swe.CALC_SET)
  setting = result[1][0]  # julian-day number
  # Convert to local time
  return [setting + tz/24., to_dms((setting - jd) * 24 + tz)]

def moonrise(jd, place):
  """Moonrise when centre of disc is at horizon for given date and place"""
  lat, lon, tz = place
  result = swe.rise_trans(jd - tz/24, swe.MOON, geopos = (lon, lat, 0), rsmi = _rise_flags + swe.CALC_RISE)
  rise = result[1][0]  # julian-day number
  # Convert to local time
  return to_dms((rise - jd) * 24 + tz)

def moonset(jd, place):
  """Moonset when centre of disc is at horizon for given date and place"""
  lat, lon, tz = place
  result = swe.rise_trans(jd - tz/24, swe.MOON, geopos = (lon, lat, 0), rsmi = _rise_flags + swe.CALC_SET)
  setting = result[1][0]  # julian-day number
  # Convert to local time
  return to_dms((setting - jd) * 24 + tz)

# Tithi doesn't depend on Ayanamsa
def tithi(jd, place):
  """Tithi at sunrise for given date and place. Also returns tithi's end time."""
  tz = place.timezone
  # 1. Find time of sunrise
  rise = sunrise(jd, place)[0] - tz / 24

  # 2. Find tithi at this JDN
  moon_phase = lunar_phase(rise)
  today = ceil(moon_phase / 12)
  degrees_left = today * 12 - moon_phase

  # 3. Compute longitudinal differences at intervals of 0.25 days from sunrise
  offsets = [0.25, 0.5, 0.75, 1.0]
  lunar_long_diff = [ (lunar_longitude(rise + t) - lunar_longitude(rise)) % 360 for t in offsets ]
  solar_long_diff = [ (solar_longitude(rise + t) - solar_longitude(rise)) % 360 for t in offsets ]
  relative_motion = [ moon - sun for (moon, sun) in zip(lunar_long_diff, solar_long_diff) ]

  # 4. Find end time by 4-point inverse Lagrange interpolation
  y = relative_motion
  x = offsets
  # compute fraction of day (after sunrise) needed to traverse 'degrees_left'
  approx_end = inverse_lagrange(x, y, degrees_left)
  ends = (rise + approx_end - jd) * 24 + tz
  answer = [int(today), to_dms(ends)]

  # 5. Check for skipped tithi
  moon_phase_tmrw = lunar_phase(rise + 1)
  tomorrow = ceil(moon_phase_tmrw / 12)
  isSkipped = (tomorrow - today) % 30 > 1
  if isSkipped:
    # interpolate again with same (x,y)
    leap_tithi = today + 1
    degrees_left = leap_tithi * 12 - moon_phase
    approx_end = inverse_lagrange(x, y, degrees_left)
    ends = (rise + approx_end -jd) * 24 + place.timezone
    leap_tithi = 1 if today == 30 else leap_tithi
    answer += [int(leap_tithi), to_dms(ends)]

  return answer


def nakshatra(jd, place):
  """Current nakshatra as of julian day (jd)
     1 = Asvini, 2 = Bharani, ..., 27 = Revati
  """
  # 1. Find time of sunrise
  lat, lon, tz = place
  rise = sunrise(jd, place)[0] - tz / 24.  # Sunrise at UT 00:00

  offsets = [0.0, 0.25, 0.5, 0.75, 1.0]
  longitudes = [ lunar_longitude(rise + t) for t in offsets]

  # 2. Today's nakshatra is when offset = 0
  # There are 27 Nakshatras spanning 360 degrees
  nak = ceil(longitudes[0] * 27 / 360)

  # 3. Find end time by 5-point inverse Lagrange interpolation
  y = unwrap_angles(longitudes)
  x = offsets
  approx_end = inverse_lagrange(x, y, nak * 360 / 27)
  ends = (rise - jd + approx_end) * 24 + tz
  answer = [int(nak), to_dms(ends)]

  # 4. Check for skipped nakshatra
  nak_tmrw = ceil(longitudes[-1] * 27 / 360)
  isSkipped = (nak_tmrw - nak) % 27 > 1
  if isSkipped:
    leap_nak = nak + 1
    approx_end = inverse_lagrange(offsets, longitudes, leap_nak * 360 / 27)
    ends = (rise - jd + approx_end) * 24 + tz
    leap_nak = 1 if nak == 27 else leap_nak
    answer += [int(leap_nak), to_dms(ends)]

  return answer


def yoga(jd, place):
  """Yoga at given jd and place.
     1 = Vishkambha, 2 = Priti, ..., 27 = Vaidhrti
  """
  # 1. Find time of sunrise
  lat, lon, tz = place
  rise = sunrise(jd, place)[0] - tz / 24.  # Sunrise at UT 00:00

  # 2. Find the Nirayana longitudes and add them
  lunar_long = lunar_longitude(rise)
  solar_long = solar_longitude(rise)
  total = (lunar_long + solar_long) % 360
  # There are 27 Yogas spanning 360 degrees
  yog = ceil(total * 27 / 360)

  # 3. Find how many longitudes is there left to be swept
  degrees_left = yog * (360 / 27) - total

  # 3. Compute longitudinal sums at intervals of 0.25 days from sunrise
  offsets = [0.25, 0.5, 0.75, 1.0]
  lunar_long_diff = [ (lunar_longitude(rise + t) - lunar_longitude(rise)) % 360 for t in offsets ]
  solar_long_diff = [ (solar_longitude(rise + t) - solar_longitude(rise)) % 360 for t in offsets ]
  total_motion = [ moon + sun for (moon, sun) in zip(lunar_long_diff, solar_long_diff) ]

  # 4. Find end time by 4-point inverse Lagrange interpolation
  y = total_motion
  x = offsets
  # compute fraction of day (after sunrise) needed to traverse 'degrees_left'
  approx_end = inverse_lagrange(x, y, degrees_left)
  ends = (rise + approx_end - jd) * 24 + tz
  answer = [int(yog), to_dms(ends)]

  # 5. Check for skipped yoga
  lunar_long_tmrw = lunar_longitude(rise + 1)
  solar_long_tmrw = solar_longitude(rise + 1)
  total_tmrw = (lunar_long_tmrw + solar_long_tmrw) % 360
  tomorrow = ceil(total_tmrw * 27 / 360)
  isSkipped = (tomorrow - yog) % 27 > 1
  if isSkipped:
    # interpolate again with same (x,y)
    leap_yog = yog + 1
    degrees_left = leap_yog * (360 / 27) - total
    approx_end = inverse_lagrange(x, y, degrees_left)
    ends = (rise + approx_end - jd) * 24 + tz
    leap_yog = 1 if yog == 27 else leap_yog
    answer += [int(leap_yog), to_dms(ends)]

  return answer


def karana(jd, place):
  """Returns the karana and their ending times. (from 1 to 60)"""
  tz = place.timezone
  # 1. Find time of sunrise
  rise = sunrise(jd, place)[0]

  # 2. Find karana at this JDN
  moon_phase = lunar_phase(rise)
  today = ceil(moon_phase / 6)
  degrees_left = today * 6 - moon_phase

  # 3. Compute longitudinal differences at intervals of 0.25 days from sunrise
  offsets = [0.25, 0.5, 0.75, 1.0]
  lunar_long_diff = [ (lunar_longitude(rise + t) - lunar_longitude(rise)) % 360 for t in offsets ]
  solar_long_diff = [ (solar_longitude(rise + t) - solar_longitude(rise)) % 360 for t in offsets ]
  relative_motion = [ moon - sun for (moon, sun) in zip(lunar_long_diff, solar_long_diff) ]

  # 4. Find end time by 4-point inverse Lagrange interpolation
  y = relative_motion
  x = offsets
  # compute fraction of day (after sunrise) needed to traverse 'degrees_left'
  approx_end = inverse_lagrange(x, y, degrees_left)
  ends = (rise + approx_end - jd) * 24 + tz
  answer = [int(today), to_dms(ends)]
  
  return answer

def vaara(jd):
  """Weekday for given Julian day. 0 = Sunday, 1 = Monday,..., 6 = Saturday"""
  return int(ceil(jd + 1) % 7)

def masa(jd, place, amanta = True):
  """Returns lunar month and if it is adhika or not.
     Set amanta = False for Purnimanta month.
     1 = Chaitra, 2 = Vaisakha, ..., 12 = Phalguna"""
  ti = tithi(jd, place)[0]
  critical = sunrise(jd, place)[0]  # - tz/24 ?
  last_moon = new_moon(critical, ti, -1) if amanta else full_moon(critical, ti, -1)
  next_moon = new_moon(critical, ti, +1) if amanta else full_moon(critical, ti, +1)
  this_solar_month = raasi(last_moon)
  next_solar_month = raasi(next_moon)
  is_leap_month = (this_solar_month == next_solar_month)
  if amanta:
    maasa = this_solar_month + 1
  else:
    maasa = 1 if (this_solar_month == 10 and ti >= 15) else this_solar_month + 2
  if maasa > 12: maasa = (maasa % 12)
  return [int(maasa), is_leap_month]

# epoch-midnight to given midnight
# Days elapsed since beginning of Kali Yuga
ahargana = lambda jd: jd - 588465.5

def elapsed_year(jd, maasa_num):
  ahar = ahargana(jd)  # or (jd + sunrise(jd, place)[0])
  kali = int((ahar + (4 - maasa_num) * 30) / sidereal_year)
  saka = kali - 3179
  vikrama = saka + 135
  return kali, saka

# New moon day: sun and moon have same longitude (0 degrees = 360 degrees difference)
def new_moon(jd, tithi_, opt = -1):
  """Returns JDN, where
     opt = -1:  JDN < jd such that lunar_phase(JDN) = 360 degrees
     opt = +1:  JDN >= jd such that lunar_phase(JDN) = 360 degrees
  """
  if opt == -1:  start = jd - tithi_         # previous new moon
  if opt == +1:  start = jd + (30 - tithi_)  # next new moon
  # Search within a span of (start +- 2) days
  x = [ -2 + offset/4 for offset in range(17) ]
  y = [lunar_phase(start + i) for i in x]
  y = unwrap_angles(y)
  y0 = inverse_lagrange(x, y, 360)
  return start + y0

# assumes "tithi" 1..30 are from new moon to new moon
# so tithi = 15 is full moon day
# Full moon day: sun and moon are 180 deg apart
def full_moon(jd, tithi_, opt = -1):
  """Returns JDN, where
     opt = -1:  JDN < jd such that lunar_phase(JDN) = 180 degrees
     opt = +1:  JDN >= jd such that lunar_phase(JDN) = 180 degrees
  """
  if opt == -1:    # previous full moon
    start = jd - (tithi_ - 15) if tithi_ > 15 else jd - (tithi_ + 15)
  if opt == +1:   # next full moon
    start = jd + (15 - tithi_) if tithi_ < 15 else jd - tithi_ + 45
  # Search within a span of (start +- 2) days
  x = [ -2 + offset/4 for offset in range(17) ]
  y = [lunar_phase(start + i) for i in x]
  y = unwrap_angles(y)
  y0 = inverse_lagrange(x, y, 180)
  return start + y0

def raasi(jd):
  """Zodiac of given jd. 1 = Mesha, ... 12 = Meena"""
  s = solar_longitude(jd)
  solar_nirayana = solar_longitude(jd)
  # 12 rasis occupy 360 degrees, so each one is 30 degrees
  return ceil(solar_nirayana / 30.)

def lunar_phase(jd):
  solar_long = solar_longitude(jd)
  lunar_long = lunar_longitude(jd)
  moon_phase = (lunar_long - solar_long) % 360
  return moon_phase

def samvatsara(jd, maasa_num):
  kali = elapsed_year(jd, maasa_num)[0]
  # Change 14 to 0 for North Indian tradition
  # See the function "get_Jovian_Year_name_south" in pancanga.pl
  if kali >= 4009:    kali = (kali - 14) % 60
  samvat = (kali + 27 + int((kali * 211 - 108) / 18000)) % 60
  return samvat

def ritu(masa_num):
  """0 = Vasanta,...,5 = Shishira"""
  return (masa_num - 1) // 2

def day_duration(jd, place):
  srise = sunrise(jd, place)[0]  # julian day num
  sset = sunset(jd, place)[0]    # julian day num
  diff = (sset - srise) * 24     # In hours
  return [diff, to_dms(diff)]

# The day duration is divided into 8 parts
# Similarly night duration
def gauri_chogadiya(jd, place):
  lat, lon, tz = place
  tz = place.timezone
  srise = swe.rise_trans(jd - tz/24, swe.SUN, geopos = (lon, lat, 0), rsmi = _rise_flags + swe.CALC_RISE)[1][0]
  sset = swe.rise_trans(jd - tz/24, swe.SUN, geopos = (lon, lat, 0), rsmi = _rise_flags + swe.CALC_SET)[1][0]
  day_dur = (sset - srise)

  end_times = []
  for i in range(1, 9):
    end_times.append(to_dms((srise + (i * day_dur) / 8 - jd) * 24 + tz))

  # Night duration = time from today's sunset to tomorrow's sunrise
  srise = swe.rise_trans((jd + 1) - tz/24, swe.SUN, geopos = (lon, lat, 0), rsmi = _rise_flags + swe.CALC_RISE)[1][0]
  night_dur = (srise - sset)
  for i in range(1, 9):
    end_times.append(to_dms((sset + (i * night_dur) / 8 - jd) * 24 + tz))

  return end_times

def trikalam(jd, place, option='rahu'):
  lat, lon, tz = place
  tz = place.timezone
  srise = swe.rise_trans(jd - tz/24, swe.SUN, geopos = (lon, lat, 0), rsmi = _rise_flags + swe.CALC_RISE)[1][0]
  sset = swe.rise_trans(jd - tz/24, swe.SUN, geopos = (lon, lat, 0), rsmi = _rise_flags + swe.CALC_SET)[1][0]
  day_dur = (sset - srise)
  weekday = vaara(jd)

  # value in each array is for given weekday (0 = sunday, etc.)
  offsets = { 'rahu': [0.875, 0.125, 0.75, 0.5, 0.625, 0.375, 0.25],
              'gulika': [0.75, 0.625, 0.5, 0.375, 0.25, 0.125, 0.0],
              'yamaganda': [0.5, 0.375, 0.25, 0.125, 0.0, 0.75, 0.625] }

  start_time = srise + day_dur * offsets[option][weekday]
  end_time = start_time + 0.125 * day_dur

  # to local timezone
  start_time = (start_time - jd) * 24 + tz
  end_time = (end_time - jd) * 24 + tz
  return [to_dms(start_time), to_dms(end_time)] # decimal hours to H:M:S

rahu_kalam = lambda jd, place: trikalam(jd, place, 'rahu')
yamaganda_kalam = lambda jd, place: trikalam(jd, place, 'yamaganda')
gulika_kalam = lambda jd, place: trikalam(jd, place, 'gulika')

def durmuhurtam(jd, place):
  lat, lon, tz = place
  tz = place.timezone

  # Night = today's sunset to tomorrow's sunrise
  sset = swe.rise_trans(jd - tz/24, swe.SUN, geopos = (lon, lat, 0), rsmi = _rise_flags + swe.CALC_SET)[1][0]
  srise = swe.rise_trans((jd + 1) - tz/24, swe.SUN, geopos = (lon, lat, 0), rsmi = _rise_flags + swe.CALC_RISE)[1][0]
  night_dur = (srise - sset)

  # Day = today's sunrise to today's sunset
  srise = swe.rise_trans(jd - tz/24, swe.SUN, geopos = (lon, lat, 0), rsmi = _rise_flags + swe.CALC_RISE)[1][0]
  day_dur = (sset - srise)

  weekday = vaara(jd)

  # There is one durmuhurtam on Sun, Wed, Sat; the rest have two
  offsets = [[10.4, 0.0],  # Sunday
             [6.4, 8.8],   # Monday
             [2.4, 4.8],   # Tuesday, [day_duration , night_duration]
             [5.6, 0.0],   # Wednesday
             [4.0, 8.8],   # Thursday
             [2.4, 6.4],   # Friday
             [1.6, 0.0]]   # Saturday

  # second durmuhurtam of tuesday uses night_duration instead of day_duration
  dur = [day_dur, day_dur]
  base = [srise, srise]
  if weekday == 2:  dur[1] = night_dur; base[1] = sset

  # compute start and end timings
  start_times = [0, 0]
  end_times = [0, 0]
  for i in range(0, 2):
    offset = offsets[weekday][i]
    if offset != 0.0:
      start_times[i] = base[i] + dur[i] * offsets[weekday][i] / 12
      end_times[i] = start_times[i] + day_dur * 0.8 / 12

      # convert to local time
      start_times[i] = (start_times[i] - jd) * 24 + tz
      end_times[i] = (end_times[i] - jd) * 24 + tz

  return [start_times, end_times]  # in decimal hours

def abhijit_muhurta(jd, place):
  """Abhijit muhurta is the 8th muhurta (middle one) of the 15 muhurtas
  during the day_duration (~12 hours)"""
  lat, lon, tz = place
  tz = place.timezone
  srise = swe.rise_trans(jd - tz/24, swe.SUN, geopos = (lon, lat, 0), rsmi = _rise_flags + swe.CALC_RISE)[1][0]
  sset = swe.rise_trans(jd - tz/24, swe.SUN, geopos = (lon, lat, 0), rsmi = _rise_flags + swe.CALC_SET)[1][0]
  day_dur = (sset - srise)

  start_time = srise + 7 / 15 * day_dur
  end_time = srise + 8 / 15 * day_dur

  # to local time
  return [(start_time - jd) * 24 + tz, (end_time - jd) * 24 + tz]

# 'jd' can be any time: ex, 2015-09-19 14:20 UTC
# today = swe.julday(2015, 9, 19, 14 + 20./60)
def planetary_positions(jd, place):
  """Computes instantaneous planetary positions
     (i.e., which celestial object lies in which constellation)

     Also gives the nakshatra-pada division
   """
  jd_ut = jd - place.timezone / 24.

  positions = []
  for planet in planet_list:
    if planet != swe.KETU:
      nirayana_long = sidereal_longitude(jd_ut, planet)
    else: # Ketu
      nirayana_long = ketu(sidereal_longitude(jd_ut, swe.RAHU))

    # 12 zodiac signs span 360°, so each one takes 30°
    # 0 = Mesha, 1 = Vrishabha, ..., 11 = Meena
    constellation = int(nirayana_long / 30)
    coordinates = to_dms(nirayana_long % 30)
    positions.append([planet, constellation, coordinates, nakshatra_pada(nirayana_long)])

  return positions

def ascendant(jd, place):
  """Lagna (=ascendant) calculation at any given time & place"""
  lat, lon, tz = place
  jd_utc = jd - (tz / 24.)
  set_ayanamsa_mode() # needed for swe.houses_ex()

  # returns two arrays, cusps and ascmc, where ascmc[0] = Ascendant
  nirayana_lagna = swe.houses_ex(jd_utc, lat, lon, flags = swe.FLG_SIDEREAL)[1][0]
  # 12 zodiac signs span 360°, so each one takes 30°
  # 0 = Mesha, 1 = Vrishabha, ..., 11 = Meena
  constellation = int(nirayana_lagna / 30)
  coordinates = to_dms(nirayana_lagna % 30)

  reset_ayanamsa_mode()
  return [constellation, coordinates, nakshatra_pada(nirayana_lagna)]

# http://www.oocities.org/talk2astrologer/LearnAstrology/Details/Navamsa.html
# Useful for making D9 divisional chart
def navamsa_from_long(longitude):
  """Calculates the navamsa-sign in which given longitude falls
  0 = Aries, 1 = Taurus, ..., 11 = Pisces
  """
  one_pada = (360 / (12 * 9))  # There are also 108 navamsas
  one_sign = 12 * one_pada    # = 40 degrees exactly
  signs_elapsed = longitude / one_sign
  fraction_left = signs_elapsed % 1
  return int(fraction_left * 12)

def navamsa(jd, place):
  """Calculates navamsa of all planets"""
  jd_utc = jd - place.timezone / 24.

  positions = []
  for planet in planet_list:
    if planet != swe.KETU:
      nirayana_long = sidereal_longitude(jd_utc, planet)
    else: # Ketu
      nirayana_long = ketu(sidereal_longitude(jd_utc, swe.RAHU))

    positions.append([planet, navamsa_from_long(nirayana_long)])

  return positions

# ----- TESTS ------
def all_tests():
  print(sys._getframe().f_code.co_name)
  print(moonrise(date2, bangalore)) # Expected: 11:32:04
  print(moonset(date2, bangalore))  # Expected: 24:8:47
  print(sunrise(date2, bangalore)[1])  # Expected:  6:49:47
  print(sunset(date2, bangalore)[1])   # Expected: 18:10:25
  assert(vaara(date2) == 5)
  print(sunrise(date4, shillong)[1])   # On this day, Nakshatra and Yoga are skipped!
  assert(karana(date2, helsinki) == [14])   # Expected: 14, Vanija
  return

def tithi_tests():
  print(sys._getframe().f_code.co_name)
  feb3 = gregorian_to_jd(Date(2013, 2, 3))
  apr24 = gregorian_to_jd(Date(2010, 4, 24))
  apr19 = gregorian_to_jd(Date(2013, 4, 19))
  apr20 = gregorian_to_jd(Date(2013, 4, 20))
  apr21 = gregorian_to_jd(Date(2013, 4, 21))
  print(tithi(date1, bangalore))  # Expected: krishna ashtami (23), ends at 27:07:38
  print(tithi(date2, bangalore))  # Expected: Saptami, ends at 16:24:19
  print(tithi(date3, bangalore))  # Expected: Krishna Saptami, ends at 25:03:30
  print(tithi(date2, helsinki))   # Expected: Shukla saptami until 12:54:19
  print(tithi(apr24, bangalore))  # Expected: [10, [6,9,29], 11, [27, 33, 58]]
  print(tithi(feb3, bangalore))   # Expected: [22, [8,14,6], 23, [30, 33, 17]]
  print(tithi(apr19, helsinki))   # Expected: [9, [28, 45, 0]]
  print(tithi(apr20, helsinki))   # Expected: [10, [29, 22, 7]]
  print(tithi(apr21, helsinki))   # Expected: [10, [5, 22, 6]]
  return

def nakshatra_tests():
  print(sys._getframe().f_code.co_name)
  print(nakshatra(date1, bangalore))  # Expected: 27 (Revati), ends at 17:06:37
  print(nakshatra(date2, bangalore))  # Expected: 27 (Revati), ends at 19:23:09
  print(nakshatra(date3, bangalore))  # Expecred: 24 (Shatabhisha) ends at 26:32:43
  print(nakshatra(date4, shillong))   # Expected: [3, [5,1,14]] then [4,[26,31,13]]
  return

def yoga_tests():
  print(sys._getframe().f_code.co_name)
  may22 = gregorian_to_jd(Date(2013, 5, 22))
  print(yoga(date3, bangalore))  # Expected: Vishkambha (1), ends at 22:59:45
  print(yoga(date2, bangalore))  # Expected: Siddha (21), ends at 29:10:56
  print(yoga(may22, helsinki))   # [16, [6,20,33], 17, [27,21,58]]

def masa_tests():
  print(sys._getframe().f_code.co_name)
  jd = gregorian_to_jd(Date(2013, 2, 10))
  aug17 = gregorian_to_jd(Date(2012, 8, 17))
  aug18 = gregorian_to_jd(Date(2012, 8, 18))
  sep19 = gregorian_to_jd(Date(2012, 9, 18))
  may20 = gregorian_to_jd(Date(2012, 5, 20))
  may21 = gregorian_to_jd(Date(2012, 5, 21))
  print(masa(jd, bangalore))     # Pusya (10)
  print(masa(aug17, bangalore))  # Shravana (5) amavasya
  print(masa(aug18, bangalore))  # Adhika Bhadrapada [6, True]
  print(masa(sep19, bangalore))  # Normal Bhadrapada [6, False]
  print(masa(may20, helsinki))   # Vaisakha [2]
  print(masa(may21, helsinki))   # Jyestha [3]
  apr17 = gregorian_to_jd(Date(2023, 4, 17)) # Purnimanta Vaisakha K12
  assert(masa(apr17, bangalore, amanta = False) == [2, False]) # Vaisakha
  assert(masa(apr17, bangalore, amanta = True) == [1, False]) # Caitra
  may21 = gregorian_to_jd(Date(2023, 5, 21)) # Jyeshtha S2
  assert(masa(may21, bangalore, amanta = False) == [3, False])
  assert(masa(may21, bangalore, amanta = True) == [3, False])
  feb21 = gregorian_to_jd(Date(2023, 2, 21)) # Phalguna S2
  assert(masa(feb21, bangalore, amanta = False) == [12, False])
  assert(masa(feb21, bangalore, amanta = True) == [12, False])
  mar15 = gregorian_to_jd(Date(2023, 3, 15)) # Phalguna K8 (amanta), Caitra K3 (purnimanta)
  assert(masa(mar15, bangalore, amanta = True) == [12, False])
  assert(masa(mar15, bangalore, amanta = False) == [1, False])

def ascendant_tests():
  print(sys._getframe().f_code.co_name)
  jd = swe.julday(2015, 9, 24, 23 + 38/60.)
  assert(ascendant(jd, bangalore) == [2, [4, 37, 10], [5, 4]])
  jd = swe.julday(2015, 9, 25, 13 + 29/60. + 13/3600.)
  assert(ascendant(jd, bangalore) == [8, [20, 23, 31], [20, 3]])

def navamsa_tests():
  print(sys._getframe().f_code.co_name)
  jd = swe.julday(2015, 9, 25, 13 + 29/60. + 13/3600.)
  nv = navamsa(jd, bangalore)
  expected = [[0, 11], [1, 5], [4, 1], [2, 2], [5, 4], [3, 10],
              [6, 4], [10, 11], [9, 5], [7, 10], [8, 10]]
  assert(nv == expected)


if __name__ == "__main__":
  import sys
  bangalore = Place(12.972, 77.594, +5.5)
  shillong = Place(25.569, 91.883, +5.5)
  helsinki = Place(60.17, 24.935, +2.0)
  date1 = gregorian_to_jd(Date(2009, 7, 15))
  date2 = gregorian_to_jd(Date(2013, 1, 18))
  date3 = gregorian_to_jd(Date(1985, 6, 9))
  date4 = gregorian_to_jd(Date(2009, 6, 21))
  apr_8 = gregorian_to_jd(Date(2010, 4, 8))
  apr_10 = gregorian_to_jd(Date(2010, 4, 10))
  all_tests()
  tithi_tests()
  nakshatra_tests()
  yoga_tests()
  masa_tests()
  ascendant_tests()
  navamsa_tests()
  # new_moon(jd)
