import shutil
import tempfile
import unittest
from pathlib import Path

from _loader import cli
from _loader.tests.common import SRC_ROOT


class TestFailLoud(unittest.TestCase):
    def test_invalid_stops_and_retains_last_good(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "world_model"
            shutil.copytree(SRC_ROOT, root, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            # Corrupt one entity so validation fails.
            f = root / "home" / "printer-3d.md"
            f.write_text(f.read_text().replace("region: home", "region: bogus"))
            artifact = root / "world_model.generated.json"
            artifact.write_text("LAST-GOOD-SENTINEL")     # pre-existing good artifact

            rc = cli.run(root=root, emit_to=artifact)

            self.assertEqual(rc, 2)                        # fail-loud
            self.assertEqual(artifact.read_text(), "LAST-GOOD-SENTINEL")  # retained, no partial


if __name__ == "__main__":
    unittest.main()
