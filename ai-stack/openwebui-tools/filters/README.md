# openwebui-tools/filters — Amarolab Open WebUI **Functions** (Filters)

Canonical, version-controlled source for Aurora's Open WebUI **Functions**
(Filter type). Open WebUI 0.8.10 stores Functions in `webui.db` — runtime
state, not git. This directory is the source of truth (AD-09); the DB copy is
reproducible from it.

**Functions ≠ Tools.** Tools are LLM-callable (`class Tools`, audit-helper
inlined, installed by `bin/install_tool` → `/api/v1/tools/*`). Functions are
request/response middleware (`class Filter|Pipe|Action`, no inlining, installed
by `bin/install_function` → `/api/v1/functions/*`). Do not cross the two.

## Contents

| File | Type | Purpose |
|---|---|---|
| `aurora_context.py` | Filter | **F-3a** — on message 1, prepends `/opt/aurora/aurora-context.md` as a system message so Aurora answers "how is the lab?" with no tool call. Freshness decided from `aurora-context.json` (AD-10); fallback on missing/stale (>26h). |

## Install / activate workflow

```bash
# Install or update + ensure the Filter is active AND global:
./bin/install_function filters/aurora_context.py

# Inspect current DB state without changing anything:
./bin/install_function --status aurora_context

# Show the payload without POSTing:
./bin/install_function --dry-run filters/aurora_context.py
```

`install_function` mints a JWT signed with `WEBUI_SECRET_KEY` (from
`/home/diego/homelab/ai-stack/.env`) for admin `diego` — same auth as
`install_tool`. It then:

1. `POST /api/v1/functions/create` (or `.../id/{id}/update` if it exists).
   Open WebUI auto-detects the type from `class Filter`.
2. Ensures `is_active=True` via `.../id/{id}/toggle`.
3. Ensures `is_global=True` via `.../id/{id}/toggle/global`.

A Filter fires for every conversation **only when both `is_active` and
`is_global` are true** (confirmed in F-0/AF-01). No container restart is
required — activation is immediate on toggle.

## Runtime requirements

- The `openwebui` container must have the read-only bind-mount
  `ai-stack/aurora:/opt/aurora:ro` (added in F-2). The Filter reads
  `/opt/aurora/aurora-context.{json,md}` from inside the container.
- `bin/aurora-context` (F-2 cron, 04:15) keeps those files fresh. If they are
  missing or older than 26h, the Filter injects a one-line fallback and the
  conversation continues normally — it never crashes (§7).

## Recovery (if `webui.db` is lost)

Functions live only in `webui.db` (covered by the R-12 nightly Restic
snapshot). Two recovery paths:

1. **Restore** the latest `webui.db` snapshot — Functions return intact with
   their active/global state. Fastest, complete.
2. **Rebuild from git** (this directory):
   ```bash
   ./bin/install_function filters/aurora_context.py   # re-creates + re-activates
   ```
   This is the only manual step for the Filter; no admin-UI action needed
   (unlike Tools, which still require per-model visibility — D-20).

## What this directory does NOT contain

- Tools (LLM-callable) — those live in `../tools/` and use `bin/install_tool`.
- HA-voice awareness (F-3b) — a separate surface (`input_text` + Jinja2), not
  an Open WebUI Function. Out of F-3a scope.
