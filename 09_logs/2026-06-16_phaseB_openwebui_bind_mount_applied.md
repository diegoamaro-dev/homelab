# Phase B: Open WebUI Bind Mount — APPLIED (Step B-3)

**Date:** 2026-06-16

This log captures the successful application of the rollback-safe recreate plan (Gate G-1) for the Open WebUI container, fulfilling Phase B step B-3.

## 1. Goal

Recreate the `openwebui` container to inject the ingest pipeline's runtime dependencies (`Embedder` and `Reranker`) via a read-only bind mount, ensuring total data persistence and configuration continuity.

## 2. Execution Log

The documented plan was executed identically:
1. `webui.db` and `amarolab-audit.log` md5 hashes were captured prior to execution.
2. The running `openwebui` container was stopped and gracefully renamed to a timestamped backup container (`openwebui_pre_phaseB_20260615235209`).
3. The new container was spun up incorporating all original `.env` parameters, ports, and networks, alongside the new `-v /home/diego/homelab/ai-stack/ingest:/opt/ingest:ro` bind mount.
4. The container was manually reattached to the `proxy_default` bridge network.

## 3. Validation Results

All validation constraints passed successfully:

- **Health Status:** `healthy`
- **Networks Attached:** `ai-local_default`, `proxy_default`
- **Port Mapping:** `8080/tcp -> 3000` (Preserved)
- **Mounts Verification:**
  - `/srv/homelab/data/openwebui` -> `/app/backend/data` (RW: true)
  - `/home/diego/homelab/ai-stack/ingest` -> `/opt/ingest` (RW: false)
- **Data Persistence:**
  - `webui.db` MD5 hash unchanged (`656d7295d3cfc00a2255bb0b2230fba1`).
  - `amarolab-audit.log` MD5 hash unchanged (`310ef8dbfd103685514addacb1ada2c3`).
- **Model State Intact:**
  - `qwen2.5:7b-instruct` `base_model_id` remains `NULL`.
  - `qwen2.5:7b-instruct` `toolIds` remain exactly `["time_now"]`.
- **Module Import Smoke Test:**
  - `from ingest.embedder import Embedder` and `from ingest.reranker import Reranker` resolved seamlessly from inside the new container environment, unblocking the execution of Tool scripts.

## 4. Scope Constraints Honoured
- No tools (`rag_search`, `audit_search`) were installed.
- No database edits were made.
- Home Assistant and Guardian Cloud were completely bypassed.

## 5. Rollback Target
The fully-intact pre-Phase B container remains paused on the host under the name:
**`openwebui_pre_phaseB_20260615235209`**
