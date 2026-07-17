# ER-1.3 — Projection emitter + `aurora-entities.json` (applied 2026-07-17)

- **Phase:** ER-1.3 — the consumer-side projection emitter, plus **D-ER-13** (freeze Revision 3).
- **Spec:** [`../04_ai_system/entity_resolution_layer.md`](../04_ai_system/entity_resolution_layer.md) (Rev 3)
- **Prior:** [`2026-07-16_ER1_2_loader_applied.md`](2026-07-16_ER1_2_loader_applied.md) ·
  [`2026-07-17_ER1_2_G-ER-5_operational_closeout.md`](2026-07-17_ER1_2_G-ER-5_operational_closeout.md)
- **Blast radius: none on live behaviour.** No consumer reads the projection until ER-1.4;
  the artifact is never written; the awareness path is untouched. **Aurora behaves exactly as
  it did before this change.**

---

## 1. Implementation

**New — `ai-stack/ingest/bin/emit-entity-projection`** (consumer-side per **D-ER-5**; the
loader stays pure and in-tree, this script owns the write into `ai-stack/aurora/`, as
`bin/aurora-context` does). Reads the compiled artifact, derives the projection, writes it
atomically. Modes: default emit; `--check` (compare only, never writes); `--artifact` / `--out`
overrides.

Exit codes: **0** emitted / current · **2** fail-loud (artifact missing, unreadable, or
carrying no valid `resolution` block — nothing written, last-good retained) · **3** `--check`
only: projection absent, unreadable or stale ("re-run me"). 2 and 3 are deliberately distinct:
*cannot work* and *needs regenerating* call for different operator actions.

**New runtime artifact — `ai-stack/aurora/aurora-entities.json`** (gitignored; `.gitignore:67`
already covers `ai-stack/aurora/`, so no `.gitignore` change — spec §10 holds). 5 684 bytes;
33 aliases → 8 targets. Content is the artifact's `resolution` block **verbatim** plus a
`provenance` block, and nothing else: the derivation stays auditable by diff, and "carries no
authorization field" stays structurally provable. The other 83 % of the artifact is awareness
material the resolver must never read (**INV-19**).

The projection lands in `ai-stack/aurora/` because that directory is bind-mounted **read-only**
into `openwebui` at `/opt/aurora` — verified in-container to be the resolver's only channel to
host-generated state (`04_ai_system/world_model/` is not visible there). This is a constraint,
not a preference.

**Loader — D-ER-13.** `_loader/validate.py` check 12a now requires an aliased signal to bind
`ha_entity`. `_loader/resolution.py`'s `ResolutionError` guard is **kept** as defence in depth;
its comment previously justified unreachability by a contingent fact about today's tree and now
cites the structural rule. `_loader/tests/test_resolution.py` gains one fault-class test
(42 → **43**). `_loader/__init__.py`: **`LOADER_VERSION` 0.2.0 → 0.2.1** — a patch bump, per the
convention documented beside the constant (0.2.0 was itself bumped for *"a new validation
contract"*); D-ER-13 tightens that contract with no output change and no consumer impact.

**The live artifact keeps `generator.loader_version` 0.2.0, and that is correct.** ER-1.3 does
not regenerate it, and **0.2.0 is the version that actually produced it** — a version stamp
records what built a thing, never whether it is current. Regenerating merely to refresh the
stamp would put ER-1.3 back on the operational path (a new artifact for the 04:15 cycle to
consume) and earn an operational gate, for zero content change. The next loader run stamps
0.2.1. Freshness remains a content question, answered by `resolution_sha256` — which is
**unmoved** (`4848e57a…`).

**Governance — `00_overview/PROJECT_RULES.md`** gains the permanent principle *Content
Provenance over Repository Chronology*. Project-wide and outlives ER-1; ER-1.3 merely authors
it.

**Not scheduled.** `etc/cron.d/aurora-signals` is untouched — deferred per spec §9. The
projection changes only when a human edits frontmatter, so nightly regeneration would buy
nothing while requiring the fail-loud loader to run nightly and placing a writer of the
artifact against `bin/aurora-context`'s 04:15 read where today there is none.

---

## 2. Validation (real data)

**ER-1.3 acceptance criteria** — all PASS:

| # | Criterion | Evidence |
|---|---|---|
| 1 | Real tree compiles under tightened 12a; `resolution` unchanged | hash `4848e57a…` before **and** after — D-ER-13 changes no behaviour |
| 2 | Injected fault rejected fail-loud | `test_alias_on_non_ha_entity_signal_rejected` — `permit_join` rebound to a container ⇒ rejected `(12a, D-ER-13)` |
| 3 | Suites green | **43** loader + **36** evaluator |
| 4 | Projection byte-derived from the artifact | `normalization` / `aliases` / `targets` / `stats` all IDENTICAL to the artifact's block; 33 → 8 |
| 5 | Re-run byte-identical modulo `generated_at` | confirmed |
| 6 | No authorization-adjacent field (**INV-17**) | 61 distinct keys, zero authorization-adjacent — asserted **structurally**, not by grep |

On criterion 6: a substring grep would false-positive on `permit`, because the model legitimately
binds `switch.zigbee2mqtt_bridge_permit_join` (alias *"permitir emparejamiento"*) — a Zigbee
pairing signal, not an authorization field. The guard must be structural.

On criterion 2: no real entity has a non-`ha_entity` binding, so the fault is injected. This does
**not** breach §6's no-synthetic-fixtures rule — G-ER-1's own frozen wording already requires
injected faults, and four have been in the suite since ER-1.2. The rule bars fabricating a gate's
**success** condition; injecting a fault to prove the validator rejects it *is* the test, and the
real evidence is the real loader's real rejection.

**G-ER-6 — producer half: PASS.** Every scenario ran against **scratch copies** via
`--artifact` / `--out`; the real artifact was never deleted or corrupted. That is not fastidiousness:
`bin/aurora-context` reads the real artifact at 04:15, and a broken artifact fail-softs home
awareness to `Unavailable`, which would pollute F-4's accruing digest evidence and undo G-ER-5's
clean baseline. Scratch copies also make the rehearsal timing-independent (cf. §6.2's window
constraint on G-ER-4 / G-ER-7).

| Scenario | Result |
|---|---|
| Artifact missing | rc **2**; nothing written; last-good byte-identical |
| Artifact corrupt (truncated) | rc **2**; nothing written; last-good byte-identical |
| Artifact valid, **no `resolution`** | rc **2**; nothing written; last-good byte-identical |
| Projection stale | `--check` rc **3**; nothing written |
| Projection absent | `--check` rc **3**; nothing written |
| Control (good artifact, current projection) | rc **0** |

**Awareness non-regression — by construction, not by test.** ER-1.3 never writes the artifact and
nothing on the awareness path reads the projection, so **no new operational gate is created**
(unlike ER-1.2, which regenerated the artifact the 04:15 cycle consumes and therefore earned one).
Verified after all work: `world_model.generated.json` and all three `aurora-context.*` files
byte-identical to the pre-change baseline; `artifact_version` still **1**; no temp-file litter.

**A measurement error, recorded.** The first G-ER-6 run reported `rc=0` for every fail-loud
scenario. The emitter was correct; the *harness* was wrong — `rc=$?` after a pipe returns the
exit status of `sed`, not of the command under test. Re-run with the status captured directly.
Recorded because a gate closed on an unexamined `rc=0` would have been exactly the class of
false success claim ER-1 exists to eliminate — here caught in the instrument rather than the
instrument's subject.

---

## 3. Decisions of record

- **D-ER-13** *(Rev 3, ratified 2026-07-17)* — an aliased signal must bind `ha_entity` (check
  12a). Ratifies finding **F-ER12-1** from ER-1.2 §6. Unreachable on the current tree; ratified
  so the rule states the constraint the registry **depends on**, not the one that happens to hold.
  Rationale: spec §3.6.
- **G-ER-6 split** — producer half (ER-1.3, closed here) / consumer half (ER-1.4). The gate as
  written asserts behaviour **at the tool boundary**, and no consumer exists until ER-1.4;
  closing it whole here would claim a verification never performed. Precedent: G-ER-2's
  pre-declared loader half, and G-ER-5's implementation/operational halves.
- **G-ER-1 is untouched.** It closed 2026-07-16 on its Rev 2 condition and that closure
  **stands**: its four enumerated fault classes (12c/12d/12e/12f) are unaffected, and its *"the
  real tree compiles"* clause still holds — provably, since the tightened 12a cannot fire.
  D-ER-13's fault class is an **ER-1.3 acceptance criterion**, never a reason to reopen a gate
  that passed on real evidence. **Gate history is not rewritten.**
- **Missing/empty `resolution` ⇒ fail loud** *(ratified 2026-07-17)*. Never an empty projection:
  that would silently turn every alias into a miss — quieter than a stale projection, and worse,
  because nothing would announce it.
- **Freshness is content-derived** *(ratified 2026-07-17)* — the host-side `--check` is the
  canonical mechanism; `provenance.resolution_sha256` is the sole authority; `docs_commit` is
  traceability only. Now a permanent project rule (`PROJECT_RULES.md`). Spec §9 rewritten
  accordingly: its Rev 1 text listed `docs_commit` as a staleness input and promised staleness
  *"at the tool boundary"* — the container cannot see the artifact, so a tool can never compute
  freshness at all.
- **`LOADER_VERSION` → 0.2.1, artifact not regenerated** *(ratified 2026-07-17)*. The patch bump
  follows the convention documented beside the constant; the artifact continues to report 0.2.0
  because that is the version that generated it. The two facts are consistent, not contradictory
  — under *Content Provenance over Repository Chronology* a version stamp is **traceability**,
  and currency is decided by content hash (unmoved).
- **Implementation choices** (not architectural): `projection_version: 1`, matching this repo's
  versioned-artifact discipline — ER-1.4 may pin it. Temp files are **pid-unique** rather than
  suffix-derived (see F-ER13-1).

---

## 4. Discovered — recorded, not silently fixed

**F-ER13-1 — `bin/aurora-context` can publish one file's content under another file's name.**
Its `write_atomic` derives the temp path via `path.with_suffix(".tmp")`, so `aurora-context.json`
and `aurora-context.md` **both** map to `aurora-context.tmp`; and unlike `bin/ingest-nightly`
(`flock -n`), `bin/aurora-context` holds **no run-lock**.

**Harmless today:** the three writes are sequential within one process, and `os.replace` removes
the temp before the next write recreates it. **The hazard is concurrency:** a manual run
overlapping the 04:15 cron could interleave — run A writes JSON to the shared temp, run B
overwrites it with markdown, run A replaces → `aurora-context.json` contains prose. The F-3a
Filter reads that file for its AD-10 freshness decision, and `system_status` reads it too.

**Not fixed.** It is pre-existing and outside ER-1.3's approved scope — a narrow change must not
quietly widen (the ER-1.2 §6 / WM-era-debt precedent). It *did* inform this phase: the emitter
uses a pid-unique temp, so the new code cannot reproduce the pattern. Tracked as **known pending
item 9** in [`../00_overview/CURRENT_STATE.md`](../00_overview/CURRENT_STATE.md) — an apply log
records a *discovery*, but only a live tracker keeps an *open hazard* visible.

---

## 5. Rollback

`git revert` the ER-1.3 commit; delete `ai-stack/aurora/aurora-entities.json` (fully regenerable,
gitignored); re-run the loader. **The artifact is untouched by ER-1.3, so there is nothing to
unwind** — and `ARTIFACT_VERSION` never moved, so the evaluator is unaffected in either
direction. Reverting D-ER-13 restores the looser check, which remains unreachable on the real
tree either way. No database, container, cron or awareness state is involved. **No live behaviour
changes in either direction.**

---

## 6. Documentation reconciliation

Freeze → **Revision 3** (status, amendment table, §3 register, §3.6, §5, §6, §9, §10). Schema
contract §2.2 + §5.1 row 12a. `PROJECT_RULES.md` gains the permanent principle (`Last updated`
→ 2026-07-17). Triad reconciled: next milestone → **ER-1.4a**; G-ER-6 halves recorded; F-ER13-1
added as pending item 9. Per *Transient Operational Status*, the sweep also clears the markers
this commit's own publication would otherwise leave behind.

---

## 7. Status

**ER-1.3 COMPLETE (implementation + validation) — at the git gate.** **G-ER-6 producer half
CLOSED**; consumer half open (ER-1.4). D-ER-13 ratified. G-ER-1 / G-ER-2 / G-ER-5 unchanged.
Next: **ER-1.4a** — capture the v0.1.0 baseline, then `ha_get_state` v0.2.0 (G-ER-7 read half).

**Aurora's behaviour is still unchanged**: the tools remain v0.1.0, no consumer reads the
projection or the registry, and the 13 historical unverified writes would still be reported as
successful today. **ER-1 changes reality at ER-1.4b**, when ER-1-C1 lands.

No `git commit` / `push` / `tag` without explicit operator approval requested immediately
beforehand (`PROJECT_RULES.md` → *Operator Git Approval*).
