# F4.3 — F-4 validation & reconciliation (applied)

- **Phase / milestone:** F — Operational Intelligence · **F4.3** (frozen at F4.0;
  authority: [`04_ai_system/phase_f_architecture.md`](../04_ai_system/phase_f_architecture.md) §9-F-4, AD-14…AD-18).
- **Date:** 2026-06-30.
- **Scope:** validate F-4 against the overnight scheduled run **with real operational data
  only**; apply the `generated_at` fidelity fix (AD-15); reconcile the architecture doc +
  overview triad. **No synthetic digests, no fabricated degraded nights** (operator
  decision). **STOP at the git approval gate.**
- **Status:** F4.1 + F4.2 implemented and **already committed** before this session
  (`9063164a`, `ac647e24`); **F4.3 implementation + reconciliation complete here.** F-4 is
  **not fully complete or fully validated** — three gates intentionally remain pending real
  operational evidence (below).

## F4.3 status (honest — reality always wins)

- **F4.3 implementation and reconciliation: complete.**
- **G-F4-01 / 02 / 03 / 04 / 09: PASS** (real data).
- **G-F4-08:** configuration verified; **empirical restic verification pending the next backup.**
- **G-F4-05 / 06 / 07:** intentionally **remain pending real operational evidence.**
- **No synthetic digests, no fabricated degraded nights, no artificial validation.**
- **F-4 is therefore not fully complete or fully validated** — it closes as real nightly
  digests accumulate and the next backup runs.

## Session-start reality check ("reality wins")

The architecture doc still read F-4 "NOT IMPLEMENTED", but the live system and git log
showed otherwise:

- `git log`: `9063164a` (F4.0 freeze + F4.1 substrate) and `ac647e24` (F4.2 generator) —
  both committed.
- `/etc/cron.d/aurora-signals` carries the **04:25** `generate-digest` line (root:root
  0644); `aurora-signals.log` shows `2026-06-30T02:25:01Z generate-digest: ok`.
- `09_ops/runtime/`: `2026-06-29_ops_digest.md` (F4.2 first real digest) +
  `2026-06-30_ops_digest.md` (the unattended 04:25 run).
- `ops_digests`: 384/Cosine, **3 points** (the indexed 2026-06-29 digest); production
  corpora untouched (`homelab_docs` 2088, `knowledge_history` 3132, …).

The "NOT IMPLEMENTED" header was stale doc-drift pending this F4.3 reconciliation; it is
now corrected in the architecture doc (§9-F-4 header + "as built", milestone table, §15).

## Generator fix — `generated_at` fidelity (AD-15)

- **Defect:** the digest stamped its own render time in `generated_at`
  (`2026-06-30T02:25:01Z`) instead of the source `aurora-context.json` `generated_at`
  (`2026-06-30T02:15:01Z`), contradicting the AD-15 data model.
- **Fix:** `bin/generate-digest` now derives `generated_at` from the parsed context
  timestamp (`gen_at = iso(ctx_dt)`), with a run-time fallback only when the context is
  absent/unparseable. One-line change at the `build_digest` return; no other behaviour
  altered. `--dry-run` confirmed, then real re-render.
- **AD-15 not amended** (operator decision — the spec was correct; the code was wrong).
- **Re-render + re-validate:** the latest digest (`2026-06-30`) was re-rendered; on-disk
  `generated_at == aurora-context.json generated_at` (`02:15:01Z`, asserted equal); schema
  correct; secret-scan clean. The pre-fix `2026-06-29` digest is left as-is — its source
  context no longer exists and re-rendering it would require fabricating a context
  (excluded). The corrected `2026-06-30` digest indexes at the next 02:30 sync.

## Gate status (real-data validation)

| Gate | Status | Evidence |
|---|---|---|
| G-F4-01 schema-correct digest | **PASS** | unattended 04:25 `2026-06-30` digest, re-rendered post-fix |
| G-F4-02 gitignored / cron runs no git | **PASS** | `git check-ignore` both digests; `git status` shows no digest; 04:25 cron runs the script directly |
| G-F4-03 collection + index + idempotent | **PASS** | `ops_digests` 384/Cosine, 3 pts; idempotent re-sync proven F4.2 |
| G-F4-04 rag_search hits + empty-path | **PASS** | real retrieval "night of 2026-06-29" → top-1 score 0.87; empty-path clean (F4.1) |
| G-F4-09 no secrets | **PASS** | secret-scan clean on the corrected digest (typed fields only, AD-18) |
| Repro gate | **PASS** (pending fix commit) | generator + corpora + enum committed; the `generated_at` fix awaits the git gate |
| G-F4-08 durability | **PARTIAL** | `09_ops/runtime/` in `homelab-backup.sh` PATHS (F4.2-verified); empirical `restic ls` is operator-gated |
| G-F4-05 date-anchored, ≥7 digests | **PENDING real accrual** | only 2 real digests today; closes once ≥7 nightly digests exist (~a week) |
| G-F4-06 same-night honesty | **PENDING** | structurally enforced (the 04:25 digest is not RAG-retrievable same-day, AD-04); needs one live-chat confirmation |
| G-F4-07 degraded night | **PENDING real degraded night** | both digests nominal; closes on the first real deviation captured by `notable` |

## Pending-gate closure procedure (repository prepared for natural closure)

No fabrication. When real data accrues, close as follows:

- **G-F4-05** — once `ls 09_ops/runtime/*_ops_digest.md | wc -l` ≥ 7, run
  `bin/ingest search --collection ops_digests --query "what happened on the night of <date>" --k 3`
  for several distinct dates → each returns its own date's digest top-1.
- **G-F4-06** — in Open WebUI, ask "¿qué pasó anoche?" the morning after a cycle → Aurora
  answers from `system_status` and states the same-night digest is not yet RAG-retrievable.
- **G-F4-07** — on the next real degraded night (a stopped container / ingest rc≠0), confirm
  that night's digest `notable` line captures the deviation and is retrievable by that
  description.
- **G-F4-08** (operator, root) — after a 03:00 backup:
  `sudo restic -r <repo> ls <latest-nightly-snap> | grep 09_ops/runtime` lists the digest(s);
  spot-check that a missing-source GC does not wipe `ops_digests`.

## Documentation

- `04_ai_system/phase_f_architecture.md` — reconciled F-4 status (header, §9-F-4 "as built",
  milestone table, §15 revision log). **AD-15 unchanged.**
- Overview triad (`CURRENT_STATE.md`, `ROADMAP.md`, `AMAROLAB_HANDOFF.md`) — F-4 status
  updated to F4.1/F4.2 done + F4.3 implementation + reconciliation complete (G-F4-05/06/07
  intentionally pending real operational evidence; F-4 not fully closed).

## Decisions

- **Real data only** (operator) — F-4 gates are validated **only** from real operational
  history, never synthetic fixtures or fabricated degraded nights. The gates that need more
  history (G-F4-05/06/07) remain open by design and close as nightly digests accumulate.
  Supersedes the F4.3 "backfill ≥7 dated fixtures" plan.
- **AD-15 is authoritative** (operator) — the generator was fixed to the spec, not the spec
  to the generator.
- F-4 is **not declared complete or fully validated**; F4.3 is implementation +
  reconciliation only, honest about the gates that still depend on real operational history.

## Rollback (AD-14 isolation)

Unchanged from F4.1/F4.2: `ops_digests` is isolated; `enabled: false` + revert the
`rag_search` enum + remove the 04:25 cron line + delete `09_ops/runtime/*.md` (gitignored)
fully reverts F-4. No production corpus is ever written to. The `generated_at` fix is a
one-line revert if needed.

## Git gate (STOP — operator approval required before any git command)

Pending working-tree changes for review:

- `ai-stack/ingest/bin/generate-digest` — `generated_at` fidelity fix (AD-15)
- `04_ai_system/phase_f_architecture.md` — F-4 status reconciliation (AD-15 untouched)
- `00_overview/CURRENT_STATE.md`, `00_overview/ROADMAP.md`, `00_overview/AMAROLAB_HANDOFF.md` — triad
- `09_logs/2026-06-30_phaseF_F4_3_closeout.md` — this log

Unrelated, **not** part of F-4 (leave for separate review): `README.md` (cosmetic
landing-page rewrite, already modified in the working tree before this session).

Runtime-only (never git): `09_ops/runtime/*_ops_digest.md`; the `ops_digests` Qdrant collection.
