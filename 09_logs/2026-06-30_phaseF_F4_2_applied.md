# F4.2 — operational digest generator + pipeline (applied)

- **Phase / milestone:** F — Operational Intelligence · **F4.2** (frozen at F4.0;
  authority: [`04_ai_system/phase_f_architecture.md`](../04_ai_system/phase_f_architecture.md)
  §9-F-4, AD-15/16/17/18).
- **Date:** 2026-06-30.
- **Scope:** the digest generator, the 04:25 nightly step, and the `ops_digests`
  integration. **Out of scope:** F4.3, triad reconciliation, commit/push/tag.
- **Status:** implementation complete + validated; **both operator `sudo` actions applied
  + verified (2026-06-30)**. Remaining is passive next-cycle confirmation only (the 04:25
  cron firing unattended; `09_ops/runtime` appearing in an actual restic snapshot). **STOP
  at the git approval gate.**

## Implementation

1. **`bin/generate-digest`** (new, `ai-stack/ingest/bin/`) — a dumb consumer (§7) of
   `aurora-context.json` (+ `health.json` for `last_successful_run_end`); **typed fields
   only** (AD-18); **date-anchored** (AD-17 — date in filename, H1, and a header line);
   AD-15 schema; one generated `notable` deviation line ("Nominal — no deviations." on a
   clean night). Atomic write, `0644`, idempotent overwrite; stdlib only (system
   `python3`, like its siblings); `--dry-run` supported.
2. **Cron** — added the **04:25** `generate-digest` line to the git-tracked source
   [`ai-stack/ingest/etc/cron.d/aurora-signals`](../ai-stack/ingest/etc/cron.d/aurora-signals)
   (runs as `diego`, after `push-voice-context` 04:20; never runs git). *Install to
   `/etc/cron.d` is an operator action — below.*

## Validation (this session, against the live 2026-06-29 context)

- **G-F4-01:** digest rendered from real signals; schema correct; `notable` reflects the
  night. Sample `09_ops/runtime/2026-06-29_ops_digest.md` (overall ok, 17/17, snapshot
  c38ddcc1).
- **G-F4-03 (full):** `ingest sync` indexed it (`files_seen 1, chunks_upserted 3,
  errors [], rc 0`); `ops_digests` → 3 points; re-sync idempotent
  (`skipped_unchanged 1, upserted 0`).
- **G-F4-04 (full):** retrieval "night of 2026-06-29" → correct digest top-1 (score 0.87;
  title carries the date) + empty-path clean (from F4.1).
- **G-F4-09 (no secrets):** the digest contains no `.env` value (compared against real
  values, never printed) and no secret var-name token (AD-18).
- **G-F4-02:** the digest is gitignored (`git check-ignore` ✓); `generate-digest` issues
  no git command; the installed `/etc/cron.d/aurora-signals` 04:25 line runs the script
  directly (no git). **PASS.**
- **G-F4-08 (durability):** `09_ops/runtime/` is now in the `homelab-backup.sh` `PATHS`
  (verified); the edited root script still parses (`bash -n`). **Config in place** —
  empirical confirmation (the path inside an actual restic snapshot + a restore-GC
  spot-check) is pending the next 03:00 backup.
- **Unattended-cron preflight:** `generate-digest` runs to success under cron's stripped
  environment (`env -i` + the cron `PATH`), and the cron daemon is `active` — so the 04:25
  job will fire correctly (not merely when run interactively). The restic repo dir
  (`/mnt/storage/backups/restic`) is present.
- **Pending (passive, next nightly cycle):** the unattended 04:25 cron producing a digest;
  `restic ls <snap> | grep 09_ops/runtime` after the next 03:00 backup (root-gated — the
  one F4.2 check that cannot be run without the restic password).

## Operator actions (APPLIED + VERIFIED 2026-06-30)

**1. Install the cron (adds the 04:25 step):**
```
sudo cp /home/diego/homelab/ai-stack/ingest/etc/cron.d/aurora-signals /etc/cron.d/aurora-signals
sudo chown root:root /etc/cron.d/aurora-signals
sudo chmod 0644      /etc/cron.d/aurora-signals
```
Verify next morning: `09_ops/runtime/<date>_ops_digest.md` exists and `aurora-signals.log`
shows the 04:25 run.
**Verified 2026-06-30:** `/etc/cron.d/aurora-signals` is `root:root 0644` and carries the
04:25 `generate-digest` line (chain: backup-probe → container-probe → aurora-context →
push-voice-context → generate-digest). Unattended firing confirms on the next cycle.

**2. Restic durability (AD-16 / G-F4-08)** — add the digest source to the backup `PATHS`
in `/usr/local/bin/homelab-backup.sh` (root-owned, **not** in the repo). Inside the
`PATHS=( … )` array, add:
```
  /home/diego/homelab/09_ops/runtime
```
Rationale: the Qdrant data dir is already backed up, but the raw digest sources are not;
on restore the fs-corpus GC would drop `ops_digests` points whose source file is missing
and **wipe operational memory** (AD-16). Verify after the next 03:00 backup:
`restic ls <latest-nightly-snap> | grep 09_ops/runtime` lists the digest(s).
**Verified 2026-06-30:** `PATHS` now includes `/home/diego/homelab/09_ops/runtime`; the
edited root script parses cleanly (`bash -n`). A trailing space on that line is inert in a
bash array literal. Snapshot/restore confirmation is pending the next 03:00 backup.

## Decisions

- The digest is a **dumb consumer** of `aurora-context.json` (the §7 model), not a
  re-reader of raw signals — one schema owner (`bin/aurora-context`), and AD-18 by design.
- **Digest date = the date of `aurora-context.json` `generated_at`** (the cycle it
  summarises) — a missed nightly cycle does not fabricate a date.
- The ~414-char digest chunks into 3 points; the date is in chunk 0 and in every chunk's
  `title`, so date-anchoring is robust across the split.
- The restic script is root-owned and not version-controlled; F4.2 **documents** the
  exact change as an operator action rather than restructuring backup-script management
  (out of scope; AD-12 caution).

## Rollback (AD-14 isolation)

Remove the 04:25 cron line (+ re-`cp`); delete the script; delete `09_ops/runtime/*.md`
(gitignored) and `ingest sync --collection ops_digests` back to 0. `ops_digests` stays
isolated — no production corpus is touched.

## Git gate (STOP — commit/push/tag out of scope this turn)

Pending working-tree changes: `ai-stack/ingest/bin/generate-digest` (new),
`ai-stack/ingest/etc/cron.d/aurora-signals` (04:25 line), this log. Runtime-only (not
git): the digest file; `ops_digests` (3 points). Triad untouched.
