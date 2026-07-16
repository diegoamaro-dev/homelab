---
id: awning
name: Awning (Toldo)
region: home
kind: device
status: active
schema_version: 1
priority: medium
writable: false
archetype: zigbee-device
baseline: { state: closed }
binding: { ha_entity: cover.toldo }
aliases: [ "toldo", "awning" ]
collector: ha-states
anomaly_rules:
  - { token: awning_left_extended, condition: "state == open AND time in overnight" }
---

## Purpose

Motorised external awning / sun-shade (Sonoff MINI-ZBRBS). Retracted (`closed`) is normal;
extended (`open`) is manual daytime use.

## Reasoning

**Manually operated, no automatic schedule.** Extending it for shade during the day is normal and
is **not** flagged; leaving it extended **overnight** is a weather / wear risk, so
`awning_left_extended` fires only when `state == open` inside the `overnight` window
(`windows.md`: 00:00–06:00). `writable: false` — cover control is **out of core F-5** (Q7),
optional and separately gated (**G-F5-08**); it is not in the `ha_call_service` allowlist, so
Aurora cannot actuate it. Depends on `zigbee-mesh` (archetype). Motor-health is possible future
enrichment, not a core token.

**Implementation surface (informational, not anomaly-tracked):**
`sensor.toldo_motor_run_status` (motor activity; idle = `Stop`) and
`sensor.toldo_motor_travel_calibration_status` (`Calibrated`). `cover.toldo` reports
`supported_features=15` (open/close/set/stop), but **write is deferred**.

## Suggested operator actions

*Recommendations only — cover control is out of core F-5, so this is manual.* If
`awning_left_extended` overnight, retract the awning manually and check for wind / weather
exposure.
