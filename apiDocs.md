Below is a ready-to-copy README.md (API documentation) for your current main.py FastAPI service, including the new endpoints.

⸻

README.md — Drik Panchanga API

Drik Panchanga API (FastAPI)

A FastAPI wrapper around the webresh/drik-panchanga codebase (Swiss Ephemeris), exposing:
	•	Daily Panchang (/panchanga)
	•	Next Maasikam dates (/next-maasikam)
	•	Next Samvatsareekam date (/next-samvatsareekam)

Base URL

If running locally:
	•	http://localhost:8000

Your server:
	•	http://13.234.17.15:8000

FastAPI Swagger UI:
	•	/docs → http://13.234.17.15:8000/docs

⸻

Important Concepts

Tithi-at-Sunrise Rule (used by Maasikam + Samvatsareekam)

For both Maasikam and Samvatsareekam we:
	1.	Compute local sunrise for a date + location
	2.	Compute the tithi at sunrise
	3.	Match by:
	•	Paksha (Shukla / Krishna)
	•	Tithi-in-paksha (1..15)

This is a practical and widely usable implementation. Some traditions may require additional constraints (masa rules, special handling for amavasya/poornima, etc.) — those can be added later as a rule parameter.

⸻

1) GET /

Description

Health check.

Example

curl "http://13.234.17.15:8000/"


⸻

2) GET /panchanga

Description

Returns daily Panchang data (tithi, nakshatra, yoga, karana, sunrise/sunset, etc.) for a given date and location.

Query Parameters

Param	Type	Required	Example
year	int	✅	2025
month	int	✅	11
day	int	✅	30
latitude	float	✅	17.3850
longitude	float	✅	78.4867
tz_offset_hours	float	✅	5.5

Example

curl "http://13.234.17.15:8000/panchanga?year=2025&month=11&day=30&latitude=17.3850&longitude=78.4867&tz_offset_hours=5.5"

Response (high level)

{
  "input": { "date": "2025-11-30", "latitude": 17.385, "longitude": 78.4867, "tz_offset_hours": 5.5 },
  "panchanga": {
    "sun_moon": { "sunrise": "06:33:00", "sunset": "17:36:00", "...": "..." },
    "angams": { "tithi": { "current_number": 10, "current_ends_at": "..." }, "nakshatra": {...}, "yoga": {...} },
    "month_year": { "masa_number": 8, "is_adhika_masa": false, "ritu_number": 3, "samvatsara_number": 12 },
    "raw": { "...": "..." }
  }
}


⸻

3) GET /next-maasikam

Description

Computes the next Maasikam date(s) after a given start date, based on death tithi at sunrise.

Query Parameters

Param	Type	Required	Notes
death_year	int	✅	Death date (Gregorian)
death_month	int	✅	
death_day	int	✅	
latitude	float	✅	Location where calculation applies
longitude	float	✅	
tz_offset_hours	float	✅	e.g. 5.5
from_year	int	❌	If omitted, defaults to death date
from_month	int	❌	
from_day	int	❌	
count	int	❌	Default 1, range 1..24

Example (single next maasikam)

curl "http://13.234.17.15:8000/next-maasikam?death_year=2025&death_month=12&death_day=25&latitude=12.9716&longitude=77.5946&tz_offset_hours=5.5"

Example (next 6 maasikams)

curl "http://13.234.17.15:8000/next-maasikam?death_year=2025&death_month=12&death_day=25&latitude=12.9716&longitude=77.5946&tz_offset_hours=5.5&count=6"

Response (high level)

{
  "input": { "...": "..." },
  "death": {
    "sunrise": "06:xx:xx",
    "tithi": { "current_number": 5, "current_ends_at": "..." },
    "paksha": "Shukla",
    "tithi_in_paksha": 5
  },
  "next_maasikam": {
    "date": "2026-01-23",
    "sunrise": "06:xx:xx",
    "tithi": { "current_number": 5, "current_ends_at": "..." },
    "paksha": "Shukla",
    "tithi_in_paksha": 5
  },
  "next_maasikams": [ ... ]
}


⸻

4) GET /next-samvatsareekam

Description

Computes the next Samvatsareekam date based on death tithi at sunrise, while enforcing a minimum gap (default 300 days) to avoid returning a monthly match.

Query Parameters

Param	Type	Required	Notes
death_year	int	✅	Death date (Gregorian)
death_month	int	✅	
death_day	int	✅	
latitude	float	✅	Location where calculation applies
longitude	float	✅	
tz_offset_hours	float	✅	e.g. 5.5
from_year	int	❌	Default: death date
from_month	int	❌	
from_day	int	❌	
min_days_after	int	❌	Default 300 (range 1..370)

Example

curl "http://13.234.17.15:8000/next-samvatsareekam?death_year=2025&death_month=12&death_day=25&latitude=12.9716&longitude=77.5946&tz_offset_hours=5.5"

Example (stricter gap)

curl "http://13.234.17.15:8000/next-samvatsareekam?death_year=2025&death_month=12&death_day=25&latitude=12.9716&longitude=77.5946&tz_offset_hours=5.5&min_days_after=330"

Response (high level)

{
  "input": { "...": "..." },
  "death": { "...": "..." },
  "next_samvatsareekam": {
    "date": "2026-xx-xx",
    "sunrise": "06:xx:xx",
    "tithi": { "current_number": 5, "current_ends_at": "..." },
    "paksha": "Shukla",
    "tithi_in_paksha": 5
  }
}


⸻

Notes / Caveats
	•	All results depend on location + timezone (lat/lon/tz_offset_hours).
	•	If your reminder worker runs late, you may see “start” events missed and only “end” messages sent (expected for a polling scheduler).
	•	Maasikam & Samvatsareekam rules can differ by sampradaya. Current implementation uses tithi at sunrise matching (paksha + tithi-in-paksha), which is a practical default.

⸻

If you want, I can also add a section for Docker run commands (build, run, env vars, health checks) based on how you run this image today.