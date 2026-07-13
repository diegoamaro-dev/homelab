"""
engine.py — the authoritative Awareness evaluation engine (WM-4).

Evaluates the COMPILED World Model (`world_model.generated.json`) against a
signals snapshot at a fixed instant and returns the ordered anomaly
evaluation `[(token, render_phrase)]` — the World Model @ now.

Two layers, preserving INV-WM3-A (backend-agnostic AST):

  • `eval_node(node, ctx)` — the AST core. Knows AST semantics only
    (and/or/not · cmp · unavailable · time_in_window · duration) and calls
    `ctx` for field resolution. No Home-Assistant ids or specifics here.
  • `HAContext` — the adapter: field name → `ha_entity` (per the entity's
    `binding.signals`) → reading from an `/api/states` dict, with the D7
    never-guess extraction rules. All HA specifics live here.

Semantics contract (identical to the WM-3 parity-proven behaviour):
  D7      — absent / "unavailable" / "unknown" readings make a predicate
            resolve to its `on_absent` binding (compiled `false`, incl. `!=`).
  N1      — string comparison is casefolded (the loader casefolds values).
  unavailable — true iff state == "unavailable" EXACTLY (not "unknown").
  duration — `now − last_changed(field) COMP seconds`, from the `last_changed`
            carried in the CURRENT signal (stateless — B3 preserved);
            missing `last_changed` → `on_absent`.
  windows — tz-anchored (frozen §4.5): local minutes are derived from the
            window's own declared tz, half-open [start_min, end_min).
  ordering — fired rules sort by `severity_rank` (the registry's canonical
            emission order); fold rules dedup by device in roster order.

Failure rule: a missing/unreadable/unsupported artifact raises
`ArtifactError` (fail-loud here); the consumer degrades honestly
(fail-soft — e.g. the home block renders Unavailable). Runtime observation
gaps never raise — they resolve per D7. Reality always wins.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

EVALUATOR_VERSION = "0.1.0"
SUPPORTED_ARTIFACT_VERSIONS = (1,)

# The emitted artifact lives at the world_model/ root (…/world_model/_evaluator/ → parent).
DEFAULT_ARTIFACT = Path(__file__).resolve().parent.parent / "world_model.generated.json"

UNAVAIL = ("unavailable", "unknown")

# Fold-member signal kind → the field name its per-signal AST reads (battery aspect).
ASPECT_SIGNAL_FIELD = {"flag": "battery_low", "pct": "battery_level", "categorical": "battery_state"}

_ZONES: dict[str, ZoneInfo] = {}


class ArtifactError(Exception):
    """The compiled artifact is missing, unreadable, or of an unsupported version."""


def load_artifact(path: Path = DEFAULT_ARTIFACT) -> dict:
    """Read + minimally guard the compiled model. Raises ArtifactError (fail-loud)."""
    try:
        artifact = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ArtifactError(f"artifact not found: {path}") from exc
    except (OSError, ValueError) as exc:
        raise ArtifactError(f"artifact unreadable: {path}: {exc}") from exc
    version = artifact.get("artifact_version")
    if version not in SUPPORTED_ARTIFACT_VERSIONS:
        raise ArtifactError(
            f"unsupported artifact_version {version!r} "
            f"(evaluator {EVALUATOR_VERSION} supports {SUPPORTED_ARTIFACT_VERSIONS})")
    return artifact


# ── Signal extraction (D7 — never guess) ─────────────────────────────────────

def parse_ts(s) -> datetime | None:
    """ISO timestamp → aware UTC datetime, or None (never guess)."""
    if not s:
        return None
    try:
        clean = re.sub(r"\.\d+", "", str(s))
        clean = re.sub(r"Z$", "+00:00", clean)
        return datetime.fromisoformat(clean).astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def _state_of(states: dict, eid: str | None):
    obj = states.get(eid) if eid else None
    return obj.get("state") if isinstance(obj, dict) else None


def _num_of(states: dict, eid: str | None):
    """Numeric state, or None if absent/unavailable/unknown/non-numeric (D7)."""
    s = _state_of(states, eid)
    if s is None or s in UNAVAIL:
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _zone(tz: str) -> ZoneInfo:
    z = _ZONES.get(tz)
    if z is None:
        z = _ZONES[tz] = ZoneInfo(tz)
    return z


def _num_cmp(op: str, a: float, b: float) -> bool:
    return {"lt": a < b, "gt": a > b, "le": a <= b, "ge": a >= b, "eq": a == b, "ne": a != b}[op]


# ── The adapter (all HA specifics live here) ─────────────────────────────────

class HAContext:
    """Field name → HA entity_id (per the entity's binding) → reading."""

    def __init__(self, states: dict, now_utc: datetime,
                 field_map: dict[str, str], windows: dict):
        self.states = states
        self.now_utc = now_utc
        self.field_map = field_map
        self.windows = windows

    def state(self, field: str):
        return _state_of(self.states, self.field_map.get(field))

    def num(self, field: str):
        return _num_of(self.states, self.field_map.get(field))

    def last_changed(self, field: str):
        eid = self.field_map.get(field)
        if not eid:
            return None
        obj = self.states.get(eid) or {}
        return parse_ts(obj.get("last_changed"))

    def in_window(self, name: str) -> bool:
        w = self.windows[name]
        local = self.now_utc.astimezone(_zone(w["tz"]))          # tz-anchored (§4.5)
        minutes = local.hour * 60 + local.minute
        if w.get("half_open", True):
            return w["start_min"] <= minutes < w["end_min"]
        return w["start_min"] <= minutes <= w["end_min"]


# ── The backend-agnostic AST core (INV-WM3-A) ────────────────────────────────

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
        return ctx.state(node["field"]) == "unavailable"         # exact — not "unknown"
    if kind == "duration":
        lc = ctx.last_changed(node["field"])
        if lc is None:
            return node.get("on_absent", False)                  # D7
        secs = (ctx.now_utc - lc).total_seconds()
        return _num_cmp(node["op"], secs, node["seconds"])
    if kind == "cmp":
        if node["value_type"] == "number":
            n = ctx.num(node["field"])
            if n is None:
                return node.get("on_absent", False)              # D7
            return _num_cmp(node["op"], n, node["value"])
        s = ctx.state(node["field"])
        if s is None or s in UNAVAIL:
            return node.get("on_absent", False)                  # D7 (incl. !=)
        s = s.casefold()                                         # N1 symmetry
        return s == node["value"] if node["op"] == "eq" else s != node["value"]
    raise ValueError(f"unknown AST node: {kind!r}")


# ── Model evaluation (Awareness = the model @ now) ───────────────────────────

def _field_map(entity: dict) -> dict[str, str]:
    signals = (entity.get("binding") or {}).get("signals") or {}
    return {name: sig["ha_entity"] for name, sig in signals.items() if "ha_entity" in sig}


def _eval_fold(rule: dict, states: dict, now_utc: datetime, windows: dict):
    """Fold rule (aspect roster): dedup by device, roster order, emit once."""
    fold = rule["fold"]
    names: list[str] = []
    for member in fold["members"]:
        fld = ASPECT_SIGNAL_FIELD[member["signal"]]
        ctx = HAContext(states, now_utc, {fld: member["binding"]}, windows)
        if eval_node(fold["per_signal"][member["signal"]], ctx) and member["device"] not in names:
            names.append(member["device"])
    if not names:
        return None
    return fold["render_phrase_prefix"] + ", ".join(names)


def evaluate_model(artifact: dict, states: dict, now_utc: datetime) -> list[tuple[str, str]]:
    """
    Ordered [(token, render_phrase)] for the snapshot at now_utc.

    Pure function of its arguments (B3): no I/O, no live reads. Retired or
    non-evaluable entities are excluded (lifecycle §3 — retirement is visible,
    never evaluated).
    """
    windows = artifact["registries"]["windows"]
    fired: list[tuple[str, str, int]] = []

    for entity in artifact["entities"].values():
        if not entity.get("evaluable") or entity.get("status") != "active":
            continue
        for rule in entity["anomaly_rules"]:
            if rule.get("kind") == "fold":
                phrase = _eval_fold(rule, states, now_utc, windows)
                if phrase is not None:
                    fired.append((rule["token"], phrase, rule["severity_rank"]))
            else:
                ctx = HAContext(states, now_utc, _field_map(entity), windows)
                if eval_node(rule["ast"], ctx):
                    fired.append((rule["token"], rule["render_phrase"], rule["severity_rank"]))

    fired.sort(key=lambda t: t[2])                     # canonical emission order
    return [(token, phrase) for token, phrase, _ in fired]
