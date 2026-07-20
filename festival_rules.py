"""Stub festival API consumed by the PDF calendar generator.

The previous multi-policy implementation lives under ``experimental/`` for
reference. This module deliberately returns empty festival and Ekadashi
results so calendars still generate while a clean-slate algorithm is built.
"""


def resolve_festivals(
    months,
    month_data,
    *,
    context_months=None,
    context_data=None,
    geopos=None,
):
    """Return no festivals until the clean-slate algorithm is implemented."""
    return {}, []


def resolve_ekadashi_dates(months, month_data):
    """Return no Ekadashi dates until the clean-slate algorithm is implemented."""
    return []
