# Phase D — D-1.4 — openWakeWord standup — APPLIED

- **Date:** 2026-06-17
- **Phase step:** D-1.4 (openWakeWord standup)
- **Ecosystem:** **AMAROLAB** — Personal Innovation Lab
  and Digital Infrastructure Ecosystem.
- **Assistant:** **AURORA** — Personal AI Assistant for
  the AMAROLAB ecosystem.
- **Independent project on AMAROLAB infrastructure:**
  **Guardian Cloud** — not modified by this work.
- **Status:** **APPLIED.** `aurora-wakeword` (Wyoming
  wake-word detector) deployed on UM790 against
  `ai-local_default`. Gate **G-D3 — container/probe
  half** validated end-to-end: Wyoming `Describe`
  probe confirms the `openwakeword` program is
  installed and advertises `okay_nabu` (plus four
  other built-ins); a synthetic-detection probe
  streaming an operator-recorded 2.539 s WAV of
  "Okay Nabu" elicited a `Detection(name="okay_nabu",
  timestamp=2010)` Wyoming event from the server,
  with zero errors in `aurora-wakeword` container
  logs. The **HA-UI half of G-D3** (HA Settings →
  Voice assistants lists openWakeWord; `okay_nabu`
  selectable in pipeline editor) is **deferred to
  D-1.5** by approved scope split. C-D-03 is closed
  by this log.
- **Scope:** openWakeWord container only. No HA
  Wyoming integration wiring (D-1.5), no HA Assist
  pipeline configuration (D-1.5), no Open WebUI
  Audio settings (D-1.7), no changes to `webui.db`
  schema, `webui.db.tool` rows,
  `qwen2.5:7b-instruct` model row, the Tool layer,
  the D-12 allowlist, Mosquitto, Zigbee2MQTT, Home
  Assistant, Open WebUI configuration, Ollama,
  Qdrant, or Guardian Cloud.
- **Inputs:**
  - Phase D component spec:
    [`../04_ai_system/amarolab-v1/phase-d/03-component-spec.md`](../04_ai_system/amarolab-v1/phase-d/03-component-spec.md)
  - Validation gates:
    [`../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md`](../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md)
  - openWakeWord deployment plan:
    [`../03_services/voice-stack/wakeword/openwakeword-deployment.md`](../03_services/voice-stack/wakeword/openwakeword-deployment.md)
  - D-1.3 apply log (template followed):
    [`./2026-06-17_phaseD_piper_installed.md`](./2026-06-17_phaseD_piper_installed.md)

---

## 1. What was installed

### 1.1 Container

| Field | Value |
|---|---|
| Container name | `aurora-wakeword` |
| Container ID | `ce6d849c3367` |
| Image | `rhasspy/wyoming-openwakeword:2.1.0` |
| Image digest (local manifest) | `sha256:52cb1168731a1849fc28cf339c935fde58746bbabc94226668a40ef6ddf5d42b` |
| Docker Hub `last_updated` | `2025-10-28T15:14:47Z` (`:latest` aliased to same image) |
| Network | `ai-local_default` |
| Container IP | `172.18.0.7` |
| Wyoming port | `10400/tcp` (internal; **not** published to host). Matches the image `EXPOSE` directive — verified from `docker inspect .Config.ExposedPorts`. |
| Host port bindings | `{}` — no host port published (mirrors `aurora-whisper` / `aurora-piper` posture) |
| Restart policy | `unless-stopped` |
| Resource caps | `--cpus 1 --memory 512m` (`NanoCpus=1000000000`, `Memory=536870912`) |
| Bind mount | `/srv/homelab/data/wakeword` → `/custom_models` (rw). See §1.4 for mount-semantics rationale. |
| Threshold (CLI flag) | `0.5` (the published model default; passed explicitly for documentation clarity) |
| Trigger-level (CLI flag) | `1` (default; minimum; one above-threshold frame triggers detection) |
| User inside container | root (uid 0) |
| Ready signal | `INFO:root:Ready` (note: logger name is `root`, not `__main__` as in D-1.2 / D-1.3 — a minor module-logger-name difference recorded here so future operators don't grep for the wrong string) |

### 1.2 Exact `docker run` command executed

```bash
docker run -d --name aurora-wakeword --restart unless-stopped \
  --network ai-local_default \
  -v /srv/homelab/data/wakeword:/custom_models \
  --cpus 1 --memory 512m \
  rhasspy/wyoming-openwakeword:2.1.0 \
  --custom-model-dir /custom_models \
  --threshold 0.5 \
  --trigger-level 1
```

CLI args after the image are forwarded by the image's
`/usr/src/docker_run.sh` entrypoint, which prepends
`--uri tcp://0.0.0.0:10400` and then runs
`.venv/bin/python3 -m wyoming_openwakeword "$@"`. The
`WAKEWORD_*` env-var formulation in the original
deployment-doc skeleton is **not** what the image
consumes; the image takes equivalent settings as CLI
flags only, and this log records what was actually
executed (per Lesson 003 — reality wins). The
component-spec decision table is updated alongside
this log to reflect that configuration is by CLI
flag, mirroring the D-1.3 finding about
`rhasspy/wyoming-piper` and `PIPER_*` env vars.

### 1.3 Bind-mount preparation

```bash
mkdir -p /srv/homelab/data/wakeword
chmod 755 /srv/homelab/data/wakeword
```

Owner: `diego:diego`. The container runs as root and
would write any custom wake-word `.tflite` files
discovered under this directory; in D-1 the directory
is empty (no custom models). A `gd3/` subfolder was
created prior to the synthetic-detection probe and
holds the operator-recorded canary WAV produced
in §2.4.

Post-state bind-mount disk usage: **88 KB total**
(≈ 84 KB for `gd3/okay_nabu_canary.wav`, plus
filesystem overhead). The container itself wrote
**nothing** to the bind mount — it only reads
`*.tflite` from `--custom-model-dir` at startup and
on the per-connection model load, and there were no
custom `.tflite` files for it to load in D-1.

### 1.4 Mount-semantics rationale — `/custom_models`, not `/data`

Unlike `rhasspy/wyoming-whisper:3.2.0` and
`rhasspy/wyoming-piper:2.2.2` (both of which expose
`--data-dir /data` and use the mount as a model/voice
cache), `rhasspy/wyoming-openwakeword:2.1.0` ships
all built-in models inside the image read-only and
has **no `--data-dir`-equivalent flag**. The only
persistence knob is `--custom-model-dir`, which the
container scans at startup and on `Describe` /
`Detect` requests for additional user-supplied
wake-word `.tflite` files. Mounting at
`/custom_models` makes the semantic role of the
mount visible at `docker inspect` time and is
forward-compatible with the planned D-2 `hey_aurora`
custom model — a future operator can `cp
hey_aurora.tflite /srv/homelab/data/wakeword/` and
the running container will discover it on the next
`Describe` cycle without a redeploy.

### 1.5 Image selection rationale

| Image | Why pinned this version |
|---|---|
| `rhasspy/wyoming-openwakeword:2.1.0` | Latest stable semver tag (Docker Hub `last_updated=2025-10-28T15:14:47Z`). Same SHA as `:latest` (`sha256:52cb1168…`) — confirming the maintainers point `:latest` at this revision. Clean semver, official Rhasspy / Home Assistant ecosystem image. Successor of `2.0.0` (2025-10-14); the `1.x` lineage (last `1.10.0`, 2024-02-18) is retired. Same selection pattern used at D-1.2 (Whisper 3.2.0) and D-1.3 (Piper 2.2.2). |

**C-D-03 is closed by this selection.**

Note on digest reporting: the Docker Hub API
per-architecture `images[].digest` field reported
`sha256:271ff3b…` for the amd64 entry, whereas the
local `docker pull` resolved the RepoDigest to
`sha256:52cb1168…`. These are the registry-index
manifest digest vs. the image manifest digest
respectively; the authoritative anchor for D-1.4 is
the local `docker inspect`-confirmed RepoDigest
`sha256:52cb1168731a1849fc28cf339c935fde58746bbabc94226668a40ef6ddf5d42b`,
recorded in §1.1.

### 1.6 Image-reality inspection (pre-`docker run`)

The image was inspected via three read-only probes
before the recipe was settled, mirroring the D-1.3
"reality wins" pattern. Findings:

1. **Entrypoint:** `bash docker_run.sh` →
   `cd /usr/src && .venv/bin/python3 -m wyoming_openwakeword --uri 'tcp://0.0.0.0:10400' "$@"`.
2. **Env vars:** none consumed by the image
   (`Config.Env=[PATH=...]` only). The original
   deployment-doc skeleton's `WAKEWORD_MODELS=ok_nabu`
   / `WAKEWORD_THRESHOLD=0.5` formulation does **not**
   apply — these are CLI flags on this image, not
   env vars.
3. **CLI flags exposed by `python -m wyoming_openwakeword --help`:**
   `--uri`, `--custom-model-dir`, `--threshold`,
   `--trigger-level`, `--refractory-seconds`,
   `--zeroconf`, `--debug`, `--log-format`,
   `--version`. The flags `--model`, `--models-dir`,
   `--preload-model`, `--output-dir`,
   `--debug-probability` are present but marked
   **Deprecated** in the help output and were not used.
4. **Built-in model files (on-disk inside image):**
   `pyopen_wakeword/models/`: `alexa.tflite`,
   `embedding_model.tflite`, `hey_jarvis.tflite`,
   `hey_mycroft.tflite`, `hey_rhasspy.tflite`,
   `melspectrogram.tflite`, **`okay_nabu.tflite`**.
5. **`pyopen_wakeword.Model` enum (authoritative model
   names):** `OKAY_NABU → "okay_nabu"`,
   `HEY_JARVIS → "hey_jarvis"`,
   `HEY_MYCROFT → "hey_mycroft"`,
   `ALEXA → "alexa"`, `HEY_RHASSPY → "hey_rhasspy"`.

**Wake-word name correction.** The D-1.1 / D-1.4 prep
docs referred to the primary wake word as `ok_nabu`.
The image reality is `okay_nabu` (file
`okay_nabu.tflite`; phrase "Okay Nabu" advertised via
Wyoming `Info`). The component-spec and deployment-doc
text is updated alongside this log to use the real
name. **This is a doc correction, not a new decision.**
Same shape as the D-1.3 finding about the stale
`10400 EXPOSE` on the Piper image.

---

## 2. Validation — Gate G-D3 (split per Q3 decision)

Spec:
[`../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md`](../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md)
§4, with the **D-1.4 split** documented inline in
that file alongside this log: the container/probe
half is closed here; the HA-UI half (Settings →
Voice assistants lists openWakeWord; `okay_nabu`
selectable in pipeline editor) is **deferred to
D-1.5** because the HA Wyoming integration wiring
itself belongs to D-1.5.

### 2.1 Restic recovery anchor

| Field | Value |
|---|---|
| Anchor snapshot ID | **`c0e8b2f5`** (D-1.4 pre-change recovery anchor) |
| Taken at | 2026-06-17 15:17:14 |
| Wrapper invoked | `sudo /usr/local/bin/homelab-backup.sh` (canonical pattern from `07_operations/backups.md`) |
| Predecessor nightly | `5a5eadf2` (2026-06-17 03:00 cron) — **explicitly not** the D-1.4 anchor |
| Coverage gap (flagged, not blocking) | The wrapper's path list is the one frozen at R-12 (2026-06-13) and does **not** include the voice-stack data dirs (`/srv/homelab/data/whisper`, `…/piper`, `…/wakeword`). The D-1.4 anchor still does its job — captures the surfaces D-1.4 promised not to touch (Open WebUI, HA, Z2M, Mosquitto, Qdrant, NPM, web roots, system configs, SQLite DBs) — but extending the script's path list to include voice-stack dirs is carried as a separate small follow-up: **R-D-14 (new)**, recorded in §6. |

### 2.2 Pre-state snapshot

| Item | Value |
|---|---|
| Snapshot dir | `/tmp/aurora-wakeword-pre-20260617131231` |
| `docker ps -a` snapshot | written to snapshot dir |
| `webui.db` md5 | `66904566476af36b110813942a2a9d8c` |
| `amarolab-audit.log` md5 | `b6c1af2e479e14588d4928fdae2e7d97` (matches D-1.3 post-state — zero drift since D-1.3 closeout) |
| `amarolab-audit.log` line count | 141 (matches D-1.3 post-state — zero drift) |
| `aurora-*` containers | `aurora-whisper`, `aurora-piper` |
| `ai-local_default` reachable | yes, 5 containers attached (`ollama`, `aurora-whisper`, `aurora-piper`, `openwebui`, `qdrant`) |
| `/srv/homelab/data/wakeword` | absent (expected) |

### 2.3 Describe probe (Wyoming `Info`)

The Describe probe is a one-off Python script running
inside a transient `python:3.12-slim` container on
`ai-local_default`, so the TCP target
`tcp://aurora-wakeword:10400` resolves via Docker DNS.
Same harness shape as D-1.3 §2.4 (Piper Describe
probe). Dependency pinned: `wyoming>=1.5,<2`.

```
>>> describe probe
   wake_programs[0].name        : 'openwakeword'
   wake_programs[0].description : 'An open-source audio wake word (or phrase) detection framework with a focus on performance and simplicity.'
   wake_programs[0].installed   : true
   wake_programs[0].models (5):
     name          phrase           languages
     ─────────────  ────────────────  ─────────
     okay_nabu     Okay Nabu        ['en']    <-- primary, target of G-D3
     hey_jarvis    Hey Jarvis       ['en']
     hey_mycroft   Hey Mycroft      ['en']
     alexa         Alexa            ['en']
     hey_rhasspy   Hey Rhasspy      ['en']
```

Confirms `okay_nabu` is advertised over Wyoming and
the program is installed.

### 2.4 Operator-recorded canary WAV (input to the detection probe)

The G-D3 synthetic-detection probe input is a
**real recording of the operator saying "Okay
Nabu"**, recorded with `arecord` on the operator's
Linux workstation and transferred into the bind
mount. Per the validation philosophy in
[`../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md`](../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md)
§1, this gives the most credible detection evidence
— an `aurora-piper`-synthesized clip in Spanish
would have introduced accent-mismatch ambiguity
(the `okay_nabu` model is trained on natural North
American English).

| Field | Value |
|---|---|
| Source recorder | `arecord` (ALSA) on the operator's Linux workstation |
| Transcode step | `ffmpeg` re-encoded the operator's source M4A (48 kHz stereo AAC) to 16 kHz mono PCM 16-bit (the format the wake-word model requires) |
| File on disk | `/srv/homelab/data/wakeword/gd3/okay_nabu_canary.wav` |
| Format (verified `file(1)`) | `RIFF (little-endian) data, WAVE audio, Microsoft PCM, 16 bit, mono 16000 Hz` |
| Sample rate | 16 000 Hz |
| Channels | 1 (mono) |
| Sample width | 2 bytes (PCM 16-bit) |
| Frame count | 40 619 |
| Duration | 2.539 s |
| Size on disk | 81 316 bytes (audio + 78 B WAV header) |
| md5 | `5a8a01cb799c67b101220817969011ce` |

### 2.5 Synthetic-detection probe (Wyoming) — G-D3 container/probe half

Harness in the same transient `python:3.12-slim`
container shape as §2.3, with two read-only bind
mounts (`${PROBE_DIR}:/probe:ro`,
`/srv/homelab/data/wakeword/gd3:/in:ro`). The probe
opens the Wyoming connection, sends
`Detect(names=["okay_nabu"])` to declare interest,
sends `AudioStart(rate=16000, width=2, channels=1)`,
streams the WAV as 30 ms / 960-byte chunks
back-to-back (85 chunks total), sends `AudioStop()`,
and reads events with a 5 s timeout.

```
>>> detection probe
   wav                   : '/in/okay_nabu_canary.wav'
   rate / width / chans  : 16000 / 2 / 1
   frames                : 40619 (duration 2.539 s)
   audio_bytes_sent      : 81238
   chunks_sent           : 85 (30 ms / 960 B each)
   t_detect_sent_ms      : 0
   t_audio_start_ms      : 0
   t_audio_stop_ms       : 1            (all audio shipped within 1 ms wall-clock)
   detections            : [
     {
       "name": "okay_nabu",
       "timestamp": 2010,
       "wall_ms_since_t0": 426
     }
   ]
   probe_exit_code       : 0            (PASS)
```

- **Server-side timestamp** `2010` (ms within the
  audio stream) — the wake word fires ≈ 2.01 s into
  the clip, which matches the natural placement of
  the operator's "Okay Nabu" utterance within the
  2.539 s recording.
- **Wall-clock latency** to receive the event = 426 ms
  from connection-open. Since the probe shipped all
  audio in 1 ms wall-clock, the server processed
  ≈ 2.5 s of audio in ≈ 425 ms — a synthesis-side
  real-time factor of **≈ 0.17** on the UM790 CPU
  under a 1.0-CPU cap.
- **`read_timeout=true`** is informational, not a
  failure: Wyoming openWakeWord emits one
  `Detection` per trigger and does **not** send a
  trailing `NotDetected` after a successful
  detection; the probe's reader waited the full
  5 s read window and returned.

**Probe artifacts on disk:**
`/tmp/aurora-wakeword-probe-20260617132015/`:
- `describe_probe.py` — §2.3 harness
- `describe_result.txt` — §2.3 result
- `detection_probe.py` — §2.5 harness (138 lines)
- `detection_probe.stdout.txt` — §2.5 result (JSON above)
- `detection_probe.stderr.txt` — `pip install` notices only; no script-side errors
- `container_logs_pre_detection.txt` — 1 line (`INFO:root:Ready`)
- `container_logs_post_detection.txt` — 1 line (unchanged)

### 2.6 Container-side log evidence — and a reality-wins clarification

`aurora-wakeword` container logs at INFO level
contain exactly **1 line** before, during, and after
the probe:

```
INFO:root:Ready
```

The image's INFO-level logger does not emit a
per-detection log line; `wyoming_openwakeword`'s
detection-side `_LOGGER.debug(...)` entries are
gated behind `--debug`. The literal wording of the
`05-validation-gates.md` §4 spec text —
*"aurora-wakeword logs a detection for the probe
clip"* — presumed a log line; the running image
publishes detections **as a `Detection` Wyoming
event on the wire**, captured by the probe in §2.5.

Per **operator decision D1 = α** at this gate, the
spec is updated alongside this apply log to
explicitly accept the Wyoming `Detection` event as
the **authoritative server-side signal** for G-D3,
while INFO-level container logs may remain quiet.
The acceptance condition is met by:

- a `Detection(name="okay_nabu", …)` event captured
  by the probe (§2.5),
- **zero errors** in `aurora-wakeword` container logs
  during the probe window (verified by `grep -iE
  "ERROR|Traceback|CRITICAL|Exception"` returning
  empty).

This mirrors the D-1.3 precedent of recording
image-reality findings (e.g. stale `10400 EXPOSE`,
`PIPER_*` env-var non-support) in the apply log and
reflecting them back into the spec. **No container
recreate. No `--debug` flag.**

### 2.7 G-D3 acceptance summary

| Criterion | Source | Status |
|---|---|---|
| HA UI lists openWakeWord as available | HA Wyoming integration UI | **Deferred to D-1.5** (split — see §2 preamble) |
| `okay_nabu` selectable in pipeline editor | HA Assist pipeline editor | **Deferred to D-1.5** |
| Server publishes a `Detection` event for the probe clip | Probe JSON §2.5 | **PASS** (`name="okay_nabu"`, `timestamp=2010`) |
| No errors in `aurora-wakeword` logs during the probe | Container logs §2.6 | **PASS** (1 log line total: `INFO:root:Ready`) |
| `okay_nabu` advertised via Wyoming `Info` | Describe probe §2.3 | **PASS** |

G-D3 container/probe half is **closed**. HA-UI half
remains open, owned by D-1.5.

---

## 3. Pre / post state evidence

### 3.1 Pre-state

| Item | Value |
|---|---|
| Snapshot dir | `/tmp/aurora-wakeword-pre-20260617131231` |
| `docker ps -a` snapshot | written to snapshot dir |
| `webui.db` md5 | `66904566476af36b110813942a2a9d8c` |
| `amarolab-audit.log` md5 | `b6c1af2e479e14588d4928fdae2e7d97` (matches D-1.3 post-state — zero drift since D-1.3) |
| `amarolab-audit.log` line count | 141 (matches D-1.3 post-state) |
| `aurora-*` containers | `aurora-whisper`, `aurora-piper` |
| `ai-local_default` reachable | yes, 5 containers attached |
| `/srv/homelab/data/wakeword` | absent |

### 3.2 Post-state

| Item | Value |
|---|---|
| Snapshot dir | `/tmp/aurora-wakeword-post-20260617134731` |
| `docker ps` | adds `aurora-wakeword Up 28 minutes`; all 11 prior live containers unchanged |
| `webui.db` md5 | `66904566476af36b110813942a2a9d8c` (**unchanged**) |
| `amarolab-audit.log` md5 | `b6c1af2e479e14588d4928fdae2e7d97` (**unchanged**) |
| `amarolab-audit.log` line count | 141 (**unchanged**) |
| `webui.db.tool` row inventory | `audit_search, docker_containers, docker_logs, ha_call_service, ha_get_state, rag_search, system_status, time_now` (**unchanged**) |
| `qwen2.5:7b-instruct.meta.toolIds` | `["time_now","rag_search","audit_search","ha_get_state","ha_call_service"]` (**unchanged**) |
| `qwen2.5:7b-instruct.base_model_id` | `NULL` (**unchanged** — D-35 preserved) |
| Bind-mount disk usage | 88 KB (84 KB for `gd3/okay_nabu_canary.wav`; container itself wrote 0 bytes — built-in models live read-only inside the image, custom-model-dir is empty) |
| `ai-local_default` attachments | 6 containers (`aurora-wakeword` added) |
| Open WebUI | healthy |
| Home Assistant | running (unchanged) |
| Mosquitto | running (hardened posture from 2026-06-17 unchanged) |
| Zigbee2MQTT | running (unchanged) |
| Ollama | running (unchanged) |
| Qdrant | running (unchanged) |
| `aurora-whisper` | running (unchanged) |
| `aurora-piper` | running (unchanged) |
| Guardian Cloud (`guardian-web`) | running (untouched) |

### 3.3 Invariant — clean window, no causality stanza needed

The clarified invariant from D-1.3 §3.3 — *"no D-1.x
action may modify Open WebUI configuration, tool
inventory, model bindings or audit structures"* —
holds **literally** for D-1.4:

- `webui.db` md5: **byte-identical** pre vs post.
- `amarolab-audit.log` md5 and line count:
  **byte-identical** pre vs post.
- `webui.db.tool` row inventory: **unchanged**.
- `qwen2.5:7b-instruct` row (`base_model_id`,
  `meta.toolIds`, `params.system`): **unchanged**.

Unlike D-1.3 — which ran during a window of
concurrent operator OWUI use and needed a multi-table
causality stanza to disentangle D-1.3 actions from
chat-side traffic — the D-1.4 window had **zero**
concurrent OWUI / HA / audit-side activity. No
causality analysis is needed for this apply log.

Mechanically: `aurora-wakeword` mounts only
`/srv/homelab/data/wakeword` (`docker inspect`
verified — single mount). The two transient
`python:3.12-slim` probe containers mounted only
`${PROBE_DIR}:/probe:ro` (read-only harness) and
`/srv/homelab/data/wakeword/gd3:/in:ro` (read-only
WAV). No access to `/srv/homelab/data/openwebui/`,
`/srv/homelab/homeassistant/`, the `webui.db`
container path, or the audit log.

---

## 4. What this did NOT change

- `webui.db` schema or `webui.db.tool` row set.
- `qwen2.5:7b-instruct` model row (`base_model_id`,
  `meta.toolIds`, `params.system` — all unchanged).
- Open WebUI Audio settings (`AUDIO_*` env vars,
  STT engine, TTS engine — none touched).
- Audit log schema (no new field, no new tool, no
  voice-side line shape — Q-D-05 still carried).
- Mosquitto config, users, ACLs.
- Z2M configuration or device list.
- Existing HA integrations (MQTT, Z2M discovery,
  Wyoming Protocol — Wyoming wake-word wiring is
  D-1.5 work, not exercised here).
- HA Assist pipeline (`AURORA v1` — D-1.5).
- Cloudflared tunnel.
- Guardian Cloud (`guardian-web`).
- `aurora-whisper` (D-1.2 deployment) — unchanged.
- `aurora-piper` (D-1.3 deployment) — unchanged;
  the D-D3-VOICE-SWAP question stays open and is
  D-1.5 work, not exercised here.

No environment file (`ai-stack/.env`) was modified.
No secrets were introduced or printed. No host port
is published by `aurora-wakeword`. No container
config recreate (no `--debug` flag, no
threshold tuning).

---

## 5. Decisions closed by this log

| Decision ID | Closes at | Outcome |
|---|---|---|
| C-D-03 (openWakeWord image pinned tag) | this log | `rhasspy/wyoming-openwakeword:2.1.0` (local manifest digest `sha256:52cb1168731a1849fc28cf339c935fde58746bbabc94226668a40ef6ddf5d42b`, Docker Hub `last_updated 2025-10-28T15:14:47Z`, same SHA as `:latest`) |

The component-spec doc
[`../04_ai_system/amarolab-v1/phase-d/03-component-spec.md`](../04_ai_system/amarolab-v1/phase-d/03-component-spec.md)
§4 is updated alongside this log to reflect the
closure and the CLI-flag-only configuration shape.

The validation-gates doc
[`../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md`](../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md)
§4 is updated alongside this log to (a) record the
G-D3 split between D-1.4 (container/probe half) and
D-1.5 (HA-UI half), and (b) replace the
"`aurora-wakeword` logs a detection" criterion with
explicit acceptance of the Wyoming `Detection` event
as the authoritative server-side signal, per
operator decision **D1 = α**.

The deployment doc
[`../03_services/voice-stack/wakeword/openwakeword-deployment.md`](../03_services/voice-stack/wakeword/openwakeword-deployment.md)
is updated alongside this log to (a) fill in §6 with
the actual `docker run` recipe, (b) correct
`ok_nabu` → `okay_nabu`, (c) remove the `WAKEWORD_*`
env-var formulation in favor of CLI flags, and (d)
clarify mount semantics (`/custom_models`, not
`/data`).

**C-D-03 ID collision noted, deferred.** The same ID
collision flagged in the D-1.3 apply log §2.7 — where
`C-D-03` is used both for "openWakeWord image pinned
tag" (now closed by this log) and for "voice
alternative evaluation" (closed by C-D-08 at D-1.3
§2.7) — is **not** corrected in D-1.4. Per the user's
explicit decision #5 at D-1.4 prep, the collision is
flagged for a separate doc-cleanup commit and carried
in §6.

---

## 6. Open / deferred items

| ID | Item | Carried to |
|---|---|---|
| **(new)** D-D4-G-D3-HA-UI | HA-UI half of G-D3 — HA Settings → Voice assistants lists openWakeWord; `okay_nabu` selectable in HA Assist pipeline editor | D-1.5 (HA Assist pipeline configuration) |
| **(new)** R-D-14 | Extend `/usr/local/bin/homelab-backup.sh` path list to include `/srv/homelab/data/whisper`, `/srv/homelab/data/piper`, `/srv/homelab/data/wakeword` so voice-stack state is covered by the nightly Restic snapshot | post-Phase-D maintenance (separate small commit) |
| C-D-05 | HA Assist pipeline timeout | D-1.5 / G-D5 prep |
| C-D-07 | Open WebUI Audio surface default for `qwen2.5` | D-1.7 |
| C-D-09 | Image candidate for the separate Piper OpenAI-compatible TTS shim container | D-1.7 prep |
| D-D1-HTTP | HTTP-shim path of G-D1 (transcription via `POST /v1/audio/transcriptions`) | D-1.7 |
| D-D2-HTTP | HTTP-shim path of G-D2 (audio playback via `POST /v1/audio/speech`) | D-1.7 |
| D-D3-VOICE-SWAP | Reconcile `aurora-piper`'s startup `--voice` flag with the AURORA voice identity (`es_ES-sharvard-medium` speaker `F`) | D-1.5 (HA Assist pipeline configuration) |
| C-D-03 ID collision | Decision ID `C-D-03` is used in two different senses across the historical docs (image-pin vs. voice-alternative). Both are now closed (this log + C-D-08 at D-1.3), but the ID collision in the docs themselves is not fixed | doc cleanup (separate small commit) |
| R-D-13 | Migrate HTTP shim off `fedirz/faster-whisper-server` to a maintained successor | post-Phase-D maintenance |
| Q-D-05 | Voice-originated entity actions are not currently written to `amarolab-audit.log` | D-2 |

---

## 7. Reproducibility

The exact `docker run` command (§1.2), the
bind-mount preparation (§1.3), the image-reality
inspection (§1.6), the Wyoming probe harnesses
(§2.3, §2.5), and the operator canary recording
spec (§2.4) are sufficient to reproduce this result
on the same UM790 host. Image digest recorded in
§1.1 anchors the binary identity. The Restic anchor
(§2.1, snapshot `c0e8b2f5`) provides the recovery
point.

For the synthetic-detection probe to be reproducible
by a different operator, the input WAV must remain
in the format constraints listed in §2.4 (16 kHz
mono PCM 16-bit, ~1.5–5 s, clear "Okay Nabu" with
small silence head/tail at conversational volume).
The model is trained on natural North American
English; synthesized speech or strongly accented
speech may score below the default 0.5 threshold and
should not be used as the canary.

---

## 8. Stop point

Per the user instruction, D-1.4 stops here. No
work has begun on:

- D-1.5 (HA Assist pipeline configuration — includes
  the deferred HA-UI half of G-D3 captured as
  D-D4-G-D3-HA-UI in §6, plus the D-D3-VOICE-SWAP
  reconciliation for Piper, plus C-D-05 pipeline
  timeout determination)
- D-1.6 (real-device end-to-end / G-D5)
- D-1.7 (Open WebUI Audio integration + the deferred
  G-D1-HTTP and G-D2-HTTP halves)
- D-1.8 (failure-mode rehearsal / G-D6)
- D-1.9 (Phase D-1 closeout)

The overview triad
(`00_overview/CURRENT_STATE.md`,
`AMAROLAB_HANDOFF.md`, `ROADMAP.md`) will be
updated at Phase D-1 closeout (D-1.9), not now —
per Lesson 005 ("harden then document" — overview
docs reflect the closed phase, not intermediate
milestones). The same discipline was applied at
D-1.2 and D-1.3.
