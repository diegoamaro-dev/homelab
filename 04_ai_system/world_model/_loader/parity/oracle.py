"""
oracle.py — differential parity runner (G-WM3-6).

For each snapshot S and fixed `now`, assert:

    evaluate_model(artifact, S, now) == detect_home(S, now)

on token set, order, and rendering. Over enumerated boundary snapshots this is
engine-equivalence (proves loader rules ≡ HOME_RULES); over a real captured
snapshot it is real-data parity. Real snapshots are used in-memory only and
never persisted (AD-18: /api/states attributes can carry ips/tokens).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from . import hostmod, snapshots
from .evaluator import evaluate_model

ARTIFACT = Path(__file__).resolve().parent.parent.parent / "world_model.generated.json"


def load_artifact(path: Path = ARTIFACT) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _norm(pairs) -> list[tuple[str, str]]:
    return [(t, p) for t, p in pairs]


def run_equivalence(artifact: dict) -> tuple[int, int, list[str]]:
    passed = failed = 0
    failures: list[str] = []
    for case in snapshots.cases():
        expected = _norm(hostmod.detect_home(case["states"], case["now_utc"], case["now_local"]))
        actual = evaluate_model(artifact, case["states"], case["now_utc"], case["now_local"])
        if actual == expected:
            passed += 1
        else:
            failed += 1
            failures.append(f"{case['name']}:\n    HOME_RULES={expected}\n    loader    ={actual}")
    return passed, failed, failures


def run_real(artifact: dict) -> dict:
    """Attempt a live read-only /api/states parity check. Never persists the snapshot."""
    try:
        env = hostmod.read_env(hostmod.ENV_FILE)
        base = (env.get("HA_BASE_URL") or "").rstrip("/")
        token = env.get("HA_LLAT") or ""
        if not base or not token:
            return {"status": "skipped", "reason": "HA_BASE_URL/HA_LLAT missing"}
        states = hostmod.fetch_ha_states(base, token, hostmod.HA_TIMEOUT_S)
        now_utc = datetime.now(timezone.utc)
        now_local = now_utc.astimezone(hostmod.HOME_TZ)
        expected = _norm(hostmod.detect_home(states, now_utc, now_local))
        actual = evaluate_model(artifact, states, now_utc, now_local)
        return {"status": "match" if actual == expected else "mismatch",
                "expected": expected, "actual": actual, "entity_count": len(states)}
    except Exception as exc:                       # noqa: BLE001 — degrade honestly
        return {"status": "unreachable", "reason": repr(exc)}


def main() -> int:
    artifact = load_artifact()
    passed, failed, failures = run_equivalence(artifact)
    print(f"engine-equivalence: {passed} passed, {failed} failed "
          f"({passed + failed} enumerated snapshots)")
    for f in failures:
        print("  FAIL", f)
    real = run_real(artifact)
    print(f"real-data parity: {real['status']}"
          + (f" — {real.get('reason')}" if real.get("reason") else "")
          + (f" — {real.get('entity_count')} entities, tokens={real.get('actual')}"
             if real["status"] in ("match", "mismatch") else ""))
    return 0 if failed == 0 and real["status"] in ("match", "skipped", "unreachable") else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
