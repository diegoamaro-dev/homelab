# Phase C — C-7 closeout

- **Date:** 2026-06-17
- **Status:** **CLOSED.** Phase C — Home Assistant
  integration — is complete. All Phase C exit criteria
  defined in
  [`2026-06-16_phaseB_closeout.md`](2026-06-16_phaseB_closeout.md)
  §6.3 are met. The `00_overview/` triad
  (`CURRENT_STATE.md`, `ROADMAP.md`,
  `AMAROLAB_HANDOFF.md`) is now synchronized with the
  Phase C reality. Phase D — Voice — is the next active
  phase, currently un-started.
- **Scope:** Documentation closeout only. This log does
  not modify `webui.db`, `.env`, runtime, containers,
  or any HA entity.
- **Inputs:**
  - Gate G-5 closeout (the apex Phase C artefact):
    [`2026-06-17_phaseC_gate_g5_applied.md`](2026-06-17_phaseC_gate_g5_applied.md).
  - C-6a closeout (first real read):
    [`2026-06-17_phaseC_ha_get_state_real_validation.md`](2026-06-17_phaseC_ha_get_state_real_validation.md).
  - C-5 closeout (refusal validation):
    [`2026-06-17_phaseC_refusal_validation_applied.md`](2026-06-17_phaseC_refusal_validation_applied.md).
  - C-4 closeout (toolIds extension):
    [`2026-06-17_phaseC_gate_g4_applied.md`](2026-06-17_phaseC_gate_g4_applied.md).
  - C-3 install:
    [`2026-06-17_phaseC_tool_install_applied.md`](2026-06-17_phaseC_tool_install_applied.md).
  - C-1 design (`ha_get_state`):
    [`2026-06-17_phaseC_ha_get_state_design.md`](2026-06-17_phaseC_ha_get_state_design.md).
  - C-2 design (`ha_call_service`):
    [`2026-06-17_phaseC_ha_call_service_design.md`](2026-06-17_phaseC_ha_call_service_design.md).
  - G-Cpre closure:
    [`2026-06-17_phaseC_secret_rotation_and_gcpre_applied.md`](2026-06-17_phaseC_secret_rotation_and_gcpre_applied.md).
  - Phase C readiness review:
    [`2026-06-17_phaseC_readiness_review.md`](2026-06-17_phaseC_readiness_review.md).
  - Phase B closeout §6.3 (Phase C entry spec):
    [`2026-06-16_phaseB_closeout.md`](2026-06-16_phaseB_closeout.md).
  - Phase C documentation sync (intermediate milestone,
    tag `v0.3-phase-c-doc-sync`).

## 1. Phase C summary

### 1.1 Goal (as originally specified)

Per the ROADMAP at Phase C entry:

> Home Assistant integration. Tasks: ha_get_state(),
> ha_call_service(). Security: allowlist only; never
> allow homeassistant.*, hassio.*, recorder.*.
> Success criteria: read and limited control of the
> house.

### 1.2 Milestones executed

| Milestone | Artefact | Outcome |
|---|---|---|
| **G-Cpre** — HA env passthrough into the openwebui container, LLAT minted | `2026-06-17_phaseC_secret_rotation_and_gcpre_applied.md` | `HA_BASE_URL` (26 chars) + `HA_LLAT` (183 chars) visible inside container; OWUI uptime preserved |
| **C-1** — `ha_get_state` design | `2026-06-17_phaseC_ha_get_state_design.md` | Read Tool source authored, 8 result codes, 87-key attribute allowlist, LLAT defense-in-depth posture |
| **C-2** — `ha_call_service` design | `2026-06-17_phaseC_ha_call_service_design.md` | Write Tool source authored, 13-domain allowlist (D-12), canonical refusal path |
| **C-3** — Tool install via D-25 workflow | `2026-06-17_phaseC_tool_install_applied.md` | Both Tools resident in `webui.db.tool` (14 982 / 18 494 chars; 1 spec each); install fidelity = trailing-newline only |
| **C-4 / Gate G-4** — qwen2.5 `meta.toolIds` extension | `2026-06-17_phaseC_gate_g4_applied.md` | toolIds extended additively to the 5-list; D-35 (`base_model_id=NULL`) and D-20 (per-model scope) preserved by SQL probe |
| **C-5** — Tool-level refusal validation | `2026-06-17_phaseC_refusal_validation_applied.md` | `ha_call_service(recorder.purge)` → `result_code="refused"`, `allowed=false`; HA never called (`_init` not invoked; `httpx` not loaded) |
| **C-6a** — first real Home Assistant read | `2026-06-17_phaseC_ha_get_state_real_validation.md` | `ha_get_state(sun.sun)` → `result_code="ok"`, `state="above_horizon"`, 83 ms cold |
| **C-7-pre** — documentation sync | `v0.3-phase-c-doc-sync` tag | CURRENT_STATE / ROADMAP / AMAROLAB_HANDOFF aligned with then-current state (Phase B closed, Phase C active, G-5 pending) |
| **C-6 / Gate G-5** — first real write happy path | `2026-06-17_phaseC_gate_g5_applied.md` | `ha_call_service(switch, turn_on, switch.impresora_3d)` → `result_code="ok"`, 105 ms cold, physical state change observed via HA `last_changed` + Z2M MQTT round-trip; baseline restored to `off` |
| **C-7** — this closeout log + overview-triad sync | this file | Phase C is now CLOSED in the canonical docs; Phase D is the next active phase |

## 2. Delivered capabilities

### 2.1 Read-side

`ha_get_state(entity_id: str) → JSON`

| Capability | Status | Evidence |
|---|---|---|
| Read any HA entity state by `entity_id` | ✓ | C-6a (`sun.sun`), Gate G-5 §3.1 / §3.3 / §6.2 (`switch.impresora_3d`) |
| Attribute allowlist (87 safe keys; allowlist-not-denylist by design) | ✓ | C-1 §3.4; C-6a §3.3 (`sun.*` attrs filtered to `{}`); Gate G-5 §3.1 (`switch.*` attrs filtered to `{}`) |
| Entity-id regex validation `^[a-z_]+\.[a-z0-9_]+$` | ✓ | C-1 line 89 / C-1 §3.5; refusal path proven via design probes |
| Per-call audit log line with `args.entity_id` only | ✓ | C-6a §4; Gate G-5 §4.1 lines 123 / 125 / 127 |
| LLAT defense-in-depth (env-only, never in audit / return / stdout) | ✓ | C-1 §4.2; C-6a §3.6; Gate G-5 §4.2 (0 / 0 / 0 sweep on 5 lines) |
| Cold call ≤ 3 000 ms / warm ≤ 1 000 ms | ✓ | observed 195 / 83 / 19 ms |

### 2.2 Write-side

`ha_call_service(domain, service, entity_id, service_data=None) → JSON`

| Capability | Status | Evidence |
|---|---|---|
| Issue HA service calls within the 13-domain allowlist | ✓ | Gate G-5 §3.2 (`switch.turn_on`); §6.1 (`switch.turn_off`) |
| Reject out-of-allowlist calls upstream of `_init()` | ✓ | C-5 §3 (`recorder.purge` short-circuits at line 232; `_init` never fires; `httpx` not loaded) |
| Per-call audit log line with `args.{domain,service,entity_id,service_data}` and `result_code` | ✓ | C-5 §2.3 (refusal); Gate G-5 §4.1 lines 124 / 126 (permits) |
| HA accepts the call (REST 200 OK) | ✓ | Gate G-5 §3.2 (`ha_status=200`) |
| Physical state change propagates Z2M → MQTT → Zigbee → device | ✓ | Gate G-5 §3.3 (HA `last_changed` advanced; observable at device) |
| LLAT defense-in-depth | ✓ | Gate G-5 §4.2 (0 / 0 / 0 sweep on the 5 new lines) |
| Cold call ≤ 3 000 ms / warm ≤ 1 500 ms | ✓ | observed 105 / 84 ms |

### 2.3 Cross-cutting

- **Inline audit helper** (`_audit_helper.py` → injected at install time per D-25/D-26) — append-only JSONL to `/data/amarolab-audit.log`, line shape contract documented in C-1 §5 and C-2 §4.
- **Per-Tool rate limit valves** — `ha_get_state.max_per_minute=60`, `ha_call_service.max_per_minute=10` (the write Tool has the lower ceiling by design — C-2 §3.6).
- **Connection pooling** — `httpx.Client()` constructed once per process inside `_init()` (class-level singleton) per C-1 §3.1; demonstrated working under multiple-call probe sequences in Gate G-5.

## 3. Validation evidence — summary table

The Phase C validation trail spans 5 Tool invocations
across C-5 / C-6a / Gate G-5:

| ts (UTC) | tool | args | allowed | result_code | duration_ms |
|---|---|---|:---:|---|---:|
| 2026-06-16 15:46:30Z | `ha_call_service` | recorder/purge | **false** | **refused** | (n/a — short-circuit) |
| 2026-06-16 15:58:12Z | `ha_get_state` | sun.sun | true | ok | 83 |
| 2026-06-16 22:29:27Z | `ha_get_state` | switch.impresora_3d | true | ok | 195 |
| **2026-06-16 22:29:59Z** | **`ha_call_service`** | **switch / turn_on / switch.impresora_3d** | **true** | **ok** | **105** |
| 2026-06-16 22:30:23Z | `ha_get_state` | switch.impresora_3d | true | ok | 83 |
| 2026-06-16 22:31:12Z | `ha_call_service` | switch / turn_off / switch.impresora_3d | true | ok | 84 |
| 2026-06-16 22:31:13Z | `ha_get_state` | switch.impresora_3d | true | ok | 19 |

The bold line at `22:29:59Z` is the Gate G-5 line and
the apex artefact of Phase C.

Cross-corpus secret-shape sweep across all
`tool ∈ {ha_get_state, ha_call_service}` audit lines
ever written: **0 matches** (`Authorization|Bearer`
keyword), **0** (64-hex), **0** (JWT-shape). `HA_LLAT`
never persisted to the audit log under any code path
exercised in Phase C.

## 4. Invariants preserved

Verified by direct SQL probe at end of Gate G-5
(2026-06-16T22:31:13Z) — see G-5 §5 and §7:

| Invariant | State at Phase C exit |
|---|---|
| **D-12** — allowlist enforced at Tool boundary | Tool source byte-identical to C-3 install; `switch ∈ _ALLOWED_DOMAINS`; `recorder ∈ _EXPLICITLY_DENIED` (runtime confirmed) |
| **D-20** — per-model scope (Amarolab tools attached only to `qwen2.5:7b-instruct`) | `llama3.2:latest` toolIds = Jarvis set, `updated_at=1773442892` unchanged; `llama3:latest` toolIds = Jarvis set, `updated_at=1775031217` unchanged |
| **D-25** — Tool install via JWT-signed `POST /api/v1/tools/create` | All 8 `webui.db.tool` rows byte-identical to C-3 install (content lengths and spec counts) |
| **D-26** — inline `_audit(...)` helper second-line-of-defense | Helper present in both runtime sources (MD5 matches C-5 / C-6a baselines); never needed — `args_snap` never carries a secret in the first place |
| **D-35** — `qwen2.5.base_model_id = NULL` | Probed at G-5 §5.1: `NULL` |
| qwen2.5 `meta.toolIds` (Phase A/B/C cumulative) | `["time_now","rag_search","audit_search","ha_get_state","ha_call_service"]` |
| qwen2.5 `params.system` length | 3 342 chars (v0.1 prompt, unchanged since Phase B) |
| qwen2.5 `updated_at` | `1781623953` (C-4 timestamp; unchanged across C-5 / C-6a / G-5) |

The Phase C work mutated **exactly one** SQL row across
the entire phase — the qwen2.5 `meta.toolIds`
additive extension at C-4 — and inserted **exactly two**
new rows — `ha_get_state` and `ha_call_service` in
`webui.db.tool` at C-3.

## 5. Remaining risks

### 5.1 Carried over from earlier phases (unchanged)

- **R-01 Cloudflare Tunnel token rotation.** Pending.
  External attack surface; mitigated by the tunnel's
  default Cloudflare-side ACL and by Guardian Cloud's
  application-layer auth, but rotation is still
  documentation-debt and a security hygiene item.
- **Dedicated NAS not yet procured.** Restic backups
  currently live on the 2 TB USB disk attached to the
  mini server. Failure mode: single-disk dependency.
  Mitigation: existing `restic check`; the snapshot
  cadence is documented; off-site copy is the natural
  next step.

### 5.2 Introduced and partially mitigated in Phase C

- **Mosquitto `allow_anonymous true`.** Validation
  posture; an MQTT broker on the LAN with no auth.
  Mitigation: LAN is segmented; the broker is not
  exposed beyond it; no public ingress. **This is a
  pre-Phase-D blocker** — authenticated users + ACLs
  must be in place before voice work touches MQTT in
  any new way.
- **`HA_LLAT` is a long-lived access token.**
  Mitigation: env-only inside the openwebui container
  (G-Cpre), defense-in-depth in the Tool source
  (`args_snap` excludes it; secret-shape sweep proven
  0 across the Phase C corpus), and the C-7 closeout
  preserves the no-leak property. Rotation cadence not
  yet scheduled — track at next security pass.
- **Single qwen2.5 row carries the entire Amarolab
  Tool surface.** Mitigation: D-20 per-model scope is
  the design; D-35 invariant is monitored by every
  Phase C closeout SQL probe; the Issue T remediation
  pattern is documented and reusable.

### 5.3 New risks introduced specifically by Gate G-5

None novel. The Z2M → MQTT → Zigbee chain was already
operational and producing real-device control via the
Home Assistant frontend prior to Gate G-5; Gate G-5
exercised the same chain through a different caller
(the Amarolab Tool) without introducing new failure
modes.

## 6. Recommended Phase D starting point

Phase D goal (per ROADMAP): voice interaction through
the house, via Whisper (STT) + Piper (TTS) + Home
Assistant Assist.

### 6.1 Pre-Phase-D blocker

**Resolve Mosquitto authentication hardening first.**
Concretely:

1. Create at least three Mosquitto users with
   distinct passwords:
   - one for `homeassistant` core
   - one for `zigbee2mqtt`
   - one for the future voice/Assist client (or reuse
     the homeassistant user if Assist runs in-process)
2. Author `mosquitto.acl` mapping users to their
   needed topic prefixes (publish/subscribe scopes).
3. Set `allow_anonymous false` in `mosquitto.conf`.
4. Update HA and Z2M integration configs to carry
   credentials.
5. Restart Mosquitto, HA, Z2M (in that order).
6. Verify `ha_call_service(switch, turn_off,
   switch.impresora_3d)` still round-trips through
   the chain (smoke re-test).

Document under
`03_services/mosquitto/auth-hardening.md` (the
existing `03_services/mosquitto/` folder is the
canonical home).

### 6.2 Phase D — first three steps

Once the MQTT blocker is closed:

1. **Decide audio path.** Two viable shapes:
   - HA Assist with cloud-piped STT/TTS (fastest to
     stand up, but inverts the "everything local"
     principle).
   - HA Assist with local Whisper + Piper (matches
     long-term vision; needs a Whisper model choice
     and a Piper voice choice).
   The local shape is the canonical Amarolab choice
   per
   [`../00_overview/AMAROLAB_HANDOFF.md`](../00_overview/AMAROLAB_HANDOFF.md)
   §"Long-Term Vision".
2. **Pick microphone hardware.** USB array (e.g.
   ReSpeaker) vs networked (HA Voice Preview Edition
   or equivalent) vs phone-as-mic via the HA
   companion app. Document the tradeoffs in
   `08_projects/phase-d-voice/audio-hardware.md`.
3. **First end-to-end voice → Tool call.** Goal:
   the user says "turn on the printer", HA Assist
   transcribes via Whisper, HA Assist resolves
   intent to `switch.turn_on(switch.impresora_3d)`,
   and the audit log records a +1 line with
   `tool=ha_call_service`, `args.service=turn_on`.
   This is the Phase D analogue of Gate G-5 — the
   voice-side first-real-write.

### 6.3 Phase D non-goals

- Do **not** extend `meta.toolIds` on qwen2.5 for
  voice work — HA Assist is a separate orchestration
  surface, parallel to OWUI, with its own intent
  resolver. The qwen2.5 row is finished as far as the
  Phase A→C ladder is concerned.
- Do **not** add new Amarolab Tools in Phase D. The
  Tool layer is locked from Phase C exit until a
  Phase D outcome demands a new one.

## 7. Documentation triad sync — applied this turn

| File | Change | Reason |
|---|---|---|
| `00_overview/CURRENT_STATE.md` | Phase C status `In progress` → `Completed (2026-06-17 — Gate G-5)`; G-5 result inlined; G-5 + closeout log refs added; Phase D section added as "Next active phase"; "Known pending items" pruned (G-5 + C-7 removed; Mosquitto hardening promoted); GitHub recent-work list extended; the duplicated `## 2026-06-17 — Phase C Completed` appended footer removed (its content folded into the canonical inline section) | Reconcile inline-vs-appended contradiction; make G-5 evidence locatable from the canonical state doc |
| `00_overview/AMAROLAB_HANDOFF.md` | `Current Goal` rewritten — Phase A/B/C all Completed, Phase D Next; "Not yet" trimmed to voice-only items; `Next Immediate Task` replaced — Phase D scoping (audio path, mic, first end-to-end), plus the Mosquitto blocker carry-over | Remove the "Gate G-5 is the next milestone" wording per user instruction; surface Phase D as the live phase |
| `00_overview/ROADMAP.md` | Phase C reformatted (clean task list; `recorder.purge` refusal + `switch.impresora_3d` Gate G-5 happy path described); Phase C `Completed (2026-06-17 — Gate G-5)`; Phase D `Next active phase (not yet started)` with the Mosquitto pre-blocker called out | Make roadmap milestones match CURRENT_STATE and the apex Phase C artefacts; mark Phase D as the next active phase |

## 8. What this closeout deliberately did NOT do

- Did not modify `webui.db`, `.env`, `ai-stack/.env`, or
  any Tool source on disk.
- Did not modify any container (no `docker restart`, no
  recreate).
- Did not touch HA, Mosquitto, Z2M, or any HA entity.
- Did not invoke any Tool (no `+1` to the audit log
  this turn).
- Did not start Mosquitto hardening — that is
  documented as the pre-Phase-D blocker but
  intentionally out of this log's scope.
- Did not start Phase D — only the scoping pointer is
  recorded.
- Did not refresh the sub-project triad under
  `04_ai_system/amarolab-v1/` — the project-level
  triad in `00_overview/` is the canonical one for
  C-7 per the user's task scope. If the sub-project
  docs exist and need a similar sync, that is a
  separate, follow-up turn.
- Did not commit anything. Per user instruction
  ("DO NOT COMMIT. DO NOT PUSH. STOP AFTER
  REPORTING.").

## 9. Phase C → Phase D handoff note

| Item | Value |
|---|---|
| Phase C closure date | 2026-06-17 |
| Apex artefact | Gate G-5 audit-log line `id=5065c3d8-f512-439f-9c7c-1ba1efa7f935`, ts `2026-06-16T22:29:59.150530+00:00`, `tool=ha_call_service`, `args={domain:switch, service:turn_on, entity_id:switch.impresora_3d}`, `result_code=ok`, `duration_ms=105` |
| qwen2.5 row state at handoff | `base_model_id=NULL`, `meta.toolIds=["time_now","rag_search","audit_search","ha_get_state","ha_call_service"]`, `params.system` length 3 342, `updated_at=1781623953` |
| `webui.db.tool` rows at handoff | 8: time_now (5 180), rag_search (11 629), audit_search (11 231), ha_get_state (14 982), ha_call_service (18 494), docker_containers (890), docker_logs (585), system_status (507) |
| Pre-Phase-D blocker | Mosquitto authentication hardening (move off `allow_anonymous true`) |
| First Phase D task | Decide local vs cloud-piped STT/TTS path |
| Phase D non-goal | Do not extend qwen2.5 `meta.toolIds`; do not add new Amarolab Tools |

## 10. Cross-references

- Apex Phase C artefact (Gate G-5):
  [`2026-06-17_phaseC_gate_g5_applied.md`](2026-06-17_phaseC_gate_g5_applied.md)
- Phase C trail (chronological):
  - G-Cpre:
    [`2026-06-17_phaseC_secret_rotation_and_gcpre_applied.md`](2026-06-17_phaseC_secret_rotation_and_gcpre_applied.md)
  - C-1 design:
    [`2026-06-17_phaseC_ha_get_state_design.md`](2026-06-17_phaseC_ha_get_state_design.md)
  - C-2 design:
    [`2026-06-17_phaseC_ha_call_service_design.md`](2026-06-17_phaseC_ha_call_service_design.md)
  - C-3 install:
    [`2026-06-17_phaseC_tool_install_applied.md`](2026-06-17_phaseC_tool_install_applied.md)
  - C-4 / Gate G-4:
    [`2026-06-17_phaseC_gate_g4_applied.md`](2026-06-17_phaseC_gate_g4_applied.md)
  - C-5 refusal:
    [`2026-06-17_phaseC_refusal_validation_applied.md`](2026-06-17_phaseC_refusal_validation_applied.md)
  - C-6a real read:
    [`2026-06-17_phaseC_ha_get_state_real_validation.md`](2026-06-17_phaseC_ha_get_state_real_validation.md)
  - C-6 / Gate G-5:
    [`2026-06-17_phaseC_gate_g5_applied.md`](2026-06-17_phaseC_gate_g5_applied.md)
  - C-7 (this log):
    `2026-06-17_phaseC_closeout.md`
- Phase B closeout (Phase C entry spec):
  [`2026-06-16_phaseB_closeout.md`](2026-06-16_phaseB_closeout.md)
- Phase C readiness review (validation matrix):
  [`2026-06-17_phaseC_readiness_review.md`](2026-06-17_phaseC_readiness_review.md)
- Zigbee onboarding (the real device under test):
  [`../03_services/zigbee-stack/zigbee2mqtt_first_devices.md`](../03_services/zigbee-stack/zigbee2mqtt_first_devices.md)
- Canonical state at end of Phase C:
  [`../00_overview/CURRENT_STATE.md`](../00_overview/CURRENT_STATE.md),
  [`../00_overview/ROADMAP.md`](../00_overview/ROADMAP.md),
  [`../00_overview/AMAROLAB_HANDOFF.md`](../00_overview/AMAROLAB_HANDOFF.md)

## 11. Stop point

Per the user's instruction ("DO NOT COMMIT. DO NOT
PUSH. STOP AFTER REPORTING."): this log is the
artefact. **Phase C is CLOSED.** Phase D — Voice — is
the next active phase, pre-blocked on Mosquitto
authentication hardening. Awaiting explicit user
instruction to begin Phase D scoping.
