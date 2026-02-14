#!/usr/bin/env python3

"""Copyright © 2022 Satish B. Setty. All Rights Reserved."""

import swisseph as swe

# ---- helper functions ----
# Make angle lie between [-180, 180) instead of [0, 360)
norm180 = lambda angle: (angle - 360) if angle >= 180 else angle;
# Julian Day number as on (year, month, day) at 00:00 UTC
gregorian_to_jd = lambda year, month, day: swe.julday(year, month, day, 0.0)
jd_to_gregorian = lambda jd: swe.revjul(jd, swe.GREG_CAL)   # returns (y, m, d, h, min, s)
is_same_sign = lambda x, y: (x * y) > 0
func = lambda jd: norm180(swe.get_ayanamsa_ut(jd))

# Convert XX degrees to D°M'S" degree-minute-seconds
def to_dms_prec(deg):
  d = int(deg)
  mins = (deg - d) * 60
  m = int(mins)
  s = round((mins - m) * 60, 6)
  return [d, m, s]

def bisect(func, start, stop, tolerance = 1E-7):
    'Find root of continuous function where func(start) and func(stop) have opposite signs'
    assert not is_same_sign(func(start), func(stop))
    count = 0
    while abs(stop - start) > tolerance:
        midpoint = (start + stop) / 2
        if is_same_sign(func(start), func(midpoint)):
            start = midpoint
        else:
            stop = midpoint
        count += 1
        if count > 1000:
            print('ERROR: func does not converge')
            return -1
    return midpoint

# Search b/w -1000 CE to 1000 CE
start = gregorian_to_jd(-1000, 1, 1)
stop = gregorian_to_jd(1000, 1, 1)
j2000_start = swe.julday(2000, 1, 1) # Jan 1, 2000
j2000_end = j2000_start + 365.25000 # length of astronomical "julian year" exactly

zeros = {}
precessions = {}
for sid in range(0, 50):
    name = swe.get_ayanamsa_name(sid)
    if name is None: break
    swe.set_sid_mode(sid)
    try:
        zeros[name] = bisect(func, start, stop)
        ayan_j2000_start = swe.get_ayanamsa_ut(j2000_start)
        ayan_j2000_end = swe.get_ayanamsa_ut(j2000_end)
        # convert degrees to seconds
        precessions[name] = (ayan_j2000_end - ayan_j2000_start) * 60 * 60
    except AssertionError:
        print(f'ERROR: adjust start and stop for ayanamsa {name}  ')
        continue

zeros_sorted_jd = dict(sorted(zeros.items(), key=lambda item: item[1]))

for ayanamsa in zeros_sorted_jd:
    zero_point = zeros_sorted_jd[ayanamsa]
    greg = jd_to_gregorian(zero_point)
    date = "%+05d/%02d/%02d" % (greg[0], greg[1], greg[2]) # YYYY-MM-DD
    time = "%02d:%02d:%05.2f" % tuple(to_dms_prec(greg[3])) # convert to hh:mm:ss
    precession = "%.7f" % precessions[ayanamsa]
    print(f"| {ayanamsa} | {zero_point:0.6f} | {date}, {time} | {precession} |")
