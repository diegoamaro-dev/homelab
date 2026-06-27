# Phase E — E5-b Continuation Handoff (pre-execution record)

> **Transient pre-execution artifact.** Lets any future session resume E5-b
> without this chat. Superseded by the E5-b apply log once the drill completes.
> Uncommitted by design (no git op taken without operator approval).

- **Created:** 2026-06-27, immediately before E5-b execution.
- **Why:** mandatory context-preservation record for a potentially disruptive
  step (restic restore + disposable test container).

## Where we are
- Phase E. **E-0, E-1 closed; E2-a done (F-01); E5-a done (F-02 — no retrieval
  drift, E2-b not required).**
- Git: local `main` HEAD = `31accae0` (E5-a). **E5-a is committed locally but
  NOT pushed** (origin/main = `4b918251`, E2-a). Working tree clean.
- Deferred (queued in memory, not a commit): scope the E5-a "no drift"
  conclusion to the current embedding model/pipeline — fold into next doc
  reconciliation. See memory `e5a-conclusion-scope-caveat`.

## E5-b — approved plan (execute exactly as planned)
**Objective:** prove the Qdrant index is recoverable from restic backup into an
isolated/disposable environment, **without touching production Qdrant**.

**Hard guardrails (operator-set):**
- Production Qdrant **not** stopped/restarted/remounted/modified (read-only:
  search + count only; uptime must stay unbroken).
- Restore **only** into a temp dir under `/mnt/storage/restore-drills/`.
- Test container disposable, isolated, **loopback-only** (`127.0.0.1:6399`),
  **not** on `ai-local_default`.
- Use the **live Qdrant version (v1.17.0)**, not `:latest`.
- No Guardian Cloud modification. No git ops without explicit approval.

**Key facts:** restic `0.16.4`; repo `/mnt/storage/backups/restic` (root-only →
sudo); passphrase `/etc/restic/passwd-homelab`; backed-up path
`/home/diego/homelab/ai-stack/data/qdrant` (36 MB, raw/hot — F-05a); `/mnt/storage`
1.7 TB free; prod Qdrant `qdrant/qdrant` **v1.17.0**, storage→`/qdrant/storage`,
REST `127.0.0.1:6333`, API key from `ai-stack/.env`.

**Procedure (🔑=sudo):** (0) read-only pre-flight: `docker inspect qdrant`
(confirm v1.17.0 + image id), `df -h /mnt/storage`, baseline prod counts. (1) 🔑
`restic snapshots` → pick latest with the qdrant path; record ID. (2) 🔑 `restic
restore <id> --include /home/diego/homelab/ai-stack/data/qdrant --target
/mnt/storage/restore-drills/e5b-<ts>`. (3) `docker run -d --name qdrant-e5b-drill
-p 127.0.0.1:6399:6333 -v <target>/home/diego/homelab/ai-stack/data/qdrant:/qdrant/storage
qdrant/qdrant:v1.17.0` (keyless, default bridge). (4) health + version==1.17.0.
(5) `/collections` all green + counts. (6) fixture parity via a thin two-endpoint
comparator (reuse `04_ai_system/validation/retrieval_validation_fixture.yaml` +
embedder + search): same stack-A query vector → search prod(6333) & restored(6399)
→ compare top-30 set + top-6 order, 16/16. (7) cleanup. (8) prod counts unchanged
+ uptime unbroken.

**Expected PASS evidence:** snapshot ID; restore ≈36 MB; container healthy;
version match; all collections green; counts `4049/872/419/280/0`; fixture
parity 16/16; prod untouched; cleanup done. A FAIL (mismatch) is still a valid
E5-b outcome → recommend quiesce/snapshot-API backup (feeds E4-b/F-05a).

## If this session is interrupted mid-drill — cleanup checklist
1. `docker ps -a | grep qdrant-e5b-drill` → `docker rm -f qdrant-e5b-drill` if present.
2. `ls /mnt/storage/restore-drills/` → 🔑 `rm -rf /mnt/storage/restore-drills/e5b-*` (NEVER the live path `/home/diego/homelab/ai-stack/data/qdrant`).
3. Confirm production `qdrant` container still up (unbroken uptime) and counts `4049/872/419/280/0`.
4. Guardian Cloud untouched.

## Resume point
After the context-preservation check is satisfied (incl. tmux decision),
execute E5-b from step 0. Stop after Validation + Git review.
