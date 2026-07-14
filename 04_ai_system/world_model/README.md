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
  _loader/                      ← WM-3 loader/compiler (Parse→Resolve→Normalize→Validate→Emit) + tests/
  _evaluator/                   ← WM-4 evaluation engine (compiled model + signals @ now → Awareness) + tests/
  world_model.generated.json    ← WM-3 emitted artifact (DERIVED · gitignored · regenerable · never canonical)
```

Separation (WM-4, operator-ratified): **`_loader/` compiles, `_evaluator/`
evaluates** — the loader never evaluates live state; the evaluator never
invokes the loader (consumers read the emitted artifact, retain-last-good).

Regions (frozen §4.1): `infrastructure` · `home` · `projects` · `operator` · `self` ·
`environment`. One file per entity; `filename == <id>.md`; ids/tokens/fields per the naming
rules in the schema.

## How to read an entity

Each entity is a literate Markdown file: **YAML frontmatter = the authoritative machine
surface**; the prose (`## Purpose` / `## Reasoning` / `## Suggested operator actions`) is
explanatory. See [`_schema/entity.schema.md`](_schema/entity.schema.md).

## Status — Phase WM

- **WM-1 (done 2026-07-01):** `_schema/` foundation — schema, tokens, windows, archetype, README.
- **WM-2 (done 2026-07-01; committed + pushed):** migrated `home_model.md`'s 9 objects → **9 literate entities**
  (`home/` ×8 + `environment/` ×1), docs-only and 1:1 (no new facts); added `_schema/collectors.md`
  (closes **F-WM1-a**) and the §2.1 binding/roster clarifications to the schema (additive,
  `schema_version` still 1). **No loader, no runtime.** `home_model.md` remains the live source
  until WM-4. Apply log: [`../../09_logs/2026-07-01_WM2_home_entities_applied.md`](../../09_logs/2026-07-01_WM2_home_entities_applied.md).
- **WM-3 (done 2026-07-02; committed + pushed — git gate closed):** the loader/compiler under `_loader/`
  (`Parse → Resolve → Normalize → Validate → Emit`) + the gitignored `world_model.generated.json`.
  Backend-agnostic rule AST (**INV-WM3-A**). Real-data parity with the live `HOME_RULES`
  **PASS** — engine-equivalence 32/32 + a live `/api/states` match (incl. a real
  `awning_left_extended`). `HOME_RULES` stayed the live path until WM-4. Apply log:
  [`../../09_logs/2026-07-02_WM3_loader_applied.md`](../../09_logs/2026-07-02_WM3_loader_applied.md).
- **WM-4 (done 2026-07-13):** evaluation cutover — the authoritative engine under `_evaluator/`
  consumes the compiled artifact; `bin/aurora-context` renders home awareness from it
  (INV-19); **`HOME_RULES` + the WM-3 parity harness retired** (the 32 parity snapshots
  live on as the `_evaluator/tests/` regression suite, expectations frozen from the final
  differential run). Differential validation: 32/32 synthetic + live real-data MATCH
  (real `plant_water_warning`); full old-vs-new output equivalence (json/md/voice
  byte-identical modulo timestamps); `aurora-context.json` schema preserved (AD-20 /
  INV-18); `overall_status` stays platform-only until WM-5. `home_model.md` is now a
  redirect. Apply log:
  [`../../09_logs/2026-07-13_WM4_evaluator_cutover_applied.md`](../../09_logs/2026-07-13_WM4_evaluator_cutover_applied.md).
- **WM-5 (done 2026-07-14; at the git gate):** consumer convergence — the §1.5 aggregate
  verdict lives in `_evaluator/` (`evaluate_world` + `aggregate_verdict`; AD-WM5-1 `unknown`
  precedence), and every surface projects it (INV-19). Additive `world.verdict` / `world.regions`
  in `aurora-context.json` (`home.anomalies` unchanged — AD-20/INV-18); home-aware `system_status`
  v0.3.0 (`webui.db` install operator-gated); home-aware voice line with the W-10 top-N cap.
  Validated on real data (G-WM5-1…5); a low-only home stays `overall_status: ok` (§1.5 — "silence
  is informative"). Apply log:
  [`../../09_logs/2026-07-14_WM5_consumer_convergence_applied.md`](../../09_logs/2026-07-14_WM5_consumer_convergence_applied.md).
- **WM-6 (next):** reopen & close **G-F5-04** on a real induced anomaly (chat + voice) — the R-F5-A closure.

Roadmap: [`../../00_overview/ROADMAP.md`](../../00_overview/ROADMAP.md) → Phase WM.
