"""Festival definitions and observance-date rules for the PDF calendar."""

import calendar
from datetime import timedelta

import panchanga

from _festival_rules import astronomy as _astronomy
from _festival_rules import ekadashi as _ekadashi
from _festival_rules import generic as _generic
from _festival_rules import records as _records
from _festival_rules import upakarma as _upakarma
from _festival_rules.catalog import *
from _festival_rules.config import *
from _festival_rules.model import *

format_festival_dates = _records.format_festival_dates
group_consecutive_candidates = _records.group_consecutive_candidates
records_for_rule = _records.records_for_rule
collect_records = _records.collect_records
collect_moonrise_jds = _records.collect_moonrise_jds
plain_tithi_number = _records.plain_tithi_number


def tithi_number_at(jd):
    return _astronomy.tithi_number_at(jd, panchanga)


def tithi_overlap_hours(start_jd, end_jd, target_tithi):
    return _astronomy.tithi_overlap_hours(
        start_jd,
        end_jd,
        target_tithi,
        tithi_number_at,
    )


intervals_overlap = _astronomy.intervals_overlap


def locally_visible_eclipse_in_window(start_jd, end_jd, geopos):
    return _astronomy.locally_visible_eclipse_in_window(
        start_jd,
        end_jd,
        geopos,
        panchanga=panchanga,
        overlap_checker=intervals_overlap,
    )


def eclipse_or_sankranti_in_window(start_jd, end_jd, geopos):
    return _astronomy.eclipse_or_sankranti_in_window(
        start_jd,
        end_jd,
        geopos,
        panchanga=panchanga,
        eclipse_checker=locally_visible_eclipse_in_window,
    )


def karana_index_at(jd):
    return _astronomy.karana_index_at(jd, panchanga)


def is_vishti_at(jd):
    return _astronomy.is_vishti_at(jd, karana_index_at)


def has_bhadra_free_purnima(start_jd, end_jd):
    return _astronomy.has_bhadra_free_purnima(
        start_jd,
        end_jd,
        tithi_number_at,
        is_vishti_at,
    )


def nakshatra_number_at(jd):
    return _astronomy.nakshatra_number_at(jd, panchanga)


def nakshatra_overlap_hours(start_jd, end_jd, target_nakshatra):
    return _astronomy.nakshatra_overlap_hours(
        start_jd,
        end_jd,
        target_nakshatra,
        nakshatra_number_at,
    )


def has_tithi_nakshatra(
    start_jd,
    end_jd,
    tithi_number,
    nakshatra_number,
):
    return _astronomy.has_tithi_nakshatra(
        start_jd,
        end_jd,
        tithi_number,
        nakshatra_number,
        tithi_at=tithi_number_at,
        nakshatra_at=nakshatra_number_at,
    )


def has_nakshatra(start_jd, end_jd, nakshatra_number):
    return _astronomy.has_nakshatra(
        start_jd,
        end_jd,
        nakshatra_number,
        nakshatra_number_at,
    )


def nakshatra_overlaps(start_jd, end_jd, nakshatra_number):
    return _astronomy.nakshatra_overlaps(
        start_jd,
        end_jd,
        nakshatra_number,
        nakshatra_number_at,
    )


def tithi_intervals(start_jd, end_jd, target_tithi):
    return _astronomy.tithi_intervals(
        start_jd,
        end_jd,
        target_tithi,
        tithi_number_at,
    )


def generic_udaya_occurrences(records, target_tithi):
    return _records.generic_udaya_occurrences(
        records,
        target_tithi,
        plain_tithi_number=plain_tithi_number,
        interval_finder=tithi_intervals,
    )


def eligible_generic_occurrences(occurrences, rule):
    return _records.eligible_generic_occurrences(
        occurrences,
        rule,
        UGADI_NUMBER,
    )


def upakarma_date_is_contaminated(records_by_date, selected_date, geopos):
    return _upakarma.date_is_contaminated(
        records_by_date,
        selected_date,
        geopos,
        contamination_checker=eclipse_or_sankranti_in_window,
    )


def select_rigveda_upakarma_dates(records, rule, geopos):
    return _upakarma.select_rigveda_dates(
        records,
        rule,
        geopos,
        one_ghati_hours=ONE_GHATI_HOURS,
        nakshatra_at=nakshatra_number_at,
        nakshatra_overlap=nakshatra_overlap_hours,
        group_candidates=group_consecutive_candidates,
        is_contaminated=upakarma_date_is_contaminated,
    )


def select_taittiriya_purnima_dates(records, masa):
    return _upakarma.select_taittiriya_purnima_dates(
        records,
        masa,
        one_ghati_hours=ONE_GHATI_HOURS,
        group_candidates=group_consecutive_candidates,
        interval_finder=tithi_intervals,
    )


def select_taittiriya_apastamba_upakarma_dates(records, rule, geopos):
    return _upakarma.select_taittiriya_apastamba_dates(
        records,
        rule,
        geopos,
        select_purnima=select_taittiriya_purnima_dates,
        is_contaminated=upakarma_date_is_contaminated,
    )


def resolve_dharma_sindhu_vaishnava_ekadashi_dates(months, month_data):
    return _ekadashi.resolve_vaishnava_dates(
        months,
        month_data,
        collect_records=collect_records,
        interval_finder=tithi_intervals,
        tithi_at=tithi_number_at,
        arunodaya_hours=ARUNODAYA_HOURS,
    )


def select_vaikuntha_ekadashi_dates(months, month_data, records=None):
    return _ekadashi.select_vaikuntha_dates(
        months,
        month_data,
        records,
        collect_records=collect_records,
        resolve_upavasa=resolve_dharma_sindhu_vaishnava_ekadashi_dates,
        raasi_at=panchanga.raasi,
    )


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


def select_generic_udaya_festival_dates(records, rule):
    """Apply the experimental sunrise-ownership policy to a plain tithi."""
    return _generic.select_udaya_festival_dates(
        records,
        rule,
        plain_tithi_number=plain_tithi_number,
        occurrence_finder=generic_udaya_occurrences,
        eligibility_filter=eligible_generic_occurrences,
    )


def select_generic_midpoint_festival_dates(records, rule):
    """Assign each eligible tithi to the sunrise-day containing its midpoint."""
    return _generic.select_midpoint_festival_dates(
        records,
        rule,
        plain_tithi_number=plain_tithi_number,
        occurrence_finder=generic_udaya_occurrences,
        eligibility_filter=eligible_generic_occurrences,
        interval_finder=tithi_intervals,
    )


generic_kala_for_rule = _generic.kala_for_rule
generic_kala_window = _generic.kala_window
generic_kala_score = _generic.kala_score


def select_generic_kala_festival_dates(records, rule):
    """Resolve a plain tithi through the private Generic Kala engine."""
    return _generic.select_kala_festival_dates(
        records,
        rule,
        plain_tithi_number=plain_tithi_number,
        occurrence_finder=generic_udaya_occurrences,
        eligibility_filter=eligible_generic_occurrences,
        interval_finder=tithi_intervals,
        kala_for_rule=generic_kala_for_rule,
        kala_window=generic_kala_window,
        kala_score=generic_kala_score,
    )


generic_anchor_for_rule = _generic.anchor_for_rule
generic_anchor_jd = _generic.anchor_jd


def select_generic_anchor_festival_dates(records, rule):
    """Resolve a plain tithi through the private Generic Anchor engine."""
    return _generic.select_anchor_festival_dates(
        records,
        rule,
        plain_tithi_number=plain_tithi_number,
        occurrence_finder=generic_udaya_occurrences,
        eligibility_filter=eligible_generic_occurrences,
        interval_finder=tithi_intervals,
        anchor_for_rule=generic_anchor_for_rule,
        anchor_jd=generic_anchor_jd,
    )


def generic_kala_date_is_valid(
    records_by_date,
    selected_date,
    overlay,
    geopos,
):
    """Apply one post-selection constraint without changing kala scoring."""
    if overlay.validator == UPAKARMA_CONTAMINATION_VALIDATOR:
        if geopos is None:
            raise ValueError(
                "Upakarma validity requires a geographic position"
            )
        return not upakarma_date_is_contaminated(
            records_by_date,
            selected_date,
            geopos,
        )
    raise ValueError(f"Unknown Generic Kala validator: {overlay.validator}")


def select_valid_generic_kala_festival_dates(
    records,
    rule,
    geopos=None,
):
    """Resolve by kala, then reject defects and retry with the same policy."""
    return _generic.select_valid_kala_festival_dates(
        records,
        rule,
        geopos,
        selector=select_generic_kala_festival_dates,
        validator=generic_kala_date_is_valid,
    )


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
        in {
            GENERIC_UDAYA_FESTIVAL_POLICY,
            GENERIC_MIDPOINT_FESTIVAL_POLICY,
            GENERIC_KALA_FESTIVAL_POLICY,
            GENERIC_ANCHOR_FESTIVAL_POLICY,
        }
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
            festival_policy == GENERIC_MIDPOINT_FESTIVAL_POLICY
            and plain_tithi_number(rule.tithi) is not None
        ):
            matches = select_generic_midpoint_festival_dates(records, rule)
        elif (
            festival_policy == GENERIC_KALA_FESTIVAL_POLICY
            and plain_tithi_number(rule.tithi) is not None
        ):
            matches = select_valid_generic_kala_festival_dates(
                records,
                rule,
                geopos,
            )
        elif (
            festival_policy == GENERIC_ANCHOR_FESTIVAL_POLICY
            and plain_tithi_number(rule.tithi) is not None
        ):
            matches = select_generic_anchor_festival_dates(records, rule)
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
            GENERIC_MIDPOINT_FESTIVAL_POLICY,
            GENERIC_KALA_FESTIVAL_POLICY,
            GENERIC_ANCHOR_FESTIVAL_POLICY,
        }:
            matches = [
                civil_date for civil_date in matches if civil_date in target_dates
            ]
        if not matches and not rule.allow_empty:
            raise RuntimeError(f"No calendar date found for {rule.name}")
        dates_by_number[rule.number] = matches
        if festival_policy == GENERIC_KALA_FESTIVAL_POLICY:
            name = GENERIC_KALA_NAME_BY_FESTIVAL.get(rule.number, rule.name)
        elif festival_policy == GENERIC_ANCHOR_FESTIVAL_POLICY:
            name = GENERIC_ANCHOR_NAME_BY_FESTIVAL.get(
                rule.number,
                rule.name,
            )
        else:
            name = rule.name
        names_by_number[rule.number] = name

    varamahalakshmi_dates = select_varamahalakshmi_dates(records)
    if festival_policy in {
        GENERIC_UDAYA_FESTIVAL_POLICY,
        GENERIC_MIDPOINT_FESTIVAL_POLICY,
        GENERIC_KALA_FESTIVAL_POLICY,
        GENERIC_ANCHOR_FESTIVAL_POLICY,
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
