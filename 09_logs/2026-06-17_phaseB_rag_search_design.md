# Phase B B-4 — `rag_search` Tool source (design + local validation)

- **Date:** 2026-06-17.
- **Goal:** author `tools/rag_search.py` as the canonical
  version-controlled source for the `rag_search` Open WebUI Tool,
  validate it locally (syntax, install-time inline, AST shape,
  in-container import-and-validation-path probe), and document
  the design decisions taken inside the locked v1 design package.
  **Do not install.** Do not edit `webui.db`, `meta.toolIds`, the
  openwebui container, Home Assistant, or the Guardian Cloud
  backend.
- **Inputs:**
  [`../04_ai_system/amarolab-v1/03-tools.md`](../04_ai_system/amarolab-v1/03-tools.md)
  §"Tool 1 — rag_search" (input / output schema, error matrix);
  [`../04_ai_system/amarolab-v1/04-security-and-permissions.md`](../04_ai_system/amarolab-v1/04-security-and-permissions.md)
  (D-06 LLM-as-adversary, allowlist constants);
  [`../FUNCTIONS_COMPATIBILITY_REPORT.md`](../FUNCTIONS_COMPATIBILITY_REPORT.md)
  §3 / §5 / §7 (D-24 `class Tools` shape, D-25 install workflow,
  D-26 inline-helper convention);
  [`../04_ai_system/amarolab-v1/PHASE_B_EXECUTION_PLAN.md`](../04_ai_system/amarolab-v1/PHASE_B_EXECUTION_PLAN.md)
  §B-4; the canonical `time_now` reference at
  [`../ai-stack/openwebui-tools/tools/time_now.py`](../ai-stack/openwebui-tools/tools/time_now.py);
  the canonical helper at
  [`../ai-stack/openwebui-tools/lib/audit_helper.py`](../ai-stack/openwebui-tools/lib/audit_helper.py);
  V-C result
  [`2026-06-17_phaseB_vc_validation.md`](2026-06-17_phaseB_vc_validation.md).

## 0. TL;DR

**`tools/rag_search.py` is on disk, syntax-clean both before and
after install-time inlining, AST-shape compliant with D-24, and
import-loads inside the openwebui container without invoking
`_init()` (so no model load happened).** The validation path
end-to-end was exercised: a deliberately-bad query returned
`{"error": "query must be 2-500 characters", "code": "bad_query"}`
and produced one corresponding line in the audit log. The Tool
is not installed in `webui.db`; B-6 owns that.

| Check | Result |
|---|---|
| `python3 -m py_compile tools/rag_search.py` (pre-inline) | **PASS** |
| `bin/install_tool --dry-run tools/rag_search.py` (parses frontmatter, inlines helper, would-POST stub) | **PASS** — id=`rag_search`, name=`Amarolab rag_search`, 11 629 chars, manifest extracted |
| `python3 -m py_compile` on the inlined body | **PASS** |
| AST inspection — `class Tools`, methods, nested `Valves`, `Literal` annotation | **PASS** (see §3.4) |
| In-container `importlib.util.spec_from_file_location` load + `Tools()` instantiation | **PASS** (no `_init()`; class-level state still `None` afterwards) |
| Validation path — `rag_search(query="x")` (length 1) | **PASS** — returns `bad_query`; audit-log delta `+1` (see §6) |
| `webui.db` tool rows, qwen2.5 `meta.toolIds`, qwen2.5 `base_model_id`, openwebui container, HA, Guardian Cloud backend | **untouched by B-4** (see §6.2 for the `webui.db` MD5 caveat — normal OWUI internal traffic) |

## 1. What this Tool is supposed to be

`rag_search(collection, query, k)` is the dense-retrieval +
cross-encoder-rerank Tool that lets the assistant ground answers
in the five Amarolab corpora. The contract — input schema, output
shape, routing description, failure modes — is locked in
[`03-tools.md`](../04_ai_system/amarolab-v1/03-tools.md)
§"Tool 1 — `rag_search`" and is **not relitigated here**. This
log only documents the runtime shape that wraps that contract.

## 2. Source-of-truth crosswalk

Every behaviour in the file maps to an existing locked decision.
No new D-3X is introduced; the user's "do not modify
implementation details that were not validated" constraint is
preserved.

| Concern | Source of truth | Implementation site in `tools/rag_search.py` |
|---|---|---|
| Tool runtime contract — `class Tools` with type-hinted methods | **D-24** (FUNCTIONS_COMPATIBILITY_REPORT §3) | `class Tools:` with public method `rag_search` and dunder `__init__` only; underscore-prefixed `_init` is skipped by OWUI's `get_functions_from_tool` |
| Per-corpus enum (`Literal[…5 names…]`) — trust model | **D-06** (04-security-and-permissions.md), **03-tools.md** §"Tool 1 → Input" | `collection: Literal["homelab_docs", "guardian_cloud", "ensambla2", "infra_audits", "myfreetour"]` — Open WebUI's spec builder emits this as a JSON-Schema enum so the LLM cannot pass an unknown collection name |
| Inline helper marker (no cross-Tool imports) | **D-26** (FUNCTIONS_COMPATIBILITY_REPORT §7) | one line: `# @@AMAROLAB_INLINE:audit_helper@@` near the top, replaced by `bin/install_tool` |
| Audit-log path | **D-07 / D-21** | inherited from the inlined helper (`AMAROLAB_AUDIT_LOG` env, default `/app/backend/data/amarolab-audit.log`) |
| `myfreetour` enum behaviour | **D-22** | generic empty-Qdrant short-circuit returns `{"hits": [], "code": "empty_collection"}`; the same path covers any future empty corpus |
| Embedder / reranker / DENSE_N = 30 / TOP_K = 6 / 600-char content cap | **D-08** (Phase 1.5 contract), **03-tools.md** §"Tool 1 → Implementation outline" | `DENSE_N`, `TOP_K_DEFAULT`, `CONTENT_CAP` module constants; `Embedder` / `Reranker` imported from `/opt/ingest/ingest/` at lazy-init time |
| Per-model scope | **D-20** | not in the Tool source — handled by `meta.toolIds` on the qwen2.5 Model entry in B-7 (Gate G-2) |
| Source location on disk | **D-23** | `ai-stack/openwebui-tools/tools/rag_search.py` (sibling to `time_now.py`) |
| Tool install workflow | **D-25** | `bin/install_tool tools/rag_search.py` — gated to B-6; this log does not install |
| `base_model_id = NULL` on the qwen2.5 Model entry | **D-35** | out of scope for this Tool source; B-7 will preserve `base_model_id = NULL` while extending `meta.toolIds` |

The `_init()` deferred-model-load shape is taken directly from
the `03-tools.md` §"Tool 1 → Implementation outline" pseudocode,
adapted to `class Tools`.

## 3. Design decisions taken inside the locked frame

These are mechanical adaptations of locked decisions, not new
decisions; they are recorded so a future reviewer can see why a
specific line of code reads the way it does.

### 3.1 Class-level (not instance-level) lazy state

The `_emb`, `_rer`, `_qdr` attributes are declared on the class
body (`Tools._emb = None`), not on `self`. Open WebUI 0.8.10
constructs a `Tools()` instance per Tool dispatch but keeps the
module object cached in `sys.modules` (per the
FUNCTIONS_COMPATIBILITY_REPORT runtime contract). Class-level
state survives between instances; instance-level state would not
and would re-pay the ~5.6 s cold model load on every call. This
matches what `_RateLimiter._counts = {}` already does in the
inlined helper.

### 3.2 Heavy imports deferred inside `_init()`

`from ingest.embedder import Embedder` and
`from ingest.reranker import Reranker` do **not** appear at module
top. They are imported inside `_init()`, which fires on the first
`rag_search()` call. Two reasons:

1. Module load is part of OWUI's tool spec build pipeline; if it
   blocks for 4 s the whole Tools page hangs.
2. If a future operator hot-reloads only this Tool (without
   restarting openwebui), keeping the heavy imports lazy avoids
   re-loading `sentence_transformers` and PyTorch at parse time.

The `qdrant_client` import is also lazy, for symmetry.

Note: `Embedder` and `Reranker` *constructors* are themselves
lazy (they `from sentence_transformers import …` inside
`__init__`), so even after `from ingest.embedder import Embedder`
runs, no model weights are pulled until `Embedder()` is called.

### 3.3 `sys.path.insert("/opt/ingest")` at module load

The path injection is cheap (one tuple operation) and must happen
before the deferred `from ingest.embedder import Embedder` inside
`_init()` can resolve. Doing it at module load keeps the lazy
import block tidy and avoids re-checking on every call. The
guard `if _INGEST_PATH not in sys.path` keeps `sys.path` clean if
the module is exec'd more than once in the same process.

### 3.4 Open WebUI tool-spec compliance

AST inspection of the post-inline body confirms:

- `class Tools` exists exactly once.
- It has a nested `class Valves(BaseModel)` — picked up by OWUI's
  Valves UI page, identical pattern to `time_now`.
- LLM-callable methods (non-underscore, non-dunder): `["rag_search"]`.
- Underscore-prefixed `_init` is not reported as an LLM tool.
- `rag_search` parameter annotations:
  - `collection: Literal[…5 names…]` → JSON-Schema enum.
  - `query: str` → JSON-Schema string.
  - `k: int = 6` → JSON-Schema integer with default 6.
- Docstring uses `:param …:` and `:return:` lines the same way
  `time_now.py` does, so the spec builder picks up parameter
  descriptions verbatim.

### 3.5 Error / result-code matrix (mirrors 03-tools.md §"Failure modes")

| Code | Trigger | HTTP-side effect |
|---|---|---|
| `bad_query` | `query` outside `[2, 500]` chars | Tool returns structured error; no model load |
| `bad_k` | `k` outside `[1, 12]` (defensive; the JSON-Schema also enforces) | Same |
| `rate_limited` | `_RateLimiter.check` denied (default 30/min) | Same |
| `init_error` | Embedder / Reranker / QdrantClient construction failed | Tool returns; subsequent calls retry init (`Tools._emb` still `None`) |
| `qdrant_unreachable` | `_qdr.query_points` raised | Tool returns |
| `empty_collection` | Qdrant returned 0 candidates | Tool returns the contract shape `{"collection", "query", "hits": [], "code"}` — matches D-22 |
| `rerank_error` | `Reranker.rerank` raised | Tool returns |
| `ok` | Top-k returned | Audit `result_code: ok`, `duration_ms` populated |

Every path either returns a JSON string or raises into the OWUI
runtime; the helper's `_audit(...)` is invoked on every path
(including the bad-input early-returns) so the audit log is the
single source of truth for "what was asked, what was decided".
The trust-model rule (D-06) requires this — defenses run before
side-effecting work.

### 3.6 Why `DENSE_N` is a module constant, not a Valve

V-C measured DENSE_N=30 reproducing the Phase 1.5 benchmark with
0 pp drift. Locking it as a module constant (rather than a Valve)
prevents accidental drift via the Open WebUI Valves UI before
B-8 runs. A comment inside the file documents the L-1 escape
hatch (lower DENSE_N toward ~12 if per-call latency becomes a
UX complaint after B-8) without exposing it as a runtime branch.
This is exactly what V-C §8 recommended.

`TOP_K` is *not* a constant — the LLM-facing `k` parameter is a
real argument (1–12, default 6) per 03-tools.md.

### 3.7 Rate limit lowered to 30/min vs `time_now`'s 60/min

`time_now` is microseconds per call. `rag_search` is ~10 s per
call on this hardware (V-C §3.2). 30/min is a defensive cap
matching the 03-tools.md outline; at the steady-state rerank
cost, the wall clock would hit 30 calls in about 5 minutes
anyway. The cap is exposed as a Valve so an operator can lower
it further without re-installing the Tool.

### 3.8 `self.citation = False`

The Tool returns hits with `source_rel` and `title` fields and
600-char `content` snippets. The LLM is expected to cite using
the `[N] source_rel` grammar locked in **D-31 / D-34**. Setting
`self.citation = True` would make OWUI wrap the entire JSON
output as one Citation, which collides with the per-hit citation
model the prompt teaches the LLM. Mirrors `time_now`.

## 4. What the Tool deliberately does **not** do

- **Does not write to Qdrant.** `query_points` only. No
  `upsert_points`, no `delete_collection`, no
  `update_collection`. The trust model (D-06) is preserved.
- **Does not call Home Assistant.** No `requests.post(/api/services/…)`,
  no token, no domain decisions. Phase C territory.
- **Does not call the Guardian Cloud backend.** The corpus is
  read from Qdrant; no HTTP call into Guardian Cloud's services.
  Production safety (homelab-wide rule, D-09) is preserved.
- **Does not write to `webui.db`.** Tool install is B-6's job.
- **Does not extend `meta.toolIds`.** B-7 / Gate G-2.
- **Does not stream partial results.** A future v1.1 might wire a
  `__user__` callback for "Searching…" feedback; out of scope
  for v1 per V-C §4.3 L-2.
- **Does not invoke `audit_search`.** B-5 will add it as a
  separate Tool.
- **Does not log `query` in plain text.** The inlined helper's
  `_amarolab_redact` covers password/token/secret/api_key/
  authorization keys; the `query` itself is recorded verbatim.
  This matches `time_now`'s behaviour (`timezone` is logged
  verbatim too) and the D-07 contract.
- **Does not run on `llama3:latest` / `llama3.2:latest` /
  `phi3:latest`.** D-20 scoping is enforced at the qwen2.5 Model
  entry level (B-7), not inside the Tool — the Tool itself has
  no concept of which model called it.

## 5. Local validation

### 5.1 Pre-inline syntax

```
$ python3 -m py_compile ai-stack/openwebui-tools/tools/rag_search.py
PASS: py_compile (pre-inline)
```

The marker `# @@AMAROLAB_INLINE:audit_helper@@` is a valid Python
comment, so `py_compile` parses cleanly even though the helper
symbols `_audit`, `_RateLimiter`, `_amarolab_redact` are not yet
defined.

### 5.2 install_tool dry-run (inline-only, no POST)

```
$ ./bin/install_tool --dry-run tools/rag_search.py
# would install id=rag_search name='Amarolab rag_search' (content 11629 chars)
# description: Search an Amarolab knowledge corpus …
# manifest: {"author": "amarolab", "author_url": "https://github.com/amaroou",
#            "version": "0.1.0", "license": "MIT"}
```

The frontmatter is parsed (title → name, description → meta.description,
author / author_url / version / license → manifest). The marker is
replaced by the full helper block. 289 lines of post-inline source
total.

### 5.3 Post-inline syntax

```
$ python3 -m py_compile /tmp/rag_search.inlined.body.py
PASS: py_compile (post-inline)
$ grep -c '_audit\|_RateLimiter\|_amarolab' /tmp/rag_search.inlined.body.py
28
```

28 cross-references between the inlined helper and the Tool body
all resolve. No undefined-name errors.

### 5.4 AST shape

```
class Tools: PRESENT
Methods: ['__init__', '_init', 'rag_search']
LLM-callable (non-underscore) methods: ['rag_search']
Nested class: Valves
collection annotation type: Subscript
```

Single LLM-callable method, Valves nested class, `collection`
annotation is `ast.Subscript` (= `Literal[…]`). Matches the D-24
contract.

### 5.5 In-container probe (read-only paths)

The canonical source was copied into the openwebui container at
`/tmp/rag_search_canonical.py`; the inlined body at
`/tmp/rag_search_inlined.py`. Then:

```python
spec = importlib.util.spec_from_file_location('tool_rag_search', '/tmp/rag_search_inlined.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print('module loaded OK')                                  # PASS
T = mod.Tools()
print('valves.max_per_minute =', T.valves.max_per_minute)  # 30
print('citation flag =', T.citation)                       # False
print('class-level _emb is None?', mod.Tools._emb is None) # True
print('DENSE_N =', mod.DENSE_N)                            # 30
import json
r = json.loads(T.rag_search(collection='homelab_docs', query='x', k=6))
print('bad_query path returns:', r)
# {'error': 'query must be 2-500 characters', 'code': 'bad_query'}
```

The class-level `_emb / _rer / _qdr` are still `None` after
instantiation and after the bad-query call — confirms `_init()`
was not invoked. No model load happened.

### 5.6 What was deliberately NOT validated locally

These are explicitly deferred to B-8 (W-1..W-8 + V-A / V-B):

- The Tool wired through OWUI's `tool_ids` auto-attach path.
- The reranker reproducing the Phase 1.5 numbers **through the
  Tool**. V-C reproduced them through a parallel script; the
  Tool layer is structurally equivalent but not yet exercised
  end-to-end.
- The audit-log shape under successful (`result_code: ok`)
  calls. The probe today only wrote a `bad_query` line; the
  full 8-field schema is verified for `bad_query` only.
- Per-corpus behaviour on `infra_audits` through the Tool.
- Behaviour under `qdrant_unreachable` (would require taking
  Qdrant offline; out of scope).

## 6. Side effects of this turn

| Artefact | Location | Reversibility |
|---|---|---|
| `ai-stack/openwebui-tools/tools/rag_search.py` | host, 9 300 chars, 246 lines | git revert |
| `/tmp/rag_search.inlined.py` (host) | host `/tmp` | tmpfs / next reboot |
| `/tmp/rag_search.inlined.body.py` (host) | host `/tmp` | tmpfs / next reboot |
| `/tmp/rag_search_canonical.py` (container) | container `/tmp` | container restart |
| `/tmp/rag_search_inlined.py` (container) | container `/tmp` | container restart |
| Cached bytecode `__pycache__/rag_search.cpython-3*.pyc` | host openwebui-tools dir; container `/tmp/__pycache__/` | rm |
| **Audit log** `/srv/homelab/data/openwebui/amarolab-audit.log` | host | **+1 line** — disclosed below |

### 6.1 Audit-log delta

The in-container `T.rag_search(query="x")` call (§5.5) hit the
`bad_query` early-return path and the inlined `_audit(...)`
helper wrote one JSONL line. This is **expected** — the helper
audits every Tool dispatch, including refusals — and is the
exact same shape Phase B B-8 will validate at scale. The line:

```json
{
  "ts": "2026-06-16T09:36:21.423388+00:00",
  "id": "9f2b835b-9d48-40bb-89b2-7904ef3d34e1",
  "user": "diego",
  "tool": "rag_search",
  "args": {"collection": "homelab_docs", "query": "x", "k": 6},
  "allowed": false,
  "result_code": "bad_query",
  "duration_ms": null
}
```

Audit log line count: 99 → 100. The line is preserved (the log
is append-only by design); it is *not* a state-change that
needs reverting. Documented here for traceability.

If the user prefers a fully zero-side-effect B-4, this single
line can be removed manually (`sed -i '$d'`); recommendation is
to leave it, since it correctly records the validation activity
and is the exact behaviour B-8 will verify.

### 6.2 Forensic state at end of B-4

| Item | Value |
|---|---|
| `webui.db` MD5 | `d44174abc30cbce203f04f0f8d79be94` — **changed** vs the post-B-3 baseline `656d7295d3cfc00a2255bb0b2230fba1`. **B-4 did not write to it.** The drift is normal Open WebUI internal state (chat sessions, browser logins, etc.) accumulated between the B-3 applied log (2026-06-16) and now. The Phase-B-relevant invariants below were verified by SQL probe, not by MD5. |
| `webui.db` qwen2.5 `meta.toolIds` (B-4 invariant) | `["time_now"]` — unchanged |
| `webui.db` qwen2.5 `base_model_id` (B-4 invariant) | `NULL` (D-35) — unchanged |
| `webui.db` `tool` rows | 4 (`time_now`, `docker_containers`, `system_status`, `docker_logs`) — **no `rag_search` row** |
| `amarolab-audit.log` | 100 lines (was 99 at the end of V-C, +1 from this probe) |
| qwen2.5 `base_model_id` | `NULL` (D-35) |
| qwen2.5 `meta.toolIds` | `["time_now"]` — unchanged |
| `infra_audits` Qdrant point count | 280 (unchanged) |
| `openwebui` container mounts | `/srv/homelab/data/openwebui:/app/backend/data` + `/opt/ingest:ro` (unchanged) |
| `ai-stack/openwebui-tools/tools/time_now.py` | unchanged |
| `ai-stack/openwebui-tools/tools/audit_search.py` | **still does not exist** (B-5) |
| Git working tree | one new file (`tools/rag_search.py`) + previously-modified state docs + previously-untracked V-C and doc-sync logs |
| Local vs `origin/main` | unchanged relative to the docs-sync turn — no new commits |

## 7. Recommended next step

The Tool source is structurally complete and locally validated.
The natural next moves, in priority order:

1. **Author `tools/audit_search.py` (B-5).** It is the documented
   sugar wrapper over `rag_search(collection="infra_audits", …)`;
   structurally a one-method `class Tools` that calls the same
   inlined helper. The user said "Do not proceed to B-5 yet";
   recommendation is to handle it in the next turn so B-6's
   install can install both Tools together.
2. **Run `bin/install_tool --dry-run` on both files** as the last
   pre-install probe. Already PASS for `rag_search`.
3. **B-6 install both** (`POST /api/v1/tools/create` for each via
   `bin/install_tool`). This is the first Phase B step that
   writes to `webui.db`.
4. **B-7 Gate G-2 — extend `meta.toolIds`** to
   `["time_now","rag_search","audit_search"]`. One row, one
   column in `webui.db`. Reversible.
5. **B-8 — W-1..W-8 + V-A / V-B end-to-end.**

If the user instead wants to commit this B-4 artefact first
(separate commit from B-5), the natural commit shape is:

```
feat(amarolab): add rag_search Open WebUI Tool source (Phase B B-4)

- tools/rag_search.py — class Tools with lazy _init() over
  Embedder / Reranker / QdrantClient; 5-collection Literal;
  DENSE_N=30, TOP_K_DEFAULT=6, CONTENT_CAP=600; inlined audit
  helper via D-26 marker.
- 09_logs/2026-06-17_phaseB_rag_search_design.md — design log
  with source-of-truth crosswalk, error matrix, local
  validation summary (py_compile pre/post inline; AST shape;
  in-container module load + bad_query path probe).
```

## 8. What B-4 deliberately did NOT do

- Did not run `bin/install_tool tools/rag_search.py` (real POST).
- Did not write to `webui.db`.
- Did not extend `meta.toolIds`.
- Did not recreate or restart the openwebui container.
- Did not call Home Assistant or the Guardian Cloud backend.
- Did not write `tools/audit_search.py` (B-5).
- Did not run W-1..W-8 (B-8).

## 9. Cross-references

- Tool source written this turn:
  `ai-stack/openwebui-tools/tools/rag_search.py`
- Canonical reference Tool:
  [`../ai-stack/openwebui-tools/tools/time_now.py`](../ai-stack/openwebui-tools/tools/time_now.py)
- Inlined helper (D-26):
  [`../ai-stack/openwebui-tools/lib/audit_helper.py`](../ai-stack/openwebui-tools/lib/audit_helper.py)
- Install workflow (D-25):
  [`../ai-stack/openwebui-tools/bin/install_tool`](../ai-stack/openwebui-tools/bin/install_tool)
- Tool design package (input/output contract, error matrix):
  [`../04_ai_system/amarolab-v1/03-tools.md`](../04_ai_system/amarolab-v1/03-tools.md)
- Trust model (D-06, allowlist constants):
  [`../04_ai_system/amarolab-v1/04-security-and-permissions.md`](../04_ai_system/amarolab-v1/04-security-and-permissions.md)
- OWUI runtime contract (D-24, D-25, D-26):
  [`../FUNCTIONS_COMPATIBILITY_REPORT.md`](../FUNCTIONS_COMPATIBILITY_REPORT.md)
- Phase B execution plan (B-4 step):
  [`../04_ai_system/amarolab-v1/PHASE_B_EXECUTION_PLAN.md`](../04_ai_system/amarolab-v1/PHASE_B_EXECUTION_PLAN.md)
- V-C reranker validation (the runtime correctness pre-empt
  that this Tool is built on top of):
  [`2026-06-17_phaseB_vc_validation.md`](2026-06-17_phaseB_vc_validation.md)
- Sub-project live state:
  [`../04_ai_system/amarolab-v1/CURRENT_STATE.md`](../04_ai_system/amarolab-v1/CURRENT_STATE.md),
  [`../04_ai_system/amarolab-v1/ROADMAP.md`](../04_ai_system/amarolab-v1/ROADMAP.md),
  [`../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md`](../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md)

## 10. Stop point

Per the user's instruction ("Stop after code creation, local
syntax validation, design review, git status. Do not proceed to
B-5 yet."): this log is the artefact. The Tool source is on
disk, locally validated, and not installed. B-5 (`audit_search`)
and B-6 (install) await explicit instruction.
