# About different ayanamshas

From the [Swiss ephemeris documentation][1]

We have found that there are basically three definitions, not counting the
manifold variations:

1. the Babylonian zodiac with Spica at 29 Virgo or Aldebaran at 15 Taurus:
    a) P. Huber, b) Fagan/Bradley c) refined with Aldebaran at 15 Tau
2. the Greek-Arabic-Hindu zodiac with the zero point between 10 and 20 east of zeta Piscium:
    a) Hipparchus, b) Ushâshashî, c) Sassanian
3. the Greek-Hindu astrological zodiac with Spica at 0 Libra
    a) Lahiri
 
The differences are:
between 1) and 3) is about 1 degree
between 1) and 2) is about 5 degrees
between 2) and 3) is about 4 degrees

The zero points of all of these are around 560 AD:

```
04. name = Ushashashi              , julday = 1925433.8940655 year = +0559, month = 07, day = 23, hour = 009:27:27.25914001
15. name = Hipparchos              , julday = 1920430.0933129 year = +0545, month = 11, day = 09, hour = 014:14:22.23971397
16. name = Sassanian               , julday = 1927135.8163668 year = +0564, month = 03, day = 20, hour = 007:35:34.09921378
22. name = Suryasiddhanta, mean Sun, julday = 1909045.5186681 year = +0514, month = 09, day = 09, hour = 000:26:52.92675734
24. name = Aryabhata, mean Sun     , julday = 1909650.7495622 year = +0516, month = 05, day = 06, hour = 005:59:22.17763424
25. name = SS Revati               , julday = 1924230.2014096 year = +0556, month = 04, day = 05, hour = 016:50:1.79022253
26. name = SS Citra                , julday = 1847826.9474462 year = +0347, month = 01, day = 29, hour = 010:44:19.35084075
```

Ushashashi (Indian), Hipparchos (Greek), Sassanian (Arabic) and SS Revati
(Suryasiddhanta) are all based on Revati.  The rest are based on Citra.


```
SS_REVATI: The Suryasiddhanta also mentions that Revati/zeta-Piscium is
exactly at 359°50’ in polar ecliptic longitude (projection onto the ecliptic
along meridians). Therefore the following two ayanamshas were added:
 
25) ayanamsha = -0.79167046          21 Mar 499, 7:30:31.57 UT = noon at Ujjain, 75.7684565 E.
                                     Revati/zePsc at polar ecliptic longitude 359°50’


SS_CITRA: The Suryasiddhanta gives Spica the position 180° in polar longitude
(ecliptic longitude, but projection on meridian lines). From this, the following
Ayanamsha can be derved:

26) ayanamsha = 2.11070444           21 Mar 499, 7:30:31.57 UT = noon at Ujjain, 75.7684565 E.
                                     Citra/Spica at polar ecliptic longitude 180°.
 
``` 

`TRUE_CITRA`, `TRUE_REVATI` and `TRUE_PUSHYA` give same constant value of their
ayanamsa. They do not change w.r.t julian date, unlike others:

```
27. name = True Citra           3°52’15.85906894”
28. name = True Revati          0°00’00.00000000”
29. name = True Pushya       -106°00’00.00000000”
```


```python 
import swisseph as swe
jd = 1927135.8747793 # 18 Mar 564

swe.set_sid_mode(swe.SIDM_TRUE_REVATI)
to_dms(swe.get_ayanamsa_ut(jd))

  [0, 0, 0.0]

swe.set_sid_mode(swe.SIDM_TRUE_CITRA)
to_dms(swe.get_ayanamsa_ut(jd))
  [3, 52, 15.859])

```

Among the Indian/Hindu traditions for calculating Ayanamsha, the Lahiri system
is based on Citra (Spica). For the above date, some notable values:

```
# All these are > 1°
('Fagan/Bradley', 0, [4, 44, 51.221])
('Lahiri', 1, [3, 51, 51.136])
('Krishnamurti', 5, [3, 46, 3.406])
('SS Citra', 26, [3, 0, 46.101])
('True Citra', 27, [3, 52, 15.859])

# All these are [0°, 1°)
('Ushashashi', 4, [0, 3, 52.862])
('Suryasiddhanta', 21, [0, 54, 7.565])
('Suryasiddhanta, mean Sun', 22, [0, 41, 14.883])
('Aryabhata', 23, [0, 54, 7.568])
('Aryabhata, mean Sun', 24, [0, 39, 52.091])
('SS Revati', 25, [0, 6, 37.551])
('True Revati', 28, [0, 0, 0.0])
```

The closest value among Indian traditions is that of Uṣāśaśi, with
0°3′53″. Interestingly, the Greek and Arabic traditions also predict a value
close to zero for the same date:

```
('Hipparchos', 15, [0, 15, 17.46])
('Sassanian', 16, [0, 0, 0.008])
```

In a sense, revatīpakṣa ayanāmśa has a remarkable Greek-Arabic-Indian
synchronism.

The Hipparchan ayanamsha is -9°20′ as on 27 June –128 (jd 1674484).

UshaShashi reaches zero point at 23 Jul 559 CE, 09:27

```python
for i in range(0, 29):
     swe.set_sid_mode(i)
     name = swe.get_ayanamsa_name(i) if i != 28 else 'True Revati'
     print(name, i, to_dms(swe.get_ayanamsa_ut(swe.julday(559, 7, 23, 9.46))))
```

[1]: http://www.astro.com/swisseph/swisseph.htm

## Galactic Center and Mūlā Nakṣatra

We can choose the zero-point of the ayanamsa to coincide exactly with the
beginning of Sagittarius/Dhanus constallation (which spans from 240° to
270°). This is what Swiss eph's `swe.SIDM_GALCENT_0SAG` does:

```
swe.set_sid_mode(swe.SIDM_GALCENT_0SAG)
julday = 1746447.4042490 # 04 Jul, 69 CE
swe.fixstar_ut("Gal. Center", julday, flag = swe.FLG_NOABERR | swe.FLG_SIDEREAL)
    (240.00133698938166, -5.349660021998989, 0.9999999999999999, 0.0, 0.0, 0.0)
```
where the longitude is `0° Sag 0’ 4.8132”`. If you get the Ayanamsa on that day,
it is indeed zero:

```
swe.get_ayanamsa_ut(julday)
    2.839101398421917e-09
```

There are 27 Nakshatras spanning 360° so each occupies 13°20’ exactly. The 30°
of Sagittarius is spanned by Mūlā Nakṣatra (0° to 13°20’), Pūrvāṣāḍhā (13°20’ to
26°40’), and Uttārāṣāḍhā 1st pādā (26°40’ to 30°). The above mode puts the
ayanamsa beginning at 0° Sag = 0° of Mūlā. However, people claim UshaShashi puts
the galactic center at the _middle_ of Mūlā instead of _beginning_.

```
swe.set_sid_mode(swe.SIDM_USHASHASHI)
julday = 1925433.8940655  # Zeropoint of Ayanamsa
swe.get_ayanamsa_ut(julday)
    1.5592931390528975e-09
galc = swe.fixstar_ut("Gal. Center", julday, flag = swe.FLG_NOABERR | swe.FLG_SIDEREAL)
to_dms_prec(galc[0] % 30)
[6, 47, 44.2442]
```

The middle of Mūlā is `6°40’` but the above is off by 7’44” :(

Repeating the procedure for other types of Ayanamsas:

```
                     Sagittarius         Sagittarius
                  (with FLG_NOABERR)  (without FLG_NOABERR)
GALACTIC_CENTER   [0, 0, 4.8132]      [0, 0, 19.7637]

SS_REVATI         [6, 44, 59.5756]    [6, 45, 12.2397]
USHASHASHI        [6, 47, 44.2442]    [6, 47, 56.4404]
SASSANIAN         [6, 51, 37.0657]    [6, 51, 44.8046]
HIPPARCHAN        [6, 36, 19.763]     [6, 35, 59.9548]

LAHIRI            [2, 59, 47.7086]    [2, 59, 44.6748]
FAGAN_BRADLEY     [2, 6, 48.0358]     [2, 6, 28.4751]
SS_CITRA          [3, 50, 52.4752]    [3, 50, 43.5064]
YUKTESHWAR        [4, 22, 28.7773]    [4, 22, 17.8058]
```

The correct value is `6°40’`, SS_REVATI is the closest.

In fact, we can calculate our own Ayanamsa (by bisection root-finding) to
coincide with the middle of Mūlā:

```
julday = swe.julday(550, 3, 9, 14 + 3/60. + 32.45/3600.)
swe.set_sid_mode(swe.SIDM_USER, julday, 0)  # we assert that ayanamsa(julday) == 0
galc = swe.fixstar_ut("Gal. Center", julday, flag = swe.FLG_SIDEREAL); to_dms_prec(galc[0] % 30)
    [6, 40, 0.0]
```

So, choosing the zero-point of Ayanamsa on 9 Mar 550 CE at 14:03:32.45 UTC
(JD 1922011.0857922453) results in placing the Galactic Center at the
middle of Mūlā nakshatra (6°40’).

[This post from Ernst Wilhelm][2] suggests to set the middle-Mula-ayanamsa to
20°11'11" on 1/1/2000. This also results in 6°39.5’

```
julday = swe.julday(2000, 1, 1)
swe.set_sid_mode(swe.SIDM_USER, julday, 20 + 11/60. + 11./3600)
galc = swe.fixstar_ut("Gal. Center", julday, flag = swe.FLG_SIDEREAL); to_dms_prec(galc[0] % 30)
   [6, 39, 34.830456]
```

## TRUE_CITRA and TRUE_REVATI

### Revati at 359°50’

The Suryasiddhanta also mentions that Revati/zeta-Piscium is exactly at 359°50’
in polar ecliptic longitude (projection onto the ecliptic along
meridians). So, according to SS_REVATI:

```
jd = swe.julday(499, 3, 21, 7 + 30/60. + 21.57/3600)
swe.set_sid_mode(swe.SIDM_USER, jd, -0.79167046)
galc = swe.fixstar_ut("Revati", jd, flag = swe.FLG_SIDEREAL)
to_dms_prec(galc[0])
    [359, 43, 18.397513]
```

which is off by 7'18.4". Once again, we can do bisection search to find the
zero-point of Revati@359°50’:

```
jd = swe.julday(563, 7, 20, 19 + 16/60. + 2.17/3600)
swe.set_sid_mode(swe.SIDM_USER, jd, 0.0)
galc = swe.fixstar_ut("Revati", jd, flag = swe.FLG_SIDEREAL | swe.FLG_SWIEPH)
to_dms_prec(galc[0])
    [359, 49, 60.0]   # == 359°50'00'
```

This date of 20 Jul 563 is tantalizingly close to Sassanian 20 Mar 564.

Note that selecting `swe.SIDM_TRUE_REVATI` places Revati at exactly 360°(=0°)
(instead of 359°50' like SS wants). It's zero-point is in 575 AD:

```
jd = swe.julday(575, 7, 18, 12 + 52/60. + 12.87/3600)
swe.set_sid_mode(swe.SIDM_USER, jd, 0.0)
galc = swe.fixstar_ut("Revati", jd, flag = swe.FLG_SIDEREAL | swe.FLG_SWIEPH)
to_dms_prec(galc[0])
    [359, 59, 60.0]   # == 360°00'00' = 0°
```

This Revati-at-zero is also mentioned in Siddhanta Siromani.

### True Citra

A similar bisection search for Citra/Spica to be exactly 180° reveals:

```
julday = swe.julday(285, 1, 30, 11 + 55/60. + 10.92/3600)
swe.set_sid_mode(swe.SIDM_USER, julday, 0.0)
galc = swe.fixstar_ut("Citra", julday, flag = swe.FLG_SIDEREAL | swe.FLG_SWIEPH)
galc[0]
    179.99999999999895
```

This date of 30 Jan 285 is very close to `swe.SIDM_TRUE_CITRA`'s 04 Oct 285 and
`swe.SIDM_LAHIRI`'s 03 Sep 285. It is preferable to use SIDM_TRUE_CITRA because
it seems to give better precision:

```
julday = 1825430.71351322  # TRUE_CITRA's zero day
swe.set_sid_mode(swe.SIDM_TRUE_CITRA)
galc = swe.fixstar_ut("Citra", julday, flag = swe.FLG_SIDEREAL | swe.FLG_SWIEPH)
galc[0]
    179.99999999999994
```

### True Pushya

Surya Siddhanta mentions that Puṣya Nakṣatra (delta Cancri) is at 106°. This is
also proposed by P V R Narasimha Rao. Once again, bisection search reveals the
zero-point ayanamsa in 368 AD:

```
jd = swe.julday(368, 10, 28, 21 + 49/60. + 15.09/3600) # TRUE_PUSHYA's zero day
swe.set_sid_mode(swe.SIDM_USER, jd, 0.0)
galc = swe.fixstar_ut(",deCnc", jd, flag = swe.FLG_SIDEREAL | swe.FLG_SWIEPH)
to_dms_prec(galc[0])
    [106, 0, 0.0]
```

## Summary

All these methods try to put zero point between 10 minutes and 20 minutes east
of zeta Piscium:

```
                                 t0              Position of zeta-Piscium
                                                  on JD 2457288.0
Hipparchan                  09 Nov 545                [359, 38, 8.060755]
Gal. Center@mid-Mūlā        09 Mar 550                [359, 41, 44.291252]
SS Revati                   05 Apr 556                [359, 46, 47.905798]
Ushashashi                  23 Jul 559                [359, 49, 32.962578]
Revati@359°50'              20 Jul 563                [359, 52, 52.125081]
Sassanian                   20 Mar 564                [359, 53, 25.4508901]
True Revati@0°              18 Jul 575                [0, 2, 51.516834]
```

SS Revati or Ushashashi seems to be a good middle-ground. Everybody seems to
have become familiar with Ushashashi only due to Swiss Ephemeris.


### Miscellaneous Dates

(All dates are proleptic Gregorian)

Beginning of Kali Yuga = 23 Jan, -3102 (JD 588466)

#### Krishna

Lord Krishna's birthday is on śrāvaṇa-māsa-kṛṣṇa-pakṣa-aṣṭamī with Rohiṇī
nakṣatra, born at midnight. 23(24) Jun, -3227 (JD 542596.54167). Location:
Mathura (27.502°N, 77.683°E) -- this is using any Citra-pakṣa ayanāmśa
(Lahiri/Raman/`SS_CITRA`/`TRUE_CITRA`) but also with Yukteshwar and
GalCent_0SAG. Kali-Ahargana = -45869 days ~ 125.58 yrs.

If you use a Revati-pakṣa (`SS_REVATI`/`TRUE_REVATI`/`USHASHASHI`/`SASSANIAN`)
you get adhika-bhādrapada instead of śrāvaṇa. But it is still rohiṇī and
kṛṣṇa-pakṣa-aṣṭamī. However, changing the date to 13 Jun, -3226 we get an exact
match with these ayanāmśas as well. Kali-Ahargana = -45515 days ~ 124.61 yrs.

If you use Krishnamurti ayanāmśa, you get Ārdrā instead of Rohiṇī.

#### Buddha

Lord Gautama Buddha's birthday is claimed as Vaishakha Masa Purnima, Tuesday, at
about mid-day near Lumbini (27.484N, 83.276E). Modern historians place him in
563 BCE. Some (ex UNESCO) place him in 623 BCE.

Using `SS_REVATI` or `TRUE_REVATI` gives the date as 23 Mar -561 which matches
the above exactly. Taking -562 gives Thursday and -563 gives Sunday :(
It's interesting that 20 Mar -623 is adhika-vaishaka-masa but Thursday. 18 Apr
-623 is "normal" Vaishakha but Friday.
-624 gives Saturday, 8 Apr -622 gives Wednesday. 28 Mar -621 gives Sunday.

`SS_REVATI`: 7 Apr -622, Tuesday, Caturdasi ends after mid-day (12:21:06).
`USHASHASHI`: 7 Apr -622, Tuesday, Caturdasi ends after mid-day (12:06:06).
`TRUE_REVATI`: 7 Apr -622, Tuesday, Caturdasi ends after mid-day (12:21:06).

#### Adi Shankara

Traditional records claim he was born vaisakha-sukla-pancami, punarvasu,
bhanuvara around mid-day.

`SS_REVATI`: 19 Apr 788 CE has punarvasu after 11:45 AM and matches well, except
that it is Tuesday instead of Sunday. The very next year (9 Apr 789 CE),
vaisakha-sukla-pancami is indeed Sunday, but Ardra until Monday morning 4 AM.

#### Caitanya Mahaprabhu

His planetary positions are [known][cait]. He was born on Phalguna-purnima
purvaphalguni nakshatra, around evening time in Simha lagna. According to
`SS_REVATI`, for Simha lagna (~15:45 to 17:45) duration, all other planetary
positions match, except that Rahu is in Meena instead of Kumbha. Same fate with
Ushashashi, True Revati, etc.

The popular ones match correctly all positions (Lahiri, Raman, KP, True
Citra). Strangely enough, GALCENT_0SAG also matches!


[cait]: http://www.dandavats.com/?p=8193

##### Misc code
```python
def galc_center(jd, mode):
    swe.set_sid_mode(mode)
    galc = swe.fixstar_ut("Gal. Center", jd, flag = swe.FLG_SIDEREAL | swe.FLG_SWIEPH | swe.FLG_NOABERR)
    return to_dms_prec(galc[0] % 30)
```

#### Julian to Gregorian date conversion in Swiss Eph

Generally years before 1582 are quoted in (proleptic) Julian, not Gregorian.
You can use `swe.date_conversion()` first and then apply `swe.revjul()`.

For example: `21 Mar 499, 7:30:31.57 UT` actually means it is Julian date
because 499 AD < 1582 AD.

```python
swe.date_conversion(499, 3, 21, 7 + 30/60. + 31.57/3600., 'j')   # [j]ulian
    (0, 1903396.8128653935)

swe.revjul(_[1], swe.GREG_CAL)
    (499, 3, 22, 7.508769443258643)
```

So, 21 Mar became 22 Mar, just one day off.

Similarly, Kali Yuga began on February 17/18, 3102 BC. Note that whenever BC is
given, you've to substract 1 from it (irrespective of Gregorian/Julian). So 3102
BC = -3101

```python
swe.date_conversion(-3101, 2, 18, cal = 'j')
    (0, 588466.0)

swe.revjul(_[1], swe.GREG_CAL)
    (-3101, 1, 23, 12.0)

ahargana(588466)
    0.5
```

Now 18 Feb 3102 BC (julian) became 23 Jan 3102 BC (greg)!
