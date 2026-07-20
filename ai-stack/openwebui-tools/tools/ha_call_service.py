"""
title: Amarolab ha_call_service
author: amarolab
author_url: https://github.com/amaroou
description: Call one Home Assistant service against a single entity to perform an action (turn a switch or light on/off, open/close a cover, activate a scene, and similar). Allowed domains (closed set, D-12): light, switch, scene, cover, climate, media_player, script, automation, fan, vacuum, input_boolean, input_select, input_number. Anything outside the allowlist is refused before any HTTP request reaches Home Assistant. Pass the everyday name the user actually said — Spanish or English ("toldo", "impresora 3d") — or a canonical entity id; the Tool resolves it and never invents one. After the call it verifies the resulting state and claims success only when confirmed (otherwise "applied_unverified"). For reads ("is X on?") use ha_get_state instead.
version: 0.2.0
license: MIT
requirements:
"""

# @@AMAROLAB_INLINE:audit_helper@@

# @@AMAROLAB_INLINE:entity_resolver@@

import json
import os
import re
import time
from typing import Any, Literal

from pydantic import BaseModel, Field


# Phase C contract — locked. The grammar itself is unchanged at v0.2.0; its
# ROLE changed (spec §4). It was a validity gate: anything not matching was
# rejected `bad_entity_id`. It is now the id-shape test of the ER-1 resolution
# ladder step 4 — a match continues to Home Assistant exactly as today, and a
# non-match is a natural name that goes to the resolver instead of being
# rejected. Grammar mirrors ha_get_state: HA's documented `<domain>.<object_id>`
# lowercase + digits + underscores.
_ENTITY_ID_RE = re.compile(r"^[a-z_]+\.[a-z0-9_]+$")
_ENTITY_ID_MIN_LEN = 3
_ENTITY_ID_MAX_LEN = 128

# Service-name grammar from HA's REST API docs. Bounded length keeps
# a misbehaving LLM from sending a 10 MB string straight at HA.
_SERVICE_RE = re.compile(r"^[a-z_][a-z0-9_]*$")
_SERVICE_MIN_LEN = 1
_SERVICE_MAX_LEN = 64

# Defense against HA-side / LLM-side surprises.
#   service_data JSON-serialized payload cap: 4 KB.
#   ha_response (HA's "list of states that changed") cap: 8 KB
#   with a "...<truncated>" marker beyond.
_SERVICE_DATA_CAP = 4096
_HA_RESPONSE_CAP = 8192
_HA_RESPONSE_TRUNCATION_MARKER = "...<truncated>"

# Per-call HTTP timeout. HA is on the trusted LAN.
_HTTP_TIMEOUT_S = 5.0

# ER-1-C1 — mandatory after-only write verification (spec §3.1). After the POST
# returns, the Tool reads back /api/states/<entity_id> and compares to the
# expected state below; success is claimed ONLY when that read-back confirms it,
# otherwise the honest `applied_unverified`. The POST itself is UNCHANGED — C1
# changes only what the Tool is willing to claim afterwards.
#
# D-ER-10 closed expected-state map, keyed by service name. Every other service
# (including `toggle`, which D-ER-10 defers) resolves to `applied_unverified`:
# after-only verification has no before-state, so only these four have an
# unambiguous expected result.
_C1_EXPECTED_STATE = {
    "turn_on": "on",
    "turn_off": "off",
    "open_cover": "open",
    "close_cover": "closed",
}

# Rule B verification window (ratified 2026-07-20 from the pre-registered N=20
# measurement on switch.impresora_3d: first read stale 20/20; state visible in
# 52–159 ms). HA returns the service POST in ~1.6 ms — before the Zigbee device
# echoes its new state back through Z2M -> MQTT -> HA — so an immediate read is
# stale. Verify by: check immediately, then poll at 100 ms within a 500 ms
# budget; success on first match; budget exhausted -> applied_unverified. The
# 500 ms floor = min(2000, max(500, 2 x max-observed 158.7 ms)) leaves the worst
# observed confirmation ~3x inside budget.
_C1_VERIFY_BUDGET_S = 0.500
_C1_VERIFY_POLL_S = 0.100

# THE SAFETY BOUNDARY — D-12 / readiness review §5.
# This is the runtime allowlist re-check that fires as the very
# first action inside ha_call_service(). The Literal enum on the
# method signature (schema layer) gives the LLM a typed enum and
# OWUI 0.8.10's spec builder serialises it; this frozenset is the
# runtime layer that holds even if the schema is ever bypassed.
# Closed for v1. Adding to this set requires a new locked decision.
_ALLOWED_DOMAINS = frozenset({
    "light",           # turn lights on/off, set brightness/color
    "switch",          # generic on/off switches
    "scene",           # activate pre-saved scenes
    "cover",           # blinds, curtains, garage doors
    "climate",         # thermostats, HVAC modes
    "media_player",    # play/pause/volume on speakers/TVs
    "script",          # user-defined HA scripts (already-allowlisted by being defined)
    "automation",      # toggle/trigger user-defined automations
    "fan",             # fans, including ceiling fans
    "vacuum",          # start/stop/return_to_base
    "input_boolean",   # user-defined boolean helper
    "input_select",    # user-defined dropdown helper
    "input_number",    # user-defined number helper
})

# Documented-but-not-enforced. The default-deny in
# `_ALLOWED_DOMAINS` covers them; this constant exists so a future
# reader (or future AI assistant) thinks twice before extending the
# allowlist with anything in here. Any addition there is a v1.1+
# design decision, not a Phase C change.
_EXPLICITLY_DENIED = frozenset({
    "homeassistant",          # restart, reload, etc.
    "recorder",               # purge, disable, etc. — the canonical refusal target
    "hassio",                 # supervisor / addon control
    "system_log",             # log writes
    "backup",                 # create/restore HA backups
    "auth",                   # auth subsystem
    "persistent_notification",  # notifications
    "notify",                 # outbound messaging
    "mqtt",                   # raw MQTT publish
    "shell_command",          # user-defined shell commands
})


class Tools:
    class Valves(BaseModel):
        max_per_minute: int = Field(
            default=10, ge=1, le=600,
            description="Per-process per-Tool rate limit (resets on openwebui restart). Lower than ha_get_state (60) and rag_search (30) because writes mutate external state — a velocity guard against runaway model behaviour.",
        )

    # Lazy runtime state. Class-level (single httpx.Client + bearer
    # per openwebui process). HA_LLAT is read from os.environ exactly
    # once inside _init(); it never enters args, never appears in
    # return JSON, never reaches the audit log. The bearer string
    # lives only in Tools._bearer (in-process memory) and the
    # outbound Authorization header.
    _httpx_client = None
    _base_url = None
    _bearer = None

    def __init__(self) -> None:
        self.valves = self.Valves()
        self.citation = False

    def _init(self) -> None:
        if Tools._httpx_client is None:
            import httpx

            base = os.environ.get("HA_BASE_URL", "").strip()
            tok = os.environ.get("HA_LLAT", "").strip()
            if not base:
                raise RuntimeError("HA_BASE_URL not set in container env")
            if not tok:
                raise RuntimeError("HA_LLAT not set in container env")

            Tools._base_url = base.rstrip("/")
            Tools._bearer = f"Bearer {tok}"
            Tools._httpx_client = httpx.Client(timeout=_HTTP_TIMEOUT_S)

    def _read_state(self, entity_id: str) -> str | None:
        """Read /api/states/<entity_id> and return the `state` string, or None on
        any failure. Used ONLY by the ER-1-C1 read-back verification; it never
        raises and reuses the initialised class client + bearer. This is
        actuation verification, not awareness (INV-19): the result is compared to
        the D-ER-10 expected state and never feeds home.anomalies or the context.
        """
        try:
            r = Tools._httpx_client.get(
                f"{Tools._base_url}/api/states/{entity_id}",
                headers={"Authorization": Tools._bearer, "Accept": "application/json"},
            )
            if r.status_code == 200:
                return r.json().get("state")
        except Exception:
            return None
        return None

    def ha_call_service(
        self,
        domain: Literal[
            "light",
            "switch",
            "scene",
            "cover",
            "climate",
            "media_player",
            "script",
            "automation",
            "fan",
            "vacuum",
            "input_boolean",
            "input_select",
            "input_number",
        ],
        service: str,
        entity_id: str,
        service_data: dict | None = None,
    ) -> str:
        """
        Call one Home Assistant service against a single entity to perform an action: turn a switch or light on/off, open or close a cover, activate a scene, set a thermostat, play media, toggle a user-defined automation. Allowed domains: light, switch, scene, cover, climate, media_player, script, automation, fan, vacuum, input_boolean, input_select, input_number. Anything else is refused before any HTTP request leaves the assistant; do not retry an action under a different allowed domain. For reads (state queries like "is X on?") use ha_get_state instead.

        After issuing the call the Tool VERIFIES the resulting Home Assistant state and reports honestly: it claims success only when the state was confirmed. A call HA accepted but that could not be confirmed comes back as result_code "applied_unverified" — surface that as "sent but not confirmed", never as done.

        :param domain: HA service domain. Must be one of the allowed values above; out-of-allowlist domains are refused.
        :param service: HA service name in lowercase snake_case (e.g. "turn_on", "turn_off", "open_cover", "close_cover", "set_temperature"). 1-64 characters; matches `^[a-z_][a-z0-9_]*$`.
        :param entity_id: The device to act on. Pass the everyday name the user actually said, in Spanish or English — "toldo", "impresora 3d", "puerta principal", "awning" — and this Tool resolves it to the real entity id. A canonical id ("switch.impresora_3d") is also accepted and passed straight through. NEVER invent an entity id: guessing an English-looking id for a device named in Spanish is the known failure mode. If the name is not recognised you get code "unknown_entity" plus a "candidates" list of what does exist — pick from it rather than guessing again. 3-128 characters.
        :param service_data: Optional extra data forwarded to HA as POST-body keys (e.g. {"brightness_pct": 60} for light.turn_on, {"hvac_mode": "heat"} for climate.set_hvac_mode). Must be a dict or null; must NOT contain a top-level "entity_id" key (the entity_id parameter owns that); JSON-serialised payload ≤ 4 KB.
        :return: JSON string. Verified success: {ok: true, domain, service, entity_id, ha_status, ha_response, result_code: "ok", verified: true, state_after}. Accepted but unverified: {ok: false, ..., result_code: "applied_unverified", verified: false, state_after}. Resolver miss: {code: "unknown_entity", candidates: [...]} and no HA call. Refusal: {allowed: false, domain, service, code: "refused", message}. Other errors: {error, code, ...}. ha_response is returned verbatim (truncated to 8 KB if very large) but is no longer interpreted — success is decided solely by the state read-back.
        """
        t0 = time.monotonic()
        args_snap = {
            "domain": domain,
            "service": service,
            "entity_id": entity_id,
            "service_data": service_data,
        }

        # ====================================================================
        # SAFETY BOUNDARY — D-12. Runtime allowlist re-check. THIS IS THE FIRST
        # action inside the method body: before service/entity_id validation,
        # before rate-limit, before _init(), before any HTTP request. Even if
        # a future change bypasses the Literal schema enum (e.g. free-form
        # tool_calls from the model, or a frontend change), this check holds.
        # No HTTP request is issued to Home Assistant on this path.
        # ====================================================================
        if domain not in _ALLOWED_DOMAINS:
            _audit("ha_call_service", args_snap, allowed=False, result_code="refused")
            return json.dumps({
                "allowed": False,
                "domain": domain,
                "service": service,
                "code": "refused",
                "message": (
                    f"I can change lights, scenes, climate, media, and similar "
                    f"— not '{domain}.{service}'."
                ),
            })

        # Input validation — service.
        if (not isinstance(service, str)
                or len(service) < _SERVICE_MIN_LEN
                or len(service) > _SERVICE_MAX_LEN):
            _audit("ha_call_service", args_snap, allowed=False, result_code="bad_service")
            return json.dumps({
                "error": f"service must be {_SERVICE_MIN_LEN}-{_SERVICE_MAX_LEN} characters",
                "code": "bad_service",
            })
        if not _SERVICE_RE.match(service):
            _audit("ha_call_service", args_snap, allowed=False, result_code="bad_service")
            return json.dumps({
                "error": "service must match lowercase snake_case grammar",
                "code": "bad_service",
            })

        # Step 3 — entity_id bounded/type check. UNCHANGED from v0.1.0 (spec §4):
        # it precedes resolution, so it still fires first and still answers
        # `bad_entity_id`. No audit_extra here — this is before resolution.
        if (not isinstance(entity_id, str)
                or len(entity_id) < _ENTITY_ID_MIN_LEN
                or len(entity_id) > _ENTITY_ID_MAX_LEN):
            _audit("ha_call_service", args_snap, allowed=False, result_code="bad_entity_id")
            return json.dumps({
                "error": f"entity_id must be {_ENTITY_ID_MIN_LEN}-{_ENTITY_ID_MAX_LEN} characters",
                "code": "bad_entity_id",
            })

        # Steps 4-6 — resolution (ER-1.4b). Slotted exactly where the old
        # id-shape rejection sat, so every preceding check (D-12 allowlist,
        # service validation, the length bound) is untouched and the rate
        # limiter still sees precisely the inputs it saw before: an input that
        # never reaches HA never reached the limiter at v0.1.0 either. This is
        # the identical ladder ha_get_state runs, plus ER-1-C1 at step 8.
        audit_extra = {}
        if _ENTITY_ID_RE.match(entity_id):
            # Step 4 — id-shaped: continue to Home Assistant EXACTLY as today,
            # whether or not the registry knows it (D-ER-9). The registry is
            # consulted for OBSERVABILITY ONLY and never to gate: `registry_target`
            # (D-ER-14) goes to the audit line and changes nothing about the
            # request. `is_target` answers None when the resolver is unavailable,
            # and the key is then omitted rather than recorded as false.
            resolved_id = entity_id
            registry_target = _EntityResolver.is_target(entity_id)
            if registry_target is not None:
                audit_extra["registry_target"] = registry_target
        else:
            # Step 5 — not id-shaped: a natural name. Normalize (D-ER-8) + closed
            # lookup. No fuzzy matching, no scoring, no LLM.
            if not _EntityResolver.available():
                _audit("ha_call_service", args_snap, allowed=False,
                       result_code="resolver_unavailable",
                       duration_ms=int((time.monotonic() - t0) * 1000))
                return json.dumps({
                    "error": "entity name resolution is unavailable; pass a canonical entity id",
                    "code": "resolver_unavailable",
                    "detail": _EntityResolver.reason(),
                })
            resolved_id = _EntityResolver.lookup(entity_id)
            if resolved_id is None:
                # Step 6 — miss: fail closed with ZERO HTTP calls. There is no
                # valid id to send, so nothing *can* pass through. The candidate
                # list is the corrective feedback that replaces guessing.
                _audit("ha_call_service", args_snap, allowed=False,
                       result_code="unknown_entity",
                       duration_ms=int((time.monotonic() - t0) * 1000))
                return json.dumps({
                    "entity_id": entity_id,
                    "error": f"'{entity_id}' is not an entity I model",
                    "code": "unknown_entity",
                    "candidates": _EntityResolver.candidates(),
                }, ensure_ascii=False)
            # An alias hit is a target by construction. `resolved_to` keeps the
            # audit line honest: without it `args.entity_id` says "toldo" and no
            # reader could tell what was actually actuated (the §1.2 defect).
            audit_extra["registry_target"] = True
            audit_extra["resolved_to"] = resolved_id

        # Input validation — service_data. Logic UNCHANGED from v0.1.0; the audit
        # lines now carry the additive resolution observability (audit_extra).
        if service_data is not None:
            if not isinstance(service_data, dict):
                _audit("ha_call_service", args_snap, allowed=False, result_code="bad_service_data",
                       extra=audit_extra or None)
                return json.dumps({
                    "error": "service_data must be a dict or null",
                    "code": "bad_service_data",
                })
            if "entity_id" in service_data:
                _audit("ha_call_service", args_snap, allowed=False, result_code="bad_service_data",
                       extra=audit_extra or None)
                return json.dumps({
                    "error": "service_data must not contain a top-level entity_id key (the entity_id parameter owns that)",
                    "code": "bad_service_data",
                })
            try:
                serialized_sd = json.dumps(service_data, ensure_ascii=False, default=str)
            except Exception as e:
                _audit("ha_call_service", args_snap, allowed=False, result_code="bad_service_data",
                       extra=audit_extra or None)
                return json.dumps({
                    "error": "service_data is not JSON-serialisable",
                    "code": "bad_service_data",
                    "detail": e.__class__.__name__,
                })
            if len(serialized_sd) > _SERVICE_DATA_CAP:
                _audit("ha_call_service", args_snap, allowed=False, result_code="bad_service_data",
                       extra=audit_extra or None)
                return json.dumps({
                    "error": f"service_data JSON-serialised payload exceeds {_SERVICE_DATA_CAP} chars",
                    "code": "bad_service_data",
                })

        if not _RateLimiter.check("ha_call_service", self.valves.max_per_minute):
            _audit("ha_call_service", args_snap, allowed=False, result_code="rate_limited",
                   extra=audit_extra or None)
            return json.dumps({
                "error": "rate limit exceeded",
                "code": "rate_limited",
            })

        try:
            self._init()
        except Exception as e:
            _audit("ha_call_service", args_snap, allowed=False, result_code="init_error",
                   duration_ms=int((time.monotonic() - t0) * 1000),
                   extra=audit_extra or None)
            return json.dumps({
                "error": "runtime initialisation failed",
                "code": "init_error",
                "detail": f"{e.__class__.__name__}: {e}",
            })

        # Build POST body: entity_id always; service_data merged after. The
        # resolved id is what reaches HA — identical to `entity_id` on the
        # id-shaped path, the real id on an alias hit (D-ER-3: same parameter).
        body_payload: dict[str, Any] = {"entity_id": resolved_id}
        if service_data:
            body_payload.update(service_data)

        # Step 7 — POST. UNCHANGED (spec §3.1: ER-1 must not change WHEN or HOW a
        # POST is issued, only what the Tool claims afterwards).
        try:
            url = f"{Tools._base_url}/api/services/{domain}/{service}"
            res = Tools._httpx_client.post(
                url,
                headers={
                    "Authorization": Tools._bearer,
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                json=body_payload,
            )
        except Exception as e:
            _audit("ha_call_service", args_snap, allowed=False, result_code="ha_unreachable",
                   duration_ms=int((time.monotonic() - t0) * 1000),
                   extra=audit_extra or None)
            return json.dumps({
                "error": "could not reach home assistant",
                "code": "ha_unreachable",
                "detail": e.__class__.__name__,
            })

        if res.status_code == 401:
            _audit("ha_call_service", args_snap, allowed=True, result_code="unauthorized",
                   duration_ms=int((time.monotonic() - t0) * 1000),
                   extra=audit_extra or None)
            return json.dumps({
                "error": "home assistant rejected the credentials",
                "code": "unauthorized",
            })

        # HA returns 400 with an entity-not-found body, or sometimes 404,
        # for unknown entities. Both flow into `entity_not_found`; other
        # non-2xx flow into `ha_error`.
        if res.status_code in (400, 404):
            try:
                body_text = res.text or ""
            except Exception:
                body_text = ""
            lower = body_text.lower()
            looks_not_found = (
                res.status_code == 404
                or "not_found" in lower
                or "not found" in lower
                or "unknown entity" in lower
            )
            if looks_not_found:
                _audit("ha_call_service", args_snap, allowed=True, result_code="entity_not_found",
                       duration_ms=int((time.monotonic() - t0) * 1000),
                       extra=audit_extra or None)
                return json.dumps({
                    "entity_id": resolved_id,
                    "code": "entity_not_found",
                    "ha_status": res.status_code,
                })
            _audit("ha_call_service", args_snap, allowed=True, result_code="ha_error",
                   duration_ms=int((time.monotonic() - t0) * 1000),
                   extra=audit_extra or None)
            return json.dumps({
                "error": f"home assistant returned {res.status_code}",
                "code": "ha_error",
                "ha_status": res.status_code,
            })

        if res.status_code >= 300:
            _audit("ha_call_service", args_snap, allowed=True, result_code="ha_error",
                   duration_ms=int((time.monotonic() - t0) * 1000),
                   extra=audit_extra or None)
            return json.dumps({
                "error": f"home assistant returned {res.status_code}",
                "code": "ha_error",
                "ha_status": res.status_code,
            })

        # Parse + possibly truncate the HA response. Per spec §3.1 it is returned
        # verbatim but NO LONGER INTERPRETED: C1 decides success solely by reading
        # the resulting state back, so the empty-changed-list ambiguity (the root
        # of the defect) is never entered and the Tool never reports state_changed.
        try:
            ha_response: Any = res.json()
        except Exception:
            ha_response = []

        try:
            serialized_resp = json.dumps(ha_response, ensure_ascii=False, default=str)
        except Exception:
            serialized_resp = "[]"
        if len(serialized_resp) > _HA_RESPONSE_CAP:
            ha_response = serialized_resp[:_HA_RESPONSE_CAP] + _HA_RESPONSE_TRUNCATION_MARKER

        # ====================================================================
        # Step 8 — ER-1-C1 — mandatory after-only write verification (spec §3.1,
        # D-ER-10). The POST above is UNCHANGED; C1 changes only what the Tool
        # will CLAIM. `ok` + `verified` is returned ONLY when the read-back
        # confirms the D-ER-10 expected state; otherwise the honest
        # `applied_unverified`. HA accepting the POST (2xx) is NOT a success
        # claim on its own — that assumption is the defect ER-1 exists to remove.
        # ====================================================================
        expected_state = _C1_EXPECTED_STATE.get(service)
        verified = False
        state_after = None
        if expected_state is not None:
            # Rule B: check immediately, then poll at 100 ms within a 500 ms
            # budget; success on first match; budget exhausted -> unverified.
            _t_c1 = time.monotonic()
            while True:
                state_after = self._read_state(resolved_id)
                if state_after == expected_state:
                    verified = True
                    break
                if (time.monotonic() - _t_c1) >= _C1_VERIFY_BUDGET_S:
                    break
                time.sleep(_C1_VERIFY_POLL_S)

        if verified:
            result = {
                "ok": True,
                "domain": domain,
                "service": service,
                "entity_id": resolved_id,
                "ha_status": res.status_code,
                "ha_response": ha_response,
                "result_code": "ok",
                "verified": True,
                "state_after": state_after,
            }
            _audit("ha_call_service", args_snap, allowed=True, result_code="ok",
                   duration_ms=int((time.monotonic() - t0) * 1000),
                   extra={**audit_extra, "verified": True, "state_after": state_after})
            return json.dumps(result, ensure_ascii=False)

        # HA accepted the call but the resulting state could NOT be verified —
        # either the service has no D-ER-10 expected state (every non-mapped
        # service, incl. `toggle`) or the read-back did not reach it within the
        # budget. This is explicitly NOT a success claim (spec §4.1); it is the
        # honest replacement for v0.1.0's unverified `ok`.
        result = {
            "ok": False,
            "domain": domain,
            "service": service,
            "entity_id": resolved_id,
            "ha_status": res.status_code,
            "ha_response": ha_response,
            "result_code": "applied_unverified",
            "verified": False,
            "state_after": state_after,
            "message": (
                "Home Assistant accepted the call but the resulting state was "
                "not verified; do not report this as confirmed."
            ),
        }
        _c1_extra = {**audit_extra, "verified": False}
        if expected_state is not None:
            _c1_extra["state_after"] = state_after
        _audit("ha_call_service", args_snap, allowed=True, result_code="applied_unverified",
               duration_ms=int((time.monotonic() - t0) * 1000),
               extra=_c1_extra)
        return json.dumps(result, ensure_ascii=False)
