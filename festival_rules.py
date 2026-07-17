"""Festival definitions and observance-date rules for the PDF calendar."""

import calendar
from dataclasses import dataclass
from datetime import date as CivilDate
from datetime import timedelta

import panchanga


TRADITIONAL_FESTIVAL_POLICY = "traditional"
GENERIC_UDAYA_FESTIVAL_POLICY = "generic-udaya"
GENERIC_KALA_FESTIVAL_POLICY = "generic-kala"
FESTIVAL_POLICIES = (
    TRADITIONAL_FESTIVAL_POLICY,
    GENERIC_UDAYA_FESTIVAL_POLICY,
    GENERIC_KALA_FESTIVAL_POLICY,
)


@dataclass(frozen=True)
class FestivalRule:
    number: int
    name: str
    masa: int
    tithi: str
    status: str = "provisional"
    source: str | None = None
    allow_empty: bool = False


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
        "Akshaya Tritiya",
        2,
        "S3",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80421210038/view",
    ),
    # No Vasavi/Kanyaka Parameshwari observance was found in Dharma Sindhu.
    # Resolve the supplied community tithi with the generic udaya policy:
    # one sunrise uses that date, vriddhi uses the first sunrise, and kshaya
    # uses the civil day whose sunrise-to-sunrise span contains Dashami.
    FestivalRule(4, "Vasavi Jayanti", 2, "S10", "generic-udaya"),
    FestivalRule(
        5,
        "Narasimha Jayanti",
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
        "Naga Panchami",
        5,
        "S5",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80422074237/view",
    ),
    FestivalRule(
        9,
        "Rig Upakarma",
        5,
        "Shravana nakshatra",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80422074617/view",
    ),
    FestivalRule(
        10,
        "Yajur Upakarma",
        5,
        "S15",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80421215029/view",
        True,
    ),
    FestivalRule(
        11,
        "Raksha Bandhan",
        5,
        "S15",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80421215617/view",
    ),
    FestivalRule(
        12,
        "Janmashtami",
        5,
        "K8",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80421220129/view",
    ),
    FestivalRule(
        13,
        "Swarna Gowri Vrata",
        6,
        "S3",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80503220901/view",
    ),
    FestivalRule(
        14,
        "Ganesha Chaturthi",
        6,
        "S4",
        "dharmasindhu",
        "https://www.kamakoti.org/kamakoti/dharmasindhu/bookview.php?chapnum=7",
    ),
    FestivalRule(
        15,
        "Mahalaya Amavasya",
        6,
        "K15",
        "dharmasindhu",
        "http://hindupanchang.blogspot.com/2008/03/",
    ),
    FestivalRule(
        16,
        "Durga Ashtami",
        7,
        "S8",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80501061410/view",
    ),
    # This is the regional South Indian/Khande-Navami observance, rather than
    # Dharma Sindhu's distinct Mahanavami puja/upavasa decision.
    FestivalRule(17,
        "Durga Ashtami (Puja)",
        7,
        "S8",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80501061410/view",
    ),    FestivalRule(18,
        "Ayudha Puja",
        7,
        "S9",
        "regional",
        (
            "https://www.drikpanchang.com/navratri/durga-puja/"
            "ayudha-puja-date-time.html"
        ),
    ),
    FestivalRule(19,
        "Mahanavami (Puja)",
        7,
        "S9",
        "dharmasindhu",
        "https://www.drikpanchang.com/navratri/durga-puja/bengal/maha-navami-date-time.html",
    ),
    FestivalRule(20,
        "Vijayadashami (Puja)",
        7,
        "S10",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80501062120/view",
    ),
    FestivalRule(21,
        "Dasara",
        7,
        "S10",
        "regional",
    ),
    FestivalRule(22,
        "Dhana Trayodashi",
        7,
        "K13",
        "dharmasindhu",
        "https://nepaljyotish.org/en/blog/dharmasindhu-vrata-nirnaya/",
    ),
    FestivalRule(
        23,
        "Naraka Chaturdashi",
        7,
        "K14",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80505062049/view",
    ),
    FestivalRule(
        24,
        "Deepavali",
        7,
        "K15",
        "dharmasindhu",
        "https://www.kamakoti.org/kamakoti/dharmasindhu/bookview.php?chapnum=8",
    ),
    FestivalRule(25,
        "Bali Padyami",
        8,
        "S1",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80505062407/view",
    ),
    # No Gita-Jayanti observance was found in Dharma Sindhu's Margashirsha
    # section. Resolve the supplied community tithi with the documented
    # generic udaya-marker policy.
    FestivalRule(26, "Gita Jayanti", 9, "S11", "generic-udaya"),
    FestivalRule(27,
        "Vaikuntha Ekadashi",
        9,
        "Dhanur-masa S11",
        "regional",
        (
            "https://www.drikpanchang.com/ekadashis/vaikuntha/"
            "vaikuntha-ekadashi-date-time.html"
        ),
        allow_empty=True,
    ),
    FestivalRule(28,
        "Makara Sankranti",
        0,
        "Solar",
        "dharmasindhu",
        "https://www.kamakoti.org/kamakoti/dharmasindhu/bookview.php?chapnum=11",
    ),
    # No Vasavi Atmarpana observance was found in Dharma Sindhu's Magha
    # section. Resolve the supplied community tithi with the documented
    # generic sunrise, first-sunrise vriddhi, and contained-tithi kshaya
    # policy.
    FestivalRule(29, "Vasavi Atmarpana", 11, "S2", "generic-udaya"),
    FestivalRule(30,
        "Vasanta Panchami",
        11,
        "S5",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80513003421/view",
    ),
    FestivalRule(31,
        "Ratha Saptami",
        11,
        "S7",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80513004113/view",
    ),
    # Vishnu-Sahasranama Jayanti was not found in Dharma Sindhu; Bhishma
    # Ashtami is present but is a different observance. Resolve the supplied
    # community tithi with the documented generic udaya-marker policy.
    FestivalRule(32, "VSN Jayanti", 11, "S11", "generic-udaya"),
    FestivalRule(33,
        "Maha Shivaratri",
        11,
        "K14",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80513005728/view",
    ),
    FestivalRule(34,
        "Kama Dahana (Holi)",
        12,
        "S15",
        "dharmasindhu",
        "https://www.kamakoti.org/kamakoti/dharmasindhu/bookview.php?chapnum=13",
    ),
    FestivalRule(35,
        "Dhanvantari Jayanti",
        7,
        "K13",
        "regional",
    ),

)

# This regional rule was not found in Dharma Sindhu. TTD and Sringeri
# calendars move the vrata seven days earlier when Shravana Purnima itself
# is Friday; SRS Mutt and Drik Panchang instead use that Purnima Friday.
# Prefer the user's TTD convention: the last Friday strictly BEFORE the
# amanta, non-adhika Shravana Purnima, independently of Upakarma deferrals.
# E.g. In 2026, Sarvana-S15 is Friday Aug 28. It overlaps with Yajur Upakarma
# so, husband/wife would be both burdened. Moving it to Aug 21 reduces
# workload and practically makes sense. TTD and Sringeri calendars do so.
VARAMAHALAKSHMI_RULE = FestivalRule(
    8,
    "Varamahalakshmi Vrata",
    5,
    "Last Friday strictly before S15",
    "regional",
)
VARAMAHALAKSHMI_NUMBER = VARAMAHALAKSHMI_RULE.number
VARAMAHALAKSHMI_NAME = VARAMAHALAKSHMI_RULE.name
UGADI_NUMBER = 1
RAMA_NAVAMI_NUMBER = 2
AKSAYA_TRTIYA_NUMBER = 3
VASAVI_JAYANTI_NUMBER = 4
NARASIMHA_JAYANTI_NUMBER = 5
GURU_PURNIMA_NUMBER = 6
NAGA_PANCHAMI_NUMBER = 7
RIG_UPAKARMA_NUMBER = 9
YAJUR_UPAKARMA_NUMBER = 10
RAKSHA_BANDHAN_NUMBER = 11
JANMASHTAMI_NUMBER = 12
GOWRI_HABBA_NUMBER = 13
GANESHA_CATURTHI_NUMBER = 14
MAHALAYA_AMAVASYA_NUMBER = 15
DURGA_ASHTAMI_NUMBER = 16
DURGA_ASHTAMI_PUJA_NUMBER = 17
AYUDHA_PUJA_NUMBER = 18
MAHANAVAMI_PUJA_NUMBER = 19
VIJAYA_DASAMI_NUMBER = 20
DASARA_NUMBER = 21
DHANA_TRAYODASHI_NUMBER = 22
NARAKA_CHATURDASHI_NUMBER = 23
DEEPAVALI_NUMBER = 24
BALI_PADYAMI_NUMBER = 25
GITA_JAYANTI_NUMBER = 26
VAIKUNTHA_EKADASHI_NUMBER = 27
MAKARA_SANKRANTI_NUMBER = 28
VASAVI_ATMARPANA_NUMBER = 29
VASANTA_PANCHAMI_NUMBER = 30
RATHA_SAPTAMI_NUMBER = 31
VSN_JAYANTI_NUMBER = 32
MAHA_SHIVARATRI_NUMBER = 33
KAMA_DAHANA_NUMBER = 34
DHANVANTARI_JAYANTI_NUMBER = 35
PURVAHNA_KALA = "purvahna"
MADHYAHNA_KALA = "madhyahna"
APARAHNA_KALA = "aparahna"
SUNSET_KALA = "sunset"
SAYAHNA_KALA = "sayahna"
RATRI_KALA = "ratri"
PURVODAYA_KALA = "purvodaya"
SUNRISE_KALA = "sunrise"
GENERIC_KALA_BY_FESTIVAL = {
    UGADI_NUMBER: SUNRISE_KALA,
    RIG_UPAKARMA_NUMBER: PURVAHNA_KALA,
    VASANTA_PANCHAMI_NUMBER: PURVAHNA_KALA,
    RAMA_NAVAMI_NUMBER: MADHYAHNA_KALA,
    AKSAYA_TRTIYA_NUMBER: MADHYAHNA_KALA,
    GANESHA_CATURTHI_NUMBER: MADHYAHNA_KALA,
    BALI_PADYAMI_NUMBER: MADHYAHNA_KALA,
    RAKSHA_BANDHAN_NUMBER: APARAHNA_KALA,
    MAHALAYA_AMAVASYA_NUMBER: APARAHNA_KALA,
    MAHANAVAMI_PUJA_NUMBER: APARAHNA_KALA,
    VIJAYA_DASAMI_NUMBER: APARAHNA_KALA,
    NARASIMHA_JAYANTI_NUMBER: SUNSET_KALA,
    DHANA_TRAYODASHI_NUMBER: SAYAHNA_KALA,
    DEEPAVALI_NUMBER: SAYAHNA_KALA,
    KAMA_DAHANA_NUMBER: SAYAHNA_KALA,
    JANMASHTAMI_NUMBER: RATRI_KALA,
    MAHA_SHIVARATRI_NUMBER: RATRI_KALA,
    NARAKA_CHATURDASHI_NUMBER: PURVODAYA_KALA,
    RATHA_SAPTAMI_NUMBER: PURVODAYA_KALA,
}
GENERIC_KALA_NAME_BY_FESTIVAL = {
    JANMASHTAMI_NUMBER: "Janmashtami (Ratri Kala)",
}
ONE_GHATI_HOURS = 24 / 60
SIX_GHATI_HOURS = 6 * ONE_GHATI_HOURS
ARUNODAYA_HOURS = 4 * ONE_GHATI_HOURS
PRADOSHA_HOURS = 6 * ONE_GHATI_HOURS


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
    """Select every Chaitra year-opening Pratipada in the supplied range.

    Dharma Sindhu takes sunrise-vyapini Pratipada. If Pratipada occurs at
    both sunrises, or at neither sunrise because it is skipped, the earlier
    civil day is selected. When Chaitra is adhika, year-opening rites belong
    to adhika Chaitra rather than the following shuddha Chaitra.

    Source:
    https://www.transliteral.org/pages/z80421204850/view
    """
    chaitra_masas = {str(rule.masa), f"A{rule.masa}"}
    segments = []
    for record in sorted(records):
        if record[2] not in chaitra_masas:
            continue
        if (
            segments
            and record[0] == segments[-1][-1][0] + timedelta(days=1)
            and record[2:4] == segments[-1][-1][2:4]
        ):
            segments[-1].append(record)
        else:
            segments.append([record])

    occurrences = []
    for segment in segments:
        sunrise_matches = [
            record[0] for record in segment if record[1] == rule.tithi
        ]
        if sunrise_matches:
            occurrence_date = min(sunrise_matches)
        else:
            first_visible_shukla = next(
                (
                    record[0]
                    for record in segment
                    if record[1].startswith("S")
                ),
                None,
            )
            if first_visible_shukla is None:
                continue
            occurrence_date = first_visible_shukla - timedelta(days=1)
        occurrences.append(
            (
                occurrence_date,
                segment[0][3] or segment[0][2].startswith("A"),
            )
        )

    # Adhika Chaitra is immediately followed by nija Chaitra. Retain the
    # adhika year-opening occurrence and suppress only that paired nija one;
    # a later Chaitra belonging to another lunisolar year remains eligible.
    adhika_dates = [value for value, is_adhika in occurrences if is_adhika]
    return sorted(
        value
        for value, is_adhika in occurrences
        if is_adhika
        or not any(
            0 < (value - adhika_date).days <= 35
            for adhika_date in adhika_dates
        )
    )


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
    neither do, use the later day. Although Yugadi Shraddha is prescribed in
    both adhika and nija Vaishakha, this public Akshaya Tritiya marker belongs
    only to nija Vaishakha.

    Source:
    https://www.transliteral.org/pages/z80421210038/view
    """
    rule_records = records_for_rule(records, rule)
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


def select_narasimha_jayanti_dates(records, rule):
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
    If Purnima is skipped at sunrise, use the civil day containing it.

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
    if selected:
        return selected
    return select_udaya_vyapini_dates(records, rule, 15)


def select_naga_panchami_dates(records, rule):
    """Prefer Shashthi-yukta Panchami when it has three muhurtas.

    The later sunrise day is selected only when Panchami remains for at
    least three muhurtas (six ghatis). A shorter later Panchami is rejected
    in favor of the preceding Caturthi-viddha Panchami. If Panchami is
    skipped at sunrise, use the generic civil day containing the tithi.

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
    if selected:
        return selected
    return select_udaya_vyapini_dates(records, rule, 5)


def intervals_overlap(first_start, first_end, second_start, second_end):
    """Return whether two non-empty Julian-day intervals overlap."""
    return max(first_start, second_start) < min(first_end, second_end)


def locally_visible_eclipse_in_window(start_jd, end_jd, geopos):
    """Return whether a non-penumbral local eclipse overlaps the window."""
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
            and intervals_overlap(
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
        and intervals_overlap(
            start_jd,
            end_jd,
            solar_start,
            solar_end,
        )
    )


def eclipse_or_sankranti_in_window(start_jd, end_jd, geopos):
    """Return whether Dharma Sindhu's eight-yama window is contaminated."""
    start_rasi = int(panchanga.solar_longitude(start_jd) // 30)
    end_rasi = int(panchanga.solar_longitude(end_jd) // 30)
    if start_rasi != end_rasi:
        return True

    return locally_visible_eclipse_in_window(start_jd, end_jd, geopos)


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


def nakshatra_overlap_hours(start_jd, end_jd, target_nakshatra):
    """Measure one nakshatra's overlap with a short ritual-time window."""
    epsilon = 1e-10
    start_matches = (
        nakshatra_number_at(start_jd + epsilon) == target_nakshatra
    )
    end_matches = (
        nakshatra_number_at(end_jd - epsilon) == target_nakshatra
    )
    if start_matches and end_matches:
        return (end_jd - start_jd) * 24
    if not start_matches and not end_matches:
        return 0

    low, high = start_jd, end_jd
    for _ in range(50):
        middle = (low + high) / 2
        middle_matches = (
            nakshatra_number_at(middle) == target_nakshatra
        )
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


def has_nakshatra(start_jd, end_jd, nakshatra_number):
    for index in range(97):
        instant = start_jd + (end_jd - start_jd) * index / 96
        if nakshatra_number_at(instant) == nakshatra_number:
            return True
    return False


def nakshatra_overlaps(start_jd, end_jd, nakshatra_number):
    """Test a short ritual window without sampling over a boundary."""
    epsilon = 1e-10
    return (
        nakshatra_number_at(start_jd + epsilon) == nakshatra_number
        or nakshatra_number_at(end_jd - epsilon) == nakshatra_number
    )


def upakarma_date_is_contaminated(records_by_date, selected_date, geopos):
    """Check Dharma Sindhu's principal eight-yama eclipse/sankranti window."""
    selected_record = records_by_date[selected_date]
    previous_record = records_by_date.get(selected_date - timedelta(days=1))
    next_record = records_by_date.get(selected_date + timedelta(days=1))
    if previous_record is None or next_record is None:
        return False
    previous_midnight = (previous_record[6] + selected_record[5]) / 2
    following_midnight = (selected_record[6] + next_record[5]) / 2
    return eclipse_or_sankranti_in_window(
        previous_midnight,
        following_midnight,
        geopos,
    )


def select_rigveda_upakarma_dates(records, rule, geopos):
    """Resolve the Bahvrca/Rigveda Upakarma prescribed by Dharma Sindhu.

    The primary time is Shravana nakshatra in shuddha Shravana Shukla
    Paksha, and the rite is performed in Purvahna. This is intentionally
    distinct from Yajurveda Upakarma, whose primary time is Purnima.

    Dharma Sindhu gives detailed rules when Shravana crosses civil days:

    * If Shravana prevails at two consecutive sunrises, use the later day
      when at least three muhurtas (six ghatis, 2.4 hours) remain after its
      sunrise; otherwise use the earlier, fully occupied day.
    * If the first sunrise has Uttara Ashadha and Shravana prevails only at
      the following sunrise, use that following day when at least two
      muhurtas (four ghatis, 1.6 hours) remain.
    * A shorter following-day remainder is rejected as Uttara-Ashadha-
      viddha, and the secondary Panchami/Hasta times are used.

    Shravana is the primary option. If it is unavailable or contaminated,
    Shukla Panchami joined with Hasta is preferred; either Panchami or Hasta
    alone is also accepted. Panchami and Hasta are primarily sunrise-vyapini
    with at least three muhurtas remaining; a shorter sunrise remainder sends
    the observance to the preceding, purva-viddha day. Shravana-masa options
    precede the corresponding Bhadrapada fallbacks.

    Upakarma is not performed in adhika masa. An eclipse or sankranti in the
    principal eight-yama window—from the preceding local midnight through
    the following local midnight—contaminates a candidate. The stricter
    separately reported opinion about an eclipse/sankranti touching the
    selected nakshatra or tithi outside that window is not used, matching the
    existing Yajurveda resolver.

    Sources:
    https://www.transliteral.org/pages/z80422074617/view
    https://www.transliteral.org/pages/z80421215344/view
    Dharma Sindhu, second pariccheda, printed pp. 97-102:
    https://archive.org/details/dharma-sindhu-hindi
    """
    records_by_date = {record[0]: record for record in records}
    three_muhurtas = 6 * ONE_GHATI_HOURS
    two_muhurtas = 4 * ONE_GHATI_HOURS

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
            if nakshatra_number_at(sunrise_jd + 1e-10) != 22:
                continue
            candidates.append(
                (
                    record[0],
                    nakshatra_overlap_hours(
                        sunrise_jd,
                        sunrise_jd + three_muhurtas / 24,
                        22,
                    ),
                )
            )

        selected = []
        for group in group_consecutive_candidates(candidates):
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
                if nakshatra_number_at(sunrise_jd + 1e-10) != 13:
                    continue
                remainder = nakshatra_overlap_hours(
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
        if not upakarma_date_is_contaminated(
            records_by_date,
            selected_date,
            geopos,
        ):
            return [selected_date]

    # Prefer a Panchami-Hasta conjunction, then Panchami, then Hasta. The
    # same order is tried first in Shravana and then in Bhadrapada.
    for masa in (rule.masa, rule.masa + 1):
        candidates = month_records(masa)
        if masa != rule.masa:
            for selected_date in shravana_candidates(candidates):
                if not upakarma_date_is_contaminated(
                    records_by_date,
                    selected_date,
                    geopos,
                ):
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
                and not upakarma_date_is_contaminated(
                    records_by_date,
                    selected_date,
                    geopos,
                )
            ):
                return [selected_date]
    return []


def select_taittiriya_purnima_dates(records, masa):
    """Resolve each non-adhika Purnima using the Taittiriya hierarchy."""
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
            for group in group_consecutive_candidates(sunrise_candidates):
                if len(group) > 1:
                    selected_dates.append(group[0][0])
                    continue

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
                    purnima_start = (
                        intervals[0][0] if intervals else later_record[5]
                    )
                    first_muhurta_end = (
                        previous_record[5]
                        + 2 * ONE_GHATI_HOURS / 24
                    )
                    if (
                        purnima_start <= first_muhurta_end
                        or remainder < 4 * ONE_GHATI_HOURS
                    ):
                        selected_date = previous_date
                selected_dates.append(selected_date)
            continue

        # A sunrise-skipped Purnima belongs to the preceding sunrise day.
        for record in segment:
            following_record = by_date.get(
                record[0] + timedelta(days=1)
            )
            if following_record is None:
                continue
            if tithi_intervals(record[5], following_record[5], 15):
                selected_dates.append(record[0])
                break

    return selected_dates


def select_taittiriya_apastamba_upakarma_dates(records, rule, geopos):
    """Resolve Taittiriya-Apastamba Yajur Upakarma.

    Shravana Purnima is primary. If Purnima covers both sunrises, all
    Yajurvedins use the earlier day. For a split Purnima beginning after the
    first fixed muhurta, Taittiriyas use the later day when at least two
    muhurtas (four ghatis) remain after its sunrise; a shorter remainder uses
    the earlier day. If Purnima is skipped at sunrise, the civil day containing
    it is used. Adhika-masa Upakarma is forbidden.

    An eclipse or sankranti between the preceding and following local night
    midpoints contaminates the selected day. Apastambas then use Bhadrapada
    Purnima, resolved and validated by the same rules. If both dates are
    defective, no date is returned rather than silently retaining a defective
    date. This implements Dharma Sindhu's principal eight-yama opinion, not
    its separately reported stricter element-touch opinion.

    Sources:
    https://www.transliteral.org/pages/z80421215029/view
    https://www.transliteral.org/pages/z80421215344/view
    """
    by_date = {record[0]: record for record in records}
    selected_dates = select_taittiriya_purnima_dates(records, rule.masa)
    fallback_dates = select_taittiriya_purnima_dates(
        records,
        rule.masa + 1,
    )

    selected = []
    for selected_date in selected_dates:
        if not upakarma_date_is_contaminated(
            by_date,
            selected_date,
            geopos,
        ):
            selected.append(selected_date)
            continue

        fallback_date = next(
            (
                candidate
                for candidate in fallback_dates
                if (
                    selected_date < candidate
                    <= selected_date + timedelta(days=45)
                )
            ),
            None,
        )
        if (
            fallback_date is not None
            and not upakarma_date_is_contaminated(
                by_date,
                fallback_date,
                geopos,
            )
        ):
            selected.append(fallback_date)
    return selected


def select_janmashtami_dates(records, rule):
    """Resolve Vaishnava Janmashtami (non-Smarta).

    Vaishnavas strictly avoid observing Janmashtami on a day tainted by
    Saptami at sunrise (Saptami-viddha). The observance falls on the day
    where Ashtami is present at sunrise (Shuddha Ashtami), or Navami if
    Ashtami started after sunrise on the previous day.

    Sources:
    https://ramanuja.org/sri/BhaktiListArchives/Article?p=aug2001%2F0207.html
    """
    rule_records = records_for_rule(records, rule)
    by_date = {record[0]: record for record in records}
    
    candidates = []
    for record in rule_records:
        next_record = by_date.get(record[0] + timedelta(days=1))
        if next_record is None:
            continue
            
        # This full sunrise-to-sunrise window can contain a kshaya Ashtami
        # even when neither endpoint is Ashtami.
        intervals = tithi_intervals(record[5], next_record[5], 23)
        if intervals:
            # 22 is Saptami, 23 is Ashtami
            tithi_at_sunrise = tithi_number_at(record[5])
            if tithi_at_sunrise == 22:
                # Saptami at sunrise -> Saptami-viddha, reject.
                # We must observe on the next day.
                next_date = record[0] + timedelta(days=1)
                if next_date not in candidates:
                    candidates.append(next_date)
            else:
                # Shuddha Ashtami (Ashtami at sunrise)
                if record[0] not in candidates:
                    candidates.append(record[0])
                
    selected = []
    for group in group_consecutive_candidates([(date, 1) for date in candidates]):
        # If multiple dates (e.g. Ashtami spans two sunrises),
        # pick the first one.
        selected.append(group[0][0])
        
    return selected


def select_smarta_janmashtami_dates(records, rule):
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


def select_vijaya_dasami_dates(records, rule):
    """Resolve Aparahna-vyapini Vijaya Dashami with Shravana exceptions.

    If only one day has Dashami in Aparahna, that day is normally used. If
    both or neither do, Shravana in exactly one Aparahna selects that date;
    otherwise the earlier date is used. One exception moves an
    earlier-Aparahna decision to the later date when sunrise Dashami remains
    there for at least three muhurtas and Shravana occupies its Aparahna.

    Source:
    https://www.transliteral.org/pages/z80501062120/view
    https://archive.org/details/in.ernet.dli.2015.513461/page/n100/mode/1up
    """
    rule_records = sorted(records_for_rule(records, rule))
    details_by_date = {}
    for record in rule_records:
        sunrise_jd, sunset_jd = record[5:7]
        day_length = sunset_jd - sunrise_jd
        aparahna = (
            sunrise_jd + day_length * 3 / 5,
            sunrise_jd + day_length * 4 / 5,
        )
        details_by_date[record[0]] = {
            "record": record,
            "dashami_in_daytime": (
                tithi_overlap_hours(sunrise_jd, sunset_jd, 10) > 0
            ),
            "dashami_in_aparahna": (
                tithi_overlap_hours(*aparahna, 10) > 0
            ),
            "shravana_in_aparahna": nakshatra_overlaps(
                *aparahna,
                22,
            ),
        }

    daytime_candidates = [
        (civil_date, details["record"][4])
        for civil_date, details in details_by_date.items()
        if details["dashami_in_daytime"]
    ]
    selected = []
    for group in group_consecutive_candidates(daytime_candidates):
        group_dates = [candidate[0] for candidate in group]
        aparahna_dates = [
            civil_date
            for civil_date in group_dates
            if details_by_date[civil_date]["dashami_in_aparahna"]
        ]
        shravana_dates = [
            civil_date
            for civil_date in group_dates
            if details_by_date[civil_date]["shravana_in_aparahna"]
        ]

        if len(aparahna_dates) == 1:
            selected_date = aparahna_dates[0]
            if selected_date == group_dates[0] and len(group_dates) > 1:
                later_date = group_dates[-1]
                later_record = details_by_date[later_date]["record"]
                if (
                    later_record[1] == rule.tithi
                    and later_record[4] >= SIX_GHATI_HOURS
                    and later_date in shravana_dates
                ):
                    selected_date = later_date
            selected.append(selected_date)
        elif len(shravana_dates) == 1:
            selected.append(shravana_dates[0])
        else:
            selected.append(group_dates[0])
    return selected


def select_bali_padyami_dates(records, rule):
    """Select Kartika Pratipada reaching the ninth daytime muhurta.

    Bali Puja, Govardhana Puja, and related rites use the sunrise day only
    when Pratipada reaches the ninth daytime muhurta. If it ends within the
    first eight muhurtas, Dharma Sindhu assigns Bali Puja to the preceding,
    Amavasya-viddha Pratipada day. Morning abhyanga and dyuta have a separate
    one-muhurta rule and do not control this festival marker.

    Source:
    https://www.transliteral.org/pages/z80505062407/view
    """
    rule_records = records_for_rule(records, rule)
    sunrise_candidates = [
        record for record in rule_records if record[1] == rule.tithi
    ]
    selected = []
    for group in group_consecutive_candidates(
        [(record[0], 1) for record in sunrise_candidates]
    ):
        candidate_date = group[-1][0]
        record = next(
            value for value in sunrise_candidates if value[0] == candidate_date
        )
        sunrise_jd, sunset_jd = record[5:7]
        ninth_muhurta_start = sunrise_jd + (
            sunset_jd - sunrise_jd
        ) * 8 / 15
        selected.append(
            candidate_date
            if tithi_number_at(ninth_muhurta_start) == 1
            else candidate_date - timedelta(days=1)
        )
    if selected:
        return selected

    first_visible = next(
        (
            record[0]
            for record in rule_records
            if record[1].startswith("S")
        ),
        None,
    )
    return [first_visible - timedelta(days=1)] if first_visible else []


def select_vasanta_panchami_dates(records, rule):
    """Select Magha Panchami by Purvahna occupancy.

    The later day is used only when it alone contains Panchami during
    Purvahna. In every other case—including both days or neither day—the
    earlier day is selected.

    Source:
    https://www.transliteral.org/pages/z80513003421/view
    """
    rule_records = records_for_rule(records, rule)
    candidates = []
    for record in rule_records:
        sunrise_jd, sunset_jd = record[5:7]
        overlap = tithi_overlap_hours(
            sunrise_jd,
            sunrise_jd + (sunset_jd - sunrise_jd) / 2,
            5,
        )
        if overlap > 0:
            candidates.append((record[0], overlap))
    if candidates:
        return [
            group[0][0]
            for group in group_consecutive_candidates(candidates)
        ]

    daytime_candidates = [
        (record[0], 1)
        for record in rule_records
        if tithi_overlap_hours(record[5], record[6], 5) > 0
    ]
    return [
        group[0][0]
        for group in group_consecutive_candidates(daytime_candidates)
    ]


def select_ratha_saptami_dates(records, rule):
    """Select Arunodaya-vyapini Magha Saptami.

    If Saptami occupies Arunodaya on two days, the earlier day is used. When
    Saptami is lost before the following Arunodaya and only about one ghati
    of Shashthi remains, Dharma Sindhu accepts the earlier Shashthi-yukta
    Saptami for the Arunodaya bath.

    Source:
    https://www.transliteral.org/pages/z80513004113/view
    """
    rule_records = records_for_rule(records, rule)
    candidates = []
    for record in rule_records:
        overlap = tithi_overlap_hours(
            record[5] - ARUNODAYA_HOURS / 24,
            record[5],
            7,
        )
        if overlap > 0:
            candidates.append((record[0], overlap))
    if candidates:
        return [
            group[0][0]
            for group in group_consecutive_candidates(candidates)
        ]

    daytime_candidates = [
        (record[0], 1)
        for record in rule_records
        if tithi_overlap_hours(record[5], record[6], 7) > 0
    ]
    return [
        group[0][0]
        for group in group_consecutive_candidates(daytime_candidates)
    ]


def select_kama_dahana_dates(records, rule):
    """Select Kama Dahana (Phalguna Purnima during Pradosha).

    The government and many South Indian calendars observe Holi on the day
    of Kama Dahana (Holi), which is Pradosha-vyapini Phalguna Purnima.
    If Purnima occupies Pradosha on both days, the later day is used.
    
    Source:
    https://www.kamakoti.org/kamakoti/dharmasindhu/bookview.php?chapnum=13
    """
    candidates = []
    for record in records_for_rule(records, rule):
        civil_date, _, _, _, _, _, sunset_jd = record
        overlap = tithi_overlap_hours(
            sunset_jd,
            sunset_jd + PRADOSHA_HOURS / 24,
            15,
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


def select_maha_shivaratri_dates(records, rule):
    """Resolve Nishitha-vyapini Magha Krishna Caturdashi.

    Nishitha is the eighth muhurta of the local night. If only one Nishitha
    contains Caturdashi, use that day; if neither does, use the later day.
    For two Nishithas Dharma Sindhu records disagreement: Hemadri/Kaustubha
    choose the earlier day, while Madhava, Nirnaya Sindhu,
    Purushartha-cintamani and others choose the later. This implementation
    follows the recorded majority/later-day opinion, except that a wholly
    covered Nishitha defeats a merely partial one.

    Source:
    https://www.transliteral.org/pages/z80513005728/view
    """
    rule_records = records_for_rule(records, rule)
    by_date = {record[0]: record for record in records}
    candidates = []
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
            29,
        )
        if overlap > 0:
            candidates.append(
                (
                    record[0],
                    overlap,
                    (nishitha_end - nishitha_start) * 24,
                )
            )

    selected = []
    for group in group_consecutive_candidates(
        [(date, overlap) for date, overlap, _ in candidates]
    ):
        if len(group) == 1:
            selected.append(group[0][0])
            continue
        details = {
            date: (overlap, length)
            for date, overlap, length in candidates
            if date in {candidate[0] for candidate in group}
        }
        first_date, later_date = group[0][0], group[-1][0]
        first_full = details[first_date][0] >= details[first_date][1] - 1e-5
        later_full = details[later_date][0] >= details[later_date][1] - 1e-5
        selected.append(first_date if first_full and not later_full else later_date)
    if selected:
        return selected

    daytime_candidates = [
        (record[0], 1)
        for record in rule_records
        if tithi_overlap_hours(record[5], record[6], 29) > 0
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
    eclipse and sankranti do not prohibit Raksha Bandhan. If Purnima is skipped
    at sunrise, use its civil day subject to the same Bhadra-free ritual window.

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
    selected_dates = []
    for group in group_consecutive_candidates(candidates):
        later_date, remainder = group[-1]
        selected_date = (
            later_date
            if remainder > SIX_GHATI_HOURS
            else later_date - timedelta(days=1)
        )
        selected_dates.append(selected_date)

    if not selected_dates:
        kshaya_candidates = []
        for record in records_for_rule(records, rule):
            following_record = by_date.get(
                record[0] + timedelta(days=1)
            )
            if following_record is None:
                continue
            if tithi_intervals(record[5], following_record[5], 15):
                kshaya_candidates.append((record[0], 1))
        selected_dates = [
            group[0][0]
            for group in group_consecutive_candidates(kshaya_candidates)
        ]

    selected = []
    for selected_date in selected_dates:
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


def generic_udaya_occurrences(records, target_tithi):
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
        if not tithi_intervals(record[5], following_record[5], target_tithi):
            continue

        # Amanta masa changes at Shukla Pratipada. For a skipped Shukla
        # tithi, the following sunrise therefore owns the new masa metadata;
        # for a skipped Krishna tithi, the preceding sunrise retains it.
        masa_record = following_record if target_tithi <= 15 else record
        occurrence = (record[0], masa_record[2], masa_record[3])
        if occurrence[0] not in sunrise_dates:
            occurrences.append(occurrence)

    return sorted(set(occurrences))


def select_generic_udaya_festival_dates(records, rule):
    """Apply the experimental sunrise-ownership policy to a plain tithi."""
    target_tithi = plain_tithi_number(rule.tithi)
    if target_tithi is None:
        raise ValueError(f"{rule.name} does not have a plain tithi rule")

    occurrences = eligible_generic_occurrences(
        generic_udaya_occurrences(records, target_tithi),
        rule,
    )
    return [occurrence[0] for occurrence in occurrences]


def eligible_generic_occurrences(occurrences, rule):
    """Filter generic occurrences by masa and the calendar's adhika policy."""
    occurrences = [
        occurrence
        for occurrence in occurrences
        if occurrence[1] in {str(rule.masa), f"A{rule.masa}"}
    ]
    if rule.number == UGADI_NUMBER and any(
        occurrence[2] for occurrence in occurrences
    ):
        occurrences = [
            occurrence for occurrence in occurrences if occurrence[2]
        ]
    else:
        occurrences = [
            occurrence for occurrence in occurrences if not occurrence[2]
        ]
    return occurrences


def generic_kala_for_rule(rule):
    """Return the lay ritual period assigned by the generic-kala experiment."""
    return GENERIC_KALA_BY_FESTIVAL.get(rule.number, SUNRISE_KALA)


def generic_kala_window(
    record,
    following_record,
    kala,
    preceding_record=None,
):
    """Return a point or one-third local day/night window for ``kala``.

    Purvahna, Madhyahna, and Aparahna are consecutive thirds from sunrise
    through sunset. Sayahna and Ratri are the first two thirds after that
    sunset. Purvodaya is the final night-third immediately before the labelled
    date's sunrise. It is an experimental lay label, not Dharma Sindhu's
    technical four-ghati Arunodaya.
    """
    sunrise_jd, sunset_jd = record[5:7]
    if kala == SUNRISE_KALA:
        return sunrise_jd, sunrise_jd
    if kala == SUNSET_KALA:
        return sunset_jd, sunset_jd

    if kala in {PURVAHNA_KALA, MADHYAHNA_KALA, APARAHNA_KALA}:
        boundaries = [
            sunrise_jd + (sunset_jd - sunrise_jd) * part / 3
            for part in range(4)
        ]
        index = {
            PURVAHNA_KALA: 0,
            MADHYAHNA_KALA: 1,
            APARAHNA_KALA: 2,
        }[kala]
        return boundaries[index], boundaries[index + 1]

    if kala == PURVODAYA_KALA:
        if preceding_record is None:
            raise ValueError("purvodaya requires the preceding sunset")
        preceding_sunset_jd = preceding_record[6]
        night_third = (sunrise_jd - preceding_sunset_jd) / 3
        return sunrise_jd - night_third, sunrise_jd

    if kala in {SAYAHNA_KALA, RATRI_KALA}:
        if following_record is None:
            raise ValueError(f"{kala} requires the following sunrise")
        following_sunrise_jd = following_record[5]
        boundaries = [
            sunset_jd + (following_sunrise_jd - sunset_jd) * part / 3
            for part in range(4)
        ]
        index = {
            SAYAHNA_KALA: 0,
            RATRI_KALA: 1,
        }[kala]
        return boundaries[index], boundaries[index + 1]

    raise ValueError(f"Unknown generic kala: {kala}")


def generic_kala_score(kala_window, target_interval, civil_date):
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


def select_generic_kala_festival_dates(records, rule):
    """Resolve a plain tithi using one kala mapping and one common tie-break.

    The date maximizing proportional tithi coverage of the assigned kala is
    selected. Equal coverage prefers the kala midpoint nearest the tithi
    midpoint; an exact final tie uses the earlier civil date. If neither date
    overlaps the kala, midpoint proximity acts as the missing-window fallback.
    """
    target_tithi = plain_tithi_number(rule.tithi)
    if target_tithi is None:
        raise ValueError(f"{rule.name} does not have a plain tithi rule")

    records = sorted(records)
    records_by_date = {record[0]: record for record in records}
    occurrences = eligible_generic_occurrences(
        generic_udaya_occurrences(records, target_tithi),
        rule,
    )
    kala = generic_kala_for_rule(rule)
    if kala == SUNRISE_KALA:
        return [occurrence[0] for occurrence in occurrences]

    selected = []
    for owner_date, _, _ in occurrences:
        owner_record = records_by_date.get(owner_date)
        if owner_record is None:
            continue
        scan_start = owner_record[5] - 1.25
        scan_end = owner_record[5] + 2.25
        intervals = tithi_intervals(scan_start, scan_end, target_tithi)
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
            if (
                kala in {SAYAHNA_KALA, RATRI_KALA}
                and following_record is None
            ):
                continue
            if kala == PURVODAYA_KALA and preceding_record is None:
                continue
            window = generic_kala_window(
                record,
                following_record,
                kala,
                preceding_record,
            )
            candidates.append(
                (
                    generic_kala_score(
                        window,
                        target_interval,
                        civil_date,
                    ),
                    civil_date,
                )
            )
        if candidates:
            selected.append(max(candidates)[1])
    return sorted(set(selected))


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


def select_vaikuntha_ekadashi_dates(months, month_data, records=None):
    """Select the Dharma-sindhu Vaishnava fast in solar Dhanur masa.

    Vaikuntha (Mukkoti) Ekadashi is a regional/Sri-Vaishnava observance, and
    no separately named Vaikuntha-Ekadashi rule was found in Dharma Sindhu's
    Margashirsha or Pausha sections. Its calendrical definition is the Shukla
    Ekadashi fast that falls in the sidereal solar month of Dhanur. It can
    therefore belong to lunar Margashirsha or Pausha.

    The festival marker reuses this calendar's existing pure Dharma Sindhu
    Vaishnava Ekadashi resolver. Consequently Dashami at the four-ghati
    Arunodaya, Ekadashi/Dvadashi adhikya, and a resulting shift of the fast
    to Dvadashi are handled identically to every teal-underlined Ekadashi.
    No ISKCON/Gaudiya Mahadvadashi categories are introduced.

    The solar test is made at local sunrise on the resolved fast day using
    panchanga.raasi(); Dhanur is rasi 9. Sunrise is appropriate because the
    Ekadashi upavasa day runs from local sunrise, and a shifted Vaishnava
    fast may have Dvadashi rather than S11 at that sunrise. The candidate
    must still be in Shukla Paksha and lunar masa 9 or 10. Adhika lunar masa
    is not rejected: the controlling definition is solar Dhanur, not the
    shuddha/adhika label.

    No occurrence is manufactured when neither candidate falls in Dhanur,
    and all qualifying occurrences are retained. Hence a Gregorian year can
    contain zero, one, or two dates, while an arbitrary 13-month PDF range
    may also contain portions of two Dhanur seasons.

    Sources:
    Dharma Sindhu Vaishnava Ekadashi decision:
    https://www.transliteral.org/pages/z80422042154/view
    https://www.transliteral.org/pages/z80422042403/view
    Regional Dhanur-masa definition:
    https://www.drikpanchang.com/ekadashis/vaikuntha/vaikuntha-ekadashi-date-time.html
    https://www.sadagopan.org/ebook/pdf/Vratams.pdf
    """
    if records is None:
        records = collect_records(months, month_data)
    records_by_date = {record[0]: record for record in records}
    upavasa_dates = resolve_dharma_sindhu_vaishnava_ekadashi_dates(
        months,
        month_data,
    )
    selected = []
    for upavasa_date in upavasa_dates:
        record = records_by_date.get(upavasa_date)
        if record is None:
            continue
        _, tithi, masa, _, _, sunrise_jd, _ = record
        if (
            masa in {"9", "10"}
            and tithi.startswith("S")
            and panchanga.raasi(sunrise_jd) == 9
        ):
            selected.append(upavasa_date)
    return selected


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


def select_gowri_habba_dates(records, rule):
    """Resolve Bhadrapada S3 Gowri Habba by Dharma Sindhu's Gauri rule.

    The South Indian Svarna-Gowri Vrata/Gowri Habba is identified with the
    Bhadrapada Shukla Tritiya Gauri (Haritalika) vrata discussed by Dharma
    Sindhu. Its date rule deliberately favors the later, Chaturthi-yukta
    Tritiya and strongly rejects a Dwitiya-yukta observance:

    * If Tritiya prevails at sunrise on one day, use that day.
    * If a vriddhi Tritiya prevails at two consecutive sunrises, use the
      later day even when only a minute remnant remains. Dharma Sindhu says
      to reject even a full sixty-ghati Tritiya on the earlier day because
      conjunction with Chaturthi gives the later observance greater merit.
    * Only in the kshaya case, when Tritiya falls wholly between two
      sunrises and no Chaturthi-yukta sunrise day exists, use the earlier
      civil day on which sunrise still has Dwitiya.

    Thus "one day before Ganesa Caturthi" is the usual consequence, not the
    controlling rule. Each vrata is independently resolved from its own
    tithi rule, which also handles skipped and repeated tithis correctly.
    Adhika Bhadrapada is excluded.

    Sources:
    https://www.transliteral.org/pages/z80503220901/view
    https://www.transliteral.org/pages/z80422023507/view
    Dharma Sindhu, first pariccheda, Tritiya-nirnaya, printed pp. 20-21:
    https://archive.org/details/dharma-sindhu-hindi
    """
    rule_records = records_for_rule(records, rule)
    sunrise_candidates = [
        (record[0], record[4])
        for record in rule_records
        if record[1] == rule.tithi
    ]
    if sunrise_candidates:
        return [
            group[-1][0]
            for group in group_consecutive_candidates(sunrise_candidates)
        ]

    # Kshaya Tritiya: S3 begins after the S2 sunrise and ends before the
    # following sunrise, which therefore already has S4.
    for earlier, later in zip(rule_records, rule_records[1:]):
        if (
            later[0] == earlier[0] + timedelta(days=1)
            and earlier[1] == "S2"
            and later[1] == "S4"
        ):
            return [earlier[0]]
    return []


def select_udaya_vyapini_dates(records, rule, tithi_number):
    """Apply this calendar's generic udaya-marker convention.

    A tithi at one sunrise uses that date; a vriddhi tithi uses its first
    sunrise; and a kshaya tithi uses the civil day containing it. This is a
    deterministic marker policy, not a universal Dharma Sindhu rule:
    observances such as Ekadashi have their own later-sunrise hierarchy.
    """
    # First-sunrise vriddhi precedents include Dharma Sindhu's Ugadi rule
    # and the sourced Ayudha Puja results for 2000 and 2034. Ekadashi is
    # intentionally different because its fasting rules seek a later,
    # Dashami-free sunrise rather than a generic civil-day marker.
    rule_records = sorted(records_for_rule(records, rule))
    sunrise_candidates = [
        (record[0], record[4])
        for record in rule_records
        if record[1] == rule.tithi
    ]
    if sunrise_candidates:
        return [
            group[0][0]
            for group in group_consecutive_candidates(sunrise_candidates)
        ]

    records_by_date = {record[0]: record for record in records}
    for record in rule_records:
        following_record = records_by_date.get(
            record[0] + timedelta(days=1)
        )
        if following_record is None:
            continue
        if tithi_intervals(
            record[5],
            following_record[5],
            tithi_number,
        ):
            return [record[0]]
    return []


def select_varamahalakshmi_dates(records):
    """Select the last Friday strictly before amanta Shravana Purnima."""
    shravana_records = sorted(
        record
        for record in records
        if record[2] == "5" and not record[3]
    )
    purnima_candidates = [
        (record[0], record[4])
        for record in shravana_records
        if record[1] == "S15"
    ]
    anchors = [
        group[0][0]
        for group in group_consecutive_candidates(purnima_candidates)
    ]

    if not anchors:
        records_by_date = {record[0]: record for record in records}
        for record in shravana_records:
            following_record = records_by_date.get(
                record[0] + timedelta(days=1)
            )
            if following_record is None:
                continue
            if tithi_intervals(record[5], following_record[5], 15):
                anchors.append(record[0])
                break

    selected = []
    for purnima_date in anchors:
        vrata_date = purnima_date - timedelta(days=1)
        while vrata_date.weekday() != calendar.FRIDAY:
            vrata_date -= timedelta(days=1)
        selected.append(vrata_date)
    return selected


def select_ayudha_puja_dates(records, rule):
    """Select shuddha Ashvina S9 by the South Indian sunrise convention.

    Ayudha Puja (also Shastra Puja, Astra Puja, or Khande Navami) is treated
    here as a regional observance distinct from Dharma Sindhu's Mahanavami
    puja/upavasa rule. The festival belongs to the civil day on which Shukla
    Navami prevails at local sunrise (udaya-vyapini).

    A long, or vriddhi, Navami can prevail at two consecutive sunrises. In
    that case the earlier civil day (purva) is selected. It contains the
    fuller Navami daytime; the later day contains only Navami's ending
    portion. Two useful regression examples from Drik Panchang are:

    * 2000: Navami ran Oct 6 05:48 to Oct 7 08:25 in New Delhi, covering both
      sunrises; Ayudha Puja was Friday, Oct 6.
    * 2034: Navami ran Oct 21 06:04 to Oct 22 06:34 in New Delhi, again
      covering both sunrises; Ayudha Puja was Saturday, Oct 21.

    The advertised "Ayudha Puja Vijaya Muhurat" does not select the civil
    date. It is the recommended eleventh daytime muhurta on the date already
    selected by the sunrise rule. This distinction matters: in ordinary
    years that window can begin after astronomical Navami has ended, while
    the sunrise-defined festival day remains Ayudha Puja.

    If Navami is skipped at sunrise, the observance falls on the civil day
    whose sunrise-to-sunrise span contains Navami. Drik Panchang's Helsinki
    2005 result is a regression example: Navami ran from Oct 11 08:59 to
    Oct 12 06:43, and Ayudha Puja was Oct 11.

    Sources:
    https://www.drikpanchang.com/navratri/durga-puja/ayudha-puja-date-time.html
    https://www.drikpanchang.com/navratri/durga-puja/ayudha-puja-date-time.html?year=2000
    https://www.drikpanchang.com/navratri/durga-puja/ayudha-puja-date-time.html?year=2034
    https://www.drikpanchang.com/navratri/durga-puja/ayudha-puja-date-time.html?year=2005&geoname-id=658225
    https://vishwakosh.marathi.gov.in/22879/
    """
    return select_udaya_vyapini_dates(records, rule, 9)


def select_vasavi_jayanti_dates(records, rule):
    """Apply generic sunrise, vriddhi, and kshaya handling to Vaishakha S10.

    No Dharma Sindhu rule is known for this community festival. Its calendar
    date is resolved by the documented generic udaya-marker convention.
    """
    return select_udaya_vyapini_dates(records, rule, 10)


def select_vasavi_atmarpana_dates(records, rule):
    """Apply the generic udaya-marker convention to Magha Shukla Dwitiya."""
    return select_udaya_vyapini_dates(records, rule, 2)


def select_vsn_jayanti_dates(records, rule):
    """Apply generic udaya handling to the Magha Shukla Ekadashi marker.

    This is a commemorative Jayanti marker, not an Ekadashi fast, so it does
    not reuse the later-sunrise fasting hierarchy.
    """
    return select_udaya_vyapini_dates(records, rule, 11)


def select_gita_jayanti_dates(records, rule):
    """Apply generic udaya handling to Margashirsha Shukla Ekadashi.

    This is a commemorative Jayanti marker, not an Ekadashi fast, so it does
    not reuse the later-sunrise fasting hierarchy.
    """
    return select_udaya_vyapini_dates(records, rule, 11)


def select_mahanavami_puja_dates(records, rule):
    """Apply Dharma Sindhu's Mahanavami puja/upavasa decision.

    An Ashtami-viddha Navami is used only when Navami occupies the final
    three muhurtas (six fixed ghatis) before sunset. A shorter evening
    Navami belongs to the following date. Otherwise the first
    sunrise-vyapini Navami is used; a Navami skipped at sunrise also falls
    on the following date.

    This marker excludes Navami Mahabali, which prefers Dashami-viddha
    Navami, and Sandhi Puja, which belongs to the exact Ashtami-Navami
    junction.

    Sources:
    https://www.transliteral.org/pages/z80501061410/view
    https://archive.org/details/in.ernet.dli.2015.513461/page/n98/mode/1up
    """
    rule_records = sorted(records_for_rule(records, rule))
    evening_candidates = []
    for record in rule_records:
        sunset_jd = record[6]
        overlap = tithi_overlap_hours(
            sunset_jd - SIX_GHATI_HOURS / 24,
            sunset_jd,
            9,
        )
        if overlap >= SIX_GHATI_HOURS - 1e-8:
            evening_candidates.append((record[0], overlap))
    if evening_candidates:
        return [
            group[0][0]
            for group in group_consecutive_candidates(evening_candidates)
        ]

    sunrise_candidates = [
        (record[0], record[4])
        for record in rule_records
        if record[1] == rule.tithi
    ]
    if sunrise_candidates:
        return [
            group[0][0]
            for group in group_consecutive_candidates(sunrise_candidates)
        ]

    records_by_date = {record[0]: record for record in records}
    for record in rule_records:
        following_date = record[0] + timedelta(days=1)
        following_record = records_by_date.get(following_date)
        if following_record is None:
            continue
        if tithi_intervals(record[5], following_record[5], 9):
            return [following_date]
    return []


def select_dasara_dates(records, rule):
    """Select the generic Udaya-vyapini Dashami public observance."""
    return select_udaya_vyapini_dates(records, rule, 10)


def select_naraka_chaturdashi_dates(records, rule, moonrise_jds=None):
    """Select Dharma Sindhu's moonrise-vyapini Naraka Chaturdashi.

    The principal bath is after the pre-dawn moonrise. If Caturdashi
    occupies both successive moonrises, the earlier civil date is used.
    When it occupies neither, a Caturdashi portion between the first
    moonrise and sunrise belongs to the earlier date; otherwise the bath
    belongs to the later moonrise, even if Amavasya then prevails.

    If a physical moonrise is unavailable, the prescribed secondary
    pre-sunrise and morning periods provide a location-safe fallback.

    Sources:
    https://www.transliteral.org/pages/z80505062049/view
    https://archive.org/details/in.ernet.dli.2015.383127/page/n193/mode/2up
    """
    rule_records = sorted(records_for_rule(records, rule))
    moonrise_jds = moonrise_jds or {}
    moonrise_records = [
        (record, moonrise_jds.get(record[0]))
        for record in rule_records
        if moonrise_jds.get(record[0]) is not None
    ]

    moonrise_candidates = [
        (record[0], 1)
        for record, moonrise_jd in moonrise_records
        if tithi_number_at(moonrise_jd) == 29
    ]
    if moonrise_candidates:
        return [
            group[0][0]
            for group in group_consecutive_candidates(moonrise_candidates)
        ]

    records_by_date = {record[0]: record for record in rule_records}
    for record, first_moonrise_jd in moonrise_records:
        following_date = record[0] + timedelta(days=1)
        following_record = records_by_date.get(following_date)
        following_moonrise_jd = moonrise_jds.get(following_date)
        if following_record is None or following_moonrise_jd is None:
            continue
        if not tithi_intervals(first_moonrise_jd, following_moonrise_jd, 29):
            continue

        sunrise_jd = record[5]
        if (
            first_moonrise_jd < sunrise_jd
            and tithi_overlap_hours(first_moonrise_jd, sunrise_jd, 29) > 0
        ):
            return [record[0]]
        return [following_date]

    secondary_candidates = []
    for record in rule_records:
        sunrise_jd = record[5]
        overlap = tithi_overlap_hours(
            sunrise_jd - ARUNODAYA_HOURS / 24,
            sunrise_jd,
            29,
        )
        if overlap > 0:
            secondary_candidates.append((record[0], overlap))
    if secondary_candidates:
        return [
            group[0][0]
            for group in group_consecutive_candidates(secondary_candidates)
        ]

    morning_candidates = [
        record[0]
        for record in rule_records
        if tithi_overlap_hours(record[5], record[6], 29) > 0
    ]
    return morning_candidates[:1]


def select_dhana_trayodashi_dates(records, rule):
    """Apply Dharma Sindhu's Pradosha-vyapini Trayodashi rule for Dhana Trayodashi.

    Dhana Trayodashi is assigned to the local evening on which Krishna Trayodashi
    occupies at least one ghati of Pradosha. When both consecutive evenings
    qualify, the later date is selected; when only the earlier evening
    qualifies, that date is retained. If neither Pradosha contains Trayodashi,
    the later date is used, including when Trayodashi is skipped at sunrise.

    Sources:
    https://nepaljyotish.org/en/blog/dharmasindhu-vrata-nirnaya/
    https://archive.org/details/in.ernet.dli.2015.383127/page/n193/mode/2up
    """
    rule_records = sorted(records_for_rule(records, rule))
    candidates = []
    for record in rule_records:
        civil_date, _, _, _, _, _, sunset_jd = record
        overlap = tithi_overlap_hours(
            sunset_jd,
            sunset_jd + PRADOSHA_HOURS / 24,
            28, # K13
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
    if selected:
        return selected

    sunrise_candidates = [
        (record[0], record[4])
        for record in rule_records
        if record[1] == rule.tithi
    ]
    if sunrise_candidates:
        return [
            group[-1][0]
            for group in group_consecutive_candidates(sunrise_candidates)
        ]

    records_by_date = {record[0]: record for record in rule_records}
    for record in rule_records:
        following_date = record[0] + timedelta(days=1)
        following_record = records_by_date.get(following_date)
        if following_record is None:
            continue
        if tithi_intervals(record[5], following_record[5], 28):
            return [following_date]
    return []


def select_dhanvantari_jayanti_dates(records, rule):
    """Select generic Udaya-vyapini K13 for Dhanvantari Jayanti."""
    return select_udaya_vyapini_dates(records, rule, 28)


def select_makara_sankranti_dates(records, rule):
    """Resolve Makara Sankranti date.

    If the Sun enters Makara (sidereal longitude 270 degrees) before local sunset,
    the festival is observed on that day. If it enters after sunset, it is
    observed on the following day.

    Source:
    https://www.kamakoti.org/kamakoti/dharmasindhu/bookview.php?chapnum=11
    """
    jan_records = [r for r in records if r[0].month == 1]
    if not jan_records:
        return []

    years = sorted(list(set(r[0].year for r in jan_records)))
    selected = []
    for year in years:
        jd_start = panchanga.gregorian_to_jd(panchanga.Date(year, 1, 13))
        jd_end = panchanga.gregorian_to_jd(panchanga.Date(year, 1, 16))

        low = jd_start
        high = jd_end
        for _ in range(50):
            mid = (low + high) / 2
            lon = panchanga.solar_longitude(mid)
            if 250 < lon < 270:
                low = mid
            else:
                high = mid
        sankranti_jd = mid

        year_records = [r for r in jan_records if r[0].year == year]
        for record in year_records:
            civil_date, _, _, _, _, _, sunset_jd = record
            if sunset_jd > sankranti_jd:
                selected.append(civil_date)
                break

    return selected


def select_deepavali_dates(records, rule):
    """Apply Dharma Sindhu's Pradosha-vyapini Amavasya rule.

    Lakshmi Puja is assigned to the local evening on which Amavasya occupies
    at least one ghati (24 minutes) of Pradosha. When both consecutive
    evenings qualify, the later, Pratipada-yukta date is selected; when only
    the earlier evening qualifies, that date is retained. If neither
    Pradosha contains Amavasya, Dharma Sindhu assigns Lakshmi Puja to the
    later date, including when Amavasya is skipped at sunrise.

    Sources:
    https://www.kamakoti.org/kamakoti/dharmasindhu/bookview.php?chapnum=8
    https://www.drikpanchang.com/diwali/diwali-puja-calendar.html
    https://archive.org/details/in.ernet.dli.2015.383127/page/n193/mode/2up
    """
    rule_records = sorted(records_for_rule(records, rule))
    candidates = []
    for record in rule_records:
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
    if selected:
        return selected

    sunrise_candidates = [
        (record[0], record[4])
        for record in rule_records
        if record[1] == rule.tithi
    ]
    if sunrise_candidates:
        return [
            group[-1][0]
            for group in group_consecutive_candidates(sunrise_candidates)
        ]

    records_by_date = {record[0]: record for record in records}
    for record in rule_records:
        following_date = record[0] + timedelta(days=1)
        following_record = records_by_date.get(following_date)
        if following_record is None:
            continue
        if tithi_intervals(record[5], following_record[5], 30):
            return [following_date]
    return []


def select_mahalaya_amavasya_dates(records, rule):
    """Apply Dharma Sindhu's Aparahna-vyapini rule for Mahalaya Amavasya.

    Mahalaya (Sarvapitri) Amavasya is the Amavasya of Bhadrapada (Krishna 15).
    The Shraddha is performed when the tithi prevails during the Aparahna kala
    (the fourth fifth of the daytime). If it prevails in Aparahna on two days,
    the day with the greater overlap is selected. If neither Aparahna contains
    Amavasya, the earlier civil day containing the tithi is used.

    Sources:
    https://www.transliteral.org/pages/z130523053523/view
    http://hindupanchang.blogspot.com/2008/03/
    https://www.onlinejyotish.com/astrology-tools/shraddha-tithi.php
    """
    candidates = []
    for record in records_for_rule(records, rule):
        civil_date, _, _, _, _, sunrise_jd, sunset_jd = record
        day_length = sunset_jd - sunrise_jd
        aparahna_start = sunrise_jd + day_length * 3 / 5
        aparahna_end = sunrise_jd + day_length * 4 / 5
        overlap = tithi_overlap_hours(
            aparahna_start,
            aparahna_end,
            30, # K15
        )
        if overlap > 0:
            candidates.append((civil_date, overlap))

    selected = []
    for group in group_consecutive_candidates(candidates):
        selected.append(max(group, key=lambda candidate: candidate[1])[0])
    if selected:
        return selected

    rule_records = sorted(records_for_rule(records, rule))
    records_by_date = {record[0]: record for record in records}
    for record in rule_records:
        following_record = records_by_date.get(
            record[0] + timedelta(days=1)
        )
        if following_record is None:
            continue
        if tithi_intervals(record[5], following_record[5], 30):
            return [record[0]]
    return []


def select_durga_ashtami_puja_dates(records, rule):
    """Apply Dharma Sindhu's Maha Ashtami civil-date hierarchy.

    A complete sunrise-to-sunrise Ashtami has first priority. Otherwise a
    Navami-yukta sunrise Ashtami is used only when at least one ghati
    remains. A shorter remnant, an Ashtami skipped at sunrise, or a
    following Navami skipped at sunrise sends the festival to the earlier,
    Saptami-yukta civil date.

    Sources:
    https://www.transliteral.org/pages/z80501061410/view
    https://www.transliteral.org/pages/z80504211648/view
    """
    rule_records = sorted(records_for_rule(records, rule))
    records_by_date = {record[0]: record for record in records}
    touched_dates = []
    complete_dates = []

    for record in rule_records:
        following_record = records_by_date.get(
            record[0] + timedelta(days=1)
        )
        if following_record is None:
            continue
        sunrise_jd = record[5]
        following_sunrise_jd = following_record[5]
        intervals = tithi_intervals(
            sunrise_jd,
            following_sunrise_jd,
            8,
        )
        if not intervals:
            continue
        touched_dates.append(record[0])
        if (
            intervals[0][0] <= sunrise_jd + 1e-10
            and intervals[-1][1] >= following_sunrise_jd - 1e-10
        ):
            complete_dates.append(record[0])

    if complete_dates:
        return [complete_dates[0]]
    if not touched_dates:
        return []

    if not any(record[1] == "S9" for record in rule_records):
        return [touched_dates[0]]

    sunrise_candidates = [
        record for record in rule_records if record[1] == rule.tithi
    ]
    if not sunrise_candidates:
        return [touched_dates[0]]

    later_record = sunrise_candidates[-1]
    if (
        tithi_number_at(
            later_record[5] + ONE_GHATI_HOURS / 24
        )
        == 8
    ):
        return [later_record[0]]
    return [touched_dates[0]]


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


def select_durga_ashtami_observance_dates(records, rule):
    """Resolve Durga Ashtami, including a generic kshaya fallback."""
    candidates = [
        (record[0], record[4])
        for record in records_for_rule(records, rule)
        if record[1] == rule.tithi
    ]
    selected = select_durga_ashtami_dates(candidates)
    if selected:
        return selected
    return select_udaya_vyapini_dates(records, rule, 8)


def resolve_festivals(
    months,
    month_data,
    festival_policy=TRADITIONAL_FESTIVAL_POLICY,
    *,
    context_months=None,
    context_data=None,
    geopos=None,
):
    """Resolve festivals against daily panchanga and ritual-time windows.

    Each raw daily record is:
    day, tithi, nakshatra, masa, is_adhika, tithi-hours-after-sunrise,
    sunrise UTC Julian day, sunset UTC Julian day, yoga,
    moonrise UTC Julian day.
    """
    if festival_policy not in FESTIVAL_POLICIES:
        raise ValueError(f"Unknown festival policy: {festival_policy}")
    if (context_months is None) != (context_data is None):
        raise ValueError("context_months and context_data must be supplied together")

    target_records = collect_records(months, month_data)
    target_dates = {record[0] for record in target_records}
    if (
        festival_policy
        in {GENERIC_UDAYA_FESTIVAL_POLICY, GENERIC_KALA_FESTIVAL_POLICY}
        and context_months is not None
    ):
        resolution_months = context_months
        resolution_data = context_data
    else:
        resolution_months = months
        resolution_data = month_data
    records = collect_records(resolution_months, resolution_data)
    moonrise_jds = collect_moonrise_jds(
        resolution_months,
        resolution_data,
    )

    dates_by_number = {}
    names_by_number = {}
    for rule in FESTIVAL_RULES:
        if (
            festival_policy == GENERIC_UDAYA_FESTIVAL_POLICY
            and plain_tithi_number(rule.tithi) is not None
        ):
            matches = select_generic_udaya_festival_dates(records, rule)
        elif (
            festival_policy == GENERIC_KALA_FESTIVAL_POLICY
            and plain_tithi_number(rule.tithi) is not None
        ):
            matches = select_generic_kala_festival_dates(records, rule)
        elif rule.number == UGADI_NUMBER:
            matches = select_ugadi_dates(records, rule)
        elif rule.number == RAMA_NAVAMI_NUMBER:
            matches = select_rama_navami_dates(records, rule)
        elif rule.number == AKSAYA_TRTIYA_NUMBER:
            matches = select_aksaya_trtiya_dates(records, rule)
        elif rule.number == VASAVI_JAYANTI_NUMBER:
            matches = select_vasavi_jayanti_dates(records, rule)
        elif rule.number == NARASIMHA_JAYANTI_NUMBER:
            matches = select_narasimha_jayanti_dates(records, rule)
        elif rule.number == GURU_PURNIMA_NUMBER:
            matches = select_guru_purnima_dates(records, rule)
        elif rule.number == NAGA_PANCHAMI_NUMBER:
            matches = select_naga_panchami_dates(records, rule)
        elif rule.number == RIG_UPAKARMA_NUMBER:
            if geopos is None:
                raise ValueError(
                    "traditional Rig Upakarma requires a geographic position"
                )
            matches = select_rigveda_upakarma_dates(records, rule, geopos)
        elif rule.number == YAJUR_UPAKARMA_NUMBER:
            if geopos is None:
                raise ValueError(
                    "traditional Yajur Upakarma requires a geographic position"
                )
            matches = select_taittiriya_apastamba_upakarma_dates(
                records,
                rule,
                geopos,
            )
        elif rule.number == RAKSHA_BANDHAN_NUMBER:
            matches = select_raksha_bandhan_dates(records, rule)
        elif rule.number == JANMASHTAMI_NUMBER:
            matches = select_janmashtami_dates(records, rule)
        elif rule.number == VIJAYA_DASAMI_NUMBER:
            matches = select_vijaya_dasami_dates(records, rule)
        elif rule.number == BALI_PADYAMI_NUMBER:
            matches = select_bali_padyami_dates(records, rule)
        elif rule.number == GITA_JAYANTI_NUMBER:
            matches = select_gita_jayanti_dates(records, rule)
        elif rule.number == VAIKUNTHA_EKADASHI_NUMBER:
            matches = select_vaikuntha_ekadashi_dates(
                resolution_months,
                resolution_data,
                records,
            )
        elif rule.number == VASANTA_PANCHAMI_NUMBER:
            matches = select_vasanta_panchami_dates(records, rule)
        elif rule.number == RATHA_SAPTAMI_NUMBER:
            matches = select_ratha_saptami_dates(records, rule)
        elif rule.number == KAMA_DAHANA_NUMBER:
            matches = select_kama_dahana_dates(records, rule)
        elif rule.number == MAHA_SHIVARATRI_NUMBER:
            matches = select_maha_shivaratri_dates(records, rule)
        elif rule.number == DHANA_TRAYODASHI_NUMBER:
            matches = select_dhana_trayodashi_dates(records, rule)
        elif rule.number == MAKARA_SANKRANTI_NUMBER:
            matches = select_makara_sankranti_dates(records, rule)
        elif rule.number == VASAVI_ATMARPANA_NUMBER:
            matches = select_vasavi_atmarpana_dates(records, rule)
        elif rule.number == VSN_JAYANTI_NUMBER:
            matches = select_vsn_jayanti_dates(records, rule)
        elif rule.number == DHANVANTARI_JAYANTI_NUMBER:
            matches = select_dhanvantari_jayanti_dates(records, rule)
        elif rule.number == MAHALAYA_AMAVASYA_NUMBER:
            matches = select_mahalaya_amavasya_dates(records, rule)
        elif rule.number == MAHANAVAMI_PUJA_NUMBER:
            matches = select_mahanavami_puja_dates(records, rule)
        elif rule.number == DASARA_NUMBER:
            matches = select_dasara_dates(records, rule)
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
            matches = select_durga_ashtami_observance_dates(records, rule)
        elif rule.number == DURGA_ASHTAMI_PUJA_NUMBER:
            matches = select_durga_ashtami_puja_dates(records, rule)
        elif rule.number == GOWRI_HABBA_NUMBER:
            matches = select_gowri_habba_dates(records, rule)
        elif rule.number == AYUDHA_PUJA_NUMBER:
            matches = select_ayudha_puja_dates(records, rule)
        elif rule.number == NARAKA_CHATURDASHI_NUMBER:
            matches = select_naraka_chaturdashi_dates(
                records,
                rule,
                moonrise_jds,
            )
        elif rule.number == DEEPAVALI_NUMBER:
            matches = select_deepavali_dates(records, rule)
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
        if festival_policy in {
            GENERIC_UDAYA_FESTIVAL_POLICY,
            GENERIC_KALA_FESTIVAL_POLICY,
        }:
            matches = [
                civil_date for civil_date in matches if civil_date in target_dates
            ]
        if not matches and not rule.allow_empty:
            raise RuntimeError(f"No calendar date found for {rule.name}")
        dates_by_number[rule.number] = matches
        names_by_number[rule.number] = (
            GENERIC_KALA_NAME_BY_FESTIVAL.get(rule.number, rule.name)
            if festival_policy == GENERIC_KALA_FESTIVAL_POLICY
            else rule.name
        )

    varamahalakshmi_dates = select_varamahalakshmi_dates(records)
    if festival_policy in {
        GENERIC_UDAYA_FESTIVAL_POLICY,
        GENERIC_KALA_FESTIVAL_POLICY,
    }:
        varamahalakshmi_dates = [
            civil_date
            for civil_date in varamahalakshmi_dates
            if civil_date in target_dates
        ]
    dates_by_number[VARAMAHALAKSHMI_NUMBER] = varamahalakshmi_dates
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
