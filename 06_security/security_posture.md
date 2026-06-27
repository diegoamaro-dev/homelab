# Security Posture

Last updated: 2026-06-27

---

# Purpose

This document defines the current security posture of Amarolab.

It serves as the authoritative reference for security-related decisions, controls, protections, risks and future improvements.

This document intentionally describes architecture and policies without exposing operational secrets.

---

# Security Philosophy

Amarolab follows a practical security model:

```text
Security
    >
Convenience
```

The goal is not maximum complexity.

The goal is:

* Reasonable risk reduction
* Recoverability
* Operational simplicity
* Protection against common failures
* Protection against accidental exposure

---

# Threat Model

Primary threats:

* Credential leakage
* Unauthorized remote access
* Misconfigured services
* Accidental exposure of secrets
* Data loss
* Hardware failure
* Documentation leaks
* Configuration drift

Not currently considered:

* Nation-state actors
* Advanced persistent threats
* Physical datacenter attacks

---

# Access Control

## Remote Access

Current approved methods:

```text
VPN
SSH
```

Administrative access is performed through:

```text
VPN
    ↓
SSH
    ↓
Server
```

No direct administrative services are intentionally exposed to the public Internet.

---

## SSH

Status:

```text
Enabled
Operational
```

Principles:

* SSH is the primary administration method.
* Access is restricted to authorized users.
* SSH keys preferred over passwords whenever possible.

Future improvements:

* Hardware-backed SSH keys
* Additional hardening
* Audit review

---

# Network Security

## Router

Current router:

```text
FRITZ!Box 5690 Pro
```

Responsibilities:

* Internet edge
* Internal routing
* VPN services
* Basic firewalling

---

## Internal Network

Current posture:

```text
Trusted LAN
```

Future posture:

```text
User devices
IoT devices
Servers
Guest network
```

Segmentation will be increased over time.

---

# Docker Security

Principles:

* Services isolated through containers.
* Data persisted through mounted volumes.
* Configuration stored separately from code.

Operational rule:

```text
Never assume a container restart reloads environment variables.
```

If environment variables change:

```text
Update configuration
Recreate container
Validate environment
Continue troubleshooting
```

Reference:

```text
07_operations/docker/docker_env_reload_behavior.md
```

---

# Home Assistant Security

Status:

```text
Operational
Validated
```

Capabilities currently exposed to AI:

```text
ha_get_state
ha_call_service
```

Protection mechanisms:

* Domain allowlist
* Tool-level validation
* Audit logging
* Explicit refusal paths

Denied domains:

```text
homeassistant.*
hassio.*
recorder.*
```

---

# MQTT Security

Status:

```text
Hardened
```

Date:

```text
2026-06-17
```

---

## Authentication

Anonymous access:

```text
Disabled
```

Configuration:

```text
allow_anonymous false
```

Users:

```text
homeassistant
zigbee2mqtt
```

---

## Authorization

ACL-based access control:

```text
acl_file
```

Model:

```text
Default Deny
Least Privilege
```

Each service receives only the permissions required for operation.

---

## Secret Storage

Passwords are not stored in Git.

Live credentials are stored outside the repository.

Examples:

```text
MQTT credentials
API tokens
Long-lived access tokens
```

---

# Secrets Management

## Repository Policy

Never commit:

```text
Passwords
API Keys
Tokens
Private Keys
Cookies
Session Data
.env files
```

---

## Documentation Policy

Use placeholders:

```text
${HA_BASE_URL}
${HA_LLAT}
${WEBUI_SECRET_KEY}
${QDRANT_API_KEY}
<TOKEN>
<PASSWORD>
<SECRET>
```

Never publish live values.

---

# AI Security

## Tool Access

Current approved tools:

```text
time_now
rag_search
audit_search
ha_get_state
ha_call_service
```

Tool execution is restricted through:

* Validation
* Allowlists
* Audit logging

---

## Knowledge Base

Current collections:

```text
homelab_docs
guardian_cloud
ensambla2
infra_audits
```

All collections remain local.

No cloud-based vector database is required.

---

# RTX Compute Node (Torre)

Status:

```text
Operational (RTX-1 closed 2026-06-27)
```

Torre is an on-demand GPU compute node. Its full security
architecture is the authoritative companion document:

```text
06_security/rtx_node_security.md
```

Summary of controls (deployed):

```text
Tailscale-only access      (encrypted transport + tailnet identity)
Host-scoped /32 firewall   (allow UM790 only; LAN blocked; default-deny)
Headless NSSM service      (OllamaService, LocalSystem, Automatic)
NSSM binary ACL-hardened   (no Authenticated Users modify)
No public path             (NAT, no port-forward, no tunnel on Torre)
```

Network-layer is the only access control: Ollama itself is
unauthenticated, so the boundary is the host firewall plus
Tailscale. Acceptable for a single-user, Tailscale-only
posture. See `rtx_node_security.md` for trust boundaries,
accepted/mitigated risks, recovery, and rollback.

---

## ollama-proxy (RTX-1.6 endpoint swap)

Status:

```text
Operational (2026-06-27)
```

A failover front end (`nginx:alpine`) presents one internal
endpoint and routes:

```text
primary  -> Torre  (RTX 5070 GPU, over Tailscale)
fallback -> UM790  (local CPU Ollama) when Torre is unreachable
```

Security properties:

```text
Published on loopback only (127.0.0.1:11435) for Home Assistant.
Open WebUI reaches it over the docker network (ollama-proxy:11434).
No LAN / tailnet / public exposure of the proxy port.
No new secrets.
```

Accepted risk:

```text
The proxy is a single point of failure in front of both
front doors. restart=unless-stopped + healthcheck. A Torre
outage fails over to the UM790; only a proxy outage stops
inference (rollback = repoint consumers to ollama:11434).
```

Reference:

```text
03_services/ollama-proxy/
09_logs/2026-06-27_phaseRTX1_6_endpoint_swap_applied.md
```

---

# Data Protection

## Backups

Current system:

```text
Restic
```

Repository location:

```text
2 TB USB Disk
```

Status:

```text
Validated
Operational
```

---

## Recovery Goal

Every critical service should be recoverable from:

```text
Documentation
Backups
Git Repository
Configuration Files
```

---

# Guardian Cloud

Guardian Cloud is considered:

```text
Production
```

Rules:

```text
Do not modify without explicit approval.
Do not perform experimental changes.
Do not break evidence retention guarantees.
```

---

# Current Security Status

Completed:

```text
VPN access
SSH administration
Docker isolation
Home Assistant integration
Tool validation
Audit logging
Restic backups
Mosquitto authentication
Mosquitto ACLs
Secret sanitisation
Git hygiene
RTX node Tailscale-only exposure (host-scoped /32)
RTX node headless service + ACL hardening
ollama-proxy failover (Torre primary + UM790 fallback)
```

Pending:

```text
Cloudflare Tunnel token rotation
Dedicated NAS deployment
Secondary backup location
Additional network segmentation
Hardware-backed authentication
```

---

# Security Principles

1. Security before convenience.
2. Documentation before modification.
3. No secrets in Git.
4. Validate before documenting.
5. Backups before major changes.
6. Production services require explicit approval.
7. Everything must be recoverable.
8. Least privilege by default.
9. Auditability matters.
10. If it is not documented, it does not exist.
