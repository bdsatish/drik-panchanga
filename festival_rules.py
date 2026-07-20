"""Stub festival API consumed by the PDF calendar generator.

The previous multi-policy implementation lives under ``experimental/`` for
reference. This module deliberately returns empty festival and Ekadashi
results so calendars still generate while a clean-slate algorithm is built.
"""

TRADITIONAL_FESTIVAL_POLICY = "traditional"
FESTIVAL_POLICIES = (TRADITIONAL_FESTIVAL_POLICY,)

# Numerically stable exclusion markers retained from the archived catalog.
RAKSHA_BANDHAN_NUMBER = 11
DURGA_ASHTAMI_NUMBER = 16
AYUDHA_PUJA_NUMBER = 18
MAHANAVAMI_PUJA_NUMBER = 19
VIJAYA_DASAMI_NUMBER = 20
DASARA_NUMBER = 21
GITA_JAYANTI_NUMBER = 26
DHANVANTARI_JAYANTI_NUMBER = 35


def resolve_festivals(
    months,
    month_data,
    festival_policy=TRADITIONAL_FESTIVAL_POLICY,
    *,
    context_months=None,
    context_data=None,
    geopos=None,
):
    """Return no festivals until the clean-slate algorithm is implemented."""
    if festival_policy not in FESTIVAL_POLICIES:
        raise ValueError(f"Unknown festival policy: {festival_policy}")
    return {}, []


def resolve_dharma_sindhu_vaishnava_ekadashi_dates(months, month_data):
    """Return no Ekadashi dates until the clean-slate algorithm is implemented."""
    return []
