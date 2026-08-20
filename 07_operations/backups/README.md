# 07_operations/backups — nightly backup mechanism

## Status: RECOVERY ARTIFACTS, not the deployment source

The two files in this directory were **captured byte-identically from the running system on
2026-08-20** (remediation item **I-8**, audit finding **N-5**). They describe what is
deployed. They are **not** the thing that deploys it.

> **Git is not the deployment source of truth for the backup mechanism.** These files are
> Recovery Artifacts under `PROJECT_RULES.md` → *Recovery Artifacts*. Promotion to a
> Deployment Source would be a separate, deliberately gated change — never a drift.

**This README is the authority for install targets and drift checks.**

---

## Inventory and install targets

| Tracked path | Installs to | Live mode | Git mode |
|---|---|---|---|
| `usr/local/bin/homelab-backup.sh` | `/usr/local/bin/homelab-backup.sh` | `0755 root:root` | **`0644` — deliberate, see below** |
| `etc/cron.d/homelab-backup` | `/etc/cron.d/homelab-backup` | `0644 root:root` | `0644` — matches live |

The directory layout **mirrors the host paths** so the install target is legible from the
path itself, following the `ai-stack/ingest/etc/cron.d/aurora-signals` precedent.

### Recorded content hashes — captured 2026-08-20

```
330df064d012f1b04f98c6dc94ab92caea08f3e9cd244a7a53aecdff5895a554  homelab-backup.sh
976aa6942c9fc286f3b5ef34e7d770cbc501160607d34dba7f2a40dc7ebc8756  homelab-backup (cron)
```

The script hash is the **I-5 version**, unchanged by I-6, which deliberately did not modify
the script. `90e8eb91…a907a45f` is the **pre-I-5 rollback reference only** and must never be
mistaken for the current target.

---

## The mode asymmetry is an inertness control, not drift

**The live script is `0755`. The tracked copy is committed `0644`. This is deliberate and
approved; do not "fix" it.**

`PROJECT_RULES.md` → *Recovery Artifacts* rule 2 requires an artifact to be **inert by
construction, not by convention**. A warning comment is not a control. Committing the script
non-executable is the mechanical guard: an accidental `./homelab-backup.sh` fails on
permissions.

**The specific hazard it blocks:** this script performs a real `restic backup`. Running a
**drifted** copy of it would create a genuine snapshot with a wrong path set, which — because
`restic forget` groups by `host,paths` — would open a **spurious group** and pollute the
input that **S-10** plans against. The guard is cheap, and it costs **zero bytes of content**,
so byte-identity with the live file is preserved and remains provable by one command.

The cron file needs no such guard: `0644` is already its live mode, so it carries **both
content and mode parity**.

---

## Drift check

The tracked copies can drift from the installed files. Content parity is the property that
matters, and it is verified directly:

```bash
sha256sum /usr/local/bin/homelab-backup.sh /etc/cron.d/homelab-backup /home/diego/homelab/07_operations/backups/usr/local/bin/homelab-backup.sh /home/diego/homelab/07_operations/backups/etc/cron.d/homelab-backup
```

The first and third hashes must match; the second and fourth must match. Both files are
world-readable, so **this check needs no root.**

Equivalent per-file form:

```bash
diff /usr/local/bin/homelab-backup.sh /home/diego/homelab/07_operations/backups/usr/local/bin/homelab-backup.sh
```

**Ignore the mode difference on the script — only content is compared.**

---

## Standing obligation

**Whenever either live file changes, the tracked copy must be updated in Git in the same
change**, and the new sha256 recorded here and in the triad. This is the same discipline that
made the script's sha256 a triad-tracked value at I-5 and kept it correct through I-6.

A change to the live script that is not mirrored here silently converts these files from a
recovery asset into a misleading one — the failure mode the *Recovery Artifacts* rule exists
to prevent, and the one that made **H-4** dangerous.

---

## What I-8 does and does not close

* **Closes: version-control durability.** Before I-8 the backup mechanism existed in exactly
  one place, on the root disk. It had **never** been tracked in Git — verified at capture:
  zero matches in the working tree and zero add-commits across all history. Git plus the
  GitHub remote now give it an **off-host** copy, which the restic repository cannot: that
  repository lives on the same physical machine (`07_operations/backups.md` → *What is still
  missing*).
* **Does NOT close: restic coverage.** `07_operations/` is **not** in the restic path set, so
  neither file entered the backup. **Audit finding H-2 is unchanged by I-8** — its non-secret
  half closed at I-5, its secret half remains **M-D**, open. The scheduling assets remain
  outside the restic set exactly as the I-5 closeout recorded.

---

## Restore procedure

Recovering the nightly backup mechanism onto a rebuilt host:

```bash
sudo install -m 0755 -o root -g root /home/diego/homelab/07_operations/backups/usr/local/bin/homelab-backup.sh /usr/local/bin/homelab-backup.sh
```

```bash
sudo install -m 0644 -o root -g root /home/diego/homelab/07_operations/backups/etc/cron.d/homelab-backup /etc/cron.d/homelab-backup
```

Note the **explicit `-m 0755`** for the script: the tracked copy is intentionally
non-executable, and the install step is where the executable bit is granted — deliberately,
by a human, on a real host.

`cron` ignores files under `/etc/cron.d/` that are not root-owned or are group/world-writable,
so the ownership and mode above are load-bearing.

**Also required, and NOT provided by these files:** `restic` installed, the repository at
`/mnt/storage/backups/restic`, and the password file `/etc/restic/passwd-homelab`. That last
one is **M-D, open** — it is outside the backup set, and without it the repository cannot be
decrypted at all. Restoring these two files does not by itself restore the ability to read a
backup.

---

## Invariants that must not be changed outside S-10

The script encodes decisions taken across three remediation items. Each is load-bearing:

| Invariant | Established by | Why |
|---|---|---|
| `SNAP_DIR` contains **no date** | I-4 | A dated path changed the recorded path set every run, so every snapshot landed in a group of one and retention was structurally inert |
| **16 static path literals** — no date, timestamp or variable component | I-5 | Same defect class; the path set must be deterministic or grouping breaks |
| `restic forget` runs `--dry-run` | I-4 | **A deliberate safety hold, not a leftover.** The policy is live again and would delete unattended without it |
| `--prune` is **absent** from the command | I-4 | `restic forget` deletes snapshots on its own; `--prune` only reclaims data afterwards, so removing it is **not** protective |
| `--group-by` is **not** overridden | I-4 | restic's default `host,paths` grouping is retained as a safety property |

**Re-enabling deletion is S-10** — attended, operator-approved per execution, and the only
irreversible item in the remediation roadmap. **S-10 is Open and unapproved.**

Separately, the D-1.5 rollback anchor `42506e44` is protected at snapshot level and sits
**outside `--tag nightly` scope** (I-6). Nothing in this directory affects it, and it must
never be retagged — see `09_logs/2026-08-20_I6_closeout.md`.

---

## References

* Capture and gates: [`../../09_logs/2026-08-20_I8_backup_script_tracked.md`](../../09_logs/2026-08-20_I8_backup_script_tracked.md)
* Retention grouping fix: [`../../09_logs/2026-07-31_I4_gate8_closeout.md`](../../09_logs/2026-07-31_I4_gate8_closeout.md)
* Coverage extension: [`../../09_logs/2026-08-19_I5_closeout.md`](../../09_logs/2026-08-19_I5_closeout.md)
* Anchor protection: [`../../09_logs/2026-08-20_I6_closeout.md`](../../09_logs/2026-08-20_I6_closeout.md)
* Backup incident diagnosis: [`../../09_logs/2026-07-28_backup_retention_incident.md`](../../09_logs/2026-07-28_backup_retention_incident.md)
* Recovery Artifact doctrine: [`../../00_overview/PROJECT_RULES.md`](../../00_overview/PROJECT_RULES.md) → *Recovery Artifacts*
* Sibling precedent (a Deployment Source, for contrast): [`../../03_services/README.md`](../../03_services/README.md)
