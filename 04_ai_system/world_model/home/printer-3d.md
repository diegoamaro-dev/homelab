---
id: printer-3d
name: 3D printer
region: home
kind: device
status: active
schema_version: 1
priority: medium
writable: true
archetype: zigbee-device
baseline: { state: off }
binding: { ha_entity: switch.impresora_3d }
aliases: [ "impresora 3D", "impresora", "3D printer", "printer" ]
collector: ha-states
anomaly_rules:
  - { token: printer_on_overnight, condition: "state == on AND time in overnight" }
---

## Purpose

The 3D printer and its switched mains plug (Sonoff S60ZBTPF) — Aurora's **one** validated control
surface. `writable: true` is **descriptive only**: the actual authority is the `ha_call_service`
allowlist (D-12; `switch.turn_on` / `switch.turn_off` on `switch.impresora_3d`, validated at Gate
G-5), of which this is a subset — never a grant (INV-17).

## Reasoning

The printer must be `off` unless an **attended** print is running. It is the only object Aurora
can switch. A printer left powered while unattended overnight is the canonical safety anomaly
(heat / fire risk) — hence `printer_on_overnight` fires only inside the `overnight` window
(`windows.md`: 00:00–06:00 Europe/Madrid). It depends on `zigbee-mesh` (via the `zigbee-device`
archetype); a mesh outage reads it `unavailable`, which does **not** itself raise a token (D7).

**Implementation surface (informational, not anomaly-tracked):**
`switch.impresora_3d_outlet_control_protect` (overload-protection config, not power state) and the
metering sensors `sensor.impresora_3d_power` (W) / `sensor.impresora_3d_voltage` (V) /
`sensor.impresora_3d_energy_today` (kWh).

## Suggested operator actions

*Recommendations only — Aurora never switches it autonomously.* Verify whether a print is
intentionally running; if not, switch the plug off (manually, or via Aurora only on an explicit
request) and check the printer.
