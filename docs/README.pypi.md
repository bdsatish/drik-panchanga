# drik-panchanga

Observational Indian lunisolar calendar (Hindu Drig-ganita / Drik Panchanga)
using the [Swiss Ephemeris](https://www.astro.com/swisseph/).

This PyPI package installs the core library modules `panchanga.py` and
`datetime_helper.py` (dates, time zones, clock formatting), plus the PDF
calendar generators behind the `[pdf]` extra:

```bash
pip install drik-panchanga          # core library only
pip install "drik-panchanga[pdf]"   # + reportlab, PDF console scripts
```

With the `[pdf]` extra, two console commands are available:

- `drik-panchanga-short` — one-page A4 landscape panchanga for 14 months
- `drik-panchanga-long` — 12-page A4 portrait wall calendar

```bash
drik-panchanga-short --city "Bengaluru, IN" --start 2026-06
```

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

panchanga.set_chosen_ayanamsa("citra")
place = panchanga.Place(12.972, 77.594, +5.5)  # lat, lon, UTC offset hours that day
day = Date(2026, 1, 15)
jd = gregorian_to_jd(day)
tithi, end = panchanga.tithi(jd, place)[:2]     # end is a UT Julian day
print(tithi, format_local_hm(end, "Asia/Kolkata", anchor_civil=day))  # 27 20:17
print(panchanga.nakshatra(jd, place))
print(panchanga.masa(jd, place, amanta=True))   # or amanta=False for pūrṇimānta
print(panchanga.moonrise(jd, place))  # UT JD in the Hindu day [sunrise, next sunrise), or None
print(format_hms([23, 59, 30]))  # "24:00" — never wraps to 00:00
```

Event times are UT Julian days; `format_local_hm` shows them as hours past
the civil day's midnight at the offset in force at each instant (DST-aware),
running past 24:00 when the Hindu day (sunrise to sunrise) does.
``moonrise`` / ``moonset`` use that window; the low-level ``moonrise_jd``
helper is first-after-local-midnight only.

For tropical (sāyana) values instead of sidereal, call
`set_coordinate_mode("tropical")` before computing; reset with
`set_coordinate_mode("sidereal")`:

```python
panchanga.set_coordinate_mode("tropical")
print(panchanga.tithi(jd, place))          # tithi from tropical longitudes
print(panchanga.masa(jd, place, amanta=True))
panchanga.set_coordinate_mode("sidereal")
```

Full source, GUI, festival rules, and PDF calendar live in the
[GitHub repository](https://github.com/bdsatish/drik-panchanga).

## License

GNU Affero General Public License v3 or later (AGPL-3.0-or-later).
