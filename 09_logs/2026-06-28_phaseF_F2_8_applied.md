# Phase F — F2-8 `aurora-signals` Cron Installation + Pipeline Validation

- **Date:** 2026-06-28
- **Phase step:** F-2 — Signal Layer and Context Generation
- **Sub-step:** F2-8 — install `/etc/cron.d/aurora-signals`; validate the nightly signal pipeline end-to-end
- **Status:** COMPLETE (manual validation) — first unattended nightly cycle confirmed in F2-9

---

## 1. What was applied

The three F-2 signal producers are now scheduled as a single root-owned cron file,
`/etc/cron.d/aurora-signals`, running after the 03:00 restic backup. Tracked source
copy committed at `ai-stack/ingest/etc/cron.d/aurora-signals` (installed via `sudo cp`,
mirroring the E4-a logrotate convention).

| Time (Europe/Madrid) | User | Script | Writes |
|---|---|---|---|
| 03:30 | root | `bin/backup-probe` | `ai-stack/ingest/logs/backup_status.json` |
| 04:00 | diego | `bin/container-probe` | `ai-stack/ingest/logs/container_status.json` |
| 04:15 | diego | `bin/aurora-context` | `ai-stack/aurora/aurora-context.{json,md,voice}` |

Mixed-user file by necessity: `backup-probe` must run as root (reads
`/etc/restic/passwd-homelab`); `container-probe` and `aurora-context` run as diego
(docker-group + reads the diego-owned signal/context dirs). All three are stdlib-only
Python 3 — no venv activation required. Cron `PATH` mirrors the existing
`/etc/cron.d/homelab-backup`.

**Scheduling notes:**
- 03:30 co-schedules with the existing `check-audit-liveness` (diego crontab). They
  write different files (`backup_status.json` vs `health.json` audit section); no
  contention. `aurora-context` at 04:15 reads both well after they complete.
- Upstream dependency order satisfied: ingest-nightly 02:30 + check-audit-liveness 03:30
  (→ `health.json`), backup-probe 03:30 (→ `backup_status.json`), container-probe 04:00
  (→ `container_status.json`), then aurora-context 04:15 aggregates all three.
- Cron output (the probes' single stderr diagnostic line) is appended to
  `ai-stack/ingest/logs/aurora-signals.log` (gitignored; pre-created `diego:diego 0664`
  so a root-run never creates it root-owned and locks out the diego appenders). Rotation
  added to `ai-stack/ingest/etc/logrotate.d/homelab-ingest` (weekly, 8 weeks, `su diego diego`).

**Backup window:** the cron entry uses `backup-probe`'s default 4h freshness window. At
03:30, ~0.5h after the 03:00 backup, that yields `status: ok`. (Today's manual validation
used `BACKUP_PROBE_WINDOW_HOURS=24` to prove the restic read path despite the snapshot
being ~11h old at midday — see §3.)

---

## 2. Installed cron file

`/etc/cron.d/aurora-signals` — `-rw-r--r-- 1 root root 1328` (root-owned, not
group/world-writable, so cron honors it):

```cron
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

30 3 * * * root  /home/diego/homelab/ai-stack/ingest/bin/backup-probe    >> /home/diego/homelab/ai-stack/ingest/logs/aurora-signals.log 2>&1
0  4 * * * diego /home/diego/homelab/ai-stack/ingest/bin/container-probe >> /home/diego/homelab/ai-stack/ingest/logs/aurora-signals.log 2>&1
15 4 * * * diego /home/diego/homelab/ai-stack/ingest/bin/aurora-context  >> /home/diego/homelab/ai-stack/ingest/logs/aurora-signals.log 2>&1
```

---

## 3. Validation results

### Privileged (operator-run, 2026-06-28 ~13:54)

| Check | Result |
|---|---|
| `/etc/cron.d/aurora-signals` installed | **PASS** `-rw-r--r-- root root 1328` |
| `systemctl is-active cron` | **PASS** `active` |
| `logrotate -d /etc/logrotate.d/homelab-ingest` (parse) | **PASS** `logrotate parses OK` |
| Root link: `sudo BACKUP_PROBE_WINDOW_HOURS=24 backup-probe` | **PASS** `ok snapshot=d6c12657 age=10.9h window=24.0h` |

### Non-privileged (diego, post-install, cron-like env)

| # | Step | Result |
|---|---|---|
| 1 | `container-probe` | **PASS** rc=0 — `degraded (openwebui_pre_f2_6) count=18` |
| 2 | `aurora-context` | **PASS** rc=0 — `degraded`, `signals_missing=[]`, sole degrade = rollback container |
| 3 | `backup_status.json` | **PASS** `status=ok`, `snapshot_id=d6c12657`, `root:root 0644` |
| 4 | `container_status.json` | **PASS** `count=18`, `all_running=false`, `degraded=[openwebui_pre_f2_6]`, `diego:diego 0644` |
| 5 | `aurora-context.json` | **PASS** `overall=degraded`; ingest ok / backup ok / audit ok; `signals_missing=[]`; `diego:diego 0644` |
| 6 | `system_status` (full mode, committed source run inside `openwebui` against live `/opt/aurora`) | **PASS** — see output below |

**Step 6 — `system_status` full-mode output (2026-06-28 11:59 UTC):**
```
AMAROLAB System Status — 2026-06-28 11:59 UTC

Overall: degraded
Reasons:
  • containers: 1 stopped (openwebui_pre_f2_6)

---

Context:     2026-06-28 11:57 UTC (0.0h ago)
Torre (live): reachable (2ms)
System:      CPU 1.4% | RAM 22.1% | Disk 29.3%

Ingest:      ok — last run 2026-06-28 00:30 UTC (11.5h ago, rc=0)
Backup:      ok — snapshot d6c12657 at 2026-06-28 01:00 UTC (11.0h ago)
Audit:       ok — last entry age 0 days
Containers:  17/18 running — stopped: openwebui_pre_f2_6

Signals missing: none
```

`Overall: degraded` is **expected and accepted for tonight**: the sole degrade reason is
`openwebui_pre_f2_6`, the F2-6 rollback container intentionally retained until one
successful nightly cycle passes. Once it is removed, container-probe returns to 17/17 and
the pipeline reports `ok`. All other signals (ingest, backup, audit, Torre) are healthy
and the live Torre probe from inside the container succeeds (2ms).

---

## 4. F2-7 / F2-9 framing (operator decision, 2026-06-28)

- **F2-7 is a validation gate, not an implementation work package.** The Phase F
  architecture (`04_ai_system/phase_f_architecture.md`) defines only sub-phases F-0…F-6;
  the `F2-N` numbering is an apply-log working convention. The "F2-7" slot is the
  **G-F1-01 chat-level tool-forwarding gate** (manual browser session: ask "¿Cuál es el
  estado del sistema?" / "¿Qué hora es?" and confirm the tool fires) — recorded as a
  platform finding in `09_logs/2026-06-28_phaseF_F1_system_prompt_installed.md §3`. It
  remains open and is the operator's manual check; it does not block F2-8.
- **F2-9 = F2 closeout:** confirm the first unattended nightly cycle (03:30/04:00/04:15),
  reconcile the onboarding triad (`CURRENT_STATE.md`, `ROADMAP.md`, `AMAROLAB_HANDOFF.md`)
  to repository reality, F2 review, then commit and **push only after approval**.

---

## 5. Files changed (staged for F2-8 commit)

| File | Action |
|---|---|
| `ai-stack/ingest/etc/cron.d/aurora-signals` | Created — tracked source copy of the installed cron |
| `ai-stack/ingest/etc/logrotate.d/homelab-ingest` | Modified — added `aurora-signals.log` rotation stanza |
| `09_logs/2026-06-28_phaseF_F2_8_applied.md` | Created — this document |

Not committed (gitignored runtime artifacts): `aurora-signals.log`, `backup_status.json`,
`container_status.json`, `aurora-context.{json,md,voice}`. System files
(`/etc/cron.d/aurora-signals`, `/etc/logrotate.d/homelab-ingest`) live outside the repo;
the repo holds their source copies.

---

## 6. Rollback

```bash
sudo rm /etc/cron.d/aurora-signals     # cron auto-detects removal; no reload needed
```
The probe scripts and signal/context artifacts are unaffected by removing the schedule.
The logrotate stanza is inert without the log and may be left in place.

---

## 7. Open items entering F2-9

| Item | Status |
|---|---|
| First unattended nightly cycle confirmation (03:30/04:00/04:15 → fresh artifacts, backup `ok`) | **Pending — overnight to 2026-06-29** |
| Remove `openwebui_pre_f2_6` rollback container (→ pipeline `ok`) | After one successful nightly cycle |
| G-F1-01 chat-level tool validation gate (browser) | Pending — operator manual check |
| Onboarding-triad reconciliation (CURRENT_STATE / ROADMAP / AMAROLAB_HANDOFF) | F2-9, before final push |
| Portainer `ai-local` stack re-association (drift from F2-6) | Deferred maintenance — needs sudo + window |

---

*F2-8 complete: `aurora-signals` cron installed and the signal pipeline validated
end-to-end (probes → signals → aurora-context → system_status). Degraded status tonight is
the retained rollback container only, as accepted. First unattended nightly cycle confirmed
in F2-9.*
