# Phase F — F2-9 Closeout: Nightly Validation, `system_status` Wiring, Triad Reconciliation

- **Date:** 2026-06-29
- **Phase step:** F-2 — Signal Layer and Context Generation (closeout)
- **Status:** COMPLETE. F-2 closed. Current active step → F-3.
- **Authority:** Reality is source of truth (PROJECT_RULES). Every claim below is
  from real commands / logs / DB readback against the running system on 2026-06-29.

---

## 1. Scope

F2-9 closes F-2: (a) confirm the first **unattended** nightly signal cycle; (b) complete
the production wiring of `system_status` (the open **G-F1-01** item); (c) remove the F2-6
rollback container so the pipeline reports `ok`; (d) reconcile the overview triad to
repository reality. No new features; F-3 not started.

## 2. Unattended nightly cycle — VALIDATED (night of 2026-06-28 → 29)

Schedulers: `/etc/cron.d/homelab-backup` (restic 03:00) + `/etc/cron.d/aurora-signals`
(F2-8: `backup-probe` 03:30, `container-probe` 04:00, `aurora-context` 04:15).

| Artifact | mtime (CEST) | Key content | Result |
|---|---|---|---|
| restic snapshot | 03:00 | `c38ddcc1` saved (3.484 GiB) — `/var/log/homelab-backup.log` | ✅ |
| `backup_status.json` | 03:30 | `status ok`, snapshot `c38ddcc1` | ✅ |
| `container_status.json` | 04:00 | 17/18 running (1 = retained rollback) | ✅ |
| `aurora-context.{json,md,voice}` | 04:15 | `signals_missing: []`; sole degrade = rollback container | ✅ |

`aurora-signals.log` shows the clean unattended chain. Inside `openwebui`: `/opt/aurora`
(ro) + `/opt/ingest` (ro) serve the fresh signals; live Torre probe 25 ms. Runtime
artifacts gitignored (incl. `09_ops/runtime/` → G-AF08-01 already satisfied); git clean.

## 3. G-F1-01 resolution + `system_status` wiring (F2-9)

**Root cause of the pending gate:** `system_status` v0.2.0 was installed (F2-5) and
functional at container level, but **never attached to qwen2.5** (`meta.toolIds`) nor
described in the F-1 prompt — only the legacy `llama3*` rows carried it. Aurora therefore
could not invoke it, which is why G-F1-01 (chat-level tool firing) never passed.

**Fix:** added `system_status` to qwen2.5 `meta.toolIds` (now 6 tools) and wove it into the
F-1 prompt (Tools list → 6 tools; LIVE-STATE routing → platform health; Context note).
Prompt **3,147 → 3,389 chars** (~485 tokens). `base_model_id` untouched (D-35). `openwebui`
restarted (healthy). Original row backed up before the edit (rollback in §9).

**Validation (all layers):**

| Layer | Evidence | Result |
|---|---|---|
| Tool attached to qwen2.5 | DB `meta.toolIds` readback includes `system_status` | ✅ |
| Model routing (native function-calling, live Ollama via proxy, temp 0) | `¿estado del sistema?`→`system_status`, `¿qué hora?`→`time_now`, `¿embeddings?`→`rag_search`, `¿impresora?`→`ha_get_state` | ✅ **4/4, no regression** |
| Tool execution | real `Tools.system_status()` vs live `/opt/aurora`: accurate ingest/backup/audit/containers + live Torre 2–3 ms | ✅ |
| Real browser UI | Operator (Diego) chat `¿Cuál es el estado del sistema?` → UI shows `system_status/system_status` invoked, returns live status | ✅ **PASS** |

G-F1-01 is fully resolved across DB, model-routing, tool-execution, and the real browser UI.

**How the attachment was performed (exact) + runtime-state safeguard.** The
attachment is a direct `sqlite3` UPDATE of the `qwen2.5:7b-instruct` `model`
row in `webui.db` (append `system_status` to `meta.toolIds`; edit
`params.system`; parameterised write; readback-verify; `docker restart
openwebui`; pre-edit row backed up). This is runtime DB state, not in git.
Its persistence, restic recoverability, fresh-deploy reproducibility, and the
recommendation to automate the model config are documented in
[`../04_ai_system/openwebui_model_runtime_state.md`](../04_ai_system/openwebui_model_runtime_state.md).

## 4. Rollback-container cleanup → `overall_status = ok`

`openwebui_pre_f2_6` (the F2-6 `docker run` rollback copy, `Exited (0)`) removed after the
first successful nightly cycle (precondition met) and G-F1-01. Re-ran `container-probe`
(`ok count=17`) + `aurora-context` (`ok signals_missing=[] degrades=[]`):

- `container_count` = **17**, `all_running` = **true**, `degraded` = **[]**,
  `overall_status` = **ok**. Confirmed in `container_status.json`, `aurora-context.json`,
  and `system_status` (Overall: ok / all checked signals ok / Torre 2 ms / 17/17).

Note: the retained rollback container provided an organic end-to-end **degraded→ok**
propagation test (container-probe → aurora-context → `system_status`), satisfying the F-2
success-criterion clause on degraded-state propagation without an artificial fault.

## 5. Running system vs. docs — drift reconciled

- **F-1**: triad said "in progress / current active step" → **complete** (2026-06-28).
- **F-2**: absent from triad → **complete** (this log).
- **Qdrant live counts** (grew via nightly ingest of the new Phase F docs):
  `homelab_docs` **1968** (was 1911), `knowledge_history` **3029** (was 2918);
  `guardian_cloud` 872, `ensambla2` 419, `infra_audits` 280, `myfreetour` 0. Recorded
  as-of 2026-06-29; counts grow nightly. `AURORA_FOUNDATION.md` (1911/2918) is a F-1
  snapshot, now superseded by live values (not edited — outside the triad scope).
- **Containers**: steady-state **17 running**.
- **Triad updated:** `CURRENT_STATE.md` (status block; new Phase F subsection; Open WebUI
  6 tools + F-1 prompt; ingest counts), `ROADMAP.md` (F-1/F-2 COMPLETE, F-3 active),
  `AMAROLAB_HANDOFF.md` (phase/next-task + `system_status` capability).

## 6. Decisions

- **Backup signal** implemented as a standalone `bin/backup-probe` (reads restic snapshot
  metadata at 03:30) instead of modifying production `homelab-backup.sh` (the architecture's
  original F-2 approach). Safer — production backup untouched. Tradeoff: `files_new` /
  `files_changed` / `data_added_mb` are `null` (snapshot list lacks per-run deltas).
  Accepted; the signal carries `status` + `snapshot_id` + `snapshot_time`, which is
  sufficient for context/`system_status`.
- **`system_status` model-attachment** treated as the F-2 completion step (not F-3), per
  operator decision 2026-06-29.

## 7. Residual / follow-ups (NOT F-2 blockers)

- **restic stale lock** (PID 226801, held since 2026-06-27 12:30) + "no parent snapshot
  found, will read all files" on each nightly run — snapshots still save, but prune/forget
  is likely blocked and runs do full reads. Out of F-2 scope; tracked separately
  (`restic unlock` investigation).
- **Portainer `ai-local` stack re-association** — drift from the F2-6 `docker run`
  recreation of `openwebui`; deferred maintenance (needs sudo + window).
- `backup_status.json` per-run deltas `null` (see §6) — enhance only if a future consumer
  needs them.
- `AURORA_FOUNDATION.md` corpus counts are a F-1 snapshot — refresh at the next milestone doc pass.

## 8. Rollback

- **Wiring:** restore qwen2.5 `meta`/`params` from the pre-edit backup + `docker restart
  openwebui`.
- **Container removal:** irreversible for that stopped copy, but the live `openwebui` is
  healthy/authoritative; a full openwebui can be rebuilt via `bin/recreate-openwebui`.

## 9. Git / next

Operator-approval-gated commit set: `00_overview/CURRENT_STATE.md`,
`00_overview/ROADMAP.md`, `00_overview/AMAROLAB_HANDOFF.md`,
`04_ai_system/openwebui_model_runtime_state.md`,
`ai-stack/openwebui-tools/README.md`, and this log. Runtime
artifacts (signal JSON, `ai-stack/aurora/`) are gitignored — not staged. The `system_status`
tool source (`ai-stack/ingest/docs/system_status_tool.py`) and probe scripts were already
committed in F2-2…F2-8; F2-9 changed only live DB state (qwen2.5 row) + docs.

**STOP before commit/push** — per PROJECT_RULES "Operator Git Approval", each of
`git commit` / `git push` / `git tag` requires fresh operator approval requested
immediately beforehand.
