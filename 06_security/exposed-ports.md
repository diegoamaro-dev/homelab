# 13 — Exposed ports

Snapshot of listening sockets on the host. "Reachable from" is inferred from
the bind address and the absence of a host firewall (UFW status not readable
without sudo, but no `ufw` listening rules visible).

## TCP

| Port | Bind | Process / container | Service | Reachable from |
|------|------|---------------------|---------|----------------|
| 22 | 0.0.0.0 | `sshd` | SSH | LAN + Tailscale |
| 80 | 0.0.0.0 | `nginx-proxy-manager` | NPM HTTP entry point | LAN + Tailscale |
| 80 | 127.0.1.1 | `apache2` | Default vhost (loopback alias only) | host only |
| 81 | 0.0.0.0 | `nginx-proxy-manager` | **NPM admin UI** | LAN + Tailscale |
| 111 | 0.0.0.0 | `rpcbind` | RPC portmapper | LAN + Tailscale |
| 139 | 0.0.0.0 | `smbd` (NetBIOS session) | Samba | LAN + Tailscale |
| 443 | 0.0.0.0 | `nginx-proxy-manager` | NPM HTTPS entry point | LAN + Tailscale |
| 445 | 0.0.0.0 | `smbd` | Samba (SMB direct) | LAN + Tailscale |
| 631 | 127.0.0.1 / ::1 | `cupsd` | Printing UI | host only |
| 3000 | 0.0.0.0 | `openwebui` | Open WebUI | LAN + Tailscale |
| 3001 | 0.0.0.0 | `node` (PM2: `guardian-cloud-backend`) | Guardian backend | LAN + Tailscale |
| 5050 | 0.0.0.0 | `homelab-tools` Flask | **Unauthenticated Docker status / logs API** | LAN + Tailscale |
| 6333 | 0.0.0.0 | `qdrant` | Qdrant REST | LAN + Tailscale |
| 8000 | 0.0.0.0 | `portainer` | Portainer Edge Agent | LAN + Tailscale |
| 8080 | 0.0.0.0 | `zigbee2mqtt` | Zigbee2MQTT frontend | LAN + Tailscale |
| 8085 | 0.0.0.0 | `guardian-web` | Static site (nginx) | LAN + Tailscale |
| 8088 | 0.0.0.0 (`*`) | `apache2` (`webdav.local` vhost) | WebDAV w/ Basic auth, plain HTTP | LAN + Tailscale |
| 8123 | 0.0.0.0 | `homeassistant` (host net) | Home Assistant UI | LAN + Tailscale |
| 9443 | 0.0.0.0 | `portainer` | Portainer HTTPS UI | LAN + Tailscale |
| 11434 | 0.0.0.0 | `ollama` | Ollama REST (no auth) | LAN + Tailscale |
| 18554 | 127.0.0.1 | (unidentified) | localhost only | host only |
| 39727 | 127.0.0.1 | VS Code Server (`code-0958016b2a`) | Remote dev | host only |
| 41645 | 100.68.180.69 (`tailscale0`) | tailscaled | Tailscale internal | tailnet |
| 41721 | tailscale IPv6 | tailscaled | Tailscale internal | tailnet |

## UDP

| Port | Bind | Process / service |
|------|------|-------------------|
| 53 | 127.0.0.53 + 127.0.0.54 | systemd-resolved (stub resolver) |
| 111 | 0.0.0.0 | rpcbind |
| 137 | broadcast on every interface | nmbd (NetBIOS Name Service) |
| 138 | broadcast on every interface | nmbd (NetBIOS Datagram Service) |
| 5353 | (avahi) | mDNS announce (homeassistant + avahi) |
| Several high random ports | LAN side | mDNS responders, CUPS browser |

`nmbd` broadcasts on every Docker bridge interface as well as the LAN. That
is noise, not a vulnerability.

## What is *not* on the host directly

Container-internal ports never exposed to the host (private to Docker
networks):

- `qdrant` gRPC `:6334` — only visible from `ai-local_default`.
- `mosquitto` `:1883` (MQTT) — would be visible inside
  `zigbee-stack_default` if mosquitto were running.
- `openwebui` listens on `:8080` inside the container; the host only sees
  `:3000`.
- `homeassistant` is *host network*, so its ports are listed above directly.

## External exposure path (Cloudflare tunnel)

`cloudflared` runs with `TUNNEL_TOKEN=…` set from `docker-compose.yml`. The
tunnel ID encoded in the token is `<REDACTED-TUNNEL-UUID>`,
account `<REDACTED-CF-ACCOUNT-TAG>`. From `cloudflare-net` the tunnel
can reach `guardian-web` directly. No other container is on `cloudflare-net`,
so only the static site is intentionally exposed via Cloudflare.

> The mapping inside the Cloudflare dashboard is not visible from the host —
> the operator should verify in Cloudflare Zero Trust which hostnames are
> bound to this tunnel.

## Router posture

The homelab overview document states *"No se utilizan puertos abiertos en el
router para acceso externo"* — i.e., the home router does **not** forward
any ports inbound. External reach is meant to be Cloudflare tunnel + Tailscale
only. This is the load-bearing assumption that makes the wide-open LAN-side
posture acceptable. If port forwarding ever changes, every port above
becomes Internet-reachable.
