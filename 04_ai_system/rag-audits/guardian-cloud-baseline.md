# RAG audit — `guardian_cloud`

- **Date:** 2026-06-14
- **Collection:** `guardian_cloud` in Qdrant 1.17.0
- **Index state at audit:** 56 distinct files, 872 chunks, 384-dim cosine
- **Embedding model:** `intfloat/multilingual-e5-small` (passage/query prefixed)
- **Method:** Read-only. 20 questions across 5 categories, top-6 retrieved
  per question, top-1 / top-3 / top-6 accuracy scored against an expected
  source file picked by reading the actual on-disk docs.
- **Raw artefacts:** [`gc_benchmark_2026-06-14.py`](gc_benchmark_2026-06-14.py)
  (the script) and [`gc_benchmark_2026-06-14.json`](gc_benchmark_2026-06-14.json)
  (raw top-6 per question).

## TL;DR

| Metric | Result |
|--------|-------:|
| **Top-1 accuracy** | **14 / 20 = 70 %** |
| Top-3 accuracy | 15 / 20 = 75 % |
| Top-6 accuracy | 16 / 20 = 80 % |
| Avg top-1 cosine | **0.8653** |
| Genuine "no answer in corpus" | 1 / 20 (Q16 — file exists but is 0 bytes) |
| Multilingual correctness | 6 / 6 Spanish queries returned the right doc when one existed; mixing langs works fine |

**One systemic failure mode dominates:** `docs/IMPLEMENTATION_STATUS.md` is a
status checklist that mentions every feature once, so it consistently
out-scores deeper single-topic docs on broad queries. 5 of the 6 failures
were caused by it.

## Methodology

### Question design

20 questions in 5 categories of 4 each. Languages mixed (12 EN / 8 ES). Each
question targets one specific file I could verify by reading the source on
disk first. Spanish questions are real ES that any Spanish-speaking
developer might write; English questions are likewise idiomatic.

Categories:

1. **Architecture** — high-level structure, protection model, invariants, data flow
2. **Deployment** — Cloudflare tunnel, release checklist, Play Store, implementation order
3. **Recovery** — cross-device recovery, kill-during-upload, scaffold rebuild, v0.2 background
4. **Chunk upload** — NAS WebDAV, errors/retries, API chunks, evidence export
5. **Backend** — endpoints, threat model, chunk security, anti-patterns

### Scoring

For each query I asked Qdrant for top-6 results (cosine score over
multilingual-e5-small embeddings of the question with the `query: ` prefix).
For each, I recorded:

- **`top1_source`**: the source_rel of the highest-scoring hit
- **`top1_score`**: its cosine similarity
- **`expected_rank`**: position of the expected doc in top-6, or `MISS`
- **`top_3_hit` / `top_6_hit`**: booleans

A "hit" is "the expected source_rel appears in top-N". Top-1 accuracy is
the strictest measure of whether the assistant would pick the right doc
without re-ranking.

## Per-category aggregates

| Category | n | Top-1 | Top-3 | Top-6 | Avg top-1 score |
|----------|--:|------:|------:|------:|---------------:|
| Architecture | 4 | **4/4** | 4/4 | 4/4 | 0.8634 |
| Deployment | 4 | 3/4 | 3/4 | 4/4 | 0.8581 |
| Recovery | 4 | **2/4** | 2/4 | 2/4 | 0.8618 |
| Chunk-upload | 4 | 2/4 | 3/4 | 3/4 | 0.8728 |
| Backend | 4 | 3/4 | 3/4 | 3/4 | 0.8704 |
| **Overall** | **20** | **14/20 (70 %)** | **15/20 (75 %)** | **16/20 (80 %)** | **0.8653** |

Architecture is solid: every architectural query lands the right file.
Recovery is the **weakest band** (50 % top-1) and chunk-upload misses the
0-byte file (Q16) plus a near-miss on Q15.

## Per-question results

|  # | Cat | Lang | Question | Expected | Top-1 actual | Rank |
|---:|-----|:----:|----------|----------|--------------|:----:|
|  1 | arch | en | High-level architecture of the mobile app | `docs/ARCHITECTURE.md` | `docs/ARCHITECTURE.md` | **1 ✓** |
|  2 | arch | es | ¿Cuáles son los estados de protección? | `docs/PROTECTION_MODEL.md` | `docs/PROTECTION_MODEL.md` | **1 ✓** |
|  3 | arch | en | System invariants | `docs/SYSTEM_INVARIANTS.md` | `docs/SYSTEM_INVARIANTS.md` | **1 ✓** |
|  4 | arch | en | Data flow from app to final storage | `docs/ARCHITECTURE.md` | `docs/ARCHITECTURE.md` | **1 ✓** |
|  5 | depl | es | ¿Cómo configuro el túnel de Cloudflare? | `docs/CLOUDFLARE_TUNNEL_SETUP.md` | `docs/CLOUDFLARE_TUNNEL_SETUP.md` | **1 ✓** |
|  6 | depl | en | Pre-flight checks for release v0.3 | `docs/RELEASE_CHECKLIST_v0.3.md` | `docs/RELEASE_CHECKLIST_v0.3.md` | **1 ✓** |
|  7 | depl | en | Play Store release plan | `strategy/PLAYSTORE_RELEASE_PLAN.md` | `strategy/PLAYSTORE_RELEASE_PLAN.md` | **1 ✓** |
|  8 | depl | es | ¿Orden de implementación del rollout? | `docs/IMPLEMENTATION_ORDER.md` | `strategy/NAS_WEBDAV_DESIGN.md` | 5 |
|  9 | rec  | en | Cross-device recovery | `docs/CROSS_DEVICE_RECOVERY.md` | `docs/IMPLEMENTATION_STATUS.md` | **MISS** |
| 10 | rec  | es | ¿Qué pasa si la app es matada durante un upload? | `docs/RECOVERY_BETA_VALIDATION.md` | `docs/RECOVERY_BETA_VALIDATION.md` | **1 ✓** |
| 11 | rec  | en | Rebuild the mobile scaffold from scratch | `REBUILD.md` | `REBUILD.md` | **1 ✓** |
| 12 | rec  | en | What changed in v0.2 for background recovery? | `docs/STATE_v0.2_BACKGROUND_RECOVERY.md` | `docs/IMPLEMENTATION_STATUS.md` | **MISS** |
| 13 | up   | en | Chunks uploaded to NAS over WebDAV | `strategy/NAS_WEBDAV_DESIGN.md` | `strategy/NAS_WEBDAV_DESIGN.md` | **1 ✓** |
| 14 | up   | es | ¿Errores y reintentos en upload al NAS? | `strategy/NAS_WEBDAV_DESIGN.md` | `strategy/NAS_WEBDAV_DESIGN.md` | **1 ✓** |
| 15 | up   | en | What does the API spec say about chunks? | `docs/API_SPEC.md` | `docs/IMPLEMENTATION_STATUS.md` | 2 |
| 16 | up   | en | Evidence export & forensic preservation | `docs/EVIDENCE_EXPORT_AND_FORENSIC.md` (0 bytes) | `docs/IMPLEMENTATION_STATUS.md` | **MISS¹** |
| 17 | back | en | Backend endpoints in NAS WebDAV design | `strategy/NAS_WEBDAV_DESIGN.md` | `strategy/NAS_WEBDAV_DESIGN.md` | **1 ✓** |
| 18 | back | es | ¿Modelo de amenazas del backend? | `docs/SECURITY.md` | `docs/SECURITY.md` | **1 ✓** |
| 19 | back | en | Chunks secured in transit and at rest | `docs/SECURITY.md` | `docs/IMPLEMENTATION_STATUS.md` | **MISS** |
| 20 | back | en | Anti-patterns to avoid | `docs/ANTI_PATTERNS.md` | `docs/ANTI_PATTERNS.md` | **1 ✓** |

¹ Q16's expected source is 0 bytes — see "Missing / empty documents" below.
The RAG arguably did the right thing by surfacing `IMPLEMENTATION_STATUS.md`,
which actually *does* describe evidence export in one of its bullets.

## Failure analysis

### Pattern: the `IMPLEMENTATION_STATUS.md` magnet (5 of 6 failures)

`docs/IMPLEMENTATION_STATUS.md` is a 18-chunk status checklist that
explicitly names every feature once:

```
- Audio recording
- Chunk generation
- Real chunk upload to Google Drive
- Chunk metadata registration
- Persistent pending recovery state
- Recovery after app kill
- Recovery after device reboot
- Session completion
- Local cleanup after success
- Evidence export from a given session (download chunks via backend
  proxy, verify sha256, concatenate in order, write .m4a to
  documentDirectory, produce partial result when some chunks are
  missing/corrupt)
```

Each bullet is a short, dense, on-topic phrase that produces a very high
similarity to broad queries about that feature. The specialist docs
(`CROSS_DEVICE_RECOVERY.md`, `STATE_v0.2_BACKGROUND_RECOVERY.md`,
`SECURITY.md`, …) lose because their relevant chunks are diluted with
context (history, motivation, code samples).

Q9 example — query "How does cross-device recovery work in Guardian Cloud?":

| Rank | Score | Source |
|-----:|------:|--------|
| 1 | 0.8884 | `docs/IMPLEMENTATION_STATUS.md` |
| 2 | 0.8752 | `docs/TEST_RESULTS.md` |
| 3 | 0.8681 | `docs/IMPLEMENTATION_STATUS.md` (different chunk) |
| 4 | 0.8658 | `docs/ARCHITECTURE.md` |
| 5 | 0.8585 | `docs/IMPLEMENTATION_STATUS.md` (third chunk) |
| 6 | 0.8551 | `docs/DEBUGGING_RULES.md` |

The expected file `docs/CROSS_DEVICE_RECOVERY.md` does not appear in
top-6 at all, despite having a literal section called "Flujo completo" and
a heading match on "cross-device recovery". Three chunks of
`IMPLEMENTATION_STATUS.md` crowd the top six.

This is a textbook "summary doc beats specialist doc" failure in pure
dense retrieval, and it's the single highest-leverage thing to fix.

### Q8 — language-mismatch + competitor doc (Spanish)

Query (ES): "¿Cuál es el orden de implementación del rollout?". Expected:
`docs/IMPLEMENTATION_ORDER.md` (5 chunks). Got:
`strategy/NAS_WEBDAV_DESIGN.md` (55 chunks, with a "Cambios exactos en
mobile" section that uses similar "implementation order" language).

Two compounding causes:

- The expected doc is **tiny (5 chunks)** so it gets relatively few
  chances to dominate the top.
- The competing doc has many "implementación / orden" mentions across its
  55 chunks; one of those is closer in embedding space to "orden de
  implementación del rollout" than the dedicated 5-chunk file.

`IMPLEMENTATION_ORDER.md` still showed up at rank 5, so a re-ranker would
likely recover this query.

### Q15 — near-miss (rank 2)

Query: "What does the API spec say about chunks?". The expected
`docs/API_SPEC.md` appears at rank 2 with score 0.8355. Rank 1 is
`IMPLEMENTATION_STATUS.md` at 0.8437 (margin 0.0082). Same pathology as
above but borderline; any re-ranker or "prefer titles containing 'API'"
heuristic would fix it.

### Q16 — empty target file (genuine miss, but with caveat)

The expected source `docs/EVIDENCE_EXPORT_AND_FORENSIC.md` is a **0-byte
placeholder** on disk (mtime 2026-05-04). The walker correctly skips
empty files, so the RAG has no choice but to surface something else. What
it returns — `IMPLEMENTATION_STATUS.md` chunks describing evidence export
— is actually a usable answer to the question, just not the
"correct" file.

This is a **content gap, not a retrieval bug**. The doc should be filled
in or deleted; either way it shouldn't sit empty in the source tree.

## Missing / empty documents

Found via cross-referencing the on-disk file tree against the indexed
`source_rel` set:

| File | Bytes | Status | Effect |
|------|-----:|--------|--------|
| `docs/EVIDENCE_EXPORT_AND_FORENSIC.md` | 0 | empty placeholder | Q16 has no canonical answer |
| `playbook/UX_STRESS_RULES.md` | 0 | empty placeholder | Possibly duplicate of `docs/UX_STRESS_RULES.md` |

The walker explicitly skips empty / non-UTF-8 files, so both are not
"failures of the ingester" — they're upstream content gaps in
guardian-cloud. Action: either populate or remove the placeholders so the
git tree matches expectations.

## Weak collections — overall

Only one collection is in scope for this audit (`guardian_cloud`). Within
it, the weakest category is **Recovery (2/4 top-1)**. The pattern is the
same in every recovery miss: a specialist doc (`CROSS_DEVICE_RECOVERY.md`,
`STATE_v0.2_BACKGROUND_RECOVERY.md`) loses to
`IMPLEMENTATION_STATUS.md` whose bullet list happens to phrase the
feature very compactly.

If the same audit were run against `homelab_docs` or `ensambla2`, the
qualitative behaviour might differ — neither collection has an
equivalent "everything-mentioned-once" status doc.

## Suggested improvements

Ranked by leverage (effort vs accuracy gain), low-hanging fruit first.

### 1. Cross-encoder re-ranker on top-N — biggest win

Add `BAAI/bge-reranker-v2-m3` (multilingual, 568 M params) as a *post*-
retrieval re-ranker. Pull top-30 from Qdrant, re-score with the
cross-encoder, return top-6. Cross-encoders look at the query and each
candidate *together* and break ties in cases like Q15 (close score margin
of 0.008) and would push the dedicated doc above the dilution doc in Q9,
Q12, Q19 almost certainly.

Cost: ~600 MB RAM during inference, ~50–150 ms per query on CPU. Easy
to wire as a pure-Python post-processing step in `ingest/store.py`
or in the soon-to-build `rag_search` tool.

Expected lift: top-1 from ~70 % to ~88–95 %.

### 2. Down-weight `IMPLEMENTATION_STATUS.md` (and similar status docs)

Three options, from cheapest to best:

- **a. Source-rel allowlist priority filter:** when the query contains a
  feature noun, prefer source_rels under `docs/` that don't match
  `*STATUS*`. Brittle.
- **b. BM25 hybrid:** combine cosine with BM25 sparse retrieval. Status
  docs win on cosine because of phrase density; BM25 with TF-IDF
  normalisation penalises them. Qdrant 1.10+ supports hybrid out of the
  box.
- **c. Chunk-budget metadata:** add a `is_status_index: true` payload
  field on chunks coming from known checklist docs, and apply a -0.05
  cosine penalty in the retrieval tool (not in storage). Discoverable
  and easy to tune.

I'd pair (b) BM25 hybrid with (1) the cross-encoder. They address the
same problem from different angles and are complementary.

### 3. Larger embedding model (`BAAI/bge-m3`)

Switch from `multilingual-e5-small` (384 dim, 118 M params) to
`bge-m3` (1024 dim, 568 M params). bge-m3 is generally state-of-the-art
for multilingual dense retrieval and would compress less. Trade-off:
~5× the on-disk size per chunk, ~5× the RAM during inference, and
re-ingestion of all corpora.

Worth doing **after** (1) and (2) if accuracy still isn't where you
want it. Re-ingestion is incremental from a developer's point of view:
write the new collection name, run sync, validate, swap the search
tool's collection target.

### 4. Markdown structure-aware payload fields

Currently chunks know `chunk_index`, `chunk_count`, and `title` (= first
H1/H2). Adding the path of headings the chunk lives under (`section: ["3
Sesiones", "3.2 Chunks"]`) would help two things:

- The reader of the RAG result can see "chunk 5/21 of API_SPEC.md, in the
  Chunks section" which is great for downstream LLM citation.
- Future filtering (e.g. "find sections under 'Chunks' across all docs")
  becomes a payload filter, free of embedding cost.

Cheap to add to `chunker.py`. No infrastructure change.

### 5. Smaller chunks for status / checklist documents

`IMPLEMENTATION_STATUS.md` is 18 chunks today (it has 35 entries in the
results because individual chunks appear in many queries). A
600-character chunk in a bulleted list can encode 4–6 distinct features,
diluting each. A 200-character chunk would isolate each feature and let
the *correct* deep doc win on shared concepts.

Easiest path: an additional `chunk_size_override` per-corpus knob in
`corpora.yaml`, or a heuristic that detects "mostly bullets" and uses a
smaller chunker. Diminishing returns vs (1) and (2).

### 6. Populate or remove the two empty docs

`docs/EVIDENCE_EXPORT_AND_FORENSIC.md` and
`playbook/UX_STRESS_RULES.md` are 0 bytes. Q16 in this benchmark relied
on the former. This is an action for the guardian-cloud repo, not the
ingester.

## What this audit did **not** measure

- **Answer quality from the LLM**, only retrieval quality. A great
  retriever with a bad LLM still gives bad answers; a mediocre retriever
  with a great LLM can sometimes recover. Phase 4 will exercise the LLM
  side.
- **Cross-collection retrieval.** Every query was scoped to
  `guardian_cloud`. The real assistant will route across all four
  collections — that adds a routing accuracy question on top.
- **Latency or throughput.** All 20 queries returned in well under
  100 ms each; no real measurement needed yet.

## Reproducing the audit

```bash
cd /home/diego/homelab/ai-stack/ingest
./venv/bin/python /home/diego/server-audit-2026-06-13/rag-audits/gc_benchmark_2026-06-14.py \
  > /tmp/rerun.json
```

The script is self-contained. To extend it: append new tuples to the
`QUESTIONS` list at the top, keeping the `(category, lang, question,
expected_source_rel)` shape. Re-run to get the updated table.
