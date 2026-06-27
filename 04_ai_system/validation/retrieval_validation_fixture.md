# Retrieval Validation Fixture

- **Status:** Permanent, stable. Project documentation (Phase E — Knowledge
  Platform Foundation, step E-5).
- **Authoritative source:** [`retrieval_validation_fixture.yaml`](retrieval_validation_fixture.yaml).
  This document describes and snapshots it; **the YAML wins** if they ever
  disagree.
- **Created:** 2026-06-27 (E5-a).

---

## Purpose

A fixed, representative query corpus for every Phase E **E-5** retrieval
validation run, so results are comparable run-to-run:

- **E5-a** — version-skew **drift measurement** (this fixture's first use).
- **E5-b** — Qdrant **restore drill** (retrieval before vs after a restore).
- **E5-c** — controlled audit-log / retrieval checks.
- any future retrieval-regression check.

Retrieval validation is only meaningful if the queries never move. An ad-hoc
set makes a "no drift / unchanged" conclusion unfalsifiable. This fixture
freezes the corpus.

## Stability contract (binding)

- Existing query `id`s and `query` text are **fixed** — never edit or delete
  an entry; that silently breaks run-to-run comparability.
- You **may append** a new entry (new `id`) with a documented reason; the
  existing entries stay byte-stable.
- `myfreetour` is intentionally **absent** (empty/disabled placeholder, 0
  points). It earns fixture entries only once a real corpus is onboarded.

## Coverage

16 queries — **4 per populated collection**, **8 Spanish + 8 English**:

| Collection | Queries | Langs |
|---|---|---|
| `homelab_docs` | HL-01 … HL-04 | 2 es / 2 en |
| `guardian_cloud` | GC-01 … GC-04 | 2 es / 2 en |
| `ensambla2` | E2-01 … E2-04 | 2 es / 2 en |
| `infra_audits` | IA-01 … IA-04 | 2 es / 2 en |

Selection criteria: cover every populated collection; both languages where
appropriate (AURORA is used primarily in es-ES over largely English technical
docs); representative of real usage; intentionally small; phrased to return
non-empty results so ranking is actually exercised.

## Schema

Each entry: `id` (stable `PREFIX-NN`), `collection` (one of the 4 populated),
`lang` (`es`|`en`), `query` (2–500 chars). E5 prefixes (`query:` / `passage:`)
are added by `ingest/embedder.py` at embed time, **not** stored here.

## How a run uses it

The companion harness
[`measure_retrieval_drift.py`](measure_retrieval_drift.py) loads this fixture,
embeds each query under both library stacks, and compares retrieval. See the
E5-a apply log for the first run's methodology and evidence:
[`../../09_logs/2026-06-27_phaseE_E5a_drift_measurement.md`](../../09_logs/2026-06-27_phaseE_E5a_drift_measurement.md).

> Snapshot of the queries lives in the YAML; this doc deliberately does not
> duplicate the text to avoid drift between the two files.
