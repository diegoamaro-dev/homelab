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

Last updated: 2026-06-27 (Phase D-1 closed; **Phase RTX-1
CLOSED** — RTX-1.4 remote exposure + RTX-1.5 headless NSSM
service + RTX-1.6 endpoint swap (failover proxy, Torre
primary + UM790 fallback) all complete. The UM790 front
doors now consume Torre's GPU Ollama via the `ollama-proxy`).
**Phase E — Knowledge Platform Foundation — started 2026-06-27;
E-0 + E-1 closed (G-E0); E2-a fail-loud sync + E5-a drift
measurement done (E5-a: no retrieval drift, E2-b not required).**

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
  RTX-1 local validation done 2026-06-18; see
  **Phase RTX-1** below.
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

## Phase RTX-1

**Status:** **CLOSED — RTX-1.6 complete (2026-06-27).** The
UM790 front doors now consume Torre's GPU Ollama through the
`ollama-proxy` (Torre primary + UM790 CPU fallback).
RTX-1.5 (headless NSSM service, persists across logoff +
reboot-without-login) and RTX-1.4 (Tailscale-only, host-scoped
/32 allowlist) remain in force.

**Outcome:** Torre (Windows + RTX 5070, 12 GB VRAM) runs
`qwen2.5:7b-instruct` GPU-accelerated — **105.3 tok/s,
≈17.6×** the UM790 CPU baseline — reachable from the UM790
over Tailscale and surviving cold boot with no interactive
login. As of RTX-1.6, Open WebUI and Home Assistant route
inference through the `ollama-proxy` to Torre when it is up
(**101.3 tok/s** end-to-end; HA conversation 24.1 s CPU →
3.9 s Torre) and **automatically fall back** to the UM790
CPU Ollama when Torre is unreachable (validated live). No
service was *moved* to Torre; the UM790 stays the 24/7 node
and the always-on fallback.

### Sub-step ledger

| Step | Description | Status |
|---|---|---|
| RTX-1.0 | Read-only post-format workstation audit | Done |
| RTX-1.1 | Install Ollama; pre-stage `D:\ai\ollama\models` | Done |
| RTX-1.2 | GPU validation (pull, placement, VRAM, benchmark) | Done |
| RTX-1.3 | Storage remediation (model store C: → D:) | Done |
| RTX-1.4 | Secure remote exposure (OLLAMA_HOST + firewall, Tailscale-only) | **Complete (2026-06-19)** |
| RTX-1.5 | Headless persistence (NSSM Windows service) | **Complete (2026-06-27)** |
| RTX-1.6 | Security delta doc + UM790 endpoint swap (failover proxy) | **Complete (2026-06-27)** |

**RTX-1.5 detail:** Ollama migrated from the interactive
tray app to a headless NSSM service (`OllamaService`,
LocalSystem, Automatic). All ten gates G-1.5-1 through
G-1.5-10 PASS — persistence across logoff and
reboot-without-login, GPU 29/29 offload restored at cold
boot, single listener `0.0.0.0:11434`, teardown leaves no
orphan and recovers VRAM, host-scoped /32 firewall allowlist
preserved (allow `100.68.180.69/32`, block LAN), and the
UM790 production stack untouched (still `http://ollama:11434`
on its local CPU Ollama).

**RTX-1.6 detail (complete):** security delta doc
[`06_security/rtx_node_security.md`](../06_security/rtx_node_security.md)
created + approved → UM790 endpoint swap via the
`ollama-proxy` failover front end (Torre primary + UM790 CPU
fallback): Open WebUI → `ollama-proxy:11434`, Home Assistant
→ `127.0.0.1:11435`. All eleven gates G-1.6-1…G-1.6-11 PASS
(primary, fallback, chat, tools, HA, voice wiring, RAG, GPU
offload, performance, live fallback, production integrity).
Architecture amendment merged into
[`amarolab_architecture.md`](../01_architecture/amarolab_architecture.md);
`security_posture.md` updated with the RTX/proxy posture.

Full status, benchmark and sub-steps:
[`04_ai_system/amarolab-v1/phase-rtx/RTX1_validation_summary.md`](../04_ai_system/amarolab-v1/phase-rtx/RTX1_validation_summary.md).
Apply logs:
[`09_logs/2026-06-18_phaseRTX1_local_validation.md`](../09_logs/2026-06-18_phaseRTX1_local_validation.md) (local validation)
·
[`09_logs/2026-06-19_phaseRTX1_4_remote_exposure.md`](../09_logs/2026-06-19_phaseRTX1_4_remote_exposure.md) (RTX-1.4)
·
[`09_logs/2026-06-19_phaseRTX1_5_headless_service.md`](../09_logs/2026-06-19_phaseRTX1_5_headless_service.md) (RTX-1.5 service)
·
[`09_logs/2026-06-27_rtx1_5_continuation_handoff.md`](../09_logs/2026-06-27_rtx1_5_continuation_handoff.md) (RTX-1.5 closeout)
·
[`09_logs/2026-06-27_phaseRTX1_6_endpoint_swap_applied.md`](../09_logs/2026-06-27_phaseRTX1_6_endpoint_swap_applied.md) (RTX-1.6 endpoint swap).

---

## Phase E

**Knowledge Platform Foundation — IN PROGRESS (bounded).**

A bounded foundation phase — it has a defined start and end
and is **not** ongoing operations activity. Purpose:
**stabilise and operationalise the existing knowledge
platform** (the RAG ingest pipeline, the Qdrant index, and
the `rag_search` retrieval path) so future knowledge domains
can onboard onto a sound foundation. **Not feature
development; Phase E changes no retrieval behaviour.**

Entry gate **G-E0 — read-only operational audit — CLOSED
2026-06-27.** The audit's finding register is the sole
source of the E-1…E-6 backlog. Report:
[`../09_logs/2026-06-27_phaseE_E0_operational_audit_report.md`](../09_logs/2026-06-27_phaseE_E0_operational_audit_report.md).

Objectives (bounded charters; work populated only by E-0
findings):

* **E-0 — Operational audit (read-only) — CLOSED 2026-06-27
  (G-E0).**
* **E-1 — Documentation reconciliation — CLOSED 2026-06-27.**
* **E-2 — Platform hardening — in progress.** E2-a (fail-loud
  nightly indexing — F-01 sync exit-code remediation) **done
  2026-06-27**; E2-b (embedder/reranker version posture)
  **not required** — E5-a measured no retrieval drift
  (2026-06-27), so no pin/unify/migration is taken; E2-c
  (run-lock, F-08) pending.
* E-3 — Observability (index freshness, run health,
  audit-log liveness).
* E-4 — Maintenance (log rotation; Qdrant backup-consistency
  spike — "no change" is an acceptable outcome).
* **E-5 — Validation — in progress.** E5-a (version-skew drift
  measurement, F-02) **done 2026-06-27** — no measurable drift,
  via the permanent
  [`04_ai_system/validation/retrieval_validation_fixture.yaml`](../04_ai_system/validation/retrieval_validation_fixture.yaml);
  E5-b (Qdrant restore drill, F-05b) and E5-c (controlled
  audit-log check) pending.
* E-6 — Future onboarding framework (contract + template +
  procedure), proven against a disposable corpus.

Out of scope (explicit):

* **MyFreeTour** onboarding — a future consumer project, not
  Phase E work (it onboards once the platform foundation is
  in place).
* **"Improve RAG" / retrieval feature work** — no
  cross-collection routing, latency tuning, or recall
  changes in this phase.
* Embedder/reranker model change or version upgrade that
  alters outputs — a re-embed is a future migration,
  considered only if E-5 measures real retrieval drift.

Continuous indexing already exists: the nightly ingest sync
runs by cron at 02:30 (before the 03:00 restic backup).
Phase E **hardens and makes it observable** — it does not
build it.

Success criteria:

The knowledge platform is audited; every observed issue is
resolved or explicitly deferred; documentation matches
deployed reality; platform health is observable; **retrieval
behaviour is provably unchanged**; and a proven onboarding
framework exists for future knowledge domains.

---

## Future projects (post-Foundation)

These consume the knowledge platform once the Phase E
foundation is in place. They are **not** Phase E work.

* **MyFreeTour** — onboard a `myfreetour` knowledge corpus
  (currently a disabled placeholder, 0 points) via the E-6
  onboarding framework. Blocked on the source path
  (sub-project ROADMAP blocker B-08).

---

## Documentation Hygiene — Follow-up

Not a phase. Future repo-wide maintenance pass.

* **Review and optionally sanitize private LAN / Tailscale node IPs across AMAROLAB documentation.**
  Private (RFC 1918) and Tailscale (CGNAT) addresses are
  not credentials, but they are operational network
  detail already committed in several docs — e.g.
  [`CURRENT_STATE.md`](CURRENT_STATE.md),
  [`../04_ai_system/amarolab-v1/phase-rtx/RTX1_validation_summary.md`](../04_ai_system/amarolab-v1/phase-rtx/RTX1_validation_summary.md),
  [`../01_architecture/amarolab_architecture_rtx_amendment_DRAFT.md`](../01_architecture/amarolab_architecture_rtx_amendment_DRAFT.md).
  Decide repo-wide: accept as non-secret, or sanitize
  consistently (note: values already exist in git
  history). Deferred from the RTX-1 triad update
  (2026-06-18) by explicit decision — secrets review
  passed; sanitizing one file only would be inconsistent.

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
