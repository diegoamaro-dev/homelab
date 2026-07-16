# ER-1 — Deterministic Entity Resolution (defect record + deferred remediation)

- **Date:** 2026-07-14   **Status:** **OPEN — deferred to a future gated phase (operator decision).**
- **Class:** defect record + accepted remediation direction. **Documentation only — no code,
  prompt, schema, loader, tool, database or architecture change has been made.**
- **Relation to Phase WM:** independent of WM-6 / G-F5-04. WM-6 validates awareness
  convergence and truthful communication (operator induces/restores manually via the HA UI);
  it does not validate natural-language actuation. ER-1 is **not** WM-5.5 — WM-5 is committed
  and published (`b2b04670`) and no work is retroactively inserted into it.
- **Supersedes in part:** the "secondary" `ha_get_state` id-hallucination note in R-F5-A
  ([`2026-07-01_phaseF_F5_3_applied.md`](2026-07-01_phaseF_F5_3_applied.md) §3.3) — promoted
  here to a standalone defect covering the **write** path as well.

## 1. Defect

Natural-language device requests (e.g. *"Enciende la impresora 3D"*) do not resolve to the
real entity id (`switch.impresora_3d`). The model invents plausible ids and, on the write
path, **HA returns HTTP 200 with an empty changed-states list for nonexistent entities**, which
`ha_call_service` v0.1.0 maps to `result_code:"ok"` — a **silent no-op reported as success**.

Evidence (live `amarolab-audit.log{,.1}`, 2026-06-16 → 2026-07-14): 30+ invented-id calls
since 2026-06-28 (`switch.3d_printer`, `switch.printer`, `switch.printer_3d`,
`switch.3dprinter`, `switch.prusa`, `cover.awning`, `binary_sensor.awning`, …). Operator
session 2026-07-14 18:03–18:17: `switch.3d_printer` → "ok" (no-op), `switch.3dprinter` →
"ok" (no-op), `switch.prusa` → "ok" (no-op); exact id `switch.impresora_3d` → real actuation.
Confirmed working: both HA tools, the D-12 allowlist, HA execution given the exact id.

## 2. Root cause

1. **No runtime source of real entity ids** — the F-1 `params.system` contains zero
   entity_ids (verified against `webui.db`); the injected Home State block carries friendly
   names only; the ids live solely in World Model `binding` fields the model never sees.
2. **Misleading tool docstring examples** (`light.kitchen`, `climate.lounge`) teach
   English-style guesses; the real id is Spanish (`impresora_3d`).
3. **No corrective feedback on writes** — HA 2xx + empty list → `"ok"`; the model cannot
   learn the id was wrong (reads at least return `not_found`).
4. **No resolution layer exists** between natural language and the tool boundary. The WM
   freeze anticipated the registry (architecture §7: real ids live in `binding`); it is not
   wired to the tools.

## 3. Accepted remediation direction (deferred — future gated phase)

Deterministic Entity Resolution Layer (ERL), design presented and broadly accepted
2026-07-14; **implementation deferred**. Summary:

- **A.** Additive optional `aliases` frontmatter field on World Model entities (es+en natural
  names); loader validates normalized-alias uniqueness fail-loud. No `schema_version` bump.
- **B.** Loader emits a resolution registry into `world_model.generated.json`; derived
  projection `aurora-entities.json` in `ai-stack/aurora/` (existing read-only bind mount —
  no container/config change). Gitignored, regenerable, no secrets.
- **C.** Deterministic closed lookup at the tool boundary (tool v-bump, contracts/ids/allowlist
  preserved; D-12 domain check remains first): normalize → exact-id fast path → alias
  substitution → on miss, **writes fail closed** (`unknown_entity` + bounded candidate list,
  no HTTP call) while **reads pass through** (HA 404 → honest `not_found`). No fuzzy matching,
  no scoring, no LLM in the loop. INV-17 untouched (aliases describe naming, never grant).
- **D.** Out of scope: frozen F-1 prompt, HA voice path (HA Assist has its own alias
  mechanism; printer intentionally not voice-exposed), allowlist changes.
- Decisions D-ER-1…4 (frontmatter as source; read/write asymmetry; same `entity_id`
  parameter accepts names; projection regenerated at loader emit) recorded as recommendations,
  to be ratified at the ER-1 freeze.

### ER-1-C1 — mandatory correction (operator-imposed, binding on the future implementation)

An HA HTTP 2xx with an empty response body **must not** be interpreted as "the entity was
already in the requested state" — the empty list is ambiguous. The write tool must **verify
the target entity state after the service call** (read-after-write, or before/after state
comparison) before reporting success or `state_changed:false`. If the requested state cannot
be verified, the tool returns an honest **unverified/failure** result — never a claimed
success. This replaces the optimistic empty-list interpretation in the original design draft.

## 4. Validation gates (sketch, for the future phase)

G-ER-1 loader alias validation/collision rejection · G-ER-2 resolution determinism on the
canonical phrase set · G-ER-3 fail-closed live replay of the real invented ids (zero HTTP
calls, audit lines) · G-ER-4 happy path via exact id **and** alias with read-after-write
verification (ER-1-C1) + baseline restore + refusal/rate-limit unchanged · G-ER-5 no WM/
awareness regression (AD-20/INV-18 not in play — the ERL never touches awareness).

## 5. Rollback (future phase)

Tools are single `webui.db` rows (restore committed v0.1.0 source + restart — D-WM5-5
pattern); `aliases` additive and revertable; projections regenerable.

## 6. Status

**ER-1 OPEN, deferred.** No change of any kind made in this session. ROADMAP slotting and
finding-register reconciliation belong to the ER-1 gated phase (or the next triad
reconciliation), not to the WM-6 gate session. WM-6 proceeds independently per the approved
runbook; G-F5-04 is judged only on awareness convergence and truthful communication.
