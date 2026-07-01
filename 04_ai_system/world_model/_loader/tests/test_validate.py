import unittest

from _loader import ast, grammar, validate
from _loader.model import ParsedRule
from _loader.tests.common import load_unvalidated


class TestValidate(unittest.TestCase):
    def test_real_tree_is_valid(self):
        entities, arch, reg = load_unvalidated()
        validate.validate(entities, arch, reg)         # must not raise

    def test_unknown_token_rejected(self):
        entities, arch, reg = load_unvalidated()
        entities[0].rules.append(
            ParsedRule("not_a_real_token", "state == on", grammar.parse("state == on")))
        with self.assertRaises(validate.ValidationError) as cm:
            validate.validate(entities, arch, reg)
        self.assertIn("not_a_real_token", str(cm.exception))

    def test_unknown_collector_rejected(self):
        entities, arch, reg = load_unvalidated()
        next(e for e in entities if e.collector).fm["collector"] = "nope"
        with self.assertRaises(validate.ValidationError) as cm:
            validate.validate(entities, arch, reg)
        self.assertIn("collector", str(cm.exception))

    def test_bad_region_rejected(self):
        entities, arch, reg = load_unvalidated()
        entities[0].fm["region"] = "bogus"
        with self.assertRaises(validate.ValidationError):
            validate.validate(entities, arch, reg)


if __name__ == "__main__":
    unittest.main()
