# Aurora — Foundation Milestone

> **Milestone:** Aurora Foundation Milestone  
> **Date:** 2026-06-28  
> **Status:** Stable baseline. Knowledge platform complete. Operational intelligence (Phase F) begins next.

---

## What is Aurora?

Aurora is the operational AI assistant for **AMAROLAB** — a personal homelab running
self-hosted infrastructure, home automation, and active software projects on privately
owned hardware.

Aurora is not a general-purpose chatbot. It is an assistant that knows this specific
environment: its infrastructure, its documentation, its history, and its devices.
Aurora runs entirely on-premises. No conversation leaves the local network.

The Foundation Milestone marks the point where all core platform layers are
stable, validated, and internally consistent: the knowledge platform is indexed and
clean, the tool surface covers the principal use cases, and the system prompt routes
correctly. From this baseline, Phase F will add situational awareness, operational
memory, and home intelligence.

---

## Capabilities

### Knowledge retrieval

Aurora can search and reason over **7,500+ indexed document chunks** across five
corpora, using dense retrieval with cross-encoder reranking:

| Domain | What it covers |
|---|---|
| Current documentation | AMAROLAB infrastructure, AI stack, service configuration, architecture records, project contracts |
| Historical records | Phase logs, gate results, apply logs, closeout reports, decision rationale |
| Infrastructure audit | Phase 0/1 server audit reports; R-XX remediation records |
| Guardian Cloud | Project documentation for an active external software project (read-only) |
| Ensambla2 | Project documentation for a second active software project |

Retrieval uses `intfloat/multilingual-e5-small` (384-dim) for embedding and
`BAAI/bge-reranker-v2-m3` as a cross-encoder reranker over 30 dense candidates.
The embedder and reranker are locked at this milestone. Knowledge is indexed
nightly at 02:30 via an incremental ingest pipeline with per-chunk content
hashing (unchanged chunks are skipped; deleted files are garbage-collected).

### Home automation

Aurora can query and control Home Assistant:

- **State queries** — any entity in the HA instance (`ha_get_state`)
- **Device control** — 12 allowed domains, gate-validated per domain
  (`ha_call_service`): lights, switches, covers, climate, fans, locks, scenes,
  scripts, automations, media players, vacuum, and input booleans

All control operations go through an explicit allowlist enforced at the tool
boundary. Aurora cannot act outside the allowlist. No domain is added
speculatively; each requires a documented gate validation.

### Time and date

Aurora knows the current date, time, and weekday (`time_now`). It does not
substitute training-data estimates for live time queries.

### Voice interface

Aurora is accessible by voice through a Home Assistant voice pipeline:

- **Wake word:** always-on on a local device
- **Speech-to-text:** `faster-whisper` (`base-int8`)
- **Text-to-speech:** Piper
- **LLM:** same model as the chat interface — voice commands reach Aurora
  directly, not a separate smaller model

### Chat interface

Aurora is accessible through a self-hosted Open WebUI instance. The chat
interface supports multi-turn conversations, full tool access, document
retrieval with citations, and structured output.

### Infrastructure audit search

Aurora can search Phase 0/1 server audit reports and R-XX remediation records
through a dedicated tool (`audit_search`), separate from the main knowledge
search to prevent contamination of live documentation by historical audit content.

---

## Tool Inventory

| Tool | What it does | Routing guidance |
|---|---|---|
| `rag_search` | Semantic search across indexed knowledge corpora with reranking | Current docs, historical records, project documentation |
| `ha_get_state` | Live Home Assistant entity state (attributes filtered by allowlist) | Any "is X on/off/open?" query |
| `ha_call_service` | HA service call through 12-domain allowlist | Explicit control requests only |
| `audit_search` | Phase 0/1 infrastructure audit; R-XX remediation records | Audit findings, remediation status |
| `time_now` | Current date, time, weekday in requested timezone | Any time or date query |

---

## Architecture

### Hardware

| Node | Role | Key specs |
|---|---|---|
| Torre | Primary inference | RTX 5070; ~101 tok/s via Ollama |
| UM790 | Host for all services; CPU fallback inference | ~6 tok/s CPU-only |

### Software stack

```
┌─────────────────────────────────────────────────────────┐
│  Interfaces                                             │
│  ┌──────────────────┐  ┌────────────────────────────┐  │
│  │  Open WebUI      │  │  Home Assistant Voice      │  │
│  │  (chat)          │  │  Whisper + Piper + Wake    │  │
│  └────────┬─────────┘  └─────────────┬──────────────┘  │
│           │                          │                  │
│  ┌────────▼──────────────────────────▼──────────────┐  │
│  │  LLM: qwen2.5:7b-instruct                        │  │
│  │  Ollama proxy → Torre RTX 5070 (primary)         │  │
│  │                → UM790 CPU (fallback)             │  │
│  └────────────────────────────────────────────────┬─┘  │
│                                                   │    │
│  ┌────────────────────────────────────────────────▼─┐  │
│  │  Knowledge Platform                              │  │
│  │  rag_search tool → Qdrant → homelab-rag-ingest  │  │
│  │  Embedder: intfloat/multilingual-e5-small        │  │
│  │  Reranker: BAAI/bge-reranker-v2-m3              │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Home Automation                                 │  │
│  │  ha_get_state / ha_call_service → HA REST API   │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

All services run as Docker containers on the UM790 host (`docker compose`).
All data is stored on-premises. The system has no cloud dependencies for
inference or retrieval.

---

## Knowledge Layer

The knowledge platform is the architectural foundation that distinguishes Aurora
from a plain LLM. It indexes structured documentation into a vector database
and retrieves it at inference time, so Aurora's answers about AMAROLAB are
grounded in current documentation rather than training-data approximations.

### Design principle

The system prompt describes knowledge domains by intent. Collection names are
an implementation detail confined to the tool layer. This means the prompt
does not need to change when the corpus layout evolves.

### Corpus layout

| Collection | Points | Type | Content |
|---|---:|---|---|
| `homelab_docs` | 1,911 | `fs` | Living AMAROLAB documentation — current state of infrastructure, services, AI stack, contracts |
| `knowledge_history` | 2,918 | `fs` | Historical records from `09_logs/` — phase logs, gate results, apply logs, closeout reports |
| `guardian_cloud` | 872 | `git` | Guardian Cloud project documentation (read-only) |
| `ensambla2` | 419 | `git` | Ensambla2 project documentation |
| `infra_audits` | 280 | `fs` | Phase 0/1 server audit reports; R-XX remediation |
| `myfreetour` | 0 | `git` | Placeholder; disabled (path TBD) |

### Separation rationale

`homelab_docs` and `knowledge_history` are deliberately separate collections.
Historical records (phase logs, apply logs) can contain documented failures,
quoted incorrect answers, and negative examples that — if mixed with living
documentation — outrank authoritative current-state chunks on factual queries.
This failure mode was observed and corrected during Phase F-1 validation.

### Retrieval pipeline

1. Query is embedded with the E5 `query:` prefix
2. Qdrant returns 30 dense candidates (cosine similarity)
3. Cross-encoder reranker scores all 30 against the query
4. Top-k reranked chunks are returned with `source_rel` citation paths

---

## Current Limitations

### No situational awareness

Every conversation begins from zero. Aurora does not automatically know whether
the nightly backup succeeded, whether services are healthy, or what the current
home state is. These answers require explicit tool calls — which the 7B model
executes correctly, but the cost is interaction friction. **This is the primary
target of Phase F-2 through F-3.**

### No operational memory

Aurora cannot answer "what happened last night?" without the operator providing
the information or fetching it manually. There is no structured operational
digest, and no mechanism for Aurora to summarise and recall nightly events.
**Phase F-4 addresses this.**

### Narrow home model

The HA integration covers all domains and any entity, but Aurora has no
baseline model of expected home state. It answers point queries but cannot
reason about deviation from normal. For example, it can say whether the
printer is currently on, but has no sense of whether it should be.
**Phase F-5 addresses this.**

### Voice quality gap

Spanish short utterances are unreliable with the current `faster-whisper
base-int8` model. Longer Spanish sentences are accurate; one- or two-word
commands frequently misfire. **Phase F-6 addresses this.**

### No live call-log query

The audit log (`amarolab-audit.log`) records every tool call Aurora makes, but
no tool currently exposes this log for querying. "Show me what tools Aurora
called recently" is not currently answerable. This is documented as a future
capability.

### Same-night operational briefing

The nightly ingest runs at 02:30. Any operational digest generated the same
night is not yet indexed by RAG at 07:00 the following morning (approximately
22-hour indexing lag). Same-night briefing requires a live signal mechanism,
not RAG. **Phase F-2 and F-3 address this through a pre-generated context
file injected by a Filter, not through RAG.**

### No session continuity

Aurora does not remember previous conversations. Each session is independent.
Conversational memory is explicitly deferred to Phase G; implementing it
prematurely in the knowledge corpus would contaminate retrieval with noise.

---

## Completed Phases

### Phase A — Initial Integration
First Aurora deployment: initial system prompt, Open WebUI wired to Ollama, basic
conversational capability established. No knowledge retrieval; no HA integration.

### Phase B — Knowledge Platform Bootstrap
RAG integration: `homelab_docs`, `guardian_cloud`, and `ensambla2` corpora indexed.
`rag_search` tool deployed. Aurora can retrieve AMAROLAB and project documentation.

### Phase C — Home Automation Integration
`ha_get_state` and `ha_call_service` tools deployed. Domain allowlist defined and
gate-validated. Aurora can query HA entity state and control devices within the
allowlist.

### Phase D — Voice Pipeline
Home Assistant voice pipeline integrated: faster-whisper (STT), Piper (TTS), wake
word detection. Aurora accessible by voice. Sub-phases:
- **D-08:** Embedding model locked at `intfloat/multilingual-e5-small` (384-dim)
- **D-09:** Guardian Cloud corpus onboarded to the knowledge platform

### Phase E — Knowledge Platform Foundation
Systematic hardening of the retrieval substrate. Seven steps:
- **E-0:** Operational audit — 13 findings documented
- **E-1:** Knowledge platform contract written (embedder, reranker, schema, sync semantics)
- **E-2:** Sync exit-code contract (F-01) — disabled corpus treated as expected skip; genuine failure signals rc=1
- **E-3:** `audit_search` tool deployed; `infra_audits` corpus onboarded (Phase 0/1 audit reports)
- **E-4:** Backup consistency investigation — no change required; hot backup proven sufficient
- **E-5:** Validation — E5-a: version-skew drift measured (zero measurable drift, E2-b not triggered); E5-b: Qdrant restore drill (snapshot `228e4183`, 4/4 collections, fixture parity 16/16 PASS)
- **E-6:** Knowledge domain onboarding framework written

### Phase F — Operational Intelligence (in progress)

**F-0 — Behavioral Audit** *(complete 2026-06-28)*  
10-query behavioral baseline established (4/10 pass). 8 AF findings documented.
System prompt confirmed stale (822 tokens, 1/5 tools described correctly, 4 tools
actively refused as "not yet implemented"). Platform finding G-F1-01: Open WebUI
REST API does not auto-forward `meta.toolIds` as the `tools` parameter — explicit
`tools` parameter required in API calls.

**F-1 — System Prompt Redesign** *(complete 2026-06-28)*  
System prompt replaced (3,147 chars / ~450 tokens). Domain-based routing. All
5 tools described correctly. No stale phase references. Collection names removed
from prompt (implementation detail confined to tool layer). Knowledge-layer corpus
split: `homelab_docs` rebuilt clean (1,911 pts, `09_logs/` excluded);
`knowledge_history` created (2,918 pts from `09_logs/`). Validation: 4/4 API-level
routing PASS; 4/4 corpus hygiene and routing tests PASS.

---

## Major Architectural Decisions

**Knowledge-layer corpus separation.** Living documentation (`homelab_docs`) and
historical records (`knowledge_history`) are separate Qdrant collections. Historical
records may contain documented failures, quoted wrong answers, and negative examples
that contaminate factual retrieval when mixed with authoritative living docs.
Observed failure mode corrected in F-1.

**Domain-based routing in the system prompt.** The system prompt describes what
Aurora should do, not how the knowledge platform is implemented. Collection names
belong in the tool layer (`rag_search` docstring). This decouples prompt stability
from corpus layout evolution.

**Situational awareness is a platform capability, not a UI plugin (AD-01).** The
mechanism that gives Aurora current state must work for any consumer surface (chat,
voice, future API callers). A context generation script produces a canonical context
document; consumers read it. No domain logic in the interface layer.

**Automatic awareness via a Filter over a pre-generated file (AD-02).** Aurora
receives current lab state in the system message before message 1 — no tool call
required. A lightweight Open WebUI Filter reads a pre-generated markdown file and
prepends it. The Filter is intentionally dumb: it reads one file, prepends it, and
exits. Context construction logic lives in `bin/aurora-context`.

**Live state and pre-generated context are complementary, not competing (AD-03/04).**
The context file reflects "what was true at last generation" (nightly, 04:15). Live
probes (`system_status` tool) answer "what is true right now?". Same-night briefing
relies on live probes, not RAG. Historical retrieval (≥22h) relies on RAG. These
are distinct retrieval paths serving distinct needs.

**Operational digest is a runtime artifact, never a git artifact (AD-07).** No cron
job commits. The ingest pipeline walks the host filesystem directly — untracked,
gitignored files are indexed identically to committed files. This resolves the
conflict between automated digest generation and the operator git-approval constraint.

**Allowlist discipline.** `ha_call_service` domains are expanded only through
per-domain gate validation with documented evidence. No domain is added
speculatively.

**Embedding model locked (D-08).** `intfloat/multilingual-e5-small` (384-dim)
is locked. Changing the embedder requires a full re-embed migration of every
collection. The library version skew between the ingest venv (sentence-transformers
3.4.1) and the openwebui container (5.2.3) was measured in E5-a and found to
produce zero measurable retrieval difference.

---

## Next Objectives — Phase F Roadmap

| Sub-phase | Objective | Key deliverable |
|---|---|---|
| **F-2** | Signal layer | `backup_status.json`, `container_status.json`, `bin/aurora-context`; `system_status` tool |
| **F-3** | Situational awareness | Open WebUI Filter reads `aurora-context.md`; Aurora knows lab state at conversation start without tool call |
| **F-4** | Operational digest | `bin/generate-digest` produces nightly ops summaries; indexed by `homelab_docs`; RAG answers "what happened N days ago?" |
| **F-5** | Home intelligence | HA entity baseline model; home state section in context file; Aurora understands expected vs actual home state |
| **F-6** | Voice quality | STT model upgrade (medium or large); Spanish short utterance reliability |

**Phase F complete** when: briefing works (no terminal required after any absence),
action is frictionless (any home model device in one exchange), knowledge is
connected (operational events retrievable by RAG), and voice is reliable (Spanish
daily use without frustration).

**Phase G** (not yet designed): session continuity, proactive behaviour (morning
summaries, anomaly push notifications), possible model upgrade (qwen2.5:14b or
equivalent pending quality gap measurement).

---

## Infrastructure Snapshot

| Component | Value |
|---|---|
| LLM model | `qwen2.5:7b-instruct` |
| Inference primary | Torre / RTX 5070 / ~101 tok/s |
| Inference fallback | UM790 CPU / ~6 tok/s |
| Chat interface | Open WebUI 0.8.10 (self-hosted) |
| Voice pipeline | Home Assistant + faster-whisper base-int8 + Piper |
| Vector store | Qdrant 1.17 |
| Embedder | `intfloat/multilingual-e5-small` 384-dim (locked D-08) |
| Reranker | `BAAI/bge-reranker-v2-m3` |
| Ingest pipeline | `homelab-rag-ingest` — Python, nightly cron 02:30 |
| Total indexed chunks | ~7,500 across 5 active corpora |
| System prompt | 3,147 chars / ~450 tokens (F-1, 2026-06-28) |

---

## What Aurora Is Not

- Not a cloud service. All inference, retrieval, and storage is on-premises.
- Not autonomous. Aurora cannot expand its own action surface. Tool allowlists are
  operator-defined and operator-revised only.
- Not a home monitoring replacement. Aurora surfaces information; it does not
  replace dashboards, alerting, or backup verification with its own judgment.
- Not a general-purpose assistant. Answering questions outside the AMAROLAB
  domain is possible using training knowledge, but that is not the design target.
- Not multi-user. AMAROLAB is a single-operator system.

---

*Aurora Foundation Milestone. All core platform layers are stable. Operational
intelligence begins in Phase F-2.*
