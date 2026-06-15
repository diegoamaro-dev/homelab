# 03 — Required integrations

Six wires need to be soldered. None of them require Internet access at
runtime; all are local-network calls.

| # | From | To | Protocol | Auth | Reach |
|---|------|-----|----------|------|-------|
| 1 | Open WebUI | Ollama | HTTP `/api/chat` | none (in-cluster) | `ai-local_default` |
| 2 | Open WebUI | Qdrant | HTTP `/collections/*/points/query` | API key | `ai-local_default` |
| 3 | Open WebUI Tools | Home Assistant REST | HTTP `/api/states`, `/api/services/*` | LLAT bearer | host net (`192.168.178.79:8123`) |
| 4 | Home Assistant | Open WebUI (LLM proxy) | HTTP `/v1/chat/completions` (OpenAI-compatible) | Open WebUI API key | host net + `ai-local_default` |
| 5 | Ingestion service | Qdrant | HTTP `/collections/*/points` | API key | `ai-local_default` |
| 6 | Ingestion service | sentence-transformers | in-process Python | n/a | host |

## 1. Open WebUI ↔ Ollama  (already wired)

- Existing env var: `OLLAMA_BASE_URL=http://ollama:11434`
- Verification: `/admin/settings/connections` in Open WebUI shows Ollama
  reachable.
- New work: pull the recommended models so Open WebUI sees them:

  ```bash
  docker exec ollama ollama pull qwen2.5:7b-instruct
  docker exec ollama ollama pull qwen2.5:3b-instruct
  # Optional: drop unused ones to save disk
  # docker exec ollama ollama rm llama3:latest
  # docker exec ollama ollama rm phi3:latest
  ```

## 2. Open WebUI ↔ Qdrant  (already wired; needs auth)

- Existing env vars: `VECTOR_DB=qdrant`, `QDRANT_URI=http://qdrant:6333`.
- After Phase 2 R-07 the Qdrant API key must also be passed:
  `QDRANT_API_KEY=<value>`.
- Collections used directly by Open WebUI:
  - `open-webui_knowledge` (built-in feature — keep enabled for ad-hoc
    document uploads)
  - `open-webui_files` (built-in)
- Collections used by the new RAG tool: `homelab_docs`,
  `guardian_cloud`, `ensambla2`, `myfreetour`.

## 3. Open WebUI Tools ↔ Home Assistant

Two tools. Both are implemented as Open WebUI **Functions** (server-side
Python that the LLM can call). Functions live under
`/srv/homelab/data/openwebui/functions/` once enabled in the admin UI.

### Long-Lived Access Token

In HA → user profile → Security → Long-Lived Access Tokens → "Create
Token". Name it `assistant-tools`. Store in
`/home/diego/homelab/ai-stack/.env`:

```bash
( umask 077 && \
  printf 'HA_BASE_URL=http://192.168.178.79:8123\nHA_LLAT=%s\n' \
    '<paste-token-here>' \
  >> /home/diego/homelab/ai-stack/.env )
```

Mount via env_file when adding the assistant container, or set in Open
WebUI's Function configuration (per-function secrets).

### Tool: `ha_get_state`

```python
# Pseudo — full version produced during implementation
from pydantic import BaseModel
import httpx, os

class GetStateArgs(BaseModel):
    entity_id: str | None = None      # exact match
    area:      str | None = None      # area_id or area name
    domain:    str | None = None      # 'sensor', 'light', ...

def ha_get_state(args: GetStateArgs) -> dict:
    """Read Home Assistant entity state(s). Use this whenever the user
    asks about sensor values, device status, or room conditions."""
    r = httpx.get(f"{os.environ['HA_BASE_URL']}/api/states",
                  headers={"Authorization": f"Bearer {os.environ['HA_LLAT']}"},
                  timeout=5.0)
    r.raise_for_status()
    states = r.json()
    # …filter by entity_id / area / domain
    return {"entities": filtered_subset}
```

### Tool: `ha_call_service`

```python
class CallArgs(BaseModel):
    domain:  str             # 'light', 'climate', 'scene', ...
    service: str             # 'turn_on', 'set_temperature', ...
    target:  dict | None
    data:    dict | None

ALLOWED_DOMAINS = {
    "light","switch","scene","cover","climate",
    "media_player","script","automation","fan",
    "vacuum","input_boolean","input_select","input_number"
}

def ha_call_service(args: CallArgs) -> dict:
    if args.domain not in ALLOWED_DOMAINS:
        return {"allowed": False, "reason":
                f"Domain '{args.domain}' is not permitted from the assistant."}
    r = httpx.post(
        f"{os.environ['HA_BASE_URL']}/api/services/{args.domain}/{args.service}",
        headers={"Authorization": f"Bearer {os.environ['HA_LLAT']}",
                 "Content-Type": "application/json"},
        json={**(args.target or {}), **(args.data or {})},
        timeout=10.0)
    return {"allowed": True, "status": r.status_code, "result": r.json()}
```

The allowlist mirrors HA's *exposed-to-assist* concept but keeps the
truth at the tool level, so the LLM can't bypass it by addressing HA
directly.

## 4. Home Assistant ↔ Open WebUI  (NEW wire)

HA's *Conversation* subsystem can target an OpenAI-compatible endpoint.
Open WebUI exposes one (`/openai/v1/chat/completions`). Result: HA Assist
ends up talking to the same brain Open WebUI talks to, including all the
tools.

### Open WebUI side

- Admin → Settings → Account → API Keys → create key named `ha-assist`.
- (Optional but recommended) restrict the key to specific models.

### HA side — two options

**A. HACS "Extended OpenAI Conversation" (recommended).** Supports
function calling against OpenAI-compatible endpoints with the model the
endpoint advertises. Configure:

- Base URL: `http://192.168.178.79:3000/openai/v1`
- API key: `<ha-assist key>`
- Model: `qwen2.5:7b-instruct` (matches Ollama tag)
- Functions: leave empty here — Open WebUI injects them server-side.

**B. Built-in `ollama` integration.** Simpler, but tool calling is
limited and you would have to duplicate tools in HA. Use this only if
you don't want HACS.

### Conversation alias

In HA Assist → Pipelines, set:

```
Wake word:       (Wyoming + porcupine, optional)
Speech-to-text:  Whisper  (Wyoming, optional)
Conversation:    Extended OpenAI Conversation (assistant)
Text-to-speech:  Piper  (Wyoming, optional)
```

Name it "Assistant" and pin it as default.

## 5. Ingestion service ↔ Qdrant  ✅ APPLIED 2026-06-13

> Built and running. Lives at `/home/diego/homelab/ai-stack/ingest/`.
> Three of four corpora populated (1 377 points). Cron installed at
> 02:30 daily. See [PHASE-1-APPLIED.md](PHASE-1-APPLIED.md).

The new service is a small Python app:

```
homelab-rag-ingest/
├── pyproject.toml
├── ingest/
│   ├── __init__.py
│   ├── cli.py             # argparse: sync, status, drop, search
│   ├── connectors/
│   │   ├── fs.py          # filesystem walker
│   │   └── git.py         # git pull + walker
│   ├── chunker.py         # markdown-aware + code-aware
│   ├── embedder.py        # sentence-transformers in-process
│   ├── store.py           # Qdrant client wrapper
│   └── config.py          # per-corpus include/exclude rules
└── conf/
    └── corpora.yaml       # list of corpora + their paths/URLs
```

### `conf/corpora.yaml` (planned shape)

```yaml
corpora:
  - name: homelab_docs
    type: fs
    root: /home/diego/homelab
    include: ["**/*.md", "**/*.yaml", "**/*.yml", "**/*.conf"]
    exclude: ["**/.git/**", "**/venv/**", "ai-tools/venv/**"]

  - name: guardian_cloud
    type: git
    path: /mnt/storage/projects/guardian-cloud
    include: ["docs/**/*.md", "strategy/**/*.md", "playbook/**/*.md",
              "Pagina web/**/*.md", "*.md"]
    exclude: ["**/node_modules/**", "**/dist/**", "**/build/**",
              "**/.gradle/**", "**/.idea/**"]

  - name: ensambla2
    type: git
    path: /mnt/storage/projects/ensambla2
    include: ["docs/**/*.md", "*.md", "**/README.md"]
    exclude: ["**/node_modules/**", "**/dist/**", "**/build/**",
              "**/.next/**"]

  - name: myfreetour
    type: git
    path: "<TBD>"   # OPEN QUESTION
    include: ["**/*.md", "README*"]
    exclude: ["**/node_modules/**", "**/dist/**"]
```

### Qdrant collection creation (one-shot)

```bash
# Run by ingest CLI on first invocation; equivalent curl shown for clarity
for c in homelab_docs guardian_cloud ensambla2 myfreetour; do
  curl -X PUT "http://127.0.0.1:6333/collections/$c" \
       -H "api-key: $QDRANT_API_KEY" \
       -H "Content-Type: application/json" \
       -d '{
         "vectors": { "size": 384, "distance": "Cosine" },
         "on_disk_payload": true
       }'

  # Payload indexes for fast filter
  for field in collection source_kind language; do
    curl -X PUT "http://127.0.0.1:6333/collections/$c/index" \
         -H "api-key: $QDRANT_API_KEY" \
         -H "Content-Type: application/json" \
         -d "{ \"field_name\": \"$field\", \"field_schema\": \"keyword\" }"
  done
done
```

## 6. Ingestion service ↔ sentence-transformers (in-process)

- Embedding model lives in `/srv/homelab/data/openwebui/cache/embedding/models/`
  (already populated for `all-MiniLM-L6-v2`).
- New model `intfloat/multilingual-e5-small` downloaded once (~110 MB),
  same cache layout, environment vars:
  `SENTENCE_TRANSFORMERS_HOME=/srv/homelab/data/openwebui/cache/embedding/models`
  `HF_HOME=/srv/homelab/data/openwebui/cache/embedding/models`
- The ingestion service loads the model into RAM once per run, embeds in
  batches of 32–64, releases on exit.

## Where each integration's secrets live

| Secret | Stored in | Mode | Consumed by |
|--------|-----------|------|-------------|
| `WEBUI_SECRET_KEY` | `/home/diego/homelab/ai-stack/.env` | 0600 | openwebui |
| `QDRANT__SERVICE__API_KEY` | same `.env` | 0600 | qdrant |
| `QDRANT_API_KEY` (client) | same `.env` | 0600 | openwebui, ingestion |
| `HA_LLAT` | same `.env` (or Open WebUI per-function secret) | 0600 | openwebui Tools |
| `OPENWEBUI_API_KEY` (for HA → Open WebUI) | HA secret store | n/a | HA Conversation |
| Cloudflare `TUNNEL_TOKEN` | already in `/home/diego/webs/cloudflared/.env` after R-01 | 0600 | cloudflared |

No assistant secrets land in git: `.env` is in `.gitignore` for the
relevant directories. The HA token file is inside HA's `secrets.yaml`
which is already `/config/secrets.yaml` mounted at
`/srv/homelab/homeassistant/`.

## What this design does **not** integrate

- **No external LLM** (OpenAI, Anthropic, Mistral cloud). The Open WebUI
  env vars for these stay empty.
- **No web search tool.** Out of scope for v1; can be added later
  (SearXNG container is a common pattern).
- **No email/calendar integration.** Out of scope.
- **No Cloudflare publication.** The assistant intentionally stays inside
  LAN + Tailscale boundary.
