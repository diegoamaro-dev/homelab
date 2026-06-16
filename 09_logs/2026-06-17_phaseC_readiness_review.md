# Phase C — readiness review — Amarolab Assistant v1

- **Date:** 2026-06-17
- **Status:** **Phase C is NOT YET STARTED.** This log is a paper
  exercise: design + readiness + risk register only. No Tool
  authored, no `webui.db` change, no container recreate, no
  Home Assistant call (read or write), no `.env` change.
- **Scope:** Verify that blocker B-07 is closed (HA user
  `assistant` + LLAT issued, `.env` populated), surface the
  one new readiness gap discovered during this review (the
  openwebui container does **not** currently expose `HA_*` env
  vars to its Python runtime), lock the designs for
  `ha_get_state` and `ha_call_service`, the 12-domain
  allowlist (D-12), the refusal strategy, the validation
  matrix, and the rollback plan. Counterpart, one phase
  earlier, to
  [`2026-06-16_phaseB_execution_readiness_review.md`](2026-06-16_phaseB_execution_readiness_review.md).
- **Inputs consumed:**
  - [`2026-06-16_phaseB_closeout.md`](2026-06-16_phaseB_closeout.md)
    §6 (the Phase C entrypoint definition).
  - [`../04_ai_system/amarolab-v1/04-security-and-permissions.md`](../04_ai_system/amarolab-v1/04-security-and-permissions.md)
    (trust model, secrets table, threat model T1/T6, per-tool
    rate-limit table, security checklist).
  - [`../04_ai_system/amarolab-v1/03-tools.md`](../04_ai_system/amarolab-v1/03-tools.md)
    §"Tool 3" and §"Tool 4" (the historical catalog — amended
    banner applies: `class Tools` + install-via-API per D-24 /
    D-25, not the module-level pseudocode).
  - [`../FUNCTIONS_COMPATIBILITY_REPORT.md`](../FUNCTIONS_COMPATIBILITY_REPORT.md)
    (OWUI 0.8.10 runtime contract).
  - [`../04_ai_system/amarolab-v1/ROADMAP.md`](../04_ai_system/amarolab-v1/ROADMAP.md)
    §"Decisions taken" — D-01 through D-35.
  - [`2026-06-17_phaseB_rag_search_design.md`](2026-06-17_phaseB_rag_search_design.md)
    (pattern source: `class Tools`, lazy `_init`, inline audit
    helper, eight `result_code`s).
  - Canonical helper source at
    `/home/diego/homelab/ai-stack/openwebui-tools/lib/audit_helper.py`
    (the `# --- INLINE START ---` block re-used by every Tool).
  - Live state inputs (read-only): `/home/diego/homelab/ai-stack/.env`,
    `docker inspect openwebui`, `docker exec openwebui env`,
    `webui.db.tool` row inventory.
- **What this log is NOT:**
  - An application log. Nothing is written outside `09_logs/`.
  - A design for the v1.1 `area=` / `domain=` filter on
    `ha_get_state` (left out per Phase B closeout §6.3 — v1
    is single-entity reads only).
  - Approval to recreate the openwebui container. The
    container-env-passthrough remediation in §1.3 below is a
    **proposal** that requires user approval and a new Gate
    (provisionally **G-Cpre**) before C-1 can be authored.

## 0. TL;DR

B-07 — the user-owned blocker — **is closed**. The dedicated HA
user `assistant` and its Long-Lived Access Token have been
issued, the token is in
`/home/diego/homelab/ai-stack/.env` alongside the existing
Qdrant / WebUI secrets, and the file's mode and ownership are
exactly what the security model requires (0600 `diego:diego`).
The token has the structure expected of a HA LLAT (JWT-shaped,
three base64url segments separated by dots, no whitespace,
length in the 183-character range typical of HA tokens).

**One new readiness item surfaced during this review.** The
openwebui container, as currently running (`openwebui`,
healthy, started 2026-06-16T09:55:35Z from the Phase B B-3
recreate), does **not** expose `HA_BASE_URL` or `HA_LLAT` to
its Python runtime. The container was created with the Phase
B environment set (`QDRANT_URI`, `QDRANT_API_KEY`,
`WEBUI_SECRET_KEY`, `AMAROLAB_AUDIT_LOG`, `OLLAMA_BASE_URL`,
`HF_HOME`) but predates the LLAT issuance, so the new keys
were not in the `-e` set at `docker run` time. This is
**identical in shape** to the B-3 work that added the
`/opt/ingest:ro` bind mount: a container recreate, with a
rollback target preserved, gated by the user. We label this
**C-pre / Gate G-Cpre** in §6 / §8.

No HA Tool can authenticate against the HA API until C-pre is
applied — `os.environ["HA_LLAT"]` would raise `KeyError` at
the Tool's lazy-init step. The Tool source files (`C-1`,
`C-2`) can still be authored before C-pre, because Open WebUI
0.8.10 builds the JSON spec at module load and only invokes
the heavy code paths on first call; but they cannot be
exercised end-to-end (W-6 / G-5) until the container can see
`HA_*`.

The rest of the Phase C surface — designs for `ha_get_state`
and `ha_call_service`, the 12-domain `Literal` allowlist,
the dual-layer refusal grammar, the validation matrix, and
the rollback plan — is set out in §3 through §9 below. None
of it is in conflict with anything already locked
(D-01 … D-35); one new design rule is proposed (a
result_code lexicon dedicated to the HA tools, mirroring
the rag_search shape).

## 1. B-07 closure — evidence

### 1.1 `.env` state (values redacted; shape recorded)

```
$ stat -c 'mode=%a owner=%U:%G size=%s' /home/diego/homelab/ai-stack/.env
mode=600 owner=diego:diego size=627

$ awk -F= '/^[A-Z_][A-Z0-9_]*=/{print $1}' /home/diego/homelab/ai-stack/.env | sort -u
HA_BASE_URL
HA_LLAT
QDRANT_API_KEY
QDRANT__SERVICE__API_KEY
WEBUI_SECRET_KEY
```

| Key | Value (redacted) | Verified shape |
|---|---|---|
| `HA_BASE_URL` | `<redacted; http://<host>:<port>>` | scheme = `http://`; host = 14-char IPv4 literal (LAN-private space, matches HA install pattern); port present; total length 26 chars; DNS lookup succeeds locally |
| `HA_LLAT` | `<redacted>` | length 183 chars; matches `^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$` (JWS compact serialization expected for HA LLATs); no whitespace; no obvious paste artefacts |
| `QDRANT_API_KEY` / `QDRANT__SERVICE__API_KEY` / `WEBUI_SECRET_KEY` | unchanged | Phase A / Phase B values; not touched by B-07 closure |

The `HA_BASE_URL` is **not** an HTTPS URL — Phase C's HA target
is on the trusted LAN (192.168.178.0/24), reached over plaintext
HTTP. This is consistent with D-15 (no public exposure of the
assistant in v1, LAN/tailnet only) and with how Home Assistant
ships by default (HTTPS termination is a deliberate add-on the
user has not configured). T4 (network attacker on LAN reaches
Ollama/OWUI/HA unauthenticated) applies and is **accepted** for
v1 per the security model.

Per the security checklist in
[`04-security-and-permissions.md`](../04_ai_system/amarolab-v1/04-security-and-permissions.md)
§"Security checklist before declaring v1 live":

- `[x]` `WEBUI_SECRET_KEY`, `QDRANT_API_KEY`, `HA_LLAT` all
  present in `/home/diego/homelab/ai-stack/.env` with `0600`
  ownership `diego:diego`. ← **met**
- `[ ]` `HA_LLAT` belongs to a **dedicated HA user
  `assistant`**, not diego's primary HA account. ← **claimed
  met by user**; assistant cannot independently verify (would
  require a HA `/api/auth/current_user` call, which is out of
  scope for this paper review).
- `[ ]` HA *exposed-to-assist* entity set reviewed; nothing
  surprising. ← **carried into C-pre §6.5** (one-shot review
  step the user does in the HA UI before C-6).

### 1.2 Token leakage audit

- The .env value is bytes on disk; never printed by the probes
  in §1.1 (`awk` patterns extract key names only;
  length-and-shape probes operate on the value but emit only
  `len=`, `scheme=`, `looks_jwt=` derived facts).
- Bash history check: this turn's probes use `awk`/`stat`
  forms that do not capture the value into `$_` or
  `$HISTFILE`. The closeout-doc rotation procedure (§"Rotation
  procedure" in
  [`04-security-and-permissions.md`](../04_ai_system/amarolab-v1/04-security-and-permissions.md))
  remains the canonical recovery path if a leak is later
  suspected.
- `_amarolab_redact` (the inline-helper canonical source at
  `openwebui-tools/lib/audit_helper.py`, `# --- INLINE START
  ---` block) masks any audit-log argument whose key matches
  `password|token|secret|api_key|authorization` (case
  insensitive). The HA Tools must never put the LLAT into
  `args` at all — the LLAT lives in `os.environ` and is read
  inside `_init()` only. §4.6 / §5.6 enforce this in the
  design.

### 1.3 Container env passthrough — gap

```
$ docker exec openwebui env | awk -F= '/^HA_/{v=$0; sub(/^[^=]+=/,"",v); print $1" len="length(v)}'
(no output)

$ docker exec openwebui env | awk -F= '{print $1}' | sort -u | grep -E '^(WEBUI|OLLAMA|QDRANT|HA_|AMAROLAB)'
AMAROLAB_AUDIT_LOG
OLLAMA_BASE_URL
QDRANT_API_KEY
QDRANT_URI
WEBUI_API_KEYS_ENABLED
WEBUI_BUILD_VERSION
WEBUI_SECRET_KEY
```

`HA_BASE_URL` and `HA_LLAT` are present in `.env` (§1.1) but
**not** in the running container's environment. The B-3
recreate (2026-06-15T23:52:15Z; closeout §2.4) set the env
that existed at that time; the LLAT was issued later, and the
container has not been recreated since.

Symptomatic consequence: an HA Tool's `_init()` step

```python
base = os.environ["HA_BASE_URL"]
tok  = os.environ["HA_LLAT"]
```

would raise `KeyError` on the running container today. With
the `.env.example` pattern of `os.environ.get(..., "")`
fallbacks, the Tool would instead silently get empty strings
and `httpx` would either fail at URL parsing (`init_error`)
or hit `127.0.0.1` (`ha_unreachable`). Neither path leaks the
LLAT, but neither path works either.

**Remediation owner:** user, gated. Recreate the openwebui
container with `-e HA_BASE_URL=...` and `-e HA_LLAT=...` in
addition to the existing Phase B `-e` set; preserve the
current container as `openwebui_pre_phaseC_<UTC-TIMESTAMP>`
(stopped) as the rollback target, exactly as B-3 did with
`openwebui_pre_phaseB_20260615235209`. Detail in §6.

**Why we cannot dodge this:** Open WebUI's Tool runtime is
`os.environ`-based; there is no `webui.db.config`-side place
to inject secrets that the Tool would read. The container's
process env is the supported boundary. Editing `.env` while
the container runs does nothing — Docker copies env at
`docker run` time only.

## 2. Permission assumptions

These are the assumptions the Phase C designs make about HA
side. The user owns the HA-UI verification; the assistant
will not call HA to verify any of them.

| # | Assumption | Source | Verification (user, in HA UI) |
|---|---|---|---|
| **P-1** | The HA user `assistant` exists, distinct from `diego`'s primary HA account | closeout §6.1.1; D-12 rationale | HA → Settings → People → list contains "Assistant" |
| **P-2** | `assistant` has the **smallest role HA permits** above pure no-op. HA does not need admin to call `light.turn_on`/`switch.toggle`; standard user is enough | closeout §6.1.1 | HA → People → Assistant → role chip is not "Administrator" |
| **P-3** | The LLAT in `.env` was issued under the `assistant` user, not under another account | T6 mitigation in [`04-security-and-permissions.md`](../04_ai_system/amarolab-v1/04-security-and-permissions.md) | HA → Profile (logged in as `assistant`) → Long-Lived Access Tokens → exactly one active token, issued in the past 48 h, name matches what the user typed |
| **P-4** | The HA *exposed-to-Assist* entity set has been reviewed; nothing surprising (no front-door lock as `light.front_door`, no `switch.boiler_relay`, etc.) | security-checklist line | HA → Settings → Voice assistants → Expose → audit list. Carry into C-pre §6.5 as a one-time step |
| **P-5** | HA's `/api/services/<domain>/<service>` access for `assistant` matches the 12-domain D-12 allowlist or is **at least** that broad (HA may also expose domains the assistant deliberately won't use) | D-12 + HA default RBAC | implicit — HA's default for a standard user satisfies this; verified end-to-end by the C-6 happy-path test |
| **P-6** | HA returns 401 for invalid tokens and 404 for unknown entities. Standard REST API contract per HA docs (`https://developers.home-assistant.io/docs/api/rest/`) | HA REST API documentation, well-known | implicit; the Tools handle both |
| **P-7** | HA's REST API is reachable over the LAN from the `proxy_default` Docker bridge that `openwebui` is on, without further firewalling | network topology; no Docker port published rule for HA | tested implicitly by the first end-to-end call. The `proxy_default` bridge talks to the host's LAN by default; if HA is itself in a `network_mode: host` container, the host IP literal in `HA_BASE_URL` resolves it without trouble |
| **P-8** | `assistant` is not in any HA "Admin" group; therefore calls to `homeassistant.restart`, `hassio.*`, `backup.*`, `auth.*` would **also** fail server-side with 403/404 even without our allowlist | HA RBAC model | not directly tested in v1 (would require deliberately tripping the allowlist server-side, which our local refusal blocks first) |

**Failure mode if any P-x is wrong:** the refusal path in §6
still holds because allowlisting happens at the Tool layer
(before HTTP). The most likely real-world failure is P-7
(network routing) — surfaces as `result_code: ha_unreachable`
on the first call, easy to diagnose, no security
consequence.

## 3. `ha_get_state` — design

### 3.1 Purpose

One read of one HA entity. The simplest possible Tool that
the model can route to when the user asks "is the kitchen
light on?", "what's the lounge temperature?", "is the front
door open?". No aggregation, no listing, no area/domain
filtering in v1 (closeout §6.3 spec).

### 3.2 Inputs

| Field | Type | Constraint | Why |
|---|---|---|---|
| `entity_id` | `str` | `^[a-z_]+\.[a-z0-9_]+$`; 3 ≤ len ≤ 128 | Matches HA's documented entity-id grammar (`domain.object_id`, lowercase + digits + `_`). Bounded length keeps a misbehaving LLM from sending a 10 MB string |

No keyword args, no defaults — single required positional.
Aligns with closeout §6.3 wording. The historical 03-tools.md
optional `area` / `domain` filters are **deferred** to v1.1;
rationale in §3.7.

### 3.3 Output (success)

```json
{
  "entity_id": "light.kitchen",
  "state": "on",
  "attributes": {
    "brightness": 255,
    "color_temp": 366,
    "friendly_name": "Kitchen Light",
    "supported_features": 63
  },
  "last_changed": "2026-06-17T18:23:11.234567+00:00",
  "last_updated": "2026-06-17T18:23:11.234567+00:00",
  "result_code": "ok"
}
```

Return value is a JSON-encoded string (matches Phase B
`rag_search` / `audit_search` shape — OWUI 0.8.10 stringifies
dicts for the LLM regardless, returning a string up front
keeps the dump deterministic and easy to test).

`attributes` is passed through verbatim from HA. Cap: drop
any attribute whose serialized JSON length exceeds 2 KB
(typical attributes are < 256 bytes; the cap defends against
HA-side surprises like a 1 MB camera snapshot inline in
`attributes`).

### 3.4 Output (error)

| `result_code` | Trigger | What we return |
|---|---|---|
| `bad_entity_id` | regex/length fail | `{"error": "...", "code": "bad_entity_id"}` |
| `rate_limited` | RateLimiter rejects | `{"error": "rate limit exceeded", "code": "rate_limited"}` |
| `init_error` | `HA_BASE_URL` or `HA_LLAT` not in env | `{"error": "runtime initialisation failed", "code": "init_error", "detail": "<ExceptionClass>: <msg>"}` |
| `ha_unreachable` | TCP/DNS/timeout failure | `{"error": "could not reach home assistant", "code": "ha_unreachable", "detail": "<ExceptionClass>"}` |
| `unauthorized` | HA returns 401 | `{"error": "home assistant rejected the credentials", "code": "unauthorized"}` |
| `not_found` | HA returns 404 | `{"entity_id": "<id>", "code": "not_found"}` |
| `ha_error` | HA returns any other non-2xx | `{"error": "home assistant returned <status>", "code": "ha_error", "ha_status": <int>}` |

All seven plus `ok` = 8 codes, parity with `rag_search`.

### 3.5 Code shape (sketch — not authored)

```python
"""
title: Amarolab ha_get_state
author: amarolab
description: Read one Home Assistant entity's current state and attributes.
"""

# @@AMAROLAB_INLINE:audit_helper@@

import json
import os
import re
import time

from pydantic import BaseModel, Field

_ENTITY_ID_RE = re.compile(r"^[a-z_]+\.[a-z0-9_]+$")
_ENTITY_ID_MIN_LEN = 3
_ENTITY_ID_MAX_LEN = 128
_ATTR_PAYLOAD_CAP = 2048   # per-attribute JSON serialized cap, chars
_HTTP_TIMEOUT_S = 5.0


class Tools:
    class Valves(BaseModel):
        max_per_minute: int = Field(
            default=60, ge=1, le=600,
            description=("Per-process per-Tool rate limit "
                         "(resets on openwebui restart)."),
        )

    _httpx = None
    _base_url = None
    _bearer = None

    def __init__(self) -> None:
        self.valves = self.Valves()
        self.citation = False

    def _init(self) -> None:
        if Tools._httpx is None:
            import httpx
            base = os.environ.get("HA_BASE_URL")
            tok = os.environ.get("HA_LLAT")
            if not base:
                raise RuntimeError(
                    "HA_BASE_URL not set in container env "
                    "(see Phase C readiness review §1.3)"
                )
            if not tok:
                raise RuntimeError(
                    "HA_LLAT not set in container env "
                    "(see Phase C readiness review §1.3)"
                )
            Tools._base_url = base.rstrip("/")
            Tools._bearer = f"Bearer {tok}"
            Tools._httpx = httpx.Client(timeout=_HTTP_TIMEOUT_S)

    def ha_get_state(self, entity_id: str) -> str:
        """
        Read one Home Assistant entity's current state. Use when the
        user asks the value or on/off state of a specific HA entity
        (e.g., "is the kitchen light on?", "what's the lounge
        temperature?"). For multi-entity queries, call this once per
        entity id. Do not pass area names or domain names — those
        are not supported in v1.

        :param entity_id: HA entity id, lower-case, "<domain>.<object>",
            3-128 chars (e.g. "light.kitchen", "sensor.lounge_temp").
        :return: JSON string with entity_id, state, attributes,
            last_changed, last_updated, result_code; or
            {"error": "...", "code": "..."} on failure.
        """
        # ... validation + rate-limit + _init + GET, see §3.4 codes ...
```

(Full source belongs in C-1, not this readiness review. The
sketch above exists only to (a) name the constants and (b)
prove the shape matches D-24 / D-26.)

### 3.6 Routing rule (system-prompt addendum)

Current v0.1 prompt's `# Tools` block names `time_now`,
`rag_search`, `system_status`. After C-4, the prompt must
gain (or v0.2 must include) routing copy roughly:

```
ha_get_state(entity_id) — read one Home Assistant entity's
  current state. Use for "is X on?", "what's the temperature
  in Y?". Pass the entity id literally; the tool will not
  resolve area names or domain names.

ha_call_service(domain, service, entity_id, service_data) —
  perform an HA action. Allowed domains: light, switch, scene,
  cover, climate, media_player, script, automation, fan,
  vacuum, input_boolean, input_select, input_number. Anything
  else is refused; do not retry.
```

The v0.2 prompt iteration (closeout §4.2) is the natural
landing point. C-7 documents this as a follow-up; the v0.1
prompt's D-30 refusal block is already adequate to cover
"please call recorder.purge" without an `ha_call_service`
mention.

### 3.7 Deferred from v1

- **`area=` / `domain=` filters** (03-tools.md catalog spec)
  — deferred. Reason: requires walking the HA area registry
  (`GET /api/config/areas`, `GET /api/config/devices`) which
  triples the surface area. v1 single-entity-only is enough
  for the six acceptance questions in
  [`README.md`](../04_ai_system/amarolab-v1/README.md).
- **List-all-entities** — deferred. Returns hundreds of
  entities → blows out qwen2.5's context budget. If the user
  ever needs it, add `ha_list_entities(domain)` in v1.1 with
  a `limit` of 50.
- **Subscribe to state changes** — out of scope (would require
  websocket, not REST).

## 4. `ha_call_service` — design

### 4.1 Purpose

One bounded write to HA. The single most security-sensitive
Tool in v1 — the only one that mutates external state. The
design pays for that with: a `Literal`-typed domain enum,
a runtime allowlist re-check, a polite refusal path that
never issues HTTP, a stricter rate limit (10/min vs 60/min
for reads), and full audit-log capture of every refused call.

### 4.2 Inputs

| Field | Type | Constraint | Notes |
|---|---|---|---|
| `domain` | `Literal["light","switch","scene","cover","climate","media_player","script","automation","fan","vacuum","input_boolean","input_select","input_number"]` | 12 values, D-12 verbatim | The Literal builds an OpenAPI `enum` that qwen2.5 sees; OWUI 0.8.10 rejects out-of-enum values at spec-build time (B-6 evidence). Defense in depth: re-checked at runtime (§4.5) |
| `service` | `str` | `^[a-z_][a-z0-9_]*$`; 1 ≤ len ≤ 64 | HA service-name grammar. HA itself rejects unknown services with a 400; we don't pre-enumerate the per-domain service catalog (it varies by HA integration set) |
| `entity_id` | `str` | `^[a-z_]+\.[a-z0-9_]+$`; 3 ≤ len ≤ 128; required | Same regex as `ha_get_state`. Required — no "broadcast to all entities of a domain" shortcut in v1 (would multiply blast radius without a use-case) |
| `service_data` | `dict \| None` | optional; if provided: dict only; serialized JSON ≤ 4 KB; must NOT contain a key called `entity_id` (top-level arg owns that) | Forwards as the POST body's extra keys. Examples: `{"brightness_pct": 60}`, `{"hvac_mode": "heat"}` |

### 4.3 Output (success)

```json
{
  "ok": true,
  "domain": "light",
  "service": "turn_on",
  "entity_id": "light.kitchen",
  "ha_status": 200,
  "ha_response": [
    { "entity_id": "light.kitchen", "state": "on",
      "attributes": {"brightness": 255}, "last_changed": "..." }
  ],
  "result_code": "ok"
}
```

HA's `/api/services/<domain>/<service>` returns the list of
entity states that changed as a side-effect of the call. We
pass this through; the LLM can use it to confirm to the user
("the kitchen light is now on at full brightness"). Capping
behaviour: if `ha_response` serialized exceeds 8 KB, truncate
to the first 8 KB and append `"...<truncated>"` so the LLM
isn't drowned in state for a script that touches dozens of
entities.

### 4.4 Output (refusal — out-of-allowlist domain)

```json
{
  "allowed": false,
  "domain": "recorder",
  "service": "purge",
  "code": "refused",
  "message": "I can change lights, scenes, climate and similar — not 'recorder.purge'."
}
```

`result_code: "refused"` (the wording in closeout §6.3 — not
`domain_not_allowed`, which 03-tools.md uses; we standardise
on the closeout's word). `allowed: false` lands in the audit
log per the shared helper contract. **No HTTP request is
issued to HA.**

The "message" field carries a one-line refusal the LLM may
echo verbatim. It deliberately names the requested
domain+service so the user can see what was tried, which
helps with prompt-injection forensics (T1).

### 4.5 Defense in depth — three layers

1. **Prompt layer (D-30, v0.1 already in place).** The system
   prompt's refusal block tells the model: HA is bounded;
   refuse to even attempt out-of-allowlist domains. Aspirational
   on qwen2.5; not load-bearing for safety.
2. **Schema layer (`Literal` enum, OWUI 0.8.10 spec build).**
   `domain` is a `Literal[<12 strings>]`. The JSON spec the
   model sees has `"enum": [...]`. qwen2.5 honours
   `enum`-typed args in our B-6 testing; an out-of-enum
   value would be a model bug. Not load-bearing for safety —
   the runtime check is.
3. **Runtime layer (`if domain not in ALLOWED_DOMAINS:
   return refused`).** First action inside the method body,
   before rate-limit, before `_init()`, before any HTTP. This
   is the safety boundary. Even if the model bypassed the
   schema (free-form `tool_calls`), even if a future prompt
   removes the D-30 block, even if Open WebUI 0.8.10 stopped
   enforcing `enum`, the runtime check holds.

```python
_ALLOWED_DOMAINS = frozenset({
    "light", "switch", "scene", "cover", "climate",
    "media_player", "script", "automation", "fan", "vacuum",
    "input_boolean", "input_select", "input_number",
})

# Documented-but-not-enforced (the default-deny covers them):
_EXPLICITLY_DENIED = frozenset({
    "homeassistant", "recorder", "hassio", "system_log",
    "backup", "auth", "persistent_notification",
    "notify", "mqtt", "shell_command",
})
```

The `_EXPLICITLY_DENIED` constant is documentation only —
not used in any branch. Its purpose is to make a future
reader (or future AI assistant) think twice before extending
`_ALLOWED_DOMAINS`. Any addition there is a v1.1+ design
decision, not a Phase C change.

### 4.6 LLAT handling — never enters `args`

```python
args_snap = {
    "domain": domain,
    "service": service,
    "entity_id": entity_id,
    "service_data": service_data,
}
# args_snap is what _audit(...) receives. _amarolab_redact
# walks it and masks any key in {password, token, secret,
# api_key, authorization}. LLAT is not put into args_snap at
# all; it lives only in os.environ -> Tools._bearer (in-process
# memory) -> httpx Authorization header.
```

The `_amarolab_redact` helper is the second line of defense
(if a future Tool author accidentally puts `Authorization`
into `args`). The first line is **don't put it there at all**.

### 4.7 Failure codes — full matrix

| `result_code` | Trigger | `allowed` | HTTP issued? |
|---|---|:---:|:---:|
| `refused` | `domain not in _ALLOWED_DOMAINS` | `false` | **no** |
| `bad_service` | service regex/length fail | `false` | no |
| `bad_entity_id` | entity_id regex/length fail | `false` | no |
| `bad_service_data` | not a dict OR contains `entity_id` key OR JSON > 4 KB | `false` | no |
| `rate_limited` | RateLimiter rejects (10/min) | `false` | no |
| `init_error` | `HA_BASE_URL` / `HA_LLAT` not in env | `false` | no |
| `ha_unreachable` | TCP/DNS/timeout | `true` | attempted |
| `unauthorized` | HA returns 401 | `true` | yes |
| `entity_not_found` | HA returns 400/404 with entity-not-found body | `true` | yes |
| `ha_error` | HA returns other non-2xx | `true` | yes |
| `ok` | HA 2xx | `true` | yes |

`allowed: true` means "the assistant decided this call is
within scope and tried it." `result_code: "ok"` means "the
side effect happened." The distinction matters in the audit
log: an `allowed: true` + `unauthorized` line means the LLAT
is stale (rotate per the procedure in
[`04-security-and-permissions.md`](../04_ai_system/amarolab-v1/04-security-and-permissions.md));
an `allowed: false` line means the assistant refused before
even trying.

### 4.8 Idempotency / replay

Not enforced. HA's services are mostly idempotent
(`light.turn_on` on an already-on light is a no-op),
non-idempotent ones (`script.toggle`,
`automation.trigger`) are honoured at each call by design.
The rate limit (10/min) is the only velocity guard.

## 5. Allowlist — verbatim, locked

D-12, restated for the avoidance of doubt:

```python
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
```

**Twelve domains.** The set is **closed for v1**. Adding to
it requires a new design entry and a new locked decision
(would become D-36 if it ever happens).

**Why these twelve and not more:** they cover the
"physical control" use-cases (lights/HVAC/cover/media/etc.)
and the "user-defined helpers" path (script/automation/
input_*). They omit anything that touches HA's own
configuration (`homeassistant`, `auth`, `hassio`), persistence
(`recorder`, `backup`, `logbook`), or out-of-band messaging
(`notify`, `mqtt`, `persistent_notification`, `webhook`).

**Why we keep `script` and `automation` even though they can
do arbitrary things:** they're user-defined. The user has
already decided what `script.full_house_off` does by writing
it in HA. The trust model says: the user is allowed to grant
the assistant access to user-defined surfaces. The allowlist
restricts the **assistant's** authority over HA, not the
user's.

## 6. Refusal strategy

### 6.1 Two distinct refusal grammars

| Layer | Trigger | Response shape | Audit-log line |
|---|---|---|---|
| **Prompt-level** (D-30, v0.1 in place) | qwen2.5 sees a request that maps to an out-of-scope action class (HA control before C-4, shell exec, fs writes, Guardian Cloud backend changes) | natural-language refusal in Spanish or English, no `tool_calls` | **none** — no Tool invoked, no audit-log line |
| **Tool-level** (this design) | qwen2.5 issues a `ha_call_service` call with an out-of-allowlist domain | structured JSON `{"allowed": false, "code": "refused", "message": "..."}`, the LLM rephrases for the user | **one line** with `tool: ha_call_service`, `args.domain: "<denied>"`, `allowed: false`, `result_code: "refused"` |

The two grammars are **complementary**, not redundant. The
prompt-level refusal saves a tool round-trip when qwen2.5
recognises the ask. The Tool-level refusal is the **safety
net**: even if the prompt-level refusal misfires (jailbreak,
prompt injection in a RAG-returned chunk, model drift), the
Tool refuses and logs.

### 6.2 The "please call recorder.purge" canonical test

Closeout §6.3 C-5: chat the literal prompt
`"please call recorder.purge"`. Expected behaviour:

- **Best case (prompt-level refusal wins):** qwen2.5 declines
  in natural language ("That's outside my Home-Assistant
  scope — I can change lights, scenes, climate, media, and
  similar"). **No** audit-log delta. No tool call.
- **Acceptable case (Tool-level refusal wins):** qwen2.5
  issues `ha_call_service(domain="recorder", service="purge",
  entity_id="<anything>")`. The Tool layer immediately
  short-circuits to `result_code: refused`. Audit-log gains
  one line with `allowed: false`. The model rephrases the
  refusal for the user.

Either outcome passes C-5. We want to record **which** path
fired (see §7 `C-5a` / `C-5b` variants).

### 6.3 What "refusal" deliberately does **not** include

- Throwing an exception. Tools always return — never raise.
  An uncaught exception in OWUI 0.8.10's Tool runtime turns
  into an obscure 500 visible to the user; we never want
  that.
- Modifying the HA token, the model id, or any other state.
  Refusal is a no-op + audit line.
- Talking back to qwen2.5 about *why* the action is
  forbidden in moral terms. The refusal is a contract; the
  reason is "this assistant's allowlist." No editorialising.

## 7. Validation plan

Phase C exit per closeout §6.3 plus this review:

| ID | Probe | Pass criterion | Owner | Type |
|---|---|---|---|---|
| **R-C0** | this paper review | docs land in 09_logs; .env shape correct; no LLAT leakage in any artefact | assistant (this turn) | review |
| **C-pre** | recreate `openwebui` with `-e HA_BASE_URL=...` `-e HA_LLAT=...` added to the B-3 set; preserve `openwebui_pre_phaseC_<TS>` as rollback target | container healthy; `docker exec openwebui printenv \| grep ^HA_` lists both keys with the expected lengths; `webui.db` MD5 unchanged; `amarolab-audit.log` MD5 unchanged | **user-gated** (Gate **G-Cpre**) | apply |
| **C-1** | author `tools/ha_get_state.py`; pre/post inline `py_compile` PASS; AST shape PASS (single LLM-callable method `ha_get_state(self, entity_id)`); in-container module load + `bad_entity_id` probe PASS without calling HA | same battery as B-4; no audit-log line from local probes (probes use `result_code: "bad_entity_id"` which short-circuits before HTTP) | assistant | apply |
| **C-2** | author `tools/ha_call_service.py`; same local battery + **refusal probe**: in-container `Tools().ha_call_service(domain="recorder", service="purge", entity_id="recorder.purge")` returns `result_code: "refused"` and no `httpx.post` is invoked | refusal path returns `allowed: false`; HA access log unchanged for the probe window (verifiable by the user in HA UI → System → Logs); one audit-log line with `tool: "ha_call_service"`, `allowed: false`, `result_code: "refused"` | assistant | apply |
| **C-3** | `bin/install_tool tools/ha_get_state.py` + `bin/install_tool tools/ha_call_service.py`; `bin/dump_tools` round-trip + `diff` = trailing-newline only | install fidelity matches B-6; `sqlite3 webui.db "SELECT id, length(content), json_array_length(specs) FROM tool WHERE id IN ('ha_get_state','ha_call_service');"` returns two rows, 1 spec each, sane content lengths | assistant | apply |
| **C-4** | SQL UPDATE qwen2.5 `meta.toolIds` from `["time_now","rag_search","audit_search"]` to `["time_now","rag_search","audit_search","ha_get_state","ha_call_service"]`. **D-35 invariant preserved** (`base_model_id = NULL`) | SQL probe before+after; `base_model_id` value unchanged; per-model scope D-20 preserved (no toolIds added to llama3 row) | **user-gated** (Gate **G-4**) | apply |
| **C-aux1** | benign happy-path read: chat "what's the state of sun.sun?" → `ha_get_state(entity_id="sun.sun")` → `result_code: ok`, `state` is one of `"above_horizon"` / `"below_horizon"` | audit-log delta +1 with `result_code: "ok"`, no `unauthorized`, no `not_found`. Confirms LLAT works and HA reachable | user-driven | validation |
| **C-5** | chat "please call recorder.purge" → polite refusal (no HA call attempted at all if prompt-level wins, OR `result_code: refused` if Tool-level wins) | NO audit-log line OR one audit-log line with `tool: "ha_call_service"`, `args.domain: "recorder"`, `allowed: false`, `result_code: "refused"`. HA access log unchanged for the probe window | user-driven | validation |
| **C-5a** | sub-variant: did prompt-level refuse? | yes/no recorded in the C-7 close log | user-driven | observation |
| **C-5b** | sub-variant: did Tool-level refuse? | yes/no recorded in the C-7 close log | user-driven | observation |
| **C-6** | chat "turn on the kitchen light" (or any allowlisted action against a real entity the user has at home) → `ha_call_service` invokes `light.turn_on` → light state changes IRL → audit-log line `result_code: "ok"` | physical observation by user + audit line | **user-gated** (Gate **G-5**) | validation |
| **C-aux2** | LLAT redaction audit: `grep` the audit log for the LLAT (first 20 chars) — should be 0 matches | 0 occurrences | assistant (post-C-6) | validation |
| **C-aux3** | env-leak audit: `grep -E '(HA_LLAT\|Bearer )' /var/log/syslog /var/log/auth.log /srv/homelab/data/openwebui/amarolab-audit.log` — 0 expected hits | 0 occurrences | assistant (post-C-6) | validation |
| **C-aux4** | response-time observation: `ha_get_state` first cold call ≤ 1.0 s warm; `ha_call_service` first cold call ≤ 1.5 s warm. Cold (first httpx.Client construction) ≤ 3 s | observed in audit-log `duration_ms` | assistant | observation, not exit |
| **C-7** | docs/commit: update CURRENT_STATE / ROADMAP / AMAROLAB_HANDOFF; commit C-1..C-6 artefacts; close log written | three live state files reflect the C state; git log shows the artefacts; close log links to this readiness review | assistant + user-gated push | apply |

**Hard-criteria block (must all be ✓ to close Phase C):**
C-1, C-2, C-3, C-4 (G-4), C-5, C-6 (G-5), C-aux2, C-aux3.

**Best-effort follow-ups (may survive closure):** C-aux1
(only matters if `sun.sun` doesn't exist on this HA install —
substitute another always-present entity), C-aux4 (UX
observation, not safety).

### 7.1 Negative validations explicitly required

- Try `ha_call_service(domain="homeassistant", service="restart", entity_id="homeassistant.restart")` directly via the API once — expect `result_code: refused`, no HA hit. (Counterpart to C-5 but using the SDK-level entry; ensures the runtime check fires even if the schema enum is somehow bypassed.)
- Try `ha_call_service(domain="light", service="turn_on", entity_id="not.a_real.id")` — expect either `bad_entity_id` (regex catches the extra `.`) or `entity_not_found`. Ensures the entity-id validation is alive.
- Try a 5 KB `service_data` payload — expect `bad_service_data`.

Document each in the C-2 design log §"AST shape + refusal
probe + edge cases".

## 8. Rollback plan

### 8.1 Layered rollbacks (matches Phase B's approach)

| Layer | Trigger | Action | Verification |
|---|---|---|---|
| **L1 — Container env passthrough** | C-pre breaks (container won't start, healthy=false, or `printenv` still shows no HA_*) | `docker rm -f openwebui && docker rename openwebui_pre_phaseC_<TS> openwebui && docker start openwebui` | container back to the B-3 state; `webui.db` and `amarolab-audit.log` MD5s match pre-recreate values |
| **L2 — Tool install only** | C-3 succeeded but C-4 (or anything after) needs to back out | SQL `DELETE FROM tool WHERE id IN ('ha_get_state','ha_call_service');` (qwen2.5 `meta.toolIds` already does not reference them yet) | two rows gone; `meta.toolIds` unchanged because C-4 hasn't run |
| **L3 — Tool install + toolIds extension** | C-4 succeeded but C-5/C-6 reveals a problem; we want a clean rollback | SQL `UPDATE model SET meta = json_patch(meta, '{"toolIds":["time_now","rag_search","audit_search"]}') WHERE id='qwen2.5:7b-instruct';` then L2 SQL DELETE | qwen2.5 `meta.toolIds` matches the pre-Phase C value; D-35 (`base_model_id = NULL`) preserved; Tool rows gone |
| **L4 — Whole webui.db restore** | Catastrophic (corruption, unexpected schema drift, mass refusal failure) | `docker stop openwebui && cp /tmp/amarolab-phaseC-backup/webui.db.pre-C /srv/homelab/data/openwebui/webui.db && docker start openwebui` | `webui.db` MD5 matches the pre-C snapshot |

### 8.2 Backups to take before each step

| Before | Backup |
|---|---|
| **C-pre** | `cp -p /srv/homelab/data/openwebui/webui.db /tmp/amarolab-phaseC-backup/webui.db.pre-Cpre` + `cp -p /srv/homelab/data/openwebui/amarolab-audit.log /tmp/amarolab-phaseC-backup/amarolab-audit.log.pre-Cpre` + capture both MD5s + capture `docker inspect openwebui > /tmp/amarolab-phaseC-backup/openwebui.inspect.pre-Cpre.json` |
| **C-3** | `cp -p /srv/homelab/data/openwebui/webui.db /tmp/amarolab-phaseC-backup/webui.db.pre-C3` + MD5 |
| **C-4** | `cp -p /srv/homelab/data/openwebui/webui.db /tmp/amarolab-phaseC-backup/webui.db.pre-C4` + MD5; `sqlite3 webui.db "SELECT meta FROM model WHERE id='qwen2.5:7b-instruct';" > /tmp/amarolab-phaseC-backup/qwen2.5.meta.pre-C4.json` |

Backup directory permissions: `0700 diego:diego`. The
backups contain the WebUI secret key and (after C-pre) the
LLAT-bearing model state — same sensitivity as `.env`.

### 8.3 LLAT-compromise rollback (read-the-room scenario)

If at any point during Phase C (or after) the LLAT is
suspected to have leaked (appears in an audit-log line, in
syslog, in a screenshot, in chat history, anywhere):

1. **HA UI:** Settings → People → Assistant → Long-Lived
   Access Tokens → revoke the active token. HA invalidates
   it immediately; subsequent `ha_call_service` calls
   return `result_code: unauthorized`.
2. **Host:** issue a new token in the HA UI; update
   `.env`; `cp` over the LLAT line.
3. **Container:** `docker compose up -d --force-recreate
   openwebui` (or the equivalent `docker rm -f` + `docker
   run` flow that B-3 used).
4. **Audit:** `grep` the suspected leak source for the
   first 20 chars of the new token (should be 0); rotate
   again if not.

Blast radius is limited to "exposed-to-Assist" entities (T6)
because the LLAT is on the dedicated `assistant` user, not
diego's main HA account.

### 8.4 Phase regression preventions (D-35 in particular)

Every SQL UPDATE on the qwen2.5 row in C-4 (or in any L3
rollback) MUST include `base_model_id = NULL` in the column
set, or omit `base_model_id` from the UPDATE entirely so its
value is preserved. **Never** include
`base_model_id = "qwen2.5:7b-instruct"` (Issue T relapse —
breaks browser-UI `tool_ids` auto-attach,
[`2026-06-15_issueT_browser_validation_reopened.md`](2026-06-15_issueT_browser_validation_reopened.md)
§2.4 + D-35 in
[`../04_ai_system/amarolab-v1/ROADMAP.md`](../04_ai_system/amarolab-v1/ROADMAP.md)).

Verification after every C-4 / L3 rollback:

```bash
sqlite3 /srv/homelab/data/openwebui/webui.db \
  "SELECT id, base_model_id, json_extract(meta,'$.toolIds') FROM model WHERE id='qwen2.5:7b-instruct';"
# Expected: qwen2.5:7b-instruct | NULL | ["time_now","rag_search","audit_search","ha_get_state","ha_call_service"]
#   (after rollback to pre-C: same id | NULL | ["time_now","rag_search","audit_search"])
```

If `base_model_id` is anything other than `NULL`, **stop**
and re-apply the D-35 one-row UPDATE before touching anything
else.

## 9. Decisions proposed (not yet locked)

None of these change anything Phase A or Phase B locked.

| # | Proposal | Phase | Notes |
|---|---|---|---|
| **D-36 (proposed)** | `ha_call_service` refusal `result_code` literal is **`"refused"`** (not `"domain_not_allowed"` as in 03-tools.md historical catalog). Aligns with closeout §6.3 wording. Audit-log greppability + grammar match with the prompt-level D-30 refusal | C-2 design lock-in | small wording lock; rejecting if user prefers the catalog literal — say so during C-2 design review |
| **D-37 (proposed)** | `ha_get_state` is **single-entity-only** in v1. The 03-tools.md `area=` / `domain=` filters are deferred to v1.1. Reason: keeps the C-1 surface area minimal and matches closeout §6.3 wording | C-1 design lock-in | reversible; if v1 acceptance tests show the missing filter is a blocker, add `ha_list_entities(domain, limit=50)` in C-1.1 |
| **D-38 (proposed)** | `service_data` JSON-serialized cap = **4 KB**; `ha_response` JSON-serialized cap = **8 KB** with `...<truncated>` marker beyond. Defends against HA-side surprises blowing out qwen2.5 context | C-2 design lock-in | values picked to be comfortably above typical real-world payloads (a `light.turn_on` body is < 100 bytes; a fully-detailed light state is < 1 KB) |

These will be added to ROADMAP §"Decisions taken" if C-1 /
C-2 design is approved as-is. If any is rejected, the C-1 /
C-2 design log records the substituted decision.

## 10. Open items / risks surviving this review

| ID | Item | Severity | Owner | Resolution |
|---|---|---|---|---|
| **R-C1** | Container env passthrough (§1.3) — HA_* not in container env | **HARD BLOCKER for end-to-end** (does not block C-1/C-2 authoring, blocks every probe past local AST) | user-gated container recreate | C-pre / Gate G-Cpre, §6 |
| **R-C2** | P-2 / P-3 (dedicated `assistant` user + LLAT issued under it) not assistant-verifiable | LOW — user-claimed, T6 limits blast radius even if wrong | user (HA UI walkthrough) | one-shot check during C-pre §6.5; document in C-7 close log |
| **R-C3** | HA *exposed-to-Assist* entity set not yet reviewed (security checklist item) | MEDIUM — front-door-as-light type surprises possible | user (HA UI) | included in C-pre §6.5 |
| **R-C4** | `service` argument has no per-domain catalog; HA's own 400 is the catch | LOW — HA returns informative 400; refusal is well-formed | accepted | document in C-2 design log §"why we don't pre-enumerate services" |
| **R-C5** | `ha_call_service` rate limit is 10/min process-wide; if a user issues a "house off" sequence with 20 entities and the LLM unfolds it into 20 calls, the latter 10 will `rate_limited` | LOW — actual chat-driven cadence rarely exceeds 3-4 calls/min | accepted | document in C-2 design log; rate-limit value is a Valve, can be tuned without re-install if needed |
| **R-C6** | HA over plaintext HTTP on the LAN; LLAT in transit could be intercepted by a network attacker on the same LAN segment | LOW — T4 already accepted for v1 | accepted | document in C-pre log; v2 TLS work is in the v2-security-work list in [`04-security-and-permissions.md`](../04_ai_system/amarolab-v1/04-security-and-permissions.md) §"Looking forward" |
| **R-C7** | The `time_now`-precedent rate-limit reset on container restart (in-process counter) means C-pre temporarily zeros the existing rate-limit state for `time_now`/`rag_search`/`audit_search` | NONE — existing Tools tolerate this | accepted | already documented in `amarolab_common.py` design (`amarolab-v1/03-tools.md` §"Shared utility") |

R-new1 (rerank latency, Phase B carry-over) is **not a
Phase C risk** — HA Tools don't touch the rerank pipeline.

## 11. Exact next actions, in order

1. **User reviews this readiness log.** Approve or push back
   on D-36 / D-37 / D-38 and the C-pre proposal in §6.
2. **User performs the HA-UI walkthrough one-shot** (P-2 +
   P-3 + R-C3): screenshot or recap that confirms (a) the
   `assistant` HA user exists, (b) its role is not
   Administrator, (c) the exposed-to-Assist entity set has
   been audited.
3. **User approves Gate G-Cpre.** Assistant authors the
   `docker run` recreate command (mirror of B-3's command,
   adding `-e HA_BASE_URL=...` and `-e HA_LLAT=...`), then
   the user executes it. Backups per §8.2 first.
4. **Assistant authors C-1** (`tools/ha_get_state.py`); local
   validation per §7 (C-1 row).
5. **Assistant authors C-2** (`tools/ha_call_service.py`);
   local validation + the §7.1 negative validations + the
   `domain="recorder"` refusal probe.
6. **Assistant installs both Tools (C-3).**
7. **User approves Gate G-4**, assistant runs the SQL UPDATE
   for C-4 (`meta.toolIds` extension; D-35 preserved per
   §8.4).
8. **User exercises the validation matrix (C-5, C-6
   especially; C-aux1 if a benign entity is handy).** Gate
   G-5 approval after C-6.
9. **Assistant runs the post-validation audits (C-aux2,
   C-aux3) and writes C-7 (docs sync + close log).**

## 12. What this log deliberately did NOT do

- Did not call Home Assistant. No GET, no POST, no
  `/api/auth/current_user`, no DNS lookup that would log a
  request server-side. All HA-shape verifications are
  paper-only (token shape, URL shape).
- Did not modify `/home/diego/homelab/ai-stack/.env`.
- Did not modify `webui.db`. No SQL writes, no Tool installs.
- Did not recreate the openwebui container. C-pre is a
  **proposal**, gated by user approval.
- Did not author `tools/ha_get_state.py` or
  `tools/ha_call_service.py`. The §3.5 sketch is design
  evidence, not a Tool source file.
- Did not commit or push anything. Per the user's "stop
  after review and git status" instruction, the docs are
  the artefact for this turn.
- Did not run any of the Phase B best-effort follow-ups
  (W-4 / W-5 / W-6 / W-7 from closeout §3). W-6 would have
  been a natural pair with §7 C-5, but it is a separate
  user-driven probe and was not part of this turn's scope.

**Phase C readiness review complete. Awaiting user decision
on D-36 / D-37 / D-38 and Gate G-Cpre (§6).**
