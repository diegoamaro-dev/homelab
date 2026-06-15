# Phase A.2 — Tool layer design — APPROVED

- **Date approved:** 2026-06-15
- **Scope:** Lock the **first three tools** the Amarolab Assistant will
  ship with — `time_now`, `rag_search`, `system_status` — and record
  the five sub-decisions that resolve the open questions of the
  design review. **Design only.** No Python files were created, no
  Open WebUI Functions directory, no containers, no env vars, no
  Qdrant collections touched.
- **Supersedes:** none.
- **Superseded by:** none.

## What this log captures (and why it exists)

Phases A.0 / 0 / 1 / 1.5 / A.1 all left an immutable artefact in this
directory or in the design package. Phase A.2 is a **design** phase —
nothing on disk changes — so without this log the locked decisions
would live only in the conversation transcript. This file makes them
durable, citable, and survivable across future AI sessions.

The full design rationale (purpose, inputs, outputs, security
considerations, Open WebUI / qwen2.5 integration, per-tool acceptance
criteria) was delivered as the **Phase A.2 design report** in the
2026-06-15 working session. The decisions below summarise what came
out of that report; the report itself is the explanatory companion.

## Scope of the three-tool first set

| Tool | Role | Implements in |
|---|---|---|
| `time_now` | Canary for the entire Open WebUI Functions pipeline; also a real utility tool that removes a class of LLM clock/calendar hallucinations | Phase A.3 |
| `rag_search` | Dense retrieval (`multilingual-e5-small`) + cross-encoder rerank (`bge-reranker-v2-m3`) over indexed corpora | Phase B |
| `system_status` | Live containers / ports / volumes / disk introspection, fronted by a containerized backing service | Phase D |

Out of scope for A.2 (deferred):

| Tool | Reason | Earliest phase |
|---|---|---|
| `audit_search` | Requires `infra_audits` corpus | Phase B |
| `ha_get_state` | Home Assistant integration | Phase C |
| `ha_call_service` | Same | Phase C |

## Decisions locked in A.2 (D-18 … D-22 in [`../04_ai_system/amarolab-v1/ROADMAP.md`](../04_ai_system/amarolab-v1/ROADMAP.md))

### D-18 — `system_status` backing path: **C (defer to Phase D)**

Three paths were on the table:

- **A** — Build the containerized `homelab-tools` + `docker-socket-proxy`
  as part of A.2/A.3.
- **B** — Point the Function at the existing bare-metal Flask
  `homelab-tools.service` on `:5050`.
- **C** — Defer `system_status` implementation entirely to Phase D;
  ship the next phase (A.3) with only the canary, and Phase B with
  `rag_search` + `audit_search`.

**Path C is chosen.** Rationale:

- Path B reintroduces audit finding **R-02** (unauthenticated 0.0.0.0
  Flask) as an architectural dependency. Phase 0 explicitly retired
  that posture; walking back is not acceptable.
- Path A is the v1 design's target shape, but builds a container in
  the same window as bringing up the Functions runtime — too many
  moving parts at once.
- Path C preserves the option to land Path A cleanly when Phase D is
  reached, without committing during A.2/A.3.

**Consequence:** the `system_status` *signature* is locked in A.2;
the *implementation* does not exist until Phase D. No Function file
called `system_status.py` is created in A.3 or B.

### D-19 — `time_now` default timezone: `Europe/Madrid`

Default timezone passed to `zoneinfo.ZoneInfo(...)` when the caller
omits the `timezone` argument is `Europe/Madrid` (host locale).

Output shape (always returned, regardless of the `format` request):

```json
{
  "now":              "2026-06-15T16:47:12+02:00",
  "unix":             1781629632,
  "timezone":         "Europe/Madrid",
  "weekday":          "Monday",
  "date":             "2026-06-15",
  "time":             "16:47:12",
  "format_requested": "iso"
}
```

`format` is an enum: `iso` (default; RFC 3339), `human` (e.g.
`"Monday 15 June 2026, 16:47 CEST"`), `unix` (epoch seconds in a
string). The four representations (`now`, `unix`, `weekday`,
`date`+`time`) are always present so the LLM can pick whichever fits
the user's question without re-calling.

Invalid `timezone` (not in `zoneinfo.available_timezones()`) returns
`{"error": "unknown timezone", "code": "bad_tz"}`. Path-traversal-style
strings cannot escape the validation.

### D-20 — Open WebUI per-Function visibility: `qwen2.5:7b-instruct` only

In Open WebUI, each Function (`time_now`, future `rag_search`,
`audit_search`, `system_status`) is scoped to the model
`qwen2.5:7b-instruct`. `llama3:latest`, `llama3.2:latest`, and
`phi3:latest` do not see the tools.

Effect:

- Switching to a fallback model in the Open WebUI UI gives the user
  plain chat without tool-calling — useful for sanity checks and as a
  fallback if qwen2.5 misbehaves.
- New tools added in the future inherit this scoping by default. A
  future v2 / multi-model agent design can revisit (D-20 supersedes
  the A.2-report-recommendation of "expose to all models").

### D-21 — Audit-log host path: confirmed (no deviation from D-07)

- Host: `/srv/homelab/data/openwebui/amarolab-audit.log`
- Inside the openwebui container: `/app/backend/data/amarolab-audit.log`
  (via the existing bind mount of `/srv/homelab/data/openwebui →
  /app/backend/data`).

Log format and rotation policy are unchanged from
[`../04_ai_system/amarolab-v1/04-security-and-permissions.md`](../04_ai_system/amarolab-v1/04-security-and-permissions.md).

### D-22 — `myfreetour` collection: keep in enum, return `empty_collection`

The `rag_search` collection enum keeps all four currently-defined
corpora **plus** `myfreetour`, even though the latter is empty:

```json
"enum": ["homelab_docs", "guardian_cloud", "ensambla2", "myfreetour"]
```

Calls to `rag_search(collection="myfreetour", …)` return:

```json
{
  "error": "empty_collection",
  "code": "empty_collection",
  "message": "The MyFreeTour corpus is not yet indexed. Ask the user for the source path."
}
```

Rationale: it forces the LLM to apologise cleanly rather than silently
picking a different corpus. When the corpus is indexed (Phase G), the
condition disappears with no schema change.

`infra_audits` is **not** in the A.2-locked enum; it is added at the
start of Phase B alongside its corpus.

## What's **locked** vs **still open**

| Locked in A.2 | Deferred |
|---|---|
| The three-tool first set | `audit_search` (Phase B), `ha_*` (Phase C) |
| Tool signatures, JSON schemas, output shapes | Final Python implementation patterns (class-based `Tools` vs module-level — picked in A.3) |
| Error code vocabulary (`bad_tz`, `rate_limited`, `empty_collection`, `bad_collection`, `bad_scope`, `homelab_tools_unreachable`, …) | Per-tool rate-limit thresholds beyond the design defaults |
| Audit log path, format, redaction list | Logrotate config (Phase E) |
| Visibility scope (`qwen2.5:7b-instruct` only) | When to broaden to other models (no v1 plan) |
| `myfreetour` placeholder treatment | MyFreeTour source path (B-08, Phase G) |
| `system_status` backing path (C: defer to Phase D) | Whether Phase D uses FastAPI vs Flask for `homelab-tools` (implementation detail) |

## What was NOT done in A.2

- No file in `/srv/homelab/data/openwebui/functions/` (the directory
  itself does not exist on host).
- No `amarolab_common.py` written.
- No env var added to the openwebui container.
- No change to Open WebUI per-model Function visibility settings.
- No change to default model in the Open WebUI workspace.
- No new Qdrant collection.
- No change to the ingest service or its corpora config.
- No HA token, no HA URL, no HA references in `.env`.
- No `homelab-tools` container, no `docker-socket-proxy`.

## Next phase

**Phase A.3 — Functions scaffold + `time_now` canary.** Plan prepared
2026-06-15 in the same working session; awaiting implementation
approval. Phase A.3 will create exactly:

- the Functions directory on host (one `mkdir`),
- `amarolab_common.py` (helper module),
- `time_now.py` (the canary tool, signatures per D-19).

Validation, rollback, and exact file content are described in the
Phase A.3 preparation document attached to the same conversation.

## Rollback

Phase A.2 changed nothing on disk except the three live-state docs in
[`../04_ai_system/amarolab-v1/`](../04_ai_system/amarolab-v1/) and
this log. Rollback is documentation-only:

1. Revert `AMAROLAB_HANDOFF.md`, `CURRENT_STATE.md`, `ROADMAP.md` to
   their pre-A.2-approval state (git history holds the previous
   revisions).
2. Delete this log file.

No services, containers, or runtime state would be affected.
