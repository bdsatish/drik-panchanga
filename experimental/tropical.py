import swisseph as swe

# Vernal equinox = 20/21 March of given year
# Find on which year was Sun and the yogataras of Ashvini nak were
# overlapping on the day of vernal equinox
def sun_closest_to_star_on_vernal_equinox(star):
  diff = {}
  for yy in range(-900, 601):
    jd = swe.julday(yy, 3, 20, 12) # 12:00 UTC on YY-03-20
    solar = swe.calc_ut(jd, swe.SUN, flags = swe.FLG_SWIEPH | swe.FLG_TROPICAL)[0][0]
    nak = swe.fixstar_ut(star, jd, flags = swe.FLG_SWIEPH | swe.FLG_TROPICAL)[0][0]
    diff[yy] = solar - nak
  # Find values where the difference is almost zero
  print(star)
  print([(year, diff[year]) for year in diff if abs(diff[year]) < 0.1])

# Yogatara of Ashvini nakshatra = twins "Hamal" (alAri) "Sheratan" (beAri)
# alAri is the 50th most brightest star (apparent magnitude = 2.00)
sun_closest_to_star_on_vernal_equinox("Hamal")
sun_closest_to_star_on_vernal_equinox("Sheratan")

# Answer: For Hamal, it is year -769 that is best. Difference = -0.00751
#         For Sheratan, it is year -501 that is best. Difference = -0.00258
#
# what this means is that Sun was in Ashvini nakshatra on March 20 from approx 769 BCE, 501 BCE onwards
# (if Ashvini nak is mapped to tropical "Aries" (Mesha rashi), then this marks the zero point
# of overlap of tropical and sidereal zodiac)
#
# Today, Hamal is at 38° on vernal equinox (Sun is ~0° by definition)
# >>> swe.fixstar_ut("Hamal", swe.julday(2024, 3, 20), flags = swe.FLG_SWIEPH | swe.FLG_TROPICAL)[0][0]
#     37.99549299764622

# The above gives the approx date when the *yogatara*s were around 0° Aries
# But "Ashvini nakshatra" is a lunar mansion, spanning 0° to 13⅓ °
# Hamal and Sheratan are about 3.933° apart (Wolfram Alpha)
# So we can instead place the Yogataras in the MIDDLE of this lunar mansion.
# It means, Hamal's will be (13.333-3.933)/2 = 4.7° and Sheratan at 8.633°
# We can then calculate when Sun was also in the MIDDLE of this lunar mansion, i.e. 13.33/2=6.666°

def sun_middle_of_ashvini_on_vernal_equinox(star, offset):
  diff = {}
  for yy in range(-2500, 700):
    jd = swe.julday(yy, 3, 20, 12) # 12:00 UTC on YY-03-20
    solar = swe.calc_ut(jd, swe.SUN, flags = swe.FLG_SWIEPH | swe.FLG_TROPICAL)[0][0]
    nak = swe.fixstar_ut(star, jd, flags = swe.FLG_SWIEPH | swe.FLG_TROPICAL)[0][0]
    diff[yy] = solar - nak
  # Find values where the difference is almost zero
  print(star)
  print([(year, diff[year]) for year in diff if abs(diff[year] - offset) < 0.1])

sun_middle_of_ashvini_on_vernal_equinox("Hamal", 6.6666 - 4.7)
sun_middle_of_ashvini_on_vernal_equinox("Sheratan", -(6.6666 - 8.633))
