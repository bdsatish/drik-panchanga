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
            return (i - 2) % 27, spacing[(i - 2)%27]

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
# - Vernal equinox will occur in the month of Caitra (by definition)
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

def tropical_nakshatra(jd, place):
  """Current nakshatra as of julian day (jd)
     1 = Asvini, 2 = Bharani, ..., 27 = Revati
  """
  # 1. Find time of sunrise
  lat, lon, tz = place
  rise = sunrise(jd, place)[0] - tz / 24.  # Sunrise at UT 00:00

  offsets = [0.0, 0.25, 0.5, 0.75, 1.0]
  longitudes = [ tropical_lunar_longitude(rise + t) for t in offsets]

  # 2. Today's nakshatra is when offset = 0
  # There are 27 Nakshatras spanning 360 degrees
  nak = ceil(longitudes[0] * 27 / 360)  # equal spacing
  print("nak long ", longitudes[0])
  nak, nak_long = find_nakshatra_garga(longitudes[0])  # unequal spacing

  # 3. Find end time by 5-point inverse Lagrange interpolation
  y = unwrap_angles(longitudes)
  x = offsets
  approx_end = inverse_lagrange(x, y, nak_long)
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



### TESTS ####
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
   assert(val == [[7, False], [15, [24, 59, 55]]]) # 7 = Ashvija :(
   val = tropical_month_tithi(dt3, bangalore, False)
   assert(val == [[8, False], [15, [24, 59, 55]]]) # 8 = Kartika :(
   # Kali Yuga start date
   dt3 = gregorian_to_jd(Date(-3101, 1, 22)) # Caitra S1
   val = tropical_month_tithi(dt3, bangalore, True)
   assert(val == [[11, False], [1, [29, 28, 11]]]) # 11 = Magha, no way January is Caitra!
   # dates from Reformed Sanathan Calendar, matches, including tithi END times!
   # http://web.archive.org/web/20160807161349/http://reformedsanathancalendar.in/sanathancalendar.pdf
   mar10 = gregorian_to_jd(Date(2016, 3, 10))
   val = tropical_month_tithi(mar10, bangalore)
   assert([[1, False], [2, [24, 34, 3]]]) # Caitra S2, ends 24:34
   nov18 = gregorian_to_jd(Date(2016, 11, 18)) # RSC expected Ardra (6)
   val = tropical_month_tithi(nov18, bangalore)
   assert(val == [[9, False], [20, [27, 32, 23]]]) # Margashira K5, ends 27:32
   print(nakshatra(nov18, bangalore)) # Punarvasu (7)
   print(tropical_nakshatra(nov18, bangalore)) # Puṣya (8)
   nov11 = gregorian_to_jd(Date(2016, 11, 11)) # RSC expected P.Bhadra (25)
   print(nakshatra(nov11, bangalore)) # U.Bhadra (26)
   print(tropical_nakshatra(nov11, bangalore)) # Revati (27) and then Asvini (1)
   mar9 = gregorian_to_jd(Date(2017, 3, 9)) # SMKAP expected Punarvasu (7)
   print(nakshatra(mar9, bangalore)) # sidereal Puṣya (8)
   print(tropical_nakshatra(mar9, bangalore)) # Magha (10)

if __name__ == "__main__":
    bangalore = Place(12.972, 77.594, +5.5)
    shillong = Place(25.569, 91.883, +5.5)
    date1 = gregorian_to_jd(Date(2009, 7, 15))
    date2 = gregorian_to_jd(Date(2013, 1, 18))
    date3 = gregorian_to_jd(Date(1985, 6, 9))
    date4 = gregorian_to_jd(Date(2022, 12, 10))
    date5 = gregorian_to_jd(Date(2022, 12, 24))
    date6 = gregorian_to_jd(Date(2022, 12, 25))
    print(vedic_month(date4, bangalore))
    print(vedic_month(date5, bangalore))
    print(vedic_month(date6, bangalore))
    tropical_month_tithi_tests()
