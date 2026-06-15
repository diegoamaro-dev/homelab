# 06 — Running services (host)

## systemd — high-value units

42 active services on the host. Filtered for the ones that matter to the
homelab workload (everything else is GNOME/desktop or stock Ubuntu plumbing):

| Unit | State | Purpose / notes |
|------|-------|-----------------|
| `docker.service` | active | Docker daemon (Engine 29.4.1) |
| `containerd.service` | active | Container runtime |
| `ssh.service` | active | OpenSSH server on TCP/22 |
| `apache2.service` | active | **Hosts WebDAV vhost on :8088 + default :80 on 127.0.1.1** |
| `smbd.service` + `nmbd.service` | active | Samba — exposes `[projects]` share |
| `snap.tailscale.tailscaled.service` | active | Tailscale (snap-packaged) |
| `pm2-diego.service` | active | PM2 startup for user `diego` (runs `guardian-cloud-backend`) |
| `homelab-tools.service` | active | **Flask dev server on `0.0.0.0:5050` — no auth** |
| `unattended-upgrades.service` | active | Daily APT security updates (host packages only) |
| `cron.service` | active | No user cronjobs; only stock `cron.daily/weekly/monthly` items |
| `rsyslog.service` | active | System log forwarding |
| `systemd-timesyncd.service` | active | NTP client |
| `systemd-resolved.service` | active | Stub resolver listening on 127.0.0.53:53 |
| `bluetooth.service` | active | Bluez (paired peripheral throwing HID errors) |
| `cups.service` + `cups-browsed.service` | active | Printing — not needed on a server |
| `gdm.service` + `gnome-remote-desktop.service` | active | GNOME desktop + RDP — desktop install used as a server |
| `rpcbind.service` | active | Portmapper on TCP/UDP 111 — **not needed; no NFS configured** |
| `avahi-daemon.service` | active | mDNS announce (used by HA for discovery) |
| `systemd-oomd.service` | active | Userspace OOM killer |

## Application services on the host (not in containers)

### `homelab-tools.service` (Flask)

- Unit: `/etc/systemd/system/homelab-tools.service`
- Command: `/home/diego/homelab/ai-tools/venv/bin/python /home/diego/homelab/ai-tools/docker_status.py`
- Listens on `http://0.0.0.0:5050` and `http://192.168.178.79:5050`
- Banner: *"WARNING: This is a development server. Do not use it in a production deployment."*
- Endpoints (read from source):
  - `GET /docker/containers` — returns `docker ps` output (verified responding with no auth)
  - `GET /docker/logs?container=<name>&lines=<n>` — returns `docker logs` for an allowlisted set (`openwebui`, `ollama`, `qdrant`, `homeassistant`, `nginx-proxy-manager`, `portainer`)
- **No authentication, no TLS, no rate limit.** See [14-security-risks.md](14-security-risks.md).

### `pm2-diego.service`

- PM2 daemon for user `diego`. Runs one Node.js app:

  | id | name | status | uptime | memory | user |
  |----|------|--------|--------|--------|------|
  | 0 | `guardian-cloud-backend` | online | 5 d | 70.2 MB | diego |

- The PID listens on TCP/3001 (`node` socket on 0.0.0.0).

### Apache 2

- Two vhosts active:
  - `000-default.conf` — default `/var/www/html` on `*:80`, but resolves
    `ServerName` to `127.0.1.1`, so it only binds the loopback alias.
  - `webdav.conf` — `webdav.local` on `*:8088`. Document root
    `/var/www/webdav`, Basic-auth (file `/etc/apache2/webdav.passwd`,
    1 entry). **No TLS.**
- Apache running on port 80 alongside NPM is **conflict-prone**. Today NPM
  wins externally because Apache only binds 127.0.1.1, but any reconfig
  could flip that.

### Samba (`smbd` / `nmbd`)

- Single share defined: `[projects]` — `/mnt/storage/projects`
  - `valid users = smbuser`
  - `force user = diego`, `force group = shared`
  - `create mask = 0664`, `directory mask = 2775`
- Server signing `auto`, min protocol SMB2 (good).
- `[printers]` and `[print$]` are stock printer-sharing entries, browsable but
  unused.

### Tailscale

- Snap-managed, user `<TAILNET-USER>@`, tailnet has 6 devices (homelab,
  `<DEVICE-DESKTOP>`, `<DEVICE-TABLET>`, `<DEVICE-MOBILE-1>`,
  `<DEVICE-MOBILE-2>`, `<DEVICE-LAPTOP>`).
- Listening on `100.68.180.69:41645` and `fd7a:115c:a1e0::a401:b4ab:41721`
  (internal control endpoints).

## Cron coverage

- No user crontabs (`crontab -l` empty for `diego`; root crontab not
  inspectable without sudo password).
- `/etc/cron.d/`: `anacron`, `e2scrub_all`, `sysstat` (stock).
- `/etc/cron.daily/`: `apache2`, `apport`, `apt-compat`, `dpkg`, `logrotate`,
  `man-db`, `sysstat`.
- **No backup / snapshot / docker-image-prune jobs anywhere.**

## What is *not* running but probably should be

| Missing | Why it would help |
|---------|-------------------|
| `ufw` (or any firewall) | Single-host hardening; today only Tailscale/LAN ACLs gate the open ports |
| `fail2ban` | Mitigate SSH brute force (port 22 is open on LAN + Tailscale) |
| `docker-cleanup` / `prune` cron | Stale images and orphaned bridges accumulate |
| Backup agent (restic, borg, rsync, …) | See [12-backups.md](12-backups.md) |
| `lm-sensors` / monitoring exporter | No telemetry beyond systemd journal |
