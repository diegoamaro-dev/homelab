# 04 — AI system

Everything in the local LLM + RAG + assistant stack lives here.

## Layout

```
04_ai_system/
├── README.md                                  ← this file
├── openwebui.md                               Open WebUI inventory + config
├── ollama.md                                  Ollama inventory + models on disk
├── qdrant.md                                  Qdrant inventory + collections
├── amarolab-v1/                               Design package for Amarolab Assistant v1
│   ├── README.md
│   ├── 01-current-state-review.md
│   ├── 02-target-architecture.md
│   ├── 03-tools.md
│   ├── 04-security-and-permissions.md
│   └── 05-implementation-roadmap.md
├── rag-audits/                                Per-collection retrieval-quality benchmarks
│   ├── guardian-cloud-baseline.md             Phase 1 baseline (dense only)
│   ├── guardian-cloud-reranked.md             Phase 1.5 with bge-reranker-v2-m3
│   └── scripts/                               Reproducible benchmark scripts
│       ├── gc_benchmark_baseline.py
│       └── gc_benchmark_reranked.py
└── _design-history/                           Superseded designs kept for archaeology
    └── phase3-2026-06-13/                     Original Phase 3 sketch (superseded by amarolab-v1/)
        ├── README.md
        ├── 01-architecture.md
        ├── 02-data-flow.md
        ├── 03-integrations.md
        ├── 04-security-model.md
        ├── 05-resource-requirements.md
        └── 06-implementation-plan.md
```

## Where the actual code lives

The **implementation** code is **not** in this category — it lives
under the top-level `ai-stack/` directory (a separate dir at the repo
root):

| Path | What |
|------|------|
| `../ai-stack/ingest/` | `homelab-rag-ingest` Python service (Phase 1 implementation) |
| `../ai-stack/data/qdrant/` | Qdrant on-disk storage (runtime, gitignored) |
| `../ai-stack/.env` | Secrets — Qdrant API key, Open WebUI secret, etc. (gitignored) |

This split — *docs* in numbered category dirs, *code* in
top-level service dirs — is the repo's convention.

## Where to start reading

- New here? Read `openwebui.md`, `ollama.md`, `qdrant.md` (~10 min)
  to understand the three running components.
- Building the assistant? Start with
  [`amarolab-v1/README.md`](amarolab-v1/README.md), then
  [`amarolab-v1/05-implementation-roadmap.md`](amarolab-v1/05-implementation-roadmap.md).
- Measuring RAG quality? See
  [`rag-audits/guardian-cloud-reranked.md`](rag-audits/guardian-cloud-reranked.md)
  for the canonical baseline.
- Investigating a past decision?
  [`_design-history/phase3-2026-06-13/`](_design-history/phase3-2026-06-13/)
  holds the pre-Phase-1 design that `amarolab-v1/` superseded.

## Snapshot date

Component docs (`openwebui.md`, `ollama.md`, `qdrant.md`) and the
benchmark results were captured during the 2026-06-13 → 2026-06-14
audit + Phase 1 work. They are snapshots — refresh per audit cycle.
The application logs that record what was actually deployed live in
`../09_logs/` (look for the dated entries from 2026-06-13 onwards).
