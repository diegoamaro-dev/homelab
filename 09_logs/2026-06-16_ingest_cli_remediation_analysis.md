# Ingest CLI Remediation Analysis

**Date:** 2026-06-16

## 1. Current State & Investigation

**Package Layout:**
The ingest service at `/home/diego/homelab/ai-stack/ingest/` follows a standard Python directory structure but lacks packaging metadata:
- `ingest/`: The actual Python package directory (contains `__init__.py`, `cli.py`, etc.).
- `venv/`: The virtual environment created by `install.sh`.
- `requirements.txt`: External dependencies (`qdrant-client`, `sentence-transformers`, etc.).
- `install.sh`: Creates the `venv` and runs `pip install -r requirements.txt`.
- `bin/ingest`: The bash wrapper that activates the `venv` and runs `exec python -m ingest.cli "$@"`.

**Import Path Expectations:**
Python modules inside the `ingest` package expect to import from `ingest.*`. When `python -m ingest.cli` is executed, Python needs to be able to locate the `ingest` module.

**Virtualenv Configuration Issue:**
The `install.sh` script does not install the `ingest` directory as a package into the `venv`. Therefore, `ingest` is only resolvable if the current working directory (CWD) is `/home/diego/homelab/ai-stack/ingest/` or if it's explicitly in the `PYTHONPATH`. The cron job executes `bin/ingest` from `/home/diego`, so the `ingest` module is never found, resulting in `ModuleNotFoundError`.

## 2. Remediation Options Comparison

### Option A: `export PYTHONPATH`
Modify `bin/ingest` to explicitly add the project root to `PYTHONPATH` before invoking python.

**Implementation:**
Add `export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"` to `bin/ingest`.

**Pros:**
- Extremely minimal change (one line in `bin/ingest`).
- No new files required.

**Cons:**
- It is a bash-wrapper workaround, not a true fix for the Python environment.
- If a user or process manually activates the venv and runs `python -m ingest.cli` without using `bin/ingest`, it will still fail.
- Does not adhere to Python packaging best practices.

### Option B: `pip install -e .`
Add a minimal `pyproject.toml` to define the package and update `install.sh` to install it into the `venv` in editable mode.

**Implementation:**
1. Create `/home/diego/homelab/ai-stack/ingest/pyproject.toml` with `[project]` and `[build-system]` metadata.
2. Update `install.sh` to run `pip install -e .`.

**Pros:**
- Idiomatic Python solution.
- The `ingest` package becomes fully resolvable within the `venv` regardless of CWD or how the interpreter is invoked.
- Future-proof: Enables IDEs, linters, and other tools to properly resolve imports.

**Cons:**
- Requires creating a new file (`pyproject.toml`) and modifying the installation script.

## 3. Recommendation

**Option B (`pip install -e .`) is the recommended long-term maintainable solution.**

While Option A is the quickest hotfix, Option B correctly aligns the service with standard Python packaging practices. By installing the package into its own virtual environment in editable mode (`-e .`), we decouple the execution context (CWD or wrapper scripts) from the module resolution logic. This guarantees that any script or cron job using that `venv` will successfully locate the `ingest` package.
