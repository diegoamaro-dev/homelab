# home_model.md — AURORA Home Model (superseded → World Model)

**SUPERSEDED at WM-4 (2026-07-13).** This document was the F5.1 source of truth
for the AURORA home model. Its content was migrated **1:1** into the canonical
**World Model** at WM-2 (docs) and became the live evaluation source at WM-4
(the `HOME_RULES` machine transcription in `bin/aurora-context` was retired;
awareness is now the compiled World Model evaluated by
[`world_model/_evaluator/`](world_model/_evaluator/engine.py)).

This file remains as a **redirect** so existing links survive (frozen migration
step M4, [`world_model_architecture.md`](world_model_architecture.md) §6). The
full original text is preserved in git history (last full revision: 2026-06-30,
committed at F5.1; history is never rewritten).

---

## Where everything lives now

| This document (old) | Canonical location (now) |
|---|---|
| §1 Purpose / modelling principle | [`world_model_architecture.md`](world_model_architecture.md) §1 (AD-21, FROZEN) |
| §4 Conventions | [`world_model/_schema/entity.schema.md`](world_model/_schema/entity.schema.md) |
| §5–§6 Object inventory (9 objects) | [`world_model/`](world_model/README.md) literate entities: [`home/zigbee-mesh.md`](world_model/home/zigbee-mesh.md) (§6.1) · [`home/internet-uplink.md`](world_model/home/internet-uplink.md) (§6.2) · [`home/printer-3d.md`](world_model/home/printer-3d.md) (§6.3) · [`home/awning.md`](world_model/home/awning.md) (§6.4) · [`home/main-door.md`](world_model/home/main-door.md) (§6.5) · [`home/entrance-plant.md`](world_model/home/entrance-plant.md) (§6.6) · [`home/battery.md`](world_model/home/battery.md) (§6.7) · [`environment/daylight-time.md`](world_model/environment/daylight-time.md) (§6.8) · [`home/firmware.md`](world_model/home/firmware.md) (§6.9) |
| §7 Anomaly-token vocabulary + severities | [`world_model/_schema/tokens.md`](world_model/_schema/tokens.md) (single source) |
| §8 windows / maintenance defaults | [`world_model/_schema/windows.md`](world_model/_schema/windows.md) · [`world_model/_schema/archetypes/zigbee-device.md`](world_model/_schema/archetypes/zigbee-device.md) |
| §10 Secret-safety (AD-18) | enforced by the loader validation ([`world_model/_loader/validate.py`](world_model/_loader/validate.py)) |
| §13 Future evolution (relationships, temporal/seasonal, learned baselines) | carried by the World Model roadmap — Phase WM-7+ ([`../00_overview/ROADMAP.md`](../00_overview/ROADMAP.md) → Phase WM) |
| Machine encoding (`HOME_RULES` in `bin/aurora-context`) | **retired (WM-4)** — replaced by the compiled `world_model.generated.json` evaluated by [`world_model/_evaluator/engine.py`](world_model/_evaluator/engine.py) |

## Contract notes (unchanged)

- The `aurora-context.json` **`home.anomalies` typed-token contract is unchanged**
  (AD-20 / INV-18): plain string tokens, severity-ordered, device detail in the
  Markdown rendering only.
- The modelling principle stands, generalized by AD-21: **AURORA reasons about
  the world, not about its implementation.**

Historical provenance: authored 2026-06-30 (F5.1, G-F5-01); migrated to entities
2026-07-01 (WM-2, G-WM2-1…10); evaluation cutover 2026-07-13 (WM-4).
