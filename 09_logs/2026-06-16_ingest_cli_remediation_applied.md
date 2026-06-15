# Ingest CLI Remediation — APPLIED

**Date:** 2026-06-16

## 1. Goal

Implement Option B (editable package installation) to fix the `ModuleNotFoundError` in the ingest service, allowing the `ingest` package to be imported successfully from anywhere, enabling the daily cron job.

## 2. Changes Made

### 2.1 Added `pyproject.toml`
Created `/home/diego/homelab/ai-stack/ingest/pyproject.toml`:
- Configured setuptools build system.
- Defined the package name `ingest` and version `0.1.0`.
- Specified `dependencies` mirroring `requirements.txt`.
- Configured explicit package discovery via `[tool.setuptools] packages = ["ingest"]`.

### 2.2 Modified `install.sh`
Updated `/home/diego/homelab/ai-stack/ingest/install.sh`:
- Appended `pip install -e .` to the end of the installation steps.

### 2.3 Updated `.gitignore`
- **Decision:** The `ai-stack/ingest/ingest.egg-info/` directory created by `pip install -e .` is dynamically generated Python build metadata. It must not be committed to version control.
- **Action:** Added `*.egg-info/` to `/home/diego/homelab/.gitignore` under the Python section.

## 3. Execution Log

Ran `/home/diego/homelab/ai-stack/ingest/install.sh` from `/home/diego/homelab/ai-stack/ingest`.
- The environment was successfully updated.
- The `ingest` package was built and installed in editable mode (`Successfully installed ingest-0.1.0`).

## 4. Validation

Ran validation commands from `/home/diego` (outside the project root, mimicking the cron job context).

**Command 1:** `/home/diego/homelab/ai-stack/ingest/bin/ingest --help`
- **Result:** PASS. Returned the CLI usage instructions.

**Command 2:** `/home/diego/homelab/ai-stack/ingest/bin/ingest status`
- **Result:** PASS. Successfully connected to Qdrant and returned the active collections and their point counts:
  - `homelab_docs`: 86
  - `guardian_cloud`: 872
  - `ensambla2`: 419
  - `myfreetour`: 0

**Conclusion:** The ingest CLI is now fully operational and path-independent. The nightly 02:30 cron job will now succeed.

## 5. Scope Constraints Honoured
- `webui.db` untouched.
- `openwebui` container untouched.
- Qdrant collections untouched.
- Tool installation untouched.
- Home Assistant untouched.
- Guardian Cloud untouched.
