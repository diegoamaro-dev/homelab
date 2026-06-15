# 03 — Medium priority fixes (this month)

Seven findings. Most are 5-minute hygiene fixes; R-10 (UFW) and R-14
(compose files) are the largest at 30 minutes / 2–4 hours.

---

## R-05 — Pin a non-empty `WEBUI_SECRET_KEY`  ✅ APPLIED 2026-06-13

**Risk L · Impact M · Time 15 m · Priority 🟡 Medium**

> **Status:** Applied 2026-06-13 as Phase 0 step 4. Secret value lives in
> `/home/diego/homelab/ai-stack/.env` (`0600 diego:diego`) and is
> injected via `-e WEBUI_SECRET_KEY=…` on the `openwebui` `docker run`.
> Verified stable across a `docker restart` (sha256 of the value
> identical before and after). See the [Phase 0 application log](#phase-0-application-2026-06-13).

### Current state

```
docker inspect openwebui --format '{{range .Config.Env}}{{println .}}{{end}}' | grep SECRET
WEBUI_SECRET_KEY=
```

Open WebUI generates a random key at boot when the env var is empty,
which is lost on every container restart. JWT-backed sessions and
user-created API keys are invalidated each time the image is pulled.

### Target state

Stable 64-hex-char value set via env_file in the compose file from R-06.

### Procedure

```bash
# 1. Append to /home/diego/homelab/ai-stack/.env (created in R-06)
( umask 077 && \
  printf 'WEBUI_SECRET_KEY=%s\n' "$(openssl rand -hex 32)" \
  >> /home/diego/homelab/ai-stack/.env )

# 2. Recreate openwebui to load the new env
cd /home/diego/homelab/ai-stack
docker compose up -d --force-recreate openwebui
```

### Validation

```bash
docker exec openwebui printenv WEBUI_SECRET_KEY | wc -c
# Expect: 65  (64 hex chars + newline)

# Restart and verify sessions persist
docker restart openwebui
# Log into the UI, refresh — your session must survive a restart.
```

### Rollback

Remove the `WEBUI_SECRET_KEY=` line from `.env` and recreate.

---

### Phase 0 application (2026-06-13)

#### What changed

- **`/home/diego/homelab/ai-stack/.env`** gained a third line
  `WEBUI_SECRET_KEY=<64 hex>`. File mode kept at `0600`.
- **`openwebui` container recreated** (same shape as the R-07 recreate
  one step earlier) with `WEBUI_SECRET_KEY="$KEY_WEBUI"` populated
  instead of empty. Networks `ai-local_default` + `proxy_default`
  preserved; mounts unchanged. Image untouched.

#### Validation (2026-06-13 18:51 UTC)

| Probe | Expected | Result |
|-------|----------|--------|
| `docker exec openwebui printenv WEBUI_SECRET_KEY \| wc -c` | 65 (64 hex + newline) | ✅ 65 |
| `sha256` of secret captured **before** `docker restart openwebui` | recorded | ✅ `f184e557…d1a717` |
| `sha256` of secret captured **after** `docker restart openwebui` | identical to before — proves env source, not on-disk fallback | ✅ identical |
| Boot log search for `Generating WEBUI_SECRET_KEY` or `Loading … from .webui_secret_key` | absent | ✅ absent |
| Open WebUI ↔ Qdrant (`api-key` from env) | 200 | ✅ 200 |
| Open WebUI ↔ Ollama | 200 + `{"version":"0.17.7"}` | ✅ |
| `GET /api/config` | `status=True`, `auth=True`, version 0.8.10 | ✅ |

#### What this fixes for the user

- Sessions, cookies, and any API keys created in the Open WebUI UI
  now **survive** `docker restart` and future image upgrades.
- Eliminates the "everyone logged out after every restart" pattern.

#### Out-of-scope observations

- `.webui_secret_key` file on disk inside the bind-mount still exists
  from previous runs. It's now ignored by Open WebUI (env var wins).
  Safe to leave for now; if you ever roll back R-05, that file becomes
  the source of truth again.
- The recreated container generated a new internal session-signing key
  *once* (when R-07 ran). Anyone who was logged in before 2026-06-13
  ~18:48 will have been logged out at that point. From here forward,
  the secret is stable.

---

## R-08 — Disable the WebDAV vhost (or front it with TLS)

**Risk L · Impact M · Time 5 m (disable) / ~1 h (TLS) · Priority 🟡 Medium**

### Current state

`/etc/apache2/sites-enabled/webdav.conf` exposes `webdav.local:8088` over
plain HTTP with Basic auth (single user in `/etc/apache2/webdav.passwd`).
Credentials traverse LAN/tailnet in clear text.

### Procedure — Option A: disable (if unused)

```bash
# Inspect what's behind it first
sudo ls -la /var/www/webdav/

# If empty / unused
sudo a2dissite webdav
sudo systemctl reload apache2
```

### Procedure — Option B: keep, behind NPM + Let's Encrypt

Outside the scope of a plain remediation file; create a new proxy host in
NPM (UI on http://homelab:81) pointing at `http://homelab:8088`, attach
the LE cert, and *additionally* lock down the vhost to listen only on
loopback:

```diff
-<VirtualHost *:8088>
+<VirtualHost 127.0.0.1:8088>
   ServerName webdav.local
```

…plus update `/etc/apache2/ports.conf`:

```diff
-Listen 8088
+Listen 127.0.0.1:8088
```

```bash
sudo systemctl reload apache2
```

### Validation

```bash
# Option A
ss -tlnp | grep 8088   # expect: no output
# Option B
ss -tlnp | grep 8088   # expect: 127.0.0.1:8088 only
# https://webdav.<your domain> via NPM should now respond
```

### Rollback

```bash
sudo a2ensite webdav
sudo systemctl reload apache2
```

---

## R-09 — Disable `rpcbind` (no NFS in use)

**Risk L · Impact L · Time 2 m · Priority 🟡 Medium**

### Current state

`rpcinfo -p` registers only `portmapper` itself — no `nfs`, no `mountd`.
The service exposes TCP/UDP 111 on `0.0.0.0` for no functional purpose.

### Procedure

```bash
sudo systemctl disable --now rpcbind.service rpcbind.socket

# Confirm nothing else pulls it in transitively
apt-cache rdepends --installed rpcbind 2>/dev/null | tail -20

# If only nfs-common is listed and you don't NFS-mount anything,
# purge them both:
sudo apt purge -y rpcbind nfs-common
```

### Validation

```bash
ss -tlnp | grep ':111 '
# Expect: no output
ss -ulnp | grep ':111 '
# Expect: no output
systemctl is-active rpcbind.service rpcbind.socket
# Expect: inactive / inactive
```

### Rollback

```bash
sudo systemctl enable --now rpcbind.service rpcbind.socket
# (or re-install: sudo apt install -y rpcbind nfs-common)
```

---

## R-10 — Enable UFW with a default-deny inbound policy

**Risk L · Impact M · Time 30 m · Priority 🟡 Medium**

### Current state

UFW is installed (`ufw 0.36.2`) but inactive. The host relies entirely on
the home router's "no inbound forwarding" stance plus the tailnet ACL.
Defense in depth recommends a local firewall too.

### Target state

| Source | Destination | Action |
|--------|-------------|--------|
| Tailnet (`tailscale0` in) | any | ALLOW |
| `192.168.178.0/24` | 22/tcp (SSH) | ALLOW |
| `192.168.178.0/24` | 80, 81, 443/tcp (NPM) | ALLOW |
| `192.168.178.0/24` | 3000/tcp (Open WebUI) | ALLOW |
| `192.168.178.0/24` | 8123/tcp (Home Assistant) | ALLOW |
| `192.168.178.0/24` | 137, 138/udp + 139, 445/tcp (Samba) | ALLOW |
| `192.168.178.0/24` | 8080/tcp (zigbee2mqtt UI) | ALLOW (if you use it) |
| Anywhere else inbound | any | DENY |
| Loopback | any | ALLOW (default) |
| All outbound | any | ALLOW |

### Procedure

> Run these in a **screen / tmux session over the LAN**. Do *not* enable
> over an SSH session that could be cut by your own rules; the SSH allow
> below is the first command so you should be safe, but caution is cheap.

```bash
# Reset (idempotent if you re-run later)
sudo ufw --force reset

# Defaults
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Tailscale: trust everything coming in over the tailnet interface
sudo ufw allow in on tailscale0

# SSH from LAN
sudo ufw allow from 192.168.178.0/24 to any port 22 proto tcp comment 'ssh-lan'

# Reverse proxy
sudo ufw allow from 192.168.178.0/24 to any port 80,443 proto tcp comment 'npm-http'
sudo ufw allow from 192.168.178.0/24 to any port 81    proto tcp comment 'npm-admin'

# Apps reachable from the LAN
sudo ufw allow from 192.168.178.0/24 to any port 3000  proto tcp comment 'openwebui'
sudo ufw allow from 192.168.178.0/24 to any port 8123  proto tcp comment 'homeassistant'
sudo ufw allow from 192.168.178.0/24 to any port 8080  proto tcp comment 'zigbee2mqtt'

# Samba (LAN only)
sudo ufw allow from 192.168.178.0/24 to any port 139,445 proto tcp comment 'samba'
sudo ufw allow from 192.168.178.0/24 to any port 137,138 proto udp comment 'samba-browse'

# Optional: tighten further by removing 8080 if you only use NPM
# Optional: 9443 / 8000 (Portainer) — leave deny unless you regularly hit it from LAN

sudo ufw enable
sudo ufw status verbose
```

### Validation

```bash
# From the host
sudo ufw status numbered

# From a LAN device (192.168.178.x)
# curl -fsI http://192.168.178.79:3000/ | head -1   # should succeed
# curl --connect-timeout 3 http://192.168.178.79:5050/   # should fail (R-02 fixed)
# curl --connect-timeout 3 http://192.168.178.79:11434/  # should fail (R-07 fixed)

# From a tailnet device
# All allowed services reachable via the tailnet IP (100.68.180.69)
```

### Rollback

```bash
sudo ufw disable
sudo ufw --force reset
```

---

## R-11 — Catch up on container image updates

**Risk M · Impact M · Time 30 m (pull) + per-stack verify · Priority 🟡 Medium**

### Current state

| Image | Last pull | Stack |
|-------|-----------|-------|
| `ghcr.io/home-assistant/home-assistant:stable` | 2026-03-06 | homeassistant |
| `ollama/ollama:latest` | 2026-03-06 | ai-stack |
| `ghcr.io/open-webui/open-webui:main` | 2026-03-09 | ai-stack |
| `cloudflare/cloudflared:latest` | 2026-03-09 | cloudflared |
| `eclipse-mosquitto:2` | 2026-02-09 | zigbee-stack |
| `koenkk/zigbee2mqtt:latest` | 2026-03-02 | zigbee-stack |
| `qdrant/qdrant:latest` | 2026-02-19 | ai-stack |
| `portainer/portainer-ce:latest` | 2026-02-25 | portainer |
| `jc21/nginx-proxy-manager:latest` | 2026-02-17 | npm |
| `nginx:alpine` | 2026-04-15 | guardian-web |

### Procedure

Run **after** R-12 (backups) is healthy and R-14 (compose files) has
captured the current state, so you can roll back cleanly.

```bash
# Pull everything
for img in \
  ghcr.io/open-webui/open-webui:main \
  ollama/ollama:latest \
  qdrant/qdrant:latest \
  ghcr.io/home-assistant/home-assistant:stable \
  jc21/nginx-proxy-manager:latest \
  portainer/portainer-ce:latest \
  cloudflare/cloudflared:latest \
  koenkk/zigbee2mqtt:latest \
  eclipse-mosquitto:2 \
  nginx:alpine
do
  echo "==> pulling $img"
  docker pull "$img"
done

# Recreate per stack (each one independently — rollback granularity)
cd /home/diego/homelab/ai-stack            && docker compose up -d
cd /home/diego/homelab/03_services/zigbee-stack && docker compose up -d   # once R-14 lands
cd /home/diego/webs/cloudflared            && docker compose up -d
cd /home/diego/webs/guardian-cloud         && docker compose up -d
# Home Assistant, NPM, Portainer — depends on R-14 progress

# Prune the dangling images
docker image prune -f
```

### Optional — Watchtower for ongoing updates

```bash
docker run -d \
  --name watchtower \
  --restart unless-stopped \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e WATCHTOWER_CLEANUP=true \
  -e WATCHTOWER_SCHEDULE="0 0 4 * * *"  `: '04:00 every day'` \
  -e WATCHTOWER_NOTIFICATIONS=email     `: 'optional'` \
  containrrr/watchtower
```

Trade-off: Watchtower will autoupdate Home Assistant (which sometimes
ships breaking changes). Restrict it to specific containers if you don't
want that:

```bash
# Only auto-update the lower-risk stacks
docker update --label-add com.centurylinklabs.watchtower.enable=true \
  cloudflared qdrant ollama npm guardian-web
# Then run watchtower with: --label-enable
```

### Validation

```bash
# Each container reports the new build / version
docker exec openwebui sh -c 'cat /app/backend/data/version.txt 2>/dev/null || echo n/a'
curl -s http://127.0.0.1:11434/api/version
curl -s http://127.0.0.1:6333/
docker exec homeassistant cat /config/.HA_VERSION

# Watch logs for the first ~30 minutes after each update
docker logs --tail 100 -f openwebui
```

### Rollback

`docker tag` the previous image, edit compose to that tag, recreate. The
backup from R-12 covers the bind-mount data side if a schema change goes
wrong.

---

## R-13 — Drop Apache's default vhost on port 80

**Risk L · Impact L · Time 2 m · Priority 🟡 Medium**

### Current state

`apache2 -S` shows two vhosts active. `000-default.conf` binds `*:80`
but the actual `ServerName` resolves to `127.0.1.1`, so it currently only
serves loopback. NPM owns the public 80. The arrangement is fragile:
adding any other vhost listening on `*:80` would conflict with NPM.

### Procedure

```bash
sudo a2dissite 000-default
sudo systemctl reload apache2
```

### Diff — `apache2ctl -S` before/after

```diff
-*:80   127.0.1.1 (/etc/apache2/sites-enabled/000-default.conf:1)
 *:8088 webdav.local (/etc/apache2/sites-enabled/webdav.conf:1)
```

### Validation

```bash
sudo apache2ctl -S 2>&1 | grep -v '^\s*$' | head -10
# Expect: only the :8088 webdav vhost (or only :8088 → loopback after R-08)

ss -tlnp | grep ':80 '
# Expect: only NPM listening on 0.0.0.0:80
```

### Rollback

```bash
sudo a2ensite 000-default
sudo systemctl reload apache2
```

---

## R-14 — Capture every container as a checked-in compose file

**Risk L (operational) · Impact M (recovery) · Time 2–4 h · Priority 🟡 Medium**

### Current state

Only `cloudflared` and `guardian-web` have compose files. The other eight
containers were started ad-hoc with `docker run`.

### Procedure (per stack)

R-06 and R-12 already produce the compose file for the AI stack. Apply
the same approach to the rest.

```bash
# Suggested folder layout
/srv/homelab/compose/
  ai-stack/docker-compose.yml         # made by R-06 (moved out of ai-tools)
  homeassistant/docker-compose.yml
  npm/docker-compose.yml
  portainer/docker-compose.yml
  zigbee-stack/docker-compose.yml     # mosquitto + zigbee2mqtt
```

For each container, render its current state with `docker inspect` and
adapt by hand:

```bash
docker inspect homeassistant > ~/server-audit-2026-06-13/inspect-homeassistant.json
# Then translate into compose by hand using the file as a reference
```

### Skeleton — `homeassistant/docker-compose.yml`

```yaml
services:
  homeassistant:
    image: ghcr.io/home-assistant/home-assistant:stable
    container_name: homeassistant
    restart: unless-stopped
    network_mode: host
    volumes:
      - /srv/homelab/homeassistant:/config
      - /etc/localtime:/etc/localtime:ro
```

### Skeleton — `npm/docker-compose.yml`

```yaml
services:
  nginx-proxy-manager:
    image: jc21/nginx-proxy-manager:latest
    container_name: nginx-proxy-manager
    restart: unless-stopped
    networks:
      - proxy
    ports:
      - "80:80"
      - "443:443"
      - "81:81"
    volumes:
      - /srv/homelab/data/npm:/data
      - /srv/homelab/data/npm/letsencrypt:/etc/letsencrypt

networks:
  proxy:
    name: proxy_default
    external: true
```

### Skeleton — `portainer/docker-compose.yml`

```yaml
services:
  portainer:
    image: portainer/portainer-ce:latest
    container_name: portainer
    restart: unless-stopped
    networks:
      - default
      - proxy
    ports:
      - "8000:8000"
      - "9443:9443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - portainer_data:/data

volumes:
  portainer_data:

networks:
  proxy:
    name: proxy_default
    external: true
```

### Skeleton — `zigbee-stack/docker-compose.yml`

```yaml
services:
  mosquitto:
    image: eclipse-mosquitto:2
    container_name: mosquitto
    restart: unless-stopped
    networks:
      - zigbee
    volumes:
      - ./mosquitto/config:/mosquitto/config
      - ./mosquitto/data:/mosquitto/data
      - ./mosquitto/log:/mosquitto/log

  zigbee2mqtt:
    image: koenkk/zigbee2mqtt:latest
    container_name: zigbee2mqtt
    restart: unless-stopped
    networks:
      - zigbee
    ports:
      - "8080:8080"
    volumes:
      - ./zigbee2mqtt/data:/app/data
      - /run/udev:/run/udev:ro
    devices:
      - /dev/serial/by-id/usb-ITead_Sonoff_Zigbee_3.0_USB_Dongle_Plus_<REDACTED-DONGLE-SERIAL>-if00-port0:/dev/ttyUSB0

networks:
  zigbee:
    name: zigbee-stack_default
    external: true
```

### Procedure to swap a container over to compose without downtime risk

```bash
# 1. Write the compose file
# 2. Stop and *rename* the existing container (don't remove)
docker stop homeassistant
docker rename homeassistant homeassistant_legacy_2026-06-13
# 3. Bring it up via compose
cd /srv/homelab/compose/homeassistant
docker compose up -d
# 4. Verify, then drop the legacy container
docker rm homeassistant_legacy_2026-06-13
```

### Validation

```bash
# Every stack has a compose file
find /srv/homelab/compose -name docker-compose.yml -type f

# `docker compose ps` per stack reflects the running containers
for d in /srv/homelab/compose/*/; do
  echo "==> $d"
  (cd "$d" && docker compose ps)
done
```

### Rollback

Renaming the legacy container instead of removing it gives a one-step
fallback for each conversion. See the procedure above.
