"""
grammar.py — tokenizer + recursive-descent parser for the closed condition grammar.

Frozen §4.5 / schema §3 (closed grammar):

    condition := disj
    disj      := conj ('OR' conj)*
    conj      := neg ('AND' neg)*
    neg       := 'NOT'? predicate | '(' condition ')'
    predicate := field COMP value
               | 'time' 'in' <window>
               | field 'unavailable'
               | field COMP value ('for' DURATION)?   # duration suffix (reality: detect_home)
               | field 'for' DURATION                 # bare form (frozen; unused by WM-2)
    COMP      := == != < > <= >=
    DURATION  := COMP <n><unit>   (unit ∈ s | m | h)

Precedence (structural): OR (loosest) → AND → NOT → predicate/paren.
Output: backend-agnostic ast.Node objects (INV-WM3-A). No evaluation here.

Reality-reconciliation (approved): the authored duration rule is
`state == on for > 15m` — a comparison WITH a `for DURATION` suffix — which the
frozen BNF's own example comment and the then-live detect_home (retired at
WM-4) both confirmed. The suffix desugars to `And(Cmp, Duration)` on the same
field.
"""

from __future__ import annotations

import re

from . import ast


class GrammarError(ValueError):
    pass


# ── Tokeniser ────────────────────────────────────────────────────────────────
_TOKEN_RE = re.compile(
    r"""
    (?P<ws>\s+)
  | (?P<op2>==|!=|<=|>=)
  | (?P<paren>[()])
  | (?P<op1>[<>])
  | (?P<duration>\d+[smh])(?![A-Za-z0-9_])
  | (?P<number>\d+(?:\.\d+)?)
  | (?P<word>[A-Za-z_][A-Za-z0-9_]*)
    """,
    re.VERBOSE,
)

_KEYWORDS = {"AND", "OR", "NOT", "time", "in", "unavailable", "for"}


class _Tok:
    __slots__ = ("kind", "text")

    def __init__(self, kind: str, text: str):
        self.kind = kind
        self.text = text

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"{self.kind}:{self.text}"


def tokenize(s: str) -> list[_Tok]:
    toks: list[_Tok] = []
    pos = 0
    for m in _TOKEN_RE.finditer(s):
        if m.start() != pos:
            raise GrammarError(f"unexpected character at {pos} in {s!r}")
        pos = m.end()
        kind = m.lastgroup
        text = m.group()
        if kind == "ws":
            continue
        toks.append(_Tok(kind, text))
    if pos != len(s):
        raise GrammarError(f"unexpected character at {pos} in {s!r}")
    return toks


# ── Parser ───────────────────────────────────────────────────────────────────
class _Parser:
    def __init__(self, toks: list[_Tok], src: str):
        self.toks = toks
        self.src = src
        self.i = 0

    def _peek(self) -> _Tok | None:
        return self.toks[self.i] if self.i < len(self.toks) else None

    def _next(self) -> _Tok:
        if self.i >= len(self.toks):
            raise GrammarError(f"unexpected end of condition in {self.src!r}")
        t = self.toks[self.i]
        self.i += 1
        return t

    def _is_word(self, t: _Tok | None, w: str) -> bool:
        return t is not None and t.kind == "word" and t.text == w

    # disj := conj ('OR' conj)*
    def parse(self) -> ast.Node:
        node = self._conj()
        ors = [node]
        while self._is_word(self._peek(), "OR"):
            self._next()
            ors.append(self._conj())
        node = ors[0] if len(ors) == 1 else ast.Or(tuple(ors))
        if self._peek() is not None:
            raise GrammarError(f"trailing tokens in {self.src!r}")
        return node

    # conj := neg ('AND' neg)*
    def _conj(self) -> ast.Node:
        node = self._neg()
        ands = [node]
        while self._is_word(self._peek(), "AND"):
            self._next()
            ands.append(self._neg())
        return ands[0] if len(ands) == 1 else ast.And(tuple(ands))

    # neg := 'NOT'? predicate | '(' condition ')'
    def _neg(self) -> ast.Node:
        t = self._peek()
        if self._is_word(t, "NOT"):
            self._next()
            return ast.Not(self._neg())
        if t is not None and t.kind == "paren" and t.text == "(":
            self._next()
            node = self.parse_inner()
            close = self._next()
            if close.kind != "paren" or close.text != ")":
                raise GrammarError(f"expected ')' in {self.src!r}")
            return node
        return self._predicate()

    def parse_inner(self) -> ast.Node:
        node = self._conj()
        ors = [node]
        while self._is_word(self._peek(), "OR"):
            self._next()
            ors.append(self._conj())
        return ors[0] if len(ors) == 1 else ast.Or(tuple(ors))

    # predicate
    def _predicate(self) -> ast.Node:
        t = self._next()
        if t.kind != "word":
            raise GrammarError(f"expected field/keyword, got {t!r} in {self.src!r}")

        # time in <window>
        if t.text == "time":
            in_tok = self._next()
            if not self._is_word(in_tok, "in"):
                raise GrammarError(f"expected 'in' after 'time' in {self.src!r}")
            win = self._next()
            if win.kind != "word":
                raise GrammarError(f"expected window name in {self.src!r}")
            return ast.TimeInWindow(win.text)

        field = t.text
        nxt = self._peek()

        # field 'unavailable'
        if self._is_word(nxt, "unavailable"):
            self._next()
            return ast.Unavailable(field)

        # field 'for' DURATION   (bare)
        if self._is_word(nxt, "for"):
            self._next()
            return self._duration(field)

        # field COMP value  (+ optional 'for' DURATION)
        if nxt is not None and nxt.kind in ("op2", "op1"):
            op_tok = self._next()
            cmp_node = self._cmp(field, op_tok.text)
            if self._is_word(self._peek(), "for"):
                self._next()
                dur = self._duration(field)
                return ast.And((cmp_node, dur))
            return cmp_node

        raise GrammarError(f"malformed predicate near {field!r} in {self.src!r}")

    def _cmp(self, field: str, op_text: str) -> ast.Cmp:
        op = ast.COMP_CANON[op_text]
        val = self._next()
        if val.kind == "number":
            value: object = float(val.text) if "." in val.text else int(val.text)
            vtype = "number"
        elif val.kind == "word":
            if op in ast.ORDER_OPS:
                raise GrammarError(
                    f"ordering op {op_text!r} needs a numeric value, got {val.text!r} in {self.src!r}"
                )
            value = val.text
            vtype = "string"
        else:
            raise GrammarError(f"expected value after {op_text!r} in {self.src!r}")
        return ast.Cmp(field=field, op=op, value=value, value_type=vtype)

    def _duration(self, field: str) -> ast.Duration:
        op_tok = self._next()
        if op_tok.kind not in ("op2", "op1"):
            raise GrammarError(f"expected comparison after 'for' in {self.src!r}")
        op = ast.COMP_CANON[op_tok.text]
        if op not in ast.ORDER_OPS:
            raise GrammarError(f"duration needs an ordering comparison in {self.src!r}")
        dur = self._next()
        if dur.kind != "duration":
            raise GrammarError(f"expected <n><unit> duration in {self.src!r}")
        n = int(dur.text[:-1])
        unit = dur.text[-1]
        seconds = n * ast.DURATION_UNIT_SECONDS[unit]
        return ast.Duration(field=field, op=op, seconds=seconds)


def parse(condition: str) -> ast.Node:
    """Parse a condition string into a backend-agnostic AST (ast.Node)."""
    toks = tokenize(condition)
    if not toks:
        raise GrammarError("empty condition")
    return _Parser(toks, condition).parse()
