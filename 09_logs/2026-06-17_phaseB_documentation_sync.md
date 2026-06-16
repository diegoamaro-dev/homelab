# Phase B — documentation sync (CURRENT_STATE / ROADMAP / AMAROLAB_HANDOFF)

- **Date:** 2026-06-17.
- **Goal:** bring the three live state docs at the root of
  `04_ai_system/amarolab-v1/` in sync with the work that landed
  between 2026-06-16 and 2026-06-17 (R-B1 ingest CLI remediation,
  Phase B B-1 + B-2 + B-3, V-C reranker validation). The state
  docs had been left at their 2026-06-15 / 2026-06-16 evening
  timestamps while the operational commits that followed
  (`06d2face`, `bf2b4dd8`, `2a84ff8f`, `09ad6821`, `4a8ff40d`)
  introduced new live state without updating the three documents
  that aggregate it.
- **Inputs (read first per the user's instruction):**
  [`../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md`](../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md),
  [`../04_ai_system/amarolab-v1/CURRENT_STATE.md`](../04_ai_system/amarolab-v1/CURRENT_STATE.md),
  [`../04_ai_system/amarolab-v1/ROADMAP.md`](../04_ai_system/amarolab-v1/ROADMAP.md),
  [`2026-06-16_ingest_cli_remediation_applied.md`](2026-06-16_ingest_cli_remediation_applied.md),
  [`2026-06-16_phaseB_infra_audits_applied.md`](2026-06-16_phaseB_infra_audits_applied.md),
  [`2026-06-16_phaseB_openwebui_bind_mount_applied.md`](2026-06-16_phaseB_openwebui_bind_mount_applied.md),
  [`2026-06-17_phaseB_vc_validation.md`](2026-06-17_phaseB_vc_validation.md).
- **What this log is NOT:** an apply log for B-4 or any later
  Phase B step. No code, Tool, `webui.db`, `meta.toolIds`,
  container, or runtime state was touched. Only three Markdown
  files were edited, plus one new Markdown file (this log) was
  created.

## 1. Why this log exists separately

The 2026-06-16 / 2026-06-17 commits each shipped their own
application log under `09_logs/`, but none of them edited
`CURRENT_STATE.md` / `ROADMAP.md` / `AMAROLAB_HANDOFF.md`. The
roadmap rule in
[`../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md`](../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md)
§"Documentation rules" treats those three files as **live state**
("rewritten in place whenever facts change"), and Phase B is
gated on them being current before B-4 starts authoring source.
This log documents the in-place rewrite that closes the gap, and
preserves the diff trail outside the next commit message.

## 2. Files edited

| File | Insertions / deletions | Sections touched |
|---|---:|---|
| `04_ai_system/amarolab-v1/CURRENT_STATE.md` | +153 / -39 | top `Last updated` line; "what is in place after Phase A.3" paragraph (now an enumerated list including B-1..B-3 + V-C); Qdrant collections table (`infra_audits` row + header count); Tool layer (added V-C readiness note); Environment / configuration table (two new rows — bind mount + editable install); What is validated table (six new rows); What is pending → Phase B (split into "Applied this phase" / "Remaining in Phase B"); Latest completed milestone (replaced single Phase-A focus with Phase B B-3 + V-C as the latest, with Phase A summary kept as historical reference). |
| `04_ai_system/amarolab-v1/ROADMAP.md` | +143 / -21 | top `Last updated` line; §"Completed phases" — appended four new sub-sections (R-B1 ingest CLI fix, B-1 + B-2 `infra_audits`, B-3 bind mount, V-C reranker validation), each with date applied, outcome, validation, evidence; §"Current phase" — Phase B status flipped from "not started" to "IN PROGRESS" with done / remaining bullets; §"Next phases" → Phase B — split into "Done" / "Remaining" lists; §"Blockers" — added R-new1 (per-call rerank latency) to the non-blocking carry-overs table and a new "Resolved during Phase B execution" table holding R-B1, R-M1, R-M3 with resolution evidence. **No D-3X decisions added** (per the user's "do not modify implementation details that were not validated" constraint). |
| `04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md` | +21 / -4 | top `Last updated` line; §"Current phase" — Phase B flipped from "Not started" to "IN PROGRESS" with the sub-step status block; §"Mandatory reading order" — new item 14 enumerates the seven Phase B logs from 2026-06-16 / 2026-06-17 in the order a fresh session should read them. |

Total: +317 / -64 across the three files. No structural
re-organisation (no section reordering, no heading renames, no
removed sections). All edits land **inside** the existing
sub-sections.

## 3. What each edit reflects

### 3.1 R-B1 ingest CLI remediation (out-of-band prerequisite)

Source log:
[`2026-06-16_ingest_cli_remediation_applied.md`](2026-06-16_ingest_cli_remediation_applied.md).

Reflected in:

- `CURRENT_STATE.md` Environment / configuration table — new
  row noting `ai-stack/ingest` is now editable-installed in its
  venv, `bin/ingest --help` exits 0 from any CWD, nightly cron
  unblocked.
- `CURRENT_STATE.md` What is validated table — new row for the
  CWD-independent CLI invocation.
- `CURRENT_STATE.md` Phase B "Applied this phase" — bulleted
  as the out-of-band prerequisite for B-2.
- `ROADMAP.md` Completed phases — new sub-section "Phase B
  preparation — Ingest CLI remediation (R-B1) — APPLIED".
- `ROADMAP.md` Resolved-during-Phase-B table — R-B1 with
  resolution evidence pointer.

### 3.2 Phase B B-1 + B-2 — `infra_audits` corpus

Source log:
[`2026-06-16_phaseB_infra_audits_applied.md`](2026-06-16_phaseB_infra_audits_applied.md).

Reflected in:

- `CURRENT_STATE.md` Qdrant collections table — `infra_audits`
  row updated from "Phase B (not created)" to "Active (created
  2026-06-16, Phase B B-1/B-2)" with 280 chunks across 6 files;
  table header updated from "(4 active, 1 pending)" to
  "(5 active, 1 placeholder)".
- `CURRENT_STATE.md` What is validated table — new row for the
  ingestion run.
- `CURRENT_STATE.md` Phase B "Applied this phase" — B-1 and
  B-2 bulleted with evidence pointer.
- `ROADMAP.md` Completed phases — new sub-section "Phase B
  B-1 + B-2 — `infra_audits` corpus — APPLIED".

### 3.3 Phase B B-3 — Open WebUI bind mount

Source log:
[`2026-06-16_phaseB_openwebui_bind_mount_applied.md`](2026-06-16_phaseB_openwebui_bind_mount_applied.md).

Reflected in:

- `CURRENT_STATE.md` Environment / configuration table — new
  row noting the `openwebui` container's mounts now include
  `/opt/ingest:ro` and the rollback container
  `openwebui_pre_phaseB_20260615235209` is preserved.
- `CURRENT_STATE.md` What is validated table — new row for the
  import smoke test (`from ingest.embedder import Embedder` +
  `from ingest.reranker import Reranker`) and for the MD5
  preservation across recreate.
- `CURRENT_STATE.md` Pre-flight backups retained — new bullet
  for the rollback container.
- `ROADMAP.md` Completed phases — new sub-section "Phase B
  B-3 — Open WebUI bind mount (Gate G-1) — APPLIED" naming
  Gate G-1 as approved.
- `AMAROLAB_HANDOFF.md` Current phase — explicit "Gate G-1
  approved" note alongside the B-3 sub-step status.

### 3.4 V-C reranker validation

Source log:
[`2026-06-17_phaseB_vc_validation.md`](2026-06-17_phaseB_vc_validation.md).

Reflected in:

- `CURRENT_STATE.md` Tool layer — added a paragraph noting V-C
  PASS, that the existing benchmark reproduces under
  `sentence-transformers 5.2.3`, and that source files are
  still not authored (B-4 is the next step).
- `CURRENT_STATE.md` What is validated table — two new rows:
  one for the 20-question accuracy reproduction (top-1/3/6 =
  15/17/19, 0 pp drift) and one for the side-by-side
  sentence-transformers latency probe (host 11 124 ms vs
  container 11 174 ms / query).
- `CURRENT_STATE.md` Open carry-overs — new bullet for R-new1
  (per-call rerank latency ≈ 10 s; not a Phase B blocker).
- `CURRENT_STATE.md` Latest completed milestone — the Phase A
  block was demoted to "for reference" and Phase B B-3 + V-C
  is now the top milestone.
- `ROADMAP.md` Completed phases — new sub-section "Phase B
  V-C — Container reranker validation — PASS".
- `ROADMAP.md` Resolved-during-Phase-B table — R-M1 (ST
  drift) and R-M3 (cold load) both moved out of the active
  risk set.
- `ROADMAP.md` Non-blocking carry-overs — new row R-new1.

## 4. What was deliberately NOT changed

Per the user's constraints ("Preserve existing structure",
"Do not rewrite unrelated sections", "Do not modify
implementation details that were not validated", "Clearly
distinguish completed work from planned work"):

- **No D-3X decisions added.** D-08 (embedder + reranker model
  identities), D-20 (per-model scope), D-22 (`myfreetour`
  enum), D-26 (inline helper) are all still authoritative for
  Phase B; V-C confirmed they remain accurate; nothing new to
  lock at the design level.
- **No Phase A.X re-numbering.** Phase A applied set is kept
  intact in HANDOFF and CURRENT_STATE; it now reads as
  "previous milestone" rather than "the most recent milestone"
  but the substance is preserved.
- **No security / permissions edits.**
  [`04-security-and-permissions.md`](../04_ai_system/amarolab-v1/04-security-and-permissions.md)
  is untouched. The trust model and allowlist constants did
  not change.
- **No edit to the immutable design package files (01–05).**
  The v1 design they describe is still the v1 design.
- **No `tools/rag_search.py` or `tools/audit_search.py`
  reference added as "exists on disk".** The doc explicitly
  states they are not yet authored. This is the
  distinguish-completed-from-planned rule.
- **No "rag_search is wired" claim.** V-C validated the
  underlying retrieval + rerank pipeline through the
  bind-mounted runtime. It did *not* validate the Tool runtime
  contract end-to-end; B-4..B-8 are still required. The docs
  reflect this distinction explicitly.
- **No prompt edit, no `meta.toolIds` edit, no `webui.db`
  edit, no container restart.** State byte-identical to the
  end of
  [`2026-06-17_phaseB_vc_validation.md`](2026-06-17_phaseB_vc_validation.md)
  §6.

## 5. Forensic state at end of this sync

| Item | Value |
|---|---|
| `webui.db` MD5 | `656d7295d3cfc00a2255bb0b2230fba1` (unchanged since B-3) |
| `amarolab-audit.log` MD5 | `310ef8dbfd103685514addacb1ada2c3` (unchanged since B-3; V-C added 0 lines) |
| qwen2.5 `base_model_id` | `NULL` (D-35; unchanged) |
| qwen2.5 `meta.toolIds` | `["time_now"]` (unchanged) |
| `infra_audits` Qdrant point count | 280 (unchanged) |
| `openwebui` container mounts | `/srv/homelab/data/openwebui` (R/W) + `/opt/ingest:ro` (unchanged since B-3) |
| `tools/rag_search.py`, `tools/audit_search.py` | **still do not exist on disk** |
| `bin/ingest --help` | exits 0 from any CWD (R-B1 remediation in place) |
| Git working tree | three modified state docs + one new log (this file) + previously-untracked V-C log |
| Local vs `origin/main` | unchanged relative to the V-C log — no commits added by this sync |

## 6. Recommended next step

The sync is complete; CURRENT_STATE, ROADMAP, and AMAROLAB_HANDOFF
now describe the live system accurately and call out exactly which
Phase B steps remain. The previously-instructed next operational
move (B-4 — author `tools/rag_search.py`) is unblocked from a
documentation-state standpoint and remains the recommended next
action, awaiting explicit user approval.

If a separate B-9-style commit is preferred over batching this
docs sync with B-4..B-8, the natural commit-message form is:

```
docs(amarolab): sync state docs with Phase B B-1..B-3 + V-C

- CURRENT_STATE.md: infra_audits active (280 chunks); /opt/ingest
  bind mount on openwebui; Phase B sub-step status split; V-C
  PASS recorded.
- ROADMAP.md: four new "Completed phases" sub-sections
  (R-B1, B-1+B-2, B-3, V-C); Phase B status flipped to IN
  PROGRESS; R-B1 / R-M1 / R-M3 moved to "Resolved during Phase
  B execution"; R-new1 added as non-blocking carry-over.
- AMAROLAB_HANDOFF.md: current phase flipped to IN PROGRESS;
  mandatory reading order extended with the seven 2026-06-16 /
  2026-06-17 Phase B logs.
- 09_logs/2026-06-17_phaseB_documentation_sync.md: this log.
```

No durable system change beyond text in three Markdown files and
one new Markdown log. Reversible by `git restore` on the four
paths.

## 7. Cross-references

- The three state docs (now current):
  [`../04_ai_system/amarolab-v1/CURRENT_STATE.md`](../04_ai_system/amarolab-v1/CURRENT_STATE.md),
  [`../04_ai_system/amarolab-v1/ROADMAP.md`](../04_ai_system/amarolab-v1/ROADMAP.md),
  [`../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md`](../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md).
- Phase B execution plan (still authoritative for B-4..B-10):
  [`../04_ai_system/amarolab-v1/PHASE_B_EXECUTION_PLAN.md`](../04_ai_system/amarolab-v1/PHASE_B_EXECUTION_PLAN.md).
- Source logs for the changes documented here:
  [`2026-06-16_ingest_cli_remediation_applied.md`](2026-06-16_ingest_cli_remediation_applied.md),
  [`2026-06-16_phaseB_infra_audits_applied.md`](2026-06-16_phaseB_infra_audits_applied.md),
  [`2026-06-16_phaseB_openwebui_bind_mount_applied.md`](2026-06-16_phaseB_openwebui_bind_mount_applied.md),
  [`2026-06-17_phaseB_vc_validation.md`](2026-06-17_phaseB_vc_validation.md).
- Readiness review that scoped the sub-steps applied here:
  [`2026-06-16_phaseB_execution_readiness_review.md`](2026-06-16_phaseB_execution_readiness_review.md).

## 8. Stop point

Per the user's instruction ("Stop after showing a summary of
documentation changes and reporting git status. Do not start B-4
yet."): this log is the artefact. The summary + git status are
reported in the chat session that triggered this work. No
subsequent action will be taken until explicit instruction.
