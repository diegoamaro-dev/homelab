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

Pending:

* R-01 Cloudflare Tunnel Token Rotation
* Mosquitto authentication hardening — currently
  `allow_anonymous true` as a temporary validation posture
  for the Zigbee2MQTT bring-up; authenticated users + ACLs
  to be added before broader device onboarding and before
  Phase D voice work

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

Phase C — Home Assistant integration.

Phase status:

* Phase A — Completed. `qwen2.5:7b-instruct` selected as the
  primary tool-calling model.
* Phase B — Completed. Tool layer delivered:
  `time_now`, `rag_search`, `audit_search`.
* Phase C — Active. `ha_get_state` installed, attached to
  qwen2.5, and validated end-to-end with a real Home
  Assistant read against `sun.sun`. `ha_call_service`
  installed, attached to qwen2.5, and validated at the
  Tool-level refusal path. Gate G-5 (first real
  `ha_call_service` happy path on a controllable entity)
  is the next validation milestone.

Not yet:

* Voice
* Whisper
* Piper
* Home Assistant Assist

---

## Next Immediate Task

Phase C Gate G-5 — execute the first real
`ha_call_service` happy path against a controllable
allowlisted entity (e.g. `light.turn_on` /
`switch.toggle`), observe the physical state change, and
confirm the audit-log delta with `result_code = "ok"`.

Then close Phase C (C-7 — sync CURRENT_STATE / ROADMAP /
AMAROLAB_HANDOFF + Phase D handoff note).
