# 01 — Critical fixes (do today)

Four findings. Total time ~50 minutes (excluding the Cloudflare UI work for R-01).

---

## R-01 — Rotate and segregate the Cloudflare tunnel token

**Risk M · Impact H · Time 30 m (incl. Cloudflare UI) · Priority 🔴 Critical**

### Current state

`/home/diego/webs/cloudflared/docker-compose.yml` contains
`TUNNEL_TOKEN=<REDACTED>` inline. The directory is **not** a git repo today
(verified with `git rev-parse`), so the token is "only" at-rest on the host
file system, but:

- The file is mode `0664`, world-readable.
- `/home/diego/homelab/` *is* git-tracked, and similar patterns risk
  spreading.
- The token decodes to `{accountTag, tunnelID, tunnelSecret}` — anyone with
  it owns the tunnel and can re-publish it pointing anywhere.

### Target state

- Token lives in `/home/diego/webs/cloudflared/.env`, mode `0600`,
  not committed to git.
- Compose file references `env_file: .env`.
- The *value* in `.env` is a **new** token issued by Cloudflare; the old
  one in the compose file is revoked.

### Procedure

```bash
# Step 1 — capture the running container's token to .env (without exposing
# it in shell history). umask 077 ensures the file is created 0600.
( umask 077 && \
  docker inspect cloudflared --format '{{range .Config.Env}}{{println .}}{{end}}' \
  | grep '^TUNNEL_TOKEN=' \
  > /home/diego/webs/cloudflared/.env )
chmod 600 /home/diego/webs/cloudflared/.env
ls -la /home/diego/webs/cloudflared/.env
# Expect: -rw------- 1 diego diego ... .env

# Step 2 — add .gitignore so this dir can safely be initialised as git later
cat > /home/diego/webs/cloudflared/.gitignore <<'EOF'
.env
EOF

# Step 3 — apply the compose diff (see below)
# (use your editor; the diff is small)

# Step 4 — rotate the token in Cloudflare:
#   https://one.dash.cloudflare.com/
#   → Networks → Tunnels → <your tunnel>
#   → Configure → Refresh token (or Public Hostname → Edit → rotate)
# Cloudflare returns a *new* TUNNEL_TOKEN string.

# Step 5 — replace the value in .env with the new token, keeping 0600
( umask 077 && printf 'TUNNEL_TOKEN=%s\n' '<NEW-TOKEN-FROM-CLOUDFLARE>' \
  > /home/diego/webs/cloudflared/.env )

# Step 6 — recreate the container with the new env_file
cd /home/diego/webs/cloudflared
docker compose up -d --force-recreate
```

### Diff — `/home/diego/webs/cloudflared/docker-compose.yml`

```diff
 services:
   cloudflared:
     image: cloudflare/cloudflared:latest
     container_name: cloudflared
     restart: unless-stopped
     command: tunnel --no-autoupdate --protocol http2 run
-    environment:
-      - TUNNEL_TOKEN=<REDACTED-CLOUDFLARE-TUNNEL-TOKEN>
+    env_file:
+      - .env
     networks:
       - cloudflare-net

 networks:
   cloudflare-net:
     external: true
```

### Validation

```bash
# Container should be Up
docker ps --filter name=cloudflared --format '{{.Names}} {{.Status}}'

# Tunnel should be HEALTHY in the Cloudflare dashboard
# CLI alternative: tail the logs for "Registered tunnel connection"
docker logs --tail 50 cloudflared | grep -i 'connection\|registered'

# Confirm the compose file no longer contains the secret
grep -c TUNNEL_TOKEN /home/diego/webs/cloudflared/docker-compose.yml
# Expect: 0
```

### Rollback

If the new token fails (e.g. mistyped), put the old value back in `.env`
and `docker compose up -d --force-recreate`. The old token works until
you explicitly revoke it in the dashboard. (Revoke only after the new one
is confirmed healthy.)

---

## R-02 — Bind `homelab-tools` Flask API to `127.0.0.1`

**Risk H · Impact H · Time 5 m · Priority 🔴 Critical**

### Current state

`homelab-tools.service` runs `/home/diego/homelab/ai-tools/docker_status.py`
which calls `app.run(host="0.0.0.0", port=5050)`. Anyone on LAN or tailnet
can hit `/docker/containers` and `/docker/logs?container=<name>` without
auth. Container logs commonly contain session tokens, recorder snapshots,
chat content, etc.

### Target state

Two equivalent fixes; pick one. **Option A** keeps the local dashboard
functional. **Option B** disables the service entirely (Portainer already
exposes the same data, gated by login).

### Procedure — Option A: bind to localhost

```bash
sed -i 's|app.run(host="0.0.0.0"|app.run(host="127.0.0.1"|' \
  /home/diego/homelab/ai-tools/docker_status.py
sudo systemctl restart homelab-tools
```

### Diff — `/home/diego/homelab/ai-tools/docker_status.py`

```diff
-app.run(host="0.0.0.0", port=5050)
+app.run(host="127.0.0.1", port=5050)
```

### Procedure — Option B: disable the service

```bash
sudo systemctl disable --now homelab-tools.service
```

(No diff; the unit file stays at `/etc/systemd/system/homelab-tools.service`
in case you want to re-enable later.)

### Validation

```bash
# Should now bind 127.0.0.1 only (Option A) or be absent entirely (Option B)
ss -tlnp | grep ':5050'

# From host: still works
curl -fsS http://127.0.0.1:5050/docker/containers && echo OK

# From LAN: should refuse (test from another device on 192.168.178.0/24)
# curl --connect-timeout 3 http://192.168.178.79:5050/docker/containers
# Expect: connection refused or timeout
```

### Rollback

```bash
# Option A → 0.0.0.0
sed -i 's|app.run(host="127.0.0.1"|app.run(host="0.0.0.0"|' \
  /home/diego/homelab/ai-tools/docker_status.py
sudo systemctl restart homelab-tools

# Option B → re-enable
sudo systemctl enable --now homelab-tools.service
```

---

## R-03 — Lock down NPM key + database mode

**Risk M · Impact H · Time 2 m · Priority 🔴 Critical**

### Current state

```
stat -c '%a %U:%G %n' /srv/homelab/data/npm/keys.json /srv/homelab/data/npm/database.sqlite
644 root:root /srv/homelab/data/npm/keys.json
644 root:root /srv/homelab/data/npm/database.sqlite
```

`keys.json` holds NPM's RSA-2048 keypair used to sign admin JWTs. World-
readable mode means any non-root host user (or any container that mounts
the path) can forge admin sessions.

### Target state

```
600 root:root /srv/homelab/data/npm/keys.json
600 root:root /srv/homelab/data/npm/database.sqlite
```

NPM's container runs as root inside the container and bind-mounts the host
directory, so `0600 root:root` on the host remains read/write inside the
container.

### Procedure

```bash
sudo chmod 600 /srv/homelab/data/npm/keys.json
sudo chmod 600 /srv/homelab/data/npm/database.sqlite

# Restart NPM so we catch any open-file regressions immediately
docker restart nginx-proxy-manager
```

### Validation

```bash
stat -c '%a %U:%G %n' \
  /srv/homelab/data/npm/keys.json \
  /srv/homelab/data/npm/database.sqlite
# Expect: 600 root:root for both

# NPM UI on http://homelab:81 should still log in
docker logs --tail 50 nginx-proxy-manager | grep -i 'error' || echo 'no errors'
```

### Rollback

```bash
sudo chmod 644 /srv/homelab/data/npm/keys.json
sudo chmod 644 /srv/homelab/data/npm/database.sqlite
docker restart nginx-proxy-manager
```

---

## R-04 — Restore Mosquitto config and fix Zigbee2MQTT broker hostname  ✅ APPLIED 2026-06-13

**Risk H (already broken) · Impact M · Time 15 m · Priority 🔴 Critical**

> **Status:** Applied 2026-06-13. Crash loop resolved. End-to-end MQTT
> round-trip validated (CONNECT/CONNACK/PUBLISH from a fresh
> `mosquitto_pub` probe container on `zigbee-stack_default` was accepted
> and logged by the broker). See the [Phase 0 application log](#phase-0-application-2026-06-13)
> at the end of this section.

### Current state (pre-fix snapshot — kept for history)

```
mosquitto: Unable to open config file '/mosquitto/config/mosquitto.conf'
```

The bind-mount directory exists but is empty. Zigbee2MQTT's
`configuration.yaml` points at `mqtt://localhost:1883`, which inside a
container resolves to *itself* — even when mosquitto is fixed, the broker
hostname is wrong because mosquitto and zigbee2mqtt live in *different*
containers on the same Docker network.

### Target state

1. Mosquitto config restored — anonymous listener on `:1883`, persistence
   on, logs on. (Matches the documented "fase de validación local"
   posture. Auth hardening is a follow-up below.)
2. Zigbee2MQTT points at `mqtt://mosquitto:1883`.
3. Both containers running cleanly with no restart loop.

### Procedure

```bash
# Step 1 — restore the minimal mosquitto.conf
sudo tee /home/diego/homelab/03_services/zigbee-stack/mosquitto/config/mosquitto.conf > /dev/null <<'EOF'
# Bare minimum to stop the restart loop. Tighten with passwd_file +
# allow_anonymous false once a user/password is provisioned.

persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/log/mosquitto.log
log_dest stdout

listener 1883 0.0.0.0
allow_anonymous true
EOF
sudo chown root:root /home/diego/homelab/03_services/zigbee-stack/mosquitto/config/mosquitto.conf
sudo chmod 644 /home/diego/homelab/03_services/zigbee-stack/mosquitto/config/mosquitto.conf

# Step 2 — point zigbee2mqtt at the broker by name (see diff below)

# Step 3 — restart both containers
docker restart mosquitto
docker restart zigbee2mqtt
```

### Diff — `/home/diego/homelab/03_services/zigbee-stack/zigbee2mqtt/data/configuration.yaml`

```diff
 version: 5
 mqtt:
   base_topic: zigbee2mqtt
-  server: mqtt://localhost:1883
+  server: mqtt://mosquitto:1883
 serial: {}
 advanced:
   log_level: info
```

### Validation

```bash
# Mosquitto should stay Up, not Restarting
docker ps --filter name=mosquitto --format '{{.Names}} {{.Status}}'
# Expect: mosquitto  Up <N> minutes  (no "Restarting")

# Mosquitto log should not show the config-file error any more
docker logs --tail 30 mosquitto

# Zigbee2MQTT should report a successful MQTT connection
docker logs --tail 60 zigbee2mqtt | grep -iE 'mqtt|connect'
# Expect: "Connected to MQTT server" (or similar)
```

### Follow-up (recommended, ~30 minutes)

Switch off anonymous access once the broker is stable:

```bash
# Inside the container, create a passwd file
docker exec -it mosquitto mosquitto_passwd -c /mosquitto/config/passwd zigbee2mqtt
# (Set a password; this writes /mosquitto/config/passwd)

# Edit mosquitto.conf
#   allow_anonymous false
#   password_file /mosquitto/config/passwd

# Update zigbee2mqtt configuration.yaml
#   mqtt:
#     server: mqtt://mosquitto:1883
#     user: zigbee2mqtt
#     password: '...'

docker restart mosquitto zigbee2mqtt
```

### Rollback

```bash
# Remove the config and revert zigbee2mqtt's server line if the new state
# breaks something downstream.
sudo rm /home/diego/homelab/03_services/zigbee-stack/mosquitto/config/mosquitto.conf
# (Container will return to its restart loop, which is the prior state.)

# Revert configuration.yaml server line
sed -i 's|server: mqtt://mosquitto:1883|server: mqtt://localhost:1883|' \
  /home/diego/homelab/03_services/zigbee-stack/zigbee2mqtt/data/configuration.yaml
docker restart zigbee2mqtt
```

---

### Phase 0 application (2026-06-13)

#### What was installed / changed

| Path | Change | Mode / owner |
|------|--------|--------------|
| `…/zigbee-stack/mosquitto/config/mosquitto.conf` | **created** — anon listener on `1883`, persistence to `/mosquitto/data/`, dual log dest (file + stdout) | `0644 root:root` |
| `…/zigbee-stack/mosquitto/log/` | **chowned to `1883:1883`** so mosquitto can write its log file | `drwxr-xr-x 1883:1883` |
| `…/zigbee-stack/zigbee2mqtt/data/configuration.yaml` | `server: mqtt://localhost:1883` → `mqtt://mosquitto:1883` | `0644 root:root` |
| `mosquitto` container | restarted via `docker restart mosquitto` | runtime change |
| `zigbee2mqtt` container | restarted via `docker restart zigbee2mqtt` | runtime change |

#### Validation results (2026-06-13 18:43 UTC)

```
mosquitto       Up 9 seconds
zigbee2mqtt     Up 6 seconds   (then steady)
```

Mosquitto log on first clean start:

```
Config loaded from /mosquitto/config/mosquitto.conf.
Bridge support available.
Persistence support available.
TLS support available.
TLS-PSK support available.
Websockets support available.
Opening ipv4 listen socket on port 1883.
mosquitto version 2.1.2 running
```

End-to-end MQTT round trip (probe from a fresh `mosquitto_pub` container
on `zigbee-stack_default`):

```
Client (null) received CONNACK (0)
Client null sending PUBLISH (d0, q0, r0, m1, 'homelab/audit', ... (9 bytes))
Client null sending DISCONNECT
```

Broker side observed the connection:

```
New connection from 172.20.0.4:50194 on port 1883.
New client connected from 172.20.0.4:50194 as auto-51D69137-… (p4, c1, k60).
Client … disconnected.
```

DNS resolution from inside `zigbee2mqtt`:

```
172.20.0.2        mosquitto  mosquitto
```

#### Side note — second issue discovered and fixed mid-deployment

After the initial `mosquitto.conf` install the broker still failed with
`Unable to open log file /mosquitto/log/mosquitto.log for writing`
because the host-side log directory was owned `root:root` while the
mosquitto user inside the container is uid `1883`. The same shape that
the existing `data/` dir already had (`1883:1883`). One extra `chown -R
1883:1883 …/log` resolved it; documented above as part of the install.

#### Out-of-scope observations (not part of R-04)

- `zigbee2mqtt` is in **onboarding mode** (`onboarding: true` in its
  `configuration.yaml`). Until you complete the onboarding wizard at
  `http://homelab:8080/`, the koenkk entrypoint script keeps the
  container alive but z2m itself does not attempt the actual MQTT
  connect. R-04 fixed the broker and the broker hostname; it did not
  finish the z2m setup. The connection path is now ready for whenever
  you do.
- `mosquitto` accepts **anonymous** connections, matching the
  "validación local" posture documented in
  `03_services/zigbee2mqtt_setup.md`. Hardening this to a password-file
  setup is a follow-up; the procedure is in this file under "Follow-up
  (recommended)".
