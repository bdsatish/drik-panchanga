Festival dates and conventions
==============================

How to choose which festivals appear on the PDF is in
[README.md](README.md) (see **Festivals (how to)** and the Ujjain example).
This file documents how those dates are computed.

Festival and Ekadashi dates are resolved for the selected location in
`festival_rules.py` (ruleset `Udaya-Vyapini-1.1`). The older multi-policy
implementation is kept under `experimental/` for reference only. The PDF
includes only festivals enabled in `festivals.cfg` (or `--festivals`).

Selecting festivals
-------------------

`festivals.cfg` is an INI file with a `[festivals]` section. Keys must match
catalog names in `festival_rules.py` exactly; every catalog name must appear
with `yes`/`no` (also `true`/`false`, `1`/`0`, `on`/`off`). Unknown or missing
names are rejected at load time.

The shipped defaults are a regional compromise (for example Onam and Mesha
Sankranti on; Karwa Chauth, Gita Jayanti, and Chhath off). Edit the cfg for
your locality. The footer holds at most 30 enabled festivals (6 columns × 5
rows); enabling more fails loudly when drawing the page.

Common sunrise rule
-------------------

A festival tied to a tithi uses the civil day where that tithi prevails at
local sunrise. If the same tithi covers two consecutive sunrises (vriddhi),
the earlier day is kept. If the tithi is skipped between sunrises (kshaya),
the later civil day is kept. Adhika (intercalary) masas are skipped for
ordinary festivals. Ugadi is the exception: when both adhika and nija Chaitra
`S1` occur, only the adhika date is marked.

Most numbered festivals are plain amanta masa + tithi pairs under that rule
(for example Rama Navami = Chaitra `S9`, Deepavali = Ashvina `K15`). Ekadashi
underlines use the same rule for every `S11` and `K11`; they are not the
*Dharma-sindhu* four-ghati Arunodaya / Mahadvadashi machinery.

Non-tithi festivals
-------------------

These have dedicated selectors (dispatch by catalog name):

* **Varamahalakshmi Vrata** — Friday strictly before nija Sravana Purnima
  (`S15`).
* **Yajur Upakarma** — nija Sravana `S15`. If eclipsed (see below), postpone to
  Bhadrapada `S15`.
* **Rig Upakarma** — nija day whose sunrise nakshatra is Sravana (`22`); if
  that nakshatra is missing at sunrise in Sravana masa, or the chosen day is
  eclipsed (see below), use Bhadrapada's Sravana-nakshatra day. Vriddhi keeps
  the former sunrise.

  Upakarma eclipse test (Yajur and Rig): postpone when the instant of a
  locally visible non-penumbral lunar eclipse's maximum falls on the chosen
  local civil date. In practical terms, an eclipse `X` on the selected
  Upakarma date triggers the fallback. Solar and purely penumbral lunar
  eclipses are ignored. Using midnight-to-midnight civil date for an eclipse
  is in line with Dharma Sindhu. Using the maximum's moment avoids interval
  arithmetic.

* **Onam** — sunrise nakshatra Sravana (`22`) while the Sun is in Simha
  (raasi 5); if none, try Kanya (raasi 6). Same vriddhi / empty-primary
  pattern as Rig Upakarma, but keyed on solar rasi rather than lunar masa, and
  with no eclipse test.
* **Vaikuntha Ekadashi** — a Margashirsha or Pausha Shukla Ekadashi upavasa
  day while the Sun is in Dhanur at sunrise. If none qualify, the PDF prints
  `None`.
* **Mesha Sankranti** / **Makara Sankranti** — first civil sunrise after the
  Sun enters Mesha (raasi 1) or Makara (raasi 10). Both use the shared
  sankranti helper.

Location dependence
-------------------

Dates are sunrise- and location-dependent, so the same festival can fall on
different Gregorian days in different cities. A city inside a polar-night or
midnight-sun period cannot be generated for dates on which Swiss Ephemeris
cannot provide a local sunrise.
