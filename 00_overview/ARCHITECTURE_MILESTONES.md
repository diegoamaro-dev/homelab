# Architecture Milestones

## 2026-06-17 — G-5

Description:

First successful physical action executed by Amarolab through Open WebUI.

Action:

switch.turn_on
entity_id=switch.impresora_3d

Verification:

Physical state transition observed.

Importance:

This milestone marks the transition from:

"AI that can observe"

to

"AI that can act"

Architecture:

Open WebUI
→ Tool Runtime
→ Home Assistant
→ MQTT
→ Zigbee2MQTT
→ Physical Device

Status:

COMPLETED