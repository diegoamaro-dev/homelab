# CURRENT STATE — before Amarolab Assistant Phase A

- **Date generated:** 2026-06-14 10:53 UTC (12:53 CEST)
- **Type:** read-only validation
- **Modifications made:** none (no installs, no restarts, no edits)
- **Privilege required:** none — diego user only, no sudo
- **Purpose:** baseline snapshot to compare against after Phase A onwards

## ⚠ Headline findings

Three things that the implementor should know **before** starting
Phase A. None are blockers; all are worth being aware of.

1. **Host was rebooted at 2026-06-14 00:28 local time.** Phase 1 audit
   recorded 5-day uptime; this run shows 12 h 25 min. Likely cause is
   `unattended-upgrades` (it is enabled); not user-initiated as far as
   shell history shows. **All Phase 0 + Phase 1 state survived the
   reboot intact** (Qdrant collections, .env file, secrets, cron
   entries, ingest service files, container restart policies). The
   reboot is informational, not a problem.
2. **Swap is 100 % used (8 / 8 GiB),** while available RAM is 7.5 GiB
   free. This is "stale swap" from an earlier pressure burst — the
   system has plenty of headroom *now*. No OOM events found in
   user-visible logs. Worth a `swapoff -a && swapon -a` sometime soon
   to reclaim the swap pages, but not urgent.
3. **A wall-clock anomaly was observed.** `date -u` reports current
   time `2026-06-14 10:53 UTC`, but every container's `StartedAt` says
   `2026-06-14T13:04:56Z` (~2 h in the "future"), and the
   `cloudflared` log carries the same `13:04Z` mark for tunnel
   registration. Either the host clock recently jumped *back* via NTP,
   or the containers and cloudflared share a different time source.
   Container `RunningFor` reports "Up 2 hours" which is consistent
   with the user-visible behaviour. Investigation deferred —
   recommend running `timedatectl status` and `chronyc tracking` (or
   `timedatectl show-timesync --all`) outside this read-only audit.

## Section 1 — Docker containers health

All ten containers expected from Phase 1 are present, running, and
**RestartCount = 0** since their last start. Open WebUI is the only one
with a defined healthcheck; status: `healthy`.

| Container | State | Up | Health | Restart count | Image |
|-----------|:----:|:---:|:------:|:-------------:|-------|
| `openwebui` | running | 2 h | **healthy** | 0 | `ghcr.io/open-webui/open-webui:main` |
| `qdrant` | running | 2 h | n/a | 0 | `qdrant/qdrant:latest` |
| `ollama` | running | 2 h | n/a | 0 | `ollama/ollama:latest` |
| `homeassistant` | running | 2 h | n/a | 0 | `ghcr.io/home-assistant/home-assistant:stable` |
| `nginx-proxy-manager` | running | 2 h | n/a | 0 | `jc21/nginx-proxy-manager:latest` |
| `portainer` | running | 2 h | n/a | 0 | `portainer/portainer-ce:latest` |
| `mosquitto` | running | 2 h | n/a | 0 | `eclipse-mosquitto:2` |
| `zigbee2mqtt` | running | 2 h | n/a | 0 | `koenkk/zigbee2mqtt:latest` |
| `guardian-web` | running | 2 h | n/a | 0 | `nginx:alpine` |
| `cloudflared` | running | 2 h | n/a | 0 | `cloudflare/cloudflared:latest` |

No container shows `Restarting` or `Exited`. No `_legacy_*` containers
left over from Phase 0 / Phase 1 recreates (cleanup was completed).

Per-container CPU + memory (live snapshot from `docker stats`):

```
NAME                  CPU %     MEM USAGE / LIMIT
openwebui             3.42%     987.9 MiB / 29.16 GiB
qdrant                0.83%     493.6 MiB / 29.16 GiB
homeassistant         0.88%     442.6 MiB / 29.16 GiB
nginx-proxy-manager   0.09%     166.0 MiB / 29.16 GiB
portainer             0.00%      81.2 MiB / 29.16 GiB
zigbee2mqtt           0.00%      71.8 MiB / 29.16 GiB
ollama                0.00%      48.99 MiB / 29.16 GiB    ← model unloaded, expected
cloudflared           0.00%      34.85 MiB / 29.16 GiB
guardian-web          0.00%      19.44 MiB / 29.16 GiB
mosquitto             0.06%      10.44 MiB / 29.16 GiB
                                ─────────────────────
                       SUM:     ~2.36 GiB
```

## Section 2 — Guardian Cloud backend status (PRODUCTION — read-only)

**Per user policy, no HTTP requests were issued to the Guardian Cloud
backend.** Observability only: PM2, container logs, and tunnel state.

### Backend (Node.js via PM2)

```
id  name                     status   uptime   restarts   pid    mem
 0  guardian-cloud-backend   online   2 h      0          2395   50.6 MB
```

User `diego`, fork mode, watching disabled. **Healthy.**

### Web frontend (nginx container)

`guardian-web` is up, serving live traffic. Recent access log (last
three lines) shows three real requests at `2026-06-14 13:54:06 UTC`
from Google-Read-Aloud / Googlebot (different `66.249/102.x` IPs), all
returning `200`, ~96 KB each. **Healthy.**

### Cloudflare tunnel

`cloudflared` registered four edge connections at startup
(`lhr01`, `lhr15`, `lhr10`, `lhr01`) and **the ingress configuration is**:

```
app.guardiancloud.app  →  http://guardian-web:80
api.guardiancloud.app  →  http://192.168.178.79:3001    ← PM2 backend
(everything else)      →  http_status:404
```

No errors in tunnel log. Tunnel **healthy**, external traffic flowing.

### Summary

Guardian Cloud production surface is up across all three layers
(backend, web, tunnel). **Nothing was modified.** The assistant
implementation in Phase A onwards must continue to treat Guardian
Cloud as a read-only target.

## Section 3 — Open WebUI status

```
HTTP probe:      http=200, time_starttransfer=3.4 ms
/api/config:
  name:        Open WebUI
  version:     0.8.10
  auth:        true
  signup:      false        (kept from Phase 0)
  api_keys:    false        (still off — Phase A roadmap turns this on)
container:     Up 2 h, healthcheck=healthy
RestartCount:  0
RAM:           988 MiB
```

**Environment variables present** (verified through the live container
during prior phases; not re-queried for this report to avoid touching
state):

- `QDRANT_URI=http://qdrant:6333`
- `QDRANT_API_KEY=<set>` ← from Phase 0 R-07
- `WEBUI_SECRET_KEY=<set, 64 hex>` ← from Phase 0 R-05
- `VECTOR_DB=qdrant`
- `OLLAMA_BASE_URL=http://ollama:11434`
- `/var/run/docker.sock` is **NOT** mounted ← Phase 0 R-06 ✓

Status: **healthy, hardened, ready to receive Tools/Functions in
Phase A.**

## Section 4 — Ollama status

```
version:     0.17.7
loaded:      (none — first request will warm a model)
disk usage:  8.3 GB in /srv/homelab/data/ollama/models
```

Models present:

| Tag | Params | Quant | Size |
|-----|-------:|-------|-----:|
| `llama3:latest` | 8.0 B | Q4_0 | 4.66 GB |
| `phi3:latest` | 3.8 B | Q4_0 | 2.18 GB |
| `llama3.2:latest` | 3.2 B | Q4_K_M | 2.02 GB |

> **Note for Phase A:** `qwen2.5:7b-instruct` (the chosen primary tool-
> calling model in the v1 design) is **not yet pulled**. This is
> expected — Phase A starts with that pull (~4.7 GB).

## Section 5 — Qdrant collections and point counts

```
version:           1.17.0 (commit 4ab6d2ee)
unauthenticated:   http=401   (API key required, as expected since Phase 0 R-07)
on-disk size:      ~12 MB total across all collections
```

All six expected collections present and **status=green**:

| Collection | Points | Source |
|------------|------:|--------|
| `homelab_docs` | 86 | Phase 1 ingest |
| `guardian_cloud` | 872 | Phase 1 ingest |
| `ensambla2` | 419 | Phase 1 ingest |
| `myfreetour` | 0 | placeholder (disabled in `corpora.yaml`) |
| `open-webui_files` | 2 | Open WebUI native |
| `open-webui_knowledge` | 3 | Open WebUI native |
| **Total** | **1 382** | |

Vector counts identical to Phase 1 / Phase 1.5 closing state. No drift.

## Section 6 — Backup validation (R-12)

The R-12 nightly restic backup **ran automatically at 03:00 this
morning** — confirmed in `/var/log/homelab-backup.log` (world-readable,
no sudo needed).

```
snapshot f2870cee saved
  date:        2026-06-14 03:00:01
  host:        homelab
  tag:         nightly
  files:       1 410
  size:        1.869 GiB
  policy:      keep 7 daily, 4 weekly, 6 monthly
```

Paths included in the snapshot match the script:

- `/etc/apache2/sites-enabled`
- `/etc/samba/smb.conf`
- `/etc/systemd/system/homelab-tools.service`
- `/home/diego/homelab/03_services/zigbee-stack/mosquitto/{config,data}`
- `/home/diego/homelab/03_services/zigbee-stack/zigbee2mqtt/data`
- `/home/diego/homelab/ai-stack/data/qdrant`
- `/home/diego/webs`
- `/srv/homelab/data/npm`
- `/srv/homelab/data/openwebui` (excluding the embedding cache)
- `/srv/homelab/homeassistant`
- `/tmp/homelab-backup-snapshots/2026-06-14` (the per-run SQLite WAL-
  consistent copies)

Restic retention forgets/prunes correctly: the prior `cc73b4fd`
snapshot (2026-06-13 14:06:34) is still present alongside `f2870cee`
under the keep-7-daily window.

`/mnt/storage/backups/restic` is mode `0700 root:shared` — only root
can list the repo contents (expected; `restic init` creates that
way). The log is sufficient for the read-only health check.

**R-12 status: healthy and active.** No action required.

## Section 7 — Mosquitto + Zigbee2MQTT status

### Mosquitto

```
state:        running, Up 2 h
RestartCount: 0
RAM:          10.4 MiB
log tail:
  mosquitto version 2.1.2 running
  Saving in-memory database to /mosquitto/data//mosquitto.db.
  Saving in-memory database to /mosquitto/data//mosquitto.db.
  Saving in-memory database to /mosquitto/data//mosquitto.db.
  Saving in-memory database to /mosquitto/data//mosquitto.db.
```

Periodic `Saving in-memory database` lines (every ~30 min) indicate
the broker is healthy and persistence is doing its job. **No crash
loop.** Phase 0 R-04 fix is holding.

### Zigbee2MQTT

```
state:        running, Up 2 h
RestartCount: 0
RAM:          71.8 MiB
log tail:
  Starting Zigbee2MQTT without watchdog.
  Onboarding page is available at http://0.0.0.0:8080/
  Using '/app/data' as data directory
  Starting Zigbee2MQTT without watchdog.
  Onboarding page is available at http://0.0.0.0:8080/
```

Same **onboarding-mode loop** noted in Phase 0 R-04 follow-ups — this
is *expected* until you complete the Zigbee2MQTT onboarding wizard at
`http://homelab:8080/` (pair coordinator + first device). Not a fault;
documented in `phase2-remediation/01-critical.md` under "Out-of-scope
observations".

MQTT round-trip mosquitto ↔ z2m was verified end-to-end in Phase 0;
not re-verified here (would require sending a publish, which counts as
modification).

## Section 8 — Home Assistant status

```
container:        Up 2 h, RestartCount=0
network mode:     host
RAM:              442.6 MiB
HA version:       2026.3.1 (from /config/.HA_VERSION inside container
                  AND from /srv/homelab/homeassistant/.HA_VERSION on host —
                  they agree)
HTTP HEAD probe:  http=405  (HA's expected response to a bare HEAD on /)
                  — port is open; no auth required to confirm liveness
```

Notable log lines from this boot (`/srv/homelab/homeassistant/home-assistant.log`):

```
WARNING (Recorder) The system could not validate that the sqlite3
  database at //config/home-assistant_v2.db was shutdown cleanly
WARNING (Recorder) Ended unfinished session (id=61 from 2026-06-13 22:28:19.184946)
ERROR (MainThread) Missing required permissions for Bluetooth management:
  Missing NET_ADMIN/NET_RAW capabilities for Bluetooth management.
  Automatic adapter recovery is unavailable. Add NET_ADMIN and NET_RAW
  capabilities to the container to enable it.
```

Interpretation:

- The **recorder SQLite was not shut down cleanly** in the previous
  session — consistent with the 00:28 host reboot being abrupt rather
  than a controlled shutdown. HA self-healed on start. No data loss
  reported.
- The **Bluetooth NET_ADMIN/NET_RAW warning** is a long-standing
  configuration gap (the HA container doesn't have those caps;
  Bluetooth still works via host's BlueZ but auto-recovery is
  unavailable). Pre-existing, unrelated to v1 work.

Status: **up, serving on :8123 (host network), version 2026.3.1.**
Image still 3 months stale (R-11 sweep deferred).

## Section 9 — PM2 services

```
id  name                     status   uptime   restarts   user    mem
 0  guardian-cloud-backend   online   2 h      0          diego   50.6 MB
```

Single PM2 app, online, zero restarts since this morning's boot. Owned
by `diego`; managed by `pm2-diego.service` systemd unit (enabled and
active per Phase 1 audit, not re-verified here).

Listens on `0.0.0.0:3001` (visible in `ss -tlnp` as
`node` PID 3117). Reached publicly via the
`api.guardiancloud.app` ingress on the Cloudflare tunnel — see
Section 2.

## Section 10 — Disk usage

```
Filesystem      Type   Size    Used    Avail   Use%   Mount
/dev/nvme0n1p2  ext4   468 G   103 G   342 G   24 %   /
/dev/sda1       ext4   1.8 T   9.7 G   1.7 T    1 %   /mnt/storage
/dev/nvme0n1p1  vfat   1.1 G   6.2 M   1.1 G    1 %   /boot/efi
```

Root grew from **98 G → 103 G** since the Phase 1 audit. Accounts for:

- `bge-reranker-v2-m3` model files (~2.6 GB) added during Phase 1.5
- Open WebUI cache + uploads churn (~1 GB)
- Restic backup metadata (~1 GB)

Key directories:

```
3.5 G   /srv/homelab/data/openwebui                 (incl. cache subdir)
3.5 G   /srv/homelab/data/openwebui/cache/embedding/models  (embedder + reranker)
8.3 G   /srv/homelab/data/ollama                    (3 models)
1.4 G   /home/diego/homelab/ai-stack/ingest         (mostly venv)
1.4 G   /home/diego/homelab/ai-stack/ingest/venv    (torch + sentence-transformers)
 12 M   /home/diego/homelab/ai-stack/data           (Qdrant on-disk storage)
400 K   /srv/homelab/data/npm
8 K     /mnt/storage/backups                        (restic repo is root-only;
                                                     real size visible only as root)
```

No disk pressure. The 1.8 TB HDD is at 1 % — plenty of room for Phase A
+ all future RAG ingestion + backup retention.

## Section 11 — RAM usage

```
                  total     used     free   shared   buff/cache  available
Mem:              29 GiB   21 GiB   3.4 GiB  5.6 GiB    10 GiB     7.5 GiB
Swap:             8.0 GiB  8.0 GiB   39 MiB
```

Top 8 processes by RSS:

```
PID    USER    RSS       CMD
4969   root    294.6 MB  python3       (homelab-tools.service — Flask, host)
163546 diego   275.2 MB  2.1.170       (recent npm process; likely a build)
2496   diego   209.6 MB  gnome-shell   (desktop session)
5220   root    138.6 MB  qdrant        (container PID 1)
163601 diego    88.2 MB  node          (related to the npm build)
4640   root     67.1 MB  python3       (a second python process)
5627   root     54.5 MB  node          (?)
3173   root     54.4 MB  dockerd
```

Container processes are dominated by `openwebui` (988 MiB),
`homeassistant` (443 MiB), `qdrant` (494 MiB). Real "live application"
RSS across the box: **~6 GiB**. The remaining 15 GiB of "used" is
**page cache + shared memory** (visible as `buff/cache 10 GiB` +
`shared 5.6 GiB`), which is *normal* and reclaimable.

**Swap 100 % usage** is the only surprise: 8 / 8 GiB. Combined with
`available 7.5 GiB`, this indicates the swap was filled during an
earlier burst (likely the embedding model load + reranker download +
ingest in Phase 1) and the pages have been **swapped but not paged
back in** because the host isn't under memory pressure now. There is
no active swap I/O (load is 0.00 / 0.10 / 0.47).

**Verdict:** memory is fine. Swap can be reclaimed cosmetically
(`swapoff -a && swapon -a`) but is not a problem for Phase A.

## Section 12 — CPU usage

```
load average:    0.00, 0.10, 0.47
%CPU(s):         0.5 us,  0.5 sy,  98.4 id,  0.5 wa
uptime:          12 h 25 min  (boot 2026-06-14 00:28 local)
```

The host is **essentially idle**. 16 threads (Zen 4) free for Phase A.

Top per-process CPU at snapshot: `tailscaled` 8.3 %, `python3` 8.3 %
(both transient — they're 0 in 5-minute load).

## Other Phase 1.5 artefacts verified

| Item | State |
|------|-------|
| `/home/diego/homelab/ai-stack/.env` (Phase 0 secrets + Phase 1 keys) | exists, mode 0600 (verified previously) |
| `/home/diego/homelab/ai-stack/ingest/venv/` | present, 1.4 GB, populated |
| `/home/diego/homelab/ai-stack/ingest/ingest/reranker.py` | present (Phase 1.5) |
| `/srv/homelab/data/openwebui/cache/embedding/models/` | 3.5 GB (embedder + reranker both cached) |
| Diego's crontab | present, contains the `30 2 * * * … ingest sync` line |
| Audit corpus (`infra_audits` Qdrant collection) | **does not exist yet** — created in Phase B per design |
| Open WebUI Functions dir | **does not exist yet** — created in Phase A |
| `homelab-tools` container | **does not exist yet** — created in Phase C |
| `qwen2.5:7b-instruct` model | **not yet pulled** — Phase A first step |
| `WEBUI_API_KEYS_ENABLED=true` | not yet set (currently `false`) — Phase D |
| `HA_LLAT` in `.env` | not present — Phase E |

This matches the v1 design's expectations: everything from Phase 0 / 1
/ 1.5 is in place; nothing from Phase A onwards exists yet.

## Ingest cron — small observation

The user crontab is installed:

```
30 2 * * * /home/diego/homelab/ai-stack/ingest/bin/ingest sync \
   >> /home/diego/homelab/ai-stack/ingest/logs/ingest.log 2>&1
```

But `/home/diego/homelab/ai-stack/ingest/logs/` is **empty** — the
`ingest.log` file does not yet exist. This is **expected**: the cron
was installed *after* today's 02:30 trigger fired, so its first
scheduled run will be **2026-06-15 02:30**. No action needed; just
worth confirming tomorrow morning.

You can also fire it on-demand any time to confirm the path works
end-to-end:

```bash
/home/diego/homelab/ai-stack/ingest/bin/ingest sync
```

(That counts as a write to Qdrant, so it was not run as part of this
read-only validation.)

## Gate for Phase A

This validation gives a clean **GO** for starting Phase A of the
Amarolab Assistant v1 design, with the following caveats noted but
not blocking:

| ID | Note | Severity |
|----|------|---------|
| O-1 | Host rebooted 12 h ago (likely unattended-upgrades) — investigate root cause if recurring | low |
| O-2 | Swap 100 % used despite RAM headroom — stale pages, harmless | low |
| O-3 | Container `StartedAt` UTC vs host `date -u` shows ~2 h discrepancy — verify with `timedatectl status` | medium-informational |
| O-4 | HA recorder DB was not cleanly shut down at last boot — self-healed; revisit only if pattern repeats | low |
| O-5 | HA Bluetooth caps still missing (NET_ADMIN/NET_RAW) — pre-existing, unrelated to v1 | low |
| O-6 | Zigbee2MQTT still in onboarding loop (no devices paired) — pre-existing, awaiting user | low |
| O-7 | R-11 image-update sweep still deferred (HA, openwebui, ollama 3 months stale) | low |

None of these prevent Phase A from starting. Phase A's first action
(`ollama pull qwen2.5:7b-instruct`) is independent of all observations
above.

## How to reproduce

This entire report was generated with read-only shell commands and
HTTP `GET`s. The single thing that required a secret was the Qdrant
collection counts, which used the API key from
`/home/diego/homelab/ai-stack/.env`. No `sudo`, no `docker exec`
beyond reading `.HA_VERSION`, no writes anywhere.
