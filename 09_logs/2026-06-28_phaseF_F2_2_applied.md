# Phase F — F2-2 `backup-probe` Implementation

- **Date:** 2026-06-28
- **Phase step:** F-2 — Signal Layer and Context Generation
- **Sub-step:** F2-2 — `backup-probe` script
- **Status:** COMPLETE

---

## 1. What was implemented

New script: `ai-stack/ingest/bin/backup-probe`

Reads the restic snapshot repository after the nightly backup window and writes
`ai-stack/ingest/logs/backup_status.json` atomically. Produces one of three
status values as defined in `ai-stack/ingest/docs/signals_contract.md`:

- `"ok"` — latest snapshot is within `BACKUP_PROBE_WINDOW_HOURS` of probe time
- `"no_snapshot_tonight"` — latest snapshot predates the expected window
- `"error"` — restic command failed; includes `probe_error` field

Key design decisions implemented:
- Does **not** modify `homelab-backup.sh`
- Reads restic via `restic snapshots --latest 1 --json --no-lock`
- Freshness validated by comparing snapshot timestamp to probe time, not by
  assuming the backup ran because the cron fired
- Atomic write: `.tmp` → `fsync` → `chmod 0644` → `os.replace()`
- Env overrides: `BACKUP_PROBE_WINDOW_HOURS` (default 4), `RESTIC_REPOSITORY`,
  `RESTIC_PASSWORD_FILE`
- Single diagnostic line to stderr for cron/syslog capture
- Stdlib only; no venv dependency

---

## 2. Bug found and fixed during validation

**Bug:** `snapshots[0]` always selected the oldest snapshot, not the most recent.

**Root cause:** `restic snapshots --latest N --json` returns one entry per
path/host group, not one globally. The repository has multiple groups
(distinct backup paths), so the JSON array contained entries ordered
oldest-first. `snapshots[0]` was consistently picking `cc73b4fd` (2026-06-13)
instead of `d6c12657` (2026-06-28).

**Observed failure:** `backup-probe` reported `status: "no_snapshot_tonight"`
despite a fresh snapshot existing. The probe ran ~8.8h after the snapshot,
and the selected snapshot (2026-06-13) was 15+ days old.

**Fix:** `snapshots[0]` → `max(snapshots, key=lambda s: s["time"])`

ISO 8601 timestamps are lexicographically ordered, so string `max()` correctly
identifies the globally most recent snapshot without requiring a datetime parse
at the selection step.

**Affected line:** `bin/backup-probe:114` (one-line change; no interface change;
contract unchanged).

---

## 3. Validation results

All tests performed manually as root (`sudo backup-probe`).

| Test | Result |
|---|---|
| Primary run — `status: "ok"`, `snapshot_id: "d6c12657"` | **PASS** |
| Snapshot timestamp matches `restic snapshots --latest 1` direct query | **PASS** |
| `BACKUP_PROBE_WINDOW_HOURS=12` → `status: "ok"` | **PASS** (confirmed fix) |
| Default 4h window at 8.8h post-snapshot → `status: "no_snapshot_tonight"` | **PASS** (expected at test time; production run at 03:30 will always be ~0.5h) |
| Error simulation (`RESTIC_REPOSITORY=/nonexistent`) → `status: "error"`, `probe_error` populated | **PASS** |
| JSON writes atomically; `python3 -m json.tool` passes | **PASS** |
| File permissions: `0644 root:root` | **PASS** (readable by diego/openwebui) |

Logic tests (no sudo, in-session):

| Test | Result |
|---|---|
| `parse_snap_time` — nanoseconds+Z, bare Z, offset | **PASS** |
| Fresh snapshot (age 0.49h, window 4h) → `"ok"` | **PASS** |
| Stale snapshot (age 24.5h, window 4h) → `"no_snapshot_tonight"` | **PASS** |
| Boundary (age exactly 4.0h) → `"ok"` (inclusive `<=`) | **PASS** |
| Multi-snapshot array: `max()` selects `d6c12657` over `cc73b4fd` | **PASS** |

---

## 4. Files created

| File | Status |
|---|---|
| `ai-stack/ingest/bin/backup-probe` | Created, committed |
| `ai-stack/ingest/logs/backup_status.json` | Runtime artifact, gitignored, written on first probe run |

---

## 5. Open items entering F2-3

| Item | Status |
|---|---|
| `/etc/cron.d/aurora-signals` (backup-probe entry) | **Not yet installed** — pending operator approval after F2-3 |
| `container-probe` script | **Next step — F2-3** |
| `aurora-context` script | Pending F2-4 |
| `system_status` Open WebUI tool | Pending F2-5 |
| `/opt/aurora` bind-mount (Portainer) | Pending F2-6 |

---

*F2-2 complete. `backup-probe` validated manually as root. Cron installation deferred to end of F2.*
