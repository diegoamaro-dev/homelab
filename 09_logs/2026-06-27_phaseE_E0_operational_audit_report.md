# Phase E — Knowledge Platform Foundation
## E-0 Operational Audit Report (permanent)

- **Phase:** E — Knowledge Platform Foundation.
- **Step:** E-0 — Operational audit (read-only).
- **Date:** 2026-06-27.
- **Gate:** G-E0 — **CLOSED 2026-06-27** (operator-approved).
- **Document type:** Permanent audit record. This is the **evidence base
  from which the entire E-1 → E-6 backlog was derived**. It is not an
  implementation log; the chronological evidence lives in this thread and
  in the apply logs.
- **Method:** strictly read-only. Zero mutations.

---

## 1. Method & attestation

The audit was conducted strictly read-only, from two evidence sources:

- **Direct read-only probes:** filesystem/code reads; `crontab -l`;
  `ingest status`; `ingest sync --dry-run` (fs corpora only); Qdrant REST
  GETs; `docker inspect`; `docker ps`; ingest-venv version introspection.
- **Operator-run read-only commands** for the privileged / container-exec
  items: `docker exec` version reads, `sqlite3 -readonly`, restic
  `snapshots` / `find`.

**Zero-mutation attestation:**

- Pre/post Qdrant point counts identical (4049 / 872 / 419 / 280 / 0).
- `ingest sync` was run **only** with `--dry-run`, **only** on the `fs`
  corpora (`homelab_docs`, `infra_audits`); the `git` corpora were never
  pulled, so the Guardian Cloud and Ensambla2 working trees were untouched.
- No container, config, collection, secret, or service was modified.
- **Guardian Cloud was not touched.**

---

## 2. Platform health snapshot (the baseline being founded)

- 5 Qdrant collections, all `status=green`, **384-dim / Cosine**:
  `homelab_docs` 4049 · `guardian_cloud` 872 · `ensambla2` 419 ·
  `infra_audits` 280 · `myfreetour` 0 (disabled).
- Nightly index cron live and functional (`30 2 * * *`); idempotent
  (content-sha compare; GC of vanished files).
- Ingest CLI healthy (editable-install remediation holding).
- `/opt/ingest (ro)` bind-mount into `openwebui` confirmed → the L-RTX-5
  container-recreate rule applies to any ingest change.
- Inference via healthy `ollama-proxy` (Torre primary + UM790 backup).
- 17 containers up; `qdrant` / `openwebui` / `ollama-proxy` healthy.

**The platform is fundamentally sound.** Findings concern robustness,
observability, and reproducibility — not breakage.

---

## 3. Platform contract captured (deployed reality)

- **Embedder:** `intfloat/multilingual-e5-small` (384-dim, batch 32); E5
  prefixes enforced (`passage:` at index, `query:` at search).
- **Reranker:** `BAAI/bge-reranker-v2-m3` (CrossEncoder); `DENSE_N=30` → top-k.
- **Chunking:** 600 chars, overlap 80.
- **Payload schema:** `collection, source_path, source_rel, source_kind,
  chunk_index, chunk_count, content, content_sha, modified_at, title`.
- **Point ID:** `uuid(sha256(collection|source_rel|chunk_index))` (idempotent).
- **Shared HF cache:** `/srv/homelab/data/openwebui/cache/embedding/models`.
- **Qdrant data dir:** `/home/diego/homelab/ai-stack/data/qdrant`.
- Full standing reference:
  [`../04_ai_system/knowledge_platform_contract.md`](../04_ai_system/knowledge_platform_contract.md).

---

## 4. Final findings register

| ID | Finding | Sev | → Step | Status |
|---|---|---|---|---|
| F-01 | No working failure signal: disabled `myfreetour` is modeled as an *error* → `cmd_sync` returns rc=1 **every** run; the cron ignores rc. A real failure is indistinguishable from a normal run. | Med-High | E-2 + E-3 | Confirmed |
| F-02 | **Compound environment skew, live-confirmed.** Index/passage path (ingest venv): `sentence-transformers 3.4.1` / `torch 2.12.0+cpu`. Query/rerank path (openwebui container): `sentence-transformers 5.2.3` / `torch 2.9.1+cpu` (operator-verified live 2026-06-27). Passages and queries embedded under different stacks; both libraries skewed. | Med | E-2 (pin) + E-5 (measure) | Confirmed (live) |
| F-03 | Index staleness is real and invisible: 16 `homelab_docs` files changed but not yet indexed at audit time; no freshness signal exists. | Med | E-3 | Confirmed |
| F-04 | `ingest.log` and `amarolab-audit.log` have no rotation (the *backup* log does, via `/etc/logrotate.d/homelab-backup`). | Low | E-4 | Confirmed |
| F-05 | **RESOLVED.** Repo `/mnt/storage/backups/restic`; the Qdrant data dir is an explicit backup path (`homelab-backup.sh`) and not excluded; scheduled nightly 03:00 via `/etc/cron.d/homelab-backup` (after the 02:30 sync); **liveness confirmed** — snapshots running nightly through 2026-06-27, Qdrant dir present in the repository. | — | — | Resolved |
| F-05a | The Qdrant store is backed up **hot/raw** (no quiesce or snapshot-API, unlike the SQLite `.backup` handling); restore-consistency is unverified. | Med | E-4 + E-5 | Open |
| F-05b | **No restore drill has ever been performed** (`07_operations/backups.md`); recoverability of the index is unproven. | Med | E-5 | Open |
| ~~F-05c~~ | ~~Backup liveness~~ | — | — | **Closed 2026-06-27** |
| F-06 | Documentation drift set (C-1…C-6): Phase-E naming collision; CURRENT_STATE HA→Ollama endpoint stale; README "cron not installed"; ROADMAP still named MyFreeTour + Improve RAG; CURRENT_STATE omitted indexing operational status. | Low-Med | E-1 | Confirmed (being resolved in E-1) |
| F-07 | Platform contract is implicit — lives only in code. | Low | E-1 + E-6 | Confirmed |
| F-08 | No run-lock / overlap guard on the nightly sync. | Low | E-2 | Confirmed |
| F-09 | `ollama-proxy` is a single point of failure in front of both front doors — **inference-plane, working as designed (RTX-1.6)**. Out of Phase E scope. | Info | — | Recorded |
| F-10 | Audit log stale since 2026-06-18; the RTX-1.6 tool-calling validation ran 2026-06-27 yet the log is unchanged → leans toward writes not landing post-recreate, **not conclusive**. | Med | E-3 + E-5 | Confirmed (root cause pending E-5) |

---

## 5. Backlog derivation (E-1 → E-6)

The E-1 → E-6 backlog was derived **solely** from the register in §4, with
these operator-approved planning adjustments (2026-06-27):

1. **E2-b** (version action) is **conditional and blocked on E5-a**;
   version pinning *or* unification is considered **only if E5-a measures
   real retrieval drift**. No drift → no version action.
2. **E5-a** (measurement) **runs first**, as the gate for E2-b.
3. **E4-b** is an **engineering spike only**; **"no change required" is an
   acceptable outcome.**
4. **F-10 is P2** until a controlled validation demonstrates an actual defect.

| Finding(s) | Step item(s) | Pri |
|---|---|---|
| F-06 | E1-a…E1-d (doc reconciliation) | P1/P2 |
| F-07 | E1-e (contract doc) + E6-a (onboarding framework) | P2 |
| F-01 | E2-a (fail-loud sync) + E3-b (run-health signal) | P1/P2 |
| F-02 | E5-a (measure) → conditional E2-b (pin/unify) | P1 / conditional |
| F-08 | E2-c (run-lock) | P3 |
| F-03 | E3-a (freshness signal) | P2 |
| F-10 | E3-c (audit-log liveness) + E5-c (controlled check) | P2 |
| F-04 | E4-a (log rotation) | P2 |
| F-05a | E4-b (backup-consistency spike) + E5-b (restore drill) | P2 |
| F-05b | E5-b (restore drill) | P1 |
| F-09 | — (no Phase E work) | Info |

**P1 spine:** E1-a → E2-a → E5-a → E5-b.

---

## 6. Gate G-E0

**CLOSED 2026-06-27 (operator-approved).** The finding register in §4 is the
**sole** source of the E-1 → E-6 backlog. No backlog item exists that does
not trace to a finding above (E-6 additionally derives from the approved
O-6 onboarding-framework charter).

---

## References

- Platform contract (standing reference):
  [`../04_ai_system/knowledge_platform_contract.md`](../04_ai_system/knowledge_platform_contract.md).
- Overview triad:
  [`../00_overview/ROADMAP.md`](../00_overview/ROADMAP.md) ·
  [`../00_overview/CURRENT_STATE.md`](../00_overview/CURRENT_STATE.md) ·
  [`../00_overview/AMAROLAB_HANDOFF.md`](../00_overview/AMAROLAB_HANDOFF.md).
- Backup script + policy:
  [`../07_operations/backups.md`](../07_operations/backups.md).
- RTX-1 retrospective (inherited dependencies):
  [`2026-06-27_phaseRTX1_retrospective.md`](2026-06-27_phaseRTX1_retrospective.md).
