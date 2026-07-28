# Security Posture

Last updated: 2026-07-28 (**S-1 — LAN trust posture decided.** *Network Security →
Internal Network* previously recorded `Trusted LAN` as an inherited assumption; it is now
a dated operator decision with an explicit minimum bar. The threat model and the pending
list are reconciled to that decision. No other section was reconciled in this change.)

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
* **A hostile device already present on the LAN** — excluded by the **S-1** decision below
  (*Network Security → Internal Network*), deliberately and not by oversight. The LAN is
  trusted as a *transport*; the minimum bar exists precisely so that this exclusion can
  never become the justification for an unauthenticated service.

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

### Decision — S-1, ratified 2026-07-28

```text
The LAN is a trusted transport.
It is never a substitute for service authentication.
Every LAN-reachable service must either:
- authenticate,
- be explicitly justified,
- or remain closed.
```

This supersedes the previous entry, which recorded `Trusted LAN` as an inherited posture —
a *trust statement* that had never been taken as a *decision*. Origin: finding **H-8** of
the 2026-07-28 infrastructure audit. Decision record:
[`../09_logs/2026-07-28_S1_lan_trust_posture_decision.md`](../09_logs/2026-07-28_S1_lan_trust_posture_decision.md).

**What it means.** AMAROLAB is a single-user, single-host platform on a home LAN behind a
FRITZ!Box, with no public administrative path. Treating that LAN as a trusted transport is
proportionate to the threat model above. The decision makes the posture explicit so that it
is a **choice**, reviewable and dated, rather than a default nobody took.

**What it does not mean.** It grants no service the right to be unauthenticated. The
minimum bar is the operative half of the decision: **trust in the transport never
substitutes for authentication at the service.** A LAN-reachable listener that neither
authenticates nor carries a written justification is a defect, and is closed.

**This is not segmentation.** VLAN separation of user / IoT / server / guest devices is a
**decided non-goal at the current scale** — not a pending task, and it is no longer listed
as one. It returns as an open question only if the LAN stops being effectively
single-user: guest access, or untrusted IoT that cannot sit behind the existing Zigbee
boundary.

### Enforcement state

No host firewall is enforcing. `/etc/ufw/ufw.conf` carries `ENABLED=no`; the `ufw` unit is
`active` and `enabled` but installs no rules. **This is consistent with the decision** —
under S-1 the LAN is trusted, so the control that matters is authentication at each
service, not packet filtering at the host.

**Verification limit, stated in place.** `iptables -S` and `nft list ruleset` both return
*permission denied* without passwordless sudo, so the *effective* filter state has never
been read directly — by this document or by the 2026-07-28 audit. Enforcement claims here
are derived from `ufw.conf` plus observed reachability, and any future change to filtering
must be verified by the operator with root.

**A closure caveat that matters.** Eight LAN-exposed ports are **Docker-published**
(`0.0.0.0:…->…`): 3000, 6333, 8085, 1883, 80/81/443, 11434, 8000/9443. Docker installs its
own `nat`/`DOCKER` rules, so **enabling UFW would not close them**. Closing a Docker-published
port means changing its publish binding (e.g. `127.0.0.1:11434`) or adding a `DOCKER-USER`
rule — never `ufw enable` alone. Recorded as a known Docker property; not verified against
this host's ruleset, for the reason above.

### Conformance against the bar — measured 2026-07-28

| Port | Service | Bar met by | Status |
|---|---|---|---|
| 22 | SSH | authenticates | **conditional** — `PasswordAuthentication` is unset in `sshd_config` / `sshd_config.d/`, so the OpenSSH default `yes` applies (**M-9 → S-5**) |
| 80 / 81 / 443 | Nginx Proxy Manager | admin account | conforms |
| 139 / 445 | Samba `[projects]` | `valid users = smbuser` | conforms |
| 1883 | Mosquitto | authentication + per-user ACLs (hardened 2026-06-17) | conforms |
| 3000 | Open WebUI | app login | conforms |
| 6333 | Qdrant | API key — verified `HTTP 401` | conforms |
| 8000 / 9443 | Portainer | app login | conforms |
| 8085 / 3001 | Guardian Cloud web / backend | production project, hosted; out of AMAROLAB scope | justified |
| 8088 | Apache WebDAV | Basic auth — verified `HTTP 401` | conforms |
| 8123 | Home Assistant | app login | conforms |
| **11434** | **Ollama** | — | **FAILS** — unauthenticated; `HTTP 200` on `/api/tags` from the LAN address (**H-5 → S-2**) |
| **5050** | **homelab-tools** | — | **FAILS** — unauthenticated Flask dev server serving Docker logs; contradicts D-18 (**H-6 → S-3**) |
| **111** | **rpcbind** (tcp+udp, IPv4+IPv6) | — | **FAILS** — no `/etc/exports`, `nfs-server` inactive: a portmapper with no NFS behind it (**F-S1-1**) |
| **18555** | **unattributed** | — | **FAILS** — LAN-reachable; the process cannot be attributed without root (**F-S1-2**) |

Loopback-bound services (`10200`, `10300`, `10400` Wyoming voice chain; `11435`
`ollama-proxy`; `631` CUPS) are outside the bar by construction — they are not
LAN-reachable.

**Four listeners fail the bar as of 2026-07-28.** Two were already tracked (H-5 → S-2,
H-6 → S-3). Two are new, found by this decision's own audit, and are recorded as findings
**F-S1-1** and **F-S1-2** in the decision record — **deliberately unimplemented here**, on
the R-I3-1…7 precedent. S-1 decides the posture; it changes no running service.

### Backup adjacency — recorded at S-1

The restic repository directory `/mnt/storage/backups/restic` is `root`-owned, mode `0700`
— its contents are not readable or writable by `smbuser` or the `shared` group. Its
**parent** `/mnt/storage/backups` is `smbuser`-owned, group-writable, and carries **no
sticky bit**, so the `restic` directory entry itself can be renamed or unlinked by
`smbuser` or any member of `shared`. That parent is on the same filesystem (`/dev/sda1`) as
the LAN-writable Samba share `[projects]`.

**Not demonstrated:** that the `[projects]` share reaches outside `/mnt/storage/projects`.
As configured it does not — the share path is scoped and `wide links` is not set. The
exposure is therefore **conditional**, requiring a second share, a configuration change, or
a compromised `smbuser` process.

It is recorded because it sets the stakes of trusting the LAN: the platform's **sole**
backup repository — single copy, and per I-4 never pruned — sits one directory-entry
permission away from a LAN-facing file service. Remediation is not assigned here.

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
LAN trust posture decided + documented (S-1, 2026-07-28)
```

Pending:

```text
Cloudflare Tunnel token rotation
Dedicated NAS deployment
Secondary backup location
Hardware-backed authentication
```

Pending against the S-1 minimum bar (four non-conforming listeners):

```text
Ollama unauthenticated on the LAN            (H-5 -> S-2)
homelab-tools unauthenticated on the LAN     (H-6 -> S-3)
SSH password authentication enabled          (M-9 -> S-5)
rpcbind + one unattributed listener          (F-S1-1, F-S1-2 — no item assigned)
```

`Additional network segmentation` was removed from this list at S-1: it is now a **decided
non-goal at the current scale**, not pending work. See *Network Security → Internal
Network*.

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
