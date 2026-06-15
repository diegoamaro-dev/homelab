# 07 — Open WebUI

## Service

| Field | Value |
|-------|-------|
| Container name | `openwebui` |
| Image | `ghcr.io/open-webui/open-webui:main` |
| Image pulled | 2026-03-09 (~3 months stale) |
| Image size | 6.62 GB |
| Build commit | `e4e69a10ec08a725bf2ab3db499ef664f2bd7570` |
| Application version | **0.8.10** |
| HTTP listener | host `:3000` → container `:8080` (uvicorn) |
| Status | Up 5 days · marked **healthy** by Docker |
| RSS | 993 MiB (largest workload on the host) |

## Networks

- `proxy_default` (172.19.0.3) — intended path from NPM
- `ai-local_default` (172.18.0.4) — internal path to Ollama and Qdrant

## Bind mounts

| Host | Container | Notes |
|------|-----------|-------|
| `/srv/homelab/data/openwebui` | `/app/backend/data` | DB + caches + uploads |
| `/var/run/docker.sock` | `/var/run/docker.sock` | **rw** — see security risks |

Sub-folders on disk: `webui.db` (2.2 MB SQLite), `cache/` (889 MB
embedding+Whisper+TikToken), `uploads/` (13 MB), `vector_db/` (188 kB
legacy Chroma — unused; Qdrant is active).

## Configuration (environment, redacted)

```
ENV=prod
PORT=8080
OLLAMA_BASE_URL=http://ollama:11434
USE_OLLAMA_DOCKER=false
USE_CUDA_DOCKER=false
USE_SLIM_DOCKER=false

VECTOR_DB=qdrant
QDRANT_URI=http://qdrant:6333

RAG_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
AUXILIARY_EMBEDDING_MODEL=TaylorAI/bge-micro-v2
RAG_RERANKING_MODEL=(unset)
WHISPER_MODEL=base

OPENAI_API_BASE_URL=
OPENAI_API_KEY=
WEBUI_SECRET_KEY=

SCARF_NO_ANALYTICS=true
DO_NOT_TRACK=true
ANONYMIZED_TELEMETRY=false
```

> Notable: `WEBUI_SECRET_KEY` is the **empty string**. Open WebUI will
> generate one at boot and lose it on the next image upgrade, invalidating
> sessions and API keys.

## Feature flags exposed by `/api/config`

```json
{
  "name": "Open WebUI",
  "version": "0.8.10",
  "features": {
    "auth": true,
    "auth_trusted_header": false,
    "enable_signup_password_confirmation": false,
    "enable_ldap": false,
    "enable_api_keys": false,
    "enable_login_form": true,
    "enable_signup": false,
    "enable_websocket": true,
    "enable_version_update_check": true,
    "enable_public_active_users_count": true
  }
}
```

- Sign-up is disabled (good for a private instance).
- API key issuance is disabled.
- LDAP / OAuth not configured (`providers: {}`).
- Update check is on — Open WebUI will tell the admin a newer version is
  available.

## Vector / RAG path

```
Open WebUI ──embed→ Qdrant (open-webui_knowledge, open-webui_files)
            ──chat→ Ollama (llama3, llama3.2, phi3)
```

Confirmed at the Qdrant side: 2 collections, 3 + 2 points (very small —
likely test documents). See [10-qdrant.md](10-qdrant.md).

## Docker socket exposure

Open WebUI has the host's Docker socket mounted read-write. Any feature in
Open WebUI that can spawn or query containers (Tools, Functions, the new
"Pipelines" subsystem) effectively has **host-root**. Combined with
`enable_signup=false` and `enable_api_keys=false`, the practical risk is
limited to the existing admin user — but it remains a sharp edge.

## Outbound configuration

- `OPENAI_API_BASE_URL` and `OPENAI_API_KEY` are empty → no upstream OpenAI
  use.
- Telemetry to Open WebUI / Scarf / HuggingFace is disabled
  (`DO_NOT_TRACK`, `ANONYMIZED_TELEMETRY`, `SCARF_NO_ANALYTICS`).
- The container will still hit GHCR on image pull and HuggingFace for
  embedding-model downloads (cached in `cache/`).
