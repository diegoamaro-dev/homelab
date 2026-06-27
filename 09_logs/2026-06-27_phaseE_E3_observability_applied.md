# Phase E — E-3 Observability Bundle — Apply Log

- **Date:** 2026-06-27
- **Phase:** E — Knowledge Platform Foundation
- **Steps:** E3-a (index freshness signal), E3-b (run-health signal), E3-c (audit-log liveness)
- **Findings addressed:** F-01 (cron-action part), F-03, F-10 (observable signal)
- **Outcome:** PASS
- **Operator:** Diego Vázquez Amaro

---

## Objective

Add three observability signals to the knowledge platform so that operational
health is continuously visible — without changing ingest behaviour, retrieval
behaviour, or any production data path.

All three signals are unified into a single machine-readable file:
`ai-stack/ingest/logs/health.json`.

---

## Architecture

Two scripts, one crontab update. No new services, no daemons, no dashboards.

```
02:30  ingest-nightly    — runs bin/ingest sync, frames ingest.log, writes ingest section
03:30  check-audit-liveness — reads audit log, writes audit section
```

Both scripts follow a read-modify-write pattern with atomic rename
(`health.json.tmp` → `health.json`). The audit section is preserved when
`ingest-nightly` writes, and the ingest section is preserved when
`check-audit-liveness` writes. No race condition: the two scripts run one hour apart.

`health.json` is gitignored via the existing `ai-stack/ingest/logs/` pattern in
`.gitignore`. It is operational state, not documentation.

---

## Files delivered

### `ai-stack/ingest/bin/ingest-nightly` (new, executable)

Replaces the raw `bin/ingest sync >> ingest.log` cron invocation.

Responsibilities:
1. Write `=== RUN START <ISO UTC> ===` to `ingest.log`.
2. Run `bin/ingest sync`, capturing exit code without propagating early exit.
3. Write `=== RUN END <ISO UTC> rc=N ===` to `ingest.log`.
4. Update `logs/health.json` ingest section atomically.
5. Carry `last_successful_run_end` forward on failure (read-modify-write).
6. Recompute `overall_status` from both sections.
7. Exit with the original ingest rc (so cron observes the failure).

### `ai-stack/ingest/bin/check-audit-liveness` (new, executable)

Responsibilities:
1. Read the last non-empty line of `/srv/homelab/data/openwebui/amarolab-audit.log`.
2. Parse `ts` field; compute age in whole days from `now(UTC)`.
3. Set `status`: `"ok"` if `age_days < 7`, `"stale"` if `age_days >= 7`,
   `"missing"` if file absent/empty, `"unparseable"` if last line not valid JSON.
4. Update `logs/health.json` audit section atomically.
5. Recompute `overall_status` from both sections.
6. Exit 0 in all cases (liveness check never fails the cron).

### Crontab (modified)

```
# Before (Phase 1 P1.10):
30 2 * * *   /home/diego/homelab/ai-stack/ingest/bin/ingest sync >> /home/diego/homelab/ai-stack/ingest/logs/ingest.log 2>&1

# After (E-3):
30 2 * * *   /home/diego/homelab/ai-stack/ingest/bin/ingest-nightly
30 3 * * *   /home/diego/homelab/ai-stack/ingest/bin/check-audit-liveness
```

---

## `health.json` schema

```json
{
  "schema_version": 1,
  "updated_at": "<ISO UTC — most recent write>",
  "overall_status": "ok | degraded | unknown",

  "ingest": {
    "last_run_start":          "<ISO UTC>",
    "last_run_end":            "<ISO UTC>",
    "last_run_rc":             0,
    "last_run_status":         "ok | failed",
    "last_successful_run_end": "<ISO UTC or null>",
    "updated_at":              "<ISO UTC>"
  },

  "audit": {
    "last_entry_ts":  "<ISO with TZ>",
    "age_days":       9,
    "status":         "ok | stale | missing | unparseable",
    "updated_at":     "<ISO UTC>"
  }
}
```

`overall_status` logic:
- `"ok"` — both `ingest.last_run_status == "ok"` AND `audit.status == "ok"`
- `"degraded"` — either signal is not ok (failed / stale / missing / unparseable)
- `"unknown"` — neither section has been written yet (first-boot state)

Each section carries its own `updated_at` so consumers can detect a frozen
section independent of `overall_status` (e.g. if the cron stops running
entirely, `ingest.updated_at` will age past 25 h).

---

## Validation evidence

### V-1 — Audit section created correctly

```
$ bin/check-audit-liveness && echo OK
OK
$ cat logs/health.json
{
  "schema_version": 1,
  "updated_at": "2026-06-27T18:41:35Z",
  "overall_status": "degraded",
  "ingest": null,
  "audit": {
    "last_entry_ts": "2026-06-17T23:21:08.172475+00:00",
    "age_days": 9,
    "status": "stale",
    "updated_at": "2026-06-27T18:41:35Z"
  }
}
```

`last_entry_ts` matches the last line of `amarolab-audit.log`.
`age_days: 9` is accurate (2026-06-17 23:21 UTC to 2026-06-27 18:41 UTC = 9 full days).
`status: "stale"` is correct — the audit log has been stale since 2026-06-18 (F-10).
`overall_status: "degraded"` is correct — ingest section not yet written, audit is stale.

### V-2 — Ingest section updates after controlled wrapper run

```
$ bin/ingest-nightly
$ echo "exit: $?"
exit: 0
$ cat logs/health.json
{
  "schema_version": 1,
  "updated_at": "2026-06-27T18:42:33Z",
  "overall_status": "degraded",
  "ingest": {
    "last_run_start":          "2026-06-27T18:42:09Z",
    "last_run_end":            "2026-06-27T18:42:33Z",
    "last_run_rc":             0,
    "last_run_status":         "ok",
    "last_successful_run_end": "2026-06-27T18:42:33Z",
    "updated_at":              "2026-06-27T18:42:33Z"
  },
  "audit": {
    "last_entry_ts": "2026-06-17T23:21:08.172475+00:00",
    "age_days": 9,
    "status": "stale",
    "updated_at": "2026-06-27T18:41:35Z"
  }
}
```

`ingest.last_run_status: "ok"` and `rc: 0` reflect successful sync.
`last_successful_run_end` is set to the run end timestamp.
`audit` section preserved unchanged (different `updated_at` confirms separate writes).

### V-3 — `overall_status: "degraded"` reflects audit stale state

`overall_status` is `"degraded"` even though `ingest.last_run_status == "ok"`,
because `audit.status == "stale"`. This is the correct behaviour: one failing signal
degrades the overall status. The platform cannot be `"ok"` while the audit log is stale.

### V-4 — `ingest.log` contains run boundaries

```
=== RUN START 2026-06-27T18:42:09Z ===
=== RUN END 2026-06-27T18:42:33Z rc=0 ===
```

### V-5 — No temp file remains

```
$ ls ai-stack/ingest/logs/
health.json  ingest.log
```

No `.health.json.tmp` — atomic rename succeeded and cleaned up.

### V-6 — No runtime state in git

```
$ git status
...
Archivos sin seguimiento:
  ai-stack/ingest/bin/check-audit-liveness
  ai-stack/ingest/bin/ingest-nightly
```

`health.json` does not appear — correctly excluded by `ai-stack/ingest/logs/`
in `.gitignore`.

### V-7 — Crontab contains correct entries

```
30 2 * * *   /home/diego/homelab/ai-stack/ingest/bin/ingest-nightly
30 3 * * *   /home/diego/homelab/ai-stack/ingest/bin/check-audit-liveness
```

---

## Current health state (post-E-3)

`health.json` as of 2026-06-27T18:42:33Z:

| Field | Value |
|---|---|
| `overall_status` | `degraded` |
| `ingest.last_run_status` | `ok` |
| `ingest.last_successful_run_end` | `2026-06-27T18:42:33Z` |
| `audit.status` | `stale` |
| `audit.age_days` | 9 |
| `audit.last_entry_ts` | `2026-06-17T23:21:08.172475+00:00` |

`"degraded"` is the expected and correct state: the audit log (F-10) has not
been updated since 2026-06-18. E3-c now makes this stale state continuously
visible. The root cause investigation is E5-c (pending, not Phase E-3 scope).

---

## Observations

### Obs-1 — E5-c dependency

E3-c reports `"stale"` and will continue to do so until E5-c resolves the
root cause of the audit log not being updated since 2026-06-18 (F-10).
This is the intended behaviour: E3-c makes the problem visible, not hidden.

### Obs-2 — knowledge_platform_contract.md updated

The contract's §5 Operational Invariants referenced `bin/ingest sync` directly.
Updated to reference `bin/ingest-nightly` and added the health.json operational
health section.

### Obs-3 — HA/Aurora integration (future, not Phase E)

`health.json` is designed for eventual HA sensor consumption. The planned path:
- A RESTful sensor or MQTT publication from the scripts exposes `health.json`
  fields as HA entities.
- Aurora uses `ha_get_state("sensor.aurora_platform_status")` to answer
  "Is the knowledge platform healthy?" without a new tool.
- No changes to the `health.json` schema are required at that point.

---

## Links

- E-3 plan: session context (2026-06-27)
- E-0 audit: `09_logs/2026-06-27_phaseE_E0_operational_audit_report.md`
- Knowledge platform contract: `04_ai_system/knowledge_platform_contract.md`
- Ingest wrapper: `ai-stack/ingest/bin/ingest-nightly`
- Audit check: `ai-stack/ingest/bin/check-audit-liveness`
