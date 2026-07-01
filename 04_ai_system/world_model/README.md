# Aurora World Model

The **World Model** is Aurora's single semantic representation of its operational world —
entities · baselines · relationships · priorities · boundaries — expressed in terms of *what
things mean*, not how they are wired. Awareness is this model **evaluated at now**; Memory is
its entities over time; Knowledge is timeless docs about them.

- **Frozen architecture (authoritative):**
  [`../world_model_architecture.md`](../world_model_architecture.md) — **AD-21** (Revision 2,
  FROZEN 2026-07-01). All content here conforms to it.
- **Operative schema contract:** [`_schema/entity.schema.md`](_schema/entity.schema.md).

## Layout

```
world_model/
  README.md                     ← this index
  _schema/
    entity.schema.md            ← the operative entity contract (fields, grammar, validation, versioning)
    tokens.md                   ← canonical anomaly-token + severity registry (single source)
    windows.md                  ← named tz-anchored time windows
    collectors.md               ← canonical collector-id registry (WM-2; closes F-WM1-a)
    archetypes/
      zigbee-device.md          ← shallow shared defaults for Zigbee devices
  home/                         ← WM-2 home region (8 entities)
    zigbee-mesh.md              ← aggregate (critical); zigbee_bridge_down, zigbee_permit_join_on
    internet-uplink.md          ← service (high); wan_down
    printer-3d.md               ← device (medium, writable); printer_on_overnight
    awning.md                   ← device (medium); awning_left_extended
    main-door.md                ← device (medium); door_open_extended (duration)
    entrance-plant.md           ← device (low); plant_water_warning, plant_soil_dry
    battery.md                  ← aspect (low); device_battery_low (5-device roster)
    firmware.md                 ← aspect (low); silent (firmware_* reserved — no token)
  environment/                  ← WM-2 environment region (1 entity)
    daylight-time.md            ← environment (low); context only, no token
```

Regions (frozen §4.1): `infrastructure` · `home` · `projects` · `operator` · `self` ·
`environment`. One file per entity; `filename == <id>.md`; ids/tokens/fields per the naming
rules in the schema.

## How to read an entity

Each entity is a literate Markdown file: **YAML frontmatter = the authoritative machine
surface**; the prose (`## Purpose` / `## Reasoning` / `## Suggested operator actions`) is
explanatory. See [`_schema/entity.schema.md`](_schema/entity.schema.md).

## Status — Phase WM

- **WM-1 (done 2026-07-01):** `_schema/` foundation — schema, tokens, windows, archetype, README.
- **WM-2 (this; done 2026-07-01):** migrated `home_model.md`'s 9 objects → **9 literate entities**
  (`home/` ×8 + `environment/` ×1), docs-only and 1:1 (no new facts); added `_schema/collectors.md`
  (closes **F-WM1-a**) and the §2.1 binding/roster clarifications to the schema (additive,
  `schema_version` still 1). **No loader, no runtime.** `home_model.md` remains the live source
  until WM-4. Apply log: [`../../09_logs/2026-07-01_WM2_home_entities_applied.md`](../../09_logs/2026-07-01_WM2_home_entities_applied.md).
- **WM-3 (next):** the loader/compiler (`Parse → Resolve → Validate → Emit`) + the gitignored
  `world_model.generated.json`; real-data parity with the current detector.
- **WM-4→WM-6:** cut over the evaluation engine, converge consumers, and close **G-F5-04**
  (the R-F5-A remedy).

Roadmap: [`../../00_overview/ROADMAP.md`](../../00_overview/ROADMAP.md) → Phase WM.
