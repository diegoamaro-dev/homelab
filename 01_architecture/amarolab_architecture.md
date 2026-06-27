# AMAROLAB Architecture

Last updated: 2026-06-27

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

Runs 24/7. Hosts all infrastructure, automation,
knowledge and AI front-door services, plus Guardian Cloud.

---

## AI Compute Node (Torre)

Provisioned 2026-06-18; consumed by the UM790 since RTX-1.6
(2026-06-27).

| Component | Specification |
| --------- | ------------- |
| Name      | Torre |
| Model     | Custom Windows tower |
| OS        | Windows 11 Pro |
| CPU       | Intel Core i5-10600K (6c / 12t) |
| RAM       | 32 GB |
| GPU       | NVIDIA RTX 5070, 12 GB VRAM |
| Model store | `D:\ai\ollama\models` (NVMe) |
| LAN       | 192.168.178.21 |
| Tailscale | 100.91.154.124 (node `torre`) |
| Runtime   | Ollama 0.30.10 (GPU) |
| Availability | On-demand (not 24/7) |

GPU compute only — large/fast model serving on demand.
Hosts **no** always-on AURORA component and **no** Guardian
Cloud surface. Security: Tailscale-only, host-scoped /32
firewall, headless NSSM service — see
[`../06_security/rtx_node_security.md`](../06_security/rtx_node_security.md).

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

## AI Inference Path (RTX-1.6)

Both front doors reach `qwen2.5:7b-instruct` through a
failover proxy, not a single Ollama:

```text
Open WebUI ─┐                         ┌─▶ Torre (RTX 5070 GPU)  ~101 tok/s  [primary]
            ├─▶ ollama-proxy ─────────┤        100.91.154.124:11434
Home        │   (nginx failover)      │
Assistant ──┘                         └─▶ UM790 (CPU) Ollama    ~6 tok/s    [fallback]
                                               ollama:11434
```

- Open WebUI → `ollama-proxy:11434` (docker network).
- Home Assistant → `127.0.0.1:11435` (loopback).
- The proxy uses Torre when reachable and **falls back
  automatically** to the UM790 CPU Ollama when Torre is
  asleep/offline. The UM790 stays the always-on path.
- Only the endpoint target changed; no voice/AI container
  moved. Config:
  [`../03_services/ollama-proxy/`](../03_services/ollama-proxy/).

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

# Distributed Architecture

Two-node model — **deployed** since RTX-1.6 (2026-06-27).
Production stays on the UM790; GPU AI compute runs on Torre
on demand, consumed via the `ollama-proxy` failover front
end (Torre primary + UM790 fallback).

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
Torre — Windows tower + RTX 5070 (deployed)
```

See the **AI Compute Node (Torre)** hardware entry above
for full specification.

Responsibilities (current):

```text
qwen2.5:7b-instruct on the GPU (~105 tok/s) — DEPLOYED
```

Responsibilities (future):

```text
Large LLMs
Large Whisper
Vision Models
Experimental AI Workloads
```

Runs on demand. Not 24/7.

---

## Interconnection

```text
Open WebUI / Home Assistant
            │
            ▼
       ollama-proxy        (nginx failover)
            │
   ┌────────┴─────────┐
   ▼                  ▼
Torre (GPU)        UM790 (CPU)
via Tailscale      local fallback
100.91.154.124     ollama:11434
```

- **Transport to Torre:** Tailscale (WireGuard) between the
  UM790 (`100.68.180.69`) and Torre (`100.91.154.124`),
  host-scoped /32 firewall on Torre.
- **Wake-on-LAN:** still the intended power-management
  trigger (owned by Home Assistant); design deferred, not
  yet configured.

Goal:

```text
Heavy AI on demand
Infrastructure always available
```

---

# Current Phase

```text
Phase A       Completed
Phase B       Completed
Phase C       Completed
Phase D-1     Completed (voice — closed 2026-06-18)
Phase RTX-1   Closed (GPU node + endpoint swap — 2026-06-27)
Phase E       In progress (Knowledge Platform Foundation — E-0 closed 2026-06-27)
```

Current objective:

```text
Knowledge Platform Foundation (Phase E) — stabilise the knowledge platform (E-1 in progress)
```

See [`../00_overview/ROADMAP.md`](../00_overview/ROADMAP.md)
for the authoritative phase ledger.

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
