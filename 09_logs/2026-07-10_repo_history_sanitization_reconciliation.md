# 2026-07-10 — Repository history sanitization — documentation reconciliation

Status: applied — **STOPPED at the git commit gate** (not committed, not pushed, not tagged).
Scope: documentation only. No runtime, tool, prompt, collection, container, DB or code change.

---

## 1. What happened

- On 2026-07-10 the full git history of this repository was **intentionally rewritten
  (sanitized)** and force-pushed to `origin`. The rewrite removed tool-vendor attribution
  from file content and commit metadata, under the standing operator exception to the
  "historical documents are never rewritten" rule (technical facts and chronology
  preserved).
- **Every commit hash changed** (143 commits on `main`; 3 branches; all 21 tags
  recreated). Content deltas were limited to attribution neutralization in 13 files plus
  one file rename under `09_logs/`. Commit dates, authorship identity, ordering and all
  technical content were preserved.
- The published history was verified from a fresh clone: zero attribution matches, single
  author identity, `git fsck` clean.
- The local working repository was resynchronized the same day: `main`, both feature
  branches and all 21 tags now match `origin` exactly (object-level); `git fsck` clean;
  no `refs/replace` / `refs/original`. `feature/zigbee-architecture` (`a145fa18`) was
  legitimately preserved unrewritten — its entire ancestry predates the sanitized
  content, so those commits were byte-identical before and after the rewrite.

## 2. Canonical hash reconciliation

Live operational documentation cited pre-rewrite commit hashes that no longer exist in
the published history (orphaned). Reconciled as follows:

| Item | Previously cited (orphaned) | Canonical (published) |
|---|---|---|
| World Model freeze (AD-21), 2026-07-01 | — (not cited by hash) | `b43e8aad` |
| WM-1 `_schema/` foundation, 2026-07-01 | `9fa4dad4` | `6e97c3fb` |
| WM-2 home entities, 2026-07-01 | `954735c1` | `4c3e2a5d` |
| WM-3 loader — current `main`, 2026-07-02 | — (was "git gate pending") | `8d653fea78ee734f44c0d5027815eb3e5e546cb7` |
| F4.1 operational memory substrate, 2026-06-30 | `9063164a` | `c524ed99` |
| F4.2 operational digest generator, 2026-06-30 | `ac647e24` | `919b8524` |

Every canonical hash above was verified against the published history by commit subject
and date (`git log`), not inferred.

Status changes recorded:

- **WM-3 is committed and pushed — the WM-3 git gate is CLOSED** (it is the current
  `main` tip). The docs' earlier "git gate pending" wording was written before the
  WM-3 commit landed and is now stale.
- **WM-4 (evaluator cutover; retire `HOME_RULES`) remains NOT STARTED** and is the next
  phase. `HOME_RULES` in `ai-stack/ingest/bin/aurora-context` is still the live
  evaluation path (verified).
- **WM-0 freeze tag remains pending** — the freeze package is committed and pushed
  (`b43e8aad`) but no freeze tag was ever created (verified against the 21 published
  tags). This is the only Phase WM git-ceremony item still open.

## 3. Files reconciled (live operational documentation only)

- `00_overview/AMAROLAB_HANDOFF.md`
- `00_overview/CURRENT_STATE.md`
- `00_overview/ROADMAP.md`
- `04_ai_system/world_model/README.md`

Changes: orphaned hashes → canonical hashes; WM-3 marked committed + pushed (git gate
closed); WM-4 confirmed not started; stale "git gate pending" wording removed;
`Last updated` fields advanced to 2026-07-10. Technical meaning and chronology unchanged.

## 4. Intentionally left unchanged

- **`09_logs/` historical logs** — they record the hashes that were real when they were
  written. Per PROJECT_RULES ("Historical Documentation"), corrections belong in later
  documentation; this log is that correction. Anyone reading an older apply log should
  map its hashes through §2 above.
- **`04_ai_system/world_model_architecture.md`** — frozen architectural baseline (AD-21).
- Runtime code, `home_model.md`, `bin/aurora-context` — untouched.

## 5. Validation

- Working tree was clean and `main == origin/main == 8d653fea…` before the edit pass;
  all local branches and all 21 tags verified object-identical to live `origin`.
- Post-edit vendor-attribution scan over every changed file: zero matches.
- `git fsck --full`: clean (0 errors).

## 6. Rollback

- Before commit: `git checkout -- <file>` restores any reconciled doc; deleting this log
  removes the only new file.
- After commit: `git revert` of the reconciliation commit.
- Pre-rewrite history remains available in the operator's local backups
  (`~/homelab_backup_before_rewrite/`, `~/homelab-sanitize-backup-2026-07-10/`) and via
  the old→new commit map (`~/homelab-sanitize-work/final-commit-map.txt`). None of these
  are in the repository.
