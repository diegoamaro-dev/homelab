# ADR / AD-22 — Voice Lab is a separate experimental track from Phase F-6

- **Status:** Accepted
- **Date:** 2026-07-27
- **Deciders:** Operator (Diego)
- **AMAROLAB decision id:** AD-22 — registered in [`../04_ai_system/phase_f_architecture.md`](../04_ai_system/phase_f_architecture.md) §4
- **Affects:** Phase F-6 (Voice Quality), the Voice Lab track, the production voice pipeline
- **Related:** AD-19 (concurrent phase progression), AD-21 (World Model baseline), R-D-13 (STT shim), §12 Phase F success criteria, Phase D-1 (voice pipeline)

---

## Context

Phase F ("Operational Intelligence") is complete through F-5; **F-6 (Voice Quality) is the
only open sub-phase**, so closing F-6 closes Phase F. The relevant open §12 success criterion
is **"Voice is reliable"** — voice used daily without frustration.

"Voice quality" is not one thing. It has two orthogonal axes:

1. **STT quality + latency** — whether Aurora *hears* Spanish correctly and *responds* fast
   enough. Today `aurora-whisper` runs Whisper `base-int8` (HA Wyoming path) and
   `aurora-whisper-http` runs `Systran/faster-whisper-base` on the **unmaintained**
   `fedirz/faster-whisper-server` (R-D-13, Open WebUI path). This axis is judged by
   **objective** gates — transcription accuracy and latency.
2. **TTS quality + voice identity** — whether Aurora *sounds* right and has a deliberately
   chosen voice. This is explored in the **Voice Lab**: an isolated, **repo-external** effort
   (its code, model weights, container images and audio are intentionally not committed —
   evaluation tooling, not production). Round 1 (native TTS casting, 2026-07-27) blind-compared
   Piper (incumbent), Kokoro `ef_dora`, XTTS v2 and Chatterbox on a fixed Spanish corpus under
   identical, loudness-matched conditions; **Kokoro `ef_dora` was preferred (~70%)** and is now
   the **native TTS reference candidate**, while **Piper remains the production voice (no
   migration)**. Round 2 (voice cloning) is designed but not started; its next gate is to
   **define Aurora's synthetic voice identity**. This axis is judged by **subjective** blind
   casting and carries **licensing/consent** dependencies (e.g. XTTS v2 is Coqui CPML
   non-commercial; a cloned reference voice must come from a legally permitted source).

The architected F-6 scope (`phase_f_architecture.md` §9-F-6) is **entirely STT + latency**; it
never mentioned TTS. The question this ADR settles: does the Voice Lab TTS track belong
**inside** F-6, or as a **separate** track?

## Decision

**The Voice Lab (TTS voice quality and Aurora's voice identity) is a separate experimental
track. Phase F-6 owns production voice reliability only — the STT and latency axis — and
performs no TTS engine migration.** A Voice Lab candidate reaches the production voice pipeline
only through a **separate, operator-approved TTS-migration gate**, never as a side effect of
F-6.

### 1. STT vs TTS responsibilities

| | STT (recognition) | TTS (synthesis) |
|---|---|---|
| Owner | **Phase F-6 (production)** | **Voice Lab (experimental)** → future TTS-migration gate |
| Components | `aurora-whisper` (HA Wyoming), `aurora-whisper-http` (OWUI) | `aurora-piper` / `aurora-piper-http` (production Piper); Kokoro / XTTS / Chatterbox (lab) |
| F-6 work | Whisper upgrade (F-6a); shim migration R-D-13 (F-6b); latency baseline (F-6c) | **none**, except an explicit accept/keep decision on the *current* production voice (F-6d) |
| Success measure | Objective: ≥9/10 Spanish short utterances; documented latency | Subjective: blind casting; operator-ratified voice identity |
| Changes production? | Yes — STT models/containers, gated and reversible | **No — not until a separate TTS-migration gate** |

### 2. Production vs experimental boundaries

| | Track A — F-6 (production) | Track B — Voice Lab (experimental) |
|---|---|---|
| Artifacts | Committed source; install/recovery notes (AD-09) | **Not committed** — code/models/images/audio are repo-external |
| Gates | Objective (G-F6-01…05) | Subjective blind casting; sealed-mapping method |
| Touches production | Yes — STT models, OWUI shim (gated, reversible) | No — nothing in production changes until a separate gate |
| Cloud / locality | Local-only, consistent with "everything local" | Reference-only hosted engines allowed **by hand**; no AMAROLAB cloud calls, no stored credentials |
| Closes Phase F? | **Yes** | **No** |

### 3. Promotion criteria — Voice Lab → production

A Voice Lab TTS candidate is promoted to the production voice **only when all of the following
hold**, at a dedicated operator-approved gate:

1. **Blind-evaluation win recorded.** The candidate wins a blind comparison under the
   sealed-mapping method (labels randomized, mapping revealed only after scoring), recorded in
   a `09_logs/` Voice Lab record.
2. **Voice identity ratified.** Aurora's synthetic voice identity is defined and
   operator-ratified (the Round 2 gate).
3. **Licensing / consent cleared.** The engine's license permits AMAROLAB's self-hosted
   production use, and any cloned reference voice comes from a legally permitted source with
   recorded consent.
4. **Runs in the production topology.** The candidate runs **locally** (no cloud dependency) on
   the production hardware and meets a TTS stability/latency bar under Torre-primary and
   UM790-fallback, without regressing the STT gains from F-6.
5. **Gated migration with rollback.** Adoption follows Phase C / G-5 discipline — pinned
   images, a restic / rollback anchor, real end-to-end re-validation on **both** front doors
   (`ha.amarolab.es`, `ai.amarolab.es`), and baseline restore. Only at this gate does the
   production voice change.

Until every criterion is met, **Piper remains the production voice** and Kokoro `ef_dora` (or
any successor) stays a **reference candidate**.

### 4. Why Phase F-6 only owns production voice reliability

- **The open §12 criterion is reliability, not aesthetics.** "Voice is reliable" is an
  objective daily-habit bar (correct recognition + acceptable latency). Voice *identity* is not
  what blocks daily use.
- **Phase-boundary hygiene.** Folding the Voice Lab into F-6 would couple Phase F's closure to
  an open, subjective R&D decision with legal dependencies — the phase could not close until an
  aesthetic choice and licensing questions resolved. That is exactly the coupling the project's
  freeze discipline (and AD-19's concurrency rule) exist to avoid.
- **Different evidence bars and artifact policies.** F-6 is committed, objectively gated
  production work that touches the STT path; the Voice Lab is uncommitted, subjectively judged
  experimentation that touches nothing in production until a separate gate. Merging them would
  drag experimental artifacts into the production ledger and dilute F-6's completion criteria.
- **Precedent already in the repo.** The project already distinguishes a "reference candidate"
  (Kokoro) from "production, no migration" (Piper). This ADR formalizes that boundary rather
  than inventing it.

## Consequences

**Positive**

- Phase F can close on an objective reliability bar (F-6) without waiting on voice-identity
  R&D.
- The production voice pipeline is protected from experimental churn; changes to it always go
  through an explicit, reversible, operator-approved gate.
- STT and TTS work can proceed in parallel without cross-blocking.

**Negative / accepted**

- A better-sounding candidate (Kokoro `ef_dora`) is deliberately *not* shipped by F-6; the
  perceived-quality improvement waits for the separate migration gate. Accepted: reliability
  first, identity later.
- Two tracks mean two places to look; this ADR and AD-22 keep the boundary explicit.

**Neutral**

- No production change results from this ADR. Piper remains the production voice; F-6's scope is
  unchanged (it was always STT + latency).

## Related

- [`../04_ai_system/phase_f_architecture.md`](../04_ai_system/phase_f_architecture.md) — §9-F-6 (F-6 architecture), §4 AD-22, §12 (success criteria), AD-19, AD-21
- Voice Lab Round 1 record: [`../09_logs/2026-07-27_voice_lab_round1.md`](../09_logs/2026-07-27_voice_lab_round1.md)
- R-D-13 (STT shim migration); Phase D-1 voice pipeline closeout: [`../09_logs/2026-06-18_phaseD1_closeout.md`](../09_logs/2026-06-18_phaseD1_closeout.md)
