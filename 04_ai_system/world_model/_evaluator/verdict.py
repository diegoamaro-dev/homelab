"""
verdict.py — the deterministic aggregate verdict (WM-5, AD-WM5-1).

The frozen §1.5 aggregate verdict lives INSIDE the evaluator (Option A,
operator-ratified): consumers are pure projections and never re-derive
escalation. `aggregate_verdict` folds per-region verdicts into one global
verdict on a single total-ordered ladder; `to_overall_status` maps that verdict
to the frozen `aurora-context.json` coarse enum (AD-20: ok | degraded | unknown).

AD-WM5-1 (ratified 2026-07-13) — `unknown` precedence. Frozen §1.5 defines the
severity tiers and the >= medium escalation rule but is silent on a region whose
awareness is absent (HA unreachable / compiled artifact missing / all platform
signals missing). AD-WM5-1 places `unknown` as a distinct, non-escalating
"cannot-confirm-ok" state:

    critical > high > medium  >  unknown  >  low > ok
    |__________ escalate ______|          |_ listed, not escalated _|

Pure functions (B3): no I/O, no live reads, no writes. Reality always wins — an
unobserved region is never reported `ok`, but an absence of information is not a
>= medium deviation, so it is not `degraded` either. See
`04_ai_system/phase_f_architecture.md` §4D and `world_model_architecture.md` §1.5.
"""

from __future__ import annotations

# Precedence ladder, lowest → highest (higher rank wins). AD-WM5-1.
LADDER: tuple[str, ...] = ("ok", "low", "unknown", "medium", "high", "critical")
_RANK: dict[str, int] = {name: i for i, name in enumerate(LADDER)}

# Verdicts at or above `medium` escalate the coarse status to `degraded`.
ESCALATING: frozenset[str] = frozenset({"medium", "high", "critical"})


def worst_verdict(verdicts) -> str:
    """
    Highest-precedence verdict in an iterable (AD-WM5-1 ladder); empty → "ok".

    The core rollup — used both for a region's worst active tier (by
    `evaluate_world`) and by `aggregate_verdict`. Raises `ValueError` on an
    unrecognized verdict (fail-loud, deterministic).
    """
    worst = "ok"
    for verdict in verdicts:
        if verdict not in _RANK:
            raise ValueError(f"unknown verdict {verdict!r}")
        if _RANK[verdict] > _RANK[worst]:
            worst = verdict
    return worst


def aggregate_verdict(region_verdicts: dict[str, str]) -> str:
    """
    Fold per-region verdicts into the global world verdict (AD-WM5-1 ladder).

    `region_verdicts` maps a region id to a verdict in `LADDER`
    (ok | low | unknown | medium | high | critical). Returns the
    highest-precedence verdict present; `{}` → "ok".
    """
    return worst_verdict(region_verdicts.values())


def to_overall_status(verdict: str) -> str:
    """Map a world verdict → the frozen coarse enum `ok | degraded | unknown` (AD-20)."""
    if verdict not in _RANK:
        raise ValueError(f"unknown verdict {verdict!r}")
    if verdict in ESCALATING:
        return "degraded"
    if verdict == "unknown":
        return "unknown"
    return "ok"
