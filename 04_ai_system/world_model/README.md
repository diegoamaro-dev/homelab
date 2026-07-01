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
    archetypes/
      zigbee-device.md          ← shallow shared defaults for Zigbee devices
  <region>/                     ← one directory per region, one file per entity (NOT YET AUTHORED)
```

Regions (frozen §4.1): `infrastructure` · `home` · `projects` · `operator` · `self` ·
`environment`. One file per entity; `filename == <id>.md`; ids/tokens/fields per the naming
rules in the schema.

## How to read an entity

Each entity is a literate Markdown file: **YAML frontmatter = the authoritative machine
surface**; the prose (`## Purpose` / `## Reasoning` / `## Suggested operator actions`) is
explanatory. See [`_schema/entity.schema.md`](_schema/entity.schema.md).

## Status — Phase WM

- **WM-1 (this):** `_schema/` foundation — schema, tokens, windows, archetype, README.
  **No entities, no loader, no runtime.**
- **WM-2:** migrate `home_model.md` → literate `home/` entities (docs only, 1:1).
- **WM-3:** the loader/compiler (`Parse → Resolve → Validate → Emit`) + the gitignored
  `world_model.generated.json`; real-data parity with the current detector.
- **WM-4→WM-6:** cut over the evaluation engine, converge consumers, and close **G-F5-04**
  (the R-F5-A remedy).

Roadmap: [`../../00_overview/ROADMAP.md`](../../00_overview/ROADMAP.md) → Phase WM.
