# 04 — Docker networks

10 networks declared on the Docker engine. Five user-defined bridges carry the
workload; three are empty / not in use.

## Inventory

| Network | Driver | Subnet | Gateway | Containers |
|---------|--------|--------|---------|------------|
| `bridge` (default) | bridge | 172.17.0.0/16 | 172.17.0.1 | `portainer` |
| `ai-local_default` | bridge | 172.18.0.0/16 | 172.18.0.1 | `qdrant`, `ollama`, `openwebui` |
| `proxy_default` | bridge | 172.19.0.0/16 | 172.19.0.1 | `nginx-proxy-manager`, `openwebui`, `portainer` |
| `zigbee-stack_default` | bridge | 172.20.0.0/16 | 172.20.0.1 | `zigbee2mqtt` |
| `html_default` | bridge | 172.21.0.0/16 | 172.21.0.1 | *(empty)* — bridge is DOWN |
| `guardian-cloud_default` | bridge | 172.22.0.0/16 | 172.22.0.1 | `guardian-web` |
| `cloudflared_default` | bridge | 172.23.0.0/16 | 172.23.0.1 | *(empty)* — bridge is DOWN |
| `cloudflare-net` | bridge | 172.24.0.0/16 | 172.24.0.1 | `cloudflared`, `guardian-web` |
| `host` | host | — | — | `homeassistant` |
| `none` | null | — | — | — |

## Membership map

```
openwebui      → ai-local_default (172.18.0.4) + proxy_default (172.19.0.3)
ollama         → ai-local_default
qdrant         → ai-local_default
nginx-proxy-manager → proxy_default
portainer      → bridge + proxy_default
zigbee2mqtt    → zigbee-stack_default
mosquitto      → zigbee-stack_default (when running) — currently restarting
guardian-web   → guardian-cloud_default + cloudflare-net
cloudflared    → cloudflare-net
homeassistant  → host (raw host network)
```

## Topology notes

- **`ai-local_default`** is the in-network path for Open WebUI ↔ Ollama
  (`OLLAMA_BASE_URL=http://ollama:11434`) and Open WebUI ↔ Qdrant
  (`QDRANT_URI=http://qdrant:6333`).
- **`proxy_default`** connects NPM to Portainer and Open WebUI, suggesting an
  intent to front them with a reverse proxy. The
  [00_overview/current-status.md](../homelab/00_overview/) document confirms
  this intent: *"Nginx Proxy Manager installed but not used as central entry
  point."*
- **`cloudflare-net`** is the egress for the Cloudflare tunnel. It reaches
  `guardian-web` directly, so guardian-web is the only container intentionally
  exposed via Cloudflare.
- **`html_default`** and **`cloudflared_default`** are dead bridges left over
  from earlier compose deployments. Their interfaces are DOWN on the host.
- **`homeassistant` on `host` network** lets it discover devices via mDNS/SSDP
  on the LAN, but it bypasses every Docker isolation. Its `:8123` listens on
  every host IP including the Tailscale interface.

## Inter-container DNS

User-defined bridges have embedded DNS. From `openwebui`, hostnames `ollama`
and `qdrant` resolve to the `ai-local_default` IPs. From `cloudflared`,
hostname `guardian-web` resolves on `cloudflare-net`. The default `bridge`
network does not have name resolution, but only `portainer` lives there.

## IP allocation pressure

Each user network claims a /16 (~65 k addresses) — well above what is needed.
The host already has 7 bridges, plus several `veth*` interfaces per
container. There is no functional issue, only `ip a` noise.
