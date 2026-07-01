import shutil
import tempfile
import unittest
from pathlib import Path

from _loader import cli, validate
from _loader.tests.common import SRC_ROOT


class TestAD18(unittest.TestCase):
    def test_real_tree_clean(self):
        cli.compile_model()                            # no AD-18 violation on the real docs

    def _inject(self, needle_replace: tuple[str, str]):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "world_model"
            shutil.copytree(SRC_ROOT, root, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            f = root / "home" / "printer-3d.md"
            f.write_text(f.read_text().replace(*needle_replace))
            with self.assertRaises(validate.ValidationError) as cm:
                cli.compile_model(root)
            self.assertIn("AD-18", str(cm.exception))

    def test_planted_ipv4_rejected(self):
        self._inject(("## Purpose", "## Purpose\nrouter at 192.168.178.21\n"))

    def test_planted_jwt_rejected(self):
        self._inject(("## Purpose", "## Purpose\ntoken eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payloadpart\n"))


if __name__ == "__main__":
    unittest.main()
