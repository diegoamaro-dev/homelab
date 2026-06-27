# Phase E — E2-c + E4-a Maintenance Apply Log

**Date:** 2026-06-27
**Phase:** E — Knowledge Platform Foundation
**Steps:** E2-c (F-08 run-lock) + E4-a (F-04 log rotation)
**Status:** Applied and validated

---

## E2-c — Run-lock (F-08)

### Context

F-08 (E-0 operational audit) identified that `bin/ingest-nightly` has no
overlap guard. Practical risk is low (a ~24-second run would need to overlap
exactly), but the gap was an open E-0 finding.

### Change

Added `flock -n` to `bin/ingest-nightly` immediately after the variable
definitions, before writing `=== RUN START ===` to the log. A lockfile at
`$ROOT/logs/ingest-nightly.lock` is opened on fd 200. If the lock cannot be
acquired (a prior run is still active), the script logs
`=== SKIPPED (lock held) <ts> ===` and exits 0. The lock is released
automatically when the script exits (fd 200 closed by the OS).

Exit 0 on skip is deliberate — a skipped run is not a failure;
`health.json` is left unchanged by the skipped invocation.

### Validation

| Scenario | Expected | Observed |
|---|---|---|
| V-1: normal run | exits 0, RUN START/END logged, health.json updated | ✓ |
| V-2: overlap (lock held by background process) | exits 0, SKIPPED line logged, health.json unchanged | ✓ |
| V-3: post-run lock state | lockfile exists; `flock -n` on it succeeds (lock released) | ✓ |

---

## E4-a — Log rotation (F-04)

### Context

F-04 identified that `ingest.log` has no rotation. Post-E5-c, `amarolab-audit.log`
writes are confirmed live; rotation for both logs is now appropriate.

### Change

New logrotate config at `ai-stack/ingest/etc/logrotate.d/homelab-ingest`
(committed to repo as the canonical source). Installed at
`/etc/logrotate.d/homelab-ingest` (requires sudo; system logrotate cron picks
it up automatically on the next daily pass).

| Log | Schedule | Retain | su |
|---|---|---|---|
| `ai-stack/ingest/logs/ingest.log` | weekly | 8 rotations | `su diego diego` |
| `/srv/homelab/data/openwebui/amarolab-audit.log` | monthly | 12 rotations | `su root root` |

Both entries use `compress`, `delaycompress`, `missingok`, `notifempty`.
`su` directives are required because both log parent directories have
group-writable permissions; without them logrotate refuses with "insecure
parent directory" errors.

### Validation

`sudo logrotate -d /etc/logrotate.d/homelab-ingest` (debug — no actual rotation):

- No insecure parent directory errors.
- `ingest.log` block: parsed correctly, switches to `diego:diego`.
- `amarolab-audit.log` block: parsed correctly, switches to `root:root`.
- Both logs considered by logrotate with correct schedules.
- No skipping errors.

---

## Files changed

| File | Change |
|---|---|
| `ai-stack/ingest/bin/ingest-nightly` | E2-c: flock run-lock added |
| `ai-stack/ingest/etc/logrotate.d/homelab-ingest` | E4-a: new logrotate config (repo canonical source) |
| `/etc/logrotate.d/homelab-ingest` | E4-a: system install (sudo; not committed) |
| `09_logs/2026-06-27_phaseE_E2c_E4a_maintenance_applied.md` | this document |
| `00_overview/ROADMAP.md` | E-2 closed; E-4 E4-a done |
| `04_ai_system/knowledge_platform_contract.md` | §5 updated: run-lock + log rotation |
| `00_overview/CURRENT_STATE.md` | E2-c + E4-a done entries |

---

## Findings closed

- **F-08 (run-lock):** closed — E2-c implemented and validated.
- **F-04 (log rotation):** closed — E4-a implemented and validated.
