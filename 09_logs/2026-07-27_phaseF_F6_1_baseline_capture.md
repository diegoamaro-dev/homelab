# Phase F — F6.1 Prep — `aurora-whisper` Production-State Capture — APPLIED

**Date:** 2026-07-27
**Type:** Read-only capture. **No production change.** No container stopped, recreated or
modified; no image pulled; no model downloaded; no HA, `webui.db`, prompt or schema change.
**Phase step:** F6.1 preparation (operator-requested, ahead of any F6.1 implementation).
**Status:** This document + the referenced bundle are the **F6.1 rollback reference**.

---

## 1. Purpose

F6.1 recreates `aurora-whisper` with a larger STT model. Recreation destroys the live container,
and the F6.1 proposal established (Finding A) that **no committed apply log records the live
container's actual `docker run` recipe**: the D-1.2 log omits the loopback port publish that
Home Assistant depends on, and the D-1.5 log states the opposite of the live state.

This capture removes that gap. It records the deployed reality of `aurora-whisper` so the
container can be reconstructed byte-for-byte in its current configuration if F6.1 must roll back.

## 2. Bundle location

```
09_ops/runtime/f6_1_baseline_capture/
```

`09_ops/runtime/` is gitignored (`.gitignore:68`) — the raw bundle is runtime state, not
committed content. This document is the committed, sanitized record of it.

| File | Content |
|---|---|
| `MANIFEST.txt` | Index + sha256 of every bundle file + key values |
| `container_inspect.json` | **Full** `docker inspect aurora-whisper` |
| `image_inspect.json` | Full `docker image inspect rhasspy/wyoming-whisper:3.2.0` |
| `docker_run_equivalent.sh` | `docker run` equivalent **derived from** `container_inspect.json` |
| `model_cache_inventory.txt` | Every entry under the model root, with symlink targets and sizes |
| `model_files_sha256.txt` | sha256 of every regular file, paths relative, NUL-sorted |
| `model_dir_checksum.txt` | The above + the single `MODEL_DIR_SHA256` |
| `consumer_references.txt` | HA Wyoming config entries + Assist pipeline rows |
| `peers_inspect.json` / `peers_startedat.txt` | Sibling containers — isolation reference |
| `docker_ps.txt` | Host-wide container snapshot at capture time |

## 3. Captured state

### 3.1 Identity

| Field | Value |
|---|---|
| Container | `aurora-whisper` |
| Container ID | `db5946850fc3373eb27c704424e7a1c8752dd35f662a946ea8a475f0a87814fc` |
| Created | `2026-06-17T14:21:14Z` |
| Started (current) | `2026-07-25T21:50:55Z` |
| Image tag | `rhasspy/wyoming-whisper:3.2.0` |
| Image ID | `sha256:966e1b0967f398b81fa2273a96b2b940004fa1b77754f9ffda6b5689a58dd158` |
| Repo digest | `rhasspy/wyoming-whisper@sha256:966e1b0967f398b81fa2273a96b2b940004fa1b77754f9ffda6b5689a58dd158` |
| Image created | `2026-06-15T16:44:59Z` · amd64/linux |

The image ID matches the digest recorded at D-1.2 §1.1 — the running image is the one D-1.2
installed, unchanged.

### 3.2 Exact `docker run` equivalent (the rollback reference)

```bash
docker run -d \
  --name aurora-whisper \
  --restart unless-stopped \
  --network ai-local_default \
  -p 127.0.0.1:10300:10300 \
  -v /srv/homelab/data/whisper/wyoming:/data \
  --cpus 4 \
  --memory 4g \
  rhasspy/wyoming-whisper:3.2.0 \
  --model base-int8 \
  --language auto \
  --beam-size 1 \
  --compute-type int8
```

Derived from `container_inspect.json`, not transcribed from a prior log.

- `--entrypoint` is **not** overridden. The image default `["bash","docker_run.sh"]` applies and
  prepends `--uri tcp://0.0.0.0:10300 --data-dir /data`.
- `MemorySwap` on the live container is 8 GiB — Docker's implicit 2× default for `--memory 4g`,
  **not** an explicitly passed flag. Omitted above so the recipe reproduces the live state exactly.
- **`-p 127.0.0.1:10300:10300` is mandatory** — see §3.3 / §4.

### 3.3 Published ports, environment, mounts

| Aspect | Live value |
|---|---|
| Published ports | `127.0.0.1:10300 -> 10300/tcp` (loopback only; not LAN, not WAN) |
| Exposed (image) | `10300/tcp` |
| Environment | **No custom variables.** `Config.Env` carries only the image-default `PATH`. All configuration is CMD arguments |
| Mount | `/srv/homelab/data/whisper/wyoming` → `/data`, bind, **rw** |
| Network | `ai-local_default` (bridge) |
| Resource caps | `--cpus 4` (`NanoCpus=4000000000`), `--memory 4g` (`4294967296`) |
| Restart policy | `unless-stopped` |
| Healthcheck | none defined |

**Consumer binding.** Home Assistant runs on the host network; its Wyoming config entry
`faster-whisper` targets `{"host": "127.0.0.1", "port": 10300}`. The Assist pipeline `Aurora v1`
(preferred) uses `stt_engine: stt.faster_whisper`, `stt_language: es`. Dropping the port publish
breaks HA STT even though the container itself would start cleanly.

### 3.4 Model cache inventory

Root `/srv/homelab/data/whisper/wyoming` — HuggingFace cache layout, 4 regular files,
**79 582 442 bytes** (75.9 MiB).

| Path (relative to root) | Bytes | Role |
|---|---|---|
| `models--rhasspy--faster-whisper-base-int8/blobs/ae13f74d…a227081` | 79 120 341 | `model.bin` |
| `models--rhasspy--faster-whisper-base-int8/blobs/c9074644…4729461324b75` | 459 861 | `vocabulary.txt` |
| `models--rhasspy--faster-whisper-base-int8/blobs/e86f0ed3…7347a1a8153b` | 2 020 | `config.json` |
| `models--rhasspy--faster-whisper-base-int8/refs/main` | 40 | revision pointer |

Snapshot dir `snapshots/a9667415b1b62cc5f4bab65ec7a50f2f4035f7f4/` holds three symlinks
(`model.bin`, `vocabulary.txt`, `config.json`) into `blobs/`. Model revision = `a9667415…`.

The measured 75.9 MiB is **half** the ≈150 MB that
`03_services/voice-stack/whisper/faster-whisper-deployment.md` §7 estimates for `base-int8`;
that table's `small-int8` (≈480 MB) and `large-v3-int8` (≈1.6 GB) figures should therefore be
read as conservative ceilings, and replaced with measurements at F6.1.

### 3.5 Model directory checksum

```
MODEL_DIR_SHA256 = 2f8d05357575312f25b9a76e71e16cff6b672b864e2b8cf30e3202bd1d6dfb4e
FILE_COUNT       = 4
TOTAL_BYTES      = 79582442
MODEL_REVISION   = a9667415b1b62cc5f4bab65ec7a50f2f4035f7f4
```

**Method** (reproducible): sha256 of every regular file under the model root, paths relative and
NUL-sorted, then sha256 of that manifest. Symlinks are inventoried but not hashed — the blobs
they point to are. Re-running the method must reproduce `MODEL_DIR_SHA256` exactly; any
difference means the cache changed.

Verification, re-runnable at any time:

```bash
cd /srv/homelab/data/whisper/wyoming && find . -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum
```

Note: the `ae13f74d…` blob's filename equals its own content sha256 (HF LFS naming); the two
smaller blobs use git-blob SHA1 filenames, so their names differ from their content hashes. Both
are expected.

### 3.6 Isolation reference (must not change during F6.1)

| Container | `StartedAt` at capture |
|---|---|
| `aurora-whisper-http` | `2026-07-25T21:50:55.315880963Z` |
| `aurora-piper` | `2026-07-25T21:50:55.345817264Z` |
| `aurora-wakeword` | `2026-07-25T21:50:55.269189885Z` |
| `homeassistant` | `2026-07-25T21:50:55.363052101Z` |
| `openwebui` | `2026-07-27T13:12:23.119237709Z` |

## 4. Findings confirmed by this capture

- **Finding A confirmed.** The live container publishes `127.0.0.1:10300:10300`; the D-1.2 recipe
  does not contain it. Reproducing D-1.2 verbatim would leave HA STT unreachable. The recipe in
  §3.2 supersedes it operationally. Historical logs are **not** rewritten
  (`PROJECT_RULES` → Historical Documentation); this record carries the correction.
- **Finding B refined — a startup-time network dependency exists on *every* start, including
  rollback.** On `2026-07-21T17:46:01Z` the container failed 5× to fetch
  `openai/whisper-tiny/…/tokenizer.json` from `huggingface.co` (`Temporary failure in name
  resolution`) and reached `Ready` at `17:46:24Z` — **23.1 s** of retry backoff, then a clean
  start. So the fetch is **non-fatal**, but a rollback to `base-int8` also performs it and can be
  slow when container egress is down. The model cache itself is complete (§3.4) and does not need
  the network.
- **`/srv/homelab/data/whisper` is not in restic coverage** (`07_operations/backups.md` §Coverage).
  The cache cannot be restored from backup — only re-downloaded. The blobs listed in §3.4 must
  never be deleted during F6.1.

## 5. Rollback procedure enabled by this capture

1. `docker stop aurora-whisper && docker rm aurora-whisper`
2. Re-run §3.2 verbatim.
3. Verify: Wyoming describe reports `model name=base-int8`; `MODEL_DIR_SHA256` unchanged;
   one canary round-trip through `Aurora v1`; canary restored to `off`.
4. Verify isolation: §3.6 `StartedAt` values unchanged; `ai.amarolab.es` voice unaffected.

Recovery time is seconds — the weights are already cached; allow up to ~25 s extra if container
egress is down (§4).

## 6. Validation of this capture

| Check | Result |
|---|---|
| Bundle integrity | Every file sha256'd in `MANIFEST.txt` |
| `MODEL_DIR_SHA256` reproducible | Recomputed and matched during capture |
| Recipe derived, not transcribed | Generated from `container_inspect.json` |
| Production untouched | No `docker stop/rm/run/pull/exec`; `StartedAt` for `aurora-whisper` unchanged before/after |
| Secrets | None present — the container declares **no** custom environment variables (§3.3) |

## 7. Stop point

F6.1 implementation has **not** started. No container was touched. The next step is operator
review of the F6.1 execution plan.

## 8. Git gate

Documentation-only. Committed 2026-07-27 on explicit operator approval per `PROJECT_RULES` →
Operator Git Approval. **Not pushed** — origin update is a separate operator decision requiring
its own fresh approval. **STOP at git gate.**
