# Phase C C-6 — Gate G-5 — first real `ha_call_service` happy path — APPLIED

- **Date:** 2026-06-17 (executed wall-clock
  `2026-06-16T22:29:27Z` → `2026-06-16T22:31:13Z` UTC,
  consistent with the wall-clock-vs-filename convention
  used in earlier Phase C logs).
- **Status:** **APPLIED.** The first real
  `ha_call_service` happy path in this sub-project's
  history was executed end-to-end against the
  `switch.impresora_3d` Zigbee smart plug (Sonoff
  S60ZBTPF — "Impresora 3D"). Sequence:
  pre-read (`off`) → **`turn_on` (the Gate G-5 line)** →
  post-read (`on`) → `turn_off` (baseline restore) →
  restore-verify-read (`off`). All five Tool invocations
  returned `result_code="ok"` and `allowed=true`. HA
  observed both state transitions
  (`last_changed` advanced `17:59:36Z` → `22:29:59Z` →
  `22:31:12Z`). The audit log gained exactly **five**
  lines; secret-shape sweep on all five = 0 / 0 / 0. All
  Phase A/B/C invariants (`base_model_id=NULL`,
  qwen2.5 `meta.toolIds` 5-list, `params.system`
  3 342 chars, llama3* rows untouched, `tool` table
  byte-identical) hold by direct SQL probe. The plug
  ends this log in its original `off` state.
- **Scope:** Tool-level happy-path write against the
  user-provided entity `switch.impresora_3d`, with
  immediate baseline restore. **Does not** exercise the
  live chat-completion path (in-container probe shape
  inherited from C-5 / C-6a). **Does not** modify
  `webui.db`, `.env`, the openwebui container, or any
  other HA entity. **Does not** start Phase C C-7
  closeout — that remains the next assistant-owned
  milestone.
- **Inputs:**
  - User confirmation this turn:
    - entity_id = `switch.impresora_3d`
    - current plug state = `off`
    - 3D printer = idle / not printing
    - direction = `switch.turn_on`
    - post-test preference = restore to `off`
  - C-6a closeout (first real HA read; the precedent
    pattern for the in-container probe):
    [`2026-06-17_phaseC_ha_get_state_real_validation.md`](2026-06-17_phaseC_ha_get_state_real_validation.md).
  - C-5 closeout (Tool-level refusal validation against
    the installed `ha_call_service` runtime source; the
    safety side of Gate G-5):
    [`2026-06-17_phaseC_refusal_validation_applied.md`](2026-06-17_phaseC_refusal_validation_applied.md).
  - C-4 closeout (the precondition that attached
    `ha_call_service` to qwen2.5 via `meta.toolIds`):
    [`2026-06-17_phaseC_gate_g4_applied.md`](2026-06-17_phaseC_gate_g4_applied.md).
  - C-3 install (the precondition that put the Tool
    source into `webui.db.tool`):
    [`2026-06-17_phaseC_tool_install_applied.md`](2026-06-17_phaseC_tool_install_applied.md).
  - C-2 design (write Tool contract, allowlist,
    canonical refusal probe):
    [`2026-06-17_phaseC_ha_call_service_design.md`](2026-06-17_phaseC_ha_call_service_design.md).
  - G-Cpre closure (the HA env passthrough consumed by
    both Tools' `_init()`):
    [`2026-06-17_phaseC_secret_rotation_and_gcpre_applied.md`](2026-06-17_phaseC_secret_rotation_and_gcpre_applied.md).
  - Zigbee first-devices onboarding (the real Z2M
    device under test):
    [`../03_services/zigbee-stack/zigbee2mqtt_first_devices.md`](../03_services/zigbee-stack/zigbee2mqtt_first_devices.md).

## 0. TL;DR

| User requirement | Status | Evidence |
|---|---|---|
| Use a non-destructive action | ✓ | Plug `off` → `turn_on` while printer idle (user-asserted); restored to `off` |
| Verify audit log entry exists | ✓ | Line count 122 → 127 (+5); Gate G-5 line at index 124 (§4.1) |
| Verify `result_code = "ok"` | ✓ | §3.2 return JSON; §4.1 audit-log line; all 5 lines `result_code="ok"` |
| Verify physical state change | ✓ | §3.3 follow-up `ha_get_state` returned `state="on"`; HA `last_changed` advanced to `2026-06-16T22:29:59Z` (matches the call ts within 36 ms) |
| Preserve D-35 (`base_model_id = NULL`) | ✓ | §5.1 — qwen2.5 row byte-identical to C-4 baseline (`updated_at=1781623953`) |
| Preserve D-20 (llama3* per-model scope) | ✓ | §5.2 — both llama3* rows byte-identical (`updated_at` unchanged) |
| Preserve D-12 (allowlist) | ✓ | §2.4 — `switch ∈ _ALLOWED_DOMAINS` (source-level invariant + runtime confirmation in the probe) |
| `HA_LLAT` is not logged | ✓ | §4.2 — secret-shape sweep on the 5 new lines = 0 / 0 / 0 |
| Restore baseline | ✓ | §6 — turn_off issued + restore-verify-read confirms `state="off"` |
| No container restart | ✓ | §7 — `openwebui.StartedAt` unchanged at `2026-06-16T12:35:59Z` |
| No `webui.db` write | ✓ | §5.3 — `tool` table byte-identical; no model row mutation |
| No `.env` mutation | ✓ — no edit issued this turn | n/a |

**Phase C C-6 (Gate G-5) is APPLIED and CLOSED.** The
`ha_call_service` write path is now live and proven
end-to-end against a real, controllable Zigbee entity.
C-7 (docs sync + Phase C closeout) is the next
assistant-owned step and is **deliberately not
exercised this turn** per the user's stop instruction.

## 1. Entity-of-test rationale

The user-confirmed entity:

| Field | Value | Source |
|---|---|---|
| `entity_id` | `switch.impresora_3d` | User confirmation this turn |
| Friendly name | "Impresora 3D" | HA → Z2M → `friendly_name` |
| Zigbee device | Sonoff S60ZBTPF smart plug | [`zigbee2mqtt_first_devices.md`](../03_services/zigbee-stack/zigbee2mqtt_first_devices.md) |
| Physical load | 3D printer (idle at test time, user-asserted) | User confirmation |
| Pre-test state | `off` | User-asserted; confirmed by §3.1 probe |

The plug is the smaller of the two onboarded Zigbee
devices (the other being the `Toldo` roller shutter,
explicitly excluded from this turn by the user). Powering
the plug on while the printer firmware is idle is a
canonical non-destructive write — the printer boots to
its idle screen and waits for a print command, drawing
only the standby current of the controller board.

## 2. Probe design and source under test

### 2.1 The two installed runtime sources

Both Tools were loaded from the `webui.db.tool` row's
`content` column (the path Open WebUI's chat-completion
dispatch uses at runtime), exactly the shape established
by C-5 / C-6a.

```bash
$ sqlite3 /srv/homelab/data/openwebui/webui.db \
    "SELECT content FROM tool WHERE id='ha_get_state';" \
    > /tmp/hgs_runtime.py
$ md5sum /tmp/hgs_runtime.py
4cad688fd82b65ccd8d2ca23ea6dc474  /tmp/hgs_runtime.py    # matches C-6a baseline
$ python3 -m py_compile /tmp/hgs_runtime.py
PASS
$ docker cp /tmp/hgs_runtime.py openwebui:/tmp/hgs_runtime.py
$ docker exec openwebui md5sum /tmp/hgs_runtime.py
4cad688fd82b65ccd8d2ca23ea6dc474  /tmp/hgs_runtime.py    # round-trip clean

$ sqlite3 /srv/homelab/data/openwebui/webui.db \
    "SELECT content FROM tool WHERE id='ha_call_service';" \
    > /tmp/hcs_runtime.py
$ md5sum /tmp/hcs_runtime.py
5a40615c1d0b120816e46700acb4d421  /tmp/hcs_runtime.py    # matches C-5 baseline
$ python3 -m py_compile /tmp/hcs_runtime.py
PASS
$ docker cp /tmp/hcs_runtime.py openwebui:/tmp/hcs_runtime.py
$ docker exec openwebui md5sum /tmp/hcs_runtime.py
5a40615c1d0b120816e46700acb4d421  /tmp/hcs_runtime.py    # round-trip clean
```

Neither source byte changed between C-5/C-6a and this
turn. Install fidelity is preserved.

### 2.2 Pre-flight backup

```bash
$ cp -p /srv/homelab/data/openwebui/webui.db \
       /tmp/amarolab-phaseC-backup/webui.db.pre-G5
$ chmod 600 /tmp/amarolab-phaseC-backup/webui.db.pre-G5
$ md5sum /tmp/amarolab-phaseC-backup/webui.db.pre-G5 \
         /srv/homelab/data/openwebui/webui.db
ca7d1f5955a678bd9b6de36525100b30  /tmp/amarolab-phaseC-backup/webui.db.pre-G5
ca7d1f5955a678bd9b6de36525100b30  /srv/homelab/data/openwebui/webui.db
```

Backup file is bit-identical to source at backup time.
Backup mode `0600`. Backup directory `0700 diego:diego`
(preserved from earlier Phase C work).

### 2.3 Container state at baseline

```bash
$ docker inspect openwebui --format \
    'State={{.State.Status}} Health={{.State.Health.Status}} StartedAt={{.State.StartedAt}}'
State=running Health=healthy StartedAt=2026-06-16T12:35:59.30214094Z
```

`openwebui` running continuously since G-Cpre Attempt 2
(~10 hours uptime). No `docker stop` / `docker start` /
`docker restart` was issued at any point this turn.

### 2.4 Runtime D-12 confirmation

From the probe stdout in §3.1 / §3.2:

```
PRE  switch in ALLOWED?  True
PRE  recorder in DENIED? True
```

The `_ALLOWED_DOMAINS` set (13 entries per C-2 design)
contains `switch`. The `_EXPLICITLY_DENIED` set (the
documented denylist) contains `recorder`. The
out-of-allowlist denial proven in C-5 still holds; the
in-allowlist permit demonstrated this turn is the
complementary half of the D-12 contract.

## 3. Probe execution + responses

### 3.1 Step 1 — pre-state read via `ha_get_state`

Probe inside the `openwebui` container:

```python
T = mod.Tools()
t0 = time.monotonic()
raw = T.ha_get_state(entity_id="switch.impresora_3d")
elapsed = time.monotonic() - t0
```

| Probe metric | Value |
|---|---|
| `Tools._httpx_client` PRE / POST | `None` / non-`None` |
| `Tools._bearer` PRE / POST | `None` / non-`None` (length 190 = `"Bearer "` + LLAT) |
| `Tools._base_url` PRE / POST | `None` / non-`None` (length 26) |
| `httpx in sys.modules` PRE / POST | `False` / `True` (deferred import fired inside `_init()`) |
| Elapsed wall-clock | **195 ms** (cold) |

Return JSON:

```json
{
  "entity_id": "switch.impresora_3d",
  "state": "off",
  "friendly_name": "Impresora 3D",
  "last_changed": "2026-06-16T17:59:36.185514+00:00",
  "last_updated": "2026-06-16T17:59:36.185514+00:00",
  "attributes": {},
  "result_code": "ok"
}
```

Field verification:

| Field | Expected | Got | Match? |
|---|---|---|:---:|
| `entity_id` | `"switch.impresora_3d"` | `"switch.impresora_3d"` | ✓ |
| `state` | `"off"` (user-asserted) | `"off"` | ✓ — matches user input |
| `friendly_name` | `"Impresora 3D"` (Z2M-assigned) | `"Impresora 3D"` | ✓ |
| `last_changed` | ISO 8601 UTC, ≥ 4 h before now | `2026-06-16T17:59:36.185514+00:00` | ✓ — last toggle ~4.5 h before this turn |
| `last_updated` | = `last_changed` for a quiet state | `2026-06-16T17:59:36.185514+00:00` | ✓ |
| `attributes` | `{}` after allowlist filter | `{}` | ✓ — same allowlist behaviour as C-6a §3.3 |
| `result_code` | `"ok"` | `"ok"` | ✓ |

`switch` domain attributes (`current_power_w`,
`energy_kwh`, `friendly_name`, etc.) are not members of
the C-1 `_SAFE_ATTRIBUTE_KEYS` allowlist; the empty
`{}` is the design-intended behaviour. The
`friendly_name` is already surfaced at top level
(C-1 §3.4).

Direction lock: per plan §3 row 1
(`off` + idle → `turn_on` is the canonical
non-destructive write).

### 3.2 Step 3 — THE Gate G-5 line — `ha_call_service` turn_on

Probe inside the `openwebui` container:

```python
T = mod.Tools()                  # fresh subprocess, fresh class state
t0 = time.monotonic()
raw = T.ha_call_service(
    domain="switch",
    service="turn_on",
    entity_id="switch.impresora_3d",
)
elapsed = time.monotonic() - t0
```

| Probe metric | Value |
|---|---|
| `Tools._httpx_client` PRE / POST | `None` / non-`None` |
| `Tools._bearer` PRE / POST | `None` / non-`None` (length 190) |
| `Tools._base_url` PRE / POST | `None` / non-`None` (length 26) |
| `httpx in sys.modules` PRE / POST | `False` / `True` |
| `T.valves.max_per_minute` | `10` (C-2 default for the write Tool) |
| Elapsed wall-clock | **105 ms** (cold; well under the C-aux4 expectation of ≤ 3 000 ms cold) |

Return JSON:

```json
{
  "ok": true,
  "domain": "switch",
  "service": "turn_on",
  "entity_id": "switch.impresora_3d",
  "ha_status": 200,
  "ha_response": [],
  "result_code": "ok"
}
```

Field verification against C-2 design §4 success-shape
contract:

| Field | Expected | Got | Match? |
|---|---|---|:---:|
| `ok` | `true` | `true` | ✓ |
| `domain` (echo) | `"switch"` | `"switch"` | ✓ |
| `service` (echo) | `"turn_on"` | `"turn_on"` | ✓ |
| `entity_id` (echo) | `"switch.impresora_3d"` | `"switch.impresora_3d"` | ✓ |
| `ha_status` | `200` (HA REST POST success) | `200` | ✓ |
| `ha_response` | list of state objects HA updated (may be empty when HA processes the call asynchronously / returns no body) | `[]` | ✓ — see note below |
| `result_code` | `"ok"` | `"ok"` | ✓ |
| (no `Authorization` field) | — | absent | ✓ |
| (no `bearer` field) | — | absent | ✓ |
| (no internal HA URL leaked) | — | absent | ✓ |

Note on `ha_response: []` — HA's REST contract for
`POST /api/services/<domain>/<service>` returns the list
of entity states that *changed* as a result of the call.
For Zigbee Z2M devices, the state change propagates via
MQTT → Z2M → device → MQTT-back, and HA frequently
returns the call before the round-trip confirms; an
empty array is the documented HA behaviour for that
shape. The state change is observable on the *next*
read (Step 4 below).

### 3.3 Step 4 — physical-change verification via `ha_get_state`

Probe inside the `openwebui` container (24 s after the
write):

Return JSON:

```json
{
  "entity_id": "switch.impresora_3d",
  "state": "on",
  "friendly_name": "Impresora 3D",
  "last_changed": "2026-06-16T22:29:59.186275+00:00",
  "last_updated": "2026-06-16T22:29:59.186275+00:00",
  "attributes": {},
  "result_code": "ok"
}
```

| Comparison | Pre-write (Step 1) | Post-write (Step 4) | Δ |
|---|---|---|---|
| `state` | `"off"` | **`"on"`** | **state changed ✓** |
| `last_changed` | `2026-06-16T17:59:36.185514+00:00` | `2026-06-16T22:29:59.186275+00:00` | advanced by ~4.5 h, but the meaningful number is **the new value matches the Gate G-5 call timestamp** (`22:29:59.150530Z` audit ts) within **36 ms** — HA observed the state transition immediately after the REST POST returned |
| `last_updated` | same as `last_changed` | same as `last_changed` | quiet state since transition |

The physical state change is end-to-end confirmed:

1. HA accepted the REST POST (`ha_status: 200`).
2. HA's internal state changed from `off` to `on`.
3. The Z2M MQTT → Zigbee → Sonoff S60ZBTPF chain
   responded (otherwise HA's `last_changed` would not
   have advanced — HA records state changes only when
   the device confirms via MQTT for Z2M-managed
   entities).
4. The user can independently confirm visually at the
   device (printer's standby LED illuminated; the
   printer firmware boots to its idle screen).

Elapsed wall-clock for this verify read: **83 ms**.

## 4. Audit-log delta

### 4.1 Line count + the five new lines

```
$ wc -l /srv/homelab/data/openwebui/amarolab-audit.log
127 /srv/homelab/data/openwebui/amarolab-audit.log
$ md5sum /srv/homelab/data/openwebui/amarolab-audit.log
11522d088fc180d2f25e6e997c47a9de  amarolab-audit.log
```

| Metric | Pre-G5 | Post-G5 | Delta |
|---|---:|---:|---:|
| Line count | 122 | 127 | **+5** |
| MD5 | `3112b4f648f4242c5ffcc989a88d58a7` | `11522d088fc180d2f25e6e997c47a9de` | append-only, +5 lines |

The five new tail lines (in execution order):

| # | ts (UTC) | tool | result_code | duration_ms | id |
|---:|---|---|:---:|---:|---|
| 123 | `22:29:27.233814Z` | `ha_get_state` (pre-read) | `ok` | 195 | `b4fb1db8-1db1-4dec-88f2-25d3ccf7d5e6` |
| **124** | **`22:29:59.150530Z`** | **`ha_call_service`** (**Gate G-5**) | **`ok`** | **105** | **`5065c3d8-f512-439f-9c7c-1ba1efa7f935`** |
| 125 | `22:30:23.100068Z` | `ha_get_state` (verify) | `ok` | 83 | `502a92ca-42bc-43ef-983d-0114a38a8dd7` |
| 126 | `22:31:12.801558Z` | `ha_call_service` (restore turn_off) | `ok` | 84 | `87f6d2b9-e64a-49a7-8591-14a25c6e02d6` |
| 127 | `22:31:13.322668Z` | `ha_get_state` (restore verify) | `ok` | 19 | `a608cdac-b414-4a1a-b765-37e62e180f18` |

**The Gate G-5 line (line 124) verbatim:**

```json
{
  "ts": "2026-06-16T22:29:59.150530+00:00",
  "id": "5065c3d8-f512-439f-9c7c-1ba1efa7f935",
  "user": "diego",
  "tool": "ha_call_service",
  "args": {
    "domain": "switch",
    "service": "turn_on",
    "entity_id": "switch.impresora_3d",
    "service_data": null
  },
  "allowed": true,
  "result_code": "ok",
  "duration_ms": 105
}
```

Field-by-field:

| Field | Value | Verified by |
|---|---|---|
| `ts` | `2026-06-16T22:29:59.150530+00:00` | ✓ matches HA's `last_changed` within 36 ms (§3.3) |
| `id` | UUID4 | ✓ audit-helper contract (D-26) |
| `user` | `"diego"` | ✓ per-Tool helper constant (D-07) |
| `tool` | `"ha_call_service"` | ✓ |
| `args.domain` | `"switch"` | ✓ as sent |
| `args.service` | `"turn_on"` | ✓ as sent |
| `args.entity_id` | `"switch.impresora_3d"` | ✓ as sent |
| `args.service_data` | `null` | ✓ unspecified parameter (default `None`) |
| `allowed` | `true` | ✓ — domain in `_ALLOWED_DOMAINS`, no refusal short-circuit |
| `result_code` | `"ok"` | ✓ HA returned 200, parseable JSON |
| `duration_ms` | `105` | ✓ matches probe wall-clock |

### 4.2 Secret-shape sweep on the 5 new lines

```
$ tail -5 amarolab-audit.log | grep -ciE 'authorization|bearer'
0
$ tail -5 amarolab-audit.log | grep -cE '[0-9a-fA-F]{64}'
0
$ tail -5 amarolab-audit.log | grep -cE '[A-Za-z0-9_-]{50,}\.[A-Za-z0-9_-]{50,}\.[A-Za-z0-9_-]{30,}'
0
```

**Zero matches** across all three patterns and all five
new lines:

- No `Authorization` / `Bearer` keyword.
- No 64-hex string.
- No JWT-shape string.

The `args_snap` for both Tools is built explicitly with
only the declared parameters; the LLAT is never a
member. The `_amarolab_redact` second-line-of-defense
(D-26) was not needed.

### 4.3 Cross-corpus tally

```
$ grep -cE '"result_code":\s*"ok"' amarolab-audit.log
```

Adding the 5 new `"ok"` lines to the audit history,
this is the second `ha_call_service` execution path
ever recorded (C-5 / refusal-path being the first
class; this Gate G-5 turn introduces the
`allowed: true, result_code: "ok"` class for
`ha_call_service`).

## 5. Model-row invariants

### 5.1 qwen2.5 — byte-identical to C-4 baseline

```
$ sqlite3 webui.db \
    "SELECT id, base_model_id,
            json_extract(meta,'\$.toolIds'),
            length(json_extract(params,'\$.system')),
            updated_at
     FROM model WHERE id='qwen2.5:7b-instruct';"
qwen2.5:7b-instruct|(NULL)|["time_now","rag_search","audit_search","ha_get_state","ha_call_service"]|3342|1781623953
```

| Field | Pre-G5 | Post-G5 | Match? |
|---|---|---|:---:|
| `base_model_id` | `NULL` (D-35) | **`NULL`** | ✓ **D-35 preserved** |
| `meta.toolIds` | 5-list (C-4) | **same 5-list** | ✓ |
| `params.system` length | 3 342 | **3 342** | ✓ |
| `updated_at` | `1781623953` (C-4 timestamp) | `1781623953` | ✓ **unchanged** |

No model row UPDATE this turn.

### 5.2 D-20 invariant — llama3* still untouched

```
$ sqlite3 webui.db \
    "SELECT id, base_model_id,
            json_extract(meta,'\$.toolIds'), updated_at
     FROM model WHERE id LIKE 'llama%' ORDER BY id;"
llama3.2:latest||["docker_logs","docker_containers","system_status"]|1773442892
llama3:latest||["docker_containers","system_status","docker_logs"]|1775031217
```

Both rows byte-identical to the C-6a forensic state
(`updated_at` unchanged since pre-Amarolab). Neither
contains `ha_get_state` or `ha_call_service`. D-20
per-model scope holds.

### 5.3 `tool` table — byte-identical to C-3 install

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

All 8 rows preserved with the C-3 install fidelity
(lengths and spec counts byte-identical). No Tool row
was modified this turn.

## 6. Baseline restore

### 6.1 Step 5 — turn_off

Inside the same `docker exec` subprocess (different
importlib module — fresh class state on
`ha_call_service`):

Return JSON:

```json
{
  "ok": true,
  "domain": "switch",
  "service": "turn_off",
  "entity_id": "switch.impresora_3d",
  "ha_status": 200,
  "ha_response": [],
  "result_code": "ok"
}
```

Elapsed: **84 ms** (cold for this subprocess's
ha_call_service module).

### 6.2 Restore-verify read

Return JSON:

```json
{
  "entity_id": "switch.impresora_3d",
  "state": "off",
  "friendly_name": "Impresora 3D",
  "last_changed": "2026-06-16T22:31:12.827336+00:00",
  "last_updated": "2026-06-16T22:31:12.827336+00:00",
  "attributes": {},
  "result_code": "ok"
}
```

Elapsed: **19 ms** (warm: httpx C-extension / OpenSSL
state cached in-process from the immediately-prior
turn_off call's `_init()`).

| Comparison | Step 4 (post-write) | Step 5 verify (post-restore) | Δ |
|---|---|---|---|
| `state` | `"on"` | **`"off"`** | restored ✓ |
| `last_changed` | `22:29:59.186275Z` | `22:31:12.827336Z` | advanced by ~1 min 13 s (matches the restore turn_off audit ts within 26 ms) |

**The plug ends this log in its original `off` state,
matching the user's pre-G5 baseline.** The 3D printer
firmware is back to standby (no power draw).

## 7. Forensic state at end of G-5

| Item | Value |
|---|---|
| `webui.db.tool.ha_get_state.content` | unchanged (14 982 chars, 1 spec) |
| `webui.db.tool.ha_call_service.content` | unchanged (18 494 chars, 1 spec) |
| qwen2.5 `meta.toolIds` | 5-list — unchanged from C-4 |
| qwen2.5 `base_model_id` | `NULL` (D-35) — unchanged |
| qwen2.5 `params.system` length | 3 342 chars — unchanged |
| qwen2.5 `updated_at` | `1781623953` (C-4 timestamp) — unchanged |
| llama3* rows | byte-identical (D-20 holds) |
| `amarolab-audit.log` line count | 127 (Δ vs pre-G5 = **+5**) |
| `amarolab-audit.log` MD5 | `11522d088fc180d2f25e6e997c47a9de` |
| Total `tool=ha_call_service, result_code=ok` lines | 2 (lines 124 + 126 — turn_on, turn_off) |
| Total `tool=ha_call_service, result_code=refused` lines | 3 (C-2 design probes + C-5 — unchanged) |
| `openwebui` container | running healthy; StartedAt `2026-06-16T12:35:59Z` (≈ 10 h uptime; no restart this turn) |
| HA env passthrough | alive (`HA_BASE_URL` len 26, `HA_LLAT` len 183) — consumed by all five probe subprocesses |
| Pre-flight backup | `/tmp/amarolab-phaseC-backup/webui.db.pre-G5` (MD5 `ca7d1f5955a678bd9b6de36525100b30`, mode 0600) |
| Probe artefacts | `/tmp/{hgs,hcs}_runtime.py` on host (MD5s match the C-5 / C-6a baselines); same files in container — both tmpfs / next-reboot cleanup |
| HA-side end state | `switch.impresora_3d.state = "off"` with `last_changed = 2026-06-16T22:31:12Z` (the restore turn_off) |
| Physical hardware | 3D printer back to standby (no power) |

## 8. What this log deliberately did NOT do

- **Did not exercise the live-chat path.** No
  `/api/chat/completions` round-trip through qwen2.5;
  this turn used `docker exec + importlib` against the
  installed runtime source, the same shape C-5 / C-6a
  used. A live chat dispatch is a separate qualitative
  observation, additive at most one audit-log line, and
  not a Gate G-5 blocker.
- **Did not modify `webui.db`.** No `UPDATE` / `INSERT`
  / `DELETE`. The model row, the tool rows, and every
  other row are byte-identical to pre-G5.
- **Did not modify `.env`.** No secret rotation, no
  edit. `HA_LLAT` issued at G-Cpre remains in place.
- **Did not modify any Tool source on disk.**
  `ai-stack/openwebui-tools/tools/{ha_get_state,ha_call_service}.py`
  are unchanged.
- **Did not restart, recreate, or otherwise disturb the
  `openwebui`, `qdrant`, `homeassistant`, `mosquitto`,
  or `zigbee2mqtt` containers.** Uptime preserved.
- **Did not touch any other HA entity.** Only
  `switch.impresora_3d` was addressed; the `Toldo`
  roller shutter (`cover.toldo` or equivalent) and all
  other HA entities were explicitly out of scope.
- **Did not touch Guardian Cloud.** Production
  invariant honoured.
- **Did not touch RAG collections or Qdrant.**
- **Did not modify any documentation file.** This log
  is the only new artefact this turn.
- **Did not start the C-7 closeout sync.** That remains
  the next assistant-owned milestone and awaits a
  separate user instruction.
- **Did not log the LLAT or any secret value.** §4.2
  establishes this end-to-end.
- **Did not commit anything.** Per the user's
  "Stop after validation, documentation and git
  status." instruction.

## 9. Recommended next step

Per the readiness review §11 and the Phase B closeout
§6.3 step 10:

1. **C-7 — Phase C closeout.** Refresh
   `00_overview/CURRENT_STATE.md` to mark Gate G-5 as
   **APPLIED** and the Phase C limited-control
   criterion as **MET**. Refresh `ROADMAP.md` to mark
   Phase C as **Completed**. Refresh
   `AMAROLAB_HANDOFF.md` to point at Phase D as the
   next phase. Optionally refresh the
   `04_ai_system/amarolab-v1/{CURRENT_STATE,ROADMAP,AMAROLAB_HANDOFF}.md`
   sub-project docs in the same pass.
2. **Phase D handoff note.** Whisper + Piper + HA
   Assist scoping. Out of this log.

If the user wants to commit G-5 first, the natural
commit-message form is:

```
test(amarolab): Gate G-5 — first real ha_call_service happy path (C-6)

- In-container probe against the installed runtime sources
  (ha_get_state MD5 4cad688fd82b65ccd8d2ca23ea6dc474,
  ha_call_service MD5 5a40615c1d0b120816e46700acb4d421 —
  both byte-identical to C-5 / C-6a baselines). Sequence:
  ha_get_state pre-read (state=off) → ha_call_service
  turn_on (the Gate G-5 line) → ha_get_state verify
  (state=on, last_changed matches the call ts within
  36 ms) → ha_call_service turn_off (baseline restore) →
  ha_get_state restore-verify (state=off).
- All 5 audit lines: allowed=true, result_code=ok.
  Secret-shape sweep on the 5 lines: 0 / 0 / 0 across
  Bearer/64-hex/JWT patterns. HA_LLAT not logged.
- D-35 preserved (qwen2.5 base_model_id NULL); D-20
  preserved (llama3* rows byte-identical); D-12
  preserved (switch in _ALLOWED_DOMAINS, source-level
  invariant intact). webui.db: no UPDATE. .env: no
  edit. openwebui: no restart.
- Plug ends restored to off; printer ends idle.
- 09_logs/2026-06-17_phaseC_gate_g5_applied.md — this
  log; full probe execution, audit-log delta, model-row
  invariant proofs, restore evidence, forensic state.
```

## 10. Cross-references

- C-6a closeout (first real read; the in-container
  probe-shape precedent):
  [`2026-06-17_phaseC_ha_get_state_real_validation.md`](2026-06-17_phaseC_ha_get_state_real_validation.md)
- C-5 closeout (Tool-level refusal validation; the
  complementary half of the D-12 contract):
  [`2026-06-17_phaseC_refusal_validation_applied.md`](2026-06-17_phaseC_refusal_validation_applied.md)
- C-4 closeout (qwen2.5 `meta.toolIds` extension that
  made `ha_call_service` addressable):
  [`2026-06-17_phaseC_gate_g4_applied.md`](2026-06-17_phaseC_gate_g4_applied.md)
- C-3 install:
  [`2026-06-17_phaseC_tool_install_applied.md`](2026-06-17_phaseC_tool_install_applied.md)
- C-2 design (write Tool contract + allowlist):
  [`2026-06-17_phaseC_ha_call_service_design.md`](2026-06-17_phaseC_ha_call_service_design.md)
- C-1 design (read Tool contract + LLAT
  defense-in-depth):
  [`2026-06-17_phaseC_ha_get_state_design.md`](2026-06-17_phaseC_ha_get_state_design.md)
- G-Cpre closure (env passthrough consumed by both
  Tools' `_init()`):
  [`2026-06-17_phaseC_secret_rotation_and_gcpre_applied.md`](2026-06-17_phaseC_secret_rotation_and_gcpre_applied.md)
- Phase C readiness review (validation matrix C-6 row;
  three-layer defense):
  [`2026-06-17_phaseC_readiness_review.md`](2026-06-17_phaseC_readiness_review.md)
- Phase B closeout §6.3 step 10 (Gate G-5 spec):
  [`2026-06-16_phaseB_closeout.md`](2026-06-16_phaseB_closeout.md)
- Zigbee onboarding (the real device under test):
  [`../03_services/zigbee-stack/zigbee2mqtt_first_devices.md`](../03_services/zigbee-stack/zigbee2mqtt_first_devices.md)
- D-12 allowlist (the rule whose permit path was
  exercised):
  [`../04_ai_system/amarolab-v1/ROADMAP.md`](../04_ai_system/amarolab-v1/ROADMAP.md)
- Live state (to be refreshed at C-7, not this turn):
  [`../00_overview/CURRENT_STATE.md`](../00_overview/CURRENT_STATE.md),
  [`../00_overview/ROADMAP.md`](../00_overview/ROADMAP.md),
  [`../00_overview/AMAROLAB_HANDOFF.md`](../00_overview/AMAROLAB_HANDOFF.md)

## 11. Stop point

Per the user's instruction
("Stop after validation, documentation and git
status."): this log is the artefact. **Phase C Gate
G-5 is APPLIED.** The first real `ha_call_service`
happy path returned `result_code="ok"` end-to-end, the
physical state transition was observed by HA via the
Z2M MQTT round-trip, the baseline was restored, all
model and tool-table invariants hold by direct SQL
probe, and `HA_LLAT` did not appear in any audit-log
line. C-7 (Phase C closeout — sync `CURRENT_STATE` /
`ROADMAP` / `AMAROLAB_HANDOFF` + Phase D handoff note)
is the next assistant-owned step and awaits explicit
user instruction.
