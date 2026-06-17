# faster-whisper Deployment — `aurora-whisper`

- **Component:** STT for AURORA (Amarolab Personal AI
  Assistant).
- **Status:** D-1.1 skeleton. **Not yet deployed.**
  This document captures the deployment **plan**; the
  apply log under `09_logs/` will record the executed
  recipe and validation evidence.
- **Phase D step:** D-1.2.

---

## 1. Purpose

Run faster-whisper as a Wyoming endpoint (for HA
Assist) and as an OpenAI-compatible HTTP endpoint
(for Open WebUI), sharing one model cache.

```
HA Assist  ──► Wyoming :10300 ──┐
                                ├── faster-whisper model files
Open WebUI ──► HTTP    :8000 ───┘     (/srv/homelab/data/whisper/)
```

---

## 2. Containers (planned)

| Container | Image | Purpose |
|---|---|---|
| `aurora-whisper` | `rhasspy/wyoming-whisper:<TBD pinned tag>` | Wyoming STT |
| `aurora-whisper-http` | `fedirz/faster-whisper-server:<TBD pinned tag>` | OpenAI-compatible STT |

Decision C-D-01 (image tag for Wyoming) and the HTTP
shim tag close at D-1.2 execution.

---

## 3. Configuration plan

| Setting | Value |
|---|---|
| Network | `ai-local_default` |
| Wyoming port | `10300/tcp` (internal) |
| HTTP port | `8000/tcp` (internal) |
| Model | `base-int8` (initial) |
| Language | auto-detect (D-1); pin during G-D5 prep |
| Beam size | 1 |
| Compute type | `int8` (CPU-only) |
| Bind mount | `/srv/homelab/data/whisper/` → model cache |
| Resource caps | `--cpus 4 --memory 4g` |
| Restart policy | `--restart unless-stopped` |
| Healthcheck | TCP probe on `10300`; HTTP `/health` on `8000` |

---

## 4. Env vars (names + intent only — no values)

| Variable | Intent |
|---|---|
| `WHISPER_MODEL` | model size identifier |
| `WHISPER_LANGUAGE` | language hint, default `auto` |
| `WHISPER_BEAM_SIZE` | decoding beam |
| `WHISPER_COMPUTE_TYPE` | `int8` for CPU |
| `WHISPER_CACHE_DIR` | path to bind-mounted model cache |

Per Lesson 001: env changes require `docker rm` +
`docker run`, not `docker restart`.

---

## 5. docker run recipe — TO BE FILLED IN AT D-1.2

The recipe is intentionally NOT written until the
operator is ready to execute, so it does not drift
between doc and reality. Recipe template:

```bash
# Filled in at D-1.2.
# Must:
#  - run on ai-local_default
#  - NOT publish host ports
#  - bind-mount /srv/homelab/data/whisper/
#  - pass model + language as env
#  - apply resource caps
#  - use --restart unless-stopped
```

The committed apply log
(`09_logs/2026-MM-DD_phaseD_whisper_installed.md`)
will contain the exact executed command, image
digest, and the G-D1 validation evidence.

---

## 6. Validation — Gate G-D1

Acceptance criteria and procedure live in
[`../../../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md`](../../../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md)
§2.

Summary:

1. Submit a 5 s WAV via Wyoming → expect matching
   transcript.
2. Submit the same WAV via the HTTP shim → expect
   matching transcript.
3. Capture latency for both paths.

---

## 7. Operational notes (planned)

| Topic | Note |
|---|---|
| Model swap | Stop container, change `WHISPER_MODEL`, recreate. Model files download on first request. |
| Disk usage | `base-int8` ≈ 150 MB; `small-int8` ≈ 480 MB; `large-v3-int8` ≈ 1.6 GB. Plan disk before swapping. |
| CPU pressure | If G-D1 latency exceeds threshold (TBD), revisit C-D-04 (model-size decision). |
| Future RTX migration | Same image, same env, different host. See [`../../../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md`](../../../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md). |

---

## 8. Related documents

- [`../wyoming/overview.md`](../wyoming/overview.md)
- [`../../../04_ai_system/amarolab-v1/phase-d/03-component-spec.md`](../../../04_ai_system/amarolab-v1/phase-d/03-component-spec.md)
- [`../../../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md`](../../../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md)
- Apply log (to be created at D-1.2):
  `09_logs/2026-MM-DD_phaseD_whisper_installed.md`
