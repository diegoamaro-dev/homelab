# 03 — Docker containers

## Engine

| Field | Value |
|-------|-------|
| Docker Engine | 29.4.1 |
| Compose plugin | v5.1.3 |
| Packages | `docker-ce`, `docker-ce-cli`, `docker-buildx-plugin`, `docker-compose-plugin`, `docker-ce-rootless-extras` |
| Daemon | `docker.service`, `containerd.service` active |
| `/var/run/docker.sock` | Mounted into `openwebui` (read/write) and `portainer` (read/write) |

> Two containers can drive the Docker daemon directly — Portainer (expected)
> and Open WebUI (used by its "Tools" / function-runner feature). Open WebUI
> RCE-equivalent: an authenticated webui user with the right permission can
> escape to host root via the socket.

## Container inventory

10 containers, all started 5 days ago at the boot on 2026-06-08. One is
crash-looping.

| # | Name | Image | Tag / version | Status | Restart policy |
|---|------|-------|--------------|--------|----------------|
| 1 | `openwebui` | `ghcr.io/open-webui/open-webui` | `main` (app 0.8.10) | Up 5 d (healthy) | unless-stopped |
| 2 | `ollama` | `ollama/ollama` | `latest` (app 0.17.7) | Up 5 d | unless-stopped (assumed) |
| 3 | `qdrant` | `qdrant/qdrant` | `latest` (app 1.17.0) | Up 5 d | — |
| 4 | `homeassistant` | `ghcr.io/home-assistant/home-assistant` | `stable` (app 2026.3.1) | Up 5 d | — |
| 5 | `nginx-proxy-manager` | `jc21/nginx-proxy-manager` | `latest` | Up 5 d | — |
| 6 | `portainer` | `portainer/portainer-ce` | `latest` | Up 5 d | — |
| 7 | `cloudflared` | `cloudflare/cloudflared` | `latest` | Up 5 d | — |
| 8 | `zigbee2mqtt` | `koenkk/zigbee2mqtt` | `latest` | Up 5 d | — |
| 9 | `mosquitto` | `eclipse-mosquitto` | `2` | **Restarting (3) ~60 s loop** | — |
| 10 | `guardian-web` | `nginx` | `alpine` | Up 5 d | unless-stopped |

`mosquitto` failure cause (from logs, repeating every minute):

```
Error: Unable to open config file '/mosquitto/config/mosquitto.conf'.
mosquitto version 2.1.2 terminating
```

The bind-mount `/home/diego/homelab/03_services/zigbee-stack/mosquitto/config`
exists on disk but contains no `mosquitto.conf`. The directory is owned by
root, so the file may have been deleted or never copied in.

## Images on disk

| Image | Size | Pulled |
|-------|------|--------|
| `ghcr.io/open-webui/open-webui:main` | 6.62 GB | 2026-03-09 01:13 |
| `ollama/ollama:latest` | 9.04 GB | 2026-03-06 03:30 |
| `ghcr.io/home-assistant/home-assistant:stable` | 3.34 GB | 2026-03-06 22:16 |
| `jc21/nginx-proxy-manager:latest` | 1.66 GB | 2026-02-17 06:43 |
| `qdrant/qdrant:latest` | 277 MB | 2026-02-19 16:01 |
| `portainer/portainer-ce:latest` | 243 MB | 2026-02-25 22:28 |
| `koenkk/zigbee2mqtt:latest` | 223 MB | 2026-03-02 12:18 |
| `cloudflare/cloudflared:latest` | 96.2 MB | 2026-03-09 15:24 |
| `nginx:alpine` | 93.5 MB | 2026-04-15 23:19 |
| `eclipse-mosquitto:2` | 35.9 MB | 2026-02-09 21:01 |
| `hello-world:latest` | 25.9 kB | 2025-08-08 — unused, candidate for `docker rmi` |

> All long-running images are 2–4 months stale. Open WebUI, Ollama and Home
> Assistant in particular ship weekly. See [14-security-risks.md](14-security-risks.md).

## Resource usage (idle snapshot)

| Container | CPU % | RSS | Net I/O | Block I/O |
|-----------|-------|-----|---------|-----------|
| `openwebui` | 0.09 | 993.6 MiB | 1.35 MB / 2.20 MB | 566 MB / 7.11 MB |
| `homeassistant` | 0.03 | 493.7 MiB | host net | 243 MB / 211 MB |
| `qdrant` | 0.09 | 301.2 MiB | 824 kB / 570 kB | 56.9 MB / 336 kB |
| `nginx-proxy-manager` | 0.03 | 181.2 MiB | 50.9 MB / 550 kB | 110 MB / 885 kB |
| `ollama` | 0.00 | 119.7 MiB | 420 kB / 59.8 kB | 4.70 GB / 0 B |
| `portainer` | 0.01 | 81.86 MiB | 768 kB / 252 B | 66.6 MB / 132 MB |
| `zigbee2mqtt` | 0.00 | 73.55 MiB | 691 kB / 126 B | 56.7 MB / 0 B |
| `cloudflared` | 0.05 | 36.00 MiB | 64.7 MB / 41.6 MB | 39.3 MB / 0 B |
| `guardian-web` | 0.00 | 19.84 MiB | 801 kB / 4.49 MB | 9.52 MB / 4.10 kB |
| `mosquitto` | 0.00 | 0 B | 0 | 0 | (crash loop) |

## Bind mounts

| Container | Host path | Container path | Mode |
|-----------|-----------|----------------|------|
| `openwebui` | `/srv/homelab/data/openwebui` | `/app/backend/data` | rw |
| `openwebui` | `/var/run/docker.sock` | `/var/run/docker.sock` | rw |
| `ollama` | `/srv/homelab/data/ollama` | `/root/.ollama` | rw |
| `qdrant` | `/home/diego/homelab/ai-stack/data/qdrant` | `/qdrant/storage` | rw |
| `homeassistant` | `/srv/homelab/homeassistant` | `/config` | rw |
| `homeassistant` | `/etc/localtime` | `/etc/localtime` | ro |
| `nginx-proxy-manager` | `/srv/homelab/data/npm` | `/data` | rw |
| `nginx-proxy-manager` | `/srv/homelab/data/npm/letsencrypt` | `/etc/letsencrypt` | rw |
| `portainer` | `portainer_data` (named) | `/data` | rw |
| `portainer` | `/var/run/docker.sock` | `/var/run/docker.sock` | rw |
| `mosquitto` | `…/zigbee-stack/mosquitto/{config,data,log}` | `/mosquitto/{config,data,log}` | rw |
| `zigbee2mqtt` | `…/zigbee-stack/zigbee2mqtt/data` | `/app/data` | rw |
| `zigbee2mqtt` | `/run/udev` | `/run/udev` | ro |
| `guardian-web` | `/home/diego/webs/guardian-cloud/html` | `/usr/share/nginx/html` | ro |
| `cloudflared` | (none) | — | — |

> Data is split across **three roots**: `/srv/homelab/data` (most stacks),
> `/srv/homelab/homeassistant` (HA only), and `/home/diego/homelab/ai-stack/data`
> (Qdrant only — and Ollama / Open WebUI bind-mounts are in `/srv/homelab` but
> the related compose/docs live under `/home/diego/homelab/ai-stack`).
> This is one of the larger documentation / consistency gaps.

## Security context (host capabilities)

| Container | Privileged | Devices | Notable caps |
|-----------|-----------|---------|--------------|
| `openwebui` | no | none | default + `NET_RAW` |
| `homeassistant` | no | none (host net) | default |
| `zigbee2mqtt` | no | `/dev/ttyUSB0` ← USB Zigbee dongle | default |
| Others | no | none | default |

`homeassistant` uses **host network mode** — it sees every host interface
including `tailscale0`, and `:8123` listens on `0.0.0.0` directly on the host.

## Compose / declaration coverage

Only two `docker-compose.yml` files exist anywhere on the host:

- `/home/diego/webs/cloudflared/docker-compose.yml`
- `/home/diego/webs/guardian-cloud/docker-compose.yml`

The other 8 containers (`openwebui`, `ollama`, `qdrant`, `homeassistant`,
`nginx-proxy-manager`, `portainer`, `zigbee2mqtt`, `mosquitto`) were created
with **ad-hoc `docker run` commands** — there is no checked-in declaration of
their configuration. This is a significant operability risk: rebuilding any of
them depends on recovering the original CLI from shell history.

`/srv/homelab/compose/` is empty.
