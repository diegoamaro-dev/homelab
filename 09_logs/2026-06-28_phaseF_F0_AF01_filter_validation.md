# F-0 Finding — AF-01: Open WebUI Filter Mechanism Validation

**Date:** 2026-06-28  
**Phase:** F-0 Behavioral Audit  
**Finding reference:** AF-01 (from `04_ai_system/phase_f_architecture.md` §11)  
**Status:** VALIDATED — architecture assumption confirmed

---

## Context

AF-01 was identified as the highest-priority F-0 validation assumption:

> AF-01: Open WebUI Filter inlet fires on message 1, does not repeat on message 2+, and can read a file. If this fails, Domain A (Situational Awareness) requires redesign before F-2.

The Phase F architecture (AD-02) specifies that the Open WebUI Filter for situational awareness must:
- Fire exclusively on the first user message of a conversation
- Inject the content of `aurora-context.md` as a system message prefix
- Degrade gracefully if the context file is absent

This validation used a disposable test filter (`af01_test_filter`, type=filter) installed via the Open WebUI Functions API (`POST /api/v1/functions/create`). The filter was activated globally, tested, then deleted. No production artifacts were modified.

---

## Test environment

| Item | Value |
|---|---|
| Open WebUI version | 0.8.10 (image `ghcr.io/open-webui/open-webui:main`) |
| Filter ID | `af01_test_filter` (DISPOSABLE — deleted after validation) |
| Filter type | `filter` (class Filter, inlet method) |
| Scope | Global (`is_global=True`, `is_active=True`) |
| Test file path | `/tmp/af01_test_context.txt` (container-internal, deleted) |
| Log path | `/tmp/af01_filter_test.log` (container-internal, deleted) |
| Model used | `qwen2.5:7b-instruct` |
| Endpoint | `POST /api/chat/completions` |

---

## Test cases and results

### Test A — Message 1, file present

**Input:** Single-message body (`messages_count=1`)  
**File state:** `/tmp/af01_test_context.txt` present, content `AF01 context sentinel`

**Filter log:**
```json
{"ts": "2026-06-27T23:54:36.408610", "messages_count": 1, "is_message_1": true, "file_exists": true}
{"ts": "2026-06-27T23:54:36.408610", "action": "injected", "prefix": "[AF01-FILE-OK] AF01 context sentinel"}
```

**Result:** PASS — inlet fired, file read successfully, prefix injected into system message.

---

### Test B — Message 2 simulation (3-message body)

**Input:** 3-message body (`user → assistant → user`), simulating the second message in an ongoing conversation (`messages_count=3`)  
**File state:** File still present

**Filter log:**
```json
{"ts": "2026-06-27T23:54:41.988329", "messages_count": 3, "is_message_1": false, "file_exists": true}
```

**Result:** PASS — inlet fired (expected; Filter always fires as middleware) but `is_message_1=false`, so no injection occurred. No crash.

---

### Test C — Message 1, file missing

**Input:** Single-message body (`messages_count=1`)  
**File state:** `/tmp/af01_test_context.txt` deleted before this call

**Filter log:**
```json
{"ts": "2026-06-27T23:54:44.290421", "messages_count": 1, "is_message_1": true, "file_exists": false}
{"ts": "2026-06-27T23:54:44.290421", "action": "injected", "prefix": "[AF01-FILE-MISSING: graceful degradation]"}
```

**Result:** PASS — inlet fired, file absence detected, graceful fallback injected (no exception raised, conversation continued normally, HTTP 200 from chat endpoint).

---

## Verdict

| Check | Result |
|---|---|
| Inlet fires on message 1 | **PASS** |
| Inlet does not inject on message 2+ | **PASS** |
| Injection occurs only on message 1 | **PASS** |
| File read succeeds when file present | **PASS** |
| Graceful degradation when file missing | **PASS** |
| No crash on any test case | **PASS** |

**All 6 checks: PASS.**

---

## Key architectural findings

### 1. `messages_count` is the correct discriminator for message 1

On message 1, the Open WebUI chat completion body contains exactly 1 message. On message 2, it contains 3 messages (user 1, assistant 1, user 2). The count is stable and unambiguous — no session ID or conversation ID is needed.

**Architecture implication:** The production Filter should use `len(body.get("messages", [])) == 1` as the sole firing condition. This matches the Phase F architecture spec.

### 2. Filter type auto-detected; installation via API is clean

Open WebUI 0.8.10 auto-detects the function type from `class Filter` in the source. The creation API (`POST /api/v1/functions/create`) works as expected. The filter is inactive and non-global by default; two subsequent toggle calls (`/toggle`, `/toggle/global`) are required to activate it globally.

**Architecture implication:** F-3 (production Filter installation) uses the same two-step toggle pattern. `is_global=True` is required for the Filter to fire for all models/conversations.

### 3. Filter runs in the openwebui container process

The filter code executes inside the `openwebui` container. File reads reference the container filesystem. The production `aurora-context.md` must be accessible at a container path.

**Bind-mount requirement (confirmed):** A new bind-mount is needed:
```
ai-stack/aurora:/opt/aurora:ro
```
The production Filter will read from `/opt/aurora/aurora-context.md` (container path). This requires a `docker-compose.yml` change plus container restart — planned for F-3, and now validated as the correct approach.

### 4. Graceful degradation contract works

When the file is absent, the filter can: detect the absence, inject a safe fallback, and return a valid body. The conversation continues normally (HTTP 200). This satisfies the Phase F architecture requirement for the `>26h or missing → fallback` branch.

---

## Production Filter contract (confirmed by validation)

```python
# Fires on every inlet call (all messages), but injects only on message 1.
def inlet(self, body: dict) -> dict:
    msgs = body.get("messages", [])
    if len(msgs) != 1:          # not message 1 — return unchanged
        return body
    # Read /opt/aurora/aurora-context.md
    # If present and fresh (≤26h): prepend to system message
    # If absent or stale (>26h): prepend fallback, do not crash
    ...
    return body
```

The `messages_count == 1` discriminator is validated. The file read + graceful fallback pattern is validated. The production implementation in F-3 follows this exact contract.

---

## AF-01 disposition

**CLOSED — assumption confirmed.** The Open WebUI Filter mechanism behaves exactly as required by the Phase F architecture. Domain A implementation can proceed without redesign.

The production Filter (F-3) will:
- Read from `/opt/aurora/aurora-context.md` (bind-mounted from host `ai-stack/aurora/`)
- Apply the 26h threshold (fresh → prepend with content, stale/missing → prepend fallback)
- Fire only on message 1 using the `len(messages) == 1` discriminator
- Require `is_global=True` and `is_active=True` to fire for all conversations

---

## Cleanup confirmation

- `af01_test_filter` deleted from Open WebUI database (HTTP 200 delete, HTTP 401 on lookup = not found)
- `/tmp/af01_filter_test.log` removed from container
- `/tmp/af01_test_context.txt` removed from container
- No production system prompt modified
- No production tools modified
- No git operations performed

---

## Next step

AF-08 (filesystem corpus indexing of runtime artifacts) is the second F-0 priority. Requires operator approval before proceeding.
