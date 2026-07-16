"""
test_resolution.py — ER-1.2 gate evidence (G-ER-1 full, G-ER-2 loader half).

Replaces the ER-1.1 scratchpad gate tool: enforcement now lives in the real loader,
so the gates run in CI-able tests instead of a throwaway script.

Every negative test mutates the REAL tree in memory and asserts the loader FAILS
LOUD. A check that cannot fail proves nothing — each fault class is injected
individually, and the positive control (§G-ER-1 real tree) proves the tree is clean
without them.
"""
import unittest

from _loader import resolution, validate
from _loader.tests.common import load_unvalidated


class TestNormalization(unittest.TestCase):
    """G-ER-2 (loader half) — the frozen D-ER-8 spec, table-driven."""

    def test_canonical_phrase_set(self):
        cases = [
            ("Impresora 3D",        "impresora 3d"),   # casefold
            ("  Toldo  ",           "toldo"),          # trim
            ("Conexión a Internet", "conexion a internet"),   # NFKD + strip marks
            ("impresora_3d",        "impresora 3d"),   # separator collapse (_)
            ("main-door",           "main door"),      # separator collapse (-)
            ("switch.impresora_3d", "switch impresora 3d"),   # `.` collapses to space
            ("ZIGBEE   MESH",       "zigbee mesh"),    # whitespace run collapse
            ("año",                 "ano"),            # ñ -> n, accepted by D-ER-8
        ]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                self.assertEqual(resolution.normalize_alias(raw), expected)

    def test_normalization_is_idempotent(self):
        for raw in ("Impresora 3D", "Conexión a Internet", "  main-door  "):
            once = resolution.normalize_alias(raw)
            self.assertEqual(resolution.normalize_alias(once), once)

    def test_normalized_alias_is_never_id_shaped(self):
        # Why 12c tests the RAW string: normalization collapses `.` to a space.
        self.assertNotIn(".", resolution.normalize_alias("switch.impresora_3d"))


class TestAliasValidation(unittest.TestCase):
    """G-ER-1 — fail-loud enforcement of check 12 (schema §5.1)."""

    def test_real_tree_is_valid(self):
        entities, arch, reg = load_unvalidated()
        validate.validate(entities, arch, reg)          # must not raise

    def test_own_entity_id_alias_is_allowed(self):
        """D-ER-12 converse — the rule that 4 of the 6 bound entities depend on.
        `awning` aliases "awning"; `main-door` aliases "main door". Rejecting these
        would gut English coverage for no safety gain."""
        entities, arch, reg = load_unvalidated()
        by = {e.id: e for e in entities}
        for eid, alias in (("awning", "awning"), ("main-door", "main door"),
                           ("internet-uplink", "internet uplink")):
            norm = resolution.normalize_alias(eid)
            self.assertEqual(norm, alias)
            self.assertIn(alias, [n for _, n in by[eid].aliases_normalized["state"]])
        validate.validate(entities, arch, reg)          # must not raise

    def test_duplicate_normalized_alias_rejected(self):
        entities, arch, reg = load_unvalidated()
        by = {e.id: e for e in entities}
        # "Toldo" normalizes onto awning's existing "toldo".
        by["main-door"].fm["aliases"] = ["Toldo"]
        by["main-door"].aliases_normalized = resolution.normalized_pairs(by["main-door"])
        with self.assertRaises(validate.ValidationError) as cm:
            validate.validate(entities, arch, reg)
        self.assertIn("12d", str(cm.exception))
        self.assertIn("toldo", str(cm.exception))

    def test_archetype_level_alias_rejected(self):
        entities, arch, reg = load_unvalidated()
        arch["zigbee-device"].defaults["aliases"] = ["ghost"]
        with self.assertRaises(validate.ValidationError) as cm:
            validate.validate(entities, arch, reg)
        self.assertIn("12f", str(cm.exception))

    def test_id_shaped_alias_rejected(self):
        entities, arch, reg = load_unvalidated()
        by = {e.id: e for e in entities}
        by["awning"].fm["aliases"] = ["cover.toldo"]
        by["awning"].aliases_normalized = resolution.normalized_pairs(by["awning"])
        with self.assertRaises(validate.ValidationError) as cm:
            validate.validate(entities, arch, reg)
        self.assertIn("12c", str(cm.exception))

    def test_cross_entity_id_collision_rejected(self):
        """12e / D-ER-12 — isolated with a NON-aliased entity id so 12d cannot mask it."""
        entities, arch, reg = load_unvalidated()
        by = {e.id: e for e in entities}
        by["printer-3d"].fm["aliases"] = ["entrance plant"]
        by["printer-3d"].aliases_normalized = resolution.normalized_pairs(by["printer-3d"])
        with self.assertRaises(validate.ValidationError) as cm:
            validate.validate(entities, arch, reg)
        self.assertIn("12e", str(cm.exception))
        self.assertIn("entrance-plant", str(cm.exception))

    def test_aliases_on_unbound_entity_rejected(self):
        entities, arch, reg = load_unvalidated()
        by = {e.id: e for e in entities}
        by["battery"].fm["aliases"] = ["bateria"]       # aspect: no binding (D-ER-6)
        with self.assertRaises(validate.ValidationError) as cm:
            validate.validate(entities, arch, reg)
        self.assertIn("no binding", str(cm.exception))

    def test_flat_list_on_multi_signal_rejected(self):
        """D-ER-11 — no implicit `state` on a multi-signal binding."""
        entities, arch, reg = load_unvalidated()
        by = {e.id: e for e in entities}
        by["zigbee-mesh"].fm["aliases"] = ["malla"]
        with self.assertRaises(validate.ValidationError) as cm:
            validate.validate(entities, arch, reg)
        self.assertIn("per-signal alias map", str(cm.exception))

    def test_map_on_single_signal_rejected(self):
        entities, arch, reg = load_unvalidated()
        by = {e.id: e for e in entities}
        by["printer-3d"].fm["aliases"] = {"state": ["impresora"]}
        with self.assertRaises(validate.ValidationError) as cm:
            validate.validate(entities, arch, reg)
        self.assertIn("flat alias list", str(cm.exception))

    def test_undeclared_signal_key_rejected(self):
        entities, arch, reg = load_unvalidated()
        by = {e.id: e for e in entities}
        by["zigbee-mesh"].fm["aliases"] = {"not_a_signal": ["x y"]}
        with self.assertRaises(validate.ValidationError) as cm:
            validate.validate(entities, arch, reg)
        self.assertIn("not a declared", str(cm.exception))

    def test_alias_bounds_rejected(self):
        entities, arch, reg = load_unvalidated()
        by = {e.id: e for e in entities}
        by["awning"].fm["aliases"] = ["x"]              # 1 char after normalization
        by["awning"].aliases_normalized = resolution.normalized_pairs(by["awning"])
        with self.assertRaises(validate.ValidationError) as cm:
            validate.validate(entities, arch, reg)
        self.assertIn("12b", str(cm.exception))


class TestResolutionRegistry(unittest.TestCase):
    """The emitted registry (additive) — shape, determinism, and what it must NOT carry."""

    def setUp(self):
        from _loader import normalize
        entities, arch, reg = load_unvalidated()
        self.entities = normalize.normalize(entities, reg)
        self.res = resolution.build(self.entities)

    def test_real_model_registry(self):
        self.assertEqual(self.res["stats"]["entities"], 6)
        self.assertEqual(self.res["stats"]["aliases"], len(self.res["aliases"]))
        self.assertEqual(self.res["stats"]["targets"], len(self.res["targets"]))

    def test_aliases_resolve_to_real_targets(self):
        self.assertEqual(self.res["aliases"]["impresora 3d"], "switch.impresora_3d")
        self.assertEqual(self.res["aliases"]["3d printer"], "switch.impresora_3d")
        self.assertEqual(self.res["aliases"]["toldo"], "cover.toldo")
        self.assertEqual(self.res["aliases"]["awning"], "cover.toldo")
        # D-ER-11: multi-signal resolves per signal, never to an entity default.
        self.assertEqual(self.res["aliases"]["permit join"],
                         "switch.zigbee2mqtt_bridge_permit_join")
        self.assertEqual(self.res["aliases"]["zigbee mesh"],
                         "binary_sensor.zigbee2mqtt_bridge_connection_state")

    def test_every_alias_target_exists_in_targets(self):
        for _, eid in self.res["aliases"].items():
            self.assertIn(eid, self.res["targets"])

    def test_registry_carries_no_authorization_field(self):
        """D-ER-9 / INV-17 — structurally un-mistakable for an allowlist. The printer
        is the one `writable: true` entity; its target must still carry no grant."""
        for eid, t in self.res["targets"].items():
            for forbidden in ("writable", "boundary", "authorization", "allowed"):
                self.assertNotIn(forbidden, t, f"{eid} leaks {forbidden!r}")

    def test_ambiguous_bare_name_is_not_aliased(self):
        """A bare "planta"/"plant" maps to two signals of entrance-plant with no
        non-arbitrary winner — a closed resolver must never guess."""
        for norm in ("planta", "plant"):
            self.assertNotIn(norm, self.res["aliases"])

    def test_normalization_stamp_present(self):
        self.assertEqual(self.res["normalization"], resolution.NORMALIZATION)

    def test_deterministic_and_sorted(self):
        from _loader import normalize
        entities2, _, reg2 = load_unvalidated()
        res2 = resolution.build(normalize.normalize(entities2, reg2))
        self.assertEqual(self.res, res2)
        self.assertEqual(list(self.res["aliases"]), sorted(self.res["aliases"]))
        self.assertEqual(list(self.res["targets"]), sorted(self.res["targets"]))


class TestArtifactIntegration(unittest.TestCase):
    """G-ER-5 (loader half) — additive only; ARTIFACT_VERSION must not move."""

    def test_artifact_version_still_1(self):
        from _loader import cli
        a = cli.build_artifact(reproducible=True)
        self.assertEqual(a["artifact_version"], 1)

    def test_resolution_is_additive_and_entities_untouched(self):
        from _loader import cli
        a = cli.build_artifact(reproducible=True)
        self.assertIn("resolution", a)
        # The awareness-bearing sections must not gain alias data.
        for eid, e in a["entities"].items():
            self.assertNotIn("aliases", e, f"{eid} leaked aliases into the entity block")


if __name__ == "__main__":
    unittest.main()
