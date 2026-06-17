# Phase D — Component Spec

- **Ecosystem:** **AMAROLAB** — Personal Innovation
  Lab and Digital Infrastructure Ecosystem.
- **Assistant:** **AURORA** — Personal AI Assistant
  for the AMAROLAB ecosystem.
- **Independent project on AMAROLAB infrastructure:**
  **Guardian Cloud** (out of scope; not modified by
  this work).
- **Status:** D-1.1 skeleton. Image tags, env values,
  resource caps captured as **decisions**. Exact
  `docker run` recipes land per component in
  [`../../../03_services/voice-stack/`](../../../03_services/voice-stack/)
  *before* any execution, per Lesson 005.

---

## 1. Common conventions

| Concern | Rule |
|---|---|
| Network | `ai-local_default` (existing). No host ports published. |
| Restart policy | `--restart unless-stopped` |
| Image pinning | Pinned tag only; **never** `:latest`. Pinned tag recorded in each component file. |
| Data persistence | Bind mounts under `/srv/homelab/data/<component>/`, mode `0755`, owner `diego`. |
| Logging | Container stdout/stderr; no extra log files unless the apply log enumerates them. |
| Healthchecks | TCP probe on the component's Wyoming port; HTTP `/health` where the image supports it. |
| Env loading | Following Lesson 001: env values are passed via `--env` or `-e` at container *create* time. Any env change requires container recreate, never a plain restart. |
| Naming | `aurora-<component>` (e.g. `aurora-whisper`, `aurora-piper`, `aurora-wakeword`) so the AURORA voice stack is visually grouped in `docker ps`. |

---

## 2. faster-whisper (STT)

| Field | Value |
|---|---|
| Container | `aurora-whisper` |
| Image (Wyoming) | `rhasspy/wyoming-whisper:3.2.0` *(C-D-01 closed at D-1.2, digest `sha256:966e1b…`)* |
| Image (HTTP shim) | `fedirz/faster-whisper-server:0.6.0-rc.3-cpu` *(pre-pulled at D-1.2, container deferred to D-1.7; digest `sha256:b9d671…`)* |
| Wyoming port | `10300/tcp` (internal, not host-published) |
| HTTP shim port | `8000/tcp` (internal) — created in D-1.7 |
| Model | `base-int8` *(C-D-04 closed at D-1.2 — RTF 0.055 on Ryzen 9 7940HS; no escalation to `small-int8` needed for D-1)* |
| Language | Auto-detect for D-1; pin during G-D5 prep |
| CPU cap | `--cpus 4` |
| Memory cap | `--memory 4g` |
| Bind mount (Wyoming) | `/srv/homelab/data/whisper/wyoming` → `/data` |
| Bind mount (HTTP) | `/srv/homelab/data/whisper/http` → cache (D-1.7) |
| Restart policy | `--restart unless-stopped` |
| CLI args (Wyoming, decided) | `--model base-int8 --language auto --beam-size 1 --compute-type int8` |
| Healthcheck | TCP probe on `10300`; HTTP `/health` on shim (D-1.7) |

Full deployment doc:
[`../../../03_services/voice-stack/whisper/faster-whisper-deployment.md`](../../../03_services/voice-stack/whisper/faster-whisper-deployment.md).

Apply log:
[`../../../09_logs/2026-06-17_phaseD_whisper_installed.md`](../../../09_logs/2026-06-17_phaseD_whisper_installed.md).

---

## 3. Piper (TTS)

| Field | Value |
|---|---|
| Container | `aurora-piper` |
| Image (Wyoming) | `rhasspy/wyoming-piper:<TBD pinned tag>` |
| HTTP shim | Built-in OpenAI-compatible mode on Wyoming image, or separate `:8001` shim (TBD at deploy time) |
| Wyoming port | `10200/tcp` (internal) |
| HTTP shim port | `8001/tcp` (internal) |
| Voice (primary) | `es_ES-davefx-medium` |
| Voice (secondary) | `en_US-libritts_r-medium` |
| CPU cap | `--cpus 1` |
| Memory cap | `--memory 1g` |
| Bind mount | `/srv/homelab/data/piper/` → voice files |
| Restart policy | `--restart unless-stopped` |
| Env (decided) | `PIPER_VOICE=es_ES-davefx-medium`, `PIPER_LENGTH_SCALE=1.0` |
| Healthcheck | TCP probe on `10200` |

Full deployment doc:
[`../../../03_services/voice-stack/piper/piper-deployment.md`](../../../03_services/voice-stack/piper/piper-deployment.md).

---

## 4. openWakeWord

| Field | Value |
|---|---|
| Container | `aurora-wakeword` |
| Image | `rhasspy/wyoming-openwakeword:<TBD pinned tag>` |
| Wyoming port | `10400/tcp` (internal) |
| Wake word (D-1) | `ok_nabu` (built-in; effectively unused in D-1 push-to-talk validation, deployed for plug-and-play with D-2 hardware satellites) |
| Wake word (D-2 candidate) | `hey_aurora` (custom — out of scope for D-1) |
| CPU cap | `--cpus 1` |
| Memory cap | `--memory 512m` |
| Restart policy | `--restart unless-stopped` |
| Env (decided) | `WAKEWORD_MODELS=ok_nabu`, `WAKEWORD_THRESHOLD=0.5` |
| Healthcheck | TCP probe on `10400` |

Full deployment doc:
[`../../../03_services/voice-stack/wakeword/openwakeword-deployment.md`](../../../03_services/voice-stack/wakeword/openwakeword-deployment.md).

---

## 5. Home Assistant Assist pipeline

| Field | Value |
|---|---|
| Pipeline name | `AURORA v1` |
| Default language | `es-ES` (revisit during G-D5 prep) |
| Wake word | `ok_nabu` via Wyoming openWakeWord (push-to-talk in D-1; always-on in D-2 with hardware satellite) |
| STT | Wyoming `aurora-whisper:10300` |
| Conversation agent | **HA Ollama integration** → `ollama:11434` → `qwen2.5:7b-instruct` |
| TTS | Wyoming `aurora-piper:10200`, voice `es_ES-davefx-medium` |
| Pipeline timeout | TBD — set during G-D5 prep after measuring qwen2.5 voice-prompt latency |
| Exposed entities (D-1) | `input_boolean.aurora_voice_canary` (G-D4), then `switch.impresora_3d` (G-D5) |

Full pipeline spec:
[`../../../03_services/voice-stack/ha-assist/pipeline-spec.md`](../../../03_services/voice-stack/ha-assist/pipeline-spec.md).

---

## 6. Open WebUI audio surface

| Field | Value |
|---|---|
| STT engine | OpenAI Whisper (HTTP) → `aurora-whisper-http:8000/v1` |
| STT model | `whisper-1` (shim-mapped) |
| TTS engine | OpenAI TTS (HTTP) → `aurora-piper-http:8001/v1` |
| TTS voice | `es_ES-davefx-medium` |
| Mic input | PC browser microphone (no new hardware) |
| Audio output | PC browser speaker (no new hardware) |
| Changes to chat path | **None.** Audio settings are additive. `qwen2.5` model row, `meta.toolIds`, and `params.system` are not modified. |

---

## 7. Phase D-1 voice satellite

| Field | Value |
|---|---|
| Hardware | Operator's workstation PC — existing mic + speakers. **No new hardware.** |
| Transport | Browser (HA UI Assist panel for voice; Open WebUI mic button for chat-with-voice). |
| Mode | Push-to-talk (click mic, speak, release). |
| Wake word | Not exercised end-to-end in D-1 (browser does not stream continuous audio). The openWakeWord container is deployed so D-2 hardware can plug in without re-architecture. |

Future hardware options enumerated in
[`../../../03_services/voice-stack/voice-satellites/hardware-options.md`](../../../03_services/voice-stack/voice-satellites/hardware-options.md).

---

## 8. What is **not** changed in Phase D

- `webui.db` schema, rows, or tools.
- `qwen2.5:7b-instruct` model row (`base_model_id`,
  `meta.toolIds`, `params.system` all unchanged).
- The `amarolab-audit.log` schema.
- Mosquitto config, users, or ACLs.
- Z2M configuration.
- Existing HA integrations (MQTT, Z2M discovery).
- Open WebUI Tool layer or the D-12 allowlist.
- Guardian Cloud — independent project hosted on
  AMAROLAB infrastructure; untouched by Phase D.

---

## 9. Open decisions tracked here

| ID | Decision | Closes at | Status |
|---|---|---|---|
| C-D-01 | Whisper image pinned tag | D-1.2 prep | **CLOSED 2026-06-17** — `rhasspy/wyoming-whisper:3.2.0` |
| C-D-02 | Piper image pinned tag | D-1.3 prep | open |
| C-D-03 | openWakeWord image pinned tag | D-1.4 prep | open |
| C-D-04 | Whisper model size after G-D1 latency | G-D1 | **CLOSED 2026-06-17** — `base-int8` (RTF 0.055) |
| C-D-05 | Pipeline timeout value | G-D5 prep | open |
| C-D-06 | Piper HTTP shim — built-in mode or separate container | D-1.3 | open |
| C-D-07 | Open WebUI audio surface enabled by default for `qwen2.5`? | D-1.7 | open |
| R-D-13 | Migrate HTTP shim off `fedirz/faster-whisper-server` (last build 2025-01-07) to a maintained successor | post-Phase-D maintenance | open |
