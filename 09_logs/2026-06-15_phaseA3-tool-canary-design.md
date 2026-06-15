# Phase A.3 — Open WebUI Tools scaffold + `time_now` canary (REVISED PLAN)

- **Date prepared:** 2026-06-15
- **Status:** Plan only. Awaiting implementation approval. Nothing
  has been created, installed, or modified.
- **Supersedes:** the in-conversation Phase A.3 plan delivered earlier
  on 2026-06-15 (which assumed module-level Functions and filesystem
  auto-discovery).
- **Driven by:**
  [`../FUNCTIONS_COMPATIBILITY_REPORT.md`](../FUNCTIONS_COMPATIBILITY_REPORT.md)
  (Open WebUI 0.8.10 source review).

## Why this revision exists

The previous A.3 plan inherited two assumptions from the v1 design
package
([`../04_ai_system/amarolab-v1/03-tools.md`](../04_ai_system/amarolab-v1/03-tools.md)):

1. Tools could be written as **module-level functions**.
2. Open WebUI would **auto-discover** tools from
   `/srv/homelab/data/openwebui/functions/`.

The compatibility report disproved both against the actual running
Open WebUI 0.8.10. The corrected truths drive this plan:

| # | Locked decision | Source |
|---|---|---|
| D-23 | Tool source location = `/home/diego/homelab/ai-stack/openwebui-tools/` (repo-tracked, sibling to `ai-stack/ingest/`) | Compat report §7 |
| D-24 | Tool code shape = `class Tools` with type-hinted methods | Compat report §3 |
| D-25 | Tool install workflow = `POST /api/v1/tools/create` (or admin UI); content lives in `webui.db` | Compat report §5 |
| D-26 | Audit / RateLimiter helper inlined per Tool file (no cross-Tool imports — each Tool runs in its own `tool_{id}` exec namespace) | Compat report §7 |

D-18..D-22 from Phase A.2 still apply unchanged (system_status
deferred to D; default tz Europe/Madrid; visibility = qwen2.5 only;
audit log path confirmed; myfreetour returns `empty_collection`).

## Scope of A.3 (unchanged from previous plan)

Phase A.3 ships **one** Tool — the canary — plus the source-tree
scaffold and install tooling. No `rag_search`, no `system_status`, no
HA, no Guardian Cloud, no Open WebUI default-model change (that's
A.4).

## Exact files to be created

### Directory tree (in the homelab repo)

```
/home/diego/homelab/ai-stack/openwebui-tools/
├── README.md                            ← workflow doc (this phase)
├── tools/
│   └── time_now.py                      ← canary Tool, class Tools shape
├── lib/
│   └── audit_helper.py                  ← canonical helper text, textually inlined by install_tool
└── bin/
    ├── install_tool                     ← Python helper: inline lib + POST /api/v1/tools/create or .../update
    └── dump_tools                       ← Python helper: GET /api/v1/tools/export → write back to disk for diff/backup
```

Mode 0755 for directories; 0644 for `.py` and `.md` files; 0755 for
the two `bin/` scripts.

### File-by-file content (high level — concrete code lands in the
applied log)

#### `README.md` (~40 lines)

Documents the workflow:

- One-paragraph reminder that Open WebUI 0.8.10 stores Tools in
  `webui.db`, not on disk; this directory is the canonical source.
- How to install a Tool: `bin/install_tool tools/time_now.py`.
- How to update a Tool: same command (idempotent — uses
  `POST /api/v1/tools/id/{id}/update` if `id` already exists).
- How to dump the live DB state for diff: `bin/dump_tools > /tmp/live`.
- Per-model visibility note: after install, enable the Tool against
  `qwen2.5:7b-instruct` in the admin UI (D-20).

#### `lib/audit_helper.py` (~50 lines)

Single-source canonical text of:

- `AUDIT_LOG` constant resolution (`os.environ.get("AMAROLAB_AUDIT_LOG",
  "/app/backend/data/amarolab-audit.log")`).
- `audit(tool, args, *, user="diego", allowed=True, result_code="ok",
  duration_ms=None)` function.
- `_redact(d: dict) -> dict` helper (mask keys in
  `{"password","token","secret","api_key","authorization"}`).
- `RateLimiter` class with `check(tool, max_per_minute)` classmethod.

This file is **never imported by a Tool**. It is read as text by
`bin/install_tool` and inlined into each Tool file at install time
(see D-26).

#### `tools/time_now.py` (~80 lines)

Open WebUI 0.8.10 Tool. Shape from the compatibility report §6,
parameterised for D-19 / D-20 / D-21 / D-26:

```
"""
title: Amarolab time_now (canary)
author: amarolab
description: Returns the current time in a specified timezone. Canary tool for the Amarolab Assistant.
version: 0.1.0
license: MIT
requirements:
"""

# @@AMAROLAB_INLINE:audit_helper@@   ← textual marker that install_tool replaces with lib/audit_helper.py

from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo, available_timezones
import json, time

from pydantic import BaseModel, Field


class Tools:
    class Valves(BaseModel):
        default_timezone: str = Field(
            default="Europe/Madrid",
            description="Timezone used when the caller does not supply one (D-19)."
        )
        max_per_minute: int = Field(default=60, ge=1, le=600)

    def __init__(self) -> None:
        self.valves = self.Valves()
        self.citation = False

    def time_now(
        self,
        timezone: str = "Europe/Madrid",
        format: Literal["iso", "human", "unix"] = "iso",
    ) -> str:
        """
        Get the current time. Call this whenever the user asks the
        date, day, weekday, or clock time. Do not answer from memory.

        :param timezone: IANA timezone name (e.g. "Europe/Madrid", "Asia/Tokyo", "UTC").
        :param format: Output flavour — "iso", "human", or "unix".
        :return: JSON string with now, unix, timezone, weekday, date, time, format_requested.
        """
        t0 = time.monotonic()
        tz = timezone or self.valves.default_timezone

        if tz not in available_timezones():
            _audit("time_now", {"timezone": tz, "format": format},
                   allowed=False, result_code="bad_tz")
            return json.dumps({"error": "unknown timezone",
                               "code": "bad_tz", "timezone": tz})

        if not _RateLimiter.check("time_now", self.valves.max_per_minute):
            _audit("time_now", {"timezone": tz, "format": format},
                   allowed=False, result_code="rate_limited")
            return json.dumps({"error": "rate limit exceeded",
                               "code": "rate_limited"})

        now = datetime.now(ZoneInfo(tz))
        result = {
            "now": now.isoformat(timespec="seconds"),
            "unix": int(now.timestamp()),
            "timezone": tz,
            "weekday": now.strftime("%A"),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "format_requested": format,
        }
        _audit("time_now", {"timezone": tz, "format": format},
               duration_ms=int((time.monotonic() - t0) * 1000))
        return json.dumps(result, ensure_ascii=False)
```

Note the **private** underscore prefixes on `_audit` and
`_RateLimiter`: per
`get_functions_from_tool` (compat report §3), Open WebUI ignores any
attribute starting with `_`, so the helper symbols don't accidentally
become tool methods.

#### `bin/install_tool` (~120 lines, Python)

Behaviour:

1. Read the Tool source file given as argv[1].
2. Locate the text marker `# @@AMAROLAB_INLINE:audit_helper@@` and
   replace it with the contents of `lib/audit_helper.py` (everything
   after the file's own frontmatter, if any).
3. Compute the Tool `id` from the basename (e.g. `time_now`).
4. Authenticate to Open WebUI (token from env
   `OPENWEBUI_API_TOKEN`, or a `--user` + interactive password
   prompt fallback).
5. `GET /api/v1/tools/id/{id}` → if 404, POST `/create`; else POST
   `/id/{id}/update`.
6. Print the resulting Tool id, version, and the inferred specs (so
   the diff is auditable).

Exit codes: 0 success, 1 source/network error, 2 auth error.

#### `bin/dump_tools` (~50 lines, Python)

`GET /api/v1/tools/export` (or list + per-id GET) and write each
Tool's content back to `tmp/<id>.dumped.py`. For diff against the
on-disk source.

### Files NOT created in A.3

- No `tools/rag_search.py`, no `tools/audit_search.py`,
  no `tools/system_status.py`, no HA tools.
- No new env var in `.env` other than the optional `OPENWEBUI_API_TOKEN`
  if API-key install is chosen (see "Authentication" below). The
  audit-log default works without any env edit (D-21).
- No changes to `ai-stack/ingest/`.
- No new container; no docker-socket-proxy; no compose file edits.
- No new bind mounts on the openwebui container. (Open WebUI's
  existing `/srv/homelab/data/openwebui` ↔ `/app/backend/data` bind
  mount already exposes the audit log path; no further mounts
  needed.)

### Open WebUI operational steps (UI / API, no files)

Performed once during A.3 implementation, after the source tree is
in place:

1. (If install via API key:) In Open WebUI admin → Settings →
   **Enable API Keys** → on. Create an API key for `diego`. Store the
   token (only) at `/home/diego/homelab/ai-stack/.env` as
   `OPENWEBUI_API_TOKEN=...` (mode 0600). Alternative: drive
   `bin/install_tool` with username+password instead, no `.env` edit.
2. Run `ai-stack/openwebui-tools/bin/install_tool tools/time_now.py`.
3. Open WebUI admin → Workspace → Tools → confirm `time_now` is
   active.
4. Open WebUI admin → Workspace → Models → `qwen2.5:7b-instruct` →
   Tools → enable `time_now`. Verify `time_now` is **not** enabled
   for `llama3:latest`, `llama3.2:latest`, `phi3:latest` (D-20).

No default-model change in A.3 (that's A.4).

## Architecture (revised)

```
SOURCE OF TRUTH (host repo, version controlled):
─────────────────────────────────────────────────
/home/diego/homelab/ai-stack/openwebui-tools/
├── tools/time_now.py        ← class Tools (canonical 0.8.10 shape)
├── lib/audit_helper.py      ← textually inlined at install
└── bin/install_tool         ← textual inline + REST POST


INSTALL FLOW (one-shot, on demand):
───────────────────────────────────
bin/install_tool tools/time_now.py
   ├─ read tools/time_now.py
   ├─ inline lib/audit_helper.py at @@AMAROLAB_INLINE:audit_helper@@
   ├─ resolve tool_id = "time_now"
   ├─ POST /api/v1/tools/create (or /id/time_now/update) with the inlined content
   └─ Open WebUI side:
       ├─ load_tool_module_by_id → exec(content) → Tools() instance
       ├─ get_tool_specs → JSON Schema → stored alongside content
       └─ webui.db now holds {id, name, content, specs, user_id, ...}


RUNTIME FLOW (per chat turn that invokes the canary):
────────────────────────────────────────────────────
user in Open WebUI chat (model=qwen2.5:7b-instruct)
   │
   ▼
POST /api/chat to ollama with
   tools=[{type:"function", function:{
       name:"time_now",
       description:"<docstring up to :param>",
       parameters:{<built from method type hints>}
   }}]
   │
   ▼
ollama qwen2.5:7b-instruct
   └─ returns tool_calls=[{name:"time_now", arguments:{timezone:"Asia/Tokyo"}}]
   │
   ▼
Open WebUI Tools runtime
   ├─ TOOLS cache miss? load_tool_module_by_id("time_now")
   │     └─ exec(content from webui.db) → Tools() instance cached in request.app.state.TOOLS
   ├─ getattr(tools_instance, "time_now")
   ├─ get_async_tool_function_and_apply_extra_params → call time_now(timezone="Asia/Tokyo")
   │     └─ method:
   │        ├─ validate Asia/Tokyo in zoneinfo.available_timezones()
   │        ├─ _RateLimiter.check("time_now", 60) → True
   │        ├─ now = datetime.now(ZoneInfo("Asia/Tokyo"))
   │        ├─ _audit("time_now", {"timezone":"Asia/Tokyo", "format":"iso"}, duration_ms=...)
   │        └─ return json.dumps({"now":"...", "unix":..., ...})
   │
   ▼
POST /api/chat (round 2) with the tool_result
   │
   ▼
ollama composes the final natural-language answer
   │
   ▼
streamed to the user
amarolab-audit.log gets one new JSONL record
```

## Validation plan

Re-issue of the previous V-1..V-20, retargeted to the revised paths.

### Static checks (no chat invocation)

| # | Check | Pass criterion |
|---|---|---|
| V-1 | Directory tree created | `ls /home/diego/homelab/ai-stack/openwebui-tools/{tools,lib,bin}/` returns three populated dirs |
| V-2 | Files present | `tools/time_now.py`, `lib/audit_helper.py`, `bin/install_tool`, `bin/dump_tools`, `README.md` all exist with correct modes |
| V-3 | Tool source python-parseable | `python3 -m py_compile tools/time_now.py lib/audit_helper.py` exits 0 |
| V-4 | Install helper python-parseable | same for `bin/install_tool`, `bin/dump_tools` |

### Install / Open WebUI

| # | Check | Pass criterion |
|---|---|---|
| V-5 | Install round-trip | `bin/install_tool tools/time_now.py` exits 0; output prints `id=time_now`, returned spec includes one function `time_now` with two params |
| V-6 | Open WebUI sees it | `curl -H "Authorization: Bearer $OPENWEBUI_API_TOKEN" http://127.0.0.1:3000/api/v1/tools/` includes `id: "time_now"` |
| V-7 | Spec is sound | `GET /api/v1/tools/id/time_now/` returns content + specs; the spec's `parameters.properties` contains `timezone` (string) and `format` (string with enum) |
| V-8 | Dump round-trip | `bin/dump_tools > /tmp/live.py`; `diff -u <(grep -v '^# @@' tools/time_now.py | <inline lib>) /tmp/live.py` is empty (modulo trailing whitespace) |
| V-9 | Per-model scoping (D-20) | Admin UI: `time_now` enabled only for `qwen2.5:7b-instruct`; not for `llama3:latest`, `llama3.2:latest`, `phi3:latest` |

### End-to-end smoke test

| # | Check | Pass criterion |
|---|---|---|
| V-10 | Happy path | Open WebUI chat (qwen2.5), prompt: *"What time is it?"* → assistant cites the time; network trace shows a `tool_call` to `time_now` |
| V-11 | Non-default timezone | *"What time is it in Tokyo?"* → tool_call with `timezone="Asia/Tokyo"`; response uses that |
| V-12 | Format variations | *"What's the Unix timestamp right now?"* → tool_call with `format="unix"`; response surfaces the integer |
| V-13 | Other models do not see the Tool (D-20) | Switch chat to `llama3:latest` and ask the same — no `tool_calls` in the API response |

### Error paths

| # | Check | Pass criterion |
|---|---|---|
| V-14 | Bad timezone | Force-call (curl with explicit tool payload, or prompt the LLM to use `timezone="Atlantis/Lost"`) → response `{"error":"unknown timezone","code":"bad_tz","timezone":"Atlantis/Lost"}` |
| V-15 | Rate limit | Curl loop firing the tool 70 times in 30 s → at least one response has `"code":"rate_limited"` |

### Audit log

| # | Check | Pass criterion |
|---|---|---|
| V-16 | Audit file created on first call | After V-10, `ls -la /srv/homelab/data/openwebui/amarolab-audit.log` shows the file with ≥ 1 line |
| V-17 | Record structure | `tail -1 \| jq` shows `ts`, `id`, `user="diego"`, `tool="time_now"`, `args`, `allowed`, `result_code`, `duration_ms` |
| V-18 | Redaction sanity | Force-call with synthetic arg `password="hunter2"` → audit line shows `"password":"<redacted>"` |
| V-19 | Concurrent writes safe | Two parallel curl calls → both lines appear; no truncation |

### Memory / network sanity

| # | Check | Pass criterion |
|---|---|---|
| V-20 | RAM impact | `openwebui` container RSS rises by < 50 MiB after the Tool is loaded |
| V-21 | No outbound network from the Tool | `time_now` uses only stdlib; `strace` / container `tcpdump` shows no outbound socket from `_tool_time_now` execution |

### A.3 exit (sub-phase done when all of these are true)

- V-1..V-19 pass. V-20, V-21 recorded (informational).
- One applied log written:
  `09_logs/YYYY-MM-DD_phaseA3-tool-canary-applied.md`.
- The three live-state docs touched to mark Phase A.3 applied and
  Phase A.4 as current.

## Rollback plan

Source side (revert disk state):

```bash
# Remove tool source from the homelab repo
rm -rf /home/diego/homelab/ai-stack/openwebui-tools/

# (And revert any git commit that added it, if already committed.)
```

Open WebUI side (revert DB state — this is the new step vs the
previous plan):

```bash
# Delete the Tool from Open WebUI's DB
curl -X DELETE \
  -H "Authorization: Bearer $OPENWEBUI_API_TOKEN" \
  http://127.0.0.1:3000/api/v1/tools/id/time_now/delete
```

Or equivalently in the admin UI: Workspace → Tools → time_now → trash icon.

Per-model scoping (revert UI changes):

- Workspace → Models → `qwen2.5:7b-instruct` → Tools → uncheck `time_now`.

Audit log:

- Keep `/srv/homelab/data/openwebui/amarolab-audit.log` for forensics
  by default. Delete only if rolling back due to a corruption issue.

Risks unchanged from previous A.3 plan; one new entry:

| Risk | Probability | Impact | Mitigation |
|---|:-:|:-:|---|
| `install_tool` POSTs to a wrong endpoint or with wrong auth | L | L | V-5 / V-6 fail-fast; helper exits non-zero; nothing in `webui.db` if create fails |
| API-key feature flag stays off | L | L | Fallback to username+password login flow in `install_tool`; or do the install through the admin UI by pasting the file content |
| Tool installed but stale source on disk | L | M | `bin/dump_tools` + diff verifies; PR review at commit time |

## Pre-flight checklist (must be true before starting A.3 implementation)

- [ ] Phase A.2 approval recorded — **done** (2026-06-15).
- [ ] FUNCTIONS_COMPATIBILITY_REPORT delivered — **done**.
- [ ] Decisions D-23..D-26 locked — **done** in
      [`../04_ai_system/amarolab-v1/ROADMAP.md`](../04_ai_system/amarolab-v1/ROADMAP.md).
- [ ] Live-state docs reflect the revision — **done**.
- [ ] 03-tools.md carries an Amendments banner — **done**.
- [ ] This design log committed — **done** (this file).
- [ ] User explicit approval to start A.3 implementation — **pending**.

## What is NOT in this plan

- No tool implementation (no `time_now.py` body executed on disk).
- No DB write to `webui.db` (no Tool installed).
- No Open WebUI admin-UI changes.
- No Home Assistant work.
- No Guardian Cloud work.
- No container changes (no recreate of openwebui or ollama).
- No Ollama default-model change (Phase A.4).
- No `rag_search` or `system_status` source (Phase B / Phase D).
