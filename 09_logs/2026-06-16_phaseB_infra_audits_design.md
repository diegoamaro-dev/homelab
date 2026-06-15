# Phase B: `infra_audits` Corpus Design

**Date:** 2026-06-16

This document defines the architecture, structure, and operational strategy for the `infra_audits` corpus, fulfilling the Phase B deliverable for homelab audit querying.

## 1. Corpus Structure

The corpus is sourced from the localized directory of the recent server audit snapshot. After the previous documentation migration to the git repo, this directory retains the immutable metadata, reports, and generated output that describe the audit execution.

- **Source Path:** `/home/diego/server-audit-2026-06-13`
- **Primary Content:**
  - `SANITIZATION_REPORT.md`: Line-level security redactions and rules.
  - `CONSOLIDATION_PLAN.md`: Directory mapping, metadata strategies, and move lists.
  - `DOCUMENTATION_SYNC_PLAN.md`: Historical execution steps.
  - `MIGRATION_REPORT.md` / `GITHUB_COMMIT_PLAN.md`: Commit-level recipes and execution traces.
  - `INGEST_REPO_REVIEW.md`: Details about ingest repo structure.

## 2. Document Ingestion Rules

The ingest pipeline will be instructed to pull Markdown documents while explicitly skipping JSON benchmark data and temporary state dumps. The stanza to be added to `ai-stack/ingest/conf/corpora.yaml` is:

```yaml
- name: infra_audits
  type: fs
  path: /home/diego/server-audit-2026-06-13
  include:
    - "**/*.md"
  exclude:
    - "**/inspect-snapshots/**"
    - "**/*.json"
  enabled: true
```
This guarantees that only the 6 core structural Markdown documents (and any future Markdown-based reports in that directory) are indexed.

## 3. Metadata Schema

The Qdrant vector payload will adopt the existing homelab standard for metadata to ensure compatibility with `rag_search`.

- `collection`: "infra_audits" (used for payload-based filtering).
- `source_kind`: "markdown" (derived from the file extension).
- `source_rel`: The relative path of the file from the root directory (e.g., `SANITIZATION_REPORT.md`).
- `title`: Extracted dynamically by the chunker from the first H1 (`# `) or H2 (`## `), falling back to the filename if no headers are present.

Qdrant payload indexes are maintained for `collection`, `source_kind`, and `source_rel`.

## 4. Chunking Strategy

Chunks are derived using the existing `ai-stack/ingest/ingest/chunker.py` and `config.py` definitions:

- **Size Limits:** Target `CHUNK_SIZE = 600` characters with `CHUNK_OVERLAP = 80`.
- **Header-Aware Splitting:** Uses Langchain's `MarkdownHeaderTextSplitter` to naturally divide the document on semantic boundaries (`#`, `##`, `###`).
- **Recursive Splitting:** If a semantic section exceeds the 600-character budget, it is recursively subdivided using `["\n\n", "\n", ". ", " ", ""]` to maintain paragraph and sentence integrity.

## 5. Retrieval Strategy

The corpus will be accessible via the `rag_search` Open WebUI Tool, and specifically highlighted by the `audit_search` semantic sugar Tool.

- **Dense Retrieval:** Embeddings are generated using `intfloat/multilingual-e5-small` (384 dimensions) and compared in Qdrant via Cosine distance.
- **Reranking:** The initial dense retrieval candidate pool is re-evaluated by the `BAAI/bge-reranker-v2-m3` cross-encoder to produce the final top-`k` results.
- **Routing:** The `audit_search` Tool hardcodes `collection="infra_audits"`, preventing cross-contamination in the LLM context window while maintaining exactly the same reranked retrieval pipeline.
