# CURRENT_STATE

Related documents:

- AMAROLAB_HANDOFF.md
- ROADMAP.md
- INITIAL_SYSTEM_STATUS.md (historical)

Last updated: 2026-06-18

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

Status: **Phase D-1 closed** (2026-06-18 — D-1.9
closeout). Aurora v1 voice pipeline operational on both
front doors. All six Phase D-1 gates (G-D1 through G-D6)
landed with dated apply logs.

#### D-1 sub-step status

| Step | Description | Status | Apply log |
|---|---|---|---|
| D-1.1 | Documentation skeleton | Closed | (planning artefact, no apply log) |
| **D-1.2** | Whisper standup (`aurora-whisper`, G-D1 Wyoming half) | **Closed (2026-06-17)** | [`09_logs/2026-06-17_phaseD_whisper_installed.md`](../09_logs/2026-06-17_phaseD_whisper_installed.md) |
| **D-1.3** | Piper standup (`aurora-piper`, G-D2 Wyoming half) | **Closed (2026-06-17)** | [`09_logs/2026-06-17_phaseD_piper_installed.md`](../09_logs/2026-06-17_phaseD_piper_installed.md) |
| **D-1.4** | openWakeWord standup (`aurora-wakeword`, G-D3 container/probe half) | **Closed (2026-06-17)** | [`09_logs/2026-06-17_phaseD_wakeword_installed.md`](../09_logs/2026-06-17_phaseD_wakeword_installed.md) |
| **D-1.5** | AURORA v1 Assist pipeline + voice canary + voice-exposure lockdown (G-D3 HA-UI half) | **Closed (2026-06-17)** | [`09_logs/2026-06-17_phaseD_voice_pipeline.md`](../09_logs/2026-06-17_phaseD_voice_pipeline.md) |
| HA reverse-proxy trust patch | `configuration.yaml` `http.trusted_proxies` + `external_url`; unblocks Secure Context | Closed (2026-06-17) | [`09_logs/2026-06-17_phaseD_ha_trusted_proxies_applied.md`](../09_logs/2026-06-17_phaseD_ha_trusted_proxies_applied.md) |
| **G-D4** | Voice canary Read → Write → Verify → Restore through `AURORA v1` from `https://ha.amarolab.es` | **PASSED (2026-06-17)** | [`09_logs/2026-06-17_phaseD_gate_gd4_applied.md`](../09_logs/2026-06-17_phaseD_gate_gd4_applied.md) |
| **D-1.6 / G-D5** | Real-device voice round-trip against `switch.impresora_3d` (Sonoff S60ZBTPF via Mosquitto + Z2M); voice Write + voice Restore; baseline `off` restored | **Closed / PASSED (2026-06-18)** | [`09_logs/2026-06-18_phaseD_gate_gd5_applied.md`](../09_logs/2026-06-18_phaseD_gate_gd5_applied.md) |
| **D-1.7** | Open WebUI Audio integration: `aurora-whisper-http` + `aurora-piper-http` (OpenAI-API-compatible shims), `webui.db.audio.*` patched, voice on `https://ai.amarolab.es`; closes G-D1 HTTP-shim half + G-D2 HTTP-shim half + C-D-07 + C-D-09 | **Closed (2026-06-18)** | [`09_logs/2026-06-18_phaseD_openwebui_audio_applied.md`](../09_logs/2026-06-18_phaseD_openwebui_audio_applied.md) |
| **D-1.8 / G-D6** | Failure-mode rehearsal (Whisper down §7.1, Piper down §7.2, Ollama unreachable §7.3); one acceptance partial on HA TTS-failure log granularity (functional behaviour PASS); canary baseline restored; printer untouched | **Closed / PASSED (2026-06-18)** | [`09_logs/2026-06-18_phaseD_gate_gd6_applied.md`](../09_logs/2026-06-18_phaseD_gate_gd6_applied.md) |
| **D-1.9** | Phase D-1 closeout — overview-triad amendment + closeout log | **Closed (2026-06-18)** | [`09_logs/2026-06-18_phaseD1_closeout.md`](../09_logs/2026-06-18_phaseD1_closeout.md) |

#### Operational surface

Aurora v1 voice is reachable on both front doors:

- **Home Assistant voice** — `https://ha.amarolab.es`
  (Assist pipeline `AURORA v1`, push-to-talk,
  Wyoming chain: `aurora-whisper:10300` →
  `qwen2.5:7b-instruct` on `ollama:11434` →
  `aurora-piper:10200`). Voice-exposure ACL: only
  `input_boolean.aurora_voice_canary`.
- **Open WebUI voice** — `https://ai.amarolab.es`
  (browser mic, OpenAI-API-compatible HTTP shims:
  `aurora-whisper-http:8000` → `qwen2.5:7b-instruct`
  → `aurora-piper-http:8000` with
  `es_ES-sharvard-medium` speaker F). Default TTS
  auto-playback **off** per C-D-07 (Open WebUI 0.8.10
  has no backend auto-play; the shipped per-user
  default is off).

#### Voice safety story (G-D6)

- **Whisper down** — STT fails closed; HA Assist
  surfaces "speech-to-text failed"; no entity state
  change; no conversation-agent call.
- **Piper down** — intent still lands (canary
  toggles) but reply is audibly silent (TTS path is
  the only break); UI banner indicates a silent
  failure.
- **Ollama unreachable** — clean conversation-agent
  error within seconds; no partial action; STT path
  still works (transcripts captured).

All three scenarios end with the canary back to `off`
baseline and `switch.impresora_3d` untouched
(voice-exposure stayed `false` throughout G-D6).

#### Carried follow-ups (post-Phase-D-1)

| Item | Note |
|---|---|
| LLM 6 tok/s ceiling on UM790 CPU | Deferred to RTX 5070 AI-node work (see [`04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md`](../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md)). Voice-stack architecture is GPU-ready; only the `ollama` endpoint target changes. |
| STT fidelity | `base-int8` produces sub-canonical Spanish on short utterances. Model-size bump (`small` or `medium-int8`) candidate. |
| HA voice-pipeline intent-matching variability | `qwen2.5` occasionally fails to resolve voice canary aliases via the WS pipeline; REST `/api/conversation/process` against the same `agent_id` resolves the same phrasing reliably. Tracked as `HA-VOICE-001`. |
| HA TTS-failure log granularity | HA Assist surfaces TTS failures only on the WS `assist_pipeline/pipeline_debug` stream and the UI banner, not on the INFO-level core log. Documented partial on G-D6 §7.2. |
| Streaming TTS in Open WebUI | Open WebUI does not stream STT/TTS today; first-token wait dominates perceived latency. |
| Open WebUI system prompt size | 3 342 chars / 822 tokens → 16.9 s cold-cache prompt eval per new conversation. Trim candidate, paired with RAG audit. |
| `ai.amarolab.es` was already bound in D-1.7 | Operator action remaining: ensure DNS + Cloudflare ingress posture stays current. |
| `cloudflared-amarolab` standalone apply log | Deployment validated through D-1.5 / D-1.7 / G-D6 but no dedicated standalone apply log yet. |
| DNS / architecture doc amendments | [`02_infrastructure/cloudflare/amarolab_dns_architecture.md`](../02_infrastructure/cloudflare/amarolab_dns_architecture.md) and [`02_infrastructure/cloudflare/cloudflared_audit_2026-06-17.md`](../02_infrastructure/cloudflare/cloudflared_audit_2026-06-17.md) still describe the original "attach existing tunnel" plan; the **separate** `amarolab` tunnel + container shipped instead. |
| R-D-13 | Migrate the Open WebUI STT HTTP shim away from the unmaintained `fedirz/faster-whisper-server`. Post-Phase-D maintenance. |
| R-01 | Cloudflare Tunnel token rotation (existing Guardian-Cloud tunnel). Independent of Phase D. |

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

Audio surface (D-1.7):

- `audio.stt.engine` = `openai`,
  `audio.stt.openai.api_base_url` =
  `http://aurora-whisper-http:8000/v1`,
  model `Systran/faster-whisper-base`.
- `audio.tts.engine` = `openai`,
  `audio.tts.openai.api_base_url` =
  `http://aurora-piper-http:8000/v1`, model `tts-1`,
  voice `alloy` (mapped to `es_ES-sharvard-medium`
  speaker F by the Amarolab voice mapping in
  `/srv/homelab/data/openedai-speech/voice_to_speaker.yaml`).
- Auto-playback default **off** (C-D-07 closed).

### Ollama

Status: Operational

`qwen2.5:7b-instruct` is shared by **two independent
integrations**:

- The Open WebUI chat path (`webui.db.tool` + `meta.toolIds`).
- The Home Assistant Ollama integration backing the
  `AURORA v1` Assist pipeline conversation agent.

A restart on either side does not disturb the other.

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

- HTTPS external URL: `https://ha.amarolab.es`
  (`homeassistant.external_url` YAML-managed).
- Reverse-proxy trust: `http.use_x_forwarded_for: true`
  with `http.trusted_proxies: [172.18.0.0/16,
  127.0.0.1, ::1]`. Only the `cloudflared-amarolab`
  bridge subnet is trusted; the LAN is intentionally
  not trusted broadly.
- MQTT integration: enabled inside Home Assistant
- Zigbee2MQTT discovery: enabled (auto-discovery active)
- Wyoming integrations (per D-1.5): `aurora-whisper`
  (STT), `aurora-piper` (TTS), `aurora-wakeword`.
- Ollama integration (per D-1.5): `http://ollama:11434`
  / `qwen2.5:7b-instruct`.
- Assist pipeline `AURORA v1` is the default /
  preferred pipeline (language `es-ES`).
- Voice canary helper: `input_boolean.aurora_voice_canary`
  (state `off`, baseline restored after every gate).
- Voice-exposure ACL: exactly **one** entity exposed —
  `input_boolean.aurora_voice_canary`. The printer
  (`switch.impresora_3d`) is reverted to `should_expose
  = false` after G-D5; permanent denies cover
  `homeassistant.*`, `hassio.*`, `recorder.*`, and any
  Guardian Cloud entity.

First Zigbee devices imported:

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
- Gate G-D5 (voice) re-executed end-to-end through the
  hardened broker — voice → HA → Mosquitto → Z2M →
  Sonoff S60ZBTPF round-trip confirmed; baseline `off`
  restored

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

Status: **Operational end-to-end** (Phase D-1 closed
2026-06-18).

### Home Assistant voice path (Wyoming)

- `aurora-whisper` (Wyoming STT) on `ai-local_default`
  - Image: `rhasspy/wyoming-whisper:3.2.0`
  - Endpoint: `tcp://aurora-whisper:10300` (internal)
  - Model: `base-int8`
  - Real-time factor on UM790 CPU: **0.055** on the
    G-D1 reference clip
- `aurora-piper` (Wyoming TTS) on `ai-local_default`
  - Image: `rhasspy/wyoming-piper:<pinned tag>`
  - Endpoint: `tcp://aurora-piper:10200` (internal)
  - Voice: `es_ES-davefx-medium` (HA-side selection
    per pipeline spec; speaker F per C-D-08)
- `aurora-wakeword` (Wyoming openWakeWord) on
  `ai-local_default`
  - Endpoint: `tcp://aurora-wakeword:10400` (internal)
  - Wake word: `okay_nabu` (push-to-talk is the D-1
    default in HA Assist; wake-word path validated by
    Wyoming describe + synthetic detection probe at
    D-1.4)
- HA Assist pipeline `AURORA v1`
  - Default / preferred pipeline
  - Slots: `aurora-wakeword` / `aurora-whisper` /
    HA Ollama (`qwen2.5:7b-instruct`) / `aurora-piper`

### Open WebUI audio path (OpenAI-API HTTP shims)

- `aurora-whisper-http` (faster-whisper HTTP shim) on
  `ai-local_default`
  - Image:
    `fedirz/faster-whisper-server:0.6.0-rc.3-cpu`
  - Endpoint: `http://aurora-whisper-http:8000/v1`
    (internal)
  - Model: `Systran/faster-whisper-base`, `int8`
  - Bind mount:
    `/srv/homelab/data/whisper/http`
- `aurora-piper-http` (openedai-speech) on
  `ai-local_default`
  - Image: `ghcr.io/matatonic/openedai-speech:0.18.2`
  - Endpoint: `http://aurora-piper-http:8000/v1`
    (internal)
  - Voice mapping: all OpenAI standard voice slots
    route to `es_ES-sharvard-medium` speaker F
    (`/srv/homelab/data/openedai-speech/voice_to_speaker.yaml`)
  - XTTS disabled via `--xtts_device none`
- Open WebUI `webui.db.audio.*` patched to route STT
  and TTS at the two shims; default auto-playback
  off (C-D-07).

### Latency profile (read-only, D-1.7 §4)

Dominant bottleneck is `qwen2.5:7b-instruct` response
generation on UM790 CPU at ~6 tok/s (≈ 89 % of
warm-cycle latency). STT (Whisper, ~0.6 s warm) and
TTS (Piper, ~0.6 s) together contribute under 2 s.
First-message cold KV cache adds ~16.9 s for the
3 342-char Amarolab system prompt and amortises to
~0.2 s on every subsequent turn.

Performance optimization is **deferred to the RTX 5070
AI-node bridge** ([`04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md`](../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md));
the voice-stack architecture is GPU-ready and only the
`ollama` endpoint target needs to change.

Reference architecture:
[`03_services/voice-stack/README.md`](../03_services/voice-stack/README.md).
Whisper deployment plan:
[`03_services/voice-stack/whisper/faster-whisper-deployment.md`](../03_services/voice-stack/whisper/faster-whisper-deployment.md).
Pipeline spec:
[`03_services/voice-stack/ha-assist/pipeline-spec.md`](../03_services/voice-stack/ha-assist/pipeline-spec.md).

---

## Cloudflare

Status: Operational with **two separate tunnels**.

- **Guardian Cloud tunnel** — `cloudflared` container
  on `cloudflare-net`. Serves
  `app.guardiancloud.app` + `api.guardiancloud.app`.
  **Untouched** throughout Phase D.
- **Amarolab tunnel** — `cloudflared-amarolab`
  container on `ai-local_default`. Public Hostnames:
  - `ha.amarolab.es` → `http://192.168.178.79:8123`
    (Home Assistant)
  - `ai.amarolab.es` → Open WebUI (bound during D-1.7;
    serves both chat and audio)
- Connector token persisted at
  `/home/diego/.secrets/cloudflared-amarolab.env`
  (mode `0600`, never in repo). Per Lesson 008.

The original Cloudflare DNS architecture note in
[`02_infrastructure/cloudflare/amarolab_dns_architecture.md`](../02_infrastructure/cloudflare/amarolab_dns_architecture.md)
described attaching the existing Guardian Cloud
tunnel to `ai-local_default`. The **shipped**
architecture is a separate tunnel + container, for
blast-radius isolation between Guardian Cloud product
surface and AMAROLAB infrastructure surface. Doc
amendment carried as a post-D-1.9 documentation-sync
follow-up.

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
- D-1.5 anchor snapshot `63c072f4` retained as the
  pre-voice-pipeline rollback point (still in the
  repository, unchanged through D-1.6 / D-1.7 / D-1.8).

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
- Mosquitto authentication hardening (tag
  `v0.4-mosquitto-hardening`)
- Phase D-1 voice stack: Whisper / Piper /
  openWakeWord / `AURORA v1` pipeline / HA reverse-
  proxy trust patch / G-D4 / G-D5 / D-1.7 Open WebUI
  audio shims / G-D6 failure-mode rehearsal / D-1.9
  closeout

---

## Secrets

All sensitive values are kept out of versioned documentation.

Placeholders used throughout:

- `${HA_BASE_URL}`
- `${HA_LLAT}`
- `${WEBUI_SECRET_KEY}`
- `${QDRANT_API_KEY}`

Authoritative location for live values: `ai-stack/.env`
(not committed in plain text). Cloudflare connector
token for the `amarolab` tunnel lives at
`/home/diego/.secrets/cloudflared-amarolab.env`
(mode `0600`, never in repo).

---

## Known pending items

1. **Cloudflare Tunnel token rotation** (R-01) — existing
   Guardian-Cloud tunnel.
2. **Phase D-2 and beyond** — RTX 5070 AI-node bridge
   (LLM acceleration), streaming TTS, prompt
   trimming, STT model-size bump. **Not started.**
3. **Dedicated NAS** — procurement and data migration.
4. **MyFreeTour** RAG collection (Phase E).
5. **DNS / Cloudflare architecture doc amendments**
   — record the separate-tunnel decision and the
   `ai.amarolab.es` binding in
   [`02_infrastructure/cloudflare/`](../02_infrastructure/cloudflare/).
6. **`cloudflared-amarolab` standalone apply log** —
   deployment validated through D-1.5 → G-D6 but no
   dedicated standalone log yet.
