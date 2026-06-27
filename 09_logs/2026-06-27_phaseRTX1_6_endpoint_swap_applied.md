# Phase RTX-1.6 — UM790 ollama Endpoint Swap (Torre primary + UM790 fallback) — APPLIED

- **Date:** 2026-06-27
- **Phase step:** RTX-1.6 — point the UM790 AI front doors at Torre's GPU Ollama, via a failover proxy, with the UM790 CPU Ollama as automatic fallback.
- **Ecosystem:** AMAROLAB — Personal Innovation Lab and Digital Infrastructure Ecosystem.
- **Assistant:** AURORA — Personal AI Assistant for the AMAROLAB ecosystem.
- **Independent project:** Guardian Cloud — **untouched** (verified; `cloudflared` + `guardian-web` up throughout, no config change).
- **Status:** **APPLIED.** All gates PASS. Both front doors (Open WebUI chat + Home Assistant voice/LLM) now consume Torre's RTX 5070 Ollama through the `ollama-proxy`, with transparent fallback to the UM790 CPU Ollama. Gated on the security delta doc [`../06_security/rtx_node_security.md`](../06_security/rtx_node_security.md) (RTX-1.6 Step 1, approved 2026-06-27).
- **Scope:** UM790-side only — one new internal proxy container + two consumer repoints. **No Torre change** (RTX-1.4/1.5 posture preserved). No Guardian Cloud / Cloudflare / Mosquitto / Z2M / Qdrant change.

---

## 1. Context

RTX-1.4 (Tailscale-only exposure) and RTX-1.5 (headless NSSM service) left Torre
serving `qwen2.5:7b-instruct` on the RTX 5070 at ~105 tok/s, reachable from the
UM790 over Tailscale but **not yet consumed**. Both UM790 front doors still ran
inference on the local CPU Ollama (~6 tok/s):

- Open WebUI → `http://ollama:11434` (env `OLLAMA_BASE_URL`; `webui.db` had no
  ollama block, so env was authoritative).
- Home Assistant (host-network) → `http://127.0.0.1:11434` (ollama config entry
  `01KVB08CQ2WTFA4MQ7FTF0NXVZ`).

Torre is an **on-demand** node (not 24/7), so a naive repoint straight at Torre
would break inference whenever Torre sleeps. RTX-1.6 therefore introduces a
failover front end so the primary→fallback decision is automatic and
consumer-agnostic.

## 2. Objective

Make Torre the **primary** inference path for both front doors, with the UM790
CPU Ollama as **automatic fallback**, changing only the endpoint each consumer
targets. Keep rollback trivial. Touch no Torre, Guardian Cloud, or unrelated
production config.

## 3. Decisions

- **D-RTX-1.6-A — Failover proxy (operator-selected).** A small `nginx:alpine`
  container (`ollama-proxy`) presents one stable internal endpoint and upstreams
  `Torre (primary)` + `UM790 (backup)`. Both Open WebUI and Home Assistant point
  at the proxy, **never** at Torre directly. Rationale: Open WebUI's multi-URL
  feature load-balances (no priority) and HA's Ollama integration is
  single-endpoint with no native fallback — only a proxy gives true automatic
  primary→fallback for **both** consumers.
- **D-RTX-1.6-B — Self-contained, repo-tracked.** The proxy is its own compose
  project under [`../03_services/ollama-proxy/`](../03_services/ollama-proxy/)
  (`docker-compose.yml` + `nginx.conf`), deployed directly (not via Portainer),
  touching no existing service definition. Addresses R-14 for this component.
- **D-RTX-1.6-C — Loopback publish for HA.** The proxy publishes
  `127.0.0.1:11435` (loopback only) for the host-network HA; Open WebUI reaches
  it over the docker network as `ollama-proxy:11434`. No LAN/tailnet exposure of
  the proxy port.
- **D-RTX-1.6-D — nginx failover semantics.** `upstream` with Torre primary
  (`max_fails=1 fail_timeout=10s`) + `server ollama:11434 backup`;
  `proxy_next_upstream … non_idempotent` so POST (`/api/chat`, `/api/generate`)
  fails over on connection error; `proxy_buffering off` to preserve token
  streaming; `proxy_connect_timeout 5s` for fast failover; `proxy_read_timeout
  900s` for slow CPU-fallback generations.

## 4. Implementation

All steps on the UM790. Read-only baseline first (per project discipline).

- **Baseline (read-only).** Confirmed the real stack (16 containers), Torre
  active on Tailscale (`100.91.154.124`), both nodes serving the identical
  `qwen2.5:7b-instruct` (digest `845dbda0ea48…`), and the exact current
  endpoints (above). Full pre-change rollback record captured
  (`openwebui` inspect, HA `core.config_entries`).
- **Step 1 — Proxy build + isolation validation.** Created
  `03_services/ollama-proxy/{docker-compose.yml,nginx.conf}`; `docker compose up
  -d`. Validated **in isolation** (no consumer repointed): health, primary→Torre
  (proxy access log `upstream=100.91.154.124:11434`), reachable from both the
  host (`127.0.0.1:11435`) and a bridge consumer (`ollama-proxy:11434`), and
  **failover** (temporary dead primary → served by `ollama:11434` backup, proxy
  log `upstream=…11999, 172.18.0.6:11434`).
- **Step 2 — Open WebUI repoint.** `webui.db` had no ollama block, so env was
  authoritative → changed `OLLAMA_BASE_URL=http://ollama-proxy:11434` and
  **recreated** the container (Lesson 001). Reproduced faithfully from the
  captured inspect: both networks (`ai-local_default` + `proxy_default`), port
  `3000:8080`, both volumes, restart policy, full env (only the one value
  changed). Validated: app-level `/ollama/*` calls appear in the proxy log from
  Open WebUI (`172.18.0.10`) served by Torre.
- **Step 3 — Home Assistant repoint.** Backed up `core.config_entries`; with HA
  **stopped**, edited ollama entry `01KVB08CQ2WTFA4MQ7FTF0NXVZ`
  `url: http://127.0.0.1:11434 → http://127.0.0.1:11435` (and its display
  `title`) via a transient `--volumes-from` helper (runs as root; no live
  overwrite risk); validated JSON; started HA.

## 5. Validation gates

| Gate | Result | Evidence |
|---|---|---|
| **G-1.6-1 Proxy primary** | PASS | Isolation: every request `upstream=100.91.154.124:11434` (Torre); reachable host + docker-net |
| **G-1.6-2 Proxy fallback** | PASS | Dead-primary test: served by `172.18.0.6:11434` (UM790); log `upstream=…11999, 172.18.0.6:11434` |
| **G-1.6-3 Open WebUI → Torre** | PASS | `OLLAMA_BASE_URL=http://ollama-proxy:11434`; app `/ollama/api/*` from `172.18.0.10` → Torre in proxy log |
| **G-1.6-4 HA → Torre** | PASS | Entry url `…:11435`; `conversation.ollama_conversation` reply `HA-PROXY-OK`; proxy log `POST /api/chat → Torre` |
| **G-1.6-5 Tools** | PASS | `/api/chat` with a tool def via proxy → `tool_calls:[get_weather{city:Paris}]` |
| **G-1.6-6 Performance** | PASS | **101.3 tok/s** via proxy→Torre; HA conversation **24.1 s (CPU) → 3.9 s (Torre)** |
| **G-1.6-7 GPU offload** | PASS | Torre `/api/ps` `size_vram == size` (full GPU) during live inference |
| **G-1.6-8 RAG** | PASS | Qdrant collections present (`homelab_docs`, `guardian_cloud`, `ensambla2`, `infra_audits`, …); `rag_search` tool intact |
| **G-1.6-9 Voice wiring** | PASS | Assist pipeline `Aurora v1` → `conversation.ollama_conversation` (→ Torre); `stt.faster_whisper` / `tts.piper` unchanged |
| **G-1.6-10 Live fallback** | PASS | With Torre down, live HA reply `HA-FALLBACK-OK` (16.9 s, CPU) via UM790; proxy log shows the failover |
| **G-1.6-11 Production integrity** | PASS | 17 containers up; Guardian Cloud (`cloudflared`, `guardian-web`) untouched; Mosquitto/Z2M/Qdrant/Cloudflare unchanged |

> Voice scope note: RTX-1.6 changes only the LLM endpoint. The voice pipeline's
> brain (`conversation.ollama_conversation`) is validated against Torre; STT/TTS
> are unchanged. Full mic-to-speaker acceptance remains an operator check.

## 6. Rollback

Trivial and fully reversible on the UM790 (no Torre/off-box change):

```text
# Home Assistant -> back to UM790 CPU
docker stop homeassistant
docker run --rm --volumes-from homeassistant nginx:alpine \
  sed -i 's#http://127.0.0.1:11435#http://127.0.0.1:11434#g' /config/.storage/core.config_entries
docker start homeassistant
# (or restore core.config_entries.rtx16-bak-<ts>)

# Open WebUI -> back to UM790 CPU (env change => recreate)
#   set OLLAMA_BASE_URL=http://ollama:11434 and recreate from the captured inspect

# Remove the proxy
docker compose -f 03_services/ollama-proxy/docker-compose.yml down
```

End state of rollback = the pre-RTX-1.6 baseline (both front doors on
`ollama:11434` / `127.0.0.1:11434`, UM790 CPU).

## 7. Final state

| Item | State |
|---|---|
| `ollama-proxy` | `nginx:alpine`, on `ai-local_default`, published `127.0.0.1:11435` (loopback), healthy |
| Upstreams | Torre `100.91.154.124:11434` (primary) · `ollama:11434` (UM790 CPU, backup) |
| Open WebUI | `OLLAMA_BASE_URL=http://ollama-proxy:11434` (recreated; both networks/volumes preserved) |
| Home Assistant | ollama entry url `http://127.0.0.1:11435` |
| Inference | Torre GPU when up (~101 tok/s, full offload); UM790 CPU fallback when Torre down |
| Torre | unchanged (RTX-1.4 firewall `/32` + RTX-1.5 NSSM service) |

## 8. Security notes

- **New internal service, not exposed.** The proxy port is published on
  **loopback only** (`127.0.0.1:11435`); Open WebUI reaches it over the docker
  network. No LAN/tailnet/public exposure added.
- **New single point of failure.** The proxy now fronts both front doors; if it
  is down, inference is unavailable until it restarts (`restart: unless-stopped`
  + healthcheck) or rollback. Accepted by design (operator-selected); the UM790
  backup means a *Torre* outage does **not** break inference, only a *proxy*
  outage does.
- **Torre boundary preserved.** Proxy→Torre traffic egresses as the UM790's
  Tailscale IP, matching Torre's host-scoped `/32` allow (RTX-1.4). No Torre-side
  change. See [`../06_security/rtx_node_security.md`](../06_security/rtx_node_security.md).
- **No secrets** introduced, printed, or committed. Private LAN (`192.168.178.x`)
  and Tailscale (`100.x`) addresses appear as operational detail, per the
  repo-wide IP-hygiene follow-up in the ROADMAP.

## 9. Operational lesson (candidate)

- **L-RTX-5 (candidate):** a Docker **single-file bind mount** does not track
  host-side inode replacement — editing `nginx.conf` on the host and running
  `nginx -s reload` kept serving the **old** config (the container still saw the
  original inode). Config changes to a bind-mounted file require a container
  **recreate** (`compose up --force-recreate`), not a reload. Echoes Lesson 001
  (env) and L-RTX-1 (server env): the running process keeps what it was started
  with. Discovered during the failover test; the test was redone correctly via
  recreate.

## 10. Next steps

- Documentation merge (this closeout): `00_overview/CURRENT_STATE.md`,
  `00_overview/ROADMAP.md`, `06_security/security_posture.md`, and
  `01_architecture/amarolab_architecture.md` (merge the RTX amendment DRAFT) —
  all updated at RTX-1.6 per the roadmap.
- Optional: add L-RTX-5 to `07_operations/lessons_learned.md`.
- Carried (unchanged): R-01 Cloudflare tunnel rotation; repo-wide IP-hygiene
  decision; `cloudflared-amarolab` standalone apply log.
