Drik Panchanga
==============

Observational Indian lunisolar calendar (Hindu Drig-ganita Panchanga) using
the Swiss Ephemeris.

Computes the five essentials — tithi, nakshatra, yoga, karana, vaara — with
end times, plus sunrise, sunset, moonrise and moonset. Lunar months can be
named in either amānta or pūrṇimānta reckoning. Accurate from 5000 BCE to
5000 CE.

Requirements
------------

Python 3.9+. The library is on PyPI as `drik-panchanga`:

```
pip install drik-panchanga          # core astronomy module
pip install "drik-panchanga[pdf]"   # + PDF calendar generators (CLIs)
```

Swiss Ephemeris needs `.se1` data files; set `SE_EPHE_PATH` or place them in
`~/.local/share/swisseph` (Windows: `%LOCALAPPDATA%\swisseph`). The Moshier
fallback is used, less accurately, until they are present.

Using `panchanga.py` as a library
---------------------------------

The core module works standalone — no Flask, no ReportLab:

```python
import panchanga
from datetime_helper import Date, format_hms, format_hms_from_jd, format_local_hm, gregorian_to_jd

panchanga.set_chosen_ayanamsa("citra")
place = panchanga.Place(12.972, 77.594, +5.5)  # lat, lon, UTC offset hours that day
day = Date(2026, 1, 15)
jd = gregorian_to_jd(day)

panchanga.tithi(jd, place)        # [27, 2461056.1160]  -> tithi 27; end as a UT Julian day
panchanga.nakshatra(jd, place)    # [18, 2461056.5111]  -> Jyeshtha
panchanga.yoga(jd, place)         # [11, 2461056.1282]
panchanga.vaara(jd)               # 4 (Thursday, 0 = Sunday)
panchanga.masa(jd, place)         # [10, False]         -> Pausha, not adhika
panchanga.sunrise(jd, place)      # 2461055.5551        (UT)
panchanga.sunset(jd, place)       # 2461056.0269
panchanga.moonrise(jd, place)     # UT JD or None — Hindu day only
panchanga.moonset(jd, place)      # same window: [sunrise, next sunrise)
panchanga.pratah_sandhya(jd, place)  # [start, end]; end is sunrise
panchanga.trikalam(jd, place, option="rahu")   # Rahu Kala [start, end]
panchanga.durmuhurtam(jd, place)               # one or two [start, end] intervals
panchanga.planetary_positions(jd, place)       # all grahas, sidereal
panchanga.gauri_chogadiya(jd, place)           # 16 Choghadiya end times

# Display: the zone (and DST) is applied here, never in the maths.
end = panchanga.tithi(jd, place)[1]
format_local_hm(end, "Asia/Kolkata", anchor_civil=day)                     # "20:17"
format_local_hm(end, "Asia/Kolkata", anchor_civil=day, show_seconds=True)  # "20:17:02"
format_hms_from_jd(end, jd, 5.5)                                           # "20:17", fixed offset
format_hms([26, 15, 0])                                                    # "26:15"
```

All timings are end timings. Event functions return UT Julian days;
`place.timezone` only locates the local midnight that opens the civil day.
`format_local_hm` shows a UT Julian day as hours past `anchor_civil`'s
midnight, at the UTC offset in force at that instant, so a DST change
mid-row needs no special handling. The Hindu day runs from sunrise to the
next sunrise, so a time after midnight reads `24:00` or later (e.g. `26:15`
= 02:15 the next morning), `23:59:30` rounds to `24:00`, never to `00:00`,
and a window that opens the previous evening reads `-00:26`.

Before a zone adopted standard time (the time-zone database's `LMT` era:
India before 1854, every BCE date), times read the
place's own local mean time, longitude / 15 hours, not the mean time of the
zone's reference city (Kolkata's +5:53 for all of India). Pass
`longitude=` to `utc_offset_hours`, `format_local_hm` and the other zone
helpers to get this; the calendars and the web UI do.

Angles are sidereal longitudes in `[degrees, minutes, seconds]`. Years in
`Date` and in the web day view are astronomical, on the proleptic Gregorian
calendar: year 0 is 1 BCE and -1 is 2 BCE (works back to 5000 BCE). Available
ayanamsas: `citra`, `revati`, `rohini`, `pushya`, `mula`, `krishnamurti`,
`raman` — or `panchanga.set_coordinate_mode("tropical")` for sāyana
positions.

Above the polar circles, `sunrise()` and `sunset()` fall back to the Sun's
meridian transit on days without a real sunrise or sunset; see
[Polar regions](docs/README.CALENDARS.md#polar-regions).

### Moonrise and moonset

`moonrise` / `moonset` return the UT Julian day of the event in
`[sunrise, next sunrise)` for that civil `jd`, or `None`. Anchored on that
day, an event after the next civil midnight reads `24:00+`. A rise at 00:40
before sunrise belongs on the **previous** civil row as `24:40`, not again
next morning as `00:40`.

`moonrise_jd` / `moonset_jd` are low-level Swiss Ephemeris helpers (first
event after **local midnight**). Prefer `moonrise` / `moonset` for calendars
and for Sankashtahara Chaturthi (K4 at Hindu-day moonrise).

Calendar PDFs
-------------

Two layouts, usable either from a repository checkout
(`python generate_*.py ...`) or after `pip install "drik-panchanga[pdf]"`:

```
drik-panchanga-short --city Ujjain --start 2026-06    # one-page A4, 14 months
drik-panchanga-long  --city Ujjain --start 2026-03    # 12-page wall calendar
```

Both accept `--month amanta|purnimanta`, `--ayanamsa` (citra, revati, rohini,
pushya, mula, krishnamurti, raman, tropical), `--festivals FILE.cfg`, and
`--output`. Cities come from `data/cities.json` as `AsciiName, CC`
(e.g. `Bengaluru, IN`). For places missing from the catalog, pass
`--place LAT,LON,TZ` with three decimal numbers instead: latitude (negative =
south), longitude (east = positive), and the timezone as a UTC offset in hours,
e.g. `--place -13.4,70,5.5` (UTC+5:30, no DST). Full details, including the
PDF legend and festival configuration:
[docs/README.CALENDARS.md](docs/README.CALENDARS.md) and
[docs/README.FESTIVALS.md](docs/README.FESTIVALS.md).

Web UI
------

Online: https://panchanga.up.railway.app/

Offline, from a repository checkout:

```
python -m webapp.app    # then open http://127.0.0.1:8765/
```

Enter a city, then look up a day's panchanga, download either calendar PDF,
or export the 14-month span as iCal (.ics). Alternatively switch to
Coordinates and enter decimal latitude/longitude plus a UTC offset in hours
(e.g. `5.5`, no DST) — useful for places missing from `data/cities.json`.
When the City field is left blank, the app suggests a city from the
visitor's IP via a third-party GeoIP service (ip-api.com, plain HTTP — their
free tier has no HTTPS).

Development
-----------

From a repository checkout:

```
./scripts/setup_venv.sh
source .venv/bin/activate
python -m unittest discover -s tests -t . -p 'test_*.py'
```

`setup_venv.sh` creates `.venv`, installs pyswisseph, ReportLab and Flask,
and offers to download the Swiss Ephemeris `.se1` files (~100 MB from
[aloistr/swisseph](https://github.com/aloistr/swisseph/tree/master/ephe))
into the default location. To use your own copy, run
`SE_EPHE_PATH=/path/to/ephemeris/files ./scripts/setup_venv.sh`.

Accuracy
--------

As accurate as the Swiss Ephemeris itself — in practice years 5000 BCE to
5000 CE. As a test, Madhva Navami (1317 CE, Māgha-māsa śukla-pakṣa navamī)
computes correctly for Udupi on 30/1/1317; cross-check with
[Calendrica](http://emr.cs.iit.edu/home/reingold/calendar-book/Calendrica.html).
Dates before 1582 are proleptic Gregorian.

Background
----------

This is a Dṛk (observation-based) calendar, in contrast to Sūrya Siddhānta
rules whose constants were last updated around 1000 CE. Planetary positions
come from measured data via the Swiss Ephemeris. More background, references
and comparisons with other software: [docs/BACKGROUND.md](docs/BACKGROUND.md).
Festival date rules: [docs/README.FESTIVALS.md](docs/README.FESTIVALS.md).

The old wxPython GUI is deprecated; its documentation lives in
[docs/DEPRECATED-wx-gui.md](docs/DEPRECATED-wx-gui.md).

Licence
-------

Copyright © Satish BD. Licensed under the GNU Affero GPL version 3 (or later).
The bundled IndUni-H fonts are GPL-2.0+ (see `fonts/README.txt`).

Word of caution
---------------

The so-called "Vedic astrology" has no basis in the Vedas, Upanishads, Bhagavad
Gita, Mahabharata or Ramayana. It is a [fringe science][1] of Hinduism. The
original [Vedanga Jyotisha](https://archive.org/details/VedangaJyotisa) (~1200
BCE) and [Surya Siddhanta](https://archive.org/details/in.ernet.dli.2015.69065)
(~400 CE) are purely astronomical.

[1]: https://en.wikipedia.org/wiki/Fringe_science
