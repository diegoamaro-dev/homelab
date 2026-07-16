# ER-1.2 — loader: D-ER-8 normalization, check-12 enforcement, resolution registry (applied)

- **Date:** 2026-07-16   **Phase:** ER-1.2   **Status:** **implemented + validated — at the git gate.**
- **Class:** loader implementation + tests + the additive emitted registry. **No tool, no
  projection, no evaluator/filter/awareness code change.** One runtime side-effect: the
  compiled artifact was regenerated (§4).
- **Authoritative design:** [`../04_ai_system/entity_resolution_layer.md`](../04_ai_system/entity_resolution_layer.md)
  (frozen, Revision 2). Decisions are cited here, never re-ratified.
- **Gates:** **G-ER-1 CLOSED** · **G-ER-2 loader half PASS** · **G-ER-5
  implementation-validated, NOT closed** (§3.4).

## 1. Implementation

| File | Change |
|---|---|
| `_loader/resolution.py` | **new** — `normalize_alias()` (D-ER-8, single source), `authored_map()` / `normalized_pairs()` (shape-aware, D-ER-11), `build()` (the registry) |
| `_loader/normalize.py` | **N9** — stamps `aliases_normalized` at stage ③, so Validate compares canonical forms and Emit is byte-deterministic |
| `_loader/model.py` | `ParsedEntity.aliases_normalized` |
| `_loader/validate.py` | **check 12** (12a–12f), fail-loud, appended to the check chain |
| `_loader/emit.py` | additive `resolution` key; omitted entirely when no entity carries aliases |
| `_loader/__init__.py` | `LOADER_VERSION` 0.1.0 → **0.2.0**; `ARTIFACT_VERSION` **unchanged at 1** |
| `_loader/tests/test_resolution.py` | **new** — 23 tests (G-ER-1 + G-ER-2 loader half) |

**`LOADER_VERSION` → 0.2.0** — minor/additive: a new validation contract and a new emitted
key, no breaking change to any consumer. It is stamped in `generator.loader_version`, so it is
real provenance. **`ARTIFACT_VERSION` stays 1 (D-ER-7)**: `_evaluator/engine.py` pins
`SUPPORTED_ARTIFACT_VERSIONS = (1,)` and `bin/aurora-context` **catches** `ArtifactError` and
fails soft to `Home State: Unavailable` — a bump would not fail loud, it would silently
degrade awareness nightly and quietly undo the WM-6 / G-F5-04 closure.

### 1.1 Implementation-inventory correction (not an architectural decision)

The spec's §10 inventory over-listed three files. Verified against the code, **none needs to
change**; §10 was corrected to match reality:

- **`parse.py`** — frontmatter loads wholesale into `.fm`, so `aliases` is already available.
  Alias *shape* is a validation concern (12a), not a parse-surface error.
- **`resolve.py`** — the archetype merge writes to `.archetype_applied` and **never** mutates
  `.fm` (proven: `printer-3d.fm` has no `depends_on`, while `archetype_applied` does). The
  registry reads only `.fm`, so an archetype alias is **structurally invisible** to it.
- **`test_emit_determinism.py`** — it serialises and compares the **whole** artifact, so it
  already covers any newly emitted key.

`model.py` was **added** (it carries the N9 field). The §3 decisions are untouched.

### 1.2 How aliases stay out of archetype inheritance — two layers

1. **Structural (pre-existing, verified):** archetype defaults land in `.archetype_applied`,
   never in `.fm`; the registry reads only `.fm`, so an archetype alias could never fan out
   across members.
2. **Explicit and fail-loud (12f):** `validate.py` rejects `aliases` in any archetype's
   `defaults`. **Validate runs before Emit**, so nothing is ever written — defence in depth
   against a future refactor that merges defaults into `.fm`.

### 1.3 The registry carries no authorization-adjacent field

`resolution.build()` never reads `writable`, and each target carries only
`entity` / `name` / `region` / `domain` / `signal` / `aliases`. A consumer therefore **cannot**
mistake the registry for an allowlist. D-12 remains the sole authority (**INV-17**); the
resolver is never consulted to permit or deny (**D-ER-9**). Asserted by test
(`test_registry_carries_no_authorization_field`), not left to convention.

## 2. Emitted structure (additive)

```json
"resolution": {
  "normalization": "casefold|nfkd|strip-marks|collapse[\\s._-]|trim",
  "aliases":  { "impresora 3d": "switch.impresora_3d", … },     // 33, sorted by key
  "targets":  { "switch.impresora_3d": { "entity": "printer-3d", "name": "3D printer",
                 "region": "home", "domain": "switch", "signal": "state",
                 "aliases": ["impresora 3D", …] }, … },          // 8, sorted by entity_id
  "stats":    { "aliases": 33, "targets": 8, "entities": 6 }
}
```

**33 aliases → 8 targets across 6 entities.** The ER-1 objective is now real in the artifact:
`"impresora 3d"` → `switch.impresora_3d` — the resolution whose absence produced 13 unverified
writes. Multi-signal entities resolve **per signal** (D-ER-11): `"permit join"` →
`switch.zigbee2mqtt_bridge_permit_join`, `"zigbee mesh"` →
`binary_sensor.zigbee2mqtt_bridge_connection_state`. The ambiguous bare `"planta"` / `"plant"`
is **absent by design** — a closed resolver must never guess.

## 3. Validation (real, this session)

### 3.1 G-ER-1 — CLOSED

Enforcement now lives in the **real loader**; the ER-1.1 scratchpad gate tool is retired and
replaced by `_loader/tests/test_resolution.py`. Every fault class is injected into the real
tree in memory and asserted to **fail loud**:

| Fault injected | Check | Result |
|---|---|---|
| Duplicate normalized alias (`"Toldo"` onto `main-door`) | 12d | **rejected** |
| Archetype-level alias (`zigbee-device.defaults`) | 12f | **rejected** |
| Id-shaped alias (`"cover.toldo"`) | 12c | **rejected** |
| Cross-entity id collision (`"entrance plant"` on `printer-3d`) | 12e | **rejected** |
| Aliases on an unbound aspect (`battery`) | 12a | **rejected** |
| Flat list on a multi-signal binding | 12a | **rejected** |
| Map on a single-signal binding | 12a | **rejected** |
| Undeclared signal key | 12a | **rejected** |
| Alias below the length bound | 12b | **rejected** |
| **Real tree** (positive control) | — | **valid** |
| **Alias equal to its OWN entity id** (`awning`, `main door`, `internet uplink`) | 12e converse | **allowed** — must not be rejected (D-ER-12) |

12e is isolated with a **non-aliased** entity id so 12d cannot mask it.

### 3.2 G-ER-2 — loader half PASS

Table-driven over the frozen D-ER-8 spec: casefold, trim, NFKD + mark-strip
(`"Conexión a Internet"` → `"conexion a internet"`), separator collapse (`_`, `-`, `.`,
whitespace runs), and `ñ → n` recorded as accepted. Normalization proven **idempotent**, and a
normalized alias proven **never id-shaped** — which is *why* 12c tests the raw string. Registry
proven byte-stable across builds and sorted. The **tool half** closes at ER-1.4.

### 3.3 Test results

| Suite | Result |
|---|---|
| Loader (19 baseline + 23 new) | **42 passed** |
| Evaluator | **36 passed** — run against the **regenerated real artifact** |

### 3.4 G-ER-5 — implementation-validated, **NOT closed**

| Evidence | Result |
|---|---|
| Loader suite | 42 green |
| Evaluator suite **against the regenerated artifact** (`test_awareness.py` calls `engine.load_artifact()`) | 36 green |
| `artifact_version` | **still 1** |
| Artifact diff (BEFORE 0.1.0 vs AFTER 0.2.0) | **additive `resolution` only**; `registries` / `emission_order` / `graph` / `stats` **unchanged**; entities differ **only** in `provenance.sha256` (the ER-1.1 alias edits); no `aliases` key leaked into any entity block |
| Evaluator / filter / awareness code | **0 changes** |

**Deliberately NOT done:** `bin/aurora-context` was **not** run. It writes production awareness
artifacts and its output depends on live HA state at that instant, so a before/after comparison
would be neither clean nor byte-stable. **Production awareness artifacts are not mutated to
manufacture evidence.**

**G-ER-5 therefore splits:**
- **Implementation validation — PASS** (this session, evidence above).
- **Operational non-regression — PENDING.** Closes only when the **next unattended 04:15
  cycle** completes successfully against the regenerated artifact. Until then G-ER-5 is
  **open**, tracked honestly — the same discipline that closed G-WM4-6.

## 4. Runtime side-effect (the only one)

`world_model.generated.json` was **regenerated**, and only **after** the loader gates passed:
`loader_version` 0.1.0 → 0.2.0, `docs_commit` `86ae969e` → `f983a04f`, plus the additive
`resolution` block. The pre-change artifact was preserved first and used for the §3.4 diff.

The previous artifact was **stale**: generated 2026-07-13 at `docs_commit 86ae969e`, it
predated ER-1.1, so its provenance hashes no longer matched the aliased entity files.
Regenerating reconciles that. The artifact is **gitignored, derived and regenerable** — never
canonical.

## 5. Rollback

`git revert` the ER-1.2 commit, then re-run the loader: the artifact regenerates **without**
`resolution` and with `loader_version` 0.1.0. No schema, entity, tool, database or awareness
state to unwind. `ARTIFACT_VERSION` never moved, so the evaluator is unaffected in either
direction — and it ignores the additive key regardless, so even a stale artifact carrying
`resolution` is harmless.

## 6. Discovered — recorded, not silently fixed

**F-ER12-1 — check 12a does not require an aliased signal to bind `ha_entity`.** The registry
maps an alias to a real HA `entity_id`; a signal bound to `container` / `corpus` / `probe` /
`signal` has no id to resolve to, so such an alias would be **dead**. The ratified 12a requires
only that the key be a *declared* signal. **Currently unreachable** — all six aliased entities
bind `ha_entity` — and guarded **fail-loud** in `resolution.build()` (`ResolutionError`) rather
than silently dropping a target. Proposed for ratification into 12a at ER-1.3 or the ER-1.5
closeout; **not** self-approved here.

## 7. Documentation reconciliation

Seven stale ER-1 status claims across the triad (all three documents asserted "at the git gate"
for work already published) were reconciled against reality: Rev 2 = `3ebf59d1`,
ER-1.1 = `f983a04f`, both pushed. `AMAROLAB_HANDOFF.md` additionally still said
*"Next: ER-1.1"*. The triad is an operational source of truth and must not knowingly remain
stale. Spec §10's inventory was corrected per §1.1.

## 8. Status

**ER-1.2 COMPLETE (implementation) — at the git gate.** **G-ER-1 CLOSED**, **G-ER-2 loader
half PASS**, **G-ER-5 open** pending the unattended cycle. Next: **ER-1.3** (projection emitter
+ `aurora-entities.json`; gate G-ER-6).

**Aurora's behaviour is still unchanged**: the tools remain v0.1.0, no consumer reads the
registry, and the 13 historical unverified writes would still be reported as successful today.
ER-1 changes reality at **ER-1.4b**, when ER-1-C1 lands. No `git commit` / `push` / `tag`
without explicit operator approval requested immediately beforehand (`PROJECT_RULES.md` →
Operator Git Approval).
