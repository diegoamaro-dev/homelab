"""
title: Amarolab ha_get_state
author: amarolab
author_url: https://github.com/amaroou
description: Read one Home Assistant entity's current state and a curated, safe subset of its attributes. Call this when the user asks the on/off state or a current value of a specific home device (e.g., "is the awning open?", "is the printer on?", "is the front door closed?"). One entity per call. Pass the everyday name the user actually said — in Spanish or English ("toldo", "impresora 3d", "puerta principal", "awning") — or a canonical entity id if you genuinely know it. Never invent an entity id: if the name is not recognised the Tool answers unknown_entity and lists what does exist. HA writes are out of scope for this Tool — use ha_call_service for those.
version: 0.2.1
license: MIT
requirements:
"""

# @@AMAROLAB_INLINE:audit_helper@@

# @@AMAROLAB_INLINE:entity_resolver@@

import json
import os
import re
import time
from typing import Any

from pydantic import BaseModel, Field


# Phase C contract — locked. The grammar itself is unchanged at v0.2.0;
# its ROLE changed. It was a validity gate: anything not matching was
# rejected `bad_entity_id`. It is now the id-shape test of the ER-1
# resolution ladder (spec §4 step 4) — a match continues to Home
# Assistant exactly as today, and a non-match is a natural name that
# goes to the resolver instead of being rejected.
#
# Entity-id grammar follows Home Assistant's documented form
# `<domain>.<object_id>` with lowercase letters, digits, and
# underscores. Length bound keeps a misbehaving caller from sending
# a 10 MB string straight at HA.
_ENTITY_ID_RE = re.compile(r"^[a-z_]+\.[a-z0-9_]+$")
_ENTITY_ID_MIN_LEN = 3
_ENTITY_ID_MAX_LEN = 128

# Per-attribute JSON-serialized cap. Defends against HA-side
# surprises like a weather entity embedding a multi-day forecast in
# attributes, or a camera entity embedding a base64-encoded snapshot.
# Numbers/strings/booleans below the cap pass through unchanged.
_ATTR_PAYLOAD_CAP = 2048

# Per-call HTTP timeout. HA is on the trusted LAN — 5 s is generous.
_HTTP_TIMEOUT_S = 5.0

# Allowlist of attribute keys that are forwarded to the LLM. Anything
# not in this set is dropped regardless of value type or size — this
# is the **security boundary** against accidentally surfacing:
#   - HA-side secrets (some integrations stash short-lived tokens
#     under names like `access_token`, `authorization`, or in
#     integration-specific attributes),
#   - entity_picture URLs that expose internal endpoints,
#   - arbitrary user-defined attributes that may leak private data,
#   - HA-internal flags (`restored`, `editable`, etc.) that are not
#     useful for the LLM's reasoning.
# Curating the allowlist (rather than denylisting) means new HA
# integrations cannot silently add forwarded attributes; growing this
# set is an explicit Phase C+ design decision, not a passive risk.
_SAFE_ATTRIBUTE_KEYS = frozenset({
    # Universal metadata — present on most entities.
    "icon",
    "unit_of_measurement",
    "device_class",
    "state_class",
    "entity_category",
    "attribution",
    "supported_features",
    "assumed_state",
    "options",

    # Light domain.
    "brightness",
    "color_mode",
    "color_temp",
    "color_temp_kelvin",
    "min_color_temp_kelvin",
    "max_color_temp_kelvin",
    "min_mireds",
    "max_mireds",
    "rgb_color",
    "hs_color",
    "xy_color",
    "supported_color_modes",
    "effect",
    "effect_list",

    # Cover domain.
    "current_position",
    "current_tilt_position",

    # Climate / thermostat / humidifier domain.
    "hvac_mode",
    "hvac_modes",
    "hvac_action",
    "current_temperature",
    "temperature",
    "target_temp_high",
    "target_temp_low",
    "target_temp_step",
    "min_temp",
    "max_temp",
    "preset_mode",
    "preset_modes",
    "fan_mode",
    "fan_modes",
    "swing_mode",
    "swing_modes",
    "current_humidity",
    "humidity",
    "target_humidity",
    "min_humidity",
    "max_humidity",

    # Media-player domain (deliberately excludes entity_picture and
    # media_image_url, which expose internal media URLs).
    "media_title",
    "media_artist",
    "media_album_name",
    "media_content_type",
    "media_duration",
    "media_position",
    "media_position_updated_at",
    "media_channel",
    "media_episode",
    "media_series_title",
    "media_season",
    "media_track",
    "volume_level",
    "volume_muted",
    "is_volume_muted",
    "shuffle",
    "repeat",
    "source",
    "source_list",
    "sound_mode",
    "sound_mode_list",
    "app_name",

    # Fan domain.
    "percentage",
    "percentage_step",
    "oscillating",
    "direction",

    # Vacuum domain.
    "battery_level",
    "battery_icon",
    "battery_state",
    "battery_charging",
    "fan_speed",
    "fan_speed_list",
    "status",
    "cleaned_area",

    # Script + automation — minimal metadata only.
    "last_triggered",
    "current",
    "mode",

    # Input_select / input_number / input_boolean.
    "min",
    "max",
    "step",

    # Sensor / binary_sensor — generic.
    "last_reset",
})


class Tools:
    class Valves(BaseModel):
        max_per_minute: int = Field(
            default=60, ge=1, le=600,
            description="Per-process per-Tool rate limit (resets on openwebui restart). Higher than rag_search because HA reads are cheap — a single HTTP GET, no model load.",
        )

    # Lazy runtime state. Class-level so a single httpx.Client +
    # bearer string survive between Tools() instantiations inside the
    # same openwebui process. HA_LLAT is read from os.environ exactly
    # once per process (inside _init()); it never appears in args
    # passed to _audit, never in the returned JSON, never logged.
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

    def ha_get_state(self, entity_id: str) -> str:
        """
        Read one Home Assistant entity's current state and a curated, safe subset of its attributes. Call this whenever the user asks the on/off state or a current value of a specific home device (e.g., "is the awning open?", "is the printer on?", "is the front door closed?", "how is the plant doing?"). For multi-entity queries, call this once per entity. HA writes are out of scope; if the user asks you to change an HA state, that belongs to ha_call_service.

        :param entity_id: The device the user means. Pass the everyday name they actually used, in Spanish or English — "toldo", "impresora 3d", "puerta principal", "awning", "front door" — and this Tool resolves it to the real entity id. A canonical id ("switch.impresora_3d") is also accepted and is passed straight through. NEVER invent an entity id: guessing an English-looking id for a device named in Spanish is the known failure mode. If the name is not recognised you get code "unknown_entity" plus a "candidates" list of every device that does exist — answer from that list rather than guessing again. 3-128 characters.
        :return: JSON string with keys entity_id, state, friendly_name, last_changed, last_updated, attributes (safe subset only), result_code. On a resolver miss: {"code": "unknown_entity", "candidates": [...]} and no HA call is made. On error or missing entity: {"error": "...", "code": "..."} or {"entity_id": "...", "code": "not_found"}.
        """
        t0 = time.monotonic()
        args_snap = {"entity_id": entity_id}

        # Step 3 — bounded/type check. UNCHANGED from v0.1.0 (spec §4):
        # it precedes resolution, so it still fires first and still
        # answers `bad_entity_id`. The Literal annotation in
        # ha_call_service (Phase C C-2) protects the domain enum at
        # spec-build time; ha_get_state has no enum-like input, so this
        # bound is the only schema we enforce here. It also keeps a
        # misbehaving caller from sending a 10 MB string at the
        # normalizer. Bearer never touches args.
        if not isinstance(entity_id, str) or len(entity_id) < _ENTITY_ID_MIN_LEN or len(entity_id) > _ENTITY_ID_MAX_LEN:
            _audit("ha_get_state", args_snap, allowed=False, result_code="bad_entity_id")
            return json.dumps({
                "error": f"entity_id must be {_ENTITY_ID_MIN_LEN}-{_ENTITY_ID_MAX_LEN} characters",
                "code": "bad_entity_id",
            })

        # Steps 4-6 — resolution (ER-1.4a). Slotted exactly where the
        # old id-shape rejection sat, so every preceding check is
        # untouched and the rate limiter still sees precisely the
        # inputs it saw before: one that never reaches HA never reached
        # the limiter at v0.1.0 either.
        #
        # `ha_get_state` runs the identical ladder to `ha_call_service`
        # minus ER-1-C1 (spec §4): reads need no write verification
        # because HA already answers 404 -> `not_found` honestly.
        audit_extra = {}
        if _ENTITY_ID_RE.match(entity_id):
            # Step 4 — id-shaped: continue to Home Assistant EXACTLY as
            # today, whether or not the registry knows it (D-ER-9). The
            # registry is consulted for OBSERVABILITY ONLY and never to
            # gate: `registry_target` (D-ER-14) goes to the audit line
            # and changes nothing about the request. `is_target` answers
            # None when the resolver is unavailable, and the key is then
            # omitted rather than recorded as false — claiming "not a
            # registry target" when the registry could not be read would
            # be exactly the unverified claim ER-1 exists to remove.
            resolved_id = entity_id
            registry_target = _EntityResolver.is_target(entity_id)
            if registry_target is not None:
                audit_extra["registry_target"] = registry_target
        else:
            # Step 5 — not id-shaped: a natural name. Normalize (D-ER-8)
            # + closed lookup. No fuzzy matching, no scoring, no LLM.
            if not _EntityResolver.available():
                _audit("ha_get_state", args_snap, allowed=False,
                       result_code="resolver_unavailable",
                       duration_ms=int((time.monotonic() - t0) * 1000))
                return json.dumps({
                    "error": "entity name resolution is unavailable; pass a canonical entity id",
                    "code": "resolver_unavailable",
                    "detail": _EntityResolver.reason(),
                })
            resolved_id = _EntityResolver.lookup(entity_id)
            if resolved_id is None:
                # Step 6 — miss: fail closed with ZERO HTTP calls. There
                # is no valid id to send, so nothing *can* pass through.
                # The candidate list is the corrective feedback that
                # replaces guessing (root cause #3).
                _audit("ha_get_state", args_snap, allowed=False,
                       result_code="unknown_entity",
                       duration_ms=int((time.monotonic() - t0) * 1000))
                return json.dumps({
                    "entity_id": entity_id,
                    "error": f"'{entity_id}' is not an entity I model",
                    "code": "unknown_entity",
                    "candidates": _EntityResolver.candidates(),
                }, ensure_ascii=False)
            # An alias hit is a target by construction. `resolved_to`
            # keeps the audit line honest: without it `args.entity_id`
            # says "toldo" and no reader could tell what was actually
            # read (the §1.2 indistinguishability defect).
            audit_extra["registry_target"] = True
            audit_extra["resolved_to"] = resolved_id

        if not _RateLimiter.check("ha_get_state", self.valves.max_per_minute):
            _audit("ha_get_state", args_snap, allowed=False, result_code="rate_limited",
                   extra=audit_extra or None)
            return json.dumps({
                "error": "rate limit exceeded",
                "code": "rate_limited",
            })

        try:
            self._init()
        except Exception as e:
            _audit("ha_get_state", args_snap, allowed=False, result_code="init_error",
                   duration_ms=int((time.monotonic() - t0) * 1000),
                   extra=audit_extra or None)
            return json.dumps({
                "error": "runtime initialisation failed",
                "code": "init_error",
                "detail": f"{e.__class__.__name__}: {e}",
            })

        try:
            url = f"{Tools._base_url}/api/states/{resolved_id}"
            res = Tools._httpx_client.get(
                url,
                headers={
                    "Authorization": Tools._bearer,
                    "Accept": "application/json",
                },
            )
        except Exception as e:
            # Catches httpx.ConnectError / .ReadTimeout / .NetworkError
            # / DNS failures. The exception class name is recorded in
            # the audit log; the bearer is NOT in args, so it is not
            # logged here either.
            _audit("ha_get_state", args_snap, allowed=False, result_code="ha_unreachable",
                   duration_ms=int((time.monotonic() - t0) * 1000),
                   extra=audit_extra or None)
            return json.dumps({
                "error": "could not reach home assistant",
                "code": "ha_unreachable",
                "detail": e.__class__.__name__,
            })

        if res.status_code == 401:
            # HA rejected the credentials. `allowed: true` because
            # the assistant did decide the call was within scope and
            # made it; the auth answer was at the HA side. If this
            # ever fires, rotate HA_LLAT per the security checklist.
            _audit("ha_get_state", args_snap, allowed=True, result_code="unauthorized",
                   duration_ms=int((time.monotonic() - t0) * 1000),
                   extra=audit_extra or None)
            return json.dumps({
                "error": "home assistant rejected the credentials",
                "code": "unauthorized",
            })
        if res.status_code == 404:
            _audit("ha_get_state", args_snap, allowed=True, result_code="not_found",
                   duration_ms=int((time.monotonic() - t0) * 1000),
                   extra=audit_extra or None)
            return json.dumps({
                "entity_id": resolved_id,
                "code": "not_found",
            })
        if res.status_code >= 300:
            _audit("ha_get_state", args_snap, allowed=True, result_code="ha_error",
                   duration_ms=int((time.monotonic() - t0) * 1000),
                   extra=audit_extra or None)
            return json.dumps({
                "error": f"home assistant returned {res.status_code}",
                "code": "ha_error",
                "ha_status": res.status_code,
            })

        try:
            body = res.json()
        except Exception as e:
            _audit("ha_get_state", args_snap, allowed=True, result_code="ha_error",
                   duration_ms=int((time.monotonic() - t0) * 1000),
                   extra=audit_extra or None)
            return json.dumps({
                "error": "home assistant returned malformed JSON",
                "code": "ha_error",
                "detail": e.__class__.__name__,
            })

        # Curate the attributes payload through the allowlist + cap.
        # friendly_name is surfaced at top level (per the C-1
        # contract); the rest of the allowed attributes are nested.
        raw_attrs = body.get("attributes") or {}
        if not isinstance(raw_attrs, dict):
            raw_attrs = {}

        friendly_name = raw_attrs.get("friendly_name")
        if friendly_name is not None and not isinstance(friendly_name, str):
            friendly_name = str(friendly_name)

        safe_attrs: dict[str, Any] = {}
        for k, v in raw_attrs.items():
            if k == "friendly_name":
                continue  # surfaced at top level
            if k not in _SAFE_ATTRIBUTE_KEYS:
                continue
            try:
                serialized = json.dumps(v, ensure_ascii=False, default=str)
            except Exception:
                continue
            if len(serialized) > _ATTR_PAYLOAD_CAP:
                continue
            safe_attrs[k] = v

        result = {
            "entity_id": body.get("entity_id", resolved_id),
            "state": body.get("state"),
            "friendly_name": friendly_name,
            "last_changed": body.get("last_changed"),
            "last_updated": body.get("last_updated"),
            "attributes": safe_attrs,
            "result_code": "ok",
        }
        _audit("ha_get_state", args_snap, result_code="ok",
               duration_ms=int((time.monotonic() - t0) * 1000),
               extra=audit_extra or None)
        return json.dumps(result, ensure_ascii=False)
