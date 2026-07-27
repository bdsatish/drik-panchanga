Festival dates and conventions
==============================

How to choose which festivals appear on the PDF is in [README.md](README.md)
(see **Festivals (how to)** and the Ujjain example).  This file documents how
those dates are computed.

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
Sankranti on; Karwa Chauth, Gita Jayanti, and Chhath off). Edit the cfg for your
locality. The footer holds at most 30 enabled festivals (6 columns ﾗ 5 rows);
enabling more fails loudly when drawing the page.

Common sunrise rule (udaya-vyāpinī)
-----------------------------------

A festival tied to a tithi uses the civil day where that tithi prevails at local
sunrise.

- If the same tithi covers two consecutive sunrises (vriddhi), the earlier day
  is kept.
- If the tithi is skipped between sunrises (kshaya), the later civil day is kept.

Adhika (intercalary) masas are skipped for ordinary festivals. Ugadi is the
exception: when both adhika and nija Chaitra `S1` occur, only the adhika date is
marked.

Most numbered festivals are plain amanta masa + tithi pairs under that rule (for
example Rama Navami = Chaitra `S9`, Deepavali = Ashvina `K15`). Ekadashi
underlines use the same rule for every `S11` and `K11`; they are not the
*Dharma-sindhu* four-ghati Arunodaya / Mahadvadashi machinery.

Non-tithi festivals
-------------------

These have dedicated selectors (dispatch by catalog name):

* **Varamahalakshmi Vrata** -- Friday strictly before nija Sravana Purnima
  (`S15`).
* **Yajur Upakarma** -- nija Sravana `S15`. If eclipsed (see below), postpone to
  Bhadrapada `S15`.
* **Rig Upakarma** -- nija day whose sunrise nakshatra is Sravana (`22`); if
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
* **Onam** -- sunrise nakshatra Sravana (`22`) while the Sun is in Simha
  (raasi 5); if none, try Kanya (raasi 6). Same vriddhi / empty-primary
  pattern as Rig Upakarma, but keyed on solar rasi rather than lunar masa, and
  with no eclipse test.
* **Vaikuntha Ekadashi** -- a Margashirsha or Pausha Shukla Ekadashi upavasa
  day while the Sun is in Dhanur at sunrise. If none qualify, the PDF prints
  `None`.
* **Mesha Sankranti** / **Makara Sankranti** -- first civil sunrise after the
  Sun enters Mesha (raasi 1) or Makara (raasi 10) respectively. Both use the
  shared sankranti helper.

Location dependence
-------------------

Dates are sunrise- and location-dependent, so the same festival can fall on
different Gregorian days in different cities. A city inside a polar-night or
midnight-sun period cannot be generated for dates on which Swiss Ephemeris
cannot provide a local sunrise.

Rationale
---------

### Inconsitent sindhu books

*Dharma-sindhu* and *Nirnaya-sindhu* decide many observances with layered kala
tests (Arunodaya, Purvahna, Madhyahna, Aparahna, Pradosha, Nishitha),
viddha/adhikya cases, Bhadra checks, and puja-muhurta detail. That apparatus
matters for ritual timing, but it is a poor fit for a one-page PDF calendar
whose job is to mark which *civil day* carries each festival for a given city
and year. There is usually no consistent logic either; just that regional and
historical preferences are codified in these books. For a universal Hindu, these
principles are meaniningless.

For example, "4-ghati before arunodaya" maps to 96 minutes before sunrise, which
is acceptable in India, but at higher latitudes (e.g. Europe or USA), there
might not be 96 minutes after sunset and next sunrise at all! Another example:
Dussehra is decided by daśamī-during-pūrvāhna in Bengal and Kerala but the rest
of India follows daśamī-during-aparāhna -- there is no logical reason to prefer
one over the other.

Another point of contention is Ekadashi rules between Vaishnavas and
non-Vaishnavas. Before computerised Panchangas, many pandits used to calculate
tithis and nakshatras using simplified arithmetic, which would lead to
inaccuracies. Consider at sunrise daśamī tithi which ends, say, 30 min after
sunrise. Until about a century ago, a temple priest might've computed that day
as ekādaśī-at-sunrise (due to approximate formulas) and unintentionally led a
devotee to fast on the wrong day. Therefore, Vaiṣṇavas came up with a rule: do
not observe fasting on the day when daśamī was still active 48 minutes _before_
sunrise -- this would tolerate computational errors by pandits. A similar logic
was applied for breaking the fast (pāraṇa): do not break fast until 25% of
dvādaśī has elapsed (this would tolerate errors in dvādaśī-at-sunrise
computation). However, we don't need such complexities today, for we can compute
panchanga exactly for any given day and location. Ekadashi fasting is for
spiritual upliftment, not panchanga appeasement.

### Sane rules

This calendar therefore uses a single shared rule for ordinary tithi festivals
and for Ekadashi underlines: *udaya-vyāpinī* (tithi ownership at local sunrise),
with fixed vriddhi and kshaya handling. The aims are:

* One rule that readers can understand without reading a dense book.
* Deterministic dates for any year and location where sunrise exists.
* Enough uniformity that the same engine covers the whole catalog instead of
  a different special case per festival.

Divergence from traditional printed panchangas and from civil holiday lists
is expected and accepted. Two concrete motivations for the vriddhi/kshaya
choices:

* This 'kshaya' logic helps us to avoid celebrating festivals on Amavasya day.
  For example, in India, 2026-03-19 is Amavasya and the next day is
  śukla-dvitīya. Traditional (Dharma-sindhu) calendar celebrates the Hindu New
  Year (Ugadi) on Amavasya day though, according to the same book, Caitra month
  begins on the next day! Would you celebrate the New Year's Day in December
  although the new year begins in January? Nope! Another example: You want to
  enjoy a festival feast on Vijaya Dashami (Dussehra) but the Ekadashi is
  kshaya. As per above the rule, the fasting is pushed to the next day after
  Dussehra, so no problem.

* The 'vriddhi' rule prioritises the principle that one should _never_ eat
  during the maximal window of an ekadashi tithi. For example, in Tirupati, both
  2027-03-03 and 2027-03-04 at sunrise are Ekadashi (no daśamī-vedha). Yet, all
  calendars (incl. Dharma-sindhu, Smarta, Madhva, Srivaishnava) prescribe
  fasting on the latter date, essentially allowing food consumption on the
  entire 3rd March which has ahorātra ekādaśī tithi! Defeats the whole emphasis
  on ekadasi fasting. Different sampradāyas may differ on pāraṇa rules (breaking
  the fast), that's alright, but in my opinion, keeping upavāsa is more
  important.

Ekadashi fast is broken (pāraṇa) on the next day after sunrise, for both normal
and kshaya observances. For the vriddhi case, wait until ekadashi tithi has
ended completely after sunrise (max 4 hrs after sunrise).

Rules that are not plain masa+tithi markers (Sankranti, Onam, Upakarma,
Varamahalakshmi, Vaikuntha Ekadashi) keep dedicated selectors, still written
in the same sunrise-first spirit. The older multi-policy / *Dharma-sindhu*
experiments remain under `experimental/` for comparison.
