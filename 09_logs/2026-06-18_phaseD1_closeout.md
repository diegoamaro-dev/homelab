# Phase D-1 — Voice — CLOSEOUT

- **Date:** 2026-06-18
- **Phase step:** **D-1.9 — Phase D-1 closeout.**
- **Ecosystem:** **AMAROLAB** — Personal Innovation Lab and Digital
  Infrastructure Ecosystem.
- **Assistant:** **AURORA** — Personal AI Assistant for the AMAROLAB
  ecosystem.
- **Independent project on AMAROLAB infrastructure:** **Guardian Cloud**
  — not modified by this work.
- **Status:** **CLOSED.** Aurora v1 voice pipeline operational on both
  front doors. All six Phase D-1 gates (G-D1 through G-D6) landed with
  dated apply logs. Overview triad
  ([`../00_overview/CURRENT_STATE.md`](../00_overview/CURRENT_STATE.md),
  [`../00_overview/AMAROLAB_HANDOFF.md`](../00_overview/AMAROLAB_HANDOFF.md),
  [`../00_overview/ROADMAP.md`](../00_overview/ROADMAP.md)) reconciled
  with the validated state as of 2026-06-18.
- **Scope:** Documentation only. **No infrastructure changes**
  performed by this log. **No validation gates rerun.** No container
  touched. No `webui.db` patch. No HA configuration change. No
  Cloudflare DNS or tunnel ingress mutation. No secret rotated or
  printed.

---

## 1. Purpose

D-1.9 is the **closeout step** of Phase D-1 (Voice).
Per Lesson 005 ("make it work, validate, harden,
document") and the closure patterns of Phase A
([`./2026-06-15_phaseA_closeout.md`](./2026-06-15_phaseA_closeout.md)),
Phase B ([`./2026-06-16_phaseB_closeout.md`](./2026-06-16_phaseB_closeout.md))
and Phase C ([`./2026-06-17_phaseC_closeout.md`](./2026-06-17_phaseC_closeout.md)),
the overview triad is amended **at the closure step**,
not at each intermediate apply log. This log is the
durable closure record for Phase D-1 and the cross-
reference point future sessions will use to confirm
that Phase D-1 is closed.

This log does **not** start any new phase. Per the
operator instruction at the start of the session:
**STOP after D-1.9 closeout.**

---

## 2. Phase D-1 — gate ledger

All six Phase D-1 validation gates are closed.

| Gate | Half | Status | Date | Apply log |
|---|---|---|---|---|
| G-D1 | Wyoming STT (`aurora-whisper`, WER 0.000, RTF 0.055) | Closed | 2026-06-17 (D-1.2) | [`./2026-06-17_phaseD_whisper_installed.md`](./2026-06-17_phaseD_whisper_installed.md) |
| G-D1 | HTTP shim (`aurora-whisper-http`, OpenAI-API-compatible) | Closed | 2026-06-18 (D-1.7) | [`./2026-06-18_phaseD_openwebui_audio_applied.md`](./2026-06-18_phaseD_openwebui_audio_applied.md) |
| G-D2 | Wyoming TTS (`aurora-piper`, `es_ES-davefx-medium`, RTF 0.31) | Closed | 2026-06-17 (D-1.3) | [`./2026-06-17_phaseD_piper_installed.md`](./2026-06-17_phaseD_piper_installed.md) |
| G-D2 | HTTP shim (`aurora-piper-http`, `openedai-speech`, voice mapped to `es_ES-sharvard-medium` speaker F) | Closed | 2026-06-18 (D-1.7) | [`./2026-06-18_phaseD_openwebui_audio_applied.md`](./2026-06-18_phaseD_openwebui_audio_applied.md) |
| G-D3 | openWakeWord container / probe (`aurora-wakeword`, `okay_nabu` detection probe) | Closed | 2026-06-17 (D-1.4) | [`./2026-06-17_phaseD_wakeword_installed.md`](./2026-06-17_phaseD_wakeword_installed.md) |
| G-D3 | HA UI (Wyoming integrations + pipeline slots) | Closed | 2026-06-17 (D-1.5) | [`./2026-06-17_phaseD_voice_pipeline.md`](./2026-06-17_phaseD_voice_pipeline.md) |
| **G-D4** | Voice canary end-to-end (Read → Write → Verify → Restore) over HTTPS via `https://ha.amarolab.es` | **PASSED** | 2026-06-17 | [`./2026-06-17_phaseD_gate_gd4_applied.md`](./2026-06-17_phaseD_gate_gd4_applied.md) |
| **G-D5** | Real-device voice round-trip (`switch.impresora_3d` — Sonoff S60ZBTPF via Mosquitto + Z2M). Executed scope: voice Write → voice Restore. Baseline `off` restored. Read / Verify query exchanges were not spoken (procedurally noted in apply log §2); query path independently proven by G-D4. | **PASSED** | 2026-06-18 | [`./2026-06-18_phaseD_gate_gd5_applied.md`](./2026-06-18_phaseD_gate_gd5_applied.md) |
| **G-D6** | Failure-mode rehearsal. §7.1 Whisper down — fail-closed; §7.2 Piper down — degrade-but-execute (silent reply); §7.3 Ollama unreachable — clean timeout. One acceptance partial on the literal "HA logs TTS failure explicitly" reading (HA Assist surfaces the failure on the WS pipeline-debug stream + UI banner, not on the INFO-level core log). All seven cross-scenario invariants hold. Canary baseline `off` restored. Printer untouched. | **PASSED** | 2026-06-18 | [`./2026-06-18_phaseD_gate_gd6_applied.md`](./2026-06-18_phaseD_gate_gd6_applied.md) |

Supplemental apply logs landed under Phase D-1:

| Log | Purpose |
|---|---|
| [`./2026-06-17_phaseD_ha_trusted_proxies_applied.md`](./2026-06-17_phaseD_ha_trusted_proxies_applied.md) | HA `configuration.yaml` reverse-proxy trust patch unblocking Secure-Context access to `https://ha.amarolab.es`. Single-file edit, single container restart, no secrets. |

---

## 3. Phase D-1 — sub-step ledger

| Step | Description | Status |
|---|---|---|
| D-1.1 | Documentation skeleton | Closed (planning artefact; no apply log) |
| **D-1.2** | Whisper standup (`aurora-whisper` Wyoming STT) | **Closed 2026-06-17** |
| **D-1.3** | Piper standup (`aurora-piper` Wyoming TTS) | **Closed 2026-06-17** |
| **D-1.4** | openWakeWord standup (`aurora-wakeword` Wyoming) | **Closed 2026-06-17** |
| **D-1.5** | AURORA v1 Assist pipeline + voice canary + voice-exposure lockdown | **Closed 2026-06-17** |
| **D-1.6** | Real-device voice end-to-end (G-D5 on `switch.impresora_3d`) | **Closed 2026-06-18** |
| **D-1.7** | Open WebUI Audio integration (STT + TTS HTTP shims; `webui.db.audio.*` patch; closes G-D1 HTTP-shim half, G-D2 HTTP-shim half, C-D-07, C-D-09) | **Closed 2026-06-18** |
| **D-1.8** | Failure-mode rehearsal (G-D6 §7.1 / §7.2 / §7.3) | **Closed 2026-06-18** |
| **D-1.9** | Phase D-1 closeout (this log + overview-triad amendment) | **Closed 2026-06-18** |

---

## 4. Final operational surface

Aurora v1 voice is reachable on both front doors.

### 4.1 Home Assistant voice — `https://ha.amarolab.es`

- Assist pipeline **`AURORA v1`** is the default /
  preferred pipeline (language `es-ES`).
- Wyoming chain on `ai-local_default`:
  - STT: `aurora-whisper:10300` (Wyoming,
    `rhasspy/wyoming-whisper:3.2.0`, model
    `base-int8`).
  - TTS: `aurora-piper:10200` (Wyoming, voice
    `es_ES-davefx-medium`).
  - Wake word: `aurora-wakeword:10400` (Wyoming,
    `okay_nabu`; push-to-talk is the D-1 default).
- Conversation agent: HA Ollama integration against
  `http://ollama:11434` / `qwen2.5:7b-instruct`.
- Voice-exposure ACL: exactly **one** entity exposed —
  `input_boolean.aurora_voice_canary`.

### 4.2 Open WebUI voice + chat — `https://ai.amarolab.es`

- Browser microphone (Secure Context over HTTPS) into
  OpenAI-API-compatible HTTP shims on
  `ai-local_default`:
  - STT: `aurora-whisper-http:8000`
    (`fedirz/faster-whisper-server:0.6.0-rc.3-cpu`,
    `Systran/faster-whisper-base`, `int8`).
  - TTS: `aurora-piper-http:8000`
    (`ghcr.io/matatonic/openedai-speech:0.18.2`;
    voice mapping routes every OpenAI standard
    voice slot to `es_ES-sharvard-medium` speaker F).
- Open WebUI `webui.db.audio.*` patched at D-1.7:
  - `audio.stt.engine = "openai"`,
    `audio.stt.openai.api_base_url =
    http://aurora-whisper-http:8000/v1`.
  - `audio.tts.engine = "openai"`,
    `audio.tts.openai.api_base_url =
    http://aurora-piper-http:8000/v1`,
    model `tts-1`, voice `alloy`.
  - Auto-playback default **off** per C-D-07
    (Open WebUI 0.8.10 has no backend auto-play; the
    shipped per-user frontend default is off).
- Chat-side Tool layer unchanged from Phase C:
  `time_now`, `rag_search`, `audit_search`,
  `ha_get_state`, `ha_call_service` attached to the
  `qwen2.5:7b-instruct` Model entry via
  `meta.toolIds`. `base_model_id = NULL` (D-35
  preserved).

### 4.3 Network edge

- **Two separate Cloudflare tunnels** in production:
  - `cloudflared` (Guardian Cloud) — on
    `cloudflare-net`. Hostnames
    `app.guardiancloud.app`,
    `api.guardiancloud.app`. **Untouched** through
    Phase D-1.
  - `cloudflared-amarolab` — on `ai-local_default`.
    Hostnames `ha.amarolab.es` (HA) and
    `ai.amarolab.es` (Open WebUI). Connector token
    persisted at `/home/diego/.secrets/cloudflared-amarolab.env`
    (mode `0600`, never in repo).
- HA reverse-proxy trust block in
  `configuration.yaml` trusts only the
  `172.18.0.0/16` Docker bridge subnet (the
  `cloudflared-amarolab` egress path) plus
  `127.0.0.1` and `::1`. LAN is intentionally **not**
  broadly trusted.

### 4.4 Operational invariants preserved through Phase D-1

- Guardian Cloud surface untouched at every gate
  (`cloudflared` `StartedAt` unchanged for
  23 h+ across the entire D-1.2 → G-D6 sequence).
- Mosquitto hardened posture (authenticated +
  per-user ACLs, default-deny) preserved through
  G-D5 (voice → MQTT round-trip) and G-D6.
- `switch.impresora_3d` voice-exposure = `false` at
  the close of every gate (exposed only for the
  duration of G-D5, reverted immediately afterwards).
- `input_boolean.aurora_voice_canary` is the only
  permanently voice-exposed entity.
- `qwen2.5:7b-instruct` Model entry: `base_model_id =
  NULL` (D-35), `meta.toolIds` unchanged from Phase C,
  `params.system` unchanged (3 342 chars / 822 tokens).
- No secret was rotated or printed during Phase D-1.

---

## 5. Closeout — exit criteria

Per [`../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md`](../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md)
the Phase D-1 exit criteria are the closure of all
six validation gates plus the restoration of
`switch.impresora_3d` to its baseline `off`.

| Criterion | Verdict | Evidence |
|---|---|---|
| G-D1 closed (both halves) | PASS | §2 ledger |
| G-D2 closed (both halves) | PASS | §2 ledger |
| G-D3 closed (both halves) | PASS | §2 ledger |
| G-D4 closed | PASS | §2 ledger |
| G-D5 closed | PASS (Write → Restore scope; query path proven by G-D4) | §2 ledger |
| G-D6 closed | PASS (one acceptance partial on HA TTS-failure log granularity, functional behaviour PASS) | §2 ledger |
| `switch.impresora_3d` restored to `off` baseline | PASS | G-D5 §3.1; G-D6 §1 / §5.B (final state `off`, `last_changed = 2026-06-17T23:03:50Z` per G-D6 pre-state, untouched through the entire G-D6 window) |
| `input_boolean.aurora_voice_canary` restored to `off` baseline | PASS | G-D6 §5.A (final `off`, `last_changed = 2026-06-18T00:29:45Z` from the REST `input_boolean.turn_off` reassertion post-§7.3 smoke) |
| Voice-exposure ACL = canary only at closeout | PASS | G-D6 §5.C |
| Guardian Cloud untouched | PASS | G-D6 §5.D |

**Phase D-1 — CLOSED.**

---

## 6. Decisions implicitly closed by Phase D-1

| Decision ID | Outcome |
|---|---|
| C-D-02 (Piper voice selection — Wyoming side) | Closed at D-1.3 — `es_ES-davefx-medium`. |
| C-D-05 (HA Assist pipeline timeouts) | Closed at D-1.5 / G-D4 — HA defaults accepted; latency measured (intent chat completions averaged ~3–6 s warm, with a documented cold-warmup outlier at G-D5); no tuning needed at this stage. |
| C-D-06 (Wyoming Piper container topology) | Closed at D-1.3. |
| C-D-07 (Open WebUI audio surface default for `qwen2.5`) | Closed at D-1.7 — STT engine `openai` → `aurora-whisper-http`; TTS engine `openai` → `aurora-piper-http`; auto-playback off (shipped default). |
| C-D-08 (HA TTS voice selection) | Closed at D-1.5 — speaker `F` of `es_ES-sharvard-medium` (pipeline slot). |
| C-D-09 (Open WebUI TTS shim image) | Closed at D-1.7 — `ghcr.io/matatonic/openedai-speech:0.18.2`, XTTS disabled. |
| HA-proxy-trust-deferred | Closed at the 2026-06-17 reverse-proxy trust apply log. |
| D-D1-HTTP (G-D1 HTTP-shim half deferred from D-1.2) | Closed at D-1.7. |

---

## 7. Carry-over follow-ups (post-Phase-D-1)

None of these are blockers. They are tracked here, in
[`../00_overview/CURRENT_STATE.md`](../00_overview/CURRENT_STATE.md)
and in [`../00_overview/ROADMAP.md`](../00_overview/ROADMAP.md).

| ID | Item | Notes |
|---|---|---|
| Performance | LLM 6 tok/s ceiling on UM790 CPU; ~89 % of warm-cycle voice latency. **Deferred to RTX 5070 AI-node bridge** ([`../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md`](../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md)). Voice-stack architecture is GPU-ready; only the `ollama` endpoint target changes. | From D-1.7 §4 |
| HA-VOICE-001 | `qwen2.5` intermittently fails to resolve "voice canary" via the HA Assist voice pipeline even though REST `/api/conversation/process` against the same `agent_id` resolves the same phrasing reliably; likely a frontend `ha-assist-chat` WS race. Workaround: refresh the HA tab. | From G-D6 §2.3 / §7 |
| HA TTS-failure log granularity | HA Assist does not write TTS failures to the INFO-level core container log; surfaces only on the WS `assist_pipeline/pipeline_debug` stream and the UI banner. Could be partially mitigated by raising HA's `wyoming` / `tts` log level to DEBUG if future post-mortems require it. | From G-D6 §3.2 |
| STT fidelity | `base-int8` produces sub-canonical Spanish on short utterances (examples since G-D4). Model-size bump candidate (`small` or `medium-int8`). | From G-D4 §3.3, G-D6 §2.3 |
| Streaming TTS in Open WebUI | OW does not stream STT/TTS today; first-token wait dominates perceived latency before the LLM acceleration lands. | From D-1.7 §4 / §8 |
| System prompt size | 3 342 chars / 822 tokens → 16.9 s cold KV cache eval per new conversation. Trim candidate, pair with RAG audit. | From D-1.7 §4 / §8 |
| `cloudflared-amarolab` standalone apply log | Deployment validated through D-1.5 / D-1.7 / G-D6 but no dedicated standalone apply log yet. | Documentation sync follow-up |
| DNS / Cloudflare architecture doc amendments | [`../02_infrastructure/cloudflare/amarolab_dns_architecture.md`](../02_infrastructure/cloudflare/amarolab_dns_architecture.md) and [`../02_infrastructure/cloudflare/cloudflared_audit_2026-06-17.md`](../02_infrastructure/cloudflare/cloudflared_audit_2026-06-17.md) still describe the "attach existing tunnel" plan; the shipped architecture is a separate `cloudflared-amarolab` tunnel + container with `ai.amarolab.es` bound at D-1.7. | Documentation sync follow-up |
| Open WebUI image size | `ghcr.io/matatonic/openedai-speech:0.18.2` is 11.4 GB because the published ghcr image bundles every TTS backend (XTTS, OpenVoice, Coqui-TTS, Piper). XTTS is disabled at runtime via `--xtts_device none`. A local rebuild of the project's minimal Piper-only image would shrink disk footprint. | Disk-only, no runtime cost |
| `ollama` 500 errors during D-1.7 validation | Four `POST /api/chat → 500` rows seen during the D-1.7 validation window alongside many 200s. Not a shim or audio fault; likely cancelled streams or context-window failures. | Stability follow-up |
| R-D-13 | Migrate the Open WebUI STT HTTP shim away from the unmaintained `fedirz/faster-whisper-server`. | Post-Phase-D maintenance |
| R-01 | Cloudflare Tunnel token rotation (existing Guardian-Cloud tunnel). | Independent of Phase D |
| G-D5 query exchanges | Voice Read / Verify exchanges against `switch.impresora_3d` were not spoken (G-D5 §2). Optional — query path independently proven against the canary by G-D4. | Optional |

---

## 8. What this log changed

- **Documentation only.**
- [`../00_overview/CURRENT_STATE.md`](../00_overview/CURRENT_STATE.md)
  — Phase D section, Voice stack section, Cloudflare
  section, Open WebUI audio surface block, Known
  pending items rewritten to reflect the validated
  state.
- [`../00_overview/AMAROLAB_HANDOFF.md`](../00_overview/AMAROLAB_HANDOFF.md)
  — Phase D status block, voice capability summary,
  security status block (added voice-exposure
  default-deny and G-D6 safety story), Current Goal
  block (Phase D-1 marked closed), Next Immediate
  Task block (no new phase started; post-D-1 follow-
  ups listed).
- [`../00_overview/ROADMAP.md`](../00_overview/ROADMAP.md)
  — Phase D section rewritten to a ledger of all six
  gates and all D-1 sub-steps; post-D-1 follow-ups
  listed as carry-overs (not new phases).
- Daily summary at
  [`./2026-06-18_daily_summary.md`](./2026-06-18_daily_summary.md)
  — extended with the additional 2026-06-18 work
  (G-D5, D-1.7, G-D6, D-1.9 closeout).

## 9. What this log did NOT change

- Any container, image, command, restart policy, bind
  mount, network attachment, or runtime configuration.
- Any HA configuration (`configuration.yaml`,
  `.storage/*`, Assist pipeline `AURORA v1`,
  conversation agent, Ollama integration, Wyoming
  integrations, voice-exposure ACL).
- The Wyoming voice-stack containers
  (`aurora-whisper`, `aurora-piper`,
  `aurora-wakeword`).
- The Open WebUI audio HTTP shims
  (`aurora-whisper-http`, `aurora-piper-http`).
- `ollama` container or model store.
- `webui.db` — schema, Tools, model rows, audio
  config, system prompt.
- Mosquitto config, users, ACLs (hardened posture
  preserved).
- Zigbee2MQTT config or device list.
- `cloudflared` (Guardian Cloud) — container, tunnel
  UUID, ingress, credentials, network attachment.
- `cloudflared-amarolab` — tunnel ingress, hostnames,
  runtime.
- Cloudflare DNS — no records created or modified.
- Restic repository — no new snapshot taken.
- No environment file (`ai-stack/.env`,
  `/home/diego/.secrets/*`) was modified. No secret
  was introduced, rotated, or printed.

---

## 10. Related documents

- [`./2026-06-17_phaseD_whisper_installed.md`](./2026-06-17_phaseD_whisper_installed.md)
  — D-1.2 apply log.
- [`./2026-06-17_phaseD_piper_installed.md`](./2026-06-17_phaseD_piper_installed.md)
  — D-1.3 apply log.
- [`./2026-06-17_phaseD_wakeword_installed.md`](./2026-06-17_phaseD_wakeword_installed.md)
  — D-1.4 apply log.
- [`./2026-06-17_phaseD_voice_pipeline.md`](./2026-06-17_phaseD_voice_pipeline.md)
  — D-1.5 apply log (AURORA v1 pipeline).
- [`./2026-06-17_phaseD_ha_trusted_proxies_applied.md`](./2026-06-17_phaseD_ha_trusted_proxies_applied.md)
  — HA reverse-proxy trust patch.
- [`./2026-06-17_phaseD_gate_gd4_applied.md`](./2026-06-17_phaseD_gate_gd4_applied.md)
  — G-D4 apply log (canary end-to-end).
- [`./2026-06-18_phaseD_gate_gd5_applied.md`](./2026-06-18_phaseD_gate_gd5_applied.md)
  — G-D5 apply log (real-device voice round-trip).
- [`./2026-06-18_phaseD_openwebui_audio_applied.md`](./2026-06-18_phaseD_openwebui_audio_applied.md)
  — D-1.7 apply log (Open WebUI Audio shims).
- [`./2026-06-18_phaseD_gate_gd6_applied.md`](./2026-06-18_phaseD_gate_gd6_applied.md)
  — G-D6 apply log (failure-mode rehearsal).
- [`../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md`](../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md)
  — gate definitions.
- [`../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md`](../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md)
  — performance-optimization deferral target.
- [`../03_services/voice-stack/README.md`](../03_services/voice-stack/README.md)
  — voice-stack reference architecture.
- [`../03_services/voice-stack/ha-assist/pipeline-spec.md`](../03_services/voice-stack/ha-assist/pipeline-spec.md)
  — `AURORA v1` pipeline spec.
- [`../07_operations/lessons_learned.md`](../07_operations/lessons_learned.md)
  — Lessons 002 / 005 / 010 / 013 / 015 underpin the
  validation rhythm of Phase D-1.
- [`./2026-06-15_phaseA_closeout.md`](./2026-06-15_phaseA_closeout.md),
  [`./2026-06-16_phaseB_closeout.md`](./2026-06-16_phaseB_closeout.md),
  [`./2026-06-17_phaseC_closeout.md`](./2026-06-17_phaseC_closeout.md)
  — prior phase closeouts (closure-pattern reference).

---

## 11. Stop point

Per the operator instruction at the start of the
session: **STOP after D-1.9 closeout.** No new phase
has been started. The post-D-1 carry-overs in §7 are
recorded but **not initiated**.
