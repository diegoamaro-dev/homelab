# 01 — Architecture

## Design principles

1. **Local-first.** No external inference, no telemetry, no cloud RAG. The
   already-present hardware budget covers a 7 B-parameter assistant for a
   single concurrent user.
2. **Two front doors, one brain.** Open WebUI and HA Assist both speak to
   the same Ollama model so behavior stays consistent regardless of how
   the user prompts.
3. **Small tool surface.** The LLM gets four tools — state read, state
   write (via HA services), RAG search, and a couple of trivia helpers.
   Each tool is documented, audited, and rate-limited.
4. **Knowledge layer is the only writer to Qdrant.** Open WebUI's "upload
   to knowledge" path is disabled in favor of a single ingestion service
   that owns indexing for all four corpora — so RAG quality is
   reproducible and per-corpus updates are deterministic.
5. **Add as little as possible.** Two new services (ingestion + optional
   socket-proxy from Phase 2/R-06); no new ports exposed to the LAN; no
   new external dependencies.

## Component map

```
┌────────────────────────────────────────────────────────────────────────┐
│                            USER SURFACES                               │
│                                                                        │
│   ┌──────────────────────┐         ┌────────────────────────────────┐  │
│   │  Open WebUI          │         │  Home Assistant Assist         │  │
│   │  • web/PWA chat      │         │  • voice (Wyoming + Piper      │  │
│   │  • file upload       │         │    + Whisper, optional)        │  │
│   │  • Whisper STT (opt) │         │  • dashboard "Assist" cards    │  │
│   │  :3000  proxy net    │         │  :8123  host net               │  │
│   └──────────┬───────────┘         └────────────────┬───────────────┘  │
│              │                                      │                  │
│              │ /v1/chat/completions                  │ OpenAI-compatible│
│              │ (Ollama-native API)                   │ /v1 endpoint via │
│              │                                      │ Open WebUI       │
└──────────────┼──────────────────────────────────────┼──────────────────┘
               │                                      │
               ▼                                      ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         ASSISTANT BRAIN                                │
│                                                                        │
│   ┌──────────────────────────┐                                         │
│   │  Ollama  (qwen2.5:7b)    │   ◄── tool calling / function calling   │
│   │  llama3.2:3b for fast    │       (native in qwen2.5 / llama3.1)    │
│   │  :11434  ai-local net    │                                         │
│   └──────────┬───────────────┘                                         │
│              │                                                         │
│              ▼  TOOL ROUTER (implemented as Open WebUI "Functions")    │
│                                                                        │
│   ┌────────────────────┐ ┌────────────────────┐ ┌────────────────────┐ │
│   │ ha_get_state       │ │ ha_call_service    │ │ rag_search         │ │
│   │ ha_list_areas      │ │ (allowlisted only) │ │ (collection, q, k) │ │
│   └─────────┬──────────┘ └─────────┬──────────┘ └──────────┬─────────┘ │
└─────────────┼──────────────────────┼───────────────────────┼───────────┘
              │                      │                       │
              ▼                      ▼                       ▼
┌──────────────────────────┐ ┌────────────────────┐ ┌─────────────────────┐
│ Home Assistant REST API  │ │ HA REST + websocket│ │  Qdrant             │
│ /api/states              │ │ /api/services      │ │  :6333  ai-local    │
│ :8123 host net           │ │ :8123 host net     │ │  collections:       │
│ token: HA Long-Lived     │ │ scope-limited      │ │   homelab_docs      │
│         Access Token     │ │ token              │ │   guardian_cloud    │
└──────────────────────────┘ └────────────────────┘ │   ensambla2         │
                                                    │   myfreetour        │
                                                    └──────────┬──────────┘
                                                               │
                                                               │  read/write
                                                               ▼
                                            ┌────────────────────────────────┐
                                            │  homelab-rag-ingest (NEW)      │
                                            │  • git/fs connectors           │
                                            │  • chunker + embedder          │
                                            │    (multilingual-e5-small)     │
                                            │  • cron 02:30 + on-demand CLI  │
                                            │  :127.0.0.1:8001  ai-local net │
                                            └────────────────────────────────┘
```

## Workload distribution

| Container | Role | Existing? | Network | Listens on (host) |
|-----------|------|-----------|---------|-------------------|
| `homeassistant` | front door + entity API | yes | host | `:8123` |
| `openwebui` | front door + tool router + LLM client | yes | ai-local + proxy | `:3000` |
| `ollama` | LLM serving | yes | ai-local | `127.0.0.1:11434` (after R-07) |
| `qdrant` | vector DB | yes | ai-local | `127.0.0.1:6333` (after R-07) |
| `mosquitto` | MQTT broker | yes (broken; R-04) | zigbee | — |
| `zigbee2mqtt` | Zigbee bridge | yes | zigbee | `:8080` |
| `homelab-rag-ingest` | RAG ingestion CLI/HTTP | **new** | ai-local | `127.0.0.1:8001` |
| `wyoming-whisper` | voice STT (optional) | new | zigbee or ha-voice | none (HA-internal) |
| `wyoming-piper` | voice TTS (optional) | new | zigbee or ha-voice | none (HA-internal) |
| `docker-socket-proxy` | gated docker socket (R-06) | new | proxy | none |

Three of the components — Ollama, Qdrant, and the new ingestion service —
all sit on the existing `ai-local_default` Docker network, so they speak
to each other by DNS hostname and never need to publish ports.

## Model selection

### LLM

| Model | Size on disk | RAM in use (Q4) | Tool calling | Multilingual | Verdict |
|-------|-------------:|----------------:|:------------:|:------------:|---------|
| `llama3.2:3b` (Q4_K_M) — present | 2.0 GB | 2.5 GB | partial | weak | Fast fallback / quick HA queries |
| `phi3:3.8b` — present | 2.2 GB | 3 GB | no | weak | Drop / repurpose for summarization |
| `llama3:8b` — present | 4.7 GB | 5.5 GB | weak | weak | Drop |
| `qwen2.5:7b-instruct` (Q4_K_M) — **recommended new** | ~4.7 GB | ~5.5 GB | native | strong | **Primary** |
| `llama3.1:8b-instruct` (Q4_K_M) | ~4.7 GB | ~5.5 GB | native | weak | Alternative if quality testing favours it |
| `qwen2.5:3b-instruct` | ~2 GB | 2.5 GB | native | strong | Faster fallback than llama3.2:3b |

Single concurrent user, ~5–8 tok/s expected for the 7 B model on CPU
(Zen 4 + AVX-512 + 16 threads, no GPU). Enough for streamed chat.

### Embeddings

| Model | Dim | RAM | Languages | Verdict |
|-------|-----|-----|-----------|---------|
| `sentence-transformers/all-MiniLM-L6-v2` — current | 384 | ~90 MB | English | Keep working but lose Spanish quality |
| `intfloat/multilingual-e5-small` — **recommended** | 384 | ~120 MB | 100+ incl. Spanish | **Primary** |
| `BAAI/bge-m3` | 1024 | ~600 MB | 100+ | Higher quality, ~5× disk per chunk; defer until measured need |

Switching embedding models means re-ingesting (the existing 5 points in
the open-webui collections are negligible — not a migration concern).

## Knowledge base layout

One Qdrant collection per corpus.

| Collection | Source path | Points (2026-06-14) | Notes |
|------------|-------------|--------------------:|-------|
| `homelab_docs` | `/home/diego/homelab/**/*.{md,yaml,yml,conf}` | 86 | git repo; .gitignore respected |
| `guardian_cloud` | `/mnt/storage/projects/guardian-cloud/{docs,strategy,playbook,Pagina web,*.md}` | 872 | git repo; excludes mobile/app/backend/gradle build trees |
| `ensambla2` | `/mnt/storage/projects/ensambla2/{*.md,docs,packages/*/README.md}` | 419 | git repo |
| `myfreetour` | TBD (open question) | 0 | collection pre-created, `enabled: false` in `corpora.yaml` |

Excluded by default: binaries, `node_modules/`, `.git/`, `dist/`,
`build/`, files > 5 MB, files that aren't UTF-8.

Payload (metadata) per point:

```json
{
  "collection": "guardian_cloud",
  "source_path": "/mnt/storage/projects/guardian-cloud/docs/architecture.md",
  "source_rel":  "docs/architecture.md",
  "source_kind": "markdown",
  "chunk_index": 4,
  "chunk_count": 18,
  "content_sha": "ab12cd…",
  "modified_at": "2026-05-30T18:11:43Z",
  "language":    "es",
  "title":       "Arquitectura — Guardian Cloud"
}
```

`content_sha` enables idempotent re-ingestion: if the chunk hash matches
an existing point, skip the embed call.

## Why two front doors instead of one

- **HA Assist** is the right surface for *control* and *quick state
  queries*: it has a voice pipeline, mobile widgets, dashboard cards, and
  knows what an "area" is.
- **Open WebUI** is the right surface for *long-form chat*, *file
  uploads*, *code Q&A*, and explaining *why* — it has streaming UI,
  conversation history, multi-turn context, and per-user accounts.
- Pointing both at the same tool-calling brain means an HA command
  ("what's the temperature in the office?") and an Open WebUI question
  ("how do I rewire the Zigbee dongle?") both go through the same
  reasoning loop and have access to the same tools.

## Why a separate ingestion service instead of Open WebUI Knowledge

Open WebUI's built-in Knowledge feature *can* upload and index files into
Qdrant. It works fine for ad-hoc documents. It is not the right tool for
**continuously syncing four corpora** because:

- No scheduled re-sync — files must be re-uploaded on every change.
- No source-tree awareness — uploaded files lose their relative path.
- No multi-source separation — everything lands in the same two
  collections (`open-webui_knowledge`, `open-webui_files`).
- No code-aware chunking — long files get cut arbitrarily.

The dedicated ingestion service owns these properties and keeps Open
WebUI's RAG knobs as a fallback for one-off documents.
