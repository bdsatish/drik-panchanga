"""Pure engines for generic festival-date policies."""

from dataclasses import replace
from datetime import timedelta

from .config import (
    APARAHNA_KALA,
    ARUNODAYA_HOURS,
    ARUNODAYA_KALA,
    DAY_MIDPOINT_ANCHOR,
    GADHARATRI_KALA,
    GENERIC_ANCHOR_BY_FESTIVAL,
    GENERIC_KALA_BY_FESTIVAL,
    GENERIC_VALIDITY_BY_FESTIVAL,
    MADHYAHNA_KALA,
    MADHYARATRI_KALA,
    NIGHT_KALAS,
    NIGHT_MIDPOINT_ANCHOR,
    PREDAWN_ANCHOR,
    PRADOSHA_KALA,
    PRATAH_KALA,
    PURVAHNA_KALA,
    PURVARATRI_KALA,
    SANGAVA_KALA,
    SAYAHNA_KALA,
    SUNRISE_ANCHOR,
    SUNRISE_KALA,
    SUNSET_ANCHOR,
    SUNSET_KALA,
)


def select_udaya_festival_dates(
    records,
    rule,
    *,
    plain_tithi_number,
    occurrence_finder,
    eligibility_filter,
):
    """Apply sunrise ownership using dependencies supplied by the facade."""
    target_tithi = plain_tithi_number(rule.tithi)
    if target_tithi is None:
        raise ValueError(f"{rule.name} does not have a plain tithi rule")
    occurrences = eligibility_filter(
        occurrence_finder(records, target_tithi),
        rule,
    )
    return [occurrence[0] for occurrence in occurrences]


def select_midpoint_festival_dates(
    records,
    rule,
    *,
    plain_tithi_number,
    occurrence_finder,
    eligibility_filter,
    interval_finder,
):
    """Assign each eligible tithi to the sunrise-day containing its midpoint."""
    target_tithi = plain_tithi_number(rule.tithi)
    if target_tithi is None:
        raise ValueError(f"{rule.name} does not have a plain tithi rule")

    records = sorted(records)
    records_by_date = {record[0]: record for record in records}
    occurrences = eligibility_filter(
        occurrence_finder(records, target_tithi),
        rule,
    )
    selected = []
    for owner_date, _, _ in occurrences:
        owner_record = records_by_date.get(owner_date)
        if owner_record is None:
            continue
        intervals = interval_finder(
            owner_record[5] - 1.25,
            owner_record[5] + 2.25,
            target_tithi,
        )
        if not intervals:
            continue
        reference = owner_record[5] + 0.5
        target_interval = min(
            intervals,
            key=lambda interval: abs(
                (interval[0] + interval[1]) / 2 - reference
            ),
        )
        tithi_midpoint = sum(target_interval) / 2
        for offset in (-1, 0, 1):
            civil_date = owner_date + timedelta(days=offset)
            record = records_by_date.get(civil_date)
            following_record = records_by_date.get(
                civil_date + timedelta(days=1)
            )
            if record is None or following_record is None:
                continue
            if record[5] <= tithi_midpoint < following_record[5]:
                selected.append(civil_date)
                break
    return sorted(set(selected))


def kala_for_rule(rule):
    """Return the ritual period assigned by the generic-kala experiment."""
    return GENERIC_KALA_BY_FESTIVAL.get(rule.number, SUNRISE_KALA)


def kala_window(record, following_record, kala, preceding_record=None):
    """Return a named slot from the proportional day/night grids."""
    sunrise_jd, sunset_jd = record[5:7]
    if kala == SUNRISE_KALA:
        return sunrise_jd, sunrise_jd
    if kala == SUNSET_KALA:
        return sunset_jd, sunset_jd

    day_boundaries = [
        sunrise_jd + (sunset_jd - sunrise_jd) * part / 5
        for part in range(6)
    ]
    if kala == PURVAHNA_KALA:
        return day_boundaries[0], day_boundaries[2]
    day_index = {
        PRATAH_KALA: 0,
        SANGAVA_KALA: 1,
        MADHYAHNA_KALA: 2,
        APARAHNA_KALA: 3,
        SAYAHNA_KALA: 4,
    }.get(kala)
    if day_index is not None:
        return day_boundaries[day_index], day_boundaries[day_index + 1]

    if kala == ARUNODAYA_KALA:
        if preceding_record is None:
            raise ValueError("arunodaya requires the preceding sunset")
        preceding_sunset_jd = preceding_record[6]
        night_fifth = (sunrise_jd - preceding_sunset_jd) / 5
        return sunrise_jd - night_fifth, sunrise_jd

    if kala in NIGHT_KALAS:
        if following_record is None:
            raise ValueError(f"{kala} requires the following sunrise")
        following_sunrise_jd = following_record[5]
        boundaries = [
            sunset_jd + (following_sunrise_jd - sunset_jd) * part / 5
            for part in range(6)
        ]
        index = {
            PRADOSHA_KALA: 0,
            PURVARATRI_KALA: 1,
            MADHYARATRI_KALA: 2,
            GADHARATRI_KALA: 3,
        }[kala]
        return boundaries[index], boundaries[index + 1]
    raise ValueError(f"Unknown generic kala: {kala}")


def kala_score(kala_window, target_interval, civil_date):
    """Score one date by kala coverage, then centrality, then earlier date."""
    kala_start, kala_end = kala_window
    tithi_start, tithi_end = target_interval
    kala_midpoint = (kala_start + kala_end) / 2
    tithi_midpoint = (tithi_start + tithi_end) / 2
    if kala_start == kala_end:
        coverage = float(tithi_start <= kala_start < tithi_end)
    else:
        overlap = max(
            0.0,
            min(kala_end, tithi_end) - max(kala_start, tithi_start),
        )
        coverage = overlap / (kala_end - kala_start)
    return coverage, -abs(kala_midpoint - tithi_midpoint), -civil_date.toordinal()


def select_kala_festival_dates(
    records,
    rule,
    *,
    plain_tithi_number,
    occurrence_finder,
    eligibility_filter,
    interval_finder,
    kala_for_rule,
    kala_window,
    kala_score,
):
    """Resolve a plain tithi using one kala mapping and common tie-break."""
    target_tithi = plain_tithi_number(rule.tithi)
    if target_tithi is None:
        raise ValueError(f"{rule.name} does not have a plain tithi rule")

    records = sorted(records)
    records_by_date = {record[0]: record for record in records}
    occurrences = eligibility_filter(
        occurrence_finder(records, target_tithi),
        rule,
    )
    kala = kala_for_rule(rule)
    if kala == SUNRISE_KALA:
        return [occurrence[0] for occurrence in occurrences]

    selected = []
    for owner_date, _, _ in occurrences:
        owner_record = records_by_date.get(owner_date)
        if owner_record is None:
            continue
        intervals = interval_finder(
            owner_record[5] - 1.25,
            owner_record[5] + 2.25,
            target_tithi,
        )
        if not intervals:
            continue
        reference = owner_record[5] + 0.5
        target_interval = min(
            intervals,
            key=lambda interval: abs(
                (interval[0] + interval[1]) / 2 - reference
            ),
        )
        candidates = []
        for offset in (-1, 0, 1):
            civil_date = owner_date + timedelta(days=offset)
            record = records_by_date.get(civil_date)
            following_record = records_by_date.get(
                civil_date + timedelta(days=1)
            )
            preceding_record = records_by_date.get(
                civil_date - timedelta(days=1)
            )
            if record is None:
                continue
            if kala in NIGHT_KALAS and following_record is None:
                continue
            if kala == ARUNODAYA_KALA and preceding_record is None:
                continue
            window = kala_window(
                record,
                following_record,
                kala,
                preceding_record,
            )
            candidates.append(
                (
                    kala_score(window, target_interval, civil_date),
                    civil_date,
                )
            )
        if candidates:
            selected.append(max(candidates)[1])
    return sorted(set(selected))


def anchor_for_rule(rule):
    """Return the instant assigned by the generic-anchor experiment."""
    return GENERIC_ANCHOR_BY_FESTIVAL.get(rule.number, SUNRISE_ANCHOR)


def anchor_jd(record, following_record, anchor):
    """Return one exact local anchor as a Julian day."""
    sunrise_jd, sunset_jd = record[5:7]
    if anchor == SUNRISE_ANCHOR:
        return sunrise_jd
    if anchor == DAY_MIDPOINT_ANCHOR:
        return (sunrise_jd + sunset_jd) / 2
    if anchor == SUNSET_ANCHOR:
        return sunset_jd
    if anchor == NIGHT_MIDPOINT_ANCHOR:
        if following_record is None:
            raise ValueError("night midpoint requires the following sunrise")
        return (sunset_jd + following_record[5]) / 2
    if anchor == PREDAWN_ANCHOR:
        return sunrise_jd - ARUNODAYA_HOURS / 24
    raise ValueError(f"Unknown generic anchor: {anchor}")


def select_anchor_festival_dates(
    records,
    rule,
    *,
    plain_tithi_number,
    occurrence_finder,
    eligibility_filter,
    interval_finder,
    anchor_for_rule,
    anchor_jd,
):
    """Resolve a plain tithi using one exact anchor and common fallback."""
    target_tithi = plain_tithi_number(rule.tithi)
    if target_tithi is None:
        raise ValueError(f"{rule.name} does not have a plain tithi rule")

    records = sorted(records)
    records_by_date = {record[0]: record for record in records}
    occurrences = eligibility_filter(
        occurrence_finder(records, target_tithi),
        rule,
    )
    anchor = anchor_for_rule(rule)
    selected = []
    for owner_date, _, _ in occurrences:
        owner_record = records_by_date.get(owner_date)
        if owner_record is None:
            continue
        intervals = interval_finder(
            owner_record[5] - 1.25,
            owner_record[5] + 2.25,
            target_tithi,
        )
        if not intervals:
            continue
        reference = owner_record[5] + 0.5
        target_interval = min(
            intervals,
            key=lambda interval: abs(
                (interval[0] + interval[1]) / 2 - reference
            ),
        )
        tithi_midpoint = sum(target_interval) / 2
        candidates = []
        for offset in (-1, 0, 1):
            civil_date = owner_date + timedelta(days=offset)
            record = records_by_date.get(civil_date)
            if record is None:
                continue
            following_record = records_by_date.get(
                civil_date + timedelta(days=1)
            )
            if anchor == NIGHT_MIDPOINT_ANCHOR and following_record is None:
                continue
            point = anchor_jd(record, following_record, anchor)
            contains_anchor = target_interval[0] <= point < target_interval[1]
            score = (
                int(contains_anchor),
                -abs(point - tithi_midpoint),
                -civil_date.toordinal(),
            )
            candidates.append((score, civil_date))
        if candidates:
            selected.append(max(candidates)[1])
    return sorted(set(selected))


def date_is_valid(
    records_by_date,
    selected_date,
    overlay,
    geopos,
    *,
    contamination_validator,
    contamination_checker,
):
    """Apply one shared post-selection constraint."""
    if overlay.validator == contamination_validator:
        if geopos is None:
            raise ValueError(
                "Upakarma validity requires a geographic position"
            )
        return not contamination_checker(
            records_by_date,
            selected_date,
            geopos,
        )
    raise ValueError(f"Unknown generic policy validator: {overlay.validator}")


def select_valid_festival_dates(
    records,
    rule,
    geopos,
    *,
    selector,
    validator,
):
    """Resolve, then reject defects and retry with the same policy."""
    selected_dates = selector(records, rule)
    overlay = GENERIC_VALIDITY_BY_FESTIVAL.get(rule.number)
    if overlay is None:
        return selected_dates

    records_by_date = {record[0]: record for record in records}
    fallback_dates = []
    if overlay.fallback_masa_offset is not None:
        fallback_rule = replace(
            rule,
            masa=rule.masa + overlay.fallback_masa_offset,
        )
        fallback_dates = selector(records, fallback_rule)

    validated = []
    for selected_date in selected_dates:
        if validator(
            records_by_date,
            selected_date,
            overlay,
            geopos,
        ):
            validated.append(selected_date)
            continue
        fallback_date = next(
            (
                candidate
                for candidate in fallback_dates
                if selected_date < candidate <= selected_date + timedelta(days=45)
            ),
            None,
        )
        if (
            fallback_date is not None
            and validator(
                records_by_date,
                fallback_date,
                overlay,
                geopos,
            )
        ):
            validated.append(fallback_date)
    return validated


select_valid_kala_festival_dates = select_valid_festival_dates
