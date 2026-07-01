---
id: daylight-time
name: Daylight / Time Context
region: environment
kind: environment
status: active
schema_version: 1
priority: low
binding: { ha_entity: sun.sun }
---

## Purpose

Day / night context — **not an anomaly source.** It provides the astronomical day/night frame for
the home; it raises no token.

## Reasoning

Centralising day/night context keeps time-aware reasoning consistent. **Reality note (reality
wins):** the `overnight` window used by `printer-3d` / `awning` is a **fixed clock window**
(00:00–06:00 Europe/Madrid) owned by `windows.md` — it is **clock-based, not sun-derived** — so
this entity currently feeds **no** rule and owns **no** window. `home_model.md §6.8`'s phrasing
that it "parameterises the overnight windows" is looser than the live encoding; the model reflects
the live reality. This entity carries **no `anomaly_rules`, no `baseline`, and no `collector`** —
nothing evaluates it (`priority: low` is presentational, matching `home_model.md §5`). First
entity in the `environment` region.

**Implementation surface (informational):** `sun.sun` (above / below horizon) and the
`sensor.sun_next_*` timestamps (dawn / dusk / midnight).

## Suggested operator actions

None — context object.
