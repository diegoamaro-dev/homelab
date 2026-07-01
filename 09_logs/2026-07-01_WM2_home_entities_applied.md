# Apply Log — WM-2: migrate `home_model.md` → literate World Model home entities

- **Date:** 2026-07-01
- **Phase:** WM-2 (World Model implementation, per **AD-21** —
  [`../04_ai_system/world_model_architecture.md`](../04_ai_system/world_model_architecture.md)
  §6-M2 / §9-WM2). Follows WM-1 (`_schema/` foundation).
- **Scope:** documentation only — **no loader, no runtime, no code, no prompt, no tool, no
  collection, no container.** Migrates the 9 objects of
  [`../04_ai_system/home_model.md`](../04_ai_system/home_model.md) into literate entities, 1:1,
  **no new facts**. `home_model.md` and `HOME_RULES`/`bin/aurora-context` are **unchanged** —
  `HOME_RULES` remains the live detector until WM-4 (frozen §6-M4).
- **Authoring model:** architect = an AI reasoning assistant (decision register approved 2026-07-01); executor /
  validator / documenter = an AI coding assistant.
- **Gate:** semantic equivalence (M2). Review-based (no loader until WM-3).

---

## 1. What was created / modified

**Created — entities (9):**

| File | id | kind | priority | tokens |
|---|---|---|---|---|
| `world_model/home/zigbee-mesh.md` | zigbee-mesh | aggregate | critical | `zigbee_bridge_down`, `zigbee_permit_join_on` |
| `world_model/home/internet-uplink.md` | internet-uplink | service | high | `wan_down` |
| `world_model/home/printer-3d.md` | printer-3d | device | medium | `printer_on_overnight` |
| `world_model/home/awning.md` | awning | device | medium | `awning_left_extended` |
| `world_model/home/main-door.md` | main-door | device | medium | `door_open_extended` (duration) |
| `world_model/home/entrance-plant.md` | entrance-plant | device | low | `plant_water_warning`, `plant_soil_dry` |
| `world_model/home/battery.md` | battery | aspect | low | `device_battery_low` (5-device roster) |
| `world_model/home/firmware.md` | firmware | aspect | low | — (silent; `firmware_*` reserved) |
| `world_model/environment/daylight-time.md` | daylight-time | environment | low | — (context) |

**Created — registry (closes F-WM1-a):** `world_model/_schema/collectors.md` — the canonical
collector-id registry. `ha-states` (HA REST `GET /api/states`; exposes `state`, numeric,
`last_changed`; fail-loud → `ha_unavailable`) is the sole active collector; `backup_status` /
`container_status` / `health` / `torre-probe` reserved for the infrastructure region (WM-7+).

**Modified — schema (additive, `schema_version` still 1; D-WM2-1/D-WM2-7):**
`world_model/_schema/entity.schema.md` §2.1 — named multi-signal `binding` + field resolution +
aspect member-roster / fold semantics; §3 field-resolution pointer; §5 check #7 now resolves
against `collectors.md`.

**Modified — index:** `world_model/README.md` — layout tree (home/ + environment/ + collectors.md)
and Phase-WM status (WM-2 done, WM-3 next).

## 2. Decision register (operator-approved 2026-07-01)

| ID | Decision |
|---|---|
| **D-WM2-1** | Named multi-signal `binding` (additive, sv=1). Applied to `zigbee-mesh` (`connection`/`permit_join`) + `entrance-plant` (`water_warning`/`soil_moisture`). |
| **D-WM2-2** | `zigbee-mesh` stays `kind: aggregate`; membership via the archetype `depends_on` only; **no `part_of`**. |
| **D-WM2-3** | `battery` aspect references raw collector bindings; the 3 privacy-excluded devices (2 motion + desk button) get **no** operational entity. |
| **D-WM2-4** | `firmware.md` authored as a documentary aspect (no rules; silent). |
| **D-WM2-5** | `internet-uplink` stays in `home` for WM-2 (infrastructure revisit deferred). |
| **D-WM2-6** | `daylight-time` placed in `environment/` (first `environment` entity). |
| **D-WM2-7** | `entity.schema.md` received additive clarifications; `schema_version` stays 1. |

## 3. Validation — review gates (evidence-based, no loader)

| Gate | Check | Result |
|---|---|---|
| **G-WM2-1** | 9 objects → 9 entities; none dropped / invented | ✅ |
| **G-WM2-2** | rule-tokens == the 9 device tokens in `tokens.md` (no add/remove/rename) | ✅ exact match |
| **G-WM2-3** | binding entity_ids + conditions == live `HOME_RULES` (read-only cross-check) | ✅ 14/14 awareness ids identical; only extra is context-only `sun.sun` (raises no token) |
| **G-WM2-4** | conditions parse frozen §4.5; `overnight` by name; door DURATION + `last_changed` (11b) | ✅ |
| **G-WM2-5** | structural / enums / id==filename / sv=1 / prose; AD-18 secret scan | ✅ clean (no ip/token/secret) |
| **G-WM2-6** | archetype ×4, `zigbee-mesh`, battery roster entities all resolve; no cycles | ✅ |
| **G-WM2-7** | every `collector: ha-states` resolves to `collectors.md`; duration contract | ✅ 7 evaluable entities |
| **G-WM2-8** | `printer-3d writable:true` ⊆ `ha_call_service` allowlist; `awning:false` (INV-17) | ✅ |
| **G-WM2-9** | semantic-equivalence sign-off (M2) — §4 below | ✅ 1:1, no new facts |
| **G-WM2-10** | scope guard — no loader/runtime/prompt/tool; `home_model.md` + `HOME_RULES` untouched | ✅ |

**Reality notes recorded (reality wins):**
- `daylight-time` — the `overnight` window is a **fixed clock window** (00:00–06:00 Europe/Madrid,
  `windows.md`), **not** sun-derived; `home_model.md §6.8`'s "parameterises the overnight windows"
  is looser than the live encoding. The entity binds `sun.sun` for context but owns no window and
  feeds no rule.
- `ha_unavailable` is **collector-produced** (ha-states failure path, `collectors.md`), not an
  entity `anomaly_rule`; coverage (#7) is satisfied without a rule. Emission is the WM-3+ evaluator's.
- Threshold asymmetry preserved: `plant_soil_dry` is strict `< 20`; `battery` pct floor is `<= 20`.

## 4. Semantic-equivalence sign-off (G-WM2-9 / M2)

Each `home_model.md §6` object ↔ its entity; no fact added, lost, or changed.

| `home_model.md` object | Baseline (raw) | Anomaly rule → token | Entity | Parity |
|---|---|---|---|---|
| §6.1 Zigbee Mesh | connection on; permit_join off | connection off/unavailable→`zigbee_bridge_down`; permit_join on→`zigbee_permit_join_on` | zigbee-mesh | ✅ (version informational→prose) |
| §6.2 Internet Uplink | on | off→`wan_down` (off only, D7) | internet-uplink | ✅ |
| §6.3 3D Printer | off | on ∧ overnight→`printer_on_overnight` | printer-3d | ✅ (metering→prose; writable⊆allowlist) |
| §6.4 Awning | closed | open ∧ overnight→`awning_left_extended` | awning | ✅ (motor→prose; write deferred G-F5-08) |
| §6.5 Main Door | off (closed) | on for >15m→`door_open_extended` | main-door | ✅ (battery→aspect) |
| §6.6 Entrance Plant | water_warning none; soil ≥20 | water_warning≠none→`plant_water_warning`; soil<20→`plant_soil_dry` | entrance-plant | ✅ (temp/hum/lux→prose; battery→aspect) |
| §6.7 Battery Health | all ok | any of 5 low (flag/pct≤20/cat low\|empty)→`device_battery_low` | battery (aspect) | ✅ 6-row roster, names in rendering only (D1) |
| §6.8 Daylight/Time | day/night cycle | — (context, no token) | daylight-time (environment) | ✅ + reality note |
| §6.9 Firmware | none pending | — (silent, no token) | firmware (aspect) | ✅ `firmware_*` reserved |

Token vocabulary (`home_model.md §7`) is **unchanged**: 9 device tokens + `ha_unavailable`
(collector-level) + `firmware_*` reserved. AD-20 typed-token contract intact; no
`aurora-context.json` schema touched (that consumer cutover is WM-4/WM-5).

## 5. Scope guard — NOT done

No loader (WM-3), no `world_model.generated.json`, no evaluation. **Untouched:** `home_model.md`
(still the live source until WM-4), `HOME_RULES`/`bin/aurora-context`, every prompt, tool,
collection, container, and all runtime. No secret in any artifact (AD-18). `.gitignore` unchanged
(WM-2 emits no generated artifact).

## 6. Rollback

Documentation-only, fully git-revertable: remove `world_model/home/`,
`world_model/environment/`, `world_model/_schema/collectors.md`; revert the `entity.schema.md`,
`README.md`, and triad edits; delete this log. **No runtime state to unwind** — no loader stood
up, no artifact generated, and `HOME_RULES` served home awareness unchanged throughout. WM-2
alters **zero** runtime behaviour.

## 7. Next

**WM-3** — build the loader/compiler (`Parse → Resolve → Validate → Emit`) + the gitignored
`world_model.generated.json`; run **in parallel** with `HOME_RULES` and prove **real-data parity**
(frozen §6-M3). Planning-gated, as before.

## 8. Git

**STOPPED at the git gate.** No `git add`, commit, push, or tag. Triad reconciled in the same
uncommitted working tree. Reality always wins.
