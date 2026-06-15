# 08 — Ollama

## Service

| Field | Value |
|-------|-------|
| Container name | `ollama` |
| Image | `ollama/ollama:latest` |
| Image pulled | 2026-03-06 (~3 months stale) |
| Image size | 9.04 GB |
| Application version | **0.17.7** (`GET /api/version`) |
| HTTP listener | host `:11434` → container `:11434` (default REST API) |
| Bind address | `OLLAMA_HOST=0.0.0.0:11434` (env var set inside container) |
| Status | Up 5 days |
| Currently loaded models | 0 (`/api/ps` → `{"models":[]}`) — models load on demand |

## Networks

- `ai-local_default` only. Reachable to / from Open WebUI as the hostname
  `ollama`. Also reachable from the LAN on `192.168.178.79:11434` (no auth).

## Environment

```
OLLAMA_HOST=0.0.0.0:11434
LD_LIBRARY_PATH=/usr/local/nvidia/lib:/usr/local/nvidia/lib64
NVIDIA_DRIVER_CAPABILITIES=compute,utility
NVIDIA_VISIBLE_DEVICES=all
```

> The image is configured for NVIDIA passthrough, but this host has only the
> integrated **AMD Radeon 780M** (Phoenix1). Ollama falls back to CPU. With
> Zen 4 + AVX-512 + 16 threads, 3B-class models are interactive; an 8B Q4
> model will be slower but usable for single-user chat. For meaningful
> acceleration the path would be ROCm (host driver + `ollama/ollama:rocm`
> image) or upgrading to a discrete GPU.

## Models on disk

`/srv/homelab/data/ollama/models/`

| Model | Family | Params | Quant | Size on disk |
|-------|--------|--------|-------|--------------|
| `llama3:latest` | llama | 8.0 B | Q4_0 | 4.66 GB (`365c0bd3c000`) |
| `phi3:latest` | phi3 | 3.8 B | Q4_0 | 2.18 GB (`4f2222927938`) |
| `llama3.2:latest` | llama | 3.2 B | Q4_K_M | 2.02 GB (`a80c4f17acd5`) |

Total: ~8.3 GB across 16 blob files plus 3 manifests under
`models/manifests/registry.ollama.ai/library/`.

Modification dates: all from 2026-03-11/13 — no new pulls in 3 months.

The container also stores its identity at:
- `id_ed25519` (387 B, mode 0600) — Ollama signing key
- `id_ed25519.pub` (81 B)
- `history` — 56 B model-pull history

## API surface

`/api/tags`, `/api/version`, `/api/ps` confirmed responding. Standard Ollama
REST surface is fully open — anyone with TCP/11434 can pull / delete models,
chat, and embed. **No auth layer.**
