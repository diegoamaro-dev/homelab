# WM-3 — Parity validation report (real /api/states corpus)

- **Date:** 2026-07-01T22:49:54Z
- **Artifact:** docs_commit `954735c1`, loader `0.1.0`, 9 rules
- **Oracle:** `evaluate_model(compiled AST)` vs `detect_home()` (HOME_RULES), read-only import; snapshots in-memory only (AD-18).
- **Verdict:** ✅ PARITY 100% — `detect_home()` NOT replaced (WM-4).

## 1. Corpus
- Real live snapshots captured: **30** / 30 (~30s window)
- Distinct home conditions observed: **1** (home stable over the window; low variance is expected)
- Anomaly tokens present in the real corpus: **['awning_left_extended']**

Observed relevant entity states (current real condition, AD-18-safe bare states):

| entity_id | state |
|---|---|
| `binary_sensor.zigbee2mqtt_bridge_connection_state` | `on` |
| `switch.zigbee2mqtt_bridge_permit_join` | `off` |
| `binary_sensor.rooter_estado_wan` | `on` |
| `switch.impresora_3d` | `off` |
| `cover.toldo` | `open` |
| `binary_sensor.sensor_puerta_principal_contact` | `off` |
| `sensor.sensor_planta_entrada_water_warning` | `none` |
| `sensor.sensor_planta_entrada_soil_moisture` | `90` |
| `binary_sensor.sensor_puerta_principal_battery_low` | `off` |
| `sensor.sensor_puerta_principal_battery` | `100` |
| `sensor.sensor_planta_entrada_battery_state` | `middle` |
| `sensor.sensor_pasillo_battery` | `100` |
| `sensor.sensor_entarda_battery` | `100` |
| `sensor.0x842712fffe3217d0_battery` | `100` |

## 2. Differential results — real corpus
- **Pass / fail: 30 / 0** (of 30)
- Token-set differences: **0**
- Ordering differences: **0**
- Rendered-text differences: **0**

## 3. Real-state × swept-time equivalence
_Real captured states evaluated at each hour 00–23 (both engines, same `now`). Exercises the `overnight` window on the real state; this is engine-equivalence, NOT a claim that a real anomaly occurred at those times._
- **Pass / fail: 24 / 0** (24 hours)

## 4. Synthetic boundary equivalence (complementary branch coverage)
- **Pass / fail: 32 / 0** enumerated snapshots (every token branch, D7, duration/window boundaries, battery kinds, ordering)

## 5. Performance comparison
- `detect_home()` (HOME_RULES): **2.2 µs/call**
- `evaluate_model()` (compiled AST): **13.1 µs/call** (×6.1)
- Live `/api/states` fetch: **3 ms** (min 2 / max 12)
- Context: both engines are sub-millisecond and **~210×** faster than the single nightly HA fetch that gates them; evaluation cost is negligible at the 04:15 cadence. Correctness parity — not speed parity — is the WM-3 gate.

## 6. Remaining mismatches & root-cause
- **None.** Every real snapshot, every swept-time evaluation, and every synthetic boundary case produced byte-identical tokens, ordering, and rendered text across both engines. No root-cause analysis required.
