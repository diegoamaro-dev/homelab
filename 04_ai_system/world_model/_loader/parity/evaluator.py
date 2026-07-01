"""
evaluator.py — minimal AST evaluator (WM-3 parity only; non-authoritative).

Two layers, keeping INV-WM3-A intact:
  • eval_node(node, ctx) — the BACKEND-AGNOSTIC core: it knows AST semantics only
    and calls ctx for field resolution. No HA ids here.
  • HAContext — the adapter: resolves fields from an /api/states dict, reusing
    detect_home()'s own _state/_num/parse_ts (via hostmod) for identical
    extraction. All Home-Assistant specifics live here, never in the AST.

Consumes the AST in its emitted dict form (from world_model.generated.json), so
this literally evaluates the same artifact a consumer would.
"""

from __future__ import annotations

from datetime import datetime

from . import hostmod

ASPECT_SIGNAL_FIELD = {"flag": "battery_low", "pct": "battery_level", "categorical": "battery_state"}


def _num_cmp(op: str, a: float, b: float) -> bool:
    return {"lt": a < b, "gt": a > b, "le": a <= b, "ge": a >= b, "eq": a == b, "ne": a != b}[op]


class HAContext:
    """Adapter: field name → HA entity_id (per the entity's binding) → reading."""

    def __init__(self, states: dict, now_utc: datetime, now_local: datetime,
                 field_map: dict[str, str], windows: dict):
        self.states = states
        self.now_utc = now_utc
        self.now_local = now_local
        self.field_map = field_map
        self.windows = windows

    def state(self, field: str):
        eid = self.field_map.get(field)
        return hostmod.state_of(self.states, eid) if eid else None

    def num(self, field: str):
        eid = self.field_map.get(field)
        return hostmod.num_of(self.states, eid) if eid else None

    def last_changed(self, field: str):
        eid = self.field_map.get(field)
        if not eid:
            return None
        obj = self.states.get(eid) or {}
        return hostmod.parse_ts(obj.get("last_changed"))

    def in_window(self, name: str) -> bool:
        w = self.windows[name]
        minutes = self.now_local.hour * 60 + self.now_local.minute
        return w["start_min"] <= minutes < w["end_min"]


def eval_node(node: dict, ctx: HAContext) -> bool:
    kind = node["node"]
    if kind == "and":
        return all(eval_node(o, ctx) for o in node["operands"])
    if kind == "or":
        return any(eval_node(o, ctx) for o in node["operands"])
    if kind == "not":
        return not eval_node(node["operand"], ctx)
    if kind == "time_in_window":
        return ctx.in_window(node["window"])
    if kind == "unavailable":
        return ctx.state(node["field"]) == "unavailable"           # exact (reality: bridge)
    if kind == "duration":
        lc = ctx.last_changed(node["field"])
        if lc is None:
            return False                                           # D7: missing last_changed
        secs = (ctx.now_utc - lc).total_seconds()
        return _num_cmp(node["op"], secs, node["seconds"])
    if kind == "cmp":
        if node["value_type"] == "number":
            n = ctx.num(node["field"])
            if n is None:
                return False                                       # D7: absent/non-numeric
            return _num_cmp(node["op"], n, node["value"])
        s = ctx.state(node["field"])
        if s is None or s in hostmod.UNAVAIL:
            return False                                           # D7: absent/unavailable/unknown
        s = s.lower()
        return s == node["value"] if node["op"] == "eq" else s != node["value"]
    raise ValueError(f"unknown AST node: {kind!r}")


def _field_map(entity: dict) -> dict[str, str]:
    signals = (entity.get("binding") or {}).get("signals") or {}
    return {name: sig["ha_entity"] for name, sig in signals.items() if "ha_entity" in sig}


def evaluate_model(artifact: dict, states: dict, now_utc: datetime,
                   now_local: datetime) -> list[tuple[str, str]]:
    """Return ordered [(token, phrase)] — the compiled-model equivalent of detect_home()."""
    windows = artifact["registries"]["windows"]
    fired: list[tuple[str, str, int]] = []

    for entity in artifact["entities"].values():
        if not entity.get("evaluable"):
            continue
        for rule in entity["anomaly_rules"]:
            if rule.get("kind") == "fold":
                fold = rule["fold"]
                names: list[str] = []
                for m in fold["members"]:
                    fld = ASPECT_SIGNAL_FIELD[m["signal"]]
                    ctx = HAContext(states, now_utc, now_local, {fld: m["binding"]}, windows)
                    if eval_node(fold["per_signal"][m["signal"]], ctx) and m["device"] not in names:
                        names.append(m["device"])
                if names:
                    phrase = fold["render_phrase_prefix"] + ", ".join(names)
                    fired.append((rule["token"], phrase, rule["severity_rank"]))
            else:
                ctx = HAContext(states, now_utc, now_local, _field_map(entity), windows)
                if eval_node(rule["ast"], ctx):
                    fired.append((rule["token"], rule["render_phrase"], rule["severity_rank"]))

    fired.sort(key=lambda t: t[2])                     # canonical emission order (severity_rank)
    return [(tok, phrase) for tok, phrase, _ in fired]
