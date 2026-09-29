# Plan: bound PDF calendars to one lunar year

Status: proposal only — no code changes in this document.
Goal: stop taking an arbitrary Gregorian start month, print exactly one
cāndramāna year (Ugadi → end of Phālguna) for both the one-page and the
monthly wall-calendar PDFs, and limit those PDFs to the years
`-3300 … 3300`.

Reviewed against `1a92df4b`. Dates and counts marked *measured* come from
running the current code (`daily_records` + `select_plain_tithi_dates`).

## 1. Why

Two recent sources of churn stack badly:

1. **Years far outside ±3000** (astronomical years, BCE, span checks near
   9999, ICS four-digit limits, header year formatting, LMT / no-`datetime`
   paths). Every caller that builds a *multi-month* product has to reason
   about a free-form month count and a free-form start.
2. **`--start YYYY-MM`** lets the user open the calendar on any civil month
   (e.g. 2026-09). The products then print a fixed civil length:
   - one-page / ICS: **14** Gregorian months (`MONTH_COUNT = 14`)
   - monthly wall: **12** pages (`MONTHLY_MONTH_COUNT = 12`)

Neither length is “one lunar year”. A Chaitra→Phālguna year, measured in the
Gregorian months that contain it, is **12, 13 or 14** months (Ujjain,
Citra-paksha, 1900–2100, measured: 12 in 80 years, 13 in 47, 14 in 74). A
lunar year has 354–385 days, so it can never touch 11 or 15 months. So:

- a 12-page wall calendar that starts on Ugadi’s month often **cuts off**
  the end of Phālguna when the next Ugadi falls in April;
- a 14-month one-pager that starts mid-year is not a samvatsara at all, and
  festival / adhika-Chaitra edge logic must keep a wide context margin so a
  neighbouring year’s Ugadi does not leak in (see `4fb41993`). Today that
  margin is 3 months on each side (`9762f2d0`); §4.5 replaces it with a
  33-day pad.

Picking the span from the lunar year removes the free parameter that forces
those guards, aligns the PDF with how the panchāṅga is actually used, and
leaves the deep-year work as a pure date-math concern rather than a
product-shape concern.

## 2. Product rule (normative)

```
--start YYYY
```

means:

> Print the amānta cāndramāna year whose **Ugadi** falls in Gregorian year
> `YYYY`, from the Gregorian month that contains that Ugadi through the
> Gregorian month that contains the last day of Phālguna.

`YYYY` is an astronomical year in `-3300 … 3300`, for every ayanāṃśa. If
`YYYY` holds zero or two Ugadis, the resolver fails with an error that names
the dates. In sidereal modes this happens in some years before about -2950
(§2.1).

Concretely, for a place and ayanāṃśa:

| Anchor | Definition |
| --- | --- |
| **Ugadi** | Civil day of Chaitra śukla 1, with the existing Ugadi rule: prefer **adhika Chaitra** S1 when that year has one (`FestivalRule("Ugadi", … allow_adhika=True)` / `select_plain_tithi_dates(..., allow_adhika=True)`). |
| **Start month** | `(ugadi.year, ugadi.month)` — the Gregorian month containing Ugadi. |
| **End of Phālguna** | Civil day immediately before the **next** Ugadi (nija or adhika). An adhika Phālguna comes before its nija month, so this day is in nija Phālguna. |
| **End month** | Gregorian month of that last Phālguna day. |
| **Printed months** | Inclusive Gregorian month sequence from start month through end month. Length ∈ {12, 13, 14}. |

### Examples (Ujjain, Citra-paksha — measured)

| `--start` | Ugadi | Last Phālguna day | Printed months | Count |
| --- | --- | --- | --- | --- |
| `2026` | 2026-03-20 | 2027-04-06 | 2026-03 … 2027-04 | 14 |
| `2027` | 2027-04-07 | 2028-03-26 | 2027-04 … 2028-03 | 12 |
| `2028` | 2028-03-27 | 2029-03-15 | 2028-03 … 2029-03 | 13 |
| `2029` | 2029-03-16 (**A**Chaitra) | 2030-04-02 | 2029-03 … 2030-04 | 14 |
| `2030` | 2030-04-03 | 2031-03-23 | 2030-04 … 2031-03 | 12 |

So `--start 2026` replaces today’s ad-hoc `--start 2026-03` plus a hope that
14/12 months are enough; the resolver computes the real end.

### 2.1 Year range, and years with zero or two Ugadis

The sidereal year is about 20 minutes longer than the Gregorian year. So in
every sidereal mode, Ugadi moves about one day later every 70–80 years. In
tropical mode it stays in February–March, because the Gregorian calendar
follows the tropical year.

| Year | -3000 | 0 | 2026 | 3000 |
| --- | --- | --- | --- | --- |
| Ugadi (Ujjain, Citra, measured) | Jan 18 | Feb 22 | Mar 20 | Apr 27 |

Near -3300, sidereal Ugadi reaches 1 January. Then one Gregorian year can
hold two Ugadis and the next year none. Example (Revati, Ujjain, measured):
`-3298` has -3298-01-11 and -3298-12-31, and `-3297` has none. Such years
always come in pairs, and the rule refuses both years of a pair.

**Rule:** the range is `-3300 … 3300` for every ayanāṃśa. `YYYY` must hold
**exactly one** Ugadi; otherwise raise `ValueError` and name the dates
found, e.g. “Gregorian year -3298 has two Ugadis at Ujjain (Revati-paksha):
-3298-01-11 and -3298-12-31.” Do not add per-ayanāṃśa year limits.

**Measured: where the rule fails.** Every year was checked, for all
8 coordinate modes, at these places:

- `-3300 … -3001`: Ujjain, Honolulu, Auckland, and longitude ±179.9°
  (latitude 21.3°N).
- `-3000 … 3000`: Ujjain, Honolulu, Auckland, Murmansk; ±179.9° for
  `-3000 … -2000`.
- `3001 … 3300`: Ujjain.

Place matters because pre-modern dates use local mean time; the far-west
places (Honolulu, −179.9°) fail most often.

| Mode | Failing years in `-3300 … -3001` (fewest–most, by place) | Failing years in `-3000 … 3300` |
| --- | --- | --- |
| Tropical | 0 (Ugadi stays ≥ 48 days from 1 January) | 0 |
| Mula | 0 (but Ugadi comes within a day of 1 January) | 0 |
| Citra, Krishnamurti | 0 at Ujjain, Auckland, +179.9°; 6 at Honolulu and −179.9° (Honolulu: `-3271`/`-3270`, `-3252`/`-3251`, `-3176`/`-3175`) | 0 |
| Rohini | 6–20 | 0 |
| Pushya | 8–22 | 0 |
| Raman | 10–24 | 0 |
| Revati | 54–76 | 2, at Honolulu only (`-2956`/`-2955`) |

From 3001 to 3300, sidereal Ugadi stays at least 84 days after 1 January,
so the top of the range never fails.

Result: all failures are before -2950, and most are Revati years before
-3000. Today `--start -3298-01` works; after this change `--start -3298`
fails under Revati-paksha with the error above.

`tests/test_deep_bce.py` locks day-level behaviour back to
`DEEPEST = Date(-3299, 1, 1)` (3300 BCE). Astronomical `-3300` is 3301 BCE,
and `--start -3300` reads even earlier days: the resolver's search window
starts on 1 November -3301 (§4.2). Move `DEEPEST` to `Date(-3301, 11, 1)`
so every day a PDF can read is inside the tested range.

### 2.2 Days outside the lunar year

Whole Gregorian months are printed. So the first month has days before Ugadi
(Phālguna of the previous year), and the last month has days after the last
Phālguna day (Chaitra of the next year, including the next Ugadi).

- Print these days in full, **festivals included**, exactly as today:
  `target_dates` stays every printed day. So `--start 2026` lists
  `Ugadi: Mar 20,Apr 07` in the footer. This is intended.
- Consecutive calendars share one month: the month of Ugadi `YYYY+1` is the
  last month of `YYYY` and the first month of `YYYY+1`. This is expected.

### 2.3 What does *not* change

- **`--month amanta|purnimanta`** still only affects *display* māsa names and
  badges. The **span** is always the amānta Chaitra→Phālguna year (Ugadi is
  defined that way in the festival catalog). Do not start a “pūrṇimānta year”
  at Kārttika or shift the span when the user picks pūrṇimānta.
- Day-view / single-date APIs (`DD/MM/YYYY`) stay as they are, including
  their `-9999 … 9999` range. Only the PDFs and ICS get the new limit.
- Core astronomy (`panchanga.py`) stays as it is; this is a calendar-product
  boundary change.

## 3. Public interface changes

### 3.1 CLI (`drik-panchanga-short`, `drik-panchanga-long`)

| Before | After |
| --- | --- |
| `--start YYYY-MM` (required) | `--start YYYY` (required) |
| metavar / help talk about “first of 14/12 months” | metavar `YYYY`; help: astronomical year; span = lunar year of Ugadi in that year |
| BCE: `--start -500-03` | BCE: `--start -500` (and `0000` = 1 BCE), still via `attach_option_values` so a leading `-` is not another flag |
| any year `-9999 … 9999` | `-3300 … 3300` |

Replace `require_start_month` with `require_start_year(text) -> int`:

- Accept `-\d{1,4}` or `\d{4}`: the rule from `f1a5c05c` stays, so positive
  years have four digits (`0500`, `0000`). This matters more now, because
  `26` alone could mean 26 CE or 2026.
- Reject years outside `-3300 … 3300` with a clear message, before any
  records are computed.
- Reject `YYYY-MM` with an explicit error (“use `--start YYYY`; the month is
  taken from Ugadi”), so old scripts fail loudly instead of being misread.

### 3.2 Builder signatures

Today:

```text
build_pdf(location, start_year, start_month, ...)
build_monthly_pdf(location, start_year, start_month, ...)
generate_ics(location, start_year, start_month, ...)
```

Move to a **resolved month list in**:

```text
months = lunar_year_months(start_year, location, coordinate_selection)
# -> [(y, m), ...], length 12..14

build_pdf(location, months, output_path, ...)
build_monthly_pdf(location, months, output_path, ...)
default_output_path(location, months, ...)
default_monthly_output_path(location, months, ...)
generate_ics(location, start_year, ...)   # resolves inside; no filename needs it
```

The resolver sets the coordinate selection itself and takes
`panchanga.coordinate_calculation_lock`. That lock is an `RLock`, so
`generate_ics` can call the resolver while it holds the lock.

**Why the PDF builders take the resolved months:** today both CLI `main()`
functions and `webapp/pdf_service.generate_pdf` build the default filename
*before* the builder runs, outside the lock, from `start_year, start_month`
alone. After this change the filename depends on the resolved span (§3.4).
So the callers resolve once, build the filename from it, and pass the same
list to the builder. Nothing resolves twice. Layout tests pass a month list
directly, so no extra helper is needed.

### 3.3 Web form + CGI + JSON clients

- `start` field: year only. Replace `<input type="month">` with a text input
  (`inputmode="numeric"`, `pattern="-?\d{1,4}"`) that uses the CLI grammar.
  Do not use `type="number"`: it turns `0500` into `500`, and the parser
  rejects `500`.
- Label “First month” → “Lunar year (Ugadi in)”. The JS default
  (`${y}-${m}` in `index.html`) becomes the current year. The ICS button
  message “Pick a first month.” and the CSS selector `input[type="month"]`
  change with it.
- Hints / button labels: drop “fourteen consecutive months”, “twelve pages”
  and “Generate monthly PDF (12 pages)”; say “one lunar year (Ugadi through
  Phālguna)” and “one page per Gregorian month in that year (12–14 pages)”.
- `pdf_service.generate_pdf` / `cgi_handlers` / ICS query params: parse year,
  not `YYYY-MM`. Also update the CGI 405 message “start (YYYY-MM)”.
- Error copy: a year outside `-3300 … 3300` is a 400 that states the range.
  A year with zero or two Ugadis (§2.1) is also a 400, with the dates found
  in the body.

### 3.4 Filenames

Keep today’s patterns, filled from the **resolved** span. Ugadi falls in
`YYYY` (§2), so the start month’s year is always `YYYY`. The
`{start}_to_{end}` part therefore already names the lunar year. A separate
`{YYYY}` would only repeat it.

```text
one-page: {city}_panchanga_{startYYYY-MM}_to_{endYYYY-MM}[_{suffix}].pdf
monthly:  {city}_panchanga_wall_{startYYYY-MM}_to_{endYYYY-MM}[_{suffix}].pdf
ICS:      panchanga-{city}-{coordinate}-{amanta|purnimanta}-{YYYY}.ics
```

Examples: `ujjain-in_panchanga_2026-03_to_2027-04.pdf` (this is the name CI
checks today), and `ujjain-in_panchanga_wall_2026-03_to_2027-04.pdf` (CI
checks `…_wall_2026-03_to_2027-02.pdf` today).

The resolved months in the PDF name make two runs diffable when Ugadi’s
month shifts under a different ayanāṃśa. `webapp/app.py` builds the ICS name
from request fields. The coordinate is already in that name, so `YYYY` is
enough there and the ICS route does not need the resolved span.

### 3.5 Docs / samples

Update in the same change set (not a follow-up):

- `README.md` CLI examples (L109–114) and “export the 14-month span as
  iCal” (L142)
- `docs/README.CALENDARS.md`: “14 consecutive months” (L7), common options
  (L21–22), example section title, image alt text (L130)
- `docs/README.pypi.md` one-liners
- Web template hints (§3.3)
- Docstrings and comments: `generate_monthly_calendar.py` module docstring
  (“12-month”, “14 months”), `webapp/ics_service.py` module docstring,
  `month_range` (the context helpers are deleted, §4.5), `panchanga.py` cache comment
  (“one 14-month PDF build”)
- Screenshots `samples/ujjain_panchanga_mar2026_mar2027.png` and
  `samples/ujjain_monthly_march2026.png`: regenerate from `--start 2026`.
  The first becomes `…_mar2026_apr2027.png`; update its link in
  `docs/README.CALENDARS.md`. (No `sample-pdfs/` directory exists.)

## 4. Core algorithm: `lunar_year_months`

Place this next to the other span helpers in `generate_panchanga_calendar.py`
(shared by monthly, one-page, ICS, web).

### 4.1 Inputs

- `start_year: int` (astronomical, already checked by `require_start_year`)
- `location` (lat/lon/tz) — sunrise boundary is place-dependent
- `coordinate_selection`: the resolver sets it under the lock (§3.2)

Records come from `daily_records`. It always computes amānta māsa, so
`--month` cannot change the result.

### 4.2 Steps

1. **Search window for Ugadi in `start_year`**: 1 Nov `start_year-1`
   through 31 Dec `start_year` (14 months).
   - It covers the **whole** year. Then the window does not depend on where
     Ugadi falls: on 1 January or even 31 December near -3300, and in late
     April or later near 3300 (§2.1). The whole year is also what makes a
     second Ugadi in the same year visible, so the check in step 2 can see
     it. The cost is about 0.1 s more than a January–June window.
   - The two-month lead-in is required. With `allow_adhika=True`,
     `select_plain_tithi_dates` drops a nija Chaitra only if it sees the
     adhika Chaitra earlier in the same records. Suppose adhika Chaitra falls
     in December and the window starts on 1 January: the nija Chaitra S1
     would then count as a false Ugadi of `start_year`. The lead-in also
     gives `select_kshaya_dates` the previous day it needs.

2. **Select Ugadi**  
   `select_plain_tithi_dates(records, 1, "S1", allow_adhika=True)` filtered to
   `civil_date.year == start_year`.  
   - Exactly one hit → that day is Ugadi.  
   - Zero or two hits → `ValueError` that names the hits (§2.1). Inside the
     range this is a real case (sidereal years before about -2950), not an
     unreachable guard, so it needs tests.

3. **Search window for the next Ugadi**: Ugadi’s month through 13 months
   later (14 months). The next Ugadi is at most 385 days later, so it is
   always inside. Because the window starts at Ugadi’s month, the adhika
   logic works: after an adhika Ugadi its nija Chaitra is dropped, and next
   year’s adhika Chaitra S1 comes before its nija. Take the smallest selected
   date that is later than this Ugadi.

4. **Last printed day** = `next_ugadi - 1`. `Date` supports day arithmetic
   for every year (`select_varamahalakshmi_dates` already uses it), so no
   `datetime.timedelta` is needed.

5. **Month list** = `_month_sequence(ugadi.year, ugadi.month, count)` with
   `count` derived from `(last.year, last.month)`.

6. **No year-10000 guard.** `require_start_year` limits the year to
   `-3300 … 3300`, so every window and day pad (§4.5) ends before 3302.
   `require_supported_span` existed only to stop spans near 9999-12. It is
   now dead code: delete it and its three call sites (both builders and
   `generate_ics`).

### 4.3 Efficiency

Resolving needs two 14-month windows of daily records, which overlap.
Measured on the dev box: `daily_records` for 16 months at Ujjain takes about
0.25 s. A full PDF build takes much longer than that. So resolve in a
separate short pass, then let the builder read its own records (§4.5).
Most of the second pass hits the `lru_cache`s in `panchanga.py`. A single
shared pass would save well under a second and needs more refactoring; do
not do it.

### 4.4 Reuse of festival logic

Do **not** reimplement adhika-Ugadi preference. Call the same
`select_plain_tithi_dates(..., allow_adhika=True)` path the Ugadi festival
uses, so calendar bounds and the Ugadi footnote can never disagree.

### 4.5 Records the builders read: a day pad, no context months

Today both builders read 3 extra months on each side of the printed span
(`CONTEXT_MARGIN_MONTHS = 3`, from `9762f2d0`): 20 months for the 14-month
one-page PDF and 18 for the 12-page monthly PDF. That margin exists because
an arbitrary start month could cut a kṣaya or adhika month in half; the
case was Rig Upakarma 8 Sep 2022, missing from a calendar that started in
September 2022.

A lunar-year span removes that cause. The only month-level rules are Rig
and Sama Upakarma (Śrāvaṇa / Bhādrapada), Onam (solar Siṃha / Kanyā) and
the adhika-Chaitra preference for Ugadi. Their months are always well inside
the printed year and never at its edges. At the edges are the previous
Phālguna and the next Chaitra.

Some rules still read a day or two past the printed edges, and the solar
day number counts from the last saṅkrānti:

| Output on printed days | Reads | Pad needed |
| --- | --- | --- |
| Solar day number (every monthly cell; every 7th day on the one-page) | back to the sunrise after the last saṅkrānti; a solar month can be 32 sunrises | 32 days before |
| Ekādaśī pāraṇa on the first printed day | the upavāsa day before it, and that day's own vṛddhi / kṣaya check | 2 days before |
| Vṛddhi / kṣaya of festival tithis, Ekādaśī, Pradoṣa, Saṅkaṣṭī; Meṣa Saṅkrānti on the first day | the previous sunrise, sunset or moonrise | 1 day before |
| Eclipse before sunrise on the day after the last printed day (it belongs to the last printed day) | that day's sunrise | 1 day after |

**Rule:** both builders read records from `first printed day - 32` through
`last printed day + 1`. Delete `CONTEXT_MARGIN_MONTHS`,
`context_month_sequence`, `context_month_range` and the monthly
`context_months`. Add a date-range form, `daily_records_between(first,
last, location)`, and let `daily_records(months, location)` wrap it; the
tests keep using the month form. Everything else stays as today: selectors
see all records, and only printed dates are drawn.

**Measured.** Every output on the printed days was compared against today's
3-month margin. Outputs checked: festival markers, Ekādaśī, Pradoṣa,
Saṅkaṣṭī, pāraṇa, solar day, the monthly māsa badges and eclipse dates.
Lunar years checked: Ujjain 1900–2100 and Helsinki 1990–2059 (every year),
Ujjain Citra `-3300 … -2000`, Revati `-3300 … -2900`, tropical
`-3300 … 3300` and Citra `2100 … 3300` (sampled), 523 in total.

| Pad (days before / after) | Differences from the 3-month margin |
| --- | --- |
| 0 / 0 | Solar day wrong at the start of every calendar. Pāraṇa, Ekādaśī, Pradoṣa, Saṅkaṣṭī or eclipse wrong on an edge day in 5–12 % of years. |
| 2 / 1 | Solar day still wrong in most calendars. |
| 32 / 1 | None. |

The 33 pad days replace about 180 margin days.

## 5. Layout consequences

### 5.1 One-page (annual) PDF

Already sizes columns with `len(months)`:

```text
month_width = (usable_width - day_column_width) / len(months)
```

So 12 / 13 / 14 columns work without a new grid. Verify:

- minimum readable column width at 14 (current design point);
- at 12, columns get wider — no overflow expected; spot-check badge + festival
  marker collision (`519ccf41`);
- header `month_span_label`, Kali ahargaṇa range, eclipse line all take the
  resolved `months` list (they already accept a list).

Festivals: no change. `target_dates` stays every printed day (§2.2). The
footer slot budget (`FOOTER_FESTIVAL_SLOTS = 30`) counts festivals, not
dates, so a festival with two dates still uses one slot. Today’s 14-month
calendars already print such entries.

`calendar_year_label` reads the middle printed month. With a lunar-year span
that month is always inside the year, so the header samvatsara is correct
without changes.

### 5.2 Monthly wall PDF

- Page count = `len(months)` (12–14), not a constant 12.
- Footer `page index / total` already parameterized — pass the real total.
- Title string: “Panchanga lunar year {YYYY} (Mon YYYY – Mon YYYY)” rather
  than “from start month for 12 months”.
- Context collection: `collect_context` reads the same day pad as the
  one-page builder (§4.5), not context months.
### 5.3 ICS

Same resolved month list as the one-page calendar (whole months). Today
`generate_ics` never calls `daily_records`. Resolving adds that one pass,
inside the lock that `generate_ics` already takes. BCE rejection stays
(`start_year < 1` → 400), so ICS years are `1 … 3300`. The far-future span
check goes away with `require_supported_span` (§4.2). Consecutive years share
one month. The UID (`panchanga-{coordinate}-{month}-{date}@{city}`) is the
same in both files, so importing both years does not duplicate those days.

## 6. Edge cases to specify up front

| Case | Behaviour |
| --- | --- |
| Adhika Chaitra year (`2029`) | Span starts at adhika Ugadi; nija Chaitra is inside the same PDF; next year’s `--start 2030` starts at nija Ugadi 2030. |
| Adhika Phālguna | Included: end is still “day before next Ugadi”. |
| `--month purnimanta` | Display only; span unchanged. |
| Ayanāṃśa / tropical changes Ugadi’s civil day across a month boundary | Filename and span follow the **active** coordinate selection; document that lunar-year bounds are place- and ayanāṃśa-dependent. |
| Ugadi on the 1st of the month | Start month still that month; no special case. |
| Last Phālguna day on the 1st | End month is that month. The whole month is printed, but only its first day is in the lunar year (§2.2). |
| Days before Ugadi / after the last Phālguna day | Printed in full, festivals included (§2.2). |
| Consecutive years | Share one month (Ugadi `YYYY+1`’s month); expected. |
| Sidereal year with zero or two Ugadis (before about -2950, e.g. Revati `-3298`/`-3297` anywhere, Citra `-3271`/`-3270` at Honolulu) | `ValueError` / 400 that names the Ugadi dates found (§2.1). |
| Tropical mode, any year in range | Always exactly one Ugadi; it stays in February–March, at least 48 days from 1 January (measured every year). |
| Year with no computable sunrise / ephemeris hole | Same failure mode as today’s PDF build for that place/date; surface as `ValueError`. |
| `--start -3301`, `--start 3301` | Rejected by the parser; the message states `-3300 … 3300`. |
| Old clients sending `2026-03` | Explicit parse error pointing at `--start YYYY`. Old ICS subscription URLs with `start=YYYY-MM` get a 400. |

## 7. Code touch map (implementation checklist)

| Area | Files (expected) |
| --- | --- |
| Span helper + year parser | `generate_panchanga_calendar.py` (`require_start_year` with the `-3300 … 3300` range, `lunar_year_months`, delete `require_supported_span`, `main()` resolves before `default_output_path`; drop fixed `MONTH_COUNT` as *the* product length; `daily_records_between` and the day pad replace `CONTEXT_MARGIN_MONTHS` / `context_month_sequence` / `context_month_range`, §4.5) |
| Monthly builder | `generate_monthly_calendar.py` (variable pages, CLI help, default path, module docstring; delete `context_months`, `collect_context` reads the day pad) |
| ICS | `webapp/ics_service.py` (resolve under the lock, drop `require_supported_span`, docstring) |
| Web PDF | `webapp/pdf_service.py` (resolve before choosing filename), `webapp/app.py` (ICS `start` + filename), `webapp/cgi_handlers.py` (405 message), `webapp/templates/index.html` (§3.3) |
| Docs | `README.md`, `docs/README.CALENDARS.md`, `docs/README.pypi.md` (§3.5) |
| CI / scripts | `.github/workflows/ci.yml` (`--start 2026-03` ×2, and the expected `_wall_…_to_2027-02.pdf` name), `scripts/ci_smoke_http.sh` (`start=2026-03` ×2, `start=2023-03`), `scripts/setup_venv.sh` (`--start 2026-03`) |
| Tests | `tests/test_pdf_layout.py`, `tests/test_monthly_calendar.py` (`test_generates_exactly_twelve_pages`), `tests/test_pdf_service.py` (form + ICS `start=2026-03`), `tests/test_custom_location.py` (`BceStartMonthTests`, whose `-5000-12` “oldest supported year” case is now out of range; `attach_option_values` with `-500-03`; BCE CLI / ICS / web), `tests/test_bce_ce_boundary.py` (`build_pdf(…, -500, 3, …)`), `tests/test_deep_bce.py` (`DEEPEST` → `Date(-3301, 11, 1)`, §2.1), context-margin tests (`test_month_ranges_cross_january_and_december` in `test_pdf_layout.py`, `test_context_months_adds_buffer` in `test_monthly_calendar.py`, the Tirupati 2086 Vaikuntha test that filters out the Dec 2085 date from the margin), `tests/test_day_panchanga.py` (ICS `start=9999-12` must still be a 400, now from the range check), `tests/test_festival_rules.py` (uses `month_range` / `context_month_range` as 14-month fixtures; `context_month_range` is deleted, so give those tests their own month lists); add focused unit tests for `lunar_year_months` |
| Samples | `samples/*.png` (§3.5) |

No change required for: `panchanga.py` māsa maths (only the cache comment in
§3.5), `festival_rules.py` catalog (unless a tiny shared “ugadi_dates” helper
is extracted), day panchāṅga, wx GUI day view.

## 8. Tests

Unit (fast, no full PDF where possible):

1. **Parser**: `2026`, `0000`, `0500`, `-500`, `-3300`, `3300` OK. `2026-03`
   fails with the “use `--start YYYY`” hint. `-3301`, `3301`, `9999`, `0`,
   `500`, `26`, `""` fail with stable messages.
2. **Resolver fixtures** (Ujjain, citra), the measured dates in §2:
   - `2026` → 2026-03 … 2027-04 (14)
   - `2027` → 2027-04 … 2028-03 (12)
   - `2028` → 2028-03 … 2029-03 (13)
   - `2029` → starts 2029-03, Ugadi 2029-03-16 on adhika Chaitra
   - `2030` → 2030-04 … 2031-03 (12)
3. **Length invariant**: for a handful of years, `12 <= len(months) <= 14` and
   first day of first month ≤ Ugadi ≤ last day of last month, and next Ugadi
   is after the last printed day.
4. **Pūrṇimānta flag does not change `lunar_year_months` result.**
5. **Builders**: one-page and monthly accept a year and produce page/column
   counts equal to `len(months)`; default filenames follow §3.4.
6. **Web**: form/API reject `YYYY-MM`; accept `YYYY`; ICS uses the same span.
7. **Regression**: adhika-Chaitra Ugadi preference still matches festival
   selection inside the printed year (no previous-year nija drop).
8. **Range edges**: `-3300` and `3300` resolve for every coordinate mode at
   Ujjain (16 fast cases; measured: the first failing year at Ujjain is
   `-3298`).
9. **Zero or two Ugadis** (§2.1), Revati at Ujjain: `-3298` raises
   `ValueError` naming -3298-01-11 and -3298-12-31; `-3297` raises for no
   Ugadi.
10. **Festivals outside the lunar year** (§2.2): `--start 2026` still lists
    Ugadi as `Mar 20,Apr 07`.
11. **Day pad** (§4.5), Ujjain, Citra (measured): with `--start 2026`,
    2026-03-01 is Kumbha solar day 17, not 1. With `--start 1905`, the
    pāraṇa on 1905-04-01 belongs to the Ekādaśī upavāsa of 1905-03-31.

Keep one smoke PDF build in CI per layout (already present) with `--start 2026`.

## 9. Implementation order

1. Add `require_start_year` + `lunar_year_months` with unit tests (no CLI switch yet).
2. Point **one-page** builder + CLI + default path at the helper; update its tests/docs examples and the first CI smoke line.
3. Point **monthly** builder + CLI the same way, with the second CI smoke line and its expected filename.
4. Web + ICS + template copy + `scripts/ci_smoke_http.sh`.
5. Delete or narrow dead fixed constants (`MONTH_COUNT` / `MONTHLY_MONTH_COUNT` as product lengths); keep only what layout math and tests still need.
6. Regenerate samples; grep the repo (outside `experimental/`) for `YYYY-MM`, `--start 20`, `start=20`, “14 month”, “14-month”, “fourteen”, “12-month”, “twelve”, “12 page”, “First month”, `type="month"` and clean stragglers.
7. Changelog / release note: breaking CLI/API change — `--start` is now a year.

## 10. Breaking-change note (for RELEASES / commit message)

```text
breaking(cli): --start takes YYYY (lunar year of Ugadi), not YYYY-MM

One-page, monthly, ICS and web PDF spans are the amānta year from the
Gregorian month of Ugadi (adhika Chaitra when present) through the month
containing the end of Phālguna. Length is 12–14 civil months.

PDF and ICS years run from -3300 to 3300 (ICS from 1 CE) for every
ayanamsa. The day view keeps -9999 to 9999. In sidereal modes some years
before about -2950 hold zero or two Ugadis; those years fail with an
error that names the dates.
```

No compatibility shim for `YYYY-MM` unless a later request needs one; a clear
error is enough for a still-young CLI.

## 11. Out of scope

- Solar (sauramāna) year calendars (Mesha saṅkrānti → next).
- Vikram / Śaka year labels as the *input* (output headers already show them).
- PDF / ICS years outside `-3300 … 3300`.
- Printing the sidereal years that fail the one-Ugadi rule (§2.1). That
  needs a different year rule, e.g. numbering lunar years by Śaka year.
- North-Indian “year starts at Kārttika” product mode.
- Changing festival cfg or ruleset version solely for this work.
- Re-opening ephemeris / BCE datetime refactors except where the new parser
  touches them.

## 12. Success criteria

- `drik-panchanga-short --city Ujjain --start 2026` and
  `drik-panchanga-long --city Ujjain --start 2026` each cover Ugadi 2026
  through the last day before Ugadi 2027, no more and no less (at month
  granularity).
- `--start 2026-09` is rejected.
- Adhika-Chaitra years are correct without special CLI flags.
- Monthly page count and one-page column count track the resolved span.
- Test suite encodes the three length classes (12 / 13 / 14) with at least one
  fixed year each (`2027` / `2028` / `2026`).
- `--start -3301` and `--start 3301` are rejected; `-3300` and `3300` build.
- A year with zero or two Ugadis fails with a message that names the dates.
- Festivals on printed days outside the lunar year still appear (§2.2).
- CI smoke steps pass with `--start 2026` and the §3.4 filenames.
- Docs and web UI no longer tell users to pick a first Gregorian month.
