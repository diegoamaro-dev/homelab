# I-8 — Track the Backup Mechanism in the Repository — APPLY + CLOSEOUT

**Date:** 2026-08-20
**Type:** Remediation-item apply and closeout record (combined — I-8 makes no production
change, so there is no overnight gate to separate them).
**Status:** **I-8 COMPLETE.** G-I8-1…G-I8-8 all PASS.
**Production changed:** **no.** Not a single host file was written. No `restic` command of any
kind was run. `cron` was not touched.
**Not done, deliberately:** any Git operation — held at the operator git gate.

---

## 1. What closed

Audit finding **N-5**: `/usr/local/bin/homelab-backup.sh` existed in exactly one place, on the
root disk, owned by root. Verified at capture — it had **never** been tracked in Git: zero
matches in the working tree and **zero add-commits across all history**.

That was a circular exposure. **The script that creates the backups was neither backed up nor
version-controlled**, and the I-5 closeout had already recorded it as outside the restic path
set. A root-disk loss would have destroyed the mechanism along with everything it protects,
and restoring from restic would have required reconstructing the script from prose scattered
across the triad and `09_logs/` before backups could resume.

It also held decisions that existed nowhere else in executable form: the undated `SNAP_DIR`
(I-4), the sixteen static paths (I-5), the deliberate `--dry-run`, and the deliberate absence
of `--prune`.

**Scope, widened deliberately.** The 2026-07-28 roadmap scoped I-8 to the script alone.
`/etc/cron.d/homelab-backup` was **equally untracked and equally unbacked-up**, and without it
the script never runs — capturing the mechanism without its schedule would have produced a
recovery that restores a script nothing invokes. **Operator decision, 2026-08-20: capture
both.** Recorded as a deliberate extension of the ledger's stated scope, not as scope drift.

### What was captured

| Tracked path | Installs to | sha256 | Live mode | Git mode |
|---|---|---|---|---|
| `07_operations/backups/usr/local/bin/homelab-backup.sh` | `/usr/local/bin/homelab-backup.sh` | `330df064…5895a554` | `0755` | **`0644`** |
| `07_operations/backups/etc/cron.d/homelab-backup` | `/etc/cron.d/homelab-backup` | `976aa694…7ebc8756` | `0644` | `0644` |

Both **byte-identical** to the installed files. The layout **mirrors the host paths** so an
install target is legible from the path itself, following the
`ai-stack/ingest/etc/cron.d/aurora-signals` precedent.

**No redaction was necessary.** Neither file contains a secret value — the script references
`/etc/restic/passwd-homelab` as a **path**, already published throughout the triad and
`09_logs/`, and the cron file scanned clean. This is the material difference from the I-3
capture, whose compose files carry redacted secrets and device paths and are therefore *not
deployable as written*. These two are.

---

## 2. The mode asymmetry — an inertness control, recorded so it is never read as drift

**The live script is `0755`. The tracked copy is committed `0644`. This is deliberate and
operator-approved.**

`PROJECT_RULES.md` → *Recovery Artifacts* rule 2 requires an artifact to be **inert by
construction, not by convention**: "a warning comment is not a control … assume the warning
will not be read, because eventually it will not be." Committing the script non-executable is
that control. An accidental `./homelab-backup.sh` fails on permissions.

**The specific hazard.** This script performs a real `restic backup`. Running a **drifted**
copy would create a genuine snapshot with a wrong path set, and because `restic forget` groups
by `host,paths`, that would open a **spurious group** — polluting exactly the input **S-10**
plans against. The guard costs **zero bytes of content**, so byte-identity with the live file
survives and stays provable by a single `sha256sum`.

**Why not an in-file status header.** Rule 3 asks an artifact to state its own status in
itself. For a byte-exact capture that requirement is in direct conflict with rule 2's
verifiability: a header changes the bytes, so the tracked file would no longer match the live
one and drift detection would degrade to "compare while ignoring the header" — weaker and
error-prone. Three options were put to the operator with that trade-off stated; **byte-identity
plus the mode guard plus a sibling README** was chosen. The alternative that satisfies both
rules — adding the header to the *live* script and reinstalling — was rejected because it is a
production change and would have moved I-8's own sha256 tracking target, recorded in four
places.

The tension is recorded here rather than papered over. **`07_operations/backups/README.md` is
the authority for install targets and drift checks**, and a reader arriving by `grep` meets
the non-executable bit immediately.

---

## 3. Gate ledger — G-I8-1 … G-I8-8

| Gate | Subject | Result |
|---|---|---|
| **G-I8-1** | content parity — both tracked files byte-identical to live | **PASS** — `330df064…5895a554` and `976aa694…7ebc8756`, matching live exactly |
| **G-I8-2** | index mode `100644` for both; script checkout non-executable | **PASS** |
| **G-I8-3** | no secret value in any new file | **PASS** |
| **G-I8-4** | **both live files byte-unchanged** by I-8 | **PASS** — sha256 **and** mtime identical to the pre-capture baseline |
| **G-I8-5** | **no production change** | **PASS** — no host write, no `restic` invocation, no service or container touched, cron untouched |
| **G-I8-6** | README states status, install targets, modes, both hashes and the drift check — and the drift check runs clean | **PASS** |
| **G-I8-7** | retention invariants intact in the tracked script | **PASS** — `--dry-run` present, `--prune` absent from the command, `SNAP_DIR` undated, exactly **16** static path literals |
| **G-I8-8** | triad reconciled; I-8 DONE; Program E next = **S-8** | **PASS** |

**No real-unattended-cycle gate exists for I-8, by design.** I-4, I-5 and I-6 each changed
production and therefore had to prove themselves against a real nightly run. I-8 changes
nothing in production, so a cycle has nothing to prove, and the operator explicitly declined a
passive 03:00 confirmation. **G-I8-4 and G-I8-5 are the gates that carry that claim**, and
both are evidenced rather than asserted: the live baseline was recorded **before** any file was
written and compared **after**.

---

## 4. What I-8 closes, and what it does not

**Closes: version-control durability.** The backup mechanism now exists in Git and, once
published, on the GitHub remote — an **off-host** copy. That is something the restic
repository cannot provide, because it sits on the same physical machine
(`07_operations/backups.md` → *What is still missing*).

**Does NOT close: restic coverage.** `07_operations/` is **not** in the restic path set, so
neither captured file entered the backup. **Audit finding H-2 is unchanged by I-8** — its
non-secret half closed at I-5, its secret half remains **M-D**, open. The scheduling assets
remain outside the restic set exactly as the I-5 closeout recorded. *Stated explicitly so no
future reader mistakes I-8 for a coverage change.*

**Restoring these two files does not by itself restore the ability to read a backup.** It also
needs `restic` installed, the repository at `/mnt/storage/backups/restic`, and
`/etc/restic/passwd-homelab` — the last of which is **M-D, open**, outside the backup set, and
without which the repository cannot be decrypted at all.

---

## 5. Standing obligation created by I-8

**Whenever either live file changes, the tracked copy must be updated in Git in the same
change**, and the new sha256 recorded in the README and the triad.

This is the same discipline that made the script's sha256 a triad-tracked value at I-5 and
kept it correct through I-6 — where the value's *not* changing was itself a recorded result. A
live change that is not mirrored here silently converts these files from a recovery asset into
a misleading one: the failure mode the *Recovery Artifacts* rule exists to prevent, and the one
that makes **H-4** dangerous.

**Drift check** (needs no root — both files are world-readable):

```bash
sha256sum /usr/local/bin/homelab-backup.sh /etc/cron.d/homelab-backup /home/diego/homelab/07_operations/backups/usr/local/bin/homelab-backup.sh /home/diego/homelab/07_operations/backups/etc/cron.d/homelab-backup
```

---

## 6. Items left open, deliberately

* **M-D — the secrets-backup strategy** remains open: `ai-stack/.env`,
  `/home/diego/.secrets/`, `/etc/restic/passwd-homelab`. Unchanged by I-8.
* **The `diego` crontab** is still in neither Git nor the backup set. It was outside I-5's
  scope and outside the I-8 ledger row; it carries no part of the backup mechanism, and no
  remediation identifier is assigned (R-I3-1…7 / F-S1-1 precedent).
* **`backup-probe` still cannot see retention outcomes or script exit status** (H-1c).
  Remediation is **S-8**, open — unchanged by I-8.
* **These files are Recovery Artifacts, not a Deployment Source.** Git does not deploy the
  backup mechanism. Promotion would be a separate, deliberately gated change.
* **The `4f4177e8` deletion remains unidentified** (I-6 §5). Unchanged by I-8.

---

## 7. Program E after I-8

| Item | Status |
|---|---|
| **I-4** — grouping defect | **DONE 2026-07-31** |
| **I-5** — extend coverage (H-2 non-secret half) | **DONE 2026-08-19** |
| **I-6** — anchor protection | **DONE 2026-08-20** |
| **I-8** — track the backup mechanism | **DONE 2026-08-20** — this record |
| **S-8** — backup monitoring blind spot | **NEXT** — depends on **S-7** (Health Aggregator), an open zero-cost decision |
| **S-10** — retention decision + attended prune | Open — **the only irreversible item in the roadmap**, and **unapproved** |

**S-8 depends on S-7**, which is still an open decision. That is a real sequencing constraint,
not a formality: S-7 decides whether a Health Aggregator is built or a third health writer is
accepted, and S-8's design follows from the answer.

**Retention stays `--dry-run`. Nothing about I-8 changes that.**

---

## 8. Rollback

`git rm` the four files, or revert the commit.

**There is nothing to undo in production** — I-8 wrote no host file. This is the first Program
E item whose rollback is genuinely trivial, and the reason is the same reason it needed no
overnight gate: it changed nothing outside the repository.

---

## 9. Documentation audit

| Check | Result |
|---|---|
| Triad reconciled (`CURRENT_STATE`, `ROADMAP`, `AMAROLAB_HANDOFF`) | **Done** — I-8 recorded complete; next milestone moved to **S-8** |
| Stale transient status swept (`PROJECT_RULES.md` → *Transient Operational Status*) | **Done** — "I-8 next" / "Track … in the repo — NEXT" removed from all three; no "at the git gate" phrasing introduced |
| Scope extension recorded, not silent | **Done** — the cron file is outside the ledger's stated I-8 scope and is documented as a deliberate operator-approved extension (§1) |
| Mode asymmetry documented as a control | **Done** — README and §2 both state it is an inertness control, **not** drift, so it is not "fixed" later |
| Doctrine tension recorded rather than hidden | **Done** — the rule 2 / rule 3 conflict, the three options and the reason for the choice are in §2 |
| Coverage claim bounded | **Done** — README and §4 both state I-8 closes version-control durability and **not** restic coverage; H-2 explicitly unchanged |
| Hashes recorded | **Done** — both, in the README, this record and the triad; the pre-I-5 value `90e8eb91…a907a45f` is flagged as a rollback reference only |
| Secrets sanitized | **Confirmed** — no key, credential, token or secret **value** in either captured file or any new document. `/etc/restic/passwd-homelab` appears only as a path, as it already does throughout the triad |
| Historical records left unrewritten | **Confirmed** — the I-4, I-5 and I-6 closeouts and the 2026-07-28 audit records are untouched |
| Gate ledger complete | **Confirmed** — G-I8-1…G-I8-8 all PASS, each with its evidence; the absence of an overnight gate is explained rather than left as a silent omission |

---

## 10. Git gate

**STOP.** Nothing has been staged, committed, pushed or tagged.

To be published together:

* `07_operations/backups/usr/local/bin/homelab-backup.sh` (new — **mode 100644**)
* `07_operations/backups/etc/cron.d/homelab-backup` (new)
* `07_operations/backups/README.md` (new)
* `09_logs/2026-08-20_I8_backup_script_tracked.md` (new — this record)
* `00_overview/CURRENT_STATE.md` (modified)
* `00_overview/ROADMAP.md` (modified)
* `00_overview/AMAROLAB_HANDOFF.md` (modified)

Each of `git commit`, `git push` and `git tag` requires **its own** operator approval,
requested immediately beforehand (`PROJECT_RULES.md` → *Operator Git Approval*). Author as
`Diego <diego@diegoamaro.dev>`.

**No tag is proposed.** I-8 is a remediation item inside Program E, not a phase; Program E
still has S-8 and S-10 open.
