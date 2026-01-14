from panchanga import *

def solstice(jd, opt = +1):
    """Finds the julian day of previous occurence of
    winter solstice (opt = +1) or summer solstice (opt = -1)."""
    if opt == -1:  sun_longitude =  90 # degrees, summer solstice
    if opt == +1:  sun_longitude = 270 # degrees, winter solstice
    flag = swe.FLG_SWIEPH | swe.FLG_TROPICAL # NOT sidereal!
    # Search in a span of 400 days before today
    start = jd - 400
    stop = jd + 25
    while stop >= start:
        longi = swe.calc_ut(stop, swe.SUN, flags = flag)[0][0]
        # difference less than 0.0005 degrees
        if abs(longi - sun_longitude) <= 5E-3:
            return stop
        stop -= 1E-2
    return None

def vedic_month(jd, place):
    uttarayana_moment = solstice(jd, +1)
    print(jd_to_gregorian(uttarayana_moment))
    lunar_month = 29.530589 # days
    month = ceil(abs(jd - uttarayana_moment) / lunar_month)
    ti = tithi(jd, place)[0]
    critical = sunrise(jd, place)[0]  # - tz/24 ?
    next_new_moon = new_moon(critical, ti, +1)
    if jd < next_new_moon: month = 12
    return month

# Following function should give almost the same result as sidereal nakshatra,
# but we don't use the swe.FLG_SIDEREAL at all! Idea is like this:
# 1. Find the tropical longitude of Ashvini nakshatra on given day (jd)
# 2. Calculate longitude of the rest of the fixed stars by successively adding 13°20'
# 3. Do a linear search to find in which interval of the above does 'longi' lie
def tropical_long_fixed_stars(jd, longi):
    """Returns nakshatra of an object's longitude `longi' on a given `jd' day
    1 = Ashvini, ..., 27 = Revati"""
    # other potential are Magha, Pushya, Satabhisha, Mrigashira, Revati, etc.
    # 1. Very bright apparent magnitude
    # 2. Latitude close to ecliptic
    # 3. Only main star in the "Lunar mansion" of 13°20'
    # 4. Very low proper motion
    # 5. Distance to next adjacent star is around 13° or 14°
    spica = swe.fixstar_ut("Spica", jd, flags = swe.FLG_TROPICAL | swe.FLG_SWIEPH)[0][0]
    # Ashvini nakshatra starts exactly 180° opposite of Citra (results exactly match TRUE_CITRA)
    ashvini_start = spica - 180
    # list like [ 23°, 36.33°, 49.66° ... ], each element 13°20' apart
    equal_spacing = [ norm360(ashvini_start + n * from_dms(13, 20)) for n in range(0, 27) ]
    # dict like { 1:23°, 2:36.33°, 3:49.66°, ... 26:356°, 27:10.66° }
    # where 1 to 27 are indexes to coordinates
    index_mapping = dict(zip(range(1, 28), equal_spacing))
    # arrange dict in descending order of coordinates (not indexes 1..27)
    # dict like { 26:356°, ..., 2:36.33°, 1:23°, 27:10.66° }
    sorted_mapping = dict(sorted(index_mapping.items(), key = lambda item: item[1], reverse = True))
    nak = None
    for key in sorted_mapping:
        if norm360(longi) > sorted_mapping[key]:
            nak = key
            break
    # residue after last element in dict, wraps around to first one
    keys = list(sorted_mapping.keys())
    if nak is None: nak = keys[0]
    prev = keys[keys.index(nak) - 1] # find key of item before 'nak'
    nak_end = sorted_mapping[prev]
    return nak, nak_end

def find_nakshatra_garga(longi):
    """Given longitude of any celestial object, determine which lunar mansion
    it falls under, as per Garga system (unequal nakshatra division)
    1 = Asvini,..., 27 = Revati"""
    # ending longitudes of 27 nakshatras. Normally it is 13°20'
    # Following Garga system is from Sewell and Dikshit. It starts with Ashvini nak as 0°0'
    # However, as observed today in sky, vernal equinox (Mar 21) starts when Sun is
    # at U.Bhadra every year, so:
    # 1. Ravi Prakrash Arya starts offset from U.Bhadra with equal spacing https://www.youtube.com/Hnj2ttPLQNQ?t=5244
    # 2. SMKAP starts from U.Bhadra with some part of it (unequal tropical spacing) pg 35 of smkap.pdf
    spacing = [ 13+20/60, 20, 33+20/60, 53+20/60, 66+40/60, 73+20/60, 93+20/60,
                106+40/60, 113+20/60, 126+40/60, 140, 160, 173+20/60, 186+40/60,
                193+20/60, 213+20/60, 226+40/60, 233+20/60, 246+40/60, 260, 280,
                293+20/60, 306+40/60, 313+20/60, 326+40/60, 346+40/60, 360]
    for i in range(0, len(spacing) + 1):
        if norm360(longi) < spacing[i]:
            return i%27, spacing[i%27]

def tropical_lunar_longitude(jd):
    longi = swe.calc_ut(jd, swe.MOON, flags = swe.FLG_SWIEPH | swe.FLG_TROPICAL)
    return norm360(longi[0][0])

def tropical_solar_longitude(jd):
    longi = swe.calc_ut(jd, swe.SUN, flags = swe.FLG_SWIEPH | swe.FLG_TROPICAL)
    return norm360(longi[0][0])

def tropical_raasi(jd):
    """Tropical (sayana) rasi of sun on given day. 1 = Aries,...,12 = Pisces (tropical)"""
    longi = swe.calc_ut(jd, swe.SUN, flags = swe.FLG_SWIEPH | swe.FLG_TROPICAL)[0][0]
    return ceil(longi / 30)

# rename = True will give lunar "masa" almost exactly same result as
# sidereal calendar. Advantages:
# - Vernal equinox mostly occur in the month of Caitra?
# - The lunar month name will have purnima on namesake star (e.g. Caitra māsa on Citrā nak.)
# - All popular festivals will coincide with sidereal calendar
# - Magha occurs around February, coinciding with Vasanta Ritu
# - Caitra around April, and New Year, coinciding with Grishma Ritu
# Basically this adds 1 month to whatever value "tropical (sayana)" month as given by
# Jagannath Hora and Sammod Acharya (rename = False).
# rename = True prints so that Pushya masa will be renamed to Margashirsha
def tropical_month_tithi(jd, place, rename = False):
    """Tropical (sayana) month and tithi. 1 = Caitra,...,12 = Phalguna"""
    ti = tithi(jd, place)  # does not depend on tropical or sidereal
    critical = sunrise(jd, place)[0]  # - tz/24 ?
    last_new_moon = new_moon(critical, ti[0], -1) # doesn't depend on ayanamsa
    next_new_moon = new_moon(critical, ti[0], +1) # doesn't depend on ayanamsa
    this_solar_month = tropical_raasi(last_new_moon)
    next_solar_month = tropical_raasi(next_new_moon)
    is_leap_month = (this_solar_month == next_solar_month)
    # Solar month is normally lunar month, adjusted for leap month.
    # There cannot be any leap months in solar calendar!
    maasa = this_solar_month
    if not rename: maasa += 1  # Like in sidereal
    if maasa > 12: maasa = (maasa % 12)
    return [[int(maasa), is_leap_month], ti]

def tropical_nakshatra(jd, place, equal = True):
  """Current nakshatra as of julian day (jd)
     1 = Asvini, 2 = Bharani, ..., 27 = Revati
     `equal = False' uses Garga's unequal nakshatra spacing.
  """
  # 1. Find time of sunrise
  lat, lon, tz = place
  rise = sunrise(jd, place)[0] - tz / 24.  # Sunrise at UT 00:00

  offsets = [0.0, 0.25, 0.5, 0.75, 1.0]
  longitudes = [tropical_lunar_longitude(rise + t) for t in offsets]

  # 2. Today's nakshatra is when offset = 0
  # There are 27 Nakshatras spanning 360 degrees
  nak, long_end = tropical_long_fixed_stars(jd, longitudes[0])
  if long_end < longitudes[0]: long_end += 360   # wraparound

  # 3. Find end time by 5-point inverse Lagrange interpolation
  y = unwrap_angles(longitudes)
  x = offsets
  approx_end = inverse_lagrange(x, y, long_end)
  ends = (rise - jd + approx_end) * 24 + tz
  answer = [int(nak), to_dms(ends)]

  # 4. Check for skipped nakshatra
  nak_tmrw, nak_tmrw_end = tropical_long_fixed_stars(jd, longitudes[-1])
  if nak_tmrw_end < longitudes[-1]: nak_tmrw_end += 360   # wraparound
  isSkipped = (nak_tmrw - nak) % 27 > 1
  if isSkipped:
    leap_nak = nak + 1
    approx_end = inverse_lagrange(offsets, longitudes, nak_tmrw_end)
    ends = (rise - jd + approx_end) * 24 + tz
    leap_nak = 1 if nak == 27 else leap_nak
    answer += [int(leap_nak), to_dms(ends)]

  return answer


### TESTS ####
def tropical_long_fixed_stars_tests():
  sun_long = tropical_solar_longitude(date1)
  nak, nak_ends_long = tropical_long_fixed_stars(date1, sun_long)
  assert(nak == 7 and (nak_ends_long - 117.31) < 0.1) # Sun in Punarvasu
  mars = swe.calc_ut(date1, swe.MARS, flags = swe.FLG_TROPICAL)[0][0]
  nak, nak_ends_long = tropical_long_fixed_stars(date1, mars)
  assert(nak == 3 and (nak_ends_long - 63.98) < 0.1) # Mars in Krittika

  bc_date = swe.julday(-2700, 2, 26, 13.0) # 18:30 PM in India
  moon = tropical_lunar_longitude(bc_date)
  nak, nak_ends_long = tropical_long_fixed_stars(bc_date, moon)
  assert(nak == 25 and (nak_ends_long - 292.23) < 0.1) # Moon in Purvabhadra
  mercury = swe.calc_ut(bc_date, swe.MERCURY, swe.FLG_TROPICAL | swe.FLG_SWIEPH)[0][0]
  nak, nak_ends_long = tropical_long_fixed_stars(bc_date, mercury)
  assert(nak == 3 and (nak_ends_long - 358.90) < 0.1) # Mercury in Krittika

def tropical_month_tithi_tests():
   dt1 = gregorian_to_jd(Date(2022, 12, 21)) # Margashira K13 in sidereal
   bangalore = Place(12.972, 77.594, +5.5)
   # Matches with JHora (sayana), month 10 = Pushya, tithi 28 = Krishna-trayodashi
   val = tropical_month_tithi(dt1, bangalore, False)
   assert(val == [[10, False], [28, [22, 16, 39]]])
   # What we actually want: month 9 = Margashira, just like in sidereal
   val = tropical_month_tithi(dt1, bangalore, True)
   assert(val == [[9, False], [28, [22, 16, 39]]])
   dt2 = gregorian_to_jd(Date(2022, 2, 21)) # sidereal Magha K5
   val = tropical_month_tithi(dt2, bangalore, True)
   assert(val == [[11, False], [20, [19, 58, 1]]]) # 11 = Magha, 20 = K5
   # Test some very old dates.
   # Pushya Purnima must have Pushya nak, but sidereal itself gives Mrgasira (=Pusya-3)
   # so something is off with sidereal calendar also.
   dt3 = gregorian_to_jd(Date(-3100, 10, 18)) # sidereal Pushya Purnima
   val = tropical_month_tithi(dt3, bangalore, True)
   assert(val == [[7, False], [15, [25, 0, 42]]]) # 7 = Ashvija :(
   val = tropical_month_tithi(dt3, bangalore, False)
   assert(val == [[8, False], [15, [25, 0, 42]]]) # 8 = Kartika :(
   # Kali Yuga start date
   dt3 = gregorian_to_jd(Date(-3101, 1, 22)) # sidereal Caitra S1
   val = tropical_month_tithi(dt3, bangalore, True)
   assert(val == [[11, False], [1, [29, 29, 5]]]) # 11 = Magha, no way January is Caitra!
   # Below dates from Reformed Sanathan Calendar, matches, including tithi END times!
   # http://web.archive.org/web/20160807161349/http://reformedsanathancalendar.in/sanathancalendar.pdf
   mar10 = gregorian_to_jd(Date(2016, 3, 10))
   val = tropical_month_tithi(mar10, bangalore)
   assert([[1, False], [2, [24, 34, 3]]]) # Caitra S2, ends 24:34
   nov18 = gregorian_to_jd(Date(2016, 11, 18)) # RSC expected Ardra (6)
   val = tropical_month_tithi(nov18, bangalore)
   assert(val == [[9, False], [20, [27, 32, 23]]]) # Margashira K5, ends 27:32

def tropical_nakshatra_tests():
   nov18 = gregorian_to_jd(Date(2016, 11, 18)) # RSC expected Ardra (6)
   nak, ends = nakshatra(nov18, bangalore) # assumes SIDM_LAHIRI
   assert(nak == 7 and ends == [28, 16, 24]) # Punarvasu (7) ends 28:16
   tr_nak = tropical_nakshatra(nov18, bangalore)
   assert(tr_nak == [7, [28, 14, 15]]) # Punarvasu (7) TRUE_PUSHYA ends 26:19
   nov11 = gregorian_to_jd(Date(2016, 11, 11)) # RSC expected P.Bhadra (25)
   nak = nakshatra(nov11, bangalore) # U.Bhadra (26), ends 25:00
   assert(nak[0] == 26 and nak[1][0] == 25)
   tr_nak = tropical_nakshatra(nov11, bangalore) # U.Bhadra (26)
   assert(tr_nak[0] == 26 and tr_nak[1] == [24, 58, 8])
   mar9 = gregorian_to_jd(Date(2017, 3, 9)) # SMKAP expected Punarvasu (7)
   nak = nakshatra(mar9, bangalore) # sidereal Puṣya (8) ends 17:12:04
   assert(nak[0] == 8 and nak[1][0:2] == [17, 12])
   tr_nak = tropical_nakshatra(mar9, bangalore) # Pushya (8)
   assert(tr_nak[0] == 8 and tr_nak[1] == [17, 10, 52])

if __name__ == "__main__":
    bangalore = Place(12.972, 77.594, +5.5)
    shillong = Place(25.569, 91.883, +5.5)
    date1 = gregorian_to_jd(Date(2009, 7, 15))
    date2 = gregorian_to_jd(Date(2013, 1, 18))
    date3 = gregorian_to_jd(Date(1985, 6, 9))
    date4 = gregorian_to_jd(Date(2022, 12, 10))
    date5 = gregorian_to_jd(Date(2022, 12, 24))
    date6 = gregorian_to_jd(Date(2022, 12, 25))
    tropical_month_tithi_tests()
    tropical_long_fixed_stars_tests()
    tropical_nakshatra_tests()
