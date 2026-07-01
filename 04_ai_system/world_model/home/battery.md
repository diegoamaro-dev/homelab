---
id: battery
name: Battery Health
region: home
kind: aspect
status: active
schema_version: 1
priority: low
collector: ha-states
applies_to:
  - { device: "Main Door",      entity: main-door,      signal: flag, binding: binary_sensor.sensor_puerta_principal_battery_low }
  - { device: "Main Door",      entity: main-door,      signal: pct,  binding: sensor.sensor_puerta_principal_battery }
  - { device: "Entrance Plant", entity: entrance-plant, signal: categorical, binding: sensor.sensor_planta_entrada_battery_state }
  - { device: "Pasillo motion", signal: pct, binding: sensor.sensor_pasillo_battery }
  - { device: "Entrada motion", signal: pct, binding: sensor.sensor_entarda_battery }
  - { device: "Desk button",    signal: pct, binding: sensor.0x842712fffe3217d0_battery }
anomaly_rules:
  - { token: device_battery_low, condition: "battery_low == on OR battery_level <= 20 OR battery_state == low OR battery_state == empty" }
---

## Purpose

Low-battery maintenance across **all Zigbee battery-powered devices** (operator decision: extend
to all five). A cross-cutting `aspect`, not a device of its own — it composes onto the battery
surface of other devices.

## Reasoning

A dead battery silently blinds a device. Battery level is a maintenance signal and is
**privacy-safe** — monitoring an occupancy sensor's *battery* does **not** track presence. The
roster therefore includes two **modelled** entities (`main-door`, `entrance-plant`) **and three
deliberately non-modelled devices** (Pasillo motion, Entrada motion, Desk button) that are
excluded as *operational* objects by the privacy decision (`home_model.md §9`) but whose
**batteries are still watched** (D-WM2-3: an aspect may reference raw collector bindings without
promoting those devices to entities).

**Fold semantics (per member; matches the live `_battery_low_devices`).** Each member is tested
only by the rule field matching its `signal` kind — any absent field never trips:

- `flag` → `battery_low == on`
- `pct` → `battery_level <= 20` (the §6.7 / §8 maintenance floor — **≤ 20 %**, distinct from the
  strict `< 20` used by `plant_soil_dry`)
- `categorical` → `battery_state == low OR battery_state == empty` (case-insensitive; `middle` /
  higher are OK)

Any member tripping raises **`device_battery_low` at most once**; the affected device name(s)
appear in the Markdown rendering **only**, never in the token (AD-20 / D1), de-duplicated by
device name and — **when rendered** — listed in the roster order above. `unavailable` / `unknown`
never guesses low (D7). The baseline is all members within their per-member normal (§2.1); the
mechanical per-member dispatch (and any iteration strategy) is a loader (WM-3) concern.

## Suggested operator actions

*Recommendations only.* Replace or recharge the named device's battery.
