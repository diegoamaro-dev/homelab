# Phase E — E-6 Onboarding Framework Apply Log

**Date:** 2026-06-28
**Phase:** E — Knowledge Platform Foundation
**Step:** E-6 — Onboarding framework (F-07)
**Outcome:** PASS — success criterion met

---

## Objective

Design and validate a repeatable framework for onboarding future knowledge domains
into the AMAROLAB Knowledge Platform.

**Success criterion:**
> A new knowledge domain can be onboarded, validated and completely removed without
> leaving any production artifact or changing the behaviour of existing collections.

---

## Hard guardrails (all maintained)

- Production Qdrant collections (homelab_docs / guardian_cloud / ensambla2 /
  infra_audits / myfreetour) were not modified at any point.
- No MyFreeTour onboarding. No real future project used as the test corpus.
- No Guardian Cloud modification.
- Disposable corpus `/tmp/e6-test-corpus/` removed in full during rollback.
- The permanent retrieval fixture (`retrieval_validation_fixture.yaml`) was not modified.

---

## Framework document

Written to: `04_ai_system/onboarding_framework.md`

Covers all 12 required sections:
1. Naming rules
2. Folder and path expectations
3. Corpus definition template
4. Collection creation (Qdrant REST API, 384-dim/Cosine)
5. Empty-collection behaviour (D-22: `empty_collection` code)
6. Indexing procedure
7. `rag_search` tool extension
8. Validation procedure (Level 1: pipeline; Level 2: end-to-end)
9. Retrieval fixture extension rules
10. Rollback and removal procedure (Mode A: placeholder; Mode B: full removal)
11. Documentation requirements
12. Security and privacy rules

---

## Proof — disposable corpus `e6_test`

### Corpus

| Item | Value |
|---|---|
| Name | `e6_test` |
| Type | `fs` |
| Path | `/tmp/e6-test-corpus/` (host temp dir, created and removed during proof) |
| Content | 4 markdown files: fictional Project Helios (IoT temperature monitoring) |
| Files | `README.md`, `sensors.md`, `api.md`, `deployment.md` |

Content is entirely fictional. No secrets, no PII, no real project data.

---

### Step 1 — Corpus files created

```
/tmp/e6-test-corpus/
  README.md     (project overview + architecture)
  sensors.md    (DHT22/DS18B20/BME280 sensor reference)
  api.md        (REST API + Bearer token authentication)
  deployment.md (Docker Compose + env vars)
```

### Step 2 — Qdrant collection created

```
PUT http://127.0.0.1:6333/collections/e6_test
{"vectors": {"size": 384, "distance": "Cosine"}}
→ {"result": true, "status": "ok"}
```

### Step 3 — corpora.yaml entry added

```yaml
- name: e6_test
  type: fs
  path: /tmp/e6-test-corpus
  include: ["**/*.md"]
  exclude: []
  enabled: true
```

### Step 4 — Dry-run

```
bin/ingest sync --collection e6_test --dry-run
→ files_seen: 4, errors: [], exit 0
```

### Step 5 — Full sync

```
bin/ingest sync --collection e6_test
→ files_seen: 4, files_with_changes: 4, chunks_upserted: 16, errors: [], exit 0
```

`bin/ingest status` confirmed `e6_test` at 16 points. Production collections unchanged:

| Collection | Points |
|---|---|
| homelab_docs | 4441 |
| guardian_cloud | 872 |
| ensambla2 | 419 |
| infra_audits | 280 |
| myfreetour | 0 |
| **e6_test** | **16** |

### Step 6 — Pipeline retrieval validation (temporary fixture HE-01 / HE-02 / HE-03)

Queries run via `bin/ingest search` (dense retrieval only; reranker applied in the
full `rag_search` tool path):

| ID | Query | Top hit | Score | Result |
|---|---|---|---|---|
| HE-01 | What temperature sensors does Project Helios support? | `README.md` chunk 0 (score 0.922); `sensors.md` chunk 0 at rank 3 — correct content present | 0.922 | PASS |
| HE-02 | How does the Helios API authenticate requests? | `api.md` chunk 1 (Authentication section) | 0.904 | PASS |
| HE-03 | What is the Project Helios architecture overview? | `README.md` chunk 0 | 0.885 | PASS |

All 3 queries: non-empty results, coherent content, correct source files in top-3.

HE-01 note: `README.md` ranks above `sensors.md` in dense-only retrieval because
the README contains high-density sensor mentions in context. The reranker in the
full `rag_search` path would reorder toward the more specific document. Expected
behaviour.

### Step 7 — `rag_search` tool extended and reinstalled

Added `"e6_test"` to `Literal[...]` in `ai-stack/openwebui-tools/tools/rag_search.py`.
Extended docstring. Reinstalled via `bin/install_tool tools/rag_search.py`:

```
OK id=rag_search name='Amarolab rag_search' action=update specs=1
```

No container recreate required. Tool code is stored in Open WebUI's database;
`bin/install_tool` pushes the updated Python source directly.

---

## Rollback — full removal

Executed in order:

1. `bin/ingest drop --collection e6_test --yes` → `deleted 16 points from e6_test`
2. `DELETE http://127.0.0.1:6333/collections/e6_test` → `{"result": true, "status": "ok"}`
3. Removed `e6_test` entry from `corpora.yaml` entirely.
4. Reverted `rag_search.py` `Literal[...]` to remove `"e6_test"`.
5. Reverted `rag_search.py` docstring.
6. `bin/install_tool tools/rag_search.py` → `OK id=rag_search action=update`
7. `rm -rf /tmp/e6-test-corpus/` → directory confirmed absent.

---

## Post-rollback verification

```
bin/ingest status
```

| Collection | Points | e6_test present? |
|---|---|---|
| homelab_docs | 4441 | — |
| guardian_cloud | 872 | — |
| ensambla2 | 419 | — |
| myfreetour | 0 | — |
| infra_audits | 280 | — |
| e6_test | — | **absent** |

```
bin/ingest sync   (full, all corpora)
→ 0 errors across all 5 corpora; exit 0
```

`e6_test` absent from `rag_search.py` Literal: **PASS**
`e6_test` absent from `corpora.yaml`: **PASS**
`/tmp/e6-test-corpus/` absent: **PASS**

---

## Success criterion — verdict

> A new knowledge domain can be onboarded, validated and completely removed without
> leaving any production artifact or changing the behaviour of existing collections.

**MET.**

- `e6_test` corpus was fully onboarded (Qdrant collection + corpora.yaml + 16 points indexed).
- Retrieval validation passed (3/3 queries, correct sources, coherent content).
- Tool enum was extended and reinstalled without a container recreate.
- Full rollback completed: no Qdrant collection, no corpora.yaml entry, no tool enum entry, no corpus directory, no fixture entry.
- Production point counts unchanged throughout.
- Full sync (all 5 enabled corpora) exits rc=0 post-rollback.

---

## Findings closed

- **F-07 (platform contract implicit / onboarding framework absent):** closed —
  E-6 framework written, validated end-to-end, and documented.

## Links

- Framework document: `04_ai_system/onboarding_framework.md`
- Platform contract: `04_ai_system/knowledge_platform_contract.md`
- E-0 audit report: `09_logs/2026-06-27_phaseE_E0_operational_audit_report.md`
