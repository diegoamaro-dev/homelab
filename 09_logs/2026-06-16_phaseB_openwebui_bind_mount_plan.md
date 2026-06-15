# Phase B: Open WebUI Bind Mount Recreate Plan (Step B-3)

**Date:** 2026-06-16

This document details the precise, rollback-safe execution plan for recreating the `openwebui` container to inject the ingest pipeline's runtime dependencies via a read-only bind mount, as required by Phase B (Gate G-1).

## 1. Current Container Configuration Inspection
Based on live inspection (`docker inspect openwebui`), the running container's footprint is:

- **Image:** `ghcr.io/open-webui/open-webui:main`
- **Networks:** Attached to both `ai-local_default` and `proxy_default`.
- **Ports:** `3000:8080` (Host 3000 mapping to Container 8080).
- **Mounts:** `-v /srv/homelab/data/openwebui:/app/backend/data` (Read/Write).
- **Restart Policy:** `unless-stopped`
- **Health:** Healthy.
- **Critical Env Vars Detected:** `VECTOR_DB`, `QDRANT_URI`, `OLLAMA_BASE_URL`, `WEBUI_SECRET_KEY`, `QDRANT_API_KEY`, etc.

## 2. Recreate Execution Plan
The recreate operation must be atomic and reversible.

### 2.1 Pre-Flight Variables
Extract the necessary live secrets from the host `.env` file to prevent hardcoding them in shell history:
```bash
KEY_QDRANT=$(awk -F= '/^QDRANT__SERVICE__API_KEY=/ {print $2; exit}' /home/diego/homelab/ai-stack/.env)
KEY_WEBUI=$(awk -F= '/^WEBUI_SECRET_KEY=/ {print $2; exit}' /home/diego/homelab/ai-stack/.env)
```

### 2.2 Container Rollback Strategy (Stop and Rename)
Instead of deleting the live container immediately, we stop it and rename it to preserve its exact state as a fast-rollback target:
```bash
docker stop openwebui
docker rename openwebui openwebui_pre_phaseB_$(date +%Y%m%d%H%M%S)
```

### 2.3 Container Re-Creation
Create the new container with the exact same configuration as the original, **plus the new `/opt/ingest` read-only bind mount**:

```bash
docker run -d --name openwebui --restart unless-stopped \
  --network ai-local_default \
  -p 3000:8080 \
  -v /srv/homelab/data/openwebui:/app/backend/data \
  -v /home/diego/homelab/ai-stack/ingest:/opt/ingest:ro \
  -e ENV=prod \
  -e PORT=8080 \
  -e OLLAMA_BASE_URL=http://ollama:11434 \
  -e QDRANT_URI=http://qdrant:6333 \
  -e QDRANT_API_KEY="$KEY_QDRANT" \
  -e VECTOR_DB=qdrant \
  -e WEBUI_SECRET_KEY="$KEY_WEBUI" \
  -e WEBUI_API_KEYS_ENABLED=true \
  -e AMAROLAB_AUDIT_LOG=/app/backend/data/amarolab-audit.log \
  -e USE_OLLAMA_DOCKER=false \
  -e USE_CUDA_DOCKER=false \
  -e USE_SLIM_DOCKER=false \
  -e OPENAI_API_BASE_URL= \
  -e OPENAI_API_KEY= \
  -e SCARF_NO_ANALYTICS=true \
  -e DO_NOT_TRACK=true \
  -e ANONYMIZED_TELEMETRY=false \
  ghcr.io/open-webui/open-webui:main
```

### 2.4 Re-Attach Secondary Networks
The inspection revealed that the container is actively participating in `proxy_default`. This must be manually restored after the `docker run` statement:

```bash
docker network connect proxy_default openwebui
```

## 3. Post-Recreate Validation
Once the container is started, verify its health and module visibility without committing to any tool updates:
1. **Network Attachment:** `docker inspect openwebui | jq '.[0].NetworkSettings.Networks | keys'` should return `["ai-local_default", "proxy_default"]`.
2. **Mount Validation:** `docker inspect openwebui | jq '.[0].HostConfig.Mounts'` should list both `/srv/homelab/data/openwebui` and `/home/diego/homelab/ai-stack/ingest`.
3. **Module Import Test:** Ensure the container can natively read the ingest logic.
   ```bash
   docker exec openwebui python3 -c "import sys; sys.path.insert(0,'/opt/ingest'); from ingest.embedder import Embedder; print(Embedder)"
   ```
4. **Data Persistence:** Confirm that the existing `webui.db` and `amarolab-audit.log` remain byte-for-byte identical, validating that no state was wiped during the recreation.

## 4. Rollback Plan
If any of the post-recreate validations fail, immediately abort and rollback to the preserved container:

```bash
docker stop openwebui
docker rm openwebui
docker rename <the_timestamped_pre_phaseB_container> openwebui
docker start openwebui
```
