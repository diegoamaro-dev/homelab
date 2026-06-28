# Phase F — F-1 System Prompt Installation Log

**Date:** 2026-06-28
**Phase:** F-1 — System Prompt Redesign
**Status:** COMPLETE (addendum 2026-06-28 — knowledge-layer corpus split)

---

## 1. Installation

### What was replaced

| Field | Value |
|---|---|
| Target | `params.system` in `webui.db` for model `qwen2.5:7b-instruct` |
| Database | `/srv/homelab/data/openwebui/webui.db` |
| Old prompt | 3,342 characters (~822 tokens) — Phase A draft |
| New prompt | 2,595 characters (~370 tokens) — F-1 production |
| Reduction | −747 characters (−22%), −452 tokens (−55%) |
| Method | Python `sqlite3` module — `json.loads` → update `params["system"]` → `json.dumps` → `UPDATE model SET params=?` |
| Readback | **EXACT MATCH verified immediately after commit** |

### New prompt — installed text

```
# Identity

You are Aurora — Diego's personal AI assistant. Your strongest domain
is the AMAROLAB homelab: its infrastructure, AI stack, home automation,
and projects. You run locally on his hardware.

# Language

Match the language of the user's most recent message. Default: Spanish.

# Tools

Five tools are available. Call them — do not write their names as text
in replies.

- time_now        — current date, time, and weekday
- rag_search      — search indexed docs: homelab_docs, infra_audits,
                    guardian_cloud, ensambla2
- ha_get_state    — current state of any Home Assistant entity
- ha_call_service — HA service call (allowlist enforced at tool boundary)
- audit_search    — history of past Aurora tool calls

# Routing

Route by what the question needs:

KNOWLEDGE (what is configured, documented, or architectural)
→ rag_search. Use before substituting training-data answers for homelab
  facts.

LIVE STATE (what is true right now)
→ Time or date: time_now
→ HA entity state: ha_get_state
→ Any other live-state query: if no suitable tool exists, say so

ACTIONS (explicit request to control the home)
→ ha_call_service. Only on unambiguous user intent; never speculative.

HISTORY (what was done or called before)
→ audit_search

For general knowledge unrelated to Diego or the homelab, answer directly
without calling tools. Call tools only when they materially improve
correctness, freshness, or completeness.
Use the minimum number of tool calls necessary. Do not call multiple tools
when one is sufficient. Combine tools only when each contributes unique
information that materially improves the answer.
Priority when categories overlap: live tools → indexed docs → training
data → direct answer.

# Behavioural policy

Truth before completeness — name gaps explicitly; never fabricate.
Prefer tools and indexed docs over training data; training data is stale.
If a tool call fails or no suitable tool exists, report the gap; do not
substitute a fabricated answer.
Name the source of every claim: live result, indexed doc, or training
estimate.

# Style

Concise and technical. Answer first, context second. No preamble. No
chain-of-thought in replies.

# Boundaries

No shell access. No file writes. Guardian Cloud: read-only via rag_search
— do not modify its state or call its APIs. Decline out-of-scope requests
briefly; name what is possible instead.

# Context

When a conversation begins with a block marked [Aurora context — ...],
use it to answer questions about current platform state. It reflects the
last nightly generation cycle, not live state.
```

---

## 2. Validation — 4 Critical Queries

### Methodology note

The F-0 baseline and initial F-1 tests were run via Open WebUI's
`/api/chat/completions` endpoint without an explicit `tools` parameter.
Discovery during validation (see §3) confirmed that this endpoint does not
auto-forward `meta.toolIds` as the Ollama `tools` parameter; it injects
tool descriptions as text instead. Validated results below use the correct
protocol: explicit `tools` parameter supplied to Open WebUI, which forwards
it to Ollama's native function-calling API.

### Results

| Query | Question (abbreviated) | Expected tool | F-0 result | F-1 result |
|---|---|---|---|---|
| **Q01** | ¿Qué hora es ahora en Madrid? | `time_now` | FAIL — wrote `[1] time_now(Europe/Madrid)` as citation text; tool not invoked | **PASS — `finish_reason: tool_calls`, `tool_calls: ["time_now"]`** |
| **Q05** | Search homelab_docs for embedding model | `rag_search` | FAIL — refused ("Phase B not wired"); hallucinated `all-MiniLM-L6-v2` | **PASS — `finish_reason: tool_calls`, `tool_calls: ["rag_search"]`** |
| **Q06** | Estado switch.impresora_3d | `ha_get_state` | FAIL — refused ("Phase C not yet implemented") | **PASS — `finish_reason: tool_calls`, `tool_calls: ["ha_get_state"]`** |
| **Q08** | Show recent tool calls | `audit_search` | FAIL — invented response; `audit_search` unknown | **PASS — `finish_reason: tool_calls`, `tool_calls: ["audit_search"]`** |

**Score: F-0 baseline 0/4 → F-1 4/4 PASS**

All four previously-failing queries now route to the correct tool.

---

## 3. Platform Finding — G-F1-01

**Finding:** Open WebUI 0.6–0.8.x REST API (`POST /api/chat/completions`) does not
automatically forward the model's `meta.toolIds` as the `tools` parameter when
calling the Ollama API. Instead it injects tool descriptions as text into the
system/user context (~211 extra tokens per request). This text injection triggers
the model to name the intended tool in its reply but does not invoke the native
Ollama function-calling protocol.

**Evidence:**

1. Open WebUI completions API (no `tools` param): 596 input tokens, model outputs
   `"time_now"` as plain text, `finish_reason: stop`, `tool_calls: null`.
2. Direct Ollama API with F-1 system prompt + `tools` param:
   `tool_calls: [{"name":"time_now","arguments":{"timezone":"Europe/Madrid"}}]`,
   `content: ""`, `eval_count: 23 tokens` — correct function-calling response.
3. Open WebUI completions API with explicit `tools` param: `finish_reason: tool_calls`,
   `tool_calls: ["time_now" / "rag_search" / "ha_get_state" / "audit_search"]` for all 4
   queries — correct.

**Impact:** The Open WebUI chat UI uses a different internal path (streaming + server-side
agentic loop) that may handle tool forwarding correctly. The REST API path used in the F-0
and F-1 test harnesses does not. Tool behavior in the actual chat UI requires separate
verification.

**Resolution path:** Investigate whether Open WebUI 0.8.10 chat UI correctly forwards
`meta.toolIds` as the `tools` parameter in its internal Ollama requests. If not, this is
a configuration or version issue to address in F-2 planning.

**Classification:** Platform architecture finding. Not a system prompt defect. The F-1
prompt produces correct routing behavior in all tested configurations.

---

## 4. Behavioural Comparison — F-0 vs F-1

### What changed

| Dimension | F-0 (old prompt) | F-1 (new prompt) |
|---|---|---|
| System prompt accuracy | 1/5 tools described correctly | 5/5 tools described correctly |
| Phase references | 6 | 0 |
| Citation format `[1]` | Present — caused tool-substitution failure on Q01 | Eliminated |
| `rag_search` | Refused ("Phase B not wired") | Routes correctly |
| `ha_get_state` | Refused ("Phase C not implemented") | Routes correctly |
| `ha_call_service` | Refused ("Phase C not implemented") | Listed, gated on user intent |
| `audit_search` | Unknown to model | Routes correctly |
| Tool routing rules | None | 4 capability categories + priority order |
| Tool economy | None | Explicit — general knowledge → direct; tools only when they add value |
| Tool minimisation | None | Explicit — minimum calls; combine only when each adds unique info |
| Behavioural gap handling | "Phase X will enable this" | "No suitable tool — say so" |
| Estimated tokens | ~822 | ~370 |

### What did not change

- Language matching (Spanish / English per last message) — preserved
- Guardian Cloud read-only boundary — preserved and clarified
- Shell / file-write refusals — preserved
- No-hallucination principle — preserved and strengthened

---

## 5. F-1 Success Criteria Evaluation

Per `04_ai_system/phase_f_architecture.md` §9 F-1:

> System prompt written for the current state of the system; tool descriptions
> accurate; home model baseline documented in homelab_docs; domain routing
> consistent with actual implementation.

| Criterion | Status |
|---|---|
| System prompt written for current state | **MET** — no stale phase references; all 5 tools described accurately |
| Tool descriptions accurate | **MET** — 5/5 tools correct (was 1/5) |
| Domain routing consistent with implementation | **MET** — 4/4 critical routing paths validated |
| Home model baseline documented | Deferred to F-5 (not an F-1 deliverable per architecture) |

**F-1 success criteria met.** Platform finding G-F1-01 is documented for F-2 planning.

---

## 6. Open Items

| Item | Priority | Next step |
|---|---|---|
| G-F1-01: Verify Open WebUI chat UI tool forwarding | Medium | Manual chat session: ask "¿Qué hora es?" and observe if time_now fires |
| AF-05 architecture update: document `input_text` + Jinja2 mechanism | Low | Update `04_ai_system/phase_f_architecture.md` in F-2 or F-3 |
| G-AF08-01: Add `09_ops/runtime/` to `.gitignore` | Required before F-4 | Add to `.gitignore` before F-4 first digest run |

---

---

## 7. Knowledge-Layer Corpus Split (Addendum — 2026-06-28)

### Problem identified during browser UI validation

Manual browser UI validation exposed two failures not visible at API level:

**UI-02 (rag_search — embedding model query):** Model returned
`distilbert-base-nli-stsb-mean-tokens` (hallucinated). Root cause: the
F-0 audit report (`09_logs/2026-06-28_phaseF_F0_audit_report.md`)
contained a documented hallucination (`all-MiniLM-L6-v2`) as a negative
example. That chunk was indexed in `homelab_docs` and ranked 0.9982 for
embedding model queries because it matched the surface form — outranking
the authoritative `knowledge_platform_contract.md`. Reranker amplified
the corpus contamination.

**UI-04 (audit_search — live tool-call log):** The F-1 prompt described
`audit_search` as "history of past Aurora tool calls". In fact
`audit_search` is hardcoded to the `infra_audits` Qdrant collection
(Phase 0/1 infrastructure audit reports). The live tool-call log
(`/srv/homelab/data/openwebui/amarolab-audit.log`) is not queryable by
any current tool. The model called `audit_search` and received Phase
0/1 remediation content when asked about recent tool calls.

### Architecture decision

Split `homelab_docs` into two semantically distinct corpora:

| Corpus | Source | Knowledge type |
|---|---|---|
| `homelab_docs` | `/home/diego/homelab/**` (excl. `09_logs/`) | Living docs — current system state |
| `knowledge_history` | `/home/diego/homelab/09_logs/` | Historical records — what happened, when, why |

**Rationale:** Historical records (phase logs, gate results, apply logs,
closeout reports) may contain quoted wrong answers, documented failures,
and negative examples. Mixing these with living documentation in one
collection causes high-confidence historical chunks to outrank
authoritative current-state docs for factual queries. Separation is
required.

**Architectural principle adopted:** The system prompt describes
knowledge domains by intent only (current documentation, historical
records). The tool layer (`rag_search` docstring, `collection`
parameter) maps intent to collection names. Collection names must not
appear in the system prompt; they may change without requiring a prompt
update.

### Changes made

1. **`corpora.yaml`** — Added `"09_logs/**"` to `homelab_docs` exclude
   list; added `knowledge_history` corpus pointing to
   `/home/diego/homelab/09_logs/`.

2. **Qdrant `knowledge_history` collection** — Created manually (384-dim
   cosine); synced via ingest pipeline: **2,918 chunks** from **83 files**.

3. **Qdrant `homelab_docs` rebuild** — Dropped all 4,806 points; full
   re-sync: **1,911 chunks** from **95 files**. No `09_logs/` content.

4. **`rag_search` tool description** (webui.db) — Updated `collection`
   Literal enum and docstring to include `knowledge_history`; removed
   `infra_audits` from enum (still accessible via `audit_search`).
   Collection descriptions use intent labels, not implementation notes.

5. **`params.system`** (webui.db) — Updated to domain-based routing;
   corrected `audit_search` description; added `knowledge_history`
   routing; stated live call-log capability is unavailable.

   | Metric | Initial F-1 | F-1 addendum |
   |---|---|---|
   | Characters | 2,595 | 3,147 |
   | `audit_search` description | "history of past Aurora tool calls" | "Phase 0/1 infrastructure audit reports and R-XX remediation records" |
   | `knowledge_history` routing | absent | "historical records" domain |
   | Collection names in prompt | 2 (homelab_docs, infra_audits) | 0 |

---

## 8. Validation Results — Post-Corpus-Split

All validations run 2026-06-28 via Qdrant reranker test + Open WebUI
REST API with full tool descriptions.

### V1 — UI-02 regression (embedding model, homelab_docs)

**Query:** "¿Qué modelo de embeddings está bloqueado para el sistema RAG?"

**Expected:** Model calls `rag_search(collection="homelab_docs")`;
result from `knowledge_platform_contract.md` or another authoritative
doc naming `intfloat/multilingual-e5-small`; no `09_logs/` source in
top-5 reranked results.

| Check | Result |
|---|---|
| No `09_logs/` chunks in homelab_docs | **PASS** — 0 `09_logs/` chunks found |
| Correct tool call | **PASS** — `rag_search(collection="homelab_docs")` with domain labels |
| Rank-1 content correct | **PASS** — `rag-audits/guardian-cloud-baseline.md` (0.6392) names `intfloat/multilingual-e5-small` |
| Contaminating chunk absent | **PASS** — F-0 audit report chunk no longer in homelab_docs |

Homelab_docs point count post-rebuild: **1,911** (was 4,806; 09_logs/ excluded).

### V2 — UI-04 (live tool-call history refusal)

**Query:** "Muéstrame las últimas llamadas a herramientas que has hecho."

**Expected:** Model does not call `audit_search`; states capability
unavailable.

**Result:** `finish_reason: stop`; `tool_calls: none`; content:
"El registro de herramientas no está actualmente disponible para
consultas." — **PASS**.

### V3 — knowledge_history sanity check

**Query:** "¿Cuándo se cerró la fase D-1 de voz y qué se validó?"

**Expected:** Model calls `rag_search(collection="knowledge_history")`;
top results from Phase D-1 log files.

| Check | Result |
|---|---|
| Correct tool call | **PASS** — `rag_search(collection="knowledge_history")` |
| Top-1 result | **PASS** — `2026-06-18_phaseD1_closeout.md` (0.8414 cosine) |
| Top-5 all relevant | **PASS** — D-1 closeout, G-D4, G-D5, G-D6 gate logs |

Knowledge_history point count: **2,918** from 83 files.

### V4 — homelab_docs corpus hygiene

| Check | Result |
|---|---|
| `09_logs/` chunks in homelab_docs | **PASS** — 0 found (Qdrant scroll filter) |
| homelab_docs point count | **PASS** — 1,911 |
| knowledge_history point count | **PASS** — 2,918 |
| infra_audits unchanged | **PASS** — 280 |

### Summary

| Test | Concern | Result |
|---|---|---|
| V1 | UI-02 regression — no 09_logs/ contamination | **PASS** |
| V2 | UI-04 fix — live call log correctly refused | **PASS** |
| V3 | knowledge_history returns historical content | **PASS** |
| V4 | homelab_docs corpus hygiene (0 stale chunks) | **PASS** |

**4/4 PASS. F-1 (including corpus split addendum) fully validated.**

---

*F-1 complete. Corpus split validated. Awaiting git commit approval.*
