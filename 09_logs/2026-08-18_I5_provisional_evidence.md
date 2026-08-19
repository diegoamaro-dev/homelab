# I-5 — Backup Coverage — PROVISIONAL EVIDENCE NOTE

**Date:** 2026-08-18
**Type:** Provisional session-preservation record (`PROJECT_RULES.md` → *AI Assistant Session
Preservation*). **Not a closeout.**
**Status:** **I-5 is OPEN.** One gate remains: **G-I5-9**, which closes only on the next
unattended 03:00 cycle.
**Production changed:** yes — `/usr/local/bin/homelab-backup.sh` replaced, and one attended
backup executed. Both operator-approved, one command at a time.
**Not done, deliberately:** triad reconciliation, I-5 completion claim, any Git operation.

> This note exists so the overnight wait can be crossed without losing context. It states what
> was true on 2026-08-18 and is **not** rewritten as the situation advances
> (`PROJECT_RULES.md` → *Historical Documentation*). The closeout is a later document.

---

## 1. What I-5 changed

Three static paths appended to the `PATHS` array of `/usr/local/bin/homelab-backup.sh`,
closing the non-secret half of audit finding **H-2**:

| Added path | Why |
|---|---|
| `/var/lib/docker/volumes/portainer_data/_data` | Holds the **only** copies of the stack definitions (H-3 / H-4) |
| `/etc/cron.d/aurora-signals` | The Aurora signal schedule |
| `/srv/homelab/data/openedai-speech/voice_to_speaker.yaml` | Aurora's TTS voice mapping — hand-authored, not reproducible |

**13 → 16 recorded paths.** Nothing else changed: `--dry-run` intact, `--prune` still absent,
`--group-by` untouched, `SNAP_DIR` still undated, excludes and tag unchanged.

| Artifact | sha256 |
|---|---|
| Pre-I5 (rollback, `/root/i5-evidence/homelab-backup.sh.pre-I5`) | `90e8eb91…a907a45f` |
| Installed at I-5 | `330df064…5895a554` |

### Containment proof (pre-implementation)

Each addition was proven **outside** the existing set before any change: no covered ancestor
among the 13 prior paths, no reverse containment, `realpath` identical (no symlink), no bind
mount grafting it into a covered tree, and the repository's own record for the then-newest
snapshot listing exactly 13 paths with `/var` absent entirely.

---

## 2. Gate results — first attended run

Attended run 2026-08-18 12:40:03 → snapshot **`afd3b4b4`**.

| Gate | Result | Evidence |
|---|---|---|
| **G-I5-1** | PASS | `bash -n` clean; diff = 6 lines added, 0 removed, one hunk |
| **G-I5-2** | PASS | 16 elements; all static literals; absolute; no duplicates or nesting |
| **G-I5-3** | **PASS WITH EVIDENCE QUALIFICATION** | see §3 |
| **G-I5-4** | PASS | new snapshot records **exactly 16** paths, no variable component |
| **G-I5-5** | PASS | groups **42 → 43**; new group holds exactly 1 snapshot; prior 22-member group **frozen at 22**; anchor group still 2 |
| **G-I5-6** | **PASS** | all three assets confirmed **inside** the snapshot — see below |
| **G-I5-7** | PASS | exactly one `no parent snapshot found`; `2775 new / 0 changed / 0 unmodified`; 35.513 MiB added from 4.134 GiB read (deduplication, as predicted) |
| **G-I5-8** | PASS | **zero** real removals; one dry-run report |
| **G-I5-10** | PASS | no independent secret store in the path set |
| **G-I5-11** | PASS | snapshots **64 → 65**; anchor `63c072f4` present, still paired with `5a5eadf2` |
| **locks** | PASS | lock listing empty |
| **G-I5-9** | **OPEN** | requires the next unattended cycle — §5 |

**G-I5-6 is the gate that proves coverage**, and it passed on real content, not on the fact
that a path was passed to restic: `compose/{1,2,3,4}/docker-compose.yml` (**four** stack
definitions — the audit named three), `/etc/cron.d/aurora-signals`, and
`voice_to_speaker.yaml` all appear in the snapshot's file listing.

### Retention behaved exactly as predicted

The would-remove set after I-5 is the **identical 11 snapshot ids** as before it: all from the
now-frozen prior group, with the new group contributing **zero**. This empirically confirms a
correction recorded earlier — a `PATHS` change does **not** reset the would-remove report to
zero, because `restic forget` evaluates each `host,paths` group independently. The *new group's*
trail starts at zero; the report as a whole does not. **S-10 must plan against the frozen
group, which no future snapshot can join.**

---

## 3. G-I5-3 — evidence qualification, stated honestly

**PASS WITH EVIDENCE QUALIFICATION.** The direct shell exit code was **not preserved** and is
**unavailable**. It was not observed, and no backup was re-run to manufacture it.

What is established instead: the attended run created snapshot `afd3b4b4`, completed the backup
phase, completed the final `restic forget --dry-run` phase under `set -euo pipefail`, left no
repository lock, and every post-run repository invariant reconciled.

This is recorded as a qualification rather than a clean PASS **deliberately** — the distinction
between an observed value and an inferred one is the same discipline ER-1 exists to enforce.

---

## 4. Scope clarification — the secret boundary

**Discovered by G-I5-6 during validation. It was not part of the original I-5 plan, and this
record does not present it as though it had been.**

The pre-flight justified `portainer_data` as "the only copies of the stack definitions" and
sized it without enumerating its contents. The file listing showed the volume also carries
Portainer's own certificates, internal keys and application database. The I-5 constraint as
written excluded keys, so validation surfaced a genuine conflict between the stated constraint
and the chosen path.

**Operator decision (2026-08-18): accept and document. No excludes were added and I-5 was not
rolled back.** Rationale of record: `portainer_data` is an **application-state volume**; its
database, certificates and internal keys form a coherent Portainer restore, and selectively
excluding them would weaken recoverability and risk a partial restore.

**The boundary, clarified:**

* **Application-internal state contained inside an explicitly backed-up volume MAY be captured**
  by the encrypted restic repository when it is required for recovery.
* **Independent operational secret stores remain EXCLUDED and deferred to M-D:**
  `ai-stack/.env` · `/home/diego/.secrets/` · `/etc/restic/passwd-homelab`.

`/etc/restic/passwd-homelab` is the sharpest of the three: without it the repository cannot be
decrypted at all. **M-D remains open.**

No key, credential or secret **content** is reproduced anywhere in this record.

---

## 5. G-I5-9 — open, with predictions registered in advance

Predictions are recorded **before** the run, so the gate cannot be judged from its own outcome.
The next unattended 03:00 cycle must show:

1. snapshot count **65 → 66**
2. group count **remains 43**
3. the 16-path group grows **1 → 2** members
4. the new snapshot names **`afd3b4b4`** as its parent
5. `no parent snapshot found` **absent**
6. all **16** recorded paths byte-for-byte identical to `afd3b4b4`'s set
7. `--dry-run` still active
8. **zero** real deletions
9. anchor **`63c072f4`** still present
10. `backup-probe` / awareness chain healthy
11. no repository lock

Failure of 3, 4 or 6 would indicate the path set is not deterministic — the I-4 defect class —
and would mean stopping rather than proceeding.

---

## 6. Observations recorded, deliberately unimplemented

* **restic cache notice** — `found 1 old cache directories in /root/.cache/restic`. Local
  scratch, unrelated to repository data. Explicitly **not** cleaned during this change. No
  remediation identifier assigned (R-I3-1…7 / F-S1-1 precedent).
* **Scheduling assets still uncovered** — `/etc/cron.d/homelab-backup` and the `diego` crontab
  are in neither git nor the backup set. Recorded during the I-5 gap analysis and left
  **out of scope**; the backup script itself is **I-8**.
* **Hot-volume capture** — `portainer_data` is read while Portainer runs, so its SQLite state
  could be caught mid-write. Same accepted risk class as the E4-b hot-backup decision; the
  compose definitions are static files.
* **Evidence files live in `/tmp`** (`i5_attended_run.log`, `restic_snapshots_post_i5.txt`,
  `i5_ls_latest.txt`, `i5_locks.txt`) and are **volatile**. Preserving them under
  `/root/i5-evidence/` before closeout is recommended; it requires root and has not been done.

---

## 7. Rollback — available and unused

```bash
sudo install -m 0755 -o root -g root /root/i5-evidence/homelab-backup.sh.pre-I5 /usr/local/bin/homelab-backup.sh
```

File restoration only; no repository state would need undoing. A rollback restores the 13-path
set, so future snapshots would **rejoin the prior group** and create no additional orphan.

**Not recommended.** Every evaluated gate passed and the installed path set is correct.

---

## 8. Status and git gate

**I-5 is OPEN.** It is **not** complete and must not be recorded as complete until **G-I5-9**
passes on real unattended evidence.

The triad has **not** been reconciled. **Nothing has been staged, committed or pushed** —
each requires explicit operator approval immediately before the command
(`PROJECT_RULES.md` → *Operator Git Approval*). Author as `Diego <diego@diegoamaro.dev>`.

**STOP at git gate.**
