# Phase A.4 — Open WebUI default model + system prompt v0 — APPLIED (with caveats)

- **Date applied:** 2026-06-15
- **Scope:** Performed the two writes specified in
  [`2026-06-15_phaseA4-default-model-and-prompt-design.md`](2026-06-15_phaseA4-default-model-and-prompt-design.md):
  set workspace default model to `qwen2.5:7b-instruct`, and attach the
  v0 system prompt (2 310 chars) to the `qwen2.5:7b-instruct` Model
  entry in `webui.db`. **Both writes landed.** Validation found
  **13 of 17 V- checks PASS, 4 FAIL** — a known regression in the v0
  system prompt that needs a v0.1 iteration before Phase B begins.
  See §"Validation" and §"Open issues" below.
- **Supersedes:** none (first apply of Phase A.4).
- **Superseded by:** none yet (a v0.1 prompt revision is recommended).

## What was changed in `webui.db`

Both writes performed via Open WebUI 0.8.10's REST API, using a JWT
minted from `WEBUI_SECRET_KEY` against admin user
`3a49344e-acf6-41a1-b28d-8cce95c36c2a` (diego). Same auth pattern as
`ai-stack/openwebui-tools/bin/install_tool`.

### W-1: qwen2.5:7b-instruct `params.system` populated

- **Endpoint:** `POST /api/v1/models/model/update?id=qwen2.5:7b-instruct`
- **Field actually used:** `params.system` (top-level `params`, NOT
  `meta.params.system` as the design log said in §"Implementation plan"
  step 2 and §"Exit criteria". Open WebUI 0.8.10's actual model schema
  has `params` and `meta` as siblings; the system prompt lives in
  `params.system`). **Design-log discrepancy noted in §"Findings" below.**
- **System prompt content:** the literal 2 310-char text drafted in the
  design log §"Draft system prompt — v0".
- **Preserved on update:** `meta.toolIds=["time_now"]` (D-20),
  `meta.description`, `meta.capabilities`, `meta.profile_image_url`,
  `base_model_id`, `is_active=true`.

### W-2: workspace `DEFAULT_MODELS` set

- **Endpoint:** `POST /api/v1/configs/models` (not
  `/api/v1/configs/default/models` — that URL returned the SPA HTML
  shell rather than an API).
- **Body:** full schema (`DEFAULT_MODELS`, `DEFAULT_PINNED_MODELS`,
  `MODEL_ORDER_LIST`, `DEFAULT_MODEL_METADATA`, `DEFAULT_MODEL_PARAMS`
  — all required by the endpoint's pydantic validator).
- **`DEFAULT_MODELS` before:** `null`.
- **`DEFAULT_MODELS` after:** `"qwen2.5:7b-instruct"` (string form;
  the GET response confirms it round-tripped as a string, not a list).
- Other workspace fields kept at their existing values.

## What was deliberately NOT changed

- `llama3:latest` Model row — **untouched**. Still has empty `params`
  and the user's custom `name="Jarvis"` alias (29 121-byte `meta`).
- `llama3.2:latest` Model row — **untouched**. Keeps its pre-existing
  system prompt about Docker tools (which is unrelated to Phase A.4
  and predates this work).
- `phi3:latest` and any other Ollama-resident model — untouched.
- `time_now` Tool source at
  `/home/diego/homelab/ai-stack/openwebui-tools/tools/time_now.py` —
  untouched (Phase A.3 artefact).
- The audit log path at
  `/srv/homelab/data/openwebui/amarolab-audit.log` — receives entries
  exactly as in Phase A.3.

## Validation (17 V- checks, 13 PASS, 4 FAIL)

Full validation script: `/tmp/amarolab_phaseA4_validate.py` (writes
nothing; sends 6 chat probes via `POST /api/chat/completions`).

| # | Check | Result |
|---|-------|:------:|
| V-1 | `DEFAULT_MODELS == 'qwen2.5:7b-instruct'` | ✓ PASS |
| V-2a | `qwen2.5.params.system` length ≥ 2000 | ✓ PASS (2 310) |
| V-2b | `qwen2.5.meta.toolIds == ["time_now"]` (D-20 preserved) | ✓ PASS |
| V-2c | `qwen2.5.meta.description` preserved | ✓ PASS |
| V-3a | `llama3:latest.params` still empty | ✓ PASS |
| V-3b | `llama3:latest.name` still "Jarvis" | ✓ PASS |
| V-4 | `llama3.2:latest.params.system` still has the pre-existing prompt | ✓ PASS |
| V-5a | Spanish greeting reply mentions "Amarolab" | **✗ FAIL** |
| V-5b | Spanish greeting reply is in Spanish | ✓ PASS |
| V-6a | English greeting reply mentions "Amarolab" | **✗ FAIL** |
| V-6b | English greeting reply is in English | **✗ FAIL** |
| V-7a | Spanish HA control prompt → refusal | ✓ PASS |
| V-7b | Refusal names Phase C | ✓ PASS |
| V-8a | Spanish doc-search prompt → "not available" | ✓ PASS |
| V-8b | Reply names Phase B | ✓ PASS |
| V-9 | Same Spanish greeting to `llama3:latest` → no "Amarolab" | ✓ PASS |
| V-10 | "¿qué hora es?" to qwen2.5 → real ISO/HH:MM in reply | **✗ FAIL** |

### Per-criterion summary against the design log's exit criteria

| Exit criterion | Status | Evidence |
|----------------|:------:|----------|
| New chats open with `qwen2.5:7b-instruct` by default | ✓ | V-1 (workspace `DEFAULT_MODELS` set) |
| qwen2.5 Model entry carries the v0 system prompt | ✓ | V-2 |
| Spanish reply to Spanish greeting | ✓ | V-5b |
| English reply to English greeting | ✗ | V-6b — reply was Spanish despite "hi there" prompt |
| qwen2.5 refuses HA control with Phase C pointer | ✓ | V-7 |
| qwen2.5 refuses RAG with Phase B pointer | ✓ | V-8 |
| `llama3:latest` unchanged in behavior | ✓ | V-9 + V-3 |

Persona ("introduce as Amarolab Assistant") and tool-call behaviour
(V-10) are NOT in the design log's strict exit criteria but were
included as defensive checks. Both regressed; see §"Open issues".

## Open issues — v0 system prompt needs a v0.1 revision

Four failed checks fall into three root causes:

### Issue 1 — Self-introduction (V-5a, V-6a)

The prompt says *"You are Amarolab Assistant"* but never explicitly
instructs the model to **introduce itself by name when greeted**.
qwen2.5 followed the system prompt's persona setup but didn't sign
its first reply. Fix: add a line under `# Style` like *"On the first
turn of a conversation, briefly identify yourself as Amarolab
Assistant."* Single-sentence addition, low risk.

### Issue 2 — Language-match strictness (V-6b)

The prompt says *"Respond in the user's language. Default to Spanish
if the user's language is ambiguous."* On `"hi there"` qwen2.5 replied
in Spanish — it appears to have treated everything as ambiguous and
fallen back to Spanish. Fix: tighten the language clause to *"Match
the language of the user's most recent message; default to Spanish
only if the user has not yet sent a message."* Single-sentence fix.

### Issue 3 — Citations vs tool invocation conflation (V-10) — significant

This is the meaningful regression. Asked `"¿qué hora es?"`, qwen2.5
replied:

```
"La hora actual en Europe/Madrid es [1]. ¿Necesitas esta
información para algo en particular?

[1] time_now(timezone="Europe/Madrid", format="%H:%M")"
```

The model **rendered the citation pattern literally** and **described
the tool call instead of issuing it**. The audit log
(`/srv/homelab/data/openwebui/amarolab-audit.log`) confirms
**no `time_now` invocation** for the V-10 prompt — last entry from
this validation run is the Phase A.3 stress-test residue at
15:28:37 UTC.

A direct probe with *"What date is it today? Use your tool."* also
returned a hallucinated `[1]` placeholder with no audit entry.

Root cause hypothesis: the `# Citations` section's instruction
*"When you use a tool result, cite each fact as `[N]`"* is being
interpreted by qwen2.5 as *"render `[N]` in your reply"* rather than
*"first invoke the tool, then cite its returned value"*. The
explicit mention of `time_now` in the `# Tools` section probably
makes the model think it has already "seen" the tool spec and can
synthesise an answer without calling it.

Fix candidates (need a small design iteration before applying):

- Reorder the prompt: put `# Tools` AFTER `# Citations`, so the
  citation rule is read in terms of *generic* tool results before the
  model sees the specific tool list.
- Add an explicit *"You MUST issue a tool call (not describe it in
  text) when a tool can answer the question"* sentence.
- Drop the literal `[N]` example from `# Citations`; let Open WebUI's
  own citation post-processing handle the rendering (it already
  worked for the Phase A.3 happy path before this prompt landed).

The Phase A.3 happy-path validation passed before the system prompt
existed — confirming this is a v0-prompt-induced regression, not a
break in the Tool or the model.

## Findings for future docs

1. **Design-log field-path discrepancy.** The design log refers to
   `meta.params.system` but Open WebUI 0.8.10 stores the per-model
   system prompt at `params.system` (top-level `params`). Both
   `params` and `meta` are siblings on the model row. **Action:**
   add a note to the design log header (does not change the
   decisions D-27..D-31).
2. **Workspace API endpoint name.** The design log says
   `POST /api/v1/configs/default/models`. That URL returns the SPA
   shell. The real endpoint is `POST /api/v1/configs/models`. **Action:**
   correct in the design log.
3. **POST schema is total, not partial.** `/api/v1/configs/models`
   requires the full pydantic schema (5 fields). Sending only
   `DEFAULT_MODELS` returns 422. The model update endpoint behaves
   similarly: if you POST a partial object, fields not in the body
   are dropped (the first probe wiped `meta.toolIds` and
   `meta.description`). **Action (already done in apply):** always
   GET → mutate → POST full object. Future Phase B / D tool installs
   should follow the same fetch-mutate-write pattern.

## Operational footnotes

- `webui.db` was backed up to
  `/tmp/amarolab-phaseA4-backup/webui.db.pre-A4` before any write.
  Kept for one cycle; safe to delete once you accept v0/v0.1.
- The `openwebui` container was restarted once mid-apply
  (after a manual SQL restore corrected the partial wipe noted in
  finding #3) to flush any in-memory model cache. Container resumed
  healthy in ~30 s. Not strictly required by the API path — included
  here for transparency.
- No services other than `openwebui` were touched. No new containers,
  no new env vars, no Qdrant changes, no Ollama changes.
- `ai-stack/openwebui-tools/` source tree unchanged. `time_now.py`
  unchanged.

## Recommended next step

The user told me to **stop after validation**, which I have. Before
Phase B starts, three options:

| Option | What | Pros | Cons |
|--------|------|------|------|
| **A — v0.1 prompt revision** *(recommended)* | Iterate the 3 prompt issues from §"Open issues" and re-run V-5/V-6/V-10. Same writes, new content. | Closes the regression; preserves the design package. | Needs a brief design log entry + re-apply. |
| B — Accept v0 as-is | Live with 13/17 validation; document V-5/V-6/V-10 as known v1 quirks. | Zero extra work. | Time-tool calling is broken in chat. Citation grammar reads as broken to the user. |
| C — Roll back A.4 entirely | Restore `webui.db` from `/tmp/amarolab-phaseA4-backup/webui.db.pre-A4`. | Returns to the Phase A.3 working state. | Loses the default-model + persona work that DOES pass. |

My recommendation is **Option A**, scoped tightly to fix the three
issues without re-opening the broader prompt design.

No changes were made beyond the two writes documented above. Awaiting
your direction.

## Cross-references

- Design: [`2026-06-15_phaseA4-default-model-and-prompt-design.md`](2026-06-15_phaseA4-default-model-and-prompt-design.md)
- Decisions taken (D-27..D-31): [`../04_ai_system/amarolab-v1/ROADMAP.md`](../04_ai_system/amarolab-v1/ROADMAP.md) (append pending — design log §"Decisions that should be added to ROADMAP.md")
- Phase A.3 (preceding): [`2026-06-15_phaseA3-tool-canary-applied.md`](2026-06-15_phaseA3-tool-canary-applied.md)
- Tool runtime contract: [`../FUNCTIONS_COMPATIBILITY_REPORT.md`](../FUNCTIONS_COMPATIBILITY_REPORT.md)
- Audit log: `/srv/homelab/data/openwebui/amarolab-audit.log`
- Backup of pre-A.4 `webui.db`: `/tmp/amarolab-phaseA4-backup/webui.db.pre-A4`
