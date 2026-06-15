# 02 — Target architecture: Amarolab Assistant v1

## Design principles

1. **Build on what works.** Open WebUI, Ollama, Qdrant, the ingest
   service, and the reranker are already in place and good. v1 wires
   them together with the smallest amount of new code possible.
2. **Tool-mediated, not implicit.** The LLM never accesses Home
   Assistant or the live system directly. Every external action goes
   through a named tool with a schema, an allowlist, and an audit line.
3. **Single user, single trust zone.** v1 is for `diego`. No
   pretending to be multi-tenant. The permission model is "the chat
   user can call any defined tool"; safety comes from tool design, not
   per-user ACLs.
4. **Read-mostly.** Reading the world is cheap and safe. Acting on it
   is rare and gated. v1's write surface is intentionally narrow.
5. **Production isolation.** Guardian Cloud backend is external
   production. The assistant has read-only RAG over its docs and never
   calls its API or modifies its source tree.

## Component map

```
                                 USER
                                  ┃
                  LAN 192.168.178.0/24    Tailnet 100.68.180.69
                                  ┃
                                  ▼
        ┌──────────────────────────────────────────────────┐
        │  Open WebUI :3000  (chat UI + Functions runtime) │
        │  - WEBUI_SECRET_KEY pinned (Phase 0 R-05)        │
        │  - QDRANT_API_KEY in env                          │
        │  - HA_BASE_URL + HA_LLAT in env (NEW)            │
        │  - HOMELAB_TOOLS_URL in env (NEW)                │
        │  - WEBUI_API_KEYS_ENABLED=true (NEW)             │
        └──────────────────────────────────────────────────┘
                                  │
              ┌───────────────────┼───────────────┬──────────────────┐
              ▼                   ▼               ▼                  ▼
      ┌─────────────┐    ┌──────────────┐  ┌──────────────┐   ┌──────────────┐
      │   Ollama    │    │   Qdrant     │  │ Home Assist. │   │ homelab-tools│
      │ qwen2.5:7b  │    │              │  │   :8123      │   │  (NEW)       │
      │ (primary)   │    │ 5 collections│  │ host network │   │ :5050 in     │
      │ llama3.1:8b │    │ + reranker   │  │ LLAT bearer  │   │ container    │
      │ (secondary) │    │   (in tool)  │  │              │   │ no host port │
      └─────────────┘    └──────────────┘  └──────────────┘   └──────────────┘
              ▲                   ▲                                   │
              │                   │                                   │ via
              └ ai-local_default ─┘                                   │ docker-socket-
                                  ▲                                   │ proxy:2375
                                  │                                   │ (ai-local)
        ┌──────────────────────────────────────────┐                  │
        │  Ingest service (containerized, NEW)     │                  │
        │  homelab-rag-ingest container            │                  ▼
        │  - reads /home/diego/homelab (ro)        │           ┌─────────────────┐
        │  - reads /mnt/storage/projects (ro)      │           │ docker-socket   │
        │  - reads /home/diego/server-audit-… (ro) │           │ -proxy  :2375   │
        │  - reads /srv/homelab/data/openwebui     │           │ (NEW, read-only)│
        │    /cache/embedding/models (rw)          │           │ → /var/run/     │
        │  - writes to Qdrant                       │           │   docker.sock   │
        │  - scheduled by host cron 02:30           │           └─────────────────┘
        └──────────────────────────────────────────┘
```

**Networks:**

- `ai-local_default` — internal traffic between openwebui, ollama,
  qdrant, homelab-tools, docker-socket-proxy, ingest. No host ports
  required for any of these except openwebui (`:3000`).
- `proxy_default` — openwebui remains here for future NPM publication.
- All others (`zigbee-stack`, `cloudflare-net`, etc.) unchanged from
  pre-v1.

## What is new in v1

### New containers

| Container | Image | Why |
|-----------|-------|-----|
| `homelab-tools` | small Python image (Flask or FastAPI) | Replaces the bare-metal `homelab-tools.service` Flask app. Containerized, no host port, on `ai-local_default`. Closes R-02. |
| `docker-socket-proxy` | `tecnativa/docker-socket-proxy` | Gives `homelab-tools` read-only access to the host Docker socket via TCP, without exposing the socket itself. |
| `homelab-rag-ingest` (optional, v1.1) | small Python image | Containerises the current bare-metal ingest service. Backed up cleanly via R-12; restart semantics. Not strictly needed for v1 to work, but cleaner. |

### New Qdrant collection

| Collection | Source | Purpose |
|------------|--------|---------|
| `infra_audits` | `/home/diego/server-audit-2026-06-13/**/*.md` | Lets the assistant answer "what was changed in the last audit", "what does the Phase 0 application log say about R-06", etc. |

### New Open WebUI Functions (Tools)

| Tool | Purpose | Allowlist? |
|------|---------|------------|
| `rag_search` | dense + rerank over one of the 5 corpora | collection name validated against allowlist |
| `audit_search` | sugar over `rag_search(collection="infra_audits")` | n/a |
| `ha_get_state` | read entity state(s) from HA | none — read-only |
| `ha_call_service` | invoke an HA service | domain allowlist |
| `system_status` | call `homelab-tools` for live container/port info | scope param validated |

Each tool is a single Python file in
`/srv/homelab/data/openwebui/functions/` (Open WebUI's standard
location for Functions; survives container restarts via the existing
bind mount).

### New Ollama model

`qwen2.5:7b-instruct` (Q4_K_M, ~4.7 GB) pulled into the existing
`/srv/homelab/data/ollama/models` cache. Existing models stay; the
admin can choose per-chat which model to use.

Rationale: tool-calling support is mature in qwen2.5 (and llama3.1);
multilingual quality is meaningfully better in qwen2.5 (matters because
roughly half the RAG content is Spanish).

### New environment variables (in `/home/diego/homelab/ai-stack/.env`)

```
# Already there from Phase 0:
QDRANT__SERVICE__API_KEY=<64 hex>
QDRANT_API_KEY=<same>
WEBUI_SECRET_KEY=<64 hex>

# Added in v1:
HA_BASE_URL=http://192.168.178.79:8123
HA_LLAT=<64 char token from HA UI>
HOMELAB_TOOLS_URL=http://homelab-tools:5050
AMAROLAB_AUDIT_LOG=/app/backend/data/amarolab-audit.log
RERANKER_ENABLED=true
RAG_TOP_N_DENSE=30
RAG_TOP_K=6
```

The audit log path is inside the openwebui container; on the host it
lives at `/srv/homelab/data/openwebui/amarolab-audit.log` (via the
existing bind mount).

## What is **modified** in v1 (carefully)

| Component | Change | Justification |
|-----------|--------|---------------|
| `openwebui` container | re-recreated with the new env vars + `enable_api_keys: true` | New env vars are needed; recreating once is cheap |
| `ingest/corpora.yaml` | add `infra_audits` corpus | New collection |
| `ingest/cli.py` | (none) — still bare-metal in v1 | Containerisation is v1.1 |
| `ingest/reranker.py` | (none) — already exists from Phase 1.5 | Just gets called by `rag_search` |
| HA `secrets.yaml` | LLAT documented but **lives in HA's user profile**, not here | Out of the HA config tree |

## What is **untouched** in v1

- Qdrant container (already has the API key; collections add cleanly without recreate).
- Ollama container (just `ollama pull`; no recreate).
- All other containers (homeassistant, npm, portainer, zigbee2mqtt, mosquitto, cloudflared, guardian-web).
- `/mnt/storage/projects/guardian-cloud/` source tree — explicitly read-only per user requirement.
- `/mnt/storage/projects/ensambla2/` source tree.
- Phase 0 hardening — none of R-02, R-09, R-10, R-11, R-13 are touched in v1 (R-02 *is* effectively solved by replacing the Flask service, but the unit file stays disabled rather than purged).

## Data flow — primary chat with tools

```
User: "How does Guardian Cloud recovery work?"
  │
  ▼
Open WebUI session
  │   loads system prompt
  │   appends 5 tool schemas
  ▼
POST http://ollama:11434/api/chat
  │   model=qwen2.5:7b-instruct
  │   messages=[system, user]
  │   tools=[rag_search, audit_search, ha_get_state, ha_call_service, system_status]
  │
  ▼
Ollama returns: tool_calls=[
   { name: "rag_search",
     arguments: { collection: "guardian_cloud",
                  query: "recovery flow",
                  k: 6 } } ]
  │
  ▼
Open WebUI runtime: invoke the Python Function
  │
  │   rag_search.py:
  │     vec  = embedder.embed_query(query)           # multilingual-e5-small
  │     cands = qdrant.query_points(coll, vec, limit=30)
  │     hits  = reranker.rerank(query, cands, top_k=6) # bge-reranker-v2-m3
  │     log_to_audit({...})
  │     return [{ source_rel, score, title, content_snippet }, ...]
  │
  ▼
POST http://ollama:11434/api/chat (round 2)
  │   messages=[system, user, assistant(tool_calls), tool_result]
  │
  ▼
Ollama generates final answer
  │   inline cites [^1], [^2] referencing source_rel
  │
  ▼
Open WebUI streams to user
```

Total wall clock estimate for one such turn:

- Embed: ~50 ms
- Qdrant search: ~20 ms
- Rerank 30 candidates: ~120 ms
- LLM round 1 (decides tool): ~1.5 s
- LLM round 2 (synthesis): ~3 s for ~400-token answer
- Open WebUI UI overhead: ~100 ms

≈ **5 s end-to-end** for a typical RAG-grounded answer. Voice-cadence
not great, chat-cadence fine.

## Data flow — secondary chat (no tools)

If the LLM decides no tool is needed (e.g., user says "thanks"), the
flow collapses to:

```
User → Open WebUI → Ollama → response
```

Same as today. ~1–3 s.

## Data flow — ingestion (unchanged from Phase 1, plus new corpus)

```
cron 02:30 (host, user diego)
  → /home/diego/homelab/ai-stack/ingest/bin/ingest sync
    → walks each enabled corpus
    → embeds new chunks with multilingual-e5-small
    → upserts to Qdrant (now 5 collections)
    → garbage-collects deleted files
    → logs JSON-line summary
```

The reranker is **not** in the ingestion path. Reranking is purely a
retrieval-time concern.

## Sample question → tool routing

The system prompt tells the LLM which collection holds what; here is the
expected routing for each acceptance question.

| Sample question | Expected tool call(s) |
|-----------------|----------------------|
| "How does Guardian Cloud recovery work?" | `rag_search(collection="guardian_cloud", query="recovery", k=6)` |
| "What containers are running?" | `system_status(scope="containers")` |
| "What services are exposed?" | `system_status(scope="ports")` |
| "What automations exist in Home Assistant?" | `ha_get_state(domain="automation")` |
| "What documentation exists for Ensambla2?" | `rag_search(collection="ensambla2", query="overview", k=10)` |
| "What was changed in the last infrastructure audit?" | `audit_search(query="applied 2026-06-13 phase 0", k=8)` |

Routing accuracy is a property of the system prompt + the LLM. v1's
acceptance test runs these six prompts and requires the right tool to
fire (and the answer to cite a real source). If routing is shaky,
qwen2.5 vs llama3.1 is the first knob to twist.

## What v1 deliberately does **not** include

- **Voice (Wyoming Whisper/Piper).** Per user request.
- **Conversation memory across sessions.** Open WebUI keeps in-session
  history in `webui.db`; cross-session recall via a `conversations`
  Qdrant collection is v2.
- **Auto-routing across all corpora.** v1 requires the LLM to pick a
  collection. v2 could fan out and rerank across collections.
- **Public exposure via Cloudflare.** Only the `guardian-web` static
  site goes through cloudflared; the assistant stays inside
  LAN/tailnet.
- **Per-user permissions.** Out of scope until a second user exists.
- **TLS in front of Open WebUI.** Recommended for v1.1 via the
  existing NPM. Not required for one user on a trusted network.
- **Write access to guardian-cloud / ensambla2 git trees.** Strictly
  read-only.

## Acceptance criteria for "v1 is done"

1. The six sample questions all return correct, cited answers.
2. The reranker is in `rag_search`; benchmark top-6 ≥ 95 % on the
   guardian_cloud benchmark (same questions, same JSON, re-runnable).
3. Audit log accumulates one JSON line per tool call.
4. `ha_call_service` with a non-allowlisted domain returns a polite
   refusal (not 500).
5. Restarting `openwebui` does not require re-login.
6. Cron-driven nightly ingest still runs cleanly (no regression from
   adding the `infra_audits` corpus).
