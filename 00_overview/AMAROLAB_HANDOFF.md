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

Amarolab Homelab

Personal infrastructure focused on:

* Local AI
* Home automation
* Learning infrastructure
* Documentation
* Portfolio development
* Guardian Cloud backend hosting
* Future Amarolab Assistant

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

### Home Automation

* Home Assistant
* Mosquitto
* Zigbee2MQTT

### Infrastructure

* Docker
* PM2
* Cloudflared
* Restic Backups

### Production Service

Guardian Cloud backend

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

Build Amarolab Assistant v1.

Current phase:

Phase D — Voice (next active phase, not yet started).

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
* Phase D — Next. Voice interaction.

Not yet:

* Whisper
* Piper
* Home Assistant Assist

---

## Next Immediate Task

Start Phase D — Voice. Scoping work:

1. Decide between locally-hosted (Whisper + Piper running
   on the same host as Open WebUI / Home Assistant) and
   HA-Assist integrated pipelines.
2. Validate microphone hardware path (USB / network
   audio).
3. Choose initial wake word + Piper voice.

Pre-Phase-D blockers: **none open.** Mosquitto auth
hardening landed 2026-06-17 (`allow_anonymous false`,
`homeassistant` + `zigbee2mqtt` users + ACLs) and Gate
G-5 was re-executed end-to-end through the hardened
broker.
