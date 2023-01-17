from panchanga import *

def solstice(jd, opt = +1):
    """Finds the julian day of previous occurence of
    winter solstice (opt = +1) or summer solstice (opt = -1)."""
    if opt == -1:  sun_longitude =  90 # degrees, summer solstice
    if opt == +1:  sun_longitude = 270 # degrees, winter solstice
    flag = swe.FLG_SWIEPH # tropical (NOT sidereal!)
    # Search in a span of 400 days before today
    start = jd - 400
    stop = jd + 25
    while stop >= start:
        longi = swe.calc_ut(stop, swe.SUN, flag = flag)[0][0]
        # difference less than 0.0005 degrees
        if abs(longi - sun_longitude) <= 5E-3:
            return stop
        stop -= 1E-2
    return None

def vedic_month(jd, place):
    uttarayana_moment = solstice(jd, +1)
    lunar_month = 29.530589 # days
    month = ceil(abs(jd - uttarayana_moment) / lunar_month)
    ti = tithi(jd, place)[0]
    critical = sunrise(jd, place)[0]  # - tz/24 ?
    next_new_moon = new_moon(critical, ti, +1)
    if jd < next_new_moon: month = 12
    return month
