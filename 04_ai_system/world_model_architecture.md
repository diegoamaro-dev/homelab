# Aurora World Model — Architecture Freeze Proposal

- **Status:** **FROZEN — architectural baseline. Ratified by the operator 2026-07-01; AD-21
  assigned (§14).** This is the accepted World Model architecture for Aurora. Revisions
  R1→R2 resolved all blocking findings (§11); deferred items are Known Architectural Debt
  (§12). **The freeze package — this document, AD-21, the triad reconciliation, the freeze
  log, and the Phase WM roadmap — is prepared; the git tag is PENDING at the git gate**
  (not committed, not pushed, not tagged; operator git-approval rule).
- **Revision history:** R1 (2026-07-01) initial freeze proposal · R2 (2026-07-01) closed
  W-1/W-2/W-3 + W-4/W-5, added Known Architectural Debt · **R3 (2026-07-01) FROZEN — AD-21
  assigned; freeze package prepared; git tag pending.**
- **Authoring model:** architect / technical authority = an AI reasoning assistant; executor, validator,
  reviewer, documenter = an AI coding assistant. This document records an accepted architecture for
  freeze. It introduces **no** runtime, tool, prompt, collection, container, DB, or git
  change.
- **Purpose:** define Aurora's **World Model** — the single semantic representation of
  its operational world — as the long-term foundation that remediates **R-F5-A**
  (§7) and underpins Phase G+ proactive intelligence.
- **Sources of record:** [`AURORA_VISION.md`](AURORA_VISION.md) (north star) ·
  [`phase_f_architecture.md`](phase_f_architecture.md) (F-5, R-F5-A, AD-01/03/04/11/18/20) ·
  [`home_model.md`](home_model.md) (the prototype region) ·
  [`home_state_design.md`](home_state_design.md).
- **Governing rule:** *Reality always wins* — over the awareness, over the model, and
  over the version of the machinery that reads it.

---

## 1. The accepted architecture

### 1.1 What changes

Aurora today reads scattered signals interpreted per-consumer. The World Model makes a
single **semantic representation of Aurora's operational world** the center of gravity:
every reading is interpreted against it, every surface renders from it, every memory and
document anchors to its entities. This is not a new data store — it is the interpretive
layer over existing signals and corpora, expressed as *what things mean*, not *how they
are wired* (the `home_model.md` principle, generalized: **Aurora reasons about the world,
not about its implementation**).

### 1.2 The four ways Aurora knows (accepted definitions)

| Layer | Definition | Volatility |
|---|---|---|
| **World Model** | the single semantic representation: entities · baselines · relationships · priorities · boundaries. Holds meaning, **not** live values. | slow (structure) |
| **Awareness** | **the World Model evaluated at the present moment** — entity states + deviations + aggregate verdict. | fast (state) |
| **Memory** | **the evolution of entities through time** — the historical record, entity-indexed. | historical |
| **Knowledge** | **documentation describing entities independent of current state** — timeless facts. | static |

Sharpest form: **Awareness = the World Model evaluated at `now`.** Memory is its past
values; Knowledge is its documentation. The World Model is the axis that finally separates
memory ≠ knowledge ≠ model (Vision §8): they are different projections of the same
entities.

### 1.3 The cognitive pipeline

```
   ①CREATE ─doc─▶ ②VALIDATE ─valid─▶ ③COMPILE ─▶ ╔══════════════╗
   Operator        Loader/CI          Loader      ║ WORLD  MODEL ║ (static)
                     ▲ STOP                        ╚══════╦═══════╝
                     │ (invalid rejected,                 ║ binds signals
                     │  fail-loud)                        ▼
   REALITY ─observe▶ Collectors ─signals─────▶ ④AWARENESS  (model @ now)
     ▲                                          Evaluation engine · DET
     ║                                                 │
 ════╬═════════ DET  ┃  PROB ═══════════════════ B3 ══ │ ════ safety seam
     ║                                                 ▼
     ║                        ┌──pull──▶ ⑤REASONING (7B) · PROB
     ║                        │                │           │
     ║                 ⑦RETRIEVAL◀──┐          │           │ intent
     ║                 (RAG · PROB) │          │           ▼
     ║                     ▲        │          │      ⑧ACTION GATE
     ║                 ⑥MEMORY──────┘   allowlist·boundary·audit · DET/fail-closed
     ║                 entity timeline           │  STOP if out-of-scope
     ║                 (DET gen · nightly)        │
     ╚═══════════ write (only here) ─────────────┘
                                          ⑨RETIRE  Operator + Loader (recompile);
                                                   memory persists (history endures)
```

Reality → Collectors → **World Model** → Awareness → Reasoning → (Action → Reality), with
Memory spiralling off Awareness and feeding back through Retrieval. Validation gates entry
to the model (②) and to reality (⑧). Determinism holds the spine; probability lives only
below the B3 seam and is fail-closed at the single write path.

### 1.4 The substrate — hybrid single-source literate model

The World Model lives in the **documentation layer** as a **literate single-source model**:
canonical Markdown carries embedded machine-readable structure; a deterministic loader
compiles it; consumers read the compiled evaluation. One canonical source, many
projections. Full authoring spec: §4.

### 1.5 Aggregate verdict model (added R2 — closes W-4)

"Is everything OK?" is answered by a **global verdict over per-region verdicts**, not a flat
worst-of over every entity:

- **Per-region verdict** = the most severe *active* deviation among that region's entities.
- **Global verdict** escalates to "attention needed" **only on a deviation of severity
  ≥ medium**; low-severity items (e.g. a low battery) are **listed** in the awareness block
  but do **not** flip the global verdict.

This preserves "silence is informative" (Vision §3) at scale: a chronic low-priority item
never makes the global answer perpetually negative. Severity tiers and ordering are unchanged
(`home_state_design §4`); this defines only how they roll up.

---

## 2. Invariants (frozen)

### 2.1 Accepted freeze candidates (verbatim, authoritative)

1. World Model as Aurora's single semantic representation.
2. Awareness as the World Model evaluated at the present moment.
3. Memory as entity evolution through time.
4. Knowledge as documentation about entities, independent of current state.
5. Hybrid single-source literate model.
6. Markdown as canonical source.
7. Structured machine-readable fields embedded in the canonical docs.
8. Generated artifacts derived, gitignored and fully regenerable.
9. Per-entity `schema_version`.
10. Additive-first schema evolution.
11. Token/id permanence.
12. Bounded loader compatibility.
13. Fail-loud validation.
14. Determinism up to Awareness and at the Action gate.
15. Probabilistic reasoning only after the B3 seam.
16. Operator-gated actions only.

### 2.2 Invariant families

| Family | Invariants | Meaning |
|---|---|---|
| **Semantic** | 1–4 | one model; awareness = model@now; memory = entities-in-time; knowledge = timeless entity docs |
| **Substrate** | 5–8, 13 | literate single-source; Markdown canonical; embedded structure; derived/gitignored artifacts; fail-loud |
| **Evolution** | 9–12 | per-entity `schema_version`; additive-first; token/id permanence; bounded loader window |
| **Determinism & safety** | 14–16 | deterministic to Awareness + at the action gate; probability only past B3; actions operator-gated |

### 2.3 The B3 seam and the safety property

Everything up to and including **Awareness** (plus Memory *generation* and the **Action
authorization gate**) is deterministic. **Reasoning and Retrieval** are the only
probabilistic layers, and the one probabilistic act that touches reality — invoking an
action — is wrapped in a **deterministic, fail-closed** gate (allowlist + boundary +
audit). This is why Aurora can hold genuine action capability without anxiety (Vision §8):
a wrong *guess* can produce a wrong *sentence*, never an unauthorized *act*.

### 2.4 Breaking an invariant = redesign

An invariant may only be revised by an explicit, gated architecture decision, never by
drift. The following would break an invariant and force a redesign — and each is already
forbidden by the Vision, which is why the architecture is durable (§5, §8): multi-operator,
autonomy, secrets-in-model, breaking the action gate, or **pushing any probabilistic
component upstream of Awareness** (e.g., a RAG-resident model or LLM-authored baselines).

### 2.5 Invariants added in Revision 2 (close W-1, W-2, W-5)

These **refine — never relax** — the accepted set. The 16 candidates in §2.1 are unchanged.

- **INV-17 (closes W-1 — action authorization is single-sourced).** The `ha_call_service`
  allowlist (D-12, enforced at the tool boundary) is the **sole** authority for what Aurora
  may actuate. World Model `writable` / `boundary` are **descriptive only**, validated to be
  a **subset of** the enforced authorization, and **never a grant**. Refines invariant #16
  and upholds Vision §7 ("Aurora does not self-modify its allowlist"; "the security model is
  a feature").
- **INV-18 (closes W-2 — the awareness output preserves the F-4/F-3a contract).** The World
  Model awareness output **preserves the `aurora-context.json` schema (AD-20)**:
  `home.anomalies` remains a list of typed tokens; the `generate-digest` (F-4) and F-3a
  Filter contracts are **unchanged**. AD-20 is **held, not superseded**.
- **INV-19 (closes W-5 — single awareness source).** **No consumer** — surface projection or
  world-aware tool — may read raw signals to construct awareness; every consumer renders from
  the World Model evaluation. Introducing a consumer that bypasses the model is the RA-03
  anti-pattern and requires a gated architecture change. This makes R-F5-A **structurally**
  solved (§7), not conditionally.

---

## 3. Entity lifecycle

| # | Stage | Transition | Owner | Nature | Validation | On failure |
|---|---|---|---|---|---|---|
| 1 | Creation | ∅ → declared | **Operator** | det (human) | none (draft) | n/a |
| 2 | Validation | declared → valid | **Loader / CI** | det | **hard gate** (schema·tokens·refs·secrets·boundary·coverage·prose) | **STOP — reject; build refuses** |
| 3 | Compile/Load | valid → compiled | **Loader** | det, idempotent | passed; emits artifact | **STOP-safe — retain last-good** |
| 4 | Awareness eval | compiled → evaluated@now | **Evaluation engine** | det | soft runtime guard (present/fresh/tz) | **DEGRADE — unknown/unavailable; reality wins** |
| 5 | Reasoning | evaluated → answer | **Reasoning (7B)** | **prob** | consumes model, not raw signals | DEGRADE — best-effort, sourced |
| 6 | Memory evolution | evaluated@now → historised | **Memory writer** | det generation | records gaps honestly | DEGRADE — record gap, never fabricate |
| 7 | Retrieval | historised/documented → in reasoning | **Retrieval (RAG)** | **prob** | entity-anchored | DEGRADE — "not found" |
| 8 | Action | interpretation → effect | **Actions** (operator-gated) | gate det/fail-closed; trigger prob | **allowlist + boundary + scope** | **STOP — refuse out-of-scope** |
| 9 | Retirement | live → retired (history persists) | **Operator + Loader** | det | re-validate dependents | STOP — fail-loud on dangling dep |

**Boundaries:** B1 documentation↔operative model (②→③) · B2 static↔live (③→④) · **B3
deterministic↔probabilistic (④→⑤)** · B4 read↔write (only ⑧ writes) · B5 per-session↔
historical (④/⑤↔⑥).

**Failure rule:** **build-time and authorization failures STOP (fail-loud/closed); runtime
observation, retrieval, and reasoning failures DEGRADE (fail-soft/honest).** Three hard
stops: invalid entity (②), unauthorized action (⑧), dangling dependency at retirement (⑨).

**Retirement is visible, not silent:** a retired entity is excluded from evaluation but its
history persists in Memory, marked historical so it is never surfaced as current.

---

## 4. Authoring format

### 4.1 Canonical file structure

```
04_ai_system/world_model/
  README.md                         ← model index
  _schema/  entity.schema.md · tokens.md · windows.md · archetypes/…
  infrastructure/  ingest-pipeline.md · backup.md · compute-torre.md · …
  home/            printer-3d.md · awning.md · zigbee-mesh.md · battery.md · …
  projects/        homelab.md · guardian-cloud.md · …
  operator/        diego.md
  self/            aurora.md
  environment/     daylight-time.md
```

One directory per **region**, one file per **entity**, `filename == <id>.md`.
Namespaces: entity ids & filenames `kebab-case`; anomaly tokens `snake_case`; field names
`snake_case`.

### 4.2 The literate contract

**Frontmatter (YAML) is the single authoritative machine surface; the prose body is
explanatory and carries no authoritative data.** One parser, one truth. Prose may narrate a
baseline but the loader reads it only from the field; a prose/field contradiction is a
validation error.

### 4.3 Fields

| Field | Req | Type / values | Purpose |
|---|---|---|---|
| `id` | ✅ | kebab slug, unique, == filename | model key |
| `name` | ✅ | string | display |
| `region` | ✅ | infrastructure·home·projects·operator·self·environment | placement |
| `kind` | ✅ | device·service·pipeline·project·person·self·environment·aggregate·aspect | class |
| `status` | ✅ | active·draft·retired | lifecycle visibility |
| `schema_version` | ✅ | integer | contract era (§5) |
| `priority` | cond | critical·high·medium·low | severity ordering |
| `baseline` | cond | `{state}`\|`{schedule}`\|`{conditions[]}` | exact "normal" |
| `binding` | cond | `{ha_entity\|container\|corpus\|probe\|signal}` | implementation link (real ids live here) |
| `collector` | cond | signal-source id | which Collector supplies live state |
| `anomaly_rules` | cond | `[{token, condition, window?}]` | deterministic deviation (closed grammar) |
| `writable` | opt (false) | bool | Action scope — **descriptive only; validated ⊆ the `ha_call_service` allowlist; never a grant (INV-17)** |
| `boundary` | cond | read_only·collaboration_context_only | Guardian / operator walls — **descriptive; mirrors the enforced boundary, never replaces it (INV-17)** |
| `archetype` | opt | archetype id | shallow shared defaults |
| `depends_on` | opt | `[id]` | directed dependency graph |
| `part_of` | opt | id | composition membership |
| `applies_to` | cond | selector | aspect targets |
| `status_semantics` | opt | rules (e.g. `unavailable: down`) | verdict derivation |

**Prose (required):** `## Purpose`, `## Reasoning`, `## Suggested operator actions`
(last optional for pure-reference/boundary entities).

### 4.4 Relationships & composition

- **`depends_on`** (directed causal edge); **`part_of`** (composition into an aggregate);
  reverse edges (`affects`/dependents) are **derived by the loader, never authored**.
- **Composition over inheritance.** Aggregates compose members; **aspects** (battery,
  firmware) apply cross-cutting via `applies_to`; **archetypes** provide *optional, shallow
  (one-level)* shared defaults. **Deep inheritance is rejected** (simplicity + determinism).

### 4.5 Condition grammar (closed; duration predicate added R2 — closes W-3)

```
condition := disj ; disj := conj ('OR' conj)* ; conj := neg ('AND' neg)*
neg := 'NOT'? predicate | '(' condition ')'
predicate := field COMP value
           | 'time' 'in' <window>
           | field 'unavailable'
           | field 'for' DURATION          # e.g. "state == open for > 15m" — closes W-3
COMP := == != < > <= >=
DURATION := COMP <n><unit>   (unit ∈ s | m | h)
```

No functions, no arithmetic, no free variables. Severity is looked up from `tokens.md` (not
authored per rule); windows are named and tz-anchored.

**Duration is stateless (B3 preserved).** `field 'for' DURATION` is evaluated as
`now − last_changed(field) COMP DURATION`, using the `last_changed` timestamp carried in the
**current** signal — so awareness stays a pure function of the current signal and the
determinism seam (B3) is intact. This expresses the existing `door_open_extended`
("main door open >15 min") rule. **Collector contract:** any collector bound to an entity
with a duration rule must expose `last_changed`.

### 4.6 Example entity

```markdown
---
id: printer-3d
name: 3D printer
region: home
kind: device
status: active
schema_version: 1
priority: medium
writable: true
archetype: zigbee-device
baseline: { state: off }
binding: { ha_entity: switch.impresora_3d }
collector: ha-states
anomaly_rules:
  - { token: printer_on_overnight, condition: "state == on AND time in overnight" }
depends_on: [ zigbee-mesh ]
---
## Purpose
The 3D printer plug — the one home object Aurora may actuate.
## Reasoning
On overnight usually means a job was left running or forgotten — surface at briefing, don't act unprompted.
## Suggested operator actions
Mention it when briefing; offer to switch it off only on an explicit request.
```

### 4.7 Validation schema (fail-loud)

Structural (fields/enums/types) · Grammar (conditions parse; windows tz-anchored) · Token
(token ∈ registry; severity resolved there) · Referential (`id` unique; refs exist; no
dependency/archetype cycles; `part_of`→aggregate) · Safety (AD-18 — no ip/token/secret/raw
payload) · Boundary (`guardian-cloud` read_only ⇒ not writable, no anomaly rules; operator
carries no presence/occupancy) · Coverage (every token produced ≥1×; every collector exists)
· Prose (required sections; no prose/field contradiction) · Lifecycle (retired excluded from
eval, retained for retrieval; nothing active depends on a retired entity) · Version
(declared `schema_version` consistent with the fields used) · **Authorization (R2, INV-17 —
closes W-1)** (`writable: true` ⇒ the entity's action surface is a subset of the
`ha_call_service` allowlist; `writable` / `boundary` never grant beyond the enforced
authorization) · **Duration/collector (R2 — closes W-3)** (any entity with a `field 'for'
DURATION` rule must bind a `collector` that exposes `last_changed`).

### 4.8 Generated artifacts & loader

- **`world_model.generated.json`** — the fully resolved model (archetype defaults merged,
  aspects expanded, reverse edges derived, rules compiled, severity resolved). `DO NOT EDIT`
  header; **gitignored, fully regenerable, never canonical.**
- **Loader/compiler** — deterministic, idempotent: **Parse → Resolve → Validate → Emit →
  Serve**. Fail-loud (retain last-good on failure). **Read-only w.r.t. canonical docs** (it
  never rewrites a doc). Does not evaluate, read live state, or interpret meaning.

---

## 5. Versioning policy

**Axes kept separate:** git versions *content*; `schema_version` versions the *contract*;
the loader declares what contracts it reads; the artifact is a disposable provenance stamp.

- **`schema_version`** — integer, **per-entity**, bumped **only on breaking changes**;
  additive changes are backward-compatible by construction and do not bump it.
- **Additive-first evolution** — new optional fields, tokens, enums, archetypes, grammar
  predicates are additive (no bump). Rename/remove/require-without-default/grammar-semantics
  are breaking (MAJOR bump + migration).
- **Backwards compatibility** — the loader reads the current major **and ≥1 prior** (bounded
  window). Forward compatibility is **not** guaranteed: an unsupported/future version
  **fails loud** (never guesses).
- **Deprecation** — deprecate → grace period (accepted with warning) → remove at a MAJOR,
  announced in the schema changelog. **Never silent.**
- **Token/id permanence** — tokens and ids are **append-only, never reused or repurposed**,
  because Memory references them across years; a retired token stays `reserved`.
- **Rollback** — `git revert` docs + regenerate; rollback pins the pair {docs commit +
  loader version}; determinism reproduces the past exactly.
- **Readability forever** — because the canonical form is literate Markdown, an old entity
  is **always human- and LLM-readable regardless of `schema_version`**; only *machine
  compilation* has a bounded window. This is the documentation-first payoff: the model can
  never rot into unreadability.
- **Safety asymmetry** — safety/boundary rules (AD-18, `read_only`) may *tighten* freely; a
  *loosening* is a high-gate MAJOR, never silent.

---

## 6. Migration from `home_model.md`

Doc-first, parallel-run, **real-data parity before cutover** (no fabrication):

| Step | Action | Gate |
|---|---|---|
| **M1** | Author `_schema/` — `tokens.md` (the 10 tokens + severity, single-sourced from `home_model.md §7` + `home_state_design §4.4`), `windows.md` (`overnight` = 00:00–06:00 Europe/Madrid), `archetypes/zigbee-device.md` | schema reviewed |
| **M2** | Restructure `home_model.md`'s 9 objects → per-entity literate docs under `home/` (frontmatter + prose lifted 1:1; battery/firmware → aspects; **no new facts**) | semantic equivalence |
| **M3** | Stand up the loader; run **in parallel** with `HOME_RULES` | **parity on real data**: loader rules ≡ `HOME_RULES`; identical anomalies on the same `/api/states` |
| **M4** | Cut the evaluator over; **retire `HOME_RULES`**; `home_model.md` → regenerated overview / redirect so links survive | detector unaffected; **awareness output preserves the `aurora-context.json` typed-token schema — `generate-digest` (F-4) + F-3a Filter unchanged (AD-20 / INV-18)** |
| **M5** | Extend to other regions (infrastructure, self, projects) incrementally | per-region validation |

`HOME_RULES` remains the live path until **M4** — the running detector is never without a
model. Each step is git-revertable; the triad reconciles at the migration closeout.

---

## 7. Relation to R-F5-A

**R-F5-A (awareness-consumption gap, G-F5-04 FAIL, 2026-07-01)** was diagnosed as a
**single-channel awareness** defect: F5.2 delivered home state to exactly one of four
consumers (the chat Filter block) and kept the other three (`overall_status`,
`system_status`, the voice line) platform-only, so the one home-aware channel was the one
the model's routing bypassed. Evidence:
[`../09_logs/2026-07-01_phaseF_F5_3_applied.md`](../09_logs/2026-07-01_phaseF_F5_3_applied.md).

The World Model **subsumes and structurally closes** this:

- **One world, many projections** — home and platform are co-equal entities in one model;
  every consumer (chat Filter, `system_status`, voice line) becomes a dumb projection of the
  same unified Awareness evaluation. A consumer **cannot** be selectively home-blind — the
  R-F5-A failure class becomes structurally impossible.
- **Precedence contest dissolves** — reasoning consumes the model's evaluation as its default
  substrate; the `# Routing`/`# Context`/`# Home` three-way instruction contest disappears.
- **Aggregate verdict spans the world** — "is everything OK?" aggregates all entities;
  a home anomaly is co-equal with a platform one.
- **Entity registry ends id-hallucination** — real entity_ids live in `binding`; Aurora can
  answer "that isn't an entity I model" instead of inventing ids.

R-F5-A is remediated at **WM-4/WM-5** (§9); **G-F5-04 reopened and CLOSED at WM-6 (2026-07-16)** on a real
induced anomaly across chat and voice — PASS on real evidence; **R-F5-A CLOSED; F-5 CLOSED** (closeout [`../09_logs/2026-07-16_WM6_G-F5-04_closeout.md`](../09_logs/2026-07-16_WM6_G-F5-04_closeout.md)). The earlier point-fix proposal (home-aware
`system_status` + voice line + prompt reinforcement) is **subsumed**: those become the
natural consequence of consumers reading the unified world evaluation.

**Structural, not conditional (R2).** **INV-19** (single awareness source) forbids any
consumer from reading raw signals to build awareness, so the single-channel failure class
**cannot recur** — this is what makes R-F5-A *structurally* solved rather than patched. The
remediation **preserves the F-4/F-3a `aurora-context.json` contract** (**INV-18 / AD-20**):
no digest or Filter regression.

---

## 8. Out of scope (explicit)

Named so they are not accidentally built:

| Deferred / rejected | Disposition |
|---|---|
| Conversational continuity (session-to-session dialogue memory) | Phase G (Vision §5; AD-06) |
| Proactive intelligence (morning summaries, anomaly push, trend flags) | Phase G+; the World Model is its **precondition**, not this deliverable (Vision §9) |
| Autonomy / Aurora acting without an explicit in-scope request | permanently rejected (Vision §7) |
| Multi-operator | out of scope (single-operator system) |
| Secrets in the model | permanently rejected (AD-18) |
| RAG-resident World Model (option D) | rejected — non-deterministic; breaks B3 |
| Deep inheritance in the authoring format | rejected — composition + shallow archetypes only |
| A general expression grammar for conditions | rejected — closed grammar only |
| Runtime World Model self-modification by Aurora | rejected (Vision §7) |
| Guardian Cloud operational access | permanent read-only boundary |

---

## 9. Proposed implementation phases

Neutral labels (WM-n); **ROADMAP slotting / phase-letter assignment is the architect's call
at ratification.** Each phase: real-data validation, documentation ends it, **STOP at the git
gate** (operator approval before any commit/push/tag).

| Phase | Objective | Gate / validation |
|---|---|---|
| **WM-0** | Ratify this freeze (assign ADs, slot ROADMAP, reconcile triad, tag) | operator/architect ratification |
| **WM-1** | `_schema/` foundation: entity schema, tokens registry, windows, archetypes, validation ruleset | schema reviewed; no entities/runtime yet |
| **WM-2** | Migrate `home_model.md` → literate `home/` entities (docs only, 1:1) | semantic equivalence (M2) |
| **WM-3** | Loader/compiler: Parse→Resolve→Validate→Emit; run **parallel** to `HOME_RULES` | **real-data parity** (M3) |
| **WM-4** | Evaluation engine consumes the World Model; produce unified Awareness (platform + home co-equal); **retire `HOME_RULES`** | cutover; **awareness output preserves the `aurora-context.json` schema — no F-4/F-3a regression (AD-20 / INV-18)** |
| **WM-5** | Consumer convergence (R-F5-A): every consumer a dumb projection — Filter, home-aware `system_status`, voice line | all surfaces home-aware |
| **WM-6** | **Reopen & close G-F5-04** — real induced anomaly across chat + voice; reconcile triad; closeout | **DONE 2026-07-16 — G-F5-04 PASS on real evidence; R-F5-A / F-5 CLOSED** (`../09_logs/2026-07-16_WM6_G-F5-04_closeout.md`) |
| **WM-7+** | Extend regions (infrastructure, self, projects); foundation for Phase G proactive intelligence | per-region validation |

---

## 10. Documentation review gate (this document stops here)

Before this proposal becomes a frozen architecture, the operator/architect must, as separate
ratification steps (**not performed here**):

1. Review and accept this document at the documentation review gate.
2. Assign AD numbers to the §2 invariants in `phase_f_architecture.md` (or a successor
   architecture doc).
3. Slot the WM phases (§9) into [`../00_overview/ROADMAP.md`](../00_overview/ROADMAP.md) with
   ratified phase labels.
4. Reconcile the overview triad (CURRENT_STATE / ROADMAP / AMAROLAB_HANDOFF).
5. Freeze (tag) — under the standing operator git-approval rule.

---

## 11. Revision 2 — findings resolution

| Finding | Class | Resolution | Where |
|---|---|---|---|
| **W-1** | Blocking | Allowlist (D-12) is the **sole** action-authorization source; `writable`/`boundary` are descriptive, validated ⊆ enforced authorization, never a grant | **INV-17** (§2.5); §4.3; §4.7 |
| **W-2** | Blocking | Awareness output **preserves the `aurora-context.json` typed-token schema**; `generate-digest` + F-3a Filter unchanged (AD-20 held) | **INV-18** (§2.5); §6 M4; §9 WM-4; §7 |
| **W-3** | Blocking | Grammar gains a `field 'for' DURATION` predicate (evaluated from `last_changed` in the current signal — B3 preserved); collectors with duration rules expose `last_changed` | §4.5; §4.7 |
| **W-4** | Strong rec | Global verdict escalates only on ≥ medium severity; low-severity items are listed, not escalated — "silence is informative" preserved | §1.5 |
| **W-5** | Strong rec | Single-awareness-source invariant: no consumer builds awareness from raw signals — makes R-F5-A structural | **INV-19** (§2.5); §7 |

No accepted invariant (§2.1) was relaxed; INV-17…19 refine the set. No concept was added
beyond what these five findings required.

## 12. Known Architectural Debt (deferred — W-6…W-15)

Recorded, accepted, and deferred by operator decision; **none blocks the freeze.** Each is a
gated future item, not silent drift.

| ID | Debt | Deferral / close-when |
|---|---|---|
| **W-6** | Memory (entity evolution) & Knowledge (entity docs) have no migration path; reconciliation with night-based `ops_digests` (AD-04/14/15/17) unspecified | out of freeze scope; home region + Awareness are the operational scope; gated when the memory/knowledge regions are taken |
| **W-7** | `binding` can drift from reality (renamed HA entity → silent "unavailable"); build-time validation is model-internal only | add a periodic binding-reconciliation check when a 2nd producer/region lands |
| **W-8** | M3 parity anchors on `HOME_RULES` (a derived transcription) rather than `home_model.md` + real anomalies | tighten the parity oracle during WM-3 execution |
| **W-9** | Schema proven on device/aggregate/aspect/boundary shapes only; `operator`/`self`/`environment` unproven | validate ≥1 non-device entity per region before extending (WM-7) |
| **W-10** | Ambient projection has no size bound; multi-region degraded state can breach voice's ≤200-char / ≤2-turn budget | add the reserved "top-N + N more" volume control (`home_state_design §8`) when a 2nd anomaly-bearing region lands |
| **W-11** | D2 (platform-only `overall_status`) effectively superseded by §1.5 but not formally recorded as such | record at ratification |
| **W-12** | "Projection" loosely includes `system_status` (a tool) — a different consumer category than surface renderers | tighten taxonomy in a later revision |
| **W-13** | The loader enters the trusted computing base for AD-18 secret-safety + boundary enforcement; its own correctness/failure modes need explicit treatment | address in the loader's build phase (WM-3) |
| **W-14** | Versioning/deprecation/multi-region apparatus is heavy for current scale | adopt lazily (YAGNI): build multi-version tooling only when a 2nd `schema_version` exists |
| **W-15** | "Deterministic Awareness" is transform-deterministic, input-variable — a precision note, not a defect | note only |

## 13. Consistency pass & freeze certification

Revision 2 consistency check:

- **Blocking W-1 / W-2 / W-3 — closed** (INV-17; INV-18; §4.5 duration grammar).
- **Strong recs W-4 / W-5 — closed** (§1.5 aggregate model; INV-19).
- **Invariants** — the 16 accepted candidates (§2.1) are unchanged; INV-17…19 **refine, never
  relax** them. Determinism (B3) and the fail-closed action gate remain intact (W-3's duration
  predicate is stateless via `last_changed`; W-1 **tightens**, not loosens, the action
  boundary).
- **No redesign, no new concepts** beyond what W-1…W-5 required; deferred debt is **recorded**
  (§12), not silently resolved.
- **AD compatibility** — AD-20 explicitly **held** (INV-18); AD-01/03/04/11/14/17 unaffected;
  D2 supersession tracked (W-11).
- **No contradiction** introduced with `AURORA_VISION.md`.

**No blocking issues remain.**

### ✅ Ready for Architecture Freeze

The World Model architecture (**Revision 2**) is certified **Ready for Architecture Freeze.**
Ratification (AD assignment, ROADMAP slotting, triad reconciliation, freeze tag) remains the
operator/architect's step per §10 — this document stops at the documentation review gate.

---

## 14. Architecture Decision AD-21 & freeze record

### AD-21 — Adopt the World Model as Aurora's semantic baseline

**Decision (ratified 2026-07-01).** Aurora adopts the **World Model** — the single semantic
representation of its operational world — as its **architectural baseline**, as specified in
this document (FROZEN, Revision 2). Frozen with it: the accepted invariants §2.1 (16 freeze
candidates) + §2.5 (INV-17/18/19), the entity lifecycle (§3), the authoring format (§4), the
versioning policy (§5), and the migration path (§6). The deferred items (§12) are Known
Architectural Debt and do **not** block the baseline.

**Relation to R-F5-A.** AD-21 defines the *remedy architecture* for R-F5-A (the
awareness-consumption gap). The World Model makes the fix **structural, not a patch** (§7,
INV-19) and preserves the F-4/F-3a `aurora-context.json` contract (INV-18 / AD-20 held).
R-F5-A itself **closes at WM-6** on real induced-anomaly validation.

**Scope.** AD-21 changes no runtime, code, prompt, tool, collection, or container. It is an
architecture-baseline decision; implementation is **Phase WM** (§9), which has **not begun**
(WM-1 not started).

**Supersession.** Refines the Phase-F awareness model (AD-01…AD-20 unaffected); D2
(platform-only `overall_status`) is superseded by the §1.5 aggregate model (tracked as W-11).
AD-21 is recorded in the running AD register in
[`phase_f_architecture.md`](phase_f_architecture.md) §4.

### Freeze record

| Item | Value |
|---|---|
| Baseline | World Model architecture — this document (Revision 2, FROZEN) |
| Decision | **AD-21** (adopt the World Model baseline) |
| Ratified | 2026-07-01, operator |
| Freeze package | this doc · AD-21 · triad reconciliation (CURRENT_STATE / ROADMAP / AMAROLAB_HANDOFF) · freeze log `09_logs/2026-07-01_world_model_architecture_freeze.md` · Phase WM roadmap (§9 + ROADMAP.md) |
| Blocking findings | W-1 / W-2 / W-3 — closed (§11) |
| Known debt | W-6…W-15 (§12) |
| Implementation | Phase WM (WM-1→WM-7) — **not started** |
| Ratification steps (§10) | 1–4 executed in this package; **step 5 (git tag) PENDING at the git gate** |
| Git status | **not committed, not pushed, not tagged** |

**No implementation, no runtime/tool/prompt/code change has been made; no git operation
(commit/push/tag) has been performed. Reality always wins.**
