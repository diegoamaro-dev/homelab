# Anomaly Token Registry — canonical, single-source

- **Role:** the **single source of truth** for anomaly tokens, their severity tier, and their
  human rendering. `anomaly_rules[].token` in every entity must reference a token defined here;
  **severity is resolved here, never authored per rule** (schema §3).
- **Authority:** conforms to [`../world_model_architecture.md`](../world_model_architecture.md)
  §5 (token permanence); tokens + tiers transcribed from the then-authoritative
  `home_model.md` §6/§7 and the rendering map `home_state_design.md` §4.4, cross-checked
  against the then-live `HOME_RULES` in `ai-stack/ingest/bin/aurora-context` (WM-1 fidelity
  gate G-WM1-2 — exact match; `HOME_RULES` retired at WM-4 — this registry is now the single
  token source, compiled and evaluated via `_loader/` + `_evaluator/`).
- **Permanence (§5):** this registry is **append-only**. A token is **never reused or
  repurposed** — Memory (digests) references tokens across years. A retired token stays,
  marked `reserved`.

---

## Registry

Order below is the fixed **§7 severity order** (critical → high → medium → low); within a tier,
the fixed order shown. Identical inputs render byte-identically (deterministic).

| Token | Tier | Rendered `Attention:` line | Source |
|---|---|---|---|
| `zigbee_bridge_down` | critical | `[critical] Zigbee mesh down — Zigbee devices unavailable` | §6.1 |
| `wan_down` | high | `[high] internet (WAN) down` | §6.2 |
| `zigbee_permit_join_on` | high | `[high] Zigbee pairing left open (security)` | §6.1 |
| `printer_on_overnight` | medium | `[medium] 3D printer on overnight` | §6.3 |
| `awning_left_extended` | medium | `[medium] awning left extended overnight` | §6.4 |
| `door_open_extended` | medium | `[medium] main door open >15 min` | §6.5 |
| `plant_water_warning` | low | `[low] entrance plant needs water` | §6.6 |
| `plant_soil_dry` | low | `[low] entrance plant soil dry (<20%)` | §6.6 |
| `device_battery_low` | low | `[low] low battery: <device(s)>` | §6.7 |

**`ha_unavailable`** — special, **not an `Attention:` item and has no tier.** Emitted when Home
Assistant is unreachable at generation time; it renders the **whole-block `Home State:
Unavailable`** (with a `Reason:` line), not a per-item anomaly (§7; `home_state_design.md`
§4.3). It is a token for the JSON `home.anomalies[]` contract, distinct from device anomalies.

## Reserved / intentionally silent

- **`firmware_*`** — **reserved, never emitted.** Firmware updates are silent maintenance and
  raise **no** token (`home_model.md` §6.9). Recorded here so the name is never repurposed.

## Rendering note

The `device_battery_low` token is a bare string in `home.anomalies[]` (AD-20 / AD-18); the
affected device name(s) appear only in the Markdown rendering, never in the token (D1).

## Change policy

Adding a token is **additive** (no `schema_version` bump). Removing one follows the
deprecation path (deprecate → grace → `reserved`), never silent, never reused (§5).
