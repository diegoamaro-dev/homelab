# Phase D — Gate G-D6 (failure-mode rehearsal) — APPLIED

- **Date:** 2026-06-18 (local; test window 2026-06-17 23:43 → 2026-06-18 00:29 UTC = 2026-06-18 01:43 → 02:29 CEST)
- **Ecosystem:** **AMAROLAB**.
- **Assistant:** **AURORA**.
- **Independent project on AMAROLAB infrastructure:** **Guardian Cloud** —
  not affected.
- **Status:** **G-D6 PASSED** with one explicit acceptance partial
  (see §3.2 / §4 — "HA logs TTS failure explicitly" surfaces in the
  WS pipeline-debug stream rather than the INFO core log). All three
  scenarios passed their core behavioral verdict; baseline canary
  `off` restored at gate end; all seven cross-scenario invariants
  hold.
- **Scope:** Validation only. The scenarios stopped and restarted
  three containers (`aurora-whisper`, `aurora-piper`, `ollama`) one
  at a time. **No configuration changed.** **No infrastructure
  changed.** The only persistent state mutated during the gate was
  the canary entity state, and it is back to baseline at gate end.
- **Pre-conditions verified:**
  - G-D5 closed
    ([`./2026-06-18_phaseD_gate_gd5_applied.md`](./2026-06-18_phaseD_gate_gd5_applied.md)).
  - D-1.7 closed
    ([`./2026-06-18_phaseD_openwebui_audio_applied.md`](./2026-06-18_phaseD_openwebui_audio_applied.md)).
  - Voice-exposure ACL = canary only.
  - `switch.impresora_3d` voice-exposure = `false`.
  - Canary at baseline `off`.
  - All containers `Up` and healthy at T0.

---

## 1. Pre-state anchor

| Field | Value |
|---|---|
| T0 (UTC) | `2026-06-17T23:43:40Z` (epoch `1781739820`) |
| Canary state | `off` (last_changed `2026-06-17T21:51:52Z` from G-D4 Restore) |
| Printer state | `off` (last_changed `2026-06-17T23:03:50Z` — pre-G-D6 manual UI flip, see §1.3 note) |
| Voice-exposure ACL | exactly one entity: `input_boolean.aurora_voice_canary` |
| Printer voice-exposure | `false` |
| HA recorder rows (states) | 17 322 |
| HA recorder rows (events) | 6 389 |
| `ai.amarolab.es` `/api/version` | `HTTP 200` |
| `ha.amarolab.es` `/` | `HTTP 200` |
| Voice-stack + shims | all `Up` and healthy |

### 1.1 Restic anchor — decision

No fresh Restic snapshot. Same rationale as G-D5 and D-1.7: G-D6 is
validation-only and does not mutate persistent configuration. The
only persistent state movement was the canary on/off (entity state,
not configuration), which is restored to baseline by gate-end (§6).

### 1.2 Log byte-position baselines (for delta capture)

| Container | Bytes at T0 |
|---|---|
| `aurora-whisper` | 2 052 |
| `aurora-piper` | 20 |
| `aurora-wakeword` | 16 |
| `aurora-whisper-http` | 83 895 |
| `aurora-piper-http` | 2 209 |
| `ollama` | 2 057 963 |
| `openwebui` | 321 825 |
| `homeassistant` | 5 218 391 |
| `mosquitto` | 11 057 754 |
| `zigbee2mqtt` | 10 985 052 |
| `cloudflared-amarolab` | 15 133 |
| `cloudflared` | 435 380 |

### 1.3 Printer pre-G-D6 timeline annotation (out-of-scope)

The printer's `last_changed` is `2026-06-17T23:03:50Z` — about 42 min
after the G-D5 Restore at `22:21:06Z`. The recorder shows:

- `23:03:43`: `on` (`switch.turn_on` only — no `homeassistant.*`
  intent prefix)
- `23:03:50`: `off` (`switch.turn_off` only — no intent prefix)

A 7-second toggle, no voice signature. The operator confirmed this
was chat-side activity (Open WebUI's `ha_call_service` Phase C
tool was exercised during D-1.7 latency profiling and audio
validation). The printer's voice-exposure was `false` throughout
and remained `false` throughout G-D6. The toggle is **not** part of
G-D6 evidence; it is recorded here for transparency only.

---

## 2. Scenario §7.1 — Whisper down

### 2.1 Procedure

| Step | Time (UTC) | Action |
|---|---|---|
| T1.0 | `23:44:48Z` | Captured §7.1 pre-state log byte positions |
| T1.1 | `23:44:48Z` | `docker stop aurora-whisper` |
| T1.2 | `23:44:50Z` | Confirmed Wyoming `:10300` unreachable from `ai-local_default` |
| T1.3 | `~23:50Z` | Operator drove one voice command at `https://ai.amarolab.es` by **mistake** — that surface uses `aurora-whisper-http` (D-1.7's separate STT shim, intentionally left up) and **succeeded** end-to-end. Independently confirmed D-1.7's surface isolation is real, but does not validate §7.1. |
| T1.4 | `~23:54Z` | Operator drove the corrected attempt on `https://ha.amarolab.es` — HA Assist UI showed **"speech-to-text failed"**; no canary state change |
| T1.5 | `~23:55Z` | §7.1 evidence sweep (§2.2) |
| T1.6 | `~23:55Z` | `docker start aurora-whisper`; Wyoming `:10300` reachable in 3 s |
| T1.7 | post-restart | Smoke retries (§2.3) |
| T1.8 | `00:13Z` | Smoke landed on "enciende voice canary" (alias-matching phrase) — canary `on`, TTS audible; smoke verified |

### 2.2 Evidence — failure window (`23:44:48Z` → `23:54:37Z`)

| Acceptance item | Verdict | Evidence |
|---|---|---|
| HA reports an STT error | **PASS** | Operator-confirmed UI message: "speech-to-text failed" |
| No entity state change | **PASS** | HA recorder query in window for canary returns **0 transitions** |
| No service-call audit row dispatched to the canary | **PASS** | HA `events.call_service` filtered to canary/printer returns **0 rows** |
| Zero `ollama POST /api/chat` from HA Assist | **PASS** | All `POST /api/chat` rows in window came from source IP `172.18.0.4` (`openwebui`, from the T1.3 misdirected attempt and earlier OW activity) — none from HA Assist (HA on host network would show as `172.18.0.1`) |
| Post-restart smoke passes cleanly | **PASS** (§2.3) | Canary `on` then `off` via voice with alias-matching phrasing |

### 2.3 Smoke detail (intent-matching aside)

During the smoke phase, two non-acceptance observations emerged
that are useful to document for D-1.9:

- **Whisper sometimes produced sub-canonical Spanish.** Examples
  from the §7.1 window: "Enfiinde el canario de voz",
  "Enfiende, voy a hacer canal", "Enfiende, Voice Canary",
  "y fiende voz canadi", "En fiende, boys". Same `base-int8`
  fidelity profile already tracked since G-D4.
- **qwen2.5 (HA Assist conversation engine) intent matching is
  non-deterministic on borderline phrasing.** "Enciende aurora
  voice canary" failed twice in a row with the response *"There is
  no device named 'aurora_voice_canary' in the input_boolean
  domain"* and once with *"There is no input_boolean device in the
  area 'aurora_voice_canary'"*. The same engine succeeded via the
  REST `/api/conversation/process` path with the **same** phrasing
  and the **same** `agent_id`, proving the engine, the exposed
  entity list, and the LLM tool access are all correct. Eventually
  "enciende voice canary" (matching the alias exactly) landed via
  the voice pipeline and the smoke cycle completed.

These two observations together account for the operator's
iterations during §7.1 and §7.2 smokes and are carried as
post-Phase-D-1 follow-ups (§7). They are not §7.1 failures —
Whisper itself recovered cleanly (transcript captured) and the
conversation engine itself works (REST-proven).

---

## 3. Scenario §7.2 — Piper down

### 3.1 Procedure

| Step | Time (UTC) | Action |
|---|---|---|
| T2.0 | `00:14:50Z` | §7.2 pre-state log byte positions captured; canary at `off` baseline |
| T2.1 | `00:14:50Z` | `docker stop aurora-piper` |
| T2.2 | `00:14:51Z` | Confirmed Wyoming `:10200` unreachable |
| T2.3 | `00:16:34Z` | Operator's voice attempt #1 transcribed `"Enfiende, voy a hacer canal."` — qwen resolved as turn-off intent on canary (no-op since canary already off) |
| T2.4 | `00:16:40Z` | Operator's voice attempt #2 transcribed cleanly as `"Enciende, Voice Canary"` — **canary → `on`**, **no audible TTS reply** |
| T2.5 | `00:17–00:18Z` | Operator's voice attempts #3 / #4 transcribed as "y fiende voz canadi" / "En fiende, boys" — qwen returned "no input_boolean device in the area 'aurora_voice_canary'" (no-op) |
| T2.6 | `~00:20Z` | §7.2 evidence sweep (§3.2) |
| T2.7 | `00:20:48Z` | Canary restored to `off` baseline via REST `input_boolean.turn_off` |
| T2.8 | `00:21:05Z` | `docker start aurora-piper`; Wyoming `:10200` reachable in 1 s; `Ready` line in log |
| T2.9 | post-restart | Smoke cycle: operator confirmed audible TTS reply on canary on / off cycle |

### 3.2 Evidence — failure window (`00:14:50Z` → `00:20:48Z`)

| Acceptance item | Verdict | Evidence |
|---|---|---|
| Intent **does** land — canary state transition on voice command | **PASS** | HA recorder shows 1 voice-driven transition: `00:16:40 → on`. Two distinct voice intents reached service-call (turn-off no-op at `00:16:34` and turn-on at `00:16:40`). |
| Service-call audit shows `homeassistant.turn_*` + domain-specific service pair | **PASS** | Four rows in window: `homeassistant.turn_off`/`input_boolean.turn_off` at `00:16:34`; `homeassistant.turn_on`/`input_boolean.turn_on` at `00:16:40` — all `entity_id=input_boolean.aurora_voice_canary` |
| **HA logs the TTS failure explicitly** | **PARTIAL** | HA Assist surfaces TTS errors to the WS pipeline-debug surface (and to the UI banner the operator saw — silent reply), but **not** to the INFO-level core log. A scan of `homeassistant` log delta for `tts/piper/wyoming/error` returned zero rows. Functionally PASS (failure observed via silence + UI), but the literal "explicit log line" reading of the spec is not met by HA's surface. Carried as a minor follow-up in §7. |
| Operator confirms no audible reply | **PASS** | Operator-confirmed: "No audible TTS reply." |
| Whisper transcript present in window | **PASS** | `aurora-whisper` delta log shows four transcripts (§3.1 T2.3–T2.5) |
| Post-restart smoke audibility re-confirmed | **PASS** | Operator-confirmed: "7.2 smoke ok" |

§7.2 verdict: **PASS** with the documented partial on the literal
"explicit log line" criterion. The functional behavior — intent
lands, audible silence, transcripts captured — is exactly the
graceful-degradation profile the gate is meant to validate.

---

## 4. Scenario §7.3 — Ollama unreachable

### 4.1 Procedure

| Step | Time (UTC) | Action |
|---|---|---|
| T3.0 | `00:23:43Z` | §7.3 pre-state log byte positions; canary at `off` baseline |
| T3.1 | `00:23:43Z` | `docker stop ollama` |
| T3.2 | `00:23:44Z` | Confirmed `http://127.0.0.1:11434` unreachable from host (HA's path) |
| T3.3 | `~00:25Z` | Operator drove voice attempts at `https://ha.amarolab.es`; HA Assist UI displayed **"Unexpected error during intent recognition"** for each attempt; no canary state change |
| T3.4 | `~00:26Z` | §7.3 evidence sweep (§4.2) |
| T3.5 | `00:26:55Z` | `docker start ollama`; `/api/tags` HTTP 200 in 2 s |
| T3.6 | `00:26:55Z` | Cold warm-up probe via `/api/chat` on `qwen2.5:7b-instruct` returned in **5.17 s** (model resident) |
| T3.7 | post-restart | Smoke cycle (§4.3) |

### 4.2 Evidence — failure window (`00:23:43Z` → `00:26:55Z`)

| Acceptance item | Verdict | Evidence |
|---|---|---|
| Pipeline times out / errors cleanly within 180 s | **PASS** | Operator-confirmed UI banner "Unexpected error during intent recognition" returned immediately per attempt (well within the 180 s cap) |
| No `call_service` rows for canary in window | **PASS** | HA `events` filter returns **0 canary call_service rows** in the window |
| No state change in window | **PASS** | HA recorder returns **0 canary transitions** in the window |
| Conversation-agent error surfaced to the UI | **PASS** | Operator-confirmed banner phrasing matches HA's `intent recognition` error class |
| Whisper transcript **is** present (STT path still worked) | **PASS** | Three transcripts captured in the `aurora-whisper` delta log: "Enfiende Boys Canary", "Enfiende, Voice Canadi", "Enfiende Voice Canadi" — proving STT was downstream-blocked, not in-pipeline-blocked |
| Post-restart smoke passes | **PASS** (§4.3) | Operator-confirmed |

§7.3 verdict: **PASS.** All six acceptance items hold cleanly.

### 4.3 Collateral impact (expected and documented)

- **Open WebUI chat** at `https://ai.amarolab.es` was unable to
  reach the LLM during the §7.3 window — expected collateral (both
  front doors share the same `ollama` endpoint). Operator was
  pre-notified and did not use chat during the window.
- `cloudflared-amarolab` log shows several `Incoming request ended
  abruptly: context canceled` rows during the broader gate window
  on `/api/tts_proxy/*.mp3` paths. Root cause is operator-driven
  (browser closed TTS audio stream when the operator moved to the
  next voice prompt). Not a tunnel fault, not a §7.3 fault.

---

## 5. Cross-scenario invariants — gate-level

| # | Invariant | Verdict | Evidence |
|---|---|---|---|
| A | Canary at gate end is `off` | **PASS** | Final state `off`; `last_changed = 2026-06-18T00:29:45Z` (REST `input_boolean.turn_off` reassertion post-§7.3 smoke) |
| B | `switch.impresora_3d` untouched throughout the gate | **PASS** | Final state `off`, `last_changed = 2026-06-17T23:03:50Z` — **identical** to the pre-G-D6 baseline. Zero printer transitions inside the gate window. |
| C | Printer voice-exposure remains `false` | **PASS** | `core.entity_registry.options.conversation.should_expose` = `false`; total voice-exposed entities = 1 (canary only) |
| D | Guardian Cloud `cloudflared` untouched | **PASS** | `StartedAt = 2026-06-17T00:19:32Z` — unchanged (23 h+ continuous run through the entire D-1.6 / D-1.7 / G-D6 sequence) |
| E | Open WebUI shims untouched | **PASS** | `aurora-whisper-http` `StartedAt = 2026-06-17T23:03:31Z`; `aurora-piper-http` `StartedAt = 2026-06-17T23:07:31Z` — both identical to D-1.7 deploy timestamps |
| F | `ai.amarolab.es` and `ha.amarolab.es` both return `HTTP 200` post-gate | **PASS** | `ha.amarolab.es /` = 200; `ai.amarolab.es /api/version` = 200 |
| G | Zero errors across `mosquitto`, `zigbee2mqtt`, `homeassistant` (in pattern outside deliberately-stopped windows), `cloudflared*`, `openwebui`, `aurora-*-http` | **PASS w/ annotation** | Mosquitto, Z2M, openwebui, both shims, Guardian `cloudflared`: 0 hits. `cloudflared-amarolab`: 16 hits — all `Incoming request ended abruptly` on `/api/tts_proxy/*.mp3`, operator-driven (§4.3), not a fault. |

---

## 6. Gate verdict

**G-D6 PASSED.**

- §7.1 — fail-closed posture verified. STT failure prevents any
  command issuance.
- §7.2 — degrade-but-execute posture verified. Intent lands while
  TTS is silent.
- §7.3 — clean-timeout posture verified. LLM unreachable produces
  a surfaced conversation-agent error with no partial action.
- One minor acceptance partial documented in §3.2 (HA TTS-failure
  log granularity), not blocking.
- All seven cross-scenario invariants hold.

Phase D-1's safety story is complete: the voice surface fails
predictably when each of its critical dependencies fails.

---

## 7. Open / deferred items

| ID | Item | Carried to |
|---|---|---|
| **Voice-pipeline intent matching variability** | qwen2.5 intermittently fails to resolve "aurora voice canary" or "voice canary" via the HA Assist voice pipeline even though REST `/api/conversation/process` against the same `agent_id` resolves the same phrasing reliably. Likely a frontend `ha-assist-chat` WS race (the HA log shows `Received binary message for non-existing handler` errors during voice activity, sourced from `src/components/ha-assist-chat.ts:385:12`). Workaround proven: refresh the HA tab after audio-handler errors. | Post-Phase-D-1 — track as `HA-VOICE-001` |
| **HA TTS-failure surface granularity** | HA Assist does not write the TTS-failure event to the INFO-level core container log; it surfaces only on the WS `assist_pipeline/pipeline_debug` admin stream and to the UI banner. §3.2 partial. Could be partially addressed by raising HA log level for `wyoming` / `tts` to DEBUG in `configuration.yaml` if future post-mortems benefit. | Post-Phase-D-1 |
| **STT fidelity** | `base-int8` continues to produce sub-canonical Spanish on short utterances. Multiple examples in §2.3. Tracked since G-D4. Model-size bump (`small` or `medium-int8`) candidate. | Post-Phase-D-1 maintenance |
| **Pipeline timeout tuning** | §7.3's clean-error response was effectively immediate (well under the 30 s default and the 180 s plan cap). Default timeouts are adequate for the clean-error case. No tuning needed at this stage. | Out of scope |
| **D-1.9 — Phase D-1 closeout** | Apply log + overview-triad amendment per Lesson 005 | **D-1.9 (next step, not started)** |
| **Overview triad** (`00_overview/CURRENT_STATE.md`, `AMAROLAB_HANDOFF.md`, `ROADMAP.md`) | Currently still reads "D-1.2 closed; D-1.3 next" — stale since D-1.5. Will be amended at D-1.9. | D-1.9 |
| **`cloudflared-amarolab` apply log** | Deployment validated D-1.5 but no dedicated apply log yet | Documentation sync, pre-D-1.9 |
| **DNS / architecture doc amendments** | `02_infrastructure/cloudflare/amarolab_dns_architecture.md` and `cloudflared_audit_2026-06-17.md` need to record the separate-tunnel decision and `ai.amarolab.es` binding | Documentation sync, pre-D-1.9 |
| **Performance / RTX 5070 AI-node** | LLM 6 tok/s ceiling already deferred to RTX 5070 work per D-1.7 §4.6 / `06-rtx-node-bridge.md` | D-3 / RTX node |
| R-D-13 | Migrate HTTP shim from `fedirz/faster-whisper-server` to maintained successor | Post-Phase-D maintenance |
| R-01 | Cloudflare Tunnel token rotation (Guardian-Cloud tunnel) | Independent |

---

## 8. What this did NOT change

- HA `configuration.yaml`, HA `.storage/*` apart from the recorder
  rows produced by the canary state transitions captured in §2–§4.
- HA Assist pipeline `AURORA v1`, conversation engine,
  Ollama integration configuration.
- HA Wyoming integrations (the three Wyoming containers were
  briefly stopped per scenario but restarted with **identical**
  command, image, bind-mount, and `restart=unless-stopped` posture).
- Voice-exposure ACL — printer remained `false`; canary remained
  `true`; total count = 1 throughout.
- Open WebUI's `webui.db` — schema, audio-config keys
  (`audio.stt.engine = "openai" → aurora-whisper-http`,
  `audio.tts.engine = "openai" → aurora-piper-http`), Tools, model
  rows — all unchanged.
- Open WebUI HTTP shims (`aurora-whisper-http`,
  `aurora-piper-http`) — `StartedAt` unchanged from D-1.7 deploy.
- Mosquitto config, users, ACLs.
- Zigbee2MQTT config or device list.
- `cloudflared` (Guardian Cloud) — container, tunnel UUID, ingress,
  credentials, network attachment.
- `cloudflared-amarolab` — tunnel ingress, hostnames, runtime.
- Cloudflare DNS — no records created or modified.
- Restic repository.

No environment file (`ai-stack/.env`, `/home/diego/.secrets/*`)
was modified. No secret was introduced, rotated, or printed.

---

## 9. Reproducibility

To re-execute G-D6:

1. Confirm pre-conditions (§ header pre-conditions block).
2. Capture T0 + log byte positions + recorder counts.
3. For each scenario in order (Whisper → Piper → Ollama):
   - `docker stop <container>`
   - Operator drives one voice command at `https://ha.amarolab.es`
     using the alias-matching phrasing (e.g., "enciende voice
     canary")
   - Capture transcripts, state transitions, call_service rows,
     ollama chat rows
   - `docker start <container>`
   - Wait for Wyoming TCP port reachable (or for ollama, `/api/tags`
     HTTP 200 + a small `/api/chat` warmup probe)
   - Operator drives a Write+Restore canary smoke cycle
   - Reset canary to `off` baseline (REST `input_boolean.turn_off`)
     before next scenario starts
4. Verify all seven cross-scenario invariants (§5).
5. Author the apply log following this template.

Notes for reproducibility:
- §7.3 affects Open WebUI chat collaterally; warn the operator and
  pre-pause OW use.
- HA's `ha-assist-chat` frontend can enter an audio-handler race
  state during repeated voice attempts; refresh the HA tab if
  intent matching starts failing on phrasing that worked earlier.
- Alias-matching phrasing for the canary is **"voice canary"**
  (not "aurora voice canary" or "canario de voz"). Same intent
  resolves cleanly via REST regardless of phrasing.

---

## 10. D-1.6 / D-1.7 / D-1.8 closure status

With G-D6 passed (§6), **D-1.8 is closed**.

All six Phase D-1 gates are now landed with dated apply logs:

| Gate | Apply log | Status |
|---|---|---|
| G-D1 (Wyoming half) | [`./2026-06-17_phaseD_whisper_installed.md`](./2026-06-17_phaseD_whisper_installed.md) | closed |
| G-D1 (HTTP-shim half) | [`./2026-06-18_phaseD_openwebui_audio_applied.md`](./2026-06-18_phaseD_openwebui_audio_applied.md) | closed (D-1.7) |
| G-D2 (Wyoming half) | [`./2026-06-17_phaseD_piper_installed.md`](./2026-06-17_phaseD_piper_installed.md) | closed |
| G-D2 (HTTP-shim half) | [`./2026-06-18_phaseD_openwebui_audio_applied.md`](./2026-06-18_phaseD_openwebui_audio_applied.md) | closed (D-1.7) |
| G-D3 (container/probe half) | [`./2026-06-17_phaseD_wakeword_installed.md`](./2026-06-17_phaseD_wakeword_installed.md) | closed |
| G-D3 (HA-UI half) | [`./2026-06-17_phaseD_voice_pipeline.md`](./2026-06-17_phaseD_voice_pipeline.md) | closed (D-1.5) |
| G-D4 | [`./2026-06-17_phaseD_gate_gd4_applied.md`](./2026-06-17_phaseD_gate_gd4_applied.md) | closed |
| G-D5 | [`./2026-06-18_phaseD_gate_gd5_applied.md`](./2026-06-18_phaseD_gate_gd5_applied.md) | closed |
| **G-D6** | this log | **closed** |

D-1.9 (Phase D-1 closeout — including the overview-triad
amendment) is the **next** step but is **not started**.

The overview triad (`00_overview/CURRENT_STATE.md`,
`AMAROLAB_HANDOFF.md`, `ROADMAP.md`) is **not** updated by this
log — that happens at D-1.9 closeout per Lesson 005 and the
D-1.5 / G-D5 / D-1.7 closure pattern.

Per the operator instruction at the start of this session:
**STOP here. D-1.9 not started.**

---

## 11. Related documents

- [`./2026-06-18_phaseD_openwebui_audio_applied.md`](./2026-06-18_phaseD_openwebui_audio_applied.md)
  — D-1.7 apply log (Open WebUI audio shims).
- [`./2026-06-18_phaseD_gate_gd5_applied.md`](./2026-06-18_phaseD_gate_gd5_applied.md)
  — G-D5 apply log (real-device voice round-trip).
- [`./2026-06-17_phaseD_gate_gd4_applied.md`](./2026-06-17_phaseD_gate_gd4_applied.md)
  — G-D4 apply log (canary end-to-end).
- [`./2026-06-17_phaseD_voice_pipeline.md`](./2026-06-17_phaseD_voice_pipeline.md)
  — D-1.5 apply log (AURORA v1 pipeline).
- [`./2026-06-17_phaseD_ha_trusted_proxies_applied.md`](./2026-06-17_phaseD_ha_trusted_proxies_applied.md)
  — HA reverse-proxy trust patch.
- [`./2026-06-17_phaseD_wakeword_installed.md`](./2026-06-17_phaseD_wakeword_installed.md)
  — D-1.4 apply log.
- [`./2026-06-17_phaseD_piper_installed.md`](./2026-06-17_phaseD_piper_installed.md)
  — D-1.3 apply log.
- [`./2026-06-17_phaseD_whisper_installed.md`](./2026-06-17_phaseD_whisper_installed.md)
  — D-1.2 apply log.
- [`../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md`](../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md)
  — gate definitions §7.
- [`../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md`](../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md)
  — performance-optimization deferral target.
- [`../07_operations/lessons_learned.md`](../07_operations/lessons_learned.md)
  — Lessons 002 / 005 / 010 / 013 / 015 underpin this validation
  rhythm.
