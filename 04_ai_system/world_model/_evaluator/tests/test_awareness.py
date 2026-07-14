"""
WM-5.1 — evaluate_world structure + evaluate_model shim identity (real artifact).

The firing paths + ordering are covered by the 32-snapshot regression (now routed
through evaluate_world via the evaluate_model shim); real tier/region enrichment on
a live anomaly is proven end-to-end at G-WM5-2. These unit tests pin the structural
contract of the new Awareness surface.
"""

import unittest
from datetime import datetime, timezone

from _evaluator import engine

NOW = datetime(2026, 7, 14, 2, 15, tzinfo=timezone.utc)   # overnight (Europe/Madrid)


class TestEvaluateWorld(unittest.TestCase):
    def setUp(self):
        self.artifact = engine.load_artifact()

    def test_empty_states_no_anomalies(self):
        aw = engine.evaluate_world(self.artifact, {}, NOW)
        self.assertEqual(aw.anomalies, [])
        self.assertEqual(aw.region_verdicts, {})

    def test_model_is_exact_projection_of_world(self):
        # evaluate_model must remain the [(token, phrase)] projection of evaluate_world
        for states in ({}, {"sensor.absent": {"state": "x"}}):
            aw = engine.evaluate_world(self.artifact, states, NOW)
            self.assertEqual(
                engine.evaluate_model(self.artifact, states, NOW),
                [(a.token, a.phrase) for a in aw.anomalies],
            )

    def test_region_verdict_is_worst_tier(self):
        # invariant: each region verdict == the worst tier among that region's anomalies
        aw = engine.evaluate_world(self.artifact, {}, NOW)
        for region, verdict in aw.region_verdicts.items():
            self.assertEqual(
                verdict,
                engine.worst_verdict(a.tier for a in aw.anomalies if a.region == region),
            )


if __name__ == "__main__":
    unittest.main()
