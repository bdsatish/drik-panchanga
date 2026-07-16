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
        "Rig upakarma",
        5,
        "Shravana nakshatra",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80422074617/view",
    ),
    FestivalRule(
        10,
        "Yajur upakarma",
        5,
        "S15",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80421215029/view",
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
        "Gowri Habba",
        6,
        "S3",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80503220901/view",
    ),
    FestivalRule(14, "Ganesa caturthi", 6, "S4"),
    FestivalRule(
        15,
        "Mahalaya Amavasya",
        6,
        "K15",
        "dharmasindhu",
        "http://hindupanchang.blogspot.com/2008/03/",
    ),
    FestivalRule(16, "Durgastami", 7, "S8"),
    # This is the regional South Indian/Khande-Navami observance, rather than
    # Dharma Sindhu's distinct Mahanavami puja/upavasa decision.
    FestivalRule(
        17,
        "Ayudha puja",
        7,
        "S9",
        "regional",
        (
            "https://www.drikpanchang.com/navratri/durga-puja/"
            "ayudha-puja-date-time.html"
        ),
    ),
    FestivalRule(
        18,
        "Vijaya dasami",
        7,
        "S10",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80501062120/view",
    ),
    FestivalRule(
        19,
        "Dhana Trayodashi",
        7,
        "K13",
        "dharmasindhu",
        "https://nepaljyotish.org/en/blog/dharmasindhu-vrata-nirnaya/",
    ),
    FestivalRule(20, "Naraka Chaturdashi", 7, "K14"),
    FestivalRule(21, "Deepavali", 7, "K15"),
    FestivalRule(
        22,
        "Bali padyami",
        8,
        "S1",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80505062407/view",
    ),
    # No Gita-Jayanti observance was found in Dharma Sindhu's Margashirsha
    # section. Preserve the supplied community date provisionally.
    FestivalRule(23, "Gita jayanti", 9, "S11", "unresolved"),
    FestivalRule(
        24,
        "Vaikuntha Ekadashi",
        9,
        "Dhanur-masa S11",
        "regional",
        (
            "https://www.drikpanchang.com/ekadashis/vaikuntha/"
            "vaikuntha-ekadashi-date-time.html"
        ),
    ),
    FestivalRule(
        25,
        "Makara Sankranti",
        0,
        "Solar",
        "dharmasindhu",
        "https://www.kamakoti.org/kamakoti/dharmasindhu/bookview.php?chapnum=11",
    ),
    # No Vasavi Atmarpana observance was found in Dharma Sindhu's Magha
    # section. Preserve the supplied community date provisionally.
    FestivalRule(26, "Vasavi atmarpana", 11, "S2", "unresolved"),
    FestivalRule(
        27,
        "Vasanta pancami",
        11,
        "S5",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80513003421/view",
    ),
    FestivalRule(
        28,
        "Ratha saptami",
        11,
        "S7",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80513004113/view",
    ),
    # Vishnu-Sahasranama Jayanthi was not found in Dharma Sindhu; Bhishma
    # Ashtami is present but is a different observance.
    FestivalRule(29, "VSN jayanthi", 11, "S11", "unresolved"),
    FestivalRule(
        30,
        "Maha Shivaratri",
        11,
        "K14",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80513005728/view",
    ),
    FestivalRule(
        31,
        "Holi",
        12,
        "K1",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80505120438/view",
    ),
    FestivalRule(
        32,
        "Dhanvantari Jayanthi",
        7,
        "K13",
        "regional",
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
RIG_UPAKARMA_NUMBER = 9
YAJUR_UPAKARMA_NUMBER = 10
RAKSHA_BANDHAN_NUMBER = 11
JANMASHTAMI_NUMBER = 12
GOWRI_HABBA_NUMBER = 13
GANESHA_CATURTHI_NUMBER = 14
MAHALAYA_AMAVASYA_NUMBER = 15
DURGA_ASHTAMI_NUMBER = 16
AYUDHA_PUJA_NUMBER = 17
VIJAYA_DASAMI_NUMBER = 18
DHANA_TRAYODASHI_NUMBER = 19
NARAKA_CHATURDASHI_NUMBER = 20
DEEPAVALI_NUMBER = 21
BALI_PADYAMI_NUMBER = 22
GITA_JAYANTI_NUMBER = 23
VAIKUNTHA_EKADASHI_NUMBER = 24
MAKARA_SANKRANTI_NUMBER = 25
VASAVI_ATMARPANA_NUMBER = 26
VASANTA_PANCHAMI_NUMBER = 27
RATHA_SAPTAMI_NUMBER = 28
VSN_JAYANTHI_NUMBER = 29
MAHA_SHIVARATRI_NUMBER = 30
HOLI_NUMBER = 31
DHANVANTARI_JAYANTHI_NUMBER = 32
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


def upakarma_date_is_contaminated(records_by_date, selected_date):
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
    )


def select_rigveda_upakarma_dates(records, rule):
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
                )
            ):
                return [selected_date]
    return []


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
            
        # Check if Ashtami (23) is active between this sunrise and next sunrise
        overlap = tithi_overlap_hours(record[5], next_record[5], 23)
        if overlap > 0:
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

    If Dashami occupies Aparahna on both days, the earlier day is used; if
    only one day qualifies, that day is used. Shravana on exactly one of two
    qualifying days gives that day priority. When neither Aparahna contains
    Dashami, the earlier day remains normal, except that a later Dashami of
    at least three muhurtas joined to Shravana in Aparahna is selected.

    Source:
    https://www.transliteral.org/pages/z80501062120/view
    """
    rule_records = records_for_rule(records, rule)
    aparahna_candidates = []
    shravana_dates = set()
    for record in rule_records:
        sunrise_jd, sunset_jd = record[5:7]
        day_length = sunset_jd - sunrise_jd
        aparahna = (
            sunrise_jd + day_length * 3 / 5,
            sunrise_jd + day_length * 4 / 5,
        )
        if tithi_overlap_hours(*aparahna, 10) > 0:
            aparahna_candidates.append((record[0], 1))
        if has_nakshatra(*aparahna, 22):
            shravana_dates.add(record[0])

    if aparahna_candidates:
        selected = []
        for group in group_consecutive_candidates(aparahna_candidates):
            with_shravana = [
                candidate[0]
                for candidate in group
                if candidate[0] in shravana_dates
            ]
            selected.append(
                with_shravana[0]
                if len(with_shravana) == 1
                else group[0][0]
            )
        return selected

    daytime_candidates = [
        (record[0], record[4])
        for record in rule_records
        if tithi_overlap_hours(record[5], record[6], 10) > 0
    ]
    selected = []
    for group in group_consecutive_candidates(daytime_candidates):
        later_date, later_remainder = group[-1]
        if (
            later_remainder >= SIX_GHATI_HOURS
            and later_date in shravana_dates
        ):
            selected.append(later_date)
        else:
            selected.append(group[0][0])
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


def select_holi_dates(records, rule):
    """Select the color-festival morning after Holika Dahana.

    The listed Holi marker denotes Dharma Sindhu's Vasantotsava/color
    observance on Phalguna Krishna Pratipada morning, not the preceding
    Purnima-Pradosha Holika Dahana. If Pratipada occupies both mornings, the
    earlier morning is selected.

    Sources:
    https://www.transliteral.org/pages/z80505120438/view
    https://kamakoti.org/kamakoti/dharmasindhu/bookview.php?chapnum=13
    """
    rule_records = records_for_rule(records, rule)
    morning_candidates = []
    for record in rule_records:
        sunrise_jd, sunset_jd = record[5:7]
        if tithi_overlap_hours(
            sunrise_jd,
            sunrise_jd + (sunset_jd - sunrise_jd) / 2,
            16,
        ) > 0:
            morning_candidates.append((record[0], 1))
    if morning_candidates:
        return [
            group[0][0]
            for group in group_consecutive_candidates(morning_candidates)
        ]

    daytime_candidates = [
        (record[0], 1)
        for record in rule_records
        if tithi_overlap_hours(record[5], record[6], 16) > 0
    ]
    return [
        group[0][0]
        for group in group_consecutive_candidates(daytime_candidates)
    ]


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
            _yoga,
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

    This selector intentionally handles only the sourced udaya-vyapini and
    vriddhi rules. A kshaya Navami, present at neither sunrise, needs a
    separately sourced fallback and must not be silently guessed here.

    Sources:
    https://www.drikpanchang.com/navratri/durga-puja/ayudha-puja-date-time.html
    https://www.drikpanchang.com/navratri/durga-puja/ayudha-puja-date-time.html?year=2000
    https://www.drikpanchang.com/navratri/durga-puja/ayudha-puja-date-time.html?year=2034
    https://vishwakosh.marathi.gov.in/22879/
    """
    sunrise_candidates = [
        (record[0], record[4])
        for record in records_for_rule(records, rule)
        if record[1] == rule.tithi
    ]
    return [
        group[0][0]
        for group in group_consecutive_candidates(sunrise_candidates)
    ]


def select_naraka_chaturdashi_dates(records, rule):
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


def select_dhana_trayodashi_dates(records, rule):
    """Apply Dharma Sindhu's Pradosha-vyapini Trayodashi rule for Dhana Trayodashi.

    Dhana Trayodashi is assigned to the local evening on which Krishna Trayodashi
    occupies at least one ghati of Pradosha. When both consecutive evenings
    qualify, the later date is selected; when only the earlier evening
    qualifies, that date is retained.

    Sources:
    https://nepaljyotish.org/en/blog/dharmasindhu-vrata-nirnaya/
    """
    candidates = []
    for record in records_for_rule(records, rule):
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
    return selected


def select_dhanvantari_jayanthi_dates(records, rule):
    """Select Udaya-vyapini Krishna Trayodashi for Dhanvantari Jayanthi.

    The festival belongs to the civil day on which Krishna Trayodashi
    prevails at local sunrise.
    """
    sunrise_candidates = [
        (record[0], record[4])
        for record in records_for_rule(records, rule)
        if record[1] == rule.tithi
    ]
    return [
        group[0][0]
        for group in group_consecutive_candidates(sunrise_candidates)
    ]


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


def select_mahalaya_amavasya_dates(records, rule):
    """Apply Dharma Sindhu's Aparahna-vyapini rule for Mahalaya Amavasya.

    Mahalaya (Sarvapitri) Amavasya is the Amavasya of Bhadrapada (Krishna 15).
    The Shraddha is performed when the tithi prevails during the Aparahna kala
    (the fourth fifth of the daytime). If it prevails in Aparahna on two days,
    the day with the greater overlap is selected.

    Sources:
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
    sunrise UTC Julian day, sunset UTC Julian day, yoga.
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
        elif rule.number == RIG_UPAKARMA_NUMBER:
            matches = select_rigveda_upakarma_dates(records, rule)
        elif rule.number == YAJUR_UPAKARMA_NUMBER:
            matches = select_taittiriya_apastamba_upakarma_dates(records, rule)
        elif rule.number == RAKSHA_BANDHAN_NUMBER:
            matches = select_raksha_bandhan_dates(records, rule)
        elif rule.number == JANMASHTAMI_NUMBER:
            matches = select_janmashtami_dates(records, rule)
        elif rule.number == VIJAYA_DASAMI_NUMBER:
            matches = select_vijaya_dasami_dates(records, rule)
        elif rule.number == BALI_PADYAMI_NUMBER:
            matches = select_bali_padyami_dates(records, rule)
        elif rule.number == VAIKUNTHA_EKADASHI_NUMBER:
            matches = select_vaikuntha_ekadashi_dates(
                months,
                month_data,
                records,
            )
        elif rule.number == VASANTA_PANCHAMI_NUMBER:
            matches = select_vasanta_panchami_dates(records, rule)
        elif rule.number == RATHA_SAPTAMI_NUMBER:
            matches = select_ratha_saptami_dates(records, rule)
        elif rule.number == HOLI_NUMBER:
            matches = select_holi_dates(records, rule)
        elif rule.number == MAHA_SHIVARATRI_NUMBER:
            matches = select_maha_shivaratri_dates(records, rule)
        elif rule.number == DHANA_TRAYODASHI_NUMBER:
            matches = select_dhana_trayodashi_dates(records, rule)
        elif rule.number == MAKARA_SANKRANTI_NUMBER:
            matches = select_makara_sankranti_dates(records, rule)
        elif rule.number == DHANVANTARI_JAYANTHI_NUMBER:
            matches = select_dhanvantari_jayanthi_dates(records, rule)
        elif rule.number == MAHALAYA_AMAVASYA_NUMBER:
            matches = select_mahalaya_amavasya_dates(records, rule)
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
        elif rule.number == GOWRI_HABBA_NUMBER:
            matches = select_gowri_habba_dates(records, rule)
        elif rule.number == AYUDHA_PUJA_NUMBER:
            matches = select_ayudha_puja_dates(records, rule)
        elif rule.number == NARAKA_CHATURDASHI_NUMBER:
            matches = select_naraka_chaturdashi_dates(records, rule)
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
        if not matches:
            raise RuntimeError(f"No calendar date found for {rule.name}")
        dates_by_number[rule.number] = matches
        names_by_number[rule.number] = rule.name

    vrata_dates = []
    for sravana_purnima_date in dates_by_number[YAJUR_UPAKARMA_NUMBER]:
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
