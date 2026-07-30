# I-4 — Backup Grouping Defect — Gate 8 Closeout

**Date:** 2026-07-31
**Type:** Closeout record. Operational, not a phase.
**Remediation item:** I-4 (Program E — backup lifecycle), from the 2026-07-28 infrastructure audit.
**Result:** **I-4 COMPLETE.** G-I4-1 … G-I4-12 all PASS.
**Production changed by this document:** none. Gate 8 was executed **read-only**.
**Current safety state:** retention runs as `--dry-run`. **No snapshot can be deleted.**

> This is a dated record. It states what was true on 2026-07-31 and is **not** rewritten as the
> situation advances (`PROJECT_RULES.md` → *Historical Documentation*). Corrections belong in
> later documents.

Predecessor documents, both dated and authoritative for their own moment:

* Diagnosis — [`2026-07-28_backup_retention_incident.md`](2026-07-28_backup_retention_incident.md)
* Change, Gate 7, and the Gate 8 predictions —
  [`2026-07-28_issue-i4_backup-grouping_handoff.md`](2026-07-28_issue-i4_backup-grouping_handoff.md)

---

## 1. Context and objective

The 2026-07-28 audit found that the nightly restic retention policy had **never removed a
snapshot** since repository creation on 2026-06-13. A stale exclusive lock masked the failure
for ~30 days but did not cause it: the policy was structurally inert by construction.

I-4's objective was narrow and deliberately so — **fix the grouping defect, and prove the fix on
real unattended operational evidence.** Deciding what the retention policy *should* delete is a
separate item (**S-10**) and is explicitly out of scope here.

I-4 is the prerequisite for all of Program E. Nothing downstream — I-5, I-6, I-8, S-8, S-10 —
could be evaluated meaningfully while snapshots landed in singleton groups.

**Gate 8 is the acceptance test**: the four gates that could only close on unattended
operational accrual, not on more implementation.

---

## 2. The original grouping defect

`/usr/local/bin/homelab-backup.sh` built its restic path set with a **dated staging directory**:

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

---

## 3. The implemented change

Two functional lines, plus two colocated comment blocks. **Everything else in the script is
byte-identical** — trap, `mkdir -p`, all twelve workload paths, the three `sqlite3 .backup`
blocks, `--tag nightly`, all `--exclude` patterns, `set -euo pipefail`, and the entire
`restic backup` invocation.

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
of another shape. Discarding it was considered and rejected. Its consequence is recorded in §9.

### Installed artifact — re-verified 2026-07-31

| Field | Value |
|---|---|
| Path | `/usr/local/bin/homelab-backup.sh` |
| sha256 | `90e8eb914601cb2a805eb5af915642e8753bdea45b715c071a424170a907a45f` |
| Size / mode / owner | 2799 bytes · `0755` · `root:root` |
| `bash -n` | PASS (at Gate 7) |
| Staging path | `/tmp/homelab-backup-snapshots` — **undated** |
| Retention flag | `--dry-run` present; `--prune` absent |

The hash is unchanged from the value recorded at installation on 2026-07-28. Cron
(`/etc/cron.d/homelab-backup`, `0 3 * * *`) was never modified.

---

## 4. Why retention remains `--dry-run`

**This is a deliberate safety hold, not an unfinished edit.**

Before I-4 the policy could not delete anything, so `--prune` was harmless. After I-4 the policy
is **live again**. Left unguarded it would begin deleting snapshots **unattended** as soon as the
post-fix group spans more than seven days — that is, from roughly 2026-08-04 — and it would do so:

1. **before the retention policy has been decided.** The pre-fix dry-run measured an inert
   policy; its result carries no information about post-fix behaviour. Deciding the policy
   deliberately is **S-10**.
2. **before the D-1.5 anchor `63c072f4` has any protection.** The anchor is an ordinary
   `nightly`-tagged snapshot and is fully in scope for `forget --tag nightly`. Giving it real
   protection is **I-6**, which must land before S-10.

`--dry-run` is the **sole** safety mechanism. `restic forget` deletes snapshots on its own;
`--prune` only reclaims unreferenced data afterwards, so removing `--prune` is **not** protective.

Re-enabling deletion is **S-10** — attended, operator-approved per execution. Both the script
comment and this record say so.

---

## 5. Gate 7 baseline (2026-07-28, attended)

### Verified repository state before any change

| Field | Value |
|---|---|
| snapshots | 42 |
| groups | 41 |
| multi-member groups | `[2]` — the 2026-06-17 pair, sharing an identical path set |
| anchor `63c072f4` | present, tags `['nightly']` |
| oldest | `2026-06-13T14:06:34` |
| newest | `2026-07-28T03:00:01` |
| `restic check` | 37/37 index files, 42/42 snapshots, **no errors** |
| locks after `check` | none |

### Attended run — snapshot `6323b009`, exit code 0

| Field | Predicted | Observed |
|---|---|---|
| exit code | 0 | 0 |
| keep blocks | 42 | 42 |
| `keep 2` blocks | 1 | 1 |
| remove blocks | 0 | 0 |
| snapshots | 43 | 43 |
| groups | 42 | 42 |
| multi-member | `[2]` | `[2]` |
| anchor | present, `['nightly']` | present, `['nightly']` |
| staging path recorded | undated | `/tmp/homelab-backup-snapshots` |
| locks after run | none | none |

Backup phase reported `no parent snapshot found` — **expected**, because `6323b009` is the first
member of a new group. 2740 files new, 1385 dirs, 50.794 MiB added / 12.525 MiB stored.

Two gate definitions were corrected during execution and those corrections stand:

* **G-I4-6** — the primary criterion is the **absence** of `no parent snapshot found`. A non-zero
  `unmodified` count is the production corollary. Neither can be evaluated on the first snapshot
  in a new group.
* **G-I4-7** — originally required a non-empty would-remove set. That was a leftover from a
  rejected design variant and is **unsatisfiable** under the approved change. Revised to: *the
  retention step completes, reports a policy evaluation, and removes nothing.*

---

## 6. Gate 8 — the unattended nights

Two unattended cycles had accrued by the time Gate 8 was executed. The §8 predictions were
written for the first; the second is independent confirming evidence.

### 6.1 Night 1 — 2026-07-29 03:00, snapshot `89966886`

```
using parent snapshot 6323b009
Files:           0 new,   267 changed,  2473 unmodified
Dirs:            0 new,   156 changed,  1229 unmodified
Added to the repository: 93.414 MiB (29.911 MiB stored)
processed 2740 files, 4.112 GiB in 0:01
snapshot 89966886 saved
Applying Policy: keep 7 daily, 4 weekly, 6 monthly snapshots
```

| Field | §8 predicted | Observed | Result |
|---|---|---|---|
| snapshots | 44 | **44** | PASS |
| **groups** | **42** | **42** | **PASS** |
| multi-member | `[2, 2]` | **`[2, 2]`** | PASS |
| keep blocks | 42 | **42** (40 × `keep 1`, 2 × `keep 2`) | PASS |
| `keep 2` blocks | exactly 2 | **2** | PASS |
| remove blocks | 0 | **0** | PASS |
| `Would have removed` | — | **0** | PASS |
| `no parent snapshot found` | absent | **absent** | PASS |
| `Files:` unmodified | non-zero, most of ~2740 | **2473** (90.3 %) | PASS |
| `error` / `Fatal` | — | **0** | PASS |

**Every §8 prediction matched exactly on the night it was written for.**

### 6.2 Night 2 — 2026-07-30 03:00, snapshot `d03f0e19`

```
using parent snapshot 89966886
Files:           1 new,   165 changed,  2575 unmodified
Dirs:            0 new,   112 changed,  1273 unmodified
Added to the repository: 65.623 MiB (17.738 MiB stored)
processed 2741 files, 4.112 GiB in 0:01
snapshot d03f0e19 saved
Applying Policy: keep 7 daily, 4 weekly, 6 monthly snapshots
```

| Field | Observed |
|---|---|
| snapshots | **45** |
| **groups** | **42 — unchanged** |
| multi-member | `[2, 3]` |
| keep blocks | 42 (40 × `keep 1`, 1 × `keep 2`, 1 × `keep 3`) |
| remove blocks | **0** |
| `no parent snapshot found` | **absent** |

The snapshot count and multi-member shape differ from §8 only by the elapsed extra night, which
§9 of the handoff explicitly anticipates: *"the post-fix group gains one distinct day per night."*
**`groups` — the decisive number — held at 42 across both nights.**

### 6.3 Awareness chain (G-I4-8)

The full 02:30 → 04:25 chain ran and propagated on both nights. Night 2, verified directly:

| Stage | Time | Artifact | Content |
|---|---|---|---|
| 02:30 ingest | — | `health.json` | `last_run_rc: 0` |
| 03:00 backup | — | — | snapshot `d03f0e19` |
| 03:30 backup probe | `01:30:01Z` | `backup_status.json` | `status: ok`, `snapshot_id: d03f0e19` |
| 04:00 container probe | `02:00:01Z` | `container_status.json` | 17 containers, `degraded: [zigbee2mqtt]` |
| 04:15 context | `02:15:01Z` | `aurora-context.{json,md,voice}` | `backup: ok / d03f0e19` |
| 04:25 digest | — | `2026-07-30_ops_digest.md` | `Backup: ok — snapshot d03f0e19` |

`backup_status.json` references the **newest** snapshot, with `status: ok`, and that value
propagates unchanged into the context artifacts and the digest. The same held on 2026-07-29 with
`89966886`.

**Note.** The digests report `overall_status: degraded` on both nights because `zigbee2mqtt` is
down (see §11). That is the chain **correctly reporting a real degradation**, not a chain
failure. G-I4-8 asks whether the signal chain is healthy, and it is.

---

## 7. Root-verified repository evidence (2026-07-31)

Executed as root, read-only, per §11 of the handoff. Both commands carry `--no-lock`; neither
`unlock`, `forget` nor `prune` was invoked at any point.

```bash
sudo restic -r /mnt/storage/backups/restic --password-file /etc/restic/passwd-homelab --no-lock snapshots --json
sudo restic -r /mnt/storage/backups/restic --password-file /etc/restic/passwd-homelab --no-lock list locks
```

Repository `843b34b8`, version 2, restic 0.16.4.

| Field | Verified value |
|---|---|
| snapshots | **45** |
| **groups** `(hostname, sorted(paths))` | **42** — 41 legacy + 1 post-fix |
| multi-member group sizes | **`[2, 3]`** |
| post-fix group | `6323b009` → `89966886` → `d03f0e19` |
| post-fix `paths[]` | **byte-identical across all three** — 13 elements, same order |
| parent chain | `89966886.parent = 6323b009`; `d03f0e19.parent = 89966886`; `6323b009` has no parent (first of group) |
| anchor `63c072f4` | present, tags `['nightly']`, in the 2026-06-17 pair with `5a5eadf2` |
| **locks** | **none** — empty output, two separate invocations |
| all snapshots tagged | `nightly`, 45/45 |

The post-fix path set, recorded identically in all three snapshots:

```
/etc/apache2/sites-enabled
/etc/samba/smb.conf
/etc/systemd/system/homelab-tools.service
/home/diego/homelab/03_services/zigbee-stack/mosquitto/config
/home/diego/homelab/03_services/zigbee-stack/mosquitto/data
/home/diego/homelab/03_services/zigbee-stack/zigbee2mqtt/data
/home/diego/homelab/09_ops/runtime
/home/diego/homelab/ai-stack/data/qdrant
/home/diego/webs
/srv/homelab/data/npm
/srv/homelab/data/openwebui
/srv/homelab/homeassistant
/tmp/homelab-backup-snapshots          ← undated
```

### Independent corroboration

Two facts derived from the JSON match the pre-fix incident record exactly, neither of them
predicted by this exercise:

* **41 legacy groups for 42 legacy snapshots** — identical to the 2026-07-28 baseline.
* **Missing nightly dates 2026-06-21, 07-22, 07-23, 07-24, 07-25** — identical to §8 of the
  incident record.

A third, historical, path-set change is visible and expected: snapshots from 2026-06-30 onward
carry 13 paths rather than 12, because `/home/diego/homelab/09_ops/runtime` was added at F4.1.
It does not affect grouping counts, since the dated staging path already differed daily.

---

## 8. Gate ledger — G-I4-1 … G-I4-12

| Gate | Criterion | Result | Closed |
|---|---|---|---|
| **G-I4-1** | Static validation — `bash -n`; diff contains only the approved edits | **PASS** | 2026-07-28 |
| **G-I4-2** | Disposable-repository rehearsal | **PASS** | 2026-07-28 |
| **G-I4-3** | Attended run exits 0 | **PASS** | 2026-07-28 |
| **G-I4-4** *(hard)* | Snapshot count + anchor intact — 42 → 43, anchor present, tags unchanged | **PASS** | 2026-07-28 |
| **G-I4-5** | Path-set stability | **PASS** — 42 groups (not 43); byte-identical `paths[]` across three post-fix snapshots | 2026-07-31 |
| **G-I4-6** *(revised)* | Parent detection restored — **absence** of `no parent snapshot found` | **PASS** — absent both nights; parent named explicitly; unmodified 2473 then 2575 | 2026-07-31 |
| **G-I4-7** *(revised)* | Retention completes, reports a policy evaluation, removes nothing | **PASS** | 2026-07-28 |
| **G-I4-8** | Awareness chain healthy — 03:30 → 04:25 | **PASS** — full chain both nights; `backup_status.json` `ok` + newest snapshot, propagated | 2026-07-31 |
| **G-I4-9** | Unattended cycle reproduces the attended result | **PASS** — reproduced twice | 2026-07-31 |
| **G-I4-10** | `restic check` — no errors | **PASS** | 2026-07-28 |
| **G-I4-11** | Rollback source intact — hash verified after installation | **PASS** | 2026-07-28 |
| **G-I4-12** | No stranded repository lock | **PASS** at the attended run; **re-verified 2026-07-31** — `list locks` empty, two invocations | 2026-07-28 / 2026-07-31 |

**All twelve gates PASS. I-4 is COMPLETE.**

---

## 9. Confirmation that no snapshot was removed

Stated explicitly, as a matter of record.

| Moment | Snapshots |
|---|---|
| Pre-change baseline (2026-07-28) | 42 |
| After the Gate 7 attended run | 43 |
| After the 2026-07-29 unattended run | 44 |
| After the 2026-07-30 unattended run | 45 |

**Monotonically increasing. No decrease at any point.**

* **Zero `remove` blocks** were emitted by any `forget` execution — before the fix or after it.
* **Zero `Would have removed` lines** appear anywhere in `/var/log/homelab-backup.log`.
* **`restic prune` has never been executed** against this repository.
* Every `forget` invocation carried both `--tag nightly` and `--dry-run`.
* The D-1.5 anchor `63c072f4` is **present and intact**, verified before the change, after the
  attended run, and again by direct repository read on 2026-07-31.
* The only mutating command ever executed against the repository during the whole of I-4 and its
  predecessor incident work was a single `restic unlock` on 2026-07-28 (plain, **not**
  `--remove-all`), which removed one abandoned lock and no snapshot.

Gate 8 itself was **entirely read-only**.

---

## 10. Open observation — the missing parent of `63c072f4`

Snapshot `63c072f4` (2026-06-17 16:19:21, the D-1.5 anchor) records:

```
"parent": "4f4177e8055636afb43b3268ba0ea25cb29b8463308012348b5fdcd610f207c9"
```

**No snapshot with that id exists in the repository.** All 45 present snapshots were enumerated
and none matches.

**This is recorded as an observation, not a diagnosis. No cause is attributed.** What is
established is only the discrepancy itself: a snapshot id referenced as a parent is not present
today.

What can be stated with confidence, and no more:

* **It is not attributable to the nightly retention policy**, which was structurally inert from
  repository creation until I-4 and emitted zero `remove` blocks across every execution examined.
* **No I-4 gate depends on it.** It does not affect grouping, parent detection, the awareness
  chain, or the unattended-cycle reproduction.
* It sits outside the window covered by the retained log rotations, so the existing evidence base
  cannot speak to it either way.

Consequence for downstream work: the flat claim *"no snapshot has ever been removed from this
repository"* is **not** supported by this evidence and should not be relied upon. The supported
claim is narrower — *the nightly retention policy has never removed a snapshot.* `CURRENT_STATE.md`
has been reconciled to the narrower wording.

Investigating this is **not** authorized by this document.

---

## 11. Final state and residual risks

### Final state

* **Grouping is fixed and proven** on real unattended operational evidence across two nights and
  a direct repository read.
* **Change detection is restored.** Nightly runs report real deltas instead of a full ~4.1 GiB
  re-scan with every file marked `new`.
* **Retention is live but held at `--dry-run`. No snapshot can be deleted by the nightly job.**
* **Backups are healthy and current**; recoverability remains proven (E5-b 2026-06-27; G-F4-08
  empirical restore drill 2026-07-27).
* **No repository locks.**

### Residual risks — all open, none introduced by I-4

1. **The 42 legacy snapshots are permanently unreachable by the nightly policy.** They occupy 41
   dated groups that no future snapshot can ever join. Removing them requires an explicit
   mechanism — selection by snapshot id, or a deliberate one-off grouping override — executed
   attended at **S-10**. This is a handover, not a defect.
2. **The anchor `63c072f4` still has no protective mechanism.** It is an ordinary
   `nightly`-tagged snapshot, in scope for `forget --tag nightly`, surviving only because nothing
   is deleted today. **I-6**, and it must land before S-10.
3. **The backup probe still cannot see retention outcomes**, script exit status, snapshot count,
   lock state or missed nights (**H-1c** / **S-8**). Unchanged by I-4.
4. **Backup coverage remains incomplete** (**H-2** / **I-5**). The Portainer volume,
   `ai-stack/.env`, `/home/diego/.secrets/`, `/etc/cron.d/aurora-signals` and the openedai voice
   map are outside the path set. Unchanged by I-4.
5. **The same-bucket retention behaviour is established but not derived.** In a group whose
   snapshots share day, week and month, policy `7/4/6` keeps exactly two regardless of group
   size. This was characterized on a disposable repository and confirmed on production, but the
   mechanism could not be reconstructed from restic's documented bucket semantics. **S-10 will
   operate in a different regime** — real multi-day buckets — and must re-establish the behaviour
   by dry-run before any irreversible prune.
6. **`zigbee2mqtt` is down** since 2026-07-28 15:52 and has deliberately not been restarted.
   Unrelated to I-4; recorded as evidence for **M-1 / M-A** and **S-9** in `ROADMAP.md`. It is
   noted here only because it explains the `degraded` verdict visible in the Gate 8 awareness
   artifacts.

### First would-remove observation — expected on or shortly after 2026-08-04

The post-fix group gains one distinct day per night. Once it spans eight days, its oldest member
(`6323b009`, 2026-07-28) falls outside `--keep-daily 7`; neither the weekly nor the monthly bucket
rescues it. With `--dry-run` in place it will be **reported, never removed**. That report is the
first real evidence of what a live retention policy would do on this repository, and it is the
input **S-10** requires. **Check the nightly log on or shortly after 2026-08-04.**

---

## 12. Next steps

Ordered. None is authorized by this document; each needs its own approval.

| # | Item | Note |
|---|---|---|
| 1 | **I-5** — extend backup coverage (H-2) | **Next.** I-5 edits the script's `PATHS` array, which changes the recorded path set and therefore **starts a new group** — expected and harmless. **It must not reintroduce a date, timestamp or any other variable path component.** |
| 2 | **I-6** — give anchor `63c072f4` real protection | A distinct keep-tag or explicit exclusion. **Must land before S-10.** Never rely on group shape for protection. |
| 3 | **I-8** — track `/usr/local/bin/homelab-backup.sh` in the repository | **Unblocked by this closeout.** The installed script is now the Gate-8-validated version (sha256 above); tracking it before Gate 8 would have committed a script the rollback could invalidate. |
| 4 | **S-8** — close the backup monitoring blind spot | Apply the E2-a fail-loud pattern to the backup path: consume the script's exit status, surface snapshot count, retention outcome, lock state and missed nights. Depends on I-4 (done) and S-7. |
| 5 | **S-10** — retention decision + attended prune | **The only irreversible item in the roadmap.** Strict order: fresh post-fix dry-run → policy decision → I-6 anchor protection → `restic check` → attended prune. Going straight to `7/4/6` on a repository that has never pruned would remove a large fraction of its snapshots in one step; a conservative first pass then tightening is the lower-risk path. Operator-approved **per execution**. |

---

## 13. Rollback and safety notes

### Rollback

| Field | Value |
|---|---|
| Rollback source | `/root/i4-evidence/homelab-backup.sh.pre-I4` |
| sha256 | `a67060552dc13b296b15a1257ca6427663ec083b04577ed97f72637048245cdf` |
| Verified | byte-identical to the pre-change live script; confirmed intact **after** installation (G-I4-11) |

```bash
sudo install -m 0755 -o root -g root /root/i4-evidence/homelab-backup.sh.pre-I4 /usr/local/bin/homelab-backup.sh
```

Rollback is **file restoration only**. No repository state was mutated by the script change, so
there is nothing to undo inside restic. Cron was never modified. Recovery time is under one
minute.

Evidence directory `/root/i4-evidence/` (mode `0700`) holds the pre-change script, the installed
candidate, the pre-change snapshot inventory, and the Gate 7 attended-run log.

**With all twelve gates passed, rollback is no longer an expected action** — it is retained as a
recovery path, not a pending decision.

### Safety notes — constraints that outlive this closeout

1. **Do not restore `--prune` or remove `--dry-run`.** That is **S-10**, attended and separately
   approved, per execution.
2. **Do not reintroduce a date, timestamp or any other variable component into `SNAP_DIR`.** That
   is the defect I-4 exists to fix, and it would silently re-open it.
3. **Do not change `--group-by`.** The default `host,paths` grouping is retained deliberately as
   a safety property.
4. **Do not automate `restic unlock`** inside the nightly script. It would mask genuine
   concurrency. Detect automatically (**S-8**), remove deliberately. Two abandoned locks occurred
   within one month from unrelated causes; nothing detects this class of failure today.
5. **Never rely on the `--tag nightly` filter as protection.** Every snapshot in this repository
   carries that tag, including the anchor. There is **no tag-based protection for any snapshot**.
6. **M-I is deferred, not bundled.** Hardening the backup staging directory is a separate change.

---

## 14. Git gate

Documentation-only. **Not committed, not pushed** — both require explicit operator approval
immediately before the command (`PROJECT_RULES.md` → *Operator Git Approval*). Author as
`Diego <diego@diegoamaro.dev>`.

**STOP at git gate.**
