# Phase C C-5 — `ha_call_service` canonical refusal validation — APPLIED

- **Date:** 2026-06-17 (executed wall-clock `2026-06-16T15:46:30Z` UTC,
  consistent with the wall-clock-vs-filename convention used in
  earlier Phase C logs).
- **Status:** **APPLIED.** The canonical out-of-allowlist
  refusal path was exercised against the **installed runtime
  source** (extracted directly from `webui.db.tool.content`),
  loaded inside the running `openwebui` container via
  `importlib`. The probe call
  `ha_call_service(domain="recorder", service="purge",
  entity_id="recorder.purge")` returned the contract-shaped
  refusal JSON with `code="refused"`, `allowed=false`. The
  audit-log gained **exactly one** line with
  `result_code="refused"`, `allowed=false`. **No** `_init()`
  invocation; **no** `httpx` import; **no** read of
  `HA_LLAT` / `HA_BASE_URL` from `os.environ`; **no** HTTP
  request issued to Home Assistant. The class-level state
  invariants (`Tools._httpx_client`, `Tools._bearer`,
  `Tools._base_url` all `None` post-probe) prove the safety
  boundary held end-to-end.
- **Scope:** Tool-level refusal path only. **Does not test
  C-6 (the happy-path `light.turn_on`).** **Does not issue a
  real HA action.** **Does not exercise the prompt-level
  refusal path** (which would require a live chat completion
  routed through qwen2.5; deliberately out of scope per the
  user's stop instruction — the Tool-level safety boundary
  is what carries the load-bearing safety promise per
  readiness review §6).
- **Inputs:**
  - C-4 closeout (the precondition that attached
    `ha_call_service` to qwen2.5 via `meta.toolIds`):
    [`2026-06-17_phaseC_gate_g4_applied.md`](2026-06-17_phaseC_gate_g4_applied.md).
  - C-3 install (the precondition that put the Tool source
    into `webui.db.tool`):
    [`2026-06-17_phaseC_tool_install_applied.md`](2026-06-17_phaseC_tool_install_applied.md).
  - C-2 design + in-process refusal probe against the
    canonical disk source (the pattern this log reproduces
    against the installed runtime source):
    [`2026-06-17_phaseC_ha_call_service_design.md`](2026-06-17_phaseC_ha_call_service_design.md)
    §5.5.
  - Phase C readiness review §6 (refusal grammar), §7 C-5
    row (validation expectations), §10 R-C1 (HA env
    passthrough — present and irrelevant to this path, by
    design):
    [`2026-06-17_phaseC_readiness_review.md`](2026-06-17_phaseC_readiness_review.md).
  - Phase B B-8 / Gate G-3 precedent (same shape of
    in-container probe against the installed source):
    [`2026-06-16_phaseB_validation_applied.md`](2026-06-16_phaseB_validation_applied.md)
    §3.
  - Phase B closeout §6.3 step 9 (the C-5 spec):
    [`2026-06-16_phaseB_closeout.md`](2026-06-16_phaseB_closeout.md).
  - D-12 allowlist (the rule whose refusal path this log
    exercises):
    [`../04_ai_system/amarolab-v1/ROADMAP.md`](../04_ai_system/amarolab-v1/ROADMAP.md)
    §"Decisions taken" D-12.

## 0. TL;DR

| User requirement | Status | Evidence |
|---|---|---|
| **Test case** — `domain="recorder", service="purge", entity_id="recorder.purge"` | ✓ executed | §2.1 probe invocation |
| **Expected** `result_code = "refused"` | ✓ | §2.1 audit-log line; §2.2 return JSON `code: "refused"` |
| **Expected** `allowed = false` | ✓ | §2.1 audit-log line; §2.2 return JSON `allowed: false` |
| **Expected** no Home Assistant call executed | ✓ — derivative proof, no HA traffic | §3.1 (`_httpx_client` None post-probe), §3.2 (`httpx` not in `sys.modules`), §3.3 (refusal returns 83 lines upstream of `self._init()`) |
| **Expected** audit entry generated | ✓ | §2.3 (line count 119 → 120; new line shape correct) |
| **Validation 1** — refusal response shape | ✓ | §2.2 full JSON parse |
| **Validation 2** — audit log entry | ✓ | §2.3 line + secret-shape sweep |
| **Validation 3** — no state change in HA | ✓ — derivative proof | §3 (`_init()` never invoked + container state preserved) |
| **Validation 4** — no outbound HA service execution | ✓ — derivative proof | §3.1, §3.2, §3.3 |

**Phase C C-5 is APPLIED.** The Tool-level safety boundary
holds against the installed runtime source. C-6 (user-driven
happy path against a real HA entity; Gate G-5) is the next
phase and is **deliberately not exercised this turn** per the
user's stop instruction.

## 1. Probe design and source under test

### 1.1 What "installed runtime source" means

Open WebUI 0.8.10 loads a Tool by reading the row's
`content` column from `webui.db.tool` and `exec`-ing it
under a per-Tool module namespace (`tool_<id>`). That is the
**runtime path**. The canonical version-controlled source on
disk (`ai-stack/openwebui-tools/tools/ha_call_service.py`)
is **not** loaded directly — only its post-inline form
(produced by `bin/install_tool`) lives in `webui.db.tool`.

For this probe to validate the path that a live chat-driven
dispatch would actually take, the source under test must be
the byte-for-byte content of `webui.db.tool` where
`id = 'ha_call_service'`. C-3's `bin/dump_tools` artefacts
add a trailing newline; this probe avoids that by going one
level lower:

```bash
$ sqlite3 /srv/homelab/data/openwebui/webui.db \
    "SELECT content FROM tool WHERE id='ha_call_service';" \
    > /tmp/hcs_runtime.py
$ wc -c /tmp/hcs_runtime.py
18516 /tmp/hcs_runtime.py
$ md5sum /tmp/hcs_runtime.py
5a40615c1d0b120816e46700acb4d421  /tmp/hcs_runtime.py
$ python3 -m py_compile /tmp/hcs_runtime.py
PASS
```

The 18 516 wire-bytes count is `length(content)=18494`
(the SQL probe value from C-3 §2.1) + the embedded newlines
SQLite renders verbatim from the stored TEXT column +
trailing newline from the CLI. The MD5
(`5a40615c1d0b120816e46700acb4d421`) matches the SQL probe
`SELECT content … | md5sum` from the C-3 baseline.

### 1.2 Copy into the container

```bash
$ docker cp /tmp/hcs_runtime.py openwebui:/tmp/hcs_runtime.py
$ docker exec openwebui md5sum /tmp/hcs_runtime.py
5a40615c1d0b120816e46700acb4d421  /tmp/hcs_runtime.py
```

Container-side MD5 matches host MD5 byte-for-byte —
`docker cp` did not transform the file.

### 1.3 Code landmarks (post-inline runtime source)

```
$ grep -n 'self._init\|def ha_call_service\|args_snap = \|
              if domain not in _ALLOWED_DOMAINS\|
              httpx_client.post\|self._httpx_client.post' /tmp/hcs_runtime.py
186:    def ha_call_service(
217:        args_snap = {
232:        if domain not in _ALLOWED_DOMAINS:
315:            self._init()
332:            res = Tools._httpx_client.post(
```

The four line numbers define the safety boundary:

| Position | Action |
|---:|---|
| **186** | `def ha_call_service(self, domain, service, entity_id, service_data=None)` — method entry |
| **217** | `args_snap = {…}` — audit snapshot constructed (no LLAT in it) |
| **232** | `if domain not in _ALLOWED_DOMAINS:` — **the refusal short-circuit** |
| **315** | `self._init()` — `httpx` import + `HA_LLAT` env read + `httpx.Client()` construction |
| **332** | `Tools._httpx_client.post(…)` — outbound HTTP request to HA |

The refusal short-circuit (line 232) returns **83 lines
upstream** of `self._init()` (line 315) and **100 lines
upstream** of the `.post(…)` call to HA (line 332). When
the refusal path fires, lines 315 and 332 are **never
reached** in the call's stack frame.

### 1.4 The refusal block, verbatim

`sed -n '225,240p' /tmp/hcs_runtime.py`:

```python
        # SAFETY BOUNDARY — D-12. Runtime allowlist re-check. THIS IS THE FIRST
        # action inside the method body: before service/entity_id validation,
        # before rate-limit, before _init(), before any HTTP request. Even if
        # a future change bypasses the Literal schema enum (e.g. free-form
        # tool_calls from the model, or a frontend change), this check holds.
        # No HTTP request is issued to Home Assistant on this path.
        # ====================================================================
        if domain not in _ALLOWED_DOMAINS:
            _audit("ha_call_service", args_snap, allowed=False, result_code="refused")
            return json.dumps({
                "allowed": False,
                "domain": domain,
                "service": service,
                "code": "refused",
                "message": (
                    f"I can change lights, scenes, climate, media, and similar "
```

(Block continues for ~6 more lines completing the message
string and closing `return json.dumps(...)`.)

The block is structured so that `_audit(...)` runs **first**
(emits the audit-log line), and `json.dumps(...)` is the
function's exclusive exit on this path.

## 2. Probe execution + response

### 2.1 The probe (run inside `openwebui` container)

```python
import sys, json, importlib.util

spec = importlib.util.spec_from_file_location('tool_hcs_runtime', '/tmp/hcs_runtime.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Pre-call invariants
print('PRE  _httpx_client is None?', mod.Tools._httpx_client is None)   # True
print('PRE  _bearer is None?      ', mod.Tools._bearer is None)         # True
print('PRE  _base_url is None?    ', mod.Tools._base_url is None)       # True
print('PRE  httpx in sys.modules? ', 'httpx' in sys.modules)            # False
print('PRE  _ALLOWED_DOMAINS card:', len(mod._ALLOWED_DOMAINS))         # 13
print('PRE  recorder in allowed? ', 'recorder' in mod._ALLOWED_DOMAINS) # False
print('PRE  recorder in denied?  ', 'recorder' in mod._EXPLICITLY_DENIED)  # True

T = mod.Tools()
# valves.max_per_minute = 10, citation = False (from constructor defaults)

# === THE CANONICAL REFUSAL PROBE ===
raw = T.ha_call_service(
    domain='recorder', service='purge', entity_id='recorder.purge'
)
parsed = json.loads(raw)

# Post-call invariants (proving _init was never invoked)
print('POST _httpx_client is None?', mod.Tools._httpx_client is None)   # True
print('POST _bearer is None?      ', mod.Tools._bearer is None)         # True
print('POST _base_url is None?    ', mod.Tools._base_url is None)       # True
print('POST httpx in sys.modules? ', 'httpx' in sys.modules)            # False
```

| Pre-probe class-level state | Value | Significance |
|---|:---:|---|
| `Tools._httpx_client` | **`None`** | No HTTP client has been constructed yet |
| `Tools._bearer` | **`None`** | `HA_LLAT` has not been read from env yet |
| `Tools._base_url` | **`None`** | `HA_BASE_URL` has not been read from env yet |
| `httpx in sys.modules` | **`False`** | `httpx` is not even loaded into the Python process |
| `_ALLOWED_DOMAINS` cardinality | **`13`** | Matches D-12 (the 13-vs-12 text-vs-list note documented in C-2 §3.4) |
| `'recorder' in _ALLOWED_DOMAINS` | **`False`** | Confirms `recorder` is not allowed → refusal path will fire |
| `'recorder' in _EXPLICITLY_DENIED` | **`True`** | Confirms `recorder` is in the documented denylist (C-2 §3.7) — the canonical refusal target |
| `T.valves.max_per_minute` | `10` | C-2 default rate limit for the write Tool |
| `T.citation` | `False` | C-2 default (status-style structured output) |

### 2.2 Return JSON

```json
{
  "allowed": false,
  "domain": "recorder",
  "service": "purge",
  "code": "refused",
  "message": "I can change lights, scenes, climate, media, and similar — not 'recorder.purge'."
}
```

Field-by-field verification against the user's expected
shape and the C-2 design log §4.4:

| Field | Expected | Got | Match? |
|---|---|---|:---:|
| `allowed` | `false` | **`False`** | ✓ |
| `domain` (echoed) | `"recorder"` | **`"recorder"`** | ✓ — what was attempted is preserved in the return JSON for forensic clarity |
| `service` (echoed) | `"purge"` | **`"purge"`** | ✓ |
| `code` | `"refused"` | **`"refused"`** | ✓ |
| `message` | polite one-liner naming the requested `<domain>.<service>` | `"I can change lights, scenes, climate, media, and similar — not 'recorder.purge'."` | ✓ |
| (no `Authorization` field) | — | absent | ✓ |
| (no `bearer` field) | — | absent | ✓ |
| (no `entity_id` echoed back) | — | absent | ✓ — by C-2 design §4.4, the refusal JSON omits `entity_id` |
| (no internal HA URL) | — | absent | ✓ |

The return JSON is exactly what C-2's design log §4.4
specified and exactly what the C-2 design log §5.5 in-
process probe (against the canonical disk source) returned.
**Install fidelity at the return-JSON level is confirmed.**

Note on the difference between the return-JSON field `code`
and the audit-log field `result_code`: this is **deliberate**
per C-2 §4.4 / §4.7. The return JSON uses the short `"code"`
key (consistent with the rest of the v1 Tool return JSONs);
the audit-log uses the verbose `"result_code"` key (consistent
with `_audit(...)` helper contract). Both carry the same
string value `"refused"`.

### 2.3 Audit-log delta

```
$ wc -l /srv/homelab/data/openwebui/amarolab-audit.log
120 /srv/homelab/data/openwebui/amarolab-audit.log

$ md5sum /srv/homelab/data/openwebui/amarolab-audit.log
62bdf45225bd9ea37d6f479cc3dcd5a1  amarolab-audit.log
```

| Metric | Pre-probe | Post-probe | Delta |
|---|---:|---:|---:|
| Line count | 119 | 120 | **+1** |
| MD5 | `4a451cddbf367187448c01b1ecf28d1a` | `62bdf45225bd9ea37d6f479cc3dcd5a1` | (changed — expected; the file is append-only and one line was added) |

The new tail line (one JSONL record, here line-wrapped for
readability):

```json
{
  "ts": "2026-06-16T15:46:30.805776+00:00",
  "id": "481e4e15-3631-4fd3-9633-653f76f0b792",
  "user": "diego",
  "tool": "ha_call_service",
  "args": {
    "domain": "recorder",
    "service": "purge",
    "entity_id": "recorder.purge",
    "service_data": null
  },
  "allowed": false,
  "result_code": "refused",
  "duration_ms": null
}
```

Field-by-field:

| Field | Value | Verified by |
|---|---|---|
| `ts` | `"2026-06-16T15:46:30.805776+00:00"` | ✓ ISO 8601 UTC; ~14 min after C-4 close (`15:32:33Z`) |
| `id` | `"481e4e15-3631-4fd3-9633-653f76f0b792"` | ✓ UUID4 per audit-helper contract |
| `user` | `"diego"` | ✓ matches the per-Tool helper's user constant (D-07) |
| `tool` | `"ha_call_service"` | ✓ Tool id |
| `args.domain` | `"recorder"` | ✓ as sent |
| `args.service` | `"purge"` | ✓ as sent |
| `args.entity_id` | `"recorder.purge"` | ✓ as sent |
| `args.service_data` | `null` | ✓ unspecified parameter (default `None`) |
| `allowed` | `false` | ✓ as required |
| `result_code` | `"refused"` | ✓ as required |
| `duration_ms` | `null` | ✓ short-circuit before t0-elapsed accounting (matches all other `allowed: false` lines pattern from C-1 / C-2) |

### 2.4 Secret-shape audit of the new audit-log line

Three independent regex sweeps:

```
$ tail -1 amarolab-audit.log | grep -ciE 'authorization|bearer'
0
$ tail -1 amarolab-audit.log | grep -cE '[0-9a-fA-F]{64}'
0
$ tail -1 amarolab-audit.log | grep -cE '[A-Za-z0-9_-]{50,}\.[A-Za-z0-9_-]{50,}\.[A-Za-z0-9_-]{30,}'
0
```

**Zero matches** on each pattern. The new line carries:

- No `Authorization` / `Bearer` keyword (the bearer was
  never constructed — see §3).
- No 64-hex string (`HA_LLAT` is a JWT, not 64-hex; the
  `WEBUI_SECRET_KEY` / `QDRANT_API_KEY` are 64-hex but
  never touch the Tool's namespace).
- No JWT-shape string (`HA_LLAT` was never read from
  `os.environ`).

The `_amarolab_redact` helper second-line-of-defense (D-26)
was not even needed here: the LLAT was never in any namespace
the audit helper had visibility into, because `_init()` was
never invoked.

### 2.5 Cross-corpus refusal greppability

```
$ grep -cE '"result_code":\s*"refused"' /srv/homelab/data/openwebui/amarolab-audit.log
3
```

Three total `"result_code": "refused"` lines in the audit log:

1. C-2 design probe — `domain="recorder", service="purge"`
   (canonical refusal probe against the canonical disk source
   — [`2026-06-17_phaseC_ha_call_service_design.md`](2026-06-17_phaseC_ha_call_service_design.md)
   §6.1).
2. C-2 design probe — `domain="backup", service="create"`
   (the second refusal probe — same log §5.5).
3. **C-5 — this turn** — `domain="recorder", service="purge"`
   against the **installed runtime source**.

C-2 and C-5 share the `recorder.purge` shape; C-5
demonstrates the path through the live `webui.db` row, while
C-2 demonstrated the path through the canonical inlined disk
source. Together they prove install fidelity at the
behavioural level (return JSON identical; audit-log shape
identical).

## 3. HA-side derivative proof — no call was made

The user explicitly forbids real HA actions and asks for
proof that none was issued. Direct probe of HA's own access
log is out of scope for the assistant (that would require HA
admin access in the HA UI, which the user owns). Instead, the
**in-process invariants** below establish the proof
end-to-end on the assistant side, and the user can
independently verify HA-side by browsing HA → System → Logs
to confirm zero `/api/services/recorder/purge` entries
appear near `2026-06-16T15:46:30Z`.

### 3.1 Class-level state — `_httpx_client` / `_bearer` / `_base_url` all `None` after the probe

| Variable | Pre-probe | Post-probe | Conclusion |
|---|:---:|:---:|---|
| `Tools._httpx_client` | `None` | **`None`** | No `httpx.Client()` instance was constructed during the call |
| `Tools._bearer` | `None` | **`None`** | `HA_LLAT` was never read from `os.environ`; no `Authorization: Bearer ...` header was assembled |
| `Tools._base_url` | `None` | **`None`** | `HA_BASE_URL` was never read from `os.environ`; no HA URL was formatted |

Per the Tool source (lines 343-369 of `/tmp/hcs_runtime.py` —
inside `_init()`), these three values are set in exactly one
place: the `_init()` method body. If they are still `None`
after the probe, **`_init()` did not run**. Q.E.D.

### 3.2 `httpx in sys.modules` is `False` after the probe

```python
PRE  httpx in sys.modules?  False
POST httpx in sys.modules?  False
```

Per the Tool source, `import httpx` lives **only inside**
`_init()` (deferred-import pattern documented in C-2 §3.3).
The Python `sys.modules` registry would carry an `'httpx'`
key the moment the import executes. It does not.

This is the strongest single derivative proof: **even the
HA-client library was not loaded into the Python process**.
A library that is not loaded cannot construct an HTTP
request.

### 3.3 Static analysis — refusal returns upstream of `_init()` and `.post()`

Recall the line landmarks from §1.3:

| Line | Action |
|---:|---|
| 232 | `if domain not in _ALLOWED_DOMAINS:` (the refusal check) |
| 233 | `_audit(...)` (audit-log emission) |
| 234 | `return json.dumps({...})` (refusal-path return) |
| 315 | `self._init()` (httpx import + env reads + Client construction) |
| 332 | `Tools._httpx_client.post(...)` (the actual HTTP call) |

Once line 234 returns, no further code in `ha_call_service`
executes for this call. Lines 315 and 332 are unreachable on
the refusal path. The static structure of the function
guarantees this property; the runtime invariants in §3.1 /
§3.2 confirm it actually held at execution time.

### 3.4 Container state — preserved (no restart, no network change)

```
$ docker inspect openwebui --format 'State={{.State.Status}} Health={{.State.Health.Status}} StartedAt={{.State.StartedAt}}'
State=running Health=healthy StartedAt=2026-06-16T12:35:59.30214094Z
```

The `openwebui` container has been running continuously
since G-Cpre Attempt 2 (`2026-06-16T12:35:59Z`) — ~3 h 11 min
of uptime at the moment of the probe. No `docker stop`,
`docker restart`, `docker rm`, no network change. The
`/opt/ingest:ro` bind mount and `HA_BASE_URL` / `HA_LLAT`
env passthrough from G-Cpre remain intact (the latter is
**irrelevant** to this probe because the refusal path does
not read them, by design).

### 3.5 Sufficient combination for HA-no-call proof

The three properties together — `_httpx_client` is `None` ∧
`httpx` is not in `sys.modules` ∧ the source statically
returns at line 234 — form a **closed proof** that:

1. No HTTP client was constructed.
2. No HTTP request was sent over any socket.
3. The request never reached the kernel TCP stack, much less
   the LAN, much less HA's `:8123`.

HA's access log will not show a request from this probe.
**No HA state was changed.**

## 4. Forensic state at end of C-5

| Item | Value |
|---|---|
| `webui.db.tool.ha_call_service.content` | unchanged (18 494 chars, 1 spec) — no SQL write this turn |
| qwen2.5 `meta.toolIds` | `["time_now","rag_search","audit_search","ha_get_state","ha_call_service"]` — unchanged from C-4 |
| qwen2.5 `base_model_id` | `NULL` (D-35) — unchanged |
| qwen2.5 `params.system` length | 3 342 chars — unchanged |
| llama3* rows | unchanged — D-20 still holds |
| `amarolab-audit.log` line count | 120 (delta vs pre-probe = **+1**) |
| `amarolab-audit.log` MD5 | `62bdf45225bd9ea37d6f479cc3dcd5a1` |
| Total `result_code: "refused"` lines | 3 (2 C-2 probes + 1 C-5 probe) |
| `openwebui` container | running healthy; uptime ~3 h 11 min; StartedAt `2026-06-16T12:35:59Z`; no restart this turn |
| `qdrant` container | running healthy (untouched) |
| HA env passthrough | alive in `openwebui` (`HA_BASE_URL` len 26, `HA_LLAT` len 183) — **not consumed by this probe by design** |
| `Tools._httpx_client` (in the probe's sub-interpreter) | `None` at end |
| `Tools._bearer` | `None` at end |
| `Tools._base_url` | `None` at end |
| `httpx` module load | not loaded in the probe sub-interpreter |
| Probe artefacts | `/tmp/hcs_runtime.py` on host (MD5 `5a40615c1d0b120816e46700acb4d421`); `/tmp/hcs_runtime.py` in container (same MD5) — both are tmpfs / next-reboot cleanup |
| HA-side state (assistant cannot verify directly) | no request sent ⇒ no state change ⇒ user-verifiable via HA → System → Logs |

## 5. What this log deliberately did NOT do

- **Did not exercise C-6.** The happy-path
  `"turn on the kitchen light"` prompt was not run, and no
  real HA action of any kind was issued. The Gate G-5 user
  approval awaits explicit instruction.
- **Did not exercise the prompt-level refusal path.** A
  live chat round-trip through qwen2.5 was not initiated
  here. The Tool-level safety boundary is what carries the
  load-bearing safety guarantee per readiness review §6;
  exercising the prompt layer is a separate qualitative
  observation that the user can do at C-6 time.
- **Did not modify `webui.db`.** No SQL UPDATE / INSERT /
  DELETE. The C-4 toolIds extension stands as is.
- **Did not modify `.env`.** No secret rotation, no key
  change. The `HA_LLAT` issued at G-Cpre remains in place
  (and was deliberately not consumed by the refusal path).
- **Did not modify any Tool row.** The 8 rows in
  `webui.db.tool` are byte-identical to the C-3 baseline.
- **Did not recreate, restart, or otherwise disturb the
  `openwebui` or `qdrant` containers.** Uptime preserved.
- **Did not call HA.** §3 establishes the in-process proof
  end-to-end.
- **Did not log any secret.** §2.4 sweep is zero across the
  three patterns.
- **Did not commit anything.** Per the user's
  "Stop after validation, documentation, git status"
  instruction. Commits are user-gated.

## 6. Recommended next step

Per the Phase C readiness review §11 step 8 / step 9 and the
user's gate sequence:

1. **C-6 (user-driven; Gate G-5) — canonical happy path.**
   Chat `"turn on the kitchen light"` (or any other
   allowlisted action against a real entity the user has at
   home). Expected: physical state change + audit-log
   `+1` line with `tool: "ha_call_service"`,
   `args.domain: "light"`, `args.service: "turn_on"`,
   `allowed: true`, `result_code: "ok"`, `duration_ms`
   ≤ ~1500 ms (warm) or ≤ ~3000 ms (cold).
2. **C-7** — docs sync (CURRENT_STATE / ROADMAP /
   AMAROLAB_HANDOFF) + git commit + Phase D hand-off note.

C-5 has demonstrated the **safety side** of the read+write
HA Tool pair. C-6 will demonstrate the **functional side**.
Together they cover the Phase C exit criterion in the Phase
B closeout §6.3.

If the user wants to commit C-5 first, the natural
commit-message form is:

```
test(amarolab): canonical refusal validation for ha_call_service (C-5)

- In-container probe against the installed runtime source
  (extracted directly from webui.db.tool.content, MD5
  5a40615c1d0b120816e46700acb4d421). Call signature
  ha_call_service(domain="recorder", service="purge",
  entity_id="recorder.purge"). Result: allowed=false,
  code="refused", expected polite message returned.
- Tool-level safety boundary held: refusal at line 232
  returns 83 lines upstream of self._init() (line 315) and
  100 lines upstream of httpx.post() (line 332). Class-level
  _httpx_client / _bearer / _base_url all None post-probe;
  httpx never loaded into sys.modules. HA-side: no request
  issued, no state change.
- Audit-log delta = +1, line shape matches contract
  (tool=ha_call_service, args={domain,service,entity_id,
  service_data:null}, allowed=false, result_code="refused",
  duration_ms=null). Secret-shape sweep returns 0 across
  Bearer/64-hex/JWT patterns. No LLAT in audit log.
- 09_logs/2026-06-17_phaseC_refusal_validation_applied.md —
  this log; full probe execution; HA-no-call derivative
  proofs; forensic state.
```

## 7. Cross-references

- C-4 closeout (the precondition that attached
  `ha_call_service` to qwen2.5):
  [`2026-06-17_phaseC_gate_g4_applied.md`](2026-06-17_phaseC_gate_g4_applied.md)
- C-3 install:
  [`2026-06-17_phaseC_tool_install_applied.md`](2026-06-17_phaseC_tool_install_applied.md)
- C-2 design + in-process refusal probe against canonical
  disk source (this log reproduces the shape against the
  installed runtime source):
  [`2026-06-17_phaseC_ha_call_service_design.md`](2026-06-17_phaseC_ha_call_service_design.md)
  §5.5
- C-1 design (sibling Tool):
  [`2026-06-17_phaseC_ha_get_state_design.md`](2026-06-17_phaseC_ha_get_state_design.md)
- G-Cpre closure (env passthrough; intentionally
  un-consumed by this probe):
  [`2026-06-17_phaseC_secret_rotation_and_gcpre_applied.md`](2026-06-17_phaseC_secret_rotation_and_gcpre_applied.md)
- Phase C readiness review (refusal grammar, validation
  matrix, three-layer defense):
  [`2026-06-17_phaseC_readiness_review.md`](2026-06-17_phaseC_readiness_review.md)
  §6 / §7 (C-5 row) / §3.1 / §4.5
- Phase B B-8 / Gate G-3 precedent (in-container probe
  against dumped runtime source):
  [`2026-06-16_phaseB_validation_applied.md`](2026-06-16_phaseB_validation_applied.md)
  §3
- Phase B closeout §6.3 step 9 (C-5 spec):
  [`2026-06-16_phaseB_closeout.md`](2026-06-16_phaseB_closeout.md)
- D-12 allowlist (the rule whose refusal path was
  exercised):
  [`../04_ai_system/amarolab-v1/ROADMAP.md`](../04_ai_system/amarolab-v1/ROADMAP.md)
- D-30 refusal grammar (the system-prompt-level refusal
  that is **complementary**, not exercised here):
  [`../04_ai_system/amarolab-v1/ROADMAP.md`](../04_ai_system/amarolab-v1/ROADMAP.md)
- Audit helper contract (the `_audit(...)` shape the new
  log line conforms to):
  [`../ai-stack/openwebui-tools/lib/audit_helper.py`](../ai-stack/openwebui-tools/lib/audit_helper.py)
- Sub-project live state (to be refreshed at C-7, not this
  turn):
  [`../04_ai_system/amarolab-v1/CURRENT_STATE.md`](../04_ai_system/amarolab-v1/CURRENT_STATE.md),
  [`../04_ai_system/amarolab-v1/ROADMAP.md`](../04_ai_system/amarolab-v1/ROADMAP.md),
  [`../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md`](../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md)

## 8. Stop point

Per the user's instruction
("Stop after: validation, documentation, git status. Do not
continue to C-6. Do not execute any real HA action."): this
log is the artefact. **Phase C C-5 (canonical refusal
validation) is APPLIED.** The Tool-level safety boundary
held against the installed runtime source. C-6 (Gate G-5 —
user-driven happy path on a real HA entity) awaits explicit
user instruction.
