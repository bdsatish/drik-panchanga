# Plan: prune dead code after the lunar-year change

Status: proposal only — no code changes in this document.
Goal: delete the functions, branches and exception handlers that the
lunar-year PDFs (`-3300 … 3300`, one Ugadi-to-Phālguna span, a 32-day /
1-day record pad) and the polar sunrise fallback have made unreachable.

Reviewed against branch `lunar-year-calendars` @ `b8538043`. All line numbers
refer to that commit.

## 1. Method

1. **vulture** (min confidence 60) on product code and tests.
2. **ruff** (F401, F841, F541, B007). Style-only hits (RET504 and similar)
   follow house style and are ignored.
3. **Branch coverage** of the full suite (612 tests). Every "never runs" claim
   below is a line that this run did not execute.
4. **Line tracing** per test (`sys.settrace` over the full suite) for guards
   that coverage did hit, to see if only mocked or synthetic tests reach them.
5. **Reachability review**: read each guard against what its callee can
   return. `panchanga.sunrise()` / `sunset()` fall back to a meridian transit
   at polar day and night, so they never return the Swiss Ephemeris `0.0`
   failure value and never raise for supported dates. `moonrise()` /
   `moonset()` return `None` or a time in `[sunrise, next sunrise)`.
6. **Polar sweep** (measured): every day of the years −3300, −1500, 1, 1500,
   2026 and 3300 at 82.5° N (Alert), 78.2° N, 69–70° N, 77.9° S and 85° N,
   through the real `place_for_date` path, with fixed-offset custom
   locations and a zone name. It checks that sunrise advances each day and
   that sun and moon events stay in `[jd − 1, jd + 2]`. The sweep found one
   real edge case (§9), which keeps several guards alive (§8).
7. **Data checks**: `data/cities.json` (10,241 keys) has no keys that differ
   only by case. `sanskrit_names.json` has an ekādaśī name for every month
   (1–12 and `adhika`) and both pakṣas.

How to read the lists: **Delete** means the code never runs in production,
so removing it cannot change output. **Simplify** means the code runs but
cannot change the result. **Optional** means cheap guards that never run,
where keeping them is also defensible.

Out of scope by choice (§8): `vimsottari.py`, `vedic.py`, `gui.py`, every
unused function in `panchanga.py`, and the web deployment code.

## 2. Delete: exception handlers that never fire

No test forces an exception into any of these, and the wrapped calls do not
raise for supported dates. Unwrap the body; drop the `log.debug` line.

`generate_monthly_calendar.py`

- `sun_moon_lines` L271 / L289–290: the outer `try` / `except Exception`
  ("sun times unavailable").
- `sun_moon_lines` L282 / L286–287: the inner `try` around
  `panchanga.pratah_sandhya`.
- `sun_moon_lines` L291 / L298–299: the `try` around the moon events.
- `varjyam_lines` L309 / L312–313: the `try` around `panchanga.varjyam`.
- `rahu_kala_table_lines` L544 / L549–551: the `try` / `except … continue`
  around `panchanga.trikalam`. After this, see §3 for L555–557.

`festival_rules.py`

- `_event_jd_ut` L20–23: `try: event = getter(jd, place) except Exception:
  return None` becomes `event = getter(jd, place)`. Keep the `event is None`
  and band check on L24 (§8).
- `find_local_eclipses` L272–276: the `try` / `except … log.error … break`
  around `finder(search_jd, geopos)`. For PDF years the search stays well
  inside the range of the `.se1` files (13201 BCE – 17191 CE), and no test
  or build reaches the handler.
- `shraddha_tithi_at_aparahna` L796–799: the `try` / `except: return None`
  around `panchanga.day_duration`. Keep `if daylight_hours <= 0` (§8).

`panchanga.py`

- `_moon_event_in_window` L590–594: the `try` around the two `sunrise()`
  calls.
- `_moon_event_in_window` L601–604: the `try` around `finder(day_jd, place)`.
  Keep the band check on L606 (§8).
- `_moon_event_in_window` L611–614: the `try` around `_next_moon_event_jd`.

`webapp/day_panchanga.py`

- `probe_moon_event` L92–97: the `try` / `except Exception` around
  `swe.rise_trans`. If the ephemeris were broken, the earlier
  `panchanga.sunrise()` call in `_compute_day_details_unlocked` would fail
  first, and that call has no handler. Keep the `try` / `finally` at L175
  that resets the ayanāṃśa mode.

## 3. Delete: guards and branches that never run

`generate_panchanga_calendar.py`

- `lunar_year_boundaries` L330–331: `if not following: raise ValueError("No
  next Ugadi …")`. The 14-month window from Ugadi's month runs 13 full
  months past that month, which is at least 393 days after Ugadi, and a
  lunar year has at most 385. The comment at L324–327 already says so.
- `_count_word` L297–298 and its use at L321: the message is only built for
  `len(ugadis) > 1`, and one Gregorian year (≤ 366 days) cannot hold three
  Ugadis (each lunar year is ≥ 354 days). Write the literal "two".
- `ayanamsa_label` L485–486: the tropical `raise`. All three callers check
  for tropical first: `draw_page_header` L1078–1082, `build_pdf`
  L1249–1252, and `webapp/day_panchanga.py` L252. What remains is
  `AYANAMSA_OPTIONS[key]`.
- `build_pdf` L1176–1178, and `generate_monthly_calendar.py` L717–719 in
  the monthly builder: `if not LUNAR_YEAR_MIN_MONTHS <= len(months) <=
  LUNAR_YEAR_MAX_MONTHS: raise`. Every caller passes `lunar_year_months()`
  output, which is 12–14 months by construction. No test asserts the
  message. After this, `LUNAR_YEAR_MIN_MONTHS` (L30, imported by the monthly
  module at L53) is unused; delete it. `LUNAR_YEAR_MAX_MONTHS` stays, since
  the resolver windows use it.

`generate_monthly_calendar.py`

- `rahu_kala_table_lines` L555–557: `if weekday not in windows: "--"`. Once
  §2 removes the `continue`, every day adds a window. Every month has each
  weekday at least four times.
- `draw_cell` L468–472: `details if details else ([], [], [])` and the
  comment above it. `day_details` always returns a 3-tuple; the comment
  itself says "day_details always computes". Unpack it directly.

`festival_rules.py`

- `hindu_day_has_eclipse` L311–314: the "Sunrise unavailable" civil-day
  fallback, and the last docstring sentence (L304–305).
  `_event_jd_ut(…, sunrise)` returns `None` only if sunrise falls outside
  `[jd − 1, jd + 2]`. Sunrise always lies inside the local civil day, which
  is `[jd − 0.6, jd + 1.5]` for every allowed UTC offset (−12 … +14). The
  §9 edge case peaks at `jd + 1.19`. Afterwards, `utc_offset_hours` in this
  module is used only at L779, so keep the import.
- `classify_ekadashi_upavasa` L824–826: `.get()` plus `raise KeyError`
  becomes `record = records_by_date[upavasa_date]`. It raises the same
  error, and the only callers pass dates from `ekadashi_dates_from_records`.

`panchanga.py`

- `varjyam` has no deletion here (its guard is live, §8). Only its docstring
  L1181–1182 changes (§4).

## 4. Simplify: code that runs but has no effect

`generate_monthly_calendar.py`

- L101–126: two `if HexColor is not None` blocks. The first `else` (L110–113)
  already sets `PURPLE … _GREY_AAAAAA = None`, and the second `else`
  (L124–126) sets them again. Merge into one `if` / `else`.
- `sun_moon_lines` L277–285, after §2:
  - The sunrise band check on L277 cannot fail (see the `hindu_day_has_eclipse`
    reasoning in §3). So `rise_text = clock(rise)`.
  - `if rise_text != "--" or set_text != "--"` (L279) and `if rise_text !=
    "--"` (L281) are then always true. Remove both conditions.
  - The pratah-sandhya band check (L284) cannot fail: sandhya starts shortly
    before an in-band sunrise.
  - **Keep** the sunset band check on L278 (§8).
  - Rewrite the stale comment L272–274 (it cites the `0.0` sentinel) and the
    docstring L258–260, 265 ("one can exist while the other does not", "if
    sandhya cannot be computed"). Only the sunset can be out of band, and
    only in the §9 case.
- `collect_context` L667: `if civil in target_dates`. `dst_transitions(…,
  year, month, …)` only returns days of a printed month, so this is always
  true. Drop the `if`.

`generate_panchanga_calendar.py`

- `build_pdf` L1182–1183 and L1226–1237: `range_start <= value <=
  range_end` gives the same result as `value in target_dates` (the months
  are contiguous and `target_dates` holds every printed day). Filter the
  three sets with `in target_dates`, then delete `range_start` and
  `range_end`.

`festival_rules.py`

- `_event_jd_ut` docstring L17 ("missing / sentinel") and `_sunset_jd_ut`
  docstring L30 ("None if the sun does not set (polar day/night)"). Polar
  day and night never give `None`. `None` means the sunset fell past
  `jd + 2` (§9).

`panchanga.py`

- `varjyam` docstring L1181–1182 ("sentinel-garbage protection"). The guard
  now catches a next sunrise past `jd + 2` (§9), not a sentinel.

`webapp/ics_service.py`

- `_utf8_cut` L24–32: the decode-and-retry loop and its final `raise
  ValueError`. That raise never runs: the input is always valid UTF-8,
  because it comes from `str.encode("utf-8")`. Step back over continuation
  bytes (`0b10xxxxxx`) instead; then no exception path is left.

## 5. Delete: dead functions, names and imports

- `generate_panchanga_calendar.py` L724: unused local `right` (ruff F841).
- `generate_monthly_calendar.py` L67: `load_location` is not used in the
  module (ruff F401), but `tests/test_monthly_calendar.py` L23 imports it
  from here. Change that test import to `generate_panchanga_calendar`.
- `generate_panchanga_calendar.py` L30 `LUNAR_YEAR_MIN_MONTHS`, and
  `_count_word` L297–298: see §3.
- `webapp/day_panchanga.py` L125–131: `compute_day_details`, a locked
  wrapper that only `tests/test_day_panchanga.py` L42–44 calls. Both
  production callers (`compute_day_panchanga` L245, `ics_service` L101)
  hold the lock themselves and call `_compute_day_details_unlocked`. In the
  test, call the unlocked function inside `with
  panchanga.coordinate_calculation_lock:`.

## 6. Tests to delete or update

Tied to deletions above:

- `tests/test_monthly_calendar.py` L208–214
  `test_sun_moon_lines_render_sunset_only` and L216–220
  `test_sun_moon_lines_omit_sun_when_both_are_missing`. Both mock
  `panchanga.sunrise` to return `0.0`, which cannot happen (§4). Replace
  them with one real test of the live sunset path: custom location
  `82.5, -62.3, -5`, 3 Sep 1500. It prints `Sun: (21:49 –) 23:22 – --`.
- `tests/test_monthly_calendar.py` L23: the import (§5).
- `tests/test_day_panchanga.py` L42–44: the call (§5).
- `tests/test_polar_fallback.py` L202–211
  `test_day_details_none_renders_empty_cell`. Its name and comment describe
  the `None` path removed in §3, but it asserts `IsNotNone`. Rename it (for
  example `test_day_details_always_returns_a_tuple`), or delete it: the
  polar test at `test_monthly_calendar.py` L148 already covers this.

Unused names (vulture):

- `tests/test_festival_rules.py` L124: helper `covering_month_data`, never
  called.
- `tests/test_pdf_layout.py` L368: `plain_text` is unused; use `_`.
- `tests/test_polar_fallback.py` L193–194: class `_R` inside
  `overshooting_search`, never used.
- Not an issue: vulture's "unused `g`" at `test_festival_rules.py`
  L1583–1732 is a required parameter of `lambda d, g, t:` mock callbacks.

## 7. Optional: cheap guards that never run

These never run in production. Deleting them is safe; keeping them costs
one or two lines each.

- `festival_rules.py` L473–474 (`_sunset_tithi_skipped`) and L534–535
  (`_moonrise_tithi_skipped`): `if following.civil_date != record.civil_date
  + 1: continue`. No test reaches them either: records come from
  `daily_records_between`, which is contiguous. The same guard in
  `select_kshaya_dates` L191–192 must stay (§8). Delete all three together
  or keep all three; don't leave the helpers inconsistent.
- `festival_rules.py` L264–265: `if end_jd <= start_jd: return []` in
  `find_local_eclipses`. Every caller passes `end > start`.
- `panchanga.py` L595–596: `if window_end <= window_start: window_end =
  window_start + 1.0` in `_moon_event_in_window`. Only the two mocked tests
  in §6 reach it. The smallest real gap between consecutive sunrises is
  0.017 days (§9), never ≤ 0.
- Data-guarded: with the shipped data files, these branches never run.
  - `generate_panchanga_calendar.py` L554–555: `resolve_city_key` "matches
    multiple keys".
  - `generate_monthly_calendar.py` L190 (`if base else None`) and L195–196:
    the `None` returns of `ekadashi_name`.
  - `generate_monthly_calendar.py` L482: `if ek_name:` in `draw_cell`.

  Remove them only if the data files are treated as fixed. A test that
  checks both data properties would then guard future edits.

## 8. Checked and kept

Kept by choice, although the scan found them unused. Leave them as they are,
lint findings included:

- `vimsottari.py`, `vedic.py` and `gui.py`. They are not packaged, and no
  product code imports them. `vimsottari.py` has B007 hits at L100, L113
  and L129; `vedic.py` has unused helpers and an unused `equal` at L147;
  `gui.py` has unused locals at L218–219, L284 and L374–379.
- Every unused function in `panchanga.py`:
  - `function(point)` L313, a scratch ayanāṃśa objective with no caller.
  - Functions used only by tests: `set_nakshatra_system` L111 (with the
    Garga system: `nakshatra_system` L41, `garga_end_points` L170,
    `nakshatra_pada_unequal_system` L405), `lon_relative_to_base` L232,
    `bisection_search` L329 (F541 at L350), `full_moon` L899,
    `samvatsara_north` L965, `drik_ritu_at` L1034, `night_duration` L1054,
    `yamaganda_kalam` / `gulika_kalam` L1102–1103, `abhijit_muhurta`
    L1144, `ascendant` L1302, `navamsa` L1337,
    `sidereal_saptarshi_nakshatra` L1353, `saptarshi_nakshatra_traditional`
    L1382.
  - Functions used only by the kept modules or tests: `get_planet_name`
    L179, `from_dms` L196, `init_swisseph` L272.
  - `ephemeris_fingerprint` L275: `tests/__init__.py` prints it as the run
    banner.
- The web deployment code:
  - `webapp/cgi_handlers.py` `write_headers` L75–76. It has no caller in
    the repo; the freesshell.de `public_html` wrapper scripts live outside
    it.
  - The `sys.path` inserts in `webapp/app.py` L22–26 and
    `webapp/cgi_handlers.py` L13–15. They repeat `webapp/__init__.py`
    L15–18 for `python -m webapp.app` and gunicorn, but `python
    webapp/app.py` and the external CGI wrappers may rely on them.
    `PROJECT_ROOT` L28 uses `_REPO_ROOT` in `handle_status`.

Live only in the §9 case (custom locations at very high latitude). Delete
these only after §9 is fixed, and re-run the sweep first:

- The sunset band check in `sun_moon_lines`, `generate_monthly_calendar.py`
  L278. The cell prints `--`.
- The band check in `_event_jd_ut`, `festival_rules.py` L24, for sunset.
- The `sunset_jd is None` skips in `_sunset_tithi_skipped` L477–478 and
  `select_pradosham_dates` L510–511. Only mocked tests cover them, but they
  are live in the §9 case. The tests at `test_festival_rules.py`
  L1672–1732 stay.
- The `varjyam` sunrise guard, `panchanga.py` L1193–1194. On the day before
  the edge day the next sunrise lands at `jd + 2.18`, and `varjyam` returns
  `[]`. `tests/test_polar_fallback.py` L176–182 stays.
- The moon band checks: `generate_monthly_calendar.py` L294 and
  `_event_jd_ut` for moonrise. On the same day before the edge day, the
  window end reaches `jd + 2.18`.

Live in normal use:

- `_moon_event_in_window` L606 band check: raw `moonrise_jd` /
  `moonset_jd` can return the failure value at high latitude.
- `_moonrise_tithi_skipped` L538–539 (`moonrise_jd is None`): real days
  with no moonrise; 26 tests reach it, including PDF builds.
- `select_kshaya_dates` L191–192 (gap guard): 14 tests build sparse record
  lists, and `test_ignores_non_consecutive_civil_days` asserts the guard.
- `shraddha_tithi_at_aparahna` `daylight_hours <= 0`, and `draw_cell` L461
  shraddha `None`: polar night.
- `panchanga._transit_jd` re-search L495–498: rare but reachable.
- `datetime_helper.py` L108–111 OverflowError guard: the day view still
  goes to year 9999.
- reportlab optional import fallbacks (`generate_panchanga_calendar.py`
  L18–19 and L105–109, `_check_reportlab`) and the `None` colour constants.
- Web and CGI input validation (`require_month_system`,
  `require_coordinate_selection`, …), city suggestions, and the CGI
  catch-alls ("so CGI still returns a response").
- Flask routes and CGI `handle_*` functions (vulture false positives: they
  are registered by decorator or called by external wrappers).
- `fitted_font_size` L879, the badge `break` L1008, the too-many-festivals
  check L1206, the `recurring` branch, `festivals_path is None`, the
  `_wrap_lines` branches, and the `__main__` blocks.
- `festival_rules.py` L73 `optionxform` (vulture false positive).

## 9. Side finding: sunrise on the first night after midnight sun

Not a pruning item, but it decides §8. With a custom location at 82.50° N,
62.30° W, UTC−5 (measured):

| Civil date | Sunrise − jd | Sunset − jd | Gap to next sunrise |
|---|---|---|---|
| 2 Sep 1500 | 0.208 (00:00) | 1.208 | 1.974 days |
| 3 Sep 1500 | 1.182 (23:22) | 2.122 | 0.026 days |

- The sun first dips below the horizon late on 3 Sep. So that day's sunrise
  is 23:22, and the next day's sunrise is logged at exactly 00:00 local.
- The Hindu day of 2 Sep lasts almost two days, and that of 3 Sep about
  37 minutes.
- The same pattern appears in −1500 (3 Sep) and 3300 (1 Sep). It did not
  appear at 78.2° N, 69–70° N, 77.9° S or 85° N (longitude 0, UTC+0) in
  the sampled years, so it depends on latitude, longitude and offset
  together. No listed
  city is above 69.4° N, so only custom coordinates reach it.
- Decide separately whether the 00:00 anchor on the following day is the
  intended fallback.

## 10. Order of work and checks

1. §5 and the §6 unused names: no behaviour change.
2. §2: unwrap the exception handlers.
3. §3 and §4, with the §6 test updates, in one commit per module.
4. §7 items, if accepted.

After each step:

- `python -m unittest discover -s tests -t . -p 'test_*.py'` (same as CI).
- `ruff check` and vulture on the touched files: no new findings. The
  modules and functions kept by choice (§8) will still show up; ignore them.
- Branch coverage again: no new missed lines in the touched functions.
- PDF smoke builds, before and after, compared with `pdftotext`:
  - one-page and monthly, `--start 2026`, Ujjain, Citra-paksha;
  - monthly, `--start 1500`, custom `82.5, -62.3, -5`. The 3 Sep cell must
    still show `Sun: (21:49 –) 23:22 – --`.
- The text must be identical. The polar case checks that the §8 guards still
  work.
