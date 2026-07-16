# Entity Resolution Layer (ER-1) — ratified design

- **Status:** **FROZEN 2026-07-16** (operator-ratified) — **Revision 2**. Implementation is
  Phase **ER-1** (ER-1.0 → ER-1.5); each sub-phase ends at a **STOP** git gate.
- **Amendments to the freeze** (a frozen design is amended only by a **gated, operator-ratified
  decision** — never by silent drift):

  | Rev | Date | Amendment | Ratified at |
  |---|---|---|---|
  | 1 | 2026-07-16 | Initial freeze — D-ER-1…10 + ER-1-C1 | ER-1.0 |
  | **2** | **2026-07-16** | **D-ER-11** (alias shape mirrors `binding`) · **D-ER-12** (alias vs entity-identifier collision — check 12e) | **ER-1.1** |
- **Role:** the deterministic bridge between natural language and real Home Assistant
  `entity_id`s, plus mandatory write verification. It is the remedy for the defect recorded in
  [`../09_logs/2026-07-14_ER1_entity_resolution_finding.md`](../09_logs/2026-07-14_ER1_entity_resolution_finding.md).
- **Authority:** this document **conforms to and cites** the frozen World Model architecture
  [`world_model_architecture.md`](world_model_architecture.md) (AD-21). **The freeze is
  authoritative**; if this document ever conflicts with it, the freeze wins and this file is
  corrected. ER-1 **amends no frozen decision and adds no architectural concept** — §7 of the
  freeze already states the intent:
  > *"Entity registry ends id-hallucination — real entity_ids live in `binding`; Aurora can
  > answer 'that isn't an entity I model' instead of inventing ids."*
  ER-1 implements that intent. **No architecture amendment is required.**
- **Relation to Phase WM:** independent. WM-6 closed G-F5-04 (awareness convergence);
  ER-1 covers **actuation**, which WM never validated. ER-1 is **not** WM-5.5 — no work is
  retroactively inserted into a published phase.

---

## 1. Defect (real evidence)

Natural-language device requests do not resolve to the real entity id
(`switch.impresora_3d`). The model invents plausible ids; on the **write** path, Home
Assistant answers **HTTP 200 with an empty changed-states list** for an entity that does not
exist, and `ha_call_service` v0.1.0 maps that to `result_code:"ok"` — **a write reported as
successful without the resulting state ever being verified.**

**Measured, live** (`amarolab-audit.log{,.1}`, 2026-06-16 → 2026-07-14; each id re-probed
against `/api/states` on 2026-07-16 and confirmed **HTTP 404 — does not exist**):

| entity_id | service | `result_code` | calls | exists in HA |
|---|---|---|---|---|
| `switch.3d_printer` | `switch.turn_on` / `turn_off` | `ok` | 6 + 1 | **no (404)** |
| `switch.3dprinter` | `switch.turn_on` | `ok` | 1 | **no (404)** |
| `switch.printer` | `switch.turn_on` | `ok` | 1 | **no (404)** |
| `switch.prusa` | `switch.turn_on` | `ok` | 1 | **no (404)** |
| `switch.filament_heater` | `switch.turn_on` | `ok` | 1 | **no (404)** |
| `automation.next_backup` | `automation.trigger` | `ok` | 1 | **no (404)** |
| `cover.awning` | `cover.open_cover` | `ok` | 1 | **no (404)** |
| **`switch.impresora_3d`** | `switch.turn_on` / `turn_off` | `ok` | 4 + 3 | **yes** (real actuation) |

**13 unverified writes across 7 non-existent ids were reported as successful.**

Two properties of the evidence are load-bearing for the design:

1. **The failure requires a live domain.** HA answers 200 + empty list only when the service
   exists (`switch`, `automation`, `cover` are live) and the entity does not. Where no service
   exists the call fails honestly (`light.kitchen` never reached HA — it failed input
   validation; `cover.close` → `ha_error`). The defect is therefore **specific to domains
   Aurora can really actuate**.
2. **The audit log cannot presently distinguish a real actuation from an unverified write.**
   `switch.impresora_3d → ok` and `switch.3d_printer → ok` are byte-identical audit lines.
   Restoring that distinction is an ER-1 acceptance condition, not a side effect.

**The read path is not defective.** `ha_get_state` already answers `not_found` for invented
ids (measured: `switch.3d_printer`, `cover.awning`, `light.server_light`, … all `not_found`).
ER-1's read-side change is therefore purely additive.

### 1.1 Root cause

1. **No runtime source of real entity ids** — the F-1 `params.system` contains **zero**
   entity_ids (verified against `webui.db`, 4 478 chars); the injected Home State block
   carries friendly names only; the ids live solely in World Model `binding` fields the model
   never sees.
2. **Misleading tool docstring examples** (`light.kitchen`, `climate.lounge`) teach
   English-style guesses; the real id is Spanish (`impresora_3d`).
3. **No corrective feedback on writes** — HA 2xx + empty list → `"ok"`; the model cannot learn
   the id was wrong.
4. **No resolution layer** between natural language and the tool boundary.

---

## 2. Scope

ER-1 fixes two **independent** defects in one gated phase:

- **D1 — resolution absent.** Natural language never reaches a real `entity_id`.
- **D2 — unverified success.** A write is reported successful without the resulting state
  being verified.

The two remedies are complementary and **deliberately not co-dependent**: ER-1-C1 is the
verification net that holds **regardless of whether the registry knows the entity**, while
the resolution layer makes the common path work. If only one existed, C1 is the one that
removes the false success claim.

**Out of scope** (unchanged by ER-1): the frozen F-1 `params.system`; the HA voice path (HA
Assist has its own alias mechanism and the printer is intentionally not voice-exposed); the
D-12 allowlist; the awareness pipeline; Guardian Cloud.

---

## 3. Ratified decisions (2026-07-16)

| # | Decision |
|---|---|
| **D-ER-1** | Entity **frontmatter is the source** of natural names — an additive optional `aliases` field on World Model entities (es + en). |
| **D-ER-2** | **Behaviour is decided by input shape, not by operation type** — see §3.3. A **natural-language miss fails closed** (`unknown_entity`, no HTTP call); a **syntactically valid `entity_id` continues directly to Home Assistant exactly as today**. ER-1 changes only the **reporting** layer (C1). |
| **D-ER-3** | The **same `entity_id` parameter** accepts natural names — no new tool parameter, no contract split. |
| **D-ER-4** | The projection is **regenerated at loader emit** — never hand-edited. |
| **D-ER-5** | **Emitter split.** The loader emits the `resolution` registry **into the artifact** (staying pure and in-tree); a consumer-side `bin/emit-entity-projection` derives `aurora-entities.json`. Writes into `ai-stack/aurora/` remain owned by the consumer side, matching `bin/aurora-context`. |
| **D-ER-6** | **Registry scope (v1)** = `binding` signals of modelled entities only. `battery.md`'s roster raw bindings (unmodelled devices, privacy-excluded) are **deferred**; aspects carry no `binding` and take no aliases. |
| **D-ER-7** | **`ARTIFACT_VERSION` stays 1.** `resolution` is an **additive** top-level key. Rationale below — this is not a stylistic choice. |
| **D-ER-8** | **Frozen normalization spec**: casefold → NFKD → strip combining marks → collapse `[\s._-]+` to a single space → trim. `ñ → n` is accepted (negligible collision risk on device names). Determinism gates depend on this text being frozen. |
| **D-ER-9** | **No write-surface restriction.** A syntactically valid HA `entity_id` follows the current path **exactly as today**. D-12 remains the **sole** authorization authority. The World Model registry is a **name-resolution convenience only** — never a write allowlist, never consulted to permit or deny. Any stronger restriction is a **future architectural decision**, out of ER-1 scope. |
| **D-ER-10** | **Closed expected-state map** for verification: `turn_on → on`, `turn_off → off`, `open_cover → open`, `close_cover → closed`. Every other service returns **`applied_unverified`**. `toggle` is deferred (its expected state depends on a before-state that after-only verification does not have). |
| **D-ER-11** *(Rev 2 — ratified at ER-1.1)* | **Aliases mirror the `binding` shape.** A **single-signal** entity uses a **flat alias list**; a **multi-signal** entity uses a **per-signal alias map**. **No implicit primary signal is introduced** — see §3.5. |
| **D-ER-12** *(Rev 2 — ratified at ER-1.1)* | **Alias vs entity identifier (validation check 12e).** An alias **may** equal **its own** entity identifier; it **must never** collide with **another** entity's identifier — see §3.5. |

### 3.1 ER-1-C1 — mandatory write verification

An HA HTTP 2xx with an empty response body **must not** be interpreted as "the entity was
already in the requested state" — the empty list is ambiguous. **A tool must never claim
success unless the resulting HA state has actually been verified.** If the requested state
cannot be verified, the tool returns an honest `applied_unverified` — never a claimed success.

**Mechanism: after-only** (ratified). The tool issues the service call exactly as today, then
reads back `/api/states/<entity_id>` and compares against the D-ER-10 expected state.

- ER-1 **must not change when a POST is issued.** It changes only what the tool is willing to
  claim afterwards.
- A pre-read that would suppress the POST for a non-existent entity was **considered and
  rejected**: it introduces a new condition under which a write is not issued, which belongs
  to the deferred architectural decision in D-ER-9.
- Because there is no before-state, the tool **never reports `state_changed`** — so C1's
  empty-list ambiguity is never entered. `ha_response` is still returned verbatim, but it is
  **no longer interpreted**.

### 3.2 Why D-ER-7 is binding

`_evaluator/engine.py` pins `SUPPORTED_ARTIFACT_VERSIONS = (1,)` and raises `ArtifactError`
on anything else — and `bin/aurora-context` **catches** that and fails soft to
`Home State: Unavailable`. Bumping `artifact_version` without updating the evaluator would
therefore **not** fail loudly: it would silently degrade home awareness every night and
quietly undo the WM-6 / G-F5-04 closure. Keeping the key additive holds ER-1 entirely outside
the awareness path and makes G-ER-5 trivially provable.

### 3.3 D-ER-2 — input shape, not operation type

The decisive question is **what the caller passed**, never **what the caller asked to do**:

| Input | Behaviour | Reads | Writes |
|---|---|---|---|
| **Natural language that does not resolve** (not id-shaped; no matching alias) | **Fails closed** — `unknown_entity` + bounded candidate list, **no HTTP call** | same | same |
| **Natural language that resolves** (known alias) | Substituted for its real id; proceeds as if the caller had passed that id | same | same |
| **A syntactically valid `entity_id`** | **Continues directly to Home Assistant exactly as today** — whether or not the World Model knows it (**D-ER-9**). The registry is **never** consulted to gate it | same | same |

**There is no read/write asymmetry in the resolution policy.** A natural-language miss fails
closed on **both** paths for a mechanical reason: there is no valid id to send, so nothing
*can* pass through (today such input is already rejected as `bad_entity_id` before reaching
HA). A valid id passes through on **both** paths because D-ER-9 forbids any new gate.

**ER-1 changes only the reporting layer.** For a valid-but-non-existent id, the two paths
differ solely because **Home Assistant behaves differently**, not because ER-1 treats them
differently:

- **Reads were already honest** — HA answers 404 → `not_found`. No change.
- **Writes were not** — HA answers 200 + an empty list, which v0.1.0 claimed as success.
  **ER-1-C1** makes the claim honest (`applied_unverified`). The request itself is unchanged.

**Supersedes** the read/write asymmetry described in the 2026-07-14 defect record §3.C. That
phrasing belonged to the **rejected** closed-lookup design, in which an unmodelled id was a
"miss" and writes to it failed closed. Under **D-ER-9** an unmodelled id is **not a miss** —
it is a valid id and it passes through. The defect record is a **historical document and is
not rewritten** (`PROJECT_RULES.md` → Historical Documentation); this section is the
correction.

### 3.4 D-ER-9 and ER-1-C1 govern different axes

This reconciliation is the interpretive core of ER-1 and must not be blurred:

- **D-ER-9 governs routing and authorization** — no new gate, ever. Nothing changes about
  *when* a service call is issued or *what* Aurora is permitted to actuate.
- **ER-1-C1 governs reporting** — never assert what was not verified.

A consequence, stated plainly: **ER-1 does not prevent a pointless HA call for an invented
id; it prevents the false success claim.** The write still reaches HA, HA still does nothing,
and C1 reports honestly. Rate-limit budget is still consumed. This is the accepted trade for
preserving an unrestricted write surface.

### 3.5 D-ER-11 and D-ER-12 (Revision 2 — ratified 2026-07-16 at ER-1.1)

Both are **architectural decisions, not implementation details**: the first fixes the shape of
the authoritative naming surface, the second fixes what the resolver's closed lookup may
legally contain. Neither existed at Revision 1 — authoring the real alias sets surfaced them.

#### D-ER-11 — aliases mirror the `binding` shape

**`aliases` takes the same single/multi duality `binding` already has (§2.1 of the schema):**

- a **single-signal** entity uses a **flat alias list**, resolving to its reserved `state`
  signal;
- a **multi-signal** entity uses a **per-signal alias map**, one entry per named signal;
- **no implicit primary signal is introduced.**

**Why it was forced.** Two of the six bound entities — `entrance-plant`
(`water_warning` + `soil_moisture`) and `zigbee-mesh` (`connection` + `permit_join`) — are
multi-signal, and the schema is explicit that such a binding has **no implicit `state`**: every
field is named. An entity-level alias on them would therefore have **no single `ha_entity` to
resolve to**. The alternatives were both worse: inventing a "primary signal" would be arbitrary
and would smuggle a guess into a resolver whose entire purpose is determinism, while deferring
the two entities would silently shrink the ratified scope. **D-ER-1 specified the field but not
its multi-signal shape; D-ER-11 closes that gap by reusing an existing contract pattern rather
than adding a concept.**

**Consequence:** a name that maps to more than one signal of the same entity (a bare
*"planta"* — soil moisture, or watering warning?) is **deliberately not aliased**. A closed
deterministic resolver must never guess; such a question is answered from the awareness block,
not a tool call (§3.3).

#### D-ER-12 — alias vs entity identifier (validation check 12e)

**An alias may equal its own entity's identifier; it must never collide with another entity's
identifier.**

**Why it was forced.** The design draft presented at ratification proposed barring an alias
from colliding with **any** entity identifier. Authoring the real sets disproved it: **4 of the
6 bound entities have an alias equal to their own normalized id** — `awning`, `main door`,
`zigbee mesh`, `internet uplink`. Those *are* the natural English names of those entities.
Barring them would have gutted English coverage for **no safety gain**, because an alias equal
to its **own** entity's identifier is a harmless redundancy: both denote the same thing, so no
ambiguity exists. A collision with a **different** entity's identifier is the genuine hazard —
a name denoting another modelled entity is almost certainly an authoring error — and that is
what 12e now rejects.

*(Recorded for accuracy: the over-restrictive wording was in the **design draft discussed at
ratification**, never in this document. Revision 1 stated no check-12 semantics at all — the
full ruleset was authored at ER-1.1.)*

**Enforcement.** The full alias ruleset these decisions govern — shape, bounds, id-shape,
global uniqueness, entity-identifier collision and archetype exclusion — is **authored into the
entity schema contract at ER-1.1**
([`world_model/_schema/entity.schema.md`](world_model/_schema/entity.schema.md)), which is the
single source for the checks; the loader implements them **fail-loud** at **ER-1.2**. *(A
precise section reference is deliberately omitted here: that contract text does not exist yet
at this revision, and a freeze must not cite what is not present. It may be added once ER-1.1
lands.)*

One rule is stated here because it follows from **D-ER-8** rather than from the contract: the
**id-shape** check is applied to the **raw authored** string. D-ER-8 collapses `.` into a
space, so a *normalized* alias can never be id-shaped — testing the normalized form would be
vacuous.

**Authority is untouched.** Both decisions concern **naming and validation only**. Aliases
neither widen nor narrow what Aurora may actuate: D-12 remains the sole authorization
authority (**INV-17**), and the resolver is never consulted to permit or deny (**D-ER-9**).

---

## 4. Resolution order at the tool boundary

Resolution slots **exactly where the existing `entity_id` check sits**, so every preceding
check is untouched and `bad_service` still fires first.

| # | Step | Change |
|---|---|---|
| 1 | **D-12 domain allowlist** | **first — unchanged** |
| 2 | Service validation | unchanged (`bad_service`) |
| 3 | Bounded/type check (3–128) | unchanged (`bad_entity_id`) |
| 4 | **Id-shaped?** (`^[a-z_]+\.[a-z0-9_]+$`) | **pass through exactly as today.** Registry consulted for **observability only** (audit records `modelled: true\|false`) — never to gate |
| 5 | Else → normalize (D-ER-8) → **closed** alias lookup | hit → substitute the resolved id and continue as if the caller had passed it |
| 6 | Miss | **`unknown_entity`** + bounded candidate list (≤ 8; names + ids; AD-18-safe); **zero HTTP calls** |
| 7 | POST | unchanged |
| 8 | **ER-1-C1** | read back `/api/states/<id>` → `ok` + `verified`/`state_after`, or `applied_unverified` |

Normalization touches **only** the alias path; id-shaped input never enters it. No fuzzy
matching, no scoring, no LLM in the loop.

**`ha_get_state` runs the identical ladder minus step 8** — steps 4–6 behave exactly as
above (D-ER-2 / §3.3): a valid id continues to HA as today; a natural-language miss returns
`unknown_entity` with no HTTP call. Reads need no C1 because HA already answers 404 →
`not_found` for a non-existent id; only the **write** path needed a verification layer.

### 4.1 Result-code taxonomy

| Code | Meaning | Status |
|---|---|---|
| `ok` + `verified: true` | write issued **and** resulting state verified per D-ER-10 | `ok` pre-existing; `verified` additive |
| `applied_unverified` | HA accepted the call; the result could **not** be verified | **new** — explicitly not a success claim |
| `unknown_entity` | resolver miss on a non-id-shaped name; **no HA contact** | **new** |
| `resolver_unavailable` | projection missing/unreadable; alias resolution impossible | **new** (distinguishes a broken resolver from an unknown name) |
| `entity_not_found` | HA reported the entity does not exist | **pre-existing, preserved** |
| `refused` · `bad_service` · `bad_service_data` · `bad_entity_id` · `rate_limited` · `ha_unreachable` · `unauthorized` · `ha_error` | unchanged | **pre-existing, preserved** |

---

## 5. Sub-phases

| Phase | Content | Gates |
|---|---|---|
| **ER-1.0** | Freeze: ratify D-ER-1…10 + C1; spec; ROADMAP slot; triad; freeze log. *(The defect record lands in its own documentation commit immediately before, so history reads: defect discovered → design frozen.)* | — |
| **ER-1.1** | Schema `aliases` + entity aliases (docs only, additive) | G-ER-1 |
| **ER-1.2** | Loader: normalizer, validation, `resolution` registry, tests | G-ER-1, G-ER-2 (loader half), G-ER-5 |
| **ER-1.3** | Projection emitter + runtime artifact | G-ER-6 |
| **ER-1.4a** | **Capture the v0.1.0 baseline**, then `ha_get_state` v0.2.0 | G-ER-7 (read half) |
| **ER-1.4b** | `ha_call_service` v0.2.0 (resolution + C1) | G-ER-2/3/4, G-ER-7 (write half) |
| **ER-1.5** | Reconciliation + closeout | — |

Reads are cut over before writes deliberately: the resolver proves itself on the path that
cannot mutate anything before it is placed in front of the path that can.

---

## 6. Validation gates

All gates close on **real evidence** — no synthetic fixtures, no fabricated failures.

| Gate | Condition |
|---|---|
| **G-ER-1** | Loader alias validation against the schema contract's alias ruleset (check 12, authored at ER-1.1): the real tree compiles, and an injected **duplicate normalized alias**, **archetype-level alias**, **id-shaped alias**, and **collision with a *different* entity's identifier** (12e — D-ER-12) are each rejected **fail-loud**. *(An alias equal to its **own** entity's identifier is legal and must **not** be rejected — D-ER-12.)* |
| **G-ER-2** | Resolution **determinism** across the canonical es + en phrase set; byte-stable registry across runs |
| **G-ER-3a** | A non-id-shaped miss → `unknown_entity` + candidates, **zero HTTP calls**, audit line |
| **G-ER-3b** | **Historical unverified writes must never again be reported as successful.** Every historical case (§1 — 13 calls across 7 non-existent ids) must now produce an honest **`verified` or `applied_unverified`** result instead of an unverified success claim. The service call is still issued exactly as today (D-ER-9); the acceptance is the **claim**, not the request |
| **G-ER-4** | Happy path via **exact id** and via **alias** → `ok` + `verified`; baseline `off` restored; refusal and rate-limit paths unchanged |
| **G-ER-5** | **No WM/awareness regression**: loader (19) + evaluator (36) suites green; `aurora-context.json` byte-identical modulo timestamps; `artifact_version` still 1 |
| **G-ER-6** | **Projection failure rehearsal**: projection missing / stale / corrupt ⇒ **direct `entity_id` reads and writes continue to work exactly as today** (primary assertion); alias resolution returns an honest `resolver_unavailable`; platform sections unaffected; no partial action |
| **G-ER-7** | **Backward compatibility** — corpus below |

### 6.1 G-ER-7 corpus (enumerated from real audit evidence)

**Must be byte-identical on pre-existing keys and on the HA-facing request:**

- `ha_get_state`: `switch.impresora_3d` (11 historical `ok`), `sun.sun`, `cover.toldo`,
  `binary_sensor.sensor_puerta_principal_contact` — all confirmed to exist (2026-07-16).
- `ha_call_service`: `switch.turn_on` / `switch.turn_off` on `switch.impresora_3d`
  (7 historical `ok`) → `ok`, plus additive `verified`.
- Refusal path (safety): `recorder.purge`, `backup.snap`, `printer.turn_on` → `refused`.
- Validation path: `light.TURN_ON` → `bad_service`; `light.turn_on` with `entity_id` inside
  `service_data` → `bad_service_data`; `x` → `bad_entity_id` (length).
- Rate-limit path: unchanged.

**Intentional, enumerated changes** — none of these "work today", so none is a regression:

| Input class | Today | After ER-1 |
|---|---|---|
| Non-id-shaped (`coverawning`, `light.`, `not_a_valid_id_no_dot`, `LIGHT.KITCHEN`, `3dprinter.status`) | `bad_entity_id` | `unknown_entity` + candidates — same safety (refused, no HA contact), better message |
| Id-shaped, non-existent, live domain | `ok` (**unverified success claim**) | `applied_unverified` — **the defect fix** |
| Successful write | `ok` | `ok` + additive `verified` / `state_after` |

### 6.2 Execution constraints

1. **The v0.1.0 baseline must be captured before the cutover** (ER-1.4a step 0). Equivalence
   cannot be demonstrated against a version that has already been replaced.
2. **G-ER-4 / G-ER-7 must run outside `00:00–06:00 Europe/Madrid`.** They actuate
   `switch.impresora_3d`; inside the `overnight` window a powered printer trips a real
   `printer_on_overnight` token (`_schema/windows.md`), which would pollute F-4's accruing
   digest evidence and confound G-ER-5. Baseline `off` is restored per the G-5 pattern.

---

## 7. Rollback

Revert **tools first**, then loader/docs.

| Layer | Rollback |
|---|---|
| Tools | Single `webui.db` rows — reinstall the committed v0.1.0 source + restart (**D-WM5-5** pattern). **Honest note: this restores the defect** — v0.1.0 is the known-bad baseline |
| Projection | Delete; fully regenerable |
| Loader | `git revert` + re-run. `artifact_version` never moved, so the evaluator is unaffected either way |
| `aliases` | Additive frontmatter — `git revert` + re-run the loader |

No database migration, no container change, no cron change, no awareness path touched.

---

## 8. Invariants that remain unchanged

| Invariant | How ER-1 holds it |
|---|---|
| **INV-17** | D-12 stays **first and sole**. The ERL carries **zero authorization semantics** — it neither narrows nor grants. **Guard: never read `writable`, and never read the registry, to allow or deny anything.** `cover.toldo` stays actuatable exactly as today |
| **INV-18 / AD-20** | `aurora-context.json` and `home.anomalies` untouched; `generate-digest` (F-4) and the F-3a Filter contracts unchanged |
| **INV-19** | The ERL constructs **resolution**, not awareness, and reads the World Model — not raw signals. C1's read-back is **actuation verification**: it never feeds `home.anomalies` or the context. (`ha_get_state` has read raw HA state since Phase C without being an awareness consumer.) |
| **INV-WM3-A** | Backend-agnostic rule AST untouched |
| **AD-18** | Projection and candidate lists are **names/ids only** — no secrets |
| **AD-21** | Frozen architecture **unamended**; ER-1 implements the §7 intent |
| **D-12** | Closed domain set unchanged |
| **`schema_version`** | Stays **1** (additive optional field — §5 / schema §6) |
| **`ARTIFACT_VERSION`** | Stays **1** (D-ER-7) |
| Voice path · Guardian Cloud | Untouched |

---

## 9. Residual risks

- **Projection staleness** — the loader is run by hand, so a stale projection degrades **alias
  resolution only** (direct ids are unaffected by D-ER-9). Mitigation: stamp the projection
  with `docs_commit` + content hash; surface staleness at the tool boundary; G-ER-6 rehearses
  it. Scheduling the regeneration is available but deferred (an operator decision — it would
  require the fail-loud loader to run nightly).
- **Latency** — C1 adds one HTTP GET per write (worst case 10 s vs 5 s at the 5 s timeout).
  A shorter verification timeout is an implementation option.
- **Tool row scope** — only `qwen2.5` carries the `ha_*` tools (verified in `meta.toolIds`),
  so the D-20 legacy `llama3*` scoping is unaffected.

---

## 10. File inventory

**Schema (1)** — `world_model/_schema/entity.schema.md`.

**Entities (6, additive)** — `home/printer-3d.md`, `home/awning.md`, `home/main-door.md`,
`home/entrance-plant.md`, `home/zigbee-mesh.md`, `home/internet-uplink.md`;
optional `environment/daylight-time.md`. **Not touched:** `home/battery.md`,
`home/firmware.md` (aspects, no `binding`).

**Loader (6 + 1 new)** — `_loader/resolution.py` (**new**), `parse.py`, `normalize.py`,
`resolve.py`, `validate.py`, `emit.py`, `__init__.py`.

**Loader tests (1 new + 2 extended)** — `tests/test_resolution.py` (**new**),
`test_validate.py`, `test_emit_determinism.py`.

**Tools (2 + 1 new + 1 harness)** — `tools/ha_call_service.py` → **v0.2.0**,
`tools/ha_get_state.py` → **v0.2.0**, `lib/entity_resolver.py` (**new**),
`bin/install_tool` (generalise the single inline marker).

**Projection (1 new)** — `ai-stack/ingest/bin/emit-entity-projection`;
`etc/cron.d/aurora-signals` only if scheduled (operator-gated — root-owned).

**Runtime artifacts** — `ai-stack/aurora/aurora-entities.json` (**new**, gitignored),
`world_model.generated.json` (additive `resolution`), `webui.db` tool rows, audit log fields.

**Explicitly NOT changed** — `world_model_architecture.md` · `_evaluator/**` ·
`bin/aurora-context` · `filters/aurora_context.py` · `webui.db params.system` · `.gitignore`
(both targets already ignored) · HA voice path/config · compose/containers · Guardian Cloud.

---

## 11. References

- Defect record: [`../09_logs/2026-07-14_ER1_entity_resolution_finding.md`](../09_logs/2026-07-14_ER1_entity_resolution_finding.md)
- Freeze log: [`../09_logs/2026-07-16_ER1_freeze.md`](../09_logs/2026-07-16_ER1_freeze.md)
- Frozen architecture (AD-21): [`world_model_architecture.md`](world_model_architecture.md) §7, §2.5
- Schema contract: [`world_model/_schema/entity.schema.md`](world_model/_schema/entity.schema.md)
- Roadmap slot: [`../00_overview/ROADMAP.md`](../00_overview/ROADMAP.md) → Phase ER-1
