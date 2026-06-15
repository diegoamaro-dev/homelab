# Phase A — formal close-out — Amarolab Assistant v1

- **Date:** 2026-06-15
- **Decision:** **Phase A is formally CLOSED.**
- **Scope:** Record the closure decision for Phase A of the
  Amarolab Assistant v1 sub-project (A.1 LLM pull, A.2 tool layer
  design, A.3 `time_now` canary install, A.4 default model + system
  prompt). This log is the durable closure record that
  [`CURRENT_STATE.md`](../04_ai_system/amarolab-v1/CURRENT_STATE.md),
  [`ROADMAP.md`](../04_ai_system/amarolab-v1/ROADMAP.md), and
  [`AMAROLAB_HANDOFF.md`](../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md)
  point to.
- **What this log is NOT:** an application log. Nothing in
  `webui.db`, no Tool source, no container, no env var, no
  filesystem path outside `09_logs/` and the three live state
  files is modified by this closure. The closure is a decision +
  documentation event, not a code/state event.
- **Inputs consumed:**
  - [`2026-06-15_phaseA1-tool-calling-llm-applied.md`](2026-06-15_phaseA1-tool-calling-llm-applied.md)
  - [`2026-06-15_phaseA2-tool-layer-design.md`](2026-06-15_phaseA2-tool-layer-design.md)
  - [`2026-06-15_phaseA3-tool-canary-applied.md`](2026-06-15_phaseA3-tool-canary-applied.md)
  - [`2026-06-15_phaseA4-default-model-and-prompt-applied.md`](2026-06-15_phaseA4-default-model-and-prompt-applied.md)
  - [`2026-06-15_phaseA4-prompt-v0.1-applied.md`](2026-06-15_phaseA4-prompt-v0.1-applied.md)
  - [`2026-06-15_issueT_root_cause_analysis.md`](2026-06-15_issueT_root_cause_analysis.md)
  - [`2026-06-15_openwebui_json_parse_error_analysis.md`](2026-06-15_openwebui_json_parse_error_analysis.md)
  - Sub-project design docs (immutable for v1) under
    `../04_ai_system/amarolab-v1/01..05`.
  - Homelab-wide state: `../00_overview/{AMAROLAB_HANDOFF,CURRENT_STATE,ROADMAP}.md`.

## 0. TL;DR

Phase A's purpose was to land the **brain layer** of the assistant:
a tool-calling LLM, a canary Tool that exercises the full Open WebUI
runtime, a per-model scope so other models stay clean, an audit log
of every Tool call, the workspace default-model pointer, and a
system prompt that gives the LLM its persona, language behaviour,
tool routing, refusal grammar and citation grammar.

All of that is on disk and live:

| Piece | State |
|---|---|
| `qwen2.5:7b-instruct` in Ollama, native `tool_calls` proven | ✓ A.1 applied |
| Three-tool design locked (`time_now`, `rag_search`, `system_status`) with five binding decisions D-18..D-22 | ✓ A.2 approved |
| `time_now` Tool installed in `webui.db`, scoped to qwen2.5 only, audit log live | ✓ A.3 applied, 19/21 V-checks PASS |
| Workspace `DEFAULT_MODELS = "qwen2.5:7b-instruct"` | ✓ A.4 v0 applied |
| System prompt v0.1 (3 342 chars) on qwen2.5 Model entry | ✓ A.4 v0.1 applied |
| Decisions D-23..D-34 locked (runtime contract, persona, citation, tool invocation rule) | ✓ A.2 + A.3 + A.4 design lock-ins |

The two open items that previously held A.4 in a "PARTIALLY APPLIED"
state are now diagnosed and reclassified:

1. **Issue T (B-09)** — `time_now` not invoked from chat with the
   v0.1 system prompt. **Diagnosed as a validation-methodology
   artefact** (validator omitted `tool_ids` from the request body;
   the browser UI auto-attaches it from `meta.toolIds`). The Tool,
   the model, the prompt, and Ollama all behave correctly. Full
   evidence in
   [`2026-06-15_issueT_root_cause_analysis.md`](2026-06-15_issueT_root_cause_analysis.md).
   **Reclassified to RESOLVED.** The blocker B-09 is downgraded; it
   does not gate Phase B.
2. **JSON-parse UX trap** — when the browser's WebSocket /
   socket.io connection is not established at the moment of the
   first message, the request body omits `session_id`, Open WebUI
   falls through to a streaming SSE response, and the frontend
   helper `A()` in `C2Mvb_V1.js` calls `.json()` on it,
   producing `Unexpected token 'd', "data: {"id"... is not valid JSON`.
   **Diagnosed as an Open WebUI 0.8.10 frontend bug** unrelated to
   any Amarolab change. Workaround documented; durable fix is
   upstream. Full evidence in
   [`2026-06-15_openwebui_json_parse_error_analysis.md`](2026-06-15_openwebui_json_parse_error_analysis.md).
   **Tracked as a new known carry-over, BX,** but **does not gate
   Phase B** because Phase B implementation does not touch the
   frontend stream pipeline.

Three prompt-cosmetic V-check failures remain (Issue L — short
English greeting; Issue B — refusal doesn't name "Phase B"; a
contradictory `[1]` citation example in the no-tools fallback
path). They are **carry-overs**, not blockers. They will be
addressed by a v0.2 prompt iteration sometime during or after
Phase B at the user's discretion.

**Phase A is closed.** Phase B is the next phase.

## 1. What Phase A delivered

| Sub-phase | Deliverable | Applied date | Evidence |
|---|---|---|---|
| **A.1** | `qwen2.5:7b-instruct` (Q4_K_M, 4.7 GB) resident in Ollama; native `tool_calls` emit verified | 2026-06-15 | [`2026-06-15_phaseA1-tool-calling-llm-applied.md`](2026-06-15_phaseA1-tool-calling-llm-applied.md); reaffirmed by Probes A–D in [`2026-06-15_issueT_root_cause_analysis.md`](2026-06-15_issueT_root_cause_analysis.md) §3 |
| **A.2** | Three-tool design lock-in (`time_now`, `rag_search`, `system_status`); five locked decisions D-18..D-22 | 2026-06-15 | [`2026-06-15_phaseA2-tool-layer-design.md`](2026-06-15_phaseA2-tool-layer-design.md) |
| **A.3** | `time_now` Tool installed in `webui.db` (5 180 chars; 1 spec); per-model scoping wired (Model entry `qwen2.5:7b-instruct` with `meta.toolIds=["time_now"]`); audit log live at `/srv/homelab/data/openwebui/amarolab-audit.log`; source tree at `/home/diego/homelab/ai-stack/openwebui-tools/`; install/dump helpers at `bin/`; 19/21 V-checks PASS, 1 informational, 1 PASS | 2026-06-15 | [`2026-06-15_phaseA3-tool-canary-applied.md`](2026-06-15_phaseA3-tool-canary-applied.md) |
| **A.4 v0** | `config.DEFAULT_MODELS = "qwen2.5:7b-instruct"`; v0 persona system prompt (2 310 chars) attached to qwen2.5 Model entry; `meta.toolIds`, `meta.description`, `llama3*` rows preserved | 2026-06-15 | [`2026-06-15_phaseA4-default-model-and-prompt-applied.md`](2026-06-15_phaseA4-default-model-and-prompt-applied.md) |
| **A.4 v0.1** | v0.1 prompt (3 342 chars) replaces v0; D-32 (first-turn intro), D-33 (tool invocation rule), D-34 (citation precondition) added; 15/21 V-checks PASS | 2026-06-15 | [`2026-06-15_phaseA4-prompt-v0.1-applied.md`](2026-06-15_phaseA4-prompt-v0.1-applied.md) |

### 1.1 Phase A locked decisions

D-01 .. D-34, recorded in
[`../04_ai_system/amarolab-v1/ROADMAP.md`](../04_ai_system/amarolab-v1/ROADMAP.md).
None are reversed by this closure. D-32, D-33, D-34 are noted as
*partially aspirational* in the v0.1 applied log; the Issue T
analysis confirms they are correctly honoured by the real chat
path and only failed in the validator's no-`tool_ids` shape.

## 2. The two open items, diagnosed in this turn

### 2.1 Issue T (B-09) — RESOLVED

**Symptom (per v0.1 applied log):** `"¿qué hora es?"` returned the
text `"La hora actual en Europe/Madrid es [1].\n\n[1] time_now(\"Europe/Madrid\", \"%H:%M:%S\")"`
with `tool_calls = None` and zero audit-log delta.

**Root cause** (full evidence in
[`2026-06-15_issueT_root_cause_analysis.md`](2026-06-15_issueT_root_cause_analysis.md)):
the V-10 / V-12 validator script omits `tool_ids` from the
`POST /api/chat/completions` request body. Open WebUI 0.8.10's
chat handler at `main.py:1783` reads `tool_ids` *only* from the
request body — it does **not** auto-resolve from `meta.toolIds` on
the Model entry. With no `tool_ids`, the tool-resolution branch in
`process_chat_payload` is skipped; the chat goes to qwen2.5 with
the v0.1 prompt as the `system` message and **no tools array**.
The model — given a prompt that literally contains
`time_now(timezone?, format?)` text and an instruction "cite as
`[1]`" — produces the only thing the prompt asks for.

**Live evidence (Probes A–G):**
- A–D (direct to Ollama with the live v0.1 prompt + live tool
  spec): all four emit valid native `tool_calls`. **Model is not
  the cause.**
- G (`/api/chat/completions` without `tool_ids`): reproduces the
  V-10 / V-12 failure exactly.
- E (same request with `tool_ids:["time_now"]` added): tool fires;
  audit log gains one fresh `time_now` line; reply contains an
  actual time.
- The Open WebUI frontend bundle `GxGTGtKc.js` auto-populates
  `tool_ids` from `model.info.meta.toolIds` for browser chats, so
  **the real user-facing path was already correct**; only the
  validator was incomplete.

**Resolution path** (no implementation in this turn):
1. The Phase B validation harness will include
   `tool_ids:["time_now"]` (and equivalent for any new Tool) in its
   chat-completions request body, so V-10/V-10b/V-12 are exercised
   the same way the UI exercises them.
2. The v0.1 prompt's contradictory `[1]` citation grammar in the
   no-tools fallback path is a separate quality concern that v0.2
   will address (see §3.1).

**Status:** B-09 reclassified from "Tool-calling regression with
custom `params.system`" to **"Resolved — validator-shape issue,
not a runtime regression"**. Does not block Phase B.

### 2.2 JSON-parse UX trap (new — BX)

**Symptom:** in the browser, the chat fails before answering with
`Unexpected token 'd', "data: {"id"... is not valid JSON`.

**Root cause** (full evidence in
[`2026-06-15_openwebui_json_parse_error_analysis.md`](2026-06-15_openwebui_json_parse_error_analysis.md)):
when any of `session_id`, `chat_id`, or `id` (message_id) is
missing from the request body, Open WebUI 0.8.10's
`main.py:1939–1955` decision branch falls through to a streaming
`text/event-stream` response. The frontend helper `A()` in
`C2Mvb_V1.js` calls `response.json()` unconditionally — no
`Content-Type` check — so `JSON.parse("data: {\"id\":...")`
throws the V8 error string that the catch handler toasts verbatim
via `mt.error`.

The trigger in practice is a race between the WebSocket /
socket.io handshake and the user's first message: `session_id`
comes from `(w())?.id` where `w()` is the socket store, which is
empty until the engine.io handshake completes.

**Phase A impact:** none. The browser UI race exists in any chat
with any model on Open WebUI 0.8.10. The v0.1 prompt and the
`time_now` Tool do not contribute to the failure. Direct LAN
connection to OWUI returns `HTTP/1.1 101 Switching Protocols` for
the WebSocket upgrade — the server side is healthy.

**Workaround (documented for Phase B verification work):**
- Open the UI over LAN/Tailnet
  (e.g. `http://192.168.178.x:3000`), **not** via cloudflared or
  nginx-proxy-manager, unless WebSocket support is verified
  end-to-end on those proxies.
- Hard-refresh (Ctrl+Shift+R) and wait until the connection
  indicator is solid before the first send.

**Durable fix:** belongs in upstream Open WebUI — `A()` should
branch on `Content-Type` instead of unconditionally `.json()`-ing.
Tracked here only; no patch applied locally.

**Status:** tracked as a new known carry-over **BX**. Does not
block Phase B implementation (Phase B does not modify the frontend
stream pipeline; the workaround is sufficient for UI verification).

## 3. Carry-overs (non-blocking)

These survive Phase A's closure and will be picked up at the user's
discretion.

### 3.1 Prompt v0.2 (Issues L, B, and the `[1]` literal contradiction)

| Issue | What | Fix candidate |
|---|---|---|
| **L** | Short English greeting on turn 1 → Spanish reply (V-6a/b). Multi-turn explicit switch works (V-11). | Drop the "default to Spanish if ambiguous" escape in `# Language`; require per-language matching unconditionally. |
| **B** | `rag_search` refusal no longer names "Phase B" (V-8b regressed from v0). | Add `"Status: Phase B"` after the `rag_search` description in `# Tools`, mirroring the Phase C / Phase D status markers. |
| **`[1]` contradiction** | `# Citations` requires `[1]` inline while `# Tools` CRITICAL RULES forbid writing a literal `[1]`. In the no-tools-attached fallback, the model resolves this by hallucinating both. | Replace the contradictory pair with a single positive rule: "Only cite when a tool result is present this turn." Drop the literal `time_now(...)` signature line and the literal `[1]` example. |

None of these affect Phase B's deliverables; they affect prompt
quality. v0.2 can land before, during, or after Phase B.

### 3.2 BX — Open WebUI browser-UI WebSocket race

Avoidable via the workaround in §2.2. Durable upstream fix
recommended. Not a Phase B blocker.

### 3.3 Carry-overs from earlier phases (unchanged)

| # | Item | Status |
|---|---|---|
| C-01 | R-07.2 — Ollama bound to `0.0.0.0:11434` | Acceptable on trusted LAN; deferred |
| C-02 | R-14 — most containers still ad-hoc `docker run` | Soft blocker when Phase D adds containers |
| C-03 | R-09 / R-10 / R-11 / R-13 | System-hardening sweep; post-v1 stable |
| C-04 | Off-site backup mirror | Out of scope for v1 |
| C-05 | Containerise the ingest service | Targeted for v1.1 |
| B-07 | HA LLAT not issued | Phase C |
| B-08 | MyFreeTour source path unknown | Phase G |

## 4. Closure decision — criteria check

| Sub-phase exit criterion | Met? | Evidence |
|---|---|---|
| qwen2.5 model present + native `tool_calls` proven | ✓ | A.1 applied log; Probes A–D in Issue T analysis |
| First three-tool set designed with decisions locked | ✓ | A.2 design log; D-18..D-22 |
| Canary Tool installed in `webui.db`; scoped to qwen2.5; audit log writing | ✓ | A.3 applied log; 19/21 V-checks PASS |
| Workspace default model set to qwen2.5 | ✓ | A.4 v0 applied log (W-2 write) |
| System prompt with persona, language, tools, refusals, citations attached to qwen2.5 Model entry | ✓ | A.4 v0.1 applied log (3 342 chars in `params.system`) |
| Real UI chat invokes `time_now` end-to-end | ✓ (proven via API equivalent — Probe E) | Issue T analysis §4. Browser-step verification deferred to Phase B kick-off because of BX workaround. |
| All A-phase exit criteria met without an open functional regression | ✓ | Remaining failures are validator artefacts (Issue T) and prompt cosmetics (L, B). No functional path is broken. |

**Decision: Phase A is CLOSED.**

## 5. What Phase A leaves to Phase B

| Artefact | State at hand-off |
|---|---|
| Tool runtime contract | Pinned in `FUNCTIONS_COMPATIBILITY_REPORT.md` (D-23..D-26) |
| Tool source location | `/home/diego/homelab/ai-stack/openwebui-tools/tools/` (D-23) |
| Tool install workflow | `bin/install_tool` (mints JWT, POSTs `/api/v1/tools/create`) (D-25) |
| Tool template | `time_now.py` is the canonical example of the v1 Tool shape (D-24, D-26) |
| Audit format | 8-field JSONL: `ts`, `id`, `user`, `tool`, `args`, `allowed`, `result_code`, `duration_ms`. Path at D-21 |
| Per-model scoping | `meta.toolIds = ["time_now"]` on qwen2.5; Phase B adds `rag_search` and `audit_search` to the list (D-20) |
| Default model | `DEFAULT_MODELS = "qwen2.5:7b-instruct"` (unchanged in Phase B) |
| System prompt | v0.1 prompt live (carry-overs to address in v0.2; Phase B does not require v0.2) |
| Ingest service | Bare-metal venv at `/home/diego/homelab/ai-stack/ingest/venv`; nightly cron 02:30; Phase B adds the `infra_audits` corpus and reuses `Embedder` + `Reranker` modules |
| Qdrant | 4 active collections; Phase B adds the 5th (`infra_audits`) |
| Validation methodology | Lesson learned from B-09 / Issue T: chat-completion probes that test tool invocation **must** include `tool_ids:[…]` in the request body. To be encoded in the Phase B validation harness. |
| BX workaround | Documented; Phase B UI-step verification uses the LAN-direct + post-WebSocket-handshake sequence |

## 6. What does *not* change with this closure

- Guardian Cloud read-only RAG access (D-09): unchanged.
- D-01 .. D-34: all binding, none reversed.
- `llama3:latest` (Jarvis), `llama3.2:latest`, `phi3:latest`:
  untouched; remain unscoped pass-through models.
- HA tools: still Phase C; no HA token, no HA call.
- `system_status` Tool: still Phase D (Path C from D-18 — wait for
  containerized `homelab-tools` + docker-socket-proxy).
- No Cloudflare exposure of the assistant in v1 (D-15).
- No conversation memory across sessions (D-16); in-session via
  Open WebUI's `webui.db` only.

## 7. Forward references

- Live state post-closure:
  [`../04_ai_system/amarolab-v1/CURRENT_STATE.md`](../04_ai_system/amarolab-v1/CURRENT_STATE.md)
- Updated phase status:
  [`../04_ai_system/amarolab-v1/ROADMAP.md`](../04_ai_system/amarolab-v1/ROADMAP.md)
- Updated handoff context:
  [`../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md`](../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md)
- Phase B execution plan:
  [`../04_ai_system/amarolab-v1/PHASE_B_EXECUTION_PLAN.md`](../04_ai_system/amarolab-v1/PHASE_B_EXECUTION_PLAN.md)

## 8. Forensic state at closure

| Item | Value |
|---|---|
| `webui.db` size / mtime | unchanged from start of this turn |
| qwen2.5 `params.system` length | 3 342 chars (v0.1 prompt) |
| qwen2.5 `meta.toolIds` | `["time_now"]` |
| `config.DEFAULT_MODELS` | `"qwen2.5:7b-instruct"` |
| `time_now` Tool installed | yes, content length 5 180 chars |
| Audit log line count | 96 (carried over from the JSON-parse investigation) |
| Containers up | `openwebui`, `ollama`, `qdrant`, `cloudflared`, `nginx-proxy-manager`, `homeassistant`, `mosquitto`, `zigbee2mqtt`, `portainer`, `guardian-web` — all up; openwebui/ollama/qdrant at the same uptimes as session start |
| Pre-A.4 backup | `/tmp/amarolab-phaseA4-backup/webui.db.pre-A4` retained |
| Pre-v0.1 backup | `/tmp/amarolab-phaseA4-v0_1-backup/webui.db.pre-v0_1` retained |
