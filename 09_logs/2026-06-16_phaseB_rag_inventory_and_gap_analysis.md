# Phase B — RAG Inventory and Gap Analysis

- **Date:** 2026-06-16.
- **Goal:** Perform read-only validation of the Amarolab Assistant v1 system to determine readiness for Phase B implementation (`rag_search`).

## 1. Qdrant Collection Inventory & Status

Read-only probes of the local Qdrant server confirmed the presence of the expected active collections.

| Collection | Status | Points | Dimensions | Distance |
|---|---|---|---|---|
| `homelab_docs` | green | 86 | 384 | Cosine |
| `guardian_cloud` | green | 872 | 384 | Cosine |
| `ensambla2` | green | 419 | 384 | Cosine |
| `myfreetour` | green | 0 | 384 | Cosine |

**Observation:** The collections defined in Phase 1 exist and have the expected dimensionality (384, consistent with `multilingual-e5-small`) and distance metric (Cosine). The `infra_audits` collection does not exist yet, which is correct for this pre-Phase B state.

## 2. Embedding & Reranker Model Availability

The local Open WebUI model cache directory (`/srv/homelab/data/openwebui/cache/embedding/models/`) contains the expected models:

- **Embedder:** `models--intfloat--multilingual-e5-small` (Present)
- **Reranker:** `hub/models--BAAI--bge-reranker-v2-m3` (Present)

**Observation:** Both required models are cached locally and available.

## 3. Ingestion Status & CLI Analysis

The `ingest` CLI wrapper at `/home/diego/homelab/ai-stack/ingest/bin/ingest` is currently broken and the daily cron job is failing.

- **Status:** Failing.
- **Log Error:** `/home/diego/homelab/ai-stack/ingest/logs/ingest.log` contains `ModuleNotFoundError: No module named 'ingest'`.
- **Root Cause:** The `bin/ingest` script activates the Python virtual environment but fails to export `PYTHONPATH` or `cd` into the package root directory. The `ingest` module is not installed via `pip install -e .`, making it unresolvable from outside the directory. 

## 4. Open WebUI & Tool Configuration

### Qwen 2.5 Model Configuration
The database (`webui.db`) was queried to confirm the `qwen2.5:7b-instruct` model configuration:

- `base_model_id`: `NULL`
- `meta.toolIds`: `["time_now"]`

**Observation:** The Issue T remediation remains intact. The model is correctly configured to use tools without being dropped by the WebUI API.

### Existing Tools
The `tool` table in `webui.db` was queried for `rag_search` and `audit_search`.

- **Result:** Neither tool exists in the database.
- **Observation:** This is the expected state before Phase B implementation. Open WebUI Tool architecture compatibility is confirmed via previous logs (D-24, D-25) meaning `class Tools` schema will be used for implementation.

## 5. Identified Blockers & Gap Analysis

1. **Ingestion CLI Broken (Blocker):** The `bin/ingest` script must be fixed before the `infra_audits` collection can be built or synchronized. Either `PYTHONPATH=$ROOT` must be added to the script, or the package should be installed into the virtual environment using a `pyproject.toml` and `pip install -e .`.
2. **Missing `infra_audits` Corpus (Gap):** This is part of the planned Phase B work, but its creation is blocked by the Broken Ingestion CLI.
3. **Open WebUI Ingest Bind Mount (Gap/Gated):** The openwebui container needs to be recreated with a read-only bind mount for `/opt/ingest` so the `rag_search` Tool can import the `Embedder` and `Reranker`. This action requires explicit user approval.
4. **Sentence-Transformers Drift (Risk):** As noted in previous reviews, there is a risk of major-version drift between the ingest venv (`<4`) and the openwebui container (`5.2.3`). This should be verified during the validation phase to ensure reranker benchmark scores do not regress.

## 6. Readiness Verdict

**Verdict: BLOCKED by Ingestion CLI.**

Phase B implementation cannot proceed until the `bin/ingest` script is fixed, as the `infra_audits` corpus cannot be created or synchronized. Once fixed, Phase B implementation is cleared to begin pending user approval for the container recreation gate.
