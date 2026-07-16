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

## 2026-07-16 — Aurora v1.0 Foundation

Description:

Aurora completed the transition from a reactive platform foundation to an aware
operational assistant.

Verification:

WM-6 canonical real induced anomaly (printer_on_overnight; overnight window;
manual induction and immediate baseline restore) surfaced truthfully across both
front doors — chat (ai.amarolab.es) and voice (ha.amarolab.es / AURORA v1) —
under the current operational configuration.

G-F5-04 CLOSED on real evidence.
R-F5-A (awareness-consumption gap) resolved structurally via INV-19.

Importance:

This milestone marks the transition from:

"AI that can act"

to

"AI that is aware"

The 2026-06-28 Aurora Foundation (knowledge platform, tool surface, system prompt)
was extended — not replaced — by Phase F (situational awareness, operational
memory, home intelligence) and WM-0…WM-6 (the World Model, AD-21).

Architecture:

World Model (literate entities)
→ Loader (compile)
→ Evaluator (one awareness evaluation — INV-19)
→ Projections: chat Filter · system_status · voice line

References:

WM-6 / G-F5-04 closure commit: b4fa1a5b
Milestone record commit: 2cee8a00
Record: 09_logs/2026-07-16_AURORA_V1_FOUNDATION.md
Predecessor: 04_ai_system/AURORA_FOUNDATION.md (2026-06-28)

Status:

COMPLETED (tag pending)