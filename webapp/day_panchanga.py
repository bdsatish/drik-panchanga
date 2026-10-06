"""Compute sunrise panchanga for one civil date and city (GUI-compatible).

Public entry points take ``panchanga.coordinate_calculation_lock``, then call
an ``_unlocked`` helper that does the real work. Hold the lock for the whole
request so ayanāṃśa / tropical mode stays stable under concurrent web use.
"""

import math
from functools import partial

import panchanga
from datetime_helper import Date, format_hms, format_local_hm, gregorian_to_jd
from generate_panchanga_calendar import (
  ayanamsa_label,
  body_altitude_at_local_noon,
  coordinate_selection_label,
  month_system_label,
  place_for_date,
  require_month_system,
  resolve_location,
  sanskrit_names,
)


def parse_civil_date(text):
  """Parse ``DD/MM/YYYY``: proleptic Gregorian, astronomical years (0 = 1 BCE, -1 = 2 BCE)."""
  text = (text or "").strip()
  if not text:
    raise ValueError("Date is required (DD/MM/YYYY)")
  parts = text.split("/")
  if len(parts) != 3:
    raise ValueError("Date must be DD/MM/YYYY (year 0 = 1 BCE, -1 = 2 BCE).")
  try:
    day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
  except ValueError:
    raise ValueError("Date must be DD/MM/YYYY (year 0 = 1 BCE, -1 = 2 BCE).") from None
  # Four-digit years, like ``require_start_year``; the ephemeris ends near -13000.
  # The day view keeps the wide range; only the PDFs and ICS stop at ±3300.
  if not -9999 <= year <= 9999:
    raise ValueError(f"Year {year} is out of range (-9999 to 9999).")
  # swe.julday would silently roll 31/4 or 30/2 into the next month.
  if not panchanga.swe.date_conversion(year, month, day)[0]:
    raise ValueError(f"Invalid date {text!r}")
  return Date(year, month, day)


def _named_segments(values, lookup, clock):
  """Map ``[index, end]`` or skipped ``[..., next_index, next_end]`` (UT JDs) to names."""
  segments = [{
    "number": int(values[0]),
    "name": lookup[str(values[0])],
    "ends": clock(values[1], show_seconds=True),
  }]
  if len(values) == 4:
    segments.append({
      "number": int(values[2]),
      "name": lookup[str(values[2])],
      "ends": clock(values[3], show_seconds=True),
    })
  return segments


def format_masa_name(names, masa_num, is_adhika):
  """Bare māsa name, with Adhika prefix when needed."""
  name = names["masas"][str(masa_num)]
  name = ("Adhika " + name) if is_adhika else name
  return name


def format_masa_label(names, masa_num, is_adhika):
  """Display māsa including the ``māsa`` suffix."""
  return format_masa_name(names, masa_num, is_adhika) + " māsa"


def probe_moon_event(jd, place, civil, clock, rise=True):
  """Moonrise/moonset on the Hindu day: ``(HH:MM:SS or None, status, UT JD or None)``.

  Status is ``ok``, ``none_today``, ``always_below``, ``always_above``, or
  ``unavailable``. ``clock`` formats a UT JD (``datetime_helper.format_local_hm``).
  """
  event = panchanga.moonrise(jd, place) if rise else panchanga.moonset(jd, place)
  if event is not None:
    return clock(event, show_seconds=True), "ok", event
  # No event in the Hindu-day window: distinguish circumpolar vs none today.
  swe = panchanga.swe
  t0 = jd - place.timezone / 24.0
  flag = swe.CALC_RISE if rise else swe.CALC_SET
  rc, times = swe.rise_trans(t0, swe.MOON, geopos=(place.longitude, place.latitude, 0.0),
                             rsmi=panchanga._rise_flags + flag)
  if rc != 0:
    altitude = body_altitude_at_local_noon(swe.MOON, civil.year, civil.month, civil.day, place)
    if altitude > 0.5:
      return None, "always_above", None
    if altitude < -0.5:
      return None, "always_below", None
    return None, "unavailable", None
  return None, "none_today", None


def _interval(start, end, clock):
  return {"start": clock(start, show_seconds=True), "end": clock(end, show_seconds=True)}


def _interval_str(start, end, clock):
  """Same two instants as ``_interval``, joined as one ``start–end`` string."""
  return f"{clock(start, show_seconds=True)}–{clock(end, show_seconds=True)}"


def ayana_label(raasi_num):
  """Uttarāyaṇa from Makara–Mithuna (10–12, 1–3); else Dakṣiṇāyana."""
  label = "Uttarāyaṇa" if raasi_num >= 10 or raasi_num <= 3 else "Dakṣiṇāyana"
  return label


def drik_ayana_label(ritu_num):
  """Ayana from Drik ṛtu: Śiśira–Vasanta–Grīṣma = Uttara; Varṣā–Śarad–Hemanta = Dakṣiṇa."""
  # Vasanta, Grīṣma, Śiśira → Uttarāyaṇa
  label = "Uttarāyaṇa" if ritu_num in (0, 1, 5) else "Dakṣiṇāyana"
  return label


def _compute_day_details_unlocked(location, civil, amanta=None, coordinate_selection=None):
  """Compute all mode-sensitive panchanga fields for one civil day.

    Shared by the JSON day API and the ICS generator so both consume the
    same normalized day record.  ``civil`` is a ``datetime_helper.Date``.

    Works at every latitude: above the polar circles the day anchors at the
    matching meridian transit (solar noon in polar night, solar midnight in
    midnight sun) via the core sunrise()/sunset() fallback.
    """
  with panchanga.using_coordinate_selection(coordinate_selection):
    place = place_for_date(location, civil)
    jd = gregorian_to_jd(civil)
    # UT JD -> this day's 24:00+ clock, at the UTC offset in force at each instant.
    clock = partial(format_local_hm, timezone_name=location.timezone_name, anchor_civil=civil,
                    longitude=location.longitude)

    sunrise = panchanga.sunrise(jd, place)
    sunset = panchanga.sunset(jd, place)
    day_dur = panchanga.day_duration(jd, place)

    names = sanskrit_names()
    ti = panchanga.tithi(jd, place)
    nak = panchanga.nakshatra(jd, place)
    yog = panchanga.yoga(jd, place)
    kar = panchanga.karana(jd, place)
    ti_num, last_nm, lunar_num, is_adhika = panchanga.lunar_masa(jd, place, tithi_number=ti[0])
    # Display māsa follows amānta/pūrṇimānta; ṛtus use lunar_num only.
    masa_num = panchanga.display_masa_number(lunar_num, is_adhika, ti_num, amanta)
    rtu_num = panchanga.ritu(lunar_num)
    prev_was_adhika = panchanga.previous_masa_was_adhika(last_nm, is_adhika)
    drik_rtu_num = panchanga.drik_ritu(lunar_num, is_adhika, ti_num, prev_was_adhika)
    samvat_num = panchanga.samvatsara(jd, lunar_num)
    samvat_north_num = panchanga.samvatsara_north_modern(jd, lunar_num)
    vara_num = panchanga.vaara(jd)
    kali_year, saka_year, vikrama_year = panchanga.elapsed_year(jd, lunar_num)
    kali_day = math.floor(panchanga.ahargana(jd))
    if coordinate_selection == "tropical":
      ayanamsa_degrees = None
    else:
      panchanga.set_ayanamsa_mode()
      try:
        ayanamsa_degrees = float(panchanga.swe.get_ayanamsa_ut(sunrise))
      finally:
        panchanga.reset_ayanamsa_mode()
    sun_raasi = int(panchanga.raasi(sunrise))
    moonrise, moonrise_status, moonrise_at = probe_moon_event(jd, place, civil, clock, rise=True)
    moonset, moonset_status, moonset_at = probe_moon_event(jd, place, civil, clock, rise=False)
    rahu_kala = panchanga.rahu_kalam(jd, place)
    durmuhurta = panchanga.durmuhurtam(jd, place)
    varjyam = panchanga.varjyam(jd, place)
    pratah_sandhya = panchanga.pratah_sandhya(jd, place)
  return {
    "civil": civil,
    "place": place,
    "jd": jd,
    "clock": clock,
    "sunrise": sunrise,
    "sunset": sunset,
    "day_dur": day_dur,
    "names": names,
    "ti": ti,
    "nak": nak,
    "yog": yog,
    "kar": kar,
    "ti_num": ti_num,
    "lunar_num": lunar_num,
    "is_adhika": bool(is_adhika),
    "masa_num": masa_num,
    "rtu_num": rtu_num,
    "drik_rtu_num": drik_rtu_num,
    "samvat_num": samvat_num,
    "samvat_north_num": samvat_north_num,
    "vara_num": vara_num,
    "kali_year": int(kali_year),
    "saka_year": int(saka_year),
    "vikrama_year": int(vikrama_year),
    "kali_day": kali_day,
    "ayanamsa_degrees": ayanamsa_degrees,
    "sun_raasi": sun_raasi,
    "moonrise": moonrise,
    "moonrise_status": moonrise_status,
    "moonrise_jd": moonrise_at,
    "moonset": moonset,
    "moonset_status": moonset_status,
    "moonset_jd": moonset_at,
    "rahu_kala": rahu_kala,
    "durmuhurta": durmuhurta,
    "varjyam": varjyam,
    "pratah_sandhya": pratah_sandhya,
  }


def compute_day_panchanga(city, date_text, month_system="amanta", coordinate_selection="citra", place=None):
  """Return named panchanga fields for ``city`` on ``date_text`` (DD/MM/YYYY).

    ``month_system`` is ``amanta`` (default) or ``purnimanta``; it affects the
    displayed māsa name only. Vedic and Drik ṛtu, the samvatsara and the year
    counters always use the shared new-moon–bounded amānta māsa identity, so
    they are the same under either display system.

    ``coordinate_selection`` is a sidereal ayanāṃśa key (``citra`` default,
    ``revati``, ``rohini``, ``pushya``, ``mula``, ``krishnamurti``, ``raman``)
    or ``"tropical"`` for tropical (sāyana) longitudes.

    ``place`` (``LAT,LON,TZ``, as the ``--city LAT,LON,TZ`` form of the CLI)
    selects a manual location with a fixed UTC offset (no DST); when set it
    wins over ``city``.
    """
  with panchanga.coordinate_calculation_lock:
    location = resolve_location(city, place)
    amanta = require_month_system(month_system)
    civil = parse_civil_date(date_text)

    details = _compute_day_details_unlocked(location, civil, amanta=amanta, coordinate_selection=coordinate_selection)
    names = details["names"]
    civil = details["civil"]

    use_tropical = coordinate_selection == "tropical"
    masa_label = format_masa_label(names, details["masa_num"], details["is_adhika"])
    month_label = month_system_label(amanta)
    ayan_label = None if use_tropical else ayanamsa_label(coordinate_selection)
    ayana = ayana_label(details["sun_raasi"])
    drik_ayana = drik_ayana_label(details["drik_rtu_num"])

    durmuhurta_intervals = [_interval(start, end, details["clock"]) for start, end in details["durmuhurta"]]
    varjyam_intervals = [_interval(start, end, details["clock"]) for start, end in details["varjyam"]]

    return {
      "city": location.name,
      "date": f"{civil.day:02d}/{civil.month:02d}/{civil.year}",
      "timezone": location.timezone_name,
      "jd": details["jd"],
      "sunrise_jd": details["sunrise"],
      "coordinate_mode": "tropical" if use_tropical else "sidereal",
      "coordinate_label": coordinate_selection_label(coordinate_selection),
      "ayanamsa": ayan_label,
      "ayanamsa_key": None if use_tropical else coordinate_selection,
      "ayanamsa_degrees": None if use_tropical else round(details["ayanamsa_degrees"], 8),
      "month_system": "amanta" if amanta else "purnimanta",
      "month_system_label": month_label,
      "samvatsara": names["samvats"][str(details["samvat_num"])],
      "samvatsara_north": names["samvats"][str(details["samvat_north_num"])],
      "ayana": ayana,
      "drik_ayana": drik_ayana,
      "masa": masa_label,
      "masa_number": details["masa_num"],
      "is_adhika": details["is_adhika"],
      "rtu": f"{names['ritus'][str(details['rtu_num'])]} ṛtu",
      "drik_rtu": f"{names['ritus'][str(details['drik_rtu_num'])]} ṛtu",
      "vaara": names["varas"][str(details["vara_num"])],
      "kali_day": details["kali_day"],
      "saka_year": details["saka_year"],
      "kali_year": details["kali_year"],
      "vikrama_year": details["vikrama_year"],
      # Instants read the event's own UTC offset; durations do not (a DST
      # lengthened day really is 25 h).
      "sunrise": details["clock"](details["sunrise"], show_seconds=True),
      "sunset": details["clock"](details["sunset"], show_seconds=True),
      "moonrise": details["moonrise"],
      "moonrise_status": details["moonrise_status"],
      "moonrise_jd": details["moonrise_jd"],
      "moonset": details["moonset"],
      "moonset_status": details["moonset_status"],
      "moonset_jd": details["moonset_jd"],
      "day_duration": format_hms(details["day_dur"][1], show_seconds=True),
      "rahu_kala": _interval(*details["rahu_kala"], details["clock"]),
      "durmuhurta": durmuhurta_intervals,
      "varjyam": varjyam_intervals,
      "pratah_sandhya": _interval(*details["pratah_sandhya"], details["clock"]),
      "tithi": _named_segments(details["ti"], names["tithis"], details["clock"]),
      "nakshatra": _named_segments(details["nak"], names["nakshatras"], details["clock"]),
      "yoga": _named_segments(details["yog"], names["yogas"], details["clock"]),
      "karana": _named_segments(details["kar"], names["karanas"], details["clock"]),
    }
