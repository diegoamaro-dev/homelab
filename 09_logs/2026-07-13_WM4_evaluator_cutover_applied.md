# WM-4 — Evaluator cutover (World Model consumes; `HOME_RULES` retired) — apply log

- **Date:** 2026-07-13
- **Phase:** WM-4 (evaluation engine consumes the compiled World Model; retire `HOME_RULES`)
- **Architecture of record:** [`../04_ai_system/world_model_architecture.md`](../04_ai_system/world_model_architecture.md)
  (AD-21, FROZEN) §6 M4 / §9 WM-4 · ROADMAP → Phase WM.
- **Entry state:** HEAD `86ae969e` (2026-07-10 reconciliation), tree clean, origin/main in sync; WM-3 parity harness green.
- **Status:** implemented + validated; **STOPPED at the git gate** (not committed/pushed/tagged).

## 1. Implementation

- **`04_ai_system/world_model/_evaluator/`** — the authoritative Awareness engine (stage ④),
  a dedicated package by operator decision: **`_loader/` compiles, `_evaluator/` evaluates**
  (architectural separation). `engine.py`: backend-agnostic `eval_node` AST core (INV-WM3-A)
  + `HAContext` adapter (self-contained D7 extraction; tz-anchored windows per frozen §4.5)
  + `evaluate_model` + `load_artifact` (artifact-version guard, fail-loud `ArtifactError`).
  Stdlib only; the engine reads `world_model.generated.json` and **never invokes the loader**
  (nightly path stays compile-free; retain-last-good by loader contract).
- **`bin/aurora-context` cutover** — the home section now loads the artifact and calls
  `evaluate_model` (INV-19: no consumer builds awareness from raw signals); collector
  (`/api/states` fetch) and `render_home` surface rendering unchanged. `HOME_RULES`
  transcription (`detect_home`, battery roster, extraction helpers) **removed**. Guarded
  import + `ArtifactError` fail-soft: evaluator/artifact failure degrades the home block to
  Unavailable with a truthful `Reason:` line (`render_home` now takes the reason; the
  HA-unreachable rendering is byte-identical to before); every other section still renders,
  rc stays 0 (RF5-3).
- **Parity harness retired** — `_loader/parity/` + `test_parity_equivalence.py` deleted with
  `HOME_RULES` (its G-WM3-6 oracle anchored on the retired detector). The 32 boundary
  snapshots migrated to **`_evaluator/tests/`** as a regression suite with expectations
  **frozen from the final differential run** (`expected.py`); 14 engine unit tests added.
- **`home_model.md` → redirect/overview** (M4 — links survive): superseded notice + mapping
  table to the canonical `world_model/` locations; full text preserved in git history.

## 2. Decisions

- **D-WM4-1** — dedicated `_evaluator/` package; loader compile-only (operator, this session).
- **D-WM4-2** — consumers read the emitted artifact; no loader invocation at runtime (operator).
- **D-WM4-3** — `overall_status` stays **platform-only** through WM-4; the §1.5 aggregate
  verdict lands at WM-5 with consumer convergence (operator). D2 supersession unchanged (W-11).
- **D-WM4-4** — artifact-failure degrade reuses the `ha_unavailable` token (frozen §7 vocabulary,
  whole-block Unavailable) but states the truthful reason in the md `Reason:` line — a state
  that could not previously exist; all previously-possible outputs are byte-identical.
- **D-WM4-5** — windows evaluated tz-anchored from the window's own declared `tz` (frozen §4.5);
  behaviour identical to the retired host-local computation for `overnight`/Europe/Madrid.

## 3. Validation gates

| Gate | Result |
|---|---|
| G-WM4-1 pre-cutover differential (engine ≡ `detect_home`) | **PASS** — 32/32 synthetic + **live real-data MATCH** (130 real entities; real active `plant_water_warning` reproduced identically) |
| G-WM4-2 cutover output equivalence (old vs new script, sandboxed, real signals + live HA, back-to-back) | **PASS** — `aurora-context.{json,md,voice}` byte-identical modulo timestamps; dry-run home block identical; HA-unreachable rehearsal identical under same sabotage |
| G-WM4-3 `aurora-context.json` schema (AD-20 / INV-18) | **PASS** — `schema_version` 1, all sections, `home.anomalies` list of plain string tokens |
| G-WM4-4 `generate-digest` consumes the new context | **PASS** — dry-run rc 0; digest identical from old-ctx vs new-ctx; real home anomaly rendered |
| G-WM4-5 F-3a Filter + `system_status` untouched | **PASS** — zero diff under `ai-stack/openwebui-tools/`; md block format proven identical (G-WM4-2) |
| Artifact-failure fail-soft rehearsal | **PASS** — artifact removed → home block Unavailable (truthful reason), platform sections intact, rc 0; artifact restored |
| Test suites | **PASS** — `_loader` 19/19 · `_evaluator` 15/15 (incl. the 32-snapshot regression) |
| First real production run post-cutover (attended) | **PASS** — 2026-07-13 14:37 UTC; `home.anomalies=["plant_water_warning"]`, schema intact, Filter serves the engine-produced context |
| **G-WM4-6 first unattended nightly cycle** | **OPEN — close-when:** the 2026-07-14 04:15 `aurora-context` + 04:25 `generate-digest` cron runs produce a valid context + digest (real evidence; check `ai-stack/ingest/logs/aurora-signals.log` and `09_ops/runtime/2026-07-14_ops_digest.md` next morning) |

Artifact regenerated at entry (`python3 -m _loader.cli`, docs_commit `86ae969e`). Real HA
snapshots used in-memory only, never persisted (AD-18). No synthetic evidence closes any gate;
the 32 snapshots are unit-test fixtures, expectations frozen from the retiring detector.

## 4. Invariant check

AD-21 conformance (loader/evaluator separation per §1.3 ③/④); **AD-20 / INV-18 preserved**
(schema + typed tokens unchanged; digest + Filter contracts proven); **INV-17 untouched**
(evaluator is read-only awareness; no action surface); **INV-19 now live** (the only home
awareness constructor is the model evaluation); B3 intact (evaluation is a pure function of
artifact + signals + now; duration via `last_changed` in the current signal). Consumers
(voice line, `system_status`) intentionally untouched — WM-5.

## 5. Rollback

Pre-commit: discard the working tree (restores `HOME_RULES` + parity harness). Post-commit:
`git revert` the WM-4 commit. The artifact is gitignored/regenerable; a broken artifact
fail-softs the home block only. No cron, HA, prompt, container, or DB change was made.

## 6. Git gate — STOP

Change set: `04_ai_system/world_model/_evaluator/**` (new) · `bin/aurora-context` (cutover) ·
`_loader/parity/**` + `test_parity_equivalence.py` (deleted) · `_loader/__init__.py` (docstring) ·
`home_model.md` (redirect) · `world_model/README.md` · triad · this log · E5-a scope caveat
(2026-06-27 queued operator decision) in `knowledge_platform_contract.md` + dated addendum in
the E5-a apply log. **No git operation performed.** Next: WM-5 (consumer convergence).
