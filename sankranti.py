import swisseph as swe

# Make angle lie between [0, 360)
norm360 = lambda angle: angle % 360

# Makara sankranti means sun enters Makara rashi Capricorn = 10th sign
# longitude = 270° = 30° x 9 previous signs traversed
makara = 270
mesha = 0
rasi = 330

def func(jd):
    longi = swe.calc_ut(jd, swe.SUN, flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
    l = norm360(longi[0][0]) # degrees
    return l - rasi

# Print julian day in readable format
def format_jd(sidm, jd):
    yy, mon, dd, hh_mm = swe.revjul(jd)
    hh = hh_mm // 1
    mm = (hh_mm % 1) * 60
    print("%02d %-40s %d-%d-%d %02d:%02d" % (sidm, swe.get_ayanamsa_name(sidm), yy, mon, dd, hh, mm))

# calculates "x", x ∈ [start, stop], such that func(x) == 0
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

# We assume that Makara Sankranti occurs between Nov and Mar
start_jd = swe.julday(2023, 11, 1) # Nov 01
end_jd = swe.julday(2024, 3, 30)   # Mar 30

# We assume that Mesha Sankranti occurs between Feb and May
start_jd = swe.julday(2024, 3, 1) # Feb 01
end_jd = swe.julday(2024, 4, 30)  # May 30

for sidm in range(0, 50):
    swe.set_sid_mode(sidm)
    sankranti = bisection_search(func, start_jd, end_jd)
    format_jd(sidm, sankranti)
