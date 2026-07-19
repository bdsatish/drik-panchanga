"""Dharma Sindhu Vaishnava, Generic Udaya, and Vaikuntha Ekadashi engines."""


def resolve_vaishnava_dates(
    months,
    month_data,
    *,
    collect_records,
    interval_finder,
    tithi_at,
    arunodaya_hours,
):
    records = collect_records(months, month_data)
    sunrises = [(record[0], record[5]) for record in records]
    if len(sunrises) < 3:
        return []

    scan_start = sunrises[0][1] - 1
    scan_end = sunrises[-1][1] + 1
    selected = []
    epsilon = 1 / (86400 * 10)
    for ekadashi_tithi in (11, 26):
        dashami_tithi = ekadashi_tithi - 1
        dvadashi_tithi = ekadashi_tithi + 1
        for ekadashi_start, _ in interval_finder(
            scan_start,
            scan_end,
            ekadashi_tithi,
        ):
            first_sunrise_index = next(
                (
                    index
                    for index, (_, sunrise_jd) in enumerate(sunrises)
                    if sunrise_jd >= ekadashi_start
                ),
                None,
            )
            if (
                first_sunrise_index is None
                or first_sunrise_index + 2 >= len(sunrises)
            ):
                continue
            first_date, first_sunrise = sunrises[first_sunrise_index]
            second_date, second_sunrise = sunrises[first_sunrise_index + 1]
            _, third_sunrise = sunrises[first_sunrise_index + 2]
            arunodaya = first_sunrise - arunodaya_hours / 24
            is_dashami_viddha = (
                tithi_at(arunodaya + epsilon) == dashami_tithi
            )
            ekadashi_has_adhikya = (
                tithi_at(second_sunrise + epsilon) == ekadashi_tithi
            )
            dvadashi_has_adhikya = (
                tithi_at(third_sunrise + epsilon) == dvadashi_tithi
            )
            selected.append(
                second_date
                if (
                    is_dashami_viddha
                    or ekadashi_has_adhikya
                    or dvadashi_has_adhikya
                )
                else first_date
            )
    return sorted(set(selected))


def resolve_generic_udaya_dates(
    months,
    month_data,
    *,
    collect_records,
    occurrence_finder,
):
    """Resolve Ekadashi dates using the generic-udaya vriddhi/kshaya rules.

    - Normal (Ekadashi at one sunrise): that civil date.
    - Vriddhi (at two consecutive sunrises): the earlier date.
    - Kshaya (misses sunrise entirely): the next civil date (Dvadashi).
    """
    records = collect_records(months, month_data)
    selected = set()
    for tithi in (11, 26):
        for owner_date, _, _ in occurrence_finder(records, tithi):
            selected.add(owner_date)
    return sorted(selected)


def select_vaikuntha_dates(
    months,
    month_data,
    records,
    *,
    collect_records,
    resolve_upavasa,
    raasi_at,
):
    if records is None:
        records = collect_records(months, month_data)
    records_by_date = {record[0]: record for record in records}
    upavasa_dates = resolve_upavasa(months, month_data)
    selected = []
    for upavasa_date in upavasa_dates:
        record = records_by_date.get(upavasa_date)
        if record is None:
            continue
        _, tithi, masa, _, _, sunrise_jd, _ = record
        if (
            masa in {"9", "10"}
            and tithi.startswith("S")
            and raasi_at(sunrise_jd) == 9
        ):
            selected.append(upavasa_date)
    return selected
