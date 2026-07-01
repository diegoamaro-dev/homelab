import unittest

from _loader import cli, emit


class TestDeterminism(unittest.TestCase):
    def test_byte_identical_reproducible(self):
        a1 = emit.serialize(cli.build_artifact(reproducible=True))
        a2 = emit.serialize(cli.build_artifact(reproducible=True))
        self.assertEqual(a1, a2)

    def test_only_generated_at_varies(self):
        # Non-reproducible builds differ ONLY in generator.generated_at.
        a1 = cli.build_artifact(reproducible=False)
        a2 = cli.build_artifact(reproducible=False)
        a1["generator"]["generated_at"] = a2["generator"]["generated_at"] = "X"
        self.assertEqual(emit.serialize(a1), emit.serialize(a2))


if __name__ == "__main__":
    unittest.main()
