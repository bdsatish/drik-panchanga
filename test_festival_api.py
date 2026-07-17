"""Compatibility tests for the public ``festival_rules`` facade."""

from dataclasses import fields
import inspect
import unittest

import festival_rules
from _festival_rules import catalog, config, model


class FestivalRulesApiTests(unittest.TestCase):
    def test_policy_values_and_order_remain_public(self):
        self.assertEqual(
            festival_rules.FESTIVAL_POLICIES,
            (
                "traditional",
                "generic-udaya",
                "generic-midpoint",
                "generic-kala",
                "generic-anchor",
            ),
        )

    def test_rule_and_overlay_field_order_is_stable(self):
        self.assertEqual(
            [field.name for field in fields(festival_rules.FestivalRule)],
            [
                "number",
                "name",
                "masa",
                "tithi",
                "status",
                "source",
                "allow_empty",
            ],
        )
        self.assertEqual(
            [
                field.name
                for field in fields(
                    festival_rules.GenericKalaValidityOverlay
                )
            ],
            ["validator", "fallback_masa_offset"],
        )

    def test_compatibility_aliases_retain_identity(self):
        self.assertIs(
            festival_rules.RATRI_KALA,
            festival_rules.MADHYARATRI_KALA,
        )
        self.assertIs(
            festival_rules.PURVODAYA_KALA,
            festival_rules.ARUNODAYA_KALA,
        )

    def test_facade_reexports_private_definition_objects(self):
        self.assertIs(festival_rules.FestivalRule, model.FestivalRule)
        self.assertIs(festival_rules.FESTIVAL_RULES, catalog.FESTIVAL_RULES)
        self.assertIs(
            festival_rules.GENERIC_KALA_BY_FESTIVAL,
            config.GENERIC_KALA_BY_FESTIVAL,
        )

    def test_calendar_generator_dependencies_remain_exported(self):
        names = {
            "FESTIVAL_POLICIES",
            "GENERIC_ANCHOR_FESTIVAL_POLICY",
            "GENERIC_KALA_FESTIVAL_POLICY",
            "GENERIC_MIDPOINT_FESTIVAL_POLICY",
            "GENERIC_UDAYA_FESTIVAL_POLICY",
            "TRADITIONAL_FESTIVAL_POLICY",
            "resolve_dharma_sindhu_vaishnava_ekadashi_dates",
            "resolve_festivals",
            "GITA_JAYANTI_NUMBER",
            "DHANVANTARI_JAYANTI_NUMBER",
            "MAHANAVAMI_PUJA_NUMBER",
            "VIJAYA_DASAMI_NUMBER",
            "DASARA_NUMBER",
            "AYUDHA_PUJA_NUMBER",
            "DURGA_ASHTAMI_NUMBER",
            "RAKSHA_BANDHAN_NUMBER",
        }
        self.assertFalse(names - set(dir(festival_rules)))

    def test_resolver_signature_is_stable(self):
        self.assertEqual(
            str(inspect.signature(festival_rules.resolve_festivals)),
            (
                "(months, month_data, festival_policy='traditional', *, "
                "context_months=None, context_data=None, geopos=None)"
            ),
        )


if __name__ == "__main__":
    unittest.main()
