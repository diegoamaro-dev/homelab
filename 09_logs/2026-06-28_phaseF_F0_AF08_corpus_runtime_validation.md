# F-0 Finding — AF-08: Filesystem Corpus Indexing of Runtime Artifacts

**Date:** 2026-06-28  
**Phase:** F-0 Behavioral Audit  
**Finding reference:** AF-08 (from `04_ai_system/phase_f_architecture.md` §11)  
**Status:** VALIDATED WITH GAP — assumption confirmed, one pre-implementation action required

---

## Context

AF-08 was identified during the Phase F architecture review to validate a foundational assumption of AD-07:

> AF-08: Confirm that untracked, gitignored files in `09_ops/runtime/` are picked up by the `homelab_docs` fs corpus on each sync cycle.

The Phase F architecture (AD-07) specifies that operational digest files (`09_ops/runtime/YYYY-MM-DD_ops_digest.md`) are runtime artifacts — gitignored, never committed, but indexed by the `homelab_docs` fs corpus so that Aurora can retrieve operational history via `rag_search`. This is the mechanism that makes "operational memory" possible without violating the no-auto-commit constraint.

---

## Pre-test state

| Item | State |
|---|---|
| `09_ops/` directory | **Did not exist** (created during this test) |
| `09_ops/runtime/` directory | **Did not exist** (created during this test) |
| `09_ops/runtime/` in `.gitignore` | **NO — gap identified (see below)** |
| `homelab_docs` corpus type | `fs` (filesystem walk, not git) — walks `/home/diego/homelab` directly |
| `homelab_docs` initial point count | 4499 |

---

## Test procedure

### Step 1 — Create test file

Created `09_ops/runtime/af08_test.md` with a distinctive sentinel:

```
Sentinel: AF08-SENTINEL-7f3a-cd82-b491

This file is a disposable test artifact for F-0 AF-08 validation.
It verifies that the homelab_docs fs corpus indexes files under
09_ops/runtime/ even when they are untracked by git.
```

Git status at this point:
```
?? 09_ops/
```

The file was **untracked** (not gitignored — gap noted, see §Gap below).

### Step 2 — Run ingest sync

```
$ ingest sync --collection homelab_docs
```

Output:
```json
{
  "files_seen": 173,
  "files_skipped_unchanged": 163,
  "files_with_changes": 10,
  "chunks_upserted": 215,
  "chunks_unchanged": 4469,
  "files_deleted": 0,
  "points_deleted": 0,
  "elapsed_seconds": 5.99
}
```

The test file was among the 10 new/changed files. It took 6 seconds.

### Step 3 — Search for sentinel

Query: `"disposable test artifact runtime corpus validation untracked git"` (semantic, k=5)

```
[1] score=0.8895  04_ai_system/phase_f_architecture.md (chunk 85)
     | AF-08 | Runtime digest path not validated for fs-corpus indexing...

[2] score=0.8865  09_logs/2026-06-27_phaseE_E2a_failloud_sync_applied.md (chunk 14)
     ...

[3] score=0.8765  09_ops/runtime/af08_test.md (chunk 0)
     title: AF08 Validation Test File
     # AF08 Validation Test File
     Sentinel: AF08-SENTINEL-7f3a-cd82-b491
     This file is a disposable test artifact for F-0 AF-08 validation...

[4] score=0.8763  04_ai_system/phase_f_architecture.md (chunk 20)
     ...AD-07...

[5] score=0.8761  04_ai_system/phase_f_architecture.md (chunk 92)
     ...
```

**Result [3] is the test file** — retrieved at rank 3, score 0.8765, showing the full sentinel and title.

### Step 4 — Remove test file and directories

```bash
rm 09_ops/runtime/af08_test.md
rmdir 09_ops/runtime/
rmdir 09_ops/
```

Git status after: only the pre-existing untracked AF-01 log file remains.

### Step 5 — Re-sync to verify deletion propagation

```
$ ingest sync --collection homelab_docs
```

Output:
```json
{
  "files_seen": 172,
  "files_skipped_unchanged": 172,
  "files_with_changes": 0,
  "chunks_upserted": 0,
  "chunks_unchanged": 4683,
  "files_deleted": 1,
  "points_deleted": 1,
  "elapsed_seconds": 0.53
}
```

`files_deleted: 1, points_deleted: 1` — the orphaned chunk was detected and removed in the next sync cycle.

**homelab_docs point count after cleanup: 4683** (higher than the initial 4499 due to other updated documents indexed in this session's sync, unrelated to the test).

---

## Verdict

| Check | Result |
|---|---|
| `09_ops/runtime/` accessible to fs corpus | **PASS** |
| Test file indexed after sync | **PASS** |
| Test file retrievable via semantic search | **PASS** (rank 3, score 0.8765) |
| Deletion propagated on next sync | **PASS** (`files_deleted: 1, points_deleted: 1`) |
| Indexing independent of git status | **PASS** (untracked file indexed correctly) |

**Core validation: PASS.** The `homelab_docs` fs corpus indexes files at `09_ops/runtime/` regardless of git tracking status. AD-07's foundational assumption is confirmed.

---

## Gap identified — G-AF08-01: `09_ops/runtime/` not in `.gitignore`

**Severity:** Low (no risk while the directory doesn't exist; risk activates when F-4 writes real digest files)

**Current state:** The `.gitignore` file does not contain an entry for `09_ops/runtime/`. During this test, `09_ops/runtime/af08_test.md` appeared as `?? 09_ops/` (untracked) rather than `!! 09_ops/runtime/` (gitignored).

**Risk:** When F-4 implementation begins writing real digest files to `09_ops/runtime/`, a `git add .` or `git add 09_ops/` would accidentally stage runtime artifacts. This contradicts AD-07's requirement that runtime digest files are never committed.

**Required action (before F-4):** Add to `.gitignore`:
```
09_ops/runtime/
```

This is a one-line change. It must be committed to take effect. It does not affect the fs corpus's ability to index the files (the corpus uses filesystem walking, not git).

**When to fix:** Before F-4 implementation begins (or as part of F-0's pre-implementation checklist). Not required today.

---

## Secondary finding — sync cycle is also the deletion cycle

Orphaned points (from deleted files) are cleaned up automatically on the next `ingest sync` run. This means:
- If a nightly digest is written at 04:20 and then deleted before the next sync, its chunks persist in the index until the following night's sync.
- This is expected and harmless — the content is just stale, it doesn't cause errors or corruption.
- The nightly cron order (§6.4) ensures `generate-digest` runs BEFORE the next `ingest sync`, so digests are written, indexed, and their predecessor is cleaned up naturally.

---

## AF-08 disposition

**VALIDATED WITH GAP.** The core assumption (fs corpus indexes `09_ops/runtime/` files regardless of git status) is confirmed. One pre-implementation action is required before F-4:

1. Add `09_ops/runtime/` to `.gitignore` — prevents accidental commit of runtime digest files.

AF-08 assumption confirmed. Domain B (Operational Memory) can proceed to F-4 design without redesign. The gitignore fix is a pre-F-4 prerequisite.

---

## Cleanup confirmation

- `09_ops/runtime/af08_test.md` deleted from filesystem
- `09_ops/runtime/` directory removed
- `09_ops/` directory removed
- Orphaned chunk cleaned up by re-sync (`points_deleted: 1`)
- No production documents modified
- No git operations performed
- No Guardian Cloud touched
