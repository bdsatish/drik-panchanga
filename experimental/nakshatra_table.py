#!/usr/bin/env python3

import os
import swisseph as swe

home = os.getenv("HOME")
swe.set_ephe_path(home + "/.local/share/swisseph")

jd = swe.julday(2000, 1, 1)
bce = swe.julday(-2500, 1, 1)
ce = swe.julday(2500, 1, 1)

stars = [
"Hamal",
",41Ari",
"Alcyone",
"Aldebaran",
"Elnath",
"Alhena",
"Pollux",
"Altarf",
"Acubens",
"Regulus",
"Chort",
"Denebola",
"Porrima",
"Spica",
"Syrma",
"ZubenElgenubi",
"Dschubba",
"Antares",
"Sabik",
"Nunki",
"GiediSecunda",
"DenebAlgedi",
"Sadalachbia",
",phAqr",
"Vernalis",
"Linteum",
"AlPherg",
]

# anything goes, ecliptic positions far too stable for succesive differences
swe.set_sid_mode(swe.SIDM_TRUE_CITRA)

longs = []

for s in stars:
    coord_jd = swe.fixstar_ut(s, jd, swe.FLG_SIDEREAL)
    bayer = coord_jd[1]
    latitude = coord_jd[0][1]
    longs.append(coord_jd[0][0])
    mag = swe.fixstar_mag(s)[0]
    coord_bce = swe.fixstar_ut(s, bce, swe.FLG_SIDEREAL)[0][0]
    coord_ce = swe.fixstar_ut(s, ce, swe.FLG_SIDEREAL)[0][0]
    motion = (coord_ce - coord_bce) * 60 # degrees to minutes
    print("%s | %.2f | %+06.2f | %+07.2f | %+08.4f |" % (bayer, mag, latitude, coord_jd[0][0], motion))

# successive differences, "span" or "width" of a nakshatra
diffs = []
for i in range(len(longs) - 1):
    x = longs[i+1] - longs[i]
    if x < 0: x += 360
    diffs.append(x)

for x in diffs: print("%05.2f" % x)
print("%05.2f" % (longs[-1] - longs[0])) # last difference, probably % 360 or sign swap required
print(longs)
