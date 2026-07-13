# Phase E — E5-a — Retrieval Drift Measurement (F-02 version skew) — MEASURED

- **Date:** 2026-06-27
- **Phase step:** E5-a — measure whether the F-02 library-version skew between
  the two embedding stacks produces **measurable retrieval drift**. This is the
  pre-registered gate for the conditional E2-b (version pin/unify).
- **Ecosystem:** AMAROLAB — Personal Innovation Lab and Digital Infrastructure Ecosystem.
- **Assistant:** AURORA — Personal AI Assistant for the AMAROLAB ecosystem.
- **Independent project:** Guardian Cloud — **untouched** (its `guardian_cloud`
  collection was only **read** via Qdrant search; no git pull, no write).
- **Document type:** Measurement evidence record (permanent). Measurement only:
  **no version change, no pin, no migration, no re-embed, no dependency change,
  no container recreate, no config change, no writes.**
- **Conclusion:** **No measurable drift detected — no change required.** E2-b is
  **not** triggered.

---

## 1. Question

E-0 finding **F-02** (live-confirmed): passages and queries are embedded under
**different** library stacks.

| Path | sentence-transformers | torch | role |
|---|---|---|---|
| Index / passage (ingest venv) — **stack A** | **3.4.1** | **2.12.0+cpu** | embeds the stored passages |
| Query / rerank (openwebui container) — **stack B** | **5.2.3** | **2.9.1+cpu** | embeds the query at search time |

Both stacks reconfirmed **live** on 2026-06-27 (stack A on host; stack B via the
operator-authorized read-only `docker exec openwebui`). Does this skew change
what `rag_search` retrieves?

## 2. Methodology

- **Fixed variable / fixed corpus.** Stored passage vectors (stack A) are never
  re-embedded. The only variable is the **query** embedding stack. The query
  corpus is the permanent fixture
  [`../04_ai_system/validation/retrieval_validation_fixture.yaml`](../04_ai_system/validation/retrieval_validation_fixture.yaml)
  (16 queries — 4 per populated collection, 8 es / 8 en).
- **Two arms, same index.** For each fixture query: embed it under **stack A**
  (`qA`, the no-skew baseline consistent with the stored passages) and under
  **stack B** (`qB`, the production reality), then search the **same** live
  Qdrant collection with each.
- **Metrics (pre-registered).**
  - **M1 (root cause):** `cosine(qA, qB)`.
  - **M2 (decisive, production-relevant):** identity of the dense top-`DENSE_N=30`
    candidate **set** (by point id), top-30 order, top-6 order, and cosine-score
    deltas on shared points.
- **Why M2 set-identity is decisive.** Production reranks the dense top-30 with a
  cross-encoder over **(query_text, passage_text)** pairs, always in stack B. The
  query *text* is identical in both arms, so if the dense top-30 **set** is
  identical the reranked top-6 is provably identical — no need to run the
  reranker cross-stack.
- **Decision rule (pre-registered):** all queries with top-30 set identical
  **and** top-6 order identical **and** cosine ≥ 0.9999 ⇒ "No measurable drift —
  no change required"; otherwise report drift magnitude and flag E2-b.
- **Harness:**
  [`../04_ai_system/validation/measure_retrieval_drift.py`](../04_ai_system/validation/measure_retrieval_drift.py)
  (permanent, reusable for E5-b/E5-c).

## 3. Execution

1. Extracted the 16 fixture queries to JSON (host).
2. **Stack B** embeddings — read-only `docker exec openwebui python …` ran the
   **same** `ingest/embedder.Embedder` code in the container (live versions
   captured: ST 5.2.3 / torch 2.9.1+cpu) → `qB.json`. The ST 5.2.3 loader prints
   `embeddings.position_ids UNEXPECTED` (a benign non-persistent-buffer change;
   `position_ids` is a fixed `arange`, so embeddings are unaffected — quantified
   below).
3. **Stack A** embeddings + comparison — ran the harness under the ingest venv
   (ST 3.4.1 / torch 2.12.0): embed `qA`, read-only Qdrant search with `qA` and
   `qB` at `limit=30`, compute M1/M2.

## 4. Evidence

Per-query (all 16):

| id | collection | cosine(qA,qB) | top30 set= | top6 order= | Jaccard | common | max Δscore |
|---|---|---|---|---|---|---|---|
| HL-01 | homelab_docs | 1.00000000 | ✓ | ✓ | 1.000 | 30/30 | 1.6e-07 |
| HL-02 | homelab_docs | 1.00000000 | ✓ | ✓ | 1.000 | 30/30 | 1.4e-07 |
| HL-03 | homelab_docs | 1.00000000 | ✓ | ✓ | 1.000 | 30/30 | 1.3e-07 |
| HL-04 | homelab_docs | 1.00000000 | ✓ | ✓ | 1.000 | 30/30 | 1.4e-07 |
| GC-01 | guardian_cloud | 1.00000000 | ✓ | ✓ | 1.000 | 30/30 | 1.0e-07 |
| GC-02 | guardian_cloud | 1.00000000 | ✓ | ✓ | 1.000 | 30/30 | 1.4e-07 |
| GC-03 | guardian_cloud | 1.00000000 | ✓ | ✓ | 1.000 | 30/30 | 1.5e-07 |
| GC-04 | guardian_cloud | 1.00000000 | ✓ | ✓ | 1.000 | 30/30 | 1.2e-07 |
| E2-01 | ensambla2 | 1.00000000 | ✓ | ✓ | 1.000 | 30/30 | 1.7e-07 |
| E2-02 | ensambla2 | 1.00000000 | ✓ | ✓ | 1.000 | 30/30 | 1.4e-07 |
| E2-03 | ensambla2 | 1.00000000 | ✓ | ✓ | 1.000 | 30/30 | 1.5e-07 |
| E2-04 | ensambla2 | 1.00000000 | ✓ | ✓ | 1.000 | 30/30 | 2.6e-07 |
| IA-01 | infra_audits | 1.00000000 | ✓ | ✓ | 1.000 | 30/30 | 6.0e-08 |
| IA-02 | infra_audits | 1.00000000 | ✓ | ✓ | 1.000 | 30/30 | 1.4e-07 |
| IA-03 | infra_audits | 1.00000000 | ✓ | ✓ | 1.000 | 30/30 | 1.0e-07 |
| IA-04 | infra_audits | 1.00000000 | ✓ | ✓ | 1.000 | 30/30 | 1.0e-07 |

Aggregate: **all top-30 sets identical**, **all top-6 orders identical**,
**all cosine ≥ 0.9999**.

Full-precision root-cause stats (float64):

- `min = max = mean cosine(qA,qB) = 1.000000000000`; `1 − min_cosine = 2.25e-13`.
- `||qA − qB||₂` ∈ [3.93e-07, 6.71e-07]; **0/16 vectors exactly identical** →
  the two stacks produce genuinely *different* vectors, differing only at the
  **float32 noise floor (~1e-7 per component)**, with direction identical to
  ~1e-13. (Rules out an accidental qA=qB copy.)

**Negative control (methodology validation).** Comparing each query against a
*different* query's vector in the same collection: mean cosine **0.8221**
(range 0.74–0.89), top-30 set identical **0/16**. The harness **does** detect
difference when vectors truly differ — so the identical-retrieval result for the
real A-vs-B comparison is a genuine finding, not a broken comparator.

**Zero-mutation attestation.** Point counts identical before/after
(`homelab_docs` 4049 · `guardian_cloud` 872 · `ensambla2` 419 · `infra_audits`
280 · `myfreetour` 0). Only query-string embedding and read-only Qdrant searches
were performed.

## 5. Conclusion

**No measurable drift detected — no change required.** The F-02 library-version
skew changes query embeddings only at the float32 numerical-noise floor
(cosine identity to ~1e-13) and produces **byte-identical retrieval** (identical
dense top-30 sets and identical top-6 order) across all 16 fixture queries,
covering every populated collection in both languages.

Per the pre-registered backlog rule (E-0 §5: "version pinning *or* unification is
considered **only if** E5-a measures real retrieval drift. No drift → no version
action"), **E2-b is not triggered**. No version is pinned, unified, or migrated.

Residual: the skew remains a **reproducibility** note (documented in the platform
contract), not a retrieval-correctness issue. If the stacks are upgraded in
future, re-run this fixture before relocking.

> **Addendum (2026-07-13, per the 2026-06-27 operator decision — folded into
> the next doc reconciliation, no standalone commit):** this conclusion is
> scoped to the **current embedding model (`intfloat/multilingual-e5-small`)
> and retrieval pipeline** (E5 prefixes, dense top-30 → `bge-reranker-v2-m3` →
> top-6). Any **embedding-model replacement** — not just a library-version
> bump — invalidates it and requires re-running the fixture.

## 6. References

- Fixture:
  [`../04_ai_system/validation/retrieval_validation_fixture.yaml`](../04_ai_system/validation/retrieval_validation_fixture.yaml)
  ·
  [`../04_ai_system/validation/retrieval_validation_fixture.md`](../04_ai_system/validation/retrieval_validation_fixture.md).
- Harness:
  [`../04_ai_system/validation/measure_retrieval_drift.py`](../04_ai_system/validation/measure_retrieval_drift.py).
- E-0 audit (F-02 + backlog rule):
  [`2026-06-27_phaseE_E0_operational_audit_report.md`](2026-06-27_phaseE_E0_operational_audit_report.md).
- Platform contract (F-02 runtime version reality):
  [`../04_ai_system/knowledge_platform_contract.md`](../04_ai_system/knowledge_platform_contract.md).
