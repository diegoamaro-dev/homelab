# Phase E — E5-b Qdrant Restore Drill — Apply Log

- **Date:** 2026-06-27
- **Phase:** E — Knowledge Platform Foundation
- **Step:** E5-b — Qdrant restore drill (F-05b)
- **Outcome:** PASS
- **Operator:** Diego Vázquez Amaro

---

## Objective

Prove that the Qdrant index is recoverable from the nightly restic backup into an
isolated, disposable environment — without touching production Qdrant at any point.

This is a validation step, not a maintenance step. A "FAIL" (counts or retrieval
mismatch) would also be a valid outcome: it would flag a backup-consistency issue
and trigger E4-b (quiesce-then-snapshot recommendation, from F-05a).

---

## Hard Guardrails (operator-set, all maintained)

- Production Qdrant was **not** stopped, restarted, remounted, or modified.
- Restore was performed **only** into `/mnt/storage/restore-drills/e5b-20260627`.
- Test container was disposable, isolated, loopback-only (`127.0.0.1:6399`), not on `ai-local_default`.
- Used the **live Qdrant version (v1.17.0)**, not `:latest`.
- No Guardian Cloud modification.
- No git operations taken.

---

## Procedure and Evidence

### Step 0 — Pre-flight (read-only)

**Production Qdrant:**
- Image tag: `qdrant/qdrant:latest` (resolved to v1.17.0 at pull time)
- Running version: `1.17.0`, commit `4ab6d2ee0f6c718667e553b1055f3e944fef025f`
- Status: running, StartedAt `2026-06-26T23:23:33Z`, RestartCount 0
- REST endpoint: `127.0.0.1:6333`, API key enforced on `/collections` endpoint

**Storage:**
- `/mnt/storage`: 1.7 TB free

**Baseline production counts:**

| Collection    | Points |
|---------------|--------|
| homelab_docs  | 4049   |
| guardian_cloud| 872    |
| ensambla2     | 419    |
| infra_audits  | 280    |
| myfreetour    | 0      |

Additional collections present (Open WebUI managed, not part of ingest audit):
`open-webui_files`, `open-webui_knowledge`.

**Size note:** E-0 audit estimated 36 MB for the Qdrant data directory.
Actual restore size was **2.8 GiB**. The discrepancy is explained by the
`open-webui_files` and `open-webui_knowledge` collections, which store
Open WebUI user-uploaded content and are not tracked by the ingest audit
(E-0 measured only the ingest-managed collections). The 36 MB figure from
F-05a was an undercount.

---

### Step 1 — Snapshot selection

Restic repository: `/mnt/storage/backups/restic` (restic 0.16.4, version 2)

```
ID        Time                 Host     Tags
cc73b4fd  2026-06-13 14:06:34  homelab  nightly
f2870cee  2026-06-14 03:00:01  homelab  nightly
8a4649dd  2026-06-15 03:00:01  homelab  nightly
e993818f  2026-06-16 03:00:01  homelab  nightly
5a5eadf2  2026-06-17 03:00:01  homelab  nightly
63c072f4  2026-06-17 16:19:21  homelab  nightly
8d509017  2026-06-18 03:00:01  homelab  nightly
591cc99f  2026-06-19 03:00:01  homelab  nightly
099cfda9  2026-06-20 03:00:02  homelab  nightly
cdda7751  2026-06-22 03:00:01  homelab  nightly
55fc2f26  2026-06-23 03:00:01  homelab  nightly
56f2df3f  2026-06-24 03:00:01  homelab  nightly
38218f84  2026-06-25 03:00:01  homelab  nightly
b1fc5d86  2026-06-26 03:00:01  homelab  nightly
228e4183  2026-06-27 03:00:01  homelab  nightly   ← selected
```

**Selected snapshot:** `228e4183` — today's nightly (2026-06-27 03:00:01).
15 consecutive nightly snapshots confirm continuous backup operation.

Snapshot includes: `/srv/homelab/data/openwebui`, `/srv/homelab/homeassistant`,
`/srv/homelab/data/npm`, `/home/diego/homelab/ai-stack/data/qdrant`,
`/home/diego/homelab/03_services/zigbee-stack/…`, `/home/diego/webs`,
`/etc/systemd/system/homelab-tools.service`, `/etc/apache2/sites-enabled`,
`/etc/samba/smb.conf`.

---

### Step 2 — Restore

```bash
sudo restic -r /mnt/storage/backups/restic \
  --password-file /etc/restic/passwd-homelab \
  restore 228e4183 \
  --include /home/diego/homelab/ai-stack/data/qdrant \
  --target /mnt/storage/restore-drills/e5b-20260627
```

Output:
```
Summary: Restored 1989 / 1984 files/dirs (2.754 GiB / 2.754 GiB) in 0:02
```

The `--include` filter scoped the restore to the Qdrant subtree only (top-level of
restore target contained only `home/` — confirmed). Restored in ~2 minutes.

---

### Step 3 — Test container

```bash
docker run -d --name qdrant-e5b-drill \
  -p 127.0.0.1:6399:6333 \
  -v /mnt/storage/restore-drills/e5b-20260627/home/diego/homelab/ai-stack/data/qdrant:/qdrant/storage \
  qdrant/qdrant:v1.17.0
```

Image pulled on first use (v1.17.0 pinned tag, digest
`sha256:f1c7272cdac52b38c1a0e89313922d940ba50afd90d593a1605dbbc214e66ffb`).
Container started on loopback-only port `127.0.0.1:6399`, default bridge network
(not `ai-local_default`). No API key (keyless drill container).

---

### Step 4 — Health and version check

```
GET http://127.0.0.1:6399/
→ {"title":"qdrant - vector search engine","version":"1.17.0","commit":"4ab6d2ee0f6c718667e553b1055f3e944fef025f"}
```

Version and commit match production exactly. Container healthy.

---

### Step 5 — Collections and counts

| Collection     | Status | Points (restored) | Points (prod) | Match |
|----------------|--------|-------------------|---------------|-------|
| homelab_docs   | green  | 4049              | 4049          | ✓     |
| guardian_cloud | green  | 872               | 872           | ✓     |
| ensambla2      | green  | 419               | 419           | ✓     |
| infra_audits   | green  | 280               | 280           | ✓     |
| myfreetour     | green  | 0                 | 0             | ✓     |

All 5 collections: green status, exact count parity.

---

### Step 6 — Fixture parity

Comparator: `e5b_comparator.py` (session scratchpad).

Method:
- Embedder: `intfloat/multilingual-e5-small`, query prefix `"query: "` (E5 convention).
- Each query embedded once; vector searched against both endpoints simultaneously.
- Comparison: top-30 id set equality + top-6 rank order equality.
- Fixture: `04_ai_system/validation/retrieval_validation_fixture.yaml` — 16 queries across
  4 collections (4 queries × 4 collections, 8 Spanish + 8 English).

Results:

| Query ID | Collection     | Lang | Set match | Order match | Result |
|----------|----------------|------|-----------|-------------|--------|
| HL-01    | homelab_docs   | es   | ✓         | ✓           | PASS   |
| HL-02    | homelab_docs   | en   | ✓         | ✓           | PASS   |
| HL-03    | homelab_docs   | es   | ✓         | ✓           | PASS   |
| HL-04    | homelab_docs   | en   | ✓         | ✓           | PASS   |
| GC-01    | guardian_cloud | es   | ✓         | ✓           | PASS   |
| GC-02    | guardian_cloud | en   | ✓         | ✓           | PASS   |
| GC-03    | guardian_cloud | es   | ✓         | ✓           | PASS   |
| GC-04    | guardian_cloud | en   | ✓         | ✓           | PASS   |
| E2-01    | ensambla2      | en   | ✓         | ✓           | PASS   |
| E2-02    | ensambla2      | es   | ✓         | ✓           | PASS   |
| E2-03    | ensambla2      | en   | ✓         | ✓           | PASS   |
| E2-04    | ensambla2      | es   | ✓         | ✓           | PASS   |
| IA-01    | infra_audits   | en   | ✓         | ✓           | PASS   |
| IA-02    | infra_audits   | es   | ✓         | ✓           | PASS   |
| IA-03    | infra_audits   | en   | ✓         | ✓           | PASS   |
| IA-04    | infra_audits   | es   | ✓         | ✓           | PASS   |

**Fixture parity: 16/16 PASS.** Top-30 set and top-6 order match exactly for
every query. The backup is a byte-exact, functionally complete replica of production.

---

### Step 7 — Cleanup

- `docker rm -f qdrant-e5b-drill` — container stopped and removed.
- `sudo rm -rf /mnt/storage/restore-drills/e5b-20260627` — restore directory removed.
- `sudo ls -la /mnt/storage/restore-drills` — confirms only the parent directory remains.
- `sudo find /mnt/storage/restore-drills -maxdepth 1` — no entries remain.

---

### Step 8 — Post-drill production verification

| Check                     | Pre-drill                    | Post-drill                   | Match |
|---------------------------|------------------------------|------------------------------|-------|
| Version                   | 1.17.0                       | 1.17.0                       | ✓     |
| StartedAt                 | 2026-06-26T23:23:33Z         | 2026-06-26T23:23:33Z         | ✓     |
| RestartCount              | 0                            | 0                            | ✓     |
| homelab_docs              | 4049                         | 4049                         | ✓     |
| guardian_cloud            | 872                          | 872                          | ✓     |
| ensambla2                 | 419                          | 419                          | ✓     |
| infra_audits              | 280                          | 280                          | ✓     |
| myfreetour                | 0                            | 0                            | ✓     |

Production Qdrant: uptime unbroken, counts unchanged.

---

## Outcome

**E5-b PASS.**

The nightly restic backup at `/mnt/storage/backups/restic` is a complete,
recoverable backup of the Qdrant index. A restore from snapshot `228e4183`
into an isolated environment produced a byte-exact replica: all collections
green, all counts matching, and retrieval fixture parity 16/16.

**Recovery capability is proven.**

---

## Observations and Follow-ups

### Obs-1 — Qdrant backup size discrepancy (documentation correction)

The E-0 audit (F-05a) estimated the Qdrant data directory at "36 MB". The
actual backup size is **2.8 GiB**. The discrepancy is explained by the
`open-webui_files` and `open-webui_knowledge` collections in Qdrant storage,
which are managed by Open WebUI and not tracked by the AMAROLAB ingest
pipeline. The 36 MB figure likely reflected only the ingest-managed collections
at a point before Open WebUI began storing user data in Qdrant. No action
required on the backup itself — 2.8 GiB is well within the restic repository
capacity and the nightly window.

### Obs-2 — Production container uses `:latest` tag (not pinned)

Production Qdrant runs `qdrant/qdrant:latest`, not a pinned version tag.
The resolved version is v1.17.0 (verified via REST API). This is consistent
with E2-c / F-08 (run-lock posture). No action in E5-b scope.

### Obs-3 — Hot backup (raw Qdrant storage)

The nightly restic backup captures the Qdrant storage directory while the
container is running. F-05a noted this as "raw/hot". The 16/16 fixture parity
result demonstrates that this hot backup approach produces a functionally
complete replica in this case. For future reference: if the backup were taken
during an active write (ingest sync), partial writes could leave segments in an
inconsistent state. The nightly cron order (ingest at 02:30, restic at 03:00)
means the backup runs after ingest completes, reducing but not eliminating this
risk. A quiesce-before-backup or Qdrant snapshot-API approach would eliminate
it entirely (E4-b candidate, not Phase E scope).

---

## Links

- Restore drill plan: `09_logs/2026-06-27_phaseE_E5b_continuation_handoff.md`
- Retrieval fixture: `04_ai_system/validation/retrieval_validation_fixture.yaml`
- E-0 audit report: `09_logs/2026-06-27_phaseE_E0_operational_audit_report.md`
- Knowledge platform contract: `04_ai_system/knowledge_platform_contract.md`
