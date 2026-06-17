# AMAROLAB Architecture

Last updated: 2026-06-17

---

# Purpose

This document describes the current architecture of
the **AMAROLAB** ecosystem.

**AMAROLAB** — Personal Innovation Lab and Digital
Infrastructure Ecosystem — provides infrastructure,
automation, knowledge systems, AI services and
documentation. It hosts **AURORA** (the AMAROLAB
Personal AI Assistant) and independent projects such
as **Guardian Cloud**.

This document is the primary architectural reference
for AMAROLAB infrastructure and the services that run
on it, including AURORA. It does **not** describe
Guardian Cloud's internal architecture; that project
maintains its own documentation.

This file is intended for future maintenance,
onboarding and portfolio presentation.

---

# Naming

**AMAROLAB**

Personal Innovation Lab and Digital Infrastructure
Ecosystem.

**AURORA**

Personal AI Assistant for the AMAROLAB ecosystem.

**Guardian Cloud**

Independent project currently hosted on AMAROLAB
infrastructure.

---

# Architecture Overview

```text
Internet
    │
    ▼
FRITZ!Box 5690 Pro
    │
    ▼
LAN
    │
    ▼
UM790 Pro (Main Server)
    │
    ├── Open WebUI
    ├── Ollama
    ├── Qdrant
    │
    ├── Home Assistant
    ├── Mosquitto
    ├── Zigbee2MQTT
    │
    ├── Cloudflared
    ├── PM2
    └── Restic
```

---

# Hardware

## Main Server

| Component | Specification        |
| --------- | -------------------- |
| Model     | Minisforum UM790 Pro |
| CPU       | AMD Ryzen 9 7940HS   |
| RAM       | 32 GB DDR5           |
| Storage   | 512 GB SSD           |
| OS        | Linux                |

---

## Network

| Component     | Specification      |
| ------------- | ------------------ |
| Router        | FRITZ!Box 5690 Pro |
| Connectivity  | LAN                |
| Remote Access | VPN                |
| SSH Access    | Enabled            |

---

# Core Service Architecture

## Artificial Intelligence

```text
Open WebUI
    │
    ▼
qwen2.5:7b-instruct
    │
    ├── time_now
    ├── rag_search
    ├── audit_search
    ├── ha_get_state
    └── ha_call_service
    │
    ▼
Qdrant
```

---

## RAG Collections

Current collections:

```text
homelab_docs
guardian_cloud
ensambla2
infra_audits
```

Planned:

```text
myfreetour
```

---

# Home Automation Architecture

```text
Home Assistant
        │
        ▼
Mosquitto
        │
        ▼
Zigbee2MQTT
        │
        ▼
Zigbee Network
```

---

## Current Devices

### Smart Plug

```text
Friendly Name:
Impresora 3D

Model:
Sonoff S60ZBTPF
```

---

### Roller Shutter

```text
Friendly Name:
Toldo

Model:
Sonoff MINI-ZBRBS
```

---

## Validated Control Path

Validated during Gate G-5.

```text
Open WebUI
        │
        ▼
ha_call_service
        │
        ▼
Home Assistant
        │
        ▼
Mosquitto
        │
        ▼
Zigbee2MQTT
        │
        ▼
Physical Device
```

Result:

```text
State read: SUCCESS
State write: SUCCESS
Audit logging: SUCCESS
Baseline restore: SUCCESS
```

---

# MQTT Architecture

Current security posture:

```text
allow_anonymous = false
```

Users:

```text
homeassistant
zigbee2mqtt
```

Authentication:

```text
password_file
acl_file
```

Access model:

```text
Default Deny
Per-user ACLs
```

---

# Storage Architecture

```text
UM790
 │
 ├── Internal SSD
 │
 └── USB Disk (2 TB)
        │
        ├── Restic Repository
        ├── Backups
        └── Bulk Data
```

---

# Backup Architecture

Current solution:

```text
Restic
```

Repository location:

```text
USB Disk (2 TB)
```

Status:

```text
Operational
Validated
```

Future:

```text
Dedicated NAS
Automated replication
Multi-location backups
```

---

# Guardian Cloud

**Guardian Cloud** is an **independent project
currently hosted on AMAROLAB infrastructure**.

It is considered production.

```text
DO NOT MODIFY
WITHOUT EXPLICIT APPROVAL
```

Current hosting:

```text
UM790 Pro (AMAROLAB infrastructure)
```

Guardian Cloud is not part of AURORA. Its internal
architecture and roadmap are tracked by the Guardian
Cloud project, not in this document.

---

# Security Architecture

## Access Model

```text
VPN
 │
 ▼
SSH
 │
 ▼
Server
```

No public administrative access is required.

---

## Secrets Management

Secrets are never committed to Git.

Examples:

```text
${HA_BASE_URL}
${HA_LLAT}
${WEBUI_SECRET_KEY}
${QDRANT_API_KEY}
```

Live values remain outside version control.

---

# Future Distributed Architecture

## Permanent Node

```text
UM790
```

Responsibilities:

```text
Home Assistant
Open WebUI
Qdrant
Guardian Cloud
Backups
Automation
Infrastructure Services
```

Runs 24/7.

---

## AI Compute Node

```text
Windows Tower + RTX GPU
```

Responsibilities:

```text
Large LLMs
Whisper
Vision Models
TTS
Experimental AI Workloads
```

Runs on demand.

---

## Interconnection

```text
Home Assistant
        │
        ▼
Wake-on-LAN
        │
        ▼
RTX Node
```

Goal:

```text
Heavy AI on demand
Infrastructure always available
```

---

# Current Phase

```text
Phase A  Completed
Phase B  Completed
Phase C  Completed
Phase D  Next
```

Current objective:

```text
Voice Interface
```

Planned components:

```text
Whisper
Piper
Home Assistant Assist
Wake Word
```

---

# Architecture Principles

1. Production stays on UM790.
2. AI compute can move to dedicated hardware.
3. Documentation first.
4. If it is not documented, it does not exist.
5. No secrets in Git.
6. Everything must be recoverable.
7. Everything must be versioned.
8. Simplicity before complexity.
9. Security before convenience.
10. Learning through real infrastructure.

```
```
