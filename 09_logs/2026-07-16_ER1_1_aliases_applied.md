# ER-1.1 — schema `aliases` + entity alias sets (applied)

- **Date:** 2026-07-16   **Phase:** ER-1.1   **Status:** **applied + validated — at the git gate.**
- **Class:** documentation + schema contract. **No loader, tool, projection, runtime or
  database change.**
- **Authoritative design:** [`../04_ai_system/entity_resolution_layer.md`](../04_ai_system/entity_resolution_layer.md)
  (frozen 2026-07-16); freeze log [`2026-07-16_ER1_freeze.md`](2026-07-16_ER1_freeze.md).
- **Gate:** **G-ER-1 — PASS within ER-1.1 scope** (§3). Fail-loud *enforcement* lands in the
  loader at **ER-1.2**; this sub-phase authors the specification and the data.

## 1. Implementation

**Schema** — [`../04_ai_system/world_model/_schema/entity.schema.md`](../04_ai_system/world_model/_schema/entity.schema.md):
optional **`aliases`** field added to the §2 table; new **§2.2** (semantics, shape,
normalization, authority); new **check 12** + **§5.1** sub-checks 12a–12f.
**`schema_version` stays 1** — a new optional field is additive by construction (§6 / frozen
architecture §5).

**Entities** — `aliases` added to the **six bound `home/` entities**; frontmatter only, no
prose changes, no other field touched:

| Entity | Shape | Signal → `ha_entity` | Aliases (authored, es + en) |
|---|---|---|---|
| `printer-3d` | single | `state` → `switch.impresora_3d` | impresora 3D · impresora · 3D printer · printer |
| `awning` | single | `state` → `cover.toldo` | toldo · awning |
| `main-door` | single | `state` → `binary_sensor.sensor_puerta_principal_contact` | puerta principal · puerta · main door · front door · door |
| `internet-uplink` | single | `state` → `binary_sensor.rooter_estado_wan` | internet · conexión a internet · internet uplink · internet connection · wan · uplink |
| `entrance-plant` | **multi** | `soil_moisture` → `sensor.sensor_planta_entrada_soil_moisture` | humedad de la planta · humedad del suelo · plant moisture · soil moisture |
| | | `water_warning` → `sensor.sensor_planta_entrada_water_warning` | aviso de riego · riego de la planta · plant water warning · water warning |
| `zigbee-mesh` | **multi** | `connection` → `binary_sensor.zigbee2mqtt_bridge_connection_state` | malla zigbee · red zigbee · zigbee · zigbee mesh · mesh |
| | | `permit_join` → `switch.zigbee2mqtt_bridge_permit_join` | permitir emparejamiento · permit join · pairing mode |

**33 unique normalized aliases → 8 `ha_entity` targets across 6 entities.**
`battery` / `firmware` (aspects, no `binding`) and `daylight-time` (`environment`, optional in
the freeze) take **no** aliases — D-ER-6.

Alias sets are **grounded in reality, not invention**: the live HA `friendly_name` of each
bound entity was read from `/api/states` (e.g. `switch.impresora_3d` = *"Impresora 3D"*,
`cover.toldo` = *"Toldo"*), and the English forms match what the model actually reached for in
the audit evidence (`switch.3d_printer`, `cover.awning`, `sensor.internet_connection_status`).
Authoring choices — including what was deliberately **not** aliased — are recorded in §2.1.

## 2. Governing decisions (ratified elsewhere — **not** re-ratified here)

Authoring the real alias sets surfaced two architectural gaps: the **multi-signal alias shape**,
and **whether an alias may equal an entity identifier**. Both are architectural decisions, not
implementation details, so they were escalated and ratified into the **ER-1 freeze as
Revision 2** — in **its own commit, immediately before this one**, so history reads *design
amended → contract applied*. **This sub-phase applies them; it neither restates nor
re-ratifies them.**

| What | Where |
|---|---|
| **D-ER-11** (aliases mirror the `binding` shape) · **D-ER-12** (alias vs entity identifier) | [`../04_ai_system/entity_resolution_layer.md`](../04_ai_system/entity_resolution_layer.md) **§3.5** |
| Amendment log — rationale, evidence, correction of record | [`2026-07-16_ER1_freeze_rev2.md`](2026-07-16_ER1_freeze_rev2.md) |

### 2.1 Authoring choices belonging to this sub-phase

These are ER-1.1's own, and are recorded here rather than in the freeze:

- **Ambiguous names are deliberately unaliased.** A bare *"planta"* / *"plant"* maps to two
  signals of `entrance-plant` with no non-arbitrary winner, so **no alias is authored**. A
  closed deterministic resolver must never guess; that question is answered from the awareness
  block, not a tool call.
- **`prusa` was deliberately not aliased.** The model guessed `switch.prusa` in the audit
  evidence, but no brand is recorded anywhere in the World Model or in Home Assistant. An alias
  is not a place to invent a fact.
- **Aliases are authored in natural form, accents included** (`conexión a internet`); D-ER-8
  normalization is the loader's job at ER-1.2, not the author's.

## 3. Validation (real, this session)

| Check | Result |
|---|---|
| Real tree remains valid — unmodified WM-3 loader `--check` | **PASS** (9 entities / 9 rules) |
| Existing loader suite (19) · evaluator suite (36) | **PASS · PASS** |
| **Aliases are inert until ER-1.2** — fresh compile vs on-disk artifact | **only `provenance.sha256` differs**; no `aliases` key emitted; `registries` / `emission_order` / `graph` / `stats` **unchanged** |
| 12a shape · 12b type/bounds · 12c not id-shaped · 12d global uniqueness · 12e no cross-entity id collision · 12f no archetype aliases | **PASS ×6** against the **applied files** (parsed via the loader's own frontmatter parser) |
| Aspects carrying aliases (must be 0) | **0** |

**The gate was negative-controlled** — a check that cannot fail proves nothing. Against a
disposable copy of the tree, each fault class was injected and confirmed caught, then reverted
and confirmed clean: duplicate normalized alias (12d), archetype-level alias (12f), id-shaped
alias (12c), and a cross-entity id collision (12e, isolated with a non-aliased entity id so it
could not be masked by 12d). Baseline passed before and after, proving the faults — not a
sticky failure — caused each rejection.

**Runtime untouched:** `world_model.generated.json` not regenerated (ER-1.1 forbids runtime
change; it is regenerated at ER-1.2 when the loader learns to emit `resolution`); tools still
v0.1.0; `aurora-context.json` untouched; no container, cron or database change.

## 4. Deferred to ER-1.2 (not done here — deliberately)

Fail-loud **enforcement** of check 12 in `_loader/validate.py`; normalization in
`_loader/normalize.py` (N9); the `resolution` registry in `_loader/emit.py`; the
`aliases`-in-archetype guard in `_loader/resolve.py`; regeneration of the compiled artifact.
Until then the aliases are **authored data with no runtime effect** — proven in §3.

## 5. Rollback

`git revert` of the ER-1.1 commit; re-run the loader. Additive frontmatter and an additive
schema section only — no runtime state, no generated artifact, no database, nothing to undo
beyond the documents. `schema_version` never moved, so no migration exists to reverse.

## 6. Status

**ER-1.1 COMPLETE — at the git gate.** Next: **ER-1.2** (loader: normalizer, check-12
enforcement, `resolution` registry, tests; gates G-ER-1 full, G-ER-2 loader half, G-ER-5).
No `git commit` / `push` / `tag` without explicit operator approval requested immediately
beforehand (`PROJECT_RULES.md` → Operator Git Approval).
