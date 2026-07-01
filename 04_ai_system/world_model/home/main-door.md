---
id: main-door
name: Main Door
region: home
kind: device
status: active
schema_version: 1
priority: medium
archetype: zigbee-device
baseline: { state: off }
binding: { ha_entity: binary_sensor.sensor_puerta_principal_contact }
collector: ha-states
anomaly_rules:
  - { token: door_open_extended, condition: "state == on for > 15m" }
---

## Purpose

Front-door open / closed state (operational + security). Contact `off` = **closed** (the
baseline); `on` = open.

## Reasoning

Brief opening during the day is **normal** and is not flagged. A door left open for an extended
period is a security / operational concern — so `door_open_extended` uses the duration predicate
`state == on for > 15m`, evaluated from the contact's `last_changed` in the current signal (B3
preserved). This is a **left-open** signal — **not** motion / presence tracking. The `main-door`
binds `ha-states`, which exposes `last_changed`, satisfying the duration/collector contract
(schema §3 / validation 11b). Depends on `zigbee-mesh` (archetype).

Battery is covered cross-cutting by the **`battery`** aspect (this device contributes
`binary_sensor.sensor_puerta_principal_battery_low` and `sensor.sensor_puerta_principal_battery`),
not by a rule here.

## Suggested operator actions

*Recommendations only.* Verify the door and close it if the opening is unintended.
