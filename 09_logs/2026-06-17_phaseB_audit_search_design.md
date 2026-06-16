# Phase B B-5 — `audit_search` Tool source (design + local validation)

- **Date:** 2026-06-17.
- **Goal:** author `tools/audit_search.py` as the canonical
  version-controlled source for the `audit_search` Open WebUI
  Tool, mirroring `rag_search.py` (B-4) with a hardcoded
  `collection = "infra_audits"`. Validate locally (syntax,
  install-time inline, AST shape, in-container import + two
  validation paths). **Do not install.** Do not edit `webui.db`,
  `meta.toolIds`, the openwebui container, Home Assistant, or
  the Guardian Cloud backend.
- **Inputs:**
  [`../04_ai_system/amarolab-v1/03-tools.md`](../04_ai_system/amarolab-v1/03-tools.md)
  §"Tool 2 — `audit_search`" (input / output schema, sugar
  rationale);
  [`../ai-stack/openwebui-tools/tools/rag_search.py`](../ai-stack/openwebui-tools/tools/rag_search.py)
  (the B-4 mirror target);
  [`../ai-stack/openwebui-tools/lib/audit_helper.py`](../ai-stack/openwebui-tools/lib/audit_helper.py)
  (D-26 inlined helper);
  [`2026-06-17_phaseB_rag_search_design.md`](2026-06-17_phaseB_rag_search_design.md)
  (B-4 design log — every rationale below either mirrors B-4 or
  documents a deliberate divergence);
  [`2026-06-16_phaseB_infra_audits_applied.md`](2026-06-16_phaseB_infra_audits_applied.md)
  (the corpus this Tool targets).

## 0. TL;DR

**`tools/audit_search.py` is on disk, syntax-clean both before
and after install-time inlining, AST-shape compliant with D-24,
and import-loads inside the openwebui container without invoking
`_init()`.** The two validation paths (`bad_query` and `bad_k`)
were exercised end-to-end and returned the contract-shaped
errors; both produced one audit-log line each. The Tool is not
installed in `webui.db`; B-6 owns that.

| Check | Result |
|---|---|
| `python3 -m py_compile tools/audit_search.py` (pre-inline) | **PASS** |
| `bin/install_tool --dry-run tools/audit_search.py` | **PASS** — id=`audit_search`, name=`Amarolab audit_search`, 11 231 chars, manifest extracted |
| `python3 -m py_compile` on the inlined body | **PASS** (29 cross-references between helper and Tool body resolve) |
| AST — `class Tools`, methods=`['__init__','_init','audit_search']`, LLM-callable=`['audit_search']`, nested `Valves`, `audit_search` args=`['self','query','k']` | **PASS** |
| In-container module load + `Tools()` instantiation + class-level state check | **PASS** (`_emb` still `None` afterwards) |
| Validation path — `audit_search(query="x")` | **PASS** — returns `bad_query` |
| Validation path — `audit_search(query=…, k=20)` | **PASS** — returns `bad_k` |
| `webui.db` tool rows, qwen2.5 `meta.toolIds`, qwen2.5 `base_model_id`, openwebui container, HA, Guardian Cloud backend | **untouched by B-5** |

## 1. What this Tool is supposed to be

`audit_search(query, k)` is the documented "schema-level
shortcut" over `rag_search(collection="infra_audits", …)`.
[`03-tools.md`](../04_ai_system/amarolab-v1/03-tools.md)
§"Tool 2" makes the rationale explicit:

> A separate tool entry in the schema makes the LLM's
> auto-routing more reliable than a single tool with five
> different collection choices.

The LLM-facing contract is `query` + `k` only; the collection is
implicit in the tool name. The runtime contract (D-26) requires
the implementation to be self-contained — see §3.1 below — so
internally this Tool re-runs the same pipeline as `rag_search`
with `collection` hardcoded to `infra_audits`.

## 2. Source-of-truth crosswalk

Every behaviour in `audit_search.py` maps to an existing locked
decision or to its B-4 counterpart. No new D-3X is introduced.

| Concern | Source of truth | Implementation site |
|---|---|---|
| Tool runtime contract — `class Tools` with type-hinted methods | **D-24** (FUNCTIONS_COMPATIBILITY_REPORT §3) | `class Tools:` with single public method `audit_search`; underscore `_init` is skipped by OWUI |
| Hardcoded `collection = "infra_audits"` | **D-22** + 03-tools.md §"Tool 2 → Input" | module constant `_COLLECTION = "infra_audits"` (underscored so OWUI does not pick it up as a Tool attribute), referenced inside the method body |
| Same pipeline as `rag_search` | **D-08** (Phase 1.5 contract), **03-tools.md** §"Tool 2 → Output: Same shape as rag_search" | identical `Embedder` / `Reranker` / `QdrantClient` chain, identical `DENSE_N=30`, `TOP_K_DEFAULT=6`, `CONTENT_CAP=600`, identical error matrix |
| Inline helper marker | **D-26** | one line: `# @@AMAROLAB_INLINE:audit_helper@@` near the top, replaced by `bin/install_tool` |
| Audit-log path + `_audit` semantics | **D-07 / D-21** | inherited from the inlined helper; `tool="audit_search"` field distinguishes the two Tools in grep |
| Per-model scope | **D-20** | not in the Tool source — handled by `meta.toolIds` on the qwen2.5 Model entry in B-7 (Gate G-2) |
| Source location on disk | **D-23** | `ai-stack/openwebui-tools/tools/audit_search.py` (sibling to `rag_search.py`) |
| Tool install workflow | **D-25** | `bin/install_tool tools/audit_search.py` — B-6 |

## 3. Decisions taken inside the locked frame

### 3.1 Why audit_search does not import rag_search

The cleanest expression of the sugar relationship would be:

```python
from rag_search import Tools as RagTools
def audit_search(query, k=6):
    return RagTools().rag_search(collection="infra_audits", query=query, k=k)
```

That **does not work** under D-26. Open WebUI 0.8.10 executes
each installed Tool inside its own `tool_{id}` module namespace
via `exec()`; cross-Tool `import` statements do not resolve.
This is exactly the constraint that led to the
`# @@AMAROLAB_INLINE:audit_helper@@` convention in the first
place.

The supported workaround per the
[`../FUNCTIONS_COMPATIBILITY_REPORT.md`](../FUNCTIONS_COMPATIBILITY_REPORT.md)
§7 is: textually inline the shared logic. For the audit-helper
(~30 lines) the inline-via-marker pattern is built in. For the
~150-line `rag_search` pipeline body, doing the same marker
dance would be over-engineered for v1 — it would also bind
`audit_search` to a specific snapshot of `rag_search`, masking
later bug fixes.

The chosen path is therefore: **straight duplication of the
pipeline body**. `audit_search.py` carries its own copy of
input validation, lazy `_init()`, embed → Qdrant → rerank,
content-cap, and audit calls. The diff against `rag_search.py`
is small (see §3.5).

### 3.2 Class-level state is independent of rag_search's

`audit_search.Tools._emb` is a *different* class attribute from
`rag_search.Tools._emb`. Both modules live in `sys.modules`
independently, and Python class attributes are per-class. This
means the first `audit_search` call pays the full ~5.6 s cold
load (Embedder 4.19 s + Reranker 1.35 s, per V-C §3.1) *again*,
even if `rag_search` already warmed up.

This is a known cost of D-26 and is documented in the file
header comment. RAM headroom is ample on this host
(~15 GB free with qwen2.5 warm; two ST instances cost ~6 GB),
so no mitigation is in scope for v1. A possible v1.1 follow-up
is a `sys.modules`-based singleton shared between the two
Tools; that requires modifying both Tools and is deferred.

### 3.3 What the docstring teaches the LLM

The LLM-facing docstring is the only signal the model uses to
choose `audit_search` vs `rag_search(collection="infra_audits")`.
It must be unambiguous. The chosen wording:

> Call this for questions about audits, sanitization, migration,
> what was applied in Phase 0/1, the current state of a specific
> R-XX remediation item, or the history of any infrastructure
> change recorded in the audit reports. Prefer this over
> rag_search when the question is about audits or past infra
> work; the collection is hardcoded so you do not need to pass
> it.

Three intent signals: (1) keyword anchors (`audit`, `Phase 0/1`,
`R-XX`), (2) explicit preference statement, (3) "no collection
arg needed" — the last is necessary because `rag_search`'s
docstring also mentions `infra_audits`, and the LLM needs to
know `audit_search` is the simpler, more reliable path.

### 3.4 args_snap drops the `collection` field

The audit-log `args` field carries the runtime-supplied
parameters only:

```json
"args": {"query": "what was applied in Phase 0", "k": 6}
```

Not `{"collection": "infra_audits", "query": ..., "k": ...}`.
Rationale: the `tool` field is `"audit_search"` and the
implicit collection is part of the tool identity, not an
argument. Matches the time_now precedent
(`args = {"timezone": tz, "format": format}` — only the
caller-supplied parameters). The audit log is still
unambiguous: `tool=audit_search` ↔ `collection=infra_audits`
is a 1:1 mapping by construction.

### 3.5 Diff vs `rag_search.py` (the mirror target)

`diff -u tools/rag_search.py tools/audit_search.py | wc -l`
shows the structural delta is small:

- Frontmatter title + description differ (Tool identity).
- `from typing import Literal` removed (no Literal arg).
- Top-of-file comments adapted to reference `rag_search.py`.
- New module constant `_COLLECTION = "infra_audits"` and its
  rationale comment.
- Two comments adjusted: the `_emb`/`_rer`/`_qdr` block
  documents the independent-from-rag_search caveat; the
  `_init` deferred-import comment cross-references
  `rag_search.py`.
- Method renamed `rag_search` → `audit_search`; signature
  drops the `collection: Literal[...]` parameter.
- Method docstring rewritten with audit-corpus routing
  language (see §3.3).
- Every `audit_search`-equivalent body line uses `_COLLECTION`
  instead of the parameter; every `_audit(...)` call passes
  `"audit_search"` as the tool name and an args dict without
  `collection`.

Pipeline body, input-validation logic, error matrix, and
return shape are byte-identical to `rag_search.py` modulo
those substitutions.

### 3.6 Error / result-code matrix

Identical to `rag_search.py` minus the `bad_collection` path
(unreachable because no `collection` parameter exists):

| Code | Trigger |
|---|---|
| `bad_query` | `query` outside `[2, 500]` chars |
| `bad_k` | `k` outside `[1, 12]` |
| `rate_limited` | `_RateLimiter.check` denied (default 30/min) |
| `init_error` | Embedder / Reranker / QdrantClient construction failed |
| `qdrant_unreachable` | `_qdr.query_points` raised |
| `empty_collection` | Qdrant returned 0 hits on `infra_audits` (unexpected — 280 chunks indexed) |
| `rerank_error` | `Reranker.rerank` raised |
| `ok` | Top-k returned |

The `empty_collection` path is kept defensively. With 280
chunks in `infra_audits` (from B-2), Qdrant should always
return ≥ 1 candidate for any sane query; if `cands == []` we
still want a structured response, not a 500.

### 3.7 Why audit logging is preserved unchanged

The user's B-5 requirement explicitly calls out "Preserve audit
logging". Concretely:

- Same `_audit(tool, args, allowed, result_code, duration_ms)`
  signature on every branch (early returns and happy path).
- Same `tool` field per call — `"audit_search"` (not
  `"rag_search"`).
- Same args-redaction path via the inlined `_amarolab_redact`
  (audit_search's args don't carry any redaction-keyword keys
  in practice, but the helper applies uniformly).
- Same audit-log file path — `AMAROLAB_AUDIT_LOG` env
  (default `/app/backend/data/amarolab-audit.log`).
- Same JSON Lines shape — 8 fields, one per call, append-only.

A future operator grepping the audit log gets a clean
`rag_search` vs `audit_search` partition.

## 4. What the Tool deliberately does **not** do

- **Does not write to Qdrant.** `query_points` only.
- **Does not call Home Assistant or the Guardian Cloud backend.**
- **Does not write to `webui.db` / extend `meta.toolIds` /
  recreate the openwebui container.**
- **Does not import or call `rag_search`** — D-26 prevents it
  cleanly; see §3.1.
- **Does not stream partial results / progress indicators.**
- **Does not return a different schema from `rag_search`'s.**
  `collection` field in the response is always `"infra_audits"`
  for grep parity.
- **Does not relax the rate limit** even though some operators
  might want a higher cap for audit-corpus queries. Same 30/min
  default; same Valves override path.

## 5. Local validation

### 5.1 Pre-inline syntax

```
$ python3 -m py_compile ai-stack/openwebui-tools/tools/audit_search.py
PASS: py_compile (pre-inline)
```

### 5.2 install_tool dry-run

```
$ ./bin/install_tool --dry-run tools/audit_search.py
# would install id=audit_search name='Amarolab audit_search' (content 11231 chars)
# description: Search the infra_audits corpus (past infrastructure audit reports
#              and Phase 0/1 application logs) with dense retrieval + cross-encoder
#              reranking. A schema-level shortcut over
#              rag_search(collection="infra_audits", ...); use this whenever the
#              user asks about audits, Phase 0/1 work, or the current state of a
#              specific R-XX item.
# manifest: {"author": "amarolab", "author_url": "https://github.com/amaroou",
#            "version": "0.1.0", "license": "MIT"}
```

Inlined output is 282 lines (vs `rag_search.py`'s 289 — the
delta is the missing `collection` Literal block in the method
signature and slightly tighter comments).

### 5.3 Post-inline syntax

```
$ python3 -m py_compile /tmp/audit_search.inlined.body.py
PASS: py_compile (post-inline)
$ grep -c '_audit\|_RateLimiter\|_amarolab' /tmp/audit_search.inlined.body.py
29
```

### 5.4 AST shape

```
Methods: ['__init__', '_init', 'audit_search']
LLM-callable: ['audit_search']
Nested classes: ['Valves']
audit_search args: ['self', 'query', 'k']
```

No `collection` argument — confirms the schema-level
simplification the design called for.

### 5.5 In-container probe

```python
spec = importlib.util.spec_from_file_location('tool_audit_search', '/tmp/audit_search_inlined.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print('module loaded OK')                                # PASS
T = mod.Tools()
print('valves.max_per_minute =', T.valves.max_per_minute) # 30
print('citation flag =', T.citation)                     # False
print('class-level _emb is None?', mod.Tools._emb is None) # True
print('_COLLECTION =', mod._COLLECTION)                  # infra_audits

import json
r = json.loads(T.audit_search(query='x', k=6))
print('bad_query path:', r)
# {'error': 'query must be 2-500 characters', 'code': 'bad_query'}
r = json.loads(T.audit_search(query='what was applied in Phase 0', k=20))
print('bad_k path:', r)
# {'error': 'k must be an integer between 1 and 12', 'code': 'bad_k'}
```

Both validation paths returned the contract-shaped error
without invoking `_init()` (class-level state still `None`
afterwards).

### 5.6 What was deliberately NOT validated locally

Deferred to B-8 (W-1..W-8 + V-A / V-B):

- The Tool wired through OWUI's `tool_ids` auto-attach path.
- The reranker reproducing Phase 1.5 numbers **through the
  Tool**.
- The audit-log shape under successful `result_code: ok`
  calls.
- Behaviour under `qdrant_unreachable`.
- Behaviour under `empty_collection` (would require pointing
  the Tool at an empty corpus or temporarily wiping
  `infra_audits`).
- Routing arbitration between `audit_search` and `rag_search`
  by the qwen2.5 system prompt — W-3 specifically covers
  "What was applied in Phase 0?" → `audit_search`.

## 6. Side effects of this turn

| Artefact | Location | Reversibility |
|---|---|---|
| `ai-stack/openwebui-tools/tools/audit_search.py` | host, 222 lines | git revert |
| `/tmp/audit_search.inlined.py` (host) | host `/tmp` | tmpfs / next reboot |
| `/tmp/audit_search.inlined.body.py` (host) | host `/tmp` | tmpfs / next reboot |
| `/tmp/audit_search_inlined.py` (container) | container `/tmp` | container restart |
| Cached bytecode `__pycache__/audit_search.cpython-3*.pyc` | host openwebui-tools dir; container `/tmp/__pycache__/` | rm |
| **Audit log** `/srv/homelab/data/openwebui/amarolab-audit.log` | host | **+2 lines** — see §6.1 |

### 6.1 Audit-log delta

Two lines, one from each validation probe, both following the
same shape `time_now` and `rag_search` already use:

```json
{"ts":"2026-06-16T09:46:23.451655+00:00","id":"fa30ff17-...","user":"diego","tool":"audit_search","args":{"query":"x","k":6},"allowed":false,"result_code":"bad_query","duration_ms":null}
{"ts":"2026-06-16T09:46:23.451789+00:00","id":"d62690f5-...","user":"diego","tool":"audit_search","args":{"query":"what was applied in Phase 0","k":20},"allowed":false,"result_code":"bad_k","duration_ms":null}
```

Audit-log line count: 100 → 102. Append-only; not reverted.
Documented for traceability.

### 6.2 Forensic state at end of B-5

| Item | Value |
|---|---|
| `webui.db` MD5 | drifting under normal OWUI traffic; the B-5-relevant invariants are below, verified by SQL probe |
| `webui.db` qwen2.5 `meta.toolIds` | `["time_now"]` — unchanged |
| `webui.db` qwen2.5 `base_model_id` | `NULL` (D-35) — unchanged |
| `webui.db` `tool` rows | 4 (`time_now`, `docker_containers`, `system_status`, `docker_logs`) — **no `audit_search` row** |
| `amarolab-audit.log` | 102 lines (was 100 at end of B-4; +2 from B-5 probes) |
| `infra_audits` Qdrant point count | 280 (unchanged) |
| `openwebui` container mounts | unchanged |
| `ai-stack/openwebui-tools/tools/rag_search.py` | committed at `a7995b3f`; unchanged this turn |
| `ai-stack/openwebui-tools/tools/audit_search.py` | **new this turn** |
| Git working tree | one new file (`tools/audit_search.py`) + this log |
| Local vs `origin/main` | unchanged relative to B-4 — no new commits |

## 7. Recommended next step

The two Phase B Tool source files (`tools/rag_search.py` from
B-4, `tools/audit_search.py` from B-5) are both:

- locally validated (syntax pre + post inline; AST shape; in-
  container module load; validation paths exercised);
- not installed in `webui.db`;
- not visible to any model (qwen2.5 `meta.toolIds` still
  `["time_now"]`).

The natural next move is **B-6 — install both Tools** via
`bin/install_tool` (two `POST /api/v1/tools/create` calls,
one per Tool). This is the first Phase B step that writes to
`webui.db` and is reversible by `DELETE /api/v1/tools/id/{id}`.

If the user prefers to commit this B-5 artefact first:

```
feat(amarolab): add audit_search Open WebUI Tool source (Phase B B-5)

- tools/audit_search.py — class Tools with the same lazy
  _init()/Embedder/Reranker/QdrantClient pipeline as
  rag_search.py, but with collection hardcoded to "infra_audits"
  and the LLM-facing schema simplified to (query, k). Inlined
  audit helper via D-26 marker. Identical error matrix +
  audit-log shape; tool="audit_search" distinguishes the two
  Tools in grep.
- 09_logs/2026-06-17_phaseB_audit_search_design.md — design log
  documenting the mirror, the D-26 reason audit_search cannot
  import rag_search, and the local validation summary.
```

## 8. What B-5 deliberately did NOT do

- Did not run `bin/install_tool tools/audit_search.py` (real POST).
- Did not write to `webui.db`.
- Did not extend `meta.toolIds`.
- Did not recreate or restart the openwebui container.
- Did not call Home Assistant or the Guardian Cloud backend.
- Did not edit `tools/rag_search.py` (B-4 artefact preserved).
- Did not run W-1..W-8 (B-8).
- Did not invoke the full embed/rerank pipeline (no `_init()`
  call; class-level state still `None` post-probe).

## 9. Cross-references

- Tool source written this turn:
  `ai-stack/openwebui-tools/tools/audit_search.py`
- B-4 sibling Tool (the mirror target):
  [`../ai-stack/openwebui-tools/tools/rag_search.py`](../ai-stack/openwebui-tools/tools/rag_search.py)
- B-4 design log (shared rationale):
  [`2026-06-17_phaseB_rag_search_design.md`](2026-06-17_phaseB_rag_search_design.md)
- Inlined helper (D-26):
  [`../ai-stack/openwebui-tools/lib/audit_helper.py`](../ai-stack/openwebui-tools/lib/audit_helper.py)
- Tool design package (input/output contract):
  [`../04_ai_system/amarolab-v1/03-tools.md`](../04_ai_system/amarolab-v1/03-tools.md)
- Trust model (D-06):
  [`../04_ai_system/amarolab-v1/04-security-and-permissions.md`](../04_ai_system/amarolab-v1/04-security-and-permissions.md)
- OWUI runtime contract (D-24, D-25, D-26):
  [`../FUNCTIONS_COMPATIBILITY_REPORT.md`](../FUNCTIONS_COMPATIBILITY_REPORT.md)
- Phase B execution plan (B-5 step):
  [`../04_ai_system/amarolab-v1/PHASE_B_EXECUTION_PLAN.md`](../04_ai_system/amarolab-v1/PHASE_B_EXECUTION_PLAN.md)
- V-C reranker validation (the runtime correctness pre-empt
  the audit pipeline is built on):
  [`2026-06-17_phaseB_vc_validation.md`](2026-06-17_phaseB_vc_validation.md)
- `infra_audits` corpus apply log (the corpus this Tool reads):
  [`2026-06-16_phaseB_infra_audits_applied.md`](2026-06-16_phaseB_infra_audits_applied.md)
- Sub-project live state:
  [`../04_ai_system/amarolab-v1/CURRENT_STATE.md`](../04_ai_system/amarolab-v1/CURRENT_STATE.md),
  [`../04_ai_system/amarolab-v1/ROADMAP.md`](../04_ai_system/amarolab-v1/ROADMAP.md),
  [`../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md`](../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md)

## 10. Stop point

Per the user's instruction ("Stop after code creation, local
validation, design review, git status. Do not proceed to B-6."):
this log is the artefact. The Tool source is on disk, locally
validated, and not installed. B-6 (install both via
`bin/install_tool`) awaits explicit instruction.
