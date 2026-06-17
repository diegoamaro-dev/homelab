# Phase D — D-1.5 — Voice pipeline (`AURORA v1`) — APPLIED

> **Promoted from DRAFT 2026-06-17** after Gate G-D4 passed end-to-end
> over HTTPS via `https://ha.amarolab.es`. Closure evidence and verdict
> in [`./2026-06-17_phaseD_gate_gd4_applied.md`](2026-06-17_phaseD_gate_gd4_applied.md).
> The HTTPS path itself was unblocked by deploying a dedicated
> `cloudflared-amarolab` tunnel + container (this session) and
> applying the HA reverse-proxy trust patch in
> [`./2026-06-17_phaseD_ha_trusted_proxies_applied.md`](2026-06-17_phaseD_ha_trusted_proxies_applied.md).

- **Date:** 2026-06-17
- **Phase step:** D-1.5 (HA Assist pipeline configuration)
- **Ecosystem:** **AMAROLAB** — Personal Innovation Lab and Digital
  Infrastructure Ecosystem.
- **Assistant:** **AURORA** — Personal AI Assistant for the AMAROLAB
  ecosystem.
- **Independent project on AMAROLAB infrastructure:** **Guardian Cloud**
  — not modified by this work.
- **Status:** **APPLIED. G-D4 passed 2026-06-17.** Wyoming
  integrations (Whisper, Piper, openWakeWord) wired into Home
  Assistant via the Wyoming Protocol integration. Home Assistant
  native **Ollama** integration wired against `qwen2.5:7b-instruct`.
  Assist pipeline **`AURORA v1`** created and set as the **default /
  preferred** Assist pipeline. Voice canary helper
  `input_boolean.aurora_voice_canary` created. Voice-exposure surface
  locked down — **only** the canary helper is exposed to voice
  assistants. G-D4 ran end-to-end over HTTPS at `https://ha.amarolab.es`
  with full Read → Write → Verify → Restore cycle and canary baseline
  restored. Evidence in
  [`./2026-06-17_phaseD_gate_gd4_applied.md`](2026-06-17_phaseD_gate_gd4_applied.md).
- **Scope:** HA configuration only — Wyoming integrations, Ollama
  integration, pipeline `AURORA v1`, canary helper, voice-exposure
  ACL. No container deploys, no image pulls, no MQTT/Z2M changes, no
  Tool-layer changes, no `webui.db` schema changes, no Open WebUI
  changes, no Cloudflare changes, no DNS changes.
- **Pre-state anchor:** **Restic snapshot `63c072f4`** taken before
  the HA configuration changes in this log (per Lesson 005 — "make
  it work, validate, harden, document" — anchor exists so the
  configuration is rollbackable).
- **Inputs:**
  - Pipeline spec:
    [`../03_services/voice-stack/ha-assist/pipeline-spec.md`](../03_services/voice-stack/ha-assist/pipeline-spec.md)
  - Validation gates:
    [`../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md`](../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md)
  - Security model:
    [`../04_ai_system/amarolab-v1/phase-d/04-security-and-permissions.md`](../04_ai_system/amarolab-v1/phase-d/04-security-and-permissions.md)
  - Component spec:
    [`../04_ai_system/amarolab-v1/phase-d/03-component-spec.md`](../04_ai_system/amarolab-v1/phase-d/03-component-spec.md)
  - D-1.2 apply log (Whisper):
    [`./2026-06-17_phaseD_whisper_installed.md`](./2026-06-17_phaseD_whisper_installed.md)
  - D-1.3 apply log (Piper):
    [`./2026-06-17_phaseD_piper_installed.md`](./2026-06-17_phaseD_piper_installed.md)
  - D-1.4 apply log (openWakeWord):
    [`./2026-06-17_phaseD_wakeword_installed.md`](./2026-06-17_phaseD_wakeword_installed.md)

---

## 1. What was configured

### 1.1 Pre-state anchor (Restic)

| Field | Value |
|---|---|
| Restic snapshot ID (short) | `63c072f4` |
| Purpose | Pre-D-1.5 rollback anchor — captures the HA configuration state immediately before the Wyoming integrations, Ollama integration, pipeline, helper, and exposure ACL were added |
| Repository | Restic repository on the 2 TB USB disk (see [`../06_security/security_posture.md`](../06_security/security_posture.md) §"Backups") |

Per Lesson 010, "backups are only real after restoration testing" —
the snapshot is referenced here as a recovery point; an actual
restore drill is **not** part of D-1.5 and remains a separate
operational item.

### 1.2 Wyoming Protocol integrations (Home Assistant)

Three Wyoming Protocol integration instances added in HA Settings →
Devices & Services. Each points to the corresponding `aurora-*`
container on `ai-local_default`:

| Wyoming integration | Target | Role | Source apply log |
|---|---|---|---|
| `aurora-whisper` | `aurora-whisper:10300` | STT — `base-int8` | [D-1.2](./2026-06-17_phaseD_whisper_installed.md) |
| `aurora-piper` | `aurora-piper:10200` | TTS — `es_ES-sharvard-medium`, speaker `F` (C-D-08) | [D-1.3](./2026-06-17_phaseD_piper_installed.md) |
| `aurora-wakeword` | `aurora-wakeword:10400` | Wake word — `okay_nabu` | [D-1.4](./2026-06-17_phaseD_wakeword_installed.md) |

HA reaches the three containers over Docker DNS on
`ai-local_default`. The container endpoints remain
**internal-only** — no host port is published by any of the three
Wyoming containers (confirmed by `docker ps` — internal Wyoming
ports are bound on `127.0.0.1` only).

This closes the **HA-UI half of G-D3** (carried as `D-D4-G-D3-HA-UI`
in [D-1.4 §6](./2026-06-17_phaseD_wakeword_installed.md)) — HA
Settings → Voice assistants now lists openWakeWord as a wake-word
provider and `okay_nabu` is selectable in the pipeline editor.

### 1.3 Home Assistant — native Ollama integration

A new HA **Ollama** integration instance added under Settings →
Devices & Services.

| Field | Value |
|---|---|
| Endpoint | `http://ollama:11434` (Ollama container on `ai-local_default`) |
| Model | `qwen2.5:7b-instruct` |
| Purpose | Conversation agent slot for the `AURORA v1` Assist pipeline |

**Decoupling note.** This is the HA-side Ollama integration. It is
**not** the Open WebUI tool-calling path. Voice and chat front doors
share the **same model** but reach it through **independent
integrations**, so a restart on either side does not disturb the
other. The Tool layer (`time_now`, `rag_search`, `audit_search`,
`ha_get_state`, `ha_call_service`) is only attached to the chat path
via `webui.db.tool` and is **not** invoked from the voice path in
D-1; voice commands run through HA's native intent matching.

### 1.4 Assist pipeline — `AURORA v1`

Pipeline created under HA Settings → Voice assistants:

| Slot | Provider | Endpoint / Model |
|---|---|---|
| Pipeline name | — | `AURORA v1` |
| Default language | — | `es-ES` |
| Wake word | openWakeWord (Wyoming) | `aurora-wakeword:10400` / `okay_nabu` |
| STT | faster-whisper (Wyoming) | `aurora-whisper:10300` / `base-int8` |
| Conversation | HA Ollama integration | `http://ollama:11434` / `qwen2.5:7b-instruct` |
| TTS | Piper (Wyoming) | `aurora-piper:10200` / `es_ES-sharvard-medium` speaker `F` |
| Status | — | **Set as the default / preferred Assist pipeline** |

Pipeline / agent / STT timeouts: HA defaults accepted at this step.
Tuning is deferred until G-D4 latency is measured end-to-end over
HTTPS (Lesson 002 — "validate before documenting" — tune only after
real measurement).

### 1.5 Voice canary helper

A new HA helper entity added:

| Field | Value |
|---|---|
| Entity ID | `input_boolean.aurora_voice_canary` |
| Initial state | `off` |
| Purpose | Safe no-effect target for G-D4 voice exercise (Read → Write → Verify → Restore) — no physical device is actuated |

### 1.6 Voice-exposure lockdown

In HA Settings → Voice assistants → Expose:

| Entity | Exposed to voice assistants | Notes |
|---|---|---|
| `input_boolean.aurora_voice_canary` | **Yes** | Only D-1.5 exposure |
| `switch.impresora_3d` | No | Added at D-1.6 / G-D5 |
| `cover.toldo` | No | Out of scope for Phase D-1 |
| All `homeassistant.*` system services | No | Permanent deny per [security model](../04_ai_system/amarolab-v1/phase-d/04-security-and-permissions.md) |
| All `hassio.*` supervisor surfaces | No | Permanent deny |
| All `recorder.*` storage entities | No | Permanent deny |
| Any Guardian Cloud entity | No | Permanent deny — Guardian Cloud stays out of AMAROLAB voice |

The default-deny posture follows the D-1.5-initial stage of the
exposure ramp-up table in
[`../03_services/voice-stack/ha-assist/pipeline-spec.md`](../03_services/voice-stack/ha-assist/pipeline-spec.md)
§3. Adding the printer to the surface is explicitly deferred to D-1.6
(G-D5).

---

## 2. Validation — Gate G-D4

Spec:
[`../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md`](../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md)
§5.

### 2.1 Pre-conditions met

| Gate | State |
|---|---|
| G-D1 Wyoming path | Closed 2026-06-17 (D-1.2 log) |
| G-D1 HTTP-shim path | Deferred to D-1.7 (per D-1.2 §2.5) |
| G-D2 Piper TTS canary | Closed 2026-06-17 (D-1.3 log) |
| G-D3 container/probe half | Closed 2026-06-17 (D-1.4 log) |
| G-D3 HA-UI half | **Closed by this log** (§1.2) |
| Pipeline `AURORA v1` configured | **Closed by this log** (§1.4) |
| `input_boolean.aurora_voice_canary` exposed; nothing else | **Closed by this log** (§1.5, §1.6) |

### 2.2 G-D4 — procedure (per spec)

The G-D4 spec (Read → Write → Verify → Restore against the canary)
requires the operator to drive the pipeline from a browser
microphone session against HA Assist.

### 2.3 G-D4 execution status

**Executed and PASSED 2026-06-17.** Full evidence and acceptance-
criteria verdict in
[`./2026-06-17_phaseD_gate_gd4_applied.md`](2026-06-17_phaseD_gate_gd4_applied.md).
Two canary state transitions recorded (`on` at 21:51:24, `off` at
21:51:52); baseline restored to `off`. Whisper transcripts captured,
Ollama conversation-agent calls completed, TTS audibility confirmed
by the operator. Zero errors across the voice-stack and HA.

### 2.4 Block — root cause (historical)

Home Assistant was originally reachable only via an HTTP URL on a
LAN IP. Modern Chromium browsers (Chrome, Edge, Brave) restrict the
`MediaDevices.getUserMedia()` API to **Secure Contexts** —
`https://`, `http://localhost`, or `http://127.0.0.1`. A LAN IP over
HTTP does **not** qualify; the browser silently refused microphone
access, so the HA Assist push-to-talk button could not capture audio
to feed into the `AURORA v1` pipeline.

This was a **browser security control**, not an HA, Whisper, Piper,
openWakeWord, Ollama, or pipeline-configuration fault.

The Wyoming integrations, Ollama integration, the pipeline
configuration, the canary helper, and the exposure ACL were all
configured correctly and ready to be exercised the moment the HA
origin became a Secure Context.

### 2.5 Unblock — actions taken

G-D4 was unblocked by exposing HA over a trusted HTTPS hostname
behind a dedicated Cloudflare Tunnel. **Final architecture differs**
from the original DRAFT plan in
[`../02_infrastructure/cloudflare/amarolab_dns_architecture.md`](../02_infrastructure/cloudflare/amarolab_dns_architecture.md):
instead of attaching the existing Guardian-Cloud `cloudflared`
container to `ai-local_default`, a **separate** `cloudflared-amarolab`
container + `amarolab` tunnel was deployed for product/infrastructure
isolation (Guardian Cloud product surface and AMAROLAB infrastructure
surface must not share blast radius).

Sequence executed this session:

1. Cloudflare zone for `amarolab.es` activated.
2. Existing `cloudflared` (Guardian Cloud) reverted from any
   `ai-local_default` attachment — restored to Guardian-Cloud-only
   posture.
3. New `amarolab` tunnel created in Cloudflare Zero Trust.
4. Connector token persisted at
   `/home/diego/.secrets/cloudflared-amarolab.env` (mode `0600`, never
   committed; supersedes the R-01 pattern from day one for the new
   tunnel).
5. New compose project at `/home/diego/webs/cloudflared-amarolab/`
   created with the new container `cloudflared-amarolab` attached
   **only** to `ai-local_default`; 4/4 edge connections registered.
6. Public Hostname `ha.amarolab.es → http://192.168.178.79:8123` added
   on the new tunnel (DNS auto-created by Cloudflare).
7. HA reverse-proxy trust patch applied —
   [`./2026-06-17_phaseD_ha_trusted_proxies_applied.md`](2026-06-17_phaseD_ha_trusted_proxies_applied.md)
   added `http.use_x_forwarded_for: true`,
   `http.trusted_proxies: [172.18.0.0/16, 127.0.0.1, ::1]`, and
   `homeassistant.external_url: https://ha.amarolab.es`. HA restarted
   cleanly.
8. G-D4 re-run end-to-end from Chromium at `https://ha.amarolab.es` —
   **PASSED**. Evidence in
   [`./2026-06-17_phaseD_gate_gd4_applied.md`](2026-06-17_phaseD_gate_gd4_applied.md).

`ai.amarolab.es` (the planned chat-side front door for AURORA via
Open WebUI) is **not** yet bound to the `amarolab` tunnel — it is not
on the G-D4 critical path and is deferred as an operator action.

Guardian Cloud (`app.guardiancloud.app`, `api.guardiancloud.app`,
tunnel `1a0df79d-…`, container `cloudflared` on `cloudflare-net`)
was verified untouched at every checkpoint.

---

## 3. Pre / post state evidence

### 3.1 Pre-state

| Item | Value |
|---|---|
| Restic anchor | snapshot `63c072f4` |
| HA Assist pipelines | (whatever HA shipped — no `AURORA v1` present) |
| HA Wyoming Protocol instances | none |
| HA Ollama integration instances | none |
| `input_boolean.aurora_voice_canary` | does not exist |
| Voice-exposed entities | none |

### 3.2 Post-state

| Item | Value |
|---|---|
| HA Wyoming integrations | 3 (Whisper, Piper, openWakeWord) — all healthy |
| HA Ollama integration | 1 — `qwen2.5:7b-instruct` listed |
| HA Assist pipeline `AURORA v1` | created, set as default |
| `input_boolean.aurora_voice_canary` | exists, state `off` |
| Voice-exposed entities | exactly 1 — `input_boolean.aurora_voice_canary` |
| `aurora-whisper` container | unchanged (still healthy on `ai-local_default`) |
| `aurora-piper` container | unchanged |
| `aurora-wakeword` container | unchanged |
| `ollama` container | unchanged |
| Open WebUI | unchanged |
| Mosquitto | unchanged (hardened posture from 2026-06-17 preserved) |
| Zigbee2MQTT | unchanged |
| `cloudflared` | unchanged |
| Guardian Cloud (`guardian-web`) | unchanged |

---

## 4. What this did NOT change

- Any container image, command, or restart policy.
- Any Wyoming container's bind mount, network attachment, or
  resource cap.
- `ollama`'s container, model store, or runtime configuration.
- `webui.db` — schema, rows, Tools, `qwen2.5` model row
  (`base_model_id`, `meta.toolIds`, `params.system` — all
  unchanged).
- `/srv/homelab/data/openwebui/amarolab-audit.log`.
- Mosquitto config, users, ACLs.
- Z2M configuration or device list.
- Existing HA non-voice integrations (MQTT, Z2M discovery).
- Open WebUI configuration (no Audio settings touched — that lands
  at D-1.7).
- Cloudflared tunnel — ingress, credentials, network, version
  unchanged. **No new tunnel hostnames were added in this step.**
- Cloudflare DNS — no records were created or modified.
- Guardian Cloud (`guardian-web`).

No environment file (`ai-stack/.env`) was modified. No secrets were
introduced, rotated, or printed.

---

## 5. Decisions closed by this log

| Decision ID | Closes at | Outcome |
|---|---|---|
| C-D-05 (HA Assist pipeline timeout) | **partial** — HA defaults accepted; final tuning deferred to post-G-D4 measurement |
| D-D4-G-D3-HA-UI (HA-UI half of G-D3) | this log §1.2 | HA UI lists openWakeWord; `okay_nabu` selectable in `AURORA v1` |

---

## 6. Open / deferred items

| ID | Item | Carried to |
|---|---|---|
| ~~G-D4 over HTTPS~~ | **CLOSED 2026-06-17** — see [`./2026-06-17_phaseD_gate_gd4_applied.md`](2026-06-17_phaseD_gate_gd4_applied.md) | — |
| **G-D4 latency measurement** | Pipeline / agent / STT timeout tuning based on measured G-D4 latency (intent-resolving chat completions averaged ~3–6 s on this hardware) | Post-D-1 maintenance |
| C-D-05 (final) | Pipeline timeout values | After G-D4 latency capture |
| C-D-07 | Open WebUI Audio surface default for `qwen2.5` | D-1.7 |
| D-D1-HTTP | HTTP-shim path of G-D1 | D-1.7 |
| R-D-13 | Migrate the HTTP shim from `fedirz/faster-whisper-server` to a maintained successor | post-Phase-D maintenance |
| R-01 | Cloudflare Tunnel token rotation (existing Guardian-Cloud tunnel) | Independent of this phase — sequenced after broader documentation sync |
| **`ai.amarolab.es`** | Public Hostname not yet bound to `amarolab` tunnel | Operator action — not on Phase D-1 critical path |
| **`cloudflared-amarolab` apply log** | Deployment validated but not yet documented in its own apply log | Companion log to author |
| **DNS / architecture doc amendments** | `02_infrastructure/cloudflare/amarolab_dns_architecture.md` and `cloudflared_audit_2026-06-17.md` need to record the separate-tunnel decision | Documentation sync, pre-D-1.9 |

---

## 7. Reproducibility

The configuration in this log is captured at the HA UI level. To
reproduce on a clean HA instance:

1. Restore Restic snapshot `63c072f4` (pre-state anchor) on a
   matching host; or start from an equivalent baseline HA install
   with Whisper / Piper / openWakeWord containers per D-1.2 / D-1.3
   / D-1.4.
2. Apply §1.2 — three Wyoming Protocol integrations.
3. Apply §1.3 — HA Ollama integration.
4. Apply §1.4 — Assist pipeline `AURORA v1` with the listed slot
   bindings; set as default.
5. Apply §1.5 — create `input_boolean.aurora_voice_canary`.
6. Apply §1.6 — expose only the canary entity to voice assistants.

No CLI command captures these steps; the configuration is HA-UI
state. A future hardening item is to express the pipeline as an HA
YAML blueprint so it can be version-controlled — tracked outside
this log.

---

## 8. Stop point

Per the user instruction, D-1.5 stops here. No work has begun on:

- D-1.6 (real-device end-to-end / G-D5 — printer added to exposure).
- D-1.7 (Open WebUI Audio integration — also closes G-D1 HTTP-shim
  path).
- D-1.8 (failure-mode rehearsal / G-D6).
- D-1.9 (Phase D-1 closeout).

The overview triad
(`00_overview/CURRENT_STATE.md`, `AMAROLAB_HANDOFF.md`,
`ROADMAP.md`) will be updated at Phase D-1 closeout (D-1.9), not
now — per Lesson 005. With G-D4 passed (2026-06-17), the existing
Phase D status text in those files now reads **stale** ("D-1.2
closed; D-1.3 next") and should be amended at D-1.9 closeout to
reflect that D-1.5 (Voice pipeline + G-D4) is **closed**, with
D-1.6 (G-D5 against `switch.impresora_3d`) as the next step.
