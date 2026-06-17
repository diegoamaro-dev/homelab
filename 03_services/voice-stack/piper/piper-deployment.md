# Piper Deployment — `aurora-piper`

- **Component:** TTS for AURORA (Amarolab Personal AI
  Assistant).
- **Status:** D-1.1 skeleton. **Not yet deployed.**
- **Phase D step:** D-1.3.

---

## 1. Purpose

Run Piper as a Wyoming endpoint (for HA Assist) and
as an OpenAI-compatible HTTP endpoint (for Open
WebUI), sharing one voice cache.

```
HA Assist  ──► Wyoming :10200 ──┐
                                ├── Piper voice files
Open WebUI ──► HTTP    :8001 ───┘     (/srv/homelab/data/piper/)
```

---

## 2. Containers (planned)

| Container | Image | Purpose |
|---|---|---|
| `aurora-piper` | `rhasspy/wyoming-piper:<TBD pinned tag>` | Wyoming TTS |
| `aurora-piper-http` | TBD — either Piper's built-in mode or a separate OpenAI-compatible shim | OpenAI-compatible TTS |

Decision C-D-02 closes at D-1.3 execution. C-D-06
(built-in vs separate shim) also closes there.

---

## 3. Voice plan

| Voice | Locale | Quality | Size | Use |
|---|---|---|---|---|
| `es_ES-davefx-medium` | Spanish (Spain) | medium | ≈ 60 MB | Primary |
| `en_US-libritts_r-medium` | English (US) | medium | ≈ 70 MB | Secondary / English replies |

Alternative Spanish voices (to evaluate later, not in
D-1):

- `es_ES-sharvard-medium`
- `es_MX-claude-high`
- `es_ES-mls_10246-low`

Decision tracked as C-D-03; closes during G-D2 review.

---

## 4. Configuration plan

| Setting | Value |
|---|---|
| Network | `ai-local_default` |
| Wyoming port | `10200/tcp` (internal) |
| HTTP port | `8001/tcp` (internal) |
| Voice (primary) | `es_ES-davefx-medium` |
| Length scale | `1.0` (natural pacing) |
| Bind mount | `/srv/homelab/data/piper/` → voice cache |
| Resource caps | `--cpus 1 --memory 1g` |
| Restart policy | `--restart unless-stopped` |
| Healthcheck | TCP probe on `10200` |

---

## 5. Env vars (names + intent only)

| Variable | Intent |
|---|---|
| `PIPER_VOICE` | voice identifier (e.g., `es_ES-davefx-medium`) |
| `PIPER_LENGTH_SCALE` | pacing multiplier |
| `PIPER_NOISE_SCALE` | optional naturalness knob (default OK) |
| `PIPER_DATA_DIR` | path to bind-mounted voice cache |

---

## 6. docker run recipe — TO BE FILLED IN AT D-1.3

Same discipline as Whisper: recipe lives in the apply
log, not in this reference doc, to avoid drift.

```bash
# Filled in at D-1.3.
# Must:
#  - run on ai-local_default
#  - NOT publish host ports
#  - bind-mount /srv/homelab/data/piper/
#  - pass voice + length scale as env
#  - apply resource caps
#  - use --restart unless-stopped
```

---

## 7. Validation — Gate G-D2

Spec in
[`../../../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md`](../../../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md)
§3.

Summary:

1. Submit known text via Wyoming → audio plays.
2. Submit same text via HTTP shim → audio plays.
3. Voice is recognisably `es_ES-davefx-medium`.

---

## 8. Operational notes

| Topic | Note |
|---|---|
| Voice swap | Stop container, change `PIPER_VOICE`, recreate. New voice downloads on first request. |
| Multi-voice | Piper can host multiple voices in one container if the image supports it; D-1 sticks to one primary voice. |
| Latency | Piper is light on CPU; typically < 200 ms for short utterances on UM790. |
| Future RTX migration | Piper stays on UM790 — it must remain always-on, and CPU latency is already low. |

---

## 9. Related documents

- [`../wyoming/overview.md`](../wyoming/overview.md)
- [`../../../04_ai_system/amarolab-v1/phase-d/03-component-spec.md`](../../../04_ai_system/amarolab-v1/phase-d/03-component-spec.md)
- [`../../../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md`](../../../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md)
- Apply log (D-1.3):
  `09_logs/2026-MM-DD_phaseD_piper_installed.md`
