# Phase E — E4-b Backup Consistency Decision Record

**Date:** 2026-06-27
**Phase:** E — Knowledge Platform Foundation
**Step:** E4-b — Qdrant backup-consistency spike (F-05a)
**Outcome:** No change required

---

## Finding under review

**F-05a (E-0 operational audit, 2026-06-27):**

> The Qdrant store is backed up hot/raw (no quiesce or snapshot-API, unlike
> the SQLite `.backup` handling); restore-consistency is unverified.
> Severity: Med. Steps: E-4 + E-5.

The finding identified two gaps:
1. No quiesce or snapshot-API mechanism before backup.
2. Restore-consistency unverified (no drill had ever been performed).

Gap 2 was the gating uncertainty. Gap 1 was the theoretical risk. E4-b evaluates whether closing gap 2 (via E5-b) is sufficient to accept the current approach, or whether gap 1 must also be addressed.

---

## Evidence

### E5-b restore drill (2026-06-27) — primary evidence

Snapshot `228e4183` (2026-06-27 03:00:01) was captured hot — Qdrant was running
at backup time, with no quiesce or snapshot-API invoked.

Restore into isolated disposable container (`qdrant/qdrant:v1.17.0`,
loopback-only `127.0.0.1:6399`, `/mnt/storage/restore-drills/e5b-20260627`):

| Collection    | Prod points | Restored points | Match |
|---------------|-------------|-----------------|-------|
| homelab_docs  | 4049        | 4049            | ✓     |
| guardian_cloud| 872         | 872             | ✓     |
| ensambla2     | 419         | 419             | ✓     |
| infra_audits  | 280         | 280             | ✓     |
| myfreetour    | 0           | 0               | ✓     |

Retrieval fixture parity: **16/16 PASS** — top-30 set and top-6 rank order
identical for all 16 queries across all 4 active collections (es + en).

E5-b conclusion: "The backup is a byte-exact, functionally complete replica of
production."

Full evidence: `09_logs/2026-06-27_phaseE_E5b_restore_drill_applied.md`

### Cron order (operational mitigation)

```
02:30  ingest-nightly   (runtime: ~24 seconds — complete by 02:31)
03:00  homelab-backup   (restic snapshot)
```

The 29-minute window between ingest completion and backup start means the
backup is taken against a quiescent Qdrant under all normal operating conditions.

### Write overlap scenario (residual risk analysis)

The only scenario where the backup could capture an in-progress write is:

1. An operator-triggered manual `bin/ingest sync` running at exactly 03:00 AM, OR
2. The nightly ingest run itself is delayed past 03:00 (cron scheduler failure or
   severe system load prolonging a 24-second job to 30 minutes).

Scenario 1: operationally implausible for a personal lab. No automation or
workflow triggers a manual sync at 03:00.

Scenario 2: would require either cron daemon failure (in which case the backup
would also likely be affected) or a 75× slowdown of the ingest run. Neither
scenario is realistic at the current scale (5620 points, batch ingest).

### Qdrant segment architecture

Qdrant stores data in segments. After a write completes and the writing process
exits, all segment data is flushed to disk. A restic snapshot of a quiescent
Qdrant (no active writes) captures a structurally consistent state. This is the
state at 03:00 under normal operation.

---

## Alternatives considered

### A. Quiesce-before-backup (stop → backup → start)

Would eliminate the residual write-overlap risk entirely. Trade-offs:

- **Downside:** Qdrant downtime of ~1–2 minutes nightly at 03:00. Affects
  HA Assist voice pipeline and Open WebUI if active at that hour.
- **Downside:** New failure mode: if Qdrant fails to restart, recovery requires
  manual intervention.
- **Benefit:** Zero theoretical write-overlap risk.
- **Assessment:** Downtime risk exceeds write-overlap risk at current scale.
  Rejected.

### B. Qdrant snapshot API (POST /collections/{name}/snapshots)

Creates a consistent point-in-time snapshot per collection for backup. Trade-offs:

- **Downside:** Requires 4 additional script operations (create snapshot per
  collection, wait, backup snapshot files, delete snapshot) and coordinated
  error handling.
- **Downside:** New failure mode: snapshot creation fails silently → restic
  captures stale or partial snapshot files.
- **Benefit:** Atomic, consistent per-collection snapshot regardless of write
  activity.
- **Assessment:** Adds operational complexity for a risk already empirically
  mitigated by cron ordering. Appropriate if write load increases significantly
  (real-time ingestion, high concurrency). Not justified at current scale.
  Rejected.

### C. No change (accept current approach)

- Current approach: hot backup of the Qdrant storage directory via restic.
- Cron order provides a 29-minute quiescent window.
- E5-b PASS proves the approach produces a byte-exact, functionally complete
  replica.
- Residual risk (write overlap) is operationally implausible under current
  usage patterns.
- Recovery capability is proven (2-minute restore, 16/16 fixture parity).
- **Selected.**

---

## Decision

**No change required.**

The current hot-backup approach is acceptable for AMAROLAB at its current scale
and write pattern. F-05a is closed.

---

## Residual risk (documented, accepted)

The residual risk of a backup capturing a mid-write state is not fully
eliminated. It is accepted on the following grounds:

1. Cron ordering makes write-overlap occurrence implausible under normal operation.
2. E5-b empirically demonstrated that the existing hot-backup approach produces
   a byte-exact, functionally complete replica.
3. The cost of eliminating the residual risk (quiesce downtime or snapshot-API
   complexity) exceeds the expected risk reduction at current scale.

**Re-evaluate this decision if:**
- Ingest moves to real-time or near-real-time (sub-hourly) writes.
- The Qdrant index grows to the point where a full sync takes longer than
  the 30-minute cron gap.
- Additional write sources are introduced that bypass the ingest pipeline cron.

---

## Findings closed

- **F-05a (hot backup consistency):** closed — no change required. Evidence:
  E5-b 16/16 PASS; cron ordering; residual risk documented and accepted.
