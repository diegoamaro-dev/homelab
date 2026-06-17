# Phase D — D-1.3 — Piper standup — APPLIED

- **Date:** 2026-06-17
- **Phase step:** D-1.3 (Piper standup)
- **Ecosystem:** **AMAROLAB** — Personal Innovation Lab
  and Digital Infrastructure Ecosystem.
- **Assistant:** **AURORA** — Personal AI Assistant
  for the AMAROLAB ecosystem.
- **Independent project on AMAROLAB infrastructure:**
  **Guardian Cloud** — not modified by this work.
- **Status:** **APPLIED.** `aurora-piper` (Wyoming
  TTS) deployed on UM790 against `ai-local_default`.
  Gate **G-D2 (Wyoming path)** validated end-to-end:
  describe probe reports `piper` program exposing
  `es_ES-davefx-medium` (`installed: true`); synthesize
  probe of `"AURORA activada"` returned
  PCM 16-bit / mono / 22 050 Hz audio totalling
  1 079 ms in 335 ms wall-clock (first chunk 332 ms;
  synthesis real-time factor **0.31**). The WAV is on
  disk at
  `/srv/homelab/data/piper/gd2/aurora_activada.wav`
  for operator listening from the workstation. The
  HTTP-shim path of G-D2 is **deferred to D-1.7**
  (Open WebUI Audio integration) — same precedent as
  the deferred G-D1 HTTP path; no HTTP-shim consumer
  exists for Piper until D-1.7. C-D-06 is closed
  accordingly: **Wyoming-only in D-1.3; OpenAI-compatible
  HTTP shim deferred to D-1.7.**
- **Scope:** Piper container only. No openWakeWord
  (D-1.4), no HA Assist configuration (D-1.5), no
  Open WebUI Audio settings (D-1.7), no changes to
  `webui.db` schema, `webui.db.tool` rows,
  `qwen2.5:7b-instruct` model row, the Tool layer,
  the D-12 allowlist, Mosquitto, Zigbee2MQTT, Home
  Assistant, Open WebUI configuration, Ollama,
  Qdrant, or Guardian Cloud.
- **Inputs:**
  - Phase D component spec:
    [`../04_ai_system/amarolab-v1/phase-d/03-component-spec.md`](../04_ai_system/amarolab-v1/phase-d/03-component-spec.md)
  - Validation gates:
    [`../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md`](../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md)
  - Piper deployment plan:
    [`../03_services/voice-stack/piper/piper-deployment.md`](../03_services/voice-stack/piper/piper-deployment.md)
  - Voice privacy policy:
    [`../06_security/voice_privacy.md`](../06_security/voice_privacy.md)
  - D-1.2 apply log (template followed):
    [`./2026-06-17_phaseD_whisper_installed.md`](./2026-06-17_phaseD_whisper_installed.md)

---

## 1. What was installed

### 1.1 Container

| Field | Value |
|---|---|
| Container name | `aurora-piper` |
| Container ID | `339d50d93129` |
| Image | `rhasspy/wyoming-piper:2.2.2` |
| Image digest | `sha256:c874e4a04657ae3381332ee5d0c8c70a310dae6722892840f530ac0890b44eb3` |
| Network | `ai-local_default` |
| Container IP | `172.18.0.6` |
| Wyoming port (actual listener) | `10200/tcp` (internal; **not** published to host) |
| Wyoming port (image `EXPOSE` — stale) | `10400/tcp` shown by `docker ps`; the upstream image carries a stale `EXPOSE` directive that does **not** match the entrypoint binding. Verified by reading `/proc/net/tcp` inside the container — actual listener is `10200/tcp`. Recorded here so future operators do not chase the wrong port. |
| Restart policy | `unless-stopped` |
| Resource caps | `--cpus 1 --memory 1g` (`NanoCpus=1000000000`, `Memory=1073741824`) |
| Bind mount | `/srv/homelab/data/piper` → `/data` (rw) |
| Voice (primary) | `es_ES-davefx-medium` |
| Length scale | `1.0` (natural pacing) |
| Noise scale | image default (not overridden) |
| User inside container | root (uid 0) |
| Ready signal | `INFO:__main__:Ready` after the voice download completed |
| Voice fetch URLs | `https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx` and `…/es_ES-davefx-medium.onnx.json` |

### 1.2 Exact `docker run` command executed

```bash
docker run -d --name aurora-piper --restart unless-stopped \
  --network ai-local_default \
  -v /srv/homelab/data/piper:/data \
  --cpus 1 --memory 1g \
  rhasspy/wyoming-piper:2.2.2 \
  --voice es_ES-davefx-medium \
  --length-scale 1.0
```

CLI args after the image are forwarded by the image's
`/usr/src/docker_run.sh` entrypoint, which prepends
`--uri tcp://0.0.0.0:10200 --data-dir /data`. The
`PIPER_*` env-var formulation in the original
deployment-doc draft is **not** what the image consumes;
the image takes equivalent settings as CLI flags, and
this log records what was actually executed (per
Lesson 003 — reality wins). The component-spec
decision table is updated alongside this log to
reflect that configuration is by CLI flag.

### 1.3 Bind-mount preparation

```bash
mkdir -p /srv/homelab/data/piper
chmod 755 /srv/homelab/data/piper
```

Owner: `diego:diego`. The container runs as root and
writes the voice cache (61 MB total — 60.3 MB ONNX +
5 KB JSON) into this directory. A `gd2/` subfolder
was created prior to the synthesize probe and contains
the canary WAV produced in §2.3.

### 1.4 Image selection rationale

| Image | Why pinned this version |
|---|---|
| `rhasspy/wyoming-piper:2.2.2` | Latest stable semver tag (Docker Hub `last_updated=2026-02-05T13:52:23Z`). Same SHA as `:latest` (`sha256:c874e4…`) — confirming the maintainers point `:latest` at this revision. Clean semver, official Rhasspy / Home Assistant ecosystem image. Successor of `2.2.1` / `2.2.0` / `2.1.x` series; `1.x` lineage retired in 2026-01. |

C-D-02 is closed by this selection.

**C-D-06 is closed in favour of a separate
OpenAI-compatible TTS container at D-1.7** (not the
built-in mode originally sketched in the D-1.1
skeleton). Verified by inspecting the running image:

```
$ docker run --rm --entrypoint /usr/src/.venv/bin/python3 \
    rhasspy/wyoming-piper:2.2.2 -m wyoming_piper --help
```

The CLI exposes `--voice`, `--uri`, `--zeroconf`,
`--data-dir`, `--download-dir`, `--speaker`,
`--noise-scale`, `--length-scale`, `--noise-w-scale`,
`--auto-punctuation`, `--samples-per-chunk`,
`--no-streaming`, `--update-voices`, `--use-cuda`,
`--debug`, `--log-format`, `--version` — and
**no `--http-port` or equivalent flag.**
`rhasspy/wyoming-piper:2.2.2` is a pure Wyoming
server. The "built-in OpenAI-compatible HTTP mode"
referenced in the D-1.1 skeleton does not exist on
this image.

Consequence: D-1.7 must add a **separate
OpenAI-compatible TTS shim container** that fronts
the same voice files (mounted from
`/srv/homelab/data/piper/`). Image selection for
that shim is a new open decision: **C-D-09**
(tracked in §6 below and in `03-component-spec.md`
§9), to close at D-1.7 prep. The Wyoming-only
posture for D-1.3 is unchanged — the HTTP shim
half of G-D2 still defers to D-1.7, and Phase D-1
closeout still requires that half to be exercised.

---

## 2. Validation — Gate G-D2

Spec:
[`../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md`](../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md)
§3.

### 2.1 Reference text

| Field | Value |
|---|---|
| Text | `AURORA activada` |
| Voice requested | `es_ES-davefx-medium` |
| Rationale | Short canonical Spanish utterance recognisable when played back; voice timbre is unambiguously `davefx` (male, neutral Spanish (Spain) accent) versus the other locally-available `es_ES-*` voices. |

### 2.2 Describe probe (Wyoming `Info`)

```
>>> describe probe
   tts_programs : ['piper']
   8 Spanish voices catalogued (installed flag from image catalog):
     es_AR-daniela-high      installed=true
     es_ES-carlfm-x_low      installed=true
     es_ES-davefx-medium     installed=true   <-- primary, on-disk weights present
     es_ES-mls_10246-low     installed=true
     es_ES-mls_9972-low      installed=true
     es_ES-sharvard-medium   installed=true
     es_MX-ald-medium        installed=true
     es_MX-claude-high       installed=true
```

Confirms the loaded voice catalog and that the primary
voice `es_ES-davefx-medium` is exposed via the
Wyoming `Info` payload. The image bundles the full
upstream voice list as catalog metadata; only voices
explicitly downloaded into `/data` (i.e.
`es_ES-davefx-medium` per §1.1) have their ONNX
weights present on disk — `installed=true` here
reflects the image's catalog flag, not the on-disk
presence of weights for every entry.

### 2.3 Synthesize probe (Wyoming)

```
>>> synthesize probe
   text                  : 'AURORA activada'
   voice_requested       : 'es_ES-davefx-medium'
   sample_rate_hz        : 22050
   sample_width_bytes    : 2 (PCM 16-bit)
   channels              : 1 (mono)
   audio_bytes           : 47 616
   audio_duration_ms     : 1 079
   latency_first_chunk_ms: 332
   latency_total_ms      : 335
   rtf_synthesis         : 0.31
   wav_path_in_container : /out/aurora_activada.wav
   wav_path_on_host      : /srv/homelab/data/piper/gd2/aurora_activada.wav
   wav_size_bytes        : 47 660  (audio + 44-byte WAV header)
   wav_md5               : c1cbd9192a7632b8040b05769b890618
   wav_format            : RIFF / WAVE / Microsoft PCM 16-bit mono 22050 Hz (verified via `file(1)`)
```

- **Latency:** first audio chunk at 332 ms, last chunk
  + stop at 335 ms total — Piper streamed nearly the
  whole utterance in one window for this short phrase.
- **Synthesis RTF: 0.31** (1 079 ms of audio produced
  in 335 ms wall-clock — ~3.2× faster than real-time
  on the UM790 CPU, with a 1.0-CPU cap).
- **Format:** matches Piper's medium-quality ONNX
  default output (22 050 Hz / 16-bit / mono).
- **File on disk:** the operator fetches
  `/srv/homelab/data/piper/gd2/aurora_activada.wav`
  to the workstation PC and plays it; G-D2 acceptance
  (audibility + recognisable timbre as
  `es_ES-davefx-medium`) is recorded by the operator
  in this log under §2.5 once verified.

### 2.4 Probe harness

The harness is a one-off Python script running inside
a transient `python:3.12-slim` container on
`ai-local_default` so the TCP target
`tcp://aurora-piper:10200` resolves via Docker DNS.
Dependencies pinned at probe time:

| Package | Version | Why |
|---|---|---|
| `wyoming` | `>=1.5,<2` | Wyoming protocol client (`AsyncTcpClient`, `Synthesize`, `SynthesizeVoice`, `AudioStart/Chunk/Stop`, `Describe`/`Info`) |

Harness file:
`/tmp/aurora-gd2-20260617092523/wyoming_probe.py`
(kept on host for reproducibility within this
session; not added to the repo).

Two minor harness fixes during execution:

1. `info.tts[*].voices[*].languages` returns bare
   strings in this client/server pair, not `Language`
   objects with `.code`. The harness was patched to
   accept both shapes before re-running.
2. The probe writes the WAV to `/out` inside the
   probe container, which is bind-mounted from
   `/srv/homelab/data/piper/gd2` on the host — no
   host-audio output configuration is involved.

### 2.5 Operator listening verdict (audibility + timbre)

| Field | Value |
|---|---|
| Plays audibly on workstation | **PASS** |
| Intelligibility ("AURORA activada" understandable) | **PASS** |
| Voice timbre matches `es_ES-davefx-medium` | **PASS** — synthesized timbre matches the requested voice |
| Notes | Voice is technically PASS on all three dimensions. **Voice identity** (whether `es_ES-davefx-medium` is the right voice for AURORA) was raised as a separate question and resolved in §2.7 — operator approved `es_ES-sharvard-medium` speaker `F` as the AURORA voice identity. G-D2 Wyoming-path acceptance is met by this PASS; the voice swap is a forward action, not a G-D2 re-run. |

The Wyoming-side acceptance criteria from
`05-validation-gates.md` §3 (Wyoming probe succeeds,
no errors in `aurora-piper` logs) are met; the
audibility criterion is closed by the PASS verdict
above.

### 2.6 HTTP-shim path of G-D2

**Deferred to D-1.7.** Rationale:

- D-1.3 (per the implementation roadmap) names only
  `rhasspy/wyoming-piper`.
- The HTTP shim half of G-D2 has no consumer until
  D-1.7 (Open WebUI Audio integration).
- The HTTP shim for D-1.7 will be a **separate
  OpenAI-compatible TTS container** (image candidate
  is C-D-09, evaluated at D-1.7 prep) — per the
  C-D-06 closure above, the rhasspy image is a pure
  Wyoming server and has no built-in HTTP mode. The
  Piper shim joins the existing OpenAI-compatible
  faster-whisper-server shim at D-1.7 to close both
  deferred HTTP halves at once.
- G-D2 status is therefore **partial — Wyoming path
  validated; HTTP path deferred to D-1.7.** Phase D-1
  closeout will only be possible once the deferred
  path is exercised.

### 2.7 Voice identity exercise — outcome

**Trigger.** §2.5 PASS-ed `es_ES-davefx-medium`
technically (audibility / intelligibility / timbre
all PASS), but the operator flagged a separate
question: davefx is **male**, and AURORA's intended
voice identity is **female Spain**. This subsection
records the voice-selection exercise that ran
post-G-D2, on 2026-06-17, without redeploying or
reconfiguring `aurora-piper`.

**Method.** The running container's startup `--voice`
flag was left at `es_ES-davefx-medium`. Per-request
voice selection via the Wyoming `SynthesizeVoice`
field was used to synthesize a single reference
phrase across five (voice, speaker) combinations:

| Sample | Voice | Speaker | Note |
|---|---|---|---|
| `baseline_davefx_M.wav` | `es_ES-davefx-medium` | — | Current, baseline for A/B |
| `sharvard_F.wav` | `es_ES-sharvard-medium` | `F` | Catalog-verified female (Hispania) |
| `sharvard_M.wav` | `es_ES-sharvard-medium` | `M` | Same model, male — speaker-map sanity check |
| `mls_10246.wav` | `es_ES-mls_10246-low` | — | MLS LibriVox, gender unknown ex-ante |
| `mls_9972.wav` | `es_ES-mls_9972-low` | — | MLS LibriVox, gender unknown ex-ante |

Reference phrase used for all five:

> *"Hola, soy AURORA. ¿En qué puedo ayudarte hoy?"*

**Authoritative source for the candidate list.**
`https://huggingface.co/rhasspy/piper-voices/resolve/main/voices.json`
(230 709 bytes). The dual-speaker disposition of
`es_ES-sharvard-medium` is from its
`speaker_id_map = {"M": 0, "F": 1}` entry — no
listening needed to confirm female availability.

**Output location.**
`/srv/homelab/data/piper/gd2/voice-compare/` —
five WAVs (~1.4 MB total) plus
`comparison_summary.json` with per-sample latency
and format metadata.

**Cache delta from the exercise.** Voice cache grew
from 61 MB to **256 MB** — three first-touch ONNX
downloads (`sharvard` 73 MB, `mls_10246` 60 MB,
`mls_9972` 60 MB) into the existing
`/srv/homelab/data/piper` bind mount. No new bind
mount, no container recreate.

**Observed anomalies.** The two MLS voices produced
audio that was **4.9× to 7.7× over-length** for the
reference phrase (`mls_10246` 19 760 ms,
`mls_9972` 12 704 ms vs ~2.5 s expected). They
were ruled out as production candidates regardless
of gender — low-quality MLS models mishandle the
Spanish `¿…?` punctuation in interactive prompts.

**Operator verdict (2026-06-17).** Approved:

> **AURORA voice identity:** `es_ES-sharvard-medium`
> with `speaker = "F"`.

Audibility PASS, intelligibility PASS, timbre PASS
on the sharvard_F sample.

**Container state at decision time.**
`aurora-piper` is still running with startup
`--voice es_ES-davefx-medium`. G-D2's Wyoming-path
acceptance was completed against davefx (§2.3,
§2.5) and is **not re-run** — it remains the
authoritative G-D2 evidence. The voice identity
decision is a **forward action**, deferred to the
HA Assist pipeline configuration at D-1.5.

**Two viable mechanisms for D-D3-VOICE-SWAP** (to
be chosen at D-1.5 prep — both are confirmed
supported by the running image):

| Mechanism | How | Pros | Cons |
|---|---|---|---|
| **Startup default** *(fallback / safer)* | Recreate `aurora-piper` with `--voice es_ES-sharvard-medium --speaker F` as startup defaults — both flags confirmed present in `python -m wyoming_piper --help`. Bind mount and voice cache preserved across recreate (~ seconds of downtime). | Works regardless of how HA Assist's TTS slot exposes per-request overrides; guaranteed default for any consumer (HA + future Open WebUI HTTP shim). | One container recreate. |
| **Per-request via HA Assist TTS slot** | Configure HA's Wyoming TTS integration with `voice = es_ES-sharvard-medium` and `speaker = F` per request, no container change. | No container recreate. | **Not yet verified** — HA Wyoming integration's UI must actually expose `speaker` as a configurable per-request field. To verify at D-1.5 prep against the live HA UI; if the field is not exposed, fall back to the startup-default mechanism. |

The original apply log wording — *"no container
recreate is strictly required"* — is **conditional
on the per-request mechanism being verified at
D-1.5 prep**. If the HA integration does not
expose `speaker` as a per-request field, the
startup-default mechanism applies and one
recreate is required.

**Decisions closed by this subsection.**

| ID | Outcome |
|---|---|
| C-D-08 *(new)* | **CLOSED 2026-06-17** — AURORA voice identity is `es_ES-sharvard-medium` speaker `F`. Recorded in `04_ai_system/amarolab-v1/phase-d/03-component-spec.md` §3 + §9. |

**Doc-cleanup item flagged.** The decision-ID `C-D-03`
is used in two different senses across the current
docs: (a) `03-component-spec.md` §9 has C-D-03 =
"openWakeWord image pinned tag" (open, planned for
D-1.4); (b) `piper-deployment.md` §3 and the §6 of
this apply log have C-D-03 = "voice alternative
evaluation". This collision was inherited from the
D-1.1 / D-1.3 skeleton work and is not corrected
here — flagged as a doc-cleanup item for a separate
small commit so this apply log's history stays
single-purpose.

---

## 3. Pre / post state evidence

### 3.1 Pre-state

| Item | Value |
|---|---|
| Snapshot dir | `/tmp/aurora-piper-pre-20260617092215` |
| `docker ps -a` snapshot | written to snapshot dir |
| `webui.db` md5 | `ce0884d7e0c8cf40cc81adcbef62fe88` (matches D-1.2 post-state — zero drift since D-1.2 closeout) |
| `amarolab-audit.log` md5 | `50dda5f5a464538753b8738d41515a1f` (matches D-1.2 post-state) |
| `audit.log` line count | 140 |
| `aurora-*` containers | `aurora-whisper` only |
| `ai-local_default` reachable | yes, 4 containers attached (`ollama`, `aurora-whisper`, `openwebui`, `qdrant`) |
| `/srv/homelab/data/piper` | absent |

### 3.2 Post-state

| Item | Value |
|---|---|
| Snapshot dir | `/tmp/aurora-piper-post-20260617092743` |
| `docker ps` | adds `aurora-piper Up <minutes>`; all 10 prior containers unchanged |
| `webui.db` md5 | `928319020cdb2e1a43769ebea9a6580c` — changed by concurrent operator activity, see §3.3 |
| `amarolab-audit.log` md5 | `b6c1af2e479e14588d4928fdae2e7d97` — changed by concurrent operator activity, see §3.3 |
| `audit.log` line count | 141 (delta: +1 line — chat-side `time_now` call) |
| Bind-mount disk usage | **61 MB** (60.3 MB ONNX + 5 KB JSON + 52 KB G-D2 WAV) *— **point-in-time at 09:27 UTC**; cache subsequently grew to **256 MB** after the C-D-08 voice-identity exercise downloaded `sharvard` (73 MB), `mls_10246` (60 MB) and `mls_9972` (60 MB). See §2.7. Current-state cache size is the 256 MB figure.* |
| `ai-local_default` attachments | 5 containers (`aurora-piper` added) |
| Open WebUI | healthy |
| Home Assistant | running (unchanged) |
| Mosquitto | running (hardened posture from 2026-06-17 unchanged) |
| Zigbee2MQTT | running (unchanged) |
| Ollama | running (unchanged) |
| Qdrant | running (unchanged) |
| `aurora-whisper` | running (unchanged) |
| Guardian Cloud (`guardian-web`) | running (untouched) |

### 3.3 Invariant clarification — D-1.3 causality vs concurrent operator activity

The D-1.2 wording "Pre/post md5 of `webui.db` and
`amarolab-audit.log` unchanged" reflected the lucky
outcome of a quiet operator window, not a structural
property of voice-stack rollout. In this D-1.3 window
the operator was actively using Open WebUI, so both
files moved.

**The original invariant is hereby clarified as:**

> **No D-1.3 action may modify Open WebUI
> configuration, tool inventory, model bindings or
> audit structures.**
>
> User-generated activity during the validation
> window is acceptable if causality is clearly
> demonstrated and documented.

**Causal proof that D-1.3 itself wrote nothing under
`/srv/homelab/data/openwebui/`:**

1. `aurora-piper` mounts only
   `/srv/homelab/data/piper` (`docker inspect`
   verified — single mount).
2. The transient `python:3.12-slim` probe container
   mounted only `/probe:ro` (harness, read-only) and
   `/out` (bind into `/srv/homelab/data/piper/gd2`)
   — no access to `/srv/homelab/data/openwebui/`.
3. `webui.db.tool` row inventory unchanged:
   `SELECT id FROM tool ORDER BY id;` returns
   `audit_search, docker_containers, docker_logs,
   ha_call_service, ha_get_state, rag_search,
   system_status, time_now` — same set as before
   D-1.3, zero `piper/aurora/tts` entries.
4. `qwen2.5:7b-instruct.meta.toolIds` is exactly
   `["time_now","rag_search","audit_search","ha_get_state","ha_call_service"]`
   — model bindings unchanged.
5. `params.system` of `qwen2.5:7b-instruct` —
   unchanged (no edit path executed against it).
6. Zero voice-tagged audit lines in
   `amarolab-audit.log` — the audit structure was
   not extended for voice in D-1.3 (Q-D-05 remains
   the carried gap for D-2).

**Concurrent operator activity, causally attributed:**

- `amarolab-audit.log` delta = +1 line:

  ```json
  {"ts": "2026-06-17T09:26:52.765513+00:00",
   "id": "1d67873d-031a-4abe-8496-04a32cba05b3",
   "user": "diego", "tool": "time_now",
   "args": {"timezone": "Europe/Madrid", "format": "human"},
   "allowed": true, "result_code": "ok", "duration_ms": 86}
  ```

  A chat-side `time_now` Tool call from a parallel
  Open WebUI session. No voice context. Not produced
  by any D-1.3 action.

- `webui.db` delta: Open WebUI's container logs
  show the operator logged in at UTC `09:25:34`,
  opened a chat (`POST /api/v1/chats/new` at
  `09:25:45`), and the Tool modules were re-loaded
  for that chat. Open WebUI writes
  chat / session / user-activity rows to `webui.db`
  on live use. None of that activity is in the
  D-1.3 causal chain.

All four structural conditions of the clarified
invariant — **configuration, tool inventory, model
bindings, audit structures** — are preserved.

---

## 4. What this did NOT change

- `webui.db` schema or `webui.db.tool` row set.
- `qwen2.5:7b-instruct` model row (`base_model_id`,
  `meta.toolIds`, `params.system` — all unchanged).
- Open WebUI Audio settings (`AUDIO_*` env vars,
  STT engine, TTS engine — none touched).
- Audit log schema (no new field, no new tool, no
  voice-side line shape).
- Mosquitto config, users, ACLs.
- Z2M configuration or device list.
- Existing HA integrations (MQTT, Z2M discovery,
  Wyoming Protocol — none added for Piper yet; that
  belongs to D-1.5).
- Cloudflared tunnel.
- Guardian Cloud (`guardian-web`).

No environment file (`ai-stack/.env`) was modified.
No secrets were introduced or printed. No host port
is published by `aurora-piper`.

---

## 5. Decisions closed by this log

| Decision ID | Closes at | Outcome |
|---|---|---|
| C-D-02 (Piper Wyoming image pinned tag) | this log | `rhasspy/wyoming-piper:2.2.2` (digest `sha256:c874e4…`, `last_updated 2026-02-05`, same SHA as `:latest`) |
| C-D-06 (Piper HTTP shim — built-in mode or separate container) | this log | **Separate OpenAI-compatible TTS container.** Built-in HTTP mode was evaluated against the running `rhasspy/wyoming-piper:2.2.2` image at D-1.3 verification (CLI help inspected via `python -m wyoming_piper --help`) and **does not exist** — the image is a pure Wyoming server. D-1.7 must therefore add a separate shim container. **Image selection is C-D-09**, deferred to D-1.7 prep. |

The component-spec doc
[`../04_ai_system/amarolab-v1/phase-d/03-component-spec.md`](../04_ai_system/amarolab-v1/phase-d/03-component-spec.md)
is updated alongside this log to reflect both
closures and the deferred HTTP-shim path.

**C-D-03 supersession.** The original D-1.3
closeout text said *"C-D-03 (voice alternative)
remains open and is explicitly not exercised in
D-1.3 — only the primary voice
`es_ES-davefx-medium` is deployed."* That was
accurate at D-1.3 apply time. **It is now
superseded** by §2.7 — the post-G-D2 voice
identity exercise closed the voice-alternative
question via the new decision ID **C-D-08**
(`es_ES-sharvard-medium` speaker `F`). The §6
table reflects the current state; the `C-D-03` ID
itself is also collided with `03-component-spec.md`
§9 (where C-D-03 is used for the openWakeWord
image), and that collision is flagged for a
separate doc-cleanup commit.

---

## 6. Open / deferred items

| ID | Item | Carried to |
|---|---|---|
| C-D-03 | Voice alternative evaluation — **superseded by §2.7 C-D-08 closure (`es_ES-sharvard-medium` speaker `F` approved).** ID-collision with `03-component-spec.md` C-D-03 flagged in §2.7 for doc cleanup. | doc cleanup (separate commit) |
| C-D-05 | HA Assist pipeline timeout | D-1.5 / G-D5 prep |
| C-D-07 | Open WebUI Audio surface default for `qwen2.5` | D-1.7 |
| **(new)** D-D2-HTTP | HTTP-shim path of G-D2 (audio playback via `POST /v1/audio/speech`). Requires a **separate** OpenAI-compatible TTS container per C-D-06 closure — image candidate selection is C-D-09. | D-1.7 |
| **(new)** C-D-09 | Image candidate for the separate Piper OpenAI-compatible TTS shim container. Must speak the OpenAI `POST /v1/audio/speech` shape and consume the existing voice files at `/srv/homelab/data/piper/`. Parallel to the `fedirz/faster-whisper-server` posture for STT (R-D-13). | D-1.7 prep |
| **(carried)** D-D1-HTTP | HTTP-shim path of G-D1 (transcription via `POST /v1/audio/transcriptions`) | D-1.7 |
| **(carried)** Q-D-05 | Voice-originated entity actions are not currently written to `amarolab-audit.log` | D-2 |
| **(new)** D-D3-VOICE-SWAP | Reconcile `aurora-piper`'s startup `--voice` flag (currently `es_ES-davefx-medium`) with the AURORA voice identity (`es_ES-sharvard-medium` speaker `F`). Two viable mechanisms (see §2.7): (i) startup defaults via `--voice es_ES-sharvard-medium --speaker F` + container recreate (safer fallback, both flags confirmed present in wyoming-piper CLI); or (ii) per-request via HA Assist TTS slot (no recreate, **but requires verifying that HA's Wyoming integration exposes `speaker` as a per-request field — to confirm at D-1.5 prep**). | D-1.5 (HA Assist pipeline configuration) |

---

## 7. Reproducibility

The exact `docker run` command (§1.2), the
bind-mount preparation (§1.3), and the Wyoming probe
harness (§2.4) are sufficient to reproduce this
result on the same UM790 host. Image digest recorded
in §1.1 anchors the binary identity. Voice download
URLs are recorded in §1.1 for offline rebuilds.

---

## 8. Stop point

Per the user instruction, D-1.3 stops here. No
work has begun on:

- D-1.4 (openWakeWord)
- D-1.5 (HA Assist pipeline configuration)
- D-1.6 (real-device end-to-end / G-D5)
- D-1.7 (Open WebUI Audio integration + the deferred
  G-D1-HTTP and G-D2-HTTP halves)

The overview triad
(`00_overview/CURRENT_STATE.md`,
`AMAROLAB_HANDOFF.md`, `ROADMAP.md`) will be
updated at Phase D-1 closeout (D-1.9), not now —
per Lesson 005 ("harden then document" — overview
docs reflect the closed phase, not intermediate
milestones). The same discipline was applied at
D-1.2.
