---
id: firmware
name: Firmware
region: home
kind: aspect
status: active
schema_version: 1
priority: low
applies_to: { domain: update, device_class: firmware }
---

## Purpose

Track device firmware updates as **silent maintenance**. A documentary cross-cutting `aspect`: it
records *that* firmware is modelled and *why it raises nothing*, so the deliberate silence is
visible in the model (not an omission).

## Reasoning

**Operator decision — firmware updates are planned maintenance, not operational anomalies.** They
are **not** written to `home.anomalies[]` and raise **no** token: `firmware_*` is **reserved,
never emitted** in `tokens.md`, and the `zigbee-device` archetype forbids authoring a firmware
anomaly rule. Accordingly this entity carries **no `anomaly_rules`, no `baseline`, and no
`collector`** — nothing evaluates it. `applies_to` names the update surface (the `update.*`
entities with `device_class: firmware` — 8 observed 2026-06-30, all `off`) without enumerating
ids the source does not enumerate (no invention).

## Suggested operator actions

*Recommendations only.* Apply firmware updates during planned maintenance; not surfaced as an
operational anomaly.
