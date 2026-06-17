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

**In progress** (started 2026-06-17). Pre-Phase-D
blockers: **none open** — Mosquitto auth hardening
landed 2026-06-17 and Gate G-5 was re-executed
end-to-end through the hardened broker.

### Goal

Voice

Tasks and status:

* **Whisper** — **DONE** (D-1.2, 2026-06-17).
  `aurora-whisper` operational
  (`rhasspy/wyoming-whisper:3.2.0`, `base-int8`).
  Gate G-D1 Wyoming path passed (WER 0.000, RTF
  0.055 on UM790 CPU). HTTP-shim path of G-D1
  deferred to D-1.7. Apply log:
  `09_logs/2026-06-17_phaseD_whisper_installed.md`.
* **Piper** — open. D-1.3 is the next step.
* **openWakeWord** — open. D-1.4.
* **Home Assistant Assist pipeline (`AURORA v1`)**
  — open. D-1.5 (configuration) through D-1.8
  (failure-mode rehearsal).
* **Open WebUI Audio integration** — open. D-1.7
  (also closes the G-D1 HTTP-shim path deferred
  from D-1.2).

Success criteria:

Voice interaction through the house.

Phase D-1 closeout will land at **D-1.9** once
Gates G-D1 through G-D6 are all documented and
`switch.impresora_3d` is restored to its baseline
after G-D5.

---

## Phase E

Unified Knowledge

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

* Open WebUI (chat)
* Home Assistant (voice)

Shared brain:

* Ollama
* Qdrant
* AMAROLAB knowledge base

Everything local.

Everything documented.

Everything recoverable.

AURORA is delivered as part of the **AMAROLAB**
ecosystem. **Guardian Cloud** remains an independent
project hosted on AMAROLAB infrastructure.
