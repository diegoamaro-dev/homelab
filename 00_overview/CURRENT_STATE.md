CURRENT STATUS

Current phase:
Phase F — Operational Intelligence — **IN PROGRESS.** F-0, F-1, F-2 and **F-3 (Situational Awareness) COMPLETE — F-3 closed 2026-06-29 (F3.3): F-3a chat Filter (G-F3-1…7) and F-3b HA-voice awareness (G-F3-8) both validated.** The nightly signal pipeline is validated, `system_status` is wired to `qwen2.5`, the `aurora_context` Open WebUI Filter is active+global, and the HA voice prompt renders the nightly context via `input_text.aurora_voice_context`. **Most recent step: F-4 — Operational Digest + Memory Corpus — CLOSED 2026-07-27: all gates G-F4-01…09 + repro pass on real evidence (G-F4-05 reranked date-anchored 24/24 indexed digests; G-F4-06 deterministic same-night disclosure; G-F4-07 degraded night; G-F4-08 empirical restic restore-drill on snapshot `7715bf6a`, 24 digests recovered). No new engineering phase selected. Closeout `09_logs/2026-07-27_phaseF_F4_closeout.md`.** Prior: Phase E COMPLETE 2026-06-28 (E-0..E-6). **World Model architecture FROZEN 2026-07-01 (AD-21, `04_ai_system/world_model_architecture.md`) as Aurora's semantic baseline and the R-F5-A remedy; implementation is Phase WM (WM-1→WM-7); WM-1 `_schema/` foundation committed 2026-07-01 (`6e97c3fb`); WM-2 committed 2026-07-01 (`4c3e2a5d`, pushed); WM-3 loader (`_loader/`; `Parse→Resolve→Normalize→Validate→Emit`; backend-agnostic AST INV-WM3-A) implemented 2026-07-02 — real-data parity PASS (engine-equiv 32/32 + live `/api/states` match), committed + pushed (`8d653fea`, git gate closed); **WM-4 (evaluator cutover) implemented + validated 2026-07-13** — the `_evaluator/` engine (loader compiles / evaluator evaluates) consumes the compiled model, `bin/aurora-context` renders home awareness from it (INV-19), **`HOME_RULES` retired**, AD-20/INV-18 schema preserved (G-WM4-1…6 PASS; **G-WM4-6 CLOSED 2026-07-14** on the first unattended nightly cycle) — **committed + pushed (`476e0ae8`)**; WM-5 (consumer convergence) done 2026-07-14 — **committed + pushed (`b2b04670`)**; **WM-6 (close G-F5-04) done 2026-07-16 — G-F5-04 CLOSED / R-F5-A · F-5 CLOSED** (`09_logs/2026-07-16_WM6_G-F5-04_closeout.md`). Hashes are the post-sanitization canonical hashes (history rewritten + republished 2026-07-10; see `09_logs/2026-07-10_repo_history_sanitization_reconciliation.md`).**

**Phase ER-1 — Deterministic Entity Resolution — design FROZEN 2026-07-16 (operator-ratified), now Revision 4. ER-1.0, the Revision 2 amendment, ER-1.1, ER-1.2 and ER-1.3 are all committed + pushed** (defect record `c147e632` → architecture freeze `38eb8262` → Rev 2 amendment `3ebf59d1` → ER-1.1 aliases contract `f983a04f` → ER-1.2 loader `b0fded73` → ER-1.3 projection emitter `ed7a149c`); **G-ER-5 CLOSED 2026-07-17** on the first unattended 04:15 cycle after the artifact regeneration (`09_logs/2026-07-17_ER1_2_G-ER-5_operational_closeout.md`); **G-ER-6 producer half CLOSED** at ER-1.3 (`09_logs/2026-07-17_ER1_3_projection_applied.md`). **ER-1.4a (v0.1.0 baseline + `ha_get_state` v0.2.0 — the first cutover) implemented + validated 2026-07-17 — G-ER-7 read half PASS; G-ER-6 consumer half PASS on the read side (write side open at ER-1.4b)** (`09_logs/2026-07-17_ER1_4a_ha_get_state_applied.md`). **The read path resolves natural language as of ER-1.4a; the write path does not change until ER-1.4b.** Spec: `04_ai_system/entity_resolution_layer.md`; freeze log `09_logs/2026-07-16_ER1_freeze.md`; **Rev 2 amendment log `09_logs/2026-07-16_ER1_freeze_rev2.md`**; defect record `09_logs/2026-07-14_ER1_entity_resolution_finding.md`. ER-1 closes the natural-language → `entity_id` gap **and** makes writes honest: real audit evidence shows **13 unverified writes across 7 non-existent entity ids reported as successful** (`result_code:"ok"`; all 7 re-probed 2026-07-16 → HTTP 404). The read path is **not** defective. ER-1 **amends no frozen decision** (AD-21 §7 anticipates the entity registry; ER-1 implements it) and is **independent of Phase WM** — **not WM-5.5**. Key decisions: **D-ER-9** (no write-surface restriction — a valid `entity_id` follows the current path exactly as today; **D-12 remains the sole authorization authority**; any stronger restriction is a future architectural decision), **ER-1-C1** (mandatory after-only write verification — never claim success unless the resulting HA state was verified; *when* a POST is issued does not change), **D-ER-10** (closed expected-state map; all other services → `applied_unverified`), **D-ER-7** (`ARTIFACT_VERSION` stays 1 — a bump would silently degrade home awareness instead of failing loud). **Revision 2 (ratified 2026-07-16, committed + pushed `3ebf59d1`): D-ER-11** (aliases mirror the `binding` shape — single-signal → flat list, multi-signal → per-signal map, **no implicit primary signal**) and **D-ER-12** (an alias **may** equal **its own** entity identifier, **never** another's — validation check 12e); both surfaced while authoring the ER-1.1 alias sets, and both are naming/validation only — **D-12 remains the sole authorization authority (INV-17)**. **Revision 3 (ratified 2026-07-17 at ER-1.3): D-ER-13** — an aliased signal must bind `ha_entity` (check 12a; ratifies finding F-ER12-1 from ER-1.2), because a signal bound to `container`/`corpus`/`probe`/`signal` has no HA id to resolve to and its alias would be **dead**. Unreachable on the real tree (every bound signal binds `ha_entity`) — ratified so the rule states the constraint the registry **depends on**, not the one that happens to hold; naming/validation only (INV-17 untouched). Rev 3 also records the **G-ER-6 split** (producer half ER-1.3 / consumer half ER-1.4) and rewrites spec §9: projection freshness is **content-derived** via the host-side `emit-entity-projection --check`, never commit-derived (`PROJECT_RULES.md` → *Content Provenance over Repository Chronology*). **Revision 4 (ratified + applied 2026-07-17, before ER-1.4b): D-ER-14** — the step-4 audit observability field is **`registry_target`**, never `modelled` (ratifies F-ER14-1: the old name overstated what is checked — `sun.sun` is modelled yet unaliased, so not a registry target); applied while the field had **zero** occurrences in the real audit log, so no historical line carries the old name; `ha_get_state` → **v0.2.1** (patch) reinstalled, returns proven byte-identical over the 18-case corpus; naming/observability only — INV-17 / D-ER-9 untouched (`09_logs/2026-07-17_ER1_freeze_rev4.md`). **ER-1.4b (`ha_call_service` v0.2.0 — resolution + ER-1-C1) implemented + validated 2026-07-20 — the write cutover, committed + pushed `5b502c96`: Rule B (500 ms window) ratified from the pre-registered N=20 measurement; G-ER-2/3a/3b/4 + G-ER-7 write half + G-ER-6 consumer half (write side) all PASS; the 13 historical unverified writes can no longer be reported as successful (`09_logs/2026-07-20_ER1_4b_ha_call_service_applied.md`).** Gates G-ER-1…7; each sub-phase STOPs at the git gate.

Overall health:
Degraded — **with 34 open audit findings, one of which is currently live.** Backup
**retention grouping is fixed** (I-4, 2026-07-31; retention deliberately held at
`--dry-run`) and **holding across eighteen further unattended nights**, but **16/17
containers are running**: `zigbee2mqtt` exited again on **2026-08-17 at 13:12:24 CEST**
— the **third** C-1 recurrence — and there is still **no real-time monitoring or alerting
of any kind**; the outage was found by inspection seven hours later, not by monitoring
(**M-1** / **M-A**; evidence in `ROADMAP.md` → *C-1 recurrence 2026-08-17 13:12*).
Independently, the platform has reported `degraded` since **2026-08-01** for a *second*
reason — an empty, freshly-rotated audit log (see *Ingest service* below). **The LAN is now
the security boundary by decision** — S-1, ratified 2026-07-28: *a trusted transport, never
a substitute for service authentication* — but **four LAN-reachable listeners do not yet
meet that bar** (H-5, H-6, M-9, plus F-S1-1 / F-S1-2). See *Infrastructure audit —
2026-07-28* below.

Production:
Degraded — **16/17 containers running (verified 2026-08-17)**. `zigbee2mqtt` is `exited (2)`
since **2026-08-17 13:12:24 CEST**; both Zigbee entities are unavailable. **This is a new
outage, not the July one:** the container restarted automatically at the 2026-08-12 reboot,
ran healthily for five days, and then exited again today by the same C-1 mechanism —
coordinator USB disconnect, followed by Docker's single `unless-stopped` restart attempt
losing a **101 ms** race against udev recreating the `by-id` symlink. **Unlike 2026-07-28
there was no trigger** — zero USB enumerations preceded the disconnect. **The adapter is
present and free**; the container has deliberately not been restarted, pending a separate
operator-approved recovery. Evidence: `ROADMAP.md` → *C-1 recurrence 2026-08-17 13:12* and
`09_logs/2026-08-17_operational_reconciliation.md` (**M-1** / **M-A** and **S-9**).

Next milestone:
**Remediation Program E — backup lifecycle: I-5** (extend backup coverage, H-2). **I-4 is
COMPLETE 2026-07-31** — the restic grouping defect is fixed and Gate 8 closed on real
evidence (45 snapshots / **42 groups**, byte-identical path sets, parent detection restored,
zero removals, no locks). Retention stays `--dry-run`. Then I-6 / I-8 / S-8, and only then
S-10 — the single irreversible step in the whole roadmap. **The S-10 input now exists:** the
first would-remove report landed **2026-08-05** exactly as I-4 predicted and has grown to
**10 snapshots** by 2026-08-17, with **nothing removed** — see *Backups* below. **Note for
I-5 sequencing:** editing the `PATHS` array changes the recorded path set and therefore
**starts a new group**, which restarts that report from zero; the accrued trail is recorded
in `09_logs/2026-08-17_operational_reconciliation.md` §5 before it is superseded. **S-1 (LAN trust posture) is
DECIDED 2026-07-28** — S-2/S-3/S-4/S-5 are
unblocked and are now conformance actions against a written bar rather than open questions.
**S-7** (Health Aggregator) remains an open zero-cost decision and gates the monitoring
build. **F-6 / F6.1 continues independently**
and is not blocked by any of this, but F6.1 Step 7 currently has no live voice acceptance path
(S-11). Program A capture is done; convergence (M-B) waits on F6.1 closing.
**Phase ER-1 is CLOSED — no ER-1 engineering remains** (ER-1.5 reconciliation + closeout COMPLETE 2026-07-21, `09_logs/2026-07-21_ER1_5_closeout.md`). The **WM-era documentation-hygiene pass is COMPLETE 2026-07-21** — the deferred WM-4/WM-5 transient-status drift is cleared across the triad and `04_ai_system/world_model/README.md` (`09_logs/2026-07-21_WM_documentation_hygiene_closeout.md`). Standing: F-4 CLOSED 2026-07-27 (all gates pass; closeout `09_logs/2026-07-27_phaseF_F4_closeout.md`). No new engineering phase selected. ER-1.5 was the final ER-1 sub-phase. **ER-1.4b — `ha_call_service` v0.2.0 (resolution + ER-1-C1) — implemented + validated 2026-07-20, committed + pushed `5b502c96`** (`09_logs/2026-07-20_ER1_4b_ha_call_service_applied.md`): **the write path now verifies before it claims success.** Rule B (check immediately, then poll 100 ms within a 500 ms budget; else `applied_unverified`) was ratified from the pre-registered N=20 measurement on `switch.impresora_3d` (immediate read stale 20/20; state visible 52–159 ms; POST returns in ~1.6 ms). Gates all PASS — **G-ER-3b** (the 13 historical unverified writes across 7 non-existent ids now return `applied_unverified`, not a false `ok`), **G-ER-4** (real actuation of `switch.impresora_3d` via exact id **and** alias `impresora 3d` → `ok`+`verified` via the live read-back; baseline `off` restored), **G-ER-7 write half** (refusal/validation/`entity_not_found` + the HA-facing POST byte-identical to v0.1.0; success adds only `verified`/`state_after`), **G-ER-6 consumer half write side** (missing/corrupt projection ⇒ direct ids work as today, alias ⇒ `resolver_unavailable`, zero HA calls), **G-ER-2** determinism, **G-ER-5** unaffected (loader 43 + evaluator 36 green). Installed to `webui.db` (attached to `qwen2.5`); stored row confirmed via Open WebUI's own loader. Finding recorded: the installed v0.1.0 row was a pre-2026-07-10 snapshot (old audit_helper + `future Claude` comment) — method body byte-identical, so equivalence asserted on behaviour. **F-ER14-1 RESOLVED — D-ER-14 ratified + applied (freeze Rev 4, 2026-07-17)**: the audit field is **`registry_target`**; the rename landed at `ha_get_state` v0.2.1 before any real audit line carried the old name (pending item 10 closed; `09_logs/2026-07-17_ER1_freeze_rev4.md`). **The C1 read-back measurement protocol is PRE-REGISTERED** (`09_logs/2026-07-17_ER1_4b_c1_measurement_protocol.md`): N=20 samples on `switch.impresora_3d`, and the immediate-read vs bounded-retry choice is decided by predefined rules (A/B/C), never from the observed outcome — the protocol commits before the measurement runs. **ER-1.4a (v0.1.0 baseline + `ha_get_state` v0.2.0) implemented + validated 2026-07-17 — G-ER-7 read half PASS, G-ER-6 consumer half (read side) PASS** (log `09_logs/2026-07-17_ER1_4a_ha_get_state_applied.md`): the read path now resolves natural language — `toldo` → `cover.toldo`, `impresora 3d` → `switch.impresora_3d`, `Conexión a Internet` → `binary_sensor.rooter_estado_wan` — via the new inline-only `ai-stack/openwebui-tools/lib/entity_resolver.py` (D-ER-8 normalization **proven byte-identical** to `_loader/resolution.py` across 46 real + adversarial cases; all 33 authored aliases resolve). A canonical `entity_id` is **byte-identical to v0.1.0**, proven by a paired A/B run with entity volatility controlled; a non-id-shaped miss returns `unknown_entity` + ≤8 candidates with **zero HTTP calls**; a missing/corrupt projection leaves direct ids working **exactly as today** and answers `resolver_unavailable` on the alias path only (D-ER-9). Root cause #2 fixed (the `light.kitchen` docstring examples that taught English-style guesses at a device named `impresora_3d`). `bin/install_tool` generalised to multiple inline markers; `lib/audit_helper.py` gains an additive `extra` (spec §10 inventory corrected — implementation-inventory correction, **not** an architectural decision). **`ha_call_service` is now v0.2.0 (ER-1.4b, applied 2026-07-20).** Prior: **ER-1.3 (projection emitter) committed + pushed (`ed7a149c`)** (log `09_logs/2026-07-17_ER1_3_projection_applied.md`): the consumer-side `ai-stack/ingest/bin/emit-entity-projection` (emit + the canonical `--check` freshness mechanism; D-ER-5) derives the gitignored runtime projection `ai-stack/aurora/aurora-entities.json` — the artifact's `resolution` block **verbatim** + provenance, 33 aliases → 8 targets, **no authorization-adjacent field** (D-ER-9/INV-17), reaching the ER-1.4 resolver through the read-only `/opt/aurora` mount. **D-ER-13 ratified — freeze Revision 3** (an aliased signal must bind `ha_entity`, check 12a; ratifies F-ER12-1): unreachable on the real tree, `resolution` hash unmoved — **no behaviour change**. **G-ER-6 producer half CLOSED** (artifact missing/corrupt/no-`resolution` ⇒ fail loud, nothing written, last-good retained byte-identical; stale/absent ⇒ honest `--check`); **consumer half open (ER-1.4)**. **G-ER-1 untouched** — it closed 2026-07-16 on its Rev 2 condition and that closure stands; gate history is not rewritten. 43 loader + 36 evaluator green; **`LOADER_VERSION` → 0.2.1** (patch — validation contract only, no output change; **the live artifact keeps `loader_version` 0.2.0 because 0.2.0 is what generated it**, and ER-1.3 deliberately does not regenerate — a version stamp is provenance, never freshness); `ARTIFACT_VERSION` still 1; the artifact is **not** touched and the awareness path is unaffected **by construction** — ER-1.3 adds no new input to the nightly 04:15 cycle and creates no new operational gate. New permanent rule: `PROJECT_RULES.md` → **Content Provenance over Repository Chronology** (canonical content hashes are the freshness authority; commit hashes are traceability only, never freshness). Prior: **ER-1.2 (loader) committed + pushed (`b0fded73`)** (log `09_logs/2026-07-16_ER1_2_loader_applied.md`): D-ER-8 normalization + fail-loud check 12 (12a–12f) in the real loader + the additive `resolution` registry (33 aliases → 8 targets; **no authorization-adjacent field** — D-ER-9/INV-17); `LOADER_VERSION` → 0.2.0, **`ARTIFACT_VERSION` still 1** (D-ER-7); 42 loader + 36 evaluator tests green (the evaluator suite runs against the **regenerated real artifact**); artifact diff = additive `resolution` + provenance only. **G-ER-1 CLOSED · G-ER-2 loader half PASS · G-ER-5 CLOSED 2026-07-17** — the first unattended 04:15 cycle after the artifact regeneration consumed the 0.2.0 artifact and produced awareness **byte-equivalent to baseline** (`degraded` / `medium` / `{home: medium, infrastructure: ok}` / `[awning_left_extended, plant_water_warning]`); Home State `Degraded`, never `Unavailable`; zero `ArtifactError` (`09_logs/2026-07-17_ER1_2_G-ER-5_operational_closeout.md`). Prior: ER-1.1 aliases contract committed + pushed (`f983a04f`; `09_logs/2026-07-16_ER1_1_aliases_applied.md`). Then ER-1.4a/b (tools v0.2.0 + ER-1-C1) → ER-1.5 (closeout). See `00_overview/ROADMAP.md` → Phase ER-1. F-4 closeout DONE 2026-07-27 — all gates (G-F4-05 date-anchored, G-F4-06 same-night honesty, G-F4-07 degraded night, G-F4-08 empirical restic durability) PASS; F-4 CLOSED (`09_logs/2026-07-27_phaseF_F4_closeout.md`). Operational memory is the dedicated `ops_digests` collection (AD-14 — **not** `homelab_docs`). See `04_ai_system/phase_f_architecture.md` §9 → F-4. (F-5 Home Intelligence **CLOSED 2026-07-16 at WM-6** — G-F5-07 Layer A + F5.2 Layer B done 2026-06-30; **F5.3 executed 2026-07-01 — G-F5-03 PASS, G-F5-04 FAIL (real validation)** → **R-F5-A** (awareness-consumption gap) remedied by the World Model and closed at WM-6; F-6 Voice Quality is unblocked.) **World Model architecture FROZEN 2026-07-01 (AD-21); WM-1 (`_schema/` foundation) committed 2026-07-01 (`6e97c3fb`); WM-2 committed 2026-07-01 (`4c3e2a5d`, pushed); WM-3 (loader/parity) implemented 2026-07-02 — real-data parity PASS, committed + pushed (`8d653fea`, git gate closed; apply log `09_logs/2026-07-02_WM3_loader_applied.md`); WM-4 (evaluator cutover) implemented + validated 2026-07-13 — awareness renders from the compiled World Model via `world_model/_evaluator/` (INV-19), `HOME_RULES` retired, `home_model.md` → redirect, AD-20/INV-18 preserved (apply log `09_logs/2026-07-13_WM4_evaluator_cutover_applied.md`) — committed + pushed (`476e0ae8`); G-WM4-6 closed 2026-07-14 (first unattended cycle) — WM-4 complete. WM-5 (consumer convergence) implemented + validated 2026-07-14 (G-WM5-1…5 real-data PASS; §1.5 low-not-escalated proven; `system_status` v0.3.0 **installed to `webui.db` + verified on the running assistant 2026-07-14** — G-WM5-3), **committed + pushed (`b2b04670`)**; **WM-6 (reopen & close G-F5-04) COMPLETE 2026-07-16 — G-F5-04 CLOSED, PASS on real evidence (chat @ ai.amarolab.es + voice @ ha.amarolab.es via AURORA v1); R-F5-A CLOSED; F-5 CLOSED** (apply log `09_logs/2026-07-16_WM6_G-F5-04_closeout.md`; Run 1 aborted — wrong endpoint (HA Assist) — then corrected; findings F-LOCALE/F-VOICE-CONTRADICT/F-PLANT-FLAP/F-ASSIST-BLIND recorded). R-F5-A's remedy is the World Model. Freeze doc: `04_ai_system/world_model_architecture.md`; freeze log: `09_logs/2026-07-01_world_model_architecture_freeze.md`; roadmap: ROADMAP.md → Phase WM.**

Last completed:
**I-4 — restic backup grouping defect — COMPLETE 2026-07-31.** `SNAP_DIR` de-dated and
retention held at `--dry-run`; **G-I4-5 / G-I4-6 / G-I4-8 / G-I4-9 / G-I4-12 all closed on
real operational evidence at Gate 8** across two unattended nightly cycles (2026-07-29 and
2026-07-30) plus a root-verified repository read on 2026-07-31: 45 snapshots in **42 groups**
(the decisive number — unchanged from Gate 7), the three post-fix snapshots sharing a
byte-identical `paths[]`, `no parent snapshot found` gone, zero `remove` blocks, and **no
repository locks**. Prerequisite for all of Program E; **I-5 is next**. Closeout:
`09_logs/2026-07-31_I4_gate8_closeout.md` (predictions and Gate 7:
`09_logs/2026-07-28_issue-i4_backup-grouping_handoff.md` §8/§11). Prior:
**I-7 — triad reconciliation after the 2026-07-28 infrastructure audit.**
Prior: **I-1 / I-2 / I-3 — audit publication, H-4 hazard record, and Program A declarative
capture — COMPLETE 2026-07-28, committed + pushed `319b2c58`** (apply log
`09_logs/2026-07-28_I3_declarative_substrate_capture.md`): 14 services captured into
`03_services/` at 103/103 field parity, plus the new *Recovery Artifacts* rule in
`PROJECT_RULES.md`. No production change. Prior:
**ER-1.5 — Phase ER-1 reconciliation + closeout — COMPLETE 2026-07-21** (`09_logs/2026-07-21_ER1_5_closeout.md`): reconciled against the frozen spec (all §10 deliverables byte-clean at HEAD; invariants hold), G-ER-1…7 ledger closed on real evidence, deferred tool hashes stamped (§3), rollback + observability reviewed, triad reconciled. Documentation-only; no code/tag. Prior: **ER-1.4b — `ha_call_service` v0.2.0 (resolution + ER-1-C1, Rule B / 500 ms) implemented + validated 2026-07-20 — committed + pushed `5b502c96`** (`09_logs/2026-07-20_ER1_4b_ha_call_service_applied.md`): the write path now verifies before claiming success; G-ER-2/3a/3b/4 + G-ER-7 write half + G-ER-6 consumer half (write side) all PASS; v0.2.0 installed to `webui.db`. Prior: **ER-1 freeze Revision 4 — D-ER-14 (`modelled` → `registry_target`) ratified + applied 2026-07-17, plus the pre-registered C1 measurement protocol** (log `09_logs/2026-07-17_ER1_freeze_rev4.md`; protocol `09_logs/2026-07-17_ER1_4b_c1_measurement_protocol.md`; `ha_get_state` → v0.2.1; *tool hashes stamped at ER-1.5 closeout — `09_logs/2026-07-21_ER1_5_closeout.md` §3*). Prior: **ER-1.4a — the v0.1.0 baseline + `ha_get_state` v0.2.0 (the first cutover), implemented + validated 2026-07-17, committed + pushed (`3ad8779f`).** G-ER-7 read half PASS · G-ER-6 consumer half (read side) PASS; the read path resolves natural language, a canonical `entity_id` stays byte-identical to v0.1.0, and `ha_call_service` was then still at v0.1.0 (cut over to v0.2.0 at ER-1.4b, 2026-07-20). Log: `09_logs/2026-07-17_ER1_4a_ha_get_state_applied.md`. Prior: **ER-1.3** projection emitter + D-ER-13 / freeze Revision 3 — committed + pushed `ed7a149c`, 2026-07-17; **ER-1.2** loader `b0fded73` with G-ER-5 closed on real unattended evidence; **WM-6** (G-F5-04 / R-F5-A / F-5 closed) 2026-07-16.

Prior (Phase F): F-4 substrate + generator — F4.1 (`c524ed99`) + F4.2 (`919b8524`), 2026-06-30 — and **F4.3 implementation + reconciliation complete** (2026-06-30): the unattended 04:25 digest verified (`2026-06-30_ops_digest.md`); `ops_digests` retrieves the real 2026-06-29 digest top-1 (score 0.87); `generated_at` fidelity fix applied (generator fixed to AD-15; AD-15 unchanged). G-F4-01/02/03/04/09 PASS; G-F4-08 was config-verified then **empirically confirmed 2026-07-27** (restic restore-drill); **G-F4-05/06/07 PASS on real evidence** — **F-4 CLOSED 2026-07-27** (`09_logs/2026-07-27_phaseF_F4_closeout.md`). F4.3 closeout: `09_logs/2026-06-30_phaseF_F4_3_closeout.md`. Prior: F-3 — Situational Awareness (closed 2026-06-29, F3.3); F-2 (2026-06-29, F2-9).

Blocking issues:
None for production/platform. **R-F5-A and F-5 CLOSED at WM-6 (2026-07-16)** — G-F5-04 PASS on real evidence (chat + voice); closeout `09_logs/2026-07-16_WM6_G-F5-04_closeout.md`. Historical (now resolved): F-5 completion was blocked by R-F5-A (awareness-consumption gap — the model routed status queries to home-blind tools instead of the injected Home State; `system_status` was home-blind). **Its remedy architecture is now FROZEN as the World Model (AD-21, `04_ai_system/world_model_architecture.md`); R-F5-A / F-5 were carried under Phase WM (WM-1 committed `6e97c3fb`; WM-2 committed `4c3e2a5d`; WM-3 loader implemented 2026-07-02, parity PASS — committed + pushed `8d653fea`, git gate closed; WM-4 evaluator cutover implemented + validated 2026-07-13 — `HOME_RULES` retired, awareness renders from the compiled model — committed + pushed `476e0ae8`) and closed at WM-6 (2026-07-16).** See `09_logs/2026-07-01_phaseF_F5_3_applied.md` and `09_logs/2026-07-01_world_model_architecture_freeze.md`.
# CURRENT_STATE

Related documents:

- AMAROLAB_HANDOFF.md
- ROADMAP.md
- INITIAL_SYSTEM_STATUS.md (historical)

Last updated: 2026-08-17 (**Operational reconciliation after seventeen unattended days.**
Documentation only; no production change. Five facts recorded — **(1)** the host rebooted
**2026-08-12 09:28 CEST** (previous boot ended 09:24:12 with no shutdown sequence; cause not
established); **(2)** `zigbee2mqtt` restarted automatically at that reboot, ran five days, and
**exited again 2026-08-17 13:12:24 CEST** — the **third** C-1 recurrence, this time with **no
trigger at all** (zero USB enumerations preceded it), Docker's single restart attempt losing a
**101 ms** race against udev; the container is **deliberately not restarted** and recovery is a
separate approved intervention; **(3)** **I-4 holds** across eighteen further nights — unbroken
nightly snapshots 2026-07-31→2026-08-17, parent detection working, installed script sha256
unchanged; **(4)** the **S-10 input exists** — first would-remove report **2026-08-05** (as
predicted), grown to **10 snapshots** by 2026-08-17, **13 reports, zero deletions**, and the
D-1.5 anchor `63c072f4` has appeared in **none** of them, protected only by group shape (**I-6
still required**); **(5)** the platform has read `degraded` since **2026-08-01** for a second,
unrelated reason — `amarolab-audit.log` rotated empty on 2026-08-01 and no tool call has written
to it since, so `check-audit-liveness` reports `missing`. Also confirmed: the F6.1 baseline
survived the reboot **without container recreation** (D-F6-1 holds; only `StartedAt` moved).
**Nothing was fixed** — S-9, M-1/M-A, S-10, I-6 all remain Open; **I-5 remains the next
milestone**. Record: `09_logs/2026-08-17_operational_reconciliation.md`. Prior —
**2026-07-31: I-4 — restic backup grouping defect — COMPLETE.** Gate 8 closed on
real evidence: **G-I4-5 / G-I4-6 / G-I4-8 / G-I4-9 / G-I4-12 all PASS** across two unattended
nightly cycles plus a root-verified repository read — 45 snapshots in **42 groups**,
byte-identical `paths[]` across the three post-fix snapshots, parent detection restored, zero
`remove` blocks, no repository locks. **Retention stays `--dry-run`; no snapshot can be
deleted.** Program E advances to **I-5**. Also reconciled: production is **degraded at
16/17** — `zigbee2mqtt` down since 2026-07-28 15:52 (shared-hub USB reset + Docker/udev
restart race), recorded as evidence for **M-1 / M-A** and **S-9** in `ROADMAP.md`; **not
restarted**. New open observation: `63c072f4` names a parent that no longer exists in the
repository. Prior — **S-1 — LAN trust posture DECIDED.** The LAN is a **trusted
transport**, never a substitute for service authentication; every LAN-reachable service must
authenticate, be explicitly justified, or remain closed. Recorded in
`06_security/security_posture.md`; decision record
`09_logs/2026-07-28_S1_lan_trust_posture_decision.md`. S-2/S-3/S-4/S-5 unblocked; four
listeners non-conforming (H-5, H-6, M-9, F-S1-1, F-S1-2); segmentation is a decided non-goal
at current scale; new tracking item **I-9** for architecture-document drift. No production
change. Prior — **I-7 — triad reconciliation after the 2026-07-28 infrastructure
audit.** The audit and its remediation roadmap are published in `09_logs/`; P0 + I-1 + I-2 +
I-3 are complete (`319b2c58`); Program A capture is closed and the *Recovery Artifacts*
doctrine is active in `PROJECT_RULES.md`. Drift closed against measured reality: system prompt
5 138 chars, `system_status` v0.3.0, voice-exposure ACL **zero**-exposed, `aurora-piper` runs
`es_ES-sharvard-medium`, Qdrant counts + the two Open WebUI-internal collections, 10 Zigbee
devices, F-ER13-1 resolved. Backups reclassified — **backup PASS, retention DEFECTIVE**.
Prior — **Voice Lab — Round 1 native TTS casting COMPLETE (repo-external)** — Kokoro `ef_dora` = native TTS reference candidate (~70% blind), Piper remains production (no migration), Round 2 designed/not-started, next gate = Aurora voice identity (`09_logs/2026-07-27_voice_lab_round1.md`). Prior — Phase ER-1 — **ER-1.5 reconciliation + closeout: Phase ER-1 COMPLETE**; ER-1.4b `ha_call_service` v0.2.0 + ER-1-C1 committed + pushed `5b502c96`; the write path now verifies before claiming success; closeout log `09_logs/2026-07-21_ER1_5_closeout.md`)

---

## Scope

This document captures the current state of the
**AMAROLAB** ecosystem and the build state of
**AURORA** (the AMAROLAB Personal AI Assistant).

**Guardian Cloud** is an independent project currently
hosted on AMAROLAB infrastructure; its internal state
is tracked by the Guardian Cloud project, not in this
document.

---

## AURORA — phase status

### Phase B — Tool layer

Status: Closed

Tools delivered and validated end-to-end against `qwen2.5:7b-instruct`:

- time_now
- rag_search
- audit_search

Closeout reference:
[`09_logs/2026-06-16_phaseB_closeout.md`](../09_logs/2026-06-16_phaseB_closeout.md).

### Phase C — Home Assistant integration

Status: **Completed** (2026-06-17 — Gate G-5)

Read path:

- `ha_get_state` installed in `webui.db.tool`
- `ha_get_state` attached to `qwen2.5` via `meta.toolIds`
- Real Home Assistant read validated against `sun.sun`
  (`result_code = "ok"`, `state = "above_horizon"`)
- Closeout:
  [`09_logs/2026-06-17_phaseC_ha_get_state_real_validation.md`](../09_logs/2026-06-17_phaseC_ha_get_state_real_validation.md)

Write path:

- `ha_call_service` installed in `webui.db.tool`
- `ha_call_service` attached to `qwen2.5` via `meta.toolIds`
- Tool-level refusal path validated against the
  out-of-allowlist canonical probe `recorder.purge`
  (`result_code = "refused"`, no HA call issued)
- Refusal closeout:
  [`09_logs/2026-06-17_phaseC_refusal_validation_applied.md`](../09_logs/2026-06-17_phaseC_refusal_validation_applied.md)
- **Gate G-5 — first real happy path executed against
  `switch.impresora_3d` (Sonoff S60ZBTPF). Sequence
  pre-read (`off`) → `turn_on` → verify (`on`) →
  `turn_off` → restore-verify (`off`). All 5 audit
  lines: `allowed=true`, `result_code="ok"`. HA
  observed both state transitions via Z2M MQTT
  round-trip. Plug restored to baseline `off`.**
- Gate G-5 closeout:
  [`09_logs/2026-06-17_phaseC_gate_g5_applied.md`](../09_logs/2026-06-17_phaseC_gate_g5_applied.md)
- Phase C closeout:
  [`09_logs/2026-06-17_phaseC_closeout.md`](../09_logs/2026-06-17_phaseC_closeout.md)

Allowlist (D-12) is enforced at the Tool boundary.

Denied domains include `homeassistant.*`, `hassio.*`,
`recorder.*`.

### Phase D — Voice

Status: **Phase D-1 closed** (2026-06-18 — D-1.9
closeout). Aurora v1 voice pipeline operational on both
front doors. All six Phase D-1 gates (G-D1 through G-D6)
landed with dated apply logs.

#### D-1 sub-step status

| Step | Description | Status | Apply log |
|---|---|---|---|
| D-1.1 | Documentation skeleton | Closed | (planning artefact, no apply log) |
| **D-1.2** | Whisper standup (`aurora-whisper`, G-D1 Wyoming half) | **Closed (2026-06-17)** | [`09_logs/2026-06-17_phaseD_whisper_installed.md`](../09_logs/2026-06-17_phaseD_whisper_installed.md) |
| **D-1.3** | Piper standup (`aurora-piper`, G-D2 Wyoming half) | **Closed (2026-06-17)** | [`09_logs/2026-06-17_phaseD_piper_installed.md`](../09_logs/2026-06-17_phaseD_piper_installed.md) |
| **D-1.4** | openWakeWord standup (`aurora-wakeword`, G-D3 container/probe half) | **Closed (2026-06-17)** | [`09_logs/2026-06-17_phaseD_wakeword_installed.md`](../09_logs/2026-06-17_phaseD_wakeword_installed.md) |
| **D-1.5** | AURORA v1 Assist pipeline + voice canary + voice-exposure lockdown (G-D3 HA-UI half) | **Closed (2026-06-17)** | [`09_logs/2026-06-17_phaseD_voice_pipeline.md`](../09_logs/2026-06-17_phaseD_voice_pipeline.md) |
| HA reverse-proxy trust patch | `configuration.yaml` `http.trusted_proxies` + `external_url`; unblocks Secure Context | Closed (2026-06-17) | [`09_logs/2026-06-17_phaseD_ha_trusted_proxies_applied.md`](../09_logs/2026-06-17_phaseD_ha_trusted_proxies_applied.md) |
| **G-D4** | Voice canary Read → Write → Verify → Restore through `AURORA v1` from `https://ha.amarolab.es` | **PASSED (2026-06-17)** | [`09_logs/2026-06-17_phaseD_gate_gd4_applied.md`](../09_logs/2026-06-17_phaseD_gate_gd4_applied.md) |
| **D-1.6 / G-D5** | Real-device voice round-trip against `switch.impresora_3d` (Sonoff S60ZBTPF via Mosquitto + Z2M); voice Write + voice Restore; baseline `off` restored | **Closed / PASSED (2026-06-18)** | [`09_logs/2026-06-18_phaseD_gate_gd5_applied.md`](../09_logs/2026-06-18_phaseD_gate_gd5_applied.md) |
| **D-1.7** | Open WebUI Audio integration: `aurora-whisper-http` + `aurora-piper-http` (OpenAI-API-compatible shims), `webui.db.audio.*` patched, voice on `https://ai.amarolab.es`; closes G-D1 HTTP-shim half + G-D2 HTTP-shim half + C-D-07 + C-D-09 | **Closed (2026-06-18)** | [`09_logs/2026-06-18_phaseD_openwebui_audio_applied.md`](../09_logs/2026-06-18_phaseD_openwebui_audio_applied.md) |
| **D-1.8 / G-D6** | Failure-mode rehearsal (Whisper down §7.1, Piper down §7.2, Ollama unreachable §7.3); one acceptance partial on HA TTS-failure log granularity (functional behaviour PASS); canary baseline restored; printer untouched | **Closed / PASSED (2026-06-18)** | [`09_logs/2026-06-18_phaseD_gate_gd6_applied.md`](../09_logs/2026-06-18_phaseD_gate_gd6_applied.md) |
| **D-1.9** | Phase D-1 closeout — overview-triad amendment + closeout log | **Closed (2026-06-18)** | [`09_logs/2026-06-18_phaseD1_closeout.md`](../09_logs/2026-06-18_phaseD1_closeout.md) |

#### Operational surface

Aurora v1 voice is reachable on both front doors:

- **Home Assistant voice** — `https://ha.amarolab.es`
  (Assist pipeline `AURORA v1`, push-to-talk,
  Wyoming chain: `aurora-whisper:10300` →
  `qwen2.5:7b-instruct` on `ollama:11434` →
  `aurora-piper:10200`). Voice-exposure ACL: only
  `input_boolean.aurora_voice_canary`.
- **Open WebUI voice** — `https://ai.amarolab.es`
  (browser mic, OpenAI-API-compatible HTTP shims:
  `aurora-whisper-http:8000` → `qwen2.5:7b-instruct`
  → `aurora-piper-http:8000` with
  `es_ES-sharvard-medium` speaker F). Default TTS
  auto-playback **off** per C-D-07 (Open WebUI 0.8.10
  has no backend auto-play; the shipped per-user
  default is off).

#### Voice safety story (G-D6)

- **Whisper down** — STT fails closed; HA Assist
  surfaces "speech-to-text failed"; no entity state
  change; no conversation-agent call.
- **Piper down** — intent still lands (canary
  toggles) but reply is audibly silent (TTS path is
  the only break); UI banner indicates a silent
  failure.
- **Ollama unreachable** — clean conversation-agent
  error within seconds; no partial action; STT path
  still works (transcripts captured).

All three scenarios end with the canary back to `off`
baseline and `switch.impresora_3d` untouched
(voice-exposure stayed `false` throughout G-D6).

#### Carried follow-ups (post-Phase-D-1)

| Item | Note |
|---|---|
| LLM 6 tok/s ceiling on UM790 CPU | Deferred to RTX 5070 AI-node work (see [`04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md`](../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md)). Voice-stack architecture is GPU-ready; only the `ollama` endpoint target changes. |
| STT fidelity | `base-int8` produces sub-canonical Spanish on short utterances. Model-size bump (`small` or `medium-int8`) candidate. |
| HA voice-pipeline intent-matching variability | `qwen2.5` occasionally fails to resolve voice canary aliases via the WS pipeline; REST `/api/conversation/process` against the same `agent_id` resolves the same phrasing reliably. Tracked as `HA-VOICE-001`. |
| HA TTS-failure log granularity | HA Assist surfaces TTS failures only on the WS `assist_pipeline/pipeline_debug` stream and the UI banner, not on the INFO-level core log. Documented partial on G-D6 §7.2. |
| Streaming TTS in Open WebUI | Open WebUI does not stream STT/TTS today; first-token wait dominates perceived latency. |
| Open WebUI system prompt size | 3 342 chars / 822 tokens → 16.9 s cold-cache prompt eval per new conversation. Trim candidate, paired with RAG audit. |
| `ai.amarolab.es` was already bound in D-1.7 | Operator action remaining: ensure DNS + Cloudflare ingress posture stays current. |
| `cloudflared-amarolab` standalone apply log | Deployment validated through D-1.5 / D-1.7 / G-D6 but no dedicated standalone apply log yet. |
| DNS / architecture doc amendments | [`02_infrastructure/cloudflare/amarolab_dns_architecture.md`](../02_infrastructure/cloudflare/amarolab_dns_architecture.md) and [`02_infrastructure/cloudflare/cloudflared_audit_2026-06-17.md`](../02_infrastructure/cloudflare/cloudflared_audit_2026-06-17.md) still describe the original "attach existing tunnel" plan; the **separate** `amarolab` tunnel + container shipped instead. |
| R-D-13 | Migrate the Open WebUI STT HTTP shim away from the unmaintained `fedirz/faster-whisper-server`. Post-Phase-D maintenance. |
| R-01 | Cloudflare Tunnel token rotation (existing Guardian-Cloud tunnel). Independent of Phase D. |

### Phase RTX-1 — Torre GPU node bring-up

Status: **Phase RTX-1 CLOSED. RTX-1.6 complete (2026-06-27)
— both UM790 front doors (Open WebUI chat + Home Assistant
voice/LLM) now consume Torre's GPU Ollama through the
`ollama-proxy` (Torre primary + UM790 CPU fallback). RTX-1.5
(headless NSSM service) and RTX-1.4 (Tailscale-only) remain
in force. The UM790 stays the 24/7 node and still serves its
own CPU Ollama as the always-on fallback.**

**Torre** (Windows 11 Pro + RTX 5070, 12 GB VRAM;
Tailscale `100.91.154.124` / LAN `192.168.178.21`) is
the on-demand GPU compute node anticipated by
[`04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md`](../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md).
`qwen2.5:7b-instruct` runs on the RTX 5070 at
**105.3 tok/s** (3-pass 105.5 / 105.5 / 104.9; model on
`D:\ai\ollama\models`, 29/29 layers on GPU) — **≈ 17.6×**
the ~6 tok/s UM790 CPU baseline. As of RTX-1.6 the front
doors consume this GPU path via the `ollama-proxy`
(measured **101.3 tok/s** end-to-end through the proxy; HA
conversation 24.1 s CPU → 3.9 s Torre). No service was
*moved* to Torre; the UM790 remains the 24/7 node and the
CPU fallback.

| Step | Description | Status |
|---|---|---|
| RTX-1.0 | Read-only post-format workstation audit | Done |
| RTX-1.1 | Install Ollama; pre-stage `D:\ai\ollama\models` | Done |
| RTX-1.2 | GPU validation (pull, placement, VRAM, benchmark) | Done |
| RTX-1.3 | Storage remediation (model store C: → D:) | Done |
| RTX-1.4 | Secure remote exposure (OLLAMA_HOST + firewall, Tailscale-only) | **Complete (2026-06-19)** |
| RTX-1.5 | Headless persistence (Windows service) | **Complete (2026-06-27)** |
| RTX-1.6 | Security delta doc + UM790 endpoint swap (failover proxy) | **Complete (2026-06-27)** |

RTX-1.6 delivered (all prerequisites resolved):

- ~~Loopback bind / no `OLLAMA_HOST` / no firewall scope /
  no headless service~~ → **RESOLVED**: RTX-1.4
  (`OLLAMA_HOST=0.0.0.0:11434`, host-scoped /32 firewall
  allowlist, Tailscale-only) + RTX-1.5 (headless NSSM
  service; persists across logoff/reboot).
- ~~Security delta doc `06_security/rtx_node_security.md`~~
  → **created + approved (RTX-1.6 Step 1, 2026-06-27)**.
- ~~UM790 endpoint swap~~ → **DONE**: `ollama-proxy`
  ([`03_services/ollama-proxy/`](../03_services/ollama-proxy/))
  fronts Torre (primary) + UM790 CPU (fallback); Open WebUI
  → `ollama-proxy:11434`, Home Assistant → `127.0.0.1:11435`.
  Apply log:
  [`09_logs/2026-06-27_phaseRTX1_6_endpoint_swap_applied.md`](../09_logs/2026-06-27_phaseRTX1_6_endpoint_swap_applied.md).
- VRAM-headroom discipline: Torre must run lean/headless
  (lesson L-RTX-2) — unchanged.

Validation summary:
[`04_ai_system/amarolab-v1/phase-rtx/RTX1_validation_summary.md`](../04_ai_system/amarolab-v1/phase-rtx/RTX1_validation_summary.md).
Apply logs:
[`09_logs/2026-06-18_phaseRTX1_local_validation.md`](../09_logs/2026-06-18_phaseRTX1_local_validation.md) (local validation) ·
[`09_logs/2026-06-19_phaseRTX1_5_headless_service.md`](../09_logs/2026-06-19_phaseRTX1_5_headless_service.md) (RTX-1.5 service) ·
[`09_logs/2026-06-27_rtx1_5_continuation_handoff.md`](../09_logs/2026-06-27_rtx1_5_continuation_handoff.md) (RTX-1.5 validation/closeout).
Architecture amendment (DRAFT — merged at RTX-1.6):
[`01_architecture/amarolab_architecture_rtx_amendment_DRAFT.md`](../01_architecture/amarolab_architecture_rtx_amendment_DRAFT.md).

### Phase F — Operational Intelligence

Status: **F-0, F-1, F-2, F-3 COMPLETE. F-3 closed 2026-06-29 (F3.3). F-4 —
Operational Digest + Memory Corpus — CLOSED 2026-07-27: all gates G-F4-01…09 + repro
pass on real evidence (G-F4-05 reranked date-anchored 24/24 indexed; G-F4-06
deterministic same-night disclosure; G-F4-07 degraded night; G-F4-08 empirical restic
restore-drill). Closeout `09_logs/2026-07-27_phaseF_F4_closeout.md`.**

Phase F shifts Aurora from reactive to aware. Architecture:
[`04_ai_system/phase_f_architecture.md`](../04_ai_system/phase_f_architecture.md).

- **F-0 — Behavioral audit** (2026-06-28). Baseline 4/10; 8 AF findings.
  Report: [`09_logs/2026-06-28_phaseF_F0_audit_report.md`](../09_logs/2026-06-28_phaseF_F0_audit_report.md).
- **F-1 — System Prompt Redesign** (2026-06-28). F-1 prompt installed
  (3 389 chars / ~485 tokens incl. the F2-9 `system_status` addition);
  domain-based routing; knowledge-layer corpus split (`homelab_docs` /
  `knowledge_history`). Platform finding G-F1-01 raised here. Log:
  [`09_logs/2026-06-28_phaseF_F1_system_prompt_installed.md`](../09_logs/2026-06-28_phaseF_F1_system_prompt_installed.md).
- **F-2 — Signal Layer + Context Generation** (closed 2026-06-29, F2-9).
  `bin/backup-probe` (03:30 → `backup_status.json`), `bin/container-probe`
  (04:00 → `container_status.json`) and `bin/aurora-context` (04:15 →
  `ai-stack/aurora/aurora-context.{json,md,voice}`), scheduled by
  `/etc/cron.d/aurora-signals`. `ai-stack/aurora/` is bind-mounted
  read-only into `openwebui` at `/opt/aurora`. The `system_status` Open
  WebUI tool (v0.2.0) reads that context + a live Torre probe and is wired
  to `qwen2.5`. First unattended nightly cycle validated 2026-06-29;
  G-F1-01 (chat-level tool firing) passed across all layers including the
  browser UI; `overall_status = ok`. Closeout:
  [`09_logs/2026-06-29_phaseF_F2_9_closeout.md`](../09_logs/2026-06-29_phaseF_F2_9_closeout.md).
- **F-3 — Situational Awareness** (closed 2026-06-29, F3.3). Split into
  F-3a (chat) + F-3b (voice) per AD-08.
  - **F-3a — Open WebUI Awareness Filter** (F3.1): committed Filter
    [`ai-stack/openwebui-tools/filters/aurora_context.py`](../ai-stack/openwebui-tools/filters/aurora_context.py)
    installed via `install_function`, **active + global** in `webui.db`;
    injects `aurora-context.md` from `/opt/aurora` on message 1 (freshness off
    the JSON; ≤26h graduated/fallback). All 7 gates G-F3-1…G-F3-7 pass — G-F3-1
    closed after an operator-approved `# Context` precedence directive in
    `params.system` + an `openwebui` reload. Apply log:
    [`09_logs/2026-06-29_phaseF_F3_1_applied.md`](../09_logs/2026-06-29_phaseF_F3_1_applied.md).
  - **F-3b — HA Voice Awareness Refresh** (F3.2): HA helper
    `input_text.aurora_voice_context` (max 255) + Jinja2
    `{{ states('input_text.aurora_voice_context') }}` appended to the Ollama
    voice prompt; `bin/push-voice-context` writes the nightly
    `aurora-context-voice.txt` into the helper via HA REST `input_text/set_value`
    at 04:20. G-F3-8 pass. Apply log:
    [`09_logs/2026-06-29_phaseF_F3_2_applied.md`](../09_logs/2026-06-29_phaseF_F3_2_applied.md).
  - Closeout:
    [`09_logs/2026-06-29_phaseF_F3_closeout.md`](../09_logs/2026-06-29_phaseF_F3_closeout.md).

- **F-4 — Operational Digest + Memory Corpus** (F4.1+F4.2 done + committed
  2026-06-30; F4.3 implementation + reconciliation complete 2026-06-30). `bin/generate-digest` writes a dated digest
  to `09_ops/runtime/` at **04:25**, indexed into the dedicated `ops_digests` Qdrant
  collection (384/Cosine — AD-14, **not** `homelab_docs`) on the next 02:30 sync (~22h
  lag, AD-04). Unattended 04:25 run verified (`2026-06-30_ops_digest.md`); real
  retrieval of the `2026-06-29` digest top-1 (0.87). `generated_at` fidelity fix applied
  (AD-15). Gates G-F4-05 (≥7 digests), G-F4-06 (same-night honesty), G-F4-07 (degraded
  night) **PASS on real operational evidence 2026-07-27** (G-F4-05 reranked date-anchored
  24/24 indexed digests; G-F4-06 deterministic same-night disclosure; G-F4-07 degraded
  night); G-F4-01/02/03/04/09 PASS; **G-F4-08 PASS** (empirical restic restore-drill,
  snapshot `7715bf6a`, 24 digests recovered). **F-4 CLOSED 2026-07-27.** Closeout:
  [`09_logs/2026-07-27_phaseF_F4_closeout.md`](../09_logs/2026-07-27_phaseF_F4_closeout.md).

Generated runtime artifacts (`ai-stack/aurora/`, signal JSON, `09_ops/runtime/`
digests) are gitignored. **F-5 Home Intelligence — CLOSED 2026-07-16 (at WM-6):** G-F5-07 Layer A
(static `# Home` prompt frame) implemented 2026-06-30
([`09_logs/2026-06-30_phaseF_F5_G-F5-07_applied.md`](../09_logs/2026-06-30_phaseF_F5_G-F5-07_applied.md));
**F5.2 Layer B** (`bin/aurora-context` reads HA `/api/states`, detects home anomalies per
`home_model.md`, populates `home.anomalies[]` + renders the `Home State:` block — Healthy/
Degraded/Unavailable) implemented + validated on real data 2026-06-30, G-F5-02/05/06 ✓
([`09_logs/2026-06-30_phaseF_F5_2_applied.md`](../09_logs/2026-06-30_phaseF_F5_2_applied.md)).
**F5.3 executed 2026-07-01: G-F5-03 PASS, G-F5-04 FAIL (real validation)** — the F-3a Filter
injects the Degraded `Home State` correctly, but the model routes status questions to tools
(`system_status`, which is home-blind) instead of the injected block; logged as **R-F5-A**
(awareness-consumption gap), **remedied by the World Model (WM-4/WM-5) and closed at WM-6 (2026-07-16)**; no fix/redesign in F-5 itself.
Apply log: [`09_logs/2026-07-01_phaseF_F5_3_applied.md`](../09_logs/2026-07-01_phaseF_F5_3_applied.md).
Optional `cover` G-F5-08 not attempted. F-6 Voice Quality
is unblocked.

---

## AI stack

### Open WebUI

Status: Healthy

Primary tool-calling model:

- id: `qwen2.5:7b-instruct`
- `base_model_id`: **NULL** (D-35 preserved)
- `meta.toolIds`:
  `["time_now","rag_search","audit_search","ha_get_state","ha_call_service","system_status"]`
- `params.system`: **F-1 system prompt + `# Home` Layer A frame** (**5 138 chars**,
  measured live 2026-07-28 at I-7; the previously recorded 4 478 was stale — L-1;
  installed 2026-06-28 F-1, `system_status` added 2026-06-29 F2-9, `# Context`
  precedence directive added 2026-06-29 F3.1, static `# Home` frame added
  2026-06-30 G-F5-07 Layer A). Domain-based routing; all 6 tools described; the
  `# Home` section (after `# Context`) names the home objects/baselines and how to
  read the dynamic `Home State:` block (Layer B / F5.2 — rendered by `bin/aurora-context`,
  implemented 2026-06-30). No
  stale phase references.
- **`aurora_context` Filter (F3.1):** Open WebUI Function (type `filter`),
  **active + global** in `webui.db.function`. Injects `aurora-context.md` from
  `/opt/aurora` on message 1 (situational awareness, no tool call). Source:
  [`ai-stack/openwebui-tools/filters/aurora_context.py`](../ai-stack/openwebui-tools/filters/aurora_context.py).
- **Runtime state:** `base_model_id` / `meta.toolIds` / `params.system` (and the
  `aurora_context` filter row) live in `webui.db` (not git). Reproduction + recovery procedure:
  [`04_ai_system/openwebui_model_runtime_state.md`](../04_ai_system/openwebui_model_runtime_state.md).

Tools registered in `webui.db.tool`:

- time_now
- rag_search
- audit_search
- `ha_get_state` (**v0.2.1** — read cutover at ER-1.4a 2026-07-17;
  0.2.1 = the D-ER-14 audit-field rename at freeze Rev 4, behaviour
  unchanged): resolves natural language to real entity ids via the
  ER-1.3 projection (`/opt/aurora/aurora-entities.json`). A canonical
  `entity_id` passes through to HA exactly as at v0.1.0 (D-ER-9); a
  non-id-shaped miss returns `unknown_entity` + candidates with no HA
  call. Audit stamps `registry_target` (observability only). **Naming
  only — never authorization: D-12 remains the sole authority (INV-17).**
- `ha_call_service` (**v0.2.0** — write cutover at ER-1.4b 2026-07-20):
  resolves natural language to real entity ids (same ladder as
  `ha_get_state`) and runs **ER-1-C1 after-only verification** — after the
  POST it reads `/api/states/<id>` back (Rule B: immediately, then poll
  100 ms within a 500 ms budget) and claims `ok`+`verified` only when the
  D-ER-10 expected state is confirmed, else honest `applied_unverified`. A
  canonical `entity_id` reaches HA byte-identically to v0.1.0 (D-ER-9); the
  POST is unchanged (§3.1). **Never authorization — D-12 remains sole
  authority (INV-17).**
- `system_status` (**v0.3.0**, verified in `webui.db` 2026-07-28) — Aurora
  operational status; attached to `qwen2.5` (F2-9) and to the legacy `llama3*`
  rows. **Provenance debt (M-3, open):** the D-23 canonical path
  `ai-stack/openwebui-tools/tools/system_status.py` **does not exist**. The tracked
  source is `ai-stack/ingest/docs/system_status_tool.py`, and a stale untracked-value
  duplicate remains at `ai-stack/openwebui-tools/tmp/system_status.dumped.py`.
  The installed tool is correct and working; this is provenance only
- legacy Jarvis tools (`docker_containers`, `docker_logs`) —
  scoped to `llama3*` rows only per D-20

Audio surface (D-1.7):

- `audio.stt.engine` = `openai`,
  `audio.stt.openai.api_base_url` =
  `http://aurora-whisper-http:8000/v1`,
  model `Systran/faster-whisper-base`.
- `audio.tts.engine` = `openai`,
  `audio.tts.openai.api_base_url` =
  `http://aurora-piper-http:8000/v1`, model `tts-1`,
  voice `alloy` (mapped to `es_ES-sharvard-medium`
  speaker F by the Amarolab voice mapping in
  `/srv/homelab/data/openedai-speech/voice_to_speaker.yaml`).
- Auto-playback default **off** (C-D-07 closed).

### Ollama

Status: Operational

`qwen2.5:7b-instruct` is shared by **two independent
integrations**:

- The Open WebUI chat path (`webui.db.tool` + `meta.toolIds`).
- The Home Assistant Ollama integration backing the
  `AURORA v1` Assist pipeline conversation agent.

A restart on either side does not disturb the other.

As of **RTX-1.6** both integrations target the
**`ollama-proxy`** instead of a single Ollama:

- Open WebUI → `http://ollama-proxy:11434` (docker network).
- Home Assistant → `http://127.0.0.1:11435` (loopback).

The proxy routes to **Torre's GPU Ollama** (`100.91.154.124:11434`,
~101 tok/s end-to-end, primary) and falls back automatically
to the **UM790 CPU Ollama** (`ollama:11434`, ~6 tok/s) when
Torre is unreachable. The UM790 CPU Ollama (v0.17.7) and
Torre (v0.30.10) are distinct instances; the UM790 remains
the always-on fallback. Proxy config:
[`03_services/ollama-proxy/`](../03_services/ollama-proxy/).

### ollama-proxy

Status: Operational (added RTX-1.6, 2026-06-27)

- Image: `nginx:alpine`; container `ollama-proxy` on
  `ai-local_default`; published `127.0.0.1:11435` (loopback
  only, for the host-network Home Assistant).
- Failover front end for the AURORA ollama endpoint:
  **Torre** `100.91.154.124:11434` (primary) →
  **UM790 CPU** `ollama:11434` (`backup`). `nginx` upstream
  with `proxy_next_upstream … non_idempotent` and
  `proxy_buffering off` (streaming preserved).
- Single point of failure in front of both front doors;
  `restart: unless-stopped` + healthcheck. A *Torre* outage
  fails over to the UM790; only a *proxy* outage stops
  inference (rollback = repoint consumers back to
  `ollama:11434`).
- Config + compose:
  [`03_services/ollama-proxy/`](../03_services/ollama-proxy/).

### Qdrant

Status: Operational

RAG collections:

- homelab_docs
- knowledge_history
- ops_digests (F-4 operational memory; 384/Cosine; AD-14)
- guardian_cloud
- ensambla2
- infra_audits
- myfreetour (disabled; 0 points)
- `open-webui_files`, `open-webui_knowledge` — **Open WebUI-internal, not AMAROLAB
  RAG collections.** Created and managed by Open WebUI itself; listed here because
  they exist in the same Qdrant instance and appear in backups (L-3, reconciled
  2026-07-28)

---

## Home Assistant

Status: Operational

- HTTPS external URL: `https://ha.amarolab.es`
  (`homeassistant.external_url` YAML-managed).
- Reverse-proxy trust: `http.use_x_forwarded_for: true`
  with `http.trusted_proxies: [172.18.0.0/16,
  127.0.0.1, ::1]`. Only the `cloudflared-amarolab`
  bridge subnet is trusted; the LAN is intentionally
  not trusted broadly.
- MQTT integration: enabled inside Home Assistant
- Zigbee2MQTT discovery: enabled (auto-discovery active)
- Wyoming integrations (per D-1.5): `aurora-whisper`
  (STT), `aurora-piper` (TTS), `aurora-wakeword`.
- Ollama integration: `http://127.0.0.1:11435` (the
  `ollama-proxy` loopback — Torre primary + UM790 CPU
  fallback — per RTX-1.6) / `qwen2.5:7b-instruct`.
- Assist pipeline `AURORA v1` is the default /
  preferred pipeline (language `es-ES`).
- **Voice awareness (F-3b):** helper `input_text.aurora_voice_context`
  (max 255) holds the nightly single-line lab status; the Ollama voice
  prompt renders it via Jinja2 `{{ states('input_text.aurora_voice_context') }}`.
  `bin/push-voice-context` pushes `aurora-context-voice.txt` into the helper at
  04:20 via HA REST `input_text/set_value` (G-F3-8). The voice prompt is
  otherwise the production baseline (the F-1 voice identity is unchanged).
- Voice canary helper: `input_boolean.aurora_voice_canary`
  (state `off`, baseline restored after every gate).
- Voice-exposure ACL: **ZERO entities are exposed** (measured live 2026-07-28 at
  I-7; `expose_new: false`, and the three listed entities —
  `conversation.home_assistant`, `zone.home`, `sun.sun` — are all
  `should_expose: false`). **The canary does not appear in the ACL at all.**
  This document previously claimed exactly one entity exposed
  (`input_boolean.aurora_voice_canary`); that was **wrong**, and reality is
  *stricter* than was documented, so it has been operationally harmless (M-5).
  The printer (`switch.impresora_3d`) is likewise not exposed; permanent denies
  cover `homeassistant.*`, `hassio.*`, `recorder.*`, and any Guardian Cloud
  entity. **Consequence: F6.1 Step 7 has no live voice acceptance path** until a
  decision is taken on re-exposing the canary — tracked as **S-11**, open.

First Zigbee devices imported:

- **Impresora 3D** — Sonoff S60ZBTPF smart plug
- **Toldo** — Sonoff MINI-ZBRBS roller shutter
- **Zigbee2MQTT Bridge** (the bridge entity itself)

Reference:
[`03_services/zigbee-stack/zigbee2mqtt_first_devices.md`](../03_services/zigbee-stack/zigbee2mqtt_first_devices.md).

---

## Mosquitto

Status: Operational — **hardened** (2026-06-17)

Current authentication posture: **authenticated MQTT
users + ACLs**.

- `allow_anonymous false`
- `password_file /mosquitto/config/passwords`
- `acl_file /mosquitto/config/acls`
- Users: `homeassistant`, `zigbee2mqtt` (passwords
  hashed in `passwords`; plaintext in
  `/home/diego/.secrets/mqtt-credentials.env`, never
  in repo)
- Per-user ACLs scope each principal to its required
  topic namespaces (default-deny)
- Anonymous `mosquitto_sub` is refused with
  `Connection Refused: not authorised`
- Gate G-5 re-executed end-to-end through the hardened
  broker — 5 audit lines, all
  `allowed=true, result_code="ok"`, baseline restored
- Gate G-D5 (voice) re-executed end-to-end through the
  hardened broker — voice → HA → Mosquitto → Z2M →
  Sonoff S60ZBTPF round-trip confirmed; baseline `off`
  restored

Reference:
[`03_services/zigbee-stack/mosquitto/auth-hardening.md`](../03_services/zigbee-stack/mosquitto/auth-hardening.md).
Apply log:
[`09_logs/2026-06-17_mosquitto_auth_hardening_applied.md`](../09_logs/2026-06-17_mosquitto_auth_hardening_applied.md).

---

## Zigbee2MQTT

Status: **DOWN since 2026-08-17 13:12:24 CEST** — `exited (2)`, **third** C-1 recurrence

- Adapter: Sonoff Zigbee Dongle Plus
- Frontend: **enabled**
- Home Assistant discovery: **enabled**
- **10 devices paired** (measured 2026-07-28 at I-7 from the Zigbee2MQTT state file;
  the earlier "first devices joined" wording predates the current network — N-1)
- **C-1 (2026-07-28): the container exited `code=2` at 00:10 CEST** when a USB
  re-enumeration removed the CP210x bridge; `zigbee2mqtt` treats adapter loss as fatal.
  Both Zigbee entities went `unavailable` and **nothing alerted** — the outage was found
  by an audit 2 h 39 m later, not by monitoring. Service restored 02:49 (`docker start`).
- **Second recurrence, 2026-07-28 15:52.** Same mechanism, independent trigger: hot-plugging
  a Bluetooth adapter into the **same external hub** as the coordinator reset that hub;
  Docker's single `unless-stopped` restart attempt then failed with `error gathering device
  information … no such file or directory` **80 ms before** udev recreated the node, and the
  restart manager gave up permanently. Timeline: `ROADMAP.md` → *C-1 recurrence 2026-07-28
  15:52*.
- **That outage ended on 2026-08-12 without being recorded.** The container restarted
  automatically at the reboot (`2026-08-12T07:28:13Z`, thirteen seconds after boot —
  `unless-stopped` restored at daemon start) and **ran healthily for five days**, publishing
  device telemetry every ten seconds. The triad's prior "deliberately not restarted" claim
  was true when written and was silently undone by the reboot.
- **Third recurrence, 2026-08-17 13:12:24 CEST — current state** (`RestartCount 1`). Same
  mechanism; **101 ms** margin this time. **What is new: there was no trigger.** Zero USB
  enumerations occurred between 00:00 and the disconnect, and the Bluetooth adapter has been
  resident on the shared hub since the 2026-08-12 boot. The coordinator dropped off the bus
  with **no observable external cause**, which widens the failure mode beyond hot-plug and
  must be reflected in any future S-9 design. **The adapter is present and free** — the node
  and `by-id` symlink were recreated at 13:12:25 and both resolve, nothing holds the device.
  **Not restarted**; recovery is a separate operator-approved intervention. Full timeline:
  `ROADMAP.md` → *C-1 recurrence 2026-08-17 13:12* and
  `09_logs/2026-08-17_operational_reconciliation.md` §3.
- **Structural half: S-9. Notification gap: M-1 / M-A** — both **Open**. The nightly signal
  layer runs 04:00–04:25, so a 13:12 failure is not visible until the next cycle; the outage
  was found by inspection seven hours later, not by monitoring.

---

## Voice stack

Status: **Operational end-to-end** (Phase D-1 closed
2026-06-18).

### Home Assistant voice path (Wyoming)

- `aurora-whisper` (Wyoming STT) on `ai-local_default`
  - Image: `rhasspy/wyoming-whisper:3.2.0`
  - Endpoint: `tcp://aurora-whisper:10300` (internal)
  - Model: `base-int8`
  - Real-time factor on UM790 CPU: **0.055** on the
    G-D1 reference clip
  - **D-F6-1 holds across the 2026-08-12 reboot — the container was restarted, not
    recreated** (verified 2026-08-17): created `2026-06-17T14:21:14Z`, image id
    `sha256:966e1b09…a58dd158` **identical** to the F6.1 baseline pin, command still
    `--model base-int8 --language auto --beam-size 1 --compute-type int8`,
    `RestartCount` 0. Only `StartedAt` moved (`2026-07-25T21:50:55Z` →
    `2026-08-12T07:28:13Z`), so the F6.1 Step 2 baseline stands; the moved timestamp is
    recorded so it is not misread as evidence of recreation.
    **Do not recreate this container while F6.1 is open.**
- `aurora-piper` (Wyoming TTS) on `ai-local_default`
  - Image: `rhasspy/wyoming-piper:<pinned tag>`
  - Endpoint: `tcp://aurora-piper:10200` (internal)
  - Voice: **`es_ES-sharvard-medium`, speaker F** (verified live 2026-07-28 at
    I-7 — the container runs `--voice es_ES-sharvard-medium --speaker F
    --length-scale 1.0`). This document previously said `es_ES-davefx-medium`;
    that was stale (L-2). Both the HA Wyoming path and the Open WebUI shim use
    sharvard, which is consistent with C-D-08
- `aurora-wakeword` (Wyoming openWakeWord) on
  `ai-local_default`
  - Endpoint: `tcp://aurora-wakeword:10400` (internal)
  - Wake word: `okay_nabu` (push-to-talk is the D-1
    default in HA Assist; wake-word path validated by
    Wyoming describe + synthetic detection probe at
    D-1.4)
- HA Assist pipeline `AURORA v1`
  - Default / preferred pipeline
  - Slots: `aurora-wakeword` / `aurora-whisper` /
    HA Ollama (`qwen2.5:7b-instruct`) / `aurora-piper`

### Open WebUI audio path (OpenAI-API HTTP shims)

- `aurora-whisper-http` (faster-whisper HTTP shim) on
  `ai-local_default`
  - Image:
    `fedirz/faster-whisper-server:0.6.0-rc.3-cpu`
  - Endpoint: `http://aurora-whisper-http:8000/v1`
    (internal)
  - Model: `Systran/faster-whisper-base`, `int8`
  - Bind mount:
    `/srv/homelab/data/whisper/http`
- `aurora-piper-http` (openedai-speech) on
  `ai-local_default`
  - Image: `ghcr.io/matatonic/openedai-speech:0.18.2`
  - Endpoint: `http://aurora-piper-http:8000/v1`
    (internal)
  - Voice mapping: all OpenAI standard voice slots
    route to `es_ES-sharvard-medium` speaker F
    (`/srv/homelab/data/openedai-speech/voice_to_speaker.yaml`)
  - XTTS disabled via `--xtts_device none`
- Open WebUI `webui.db.audio.*` patched to route STT
  and TTS at the two shims; default auto-playback
  off (C-D-07).

### Latency profile (read-only, D-1.7 §4)

Dominant bottleneck is `qwen2.5:7b-instruct` response
generation on UM790 CPU at ~6 tok/s (≈ 89 % of
warm-cycle latency). STT (Whisper, ~0.6 s warm) and
TTS (Piper, ~0.6 s) together contribute under 2 s.
First-message cold KV cache adds ~16.9 s for the
3 342-char Amarolab system prompt and amortises to
~0.2 s on every subsequent turn.

Performance optimization is **deferred to the RTX 5070
AI-node bridge** ([`04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md`](../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md));
the voice-stack architecture is GPU-ready and only the
`ollama` endpoint target needs to change.

Reference architecture:
[`03_services/voice-stack/README.md`](../03_services/voice-stack/README.md).
Whisper deployment plan:
[`03_services/voice-stack/whisper/faster-whisper-deployment.md`](../03_services/voice-stack/whisper/faster-whisper-deployment.md).
Pipeline spec:
[`03_services/voice-stack/ha-assist/pipeline-spec.md`](../03_services/voice-stack/ha-assist/pipeline-spec.md).

---

## Voice Lab — Round 1 (native TTS casting)

Status: **Round 1 COMPLETE 2026-07-27. Repo-external — not committed. No production change.**

An isolated local **Voice Lab** (outside this repository; its code, model weights, container
images and audio outputs are intentionally **not** committed — evaluation tooling, not
production infrastructure) was used to cast Aurora's candidate **native** TTS voice. Method: a
fixed Spanish evaluation corpus synthesized under **identical, loudness-matched conditions** by
every engine, then a **blind** comparison (engines relabeled Voice A/B/…, order randomized,
mapping sealed and revealed only after scoring; subjective casting primary, engineering metrics
tie-breakers only).

- Engines cast (native, female Spanish): **Piper** (incumbent production voice), **Kokoro**
  (`ef_dora`), **XTTS v2** (Coqui CPML — reference only, non-commercial), **Chatterbox**. A
  hosted engine was included **reference-only** (imported by hand — no cloud call from AMAROLAB,
  no credentials stored).
- **Result: Kokoro `ef_dora` preferred at ~70% confidence, ahead of the incumbent Piper.**
- **Kokoro is now the native TTS reference candidate. Piper remains the production voice — no
  production migration occurred** (HA, Open WebUI and the Piper services are unchanged).
- **Round 2 (voice cloning) is designed, not started.** **Next gate: define Aurora's synthetic
  voice identity**, then record a legally-permitted Castilian reference and evaluate cloning
  under the same blind method.

Record: [`09_logs/2026-07-27_voice_lab_round1.md`](../09_logs/2026-07-27_voice_lab_round1.md).

---

## Cloudflare

Status: Operational with **two separate tunnels**.

- **Guardian Cloud tunnel** — `cloudflared` container
  on `cloudflare-net`. Serves
  `app.guardiancloud.app` + `api.guardiancloud.app`.
  **Untouched** throughout Phase D.
- **Amarolab tunnel** — `cloudflared-amarolab`
  container on `ai-local_default`. Public Hostnames:
  - `ha.amarolab.es` → `http://192.168.178.79:8123`
    (Home Assistant)
  - `ai.amarolab.es` → Open WebUI (bound during D-1.7;
    serves both chat and audio)
- Connector token persisted at
  `/home/diego/.secrets/cloudflared-amarolab.env`
  (mode `0600`, never in repo). Per Lesson 008.

The original Cloudflare DNS architecture note in
[`02_infrastructure/cloudflare/amarolab_dns_architecture.md`](../02_infrastructure/cloudflare/amarolab_dns_architecture.md)
described attaching the existing Guardian Cloud
tunnel to `ai-local_default`. The **shipped**
architecture is a separate tunnel + container, for
blast-radius isolation between Guardian Cloud product
surface and AMAROLAB infrastructure surface. Doc
amendment carried as a post-D-1.9 documentation-sync
follow-up.

---

## Storage

Status: Operational

Current setup:

- **2 TB USB disk** connected directly to the mini server
- Hosts the Restic backup repository and bulk data
- **Not** a dedicated NAS

Planned:

- Dedicated NAS purchase, to be scheduled later
- Migration of backups and bulk data once procured

---

## Backups

Status: **Backup PASS — grouping defect FIXED at I-4 (2026-07-31); retention live but
`--dry-run`, so no snapshot can be deleted.** The nightly `restic backup` step has
succeeded every night and recoverability is proven (restore drill PASS E5-b 2026-06-27;
empirical restic restore-drill G-F4-08 2026-07-27 on snapshot `7715bf6a`).
**Re-verified 2026-08-17:** the fix has now held across **eighteen further unattended
nights** — unbroken nightly snapshots from 2026-07-31 (`34def61f`) through 2026-08-17
(`fe0409fb`), parent detection working throughout (`17990ec0` → `c1707709` → `fe0409fb`),
installed script sha256 unchanged, and the 2026-08-12 reboot did not disturb the schedule.
**G-I4-1…12 are not reopened** — this is continuing evidence, not a re-gate.

- **The grouping defect is FIXED (H-1a / L-9 — CLOSED at I-4).** `homelab-backup.sh` used
  to embed `$(date +%F)` in the restic path set, and restic groups by `host,paths` by
  default, so every nightly snapshot landed in its own group of one and the policy could
  delete nothing. `SNAP_DIR` is now the undated `/tmp/homelab-backup-snapshots`
  (script sha256 `90e8eb91…a907a45f`). **Verified on real evidence at Gate 8, 2026-07-31:**
  45 snapshots in **42 groups**, the three post-fix snapshots
  (`6323b009` → `89966886` → `d03f0e19`) sharing a **byte-identical 13-element `paths[]`**
  and forming one group. `--group-by` was deliberately **not** changed; restic's default
  `host,paths` grouping is retained as a safety property.
- **Change detection is restored (L-9 — CLOSED).** `no parent snapshot found` is gone;
  each run now names its parent and reports real deltas — `0 new, 267 changed, 2473
  unmodified` (2026-07-29) and `1 new, 165 changed, 2575 unmodified` (2026-07-30),
  against ~2740 files. The nightly full ~4.1 GiB re-scan is over.
- **Retention runs as `--dry-run`. No snapshot can be deleted by the nightly job.** This is
  deliberate, not a leftover: with grouping fixed the policy is live again and would begin
  deleting once the post-fix group spans more than 7 days — before the policy has been
  decided (**S-10**) and before the anchor has protection (**I-6**). Re-enabling deletion is
  **S-10**, attended and operator-approved per execution.
- **The 42 legacy snapshots are permanently unreachable by the nightly policy.** They sit in
  41 dated groups no future snapshot can join. Removing them needs an explicit mechanism —
  selection by ID, or a deliberate one-off grouping override — executed attended at
  **S-10**. This is a handover, not a defect.
- **The would-remove report arrived on 2026-08-05 — the prediction held.** I-4 expected it
  "on or shortly after 2026-08-04"; the 2026-08-04 run produced none, and the 2026-08-05 run
  produced the first, `{89966886}`. It has grown monotonically since: **1 (08-05) → 3 (08-08)
  → 6 (08-12) → 9 (08-15) → 10 (08-17)**. **13 reports across 13 nights, and nothing was ever
  removed** — every one is phrased `Would have removed the following snapshots:`, restic's
  dry-run wording, and no deletion of any kind appears anywhere in the log history. **This is
  the input S-10 requires.** Full night-by-night table:
  `09_logs/2026-08-17_operational_reconciliation.md` §5.
- **The report now proposes the two Gate 8 snapshots** (`89966886`, `d03f0e19`). They are
  ordinary `nightly`-tagged snapshots with no protection and the policy is correctly aging
  them out of `--keep-daily 7`. Expected, not a defect — but it is what S-10 would delete.
- **The D-1.5 anchor `63c072f4` has appeared in none of the 13 reports.** It survives only
  because it sits in a legacy dated group of one that no future snapshot can join — **group
  shape, not protection**. This is exactly the risk I-4 named (*never rely on group shape for
  protection*): **I-6 must land before S-10.**
- **The nightly retention policy has never removed a snapshot** since repository creation on
  2026-06-13. Re-verified 2026-08-17 across the retained log history (current log plus eight
  rotated predecessors): **26 `forget` executions, 13 would-remove reports, zero real
  removals.** **Open
  observation, raised 2026-07-31:** snapshot `63c072f4` records `parent: 4f4177e8…`, and no
  snapshot with that id exists in the repository — so *something* removed a snapshot on or
  before 2026-06-17. Not the nightly policy, which was structurally inert throughout.
  Unexplained; no I-4 gate depends on it.
- **No tag-based protection exists for any snapshot** (§5 of the incident record).
- **The backup probe cannot see any of this (H-1c, open).** `bin/backup-probe` evaluates
  only newest-snapshot age against a 4 h window, so `backup_status.json` reported `ok`
  for 30 days while half the job failed nightly. Remediation is **S-8**.
- **Backup coverage is incomplete (H-2, open).** The Portainer volume,
  `ai-stack/.env`, `/home/diego/.secrets/`, `/etc/cron.d/aurora-signals` and the
  openedai voice map are outside the path set — a root-disk loss is **not** currently
  recoverable to a running state from restic alone. Remediation is **I-5** / **M-D**.
- Incident record (dated, authoritative for the diagnosis):
  [`../09_logs/2026-07-28_backup_retention_incident.md`](../09_logs/2026-07-28_backup_retention_incident.md).
- **I-4 Gate 8 closeout (dated, authoritative for the fix and its gates):**
  [`../09_logs/2026-07-31_I4_gate8_closeout.md`](../09_logs/2026-07-31_I4_gate8_closeout.md).

- Restic installed
- Repository initialised on the 2 TB USB disk
- Snapshot validated
- D-1.5 anchor snapshot `63c072f4` retained as the
  pre-voice-pipeline rollback point (still in the
  repository, unchanged through D-1.6 / D-1.7 / D-1.8).
  **It has no protective mechanism.** It is tagged `nightly` like every other
  snapshot and is fully in scope for `forget --tag nightly`; it survives only
  because the policy currently deletes nothing (§5 of the incident record).
  Giving it real protection is **I-6**, open — and must land before **S-10**.
- **E5-b restore drill (2026-06-27):** snapshot `228e4183`
  (2026-06-27 nightly) restored into isolated environment;
  Qdrant data fully recoverable; 15 consecutive nightly
  snapshots confirmed in repository. Actual Qdrant backup
  size: 2.8 GiB (E-0 estimate of 36 MB was an undercount —
  includes `open-webui_files` and `open-webui_knowledge`
  collections). Apply log:
  [`../09_logs/2026-06-27_phaseE_E5b_restore_drill_applied.md`](../09_logs/2026-06-27_phaseE_E5b_restore_drill_applied.md).

---

## Ingest service

Status: Versioned + operational (nightly indexing live)

Path: `ai-stack/ingest`

Includes:

- chunking
- embeddings
- reranker
- qdrant storage
- filesystem connector
- git connector

Indexing operational status (verified 2026-06-29, Phase F F2-9):

- Nightly sync: cron `30 2 * * *` (`diego` crontab), before the
  03:00 restic backup. Idempotent (per-chunk `content_sha`); GC of
  vanished files.
- Live collection point counts (**measured 2026-07-28 at I-7**; the growing
  collections grow nightly, so these are a dated observation, not a fixed value):
  `homelab_docs` 2875 · `knowledge_history` 3780 · `ops_digests` 75 (F-4
  operational memory) · `guardian_cloud` 872 · `ensambla2` 419 ·
  `infra_audits` 280 · `myfreetour` 0 (disabled). Open WebUI-internal:
  `open-webui_knowledge` 3 · `open-webui_files` 2.
  *(Prior record, 2026-06-30: `homelab_docs` 2088 excl. `09_logs/`,
  `knowledge_history` 3132, `ops_digests` 3.)*
- Embedder `intfloat/multilingual-e5-small` (384-dim) / reranker
  `BAAI/bge-reranker-v2-m3`. Full contract:
  [`../04_ai_system/knowledge_platform_contract.md`](../04_ai_system/knowledge_platform_contract.md).
- The Qdrant data dir (`ai-stack/data/qdrant`) is in the nightly
  restic backup.

Phase E hardening: **E2-a done (2026-06-27)** — the nightly sync exit code is
now a reliable failure signal (a disabled corpus is an expected skip → rc 0;
a genuine failure → rc 1), per finding F-01. Apply log:
[`../09_logs/2026-06-27_phaseE_E2a_failloud_sync_applied.md`](../09_logs/2026-06-27_phaseE_E2a_failloud_sync_applied.md).
**E2-c done (2026-06-27)** — run-lock (`flock -n`, F-08): `bin/ingest-nightly`
holds `logs/ingest-nightly.lock`; overlapping runs exit 0 with
`SKIPPED (lock held)`. **E4-a done (2026-06-27)** — log rotation (F-04):
`/etc/logrotate.d/homelab-ingest` (source:
`ai-stack/ingest/etc/logrotate.d/homelab-ingest`); `ingest.log` weekly/8-week;
`amarolab-audit.log` monthly/12-month. Apply log:
[`../09_logs/2026-06-27_phaseE_E2c_E4a_maintenance_applied.md`](../09_logs/2026-06-27_phaseE_E2c_E4a_maintenance_applied.md).
Audit evidence base:
[`../09_logs/2026-06-27_phaseE_E0_operational_audit_report.md`](../09_logs/2026-06-27_phaseE_E0_operational_audit_report.md).

**E5-b restore drill done (2026-06-27)** — nightly restic backup proven
recoverable: snapshot `228e4183` restored into isolated disposable container
(`qdrant/qdrant:v1.17.0`, loopback-only `127.0.0.1:6399`), all 5 collections
green (4049/872/419/280/0), fixture parity 16/16 (top-30 set + top-6 order).
Production untouched (uptime unbroken, counts unchanged). Apply log:
[`../09_logs/2026-06-27_phaseE_E5b_restore_drill_applied.md`](../09_logs/2026-06-27_phaseE_E5b_restore_drill_applied.md).

**E4-b done (2026-06-27)** — backup-consistency spike (F-05a): no change required.
Hot backup (E5-b 16/16 PASS) + cron order (ingest 02:30, restic 03:00 — 29-minute
quiescent window) are sufficient. Quiesce/snapshot-API rejected for current scale.
Residual risk documented and accepted. Decision record:
[`../09_logs/2026-06-27_phaseE_E4b_backup_consistency_decision.md`](../09_logs/2026-06-27_phaseE_E4b_backup_consistency_decision.md).

**E-6 done (2026-06-28)** — onboarding framework (F-07): framework document at
`04_ai_system/onboarding_framework.md` (12 sections). Proven end-to-end against
disposable corpus `e6_test` (fictional Project Helios, 16 points indexed): onboarded,
retrieval validated (HE-01/HE-02/HE-03 all PASS), and fully removed — no production
artifact remaining. Success criterion met. Apply log:
[`../09_logs/2026-06-28_phaseE_E6_onboarding_framework_applied.md`](../09_logs/2026-06-28_phaseE_E6_onboarding_framework_applied.md).

**E-3 observability bundle done (2026-06-27)** — unified platform health
file `ai-stack/ingest/logs/health.json` live (gitignored; runtime state).
Two new scripts: `bin/ingest-nightly` (02:30 cron, wraps ingest sync, writes
ingest section, frames `ingest.log` with run boundaries — E3-a/E3-b) and
`bin/check-audit-liveness` (03:30 cron, writes audit section — E3-c).
`overall_status` computed from both sections; carries `last_successful_run_end`
across failures. `overall_status=ok` (resolved 2026-06-27 after E5-c closed F-10).
Apply log:
[`../09_logs/2026-06-27_phaseE_E3_observability_applied.md`](../09_logs/2026-06-27_phaseE_E3_observability_applied.md).

**Open observation, raised 2026-08-17 — `overall_status` has read `degraded` since
2026-08-01 because the audit log is empty.** `logrotate` rotates
`/srv/homelab/data/openwebui/amarolab-audit.log` **monthly** (E4-a); it rotated at
2026-08-01 00:00 creating a new empty file, and **no Aurora tool call has been made since**
(July's content is intact in `amarolab-audit.log.1`, last entry `2026-07-28T16:09:40Z`). So
`bin/check-audit-liveness` finds no entry and writes `audit.status = "missing"`, and
`bin/aurora-context` has carried `degrades=['audit log missing']` on every nightly cycle
since. **The cause is benign — monthly rotation plus genuine non-use, not a broken audit
path** — but the probe cannot distinguish "nobody used the tools" from "the audit path is
broken" and answers `missing` for both. This is the symptom shape of **F-10** (closed at
E5-c) returning by a different mechanism, and a platform pinned at `degraded` on every
nightly cycle since 2026-08-01 is a status that stops being read — it masked the Zigbee
anomaly clearing on 2026-08-12 and returning on 2026-08-17. **Not fixed; no remediation identifier assigned**, on the
R-I3-1…7 / F-S1-1 precedent. Record:
[`../09_logs/2026-08-17_operational_reconciliation.md`](../09_logs/2026-08-17_operational_reconciliation.md) §6.

---

## Documentation

Status: Consolidated

Repository structure:

- 00_overview
- 01_architecture
- 02_infrastructure
- 03_services
- 04_ai_system
- 05_data
- 06_security
- 07_operations
- 08_projects
- 09_logs

---

## GitHub

Status: Synchronized

Recent work landed on `main`:

- Phase B closeout
- Phase C Tool installs (`ha_get_state`, `ha_call_service`)
- Gate G-4 — qwen2.5 `meta.toolIds` extension
- C-5 — Tool-level refusal validation
- C-6a — first real Home Assistant read against `sun.sun`
- Zigbee2MQTT first devices imported into Home Assistant
- Phase C documentation sync (tag `v0.3-phase-c-doc-sync`)
- Gate G-5 — first real `ha_call_service` happy path
  against `switch.impresora_3d`
- Phase C closeout
- Mosquitto authentication hardening (tag
  `v0.4-mosquitto-hardening`)
- Phase D-1 voice stack: Whisper / Piper /
  openWakeWord / `AURORA v1` pipeline / HA reverse-
  proxy trust patch / G-D4 / G-D5 / D-1.7 Open WebUI
  audio shims / G-D6 failure-mode rehearsal / D-1.9
  closeout
- 2026-07-10 — repository history intentionally sanitized
  and republished (force-push): every commit hash changed;
  technical content and chronology preserved. Local repo,
  branches and all 21 tags resynchronized to the rewritten
  origin; live docs reconciled to the canonical hashes. See
  `09_logs/2026-07-10_repo_history_sanitization_reconciliation.md`.

---

## Secrets

All sensitive values are kept out of versioned documentation.

Placeholders used throughout:

- `${HA_BASE_URL}`
- `${HA_LLAT}`
- `${WEBUI_SECRET_KEY}`
- `${QDRANT_API_KEY}`

Authoritative location for live values: `ai-stack/.env`
(not committed in plain text). Cloudflare connector
token for the `amarolab` tunnel lives at
`/home/diego/.secrets/cloudflared-amarolab.env`
(mode `0600`, never in repo).

---

## Infrastructure audit — 2026-07-28

A full read-only technical audit of the running platform ran 2026-07-28 (02:28–02:50 CEST),
producing **38 findings** (1 Critical · 8 High · 10 Medium · 11 Low, plus 8 derived during
P0 execution) and a five-program remediation roadmap. Both are published and are the
authoritative finding register:

- Audit: [`../09_logs/2026-07-28_amarolab_technical_audit.md`](../09_logs/2026-07-28_amarolab_technical_audit.md)
- Roadmap: [`../09_logs/2026-07-28_amarolab_remediation_roadmap.md`](../09_logs/2026-07-28_amarolab_remediation_roadmap.md)

> Both are **dated records**. Their own status columns are frozen as-of-2026-07-28 and do
> **not** track execution. This section is the live status.

### Program status

| | Program | Status |
|---|---|---|
| **A** | Declarative substrate | **Capture COMPLETE** (I-3). Convergence (M-B) + digest pinning (M-C) open |
| **B** | Observability & alerting | **Open** — nothing observes anything in real time. M-1 is the largest item in the roadmap |
| **C** | Security posture | **S-1 DECIDED 2026-07-28** — the LAN is a trusted transport, never a substitute for service authentication. S-2/S-3/S-4/S-5 unblocked; four listeners non-conforming |
| **D** | Documentation truth | **This reconciliation (I-7)**. Drift items closed below |
| **E** | Backup lifecycle | **I-4 COMPLETE 2026-07-31** (grouping fixed, Gate 8 closed on real evidence; retention held at `--dry-run`). Remaining: I-5 → I-6 → I-8 → S-8 → S-10 |

### Completed

- **P0 (2026-07-28):** C-1 service restored (`docker start zigbee2mqtt`); stale restic lock
  cleared. **No snapshot was deleted; Stage C was never approved or executed.**
- **I-1** — audit, roadmap and the backup incident record published to `09_logs/`.
- **I-2** — the H-4 redeploy hazard recorded: [`../07_operations/hazards/portainer_ai_local_redeploy.md`](../07_operations/hazards/portainer_ai_local_redeploy.md).
- **I-3 — Program A capture COMPLETE** (`319b2c58`, 2026-07-28). 14 services across 6
  compose projects captured from `docker inspect` into `03_services/`; field-by-field
  parity **103/103, 0 differences**; no production change. Apply log:
  [`../09_logs/2026-07-28_I3_declarative_substrate_capture.md`](../09_logs/2026-07-28_I3_declarative_substrate_capture.md).
  Seven items discovered during capture (**R-I3-1…7**) are recorded there and deliberately
  unimplemented — R-I3-1 is the sharpest: docker network subnets are assigned by creation
  order and Home Assistant's `trusted_proxies` depends on `172.18.0.0/16`.
- **S-1 — LAN trust posture DECIDED 2026-07-28.** *The LAN is a trusted transport; it is
  never a substitute for service authentication; every LAN-reachable service must
  authenticate, be explicitly justified, or remain closed.* Recorded in
  [`../06_security/security_posture.md`](../06_security/security_posture.md); decision
  record [`../09_logs/2026-07-28_S1_lan_trust_posture_decision.md`](../09_logs/2026-07-28_S1_lan_trust_posture_decision.md).
  **S-2/S-3/S-4/S-5 unblocked.** Ten of fourteen LAN-reachable services meet the bar; four
  do not — **H-5** (Ollama, `HTTP 200` unauthenticated from the LAN), **H-6**
  (homelab-tools), **M-9** (SSH password auth), plus two new findings **F-S1-1**
  (`rpcbind` listening with no NFS behind it) and **F-S1-2** (an unattributed LAN-reachable
  listener on `18555`) — both recorded and **deliberately unimplemented**, on the R-I3-1…7
  precedent, with **no remediation identifier assigned**. Network segmentation is now a
  **decided non-goal at current scale**, removed from pending. `ufw` remains off **by
  decision**; note that eight of the exposed ports are Docker-published, so enabling it
  would not close them. **No production change.**

### Recovery Artifact doctrine — ACTIVE

`PROJECT_RULES.md` → **Recovery Artifacts** (added at I-3) is a permanent rule. It defines
three states a definition may occupy — *Recovery Artifact* (describes) → *Validated*
(proven) → *Deployment Source* (governs) — and forbids promotion by drift.

**Every compose file under `03_services/` is a Recovery Artifact except
`ollama-proxy/docker-compose.yml`, which is the sole Deployment Source.** The captured
files describe reality and have no authority to change it; they are inert by construction
(an `amarolab-` prefixed project name that cannot match a running container, plus explicit
`container_name` so an accidental apply collides and aborts) and carry redacted secrets and
device paths, so they are **not deployable as written**. **Git is not yet the deployment
source of truth for these services** — that changes only at M-B, which depends on I-3 and on
F6.1 being closed.

### Deferred to Documentation Hygiene

The audit's remaining Low-severity documentation items are tracked in `ROADMAP.md` →
*Documentation Hygiene* (L-6, L-7, L-8, L-11, M-4) — none affects an operational claim.
L-10 needs no action: it self-corrects at the next 04:15 cycle and was a symptom of M-1.

---

## Known pending items

1. **Cloudflare Tunnel token rotation** (R-01) — existing
   Guardian-Cloud tunnel.
2. **RTX 5070 AI-node bridge** — **Phase RTX-1 CLOSED.**
   RTX-1.4 (Tailscale-only), RTX-1.5 (headless NSSM
   service), and **RTX-1.6 (endpoint swap via `ollama-proxy`,
   Torre primary + UM790 fallback) all complete (2026-06-27).**
   Streaming TTS, prompt trimming, and the STT model-size
   bump remain not started.
3. **Dedicated NAS** — procurement and data migration.
4. **MyFreeTour** RAG collection — **future consumer project**,
   onboards onto the knowledge platform after Phase E (Foundation);
   not Phase E work. Source path still TBD (sub-project blocker B-08).
5. **DNS / Cloudflare architecture doc amendments**
   — record the separate-tunnel decision and the
   `ai.amarolab.es` binding in
   [`02_infrastructure/cloudflare/`](../02_infrastructure/cloudflare/).
6. **`cloudflared-amarolab` standalone apply log** —
   deployment validated through D-1.5 → G-D6 but no
   dedicated standalone log yet.
7. ~~**R-F5-A — Awareness-consumption gap (F-5 blocker)**~~ — **CLOSED 2026-07-16 at WM-6.**
   G-F5-04 failed real validation on 2026-07-01 (the model routed status queries to
   home-blind tools instead of the injected `Home State` block); the World Model was its
   structural remedy (WM-4/WM-5), and **G-F5-04 was reopened and CLOSED on real evidence
   (chat + voice) at WM-6 — R-F5-A and F-5 are CLOSED.** Closeout:
   `09_logs/2026-07-16_WM6_G-F5-04_closeout.md`. History:
   `09_logs/2026-07-01_phaseF_F5_3_applied.md`. *(Entry reconciled at ER-1.0 — it still
   listed R-F5-A as a pending blocker, contradicting this document's own header.)*
8. **ER-1 — Deterministic Entity Resolution** — **design FROZEN 2026-07-16 (now Revision 4);
   implementation COMPLETE — Phase ER-1 CLOSED at ER-1.5 (closeout 2026-07-21, `09_logs/2026-07-21_ER1_5_closeout.md`). ER-1.0 (`c147e632` → `38eb8262`), the Revision 2 amendment
   (`3ebf59d1`), ER-1.1 (`f983a04f`), ER-1.2 (`b0fded73`) and ER-1.3 (`ed7a149c`) are
   committed + pushed; G-ER-5 CLOSED 2026-07-17 on real unattended evidence; G-ER-6 producer
   half CLOSED at ER-1.3. ER-1.4a (v0.1.0 baseline + `ha_get_state` v0.2.0) implemented +
   validated 2026-07-17 — G-ER-7 read half + G-ER-6 consumer half (read side) CLOSED. **ER-1.4b
   (`ha_call_service` v0.2.0 — resolution + ER-1-C1, Rule B / 500 ms) implemented + validated
   2026-07-20 — committed + pushed `5b502c96`; G-ER-2/3a/3b/4 + G-ER-7 write half + G-ER-6 consumer half
   (write side) all PASS. ER-1.5 (closeout) COMPLETE 2026-07-21.** **The read path (ER-1.4a) and the write
   path (ER-1.4b) both resolve natural language now; the write path also verifies before it
   claims success**, so the 13 historical unverified writes to non-existent entities in a live
   HA domain can no longer be reported as successful (proven by G-ER-3b). Spec:
   `04_ai_system/entity_resolution_layer.md`; roadmap: `ROADMAP.md` → Phase ER-1.
9. ~~**F-ER13-1 — `bin/aurora-context` can publish one file's content under another file's
   name.**~~ — **RESOLVED.** Fixed in commit `6525b0d2`; verified live 2026-07-28 at I-7:
   `bin/aurora-context` now derives the temp path via
   `path.with_name(f".{path.name}.{os.getpid()}.tmp")` (line 107) **and** holds a
   `fcntl.flock(LOCK_EX | LOCK_NB)` run-lock (line 252), mirroring `bin/ingest-nightly`.
   Both halves of the hazard are closed. The original description follows for the record:
   Its `write_atomic` derived the temp path via `path.with_suffix(".tmp")`, so
   `aurora-context.json` and `aurora-context.md` **both** map to `aurora-context.tmp`; and
   unlike `bin/ingest-nightly` (`flock -n`), `bin/aurora-context` holds **no run-lock**.
   Harmless today — the three writes are sequential within one process. The hazard is
   **concurrency**: a manual run overlapping the 04:15 cron could interleave and leave
   `aurora-context.json` containing markdown prose, which the F-3a Filter reads for its AD-10
   freshness decision and `system_status` reads too. Found at ER-1.3 and **deliberately not
   fixed** — pre-existing and outside that change's approved scope. The ER-1.3 emitter uses a
   pid-unique temp, so the new code cannot reproduce the pattern. Record:
   `09_logs/2026-07-17_ER1_3_projection_applied.md` §4.
10. **F-ER14-1 — the audit field `modelled` asserts more than it verifies. RESOLVED — ratified
    2026-07-17 as D-ER-14 (freeze Revision 4): renamed `registry_target`, applied at
    `ha_get_state` v0.2.1 with zero real audit lines carrying the old name; record
    `09_logs/2026-07-17_ER1_freeze_rev4.md`.** As recorded at ER-1.4a: spec §4 step 4 named
    the field and its own sentence scoped it to
    the registry, so the ER-1.4a implementation is faithful to the freeze. But the **name**
    claims *"the World Model models this entity"* while the field answers *"this id is a target
    in the resolution registry"* — and those differ, provably: `sun.sun` → `modelled: false`,
    while `environment/daylight-time.md` reads `binding: { ha_entity: sun.sun }`. The World
    Model models it; it is simply **unaliased**, so it is not a resolution target (D-ER-6).
    Not cosmetic — ER-1 exists partly because the audit log cannot distinguish a real actuation
    from an unverified write (spec §1.2), and a field whose name overstates what was checked is
    that same defect in a new place. Small today (one entity), structural tomorrow (every
    modelled-but-unaliased entity). **Recorded, not self-approved** — the name is frozen, and
    the D-ER-11/12/13 precedent is that implementation surfacing a gap in a frozen rule is
    ratified by the operator. Options: rename (`registry_target`, `resolvable`), or keep
    `modelled` and define it precisely in §4. The operator ratified the rename on 2026-07-17,
    before ER-1.4b — the point at which the field starts describing actuation rather than
    reads. Finding record: `09_logs/2026-07-17_ER1_4a_ha_get_state_applied.md` §4; resolution:
    `09_logs/2026-07-17_ER1_freeze_rev4.md`.
11. **H-4 — the Portainer `ai-local` stack must not be redeployed.** The stored stack
    definition and the running containers have diverged; a redeploy would drop the RTX-1.6
    endpoint, the Qdrant API key, `HA_LLAT`, the audit-log path and the `/opt/aurora` +
    `/opt/ingest` mounts. **Hazard record — read before touching Portainer:**
    [`../07_operations/hazards/portainer_ai_local_redeploy.md`](../07_operations/hazards/portainer_ai_local_redeploy.md).
    Source finding H-4 in `09_logs/2026-07-28_amarolab_technical_audit.md`; removed by M-B
    (convergence), which depends on I-3 and on F6.1 being closed. *(Pointer only — the full
    2026-07-28 audit reconciliation is I-7 and has not run.)*
