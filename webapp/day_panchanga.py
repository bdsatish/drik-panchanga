"""Compute sunrise panchanga for one civil date and city (GUI-compatible).

Public entry points take ``panchanga.coordinate_calculation_lock``, then call
an ``_unlocked`` helper that does the real work. Hold the lock for the whole
request so ayanāṃśa / tropical mode stays stable under concurrent web use.
"""

import logging

import panchanga
from generate_panchanga_calendar import (
  ayanamsa_label,
  body_altitude_at_local_noon,
  coordinate_selection_label,
  format_sunrise_unavailable_message,
  load_location,
  month_system_label,
  place_for_date,
  require_local_sunrise,
  require_month_system,
  sanskrit_names,
)

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


def parse_civil_date(text):
  """Parse ``DD/MM/YYYY``; negative years are proleptic Gregorian."""
  text = (text or "").strip()
  if not text:
    raise ValueError("Date is required (DD/MM/YYYY)")
  parts = text.split("/")
  if len(parts) != 3:
    raise ValueError("Date must be DD/MM/YYYY (negative years allowed).")
  try:
    day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
  except ValueError:
    raise ValueError("Date must be DD/MM/YYYY (negative years allowed).") from None
  if year == 0:
    raise ValueError("Year 0 is not used; use negative years for BCE")
  if not 1 <= month <= 12 or not 1 <= day <= 31:
    raise ValueError(f"Invalid date {text!r}")
  return panchanga.Date(year, month, day)


def format_time(hms):
  hours, minutes, seconds = hms
  return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"


def _named_segments(nhms, lookup):
  """Map ``[index, [h,m,s]]`` or skipped ``[..., next_index, next_hms]`` to names."""
  segments = [{
    "number": int(nhms[0]),
    "name": lookup[str(nhms[0])],
    "ends": format_time(nhms[1]),
  }]
  if len(nhms) == 4:
    segments.append({
      "number": int(nhms[2]),
      "name": lookup[str(nhms[2])],
      "ends": format_time(nhms[3]),
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


def probe_moon_event(jd, place, civil, rise=True):
  """Return ``(time_or_None, status)`` for moonrise/moonset on a civil day.

    Status is ``ok``, ``none_today`` (next event is after local midnight+24h),
    ``always_below``, ``always_above``, or ``unavailable``.
    """
  swe = panchanga.swe
  t0 = jd - place.timezone / 24.0
  flag = swe.CALC_RISE if rise else swe.CALC_SET
  try:
    rc, times = swe.rise_trans(t0, swe.MOON, geopos=(place.longitude, place.latitude, 0.0),
                               rsmi=panchanga._rise_flags + flag)
  except Exception as error:
    log.error("Moon %s probe failed: %s", "rise" if rise else "set", error)
    return None, "unavailable"
  if rc != 0:
    altitude = body_altitude_at_local_noon(swe.MOON, civil.year, civil.month, civil.day, place)
    if altitude > 0.5:
      return None, "always_above"
    if altitude < -0.5:
      return None, "always_below"
    return None, "unavailable"
  local_hours = (times[0] - t0) * 24.0
  if not 0.0 <= local_hours < 24.0:
    return None, "none_today"
  return format_time(panchanga.to_dms(local_hours)), "ok"


def _interval_from_hms(start_hms, end_hms):
  return {"start": format_time(start_hms), "end": format_time(end_hms)}


def _valid_durmuhurta_intervals(values):
  """Return Durmuhūrta interval values without unused ``(0, 0)`` slots."""
  starts, ends = values
  intervals = []
  for start, end in zip(starts, ends):
    if start != 0 or end != 0:
      intervals.append((start, end))
  return intervals


def ayana_label(raasi_num):
  """Uttarāyaṇa from Makara–Mithuna (10–12, 1–3); else Dakṣiṇāyana."""
  label = "Uttarāyaṇa" if raasi_num >= 10 or raasi_num <= 3 else "Dakṣiṇāyana"
  return label


def drik_ayana_label(ritu_num):
  """Ayana from Drik ṛtu: Śiśira–Vasanta–Grīṣma = Uttara; Varṣā–Śarad–Hemanta = Dakṣiṇa."""
  # Vasanta, Grīṣma, Śiśira → Uttarāyaṇa
  label = "Uttarāyaṇa" if ritu_num in (0, 1, 5) else "Dakṣiṇāyana"
  return label


def compute_day_details(location, civil, amanta=None, coordinate_selection=None):
  """Compute one day while holding the shared coordinate-state lock.

    Lock here, then ``_compute_day_details_unlocked`` does the astronomy.
    """
  with panchanga.coordinate_calculation_lock:
    return _compute_day_details_unlocked(location, civil, amanta=amanta, coordinate_selection=coordinate_selection)


def _compute_day_details_unlocked(location, civil, amanta=None, coordinate_selection=None):
  """Compute all mode-sensitive panchanga fields for one civil day.

    Shared by the JSON day API and the ICS generator so both consume the
    same normalized day record.  ``civil`` has ``year``/``month``/``day``
    attributes (``panchanga.Date`` or ``datetime.date``).

    Raises ``ValueError`` when sunrise cannot be computed for the date/location.
    """
  panchanga.set_coordinate_selection(coordinate_selection)
  place = place_for_date(location, civil)
  jd = panchanga.gregorian_to_jd(civil)

  sunrise = require_local_sunrise(jd, place, location.name, civil.year, civil.month, civil.day)
  if sunrise is None:
    raise ValueError(format_sunrise_unavailable_message(location.name, civil.year, civil.month, civil.day, place))
  sunset = panchanga.sunset(jd, place)
  sunset_jd = sunset[0]
  if not jd - 1 <= sunset_jd <= jd + 2:
    message = format_sunrise_unavailable_message(location.name, civil.year, civil.month, civil.day, place)
    log.error("%s (no local sunset)", message)
    raise ValueError(message)
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
  samvat_num = panchanga.samvatsara(jd, masa_num)
  samvat_north_num = panchanga.samvatsara_north_modern(jd, masa_num)
  vara_num = panchanga.vaara(jd)
  kali_year, saka_year, vikrama_year = panchanga.elapsed_year(jd, masa_num)
  kali_day = int(panchanga.ahargana(jd))
  sunrise_jd_ut = sunrise[0] - place.timezone / 24.0
  if coordinate_selection == "tropical":
    ayanamsa_degrees = None
  else:
    panchanga.set_ayanamsa_mode()
    try:
      ayanamsa_degrees = float(panchanga.swe.get_ayanamsa_ut(sunrise_jd_ut))
    finally:
      panchanga.reset_ayanamsa_mode()
  sun_raasi = int(panchanga.raasi(sunrise_jd_ut))
  moonrise, moonrise_status = probe_moon_event(jd, place, civil, rise=True)
  moonset, moonset_status = probe_moon_event(jd, place, civil, rise=False)
  rahu_kala = panchanga.rahu_kalam(jd, place)
  durmuhurta = panchanga.durmuhurtam(jd, place)
  varjyam = panchanga.varjyam(jd, place)

  return {
    "civil": civil,
    "place": place,
    "jd": jd,
    "sunrise_jd_ut": sunrise_jd_ut,
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
    "moonset": moonset,
    "moonset_status": moonset_status,
    "rahu_kala": rahu_kala,
    "durmuhurta": durmuhurta,
    "varjyam": varjyam,
  }


def compute_day_panchanga(city, date_text, month_system="amanta", coordinate_selection="citra"):
  """Return named panchanga fields for ``city`` on ``date_text`` (DD/MM/YYYY).

    ``month_system`` is ``amanta`` (default) or ``purnimanta``; it affects the
    displayed māsa name (and samvatsara / year counters derived from that name).
    Vedic and Drik ṛtu always use the shared new-moon–bounded māsa identity.

    ``coordinate_selection`` is a sidereal ayanāṃśa key (``citra`` default,
    ``revati``, ``rohini``, ``pushya``, ``mula``, ``krishnamurti``, ``raman``)
    or ``"tropical"`` for tropical (sāyana) longitudes.
    """
  with panchanga.coordinate_calculation_lock:
    city = (city or "").strip()
    if not city:
      raise ValueError("City is required.")
    amanta = require_month_system(month_system)
    civil = parse_civil_date(date_text)
    location = load_location(city)

    details = _compute_day_details_unlocked(location, civil, amanta=amanta, coordinate_selection=coordinate_selection)
    names = details["names"]
    civil = details["civil"]

    use_tropical = coordinate_selection == "tropical"
    masa_label = format_masa_label(names, details["masa_num"], details["is_adhika"])
    month_label = month_system_label(amanta)
    ayan_label = None if use_tropical else ayanamsa_label(coordinate_selection)
    ayana = ayana_label(details["sun_raasi"])
    drik_ayana = drik_ayana_label(details["drik_rtu_num"])

    durmuhurta_intervals = []
    for start, end in _valid_durmuhurta_intervals(details["durmuhurta"]):
      durmuhurta_intervals.append(_interval_from_hms(panchanga.to_dms(start), panchanga.to_dms(end)))

    varjyam_intervals = []
    for start, end in details["varjyam"]:
      varjyam_intervals.append(_interval_from_hms(start, end))

    return {
      "city": location.name,
      "date": f"{civil.day:02d}/{civil.month:02d}/{civil.year}",
      "timezone": location.timezone_name,
      "jd": details["jd"],
      "sunrise_jd": details["sunrise_jd_ut"],
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
      "sunrise": format_time(details["sunrise"][1]),
      "sunset": format_time(details["sunset"][1]),
      "moonrise": details["moonrise"],
      "moonrise_status": details["moonrise_status"],
      "moonset": details["moonset"],
      "moonset_status": details["moonset_status"],
      "day_duration": format_time(details["day_dur"][1]),
      "rahu_kala": _interval_from_hms(*details["rahu_kala"]),
      "durmuhurta": durmuhurta_intervals,
      "varjyam": varjyam_intervals,
      "tithi": _named_segments(details["ti"], names["tithis"]),
      "nakshatra": _named_segments(details["nak"], names["nakshatras"]),
      "yoga": _named_segments(details["yog"], names["yogas"]),
      "karana": _named_segments(details["kar"], names["karanas"]),
    }
