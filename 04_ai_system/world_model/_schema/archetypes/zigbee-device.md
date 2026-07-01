---
archetype: zigbee-device
defaults:
  depends_on: [ zigbee-mesh ]
---

# Archetype — zigbee-device (shallow shared defaults)

- **Role:** optional, **shallow (one-level)** shared defaults for entities on the Zigbee mesh.
  An entity that declares `archetype: zigbee-device` merges these `defaults` unless it
  overrides them (schema §4). **No archetype-of-archetype** (deep inheritance rejected).
- **Authority:** conforms to [`../../world_model_architecture.md`](../../world_model_architecture.md)
  §4.4. Grounded in `home_model.md` §6 and the live `HOME_RULES` in
  `ai-stack/ingest/bin/aurora-context` (WM-1 gate G-WM1-4).

## Shared default

- **`depends_on: [ zigbee-mesh ]`** — every Zigbee-attached device depends on the mesh; when
  the mesh is down its members read `unavailable`. This is the one genuinely universal trait,
  so it is the archetype default (the loader derives the reverse `affects` edges).

## Conventions (documented, not fields)

- **Firmware is silent** — Zigbee firmware updates are silent maintenance and raise **no**
  token (`home_model.md` §6.9; `firmware_*` is `reserved` in `tokens.md`). Do **not** author a
  firmware anomaly rule.
- **Battery membership is per-device** — only *battery-powered* members join the `battery`
  aspect (via that aspect's `applies_to`, authored in the home region at WM-2). Mains-powered
  Zigbee devices (e.g. the printer plug) are **not** in it. Battery is therefore **not** an
  archetype default.

## Reality note (unavailable handling)

`unavailable → down` is **not** a zigbee-device default. Per the live model (D7), an
`unavailable`/`unknown` reading **never raises a token** for ordinary devices; only the mesh
aggregate (`zigbee-mesh`) sets `status_semantics: { unavailable: down }`, because a down mesh
*is* the critical fault. Individual devices leave `status_semantics` unset (default: do not
raise on unavailable). *(This corrects the illustrative example in the frozen doc, which is a
format illustration, not a normative archetype spec; reality wins for the actual defaults.)*
