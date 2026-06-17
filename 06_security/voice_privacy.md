# Voice Privacy — AURORA

- **Scope:** Privacy and security posture of the
  voice surface of AURORA (Amarolab Personal AI
  Assistant).
- **Status:** D-1.1 skeleton. Companion to
  [`security_posture.md`](security_posture.md). This
  file is the **durable** reference for what voice
  data exists, where it lives, who can reach it, and
  how it is retained.

---

## 1. Principles (extending `security_posture.md`)

1. **All voice processing is local.** No third-party
   STT, TTS, wake-word, or conversation API.
2. **No audio crosses WAN.** Mic and TTS audio remain
   on LAN or inside Docker networks.
3. **No persistent audio at rest by default.** Audio
   frames are processed and discarded. Optional debug
   logging is documented per gate when used.
4. **Voice control surface is narrower than chat.**
   Voice can only act on entities explicitly toggled
   "Expose to voice assistants" in HA. Chat tools
   have the D-12 allowlist; voice has the HA
   exposure toggle.
5. **One operator at a time in D-1.** Multi-user
   voice posture is D-2+.

---

## 2. Data flow

```
PC mic ─► Browser ─► HA UI ─► HA Assist pipeline
                                │
                                ├─► aurora-whisper (STT) ── frames discarded
                                │
                                ├─► HA Ollama (qwen2.5)  ── prompt + response in HA memory
                                │
                                └─► aurora-piper (TTS) ─── audio to HA UI ─► Browser ─► PC speaker
```

Each hop, and what crosses it:

| Hop | Payload | Retention default |
|---|---|---|
| PC mic → Browser | Raw mic audio | In-memory only; not stored by browser |
| Browser → HA | Encoded audio (Opus / WAV) | In HA's transient pipeline buffer |
| HA → Whisper (Wyoming TCP) | Audio frames | Discarded after transcription |
| HA → Ollama | Transcript text + system prompt | Not persisted by Ollama beyond inference |
| Ollama → HA | Response text | Stored briefly in HA pipeline log (rolling, HA-configured retention) |
| HA → Piper | Response text | Discarded after synthesis |
| Piper → HA → Browser → speaker | Synthesised audio | In-memory; not stored |

---

## 3. What HA persists

HA's voice pipeline log records (per HA's own retention
policy):

- Pipeline run ID and timestamp.
- Wake-word event (when used).
- STT transcript (text).
- Conversation prompt sent to the agent.
- Agent response (text).
- TTS request (text).
- Entity actions triggered.
- Error events.

This is **operationally necessary** for debugging.
It is also **PII-relevant**: transcripts may contain
spoken household conversation snippets if a false
wake-word fires (D-2+) or if push-to-talk is held too
long (D-1).

### 3.1 Retention guidance

| Setting | Default | AURORA posture |
|---|---|---|
| HA voice pipeline log retention | HA default (typically 10 days) | Accepted in D-1. Revisit in D-2 once always-listening is added. |
| HA logbook entity history | HA default | Accepted. |
| Whisper container logs | Per Docker | Stdout only. No audio in logs. |
| Piper container logs | Per Docker | Stdout only. |
| openWakeWord container logs | Per Docker | Stdout only. Detection events but no audio content. |

---

## 4. Network exposure

| Surface | Reachable from |
|---|---|
| `aurora-whisper` (Wyoming :10300) | `ai-local_default` only |
| `aurora-whisper-http` (HTTP :8000) | `ai-local_default` only |
| `aurora-piper` (Wyoming :10200) | `ai-local_default` only |
| `aurora-piper-http` (HTTP :8001) | `ai-local_default` only |
| `aurora-wakeword` (Wyoming :10400) | `ai-local_default` only |
| HA Assist endpoint | Reachable from operator's LAN — same exposure as HA itself |
| Open WebUI voice (mic/play) | Same exposure as Open WebUI itself |

**No new host port is published by Phase D-1.** No
Cloudflared route is added for voice surfaces.

---

## 5. Authentication

| Surface | Auth |
|---|---|
| HA Assist UI | HA's existing user auth |
| Open WebUI mic / play | Open WebUI's existing user auth |
| Wyoming endpoints (HA → Whisper / Piper / wakeword) | None at the Wyoming layer; isolation via Docker network |
| HTTP shims (Open WebUI → Whisper / Piper) | None at the HTTP layer; isolation via Docker network |
| Ollama (HA Ollama integration → Ollama) | None at the Ollama layer; isolation via Docker network |

No secrets are introduced. The "no auth on internal
Docker network" posture matches the existing pattern
already used by Open WebUI ↔ Ollama ↔ Qdrant.

---

## 6. Voice exposure ramp-up policy

A new entity is added to "Expose to voice assistants"
**only** via a dated apply log under `09_logs/`:

- The log states the entity, the rationale, the
  domain it belongs to, and the expected voice
  phrases.
- Default-deny applies until the apply log lands.
- Removal is also via apply log.

Reset rule: at any point, the operator can run
`/api/voice_assistant/clear_exposures` (or the
HA UI equivalent) to reset exposure to zero, then
re-add via apply logs.

---

## 7. False-wake-word handling (D-2+)

When always-listening hardware is added in D-2:

- Wake-word runs on the satellite (HA Voice PE) or
  on UM790 (M5 / ESP32 streaming).
- A false-positive uploads a short audio window to
  Whisper.
- Whisper transcribes; conversation agent decides.
- Mitigations applicable from D-2 onward:
  - Tune `WAKEWORD_THRESHOLD` upward if FP rate is
    noticeable.
  - Limit voice exposure to high-confidence intent
    targets.
  - Document an operator-facing "voice off" toggle
    that disables the pipeline at the HA layer
    without removing the containers.

D-1 has no always-listening surface, so this risk
does not apply.

---

## 8. Operator visibility

- HA's voice pipeline debug panel shows the most
  recent transcripts and entity actions.
- Open WebUI's chat log shows any voice-originated
  chat exchanges via the mic button.
- `amarolab-audit.log` continues to record chat-side
  Tool calls. **Voice-originated entity actions do
  not currently land in `amarolab-audit.log`** —
  this is Q-D-05, an explicit gap accepted for D-1
  and tracked for D-2.

---

## 9. Production segregation

- Guardian Cloud is untouched by Phase D.
- The voice pipeline shares Mosquitto and Z2M with
  the existing automation surface but does not
  modify their configuration.
- Mosquitto hardening (2026-06-17) remains in force;
  voice commands traversing
  Open WebUI → ha_call_service → HA → MQTT → Z2M
  continue to do so under the authenticated
  `homeassistant` user.

---

## 10. Related documents

- [`security_posture.md`](security_posture.md) — overall security posture
- [`../03_services/zigbee-stack/mosquitto/auth-hardening.md`](../03_services/zigbee-stack/mosquitto/auth-hardening.md) — MQTT auth boundary
- [`../03_services/voice-stack/README.md`](../03_services/voice-stack/README.md) — voice service layout
- [`../04_ai_system/amarolab-v1/phase-d/04-security-and-permissions.md`](../04_ai_system/amarolab-v1/phase-d/04-security-and-permissions.md) — phase-scoped security delta
- [`../07_operations/lessons_learned.md`](../07_operations/lessons_learned.md) — operational rules
