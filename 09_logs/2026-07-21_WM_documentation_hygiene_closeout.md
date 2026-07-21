# WM documentation hygiene — closeout (2026-07-21)

- **Task:** WM-era documentation hygiene. **Documentation-only reconciliation.** No
  production code, schema, loader, tool, generated artifact, or tag.
- **Governing rule:** [`../00_overview/PROJECT_RULES.md`](../00_overview/PROJECT_RULES.md)
  → *Transient Operational Status* (rules 1–3: the triad must never knowingly contain
  false operational status; every reconciliation sweeps for stale transient markers;
  prefer durable phrasing).
- **Closes:** the WM-era stale-transient-status debt recorded at
  [`../00_overview/ROADMAP.md`](../00_overview/ROADMAP.md) → *Documentation Hygiene —
  Follow-up*, found 2026-07-17 and deliberately deferred then (it predated ER-1.2 and
  was outside that change's approved scope).
- **Prior:** [`2026-07-21_ER1_5_closeout.md`](2026-07-21_ER1_5_closeout.md) §6, which
  carried this debt forward as a separate task.
- **Baseline:** branch `main`, working tree clean, `HEAD = origin/main = 49caf91d`.

---

## 1. The defect

Four live documents asserted a **git status that had been false since 2026-07-14**:
WM-4 and WM-5 were described as "STOPPED at the git gate (not committed)" when both
were long committed and published. `CURRENT_STATE.md` was **internally
contradictory** — the same paragraph recorded WM-4 as both "STOPPED at the git gate"
and "committed + pushed (`476e0ae8`)".

Two further transient markers were in the same class and are cleared with them:

- **G-WM4-6** described as "open, closes on 2026-07-14 real evidence" — it closed on
  2026-07-14.
- **`system_status` v0.3.0** described as "`webui.db` install operator-gated" — the
  install was performed and verified on the running assistant 2026-07-14 (G-WM5-3,
  D-WM5-5).

## 2. Verification of the durable facts

Established from git before any edit, not from documentation:

| Claim | Evidence |
|---|---|
| WM-4 = `476e0ae8` | `feat+docs(world-model): WM-4 evaluator cutover — retire HOME_RULES`, 2026-07-13; ancestor of `origin/main` |
| WM-5 = `b2b04670` | `feat+docs(world-model): WM-5 consumer convergence — world verdict, home-aware surfaces`, 2026-07-14; ancestor of `origin/main` |
| G-WM4-6 closed 2026-07-14 | [`2026-07-13_WM4_evaluator_cutover_applied.md`](2026-07-13_WM4_evaluator_cutover_applied.md) (closure recorded at WM-5) |
| `system_status` v0.3.0 installed + verified | [`2026-07-14_WM5_consumer_convergence_applied.md`](2026-07-14_WM5_consumer_convergence_applied.md) §D-WM5-5 and G-WM5-3 |
| No WM tag exists | `git tag -l` — 22 tags, none for Phase WM |

## 3. Changes applied

Transient markers replaced with the **fact**, per rule 3.

| Document | Change |
|---|---|
| [`../00_overview/CURRENT_STATE.md`](../00_overview/CURRENT_STATE.md) | §Current phase — WM-4 "STOPPED at the git gate (not committed)" → `committed + pushed 476e0ae8`; G-WM4-6 "open, closes on…" → `CLOSED 2026-07-14`; WM-5 → `committed + pushed b2b04670`. §Next milestone — WM-5 "at the git gate" → the published hash, `system_status` "operator-gated" → installed + verified; the "immediate next task = the hygiene pass" sentence retired (it goes false as this commit lands — rule 1). §Blocking issues — WM-4 "at the git gate" → the published hash |
| [`../00_overview/ROADMAP.md`](../00_overview/ROADMAP.md) | §Phase F header line and §Phase WM narrative — WM-4 "STOPPED at the git gate" → published hashes, WM-5 hash added; WM-5 table row — "at the git gate" + "install operator-gated" → published hash + installed/verified; §Documentation Hygiene — Follow-up — the WM-era bullet marked **RESOLVED** with a pointer to this log |
| [`../00_overview/AMAROLAB_HANDOFF.md`](../00_overview/AMAROLAB_HANDOFF.md) | Phase WM summary — WM-4 "STOPPED at the git gate (not committed)" → `committed + pushed 476e0ae8`, G-WM4-6 "open" → `CLOSED 2026-07-14`, WM-5 hash added; Phase WM-5 detail — "STOPPED at the git gate" → `committed + pushed b2b04670`, `system_status` "operator-gated" → installed + verified |
| [`../04_ai_system/world_model/README.md`](../04_ai_system/world_model/README.md) | §Status — Phase WM — WM-5 "at the git gate" → `committed + pushed b2b04670`; `system_status` "operator-gated" → installed + verified |

## 4. Deliberately not changed

- **All of `09_logs/`.** No historical log was modified. Their transient status is
  **evidence of what was true then** (*Transient Operational Status* rule 4 /
  *Historical Documentation*). This specifically includes
  [`2026-07-14_WM5_consumer_convergence_applied.md`](2026-07-14_WM5_consumer_convergence_applied.md),
  which is **internally inconsistent** — §Deliverables says `system_status` is "Not yet
  installed" while D-WM5-5, G-WM5-3 and §Rollback record the install as performed and
  verified the same day. It stays exactly as written; the live documents above now
  carry the correct state, which is the sanctioned form of correction.
- **Process-rule phrasing.** "Each phase / sub-phase: … STOP at the git gate"
  (`ROADMAP.md`, [`../04_ai_system/entity_resolution_layer.md`](../04_ai_system/entity_resolution_layer.md))
  describes the **workflow** and is correct as written.
- **Secrets policy.** "`ai-stack/.env` (not committed in plain text)" in
  `CURRENT_STATE.md` is a **secrets statement**, not a git status.
- **[`../04_ai_system/world_model_architecture.md`](../04_ai_system/world_model_architecture.md)
  — excluded by operator decision.** Two stale claims remain, both in the §Status header
  (lines 7–8, 11) and the *Freeze record* table (lines 568–569):
  **(i)** the freeze package is "not committed, not pushed, not tagged" — "not committed /
  not pushed" is **false** (`b43e8aad`, published), while **"not tagged" is true** (no WM
  tag exists; `git tag -l` → 22 tags, none for Phase WM);
  **(ii)** `| Implementation | Phase WM (WM-1→WM-7) — **not started** |` — false, Phase WM
  ran WM-1 through WM-6 (WM-6 closed 2026-07-16).
  Left untouched because it is a **frozen architecture document** and WM-0 era, not
  WM-4/WM-5. **Recorded as remaining debt** in `ROADMAP.md` → *Documentation Hygiene —
  Follow-up*.
- **[`../04_ai_system/phase_f_architecture.md`](../04_ai_system/phase_f_architecture.md):1042**
  — the F3.3 milestone row still reads "**current**" though F-3 closed 2026-06-29. Genuine
  drift of the same class, but **F-3 era, not WM-4/WM-5**; outside this pass's scope.
  Flagged here so a future sweep does not have to rediscover it.

## 5. Validation

- Sweep re-run after the edits over the three triad documents and
  `world_model/README.md`: **zero** remaining WM-4 / WM-5 transient markers.
- No file outside the four documents above and this log was modified
  (`git status --porcelain`).
- No file under `09_logs/` was modified other than the addition of this new log.
- No code, schema, loader, tool, generated artifact, or tag was touched.

## 6. Rollback

`git checkout -- 00_overview/CURRENT_STATE.md 00_overview/ROADMAP.md
00_overview/AMAROLAB_HANDOFF.md 04_ai_system/world_model/README.md` and delete this log.
Documentation-only: nothing runtime, nothing generated, no operational consequence.

## 7. Note on the rule

This is the second sweep under *Transient Operational Status*. The first (2026-07-17)
**found** this drift and correctly declined to fix it out of scope; the rule's guarantee
that "a future reconciliation will clear it" is what this log discharges. The drift had
survived publication for **seven days** across four documents while two of them stated
the correct hash elsewhere in the same paragraph — evidence for the rule's own premise
that a document asserting its own pending state is false the moment it lands, and that
the marker is not reliably noticed by the change that publishes it.
