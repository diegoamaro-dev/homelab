# 01 — Current state review

Snapshot of the AI stack as of 2026-06-14, after Phase 0 (security
remediation), Phase 1 (RAG foundation), and Phase 1.5 (cross-encoder
reranker). All seven review topics are covered in order.

## 1. Current architecture (ASCII diagram)

```
                          USER  (diego)
                              ┃
                LAN 192.168.178.0/24    Tailnet 100.68.180.69/32
                              ┃
                              ▼
        ┌──────────────────────────────────────────────────────┐
        │  homelab (Ubuntu 24.04, Ryzen 9 7940HS, 30 GiB RAM)  │
        └──────────────────────────────────────────────────────┘
                              │
   ┌──────────────────────────┴──────────────────────────────┐
   │                                                         │
   ▼                                                         ▼
listening on host                                  not exposed on host
:22  sshd                                          (container-internal only)
:3000 openwebui  ──┐                                
:8123 homeassistant│ host network                  
:8080 zigbee2mqtt   │                              
:11434 ollama      │      ┌─────────────────┐
:6333 qdrant       │      │ ai-local_default│
:5050 homelab-tools│      │  172.18.0.0/16  │
       (Flask, host)│      │                 │
:80/443/81 npm     │      │  openwebui      │ ⇄ ollama, qdrant
:8085 guardian-web │      │  ollama         │
:8088 apache wdav  │      │  qdrant         │
:9443/:8000 portainer     │                 │
                          └─────────────────┘
                                            
                          ┌─────────────────┐
                          │ proxy_default   │
                          │  172.19.0.0/16  │
                          │                 │
                          │  npm            │
                          │  portainer      │
                          │  openwebui      │
                          └─────────────────┘
                                            
                          ┌─────────────────┐
                          │ zigbee-stack    │
                          │  172.20.0.0/16  │
                          │                 │
                          │  mosquitto      │
                          │  zigbee2mqtt    │
                          └─────────────────┘
                                            
                          ┌─────────────────┐
                          │ cloudflare-net  │
                          │  172.24.0.0/16  │
                          │                 │
                          │  cloudflared    │
                          │  guardian-web   │
                          └─────────────────┘

Non-container processes:
  - homelab-tools.service  → Flask dev server, 0.0.0.0:5050, no auth
  - pm2-diego              → guardian-cloud-backend Node app, :3001
  - apache2                → :80 (lo only) + :8088 webdav
  - smbd/nmbd              → SMB share /mnt/storage/projects
  - tailscaled (snap)      → tailnet
  - homelab-rag-ingest     → bare-metal Python venv + cron (02:30 daily)
```

**Three "AI stack" components**: openwebui (UI + tool runner), ollama
(LLM), qdrant (vectors). They cross-talk via the user-defined
`ai-local_default` bridge by service-name DNS. The host-published ports
on openwebui (`:3000`) and qdrant (`:6333`), and ollama (`:11434`) are
for *external* / debug access only — Open WebUI calls Ollama and
Qdrant by hostname inside the docker network.

## 2. Data flow today

**Path 1 — Direct chat (what the user gets right now):**

```
user types "hello"
  → openwebui (browser session, webui.db user lookup)
    → POST /api/chat to ollama:11434
      → Ollama loads llama3.2:3b / llama3:8b / phi3 (whichever the user picked)
      → streamed response
    → openwebui renders
```

No tools. No RAG. No Home Assistant. The assistant currently has
nothing to ground on; if asked about the homelab it will hallucinate.

**Path 2 — Nightly ingest (already running):**

```
cron 02:30 (user diego)
  → /home/diego/homelab/ai-stack/ingest/bin/ingest sync
    → for each enabled corpus:
        - git pull --ff-only  (guardian_cloud + ensambla2)
        - walk filesystem with include/exclude rules
        - chunk markdown
        - for each chunk:
            if content_sha already in Qdrant → skip
            else: embed with multilingual-e5-small, upsert
        - garbage-collect points for files no longer on disk
    → logs to /home/diego/homelab/ai-stack/ingest/logs/ingest.log
  → restic at 03:00 picks up the new vector state
```

**Path 3 — Open WebUI ↔ Qdrant (alive but unused):**

Open WebUI's own "Knowledge" feature can already query
`open-webui_knowledge` and `open-webui_files`. It has the
`QDRANT_API_KEY` env it needs. But our four custom corpora
(`homelab_docs`, `guardian_cloud`, `ensambla2`, `myfreetour`) are
**invisible to the chat loop** because no tool/function calls them.

This is the gap v1 closes.

## 3. Resource usage analysis

Idle snapshot (no chat in flight, no ingest running):

| Component | RSS | CPU idle | Disk |
|-----------|---:|---:|---:|
| `openwebui` | 994 MiB | <0.1 % | 903 MB data + ~6.6 GB image |
| `homeassistant` | 494 MiB | <0.1 % | ~12 MB config + 3.3 GB image |
| `qdrant` | 301 MiB | <0.1 % | 2.8 MB storage + 277 MB image |
| `npm` | 181 MiB | <0.1 % | 292 KB data + 1.66 GB image |
| `ollama` | 120 MiB | 0 % (idle; loads model on demand) | 8.3 GB models + 9 GB image |
| `portainer` | 82 MiB | <0.1 % | small + 243 MB image |
| `zigbee2mqtt` | 73 MiB | <0.1 % | small + 223 MB image |
| `mosquitto` | small | <0.1 % | small + 36 MB image |
| `guardian-web` (nginx) | 20 MiB | 0 % | 93 MB image |
| `cloudflared` | 36 MiB | <0.1 % | 96 MB image |
| Host (sshd, apache, samba, snap…) | ~3 GiB | <1 % | n/a |
| `homelab-rag-ingest` venv (on-disk) | — | — | 1.4 GB |
| HF cache (embedding + reranker) | — | — | 3.5 GB |

**Total idle RSS:** ~6 GiB.  
**Host RAM:** 30 GiB — 24 GiB free.  
**Root FS:** 468 GB, 98 GB used (23 %).  
**Bulk HDD (`/mnt/storage`):** 1.8 TB, ~10 GB used.

When the assistant goes live:

| Workload | Adds | Peak RSS |
|----------|-----|---------:|
| Ollama serving qwen2.5:7b-instruct (warm) | +5.5 GiB | ~12 GiB total |
| Reranker loaded in Open WebUI tool process | +600 MiB | ~13 GiB total |
| Burst during embedding+rerank for a single query | <100 MB extra | — |

Headroom: ~17 GiB free at peak. No swap pressure expected.

CPU: 16-thread Zen 4 with AVX-512. Empirical from Phase 1.5:
embedding ~50 ms, Qdrant scroll ~10 ms, reranker top-30 ~120 ms,
Ollama generation ~4–7 tok/s for 7B Q4. A typical end-to-end query
(embed → search → rerank → LLM) lands in ~3–8 seconds for a
500-token answer. Acceptable for chat; not for voice without TTS
latency mitigation (out of scope for v1).

Disk forecast: pulling `qwen2.5:7b-instruct` adds ~4.7 GB to
`/srv/homelab/data/ollama/models`. New `infra_audits` corpus adds
~1 MB to Qdrant. No pressure.

## 4. Bottlenecks

In order of how soon they bite:

| Bottleneck | When it bites | Why |
|------------|---------------|-----|
| **No tool-calling model is loaded** | First time the assistant tries to call a tool | `llama3.2:3b` and `phi3` have weak/no tool support; `llama3:8b` is also weak. Must pull `qwen2.5:7b-instruct` (or `llama3.1:8b-instruct`) before tools can be wired |
| **Single concurrent LLM stream** | Two simultaneous chats | Ollama keeps one model warm at a time on CPU; second user waits for `OLLAMA_KEEP_ALIVE` to kick another out |
| **CPU-only embedding/rerank latency** | Heavy RAG bursts | ~170 ms per query for embed+rerank is fine for chat; for an agent doing 10 RAG calls in a single turn it's 1.7 s before the LLM even starts |
| **`homelab-tools` Flask is a single-threaded dev server** | First time tool fires often | One concurrent request; restart on every code change; binds 0.0.0.0 (R-02 still open). Needs replacement, not just hardening |
| **Qdrant on `0.0.0.0:6333`** | Multiple writers join | Today only the ingest service writes. When the assistant adds conversation memory, the picture muddies. Rebind to `127.0.0.1` (R-07 deferred half) is the right pre-emptive fix |
| **Open WebUI single SQLite file** | High write volume | webui.db is fine for one user; if family/voice ever joins, expect lock contention |
| **No model warm-up on container restart** | After every `docker compose up -d` | First query loads the 5.5 GiB model, takes 15–30 s. Not a perf bottleneck, a UX one |

None of these are blockers for v1; they're future-fingerprints.

## 5. Technical debt

Captured from Phase 0 / 1 / 1.5 follow-ups. Items already known but not
yet acted on:

| ID | Item | Cost to fix | Why pending |
|----|------|------------|-------------|
| R-02 | Flask `homelab-tools` on `0.0.0.0:5050` with no auth | 5 min (rebind) or ~2 h (containerize) | Will be **resolved by v1** via the homelab-tools rewrite — see [02-target-architecture.md](02-target-architecture.md) |
| R-07.2 | Ollama still on `0.0.0.0:11434` unauthenticated | 30 min | Will be addressed as part of v1's container rework |
| R-07.3 | Qdrant still on `0.0.0.0:6333` (key enforced, but port still public) | 30 min | Same window |
| R-09 | `rpcbind` on `:111` | 2 min | Not a v1 blocker; queued |
| R-10 | UFW not enabled | 30 min | Queued; v1 doesn't depend on it |
| R-11 | Container images 3 months stale | 1 h + verify | Queued; will sweep after v1 lands |
| R-13 | Apache default vhost still enabled on `:80` (loopback only) | 2 min | Queued |
| R-14 | Most containers still ad-hoc `docker run` | 2–4 h | **Soft blocker** — every v1 change recreates openwebui or adds new containers; should be done in lockstep |
| Empty docs in guardian-cloud (R-15-style) | 0 (upstream) | Awaiting user | Captured in RAG audit |
| Zigbee2MQTT still in onboarding | (upstream) | Awaiting user | Captured |
| No off-site backups | ~4 h | Phase 0 R-12 baseline only | Out of scope for v1 |
| `homelab-rag-ingest` is bare-metal, not containerized | ~2 h | Backup hygiene; for v2 |

**Debt that v1 explicitly resolves:**

- R-02 (homelab-tools rewrite into a container).
- R-14 (compose files written for at least the AI stack subset).
- Adds the missing tool-calling path (the largest piece of "debt by
  absence").

**Debt v1 deliberately defers** (worth flagging now):

- R-09, R-10, R-11, R-13 — system hardening sweep, do as a batch
  after v1 is stable.
- Off-site backups — Phase 0 only covered local; an off-site mirror
  (tailnet peer or B2) is its own project.

## 6. Security review of the AI stack

Component-by-component, with current state and v1 deltas. (Tool-level
security is covered in detail in
[04-security-and-permissions.md](04-security-and-permissions.md);
this is the infrastructure view.)

### Open WebUI

| Property | State today | v1 change? |
|----------|-------------|-----------|
| Auth required | ✅ yes (`auth: true`, `enable_signup: false`) | unchanged |
| Stable `WEBUI_SECRET_KEY` | ✅ yes (Phase 0 R-05) | unchanged |
| Docker socket mount | ✅ removed (Phase 0 R-06) | unchanged |
| API key issuance | ❌ disabled (`enable_api_keys: false`) | **enabled, gated** — needed so HA Assist later can call us back |
| Bind | `0.0.0.0:3000` | unchanged; LAN/tailnet reach is intentional |
| TLS | none (HTTP) | unchanged for v1; NPM proxy host is the cleaner v1.5 path |

### Ollama

| Property | State today | v1 change? |
|----------|-------------|-----------|
| Auth | none | **deferred** — bind to `127.0.0.1` is the v1 stretch goal |
| Bind | `0.0.0.0:11434` | should change; non-blocking |
| Available models | llama3.2:3b, phi3:3.8b, llama3:8b (none ideal for tools) | **add qwen2.5:7b-instruct** as primary |

### Qdrant

| Property | State today | v1 change? |
|----------|-------------|-----------|
| API key required | ✅ yes (Phase 0 R-07.1) | unchanged |
| Bind | `0.0.0.0:6333` (key gates everything) | should rebind to `127.0.0.1`; non-blocking |
| Telemetry / metrics | reachable behind same key | acceptable |
| Cluster mode | single-node, no peers | unchanged |

### Tool runtime (Open WebUI Functions)

| Property | State today | v1 change? |
|----------|-------------|-----------|
| Process model | each Function runs as `python3` inside the openwebui container | unchanged |
| Network reach | same as openwebui — `ai-local_default` + `proxy_default` | OK; tools call ollama / qdrant by hostname, HA via host IP |
| Secrets exposure | per-function "valves" (Open WebUI config), or env vars passed at container start | v1 standardises on env vars from `/home/diego/homelab/ai-stack/.env` |
| Sandbox | none — full Python execution | **mitigations:** small tool surface, no `eval`, hand-written tools only |
| Audit | none today | **v1 adds:** JSON-line log to `/var/log/amarolab-audit.log` (file under bind mount), logrotated weekly, 12 weeks |

### Ingest service

| Property | State today | v1 change? |
|----------|-------------|-----------|
| Runs as | user `diego` via cron | unchanged |
| Read scope | `/home/diego/homelab`, `/mnt/storage/projects/{guardian-cloud,ensambla2}`, the openwebui HF cache | **v1 adds:** `/home/diego/server-audit-2026-06-13` as `infra_audits` corpus |
| Write scope | Qdrant (4→5 collections), logs dir | unchanged plus new corpus |
| Git operations | `git pull --ff-only`, skip if dirty | unchanged |

### Home Assistant integration (new in v1)

| Property | v1 state |
|----------|----------|
| Auth to HA | Long-Lived Access Token, single token for the assistant |
| Token storage | `/home/diego/homelab/ai-stack/.env`, mode 0600 |
| Token scope | tied to a dedicated HA user `assistant` (recommendation in roadmap) — limits blast radius if leaked |
| Network path | tool inside openwebui container → `http://192.168.178.79:8123` (host LAN IP, HA listens host-net) |
| Allowed services | allowlist enforced *client-side* in `ha_call_service`; HA's own "exposed to assist" config is the second line |

### `homelab-tools` rewrite (new in v1)

| Property | v1 state |
|----------|----------|
| Runtime | container on `ai-local_default` |
| Bind | container-internal `:5050`; no host port published |
| Auth | none required (network is the boundary; only openwebui can reach it) |
| Scope | read-only: `docker ps`, `docker logs --tail` for the allowlisted containers, `ss -tlnp` summary |
| Source of truth | container talks to the host's Docker socket via `docker-socket-proxy` (read-only) — same pattern as the R-06 fallback path |

This collapses two old problems (R-02 + R-06) into one architectural
move.

### Data exposure model

The assistant has read access to:

- All homelab docs (`/home/diego/homelab/**`)
- All guardian-cloud docs (paths listed in `corpora.yaml`)
- All ensambla2 docs (paths listed)
- All infrastructure audit docs (`/home/diego/server-audit-2026-06-13/**`)
- Live HA state (every entity exposed to Assist)
- Live container list + recent logs (allowlisted containers)

Anyone who can chat with the assistant has read access, *via tools*, to
all of the above. Today that's only `diego`. Multi-user is out of scope
for v1; permission model fully spelled out in
[04-security-and-permissions.md](04-security-and-permissions.md).

## 7. Missing pieces before production use

"Production" here means "everyday daily-driver, not a demo". The
implementation roadmap (
[05-implementation-roadmap.md](05-implementation-roadmap.md)) builds
each of these in order.

### Functional gaps (the assistant cannot answer the sample questions today)

| Missing | Required for which sample question |
|---------|--------------------------------------|
| Tool-calling LLM in Ollama | All tool-mediated questions |
| `rag_search` Open WebUI Function | Guardian Cloud / Ensambla2 docs |
| `ha_get_state` Function | HA automations / sensors |
| `ha_call_service` Function | Acting on HA (optional in v1) |
| `system_status` Function | Containers / ports |
| `audit_search` Function | "What changed in the last audit" |
| `infra_audits` Qdrant collection | Same |
| HA Long-Lived Access Token | HA tools |
| Containerized `homelab-tools` | `system_status` |
| Reranker wired into `rag_search` | Quality target (top-6 ≥ 95 % observed in benchmark) |
| System prompt | All |

### Operability gaps

- **No per-tool audit log.** First leaked secret or unintended action
  becomes a forensics nightmare without one. v1 ships a JSON-line log.
- **No rate limits on tools.** A runaway LLM (or a deliberate misuse)
  could hammer HA or Qdrant. v1 adds simple per-session counters.
- **No health probes for the assistant as a whole.** Today, you'd
  notice it's broken when you tried to use it. v1 ships a one-liner
  `bin/amarolab-health` that exercises every tool.
- **No "model warm" cron.** First query of the day pays the 20-second
  load tax. Optional v1 polish.

### Documentation gaps

- **No user-facing "what can I ask?" cheat sheet.** Currently lives only
  in this design package.
- **No "this is what the assistant cannot do" list.** Important — Open
  WebUI users will probe edge cases; clear refusals beat hallucinated
  pretend-it-can.

### Hardening gaps (acceptable for v1, must close before public exposure)

- **No TLS in front of Open WebUI.** Today HTTP on `:3000`. NPM proxy
  host with Let's Encrypt is the right fix and is one click away.
- **No outbound egress restrictions on the openwebui container.** A
  malicious Tool function could `requests.post()` anywhere. Mitigated by
  "only hand-written tools" policy.
- **No second-factor on the Open WebUI login.** Single password is the
  only door.

None of these block v1 going live for the *one user* it's built for;
all become real if you ever broaden access.
