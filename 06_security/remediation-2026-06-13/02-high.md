# 02 — High priority fixes (this week)

Three findings: an exploit path that *would* be Critical without the
"only-LAN" boundary (R-06), unauthenticated AI service APIs (R-07), and
the operational risk of running with no backups (R-12).

R-06, R-07 and R-11 (in [03-medium.md](03-medium.md)) all benefit from
having a checked-in compose file per stack (R-14). The procedures below
include a minimal compose stub each time so they remain stand-alone.

---

## R-06 — Stop sharing the host Docker socket with Open WebUI  ✅ APPLIED 2026-06-13

**Risk M · Impact H (host root) · Time 45 m · Priority 🟠 High**

> **Status:** Applied 2026-06-13. Open WebUI was recreated **without**
> the `/var/run/docker.sock` bind mount. The host Docker socket can no
> longer be reached from inside the openwebui container, eliminating
> the host-root escape path. See the [Phase 0 application log](#phase-0-application-2026-06-13)
> at the end of this section.

### Current state

```
docker inspect openwebui --format '{{json .Mounts}}'
[
  {"Type":"bind","Source":"/srv/homelab/data/openwebui","Destination":"/app/backend/data", …},
  {"Type":"bind","Source":"/var/run/docker.sock","Destination":"/var/run/docker.sock","RW":true, …}
]
```

Open WebUI Tools / Functions / Pipelines can issue Docker API calls and
escape to host root via `docker run -v /:/host …`. Today the existing
admin account is the only entity that could do that, but the surface is
real and grows every time a "tool" is installed in Open WebUI.

### Target state

The `openwebui` container no longer has direct access to
`/var/run/docker.sock`. Two acceptable end states:

- **A (preferred):** socket removed entirely. Open WebUI's container-aware
  features go offline; everything else is unaffected.
- **B (only if you actively use Open WebUI's container features):** access
  is proxied by `tecnativa/docker-socket-proxy` with a read-only allowlist.

### Procedure — Option A: drop the socket mount

`openwebui` was started with `docker run`, not compose, so first capture
its current shape so the rebuild is reproducible.

```bash
# Step 1 — capture a compose file from the running container
# (no external dependency; uses the inspect output we already have)
mkdir -p /home/diego/homelab/ai-stack
cat > /home/diego/homelab/ai-stack/docker-compose.yml <<'EOF'
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    restart: unless-stopped
    networks:
      - ai-local
    ports:
      - "127.0.0.1:11434:11434"        # see R-07
    environment:
      - OLLAMA_HOST=0.0.0.0:11434
    volumes:
      - /srv/homelab/data/ollama:/root/.ollama

  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant
    restart: unless-stopped
    networks:
      - ai-local
    ports:
      - "127.0.0.1:6333:6333"          # see R-07
    env_file:
      - .env                            # QDRANT__SERVICE__API_KEY (R-07)
    volumes:
      - /home/diego/homelab/ai-stack/data/qdrant:/qdrant/storage

  openwebui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: openwebui
    restart: unless-stopped
    networks:
      - ai-local
      - proxy
    ports:
      - "3000:8080"
    env_file:
      - .env                            # WEBUI_SECRET_KEY etc (R-05)
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - VECTOR_DB=qdrant
      - QDRANT_URI=http://qdrant:6333
      - ENV=prod
      - PORT=8080
      - SCARF_NO_ANALYTICS=true
      - DO_NOT_TRACK=true
      - ANONYMIZED_TELEMETRY=false
    volumes:
      - /srv/homelab/data/openwebui:/app/backend/data
      # NOTE: /var/run/docker.sock is INTENTIONALLY OMITTED (R-06)

networks:
  ai-local:
    name: ai-local_default
    external: true
  proxy:
    name: proxy_default
    external: true
EOF

# Step 2 — stop and remove the old containers in the right order
docker stop openwebui ollama qdrant
docker rename openwebui openwebui_legacy_2026-06-13
docker rename ollama    ollama_legacy_2026-06-13
docker rename qdrant    qdrant_legacy_2026-06-13

# Step 3 — bring up the new ones
cd /home/diego/homelab/ai-stack
docker compose up -d

# Step 4 — verify, then drop the renamed legacy containers
# (only once Open WebUI works end-to-end)
docker rm openwebui_legacy_2026-06-13 \
          ollama_legacy_2026-06-13 \
          qdrant_legacy_2026-06-13
```

### Diff — what changed in `openwebui` mounts

```diff
 Mounts:
 - bind  /srv/homelab/data/openwebui  →  /app/backend/data  (rw)
-- bind  /var/run/docker.sock         →  /var/run/docker.sock  (rw)
```

### Procedure — Option B: docker-socket-proxy

Adds one new container that owns the socket and exposes a filtered API on
its container network. Open WebUI talks to `tcp://docker-socket-proxy:2375`
instead of the socket.

```yaml
# Add to the compose file above:
  docker-socket-proxy:
    image: tecnativa/docker-socket-proxy
    container_name: docker-socket-proxy
    restart: unless-stopped
    networks:
      - ai-local
    environment:
      CONTAINERS: 1
      INFO: 1
      VERSION: 1
      # POST=0, DELETE=0 by default → read-only
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
```

```diff
# openwebui environment
+      - DOCKER_HOST=tcp://docker-socket-proxy:2375
```

Open WebUI loses *write* access to Docker; it can still introspect
containers it has been told about.

### Validation

```bash
# 1. Open WebUI mount no longer includes the socket
docker inspect openwebui --format '{{json .Mounts}}' | grep -c docker.sock
# Expect: 0  (Option A)  or  : 0 in openwebui, 1 in docker-socket-proxy (Option B)

# 2. UI is reachable
curl -fsI http://127.0.0.1:3000/ | head -1
# Expect: HTTP/1.1 200 OK

# 3. Ollama and Qdrant still reachable from openwebui via the docker
#    network (this is the path that actually matters):
docker exec openwebui sh -c 'wget -qO- http://ollama:11434/api/version'
docker exec openwebui sh -c 'wget -qO- http://qdrant:6333/'
```

### Rollback

The legacy containers were preserved as `*_legacy_2026-06-13`. To return
to the previous state:

```bash
docker stop openwebui ollama qdrant
docker rm   openwebui ollama qdrant
docker start openwebui_legacy_2026-06-13 \
             ollama_legacy_2026-06-13 \
             qdrant_legacy_2026-06-13
docker rename openwebui_legacy_2026-06-13 openwebui
docker rename ollama_legacy_2026-06-13    ollama
docker rename qdrant_legacy_2026-06-13    qdrant
```

---

### Phase 0 application (2026-06-13)

#### Pre-flight check

Before pulling the mount I confirmed nothing inside the container was
holding it open:

- No process FD in `/proc/*/fd/*` referenced `docker.sock`.
- No file under the `/srv/homelab/data/openwebui/` bind-mount contained
  the string `docker` (excluding the cache dir and the SQLite DB).
- The `webui.db` `tool` table holds 3 rows: `docker_containers`,
  `docker_logs`, `system_status`. The two docker-named tools were
  inspected; both use `requests` to call the LAN `homelab-tools` Flask
  API at `http://192.168.178.79:5050/docker/...` — they do **not**
  touch the socket. `system_status` uses `psutil` against the
  container's own `/proc`.

#### What changed

The `openwebui` container was recreated with the same env-set and
networks as the R-05 recreate, but the
`/var/run/docker.sock:/var/run/docker.sock` bind mount was **dropped**.
The single remaining mount is `/srv/homelab/data/openwebui:/app/backend/data`.

Legacy container preserved as `openwebui_legacy_2026-06-13_r06` until
validation passed, then `docker rm`'d.

#### Validation (2026-06-13 18:54 UTC)

| # | Probe | Expected | Result |
|---|-------|----------|--------|
| 1 | Container reaches health=healthy | Yes | ✅ Up 30 s, healthy |
| 2 | docker.sock no longer in container mounts | 0 matches | ✅ 0 |
| 3 | `ls /var/run/docker.sock` inside container | "No such file" | ✅ |
| 4 | All 3 stored tools still rows in DB | yes | ✅ |
| 5 | `docker_*` tools' upstream (Flask `:5050`) reachable | 200 | ✅ 200 |
| 6 | Open WebUI ↔ Qdrant (auth) | 200 | ✅ 200 |
| 7 | Open WebUI ↔ Ollama | `{"version":"0.17.7"}` | ✅ |
| 8 | `WEBUI_SECRET_KEY` length still 65 (R-05 not regressed) | 65 | ✅ 65 |
| 9 | `/api/config` healthy | status=true, auth=true, version 0.8.10 | ✅ |

#### Coupling to R-02 (Flask homelab-tools)

The `docker_containers` and `docker_logs` Open WebUI tools reach
`homelab-tools` over the LAN IP `192.168.178.79:5050`. They are now
**fully dependent on the Flask API being LAN-reachable** — the socket
fallback no longer exists. This is fine today; the consequence is:

- **If/when R-02 is applied** (Flask binds to `127.0.0.1` instead of
  `0.0.0.0`), those two tools will break, because Open WebUI's
  container cannot reach the host's `127.0.0.1:5050`.
- **Recommended migration when R-02 lands:** containerise
  `homelab-tools`, put it on `ai-local_default`, and update the two
  tool URLs to `http://homelab-tools:5050/docker/*`. That replaces a
  LAN-IP cross-call with a Docker DNS name and removes the
  "0.0.0.0 vs 127.0.0.1" question entirely.

A flag of this dependency is now part of R-02's open follow-ups.

---

## R-07 — Bind Ollama and Qdrant published ports to `127.0.0.1` (and add Qdrant API key)  ✅ PARTIALLY APPLIED 2026-06-13

**Risk M · Impact M · Time 20 m · Priority 🟠 High**

> **Status (Phase 0):** The **Qdrant API key** half is applied. The
> **port-rebind to `127.0.0.1`** half is intentionally deferred — the
> assistant work in Phase 3 is the right time to fold it in alongside
> R-14 (compose files). Ollama is untouched in this round.
>
> See the [Phase 0 application log](#phase-0-application-2026-06-13) at
> the end of this section for the qdrant + openwebui recreate map and
> the full validation log.

### Current state

```
ollama   0.0.0.0:11434 → 11434/tcp
qdrant   0.0.0.0:6333  → 6333/tcp
```

Both are reachable from LAN and tailnet with no authentication. Qdrant
also exposes `/metrics` and `/telemetry` unauthenticated (R-19).

Inside the `ai-local_default` Docker network, Open WebUI talks to them by
DNS name (`http://ollama:11434`, `http://qdrant:6333`) — that path is
*separate* from the host port-publish, so flipping the host bind does not
break Open WebUI.

### Target state

```
ollama   127.0.0.1:11434 → 11434/tcp
qdrant   127.0.0.1:6333  → 6333/tcp   + QDRANT__SERVICE__API_KEY set
```

The compose file in R-06 already encodes this. If R-06 has been applied,
the only thing left is to drop a Qdrant API key in the env file.

### Procedure (assuming R-06's compose has been applied)

```bash
# 1. Generate API key and append to ai-stack/.env (mode 600)
( umask 077 && \
  printf 'QDRANT__SERVICE__API_KEY=%s\n' "$(openssl rand -hex 32)" \
  >> /home/diego/homelab/ai-stack/.env )

# 2. Recreate qdrant and openwebui so they pick the new env up.
#    OpenWebUI also needs the matching client key:
( umask 077 && \
  echo "QDRANT_API_KEY=$(grep '^QDRANT__SERVICE__API_KEY=' /home/diego/homelab/ai-stack/.env | cut -d= -f2)" \
  >> /home/diego/homelab/ai-stack/.env )

cd /home/diego/homelab/ai-stack
docker compose up -d --force-recreate qdrant openwebui
```

### Procedure (no compose yet — quick fix)

If you can't do R-14/R-06 right now and just want the ports rebound:

```bash
# Capture full inspect first (writes JSON next to the audit folder)
docker inspect ollama qdrant > ~/server-audit-2026-06-13/inspect-ollama-qdrant-pre.json

# Stop, remove, restart with the new -p binding
docker stop ollama && docker rm ollama
docker run -d \
  --name ollama \
  --restart unless-stopped \
  --network ai-local_default \
  -p 127.0.0.1:11434:11434 \
  -e OLLAMA_HOST=0.0.0.0:11434 \
  -v /srv/homelab/data/ollama:/root/.ollama \
  ollama/ollama:latest

docker stop qdrant && docker rm qdrant
docker run -d \
  --name qdrant \
  --restart unless-stopped \
  --network ai-local_default \
  -p 127.0.0.1:6333:6333 \
  -v /home/diego/homelab/ai-stack/data/qdrant:/qdrant/storage \
  qdrant/qdrant:latest
```

### Validation

```bash
# Listening sockets
ss -tlnp | grep -E ':(11434|6333)'
# Expect: both lines show 127.0.0.1, NOT 0.0.0.0

# From LAN: should refuse (run from another device)
# curl --connect-timeout 3 http://192.168.178.79:11434/api/version  # refused

# Open WebUI ↔ Ollama / Qdrant should still work
docker exec openwebui sh -c 'wget -qO- http://ollama:11434/api/version'
docker exec openwebui sh -c 'wget -qO- http://qdrant:6333/ | head -c 80'

# (If you set the API key) Qdrant unauthenticated request should now 401
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:6333/collections
# Expect: 401
curl -s -H "api-key: <KEY>" http://127.0.0.1:6333/collections | head -c 80
# Expect: 200 JSON
```

### Rollback

```bash
# Re-publish on 0.0.0.0
docker stop ollama qdrant && docker rm ollama qdrant
# rerun the original docker run commands with `-p 11434:11434` / `-p 6333:6333`
```

---

### Phase 0 application (2026-06-13)

#### Scope applied

| Sub-item | Status | Notes |
|----------|--------|-------|
| Qdrant `QDRANT__SERVICE__API_KEY` set | ✅ | 64-hex random; stored at `/home/diego/homelab/ai-stack/.env` (`0600`) |
| Open WebUI sends `QDRANT_API_KEY` on every request | ✅ | Env-var injected on recreate |
| Qdrant published port bound to `127.0.0.1` | ⏭ deferred | Will fold in with R-14 / Phase 3 |
| Ollama touched at all | ⏭ deferred | Untouched in Phase 0 |

#### What changed

- **New file:** `/home/diego/homelab/ai-stack/.env`, mode `0600
  diego:diego`, two entries:

  ```
  QDRANT__SERVICE__API_KEY=<64 hex>
  QDRANT_API_KEY=<same 64 hex>
  ```

  First line is the server-side variable Qdrant reads at startup.
  Second mirrors the value under the client-side variable name Open
  WebUI reads. Both point at the same secret.

- **`qdrant` container recreated** (image unchanged):

  ```
  docker run -d \
    --name qdrant --restart unless-stopped \
    --network ai-local_default \
    -p 6333:6333 \
    -v /home/diego/homelab/ai-stack/data/qdrant:/qdrant/storage:rw \
    -e QDRANT__SERVICE__API_KEY="$KEY" \
    qdrant/qdrant:latest
  ```

  The old container was renamed `qdrant_legacy_2026-06-13`, kept until
  validation passed, then `docker rm`'d.

- **`openwebui` container recreated** with the full original env-set
  *plus* `QDRANT_API_KEY=$KEY`. Networks restored: `ai-local_default`
  + `proxy_default`. Mounts unchanged including
  `/var/run/docker.sock` (that's R-06's job, not R-07's). Healthcheck
  is inherited from the image (`curl … /health | jq -ne 'input.status
  == true'`).

  Pre/post container snapshots are saved as
  `phase2-remediation/inspect-snapshots/{qdrant,openwebui}-pre-r07.json`.

#### Validation (2026-06-13 18:48 UTC)

| Probe | Expected | Result |
|-------|----------|--------|
| `curl http://127.0.0.1:6333/collections` (no key) | 401 | ✅ 401 |
| `curl -H 'api-key: $KEY' http://127.0.0.1:6333/collections` | 200, both collections | ✅ 200, `open-webui_files` + `open-webui_knowledge` |
| `docker exec openwebui curl http://qdrant:6333/collections` (no key) | 401 | ✅ 401 |
| `docker exec openwebui curl -H 'api-key: $QDRANT_API_KEY' http://qdrant:6333/collections` | 200 | ✅ 200, key picked up from env |
| `docker exec openwebui curl http://ollama:11434/api/version` | 0.17.7 | ✅ 0.17.7 |
| `curl http://127.0.0.1:3000/api/config` | Open WebUI healthy | ✅ name=Open WebUI, version=0.8.10, auth=true |
| Container health | both up, openwebui healthy | ✅ openwebui Up 47s (healthy), qdrant Up 1m |

#### Follow-ups generated by this round

- **Qdrant ports still on `0.0.0.0:6333`.** Anyone on LAN/tailnet can
  still *probe* (they'll get 401 instead of data, which closes the
  exfiltration leg, but the API surface is still reachable). The full
  R-07 description above ends this with `-p 127.0.0.1:6333` — defer
  until Phase 3 / R-14 to avoid a second recreate of the same
  container in the same week.
- **Ollama still on `0.0.0.0:11434` with no auth.** Same defer.
- **Open WebUI sessions invalidated.** The recreate generated a new
  `WEBUI_SECRET_KEY` from `.webui_secret_key` (the per-disk fallback)
  because the env var was passed as empty. R-05 (next Phase 0 step)
  will pin a stable key and finish this part for good.

---

## R-12 — Stand up nightly backups to the local HDD

**Risk M (host has crashed once already) · Impact H · Time 2 h · Priority 🟠 High**

### Current state

- `/srv/homelab/backups`, `/mnt/storage/backups`: both empty since
  creation.
- No backup binary installed.
- No cron / systemd timer doing snapshots.
- HA recorder DB, Zigbee2MQTT pair database, NPM config, Open WebUI
  chats/users are all single-copy on the NVMe.

### Target state

- `restic` installed.
- Nightly backup at 03:00 to `/mnt/storage/backups/restic` covering all
  workload bind-mounts.
- SQLite databases snapshotted via `sqlite3 .backup` before restic runs
  (avoids WAL corruption).
- 7 daily / 4 weekly / 6 monthly retention.
- Log written to `/var/log/homelab-backup.log`, rotated by `logrotate`.

This **does not** add off-site backups (e.g. S3, second tailnet host).
Treat this as Phase 1 of the backup story.

### Procedure

```bash
# 1. Install restic + sqlite3
sudo apt update
sudo apt install -y restic sqlite3

# 2. Generate a repository passphrase and store it 0600 (root)
sudo mkdir -p /etc/restic
( umask 077 && openssl rand -hex 32 | sudo tee /etc/restic/passwd-homelab > /dev/null )
sudo chmod 600 /etc/restic/passwd-homelab
sudo chown root:root /etc/restic/passwd-homelab

# 3. Initialise the restic repo on the HDD
sudo RESTIC_PASSWORD_FILE=/etc/restic/passwd-homelab \
     restic init --repo /mnt/storage/backups/restic
```

### File — `/usr/local/bin/homelab-backup.sh` (new, mode 0755 root:root)

```bash
#!/usr/bin/env bash
# /usr/local/bin/homelab-backup.sh
# Nightly homelab backup. Idempotent; safe to re-run by hand.
set -euo pipefail

export RESTIC_REPOSITORY=/mnt/storage/backups/restic
export RESTIC_PASSWORD_FILE=/etc/restic/passwd-homelab

SNAP_DIR=/tmp/homelab-backup-snapshots/$(date +%F)
mkdir -p "$SNAP_DIR"
trap 'rm -rf "$SNAP_DIR"' EXIT

# SQLite databases need a consistent snapshot (sqlite3 .backup respects
# the WAL and produces a clean copy).
sqlite3 /srv/homelab/data/openwebui/webui.db ".backup '$SNAP_DIR/openwebui-webui.db'"
sqlite3 /srv/homelab/homeassistant/home-assistant_v2.db ".backup '$SNAP_DIR/homeassistant.db'"
sqlite3 /srv/homelab/data/npm/database.sqlite ".backup '$SNAP_DIR/npm.sqlite'"

restic backup \
  --tag nightly \
  --exclude '/srv/homelab/data/openwebui/cache/**' \
  /srv/homelab/data/openwebui \
  /srv/homelab/homeassistant \
  /srv/homelab/data/npm \
  /home/diego/homelab/ai-stack/data/qdrant \
  /home/diego/homelab/03_services/zigbee-stack/zigbee2mqtt/data \
  /home/diego/homelab/03_services/zigbee-stack/mosquitto/data \
  /home/diego/webs \
  /etc/systemd/system/homelab-tools.service \
  /etc/apache2/sites-enabled \
  /etc/samba/smb.conf \
  "$SNAP_DIR"

restic forget \
  --tag nightly \
  --keep-daily 7 \
  --keep-weekly 4 \
  --keep-monthly 6 \
  --prune
```

### File — `/etc/cron.d/homelab-backup` (new, mode 0644 root:root)

```
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Nightly homelab backup
0 3 * * * root /usr/local/bin/homelab-backup.sh >> /var/log/homelab-backup.log 2>&1
```

### File — `/etc/logrotate.d/homelab-backup` (new, mode 0644 root:root)

```
/var/log/homelab-backup.log {
    weekly
    rotate 8
    compress
    missingok
    notifempty
    create 0640 root adm
}
```

### Install commands

```bash
sudo install -m 0755 -o root -g root \
  /dev/stdin /usr/local/bin/homelab-backup.sh <<'SH'
<paste the script body from above here>
SH

sudo install -m 0644 -o root -g root \
  /dev/stdin /etc/cron.d/homelab-backup <<'CRON'
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
0 3 * * * root /usr/local/bin/homelab-backup.sh >> /var/log/homelab-backup.log 2>&1
CRON

sudo install -m 0644 -o root -g root \
  /dev/stdin /etc/logrotate.d/homelab-backup <<'LR'
/var/log/homelab-backup.log {
    weekly
    rotate 8
    compress
    missingok
    notifempty
    create 0640 root adm
}
LR
```

### Validation

```bash
# 1. Run once on-demand and time it (~few minutes for first run)
sudo /usr/local/bin/homelab-backup.sh
tail -50 /var/log/homelab-backup.log

# 2. Confirm snapshot
sudo RESTIC_PASSWORD_FILE=/etc/restic/passwd-homelab \
     restic -r /mnt/storage/backups/restic snapshots

# 3. Spot-restore one file from the snapshot to /tmp/restore-test
sudo RESTIC_PASSWORD_FILE=/etc/restic/passwd-homelab \
     restic -r /mnt/storage/backups/restic restore latest \
     --include /srv/homelab/data/npm/database.sqlite \
     --target /tmp/restore-test
ls -lh /tmp/restore-test/srv/homelab/data/npm/database.sqlite

# 4. Disk pressure check on /mnt/storage
df -h /mnt/storage
```

### Rollback / removal

```bash
sudo rm /etc/cron.d/homelab-backup \
        /etc/logrotate.d/homelab-backup \
        /usr/local/bin/homelab-backup.sh
# Optional: keep the repo on disk for cold restore
# sudo rm -rf /mnt/storage/backups/restic
```

### Follow-up (off-site copy)

Once the local backup has been observed running for ~1 week, mirror it to
a second target:

- A second restic repo on another tailnet host (`sftp:diego@diego:/…`).
- Or `rclone serve restic` against B2 / S3 / Backblaze.

This is the gap that turns a single-disk backup into something that
survives a physical incident.
