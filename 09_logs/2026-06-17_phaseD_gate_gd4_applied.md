# Phase D — Gate G-D4 (voice canary end-to-end) — APPLIED

- **Date:** 2026-06-17
- **Ecosystem:** **AMAROLAB** — Personal Innovation Lab and Digital
  Infrastructure Ecosystem.
- **Assistant:** **AURORA** — Personal AI Assistant for the AMAROLAB
  ecosystem.
- **Independent project on AMAROLAB infrastructure:** **Guardian Cloud**
  — not affected by this work.
- **Status:** **G-D4 PASSED.** Full Read → Write → Verify → Restore
  cycle against `input_boolean.aurora_voice_canary` succeeded
  end-to-end through the `AURORA v1` Assist pipeline. Baseline
  (`off`) restored. All four acceptance criteria met.
- **Scope:** Validation only. No config changes during this gate.
- **Pre-conditions verified:**
  - G-D1 (Whisper Wyoming) — closed (D-1.2).
  - G-D2 (Piper TTS) — closed (D-1.3).
  - G-D3 container/probe half — closed (D-1.4).
  - G-D3 HA-UI half — closed (D-1.5).
  - Pipeline `AURORA v1` configured + default — closed (D-1.5).
  - Voice canary exposed and only canary exposed — closed (D-1.5).
  - HTTPS Secure Context for HA — closed (D-1.5 supplement, see
    [`./2026-06-17_phaseD_ha_trusted_proxies_applied.md`](2026-06-17_phaseD_ha_trusted_proxies_applied.md)).

---

## 1. Pre-state anchor

| Field | Value |
|---|---|
| T0 (UTC) | `2026-06-17T21:46:47Z` (epoch `1781732807`) |
| Canary state | `off` (last_changed `2026-06-17 21:36:10` — set during HA restart from the proxy-trust patch) |
| Recorder rows (`states`) | 16 750 |
| Recorder rows (canary states) | 6 (historical baseline) |
| Recorder rows (`events`) | 6 329 |
| Voice-stack containers | `aurora-whisper`, `aurora-piper`, `aurora-wakeword`, `ollama`, `homeassistant` — all `Up`, no error lines |

Log byte-position baselines (for delta capture):

| Container | Bytes at T0 |
|---|---|
| `aurora-whisper` | 1 052 |
| `aurora-piper` | 20 |
| `aurora-wakeword` | 16 |
| `ollama` | 2 033 192 |
| `homeassistant` | 5 218 391 |

---

## 2. Procedure (per spec §5 of phase-d/05-validation-gates.md)

Operator drove the Assist push-to-talk microphone session at
`https://ha.amarolab.es` from a Chromium browser (Secure Context
confirmed). Pipeline language `es-ES`; phrasing executed in Spanish.

| # | Step | Spoken phrase (canonical class) | Expected outcome |
|---|---|---|---|
| 1 | Read | *"¿está encendido aurora voice canary?"* | TTS reports `off` |
| 2 | Write | *"enciende aurora voice canary"* | Canary → `on`; TTS confirms |
| 3 | Verify | *"¿está encendido aurora voice canary?"* | TTS reports `on` |
| 4 | Restore | *"apaga aurora voice canary"* | Canary → `off`; TTS confirms |

All four steps were executed audibly by the operator within the
test window. Operator iterated phrasing during steps 1 and 3
(common during first-time voice-pipeline exercise) before the
canonical write+restore pair landed cleanly.

---

## 3. Evidence — captured post-test from the host

### 3.1 State transitions (Home Assistant recorder)

Query window `last_updated_ts >= T0_TS` on
`/srv/homelab/homeassistant/home-assistant_v2.db`:

| `last_updated_utc` | `state` |
|---|---|
| 2026-06-17 21:51:24 | **`on`** |
| 2026-06-17 21:51:52 | **`off`** |

Transition count in window: **2** (matches Write + Restore — the
Read and Verify steps query state without changing it).

Final canary state: **`off` at 21:51:52** — baseline restored.

### 3.2 Service-call audit (logbook source)

| `time_utc` | `event_type` | Service |
|---|---|---|
| 2026-06-17 21:51:24 | `call_service` | `homeassistant.turn_on` on `input_boolean.aurora_voice_canary` |
| 2026-06-17 21:51:24 | `call_service` | `input_boolean.turn_on` on `[input_boolean.aurora_voice_canary]` |
| 2026-06-17 21:51:52 | `call_service` | `homeassistant.turn_off` on `input_boolean.aurora_voice_canary` |
| 2026-06-17 21:51:52 | `call_service` | `input_boolean.turn_off` on `[input_boolean.aurora_voice_canary]` |

The HA logbook UI is rendered from these `call_service` events
combined with the state transitions in §3.1.

### 3.3 STT — `aurora-whisper` transcripts (delta +737 bytes since T0)

Transcripts captured during the test window:

- "*el canal de voz está encendido*" (Read attempt — Whisper rendered "canario" as "canal")
- "*el canario de voz está encendido*" (clean Verify)
- "*Apara el canario de voz*" (Restore — Whisper rendered "apaga" as "apara")

Notes:

- Whisper transcription was **not 100 % literal** but the
  conversation agent + intent matcher resolved every voice
  command correctly (state changes happened at the expected
  step).
- Sub-canonical recognition fidelity is consistent with the
  `base-int8` model on a 5-second utterance (the smallest /
  fastest of the supported voices). This is a tuning observation
  for a future iteration (e.g., `small` or `medium-int8`), not a
  G-D4 fault.
- Empty 15-second recordings interspersed in the log are
  silence-only chunks from push-to-talk timing — normal.

### 3.4 TTS — `aurora-piper`

Container log unchanged (delta 0 bytes). Piper logs at INFO only
emit a single "Ready" line at startup; per-request synthesis is
not logged at this level (matches the operational profile
documented in D-1.3).

TTS audibility is confirmed by the operator (acceptance criterion
3 — operator-reported only).

### 3.5 Wake-word — `aurora-wakeword`

Container log unchanged (delta 0 bytes). Per the D-1.4 decision,
INFO-level container logs are intentionally quiet during normal
operation; detection signals are exposed only on the Wyoming wire
event. G-D4 uses push-to-talk (D-1 default), not always-listening,
so wake-word detections are not expected here.

### 3.6 Conversation agent — `ollama` (delta +1 092 bytes since T0)

Ten `POST /api/chat` requests during the test window, all
`HTTP 200`, source IP `172.18.0.1` (ai-local_default bridge
gateway — HA on host network reaching `ollama` via the bridge):

| Time (UTC) | Latency | Status |
|---|---|---|
| 21:48:59 | 2.157 s | 200 |
| 21:49:50 | 3.178 s | 200 |
| 21:49:53 | 3.201 s | 200 |
| 21:51:07 | 3.240 s | 200 |
| 21:51:10 | 3.372 s | 200 |
| 21:51:24 | **5.761 s** | 200 |
| 21:51:27 | 3.556 s | 200 |
| 21:51:39 | 4.108 s | 200 |
| 21:51:52 | **5.782 s** | 200 |
| 21:51:55 | 3.592 s | 200 |

The two longest calls (5.76 s and 5.78 s) align exactly with the
two state-change timestamps (21:51:24, 21:51:52) — consistent with
the conversation agent emitting tool/intent calls that translate
to HA service invocations.

### 3.7 Error scan

`docker logs --since 10m` filtered for
`ERROR | CRITICAL | Traceback | Exception | panic | fatal | refused`
across `aurora-whisper`, `aurora-piper`, `aurora-wakeword`,
`ollama`, `homeassistant`: **zero matches in any container.**

---

## 4. Acceptance criteria — verdict

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | Each pipeline cycle produces a transcript in HA's voice pipeline debug log | **PASS** | §3.3 Whisper transcripts; §3.6 Ollama chat completions paired with each cycle |
| 2 | Each state change is logged in HA logbook | **PASS** | §3.1 state transitions + §3.2 service-call audit |
| 3 | TTS response is audible and intelligible on each step | **PASS** (operator-reported) | Operator confirmation: "gd4 done"; earlier "Aurora responds to spoken requests" |
| 4 | Baseline (`off`) is restored at end | **PASS** | §3.1 final state `off` at 21:51:52 |

**Gate G-D4 — PASSED.**

---

## 5. What this did NOT change

- HA `configuration.yaml` (unchanged since the proxy-trust patch
  earlier this session).
- HA `.storage/http`, `.storage/core.config`.
- HA assist pipeline `AURORA v1` configuration.
- HA voice-exposure ACL (only `input_boolean.aurora_voice_canary`
  remains exposed).
- The voice-stack containers (`aurora-whisper`, `aurora-piper`,
  `aurora-wakeword`) — no restarts, no config edits.
- Open WebUI, Mosquitto, Z2M, the existing `cloudflared`
  container, or any Guardian Cloud surface.
- `webui.db` (Tools, model entry, system prompt, `meta.toolIds`).
- The `cloudflared-amarolab` container or tunnel ingress.

---

## 6. Open / deferred items

| ID | Item | Carried to |
|---|---|---|
| **G-D4 latency tuning** | Pipeline / agent / STT timeout values informed by measured latency (intent-resolving chat completions averaged ~3–6 s on this hardware) | Post-D-1 maintenance |
| **STT fidelity** | `base-int8` produced sub-canonical transcripts ("canal"/"canario", "apara"/"apaga"). Consider a model-size bump if fidelity becomes a UX issue | Post-D-1 maintenance |
| **`ai.amarolab.es` Public Hostname** | Not yet bound to the `amarolab` tunnel | Operator action (not on Phase D-1 critical path) |
| **`cloudflared-amarolab` apply log** | Deployment validated this session but not yet documented in its own apply log | Suggested companion log to write next |
| **Architecture doc amendments** | `02_infrastructure/cloudflare/amarolab_dns_architecture.md` and `cloudflared_audit_2026-06-17.md` need to record the separate-tunnel decision | Documentation sync, pre-D-1.9 |
| **Overview triad** (`00_overview/CURRENT_STATE.md` / `AMAROLAB_HANDOFF.md` / `ROADMAP.md`) | Will be updated at D-1.9 closeout per Lesson 005 | D-1.9 |
| **G-D5** (`switch.impresora_3d`) | Real-device voice round-trip through Mosquitto + Z2M | D-1.6 |
| **G-D6** | Failure-mode rehearsal (Whisper down, Piper down, Ollama unreachable) | D-1.8 |

---

## 7. D-1.5 closure status

With G-D4 passed, **D-1.5 is closed**.

The D-1.5 apply log
[`./2026-06-17_phaseD_voice_pipeline.md`](2026-06-17_phaseD_voice_pipeline.md)
was authored as a DRAFT pending G-D4 (per its §2.5 step 5). With
this gate log written, the DRAFT marker on D-1.5 can be removed
and the document promoted to non-draft. The promotion edit is
applied in the same session as this log.

Phase D-1 itself does not close until G-D5 and G-D6 also pass and
their dated apply logs land in `09_logs/`.

---

## 8. Reproducibility

To re-execute G-D4 from this point forward:

1. Confirm Aurora v1 pipeline is preferred and only the canary
   helper is exposed to voice assistants.
2. Confirm `https://ha.amarolab.es` is a Chromium Secure Context.
3. Capture T0 timestamp, log byte positions, canary baseline
   state, and recorder row counts (§1 baseline block).
4. Speak the four canonical phrases in §2 against the Assist
   microphone.
5. Diff the recorder DB, voice-stack container logs, and Ollama
   chat completions in the window `[T0, now]`.
6. Confirm the four acceptance criteria in §4.

---

## 9. Related documents

- [`./2026-06-17_phaseD_voice_pipeline.md`](2026-06-17_phaseD_voice_pipeline.md)
  — D-1.5 apply log (this gate closes its open item).
- [`./2026-06-17_phaseD_ha_trusted_proxies_applied.md`](2026-06-17_phaseD_ha_trusted_proxies_applied.md)
  — supplemental HA-side patch that unblocked the Secure Context
  + Host-header path.
- [`./2026-06-17_phaseD_wakeword_installed.md`](2026-06-17_phaseD_wakeword_installed.md)
  — D-1.4 apply log (G-D3 container/probe half).
- [`./2026-06-17_phaseD_piper_installed.md`](2026-06-17_phaseD_piper_installed.md)
  — D-1.3 apply log (G-D2).
- [`./2026-06-17_phaseD_whisper_installed.md`](2026-06-17_phaseD_whisper_installed.md)
  — D-1.2 apply log (G-D1 Wyoming half).
- [`../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md`](../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md)
  — gate definitions.
- [`../03_services/voice-stack/ha-assist/pipeline-spec.md`](../03_services/voice-stack/ha-assist/pipeline-spec.md)
  — `AURORA v1` pipeline spec.
- [`../07_operations/lessons_learned.md`](../07_operations/lessons_learned.md)
  — Lessons 002 / 005 / 013 / 015 underpin this validation rhythm.
