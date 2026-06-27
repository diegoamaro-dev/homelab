# Knowledge Platform Contract

- **Status:** Standing reference. Describes **deployed reality** of the
  AMAROLAB knowledge platform as of 2026-06-27.
- **Authored:** Phase E — Knowledge Platform Foundation, step E-1 (from
  finding F-07: the contract was previously implicit, living only in code).
- **Authority:** This document records what is deployed. If it disagrees
  with the running system, the running system wins and this document is
  corrected (per `00_overview/PROJECT_RULES.md`).

The "knowledge platform" is the retrieval substrate shared by AURORA's two
front doors: the **ingest pipeline** → **Qdrant index** → **`rag_search`
Tool**. This contract is the stable surface a future knowledge domain
onboards against (see the E-6 onboarding framework).

---

## 1. Components

| Component | Location | Runtime |
|---|---|---|
| Ingest pipeline | `ai-stack/ingest/` (CLI `bin/ingest`) | Python venv on the UM790 host; nightly cron |
| Vector store | Qdrant container; data at `ai-stack/data/qdrant` → `/qdrant/storage` | `qdrant` container |
| Retrieval Tool | `ai-stack/openwebui-tools/tools/rag_search.py` | runs **inside** the `openwebui` container; imports the ingest package from the `/opt/ingest` (ro) bind-mount |

---

## 2. Embedding & rerank contract (locked — D-08)

- **Embedder:** `intfloat/multilingual-e5-small` — **384-dim**, batch 32.
  E5 prefixes are mandatory and enforced in `ingest/embedder.py`:
  `passage: ` at index time, `query: ` at retrieval time.
- **Reranker:** `BAAI/bge-reranker-v2-m3` (CrossEncoder). Retrieval pulls
  `DENSE_N=30` dense candidates from Qdrant, then reranks to top-k.
- **Distance:** Cosine.
- **Shared model cache:** `/srv/homelab/data/openwebui/cache/embedding/models`
  (used by both the ingest venv and the openwebui container).

> **Do not** change the embedder/reranker model or alter outputs without a
> deliberate re-embed migration of **every** collection. The models are
> locked for v1 (D-08).

### Runtime version reality (finding F-02, live-confirmed 2026-06-27)

| Path | sentence-transformers | torch |
|---|---|---|
| Index / passage (ingest venv) | 3.4.1 | 2.12.0+cpu |
| Query / rerank (openwebui container) | 5.2.3 | 2.9.1+cpu |

Passages and queries are currently embedded under **different** library
stacks. Whether this skew moves retrieval ranking is **measured in E-5**
(`E5-a`); any version action (pin or unify) is taken **only if** that
measurement shows real drift.

---

## 3. Collection shape & payload schema

Every corpus is one Qdrant collection of the same name, created at
**384-dim / Cosine**. Each point carries this payload:

```
collection     # corpus name
source_path    # absolute path on the host
source_rel     # path relative to the corpus root (used for citations + idempotency)
source_kind    # markdown | yaml | conf | code | … (from corpora.yaml source_kind_map)
chunk_index    # 0-based index of this chunk within its source file
chunk_count    # total chunks for that file
content        # the chunk text (≤ ~600 chars target)
content_sha    # sha256 of the chunk content (idempotency key)
modified_at    # file mtime
title          # derived document title
```

- **Deterministic point ID:** `uuid(sha256(collection|source_rel|chunk_index))`.
- **Chunking:** 600 chars target, 80-char overlap.

### Live collection inventory (2026-06-27)

| Collection | Points | Enabled | Source |
|---|---:|---|---|
| `homelab_docs` | 4049 | yes | `fs` — `/home/diego/homelab` |
| `guardian_cloud` | 872 | yes | `git` — read-only over Guardian Cloud docs (D-09) |
| `ensambla2` | 419 | yes | `git` |
| `infra_audits` | 280 | yes | `fs` |
| `myfreetour` | 0 | **no** | `git` — **placeholder** for a future consumer project (path TBD, blocker B-08) |

---

## 4. Idempotency & sync semantics

- Per-chunk `content_sha` is compared against what is already stored;
  unchanged chunks are skipped (no embed, no write).
- A shrunk file has its old points dropped and is fully re-embedded.
- Points for files that no longer exist on disk are garbage-collected at
  the end of a run.
- `git` corpora run a `git pull` at sync time; `fs` corpora walk the host
  path directly. A read-only walk is available via `bin/ingest sync
  --dry-run` (no embed, no upsert — but **note** the `git` corpora still
  pull, so dry-run is only side-effect-free for `fs` corpora).

---

## 5. Operational invariants

- **Nightly sync:** cron `30 2 * * *` runs `bin/ingest sync` (before the
  03:00 restic backup). Indexing is **batch**, not real-time — intra-day
  staleness up to ~24 h is expected (finding F-03).
- **Backup:** the Qdrant data dir is included in the nightly restic backup
  (`/etc/cron.d/homelab-backup`, 03:00). Restore-consistency of a hot
  Qdrant copy is unverified (findings F-05a/F-05b).
- **L-RTX-5 (bind-mount recreate):** `rag_search` and the ingest package
  are bind-mounted read-only into `openwebui` at `/opt/ingest`. Editing
  that code on the host and reloading serves the **old** code — a change
  requires an `openwebui` **container recreate**, not a reload.
- **`rag_search` placeholder behaviour (D-22):** a query against a 0-point
  collection returns `{"hits": [], "code": "empty_collection"}` so the LLM
  apologises cleanly instead of silently picking another corpus.

---

## 6. Onboarding a new knowledge domain (summary)

The full, validated procedure is the **E-6 onboarding framework**. In
short, a future domain (e.g. MyFreeTour) onboards by: adding a `corpora.yaml`
entry (type `fs`/`git`, path, include/exclude, `enabled: true`); ensuring
the collection exists at 384-dim/Cosine; extending the `rag_search` Tool's
`collection` enum and **recreating** the `openwebui` container (L-RTX-5);
running `bin/ingest sync --collection <name>`; and validating retrieval.
No platform-contract value above changes when a domain onboards.
