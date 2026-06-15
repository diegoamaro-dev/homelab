# Issue T (B-09) — root cause analysis — INVESTIGATION ONLY

- **Date:** 2026-06-15
- **Scope:** Investigate why `time_now` stops being invoked from chat
  when a custom `params.system` is attached to `qwen2.5:7b-instruct`
  in Open WebUI 0.8.10. Determine whether the root cause is at the
  qwen2.5 model layer, the Open WebUI tool-wiring layer, the system
  prompt design, or the Ollama tool-calling layer.
- **What this log is NOT:** an application log. No code, prompt, or
  configuration was modified. Five read-only API probes were made
  (two of which exercised the live `time_now` Tool, adding one
  benign entry to the audit log). No services restarted, no
  containers recreated, no DB writes.
- **Reads / probes performed:**
  - `webui.db` (sqlite, read-only): qwen2.5 Model entry + global
    config.
  - `GET /api/v1/tools/id/time_now` (OWUI admin) for the live tool
    spec.
  - `POST /api/chat` direct to Ollama for four model-layer probes.
  - `POST /api/chat/completions` to Open WebUI for three full-stack
    probes.
  - Source inspection inside the `openwebui` container at
    `/app/backend/open_webui/main.py`, `utils/middleware.py`,
    `utils/task.py`, `utils/plugin.py`, `utils/tools.py`,
    `config.py`, and `/app/build/_app/immutable/chunks/*.js` (the
    Svelte frontend bundle).

## 0. TL;DR

**Issue T is not a model defect, a prompt defect, an Open WebUI
tool-runtime defect, or an Ollama defect.** It is a **validation
methodology artefact** in the V-10 / V-12 probe script.

- The V-10 / V-12 validator calls
  `POST /api/chat/completions` with no `tool_ids` field in the
  request body.
- Open WebUI 0.8.10's `chat_completion` handler reads `tool_ids`
  *only* from the request body
  (`main.py:1783 — "tool_ids": form_data.get("tool_ids", None)`).
  It does **not** auto-resolve `meta.toolIds` from the Model entry
  for this code path. So the inbound chat carries `tool_ids = None`.
- With no `tool_ids`, the tool-resolution branch in
  `process_chat_payload` is skipped entirely. The chat goes to
  qwen2.5 with the v0.1 system prompt as the `system` message and
  **no tools array at all**. The model — given a prompt that
  literally contains the text `time_now(timezone?, format?)` and an
  instruction "cite each fact as `[1]`" — produces the only thing
  the prompt asks for: a citation block that hallucinates the call.
- The Open WebUI **browser UI** populates `tool_ids` automatically
  from the Model entry's `meta.toolIds` (verified in the frontend
  bundle, `chunk GxGTGtKc.js`). So the **real user-facing chat path
  is not broken** — only the programmatic probe path is.

Live evidence (Probe E, §4 below): when the same request is
re-issued with `tool_ids: ["time_now"]` added to the body, the
Open WebUI chat completion returns
`"Actualmente son las 22:29 CEST (...) del lunes 15 de junio de 2026. [1]"`
and the audit log gains one fresh `time_now` invocation. Same
prompt, same model, same Open WebUI, same Ollama. The only
difference is the one missing field in the request body.

## 1. The four-candidate verdict

| Candidate | Verdict | Decisive evidence |
|---|---|---|
| qwen2.5 behaviour | **NOT THE CAUSE** | Probes A, B, C, D (§3) all emit valid native `tool_calls` directly to Ollama under the live v0.1 system prompt + live tool schema, in Spanish *and* English, with and without the system prompt. |
| Open WebUI tool wiring | **PROXIMATE CAUSE — at the OpenAI-compat endpoint only** | `main.py:1783` does not derive `tool_ids` from `meta.toolIds`. `middleware.py:2497` only enters the tool branch when `tool_ids` is truthy. With no `tool_ids` in the body, the tool is never offered to the model. |
| System prompt design | **CONTRIBUTORY (cosmetic) — but irrelevant to the failure to invoke** | The v0.1 `[1]` citation grammar contradicts its own "do not write literal `[1]`" rule in the no-tools-attached fallback. This explains *why* the model fabricated `[1] time_now(...)` instead of refusing — but the failure to invoke is upstream of the prompt. |
| Ollama tool-calling behaviour | **NOT THE CAUSE** | Ollama returns `tool_calls` JSON cleanly whenever Open WebUI does forward a tools array (Probes A, B, C, D direct, and Probe F via Open WebUI's native path). |

## 2. Background — what was already known

| Source | Fact |
|---|---|
| Phase A.3 applied log | Without any system prompt (V-10 in A.3), `time_now` invokes correctly end-to-end. 19/21 V-checks PASS. |
| Phase A.4 v0 applied log | After installing the v0 system prompt + scoping `meta.toolIds=["time_now"]` on the qwen2.5 Model entry, V-10 fails. Audit log: 0 invocations. |
| Phase A.4 v0.1 applied log | After installing the v0.1 prompt with explicit "MUST issue a real tool call" CRITICAL RULES block, V-10 still fails. Audit log: 0 invocations. Same failure mode: `"La hora actual ... [1].\n\n[1] time_now(\"Europe/Madrid\", \"%H:%M:%S\")"`. |
| Validator | `/tmp/amarolab_phaseA4_v0_1_validate.py` — drives all 21 V-checks via `POST /api/chat/completions`. |

The three Phase A logs framed Issue T as a model / prompt regression
caused by the custom system prompt being in scope. The actual cause
is a single missing field in the validator's request body.

## 3. Direct-to-Ollama probes (model layer in isolation)

The probes used the exact live tool spec extracted from
`GET /api/v1/tools/id/time_now`, wrapped in the standard
`{type:"function", function:{...}}` envelope. `temperature: 0`, `seed: 7`.

| Probe | System message | User message | tool_calls? | Verdict |
|---|---|---|---|---|
| **A** | v0.1 prompt (3342 chars, verbatim from `webui.db`) | `¿qué hora es?` | YES — `{"name":"time_now","arguments":{"format":"human","timezone":"Europe/Madrid"}}` | qwen2.5 invokes correctly with the v0.1 prompt attached |
| **B** | v0.1 prompt | `what time is it in Tokyo?` | YES — `{"name":"time_now","arguments":{"timezone":"Asia/Tokyo","format":"human"}}` | language is irrelevant |
| **C** | (none) | `¿qué hora es?` | YES — same shape as A | reproduces A.3 happy-path baseline |
| **D** | minimal "You are a helpful assistant." | `¿qué hora es?` | YES — same shape | confirms no "any prompt breaks it" regression |

All four probes returned `message.content == ""` and a populated
`message.tool_calls`. **qwen2.5:7b-instruct correctly emits native
tool calls under every combination of system-prompt + question
tested, including the live v0.1 prompt verbatim from `webui.db`.**

The "model layer" candidate is eliminated.

## 4. Full-stack probes through Open WebUI (`/api/chat/completions`)

Same `model: qwen2.5:7b-instruct`, same `messages`, same temperature.
Only the body fields differ.

| Probe | Body extra | finish_reason | tool_calls in resp | Rendered content | Audit log delta |
|---|---|---|---|---|---|
| **E** | `"tool_ids": ["time_now"]` | `stop` | `None` (resolved server-side) | `"Actualmente son las 22:29 CEST (...) del lunes 15 de junio de 2026. [1]"` | **+1** (live tool fired) |
| **F** | `"tool_ids": ["time_now"]` AND `"params": {"function_calling": "native"}` | `tool_calls` | populated `[{name:"time_now", arguments:{...}}]` | `""` (model defers execution to caller) | 0 (caller is expected to run the tool — native OpenAI-compat semantics) |
| **G** | none (reproduces V-10) | `stop` | `None` | `"La hora actual en Europa/Madrid es [1].\n\n[1] time_now(\"Europe/Madrid\", \"%H:%M:%S\")"` | 0 |

Probes E, F, G are **identical to V-10 except for the one body
field**. Probe G is the exact V-10 / V-12 failure reproduced on
demand. Probe E shows the failure disappears the moment `tool_ids`
is added to the body. Probe F shows that even native mode produces
a real tool_call from qwen2.5 through the OWUI stack.

## 5. Mechanism — exactly why a missing `tool_ids` produces the V-10 output

Reading the Open WebUI 0.8.10 source in
`/app/backend/open_webui/`:

### 5.1 Where `tool_ids` enters the chat path

`main.py:1685–1830` — the OpenAI-compat chat handler:

```python
metadata = {
    ...
    "tool_ids": form_data.get("tool_ids", None),
    ...
    "params": {
        ...
        "function_calling": (
            "native"
            if (
                form_data.get("params", {}).get("function_calling") == "native"
                or model_info_params.get("function_calling") == "native"
            )
            else "default"
        ),
    },
}
```

- `tool_ids` is read **only from the request body**.
- `meta.toolIds` from the Model entry is **not consulted here**.
- `function_calling` is read from request body **or** Model entry
  params. The qwen2.5 Model entry's `params` is currently
  `{"system": "..."}` only (no `function_calling` field), so it
  defaults to `"default"`.

### 5.2 What "default" function-calling mode does

`middleware.py:2497` and following:

```python
if tool_ids:
    for tool_id in tool_ids:
        ...      # resolve tools via get_tools(...)
    ...
    if tools_dict:
        if metadata.get("params", {}).get("function_calling") == "native":
            metadata["tools"] = tools_dict
            form_data["tools"] = [
                {"type": "function", "function": tool.get("spec", {})}
                for tool in tools_dict.values()
            ]
        else:
            form_data, flags = await chat_completion_tools_handler(
                request, form_data, extra_params, user, models, tools_dict
            )
```

- The outer `if tool_ids:` gate is the load-bearing one. **If
  `tool_ids` is None, none of this runs and the chat proceeds with
  no tools array attached.** That is exactly the V-10 / Probe G
  path.
- In native mode (Probe F), the tools array is attached to
  `form_data["tools"]` and forwarded as-is to Ollama — which is
  identical to what Probes A / B / C / D do directly.
- In default mode (Probe E), `chat_completion_tools_handler` runs a
  *separate* "task" LLM call to extract a JSON tool_call from the
  user's query, runs the tool inline, and inserts the result as a
  source/citation into the **subsequent** user-facing chat call
  (which then runs *without* the tools array but *with* the source
  pre-attached).

### 5.3 The "default" task-call template

From `config.py:2150`:

```python
DEFAULT_TOOLS_FUNCTION_CALLING_PROMPT_TEMPLATE = """Available Tools: {{TOOLS}}

Your task is to choose and return the correct tool(s) ...
Return only the JSON object, without any additional text or explanation.
...
The format for the JSON response is strictly:
{
  "tool_calls": [
    {"name": "toolName1", "parameters": {"key1": "value1"}},
    ...
  ]
}"""
```

The task call uses **this template as the system message** —
**not** the v0.1 prompt. The v0.1 prompt is only attached on the
final user-facing chat call. Simulating the task call directly to
Ollama (with the live `time_now` spec substituted into `{{TOOLS}}`,
in Spanish, English, and with a chat history prefix) all three
times returned a clean `{"tool_calls": [{"name": "time_now", ...}]}`
JSON, which Open WebUI's slicer (`content[content.find("{") :
content.rfind("}") + 1]`) would happily parse. **If `tool_ids` were
attached, default mode would also work** — which is what Probe E
demonstrates.

### 5.4 What the model actually saw in Probe G / V-10 / V-12

With `tool_ids = None`:

- System message: the v0.1 prompt (3342 chars), which contains the
  literal text `time_now(timezone?, format?)` and the literal
  rendering `[1]` as a citation example.
- User message: `¿qué hora es?`.
- Tools: none.

The model has no callable tool. It has been told three contradictory
things by the prompt at once:

1. *"You MUST issue a real tool call to time_now ..."*
2. *"Do not write the function signature ..."* and *"Do not write a
   literal '[1]' ..."*
3. *"Optionally citing the result inline as [1] ... End with a '[1]
   <source>' footer line."*

The contradiction is irresoluble in this state. The model split the
difference: hallucinated a citation footer naming
`time_now("Europe/Madrid", "%H:%M:%S")`, used `[1]` as the inline
marker, and did not invoke anything because nothing was invocable.
Both V-10 and V-12 read this output and reported failure.

### 5.5 What the frontend (UI) does

`/app/build/_app/immutable/chunks/GxGTGtKc.js` (minified Svelte
build):

```
... (ee.info.meta).toolIds ?
  u(ae, [...new Set([...((ee.info.meta).toolIds) ?? []]
                    .filter(pi => o().find(ni => ni.id === pi)))])
  : ...
```

i.e., when a chat opens against a Model entry whose `info.meta`
carries `toolIds`, the UI initialises its local `ae` (the active
tool-id list) from that list. Then in
`/app/build/_app/immutable/chunks/GxGTGtKc.js` again:

```
... tool_ids: _t.length > 0 ? _t : void 0, ...
```

When `_t` (the live tool-id list, derived from `ae`) is non-empty,
the request body includes `tool_ids`. **The UI path therefore
auto-attaches `tool_ids:["time_now"]` for any chat with the qwen2.5
Model entry as long as the user has not manually deselected the
tool from the chat input.** Probe E approximates that real-UI
request.

## 6. Why the previous hypotheses missed it

The Phase A.4 v0 and v0.1 applied logs framed three hypotheses
(quoted from v0.1 §"What v0.1 did NOT fix"):

| # | Original hypothesis | What we found |
|---|---|---|
| 1 | "Prompt-induced description" — the `time_now()` signature line trains the model to render text | The signature line *does* steer the failure-mode output (when no tools are attached), but the failure to invoke is upstream of the prompt. With `tool_ids` present (Probe E) the model invokes regardless of the signature line. |
| 2 | "Tool-injection conflict in Open WebUI 0.8.10 when a custom `params.system` is present" | The `params.system` field is irrelevant to Open WebUI's tool-injection branch. The two are independent: tool resolution is gated by `tool_ids`, prompt resolution is gated by `params.system`. Probes A–D confirm the prompt does not block native tool_calls at the model layer. |
| 3 | "Citation grammar still dominates" — `[1]` interpreted as a literal format | True for the no-tools path. Fixing this in v0.2 would harden the fallback but does not address the missing-`tool_ids` cause. |

Hypothesis (1) was nearly right about *what the model writes*;
hypothesis (3) is the cleanest explanation of the exact text shape;
but the root cause is (2)'s family — Open WebUI's wiring — in a way
not previously suspected.

## 7. Implications

- **Phase A.3's evidence is still valid.** A.3 validated `time_now`
  via the live UI (browser chat), which does include `tool_ids`. The
  invocation count of 7 in the audit log between 17:24–17:28 UTC
  came from real `time_now` calls. A.3's correctness is not in
  question.
- **Phase A.4 v0 and v0.1's "Issue T" finding is a validator bug.**
  The validator omits `tool_ids` from the request. The failure mode
  it reports is exactly what Open WebUI 0.8.10 does for any chat
  call without `tool_ids` — regardless of model, prompt, or
  intent.
- **The real chat experience is likely already working.** Probe E
  is the closest analogue to a UI chat we can produce server-side,
  and it succeeds. The remaining unknown is whether the live UI in
  a browser, with the v0.1 prompt loaded, also produces a real
  invocation. **This must be verified by hand before Phase B starts.**
- **The v0.1 prompt has an independent, latent weakness in the
  no-tools fallback path.** If the UI ever omits `tool_ids` (user
  manually deselects the tool, or a future regression in the
  frontend), the model will hallucinate citations instead of
  refusing. This is worth hardening in v0.2 — see §8.

## 8. Recommendation

Phase B (`rag_search`) **should not be permanently blocked by
Issue T**. The diagnosis is complete; the fix is small and falls
into two unrelated tracks.

### 8.1 Validator track — necessary, smallest possible change

Update the validator script `/tmp/amarolab_phaseA4_v0_1_validate.py`
(and any future validator) so the V-10 / V-10b / V-12 chat-completion
calls include `tool_ids: ["time_now"]` in the request body. Re-run
the validation suite. Expected outcome:

- V-10a passes — reply has a real `HH:MM` / ISO timestamp.
- V-10b passes — a fresh `time_now` line lands in
  `/srv/homelab/data/openwebui/amarolab-audit.log` with
  `result_code: "ok"`.
- V-12 passes — reply does not contain the literal `time_now(`.

This is sufficient to **resolve B-09** at the validator level. No
DB write, no prompt change, no infra change required.

### 8.2 UI-path verification — manual, mandatory before Phase B

Open Open WebUI in a browser (LAN: `http://192.168.178.x:3000`).
Open a new chat with the `qwen2.5:7b-instruct` Model entry as the
selected model. Send `"¿qué hora es?"`. Confirm:

1. The rendered reply contains an actual time (e.g.,
   `"Actualmente son las HH:MM CEST ..."`).
2. A fresh `time_now` JSONL line appears in the audit log within
   the response window.
3. The reply *does not* contain the literal string `time_now(`.

If all three hold, **the real user-facing chat path is correct**
and B-09 is fully resolved. If any one fails, the v0.1 prompt's
no-tools-fallback failure mode is being reproduced by the UI
(unexpected — the UI bundle indicates it auto-attaches `tool_ids`),
and §8.3 becomes necessary.

### 8.3 Phase A.4 v0.2 prompt iteration — independent of B-09, defensive

The prompt has two self-contradictions that produce the exact
hallucination Probe G shows. They should be removed regardless of
B-09's status, because they will resurface in any future scenario
where tools are temporarily unavailable.

| Change | Why |
|---|---|
| Remove the literal `time_now(timezone?, format?)` signature line from `# Tools`. Describe the tool semantically only. | Eliminates the textual artefact the model is currently mimicking when no tool is attached. |
| Remove the literal `[1]` example from `# Citations`. Use prose ("cite numerically from `1`") or no example. | The model parses `[1]` as a format template even when forbidden literally. |
| Replace the contradictory pair ("MUST cite each fact as `[N]`" + "do not write `[N]` without a tool result") with a single positive rule: *"Only cite when a tool result is in this turn's context."* | Removes the contradiction the model is currently resolving by hallucinating. |
| (Optional, v0.3) Set `params.function_calling = "native"` on the qwen2.5 Model entry. | Eliminates the round-trip task call in the default-mode tool handler. qwen2.5's strongest mode is native. Trade-off: native mode in the OpenAI-compat endpoint returns the tool_call to the caller for execution (Probe F); the browser UI handles this, programmatic clients must implement the tool_call loop. |

None of these changes are required to *resolve B-09*. They are
hardening for the prompt's robustness profile.

### 8.4 Blocker B-09 status transition

Recommended in [`../04_ai_system/amarolab-v1/ROADMAP.md`](../04_ai_system/amarolab-v1/ROADMAP.md):

- Reclassify B-09 in the ROADMAP from "Tool-calling regression with
  custom `params.system`" to "Validator omits `tool_ids` in
  `/api/chat/completions` body".
- Note: B-09 **no longer blocks Phase B** once §8.1 (validator
  patch + re-run) and §8.2 (UI verification) are both green.
- Decisions D-33 ("Tool invocation rule") and D-34 ("Citation
  precondition") remain valid as prompt-design intent for v0.2 but
  are no longer aspirational on qwen2.5 — qwen2.5 already honours
  them given proper tool wiring (Probes A, B, F).

## 9. What this investigation deliberately did not do

- No prompt rewrite. v0.2 is still unwritten.
- No DB write. `webui.db` is byte-identical to the start of the
  investigation.
- No service restart. `openwebui`, `ollama`, `qdrant` containers
  were continuously up throughout. Same uptimes as at investigation
  start.
- No Tool source change. `time_now.py` is unchanged.
- No infrastructure change. No new env vars, no
  `homelab-tools`, no Home Assistant tokens, no Guardian Cloud
  touch.
- One incidental side effect: the live `time_now` Tool fired once
  during Probe E (audit log line +1, at `2026-06-15T20:29:21Z`,
  `result_code: "ok"`). This is benign — a legitimate tool call
  from a legitimate user, identical to any other call. Counted in
  §10 below.

## 10. Forensic state at end of investigation

| Item | Value |
|---|---|
| `webui.db` size | 2 334 720 bytes (unchanged) |
| `webui.db` mtime | 2026-06-15 19:49 (unchanged from pre-investigation) |
| qwen2.5 `params.system` length | 3 342 chars (unchanged, v0.1 prompt verbatim) |
| qwen2.5 `meta.toolIds` | `["time_now"]` (unchanged, D-20 preserved) |
| `time_now` Tool installed | yes, content length 5 180 chars (unchanged, A.3 install) |
| Audit log line count | 91 (was 90; +1 from Probe E at `20:29:21Z`) |
| Containers up | `openwebui` (healthy), `ollama`, `qdrant` — same uptimes as session start |
| Pre-flight backups | none new; existing `/tmp/amarolab-phaseA4-backup/webui.db.pre-A4` and `/tmp/amarolab-phaseA4-v0_1-backup/webui.db.pre-v0_1` retained |

## 11. Cross-references

- v0.1 apply (the failure being investigated): [`2026-06-15_phaseA4-prompt-v0.1-applied.md`](2026-06-15_phaseA4-prompt-v0.1-applied.md)
- v0.1 design (the prompt text): [`2026-06-15_phaseA4-prompt-v0.1-design.md`](2026-06-15_phaseA4-prompt-v0.1-design.md)
- v0 apply (where Issue T was first observed): [`2026-06-15_phaseA4-default-model-and-prompt-applied.md`](2026-06-15_phaseA4-default-model-and-prompt-applied.md)
- Phase A.3 (Tool works in isolation, via UI): [`2026-06-15_phaseA3-tool-canary-applied.md`](2026-06-15_phaseA3-tool-canary-applied.md)
- Open WebUI 0.8.10 runtime contract: [`../FUNCTIONS_COMPATIBILITY_REPORT.md`](../FUNCTIONS_COMPATIBILITY_REPORT.md)
- ROADMAP blocker B-09: [`../04_ai_system/amarolab-v1/ROADMAP.md`](../04_ai_system/amarolab-v1/ROADMAP.md)
- Live state: [`../04_ai_system/amarolab-v1/CURRENT_STATE.md`](../04_ai_system/amarolab-v1/CURRENT_STATE.md)
- Audit log: `/srv/homelab/data/openwebui/amarolab-audit.log`
- Tool source: `/home/diego/homelab/ai-stack/openwebui-tools/tools/time_now.py`
- Open WebUI source (read inside the `openwebui` container):
  - `/app/backend/open_webui/main.py:1685–1830` (chat handler, metadata build, line 1783 = `tool_ids` source)
  - `/app/backend/open_webui/utils/middleware.py:2400–2740` (tool resolution + native-vs-default branch)
  - `/app/backend/open_webui/utils/middleware.py:1186–1280` (`get_tools_function_calling_payload` + JSON-slice parser)
  - `/app/backend/open_webui/utils/task.py:429` (`tools_function_calling_generation_template`)
  - `/app/backend/open_webui/config.py:2150` (`DEFAULT_TOOLS_FUNCTION_CALLING_PROMPT_TEMPLATE`)
  - `/app/build/_app/immutable/chunks/GxGTGtKc.js` (frontend `tool_ids` initialisation from `meta.toolIds` and inclusion in request body)
