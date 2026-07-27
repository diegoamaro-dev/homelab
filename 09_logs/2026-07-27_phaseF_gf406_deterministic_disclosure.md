# G-F4-06 closure — deterministic same-night disclosure (F-3a `outlet`)

- **Phase / gate:** F — Operational Intelligence · **G-F4-06** (authority:
  [`04_ai_system/phase_f_architecture.md`](../04_ai_system/phase_f_architecture.md)
  §9-F-4, AD-04 / AF-04).
- **Date:** 2026-07-27.
- **Scope:** make the **mandatory** AD-04 same-night disclosure hold every time and
  mark **G-F4-06 PASS**. No tool code / description / schema / registration change.
  **STOP at the git gate.**
- **Status:** **G-F4-06 = PASS** on real browser evidence. **F-4 NOT closed** —
  **G-F4-08** (empirical restic durability, operator/root) is the final blocking gate.

## Problem

G-F4-06 requires two **mandatory** conjuncts for "¿qué pasó anoche?": (a) answer from
`system_status`, and (b) Aurora states the same-night digest is not yet RAG-retrievable
(AD-04, ~22 h indexing lag). Routing (a) was fixable in the prompt; the disclosure (b)
was not — see below.

## Implementation (two layers)

1. **Routing** — `params.system` (`webui.db`, runtime, not git). The `# Routing` recap
   clause + `# Context` now send a recent-night recap to `system_status`, not
   `rag_search`. This corrected the original misroute.
2. **Disclosure** — F-3a Filter `aurora_context` **v0.1.0 → v0.2.0** (`function` table,
   runtime; repo source [`ai-stack/openwebui-tools/filters/aurora_context.py`](../ai-stack/openwebui-tools/filters/aurora_context.py)
   synced). Prompt-only reinforcement **failed twice** on `qwen2.5:7b-instruct` — the
   `# Style` "answer-first / concise" directive prunes the sentence — so the guarantee
   was moved into deterministic orchestration. The new fail-closed `outlet` appends the
   disclosure **iff**: the answer's source is `system_status` **and** the question is a
   recent-night recap **and** it is not already present. `inlet` unchanged; never raises.
   - Historical answers route to `rag_search` (source `rag_search/rag_search`) and are
     therefore **structurally excluded** — the "never trigger for historical" guarantee.
   - Appended sentence (ES): *"El resumen operativo de esta noche aún no es consultable
     mediante rag_search (~22 h de retardo de indexado); esta respuesta procede de
     system_status."*

## Validation

- **Offline — 12/12 deterministic unit tests:** same-night ES/EN append; historical
  `rag_search` **not** touched; `anoche`+`rag_search`-source **not** appended (no
  papering over a misroute); live-health non-recap **not** appended; idempotent (×2 →
  one sentence); multi-turn targets the current answer; valve-off no-op; never raises;
  `inlet` intact.
- **Authoritative browser (operator, 2026-07-27):**
  - **Same-night** `¿Qué pasó anoche?` (chat `9628cbe6`) — source
    `system_status/system_status`; **no** `rag_search` audit entry; latest cycle
    summarized; **disclosure present** (exact ES sentence above).
  - **Control** `¿Qué pasó la noche del 20 de julio de 2026?` (chat `1ddc6f84`) — source
    `rag_search/rag_search`; audit line 94 = `rag_search ops_digests "20 de julio de
    2026"`; retrieved the **correct** `2026-07-20_ops_digest.md`; **disclosure absent**.
  - → both G-F4-06 conjuncts satisfied; control clean. **G-F4-06 = PASS.**

## Decisions

- **Prompt → deterministic** (operator-approved 2026-07-27). A mandatory-every-time
  guarantee cannot rest on a probabilistic 7B. The **gate wording was not weakened**;
  the disclosure was relocated to deterministic code.
- **Gate discipline preserved** — G-F4-06 was held FAIL until every conjunct passed on
  real evidence.

## Lessons learned

Mandatory operational guarantees must not depend solely on probabilistic LLM prompting.
When a requirement must hold every time, it belongs in deterministic orchestration.

## Rollback

- **Soft (no restart):** Open WebUI → `aurora_context` Valves →
  `same_night_disclosure = False` → the `outlet` is a no-op (`inlet` + context injection
  unaffected).
- **Full:** restore the prior `function.content` (pre-outlet, sha256 `23cf205f…`) via a
  guarded `sqlite3` UPDATE + `git checkout --` the repo Filter file +
  `docker restart openwebui`.
- The routing edits revert independently in `params.system`.

## Git gate (STOP — operator approval required before any git command)

Pending working-tree changes for review:

- `ai-stack/openwebui-tools/filters/aurora_context.py` — F-3a `outlet` (v0.2.0).
- `04_ai_system/phase_f_architecture.md` — G-F4-06 PASS + as-built status note + §15
  revision entry.
- `09_logs/2026-07-27_phaseF_gf406_deterministic_disclosure.md` — this log.

Runtime-only (never git): `params.system` routing edits + `function.content` `outlet`
(both in `webui.db`); the browser chat records; the audit log.
