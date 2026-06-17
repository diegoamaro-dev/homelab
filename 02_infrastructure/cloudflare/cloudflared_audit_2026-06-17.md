# Cloudflared — read-only audit (2026-06-17) — DRAFT

> **DRAFT.** Read-only audit captured during the Cloudflare zone
> migration for `amarolab.es`. **No changes were made to the
> container, the tunnel, the ingress rules, the DNS records, or any
> Cloudflare account state.** This document records the audit
> findings and the gaps that the post-activation migration will
> need to close.

- **Date:** 2026-06-17
- **Scope:** Existing `cloudflared` container on the UM790 — image,
  network, environment, log signature, tunnel UUID, ingress rules,
  reachable origins.
- **Result (one-line):** The existing Cloudflare Tunnel is a
  **token-managed Guardian Cloud tunnel**. **Zero Amarolab
  hostnames** are bound to it. The container is healthy with 4
  registered edge connections; the cloudflared binary is **one
  minor version behind upstream**. The container sits on its **own
  Docker network** (`cloudflare-net`) and currently has **no path**
  to `homeassistant`, `openwebui`, `qdrant`, or any other container
  on `ai-local_default`.

---

## 1. Container — identity and runtime

| Field | Value |
|---|---|
| Container name | `cloudflared` |
| Image | `cloudflare/cloudflared:latest` |
| Running binary version | `2026.3.0` (Checksum `4f15721f176cd8f6a9cfed7390d0b713538c829995923eda49fa82c7c974f403`) |
| Cloudflare upstream warning | `Your version 2026.3.0 is outdated. We recommend upgrading it to 2026.6.0` (observed in container log 2026-06-16T20:14:03Z) |
| Uptime at audit time | ~17 hours |
| Restart policy | (inherited from `docker-compose.yml` — to be re-verified before any tunnel work) |
| Bind mounts | **none** |
| Authentication mode | `TUNNEL_TOKEN=*****` (single env var; no `config.yml`, no `cert.pem`) |
| Process flags from log | `Settings: map[no-autoupdate:true p:http2 protocol:http2]` |

Implication of "token-managed, no `config.yml`": ingress is
configured **centrally** in the Cloudflare Zero Trust dashboard;
it is **not** local to the container and is **not** version-controlled
in the repository.

The "no-autoupdate: true" setting means the version warning will
**not** auto-resolve. A version bump is a documented future step,
not part of this audit.

---

## 2. Tunnel identity

| Field | Value |
|---|---|
| Tunnel UUID | `1a0df79d-18f0-4fd0-ba16-e51739a54c30` |
| Latest connector ID | `b00babec-6ee5-4e70-90b9-d6448866e9c6` (started 2026-06-17T00:19:32Z) |
| Registered edge connections | 4 / 4 (connIndex 0–3, all `protocol=http2`, locations `lhr*`) |
| Tunnel health | Healthy — log shows occasional `Lost connection with the edge` / `connection with edge closed` followed by `Retrying connection` and a successful `Registered tunnel connection`. This is normal edge churn, not a fault. |

**Cross-reference to existing security docs.** The same tunnel UUID
is referenced (redacted) in
[`../../06_security/exposed-ports.md`](../../06_security/exposed-ports.md)
§"External exposure path (Cloudflare tunnel)" and is the same
tunnel flagged by **R-01** in
[`../../06_security/security-risks-2026-06-13.md`](../../06_security/security-risks-2026-06-13.md)
— the TUNNEL_TOKEN was committed to a `docker-compose.yml` in
plaintext and has not yet been rotated.

---

## 3. Ingress configuration (as advertised by the dashboard)

The container log line at 2026-06-17T00:19:33Z
(`Updated to new configuration config="{…}" version=9`) reports the
ingress as:

| # | Hostname | Service | Notes |
|---|---|---|---|
| 1 | `app.guardiancloud.app` | `http://guardian-web:80` | Resolved via `cloudflare-net` Docker DNS — the `guardian-web` container is on the same bridge |
| 2 | `api.guardiancloud.app` | `http://192.168.178.79:3001` | Resolved via the LAN — the host IP of the UM790 |
| 3 | *(catch-all)* | `http_status:404` | Default Cloudflared catch-all |
| | `warp-routing` | `enabled: false` | |

Configuration version observed: `version=9`.

### 3.1 Observations on the ingress

- **Amarolab hostnames are absent.** Neither `ha.amarolab.es` nor
  `ai.amarolab.es` (nor any other `*.amarolab.es`) is in the
  ingress. The existing tunnel is **Guardian-Cloud-only**.
- The `api.guardiancloud.app` entry resolves to a **host IP**
  (`192.168.178.79:3001`) rather than a Docker hostname. This is a
  pre-existing arrangement; it is **not** the model the Amarolab
  hostnames will use (those should resolve to Docker container
  names on the same Docker network as `cloudflared`, to avoid the
  host-port surface).
- The catch-all returns `http_status:404`, so any unknown hostname
  routed to this tunnel ID will refuse cleanly rather than leak.

---

## 4. Docker networking — current path from the tunnel to upstreams

| Network | Driver | Subnet | Members (relevant) |
|---|---|---|---|
| `cloudflare-net` | bridge | `172.24.0.0/16` (gw `172.24.0.1`) | `cloudflared` (172.24.0.3), `guardian-web` |
| `ai-local_default` | bridge | (separate) | `openwebui`, `ollama`, `qdrant`, `aurora-whisper`, `aurora-piper`, `aurora-wakeword` |
| `zigbee-stack_default` | bridge | (separate) | `mosquitto`, `zigbee2mqtt` |
| `cloudflared_default` | bridge | (separate) | *empty — dead bridge* |
| `html_default` | bridge | (separate) | *empty — dead bridge* |
| `proxy_default` | bridge | (separate) | `nginx-proxy-manager` |
| `homeassistant` (container) | — | host network | bound directly on the host network stack |

This matches what is already documented in
[`../docker-networks.md`](../docker-networks.md).

### 4.1 Origin-reachability matrix (current)

| Origin we will want to expose | Container | Network | Reachable from `cloudflared` today |
|---|---|---|---|
| Home Assistant (target `ha.amarolab.es`) | `homeassistant` | host network | **Yes**, via the host IP (e.g., `http://192.168.178.79:8123`) — same pattern as `api.guardiancloud.app` |
| Open WebUI (target `ai.amarolab.es`) | `openwebui` | `ai-local_default` | **No** by Docker DNS — `cloudflared` is not on `ai-local_default`. Either (a) attach `cloudflared` to `ai-local_default` as a second network, **or** (b) route through the host IP `http://192.168.178.79:3000`. |
| Qdrant (target `qdrant.amarolab.es`, reserved) | `qdrant` | `ai-local_default` | Same as Open WebUI |
| Docs (target `docs.amarolab.es`, reserved) | TBD | TBD | TBD |
| Status (target `status.amarolab.es`, reserved) | TBD | TBD | TBD |

The preferred long-term posture (per Lesson 011 — "simplicity
scales") is option (a): add `cloudflared` to `ai-local_default` so
all upstreams resolve by Docker container name. This avoids
publishing host ports for the Amarolab services and keeps the
ingress free of LAN IPs.

This is a **planning note only**. **No Docker network changes were
made.**

---

## 5. Log signature — last ~24 hours

Sampled from `docker logs --tail 100 cloudflared`:

- 2026-06-14T19:03Z — brief edge churn; all four connections
  re-registered within 1 s.
- 2026-06-14T20:42Z — full restart (`Starting tunnel
  tunnelID=1a0df79d-…`); all four connections registered cleanly.
- 2026-06-14T23:04Z — another full restart; same pattern.
- 2026-06-15T19:00Z — single edge churn on connIndex 1 and 3; both
  recovered within ~20 s.
- 2026-06-15T20:14Z — another full restart; clean.
- 2026-06-16T00:21Z — single edge churn on connIndex 0; recovered
  within 4 s.
- 2026-06-16T20:14Z — upstream version warning logged.
- 2026-06-17T00:19Z — current restart; **all 4 connections still
  registered at audit time**, no errors since.

No `ERR` lines unrelated to expected edge churn. No `panic`,
`fatal`, or origin-unreachable errors.

---

## 6. Findings summary

| # | Finding | Severity | Action |
|---|---|---|---|
| F-1 | Existing tunnel is Guardian-Cloud-only. No Amarolab hostnames are configured. | informational | Plan ingress additions for `ha.` and `ai.` (post-zone-activation, in [`./amarolab_dns_architecture.md`](./amarolab_dns_architecture.md)) |
| F-2 | `cloudflared` is **not** on `ai-local_default`. It cannot reach `openwebui`, `qdrant`, or the Aurora voice containers by Docker DNS today. | medium (will block `ai.amarolab.es` ingress) | Decision item: attach `cloudflared` to `ai-local_default` **vs** route via host IP. Decision deferred — captured in [`./amarolab_dns_architecture.md`](./amarolab_dns_architecture.md). |
| F-3 | Container running `cloudflared 2026.3.0`; Cloudflare recommends `2026.6.0`. `no-autoupdate: true` means this will not self-resolve. | low (operational) | Schedule a version bump **after** the migration lands, so config and binary are not changed in the same window. |
| F-4 | Tunnel is token-authenticated; ingress is **dashboard-managed**. There is no `config.yml` in the repo or on the host to version-control. | informational | Out of scope for this audit. Long-term, consider documenting the dashboard ingress in a versioned snapshot file under `02_infrastructure/cloudflare/`. |
| F-5 | The same tunnel token is the one referenced by **R-01** in `06_security/security-risks-2026-06-13.md`. It is still pending rotation. | high (pre-existing) | R-01 remains the open security item. Sequence: zone activates → ingress migration → token rotation in the same maintenance window, **not** before. |
| F-6 | `api.guardiancloud.app` ingress points to a host IP (`192.168.178.79:3001`) rather than a Docker hostname. This is pre-existing. | informational | Not changed by this audit. Out of scope for the Amarolab migration. |
| F-7 | `cloudflared_default` and `html_default` are empty dead bridges (matches `02_infrastructure/docker-networks.md`). | low (housekeeping) | Out of scope. |

---

## 7. What this audit did NOT do

- Did **not** modify the `cloudflared` container.
- Did **not** modify the Cloudflare Zero Trust dashboard
  (ingress, public hostname mappings, access policies — none
  touched).
- Did **not** modify Cloudflare DNS (no records created or
  changed).
- Did **not** rotate the tunnel token (R-01 still open).
- Did **not** modify any Docker network.
- Did **not** modify Home Assistant, Open WebUI, Qdrant, or any
  Aurora voice container.
- Did **not** print the value of `TUNNEL_TOKEN`. The env var is
  recorded as `*****` everywhere.

---

## 8. Related documents

- [`./amarolab_dns_architecture.md`](./amarolab_dns_architecture.md)
  — target DNS / ingress architecture (DRAFT, alongside this
  audit).
- [`../docker-networks.md`](../docker-networks.md) — existing
  network inventory.
- [`../../06_security/exposed-ports.md`](../../06_security/exposed-ports.md)
  — exposure surface, including the tunnel.
- [`../../06_security/security-risks-2026-06-13.md`](../../06_security/security-risks-2026-06-13.md)
  — R-01 tunnel token rotation.
