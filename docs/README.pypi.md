# drik-panchanga

Observational Indian lunisolar calendar (Hindu Drig-ganita / Drik Panchanga)
using the [Swiss Ephemeris](https://www.astro.com/swisseph/).

This PyPI package installs the core library module `panchanga.py`, plus the
PDF calendar generators behind the `[pdf]` extra:

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

panchanga.set_chosen_ayanamsa("citra")
place = panchanga.Place(12.972, 77.594, +5.5)  # lat, lon, timezone hours
jd = panchanga.gregorian_to_jd(panchanga.Date(2026, 1, 15))
print(panchanga.tithi(jd, place))
print(panchanga.nakshatra(jd, place))
print(panchanga.masa(jd, place, amanta=True))   # or amanta=False for pūrṇimānta
print(panchanga.moonrise(jd, place))  # Hindu day [sunrise, next sunrise), or None
print(panchanga.format_hms([23, 59, 30]))  # "24:00" — never wraps to 00:00
```

Times are hours past civil midnight and may run past 24:00 (Hindu day =
sunrise to sunrise). ``moonrise`` / ``moonset`` use that window; the low-level
``moonrise_jd`` helper is first-after-local-midnight only.

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
