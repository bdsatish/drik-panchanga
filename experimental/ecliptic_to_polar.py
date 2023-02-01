#!/usr/bin/env python3

import swisseph as swe
import math

_VERY_SMALL = 1e-10

# Helper functions for working in degrees instead of radians
tand = lambda x: math.tan(x * math.pi/180)
cosd = lambda x: math.cos(x * math.pi/180)
atand = lambda x: math.atan(x) * 180 / math.pi
atan2d = lambda y, x: math.atan2(y, x) * 180 / math.pi

def to_dms_prec(deg):
  d = int(deg)
  mins = (deg - d) * 60
  m = int(mins)
  s = round((mins - m) * 60, 6)
  return [d, m, s]

def to_dms(deg):
  d, m, s = to_dms_prec(deg)
  return [d, m, int(s)]

# Direct translation of swi_armc_to_mc from swehouse.c file
def swi_armc_to_mc(armc, epsln):
  if abs(armc - 90) > _VERY_SMALL and abs(armc - 270) > _VERY_SMALL:
    tant = tand(armc)
    mc = atan2d(tant, cosd(epsln)) # This is same as ayan_on_jd, below
    if armc > 90 and armc <= 270:
      mc = swe.degnorm(mc + 180)
  else:
      mc = 90 if abs(armc - 90) <= _VERY_SMALL else 270

  return mc;

# Below is same as swi_armc_to_mc()
def ra_to_pl(ra, epsln):
    coseps = cosd(epsln)
    if abs(ra - 90) < _VERY_SMALL or abs(ra - 270) < _VERY_SMALL:
        pl = ra
    elif ra < 90 or ra > 270: # ra in quadrant 1 or 4
        pl = atand(tand(ra) / coseps)
    else: # quadrant 2 or 3
        ra1 = 180 - ra # shifts to quadrant 1 or 4
        pl1 = atand(tand(ra1) / coseps)
        pl = 180 - pl1 # shift back to quad 2 or 3
    return pl

def ecliptic_to_polar_longitude(jd, ecl_long):
    """Converts ecliptic longitude as given by fixstar_ut or calc_ut to polar longitude"""
    # ECL_NUT is a special "planet" which returns obliquity and nutation
    epsln = swe.calc_ut(jd, swe.ECL_NUT, swe.FLG_TROPICAL)  # obliquity to the ecliptic
    mc = swi_armc_to_mc(ecl_long, epsln[0][0])
    return mc

def ecliptic_to_polar_longitude_new(jd, right_ascension):
    """Input right_ascension must be from TROPICAL | EQUATORIAL coordinates as on jd"""
    epsln = swe.calc(jd_ss_citra, swe.ECL_NUT, swe.FLG_TROPICAL)
    pl = ra_to_pl(right_ascension, epsln[0][0])
    return pl

if __name__ == "__main__":
    # SIDM_SS_CITRA should have ayannamsha of 2.11070444 on jd 1903396.8128654
    jd_ss_citra = 1903396.8128654 # taken from sweph.h
    ayan_on_jd = 2.11070444 # same as swe.get_ayanamsha(jd_ss_citra), remember to set SIDM_SS_CITRA
    expected = ayan_on_jd + 180 # expected longitude on given jd is 180° + ayanamsha
    # Surya siddhanta (all other indian siddhantas) give coordinates in equatorial+tropical
    # with no nutation and no aberration
    spica = swe.fixstar_ut("Spica", jd_ss_citra , swe.FLG_TROPICAL | swe.FLG_EQUATORIAL | swe.FLG_NONUT | swe.FLG_NOABERR)
    ll = spica[0][0] # longitude
    new_ll = ecliptic_to_polar_longitude(jd_ss_citra, ll)
    print("Equatorial: ", ll, "Polar:", new_ll)
    print("Expected: ", to_dms(expected), "Actual: ", to_dms(new_ll))
    assert(to_dms(expected) == to_dms(new_ll))

    (right_asc, decl, *_), *_ = swe.fixstar("Spica", jd_ss_citra, swe.FLG_TROPICAL | swe.FLG_EQUATORIAL)
    print("Polar long spica:", ecliptic_to_polar_longitude_new(jd_ss_citra, right_asc))

    (right_asc, decl, *_), *_ = swe.fixstar(",zePsc", jd_ss_citra, swe.FLG_TROPICAL | swe.FLG_EQUATORIAL)
    ayan_on_jd = -0.79167046
    expected = ayan_on_jd + (359 + 50/60)
    print("Expected long? Revati", expected)
    print("His formula: ", ecliptic_to_polar_longitude_new(jd_ss_citra, right_asc))
    print("My formula: ", ecliptic_to_polar_longitude(jd_ss_citra, right_asc))

