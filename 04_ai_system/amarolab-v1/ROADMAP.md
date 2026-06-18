# ROADMAP — Amarolab Assistant v1 · decisions overlay

Last updated: 2026-06-19 — reconciled. Phase-status narrative moved to the
overview triad; this file now retains only the durable, sub-project-specific
**locked-decisions ledger (D-01…D-35)** and blockers.

> ⚠️ **Phase status is NOT tracked in this file anymore.**
> Authoritative phase plan + status:
> [`../../00_overview/ROADMAP.md`](../../00_overview/ROADMAP.md).
>
> Obsolete statements removed in the 2026-06-19 reconciliation (each
> contradicted reality as of 2026-06-18):
> - ~~"Phase C — Home Assistant integration (NEXT PHASE / NOT STARTED)"~~ →
>   **Phase C CLOSED 2026-06-17 (Gate G-5).**
> - ~~"Phase D — `system_status` backing service"~~ / ~~"Phase F — Voice
>   (deferred)"~~ → the executed roadmap re-sequenced: **Phase D = Voice;
>   Phase D-1 CLOSED 2026-06-18.** `system_status` was never rebuilt as the
>   containerized service and survives only as a legacy Jarvis tool scoped to
>   `llama3*` (see overview `CURRENT_STATE.md`).

## Phase status — tracked in the overview

This file does not track current phase. Live phase plan and status:
[`../../00_overview/ROADMAP.md`](../../00_overview/ROADMAP.md). The immutable
v1 design-intent plan is
[`05-implementation-roadmap.md`](05-implementation-roadmap.md) (design intent,
not executed status).

---

## Blockers

| # | Blocker | Phase | Owner | Status |
|---|---|---|---|---|
| B-07 | HA Long-Lived Access Token | C | user | **RESOLVED** — token issued; Phase C closed 2026-06-17; `ha_get_state` / `ha_call_service` live |
| B-08 | MyFreeTour source path unknown | E | user | **OPEN** — `myfreetour` corpus stays empty until decided |

Phase-B-era non-blocking carry-overs (BX WebSocket race, v0.2 prompt polish,
R-new1 rerank latency, W-4…W-7 evidence items) are historical. Current
carry-overs are tracked in
[`../../00_overview/CURRENT_STATE.md`](../../00_overview/CURRENT_STATE.md) and
the Phase D-1 closeout
([`../../09_logs/2026-06-18_phaseD1_closeout.md`](../../09_logs/2026-06-18_phaseD1_closeout.md) §7).

---

## Decisions taken (locked)

> **Phase-number caveat:** rows below use the **v1 design-package** numbering
> (where "Phase D" = the `system_status` service and "Phase F" = voice). The
> **executed** roadmap differs — Voice shipped as Phase D-1. Read phase names
> here as historical design intent; the
> [overview ROADMAP](../../00_overview/ROADMAP.md) is authoritative for what
> actually happened.
>
> **Spent forward-clauses:** D-10/D-11/D-18 reference tooling that has since
> moved on — `system_status` (D-10) was deferred (D-18) and never rebuilt as a
> service; HA tools (D-11, "deferred to Phase C") shipped and Phase C is
> closed. The decisions are kept verbatim for traceability; their
> forward-looking clauses are satisfied or superseded.

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

*(De-duplicated 2026-06-19: an accidental second copy of D-23…D-26 that
previously trailed this table was removed. The single canonical rows above are
authoritative.)*
