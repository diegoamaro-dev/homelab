# Phase F — F2-3 `container-probe` Implementation

- **Date:** 2026-06-28
- **Phase step:** F-2 — Signal Layer and Context Generation
- **Sub-step:** F2-3 — `container-probe` script
- **Status:** COMPLETE

---

## 1. What was implemented

New script: `ai-stack/ingest/bin/container-probe`

Enumerates all Docker containers via `docker ps -a` and writes
`ai-stack/ingest/logs/container_status.json` atomically. Runs as diego
(docker group member; no sudo needed).

Key design decisions:
- `docker ps -a` — includes stopped containers; omitting `-a` would silently
  hide degraded services
- `State` field (not `Status`) — machine-readable Docker state string:
  `"running"`, `"exited"`, `"paused"`, etc.
- `running: true` only when `State == "running"`
- `degraded[]` — names of all non-running containers; drives
  `all_running: false` and aurora-context's `overall_status: "degraded"`
- Explicit error payload on Docker failure (daemon unreachable, binary
  missing): `probe_error` set, all data fields `null`, exits 1
- Atomic write: `.tmp` → fsync → `chmod 0644` → `os.replace()`
- Stdlib only; no venv dependency
- No hardcoded container baseline — fully dynamic discovery

Updated `ai-stack/ingest/docs/signals_contract.md`:
- Added error payload example for `container_status.json`
- Added `probe_error` field to field reference
- Added status rules section
- Clarified baseline note: script is dynamic; 17 is a documentation
  reference, not a code constraint

---

## 2. Baseline finding and cleanup

During initial validation, `docker ps -a` returned **21 containers** (not 17),
with 4 in `exited` state:

| Container | Image | Created | Reason |
|---|---|---|---|
| `openwebui_pre_llat_recreate_20260617004619` | `open-webui:main` | 2026-06-17 | Phase LLAT rollback snapshot |
| `openwebui_pre_phaseC_20260616123559` | `open-webui:main` | 2026-06-16 | Phase C rollback snapshot |
| `openwebui_pre_phaseB_20260616015215` | `open-webui:main` | 2026-06-16 | Phase B rollback snapshot |
| `qdrant_pre_phaseC_20260616123238` | `qdrant:latest` | 2026-06-16 | Phase C rollback snapshot |

These are historical rollback artifacts with no further use. They were causing
`all_running: false` and would have made Aurora report a degraded state every
night.

**Pre-removal checks (all passed):**
- All 4 in `exited` state, `running=false`
- No running container has `volumes-from` dependency on any of the 4
- No running container has `--link` to any of the 4
- Mounts were bind paths shared with live containers — removing the stopped
  containers does not affect data on disk

**Action:** `docker rm` on all 4. Operator-approved.

**Mounts at time of removal (for the record):**
- `openwebui_pre_llat_recreate`: `/srv/homelab/data/openwebui`, `/home/diego/homelab/ai-stack/ingest`
- `openwebui_pre_phaseC`: `/srv/homelab/data/openwebui`, `/home/diego/homelab/ai-stack/ingest`
- `openwebui_pre_phaseB`: `/srv/homelab/data/openwebui`
- `qdrant_pre_phaseC`: `/home/diego/homelab/ai-stack/data/qdrant`

---

## 3. Validation results

| Step | Test | Result |
|---|---|---|
| 1 | Primary run — exits 0, writes file | **PASS** |
| 2 | `python3 -m json.tool` — JSON valid | **PASS** |
| 3 | `container_count` matches `docker ps -a \| wc -l` (21 = 21 pre-cleanup; 17 = 17 post-cleanup) | **PASS** |
| 4 | Mock degraded: `bad-worker` exited → `degraded: ["bad-worker"]`, `all_running: false` | **PASS** |
| 5 | `DOCKER_HOST=unix:///nonexistent.sock` → `probe_error` set, all data `null`, exits 1 | **PASS** |
| 6 | Post-cleanup re-run: `container_count=17`, `all_running=true`, `degraded=[]` | **PASS** |

---

## 4. Files created or modified

| File | Action |
|---|---|
| `ai-stack/ingest/bin/container-probe` | Created, committed |
| `ai-stack/ingest/docs/signals_contract.md` | Updated — error payload, status rules |
| `ai-stack/ingest/logs/container_status.json` | Runtime artifact, gitignored |

---

## 5. Open items entering F2-4

| Item | Status |
|---|---|
| `/etc/cron.d/aurora-signals` (all probe entries) | **Not yet installed** — deferred to end of F2 |
| `aurora-context` script | **Next step — F2-4** |
| `system_status` Open WebUI tool | Pending F2-5 |
| `/opt/aurora` bind-mount (Portainer) | Pending F2-6 |

---

*F2-3 complete. `container-probe` validated; 4 historical rollback containers removed; 17-container all-running baseline confirmed.*
