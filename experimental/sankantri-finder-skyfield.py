# tropical_sankranti_utc.py
# pip install skyfield jplephem
from skyfield.api import load
from skyfield.searchlib import find_discrete
from datetime import timezone

import numpy as np

YEAR = 2026
EPHEMERIS = 'de421.bsp'   # high-precision JPL ephemeris

# --- load ---
eph = load(EPHEMERIS)
ts  = load.timescale()

# --- sector function (vectorized) ---
def tropical_sector(t):
    # t is a skyfield Time (scalar or array); return integer sector 0..11
    astrom = eph['earth'].at(t).observe(eph['sun']).apparent()
    lat, lon, distance = astrom.ecliptic_latlon()   # apparent ecliptic lon w.r.t. equinox of date
    degs = np.mod(lon.degrees, 360.0)
    return np.floor(degs / 30.0).astype(int)

# Important hint for find_discrete() to choose sampling spacing
tropical_sector.step_days = 15.0

# --- search window (UTC) ---
t0 = ts.utc(YEAR, 1, 1, 0, 0, 0)
t1 = ts.utc(YEAR, 12, 31, 23, 59, 59)

# --- find transitions ---
times, sectors = find_discrete(t0, t1, tropical_sector)

# Map sector -> name (new sector after transit)
names = [
    'Mesha (Aries)', 'Vrishabha (Taurus)', 'Mithuna (Gemini)', 'Karka (Cancer)',
    'Simha (Leo)', 'Kanya (Virgo)', 'Tula (Libra)', 'Vrishchika (Scorpio)',
    'Dhanu (Sagittarius)', 'Makara (Capricorn)', 'Kumbha (Aquarius)', 'Meena (Pisces)'
]

# Print UTC instants
for t, sector in zip(times, sectors):
    utc_dt = t.utc_datetime().replace(tzinfo=timezone.utc)
    print(f"{names[int(sector)]:20s}  UTC {utc_dt.isoformat()}")

# Note: find_discrete returns each sector-change instant; result order is chronological.
