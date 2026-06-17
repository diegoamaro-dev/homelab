# Phase D — D-1.2 — Whisper standup — APPLIED

- **Date:** 2026-06-17
- **Phase step:** D-1.2 (Whisper standup)
- **Ecosystem:** **AMAROLAB** — Personal Innovation Lab
  and Digital Infrastructure Ecosystem.
- **Assistant:** **AURORA** — Personal AI Assistant
  for the AMAROLAB ecosystem.
- **Independent project on AMAROLAB infrastructure:**
  **Guardian Cloud** — not modified by this work.
- **Status:** **APPLIED.** `aurora-whisper` (Wyoming
  STT) deployed on UM790 against `ai-local_default`.
  Gate **G-D1 (Wyoming path)** validated end-to-end:
  WER = 0.000 against the canonical openai/whisper
  smoke-test clip (`jfk.flac`, 11.00 s), total latency
  609 ms, real-time factor 0.055. The HTTP-shim path
  of G-D1 is **deferred to D-1.7** (Open WebUI Audio
  integration) — no consumer exists for the shim until
  then; image is pre-pulled.
- **Scope:** Whisper container only. No Piper, no
  openWakeWord, no HA Assist configuration. No
  changes to `webui.db`, `qwen2.5`, the Tool layer,
  Mosquitto, Zigbee2MQTT, Home Assistant, Open WebUI,
  or Ollama. Pre/post md5 of `webui.db` and
  `amarolab-audit.log` unchanged.
- **Inputs:**
  - Phase D target architecture:
    [`../04_ai_system/amarolab-v1/phase-d/02-target-architecture.md`](../04_ai_system/amarolab-v1/phase-d/02-target-architecture.md)
  - Component spec:
    [`../04_ai_system/amarolab-v1/phase-d/03-component-spec.md`](../04_ai_system/amarolab-v1/phase-d/03-component-spec.md)
  - Validation gates:
    [`../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md`](../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md)
  - Whisper deployment plan:
    [`../03_services/voice-stack/whisper/faster-whisper-deployment.md`](../03_services/voice-stack/whisper/faster-whisper-deployment.md)

---

## 1. What was installed

### 1.1 Container

| Field | Value |
|---|---|
| Container name | `aurora-whisper` |
| Container ID | `7e5968b28ab4` |
| Image | `rhasspy/wyoming-whisper:3.2.0` |
| Image digest | `sha256:966e1b0967f398b81fa2273a96b2b940004fa1b77754f9ffda6b5689a58dd158` |
| Network | `ai-local_default` |
| Container IP | `172.18.0.5` |
| Wyoming port | `10300/tcp` (internal; **not** published to host) |
| Restart policy | `unless-stopped` |
| Resource caps | `--cpus 4 --memory 4g` |
| Bind mount | `/srv/homelab/data/whisper/wyoming` → `/data` |
| Model | `base-int8` (rhasspy/faster-whisper-base-int8 from HF) |
| Language | auto-detect |
| Beam size | `1` |
| Compute type | `int8` |
| User inside container | root (uid 0) |
| Ready signal | `INFO:__main__:Ready` at t+2 s after `docker run` |

### 1.2 Exact `docker run` command executed

```bash
docker run -d --name aurora-whisper --restart unless-stopped \
  --network ai-local_default \
  -v /srv/homelab/data/whisper/wyoming:/data \
  --cpus 4 --memory 4g \
  rhasspy/wyoming-whisper:3.2.0 \
  --model base-int8 \
  --language auto \
  --beam-size 1 \
  --compute-type int8
```

CLI args after the image are forwarded by the image's
`/usr/src/docker_run.sh` entrypoint, which prepends
`--uri tcp://0.0.0.0:10300 --data-dir /data`.

### 1.3 Bind-mount preparation

```bash
mkdir -p /srv/homelab/data/whisper/wyoming
chmod 755 /srv/homelab/data/whisper /srv/homelab/data/whisper/wyoming
```

Owner: `diego:diego`. The container runs as root and
writes the model cache (76 MB after first start) into
`models--rhasspy--faster-whisper-base-int8/` under
this directory.

### 1.4 Image selection rationale

| Image | Why pinned this version |
|---|---|
| `rhasspy/wyoming-whisper:3.2.0` | Latest stable release (Docker Hub `last_updated=2026-06-15`). Clean semver tag. Official Rhasspy / Home Assistant ecosystem image. |
| `fedirz/faster-whisper-server:0.6.0-rc.3-cpu` | Pre-pulled (digest `sha256:b9d671…`) for D-1.7. **Container not created in D-1.2.** Last build 2025-01-07 — staleness flagged; the successor project `speaches-ai/speaches` only ships SHA-tagged images (no semver), so fedirz remains the cleanest semver-pinned OpenAI-compatible option for now. Migration to a maintained successor is a tracked decision (see §6). |

---

## 2. Validation — Gate G-D1

Spec:
[`../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md`](../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md)
§2.

### 2.1 Reference audio

| Field | Value |
|---|---|
| Source | `openai/whisper/tests/jfk.flac` (canonical Whisper smoke-test clip) |
| URL | `https://github.com/openai/whisper/raw/main/tests/jfk.flac` |
| sha256 | `63a4b1e4c1dc655ac70961ffbf518acd249df237e5a0152faae9a4a836949715` |
| Format (source) | FLAC, 44 100 Hz, mono, 11.00 s |
| Format (sent to Whisper) | PCM 16 000 Hz mono 16-bit (downsampled in-probe via integer-stride decimation) |

Ground-truth text used for WER scoring:

> and so my fellow americans ask not what your
> country can do for you ask what you can do for
> your country

### 2.2 Describe probe (Wyoming info)

```
>>> describe probe
   model name=base-int8 languages_count=100
```

Confirms the loaded model is `base-int8` and exposes
100 ASR language codes.

### 2.3 Transcribe probe (Wyoming)

```
>>> transcribe probe
   transcript: ' And so my fellow Americans ask not what
                 your country can do for you,  ask what
                 you can do for your country.'
   expected  : 'and so my fellow americans ask not what
                your country can do for you ask what
                you can do for your country'
   wer       : 0.000
   latency_send_ms   : 1
   latency_total_ms  : 609
   audio_duration_ms : 11000
   realtime_factor   : 0.055
```

- **Word Error Rate: 0.000** (perfect match after
  case-insensitive, punctuation-stripped
  normalisation).
- **Total round-trip latency: 609 ms** for an 11 s
  audio clip.
- **Real-time factor: 0.055** — `base-int8` on
  UM790 (Ryzen 9 7940HS, CPU-only, 4 cores) is
  ~18× faster than real time on this clip.

### 2.4 Probe harness

The harness is a one-off Python script running inside
a transient `python:3.12-slim` container on
`ai-local_default` so the TCP target
`tcp://aurora-whisper:10300` resolves via Docker DNS.
Dependencies pinned at probe time:

| Package | Version | Why |
|---|---|---|
| `wyoming` | `>=1.5,<2` | Wyoming protocol client (`AsyncTcpClient`, `Transcribe`, `AudioStart/Chunk/Stop`, `Transcript`, `Describe`/`Info`) |
| `soundfile` | latest | FLAC decoding without host-side `ffmpeg` |
| `numpy` | latest | resampling 44 100 Hz → 16 000 Hz |
| `libsndfile1` (apt) | latest | required by `soundfile` |

Harness file:
`/tmp/aurora-gd1-20260617022735/wyoming_probe.py`
(kept on host for reproducibility within this
session; not added to the repo).

### 2.5 HTTP-shim path of G-D1

**Deferred to D-1.7.** Rationale:

- D-1.2 (per
  [`../04_ai_system/amarolab-v1/05-implementation-roadmap.md`](../04_ai_system/amarolab-v1/05-implementation-roadmap.md))
  names only `rhasspy/wyoming-whisper`.
- The HTTP shim has no consumer until D-1.7 (Open
  WebUI Audio integration).
- The shim image
  (`fedirz/faster-whisper-server:0.6.0-rc.3-cpu`,
  digest `sha256:b9d671…`) is pre-pulled and stored
  locally, so D-1.7 has no pull-time blocker.
- G-D1 status is therefore **partial — Wyoming path
  validated; HTTP path deferred to D-1.7.** Phase
  D-1 closeout will only be possible once the
  deferred path is exercised.

---

## 3. Pre / post state evidence

### 3.1 Pre-state

| Item | Value |
|---|---|
| Snapshot dir | `/tmp/aurora-whisper-pre-20260617022217` |
| `docker ps -a` snapshot | written to snapshot dir |
| `webui.db` md5 | `ce0884d7e0c8cf40cc81adcbef62fe88` |
| `amarolab-audit.log` md5 | `50dda5f5a464538753b8738d41515a1f` |
| `aurora-*` containers | none |
| `ai-local_default` reachable | yes, 3 containers attached |

### 3.2 Post-state

| Item | Value |
|---|---|
| `docker ps` | adds `aurora-whisper Up 2 minutes`; all 10 prior containers unchanged |
| `webui.db` md5 | `ce0884d7e0c8cf40cc81adcbef62fe88` — **unchanged** |
| `amarolab-audit.log` md5 | `50dda5f5a464538753b8738d41515a1f` — **unchanged** |
| Bind-mount disk usage | 76 MB (3 model blobs cached) |
| Open WebUI | healthy |
| Home Assistant | running (unchanged) |
| Mosquitto | running (hardened posture from 2026-06-17 unchanged) |
| Zigbee2MQTT | running (unchanged) |
| Ollama | running (unchanged) |
| Qdrant | running (unchanged) |
| Guardian Cloud (`guardian-web`) | running (untouched) |

---

## 4. What this did NOT change

- `webui.db` schema, rows, or any Tool.
- `qwen2.5:7b-instruct` model row (`base_model_id`,
  `meta.toolIds`, `params.system` — all unchanged).
- `/srv/homelab/data/openwebui/amarolab-audit.log`
  (no audit lines emitted).
- Mosquitto config, users, ACLs.
- Z2M configuration or device list.
- Existing HA integrations (MQTT, Z2M discovery).
- Open WebUI configuration (no Audio settings touched).
- Cloudflared tunnel.
- Guardian Cloud (`guardian-web`).

No environment file (`ai-stack/.env`) was modified.
No secrets were introduced or printed. No host port
is published by `aurora-whisper`.

---

## 5. Decisions closed by this log

| Decision ID | Closes at | Outcome |
|---|---|---|
| C-D-01 (Whisper Wyoming image pinned tag) | this log | `rhasspy/wyoming-whisper:3.2.0` |
| C-D-04 (Whisper model size after G-D1 latency) | this log | `base-int8` confirmed adequate — RTF 0.055 on 7940HS CPU; no need to escalate to `small-int8` for D-1 |

The component-spec doc
[`../04_ai_system/amarolab-v1/phase-d/03-component-spec.md`](../04_ai_system/amarolab-v1/phase-d/03-component-spec.md)
is updated alongside this log to reflect both closures
and the HTTP-shim pre-pull status.

---

## 6. Open / deferred items

| ID | Item | Carried to |
|---|---|---|
| C-D-02 | Piper image tag | D-1.3 |
| C-D-03 | openWakeWord image tag | D-1.4 |
| C-D-05 | HA Assist pipeline timeout | D-1.5 / G-D5 prep |
| C-D-06 | Piper HTTP-shim mode | D-1.3 |
| C-D-07 | Open WebUI Audio surface default for `qwen2.5` | D-1.7 |
| **(new)** D-D1-HTTP | HTTP-shim path of G-D1 | D-1.7 |
| **(new)** R-D-13 | Migrate the HTTP shim from `fedirz/faster-whisper-server:0.6.0-rc.3-cpu` to a maintained successor (`speaches-ai/speaches` if/when it adopts semver, or another OpenAI-compatible alternative). Currently stale (last build 2025-01-07). | post-Phase-D maintenance |

---

## 7. Reproducibility

The exact `docker run` command (§1.2), the
bind-mount preparation (§1.3), and the Wyoming probe
harness (§2.4) are sufficient to reproduce this
result on the same UM790 host. Image digests
recorded in §1.1 anchor the binary identity.

---

## 8. Stop point

Per the user instruction, D-1.2 stops here. No
work has begun on:

- D-1.3 (Piper)
- D-1.4 (openWakeWord)
- D-1.5 (HA Assist pipeline)
- D-1.6 (real-device end-to-end / G-D5)
- D-1.7 (Open WebUI Audio integration)

The overview triad
(`00_overview/CURRENT_STATE.md`,
`AMAROLAB_HANDOFF.md`, `ROADMAP.md`) will be
updated at Phase D-1 closeout (D-1.9), not now —
per Lesson 005 ("harden then document" — overview
docs reflect the closed phase, not intermediate
milestones).
