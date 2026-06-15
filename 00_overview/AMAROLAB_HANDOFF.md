# AMAROLAB_HANDOFF
## Mandatory Reading Order

1. AMAROLAB_HANDOFF.md
2. CURRENT_STATE.md
3. ROADMAP.md
4. INITIAL_SYSTEM_STATUS.md (optional historical context)
Last updated: 2026-06-15

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

Future:

* myfreetour

---

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

* R-04 Mosquitto
* R-12 Backups

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

Phase A.

Focus:

Brain layer only.

Not yet:

* Voice
* Whisper
* Piper
* Home Assistant tool execution
* Open WebUI Functions
* Tool Calling

---

## Next Immediate Task

Evaluate qwen2.5:7b against llama3.

Choose the primary assistant model.

Then continue with Amarolab Assistant Phase A.
