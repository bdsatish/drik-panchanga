"""Formatting and record-adaptation helpers for festival resolution."""

import calendar
from datetime import date as CivilDate
from datetime import timedelta


def format_festival_dates(dates):
    dates = sorted(dates)
    if not dates:
        return "None"
    if (
        len(dates) > 1
        and len({(value.year, value.month) for value in dates}) == 1
        and all(
            right == left + timedelta(days=1)
            for left, right in zip(dates, dates[1:])
        )
    ):
        return (
            f"{calendar.month_abbr[dates[0].month]} "
            f"{dates[0].day:02d}-{dates[-1].day:02d}"
        )
    return ",".join(
        f"{calendar.month_abbr[value.month]} {value.day:02d}"
        for value in dates
    )


def group_consecutive_candidates(candidates):
    groups = []
    for candidate in sorted(candidates):
        if groups and candidate[0] == groups[-1][-1][0] + timedelta(days=1):
            groups[-1].append(candidate)
        else:
            groups.append([candidate])
    return groups


def records_for_rule(records, rule):
    return [
        record
        for record in records
        if record[2] == str(rule.masa) and not record[3]
    ]


def collect_records(months, month_data):
    records = []
    for year, month in months:
        for (
            day,
            tithi,
            _,
            masa,
            is_adhika,
            tithi_hours_after_sunrise,
            sunrise_jd,
            sunset_jd,
            _yoga,
            _moonrise_jd,
        ) in month_data[(year, month)]:
            records.append(
                (
                    CivilDate(year, month, day),
                    tithi,
                    masa,
                    is_adhika,
                    tithi_hours_after_sunrise,
                    sunrise_jd,
                    sunset_jd,
                )
            )
    return records


def collect_moonrise_jds(months, month_data):
    """Map civil dates to the first local moonrise, expressed as UTC JD."""
    return {
        CivilDate(year, month, values[0]): values[9]
        for year, month in months
        for values in month_data[(year, month)]
    }


def plain_tithi_number(tithi):
    """Convert a plain S1..S15 or K1..K15 code to 1..30."""
    if not isinstance(tithi, str) or len(tithi) < 2:
        return None
    paksha = tithi[0]
    if paksha not in {"S", "K"}:
        return None
    try:
        paksha_tithi = int(tithi[1:])
    except ValueError:
        return None
    if not 1 <= paksha_tithi <= 15:
        return None
    return paksha_tithi if paksha == "S" else paksha_tithi + 15


def generic_udaya_occurrences(
    records,
    target_tithi,
    *,
    plain_tithi_number,
    interval_finder,
):
    """Return sunrise-owned occurrences with their amanta-masa metadata."""
    records = sorted(records)
    occurrences = []
    sunrise_candidates = [
        (record[0], record[2], record[3])
        for record in records
        if plain_tithi_number(record[1]) == target_tithi
    ]
    for group in group_consecutive_candidates(sunrise_candidates):
        occurrences.append(group[0])

    sunrise_dates = {occurrence[0] for occurrence in occurrences}
    for record, following_record in zip(records, records[1:]):
        if following_record[0] != record[0] + timedelta(days=1):
            continue
        start_tithi = plain_tithi_number(record[1])
        end_tithi = plain_tithi_number(following_record[1])
        if start_tithi is None or end_tithi is None:
            continue
        skipped = [
            (start_tithi + offset - 1) % 30 + 1
            for offset in range(1, (end_tithi - start_tithi) % 30)
        ]
        if target_tithi not in skipped:
            continue
        if not interval_finder(record[5], following_record[5], target_tithi):
            continue
        masa_record = following_record if target_tithi <= 15 else record
        occurrence = (record[0], masa_record[2], masa_record[3])
        if occurrence[0] not in sunrise_dates:
            occurrences.append(occurrence)
    return sorted(set(occurrences))


def generic_udaya_sunset_sunrise_occurrences(
    records,
    target_tithi,
    *,
    plain_tithi_number,
    interval_finder,
    tithi_number_at,
):
    """Return occurrences where the tithi prevails at sunrise OR sunset.

    Groups consecutive qualifying dates and picks the *first* in each group
    when any member qualified by sunset (night-anchor preference), otherwise
    the *last* (vriddhi day-anchor rule).
    """
    records = sorted(records)
    date_info = {}
    sunset_dates = set()

    for record in records:
        sunrise_match = plain_tithi_number(record[1]) == target_tithi
        sunset_match = tithi_number_at(record[6]) == target_tithi
        if sunrise_match or sunset_match:
            date_info.setdefault(record[0], (record[2], record[3]))
            if sunset_match:
                sunset_dates.add(record[0])

    # Handle kshaya (skipped) tithis that span between two consecutive records
    # without being present at either sunrise or sunset.
    for record, following_record in zip(records, records[1:]):
        if following_record[0] != record[0] + timedelta(days=1):
            continue
        start_tithi = plain_tithi_number(record[1])
        end_tithi = plain_tithi_number(following_record[1])
        if start_tithi is None or end_tithi is None:
            continue
        skipped = [
            (start_tithi + offset - 1) % 30 + 1
            for offset in range(1, (end_tithi - start_tithi) % 30)
        ]
        if target_tithi not in skipped:
            continue
        if not interval_finder(record[5], following_record[5], target_tithi):
            continue
        masa_record = following_record if target_tithi <= 15 else record
        date_info.setdefault(record[0], (masa_record[2], masa_record[3]))

    # Prune sunset-only dates that are month-boundary artifacts:
    # when a date qualifies only at sunset, and the same day's sunrise
    # tithi is in Krishna paksha while the target is in Shukla paksha
    # (or vice versa), the sunset capture may belong to a different masa.
    records_by_date = {r[0]: r for r in records}
    for d in list(date_info):
        if d not in sunset_dates:
            continue
        if plain_tithi_number(records_by_date[d][1]) == target_tithi:
            continue
        sunrise_tithi = plain_tithi_number(records_by_date[d][1])
        if sunrise_tithi is None:
            continue
        # If sunrise belongs to opposite paksha, the sunset capture
        # may be at a month boundary with stale masa metadata.
        same_paksha = (sunrise_tithi <= 15) == (target_tithi <= 15)
        if not same_paksha:
            del date_info[d]
            sunset_dates.discard(d)
            continue
        next_d = d + timedelta(days=1)
        if next_d not in records_by_date:
            continue
        next_rec = records_by_date[next_d]
        if plain_tithi_number(next_rec[1]) != target_tithi:
            continue
        if next_rec[2] != date_info[d][0]:
            del date_info[d]
            sunset_dates.discard(d)

    sorted_dates = sorted(date_info)
    groups = []
    for d in sorted_dates:
        masa = date_info[d][0]
        if groups:
            last_d = groups[-1][-1]
            last_masa = date_info[last_d][0]
            if d == last_d + timedelta(days=1) and masa == last_masa:
                groups[-1].append(d)
            else:
                groups.append([d])
        else:
            groups.append([d])

    occurrences = []
    for group in groups:
        has_sunset = any(d in sunset_dates for d in group)
        selected = group[0] if has_sunset else group[-1]
        masa, is_adhika = date_info[selected]
        occurrences.append((selected, masa, is_adhika))
    return sorted(occurrences)


def eligible_generic_occurrences(occurrences, rule, ugadi_number):
    """Filter generic occurrences by masa and the calendar's adhika policy."""
    occurrences = [
        occurrence
        for occurrence in occurrences
        if occurrence[1] in {str(rule.masa), f"A{rule.masa}"}
    ]
    if rule.number == ugadi_number and any(
        occurrence[2] for occurrence in occurrences
    ):
        return [
            occurrence for occurrence in occurrences if occurrence[2]
        ]
    return [
        occurrence for occurrence in occurrences if not occurrence[2]
    ]
