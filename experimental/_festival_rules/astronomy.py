"""Low-level astronomical helpers with injectable compatibility seams."""


def tithi_number_at(jd, panchanga):
    return int(panchanga.lunar_phase(jd) // 12) + 1


def tithi_overlap_hours(start_jd, end_jd, target_tithi, tithi_at):
    epsilon = 1e-10
    start_matches = tithi_at(start_jd + epsilon) == target_tithi
    end_matches = tithi_at(end_jd - epsilon) == target_tithi
    if start_matches and end_matches:
        return (end_jd - start_jd) * 24
    if not start_matches and not end_matches:
        return 0

    low, high = start_jd, end_jd
    for _ in range(50):
        middle = (low + high) / 2
        middle_matches = tithi_at(middle) == target_tithi
        if start_matches:
            if middle_matches:
                low = middle
            else:
                high = middle
        elif middle_matches:
            high = middle
        else:
            low = middle
    if start_matches:
        return (low - start_jd) * 24
    return (end_jd - high) * 24


def intervals_overlap(first_start, first_end, second_start, second_end):
    return max(first_start, second_start) < min(first_end, second_end)


def locally_visible_eclipse_in_window(
    start_jd,
    end_jd,
    geopos,
    *,
    panchanga,
    overlap_checker,
):
    search_start = start_jd - 1
    lunar_flags, lunar_times, _ = panchanga.swe.lun_eclipse_when_loc(
        search_start,
        geopos,
    )
    is_purely_penumbral = (
        lunar_flags & panchanga.swe.ECL_PENUMBRAL
        and not lunar_flags
        & (panchanga.swe.ECL_PARTIAL | panchanga.swe.ECL_TOTAL)
    )
    if not is_purely_penumbral:
        lunar_start, lunar_end = lunar_times[2], lunar_times[3]
        moonrise, moonset = lunar_times[8], lunar_times[9]
        if moonrise and lunar_start <= moonrise <= lunar_end:
            lunar_start = moonrise
        if moonset and lunar_start <= moonset <= lunar_end:
            lunar_end = moonset
        if (
            lunar_start
            and lunar_end
            and overlap_checker(
                start_jd,
                end_jd,
                lunar_start,
                lunar_end,
            )
        ):
            return True

    _, solar_times, _ = panchanga.swe.sol_eclipse_when_loc(
        search_start,
        geopos,
    )
    solar_start, solar_end = solar_times[1], solar_times[4]
    sunrise, sunset = solar_times[5], solar_times[6]
    if sunrise and solar_start <= sunrise <= solar_end:
        solar_start = sunrise
    if sunset and solar_start <= sunset <= solar_end:
        solar_end = sunset
    return bool(
        solar_start
        and solar_end
        and overlap_checker(
            start_jd,
            end_jd,
            solar_start,
            solar_end,
        )
    )


def eclipse_or_sankranti_in_window(
    start_jd,
    end_jd,
    geopos,
    *,
    panchanga,
    eclipse_checker,
):
    start_rasi = int(panchanga.solar_longitude(start_jd) // 30)
    end_rasi = int(panchanga.solar_longitude(end_jd) // 30)
    if start_rasi != end_rasi:
        return True
    return eclipse_checker(start_jd, end_jd, geopos)


def karana_index_at(jd, panchanga):
    return int(panchanga.lunar_phase(jd) // 6) + 1


def is_vishti_at(jd, karana_at):
    index = karana_at(jd)
    return 2 <= index <= 57 and (index - 2) % 7 == 6


def has_bhadra_free_purnima(start_jd, end_jd, tithi_at, vishti_at):
    for index in range(97):
        instant = start_jd + (end_jd - start_jd) * index / 96
        if tithi_at(instant) == 15 and not vishti_at(instant):
            return True
    return False


def nakshatra_number_at(jd, panchanga):
    return int(panchanga.lunar_longitude(jd) // (360 / 27)) + 1


def nakshatra_overlap_hours(start_jd, end_jd, target_nakshatra, nakshatra_at):
    epsilon = 1e-10
    start_matches = nakshatra_at(start_jd + epsilon) == target_nakshatra
    end_matches = nakshatra_at(end_jd - epsilon) == target_nakshatra
    if start_matches and end_matches:
        return (end_jd - start_jd) * 24
    if not start_matches and not end_matches:
        return 0

    low, high = start_jd, end_jd
    for _ in range(50):
        middle = (low + high) / 2
        middle_matches = nakshatra_at(middle) == target_nakshatra
        if start_matches:
            if middle_matches:
                low = middle
            else:
                high = middle
        elif middle_matches:
            high = middle
        else:
            low = middle
    if start_matches:
        return (low - start_jd) * 24
    return (end_jd - high) * 24


def has_tithi_nakshatra(
    start_jd,
    end_jd,
    tithi_number,
    nakshatra_number,
    *,
    tithi_at,
    nakshatra_at,
):
    for index in range(97):
        instant = start_jd + (end_jd - start_jd) * index / 96
        if (
            tithi_at(instant) == tithi_number
            and nakshatra_at(instant) == nakshatra_number
        ):
            return True
    return False


def has_nakshatra(start_jd, end_jd, nakshatra_number, nakshatra_at):
    for index in range(97):
        instant = start_jd + (end_jd - start_jd) * index / 96
        if nakshatra_at(instant) == nakshatra_number:
            return True
    return False


def nakshatra_overlaps(start_jd, end_jd, nakshatra_number, nakshatra_at):
    epsilon = 1e-10
    return (
        nakshatra_at(start_jd + epsilon) == nakshatra_number
        or nakshatra_at(end_jd - epsilon) == nakshatra_number
    )


def tithi_intervals(start_jd, end_jd, target_tithi, tithi_at):
    step = 0.25
    intervals = []
    cursor = start_jd
    active = tithi_at(cursor) == target_tithi
    interval_start = cursor if active else None
    while cursor < end_jd:
        following = min(cursor + step, end_jd)
        following_active = tithi_at(following) == target_tithi
        if active != following_active:
            low, high = cursor, following
            for _ in range(50):
                middle = (low + high) / 2
                middle_active = tithi_at(middle) == target_tithi
                if middle_active == active:
                    low = middle
                else:
                    high = middle
            boundary = (low + high) / 2
            if following_active:
                interval_start = boundary
            else:
                intervals.append((interval_start, boundary))
                interval_start = None
        cursor = following
        active = following_active
    if interval_start is not None:
        intervals.append((interval_start, end_jd))
    return intervals
