# HA Assist Pipeline — `AURORA v1`

- **Scope:** The Home Assistant Assist pipeline that
  fronts AURORA (Amarolab Personal AI Assistant) on
  the voice side.
- **Status:** D-1.1 skeleton. **Not yet created.**
  Configuration lands in HA UI at D-1.5.

---

## 1. Pipeline identity

| Field | Value |
|---|---|
| Pipeline name | `AURORA v1` |
| Default language | `es-ES` (revisit during G-D5 prep) |
| Secondary language | `en-US` (fallback for English commands) |

---

## 2. Slot configuration (planned)

| Slot | Provider | Endpoint | Model / Voice / Word |
|---|---|---|---|
| Wake word | openWakeWord (Wyoming) | `aurora-wakeword:10400` | `ok_nabu` |
| STT | faster-whisper (Wyoming) | `aurora-whisper:10300` | `base-int8` |
| Conversation | HA Ollama integration | `http://ollama:11434` | `qwen2.5:7b-instruct` |
| TTS | Piper (Wyoming) | `aurora-piper:10200` | `es_ES-davefx-medium` |

Note on the conversation slot: HA's **native Ollama
integration** is used (not Open WebUI). This keeps
voice and chat decoupled — the chat path can be
restarted or recreated without disrupting voice.

---

## 3. Exposure ramp-up

Per the security model in
[`../../../04_ai_system/amarolab-v1/phase-d/04-security-and-permissions.md`](../../../04_ai_system/amarolab-v1/phase-d/04-security-and-permissions.md)
§2.

| Stage | Exposed entities | Gate |
|---|---|---|
| D-1.5 initial | `input_boolean.aurora_voice_canary` (new HA helper) | G-D4 |
| D-1.6 | + `switch.impresora_3d` | G-D5 |
| D-2+ | per documented apply log; one entity per change | — |

**Always-denied** (never expose to voice
assistants):

- Any `homeassistant.*` system service
- Any `hassio.*` supervisor surface
- Any `recorder.*` storage entity
- Any HA entity related to Guardian Cloud

---

## 4. Pipeline timeout

| Setting | Value |
|---|---|
| Pipeline timeout | TBD — measured during G-D5 prep |
| Conversation agent timeout | TBD — set after measuring qwen2.5 voice-prompt latency |
| STT timeout | TBD — set after measuring G-D1 latency |

Default values are accepted in HA at first
configuration. Tuning happens after measurement, per
Lesson 002 ("validate before documenting").

---

## 5. UI access (D-1)

| Front door | Path |
|---|---|
| HA browser UI | Sidebar → Assist → voice icon → push-to-talk |
| HA companion app (mobile) | Voice tile if/when configured (optional in D-1) |
| Open WebUI | Mic button in chat (uses HTTP shims, not this pipeline) |

D-1 expects the operator to test from the workstation
browser, since that PC is the validation hardware.

---

## 6. Configuration order (planned for D-1.5)

1. Confirm `aurora-whisper`, `aurora-piper`,
   `aurora-wakeword` are healthy (Wyoming probes).
2. Add three Wyoming Protocol integrations in HA
   (one per endpoint).
3. Add the HA Ollama integration; confirm it can list
   `qwen2.5:7b-instruct`.
4. Create the `AURORA v1` pipeline with the slots
   above.
5. Create `input_boolean.aurora_voice_canary` HA
   helper.
6. Expose only `input_boolean.aurora_voice_canary` to
   voice (G-D4 scope).
7. Capture the configuration in
   `09_logs/2026-MM-DD_phaseD_pipeline_configured.md`.

---

## 7. Validation hooks

- G-D4 — first run-through of this pipeline.
- G-D5 — same pipeline with the printer entity added
  to exposure.
- G-D6 — failure-mode rehearsals through this
  pipeline.

Specs in
[`../../../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md`](../../../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md).

---

## 8. Related documents

- [`../wyoming/overview.md`](../wyoming/overview.md)
- [`../whisper/faster-whisper-deployment.md`](../whisper/faster-whisper-deployment.md)
- [`../piper/piper-deployment.md`](../piper/piper-deployment.md)
- [`../wakeword/openwakeword-deployment.md`](../wakeword/openwakeword-deployment.md)
- [`../../../04_ai_system/amarolab-v1/phase-d/02-target-architecture.md`](../../../04_ai_system/amarolab-v1/phase-d/02-target-architecture.md)
- [`../../../04_ai_system/amarolab-v1/phase-d/04-security-and-permissions.md`](../../../04_ai_system/amarolab-v1/phase-d/04-security-and-permissions.md)
- Apply log (D-1.5):
  `09_logs/2026-MM-DD_phaseD_pipeline_configured.md`
