# Phase F — F-0 Behavioral Audit Report

**Date:** 2026-06-28  
**Phase:** F-0 — Behavioral Audit (read-only, no implementation)  
**Status:** COMPLETE  
**Recommendation:** Phase F is ready to enter F-1. One blocker must be resolved in F-1.

---

## 1. Scope

F-0 is the read-only audit that precedes any Phase F implementation. Its purpose is to:

1. Validate or disprove the eight architecture assumptions (AF-01..AF-08)
2. Establish a behavioral baseline for the current Aurora assistant
3. Surface implementation risks before code is written
4. Confirm that the Phase F architecture is internally consistent

F-0 is complete. No production systems were modified. No git operations were performed.

---

## 2. System Prompt Audit

### Location

The Aurora system prompt is stored as the `params.system` field of the `Aurora` workspace model in Open WebUI's `webui.db`. It is the **Phase A draft** — written before Phases B and C were implemented.

### Current prompt (abbreviated)

```
You are Amarolab Assistant, a local AI running on this homelab.
...
You have three planned tools. Their current implementation status:

1. time_now(timezone?, format?) — APPLIED.
2. rag_search(collection, query, top_k?) — NOT YET WIRED (Phase B).
   [Do not call it.]
3. system_status(scope) — NOT YET WIRED (Phase D).
   [Do not call it.]

Refusals:
- Home Assistant control (turn on/off devices) — Phase C, not yet implemented.
```

### Prompt vs. reality

| Claim in prompt | Actual state |
|---|---|
| `rag_search` — "NOT YET WIRED (Phase B)" | **WIRED** — `rag_search` is production |
| `system_status` — "NOT YET WIRED (Phase D)" | Not yet wired — correct |
| HA control — "Phase C, not yet implemented" | **Phase C is COMPLETE** — `ha_get_state` and `ha_call_service` are wired and production |
| `audit_search` — not mentioned | **WIRED** — `audit_search` is production |
| "You have three planned tools" | **FIVE tools are attached**: `time_now`, `rag_search`, `audit_search`, `ha_get_state`, `ha_call_service` |

**Verdict: the system prompt is 2–3 phases behind reality.** It actively prevents Aurora from using 4 of its 5 wired tools. This is the single most impactful correctable defect in the current system.

### Prompt metrics

| Metric | Value |
|---|---|
| Total length | ~3,342 characters (referenced in CURRENT_STATE.md) |
| Tool descriptions correct | 1 of 5 (time_now only) |
| Phase references accurate | 0 of 4 |
| Refusal rules accurate | 0 of 2 (both now outdated) |
| First-turn introduction instruction | Present — correct |
| Language matching instruction | Present — functional |
| Citation format instruction | Present — but causes tool-substitution failure (see §4) |

---

## 3. Behavioral Baseline — 10-Query Test

All 10 queries sent to the live Aurora model (`qwen2.5:7b-instruct`, Aurora workspace, all 5 tools attached). Queries cover all F-0 behavioral dimensions.

### Results table

| # | Query | Expected | Actual behavior | Tools fired | Latency | Score |
|---|---|---|---|---|---|---|
| Q01 | ¿Qué hora es ahora? | Call `time_now`, return time | Wrote citation text `[1] time_now(Europe/Madrid)` — tool NOT called; time placeholder shown | None | 0.4s | **FAIL** |
| Q02 | Estado actual del lab | Acknowledge no situational awareness | Correctly deferred — "system_status not available (Phase D)" | None | 1.2s | **PASS** |
| Q03 | ¿Cuándo fue el último backup? | Acknowledge gap, no hallucination | Correctly deferred; did not invent backup time | None | 1.2s | **PASS** |
| Q04 | ¿Cuántos contenedores Docker corren? | Acknowledge no container probe | Correctly deferred; no hallucinated count | None | 1.2s | **PASS** |
| Q05 | Search homelab_docs for embedding model | Call `rag_search` | Refused ("Phase B not yet wired"); hallucinated embedding model as `all-MiniLM-L6-v2` | None | 1.2s | **FAIL×2** |
| Q06 | Estado switch.impresora_3d | Call `ha_get_state` | Refused ("Phase C not yet implemented") | None | 0.9s | **FAIL** |
| Q07 | Is Torre online? | Acknowledge limitation; suggest probe | Correctly deferred; no false claim | None | 1.1s | **PASS** |
| Q08 | Recent tool calls | Call `audit_search` | Invented response ("no tool calls in this conversation"); `audit_search` unknown to model | None | 1.0s | **FAIL** |
| Q09 | Exact homelab_docs point count | Search or admit uncertainty | Correctly did not hallucinate a number; rambled; deferred to Phase B | None | 1.6s | **PARTIAL** |
| Q10 | List available tools | Accurate tool inventory | Listed only `time_now`; said rag_search/system_status are future phases; mixed Chinese characters in response | None | 1.0s | **FAIL** |

**Score: 4 PASS / 1 PARTIAL / 5 FAIL**

### Critical finding — Q01: `time_now` failure

`time_now` IS the one tool the system prompt says is wired, and it still was NOT called. The model produced:

```
La hora actual en Madrid es [1].

[1] time_now(Europe/Madrid)
```

The model is treating the post-tool-call citation format (defined in the system prompt) as a mechanism to EXPRESS a tool call rather than a consequence of one. The tool was not invoked — `tool_calls: None` in the API response, `finish_reason: stop`. The actual current time was never retrieved.

**Root cause:** The system prompt's citation format instruction (`[1] <source>`) is close enough to the model's natural output format that the model generates it as a response pattern rather than first invoking the actual tool. The model then stops (finish_reason: stop) believing it has cited a tool result.

This is the most severe finding because `time_now` was the one tool described as working.

### Q05 hallucination — embedding model

When unable to call `rag_search`, the model stated:

> "Según mis registros, el modelo de embedding actualmente bloqueado para el sistema RAG es **sentence-transformers/all-MiniLM-L6-v2**"

**This is wrong.** The actual embedding model is `intfloat/multilingual-e5-small` (384-dim), locked per D-08. The model hallucinated a plausible but incorrect model name when unable to retrieve the ground truth.

### Q10 language failure — Chinese character injection

The response to "List all tools you have available" contained Chinese characters (`工具尚未启用，请稍候使用`). This is an artefact of `qwen2.5`'s training data leakage — when asked about its own capabilities in a mixed-language context, the Chinese training data surface. This has not been observed in normal use and appears only under specific self-referential prompting.

---

## 4. Behavioral Scorecard

### Strengths

| Strength | Evidence |
|---|---|
| **Hallucination discipline (numerical)** | Q03, Q04, Q07, Q09 — correctly refused to invent backup time, container count, Torre status, point counts |
| **Graceful limitation acknowledgment** | Q02, Q03, Q04, Q07 — politely defers and names missing capability |
| **Low latency** | All 10 queries: 0.4–1.6s end-to-end; Torre GPU at ~101 tok/s performing well |
| **Language matching** | Spanish queries → Spanish replies (except Q10 Chinese injection) |
| **No dangerous refusals** | No false safety refusals for legitimate queries |

### Weaknesses

| Weakness | Severity | Queries |
|---|---|---|
| **System prompt is 3 phases stale** — actively blocks 4/5 wired tools | **Critical** | Q01, Q05, Q06, Q08, Q10 |
| **Citation format confuses tool invocation** — model writes `[1] tool_name()` instead of calling the tool | **Critical** | Q01 |
| **`rag_search` not used** despite being wired and directly applicable | **High** | Q05, Q09 |
| **`ha_get_state` not used** despite Phase C being complete | **High** | Q06 |
| **`audit_search` entirely unknown** to the model | **High** | Q08 |
| **Hallucination under uncertainty** — invents plausible answer when tool is unavailable | **Medium** | Q05 (embedding model) |
| **Zero situational awareness** — every conversation starts from zero with no platform state | **Medium** | Q02 (expected; Phase F goal) |
| **Chinese character injection** under self-referential prompting | **Low** | Q10 |

### Latency observations

| Observation | Value |
|---|---|
| Fastest response | 0.4s (Q01 — no actual tool call, pure generation) |
| Slowest response | 1.6s (Q09 — longer deliberation) |
| Median | ~1.1s |
| Tool-call overhead | Not measurable — no tools actually fired in baseline |
| Assessment | Excellent raw generation speed; Torre GPU performing as expected |

---

## 5. AF Register — Final Status

| Finding | Description | Status |
|---|---|---|
| **AF-01** | Open WebUI Filter inlet mechanism | **CONFIRMED** (2026-06-28) — 6/6 checks pass; fires on message 1 only; reads file; degrades gracefully. No redesign required. |
| **AF-02** | `backup_status.json` does not exist | **CONFIRMED** (2026-06-28) — absent as expected. `homelab-backup.sh` writes no JSON. Gap is a pre-F-2 pre-condition, not a defect. |
| **AF-03** | `container_status.json` does not exist | **CONFIRMED** (2026-06-28) — absent as expected. No `bin/container-probe` script exists. Gap is a pre-F-2 pre-condition. |
| **AF-04** | `system_status` tool not yet wired | **CONFIRMED** — not yet wired (not audited separately; consistent with all baseline queries). Scheduled for F-2. |
| **AF-05** | HA voice system prompt update mechanism | **CONFIRMED + SUPERSEDED** (2026-06-28) — mechanism is validated as feasible. Architecture improved: `input_text.aurora_voice_context` + Jinja2 template rendering (per-request, no reload). Original "REST API vs. direct config write" question resolved in favour of `input_text` entity approach. |
| **AF-06** | Current system prompt accuracy | **DISPROVED** (2026-06-28) — prompt is not accurate. Phase A draft. 5 tools wired; prompt describes 1 correctly, actively disables 4. This is the primary F-1 deliverable. |
| **AF-07** | Torre Ollama reachability from container | **CONFIRMED** (2026-06-28) — HTTP 200 from `openwebui` container to `100.91.154.124:11434` in <2ms. Routing: docker bridge → UM790 host → tailscale0 → Torre. No fallback intermediary needed. |
| **AF-08** | Filesystem corpus indexes runtime artifacts | **CONFIRMED WITH GAP** (2026-06-28) — fs corpus indexes `09_ops/runtime/` regardless of git status. Deletion propagates on next sync. Gap: `09_ops/runtime/` not yet in `.gitignore` (required before F-4). |

**Summary:** 6 confirmed, 1 disproved (AF-06), 1 confirmed + superseded (AF-05).

---

## 6. Pre-Implementation Requirements

Items surfaced by F-0 that must be addressed before or during the specified sub-phase:

| Requirement | Sub-phase | Severity |
|---|---|---|
| Rewrite system prompt to reflect actual tool surface (Phases B, C complete; AF-06 disproved) | **F-1** | **Blocker** |
| Fix citation format instruction to not interfere with tool invocation | **F-1** | **Blocker** |
| Add `ai-stack/aurora/` to `.gitignore` | F-2 (before first `bin/aurora-context` run) | Required |
| Add `09_ops/runtime/` to `.gitignore` (G-AF08-01) | F-4 (before first digest run) | Required |
| `homelab-backup.sh` root→diego file ownership for `backup_status.json` | F-2 | Required |
| Write `bin/container-probe` from scratch | F-2 | Required |
| Create `input_text.aurora_voice_context` (max_length 255, via YAML) | F-3 | Required |
| One-time update of HA Ollama voice prompt to add Jinja2 `{{ states(...) }}` reference | F-3 | Required |
| Add `input_text/set_value` API call to `bin/aurora-context` | F-2 or F-3 | Required |

---

## 7. F-1 Readiness Recommendation

### Is Phase F ready to enter F-1?

**Yes, with one blocker.**

The architecture is sound. All AF findings have been resolved. The F-0 audit has surfaced no architectural redesign requirements — the Phase F architecture stands as designed and reviewed.

**Blocker:** AF-06 (system prompt stale — disproved) is the primary F-1 deliverable. F-1 must deliver a new system prompt that:

1. Accurately describes all 5 wired tools (`time_now`, `rag_search`, `audit_search`, `ha_get_state`, `ha_call_service`)
2. Removes stale Phase B/C/D "not yet wired" language
3. Fixes the citation format so it does not interfere with actual tool invocation
4. Adds `ha_call_service` usage guidance and allowlist awareness
5. Is shorter and more precise — the current 3,342-char prompt is partially self-defeating

**Note on `system_status`:** Since F-1 is system prompt only (no tool implementation), the updated prompt should describe `system_status` as "planned for F-2" — an honest forward reference rather than the current stale "Phase D" reference.

**Not blockers for F-1:**
- AF-02 / AF-03 (signal gaps) — expected pre-F-2 state
- AF-08 gitignore gap — not needed until F-4
- AF-07 Torre probe — architecture confirmed; implementation in F-2

### F-1 success criteria

Per the Phase F architecture (§9 F-1):

> System prompt written for the current state of the system; tool descriptions accurate; home model baseline documented in homelab_docs; domain routing consistent with actual implementation.

F-0 confirms this is the correct scope and the correct priority.

---

## 8. Git Review

### Untracked files (pending git approval)

```
?? 09_logs/2026-06-28_phaseF_F0_AF01_filter_validation.md
?? 09_logs/2026-06-28_phaseF_F0_AF02_AF03_signal_gap_confirmation.md
?? 09_logs/2026-06-28_phaseF_F0_AF05_ha_voice_prompt_mechanism.md
?? 09_logs/2026-06-28_phaseF_F0_AF07_torre_probe_validation.md
?? 09_logs/2026-06-28_phaseF_F0_AF08_corpus_runtime_validation.md
?? 09_logs/2026-06-28_phaseF_F0_audit_report.md   ← this file
```

### Proposed commit

**Files to stage (by name — no `git add .`):**
```
09_logs/2026-06-28_phaseF_F0_AF01_filter_validation.md
09_logs/2026-06-28_phaseF_F0_AF02_AF03_signal_gap_confirmation.md
09_logs/2026-06-28_phaseF_F0_AF05_ha_voice_prompt_mechanism.md
09_logs/2026-06-28_phaseF_F0_AF07_torre_probe_validation.md
09_logs/2026-06-28_phaseF_F0_AF08_corpus_runtime_validation.md
09_logs/2026-06-28_phaseF_F0_audit_report.md
```

**Proposed commit message:**
```
docs(phase-f): F-0 behavioral audit complete — 6 AF findings + baseline

F-0 audit (read-only):

AF-01 CONFIRMED — OWU Filter fires message-1 only; file read + graceful
  degradation validated. Domain A proceeds without redesign.

AF-02/03 CONFIRMED — backup_status.json and container_status.json absent
  as expected. Pre-F-2 pre-conditions, not defects.

AF-05 CONFIRMED + SUPERSEDED — HA voice prompt updatable without restart
  via input_text entity + Jinja2 template (rendered per request). No
  integration reload needed. Architecture improved.

AF-07 CONFIRMED — openwebui container reaches Torre at 100.91.154.124:11434
  directly via docker bridge → tailscale0. No host-side intermediary needed.

AF-08 CONFIRMED WITH GAP — homelab_docs fs corpus indexes 09_ops/runtime/
  regardless of git status. Gitignore gap (G-AF08-01) flagged for pre-F-4.

AF-06 DISPROVED — system prompt is Phase A draft. 5 tools wired; prompt
  describes 1 correctly. Primary F-1 deliverable.

Behavioral baseline: 4/10 pass. time_now not invoked (citation format
  conflict); rag_search/ha_get_state/audit_search blocked by stale prompt.
  Hallucination discipline good. Latency excellent (0.4–1.6s, Torre GPU).

F-0 recommendation: ready to enter F-1. System prompt rewrite is the
  blocker and the entire F-1 scope.
```

**No other files are staged.** The architecture document update for AF-05 (Jinja2 refinement) is deferred — the finding log captures it for reference during F-1 planning.

---

*End of F-0 Audit Report*
