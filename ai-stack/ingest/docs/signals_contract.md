# Aurora Signal Layer — Signals Contract

- **Status:** Standing reference. Describes **deployed reality** of the
  Aurora signal layer as of 2026-06-28 (introduced Phase F-2).
- **Authority:** This document records the schema and compatibility rules for
  every signal file consumed by `bin/aurora-context` and the `system_status`
  tool. If the running system disagrees with this document, the running system
  wins and this document is corrected.
- **Companion:** [`knowledge_platform_contract.md`](../../../04_ai_system/knowledge_platform_contract.md)
  covers the RAG retrieval substrate. This document covers operational signals only.

---

## Overview

The Aurora signal layer is a set of JSON files written by independent producers
and read by `bin/aurora-context` to construct the nightly context document.
Consumers never call the producers directly; they only read files.

```
Producers                          Signal files                  Consumers
─────────────────────────────────────────────────────────────────────────────
ingest-nightly                 →   health.json          ─┐
check-audit-liveness           →   health.json          ─┤→ bin/aurora-context
backup-probe (new, F-2)        →   backup_status.json   ─┤→ system_status tool
container-probe (new, F-2)     →   container_status.json─┘
                                                          ↓
                                                    aurora-context.json
                                                    aurora-context.md
                                                    aurora-context-voice.txt
```

All signal files live in `ai-stack/ingest/logs/` on the host, which is
bind-mounted read-only into the `openwebui` container as `/opt/ingest/logs/`.
All context artifacts live in `ai-stack/aurora/`, bind-mounted as `/opt/aurora/`.

---

## Compatibility Rules

These rules apply to **all** signal files defined in this document.

### Schema versioning

Every signal file carries a `schema_version` integer field. The current version
for all files is `1`.

- Consumers **must** check `schema_version` before reading. If the version is
  not a value the consumer was written for, the consumer must treat the file as
  missing (log a warning; do not attempt to parse unknown fields).
- **Backwards-compatible changes** (adding a new optional field) do **not**
  require a version bump. The consumer ignores unknown fields.
- **Breaking changes** (removing, renaming, or changing the type of an existing
  field) **require** a `schema_version` bump. The producer and all consumers
  must be updated atomically; document the migration in an apply log.

### Missing file

If a signal file is absent, the consumer:
- Adds the file name to the `signals_missing` array in `aurora-context.json`.
- Sets the corresponding section to `{"status": "signal_missing"}`.
- Emits an honest human-readable note in `aurora-context.md` (e.g., "backup:
  signal missing").
- Does **not** crash; does **not** guess; does **not** substitute a stale value
  from a previous run.

### Missing field within a file

If a required field is absent within an otherwise-valid file:
- The consumer treats the field as `null`.
- The consumer does not crash.
- If the field is critical for status determination, the consumer sets the
  relevant status to `"unknown"`.

### Stale file

A signal file is considered stale when its internal timestamp field (not
filesystem mtime) is older than the expected freshness threshold. Thresholds:

| File | Freshness threshold | Timestamp field |
|---|---|---|
| `health.json` (ingest section) | 26 hours | `ingest.updated_at` |
| `health.json` (audit section) | 26 hours | `audit.updated_at` |
| `backup_status.json` | 26 hours | `probed_at` |
| `container_status.json` | 26 hours | `generated_at` |

A stale file is treated the same as a missing file by `aurora-context`. The
Open WebUI Filter (F-3) applies its own 26-hour threshold to `aurora-context.md`
as a whole; individual signal staleness is handled at the `aurora-context` layer.

### Atomicity

Signal files are written atomically: the producer writes to a `.tmp` file and
renames it over the target. This prevents a consumer reading a partial file
during a concurrent write. All producers **must** follow this pattern.

### No cross-file dependencies

`health.json`, `backup_status.json`, and `container_status.json` are produced
independently. No signal file reads another. `aurora-context` is the only
component that aggregates them.

---

## Signal Files

### 1. `health.json`

- **Path (host):** `ai-stack/ingest/logs/health.json`
- **Path (container):** `/opt/ingest/logs/health.json`
- **Producer:** `ingest-nightly` (ingest section, 02:30) + `check-audit-liveness`
  (audit section, 03:30)
- **Existing signal:** Yes — deployed Phase E.

```json
{
  "schema_version": 1,
  "updated_at": "2026-06-28T01:30:01Z",
  "overall_status": "ok",
  "ingest": {
    "last_run_start": "2026-06-28T00:30:01Z",
    "last_run_end":   "2026-06-28T00:30:13Z",
    "last_run_rc":    0,
    "last_run_status": "ok",
    "last_successful_run_end": "2026-06-28T00:30:13Z",
    "updated_at":     "2026-06-28T00:30:13Z"
  },
  "audit": {
    "last_entry_ts": "2026-06-28T00:36:48.484119+00:00",
    "age_days":      0,
    "status":        "ok",
    "updated_at":    "2026-06-28T01:30:01Z"
  }
}
```

**Field reference:**

| Field | Type | Description |
|---|---|---|
| `schema_version` | int | Always `1` |
| `updated_at` | ISO 8601 UTC | Timestamp of the last write to this file (audit section wins) |
| `overall_status` | `"ok"` \| `"degraded"` \| `"error"` | Aggregate of ingest + audit status |
| `ingest.last_run_start` | ISO 8601 UTC | Start of the most recent ingest run |
| `ingest.last_run_end` | ISO 8601 UTC | End of the most recent ingest run |
| `ingest.last_run_rc` | int | Exit code of the most recent ingest run |
| `ingest.last_run_status` | `"ok"` \| `"error"` | Derived from `last_run_rc` |
| `ingest.last_successful_run_end` | ISO 8601 UTC | End of the last run with `rc == 0` |
| `ingest.updated_at` | ISO 8601 UTC | Timestamp of the ingest section's last write |
| `audit.last_entry_ts` | ISO 8601 | Timestamp of the most recent entry in `amarolab-audit.log` |
| `audit.age_days` | float | Age of the most recent audit entry in days |
| `audit.status` | `"ok"` \| `"stale"` \| `"missing"` | Freshness of the audit log |
| `audit.updated_at` | ISO 8601 UTC | Timestamp of the audit section's last write |

**Do not modify** the schema of this file without updating `ingest-nightly`,
`check-audit-liveness`, and this contract simultaneously. This file predates
the signal contract; its schema is locked at v1 for Phase F.

---

### 2. `backup_status.json`

- **Path (host):** `ai-stack/ingest/logs/backup_status.json`
- **Path (container):** `/opt/ingest/logs/backup_status.json`
- **Producer:** `ai-stack/ingest/bin/backup-probe` (new, F-2; runs as root at 03:30)
- **Existing signal:** No — created in F-2.

```json
{
  "schema_version": 1,
  "probed_at": "2026-06-28T03:30:00Z",
  "status": "ok",
  "snapshot_id": "d6c12657",
  "snapshot_time": "2026-06-28T03:00:47Z",
  "files_new": 2380,
  "files_changed": 0,
  "data_added_mb": 68.4
}
```

**Field reference:**

| Field | Type | Description |
|---|---|---|
| `schema_version` | int | Always `1` |
| `probed_at` | ISO 8601 UTC | When `backup-probe` ran and wrote this file |
| `status` | `"ok"` \| `"no_snapshot_tonight"` \| `"error"` | See status rules below |
| `snapshot_id` | string \| `null` | 8-char restic snapshot ID; `null` if no snapshot found |
| `snapshot_time` | ISO 8601 UTC \| `null` | Timestamp of the snapshot; `null` if no snapshot found |
| `files_new` | int \| `null` | New files in the snapshot (from restic JSON output) |
| `files_changed` | int \| `null` | Changed files in the snapshot |
| `data_added_mb` | float \| `null` | Data added to the repository (MiB) |

**`status` rules:**
- `"ok"` — the latest restic snapshot's `snapshot_time` falls within the
  expected nightly backup window (configurable; default: within the 4 hours
  preceding `probed_at`). Backup ran tonight.
- `"no_snapshot_tonight"` — the latest snapshot exists but its timestamp
  predates the expected window. The backup script ran but produced no new
  snapshot, or no backup has run since the previous night. This is distinct
  from failure; it may indicate the backup is still running.
- `"error"` — `backup-probe` itself failed (e.g., `restic` command failed,
  passphrase unavailable, repository unreadable). `snapshot_id` and all
  data fields are `null`.

**Design note:** `duration_seconds` and `prune_removed` are not included.
They are not available from `restic snapshots --json`; extracting them would
require log parsing, which is fragile. This is an intentional omission, not
an oversight. Add them in a v2 schema if needed.

**`homelab-backup.sh` is not modified.** This signal is produced by a
separate `backup-probe` script reading the restic repository after the backup
window. The backup script remains untouched.

---

### 3. `container_status.json`

- **Path (host):** `ai-stack/ingest/logs/container_status.json`
- **Path (container):** `/opt/ingest/logs/container_status.json`
- **Producer:** `ai-stack/ingest/bin/container-probe` (new, F-2; runs as diego at 04:00)
- **Existing signal:** No — created in F-2.

**Normal payload:**

```json
{
  "schema_version": 1,
  "generated_at": "2026-06-28T04:00:00Z",
  "container_count": 17,
  "all_running": true,
  "degraded": [],
  "containers": [
    {"name": "openwebui",          "status": "running", "running": true},
    {"name": "qdrant",             "status": "running", "running": true},
    {"name": "ollama-proxy",       "status": "running", "running": true},
    {"name": "ollama",             "status": "running", "running": true},
    {"name": "homeassistant",      "status": "running", "running": true},
    {"name": "nginx-proxy-manager","status": "running", "running": true},
    {"name": "portainer",          "status": "running", "running": true},
    {"name": "guardian-web",       "status": "running", "running": true},
    {"name": "zigbee2mqtt",        "status": "running", "running": true},
    {"name": "mosquitto",          "status": "running", "running": true},
    {"name": "cloudflared",        "status": "running", "running": true},
    {"name": "cloudflared-amarolab","status": "running","running": true},
    {"name": "aurora-piper",       "status": "running", "running": true},
    {"name": "aurora-piper-http",  "status": "running", "running": true},
    {"name": "aurora-whisper",     "status": "running", "running": true},
    {"name": "aurora-whisper-http","status": "running", "running": true},
    {"name": "aurora-wakeword",    "status": "running", "running": true}
  ]
}
```

**Error payload** (Docker daemon unreachable or probe failure):

```json
{
  "schema_version": 1,
  "generated_at": "2026-06-28T04:00:00Z",
  "probe_error": "docker command failed: ...",
  "container_count": null,
  "all_running": null,
  "degraded": null,
  "containers": null
}
```

**Field reference:**

| Field | Type | Description |
|---|---|---|
| `schema_version` | int | Always `1` |
| `generated_at` | ISO 8601 UTC | When `container-probe` ran |
| `probe_error` | string \| absent | Present only on probe failure; error message truncated to 200 chars |
| `container_count` | int \| `null` | Total containers found; `null` on probe error |
| `all_running` | bool \| `null` | `true` if every container has `running: true`; `null` on probe error |
| `degraded` | string[] \| `null` | Names of containers with `running: false`; `null` on probe error |
| `containers` | object[] \| `null` | Per-container detail; `null` on probe error |
| `containers[].name` | string | Container name (leading `/` stripped) |
| `containers[].status` | string | Raw Docker state string (`"running"`, `"exited"`, `"paused"`, etc.) |
| `containers[].running` | bool | `true` only when `status == "running"` |

**Status rules:**
- **Normal** — `container_count` ≥ 0, `containers` is an array, `all_running` and `degraded`
  reflect actual state. If any container is not running, `all_running` is `false` and its
  name appears in `degraded`. `aurora-context` sets `overall_status: "degraded"` when
  `degraded` is non-empty.
- **Error** — `probe_error` is present; all data fields are `null`. `aurora-context` treats
  this the same as a missing file (adds `container_status.json` to `signals_missing`). This
  is preferred over leaving yesterday's healthy file in place, because stale success is worse
  than an explicit probe failure.

**Expected baseline:** 17 containers as of 2026-06-28. `container-probe` is fully dynamic —
it never enforces a hardcoded count. If `container_count` differs from 17, `aurora-context`
reports the delta to Aurora. Update this document when containers are intentionally added or
removed.

---

### 4. `aurora-context.json`

- **Path (host):** `ai-stack/aurora/aurora-context.json`
- **Path (container):** `/opt/aurora/aurora-context.json`
- **Producer:** `ai-stack/ingest/bin/aurora-context` (new, F-2; runs as diego at 04:15)
- **Consumers:** `system_status` tool (F-2); Open WebUI Filter reads the `.md`
  variant (F-3); HA voice reads the `.txt` variant (F-3)
- **Existing signal:** No — created in F-2.

```json
{
  "schema_version": 1,
  "generated_at": "2026-06-28T04:15:00Z",
  "overall_status": "ok",
  "ingest": {
    "status": "ok",
    "last_run_end": "2026-06-28T00:30:13Z",
    "last_run_rc": 0
  },
  "backup": {
    "status": "ok",
    "snapshot_id": "d6c12657",
    "snapshot_time": "2026-06-28T03:00:47Z",
    "data_added_mb": 68.4
  },
  "audit": {
    "status": "ok",
    "age_days": 0
  },
  "containers": {
    "all_running": true,
    "count": 17,
    "degraded": []
  },
  "home": {
    "anomalies": []
  },
  "signals_missing": []
}
```

**Field reference:**

| Field | Type | Description |
|---|---|---|
| `schema_version` | int | Always `1` |
| `generated_at` | ISO 8601 UTC | When `aurora-context` ran |
| `overall_status` | `"ok"` \| `"degraded"` \| `"unknown"` | See rules below |
| `ingest.status` | `"ok"` \| `"error"` \| `"signal_missing"` | Derived from `health.json` |
| `ingest.last_run_end` | ISO 8601 UTC \| `null` | Passed through from `health.json` |
| `ingest.last_run_rc` | int \| `null` | Passed through from `health.json` |
| `backup.status` | `"ok"` \| `"no_snapshot_tonight"` \| `"error"` \| `"signal_missing"` | Derived from `backup_status.json` |
| `backup.snapshot_id` | string \| `null` | Passed through; `null` when missing/error |
| `backup.snapshot_time` | ISO 8601 UTC \| `null` | Passed through |
| `backup.data_added_mb` | float \| `null` | Passed through |
| `audit.status` | `"ok"` \| `"stale"` \| `"missing"` \| `"signal_missing"` | Derived from `health.json` |
| `audit.age_days` | float \| `null` | Passed through from `health.json` |
| `containers.all_running` | bool \| `null` | Passed through; `null` when signal missing |
| `containers.count` | int \| `null` | Total count from `container_status.json` |
| `containers.degraded` | string[] | Names of non-running containers |
| `home.anomalies` | string[] | Home state anomalies (populated in F-5; empty until then) |
| `signals_missing` | string[] | Names of signal files absent at generation time |

**`overall_status` rules:**
- `"ok"` — all present signals have status `"ok"`. Missing signals do **not**
  downgrade `overall_status`; they are represented in `signals_missing`.
- `"degraded"` — at least one present signal has a non-ok status
  (`"error"`, `"no_snapshot_tonight"`, `"stale"`, or `running: false` on any container).
- `"unknown"` — all three input signal files are missing.

**Companion text artifacts** (same producer, not documented in detail here):

- **`aurora-context.md`** — LLM-formatted prose summary. Consumed by the
  Open WebUI Filter (F-3). Begins with `[Aurora context — YYYY-MM-DD HH:MM UTC]`.
  Honest about missing signals and data age. Never omits a known-bad status.
- **`aurora-context-voice.txt`** — Single-line ≤200-character summary for the
  HA voice LLM configuration. Format: `YYYY-MM-DD HH:MM | <status> | <backup> | <containers> | <anomalies>`.

---

## Nightly Production Schedule

After all F-2 cron entries are in place, the complete signal write order:

| Time | Producer | Signal written |
|---|---|---|
| 02:30 | `ingest-nightly` | `health.json` (ingest section) |
| 03:00 | `homelab-backup.sh` | *(backup runs; no signal yet)* |
| 03:30 | `backup-probe` | `backup_status.json` |
| 03:30 | `check-audit-liveness` | `health.json` (audit section) |
| 04:00 | `container-probe` | `container_status.json` |
| 04:15 | `aurora-context` | `aurora-context.json`, `aurora-context.md`, `aurora-context-voice.txt` |

`backup-probe` and `check-audit-liveness` at 03:30 are independent — no
ordering constraint between them. Both are complete well before 04:00.

---

## Adding a New Signal

1. Define the schema here (new section, `schema_version: 1`).
2. Write the producer script.
3. Update `aurora-context` to read the new file and merge its data into
   `aurora-context.json` and `aurora-context.md`.
4. Update the nightly schedule table above.
5. Update `04_ai_system/phase_f_architecture.md` §6.1 signal layer table.
6. Document the change in an apply log under `09_logs/`.

Do not add signals that duplicate existing ones. One producer per signal file.

---

*Signals contract v1. Introduced Phase F-2, 2026-06-28.*
