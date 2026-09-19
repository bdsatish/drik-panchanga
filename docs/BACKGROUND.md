Background and references
=========================

About the calendar
------------------

There are two schools of Indian calendar makers:

1. Those who follow the rules of the [_Sūrya Siddhāntā_](http://en.wikipedia.org/wiki/Surya_Siddhanta)
   (SS, Theory of the Sun) or its variants like _Ārya Siddhānta_ of Aryabhata.
2. Those who follow the _Dṛk Siddhāntā_ (Empirical Theory).

SS contains semi-analytical equations for specifying the positions of sun and moon.
However, the constants in these equations have to be updated regularly ( _bīja saṃskāra_ ).
But the equations in SS were last updated around 1000 CE, so they no longer match the
planetary positions as we see today. For example, the date of solar eclipse as predicted
by the equations of SS are off by many hours from its actual occurence. In spite of this,
most Hindu maṭhas still publish yearly pañcāṅgas according to the rules of SS, in the name
of preserving and practising tradition ( _paramparā_ ).

The latter one, _Drik_ school, still follow the general concepts from SS,
but get the planetary positions from measured or observed data (dṛś = to see).
Hence, their results match accurately with observed celestial phenomena.
The [Swiss Ephemeris](http://www.astro.com/swisseph/swephinfo_e.htm) is probably
the best source available today for planetary calculations. It provides highly
accurate databases of planetary data for about 10000 years. Hence, this panchanga
is based on the Swiss Ephemeris. Other databases include those published by NASA's
JPL (DE405) or the Moshier ephemeris.

### Śubhāśubha Samaya

Gaurī (Gowri) Panchanga and Choghadiya are south Indian and north Indian names
respectively, for the same mathematical calculation. Basically, day and night
duration are each divided into eight parts; the difference between N.Indian and
S.Indian lies in their names and which part is considered
auspicious/inauspicious. In the S.Indian variant, Tamilians use
[different order][kowri] and names compared to Kannadigas/Telugus. This program
provides the latter only.

Rāhukāla, Yamagaṇḍakāla, Gulikakāla, Durmuhūrtams and Varjyam are all considered
inauspicious. Abhijit muhūrta and Amṛtakāla are considered auspicious.

[kowri]: http://tamilastrology.hosuronline.com/KowriPanchangam/

### Uranus and Neptune

These planets were not discovered by Indian astronomers. They are sometimes
translated as "[Aruṇa graha][ar_hi]" and "[Varuṇa graha][va_hi]" in languages
like Hindi, Nepali, etc. Problem is that there is another trans-Neptunian
planet which is also called [Varuna][v20k] in English.

The Positional Astronomy Center [translates][pac] them as `हर्शल` and
`नेपच्यून`. This is inconsistent in the sense that Uranus was translated after its
discoverer (William Herschel) where as Neptune was phonetically transcribed from
English, instead of basing on its discoverer (Johann Galle). Therefore, I've
"Indianized" their names in a rhyming fashion as **`हर्षल`** (=Uranus) and
**`गाल्ल`** (=Neptune). They also mean "happy" and "cheek/chin" respectively in
many Indian languages.

Other probable names are: हिमनील (=icy-blue, Uranus), इन्द्रनील
(=sapphire-colored, Neptune), तुषार (=frigid), पलाश (=green).

[ar_hi]: https://hi.wikipedia.org/wiki/अरुण_(ग्रह)
[va_hi]: https://hi.wikipedia.org/wiki/वरुण_(ग्रह)
[pac]: http://www.packolkata.gov.in/download/hindi/Page_020.jpg
[v20k]: https://en.wikipedia.org/wiki/20000_Varuna

References
----------

These ones are helpful for implementing panchanga software:

* Karanam Ramakumar, [_Panchangam Calculations_](http://archive.org/details/PanchangamCalculations)
* [_Second Level of the Astronomical Calculations in GCAL_](http://www.krishnadays.com/eng/index.php?option=com_docman&task=doc_download&gid=7&Itemid=58),
  used in ISKCON's GCal software.
* Dershowitz and Reingold, _Calendrical Calculations_, 3rd edition, 2008.
  [Online Java applet](http://emr.cs.iit.edu/home/reingold/calendar-book/Calendrica.html).
* Shayamasundara Dasa, [_Vimsottari Year -- 360 or 365 ?_](http://shyamasundaradasa.com/jyotish/resources/articles/pdf_versions/english/360_vs_365.pdf)

Similar software
----------------

Prof. M. Yanom's [online interface](http://www.cc.kyoto-su.ac.jp/~yanom/pancanga/)
to his [Perl code](http://www.cc.kyoto-su.ac.jp/~yanom/sanskrit/pancanga/pancanga3.13) —
the best implementation of the old Surya Siddhanta panchanga; however, the SS system
itself is not accurate for dates several centuries before our time.

[drikpanchang](http://drikpanchang.com) is a reliable online Drik calendar, but neither
open source nor offering a desktop program. It doesn't work for dates before 1600 CE;
their [Android app](https://play.google.com/store/apps/details?id=com.drikp.core)
doesn't work outside 1900–2100 CE.

[Hindu Calendar](https://play.google.com/store/apps/details?id=com.alokmandavgane.hinducalendar)
for Android is another offline Drik calendar by Alok Mandavgane. Not open source; it
has a DST bug in Europe and doesn't work outside 1900–2100 CE.

Among open source programs:

* [On Google Code](http://panchangam.googlecode.com/svn/calc-v2): generates a PDF
  panchanga for any year and place, but imprecise (tithi end times off by ~10 min).
  No GUI.
* [On GitHub](https://github.com/santhoshn/panchanga): based on Paul Schlyter's
  semi-analytical model for [planetary positions](http://stjarnhimlen.se/comp/ppcomp.html).
  Computes the panchanga for a given _instant_ but doesn't ask for a place's
  coordinates or timezone (it doesn't compute sunrise timings at all). The
  planetary model fails outside 1800–2100 CE.

CLI extras
----------

The CLI also computes (not yet in the Web UI): instantaneous planetary
positions including Lagna (Ascendant), Navamsa positions, Choghadiya/Gauri
panchanga, Vimsottari Dasha-Bhukti, Rahu Kala, Yamaganda Kala, Gulika Kala,
Abhijit muhurta and Durmuhurtams.

TODO
----

* Amritakala
* gettext translations
* Harmonize all functions to use UT aka UT1 instead of UTC or ET
  (`swe.jdut1_to_utc() <==> swe.utc_to_jd()[1]`, `swe.utc_time_zone()`, etc.)
