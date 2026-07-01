# Collector Registry — canonical, single-source

- **Role:** the **single source of truth** for valid `collector` ids. Every entity's `collector`
  field (schema §2) must reference a collector defined here; validation check #7 ("every
  referenced `collector` exists") resolves against this file.
- **Authority:** conforms to [`../world_model_architecture.md`](../world_model_architecture.md)
  §1.3 (Collectors bind signals to the model) and §4.5 (duration/`last_changed` contract).
  Closes **F-WM1-a** (WM-1 apply log §4 — the enumerated collector set the schema's coverage
  check needs). Grounded in the live signal surface read by `bin/aurora-context` (read-only
  cross-check — not modified).
- **What a collector is:** a deterministic signal source that supplies **live state** for the
  entities bound to it. A collector observes reality; it does **not** interpret meaning
  (interpretation is Awareness). Collectors sit on the deterministic side of the **B3** seam.
- **What a collector is not:** it is **not** a data store and holds no baselines. Real ids live
  in each entity's `binding`; the collector is only the *source* that resolves those ids to
  current values.

---

## Registry

| Collector id | Source | Exposes (per bound entity) | Failure mode | Status |
|---|---|---|---|---|
| `ha-states` | Home Assistant REST `GET /api/states` (host-side; `HA_BASE_URL` + `HA_LLAT` from `ai-stack/.env`, token never printed — AD-18) | `state` (string), numeric value (for numeric sensors), **`last_changed`** (timestamp) | fail-loud → whole-block **`ha_unavailable`** degradation (`tokens.md`; `home_state_design §4.3`) | **active** |

`ha-states` is the **only** collector any home-region entity binds to (WM-2). Every evaluable
home entity — `zigbee-mesh`, `internet-uplink`, `printer-3d`, `awning`, `main-door`,
`entrance-plant`, `battery` — declares `collector: ha-states`.

### Duration / `last_changed` contract (schema §3; frozen §4.5)

`ha-states` exposes **`last_changed`** on every entity, so any entity carrying a `field for
DURATION` rule may bind it (satisfying validation 11b). The specific duration rules live in the
entities, not here.

### Failure semantics (reality wins)

This is the **collector's own** failure contract only: when `GET /api/states` fails at generation
time, `ha-states` supplies no state at all → the whole home block degrades to **`Home State:
Unavailable`** with `home.anomalies[] = ["ha_unavailable"]` (the reserved, tier-less token in
`tokens.md`). How a *present* `unavailable` / `unknown` reading for an individual entity is
treated is **not** the collector's concern — it is entity/evaluator-owned (D7 default raises no
token; `zigbee-mesh` overrides via its `status_semantics`).

## Anticipated / reserved (not yet referenced — do not author entities against these)

Named here so the ids are reserved and coverage validation has a stable target when the
**infrastructure** region lands (WM-7+). **No WM-2 entity references any of these**; they are
listed only to reserve the names (YAGNI — frozen §12 W-14). The *Anticipated source* column is
**illustrative, not binding** — WM-7 defines each collector's real contract when it lands.

| Collector id | Anticipated source | For |
|---|---|---|
| `backup_status` | `bin/backup-probe` → `backup_status.json` (F-2) | infrastructure/backup |
| `container_status` | `bin/container-probe` → `container_status.json` (F-2) | infrastructure/containers |
| `health` | `ai-stack/ingest/logs/health.json` (E-3) | infrastructure/ingest-pipeline |
| `torre-probe` | live Torre GPU Ollama probe (`system_status`) | infrastructure/compute-torre |

## Change policy

Adding a collector is **additive** (no `schema_version` bump). A collector id is **append-only**
— never reused or repurposed (Memory references awareness produced from it across years). Moving
a collector from *anticipated* to *active* is a content change, made when the first entity binds
it (with its own validation).
