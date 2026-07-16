# Aurora v1.0 — Foundation Milestone

- **Date:** 2026-07-16   **Type:** milestone / chapter closeout (documentation only)
- **State of record:** `origin/main` @ `b4fa1a5b` (WM-6 — G-F5-04 closed).
- **Status:** **PREPARED — not committed / pushed / tagged.** No code, prompt, tool, schema, loader, database or architecture change.
- **Authority:** [`../04_ai_system/AURORA_VISION.md`](../04_ai_system/AURORA_VISION.md) §1/§2/§9 · [`../00_overview/ROADMAP.md`](../00_overview/ROADMAP.md) · [`../04_ai_system/world_model_architecture.md`](../04_ai_system/world_model_architecture.md) (AD-21).

---

## 1. What this milestone marks

Aurora has completed the transition the vision was built around: from a **reactive** assistant that answers when asked to an **aware, remembering** operational assistant that "arrives to each conversation already knowing the relevant state of the world" (AURORA_VISION §1). With WM-6 (2026-07-16) closing G-F5-04, that awareness was **validated across both front doors — chat (`ai.amarolab.es`) and voice (`ha.amarolab.es` / AURORA v1) — under the current operational configuration** (a real induced anomaly, chat + voice). Documented voice-path refinements (F-VOICE-CONTRADICT, F-ASSIST-BLIND) remain future improvements, not unresolved foundations.

This is the **first complete operational configuration** of Aurora as the vision defines it: aware, remembering, honest, and safe-by-construction. It is the foundation on which every later addition (Depth, Breadth, proactive intelligence — §9) compounds.

## 2. What has been achieved (the operational spine)

| Layer | Capability | Closed |
|---|---|---|
| Reasoning core | `qwen2.5:7b-instruct` + tool layer (`time_now`, `rag_search`, `audit_search`, `ha_get_state`, `ha_call_service`, `system_status`, `docker_*`) | Phases A/B/C |
| Safe action | HA control via the **D-12 allowlist**, validated end-to-end at Gate G-5 (`switch.impresora_3d`, real Z2M round-trip + baseline restore) | Phase C (2026-06-17) |
| Voice front door | STT / TTS / wake-word — AURORA v1 pipeline, real-device round-trip | Phase D-1 (2026-06-18) |
| Compute | Torre GPU node + failover proxy (Torre primary, UM790 fallback) | Phase RTX-1 (2026-06-27) |
| Knowledge | RAG corpora + onboarding framework (`ops_digests`, `homelab_docs`, …) | Phase E (2026-06-28) |
| Situational awareness | nightly signals → `aurora-context` → F-3a chat Filter + F-3b voice line | Phase F-0…F-3 (2026-06-29) |
| Operational memory | nightly operational digests → `ops_digests` → date-anchored retrieval | F-4 (implemented 2026-06-30) |
| **World Model** | a single semantic representation of Aurora's world (AD-21): literate entities → deterministic loader → evaluator → **every surface a projection of one evaluation** (INV-19) | WM-0…WM-6 |
| **Awareness convergence** | **G-F5-04 CLOSED** — the induced home anomaly is surfaced truthfully across chat **and** voice; R-F5-A structurally resolved | WM-6 (2026-07-16, `b4fa1a5b`) |

Foundation state: WM-1 `6e97c3fb` · WM-2 `4c3e2a5d` · WM-3 `8d653fea` · WM-4 `476e0ae8` · WM-5 `b2b04670` · WM-6 `b4fa1a5b`. Every phase closed on **real-data validation** with an apply log; no synthetic fixtures.

## 3. Architectural goals now complete

- **Reactive → aware (§1).** Aurora arrives to a conversation already holding the current world state; proven end-to-end at WM-6 on both front doors.
- **Home state, not point queries (§2 · Action).** The vision's named gap — "no home context to reason with — only point queries" — is closed: the World Model gives Aurora a reasoned home state, not raw entity values.
- **One world, many projections (INV-19).** A single awareness source; chat Filter, `system_status`, and the voice line are dumb projections of one evaluation. The R-F5-A single-channel failure class is now **structurally impossible**, not merely patched.
- **Honest awareness / reliability (§1).** Severity-tiered surfacing with "silence is informative" (§1.5 — a low-only home stays `ok`); the system reports the real world, including when it is degraded.
- **Safe-by-construction action (AURORA_VISION §7 · INV-17).** Actuation is bounded by the D-12 allowlist; Aurora executes or recommends — it never acts autonomously.
- **Local, documented, recoverable (Long-Term Vision).** Fully local stack; every phase gated on real evidence, apply-logged, and restic-backed.

## 4. Why this is the first complete operational version

The daily value loop (AURORA_VISION §2) now closes end-to-end on real data:
- **Briefing** — "what happened / is everything OK?" answered without a command, from the pre-generated nightly context, honest about generation time and degradation.
- **Action** — home devices queried and controlled through voice or chat, over a reasoned home state, within a safe allowlist.
- **Knowledge** — operational digests and project documentation retrieved and reasoned over via RAG.

Aware **and** remembering, honest **and** safe — this is the minimal complete form of the assistant the vision describes. Everything beyond it makes the foundation richer; nothing beyond it is required for the foundation to stand.

## 5. Intentionally outside v1.0 — enhancements, not missing foundations

Each deferred item maps to the vision's own **Depth / Breadth / proactive** axes (§9): additions that compound on the foundation, not gaps in it.

| Item | Why it is an enhancement (the foundation already stands without it) |
|---|---|
| **ER-1** — deterministic entity resolution | Action already works via the validated **exact-id path + allowlist** (G-5; safe by construction). ER-1 improves NL→`entity_id` resolution and replaces a silent no-op write with **fail-closed + read-after-write** honesty. A robustness/honesty hardening of an already-functional, already-safe control surface — the **highest-priority** enhancement (§6 below). |
| **F-4 closeout** | The operational-memory layer is **implemented and validated** (digest generation + date-anchored retrieval, 2026-06-30). What remains is passive gate verification (≥7 accumulated nightly digests) + an operator-gated restic check — completion of an existing capability, not new capability. |
| **F-6 — Voice Quality** | The voice front door **works** (D-1; WM-6 voice leg PASS). F-6 upgrades the Whisper model, migrates off an unmaintained STT server (tech debt), and baselines latency — quality, not capability. |
| **WM-7 — extend World Model regions** | The World Model **architecture is complete and proven** on the home region. WM-7 extends coverage to infrastructure / self / projects — **Depth** (§9), not a missing foundation. |
| **Phase G — proactive intelligence** | Explicitly future (§9): "requires the awareness and memory layers to be stable first." It is the capability the foundation **exists to enable**, delivered conservatively (flag, do not act — AURORA_VISION §6). Not part of the foundation. |

## 6. Recommended execution order (next stage)

The enhancements above are sequenced so a hardened, trustworthy foundation comes before breadth:

1. **ER-1 — deterministic entity resolution** — the highest **operational-safety** priority: replace the silent no-op write (success reported when nothing happened, on a fire-risk device) with fail-closed + read-after-write honesty.
2. **F-4 closeout** — completes the **operational-memory** layer (verify the accumulated nightly digests; operator-gated restic check).
3. **F-6 — Voice Quality** — finishes the **user-facing operational quality** (Whisper upgrade, maintained STT path, latency baseline) before the architecture is expanded.
4. **WM-7 — extend World Model regions** — extends the World Model (infrastructure / self / projects) **on top of a hardened foundation**.
5. **Phase G — proactive intelligence** — the natural next generation once the prerequisites above are complete (delivered conservatively — flag, do not act).

---

## 7. Status & tag (recommendation only — not executed)

This document is prepared as the chapter closeout; **nothing is committed, pushed, or tagged.** Recommendation: after this document is committed and pushed, apply an **annotated** tag `aurora-v1.0-foundation` to that commit (see the accompanying review for the rationale and the alternative "wait" argument). Reconcile at the same time with the still-pending **WM-0 freeze tag** so tag policy is consistent.

---

*Reality wins: this milestone is claimed on closed gates and real-data evidence only. The named enhancements are real and, in ER-1's case, safety-relevant; they are sequenced in §6 above.*
