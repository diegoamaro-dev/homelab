# openWakeWord Deployment — `aurora-wakeword`

- **Component:** Wake-word detection for AURORA
  (Amarolab Personal AI Assistant).
- **Status:** D-1.1 skeleton. **Not yet deployed.**
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

## 2. Container (planned)

| Container | Image | Purpose |
|---|---|---|
| `aurora-wakeword` | `rhasspy/wyoming-openwakeword:<TBD pinned tag>` | Wyoming wake-word |

Decision C-D-03 closes at D-1.4 execution.

---

## 3. Wake-word plan

| Phase | Wake word | Model | Notes |
|---|---|---|---|
| D-1 | `ok_nabu` | built-in | No training. Deployed so D-2 hardware plugs in cleanly. |
| D-2 candidate | `hey_aurora` | custom | Requires recorded samples + training. Out of scope for D-1. |

---

## 4. Configuration plan

| Setting | Value |
|---|---|
| Network | `ai-local_default` |
| Wyoming port | `10400/tcp` (internal) |
| Wake-word models | `ok_nabu` |
| Threshold | `0.5` (start) |
| Resource caps | `--cpus 1 --memory 512m` |
| Restart policy | `--restart unless-stopped` |
| Healthcheck | TCP probe on `10400` |

---

## 5. Env vars (names + intent only)

| Variable | Intent |
|---|---|
| `WAKEWORD_MODELS` | comma-separated list of models |
| `WAKEWORD_THRESHOLD` | detection threshold |
| `WAKEWORD_PRELOAD` | optional; force-load models at start |

---

## 6. docker run recipe — TO BE FILLED IN AT D-1.4

```bash
# Filled in at D-1.4.
# Must:
#  - run on ai-local_default
#  - NOT publish host ports
#  - apply resource caps
#  - use --restart unless-stopped
```

---

## 7. Validation — Gate G-D3

Spec in
[`../../../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md`](../../../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md)
§4.

**D-1-specific scope.** G-D3 verifies:

- HA UI lists openWakeWord as a wake-word provider.
- `ok_nabu` is selectable in the pipeline editor.
- A synthetic wake-word probe via `wyoming-cli`
  triggers a detection event in container logs.

G-D3 **does not** validate room-listening; that
requires hardware satellites.

---

## 8. Operational notes

| Topic | Note |
|---|---|
| Threshold tuning | If false-positives are seen during D-2 hardware bring-up, raise threshold incrementally. |
| Custom model training | `hey_aurora` requires ≈ 100 recorded "wake" samples and a larger negative set. Plan for a recording session in D-2 design. |
| Privacy | Audio frames sent to openWakeWord are short windows from the satellite; no audio is persisted. |
| Future RTX migration | openWakeWord stays on UM790 — always-on requirement. |

---

## 9. Related documents

- [`../wyoming/overview.md`](../wyoming/overview.md)
- [`../voice-satellites/hardware-options.md`](../voice-satellites/hardware-options.md)
- [`../../../04_ai_system/amarolab-v1/phase-d/03-component-spec.md`](../../../04_ai_system/amarolab-v1/phase-d/03-component-spec.md)
- [`../../../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md`](../../../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md)
- Apply log (D-1.4):
  `09_logs/2026-MM-DD_phaseD_wakeword_installed.md`
