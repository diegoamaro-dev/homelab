# 10 — Qdrant

## Service

| Field | Value |
|-------|-------|
| Container name | `qdrant` |
| Image | `qdrant/qdrant:latest` |
| Image pulled | 2026-02-19 |
| Image size | 277 MB |
| Application version | **1.17.0** (`commit 4ab6d2ee0f6c…`) |
| Startup time | 2026-06-08 08:04:42 UTC |
| HTTP listener | `:6333` (REST) — bound to host `0.0.0.0:6333` |
| gRPC listener | `:6334` — only exposed inside the container (no host port) |
| Status | Up 5 days |
| Telemetry | reports `cluster.enabled=false`, `recovery_mode=0`, status green |

## Storage

`/home/diego/homelab/ai-stack/data/qdrant` → `/qdrant/storage` (2.8 MB total)

```
aliases/
collections/
  open-webui_files/
  open-webui_knowledge/
raft_state.json
```

> Path inconsistency: every other AI service stores its data under
> `/srv/homelab/data/`, but Qdrant is under
> `/home/diego/homelab/ai-stack/data/`. Worth aligning before adding more
> collections or backups.

## Collections

### `open-webui_knowledge`

| Field | Value |
|-------|-------|
| Status | green |
| Points | 3 |
| Indexed vectors | 0 (under 10 000-vector index threshold) |
| Segments | 8 |
| Vector size | 384, cosine, in-memory (`on_disk:false`) |
| Tenant key | `tenant_id` (multi-tenant payload index, `is_tenant: true`) |
| Payload indexes | `metadata.hash`, `metadata.file_id`, `tenant_id` |

### `open-webui_files`

| Field | Value |
|-------|-------|
| Status | green |
| Points | 2 |
| Indexed vectors | 0 |
| Segments | 8 |
| Vector size | 384, cosine, in-memory |
| Tenant key | `tenant_id` |
| Payload indexes | `metadata.hash`, `metadata.file_id`, `tenant_id` |

> Vector size 384 matches the configured embedding model
> `sentence-transformers/all-MiniLM-L6-v2`. The collections are essentially
> empty — only test documents have been ingested through Open WebUI's RAG
> uploader so far.

## Access control

No API key is configured (`/cluster` returns `{"status":"disabled"}` for
cluster mode, but more importantly the REST surface accepts unauthenticated
calls). Any host with TCP/6333 reachability can read, write, or delete
collections.

## Cluster / HA

Single-node. Raft state present but no peers. `cluster.enabled=false`.

## Metrics

Qdrant exposes `/metrics` in Prometheus format on the same port. No scraper
is configured.
