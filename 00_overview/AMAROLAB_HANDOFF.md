# AMAROLAB_HANDOFF
## Mandatory Reading Order

1. AMAROLAB_HANDOFF.md
2. CURRENT_STATE.md
3. ROADMAP.md
4. INITIAL_SYSTEM_STATUS.md (optional historical context)
Last updated: 2026-06-18

## Purpose

This document allows any future AI session to rebuild project context quickly and continue work without relying on conversation history.

---

## Project

**AMAROLAB** — Personal Innovation Lab and Digital
Infrastructure Ecosystem.

AMAROLAB provides infrastructure, automation,
knowledge systems, AI services and documentation. It
hosts **AURORA** (the personal AI assistant for the
AMAROLAB ecosystem) and independent projects such as
**Guardian Cloud**.

Focus areas:

* Local AI
* Home automation
* Learning infrastructure
* Documentation
* Portfolio development
* Hosting of independent projects (e.g., Guardian Cloud)
* AURORA — the AMAROLAB Personal AI Assistant

---

## Naming

**AMAROLAB**

Personal Innovation Lab and Digital Infrastructure
Ecosystem. Provides infrastructure, automation,
knowledge systems, AI services and documentation.

**AURORA**

Personal AI Assistant for the AMAROLAB ecosystem.

**Guardian Cloud**

Independent project currently hosted on AMAROLAB
infrastructure.

---

## Hardware

### Main Server

* Minisforum UM790 Pro
* AMD Ryzen 9 7940HS
* 32 GB DDR5
* 512 GB SSD
* Linux

### Network

* FRITZ!Box 5690 Pro
* LAN connected server
* VPN access

---

## Running Core Services

### AI

* Open WebUI (chat + voice — `https://ai.amarolab.es`)
* Ollama (`qwen2.5:7b-instruct` shared by both front doors)
* Qdrant

### Voice (Phase D-1 — closed 2026-06-18)

Wyoming chain (HA Assist):

* `aurora-whisper` (STT, `base-int8`, D-1.2)
* `aurora-piper` (TTS, `es_ES-davefx-medium`, D-1.3)
* `aurora-wakeword` (`okay_nabu`, D-1.4)

Open WebUI HTTP shims (D-1.7):

* `aurora-whisper-http`
  (`fedirz/faster-whisper-server:0.6.0-rc.3-cpu`)
* `aurora-piper-http`
  (`ghcr.io/matatonic/openedai-speech:0.18.2`,
  voice mapped to `es_ES-sharvard-medium` speaker F)

HA Assist pipeline `AURORA v1` is the default /
preferred pipeline (language `es-ES`); voice surface
is exposed via `https://ha.amarolab.es`.

### Home Automation

* Home Assistant (HTTPS via `ha.amarolab.es`;
  reverse-proxy trust patch applied 2026-06-17)
* Mosquitto (authenticated + ACLs, hardened 2026-06-17)
* Zigbee2MQTT

### Infrastructure

* Docker
* PM2
* Cloudflared (**two separate tunnels**: existing
  `cloudflared` for Guardian Cloud; new
  `cloudflared-amarolab` on `ai-local_default` for
  AMAROLAB infrastructure surfaces — `ha.amarolab.es`,
  `ai.amarolab.es`)
* Restic Backups

### Hosted independent project

**Guardian Cloud** — independent project currently
hosted on AMAROLAB infrastructure.

IMPORTANT:

Guardian Cloud is considered production.

Do not modify Guardian Cloud without explicit approval.

---

## Current AI Architecture

Open WebUI (chat + voice)
↓
Ollama (`qwen2.5:7b-instruct`)
↓
Qdrant
↓
RAG Collections

In parallel:

Home Assistant Assist (`AURORA v1`)
↓
HA Ollama integration → same `qwen2.5:7b-instruct`

Collections:

* homelab_docs
* guardian_cloud
* ensambla2
* infra_audits

Future:

* myfreetour

---
## Current Operational Status

The Home Assistant integration is operational.

Validated capabilities:

- ha_get_state
- ha_call_service
- audit logging
- allowlist enforcement
- runtime secret loading
- Zigbee device control
- **voice control** through Aurora v1 Assist pipeline

Verified device:

`switch.impresora_3d`

Real-world state changes have been executed via:

* Open WebUI chat → `ha_call_service` (2026-06-17, Gate G-5)
* Home Assistant voice → `AURORA v1` pipeline →
  Mosquitto → Z2M → Sonoff S60ZBTPF (2026-06-18, Gate G-D5)

Both paths restore the printer to its `off` baseline
after every gate.

Future assistants should treat Home Assistant tool
integration and the Aurora v1 voice pipeline as
**PRODUCTION READY**.

### Phase D-1 closure (2026-06-18)

Aurora v1 voice pipeline operational on both front
doors:

* `https://ha.amarolab.es` — Home Assistant Assist
  push-to-talk over the Wyoming chain.
* `https://ai.amarolab.es` — Open WebUI browser mic
  over the OpenAI-API-compatible HTTP shims.

All six Phase D-1 gates landed with dated apply logs
(G-D1 through G-D6). Failure-mode rehearsal (G-D6)
confirmed the voice surface fails predictably when
each of its critical dependencies fails (STT, TTS,
LLM). Closeout document:
[`../09_logs/2026-06-18_phaseD1_closeout.md`](../09_logs/2026-06-18_phaseD1_closeout.md).

Voice exposure ACL: exactly one entity exposed —
`input_boolean.aurora_voice_canary`. The printer
(`switch.impresora_3d`) is exposed only for the
duration of a voice gate and reverted to
`should_expose = false` immediately afterwards.

## Documentation Status

Documentation consolidated into:

/home/diego/homelab

Single source of truth.

Audit documentation merged.

Security documentation merged.

AI documentation merged.

Operations documentation merged.

GitHub synchronized.

---

## Security Status

Completed:

* R-04 Mosquitto crash-loop (resolved 2026-06-13)
* R-12 Backups
* Mosquitto authentication hardening (2026-06-17) —
  moved off `allow_anonymous true` to authenticated
  `homeassistant` + `zigbee2mqtt` users with per-user
  ACLs; Gate G-5 re-executed end-to-end through the
  hardened broker. See
  `03_services/zigbee-stack/mosquitto/auth-hardening.md`
  and
  `09_logs/2026-06-17_mosquitto_auth_hardening_applied.md`
* HA reverse-proxy trust (2026-06-17) — `cloudflared-amarolab`
  bridge subnet trusted; LAN intentionally not trusted
  broadly. See
  `09_logs/2026-06-17_phaseD_ha_trusted_proxies_applied.md`
* Voice-exposure default-deny posture (2026-06-17)
  — only `input_boolean.aurora_voice_canary` is
  exposed to voice assistants; `homeassistant.*`,
  `hassio.*`, `recorder.*`, and any Guardian Cloud
  entity are permanent denies. Maintained through
  G-D4 / G-D5 / G-D6.
* Voice failure-mode safety story (2026-06-18, G-D6)
  — Whisper down / Piper down / Ollama unreachable
  scenarios validated; each fails predictably with no
  partial action and baseline restored.

Pending:

* R-01 Cloudflare Tunnel Token Rotation (existing
  Guardian-Cloud tunnel)

---

## Important Rules

* If it's not documented, it doesn't exist.
* Documentation first.
* Sanitize before GitHub.
* Do not expose secrets.
* Guardian Cloud is production.

---

## Current Goal

Build **AURORA v1** — the AMAROLAB Personal AI
Assistant.

Current phase:

**Phase D-1 — Voice — CLOSED 2026-06-18.**

Phase status:

* Phase A — Completed. `qwen2.5:7b-instruct` selected as the
  primary tool-calling model.
* Phase B — Completed. Tool layer delivered:
  `time_now`, `rag_search`, `audit_search`.
* Phase C — Completed (2026-06-17). `ha_get_state` and
  `ha_call_service` installed, attached to qwen2.5, and
  validated end-to-end. Refusal path proven against
  `recorder.purge`; read path proven against `sun.sun`;
  Gate G-5 happy-path write proven against
  `switch.impresora_3d` with full Z2M MQTT round-trip and
  baseline restore.
* **Phase D-1 — Voice — Closed 2026-06-18.**
  * D-1.1 (documentation skeleton) — closed.
  * **D-1.2 (Whisper) — closed 2026-06-17.**
  * **D-1.3 (Piper) — closed 2026-06-17.**
  * **D-1.4 (openWakeWord) — closed 2026-06-17.**
  * **D-1.5 (AURORA v1 pipeline + voice canary +
    exposure lockdown) — closed 2026-06-17.**
  * HA reverse-proxy trust patch — closed 2026-06-17.
  * **G-D4 (canary end-to-end) — PASSED 2026-06-17.**
  * **D-1.6 / G-D5 (real-device voice round-trip on
    `switch.impresora_3d`) — closed / PASSED 2026-06-18.**
  * **D-1.7 (Open WebUI Audio shims + audio surface)
    — closed 2026-06-18.**
  * **D-1.8 / G-D6 (failure-mode rehearsal) —
    closed / PASSED 2026-06-18.**
  * **D-1.9 (Phase D-1 closeout) — closed 2026-06-18.**

Closeout document:
[`../09_logs/2026-06-18_phaseD1_closeout.md`](../09_logs/2026-06-18_phaseD1_closeout.md).

---

## Next Immediate Task

**No new phase started.** Phase D-1 is closed; the
documentation triad is up to date as of 2026-06-18.

Pending post-D-1 follow-ups (tracked in
[`CURRENT_STATE.md`](CURRENT_STATE.md) and the closeout
document — none of these are mandatory next steps):

* `cloudflared-amarolab` standalone apply log.
* DNS / Cloudflare architecture doc amendments to
  record the separate-tunnel decision and the
  `ai.amarolab.es` binding.
* RTX 5070 AI-node bridge — LLM acceleration for the
  voice pipeline. Defined in
  [`../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md`](../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md).
* STT model-size bump candidate (`small` or
  `medium-int8`).
* Streaming TTS in Open WebUI.
* System-prompt trim (3 342 chars → cold-cache cost).
* R-01 Cloudflare Tunnel token rotation (Guardian
  Cloud tunnel).

Pre-Phase-E blockers: **none open.**
