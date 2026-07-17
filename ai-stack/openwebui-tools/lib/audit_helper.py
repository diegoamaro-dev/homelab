"""
amarolab_audit_helper — inline-only helper text.

This file is the canonical source of the audit + rate-limit helpers
that every Amarolab Open WebUI Tool inlines via ../bin/install_tool.

Do NOT `import` this file from a Tool. Open WebUI 0.8.10 executes each
Tool in its own `tool_{id}` module namespace; cross-module imports do
not resolve.

Convention: at install time, `bin/install_tool` replaces the literal
marker

    # @@AMAROLAB_INLINE:audit_helper@@

in a Tool source with everything between the `# --- INLINE START ---`
and `# --- INLINE END ---` lines below. Everything outside those
markers (including this docstring) is dropped.

Exposed inlined symbols (all underscore-prefixed so they are not
treated as Tool methods by Open WebUI's `get_functions_from_tool`):

    _audit(tool, args, *, user="diego", allowed=True, result_code="ok", duration_ms=None, extra=None) -> None
    _RateLimiter.check(tool, max_per_minute) -> bool
    _amarolab_redact(d) -> dict
    _AMAROLAB_AUDIT_LOG: Path

Audit log location (matches Amarolab D-07 / D-21):
    container: /app/backend/data/amarolab-audit.log
    host:      /srv/homelab/data/openwebui/amarolab-audit.log
"""

# --- INLINE START ---
import json as _amarolab_json
import os as _amarolab_os
import time as _amarolab_time
import uuid as _amarolab_uuid
from datetime import datetime as _amarolab_datetime, timezone as _amarolab_timezone
from pathlib import Path as _amarolab_path

_AMAROLAB_AUDIT_LOG = _amarolab_path(_amarolab_os.environ.get(
    "AMAROLAB_AUDIT_LOG",
    "/app/backend/data/amarolab-audit.log",
))

_AMAROLAB_REDACT_KEYS = {"password", "token", "secret", "api_key", "authorization"}


def _amarolab_redact(d):
    if not isinstance(d, dict):
        return d
    out = {}
    for k, v in d.items():
        if isinstance(k, str) and k.lower() in _AMAROLAB_REDACT_KEYS:
            out[k] = "<redacted>"
        elif isinstance(v, dict):
            out[k] = _amarolab_redact(v)
        else:
            out[k] = v
    return out


def _audit(tool, args, *, user="diego", allowed=True, result_code="ok", duration_ms=None,
           extra=None):
    """Append one JSON line per Tool call. Never raises.

    `extra` merges additive top-level fields (ER-1.4 — `registry_target`, `resolved_to`).
    It is applied AFTER the fixed keys and can only ADD: a colliding key is
    dropped, never allowed to overwrite. So the fixed keys' names, values and
    serialized order are untouched by construction, and a caller passing no
    `extra` produces a byte-identical line to before the parameter existed.
    Additive-only is enforced rather than trusted because this is an evidence
    record: an `extra` that could silently rewrite `result_code` or `args` would
    be a way to log a claim that never happened.

    Facts about the call belong here rather than in `args`, which is a snapshot
    of what the caller actually passed and must stay that.
    """
    line = {
        "ts": _amarolab_datetime.now(_amarolab_timezone.utc).isoformat(),
        "id": str(_amarolab_uuid.uuid4()),
        "user": user,
        "tool": tool,
        "args": _amarolab_redact(args),
        "allowed": allowed,
        "result_code": result_code,
        "duration_ms": duration_ms,
    }
    if extra:
        for _k, _v in _amarolab_redact(extra).items():
            if _k not in line:
                line[_k] = _v
    try:
        _AMAROLAB_AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with _AMAROLAB_AUDIT_LOG.open("a", encoding="utf-8") as f:
            f.write(_amarolab_json.dumps(line, ensure_ascii=False) + "\n")
    except OSError:
        pass  # never fail a Tool because audit can't write


class _RateLimiter:
    """Per-process per-Tool counter. Resets when openwebui restarts."""
    _counts = {}

    @classmethod
    def check(cls, tool, max_per_minute):
        now = _amarolab_time.monotonic()
        window = cls._counts.setdefault(tool, [])
        cutoff = now - 60.0
        window[:] = [t for t in window if t > cutoff]
        if len(window) >= max_per_minute:
            return False
        window.append(now)
        return True
# --- INLINE END ---
