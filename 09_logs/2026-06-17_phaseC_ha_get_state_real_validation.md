# Phase C C-6a — `ha_get_state` first real Home Assistant read validation — APPLIED

- **Date:** 2026-06-17 (executed wall-clock `2026-06-16T15:58:12Z` UTC,
  consistent with the wall-clock-vs-filename convention used in
  earlier Phase C logs).
- **Status:** **APPLIED.** The first **real Home Assistant call**
  in this sub-project's history was issued from the
  Amarolab Assistant Tool layer — a single GET to
  `${HA_BASE_URL}/api/states/sun.sun` from inside the
  `openwebui` container, with the LLAT-bearing
  `Authorization: Bearer …` header constructed in-process and
  never persisted to disk. The probe returned
  `result_code="ok"`, `state="above_horizon"`,
  `friendly_name="Sun"`, with `duration_ms=83` (cold). The
  audit-log gained **exactly one** line carrying the
  contract-shaped success record. The LLAT did not appear in
  any artefact (chat, audit log, return JSON). All Phase A/B/C
  invariants (`base_model_id=NULL`, qwen2.5 `meta.toolIds` 5-list,
  llama3* rows untouched, `params.system` 3 342 chars) hold.
- **Scope:** Tool-level real read against the user-provided
  entity `sun.sun`. **Does not call `ha_call_service`**. **Does
  not change any Home Assistant state** (HTTP GETs are
  read-only by HA's REST API contract). **Does not exercise
  the prompt-level / live-chat path** — this is a direct
  in-container probe against the installed runtime source, the
  same shape that B-8 used for `rag_search` end-to-end. The
  live-chat happy-path (C-6 / Gate G-5 against a real
  controllable entity like `light.<...>`) remains the next
  user-gated step and is **explicitly out of scope this turn**.
- **Inputs:**
  - User-provided entity_id `sun.sun` (selected this turn from
    the three suggested candidates `sun.sun` / `weather.home`
    / `zone.home`).
  - C-5 closeout (the precondition that proved the Tool-level
    safety boundary on the write Tool's refusal path):
    [`2026-06-17_phaseC_refusal_validation_applied.md`](2026-06-17_phaseC_refusal_validation_applied.md).
  - C-4 closeout (the precondition that attached
    `ha_get_state` to qwen2.5 via `meta.toolIds`):
    [`2026-06-17_phaseC_gate_g4_applied.md`](2026-06-17_phaseC_gate_g4_applied.md).
  - C-3 install (the precondition that put the Tool source
    into `webui.db.tool`):
    [`2026-06-17_phaseC_tool_install_applied.md`](2026-06-17_phaseC_tool_install_applied.md).
  - C-1 design (the read-Tool contract, attribute allowlist,
    8 result codes):
    [`2026-06-17_phaseC_ha_get_state_design.md`](2026-06-17_phaseC_ha_get_state_design.md).
  - G-Cpre closure (the prerequisite that made `HA_BASE_URL` /
    `HA_LLAT` visible to the openwebui container's Python
    runtime):
    [`2026-06-17_phaseC_secret_rotation_and_gcpre_applied.md`](2026-06-17_phaseC_secret_rotation_and_gcpre_applied.md).
  - Phase C readiness review §3 (Tool contract), §7 C-aux1 row
    (the `sun.sun` benign happy-path probe), §7 C-aux4 (response-
    time observation):
    [`2026-06-17_phaseC_readiness_review.md`](2026-06-17_phaseC_readiness_review.md).
  - Phase B B-8 precedent (in-container probe against installed
    runtime source):
    [`2026-06-16_phaseB_validation_applied.md`](2026-06-16_phaseB_validation_applied.md)
    §3.

## 0. TL;DR

| User requirement | Status | Evidence |
|---|---|---|
| Use a harmless real entity | ✓ | `sun.sun` — built-in HA sun integration; read-only |
| Prefer sensor / binary_sensor | n/a — user chose `sun.sun` from the offered options (declined to provide a `sensor.*` entity from their install; `sun.sun` is the universally-present fallback) | §1.0 |
| Do not call `ha_call_service` | ✓ | only `ha_get_state` invoked; no POST to `/api/services/*` |
| Do not change any HA state | ✓ — GET only | §3.3, §6.4 |
| `result_code = "ok"` | ✓ | §3.2 return JSON; §4.1 audit-log line |
| Audit log entry exists | ✓ | §4 — line count 120 → 121 (+1); full field parse |
| `HA_LLAT` is not logged | ✓ | §4.2 secret-shape sweep (0 / 0 / 0) |
| `base_model_id` remains `NULL` | ✓ | §5.1 — D-35 preserved |
| `toolIds` remain unchanged | ✓ | §5.1 — 5-list intact since C-4 |

**Phase C C-6a is APPLIED.** The read path is now live and
proven end-to-end. C-6 (Gate G-5 — live-chat happy-path via
`ha_call_service` against a real controllable entity) is the
next user-gated step.

## 1. Entity-of-test rationale

The user instruction explicitly required asking before
running the probe. The three offered candidates were:

| Candidate | Description | Domain | User chose? |
|---|---|---|:---:|
| `sun.sun` | Universally-present HA built-in; state is `"above_horizon"` / `"below_horizon"`; harmless read | `sun` | **✓** |
| `weather.home` | Common default if user has Met.no integration | `weather` | — |
| `zone.home` | Built-in zone for the configured home location | `zone` | — |

The user chose `sun.sun`, the universally-safe fallback. None
of the three is `sensor.*` or `binary_sensor.*`, but
`sun.sun` is guaranteed to exist on every HA install (it's
part of the HA core), which is the strongest baseline-
correctness guarantee for a first-real-call probe. The
"prefer a sensor or binary_sensor" preference is a soft hint;
the hard constraint ("harmless real entity") is met.

`sun.sun` is also documented in the Phase C readiness review
§7 C-aux1 row as the example benign happy-path entity:

> chat "what's the state of sun.sun?" → `ha_get_state(entity_id="sun.sun")`
> → `result_code: ok`, `state` is one of `"above_horizon"` /
> `"below_horizon"`

so this probe directly satisfies C-aux1.

## 2. Probe design and source under test

### 2.1 "Installed runtime source" — same pattern as C-5

Extracted from `webui.db.tool.content` where `id='ha_get_state'`:

```bash
$ sqlite3 /srv/homelab/data/openwebui/webui.db \
    "SELECT content FROM tool WHERE id='ha_get_state';" \
    > /tmp/hgs_runtime.py
$ wc -c /tmp/hgs_runtime.py
15001 /tmp/hgs_runtime.py
$ md5sum /tmp/hgs_runtime.py
4cad688fd82b65ccd8d2ca23ea6dc474  /tmp/hgs_runtime.py
$ python3 -m py_compile /tmp/hgs_runtime.py
PASS

$ docker cp /tmp/hgs_runtime.py openwebui:/tmp/hgs_runtime.py
$ docker exec openwebui md5sum /tmp/hgs_runtime.py
4cad688fd82b65ccd8d2ca23ea6dc474  /tmp/hgs_runtime.py
```

The 15 001 wire-bytes count is `length(content)=14982` (C-3
§2.1) + embedded newlines + trailing newline from the SQLite
CLI. Host/container MD5s match byte-for-byte — `docker cp` did
not transform the file.

### 2.2 Code landmarks in the runtime source

```
$ grep -n 'def ha_get_state\|args_snap = \|self._init\|_httpx_client.get\|_ENTITY_ID_RE\|_SAFE_ATTRIBUTE_KEYS' /tmp/hgs_runtime.py
89:_ENTITY_ID_RE = re.compile(r"^[a-z_]+\.[a-z0-9_]+$")
115:_SAFE_ATTRIBUTE_KEYS = frozenset({
261:    def ha_get_state(self, entity_id: str) -> str:
269:        args_snap = {"entity_id": entity_id}
282:        if not _ENTITY_ID_RE.match(entity_id):
297:            self._init()
309:            res = Tools._httpx_client.get(
```

The successful read path for a well-formed `entity_id` like
`"sun.sun"` traverses:

| Line | Action |
|---:|---|
| 261 | `def ha_get_state(self, entity_id)` — method entry |
| 269 | `args_snap = {"entity_id": "sun.sun"}` — audit snapshot (only entity_id) |
| 282 | `_ENTITY_ID_RE.match(...)` — regex check **passes** for `sun.sun` (`[a-z_]+\.[a-z0-9_]+`) |
| 297 | `self._init()` — `httpx` import + `HA_BASE_URL` / `HA_LLAT` read + `httpx.Client` construction |
| 309 | `Tools._httpx_client.get(...)` — outbound HTTP GET to `${HA_BASE_URL}/api/states/sun.sun` with `Authorization: Bearer …` |

Unlike C-5's refusal probe (which short-circuits at line 234,
upstream of `_init()`), this happy path **does** invoke
`_init()` and **does** issue an HTTP GET to HA. Both side
effects are evidenced in §3.5 (class-level state changes)
and §6.

## 3. Probe execution + response

### 3.1 The probe (run inside `openwebui` container)

```python
import sys, json, importlib.util, time

spec = importlib.util.spec_from_file_location('tool_hgs_runtime', '/tmp/hgs_runtime.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Pre-call invariants (proving no prior init)
print('PRE  _httpx_client is None?', mod.Tools._httpx_client is None)   # True
print('PRE  _bearer is None?      ', mod.Tools._bearer is None)         # True
print('PRE  _base_url is None?    ', mod.Tools._base_url is None)       # True
print('PRE  httpx in sys.modules? ', 'httpx' in sys.modules)            # False
print('PRE  _SAFE_ATTRIBUTE_KEYS cardinality:', len(mod._SAFE_ATTRIBUTE_KEYS))  # 87

T = mod.Tools()
# valves.max_per_minute = 60, citation = False (from constructor defaults)

# === THE FIRST REAL HA CALL ===
t0 = time.monotonic()
raw = T.ha_get_state(entity_id='sun.sun')
elapsed = time.monotonic() - t0
parsed = json.loads(raw)

# Post-call invariants (proving _init was invoked and the
# HA call succeeded; values not printed — lengths only)
print('POST _httpx_client is None?', mod.Tools._httpx_client is None)   # False
print('POST _bearer is None?      ', mod.Tools._bearer is None)         # False
print('POST _base_url is None?    ', mod.Tools._base_url is None)       # False
print('POST httpx in sys.modules? ', 'httpx' in sys.modules)            # True
print('POST _bearer length        :', len(mod.Tools._bearer))           # 190
print('POST _base_url length      :', len(mod.Tools._base_url))         # 26
```

| Pre-probe class-level state | Value |
|---|:---:|
| `Tools._httpx_client` | `None` |
| `Tools._bearer` | `None` |
| `Tools._base_url` | `None` |
| `httpx in sys.modules` | `False` |
| `_SAFE_ATTRIBUTE_KEYS` cardinality | `87` (matches C-1 §3.4) |
| `T.valves.max_per_minute` | `60` (C-1 default — read Tools get the high ceiling) |
| `T.citation` | `False` (status-style structured output) |

Wall-clock elapsed: **83 ms** (cold call — including `httpx`
import, `httpx.Client()` construction, the LAN GET to HA, JSON
parse, and attribute-allowlist filter). This is well under the
readiness review §7 C-aux4 expectation (cold ≤ 3 s, warm
≤ 1 s).

### 3.2 Return JSON

```json
{
  "entity_id": "sun.sun",
  "state": "above_horizon",
  "friendly_name": "Sun",
  "last_changed": "2026-06-16T04:52:57.703302+00:00",
  "last_updated": "2026-06-16T15:56:03.085512+00:00",
  "attributes": {},
  "result_code": "ok"
}
```

Field-by-field verification against the C-1 design §3.8
output-shape contract and the user's expected criteria:

| Field | Expected | Got | Match? |
|---|---|---|:---:|
| `entity_id` | `"sun.sun"` | **`"sun.sun"`** | ✓ |
| `state` | `"above_horizon"` or `"below_horizon"` | **`"above_horizon"`** | ✓ — sun is up in Madrid at 15:58 UTC (17:58 local, mid-June) |
| `friendly_name` | non-empty string | **`"Sun"`** | ✓ |
| `last_changed` | ISO 8601 UTC | **`"2026-06-16T04:52:57.703302+00:00"`** | ✓ — sun rose this morning ~04:52 UTC (06:52 local Madrid) |
| `last_updated` | ISO 8601 UTC, ≥ `last_changed` | **`"2026-06-16T15:56:03.085512+00:00"`** | ✓ — HA updates `sun.sun.last_updated` on every elevation/azimuth tick |
| `attributes` | object (may be empty after allowlist filter) | **`{}`** | ✓ — see §3.4 below |
| `result_code` | `"ok"` | **`"ok"`** | ✓ |
| (no `Authorization` field) | — | absent | ✓ |
| (no `bearer` field) | — | absent | ✓ |
| (no `HA_LLAT` value anywhere) | — | absent | ✓ |
| (no internal HA URL leaked) | — | absent | ✓ |

The return JSON exactly satisfies the C-1 design §3.8
contract: `entity_id`, `state`, `friendly_name` at top level;
`last_changed` / `last_updated` ISO 8601; `attributes` dict;
`result_code`. **No bearer, no LLAT, no internal URL escapes
to the caller.**

### 3.3 Why `attributes: {}` (the allowlist working as designed)

HA's `sun.sun` carries these attributes in its raw state:
`next_dawn`, `next_dusk`, `next_midnight`, `next_noon`,
`next_rising`, `next_setting`, `elevation`, `azimuth`,
`rising`, `friendly_name`. None of these (except
`friendly_name`, which is surfaced at top-level per C-1 §3.4)
are members of the 87-key `_SAFE_ATTRIBUTE_KEYS` allowlist.

C-1 §3.4 explicitly chose **allowlist over denylist** for HA
attributes:

> The choice of **allowlist over denylist** matters: new HA
> integrations cannot silently add forwarded attributes;
> growing this set is an explicit Phase C+ design decision,
> not a passive risk.

`sun` is not one of the categories the allowlist covers
(universal metadata + light / cover / climate / media_player
/ fan / vacuum / script / automation / input_* / sensor). So
`sun.sun`'s attributes are filtered to `{}`. The `state` field
alone carries the load-bearing information for the canonical
"is the sun up?" question, so this filter behaviour is
**correct** and **harmless** for `sun.sun`.

If a future user wants to surface `sun.sun.elevation` or
`sun.sun.next_dawn`, that becomes a v1.1+ allowlist
extension — a single-line change to `_SAFE_ATTRIBUTE_KEYS`
and a re-install. Not done this turn.

### 3.4 The first HA REST call from this sub-project

Combining the in-process invariants in §3.5 with the return
JSON in §3.2 yields the strongest evidence we can produce on
the assistant side: an HTTP GET went to
`${HA_BASE_URL}/api/states/sun.sun` and HA returned 200 with
the documented sun-state JSON body. **Home Assistant
participated in the assistant's runtime for the first time
in this sub-project's history**, and the call is fully
recorded in the audit log (§4).

User-side independent verification: HA → Settings → Logs (or
HA `home-assistant.log`) should show one
`GET /api/states/sun.sun` entry from the
`openwebui`-container IP at `2026-06-16T15:58:12Z`. The
assistant cannot read HA's logs directly (no HA admin
access), but the test is symmetric — if HA returned the JSON
in §3.2, HA logged the request.

### 3.5 Class-level state — `_init()` fired (this is normal for a happy path)

| Variable | Pre-probe | Post-probe |
|---|:---:|:---:|
| `Tools._httpx_client` | `None` | **non-None** (an `httpx.Client` instance) |
| `Tools._bearer` | `None` | **non-None** — length `190` = `"Bearer "` (7) + LLAT (183) |
| `Tools._base_url` | `None` | **non-None** — length `26` (matches `.env` `HA_BASE_URL` length per G-Cpre §2) |
| `httpx in sys.modules` | `False` | **`True`** (deferred import fired inside `_init()`) |

This is the **expected** state transition for a successful
read. Compare to C-5 (refusal):

| State | C-5 refusal (post) | C-6a happy path (post) |
|---|:---:|:---:|
| `_httpx_client` | `None` | **non-None** |
| `_bearer` | `None` | **non-None** |
| `_base_url` | `None` | **non-None** |
| `httpx` loaded | no | **yes** |

The class-level state is a process-scoped singleton: once
`_init()` fires in the openwebui Python process, subsequent
calls to `ha_get_state` (or to `ha_call_service`, when its
`_init()` fires) reuse the same `httpx.Client` + bearer
without re-reading `.env`. This is the connection-pooling
design documented in C-1 §3.1. In the **probe**'s own
sub-interpreter (a fresh process spawned by
`docker exec python3 -c`), the state was initially clean —
this lets us assert the pre-probe baseline cleanly. The main
`openwebui` server process (uvicorn) is a **separate** process
from the probe; this probe did not initialise its global
state.

### 3.6 The LLAT was read, used, and never printed

The probe's output line `POST _bearer length: 190` prints the
**length** of `Tools._bearer` (`len("Bearer " + LLAT) = 7 +
183`), not its value. The same applies to `_base_url`: only
the length (26) was emitted. Neither value was substituted or
echoed.

The LLAT lives in three places during this probe:
1. The container's `os.environ["HA_LLAT"]` (read at line 297's
   `_init()`).
2. `Tools._bearer` (in-process Python string, scoped to the
   probe sub-interpreter — discarded at process exit).
3. The `Authorization: Bearer …` HTTP header on the outbound
   GET (in-flight TCP bytes, never persisted to disk on the
   assistant side; HA's logs may record the request line +
   client IP but typically not the header value).

It does **not** appear in:
- The audit log (`args_snap` is built at line 269 with only
  `entity_id`; the LLAT is never a member).
- The return JSON to the caller (no `Authorization` /
  `bearer` field).
- Any stdout from the probe (length-only prints).

## 4. Audit-log delta

### 4.1 Line count + new line

```
$ wc -l /srv/homelab/data/openwebui/amarolab-audit.log
121 /srv/homelab/data/openwebui/amarolab-audit.log
$ md5sum /srv/homelab/data/openwebui/amarolab-audit.log
647cdad6487757f59d625dcf6c8d5774  amarolab-audit.log
```

| Metric | Pre-probe | Post-probe | Delta |
|---|---:|---:|---:|
| Line count | 120 | 121 | **+1** |
| MD5 | `62bdf45225bd9ea37d6f479cc3dcd5a1` | `647cdad6487757f59d625dcf6c8d5774` | (changed — expected; append-only +1 line) |

The new tail line (one JSONL record):

```json
{
  "ts": "2026-06-16T15:58:12.819992+00:00",
  "id": "1ae779ea-10e2-4703-9b2a-417009888949",
  "user": "diego",
  "tool": "ha_get_state",
  "args": {"entity_id": "sun.sun"},
  "allowed": true,
  "result_code": "ok",
  "duration_ms": 83
}
```

Field-by-field:

| Field | Value | Verified by |
|---|---|---|
| `ts` | `"2026-06-16T15:58:12.819992+00:00"` | ✓ ISO 8601 UTC; ~12 min after C-5 close (`15:46:30Z`) |
| `id` | `"1ae779ea-10e2-4703-9b2a-417009888949"` | ✓ UUID4 per audit-helper contract |
| `user` | `"diego"` | ✓ matches the per-Tool helper's user constant (D-07) |
| `tool` | `"ha_get_state"` | ✓ Tool id |
| `args.entity_id` | `"sun.sun"` | ✓ as requested |
| (no other args fields) | — | ✓ — `args_snap` for the read Tool carries only `entity_id` (C-1 §3.3 first-line-of-defense) |
| `allowed` | `true` | ✓ — the call was within scope (LLM-decision-to-call was allowed) |
| `result_code` | `"ok"` | ✓ — HA returned 200, parseable JSON |
| `duration_ms` | `83` | ✓ — matches the probe's wall-clock measurement (the audit helper uses the same `time.monotonic()` reference) |

### 4.2 Secret-shape audit of the new line

```
$ tail -1 amarolab-audit.log | grep -ciE 'authorization|bearer'
0
$ tail -1 amarolab-audit.log | grep -cE '[0-9a-fA-F]{64}'
0
$ tail -1 amarolab-audit.log | grep -cE '[A-Za-z0-9_-]{50,}\.[A-Za-z0-9_-]{50,}\.[A-Za-z0-9_-]{30,}'
0
```

**Zero matches** across all three patterns:

- No `Authorization` / `Bearer` keyword (the bearer was
  constructed in-process and sent as an HTTP header — never
  serialised into the audit-log JSON).
- No 64-hex string (`HA_LLAT` is JWT-shaped, not 64-hex; the
  64-hex secrets — `WEBUI_SECRET_KEY` / `QDRANT_API_KEY` — are
  not in the Tool's namespace at all).
- No JWT-shape string (`HA_LLAT` was never put into
  `args_snap` and was never serialised into the audit line).

The `_amarolab_redact` helper (D-26 second-line-of-defense)
was not needed here either: the LLAT was never in any
namespace the audit helper had visibility into, because
`args_snap` is built explicitly with only the declared
parameters.

## 5. Model-row invariants (D-20 + D-35 still hold)

### 5.1 qwen2.5 unchanged from C-4

```
$ sqlite3 webui.db \
    "SELECT id, base_model_id,
            json_extract(meta,'$.toolIds'),
            length(json_extract(params,'$.system')),
            updated_at
     FROM model WHERE id='qwen2.5:7b-instruct';"
qwen2.5:7b-instruct|(NULL)|["time_now","rag_search","audit_search","ha_get_state","ha_call_service"]|3342|1781623953
```

| Field | Pre-C-6a | Post-C-6a | Match? |
|---|---|---|:---:|
| `id` | `qwen2.5:7b-instruct` | `qwen2.5:7b-instruct` | ✓ |
| `base_model_id` | `NULL` (D-35) | **`NULL`** | ✓ **D-35 preserved** |
| `meta.toolIds` | `["time_now","rag_search","audit_search","ha_get_state","ha_call_service"]` (C-4) | **same 5-list** | ✓ |
| `params.system` length | 3 342 chars (v0.1 prompt) | **3 342** | ✓ |
| `updated_at` | `1781623953` (C-4) | `1781623953` | ✓ **unchanged** |

The probe did **not** touch the qwen2.5 Model row — only the
`amarolab-audit.log` and HA itself. `updated_at` is byte-
identical to the C-4 timestamp.

### 5.2 D-20 invariant — llama3* still untouched

```
$ sqlite3 webui.db \
    "SELECT id, base_model_id,
            json_extract(meta,'$.toolIds'), updated_at
     FROM model WHERE id LIKE 'llama%' OR id LIKE 'phi%'
     ORDER BY id;"
llama3.2:latest||["docker_logs","docker_containers","system_status"]|1773442892
llama3:latest||["docker_containers","system_status","docker_logs"]|1775031217
```

Both Jarvis-era rows carry their original Jarvis tool sets
and their original `updated_at` timestamps from before any
Amarolab Phase A work began. **Neither contains
`ha_get_state` or `ha_call_service`.** D-20 per-model scope
holds — only qwen2.5 sees the HA Tools.

### 5.3 `tool` table — byte-identical to C-5 / C-4 / C-3

```
$ sqlite3 webui.db \
    "SELECT id, length(content), json_array_length(specs)
     FROM tool ORDER BY id;"
audit_search       | 11231 | 1
docker_containers  |   890 | 1
docker_logs        |   585 | 1
ha_call_service    | 18494 | 1
ha_get_state       | 14982 | 1
rag_search         | 11629 | 1
system_status      |   507 | 1
time_now           |  5180 | 1
```

All 8 rows preserved with the C-3 install fidelity (lengths
and spec counts byte-identical). The probe did not modify
`webui.db.tool`.

## 6. HA-side observations

### 6.1 The single GET that happened

The probe issued exactly one HTTP request:

```
GET ${HA_BASE_URL}/api/states/sun.sun
Authorization: Bearer ${HA_LLAT}
Accept: */*
User-Agent: python-httpx/<version>
```

(Headers reconstructed from the C-1 design; the
`Authorization` value is the bearer string — value not
printed here.)

HA responded with **200 OK** and a JSON body containing the
sun state. The Tool extracted `entity_id`, `state`,
`attributes.friendly_name` (surfaced at top-level),
`last_changed`, `last_updated`, applied the
`_SAFE_ATTRIBUTE_KEYS` filter to `attributes`, and returned
the JSON in §3.2.

### 6.2 What HA did NOT see

- No POST. No `/api/services/*` request.
- No write of any kind.
- No state changed on the HA side — `GET /api/states/sun.sun`
  is read-only by HA's REST API contract.
- No request to any other entity_id.
- No request from any other source than the openwebui
  container's IP on the LAN.

### 6.3 The user can independently verify HA-side

Recommended user-side check, when convenient:

1. HA → Settings → System → Logs (or `tail home-assistant.log`).
2. Filter near timestamp `2026-06-16T15:58:12Z` (Madrid local
   `17:58:12`).
3. Expected entry shape:
   ```
   INFO (MainThread) [homeassistant.components.http.view] Serving /api/states/sun.sun to <openwebui-IP>
   ```
   (Exact log line shape varies by HA version; the
   substantive content is "single GET to `/api/states/sun.sun`
   from the openwebui-container IP at that minute").

### 6.4 Why this is "no HA state change"

HA's `/api/states/<entity_id>` is a **read** endpoint by HA's
own REST API contract
(`https://developers.home-assistant.io/docs/api/rest/`). A
GET cannot mutate state. HA's `sun.sun` state may also tick
forward between calls (the integration updates its `state`
on every elevation/azimuth re-compute) but that's HA's own
internal scheduling, not anything our probe triggered.

The `_SAFE_ATTRIBUTE_KEYS` filter is also a **read-side**
operation (post-response, in our Python process). It cannot
mutate HA.

## 7. Forensic state at end of C-6a

| Item | Value |
|---|---|
| `webui.db.tool.ha_get_state.content` | unchanged (14 982 chars, 1 spec) |
| `webui.db.tool.ha_call_service.content` | unchanged (18 494 chars, 1 spec) |
| qwen2.5 `meta.toolIds` | `["time_now","rag_search","audit_search","ha_get_state","ha_call_service"]` — unchanged from C-4 |
| qwen2.5 `base_model_id` | `NULL` (D-35) — unchanged |
| qwen2.5 `params.system` length | 3 342 chars — unchanged |
| qwen2.5 `updated_at` | `1781623953` (C-4 timestamp; not touched this turn) |
| llama3* rows | unchanged — D-20 holds |
| `amarolab-audit.log` line count | 121 (delta vs pre-probe = **+1**) |
| `amarolab-audit.log` MD5 | `647cdad6487757f59d625dcf6c8d5774` |
| Total `result_code: "ok"` lines in audit log | (prior 4 + this 1 = 5; pre-Phase-C: `time_now`, `audit_search` x 2, plus `time_now` after Issue T remediation; Phase B/A baseline preserved) |
| `openwebui` container | running healthy; uptime ≈ 3 h 22 min (StartedAt `2026-06-16T12:35:59Z` from G-Cpre Attempt 2; no restart this turn) |
| `qdrant` container | running healthy (untouched) |
| HA env passthrough | alive in `openwebui` (`HA_BASE_URL` len 26, `HA_LLAT` len 183) — consumed by this probe at `_init()` |
| Probe sub-interpreter `Tools._httpx_client` | non-None (Client constructed) |
| Probe sub-interpreter `Tools._bearer` | non-None (length 190 = `"Bearer "` + LLAT) |
| Probe sub-interpreter `Tools._base_url` | non-None (length 26 = matches `.env` `HA_BASE_URL`) |
| `httpx` module in probe sub-interpreter | loaded |
| Probe artefacts | `/tmp/hgs_runtime.py` on host (MD5 `4cad688fd82b65ccd8d2ca23ea6dc474`); `/tmp/hgs_runtime.py` in container (same MD5) — both are tmpfs / next-reboot cleanup |
| HA-side state | `sun.sun` unchanged; HA `/api/states/sun.sun` GET recorded in HA logs (user-verifiable) |

## 8. What this log deliberately did NOT do

- **Did not call `ha_call_service`.** The write Tool's runtime
  was not exercised this turn. C-5 already proved the
  refusal-path; C-6 (Gate G-5) will exercise the happy-path
  via a real chat dispatch when the user approves.
- **Did not change any HA state.** Read-only GET; HA's
  `sun.sun` state may have ticked forward in HA's own
  scheduler but not because of this probe.
- **Did not exercise the live-chat / prompt-routing path.**
  This probe used `docker exec` to load the installed runtime
  source directly via `importlib`; it did not go through
  `/api/chat/completions` or trigger any prompt-level
  decision. The user can chat the equivalent question
  ("what's the state of sun.sun?") through the OWUI browser
  UI as a follow-up if desired — separate test, separate
  audit-log line.
- **Did not log the LLAT or any secret value.** §3.6 + §4.2
  establish this end-to-end.
- **Did not modify `webui.db`.** No SQL UPDATE / INSERT /
  DELETE.
- **Did not modify `.env`.** No secret rotation.
- **Did not modify any Tool row.** All 8 rows byte-identical.
- **Did not recreate, restart, or otherwise disturb the
  `openwebui` or `qdrant` containers.** Uptime preserved.
- **Did not commit anything.** Per the user's instruction
  ("Stop after validation and git status").

## 9. Recommended next step

C-5 + C-6a together cover the load-bearing safety + read-path
proofs. The remaining Phase C item per the readiness review
§11 + Phase B closeout §6.3 is the **happy-path write**:

1. **C-6 (user-driven; Gate G-5) — write happy path.** Chat
   `"turn on the kitchen light"` (or any allowlisted
   `light.turn_on` / `switch.toggle` against a real entity
   the user has at home), observe both the physical state
   change *and* the audit-log delta with
   `tool: "ha_call_service"`, `args.domain: "light"`,
   `args.service: "turn_on"`, `allowed: true`,
   `result_code: "ok"`, `duration_ms` ≤ ~1500 ms (warm) or
   ≤ ~3 000 ms (cold).
2. **C-7** — docs sync (CURRENT_STATE / ROADMAP /
   AMAROLAB_HANDOFF) + git commit + Phase D hand-off note.

If the user wants to commit C-6a first, the natural
commit-message form is:

```
test(amarolab): first real HA read via ha_get_state(sun.sun) (C-6a)

- In-container probe against the installed runtime source
  (extracted directly from webui.db.tool.content, MD5
  4cad688fd82b65ccd8d2ca23ea6dc474). Call signature
  ha_get_state(entity_id="sun.sun") returned result_code=ok,
  state="above_horizon", friendly_name="Sun", duration_ms=83
  (cold). attributes={} because sun.* attributes are not in
  the _SAFE_ATTRIBUTE_KEYS allowlist (working as designed).
- _init() fired (httpx imported, HA_BASE_URL + HA_LLAT read
  from os.environ, httpx.Client constructed, Bearer header
  assembled). Class-level state: _httpx_client non-None,
  _bearer length 190, _base_url length 26, httpx loaded.
  LLAT value never printed — lengths only.
- Audit-log delta = +1; new line shape:
  {tool=ha_get_state, args={entity_id:"sun.sun"},
   allowed=true, result_code=ok, duration_ms=83}.
  Secret-shape sweep on the new line: 0 across
  Bearer/64-hex/JWT patterns. HA_LLAT not in audit log.
- D-35 preserved (qwen2.5 base_model_id NULL); D-20
  preserved (llama3* rows untouched); meta.toolIds 5-list
  intact from C-4; params.system 3 342 chars unchanged.
- 09_logs/2026-06-17_phaseC_ha_get_state_real_validation.md
  — this log; full probe execution; LLAT-handling proofs;
  HA-side derivative observations; forensic state.
```

## 10. Cross-references

- C-5 closeout (refusal validation against installed
  runtime source — companion to this log):
  [`2026-06-17_phaseC_refusal_validation_applied.md`](2026-06-17_phaseC_refusal_validation_applied.md)
- C-4 closeout (toolIds extension that made `ha_get_state`
  addressable):
  [`2026-06-17_phaseC_gate_g4_applied.md`](2026-06-17_phaseC_gate_g4_applied.md)
- C-3 install:
  [`2026-06-17_phaseC_tool_install_applied.md`](2026-06-17_phaseC_tool_install_applied.md)
- C-1 design (the read-Tool contract, allowlist rationale,
  LLAT defense-in-depth):
  [`2026-06-17_phaseC_ha_get_state_design.md`](2026-06-17_phaseC_ha_get_state_design.md)
- G-Cpre closure (env passthrough prerequisite, consumed by
  `_init()` this turn):
  [`2026-06-17_phaseC_secret_rotation_and_gcpre_applied.md`](2026-06-17_phaseC_secret_rotation_and_gcpre_applied.md)
- Phase C readiness review (validation matrix C-aux1 +
  C-aux4):
  [`2026-06-17_phaseC_readiness_review.md`](2026-06-17_phaseC_readiness_review.md)
- Phase B B-8 precedent (in-container probe against
  installed runtime source):
  [`2026-06-16_phaseB_validation_applied.md`](2026-06-16_phaseB_validation_applied.md)
  §3
- Phase B closeout §6.3 step 5 + step 10 (Phase C exit
  spec):
  [`2026-06-16_phaseB_closeout.md`](2026-06-16_phaseB_closeout.md)
- Audit helper (the `_audit(...)` shape the new line
  conforms to):
  [`../ai-stack/openwebui-tools/lib/audit_helper.py`](../ai-stack/openwebui-tools/lib/audit_helper.py)
- Sub-project live state (to be refreshed at C-7, not this
  turn):
  [`../04_ai_system/amarolab-v1/CURRENT_STATE.md`](../04_ai_system/amarolab-v1/CURRENT_STATE.md),
  [`../04_ai_system/amarolab-v1/ROADMAP.md`](../04_ai_system/amarolab-v1/ROADMAP.md),
  [`../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md`](../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md)

## 11. Stop point

Per the user's instruction
("Stop after validation and git status."): this log is the
artefact. **Phase C C-6a is APPLIED.** The first real HA
read returned the contract-shaped JSON with
`result_code="ok"`; `HA_LLAT` is preserved in `.env` and
in-process memory only; all model-row invariants hold. C-6
(Gate G-5 — write happy path) awaits explicit user
instruction.
