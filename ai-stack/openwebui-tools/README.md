# openwebui-tools — Amarolab Tool source for Open WebUI

Canonical, version-controlled source of the Amarolab Assistant's Open
WebUI Tools. Open WebUI 0.8.10 stores Tools in `webui.db`; this
directory is the source of truth, not the runtime copy.

For the rationale, see
[`/home/diego/FUNCTIONS_COMPATIBILITY_REPORT.md`](../../../FUNCTIONS_COMPATIBILITY_REPORT.md).
For the design and validation plan, see
[`09_logs/2026-06-15_phaseA3-tool-canary-design.md`](../../09_logs/2026-06-15_phaseA3-tool-canary-design.md).

## Layout

```
openwebui-tools/
├── README.md           this file
├── tools/
│   └── time_now.py     canary Tool — Open WebUI Tool with `class Tools`
├── lib/
│   └── audit_helper.py canonical audit + RateLimiter helpers,
│                       textually inlined into each Tool at install time
└── bin/
    ├── install_tool    inline lib + POST /api/v1/tools/create (or .../update)
    └── dump_tools      GET each Tool's content from webui.db and write to ./tmp/
```

## Install workflow

```bash
# Install or update a Tool (auto-detects create vs update):
./bin/install_tool tools/time_now.py

# Dry-run: inline + print, do not POST:
./bin/install_tool --dry-run tools/time_now.py

# Pull current DB state back to disk for diff:
./bin/dump_tools
diff tools/time_now.py tmp/time_now.dumped.py
```

Authentication: `install_tool` mints a JWT signed with
`WEBUI_SECRET_KEY` (read from
`/home/diego/homelab/ai-stack/.env`) for the admin user
`diego`. No interactive password prompt, no Open WebUI API-key feature
flag required.

## Why the helper is inlined

Open WebUI 0.8.10 executes each Tool inside its own
`tool_{id}` module namespace via `exec()`. Cross-Tool `import`
statements do not resolve. To keep the audit / rate-limit machinery
DRY, the canonical text lives once in `lib/audit_helper.py` and
`install_tool` textually substitutes it into each Tool source where
the marker

```
# @@AMAROLAB_INLINE:audit_helper@@
```

appears. The inlined symbols use a `_` prefix so Open WebUI's tool
discovery (`get_functions_from_tool`) does not treat them as
LLM-callable methods.

## Per-model visibility

After install, scope the Tool to the primary tool-calling model in
the Open WebUI admin UI:

- Workspace → Models → `qwen2.5:7b-instruct` → Tools → enable the Tool.
- Verify the Tool is **not** enabled for `llama3:latest`,
  `llama3.2:latest`, or `phi3:latest` (Amarolab decision D-20).

## Adding a new Tool

1. Drop a file at `tools/<id>.py`. Keep `<id>` a valid Python
   identifier (alphanumeric + underscores).
2. The file must declare `class Tools:` and put each LLM-callable
   method as a public (non-underscore) method with full type hints
   and a docstring.
3. Inline the helper by placing `# @@AMAROLAB_INLINE:audit_helper@@`
   on its own line, near the top after the docstring.
4. `./bin/install_tool tools/<id>.py`.
5. Enable per-model in the admin UI (D-20).

## Backup posture

This directory is inside the homelab git repository; commits are
pushed to GitHub. Open WebUI's `webui.db` (the runtime copy) is at
`/srv/homelab/data/openwebui/webui.db` and is covered by the R-12
nightly Restic snapshot.

If `webui.db` is ever lost, the recovery flow is:

```bash
./bin/install_tool tools/time_now.py
# repeat for every Tool in tools/
# then re-do per-model visibility in the admin UI
```

## What this directory does NOT contain

- Home Assistant tool source (Phase C; not yet designed in this repo).
- The `homelab-tools` backing container for `system_status` (Phase D).
- Open WebUI Pipes / Filters / Actions (different extension concept;
  Amarolab v1 does not use them).
