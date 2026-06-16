# AMAROLAB_HANDOFF — Amarolab Assistant v1

Last updated: 2026-06-17

## Purpose

This file rebuilds **Amarolab Assistant v1 sub-project** context for any
future AI session without conversation history. For homelab-wide
context, see [`../../00_overview/AMAROLAB_HANDOFF.md`](../../00_overview/AMAROLAB_HANDOFF.md).

## Project purpose

Build a fully local AI assistant grounded by:

- Indexed homelab and product documentation (RAG over Qdrant).
- Live infrastructure state (containers, ports, volumes, disk).
- Home Assistant entity state and bounded control (Phase C, deferred).

Two front doors planned long-term: Open WebUI (chat) and Home Assistant
(voice). v1 is chat-only.

Constraints (non-negotiable):

- Single user (`diego`).
- Read-mostly. Write surface is narrow and per-tool allowlisted.
- Guardian Cloud is **production** — read-only RAG over its docs only.
  Never call its backend, never modify its source tree.
- Everything local. No external LLM calls. No public exposure of the
  assistant via Cloudflare in v1.

## Architecture summary

```
USER (LAN 192.168.178.0/24 / Tailnet)
   │
   ▼
Open WebUI :3000      ◄── chat UI + Tools runtime (Python)
   │
   ▼
Ollama :11434
   ├─ qwen2.5:7b-instruct  (primary, tool-calling, pulled 2026-06-15)
   └─ llama3:latest        (fallback non-tool chat)
   │
   ▼ (Open WebUI Tools — partial; scoped to qwen2.5:7b-instruct per D-20)
   ┌──────────────────────────────────────────────────────────────┐
   │ time_now()           — APPLIED (Phase A.3, 2026-06-15)       │
   │ rag_search()         — designed (Phase A.2); wired in Phase B│
   │ system_status()      — designed (Phase A.2); wired in Phase D│
   │ audit_search()       — Phase B                               │
   │ ha_get_state()       — Phase C                               │
   │ ha_call_service()    — Phase C (12-domain allowlist)         │
   └──────────────────────────────────────────────────────────────┘
   │
   ▼
Qdrant :6333  (API key enforced)
   ├─ homelab_docs     (86 chunks)
   ├─ guardian_cloud   (872 chunks)
   ├─ ensambla2        (419 chunks)
   ├─ myfreetour       (empty placeholder)
   └─ infra_audits     (Phase B)

Embedder:  intfloat/multilingual-e5-small  (384-dim, cached on host)
Reranker:  BAAI/bge-reranker-v2-m3         (top-6 ≥ 95% on bench)

Ingest: bare-metal venv, cron 02:30 daily, writes to Qdrant only.
```

## Current phase

**Phase B — Knowledge Tool + audit corpus.** **B-1..B-8
applied.** As of 2026-06-17, both Phase B Tools (`rag_search`,
`audit_search`) are authored, committed, installed in
`webui.db`, and attached to the `qwen2.5:7b-instruct` Model
entry's `meta.toolIds`. Browser-path end-to-end was exercised
by the user on `audit_search` with two `result_code: ok` runs;
Tool-runtime evidence for `rag_search` end-to-end was captured
via a read-only probe against the installed source. **Gates
G-1, G-2, G-3 all approved.** Only **B-9 (docs sync + git
commit/push)** and **B-10 (Phase C hand-off note)** remain.
The literal W-4 / W-5 / W-6 / W-7 prompts from the formal B-8
plan exit were not exercised; tracked in the validation log
§7 as best-effort follow-ups. Execution plan in
[`PHASE_B_EXECUTION_PLAN.md`](PHASE_B_EXECUTION_PLAN.md);
status overlay in [`ROADMAP.md`](ROADMAP.md).

**Phase A is formally CLOSED** as of 2026-06-15. Closure decision +
criteria check in
[`../../09_logs/2026-06-15_phaseA_closeout.md`](../../09_logs/2026-06-15_phaseA_closeout.md).
Phase A applied set (all live):

- Phase A.1 (qwen2.5 pull + tool-calling smoke test) — **APPLIED**
  2026-06-15. See
  [`../../09_logs/2026-06-15_phaseA1-tool-calling-llm-applied.md`](../../09_logs/2026-06-15_phaseA1-tool-calling-llm-applied.md).
- Phase A.2 (three-tool design lock-in: `time_now`, `rag_search`,
  `system_status`) — **APPROVED** 2026-06-15 with 5 locked decisions
  (D-18..D-22 in [`ROADMAP.md`](ROADMAP.md)). See
  [`../../09_logs/2026-06-15_phaseA2-tool-layer-design.md`](../../09_logs/2026-06-15_phaseA2-tool-layer-design.md).
- Open WebUI 0.8.10 Tools API audit — **APPROVED** 2026-06-15. See
  [`../../FUNCTIONS_COMPATIBILITY_REPORT.md`](../../FUNCTIONS_COMPATIBILITY_REPORT.md).
  Four additional decisions locked (D-23..D-26).
- Phase A.3 (Open WebUI Tools scaffold + `time_now` canary) —
  **APPLIED** 2026-06-15. Source tree at
  `/home/diego/homelab/ai-stack/openwebui-tools/` (5 files);
  `time_now` Tool installed in `webui.db` (5180 chars, 1 spec);
  per-model scoping wired (`qwen2.5:7b-instruct` Model entry with
  `meta.toolIds=["time_now"]`); audit log live at
  `/srv/homelab/data/openwebui/amarolab-audit.log`. 19/21 V-checks
  PASS, 1 informational, 1 PASS. See
  [`../../09_logs/2026-06-15_phaseA3-tool-canary-applied.md`](../../09_logs/2026-06-15_phaseA3-tool-canary-applied.md).
- Phase A.4 v0 (default model + system prompt v0) — **APPLIED**
  2026-06-15. Five new locked decisions (D-27..D-31). See
  [`../../09_logs/2026-06-15_phaseA4-default-model-and-prompt-applied.md`](../../09_logs/2026-06-15_phaseA4-default-model-and-prompt-applied.md).
- Phase A.4 v0.1 (system prompt revision) — **APPLIED** 2026-06-15
  with three new locked decisions (D-32..D-34). v0.1 prompt
  (3 342 chars) attached to qwen2.5 Model entry. See
  [`../../09_logs/2026-06-15_phaseA4-prompt-v0.1-applied.md`](../../09_logs/2026-06-15_phaseA4-prompt-v0.1-applied.md).
- **Issue T (B-09)** — **RESOLVED 2026-06-15 → REOPENED 2026-06-16
  → RE-RESOLVED 2026-06-16.** Initial 2026-06-15 diagnosis (validator
  omitted `tool_ids`) was correct *for the validator path only* but
  wrong about the browser path. Real root cause: the
  `qwen2.5:7b-instruct` Model entry was created with
  `base_model_id` equal to its own `id`, which OWUI 0.8.10's
  `get_all_models` (`utils/models.py:159–175`) silently drops from
  `/api/models`. The browser's auto-attach (`ee.info.meta.toolIds`
  in `GxGTGtKc.js`) therefore had no `info` to read and
  `tool_ids` never made it into the chat-completion body. Fix:
  one-row SQL UPDATE setting `base_model_id = NULL`. Apply day
  validation: `+1` audit-log line at `2026-06-15T22:34:39Z`,
  `result_code: ok`. New locked decision **D-35** captures the
  rule. Evidence:
  [`../../09_logs/2026-06-15_issueT_browser_validation_reopened.md`](../../09_logs/2026-06-15_issueT_browser_validation_reopened.md)
  (root cause),
  [`../../09_logs/2026-06-15_issueT_remediation_plan.md`](../../09_logs/2026-06-15_issueT_remediation_plan.md)
  (plan),
  [`../../09_logs/2026-06-15_issueT_remediation_applied.md`](../../09_logs/2026-06-15_issueT_remediation_applied.md)
  (apply). The 2026-06-15 partially-incorrect analysis is preserved
  at
  [`../../09_logs/2026-06-15_issueT_root_cause_analysis.md`](../../09_logs/2026-06-15_issueT_root_cause_analysis.md)
  for traceability.
- **New carry-over BX — Open WebUI 0.8.10 browser-UI WebSocket
  race** (`Unexpected token 'd', "data: {"id"... is not valid JSON`
  shown when the first message is sent before socket.io connects).
  Upstream frontend bug; workaround in
  [`../../09_logs/2026-06-15_openwebui_json_parse_error_analysis.md`](../../09_logs/2026-06-15_openwebui_json_parse_error_analysis.md).
  Not a Phase B blocker.

## Mandatory reading order

For a future session resuming work, read in this order:

1. This file (`AMAROLAB_HANDOFF.md`).
2. [`CURRENT_STATE.md`](CURRENT_STATE.md) — live state of the sub-project.
3. [`ROADMAP.md`](ROADMAP.md) — phases, blockers, decisions taken.
4. [`README.md`](README.md) — design package overview.
5. [`01-current-state-review.md`](01-current-state-review.md) — pre-design state snapshot.
6. [`02-target-architecture.md`](02-target-architecture.md) — v1 target shape.
7. [`03-tools.md`](03-tools.md) — full tool catalog (superset of Phase A.2). **Read with the amendments banner at the top in mind**; Open WebUI 0.8.10's actual runtime contract is captured in §11 below.
8. [`04-security-and-permissions.md`](04-security-and-permissions.md) — trust model, allowlists, audit.
9. [`05-implementation-roadmap.md`](05-implementation-roadmap.md) — phase-by-phase plan with exit criteria.
10. [`../../FUNCTIONS_COMPATIBILITY_REPORT.md`](../../FUNCTIONS_COMPATIBILITY_REPORT.md) — **MANDATORY** for anyone implementing Tools. Source-grounded Open WebUI 0.8.10 contract: `class Tools`, JSON-Schema build, install path, valves, frontmatter.
11. **Phase A closure & current state** — read these together:
    - [`../../09_logs/2026-06-15_phaseA_closeout.md`](../../09_logs/2026-06-15_phaseA_closeout.md) — durable closure record.
    - [`../../09_logs/2026-06-15_issueT_root_cause_analysis.md`](../../09_logs/2026-06-15_issueT_root_cause_analysis.md) — the **2026-06-15** partially-correct B-09 diagnosis (kept for traceability).
    - [`../../09_logs/2026-06-15_openwebui_json_parse_error_analysis.md`](../../09_logs/2026-06-15_openwebui_json_parse_error_analysis.md) — BX workaround for UI verification.
12. **Issue T re-opening (2026-06-16) — read in order**:
    - [`../../09_logs/2026-06-15_issueT_browser_validation_reopened.md`](../../09_logs/2026-06-15_issueT_browser_validation_reopened.md) — the corrected B-09 root cause (`base_model_id = id` collision with the OWUI 0.8.10 model-merge skip branch).
    - [`../../09_logs/2026-06-15_issueT_remediation_plan.md`](../../09_logs/2026-06-15_issueT_remediation_plan.md) — the minimal remediation plan.
    - [`../../09_logs/2026-06-15_issueT_remediation_applied.md`](../../09_logs/2026-06-15_issueT_remediation_applied.md) — the apply log, including browser-equivalent end-to-end validation and the audit-log `+1` proof.
13. **Phase B execution plan** — [`PHASE_B_EXECUTION_PLAN.md`](PHASE_B_EXECUTION_PLAN.md). Read before touching anything for Phase B.
14. **Phase B readiness + applied work (2026-06-16 / 2026-06-17) — read in order**:
    - [`../../09_logs/2026-06-16_phaseB_execution_readiness_review.md`](../../09_logs/2026-06-16_phaseB_execution_readiness_review.md) — readiness verdict that discovered R-B1 and added V-C as a pre-empt for R-M1.
    - [`../../09_logs/2026-06-16_phaseB_rag_inventory_and_gap_analysis.md`](../../09_logs/2026-06-16_phaseB_rag_inventory_and_gap_analysis.md) — RAG inventory probe.
    - [`../../09_logs/2026-06-16_ingest_cli_remediation_analysis.md`](../../09_logs/2026-06-16_ingest_cli_remediation_analysis.md) and [`../../09_logs/2026-06-16_ingest_cli_remediation_applied.md`](../../09_logs/2026-06-16_ingest_cli_remediation_applied.md) — R-B1 (ingest CLI) analysis + remediation (`pyproject.toml` + `pip install -e .`).
    - [`../../09_logs/2026-06-16_phaseB_infra_audits_design.md`](../../09_logs/2026-06-16_phaseB_infra_audits_design.md) and [`../../09_logs/2026-06-16_phaseB_infra_audits_applied.md`](../../09_logs/2026-06-16_phaseB_infra_audits_applied.md) — B-1 + B-2 (`infra_audits` corpus, 280 chunks).
    - [`../../09_logs/2026-06-16_phaseB_openwebui_bind_mount_plan.md`](../../09_logs/2026-06-16_phaseB_openwebui_bind_mount_plan.md) and [`../../09_logs/2026-06-16_phaseB_openwebui_bind_mount_applied.md`](../../09_logs/2026-06-16_phaseB_openwebui_bind_mount_applied.md) — B-3 (`openwebui` recreate with `/opt/ingest:ro`, Gate G-1 approved, rollback container `openwebui_pre_phaseB_20260615235209` preserved).
    - [`../../09_logs/2026-06-17_phaseB_vc_validation.md`](../../09_logs/2026-06-17_phaseB_vc_validation.md) — V-C reranker validation **PASS**, R-M1 resolved.
    - [`../../09_logs/2026-06-17_phaseB_rag_search_design.md`](../../09_logs/2026-06-17_phaseB_rag_search_design.md) — B-4 design + local validation of `tools/rag_search.py`.
    - [`../../09_logs/2026-06-17_phaseB_audit_search_design.md`](../../09_logs/2026-06-17_phaseB_audit_search_design.md) — B-5 design + local validation of `tools/audit_search.py`.
    - [`../../09_logs/2026-06-16_phaseB_validation_applied.md`](../../09_logs/2026-06-16_phaseB_validation_applied.md) — B-6 install + B-7 `meta.toolIds` extension + B-8 browser/Tool-runtime validation evidence (with the W-4/W-5/W-6/W-7 follow-up gap explicitly documented in §7).
15. Most recent log in [`../../09_logs/`](../../09_logs/) matching `*phase*-applied*.md` (applied work) and `*phase*-design*.md` (design lock-ins).

## Safety rules (Amarolab-specific)

The homelab-wide rules in
[`../../00_overview/AMAROLAB_HANDOFF.md`](../../00_overview/AMAROLAB_HANDOFF.md)
apply. The following are **sub-project additions**:

- **Guardian Cloud is production.** RAG read-only over its docs.
  Never write to `/mnt/storage/projects/guardian-cloud`. Never call its
  backend API.
- **Home Assistant is out of scope until Phase C.** No HA token, no HA
  calls, no HA tool code, no changes to HA configuration until Phase C
  is explicitly approved.
- **The LLM is adversarial input.** Tool argument allowlists are
  file-level Python constants. No `eval`, no `subprocess`, no
  path-from-arg, no shell building from arguments.
- **No new Open WebUI Tools are created** in `webui.db` until the
  user explicitly approves each sub-phase. As of 2026-06-16 the
  Amarolab Tools installed are: `time_now` (Phase A.3, 2026-06-15),
  `rag_search` (Phase B B-6, 2026-06-16), and `audit_search`
  (Phase B B-6, 2026-06-16). Canonical sources at
  `/home/diego/homelab/ai-stack/openwebui-tools/tools/`
  (`time_now.py`, `rag_search.py` @ `a7995b3f`,
  `audit_search.py` @ `a13d5e94`). `system_status`, `ha_get_state`,
  `ha_call_service` remain designed only — not on disk as Tool
  files, not in `webui.db`. (Note: the v1 design package uses
  "Functions" loosely — Open WebUI 0.8.10's runtime term is
  **Tools**; see
  [`../../FUNCTIONS_COMPATIBILITY_REPORT.md`](../../FUNCTIONS_COMPATIBILITY_REPORT.md).)
- **Default model in Open WebUI must not be changed** without explicit
  user approval. Phase A.1 pulled `qwen2.5:7b-instruct` but did not
  set it as default.
- **Container changes are gated.** No new containers, no recreates of
  existing ones (openwebui, ollama, qdrant), no compose-file changes
  in this sub-project without explicit approval.
- **Secrets stay in `/home/diego/homelab/ai-stack/.env`** (mode 0600).
  Never paste secrets into design docs or status files; reference by
  env-var name only.
- **Audit-log path is fixed.**
  `/srv/homelab/data/openwebui/amarolab-audit.log` on host,
  `/app/backend/data/amarolab-audit.log` in container. Do not relocate
  without a security model update.

## Documentation rules

- **If it's not documented, it doesn't exist.** Inherited from the
  homelab-level rule.
- **Three files at this directory's root are live state:**
  `AMAROLAB_HANDOFF.md` (this file), `CURRENT_STATE.md`,
  `ROADMAP.md`. They are rewritten in place whenever facts change.
- **Design documents (01–05) are immutable for v1.** They describe
  what v1 *is*. Changes to that design go into a v1.1 / v2 package or
  into a new application log explaining the divergence.
- **Application logs are immutable and dated**:
  `YYYY-MM-DD_phaseX_name-applied.md` in
  [`../../09_logs/`](../../09_logs/). One per applied sub-phase.
- **Design reports (review-only, no application)** that occur between
  phases may live in the conversation only, or be committed as
  `YYYY-MM-DD_phaseX-design.md` if the user requests durability.
- **No secrets in any file in this directory.** References only
  (env-var names, paths to `.env`, never the value).
- **Sanitize before pushing to GitHub.** The homelab repo is
  synchronized; nothing under this directory should contain LLATs,
  API keys, or internal IPs that are not already in the design docs.
- **Cross-link with relative paths.** All references between docs in
  this sub-project use relative paths (e.g. `[`02-target-architecture.md`](02-target-architecture.md)`).
  Links to the rest of the homelab use `../../` prefixes.
