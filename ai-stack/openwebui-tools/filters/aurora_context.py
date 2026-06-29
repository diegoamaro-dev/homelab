"""
title: Aurora Context Injector
author: amarolab
description: F-3a situational-awareness Filter. On the first message of a conversation, prepends the nightly-generated Aurora context (/opt/aurora/aurora-context.md) as a system message so Aurora can answer "how is the lab?" with no tool call. Dumb delivery only — freshness decided from aurora-context.json (AD-10); construction lives in bin/aurora-context.
version: 0.1.0
required_open_webui_version: 0.8.10
license: MIT
"""

# F-3a — Open WebUI Awareness Filter.
#
# Authoritative spec: 04_ai_system/phase_f_architecture.md §7 (Filter behaviour
# contract) + AD-08..AD-11. Mechanism validated in F-0 (AF-01):
#   - inlet fires every request; inject only when len(messages) == 1 (message 1)
#   - reads container path /opt/aurora (bind-mounted read-only from ai-stack/aurora)
#   - never raises; on any failure the conversation continues unchanged
#
# This Filter contains NO domain logic. It reads two pre-generated artifacts
# (json for the freshness decision, md for the injected prose) and prepends the
# prose as a system message. It does not construct context from raw signals
# (that is bin/aurora-context — RA-03 rejected putting construction here).

import json
import os
from datetime import datetime, timezone

from pydantic import BaseModel, Field

CONTEXT_JSON = "/opt/aurora/aurora-context.json"   # freshness decision (AD-10)
CONTEXT_MD = "/opt/aurora/aurora-context.md"       # injected payload (AD-11)
FRESH_HOURS = 24.0                                 # <=24h: inject as-is
STALE_HOURS = 26.0                                 # >26h: fallback only (§7)
MARKER = "[Aurora context"                          # idempotency / prompt marker
FALLBACK = "Context file unavailable — use system_status for current state."


class Filter:
    class Valves(BaseModel):
        enabled: bool = Field(
            default=True,
            description="Master switch. When false the Filter is a no-op.",
        )
        priority: int = Field(
            default=0,
            description="Filter execution priority (lower runs earlier).",
        )

    def __init__(self) -> None:
        self.valves = self.Valves()

    # --- helpers -----------------------------------------------------------

    def _log(self, **kw) -> None:
        # One structured line per inlet decision -> visible in `docker logs openwebui`.
        # Satisfies the "verified in inlet logs" clause of G-F3-2. Never raises.
        try:
            print("aurora_context_filter " + json.dumps(kw, ensure_ascii=False), flush=True)
        except Exception:
            pass

    def _build_block(self):
        """Return (text, reason). text is None when the §7 fallback must be used."""
        now = datetime.now(timezone.utc)
        # Freshness decision from the JSON (robust machine field, not file mtime).
        try:
            with open(CONTEXT_JSON, "r", encoding="utf-8") as fh:
                meta = json.load(fh)
            gen = str(meta.get("generated_at", ""))
            g = datetime.fromisoformat(gen.replace("Z", "+00:00"))
            age_h = (now - g).total_seconds() / 3600.0
        except Exception as exc:
            return None, f"json_unavailable:{type(exc).__name__}"

        if age_h > STALE_HOURS:
            return None, f"stale:{age_h:.1f}h"

        try:
            with open(CONTEXT_MD, "r", encoding="utf-8") as fh:
                md = fh.read().strip()
        except Exception as exc:
            return None, f"md_unavailable:{type(exc).__name__}"
        if not md:
            return None, "md_empty"

        if age_h > FRESH_HOURS:  # graduated 24h..26h note
            md = f"{md}\n\n[context is {age_h:.0f} hours old — use system_status for current state]"
        return md, f"ok:{age_h:.1f}h"

    # --- Open WebUI hook ---------------------------------------------------

    def inlet(self, body: dict) -> dict:
        try:
            if not self.valves.enabled:
                return body

            messages = body.get("messages", []) or []
            # Message-1 discriminator validated in AF-01: body holds exactly the
            # single user message on the first turn; 3 messages on the second.
            first_turn = len(messages) == 1 and (messages[0].get("role") == "user")
            already = any(
                m.get("role") == "system"
                and isinstance(m.get("content"), str)
                and MARKER in m["content"]
                for m in messages
            )
            if not first_turn or already:
                self._log(event="skip", n=len(messages), first_turn=first_turn, already=already)
                return body

            block, reason = self._build_block()
            inject = block if block is not None else FALLBACK
            messages.insert(0, {"role": "system", "content": inject})
            body["messages"] = messages
            self._log(event="inject", reason=reason, fallback=(block is None), chars=len(inject))
        except Exception as exc:
            # §7: never crash the conversation.
            self._log(event="error", err=f"{type(exc).__name__}:{exc}")
        return body
