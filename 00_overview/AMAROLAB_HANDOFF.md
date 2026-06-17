# AMAROLAB_HANDOFF
## Mandatory Reading Order

1. AMAROLAB_HANDOFF.md
2. CURRENT_STATE.md
3. ROADMAP.md
4. INITIAL_SYSTEM_STATUS.md (optional historical context)
Last updated: 2026-06-17

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

* Open WebUI
* Ollama
* Qdrant

### Voice (Phase D — in progress)

* `aurora-whisper` (Wyoming STT, D-1.2 closed
  2026-06-17)

### Home Automation

* Home Assistant
* Mosquitto
* Zigbee2MQTT

### Infrastructure

* Docker
* PM2
* Cloudflared
* Restic Backups

### Hosted independent project

**Guardian Cloud** — independent project currently
hosted on AMAROLAB infrastructure.

IMPORTANT:

Guardian Cloud is considered production.

Do not modify Guardian Cloud without explicit approval.

---

## Current AI Architecture

Open WebUI
↓
Ollama
↓
Qdrant
↓
RAG Collections

Collections:

* homelab_docs
* guardian_cloud
* ensambla2
* infra_audits

Future:

* myfreetour

---
## Current Operational Status

The Home Assistant integration is now operational.

Validated capabilities:

- ha_get_state
- ha_call_service
- audit logging
- allowlist enforcement
- runtime secret loading
- Zigbee device control

Verified device:

switch.impresora_3d

The first real-world state change was executed successfully on 2026-06-17.

Future assistants should treat Home Assistant tool integration as PRODUCTION READY.

The voice STT layer (`aurora-whisper`) is operational
as of 2026-06-17 (D-1.2 closed). Gate G-D1 Wyoming
path passed: WER 0.000 against the canonical
openai/whisper smoke-test clip, real-time factor
0.055 on UM790 CPU. End-to-end voice control is
**not** yet operational — Piper, openWakeWord, the
HA Assist pipeline, and the Open WebUI Audio
integration are still to be installed in D-1.3
through D-1.7.

Apply log:
`09_logs/2026-06-17_phaseD_whisper_installed.md`.

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

Pending:

* R-01 Cloudflare Tunnel Token Rotation

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

Phase D — Voice (**in progress**; D-1.2 closed
2026-06-17).

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
* Phase D — **In progress.**
  * D-1.1 (documentation skeleton) — closed.
  * D-1.2 (Whisper standup) — **closed 2026-06-17.**
    `aurora-whisper` (`rhasspy/wyoming-whisper:3.2.0`,
    `base-int8`) operational; Gate G-D1 Wyoming path
    passed (WER 0.000, RTF 0.055). HTTP-shim path of
    G-D1 deferred to D-1.7. Apply log:
    `09_logs/2026-06-17_phaseD_whisper_installed.md`.
  * D-1.3 through D-1.9 — open.

Not yet:

* Piper (`aurora-piper`)
* openWakeWord (`aurora-wakeword`)
* Home Assistant Assist pipeline (`AURORA v1`)
* Open WebUI Audio integration

---

## Next Immediate Task

Continue Phase D — Voice. D-1.2 (Whisper) is closed;
the next step is **D-1.3 — Piper standup**.

Per the approved spec in
`04_ai_system/amarolab-v1/phase-d/03-component-spec.md`
and the deployment plan in
`03_services/voice-stack/piper/piper-deployment.md`:

1. Pull `rhasspy/wyoming-piper:<pinned tag>` and
   document the `docker run` recipe.
2. Create `aurora-piper` on `ai-local_default` with
   bind mount `/srv/homelab/data/piper/`, voice
   `es_ES-davefx-medium`, Wyoming port `10200/tcp`
   (internal-only).
3. Run Gate G-D2 (Piper TTS canary).
4. Write `09_logs/2026-MM-DD_phaseD_piper_installed.md`
   and close decisions C-D-02 and C-D-06.

Pre-Phase-D blockers: **none open.**
Pre-D-1.3 blockers: **none open.**
