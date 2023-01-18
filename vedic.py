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

def tropical_raasi(jd):
    """Tropical (sayana) rasi of sun on given day. 1 = Aries,...,12 = Pisces (tropical)"""
    longi = swe.calc_ut(jd, swe.SUN, flags = swe.FLG_SWIEPH | swe.FLG_TROPICAL)[0][0]
    return ceil(longi / 30)

# rename = True will give lunar "masa" almost exactly same result as
# sidereal calendar. Advantages:
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
