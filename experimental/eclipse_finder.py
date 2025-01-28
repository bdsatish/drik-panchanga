import swisseph as swe

EVENT_LIMIT = 2000  # Maximum number of days to search

# Function to find eclipses at a given location and date
def find_eclipse(year, month, day, longitude, latitude, altitude, timezone):
    # Constants
    JD_START = swe.julday(year, month, day)  # Start Julian Day
    
    # Eclipse types (sun and moon)
    ECLIPSE_TYPES = ["Solar", "Lunar"]
    
    eclipses = []
    
    # Check for both solar and lunar eclipses
    for eclipse_type in ECLIPSE_TYPES:
        jd = JD_START  # Start from the given Julian day
        while True:
            # Find next eclipse of the specified type
            if eclipse_type == "Lunar":
                next_eclipse = swe.lun_eclipse_when_loc(jd, (longitude, latitude, altitude), flags = swe.FLG_SWIEPH)
            else:
                next_eclipse = swe.sol_eclipse_when_loc(jd, (longitude, latitude, altitude), flags = swe.FLG_SWIEPH)

            flags = next_eclipse[0]

            # Extract relevant details
            jd = next_eclipse[1][0]  # Julian day of the event
            if jd - JD_START > EVENT_LIMIT:
                break  # Stop if we go beyond the search limit

            local_date = swe.revjul(jd + timezone / 24.0)  # Convert Julian day to calendar date
            eclipse_info = {
                "type": eclipse_type,
                "date": f"{int(local_date[2]):02d}/{int(local_date[1]):02d}/{int(local_date[0]):04d}",
                "time": f"{int(local_date[3]):02d}:{round(local_date[3] % 1 * 60):02d}",
            }

            # Ignore if eclipse is not visible. Ignore penumbral lunar eclipses
            if flags & swe.ECL_VISIBLE and (not flags & swe.ECL_PENUMBRAL):
                eclipses.append(eclipse_info)
            
            # Increment Julian day for the next search
            jd += 1  # Move forward to the next day
    
    return eclipses


# Example Usage
if __name__ == "__main__":
    year = 2025
    month = 1
    day = 1
    longitude = 77.5946  # Bangalore longitude
    latitude = 12.9716   # Bangalore latitude
    timezone = +5.5      # India timezone

    kurukshetra_lat = 29.969513
    kurukshetra_lon = 76.878281
    kurukshetra_alt = 250 # average, metres

    eclipse_results = find_eclipse(year, month, day,
                                   kurukshetra_lon, kurukshetra_lat, kurukshetra_alt, timezone)
    for eclipse in eclipse_results:
        print(f"{eclipse['type']} Eclipse on {eclipse['date']} at {eclipse['time']} local time")
