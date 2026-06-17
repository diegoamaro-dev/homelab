# Voice Stack — AURORA

**AURORA** — Amarolab Personal AI Assistant.

This directory holds the durable reference
architecture for AURORA's voice surface. It is the
service-level companion to the Phase D design under
[`../../04_ai_system/amarolab-v1/phase-d/`](../../04_ai_system/amarolab-v1/phase-d/).

---

## Layout

| Path | Purpose |
|---|---|
| [`wyoming/overview.md`](wyoming/overview.md) | Wyoming protocol primer — why it is the spine of the voice stack |
| [`whisper/faster-whisper-deployment.md`](whisper/faster-whisper-deployment.md) | STT — `aurora-whisper` container, model, ports |
| [`piper/piper-deployment.md`](piper/piper-deployment.md) | TTS — `aurora-piper` container, voice, ports |
| [`wakeword/openwakeword-deployment.md`](wakeword/openwakeword-deployment.md) | Wake word — `aurora-wakeword` container |
| [`voice-satellites/hardware-options.md`](voice-satellites/hardware-options.md) | Satellite hardware options (D-1 = PC mic; D-2+ = HA Voice PE, M5 ATOM Echo, ESP32-S3-BOX) |
| [`ha-assist/pipeline-spec.md`](ha-assist/pipeline-spec.md) | HA Assist pipeline configuration |

---

## Status at Phase D-1 entry

| Component | Container | Status |
|---|---|---|
| Whisper STT | `aurora-whisper` | **Not deployed.** Spec captured. |
| Piper TTS | `aurora-piper` | **Not deployed.** Spec captured. |
| openWakeWord | `aurora-wakeword` | **Not deployed.** Spec captured. |
| HA Assist pipeline | `AURORA v1` | **Not created.** Spec captured. |
| Voice satellite | PC browser mic + speakers | Available today (no deploy needed). |

D-1.1 is documentation-only. Container creation lands
in D-1.2 (Whisper), D-1.3 (Piper), D-1.4 (wakeword),
D-1.5 (pipeline).

---

## Rules (apply to every file under this directory)

1. **No secrets.** Variable names and shapes only.
2. **Image tags pinned.** Never `:latest`.
3. **No host ports published.** All voice traffic stays
   on `ai-local_default`.
4. **Container names start with `aurora-`** so the
   voice stack is grouped in `docker ps`.
5. **Env changes require recreate, not restart** —
   Lesson 001 (`07_operations/lessons_learned.md`).
6. **Validate before documenting** — Lesson 002.
7. **Documentation files end with their related apply
   logs** under `09_logs/` so reference docs and
   evidence stay linked.
