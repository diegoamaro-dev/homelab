# I-6 — Anchor Protection — PROVISIONAL EVIDENCE NOTE

**Date:** 2026-08-20
**Type:** Provisional session-preservation record (`PROJECT_RULES.md` → *AI Assistant Session
Preservation*). **Not a closeout.**
**Status:** **I-6 is OPEN.** One gate remains: **G-I6-8**, which closes only on the
2026-08-20 03:00 unattended cycle.
**Production changed:** yes — one snapshot retagged in the restic repository, operator-approved,
one command at a time. **No further production change is authorized.**
**Not done, deliberately:** triad reconciliation (beyond one safety pointer in
`AMAROLAB_HANDOFF.md`, §7), I-6 completion claim, any Git operation.

> This note exists so the overnight wait can be crossed without losing context. It states what
> was true on 2026-08-20 at ~00:15 CEST and is **not** rewritten as the situation advances
> (`PROJECT_RULES.md` → *Historical Documentation*). The closeout is a later document.

---

## 1. Exact current state

I-6 gives the D-1.5 anchor real protection, replacing survival-by-group-shape with a mechanism.
**Decision B** (operator-approved): snapshot-level protection — the anchor leaves the `nightly`
retention scope and carries dedicated anchor tags. **The backup script was deliberately NOT
modified**, so **I-8's tracking target is unchanged at sha256 `330df064…5895a554`.**

### The identity change — executed 2026-08-19

```
63c072f47e532e0bb4e411522163720e8217c1311beb486bf9abce88de75aacc   (63c072f4, tags: nightly)
                              ↓  restic tag --set anchor,d15-rollback
42506e442780fb99702b6f3e2a7af0c01a858cf0600db455d2dcd1160e5da5ca   (42506e44, tags: anchor,d15-rollback)
                              original: 63c072f47e532e0b…de75aacc
```

**`42506e44` is the live protected anchor. `63c072f4` no longer names any snapshot** — it
survives only as the `original` provenance field, where it remains permanently resolvable.

| Property | Value |
|---|---|
| Repository | 66 snapshots, 43 groups, distribution `{1:40, 2:2, 22:1}` |
| `nightly`-tagged | **65** — the anchor is outside retention scope |
| 2026-06-17 group | 2 members — `5a5eadf2` (`nightly`) and `42506e44` (protected) |
| Would-remove set | the same 11 IDs as at I-5, unchanged |
| Repository lock | none |
| `restic check` | no errors, 66/66 snapshots |

### Gate ledger so far

| Gate | Result |
|---|---|
| **P1–P5** pre-flight | **ALL PASS** — anchor tags exactly `["nightly"]`; **zero** snapshots named it as parent; **zero** `original` fields existed repository-wide; `restic check` clean; no lock (closed by operator observation) |
| **G-I6-1…G-I6-5** | **PASS** — count Δ0 (66), groups Δ0 (43), group membership intact, tags exact, `original` exact, `time`/`tree`/`paths`/`hostname`/`username`/`excludes`/`parent` all unchanged, and the other **65 snapshots byte-identical** |
| **G-I6-6** | **PASS** — see §2 |
| **G-I6-8** | **OPEN** — requires the 2026-08-20 03:00 unattended cycle |

### G-I6-6 — passed on the real production policy

Attended, read-only (`--no-lock`), 2026-08-19 23:59. All eight operator-registered assertions hold:

1. would-remove set **exactly** the known 11 — zero missing, zero extra;
2. `5a5eadf2` **absent**, retained as its day's `daily snapshot`;
3. `42506e44` **absent from the forget output entirely** — zero occurrences;
4. zero real removals — dry-run wording only;
5. count **66**; 6. groups **43** `{1:40, 2:2, 22:1}`;
7. tags `["anchor","d15-rollback"]`, `original` == the historical full ID;
8. no lock.

**The arithmetic that proves protection:** 43 keep blocks → 54 kept, plus 11 proposed =
**65 evaluated**, against **66** in the repository. The one snapshot the policy cannot see is
`42506e44`. It is not *spared by* the policy; it is *invisible to* it.

**The one genuinely unknown outcome resolved safely.** The 2026-06-17 group went from 2
`nightly` members to 1 — a retention regime this estate had never observed, flagged as a risk
before execution. `5a5eadf2` was kept, the group still counts as one of the 43, and nothing
was exposed.

### Two findings established during the pre-flight

* **The `4f4177e8` retag hypothesis is REFUTED.** No snapshot in the repository carried an
  `original` field before I-6, so nothing had ever been retagged. `5a5eadf2` has no `original`
  and no parent at all.
* **The observation is strengthened and its wording corrected.** `4f4177e8` must have existed
  at 2026-06-17 16:19 — restic selected it as parent, which requires a matching host and path
  set, so it was a **third member of the 2026-06-17 12-path group**. It is gone, and not by
  retagging and not by the nightly policy. **The deletion happened *after* 2026-06-17 16:19**,
  not "on or before", as `CURRENT_STATE.md` currently phrases it. Exactly **one** dangling
  parent exists repository-wide, inherited verbatim by `42506e44`.
  **I-6 makes no claim against that unknown mechanism** (operator-accepted); it protects the
  anchor from the normal nightly retention path only.

### Wording to carry into the closeout — the accidental second invocation

The retag command was run twice. The second run reported
`Ignoring "63c072f4": no matching ID found for prefix` / `no snapshots were modified`.

**It is recorded as a no-op, not a second retag**, and this is provable from the data: no live
snapshot ID carries the prefix `63c072f4`, so run 2 was structurally incapable of modifying
anything. Exactly one snapshot carries an `original` field.

**Do not generalize this into a safety property of `restic tag`.** The precise statement,
per operator direction:

* repeating the command with the **historical** ID `63c072f4` was a no-op **because that ID
  stopped resolving immediately after the first successful retag**;
* repeating a tag operation against the **new live** ID `42506e44` **would modify the snapshot
  again and produce another ID.**

---

## 2. G-I6-8 — the pending predictions, registered in advance

Recorded **before** the run so the gate cannot be judged from its own outcome. The
2026-08-20 03:00 unattended cycle must show:

1. snapshot count **66 → 67**
2. group count **remains 43**
3. the 16-path group grows **2 → 3** members
4. the new snapshot names **`ae45cd50`** as its parent
5. `no parent snapshot found` **absent**
6. all **16** recorded paths byte-for-byte identical to `ae45cd50`'s set
7. `--dry-run` still active; installed script sha256 still `330df064…5895a554`
8. **zero** real deletions
9. **`42506e44` present**, tags exactly `["anchor","d15-rollback"]`, `original` == the
   historical full `63c072f4…` ID
10. **`42506e44` absent from the forget output entirely** — outside `--tag nightly` scope; the
    policy evaluates **66** (65 + the new snapshot)
11. **`5a5eadf2` absent** from the would-remove set
12. **the would-remove set unchanged at exactly the same 11 IDs.** Reasoning: the 22-member
    group is frozen and its retention outcome is static; the new snapshot joins the 16-path
    group, which at 3 distinct days sits inside `--keep-daily 7` and contributes zero.
    **If the set grows, that is a deviation.**
13. `backup-probe` → `status ok`, `snapshot_id` = the new ID, age ≈ 0.5 h; awareness chain
    healthy through the 04:25 digest
14. **no repository lock**

Failure of **9, 10 or 12** would mean the protection is not holding under the real unattended
job, and would mean stopping rather than proceeding.

**The known 11, for comparison:**

```
106316a6  39c4f6fe  5818569e  599d98f8  89966886  98bcc984
9b50911b  9f37d45d  d03f0e19  f41248e1  f889868d
```

---

## 3. Evidence that already exists

**Preserved out of volatile `/tmp` into `/home/diego/i6-evidence/`** (repo-external, survives
reboot; this closes for I-6 the gap the I-5 closeout left open for I-5):

| File | sha256 | What it is |
|---|---|---|
| `01_snapshots_PRE.json` | `92290ca400258e28…` | P1–P3 pre-flight — full metadata, all 66 snapshots, **before** the retag |
| `02_check_PRE.txt` | `f84ee11001d2a18c…` | P5 — `restic check`, 66/66, no errors |
| `03_snapshots_POST_retag.json` | `d807fd718a96daf1…` | Full metadata **after** the retag |
| `04_GI6-6_dryrun.txt` | `195f4cca4a6a6259…` | The complete G-I6-6 attended dry-run output |
| `05_snapshots_GI6-6_gate.json` | `d807fd718a96daf1…` | Full metadata at the G-I6-6 gate |

**`03_` and `05_` are byte-identical** — independent proof that the repository did not change
between the retag and the gate.

Originals remain at `/tmp/i6_snapshots.json`, `/tmp/i6_check.txt`,
`/tmp/i6_snapshots_post.json`, `/tmp/i6_gi6_6_dryrun.txt`, `/tmp/i6_snapshots_gate.json` and
are **volatile**.

**Still open from I-5, unchanged and out of I-6 scope:** the four I-5 evidence files remain in
`/tmp` only (`i5_attended_run.log`, `i5_ls_latest.txt`, `restic_snapshots_post_i5.txt`,
`i5_locks.txt`); preserving them under `/root/i5-evidence/` requires root and is still undone.

---

## 4. Evidence to collect tomorrow, after the 03:00 cycle

**Read-only only. No mutating command is authorized.**

Most of G-I6-8 needs no privilege: `/var/log/homelab-backup.log` is readable via the `adm`
group and carries the complete `forget` output, so predictions **1–8 and 10–12** are verifiable
directly, and **13** comes from the world-readable
`ai-stack/ingest/logs/backup_status.json` plus the awareness artifacts.

Two predictions need one operator-run command each — `9` (anchor tags + `original`) and
`14` (lock state). Both are `--no-lock` and write nothing:

```bash
sudo sh -c 'RESTIC_REPOSITORY=/mnt/storage/backups/restic RESTIC_PASSWORD_FILE=/etc/restic/passwd-homelab restic --no-lock snapshots --json > /tmp/i6_snapshots_g8.json; chmod 0644 /tmp/i6_snapshots_g8.json'
```

```bash
sudo sh -c 'RESTIC_REPOSITORY=/mnt/storage/backups/restic RESTIC_PASSWORD_FILE=/etc/restic/passwd-homelab restic --no-lock list locks'
```

`diego` has no passwordless sudo, so every privileged step is operator-run by design.

**Timing note.** The backup layer is verifiable from ~03:30 (once `backup-probe` lands), but
the full awareness chain does not finish until **04:25**
(`container-probe` 04:00 → `aurora-context` 04:15 → `push-voice-context` 04:20 →
`generate-digest` 04:25). Chain health must be verified after 04:25, not claimed early.

---

## 5. Authorization state

**No further production change is authorized.** Specifically forbidden until the operator says
otherwise:

* no further `restic tag` — **and never against the new live ID `42506e44`**, which would
  change the ID again;
* no `restic forget` of any kind, dry-run or otherwise;
* no edit to `/usr/local/bin/homelab-backup.sh`;
* no `git add`, `commit`, `push` or `tag` (`PROJECT_RULES.md` → *Operator Git Approval*);
* **I-8, S-8 and S-10 are not started.** S-10 remains the only irreversible item in the roadmap
  and is still Open and unapproved.

---

## 6. Next action

**Read-only verification only.** Rebuild context from the repository, collect the post-03:00
evidence per §4, evaluate the fourteen §2 predictions, and report PASS/FAIL.

**If every prediction passes:** close G-I6-8 → mark I-6 complete → reconcile the triad → write
the I-6 closeout → documentation audit and Git review → **stop before `git add` / commit
approval.**

**If anything differs:** stop. Do not retag. Do not run another forget. Report the exact
discrepancy.

---

## 7. Documentation state — one deliberate exception, and a known gap

**`AMAROLAB_HANDOFF.md` has been given a minimal safety pointer** to this record. Without it,
that document still read *"Next: I-6 — give the D-1.5 anchor `63c072f4` real protection"*,
which is now false in a way that matters: it implies I-6 has not started and names an ID that
no longer resolves. `PROJECT_RULES.md` → *Transient Operational Status* rule 1 forbids
knowingly false status in the triad.

**`CURRENT_STATE.md` and `ROADMAP.md` are deliberately NOT reconciled yet** — that belongs to
the closeout, after G-I6-8. They therefore still describe I-6 as the next milestone and still
name `63c072f4`. **This is known, deliberate and time-boxed debt**, recorded here rather than
left to be discovered. Because `CURRENT_STATE.md` is the declared source of truth and would
otherwise win the conflict by its own rule, the handoff pointer states explicitly that it
supersedes both documents on I-6 until the closeout lands.

**Correction owed at the closeout, additional to the I-6 status itself:**
`CURRENT_STATE.md` phrases the `4f4177e8` observation as *"something removed a snapshot on or
before 2026-06-17"*. The evidence shows the removal must have occurred **after 2026-06-17
16:19**.

---

## 8. Status and git gate

**I-6 is OPEN.** It is **not** complete and must not be recorded as complete until **G-I6-8**
passes on real unattended evidence.

**Nothing has been staged, committed or pushed** — each requires explicit operator approval
immediately before the command (`PROJECT_RULES.md` → *Operator Git Approval*). Author as
`Diego <diego@diegoamaro.dev>`.

**STOP at git gate.**
