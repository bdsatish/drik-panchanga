#!/usr/bin/env python3

import datetime
from skyfield.api import load
from skyfield.framelib import true_equator_and_equinox_of_date
from skyfield.searchlib import find_discrete

# Load ephemeris and timescale
ts = load.timescale()
eph = load('de421.bsp')
earth, sun = eph['earth'], eph['sun']

# Tropical Rasis (Signs) corresponding to 30° segments
rasis = [
    "Mesha (Aries) - 0°", "Vrishabha (Taurus) - 30°", "Mithuna (Gemini) - 60°",
    "Karka (Cancer) - 90°", "Simha (Leo) - 120°", "Kanya (Virgo) - 150°",
    "Tula (Libra) - 180°", "Vrishchika (Scorpio) - 210°", "Dhanus (Sagittarius) - 240°",
    "Makara (Capricorn) - 270°", "Kumbha (Aquarius) - 300°", "Meena (Pisces) - 330°"
]

def generate_tropical_sankrantis(year):

    # Function to calculate which 30° segment the Sun is currently in
    def sankranti_state(t):
        apparent = earth.at(t).observe(sun).apparent()
        lat, lon, distance = apparent.ecliptic_latlon(epoch='date')
        # _, lon, _ = apparent.frame_latlon(true_equator_and_equinox_of_date)
        return (lon.degrees // 30).astype(int)

    sankranti_state.step_days = 15.0  # Safe step size for root finding

    # Define the time bounds for the specified year
    t0 = ts.utc(year, 1, 1)
    t1 = ts.utc(year + 1, 1, 1)

    # Find the exact transition times
    times, states = find_discrete(t0, t1, sankranti_state)

    print(f"--- Tropical (Sayana) Sankrantis for {year} ---")
    for time, state in zip(times, states):
        # State corresponds to the integer 0-11 (0 = Mesha/0°, 1 = Vrishabha/30°, etc.)
        # We use standard UTC for the output
        date_str = time.utc_strftime('%Y-%m-%d %H:%M:%S UTC')

        # Map state (0-11) to the correct Rasi. 0 is Mesha.
        # Shift index to align with the rasis list display formatting

        print(f"{date_str} : Sun enters {rasis[state]}")

def gregorian_to_sayana(year, month, day, hour=0, minute=0, second=0):
    # Set the target date
    target_t = ts.utc(year, month, day, hour, minute, second)

    # 1. Find the Sun's current apparent longitude
    apparent = earth.at(target_t).observe(sun).apparent()
    lat, lon, distance = apparent.ecliptic_latlon()
    # _, lon, _ = apparent.frame_latlon(true_equator_and_equinox_of_date)
    current_deg = lon.degrees

    # Determine the current Sayana month index (0 to 11)
    month_idx = int(current_deg // 30)

    # 2. Find the exact moment of the previous Sankranti
    # Search backwards over the last 32 days
    t0_datetime = target_t.utc_datetime() - datetime.timedelta(days=32)
    t0 = ts.utc(t0_datetime.year, t0_datetime.month, t0_datetime.day)

    def sankranti_state(t):
        app = earth.at(t).observe(sun).apparent()
        _, l, _ = app.ecliptic_latlon(epoch='date')
        # _, l, _ = app.frame_latlon(true_equator_and_equinox_of_date)
        return (l.degrees // 30).astype(int)

    sankranti_state.step_days = 1.0 # 1-day step for reliable root finding over a short period

    times, states = find_discrete(t0, target_t, sankranti_state)

    # 3. Calculate the day of the solar month
    if len(times) > 0:
        sankranti_time = times[-1]
        # Calculate full 24-hour periods elapsed since the Sankranti
        delta_days = target_t - sankranti_time
        # Add 1 so the day of Sankranti is Day 1
        sayana_day = int(delta_days) + 1
    else:
        return "Error: Could not locate previous Sankranti."

    return {
        "Gregorian Date": target_t.utc_strftime('%Y-%m-%d %H:%M:%S UTC'),
        "Sayana Month": rasis[month_idx],
        "Sayana Day": sayana_day,
        "Degrees": round(current_deg, 4)
    }

# Example usage for today:
if __name__ == "__main__":
    # March 17, 2026 at 12:36 UTC
    generate_tropical_sankrantis(2026)
    result = gregorian_to_sayana(2026, 3, 17, 3, 36)
    for key, value in result.items():
        print(f"{key}: {value}")
