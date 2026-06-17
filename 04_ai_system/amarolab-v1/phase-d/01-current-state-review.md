# Phase D — Current State Review

- **Phase:** D — Voice
- **Assistant:** **AURORA** (Amarolab Personal AI Assistant).
  The on-disk directory `amarolab-v1` is preserved as the
  project's existing v1 namespace; AURORA is the
  human-readable name from Phase D onward and applies to
  the same codebase, model, tools, and audit log.
- **Status:** Design approved. D-1.1 skeleton in flight.
  No installations, no container changes, no config
  changes.
- **Authoritative inputs (read in order, per
  `00_overview/START_HERE.md`):**
  - [`../../../00_overview/AMAROLAB_HANDOFF.md`](../../../00_overview/AMAROLAB_HANDOFF.md)
  - [`../../../00_overview/CURRENT_STATE.md`](../../../00_overview/CURRENT_STATE.md)
  - [`../../../00_overview/ROADMAP.md`](../../../00_overview/ROADMAP.md)
  - [`../../../01_architecture/amarolab_architecture.md`](../../../01_architecture/amarolab_architecture.md)
  - [`../../../06_security/security_posture.md`](../../../06_security/security_posture.md)
  - [`../../../07_operations/lessons_learned.md`](../../../07_operations/lessons_learned.md)

---

## 1. Snapshot at Phase D entry

### 1.1 Stack

| Layer | Component | Status |
|---|---|---|
| Brain | `qwen2.5:7b-instruct` (Ollama) | Operational |
| Chat front door | Open WebUI | Healthy |
| Tools | `time_now`, `rag_search`, `audit_search`, `ha_get_state`, `ha_call_service` | All five validated, Phase C closed |
| RAG | Qdrant — `homelab_docs`, `guardian_cloud`, `ensambla2`, `infra_audits` | Operational |
| Home Assistant | `homeassistant` container | Operational |
| MQTT | Mosquitto — `allow_anonymous false`, `homeassistant` + `zigbee2mqtt` users + ACLs | **Hardened** 2026-06-17 |
| Zigbee | Zigbee2MQTT with Sonoff dongle | Operational; 10 devices interviewed |
| Audit | `/srv/homelab/data/openwebui/amarolab-audit.log` | Operational |
| Voice | none | **Phase D target** |

### 1.2 Hardware available *today* (Phase D-1 budget = €0)

| Item | Notes |
|---|---|
| UM790 Pro server | Ryzen 9 7940HS, 32 GB DDR5. Phase D-1 CPU host for Whisper/Piper/openWakeWord. |
| Workstation PC (operator) | Has microphone + speakers. Browser already used to access HA and Open WebUI. **This is the Phase D-1 voice front-end.** |
| LAN | UM790 reachable from workstation. |
| RTX tower | Not yet present. Reserved as the future on-demand AI compute node per `01_architecture/amarolab_architecture.md`. |
| HA Voice Preview Edition / ESP32 satellites | Not yet purchased. Documented as future hardware in [`../../../03_services/voice-stack/voice-satellites/hardware-options.md`](../../../03_services/voice-stack/voice-satellites/hardware-options.md). |

### 1.3 Lessons that already shape Phase D

From [`../../../07_operations/lessons_learned.md`](../../../07_operations/lessons_learned.md):

- **Lesson 001** — `docker restart` does not reload env;
  every new voice container must be created (not just
  restarted) when its env changes.
- **Lesson 005** — Make it work, validate, harden,
  document. Phase D-1 sticks to this order.
- **Lesson 013** — Tools must be validated individually.
  Phase D validates Whisper, Piper, openWakeWord, the
  pipeline, and end-to-end **separately** (G-D1…G-D6).
- **Lesson 003** — Always restore baseline state after
  any automation test. Voice G-D5 mirrors the Gate G-5
  baseline-restore pattern.

---

## 2. What Phase D adds to the architecture

```
                    ┌──────────────────────────┐
                    │  AURORA — one brain      │
                    │  qwen2.5:7b-instruct     │
                    │  + tools + RAG           │
                    └────┬───────────────┬─────┘
                         │               │
              ┌──────────▼───┐   ┌───────▼──────────┐
              │ Front door 1 │   │ Front door 2     │
              │ Open WebUI   │   │ HA Assist        │
              │ (chat)       │   │ (voice)          │
              └──────────────┘   └──────────────────┘
                         ▲               ▲
                         │               │
                         └──── PC mic / speakers ────┘
                              (D-1 validation path)
```

D-1 introduces **no new hardware**. Both front doors are
exercised through the workstation's existing browser
mic/speakers.

---

## 3. Gate-by-gate readiness

| Gate | Prerequisite | Status |
|---|---|---|
| G-D1 STT canary | faster-whisper Wyoming container | TBD — not deployed |
| G-D2 TTS canary | Piper Wyoming container | TBD — not deployed |
| G-D3 Wake → STT | openWakeWord container | TBD; D-1 exercises configuration only (browser uses push-to-talk) |
| G-D4 Safe-entity end-to-end | HA Assist pipeline + `input_boolean.aurora_voice_canary` helper | TBD |
| G-D5 Real-device end-to-end | Voice exposure of `switch.impresora_3d` | TBD — Gate G-5 entity reused |
| G-D6 Failure modes | All three containers up | TBD |

Validation specs: [`05-validation-gates.md`](05-validation-gates.md).

---

## 4. Open questions captured at entry

| ID | Question | Decision target |
|---|---|---|
| Q-D-01 | Pipeline language: default `es-ES` or auto-detect? | Decide at G-D5 prep |
| Q-D-02 | Whisper model size — `base-int8` vs `small-int8`? | Measure during G-D1 |
| Q-D-03 | Piper voice — `es_ES-davefx-medium` vs alternatives? | Compare during G-D2 |
| Q-D-04 | Push-to-talk only, or attempt always-listening on workstation? | Default to push-to-talk for D-1; always-listening requires hardware satellite (deferred to D-2) |
| Q-D-05 | Should voice command audits land in `amarolab-audit.log` or stay in HA's pipeline log? | Document the gap; bridge in D-2 |

---

## 5. Out of scope for Phase D-1

- Custom wake word ("Hey AURORA").
- Always-listening hardware satellites (HA Voice Preview
  Edition, ESP32, ATOM Echo).
- RTX tower bring-up.
- Multi-room.
- Spanish-only conversation pinning beyond pipeline
  language selection.
- Voice-originated tool calls through Open WebUI's Tool
  layer (voice uses HA Assist's intent layer).

These are tracked in the Phase D roadmap notes in
[`06-rtx-node-bridge.md`](06-rtx-node-bridge.md) and
[`05-implementation-roadmap.md`](../05-implementation-roadmap.md).
