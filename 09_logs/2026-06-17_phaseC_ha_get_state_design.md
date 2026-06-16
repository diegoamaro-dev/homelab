# Phase C C-1 — `ha_get_state` Tool source (design + local validation)

- **Date:** 2026-06-17.
- **Goal:** author `tools/ha_get_state.py` as the canonical
  version-controlled source for the `ha_get_state` Open WebUI
  Tool — read **one** Home Assistant entity's current state +
  curated attributes via HA's REST API. Mirror the architecture
  of `time_now.py` / `rag_search.py`. Validate locally only —
  no Tool install, no `webui.db` change, no `meta.toolIds`
  extension, no container recreate, no Home Assistant write
  operation. (Read operations to HA are also out of scope this
  turn — local validation deliberately exercises only the
  short-circuit paths that don't invoke `_init()`.)
- **Inputs:**
  [`2026-06-17_phaseC_readiness_review.md`](2026-06-17_phaseC_readiness_review.md)
  §3 (`ha_get_state` design contract);
  [`2026-06-17_phaseC_secret_rotation_and_gcpre_applied.md`](2026-06-17_phaseC_secret_rotation_and_gcpre_applied.md)
  (G-Cpre closure, env passthrough verified);
  [`../04_ai_system/amarolab-v1/04-security-and-permissions.md`](../04_ai_system/amarolab-v1/04-security-and-permissions.md)
  (trust model, T1/T6, audit redaction contract);
  [`../FUNCTIONS_COMPATIBILITY_REPORT.md`](../FUNCTIONS_COMPATIBILITY_REPORT.md)
  §3 / §5 / §7 (D-24 `class Tools`, D-25 install workflow,
  D-26 inline-helper convention);
  the canonical `time_now` Tool at
  [`../ai-stack/openwebui-tools/tools/time_now.py`](../ai-stack/openwebui-tools/tools/time_now.py);
  the Phase B-shaped `rag_search` Tool at
  [`../ai-stack/openwebui-tools/tools/rag_search.py`](../ai-stack/openwebui-tools/tools/rag_search.py);
  the canonical inlined helper at
  [`../ai-stack/openwebui-tools/lib/audit_helper.py`](../ai-stack/openwebui-tools/lib/audit_helper.py).

## 0. TL;DR

**`tools/ha_get_state.py` is on disk, syntax-clean both before
and after install-time inlining, AST-shape compliant with D-24,
and import-loads inside the openwebui container without
invoking `_init()`.** Four `bad_entity_id` validation probes
returned the contract-shaped errors without constructing the
httpx client and without making any HA call. The Tool is not
installed in `webui.db`; C-3 owns that.

| Check | Result |
|---|---|
| `python3 -m py_compile tools/ha_get_state.py` (pre-inline) | **PASS** |
| `bin/install_tool --dry-run tools/ha_get_state.py` | **PASS** — id=`ha_get_state`, name=`Amarolab ha_get_state`, **14 982 chars**, manifest extracted |
| `python3 -m py_compile` on the inlined body | **PASS** (28 references between helper and Tool body resolve) |
| AST shape — `class Tools`, methods=`['__init__','_init','ha_get_state']`, LLM-callable=`['ha_get_state']`, nested `Valves`, args=`['self','entity_id']`, `_SAFE_ATTRIBUTE_KEYS` module-level Assign | **PASS** |
| In-container `importlib.spec_from_file_location` load + `Tools()` instantiation | **PASS** (Valves defaults, `citation=False`, class-level state `None`) |
| Validation path — `ha_get_state(entity_id="x")` (too short) | **PASS** — `bad_entity_id` |
| Validation path — `ha_get_state(entity_id="LIGHT.KITCHEN")` (uppercase) | **PASS** — `bad_entity_id` |
| Validation path — `ha_get_state(entity_id="not_a_valid_id_no_dot")` (no dot) | **PASS** — `bad_entity_id` |
| Validation path — `ha_get_state(entity_id="light.")` (empty object_id) | **PASS** — `bad_entity_id` |
| Class-level `_httpx_client` / `_bearer` after the four probes | **still `None`** — `_init()` was never invoked; no HA call attempted; HA_LLAT was never read from env |
| `webui.db`, `meta.toolIds`, `webui.db` tool table, openwebui container env, Home Assistant | **untouched by C-1** |

## 1. What this Tool is supposed to be

`ha_get_state(entity_id)` is the **single-entity read** Tool
for Home Assistant. The LLM calls it whenever the user asks
the on/off state or a current numeric/string value of a
specific HA entity (e.g., "is the kitchen light on?", "what's
the lounge temperature?"). It returns the entity's `state`
plus `friendly_name` plus `last_changed` plus a curated subset
of `attributes`; HA writes are out of scope (C-2 owns them).

The contract in the Phase C readiness review §3 — input
schema, output shape, error codes, lazy `_init()` pattern,
allowlist + cap on attributes — is honoured verbatim. This log
documents only the runtime shape that wraps that contract.

## 2. Source-of-truth crosswalk

Every behaviour in the file maps to an existing locked
decision or to a Phase C readiness-review proposal explicitly
acknowledged in §11.

| Concern | Source of truth | Implementation site |
|---|---|---|
| Tool runtime contract — `class Tools` with type-hinted methods | **D-24** (FUNCTIONS_COMPATIBILITY_REPORT §3) | `class Tools:` with a single public method `ha_get_state` and a single underscore-prefixed `_init`; `__init__` dunder; underscore-prefixed module-level constants (`_ENTITY_ID_RE`, `_SAFE_ATTRIBUTE_KEYS`, etc.) are not exposed as Tool attributes by OWUI |
| Inline helper marker (no cross-Tool imports) | **D-26** | one line: `# @@AMAROLAB_INLINE:audit_helper@@` near the top, replaced by `bin/install_tool` |
| Source location on disk | **D-23** | `ai-stack/openwebui-tools/tools/ha_get_state.py` (sibling to `rag_search.py`, `audit_search.py`, `time_now.py`) |
| Tool install workflow | **D-25** | `bin/install_tool tools/ha_get_state.py` — gated to C-3; this log does not install |
| Per-model scope | **D-20** | not in the Tool source — handled by `meta.toolIds` on the qwen2.5 Model entry in C-4 (Gate G-4) |
| Trust model — LLM is adversarial; allowlists are file-level constants | **D-06** | `_ENTITY_ID_RE`, `_ENTITY_ID_MIN_LEN`, `_ENTITY_ID_MAX_LEN`, `_SAFE_ATTRIBUTE_KEYS`, `_ATTR_PAYLOAD_CAP` are module-level constants in this file; the regex anchors at both ends; no `eval`, no `subprocess`, no path-from-arg, no shell building from arguments |
| HA token handling | T6 mitigation in [`04-security-and-permissions.md`](../04_ai_system/amarolab-v1/04-security-and-permissions.md); readiness review §1.2, §4.6 | `HA_LLAT` is read from `os.environ` inside `_init()` exactly once per process; its value goes into `Tools._bearer` as `"Bearer <token>"` and from there into the outbound `Authorization` header; it never enters `args_snap`, never appears in the returned JSON, never reaches the audit log |
| Audit-log path | **D-07 / D-21** | inherited from the inlined helper |
| Entity-id grammar + length bound | readiness review §3.2 | `^[a-z_]+\.[a-z0-9_]+$`, length 3-128 |
| Per-attribute JSON cap | readiness review §3.3 | `_ATTR_PAYLOAD_CAP = 2048` chars-serialized |
| HTTP timeout | readiness review §3.5 sketch | `_HTTP_TIMEOUT_S = 5.0` |
| Result codes (8: parity with `rag_search`) | readiness review §3.4 | `bad_entity_id`, `rate_limited`, `init_error`, `ha_unreachable`, `unauthorized`, `not_found`, `ha_error`, `ok` |
| `base_model_id = NULL` invariant on qwen2.5 | **D-35** | out of scope for this Tool source; C-4 will preserve `base_model_id = NULL` when extending `meta.toolIds` |
| Readiness-review proposed **D-37** | readiness review §9 | `ha_get_state` is single-entity-only in v1; `area=` / `domain=` filters deferred to v1.1. This Tool implements that proposal verbatim — the method signature is `(self, entity_id)` only |

## 3. Design decisions taken inside the locked frame

These are mechanical adaptations of locked decisions plus the
in-progress readiness-review proposals (D-37 in particular).

### 3.1 Class-level `httpx.Client` + bearer (single per process)

`_httpx_client`, `_base_url`, `_bearer` are declared on the
class body (`Tools._httpx_client = None`), not on `self`. Per
the FUNCTIONS_COMPATIBILITY_REPORT runtime contract, Open WebUI
0.8.10 constructs a `Tools()` instance per dispatch but keeps
the module object cached in `sys.modules`; class-level state
survives between instances. This means:

- The bearer string is built once (on first call) and reused
  for every subsequent call until the openwebui container
  restarts.
- A single `httpx.Client` keeps connection pooling alive across
  calls — the first call pays the TCP / TLS handshake to HA,
  later calls reuse the connection. On a LAN-local HA install
  this is in the ~10-50 ms range.
- `HA_LLAT` is read from `os.environ` exactly once per process.
  If the user rotates the token in `.env`, the openwebui
  container must be recreated for the new value to take effect
  — same `.env`-is-read-only-at-start contract that Phase B B-3
  and Phase C G-Cpre already enforce.

### 3.2 Heavy import (`httpx`) deferred to `_init()`

`import httpx` appears **inside** `_init()`, not at module top.
Two reasons:

1. Module load is part of OWUI's tool spec build pipeline; even
   though `httpx` import is light (~10-50 ms), keeping it lazy
   keeps the spec build perfectly cheap.
2. If a future operator hot-reloads only this Tool without
   restarting openwebui, deferring `httpx` import keeps the
   import-time semantics identical to `rag_search`'s
   `from ingest.embedder import Embedder`.

The deferred-import pattern is the same one B-4 / B-5 used for
the much heavier `sentence_transformers` imports.

### 3.3 `HA_LLAT` security model — defense in depth

Three boundaries protect the token from accidental disclosure:

1. **Never put it into `args`.** The `args_snap` dict has only
   `{"entity_id": entity_id}`. The `_audit(...)` calls receive
   exactly that dict. The inlined `_amarolab_redact` helper
   then walks the dict and masks any value whose key matches
   `password|token|secret|api_key|authorization` — but since
   the LLAT key isn't in `args_snap` at all, redaction isn't
   load-bearing here. **The first line of defense is "don't
   put it there in the first place."**
2. **Never include it in the return value.** The JSON response
   has `entity_id`, `state`, `friendly_name`, `last_changed`,
   `last_updated`, `attributes`, `result_code`. No bearer, no
   header dump, no debug trail.
3. **HA-side response sanitisation.** Some HA integrations
   stash short-lived tokens under attribute names like
   `access_token` or vendor-specific keys. The attribute
   allowlist (§3.4) means none of these reach the LLM unless we
   explicitly add the key — and we never have.

The `_amarolab_redact` helper is the second line of defense
*if* a future Tool author accidentally puts `Authorization`
into `args`. The first line is "don't put it there at all" —
and the four local-validation probes in §5.5 confirm that
neither `args` nor any error output contains the bearer.

### 3.4 Attribute allowlist (`_SAFE_ATTRIBUTE_KEYS`) — security boundary

87 attribute keys are forwarded; everything else is dropped.
The set is grouped by HA domain (universal metadata, light,
cover, climate, media_player, fan, vacuum, script /
automation, input_*, sensor) and deliberately excludes
**every** attribute that could surface:

- HA-side credentials (`access_token`, integration-specific
  token keys, OAuth client ids).
- URLs that expose internal endpoints (`entity_picture`,
  `media_image_url`, camera snapshot URLs).
- Internal HA state (`restored`, `editable`,
  `friendly_name_template`, etc.).
- Arbitrary user-defined attributes (HA lets users add custom
  attributes via `customize.yaml`; we drop them all rather than
  case-by-case allowlisting).

The choice of **allowlist over denylist** matters: new HA
integrations cannot silently add forwarded attributes; growing
this set is an explicit Phase C+ design decision, not a passive
risk. If a useful attribute is missing, adding it is a small
PR with a single line change.

The per-attribute 2 KB serialized cap is a second line of
defense: even an allowlisted attribute (e.g.
`supported_features` is sometimes a list of dozens of integer
flags) that grows unexpectedly will be silently dropped from
the response rather than blowing out the LLM's context budget.
2 KB is comfortably above typical real-world payloads (most
attributes are < 256 bytes serialized).

`friendly_name` is surfaced at the top level (not nested in
`attributes`) because the C-1 contract makes it a first-class
field — the LLM uses it for natural-language references in its
reply ("the Kitchen Light is on").

### 3.5 Result-code matrix (8 codes — parity with `rag_search`)

| Code | Trigger | `allowed` | HA call attempted? |
|---|---|:---:|:---:|
| `bad_entity_id` | regex fail or length out of `[3, 128]` | `false` | no |
| `rate_limited` | `_RateLimiter.check` denies (default 60/min) | `false` | no |
| `init_error` | `HA_BASE_URL` or `HA_LLAT` missing/empty in env | `false` | no |
| `ha_unreachable` | TCP / DNS / timeout / `httpx` raised on `.get()` | `false` | attempted (`httpx` raised) |
| `unauthorized` | HA returned 401 — token rejected | `true` | yes |
| `not_found` | HA returned 404 — entity doesn't exist | `true` | yes |
| `ha_error` | HA returned other non-2xx OR returned 2xx with malformed JSON | `true` | yes |
| `ok` | HA returned 200 + parseable JSON | `true` | yes |

`allowed: true` means "the assistant decided this call was
within scope and tried it"; `allowed: false` means "the
assistant refused before even reaching HA." The distinction
matters for the audit log: an `unauthorized` line says the
LLAT is stale (rotate); a `bad_entity_id` line says the LLM
sent a malformed id (model bug or jailbreak).

Every path either returns a JSON string or raises into the
OWUI runtime; `_audit(...)` runs on every path. Per D-06, the
audit log is the single source of truth for "what was asked,
what was decided."

### 3.6 Rate limit at 60/min (vs 30/min for `rag_search`)

HA reads are cheap — a single HTTP GET on the LAN, no model
load, no cross-encoder pass. 60/min is the same default
`time_now` ships with (the Phase A.3 canary), which is a good
ceiling for "user spam-clicks the chat." `rag_search` /
`audit_search` are lower (30/min) because each call costs
~10 s of CPU on the bge-reranker. Operators can tune
`max_per_minute` from 1 to 600 via the Valves UI.

### 3.7 `self.citation = False`

The Tool returns structured state data with `entity_id`,
`state`, `friendly_name`, etc. The LLM is expected to compose
a natural-language reply around those fields. Setting
`self.citation = True` would make OWUI wrap the entire JSON
output as a single Citation, which is wrong for status
reporting. Mirrors `time_now` / `rag_search`.

### 3.8 Output shape contract

```json
{
  "entity_id": "light.kitchen",
  "state": "on",
  "friendly_name": "Kitchen Light",
  "last_changed": "2026-06-17T18:23:11.234567+00:00",
  "last_updated": "2026-06-17T18:23:11.234567+00:00",
  "attributes": {
    "brightness": 255,
    "color_mode": "color_temp",
    "color_temp": 366,
    "supported_features": 63
  },
  "result_code": "ok"
}
```

Top-level fields exactly match the user's C-1 capability list
(`state`, `friendly_name`, `last_changed`, `attributes
(limited/safe subset)`) — plus three pass-through fields
(`entity_id`, `last_updated`, `result_code`) that are needed by
the audit log + the LLM's grounding logic. The readiness
review §3.3 has `friendly_name` nested inside `attributes`;
this implementation surfaces it at the top level per the
user's wording. Net effect: the LLM gets the same data either
way, with the C-1 wording slightly more direct for the model.

## 4. What the Tool deliberately does **not** do

- **Does not write to Home Assistant.** No `POST`, no `PUT`,
  no `DELETE`. The Tool is read-only by construction (only
  `httpx_client.get(...)` is called).
- **Does not list multiple entities.** The LLM must call once
  per `entity_id`. v1.1 may add `ha_list_entities(domain,
  limit=50)` per readiness review §3.7; not in scope here.
- **Does not resolve area names or domain filters.** v1
  ships single-entity-only per readiness-review-proposed D-37;
  the docstring tells the LLM not to pass area/domain.
- **Does not subscribe to state changes.** REST API only; no
  websocket.
- **Does not call Guardian Cloud, Qdrant, or the ingest
  pipeline.** No cross-Tool imports (D-26); the bind-mounted
  `/opt/ingest` from B-3 is not used here.
- **Does not log the bearer / LLAT.** The bearer lives in
  `Tools._bearer` (in-process memory) and goes into the
  `Authorization` header only. Never on disk, never in
  return JSON, never in `args_snap`.
- **Does not invoke `ha_call_service`.** That's C-2.
- **Does not extend `meta.toolIds`.** That's C-4 / Gate G-4.

## 5. Local validation

### 5.1 Pre-inline syntax

```
$ python3 -m py_compile ai-stack/openwebui-tools/tools/ha_get_state.py
PASS: py_compile (pre-inline)
```

The marker `# @@AMAROLAB_INLINE:audit_helper@@` is a valid
Python comment, so `py_compile` parses cleanly even though the
helper symbols `_audit`, `_RateLimiter`, `_amarolab_redact`
are not yet defined.

### 5.2 install_tool dry-run

```
$ ./bin/install_tool --dry-run tools/ha_get_state.py
# would install id=ha_get_state name='Amarolab ha_get_state' (content 14982 chars)
# description: Read one Home Assistant entity's current state and a
#              curated, safe subset of its attributes. …
# manifest: {"author": "amarolab", "author_url": "https://github.com/amaroou",
#            "version": "0.1.0", "license": "MIT"}
```

Inlined output is 408 lines (vs `rag_search.py`'s 289 and
`audit_search.py`'s 282 — the delta is the 87-key
`_SAFE_ATTRIBUTE_KEYS` constant and the longer error-code
matrix). 14 982 chars is well within Open WebUI 0.8.10's
practical Tool-content limit (`time_now` is 5 180; `rag_search`
is 11 629; both ship cleanly).

### 5.3 Post-inline syntax

```
$ python3 -m py_compile /tmp/hgs.inlined.body.py
PASS: py_compile (post-inline)
$ grep -c '_audit\|_RateLimiter\|_amarolab' /tmp/hgs.inlined.body.py
28
```

28 cross-references between the inlined helper and the Tool
body all resolve. No undefined-name errors.

### 5.4 AST shape

```
class Tools: PRESENT
Methods: ['__init__', '_init', 'ha_get_state']
LLM-callable (non-underscore) methods: ['ha_get_state']
Nested classes: ['Valves']
ha_get_state args: ['self', 'entity_id']
_SAFE_ATTRIBUTE_KEYS: module-level Assign found
```

Single LLM-callable method, Valves nested class,
`(self, entity_id)` signature matches D-37 (no area / domain
filter), `_SAFE_ATTRIBUTE_KEYS` lives at module level (not
inside `Tools` — module-level so it's a true singleton,
shared across `Tools()` instances if any are constructed).

### 5.5 In-container probes (no HA call, no `_init()` invocation)

```python
spec = importlib.util.spec_from_file_location('tool_ha_get_state', '/tmp/hgs_inlined.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print('module loaded OK')                              # PASS
T = mod.Tools()
print('valves.max_per_minute =', T.valves.max_per_minute)  # 60
print('citation flag =', T.citation)                       # False
print('class-level _httpx_client is None?', mod.Tools._httpx_client is None)  # True
print('class-level _bearer is None?', mod.Tools._bearer is None)              # True
print('_SAFE_ATTRIBUTE_KEYS size:', len(mod._SAFE_ATTRIBUTE_KEYS))            # 87
print('_HTTP_TIMEOUT_S:', mod._HTTP_TIMEOUT_S,
      '_ATTR_PAYLOAD_CAP:', mod._ATTR_PAYLOAD_CAP)                            # 5.0, 2048

# Four bad_entity_id paths (no _init invoked, no HA call attempted):
r = json.loads(T.ha_get_state(entity_id='x'))
# → {'error': 'entity_id must be 3-128 characters', 'code': 'bad_entity_id'}
r = json.loads(T.ha_get_state(entity_id='LIGHT.KITCHEN'))
# → {'error': 'entity_id must match <domain>.<object_id> lowercase grammar', 'code': 'bad_entity_id'}
r = json.loads(T.ha_get_state(entity_id='not_a_valid_id_no_dot'))
# → {'error': 'entity_id must match <domain>.<object_id> lowercase grammar', 'code': 'bad_entity_id'}
r = json.loads(T.ha_get_state(entity_id='light.'))
# → {'error': 'entity_id must match <domain>.<object_id> lowercase grammar', 'code': 'bad_entity_id'}

print('after probes class-level _httpx_client is None?', mod.Tools._httpx_client is None)  # True
print('after probes class-level _bearer is None?', mod.Tools._bearer is None)              # True
```

Key invariant: **`_httpx_client` and `_bearer` are both still
`None` after the four probes.** This proves:

- `_init()` was never called.
- `httpx` was never imported.
- `HA_LLAT` was never read from `os.environ`.
- `HA_BASE_URL` was never read from `os.environ`.
- No HTTP request was issued to Home Assistant.
- HA's access log records nothing from this validation turn.

The four probes test the four distinct `bad_entity_id`
failure modes (length-too-short, uppercase letters, missing
dot, empty object_id). All four return the contract-shaped
error JSON.

### 5.6 What was deliberately NOT validated locally

Deferred to C-5 / C-6 (user-driven) and to follow-up
validation logs:

- The Tool wired through OWUI's `tool_ids` auto-attach path
  (gated by C-3 install + C-4 / Gate G-4 toolIds extension).
- A successful `result_code: ok` end-to-end call (would
  require `_init()` → `httpx` → HA → response curation).
- The `unauthorized` path (would require HA to return 401 —
  e.g., by deliberately corrupting the LLAT first).
- The `not_found` path (would require querying for a known-
  missing entity).
- The `ha_unreachable` path (would require taking HA off the
  network).
- The attribute-allowlist filter applied to a real HA response
  (the test fixture would need a HA instance with a known
  light + thermostat + media_player to stress all branches of
  the allowlist).
- Performance — readiness review §7 C-aux4 expects warm reads
  ≤ 1.0 s; not measured here.

These are the C-5 / C-6 / C-aux1..4 lines in the readiness
review §7. The current turn's `bad_entity_id` probes prove
the schema layer; everything past `_init()` waits for the
user-gated installation steps.

## 6. Side effects of this turn

| Artefact | Location | Reversibility |
|---|---|---|
| `ai-stack/openwebui-tools/tools/ha_get_state.py` | host, 305 lines | `git restore` |
| `/tmp/hgs.inlined.py` (host) | host `/tmp` | tmpfs / next reboot |
| `/tmp/hgs.inlined.body.py` (host) | host `/tmp` | tmpfs / next reboot |
| `/tmp/hgs_inlined.py` (container) | container `/tmp` | container restart |
| Cached bytecode `__pycache__/ha_get_state.cpython-3*.pyc` | host `openwebui-tools/tools/__pycache__/`; container `/tmp/__pycache__/` | rm |
| **Audit log** `/srv/homelab/data/openwebui/amarolab-audit.log` | host | **+4 lines** — disclosed below |

### 6.1 Audit-log delta — exactly the 4 `bad_entity_id` lines

```json
{"ts":"2026-06-16T14:11:39.456294+00:00","tool":"ha_get_state","args":{"entity_id":"x"},"allowed":false,"result_code":"bad_entity_id","duration_ms":null}
{"ts":"2026-06-16T14:11:39.456419+00:00","tool":"ha_get_state","args":{"entity_id":"LIGHT.KITCHEN"},"allowed":false,"result_code":"bad_entity_id","duration_ms":null}
{"ts":"2026-06-16T14:11:39.456483+00:00","tool":"ha_get_state","args":{"entity_id":"not_a_valid_id_no_dot"},"allowed":false,"result_code":"bad_entity_id","duration_ms":null}
{"ts":"2026-06-16T14:11:39.456551+00:00","tool":"ha_get_state","args":{"entity_id":"light."},"allowed":false,"result_code":"bad_entity_id","duration_ms":null}
```

Audit log line count: 108 → 112 (`+4`). All four:
- `tool: "ha_get_state"`
- `args: {"entity_id": "<value>"}` — only entity_id, no LLAT, no bearer, no base_url
- `allowed: false`
- `result_code: "bad_entity_id"`
- `duration_ms: null` (validation short-circuits before `t0`-elapsed accounting kicks in — same pattern as `rag_search` / `audit_search` bad_query probes)

The append-only line shape matches the contract Phase A.3
established for `time_now` and Phase B B-6 extended for
`rag_search` / `audit_search`. **No bearer-shape string is
present in any of the four lines** (LLAT pattern is
`^[A-Za-z0-9_-]{50,}\.[A-Za-z0-9_-]{50,}\.[A-Za-z0-9_-]{30,}$`;
the entity_ids written are clearly not JWTs).

### 6.2 Forensic state at end of C-1

| Item | Value |
|---|---|
| `webui.db` MD5 | drifts under normal OWUI traffic; the C-1-relevant invariants are below |
| `webui.db` qwen2.5 `meta.toolIds` | `["time_now","rag_search","audit_search"]` — unchanged (still pre-C-4) |
| `webui.db` qwen2.5 `base_model_id` | `NULL` (D-35) — unchanged |
| `webui.db` `tool` rows | 4 Amarolab/Jarvis (`audit_search`, `docker_containers`, `docker_logs`, `rag_search`, `system_status`, `time_now`) + 2 Jarvis pre-existing — **no `ha_get_state` row** |
| `amarolab-audit.log` line count | 112 (was 108 at end of G-Cpre closeout; +4 from C-1 probes) |
| qdrant + openwebui containers | running healthy; HA env passthrough alive (G-Cpre invariant) |
| `tools/ha_get_state.py` on disk | **new this turn** |
| `tools/ha_call_service.py` on disk | **does not exist** (C-2) |
| Git working tree | one new tool source + this log untracked; otherwise tracking what was already there |
| Local vs `origin/main` | unchanged relative to G-Cpre — no new commits |

## 7. Recommended next step

The Tool source is structurally complete and locally
validated. The natural next moves, in priority order:

1. **Author `tools/ha_call_service.py` (C-2).** Pair to this
   Tool; implements the 12-domain Literal allowlist + runtime
   `_ALLOWED_DOMAINS` re-check + refusal grammar. Closes the
   read+write pair so C-3 can install both in one batch.
2. **C-3 install both Tools** via `bin/install_tool` (D-25).
3. **C-4 Gate G-4** — extend qwen2.5 `meta.toolIds` to
   `["time_now","rag_search","audit_search","ha_get_state","ha_call_service"]`,
   preserving `base_model_id = NULL` (D-35).
4. **C-5 / C-6** — user-driven refusal + happy-path tests.

If the user wants to commit this C-1 artefact first, the
natural commit-message form is:

```
feat(amarolab): add ha_get_state Open WebUI Tool source (Phase C C-1)

- tools/ha_get_state.py — class Tools with lazy _init() reading
  HA_BASE_URL / HA_LLAT from env into a single class-level
  httpx.Client + bearer; entity_id regex + length validation;
  attribute allowlist (87 keys, security boundary per D-06);
  per-attribute JSON cap 2 KB; eight result codes
  (bad_entity_id / rate_limited / init_error / ha_unreachable /
   unauthorized / not_found / ha_error / ok); inlined audit
  helper via D-26 marker; LLAT never enters args or return JSON.
- 09_logs/2026-06-17_phaseC_ha_get_state_design.md — design log
  with D-24/D-26 crosswalk, allowlist rationale, LLAT-handling
  defense-in-depth, local validation summary (py_compile pre/
  post inline; AST shape; in-container module load + 4
  bad_entity_id probes; class-level state still None proving
  no HA call was made).
```

## 8. What C-1 deliberately did NOT do

- Did not run `bin/install_tool tools/ha_get_state.py` (real POST).
- Did not write to `webui.db`.
- Did not extend `meta.toolIds`.
- Did not recreate or restart any container.
- Did not call Home Assistant (no GET, no POST, no
  `/api/auth/current_user`, no DNS lookup that would log a
  request HA-side).
- Did not read `HA_LLAT` or `HA_BASE_URL` from
  `os.environ` — confirmed by class-level state staying `None`
  after the four probes.
- Did not author `tools/ha_call_service.py` (C-2).
- Did not invoke `_init()`. The four validation probes
  short-circuited on the entity_id regex / length check before
  reaching `self._init()`.

## 9. Cross-references

- Tool source written this turn:
  `ai-stack/openwebui-tools/tools/ha_get_state.py`
- Phase C readiness review (the C-1 contract):
  [`2026-06-17_phaseC_readiness_review.md`](2026-06-17_phaseC_readiness_review.md)
- G-Cpre closure (the runtime env pre-requisite):
  [`2026-06-17_phaseC_secret_rotation_and_gcpre_applied.md`](2026-06-17_phaseC_secret_rotation_and_gcpre_applied.md)
- Reference Tool (`time_now`):
  [`../ai-stack/openwebui-tools/tools/time_now.py`](../ai-stack/openwebui-tools/tools/time_now.py)
- Phase B-shaped sibling Tool (`rag_search`):
  [`../ai-stack/openwebui-tools/tools/rag_search.py`](../ai-stack/openwebui-tools/tools/rag_search.py)
- Inlined helper (D-26):
  [`../ai-stack/openwebui-tools/lib/audit_helper.py`](../ai-stack/openwebui-tools/lib/audit_helper.py)
- Install workflow (D-25):
  [`../ai-stack/openwebui-tools/bin/install_tool`](../ai-stack/openwebui-tools/bin/install_tool)
- Trust model (D-06, audit redaction contract):
  [`../04_ai_system/amarolab-v1/04-security-and-permissions.md`](../04_ai_system/amarolab-v1/04-security-and-permissions.md)
- OWUI runtime contract (D-24, D-25, D-26):
  [`../FUNCTIONS_COMPATIBILITY_REPORT.md`](../FUNCTIONS_COMPATIBILITY_REPORT.md)
- Phase C execution plan source (closeout §6):
  [`2026-06-16_phaseB_closeout.md`](2026-06-16_phaseB_closeout.md)
- Sub-project live state:
  [`../04_ai_system/amarolab-v1/CURRENT_STATE.md`](../04_ai_system/amarolab-v1/CURRENT_STATE.md),
  [`../04_ai_system/amarolab-v1/ROADMAP.md`](../04_ai_system/amarolab-v1/ROADMAP.md),
  [`../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md`](../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md)

## 10. Stop point

Per the user's instruction ("Stop after code creation, design
review, git status."): this log is the artefact. The Tool
source is on disk, locally validated, and not installed. C-2
(`tools/ha_call_service.py`) awaits explicit instruction.
