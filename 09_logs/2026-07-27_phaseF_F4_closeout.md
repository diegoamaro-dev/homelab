# F-4 — Operational Intelligence · phase closeout (F-4 CLOSED)

- **Phase / milestone:** F — Operational Intelligence · **F-4 closeout** (authority:
  [`04_ai_system/phase_f_architecture.md`](../04_ai_system/phase_f_architecture.md)
  §9-F-4, AD-04/AD-14…AD-18).
- **Date:** 2026-07-27.
- **Scope:** close F-4 on **real operational evidence** — record the empirical **G-F4-08**
  restore-drill and the production-equivalent **G-F4-05** validation; declare F-4 CLOSED.
  **Documentation-only** (no code/prompt/tool/schema/DB change). **STOP at the git gate.**
- **Status:** **F-4 CLOSED.** All acceptance gates pass on real evidence.

## Gate ledger (all real data — no synthetic fixtures)

| Gate | Status | Evidence |
|---|---|---|
| G-F4-01/02/03/04/09 + repro | **PASS** | F4.3, 2026-06-30 (`2026-06-30_phaseF_F4_3_closeout.md`) |
| **G-F4-05** date-anchored (key gate) | **PASS** | reranked retrieval **24/24** indexed digests top-1 (below) |
| **G-F4-06** same-night honesty | **PASS** | deterministic F-3a `outlet` (`2026-07-27_phaseF_gf406_deterministic_disclosure.md`) |
| **G-F4-07** degraded night | **PASS** | real deviations in `notable`, retrievable by description (below) |
| **G-F4-08** durability | **PASS** | empirical restic restore-drill (below) |

## G-F4-08 — empirical durability evidence (operator/root, sanitized)

Latest nightly snapshot **`7715bf6a`** (2026-07-27 01:00:02Z, tag `nightly`).

1. **In the restic set:** `restic ls 7715bf6a /home/diego/homelab/09_ops/runtime` lists the
   `*_ops_digest.md` files → conjunct (a) satisfied.
2. **Restore-drill (recoverability):** `restic restore 7715bf6a --target /tmp/gf408-restore-drill
   --include …/09_ops/runtime` → `Restored 29 files/dirs`; **24** `*_ops_digest.md` recovered
   (`2026-06-29 … 2026-07-26`) at `/tmp/gf408-restore-drill/home/diego/homelab/09_ops/runtime`.
   Temp dir removed afterwards; production untouched.
3. **Missing-source GC (non-privileged dry-run):** `ingest sync --collection ops_digests
   --dry-run` → `files_deleted: 0, points_deleted: 0` with all sources present. The GC
   (`pipeline.py`) deletes only `source_rel`s absent on disk; a restore repopulates them, so
   `ops_digests` is not wiped → conjunct (b) satisfied.

**Restored count = 24, not 25 (recorded intentionally):** the nightly backup runs at 01:00 UTC;
the nightly digest is generated later (~02:15 UTC). So `2026-07-27_ops_digest.md` post-dates
snapshot `7715bf6a` and is expected to be absent from it — it enters the next nightly snapshot.
This is correct, not a durability gap.

### Restore-drill false negative (recorded per operator request)

The first verification — `sudo ls -1 /tmp/gf408-restore-drill/…/runtime/*_ops_digest.md` —
returned "No such file or directory" **despite a successful restore**. **Root cause:** the
`*_ops_digest.md` glob is expanded by the **unprivileged shell before `sudo` runs**; the
restore tree was created by root with restrictive permissions, so the unprivileged shell could
not traverse it, the glob stayed literal, and `ls` reported the literal pattern as missing. It
was a **verification-method artifact, not a restore failure** — confirmed by re-running the
traversal entirely as root (`sudo find …` / `sudo bash -c 'ls …'`), which located all 24 files
at the expected path.

## G-F4-05 — production-equivalent validation (key gate)

`bin/ingest search` is **dense-only** (`store.query`, no reranker); production `rag_search`
adds `bge-reranker-v2-m3` over `DENSE_N=30` candidates (AD-17). The gate must be judged on the
**reranked** path. Replicating it (dense-30 → reranker → top-1) over all indexed digests:
**24/24 correct top-1** (`2026-06-29 … 2026-07-26`). `2026-07-27` is **not indexed** (AD-04
~22 h lag) so its date query returns the nearest (`2026-07-26`) — the expected same-night
behaviour, consistent with G-F4-06, **not** a defect. This matches the G-F4-06 browser control
(`la noche del 20 de julio` → correct `2026-07-20`), so **no contradiction** between the
reranked path and the browser evidence. A dense-only CLI artifact (`2026-07-10 → 2026-07-20`)
is corrected by the reranker (`2026-07-10 → 2026-07-10`).

## G-F4-07 — degraded night

Real deviation nights are captured in `notable` (e.g. `2026-07-10` "audit stale";
`awning_left_extended` across many nights) and are retrievable by description
(`rag_search(ops_digests)` "night the awning was left extended" → a real awning night).

## Lessons learned

1. **Privileged restore verification + shell globs.** When verifying root-created trees, run the
   whole traversal/glob as root (`sudo find …`, `sudo bash -c 'ls …'`). A glob in
   `sudo ls DIR/*.ext` is expanded by the unprivileged shell first; over a root-owned tree it
   silently fails and looks like a missing file — a false negative. Confirm with an authoritative
   root-side traversal before concluding.
2. **Dense-only CLI ≠ reranked production for retrieval gates.** `bin/ingest search` skips the
   reranker; judging a retrieval gate on it can produce false misses. Validate retrieval gates on
   the reranked (`rag_search`-equivalent) path.
3. **Mandatory guarantees belong in deterministic orchestration, not probabilistic prompting**
   (from the G-F4-06 closeout) — carried forward.

## Rollback / notes

Documentation-only; nothing to roll back. The restore-drill wrote only to a temp dir (removed).
No production data, digest, collection, or config was modified during F-4 closure.

## Git gate (STOP — operator approval required before any git command)

Pending working-tree changes for review:

- `04_ai_system/phase_f_architecture.md` — G-F4-05/07/08 PASS markers, as-built status → **F-4
  CLOSED**, header status, §15 revision entry.
- `00_overview/CURRENT_STATE.md`, `00_overview/ROADMAP.md`, `00_overview/AMAROLAB_HANDOFF.md` —
  F-4 status → CLOSED.
- `09_logs/2026-07-27_phaseF_F4_closeout.md` — this log.

Runtime-only (never git): `ops_digests` Qdrant collection; `09_ops/runtime/*.md`; the restic
repository; the audit log. No secrets or restic passphrase appear in any artifact.
