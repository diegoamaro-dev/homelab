# WM-5 — Consumer convergence (world verdict; every surface a projection) — apply log

- **Date:** 2026-07-14   **Phase:** WM-5 (§9 · AD-21 §1.5/§7 · AD-WM5-1)
- **Authority:** [`../04_ai_system/world_model_architecture.md`](../04_ai_system/world_model_architecture.md) · [`../04_ai_system/phase_f_architecture.md`](../04_ai_system/phase_f_architecture.md) §4D · ROADMAP → Phase WM.
- **Entry state:** HEAD `476e0ae8` (WM-4); **G-WM4-6 PASS / closed 2026-07-14** (first unattended cycle — see [`2026-07-13_WM4_evaluator_cutover_applied.md`](2026-07-13_WM4_evaluator_cutover_applied.md)). Artifact regenerated.
- **Status:** implemented + validated on real data; **STOPPED at the git gate** (not committed/pushed/tagged). One runtime step (system_status `webui.db` install) staged, operator-gated.

## 1. Implementation (additive)
- **`_evaluator/verdict.py`** (new) — `aggregate_verdict` / `to_overall_status` / `worst_verdict` + the AD-WM5-1 ladder. Pure (B3).
- **`_evaluator/engine.py`** — `evaluate_world() -> Awareness` (anomalies enriched with tier + region; per-region verdicts); `evaluate_model()` kept as the byte-identical compatibility shim (32-snapshot pin); re-exports the verdict API. `__init__.py` exports the new surface.
- **`bin/aurora-context`** — home section reads `evaluate_world`; the world verdict folds the home region verdict + the injected `infrastructure` pseudo-region via `aggregate_verdict` → `overall_status = to_overall_status(world.verdict)`; additive `world: {verdict, regions}` in the JSON (`home.anomalies` unchanged — AD-20); voice line home-aware with the deterministic top-N + "+K more" ≤200 cap (W-10); dry-run instrumented.
- **`system_status` v0.3.0** ([`../ai-stack/ingest/docs/system_status_tool.py`](../ai-stack/ingest/docs/system_status_tool.py)) — folds the home region verdict into Overall/Reasons and echoes the md Home State block (D-1; D1-preserving). **Not yet installed to `webui.db`** (§6).
- **F-3a Filter, `push-voice-context`, `params.system`** — unchanged (verified byte-identical / no change).

## 2. Decisions
- **AD-WM5-1** (unknown precedence) — ratified 2026-07-13; recorded `phase_f_architecture.md` §4D.
- **D-WM5-2** — `infrastructure` pseudo-region key (stable into WM-7; source changes, contract does not).
- **D-WM5-3** — `world.anomalies` + multi-region voice allocation deferred to the first second anomaly-producing region (W-10/W-14).
- **D-WM5-4** — `overall_status` is now the coarse projection of `world.verdict` (supersedes D2 / closes W-11); enum unchanged (`ok|degraded|unknown`).
- **D-WM5-5** — the system_status `webui.db` install **was performed 2026-07-14 (operator-approved)**: OWUI stopped → `sqlite3` UPDATE `tool.content` (id `system_status`) → OWUI started (`journal_mode=delete`, so stop/start avoids lock contention). v0.2.0 row backed up; rollback = restore the v0.2.0 content (committed source) + restart. Browser-UI model-routing remains a human confirmation.

## 3. Validation gates (real data; no fabrication)
| Gate | Result |
|---|---|
| G-WM5-1 evaluator + AD-WM5-1 truth table | **PASS** — `_evaluator` 36/36 (incl. the 32-snapshot regression via the shim), `_loader` 19/19 |
| G-WM5-2 aurora-context world block + non-regression | **PASS** — sandboxed old-vs-new differential (real signals + live HA): **only** the additive `world` block added; `home.anomalies` / platform sections / md byte-identical; voice home-aware, ≤200 |
| G-WM5-2b "silence is informative" (§1.5) | **PASS** — real platform-ok + home-low → `world.verdict=low`, `overall_status=ok`, plant **listed** (not escalated) |
| G-WM5-3 system_status home-aware | **PASS** — v0.3.0 **installed to the live `webui.db` + verified on the running assistant** (2026-07-14): tool present (v0.3.0), loads clean (OWUI `Up (healthy)`, no tool-load error), executes in-container against `/opt/aurora`, **Home State block returned**; no regression (qwen2.5 `toolIds` + F-1 `params.system` + all 8 tool rows intact). Browser-UI model-routing = human confirmation. |
| G-WM5-4 INV-18 / AD-20 non-regression | **PASS** — generate-digest consumes the world-block context (rc 0, valid digest, `home anomalies: plant_water_warning`); Filter byte-identical; digest ignores `world.*` |
| G-WM5-5 cross-surface convergence | **PASS (real snapshot)** — md home block · system_status · voice · `overall_status` · `world.verdict` all agree (home low, listed, overall ok); Filter injects the home-aware md |

Escalation direction (home ≥ medium → degraded) is unit-proven (G-WM5-1) and recurs on real data at the overnight awning window; the real induced-anomaly end-to-end across chat + voice is **WM-6 / G-F5-04** (out of WM-5 scope).

## 4. Invariant check
**AD-20 / INV-18 preserved** (`home.anomalies` typed-token list unchanged; digest + Filter contracts proven on real data). **INV-19** (every surface projects the one evaluation; the aggregate lives in `_evaluator/`, not in any consumer). **B3** (the verdict is a pure function of artifact + signals + now). **D1** (device detail only in the md rendering). **INV-17** untouched (the evaluator is read-only awareness; no action surface). G-F5-04 remains open → WM-6.

## 5. Rollback
Pre-commit: `git checkout --` the modified tracked files + delete the three new `_evaluator` files (restores WM-4). system_status is **not yet installed** — no runtime rollback needed; if installed, restore the committed v0.2.0 source into `webui.db` + `docker restart openwebui`. The artifact is gitignored/regenerable; a broken artifact fail-softs the home block only. No cron, HA, prompt, container, or DB change has been made.

## 6. Git gate — STOP
Change set: `_evaluator/{verdict.py, engine.py, __init__.py, tests/test_verdict.py, tests/test_awareness.py}` · `bin/aurora-context` · `system_status_tool.py` · `phase_f_architecture.md` (§4D) · the WM-4 apply log (G-WM4-6 closure) · triad + `world_model/README.md` (reconciled) · this log. **No git operation performed.** Runtime deployment **done 2026-07-14**: system_status v0.3.0 installed to `webui.db` + verified on the running assistant (Home State block returned; no regression). Remaining: (a) human browser-UI confirmation that the model routes a home query to the tool; (b) **WM-6** — reopen & close **G-F5-04** on a real induced anomaly (chat + voice), the R-F5-A closure. The live `aurora-context.{json,md,voice}` refresh to the WM-5 format at the next 02:15 cron (then `overall_status` folds home too).
