---
id: zigbee-mesh
name: Zigbee Mesh
region: home
kind: aggregate
status: active
schema_version: 1
priority: critical
baseline: { conditions: [ "connection == on", "permit_join == off" ] }
binding:
  connection: { ha_entity: binary_sensor.zigbee2mqtt_bridge_connection_state }
  permit_join: { ha_entity: switch.zigbee2mqtt_bridge_permit_join }
aliases:
  connection: [ "malla zigbee", "red zigbee", "zigbee", "zigbee mesh", "mesh" ]
  permit_join: [ "permitir emparejamiento", "permit join", "pairing mode" ]
collector: ha-states
status_semantics: { unavailable: down }
anomaly_rules:
  - { token: zigbee_bridge_down, condition: "connection == off OR connection unavailable" }
  - { token: zigbee_permit_join_on, condition: "permit_join == on" }
---

## Purpose

The Zigbee2MQTT bridge — the network **every** Zigbee object (printer, awning, door, plant,
motion sensors) depends on. Modelled as an `aggregate`: it is the mesh the Zigbee devices read
their state through, so its own health governs theirs.

## Reasoning

If the bridge is down, **every other Zigbee object is blind / stale** — this signal takes
precedence in any surfaced summary (it is the one `critical` home entity). Because a down mesh
*is* the fault, this is the only entity where an `unavailable` reading counts as `down`
(`status_semantics: { unavailable: down }`); ordinary Zigbee devices leave `status_semantics`
unset and never raise on `unavailable` (D7). Permit-join must be `off` except during a deliberate
pairing window — an open pairing window is a security exposure (`zigbee_permit_join_on`, high).

**Implementation surface (informational):** the Z2M version sensor
`sensor.zigbee2mqtt_bridge_version` (`2.9.1` at authoring) is drift-awareness only — **not** an
authoritative field and **not** anomaly-tracked.

## Suggested operator actions

*Recommendations only — Aurora never acts autonomously.* If `zigbee_bridge_down`, check the Z2M
add-on / container and the MQTT broker and restart the bridge if needed (every Zigbee state is
stale until restored). If `zigbee_permit_join_on` and not intentionally pairing, turn permit-join
off.
