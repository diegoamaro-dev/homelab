# Amarolab Assistant v1 — Design package

- **Date:** 2026-06-14
- **Status:** Design only. **Nothing has been implemented, installed, or
  modified.** Live infrastructure is the same as it was at the end of
  Phase 1.5 (RAG reranker benchmark).
- **Audience:** Future-you, sitting down to build. Each section answers
  one question; the implementation roadmap chains them.

## What this package replaces

The Phase 3 design package
([`../phase3-ai-assistant/`](../phase3-ai-assistant/)) was the original
"how would the assistant look" sketch, written *before* Phase 1 had any
RAG content in Qdrant and *before* the audit/benchmark/reranker work.

This v1 package is the **buildable** version, written *after* those
phases. It supersedes phase3-ai-assistant for anything to do with the
assistant itself. The phase3 design is kept as a historical reference
because some of its content (resource forecasts, the broader sequencing
strategy) is still useful.

## Document index

| # | Document | Question it answers |
|---|----------|---------------------|
| 01 | [Current state review](01-current-state-review.md) | What does the AI stack look like *today*, where does it strain, what's missing? |
| 02 | [Target architecture](02-target-architecture.md) | What does Amarolab Assistant v1 look like, and how does it sit on top of what we already have? |
| 03 | [Tool catalog](03-tools.md) | Exactly which tools does the LLM get, with what signatures and what guardrails? |
| 04 | [Security & permission model](04-security-and-permissions.md) | Who can do what, how secrets flow, what gets audited |
| 05 | [Implementation roadmap](05-implementation-roadmap.md) | What to build in what order, with effort estimates and exit criteria |

## TL;DR — what gets built

```
                       USER (diego, LAN/Tailscale)
                                 │
                                 ▼
                       Open WebUI :3000  ◄── chat UI + tool runner
                                 │
                                 ▼
                       Ollama  qwen2.5:7b-instruct  ◄── tool-calling LLM
                                 │
              ┌──────────────────┼────────────────────┐
              │                  │                    │
              ▼                  ▼                    ▼
       rag_search()         ha_get_state()      system_status()
       ha_call_service()    audit_search()
              │                  │                    │
              ▼                  ▼                    ▼
     Qdrant + reranker      HA :8123          homelab-tools
        (4–5 corpora)       (REST API)         (containerized,
        bge-reranker                            new, replaces
        -v2-m3                                  bare-metal Flask)
```

Five tools, one LLM, four (later five) RAG corpora, two live-system
integrations (HA + homelab-tools).

Scope:

- **In scope for v1:** answer questions about the homelab, Guardian
  Cloud / Ensambla2 docs, infrastructure audit history, HA entity
  state, and basic HA control (lights, scenes, climate via allowlist).
- **In scope for v1.5:** MyFreeTour corpus once source path is known.
- **Out of scope for v1:** voice (Wyoming Whisper/Piper), public
  exposure via Cloudflare, multi-user permissions, conversation memory
  across chats, write access to Guardian Cloud / Ensambla2 repos.
- **Explicitly forbidden:** any tool that calls Guardian Cloud's
  backend API or modifies its source tree. Guardian Cloud is treated as
  external production; the assistant has read-only RAG over its docs
  and that is the limit.

## Sample interactions the design must support

These are the user-supplied acceptance questions for the design. Each
maps to a specific path through the architecture; the [tool catalog](03-tools.md)
shows which tool(s) fire for each.

| Question | Path |
|----------|------|
| "How does Guardian Cloud recovery work?" | `rag_search(collection="guardian_cloud", query="recovery flow")` → reranker → answer with citations |
| "What containers are running?" | `system_status(scope="containers")` → live `docker ps`-equivalent |
| "What services are exposed?" | `system_status(scope="ports")` → live listening-port enumeration |
| "What automations exist in Home Assistant?" | `ha_get_state(domain="automation")` |
| "What documentation exists for Ensambla2?" | `rag_search(collection="ensambla2", query="*")` + metadata listing |
| "What was changed in the last infrastructure audit?" | `audit_search(query="last applied")` over new `infra_audits` collection |

The implementation roadmap ends with a "smoke test" gate that runs
exactly these six questions and requires top-1 quality on all of them.

## Decisions already made (Phase 0 / 1 / 1.5)

For context — the design assumes these are non-negotiable:

- **Open WebUI** is the primary UI (already running, hardened).
- **Ollama** is the LLM backend (CPU-only on Zen 4 + AVX-512; ~5 tok/s
  for 7B Q4 is the budget).
- **Qdrant** is the vector store (4 collections, 1 377 points, API key
  enforced).
- **`intfloat/multilingual-e5-small`** is the embedding model. Not
  swapping in v1.
- **`BAAI/bge-reranker-v2-m3`** is the reranker. Already proven to lift
  top-6 from 80 % to 95 % on the guardian_cloud benchmark.
- **Guardian Cloud backend is production** — read-only RAG only.

## Decisions still to make (for the user)

These are explicit unknowns the implementation roadmap will pause on:

1. **Tool-calling LLM:** `qwen2.5:7b-instruct` (recommended) vs
   `llama3.1:8b-instruct` (alternative). Defaults applied in design.
2. **HA control allowlist:** which domains the assistant can invoke. v1
   recommendation is conservative (lights, scenes, climate, scripts);
   anything else asks the user.
3. **Audit corpus:** include or exclude? v1 recommendation: include as a
   separate `infra_audits` collection. Single-user posture makes this
   safe; documented in security model.
4. **MyFreeTour source:** still unknown. Placeholder in `corpora.yaml`
   already exists.
5. **HA Long-Lived Access Token:** to be issued by the user via the HA
   UI, then stored in `/home/diego/homelab/ai-stack/.env`. No way to
   automate the creation; documented in the roadmap.

## What is **not** in this package

- Concrete Python code for the tools. The catalog gives function
  signatures, JSON schemas, error semantics, and pseudocode. Real code
  lands during implementation.
- Container images for new services. The roadmap describes the
  containerization of `homelab-tools` but does not ship a Dockerfile.
- New compose files. Same.
- A model-pull script. The roadmap step "pull qwen2.5:7b-instruct" is a
  one-line `docker exec`.

This is on purpose: design first, build second. The user explicitly
asked for "design and implementation plan, do not implement anything".
