# Phase F — F6.0 Architecture (drafted) + R-F5-A Documentation Hygiene — Applied

**Date:** 2026-07-27
**Type:** Documentation only — architecture draft + record reconciliation. No code, tool,
container, DB, prompt, or schema change. **No Phase F-6 implementation started.**
**Files:** `04_ai_system/phase_f_architecture.md` (modified),
`01_architecture/adr_voice_lab_phase_f6_separation.md` (new), this log.

---

## 1. Implementation

### Step 1 — R-F5-A stale-reference hygiene (no architectural change)

Reconciled four spots in `phase_f_architecture.md` that still framed R-F5-A as *"deferred to a
future gated phase"* — stale since WM-6:

- **AD-21 note (§4):** "closes at WM-6 … not started" → "closed at WM-6 (2026-07-16; Phase WM
  implemented through WM-6)".
- **F-5 section header (§9).**
- **F5.3 milestone row.**
- **§11 R-F5-A finding note.**

All updated to the durable fact already recorded in the file's own F-5 body (WM-6 update) +
revision log (WM-6 row) and across the overview triad: **G-F5-04 CLOSED / R-F5-A CLOSED / F-5
CLOSED at WM-6 (2026-07-16)**. The historical **2026-07-01 F5.3 revision row is left intact**
(superseded, not rewritten). A dated hygiene entry was added to §15.

### Step 2 — F-6 architecture drafted + AD-22 + ADR

- **AD-22** registered in `phase_f_architecture.md` §4: the Voice Lab (TTS voice quality /
  Aurora's voice identity) is a **separate experimental track** that does not gate Phase F.
- **Standalone ADR** published — `01_architecture/adr_voice_lab_phase_f6_separation.md`:
  STT/TTS responsibilities, production-vs-experimental boundary, 5-point promotion criteria,
  why F-6 owns reliability only.
- **F-6 section (§9)** redrawn from the operator-approved shape — **production voice
  reliability only (STT + latency)**: F-6a STT model quality, F-6b STT shim migration (R-D-13),
  F-6c latency baseline, F-6d production-TTS acceptance *decision* (no engine swap). Gates
  **G-F6-01…05** + repro. Milestones **F6.0→F6.4** (F6.1+ NOT STARTED). A dated F6.0 entry was
  added to §15.

## 2. Decisions of record

- **AD-22 (ratified 2026-07-27):** Voice Lab separated from Phase F-6; a lab candidate reaches
  production only through a separate operator-approved **TTS-migration gate** (Phase C / G-5
  discipline). **Piper remains the production voice; no migration implied.**
- **F6.0:** F-6 architecture **DRAFTED**; shape operator-approved; formal freeze at the git
  gate. F6.1+ not started.

## 3. Validation (read-only review, 2026-07-27)

**PASS on all 8 review points:** AD-22 style-consistent with the existing register; ADR ↔ AD-22
no contradiction; F-6d strictly a production acceptance decision (no migration / no deployment /
no lab artifact enters production / future migration = separate gate); Voice Lab Round 2
non-blocking for F-6 closure; F-6 success criteria objective and testable; rollback defined for
the production-changing milestones (F6.1 / F6.2); no implementation implied as approved;
sanitized (no secrets, no private IPs, no vendor/AI attribution). **No required corrections.**
Authoritative artifacts: `phase_f_architecture.md` §4 (AD-22) / §9-F-6 / §15; the ADR.

## 4. Rollback

`git revert` this commit, or restore the three files to their pre-commit state. No runtime state
was touched — nothing to unwind operationally.

## 5. Git gate

Documentation-only commit. **Not pushed** — origin update is a separate operator decision.
STOP at git gate.
