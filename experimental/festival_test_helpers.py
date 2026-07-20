"""Shared builders used by focused festival-rule test modules."""

from experimental.festival_rules import FESTIVAL_RULES


def record(day, tithi, masa="1", is_adhika=False):
    """Build the compact record shape consumed by festival selectors."""
    return (day, tithi, masa, is_adhika, 1.0, 0.0, 0.5)


def festival_rule(name):
    """Return one catalog rule by its public display name."""
    return next(rule for rule in FESTIVAL_RULES if rule.name == name)
