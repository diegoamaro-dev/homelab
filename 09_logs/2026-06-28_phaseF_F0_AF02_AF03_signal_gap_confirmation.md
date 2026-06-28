# F-0 Finding — AF-02 / AF-03: Signal Gap Confirmation

**Date:** 2026-06-28  
**Phase:** F-0 Behavioral Audit  
**Finding references:** AF-02, AF-03 (from `04_ai_system/phase_f_architecture.md` §11)  
**Status:** CONFIRMED GAPS — expected pre-F-2 state, not defects

---

## Context

AF-02 and AF-03 document known gaps that the architecture explicitly expects at the start of Phase F. These are pre-conditions for F-2 (Signal Layer and Context Generation), confirmed here by read-only inspection of the live system.

From `phase_f_architecture.md` §11:

> **AF-02** — `backup_status.json` does not exist. No structured backup signal is available until `homelab-backup.sh` is modified. High priority. First deliverable of F-2. `aurora-context` must degrade gracefully until F-2 is complete.

> **AF-03** — `container_status.json` does not exist. Docker container health is unavailable to the context layer without a new probe script. Medium priority. Part of F-2. Until it exists, context document omits container health; `aurora-context` logs the missing signal.

---

## AF-02 — `backup_status.json`

### Absence confirmed

```bash
find /home/diego/homelab -name "backup_status.json"
# → (no output)
```

Neither `backup_status.json` nor any analogous JSON backup signal file exists anywhere under `/home/diego/homelab`.

### Current backup pipeline (read-only survey)

| Item | Value |
|---|---|
| Script | `/usr/local/bin/homelab-backup.sh` |
| Owner / permissions | `root:root 0755` |
| Schedule | `/etc/cron.d/homelab-backup` — `0 3 * * * root /usr/local/bin/homelab-backup.sh >> /var/log/homelab-backup.log 2>&1` |
| Log | `/var/log/homelab-backup.log` (text/append; rotated by `/etc/logrotate.d/homelab-backup`) |
| Repository | `/mnt/storage/backups/restic` |
| Password file | `/etc/restic/passwd-homelab` |

### What the script currently does

The script performs two operations:
1. `restic backup` — backs up workload roots (openwebui data, HA, npm, Qdrant, zigbee-stack, webs, etc.) plus SQLite snapshots. Appends to `/var/log/homelab-backup.log`.
2. `restic forget` — retention policy (7 daily, 4 weekly, 6 monthly), with `--prune`.

**The script writes no structured output.** There is no JSON, no status file, no signal. The only machine-readable artifact is the non-zero exit code on failure (caught by the shell's `set -euo pipefail`).

### What F-2 must deliver for AF-02

Modify `homelab-backup.sh` to write `ai-stack/ingest/logs/backup_status.json` immediately after the `restic backup` + `restic forget` calls complete. Required fields per §6.1:

```json
{
  "schema_version": 1,
  "run_at": "...",
  "exit_code": 0,
  "status": "ok | failed",
  "snapshot_id": "...",
  "files_new": ...,
  "files_changed": ...,
  "data_added_mb": ...,
  "duration_seconds": ...,
  "prune_removed": ...
}
```

### F-2 implementation note (root → user boundary)

The backup script runs as `root` (via `/etc/cron.d/homelab-backup`). The target write path `ai-stack/ingest/logs/` is owned by `diego:diego`. This is not a blocker — root can write to any directory — but the written file will be root-owned unless the script calls `chown diego:diego` or `chmod` immediately after writing. `bin/aurora-context` reads the file as the `diego` user, so the file must be readable by diego. **This is a concrete F-2 implementation requirement.**

---

## AF-03 — `container_status.json`

### Absence confirmed

```bash
find /home/diego/homelab -name "container_status.json"
# → (no output)

find /home/diego/homelab/ai-stack/ingest/bin -type f
# → bin/ingest, bin/ingest-nightly, bin/check-audit-liveness
# → (no container-probe)

find /usr/local/bin -name "*container*" -o -name "*probe*"
# → (no output)
```

Neither `container_status.json` nor a `container-probe` script exists anywhere on the system.

### Current container state (live snapshot, 2026-06-28)

`docker ps` confirms 17 containers running:

| Container | Status |
|---|---|
| `ollama-proxy` | Up 21 hours (healthy) |
| `openwebui` | Up 21 hours (healthy) |
| `aurora-piper-http` | Up 25 hours |
| `aurora-whisper-http` | Up 25 hours |
| `cloudflared-amarolab` | Up 25 hours |
| `aurora-wakeword` | Up 25 hours |
| `aurora-piper` | Up 25 hours |
| `aurora-whisper` | Up 25 hours |
| `qdrant` | Up 25 hours |
| `cloudflared` | Up 25 hours |
| `guardian-web` | Up 25 hours |
| `zigbee2mqtt` | Up 25 hours |
| `mosquitto` | Up 25 hours |
| `nginx-proxy-manager` | Up 25 hours |
| `ollama` | Up 25 hours |
| `homeassistant` | Up 21 hours |
| `portainer` | Up 25 hours |

This matches the "all 17 containers" referenced in the F-2 success criterion (`phase_f_architecture.md` §9 F-2).

### What F-2 must deliver for AF-03

Write a new `bin/container-probe` script (runs as `diego`, scheduled at 04:00 nightly in the user crontab). It must:
- Call `docker ps` or `docker inspect` for all containers
- Write `ai-stack/ingest/logs/container_status.json` with schema per §6.1:

```json
{
  "schema_version": 1,
  "generated_at": "...",
  "containers": [
    {"name": "openwebui", "status": "running", "running": true},
    ...
  ]
}
```

- Be lightweight and fast (no embedding, no LLM calls)
- Be scheduled in the user crontab at 04:00 (after the 03:30 `check-audit-liveness`, before the 04:15 `bin/aurora-context`)

---

## Expected signal file paths (architecture §6.1)

Both signals live alongside the existing `health.json` in the same directory:

```
ai-stack/ingest/logs/
├── health.json             ← EXISTS (production)
├── backup_status.json      ← MISSING (F-2 creates)
└── container_status.json   ← MISSING (F-2 creates)
```

This directory is:
- Gitignored via `ai-stack/ingest/logs/` in `.gitignore` (already present — both new files will be automatically excluded from git)
- Accessible inside the `openwebui` container at `/opt/ingest/logs/` via the existing bind-mount `ai-stack/ingest:/opt/ingest:ro`
- Readable by `bin/aurora-context` running as `diego`

**Note:** `backup_status.json` is written by root (backup script), but the target directory is accessible and the files must be made readable by diego. See F-2 implementation note above.

---

## Nightly cron order context

Current cron (pre-F-2):

| Time | Job | Produces |
|---|---|---|
| 02:30 | `ingest-nightly` | `health.json` (ingest section) |
| 03:00 | `homelab-backup.sh` | `/var/log/homelab-backup.log` only |
| 03:30 | `check-audit-liveness` | `health.json` (audit section) |

After F-2 (target cron order per §6.4):

| Time | Job | Produces |
|---|---|---|
| 02:30 | `ingest-nightly` | `health.json` |
| 03:00 | `homelab-backup.sh` (modified) | `health.json` update + `backup_status.json` |
| 03:30 | `check-audit-liveness` | `health.json` (audit section) |
| 04:00 | `bin/container-probe` (new) | `container_status.json` |
| 04:15 | `bin/aurora-context` (new) | `aurora-context.json`, `aurora-context.md`, `aurora-context-voice.txt` |
| 04:20 | `bin/generate-digest` (new, F-4) | `09_ops/runtime/YYYY-MM-DD_ops_digest.md` |

---

## Verdict

| Check | Result |
|---|---|
| `backup_status.json` does not exist | **CONFIRMED ABSENT** |
| `container_status.json` does not exist | **CONFIRMED ABSENT** |
| Expected location documented | **CONFIRMED** — both in `ai-stack/ingest/logs/` |
| Producer for `backup_status.json` identified | **CONFIRMED** — `homelab-backup.sh` (modification required) |
| Producer for `container_status.json` identified | **CONFIRMED** — new `bin/container-probe` (does not yet exist) |
| Signal directory already gitignored | **CONFIRMED** — `ai-stack/ingest/logs/` is in `.gitignore` |
| Signal directory accessible in container | **CONFIRMED** — `/opt/ingest/logs/` via existing bind-mount |
| Container count for F-2 success criterion | **CONFIRMED** — 17 containers running |

---

## AF-02 / AF-03 disposition

**CONFIRMED GAPS — not defects.** Both absences are expected and documented in the Phase F architecture as known pre-conditions for F-2. No corrective action is required in F-0.

**F-2 pre-implementation requirements surfaced by this audit:**

1. `homelab-backup.sh` runs as root. The `backup_status.json` write must use `chown diego:diego` (or `chmod a+r`) immediately after writing, so `bin/aurora-context` can read it as the `diego` user.
2. `bin/container-probe` does not exist and must be written from scratch. It is straightforward: `docker ps` → JSON output.
3. Both files land in `ai-stack/ingest/logs/` which is already gitignored — no `.gitignore` change needed for these two signals.
4. Both files are already accessible in the container via the existing bind-mount — no new bind-mount needed for these signals.

**`bin/aurora-context` graceful degradation requirement (confirmed for F-2):** When `backup_status.json` or `container_status.json` are absent, `bin/aurora-context` must populate `signals_missing` in `aurora-context.json` and omit those sections from `aurora-context.md` without erroring. This is the behavior required during the window between F-2 deployment and the first nightly cycle that produces all three signals.

---

## Cleanup confirmation

Read-only audit. No files created. No scripts modified. No git operations performed.
