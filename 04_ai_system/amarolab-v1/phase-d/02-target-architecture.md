# Phase D — Target Architecture

- **Ecosystem:** **AMAROLAB** — Personal Innovation
  Lab and Digital Infrastructure Ecosystem. Provides
  infrastructure, automation, knowledge systems, AI
  services and documentation.
- **Assistant:** **AURORA** — Personal AI Assistant
  for the AMAROLAB ecosystem.
- **Independent project on AMAROLAB infrastructure:**
  **Guardian Cloud** (out of scope for Phase D; not
  modified by this work).
- **Status:** Approved at design level (2026-06-17).
  This document is the durable architectural reference
  for AURORA's voice surface. Component specs live in
  [`03-component-spec.md`](03-component-spec.md).

---

## 1. One assistant, two front doors

AURORA is **one** assistant — one brain, one set of
tools, one knowledge base, one audit trail — accessed
through **two** front doors:

```
                ┌────────────────────────────────────┐
                │   AURORA                           │
                │   qwen2.5:7b-instruct (Ollama)     │
                │   + tools: time_now, rag_search,   │
                │     audit_search, ha_get_state,    │
                │     ha_call_service                │
                │   + Qdrant RAG                     │
                │   + amarolab-audit.log             │
                └────────┬───────────────────┬───────┘
                         │                   │
              ┌──────────▼──────┐   ┌────────▼───────────┐
              │ Open WebUI      │   │ Home Assistant     │
              │  • chat         │   │  • Assist          │
              │  • Tool layer   │   │  • intent layer    │
              │    (D-12        │   │    (HA exposure    │
              │    allowlist)   │   │    toggle)         │
              └─────────────────┘   └────────────────────┘
                         ▲                   ▲
                         │                   │
                       browser            browser
                       mic + spk          mic + spk
                       (D-1 path)         (D-1 path)
```

The two front doors are **independent**. Open WebUI does
not depend on HA Assist; HA Assist does not depend on
Open WebUI. They converge inside HA at the entity layer.

---

## 2. Voice pipeline (HA Assist side)

```
PC browser (HA UI)
   │  push-to-talk
   ▼
Home Assistant
   │
   ├── STT  ──► wyoming-faster-whisper  (CPU, UM790)
   │
   ├── Conversation ──► HA Ollama integration ──► ollama: qwen2.5:7b-instruct
   │                       │
   │                       └── HA-exposed entities only
   │
   ├── TTS  ──► wyoming-piper             (CPU, UM790)
   │
   └── Wake word ──► wyoming-openwakeword (CPU, UM790)
                       │
                       └── D-1: deployed but exercised
                             only at the configuration
                             level (push-to-talk via
                             browser). D-2+ uses it on
                             always-listening satellites.
```

Pipeline name in HA: **"AURORA v1"**.

---

## 3. Open WebUI voice surface

Open WebUI consumes the **same** Whisper and Piper via
OpenAI-compatible HTTP shims:

```
PC browser (Open WebUI)
   │  mic button / play-aloud
   ▼
Open WebUI
   │
   ├── STT  ──► HTTP shim ──► faster-whisper (same model files as HA Assist)
   │
   └── TTS  ──► HTTP shim ──► piper          (same voice files as HA Assist)
```

Effect: one Whisper, one Piper, two protocols (Wyoming
for HA, OpenAI HTTP for Open WebUI). The chat path
remains text-first and tool-capable; voice is additive,
not a replacement.

---

## 4. Conversation routing

| Front door | Conversation engine | Entity / capability surface |
|---|---|---|
| Open WebUI (chat) | qwen2.5 via Open WebUI's Ollama-backed model row, with the Tool layer attached | The five tools (`ha_get_state`, `ha_call_service`, etc.) + the D-12 allowlist |
| HA Assist (voice) | qwen2.5 via the **HA Ollama integration** (HA-native) | HA-exposed entities only (the "Expose to voice assistants" toggle) |

These are two different safety boundaries pointing at
the same brain:

- **Tool boundary** governs chat. Documented in
  [`../04-security-and-permissions.md`](../04-security-and-permissions.md).
- **HA exposure boundary** governs voice. Documented in
  [`04-security-and-permissions.md`](04-security-and-permissions.md).

Both ultimately land at HA's entity layer, which is the
single source of truth for what AURORA can do in the
physical world.

---

## 5. Where each component runs

### 5.1 Phase D-1 (CPU-only on UM790)

| Component | Host | Always-on |
|---|---|---|
| faster-whisper (Wyoming + HTTP shim) | UM790 | Yes |
| Piper (Wyoming + HTTP shim) | UM790 | Yes |
| openWakeWord (Wyoming) | UM790 | Yes |
| Mic + speakers (D-1 satellite) | Workstation PC, via browser | n/a (operator's PC) |

### 5.2 Phase D-2 (hardware satellites added)

| Component | Host | Always-on |
|---|---|---|
| All D-1 components | unchanged | unchanged |
| Voice satellite (HA Voice Preview Edition / M5 ATOM Echo / ESP32-S3-BOX) | LAN | Per-device |
| Wake word | runs **on the satellite** (HA Voice Preview Edition does this natively) | Yes |

### 5.3 Phase D-3 (RTX node online)

| Component | Host | Always-on |
|---|---|---|
| Wake word, Piper, small Whisper | UM790 | Yes |
| Large Whisper (`large-v3-int8`) | RTX tower | On demand (Wake-on-LAN from HA) |
| HA Assist pipeline | Dual-route: prefer RTX large model when awake; fall back to UM790 small model | n/a |

Design rule: **HA's Wyoming endpoint URLs use Docker
network aliases, not hard-coded IPs.** When Whisper
relocates, the alias changes; HA changes nothing.
Details in
[`06-rtx-node-bridge.md`](06-rtx-node-bridge.md).

---

## 6. Architectural invariants (do not violate)

1. **AURORA is one assistant.** Two front doors share
   one brain. No second model is introduced for voice
   without an explicit ROADMAP change.
2. **UM790 hosts everything always-on.** Wake word,
   Piper, small Whisper, and the conversation engine
   remain on UM790 even after the RTX node arrives.
3. **RTX is opportunistic, not load-bearing.** The
   house must keep working with the RTX off.
4. **Voice does not bypass HA's entity layer.** Any
   physical effect goes through `ha_call_service`
   (chat path) or HA Assist intents (voice path),
   both of which terminate at HA's entity layer.
5. **No secrets in Git.** Voice adds no new secrets to
   the repo. Any model API keys (if introduced) live
   alongside existing secrets per
   [`../../../06_security/security_posture.md`](../../../06_security/security_posture.md).
6. **All voice components run inside `ai-local_default`**
   with no host ports published. The voice surface is
   not reachable from outside Docker without explicit
   routing.
7. **Guardian Cloud is untouched.** Guardian Cloud is
   an independent project hosted on AMAROLAB
   infrastructure; Phase D does not modify any of its
   surfaces.

---

## 7. Related documents

- [`03-component-spec.md`](03-component-spec.md) — per-container specs
- [`04-security-and-permissions.md`](04-security-and-permissions.md) — voice security delta
- [`05-validation-gates.md`](05-validation-gates.md) — G-D1…G-D6
- [`06-rtx-node-bridge.md`](06-rtx-node-bridge.md) — future migration design
- [`../../../03_services/voice-stack/README.md`](../../../03_services/voice-stack/README.md) — service-level index
