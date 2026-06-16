"""
title: Amarolab ha_call_service
author: amarolab
author_url: https://github.com/amaroou
description: Call one Home Assistant service against a single entity. Allowed domains (closed set, D-12): light, switch, scene, cover, climate, media_player, script, automation, fan, vacuum, input_boolean, input_select, input_number. Anything outside the allowlist is refused before any HTTP request reaches Home Assistant. For reads ("is X on?") use ha_get_state instead.
version: 0.1.0
license: MIT
requirements:
"""

# @@AMAROLAB_INLINE:audit_helper@@

import json
import os
import re
import time
from typing import Any, Literal

from pydantic import BaseModel, Field


# Phase C contract — locked.
# Entity-id grammar mirrors ha_get_state. HA's documented form is
# `<domain>.<object_id>` lowercase + digits + underscores.
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
        Call one Home Assistant service against a single entity. Use to perform an action: turn a light on/off, set thermostat target temperature, play media on a speaker, activate a scene, toggle a user-defined automation. Allowed domains: light, switch, scene, cover, climate, media_player, script, automation, fan, vacuum, input_boolean, input_select, input_number. Anything else is refused before any HTTP request leaves the assistant; do not retry an action under a different allowed domain. For reads (state queries like "is X on?") use ha_get_state instead.

        :param domain: HA service domain. Must be one of the allowed values above; out-of-allowlist domains are refused.
        :param service: HA service name in lowercase snake_case (e.g. "turn_on", "set_temperature", "play_media", "toggle"). 1-64 characters; matches `^[a-z_][a-z0-9_]*$`.
        :param entity_id: HA entity id in lowercase domain.object_id form (e.g. "light.kitchen", "climate.lounge"). 3-128 characters; matches `^[a-z_]+\\.[a-z0-9_]+$`.
        :param service_data: Optional extra data forwarded to HA as POST-body keys (e.g. {"brightness_pct": 60} for light.turn_on, {"hvac_mode": "heat"} for climate.set_hvac_mode). Must be a dict or null; must NOT contain a top-level "entity_id" key (the entity_id parameter owns that); JSON-serialised payload ≤ 4 KB.
        :return: JSON string. Success: {ok, domain, service, entity_id, ha_status, ha_response, result_code: "ok"}. Refusal: {allowed: false, domain, service, code: "refused", message}. Error: {error, code, ...}. ha_response truncated to 8 KB if HA returns a very large response.
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

        # Input validation — entity_id (same shape as ha_get_state).
        if (not isinstance(entity_id, str)
                or len(entity_id) < _ENTITY_ID_MIN_LEN
                or len(entity_id) > _ENTITY_ID_MAX_LEN):
            _audit("ha_call_service", args_snap, allowed=False, result_code="bad_entity_id")
            return json.dumps({
                "error": f"entity_id must be {_ENTITY_ID_MIN_LEN}-{_ENTITY_ID_MAX_LEN} characters",
                "code": "bad_entity_id",
            })
        if not _ENTITY_ID_RE.match(entity_id):
            _audit("ha_call_service", args_snap, allowed=False, result_code="bad_entity_id")
            return json.dumps({
                "error": "entity_id must match <domain>.<object_id> lowercase grammar",
                "code": "bad_entity_id",
            })

        # Input validation — service_data.
        if service_data is not None:
            if not isinstance(service_data, dict):
                _audit("ha_call_service", args_snap, allowed=False, result_code="bad_service_data")
                return json.dumps({
                    "error": "service_data must be a dict or null",
                    "code": "bad_service_data",
                })
            if "entity_id" in service_data:
                _audit("ha_call_service", args_snap, allowed=False, result_code="bad_service_data")
                return json.dumps({
                    "error": "service_data must not contain a top-level entity_id key (the entity_id parameter owns that)",
                    "code": "bad_service_data",
                })
            try:
                serialized_sd = json.dumps(service_data, ensure_ascii=False, default=str)
            except Exception as e:
                _audit("ha_call_service", args_snap, allowed=False, result_code="bad_service_data")
                return json.dumps({
                    "error": "service_data is not JSON-serialisable",
                    "code": "bad_service_data",
                    "detail": e.__class__.__name__,
                })
            if len(serialized_sd) > _SERVICE_DATA_CAP:
                _audit("ha_call_service", args_snap, allowed=False, result_code="bad_service_data")
                return json.dumps({
                    "error": f"service_data JSON-serialised payload exceeds {_SERVICE_DATA_CAP} chars",
                    "code": "bad_service_data",
                })

        if not _RateLimiter.check("ha_call_service", self.valves.max_per_minute):
            _audit("ha_call_service", args_snap, allowed=False, result_code="rate_limited")
            return json.dumps({
                "error": "rate limit exceeded",
                "code": "rate_limited",
            })

        try:
            self._init()
        except Exception as e:
            _audit("ha_call_service", args_snap, allowed=False, result_code="init_error",
                   duration_ms=int((time.monotonic() - t0) * 1000))
            return json.dumps({
                "error": "runtime initialisation failed",
                "code": "init_error",
                "detail": f"{e.__class__.__name__}: {e}",
            })

        # Build POST body: entity_id always; service_data merged after.
        body_payload: dict[str, Any] = {"entity_id": entity_id}
        if service_data:
            body_payload.update(service_data)

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
                   duration_ms=int((time.monotonic() - t0) * 1000))
            return json.dumps({
                "error": "could not reach home assistant",
                "code": "ha_unreachable",
                "detail": e.__class__.__name__,
            })

        if res.status_code == 401:
            _audit("ha_call_service", args_snap, allowed=True, result_code="unauthorized",
                   duration_ms=int((time.monotonic() - t0) * 1000))
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
                       duration_ms=int((time.monotonic() - t0) * 1000))
                return json.dumps({
                    "entity_id": entity_id,
                    "code": "entity_not_found",
                    "ha_status": res.status_code,
                })
            _audit("ha_call_service", args_snap, allowed=True, result_code="ha_error",
                   duration_ms=int((time.monotonic() - t0) * 1000))
            return json.dumps({
                "error": f"home assistant returned {res.status_code}",
                "code": "ha_error",
                "ha_status": res.status_code,
            })

        if res.status_code >= 300:
            _audit("ha_call_service", args_snap, allowed=True, result_code="ha_error",
                   duration_ms=int((time.monotonic() - t0) * 1000))
            return json.dumps({
                "error": f"home assistant returned {res.status_code}",
                "code": "ha_error",
                "ha_status": res.status_code,
            })

        # Parse + possibly truncate the HA response.
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

        result = {
            "ok": True,
            "domain": domain,
            "service": service,
            "entity_id": entity_id,
            "ha_status": res.status_code,
            "ha_response": ha_response,
            "result_code": "ok",
        }
        _audit("ha_call_service", args_snap, allowed=True, result_code="ok",
               duration_ms=int((time.monotonic() - t0) * 1000))
        return json.dumps(result, ensure_ascii=False)
