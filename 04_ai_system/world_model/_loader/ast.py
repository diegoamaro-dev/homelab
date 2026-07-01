"""
ast.py — the World Model canonical rule language (backend-agnostic).

INV-WM3-A (AST is the canonical rule language):
    The rule AST is the canonical rule language of the World Model. It is
    BACKEND-AGNOSTIC: it contains NO implementation detail specific to Home
    Assistant, detect_home(), or any evaluator. Every evaluator consumes the
    same AST. Consequently this module holds pure data + the language contract
    ONLY — no state resolution, no HA ids, no evaluation. All backend/state
    logic lives in an evaluator's adapter, never here.

Node catalogue (frozen §4.5 closed grammar):
    And(operands)              conjunction (n-ary)
    Or(operands)               disjunction (n-ary)
    Not(operand)               negation
    Cmp(field, op, value, ...) field COMP value        (op ∈ eq ne lt gt le ge)
    Unavailable(field)         field 'unavailable'     (true iff state == "unavailable" exactly)
    TimeInWindow(window)       time in <window>
    Duration(field, op, secs)  now − last_changed(field) COMP <seconds>

Evaluation semantics are DOCUMENTED here (the shared contract) but IMPLEMENTED by
evaluators. See §"Evaluation contract" below.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Union

# ── Operator canonicalisation (language-level, not backend) ──────────────────
COMP_CANON = {"==": "eq", "!=": "ne", "<": "lt", ">": "gt", "<=": "le", ">=": "ge"}
ORDER_OPS = {"lt", "gt", "le", "ge"}          # require a numeric operand
EQ_OPS = {"eq", "ne"}
DURATION_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600}


# ── Nodes ────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class And:
    operands: tuple["Node", ...]


@dataclass(frozen=True)
class Or:
    operands: tuple["Node", ...]


@dataclass(frozen=True)
class Not:
    operand: "Node"


@dataclass(frozen=True)
class Cmp:
    field: str
    op: str                      # eq ne lt gt le ge
    value: Union[str, float, int]
    value_type: str              # "string" | "number"
    on_absent: bool = False      # D7: absent/unavailable/unknown ⇒ predicate false


@dataclass(frozen=True)
class Unavailable:
    field: str


@dataclass(frozen=True)
class TimeInWindow:
    window: str


@dataclass(frozen=True)
class Duration:
    field: str
    op: str                      # gt lt ge le
    seconds: int
    on_absent: bool = False      # false if last_changed missing


Node = Union[And, Or, Not, Cmp, Unavailable, TimeInWindow, Duration]
LEAVES = (Cmp, Unavailable, TimeInWindow, Duration)


# ── Serialisation to the artifact JSON form ──────────────────────────────────
def to_dict(node: Node) -> dict:
    if isinstance(node, And):
        return {"node": "and", "operands": [to_dict(o) for o in node.operands]}
    if isinstance(node, Or):
        return {"node": "or", "operands": [to_dict(o) for o in node.operands]}
    if isinstance(node, Not):
        return {"node": "not", "operand": to_dict(node.operand)}
    if isinstance(node, Cmp):
        return {
            "node": "cmp", "field": node.field, "op": node.op,
            "value": node.value, "value_type": node.value_type,
            "on_absent": node.on_absent,
        }
    if isinstance(node, Unavailable):
        return {"node": "unavailable", "field": node.field}
    if isinstance(node, TimeInWindow):
        return {"node": "time_in_window", "window": node.window}
    if isinstance(node, Duration):
        return {
            "node": "duration", "field": node.field, "op": node.op,
            "seconds": node.seconds, "on_absent": node.on_absent,
        }
    raise TypeError(f"unknown AST node: {node!r}")


def fields_read(node: Node) -> list[str]:
    """Ordered, de-duplicated list of signal fields the AST reads (for provenance)."""
    out: list[str] = []

    def walk(n: Node) -> None:
        if isinstance(n, (And, Or)):
            for o in n.operands:
                walk(o)
        elif isinstance(n, Not):
            walk(n.operand)
        elif isinstance(n, (Cmp, Unavailable, Duration)):
            if n.field not in out:
                out.append(n.field)
        # TimeInWindow reads no signal field

    walk(node)
    return out


def uses_last_changed(node: Node) -> bool:
    if isinstance(node, Duration):
        return True
    if isinstance(node, (And, Or)):
        return any(uses_last_changed(o) for o in node.operands)
    if isinstance(node, Not):
        return uses_last_changed(node.operand)
    return False


def windows_used(node: Node) -> list[str]:
    out: list[str] = []

    def walk(n: Node) -> None:
        if isinstance(n, TimeInWindow):
            if n.window not in out:
                out.append(n.window)
        elif isinstance(n, (And, Or)):
            for o in n.operands:
                walk(o)
        elif isinstance(n, Not):
            walk(n.operand)

    walk(node)
    return out
