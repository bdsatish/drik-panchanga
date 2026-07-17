# Festival Date Policies

The calendar provides four festival-date policies, ordered here from the
simplest and most uniform to the most detailed:

1. `generic-udaya`
2. `generic-anchor`
3. `generic-kala`
4. `traditional` (Dharma-Sindhu-oriented)

The traditional policy remains the default. The three generic policies are
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

## 2. Generic Anchor Point

CLI value: `generic-anchor`

This policy replaces kala windows with five exact local instants:

- Sunrise.
- Day midpoint, halfway from sunrise to sunset.
- Sunset.
- Night midpoint, halfway from sunset to the following sunrise.
- Technical Arunodaya start, four ghatis (96 minutes) before sunrise.

The current ritual classifications collapse into this reduced vocabulary:

| Anchor | Festivals |
|---|---|
| Sunrise | Ugadi, Yajur Upakarma, and every otherwise unclassified plain-tithi festival |
| Day midpoint | Vasanta Panchami, Rama Navami, Akshaya Tritiya, Ganesha Chaturthi, Bali Padyami, Raksha Bandhan, Mahalaya Amavasya, Mahanavami (Puja), Vijayadashami (Puja) |
| Sunset | Narasimha Jayanti, Dhana Trayodashi, Deepavali, Kama Dahana (Holi) |
| Night midpoint | Janmashtami, Maha Shivaratri |
| Arunodaya start | Naraka Chaturdashi, Ratha Saptami |

For each target tithi occurrence, the resolver selects a candidate date whose
anchor lies inside the tithi. If multiple anchors qualify, the one nearest the
tithi midpoint wins; if none qualify, the nearest anchor supplies the common
fallback. An exact final tie uses the earlier date.

This policy does not inherit Generic Kala's Yajur Upakarma validity overlay.
Rig Upakarma and other non-plain-tithi rules retain their dedicated selectors.
Janmashtami is displayed as `Janmashtami (Night-Midpoint Anchor)` under this
policy.

The policy is identified as `Generic-anchor EXP-1.0` in generated PDFs.
Accuracy benchmarking is intentionally deferred.

## 3. Generic Kala

CLI value: `generic-kala`

This policy retains a common resolver but assigns a simple ritual period to
each festival type. It is more expressive than Generic Udaya without
introducing festival-specific competition rules.

The ten-slot model is identified as `Generic-kala EXP-2.0` in generated PDFs.

### Granular kala slots

The actual local intervals of daylight and night are each divided into five
equal proportional parts. Festival windows use this one predictable grid:

- Daylight: Pratah, Sangava, Madhyahna, Aparahna, and Sayahna.
- Night: Pradosha, Purvaratri, Madhyaratri, Apararatri, and Arunodaya.
- Purvahna is the explicit Pratah-plus-Sangava span.

Sunrise and sunset are also available as exact points. Every boundary scales
with local day or night length; the policy does not mix proportional divisions
with fixed-ghati widths.

These names provide a one-to-one ritual vocabulary for the ten addressable
slots. Their numerical boundaries remain the experiment's uniform
proportional grid; they do not claim that every Dharma Sindhu use of a named
kala has exactly that width.

### Festival assignments

| Kala | Festivals |
|---|---|
| Pratah | None directly assigned |
| Sangava | None directly assigned |
| Purvahna (Pratah + Sangava) | Rig Upakarma, Vasanta Panchami |
| Madhyahna | Rama Navami, Akshaya Tritiya, Ganesha Chaturthi, Bali Padyami |
| Aparahna | Raksha Bandhan, Mahalaya Amavasya, Mahanavami (Puja), Vijayadashami (Puja) |
| Sayahna | None directly assigned |
| Sunset | Narasimha Jayanti |
| Pradosha | Dhana Trayodashi, Deepavali, Kama Dahana (Holi) |
| Purvaratri | None directly assigned |
| Madhyaratri | Janmashtami, Maha Shivaratri |
| Apararatri | None directly assigned |
| Arunodaya | Naraka Chaturdashi, Ratha Saptami |
| Sunrise | Ugadi and every otherwise unclassified plain-tithi festival |

Rig Upakarma is nakshatra-based rather than a plain-tithi festival. Its
dedicated selector is therefore retained, although Purvahna is its conceptual
assignment.

Under this policy, Janmashtami is displayed as
`Janmashtami (Madhyaratri Kala)` to distinguish the experimental night-slot
date from the traditional Vaishnava date.

Mahanavami's source-derived final-six-ghati window initially suggested
Sayahna. A 2026–2075 exploratory comparison and an independent 2076–2125
holdout comparison rejected that reassignment: Sayahna reduced Helsinki
matches from 50/50 to 45/50 in exploration and from 48/50 to 45/50 in
holdout, while Tirupati improved from 46/50 to 50/50 in exploration but tied
49/50 in holdout. Aparahna was therefore retained rather than fitting one
location.

### Common competition rule

Sunrise uses the Generic Udaya ownership rule: one sunrise uses that date,
vriddhi uses the first sunrise, and kshaya uses the containing
sunrise-to-sunrise day.

Every other assigned kala uses the same competition rule:

1. Calculate the proportional overlap between the target tithi and the
   assigned kala on each candidate date.
2. Choose the date with the greatest proportional overlap.
3. If coverage is equal, choose the kala midpoint nearest the tithi midpoint.
4. If neither date overlaps the kala, midpoint proximity supplies the common
   missing-window fallback.
5. Use the earlier date only for an exact final tie.

### Validity overlays

A validity overlay is a narrow post-selection constraint. It does not change
the common kala overlap score or its tie-breaks. It can only accept the
selected date, retry a declared fallback with the same Generic Kala resolver,
or return no date.

Yajur Upakarma currently has one such overlay. Its Sunrise-selected Shravana
Purnima is rejected when a locally visible non-penumbral eclipse or Sankranti
occurs in Dharma Sindhu's eight-yama window. The fallback is Bhadrapada
Purnima, independently selected by the same Sunrise rule and checked by the
same overlay. If both dates are defective, the result is `None`.

Generic Udaya intentionally does not apply this overlay, preserving that
policy as the uniform sunrise-only baseline.

The policy intentionally ignores festival-specific purva-viddha,
para-viddha, minimum-ghati, nakshatra, Bhadra, and similar tie-breakers.

## 4. Dharma Sindhu / Traditional

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
| Generic Anchor | Yes, from five exact instants | No | Exact-point alternative to kala windows |
| Generic Kala | Yes, from a small fixed vocabulary | No | Experimental balance of simplicity and ritual timing |
| Traditional | Yes | Yes | Normal calendar generation and highest textual fidelity |

The generic policies apply their common resolver only to plain-tithi rules.
Complex solar, weekday, nakshatra, and sectarian observances remain on
dedicated selectors so that an experimental policy does not make them
undefined.

## Benchmark snapshot

Generic Udaya and Generic Kala were compared over the 2026–2125 range using
non-overlapping January–December windows, so each physical festival
occurrence is counted only once. The traditional resolver supplies the
reference, with one deliberate substitution: Janmashtami uses Dharma Sindhu's
Smarta Nishitha selector. The PDF's Vaishnava Janmashtami variant is omitted
from this comparison.

Mapping decisions use 2026–2075 as the exploratory range and 2076–2125 as
independent holdout validation at both locations. A neighboring slot is
accepted only when ritually supportable and when its exploratory gain does not
regress either holdout.

The figures below are exact occurrence-date matches for plain-tithi festivals.
Traditional is 100% by definition because it supplies the reference dates.

| Location and scope | Traditional | Generic Udaya | Generic Kala |
|---|---:|---:|---:|
| Helsinki, all plain-tithi rules | 100% | 81.72% | 97.17% |
| Helsinki, PDF-visible subset | 100% | 78.87% | 96.77% |
| Tirupati, all plain-tithi rules | 100% | 80.68% | 96.54% |
| Tirupati, PDF-visible subset | 100% | 77.31% | 96.29% |

The measured PDF-visible ceiling of this ten-slot allocation is therefore
96.77% in Helsinki and 96.29% in Tirupati, short of the 99% goal. Closing that
gap would require changing mappings that fail holdout or adding the
festival-specific rules this experiment intentionally avoids.

The Helsinki comparison used 99 successfully resolved traditional reference
years; 2072 was excluded because the traditional resolver returned no Kama
Dahana date. The Tirupati comparison used 98 years; 2055 and 2118 were
excluded because the traditional resolver returned no Ganesha Chaturthi date.

These percentages measure agreement with this project's traditional resolver,
not independent proof that either generic policy is religiously authoritative.
For Janmashtami specifically, Generic Kala's broad Ratri window matched the
Smarta Nishitha result in 98 of 99 evaluated Helsinki years and 94 of 98
Tirupati years. Generic Udaya matched only 17 and 32 years respectively. This
does not change normal PDF generation, which continues to use the separately
implemented Vaishnava Janmashtami rule under the traditional policy.

Ugadi uses explicit first-sunrise ownership under Generic Udaya and Generic
Kala and matched every evaluated traditional occurrence at both locations.

For Yajur Upakarma, Generic Kala's Sunrise resolver plus validity overlay
matched 95 of 99 evaluated Helsinki occurrences and 83 of 98 Tirupati
occurrences. Generic Udaya, which deliberately omits the overlay, matched 92
and 77 respectively.
