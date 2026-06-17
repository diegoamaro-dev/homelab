# openWakeWord Deployment — `aurora-wakeword`

- **Component:** Wake-word detection for AURORA
  (Amarolab Personal AI Assistant).
- **Status:** **Deployed** (D-1.4, 2026-06-17).
  Container/probe half of Gate G-D3 closed; HA-UI
  half deferred to D-1.5.
- **Phase D step:** D-1.4.

---

## 1. Purpose

Provide a wake-word detector via Wyoming so that
future hardware satellites (D-2+) can stream
audio to it and trigger HA Assist on detection.

**Phase D-1 note.** D-1's primary satellite is the
operator's workstation browser, which uses
**push-to-talk** rather than always-listening. The
wake-word container is deployed so the system surface
is ready for D-2 hardware — its G-D3 acceptance is a
**configuration probe**, not an end-to-end
always-listening test.

---

## 2. Container

| Container | Image | Purpose |
|---|---|---|
| `aurora-wakeword` | `rhasspy/wyoming-openwakeword:2.1.0` | Wyoming wake-word |

Image manifest digest (local, host-resolved):
`sha256:52cb1168731a1849fc28cf339c935fde58746bbabc94226668a40ef6ddf5d42b`.

Docker Hub `last_updated`: `2025-10-28T15:14:47Z`
(`:latest` aliased to the same image at selection
time). Decision **C-D-03 closed at D-1.4** — see
`09_logs/2026-06-17_phaseD_wakeword_installed.md`.

---

## 3. Wake-word plan

| Phase | Wake word | Model | Notes |
|---|---|---|---|
| D-1 | `okay_nabu` | built-in (`okay_nabu.tflite`) | No training. Deployed so D-2 hardware plugs in cleanly. **Name is `okay_nabu`** (image reality — the Wyoming `Info` payload advertises this exact name; the D-1.1 sketch using `ok_nabu` was corrected at D-1.4). |
| D-2 candidate | `hey_aurora` | custom | Requires recorded samples + training. Out of scope for D-1. A future `hey_aurora.tflite` dropped into `/srv/homelab/data/wakeword/` will be discovered by the running container without a redeploy (the bind mount is the `--custom-model-dir`). |

---

## 4. Configuration (applied)

| Setting | Value |
|---|---|
| Network | `ai-local_default` |
| Wyoming port | `10400/tcp` (internal; **not** host-published). Matches the image `EXPOSE` directive — verified at D-1.4. |
| Bind mount | `/srv/homelab/data/wakeword` → `/custom_models` (rw). Empty in D-1; D-2 plug-in point for `hey_aurora.tflite`. |
| Wake-word models | Built-ins advertised by the running image: `okay_nabu`, `hey_jarvis`, `hey_mycroft`, `alexa`, `hey_rhasspy` (all `installed=true`). HA Assist client selects `okay_nabu` at D-1.5 pipeline configuration. |
| Threshold | `0.5` (image default; passed explicitly to `--threshold` for documentation clarity) |
| Trigger-level | `1` (image default; minimum) |
| Refractory seconds | image default (`2`); not overridden |
| Zeroconf | **off** (no `--zeroconf` flag — no mDNS advertisement on `ai-local_default`) |
| Resource caps | `--cpus 1 --memory 512m` |
| Restart policy | `--restart unless-stopped` |
| Healthcheck | Validation-time TCP probe on `10400`; no custom Docker `HEALTHCHECK` directive (mirrors D-1.2 / D-1.3 precedent) |
| Ready signal | `INFO:root:Ready` (logger name is `root`, not `__main__`) |

---

## 5. Configuration is CLI flags, not env vars

The D-1.1 deployment-doc skeleton listed
`WAKEWORD_MODELS=ok_nabu`, `WAKEWORD_THRESHOLD=0.5`,
`WAKEWORD_PRELOAD` as env vars. **The running image
does not consume any `WAKEWORD_*` env vars.**
Verified at D-1.4 by inspecting `Config.Env` and by
reading the image's entrypoint script:

```bash
$ docker inspect rhasspy/wyoming-openwakeword:2.1.0 \
    --format '{{json .Config.Env}}'
["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"]
```

```
$ cat /usr/src/docker_run.sh   # inside the image
#!/usr/bin/env bash
cd /usr/src
.venv/bin/python3 -m wyoming_openwakeword \
    --uri 'tcp://0.0.0.0:10400' "$@"
```

The configuration knobs are exposed via CLI flags
only. Available flags (from
`python -m wyoming_openwakeword --help` inside the
image):

| Flag | Purpose | Default |
|---|---|---|
| `--uri` | Wyoming bind URI | hardcoded to `tcp://0.0.0.0:10400` by `docker_run.sh` |
| `--custom-model-dir` | Path to directory with custom `.tflite` files; can be passed multiple times | none |
| `--threshold` | Per-model probability threshold (0.0–1.0) | `0.5` |
| `--trigger-level` | Number of consecutive above-threshold frames before emitting Detection | `1` |
| `--refractory-seconds` | Cooldown after a detection | `2` |
| `--zeroconf [NAME]` | Advertise over mDNS | off |
| `--debug` | Enable DEBUG-level logging | off |
| `--log-format` | Python logging format string | image default |
| `--version` | print version | — |
| `--model`, `--models-dir`, `--preload-model`, `--output-dir`, `--debug-probability` | **Deprecated**; do not use | — |

Same Lesson-003 (reality wins) shape as D-1.3 made
for `rhasspy/wyoming-piper` and `PIPER_*` env vars.

---

## 6. `docker run` recipe (applied)

```bash
# Bind-mount prep
mkdir -p /srv/homelab/data/wakeword
chmod 755 /srv/homelab/data/wakeword

# Container create
docker run -d --name aurora-wakeword --restart unless-stopped \
  --network ai-local_default \
  -v /srv/homelab/data/wakeword:/custom_models \
  --cpus 1 --memory 512m \
  rhasspy/wyoming-openwakeword:2.1.0 \
  --custom-model-dir /custom_models \
  --threshold 0.5 \
  --trigger-level 1
```

Notes:

- **Mount path is `/custom_models`, not `/data`.** This
  image has no `--data-dir` flag — built-in models
  live read-only inside the image; the bind mount is
  specifically `--custom-model-dir`. Mounting at
  `/custom_models` makes the role visible at
  `docker inspect` time. The bind-mount path on the
  host (`/srv/homelab/data/wakeword`) preserves
  symmetry with `aurora-whisper` / `aurora-piper` in
  the host's filesystem layout.
- **Internal-only.** No `-p` / host port published —
  same posture as `aurora-whisper` and `aurora-piper`.
- **No `--zeroconf`** — no mDNS advertisement on
  `ai-local_default`.
- **No `--debug`** — INFO-level logging is the
  production posture; detection events are emitted
  on the Wyoming wire, not in container logs (see §7).

---

## 7. Validation — Gate G-D3

Spec in
[`../../../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md`](../../../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md)
§4.

G-D3 is **split** between D-1.4 (container/probe
half — closed by this deployment) and D-1.5 (HA-UI
half — open).

**Container/probe half — closed at D-1.4
(2026-06-17).**

- Wyoming `Describe` probe confirms `openwakeword`
  program is installed and advertises `okay_nabu` +
  4 other built-ins.
- Synthetic-detection probe streaming an
  operator-recorded 2.539 s WAV of "Okay Nabu" elicits
  a `Detection(name="okay_nabu", timestamp=2010)`
  Wyoming event on the wire.
- Zero errors in `aurora-wakeword` container logs.
- Apply log:
  [`../../../09_logs/2026-06-17_phaseD_wakeword_installed.md`](../../../09_logs/2026-06-17_phaseD_wakeword_installed.md).

**HA-UI half — deferred to D-1.5.** HA Settings →
Voice assistants must list openWakeWord; `okay_nabu`
must be selectable in the HA Assist pipeline editor.
Carried as **D-D4-G-D3-HA-UI** in the D-1.4 apply
log §6.

**Reality-wins clarification on the "logs a
detection" criterion.** The image's INFO-level
logger does not emit a per-detection log line —
`wyoming_openwakeword`'s detection-side debug
lines are gated behind `--debug`. The authoritative
server-side signal is the Wyoming `Detection` event
on the wire, captured by the probe. The validation
spec was updated alongside the D-1.4 apply log to
make this explicit; **no container recreate, no
`--debug` flag**.

G-D3 **does not** validate room-listening; that
requires hardware satellites (D-2).

---

## 8. Operational notes

| Topic | Note |
|---|---|
| Threshold tuning | If false-positives are seen during D-2 hardware bring-up, raise threshold incrementally above `0.5`. |
| Trigger-level tuning | Raising `--trigger-level` above `1` reduces false-positives at the cost of slower detection. D-2 hardware bring-up may want `2`. |
| Custom model training | `hey_aurora` requires ≈ 100 recorded "wake" samples and a larger negative set. Plan for a recording session in D-2 design. The trained `.tflite` will drop into `/srv/homelab/data/wakeword/` and be picked up by the running container without redeploy. |
| Privacy | Audio frames sent to openWakeWord are short windows from the satellite; no audio is persisted by the container. |
| Future RTX migration | openWakeWord stays on UM790 — always-on requirement, low compute, no benefit from GPU acceleration. |
| Backup coverage | `/srv/homelab/data/wakeword/` is **not yet** in the nightly `homelab-backup.sh` path list (the list was frozen at R-12 / 2026-06-13 and predates the voice stack). Extending it is carried as **R-D-14** in the D-1.4 apply log §6. |

---

## 9. Related documents

- [`../wyoming/overview.md`](../wyoming/overview.md)
- [`../voice-satellites/hardware-options.md`](../voice-satellites/hardware-options.md)
- [`../../../04_ai_system/amarolab-v1/phase-d/03-component-spec.md`](../../../04_ai_system/amarolab-v1/phase-d/03-component-spec.md)
- [`../../../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md`](../../../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md)
- Apply log (D-1.4):
  [`../../../09_logs/2026-06-17_phaseD_wakeword_installed.md`](../../../09_logs/2026-06-17_phaseD_wakeword_installed.md)
