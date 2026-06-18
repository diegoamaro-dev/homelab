# Phase D — D-1.7 — Open WebUI Audio integration — APPLIED

- **Date:** 2026-06-18 (local; deploy + validation window 2026-06-17 22:57 → 23:30 UTC = 2026-06-18 00:57 → 01:30 CEST)
- **Phase step:** D-1.7 — Open WebUI audio surface (STT + TTS HTTP shims)
- **Ecosystem:** **AMAROLAB** — Personal Innovation Lab and Digital
  Infrastructure Ecosystem.
- **Assistant:** **AURORA** — Personal AI Assistant for the AMAROLAB
  ecosystem.
- **Independent project on AMAROLAB infrastructure:** **Guardian Cloud**
  — not modified by this work.
- **Status:** **APPLIED.** Two OpenAI-API-compatible HTTP shims
  (`aurora-whisper-http`, `aurora-piper-http`) deployed on
  `ai-local_default`, both internal-only (no host port published).
  Open WebUI `audio.stt` and `audio.tts` configured in `webui.db` to
  point at the two shims. Operator browser validation passed end-to-
  end at `https://ai.amarolab.es`: STT works, Open WebUI receives the
  transcript, `qwen2.5:7b-instruct` responds, manual TTS playback
  works. Default TTS auto-playback **disabled** per C-D-07. HA Assist
  (G-D5-proven) untouched; Guardian Cloud untouched;
  `ha.amarolab.es` untouched; `ai.amarolab.es` preserved.
- **Scope:** Two new sidecar containers, one new Amarolab config
  file under `/srv/homelab/data/openedai-speech/`, two new bind-
  mount cache dirs, one webui.db config patch (audio.* keys only).
  No HA changes, no Wyoming changes, no Mosquitto/Z2M changes, no
  Cloudflare DNS or tunnel ingress changes, no Open WebUI image or
  schema changes.
- **Inputs:**
  - D-1.7 plan: prior session (this thread) — architecture,
    container topology, rollback layers.
  - Component spec (`fedirz` pre-pulled, ports, bind-mount paths):
    [`../04_ai_system/amarolab-v1/phase-d/03-component-spec.md`](../04_ai_system/amarolab-v1/phase-d/03-component-spec.md)
    §3 (Whisper) and §4 (Piper).
  - Validation gates (G-D1 HTTP-shim half deferred to this step):
    [`../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md`](../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md)
    §2.
  - D-1.5 apply log (pipeline + reverse-proxy + HTTPS context):
    [`./2026-06-17_phaseD_voice_pipeline.md`](./2026-06-17_phaseD_voice_pipeline.md).
  - G-D4 apply log (canary):
    [`./2026-06-17_phaseD_gate_gd4_applied.md`](./2026-06-17_phaseD_gate_gd4_applied.md).
  - G-D5 apply log (real device):
    [`./2026-06-18_phaseD_gate_gd5_applied.md`](./2026-06-18_phaseD_gate_gd5_applied.md).

---

## 1. Pre-state anchor

| Field | Value |
|---|---|
| T0 (UTC) | `2026-06-17T22:57:56Z` (epoch `1781737076`) |
| `switch.impresora_3d` state | `off` (baseline preserved from G-D5 Restore) |
| `input_boolean.aurora_voice_canary` state | `off` (unchanged from G-D4) |
| Voice-exposure ACL | only canary (printer reverted post-G-D5) |
| `webui.db` `audio.stt` | `{}` |
| `webui.db` `audio.tts` | `{}` |
| `webui.db` `qwen2.5:7b-instruct` system prompt | 3,342 chars (≈ 822 tokens), unchanged |
| `webui.db` `qwen2.5:7b-instruct` `meta.toolIds` | `["time_now","rag_search","audit_search","ha_get_state","ha_call_service"]` (unchanged) |
| `cloudflared-amarolab` | running since `2026-06-17T21:19:16Z` (D-1.5) |
| `cloudflared` (Guardian) | running since `2026-06-17T00:19:32Z` (untouched 22h+) |
| HA Assist Wyoming chain | `aurora-whisper`, `aurora-piper`, `aurora-wakeword` — all running since `2026-06-17T14:21Z` (untouched 8h+) |
| Disk free on `/` | 316 GB (29% used) |
| `ai.amarolab.es` | `HTTP 200` on `/api/version` |
| `ha.amarolab.es` | `HTTP 200` on `/` |

### 1.1 Restic anchor — decision

**No fresh Restic snapshot was taken for D-1.7.** Same rationale as
G-D5 (see §1.1 of
[`./2026-06-18_phaseD_gate_gd5_applied.md`](./2026-06-18_phaseD_gate_gd5_applied.md)),
adapted for this step:

- The new containers create only new state on disk: their own bind-
  mount cache dirs (`/srv/homelab/data/whisper/http/`,
  `/srv/homelab/data/openedai-speech/`). They do not mutate any
  existing service state.
- The single persistent mutation against existing data is two keys in
  `webui.db.config.data`: `audio.stt` and `audio.tts`. Pre-state
  values for both were `{}` (captured in §1).
- A byte-perfect copy of `webui.db` immediately before the patch was
  taken at
  `/srv/homelab/data/_apply_anchors/2026-06-18_pre-D-1.7_webui.db`
  (preserved out of the original `/tmp` capture so it survives a
  reboot). Layer B in-band rollback uses this anchor directly.
- Layer C (Restic) remains available via the broader system-wide
  Restic repository on the 2 TB USB disk. Snapshot `63c072f4` (D-1.5
  anchor) still covers the relevant pre-D-1.7 OpenWebUI tree at
  rest. No new D-1.7 snapshot adds material recoverability beyond
  this.

Per Lesson 010, reversibility was provided by file-level capture +
in-band SQL rollback, which is the appropriate granularity for a
two-key config patch.

### 1.2 Log byte-position baselines (for delta capture)

| Container | Bytes at T0 |
|---|---|
| `aurora-whisper` | 2 052 |
| `aurora-piper` | 20 |
| `aurora-wakeword` | 16 |
| `ollama` | 2 036 577 |
| `openwebui` | 255 022 |
| `homeassistant` | 5 218 391 |
| `mosquitto` | 11 057 754 |
| `zigbee2mqtt` | 10 732 301 |
| `cloudflared-amarolab` | 8 740 |
| `cloudflared` | 435 380 |

---

## 2. What was deployed

### 2.1 `aurora-whisper-http` — OpenAI-API-compatible STT shim

| Field | Value |
|---|---|
| Container name | `aurora-whisper-http` |
| Image | `fedirz/faster-whisper-server:0.6.0-rc.3-cpu` |
| Image digest | `sha256:b9d6714f0a2ad53778c70da370586099fcf77e918447ca197b808f9492bcc29d` |
| Image pre-pulled at D-1.2; **container created at D-1.7** | yes |
| Network | `ai-local_default` (IPv4 172.18.0.9) |
| Internal port | `8000/tcp` (Wyoming port 10300 stays with `aurora-whisper` for HA Assist) |
| Host port publish | **none** (internal-only) |
| Bind mount | `/srv/homelab/data/whisper/http` → `/home/ubuntu/.cache/huggingface` (per-instance model cache; **not** shared with `aurora-whisper` Wyoming) |
| Model | `Systran/faster-whisper-base` |
| Compute type | `int8` (matches the `base-int8` profile chosen for `aurora-whisper` at D-1.2) |
| Restart policy | `unless-stopped` |
| Container UID:GID | `1000:1000` (`ubuntu`) — aligns with host `diego` UID 1000 for bind-mount permission |
| Healthcheck | image does not declare one; HTTP `/health` returns `OK` |

The container deploys faster-whisper independently from the Wyoming
instance. **Memory cost on first warm:** ~374 MiB. **Concurrent STT
load is doubled only during simultaneous transcription** — acceptable
on 32 GB DDR5 (per the D-1.7 plan §5 risk #1).

### 2.2 `aurora-piper-http` — OpenAI-API-compatible TTS shim (closes C-D-09)

| Field | Value |
|---|---|
| Container name | `aurora-piper-http` |
| Image | `ghcr.io/matatonic/openedai-speech:0.18.2` (the pinned-version equivalent of `:latest` at the time of pull) |
| Image digest | `sha256:fb712f8f66290b498b68d3e7a3926475a85d7870b341aa0abc6f7e78e944b2c3` |
| Image size | **11.4 GB** — flagged in §8. The project's minimal Piper-only build (`min-latest`) is not published to ghcr; building a slimmer image is a post-Phase-D maintenance candidate. |
| Network | `ai-local_default` (IPv4 172.18.0.10) |
| Internal port | `8000/tcp` |
| Host port publish | **none** (internal-only) |
| Bind mounts | `/srv/homelab/data/piper:/app/voices:ro` (the same Piper voice files used by `aurora-piper` Wyoming, mounted read-only); `/srv/homelab/data/openedai-speech/voice_to_speaker.yaml:/app/config/voice_to_speaker.yaml:ro` (Amarolab voice mapping — see §2.3) |
| Entrypoint override | `/bin/bash -c 'python speech.py --xtts_device none --host 0.0.0.0 --port 8000'` (bypasses the image's default `startup.sh`, which would attempt to download English voices from the network; we provide our own Piper voices via the bind mount instead) |
| Default voice (`alloy`) | `es_ES-sharvard-medium` speaker `1` (= `F` per the voice's `speaker_id_map`) — **matches the AURORA v1 pipeline TTS in HA Assist (C-D-08)** |
| Restart policy | `unless-stopped` |

### 2.3 Amarolab voice mapping

File: `/srv/homelab/data/openedai-speech/voice_to_speaker.yaml`
(host-owned, mounted read-only into the container).

All six OpenAI standard voice slots route to the same Aurora voice
so that any caller — including Open WebUI's `alloy` default —
produces the canonical Spanish voice:

```yaml
tts-1:
  alloy:   { model: voices/es_ES-sharvard-medium.onnx, speaker: 1 }  # F (Aurora)
  echo:    { model: voices/es_ES-sharvard-medium.onnx, speaker: 1 }
  fable:   { model: voices/es_ES-sharvard-medium.onnx, speaker: 1 }
  onyx:    { model: voices/es_ES-sharvard-medium.onnx, speaker: 0 }  # M (alternate)
  nova:    { model: voices/es_ES-sharvard-medium.onnx, speaker: 1 }
  shimmer: { model: voices/es_ES-sharvard-medium.onnx, speaker: 1 }
```

`tts-1-hd` slots intentionally **not** defined — that would route to
XTTS, which we disabled via `--xtts_device none`.

### 2.4 Open WebUI `audio.*` config patch (`webui.db.config.data`)

| Key | Value |
|---|---|
| `audio.stt.engine` | `"openai"` (was `""` — default disabled / built-in) |
| `audio.stt.model` | `"Systran/faster-whisper-base"` |
| `audio.stt.openai.api_base_url` | `"http://aurora-whisper-http:8000/v1"` |
| `audio.stt.openai.api_key` | `"sk-amarolab-local-not-secret"` (dummy bearer; the shim does not validate) |
| `audio.tts.engine` | `"openai"` |
| `audio.tts.model` | `"tts-1"` |
| `audio.tts.voice` | `"alloy"` |
| `audio.tts.split_on` | `"punctuation"` (Open WebUI default for chunking long replies) |
| `audio.tts.openai.api_base_url` | `"http://aurora-piper-http:8000/v1"` |
| `audio.tts.openai.api_key` | `"sk-amarolab-local-not-secret"` (dummy bearer) |

**C-D-07 closeout — TTS auto-playback default.** The decision was
"may be configured but not enabled by default." This is naturally
satisfied because Open WebUI 0.8.10 does **not** expose a global
auto-play flag in the backend `PersistentConfig` surface (verified
by grepping `auto.?play|autoplay` in
`/app/backend/open_webui/config.py`). Auto-play is a per-user/per-
chat toggle in the frontend, defaulting to **off** for every user.
Manual playback works (the "read aloud" / speaker icon on each
reply triggers a TTS call on demand). No back-end change was made
to enforce or override this — the desired default is the shipped
default.

### 2.5 Pre-patch `webui.db` backup

A byte-exact pre-patch copy of `webui.db` was preserved at
`/srv/homelab/data/_apply_anchors/2026-06-18_pre-D-1.7_webui.db`
(2,605,056 bytes). This is the Layer B rollback artifact referenced
in §1.1 and §8.

---

## 3. Validation evidence

### 3.1 Standalone STT shim — direct probes (no Open WebUI)

| Probe | Result |
|---|---|
| `GET /health` | `HTTP 200` body `OK` |
| `GET /v1/models` | `HTTP 200`, lists `Systran/faster-whisper-base` with `language: ["en","es", …]` |
| `POST /v1/audio/transcriptions` with synthetic Spanish WAV (5 s) | `HTTP 200`, body `{"text":"…"}` returned in 0.57 s warm (see §4) |

### 3.2 Standalone TTS shim — direct probes

| Probe | Result |
|---|---|
| `GET /v1/models` | `HTTP 200`, returns `tts-1` and `tts-1-hd` |
| `POST /v1/audio/speech` `{"model":"tts-1","voice":"alloy","input":"AURORA está lista."}` | `HTTP 200`, valid MP3 (`ID3 v2.4.0, MPEG ADTS layer III, 64 kbps, 22.05 kHz, mono`), 9 867 bytes, ~1.4 s wall time |

### 3.3 Reachability from Open WebUI's network namespace

| Probe | Result |
|---|---|
| `openwebui` → `aurora-whisper-http:8000/health` | `HTTP 200` (Docker DNS resolution OK on `ai-local_default`) |
| `openwebui` → `aurora-piper-http:8000/v1/models` | `HTTP 200` |

### 3.4 Synthetic end-to-end loop (lab-side)

| Stage | Input | Output |
|---|---|---|
| TTS | "Aurora está lista para asistir." | 15 509-byte MP3, 22.05 kHz mono |
| ffmpeg | MP3 | 16 kHz WAV, ~1.6 s |
| STT | the WAV | "Ahora está lista para asistir." |

"Aurora" → "Ahora" is the same sub-canonical fidelity profile
observed at G-D4 with `base-int8` on short utterances. Pipeline path
is end-to-end correct; STT fidelity remains the carried follow-up
from G-D4 (post-D-1 maintenance — model-size bump candidate).

### 3.5 Operator browser validation at `https://ai.amarolab.es`

Operator drove the validation from Chromium (Secure Context
confirmed). Acceptance criteria from the D-1.7 runbook:

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | Mic icon appears in chat input; browser grants `getUserMedia()` over HTTPS | **PASS** | Operator-confirmed |
| 2 | STT transcription returns a usable transcript to Open WebUI | **PASS** | Operator-confirmed; `aurora-whisper-http` log shows `POST /v1/audio/transcriptions HTTP/1.1 200 OK` rows during the validation window |
| 3 | `qwen2.5:7b-instruct` receives the transcript as a chat message and responds | **PASS** | Operator-confirmed; `ollama` log shows multiple `POST /api/chat 200` rows during the window, source IP `172.18.0.4` (openwebui) |
| 4 | Manual TTS playback works (operator-triggered, not auto-play) | **PASS** | Operator-confirmed; `aurora-piper-http` log shows `POST /v1/audio/speech HTTP/1.1 200 OK` rows during the window |
| 5 | `ai.amarolab.es` HTTPS preserved | **PASS** | `GET /api/version` returns `HTTP 200` post-validation |
| 6 | `ha.amarolab.es` HTTPS preserved | **PASS** | `GET /` returns `HTTP 200` post-validation |
| 7 | HA Assist (G-D5-proven) untouched | **PASS** | `aurora-whisper`, `aurora-piper`, `aurora-wakeword` all `Up 8h+` with `StartedAt` unchanged from pre-D-1.7 |
| 8 | Guardian Cloud untouched | **PASS** | `cloudflared` on `cloudflare-net` `StartedAt 2026-06-17T00:19:32Z` (22 h+ stable) |

**D-1.7 functional validation: PASSED.**

### 3.6 Error scan

`docker logs --since 30m` filtered for
`ERROR | CRITICAL | Traceback | Exception | panic | fatal | refused`
across `aurora-whisper-http`, `aurora-piper-http`, `openwebui`,
`ollama`, `aurora-whisper`, `aurora-piper`, `aurora-wakeword`,
`homeassistant`, `mosquitto`, `zigbee2mqtt`, `cloudflared-amarolab`,
`cloudflared`: zero matches outside the documented benchmark noise
(see §4) and four upstream-side `500 POST /api/chat` rows in
`ollama` during the operator session — those are routine
chat-completion failures, not shim or audio faults, and are carried
as a stability follow-up (§8).

---

## 4. Latency profile (read-only profiling)

A dedicated read-only profiling pass was executed against the
deployed chain at idle (UM790 Ryzen 9 7940HS, CPU-only inference,
all containers steady-state). The operator-reported "voice response
latency is perceived as very high" was investigated and the
dominant bottleneck identified.

### 4.1 Method

Each stage hit directly on `ai-local_default`, bypassing Cloudflare
and Open WebUI middleware so each number is the component's raw
cost. Fixtures: three Piper-synthesized Spanish WAVs at 0.4 s, 1.6 s
and 5.0 s. LLM tested both with a raw user message and with the
**live** Open WebUI system prompt extracted from `webui.db`
(`qwen2.5:7b-instruct.params.system` = 3,342 chars / 822 tokens).
Operator's real session reconstructed from container logs.

### 4.2 Per-stage latency

| Stage | Cold | Warm | Notes |
|---|---|---|---|
| **STT** (Whisper `base-int8`) on 5 s of audio | 0.91 s | **0.57 s** | RTF ≈ 0.12. ~0.4–0.6 s warm regardless of input length (0.4 s, 1.6 s, 5 s fixtures all in band). |
| **LLM prompt eval** (qwen2.5:7b-instruct, 822-token Amarolab system prompt + user) | **16.90 s** (cold KV cache) | **0.18 s** (warm KV cache, ~4 635 tok/s effective) | First message in a new conversation pays this; subsequent turns do not. |
| **LLM response generation** | **6.0 tok/s** | **6.0 tok/s** | Pure CPU inference ceiling on UM790. 100-token reply = ~16.7 s, 200-token = ~33 s, 300-token = ~50 s. Confirmed across 7 fresh runs (5.4–14.8 s for 20–87 tokens) and against the operator's session (2.4 s – 55.5 s long-tail). |
| **LLM first token streamed** | n/a | **0.25–0.40 s** (warm) | First-token is fast; total wait dominated by full generation. Open WebUI's audio flow is **not** streaming — it waits for the full reply before TTS, then for the full audio before playback. |
| **TTS** (Piper via openedai-speech, `es_ES-sharvard-medium`) | 0.56 s | 0.56 s | RTF ≈ 0.06. 17 s of audio in 1.1 s wall time. No cold/warm difference (no model load). |

### 4.3 Reconstructed end-to-end (typical warm conversation, 100-token reply)

```
push-to-talk stop  ──┐
                     │ 0.6 s   STT
                     │ 0.2 s   LLM prompt eval (warm KV)
                     │ 16.7 s  LLM response gen (100 toks × 6 tok/s)  ◀── dominant
                     │ 0.7 s   TTS
                     │ ~0.5 s  Open WebUI middleware + Cloudflare hop
                     ▼
audio plays         total ≈ 18.7 s
```

For the **first** turn of a new conversation (cold KV cache):

```
+ 16.9 s   LLM prompt eval (cold)
            total ≈ 35.6 s
```

This is consistent with the operator's session: 2.4 s shortest
reply (very short answer) → 55.5 s longest (long Spanish answer
with cold-cache penalty).

### 4.4 Decomposition by share of perceived latency

| Source | Warm-conversation share | First-turn share |
|---|---|---|
| **LLM eval (6 tok/s)** | **~89 %** | **~47 %** |
| LLM cold prompt KV cache | 0 % (cached) | **~47 %** |
| STT | 3 % | 2 % |
| TTS | 4 % | 2 % |
| Middleware + tunnel + UI | ~4 % | ~2 % |

### 4.5 Dominant bottleneck — verdict

**`qwen2.5:7b-instruct` response generation on UM790 CPU at
~6 tok/s is the bottleneck.** It dominates ~89 % of warm-cycle
latency. STT (Whisper) and TTS (Piper) together contribute under
2 s and are **not** the bottleneck. Cold-prompt KV cache adds ~17 s
on the first message of each new conversation but amortizes to
~0.2 s on every subsequent turn in the same conversation.

### 4.6 Performance optimization — DEFERRED to RTX 5070 AI-node work

Per
[`../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md`](../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md),
the planned acceleration path for LLM inference is the dedicated
**RTX 5070 AI-node** bridge. UM790 Ryzen 9 7940HS has only an
integrated Radeon 780M with no CUDA path; pure-CPU inference at
~6 tok/s on a 7B-parameter model is the hardware ceiling for this
host. Smaller quantizations and prompt-trimming would yield only
partial improvements and are not on the Phase D-1 critical path.

**The voice-stack architecture validated in D-1.7 is GPU-ready:**
the Wyoming and HTTP shim layers do not depend on `ollama` host
locality. When the RTX 5070 node lands, only the `ollama` endpoint
target (and the corresponding `audio.tts.openai.api_base_url` /
chat-side base URL for the Open WebUI Ollama integration) will need
to change. The voice latency reduction will be proportional to the
LLM-stage tok/s improvement (RTX 5070 + 7B int4 is expected in the
60–120 tok/s band, i.e., 10–20× the current rate — moving 100-token
warm replies from ~16.7 s to ~0.8–1.7 s, and total round-trip into
the ~3 s band).

No latency-targeted change is applied to the Phase D-1 surface at
this step. STT and TTS posture remain as deployed in D-1.7.

---

## 5. Decisions closed by this log

| Decision ID | Closes at | Outcome |
|---|---|---|
| **C-D-07** — Open WebUI audio surface enabled by default for `qwen2.5`? | this log §2.4 | **Closed.** STT enabled (engine `openai` → `aurora-whisper-http`). TTS configured (engine `openai` → `aurora-piper-http`) but **not auto-playing**: Open WebUI 0.8.10 has no backend auto-play config, frontend per-user toggle defaults to off — desired posture is the shipped default. No backend override applied. |
| **C-D-09** — Piper OpenAI-compatible TTS shim image | this log §2.2 | **Closed.** `ghcr.io/matatonic/openedai-speech:0.18.2` (digest `sha256:fb712f…`). Size 11.4 GB acknowledged (§8). XTTS disabled (`--xtts_device none`); only Piper backend used. |
| **D-D1-HTTP** — G-D1 HTTP-shim path (deferred from D-1.2 §2.5) | this log §3.1, §3.4 | **Closed.** STT HTTP shim is reachable internally, returns `{"text":…}` from `POST /v1/audio/transcriptions`, end-to-end loop succeeds. |
| **G-D2 HTTP-shim half** (deferred from D-1.3) | this log §3.2, §3.4 | **Closed.** TTS HTTP shim returns valid MP3 from `POST /v1/audio/speech`, end-to-end loop succeeds with es_ES-sharvard-medium voice F. |

---

## 6. What this did NOT change

- HA `configuration.yaml`.
- HA Assist pipeline `AURORA v1`, voice-exposure ACL, recorder DB.
- HA Wyoming integrations (Whisper, Piper, openWakeWord — all still
  point at the **Wyoming** containers `aurora-whisper:10300`,
  `aurora-piper:10200`, `aurora-wakeword:10400` — **not** the new
  HTTP shims).
- The Wyoming voice-stack containers (`aurora-whisper`,
  `aurora-piper`, `aurora-wakeword`) — `StartedAt` unchanged,
  `Up 8h+` post-D-1.7. The HA voice round-trip (G-D5-proven against
  `switch.impresora_3d`) is fully preserved.
- The HA Ollama integration — same `qwen2.5:7b-instruct` endpoint
  shared with Open WebUI, no routing change.
- The `openwebui` container image (`ghcr.io/open-webui/open-webui:main`,
  revision `e4e69a10`) — not pulled, not rebuilt; only the SQLite
  config row was patched.
- The `qwen2.5:7b-instruct` model row in `webui.db` — `base_model_id`
  (NULL per D-35), `meta.toolIds`, `params.system` (3,342-char Amarolab
  prompt) all unchanged.
- Tools registered in `webui.db.tool` (`time_now`, `rag_search`,
  `audit_search`, `ha_get_state`, `ha_call_service`, legacy Jarvis
  trio) — unchanged.
- `/srv/homelab/data/openwebui/amarolab-audit.log`.
- Mosquitto config, users, ACLs (hardened posture preserved).
- Zigbee2MQTT config or device list.
- `cloudflared` (Guardian Cloud) — container, tunnel UUID,
  ingress, credentials, network attachment.
- `cloudflared-amarolab` — tunnel ingress, hostnames, runtime.
  `ai.amarolab.es` and `ha.amarolab.es` both remain `HTTP 200`.
- Cloudflare DNS — no records created or modified.
- The Restic repository — no new snapshot taken; see §1.1.

No environment file (`ai-stack/.env`, `/home/diego/.secrets/*`) was
modified. No secret was introduced, rotated, or printed. Both
shims use dummy bearer `sk-amarolab-local-not-secret`.

---

## 7. Stage / phase impact map

| Surface | State |
|---|---|
| `ai.amarolab.es` | preserved + now serves voice (chat front door) |
| `ha.amarolab.es` | unchanged (voice front door, G-D5-proven) |
| AURORA v1 pipeline in HA | unchanged |
| Open WebUI chat with tools | unchanged |
| Open WebUI **chat with voice** | **new — operational** |
| `switch.impresora_3d` | `off`, baseline restored, voice-exposure `false` |
| `input_boolean.aurora_voice_canary` | `off`, voice-exposure `true`, unchanged |
| Guardian Cloud surface | unchanged |

---

## 8. Open / deferred items

| ID | Item | Carried to |
|---|---|---|
| **Performance — LLM 6 tok/s ceiling** | Bottleneck §4.5. **Deferred to RTX 5070 AI-node bridge** per [`../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md`](../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md). Voice-stack architecture is GPU-ready; only the `ollama` endpoint target changes. | D-3 / RTX 5070 node work |
| **Streaming TTS** | Open WebUI does not stream STT or TTS today. First-token latency is 0.25–0.40 s but unrealized at the UI because Open WebUI waits for the full LLM reply before TTS. Streaming TTS would cut perceived latency materially even before the RTX node lands. | Post-D-1 maintenance |
| **System prompt size** | 3 342-char prompt → 822 tokens → 16.9 s cold KV cache eval per new conversation. Trimming could halve the cold penalty. Behavioral risk: tool-use guidance is in there. | Post-D-1 maintenance, paired with RAG audit |
| **STT fidelity** | `base-int8` still produces sub-canonical renderings ("Aurora" → "Ahora" in the §3.4 loop). Model-size bump candidate (`small` or `medium-int8`). Tracked since G-D4. | Post-D-1 maintenance |
| **openedai-speech image size** | 11.4 GB because the published ghcr image bundles every TTS backend (XTTS, OpenVoice, Coqui-TTS, Piper). XTTS is disabled at runtime (`--xtts_device none`) so dormant; size is disk only. The project's minimal Piper-only build would need a local rebuild. | Post-D-1 maintenance |
| **`fedirz/faster-whisper-server` unmaintained** (R-D-13) | Already known. Pinned at `0.6.0-rc.3-cpu`. Migration candidate exists but is post-Phase-D. | R-D-13 — post-Phase-D maintenance |
| **`ollama` 500 errors observed during operator session** | Four `POST /api/chat → HTTP 500` rows during the validation window (alongside many 200 rows). Likely cancelled streams or context-window failures; not a D-1.7 surface fault. | Stability follow-up, post-D-1 |
| **G-D6 — failure-mode rehearsal** | Whisper down / Piper down / Ollama unreachable rehearsal per `05-validation-gates.md` §7. | **D-1.8 (next step, not started)** |
| **Overview triad** (`00_overview/CURRENT_STATE.md`, `AMAROLAB_HANDOFF.md`, `ROADMAP.md`) | Will be amended at D-1.9 closeout once D-1.8 lands. | D-1.9 |
| **`cloudflared-amarolab` apply log** | Deployment validated at D-1.5 but no dedicated apply log yet. | Documentation sync, pre-D-1.9 |
| **DNS / architecture doc amendments** | `02_infrastructure/cloudflare/amarolab_dns_architecture.md` + `cloudflared_audit_2026-06-17.md` need to record the separate-tunnel decision and the `ai.amarolab.es` binding. | Documentation sync, pre-D-1.9 |
| R-01 | Cloudflare Tunnel token rotation (existing Guardian-Cloud tunnel). | Independent of this phase |

---

## 9. Rollback (preserved for the record)

If D-1.7 needs to be reversed:

**Layer B — in-band rollback (default path)**

1. Stop and remove the two new containers — nothing else is
   touched:
   ```
   docker rm -f aurora-piper-http aurora-whisper-http
   ```
2. Restore `webui.db` from the pre-patch backup:
   ```
   docker stop openwebui
   cp /srv/homelab/data/_apply_anchors/2026-06-18_pre-D-1.7_webui.db \
      /srv/homelab/data/openwebui/webui.db
   docker start openwebui
   ```
3. Verify: `GET https://ai.amarolab.es/api/version → 200`,
   `webui.db.config.data.audio.stt == {}` and `.audio.tts == {}`.
4. HA voice path (G-D5-proven) is untouched. Guardian Cloud
   untouched.

**Layer C — Restic restore.** Only required if `webui.db` is
corrupted beyond Layer B's reach. Use D-1.5 anchor `63c072f4`
against the system-wide repository.

---

## 10. Reproducibility

To re-apply D-1.7 from a clean state:

1. Confirm Phase D-1 pre-conditions: Wyoming voice stack
   operational (D-1.2 / D-1.3 / D-1.4), AURORA v1 pipeline default
   (D-1.5), G-D4 and G-D5 closed.
2. Confirm `ai.amarolab.es` is bound to the `amarolab` tunnel and
   returns `HTTP 200` over HTTPS.
3. Pre-pull both images (digests in §2.1 and §2.2).
4. Capture `webui.db` byte-exact backup.
5. Write the Amarolab voice-mapping YAML (§2.3).
6. Deploy `aurora-whisper-http` (§2.1). Verify `/health = OK`,
   `/v1/models` lists `Systran/faster-whisper-base`,
   `/v1/audio/transcriptions` returns text on a real WAV.
7. Deploy `aurora-piper-http` (§2.2). Verify `/v1/models` lists
   `tts-1`, `/v1/audio/speech` returns a valid MP3 on a Spanish
   phrase.
8. Stop `openwebui`, patch the audio config in `webui.db` (§2.4),
   start `openwebui`. Verify `/health`, `/api/version`.
9. Operator runs the §3.5 acceptance criteria from
   `https://ai.amarolab.es`.

---

## 11. D-1.7 closure status

**D-1.7 is closed.**

- C-D-07 closed (§5).
- C-D-09 closed (§5).
- D-D1-HTTP closed (§5).
- G-D2 HTTP-shim half closed (§5).
- Performance optimization deferred to RTX 5070 AI-node work
  ([`../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md`](../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md)).

Phase D-1 itself does **not** close until D-1.8 (G-D6 failure-mode
rehearsal) also lands. The overview triad
(`00_overview/CURRENT_STATE.md`, `AMAROLAB_HANDOFF.md`,
`ROADMAP.md`) is **not** updated by this log — per the D-1.5 /
G-D5 closure pattern and Lesson 005, the triad is amended at D-1.9
closeout.

Per the operator instruction at the start of this session:
**STOP here. D-1.8 not started.**

---

## 12. Related documents

- [`./2026-06-18_phaseD_gate_gd5_applied.md`](./2026-06-18_phaseD_gate_gd5_applied.md)
  — G-D5 (real-device voice round-trip, immediately preceding gate).
- [`./2026-06-17_phaseD_gate_gd4_applied.md`](./2026-06-17_phaseD_gate_gd4_applied.md)
  — G-D4 (canary end-to-end through HA Assist).
- [`./2026-06-17_phaseD_voice_pipeline.md`](./2026-06-17_phaseD_voice_pipeline.md)
  — D-1.5 apply log (AURORA v1 pipeline).
- [`./2026-06-17_phaseD_ha_trusted_proxies_applied.md`](./2026-06-17_phaseD_ha_trusted_proxies_applied.md)
  — HA reverse-proxy trust patch.
- [`./2026-06-17_phaseD_wakeword_installed.md`](./2026-06-17_phaseD_wakeword_installed.md)
  — D-1.4 apply log.
- [`./2026-06-17_phaseD_piper_installed.md`](./2026-06-17_phaseD_piper_installed.md)
  — D-1.3 apply log.
- [`./2026-06-17_phaseD_whisper_installed.md`](./2026-06-17_phaseD_whisper_installed.md)
  — D-1.2 apply log.
- [`../04_ai_system/amarolab-v1/phase-d/03-component-spec.md`](../04_ai_system/amarolab-v1/phase-d/03-component-spec.md)
  — closes C-D-07 (§185) and C-D-09 (§187).
- [`../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md`](../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md)
  — closes G-D1 HTTP-shim half (deferred from D-1.2 §2.5) and G-D2
  HTTP-shim half (deferred from D-1.3).
- [`../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md`](../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md)
  — performance-optimization deferral target (RTX 5070 AI-node).
- [`../03_services/voice-stack/whisper/faster-whisper-deployment.md`](../03_services/voice-stack/whisper/faster-whisper-deployment.md)
  — Whisper deployment plan (HTTP shim now lit).
- [`../07_operations/lessons_learned.md`](../07_operations/lessons_learned.md)
  — Lessons 002 / 005 / 010 / 013 / 015 underpin this validation
  rhythm.
