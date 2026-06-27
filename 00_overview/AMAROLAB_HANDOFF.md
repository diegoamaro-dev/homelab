# AMAROLAB_HANDOFF
## Mandatory Reading Order

1. AMAROLAB_HANDOFF.md
2. CURRENT_STATE.md
3. ROADMAP.md
4. INITIAL_SYSTEM_STATUS.md (optional historical context)
Last updated: 2026-06-27

## Purpose

This document allows any future AI session to rebuild project context quickly and continue work without relying on conversation history.
This document is intentionally concise.

Detailed operational state lives in CURRENT_STATE.md.
---

## Project

**AMAROLAB** — Personal Innovation Lab and Digital
Infrastructure Ecosystem.

AMAROLAB provides infrastructure, automation,
knowledge systems, AI services and documentation. It
hosts **AURORA** (the personal AI assistant for the
AMAROLAB ecosystem) and independent projects such as
**Guardian Cloud**.

Focus areas:

* Local AI
* Home automation
* Learning infrastructure
* Documentation
* Portfolio development
* Hosting of independent projects (e.g., Guardian Cloud)
* AURORA — the AMAROLAB Personal AI Assistant

---

## Naming

**AMAROLAB**

Personal Innovation Lab and Digital Infrastructure
Ecosystem. Provides infrastructure, automation,
knowledge systems, AI services and documentation.

**AURORA**

Personal AI Assistant for the AMAROLAB ecosystem.

**Guardian Cloud**

Independent project currently hosted on AMAROLAB
infrastructure.

---

## Hardware

### Main Server

* Minisforum UM790 Pro
* AMD Ryzen 9 7940HS
* 32 GB DDR5
* 512 GB SSD
* Linux

### AI Compute Node (Torre) — Phase RTX-1 closed 2026-06-27

* Windows tower + NVIDIA RTX 5070 (12 GB VRAM)
* On-demand GPU compute (not 24/7)
* Runs Ollama as a **headless NSSM service** (LocalSystem,
  Automatic) — Tailscale-only (host-scoped /32 allowlist),
  persists across logoff + reboot-without-login (RTX-1.5).
* **Consumed by the UM790 since RTX-1.6** via the
  `ollama-proxy` (Torre primary + UM790 CPU fallback);
  ~101 tok/s end-to-end.

### Network

* FRITZ!Box 5690 Pro
* LAN connected server
* VPN access

---

## Running Core Services

### AI

* Open WebUI (chat + voice — `https://ai.amarolab.es`)
* Ollama (`qwen2.5:7b-instruct` shared by both front doors)
* Qdrant

### Voice (Phase D-1 — closed 2026-06-18)

Wyoming chain (HA Assist):

* `aurora-whisper` (STT, `base-int8`, D-1.2)
* `aurora-piper` (TTS, `es_ES-davefx-medium`, D-1.3)
* `aurora-wakeword` (`okay_nabu`, D-1.4)

Open WebUI HTTP shims (D-1.7):

* `aurora-whisper-http`
  (`fedirz/faster-whisper-server:0.6.0-rc.3-cpu`)
* `aurora-piper-http`
  (`ghcr.io/matatonic/openedai-speech:0.18.2`,
  voice mapped to `es_ES-sharvard-medium` speaker F)

HA Assist pipeline `AURORA v1` is the default /
preferred pipeline (language `es-ES`); voice surface
is exposed via `https://ha.amarolab.es`.

### Home Automation

* Home Assistant (HTTPS via `ha.amarolab.es`;
  reverse-proxy trust patch applied 2026-06-17)
* Mosquitto (authenticated + ACLs, hardened 2026-06-17)
* Zigbee2MQTT

### Infrastructure

* Docker
* PM2
* Cloudflared (**two separate tunnels**: existing
  `cloudflared` for Guardian Cloud; new
  `cloudflared-amarolab` on `ai-local_default` for
  AMAROLAB infrastructure surfaces — `ha.amarolab.es`,
  `ai.amarolab.es`)
* Restic Backups

### Hosted independent project

**Guardian Cloud** — independent project currently
hosted on AMAROLAB infrastructure.

IMPORTANT:

Guardian Cloud is considered production.

Do not modify Guardian Cloud without explicit approval.

---

## Current AI Architecture

Open WebUI (chat + voice)
↓
Ollama (`qwen2.5:7b-instruct`)
↓
Qdrant
↓
RAG Collections

In parallel:

Home Assistant Assist (`AURORA v1`)
↓
HA Ollama integration → same `qwen2.5:7b-instruct`

Collections:

* homelab_docs
* guardian_cloud
* ensambla2
* infra_audits

Future (consumer project — onboards after Phase E Foundation):

* myfreetour

---
## Current Operational Status

The Home Assistant integration is operational.

Validated capabilities:

- ha_get_state
- ha_call_service
- audit logging
- allowlist enforcement
- runtime secret loading
- Zigbee device control
- **voice control** through Aurora v1 Assist pipeline

Verified device:

`switch.impresora_3d`

Real-world state changes have been executed via:

* Open WebUI chat → `ha_call_service` (2026-06-17, Gate G-5)
* Home Assistant voice → `AURORA v1` pipeline →
  Mosquitto → Z2M → Sonoff S60ZBTPF (2026-06-18, Gate G-D5)

Both paths restore the printer to its `off` baseline
after every gate.

Future assistants should treat Home Assistant tool
integration and the Aurora v1 voice pipeline as
**PRODUCTION READY**.

### Phase D-1 closure (2026-06-18)

Aurora v1 voice pipeline operational on both front
doors:

* `https://ha.amarolab.es` — Home Assistant Assist
  push-to-talk over the Wyoming chain.
* `https://ai.amarolab.es` — Open WebUI browser mic
  over the OpenAI-API-compatible HTTP shims.

All six Phase D-1 gates landed with dated apply logs
(G-D1 through G-D6). Failure-mode rehearsal (G-D6)
confirmed the voice surface fails predictably when
each of its critical dependencies fails (STT, TTS,
LLM). Closeout document:
[`../09_logs/2026-06-18_phaseD1_closeout.md`](../09_logs/2026-06-18_phaseD1_closeout.md).

Voice exposure ACL: exactly one entity exposed —
`input_boolean.aurora_voice_canary`. The printer
(`switch.impresora_3d`) is exposed only for the
duration of a voice gate and reverted to
`should_expose = false` immediately afterwards.

## Documentation Status

Documentation consolidated into:

/home/diego/homelab

Single source of truth.

Audit documentation merged.

Security documentation merged.

AI documentation merged.

Operations documentation merged.

GitHub synchronized.

---

## Security Status

Completed:

* R-04 Mosquitto crash-loop (resolved 2026-06-13)
* R-12 Backups
* Mosquitto authentication hardening (2026-06-17) —
  moved off `allow_anonymous true` to authenticated
  `homeassistant` + `zigbee2mqtt` users with per-user
  ACLs; Gate G-5 re-executed end-to-end through the
  hardened broker. See
  `03_services/zigbee-stack/mosquitto/auth-hardening.md`
  and
  `09_logs/2026-06-17_mosquitto_auth_hardening_applied.md`
* HA reverse-proxy trust (2026-06-17) — `cloudflared-amarolab`
  bridge subnet trusted; LAN intentionally not trusted
  broadly. See
  `09_logs/2026-06-17_phaseD_ha_trusted_proxies_applied.md`
* Voice-exposure default-deny posture (2026-06-17)
  — only `input_boolean.aurora_voice_canary` is
  exposed to voice assistants; `homeassistant.*`,
  `hassio.*`, `recorder.*`, and any Guardian Cloud
  entity are permanent denies. Maintained through
  G-D4 / G-D5 / G-D6.
* Voice failure-mode safety story (2026-06-18, G-D6)
  — Whisper down / Piper down / Ollama unreachable
  scenarios validated; each fails predictably with no
  partial action and baseline restored.

Pending:

* R-01 Cloudflare Tunnel Token Rotation (existing
  Guardian-Cloud tunnel)

---

## Important Rules

* If it's not documented, it doesn't exist.
* Documentation first.
* Sanitize before GitHub.
* Do not expose secrets.
* Guardian Cloud is production.
* **Operator Git Approval** — never run `git commit`,
  `git push` or `git tag` without explicit operator approval
  requested immediately before each command. Approval never
  carries over between commands or sessions. See
  `PROJECT_RULES.md` → "Operator Git Approval".

---

## Current Goal

Build **AURORA v1** — the AMAROLAB Personal AI
Assistant.

Current phase:

**Phase D-1 — Voice — CLOSED 2026-06-18.**

Active follow-on: **Phase RTX-1 — Torre GPU node — CLOSED
2026-06-27. RTX-1.4 (Tailscale-only) + RTX-1.5 (headless
NSSM service) + RTX-1.6 (UM790 endpoint swap via the
`ollama-proxy`, Torre primary + UM790 fallback) all
complete. The front doors now consume Torre's GPU
(≈17.6× the UM790 CPU).**

Phase status:

* Phase A — Completed. `qwen2.5:7b-instruct` selected as the
  primary tool-calling model.
* Phase B — Completed. Tool layer delivered:
  `time_now`, `rag_search`, `audit_search`.
* Phase C — Completed (2026-06-17). `ha_get_state` and
  `ha_call_service` installed, attached to qwen2.5, and
  validated end-to-end. Refusal path proven against
  `recorder.purge`; read path proven against `sun.sun`;
  Gate G-5 happy-path write proven against
  `switch.impresora_3d` with full Z2M MQTT round-trip and
  baseline restore.
* **Phase D-1 — Voice — Closed 2026-06-18.**
  * D-1.1 (documentation skeleton) — closed.
  * **D-1.2 (Whisper) — closed 2026-06-17.**
  * **D-1.3 (Piper) — closed 2026-06-17.**
  * **D-1.4 (openWakeWord) — closed 2026-06-17.**
  * **D-1.5 (AURORA v1 pipeline + voice canary +
    exposure lockdown) — closed 2026-06-17.**
  * HA reverse-proxy trust patch — closed 2026-06-17.
  * **G-D4 (canary end-to-end) — PASSED 2026-06-17.**
  * **D-1.6 / G-D5 (real-device voice round-trip on
    `switch.impresora_3d`) — closed / PASSED 2026-06-18.**
  * **D-1.7 (Open WebUI Audio shims + audio surface)
    — closed 2026-06-18.**
  * **D-1.8 / G-D6 (failure-mode rehearsal) —
    closed / PASSED 2026-06-18.**
  * **D-1.9 (Phase D-1 closeout) — closed 2026-06-18.**

Closeout document:
[`../09_logs/2026-06-18_phaseD1_closeout.md`](../09_logs/2026-06-18_phaseD1_closeout.md).

---

## Next Immediate Task

Phase D-1 closed; **Phase RTX-1 closed 2026-06-27 —
RTX-1.4 + RTX-1.5 + RTX-1.6 all complete.** The UM790 front
doors consume Torre's GPU via the `ollama-proxy` (Torre
primary + UM790 fallback). **Phase E — Knowledge Platform
Foundation — CLOSED 2026-06-28.** All steps complete: E-0
(audit), E-1 (doc reconciliation), E-2 (fail-loud sync +
run-lock), E-3 (unified health.json), E-4 (log rotation +
backup-consistency decision), E-5 (drift measurement + restore
drill + audit-log check), E-6 (onboarding framework proven
end-to-end). All 13 E-0 findings resolved or accepted. Platform
health `overall_status=ok`. **Current phase: Phase F (to be
defined).** E-0 report:
[`../09_logs/2026-06-27_phaseE_E0_operational_audit_report.md`](../09_logs/2026-06-27_phaseE_E0_operational_audit_report.md).

The overview triad, `06_security/rtx_node_security.md`,
`06_security/security_posture.md`, and the live architecture
doc (`01_architecture/amarolab_architecture.md`, RTX
amendment merged) all reflect RTX-1.6. Apply log:
[`../09_logs/2026-06-27_phaseRTX1_6_endpoint_swap_applied.md`](../09_logs/2026-06-27_phaseRTX1_6_endpoint_swap_applied.md).

Pending post-D-1 follow-ups (tracked in
[`CURRENT_STATE.md`](CURRENT_STATE.md) and the closeout
document — none of these are mandatory next steps):

* `cloudflared-amarolab` standalone apply log.
* DNS / Cloudflare architecture doc amendments to
  record the separate-tunnel decision and the
  `ai.amarolab.es` binding.
* ~~**RTX-1.6** — UM790 `ollama` endpoint swap~~ **DONE
  (2026-06-27)** via the `ollama-proxy` (Torre primary +
  UM790 fallback). Apply log:
  [`../09_logs/2026-06-27_phaseRTX1_6_endpoint_swap_applied.md`](../09_logs/2026-06-27_phaseRTX1_6_endpoint_swap_applied.md).
* STT model-size bump candidate (`small` or
  `medium-int8`).
* Streaming TTS in Open WebUI.
* System-prompt trim (3 342 chars → cold-cache cost).
* R-01 Cloudflare Tunnel token rotation (Guardian
  Cloud tunnel).

Pre-Phase-E blockers: **none open.**
