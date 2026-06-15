# 02 — Data flow

Five flows cover the full system: conversation routing, RAG read,
ingestion, HA state read, HA service call. Each is described as a
numbered sequence with the actual API calls / payloads the components
exchange.

## Flow 1 — Conversation routing

The same flow for both front doors; only the entry differs.

```
                 ┌─────────────┐
   user text ─►  │ Open WebUI  │ ─► /api/chat/completions ─►
                 │  or HA      │     (or HA conversation agent)
                 │  Assist     │
                 └─────────────┘
                       │
                       ▼
            ┌────────────────────┐
            │ Tool router        │   ◄── system prompt injects tool schemas
            │ (Open WebUI fn)    │       + "you may call rag_search before
            └────────────────────┘            answering anything not about HA"
                       │
                       ▼
            ┌────────────────────┐
            │ Ollama  qwen2.5:7b │   ◄── tool-call JSON
            └────────────────────┘
                       │
       ┌───────────────┼───────────────┐
       │               │               │
       ▼               ▼               ▼
 ha_get_state    rag_search       ha_call_service
 (one or more    (one or more     (zero or one)
  in parallel)    in parallel)
       │               │               │
       └────────► tool results ◄───────┘
                       │
                       ▼
            ┌────────────────────┐
            │ Ollama (round 2)   │   ◄── synthesises final answer
            └────────────────────┘
                       │
                       ▼
                streaming text
                + citations
```

Two notable shapes:

- The model is *allowed* to skip tools entirely for casual conversation;
  the system prompt nudges it to use `rag_search` only when the question
  is about a known corpus (homelab, guardian-cloud, ensambla2,
  myfreetour) or refers to "the docs / repo / project".
- Multiple tool calls in a single round are encouraged (parallel
  function calling). qwen2.5 and llama3.1 both support this natively.

## Flow 2 — RAG search (read path)

```
LLM ─► rag_search(collection="homelab_docs",
                  query="how do I rebuild the zigbee stack?",
                  k=6)

  1. Tool fn builds embedding request to Open WebUI's built-in
     embedding endpoint OR directly to sentence-transformers in-process
     (faster, no HTTP):
        POST /api/embed { model: "intfloat/multilingual-e5-small",
                          input: "query: how do I rebuild …" }
        →  [0.014, -0.026, …]   (384 floats)

  2. Tool fn queries Qdrant:
        POST /collections/homelab_docs/points/query
        Headers: api-key: <QDRANT_API_KEY>
        Body:   { query: [0.014, …], limit: 6,
                  with_payload: true }
        →  6 points, each with payload + score

  3. Tool fn returns to LLM:
        {
          "hits": [
            { "title": "Zigbee stack setup",
              "source": "03_services/zigbee2mqtt_setup.md",
              "snippet": "…",
              "score": 0.87 },
            …
          ]
        }

  4. LLM grounds its answer in those snippets.
     System prompt requires inline citations [^N] for any factual claim.

  5. Open WebUI renders the citations as expandable footers linking back
     to the source path on disk.
```

## Flow 3 — Ingestion (write path)

Triggered by:

- cron at 02:30 daily (full sync, all corpora)
- ad-hoc: `homelab-rag-ingest sync --collection guardian_cloud`
- git post-receive hook on `/home/diego/homelab/.git` (later)

```
1. For each corpus:
     a. git -C <path> pull --ff-only   (skip on dirty trees)
     b. Walk the file tree with the corpus's include/exclude rules.
     c. For each file:
        - if mtime < last_run_mtime[corpus] and content_sha already
          present in Qdrant for this path → skip
        - else: chunk file with a markdown-aware splitter
          (~600 tokens, 80-token overlap, respects headings + code
          fences)
        - For each chunk:
          • sha256(chunk_text) → content_sha
          • if (collection, source_rel, content_sha) already exists in
            Qdrant → skip
          • else: embed → upsert with payload

     d. After the walk, list points whose source_rel is no longer
        present in the tree and delete them (handles file removals).

2. Write run report to /var/log/homelab-rag-ingest.log:
     - corpus, files seen, chunks added, chunks deleted, chunks
       unchanged, total time, errors.

3. (Optional) POST a summary to Home Assistant as a persistent
   notification so the user sees RAG churn in the morning.
```

Chunk count idempotency relies on **deterministic chunking**: same input
→ same chunk boundaries. The recommended chunker:

```python
# Pseudocode — markdown-aware
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
header = MarkdownHeaderTextSplitter(headers_to_split_on=[("#",1),("##",2),("###",3)])
body   = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=80,
                                        separators=["\n\n", "\n", " "])
```

## Flow 4 — Home Assistant state read

```
LLM ─► ha_get_state(area="lounge", domain="sensor")

  1. Tool fn calls HA REST:
        GET http://homeassistant.lan:8123/api/states
        Headers: Authorization: Bearer <HA_LLAT>

  2. Filter client-side by area registry membership
     (cached locally for ~60s).

  3. Return condensed view:
        [
          { "entity_id": "sensor.lounge_temperature",
            "state": "23.4",
            "unit": "°C",
            "last_changed": "2026-06-13T11:08:21Z" },
          { "entity_id": "binary_sensor.lounge_motion",
            "state": "off",
            "last_changed": "2026-06-13T10:42:11Z" }
        ]

  4. LLM uses values to answer.
```

Why not the websocket API? The REST `/api/states` is simpler and good
enough for one-shot lookups. For *streaming* awareness (push of new
sensor events into context) the websocket would be appropriate; that is
explicitly out of scope for v1.

## Flow 5 — Home Assistant service call (write path)

```
LLM ─► ha_call_service(domain="light",
                       service="turn_on",
                       target={"area_id":"lounge"},
                       data={"brightness_pct":60})

  1. Tool fn checks the call against the *exposed-to-assist allowlist*
     (stored locally; mirror of what HA itself exposes).
     - Allowed: light.*, switch.*, scene.turn_on, climate.set_temperature,
                cover.*, media_player.play_media, script.assistant_*
     - Refused: homeassistant.*, persistent_notification.*, system_log.*,
                hassio.*, recorder.*, every domain not on the list.

  2. If allowed:
        POST http://homeassistant.lan:8123/api/services/light/turn_on
        Headers: Authorization: Bearer <HA_LLAT>
        Body:    { "area_id": "lounge", "brightness_pct": 60 }

  3. Audit log entry:
        {
          "timestamp": "...",
          "user":      "diego" (Open WebUI session) or "assist" (HA),
          "tool":      "ha_call_service",
          "args":      {...},
          "allowed":   true,
          "result":    "200 OK"
        }

  4. LLM confirms to the user with the actual state change.
```

If the call is **denied** by the allowlist, the tool returns an error
the LLM can verbalize ("I can change lights and scenes, but not delete
entities. Want me to try a different action?").

## Sensor awareness — push vs pull

For v1, all sensor knowledge is **pull-on-demand** via `ha_get_state`.
The LLM doesn't proactively know the room temperature unless it asks.

For v2 (deferred), a "context summarizer" cron can pre-build a short
"home status" string every 5 minutes and inject it into the system
prompt:

```
Current home state (auto-refreshed):
- Lounge: 23.4°C, no motion since 10:42, lights off
- Office: 28.1°C, motion now, lights on
- Outside: 31°C, sunny, sunset 21:48
```

That lets the LLM answer "is it too hot anywhere?" without a tool call.
Skipped for v1 because:

- Costs a few hundred tokens in every system prompt.
- Stale data risks confident-wrong answers.
- The tool path is fast enough on local Ollama.

## Citation propagation

Each `rag_search` hit carries `source_path` and `source_rel`. The system
prompt instructs the LLM:

> When you use information from `rag_search`, cite each fact as
> `[^N]` where N is the hit index (1-based). Render citations at the end
> as `[^1]: <source_rel>`.

Open WebUI renders standard Markdown footnotes, so this lands as
clickable inline citations with a list at the bottom. HA Assist strips
footnotes but speaks the underlying answer; the dashboard card can show
the full text with citations.
