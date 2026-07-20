"""Festival catalog, stable numbering, and rule metadata."""

from .model import FestivalRule


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
        "Akshaya Tritiya",
        2,
        "S3",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80421210038/view",
    ),
    # No Vasavi/Kanyaka Parameshwari observance was found in Dharma Sindhu.
    # Resolve the supplied community tithi with the generic udaya policy.
    FestivalRule(4, "Vasavi Jayanti", 2, "S10", "generic-udaya"),
    FestivalRule(
        5,
        "Narasimha Jayanti",
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
        "Naga Panchami",
        5,
        "S5",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80422074237/view",
    ),
    FestivalRule(
        9,
        "Rig Upakarma",
        5,
        "Shravana nakshatra",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80422074617/view",
    ),
    FestivalRule(
        10,
        "Yajur Upakarma",
        5,
        "S15",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80421215029/view",
        True,
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
        "Swarna Gowri Vrata",
        6,
        "S3",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80503220901/view",
    ),
    FestivalRule(
        14,
        "Ganesha Chaturthi",
        6,
        "S4",
        "dharmasindhu",
        "https://www.kamakoti.org/kamakoti/dharmasindhu/bookview.php?chapnum=7",
    ),
    FestivalRule(
        15,
        "Mahalaya Amavasya",
        6,
        "K15",
        "dharmasindhu",
        "http://hindupanchang.blogspot.com/2008/03/",
    ),
    FestivalRule(
        16,
        "Durga Ashtami",
        7,
        "S8",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80501061410/view",
    ),
    FestivalRule(
        17,
        "Durga Ashtami (Puja)",
        7,
        "S8",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80501061410/view",
    ),
    FestivalRule(
        18,
        "Ayudha Puja",
        7,
        "S9",
        "regional",
        (
            "https://www.drikpanchang.com/navratri/durga-puja/"
            "ayudha-puja-date-time.html"
        ),
    ),
    FestivalRule(
        19,
        "Mahanavami (Puja)",
        7,
        "S9",
        "dharmasindhu",
        (
            "https://www.drikpanchang.com/navratri/durga-puja/"
            "bengal/maha-navami-date-time.html"
        ),
    ),
    FestivalRule(
        20,
        "Vijayadashami (Puja)",
        7,
        "S10",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80501062120/view",
    ),
    FestivalRule(21, "Dasara", 7, "S10", "regional"),
    FestivalRule(
        22,
        "Dhana Trayodashi",
        7,
        "K13",
        "dharmasindhu",
        "https://nepaljyotish.org/en/blog/dharmasindhu-vrata-nirnaya/",
    ),
    FestivalRule(
        23,
        "Naraka Chaturdashi",
        7,
        "K14",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80505062049/view",
    ),
    FestivalRule(
        24,
        "Deepavali",
        7,
        "K15",
        "dharmasindhu",
        "https://www.kamakoti.org/kamakoti/dharmasindhu/bookview.php?chapnum=8",
    ),
    FestivalRule(
        25,
        "Bali Padyami",
        8,
        "S1",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80505062407/view",
    ),
    FestivalRule(26, "Gita Jayanti", 9, "S11", "generic-udaya"),
    FestivalRule(
        27,
        "Vaikuntha Ekadashi",
        9,
        "Dhanur-masa S11",
        "regional",
        (
            "https://www.drikpanchang.com/ekadashis/vaikuntha/"
            "vaikuntha-ekadashi-date-time.html"
        ),
        allow_empty=True,
    ),
    FestivalRule(
        28,
        "Makara Sankranti",
        0,
        "Solar",
        "dharmasindhu",
        "https://www.kamakoti.org/kamakoti/dharmasindhu/bookview.php?chapnum=11",
    ),
    FestivalRule(29, "Vasavi Atmarpana", 11, "S2", "generic-udaya"),
    FestivalRule(
        30,
        "Vasanta Panchami",
        11,
        "S5",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80513003421/view",
    ),
    FestivalRule(
        31,
        "Ratha Saptami",
        11,
        "S7",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80513004113/view",
    ),
    FestivalRule(32, "VSN Jayanti", 11, "S11", "generic-udaya"),
    FestivalRule(
        33,
        "Maha Shivaratri",
        11,
        "K14",
        "dharmasindhu",
        "https://www.transliteral.org/pages/z80513005728/view",
    ),
    FestivalRule(
        34,
        "Kama Dahana (Holi)",
        12,
        "S15",
        "dharmasindhu",
        "https://www.kamakoti.org/kamakoti/dharmasindhu/bookview.php?chapnum=13",
    ),
    FestivalRule(35, "Dhanvantari Jayanti", 7, "K13", "regional"),
)

# TTD preference: use the last Friday strictly before non-adhika Shravana
# Purnima, independently of Upakarma deferrals.
VARAMAHALAKSHMI_RULE = FestivalRule(
    8,
    "Varamahalakshmi Vrata",
    5,
    "Last Friday strictly before S15",
    "regional",
)
VARAMAHALAKSHMI_NUMBER = VARAMAHALAKSHMI_RULE.number
VARAMAHALAKSHMI_NAME = VARAMAHALAKSHMI_RULE.name

UGADI_NUMBER = 1
RAMA_NAVAMI_NUMBER = 2
AKSAYA_TRTIYA_NUMBER = 3
VASAVI_JAYANTI_NUMBER = 4
NARASIMHA_JAYANTI_NUMBER = 5
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
DURGA_ASHTAMI_PUJA_NUMBER = 17
AYUDHA_PUJA_NUMBER = 18
MAHANAVAMI_PUJA_NUMBER = 19
VIJAYA_DASAMI_NUMBER = 20
DASARA_NUMBER = 21
DHANA_TRAYODASHI_NUMBER = 22
NARAKA_CHATURDASHI_NUMBER = 23
DEEPAVALI_NUMBER = 24
BALI_PADYAMI_NUMBER = 25
GITA_JAYANTI_NUMBER = 26
VAIKUNTHA_EKADASHI_NUMBER = 27
MAKARA_SANKRANTI_NUMBER = 28
VASAVI_ATMARPANA_NUMBER = 29
VASANTA_PANCHAMI_NUMBER = 30
RATHA_SAPTAMI_NUMBER = 31
VSN_JAYANTI_NUMBER = 32
MAHA_SHIVARATRI_NUMBER = 33
KAMA_DAHANA_NUMBER = 34
DHANVANTARI_JAYANTI_NUMBER = 35
