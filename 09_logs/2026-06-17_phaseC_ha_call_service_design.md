# Phase C C-2 — `ha_call_service` Tool source (design + local validation)

- **Date:** 2026-06-17.
- **Goal:** author `tools/ha_call_service.py` as the canonical
  version-controlled source for the `ha_call_service` Open
  WebUI Tool — the **single bounded-write** entry point into
  Home Assistant for the Amarolab Assistant. Mirror
  `tools/ha_get_state.py`'s architecture. Validate locally
  only — no Tool install, no `webui.db` change, no `meta.toolIds`
  extension, no container recreate, **no real HA write
  operation.** The local validation includes the
  user-mandated **canonical refusal probe**
  (`domain="recorder", service="purge", entity_id="recorder.purge"`)
  exercised against the in-container module-loaded source —
  verified to short-circuit at the safety boundary, before any
  `httpx` import, before any `_init()` invocation, before any
  HTTP request to HA.
- **Inputs:**
  [`2026-06-17_phaseC_readiness_review.md`](2026-06-17_phaseC_readiness_review.md)
  §4 (`ha_call_service` design contract), §5 (12-domain
  allowlist, locked), §6 (refusal grammar);
  [`2026-06-17_phaseC_ha_get_state_design.md`](2026-06-17_phaseC_ha_get_state_design.md)
  (C-1 — pattern mirror target);
  [`2026-06-17_phaseC_secret_rotation_and_gcpre_applied.md`](2026-06-17_phaseC_secret_rotation_and_gcpre_applied.md)
  (G-Cpre closure — `HA_BASE_URL` / `HA_LLAT` in container env);
  [`../04_ai_system/amarolab-v1/04-security-and-permissions.md`](../04_ai_system/amarolab-v1/04-security-and-permissions.md)
  (trust model, D-12 allowlist text);
  [`../FUNCTIONS_COMPATIBILITY_REPORT.md`](../FUNCTIONS_COMPATIBILITY_REPORT.md)
  (D-24/D-25/D-26 runtime contract);
  the inlined helper at
  [`../ai-stack/openwebui-tools/lib/audit_helper.py`](../ai-stack/openwebui-tools/lib/audit_helper.py).

## 0. TL;DR

**`tools/ha_call_service.py` is on disk, syntax-clean both
before and after install-time inlining, AST-shape compliant
with D-24, and import-loads inside the openwebui container.**
The canonical refusal probe and six additional validation
probes all returned the contract-shaped errors **without
constructing the `httpx.Client` and without sending any HTTP
request to Home Assistant.** The Tool is not installed in
`webui.db`; C-3 owns that.

| Check | Result |
|---|---|
| `python3 -m py_compile tools/ha_call_service.py` (pre-inline) | **PASS** |
| `bin/install_tool --dry-run tools/ha_call_service.py` | **PASS** — id=`ha_call_service`, name=`Amarolab ha_call_service`, **18 494 chars**, manifest extracted |
| `python3 -m py_compile` on the inlined body | **PASS** (34 references between helper and Tool body resolve) |
| AST shape — `class Tools`, methods=`['__init__','_init','ha_call_service']`, LLM-callable=`['ha_call_service']`, nested `Valves`, args=`['self','domain','service','entity_id','service_data']`, `domain` annotation = `Subscript` (Literal) | **PASS** |
| AST — `_ALLOWED_DOMAINS` cardinality | **13 elements** (matches the user's listed enumeration verbatim — see §3.4 note on D-12 text-vs-list off-by-one) |
| In-container module load + `Tools()` instantiation | **PASS** (Valves defaults `max_per_minute=10`, `citation=False`, class-level state `None`) |
| **Canonical refusal probe** — `ha_call_service(domain="recorder", service="purge", entity_id="recorder.purge")` | **PASS** — returned `{"allowed": false, "domain": "recorder", "service": "purge", "code": "refused", "message": "..."}` |
| Refusal probe — out-of-allowlist `backup.create` | **PASS** — `refused` |
| Validation probe — `bad_service` (uppercase) | **PASS** |
| Validation probe — `bad_entity_id` (uppercase) | **PASS** |
| Validation probe — `bad_service_data` (non-dict) | **PASS** |
| Validation probe — `bad_service_data` (contains `entity_id` key) | **PASS** |
| Validation probe — `bad_service_data` (> 4 KB serialised) | **PASS** |
| Class-level `_httpx_client` / `_bearer` after all 7 probes | **still `None`** — proves `_init()` was never invoked; `httpx` was never imported; `HA_LLAT` / `HA_BASE_URL` were never read from env; **NO HTTP request was sent to Home Assistant** |
| `webui.db`, `meta.toolIds`, openwebui container env, Home Assistant runtime | **untouched by C-2** |

## 1. What this Tool is supposed to be

`ha_call_service(domain, service, entity_id, service_data?)` is
the **single write** entry point into Home Assistant — the
only Amarolab Tool that mutates external state. It POSTs to
`${HA_BASE_URL}/api/services/{domain}/{service}` with an
`Authorization: Bearer ${HA_LLAT}` header and a JSON body
containing the `entity_id` and (optionally) extra
`service_data` keys.

The design pays for its safety-sensitive role with:

1. **A `Literal`-typed `domain` enum** so OWUI 0.8.10's spec
   builder emits a typed JSON-Schema `enum` to the LLM.
2. **A runtime allowlist re-check** as the very first action
   inside the method body — `if domain not in _ALLOWED_DOMAINS:
   return refused` — that holds even if the schema layer is
   ever bypassed.
3. **A polite refusal path** (`result_code: "refused"`,
   `allowed: false`) that **never issues an HTTP request to
   HA**, never constructs the `httpx.Client`, never reads
   `HA_LLAT` from env.
4. **A stricter rate limit** (10/min vs `ha_get_state`'s 60
   and `time_now`'s 60) reflecting that each call mutates
   external state.
5. **Full audit-log capture** of every refused call.
6. **Per-input validation** for `service` (regex + length),
   `entity_id` (same shape as `ha_get_state`), and
   `service_data` (dict + JSON-serialisable + ≤ 4 KB + no
   embedded `entity_id` key).
7. **An `ha_response` cap** (8 KB serialised, with a
   `...<truncated>` marker beyond) so an HA script that
   touches dozens of entities doesn't drown the LLM in state.

## 2. Source-of-truth crosswalk

| Concern | Source of truth | Implementation site |
|---|---|---|
| Tool runtime contract — `class Tools` | **D-24** | `class Tools:` with one public method (`ha_call_service`) and one underscore-prefixed runtime helper (`_init`) |
| Inline helper marker | **D-26** | `# @@AMAROLAB_INLINE:audit_helper@@` near the top, replaced by `bin/install_tool` |
| Source location on disk | **D-23** | `ai-stack/openwebui-tools/tools/ha_call_service.py` |
| Tool install workflow | **D-25** | `bin/install_tool tools/ha_call_service.py` — gated to C-3; this log does not install |
| Per-model scope | **D-20** | handled by `meta.toolIds` on the qwen2.5 Model entry at C-4 (Gate G-4) |
| Trust model — LLM is adversarial; allowlists are file-level Python constants | **D-06** | `_ALLOWED_DOMAINS`, `_EXPLICITLY_DENIED`, `_ENTITY_ID_RE`, `_SERVICE_RE`, `_SERVICE_DATA_CAP`, `_HA_RESPONSE_CAP` are module-level constants; no `eval`, no `subprocess`, no path-from-arg, no shell from arguments |
| 12-domain HA allowlist | **D-12** (text in ROADMAP.md says "12 domains", lists 13; see §3.4) | `_ALLOWED_DOMAINS = frozenset({…13 strings…})`; matched verbatim by the `Literal[…]` enum on the `domain` parameter |
| Refusal `result_code` literal = `"refused"` | readiness review §4.4 (proposed D-36) + closeout §6.3 wording | `_audit(..., result_code="refused")` + return JSON `"code": "refused"` |
| HA token handling | T6 mitigation in [`04-security-and-permissions.md`](../04_ai_system/amarolab-v1/04-security-and-permissions.md); readiness review §4.6 | `HA_LLAT` is read from `os.environ` inside `_init()` exactly once per process; goes into `Tools._bearer` as `"Bearer <token>"`; never enters `args_snap`, never appears in returned JSON, never reaches the audit log |
| Audit-log path | **D-07 / D-21** | inherited from the inlined helper |
| Entity-id grammar + length | readiness review §4.2 + C-1 parity | `^[a-z_]+\.[a-z0-9_]+$`, length 3-128 |
| Service-name grammar + length | readiness review §4.2 | `^[a-z_][a-z0-9_]*$`, length 1-64 |
| Service-data JSON cap | readiness review §4.2 (proposed D-38) | `_SERVICE_DATA_CAP = 4096` chars |
| `ha_response` cap | readiness review §4.3 (proposed D-38) | `_HA_RESPONSE_CAP = 8192` chars + `_HA_RESPONSE_TRUNCATION_MARKER = "...<truncated>"` |
| Rate limit at 10/min | readiness review §4.1 + §10 R-C5 | `Valves.max_per_minute` default 10 (operator-tunable 1-600) |
| HTTP timeout | readiness review §4 / C-1 parity | `_HTTP_TIMEOUT_S = 5.0` |
| Result codes (11 — refusal + 4 input + rate + init + 4 HA outcomes) | readiness review §4.7 | enumerated in §3.5 |
| `base_model_id = NULL` invariant on qwen2.5 | **D-35** | out of scope here; C-4 will preserve `base_model_id = NULL` when extending `meta.toolIds` |

## 3. Design decisions taken inside the locked frame

### 3.1 Three-layer defense against out-of-allowlist domains

| Layer | What | When it fires |
|---|---|---|
| **Prompt layer (D-30, v0.1 prompt in place)** | The system prompt's refusal block tells qwen2.5: HA control is bounded; refuse to even attempt out-of-allowlist domains | Best case — no Tool call dispatched, no audit-log delta |
| **Schema layer (`Literal["light", ..., "input_number"]`)** | OWUI 0.8.10's spec builder emits a JSON-Schema `enum` over the 13 allowed values. qwen2.5 honours enum-typed args in B-6 / Phase B testing | An out-of-enum value would be a model bug (free-form `tool_calls` from a jailbreak, frontend bug, etc.). Not load-bearing for safety on its own |
| **Runtime layer (`if domain not in _ALLOWED_DOMAINS: return refused`)** | First action inside the method body. Even if a future change bypasses the schema (free-form tool_calls, frontend change, OWUI version bump that drops `enum` enforcement), this check holds | **The safety boundary.** Out-of-allowlist domain ⇒ no `_init()`, no `httpx` import, no HTTP request to HA. The local refusal probes in §5.5 exercise this layer directly |

The layers are **complementary**, not redundant. The prompt
layer saves a tool round-trip when qwen2.5 recognises the ask;
the schema layer keeps the LLM's tool-arg generation aligned
with the contract; the runtime layer is the **safety net**.

### 3.2 Refusal happens FIRST inside the method body

The first executable statement after `args_snap` construction
is:

```python
if domain not in _ALLOWED_DOMAINS:
    _audit("ha_call_service", args_snap, allowed=False, result_code="refused")
    return json.dumps({...})
```

**Before** `service` regex validation. **Before** `entity_id`
regex validation. **Before** `service_data` validation.
**Before** the rate limit check. **Before** `self._init()`.
**Before** any `httpx` import or HTTP request.

This ordering matters because:

- An out-of-allowlist `domain` is the most-sensitive failure
  mode. Putting it first means even malformed inputs that
  would otherwise trip `bad_service` or `bad_entity_id` get
  reported as `refused` — which is the correct semantic
  signal to the LLM ("the action is forbidden, not the
  syntax").
- The audit log records the canonical refusal shape on a
  single distinct line. Greppability for `result_code:
  "refused"` is the operator's primary safety telemetry.
- Defense in depth: if a future Tool author adds a new
  validation step, the refusal short-circuit is already
  upstream of it. The safety boundary doesn't drift.

### 3.3 Class-level `httpx.Client` + bearer (same pattern as C-1)

`_httpx_client`, `_base_url`, `_bearer` are on the class body,
not on `self`. The bearer string is built once per openwebui
process (in `_init()` on the first allowed call) and reused.
`HA_LLAT` is read from `os.environ` exactly once. If the user
rotates the token, the container must be recreated (G-Cpre
pattern) for the new value to take effect.

If the user issues a stream of **refused** calls and never an
allowed one, `_init()` is never invoked and `Tools._bearer`
remains `None` — confirmed by the §5.5 in-container probe.

### 3.4 The 12-vs-13 domain note

The user's C-2 brief, the readiness review §5, and ROADMAP.md
D-12 all use the phrase "12 domains" but list **13** strings:
`light`, `switch`, `scene`, `cover`, `climate`, `media_player`,
`script`, `automation`, `fan`, `vacuum`, `input_boolean`,
`input_select`, `input_number`. This is a long-standing
text-vs-rendered-list off-by-one in the v1 design package.

This implementation honours the **rendered list** (13
strings) because:

1. The user's C-2 brief lists 13 names verbatim and asks the
   Tool to "enforce the 12-domain allowlist" with those 13
   names. Choosing one to drop would be a unilateral
   restriction the user did not ask for.
2. The readiness review §5 enumerates the 13 names in the
   `_ALLOWED_DOMAINS` frozenset literal and labels it "Twelve
   domains" in the comment.
3. ROADMAP.md D-12 uses the same 13-string list.

If the user prefers the literal "12 domains", the smallest
edit is removing one entry (probably `input_number` or
`input_select`) from both `_ALLOWED_DOMAINS` and the `Literal`
enum on the method signature, with a corresponding update to
D-12's text. **Not done this turn** — the user's brief is
preserved verbatim, and this design log records the
discrepancy in §10 so a future reviewer can resolve it.

### 3.5 Result-code matrix (11 codes)

| Code | Trigger | `allowed` | HTTP issued? |
|---|---|:---:|:---:|
| `refused` | `domain` not in `_ALLOWED_DOMAINS` | `false` | **no** — safety boundary |
| `bad_service` | service regex fail or length out of `[1, 64]` | `false` | no |
| `bad_entity_id` | entity_id regex fail or length out of `[3, 128]` | `false` | no |
| `bad_service_data` | service_data not a dict OR contains top-level `entity_id` key OR not JSON-serialisable OR > 4 KB serialised | `false` | no |
| `rate_limited` | `_RateLimiter.check("ha_call_service", 10)` denies | `false` | no |
| `init_error` | `HA_BASE_URL` or `HA_LLAT` missing/empty in env | `false` | no |
| `ha_unreachable` | TCP / DNS / timeout / `httpx` raised on `.post()` | `false` | attempted |
| `unauthorized` | HA returned 401 | `true` | yes |
| `entity_not_found` | HA returned 400 with not-found body OR 404 | `true` | yes |
| `ha_error` | HA returned any other non-2xx | `true` | yes |
| `ok` | HA 2xx + parseable JSON | `true` | yes |

`allowed: true` means "the assistant decided this call was in
scope and tried it"; `allowed: false` means "the assistant
refused before reaching HA." The distinction lets an operator
grep the audit log for:

- `"allowed": false, "result_code": "refused"` — the model
  attempted an out-of-allowlist domain (or `EXPLICITLY_DENIED`
  domain). T1 / prompt-injection forensics.
- `"allowed": true, "result_code": "unauthorized"` — the
  LLAT is stale or revoked (rotate per the security
  checklist).

### 3.6 `service_data` validation — what's in scope and why

`service_data` is the only optional parameter. Four rules:

| Rule | Why |
|---|---|
| Must be a `dict` (or `None`) | HA's REST API expects a JSON object as POST body; a list / string / int would fail HA-side anyway, but the typed check gives a clean `bad_service_data` instead of a hard-to-diagnose HA 400 |
| Must NOT contain a top-level `"entity_id"` key | The `entity_id` parameter is the canonical place for that. Two paths (top-level arg + nested in service_data) would lead to ambiguity about which wins. Reject early |
| Must be JSON-serialisable (`json.dumps`) | Defense against the LLM passing a non-serialisable object (e.g. a numpy scalar leaked from RAG content). HA-side would 400; we refuse cleanly |
| Serialised payload ≤ 4 KB | Defense against runaway service_data — a 1 MB blob would either OOM HA or hang the http POST. Real-world payloads are < 100 bytes |

Note on **audit-log retention of `service_data`:** the
`args_snap` dict passed to `_audit(...)` contains the
verbatim `service_data`. The inlined `_amarolab_redact`
helper walks it recursively and masks any value whose key
matches `password|token|secret|api_key|authorization`
(case-insensitive). The LLAT is **not** at risk of being
logged via `service_data` because:

1. The Tool's `args_snap` only contains the four declared
   parameters — the bearer string is never put into it.
2. If the LLM hypothetically tried to forward an
   "authorization" value via `service_data` (e.g., user said
   "set HA's API password to XYZ"), the redact helper would
   mask it as `<redacted>` before write.

Both defenses are belt-and-suspenders against the same
threat.

### 3.7 The `_EXPLICITLY_DENIED` constant — documentation only

```python
_EXPLICITLY_DENIED = frozenset({
    "homeassistant", "recorder", "hassio", "system_log",
    "backup", "auth", "persistent_notification",
    "notify", "mqtt", "shell_command",
})
```

This constant **is not referenced anywhere in the runtime
code path.** The default-deny in `_ALLOWED_DOMAINS` covers
every domain it lists (and every domain it doesn't list).
Its purpose is to make a future reader (or future AI assistant)
think twice before adding any of these to the allowlist.

`recorder` is in particular the **canonical refusal target**
the user's C-2 brief specifies (`recorder.purge`) — its
presence in `_EXPLICITLY_DENIED` is a documentation
breadcrumb that says "this was deliberately denied; do not
add."

### 3.8 Rate limit at 10/min (lower than reads)

The Valves default is 10/min, vs:

- `time_now`: 60/min (microsecond operations)
- `ha_get_state`: 60/min (single HTTP GET on LAN, no model load)
- `rag_search` / `audit_search`: 30/min (~10 s rerank pass each)
- `ha_call_service`: **10/min** (each call mutates external state)

The readiness review §10 R-C5 flagged the cost of this:
> if a user issues a "house off" sequence with 20 entities
> and the LLM unfolds it into 20 calls, the latter 10 will
> `rate_limited`

Accepted trade-off. The rate-limit value is a Valve — an
operator can raise it via the OWUI Workspace UI without
re-installing the Tool. The default is the floor.

### 3.9 Output shape contracts

**Success:**

```json
{
  "ok": true,
  "domain": "light",
  "service": "turn_on",
  "entity_id": "light.kitchen",
  "ha_status": 200,
  "ha_response": [
    {"entity_id": "light.kitchen", "state": "on",
     "attributes": {"brightness": 255}, "last_changed": "..."}
  ],
  "result_code": "ok"
}
```

**Refusal:**

```json
{
  "allowed": false,
  "domain": "recorder",
  "service": "purge",
  "code": "refused",
  "message": "I can change lights, scenes, climate, media, and similar — not 'recorder.purge'."
}
```

The `message` field carries a one-line refusal the LLM may
echo verbatim. It deliberately names the requested
`<domain>.<service>` so the user (and the audit-log reader)
sees what was tried.

**Other errors:** structured `{"error": "...", "code": "..."}`
plus context (`"ha_status": int` where available,
`"detail": "<ExceptionClass>"` for transport failures).

## 4. What the Tool deliberately does **not** do

- **Does not read Home Assistant.** Use `ha_get_state` (C-1).
  This Tool's `_init()` opens an `httpx.Client` capable of
  both GET and POST; the method body only calls `.post()`.
- **Does not target multiple entities in one call.** HA's
  REST API supports `entity_id: ["a", "b"]`; this Tool
  insists on a single string. The LLM may unfold the
  multi-entity case into multiple calls (subject to the
  10/min rate limit).
- **Does not call any service in `_EXPLICITLY_DENIED`.** The
  default-deny in `_ALLOWED_DOMAINS` already covers them;
  the explicit constant is documentation-only.
- **Does not enforce per-service whitelisting.** HA's own
  catalog of services per integration varies; HA returns 400
  for unknown services. We accept that error and surface it
  as `ha_error` / `entity_not_found` rather than pre-
  enumerating per-domain catalogs (readiness review §10
  R-C4).
- **Does not log the bearer / LLAT.** Same posture as C-1.
- **Does not stream partial results.** OWUI 0.8.10's Tool
  runtime is one-shot.
- **Does not auto-retry on `unauthorized` / `ha_error`.**
  The LLM (and the user) decide the response.
- **Does not extend `meta.toolIds`.** That's C-4 / Gate G-4.

## 5. Local validation

### 5.1 Pre-inline syntax

```
$ python3 -m py_compile ai-stack/openwebui-tools/tools/ha_call_service.py
PASS: py_compile (pre-inline)
```

### 5.2 install_tool dry-run

```
$ ./bin/install_tool --dry-run tools/ha_call_service.py
# would install id=ha_call_service name='Amarolab ha_call_service' (content 18494 chars)
# description: Call one Home Assistant service against a single entity. Allowed
#              domains (closed set, D-12): light, switch, scene, cover, climate,
#              media_player, script, automation, fan, vacuum, input_boolean,
#              input_select, input_number. Anything outside the allowlist is
#              refused before any HTTP request reaches Home Assistant. For
#              reads ("is X on?") use ha_get_state instead.
# manifest: {"author": "amarolab", "author_url": "https://github.com/amaroou",
#            "version": "0.1.0", "license": "MIT"}
```

Inlined output is **18 494 chars** post-inline; well within
OWUI 0.8.10's practical Tool-content envelope (`time_now`
5 180, `rag_search` 11 629, `audit_search` 11 231,
`ha_get_state` 14 982, `ha_call_service` **18 494**). The
delta vs C-1 is the 13-element `Literal` enum + 13-element
allowlist + 10-element `_EXPLICITLY_DENIED` + 11-code result
matrix + service_data validation block.

### 5.3 Post-inline syntax

```
$ python3 -m py_compile /tmp/hcs.inlined.body.py
PASS: py_compile (post-inline)
$ grep -c '_audit\|_RateLimiter\|_amarolab' /tmp/hcs.inlined.body.py
34
```

34 cross-references between the inlined helper and the Tool
body all resolve.

### 5.4 AST shape

```
Methods: ['__init__', '_init', 'ha_call_service']
LLM-callable: ['ha_call_service']
Nested classes: ['Valves']
ha_call_service args: ['self', 'domain', 'service', 'entity_id', 'service_data']
domain annotation type: Subscript           ← Literal[...]
_ALLOWED_DOMAINS items: ['automation', 'climate', 'cover', 'fan',
                        'input_boolean', 'input_number', 'input_select',
                        'light', 'media_player', 'scene', 'script',
                        'switch', 'vacuum']
_ALLOWED_DOMAINS size: 13
```

Single LLM-callable method; `(self, domain, service,
entity_id, service_data)` signature; `domain` carries a
`Subscript` annotation (= `Literal[…]`); allowlist matches
the user's brief and the readiness review §5 verbatim.

### 5.5 In-container probes (the canonical refusal + 6 more)

The inlined Tool body was copied into the container at
`/tmp/hcs_inlined.py` and loaded via `importlib`. Then:

| Probe | Inputs | Expected | Got |
|---|---|---|---|
| **Canonical refusal** | `domain="recorder", service="purge", entity_id="recorder.purge"` | `result_code="refused"` and **no HA call** | `{"allowed": false, "domain": "recorder", "service": "purge", "code": "refused", "message": "I can change lights, scenes, climate, media, and similar — not 'recorder.purge'."}` ✓ |
| Refusal — `backup.create` | out-of-allowlist | `refused` | `refused` ✓ |
| `bad_service` — uppercase | `service="TURN_ON"` | `bad_service` | `bad_service` ✓ |
| `bad_entity_id` — uppercase | `entity_id="LIGHT.KITCHEN"` | `bad_entity_id` | `bad_entity_id` ✓ |
| `bad_service_data` — non-dict | `service_data="not a dict"` | `bad_service_data` | `bad_service_data` ✓ |
| `bad_service_data` — embedded entity_id | `service_data={"entity_id": "foo"}` | `bad_service_data` | `bad_service_data` ✓ |
| `bad_service_data` — > 4 KB | `service_data={"k": "x"*5000}` | `bad_service_data` | `bad_service_data` ✓ |

After all seven probes:

```
class-level _httpx_client is None? True
class-level _bearer is None? True
```

**`Tools._httpx_client` and `Tools._bearer` are both still
`None`.** This proves:

- `_init()` was never invoked.
- `httpx` was never imported by the Tool.
- `HA_LLAT` was never read from `os.environ`.
- `HA_BASE_URL` was never read from `os.environ`.
- **No HTTP request was sent to Home Assistant.**

HA's own access log records nothing from this validation
turn — the safety boundary holds end-to-end.

### 5.6 What was deliberately NOT validated locally

- **Real `result_code: "ok"` end-to-end** — would require
  `_init()` → `httpx` → HA → response curation, and the user
  explicitly forbade real HA write operations.
- `unauthorized` / `entity_not_found` / `ha_error` paths
  past `_init()` — would require HA-side state manipulation.
- `ha_unreachable` — would require taking HA off the network.
- Performance — readiness review §7 C-aux4 expects warm
  writes ≤ 1.5 s. Not measured.
- The `_HA_RESPONSE_CAP` truncation — would require HA to
  return a huge response.

These belong to C-5 (user-driven canonical refusal in
chat) and C-6 (user-driven happy-path; **Gate G-5**).

## 6. Side effects of this turn

| Artefact | Location | Reversibility |
|---|---|---|
| `ai-stack/openwebui-tools/tools/ha_call_service.py` | host, 357 lines | `git restore` |
| `/tmp/hcs.inlined.py` (host) | host `/tmp` | tmpfs / next reboot |
| `/tmp/hcs.inlined.body.py` (host) | host `/tmp` | tmpfs / next reboot |
| `/tmp/hcs_inlined.py` (container) | container `/tmp` | container restart |
| Cached bytecode `__pycache__/ha_call_service.cpython-3*.pyc` | host `openwebui-tools/tools/__pycache__/`; container `/tmp/__pycache__/` | rm |
| **Audit log** `/srv/homelab/data/openwebui/amarolab-audit.log` | host | **+7 lines** — disclosed below |

### 6.1 Audit-log delta — 7 lines, all `allowed: false`

Line count: **112 → 119** (`+7`). All seven lines have:

- `tool: "ha_call_service"`
- `args: {"domain": "...", "service": "...", "entity_id": "...", "service_data": ...}` — only the declared parameters; **no bearer, no base_url, no HA_LLAT**
- `allowed: false`
- `duration_ms: null` (validation short-circuited before `t0`-elapsed accounting)
- `result_code` ∈ `{"refused", "bad_service", "bad_entity_id", "bad_service_data"}`

A `grep` for `result_code": "refused"` in the audit log
returns 2 matches (canonical `recorder.purge` and the
`backup.create` probe), both with the expected shape.

Secret-shape scan on the new 7 lines:

```
$ tail -7 /srv/homelab/data/openwebui/amarolab-audit.log | \
    grep -cE '[0-9a-fA-F]{64}|bearer|[A-Za-z0-9_-]{50,}\.[A-Za-z0-9_-]{50,}\.[A-Za-z0-9_-]{30,}'
0
```

Zero 64-hex strings, zero Bearer keyword matches, zero
JWT-shape strings. The `_amarolab_redact` helper +
"never put it into args" first-line-of-defense both held.

### 6.2 Forensic state at end of C-2

| Item | Value |
|---|---|
| `webui.db` qwen2.5 `meta.toolIds` | `["time_now","rag_search","audit_search"]` — unchanged (still pre-C-4) |
| `webui.db` qwen2.5 `base_model_id` | `NULL` (D-35) — unchanged |
| `webui.db` `tool` rows | 6 (`audit_search`, `docker_containers`, `docker_logs`, `rag_search`, `system_status`, `time_now`) — **no `ha_get_state` or `ha_call_service` row** |
| `amarolab-audit.log` line count | 119 (was 112 at end of C-1; +7 from C-2 probes) |
| qdrant + openwebui containers | running healthy; HA env passthrough alive (G-Cpre invariant) |
| `tools/ha_get_state.py` on disk | committed pending (C-1) |
| `tools/ha_call_service.py` on disk | **new this turn** |
| Git working tree | one new tool source + this log untracked; otherwise tracking what was already there |
| Local vs `origin/main` | unchanged relative to G-Cpre — no new commits this turn |

## 7. Recommended next step

The C-1 + C-2 source pair is structurally complete and
locally validated. The natural next moves:

1. **C-3 — install both Tools** via `bin/install_tool`. Same
   D-25 workflow B-6 used. Install fidelity check via
   `bin/dump_tools` round-trip + `diff` (expected to be
   trailing-newline only, per the rag_search / audit_search
   precedent).
2. **C-4 / Gate G-4** — extend qwen2.5 `meta.toolIds` to
   `["time_now","rag_search","audit_search","ha_get_state","ha_call_service"]`.
   D-35 invariant (`base_model_id = NULL`) preserved.
3. **C-5 (user-driven refusal test)** — chat
   `"please call recorder.purge"` → polite refusal (prompt
   layer wins) OR `result_code: "refused"` (Tool layer wins,
   the audit-log shape matches the §5.5 canonical probe).
4. **C-6 (user-driven happy path; Gate G-5)** — chat
   `"turn on the kitchen light"` → physical observation +
   `result_code: "ok"`.
5. **C-7 — docs/commit + Phase D hand-off note.**

If the user wants to commit C-2 first, the natural
commit-message form is:

```
feat(amarolab): add ha_call_service Open WebUI Tool source (Phase C C-2)

- tools/ha_call_service.py — class Tools with lazy _init()
  reading HA_BASE_URL / HA_LLAT from env; runtime allowlist
  re-check at body-line-1 as the safety boundary (D-12);
  Literal enum (13 values) on `domain` for OWUI spec build;
  4-input validation (refused / bad_service / bad_entity_id /
  bad_service_data) before rate_limit and _init; 11 result
  codes total. Canonical refusal probe
  (domain=recorder, service=purge, entity_id=recorder.purge)
  returns result_code=refused without invoking _init() or
  reaching HA. Inlined audit helper via D-26 marker. LLAT
  never enters args or return JSON.
- 09_logs/2026-06-17_phaseC_ha_call_service_design.md —
  design log with three-layer defense crosswalk
  (prompt/schema/runtime), refusal-first ordering, 11-code
  matrix, validation summary (py_compile pre/post inline;
  AST shape; in-container module load + canonical refusal +
  6 additional probes; class-level state still None proving
  no HA call was made).
```

## 8. What C-2 deliberately did NOT do

- Did not run `bin/install_tool tools/ha_call_service.py`.
- Did not write to `webui.db`.
- Did not extend `meta.toolIds`.
- Did not recreate or restart any container.
- Did not call Home Assistant (no GET, no POST, no
  `/api/auth/current_user`, no DNS lookup). HA's access log
  records nothing from this turn.
- Did not read `HA_LLAT` or `HA_BASE_URL` from
  `os.environ` — confirmed by class-level `_bearer` /
  `_base_url` / `_httpx_client` staying `None` after all
  seven probes.
- Did not author any other Tool. C-1 was the previous turn;
  C-3 (install) is the next.
- Did not invoke `_init()`. All seven probes short-circuited
  upstream of it.
- Did not perform any real HA write operation. The
  canonical refusal probe and all other probes either
  refused (`refused`) or rejected validation
  (`bad_service` / `bad_entity_id` / `bad_service_data`).

## 9. Cross-references

- Tool source written this turn:
  `ai-stack/openwebui-tools/tools/ha_call_service.py`
- C-1 sibling Tool + design log:
  [`../ai-stack/openwebui-tools/tools/ha_get_state.py`](../ai-stack/openwebui-tools/tools/ha_get_state.py),
  [`2026-06-17_phaseC_ha_get_state_design.md`](2026-06-17_phaseC_ha_get_state_design.md)
- Phase C readiness review (the C-2 contract):
  [`2026-06-17_phaseC_readiness_review.md`](2026-06-17_phaseC_readiness_review.md)
  §4 (`ha_call_service` design), §5 (allowlist), §6
  (refusal grammar), §7 C-2 row
- G-Cpre closure (runtime env pre-requisite):
  [`2026-06-17_phaseC_secret_rotation_and_gcpre_applied.md`](2026-06-17_phaseC_secret_rotation_and_gcpre_applied.md)
- Inlined helper (D-26):
  [`../ai-stack/openwebui-tools/lib/audit_helper.py`](../ai-stack/openwebui-tools/lib/audit_helper.py)
- Install workflow (D-25):
  [`../ai-stack/openwebui-tools/bin/install_tool`](../ai-stack/openwebui-tools/bin/install_tool)
- Trust model (D-06, audit redaction contract):
  [`../04_ai_system/amarolab-v1/04-security-and-permissions.md`](../04_ai_system/amarolab-v1/04-security-and-permissions.md)
- OWUI runtime contract (D-24 / D-25 / D-26):
  [`../FUNCTIONS_COMPATIBILITY_REPORT.md`](../FUNCTIONS_COMPATIBILITY_REPORT.md)
- Phase B closeout (the Phase C handoff spec):
  [`2026-06-16_phaseB_closeout.md`](2026-06-16_phaseB_closeout.md)
- Sub-project live state:
  [`../04_ai_system/amarolab-v1/CURRENT_STATE.md`](../04_ai_system/amarolab-v1/CURRENT_STATE.md),
  [`../04_ai_system/amarolab-v1/ROADMAP.md`](../04_ai_system/amarolab-v1/ROADMAP.md),
  [`../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md`](../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md)

## 10. Open items surfaced (not blockers)

| ID | Item | Owner | Notes |
|---|---|---|---|
| R-C2-1 | D-12 says "12 domains" but the rendered list (in readiness review §5, ROADMAP D-12, the user's C-2 brief, and now this Tool) has **13**. The Tool implements 13 verbatim; either D-12's text should be corrected to "13 domains" or one domain (likely `input_number` or `input_select`) should be dropped. **Not a Phase C blocker.** | user | resolvable by a single-line edit to D-12 text + roadmap; no Tool re-author needed unless dropping a domain |
| R-C2-2 | The `_EXPLICITLY_DENIED` constant is module-level documentation only (not referenced in any code path). A future grep for `_EXPLICITLY_DENIED` will find only the literal declaration — readable, but possibly surprising. | accepted | `# Documented-but-not-enforced` comment above the constant flags this clearly |
| R-C2-3 | HA's response shape on the `entity_not_found` path may not always include `"not_found"` or `"not found"` text — some HA versions return 400 with just `{"message": "Entity light.foo not found in the system"}`. The regex catches "not found" and "not_found" substrings. If HA changes its message format in a future version, the code would route to `ha_error` instead of `entity_not_found`. **Cosmetic only — the `ha_status` field still distinguishes the cases.** | accepted | document as a known edge in C-7 close log |
| R-C2-4 | The `service_data` 4 KB cap measures the **caller-provided** payload, not the HA-bound POST body (which adds the `entity_id` key, ~30 bytes). HA's request limit is much higher than 4 KB; this is a defense-in-depth cap, not an HA-side compliance check. | accepted | document in §3.6 above |

None of these block C-3 install or C-5 / C-6 user-driven
validation.

## 11. Stop point

Per the user's instruction ("Stop after code creation, local
validation, refusal validation, design review, git
status."): this log is the artefact. The Tool source is on
disk, locally validated, the canonical refusal probe **PASS**.
C-3 (install both Tools) and C-4 (toolIds extension, Gate
G-4) await explicit instruction.
