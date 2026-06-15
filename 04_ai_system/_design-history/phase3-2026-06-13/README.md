# Phase 3 — Local AI assistant for house + homelab

- **Date:** 2026-06-13
- **Status:** Design only. No implementation. **Phase 2 Critical fixes are
  prerequisites** (Mosquitto config, Flask API rebind, NPM permissions,
  Cloudflare token segregation).
- **Building blocks already present on the host:** Home Assistant 2026.3.1,
  Zigbee2MQTT, Mosquitto, Open WebUI 0.8.10, Ollama 0.17.7 (`llama3.2:3b`,
  `phi3:3.8b`, `llama3:8b`), Qdrant 1.17.0, Cloudflared tunnel, Docker
  29.4.1.
- **Hardware budget:** AMD Ryzen 9 7940HS (16 t, AVX-512), 30 GiB RAM,
  AMD Radeon 780M (CPU-only inference for now), 476 GB NVMe + 1.8 TB HDD.

## Report index

| # | Document | Focus |
|---|----------|-------|
| 01 | [Architecture](01-architecture.md) | Components, surfaces, model |
| 02 | [Data flow](02-data-flow.md) | Conversation, RAG, ingestion, control |
| 03 | [Required integrations](03-integrations.md) | HA, Ollama, Qdrant, Open WebUI |
| 04 | [Security model](04-security-model.md) | Trust boundaries, secrets, audit |
| 05 | [Resource requirements](05-resource-requirements.md) | RAM/CPU/disk/network |
| 06 | [Implementation plan](06-implementation-plan.md) | 7-phase rollout with exit criteria |
| — | [PHASE-1-APPLIED](PHASE-1-APPLIED.md) ✅ | Phase 1 application log (1 377 points indexed across 3 collections) |

## TL;DR

**One assistant, two front doors.**

- **Open WebUI** (text chat, mobile PWA, file uploads, occasional voice).
- **Home Assistant Assist** (voice, dashboard cards, mobile widgets, quick
  intents like "turn on lounge lights" or "is the office hot?").

**Same brain underneath:** a tool-calling LLM running on Ollama. Both
front doors point at it; Open WebUI calls Ollama directly, HA calls Open
WebUI's OpenAI-compatible endpoint (so the *same* tools are available to
both).

**Tool surface — kept deliberately small:**

1. `ha_get_state(entity_id | area | domain)` — read sensor / device state.
2. `ha_call_service(domain, service, target, data)` — execute HA actions,
   restricted to an exposed-to-assist allowlist.
3. `rag_search(collection, query, k)` — query the four knowledge bases:
   `homelab_docs`, `guardian_cloud`, `ensambla2`, `myfreetour`.
4. `time_now()` / `weather_now()` — trivia tools to anchor responses.

**Knowledge base layout (Qdrant collections):**

| Collection | Source | Status today |
|------------|--------|--------------|
| `homelab_docs` | `/home/diego/homelab/**` (git) | ready to index |
| `guardian_cloud` | `/mnt/storage/projects/guardian-cloud/**` (git) | ready to index |
| `ensambla2` | `/mnt/storage/projects/ensambla2/**` (git) | ready to index |
| `myfreetour` | **location unknown — open question** | needs the path / git URL |

A new ingestion service runs on the host (Python, scheduled by cron, also
invocable on demand) and is the only component that writes to Qdrant.

## Open questions to confirm before implementation

1. **MyFreeTour source location.** Not found on the host. Options:
   - A git URL to clone (preferred).
   - A path on `/mnt/storage/projects/` once you upload it.
   - A live URL/API to crawl (would require a different connector design).
2. **Language(s) of the four corpora.** Likely a mix of Spanish and
   English. Recommended embedding model is multilingual
   (`intfloat/multilingual-e5-small`); see [03-integrations.md](03-integrations.md).
3. **Tool-calling LLM choice.** Current models (llama3.2:3b, llama3:8b,
   phi3) don't all support function calling well on CPU. Recommended:
   pull `qwen2.5:7b-instruct` (multilingual + native tool calling) as the
   primary, keep `llama3.2:3b` as the fast fallback.
4. **External exposure.** Default plan keeps the assistant on LAN +
   Tailscale only (no Cloudflare exposure). Confirm or change.
5. **Voice scope.** HA Assist voice (Wyoming + Piper/Whisper) adds two
   more containers; Open WebUI's built-in voice doesn't. Pick: full-house
   voice, web-only voice, or no voice for v1.

## How this stack sits on top of Phase 1 / Phase 2

The audit's [headline findings](../README.md) include several items that
*must* be applied first because Phase 3 builds on them:

| Audit finding | Why it blocks Phase 3 |
|----------------|------------------------|
| R-04 Mosquitto crash loop ✅ | Applied 2026-06-13. Broker healthy, hostname fixed, MQTT round trip validated. (Z2M onboarding still to be completed by user before entities flow.) |
| R-07 Qdrant unauthenticated ✅ (key) / ⏭ (port rebind) | API key applied 2026-06-13. Open WebUI sends `QDRANT_API_KEY`; ingestion service will read the same value from `/home/diego/homelab/ai-stack/.env`. Port rebind to `127.0.0.1` still deferred to R-14. |
| R-05 Open WebUI secret key ✅ | Applied 2026-06-13. Sessions and API keys now survive restarts. |
| R-12 Backups ✅ | Applied 2026-06-13. Snapshot `cc73b4fd`. New ingestion artefacts will land in the existing nightly job. |
| R-14 Compose files | Adding new containers (ingestion service, possibly Whisper/Piper) without compose is technical debt that will hurt |

Phase 3 doesn't depend on R-06 (Open WebUI Docker socket — applied
2026-06-13 ✅, socket no longer mounted), R-09 (rpcbind), R-10 (UFW),
R-11 (image updates), R-13 (Apache), or any 🟢 Low items — those can
happen in parallel.
