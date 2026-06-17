# Piper Deployment — `aurora-piper`

- **Component:** TTS for AURORA (Amarolab Personal AI
  Assistant).
- **Status:** **DEPLOYED (Wyoming path) 2026-06-17**
  at D-1.3. `aurora-piper` running
  (`rhasspy/wyoming-piper:2.2.2`, startup-default
  voice `es_ES-davefx-medium`). Gate G-D2 Wyoming
  path passed (synthesis RTF 0.31, first chunk
  332 ms). HTTP-shim path deferred to D-1.7 — and
  will require a **separate** OpenAI-compatible TTS
  container (the `rhasspy/wyoming-piper:2.2.2` image
  is a pure Wyoming server with no built-in HTTP
  mode; C-D-06 closed at D-1.3 verification, image
  candidate is C-D-09). **AURORA voice identity
  decided post-G-D2 (C-D-08 closed 2026-06-17):
  `es_ES-sharvard-medium` speaker `F`** —
  operative through HA Assist TTS slot at D-1.5;
  container `--voice`/`--speaker` reconciliation is
  D-D3-VOICE-SWAP.
- **Phase D step:** D-1.3 (Wyoming) + D-1.7 (HTTP).

---

## 1. Purpose

Run Piper as a Wyoming endpoint (for HA Assist) and
front the same voice files with a separate
OpenAI-compatible HTTP shim (for Open WebUI). The
two containers share one voice cache on the host.

```
HA Assist  ──► aurora-piper (Wyoming :10200) ─────┐
                                                  ├── Piper voice files
Open WebUI ──► aurora-piper-http (HTTP :8001) ────┘     (/srv/homelab/data/piper/)
                ^ separate container, image TBD at D-1.7 (C-D-09)
```

---

## 2. Containers

| Container | Image | Purpose | Status |
|---|---|---|---|
| `aurora-piper` | `rhasspy/wyoming-piper:2.2.2` *(digest `sha256:c874e4…`)* | Wyoming TTS on `10200/tcp` (internal) | **deployed 2026-06-17 at D-1.3** |
| `aurora-piper-http` *(planned)* | **separate OpenAI-compatible TTS image** — TBD at D-1.7 prep (**C-D-09**) | OpenAI-compatible TTS on `8001/tcp` (internal), consuming the same voice cache at `/srv/homelab/data/piper/` | deferred to D-1.7 |

C-D-02 closed at D-1.3 — Wyoming image pinned to
`rhasspy/wyoming-piper:2.2.2`.

C-D-06 closed at D-1.3 — **the HTTP shim is a
separate container, not a built-in mode.** The
D-1.1 skeleton hypothesised a `--http-port`-style
flag on the Wyoming image; verification against
`rhasspy/wyoming-piper:2.2.2` showed that flag does
not exist. The image is a pure Wyoming server.
Image candidate selection for the separate shim is
C-D-09, deferred to D-1.7 prep.

---

## 3. Voice plan

| Voice | Locale | Quality | Speakers | Size | Use |
|---|---|---|---|---|---|
| **`es_ES-sharvard-medium` (speaker `F`)** | **Spanish (Spain)** | **medium** | **2 (M/F)** | **≈ 73 MB** | **AURORA voice identity — approved 2026-06-17 (C-D-08)** |
| `es_ES-davefx-medium` | Spanish (Spain) | medium | 1 (M) | ≈ 60 MB | Startup default on `aurora-piper` (G-D2 baseline); to be reconciled at D-1.5 (D-D3-VOICE-SWAP) |
| `en_US-libritts_r-medium` | English (US) | medium | many | ≈ 70 MB | Secondary / English replies — not pre-loaded in D-1 |

Voice candidates evaluated post-G-D2 (2026-06-17,
recorded in
[`../../../09_logs/2026-06-17_phaseD_piper_installed.md`](../../../09_logs/2026-06-17_phaseD_piper_installed.md)
§2.7):

| Voice | Disposition |
|---|---|
| `es_ES-sharvard-medium` speaker `F` | **APPROVED** — AURORA voice identity |
| `es_ES-sharvard-medium` speaker `M` | considered for sanity-check, not chosen |
| `es_ES-mls_10246-low` | not recommended — low quality + over-length on `¿…?` |
| `es_ES-mls_9972-low` | not recommended — same anomaly |
| `es_ES-carlfm-x_low` | not evaluated — male + x_low tier |

Non-Spain options (`es_AR-daniela-high`,
`es_MX-claude-high`) are out of scope for AURORA's
Spain-locale identity; revisit only if the Spain
constraint relaxes.

C-D-03 in this file referred historically to the
"voice alternative" decision and is **superseded by
C-D-08** in
[`../../../04_ai_system/amarolab-v1/phase-d/03-component-spec.md`](../../../04_ai_system/amarolab-v1/phase-d/03-component-spec.md).
A separate doc-cleanup commit will reconcile the
C-D-03 ID collision (component-spec §9 uses it for
"openWakeWord image pinned tag").

---

## 4. Configuration plan

| Setting | Value |
|---|---|
| Network | `ai-local_default` |
| Wyoming port | `10200/tcp` (internal) — active at D-1.3 |
| HTTP port | `8001/tcp` (internal) — **deferred to D-1.7** (no consumer until Open WebUI Audio) |
| Voice (startup default at D-1.3) | `es_ES-davefx-medium` *(G-D2 baseline; AURORA voice identity is `es_ES-sharvard-medium` speaker `F` per C-D-08 — reconciled operationally at D-1.5 via HA Assist TTS slot, D-D3-VOICE-SWAP)* |
| Length scale | `1.0` (natural pacing) |
| Bind mount | `/srv/homelab/data/piper/` → voice cache |
| Resource caps | `--cpus 1 --memory 1g` |
| Restart policy | `--restart unless-stopped` |
| Healthcheck | TCP probe on `10200` |

---

## 5. Configuration mechanism — CLI flags, not env vars

The original D-1.1 skeleton sketched `PIPER_*` env
vars; the rhasspy image **does not consume them**.
The image's entrypoint
(`/usr/src/docker_run.sh`) is:

```bash
exec .venv/bin/python3 -m wyoming_piper \
    --uri 'tcp://0.0.0.0:10200' \
    --data-dir /data "$@"
```

Settings are passed as CLI flags after the image name
and forwarded via `"$@"`:

| Flag | Value used at D-1.3 | Equivalent intent |
|---|---|---|
| `--voice` | `es_ES-davefx-medium` | voice identifier |
| `--length-scale` | `1.0` | pacing multiplier (natural) |
| `--noise-scale` | (image default) | naturalness knob |
| `--data-dir` | `/data` (set by entrypoint; bind-mounted to `/srv/homelab/data/piper`) | voice cache path |

---

## 6. docker run recipe — applied at D-1.3

Same discipline as Whisper: the executable recipe
lives in the apply log; this section reproduces the
exact command for browsing convenience.

```bash
docker run -d --name aurora-piper --restart unless-stopped \
  --network ai-local_default \
  -v /srv/homelab/data/piper:/data \
  --cpus 1 --memory 1g \
  rhasspy/wyoming-piper:2.2.2 \
  --voice es_ES-davefx-medium \
  --length-scale 1.0
```

Apply log:
[`../../../09_logs/2026-06-17_phaseD_piper_installed.md`](../../../09_logs/2026-06-17_phaseD_piper_installed.md).

---

## 7. Validation — Gate G-D2

Spec in
[`../../../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md`](../../../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md)
§3.

Summary:

1. Submit known text via Wyoming → audio plays.
   **Wyoming path passed at D-1.3** — `AURORA activada`
   synthesized in 335 ms wall-clock (RTF 0.31) at
   22 050 Hz / 16-bit / mono; WAV at
   `/srv/homelab/data/piper/gd2/aurora_activada.wav`
   for operator listening from the workstation.
2. Submit same text via HTTP shim → audio plays.
   **Deferred to D-1.7** (no HTTP consumer until then).
3. Voice is recognisably `es_ES-davefx-medium`.
   Operator listening verdict recorded in the D-1.3
   apply log §2.5.

---

## 8. Operational notes

| Topic | Note |
|---|---|
| Voice swap | Stop container, change the `--voice` CLI flag, recreate. New voice downloads from HuggingFace on first request and lands in `/srv/homelab/data/piper/`. |
| Multi-voice | The Wyoming Piper image catalogues the full upstream voice list; only voices whose ONNX weights have been downloaded into `/data` are usable for synthesis. D-1 sticks to one primary voice. |
| Latency | Measured at D-1.3 on UM790 (1 CPU cap): 332 ms time-to-first-chunk and 335 ms total wall-clock for 1 079 ms of audio (synthesis RTF 0.31). Well under the < 200 ms / short-utterance target after the first-chunk warm-up. |
| Stale image `EXPOSE` | `docker ps` shows `10400/tcp` for this image because the upstream `Dockerfile` carries a stale `EXPOSE 10400`. The actual server binds on `10200/tcp` per the entrypoint script — verified at D-1.3 by reading `/proc/net/tcp` inside the container. Treat the displayed port as cosmetic; HA Wyoming integration must point at `10200`. |
| Future RTX migration | Piper stays on UM790 — it must remain always-on, and CPU latency is already low. |

---

## 9. Related documents

- [`../wyoming/overview.md`](../wyoming/overview.md)
- [`../../../04_ai_system/amarolab-v1/phase-d/03-component-spec.md`](../../../04_ai_system/amarolab-v1/phase-d/03-component-spec.md)
- [`../../../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md`](../../../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md)
- Apply log (D-1.3):
  [`../../../09_logs/2026-06-17_phaseD_piper_installed.md`](../../../09_logs/2026-06-17_phaseD_piper_installed.md)
