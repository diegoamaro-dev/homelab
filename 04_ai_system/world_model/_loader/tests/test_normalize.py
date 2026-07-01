import unittest

from _loader import ast, normalize
from _loader.tests.common import load_unvalidated


class TestNormalize(unittest.TestCase):
    def test_casefold_and_on_absent_binding(self):
        node = ast.Cmp("battery_state", "eq", "LOW", "string", on_absent=True)
        out = normalize._norm_node(node)
        self.assertEqual(out.value, "low")            # N1 casefold
        self.assertFalse(out.on_absent)               # N2 D7 bound false

    def test_numeric_value_preserved(self):
        node = ast.Cmp("soil_moisture", "lt", 20, "number")
        out = normalize._norm_node(node)
        self.assertEqual(out.value, 20)
        self.assertEqual(out.value_type, "number")

    def test_entities_sorted_and_ranks_stamped(self):
        entities, _, _ = load_unvalidated()
        ids = [e.id for e in entities]
        self.assertEqual(ids, sorted(ids))            # N7 deterministic order
        for e in entities:
            for r in e.rules:
                self.assertIsNotNone(r.severity_rank)
                self.assertIsNotNone(r.render_phrase)


if __name__ == "__main__":
    unittest.main()
