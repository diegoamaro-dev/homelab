# ER-1.2 — G-ER-5 operational half: CLOSED on real unattended evidence

- **Date:** 2026-07-17   **Phase:** ER-1.2 (gate closure)   **Status:** **G-ER-5 CLOSED — PASS.**
- **Class:** read-only operational verification + documentation reconciliation.
  **No code, loader, evaluator, tool, artifact, test or architecture change.**
- **Closes:** the operational half of **G-ER-5** left open by
  [`2026-07-16_ER1_2_loader_applied.md`](2026-07-16_ER1_2_loader_applied.md) §3.4.
  That log recorded *"NOT closed — pending the next unattended 04:15 cycle"*, which was
  **true when written**. It is a historical record and is **not rewritten**
  (`PROJECT_RULES.md` → *Historical Documentation*); this log is the later documentation
  that closes the gate.

## 1. The evidence — real, unattended, cron-driven

The **first unattended 04:15 cycle after the ER-1.2 artifact regeneration** ran on
**2026-07-17**. No attended or synthetic run was used, and none was permitted as evidence.

| Fact | Value |
|---|---|
| Artifact regenerated (ER-1.2) | 2026-07-16 **22:08:12** |
| Unattended cycle | 2026-07-17 **04:15:01** CEST (`generated_at 2026-07-17T02:15:01Z`) |
| Cycle chain | backup-probe **ok** → container-probe **ok** → aurora-context → push-voice-context **ok** (`http=200`) → generate-digest **ok** |
| Artifact consumed | `loader_version 0.2.0`, `artifact_version 1`, `resolution` present |
| Digest | `09_ops/runtime/2026-07-17_ops_digest.md` (`overall_status: degraded`) |

## 2. Acceptance criteria

| Criterion | Result |
|---|---|
| Unattended cycle completed | **PASS** — all five steps |
| `generated_at` after the regeneration | **PASS** — 22:08 → 04:15 |
| Regenerated artifact consumed | **PASS** — 0.2.0 + `resolution` is the only artifact the evaluator reads |
| `artifact_version 1` accepted | **PASS** — Home State rendered ⇒ `load_artifact()` did not raise |
| No `ArtifactError` / fallback | **PASS** — **0** occurrences across the whole log history |
| Home State remained available | **PASS** — **`Degraded`**, not `Unavailable` |
| No evaluator / awareness regression | **PASS** — every field identical to baseline (§3) |
| Real anomaly reported truthfully | **PASS** — §4 |
| No synthetic / attended run as evidence | **PASS** |

## 3. Post-cycle vs the pre-ER-1.2 baseline — identical

| Field | Baseline (2026-07-16 04:15) | Post-cycle (2026-07-17 04:15) | Match |
|---|---|---|---|
| `overall_status` | degraded | degraded | ✓ |
| `world.verdict` | medium | medium | ✓ |
| `world.regions` | `{home: medium, infrastructure: ok}` | `{home: medium, infrastructure: ok}` | ✓ |
| `home.anomalies` | `[awning_left_extended, plant_water_warning]` | `[awning_left_extended, plant_water_warning]` | ✓ |
| `signals_missing` | `[]` | `[]` | ✓ |
| `schema_version` | 1 | 1 | ✓ |

Only `generated_at` advanced (by exactly 24 h). **The additive `resolution` registry and
`LOADER_VERSION 0.2.0` are operationally inert**: real unattended awareness is unchanged.
**D-ER-7 held** — `ARTIFACT_VERSION` stayed **1**, so the evaluator accepted the artifact
instead of failing soft to `Home State: Unavailable`.

## 4. Truthfulness — legitimate state change vs regression

**`awning_left_extended` — real.** `cover.toldo = open`, `last_changed 2026-07-09`:
unchanged for eight days, so it was demonstrably open at 04:15. The rule
(`state == open AND time in overnight`, 00:00–06:00) fired correctly.

**A reading that would have looked like a regression, and was not.** Evaluated at 22:33
the night before, the model reported **one** anomaly / `home: low` / `ok` — the awning
token cannot fire outside the overnight window. At 04:15 the window reopened and the
token returned, restoring two anomalies / `medium` / `degraded`. This was **predicted in
advance** and confirmed. Judging that evening reading against the 04:15 baseline would
have raised a **false regression**.

**`plant_water_warning` — real, but live state is not the proof.**
`sensor.sensor_planta_entrada_water_warning` now reads `alarm` with
`last_changed 2026-07-17T06:57:09Z` — **after** the `02:15:01Z` cycle. The current value
therefore **cannot** confirm what the cycle observed. Corroborated instead from three
records written **by that cycle** — the context block (`[low] entrance plant needs
water`), the voice line, and the digest — plus the token appearing in **five consecutive**
unattended cycles (2026-07-13 → 2026-07-17). The report was truthful; the 06:57Z change is
a legitimate post-cycle sensor movement, not drift.

## 5. Gate status after this closure

| Gate | Status |
|---|---|
| **G-ER-1** | **CLOSED** (ER-1.2 — check 12 fail-loud in the real loader) |
| **G-ER-2** | loader half **PASS**; tool half closes at ER-1.4 |
| **G-ER-5** | **CLOSED** — implementation validation (ER-1.2) **+ operational non-regression (this log)** |
| G-ER-3a/3b · G-ER-4 · G-ER-6 · G-ER-7 | open — ER-1.3 / ER-1.4 |

## 6. Documentation reconciliation performed here

1. **G-ER-5 → CLOSED** across the triad.
2. **Stale transient status reconciled.** All three triad documents still described
   ER-1.2 as *"at the git gate"* after `b0fded73` was committed **and pushed**
   (`HEAD == origin/main`) — the third recurrence of this drift in Phase ER-1.
3. **New permanent convention: `PROJECT_RULES.md` → *Transient Operational Status*.**
   Operational status is transient metadata; the triad must never knowingly hold a false
   status; every reconciliation sweeps for stale markers; durable phrasing
   (`committed + pushed <hash>`) is preferred to the moment ("at the git gate");
   **historical logs are exempt and stay exempt**; accuracy outranks commit purity. The
   rule exists because the pattern is **structural** — a document asserting its own
   pending state is false the moment it lands — not because anyone was careless.

### 6.1 Found and deliberately NOT reconciled — WM-era debt

The first sweep under the new rule surfaced **pre-existing WM-era** stale status:
`CURRENT_STATE.md` and `ROADMAP.md` still describe **WM-4** as *"STOPPED at the git gate
(not committed)"* (reality: **`476e0ae8`, pushed**), and `AMAROLAB_HANDOFF.md` describes
**WM-5** the same way (reality: **`b2b04670`, pushed**).

**Left unreconciled by operator decision.** It predates ER-1.2 and is outside this
change's approved scope; a narrow commit must not quietly widen. Recorded as technical
debt in `ROADMAP.md` → *Documentation Hygiene — Follow-up*, with exact sites, so a future
reconciliation can act without rediscovering it. The governance rule guarantees it is
eventually cleared.

**Two classes the sweep also surfaced must NOT be "fixed"**, and are recorded so a future
session does not mistake them for drift:
- `"Each phase/sub-phase: … STOP at the git gate"` — a **process rule** describing the
  gate discipline itself; correct as written. Sweeping carelessly would delete the
  project's own workflow rule.
- `"not committed in plain text"` (Secrets section) — the **secrets policy**, not a git
  status.

## 7. Rollback

Documentation only — `git revert` of this commit. No runtime state, artifact, database or
code is touched. The gate evidence itself is immutable: it is the cron log, the digest,
and the awareness artifacts written by the unattended cycle.

## 8. Status

**G-ER-5 CLOSED. ER-1.2 COMPLETE.** Next: **ER-1.3** (projection emitter +
`aurora-entities.json`; gate G-ER-6).

**Aurora's behaviour is still unchanged** — tools remain v0.1.0, no consumer reads the
resolution registry, and the 13 historical unverified writes would still be reported as
successful today. ER-1 changes reality at **ER-1.4b**, when ER-1-C1 lands.
