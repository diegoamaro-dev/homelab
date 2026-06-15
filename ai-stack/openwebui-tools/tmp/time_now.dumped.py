"""
title: Amarolab time_now
author: amarolab
author_url: https://github.com/amaroou
description: Returns the current time in a specified timezone. Canary Tool for the Amarolab Assistant - exercises the full Open WebUI Tools pipeline end-to-end.
version: 0.1.0
license: MIT
requirements:
"""

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


def _audit(tool, args, *, user="diego", allowed=True, result_code="ok", duration_ms=None):
    """Append one JSON line per Tool call. Never raises."""
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

from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo, available_timezones
import json
import time

from pydantic import BaseModel, Field


class Tools:
    class Valves(BaseModel):
        default_timezone: str = Field(
            default="Europe/Madrid",
            description="Timezone used when the caller does not supply one (Amarolab D-19).",
        )
        max_per_minute: int = Field(
            default=60, ge=1, le=600,
            description="Per-process per-Tool rate limit (resets on openwebui restart).",
        )

    def __init__(self) -> None:
        self.valves = self.Valves()
        self.citation = False

    def time_now(
        self,
        timezone: str = "Europe/Madrid",
        format: Literal["iso", "human", "unix"] = "iso",
    ) -> str:
        """
        Get the current time. Call this whenever the user asks the date, the day, the weekday, or the clock time. Do not answer from memory - the model's training cutoff is not the current date.

        :param timezone: IANA timezone name (e.g. "Europe/Madrid", "Asia/Tokyo", "UTC"). Defaults to Europe/Madrid.
        :param format: Output flavour preferred by the caller - "iso" (RFC 3339), "human" (readable English), or "unix" (epoch seconds). The response always includes all representations.
        :return: JSON string with now, unix, timezone, weekday, date, time, human, format_requested. On error: {"error": "...", "code": "..."}.
        """
        t0 = time.monotonic()
        tz = timezone or self.valves.default_timezone

        if tz not in available_timezones():
            _audit("time_now", {"timezone": tz, "format": format},
                   allowed=False, result_code="bad_tz")
            return json.dumps({
                "error": "unknown timezone",
                "code": "bad_tz",
                "timezone": tz,
            })

        if not _RateLimiter.check("time_now", self.valves.max_per_minute):
            _audit("time_now", {"timezone": tz, "format": format},
                   allowed=False, result_code="rate_limited")
            return json.dumps({
                "error": "rate limit exceeded",
                "code": "rate_limited",
            })

        now = datetime.now(ZoneInfo(tz))
        result = {
            "now": now.isoformat(timespec="seconds"),
            "unix": int(now.timestamp()),
            "timezone": tz,
            "weekday": now.strftime("%A"),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "human": now.strftime("%A %d %B %Y, %H:%M %Z"),
            "format_requested": format,
        }
        _audit("time_now", {"timezone": tz, "format": format},
               duration_ms=int((time.monotonic() - t0) * 1000))
        return json.dumps(result, ensure_ascii=False)
