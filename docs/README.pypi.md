# drik-panchanga

Observational Indian lunisolar calendar (Hindu Drig-ganita / Drik Panchanga)
using the [Swiss Ephemeris](https://www.astro.com/swisseph/).

**2.0.0** installs the core library modules `panchanga.py` and
`datetime_helper.py` (dates, time zones, clock formatting), plus the PDF
calendar generators behind the `[pdf]` extra:

```bash
pip install drik-panchanga          # core library only
pip install "drik-panchanga[pdf]"   # + reportlab, PDF console scripts
```

With the `[pdf]` extra, two console commands are available:

- `drik-panchanga-short` — one-page A4 landscape panchanga for one lunar year
- `drik-panchanga-long` — A4 portrait wall calendar, one page per month of the
  lunar year

`--start YYYY` prints the cāndramāna year whose Ugadi falls in Gregorian year
`YYYY`, from the month containing Ugadi through the month containing the last
Phālguna day (12–14 months; years `-3300 ... 3300`). BCE years take a leading
minus on the flag value (`--start=-0500`). Use `--city LAT,LON,TZ` when the
city is missing from the catalog.

```bash
drik-panchanga-short --city "Bengaluru, IN" --start 2026
drik-panchanga-short --city=-13.4,70,5.5 --start 2026  # lat, lon, UTC offset hours
drik-panchanga-long  --city Ujjain --start=-500
```

## Changes in 2.0.0

Breaking relative to 1.0.0:

- `Date`, `gregorian_to_jd`, `format_hms`, `format_local_hm` and the other
  civil-date / time-zone helpers live in `datetime_helper`, not `panchanga`.
- Event functions return **UT Julian days**. Format for display with
  `format_local_hm` (IANA zone, DST-aware) or `format_hms_from_jd` (fixed
  offset). Do not treat the second element of `tithi` / `nakshatra` as a local
  clock triple.
- CLI `--start` is an astronomical year `YYYY` (the lunar year of that year's
  Ugadi), not `YYYY-MM`.
- Prefer `set_coordinate_selection("citra")` to set the ayanāṃśa **and**
  sidereal mode together. `set_chosen_ayanamsa` only sets the key and leaves a
  prior tropical mode in place.

Also new: `--city LAT,LON,TZ`, Hindu-day `moonrise` / `moonset`, polar
transit fallbacks, and BCE years through about 5000 BCE.

## Ephemeris data

Swiss Ephemeris needs `.se1` data files. Either set `SE_EPHE_PATH` to a
directory that contains them, or place them in the default location used by
this library:

- Linux / macOS: `~/.local/share/swisseph` (or `$XDG_DATA_HOME/swisseph`)
- Windows: `%LOCALAPPDATA%\swisseph`

## Usage

```python
import panchanga
from datetime_helper import Date, format_hms, format_local_hm, gregorian_to_jd

panchanga.set_coordinate_selection("citra")  # ayanāṃśa key + sidereal mode
place = panchanga.Place(12.972, 77.594, +5.5)  # lat, lon, UTC offset hours that day
day = Date(2026, 1, 15)
jd = gregorian_to_jd(day)
tithi, end = panchanga.tithi(jd, place)[:2]     # end is a UT Julian day
print(tithi, format_local_hm(end, "Asia/Kolkata", anchor_civil=day))  # 27 20:17
print(panchanga.nakshatra(jd, place))
print(panchanga.masa(jd, place, amanta=True))   # or amanta=False for pūrṇimānta
print(panchanga.moonrise(jd, place))  # UT JD in [sunrise, next sunrise), or None
print(format_hms([23, 59, 30]))  # "24:00" — never wraps to 00:00
```

Event times are UT Julian days; `format_local_hm` shows them as hours past
the civil day's midnight at the offset in force at each instant (DST-aware),
running past 24:00 when the Hindu day (sunrise to sunrise) does.
`moonrise` / `moonset` use that window; the low-level `moonrise_jd` helper is
first-after-local-midnight only.

For tropical (sāyana) values instead of sidereal, call
`set_coordinate_mode("tropical")` before computing; reset with
`set_coordinate_mode("sidereal")`:

```python
panchanga.set_coordinate_mode("tropical")
print(panchanga.tithi(jd, place))          # tithi from tropical longitudes
print(panchanga.masa(jd, place, amanta=True))
panchanga.set_coordinate_mode("sidereal")
```

Full source, web UI, festival rules, and PDF calendar live in the
[GitHub repository](https://github.com/bdsatish/drik-panchanga).

## License

GNU Affero General Public License v3 or later (AGPL-3.0-or-later).
