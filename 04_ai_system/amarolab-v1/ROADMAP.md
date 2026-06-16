# ROADMAP — Amarolab Assistant v1

Last updated: 2026-06-16 (Phase B **CLOSED**; closeout log [`../../09_logs/2026-06-16_phaseB_closeout.md`](../../09_logs/2026-06-16_phaseB_closeout.md). Phase C is **NEXT PHASE** — gated by user HA-UI actions (B-07: HA user `assistant` + LLAT). W-4 / W-5 / W-6 / W-7 survive as best-effort follow-ups.)

Phase plan for the Amarolab Assistant v1 sub-project. For the
homelab-wide roadmap see
[`../../00_overview/ROADMAP.md`](../../00_overview/ROADMAP.md).

The canonical phase-by-phase plan with full exit criteria lives in
[`05-implementation-roadmap.md`](05-implementation-roadmap.md). This
file is the **status overlay** on top of that plan: what's done, what's
current, what's next, what's blocked, what's decided.

---

## Completed phases

### Phase 0 — Audit and remediation
- Outcome: R-04 (Mosquitto), R-05 (`WEBUI_SECRET_KEY`), R-06 (docker
  socket removed from openwebui), R-07.1 (Qdrant API key enforced),
  R-12 (Restic backups) all complete.
- Still open from the audit (queued, not blocking v1): R-01, R-07.2,
  R-09, R-10, R-11, R-13, R-14.
- Evidence: `/home/diego/server-audit-2026-06-13/**` and Phase 0
  application logs.

### Phase 1 — RAG foundation
- Outcome: ingest service shipped at `ai-stack/ingest`; 4 Qdrant
  collections populated with 1 377 chunks total; nightly cron at
  02:30; `multilingual-e5-small` embedder cached.
- Evidence:
  [`../../09_logs/2026-06-14_phase1-rag-foundation-applied.md`](../../09_logs/2026-06-14_phase1-rag-foundation-applied.md).

### Phase 1.5 — Reranker benchmark
- Outcome: `BAAI/bge-reranker-v2-m3` integrated into the eval harness;
  top-6 lifted from 80 % to ≥ 95 % on the `guardian_cloud` benchmark.
- Evidence: `04_ai_system/rag-audits/` (reranker benchmark report).

### Phase A.1 — Tool-calling LLM pull
- Date applied: 2026-06-15.
- Outcome: `qwen2.5:7b-instruct` (Q4_K_M, 4.7 GB) pulled into Ollama;
  roadmap smoke test PASS — model emits valid native `tool_calls`.
- Evidence:
  [`../../09_logs/2026-06-15_phaseA1-tool-calling-llm-applied.md`](../../09_logs/2026-06-15_phaseA1-tool-calling-llm-applied.md).

### Phase A.2 — Tool layer design
- Date approved: 2026-06-15.
- Outcome: first three-tool set locked — `time_now`, `rag_search`,
  `system_status`. Five sub-decisions resolved (D-18 … D-22 below).
- Tools deferred out of this phase: `audit_search` (waits for
  `infra_audits` corpus in Phase B), `ha_get_state`, `ha_call_service`
  (Phase C).
- Evidence:
  [`../../09_logs/2026-06-15_phaseA2-tool-layer-design.md`](../../09_logs/2026-06-15_phaseA2-tool-layer-design.md).

### Phase A.3 — Open WebUI Tools scaffold + `time_now` canary
- Date applied: 2026-06-15.
- Outcome: source tree at `/home/diego/homelab/ai-stack/openwebui-tools/`
  (5 files); `time_now` Tool installed in `webui.db` (5180 chars
  content, 1 spec); per-model scoping wired (Model entry for
  `qwen2.5:7b-instruct` with `meta.toolIds=["time_now"]`); audit log
  live at `/srv/homelab/data/openwebui/amarolab-audit.log`.
- Validation: V-1..V-19 PASS; V-20 informational (no regression);
  V-21 PASS. End-to-end happy path returns correct real date/time
  with citation; rate limit exact at 60/min; redaction works; other
  models do not see the Tool.
- Evidence:
  [`../../09_logs/2026-06-15_phaseA3-tool-canary-applied.md`](../../09_logs/2026-06-15_phaseA3-tool-canary-applied.md).

### Phase A.4 v0 — Open WebUI default model + system prompt v0 — APPLIED
- Date applied: 2026-06-15.
- Outcome: `config.DEFAULT_MODELS = "qwen2.5:7b-instruct"`; v0
  system prompt (2 310 chars) installed in `model.params.system`
  on the qwen2.5 row. `meta.toolIds=["time_now"]` and
  `meta.description` preserved. `llama3:latest` (Jarvis) and
  `llama3.2:latest` untouched.
- Validation: **13 / 17 PASS**, 4 FAIL (V-5a, V-6a, V-6b, V-10).
- Decisions added: D-27..D-31 (see below).
- Evidence:
  [`../../09_logs/2026-06-15_phaseA4-default-model-and-prompt-design.md`](../../09_logs/2026-06-15_phaseA4-default-model-and-prompt-design.md)
  and
  [`../../09_logs/2026-06-15_phaseA4-default-model-and-prompt-applied.md`](../../09_logs/2026-06-15_phaseA4-default-model-and-prompt-applied.md).

### Phase A.4 v0.1 — System prompt revision — APPLIED
- Date applied: 2026-06-15.
- Outcome: v0.1 prompt (3 342 chars) replaces v0 on the qwen2.5
  row. `meta.toolIds`, `meta.description`, `DEFAULT_MODELS` all
  unchanged. No services restarted.
- Validation: **15 / 21 PASS at apply time**; remaining six
  failures triaged and reclassified in §"Issue-T resolution"
  below.
- Decisions added: D-32..D-34.
- Evidence:
  [`../../09_logs/2026-06-15_phaseA4-prompt-v0.1-design.md`](../../09_logs/2026-06-15_phaseA4-prompt-v0.1-design.md)
  and
  [`../../09_logs/2026-06-15_phaseA4-prompt-v0.1-applied.md`](../../09_logs/2026-06-15_phaseA4-prompt-v0.1-applied.md).

### Phase A — formally CLOSED
- Date closed: 2026-06-15.
- Decision + criteria check:
  [`../../09_logs/2026-06-15_phaseA_closeout.md`](../../09_logs/2026-06-15_phaseA_closeout.md).
- Issue T (B-09) **resolved** as a validation-methodology
  artefact, not a runtime regression. Evidence:
  [`../../09_logs/2026-06-15_issueT_root_cause_analysis.md`](../../09_logs/2026-06-15_issueT_root_cause_analysis.md).
- New known carry-over **BX — Open WebUI 0.8.10 browser-UI
  WebSocket race**. Workaround documented; durable fix upstream;
  not a Phase B blocker. Evidence:
  [`../../09_logs/2026-06-15_openwebui_json_parse_error_analysis.md`](../../09_logs/2026-06-15_openwebui_json_parse_error_analysis.md).
- Prompt-cosmetic carry-overs (Issue L, Issue B, `[1]` literal
  contradiction in the no-tools fallback) move to a v0.2 prompt
  iteration scheduled at the user's discretion; **not Phase B
  blockers**.
- **Issue T re-opening (2026-06-16).** A live browser test
  reproduced the V-10 / V-12 failure on 2026-06-16, B-09 was
  re-opened, the true root cause was traced to the qwen2.5
  Model entry's `base_model_id` value (same as `id`, causing
  OWUI 0.8.10 to silently drop the custom entry in
  `get_all_models`), and a one-row SQL UPDATE remediation was
  applied the same day. See
  [`../../09_logs/2026-06-15_issueT_browser_validation_reopened.md`](../../09_logs/2026-06-15_issueT_browser_validation_reopened.md)
  (root-cause investigation),
  [`../../09_logs/2026-06-15_issueT_remediation_plan.md`](../../09_logs/2026-06-15_issueT_remediation_plan.md)
  (plan), and
  [`../../09_logs/2026-06-15_issueT_remediation_applied.md`](../../09_logs/2026-06-15_issueT_remediation_applied.md)
  (apply, with browser-equivalent end-to-end validation and the
  `+1` audit-log line that closes B-09 for the second and
  final time). New locked decision **D-35** captures the
  operational rule.

### Phase B preparation — Ingest CLI remediation (R-B1) — APPLIED
- Date applied: 2026-06-16.
- Outcome: discovered during the Phase B readiness review that
  `bin/ingest --help` was failing from any non-package CWD with
  `ModuleNotFoundError: No module named 'ingest'`, and the
  nightly 02:30 cron had been silently failing since at least
  2026-06-15. Root cause: the `ingest` package was not
  pip-installed in its own venv, and the bash wrapper did not
  set `PYTHONPATH` or `cd` to the package root. Fix:
  added a minimal `pyproject.toml` to `ai-stack/ingest/` and
  appended `pip install -e .` to `install.sh`. The
  `ai-stack/ingest/ingest.egg-info/` directory is now excluded
  from git via the existing Python `.gitignore` pattern.
- Validation: `bin/ingest --help` exits 0 from `/home/diego`;
  `bin/ingest status` returns the four pre-existing corpora
  with documented counts (`homelab_docs` 86, `guardian_cloud`
  872, `ensambla2` 419, `myfreetour` 0).
- Evidence:
  [`../../09_logs/2026-06-16_ingest_cli_remediation_analysis.md`](../../09_logs/2026-06-16_ingest_cli_remediation_analysis.md)
  and
  [`../../09_logs/2026-06-16_ingest_cli_remediation_applied.md`](../../09_logs/2026-06-16_ingest_cli_remediation_applied.md).

### Phase B B-1 + B-2 — `infra_audits` corpus — APPLIED
- Date applied: 2026-06-16.
- Outcome: `infra_audits` stanza added to
  `ai-stack/ingest/conf/corpora.yaml` (`type: fs`, include
  `**/*.md`, exclude `**/inspect-snapshots/**` + `**/*.json`).
  Qdrant collection created (384 d, cosine, payload indexes
  on `collection` / `source_kind` / `source_rel`). One-shot
  backfill of the 6 markdown files under
  `/home/diego/server-audit-2026-06-13/` produced 280 chunks.
- Validation: `bin/ingest status` reports the collection as
  enabled with 280 points; dense + reranked spot-check on the
  query "sanitization report" returns chunk 36 of
  `DOCUMENTATION_SYNC_PLAN.md` at score 0.8809 and chunk 0 of
  `SANITIZATION_REPORT.md` at 0.8693.
- Evidence:
  [`../../09_logs/2026-06-16_phaseB_infra_audits_design.md`](../../09_logs/2026-06-16_phaseB_infra_audits_design.md)
  and
  [`../../09_logs/2026-06-16_phaseB_infra_audits_applied.md`](../../09_logs/2026-06-16_phaseB_infra_audits_applied.md).

### Phase B B-3 — Open WebUI bind mount (Gate G-1) — APPLIED
- Date applied: 2026-06-16.
- Outcome: Gate **G-1** approved; `openwebui` container stopped,
  renamed to `openwebui_pre_phaseB_20260615235209` as the
  rollback target, and replaced with a new container carrying
  the same image / ports / env / `proxy_default` attachment
  **plus** the read-only bind mount
  `/home/diego/homelab/ai-stack/ingest:/opt/ingest:ro`.
- Validation: container healthy on both networks; mounts
  verified; `webui.db` MD5 = `656d7295d3cfc00a2255bb0b2230fba1`
  and `amarolab-audit.log` MD5 =
  `310ef8dbfd103685514addacb1ada2c3` both unchanged across
  the recreate; `qwen2.5:7b-instruct` `base_model_id = NULL`
  and `meta.toolIds = ["time_now"]` preserved;
  `from ingest.embedder import Embedder` and
  `from ingest.reranker import Reranker` resolve inside the
  container.
- Evidence:
  [`../../09_logs/2026-06-16_phaseB_openwebui_bind_mount_plan.md`](../../09_logs/2026-06-16_phaseB_openwebui_bind_mount_plan.md)
  and
  [`../../09_logs/2026-06-16_phaseB_openwebui_bind_mount_applied.md`](../../09_logs/2026-06-16_phaseB_openwebui_bind_mount_applied.md).

### Phase B V-C — Container reranker validation — PASS
- Date validated: 2026-06-17.
- Outcome: the openwebui container's `sentence-transformers
  5.2.3` reproduces the documented Phase 1.5 reranker benchmark
  on `guardian_cloud` exactly — top-1 / top-3 / top-6 =
  15 / 17 / 19 (75 % / 85 % / 95 %), 0 pp drift on every
  metric, and all 20 per-question rankings identical to the
  baseline (including the Q12 cross-encoder win, the Q17
  documented regression, and the Q16 empty-file persistent
  miss). One benign `embeddings.position_ids UNEXPECTED`
  load warning, no API breakage. **R-M1 (sentence-transformers
  drift) resolved at zero accuracy drift; R-M3 (cold load)
  recalibrated downwards (~5.6 s total).** New observation
  R-new1 — per-call rerank cost ≈ 10 s / query at DENSE_N=30
  on this hardware — is a property of the locked
  (`bge-reranker-v2-m3`, DENSE_N=30) tuple, measured
  identically on host (ST 3.4.1, 11 124 ms) and container
  (ST 5.2.3, 11 174 ms); not a regression introduced by the
  container migration; **not a Phase B blocker**.
- Evidence:
  [`../../09_logs/2026-06-17_phaseB_vc_validation.md`](../../09_logs/2026-06-17_phaseB_vc_validation.md).

### Phase B B-4 — `rag_search` Tool source — APPLIED
- Date applied: 2026-06-17.
- Outcome: `ai-stack/openwebui-tools/tools/rag_search.py`
  authored as a `class Tools` Open WebUI Tool (D-24) with the
  audit helper inlined via the
  `# @@AMAROLAB_INLINE:audit_helper@@` marker (D-26). Lazy
  `_init()` over `Embedder` / `Reranker` / `QdrantClient`;
  `collection: Literal[…5 corpora…]`; DENSE_N=30,
  TOP_K_DEFAULT=6, CONTENT_CAP=600 (D-08, D-22). Eight result
  codes covering `bad_query` / `bad_k` / `rate_limited` /
  `init_error` / `qdrant_unreachable` / `empty_collection` /
  `rerank_error` / `ok`.
- Local validation: pre/post inline `py_compile` PASS; AST
  shape PASS (single LLM-callable method, Valves nested class,
  Literal annotation); in-container module load + `bad_query`
  probe PASS (no `_init()` invoked).
- Commit: `a7995b3f`.
- Evidence:
  [`../../09_logs/2026-06-17_phaseB_rag_search_design.md`](../../09_logs/2026-06-17_phaseB_rag_search_design.md).

### Phase B B-5 — `audit_search` Tool source — APPLIED
- Date applied: 2026-06-17.
- Outcome:
  `ai-stack/openwebui-tools/tools/audit_search.py` authored as
  a mirror of `rag_search.py`, with the `collection` parameter
  dropped and `_COLLECTION = "infra_audits"` hardcoded
  (03-tools.md §"Tool 2"). Same lazy `_init()` pipeline,
  same DENSE_N / TOP_K / CONTENT_CAP constants, same inlined
  audit helper, same error matrix. Per D-26, the body is
  duplicated rather than cross-imported.
- Local validation: pre/post inline `py_compile` PASS; AST
  shape PASS (`audit_search` args = `[self, query, k]` — no
  `collection`); in-container module load + `bad_query` +
  `bad_k` probes PASS.
- Commit: `a13d5e94`.
- Evidence:
  [`../../09_logs/2026-06-17_phaseB_audit_search_design.md`](../../09_logs/2026-06-17_phaseB_audit_search_design.md).

### Phase B B-6 — Tool install (both Tools) — APPLIED
- Date applied: 2026-06-16.
- Outcome: `bin/install_tool tools/rag_search.py` and
  `bin/install_tool tools/audit_search.py` (D-25 workflow)
  POSTed both inlined sources to `/api/v1/tools/create`. Rows
  present in `webui.db`: `rag_search` (11 629 chars, 1 spec)
  and `audit_search` (11 231 chars, 1 spec); owner `diego`
  admin; `created_at` one second apart.
- Validation: `bin/dump_tools` round-trip + `diff` shows
  install fidelity vs canonical disk source = trailing-newline
  only. Both Tools' JSON specs build correctly under Open
  WebUI 0.8.10 (Literal → enum, docstring → description).
- Evidence:
  [`../../09_logs/2026-06-16_phaseB_validation_applied.md`](../../09_logs/2026-06-16_phaseB_validation_applied.md)
  §1.

### Phase B B-7 — qwen2.5 `meta.toolIds` extension (Gate G-2) — APPLIED
- Date applied: 2026-06-16.
- Outcome: Gate **G-2** approved. qwen2.5 Model entry
  `meta.toolIds` extended from `["time_now"]` to
  `["time_now","rag_search","audit_search"]`. The
  `base_model_id = NULL` rule (D-35, from the Issue T
  re-investigation) is preserved unchanged, so the OWUI 0.8.10
  browser-UI tool-attach path continues to work. Per-model
  scope (D-20) preserved — Tools remain attached only to the
  qwen2.5 row.
- Evidence:
  [`../../09_logs/2026-06-16_phaseB_validation_applied.md`](../../09_logs/2026-06-16_phaseB_validation_applied.md)
  §2.

### Phase B B-8 — End-to-end validation (Gate G-3) — APPLIED (partial)
- Date applied: 2026-06-16.
- Outcome: Gate **G-3** approved. Two browser-path
  `audit_search` queries by the user returned
  `result_code: ok` with realistic timing — a Spanish R-12
  query at 20 694 ms (cold) and `SANITIZATION_REPORT` at
  12 788 ms (warm). This-log probes against the installed Tool
  source dumped from `webui.db` produced additional evidence
  for `rag_search` end-to-end (22.5 s, 6 hits) and replayed
  the `audit_search` queries with matching durations and
  concrete top-3 hits (DOCUMENTATION_SYNC_PLAN / CONSOLIDATION
  for the R-12 query; SANITIZATION_REPORT.md top-1 score
  0.9638 for the literal-term query). **The literal W-1..W-8 +
  V-A / V-B sweep was not fully run**; W-4 / W-5 / W-6 / W-7
  remain open. User marked B-8 complete; gaps tracked in the
  validation log §7.
- Evidence:
  [`../../09_logs/2026-06-16_phaseB_validation_applied.md`](../../09_logs/2026-06-16_phaseB_validation_applied.md).

### Phase B — formally CLOSED
- Date closed: 2026-06-16.
- Decision + criteria check:
  [`../../09_logs/2026-06-16_phaseB_closeout.md`](../../09_logs/2026-06-16_phaseB_closeout.md).
- Outcome: hard-criteria block (install, scope, browser-path
  Tool invocation OK, no Phase A regression) fully met. B-9
  (docs sync) and B-10 (Phase C hand-off note — the closeout
  log) both delivered. Only mechanical git commit/push of the
  Phase B artefacts remains and is user-gated.
- One new locked decision issued during Phase B: **D-35**
  (custom Model entries must set `base_model_id = NULL`; see
  *Decisions taken* below).
- **Open evidence items surviving closure as best-effort
  follow-ups (NOT blockers):** W-4 / W-5 / W-6 / W-7
  (`rag_search(guardian_cloud)`, `rag_search(myfreetour) →
  empty_collection`, HA refusal, Phase 1.5 benchmark
  through-Tool); V-A (next nightly cron observation); V-B
  (live `/api/v1/models` read — SQL probe structurally proves
  it). All itemised in the closeout log §3 and the validation
  log §7.

---

## Current phase

### Phase C — Home Assistant integration (NEXT PHASE)

Phase C implements `ha_get_state` (read) and `ha_call_service`
(bounded write, 12-domain allowlist per D-12), then proves the
refusal grammar (D-30) against out-of-allowlist domains.

Entrypoint and exact starting point:
[`../../09_logs/2026-06-16_phaseB_closeout.md`](../../09_logs/2026-06-16_phaseB_closeout.md)
§6.

Status: **NOT STARTED.** Gated by user actions in the Home
Assistant UI:

- **Blocker B-07 — HA Long-Lived Access Token not issued.**
  Must be created in the HA UI by the user (the dedicated HA
  user `assistant` + its LLAT). Not automatable.
- After B-07 is resolved: populate `HA_BASE_URL` + `HA_LLAT`
  in `/home/diego/homelab/ai-stack/.env` (mode 0600); then
  the assistant can author C-1 (`ha_get_state.py`) and C-2
  (`ha_call_service.py`).

Invariants preserved from Phase B:
- `base_model_id = NULL` on the qwen2.5 row (D-35).
- Per-model scope D-20: HA Tools attach only to qwen2.5.
- `webui.db` Tool rows for `time_now`, `rag_search`,
  `audit_search` are not touched; `meta.toolIds` is extended
  additively at C-4.

---

## Next phases

The numbering matches
[`05-implementation-roadmap.md`](05-implementation-roadmap.md) where
applicable, with the Phase A subdivided into A.1 … A.4 to match how
work has actually been sequenced.

(Phase A.3 and Phase A.4 are CLOSED — see §"Completed phases"
above and the Phase A closeout log
[`../../09_logs/2026-06-15_phaseA_closeout.md`](../../09_logs/2026-06-15_phaseA_closeout.md).)

(Phase B is CLOSED — see §"Completed phases" above and the
Phase B closeout log
[`../../09_logs/2026-06-16_phaseB_closeout.md`](../../09_logs/2026-06-16_phaseB_closeout.md).
Best-effort follow-ups W-4 / W-5 / W-6 / W-7 + V-A / V-B
itemised in the closeout log §3 — not Phase C blockers.)

### Phase C — Home Assistant integration (current — NEXT PHASE)

**Required pre-actions (user, NOT the assistant):**
- **HA UI:** create dedicated HA user `assistant`; issue
  Long-Lived Access Token (closes blocker B-07).
- **Host shell:** populate `HA_BASE_URL` + `HA_LLAT` in
  `/home/diego/homelab/ai-stack/.env` (mode 0600).

**Owned by the assistant:**
- **C-1** — `tools/ha_get_state.py`: `class Tools` Tool (D-24),
  audit helper inlined (D-26). One LLM-callable
  `ha_get_state(entity_id)` that GETs
  `${HA_BASE_URL}/api/states/{entity_id}` with
  `Authorization: Bearer ${HA_LLAT}`. Result codes:
  `bad_entity_id` / `unauthorized` / `not_found` /
  `ha_unreachable` / `ok`.
- **C-2** — `tools/ha_call_service.py`: `class Tools` Tool with
  `ha_call_service(domain: Literal[…12 domains…], service,
  entity_id, service_data)`. `domain` hardcodes the D-12
  allowlist (`light`, `switch`, `scene`, `cover`, `climate`,
  `media_player`, `script`, `automation`, `fan`, `vacuum`,
  `input_boolean`, `input_select`, `input_number`); explicit
  deny on `homeassistant`, `recorder`, `hassio`, `system_log`,
  `backup`, `auth`. Out-of-allowlist → `result_code: refused`,
  `allowed: false`, polite refusal string.
- **C-3** — install both via `bin/install_tool` (D-25 flow);
  install-fidelity check (`dump_tools` + `diff` =
  trailing-newline only).
- **C-4** — extend qwen2.5 `meta.toolIds` to
  `["time_now","rag_search","audit_search","ha_get_state","ha_call_service"]`
  (Gate **G-4**). D-35 (`base_model_id = NULL`) preserved.
  D-20 per-model scope preserved.
- **C-5 — Refusal test:** chat `"please call recorder.purge"`
  → polite refusal; audit-log line `tool: ha_call_service`,
  `domain: "recorder"`, `allowed: false`,
  `result_code: "refused"`; no HA call made.
- **C-6 — Happy-path test:** chat `"turn on the kitchen
  light"` → `ha_call_service` invokes `light.turn_on`; light
  state changes; audit-log line `result_code: ok`. Gate
  **G-5**.
- **C-7** — docs/commit + Phase D hand-off note.

Exit: read + bounded write of HA via tools; refusal path
tested; happy path observed.

Entrypoint definition (the exact starting point at the time of
Phase B closure):
[`../../09_logs/2026-06-16_phaseB_closeout.md`](../../09_logs/2026-06-16_phaseB_closeout.md)
§6.

### Phase C — extra contract notes
- HA Tools speak HTTP only; the `/opt/ingest:ro` bind mount
  from B-3 is **not** required for Phase C.
- HA token (`HA_LLAT`) MUST stay in `.env` only; never paste
  into design docs, state files, or commits.

### Phase D — `system_status` backing service
- Per locked D-18 (Path C), this phase builds the containerized
  `homelab-tools` (FastAPI) + `tecnativa/docker-socket-proxy` on the
  `ai-local_default` network, no host port published.
- Add per-scope endpoints (`/containers`, `/ports`, `/volumes`,
  `/disk`, `/healthz`) — see contract in [`03-tools.md`](03-tools.md).
- Write `tools/system_status.py` as a `class Tools` Open WebUI Tool
  (D-24): thin HTTP client of `HOMELAB_TOOLS_URL`.
- Install via the supported API/UI flow (D-25).
- Disable the bare-metal `homelab-tools.service`. Closes audit R-02.
- Exit: live system data readable from chat; bare-metal Flask service
  is gone.

### Phase E — Acceptance + hardening
- Run the six acceptance questions from
  [`README.md`](README.md) against the live assistant; require
  correct, cited answers on each.
- `/etc/logrotate.d/amarolab-audit` written; 12-week rotation.
- Refusal-test script in `bin/amarolab-health` (or equivalent).
- Walk the security checklist in
  [`04-security-and-permissions.md`](04-security-and-permissions.md).
- Exit: v1 declared "live".

### Phase F — Voice (deferred from v1)
- Wyoming Whisper + Piper containers; HA Assist integration. Out of
  scope for v1 per [`02-target-architecture.md`](02-target-architecture.md).

### Phase G — Unified knowledge (deferred from v1)
- Resolve MyFreeTour corpus source path; index it.
- Continuous-ingest improvements (Open WebUI Knowledge feed,
  per-corpus chunking refinements).

---

## Blockers

Active blockers (resolution required before the phase listed in "phase
blocked" can start):

| # | Blocker | Phase blocked | Owner | Notes |
|---|---|---|---|---|
| B-07 | HA Long-Lived Access Token not issued | C | user | Must be created in HA UI; not automatable |
| B-08 | MyFreeTour source path unknown | G | user | Phase 1 placeholder corpus stays empty until decided |

Resolved blockers (kept for traceability; superseded by locked
decisions D-18 … D-22 and the Phase A closeout):

| # | Blocker | Resolved on | Resolution |
|---|---|---|---|
| B-01 | Phase A.2 design unapproved | 2026-06-15 | Approved by user; see D-18..D-22 |
| B-02 | A.2 Q1: `system_status` backing path | 2026-06-15 | Path C — defer implementation to Phase D (D-18) |
| B-03 | A.2 Q2: `time_now` default timezone | 2026-06-15 | `Europe/Madrid` (D-19) |
| B-04 | A.2 Q3: Function visibility scope | 2026-06-15 | `qwen2.5:7b-instruct` only (D-20) |
| B-05 | A.2 Q4: confirm audit-log host path | 2026-06-15 | Confirmed `/srv/homelab/data/openwebui/amarolab-audit.log` (re-affirms D-07) |
| B-06 | A.2 Q5: `myfreetour` enum treatment | 2026-06-15 | Leave in enum; return `empty_collection` (D-22) |
| B-09 | Tool-calling regression with custom `params.system` (Issue T) — `time_now` not invoked from chat | 2026-06-15 → re-opened 2026-06-16 → re-resolved 2026-06-16 | **2026-06-15 (incorrect):** diagnosed as a validation-methodology artefact (validator omitted `tool_ids`). **2026-06-16 re-investigation:** a live browser test reproduced the failure; real root cause is the qwen2.5 Model entry's `base_model_id = "qwen2.5:7b-instruct"` (same as `id`), which sends it to OWUI 0.8.10's `elif … continue` skip branch in `utils/models.py:159–175`. The custom entry was silently dropped from `/api/models`, so the browser's auto-attach (`ee.info.meta.toolIds` in `GxGTGtKc.js`) had no `info` to read and `tool_ids` never made it into the request body. **Remediated 2026-06-16** with a one-row SQL UPDATE setting `base_model_id = NULL`; browser-equivalent validation green; audit log gained one fresh `time_now / result_code: ok` line at `2026-06-15T22:34:39Z`. Captured as locked decision **D-35**. Evidence: [`../../09_logs/2026-06-15_issueT_browser_validation_reopened.md`](../../09_logs/2026-06-15_issueT_browser_validation_reopened.md), [`../../09_logs/2026-06-15_issueT_remediation_plan.md`](../../09_logs/2026-06-15_issueT_remediation_plan.md), [`../../09_logs/2026-06-15_issueT_remediation_applied.md`](../../09_logs/2026-06-15_issueT_remediation_applied.md). The prior partially-incorrect analysis is preserved at [`../../09_logs/2026-06-15_issueT_root_cause_analysis.md`](../../09_logs/2026-06-15_issueT_root_cause_analysis.md) for traceability. |

Non-blocking carry-overs (do not stop any v1 phase, listed for
visibility):

| # | Item | Notes |
|---|---|---|
| C-01 | R-07.2 — Ollama bound to `0.0.0.0:11434` | Acceptable on trusted LAN; deferred per [`01-current-state-review.md`](01-current-state-review.md) |
| C-02 | R-14 — most containers still ad-hoc `docker run` | Will become a soft blocker when Phase D adds new containers; queued for batch fix |
| C-03 | R-09 / R-10 / R-11 / R-13 | System-hardening sweep, do after v1 is stable |
| C-04 | Off-site backup mirror | Out of scope for v1 |
| C-05 | Containerise the ingest service | Cleaner backup story; targeted for v1.1 |
| BX | Open WebUI 0.8.10 browser-UI WebSocket race — `Unexpected token 'd', "data: {"id"... is not valid JSON` shown to the user when the first chat is sent before socket.io has connected | Upstream Open WebUI frontend bug (helper `A()` in `C2Mvb_V1.js` calls `.json()` on a streaming SSE response). Workaround: LAN-direct UI + hard-refresh + wait for the connection indicator. Evidence: [`../../09_logs/2026-06-15_openwebui_json_parse_error_analysis.md`](../../09_logs/2026-06-15_openwebui_json_parse_error_analysis.md). Not a Phase B blocker; Phase B UI verification uses the workaround |
| v0.2 | Prompt-cosmetic carry-overs: Issue L (short English greeting), Issue B (refusal copy now factually stale since `rag_search` is live, not deferred — Phase B closeout §4.2 has the updated fix candidate), `[1]` literal contradiction in the no-tools fallback path | Tracked in the Phase A closeout [`../../09_logs/2026-06-15_phaseA_closeout.md`](../../09_logs/2026-06-15_phaseA_closeout.md) §3.1 and the Phase B closeout [`../../09_logs/2026-06-16_phaseB_closeout.md`](../../09_logs/2026-06-16_phaseB_closeout.md) §4.2. Can land before, during, or after Phase C at the user's discretion |
| R-new1 | Per-call rerank latency ≈ 10 s on this hardware at DENSE_N=30 (`bge-reranker-v2-m3`); host and container measure identically | Not introduced by the container migration. Documented in [`../../09_logs/2026-06-17_phaseB_vc_validation.md`](../../09_logs/2026-06-17_phaseB_vc_validation.md) §4.3 and carried into the Phase B closeout [`../../09_logs/2026-06-16_phaseB_closeout.md`](../../09_logs/2026-06-16_phaseB_closeout.md) §4.1. B-8 chat behaviour showed the cost at 20.7 s cold / 12.8 s warm; possible DENSE_N knob deferred — not a Phase C blocker. |
| W-4..W-7 | Best-effort follow-up evidence items surviving Phase B closure: W-4 `rag_search(guardian_cloud)`, W-5 `rag_search(myfreetour) → empty_collection`, W-6 HA refusal, W-7 Phase 1.5 reranker bench through-Tool path | Itemised in the Phase B closeout [`../../09_logs/2026-06-16_phaseB_closeout.md`](../../09_logs/2026-06-16_phaseB_closeout.md) §3 and the validation log [`../../09_logs/2026-06-16_phaseB_validation_applied.md`](../../09_logs/2026-06-16_phaseB_validation_applied.md) §7. ~30 min total to close in one browser session; user-gated; not a Phase C blocker. |

Resolved during Phase B execution (kept here for traceability;
not blockers anymore):

| # | Item | Resolved on | Resolution |
|---|---|---|---|
| R-B1 | Ingest CLI broken (`bin/ingest` raised `ModuleNotFoundError` from any CWD outside the package dir; nightly cron failing) | 2026-06-16 | Added `pyproject.toml` + `pip install -e .` in `install.sh`. See [`../../09_logs/2026-06-16_ingest_cli_remediation_applied.md`](../../09_logs/2026-06-16_ingest_cli_remediation_applied.md). |
| R-M1 | `sentence-transformers` major-version drift between ingest venv (3.4.1) and openwebui container (5.2.3) — risk of reranker score drift | 2026-06-17 | V-C measured **0 pp drift** on every metric of the Phase 1.5 benchmark; all 20 per-question ranks identical. See [`../../09_logs/2026-06-17_phaseB_vc_validation.md`](../../09_logs/2026-06-17_phaseB_vc_validation.md). |
| R-M3 | Lazy-init cold-load timeout on first `rag_search` call | 2026-06-17 | Recalibrated downwards: 5.6 s total (embedder 4.19 s + reranker 1.35 s), well under the 8-25 s estimate. Plan's post-install warm-up curl will absorb it. |

---

## Decisions taken (locked)

These are the binding decisions made for v1. Reversing one requires an
explicit user decision and a new design entry.

| # | Decision | When | Source |
|---|---|---|---|
| D-01 | Primary tool-calling LLM = `qwen2.5:7b-instruct` (Q4_K_M) | 2026-06-15 | Phase A architecture review |
| D-02 | `llama3:latest` (Llama 3.0 8B Q4_0) retained as fallback non-tool chat | 2026-06-15 | same |
| D-03 | Do **not** pull `llama3.1:8b-instruct` in Phase A | 2026-06-15 | same |
| D-04 | Open WebUI's Tools subsystem is the tool runtime (no separate tool server). *(v1 design called this "Functions"; Open WebUI 0.8.10's term is "Tools" — see D-24.)* | Pre-A (v1 design) | [`02-target-architecture.md`](02-target-architecture.md) |
| D-05 | `amarolab_common.py` is the single shared helper (audit + rate limit + redact) | v1 design | [`03-tools.md`](03-tools.md) |
| D-06 | Trust model: LLM is adversarial; allowlists are file-level constants; no `eval`, `subprocess`, or path-from-arg | v1 design | [`04-security-and-permissions.md`](04-security-and-permissions.md) |
| D-07 | Audit-log path: `/srv/homelab/data/openwebui/amarolab-audit.log` (host) | v1 design | [`04-security-and-permissions.md`](04-security-and-permissions.md) |
| D-08 | Embedder = `intfloat/multilingual-e5-small` (384-dim); reranker = `BAAI/bge-reranker-v2-m3`; not swapped in v1 | Phase 1 / 1.5 | Phase 1.5 benchmark |
| D-09 | Guardian Cloud is production; RAG read-only over its docs; never call its backend API | Pre-existing | top-level homelab rule |
| D-10 | First three tools to implement = `time_now`, `rag_search`, `system_status` | 2026-06-15 | Phase A.2 scope as set by user |
| D-11 | HA tools (`ha_get_state`, `ha_call_service`) deferred to Phase C; no HA-related changes before then | 2026-06-15 | user |
| D-12 | HA control allowlist = 12 domains (`light`, `switch`, `scene`, `cover`, `climate`, `media_player`, `script`, `automation`, `fan`, `vacuum`, `input_boolean`, `input_select`, `input_number`); explicitly deny `homeassistant`, `recorder`, `hassio`, `system_log`, `backup`, `auth`, etc. | v1 design | [`04-security-and-permissions.md`](04-security-and-permissions.md) |
| D-13 | `infra_audits` corpus included in v1 (Phase B), single-user posture makes it safe | v1 design | [`02-target-architecture.md`](02-target-architecture.md) |
| D-14 | No voice in v1 (Whisper/Piper deferred to Phase F) | v1 design | user request |
| D-15 | No public exposure of the assistant via Cloudflare in v1; LAN/tailnet only | v1 design | [`02-target-architecture.md`](02-target-architecture.md) |
| D-16 | No conversation memory across sessions in v1; in-session only via Open WebUI's webui.db | v1 design | [`02-target-architecture.md`](02-target-architecture.md) |
| D-17 | Out-of-band: VSCode Remote machine settings written with `search.followSymlinks: false` + Steam Proton excludes | 2026-06-15 | Investigation report (outside repo) |
| D-18 | `system_status` backing path = **C (defer to Phase D)**. No bare-metal Flask call in A.2/A.3; the Tool is not implemented until the containerized `homelab-tools` + `docker-socket-proxy` are built in Phase D | 2026-06-15 | Phase A.2 approval |
| D-19 | `time_now` default timezone = `Europe/Madrid`. `format` enum is `iso` (default) / `human` / `unix`; all four representations (`now`, `unix`, `weekday`, `date`+`time`) are always returned regardless of `format` | 2026-06-15 | Phase A.2 approval |
| D-20 | Open WebUI per-Tool visibility = **`qwen2.5:7b-instruct` only**. The three A.2 tools (and any future tool) are scoped to the primary tool-calling model; `llama3:latest` / `llama3.2` / `phi3` do not see them | 2026-06-15 | Phase A.2 approval |
| D-21 | Audit-log host path **confirmed** as `/srv/homelab/data/openwebui/amarolab-audit.log` (container path `/app/backend/data/amarolab-audit.log`). No deviation from D-07 | 2026-06-15 | Phase A.2 approval |
| D-22 | `rag_search` collection enum **keeps** `myfreetour`. When called, the Tool returns `{"error":"empty_collection","code":"empty_collection"}` until the corpus is indexed (Phase G). Forces the LLM to apologise cleanly instead of silently picking another corpus | 2026-06-15 | Phase A.2 approval |
| D-23 | **Tool source location** = `/home/diego/homelab/ai-stack/openwebui-tools/` (sibling to `ai-stack/ingest/`). Tracked in the homelab git repo; synced to GitHub. The bind-mounted `/srv/homelab/data/openwebui/` is **not** used to hold Tool source — Open WebUI 0.8.10 does not auto-discover Tools from disk | 2026-06-15 | Phase A.3 plan revision after Open WebUI 0.8.10 compatibility audit |
| D-24 | **Tool code shape** = `class Tools` with type-hinted methods. Module-level callables are not supported by Open WebUI 0.8.10's tool loader (`load_tool_module_by_id` requires `hasattr(module, "Tools")` and raises otherwise). Each public, non-class, non-underscore attribute of the `Tools()` instance becomes a separately-callable tool | 2026-06-15 | Compatibility report §3 |
| D-25 | **Tool install workflow** = the supported Open WebUI API/UI flow: `POST /api/v1/tools/create` (or admin UI: Workspace → Tools → "+"). Open WebUI stores the source in `webui.db`. The disk-side `openwebui-tools/tools/*.py` files are the canonical version-controlled copy; the DB row is the runtime copy. Edits round-trip via `POST /api/v1/tools/id/{id}/update` | 2026-06-15 | Compatibility report §5 |
| D-26 | **Shared helper handling** = inline the audit / RateLimiter / redaction helper in each Tool file. Open WebUI executes each Tool in its own `tool_{id}` module namespace; cross-Tool `import` does not work. For v1, accept ~30 lines of duplicated audit code per Tool; revisit at v2 if the Tool count grows. (The canonical helper text still lives once at `openwebui-tools/lib/audit_helper.py` and is textually inlined by the install helper.) | 2026-06-15 | Compatibility report §7 |
| D-27 | **System-prompt scope** = per-model only, attached to the `qwen2.5:7b-instruct` Model entry. Other models (`llama3:latest`, `llama3.2:latest`) remain clean | 2026-06-15 | Phase A.4 design approval |
| D-28 | **Persona** = "Amarolab Assistant"; default language Spanish; style concise / technical / practical; prefer documented facts over assumptions | 2026-06-15 | Phase A.4 design approval |
| D-29 | **Tool routing description** in the system prompt names all three Phase A.2 tools (`time_now`, `rag_search`, `system_status`) with current implementation status, so the prompt is forward-compatible with Phase B and Phase D | 2026-06-15 | Phase A.4 design approval |
| D-30 | **Refusal block** for four out-of-scope action classes: Home Assistant control (Phase C), shell exec, filesystem writes, Guardian Cloud backend changes. Refusal names the planned phase when applicable | 2026-06-15 | Phase A.4 design approval |
| D-31 | **Citation grammar** = `[N]` inline + final `[N] <source>` list; extends from `time_now` today to `rag_search` in Phase B. Refined by D-34 | 2026-06-15 | Phase A.4 design approval |
| D-32 | **First-turn self-introduction** is mandatory in the system prompt: single short opening sentence identifying as "Amarolab Assistant" on the first reply of a conversation only | 2026-06-15 | Phase A.4 v0.1 design |
| D-33 | **Tool invocation rule** in the system prompt: the model MUST issue a real tool call (never describe one in text, never write literal `[N]` placeholders) when a wired tool can answer the question. *Aspirational on qwen2.5 until Issue T is resolved.* | 2026-06-15 | Phase A.4 v0.1 design |
| D-34 | **Citation precondition**: a citation may only be rendered after an actual tool invocation that returned a result. Refines (does not replace) D-31's citation grammar. Honoured by qwen2.5 as of the Issue T remediation 2026-06-16 (the model now actually invokes the tool before citing). | 2026-06-15 | Phase A.4 v0.1 design |
| D-35 | **Custom Model entries that override an existing base model id MUST set `base_model_id = NULL`** (not `= id`). Rationale: OWUI 0.8.10's `get_all_models` (`utils/models.py:159–175`) silently drops same-id custom rows whose `base_model_id` is non-NULL, which hides `info.meta.toolIds` from `/api/models` and breaks the browser's `tool_ids` auto-attach. Applies to: the existing `qwen2.5:7b-instruct` row (fixed 2026-06-16); any future Model entry created via API/UI/script in this sub-project. The Tool runtime contract (D-23..D-26) is unchanged; this is a Model-entry shape rule one level above it. | 2026-06-16 | Issue T re-investigation + remediation |
| D-23 | **Tool source location** = `/home/diego/homelab/ai-stack/openwebui-tools/` (sibling to `ai-stack/ingest/`). Tracked in the homelab git repo; synced to GitHub. The bind-mounted `/srv/homelab/data/openwebui/` is **not** used to hold Tool source — Open WebUI 0.8.10 does not auto-discover Tools from disk | 2026-06-15 | Phase A.3 plan revision after Open WebUI 0.8.10 compatibility audit |
| D-24 | **Tool code shape** = `class Tools` with type-hinted methods. Module-level callables are not supported by Open WebUI 0.8.10's tool loader (`load_tool_module_by_id` requires `hasattr(module, "Tools")` and raises otherwise). Each public, non-class, non-underscore attribute of the `Tools()` instance becomes a separately-callable tool | 2026-06-15 | Compatibility report §3 |
| D-25 | **Tool install workflow** = the supported Open WebUI API/UI flow: `POST /api/v1/tools/create` (or admin UI: Workspace → Tools → "+"). Open WebUI stores the source in `webui.db`. The disk-side `openwebui-tools/tools/*.py` files are the canonical version-controlled copy; the DB row is the runtime copy. Edits round-trip via `POST /api/v1/tools/id/{id}/update` | 2026-06-15 | Compatibility report §5 |
| D-26 | **Shared helper handling** = inline the audit / RateLimiter / redaction helper in each Tool file. Open WebUI executes each Tool in its own `tool_{id}` module namespace; cross-Tool `import` does not work. For v1, accept ~30 lines of duplicated audit code per Tool; revisit at v2 if the Tool count grows. (The canonical helper text still lives once at `openwebui-tools/lib/audit_helper.py` and is textually inlined by the install helper.) | 2026-06-15 | Compatibility report §7 |
