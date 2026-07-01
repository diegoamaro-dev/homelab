# WM-3 — World Model loader/compiler — apply log

- **Date:** 2026-07-02
- **Phase:** WM-3 (Loader/compiler; parallel to `HOME_RULES`)
- **Architecture of record:** [`../04_ai_system/world_model_architecture.md`](../04_ai_system/world_model_architecture.md)
  (AD-21, FROZEN) §4.8 · operative contract
  [`../04_ai_system/world_model/_schema/entity.schema.md`](../04_ai_system/world_model/_schema/entity.schema.md) · ROADMAP → Phase WM.
- **Entry state:** HEAD `954735c1` (WM-2), tree clean, origin/main in sync.
- **Status:** implemented + validated; **STOPPED at the git gate** (not committed/pushed/tagged).

## 1. Implementation

Deterministic loader at **`04_ai_system/world_model/_loader/`** compiling the 15 canonical
docs → gitignored **`world_model.generated.json`**, pipeline
**Parse → Resolve → Normalize → Validate → Emit**. Read-only w.r.t. the docs; does not
evaluate live state (that is WM-4). Non-load-bearing: `HOME_RULES`/`detect_home()` remain
the live path (cutover is WM-4).

Modules (26 tracked files): `parse · grammar · ast · registry · model · resolve · normalize ·
authorization · validate · emit · cli`; parity harness `parity/{hostmod,evaluator,snapshots,oracle}`;
`tests/` (8 suites). PyYAML available; stdlib otherwise.

## 2. Locked decisions

- **INV-WM3-A** — the rule **AST is backend-agnostic** (canonical rule language); no HA/`detect_home`/
  evaluator specifics; every evaluator consumes the same AST. `ast.py` = pure data + contract; all
  state resolution lives in the evaluator adapter (`parity/evaluator.py::HAContext`). Binds WM-4.
- **Normalize stage** (between Resolve and Validate): N1 casefold string `==`/`!=`; N2 bind D7
  `on_absent=false` (incl. `!=`); N3 duration→seconds; N4 window canonical; N5 baseline uniform;
  N6 battery fold; N7 emission-order/`id` sort; N8 id/token trim.
- **`for`-suffix grammar** — `field COMP value 'for' DURATION` desugars to `And(Cmp, Duration)` on the
  same field (frozen example + `detect_home` reality).
- **`field unavailable` ≡ `state == "unavailable"` exactly** (not `unknown`), matching the bridge's
  `in ("off","unavailable")`.
- **YAML** — strict loader: only `true`/`false` are booleans, so `{ state: off }` stays the string
  `"off"` (avoids YAML-1.1 `off→False`).
- **Authorization (11a / INV-17)** — `authorization.py` mirrors the D-12 `_ALLOWED_DOMAINS` from
  `ai-stack/openwebui-tools/tools/ha_call_service.py` as a **descriptive** subset check; never a grant.

## 3. Validation gates

| Gate | Result |
|---|---|
| G-WM3-1 parse/emit all 15 docs, exit 0 | **PASS** (9 entities, 9 rules, 9 tokens) |
| G-WM3-2 fail-loud + retain last-good | **PASS** (`test_failloud`) |
| G-WM3-3 determinism/idempotence (modulo `generated_at`) | **PASS** (byte-identical) |
| G-WM3-4 AD-18 secret-safety | **PASS** (real tree clean; planted IPv4/JWT rejected) |
| G-WM3-5 schema conformance (11 passes) | **PASS** (`test_validate`) |
| **G-WM3-6 real-data parity (M3)** | **PASS** — engine-equivalence **32/32** synthetic snapshots + **live real-data MATCH** (130 real entities; real anomaly `awning_left_extended` reproduced identically by loader and `detect_home`) |
| G-WM3-7 read-only w.r.t. docs | **PASS** (no `.md` modified) |
| G-WM3-9/10 loader-TCB + Normalize unit tests | **PASS** (20/20 tests) |

Parity oracle: `python3 -m _loader.parity.oracle`. Tests:
`python3 -m unittest discover -s _loader/tests -t 04_ai_system/world_model` (PYTHONPATH = `04_ai_system/world_model`).
Real snapshots are used in-memory only, never persisted (AD-18).

## 4. Rollback

Non-load-bearing. Artifact is gitignored/regenerable (delete = no-op operationally; `HOME_RULES`
unaffected). Pre-commit: discard working tree. Post-commit: `git revert` the loader commit. A failed
run writes nothing and retains last-good.

## 5. Git gate — STOP

Change set: `04_ai_system/world_model/_loader/**` (26 files) + this log + README/triad reconciliation.
Artifact `world_model.generated.json` gitignored (`.gitignore:71`). **No git operation performed.**
Next: WM-4 (evaluation engine consumes the model; retire `HOME_RULES`; AD-20/INV-18 preserved).
