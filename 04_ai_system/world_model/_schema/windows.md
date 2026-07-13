# Named Time Windows — canonical, single-source

- **Role:** the **single source of truth** for named time windows used by the `'time' 'in'
  <window>` predicate (schema §3). `anomaly_rules` reference a window **by name only**; the
  definition (bounds + timezone) lives here.
- **Authority:** conforms to [`../world_model_architecture.md`](../world_model_architecture.md)
  §4.5. Bounds transcribed from `home_model.md` §6.3/§8, cross-checked against the then-live
  `HOME_RULES` in `ai-stack/ingest/bin/aurora-context` (`0 <= hour < 6` local — WM-1 gate
  G-WM1-3; `HOME_RULES` retired at WM-4 — windows are now evaluated tz-anchored from this
  registry by `_evaluator/`).

---

## Windows

| Name | Bounds (half-open) | Timezone | Used by |
|---|---|---|---|
| `overnight` | `00:00` ≤ t < `06:00` | `Europe/Madrid` | `printer_on_overnight`, `awning_left_extended` |

Semantics: `time in overnight` is true when the local (`Europe/Madrid`) hour is in `[0, 6)`,
matching the live encoding `0 <= now_local.hour < 6`.

## Not a window: durations

Duration conditions such as `door_open_extended` ("main door open **>15 min**") are **not**
windows — they use the grammar's `field 'for' DURATION` predicate (schema §3), evaluated from
the entity's `last_changed`. Do not model durations here.

## Change policy

Adding a window is **additive** (no `schema_version` bump). Changing a window's bounds is a
**content** change (git-versioned), reflected wherever the window is referenced; it is not a
schema change.
