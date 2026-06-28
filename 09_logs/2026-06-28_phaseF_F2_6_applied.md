# Phase F — F2-6 `/opt/aurora` Bind-Mount Applied to `openwebui`

- **Date:** 2026-06-28
- **Phase step:** F-2 — Signal Layer and Context Generation
- **Sub-step:** F2-6 — Mount `aurora/` into openwebui container
- **Status:** COMPLETE

---

## 1. What was applied

Added bind-mount to the running `openwebui` container:

```
/home/diego/homelab/ai-stack/aurora → /opt/aurora  (ro)
```

This mount makes the three context artifacts produced by `aurora-context`
(`aurora-context.json`, `aurora-context.md`, `aurora-context-voice.txt`)
visible inside the container at `/opt/aurora/`, enabling the `system_status`
Open WebUI tool to run in **full mode** instead of fallback mode.

---

## 2. Why Portainer could not apply this change

The original F2-6 plan called for updating the `ai-local` Portainer stack.
This failed with container name conflicts: Portainer reported
`openwebui already exists` and `qdrant already exists`.

### Root cause — Portainer stack drift

The `ai-local` Portainer stack has drifted. Only `ollama` carries
`com.docker.compose.project=ai-local` labels. The other containers that
logically belong to the same stack — `openwebui`, `qdrant`, `portainer`,
and all `aurora-*` services — were recreated at different phases via
Portainer's "Container" UI (equivalent to `docker run`), which drops the
compose project association.

```
docker compose ls → ai-local running(1)   # only ollama is compose-managed
docker ps -a | grep ai-local label        # openwebui: no labels
                                           # qdrant: no labels
```

When Portainer runs `docker compose up` to update the stack, Docker Compose
sees `openwebui` and `qdrant` as **foreign containers** (present but without
project labels) and attempts to create new containers with the same names.
This fails immediately.

### This is a pre-existing condition

The drift predates F2-6. `openwebui` was last recreated 2026-06-27 during
Phase LLAT work; `qdrant` was last recreated 2026-06-16 during Phase C.
Day-to-day operations are completely unaffected. The containers communicate
correctly via the `ai-local_default` Docker network.

### Portainer stack re-association — deferred

Fixing this properly requires:
1. `sudo` access to read `/var/lib/docker/volumes/portainer_data/_data/compose/2/docker-compose.yml`
2. Verification that the compose file matches all current env vars and secrets
3. A controlled maintenance window to stop and recreate the affected containers

This work is **deferred** to a dedicated maintenance session. It is not
required for Aurora functionality.

---

## 3. Recovery method used

Since Portainer could not apply the change, a `docker stop → docker rename
→ docker run` approach was used, deriving all configuration automatically
from `docker inspect` of the live container.

**Script:** `ai-stack/ingest/bin/recreate-openwebui`

The script:
1. Calls `docker inspect openwebui` and parses the full JSON
2. Extracts all 41 env vars and writes them to a `chmod 600` temp file
3. Reconstructs `docker run` from inspect fields (image, restart, network,
   ports, mounts) — no hardcoded configuration
4. Appends the single new mount as the only intentional change
5. Renames the original container to `openwebui_pre_f2_6` (not deleted —
   rollback safety)
6. Stops the renamed original, starts the new container
7. Connects the new container to `proxy_default` (second network, must be
   added post-start)
8. Waits up to 120s for the healthcheck to pass
9. Removes the env file in a `finally` block regardless of outcome

Rollback procedure (if needed):
```bash
docker stop openwebui && docker rm openwebui
docker rename openwebui_pre_f2_6 openwebui
docker start openwebui
```

---

## 4. Execution log

```
Preflight checks:
  openwebui:                Up 37 minutes (healthy)     ✓
  aurora-context.json:      present, -rw-r--r-- diego   ✓

Script output:
  Renaming openwebui → openwebui_pre_f2_6...           ✓
  Stopping openwebui_pre_f2_6...                        ✓
  Starting new container...    ID: 18b8b2d133b3         ✓
  Connecting to proxy_default...                        ✓
  health: starting × 6
  health: healthy                                       ✓
  SUCCESS: openwebui is healthy.
  Env file removed.                                     ✓
```

---

## 5. Validation results

| # | Check | Result |
|---|---|---|
| V1 | `docker ps` — container running and healthy | **PASS** `Up 50s (healthy)` |
| V2 | Three mounts present (`/app/backend/data` rw, `/opt/ingest` ro, `/opt/aurora` ro) | **PASS** |
| V3 | Host/container `aurora-context.json` timestamps identical (`2026-06-28T10:17:54Z`) | **PASS** |
| V4 | `/opt/ingest/logs/health.json` accessible inside container | **PASS** |
| V5 | `system_status` tool in **full mode** (not fallback) | **PASS** — see below |
| V6 | `openwebui_pre_f2_6` exists and is stopped | **PASS** `Exited (0)` |

### V5 — `system_status` full mode output (2026-06-28 10:55 UTC)

```
AMAROLAB System Status — 2026-06-28 10:55 UTC

Overall: degraded
Reasons:
  • backup outside freshness window

---

Context:     2026-06-28 10:17 UTC (0.6h ago)
Torre (live): reachable (3ms)
System:      CPU 1.3% | RAM 16.8% | Disk 29.3%

Ingest:      ok — last run 2026-06-28 00:30 UTC (10.4h ago, rc=0)
Backup:      no snapshot tonight — last: 2026-06-28 01:00 UTC (9.9h ago)
Audit:       ok — last entry age 0 days
Containers:  17/17 running

Signals missing: none
```

**Full mode confirmed:** `Context:` shows a real timestamp (not "not mounted");
`Containers:` and `Backup:` both show live signal data (not "not available");
`Signals missing: none`.

`Overall: degraded` is expected and correct — the snapshot at 01:00 UTC is
~9.9h old at test time; the production cron at 04:15 CEST (~02:15 UTC) runs
within the 4h window and will report `ok`.

---

## 6. Rollback container

`openwebui_pre_f2_6` — `Exited (0)`, preserved for 24h minimum.

To roll back:
```bash
docker stop openwebui && docker rm openwebui
docker rename openwebui_pre_f2_6 openwebui
docker start openwebui
```

Remove after confirming stable operation through at least one nightly cron
cycle (backup-probe 03:30, container-probe 04:00, aurora-context 04:15).

---

## 7. Files changed

| File | Action |
|---|---|
| `ai-stack/ingest/bin/recreate-openwebui` | Created — F2-6 recovery script (derived from docker inspect) |
| `09_logs/2026-06-28_phaseF_F2_6_applied.md` | Created — this document |

---

## 8. Open items entering F2-7 / F2-8

| Item | Status |
|---|---|
| Portainer stack re-association | **Deferred maintenance** — needs sudo + controlled window |
| `/etc/cron.d/aurora-signals` | **Next step** — backup-probe 03:30, container-probe 04:00, aurora-context 04:15 |
| Chat-level tool validation (G-F1-01) | Pending browser session — "¿Cuál es el estado del sistema?" |
| Remove `openwebui_pre_f2_6` rollback container | After 24h stable operation |

---

*F2-6 complete. `/opt/aurora` bind-mount applied. `system_status` tool running in full mode.*
*All 6 validation checks pass. Rollback container preserved.*
