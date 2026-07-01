import unittest

from _loader import cli
from _loader.parity import oracle


class TestParityEquivalence(unittest.TestCase):
    def test_engine_equivalence(self):
        artifact = cli.build_artifact(reproducible=True)
        passed, failed, failures = oracle.run_equivalence(artifact)
        self.assertEqual(failed, 0, "\n".join(failures))
        self.assertGreaterEqual(passed, 30)


if __name__ == "__main__":
    unittest.main()
