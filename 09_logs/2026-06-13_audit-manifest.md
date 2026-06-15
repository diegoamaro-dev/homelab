# Server Audit — homelab

- **Date:** 2026-06-13
- **Host:** `homelab` (Ubuntu 24.04.4 LTS, kernel 6.17.0-35-generic)
- **Audit type:** Read-only inventory and risk surface
- **Operator:** diego (uid 1000)

This audit was performed without modifying the system. All data was collected
through unprivileged commands and Docker / HTTP introspection APIs. Items that
required root were skipped (UFW status, raw iptables, SMART data, lastb,
`/etc/sudoers`, NPM SQLite, WebDAV passwd, Samba pdbedit) — they are explicitly
noted in the relevant sections.

## Report index

| # | Report | Description |
|---|--------|-------------|
| 01 | [Hardware](01-hardware.md) | CPU, RAM, GPU, disks, NICs, chassis |
| 02 | [Operating system](02-operating-system.md) | Ubuntu release, kernel, uptime, users |
| 03 | [Docker containers](03-docker-containers.md) | 10 containers, images, mounts, env, restart policy |
| 04 | [Docker networks](04-docker-networks.md) | 10 networks, IPAM, container membership |
| 05 | [Docker volumes](05-docker-volumes.md) | Named volumes + bind mount inventory |
| 06 | [Running services](06-running-services.md) | systemd, PM2, Flask, Apache, Samba |
| 07 | [Open WebUI](07-openwebui.md) | Version, env, data dir, RAG / vector backend |
| 08 | [Ollama](08-ollama.md) | Version, models on disk, GPU expectations |
| 09 | [Home Assistant](09-homeassistant.md) | Version, location, integrations, auth, host networking |
| 10 | [Qdrant](10-qdrant.md) | Version, collections, points, on-disk layout |
| 11 | [Storage](11-storage.md) | Block devices, filesystems, fstab, Samba shares |
| 12 | [Backups](12-backups.md) | Current backup posture (gap analysis) |
| 13 | [Exposed ports](13-exposed-ports.md) | Listening sockets host + containers |
| 14 | [Security risks](14-security-risks.md) | Prioritised risk register with remediation hints |

## Headline findings

- **10 containers** run on this host. One — `mosquitto` — is **crash-looping**
  every ~60 s because `/mosquitto/config/mosquitto.conf` is missing in the
  expected bind-mount path.
- **Cloudflare tunnel token** is committed in plaintext in
  [`/home/diego/webs/cloudflared/docker-compose.yml`](../webs/cloudflared/docker-compose.yml).
- **Nginx Proxy Manager private RSA key** is stored in plaintext in
  [`/srv/homelab/data/npm/keys.json`](../../srv/homelab/data/npm/keys.json)
  (world-readable to anyone with root on the host).
- A **Flask development server** (`homelab-tools.service`) is bound to
  `0.0.0.0:5050` with **no authentication** and exposes Docker container status
  and logs.
- **Open WebUI `WEBUI_SECRET_KEY` is empty** — JWT signing key is generated at
  startup and lost on every container restart, invalidating user sessions.
- **No backups are running.** `/srv/homelab/backups` and `/mnt/storage/backups`
  are empty; no backup cron jobs or scripts exist.
- **UFW is disabled / inaccessible** to non-root; the host relies entirely on
  the LAN/Tailscale boundary for protection. `rpcbind` (portmapper) is exposed
  on `0.0.0.0:111` even though NFS is not configured.
- Container images for **Home Assistant (2026.3.1)**, **Open WebUI (0.8.10)**,
  **Ollama (0.17.7)** were last pulled on 2026-03-06/09. Three months of
  upstream updates pending.
- The system **crashed on 2026-06-03 12:55** (`last` shows the prior session
  ended in `crash`). No oops/panic captured in the current journal window.

See [14-security-risks.md](14-security-risks.md) for the full prioritised list.
