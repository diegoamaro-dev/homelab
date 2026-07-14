"""
title: System Status
author: amarolab
description: AMAROLAB homelab operational status — world verdict + home state,
             ingest pipeline, backup, container health, Torre GPU reachability,
             and live system metrics.
version: 0.3.0
"""

import json
import re
import socket
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import psutil

AURORA_CTX    = Path("/opt/aurora/aurora-context.json")
AURORA_MD     = Path("/opt/aurora/aurora-context.md")
HEALTH_FILE   = Path("/opt/ingest/logs/health.json")
TORRE_URL     = "http://100.91.154.124:11434/api/tags"
TORRE_TIMEOUT = 3
STALE_HOURS   = 26


# ── Utilities ──────────────────────────────────────────────────────────────

def _parse_ts(s) -> datetime | None:
    if not s:
        return None
    try:
        clean = re.sub(r"\.\d+", "", str(s))
        clean = re.sub(r"Z$", "+00:00", clean)
        return datetime.fromisoformat(clean).astimezone(timezone.utc)
    except Exception:
        return None


def _age_h(ts, now) -> float:
    if ts is None:
        return float("inf")
    return (now - ts).total_seconds() / 3600


def _fmt_h(h) -> str:
    if h == float("inf"):
        return "unknown"
    return f"{h:.1f}h ago"


def _ts_disp(ts_str) -> str:
    if not ts_str:
        return "unknown"
    return ts_str[:16].replace("T", " ") + " UTC"


def _probe_torre() -> tuple[bool, str]:
    try:
        t0 = time.monotonic()
        resp = urllib.request.urlopen(TORRE_URL, timeout=TORRE_TIMEOUT)
        ms = int((time.monotonic() - t0) * 1000)
        if 200 <= resp.status < 300:
            return True, f"reachable ({ms}ms)"
        return False, f"reachable but returned HTTP {resp.status}"
    except socket.timeout:
        return False, f"unreachable — timeout ({TORRE_TIMEOUT}s)"
    except Exception as exc:
        return False, f"unreachable — {type(exc).__name__}"


def _live_system() -> str:
    try:
        cpu  = psutil.cpu_percent(interval=1)
        ram  = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent
        return f"CPU {cpu}% | RAM {ram}% | Disk {disk}%"
    except Exception as exc:
        return f"unavailable ({exc})"


# ── Context readers ────────────────────────────────────────────────────────

def _read_home_block():
    """Echo the rendered Home State block from the context md (WM-5 projection;
    device detail lives in the md per D1). Returns the block text, or None."""
    try:
        md = AURORA_MD.read_text(encoding="utf-8")
    except Exception:
        return None
    idx = md.find("Home State:")
    return md[idx:].strip() if idx != -1 else None


def _from_aurora_ctx(ctx, now):
    """Extract display strings from a parsed aurora-context.json dict."""
    overall   = ctx.get("overall_status", "unknown")
    sig_miss  = ctx.get("signals_missing") or []
    ingest    = ctx.get("ingest") or {}
    backup    = ctx.get("backup") or {}
    audit     = ctx.get("audit") or {}
    containers = ctx.get("containers") or {}

    # Ingest line
    ist = ingest.get("status", "unknown")
    if ist == "ok":
        last_end = ingest.get("last_run_end")
        last_rc  = ingest.get("last_run_rc")
        ingest_line = (
            f"ok — last run {_ts_disp(last_end)}"
            f" ({_fmt_h(_age_h(_parse_ts(last_end), now))}, rc={last_rc})"
        )
    elif ist == "signal_missing":
        ingest_line = "signal missing"
    else:
        last_end = ingest.get("last_run_end")
        last_rc  = ingest.get("last_run_rc")
        ingest_line = (
            f"error — failed (rc={last_rc})"
            f" at {_ts_disp(last_end)}"
            f" ({_fmt_h(_age_h(_parse_ts(last_end), now))})"
        )

    # Backup line
    bst = backup.get("status", "unknown")
    if bst == "ok":
        snap_id  = backup.get("snapshot_id")
        snap_ts  = backup.get("snapshot_time")
        snap_mb  = backup.get("data_added_mb")
        mb_str   = f", {snap_mb} MB added" if snap_mb is not None else ""
        backup_line = (
            f"ok — snapshot {snap_id}"
            f" at {_ts_disp(snap_ts)}"
            f" ({_fmt_h(_age_h(_parse_ts(snap_ts), now))}{mb_str})"
        )
    elif bst == "no_snapshot_tonight":
        snap_ts = backup.get("snapshot_time")
        snap_desc = (
            f"last: {_ts_disp(snap_ts)} ({_fmt_h(_age_h(_parse_ts(snap_ts), now))})"
            if snap_ts else "no prior snapshot"
        )
        backup_line = f"no snapshot tonight — {snap_desc}"
    elif bst == "signal_missing":
        backup_line = "signal missing"
    else:
        backup_line = "error — backup probe failed"

    # Audit line
    ast   = audit.get("status", "unknown")
    age_d = audit.get("age_days")
    if ast == "ok":
        audit_line = f"ok — last entry age {age_d} days"
    elif ast == "stale":
        audit_line = f"stale — last entry {age_d} days ago (threshold 7 days)"
    elif ast == "signal_missing":
        audit_line = "signal missing"
    else:
        audit_line = f"{ast} — age {age_d} days"

    # Containers line
    all_running = containers.get("all_running")
    count       = containers.get("count")
    deg         = containers.get("degraded") or []
    if all_running is None:
        containers_line = "signal missing"
    elif all_running:
        containers_line = f"{count}/{count} running"
    else:
        running_n = (count - len(deg)) if count is not None else "?"
        containers_line = f"{running_n}/{count} running — stopped: {', '.join(deg)}"

    # Reasons for machine-readable summary
    reasons = []
    if bst not in ("ok", "signal_missing"):
        reasons.append(
            "backup outside freshness window" if bst == "no_snapshot_tonight"
            else f"backup: {bst}"
        )
    if ist not in ("ok", "signal_missing"):
        reasons.append(f"ingest: {ist}")
    if ast not in ("ok", "signal_missing"):
        reasons.append(f"audit: {ast}")
    if all_running is False and deg:
        reasons.append(f"containers: {len(deg)} stopped ({', '.join(deg)})")

    # WM-5: the home region verdict (already folded into overall_status by
    # aurora-context). Surfaced here so a status query is never home-blind (R-F5-A).
    world        = ctx.get("world") or {}
    home_verdict = (world.get("regions") or {}).get("home")
    if home_verdict in ("medium", "high", "critical"):
        reasons.append(f"home: {home_verdict} anomaly")

    sig_miss_str = ", ".join(sig_miss) if sig_miss else "none"

    return {
        "overall":       overall,
        "world_verdict": world.get("verdict"),
        "home_verdict":  home_verdict,
        "reasons":       reasons,
        "ingest":        ingest_line,
        "backup":        backup_line,
        "audit":         audit_line,
        "containers":    containers_line,
        "sig_miss":      sig_miss_str,
    }


def _from_health_fallback(now):
    """Read health.json directly when aurora-context.json is not mounted."""
    ingest_line = "not available"
    audit_line  = "not available"

    if HEALTH_FILE.exists():
        try:
            h      = json.loads(HEALTH_FILE.read_text(encoding="utf-8"))
            ingest = h.get("ingest") or {}
            audit  = h.get("audit") or {}

            ist      = ingest.get("last_run_status", "unknown")
            last_end = ingest.get("last_run_end")
            last_rc  = ingest.get("last_run_rc")
            age_str  = _fmt_h(_age_h(_parse_ts(last_end), now))
            if ist == "ok":
                ingest_line = (
                    f"ok — last run {_ts_disp(last_end)} ({age_str}, rc={last_rc})"
                )
            else:
                ingest_line = (
                    f"error — failed (rc={last_rc})"
                    f" at {_ts_disp(last_end)} ({age_str})"
                )

            ast   = audit.get("status", "unknown")
            age_d = audit.get("age_days")
            if ast == "ok":
                audit_line = f"ok — last entry age {age_d} days"
            elif ast == "stale":
                audit_line = f"stale — last entry {age_d} days ago"
            else:
                audit_line = f"{ast}"

        except Exception as exc:
            ingest_line = f"health.json error: {exc}"
            audit_line  = "health.json error"
    else:
        ingest_line = "not available (health.json missing)"
        audit_line  = "not available (health.json missing)"

    return {
        "overall":       "partial",
        "world_verdict": None,
        "home_verdict":  None,
        "reasons":       ["aurora-context.json not mounted — backup and container signals unavailable"],
        "ingest":        ingest_line,
        "backup":        "not available (context not mounted)",
        "audit":         audit_line,
        "containers":    "not available (context not mounted)",
        "sig_miss":      "aurora-context.json",
    }


# ── Main runner ────────────────────────────────────────────────────────────

def _run() -> str:
    now     = datetime.now(timezone.utc)
    now_str = now.strftime("%Y-%m-%d %H:%M UTC")

    # Live Torre probe (always runs first, independent of context)
    torre_ok, torre_desc = _probe_torre()

    # Context source
    ctx_header = ""
    data = None

    if AURORA_CTX.exists():
        try:
            raw = json.loads(AURORA_CTX.read_text(encoding="utf-8"))
            ctx_ts  = _parse_ts(raw.get("generated_at"))
            ctx_age = _age_h(ctx_ts, now)
            stale   = " — STALE" if ctx_age > STALE_HOURS else ""
            ctx_header = (
                f"{_ts_disp(raw.get('generated_at'))}"
                f" ({_fmt_h(ctx_age)}){stale}"
            )
            data = _from_aurora_ctx(raw, now)
        except Exception as exc:
            ctx_header = f"unparseable ({exc})"
            data = None

    if data is None:
        ctx_header = ctx_header or "not mounted (aurora-context.json unavailable — F2-6 pending)"
        data = _from_health_fallback(now)

    # Add Torre to reasons if unreachable
    reasons = list(data["reasons"])
    if not torre_ok:
        reasons.append(f"Torre: {torre_desc}")
    if not reasons:
        reasons.append("all checked signals ok")

    reason_block = "\n".join(f"  • {r}" for r in reasons)
    system_line  = _live_system()
    home_block   = _read_home_block() or "Home State: (not available)"

    output = (
        f"AMAROLAB System Status — {now_str}\n"
        f"\n"
        f"Overall: {data['overall']}\n"
        f"Reasons:\n{reason_block}\n"
        f"\n"
        f"---\n"
        f"\n"
        f"Context:     {ctx_header}\n"
        f"Torre (live): {torre_desc}\n"
        f"System:      {system_line}\n"
        f"\n"
        f"Ingest:      {data['ingest']}\n"
        f"Backup:      {data['backup']}\n"
        f"Audit:       {data['audit']}\n"
        f"Containers:  {data['containers']}\n"
        f"\n"
        f"{home_block}\n"
        f"\n"
        f"Signals missing: {data['sig_miss']}\n"
    )
    return output


class Tools:
    def system_status(self) -> str:
        """
        Get the current AMAROLAB homelab system status: ingest pipeline health,
        nightly backup status, audit log freshness, container health, Torre GPU
        node reachability, and live CPU/RAM/disk usage. Call this when the user
        asks about homelab health, whether the backup ran, whether services are
        up, or whether Torre is reachable.
        """
        try:
            return _run()
        except Exception as exc:
            return f"AMAROLAB System Status — error\n\n[Tool error: {type(exc).__name__}: {exc}]"
