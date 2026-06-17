# CURRENT_STATE

Related documents:

- AMAROLAB_HANDOFF.md
- ROADMAP.md
- INITIAL_SYSTEM_STATUS.md (historical)

Last updated: 2026-06-17

---

## Scope

This document captures the current state of the
**AMAROLAB** ecosystem and the build state of
**AURORA** (the AMAROLAB Personal AI Assistant).

**Guardian Cloud** is an independent project currently
hosted on AMAROLAB infrastructure; its internal state
is tracked by the Guardian Cloud project, not in this
document.

---

## AURORA — phase status

### Phase B — Tool layer

Status: Closed

Tools delivered and validated end-to-end against `qwen2.5:7b-instruct`:

- time_now
- rag_search
- audit_search

Closeout reference:
[`09_logs/2026-06-16_phaseB_closeout.md`](../09_logs/2026-06-16_phaseB_closeout.md).

### Phase C — Home Assistant integration

Status: **Completed** (2026-06-17 — Gate G-5)

Read path:

- `ha_get_state` installed in `webui.db.tool`
- `ha_get_state` attached to `qwen2.5` via `meta.toolIds`
- Real Home Assistant read validated against `sun.sun`
  (`result_code = "ok"`, `state = "above_horizon"`)
- Closeout:
  [`09_logs/2026-06-17_phaseC_ha_get_state_real_validation.md`](../09_logs/2026-06-17_phaseC_ha_get_state_real_validation.md)

Write path:

- `ha_call_service` installed in `webui.db.tool`
- `ha_call_service` attached to `qwen2.5` via `meta.toolIds`
- Tool-level refusal path validated against the
  out-of-allowlist canonical probe `recorder.purge`
  (`result_code = "refused"`, no HA call issued)
- Refusal closeout:
  [`09_logs/2026-06-17_phaseC_refusal_validation_applied.md`](../09_logs/2026-06-17_phaseC_refusal_validation_applied.md)
- **Gate G-5 — first real happy path executed against
  `switch.impresora_3d` (Sonoff S60ZBTPF). Sequence
  pre-read (`off`) → `turn_on` → verify (`on`) →
  `turn_off` → restore-verify (`off`). All 5 audit
  lines: `allowed=true`, `result_code="ok"`. HA
  observed both state transitions via Z2M MQTT
  round-trip. Plug restored to baseline `off`.**
- Gate G-5 closeout:
  [`09_logs/2026-06-17_phaseC_gate_g5_applied.md`](../09_logs/2026-06-17_phaseC_gate_g5_applied.md)
- Phase C closeout:
  [`09_logs/2026-06-17_phaseC_closeout.md`](../09_logs/2026-06-17_phaseC_closeout.md)

Allowlist (D-12) is enforced at the Tool boundary.

Denied domains include `homeassistant.*`, `hassio.*`,
`recorder.*`.

### Phase D — Voice

Status: **In progress.**

- **D-1.1 (documentation skeleton)** — closed.
- **D-1.2 (Whisper standup)** — closed (2026-06-17).
  - `aurora-whisper` container running on
    `ai-local_default`.
  - Image: `rhasspy/wyoming-whisper:3.2.0` (digest
    `sha256:966e1b…`).
  - Model: `base-int8`. Language: auto-detect.
  - Wyoming endpoint reachable at
    `aurora-whisper:10300` (internal-only; no host
    port).
  - Bind mount: `/srv/homelab/data/whisper/wyoming`
    → `/data` (76 MB model cache after first load).
  - **Gate G-D1 (Wyoming path) passed.** WER 0.000
    against the canonical openai/whisper smoke-test
    clip; total latency 609 ms on 11.00 s of audio;
    real-time factor 0.055 on UM790 CPU.
  - G-D1 HTTP-shim path deferred to D-1.7 (no
    consumer until Open WebUI Audio integration);
    HTTP-shim image pre-pulled.
  - Apply log:
    [`09_logs/2026-06-17_phaseD_whisper_installed.md`](../09_logs/2026-06-17_phaseD_whisper_installed.md)

Not yet:

- D-1.3 — Piper (`aurora-piper`)
- D-1.4 — openWakeWord (`aurora-wakeword`)
- D-1.5 — HA Assist pipeline (`AURORA v1`)
- D-1.6 — Real-device end-to-end (G-D5)
- D-1.7 — Open WebUI Audio integration (also closes
  G-D1 HTTP-shim path)
- D-1.8 — Failure-mode rehearsal (G-D6)
- D-1.9 — Phase D-1 closeout

---

## AI stack

### Open WebUI

Status: Healthy

Primary tool-calling model:

- id: `qwen2.5:7b-instruct`
- `base_model_id`: **NULL** (D-35 preserved)
- `meta.toolIds`:
  `["time_now","rag_search","audit_search","ha_get_state","ha_call_service"]`
- `params.system`: Amarolab v0.1 system prompt
  (≈ 3 342 chars)

Tools registered in `webui.db.tool`:

- time_now
- rag_search
- audit_search
- ha_get_state
- ha_call_service
- legacy Jarvis tools (`docker_containers`, `docker_logs`,
  `system_status`) — scoped to `llama3*` rows only per D-20

### Ollama

Status: Operational

### Qdrant

Status: Operational

RAG collections:

- homelab_docs
- guardian_cloud
- ensambla2
- infra_audits

---

## Home Assistant

Status: Operational

- MQTT integration: enabled inside Home Assistant
- Zigbee2MQTT discovery: enabled (auto-discovery active)
- First Zigbee devices imported:
  - **Impresora 3D** — Sonoff S60ZBTPF smart plug
  - **Toldo** — Sonoff MINI-ZBRBS roller shutter
  - **Zigbee2MQTT Bridge** (the bridge entity itself)

Reference:
[`03_services/zigbee-stack/zigbee2mqtt_first_devices.md`](../03_services/zigbee-stack/zigbee2mqtt_first_devices.md).

---

## Mosquitto

Status: Operational — **hardened** (2026-06-17)

Current authentication posture: **authenticated MQTT
users + ACLs**.

- `allow_anonymous false`
- `password_file /mosquitto/config/passwords`
- `acl_file /mosquitto/config/acls`
- Users: `homeassistant`, `zigbee2mqtt` (passwords
  hashed in `passwords`; plaintext in
  `/home/diego/.secrets/mqtt-credentials.env`, never
  in repo)
- Per-user ACLs scope each principal to its required
  topic namespaces (default-deny)
- Anonymous `mosquitto_sub` is refused with
  `Connection Refused: not authorised`
- Gate G-5 re-executed end-to-end through the hardened
  broker — 5 audit lines, all
  `allowed=true, result_code="ok"`, baseline restored

Reference:
[`03_services/zigbee-stack/mosquitto/auth-hardening.md`](../03_services/zigbee-stack/mosquitto/auth-hardening.md).
Apply log:
[`09_logs/2026-06-17_mosquitto_auth_hardening_applied.md`](../09_logs/2026-06-17_mosquitto_auth_hardening_applied.md).

---

## Zigbee2MQTT

Status: Operational

- Adapter: Sonoff Zigbee Dongle Plus
- Frontend: **enabled**
- Home Assistant discovery: **enabled**
- First devices joined and exposed to Home Assistant
  (see Home Assistant section above)

---

## Voice stack

Status: **Operational — STT only** (D-1.2 closed
2026-06-17).

`aurora-whisper` (Wyoming STT) is running on
`ai-local_default`.

- Container: `aurora-whisper`
- Image: `rhasspy/wyoming-whisper:3.2.0`
- Endpoint: `tcp://aurora-whisper:10300` (internal)
- Model: `base-int8`
- Real-time factor on UM790 CPU: **0.055** on the
  G-D1 reference clip (~18× faster than real time)
- Bind mount: `/srv/homelab/data/whisper/wyoming`
  (76 MB cached)
- No host port published

Not yet deployed (Phase D-1 remainder):

- `aurora-piper` (TTS) — D-1.3
- `aurora-wakeword` (openWakeWord) — D-1.4
- HA Assist pipeline (`AURORA v1`) — D-1.5
- HTTP shim for Open WebUI integration — D-1.7

Reference architecture:
[`03_services/voice-stack/README.md`](../03_services/voice-stack/README.md).
Whisper deployment plan:
[`03_services/voice-stack/whisper/faster-whisper-deployment.md`](../03_services/voice-stack/whisper/faster-whisper-deployment.md).
Apply log:
[`09_logs/2026-06-17_phaseD_whisper_installed.md`](../09_logs/2026-06-17_phaseD_whisper_installed.md).

---

## Storage

Status: Operational

Current setup:

- **2 TB USB disk** connected directly to the mini server
- Hosts the Restic backup repository and bulk data
- **Not** a dedicated NAS

Planned:

- Dedicated NAS purchase, to be scheduled later
- Migration of backups and bulk data once procured

---

## Backups

Status: Operational

- Restic installed
- Repository initialised on the 2 TB USB disk
- Snapshot validated

---

## Ingest service

Status: Versioned

Path: `ai-stack/ingest`

Includes:

- chunking
- embeddings
- reranker
- qdrant storage
- filesystem connector
- git connector

---

## Documentation

Status: Consolidated

Repository structure:

- 00_overview
- 01_architecture
- 02_infrastructure
- 03_services
- 04_ai_system
- 05_data
- 06_security
- 07_operations
- 08_projects
- 09_logs

---

## GitHub

Status: Synchronized

Recent work landed on `main`:

- Phase B closeout
- Phase C Tool installs (`ha_get_state`, `ha_call_service`)
- Gate G-4 — qwen2.5 `meta.toolIds` extension
- C-5 — Tool-level refusal validation
- C-6a — first real Home Assistant read against `sun.sun`
- Zigbee2MQTT first devices imported into Home Assistant
- Phase C documentation sync (tag `v0.3-phase-c-doc-sync`)
- Gate G-5 — first real `ha_call_service` happy path
  against `switch.impresora_3d`
- Phase C closeout

---

## Secrets

All sensitive values are kept out of versioned documentation.

Placeholders used throughout:

- `${HA_BASE_URL}`
- `${HA_LLAT}`
- `${WEBUI_SECRET_KEY}`
- `${QDRANT_API_KEY}`

Authoritative location for live values: `ai-stack/.env`
(not committed in plain text).

---

## Known pending items

1. **Cloudflare Tunnel token rotation** (R-01)
2. **Phase D** — Voice interface — **in progress.**
   D-1.2 closed (Whisper). **D-1.3 (Piper)** is the
   next active step.
3. **Dedicated NAS** — procurement and data migration
4. **MyFreeTour** RAG collection (Phase E)