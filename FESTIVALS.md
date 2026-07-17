# Festival Date Policies

The calendar provides three festival-date policies, ordered here from the
simplest and most uniform to the most detailed:

1. `generic-udaya`
2. `generic-kala`
3. `traditional` (Dharma-Sindhu-oriented)

The traditional policy remains the default. The two generic policies are
experimental alternatives for studying how much of traditional festival
reckoning can be reproduced with a small common rule set.

Select a policy when generating a calendar:

```bash
python generate_panchanga_calendar.py \
  --city Helsinki \
  --start 2026-03 \
  --festival-policy generic-kala
```

Experimental PDFs identify their policy in their metadata, page heading, and
default filename.

## 1. Generic Udaya

CLI value: `generic-udaya`

This is the least complex policy. Every plain masa-and-tithi festival uses
sunrise ownership without considering the festival's ritual time.

For each occurrence of the target tithi:

- If the tithi prevails at one sunrise, use that civil date.
- If it prevails at two consecutive sunrises (vriddhi), use the first sunrise.
- If it misses sunrise entirely (kshaya), use the civil day whose
  sunrise-to-sunrise span contains the tithi.
- Exclude adhika-masa occurrences by default.
- Ugadi is the deliberate exception: when Chaitra is adhika, the year-opening
  occurrence belongs to adhika Chaitra.

This policy is deterministic and easy to explain, but it cannot represent
festivals whose decisive ritual occurs at noon, sunset, midnight, or another
part of the day.

Rules that are not plain masa-and-tithi markers—such as solar Sankranti,
Vaikuntha Ekadashi, Rig Upakarma, and Varamahalakshmi Vrata—continue to use
their dedicated selectors.

## 2. Generic Kala

CLI value: `generic-kala`

This policy retains a common resolver but assigns a simple ritual period to
each festival type. It is more expressive than Generic Udaya without
introducing festival-specific competition rules.

### Lay kala divisions

The actual local interval from sunrise to sunset is divided into three equal
parts:

1. Purvahna
2. Madhyahna
3. Aparahna

The local night is treated as three corresponding parts:

1. Sayahna: first third after sunset
2. Ratri: middle third after sunset
3. Purvodaya: final third immediately before the labelled date's sunrise

Sunrise and sunset are also available as exact points.

These thirds vary with local day and night length. They are each four hours
(ten ghatis) only when day and night are both twelve hours long.

`Purvodaya` is an experimental lay label. It must not be confused with Dharma
Sindhu's technical four-ghati Arunodaya. Likewise, Ratri is a broad night
third, not the narrower technical Nishitha.

### Festival assignments

| Kala | Festivals |
|---|---|
| Purvahna | Rig Upakarma, Vasanta Panchami |
| Madhyahna | Rama Navami, Akshaya Tritiya, Ganesha Chaturthi, Bali Padyami |
| Aparahna | Raksha Bandhan, Mahalaya Amavasya, Mahanavami (Puja), Vijayadashami (Puja) |
| Sunset | Narasimha Jayanti |
| Sayahna | Dhana Trayodashi, Deepavali, Kama Dahana (Holi) |
| Ratri | Janmashtami, Maha Shivaratri |
| Purvodaya | Naraka Chaturdashi, Ratha Saptami |
| Sunrise | Every otherwise unclassified plain-tithi festival |

Rig Upakarma is nakshatra-based rather than a plain-tithi festival. Its
dedicated selector is therefore retained, although Purvahna is its conceptual
assignment.

Under this policy, Janmashtami is displayed as
`Janmashtami (Ratri Kala)` to distinguish the broad experimental night-window
date from the traditional Vaishnava date.

### Common competition rule

The same rule resolves every plain-tithi festival:

1. Calculate the proportional overlap between the target tithi and the
   assigned kala on each candidate date.
2. Choose the date with the greatest proportional overlap.
3. If coverage is equal, choose the kala midpoint nearest the tithi midpoint.
4. If neither date overlaps the kala, midpoint proximity supplies the common
   missing-window fallback.
5. Use the earlier date only for an exact final tie.

The policy intentionally ignores festival-specific purva-viddha,
para-viddha, minimum-ghati, nakshatra, Bhadra, and similar tie-breakers.

## 3. Dharma Sindhu / Traditional

CLI value: `traditional`

This is the most detailed policy and the default used for normal PDF
generation. It first identifies the ritual's prescribed kala and then applies
the festival's own rules for competing dates, vriddhi, kshaya, contamination,
and missing windows.

Examples include:

- Rama Navami: Madhyahna-vyapini Navami with its specific fallback hierarchy.
- Narasimha Jayanti: Chaturdashi prevailing at exact sunset.
- Raksha Bandhan: Bhadra-free Aparahna or Pradosha with Purnima-duration rules.
- Naraka Chaturdashi: moonrise and pre-dawn abhyanga hierarchy.
- Deepavali: Pradosha-vyapini Amavasya for Lakshmi Puja.
- Mahalaya Amavasya: Aparahna-vyapini Amavasya for Shraddha.
- Maha Shivaratri: Nishitha-vyapini Chaturdashi.
- Vijayadashami: Aparahna, Shravana, and three-muhurta exceptions.

“Traditional” is more accurate than claiming that every listed festival is
directly prescribed by Dharma Sindhu. The calendar also contains:

- Regional South Indian and TTD-oriented conventions.
- Community observances not found in Dharma Sindhu.
- A Vaishnava Janmashtami selector distinct from Dharma Sindhu's Smarta
  Nishitha rule.
- Explicit project preferences documented beside individual rules.

Each rule's source and status in `festival_rules.py` should therefore be
consulted when textual provenance matters.

## Complexity and fidelity

| Policy | Festival-specific kala | Festival-specific competition | Intended use |
|---|---:|---:|---|
| Generic Udaya | No | No | Simplest universal sunrise marker |
| Generic Kala | Yes, from a small fixed vocabulary | No | Experimental balance of simplicity and ritual timing |
| Traditional | Yes | Yes | Normal calendar generation and highest textual fidelity |

The generic policies apply their common resolver only to plain-tithi rules.
Complex solar, weekday, nakshatra, and sectarian observances remain on
dedicated selectors so that an experimental policy does not make them
undefined.

## Benchmark snapshot

The generic policies were compared over the 2026–2125 range using the
traditional resolver as the reference, with one deliberate substitution:
Janmashtami uses Dharma Sindhu's Smarta Nishitha selector. The PDF's
Vaishnava Janmashtami variant is omitted from this comparison.

The figures below are exact annual date-set matches for plain-tithi festivals.
Traditional is 100% by definition because it supplies the reference dates.

| Location and scope | Traditional | Generic Udaya | Generic Kala |
|---|---:|---:|---:|
| Helsinki, all plain-tithi rules | 100% | 78.29% | 91.77% |
| Helsinki, PDF-visible subset | 100% | 74.60% | 90.72% |
| Tirupati, all plain-tithi rules | 100% | 77.06% | 91.74% |
| Tirupati, PDF-visible subset | 100% | 72.82% | 91.10% |

The Tirupati comparison used 98 successfully resolved traditional reference
years. The traditional resolver returned no Ganesha Chaturthi date in the
2055 and 2118 calendar ranges, so those two reference years were excluded.

These percentages measure agreement with this project's traditional resolver,
not independent proof that either generic policy is religiously authoritative.
For Janmashtami specifically, Generic Kala's broad Ratri window matched the
Smarta Nishitha result in 99 of 100 Helsinki years and 94 of 98 evaluated
Tirupati years. Generic Udaya matched only 17 and 32 years respectively. This
does not change normal PDF generation, which continues to use the separately
implemented Vaishnava Janmashtami rule under the traditional policy.
