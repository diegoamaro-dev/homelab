# 05 — Docker volumes

## Named volumes

| Volume | Driver | Used by | Size on disk |
|--------|--------|---------|--------------|
| `portainer_data` | local | `portainer` → `/data` | (small, lives under `/var/lib/docker/volumes/`) |

Everything else is a **bind mount** (host directory directly mounted into the
container). Pros: easy to inspect / back up from the host. Cons: permissions
are managed by the host filesystem, not Docker; uid/gid mismatches are common.

## Bind mounts by service

### Open WebUI

`/srv/homelab/data/openwebui` → `/app/backend/data`

| Sub-path | Size | Purpose |
|----------|------|---------|
| `webui.db` | 2.2 MB | SQLite — users, chats, settings |
| `cache/` | 889 MB | Embedding / Whisper / TikToken model caches |
| `uploads/` | 13 MB | User-uploaded RAG documents |
| `vector_db/chroma.sqlite3` | 188 kB | Legacy local Chroma store (now unused — Qdrant is the active vector DB) |

> Open WebUI is configured with `VECTOR_DB=qdrant`, so `vector_db/` is dead
> weight. Active embeddings live in Qdrant (see [10-qdrant.md](10-qdrant.md)).

### Ollama

`/srv/homelab/data/ollama` → `/root/.ollama` (8.3 GB total)

| Sub-path | Size |
|----------|------|
| `models/blobs` | 8.3 GB |
| `models/manifests/registry.ollama.ai/library/{llama3,llama3.2,phi3}/latest` | 36 kB |
| `history` | 56 B |
| `id_ed25519` + `.pub` | Ollama's signing key for model pulls |

### Qdrant

`/home/diego/homelab/ai-stack/data/qdrant` → `/qdrant/storage` (2.8 MB)

```
aliases/
collections/open-webui_files/
collections/open-webui_knowledge/
raft_state.json
```

> Path inconsistency: Qdrant data is under `/home/diego/homelab/ai-stack/data`,
> not `/srv/homelab/data/qdrant` like Ollama and Open WebUI. The
> `/srv/homelab/data/openwebui/vector_db/` directory hints that this was once
> intended to be a single Chroma store under `/srv/homelab`.

### Home Assistant

`/srv/homelab/homeassistant` → `/config`

Notable files: `configuration.yaml`, `automations.yaml`, `scripts.yaml`,
`scenes.yaml`, `secrets.yaml`, `home-assistant_v2.db` (8.4 MB recorder DB,
plus 4.1 MB WAL), `.storage/` (auth, entity registry, integrations),
`tts/`, `blueprints/`. Detailed in [09-homeassistant.md](09-homeassistant.md).

### Nginx Proxy Manager

`/srv/homelab/data/npm` → `/data` and `/srv/homelab/data/npm/letsencrypt` →
`/etc/letsencrypt`

Contains `database.sqlite` (NPM's user/host config DB), `keys.json` (NPM's
RSA key pair — see [14-security-risks.md](14-security-risks.md)),
`nginx/`, `letsencrypt/`, `letsencrypt-acme-challenge/`, `logs/`,
`custom_ssl/`, `access/`.

### Zigbee stack

`/home/diego/homelab/03_services/zigbee-stack/`

- `mosquitto/config` → `/mosquitto/config` — **empty (missing `mosquitto.conf`)**
- `mosquitto/data`   → `/mosquitto/data`
- `mosquitto/log`    → `/mosquitto/log`
- `zigbee2mqtt/data` → `/app/data` (contains `configuration.yaml`)
- `/run/udev`        → `/run/udev` (read-only, for USB device hot-plug)

### Other

- `guardian-web`: `/home/diego/webs/guardian-cloud/html` → `/usr/share/nginx/html` (read-only static site)
- `portainer`: `portainer_data` named volume + `/var/run/docker.sock`
- `openwebui`: `/var/run/docker.sock` (writable!)
- `homeassistant`: `/etc/localtime` (read-only)

## Orphaned / unused

- `vector_db/` inside Open WebUI's data dir — superseded by Qdrant.
- The dead `html_default` and `cloudflared_default` bridge networks (see
  [04-docker-networks.md](04-docker-networks.md)) have no volumes referencing
  them.
- `hello-world` image (25.9 kB) — no container exists for it.
