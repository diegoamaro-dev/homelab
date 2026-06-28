# Phase F — F2-5 `system_status` Open WebUI Tool

- **Date:** 2026-06-28
- **Phase step:** F-2 — Signal Layer and Context Generation
- **Sub-step:** F2-5 — `system_status` Open WebUI tool (v0.2.0)
- **Status:** COMPLETE

---

## 1. What was implemented

Updated the existing `system_status` tool in Open WebUI (`webui.db`, id=`system_status`)
to read Aurora context signals and produce a structured homelab status report.

**Previous version (v0.1.0):** psutil only — CPU, RAM, disk.
**New version (v0.2.0):** Full Aurora context + live Torre probe + psutil metrics.

**Source:** `ai-stack/ingest/docs/system_status_tool.py`
Installed via: `sqlite3` Python module updating `tool` table, then `docker restart openwebui`.

---

## 2. Tool behaviour

### Primary path (aurora-context.json available — requires F2-6)

Reads `/opt/aurora/aurora-context.json` (bind-mounted from host `ai-stack/aurora/`).
Extracts `overall_status`, per-signal statuses, and all detail fields. Also performs
a live Torre probe independently of the context file.

Output structure:
```
AMAROLAB System Status — YYYY-MM-DD HH:MM UTC

Overall: <ok|degraded|unknown>
Reasons:
  • <reason 1>
  • <reason 2>

---

Context:     YYYY-MM-DD HH:MM UTC (Xh ago)
Torre (live): reachable (Xms)
System:      CPU X% | RAM X% | Disk X%

Ingest:      <detail>
Backup:      <detail>
Audit:       <detail>
Containers:  <detail>

Signals missing: <none|list>
```

### Fallback path (aurora-context.json not mounted — pre-F2-6 / F2-6 pending)

Falls back to reading `/opt/ingest/logs/health.json` directly (already bind-mounted).
Reports ingest and audit from health.json; backup and containers shown as "not available".
Torre probe still runs live.

### Error path

All exceptions caught at every level. Any unhandled exception in the top-level
`system_status()` method is caught and returned as an error string — the tool
never raises to Open WebUI.

### Live Torre probe

- Target: `http://100.91.154.124:11434/api/tags` (Torre Tailscale IP, direct)
- Timeout: 3s
- Reports: latency in ms on success; exception type on failure
- Independent of context file: runs regardless of which path is taken
- Added to `Reasons` block only if Torre is unreachable

---

## 3. Validation results

All tests executed by running the installed code from inside the openwebui container
(`exec` + `python3 -c "...exec(code)..."`), avoiding the need for a chat session.

| Test | Mode | Result |
|---|---|---|
| Fallback path — health.json read, Torre probe | pre-F2-6 | **PASS** |
| Full path — aurora-context.json read, all sections | full (docker cp) | **PASS** |
| Reasons block present and accurate | full | **PASS** |
| Context freshness shown separately from Torre probe | both | **PASS** |
| Torre reachable (3ms), Tailscale direct | both | **PASS** |
| `overall_status` matches aurora-context.json | full | **PASS** |
| `Signals missing: none` when all signals present | full | **PASS** |
| `Signals missing: aurora-context.json` in fallback | fallback | **PASS** |
| psutil CPU/RAM/disk present | both | **PASS** |
| Tool never raises — exception guard verified by code review | — | **PASS** |

**Full mode note:** `/opt/aurora/` was created temporarily inside the container
via `docker exec mkdir` + `docker cp`. This copy persists in the container's
writable layer until the container is recreated. F2-6 (Portainer bind-mount) will
replace this with a permanent, auto-updated mount.

**Fallback mode note:** After removing the docker-cp'd file, the tool fell back
cleanly to health.json with `overall: partial` and honest "not available" lines.

**Backup status at test time:** `no_snapshot_tonight` — expected and correct.
The snapshot at 01:00 UTC is 9.3h old at test time (10:18 UTC); the production
cron at 04:15 CEST (~02:15 UTC) will see it as 1.2h old and report `ok`.

---

## 4. Installation record

- **DB path:** `/srv/homelab/data/openwebui/webui.db`
- **Table:** `tool`, row `id='system_status'`
- **Method:** Python `sqlite3` module — parameterised UPDATE (no shell quoting issues)
- **Container restart:** `docker restart openwebui` — required for tool reload
- **Source committed:** `ai-stack/ingest/docs/system_status_tool.py`

---

## 5. Open items entering F2-6

| Item | Status |
|---|---|
| `/opt/aurora` bind-mount | **Next step — F2-6 (Portainer UI, operator action)** |
| `/etc/cron.d/aurora-signals` | Pending end of F2 (all probes ready) |
| Chat-level tool validation (G-F1-01) | Pending browser session — "¿Cuál es el estado del sistema?" |

---

*F2-5 complete. Tool installed and validated in both fallback and full modes.*
*F2-6 (Portainer bind-mount) required before production full-mode operation.*
