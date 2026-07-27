"""
title: Aurora Context Injector
author: amarolab
description: F-3a situational-awareness Filter. inlet: on the first message of a conversation, prepends the nightly-generated Aurora context (/opt/aurora/aurora-context.md) as a system message so Aurora can answer "how is the lab?" with no tool call. outlet: on a same-night operational recap answered from system_status, deterministically appends the mandatory AD-04 disclosure that the same-night digest is not yet retrievable via rag_search (G-F4-06). Dumb delivery only — freshness decided from aurora-context.json (AD-10); construction lives in bin/aurora-context.
version: 0.2.0
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
#
# ---------------------------------------------------------------------------
# outlet (v0.2.0) — G-F4-06 mandatory same-night disclosure (AD-04 / AF-04).
#
# WHY THIS IS DETERMINISTIC LOGIC AND NOT A PROMPT INSTRUCTION.
# G-F4-06 requires, as a MANDATORY conjunct, that when "what happened last
# night?" is answered from system_status, Aurora also states the same-night
# digest is not yet RAG-retrievable (~22h indexing lag). Two prompt-only
# reinforcement iterations were tried in params.system and both FAILED on
# qwen2.5:7b-instruct (2026-07-27): the routing was corrected (rag_search ->
# system_status) but the disclosure sentence was still dropped, because the
# "# Style: Concise / Answer first / No preamble" directive prunes it at
# generation time. A 7B cannot be made to emit a mandatory-every-time sentence
# reliably by prompting. The operator therefore approved (2026-07-27) the
# smallest deterministic mechanism: append the sentence in the outlet.
#
# TRIGGER (all three required; fails closed on any doubt):
#   1. the answer's source is system_status  (source.name contains
#      "system_status"). Historical/older-night queries route to rag_search
#      (source.name "rag_search/..."), so they can NEVER satisfy this and are
#      structurally excluded — this is the "never trigger for historical"
#      guarantee, proven against real data 2026-07-27.
#   2. the user's question is a recent-night recap (RECAP markers), so plain
#      live-health system_status answers ("¿cómo está el lab?") are excluded.
#   3. the disclosure is not already present (idempotent).
# Fully reversible: Valves.same_night_disclosure=False disables just the outlet
# (inlet untouched); or restore the prior function content. Never raises (§7).
# ---------------------------------------------------------------------------

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

# --- outlet (G-F4-06) constants ------------------------------------------
DISCLOSURE_ES = (
    "El resumen operativo de esta noche aún no es consultable mediante "
    "rag_search (~22 h de retardo de indexado); esta respuesta procede de "
    "system_status."
)
DISCLOSURE_EN = (
    "The same-night operational digest is not yet retrievable via rag_search "
    "(~22h indexing lag); this answer comes from system_status."
)
_RECAP_MARKERS = (
    "anoche", "last night", "esta madrugada", "overnight",
    "durante la noche", "during the night", "por la noche",
    "último ciclo", "ultimo ciclo", "nightly cycle", "last cycle",
    "esta noche",
)
_NIGHT_WORDS = ("noche", "night", "madrugada")
_HAPPENED_WORDS = (
    "pas", "happen", "ocurr", "hubo", "novedad", "importante",
    "important", " ran", " run", "sucedi", "aconteci",
)


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
        same_night_disclosure: bool = Field(
            default=True,
            description=(
                "outlet: append the G-F4-06 same-night AD-04 disclosure on "
                "system_status recap answers. False disables ONLY the outlet."
            ),
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

    # --- outlet (G-F4-06) helpers -----------------------------------------

    @staticmethod
    def _answer_source_names(target: dict, body: dict):
        """Lower-cased source names for THIS answer only (not prior turns)."""
        out = []
        for bag in (target.get("sources"), body.get("sources")):
            if isinstance(bag, list):
                for s in bag:
                    if isinstance(s, dict):
                        src = s.get("source")
                        nm = src.get("name") if isinstance(src, dict) else s.get("name")
                        if nm:
                            out.append(str(nm).lower())
        return out

    @staticmethod
    def _is_recap(question: str) -> bool:
        t = (question or "").lower()
        if any(mk in t for mk in _RECAP_MARKERS):
            return True
        if any(n in t for n in _NIGHT_WORDS) and any(h in t for h in _HAPPENED_WORDS):
            return True
        return False

    @staticmethod
    def _already_disclosed(content: str) -> bool:
        c = (content or "").lower()
        return ("rag_search" in c) and any(
            k in c for k in (
                "indexado", "indexing lag", "not yet retrievable",
                "no es consultable", "todavía no", "aún no",
            )
        )

    @staticmethod
    def _is_spanish(question: str) -> bool:
        if any(ch in (question or "") for ch in "¿¡ñÑáéíóúÁÉÍÓÚ"):
            return True
        t = " " + (question or "").lower() + " "
        es = sum(w in t for w in (
            " qué", " que ", " pasó ", " paso ", " anoche", " noche", " cómo",
            " como ", " está", " sistema", " del ", " ayer", " ocurrió",
        ))
        en = sum(w in t for w in (
            " the ", " what ", " did ", " happen", " last ", " night ",
            " during ", " system ", " anything", " last night",
        ))
        return es >= en  # tie -> Spanish (Aurora default)

    # --- Open WebUI hooks --------------------------------------------------

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

    def outlet(self, body: dict) -> dict:
        # G-F4-06: deterministically guarantee the AD-04 same-night disclosure
        # on system_status recap answers (see module header for rationale).
        try:
            if not self.valves.enabled or not self.valves.same_night_disclosure:
                return body

            messages = body.get("messages", []) or []
            if not messages:
                return body

            # target = the assistant message just produced (id match, else last)
            target = None
            mid = body.get("id")
            if mid:
                for m in messages:
                    if m.get("id") == mid and m.get("role") == "assistant":
                        target = m
                        break
            if target is None:
                for m in reversed(messages):
                    if m.get("role") == "assistant":
                        target = m
                        break
            if target is None or not isinstance(target.get("content"), str):
                return body

            content = target["content"]

            # the user's question this answer responds to
            question = ""
            for m in reversed(messages):
                if m.get("role") == "user" and isinstance(m.get("content"), str):
                    question = m["content"]
                    break

            names = self._answer_source_names(target, body)
            if not any("system_status" in n for n in names):
                self._log(event="outlet_skip", reason="not_system_status", srcs=names)
                return body
            if not self._is_recap(question):
                self._log(event="outlet_skip", reason="not_recap")
                return body
            if self._already_disclosed(content):
                self._log(event="outlet_skip", reason="already_disclosed")
                return body

            es = self._is_spanish(question)
            disclosure = DISCLOSURE_ES if es else DISCLOSURE_EN
            target["content"] = content.rstrip() + "\n\n" + disclosure
            body["messages"] = messages
            self._log(event="outlet_append", lang=("es" if es else "en"), chars=len(disclosure))
        except Exception as exc:
            # §7: never crash the conversation.
            self._log(event="outlet_error", err=f"{type(exc).__name__}:{exc}")
        return body
