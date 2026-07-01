# Entity Schema — World Model operative contract

- **Role:** the **single operative schema contract** for the World Model — the reference that
  entity authors (WM-2+) and the future loader/compiler (WM-3) both conform to.
- **Authority:** this document **conforms to and cites** the frozen architecture
  [`../../world_model_architecture.md`](../../world_model_architecture.md) — §4 (authoring
  format), §4.7 (validation), §5 (versioning). **The frozen document is authoritative**; if
  this contract ever conflicts with it, the freeze wins and this file is corrected. A change
  to the *contract itself* is a `schema_version` event (§ Versioning) and, where it touches a
  frozen invariant, a gated architecture decision — never silent drift.
- **`schema_version`: 1** (the initial contract era; unchanged by WM-2 — its clarifications are additive).
- **Status:** operative contract. WM-1 authored the foundation; **WM-2** added the §2.1
  binding/roster clarifications (additive; `schema_version` unchanged). The loader is **WM-3**.

---

## 1. The literate contract (frozen §4.2)

Each entity is one Markdown file: **YAML frontmatter is the single authoritative machine
surface; the prose body is explanatory and carries no authoritative data.** The loader reads
values **only** from frontmatter. Prose may narrate a baseline, but a prose/field
contradiction is a validation error.

**Naming (frozen §4.1):** entity `id` and filename `kebab-case` (`filename == <id>.md`);
anomaly tokens `snake_case`; field names `snake_case`. One directory per region; one file per
entity.

## 2. Fields (frozen §4.3)

Legend — Req: ✅ required · cond: conditional (required when the entity is evaluable / bound /
an aspect, per Notes) · opt: optional.

| Field | Req | Type / values | Notes |
|---|---|---|---|
| `id` | ✅ | kebab slug, unique, `== filename` | the model key |
| `name` | ✅ | string | human display |
| `region` | ✅ | `infrastructure`·`home`·`projects`·`operator`·`self`·`environment` | placement |
| `kind` | ✅ | `device`·`service`·`pipeline`·`project`·`person`·`self`·`environment`·`aggregate`·`aspect` | class |
| `status` | ✅ | `active`·`draft`·`retired` | lifecycle visibility (frozen §3) |
| `schema_version` | ✅ | integer | contract era (§ Versioning) |
| `priority` | cond | `critical`·`high`·`medium`·`low` | required if the entity can deviate; drives severity ordering |
| `baseline` | cond | `{state: …}` \| `{schedule: …}` \| `{conditions: […]}` | the exact "normal"; required if evaluable |
| `binding` | cond | map: `ha_entity` \| `container` \| `corpus` \| `probe` \| `signal` | implementation link — **real ids live here, not in prose**; single- or named-multi-signal (§2.1) |
| `collector` | cond | signal-source id | which Collector supplies live state; required if evaluable |
| `anomaly_rules` | cond | `[{ token, condition, window? }]` | deterministic deviation rules (§3 grammar); required if the entity can deviate |
| `writable` | opt (`false`) | bool | **descriptive only; validated ⊆ the `ha_call_service` allowlist; never a grant (INV-17)** |
| `boundary` | cond | `read_only` · `collaboration_context_only` | **descriptive; mirrors the enforced boundary, never replaces it (INV-17)**; required for Guardian/operator entities |
| `archetype` | opt | archetype id (`_schema/archetypes/<id>`) | shallow shared defaults (§4) |
| `depends_on` | opt | `[id]` | directed causal edge |
| `part_of` | opt | id (an `aggregate`) | composition membership |
| `applies_to` | cond | selector | required for `kind: aspect` — the entities the aspect covers; may be a member roster over modelled entities and/or raw bindings (§2.1) |
| `status_semantics` | opt | rules (e.g. `{ unavailable: down }`) | verdict derivation override |

**Prose (required):** `## Purpose`, `## Reasoning`, `## Suggested operator actions` (the last
optional for pure-reference / boundary entities).

### 2.1 Binding shapes and field resolution (WM-2 additive clarification — `schema_version` 1)

`binding` links an entity to the real signals a Collector supplies. Two shapes, both valid; this
clarification is **additive** (no `schema_version` bump — D-WM2-1):

- **Single-signal** — `binding: { ha_entity: <id> }` (or `container` / `corpus` / `probe` /
  `signal`). Exposes the reserved field **`state`** (the bound entity's state string) and
  **`last_changed`** (its last-change timestamp). This is the frozen §4.6 shape.
- **Named multi-signal** — `binding: { <signal>: { ha_entity: <id> }, … }`, one named signal per
  bound entity. Each `<signal>` name is a **field** usable in `condition`s and `baseline`; it
  exposes that signal's value and its own `last_changed`. There is **no** implicit `state` on a
  multi-signal binding — every field is named. Used by `zigbee-mesh` (`connection`,
  `permit_join`) and `entrance-plant` (`water_warning`, `soil_moisture`).

**Field resolution (grammar §3).** A `field` in a `condition` (or `baseline` condition) resolves
to the reserved **`state`** (single-signal) or a **named signal** (multi-signal), interpreted as
the signal's **state string** for state comparisons (`==`, `!=`) and the `field unavailable`
predicate, and as its **numeric value** for numeric comparisons (`<`, `>`, `<=`, `>=`).
**`last_changed`** is the bound
entity's / named signal's last-change timestamp, used **only** by the `field for DURATION`
predicate.

Only awareness-relevant signals (those a rule or `baseline` reads) live in `binding`.
Informational implementation entity_ids that no rule reads (e.g. printer power metering, awning
motor status, Z2M version) are recorded in the entity's prose as the known implementation surface
— they are names/ids, not authoritative machine fields (AD-18: names/ids only, never secrets).

**Aspect rosters (`applies_to`; D-WM2-3).** A `kind: aspect` entity may declare `applies_to` as a
**roster of members**, each referencing a **modelled entity** (`entity: <id>`) and/or a **raw
collector binding** (an entity_id), tagged with the member's signal kind. This lets a
cross-cutting aspect (e.g. `battery`) cover devices that are deliberately **not** modelled as
operational entities (privacy exclusion, `home_model.md §9`) without inventing entities for them.
The aspect's rule is a **fold over the roster**: the `anomaly_rules` condition is a per-member
template (only the field matching a member's kind is evaluated; absent fields never trip); any
member tripping emits the token **once**; member names appear in the **rendering only**, never in
the token (AD-20 / D1); duplicates de-dup by name. A roster aspect's `baseline` (all members
within their per-member normal) is documented in prose. The fold's mechanical evaluation is a
**loader (WM-3)** concern; WM-2 records the roster and the intended semantics.

## 3. Condition grammar (frozen §4.5 — closed)

```
condition := disj ; disj := conj ('OR' conj)* ; conj := neg ('AND' neg)*
neg := 'NOT'? predicate | '(' condition ')'
predicate := field COMP value
           | 'time' 'in' <window>
           | field 'unavailable'
           | field 'for' DURATION
COMP := == != < > <= >=
DURATION := COMP <n><unit>   (unit ∈ s | m | h)
```

No functions, no arithmetic, no free variables. **Severity is not authored per rule** — it is
looked up from [`tokens.md`](tokens.md) by token. **Windows** are named and tz-anchored in
[`windows.md`](windows.md). A `field` resolves to a binding signal per §2.1.

**Worked examples (one per predicate form):**

| Form | Example condition | Real rule |
|---|---|---|
| comparison | `state == on` | `printer_on_overnight` (with window) |
| numeric comparison | `soil_moisture < 20` | `plant_soil_dry` |
| `time in <window>` | `state == on AND time in overnight` | `printer_on_overnight` |
| `field unavailable` | `state == off OR state unavailable` | `zigbee_bridge_down` |
| `field for DURATION` | `state == on for > 15m` | `door_open_extended` |

**Duration is stateless (B3 preserved).** `field for DURATION` = `now − last_changed(field)
COMP DURATION`, using the `last_changed` timestamp in the **current** signal — awareness stays
a pure function of the current signal. **Collector contract:** a collector bound to an entity
with a duration rule must expose `last_changed`.

## 4. Relationships & composition (frozen §4.4)

- **`depends_on`** — directed causal edge (a device depends on the mesh). Reverse edges
  (`affects` / dependents) are **derived by the loader, never authored**.
- **`part_of`** — composition into an `aggregate` (a member device is `part_of` an aggregate).
- **Aspects** (`kind: aspect`) — cross-cutting checks (e.g. battery) applied to a set of
  entities via `applies_to`. Not entities of their own domain; composed *onto* others.
  `applies_to` may be a member roster over modelled entities and/or raw collector bindings, and
  the rule folds over the roster (§2.1).
- **Archetypes** — *optional, shallow, one-level* shared defaults merged by the loader unless
  the entity overrides them. **Deep inheritance is rejected** (no archetype-of-archetype).

## 5. Validation ruleset (frozen §4.7 — fail-loud)

Authored here as the **specification**; the loader (WM-3) enforces it and **fails loud** on any
violation (never emits a partial model).

| # | Check | Rule |
|---|---|---|
| 1 | **Structural** | required fields present; enums valid; types correct |
| 2 | **Grammar** | every `condition` parses under §3; windows tz-anchored |
| 3 | **Token** | every rule `token` ∈ [`tokens.md`](tokens.md); severity resolved there (not authored) |
| 4 | **Referential** | `id` unique; `depends_on`/`part_of`/`applies_to`/`archetype` referents exist; **no dependency or archetype cycles**; `part_of` → an `aggregate` |
| 5 | **Safety (AD-18)** | no ip / token / secret / raw payload in any field or prose; bindings are names/ids only |
| 6 | **Boundary** | `guardian-cloud` = `read_only` ⇒ not `writable`, no `anomaly_rules`; `operator` carries no presence/occupancy fields |
| 7 | **Coverage** | every registry token is produced by ≥1 rule (or reserved); every referenced `collector` exists in [`collectors.md`](collectors.md) |
| 8 | **Prose** | required sections present; no prose value contradicts its authoritative field |
| 9 | **Lifecycle** | `retired` excluded from evaluation, retained for retrieval; nothing `active` may `depend_on` a `retired` entity |
| 10 | **Version** | declared `schema_version` consistent with the fields used |
| 11a | **Authorization (INV-17)** | `writable: true` ⇒ the entity's action surface is a subset of the `ha_call_service` allowlist; `writable`/`boundary` never grant beyond the enforced authorization |
| 11b | **Duration/collector** | any entity with a `field for DURATION` rule must bind a `collector` that exposes `last_changed` |

## 6. Versioning (frozen §5)

- **`schema_version`** — integer, **per-entity**, bumped **only on breaking changes**;
  additive changes (new optional field, token, enum, archetype, grammar predicate) do **not**
  bump it.
- **Backwards compatibility** — the loader reads the current major **and ≥1 prior** (bounded
  window); an unsupported/future version **fails loud**.
- **Token/id permanence** — tokens and ids are **append-only, never reused or repurposed** (a
  retired token stays `reserved`) — Memory references them across years.
- **Deprecation** — deprecate → grace period (warning) → remove at a MAJOR, announced; never
  silent. Safety/boundary rules may *tighten* freely; *loosening* is a high-gate MAJOR.

## 7. Generated artifact & loader (frozen §4.8 — WM-3, not WM-1)

The loader compiles these docs → `world_model.generated.json` (fully resolved: archetype
defaults merged, aspects expanded, reverse edges derived, rules compiled, severity resolved).
That artifact is **derived, gitignored, fully regenerable, never canonical**. The loader is
deterministic/idempotent (**Parse → Resolve → Validate → Emit → Serve**), fail-loud, and
**read-only w.r.t. canonical docs**. **The loader is built at WM-3, not here.**
