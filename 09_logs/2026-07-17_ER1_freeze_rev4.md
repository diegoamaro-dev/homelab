# ER-1 — freeze amendment: Revision 4 (D-ER-14) — applied

- **Date:** 2026-07-17   **Phase:** ER-1 (design amendment + applied rename)   **Status:**
  **RATIFIED + APPLIED — at the git gate.**
- **Class:** design amendment + decision register + the applied rename it mandates. Unlike
  Rev 2 this amendment carries an implementation delta: `ha_get_state` **0.2.0 → 0.2.1**
  (patch), reinstalled in `webui.db`. No schema, entity, loader, projection, artifact or
  cron change; `ha_call_service` untouched at v0.1.0.
- **Amends:** [`../04_ai_system/entity_resolution_layer.md`](../04_ai_system/entity_resolution_layer.md)
  → **Revision 4**.
- **Preserves:** the ER-1.4a apply log
  [`2026-07-17_ER1_4a_ha_get_state_applied.md`](2026-07-17_ER1_4a_ha_get_state_applied.md)
  is unchanged historical evidence — it records the field as `modelled` because that is what
  it was named when written (`PROJECT_RULES.md` → Historical Documentation). This log is the
  later documentation that carries the correction.
- **Also in this change:** the **pre-registered ER-1.4b C1 measurement protocol**
  ([`2026-07-17_ER1_4b_c1_measurement_protocol.md`](2026-07-17_ER1_4b_c1_measurement_protocol.md))
  — committed **before any measurement is taken**, so the immediate-read vs bounded-retry
  choice is provably decided by predefined criteria, not by the observed outcome (operator
  direction, 2026-07-17). Git order is the proof: protocol first, measurement later.

## 1. Ratified — D-ER-14: the step-4 audit observability field is named `registry_target`

**Operator-ratified 2026-07-17** (resolves **F-ER14-1**, recorded at ER-1.4a §4): the field
the §4 ladder stamps at step 4 answers *"is this id a target in the resolution registry?"* —
the aliased, `ha_entity`-bound signals of modelled entities (D-ER-6) — and its name now says
exactly that. The operator's ratification wording: *"the audit field should describe exactly
what is being verified, not a broader architectural concept … apply the rename as a
controlled specification update before ER-1.4b so write-path audit records are created with
the correct field name from the beginning."*

**What forced it.** `modelled` claimed *"the World Model models this entity"* while the check
answers registry-target membership, and the two provably diverge: `sun.sun` →
`modelled: false` though `environment/daylight-time.md` binds it. A field whose name
overstates what was checked is the §1.2 defect class in a new place. Alternatives considered
at ratification: keep `modelled` + define it in §4 (rejected — an evidence record is read
wherever the log is read; the trap survives every reading that skips the spec);
`resolvable` (rejected — membership, not resolvability, is what is checked).

**Cost — measured, zero.** `modelled`: **0 occurrences** in
`amarolab-audit.log{,.1}` (verified 2026-07-17 before the rename; the ER-1.4a probes ran
against a scratch log). No historical audit line carries the old name. This was the last
moment the rename would ever be free — ER-1.4b stamps the field on writes.

## 2. Applied

| File | Delta |
|---|---|
| `04_ai_system/entity_resolution_layer.md` | Status → **Revision 4**; amendment-table row; **D-ER-14** in the §3 register; new **§3.7** (rationale, options, zero-cost proof, gate treatment); §4 step 4 → `registry_target`; §10 inventory updated (`ha_get_state` → v0.2.1; audit-writer note) |
| `ai-stack/openwebui-tools/tools/ha_get_state.py` | `audit_extra["modelled"]` → `audit_extra["registry_target"]` (both sites), local variable + step-4 comment aligned; frontmatter **0.2.0 → 0.2.1**; reinstalled via `bin/install_tool` (row verified `version: 0.2.1`) |
| `ai-stack/openwebui-tools/lib/entity_resolver.py` | `is_target.__doc__`: the F-ER14-1 trap warning becomes the field's definition; history note retained (docstring only — no behaviour change) |
| `ai-stack/openwebui-tools/lib/audit_helper.py` | docstring example list `modelled` → `registry_target` (docstring only) |

The word *modelled* elsewhere (D-ER-6 "modelled entities", schema prose, World Model docs) is
not the audit field and is untouched. Historical logs untouched.

## 3. Validation (real data)

**Baseline first (§6.2.1 discipline):** before any edit, the HEAD source inlined via
`install_tool --dry-run` was proven **byte-identical to the installed v0.2.0 row** (modulo
the dry-run's trailing newline) — the reference and rollback target is exact.

**Paired A/B, v0.2.0 (reproduced baseline) vs v0.2.1 (installed row, loaded through
`load_tool_module_by_id` — the production path), 18-case §6.1 read corpus,** pairs
back-to-back to control entity volatility (zero volatility re-runs needed):

- **Return payloads: 18/18 byte-identical.** The tool's return contract never carried the
  field; the rename is invisible at the return surface — confirmed, not assumed.
- **Audit lines: 18 vs 18, zero mismatches** outside the mapped key name. The rename applies
  on exactly the expected **12** pairs (7 id-shaped → `registry_target: true|false`, 5 alias
  hits → `registry_target: true`); fixed keys, values and `resolved_to` identical.
- **v0.2.1 emitted zero `modelled` keys; v0.2.0 emitted zero `registry_target` keys** — the
  cutover is total, not partial.
- **The real `amarolab-audit.log` is untouched** — md5-identical before/after; all probe
  audit went to container-scratch paths via the helper's documented override.
- Probes are reads only; the printer was not actuated; the §6.2.2 window does not bind.

## 4. Gate treatment — nothing reopened

**G-ER-7 (read half) stays CLOSED on its 2026-07-17 evidence.** Its condition — pre-existing
audit keys byte-identical, new keys purely additive — is untouched by renaming an additive
key. The rename is validated as an **ER-1.4b acceptance criterion** (the D-ER-13 pattern:
a frozen-rule gap surfaced by implementation is ratified and validated forward, never by
rewriting a closed gate). The A/B run above is that acceptance evidence, banked early.

## 5. Rollback

Reinstall the committed v0.2.0 source (`3ad8779f`) via `install_tool` — single `webui.db`
row, no restart (D-WM5-5 pattern); `git revert` restores spec Revision 3. Lib docstring
changes are inert for every other tool (each carries its own inlined snapshot). Honest note:
rollback restores the misleading field name, not any behaviour — behaviour is identical on
both sides, proven above.

## 6. Status

**Revision 4 RATIFIED + APPLIED — at the git gate.** Pending item 10 (F-ER14-1) is resolved.
Next: **ER-1.4b proper** — Step 1 (capture the `ha_call_service` v0.1.0 baseline), Step 2
(execute the pre-registered C1 measurement protocol), Step 3 (`ha_call_service` v0.2.0 —
resolution + ER-1-C1), gates G-ER-2/3/4, G-ER-7 write half, G-ER-6 consumer half (write
side). No `git commit` / `push` / `tag` without explicit operator approval requested
immediately beforehand (`PROJECT_RULES.md` → Operator Git Approval).
