# Phase F — F2-4 `aurora-context` Implementation

- **Date:** 2026-06-28
- **Phase step:** F-2 — Signal Layer and Context Generation
- **Sub-step:** F2-4 — `aurora-context` aggregator script
- **Status:** COMPLETE

---

## 1. What was implemented

New script: `ai-stack/ingest/bin/aurora-context`

Reads three signal files, applies aggregation and staleness rules, and writes
three context artifacts atomically. Runs as diego at 04:15 (after all probes).

**Inputs:**
- `ai-stack/ingest/logs/health.json` (ingest + audit sections, separate staleness per section)
- `ai-stack/ingest/logs/backup_status.json` (`probed_at` field, 26h threshold)
- `ai-stack/ingest/logs/container_status.json` (`generated_at` field, 26h threshold)

**Outputs:**
- `ai-stack/aurora/aurora-context.json` — machine-readable for `system_status` tool
- `ai-stack/aurora/aurora-context.md` — LLM prose for Open WebUI Filter / system prompt
- `ai-stack/aurora/aurora-context-voice.txt` — single-line ≤200-char summary for HA voice

All three written atomically: `.tmp` → fsync → `chmod 0644` → `os.replace()`.
The output directory `ai-stack/aurora/` is created if absent (gitignored runtime dir).

---

## 2. Staleness rules implemented (F-2 design adjustment)

Per operator decision: stale operational signals degrade, absent signals do not.

| Signal file state | `signals_missing` | `overall_status` effect |
|---|---|---|
| File absent (never written) | yes | none — first boot or new deployment |
| File exists, internal ts > 26h | yes | **degraded** — pipeline has stopped |
| File exists, `probe_error` present (container only) | yes | **degraded** — explicit probe failure |
| File exists, fresh, content non-ok | no | **degraded** — content-level problem |
| File exists, fresh, content ok | no | none |

`overall_status: "unknown"` is reserved for the case where all three signal files
are absent simultaneously (fresh deployment before first cron run).

---

## 3. Validation results

All 11 scenarios in the validation matrix passed.

| ID | Scenario | overall_status | signals_missing | Result |
|---|---|---|---|---|
| V1 | Live run (all signals present) | `degraded` | `[]` | **PASS** |
| V2 | `backup_status.json` absent | `ok` | `["backup_status.json"]` | **PASS** |
| V3 | Backup `no_snapshot_tonight` (mock) | `degraded` | `[]` | **PASS** |
| V4 | Backup `error` (mock) | `degraded` | `[]` | **PASS** |
| V5 | `health.json` ingest section stale >26h | `degraded` | `["health.json"]` | **PASS** |
| V6 | Ingest `last_run_status=failed` | `degraded` | `[]` | **PASS** |
| V7 | `audit.status=stale` | `degraded` | `[]` | **PASS** |
| V8 | `container_status.json` absent (fresh backup injected) | `ok` | `["container_status.json"]` | **PASS** |
| V9 | `container_status.json` stale >26h | `degraded` | `["container_status.json"]` | **PASS** |
| V10 | Container `probe_error` payload | `degraded` | `["container_status.json"]` | **PASS** |
| V11 | 2 containers stopped (mock) | `degraded` | `[]` | **PASS** |
| V12 | All three signal files absent | `unknown` | all three | **PASS** |

**V1 note:** Live run at 10:07 UTC correctly reports `no_snapshot_tonight` because
the snapshot is from 01:00 UTC (9.1h ago, outside the 4h window). In production the
cron fires at 04:15 CEST (~02:15 UTC), ~1.2h after the 03:00 CEST backup: `status: ok`.

**V8 note:** Initial V8 assertion expected `ok` but the live `backup_status.json` was
also `no_snapshot_tonight`, causing `degraded`. Corrected by injecting a fresh "ok"
backup mock to isolate the container-absent path. Behaviour is correct.

---

## 4. Generated artifact sample (live, 10:07 UTC)

**aurora-context.md:**
```
[Aurora context — 2026-06-28 10:07 UTC]

Status:      degraded

Ingest:      ok — last run 2026-06-28 00:30 UTC (9.6h ago, rc=0)
Backup:      no snapshot tonight — last: 2026-06-28 01:00 UTC (9.1h ago)
Audit:       ok — last entry age 0 days
Containers:  17/17 running
```

**aurora-context-voice.txt:**
```
2026-06-28 10:07 | degraded | no backup tonight | 17/17 running | no anomalies
```
Voice line: 78 chars (≤200 limit).

**Output file permissions:** `0644`, owned by diego — readable by the openwebui
container and the `system_status` tool.

---

## 5. Files created

| File | Action |
|---|---|
| `ai-stack/ingest/bin/aurora-context` | Created, committed |
| `ai-stack/aurora/aurora-context.json` | Runtime artifact, gitignored |
| `ai-stack/aurora/aurora-context.md` | Runtime artifact, gitignored |
| `ai-stack/aurora/aurora-context-voice.txt` | Runtime artifact, gitignored |

---

## 6. Open items entering F2-5

| Item | Status |
|---|---|
| `system_status` Open WebUI tool | **Next step — F2-5** |
| `/opt/aurora` bind-mount (Portainer) | Pending F2-6 (operator, manual) |
| `/etc/cron.d/aurora-signals` (all entries) | Pending end of F2 |

---

*F2-4 complete. All three context artifacts generating correctly. 11/11 validation scenarios pass.*
