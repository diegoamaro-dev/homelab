# Phase A.4 — Open WebUI default model + system prompt v0 — DESIGN

- **Date approved:** 2026-06-15
- **Scope:** Lock the **default tool-calling model** and the **v0
  system prompt** for the Amarolab Assistant in Open WebUI. Both
  changes happen in Open WebUI configuration (workspace default
  setting + per-Model entry in `webui.db`). **Design only.** No
  Open WebUI UI changes were made; the default model is still
  unchanged; no system prompt has been loaded.
- **Supersedes:** none.
- **Superseded by:** none (will be marked when the corresponding
  `…-applied.md` log lands).

## What this log captures (and why it exists)

Phase A.3 closed with the `time_now` Tool live in `webui.db`, scoped
per D-20 to `qwen2.5:7b-instruct` only — but the workspace default
model is still whatever it was before Phase A: each new chat requires
the user to pick qwen2.5 from the dropdown, and there is no system
prompt directing the assistant's persona, language preference, tool
routing, or refusal behaviour. Phase A.4 fixes both.

This is a **design** phase — nothing on disk changes — so without
this log the five locked decisions below would live only in the
conversation transcript.

## Decisions locked in A.4 (D-27 … D-31 — to be appended to [`../04_ai_system/amarolab-v1/ROADMAP.md`](../04_ai_system/amarolab-v1/ROADMAP.md))

### D-27 — System-prompt scope = **per-model only, on `qwen2.5:7b-instruct`**

The prompt is attached to the existing per-model Model entry in
`webui.db` (the same entry that already carries
`meta.toolIds=["time_now"]` per D-20), not set as the workspace-wide
default system prompt.

Rationale:

- Mirrors D-20's per-model tool scoping. Same blast radius, same
  rollback path.
- Keeps `llama3:latest` and `llama3.2:latest` clean as **fallback
  non-tool chat models**. A user who picks llama3 from the dropdown
  gets a vanilla LLM, not a tool-mediated assistant pretending it has
  tools it can't see.
- Removes the failure mode where a non-tool-capable model receives
  prompt instructions to call `time_now` and either hallucinates
  results or apologises in a loop.

Implementation: write to the `params.system` field of the
`qwen2.5:7b-instruct` Model row in `webui.db`. Same row, same
update path that D-25 already exercises for `meta.toolIds`.

### D-28 — Persona = **Amarolab Assistant; default Spanish; concise / technical / practical; documented facts over assumptions**

The prompt opens with a four-line persona block:

```
You are Amarolab Assistant, a local AI running on this homelab.
You help diego operate his homelab and his projects.

Language: respond in the user's language. Default to Spanish.
Style: concise, technical, practical. Prefer documented facts
over assumptions. When you don't know, say so — don't invent.
```

Rationale:

- "Amarolab Assistant" matches the sub-project name in `04_ai_system/amarolab-v1/`.
- Default Spanish matches the operator's locale (Ourense) and the
  language of most existing homelab/project documentation that the
  assistant will eventually search via `rag_search`.
- "Respond in the user's language" preserves the cross-language
  retrieval property already validated in the Phase 1.5 reranker
  benchmark (Spanish queries on English content and vice versa).
- "Documented facts over assumptions" is the operator's
  conversation-style preference, transferred into the prompt so the
  assistant inherits it without prompting per-turn.

### D-29 — Tool routing description includes **all three Phase A.2 tools** (`time_now`, `rag_search`, `system_status`) — even though only `time_now` is wired today

The prompt's tool catalog enumerates the three A.2 tools and labels
each with its **current implementation status** and the
**phase that will wire it**:

- `time_now` — APPLIED
- `rag_search` — Phase B (not wired)
- `system_status` — Phase D (not wired)

The model is instructed to **refuse politely** when asked to do
something only an unwired tool could do, and (when relevant) to name
the phase that will enable it.

Rationale:

- The prompt becomes forward-compatible: when Phase B and Phase D
  land, only the per-tool status flips, not the entire prompt
  structure.
- The model does not get to "discover" tools mid-conversation by
  receiving them only when Phase B / D land. The schema is stable
  from the user's first interaction.
- Refusing politely *with the planned phase named* keeps the user
  informed without requiring a separate "roadmap" command.

This decision overrides the alternative "grow the prompt phase by
phase" approach — that would have produced three different prompt
versions during v1 development and risked drift between the prompt
and the actual roadmap.

### D-30 — Refusal behaviour = **explicit refusals for the four out-of-scope action classes**

The prompt closes with an explicit refusal block listing what the
assistant **cannot do**, even if asked nicely:

1. **Home Assistant control** (turn on/off devices, change
   automations) — status: Phase C, not yet implemented.
2. **Shell command execution** — out of scope; the LLM is treated as
   adversarial input.
3. **Filesystem modifications** (create / edit / delete files,
   including `/tmp`) — out of scope; no file-write tools exist.
4. **Guardian Cloud backend changes** (source tree, API) — Guardian
   Cloud is production; the assistant has read-only RAG over its
   docs only (D-09).

Each refusal is a one-line "I cannot do X because Y, planned in
phase Z" template the model can adapt.

Rationale: explicit refusals are shorter, more honest, and easier to
audit than "polite deflection." They also reinforce the trust model
(D-06) without requiring the model to derive it from generic safety
training.

### D-31 — Citations = **keep the existing `[N]` pattern from `time_now`; extend to `rag_search` in Phase B**

`time_now` already uses `[1]` as the in-line citation, with a final
`[1] <iso-timestamp>` reference. The prompt instructs the assistant
to apply the same pattern to *every* tool result it surfaces:

```
When you use a tool result, cite each fact as [N] where N matches
the tool result index, and list sources at the end as
  [1] <source>
This rule applies to time_now today and will apply to rag_search
in Phase B.
```

Rationale:

- Stable citation grammar = one fewer thing for the user to learn
  between phases.
- The `[N]` pattern is what the Phase A.3 V- checks validated for
  `time_now`; reusing it keeps that validation valid for future
  tools.
- Makes the audit log easier to grep: a chat reply with `[1]` is
  evidence the assistant grounded on a real tool result.

## Draft system prompt — v0

This is the literal text that lands in `webui.db.params.system` for
the `qwen2.5:7b-instruct` Model entry on Phase A.4 application.
Lines wrapped at ~70 cols for readability; the database will store
the unwrapped form.

```
You are Amarolab Assistant, a local AI running on this homelab.
You help diego operate his homelab and his projects.

# Language
Respond in the user's language. Default to Spanish if the user's
language is ambiguous.

# Style
- Concise, technical, practical.
- Prefer documented facts over assumptions.
- When you don't know, say so — don't invent.

# Tools

You have three planned tools. Their current implementation status:

1. time_now(timezone?, format?) — APPLIED.
   Returns the current date and time in Europe/Madrid by default.
   Use it whenever the user asks "what time", "what date",
   "what day of the week", or for stamping log entries.

2. rag_search(collection, query, top_k?) — NOT YET WIRED (Phase B).
   Will search indexed documentation across four corpora:
     - homelab_docs     — homelab infrastructure
     - guardian_cloud   — Guardian Cloud product docs (read-only)
     - ensambla2        — Ensambla2 product docs
     - myfreetour       — placeholder, not yet indexed
   Do not pretend to call it. If the user asks a doc-grounded
   question, explain it will be available in Phase B and offer
   the user's best-effort answer from your own knowledge,
   clearly labelled as such.

3. system_status(scope) — NOT YET WIRED (Phase D).
   Will inspect live infrastructure (containers, ports, volumes,
   disk). Do not pretend to call it. If the user asks for live
   system info, explain it will be available in Phase D.

# Citations

When you use a tool result, cite each fact as [N] where N matches
the tool result index, and list sources at the end:
  [1] <source>
Applies to time_now today and to rag_search in Phase B.

# Refusals — explicit, no apology theater

You cannot do any of these. Refuse politely and tell the user why:

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

Character count: ~1.8 KB. Will land in `webui.db.params.system`
(text column; no schema constraint to worry about).

## Implementation plan (for the eventual `…-applied.md` log — NOT executed here)

When Phase A.4 application is approved, the steps are:

1. **Set workspace default model.** Open WebUI admin → Settings →
   Interface → Default Model = `qwen2.5:7b-instruct`. Equivalent
   API: `POST /api/v1/configs/default/models` with
   `{ "models": ["qwen2.5:7b-instruct"] }`.
2. **Attach the v0 system prompt to the qwen2.5 Model entry.**
   Open WebUI admin → Workspace → Models → `qwen2.5:7b-instruct`
   → System Prompt field. Equivalent API:
   `POST /api/v1/models/model/update` with the Model id and
   `meta.params.system` populated.
3. **Verify per-model scoping holds.** Open a new chat without
   selecting a model (should default to qwen2.5). Send "hola" —
   reply should sign as "Amarolab Assistant" and be in Spanish.
   Open another chat, switch model to `llama3:latest`, send the
   same — reply should be vanilla (no Amarolab persona).
4. **Validate refusal behaviour.** From a qwen2.5 chat, ask "apaga
   las luces del salón" (Phase C) and "busca en los docs cómo va
   recovery en Guardian Cloud" (Phase B). Expect explicit refusal
   in both cases naming the planned phase.
5. **Capture the application log** at
   `09_logs/2026-06-15_phaseA4-default-model-and-prompt-applied.md`
   with the on-disk evidence (sqlite query output, screenshots if
   any, validation result table V-1..V-N).

No new containers, no new env vars, no `webui.db` schema changes
beyond writes to the existing `model` row's `meta.params.system`
field.

## Exit criteria

- New chats open with `qwen2.5:7b-instruct` selected by default.
- The qwen2.5 Model entry in `webui.db` has the v0 system prompt
  populated in `meta.params.system` (or equivalent location per
  Open WebUI 0.8.10's schema — to confirm at apply time).
- A qwen2.5 chat replies as **Amarolab Assistant** in Spanish to a
  Spanish greeting, in English to an English greeting.
- A qwen2.5 chat correctly refuses (with phase pointer) when asked
  for HA control, shell exec, filesystem write, or Guardian Cloud
  backend changes.
- `llama3:latest` chats are **unchanged** — no Amarolab persona, no
  tool routing, vanilla LLM behaviour.
- This design log is referenced from `AMAROLAB_HANDOFF.md`,
  `CURRENT_STATE.md`, and `ROADMAP.md` (cross-link added in the
  application log).

## Out of scope for A.4

- Wiring `rag_search` or `system_status`. They are *named* in the
  prompt with NOT-YET-WIRED labels; they are not implemented here.
- Editing the `time_now` Tool or its scoping (D-20).
- Loading the system prompt into any other model.
- Touching Home Assistant, Guardian Cloud, or any container.
- Writing the application log (that lands in a separate file when
  application is approved and executed).

## Decisions that should be added to ROADMAP.md (when applied)

Append to the "Decisions taken (locked)" table:

| # | Decision | When | Source |
|---|---|---|---|
| D-27 | System-prompt scope = per-model, attached to `qwen2.5:7b-instruct` Model entry only. Other models stay clean. | 2026-06-15 | Phase A.4 design approval |
| D-28 | Persona = "Amarolab Assistant"; default language Spanish; style concise / technical / practical; prefer documented facts over assumptions | 2026-06-15 | Phase A.4 design approval |
| D-29 | System prompt names all three Phase A.2 tools (`time_now`, `rag_search`, `system_status`) with current implementation status, so the prompt is forward-compatible with Phase B and Phase D | 2026-06-15 | Phase A.4 design approval |
| D-30 | Explicit refusal block for four out-of-scope action classes: Home Assistant control (Phase C), shell exec, filesystem writes, Guardian Cloud backend changes | 2026-06-15 | Phase A.4 design approval |
| D-31 | Citation grammar = `[N]` inline + final `[N] <source>` list; extends from `time_now` today to `rag_search` in Phase B | 2026-06-15 | Phase A.4 design approval |

## What this log is NOT

- An application log. Nothing has been changed in `webui.db`, in the
  Open WebUI workspace settings, or in any Model entry.
- An approval to execute. Per the user's instruction, this design
  requires a separate explicit "apply Phase A.4" before any UI
  change happens.
- A revision of any immutable design doc in `04_ai_system/amarolab-v1/`.
  Those describe what v1 *is*; this log describes what Phase A.4
  *will do*.
