import unittest

from _loader import ast, grammar

REAL = [
    "connection == off OR connection unavailable",
    "permit_join == on",
    "state == off",
    "state == on AND time in overnight",
    "state == open AND time in overnight",
    "state == on for > 15m",
    "water_warning != none",
    "soil_moisture < 20",
    "battery_low == on OR battery_level <= 20 OR battery_state == low OR battery_state == empty",
]


class TestGrammar(unittest.TestCase):
    def test_all_real_conditions_parse(self):
        for c in REAL:
            self.assertIsNotNone(grammar.parse(c))

    def test_precedence_or_binds_loosest(self):
        n = grammar.parse("a == 1 AND b == 2 OR c == 3")
        self.assertIsInstance(n, ast.Or)
        self.assertIsInstance(n.operands[0], ast.And)

    def test_duration_desugars_to_and(self):
        n = grammar.parse("state == on for > 15m")
        self.assertIsInstance(n, ast.And)
        self.assertIsInstance(n.operands[0], ast.Cmp)
        self.assertIsInstance(n.operands[1], ast.Duration)
        self.assertEqual(n.operands[1].seconds, 900)
        self.assertEqual(n.operands[1].op, "gt")

    def test_not_and_parens(self):
        n = grammar.parse("NOT (state == on OR state unavailable)")
        self.assertIsInstance(n, ast.Not)
        self.assertIsInstance(n.operand, ast.Or)

    def test_ordering_op_requires_number(self):
        with self.assertRaises(grammar.GrammarError):
            grammar.parse("state < on")

    def test_garbage_rejected(self):
        for bad in ("state == == on", "== on", "state for", "time in"):
            with self.assertRaises(grammar.GrammarError):
                grammar.parse(bad)


if __name__ == "__main__":
    unittest.main()
