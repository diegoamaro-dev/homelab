# home_model.md — AURORA Home Model (Phase F-5)

Phase: **F-5 — Home Intelligence**, milestone **F5.1** (this document).
Last updated: 2026-06-30 (object-first + cognitive-model revision; RF5-2 applied).
Architecture of record: [`phase_f_architecture.md`](phase_f_architecture.md) →
§9-F-5, §4C (F5.0 decision register), **AD-19**, **AD-20**.
Target gate: **G-F5-01**.

---

## 1. Purpose and modelling principle

> **Core design principle.**
> **AURORA reasons about the home, not about Home Assistant.**
> **Home Assistant is only the implementation layer.**

This document is the **source of truth for the AURORA home model**: the real
things AURORA reasons about, their expected baseline, and the rules that define
an *anomaly* for each.

**Object-first, concept-before-implementation.** AURORA reasons about
**real-world objects** — the *"Entrance Plant"*, the *"Main Door"*, the
*"3D Printer"* — and only *afterwards* knows which Home Assistant entities
implement them. Each object is modelled with **seven fields, in this order**:

1. **Purpose** — what the object is, in the home.
2. **Operational Priority** — one of **Critical / High / Medium / Low**.
3. **Reasoning** — how AURORA should think about the object.
4. **Baseline** — the expected normal state.
5. **Anomaly Rules** — condition(s) → typed token (tokens only; AD-20).
6. **Suggested Operator Actions** — **human recommendations** if an anomaly
   occurs. These are **recommendations only** — they are **not** automations and
   **never** imply autonomous execution. AURORA *surfaces*; the operator decides
   and acts (`AURORA_VISION.md` §7; §9-F-5 "What F-5 explicitly does not do").
7. **Implementation (Home Assistant entities)** — the HA entity_ids that
   implement the object (the implementation layer; last, by design).

What this document **is not** (out of scope for F5.1, by operator instruction):

- It does **not** implement anomaly detection. No code runs from this document.
  Detection is F5.2 (`bin/aurora-context` home section) and F5.3 (validation).
- It does **not** modify `bin/aurora-context`, any prompt, or any tool.

---

## 2. Data provenance (no fabrication)

Every object, entity, state and capability below was read from the **live
production Home Assistant** via the read-only REST API on 2026-06-30:

- `GET /api/states` → 130 entities (HTTP 200; `HA_LLAT`, non-admin, `states`
  scope — RF5-1 confirmed at F5.1 entry).
- The battery surface (§6.8) was enumerated from the live `device_class=battery`
  entities — exactly 5 real battery-powered devices, none invented.
- Credentials (`HA_BASE_URL`, `HA_LLAT`) are read from `ai-stack/.env`
  (gitignored). **The token never appears in this document or any context
  artifact** (§13; AD-18).
- Live readings are cited only as *observed-at-authoring* grounding; baselines
  are expressed as states/ranges, not pinned to a single volatile reading.

All baselines and anomaly rules are **operator-confirmed** (§8) or grounded in
documented history / unambiguous device semantics. Nothing is invented (RF5-2).

---

## 3. Scope (privacy-aware operational core)

In scope (operator decision, 2026-06-30 — "Operational core, privacy-aware"),
expressed as objects: **3D Printer · Awning · Zigbee Mesh · Main Door ·
Entrance Plant · Internet Uplink · Daylight/Time context**, plus cross-cutting
**Battery Health** (surfaced) and **Firmware** (silent maintenance).

Explicitly **excluded** from core F5.1 (transparent list in §9): occupancy /
motion / presence tracking; `person.*`; media players / TV; the desk button as
an *operational* object (its battery is still monitored); a raw HA dump.

### 3.1 Reconciliation note vs the F5.0 frozen scope

> Reality check found more real HA devices than the original minimal scope.
> F5.1 intentionally expands from "strict minimal device scope" to a
> privacy-aware operational core because those entities directly support
> anomaly detection without modelling personal presence or entertainment
> behaviour.

This supersedes the **minimal** device list assumed in the frozen F5.0 scope
(§4C-Q6 / §9-F-5: "`switch.impresora_3d`, `cover.toldo`, Z2M bridge").
Reconciling that text in `phase_f_architecture.md` to this operational core is a
**follow-up architecture edit** (its own review + commit) — not made here, since
F5.1 is scoped to authoring `home_model.md` only.

---

## 4. Conventions

- **Operational Priority** ladder: **Critical** (infra everything depends on) >
  **High** (connectivity/security) > **Medium** (safety/operational) > **Low**
  (maintenance/care/context). Aligned with the per-token priorities in §7;
  this is a presentation field — it changes no token.
- **R** — entity state readable (HA REST `/api/states`; `ha_get_state`).
- **W** — controllable via `ha_call_service` (D-12 allowlist + per-domain gate).
  Core F5.1 is **read / surface-only**; the only writable in-scope entity is the
  printer plug (`switch.turn_on` / `switch.turn_off` — allowlisted, validated at
  Gate G-5). Awning `cover.*` control is **out of core F-5** (Q7) → optional,
  separately gated (**G-F5-08**). All else is read-only by nature.
- **[confirmed]** — operator-ratified value (§8, 2026-06-30).
  **[established]** — grounded in documented history / unambiguous semantics.
- Anomaly tokens are **short typed snake_case strings** (AD-20). F5.2 will write
  only these into `aurora-context.json` → `home.anomalies[]`; never a raw HA
  payload (AD-18).

---

## 5. Object inventory (G-F5-01 at a glance)

| Object | Priority | Purpose | Baseline | Anomaly token(s) |
|---|---|---|---|---|
| **Zigbee Mesh** | Critical | Network all Zigbee devices depend on | connected, permit-join off | `zigbee_bridge_down`, `zigbee_permit_join_on` |
| **Internet Uplink** | High | WAN / internet connectivity | connected | `wan_down` |
| **3D Printer** | Medium | Printer + switched mains supply | off | `printer_on_overnight` |
| **Awning (Toldo)** | Medium | External sun-shade | retracted | `awning_left_extended` |
| **Main Door** | Medium | Front-door open/closed | closed | `door_open_extended` |
| **Entrance Plant** | Low | Monitored plant (soil/water) | watered, soil ≥20% | `plant_water_warning`, `plant_soil_dry` |
| **Battery Health** | Low | Low-battery across all Zigbee battery devices | all ok | `device_battery_low` |
| **Daylight / Time** | Low | Day-night context (no anomaly) | day/night cycle | — (context) |
| **Firmware** | Low | Device firmware updates (silent) | none pending | — (silent maintenance) |

---

## 6. Objects (full model — 7-field cognitive structure)

### 6.1 Object: Zigbee Mesh (Z2M Bridge)

1. **Purpose:** The Zigbee2MQTT bridge — the network **every** Zigbee object
   (printer, awning, door, plant, motion sensors) depends on.
2. **Operational Priority:** **Critical.**
3. **Reasoning:** If the bridge is down, **every other Zigbee object is blind /
   stale** — this signal takes precedence in any surfaced summary. Permit-join
   must be `off` except during deliberate pairing (an open pairing window is a
   security exposure).
4. **Baseline:** connected (`on`); permit-join `off`; version stable (`2.9.1`).
5. **Anomaly Rules:** connection_state `off`/unavailable ⇒ **`zigbee_bridge_down`**
   (critical) · **[established]**; permit_join `on` outside a deliberate pairing
   window ⇒ **`zigbee_permit_join_on`** (security) · **[established]**. Version is
   informational (drift awareness) — not surfaced.
6. **Suggested Operator Actions** *(recommendations only — AURORA never acts):*
   if `zigbee_bridge_down`, check the Z2M add-on/container and the MQTT broker
   and restart the bridge if needed (every Zigbee state is stale until restored);
   if `zigbee_permit_join_on` and not intentionally pairing, turn permit-join off.
7. **Implementation (Home Assistant entities):**
   - `binary_sensor.zigbee2mqtt_bridge_connection_state` — mesh ↔ MQTT link (R).
   - `switch.zigbee2mqtt_bridge_permit_join` — pairing window (R, monitor only).
   - `sensor.zigbee2mqtt_bridge_version` — Z2M version (R; `2.9.1`).

### 6.2 Object: Internet Uplink (WAN)

1. **Purpose:** Internet / WAN connectivity (router integration).
2. **Operational Priority:** **High.**
3. **Reasoning:** Loss of WAN affects remote access and cloud-dependent
   functions; a clean binary up/down signal. (The router's external-IP and speed
   sensors are **deliberately unmodelled** — the IP value never enters any
   artifact, AD-18.)
4. **Baseline:** Connected (`on`).
5. **Anomaly Rules:** `off` ⇒ **`wan_down`** · **[established]**.
6. **Suggested Operator Actions** *(recommendations only):* check the router /
   ISP; power-cycle the router if needed; remote access is unavailable until
   restored.
7. **Implementation (Home Assistant entities):**
   - `binary_sensor.rooter_estado_wan` — connectivity (R; dc `connectivity`).

### 6.3 Object: 3D Printer

1. **Purpose:** The 3D printer and its switched mains plug (Sonoff S60ZBTPF).
   AURORA's one validated control surface.
2. **Operational Priority:** **Medium** (safety-relevant).
3. **Reasoning:** The printer must be off unless an **attended** print is
   running. It is the only object AURORA can switch. A printer left powered while
   unattended overnight is the canonical safety anomaly (heat/fire risk).
4. **Baseline:** **Off** (≈0 W idle; mains present ≈235 V).
5. **Anomaly Rules:** power state `on` during the overnight window
   **00:00–06:00** local ⇒ **`printer_on_overnight`** · **[confirmed]**.
6. **Suggested Operator Actions** *(recommendations only — AURORA never switches
   it autonomously):* verify whether a print is intentionally running; if not,
   switch the plug off (manually, or via AURORA only on an explicit request) and
   check the printer.
7. **Implementation (Home Assistant entities):**
   - `switch.impresora_3d` — power state. **R + W** (`switch.turn_on`/`turn_off`,
     allowlisted D-12, validated G-5; baseline `off` restored after every gate).
   - `switch.impresora_3d_outlet_control_protect` — overload-protection config
     (R; not power state, not anomaly-tracked).
   - `sensor.impresora_3d_power` (W), `sensor.impresora_3d_voltage` (V),
     `sensor.impresora_3d_energy_today` (kWh) — power metering (R).

### 6.4 Object: Awning (Toldo)

1. **Purpose:** Motorised external awning / sun-shade (Sonoff MINI-ZBRBS).
2. **Operational Priority:** **Medium.**
3. **Reasoning:** **Manually operated, no automatic schedule.** Extending it for
   shade during the day is normal manual use; leaving it extended **overnight** is
   a weather/wear risk — it should be retracted when unattended at night.
4. **Baseline:** **Retracted (closed)** · **[confirmed]**. Manual operation, no
   schedule. Motor idle (`Stop`), `Calibrated`.
5. **Anomaly Rules:** awning extended (not retracted) during the overnight window
   **00:00–06:00** ⇒ **`awning_left_extended`** · **[confirmed]** (daytime
   extension is intentional and not flagged). Motor-health fault is a possible
   future enrichment, not a core token.
6. **Suggested Operator Actions** *(recommendations only — cover control is out
   of core F-5, so this is manual):* if `awning_left_extended` overnight, retract
   the awning manually and check for wind/weather exposure.
7. **Implementation (Home Assistant entities):**
   - `cover.toldo` — position/state. **R** in core (supports open/close/set/stop,
     `supported_features=15`; **write deferred** — Q7 / optional G-F5-08).
   - `sensor.toldo_motor_run_status` — motor activity (R; idle = `Stop`).
   - `sensor.toldo_motor_travel_calibration_status` — calibration (R; `Calibrated`).

### 6.5 Object: Main Door

1. **Purpose:** Front-door open/closed state (operational + security).
2. **Operational Priority:** **Medium.**
3. **Reasoning:** Brief opening during the day is **normal** and is not flagged.
   A door left open for an extended period is a security/operational concern.
   This is a **left-open** signal — **not** motion/presence tracking.
4. **Baseline:** **Closed** (`off`).
5. **Anomaly Rules:** contact `on` (open) continuously **longer than 15 minutes**
   ⇒ **`door_open_extended`** · **[confirmed]**.
6. **Suggested Operator Actions** *(recommendations only):* verify the door and
   close it if the opening is unintended.
7. **Implementation (Home Assistant entities):**
   - `binary_sensor.sensor_puerta_principal_contact` — contact (R; dc `door`).
   - Battery handled by **Battery Health** (§6.7):
     `binary_sensor.sensor_puerta_principal_battery_low` +
     `sensor.sensor_puerta_principal_battery`.

### 6.6 Object: Entrance Plant

1. **Purpose:** The monitored entrance plant — soil/water health.
2. **Operational Priority:** **Low.**
3. **Reasoning:** AURORA reasons about *"the entrance plant needs water"*, not
   about raw sensor numbers. Two complementary signals: the device's own
   water-warning flag and a numeric soil-moisture floor.
4. **Baseline:** water_warning `none`; soil moisture **≥ 20 %**.
5. **Anomaly Rules:** water_warning `!= none` ⇒ **`plant_water_warning`** ·
   **[established]**; soil moisture **< 20 %** ⇒ **`plant_soil_dry`** ·
   **[confirmed]**.
6. **Suggested Operator Actions** *(recommendations only):* water the plant;
   if a reading looks implausible, verify the sensor.
7. **Implementation (Home Assistant entities):**
   - `sensor.sensor_planta_entrada_water_warning` — device water alarm (R; `none`).
   - `sensor.sensor_planta_entrada_soil_moisture` — soil moisture % (R; ~74 %).
   - `sensor.sensor_planta_entrada_battery_state` — battery (R; `middle`) → feeds
     Battery Health (§6.7). (`temperature`/`humidity`/`illuminance` exist; not
     anomaly-tracked.)

### 6.7 Object: Battery Health (cross-cutting, surfaced)

1. **Purpose:** Low-battery maintenance across **all Zigbee battery-powered
   devices** (operator decision: extend to all).
2. **Operational Priority:** **Low** (maintenance).
3. **Reasoning:** A dead battery silently blinds a device. Battery level is a
   maintenance signal and is **privacy-safe** — monitoring an occupancy sensor's
   *battery* does **not** track presence. (The motion sensors and desk button are
   excluded as *operational objects* in §9, but their batteries are still watched.)
4. **Baseline:** all ok (% devices ≈100 %; plant `middle`).
5. **Anomaly Rules:** any device's `battery_low` flag `on`, **or** battery
   **≤ 20 %**, **or** categorical battery_state low/empty ⇒ **`device_battery_low`**
   (token carries which device) · **[established]**; 20 % is the maintenance
   default.
6. **Suggested Operator Actions** *(recommendations only):* replace or recharge
   the named device's battery.
7. **Implementation (Home Assistant entities)** — the real battery surface
   (5 devices):
   - Main Door — `sensor.sensor_puerta_principal_battery` (%) +
     `binary_sensor.sensor_puerta_principal_battery_low`.
   - Entrance Plant — `sensor.sensor_planta_entrada_battery_state` (categorical).
   - Motion sensor *Pasillo* — `sensor.sensor_pasillo_battery` (%).
   - Motion sensor *Entrada* — `sensor.sensor_entarda_battery` (%).
   - Desk button — `sensor.0x842712fffe3217d0_battery` (%).

### 6.8 Object: Daylight / Time Context

1. **Purpose:** Day/night context — **not an anomaly source.** It parameterises
   the overnight windows (00:00–06:00) used by the Printer, Awning and Door.
2. **Operational Priority:** **Low** (context only — raises no anomaly).
3. **Reasoning:** Centralising day/night keeps every time-window rule consistent.
4. **Baseline:** follows the astronomical day/night cycle.
5. **Anomaly Rules:** **none** — never raises a token.
6. **Suggested Operator Actions:** none — context object.
7. **Implementation (Home Assistant entities):**
   - `sun.sun` (above/below horizon) + `sensor.sun_next_*` (dawn/dusk/midnight).

### 6.9 Object: Firmware (cross-cutting, silent maintenance)

1. **Purpose:** Track device firmware updates as **silent maintenance**.
2. **Operational Priority:** **Low** (silent — not surfaced).
3. **Reasoning:** **Operator decision — firmware updates are planned maintenance,
   not operational anomalies.** They are **not** written to `home.anomalies[]` and
   raise **no** token.
4. **Baseline:** all `off` (none pending).
5. **Anomaly Rules:** **none surfaced** (silent by operator decision).
6. **Suggested Operator Actions** *(recommendations only):* apply firmware updates
   during planned maintenance; not surfaced as an operational anomaly.
7. **Implementation (Home Assistant entities):**
   - `update.*` (8 firmware entities, dc `firmware`; all `off`).

---

## 7. Anomaly-token vocabulary (AD-20 contract for F5.2 — unchanged)

F5.2 will write **only** these short typed tokens into `aurora-context.json` →
`home.anomalies[]` (empty list on a nominal night). No raw HA payload is ever
placed in the array (AD-18 / AD-20). **This table is unchanged by the
cognitive-model revision** (no token added, removed, or renamed).

| Token | Object | Raised when | Priority | Status |
|---|---|---|---|---|
| `zigbee_bridge_down` | Zigbee Mesh | connection `off`/unavailable | critical | established |
| `wan_down` | Internet Uplink | connectivity `off` | high | established |
| `zigbee_permit_join_on` | Zigbee Mesh | permit-join `on` outside pairing | high (security) | established |
| `printer_on_overnight` | 3D Printer | plug `on` during 00:00–06:00 | medium | confirmed |
| `awning_left_extended` | Awning | extended during 00:00–06:00 | medium | confirmed |
| `door_open_extended` | Main Door | open > 15 min continuously | medium | confirmed |
| `plant_water_warning` | Entrance Plant | water_warning `!= none` | low | established |
| `plant_soil_dry` | Entrance Plant | soil moisture < 20 % | low | confirmed |
| `device_battery_low` | Battery Health | any Zigbee battery device low | low | established |
| `ha_unavailable` | (degradation) | HA unreachable at generation | n/a | reserved (F5.2) |

**Not surfaced (by operator decision):** firmware updates — silent maintenance,
no token. `ha_unavailable` is reserved: F5.2 sets
`home: {"anomalies": ["ha_unavailable"]}` if HA is unreachable at 04:15
(RF5-3 degradation); it is not a device anomaly.

---

## 8. RF5-2 confirmations — resolved (2026-06-30)

All operator-input items are ratified; **no open RF5-2 items remain.**

| # | Item | Confirmed value |
|---|---|---|
| 1 | Printer overnight window | **00:00–06:00** |
| 2 | Awning baseline | **Retracted (closed); manual; no automatic schedule** |
| 3 | Door open threshold | **Open longer than 15 minutes** |
| 4 | Plant dry threshold | **Soil moisture < 20 %** |
| 5 | Battery monitoring coverage | **All Zigbee battery-powered devices** |
| 6 | Firmware updates | **Silent maintenance — not surfaced as operational anomalies** |

---

## 9. Real-but-excluded inventory (transparency, not a dump)

Real, present entities **intentionally out of core F5.1** per the privacy-aware
operational-core decision. Listed so nothing is hidden; not modelled.

| Real entities | Why excluded from core F5.1 |
|---|---|
| 5 occupancy/motion sensors (`binary_sensor.sensor_*_occupancy`) + illumination | Presence/occupancy tracking — excluded by privacy decision. *(Their **batteries** are still monitored — §6.7.)* |
| `person.*` (2) | Personal presence — excluded |
| `media_player.*` (27), TV (`switch.tele_salon_*`, `remote.tele_salon_*`, recording binary_sensors) | Entertainment behaviour — not operational intelligence |
| Desk button (`0x842712fffe3217d0`: button/event) | No documented operational purpose as an object — revisit if one is defined. *(Battery monitored — §6.7.)* |
| HA backup-manager sensors (`sensor.backup_*`) | restic is the authoritative AMAROLAB backup (F-2 `bin/backup-probe`); HA-native backup unused (last/next `unknown`) — excluded to avoid a misleading duplicate signal |
| Voice-pipeline entities (`conversation.*`, `stt.faster_whisper`, `tts.*`, `wake_word.openwakeword`) | AURORA voice-surface registration; state semantics are timestamps/`unknown`, not clean health — candidate for an explicit voice-health signal in F-6 |
| `weather.*`, `zone.*`, `todo.*`, `light.*`, `number.*`, `select.*` (non-bridge) | Not lab-operational-anomaly relevant |

---

## 10. Secret-safety (AD-18 / AD-20 / §13)

- This document defines only **typed states and tokens** — no raw HA attribute
  payloads, **no** IP addresses (router external-IP deliberately unmodelled),
  **no** credential.
- F5.2 emits only the §7 typed tokens into `home.anomalies[]`; preserving the
  existing `aurora-context.json` schema keeps `generate-digest` valid (AD-20 —
  no F-4 regression).
- `HA_LLAT` is read at runtime from `ai-stack/.env` (gitignored) and never
  enters this document, the context artifacts, or the digest (§13).

---

## 11. Validation against G-F5-01 (revalidated) + contract check

**G-F5-01** — *"`home_model.md` exists and is complete for the real current
inventory: per entity object_id, purpose, read/write, baseline state, anomaly
rule."* Satisfied via the object-first, concept-before-implementation structure
(object_id + R/W live in each object's **Implementation** field; purpose /
baseline / anomaly rule at the object level).

| Criterion | Status |
|---|---|
| File exists (`04_ai_system/home_model.md`) | ✅ |
| Real current inventory, no invented devices/entities | ✅ all read from live `/api/states` 2026-06-30 (§2); battery surface 5/5 parity (§6.7) |
| Object-first; concept before implementation | ✅ §6 — 9 objects, 7-field order (Implementation last) |
| Per object: Purpose / Operational Priority / Reasoning / Baseline / Anomaly Rules / Suggested Operator Actions / Implementation | ✅ §6 |
| object_id present for every entity | ✅ §6 Implementation fields |
| read/write capability | ✅ §4 + §6 (printer R+W; awning R, write deferred Q7/G-F5-08; rest R) |
| baseline state | ✅ §6 (all [confirmed]/[established]) |
| anomaly rule + typed token | ✅ §6 + §7 |
| RF5-2 operator confirmations resolved | ✅ §8 — all 6 confirmed; no open items |
| AD-20 typed-token contract for F5.2 | ✅ §7 |
| Secret-safe (AD-18) | ✅ §10 |

**Contract / architecture integrity (this revision changed presentation only):**

| Contract | Status after revision |
|---|---|
| Anomaly tokens (set, names, semantics) | **Unchanged** — §7 identical (10 tokens; firmware still silent) |
| AD-20 (schema preserved; short typed tokens; no raw payloads; no Filter change) | **Compatible / unchanged** — tokens and the `home.anomalies[]` contract untouched |
| F-5 architecture (`phase_f_architecture.md`) | **Not touched** — no edit to §9-F-5 / §4C / AD-19 / AD-20 |
| Implementation layer (HA entities per object) | **Unchanged** — same entity_ids, same R/W |
| Scope, baselines, RF5-2 confirmations | **Unchanged** — only field order + 2 new presentation fields (Priority, Suggested Operator Actions) |

**Result:** G-F5-01 **met**; the change is purely presentational (a stronger
cognitive model); no architectural contract changed; AD-20 remains satisfied.

**Not in this milestone:** G-F5-07 (system-prompt home summary) and anomaly
detection (F5.2/F5.3) — per operator instruction, F5.1 authors `home_model.md`
only.

---

## 12. Cross-references

- [`phase_f_architecture.md`](phase_f_architecture.md) — §9-F-5, §4C, AD-19,
  AD-20, G-F5-01…G-F5-08.
- [`00_overview/CURRENT_STATE.md`](../00_overview/CURRENT_STATE.md) — HA surface,
  Zigbee devices, voice-exposure ACL.
- [`ai-stack/ingest/bin/aurora-context`](../ai-stack/ingest/bin/aurora-context) ·
  [`ai-stack/ingest/bin/push-voice-context`](../ai-stack/ingest/bin/push-voice-context)
  — the host-side HA-REST pattern F5.2 reuses (`HA_BASE_URL`+`HA_LLAT` from
  `ai-stack/.env`, token never printed).

---

## 13. Future evolution (intentionally deferred)

The object-centric model above is **intentionally stable**: it captures the home
as discrete objects with fixed baselines and typed anomaly tokens — the right
foundation for F5.2/F5.3. It is recorded here that the model **may later be
extended**, as separate and individually gated work with its own architecture
review, with:

- **Relationships between objects** — e.g. a Zigbee Mesh outage *explains* why
  other Zigbee objects are stale (dependency / causality links).
- **Temporal behaviour** — richer per-object time profiles beyond the single
  overnight window (expected patterns across the day).
- **Seasonal behaviour** — expectations that vary by season (e.g. awning or
  plant norms in summer vs winter).
- **Learned operator habits** — baselines refined from observed normal behaviour
  rather than only operator-stated values.
- **Confidence scoring** — a per-anomaly confidence to rank or suppress
  low-certainty signals.

None of these is in scope for F-5. They are noted only so the stable core is not
mistaken for the final ceiling. Any such extension is **future work** and must
not change current behaviour, the anomaly tokens, the `aurora-context.json`
schema, or any AD without its own freeze (AMAROLAB architecture-first discipline).
