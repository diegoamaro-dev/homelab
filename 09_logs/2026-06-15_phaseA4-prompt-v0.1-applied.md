# Phase A.4 — system prompt v0.1 — APPLIED (partial; tool-calling regression persists)

- **Date applied:** 2026-06-15
- **Scope:** Replaced `params.system` on the `qwen2.5:7b-instruct`
  model row with the v0.1 prompt designed in
  [`2026-06-15_phaseA4-prompt-v0.1-design.md`](2026-06-15_phaseA4-prompt-v0.1-design.md).
  **One API write performed.** `webui.db` size 2 334 720 → unchanged
  (UPDATE in place). No services restarted. No `llama3*` rows
  touched. No new containers, env vars, or filesystem changes
  outside `/tmp/`.
- **Supersedes:** v0 prompt installed 2026-06-15 19:34 UTC.
- **Superseded by:** none yet (v0.2 needed before Phase B can start —
  see §"Open issues" and §"Recommended next step").
- **Result:** **15 of 21 V- checks PASS, 6 FAIL.** Persona on first
  turn (Spanish path), multi-turn language switching, per-model
  isolation, and the refusal paths all improved. The `time_now`
  tool-calling regression from v0 **was not fixed by v0.1** — the
  audit log confirms zero invocations during the V-10 probe.

## What was changed in `webui.db`

| Field | Before (v0) | After (v0.1) |
|---|---|---|
| `model.params.system` length on `qwen2.5:7b-instruct` | 2 310 chars | 3 342 chars |
| `model.meta.toolIds` | `["time_now"]` | **unchanged** |
| `model.meta.description` | "Amarolab primary tool-calling LLM…" | **unchanged** |
| `model.meta.capabilities` | `{vision:false, usage:true, citations:true}` | **unchanged** |
| `model.base_model_id` | `qwen2.5:7b-instruct` | **unchanged** |
| `config.DEFAULT_MODELS` | `"qwen2.5:7b-instruct"` | **unchanged** (no second W-2 write needed) |

Endpoint used: `POST /api/v1/models/model/update?id=qwen2.5:7b-instruct`
with the **full record body** (GET → mutate `params.system` only →
POST back). Same fetch-mutate-write pattern as v0 to avoid the
field-wipe trap.

Pre-flight backup taken at
`/tmp/amarolab-phaseA4-v0_1-backup/webui.db.pre-v0_1` (2.33 MB; the
post-v0 state) in addition to the original
`/tmp/amarolab-phaseA4-backup/webui.db.pre-A4` from the pre-A.4
state.

## Validation results — 15 of 21 PASS

Full transcript: `/tmp/amarolab_phaseA4_v0_1_validate.py` (19 V-
checks, 21 sub-assertions). All chat probes via the OpenAI-compatible
`POST /api/chat/completions`. Audit-log truth source:
`/srv/homelab/data/openwebui/amarolab-audit.log`.

| # | Check | v0 | **v0.1** | Notes |
|---|---|:---:|:---:|---|
| V-1 | `DEFAULT_MODELS == "qwen2.5:7b-instruct"` | ✓ | **✓** | carry-over |
| V-2a | `params.system` length ≥ 3000 | n/a | **✓** | 3 342 chars |
| V-2b | `params.system` starts with v0.1 persona line | n/a | **✓** | |
| V-2c | `meta.toolIds == ["time_now"]` | ✓ | **✓** | D-20 preserved |
| V-2d | `meta.description` preserved | ✓ | **✓** | |
| V-3a | `llama3:latest.params == {}` | ✓ | **✓** | |
| V-3b | `llama3:latest.name == "Jarvis"` | ✓ | **✓** | |
| V-4 | `llama3.2:latest.params.system` unchanged | ✓ | **✓** | "You are connected to tools…" intact |
| V-5a | qwen2.5 Spanish greeting → "Amarolab Assistant" in reply | ✗ | **✓** | **fixed:** `"¡Hola! Soy Amarolab Assistant. ¿En qué puedo ayudarte hoy?"` |
| V-5b | qwen2.5 Spanish greeting → Spanish reply | ✓ | **✓** | |
| V-6a | qwen2.5 English greeting → "Amarolab Assistant" | ✗ | **✗** | model still replies in Spanish (see V-6b) |
| V-6b | qwen2.5 English greeting → English reply | ✗ | **✗** | `"hi there"` → `"¡Hola! ¿Cómo estás? …"` — model treats short greeting as ambiguous |
| V-7a | HA control prompt → polite refusal | ✓ | **✓** | |
| V-7b | refusal names Phase C | ✓ | **✓** | |
| V-8a | doc-search prompt → "not available" | ✓ | **✓** | |
| V-8b | reply names Phase B | ✓ | **✗** | softened: reply said *"Rag_search aún no está disponible"* but didn't name Phase B explicitly |
| V-9 | `llama3:latest` chat — no "Amarolab" | ✓ | **✓** | |
| V-10a | qwen2.5 "¿qué hora es?" → real ISO date or HH:MM | ✗ | **✗** | still rendering `[1]` placeholder |
| V-10b | (new) fresh `time_now` entry in audit log | n/a | **✗** | **0 invocations** during V-10 — confirmed via audit log |
| V-11 | (new) ES turn 1 → EN turn 2 explicit switch | n/a | **✓** | `"actually, please switch to English"` → `"Hi! How can I assist you today?"` |
| V-12 | (new) reply does NOT contain literal `time_now(` | n/a | **✗** | reply contained `time_now("Europe/Madrid", "%H:%M:%S")` |

**Delta from v0:** +2 PASS (V-5a Spanish persona, V-11 multi-turn);
+0 net for tool-calling (V-10 still fails, V-12 newly captures the
same root cause); −1 (V-8b softened — Phase B not explicitly named).

## What v0.1 fixed

- **First-turn self-introduction works in Spanish** (V-5a). The
  `# First turn` block landed:
  > `"¡Hola! Soy Amarolab Assistant. ¿En qué puedo ayudarte hoy?"`
- **Multi-turn language switch works on explicit request** (V-11).
  User said *"actually, please switch to English"* on turn 2; model
  replied:
  > `"Hi! How can I assist you today?"`
- **All carry-over PASSes held.** Default model, system prompt
  landing, per-model isolation, refusal paths, and llama3
  cleanliness all stayed green.

## What v0.1 did NOT fix

### Issue T (carried from v0, **most serious**) — `time_now` not invoked

The CRITICAL RULES block in the v0.1 prompt explicitly says:

> *"When a user asks for current time, date, or weekday, you MUST
> issue a real tool call to time_now. Do not write the function
> signature in your reply text. Do not write a literal '[1]' or
> any other placeholder."*

qwen2.5 still ignored this. Reply to `"¿qué hora es?"`:

```
"La hora actual en Europe/Madrid es [1].

[1] time_now("Europe/Madrid", "%H:%M:%S")"
```

Audit log: **0 new `time_now` entries** in the window starting at
`2026-06-15T17:49:02 UTC` (boundary captured pre-probe). The model
synthesised both the inline `[1]` and the footer signature without
ever issuing a tool call.

Hypotheses (none confirmed):

1. **Prompt-induced description**: by including
   `time_now(timezone?, format?)` in the `# Tools` section, the
   model is treating the documentation as the artefact to render
   instead of the schema to invoke. v0.2 candidate: drop the
   signature line, leave only English-language description.
2. **Tool-injection conflict in Open WebUI 0.8.10**: when a custom
   `params.system` is present, Open WebUI's auto-injection of tool
   schemas to Ollama may be ordered behind the custom prompt in a
   way qwen2.5 doesn't reconcile. v0.2 candidate: bypass via a
   direct `curl http://127.0.0.1:11434/api/chat` test to confirm /
   isolate.
3. **Citation grammar still dominates**: the `# Citations` ordering
   block tries to anchor citations to actual tool results, but the
   model may be reading "cite as `[1]`" as a *suggested format* and
   producing it even without a call. v0.2 candidate: replace `[1]`
   with a marker that's harder to confuse (e.g., literally write
   the time, no marker).

Phase A.3's happy-path validation passed **before** any system
prompt existed. So this is unambiguously prompt-induced; Phase A.3
proves the Tool itself works.

### Issue L (regression from v0.1, minor) — English greeting still defaults to Spanish

`# Language` says:

> *"Match the language of the user's MOST RECENT message:
> Spanish → Spanish reply. English → English reply…"*

But `"hi there"` got `"¡Hola! ¿Cómo estás?..."`. qwen2.5 appears to
treat a two-word English greeting as language-ambiguous despite the
explicit per-language rule.

Note V-11 *did* pass — when the user wrote a full English sentence
("actually, please switch to English. say hi back briefly."), the
model switched. So the model can do it; it just struggles with
short greetings as the first turn. v0.2 candidate: drop the
"ambiguous" escape hatch entirely (*"Always match the script /
language of the user's message; if you cannot tell, ask"*).

### Issue B (regression from v0, minor) — Phase B not named in V-8b

v0 reply named "Phase B" explicitly. v0.1 reply was
> *"Rag_search aún no está disponible en esta versión, pero puedo
> proporcionarte información basada en mi conocimiento actual…"*

— useful refusal, just missing the phase pointer. The bullets under
`# Refusals` only mention Phase C explicitly; for `rag_search` the
explanation lives in the `# Tools and how to use them` section. v0.2
candidate: add `"Status: Phase B"` after the `rag_search`
description in the Tools section, mirroring the Phase C / Phase D
status markers.

## Net impact on Phase A.4 exit criteria

| Exit criterion from design log | v0.1 status |
|---|:---:|
| New chats open with `qwen2.5:7b-instruct` by default | ✓ |
| qwen2.5 Model entry carries the v0.1 system prompt | ✓ |
| Spanish reply to Spanish greeting | ✓ |
| English reply to English greeting | ✗ (Issue L) |
| qwen2.5 refuses HA control with Phase C pointer | ✓ |
| qwen2.5 refuses RAG with Phase B pointer | ✗ (Issue B — refuses but no phase pointer) |
| `llama3:latest` unchanged in behavior | ✓ |
| (new from v0.1) `time_now` actually invoked when asked | ✗ (Issue T) |

5 of 8 design-log exit criteria met. Issue T is the only one
that blocks Phase B (the assistant's tool-calling muscle must work
before we wire `rag_search`).

## Operational footnotes

- No `openwebui` restart was performed during v0.1 apply or
  validation. Container has been continuously up since 19:36 UTC
  (post-recovery from the v0 partial-wipe incident).
- `time_now` Tool source at
  `/home/diego/homelab/ai-stack/openwebui-tools/tools/time_now.py`
  is unchanged. The Phase A.3 happy-path proves the Tool works in
  isolation.
- No new audit-log entries for `time_now` since the v0.1 apply,
  consistent with the V-10 / V-10b / V-12 failures.
- Decisions to add to ROADMAP.md when this lands: **D-32, D-33,
  D-34** (from the design log). D-33 and D-34 are *aspirational
  until Issue T is resolved* — they describe the rule the prompt
  intends to enforce; v0.1 demonstrates that the rule alone is
  insufficient for qwen2.5.

## Recommended next step (NOT performed; awaiting decision)

Phase B (RAG tool) **should not start** while `time_now` is silently
not invoking from chat. Three viable next moves, ordered by risk:

| Option | What | Pros | Cons |
|--------|------|------|------|
| **A — diagnose first (recommended)** | Direct Ollama probe: `curl http://127.0.0.1:11434/api/chat` with the v0.1 system prompt + `time_now` tool definition + `"¿qué hora es?"`. Confirms whether the regression is at the model layer (qwen2.5 ignoring tool when system prompt is present) or at the Open WebUI layer (tool-injection ordering with a custom prompt). | Tells us if v0.2 is the right fix or if Open WebUI's prompt+tools wiring needs work | ~30 min |
| **B — v0.2 prompt iteration without diagnosis** | Apply the three v0.2 candidates from §"Issues": drop `time_now()` signature, drop `[1]` example, drop language ambiguity escape | Fast | Might still fail if root cause is at Open WebUI layer |
| **C — rollback to v0** | Restore `/tmp/amarolab-phaseA4-v0_1-backup/webui.db.pre-v0_1` | Returns to known v0 state | Loses the V-5a / V-11 fixes |

My recommendation: **Option A** first (diagnose), then either v0.2
or an Open WebUI integration fix depending on what the diagnosis
shows.

## Cross-references

- Design: [`2026-06-15_phaseA4-prompt-v0.1-design.md`](2026-06-15_phaseA4-prompt-v0.1-design.md)
- v0 apply (failures that v0.1 was trying to fix): [`2026-06-15_phaseA4-default-model-and-prompt-applied.md`](2026-06-15_phaseA4-default-model-and-prompt-applied.md)
- v0 design: [`2026-06-15_phaseA4-default-model-and-prompt-design.md`](2026-06-15_phaseA4-default-model-and-prompt-design.md)
- Phase A.3 (Tool works in isolation): [`2026-06-15_phaseA3-tool-canary-applied.md`](2026-06-15_phaseA3-tool-canary-applied.md)
- Tool runtime contract: [`../FUNCTIONS_COMPATIBILITY_REPORT.md`](../FUNCTIONS_COMPATIBILITY_REPORT.md)
- Audit log: `/srv/homelab/data/openwebui/amarolab-audit.log`
- Pre-v0.1 webui.db backup: `/tmp/amarolab-phaseA4-v0_1-backup/webui.db.pre-v0_1`
- Pre-A.4 webui.db backup: `/tmp/amarolab-phaseA4-backup/webui.db.pre-A4`
