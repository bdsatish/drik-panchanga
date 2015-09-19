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
