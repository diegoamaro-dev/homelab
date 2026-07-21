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

Last updated: 2026-07-21 (**Phase ER-1 — Deterministic Entity Resolution — COMPLETE at ER-1.5
(closeout 2026-07-21, `09_logs/2026-07-21_ER1_5_closeout.md`); design FROZEN 2026-07-16,
Revision 4**; ER-1.0 committed + pushed (`c147e632` → `38eb8262`); the
Revision 2 amendment (D-ER-11 + D-ER-12) committed + pushed (`3ebf59d1`); ER-1.1 (aliases
contract) committed + pushed (`f983a04f`); **ER-1.2 (loader) committed + pushed (`b0fded73`) —
G-ER-5 CLOSED 2026-07-17 on the first unattended 04:15 cycle**; **ER-1.3 (projection emitter +
D-ER-13 / Revision 3) committed + pushed (`ed7a149c`) — G-ER-6 producer half CLOSED**;
**ER-1.4a (v0.1.0 baseline + `ha_get_state` v0.2.0 — the first cutover) implemented +
validated 2026-07-17, committed + pushed (`3ad8779f`) — G-ER-7 read half PASS, G-ER-6 consumer
half PASS on the read side; the read path resolves natural language (`ha_call_service`
then still v0.1.0)**; **Rev 4 (D-ER-14 — audit field `registry_target`; `ha_get_state` →
v0.2.1) ratified + applied 2026-07-17, with the ER-1.4b C1 measurement protocol
pre-registered**; **ER-1.4b (`ha_call_service` v0.2.0 — resolution + ER-1-C1, Rule B / 500 ms)
implemented + validated 2026-07-20 — the write cutover, committed + pushed `5b502c96`:
G-ER-2/3a/3b/4 + G-ER-7 write half + G-ER-6 consumer half (write side) all PASS; the write path
now verifies before it claims success (`09_logs/2026-07-20_ER1_4b_ha_call_service_applied.md`)**;
spec
`04_ai_system/entity_resolution_layer.md`. Phase
D-1 closed; **Phase RTX-1
CLOSED** — RTX-1.4 remote exposure + RTX-1.5 headless NSSM
service + RTX-1.6 endpoint swap (failover proxy, Torre
primary + UM790 fallback) all complete. The UM790 front
doors now consume Torre's GPU Ollama via the `ollama-proxy`).
**Phase E — Knowledge Platform Foundation — CLOSED 2026-06-28.**
All steps done: E-0..E-6; 13 findings resolved or accepted.
**Phase F — Operational Intelligence — IN PROGRESS. F-0, F-1, F-2 and F-3
(Situational Awareness) COMPLETE — F-3 closed 2026-06-29 (F3.3): F-3a chat
Filter (G-F3-1…7) + F-3b HA-voice awareness (G-F3-8) both validated. F-4: F4.1
(substrate) + F4.2 (generator) DONE + committed 2026-06-30; F4.3 implementation +
reconciliation complete 2026-06-30 — G-F4-01/02/03/04/09 PASS, G-F4-08
config-verified (empirical restic pending next backup), G-F4-05/06/07 intentionally
pending real operational evidence; F-4 not fully closed. F-5 **CLOSED 2026-07-16 (at WM-6)** — F5.1/F5.2 done; **F5.3 (2026-07-01): G-F5-03 PASS, G-F5-04 FAIL** → R-F5-A logged; **remedied by the World Model, closed at WM-6 — G-F5-04 PASS on real evidence (chat + voice); R-F5-A closed** (`09_logs/2026-07-16_WM6_G-F5-04_closeout.md`); F-6 unblocked. **World Model architecture FROZEN 2026-07-01 (AD-21) as the R-F5-A remedy + Aurora's semantic baseline; Phase WM (WM-1→WM-7) implementation underway — WM-1 `_schema/` foundation committed 2026-07-01 (`6e97c3fb`); WM-2 committed 2026-07-01 (`4c3e2a5d`, pushed); WM-3 loader implemented 2026-07-02 — real-data parity PASS, committed + pushed (`8d653fea`, git gate closed); WM-4 evaluator cutover implemented + validated 2026-07-13 — `HOME_RULES` retired, AD-20/INV-18 preserved, STOPPED at the git gate (G-WM4-6 closed 2026-07-14); WM-5 done 2026-07-14; **WM-6 done 2026-07-16 — G-F5-04 CLOSED / R-F5-A · F-5 CLOSED** (`09_logs/2026-07-16_WM6_G-F5-04_closeout.md`).**

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
* **E-2 — Platform hardening — done 2026-06-27.** E2-a (fail-loud
  nightly indexing — F-01 sync exit-code remediation) **done
  2026-06-27**; E2-b (embedder/reranker version posture)
  **not required** — E5-a measured no retrieval drift
  (2026-06-27), so no pin/unify/migration is taken; E2-c
  (run-lock, F-08) **done 2026-06-27**.
* **E-3 — Observability — done 2026-06-27.** Unified `health.json`
  (gitignored runtime state): `ingest-nightly` wrapper (02:30, E3-a/E3-b)
  + `check-audit-liveness` (03:30, E3-c). `overall_status=ok` (resolved
  2026-06-27 after E5-c closed F-10). Apply log:
  [`../09_logs/2026-06-27_phaseE_E3_observability_applied.md`](../09_logs/2026-06-27_phaseE_E3_observability_applied.md).
* **E-4 — Maintenance — done 2026-06-27.** E4-a (log rotation, F-04)
  **done 2026-06-27** — `/etc/logrotate.d/homelab-ingest`; E4-b (Qdrant
  backup-consistency spike, F-05a) **done 2026-06-27 — no change required**:
  E5-b 16/16 PASS proves hot backup is recoverable; cron order (ingest
  02:30, restic 03:00) provides quiescent window; residual risk documented
  and accepted. Decision record:
  [`../09_logs/2026-06-27_phaseE_E4b_backup_consistency_decision.md`](../09_logs/2026-06-27_phaseE_E4b_backup_consistency_decision.md).
* **E-5 — Validation — done 2026-06-27.** E5-a (version-skew drift
  measurement, F-02) **done 2026-06-27** — no measurable drift,
  via the permanent
  [`04_ai_system/validation/retrieval_validation_fixture.yaml`](../04_ai_system/validation/retrieval_validation_fixture.yaml);
  **E5-b (Qdrant restore drill, F-05b) done 2026-06-27** — PASS:
  snapshot `228e4183` restored into isolated container, all 5
  collections green (4049/872/419/280/0), fixture parity 16/16,
  prod untouched. Apply log:
  [`../09_logs/2026-06-27_phaseE_E5b_restore_drill_applied.md`](../09_logs/2026-06-27_phaseE_E5b_restore_drill_applied.md);
  **E5-c (controlled audit-log check, F-10) done 2026-06-27** — no defect:
  root cause was absence of web UI tool calls during observation period;
  audit log scope documented (web UI only). Apply log:
  [`../09_logs/2026-06-27_phaseE_E5c_audit_log_check.md`](../09_logs/2026-06-27_phaseE_E5c_audit_log_check.md).
* **E-6 — Onboarding framework — done 2026-06-28.** Framework document at
  `04_ai_system/onboarding_framework.md` covering 12 sections (naming rules,
  collection creation, indexing, tool extension, validation, rollback, security).
  Proven end-to-end against disposable corpus `e6_test` (fictional Project Helios,
  16 points); success criterion met — onboarded, validated, and fully removed with
  no production artifact remaining. Closes F-07. Apply log:
  [`../09_logs/2026-06-28_phaseE_E6_onboarding_framework_applied.md`](../09_logs/2026-06-28_phaseE_E6_onboarding_framework_applied.md).

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

## Phase F — Operational Intelligence

**Architecture approved 2026-06-28.** See
[`04_ai_system/phase_f_architecture.md`](../04_ai_system/phase_f_architecture.md)
for the complete design. Mission: shift Aurora from reactive to aware.

Sub-phases:

* **F-0 — Behavioral Audit — COMPLETE 2026-06-28.** Read-only baseline.
  8 AF findings: 6 confirmed, 1 superseded (AF-05 → `input_text` +
  Jinja2), 1 disproved (AF-06 — system prompt stale, blocks 4/5 tools).
  Baseline 4/10 pass. Audit report:
  [`09_logs/2026-06-28_phaseF_F0_audit_report.md`](../09_logs/2026-06-28_phaseF_F0_audit_report.md).
* **F-1 — System Prompt Redesign — COMPLETE 2026-06-28.** F-1 prompt
  installed (3 389 chars / ~485 tokens incl. the F2-9 `system_status`
  addition); domain-based routing; all tools described; stale phase
  language removed; citation-format bug fixed; knowledge-layer corpus
  split (`homelab_docs` / `knowledge_history`). Platform finding G-F1-01
  (UI tool-forwarding) raised here, resolved in F-2. Log:
  [`09_logs/2026-06-28_phaseF_F1_system_prompt_installed.md`](../09_logs/2026-06-28_phaseF_F1_system_prompt_installed.md).
* **F-2 — Signal Layer + Context Generation — COMPLETE 2026-06-29
  (F2-9).** `bin/backup-probe` → `backup_status.json` (03:30);
  `bin/container-probe` → `container_status.json` (04:00);
  `bin/aurora-context` → `ai-stack/aurora/aurora-context.{json,md,voice}`
  (04:15); scheduled by `/etc/cron.d/aurora-signals`; `ai-stack/aurora`
  bind-mounted read-only into `openwebui` at `/opt/aurora`. The
  `system_status` tool (v0.2.0) is wired to `qwen2.5` and reads that
  context + a live Torre probe. First unattended nightly cycle validated;
  G-F1-01 passed across all layers incl. the browser UI;
  `overall_status = ok`. Closeout:
  [`09_logs/2026-06-29_phaseF_F2_9_closeout.md`](../09_logs/2026-06-29_phaseF_F2_9_closeout.md).
* **F-3 — Situational Awareness — COMPLETE 2026-06-29 (F3.3).** Split into
  F-3a (chat) + F-3b (voice) per AD-08.
  * **F-3a — Open WebUI Awareness Filter (F3.1):** committed Filter
    `ai-stack/openwebui-tools/filters/aurora_context.py`, installed
    active+global; injects `aurora-context.md` on message 1. G-F3-1…G-F3-7
    pass (G-F3-1 closed after an operator-approved `# Context` precedence
    directive + `openwebui` reload). Log:
    [`09_logs/2026-06-29_phaseF_F3_1_applied.md`](../09_logs/2026-06-29_phaseF_F3_1_applied.md).
  * **F-3b — HA Voice Awareness Refresh (F3.2):** `input_text.aurora_voice_context`
    + Jinja2 in the Ollama voice prompt + 04:20 `bin/push-voice-context`
    (`input_text/set_value`). G-F3-8 pass. Log:
    [`09_logs/2026-06-29_phaseF_F3_2_applied.md`](../09_logs/2026-06-29_phaseF_F3_2_applied.md).
  * Closeout:
    [`09_logs/2026-06-29_phaseF_F3_closeout.md`](../09_logs/2026-06-29_phaseF_F3_closeout.md).
* **F-4 — Operational Digest + Memory Corpus — F4.1+F4.2 DONE + committed
  2026-06-30; F4.3 implementation + reconciliation complete 2026-06-30.** `bin/generate-digest`
  writes a dated digest to `09_ops/runtime/` at 04:25, indexed into the dedicated
  `ops_digests` collection (384/Cosine — AD-14, **not** `homelab_docs`) on the next
  02:30 sync. Unattended 04:25 run + real retrieval (2026-06-29 digest top-1 0.87)
  verified; `generated_at` fidelity fix applied (AD-15). G-F4-01/02/03/04/09 PASS; G-F4-08
  config verified (empirical restic pending next backup); G-F4-05/06/07 **intentionally
  pending real operational evidence** (no synthetic digests / fabricated degraded nights —
  operator decision). F-4 not fully closed. Closeout:
  [`09_logs/2026-06-30_phaseF_F4_3_closeout.md`](../09_logs/2026-06-30_phaseF_F4_3_closeout.md).
* **F-5 — Home Intelligence** — **CLOSED 2026-07-16 (at WM-6; G-F5-04 PASS on real evidence, chat + voice; R-F5-A closed; closeout `09_logs/2026-07-16_WM6_G-F5-04_closeout.md`).** `home_model.md` (F5.1) + G-F5-07
  Layer A + F5.2 Layer B done 2026-06-30. **F5.3 executed 2026-07-01: G-F5-03
  PASS, G-F5-04 FAIL (real validation)** — the F-3a Filter injects the Degraded
  Home State correctly, but the model routes status questions to tools
  (`system_status`, home-blind) instead of the injected block. Logged as
  **R-F5-A** (awareness-consumption gap), **deferred to Phase WM (its remedy) — closed at WM-6, 2026-07-16**;
  no fix/redesign in F-5 (the World Model is the structural fix). F5.3 apply log:
  [`09_logs/2026-07-01_phaseF_F5_3_applied.md`](../09_logs/2026-07-01_phaseF_F5_3_applied.md).
* **F-6 — Voice Quality** — Whisper upgrade; STT shim migration; latency
  baseline. Parallel track; no dependency on F-2..F-5.

---

## Phase WM — World Model (architectural baseline)

**Architecture FROZEN 2026-07-01 (AD-21).** Full specification:
[`../04_ai_system/world_model_architecture.md`](../04_ai_system/world_model_architecture.md)
(Revision 2, frozen); freeze log
[`../09_logs/2026-07-01_world_model_architecture_freeze.md`](../09_logs/2026-07-01_world_model_architecture_freeze.md).
The World Model is Aurora's **single semantic representation** of its operational world; it is
the **structural remedy for R-F5-A** (the awareness-consumption gap) and the substrate for
future proactive intelligence. **WM-1 (`_schema/` foundation) committed 2026-07-01** (`6e97c3fb`;
apply log `09_logs/2026-07-01_WM1_schema_foundation_applied.md`); **WM-2** entities + `_schema/collectors.md` **committed 2026-07-01** (`4c3e2a5d`, pushed; apply log
`09_logs/2026-07-01_WM2_home_entities_applied.md`); **WM-3** loader/compiler **implemented 2026-07-02**
— real-data parity with `HOME_RULES` **PASS** (engine-equivalence 32/32 + live `/api/states` match;
apply log `09_logs/2026-07-02_WM3_loader_applied.md`), **committed + pushed (`8d653fea`) — git
gate closed**; **WM-4** evaluator cutover **implemented + validated 2026-07-13** — the dedicated
`world_model/_evaluator/` engine consumes the compiled model (loader compiles / evaluator
evaluates — architectural separation), `bin/aurora-context` renders home awareness from it
(INV-19), **`HOME_RULES` + the WM-3 parity harness retired** (32 snapshots migrated to the
`_evaluator/tests/` regression suite), `home_model.md` → redirect, `aurora-context.json`
schema preserved (AD-20/INV-18), `overall_status` platform-only until WM-5 (apply log
`09_logs/2026-07-13_WM4_evaluator_cutover_applied.md`) — **STOPPED at the git gate**;
G-WM4-6 (first unattended nightly cycle) closed 2026-07-14; WM-5 (consumer convergence) done 2026-07-14; **WM-6 (close G-F5-04) done 2026-07-16 — G-F5-04 CLOSED / R-F5-A · F-5 CLOSED** (`09_logs/2026-07-16_WM6_G-F5-04_closeout.md`).
Each phase: real-data validation, documentation, **STOP at the git gate**. Hashes are the
post-sanitization canonical hashes (history rewritten + republished 2026-07-10; see
`09_logs/2026-07-10_repo_history_sanitization_reconciliation.md`).

| Phase | Objective | Gate |
|---|---|---|
| WM-0 | Freeze (this baseline; AD-21; ROADMAP slot; triad; freeze log) | **docs committed + pushed (`b43e8aad`); freeze tag still pending** |
| WM-1 | `_schema/` foundation (entity schema, tokens, windows, archetypes, validation) | **committed 2026-07-01 (`6e97c3fb`)** |
| WM-2 | Migrate `home_model.md` → literate `home/`+`environment/` entities + `collectors.md` (docs only, 1:1) | **semantic equivalence — docs done 2026-07-01 (G-WM2-1…10 pass); committed + pushed (`4c3e2a5d`)** |
| WM-3 | Loader/compiler (`_loader/`); run parallel to `HOME_RULES` | **real-data parity — PASS 2026-07-02; committed + pushed (`8d653fea`) — git gate closed** |
| WM-4 | Evaluation engine consumes the model; retire `HOME_RULES` | **committed + pushed (`476e0ae8`); G-WM4-1…6 PASS — G-WM4-6 closed 2026-07-14 (first unattended cycle); WM-4 complete** |
| WM-5 | Consumer convergence (Filter, home-aware `system_status`, voice line) | **implemented + validated 2026-07-14 — G-WM5-1…5 PASS on real data (§1.5 low-not-escalated proven; `system_status` webui.db install operator-gated); at the git gate** |
| WM-6 | **Reopen & close G-F5-04** (real induced anomaly, chat + voice) | **DONE 2026-07-16 — G-F5-04 CLOSED, PASS (chat @ ai.amarolab.es + voice @ ha.amarolab.es/AURORA v1); R-F5-A / F-5 CLOSED** (`09_logs/2026-07-16_WM6_G-F5-04_closeout.md`) |
| WM-7+ | Extend regions (infrastructure, self, projects); foundation for proactive intelligence | per-region validation |

**R-F5-A and F-5 completion were carried under Phase WM** (closed at WM-6, 2026-07-16). The earlier
"deferred to a future gated phase" for R-F5-A resolved to **Phase WM** and is now **closed**.

---

## Phase ER-1 — Deterministic Entity Resolution

**Design FROZEN 2026-07-16 (operator-ratified) — now Revision 4.** Full specification:
[`../04_ai_system/entity_resolution_layer.md`](../04_ai_system/entity_resolution_layer.md);
freeze log [`../09_logs/2026-07-16_ER1_freeze.md`](../09_logs/2026-07-16_ER1_freeze.md);
**Rev 2 amendment log** [`../09_logs/2026-07-16_ER1_freeze_rev2.md`](../09_logs/2026-07-16_ER1_freeze_rev2.md);
**Rev 4 amendment log** [`../09_logs/2026-07-17_ER1_freeze_rev4.md`](../09_logs/2026-07-17_ER1_freeze_rev4.md);
defect record [`../09_logs/2026-07-14_ER1_entity_resolution_finding.md`](../09_logs/2026-07-14_ER1_entity_resolution_finding.md).
A frozen design is amended only by a **gated, operator-ratified decision** — never by silent
drift: **Rev 1** = the initial freeze (ER-1.0); **Rev 2** = **D-ER-11** + **D-ER-12**, ratified
2026-07-16 when authoring the ER-1.1 alias sets surfaced two gaps (spec §3.5); **Rev 3** =
**D-ER-13** + the **G-ER-6 split** + content-derived projection freshness, ratified 2026-07-17 at
ER-1.3 (spec §3.6, §6, §9); **Rev 4** = **D-ER-14** (the step-4 audit field is
`registry_target`, never `modelled` — ratifies F-ER14-1), ratified + applied 2026-07-17 before
ER-1.4b (spec §3.7; `09_logs/2026-07-17_ER1_freeze_rev4.md`).

**Mission:** close the gap between natural language and real Home Assistant `entity_id`s, and
make every write **honest**. ER-1 fixes two independent defects: natural-language requests do
not resolve to the real id (the model invents plausible ids), and a write to a non-existent
entity in a **live** HA domain returns 200 + an empty changed-states list, which
`ha_call_service` v0.1.0 reports as `result_code:"ok"` — **13 unverified writes across 7
non-existent ids were reported as successful** (real audit evidence; all 7 re-probed
2026-07-16 → HTTP 404). The read path is **not** defective (`ha_get_state` already answers
`not_found`). **Fixed at ER-1.4b (2026-07-20): `ha_call_service` v0.2.0 + ER-1-C1 now return
`applied_unverified` for these — proven by G-ER-3b.**

ER-1 **amends no frozen decision** — AD-21 §7 already anticipates the entity registry; ER-1
implements that intent. **No architecture amendment.** Independent of Phase WM (WM validated
awareness convergence; ER-1 covers actuation, which WM never validated). **Not WM-5.5** — no
work is retroactively inserted into a published phase.

Key ratified decisions (register: spec §3):

* **D-ER-9 — no write-surface restriction.** A syntactically valid `entity_id` follows the
  current path **exactly as today**; **D-12 remains the sole authorization authority**; the
  World Model registry is a name-resolution convenience, **never a write allowlist**. Any
  stronger restriction is a **future architectural decision**, out of ER-1 scope.
* **ER-1-C1 — mandatory write verification (after-only).** A tool **must never claim success
  unless the resulting HA state has actually been verified**. ER-1 does **not** change *when*
  a POST is issued — only what the tool claims afterwards.
* **D-ER-10 — closed expected-state map** (`turn_on→on`, `turn_off→off`, `open_cover→open`,
  `close_cover→closed`); every other service returns `applied_unverified`.
* **D-ER-7 — `ARTIFACT_VERSION` stays 1** (additive `resolution` key) — a bump would silently
  degrade home awareness rather than fail loud, and quietly undo the WM-6 / G-F5-04 closure.
* **D-ER-11 (Rev 2) — aliases mirror the `binding` shape.** Single-signal → flat alias list;
  multi-signal → per-signal alias map; **no implicit primary signal** (a multi-signal binding
  has no implicit `state`, so an entity-level alias would have no single target).
* **D-ER-12 (Rev 2) — alias vs entity identifier.** An alias **may** equal **its own** entity's
  identifier; it **must never** collide with **another** entity's identifier.
* **D-ER-13 (Rev 3) — an aliased signal must bind `ha_entity`** (check 12a; ratifies finding
  F-ER12-1). A signal bound to `container` / `corpus` / `probe` / `signal` has no HA id to
  resolve to, so its alias would be **dead**. Unreachable on the real tree — ratified so the
  rule states the constraint the registry **depends on**, not the one that happens to hold.
  Naming/validation only; **INV-17 untouched**.
* **D-ER-14 (Rev 4) — the step-4 audit observability field is `registry_target`** (ratifies
  finding F-ER14-1). The field answers *"is this id a target in the resolution registry?"*
  (D-ER-6 scope), not *"does the World Model model this entity?"* — `sun.sun` is modelled yet
  unaliased, so the old name `modelled` mis-reported it. Renamed while the field had **zero**
  occurrences in the real audit log, before ER-1.4b stamps it on writes.
  Naming/observability only; **INV-17 / D-ER-9 untouched**.
* **Projection freshness is content-derived (Rev 3).** The host-side
  `emit-entity-projection --check` is the canonical mechanism; `resolution_sha256` is the sole
  authority; **`docs_commit` is traceability only and is never a freshness indicator**. Now a
  permanent project rule — [`PROJECT_RULES.md`](PROJECT_RULES.md) → *Content Provenance over
  Repository Chronology*.

Each sub-phase: real-data validation, documentation, **STOP at the git gate**.

| Phase | Objective | Gate |
|---|---|---|
| ER-1.0 | Freeze (spec; decision register D-ER-1…10 + C1; ROADMAP slot; triad; freeze log). The 2026-07-14 defect record is committed separately, immediately before — history reads *defect discovered → design frozen* | **frozen 2026-07-16 — committed + pushed**: defect record `c147e632` → architecture freeze `38eb8262` |
| ER-1 Rev 2 | Freeze amendment — ratify **D-ER-11** (alias shape) + **D-ER-12** (alias vs entity identifier); correct the record on check-12 semantics | **ratified 2026-07-16 — committed + pushed** (`3ebf59d1`; `09_logs/2026-07-16_ER1_freeze_rev2.md`) |
| ER-1.1 | Schema `aliases` (additive, `schema_version` unchanged) + entity aliases (docs only) | **applied + validated 2026-07-16 — G-ER-1 PASS within ER-1.1 scope** (33 unique normalized aliases → 8 `ha_entity` targets across the 6 bound entities; `schema_version` unchanged; aliases proven **inert** — a fresh compile differs from the on-disk artifact only in `provenance.sha256`); **committed + pushed** (`f983a04f`; `09_logs/2026-07-16_ER1_1_aliases_applied.md`). Fail-loud enforcement lands at ER-1.2 |
| ER-1.2 | Loader: normalizer, validation, `resolution` registry + tests | **committed + pushed** (`b0fded73`; `09_logs/2026-07-16_ER1_2_loader_applied.md`). **G-ER-1 CLOSED** (check 12 fail-loud in the real loader; every fault class rejected by test) · **G-ER-2 loader half PASS** (D-ER-8 table-driven + byte-stable registry) · **G-ER-5 CLOSED 2026-07-17** — implementation validation **plus** operational non-regression on the first unattended 04:15 cycle after the artifact regeneration: awareness byte-equivalent to baseline, Home State `Degraded` (never `Unavailable`), zero `ArtifactError` (`09_logs/2026-07-17_ER1_2_G-ER-5_operational_closeout.md`). 42 loader + 36 evaluator tests green; `artifact_version` still 1; `LOADER_VERSION` → 0.2.0 |
| ER-1.3 | Projection emitter + `aurora-entities.json` runtime artifact; **D-ER-13** (check 12a — Rev 3) | **implemented + validated 2026-07-17** (`09_logs/2026-07-17_ER1_3_projection_applied.md`). **G-ER-6 producer half CLOSED** — artifact missing / corrupt / no-`resolution` ⇒ fail loud, nothing written, last-good retained byte-identical; stale / absent ⇒ honest `--check` (rc 3); consumer half open (ER-1.4). **D-ER-13 ratified — no behaviour change** (unreachable on the real tree; `resolution` hash unmoved). **G-ER-1 untouched** — its 2026-07-16 closure stands; gate history is not rewritten. 43 loader + 36 evaluator green; **`LOADER_VERSION` → 0.2.1** (patch — validation contract only; the live artifact keeps `loader_version` 0.2.0, the version that generated it — ER-1.3 does not regenerate); `artifact_version` still 1; artifact **not** touched, awareness unaffected by construction |
| ER-1.4a | Capture the v0.1.0 baseline, then `ha_get_state` v0.2.0 | **implemented + validated 2026-07-17** (`09_logs/2026-07-17_ER1_4a_ha_get_state_applied.md`). **G-ER-7 read half PASS** — baseline captured from the **installed** v0.1.0 row before the cutover (§6.2.1), and the repo source proven byte-identical to it, so the rollback target is exact. Every difference falls in an enumerated intentional-change class: a canonical `entity_id` is **byte-identical** (established by a paired A/B run with entity volatility controlled, `sun.sun` included); non-id-shaped → `unknown_entity` + ≤8 candidates, **zero HTTP calls**; aliases resolve (`toldo`, `impresora 3d`, `Conexión a Internet`). D-ER-8 normalization **proven byte-identical** to `_loader/resolution.py` over 46 real + adversarial cases; all 33 authored aliases resolve. **G-ER-6 consumer half PASS on the read side** — missing/corrupt/version-mismatch/normalization-mismatch/bad-target ⇒ direct ids work **exactly as today**, alias → honest `resolver_unavailable`; **stale ⇒ used** (a tool cannot compute freshness — §9), degrading alias resolution only. Real audit log and real projection both untouched. **New:** `lib/entity_resolver.py`; `bin/install_tool` multi-marker; `lib/audit_helper.py` additive `extra`. **F-ER14-1 recorded** (audit field `modelled` overstates what it verifies) — **ratified as D-ER-14 at Rev 4, 2026-07-17: renamed `registry_target`**. Committed + pushed (`3ad8779f`) |
| ER-1 Rev 4 | Freeze amendment — ratify **D-ER-14** (step-4 audit field → `registry_target`; resolves F-ER14-1); `ha_get_state` → **v0.2.1** reinstalled (returns proven byte-identical, 18-case A/B); **pre-register the ER-1.4b C1 measurement protocol** (predefined decision rules — never outcome-driven) | **ratified + applied 2026-07-17** (`09_logs/2026-07-17_ER1_freeze_rev4.md`; protocol `09_logs/2026-07-17_ER1_4b_c1_measurement_protocol.md`; tool hashes stamped at ER-1.5 closeout — `09_logs/2026-07-21_ER1_5_closeout.md` §3) |
| ER-1.4b | `ha_call_service` v0.2.0 (resolution + ER-1-C1); Step 2 executed the pre-registered C1 measurement protocol first (→ **Rule B / 500 ms**) | **applied + validated 2026-07-20 — G-ER-2/3a/3b/4 + G-ER-7 write half + G-ER-6 consumer half (write side) all PASS; the write path now verifies before claiming success** (`09_logs/2026-07-20_ER1_4b_ha_call_service_applied.md`) — **committed + pushed `5b502c96`** |
| ER-1.5 | Reconciliation + closeout | **COMPLETE 2026-07-21 — Phase ER-1 CLOSED** (`09_logs/2026-07-21_ER1_5_closeout.md`): reconciled against the frozen spec (all §10 deliverables byte-clean at HEAD; invariants hold); G-ER-1…7 ledger closed on real evidence; deferred tool hashes stamped; rollback + observability reviewed; triad reconciled (ER-1 transient markers cleared). Documentation-only; no code/tag |

Gates **G-ER-1…7** (spec §6). **G-ER-3b:** *historical unverified writes must never again be
reported as successful* — every historical case must produce an honest `verified` or
`applied_unverified` result. **G-ER-6:** projection-failure rehearsal (G-D6 discipline) — **split at Rev 3** into a
**producer half** (ER-1.3: the emitter fails loud and retains last-good; closed 2026-07-17) and
a **consumer half** (ER-1.4: direct `entity_id` keeps working, alias resolution returns an honest
`resolver_unavailable`), because the gate as written asserts behaviour **at the tool boundary**
and no consumer of the projection exists until ER-1.4.
**G-ER-7:** backward compatibility — every operation that already works today with real HA
entity_ids behaves equivalently before and after ER-1.

Out of scope (explicit): the frozen F-1 `params.system`; the HA voice path (HA Assist has its
own alias mechanism; the printer is intentionally not voice-exposed); D-12 allowlist changes;
the awareness pipeline (INV-18 / AD-20 / INV-19 all hold).

---

## Future projects (post-Foundation)

These consume the knowledge platform once the Phase E
foundation is in place. They are **not** Phase E work.

* **MyFreeTour** — onboard a `myfreetour` knowledge corpus
  (currently a disabled placeholder, 0 points) via the E-6
  onboarding framework. Blocked on the source path
  (sub-project ROADMAP blocker B-08).

---

## Architectural Backlog — Health Aggregator (future, not Phase E)

Not a phase. Deferred evolution for when additional health producers appear.

The current E-3 design (two writers, one shared `health.json`) is appropriate
for the current scale. When the platform grows to include additional health
producers (Docker, Ollama, Qdrant, Home Assistant, GPU node, backups, etc.),
the recommended evolution is:

* **Multiple health producers** — each subsystem writes its own signal
  independently (e.g. `ingest-nightly`, a future `qdrant-health`, a future
  `ollama-health`).
* **One health builder/aggregator** — a single script assembles all producer
  signals into one authoritative `health.json` and computes `overall_status`.
* **One authoritative `health.json`** — same schema, same HA/Aurora integration
  target; only the build process changes.

This evolution requires no schema change and no HA integration rework.
Trigger: when a third health producer would otherwise require a third writer
touching the shared file.

---

## Documentation Hygiene — Follow-up

Not a phase. Future repo-wide maintenance pass.

* **WM-era stale transient status — technical debt, found 2026-07-17.** Discovered by the
  first sweep under `PROJECT_RULES.md` → *Transient Operational Status*, and **deliberately
  left unreconciled**: it predates ER-1.2 and is outside that change's approved scope
  (operator decision — a narrow commit must not quietly widen). The governance rule
  guarantees a future reconciliation will clear it. Known sites:
  * [`CURRENT_STATE.md`](CURRENT_STATE.md) §*Current phase* — WM-4 described as
    **"STOPPED at the git gate (not committed)"**; reality: **committed + pushed
    `476e0ae8`** (the same paragraph already says so elsewhere — internally contradictory).
    It also says G-WM4-6 "closes on 2026-07-14 real evidence"; it closed.
  * [`ROADMAP.md`](ROADMAP.md) → Phase WM narrative — same WM-4 "STOPPED at the git gate".
  * [`AMAROLAB_HANDOFF.md`](AMAROLAB_HANDOFF.md) — WM-5 described as **"STOPPED at the git
    gate"**; reality: **committed + pushed `b2b04670`**.
  * **Do not "fix" these two classes**, which the same sweep surfaces:
    **(a)** `"Each phase/sub-phase: … STOP at the git gate"` — a *process rule* describing
    the workflow, correct as written; **(b)** `"not committed in plain text"` in the Secrets
    section — the *secrets policy*, not a git status.
  * Historical `09_logs/` entries are **exempt** and must stay so: their transient status is
    evidence of what was true then, corrected only by later documentation.

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
