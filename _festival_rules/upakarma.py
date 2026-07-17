"""Rig and Yajur Upakarma resolution engines."""

from datetime import timedelta


def date_is_contaminated(
    records_by_date,
    selected_date,
    geopos,
    *,
    contamination_checker,
):
    selected_record = records_by_date[selected_date]
    previous_record = records_by_date.get(selected_date - timedelta(days=1))
    next_record = records_by_date.get(selected_date + timedelta(days=1))
    if previous_record is None or next_record is None:
        return False
    previous_midnight = (previous_record[6] + selected_record[5]) / 2
    following_midnight = (selected_record[6] + next_record[5]) / 2
    return contamination_checker(
        previous_midnight,
        following_midnight,
        geopos,
    )


def select_rigveda_dates(
    records,
    rule,
    geopos,
    *,
    one_ghati_hours,
    nakshatra_at,
    nakshatra_overlap,
    group_candidates,
    is_contaminated,
):
    records_by_date = {record[0]: record for record in records}
    three_muhurtas = 6 * one_ghati_hours
    two_muhurtas = 4 * one_ghati_hours

    def month_records(masa):
        return [
            record
            for record in records
            if (
                record[2] == str(masa)
                and not record[3]
                and record[1].startswith("S")
            )
        ]

    def shravana_candidates(candidate_records):
        candidates = []
        for record in candidate_records:
            sunrise_jd = record[5]
            if nakshatra_at(sunrise_jd + 1e-10) != 22:
                continue
            candidates.append(
                (
                    record[0],
                    nakshatra_overlap(
                        sunrise_jd,
                        sunrise_jd + three_muhurtas / 24,
                        22,
                    ),
                )
            )
        selected = []
        for group in group_candidates(candidates):
            if len(group) > 1:
                selected.append(
                    group[-1][0]
                    if group[-1][1] + 1e-9 >= three_muhurtas
                    else group[0][0]
                )
            elif group[0][1] + 1e-9 >= two_muhurtas:
                selected.append(group[0][0])
        return selected

    def sunrise_fallback_dates(candidate_records, kind):
        candidates = []
        for record in candidate_records:
            civil_date, tithi, _, _, tithi_remainder, sunrise_jd, _ = record
            if kind == "panchami":
                if tithi != "S5":
                    continue
                remainder = tithi_remainder
            else:
                if nakshatra_at(sunrise_jd + 1e-10) != 13:
                    continue
                remainder = nakshatra_overlap(
                    sunrise_jd,
                    sunrise_jd + three_muhurtas / 24,
                    13,
                )
            candidates.append(
                civil_date
                if remainder + 1e-9 >= three_muhurtas
                else civil_date - timedelta(days=1)
            )
        return sorted(set(candidates))

    shravana_month = month_records(rule.masa)
    for selected_date in shravana_candidates(shravana_month):
        if not is_contaminated(records_by_date, selected_date, geopos):
            return [selected_date]

    for masa in (rule.masa, rule.masa + 1):
        candidates = month_records(masa)
        if masa != rule.masa:
            for selected_date in shravana_candidates(candidates):
                if not is_contaminated(records_by_date, selected_date, geopos):
                    return [selected_date]
        panchami_dates = sunrise_fallback_dates(candidates, "panchami")
        hasta_dates = sunrise_fallback_dates(candidates, "hasta")
        common_dates = sorted(set(panchami_dates) & set(hasta_dates))
        ordered_dates = common_dates + [
            value
            for value in panchami_dates + hasta_dates
            if value not in common_dates
        ]
        for selected_date in ordered_dates:
            if (
                selected_date in records_by_date
                and not is_contaminated(
                    records_by_date,
                    selected_date,
                    geopos,
                )
            ):
                return [selected_date]
    return []


def select_taittiriya_purnima_dates(
    records,
    masa,
    *,
    one_ghati_hours,
    group_candidates,
    interval_finder,
):
    by_date = {record[0]: record for record in records}
    masa_records = sorted(
        record
        for record in records
        if record[2] == str(masa) and not record[3]
    )
    segments = []
    for record in masa_records:
        if (
            segments
            and record[0] == segments[-1][-1][0] + timedelta(days=1)
        ):
            segments[-1].append(record)
        else:
            segments.append([record])

    selected_dates = []
    for segment in segments:
        sunrise_candidates = [
            (record[0], record[4])
            for record in segment
            if record[1] == "S15"
        ]
        if sunrise_candidates:
            for group in group_candidates(sunrise_candidates):
                if len(group) > 1:
                    selected_dates.append(group[0][0])
                    continue
                later_date, remainder = group[0]
                previous_date = later_date - timedelta(days=1)
                previous_record = by_date.get(previous_date)
                later_record = by_date[later_date]
                selected_date = later_date
                if previous_record is not None:
                    intervals = interval_finder(
                        previous_record[5],
                        later_record[5],
                        15,
                    )
                    purnima_start = (
                        intervals[0][0] if intervals else later_record[5]
                    )
                    first_muhurta_end = (
                        previous_record[5]
                        + 2 * one_ghati_hours / 24
                    )
                    if (
                        purnima_start <= first_muhurta_end
                        or remainder < 4 * one_ghati_hours
                    ):
                        selected_date = previous_date
                selected_dates.append(selected_date)
            continue

        for record in segment:
            following_record = by_date.get(
                record[0] + timedelta(days=1)
            )
            if following_record is None:
                continue
            if interval_finder(record[5], following_record[5], 15):
                selected_dates.append(record[0])
                break
    return selected_dates


def select_taittiriya_apastamba_dates(
    records,
    rule,
    geopos,
    *,
    select_purnima,
    is_contaminated,
):
    by_date = {record[0]: record for record in records}
    selected_dates = select_purnima(records, rule.masa)
    fallback_dates = select_purnima(records, rule.masa + 1)
    selected = []
    for selected_date in selected_dates:
        if not is_contaminated(by_date, selected_date, geopos):
            selected.append(selected_date)
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
            and not is_contaminated(by_date, fallback_date, geopos)
        ):
            selected.append(fallback_date)
    return selected
