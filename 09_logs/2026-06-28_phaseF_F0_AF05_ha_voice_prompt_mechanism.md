# F-0 Finding — AF-05: HA Voice System Prompt Update Mechanism

**Date:** 2026-06-28  
**Phase:** F-0 Behavioral Audit  
**Finding reference:** AF-05 (from `04_ai_system/phase_f_architecture.md` §11)  
**Status:** VALIDATED — dynamic update confirmed; recommended mechanism is `input_text` entity + Jinja2 template

---

## Context

AF-05 validates the mechanism for updating the HA Assist (Aurora voice) system prompt from a nightly script, as required by the Phase F architecture. The architecture specifies a "nightly refresh" of the voice LLM configuration reading from `aurora-context-voice.txt`, but the mechanism ("REST API vs. direct config write") was unvalidated.

---

## Step 1 — Where the prompt is defined

### Storage location

The HA Ollama Conversation integration stores its configuration in:

```
/srv/homelab/homeassistant/.storage/core.config_entries
```

Relevant entry (read-only inspection, values sanitised):

```json
{
  "domain": "ollama",
  "entry_id": "01KVB08CQ2WTFA4MQ7FTF0NXVZ",
  "title": "http://127.0.0.1:11435",
  "state": "loaded",
  "subentries": [
    {
      "subentry_id": "01KVB0A3NE2PBXKFFANSJPNN85",
      "subentry_type": "conversation",
      "title": "Ollama Conversation",
      "data": {
        "model": "qwen2.5:7b-instruct",
        "prompt": "You are a voice assistant for Home Assistant.\nAnswer questions about the world truthfully.\nAnswer in plain text. Keep it simple and to the point.",
        "max_history": 20,
        "num_ctx": 8192,
        "llm_hass_api": ["assist"],
        "keep_alive": -1,
        "think": false
      }
    }
  ]
}
```

**The prompt is a flat string stored in the subentry `data.prompt` field.**

### Storage type

- **Not file-based** — there is no external `.yaml` or `.txt` file the integration reads.
- **Not entity-based** (currently) — the prompt does not reference any HA entity.
- **Internal storage** — loaded from `.storage/core.config_entries` at startup into HA's in-memory config entry registry. The in-memory value is what the integration reads on every request.

### Integration state from REST API (`GET /api/config/config_entries/entry`)

```json
{
  "supports_options": false,
  "supports_unload": true,
  "supported_subentry_types": {
    "conversation": { "supports_reconfigure": true }
  }
}
```

Key flags: `supports_options: false` (no standard options update endpoint), `supports_unload: true` (integration can be reloaded), `conversation subentry: supports_reconfigure: true` (reconfigure is supported, but only via UI config flow — no REST endpoint available).

---

## Step 2 — Whether the prompt is static or dynamic

### The prompt IS rendered as a Jinja2 template on every conversation turn

From HA 2026.3.1 source (`/usr/src/homeassistant/homeassistant/components/conversation/chat_log.py`):

```python
# chat_log.py, _async_expand_prompt_template()
return template.Template(prompt, self.hass).async_render(
    {
        "ha_name": self.hass.config.location_name,
        "user_name": user_name,
        "llm_context": llm_context,
    },
    parse_result=False,
)
```

This is called from `async_provide_llm_data()` on every conversation request, **before** the message is sent to Ollama. The `prompt` string is treated as a Jinja2 template, with the full HA template context available (including `states()`, `state_attr()`, HA helper entities, etc.).

**This is the key architectural enabler.** The prompt does not need to be a static string. It is re-evaluated on every voice request.

---

## Step 3 — Update mechanism options

### Option A — `input_text` entity + Jinja2 reference (RECOMMENDED)

**Mechanism:**

1. Create an `input_text` helper entity: `input_text.aurora_voice_context` (max_length 255 — must be configured via YAML since the UI default is 100)
2. Modify the stored voice prompt once (via HA UI or one-time config reload) to include a Jinja2 reference:
   ```
   You are a voice assistant for Home Assistant called Aurora.
   {{ states('input_text.aurora_voice_context') }}
   Answer in plain text. Keep it simple and to the point.
   ```
3. In `bin/aurora-context`, after writing `aurora-context-voice.txt`, call the HA REST API:
   ```
   POST /api/services/input_text/set_value
   {
     "entity_id": "input_text.aurora_voice_context",
     "value": "2026-06-28 04:15 | ok | backup ok | 17 containers up | no anomalies"
   }
   ```
4. No reload. No restart. The template is re-evaluated on every voice request.

**Properties:**

| Property | Value |
|---|---|
| Requires HA restart | No |
| Requires integration reload | No |
| Requires pipeline reload | No |
| Requires one-time setup | Yes — add `input_text` entity and modify stored prompt once |
| Nightly update mechanism | `POST /api/services/input_text/set_value` |
| Update takes effect | Immediately on next voice request |
| Voice service interruption | None |
| `input_text` max length | 255 chars (needs YAML config: `max_length: 255`) |
| `aurora-context-voice.txt` target size | ≤200 chars (fits within 255) |
| HA token already available | Yes — `HA_LLAT` in `ai-stack/.env` |

**Why this is preferred:** The template evaluation happens inside the HA conversation pipeline at request time. No file synchronisation, no reload cycle, no downtime window. The nightly `bin/aurora-context` script can call `input_text/set_value` as an additional step after writing the context files — no architectural complexity.

---

### Option B — Direct `.storage` edit + `homeassistant.reload_config_entry`

**Mechanism:**

1. `bin/aurora-context` reads `.storage/core.config_entries`, modifies `subentries[0].data.prompt`, writes the file back atomically
2. Calls `POST /api/services/homeassistant/reload_config_entry` with `entry_id: 01KVB08CQ2WTFA4MQ7FTF0NXVZ`
3. HA unloads and reloads the Ollama integration (`supports_unload: true` confirmed)
4. The conversation entity is recreated with the new prompt value

**Properties:**

| Property | Value |
|---|---|
| Requires HA restart | No |
| Requires integration reload | Yes — `homeassistant.reload_config_entry` |
| Brief voice downtime | Yes — seconds during reload |
| Risk | Race condition if HA writes to `.storage` concurrently |
| HA token already available | Yes — `HA_LLAT` in `ai-stack/.env` |

**Why this is not preferred:** Direct `.storage` manipulation is fragile — HA actively manages this file. A concurrent write from HA during the script's edit window would corrupt or lose the change. The reload also introduces a brief service interruption.

---

### Option C — Leave voice prompt static, manual update per phase

As specified in AF-05: "If automated refresh is not feasible, the voice system prompt is updated manually each phase; document as a known manual step."

This is the fallback position, but it is not required — Option A is feasible.

---

## Step 4 — conversation.reload assessment

The `conversation.reload` service reloads the intent matchers for the **built-in conversation agent** (NLP parsing for built-in intents). It does not reload the Ollama conversation entity or refresh its configuration. **Not applicable for this use case.**

---

## Recommended architecture for F-3/F-5

```
bin/aurora-context (04:15 nightly)
│
├── reads signal files
├── writes ai-stack/aurora/aurora-context.json
├── writes ai-stack/aurora/aurora-context.md
├── writes ai-stack/aurora/aurora-context-voice.txt
│   └── content: "2026-06-28 04:15 | ok | backup ok | 17 containers up | no anomalies"
│
└── POST /api/services/input_text/set_value            ← NEW step in F-3/F-5
    entity_id: input_text.aurora_voice_context
    value: <content of aurora-context-voice.txt>
```

Voice request path (after F-3 setup):

```
Voice input → Whisper (STT) → Aurora v1 pipeline
  → Ollama conversation entity
    → chat_log.async_provide_llm_data()
      → _async_expand_prompt_template()
        → Jinja2 renders {{ states('input_text.aurora_voice_context') }}
          → current entity value = "2026-06-28 04:15 | ok | ..."
        → prompt injected into system message
    → Ollama (qwen2.5:7b-instruct)
  → Piper (TTS) → voice response
```

The voice pipeline reads the current `input_text.aurora_voice_context` value on every request. The entity value is updated once per night by `bin/aurora-context`. No reload, no restart.

---

## Pre-implementation requirements surfaced by this audit

1. **Create `input_text.aurora_voice_context` helper** with `max_length: 255`. Must be configured in YAML (not UI) to exceed the 100-char UI default. Add to a `helpers.yaml` include or directly in `configuration.yaml`.

2. **One-time prompt update**: modify the stored Ollama conversation prompt to include `{{ states('input_text.aurora_voice_context') }}`. This requires a one-time config entry update via the HA UI (Settings → Devices & Services → Ollama → Ollama Conversation → Configure). After this one-time change, all subsequent updates are via `input_text/set_value` with no reload.

3. **HA credential**: `HA_LLAT` is already in `ai-stack/.env` and available to `bin/aurora-context`. The existing token is sufficient for `input_text/set_value` calls.

4. **Architecture note**: this mechanism means the voice context update is instantaneous (takes effect on the next voice request, not the next HA cycle). The `aurora-context-voice.txt` file remains the source of truth written by `bin/aurora-context`, and the `input_text` entity mirrors it.

---

## AF-05 disposition

**VALIDATED.** Dynamic voice prompt update is confirmed feasible without HA restart, pipeline reload, or integration reload.

**Mechanism:** `input_text` entity + Jinja2 template reference in the stored Ollama prompt. Update via `POST /api/services/input_text/set_value` from `bin/aurora-context`.

**Architecture change from the original AF-05 description:** The architecture document referenced "script writes single-line content into HA voice LLM config via HA REST API or direct config write." The validated mechanism is the REST API path (Option A), but it operates through an `input_text` entity rather than directly modifying the stored prompt. The stored prompt is modified **once** (at F-3 setup time) to add the Jinja2 reference; thereafter all nightly updates go through the entity.

**F-3 scope addition**: add `input_text.aurora_voice_context` creation and Jinja2 prompt setup to F-3 scope. The nightly `input_text/set_value` call is added to `bin/aurora-context` in F-2 (or F-3 if F-2 completes before F-3 voice integration).

---

## Cleanup confirmation

Read-only audit (except file read of `.storage/core.config_entries` and HA source). No HA configuration modified. No integration reloaded. No git operations performed.
