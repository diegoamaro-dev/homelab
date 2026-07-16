# ER-1 — freeze amendment: Revision 2 (D-ER-11, D-ER-12)

- **Date:** 2026-07-16   **Phase:** ER-1 (design amendment)   **Status:** **RATIFIED — at the git gate.**
- **Class:** design amendment + decision register + correction of record. **Documentation only —
  no schema, entity, loader, tool, projection, runtime or database change.**
- **Amends:** [`../04_ai_system/entity_resolution_layer.md`](../04_ai_system/entity_resolution_layer.md)
  → **Revision 2**.
- **Preserves:** the ER-1.0 freeze log
  [`2026-07-16_ER1_freeze.md`](2026-07-16_ER1_freeze.md) is **unchanged historical evidence** of
  what was ratified at Revision 1. It is not rewritten (`PROJECT_RULES.md` → Historical
  Documentation); this log is the later documentation that carries the correction.

## 1. Why an amendment exists

A frozen design is amended **only** by a gated, operator-ratified decision — never by silent
drift. Authoring the real ER-1.1 alias sets surfaced **two gaps in Revision 1**. Both are
architectural (they fix the shape of the authoritative naming surface, and what the resolver's
closed lookup may legally contain), not implementation details, so they belong in the freeze
rather than in an apply log. Both were escalated and **ratified by the operator on 2026-07-16**.

## 2. Ratified — D-ER-11: aliases mirror the `binding` shape

- A **single-signal** entity uses a **flat alias list**.
- A **multi-signal** entity uses a **per-signal alias map**.
- **No implicit primary signal is introduced.**

**What forced it.** Two of the six bound entities — `entrance-plant`
(`water_warning` + `soil_moisture`) and `zigbee-mesh` (`connection` + `permit_join`) — are
multi-signal, and the schema contract is explicit that such a binding has **no implicit
`state`**: every field is named. An entity-level alias on them would therefore have **no single
`ha_entity` to resolve to**. Both alternatives were worse: inventing a "primary signal" would
smuggle a guess into a resolver whose entire purpose is determinism, and deferring the two
entities would silently shrink the ratified scope. **D-ER-1 specified the field but not its
multi-signal shape; D-ER-11 closes that gap by reusing a pattern the contract already has.**

**Consequence of record.** A name mapping to more than one signal of the same entity (a bare
*"planta"* — soil moisture, or watering warning?) is **deliberately not aliased**. A closed
deterministic resolver must never guess.

## 3. Ratified — D-ER-12: alias vs entity identifier (validation check 12e)

- An alias **may** equal **its own** entity's identifier.
- It **must never** collide with **another** entity's identifier.

**What forced it.** The design draft proposed barring an alias from colliding with **any**
entity identifier. Authoring the real sets disproved it: **4 of the 6 bound entities have an
alias equal to their own normalized id** — `awning`, `main door`, `zigbee mesh`,
`internet uplink`. Those *are* the natural English names of those entities. A blanket ban would
have gutted English coverage for **no safety gain**, because an alias equal to its **own**
entity's identifier is a harmless redundancy: both forms denote the same thing, so no ambiguity
exists. The genuine hazard is a collision with a **different** entity's identifier — a name
denoting another modelled entity is almost certainly an authoring error — and that is what 12e
rejects.

## 4. Correction of record — false attribution about check-12 semantics

**Corrected here, per "reality always wins."**

An earlier draft of the ER-1.1 documentation stated that the **freeze** had barred collision
with "any real id or entity `id`", and described D-ER-12 as *narrowing the freeze's wording*.
**That was false.** Verified against the published Revision 1
(`git show 38eb8262:04_ai_system/entity_resolution_layer.md`): it contains **zero** statements
of check-12 semantics. The over-restrictive rule existed only in the **design draft discussed
at ratification** — never in the frozen document.

The accurate account: **Revision 1 stated no check-12 semantics at all.** The alias ruleset is
authored for the first time at ER-1.1, under the two decisions above. D-ER-12 therefore
**establishes** a rule; it does not narrow a frozen one. The misattribution was caught before
commit and corrected in both places that carried it. A tidier narrative would have blamed the
freeze; the record says otherwise.

## 5. What changed in the spec (Revision 2)

- Status → **Revision 2** + an **amendment table** (Rev 1 = initial freeze at ER-1.0; Rev 2 =
  this amendment at ER-1.1).
- **§3 register** → **D-ER-11** and **D-ER-12** added as first-class ratified decisions.
- **§3.5 (new)** → both decisions with the reasoning that forced them, the consequence for
  ambiguous names, the correction of record, and the authority statement.
- **G-ER-1** → wording aligned to the ratified rules, including the explicit converse: *an alias
  equal to its own entity's identifier is legal and must not be rejected.*

**No dangling forward reference.** The spec deliberately does **not** cite a schema section
number for the alias ruleset: that contract text does not exist at this revision, and a freeze
must not cite what is not present. The enforcement is described as belonging to **ER-1.1**
(authoring) and **ER-1.2** (fail-loud implementation). A precise section reference may be added
once ER-1.1 lands.

## 6. Scope — what this amendment does *not* touch

**Authority is unchanged.** Both decisions concern **naming and validation only**. Aliases
neither widen nor narrow what Aurora may actuate: **D-12 remains the sole authorization
authority (INV-17)**, and the resolver is never consulted to permit or deny (**D-ER-9**).
INV-18 / INV-19 / AD-20 / AD-21 are untouched; `schema_version` and `ARTIFACT_VERSION` both
stay **1**.

No schema change, no entity change, no alias data, no loader code, no runtime or database
change is present in this commit — those are **ER-1.1**, which follows immediately.

## 7. Rollback

`git revert` of this commit restores Revision 1. Documentation only — no runtime state, no
generated artifact, no database, nothing to undo beyond the document. Since ER-1.1 has not yet
landed, reverting leaves no orphaned reference.

## 8. Status

**Revision 2 RATIFIED — at the git gate.** Next: **ER-1.1** (schema `aliases` contract + the six
entity alias sets + G-ER-1 validation), which lands as its own commit immediately after this
one, so history reads *design amended → contract applied*. No `git commit` / `push` / `tag`
without explicit operator approval requested immediately beforehand (`PROJECT_RULES.md` →
Operator Git Approval).
