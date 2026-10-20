# 03_services — service definitions

## Status: RECOVERY ARTIFACTS, not the deployment source

The `docker-compose.yml` files in this directory were **captured from the running
system on 2026-07-28** (remediation item I-3). They describe what is deployed. They are
**not** yet the thing that deploys it.

> **Git is not the deployment source of truth for these services.** A future convergence
> project will validate these files and only then will that change.

**Do not run `docker compose up` against any file here.** Two guards make an accidental
run fail rather than damage something, but neither is a substitute for not doing it:

1. Every captured project uses an `amarolab-` prefixed `name:`, which cannot match any
   running container's compose project label. No file here can adopt or recreate a
   running container.
2. Every service sets `container_name`, so an `up` collides on the name and aborts.

Verified 2026-07-28: `docker compose up --dry-run` on all six captured projects reports
`Creating` for every service — i.e. none of them matches anything running.

## Inventory

| File | Services | Live compose project | Notes |
|---|---|---|---|
| `ai-local/` | `openwebui`, `qdrant`, `ollama` | `ollama` only (`ai-local`) | `openwebui`/`qdrant` carry **no** compose labels. See the H-4 hazard |
| `aurora-voice/` | `aurora-whisper`, `-piper`, `-wakeword`, `-whisper-http`, `-piper-http` | none | **`aurora-whisper` must not be recreated** — D-F6-1 |
| `portainer/` | `portainer` | none | `portainer_data` holds the only copies of stacks 1/2/4 |
| `proxy/` | `npm` → `nginx-proxy-manager` | `proxy` | stored definition in `portainer_data`, not read |
| `home-assistant/` | `homeassistant` | `homeassistant` | host network |
| `zigbee-stack/` | `zigbee2mqtt`, `mosquitto` | `zigbee-stack` | file had been missing and was **never** in git history |
| `ollama-proxy/` | `ollama-proxy` | `ollama-proxy` | **pre-existing and authored, not captured** — the intended pattern |

Out of scope for I-3: `guardian-web` (Guardian Cloud is production), `cloudflared`
(plaintext token — S-4 rotation must come first), `cloudflared-amarolab` (already correct).
All three live under `/home/diego/webs/`.

## Hosted services not captured here (recorded 2026-10-20)

These containers postdate I-3 and have **no** file in this directory. They are intentional
(operator-confirmed). Their absence from this inventory was documentation drift
(`../09_logs/2026-10-20_operational_drift_reconciliation.md` §3–§5). Listing them here does
**not** make this directory their deployment source.

| Container | Purpose | Deployment definition | Notes |
|---|---|---|---|
| `amarolab-portfolio` | Amarolab company website (`amarolab.es`) — production | **Not found.** The compose label names `/home/diego/webs/amarolab-portfolio/docker-compose.yml`, which does not exist | `nginx:alpine`, read-only content bind from `/home/diego/webs/amarolab-portfolio`; `ai-local_default` only, no published port; served via `cloudflared-amarolab` |
| QR/NFC application components (observed 2026-10-20: `qr-amarolab`, `qr-public-edge`) | Amarolab QR/NFC application, hosted on the UM790 — **deployment in progress** | The QR project's own repository (`/home/diego/webs/generador-qr`, compose project `generador-qr`) — **authoritative for its topology**; this table does not track its component set | `qr-amarolab` is published on `127.0.0.1:18000` only. `qr.amarolab.es` is **not** published. Production data is **outside** the restic path set |

## Why the files are not directly deployable

Two value classes are redacted for publication, per
[`CAPTURE_CONTRACT.md`](CAPTURE_CONTRACT.md) §3:

- **secret env values** → `<REDACTED:sha256:…:len=N>`
- **the Zigbee dongle host path** → `<DEVICE_ID>`

Both must be substituted before any deployment. Choosing how is deliberately **not** part
of I-3 — it is queued as R-I3-2 and R-I3-5.

## What "matches reality" means

[`CAPTURE_CONTRACT.md`](CAPTURE_CONTRACT.md) defines the field set, the method (image-default
differencing), and what is excluded and why. Parity evidence for every field:
[`../09_logs/2026-07-28_I3_declarative_substrate_capture.md`](../09_logs/2026-07-28_I3_declarative_substrate_capture.md).

## Networks

All four networks are referenced `external: true` with an explicit `name:`, so no project
name determines a network name. Their subnets are **auto-assigned by creation order** and
are not pinned anywhere:

| Network | Subnet | Depended on by |
|---|---|---|
| `bridge` | 172.17.0.0/16 | Docker default |
| `ai-local_default` | 172.18.0.0/16 | **Home Assistant `trusted_proxies`** |
| `proxy_default` | 172.19.0.0/16 | |
| `zigbee-stack_default` | 172.20.0.0/16 | |

A rebuild that creates these in a different order silently breaks Home Assistant's
reverse-proxy trust while every container reports healthy. Queued as **R-I3-1**.

### Other networks on the engine (observed 2026-10-20 01:04 CEST)

None of these is referenced by a captured file. They are listed because they take part in the
same creation-order assignment:

| Network | Subnet | Members at observation |
|---|---|---|
| `html_default` | 172.21.0.0/16 | none |
| `guardian-cloud_default` | 172.22.0.0/16 | `guardian-web` |
| `cloudflared_default` | 172.23.0.0/16 | none |
| `cloudflare-net` | 172.24.0.0/16 | `cloudflared`, `guardian-web` |
| `voicelab_net` | 172.25.0.0/16 | none |
| `generador-qr_qr-interna` | 172.26.0.0/16 | `qr-amarolab`, `qr-public-edge` |
| `qr-edge` (internal) | 172.27.0.0/16 | `qr-public-edge` |

**Subnets are reused, not only assigned in order.** At 00:30 `172.27.0.0/16` belonged to a
network named `qr-g7_test`. By 01:04 that network was gone and `qr-edge`, created at 01:03, held
the same subnet. This strengthens R-I3-1, which remains recorded and unimplemented.
