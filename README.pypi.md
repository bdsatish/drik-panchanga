# drik-panchanga

Observational Indian lunisolar calendar (Hindu Drig-ganita / Drik Panchanga)
using the [Swiss Ephemeris](https://www.astro.com/swisseph/).

This PyPI package installs only the core library module `panchanga.py`.

## Install

```bash
pip install drik-panchanga
```

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
```

Full source, GUI, festival rules, and PDF calendar live in the
[GitHub repository](https://github.com/bdsatish/drik-panchanga).

## License

GNU Affero General Public License v3 or later (AGPL-3.0-or-later).
