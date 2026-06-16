# Phase B — formal close-out — Amarolab Assistant v1

- **Date:** 2026-06-16
- **Decision:** **Phase B is CLOSED.** Phase C is the next phase.
- **Scope:** Record the closure of Phase B (Knowledge Tool +
  `infra_audits` corpus) of the Amarolab Assistant v1 sub-project,
  define the Phase C starting point, and capture the open evidence
  items (W-4 / W-5 / W-6 / W-7) that survive the closure as
  best-effort follow-ups. Counterpart to
  [`2026-06-15_phaseA_closeout.md`](2026-06-15_phaseA_closeout.md).
- **What this log is NOT:** an application log. Nothing in
  `webui.db`, no Tool source, no container, no Qdrant collection,
  no env var, no filesystem path outside `09_logs/` and the three
  live state files at
  `04_ai_system/amarolab-v1/{AMAROLAB_HANDOFF,CURRENT_STATE,ROADMAP}.md`
  is modified by this closure. Closure is a decision + documentation
  event, not a code/state event.
- **Inputs consumed:**
  - [`2026-06-16_phaseB_execution_readiness_review.md`](2026-06-16_phaseB_execution_readiness_review.md)
  - [`2026-06-16_phaseB_rag_inventory_and_gap_analysis.md`](2026-06-16_phaseB_rag_inventory_and_gap_analysis.md)
  - [`2026-06-16_ingest_cli_remediation_analysis.md`](2026-06-16_ingest_cli_remediation_analysis.md)
  - [`2026-06-16_ingest_cli_remediation_applied.md`](2026-06-16_ingest_cli_remediation_applied.md)
  - [`2026-06-16_phaseB_infra_audits_design.md`](2026-06-16_phaseB_infra_audits_design.md)
  - [`2026-06-16_phaseB_infra_audits_applied.md`](2026-06-16_phaseB_infra_audits_applied.md)
  - [`2026-06-16_phaseB_openwebui_bind_mount_plan.md`](2026-06-16_phaseB_openwebui_bind_mount_plan.md)
  - [`2026-06-16_phaseB_openwebui_bind_mount_applied.md`](2026-06-16_phaseB_openwebui_bind_mount_applied.md)
  - [`2026-06-17_phaseB_vc_validation.md`](2026-06-17_phaseB_vc_validation.md)
  - [`2026-06-17_phaseB_rag_search_design.md`](2026-06-17_phaseB_rag_search_design.md)
  - [`2026-06-17_phaseB_audit_search_design.md`](2026-06-17_phaseB_audit_search_design.md)
  - [`2026-06-16_phaseB_validation_applied.md`](2026-06-16_phaseB_validation_applied.md)
  - Sub-project design docs (immutable for v1) under
    `../04_ai_system/amarolab-v1/01..05` and
    `../04_ai_system/amarolab-v1/PHASE_B_EXECUTION_PLAN.md`.
  - Live state inputs:
    `../04_ai_system/amarolab-v1/{AMAROLAB_HANDOFF,CURRENT_STATE,ROADMAP}.md`.

## 0. TL;DR

Phase B's purpose was to land the **knowledge layer** of the
assistant: a Qdrant corpus indexed off the infra-audit tree, a
`class Tools` Open WebUI Tool that does dense → rerank retrieval
across all five corpora (`rag_search`), a paired Tool hardcoded to
the audit corpus (`audit_search`), and a runtime substrate inside
the `openwebui` container that can load the ingest pipeline from a
read-only bind mount.

All of that is on disk and live:

| Piece | State |
|---|---|
| `infra_audits` Qdrant collection (384 d cosine, 280 chunks from `/home/diego/server-audit-2026-06-13/**/*.md`) | ✓ B-1 + B-2 applied |
| `openwebui` container with `/opt/ingest:ro` bind mount; rollback target preserved as `openwebui_pre_phaseB_20260615235209` | ✓ B-3 applied, Gate **G-1** approved |
| V-C reranker readiness — container `sentence-transformers 5.2.3` reproduces the Phase 1.5 `guardian_cloud` benchmark with 0 pp drift (top-1/3/6 = 15/17/19) | ✓ V-C PASS (R-M1 resolved) |
| `tools/rag_search.py` (11 629 chars after inline, 1 spec; `class Tools`; lazy `_init()`; `Literal[…5 corpora…]`; D-08 / D-22 / D-24 / D-26 honoured); committed at `a7995b3f` | ✓ B-4 applied |
| `tools/audit_search.py` (11 231 chars after inline, 1 spec; `class Tools`; mirror of `rag_search.py` with `_COLLECTION = "infra_audits"`); committed at `a13d5e94` | ✓ B-5 applied |
| Both Tools installed in `webui.db` via `bin/install_tool` → `POST /api/v1/tools/create`; install-fidelity diff vs canonical = trailing-newline only | ✓ B-6 applied |
| qwen2.5 Model entry `meta.toolIds = ["time_now","rag_search","audit_search"]`; `base_model_id = NULL` (D-35) preserved; D-20 per-model scope preserved | ✓ B-7 applied, Gate **G-2** approved |
| Browser-path `audit_search` end-to-end: two `result_code: ok` runs by the user (Spanish R-12 query, 20 694 ms cold; `SANITIZATION_REPORT`, 12 788 ms warm); Tool-runtime `rag_search` probe `result_code: ok` (22.5 s, 6 hits) against the installed source dumped from `webui.db` | ✓ B-8 applied (partial), Gate **G-3** approved |

One open item survives this closure, by user decision:

- **The literal W-1..W-8 + V-A / V-B prompt sweep was not fully
  run.** Of the eight W-prompts, W-1 / W-3 are implicitly covered
  (Phase A.3 canary + the user's two `audit_search` queries) and
  W-2 has a Tool-runtime probe on a non-literal `homelab_docs`
  query. **W-4 / W-5 / W-6 / W-7 remain unexercised.** The user
  has marked B-8 complete; this log records the gap as
  *best-effort follow-up*, not a Phase B blocker, and itemises it
  in §3 so a future reviewer can reopen it without re-deriving
  the context.

**Phase B is closed.** Phase C is the next phase. The next
substantive change to the assistant is creating the dedicated
Home Assistant user `assistant` and issuing its Long-Lived Access
Token (blocker B-07; HA UI action, owner: user).

## 1. What Phase B delivered

| Sub-step | Deliverable | Applied date | Evidence |
|---|---|---|---|
| **R-B1** (out-of-band) | `ai-stack/ingest/pyproject.toml` added; `pip install -e .` appended to `install.sh`; `bin/ingest --help` exits 0 from any CWD; nightly 02:30 cron unblocked | 2026-06-16 | [`2026-06-16_ingest_cli_remediation_applied.md`](2026-06-16_ingest_cli_remediation_applied.md) |
| **B-1** | `infra_audits` stanza appended to `ai-stack/ingest/conf/corpora.yaml` (`type: fs`, include `**/*.md`, exclude `**/inspect-snapshots/**` + `**/*.json`) | 2026-06-16 | [`2026-06-16_phaseB_infra_audits_applied.md`](2026-06-16_phaseB_infra_audits_applied.md) §1 |
| **B-2** | Qdrant collection `infra_audits` created (384-d cosine, payload indexes on `collection` / `source_kind` / `source_rel`); one-shot backfill of `/home/diego/server-audit-2026-06-13/**/*.md` → 280 chunks across 6 files; spot rerank top-1 0.8809 on `DOCUMENTATION_SYNC_PLAN.md` chunk 36, 0.8693 on `SANITIZATION_REPORT.md` chunk 0 | 2026-06-16 | [`2026-06-16_phaseB_infra_audits_applied.md`](2026-06-16_phaseB_infra_audits_applied.md) §2 |
| **B-3** (Gate **G-1**) | `openwebui` container stopped, renamed `openwebui_pre_phaseB_20260615235209` as the rollback target, replaced with a new container carrying the same image / ports / env / `proxy_default` attachment **plus** `/home/diego/homelab/ai-stack/ingest:/opt/ingest:ro`; `webui.db` MD5 = `656d7295d3cfc00a2255bb0b2230fba1` and `amarolab-audit.log` MD5 = `310ef8dbfd103685514addacb1ada2c3` unchanged across the recreate; `from ingest.embedder import Embedder` and `from ingest.reranker import Reranker` resolve inside the container | 2026-06-16 | [`2026-06-16_phaseB_openwebui_bind_mount_applied.md`](2026-06-16_phaseB_openwebui_bind_mount_applied.md) |
| **V-C** | 20-question `guardian_cloud` benchmark replayed inside the container with a `class Tools`-shaped probe: top-1 / top-3 / top-6 = 15 / 17 / 19 (75 % / 85 % / 95 %); 0 pp drift vs Phase 1.5; all 20 per-question ranks identical (Q12 cross-encoder win, Q17 documented regression, Q16 empty-file persistent miss). One benign `embeddings.position_ids UNEXPECTED` warning. **R-M1 resolved.** R-M3 recalibrated downwards (cold load 5.6 s total). Side observation R-new1 (per-call rerank ≈ 10 s / query) measured identically on host (ST 3.4.1, 11 124 ms) and container (ST 5.2.3, 11 174 ms) — property of the locked (`bge-reranker-v2-m3`, DENSE_N=30) tuple, not a regression | 2026-06-17 | [`2026-06-17_phaseB_vc_validation.md`](2026-06-17_phaseB_vc_validation.md) |
| **B-4** | `ai-stack/openwebui-tools/tools/rag_search.py` authored as a `class Tools` Open WebUI Tool (D-24) with the audit helper inlined via `# @@AMAROLAB_INLINE:audit_helper@@` (D-26); lazy `_init()` over `Embedder` / `Reranker` / `QdrantClient`; `collection: Literal["homelab_docs","guardian_cloud","ensambla2","infra_audits","myfreetour"]`; DENSE_N=30, TOP_K_DEFAULT=6, CONTENT_CAP=600 (D-08, D-22); eight `result_code`s: `bad_query` / `bad_k` / `rate_limited` / `init_error` / `qdrant_unreachable` / `empty_collection` / `rerank_error` / `ok`. Local validation: pre/post inline `py_compile` PASS, AST shape PASS (single LLM-callable method, Valves nested class, Literal annotation), in-container module load + `bad_query` probe PASS (no `_init()` invoked) | 2026-06-17 | [`2026-06-17_phaseB_rag_search_design.md`](2026-06-17_phaseB_rag_search_design.md); commit `a7995b3f` |
| **B-5** | `ai-stack/openwebui-tools/tools/audit_search.py` authored as a mirror of `rag_search.py` with the `collection` parameter dropped and `_COLLECTION = "infra_audits"` hardcoded (03-tools.md §"Tool 2"). Same lazy `_init()` pipeline, same DENSE_N / TOP_K / CONTENT_CAP, same inlined audit helper, same error matrix. Per D-26, the body is duplicated rather than cross-imported. Local validation: pre/post inline `py_compile` PASS, AST shape PASS (`audit_search` args = `[self, query, k]` — no `collection`), in-container module load + `bad_query` + `bad_k` probes PASS | 2026-06-17 | [`2026-06-17_phaseB_audit_search_design.md`](2026-06-17_phaseB_audit_search_design.md); commit `a13d5e94` |
| **B-6** | `bin/install_tool tools/rag_search.py` and `bin/install_tool tools/audit_search.py` (D-25 workflow) POSTed both inlined sources to `/api/v1/tools/create`. Rows present in `webui.db`: `rag_search` (11 629 chars, 1 spec) and `audit_search` (11 231 chars, 1 spec); owner `diego` admin; `created_at` one second apart. `bin/dump_tools` round-trip + `diff` shows install-fidelity vs canonical = trailing-newline only. Both Tools' JSON specs build correctly under Open WebUI 0.8.10 (Literal → enum, docstring → description) | 2026-06-16 | [`2026-06-16_phaseB_validation_applied.md`](2026-06-16_phaseB_validation_applied.md) §1 |
| **B-7** (Gate **G-2**) | qwen2.5 Model entry `meta.toolIds` extended from `["time_now"]` to `["time_now","rag_search","audit_search"]`. The `base_model_id = NULL` rule locked as **D-35** during the Issue T remediation (2026-06-16) is preserved unchanged, so the OWUI 0.8.10 browser-UI `tool_ids` auto-attach continues to work. Per-model scope (D-20) preserved — Tools attached only to the qwen2.5 row | 2026-06-16 | [`2026-06-16_phaseB_validation_applied.md`](2026-06-16_phaseB_validation_applied.md) §2 |
| **B-8** (Gate **G-3**, partial) | Two browser-path `audit_search` queries by the user returned `result_code: ok`: Spanish R-12 query (`{"query":"¿Qué se hizo en la remediación R-12?","k":6}`) at `2026-06-16T09:58:16Z`, `duration_ms = 20 694`; `SANITIZATION_REPORT` (`{"query":"SANITIZATION_REPORT","k":6}`) at `2026-06-16T10:04:37Z`, `duration_ms = 12 788`. Three this-log read-only probes against the installed Tool source dumped from `webui.db` produced parity evidence: P-1 `rag_search(homelab_docs, "What is the homelab AI stack architecture?", k=6)` → ok, 22.5 s, 6 hits, top-1 0.2941; P-2 replayed the R-12 query (24.18 s, top-1 0.1592 on `DOCUMENTATION_SYNC_PLAN.md`); P-3 replayed `SANITIZATION_REPORT` (12.88 s, top-1 0.9638 on `SANITIZATION_REPORT.md` chunk 0). Audit-log line count progression: 102 → 104 (user) → 107 (probes). All append-only. **The literal W-1..W-8 + V-A / V-B sweep was not fully run** — W-4 / W-5 / W-6 / W-7 not exercised; itemised in §3 below | 2026-06-16 | [`2026-06-16_phaseB_validation_applied.md`](2026-06-16_phaseB_validation_applied.md) §3–§7 |

### 1.1 Phase B locked decisions

Only one new locked decision was issued during Phase B:

| # | Decision | When | Source |
|---|---|---|---|
| **D-35** | Custom Model entries that override an existing base model id **MUST** set `base_model_id = NULL` (not `= id`). Rationale: OWUI 0.8.10's `get_all_models` (`utils/models.py:159–175`) silently drops same-id custom rows whose `base_model_id` is non-NULL, which hides `info.meta.toolIds` from `/api/models` and breaks the browser's `tool_ids` auto-attach. Applies to the existing `qwen2.5:7b-instruct` row (fixed 2026-06-16) and any future Model entry created via API/UI/script in this sub-project | 2026-06-16 | Issue T re-investigation + remediation (carried into Phase B as an invariant verified at B-7) |

D-01..D-34 are not modified by Phase B. D-08 (embedder + reranker
pinning), D-13 (`infra_audits` corpus in v1), D-20 (per-model
visibility), D-22 (`myfreetour` returns `empty_collection`), D-23
(Tool source location), D-24 (`class Tools` shape), D-25 (install
workflow), and D-26 (inlined helpers) are all honoured by the
B-4..B-7 deliverables.

## 2. Live state at closure

### 2.1 Qdrant collections (5 — 1 placeholder)

| Collection | Source | Chunks | Files | Status |
|---|---|---:|---:|---|
| `homelab_docs` | `/home/diego/homelab` | 86 | 15 | Active |
| `guardian_cloud` | `/mnt/storage/projects/guardian-cloud` | 872 | 56 | Active (read-only RAG; production code never touched — D-09) |
| `ensambla2` | `/mnt/storage/projects/ensambla2` | 419 | 48 | Active |
| `infra_audits` | `/home/diego/server-audit-2026-06-13` | **280** | **6** | **Active (created 2026-06-16, B-1 / B-2)** |
| `myfreetour` | TBD (B-08) | 0 | 0 | Placeholder, disabled — `rag_search(myfreetour, …)` returns `result_code: empty_collection` per D-22 |

Total: **1 657** active chunks across 4 collections; 1 placeholder.
Dimensionality 384 (`intfloat/multilingual-e5-small`); distance
cosine; payload indexes on `collection` / `source_kind` /
`source_rel`. Counts reflect the documented state at end of B-2
(infra_audits) and the pre-Phase B nightly cron (others); the
nightly 02:30 cron is now unblocked by R-B1.

### 2.2 Open WebUI Tools installed (`webui.db.tool`)

| Tool id | Content (chars) | Specs | Owner | Provenance |
|---|---:|---:|---|---|
| `time_now` | 5 180 | 1 | diego | **Phase A.3** canary (2026-06-15). Returns `{now, unix, weekday, date, time}` for a tz; default `Europe/Madrid` (D-19) |
| `rag_search` | 11 629 | 1 | diego | **Phase B B-6** (2026-06-16). Dense → rerank pipeline over the 5-corpus enum; commit `a7995b3f` |
| `audit_search` | 11 231 | 1 | diego | **Phase B B-6** (2026-06-16). Mirror of `rag_search` with `_COLLECTION = "infra_audits"`; commit `a13d5e94` |
| `system_status` | 507 | 1 | (Jarvis, pre-existing) | Not Amarolab. Phase D will replace it with a `class Tools` HTTP client of `homelab-tools` (D-18 Path C) |
| `docker_containers` | 890 | 1 | (Jarvis, pre-existing) | Not Amarolab. Not visible to qwen2.5 (per-model scope D-20) |
| `docker_logs` | 585 | 1 | (Jarvis, pre-existing) | Not Amarolab. Not visible to qwen2.5 (per-model scope D-20) |

**Only `time_now`, `rag_search`, and `audit_search` are visible to
`qwen2.5:7b-instruct`** via the per-model scope (D-20). The three
pre-existing Jarvis rows remain attached to other models /
admin-default behaviour and were not modified by Phase B.

### 2.3 Model-entry runtime configuration (`webui.db.model`, qwen2.5)

| Field | Value | Rule / source |
|---|---|---|
| `id` | `qwen2.5:7b-instruct` | A.1 (Ollama pull) |
| `base_model_id` | `NULL` | **D-35** — must be `NULL` for OWUI 0.8.10 `get_all_models` to expose `info.meta.toolIds` via `/api/models`; verified by B-7 SQL probe |
| `meta.toolIds` | `["time_now","rag_search","audit_search"]` | **B-7** (Gate G-2). Per-model scope D-20 preserved — the three Tools are attached only to this row |
| `meta.description` | preserved | Phase A.4 |
| `params.system` | v0.1 prompt, 3 342 chars | Phase A.4 v0.1; v0.2 cosmetic carry-overs in §4.2 |
| Workspace `config.DEFAULT_MODELS` | `"qwen2.5:7b-instruct"` | Phase A.4 v0 |

`llama3:latest`, `llama3.2:latest`, `phi3:latest` Model entries
are untouched by Phase B. They do **not** see the three Amarolab
Tools — per-model scope D-20 holds.

### 2.4 Container + filesystem layout

| Knob | Value |
|---|---|
| `openwebui` mounts | `/srv/homelab/data/openwebui:/app/backend/data` (R/W) + `/home/diego/homelab/ai-stack/ingest:/opt/ingest:ro` (added B-3) |
| `openwebui` rollback target | `openwebui_pre_phaseB_20260615235209` (stopped; preserved for G-1 rollback) |
| Audit log | `/srv/homelab/data/openwebui/amarolab-audit.log` (host) ↔ `/app/backend/data/amarolab-audit.log` (container); D-07 / D-21 |
| Tool source | `/home/diego/homelab/ai-stack/openwebui-tools/tools/` (D-23) — `time_now.py`, `rag_search.py` (`a7995b3f`), `audit_search.py` (`a13d5e94`) |
| Ingest package | `ai-stack/ingest/` editable-installed (`pip install -e .` in `install.sh`); `pyproject.toml` present; nightly 02:30 cron unblocked |

## 3. Open evidence items — best-effort follow-ups

The Phase B execution plan §B-8 specifies a literal eight-prompt
sweep plus two add-on probes from the readiness review (V-A,
V-B). The user-driven B-8 exercise + the validation log probes
cover a strict subset. The user has marked B-8 complete; the
following are recorded as **best-effort follow-ups**, not Phase B
blockers, and do not affect the install (B-6), the toolIds
extension (B-7), or the closure decision in §5.

| ID | Required prompt / probe | Status at closure | Notes |
|---|---|---|---|
| **W-1** | `¿qué hora es?` → `time_now` | **Implicit PASS** | Phase A.3 canary and Issue T remediation already exercised the equivalent path (pre-existing audit-log line at `2026-06-15T22:34:39Z`, `time_now / result_code: ok`) |
| **W-2** | `Find mosquitto configuration notes in the homelab docs.` → `rag_search(homelab_docs, …)` | **Partial** | Probe P-1 ran a different `homelab_docs` query ("What is the homelab AI stack architecture?") with `result_code: ok`; the literal mosquitto prompt was not run |
| **W-3** | `What was applied in Phase 0?` → `audit_search` | **De-facto PASS on routing** | The user issued two Spanish/English `audit_search` queries that returned `ok`; the literal Phase 0 prompt was not run, but the routing surface (qwen2.5 → spec build → `audit_search` dispatch → audit log) is proven by §3.1 in [`2026-06-16_phaseB_validation_applied.md`](2026-06-16_phaseB_validation_applied.md) |
| **W-4** | `Search guardian_cloud for recovery flow.` → `rag_search(guardian_cloud, …)` | **NOT run** | The single most valuable follow-up — Guardian Cloud is the largest corpus (872 chunks) and the Phase 1.5 benchmark fixture; running this would cover both the production-RAG path (D-09) and the corpus that V-C numerics live in |
| **W-5** | `Search myfreetour for tours.` → `rag_search(myfreetour, …)` → `empty_collection` | **NOT run** | The only path that exercises the D-22 `empty_collection` short-circuit. Returns the structured refusal that forces the LLM to apologise cleanly instead of silently switching corpora |
| **W-6** | `Please turn on the kitchen light.` → refusal naming Phase C; no audit-log delta | **NOT run** | The D-30 refusal grammar surface for HA. No HA wiring is involved (Phase C); this just verifies the prompt's refusal routing for an HA-shaped ask |
| **W-7** | Re-run the Phase 1.5 reranker benchmark *through the Tool path* against `guardian_cloud`; top-6 ≥ 95 % | **NOT run** | V-C proved the same numerics *off-Tool* inside the container (15/17/19, identical to baseline); W-7 wants the same numbers when the call route is qwen2.5 → spec → `Tools().rag_search(...)`. The plan's exit criterion ("Phase 1.5 reranker benchmark reproduces through the Tool path") technically remains formally unmet, but V-C carries the burden of proof for the underlying pipeline. The expected delta is 0 pp |
| **W-8** | Real browser tab + BX workaround: ask "What was applied in Phase 0?", confirm `[1] <source_rel>` footer | **NOT explicitly run** for the literal prompt | The two user-issued `audit_search` queries are shape-equivalent and returned `ok`; the cited-footer rendering was not separately recorded |
| **V-A** | After R-B1 fix, next nightly 02:30 cron succeeds | **Pending the next cron tick** | Overnight observation; mechanical |
| **V-B** | `info.meta.toolIds == ["time_now","rag_search","audit_search"]` via `/api/v1/models`; no Jarvis tool leak | **Structurally verified by SQL probe** in §2 of the validation log; live `/api/v1/models` read **NOT run** | The SQL probe + the working browser-path runs together prove the same thing (if `info.meta.toolIds` did not surface, the `audit_search` runs in §3 would not have happened) |

**Cheapest path to close all four W-4..W-7 items:** one browser
session with the literal prompts in the table above, followed by
a `tail -n 12 amarolab-audit.log` capture into a follow-up log,
plus one in-container reranker bench replay routed through the
installed `Tools().rag_search(...)` for W-7. The validation log
§9.3 estimates ~30 minutes total. **Not done in this turn.**

## 4. Carry-overs (non-blocking)

These survive Phase B's closure and will be picked up at the
user's discretion.

### 4.1 R-new1 — per-call rerank latency ≈ 10 s

Measured identically on host (ST 3.4.1, 11 124 ms/query) and
container (ST 5.2.3, 11 174 ms/query) over the 20-question
`guardian_cloud` benchmark at DENSE_N = 30. **Property of the
locked (`bge-reranker-v2-m3`, DENSE_N=30) tuple, not a regression
introduced by the container migration.** Possible knob (lowering
DENSE_N) is deferred until real chat usage shows whether the
~10 s rerank cost is a UX problem. **Not a Phase C blocker.**
Detail in
[`2026-06-17_phaseB_vc_validation.md`](2026-06-17_phaseB_vc_validation.md)
§4.3.

### 4.2 Prompt v0.2 (Issues L, B, the `[1]` literal contradiction)

| Issue | What | Fix candidate |
|---|---|---|
| **L** | Short English greeting on turn 1 → Spanish reply (V-6a/b carry-over from A.4). | Drop the "default to Spanish if ambiguous" escape in `# Language`; require per-language matching unconditionally |
| **B** | `rag_search` refusal no longer names "Phase B" (V-8b regressed from v0). With B-6 / B-7 applied, **the refusal copy is also now factually wrong** — `rag_search` is live, not deferred. v0.2 should rewrite this paragraph entirely | Replace the "Phase B" status marker with current routing copy: `rag_search` is the default knowledge tool, `audit_search` is the audit-corpus shortcut, `system_status` stays "Status: Phase D" |
| **`[1]` contradiction** | `# Citations` requires `[1]` inline while `# Tools` CRITICAL RULES forbid writing a literal `[1]`. Only matters in the no-tools-attached fallback path | Replace the contradictory pair with a positive rule: "Only cite when a tool result is present this turn." Drop the literal `time_now(...)` signature line and the literal `[1]` example |

None of these affect Phase C deliverables. v0.2 can land before,
during, or after Phase C at the user's discretion. The B-row in
particular is now stale enough that landing v0.2 before Phase C
chat-testing would avoid one source of confusion when verifying
the HA-related refusals (W-6 / D-30).

### 4.3 BX — Open WebUI 0.8.10 browser-UI WebSocket race

Upstream Open WebUI frontend bug (`A()` helper in `C2Mvb_V1.js`
calls `.json()` on a streaming SSE response when the first send
beats the socket.io handshake). Workaround documented in
[`2026-06-15_openwebui_json_parse_error_analysis.md`](2026-06-15_openwebui_json_parse_error_analysis.md):
LAN-direct UI + hard-refresh + wait for the connection indicator
before the first send. **Survived Phase B unchanged.** Not a
Phase C blocker; Phase C UI verification uses the workaround.

### 4.4 Carry-overs from earlier phases (unchanged)

| # | Item | Status |
|---|---|---|
| C-01 | R-07.2 — Ollama bound to `0.0.0.0:11434` | Acceptable on trusted LAN; deferred |
| C-02 | R-14 — most containers still ad-hoc `docker run` | Will become a soft blocker when Phase D adds containers |
| C-03 | R-09 / R-10 / R-11 / R-13 | System-hardening sweep; post-v1 stable |
| C-04 | Off-site backup mirror | Out of scope for v1 |
| C-05 | Containerise the ingest service | Targeted for v1.1 |
| **B-07** | HA Long-Lived Access Token not issued | **Phase C entrypoint — see §6 below** |
| B-08 | MyFreeTour source path unknown | Phase G |

## 5. Closure decision — criteria check

Phase B exit criteria from
[`../04_ai_system/amarolab-v1/PHASE_B_EXECUTION_PLAN.md`](../04_ai_system/amarolab-v1/PHASE_B_EXECUTION_PLAN.md)
§B-8 plus the readiness-review add-ons:

| Criterion | Met? | Evidence |
|---|---|---|
| `infra_audits` Qdrant collection exists and is indexed off the audit tree | ✓ | B-1 / B-2 (280 chunks) |
| `openwebui` container can load the ingest pipeline | ✓ | B-3 + V-C (`Embedder` / `Reranker` import; 0 pp drift on `guardian_cloud` benchmark) |
| `rag_search` Tool authored and installed in `webui.db` | ✓ | B-4 + B-6 (11 629 chars, 1 spec; commit `a7995b3f`) |
| `audit_search` Tool authored and installed in `webui.db` | ✓ | B-5 + B-6 (11 231 chars, 1 spec; commit `a13d5e94`) |
| qwen2.5 sees both new Tools via `meta.toolIds` (D-20 + D-35 honoured) | ✓ | B-7 SQL probe |
| End-to-end browser path invokes a Phase B Tool, audit log gains `result_code: ok`, no `tool_calls = None` regression | ✓ | B-8 user-issued runs at `2026-06-16T09:58:16Z` and `2026-06-16T10:04:37Z`, both `ok` |
| Equivalent Tool-runtime evidence captured for `rag_search` end-to-end | ✓ | B-8 probe P-1: 22.5 s, 6 hits, top-1 0.2941 |
| Reranker benchmark reproduces through the Tool path (top-6 ≥ 95 % on `guardian_cloud`) | △ **Formally unmet but de-risked** — V-C proved the same numerics off-Tool inside the container at 0 pp drift; on-Tool W-7 not run. **User-accepted gap; tracked in §3** | V-C off-Tool + W-7 marker |
| Full literal W-1..W-8 + V-A / V-B sweep | △ **Partial** — W-1 / W-3 implicit, W-2 partial, W-4 / W-5 / W-6 / W-7 not run, W-8 shape-equivalent only. **User-accepted gap; tracked in §3** | §3 above |
| No functional regression in Phase A deliverables | ✓ | Audit-log line count progression 96 → 107 is monotonic; `time_now` audit lines preserved; qwen2.5 `params.system` / `DEFAULT_MODELS` / `base_model_id` unchanged |

The user has marked B-8 complete with the explicit understanding
that W-4 / W-5 / W-6 / W-7 are best-effort follow-ups; both
"formally unmet" criteria above are gated by the user's decision
and are recorded as such. The hard-criteria block (install,
scope, end-to-end OK on the chat path) is fully met.

**Decision: Phase B is CLOSED.** Phase C is the next phase.

## 6. What Phase B leaves to Phase C — exact starting point

Phase C — Home Assistant integration — owns the **action layer**
of the assistant. It does not need to touch any Tool already
installed; it adds `ha_get_state` (read) and `ha_call_service`
(bounded write) as two new `class Tools` Tools, attaches them to
qwen2.5 via `meta.toolIds`, and proves the refusal path on
out-of-allowlist domains.

### 6.1 Required pre-action (user, in HA UI)

1. **Create dedicated HA user `assistant`.** Not a real account
   for a human — a service identity scoped narrowly to the
   12-domain allowlist (D-12). Group/role: standard user (HA does
   not need admin for `light.turn_on` / `switch.toggle`).
2. **Issue a Long-Lived Access Token (LLAT)** under that user.
   Copy the token; HA shows it once. **Closes blocker B-07.**

Both actions are HA-UI only — not automatable; not done in this
turn (no HA changes — out of scope for Phase B closure).

### 6.2 Required pre-action (user, on the host)

3. **Populate `.env`:** add `HA_BASE_URL` (e.g.
   `http://homeassistant.local:8123` or the LAN IP) and
   `HA_LLAT` (the token from step 2) to
   `/home/diego/homelab/ai-stack/.env` (mode 0600, owner
   `diego:diego`). Confirm with `stat -c '%a %U:%G'` afterwards.
4. **Restart `openwebui` only if `.env` is read at startup;** the
   Tool reads env at lazy-init, so a restart is **not required**
   if the next chat-invoked init picks up the freshly written
   `.env` via container env passthrough. Verify by checking
   `docker exec openwebui printenv | grep ^HA_` before the first
   call.

### 6.3 Phase C work owned by the assistant

5. **C-1 — `tools/ha_get_state.py`**: `class Tools` Tool (D-24),
   audit helper inlined (D-26). One LLM-callable method
   `ha_get_state(entity_id: str)` that GETs
   `${HA_BASE_URL}/api/states/{entity_id}` with
   `Authorization: Bearer ${HA_LLAT}`. Result shape:
   `{entity_id, state, attributes, last_changed, last_updated}`;
   error codes: `bad_entity_id` / `unauthorized` / `not_found` /
   `ha_unreachable` / `ok`.
6. **C-2 — `tools/ha_call_service.py`**: `class Tools` Tool with a
   single `ha_call_service(domain: Literal[…12 domains…],
   service: str, entity_id: str, service_data: dict | None)`
   method that POSTs `${HA_BASE_URL}/api/services/{domain}/{service}`.
   `domain` Literal hardcodes the 12-domain allowlist (D-12).
   Out-of-allowlist domain → `result_code: refused`, audit-log
   line `allowed: false`, polite-refusal string returned.
7. **C-3 — Install both Tools** via `bin/install_tool` (D-25
   workflow). Same install fidelity check as B-6
   (`dump_tools` + `diff` = trailing-newline only).
8. **C-4 — `meta.toolIds` extension** on the qwen2.5 row:
   `["time_now","rag_search","audit_search","ha_get_state","ha_call_service"]`.
   D-35 (`base_model_id = NULL`) preserved unchanged. New Gate
   **G-4**.
9. **C-5 — Refusal test:** chat prompt
   `"please call recorder.purge"` → polite refusal with audit-log
   delta showing `tool: ha_call_service`, `args: {domain:"recorder",...}`,
   `allowed: false`, `result_code: "refused"`. No HA call made.
10. **C-6 — Happy-path test:** chat prompt
    `"turn on the kitchen light"` → `ha_call_service` invokes
    `light.turn_on`, light changes state, audit-log delta with
    `result_code: ok`. Gate **G-5**.
11. **C-7 — Docs + commit:** update CURRENT_STATE / ROADMAP /
    AMAROLAB_HANDOFF; git commit/push C-1..C-6 artefacts;
    hand-off note to Phase D.

### 6.4 Inputs Phase C does NOT touch

- `webui.db.tool` rows for `time_now`, `rag_search`,
  `audit_search` — **unchanged**.
- `webui.db.model.qwen2.5:7b-instruct.base_model_id` — **stays
  `NULL`** (D-35); `meta.toolIds` is extended additively at C-4.
- `params.system` (v0.1 prompt) — **unchanged unless v0.2 ships
  first**; the D-30 HA-refusal grammar is already in v0.1.
- `infra_audits` Qdrant collection — **unchanged**.
- `openwebui` container mounts — **unchanged**; the
  `/opt/ingest:ro` bind mount is sufficient (HA Tools speak HTTP,
  not the ingest pipeline).
- `system_status` Tool replacement — **stays Phase D** (D-18 Path
  C; deferred until the containerized `homelab-tools` +
  `docker-socket-proxy` are built).

## 7. What does *not* change with this closure

- Guardian Cloud read-only RAG access (D-09): unchanged.
- D-01..D-35: all binding, none reversed.
- `llama3:latest`, `llama3.2:latest`, `phi3:latest` Model entries:
  untouched; remain unscoped pass-through models without Amarolab
  Tools (D-20).
- HA tools: still **not yet installed**; gated behind the user's
  HA UI actions in §6.1.
- `system_status` Tool: still Phase D (Path C from D-18 — wait for
  the containerized `homelab-tools` + docker-socket-proxy).
- No Cloudflare exposure of the assistant in v1 (D-15).
- No conversation memory across sessions (D-16); in-session via
  Open WebUI's `webui.db` only.

## 8. Forward references

- Live state post-closure:
  [`../04_ai_system/amarolab-v1/CURRENT_STATE.md`](../04_ai_system/amarolab-v1/CURRENT_STATE.md)
- Updated phase status:
  [`../04_ai_system/amarolab-v1/ROADMAP.md`](../04_ai_system/amarolab-v1/ROADMAP.md)
- Updated handoff context:
  [`../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md`](../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md)
- Phase B execution plan (now historical reference):
  [`../04_ai_system/amarolab-v1/PHASE_B_EXECUTION_PLAN.md`](../04_ai_system/amarolab-v1/PHASE_B_EXECUTION_PLAN.md)
- Phase B validation log (the evidence base for §1 / §2 / §3):
  [`2026-06-16_phaseB_validation_applied.md`](2026-06-16_phaseB_validation_applied.md)

## 9. Forensic state at closure

| Item | Value |
|---|---|
| `webui.db.tool` rows | `audit_search` (11 231 c, 1 spec), `docker_containers`, `docker_logs`, `rag_search` (11 629 c, 1 spec), `system_status`, `time_now` (5 180 c, 1 spec) |
| `webui.db.model.qwen2.5:7b-instruct.meta.toolIds` | `["time_now","rag_search","audit_search"]` |
| `webui.db.model.qwen2.5:7b-instruct.base_model_id` | `NULL` (D-35) |
| `webui.db.model.qwen2.5:7b-instruct.params.system` | v0.1 prompt, 3 342 chars (unchanged from Phase A.4 v0.1) |
| `webui.db.config.DEFAULT_MODELS` | `"qwen2.5:7b-instruct"` |
| `amarolab-audit.log` line count | 107 (carried forward from the validation log §6) |
| Qdrant collections / chunks | 5 collections (`homelab_docs` 86, `guardian_cloud` 872, `ensambla2` 419, `infra_audits` 280, `myfreetour` 0); total 1 657 active chunks |
| Tool source on disk | `time_now.py`, `rag_search.py` (`a7995b3f`), `audit_search.py` (`a13d5e94`) under `/home/diego/homelab/ai-stack/openwebui-tools/tools/` |
| `openwebui` mounts | `/srv/homelab/data/openwebui:/app/backend/data` (R/W) + `/home/diego/homelab/ai-stack/ingest:/opt/ingest:ro` |
| Containers up | `openwebui`, `ollama`, `qdrant` healthy; rollback target `openwebui_pre_phaseB_20260615235209` preserved stopped |
| Pre-flight backups retained | `/tmp/amarolab-phaseA4-backup/webui.db.pre-A4`, `/tmp/amarolab-phaseA4-v0_1-backup/webui.db.pre-v0_1`, plus the `openwebui_pre_phaseB_20260615235209` container as the B-3 G-1 rollback target |
| Open evidence items survived | W-4, W-5, W-6, W-7 (best-effort follow-ups; §3) |
| Open carry-overs survived | R-new1 (rerank latency), v0.2 (prompt cosmetics), BX (browser WebSocket race) |

## 10. What this log deliberately did NOT do

- Did not install or update any Tool (B-6 was applied 2026-06-16
  by the user via `bin/install_tool`).
- Did not edit `meta.toolIds` (B-7 was applied 2026-06-16).
- Did not recreate the `openwebui` container.
- Did not touch `webui.db` (no SQL writes from this closure).
- Did not touch Qdrant.
- Did not call Home Assistant or Guardian Cloud backend.
- Did not run the open W-4 / W-5 / W-6 / W-7 prompts (those
  remain best-effort follow-ups in §3).
- Did not commit or push anything; per the user's "stop after
  documentation review and git status" instruction, the docs are
  the artefact for this turn.

**Phase B is closed.** Phase C entrypoint defined in §6.
