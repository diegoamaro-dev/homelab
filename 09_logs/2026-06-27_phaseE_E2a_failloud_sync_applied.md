# Phase E — E2-a — Fail-Loud Nightly Sync (F-01 exit-code remediation) — APPLIED

- **Date:** 2026-06-27
- **Phase step:** E2-a — correct the ingest sync exit-code semantics so a
  **disabled** corpus is an expected operational state (rc 0), not a failure,
  while preserving genuine failure signalling (rc 1).
- **Ecosystem:** AMAROLAB — Personal Innovation Lab and Digital Infrastructure Ecosystem.
- **Assistant:** AURORA — Personal AI Assistant for the AMAROLAB ecosystem.
- **Independent project:** Guardian Cloud — **untouched** (no code, config,
  container, git-tree or collection of Guardian Cloud was read-mutated; the
  `git` corpora were never pulled during validation).
- **Status:** **APPLIED.** Validation PASS on all four required criteria.
- **Scope:** ingest pipeline only — a single semantic change in
  [`../ai-stack/ingest/ingest/pipeline.py`](../ai-stack/ingest/ingest/pipeline.py).
  No `cli.py` change, no crontab change, no `openwebui` container recreate, no
  dependency change, no retrieval-behaviour change.
- **Finding:** F-01 (E-0 audit register §4) → backlog item **E2-a** (the
  run-health signal / cron rc-handling half is **E3-b**, not this step).

---

## 1. Context

The E-0 operational audit recorded finding **F-01** (Med-High):

> No working failure signal: disabled `myfreetour` is modeled as an *error* →
> `cmd_sync` returns rc=1 **every** run; the cron ignores rc. A real failure is
> indistinguishable from a normal run.

Root cause, in deployed code:

- [`pipeline.py`](../ai-stack/ingest/ingest/pipeline.py) `sync_corpus()` appended
  the disabled corpus to `rep.errors` (`"corpus disabled in corpora.yaml —
  skipped"`).
- [`cli.py`](../ai-stack/ingest/ingest/cli.py) `cmd_sync()` sets `rc = 1` for any
  corpus whose `rep.errors` is non-empty.

`myfreetour` is `enabled: false` ([`corpora.yaml`](../ai-stack/ingest/conf/corpora.yaml)),
so **every** full `ingest sync` returned rc=1. The exit code therefore carried no
information: a genuine failure (e.g. an enabled corpus whose path disappeared)
produced the same rc=1 as a perfectly healthy night.

## 2. Objective

Make the sync exit code trustworthy:

- A **disabled** corpus is an **expected** state → it must **not** make the run fail.
- A **genuine** failure (e.g. an enabled corpus with a missing path) must **still**
  produce rc 1.
- Existing **indexing behaviour** must be unchanged.

E2-a corrects the **semantics only**. It does **not** add operator-facing summary
output (deliberately deferred — separate concern) and does **not** make the cron
act on rc (that is E3-b).

## 3. Decision

- **D-E2a-A — Model "disabled" as an expected skip, not an error.** Add a nullable
  `skipped_reason: str | None` field to `CorpusReport`; the disabled branch sets
  `rep.skipped_reason` and records **no** error. The `cmd_sync` rc rule
  (`if rep.errors: rc = 1`) is then correct unchanged — `cli.py` is **not** edited.
- **D-E2a-B — Preserve every other failure channel verbatim.** The
  `path does not exist` branch still appends to `rep.errors` (genuine failure);
  git-pull degradation (dirty tree / pull failure) still degrades silently as
  designed; uncaught exceptions still propagate. No try/except was added (out of
  scope — that is run-health, E3-b).

### Exit-code contract (now documented)

| rc | Meaning |
|---:|---|
| 0 | Completed; no **enabled** corpus failed. Expected skips (disabled corpora) are reported in `skipped_reason` and do **not** affect rc. |
| 1 | At least one **enabled** corpus reported a real error (e.g. path does not exist). |
| 2 | Usage error (unknown `--collection`, `drop` without `--yes`). Unchanged. |

## 4. Implementation

Single file, two hunks (`git diff --stat`: `1 file changed, 5 insertions(+), 1 deletion(-)`):

```diff
@@ class CorpusReport:
     files_deleted: int = 0
     points_deleted: int = 0
+    skipped_reason: str | None = None
     errors: list[str] = field(default_factory=list)

@@ def sync_corpus(...):
     rep = CorpusReport(name=corpus.name)
     if not corpus.enabled:
-        rep.errors.append("corpus disabled in corpora.yaml — skipped")
+        # A disabled corpus (e.g. the myfreetour placeholder) is an expected
+        # operational state, not a failure: record it as a skip so the run's
+        # exit code stays 0. Genuine problems below still populate errors.
+        rep.skipped_reason = "disabled in corpora.yaml"
         return rep
     if not corpus.path.exists():
         rep.errors.append(f"path does not exist: {corpus.path}")
         return rep
```

The entire indexing body (walk → chunk → content_sha compare → embed → upsert →
shrink-handling → GC) is **untouched**.

### Deployment reality

- The ingest venv is an **editable install** (`pip install -e .`), so the nightly
  cron (`30 2 * * *`, host venv) picks up this source change immediately — no
  reinstall.
- The ingest tree is also bind-mounted read-only into the `openwebui` container at
  `/opt/ingest` (L-RTX-5). The query path — `rag_search.py` — imports only
  `ingest.embedder` and `ingest.reranker`; `ingest/__init__.py` is empty. It
  **never** imports `sync_corpus`/`cmd_sync`. The changed symbols are not on the
  retrieval path, so **no `openwebui` container recreate is required** and
  retrieval behaviour is unchanged.

## 5. Validation (real evidence — zero Qdrant mutation)

Baselines captured **before** the edit; re-run after. All sync probes used
`--dry-run` on `fs`/disabled corpora only, so no `git` corpus was pulled and no
vector was written.

| # | Criterion | Command / method | Before | After |
|---|---|---|---|---|
| V1 | **Disabled ≠ failure** (req 1, 3) | `bin/ingest sync --collection myfreetour --dry-run; echo $?` | **rc=1**, `errors=["corpus disabled…"]` | **rc=0**, `skipped_reason="disabled in corpora.yaml"`, `errors=[]` |
| V2 | **Genuine failure still fails** (req 2, 3) | real `cmd_sync` over a temp config: one disabled corpus + one **enabled** corpus at a non-existent path | — | **rc=1**; disabled→`skipped_reason` (no error), enabled-missing→`errors=["path does not exist…"]` |
| V3 | **Indexing unchanged** (req 4) | `bin/ingest sync --collection homelab_docs --dry-run`, before vs after | 157 seen / 137 unchanged / 20 changed / 3881 chunks / `errors=[]` | identical on every counter; sole report delta is the additive `skipped_reason: null` field |
| V4 | **Zero mutation** (req 4) | `bin/ingest status`, before vs after | `4049 / 872 / 419 / 0 / 280` | identical |

- **V2** is decisive for the semantics: in a **single** run the disabled corpus
  contributes **no** failure while the genuine missing-path corpus drives rc=1.
- A full non-dry-run `ingest sync` was **deliberately not** run (it mutates Qdrant
  and pulls the Guardian Cloud / Ensambla2 git trees). The healthy-night result
  (rc=0 with `myfreetour` disabled) is entailed by V1 (disabled→0) and V2 (the rc
  loop aggregates: a skip contributes 0, a real error contributes 1).

## 6. Outcome & residual

- F-01's E2-a half is **resolved**: the nightly sync exit code is now a reliable
  failure signal — disabled corpora no longer raise a false rc=1, and genuine
  failures still surface as rc=1.
- **Residual (tracked, not E2-a):** the cron still `>>`-appends output and does not
  *act* on rc; wiring rc into a run-health/alerting signal is **E3-b** (F-01's
  second half). Adding operator-facing run summary output is a separate,
  deferred improvement.
- **Not touched in E2-a:** E2-b (version pin/unify — conditional, blocked on E5-a),
  E2-c (run-lock, F-08).

## 7. References

- E-0 audit register (F-01):
  [`2026-06-27_phaseE_E0_operational_audit_report.md`](2026-06-27_phaseE_E0_operational_audit_report.md).
- Platform contract:
  [`../04_ai_system/knowledge_platform_contract.md`](../04_ai_system/knowledge_platform_contract.md).
- Ingest service:
  [`../ai-stack/ingest/README.md`](../ai-stack/ingest/README.md).
- Operational source of truth:
  [`../00_overview/CURRENT_STATE.md`](../00_overview/CURRENT_STATE.md).
