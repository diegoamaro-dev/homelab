# Phase D — Gate G-D5 (real-device voice end-to-end) — APPLIED

- **Date:** 2026-06-18 (local; test window 2026-06-17 22:20 UTC = 2026-06-18 00:20 CEST)
- **Ecosystem:** **AMAROLAB** — Personal Innovation Lab and Digital
  Infrastructure Ecosystem.
- **Assistant:** **AURORA** — Personal AI Assistant for the AMAROLAB
  ecosystem.
- **Independent project on AMAROLAB infrastructure:** **Guardian Cloud**
  — not affected by this work.
- **Status:** **G-D5 PASSED**, with a transparent procedural
  simplification. The full Read → Write → Verify → Restore voice
  sequence in the spec was **not** fully spoken; G-D5 as executed was
  a **Write → Restore physical-device voice validation** against
  `switch.impresora_3d`. Final baseline `off` restored. Full
  Mosquitto + Z2M + Sonoff S60ZBTPF round-trip confirmed for both
  voice transitions. The printer's voice-exposure ACL was reverted
  to `false` immediately after the cycle.
- **Scope:** Validation only. No infrastructure or configuration
  mutation. The only persistent change during the gate window was
  the temporary voice-exposure ACL toggle on
  `switch.impresora_3d`, reverted by the operator before this log
  was authored.
- **Pre-conditions verified:**
  - G-D1 (Whisper Wyoming) — closed (D-1.2).
  - G-D2 (Piper TTS) — closed (D-1.3).
  - G-D3 container/probe half — closed (D-1.4).
  - G-D3 HA-UI half — closed (D-1.5).
  - G-D4 (canary end-to-end) — closed (see
    [`./2026-06-17_phaseD_gate_gd4_applied.md`](2026-06-17_phaseD_gate_gd4_applied.md)).
  - `AURORA v1` Assist pipeline is the HA default / preferred
    pipeline — closed (D-1.5).
  - HTTPS Secure Context for HA over `https://ha.amarolab.es` —
    closed (D-1.5 supplement, see
    [`./2026-06-17_phaseD_ha_trusted_proxies_applied.md`](2026-06-17_phaseD_ha_trusted_proxies_applied.md)).
  - `switch.impresora_3d` temporarily exposed to voice for the test
    window (operator HA UI toggle); no other entity added to the
    voice surface beyond the canary.

---

## 1. Pre-state anchor

| Field | Value |
|---|---|
| T0 (UTC) | `2026-06-17T22:11:18Z` (epoch `1781734278`) |
| `switch.impresora_3d` state at T0 | `off` (last_changed `2026-06-17T21:48:28Z`, the HA restart from the trusted-proxies patch — no manual flip) |
| `input_boolean.aurora_voice_canary` state at T0 | `off` (last_changed `2026-06-17T21:51:52Z` from G-D4 Restore) |
| HA recorder rows (`states`) | 16 878 |
| HA recorder rows (`events`) | 6 350 |
| Recorder rows (printer states) | 27 (historical baseline) |
| Recorder rows (canary states) | 8 (historical baseline) |
| Voice-exposure ACL at T0 | exactly one entity — the canary. `switch.impresora_3d` `should_expose = false` |
| Z2M `bridge/state` (retained) | `{"state":"online"}` |
| Voice-stack containers | `aurora-whisper`, `aurora-piper`, `aurora-wakeword`, `ollama`, `homeassistant`, `mosquitto`, `zigbee2mqtt`, `cloudflared-amarolab` — all `Up`, no error lines in prior 24 h |
| HA errors in prior 24 h | **0** |

### 1.1 Restic anchor

**No fresh Restic snapshot was taken for this gate.** Rationale:

- G-D5 is validation-only against an already-known Zigbee switch
  state. No infrastructure or configuration was mutated.
- The only persistent change made during the gate was the temporary
  voice-exposure ACL toggle on `switch.impresora_3d`. That toggle is
  fully reversible through the same HA UI (and was reverted post-
  test — see §3.11).
- The rollback condition for the gate was "restore
  `switch.impresora_3d` to `off`". That condition was met by the
  voice Restore step at 22:21:06 UTC and re-verified via HA REST
  GET after the operator revoked exposure.
- The system-wide Restic repository on the 2 TB USB disk remains
  the broader recovery anchor (last full snapshot from the D-1.5
  apply window, snapshot `63c072f4`, is still in the repo and
  unchanged).

Per Lesson 010 ("backups are only real after restoration testing"),
the gate's reversibility was provided by entity state rather than
by file-system rollback, which is the appropriate granularity for a
validation-only step.

### 1.2 Log byte-position baselines (for delta capture)

| Container | Bytes at T0 |
|---|---|
| `aurora-whisper` | 1 789 |
| `aurora-piper` | 20 |
| `aurora-wakeword` | 16 |
| `ollama` | 2 034 284 |
| `homeassistant` | 5 218 391 |
| `mosquitto` | 11 057 754 |
| `zigbee2mqtt` | 10 479 443 |

---

## 2. Procedure — deviation from spec §6

The spec procedure
([`../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md`](../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md)
§6) defines a 4-exchange Read → Write → Verify → Restore voice cycle
against `switch.impresora_3d`.

**As executed, G-D5 was simplified to Write → Restore.** Two voice
utterances were spoken against the HA Assist push-to-talk microphone
at `https://ha.amarolab.es` from a Chromium browser (Secure Context
confirmed). Pipeline language `es-ES`.

| # | Spoken phrase | Step | Expected outcome |
|---|---|---|---|
| 1 | *"Enciende la impresora 3D"* | Write | Plug → `on`; TTS confirms |
| 2 | *"Apaga la impresora 3D"* | Restore | Plug → `off`; TTS confirms |

The Read and Verify state-query exchanges were **deliberately not
spoken**. Operator-stated rationale:

> The query path of the pipeline (intent classification, conversation
> agent, TTS response) was already proven against the canary in G-D4.
> G-D5 was scoped down to the state-mutating half so the real-device
> physical round-trip (Mosquitto + Z2M + Sonoff S60ZBTPF) could be
> exercised once without re-litigating the read path.

This is honest framing: **G-D5 demonstrates voice Write + voice
Restore physical-device round-trip**, not the full Read → Write →
Verify → Restore template. The query exchanges are carried as a
non-blocking completeness item (§6).

### 2.1 Out-of-scope manual UI toggle pair (transparency note)

The HA recorder also records a transition pair at `22:20:02 → on`
and `22:20:05 → off` (a 3-second toggle), **before** the voice
cycle began. This pair is **not** part of G-D5 voice evidence:

- No Whisper transcript for the corresponding window.
- No `ollama` `POST /api/chat` for the corresponding window.
- The service-call audit shows only `switch.turn_on` /
  `switch.turn_off` with **no** `homeassistant.turn_*` intent prefix
  — i.e., not dispatched by the conversation agent.

The operator confirmed this was a manual UI sanity-check toggle
performed after exposing the printer to voice and before driving
the voice utterances. It is reported here for completeness and is
**not counted** as G-D5 voice evidence in §4.

---

## 3. Evidence — captured post-test from the host

### 3.1 Voice-driven state transitions (Home Assistant recorder)

Query window `last_updated_ts >= T0_TS` on
`/srv/homelab/homeassistant/home-assistant_v2.db`, filtered to the
voice-attributable transitions:

| `last_updated_utc` | `state` | Step |
|---|---|---|
| 2026-06-17 22:20:37 | **`on`** | Write (voice) |
| 2026-06-17 22:21:06 | **`off`** | Restore (voice) |

Voice-driven transition count in window: **2** (matches Write +
Restore).

Final printer state: **`off` at 22:21:06** — baseline restored.

### 3.2 Service-call audit (logbook source)

Voice-driven calls only:

| `time_utc` | `event_type` | Service |
|---|---|---|
| 2026-06-17 22:20:37 | `call_service` | `homeassistant.turn_on` on `switch.impresora_3d` |
| 2026-06-17 22:20:37 | `call_service` | `switch.turn_on` on `[switch.impresora_3d]` |
| 2026-06-17 22:21:06 | `call_service` | `homeassistant.turn_off` on `switch.impresora_3d` |
| 2026-06-17 22:21:06 | `call_service` | `switch.turn_off` on `[switch.impresora_3d]` |

The `homeassistant.turn_*` prefix is the conversation-agent → intent
dispatch signature, identical to the G-D4 pattern against the
canary.

Out-of-scope manual UI pair (not voice — included for full
auditability, not counted in §4):

| `time_utc` | `event_type` | Service |
|---|---|---|
| 2026-06-17 22:20:02 | `call_service` | `switch.turn_on` on `switch.impresora_3d` |
| 2026-06-17 22:20:05 | `call_service` | `switch.turn_off` on `switch.impresora_3d` |

### 3.3 STT — `aurora-whisper` transcripts (delta +263 bytes)

Transcripts captured in the test window:

| Step | Whisper transcript |
|---|---|
| Write | *"Enciende la impresora 3D."* |
| Restore | *"Apaga la impresora 3D."* |

Both transcripts were canonical — zero STT slop. Same `base-int8`
model and the same RTF profile as G-D1 / G-D4. (G-D4 had observed
sub-canonical renderings such as "canario" → "canal" and "apaga" →
"apara" on the canary; G-D5 saw none of that on the printer.)

### 3.4 TTS — `aurora-piper`

Container log delta **0 bytes**. Piper at INFO logs a single
`Ready` line at startup; per-request synthesis is not logged at
this level (matches the operational profile from D-1.3 and G-D4).

TTS audibility for both voice exchanges confirmed by the operator
(acceptance criterion 5 — operator-reported only).

### 3.5 Wake-word — `aurora-wakeword`

Container log delta **0 bytes**. Push-to-talk pipeline (D-1
default) does not exercise the wake-word path, so silent INFO logs
are expected.

### 3.6 Conversation agent — `ollama` (delta +364 bytes)

Four `POST /api/chat` requests during the test window, all
`HTTP 200`, source IP `172.18.0.1` (ai-local_default bridge gateway
— HA on host network reaching `ollama` via the bridge):

| Time (UTC) | Latency | Correlation |
|---|---|---|
| 22:20:37 | **19.418 s** | Write intent processing — correlates with `switch.impresora_3d` → `on` |
| 22:20:41 | 3.927 s | Write response generation (TTS prompt) |
| 22:21:06 | **7.465 s** | Restore intent processing — correlates with `switch.impresora_3d` → `off` |
| 22:21:10 | 3.674 s | Restore response generation |

The two state-mutating intents (22:20:37, 22:21:06) align exactly
with the recorder transitions in §3.1.

The Write intent's 19.4 s latency is notably higher than the 3–6 s
band seen across G-D4 (10 chat completions averaged ~3.8 s). The
Restore intent at 7.5 s is also above the G-D4 band but closer to
it. The most likely cause is a cold-model warmup — this was the
first conversation-agent call into `ollama` in ~28 minutes (last
G-D4 completion at 21:51:55, first G-D5 completion at 22:20:37).
The Restore call 30 seconds later landed at less than half the
latency, consistent with that hypothesis. Carried as a non-blocking
observation in §6.

### 3.7 Z2M MQTT round-trip — `zigbee2mqtt` (delta +84 672 bytes)

The Z2M log is dominated by the device's periodic telemetry
(voltage, current, power, linkquality, OTA status). Filtering to
`state` field transitions only (deduped):

| Z2M timestamp (local CEST) | UTC | `state` | Notes |
|---|---|---|---|
| 2026-06-18 00:20:02 | 2026-06-17 22:20:02 | `ON` | Manual UI flip — out of scope |
| 2026-06-18 00:20:05 | 2026-06-17 22:20:05 | `OFF` | Manual UI flip — out of scope |
| **2026-06-18 00:20:37** | **2026-06-17 22:20:37** | **`ON`** | **Voice Write** |
| **2026-06-18 00:21:06** | **2026-06-17 22:21:06** | **`OFF`** | **Voice Restore** |

Z2M timestamps for both voice-driven transitions match the HA
recorder timestamps to the second. **Full physical round-trip
confirmed**: voice → HA STT → conversation agent → intent →
`switch.turn_*` → HA-side MQTT publish → Mosquitto → Z2M → Sonoff
S60ZBTPF → Z2M state publish → HA state update via MQTT discovery.

### 3.8 Mosquitto

Container log delta **0 bytes**. Zero authorization failures, zero
connection errors during the window. The hardened broker continued
to serve `homeassistant` + `zigbee2mqtt` under per-user ACLs as
expected — the auth-hardening posture from 2026-06-17 is preserved
end-to-end through G-D5.

### 3.9 Error scan

`docker logs --since 15m` filtered for
`ERROR | CRITICAL | Traceback | Exception | panic | fatal | refused`
across `aurora-whisper`, `aurora-piper`, `aurora-wakeword`,
`ollama`, `homeassistant`, `mosquitto`, `zigbee2mqtt`,
`cloudflared-amarolab`: **zero matches in any container**.

### 3.10 Guardian Cloud isolation

| Container | Status | StartedAt |
|---|---|---|
| `cloudflared` (Guardian Cloud) | running | `2026-06-17T00:19:32Z` (untouched 22 h+ before G-D5) |
| `cloudflared-amarolab` | running | `2026-06-17T21:19:16Z` (untouched since D-1.5) |

Guardian Cloud's surface, tunnel, network attachment, and runtime
were unaffected by G-D5. The two cloudflared instances continued to
serve their separated tunnels — `cloudflared` on `cloudflare-net`
for Guardian Cloud, `cloudflared-amarolab` on `ai-local_default`
for AMAROLAB infrastructure.

### 3.11 Voice-exposure ACL — pre / post

Read directly from `.storage/core.entity_registry`:

| Entity | Pre-test `should_expose` | Post-test `should_expose` |
|---|---|---|
| `input_boolean.aurora_voice_canary` | `true` | `true` (unchanged) |
| `switch.impresora_3d` | `false` | **`false` (operator revoked after voice cycle)** |
| every other entity | n/a or `false` | n/a or `false` (unchanged) |

Post-test count of `should_expose = true` entities: **1** (canary
only). No other entity was exposed at any point during G-D5. The
printer's exposure was opened only for the duration of the voice
cycle and was closed before this log was authored.

---

## 4. Acceptance criteria — verdict

Per spec §6:

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | All four voice exchanges complete within the pipeline timeout | **PARTIAL → PASS as scoped** — only the two state-mutating voice exchanges (Write, Restore) were spoken; both completed cleanly through STT → conversation agent → intent → service → TTS. The Read and Verify query exchanges were deliberately skipped (procedure §2). The query path is independently proven by G-D4. | §3.3, §3.6 |
| 2 | HA logbook records both state transitions | **PASS** | §3.1 + §3.2 (voice-driven rows only) |
| 3 | Z2M MQTT publishes both transitions on `zigbee2mqtt/Impresora 3D` | **PASS** | §3.7 (voice-driven `state` field transitions) |
| 4 | Physical plug state restored to baseline (`off`) | **PASS** | §3.1 final state `off` at 22:21:06; HA REST GET post-test confirms `off` |
| 5 | HA voice pipeline log shows the cycles cleanly | **PASS for the two cycles driven** | 1:1:1 cross-correlation in §3.3 (transcript) ↔ §3.6 (chat completion) ↔ §3.1 (state transition) for both voice exchanges; zero errors in §3.9 |

**Gate G-D5 — PASSED** as a **Write → Restore physical-device voice
validation**. The voice → real Zigbee switch round-trip is proven
end-to-end through the AURORA v1 pipeline, the hardened Mosquitto
broker, Z2M, and the Sonoff S60ZBTPF plug. The optional Read /
Verify voice exchanges are carried as a non-blocking completeness
item (§6).

---

## 5. What this did NOT change

- HA `configuration.yaml`.
- HA `.storage/http`, `.storage/core.config`,
  `.storage/assist_pipeline.pipelines`,
  `.storage/homeassistant.exposed_entities` (the in-memory exposure
  was toggled and reverted — no net delta to disk for unrelated
  entities).
- HA Ollama integration or model assignment.
- HA Wyoming integrations (Whisper, Piper, openWakeWord).
- The `AURORA v1` pipeline definition or its `preferred_item`
  status.
- `input_boolean.aurora_voice_canary` — state, alias, exposure all
  unchanged.
- Any other entity's voice-exposure ACL (only `switch.impresora_3d`
  was temporarily toggled, then reverted).
- Voice-stack containers (`aurora-whisper`, `aurora-piper`,
  `aurora-wakeword`) — no restarts, no config edits.
- `ollama` container or model store.
- Open WebUI — no Audio config, no `webui.db` schema, no Tools, no
  `qwen2.5` model row.
- `/srv/homelab/data/openwebui/amarolab-audit.log`.
- Mosquitto config, users, ACLs (hardened posture preserved).
- Zigbee2MQTT config or device list.
- `cloudflared` (Guardian Cloud) — container, tunnel, ingress,
  credentials, network attachment.
- `cloudflared-amarolab` — tunnel ingress, hostnames, runtime.
- Cloudflare DNS — no records created or modified.
- Restic repository — no new snapshot taken; see §1.1 rationale.

No environment file (`ai-stack/.env`, `/home/diego/.secrets/*`) was
modified. No secret was introduced, rotated, or printed.

---

## 6. Open / deferred items

| ID | Item | Carried to |
|---|---|---|
| **G-D5 query exchanges** | Drive the Read and Verify voice exchanges against `switch.impresora_3d` to close the full Read → Write → Verify → Restore template for the printer. Non-blocking — pipeline query path is already proven by G-D4. | Optional — post-D-1, or accepted as-scoped at D-1.9 closeout |
| **G-D5 latency observation** | First voice intent into `ollama` after a 28-min idle landed at 19.4 s; second intent 30 s later landed at 7.5 s. Most likely cold-model warmup. Re-measure during G-D6 and post-D-1 maintenance. Folds into the G-D4 latency tuning item. | Post-D-1 maintenance |
| **G-D6 — failure-mode rehearsal** | Whisper down / Piper down / Ollama unreachable rehearsal per `05-validation-gates.md` §7 | D-1.8 |
| **D-1.7 — Open WebUI Audio integration** | Also closes the G-D1 HTTP-shim path deferred from D-1.2 | D-1.7 |
| **Overview triad** (`00_overview/CURRENT_STATE.md`, `AMAROLAB_HANDOFF.md`, `ROADMAP.md`) | Triad currently says "D-1.2 closed; D-1.3 next" — stale as of D-1.5 + D-1.6. Update at D-1.9 closeout per Lesson 005. | D-1.9 |
| **`ai.amarolab.es`** | Public Hostname not yet bound to the `amarolab` tunnel | Operator action — not on Phase D-1 critical path |
| **`cloudflared-amarolab` apply log** | Deployment validated D-1.5 but no dedicated apply log yet | Documentation sync, pre-D-1.9 |
| **DNS / architecture doc amendments** | `02_infrastructure/cloudflare/amarolab_dns_architecture.md` and `cloudflared_audit_2026-06-17.md` need to record the separate-tunnel decision | Documentation sync, pre-D-1.9 |
| R-D-13 | Migrate the HTTP shim from `fedirz/faster-whisper-server` to a maintained successor | Post-Phase-D maintenance |
| R-01 | Cloudflare Tunnel token rotation (existing Guardian-Cloud tunnel) | Independent of this phase |

---

## 7. D-1.6 closure status

With G-D5 passed (Write → Restore physical-device voice
validation, transparent procedural simplification documented in
§2), **D-1.6 is closed**.

Phase D-1 itself does **not** close until D-1.7 (Open WebUI Audio /
G-D1 HTTP-shim) and D-1.8 (G-D6 failure-mode rehearsal) also land,
with their dated apply logs.

The overview triad
(`00_overview/CURRENT_STATE.md`, `AMAROLAB_HANDOFF.md`,
`ROADMAP.md`) is **not** updated by this log — per the D-1.5 closure
pattern and Lesson 005, the triad is amended at D-1.9 closeout
once all six Phase D-1 gates and their apply logs are landed.

Per the operator instruction at the start of this session: **STOP
here**. No broader voice rollout. No additional entity is exposed
beyond the canary. The printer's voice-exposure ACL is `false` at
the close of this log.

---

## 8. Reproducibility

To re-execute G-D5 from this point forward:

1. Confirm `AURORA v1` is the preferred Assist pipeline and that
   only `input_boolean.aurora_voice_canary` is exposed to voice
   assistants.
2. Capture T0 (UTC), log byte positions per voice-stack container,
   HA recorder row counts (§1).
3. (Optional) Take a Restic snapshot if the test will mutate HA
   storage or configuration. G-D5 itself did not require one
   because it mutates only the in-memory exposure ACL, which is
   trivially reversible (§1.1).
4. In HA Settings → Voice assistants → Expose, toggle
   `switch.impresora_3d` **on** for the conversation engine. Leave
   every other entity untouched.
5. From a Chromium Secure Context at `https://ha.amarolab.es`,
   drive the voice cycle:
   - Speak *"Enciende la impresora 3D"* — confirm physical
     plug → `on` and TTS confirmation.
   - Speak *"Apaga la impresora 3D"* — confirm physical
     plug → `off` and TTS confirmation.
   - (Optional, for full spec coverage) speak the Read /
     Verify query phrases.
6. In HA UI, revoke the printer's voice exposure (toggle off).
7. Diff the HA recorder DB (`states` + `events`), voice-stack
   container logs, `ollama` `POST /api/chat` lines, and the
   `zigbee2mqtt/Impresora 3D` MQTT publish stream over the window
   `[T0, now]`.
8. Confirm the criteria in §4 and the post-state ACL in §3.11.

---

## 9. Related documents

- [`./2026-06-17_phaseD_gate_gd4_applied.md`](2026-06-17_phaseD_gate_gd4_applied.md)
  — G-D4 (canary end-to-end), the immediately preceding gate.
- [`./2026-06-17_phaseD_voice_pipeline.md`](2026-06-17_phaseD_voice_pipeline.md)
  — D-1.5 apply log (`AURORA v1` pipeline configuration).
- [`./2026-06-17_phaseD_ha_trusted_proxies_applied.md`](2026-06-17_phaseD_ha_trusted_proxies_applied.md)
  — HA reverse-proxy trust patch that unblocked Secure Context.
- [`./2026-06-17_phaseD_wakeword_installed.md`](2026-06-17_phaseD_wakeword_installed.md)
  — D-1.4 apply log (G-D3 container/probe half).
- [`./2026-06-17_phaseD_piper_installed.md`](2026-06-17_phaseD_piper_installed.md)
  — D-1.3 apply log (G-D2).
- [`./2026-06-17_phaseD_whisper_installed.md`](2026-06-17_phaseD_whisper_installed.md)
  — D-1.2 apply log (G-D1 Wyoming half).
- [`./2026-06-17_phaseC_gate_g5_applied.md`](2026-06-17_phaseC_gate_g5_applied.md)
  — Gate G-5 (chat-side `switch.impresora_3d` round-trip that G-D5
  mirrors via voice).
- [`../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md`](../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md)
  — gate definitions.
- [`../03_services/voice-stack/ha-assist/pipeline-spec.md`](../03_services/voice-stack/ha-assist/pipeline-spec.md)
  — `AURORA v1` pipeline spec.
- [`../07_operations/lessons_learned.md`](../07_operations/lessons_learned.md)
  — Lessons 002 / 005 / 010 / 013 / 015 underpin this validation
  rhythm.
