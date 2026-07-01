# Freeze Log — World Model Architecture (AD-21)

- **Date:** 2026-07-01
- **Type:** Architecture freeze (documentation only; no runtime/code/prompt/tool change).
- **Decision:** **AD-21 — Aurora adopts the World Model as its semantic architectural
  baseline.**
- **Authority:** architect = an AI reasoning assistant; executor/reviewer/documenter = an AI coding assistant. Ratified by the
  operator 2026-07-01.
- **Baseline document (authoritative):**
  [`../04_ai_system/world_model_architecture.md`](../04_ai_system/world_model_architecture.md)
  (FROZEN, Revision 2). This log does not duplicate it — it records the freeze event only.

---

## 1. What was frozen

The World Model as Aurora's **single semantic representation** of its operational world, with:

- **Semantics** — World Model (structure/meaning); Awareness = the model evaluated at `now`;
  Memory = entity evolution over time; Knowledge = timeless entity docs.
- **Substrate** — hybrid single-source **literate model**: Markdown canonical + embedded YAML
  frontmatter; deterministic loader → gitignored/regenerable generated artifact; fail-loud
  validation.
- **Determinism & safety** — deterministic up to Awareness and at the fail-closed Action gate;
  probability only past the B3 seam (reasoning/retrieval); operator-gated actions only.
- **Evolution** — per-entity `schema_version`, additive-first, token/id permanence, bounded
  loader compatibility.
- **Invariants** — the 16 accepted freeze candidates (§2.1) + **INV-17/18/19** (§2.5).

## 2. Findings disposition (from the final audit)

- **Blocking W-1 / W-2 / W-3 — closed** in Revision 2: W-1 → INV-17 (allowlist is the sole
  action-authorization source; `writable`/`boundary` descriptive, never a grant); W-2 → INV-18
  (awareness output preserves the `aurora-context.json` / AD-20 contract); W-3 → duration
  predicate added to the condition grammar (stateless via `last_changed`; B3 intact).
- **Strong recs W-4 / W-5 — closed**: W-4 → §1.5 aggregate model (global verdict escalates
  only ≥ medium); W-5 → INV-19 (single awareness source; makes R-F5-A structural).
- **W-6…W-15 — deferred** as Known Architectural Debt (freeze doc §12); none blocks the
  baseline.

## 3. Relation to R-F5-A

AD-21 is the **remedy architecture** for R-F5-A (the awareness-consumption gap): the
single-channel awareness defect is closed **structurally** (INV-19 — no consumer builds
awareness from raw signals), and the F-4/F-3a contract is preserved (INV-18 / AD-20 held).
**R-F5-A and F-5 completion close at WM-6** (Phase WM). This supersedes the earlier "deferred
to a future gated phase" wording — that phase is now defined as **Phase WM**.

## 4. Freeze package (this change set)

| Artifact | Change |
|---|---|
| `04_ai_system/world_model_architecture.md` | Status PROPOSED → **FROZEN**; §14 AD-21 + freeze record added |
| `04_ai_system/phase_f_architecture.md` | **AD-21** registered in §4 (running AD register); R-F5-A relationship reconciled |
| `00_overview/CURRENT_STATE.md` | Current phase / Next milestone / Blocking issues reconciled |
| `00_overview/ROADMAP.md` | Top summary + new **Phase WM** ledger (WM-0→WM-7) |
| `00_overview/AMAROLAB_HANDOFF.md` | Current phase + Next Immediate Task reconciled |
| `09_logs/2026-07-01_world_model_architecture_freeze.md` | this freeze log |

## 5. Scope guard — what was NOT done

No implementation, no `WM-1`, no runtime/container/DB change, no code, no prompt, no tool,
no collection change. **Implementation (Phase WM) has not begun.**

## 6. Rollback

Documentation-only change set, fully git-revertable: revert the six files above. No runtime
state was touched, so there is nothing operational to unwind. The World Model has no
generated artifact yet (WM-1 not started).

## 7. Next

**Phase WM-1** — `_schema/` foundation (entity schema, tokens registry, windows, archetypes,
validation ruleset). Documentation/authoring only; no runtime. Awaiting operator go-ahead.

## 8. Git

**STOPPED at the git gate.** No `git add`, commit, push, or tag performed. The freeze **tag**
is pending operator approval (ratification step 5, freeze doc §10 / §14). Reality always wins.
