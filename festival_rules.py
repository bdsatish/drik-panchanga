"""Festival definitions and observance-date rules for the PDF calendar."""

import calendar
from dataclasses import dataclass
from datetime import date as CivilDate
from datetime import timedelta

import panchanga


@dataclass(frozen=True)
class FestivalRule:
    number: int
    name: str
    masa: int
    tithi: str


FESTIVAL_RULES = (
    FestivalRule(1, "Ugadi", 1, "S1"),
    FestivalRule(2, "Rama Navami", 1, "S9"),
    FestivalRule(3, "Aksaya Trtiya", 2, "S3"),
    FestivalRule(4, "Vasavi jayanthi", 2, "S10"),
    FestivalRule(5, "Narasimha jayanthi", 2, "S14"),
    FestivalRule(6, "Guru Purnima", 4, "S15"),
    FestivalRule(7, "Naga panchami", 5, "S5"),
    FestivalRule(9, "Yajur upakarma, Rakhi", 5, "S15"),
    FestivalRule(10, "Janmashtami", 5, "K8"),
    FestivalRule(11, "Ganesa caturthi", 6, "S4"),
    FestivalRule(12, "Durgastami", 7, "S8"),
    FestivalRule(13, "Ayudha puja", 7, "S9"),
    FestivalRule(14, "Vijaya dasami", 7, "S10"),
    FestivalRule(15, "Naraka caturdasi", 7, "K14"),
    FestivalRule(16, "Dipavali", 7, "K15"),
    FestivalRule(17, "Bali padyami", 8, "S1"),
    FestivalRule(18, "Gita jayanti", 9, "S11"),
    FestivalRule(19, "Vasavi atmarpana", 11, "S2"),
    FestivalRule(20, "Vasanta pancami", 11, "S5"),
    FestivalRule(21, "Ratha saptami", 11, "S7"),
    FestivalRule(22, "VSN jayanthi", 11, "S11"),
    FestivalRule(23, "Holi", 12, "K1"),
    FestivalRule(24, "Maha Shivaratri", 11, "K14"),
)

VARAMAHALAKSHMI_NUMBER = 8
VARAMAHALAKSHMI_NAME = "Varamahalakshmi vrata"
GANESHA_CATURTHI_NUMBER = 11
DURGA_ASHTAMI_NUMBER = 12
NARAKA_CATURDASI_NUMBER = 15
DIPAVALI_NUMBER = 16
ONE_GHATI_HOURS = 24 / 60
ARUNODAYA_HOURS = 4 * ONE_GHATI_HOURS
PRADOSHA_HOURS = 6 * ONE_GHATI_HOURS


def format_festival_dates(dates):
    dates = sorted(dates)
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
            f"{dates[0].day}-{dates[-1].day}"
        )
    return ",".join(
        f"{calendar.month_abbr[value.month]} {value.day}"
        for value in dates
    )


def tithi_number_at(jd):
    """Return the tithi prevailing at an arbitrary UTC Julian instant."""
    return int(panchanga.lunar_phase(jd) // 12) + 1


def tithi_overlap_hours(start_jd, end_jd, target_tithi):
    """Measure target-tithi overlap with a short ritual-time window."""
    epsilon = 1e-10
    start_matches = tithi_number_at(start_jd + epsilon) == target_tithi
    end_matches = tithi_number_at(end_jd - epsilon) == target_tithi
    if start_matches and end_matches:
        return (end_jd - start_jd) * 24
    if not start_matches and not end_matches:
        return 0

    low, high = start_jd, end_jd
    for _ in range(50):
        middle = (low + high) / 2
        middle_matches = tithi_number_at(middle) == target_tithi
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


def select_ganesha_caturthi_dates(records, rule):
    """Apply Dharma Sindhu's Madhyahna-vyapini, purva-viddha rule.

    Madhyahna is the middle fifth of local daytime. When Caturthi qualifies
    on both days, the earlier day is selected if Caturthi occupies at least
    one ghati (24 minutes) of its Madhyahna. If Caturthi begins only after
    the first day's Madhyahna, the following day is selected.

    Sources:
    https://www.kamakoti.org/kamakoti/dharmasindhu/bookview.php?chapnum=5
    https://www.kamakoti.org/kamakoti/dharmasindhu/bookview.php?chapnum=7
    """
    candidates = []
    for record in records_for_rule(records, rule):
        civil_date, _, _, _, _, sunrise_jd, sunset_jd = record
        day_length = sunset_jd - sunrise_jd
        madhyahna_start = sunrise_jd + day_length * 2 / 5
        madhyahna_end = sunrise_jd + day_length * 3 / 5
        overlap = tithi_overlap_hours(
            madhyahna_start,
            madhyahna_end,
            4,
        )
        if overlap > 0:
            candidates.append((civil_date, overlap))

    selected = []
    for group in group_consecutive_candidates(candidates):
        qualified = [
            candidate
            for candidate in group
            if candidate[1] >= ONE_GHATI_HOURS
        ]
        selected.append((qualified or group)[0][0])
    return selected


def select_naraka_caturdasi_dates(records, rule):
    """Select K14 during Arunodaya for the South Indian pre-dawn observance.

    Arunodaya is the four-ghati (96-minute) period before local sunrise.
    If K14 touches Arunodaya on two successive dates, the date with greater
    K14 coverage of the ritual window is selected.

    Sources:
    https://www.kamakoti.org/kamakoti/dharmasindhu/bookview.php?chapnum=8
    https://www.drikpanchang.com/diwali/naraka-chaturdashi/info/naraka-chaturdashi.html
    """
    candidates = []
    for record in records_for_rule(records, rule):
        civil_date, _, _, _, _, sunrise_jd, _ = record
        overlap = tithi_overlap_hours(
            sunrise_jd - ARUNODAYA_HOURS / 24,
            sunrise_jd,
            29,
        )
        if overlap > 0:
            candidates.append((civil_date, overlap))

    selected = []
    for group in group_consecutive_candidates(candidates):
        selected.append(max(group, key=lambda candidate: candidate[1])[0])
    return selected


def select_dipavali_dates(records, rule):
    """Apply Dharma Sindhu's Pradosha-vyapini Amavasya rule.

    Lakshmi Puja is assigned to the local evening on which Amavasya occupies
    at least one ghati (24 minutes) of Pradosha. When both consecutive
    evenings qualify, the later, Pratipada-yukta date is selected; when only
    the earlier evening qualifies, that date is retained.

    Sources:
    https://www.kamakoti.org/kamakoti/dharmasindhu/bookview.php?chapnum=8
    https://www.drikpanchang.com/diwali/diwali-puja-calendar.html
    """
    candidates = []
    for record in records_for_rule(records, rule):
        civil_date, _, _, _, _, _, sunset_jd = record
        overlap = tithi_overlap_hours(
            sunset_jd,
            sunset_jd + PRADOSHA_HOURS / 24,
            30,
        )
        if overlap > 0:
            candidates.append((civil_date, overlap))

    selected = []
    for group in group_consecutive_candidates(candidates):
        qualified = [
            candidate
            for candidate in group
            if candidate[1] >= ONE_GHATI_HOURS
        ]
        selected.append((qualified or group)[-1][0])
    return selected


def select_durga_ashtami_dates(candidates):
    """Apply Dharma Sindhu's rule to Ashtami at consecutive sunrises.

    The Navami-yukta (later) day is selected only when Ashtami remains
    for at least one ghati (24 minutes) after that day's sunrise. If less
    than one ghati remains, the previous day is selected. A Saptami-viddha
    day is excluded because candidates contain only days on which Ashtami
    itself prevails at sunrise. Sandhi Puja is intentionally not considered.

    Source, "Mahashtami Nirnaya":
    https://www.transliteral.org/pages/z80501061410/view
    """
    selected = []
    for group in group_consecutive_candidates(candidates):
        if len(group) == 1:
            selected.append(group[0][0])
            continue
        later_date, hours_after_sunrise = group[-1]
        if hours_after_sunrise >= ONE_GHATI_HOURS:
            selected.append(later_date)
        else:
            selected.append(group[-2][0])
    return selected


def resolve_festivals(months, month_data):
    """Resolve festivals against daily panchanga and ritual-time windows.

    Each raw daily record is:
    day, tithi, nakshatra, masa, is_adhika, tithi-hours-after-sunrise,
    sunrise UTC Julian day, sunset UTC Julian day.
    """
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

    dates_by_number = {}
    names_by_number = {}
    for rule in FESTIVAL_RULES:
        if rule.tithi == "S1":
            matches = []
            for index, (
                civil_date,
                day_tithi,
                masa,
                is_adhika,
                _,
                _,
                _,
            ) in enumerate(records):
                if (
                    masa != str(rule.masa)
                    or is_adhika
                    or not day_tithi.startswith("S")
                ):
                    continue
                if index == 0:
                    is_masa_start = day_tithi in {"S1", "S2"}
                else:
                    (
                        _,
                        _,
                        previous_masa,
                        previous_is_adhika,
                        _,
                        _,
                        _,
                    ) = records[
                        index - 1
                    ]
                    is_masa_start = (
                        previous_masa != masa
                        or previous_is_adhika != is_adhika
                    )
                if is_masa_start:
                    matches.append(civil_date)
        elif rule.number == GANESHA_CATURTHI_NUMBER:
            matches = select_ganesha_caturthi_dates(records, rule)
        elif rule.number == DURGA_ASHTAMI_NUMBER:
            candidates = [
                (civil_date, hours_after_sunrise)
                for (
                    civil_date,
                    day_tithi,
                    masa,
                    is_adhika,
                    hours_after_sunrise,
                    _,
                    _,
                ) in records
                if (
                    day_tithi == rule.tithi
                    and masa == str(rule.masa)
                    and not is_adhika
                )
            ]
            matches = select_durga_ashtami_dates(candidates)
        elif rule.number == NARAKA_CATURDASI_NUMBER:
            matches = select_naraka_caturdasi_dates(records, rule)
        elif rule.number == DIPAVALI_NUMBER:
            matches = select_dipavali_dates(records, rule)
        else:
            matches = [
                civil_date
                for (
                    civil_date,
                    day_tithi,
                    masa,
                    is_adhika,
                    _,
                    _,
                    _,
                ) in records
                if (
                    day_tithi == rule.tithi
                    and masa == str(rule.masa)
                    and not is_adhika
                )
            ]
        if not matches:
            raise RuntimeError(f"No calendar date found for {rule.name}")
        dates_by_number[rule.number] = matches
        names_by_number[rule.number] = rule.name

    vrata_dates = []
    for sravana_purnima_date in dates_by_number[9]:
        vrata_date = sravana_purnima_date - timedelta(days=1)
        while vrata_date.weekday() != calendar.FRIDAY:
            vrata_date -= timedelta(days=1)
        vrata_dates.append(vrata_date)
    dates_by_number[VARAMAHALAKSHMI_NUMBER] = sorted(set(vrata_dates))
    names_by_number[VARAMAHALAKSHMI_NUMBER] = VARAMAHALAKSHMI_NAME

    numbers_by_date = {}
    entries = []
    for number in sorted(names_by_number):
        dates = dates_by_number[number]
        for civil_date in dates:
            numbers_by_date.setdefault(civil_date, []).append(number)
        entries.append(
            (
                number,
                format_festival_dates(dates),
                names_by_number[number],
            )
        )
    return numbers_by_date, entries
