# Phase F — F-3 Closeout: Situational Awareness

- **Date:** 2026-06-29
- **Step:** F3.3 — reconciliation & closeout for **F-3 (Situational Awareness)**,
  covering F-3a (chat) and F-3b (voice).
- **Authority:** Reality is source of truth (PROJECT_RULES). Frozen spec:
  [`../04_ai_system/phase_f_architecture.md`](../04_ai_system/phase_f_architecture.md)
  §7, §9-F-3, AD-08…AD-13. Detail lives in the F3.1 / F3.2 apply logs; this is the
  phase-level summary.
- **Status:** **F-3 COMPLETE.** All gates **G-F3-1…G-F3-8 pass.** Overview triad +
  architecture reconciled. **No git operations performed** — staged for operator review.

---

## 1. What F-3 delivered

Aurora reports current lab state at conversation start with **no tool call**, on both
front doors, reading the same nightly context artifact produced by F-2
(`bin/aurora-context` → `ai-stack/aurora/aurora-context.{json,md,voice}`).

- **F-3a — Open WebUI chat** (milestone F3.1): an Open WebUI Filter injects
  `aurora-context.md` into message 1.
- **F-3b — Home Assistant voice** (milestone F3.2): the Ollama voice prompt renders a
  nightly `input_text` helper via Jinja2.

## 2. F-3a — Open WebUI Awareness Filter (F3.1)

- Committed Filter
  [`../ai-stack/openwebui-tools/filters/aurora_context.py`](../ai-stack/openwebui-tools/filters/aurora_context.py)
  (AD-09), installed via `install_function`; **active + global** in `webui.db.function`
  (`aurora_context | filter | 1 | 1`). Injects on message 1 only; freshness off the
  JSON `generated_at`; ≤24h plain, 24–26h graduated note, >26h/missing → one-line
  fallback; idempotency guard; never raises.
- **G-F3-1 required a prompt change:** with tools offered, the 7B preferred a
  `system_status` call over answering from the block. An operator-approved
  **`# Context`-over-`# Routing` precedence directive** in `params.system`
  (live prompt now 3 532 chars) + an `openwebui` reload closed G-F3-1.
- Published: tag **`phase-f3a-complete`** (commit `96217e52`, already on `origin/main`).
- Detail: [`2026-06-29_phaseF_F3_1_applied.md`](2026-06-29_phaseF_F3_1_applied.md).

## 3. F-3b — HA Voice Awareness Refresh (F3.2)

- HA helper `input_text.aurora_voice_context` (`max: 255`, `configuration.yaml`).
- One line appended to the **stock** Ollama voice prompt:
  `Recent lab status: {{ states('input_text.aurora_voice_context') }}` (AD-13).
- [`../ai-stack/ingest/bin/push-voice-context`](../ai-stack/ingest/bin/push-voice-context)
  writes `aurora-context-voice.txt` into the helper via HA REST `input_text/set_value`;
  scheduled at **04:20** in `/etc/cron.d/aurora-signals` (after 04:15 `aurora-context`).
- **G-F3-8 pass:** the conversation agent (the same agent the voice pipeline drives)
  recited the exact injected status; helper == voice line; token never in a committed
  artifact. Detail: [`2026-06-29_phaseF_F3_2_applied.md`](2026-06-29_phaseF_F3_2_applied.md).

## 4. Gate ledger

| Gate | Surface | Result |
|---|---|---|
| G-F3-1 | chat — answer from block, no tool call, cites `generated_at` | ✅ (after `# Context` precedence + reload) |
| G-F3-2 | chat — no re-injection on messages 2+ | ✅ |
| G-F3-3 | chat — degraded context surfaces, points to `system_status` | ✅ |
| G-F3-4 | chat — missing/unreadable/>26h → fallback, never crashes | ✅ |
| G-F3-5 | chat — graduated note at 24–26h | ✅ |
| G-F3-6 | chat — intra-day "ahora mismo" → defers to `system_status` (live) | ✅ |
| G-F3-7 | chat — no tool-routing regression with the block present | ✅ |
| Repro | F-3a Filter source committed + install/recovery documented (AD-09) | ✅ |
| G-F3-8 | voice — first exchange reflects latest `aurora-context-voice.txt`; push verified; token clean | ✅ |

## 5. Deviations / decisions (consolidated)

1. **G-F3-1 `# Context` precedence directive** — required and operator-approved; recorded
   in the architecture §9 note and revision log. The frozen plan under-specified prompt
   precedence; reality required it.
2. **F-3b privileged steps were operator actions** — `HA_LLAT` is a non-admin token
   (admin endpoints → 401) and there is no passwordless `sudo`, so the helper reload,
   the prompt edit, and the cron install were performed by the operator (admin UI / sudo).
   Everything else was autonomous; no HA restart was used.
3. **F-3b minimal label** — `Recent lab status:` precedes the frozen AD-13 Jinja
   expression (unchanged) to frame the value; baseline prompt otherwise verbatim.
4. **F-3b helper has no `initial:` / no `default()` guard** — restores last value across
   restarts; pre-first-push renders `unknown`, resolved by the immediate first push.
   Honest degradation; the value is self-timestamped. Accepted.
5. **F-1 HA voice identity is absent** — the live voice prompt is the integration's stock
   default, not an F-1 identity (likely reset by the RTX-1.6 config rewrite, 2026-06-27).
   Out of F-3b scope by operator decision; tracked as a separate maintenance item.

## 6. Reconciliation performed (F3.3)

- **CURRENT_STATE.md / ROADMAP.md / AMAROLAB_HANDOFF.md** — F-3 marked COMPLETE;
  current active step advanced to **F-4**; F-3a Filter + F-3b voice awareness recorded
  as live components; Open WebUI `params.system` updated to 3 532 chars + `# Context`.
- **phase_f_architecture.md** — §9 F-3 "as built" note; milestone statuses (F3.0→F3.3);
  status header + revision-log entry; G-F3-1 precedence + F-1-voice-identity notes.

## 7. Runtime state vs git (reproducibility)

- **Runtime (not git):** the `aurora_context` filter row + `# Context` prompt in `webui.db`;
  the `input_text` helper + voice prompt line in HA (`configuration.yaml` / `.storage`).
  Recovery: F-3a — re-run `install_function` + restore `params` (R-12 snapshot); F-3b —
  re-apply the YAML helper + prompt line (documented in F3.2 §3). Parallel to
  [`../04_ai_system/openwebui_model_runtime_state.md`](../04_ai_system/openwebui_model_runtime_state.md).
- **Git-tracked (this publication):** `push-voice-context`, the cron source, the F3.2 apply
  log, this closeout, and the four reconciled docs. F-3a source was already published under
  `phase-f3a-complete`.

## 8. Publication set (staged; not committed)

F-3b build (left uncommitted at F3.2) + F3.3 reconciliation, to be published together:

- `ai-stack/ingest/bin/push-voice-context` (new)
- `ai-stack/ingest/etc/cron.d/aurora-signals` (modified)
- `09_logs/2026-06-29_phaseF_F3_2_applied.md` (new)
- `00_overview/CURRENT_STATE.md` (modified)
- `00_overview/ROADMAP.md` (modified)
- `00_overview/AMAROLAB_HANDOFF.md` (modified)
- `04_ai_system/phase_f_architecture.md` (modified)
- `09_logs/2026-06-29_phaseF_F3_closeout.md` (new — this file)

No runtime artifacts (`ai-stack/aurora/*`, signal JSON, `health.json`, `.env`,
`09_ops/runtime/`) are staged — all gitignored.

## 9. Next

**STOP — no `git add` / commit / push / tag** (operator gate; operator reviews this
closeout before publication). Suggested publication tag after approval:
`phase-f3-complete`. Next Phase F sub-phase: **F-4 — Operational Digest + Memory
Corpus** (F-5 / F-6 also unblocked). The 04:20 voice push first fires live tonight.
