"""Snapshot regression suite: the engine must match the frozen HOME_RULES outcomes.

Successor of the WM-3 parity oracle (retired at WM-4 with `HOME_RULES`): the
32 boundary snapshots run against the compiled artifact and must reproduce the
outcomes frozen in `expected.py` — token set, order, and rendering.
"""

import unittest

from _evaluator import engine
from _evaluator.tests import snapshots
from _evaluator.tests.expected import EXPECTED


class TestSnapshotRegression(unittest.TestCase):
    def test_all_snapshots_match_frozen_expectations(self):
        artifact = engine.load_artifact()
        cases = snapshots.cases()
        self.assertEqual(len(cases), len(EXPECTED), "case list and expectations diverged")
        for case in cases:
            with self.subTest(case=case["name"]):
                actual = engine.evaluate_model(artifact, case["states"], case["now_utc"])
                self.assertEqual(actual, EXPECTED[case["name"]])


if __name__ == "__main__":
    unittest.main()
