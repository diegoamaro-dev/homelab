# CURRENT_STATE

Related documents:

- AMAROLAB_HANDOFF.md
- ROADMAP.md
- INITIAL_SYSTEM_STATUS.md (historical)

Last updated: 2026-06-17

---

## Phase status

### Phase B — Tool layer

Status: Closed

Tools delivered and validated end-to-end against `qwen2.5:7b-instruct`:

- time_now
- rag_search
- audit_search

Closeout reference:
[`09_logs/2026-06-16_phaseB_closeout.md`](../09_logs/2026-06-16_phaseB_closeout.md).

### Phase C — Home Assistant integration

Status: In progress

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
- Closeout:
  [`09_logs/2026-06-17_phaseC_refusal_validation_applied.md`](../09_logs/2026-06-17_phaseC_refusal_validation_applied.md)
- **Gate G-5 — first real `ha_call_service` happy path on a
  controllable entity — PENDING**

Allowlist (D-12) is enforced at the Tool boundary.

Denied domains include `homeassistant.*`, `hassio.*`,
`recorder.*`.

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

Status: Operational

Current authentication posture: **anonymous local access**
(`allow_anonymous true`).

This is the **validation posture** for bringing up the
Zigbee2MQTT ↔ Mosquitto ↔ Home Assistant chain.

It is **not** the final hardened posture.

Hardening (authenticated MQTT users + ACLs) is planned
before broader device onboarding and before Phase D voice
work.

---

## Zigbee2MQTT

Status: Operational

- Adapter: Sonoff Zigbee Dongle Plus
- Frontend: **enabled**
- Home Assistant discovery: **enabled**
- First devices joined and exposed to Home Assistant
  (see Home Assistant section above)

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

1. **Phase C Gate G-5** — first real `ha_call_service`
   happy path on a controllable entity
2. **Phase C C-7** — Phase C closeout + Phase D handoff note
3. **Mosquitto hardening** — move off `allow_anonymous true`
   to authenticated users + ACLs
4. **Cloudflare Tunnel token rotation** (R-01)
5. **Dedicated NAS** — procurement and data migration
6. **MyFreeTour** RAG collection (Phase E)
7. **Voice interface** — Whisper + Piper + HA Assist
   (Phase D)
