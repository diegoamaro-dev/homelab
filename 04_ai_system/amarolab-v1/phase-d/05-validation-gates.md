# Phase D — Validation Gates (G-D1…G-D6)

- **Assistant:** **AURORA** (Amarolab Personal AI
  Assistant).
- **Status:** D-1.1 skeleton.
- **Convention:** Each gate mirrors the Gate G-5
  pattern from Phase C — explicit pre-condition,
  procedure, acceptance criteria, evidence captured
  in a dated apply log.

---

## 1. Validation philosophy

From [`../../../07_operations/lessons_learned.md`](../../../07_operations/lessons_learned.md):

- **Lesson 002** — Read / Write / Verify / Restore.
- **Lesson 005** — Make it work, validate, harden,
  document.
- **Lesson 013** — Validate tools individually.

D-1 therefore validates **per component** first
(G-D1 / G-D2 / G-D3), **then** the pipeline against a
no-effect entity (G-D4), **then** the pipeline against
the Gate G-5 real entity (G-D5), **then** failure
modes (G-D6). Phase D-1 does not close until all six
gates are documented.

---

## 2. G-D1 — Whisper STT canary

**Goal.** Prove `aurora-whisper` can transcribe a
known utterance correctly via **both** the Wyoming
protocol and the HTTP shim.

**Pre-condition.** `aurora-whisper` (Wyoming) and the
HTTP shim are deployed per
[`../../../03_services/voice-stack/whisper/faster-whisper-deployment.md`](../../../03_services/voice-stack/whisper/faster-whisper-deployment.md).

**Procedure.**

1. Record a 5-second WAV on the workstation PC of a
   known phrase (e.g., "is the printer on").
2. Submit it via the Wyoming protocol (using
   `wyoming-cli` or the documented test client).
3. Submit it via the HTTP shim
   (`POST /v1/audio/transcriptions` with `model=whisper-1`).
4. Capture the transcripts.
5. Measure end-to-end latency for each path.

**Acceptance.**

- Both transcripts match the spoken phrase modulo case
  and punctuation.
- Both latencies are recorded; if HTTP path > 5 s on
  a 5 s clip, raise C-D-04 (model-size decision).
- No errors in `aurora-whisper` logs.

**Evidence.** `09_logs/2026-MM-DD_phaseD_gate_gd1_applied.md`

---

## 3. G-D2 — Piper TTS canary

**Goal.** Prove `aurora-piper` can synthesize a known
text correctly via **both** the Wyoming protocol and
the HTTP shim.

**Pre-condition.** `aurora-piper` is deployed per
[`../../../03_services/voice-stack/piper/piper-deployment.md`](../../../03_services/voice-stack/piper/piper-deployment.md).

**Procedure.**

1. Submit a known text via Wyoming (e.g., "AURORA
   activada").
2. Submit the same text via the HTTP shim
   (`POST /v1/audio/speech`).
3. Save both audio outputs.
4. Play each on the workstation PC speakers.
5. Inspect spectrograms / inspect audibility.

**Acceptance.**

- Both audio outputs play audibly on the workstation.
- Voice timbre matches `es_ES-davefx-medium`.
- No errors in `aurora-piper` logs.

**Evidence.** `09_logs/2026-MM-DD_phaseD_gate_gd2_applied.md`

---

## 4. G-D3 — Wake-word configuration verification

**Goal.** Prove `aurora-wakeword` is reachable and
correctly registered with HA. **Not** an end-to-end
always-listening test — D-1 uses push-to-talk via the
browser; G-D3 only confirms the configuration surface
so that D-2 hardware satellites can plug in
unchanged.

**Pre-condition.** `aurora-wakeword` deployed per
[`../../../03_services/voice-stack/wakeword/openwakeword-deployment.md`](../../../03_services/voice-stack/wakeword/openwakeword-deployment.md);
Wyoming integration added to HA.

**Procedure.**

1. In HA Settings → Voice assistants, confirm
   `openWakeWord` appears as a wake-word provider.
2. Confirm `ok_nabu` is selectable.
3. Send a synthetic wake-word probe via `wyoming-cli`
   (a known clip of "ok nabu") to `aurora-wakeword`.
4. Inspect container logs for the detection event.

**Acceptance.**

- HA UI lists openWakeWord as available.
- `ok_nabu` is selectable in the pipeline editor.
- `aurora-wakeword` logs a detection for the probe clip.

**Evidence.** `09_logs/2026-MM-DD_phaseD_gate_gd3_applied.md`

---

## 5. G-D4 — Safe-entity end-to-end (`input_boolean.aurora_voice_canary`)

**Goal.** Prove the full pipeline (PC mic → HA Assist
→ qwen2.5 via HA Ollama → HA intent → entity state
change → Piper response) against a no-effect entity.

**Pre-condition.**

- G-D1, G-D2, G-D3 all closed.
- HA Assist pipeline `AURORA v1` configured per
  [`../../../03_services/voice-stack/ha-assist/pipeline-spec.md`](../../../03_services/voice-stack/ha-assist/pipeline-spec.md).
- `input_boolean.aurora_voice_canary` created in HA
  and marked "Expose to voice assistants".
- No other entity is exposed for voice.

**Procedure (Read → Write → Verify → Restore).**

1. Read pre-state: voice "is the voice canary on?"
   → AURORA reports `off` (assumed initial state).
2. Write: voice "turn on the voice canary."
   → AURORA confirms, HA state = `on`.
3. Verify: voice "is the voice canary on?"
   → AURORA reports `on`.
4. Restore: voice "turn off the voice canary."
   → HA state = `off`, AURORA confirms.

**Acceptance.**

- Each pipeline cycle produces a transcript in HA's
  voice pipeline debug log.
- Each state change is logged in HA logbook.
- TTS response is audible and intelligible on each
  step.
- Baseline (`off`) is restored at end.

**Evidence.** `09_logs/2026-MM-DD_phaseD_gate_gd4_applied.md`

---

## 6. G-D5 — Real-device end-to-end (`switch.impresora_3d`)

**Goal.** The voice analogue of Gate G-5 — same
entity, same sequence, full physical round-trip
through Mosquitto + Z2M.

**Pre-condition.**

- G-D4 closed.
- `switch.impresora_3d` exposed to voice assistants
  in HA.
- Mosquitto hardened (already true since 2026-06-17).
- Operator physically able to confirm device state
  (visual / Z2M state retained).

**Procedure (mirrors Gate G-5).**

1. Pre-read (voice): "is the 3D printer on?"
   → expect `off`.
2. Write (voice): "turn on the 3D printer."
   → expect plug `on` within Z2M settle window.
3. Verify (voice): "is the 3D printer on?"
   → expect `on`.
4. Restore (voice): "turn off the 3D printer."
   → expect plug `off`.

**Acceptance.**

- All four voice exchanges complete within the
  pipeline timeout.
- HA logbook records both state transitions.
- Z2M MQTT publishes both transitions on
  `zigbee2mqtt/Impresora 3D`.
- Physical plug state restored to baseline (`off`).
- HA voice pipeline log shows the four cycles
  cleanly.

**Evidence.** `09_logs/2026-MM-DD_phaseD_gate_gd5_applied.md`

---

## 7. G-D6 — Failure-mode rehearsal

**Goal.** Document graceful degradation under
realistic component failures.

**Pre-condition.** G-D5 closed.

### 7.1 Whisper down

1. `docker stop aurora-whisper`.
2. Attempt a voice command via HA Assist.
3. Capture HA's error response.
4. `docker start aurora-whisper`.

Acceptance: HA reports an STT error; no command is
issued to any entity.

### 7.2 Piper down

1. `docker stop aurora-piper`.
2. Attempt a voice command.
3. Verify the command **still executes** (HA → intent
   → entity) but TTS confirmation is silent / shows
   error in pipeline log.
4. `docker start aurora-piper`.

Acceptance: command lands; HA logs the TTS failure
explicitly.

### 7.3 Ollama unreachable

1. `docker stop ollama` (verify backup state first
   per Lesson 010).
2. Attempt a voice command.
3. HA Assist should time out per pipeline timeout.
4. `docker start ollama`.

Acceptance: pipeline times out cleanly; no partial
state change; conversation agent error surfaced.

**Evidence.** `09_logs/2026-MM-DD_phaseD_gate_gd6_applied.md`

---

## 8. Phase D-1 closeout criteria

D-1 closes when **all** of the following hold:

- G-D1, G-D2, G-D3, G-D4, G-D5, G-D6 all have a
  dated apply log under `09_logs/`.
- Each gate's evidence matches its acceptance
  criteria.
- `switch.impresora_3d` is restored to baseline
  `off`.
- `00_overview/CURRENT_STATE.md`,
  `AMAROLAB_HANDOFF.md`, `ROADMAP.md` updated to
  reflect Phase D-1 outcome (per Lesson 005,
  documentation last).

---

## 9. Out of scope for D-1 validation

- Always-listening wake-word from a hardware
  satellite (D-2).
- Multi-room concurrent voice (D-2+).
- Voice quality A/B between Piper voices (D-2).
- Spanish dialect tuning (D-2).
- RTX node fallback (D-3).

---

## 10. Related documents

- [`02-target-architecture.md`](02-target-architecture.md)
- [`03-component-spec.md`](03-component-spec.md)
- [`04-security-and-permissions.md`](04-security-and-permissions.md)
- Gate G-5 closeout (the chat-side template that
  G-D5 mirrors):
  [`../../../09_logs/2026-06-17_phaseC_gate_g5_applied.md`](../../../09_logs/2026-06-17_phaseC_gate_g5_applied.md)
