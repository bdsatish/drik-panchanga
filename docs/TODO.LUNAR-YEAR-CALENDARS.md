# TODO: lunar-year PDF calendars

Plan: [PLAN.LUNAR-YEAR-CALENDARS.md](PLAN.LUNAR-YEAR-CALENDARS.md)

## 1. Core helpers (`generate_panchanga_calendar.py`)

- [x] `require_start_year(text) -> int` — `-\d{1,4}` or `\d{4}`; range `-3300 ... 3300`; clear reject of `YYYY-MM`
- [x] `lunar_year_months(start_year, location, coordinate_selection) -> [(y, m), ...]`
  - [x] window 1 Nov `Y-1` … 31 Dec `Y`; exactly one Ugadi rule (§2.1, §4.2)
  - [x] next-Ugadi window, last day = `next_ugadi - 1`, month list via `_month_sequence`
  - [x] error names the Ugadi dates found (zero or two)
  - [x] takes `coordinate_calculation_lock`, sets coordinate selection
- [x] `daily_records_between(first, last, location)`; `daily_records(months, ...)` wraps it
- [x] delete `require_supported_span`, `CONTEXT_MARGIN_MONTHS`, `context_month_sequence`, `context_month_range`

## 2. Day pad in builders (§4.5)

- [x] one-page: records `first - 32` … `last + 1`; `target_dates` = printed days
- [x] monthly: `collect_context` reads the same pad

## 3. One-page CLI + builder

- [x] `build_pdf(location, months, output_path, ...)`
- [x] `default_output_path(location, months, ...)`; names per §3.4
- [x] `--start YYYY` help text; `main()` resolves once, then path + build

## 4. Monthly CLI + builder

- [x] `build_monthly_pdf(location, months, output_path, ...)`; pages = `len(months)`
- [x] title / footer total / module docstring
- [x] `--start YYYY`, `default_monthly_output_path(location, months, ...)`

## 5. ICS + web

- [x] `webapp/ics_service.py`: year in, resolve under lock, BCE 400 stays, docstring
- [x] `webapp/pdf_service.py`: parse year, resolve, then filename
- [x] `webapp/app.py`: ICS `start=YYYY`
- [x] `webapp/cgi_handlers.py`: 405 message
- [x] `webapp/templates/index.html`: year input (`pattern`), labels, hints, JS default, CSS selector

## 6. Tests

- [x] parser cases (§8.1)
- [x] resolver fixtures 2026/2027/2028/2029/2030 (§8.2), length invariant, purnimanta no-op
- [x] builders: columns/pages == `len(months)`, filenames
- [x] range edges `-3300` / `3300`; zero-or-two-Ugadi errors (§8.8–9)
- [x] festival outside lunar year (`Ugadi: Mar 20,Apr 07`) (§8.10)
- [x] day pad cases: solar day 17 on 2026-03-01; 1905 parana (§8.11)
- [x] rewrite fixtures that used `month_range` / `context_month_range` (`test_pdf_layout`, `test_festival_rules`, `test_monthly_calendar`)
- [x] `test_custom_location.py`: `BceStartMonthTests` → year tests; `-5000-12` out of range
- [x] `test_bce_ce_boundary.py`, `test_day_panchanga.py` (`start=9999-12` → 400 from range), `test_pdf_service.py`
- [x] `test_deep_bce.py`: `DEEPEST = Date(-3301, 11, 1)`

## 7. CI / scripts

- [x] `.github/workflows/ci.yml` `--start 2026` ×2 + expected filenames
- [x] `scripts/ci_smoke_http.sh` `start=2026` / `start=2023`
- [x] `scripts/setup_venv.sh`

## 8. Docs + samples

- [x] `README.md`, `docs/README.CALENDARS.md`, `docs/README.pypi.md`
- [x] `panchanga.py` cache comment (§3.5)
- [x] regenerate `samples/*.png`, rename mar2026→apr2027 link

## 9. Final sweep

- [x] grep for `YYYY-MM`, `--start 20`, `start=20`, “14 month”, “fourteen”, “12-month”, “twelve”, “12 page”, “First month”, `type="month"` (outside `experimental/`)
- [x] full `python -m unittest discover`
- [x] breaking-change commit message (§10)

## Done (deviations noted)

- All items above are complete; 610 tests pass (`python -m unittest discover -s tests -t .`).
- `require_start_year` also rejects `-3301/3301` *before* any records are
  computed, as the plan asks.
- Extra lock added while implementing: `tests/test_lunar_year_calendar.py`
  covers parser grammar, the five measured fixtures, -3300/3300 edges for
  every mode, the Revati two-Ugadi / no-Ugadi errors, the 32/1-day pad
  (solar day 17 at 2026-03-01; 1905 pāraṇā), shared month across consecutive
  years, and the adhika-Chaitra 2029 start.
- `lunar_year_boundaries()` is public: callers needing the exact Ugadi and
  last Phālguna day (tests, future footers) get them without re-scan logic.
- Samples regenerated at 150 dpi from `--start 2026`:
  `ujjain_panchanga_mar2026_apr2027.png` (replaces `..._mar2026_mar2027.png`)
  and `ujjain_monthly_march2026.png`.
- `attach_option_values` docstring updated to `--start -0500`.
