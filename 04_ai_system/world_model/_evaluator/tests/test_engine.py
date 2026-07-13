"""Unit tests for the AST core + adapter semantics (D7, N1, windows, duration)."""

import unittest
from datetime import datetime, timedelta, timezone

from _evaluator import engine

WINDOWS = {"overnight": {"tz": "Europe/Madrid", "start_min": 0, "end_min": 360, "half_open": True}}
NOW = datetime(2026, 7, 2, 10, 0, tzinfo=timezone.utc)          # 12:00 Europe/Madrid (CEST)


def ctx(states: dict, field_map: dict | None = None, now: datetime = NOW) -> engine.HAContext:
    return engine.HAContext(states, now, field_map or {"state": "sensor.x"}, WINDOWS)


def cmp_eq(value: str) -> dict:
    return {"node": "cmp", "field": "state", "op": "eq", "value": value,
            "value_type": "string", "on_absent": False}


class TestCmpString(unittest.TestCase):
    def test_eq_match_and_casefold(self):
        self.assertTrue(engine.eval_node(cmp_eq("on"), ctx({"sensor.x": {"state": "on"}})))
        self.assertTrue(engine.eval_node(cmp_eq("low"), ctx({"sensor.x": {"state": "LOW"}})))

    def test_d7_absent_unavailable_unknown_false(self):
        for st in ({}, {"sensor.x": {"state": "unavailable"}}, {"sensor.x": {"state": "unknown"}}):
            self.assertFalse(engine.eval_node(cmp_eq("on"), ctx(st)))

    def test_d7_binds_ne_too(self):
        ne = dict(cmp_eq("on"), op="ne")
        self.assertFalse(engine.eval_node(ne, ctx({})))          # absent ⇒ false, not "≠ on"
        self.assertTrue(engine.eval_node(ne, ctx({"sensor.x": {"state": "off"}})))


class TestCmpNumber(unittest.TestCase):
    NODE = {"node": "cmp", "field": "state", "op": "lt", "value": 20,
            "value_type": "number", "on_absent": False}

    def test_numeric_threshold(self):
        self.assertTrue(engine.eval_node(self.NODE, ctx({"sensor.x": {"state": "15"}})))
        self.assertFalse(engine.eval_node(self.NODE, ctx({"sensor.x": {"state": "20"}})))

    def test_d7_non_numeric_false(self):
        for st in ("unknown", "unavailable", "abc"):
            self.assertFalse(engine.eval_node(self.NODE, ctx({"sensor.x": {"state": st}})))


class TestUnavailable(unittest.TestCase):
    NODE = {"node": "unavailable", "field": "state"}

    def test_exactly_unavailable(self):
        self.assertTrue(engine.eval_node(self.NODE, ctx({"sensor.x": {"state": "unavailable"}})))
        self.assertFalse(engine.eval_node(self.NODE, ctx({"sensor.x": {"state": "unknown"}})))
        self.assertFalse(engine.eval_node(self.NODE, ctx({})))


class TestDuration(unittest.TestCase):
    NODE = {"node": "duration", "field": "state", "op": "gt", "seconds": 900, "on_absent": False}

    def _st(self, minutes_ago: int) -> dict:
        lc = (NOW - timedelta(minutes=minutes_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")
        return {"sensor.x": {"state": "on", "last_changed": lc}}

    def test_duration_boundary(self):
        self.assertTrue(engine.eval_node(self.NODE, ctx(self._st(20))))
        self.assertFalse(engine.eval_node(self.NODE, ctx(self._st(5))))

    def test_d7_missing_last_changed_false(self):
        self.assertFalse(engine.eval_node(self.NODE, ctx({"sensor.x": {"state": "on"}})))


class TestWindow(unittest.TestCase):
    NODE = {"node": "time_in_window", "window": "overnight"}

    def _at(self, hour: int, minute: int = 0) -> engine.HAContext:
        from zoneinfo import ZoneInfo
        local = datetime(2026, 7, 2, hour, minute, tzinfo=ZoneInfo("Europe/Madrid"))
        return ctx({}, now=local.astimezone(timezone.utc))

    def test_half_open_boundaries(self):
        self.assertTrue(engine.eval_node(self.NODE, self._at(0, 0)))     # start inclusive
        self.assertTrue(engine.eval_node(self.NODE, self._at(5, 59)))
        self.assertFalse(engine.eval_node(self.NODE, self._at(6, 0)))    # end exclusive
        self.assertFalse(engine.eval_node(self.NODE, self._at(12, 0)))


class TestBooleanNodes(unittest.TestCase):
    def test_and_or_not(self):
        t, f = cmp_eq("on"), cmp_eq("off")
        st = ctx({"sensor.x": {"state": "on"}})
        self.assertTrue(engine.eval_node({"node": "and", "operands": [t, t]}, st))
        self.assertFalse(engine.eval_node({"node": "and", "operands": [t, f]}, st))
        self.assertTrue(engine.eval_node({"node": "or", "operands": [f, t]}, st))
        self.assertFalse(engine.eval_node({"node": "not", "operand": t}, st))

    def test_unknown_node_fails_loud(self):
        with self.assertRaises(ValueError):
            engine.eval_node({"node": "xor", "operands": []}, ctx({}))


class TestLoadArtifact(unittest.TestCase):
    def test_missing_artifact_fails_loud(self):
        with self.assertRaises(engine.ArtifactError):
            engine.load_artifact(engine.DEFAULT_ARTIFACT.with_name("does_not_exist.json"))

    def test_unsupported_version_fails_loud(self):
        import json
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "artifact.json"
            p.write_text(json.dumps({"artifact_version": 99}), encoding="utf-8")
            with self.assertRaises(engine.ArtifactError):
                engine.load_artifact(p)

    def test_real_artifact_loads(self):
        artifact = engine.load_artifact()
        self.assertIn("entities", artifact)
        self.assertIn("windows", artifact["registries"])


if __name__ == "__main__":
    unittest.main()
