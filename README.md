Drik Panchanga
==============

Observational Indian lunisolar calendar (Hindu Drig-ganita Panchanga) using
the Swiss Ephemeris.

Computes the five essentials — tithi, nakshatra, yoga, karana, vaara — with
end times, plus sunrise, sunset, moonrise and moonset. Lunar months can be
named in either amānta or pūrṇimānta reckoning. Accurate from 5000 BCE to
5000 CE. All timings are end timings. Times use a hours-past-midnight clock that
may run past 24:00 (e.g. ``26:15`` = 02:15 next civil morning); ``23:59:30``
rounds to ``24:00``, never wraps to ``00:00``. The Hindu day itself runs
sunrise to sunrise. Format with ``panchanga.format_hms`` / ``format_hms_from_jd``.

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

panchanga.set_chosen_ayanamsa("citra")
place = panchanga.Place(12.972, 77.594, +5.5)  # lat, lon, timezone hours
jd = panchanga.gregorian_to_jd(panchanga.Date(2026, 1, 15))

panchanga.tithi(jd, place)        # [27, [20, 17, 1]]  -> tithi 27, ends 20:17:01
panchanga.nakshatra(jd, place)    # [18, [29, 46, 1]]  -> Jyeshtha, end time
panchanga.yoga(jd, place)         # [11, [20, 34, 38]]
panchanga.vaara(jd)               # 4 (Thursday, 0 = Sunday)
panchanga.masa(jd, place)         # [10, False]        -> Pausha, not adhika
panchanga.sunrise(jd, place)      # [jd, [6, 49, 18]]  -> local sunrise 06:49:18
panchanga.sunset(jd, place)       # [jd, [18, 8, 40]]  -> local sunset
panchanga.pratah_sandhya(jd, place)  # [[5, 10, 59], [5, 56, 18]]  start, end
panchanga.trikalam(jd, place, option="rahu")   # Rahu Kala interval
panchanga.durmuhurtam(jd, place)               # Durmuhurta intervals
panchanga.planetary_positions(jd, place)       # all grahas, sidereal
panchanga.gauri_chogadiya(jd, place)           # 16 Choghadiya boundaries
```

Times are `[hours, minutes, seconds]` in the place's local civil time. Angles
are sidereal longitudes in `[degrees, minutes, seconds]`. Negative years in
`Date` are proleptic Gregorian (works back to 5000 BCE). Available ayanamsas:
`citra`, `revati`, `rohini`, `pushya`, `mula`, `krishnamurti`, `raman` — or
`panchanga.set_coordinate_mode("tropical")` for sāyana positions.

Polar regions
-------------

Above the polar circles the Sun can go days or months without rising or
setting. `sunrise()`/`sunset()` still return an anchor on every such day by
falling back to the matching meridian transit, which exists at every latitude
on every day:

- **Polar night** — sunrise and sunset both anchor at the upper transit (the
  noon glow): day length 0, night 24 h, as observed.
- **Midnight sun** — sunrise anchors at the lower transit (solar midnight) and
  sunset at the next day's lower transit: day length 24 h, night 0 h.

Both transits sit within ~30 minutes of the real sunrises on the days just
outside the polar period, so tithi, nakshatra, yoga, karaṇa and the derived
kalas (Rahu Kala, Abhijit, Durmuhurta, Varjyam, sandhya) stay continuous
across the polar edges. Solar-dependent intervals degrade truthfully: in
polar night, Rahu Kala etc. collapse to the transit instant (there is no
daylight to divide); in midnight sun they stretch to 1/8 of 24 h. Calendar
PDFs and the web UI therefore generate for any city on any date; no visual
marker distinguishes transit-anchored days from real sunrise days.

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
(e.g. `Bengaluru, IN`). Full details, including the PDF legend and festival
configuration: [docs/README.CALENDARS.md](docs/README.CALENDARS.md) and
[docs/README.FESTIVALS.md](docs/README.FESTIVALS.md).

For development setup (venv, ephemeris download), run
`./scripts/setup_venv.sh`. Tests:

```
python -m unittest discover -s tests -t . -p 'test_*.py'
```

Web UI
------

Online: https://panchanga.up.railway.app/

Offline, from a repository checkout:

```
python -m webapp.app    # then open http://127.0.0.1:8765/
```

Enter a city, then look up a day's panchanga, download either calendar PDF,
or export the 14-month span as iCal (.ics). When the City field is left
blank, the app suggests a city from the visitor's IP via a third-party GeoIP
service (ip-api.com, plain HTTP — their free tier has no HTTPS).

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
