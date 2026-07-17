"""Shared festival rule types and policy identifiers."""

from dataclasses import dataclass


TRADITIONAL_FESTIVAL_POLICY = "traditional"
GENERIC_UDAYA_FESTIVAL_POLICY = "generic-udaya"
GENERIC_MIDPOINT_FESTIVAL_POLICY = "generic-midpoint"
GENERIC_KALA_FESTIVAL_POLICY = "generic-kala"
GENERIC_ANCHOR_FESTIVAL_POLICY = "generic-anchor"
FESTIVAL_POLICIES = (
    TRADITIONAL_FESTIVAL_POLICY,
    GENERIC_UDAYA_FESTIVAL_POLICY,
    GENERIC_MIDPOINT_FESTIVAL_POLICY,
    GENERIC_KALA_FESTIVAL_POLICY,
    GENERIC_ANCHOR_FESTIVAL_POLICY,
)


@dataclass(frozen=True)
class FestivalRule:
    number: int
    name: str
    masa: int
    tithi: str
    status: str = "provisional"
    source: str | None = None
    allow_empty: bool = False


@dataclass(frozen=True)
class GenericKalaValidityOverlay:
    """Post-selection constraint and same-policy fallback definition."""

    validator: str
    fallback_masa_offset: int | None = None
