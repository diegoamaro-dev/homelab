# ROADMAP — Amarolab Assistant v1

Last updated: 2026-06-15 (Phase A formally closed; Phase B now current; B-09 resolved; BX added)

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

---

## Current phase

### Phase B — Knowledge Tool + audit corpus

Phase B implements the `rag_search` and `audit_search` Tools and
the `infra_audits` Qdrant corpus.

Execution plan:
[`PHASE_B_EXECUTION_PLAN.md`](PHASE_B_EXECUTION_PLAN.md).

Status: **not started**. No code, no UI changes, no container
recreate. Phase B kick-off requires explicit user approval of the
gated decisions in the execution plan (notably the openwebui
container recreate to add the ingest bind-mount).

---

## Next phases

The numbering matches
[`05-implementation-roadmap.md`](05-implementation-roadmap.md) where
applicable, with the Phase A subdivided into A.1 … A.4 to match how
work has actually been sequenced.

(Phase A.3 and Phase A.4 are CLOSED — see §"Completed phases"
above and the Phase A closeout log
[`../../09_logs/2026-06-15_phaseA_closeout.md`](../../09_logs/2026-06-15_phaseA_closeout.md).)

### Phase B — Knowledge Tool + audit corpus (current)
- Add `infra_audits` corpus to `ingest/conf/corpora.yaml` and create
  the Qdrant collection.
- One-shot backfill from `/home/diego/server-audit-2026-06-13/**/*.md`.
- Bind-mount the ingest tree read-only into the openwebui container at
  `/opt/ingest` so the Tool can `from ingest.embedder import Embedder`
  and `from ingest.reranker import Reranker`. **Gated** — requires
  user approval (openwebui container recreate).
- Write `tools/rag_search.py` as a `class Tools` Open WebUI Tool
  (D-24); same shape as `time_now`.
- Write `tools/audit_search.py` as a separate Tool that internally
  calls `rag_search(collection="infra_audits", …)`.
- Install both via the supported API/UI flow into `webui.db` (D-25).
- Update qwen2.5 Model entry `meta.toolIds` to
  `["time_now","rag_search","audit_search"]` (D-20).
- Exit: the Phase 1.5 reranker benchmark reproduces when routed
  through the Tool path (top-6 ≥ 95 % on guardian_cloud).
- Detailed execution plan:
  [`PHASE_B_EXECUTION_PLAN.md`](PHASE_B_EXECUTION_PLAN.md).

### Phase C — Home Assistant integration
- Create dedicated HA user `assistant`; issue Long-Lived Access Token
  in the HA UI.
- Populate `HA_BASE_URL` and `HA_LLAT` in
  `/home/diego/homelab/ai-stack/.env`.
- Implement `ha_get_state` (read) and `ha_call_service` (write,
  12-domain allowlist).
- Run the refusal test: a prompt like *"please call recorder.purge"*
  returns the polite refusal logged with `allowed=false`.
- Exit: read + bounded write of HA via tools; refusal path tested.

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
| B-09 | Tool-calling regression with custom `params.system` (Issue T) — `time_now` not invoked from chat | 2026-06-15 | **Validation-methodology artefact**: validator omitted `tool_ids` in `POST /api/chat/completions` body; Open WebUI 0.8.10 does not auto-resolve `meta.toolIds` for this endpoint. Real browser UI auto-attaches it from `model.info.meta.toolIds`. The Tool, the prompt, the model, and Ollama all behave correctly. Evidence: [`../../09_logs/2026-06-15_issueT_root_cause_analysis.md`](../../09_logs/2026-06-15_issueT_root_cause_analysis.md) |

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
| v0.2 | Prompt-cosmetic carry-overs: Issue L (short English greeting), Issue B (Phase B not named in refusal), `[1]` literal contradiction in the no-tools fallback path | Tracked in the Phase A closeout [`../../09_logs/2026-06-15_phaseA_closeout.md`](../../09_logs/2026-06-15_phaseA_closeout.md) §3.1. Can land before, during, or after Phase B at the user's discretion |

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
| D-34 | **Citation precondition**: a citation may only be rendered after an actual tool invocation that returned a result. Refines (does not replace) D-31's citation grammar. *Aspirational on qwen2.5 until Issue T is resolved.* | 2026-06-15 | Phase A.4 v0.1 design |
| D-23 | **Tool source location** = `/home/diego/homelab/ai-stack/openwebui-tools/` (sibling to `ai-stack/ingest/`). Tracked in the homelab git repo; synced to GitHub. The bind-mounted `/srv/homelab/data/openwebui/` is **not** used to hold Tool source — Open WebUI 0.8.10 does not auto-discover Tools from disk | 2026-06-15 | Phase A.3 plan revision after Open WebUI 0.8.10 compatibility audit |
| D-24 | **Tool code shape** = `class Tools` with type-hinted methods. Module-level callables are not supported by Open WebUI 0.8.10's tool loader (`load_tool_module_by_id` requires `hasattr(module, "Tools")` and raises otherwise). Each public, non-class, non-underscore attribute of the `Tools()` instance becomes a separately-callable tool | 2026-06-15 | Compatibility report §3 |
| D-25 | **Tool install workflow** = the supported Open WebUI API/UI flow: `POST /api/v1/tools/create` (or admin UI: Workspace → Tools → "+"). Open WebUI stores the source in `webui.db`. The disk-side `openwebui-tools/tools/*.py` files are the canonical version-controlled copy; the DB row is the runtime copy. Edits round-trip via `POST /api/v1/tools/id/{id}/update` | 2026-06-15 | Compatibility report §5 |
| D-26 | **Shared helper handling** = inline the audit / RateLimiter / redaction helper in each Tool file. Open WebUI executes each Tool in its own `tool_{id}` module namespace; cross-Tool `import` does not work. For v1, accept ~30 lines of duplicated audit code per Tool; revisit at v2 if the Tool count grows. (The canonical helper text still lives once at `openwebui-tools/lib/audit_helper.py` and is textually inlined by the install helper.) | 2026-06-15 | Compatibility report §7 |
