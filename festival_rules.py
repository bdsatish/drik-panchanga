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
    status: str = "provisional"
    source: str | None = None


FESTIVAL_RULES = (
    FestivalRule(
        1,
        "Ugadi",
        1,
        "S1",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80421204850/view",
    ),
    FestivalRule(
        2,
        "Rama Navami",
        1,
        "S9",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80421205021/view",
    ),
    FestivalRule(
        3,
        "Aksaya Trtiya",
        2,
        "S3",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80421210038/view",
    ),
    # No Vasavi/Kanyaka Parameshwari observance was found in Dharma Sindhu.
    # Keep the supplied community date provisionally until an authority is
    # provided; it must not be represented as a Dharma Sindhu rule.
    FestivalRule(4, "Vasavi jayanthi", 2, "S10", "unresolved"),
    FestivalRule(
        5,
        "Narasimha jayanthi",
        2,
        "S14",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80421210345/view",
    ),
    FestivalRule(
        6,
        "Guru Purnima",
        4,
        "S15",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80421213928/view",
    ),
    FestivalRule(
        7,
        "Naga panchami",
        5,
        "S5",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80422074237/view",
    ),
    FestivalRule(
        9,
        "Yajur upakarma",
        5,
        "S15",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80421215029/view",
    ),
    FestivalRule(
        10,
        "Janmashtami",
        5,
        "K8",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80421220129/view",
    ),
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
    FestivalRule(
        25,
        "Raksha Bandhan",
        5,
        "S15",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80421215617/view",
    ),
)

# The popular Friday-before-Sravana-Purnima rule was not found in Dharma
# Sindhu. Preserve it provisionally, but keep its provenance unresolved.
VARAMAHALAKSHMI_RULE = FestivalRule(
    8,
    "Varamahalakshmi vrata",
    5,
    "Friday before S15",
    "unresolved",
)
VARAMAHALAKSHMI_NUMBER = VARAMAHALAKSHMI_RULE.number
VARAMAHALAKSHMI_NAME = VARAMAHALAKSHMI_RULE.name
UGADI_NUMBER = 1
RAMA_NAVAMI_NUMBER = 2
AKSAYA_TRTIYA_NUMBER = 3
NARASIMHA_JAYANTHI_NUMBER = 5
GURU_PURNIMA_NUMBER = 6
NAGA_PANCHAMI_NUMBER = 7
YAJUR_UPAKARMA_NUMBER = 9
RAKSHA_BANDHAN_NUMBER = 25
JANMASHTAMI_NUMBER = 10
GANESHA_CATURTHI_NUMBER = 11
DURGA_ASHTAMI_NUMBER = 12
NARAKA_CATURDASI_NUMBER = 15
DIPAVALI_NUMBER = 16
ONE_GHATI_HOURS = 24 / 60
SIX_GHATI_HOURS = 6 * ONE_GHATI_HOURS
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


def select_ugadi_dates(records, rule):
    """Select the Chaitra year-opening Pratipada at local sunrise.

    Dharma Sindhu takes sunrise-vyapini Pratipada. If Pratipada occurs at
    both sunrises, or at neither sunrise because it is skipped, the earlier
    civil day is selected. When Chaitra is adhika, year-opening rites belong
    to adhika Chaitra rather than the following shuddha Chaitra.

    Source:
    https://www.transliteral.org/pages/z80421204850/view
    """
    chaitra_records = [
        record for record in records if record[2] == str(rule.masa)
    ]
    if not chaitra_records:
        return []

    preferred_is_adhika = any(record[3] for record in chaitra_records)
    chaitra_records = [
        record
        for record in chaitra_records
        if record[3] == preferred_is_adhika
    ]
    sunrise_matches = [
        record[0] for record in chaitra_records if record[1] == rule.tithi
    ]
    if sunrise_matches:
        return [min(sunrise_matches)]

    first_visible_shukla = next(
        (
            record[0]
            for record in chaitra_records
            if record[1].startswith("S")
        ),
        None,
    )
    if first_visible_shukla is None:
        return []
    return [first_visible_shukla - timedelta(days=1)]


def select_rama_navami_dates(records, rule):
    """Apply Dharma Sindhu's Madhyahna-vyapini Rama Navami rule.

    A day whose Madhyahna alone contains Navami is selected. If both days
    contain it, the later day is selected. If neither does, the later day is
    retained only when Navami lasts at least three daytime muhurtas after its
    sunrise; otherwise the earlier, Ashtami-viddha day is used. The vrata is
    not performed in adhika Chaitra.

    Sources:
    https://www.transliteral.org/pages/z80421205021/view
    https://www.transliteral.org/pages/z80421205313/view
    """
    candidates = []
    rule_records = records_for_rule(records, rule)
    for record in rule_records:
        civil_date, _, _, _, _, sunrise_jd, sunset_jd = record
        day_length = sunset_jd - sunrise_jd
        overlap = tithi_overlap_hours(
            sunrise_jd + day_length * 2 / 5,
            sunrise_jd + day_length * 3 / 5,
            9,
        )
        if overlap > 0:
            candidates.append((civil_date, overlap))

    if candidates:
        return [
            group[-1][0]
            for group in group_consecutive_candidates(candidates)
        ]

    daytime_candidates = []
    by_date = {record[0]: record for record in rule_records}
    for record in rule_records:
        civil_date, _, _, _, _, sunrise_jd, sunset_jd = record
        if tithi_overlap_hours(sunrise_jd, sunset_jd, 9) > 0:
            daytime_candidates.append((civil_date, 1))

    selected = []
    for group in group_consecutive_candidates(daytime_candidates):
        later_date = group[-1][0]
        later_record = by_date[later_date]
        sunrise_jd, sunset_jd = later_record[5:7]
        three_muhurtas_end = sunrise_jd + (sunset_jd - sunrise_jd) / 5
        if tithi_number_at(three_muhurtas_end) == 9:
            selected.append(later_date)
        else:
            selected.append(group[0][0])
    return selected


def select_aksaya_trtiya_dates(records, rule):
    """Apply Dharma Sindhu's preferred Yugadi-window decision.

    Akshaya Tritiya's japa, homa, tarpana, and dana follow the Shukla-Yugadi
    decision. Dharma Sindhu prefers the seventh through ninth daytime
    muhurtas. If only one civil day overlaps that window, use it; if both or
    neither do, use the later day. Yugadi rites are prescribed in both
    adhika and shuddha Vaishakha, so this selector does not discard adhika
    records.

    Source:
    https://www.transliteral.org/pages/z80421210038/view
    """
    rule_records = [
        record for record in records if record[2] == str(rule.masa)
    ]
    candidates = []
    for record in rule_records:
        civil_date, _, _, _, _, sunrise_jd, sunset_jd = record
        day_length = sunset_jd - sunrise_jd
        overlap = tithi_overlap_hours(
            sunrise_jd + day_length * 6 / 15,
            sunrise_jd + day_length * 9 / 15,
            3,
        )
        if overlap > 0:
            candidates.append((civil_date, overlap))

    if candidates:
        return [
            group[-1][0]
            for group in group_consecutive_candidates(candidates)
        ]

    daytime_candidates = []
    for record in rule_records:
        civil_date, _, _, _, _, sunrise_jd, sunset_jd = record
        if tithi_overlap_hours(sunrise_jd, sunset_jd, 3) > 0:
            daytime_candidates.append((civil_date, 1))
    return [
        group[-1][0]
        for group in group_consecutive_candidates(daytime_candidates)
    ]


def select_narasimha_jayanthi_dates(records, rule):
    """Select Vaishakha S14 at the exact local sunset.

    If Caturdashi occupies sunset on both civil days, or on neither, Dharma
    Sindhu selects the later day. Swati and Saturday increase merit but do
    not override this sunset decision.

    Source:
    https://www.transliteral.org/pages/z80421210345/view
    """
    rule_records = records_for_rule(records, rule)
    sunset_candidates = [
        (record[0], 1)
        for record in rule_records
        if tithi_number_at(record[6]) == 14
    ]
    if sunset_candidates:
        return [
            group[-1][0]
            for group in group_consecutive_candidates(sunset_candidates)
        ]

    daytime_candidates = [
        (record[0], 1)
        for record in rule_records
        if tithi_overlap_hours(record[5], record[6], 14) > 0
    ]
    return [
        group[-1][0]
        for group in group_consecutive_candidates(daytime_candidates)
    ]


def select_guru_purnima_dates(records, rule):
    """Select Ashadha Purnima with six ghatis after local sunrise.

    Dharma Sindhu's Vyasa-puja decision uses the later sunrise day only when
    Purnima remains for at least three muhurtas (six ghatis) after sunrise;
    when the later remainder is shorter, the previous Purnima day is used.

    Sources:
    https://www.transliteral.org/pages/z80421213928/view
    https://www.transliteral.org/pages/z80422074133/view
    """
    candidates = [
        (record[0], record[4])
        for record in records_for_rule(records, rule)
        if record[1] == rule.tithi
    ]
    selected = []
    for group in group_consecutive_candidates(candidates):
        if len(group) == 1:
            selected.append(group[0][0])
        elif group[-1][1] >= SIX_GHATI_HOURS:
            selected.append(group[-1][0])
        else:
            selected.append(group[-2][0])
    return selected


def select_naga_panchami_dates(records, rule):
    """Prefer Shashthi-yukta Panchami when it has three muhurtas.

    The later sunrise day is selected only when Panchami remains for at
    least three muhurtas (six ghatis). A shorter later Panchami is rejected
    in favor of the preceding Caturthi-viddha Panchami.

    Source:
    https://www.transliteral.org/pages/z80422074237/view
    """
    candidates = [
        (record[0], record[4])
        for record in records_for_rule(records, rule)
        if record[1] == rule.tithi
    ]
    selected = []
    for group in group_consecutive_candidates(candidates):
        if len(group) == 1:
            selected.append(group[0][0])
        elif group[-1][1] >= SIX_GHATI_HOURS:
            selected.append(group[-1][0])
        else:
            selected.append(group[-2][0])
    return selected


def eclipse_or_sankranti_in_window(start_jd, end_jd):
    """Return whether Dharma Sindhu's eight-yama window is contaminated."""
    start_rasi = int(panchanga.solar_longitude(start_jd) // 30)
    end_rasi = int(panchanga.solar_longitude(end_jd) // 30)
    if start_rasi != end_rasi:
        return True

    for finder in (
        panchanga.swe.lun_eclipse_when,
        panchanga.swe.sol_eclipse_when_glob,
    ):
        _, eclipse_times = finder(start_jd - 2)
        if start_jd <= eclipse_times[0] <= end_jd:
            return True
    return False


def karana_index_at(jd):
    """Return the half-tithi index, 1 through 60, at an arbitrary instant."""
    return int(panchanga.lunar_phase(jd) // 6) + 1


def is_vishti_at(jd):
    index = karana_index_at(jd)
    return 2 <= index <= 57 and (index - 2) % 7 == 6


def has_bhadra_free_purnima(start_jd, end_jd):
    """Check a ritual window for a Purnima instant outside Vishti/Bhadra."""
    for index in range(97):
        instant = start_jd + (end_jd - start_jd) * index / 96
        if tithi_number_at(instant) == 15 and not is_vishti_at(instant):
            return True
    return False


def nakshatra_number_at(jd):
    """Return the equal 27-part nakshatra at an arbitrary UTC instant."""
    return int(panchanga.lunar_longitude(jd) // (360 / 27)) + 1


def has_tithi_nakshatra(start_jd, end_jd, tithi_number, nakshatra_number):
    """Check whether a short ritual window contains a tithi/nakshatra yoga."""
    for index in range(97):
        instant = start_jd + (end_jd - start_jd) * index / 96
        if (
            tithi_number_at(instant) == tithi_number
            and nakshatra_number_at(instant) == nakshatra_number
        ):
            return True
    return False


def select_taittiriya_apastamba_upakarma_dates(records, rule):
    """Resolve Taittiriya-Apastamba Yajur Upakarma.

    Shravana Purnima is primary. If Purnima covers both sunrises, all
    Yajurvedins use the earlier day. For a split Purnima beginning after the
    first daytime muhurta, Taittiriyas use the later day when at least two
    muhurtas (four ghatis) remain after its sunrise; a shorter remainder uses
    the earlier day. Adhika-masa Upakarma is forbidden.

    An eclipse or sankranti between the preceding and following local night
    midpoints contaminates the selected day. Apastambas then use Bhadrapada
    Purnima. This implements Dharma Sindhu's principal eight-yama opinion,
    not its separately reported stricter element-touch opinion.

    Sources:
    https://www.transliteral.org/pages/z80421215029/view
    https://www.transliteral.org/pages/z80421215344/view
    """
    rule_records = records_for_rule(records, rule)
    by_date = {record[0]: record for record in records}
    sunrise_candidates = [
        (record[0], record[4])
        for record in rule_records
        if record[1] == rule.tithi
    ]
    selected = []
    for group in group_consecutive_candidates(sunrise_candidates):
        if len(group) > 1:
            selected_date = group[0][0]
        else:
            later_date, remainder = group[0]
            previous_date = later_date - timedelta(days=1)
            previous_record = by_date.get(previous_date)
            later_record = by_date[later_date]
            selected_date = later_date
            if previous_record is not None:
                intervals = tithi_intervals(
                    previous_record[5],
                    later_record[5],
                    15,
                )
                purnima_start = intervals[0][0] if intervals else later_record[5]
                first_muhurta_end = previous_record[5] + (
                    previous_record[6] - previous_record[5]
                ) / 15
                if (
                    purnima_start <= first_muhurta_end
                    or remainder < 4 * ONE_GHATI_HOURS
                ):
                    selected_date = previous_date

        selected_record = by_date[selected_date]
        previous_record = by_date.get(selected_date - timedelta(days=1))
        next_record = by_date.get(selected_date + timedelta(days=1))
        if previous_record is not None and next_record is not None:
            previous_midnight = (previous_record[6] + selected_record[5]) / 2
            following_midnight = (selected_record[6] + next_record[5]) / 2
            if eclipse_or_sankranti_in_window(
                previous_midnight,
                following_midnight,
            ):
                fallback_rule = FestivalRule(9, rule.name, 6, "S15")
                fallback = [
                    record[0]
                    for record in records_for_rule(records, fallback_rule)
                    if record[1] == "S15"
                ]
                if fallback:
                    selected_date = fallback[0]
        selected.append(selected_date)
    return selected


def select_janmashtami_dates(records, rule):
    """Resolve Dharma Sindhu Janmashtami at Nishitha.

    Nishitha is the eighth muhurta of the local night. A sole Nishitha-
    vyapini Ashtami is used; if Ashtami occupies both Nishithas, or neither,
    the later day is used. Rohini joined to Ashtami at Nishitha is preferred
    when available. Monday and Wednesday add merit but do not change dates.
    This is Dharma Sindhu Janmashtami, not a Gaudiya rule or either
    Sri-Vaishnava Sri-Jayanthi reckoning.

    Sources:
    https://www.transliteral.org/pages/z80421220129/view
    https://www.transliteral.org/pages/z80421220717/view
    https://www.transliteral.org/pages/z80421221115/view
    """
    rule_records = records_for_rule(records, rule)
    by_date = {record[0]: record for record in records}
    nishitha_candidates = []
    rohini_candidates = []
    for record in rule_records:
        next_record = by_date.get(record[0] + timedelta(days=1))
        if next_record is None:
            continue
        night_length = next_record[5] - record[6]
        nishitha_start = record[6] + night_length * 7 / 15
        nishitha_end = record[6] + night_length * 8 / 15
        overlap = tithi_overlap_hours(
            nishitha_start,
            nishitha_end,
            23,
        )
        if overlap > 0:
            candidate = (record[0], overlap)
            nishitha_candidates.append(candidate)
            if has_tithi_nakshatra(
                nishitha_start,
                nishitha_end,
                23,
                4,
            ):
                rohini_candidates.append(candidate)

    candidates = rohini_candidates or nishitha_candidates
    if candidates:
        return [
            group[-1][0]
            for group in group_consecutive_candidates(candidates)
        ]

    daytime_candidates = [
        (record[0], 1)
        for record in rule_records
        if tithi_overlap_hours(record[5], record[6], 23) > 0
    ]
    return [
        group[-1][0]
        for group in group_consecutive_candidates(daytime_candidates)
    ]


def select_raksha_bandhan_dates(records, rule):
    """Select Bhadra-free Shravana Purnima in Aparahna or Pradosha.

    When Purnima remains for more than three muhurtas (six ghatis) after
    sunrise, that day is used. A shorter next-sunrise remainder sends the
    observance to the preceding day's Bhadra-free Pradosha. Unlike Upakarma,
    eclipse and sankranti do not prohibit Raksha Bandhan.

    Sources:
    https://www.transliteral.org/pages/z80421215617/view
    https://www.transliteral.org/pages/z80422112841/view
    """
    by_date = {record[0]: record for record in records}
    candidates = [
        (record[0], record[4])
        for record in records_for_rule(records, rule)
        if record[1] == rule.tithi
    ]
    selected = []
    for group in group_consecutive_candidates(candidates):
        later_date, remainder = group[-1]
        selected_date = (
            later_date
            if remainder > SIX_GHATI_HOURS
            else later_date - timedelta(days=1)
        )
        selected_record = by_date.get(selected_date)
        if selected_record is not None:
            sunrise_jd, sunset_jd = selected_record[5:7]
            day_length = sunset_jd - sunrise_jd
            aparahna = (
                sunrise_jd + day_length * 3 / 5,
                sunrise_jd + day_length * 4 / 5,
            )
            pradosha = (
                sunset_jd,
                sunset_jd + PRADOSHA_HOURS / 24,
            )
            if not (
                has_bhadra_free_purnima(*aparahna)
                or has_bhadra_free_purnima(*pradosha)
            ):
                previous_date = selected_date - timedelta(days=1)
                if previous_date in by_date:
                    selected_date = previous_date
        selected.append(selected_date)
    return selected


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


def tithi_intervals(start_jd, end_jd, target_tithi):
    """Find target-tithi intervals by bracketing each phase transition."""
    step = 0.25
    intervals = []
    cursor = start_jd
    active = tithi_number_at(cursor) == target_tithi
    interval_start = cursor if active else None

    while cursor < end_jd:
        following = min(cursor + step, end_jd)
        following_active = tithi_number_at(following) == target_tithi
        if active != following_active:
            low, high = cursor, following
            for _ in range(50):
                middle = (low + high) / 2
                middle_active = tithi_number_at(middle) == target_tithi
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


def resolve_dharma_sindhu_vaishnava_ekadashi_dates(months, month_data):
    """Resolve Dharma Sindhu Vaishnava Ekadashi upavasa dates.

    Dharma Sindhu distinguishes Vaishnavas from Smartas by Dashami-vedha:

    * Arunodaya is the four-ghati (96-minute) period before local sunrise.
      If even a trace of Dashami remains after Arunodaya begins, Ekadashi is
      viddha for Vaishnavas; that civil day is rejected and upavasa moves to
      the following day (Dvadashi).
    * A shuddha Ekadashi also moves to the following day when Ekadashi has
      adhikya (it remains after the next sunrise), when Dvadashi has adhikya
      (it remains after the subsequent sunrise), or when both have adhikya.
    * Only a shuddha occurrence with neither Ekadashi nor Dvadashi adhikya
      is observed on the first day.
    * Both Shukla and Krishna Ekadashis are included. An adhika masa therefore
      contributes its own two observances. This function selects upavasa dates
      only; it intentionally does not calculate the following day's Parana.

    Dharma Sindhu, "Vaishnava vrata-day determination" and its summary:
    https://www.transliteral.org/pages/z80422042154/view
    https://www.transliteral.org/pages/z80422042403/view

    Sri Vaishnava sources confirm the four-ghati Arunodaya/Dashami rule while
    cautioning that exceptional Ekadashi/Dvadashi growth and loss cases can
    depend on one's acharya, family, or regional practice:
    https://ibiblio.org/sripedia/srirangasri/archives/jul01/msg00084.html
    https://www.ibiblio.org/sripedia/ramanuja/archives/jan06/msg00060.html

    Therefore this is deliberately the pure Dharma Sindhu fallback requested
    for this calendar. It does not import the Gaudiya/ISKCON GCal rules for
    named nakshatra Mahadvadashis, Pakshavardhini, or other Gaurabda-specific
    decisions.
    """
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
        for ekadashi_start, _ in tithi_intervals(
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
            arunodaya = first_sunrise - ARUNODAYA_HOURS / 24

            is_dashami_viddha = (
                tithi_number_at(arunodaya + epsilon) == dashami_tithi
            )
            ekadashi_has_adhikya = (
                tithi_number_at(second_sunrise + epsilon)
                == ekadashi_tithi
            )
            dvadashi_has_adhikya = (
                tithi_number_at(third_sunrise + epsilon)
                == dvadashi_tithi
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
    records = collect_records(months, month_data)

    dates_by_number = {}
    names_by_number = {}
    for rule in FESTIVAL_RULES:
        if rule.number == UGADI_NUMBER:
            matches = select_ugadi_dates(records, rule)
        elif rule.number == RAMA_NAVAMI_NUMBER:
            matches = select_rama_navami_dates(records, rule)
        elif rule.number == AKSAYA_TRTIYA_NUMBER:
            matches = select_aksaya_trtiya_dates(records, rule)
        elif rule.number == NARASIMHA_JAYANTHI_NUMBER:
            matches = select_narasimha_jayanthi_dates(records, rule)
        elif rule.number == GURU_PURNIMA_NUMBER:
            matches = select_guru_purnima_dates(records, rule)
        elif rule.number == NAGA_PANCHAMI_NUMBER:
            matches = select_naga_panchami_dates(records, rule)
        elif rule.number == YAJUR_UPAKARMA_NUMBER:
            matches = select_taittiriya_apastamba_upakarma_dates(records, rule)
        elif rule.number == RAKSHA_BANDHAN_NUMBER:
            matches = select_raksha_bandhan_dates(records, rule)
        elif rule.number == JANMASHTAMI_NUMBER:
            matches = select_janmashtami_dates(records, rule)
        elif rule.tithi == "S1":
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
