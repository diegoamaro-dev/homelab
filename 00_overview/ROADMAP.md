# ROADMAP

This document tracks the build phases of **AURORA** —
the Personal AI Assistant for the **AMAROLAB**
ecosystem.

**AMAROLAB** — Personal Innovation Lab and Digital
Infrastructure Ecosystem — provides infrastructure,
automation, knowledge systems, AI services and
documentation.

**Guardian Cloud** is an independent project currently
hosted on AMAROLAB infrastructure; its roadmap is
tracked by the Guardian Cloud project, not in this
document.

Last updated: 2026-06-18 (Phase D-1 closed).

---

## Phase 0

Completed

* Audit
* Remediation
* Documentation consolidation
* Security review
* Backup implementation
* RAG foundation

---

## Phase A

Completed

### Goal

Assistant brain layer

Tasks:

* Evaluate qwen2.5:7b
* Compare against llama3
* Select default model
* Document findings

Outcome:

`qwen2.5:7b-instruct` selected as the primary tool-calling
model (`base_model_id = NULL`, D-35 preserved).

Success criteria met:

Stable local model selected.

---

## Phase B

Completed

### Goal

Tool layer

Tasks:

* time_now()
* rag_search()
* audit_search()

Outcome:

All three tools installed in `webui.db.tool`, attached to
`qwen2.5:7b-instruct` via `meta.toolIds`, and validated
end-to-end. Per-model scope D-20 preserved (legacy
Jarvis tools remain scoped to `llama3*`).

Success criteria met:

Assistant can retrieve knowledge.

---

## Phase C

Completed (2026-06-17 — Gate G-5)

### Goal

Home Assistant integration

Tasks:

* ha_get_state() — installed, attached to qwen2.5,
  validated against real HA read (`sun.sun` →
  `result_code = "ok"`).
* ha_call_service() — installed, attached to qwen2.5.
  Tool-level refusal path validated against
  `recorder.purge` (C-5). First real happy-path write
  validated against `switch.impresora_3d` (Gate G-5 —
  full sequence `off` → `turn_on` → `on` → `turn_off`
  → `off`, all `result_code="ok"`, baseline restored).

Security:

Allowlist only (D-12 enforced at the Tool boundary).

Never allow:

* homeassistant.*
* hassio.*
* recorder.*

Success criteria met:

* Read criterion — met.
* Limited-control criterion — met.

Phase C closeout:
`09_logs/2026-06-17_phaseC_closeout.md`.

---

## Phase D

**Phase D-1 — Voice — CLOSED 2026-06-18** (D-1.9
closeout). Pre-Phase-D blockers cleared 2026-06-17
(Mosquitto auth hardening + Gate G-5 re-execution).

### Goal

Voice interaction through the house.

### Phase D-1 outcome

Aurora v1 voice pipeline operational on both front
doors:

* **Home Assistant voice** — `https://ha.amarolab.es`
  → Assist pipeline `AURORA v1` (Wyoming chain
  Whisper / Piper / openWakeWord + HA Ollama
  integration on `qwen2.5:7b-instruct`).
* **Open WebUI voice** — `https://ai.amarolab.es`
  → browser mic into OpenAI-API-compatible STT/TTS
  HTTP shims (`aurora-whisper-http`,
  `aurora-piper-http`).

All six Phase D-1 gates landed with dated apply logs:

| Gate | Half | Apply log | Status |
|---|---|---|---|
| G-D1 | Wyoming | [`09_logs/2026-06-17_phaseD_whisper_installed.md`](../09_logs/2026-06-17_phaseD_whisper_installed.md) | Closed (D-1.2) |
| G-D1 | HTTP shim | [`09_logs/2026-06-18_phaseD_openwebui_audio_applied.md`](../09_logs/2026-06-18_phaseD_openwebui_audio_applied.md) | Closed (D-1.7) |
| G-D2 | Wyoming | [`09_logs/2026-06-17_phaseD_piper_installed.md`](../09_logs/2026-06-17_phaseD_piper_installed.md) | Closed (D-1.3) |
| G-D2 | HTTP shim | [`09_logs/2026-06-18_phaseD_openwebui_audio_applied.md`](../09_logs/2026-06-18_phaseD_openwebui_audio_applied.md) | Closed (D-1.7) |
| G-D3 | Container / probe | [`09_logs/2026-06-17_phaseD_wakeword_installed.md`](../09_logs/2026-06-17_phaseD_wakeword_installed.md) | Closed (D-1.4) |
| G-D3 | HA UI | [`09_logs/2026-06-17_phaseD_voice_pipeline.md`](../09_logs/2026-06-17_phaseD_voice_pipeline.md) | Closed (D-1.5) |
| G-D4 | Canary end-to-end | [`09_logs/2026-06-17_phaseD_gate_gd4_applied.md`](../09_logs/2026-06-17_phaseD_gate_gd4_applied.md) | **PASSED 2026-06-17** |
| G-D5 | Real-device voice (printer) | [`09_logs/2026-06-18_phaseD_gate_gd5_applied.md`](../09_logs/2026-06-18_phaseD_gate_gd5_applied.md) | **PASSED 2026-06-18** (Write→Restore scope; baseline restored) |
| G-D6 | Failure-mode rehearsal | [`09_logs/2026-06-18_phaseD_gate_gd6_applied.md`](../09_logs/2026-06-18_phaseD_gate_gd6_applied.md) | **PASSED 2026-06-18** (one acceptance partial on HA TTS-failure log granularity, functional behaviour PASS) |

### Phase D-1 sub-step ledger

| Step | Status |
|---|---|
| D-1.1 documentation skeleton | Closed |
| D-1.2 Whisper standup | **Closed 2026-06-17** |
| D-1.3 Piper standup | **Closed 2026-06-17** |
| D-1.4 openWakeWord standup | **Closed 2026-06-17** |
| D-1.5 AURORA v1 Assist pipeline + voice canary + voice-exposure lockdown | **Closed 2026-06-17** |
| HA reverse-proxy trust patch | Closed 2026-06-17 (supplement to D-1.5) |
| D-1.6 Real-device voice end-to-end / G-D5 | **Closed 2026-06-18** |
| D-1.7 Open WebUI Audio integration (+ closes G-D1 HTTP-shim half, G-D2 HTTP-shim half, C-D-07, C-D-09) | **Closed 2026-06-18** |
| D-1.8 Failure-mode rehearsal / G-D6 | **Closed 2026-06-18** |
| D-1.9 Phase D-1 closeout | **Closed 2026-06-18** |

Closeout document:
[`09_logs/2026-06-18_phaseD1_closeout.md`](../09_logs/2026-06-18_phaseD1_closeout.md).

### Success criteria

Voice interaction through the house — **met**.

* Canary Read / Write / Verify / Restore — G-D4.
* Real Zigbee plug Write / Restore (Sonoff S60ZBTPF)
  via voice — G-D5; baseline `off` restored.
* Failure-mode safety story (Whisper down /
  Piper down / Ollama unreachable) — G-D6.

### Post-D-1 follow-ups (NOT new phases)

Tracked in the closeout document and in
[`00_overview/CURRENT_STATE.md`](CURRENT_STATE.md):

* LLM 6 tok/s ceiling on UM790 CPU — deferred to
  RTX 5070 AI-node work (see
  [`04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md`](../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md)).
* STT fidelity — `base-int8` produces sub-canonical
  Spanish on short utterances; model-size bump
  candidate.
* HA voice-pipeline intent-matching variability
  (`HA-VOICE-001`).
* HA TTS-failure log granularity (G-D6 §7.2 partial).
* Streaming TTS in Open WebUI.
* System prompt size (3 342 chars / 822 tokens) →
  cold-cache trim candidate.
* `cloudflared-amarolab` standalone apply log.
* DNS / Cloudflare architecture doc amendments
  (separate-tunnel decision +
  `ai.amarolab.es` binding).
* R-D-13 — migrate Open WebUI STT HTTP shim away
  from the unmaintained `fedirz/faster-whisper-server`.
* R-01 — Cloudflare Tunnel token rotation (existing
  Guardian-Cloud tunnel).

---

## Phase E

Unified Knowledge — **NOT STARTED**.

Tasks:

* Add MyFreeTour
* Improve RAG
* Continuous indexing

Success criteria:

Single assistant with access to all project knowledge.

---

## Long-Term Vision

One assistant — **AURORA**.

Two front doors:

* Open WebUI (chat + voice) — `https://ai.amarolab.es`
* Home Assistant (voice) — `https://ha.amarolab.es`

Shared brain:

* Ollama (`qwen2.5:7b-instruct`)
* Qdrant
* AMAROLAB knowledge base

Everything local.

Everything documented.

Everything recoverable.

AURORA is delivered as part of the **AMAROLAB**
ecosystem. **Guardian Cloud** remains an independent
project hosted on AMAROLAB infrastructure.
