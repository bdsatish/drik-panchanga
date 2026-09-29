# Plan: bound PDF calendars to one lunar year

Status: proposal only — no code changes in this document.
Goal: stop taking an arbitrary Gregorian start month, and print exactly one
cāndramāna year (Ugadi → end of Phālguna) for both the one-page and the
monthly wall-calendar PDFs.

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
1900–2100 sample: 12 ≈ 40 %, 13 ≈ 23 %, 14 ≈ 37 %). So:

- a 12-page wall calendar that starts on Ugadi’s month often **cuts off**
  the end of Phālguna when the next Ugadi falls in April;
- a 14-month one-pager that starts mid-year is not a samvatsara at all, and
  festival / adhika-Chaitra edge logic must keep a wide context margin so a
  neighbouring year’s Ugadi does not leak in (see `4fb41993`).

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

Concretely, for a place and ayanāṃśa:

| Anchor | Definition |
| --- | --- |
| **Ugadi** | Civil day of Chaitra śukla 1, with the existing Ugadi rule: prefer **adhika Chaitra** S1 when that year has one (`FestivalRule("Ugadi", … allow_adhika=True)` / `select_plain_tithi_dates(..., allow_adhika=True)`). |
| **Start month** | `(ugadi.year, ugadi.month)` — the Gregorian month containing Ugadi. |
| **End of Phālguna** | Civil day immediately before the **next** Ugadi (nija or adhika). That day is always in Phālguna (nija, or adhika Phālguna when present). |
| **End month** | Gregorian month of that last Phālguna day. |
| **Printed months** | Inclusive Gregorian month sequence from start month through end month. Length ∈ {12, 13, 14}. |

### Examples (Ujjain, Citra-paksha — illustrative)

| `--start` | Ugadi | Last Phālguna day | Printed months | Count |
| --- | --- | --- | --- | --- |
| `2026` | 2026-03-20 | 2027-04-06 | 2026-03 … 2027-04 | 14 |
| `2029` | 2029-03-16 (**A**Chaitra) | 2030-04-02 | 2029-03 … 2030-04 | 14 |
| `2030` | 2030-04-03 | 2031-03-23 | 2030-04 … 2031-03 | 12 |

So `--start 2026` replaces today’s ad-hoc `--start 2026-03` plus a hope that
14/12 months are enough; the resolver computes the real end.

### What does *not* change

- **`--month amanta|purnimanta`** still only affects *display* māsa names and
  badges. The **span** is always the amānta Chaitra→Phālguna year (Ugadi is
  defined that way in the festival catalog). Do not start a “pūrṇimānta year”
  at Kārttika or shift the span when the user picks pūrṇimānta.
- Day-view / single-date APIs (`DD/MM/YYYY`) stay as they are.
- Core astronomy (`panchanga.py`) stays as it is; this is a calendar-product
  boundary change.

## 3. Public interface changes

### 3.1 CLI (`drik-panchanga-short`, `drik-panchanga-long`)

| Before | After |
| --- | --- |
| `--start YYYY-MM` (required) | `--start YYYY` (required) |
| metavar / help talk about “first of 14/12 months” | metavar `YYYY`; help: astronomical year; span = lunar year of Ugadi in that year |
| BCE: `--start -500-03` | BCE: `--start -500` (and `0` = 1 BCE), still via `attach_option_values` so a leading `-` is not another flag |

Replace `require_start_month` with something like `require_start_year(text) -> int`:

- Accept `-?\d{1,4}` with the same “positive years are four digits” rule already
  enforced for months (`f1a5c05c`), or a single clear year grammar documented
  once.
- Reject `YYYY-MM` with an explicit error (“use `--start YYYY`; the month is
  taken from Ugadi”), so old scripts fail loudly instead of being misread.

### 3.2 Builder signatures

Today:

```text
build_pdf(location, start_year, start_month, ...)
build_monthly_pdf(location, start_year, start_month, ...)
generate_ics(location, start_year, start_month, ...)
```

Move to **year-in, resolved span inside** (preferred):

```text
build_pdf(location, start_year, ...)
build_monthly_pdf(location, start_year, ...)
generate_ics(location, start_year, ...)
```

Internally the first step is always:

```text
months = lunar_year_months(start_year, location, coordinate_selection)
# -> [(y, m), ...] length 12..14
```

Keep a thin internal helper that still takes an explicit month list so layout
tests can feed a fixed sequence without re-resolving Ugadi.

### 3.3 Web form + CGI + JSON clients

- `start` field: year only (replace `<input type="month">` with a year control
  or plain text with the same grammar as the CLI).
- Hints / button labels: drop “fourteen consecutive months” / “twelve pages”;
  say “one lunar year (Ugadi through Phālguna)” and “one page per Gregorian
  month in that year (12–14 pages)”.
- `pdf_service.generate_pdf` / `cgi_handlers` / ICS query params: parse year,
  not `YYYY-MM`.
- Error copy: out-of-range year stays 400; “no Ugadi in this year” (should be
  unreachable for normal ephemeris years — see §5) stays 400 with a clear body.

### 3.4 Filenames

Prefer encoding the **lunar year** and the resolved civil span:

```text
{city}_panchanga_{YYYY}_{startYYYY-MM}_to_{endYYYY-MM}[_{suffix}].pdf
```

Example: `ujjain-in_panchanga_2026_2026-03_to_2027-04.pdf`.

ICS attachment names follow the same pattern. Keeping the resolved months in
the name makes two runs diffable when Ugadi’s month shifts under a different
ayanāṃśa.

### 3.5 Docs / samples

Update in the same change set (not a follow-up):

- `README.md` CLI examples
- `docs/README.CALENDARS.md` (common options, example section title)
- `docs/README.pypi.md` one-liners
- Web template hints
- Sample PDFs / screenshots that still say “Mar 2026 – Mar 2027” as if the
  user chose March: regenerate from `--start 2026` and retitle as the lunar
  year

## 4. Core algorithm: `lunar_year_months`

Place this next to the other span helpers in `generate_panchanga_calendar.py`
(shared by monthly, one-page, ICS, web).

### 4.1 Inputs

- `start_year: int` (astronomical)
- `location` (lat/lon/tz) — sunrise boundary is place-dependent
- active coordinate mode / ayanāṃśa (already process-global under the
  coordinate lock; callers must enter the lock before resolving, same as
  today’s `build_*`)

### 4.2 Steps

1. **Search window for Ugadi in `start_year`**  
   Build daily records for a small civil window that always contains Chaitra
   S1 for that Gregorian year, e.g. **January–June of `start_year`**, plus a
   short margin on each side if we want to reuse existing month iterators
   (Feb–May is enough in practice; Jan–Jun is safer and cheap).

2. **Select Ugadi**  
   `select_plain_tithi_dates(records, 1, "S1", allow_adhika=True)` filtered to
   `civil_date.year == start_year`.  
   - Exactly one hit → that day is Ugadi.  
   - Zero hits → `ValueError` (“no Ugadi in Gregorian year …”).  
   - Multiple hits → should not happen with `allow_adhika=True` (adhika year
     keeps adhika, drops following nija); if it does, treat as a hard error so
     we notice.

3. **Search window for the next Ugadi**  
   From roughly `ugadi` through `ugadi + ~14 civil months` (e.g. months from
   Ugadi’s month through thirteen months later). Select the next S1 Chaitra
   (adhika-aware) **strictly after** this Ugadi.

4. **Last printed day** = day before next Ugadi (iterate the in-memory civil
   dates already computed; do not depend on `datetime.timedelta` for BCE).

5. **Month list** = `_month_sequence(ugadi.year, ugadi.month, count)` with
   `count` derived from `(last.year, last.month)`.

6. **`require_supported_span`** runs on the *resolved* list (still reject
   spans that touch 9999-12 / year 10000), not on a fixed 12/14.

### 4.3 Efficiency

Resolving the span needs ~6 + ~14 months of daily records once. The PDF
builders already compute a wider context (`CONTEXT_MARGIN_MONTHS = 3` on each
side of the printed span). Options, in order of preference:

1. **Resolve with a dedicated short pass**, then run the existing
   `daily_records(context_months(...))` as today (simplest, two passes, fine
   for CLI/web).
2. **Resolve inside one wide pass** (e.g. always load
   `start_year-01 .. start_year+1-06` plus margin, derive months, filter
   `target_dates`) — fewer Swiss Ephemeris walks, more refactor.

Start with (1); switch to (2) only if profiling says the double pass matters.

### 4.4 Reuse of festival logic

Do **not** reimplement adhika-Ugadi preference. Call the same
`select_plain_tithi_dates(..., allow_adhika=True)` path the Ugadi festival
uses, so calendar bounds and the Ugadi footnote can never disagree.

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

Footer festival slot budget (`FOOTER_FESTIVAL_SLOTS = 30`) is unchanged: still
one lunar year’s festivals.

### 5.2 Monthly wall PDF

- Page count = `len(months)` (12–14), not a constant 12.
- Footer `page index / total` already parameterized — pass the real total.
- Title string: “Panchanga lunar year {YYYY} (Mon YYYY – Mon YYYY)” rather
  than “from start month for 12 months”.
- Context collection: `context_month_sequence(start_y, start_m, len(months))`
  — same margin policy; a span that *is* one lunar year reduces
  cross-samvatsara festival leakage but **keep** the margin for rules that
  look at neighbouring māsa (Upākarma / Onam fallbacks, etc.).

### 5.3 ICS

Same resolved month list as the one-page calendar. BCE rejection stays
(`start_year < 1` → 400). Far-future span check uses resolved end, not
`+14`.

## 6. Edge cases to specify up front

| Case | Behaviour |
| --- | --- |
| Adhika Chaitra year (`2029`) | Span starts at adhika Ugadi; nija Chaitra is inside the same PDF; next year’s `--start 2030` starts at nija Ugadi 2030. |
| Adhika Phālguna | Included: end is still “day before next Ugadi”. |
| `--month purnimanta` | Display only; span unchanged. |
| Ayanāṃśa / tropical changes Ugadi’s civil day across a month boundary | Filename and span follow the **active** coordinate selection; document that lunar-year bounds are place- and ayanāṃśa-dependent. |
| Ugadi on the 1st of the month | Start month still that month; no special case. |
| Last Phālguna day on the 1st | End month is that month (one day printed); correct. |
| Year with no computable sunrise / ephemeris hole | Same failure mode as today’s PDF build for that place/date; surface as `ValueError`. |
| `--start 9998` / near 9999 | Resolver + `require_supported_span` reject if the lunar year would touch the forbidden end. |
| Old clients sending `2026-03` | Explicit parse error pointing at `--start YYYY`. |

## 7. Code touch map (implementation checklist)

| Area | Files (expected) |
| --- | --- |
| Span helper + year parser | `generate_panchanga_calendar.py` (`require_start_year`, `lunar_year_months`, drop fixed `MONTH_COUNT` as *the* product length; keep only as max/legacy if needed) |
| Monthly builder | `generate_monthly_calendar.py` (variable pages, CLI help, default path) |
| ICS | `webapp/ics_service.py` |
| Web PDF | `webapp/pdf_service.py`, `webapp/app.py`, `webapp/cgi_handlers.py`, `webapp/templates/index.html` |
| Docs | `README.md`, `docs/README.CALENDARS.md`, `docs/README.pypi.md` |
| Tests | `tests/test_pdf_layout.py`, `tests/test_monthly_calendar.py`, `tests/test_pdf_service.py`, webapp ICS tests if any; add focused unit tests for `lunar_year_months` |
| Samples | `samples/`, `sample-pdfs/` regenerate under the new naming |

No change required for: `panchanga.py` māsa maths, `festival_rules.py` catalog
(unless a tiny shared “ugadi_dates” helper is extracted), day panchāṅga,
wx GUI day view.

## 8. Tests

Unit (fast, no full PDF where possible):

1. **Parser**: `2026`, `0`, `-500` OK; `2026-03`, `26`, `""` fail with stable messages.
2. **Resolver fixtures** (Ujjain, citra), locked civil dates:
   - `2026` → months 2026-03 … 2027-04 (14)
   - `2029` → starts 2029-03, Ugadi on adhika Chaitra
   - `2030` → 2030-04 … 2031-03 (12)
3. **Length invariant**: for a handful of years, `1 <= len(months) <= 14` and
   first day of first month ≤ Ugadi ≤ last day of last month, and next Ugadi
   is after the last printed day.
4. **Pūrṇimānta flag does not change `lunar_year_months` result.**
5. **Builders**: one-page and monthly accept a year and produce page/column
   counts equal to `len(months)`; default filenames contain the year and the
   resolved span.
6. **Web**: form/API reject `YYYY-MM`; accept `YYYY`; ICS uses the same span.
7. **Regression**: adhika-Chaitra Ugadi preference still matches festival
   selection inside the printed year (no previous-year nija drop).

Keep one smoke PDF build in CI per layout (already present) with `--start 2026`.

## 9. Implementation order

1. Add `require_start_year` + `lunar_year_months` with unit tests (no CLI switch yet).
2. Point **one-page** builder + CLI + default path at the helper; update its tests/docs examples.
3. Point **monthly** builder + CLI the same way.
4. Web + ICS + template copy.
5. Delete or narrow dead fixed constants (`MONTH_COUNT` / `MONTHLY_MONTH_COUNT` as product lengths); keep only what layout math still needs.
6. Regenerate samples; grep the repo for `YYYY-MM`, “14 month”, “12 page”, `type="month"` and clean stragglers.
7. Changelog / release note: breaking CLI/API change — `--start` is now a year.

## 10. Breaking-change note (for RELEASES / commit message)

```text
breaking(cli): --start takes YYYY (lunar year of Ugadi), not YYYY-MM

One-page, monthly, ICS and web PDF spans are the amānta year from the
Gregorian month of Ugadi (adhika Chaitra when present) through the month
containing the end of Phālguna. Length is 12–14 civil months.
```

No compatibility shim for `YYYY-MM` unless a later request needs one; a clear
error is enough for a still-young CLI.

## 11. Out of scope

- Solar (sauramāna) year calendars (Mesha saṅkrānti → next).
- Vikram / Śaka year labels as the *input* (output headers already show them).
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
  fixed year each.
- Docs and web UI no longer tell users to pick a first Gregorian month.
