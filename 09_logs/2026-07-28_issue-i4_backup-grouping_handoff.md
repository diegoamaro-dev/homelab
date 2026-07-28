# I-4 — Backup Grouping Defect — Session Handoff

**Date:** 2026-07-28
**Type:** Session handoff. Operational, not a phase.
**Remediation item:** I-4 (Program E — backup lifecycle), from the 2026-07-28 infrastructure audit.
**Production changed:** yes — `/usr/local/bin/homelab-backup.sh` replaced (three edits), one stale
repository lock removed, one attended backup run executed.
**Current safety state:** retention runs as `--dry-run`. **No snapshot can be deleted.**

> This is a dated record. It states what was true on 2026-07-28 and is **not** rewritten as the
> situation advances (`PROJECT_RULES.md` → *Historical Documentation*). Its transient status
> markers are evidence of that moment, not drift (`PROJECT_RULES.md` → *Transient Operational
> Status*, rule 4). Corrections belong in later documents.

**Purpose.** I-4 spans a session boundary and an overnight wait. This document allows a future
session to resume without relying on conversation history, per the project's session-preservation
rule in `PROJECT_RULES.md`.

Repository and password-file values are written below as `<RESTIC_REPOSITORY>` and
`<RESTIC_PASSWORD_FILE>`. Both are the values exported at the top of
`/usr/local/bin/homelab-backup.sh` and documented in `07_operations/backups.md`.

---

## 1. Issue context and root cause

The nightly backup script built its restic path set with a **dated staging directory**:

```bash
SNAP_DIR=/tmp/homelab-backup-snapshots/$(date +%F)   # ← changed every night
PATHS=( ...twelve stable paths... "$SNAP_DIR" )
restic backup --tag nightly "${PATHS[@]}"
restic forget --tag nightly --keep-daily 7 --keep-weekly 4 --keep-monthly 6 --prune
```

restic groups snapshots by `host,paths` by default, for **both** `backup` (parent selection) and
`forget` (policy application). Because the recorded path list differed on every run, **every
nightly snapshot landed in a group of one.**

One defect, two symptoms:

| Symptom | Mechanism | Finding |
|---|---|---|
| Retention structurally inert | A keep-policy applied to a group of one keeps that one. Applied to N singleton groups it keeps all N | H-1a |
| Change detection blind | No prior group member ⇒ no parent snapshot ⇒ full ~4.1 GiB re-scan nightly, every file reported `new` | L-9 (promoted to High) |

**No snapshot had ever been removed since repository creation on 2026-06-13.** The stale lock
described in `2026-07-28_backup_retention_incident.md` masked an already-inert policy; it did not
cause the failure. Confirmed independently from pre-lock log rotations: 14 successful `forget`
executions, zero `remove` blocks.

Authoritative diagnosis: [`2026-07-28_backup_retention_incident.md`](2026-07-28_backup_retention_incident.md).

---

## 2. Recovery-audit baseline

An unclean power loss occurred at **13:28:48**; the host rebooted at **13:29:31**. A full recovery
audit found **no partial state** from the interrupted session: script, cron, git working tree,
storage mount and containers were all in their documented pre-I-4 condition.

The audit surfaced one item: an **abandoned exclusive repository lock**.

| Field | Value |
|---|---|
| Lock storage ID | `28ea22d6c60de39cd4c8a5cfc0cc16639bc56a0895073e2d1b111807273105aa` |
| Created | `2026-07-28T03:04:21` |
| Type | exclusive, `root`, this host, PID from the pre-reboot process namespace |
| Attribution | the Stage B retention dry-run — **strong circumstantial, not proof** |
| Removed | 2026-07-28, plain `restic unlock` (**not** `--remove-all`) → `successfully removed 1 locks` |

The lock was **exclusive**, unlike the 2026-06-27 one, so it would have blocked `restic backup`
entirely rather than only the retention half. Left in place it would have failed the next
nightly run outright.

**This is the second abandoned lock in one month, from unrelated causes** (2026-06-27: a restore
drill; 2026-07-28: a retention dry-run). Nothing detects this class of failure. Detection is
assigned to **S-8**. Automatic `unlock` inside the nightly script is **not** recommended — it
would mask genuine concurrency. Detect automatically, remove deliberately.

### Verified baseline before any change

| Field | Value |
|---|---|
| snapshots | 42 |
| groups | 41 |
| multi-member groups | `[2]` — the 2026-06-17 pair, sharing an identical path set |
| anchor `63c072f4` | present, tags `['nightly']` |
| oldest | `2026-06-13T14:06:34` |
| newest | `2026-07-28T03:00:01` |
| `restic check` | 37/37 index files, 42/42 snapshots, **no errors** |
| locks after `check` | none — the command released its own lock cleanly |

---

## 3. Change applied

Three edits, plus two colocated comment blocks. **Everything else in the script is byte-identical**
— trap, `mkdir -p`, all twelve workload paths, the three `sqlite3 .backup` blocks, `--tag nightly`,
all `--exclude` patterns, `set -euo pipefail`, and the entire `restic backup` invocation.

```diff
-SNAP_DIR=/tmp/homelab-backup-snapshots/$(date +%F)
+SNAP_DIR=/tmp/homelab-backup-snapshots

-  --prune
+  --dry-run
```

Verified accounting of the full diff: **2 hunks · 15 lines added (13 comment, 2 functional) ·
2 lines removed · exactly 2 non-comment changed lines.**

**`--group-by` was deliberately NOT changed.** restic's default `host,paths` grouping is a safety
property: it guarantees a snapshot with a different content shape cannot justify pruning snapshots
of another shape. Discarding it was considered and rejected. A consequence is recorded in §8.

**`--dry-run` is the sole safety mechanism.** `restic forget` deletes snapshots on its own;
`--prune` only reclaims unreferenced data afterwards. Removing `--prune` is not protective.

### Installed artifact

| Field | Value |
|---|---|
| Path | `/usr/local/bin/homelab-backup.sh` |
| sha256 | `90e8eb914601cb2a805eb5af915642e8753bdea45b715c071a424170a907a45f` |
| Size / mode / owner | 2799 bytes · `0755` · `root:root` |
| `bash -n` | PASS |

---

## 4. Rollback

| Field | Value |
|---|---|
| Rollback source | `/root/i4-evidence/homelab-backup.sh.pre-I4` |
| sha256 | `a67060552dc13b296b15a1257ca6427663ec083b04577ed97f72637048245cdf` |
| Verified | byte-identical to the pre-change live script; confirmed intact **after** installation |

```bash
sudo install -m 0755 -o root -g root /root/i4-evidence/homelab-backup.sh.pre-I4 /usr/local/bin/homelab-backup.sh
```

Rollback is **file restoration only**. No repository state was mutated by the script change, so
there is nothing to undo inside restic. Cron was never modified. Recovery time under one minute.

Evidence directory `/root/i4-evidence/` (mode `0700`) contains: the pre-change script, the
installed candidate, the pre-change snapshot inventory, and the Gate 7 attended-run log.

---

## 5. Gates closed

| Gate | Result |
|---|---|
| G-I4-1 static validation | PASS — `bash -n`; diff contains only the approved edits |
| G-I4-2 disposable-repo rehearsal | PASS — see §7 |
| G-I4-3 attended run exits 0 | PASS |
| **G-I4-4 (hard) count + anchor** | **PASS** — 42 → 43 snapshots; anchor present, tags unchanged |
| G-I4-7 *(revised)* retention reports only | PASS — policy evaluated, zero removals |
| G-I4-10 `restic check` | PASS — no errors |
| G-I4-11 rollback source intact | PASS — hash verified after installation |
| G-I4-12 no stranded lock | PASS for the attended run; re-checked at Gate 8 |

Two gate definitions were **corrected during execution** and the corrections stand:

* **G-I4-6** — primary criterion is the **absence** of `no parent snapshot found`. A non-zero
  `unmodified` count is the production corollary. It cannot be evaluated on the first snapshot in
  a new group.
* **G-I4-7** — originally required a non-empty would-remove set. That was a leftover from a
  rejected design variant and is **unsatisfiable** under the approved change: legacy groups are
  untouched and the new group has too few days to exceed the policy. Revised to: *the retention
  step completes, reports a policy evaluation, and removes nothing.*

---

## 6. Gates still open

| Gate | Closes on |
|---|---|
| G-I4-5 path-set stability | the second post-fix snapshot |
| G-I4-6 parent detection restored | the second post-fix snapshot |
| G-I4-8 awareness chain healthy | the 03:30 → 04:25 signal chain |
| G-I4-9 unattended cycle reproduces | the unattended nightly run |

All four close together at Gate 8.

---

## 7. Gate 7 — attended run, observed

**Snapshot created: `6323b009`.** Exit code 0.

| Field | Predicted | Observed |
|---|---|---|
| exit code | 0 | 0 |
| keep blocks | 42 | 42 |
| `keep 2` blocks | 1 | 1 |
| remove blocks | 0 | 0 |
| would-remove entries | 0 | 0 |
| snapshots | 43 | 43 |
| groups | 42 | 42 |
| multi-member | `[2]` | `[2]` |
| anchor | present, `['nightly']` | present, `['nightly']` |
| staging path recorded | undated | `/tmp/homelab-backup-snapshots` |
| locks after run | none | none |

Backup phase: `no parent snapshot found` (**expected** — first member of a new group),
2740 files new, 1385 dirs, 50.794 MiB added / 12.525 MiB stored.

### Recorded finding — same-bucket retention behaviour

Characterized on a disposable repository during G-I4-2, then confirmed on production by the
prediction above. In a group whose snapshots share the same day, week and month, policy
`7/4/6` keeps exactly **two** — the oldest and the newest — regardless of group size:

| Members | Kept | Removed |
|---|---|---|
| 2 | 2 | 0 |
| 3 | 2 | 1 |
| 4 | 2 | 2 |
| 5 | 2 | 3 |

N = 2 producing zero removals explains why the 2026-06-17 pair survived 14 live `forget`
executions and the 2026-07-28 dry-run.

**The behaviour is established; the mechanism is not derived.** It could not be reconstructed from
restic's documented bucket semantics. **This matters at S-10**, which will collapse groups and put
snapshots into real multi-day buckets — a regime not tested here. S-10 must re-establish the
behaviour by dry-run before any irreversible prune.

---

## 8. Gate 8 — predictions, and when to check

> **Do not run the Gate 8 checks before 04:30.** The signal chain runs at 02:30, 03:00, 03:30,
> 04:00, 04:15, 04:20 and 04:25. Checking earlier reads an incomplete cycle and produces
> misleading results.

The next snapshot carries the **same** path set as `6323b009` and therefore joins its group
rather than forming a new one.

| Field | Predicted |
|---|---|
| snapshots | 44 |
| **groups** | **42 — unchanged** |
| multi-member | `[2, 2]` |
| keep blocks | 42, of which **2** are `keep 2` |
| remove blocks | 0 |
| `no parent snapshot found` | **absent** (G-I4-6) |
| `Files:` line | non-zero `unmodified`, most of ~2740 files |
| `paths[]` of the two post-fix snapshots | byte-identical (G-I4-5) |
| `backup_status.json` | `status: ok`, newest snapshot |
| locks | none |

**`groups` is the decisive number.** If it returns 43 rather than 42, the path set is not stable
and **G-I4-5 has failed** — roll back and re-investigate.

### Consequence of retaining `host,paths` grouping

The 42 legacy snapshots remain in their own groups permanently; no future snapshot can join them.
They are therefore **unreachable by the nightly policy** and cannot be removed by it. **S-10 will
need an explicit mechanism** — selection by snapshot ID, or a deliberate one-off grouping override
— executed attended. This is a handover, not a defect.

---

## 9. First would-remove observation — expected around 2026-08-04

The post-fix group gains one distinct day per night. Once it spans eight days, the oldest member
(`6323b009`, 2026-07-28) falls outside `--keep-daily 7`. Neither the weekly nor the monthly bucket
rescues it: week 31's slot goes to 2026-08-02 and July's monthly slot to 2026-07-31.

With `--dry-run` in place it will be **reported, never removed**. That report is the first real
evidence of what a live retention policy would do on this repository, and it is the input S-10
requires. **Check the nightly log on or shortly after 2026-08-04.**

---

## 10. Current safety state

* **Retention is `--dry-run`. No snapshot can be deleted by the nightly job.**
* Re-enabling deletion is **S-10** — attended, operator-approved per execution. Both the script
  comment and this document say so.
* The anchor `63c072f4` still has **no protective mechanism**. It is an ordinary `nightly`-tagged
  snapshot. Giving it real protection is **I-6**, which must land before S-10, and must use an
  explicit mechanism (a keep-tag) rather than relying on group shape.
* Backup coverage remains incomplete (**H-2** / **I-5**). Unchanged by I-4.
* The backup probe still cannot see retention outcomes, script exit status, snapshot count, lock
  state or missed nights (**H-1c** / **S-8**). Unchanged by I-4.

---

## 11. Resume — read these, then do this

**Read in this order:**

1. `00_overview/START_HERE.md`
2. `00_overview/PROJECT_RULES.md`
3. `00_overview/AMAROLAB_HANDOFF.md`
4. `00_overview/CURRENT_STATE.md`
5. `00_overview/ROADMAP.md` → *Infrastructure Remediation — 2026-07-28 audit*
6. `09_logs/2026-07-28_backup_retention_incident.md` — authoritative diagnosis
7. `09_logs/2026-07-28_amarolab_remediation_roadmap.md` — the item ledger
8. **this document**

**Then, after 04:30:**

Run the three read-only Gate 8 checks as root.

```bash
sudo sh -c 'tail -n +40 /var/log/homelab-backup.log | grep -E "no parent snapshot|Files:|Applying Policy|^keep [0-9]+ snapshots|^remove [0-9]+ snapshots|Would have removed|error|Fatal"'
```

Line 40 onward is the new content; the log held 39 lines (1752 bytes) at the pre-change baseline.

```bash
sudo restic -r "<RESTIC_REPOSITORY>" --password-file "<RESTIC_PASSWORD_FILE>" --no-lock snapshots --json
```

Group the result by `(hostname, sorted(paths))` and compare against the §8 predictions, then
confirm the two post-fix snapshots share an identical `paths` list (G-I4-5).

```bash
sudo restic -r "<RESTIC_REPOSITORY>" --password-file "<RESTIC_PASSWORD_FILE>" --no-lock list locks
```

Also inspect `ai-stack/ingest/logs/backup_status.json`, `ai-stack/aurora/` and the newest
`09_ops/runtime/` digest for G-I4-8.

**If every prediction holds:** G-I4-5, G-I4-6, G-I4-8 and G-I4-9 close, and **I-4 is complete**.
The remaining work is documentation reconciliation, then the git gate.

**If any prediction fails:** roll back with the §4 command and re-investigate before proceeding.

**Next remediation item after I-4:** **I-5** (extend backup coverage). Note that I-5 edits the
script's `PATHS` array, which changes the recorded path set and therefore starts a new group —
expected and harmless, but it must not reintroduce a variable path component.

---

## 12. Constraints in force

1. **Do not restore `--prune` or remove `--dry-run`.** That is S-10, attended and separately
   approved.
2. **Do not reintroduce a date, timestamp or any other variable component into `SNAP_DIR`.**
3. **Do not automate `restic unlock`** inside the nightly script.
4. **Do not recreate `aurora-whisper`** while F6.1 is open (D-F6-1).
5. **Do not redeploy the stored container stack definition** — see the recorded hazard under
   `07_operations/hazards/`.
6. **`03_services/` compose files are Recovery Artifacts**, not deployment sources.
7. **M-I is deferred, not bundled.** Hardening the staging directory is a separate change.

---

## 13. Git gate

Documentation-only. **Not committed, not pushed** — both require explicit operator approval
immediately before the command (`PROJECT_RULES.md` → *Operator Git Approval*). Triad
reconciliation for I-4 has **not** been performed and is a separate step.

**STOP at git gate.**
