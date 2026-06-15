# Phase A.4 — system prompt v0.1 — DESIGN

- **Date approved:** 2026-06-15
- **Scope:** Iterate the v0 system prompt attached to
  `qwen2.5:7b-instruct` to fix the three regressions reported in
  [`2026-06-15_phaseA4-default-model-and-prompt-applied.md`](2026-06-15_phaseA4-default-model-and-prompt-applied.md).
  **One API write** (replace `params.system` on the qwen2.5 model row).
  Nothing else changes: default model, tool scoping, refusal behaviour,
  per-model isolation, and the audit log all stay as they are.
- **Supersedes:** the v0 system prompt text installed at 19:34 UTC on
  2026-06-15.
- **Superseded by:** none yet.

## What this log captures (and why it exists)

v0 validation found 4 of 17 V- checks failing (V-5a, V-6a, V-6b,
V-10). The application log already documents the symptoms and root
causes. **This file is the design lock for the fix** — what the v0.1
prompt looks like, why each change addresses a specific failure, and
what the exit criteria for the re-apply are. The user requested a log
of this design before the prompt is changed.

## Failure → fix map

| V-check | v0 symptom | Root cause | v0.1 fix |
|---|---|---|---|
| V-5a (Spanish greeting) | Reply did not mention "Amarolab" | Prompt told the model *who it is* but never told it to *say so* when greeted | **New `# First turn` section**: "introduce yourself as Amarolab Assistant in a single short opening sentence on the very first reply of a conversation, then answer; do not repeat on later turns" |
| V-6a (English greeting) | Same | Same | Same fix |
| V-6b (English→Spanish) | Reply to `"hi there"` was Spanish | v0 said *"Default to Spanish if the user's language is ambiguous"* — model treated short greetings as ambiguous | **Rewritten `# Language` section**: explicit per-language rules; *only* default to Spanish on a turn where the user has not yet written anything |
| V-10 (`¿qué hora es?` → fake `[1]`) | Model wrote literal `[1]` and described `time_now(...)` as a string instead of invoking the tool | v0's `# Citations` section *"cite each fact as [N]"* was interpreted as *"render `[N]` literally in the reply"*. Tool was never invoked (audit log: 0 entries during the probe) | **Two changes:** (a) new CRITICAL RULES block under `# Tools and how to use them` mandating that real tool calls are issued and forbidding the model from writing function signatures or `[N]` placeholders in its reply text; (b) rewritten `# Citations` section that defines citations as a *derivative* of an actual tool result, with explicit ordering (call → receive → reply → cite). |

The fixes are targeted and minimal. They do not change persona
text, tool list, refusal list, per-model scoping, or any other
locked decision.

## Decisions added in v0.1 (D-32 … D-34 — to be appended to [`../04_ai_system/amarolab-v1/ROADMAP.md`](../04_ai_system/amarolab-v1/ROADMAP.md))

### D-32 — First-turn self-introduction is mandatory

The prompt instructs the model: *on the very first reply of a
conversation, introduce yourself as "Amarolab Assistant" in a
single short opening sentence; do not repeat on later turns.*

Rationale: v0 told the model what it *is* but not what it should
*say*. qwen2.5 followed the persona but didn't sign its replies.
Explicit instruction closes the gap with one sentence; "do not
repeat" prevents Phase B/D chats from becoming verbose.

### D-33 — Tool invocation rule: the model MUST issue a real call, never describe one

The `# Tools and how to use them` section now ends with a CRITICAL
RULES block:

- When a user asks for current time / date / weekday, the model
  must emit a real `time_now` tool call.
- The model must not write the function signature in its reply
  text. It must not write a literal `[1]` or any placeholder.
- If a tool is not wired (rag_search, system_status), the model
  must say so in plain text, not pretend to call it.

Rationale: v0's hands-off "use this when relevant" wording was too
gentle. qwen2.5 interpreted the prompt's literal `[N]` example as
*"render `[N]` in text"* rather than *"emit a tool call and cite
its result"*. The new rule is procedural: invoke first, then cite.

### D-34 — Citation grammar is a derivative of an actual tool result

The `# Citations` section becomes explicit about ordering:

```
1. Call the tool.
2. Receive the result.
3. Write your reply, optionally citing the result inline as [1].
4. End with a "[1] <source>" footer line.
If step 1 didn't happen, you have no citation to render.
```

This replaces v0's *"When you use a tool result, cite each fact as
[N]"* which qwen2.5 parsed without the precondition.

D-34 **refines** D-31 (citation grammar still uses `[N]` inline +
final footer); the change is to the *precondition*, not the
grammar. D-31 stays valid; D-34 adds the "no tool, no citation"
guard.

## Draft v0.1 prompt — literal text

This is what lands in `params.system` for the
`qwen2.5:7b-instruct` Model entry on apply. Lines wrapped ~75 cols
for readability; the database stores the unwrapped form.

```
You are Amarolab Assistant, a local AI running on this homelab.
You help diego operate his homelab and his projects.

# First turn

On the very first reply of a conversation, introduce yourself as
"Amarolab Assistant" in a single short opening sentence, then
answer the user's actual question. Do not repeat the introduction
on later turns.

# Language

Match the language of the user's MOST RECENT message:
- Spanish message → Spanish reply.
- English message → English reply.
- Other language → reply in that language if you can; otherwise
  ask in Spanish whether the user prefers Spanish or English.

Only default to Spanish on a turn where the user has not yet
written anything.

# Style

- Concise, technical, practical.
- Prefer documented facts over assumptions.
- When you don't know, say so — don't invent.

# Tools and how to use them

You have three planned tools. Their current implementation status:

1. time_now(timezone?, format?) — APPLIED.
   Returns the current date and time in Europe/Madrid by default.

2. rag_search(collection, query, top_k?) — NOT YET WIRED (Phase B).
   Will search indexed documentation across four corpora:
     - homelab_docs     — homelab infrastructure
     - guardian_cloud   — Guardian Cloud product docs (read-only)
     - ensambla2        — Ensambla2 product docs
     - myfreetour       — placeholder, not yet indexed
   Do not call it. If the user asks a doc-grounded question, explain
   it will be available in Phase B and offer the user's best-effort
   answer from your own knowledge, clearly labelled as such.

3. system_status(scope) — NOT YET WIRED (Phase D).
   Will inspect live infrastructure. Do not call it. If the user
   asks for live system info, explain it will be available in
   Phase D.

CRITICAL RULES for tools:

- When a user asks for current time, date, or weekday, you MUST
  issue a real tool call to time_now. Do not write the function
  signature in your reply text. Do not write a literal "[1]" or
  any other placeholder. Issue the actual tool call; the runtime
  will return the result; THEN write your reply using that result.
- If you cannot use a tool because it is not wired yet, say so in
  plain text. Do not pretend to call it.

# Citations

Citations are ONLY for facts you obtained from an actual tool
invocation whose result you have just received.

Order of operations:
  1. Call the tool.
  2. Receive the result.
  3. Write your reply, optionally citing the result inline as [1].
  4. End with a "[1] <source>" footer line.

If step 1 didn't happen, you have no citation to render. Do not
write "[N]" markers or footer lines based on an imagined tool call.

# Refusals — explicit, no apology theater

You cannot do any of these. Refuse politely and name the planned
phase (when applicable):

- Home Assistant control (turn on/off devices, change automations).
  Status: Phase C, not yet implemented.
- Shell command execution.
  Out of scope; you are treated as adversarial input.
- Filesystem modifications (create/edit/delete files, even in /tmp).
  Out of scope; no file-write tools exist.
- Guardian Cloud backend or source-tree changes.
  Guardian Cloud is production; you have read-only RAG over its
  docs only.

If a user asks for any of the above, explain the action is
unsupported in v1 and name the phase (if any) that will enable it.
```

Character count: ~2.9 KB (vs v0's 2.3 KB). The new content is the
`# First turn` block, the CRITICAL RULES block, and the rewritten
`# Citations` ordering.

## Implementation plan (for the eventual `…-applied.md` log — NOT executed here)

When v0.1 application is approved:

1. **Re-use the same script pattern as Phase A.4 apply**:
   `/tmp/amarolab_phaseA4_apply.py` already does GET → mutate → POST
   the full record. Update the `SYSTEM_PROMPT` constant to the v0.1
   text, set `TARGET_MODEL = "qwen2.5:7b-instruct"`, and run only
   the W-1 step (the W-2 workspace-default write is unchanged from
   the v0 apply — `DEFAULT_MODELS` is already
   `"qwen2.5:7b-instruct"`).
2. **Verify the write round-tripped**: `GET
   /api/v1/models/model?id=qwen2.5:7b-instruct` → `params.system`
   starts with `"You are Amarolab Assistant, a local AI running on
   this homelab.\nYou help diego operate his homelab"`,
   `meta.toolIds == ["time_now"]`, `meta.description` unchanged.
3. **Re-run the 17 V- checks** from
   `/tmp/amarolab_phaseA4_validate.py`. Append three extra
   audit-log assertions:
   - V-10b: after the `¿qué hora es?` probe, a new `time_now`
     entry with `result_code: "ok"` exists in
     `/srv/homelab/data/openwebui/amarolab-audit.log` with a
     timestamp within the validation window.
   - V-11 (new): English follow-up after Spanish greeting → reply
     switches to English (confirms language-match works per-turn,
     not just per-conversation).
   - V-12 (new): after V-10 the reply does NOT contain the literal
     string `time_now(` (would indicate the model is still
     describing the call instead of issuing it).

No `openwebui` restart should be required (v0 apply worked without
one; the manual restart there was a recovery action, not a
prerequisite).

## Exit criteria (re-validation)

All of these must hold:

| ID | Criterion | Source |
|----|-----------|--------|
| Carry-over | V-1 .. V-4 (default model, system prompt landed, toolIds preserved, llama3 untouched, llama3.2 untouched) all PASS | v0 validation set |
| Carry-over | V-7 .. V-9 (refusals, llama3 isolation) all PASS | same |
| New | V-5a, V-6a — qwen2.5 first reply contains "Amarolab" on both Spanish and English greetings | D-32 |
| New | V-6b — qwen2.5 reply to `"hi there"` is in English | v0.1 `# Language` |
| New | V-10 — qwen2.5 reply to `"¿qué hora es?"` contains an actual ISO date or `HH:MM` time **AND** the audit log contains a fresh `time_now` entry with `result_code: "ok"` | D-33 + D-34 |
| New | V-11 — second turn in English after a Spanish first turn switches language correctly | tightened `# Language` |
| New | V-12 — qwen2.5 reply does NOT contain the literal string `time_now(` | D-33 |

**Total target:** 19 / 19 PASS (the original 17 plus V-11 and V-12).

If any FAIL, the application log will record honestly and recommend
either a v0.2 micro-fix or a rollback to the pre-A.4 state.

## What stays unchanged

- D-27 (per-model scope on qwen2.5 only).
- D-28 (persona "Amarolab Assistant"; default Spanish; concise /
  technical / practical; documented facts over assumptions).
- D-29 (prompt names all three Phase A.2 tools with status).
- D-30 (refusal block for four out-of-scope action classes).
- D-31 (citation grammar = `[N]` inline + final footer) —
  **clarified** by D-34, not replaced.
- `meta.toolIds = ["time_now"]` on qwen2.5 (D-20).
- `DEFAULT_MODELS = "qwen2.5:7b-instruct"` (v0 apply W-2).
- `llama3:latest` row (D-27 still says don't touch).
- `llama3.2:latest` row (same).
- `time_now` Tool source at
  `/home/diego/homelab/ai-stack/openwebui-tools/tools/time_now.py`.
- Audit log path `/srv/homelab/data/openwebui/amarolab-audit.log`.
- All other containers, env vars, ingest cron, Qdrant collections.

## What this log is NOT

- An application log. Nothing has been changed in `webui.db` since
  the v0 apply.
- A re-validation of v0. The 4 v0 failures still hold on disk;
  any chat right now still uses the v0 prompt.
- A revision of the design documents under
  `04_ai_system/amarolab-v1/`. Those describe what v1 *is* and
  remain immutable; this log describes a tactical iteration on the
  prompt artefact only.

## Decisions to append to ROADMAP.md (when applied)

| # | Decision | When | Source |
|---|---|---|---|
| D-32 | First-turn self-introduction as "Amarolab Assistant" is mandatory; single short sentence; do not repeat on later turns | 2026-06-15 | Phase A.4 v0.1 design |
| D-33 | Tool invocation rule: model MUST issue a real tool call (never describe one in text, never write literal `[N]` placeholders) when a wired tool can answer the question | 2026-06-15 | Phase A.4 v0.1 design |
| D-34 | Citation precondition: a citation may only be rendered after an actual tool invocation that returned a result. Refines (does not replace) D-31's citation grammar | 2026-06-15 | Phase A.4 v0.1 design |

## Cross-references

- v0 design: [`2026-06-15_phaseA4-default-model-and-prompt-design.md`](2026-06-15_phaseA4-default-model-and-prompt-design.md)
- v0 apply (the source of the 4 failures): [`2026-06-15_phaseA4-default-model-and-prompt-applied.md`](2026-06-15_phaseA4-default-model-and-prompt-applied.md)
- Tool runtime contract: [`../FUNCTIONS_COMPATIBILITY_REPORT.md`](../FUNCTIONS_COMPATIBILITY_REPORT.md)
- Phase A.3 (`time_now` install + happy path before the prompt existed): [`2026-06-15_phaseA3-tool-canary-applied.md`](2026-06-15_phaseA3-tool-canary-applied.md)
- Audit log: `/srv/homelab/data/openwebui/amarolab-audit.log`
- v0 backup of `webui.db`: `/tmp/amarolab-phaseA4-backup/webui.db.pre-A4` (kept; safe to delete after v0.1 is accepted)
