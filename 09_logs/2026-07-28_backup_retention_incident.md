# Backup Retention Incident — Stale Restic Lock and Structurally Inert Retention Policy

**Date:** 2026-07-28
**Type:** Incident record + corrected diagnosis. Operational, not a phase.
**Trigger:** Full technical audit of the running homelab, 2026-07-28 02:28–03:15 CEST.
**Production changed:** **One command only** — `restic unlock` (Stage A). No snapshot was
deleted. No backup script, cron entry, or repository configuration was modified.
**Related findings:** H-1 (backup retention failure + monitoring blind spot), L-9 →
**promoted to High** (parent-snapshot matching).

> This is a dated historical record. It states what was true on 2026-07-28 and is not
> rewritten as the situation advances (`PROJECT_RULES.md` → *Historical Documentation*).
> Corrections belong in later documents.

---

## 1. Original finding — stale lock (as first diagnosed)

The audit found that `restic forget --prune` had failed on every nightly run for
approximately 30 days, blocked by an exclusive repository lock left behind by a process
that no longer existed.

`/var/log/homelab-backup.log`, last two runs before the incident:

```
snapshot 7715bf6a saved
repo already locked, waiting up to 0s for the lock
unable to create lock in backend: repository is already locked by
  PID 226801 on homelab by root (UID 0, GID 0)
lock was created at 2026-06-27 12:30:52 (710h29m12s ago)
storage ID 06c1fdfa
the `unlock` command can be used to remove stale locks
```

The **backup half succeeded every night**; only the retention half failed. Recoverability
was never impaired — this was confirmed independently by G-F4-08 on 2026-07-27, an
empirical restic restore-drill that recovered 24 digests from snapshot `7715bf6a`.

### Lock holder confirmed dead

```
ps -p 226801            → PID 226801 does not exist
pgrep -a restic         → no restic process
pgrep -a homelab-backup → none
uptime -s               → 2026-07-25 23:50:44
```

The host rebooted on **2026-07-25**, four weeks after the lock was created on
**2026-06-27**. The process namespace containing PID 226801 no longer existed, so the lock
was unambiguously stale.

### Attribution of the lock

The lock timestamp (2026-06-27 12:30:52) falls inside the Phase E **E5-b restore-drill**
window. `09_logs/2026-06-27_phaseE_E5b_continuation_handoff.md` records that a
context-preservation checkpoint was written that day, immediately before *"a potentially
disruptive step (restic restore + disposable test container)"*. A `restic restore` takes a
repository lock; a session interrupted mid-restore orphans it.

This is **strongly supported circumstantial attribution, not proof**. The E5-b drill itself
succeeded and is correctly documented. What went unnoticed is that it left a lock behind.

---

## 2. Evidence across 30 failed retention runs

The failure is a single lock failing identically every night, reconstructed across all
retained log rotations:

| Log rotation | Snapshot saved | Lock age reported | Date |
|---|---|---|---|
| `homelab-backup.log.5.gz` | `cdda7751`, `55fc2f26` | — `Applying Policy: keep 7 daily, 4 weekly, 6 monthly` | ≤ 2026-06-27 |
| `homelab-backup.log.4.gz` | `d6c12657` | 14h29m | **2026-06-28 — first failure** |
| `homelab-backup.log.4.gz` | `c38ddcc1`, `2282b02e` | 38h29m, 62h29m | 2026-06-29, 06-30 |
| `homelab-backup.log.3.gz` | `af0f9fee` … | 182h → 230h | 2026-07-04 → 07-06 |
| `homelab-backup.log.2.gz` | `77a1ff08` … | 350h → 398h | 2026-07-11 → 07-13 |
| `homelab-backup.log.1.gz` | `401674d2` … | 518h → 566h | 2026-07-18 → 07-20 |
| `homelab-backup.log` | `aa16c536`, `7715bf6a` | 686h29m, **710h29m** | 2026-07-26, 07-27 |

**Last successful retention execution: 2026-06-27 03:00. First failure: 2026-06-28 03:00.
Unbroken thereafter.**

---

## 3. Stage A — execution and verification

Approved and executed 2026-07-28 03:04 CEST. Guards verified at execution time: running as
root, no `restic` process, no `homelab-backup.sh` running.

```
STEP 0 — locks BEFORE unlock
06c1fdfa44df33d46702d2bbfdfe742601e6b4c6a647b6e372bdde0fcfec43e5   [rc=0]

STEP 1 — restic unlock
successfully removed 1 locks                                        [rc=0]

STEP 2 — locks AFTER unlock (expect empty)
                                                                    [rc=0]
```

The removed lock's storage ID `06c1fdfa` matches the ID named in 30 nights of failure logs
exactly. **Remaining lock count: 0.**

`restic unlock` removes only locks restic classifies as stale (matching hostname, absent
PID). `--remove-all` was deliberately **not** used.

---

## 4. Stage B — retention dry-run results

Executed with the exact policy and tag filter used by `homelab-backup.sh`:

```
restic forget --tag nightly --keep-daily 7 --keep-weekly 4 --keep-monthly 6 --dry-run
```

### Inventory

| Metric | Value |
|---|---|
| Total snapshots | **42** |
| Tagged `nightly` | **42 (100 %)** |
| Untagged / other tags | **0** |
| First snapshot | `cc73b4fd`, 2026-06-13 14:06:34 |
| Latest snapshot | `4e769974`, 2026-07-28 03:00:01 |

### Dry-run outcome

| Metric | Value |
|---|---|
| `keep` blocks emitted | **41** |
| `remove` blocks emitted | **0** |
| Snapshots kept | **42** |
| **Snapshots that would be removed** | **0** |

Restic emitted no `remove` block at all. Every snapshot was retained, and each was
classified as satisfying all three retention dimensions simultaneously:

```
keep 1 snapshots:
ID        Time                 Host      Tags      Reasons           Paths
7715bf6a  2026-07-27 03:00:02  homelab   nightly   daily snapshot    …
                                                   weekly snapshot   /tmp/homelab-backup-snapshots/2026-07-27
                                                   monthly snapshot
```

41 groups for 42 snapshots. The single group containing two snapshots is **2026-06-17**,
where two runs occurred on the same calendar day and therefore shared an identical path
set.

---

## 5. Correction — snapshot `63c072f4` and its `nightly` tag

`CURRENT_STATE.md` records `63c072f4` as *"the D-1.5 anchor snapshot retained as the
pre-voice-pipeline rollback point"*.

**The pre-execution analysis asserted that the `--tag nightly` filter protected this anchor
from the retention policy. That assertion was wrong.**

```
63c072f4  2026-06-17 16:19:21  homelab     nightly     /etc/apache2/sites-enabled …
```

The anchor **is itself tagged `nightly`**. The tag filter does not exclude it; it is fully
in scope for `forget --tag nightly`. It survives only because the policy currently *keeps*
it — a property of the defect described in §6, not of any protective mechanism.

Verified present on both sides of the dry-run:

```
STEP 5a (before dry-run)  →  63c072f4 present, tags=[nightly]
line 1035 (in a KEEP block) →  63c072f4 … daily snapshot
STEP 5b (after dry-run)   →  PRESENT
```

**Consequence to carry forward:** there is **no tag-based protection for any snapshot in
this repository**. Any future retention change must treat `63c072f4` as an ordinary
in-scope `nightly` snapshot. If it is to be preserved deliberately, it needs an explicit
mechanism — a distinct tag, or exclusion by ID — that does not exist today.

---

## 6. Root cause — the dated path in the restic path set

`/usr/local/bin/homelab-backup.sh` builds its backup path list as:

```bash
SNAP_DIR=/tmp/homelab-backup-snapshots/$(date +%F)
mkdir -p "$SNAP_DIR"
trap 'rm -rf "$SNAP_DIR"' EXIT

# … sqlite3 .backup dumps written into "$SNAP_DIR" …

PATHS=(
  /srv/homelab/data/openwebui
  /srv/homelab/homeassistant
  /srv/homelab/data/npm
  /home/diego/homelab/ai-stack/data/qdrant
  /home/diego/homelab/03_services/zigbee-stack/zigbee2mqtt/data
  /home/diego/homelab/03_services/zigbee-stack/mosquitto/data
  /home/diego/homelab/03_services/zigbee-stack/mosquitto/config
  /home/diego/webs
  /home/diego/homelab/09_ops/runtime
  /etc/systemd/system/homelab-tools.service
  /etc/apache2/sites-enabled
  /etc/samba/smb.conf
  "$SNAP_DIR"                      # ← changes every single night
)

restic backup --tag nightly … "${PATHS[@]}"
```

`$(date +%F)` embeds the current date in the path set, so **the recorded path list is
different on every run**. Restic's default grouping for both `backup` and `forget` is
`host,paths` (confirmed against restic 0.16.4 `--help`: `--group-by … (default
host,paths)`).

The consequence is that **every nightly snapshot lands in its own group of one.**

---

## 7. Impact — two symptoms, one defect

### 7.1 Retention grouping

`--keep-daily 7` applied to a group containing exactly one snapshot keeps that one
snapshot. Applied to 41 singleton groups, it keeps all of them. The retention policy is
therefore **structurally inert**: it cannot delete anything, regardless of how many
snapshots accumulate or how long the policy runs.

This is **not** a consequence of the stale lock. Inspection of
`homelab-backup.log.6.gz` and `.5.gz` — from *before* the lock existed, when `forget` ran
successfully — shows the identical signature: `Applying Policy…` followed by repeated
`keep 1 snapshots:`, never a `remove` block.

**The retention policy has never deleted a snapshot since repository creation on
2026-06-13.** The stale lock masked an already-inert policy; it did not cause the
retention failure.

### 7.2 Parent-snapshot detection

Restic selects a parent snapshot from the group determined by the same `--group-by`
setting. With a unique path set every night there is never a matching parent, producing on
every run:

```
no parent snapshot found, will read all files
Files:  2674 new, 0 changed, 0 unmodified
processed 2674 files, 4.145 GiB in 0:02
```

Every backup is a **full re-scan of ~4.1 GiB**, and every file is reported as `new`.
Content-defined deduplication still works — only ~19–24 MiB is actually stored per night —
so the storage cost is negligible, but the change-detection signal is destroyed: it is
impossible to tell from a snapshot summary what actually changed.

**These are the same defect.** L-9 was originally recorded as a Low-severity performance
nuisance; it is in fact the mechanism behind the High-severity retention failure and is
promoted accordingly.

---

## 8. Missing backup dates observed

The inventory revealed gaps in nightly coverage:

```
first 2026-06-13   last 2026-07-28   span 46 days   distinct days 41   snapshots 42
MISSING: 2026-06-21, 2026-07-22, 2026-07-23, 2026-07-24, 2026-07-25
```

The four-night July gap ends on the day the host booted (`uptime -s` = 2026-07-25 23:50),
so the host was most likely powered off across that window. **This is an explanation, not a
verification** — no independent evidence was gathered.

`2026-06-17` carries two snapshots (`5a5eadf2` at 03:00:01 and the `63c072f4` D-1.5 anchor
at 16:19:21), consistent with a deliberate ad-hoc run.

No mechanism exists today to detect or report a missing nightly backup.

---

## 9. Current operational risk

**Materially lower than the raw finding suggests, and stated precisely:**

- **Backups are healthy and current.** The most recent snapshot is `4e769974`
  (2026-07-28 03:00:01). Every nightly run has succeeded at the backup step.
- **Recoverability is proven, not assumed** — G-F4-08 empirical restore-drill,
  2026-07-27, snapshot `7715bf6a`.
- **No capacity pressure.** `/mnt/storage` is at 1 % of 1.8 TB. Restic deduplication keeps
  each night to ~20 MiB stored.
- **Unbounded snapshot growth is real but slow**, and 42 retained snapshots represent
  *more* recovery coverage than the policy intends, not less.

**The material risks are:**

1. **The retention policy does not do what the documentation and the script both claim.**
   Any assumption built on "old snapshots are pruned after 7 days / 4 weeks / 6 months" is
   false and has always been false.
2. **No snapshot in the repository has tag-based protection**, including the anchor
   documented as a rollback point (§5).
3. **Change detection is blind.** Every file reports as `new` every night, so a snapshot
   summary cannot reveal what changed.
4. **The monitoring blind spot below.**

---

## 10. Unresolved monitoring blind spot

`ai-stack/ingest/bin/backup-probe` executes:

```python
[RESTIC_BIN, "-r", RESTIC_REPO, "--password-file", RESTIC_PASSFILE,
 "--no-lock",              # read-only; skip lock acquisition
 "snapshots", "--latest", "1", "--json"]
```

It reads **one** snapshot and compares its age against a 4-hour window. It has no
visibility into:

- the exit code of `homelab-backup.sh`,
- the `forget` / `prune` step or its failure,
- total snapshot count or growth,
- repository lock state (`--no-lock` makes it immune to the very lock that broke retention),
- missing nightly runs (§8).

Consequently `backup_status.json` reported `"status": "ok"` continuously for 30 days while
half the backup job failed nightly, and would have reported `ok` through the four-night
July gap as well.

`homelab-backup.sh` runs under `set -euo pipefail`, but `restic forget` is the **last**
command in the script, so its non-zero exit becomes the script's exit code — which cron
discards and nothing consumes.

**This blind spot is unchanged by this incident and remains open.** Phase E applied exactly
this fail-loud lesson to the ingest pipeline at **E2-a** (finding F-01); the backup path
never received it.

---

## 11. Explicit statements of record

- **No snapshot was deleted.** Snapshot count was 42 before Stage B and 42 after. The only
  `forget` invocations carried both `--tag nightly` and `--dry-run`. No `prune` command was
  executed at any point.
- **Stage C (`restic forget --prune`, actual snapshot deletion) was NOT approved and was
  NOT executed.** It remains explicitly unapproved.
- **The anchor snapshot `63c072f4` is present and intact**, verified before and after the
  dry-run.
- **No backup configuration was modified.** `/usr/local/bin/homelab-backup.sh`,
  `/etc/cron.d/homelab-backup` and `/etc/cron.d/aurora-signals` are unchanged.
- **The only mutating command executed against the repository was `restic unlock`.**
- Approving Stage C as originally specified would currently be a **no-op**: with the
  grouping defect in place, `forget` removes nothing.

---

## 12. Next remediation work required

Ordered. None of this is authorized by this document; each item needs its own approval.

| # | Work | Severity | Notes |
|---|---|---|---|
| 1 | **Fix the grouping defect** — stabilize the restic path set and/or set an explicit `--group-by` | **High** | Prerequisite for everything below. A separate remediation brief accompanies this record |
| 2 | **Re-run the retention dry-run after the fix** | High | The current dry-run measured an inert policy; its result carries no information about post-fix behaviour |
| 3 | **Decide the retention policy deliberately**, then apply it | Medium | Only after 1 and 2. Snapshot deletion is irreversible and stays operator-approved per execution |
| 4 | **Give `63c072f4` real protection** — a distinct tag or explicit exclusion | Medium | Today it is an ordinary `nightly` snapshot despite being documented as an anchor (§5) |
| 5 | **Close the monitoring blind spot** — `backup-probe` must consume the backup script's exit status, and should surface snapshot count, retention outcome and missed nights | High | Apply the E2-a fail-loud pattern to the backup path |
| 6 | **Extend backup coverage** (audit finding H-2) | High | Portainer volume, `ai-stack/.env`, `/home/diego/.secrets/`, `/etc/cron.d/aurora-signals`, openedai voice map are all outside the current path set |
| 7 | **Harden the staging directory** | Low | SQLite dumps of `webui.db` and `home-assistant_v2.db` are written into a `0755` directory under `/tmp` during the backup window. `/tmp` is also tmpfiles-managed (`D /tmp 1777 root root 30d`) |
| 8 | **Reconcile documentation** | Medium | `CURRENT_STATE.md` → Backups states "Operational" without qualification, and describes `63c072f4` as "retained" without noting it has no protective mechanism |

---

## 13. Git gate

Documentation-only. **Not committed, not pushed** — both require explicit operator approval
immediately before the command (`PROJECT_RULES.md` → *Operator Git Approval*). Author as
`Diego <diego@diegoamaro.dev>`.

**STOP at git gate.**
