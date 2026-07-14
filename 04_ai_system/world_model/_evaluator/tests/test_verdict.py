"""
G-WM5-1 (verdict portion) — AD-WM5-1 `unknown`-precedence truth table.

Pure-logic unit tests for the evaluator's aggregate verdict. These are unit
fixtures (like the WM-4 snapshot suite), not gate-closing operational evidence;
the real-data end-to-end verdict gates are G-WM5-2 / G-WM5-2b / G-WM5-5.
"""

import unittest

from _evaluator.verdict import LADDER, aggregate_verdict, to_overall_status, worst_verdict


class TestUnknownPrecedenceTruthTable(unittest.TestCase):
    """Every row of the AD-WM5-1 truth table (phase_f_architecture.md §4D)."""

    def _row(self, regions, world, overall):
        v = aggregate_verdict(regions)
        self.assertEqual(v, world, f"world.verdict for {regions}")
        self.assertEqual(to_overall_status(v), overall, f"overall_status for {regions}")

    # --- the five required rows ------------------------------------------
    def test_home_unknown_infra_ok(self):
        self._row({"home": "unknown", "infrastructure": "ok"}, "unknown", "unknown")

    def test_home_ok_infra_unknown(self):
        # preserves the pre-existing "all platform signals absent → unknown"
        self._row({"home": "ok", "infrastructure": "unknown"}, "unknown", "unknown")

    def test_home_low_infra_unknown(self):
        self._row({"home": "low", "infrastructure": "unknown"}, "unknown", "unknown")

    def test_home_unknown_infra_medium(self):
        # a known >= medium deviation outranks an unknown region
        self._row({"home": "unknown", "infrastructure": "medium"}, "medium", "degraded")

    def test_all_regions_unknown(self):
        self._row({"home": "unknown", "infrastructure": "unknown"}, "unknown", "unknown")

    # --- escalation + "silence is informative" (§1.5) --------------------
    def test_low_only_does_not_escalate(self):
        self._row({"home": "low", "infrastructure": "ok"}, "low", "ok")

    def test_medium_escalates(self):
        self._row({"home": "medium", "infrastructure": "ok"}, "medium", "degraded")

    def test_worst_of_wins(self):
        self._row({"home": "critical", "infrastructure": "medium"}, "critical", "degraded")

    def test_all_ok(self):
        self._row({"home": "ok", "infrastructure": "ok"}, "ok", "ok")

    # --- the two ordering hinges of AD-WM5-1 ------------------------------
    def test_unknown_outranks_low(self):
        self._row({"a": "unknown", "b": "low"}, "unknown", "unknown")

    def test_medium_outranks_unknown(self):
        self._row({"a": "medium", "b": "unknown"}, "medium", "degraded")

    def test_high_and_critical(self):
        self._row({"a": "high", "b": "low"}, "high", "degraded")
        self._row({"a": "critical", "b": "unknown"}, "critical", "degraded")


class TestLadderAndGuards(unittest.TestCase):

    def test_ladder_order(self):
        self.assertEqual(LADDER, ("ok", "low", "unknown", "medium", "high", "critical"))

    def test_empty_is_ok(self):
        self.assertEqual(aggregate_verdict({}), "ok")

    def test_single_region(self):
        for tier in LADDER:
            self.assertEqual(aggregate_verdict({"home": tier}), tier)

    def test_bad_verdict_fails_loud(self):
        with self.assertRaises(ValueError):
            aggregate_verdict({"home": "weird"})
        with self.assertRaises(ValueError):
            to_overall_status("weird")


class TestWorstVerdict(unittest.TestCase):
    """The per-region rollup helper (iterable form) used by evaluate_world."""

    def test_rollup(self):
        self.assertEqual(worst_verdict([]), "ok")
        self.assertEqual(worst_verdict(["low", "low"]), "low")
        self.assertEqual(worst_verdict(["low", "medium"]), "medium")
        self.assertEqual(worst_verdict(["unknown", "low"]), "unknown")
        self.assertEqual(worst_verdict(["medium", "unknown"]), "medium")
        self.assertEqual(worst_verdict(["ok", "critical", "high"]), "critical")

    def test_bad_fails_loud(self):
        with self.assertRaises(ValueError):
            worst_verdict(["nope"])


if __name__ == "__main__":
    unittest.main()
