# Phase E — E5-c Audit Log Check — Apply Log

- **Date:** 2026-06-27
- **Phase:** E — Knowledge Platform Foundation
- **Step:** E5-c — Controlled audit-log check
- **Finding addressed:** F-10 (audit log stale since 2026-06-18)
- **Outcome:** Resolved — no defect. Root cause: absence of Open WebUI web UI tool executions during the observation period.
- **Operator:** Diego Vázquez Amaro

---

## Objective

Identify the root cause of `amarolab-audit.log` being stale since 2026-06-18.
E-3 (E3-c) had already made the staleness continuously visible via `health.json`
(`audit.status: "stale"`, `age_days: 9`). E5-c is the root cause investigation.

---

## Pre-investigation state

| Fact | Value |
|---|---|
| Last audit entry | `2026-06-17T23:21:08 UTC` — `rag_search` on `homelab_docs` |
| Audit log size | 143 lines, 40 KB |
| `health.json` `audit.status` | `stale` |
| `health.json` `audit.age_days` | 9 |
| `health.json` `overall_status` | `degraded` |

---

## Investigation

### I-1 — Tool registration

All 5 Amarolab tools confirmed registered in Open WebUI:

```
time_now        updated=2026-06-17T23:13:28Z
rag_search      updated=2026-06-17T23:13:28Z
audit_search    updated=2026-06-17T23:13:28Z
ha_get_state    updated=2026-06-17T23:13:28Z
ha_call_service updated=2026-06-17T23:13:28Z
```

Last install timestamp (23:13:28 UTC) is 8 minutes before the last audit entry
(23:21:08 UTC). Tools were present throughout the observation period.

**H-1 (tool registrations lost) — ELIMINATED.**

### I-2 — Live tool code audit

Running tool code dumped from Open WebUI database via `bin/dump_tools`.

- `_audit()` function fully present in all 5 live tools.
- Call sites: `rag_search` (9), `ha_get_state` (11), `ha_call_service` (18),
  `audit_search` (9), `time_now` (4).
- `_AMAROLAB_AUDIT_LOG` resolves via `AMAROLAB_AUDIT_LOG` env var, which is
  explicitly set in the container to `/app/backend/data/amarolab-audit.log`.

**H-2 (missing `_audit()` code in running tools) — ELIMINATED.**

### I-3 — Write path and full pipeline test

**I-3a — Model tool selection (chat completions API):**

```
POST /api/chat/completions
  model: qwen2.5:7b-instruct
  tool_choice: {"type":"function","function":{"name":"rag_search"}}

Response:
  finish_reason: tool_calls
  tool called: rag_search
  arguments: {"collection":"homelab_docs","query":"fase E del homelab"}
```

The model correctly selects `rag_search`. Note: `/api/chat/completions` is a model
proxy and does NOT dispatch the tool Python code. Tool execution only happens in
Open WebUI's full WebSocket/SSE pipeline (the web UI).

**I-3b — Direct write path test (container exec):**

```bash
docker cp e5c_write_test.py openwebui:/tmp/e5c_write_test.py
docker exec openwebui python3 /tmp/e5c_write_test.py

Target path: /app/backend/data/amarolab-audit.log
Path exists: True
Parent writable: True
File stat: 0o100644
WRITE: OK
```

Host-side verification: 143 → 144 lines; test entry appeared at `2026-06-27T19:10:47Z`.

The `_audit()` write path works from inside the container's Python environment.
No exception, no silent failure. Test entry removed after verification.

**H-4 (silent write failure) — ELIMINATED.**

**I-3c — Full pipeline test (web UI, operator-executed):**

Operator opened `https://ai.amarolab.es`, sent a prompt that forced `rag_search`
invocation. Tool returned retrieved documents (`result_code: "ok"`, duration: 11959 ms).

Audit log immediately updated:

```json
{
  "ts": "2026-06-27T21:13:26.539869+00:00",
  "user": "diego",
  "tool": "rag_search",
  "args": {"collection": "homelab_docs", "query": "¿qué es la fase E?", "k": 6},
  "allowed": true,
  "result_code": "ok",
  "duration_ms": 11959
}
```

The complete execution path is functional:
**Web UI → Open WebUI tool dispatch → `Tools.rag_search()` → `_audit()` → file write → bind-mount → host filesystem.**

**H-3 (no tool calls through the web UI during the observation period) — CONFIRMED.**

---

## Root cause

The audit log gap (2026-06-17 to 2026-06-27) was caused by the absence of
Open WebUI web UI tool executions during that period, not by any failure in
the audit subsystem.

During that window, operator activity involved:
- E5-a drift measurement: direct Qdrant API queries (not Open WebUI tools)
- E5-b restore drill: direct Qdrant/restic operations (not Open WebUI tools)
- E-3 implementation and validation: CLI + cron scripts (not Open WebUI tools)
- Voice pipeline activity: HA Assist → Ollama integration (bypasses Open WebUI entirely)

None of these paths invoke Open WebUI Python tool code, and therefore none
generate audit entries.

---

## Scope clarification (architectural boundary)

The Amarolab audit log records **Open WebUI web UI tool executions only**.

| Execution path | Audit entry generated |
|---|---|
| Open WebUI web UI chat → tool call | **Yes** — `_audit()` writes to log |
| HA Assist voice pipeline → Ollama → HA integration | **No** — bypasses Open WebUI tools entirely |
| Direct Qdrant/API queries (CLI, scripts) | **No** — no Open WebUI involvement |
| Home Assistant automations | **No** — separate system |

This is an architectural boundary, not a defect. Documented in
`knowledge_platform_contract.md` §5.

---

## Post-resolution state

After the I-3c confirmation, `check-audit-liveness` was run to refresh `health.json`:

```json
{
  "schema_version": 1,
  "updated_at": "2026-06-27T21:15:38Z",
  "overall_status": "ok",
  "ingest": {
    "last_run_status": "ok",
    "last_successful_run_end": "2026-06-27T18:42:33Z"
  },
  "audit": {
    "last_entry_ts": "2026-06-27T21:13:26.539869+00:00",
    "age_days": 0,
    "status": "ok"
  }
}
```

`overall_status: "ok"` — first time the platform has reported fully healthy status.

---

## Hypotheses summary

| Hypothesis | Verdict | Evidence |
|---|---|---|
| H-1: Tool registrations lost | Eliminated | All 5 tools registered (I-1) |
| H-2: `_audit()` missing from live code | Eliminated | Code present in all 5 tools (I-2) |
| H-3: No web UI tool calls during period | **Confirmed** | Full pipeline test succeeded immediately (I-3c) |
| H-4: Silent write failure | Eliminated | Direct container write: OK (I-3b) |

---

## Links

- E-3 apply log: `09_logs/2026-06-27_phaseE_E3_observability_applied.md`
- E-0 audit report: `09_logs/2026-06-27_phaseE_E0_operational_audit_report.md`
- Knowledge platform contract: `04_ai_system/knowledge_platform_contract.md`
- Audit helper: `ai-stack/openwebui-tools/lib/audit_helper.py`
