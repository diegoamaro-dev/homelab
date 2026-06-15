# 03 — Tool catalog

> **AMENDMENTS — 2026-06-15.** This document was written before the
> Open WebUI 0.8.10 source review. Two assumptions in it are wrong as
> stated; act on the corrected sources instead of this file's
> implementation details:
>
> 1. **Code shape.** The catalog shows module-level functions
>    (`def rag_search(...): ...`). Open WebUI 0.8.10's tool loader
>    (`load_tool_module_by_id`) **requires** `class Tools:` and
>    raises `Exception("No Tools class found in the module")`
>    otherwise. Every tool must be a method of a `class Tools`.
> 2. **Source location.** The catalog says each tool is a Python file
>    under `/srv/homelab/data/openwebui/functions/`. Open WebUI 0.8.10
>    does **not** auto-discover Tools from disk; source is stored in
>    `webui.db` and installed via `POST /api/v1/tools/create` (or the
>    admin UI). The canonical disk copies live in the homelab repo at
>    `/home/diego/homelab/ai-stack/openwebui-tools/`.
>
> Authoritative corrected sources:
>
> - [`../../FUNCTIONS_COMPATIBILITY_REPORT.md`](../../FUNCTIONS_COMPATIBILITY_REPORT.md)
>   — full Open WebUI 0.8.10 runtime contract, source-grounded, with
>   a minimal working example.
> - [`../../09_logs/2026-06-15_phaseA3-tool-canary-design.md`](../../09_logs/2026-06-15_phaseA3-tool-canary-design.md)
>   — corrected Phase A.3 plan (`time_now` canary in `class Tools`
>   shape, installed via API).
> - Decisions D-23..D-26 in [`ROADMAP.md`](ROADMAP.md) — locked.
>
> Everything else in this catalog (per-tool **purpose**, **inputs**,
> **outputs**, **schemas**, **error codes**, **allowlists**, **security
> considerations**, **rate limits**, **system-prompt routing rules**)
> is still authoritative. Treat the implementation outlines below as
> pseudocode of the *behaviour* the tools must implement, not as
> ready-to-run code.

---

Five tools. Each tool is a single Python file under
`/srv/homelab/data/openwebui/functions/`. Open WebUI loads them at
startup and exposes them to whichever model the user selects (Open
WebUI calls them "Functions"; the LLM sees them as "tools").

Conventions used in every tool:

- **Input schema** in pydantic, so Open WebUI generates the right
  JSON Schema for the LLM.
- **Output** is always a JSON-serializable dict. Strings only — no
  raw bytes.
- **Errors** are returned as `{"error": "<message>", "code": "..."}`
  rather than raised, so the LLM can surface the failure to the user
  instead of seeing a stacktrace.
- **Audit logging** is mandatory. Each call appends one JSON line to
  `/app/backend/data/amarolab-audit.log` (see
  [04-security-and-permissions.md](04-security-and-permissions.md)).
- **Allowlists** are constants at the top of the file. Editing them
  requires editing the file — there is no runtime "expand my
  permissions" path.

## Shared utility — `amarolab_common.py`

Not a tool itself; a small support module the five tools import.

```python
# /srv/homelab/data/openwebui/functions/amarolab_common.py
from __future__ import annotations
import json, os, time, uuid
from datetime import datetime, timezone
from pathlib import Path

AUDIT_LOG = Path(os.environ.get(
    "AMAROLAB_AUDIT_LOG",
    "/app/backend/data/amarolab-audit.log",
))

def audit(tool: str, args: dict, *, user: str = "diego",
          allowed: bool = True, result_code: str = "ok",
          duration_ms: int | None = None) -> None:
    """Append one JSON line per tool invocation."""
    line = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "id": str(uuid.uuid4()),
        "user": user,
        "tool": tool,
        "args": _redact(args),
        "allowed": allowed,
        "result_code": result_code,
        "duration_ms": duration_ms,
    }
    try:
        AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with AUDIT_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
    except OSError:
        pass  # never fail a tool because audit can't write

_REDACT_KEYS = {"password", "token", "secret", "api_key", "authorization"}

def _redact(d: dict) -> dict:
    out = {}
    for k, v in d.items():
        if k.lower() in _REDACT_KEYS:
            out[k] = "<redacted>"
        elif isinstance(v, dict):
            out[k] = _redact(v)
        else:
            out[k] = v
    return out

class RateLimiter:
    """Simple in-process per-tool rate limit.

    Process-local; resets on container restart. Fine for a single user.
    """
    _counts: dict[str, list[float]] = {}

    @classmethod
    def check(cls, tool: str, max_per_minute: int) -> bool:
        now = time.monotonic()
        window = cls._counts.setdefault(tool, [])
        cutoff = now - 60.0
        window[:] = [t for t in window if t > cutoff]
        if len(window) >= max_per_minute:
            return False
        window.append(now)
        return True
```

## Tool 1 — `rag_search`

Query one of the indexed corpora with dense retrieval + cross-encoder
reranking. The biggest, most-used tool.

### Input

```json
{
  "type": "object",
  "properties": {
    "collection": {
      "type": "string",
      "enum": ["homelab_docs", "guardian_cloud", "ensambla2",
               "myfreetour", "infra_audits"],
      "description": "Which knowledge base to search."
    },
    "query": {
      "type": "string",
      "description": "Natural-language question or topic."
    },
    "k": {
      "type": "integer",
      "minimum": 1, "maximum": 12, "default": 6,
      "description": "How many results to return after reranking."
    }
  },
  "required": ["collection", "query"]
}
```

### Output

```json
{
  "collection": "guardian_cloud",
  "query": "recovery flow",
  "hits": [
    {
      "rank": 1,
      "source_rel": "docs/RECOVERY_BETA_VALIDATION.md",
      "title": "Guardian Cloud — Recovery Beta Validation",
      "chunk_index": 4,
      "score": 0.7341,
      "content": "## R1 — Kill app durante upload\n\n…"
    },
    …
  ]
}
```

### Routing guidance (in system prompt)

```
rag_search collections:
  homelab_docs    — homelab infrastructure docs, services, configs
  guardian_cloud  — Guardian Cloud product / architecture / recovery docs
  ensambla2       — Ensambla2 product / auth / multitenancy docs
  myfreetour      — (placeholder, ask the user if they need this)
  infra_audits    — past infrastructure audit reports and Phase 0/1 application logs
```

### Implementation outline

```python
from amarolab_common import audit, RateLimiter
from pydantic import BaseModel, Field
from typing import Literal
import os, time, sys

# Reuse the existing modules — they live in the ingest service, which is
# on the host filesystem. We mount /home/diego/homelab/ai-stack/ingest
# read-only into the openwebui container at /opt/ingest (added in v1
# compose). Or we copy a slim version. See implementation roadmap.
sys.path.insert(0, "/opt/ingest")
from ingest.embedder import Embedder
from ingest.reranker import Reranker
from qdrant_client import QdrantClient

ALLOWED_COLLECTIONS = {
    "homelab_docs", "guardian_cloud", "ensambla2",
    "myfreetour", "infra_audits",
}

class Args(BaseModel):
    collection: Literal["homelab_docs", "guardian_cloud", "ensambla2",
                        "myfreetour", "infra_audits"]
    query: str = Field(..., min_length=2, max_length=500)
    k: int = Field(default=6, ge=1, le=12)

_emb = None  # lazy init; first call pays the load cost
_rer = None
_qdr = None

def _init():
    global _emb, _rer, _qdr
    if _emb is None:
        _emb = Embedder()
        _rer = Reranker()
        _qdr = QdrantClient(
            url=os.environ["QDRANT_URI"],
            api_key=os.environ["QDRANT_API_KEY"],
            timeout=30.0,
        )

def rag_search(collection: str, query: str, k: int = 6) -> dict:
    """Search a knowledge base; returns reranked top-k chunks with citations."""
    t0 = time.monotonic()
    args = Args(collection=collection, query=query, k=k)

    if not RateLimiter.check("rag_search", max_per_minute=30):
        audit("rag_search", args.model_dump(),
              allowed=False, result_code="rate_limited")
        return {"error": "rate limit (30/min) exceeded", "code": "rate_limited"}

    _init()
    vec = _emb.embed_query(args.query)
    res = _qdr.query_points(collection_name=args.collection,
                            query=vec, limit=30,
                            with_payload=True)
    cands = [{
        "source_rel": p.payload.get("source_rel"),
        "title": p.payload.get("title"),
        "chunk_index": p.payload.get("chunk_index"),
        "content": p.payload.get("content", ""),
        "cosine_score": float(p.score),
    } for p in res.points]
    top = _rer.rerank(args.query, cands, top_k=args.k)
    hits = [{
        "rank": i + 1,
        "source_rel": h["source_rel"],
        "title": h["title"],
        "chunk_index": h["chunk_index"],
        "score": round(h["rerank_score"], 4),
        "content": h["content"][:600],
    } for i, h in enumerate(top)]

    audit("rag_search", args.model_dump(),
          duration_ms=int((time.monotonic() - t0) * 1000))
    return {"collection": args.collection, "query": args.query, "hits": hits}
```

### Failure modes & error codes

| Code | When | What the LLM should say |
|------|------|-------------------------|
| `rate_limited` | >30 calls/min from one process | "I'm searching too fast — give me a moment." |
| `bad_collection` | (filtered earlier by pydantic) | n/a |
| `qdrant_unreachable` | network blip | "I couldn't reach the knowledge base; try again." |
| `empty_collection` | hits=[] | "I don't have anything indexed for that — would you like me to check another corpus?" |

## Tool 2 — `audit_search`

Thin sugar over `rag_search(collection="infra_audits", …)`. Exists
solely to make the LLM more likely to use the audit corpus when asked
"what changed", "what was the last audit", "what is the current
state of R-XX".

### Input

```json
{
  "type": "object",
  "properties": {
    "query": {"type": "string"},
    "k": {"type": "integer", "minimum": 1, "maximum": 12, "default": 6}
  },
  "required": ["query"]
}
```

### Output

Same shape as `rag_search`.

### Implementation outline

```python
def audit_search(query: str, k: int = 6) -> dict:
    return rag_search(collection="infra_audits", query=query, k=k)
```

Rationale: a separate tool entry in the schema makes the LLM's
auto-routing more reliable than a single tool with five different
collection choices. We measured this kind of "make it obvious" effect
in the guardian_cloud benchmark; small clarity wins for the model are
high leverage.

## Tool 3 — `ha_get_state`

Read Home Assistant entity states. Pure read; no allowlist required.

### Input

```json
{
  "type": "object",
  "properties": {
    "entity_id": {
      "type": "string",
      "description": "Exact entity id, e.g. 'sensor.lounge_temperature'."
    },
    "area":   {"type": "string", "description": "HA area_id or area name."},
    "domain": {"type": "string", "description": "HA domain, e.g. 'sensor'."}
  }
}
```

At least one of `entity_id`, `area`, `domain` must be provided.

### Output

```json
{
  "entities": [
    {
      "entity_id": "sensor.lounge_temperature",
      "state": "23.4",
      "attributes": { "unit_of_measurement": "°C", "friendly_name": "Lounge T" },
      "last_changed": "2026-06-14T08:11:23+00:00"
    }
  ],
  "count": 1
}
```

If no filter matches: `{"entities": [], "count": 0}` (not an error;
information is the answer).

### Implementation outline

```python
import httpx, os, time
from amarolab_common import audit, RateLimiter
from pydantic import BaseModel

class Args(BaseModel):
    entity_id: str | None = None
    area:      str | None = None
    domain:    str | None = None

def ha_get_state(entity_id: str | None = None,
                 area: str | None = None,
                 domain: str | None = None) -> dict:
    t0 = time.monotonic()
    args = Args(entity_id=entity_id, area=area, domain=domain)
    if not any([entity_id, area, domain]):
        audit("ha_get_state", args.model_dump(),
              allowed=False, result_code="bad_args")
        return {"error": "must specify entity_id, area, or domain",
                "code": "bad_args"}

    if not RateLimiter.check("ha_get_state", max_per_minute=60):
        audit("ha_get_state", args.model_dump(),
              allowed=False, result_code="rate_limited")
        return {"error": "rate limit", "code": "rate_limited"}

    headers = {"Authorization": f"Bearer {os.environ['HA_LLAT']}"}
    base = os.environ["HA_BASE_URL"]
    if entity_id:
        r = httpx.get(f"{base}/api/states/{entity_id}",
                      headers=headers, timeout=5.0)
        if r.status_code == 404:
            ents = []
        else:
            r.raise_for_status()
            ents = [r.json()]
    else:
        r = httpx.get(f"{base}/api/states", headers=headers, timeout=10.0)
        r.raise_for_status()
        ents = r.json()
        if domain:
            ents = [e for e in ents if e["entity_id"].startswith(f"{domain}.")]
        if area:
            # NOTE: area filtering requires walking the area registry —
            # implement when we have a real area registry to test against.
            pass

    audit("ha_get_state", args.model_dump(),
          duration_ms=int((time.monotonic() - t0) * 1000))
    return {"entities": ents, "count": len(ents)}
```

### Failure modes

| Code | When |
|------|------|
| `bad_args` | no filter provided |
| `rate_limited` | >60 calls/min |
| `ha_unreachable` | network / token problem |

## Tool 4 — `ha_call_service`

Invoke a Home Assistant service. Domain allowlist enforced; nothing
admin-flavoured.

### Input

```json
{
  "type": "object",
  "properties": {
    "domain":  {"type": "string", "description": "e.g. 'light', 'scene'."},
    "service": {"type": "string", "description": "e.g. 'turn_on'."},
    "target":  {"type": "object", "description": "e.g. {area_id: 'lounge'}"},
    "data":    {"type": "object", "description": "e.g. {brightness_pct: 60}"}
  },
  "required": ["domain", "service"]
}
```

### Allowlist (constant at top of file)

```python
ALLOWED_DOMAINS = frozenset({
    "light", "switch", "scene", "cover", "climate",
    "media_player", "script", "automation", "fan", "vacuum",
    "input_boolean", "input_select", "input_number",
})
```

**Explicitly forbidden:** `homeassistant`, `recorder`, `hassio`,
`system_log`, `persistent_notification`, `notify`, `mqtt`, `shell_command`,
`backup`, `auth`. The "if it isn't in `ALLOWED_DOMAINS`, deny" default
catches anything added later.

### Output

```json
{
  "allowed": true,
  "domain": "light",
  "service": "turn_on",
  "target": { "area_id": "lounge" },
  "data": { "brightness_pct": 60 },
  "ha_status": 200,
  "ha_response": []
}
```

Refusal:
```json
{
  "allowed": false,
  "domain": "recorder",
  "code": "domain_not_allowed",
  "message": "I can change lights, scenes, climate and similar — not 'recorder.purge'."
}
```

### Implementation outline

```python
def ha_call_service(domain: str, service: str,
                    target: dict | None = None,
                    data: dict | None = None) -> dict:
    t0 = time.monotonic()
    args = dict(domain=domain, service=service, target=target, data=data)

    if domain not in ALLOWED_DOMAINS:
        audit("ha_call_service", args,
              allowed=False, result_code="domain_not_allowed")
        return {
            "allowed": False, "domain": domain,
            "code": "domain_not_allowed",
            "message": f"Domain '{domain}' is not in the assistant's allowlist.",
        }

    if not RateLimiter.check("ha_call_service", max_per_minute=10):
        audit("ha_call_service", args,
              allowed=False, result_code="rate_limited")
        return {"allowed": False, "code": "rate_limited"}

    body = {**(target or {}), **(data or {})}
    r = httpx.post(
        f"{os.environ['HA_BASE_URL']}/api/services/{domain}/{service}",
        headers={"Authorization": f"Bearer {os.environ['HA_LLAT']}",
                 "Content-Type": "application/json"},
        json=body, timeout=10.0,
    )
    audit("ha_call_service", args,
          result_code=str(r.status_code),
          duration_ms=int((time.monotonic() - t0) * 1000))
    return {
        "allowed": True, "domain": domain, "service": service,
        "target": target, "data": data,
        "ha_status": r.status_code,
        "ha_response": r.json() if r.headers.get("content-type", "").startswith("application/json") else None,
    }
```

### Confirmation hook (optional v1.1)

For high-blast-radius services like `cover.close_all` or `script.full_house_off`,
add a `requires_confirmation` flag to the per-service allowlist and
return `{"allowed": true, "pending_confirmation": true, ...}`. The LLM
then asks the user "Are you sure?" and re-issues the call with
`confirmed: true`. Keeping it out of v1 for simplicity.

## Tool 5 — `system_status`

Live system introspection. Calls the new containerized `homelab-tools`
service. Replaces the bare-metal Flask app and closes audit finding R-02.

### Input

```json
{
  "type": "object",
  "properties": {
    "scope": {
      "type": "string",
      "enum": ["containers", "ports", "volumes", "disk"],
      "default": "containers"
    },
    "lines": {
      "type": "integer", "minimum": 1, "maximum": 200, "default": 50,
      "description": "Only meaningful when paired with logs (future scope)."
    }
  }
}
```

### Output

```json
{
  "scope": "containers",
  "containers": [
    {"name": "openwebui", "image": "ghcr.io/.../open-webui:main",
     "status": "Up 2 hours (healthy)", "ports": "0.0.0.0:3000->8080/tcp"},
    …
  ]
}
```

### Implementation outline

```python
import httpx, os, time
from amarolab_common import audit, RateLimiter

ALLOWED_SCOPES = frozenset({"containers", "ports", "volumes", "disk"})

def system_status(scope: str = "containers", lines: int = 50) -> dict:
    t0 = time.monotonic()
    if scope not in ALLOWED_SCOPES:
        audit("system_status", {"scope": scope},
              allowed=False, result_code="bad_scope")
        return {"error": "bad scope", "code": "bad_scope"}

    if not RateLimiter.check("system_status", max_per_minute=30):
        return {"error": "rate limit", "code": "rate_limited"}

    base = os.environ["HOMELAB_TOOLS_URL"]
    r = httpx.get(f"{base}/{scope}", timeout=10.0)
    audit("system_status", {"scope": scope},
          duration_ms=int((time.monotonic() - t0) * 1000))
    r.raise_for_status()
    return r.json()
```

### `homelab-tools` API contract (the new container)

This is a small Python service (FastAPI recommended; ~80 LoC). All
endpoints return JSON. No auth — network isolation on
`ai-local_default` is the perimeter.

| Endpoint | Returns |
|----------|---------|
| `GET /containers` | list of running containers via docker-socket-proxy |
| `GET /ports` | host listening sockets (parsed from `ss -tlnp` snapshot — pre-baked from inside the container by mounting `/proc/net` read-only, or by maintaining a `homelab-tools` companion script on the host that posts updates) |
| `GET /volumes` | docker volumes (read-only via socket-proxy) |
| `GET /disk` | host disk usage (via a shared bind mount of `/proc` & `/sys`, or via a side-channel) |
| `GET /healthz` | `{"ok": true}` for compose healthcheck |

Note: "ports" and "disk" need careful design — a container can't see
host-side listening sockets natively. The pragmatic v1 design: have a
small host-side cron (e.g., every 60 s) write
`/srv/homelab/data/homelab-tools/ports.json` and
`/srv/homelab/data/homelab-tools/disk.json`, which the container reads
via bind mount. Less elegant than introspection but reliable and
unprivileged.

## Tool composition rules (in the system prompt)

The LLM gets these rules in the system prompt. They are belt-and-
braces — the tool code enforces them too, but telling the model
prevents wasted round-trips.

```
You have five tools. Use them; do not invent answers about state.

  rag_search(collection, query, k=6)
  audit_search(query, k=6)
  ha_get_state(entity_id | area | domain)
  ha_call_service(domain, service, target, data)
  system_status(scope)

Rules:
  1. Never assert a sensor value, container state, port number, or
     audit finding without a tool call.
  2. When you use rag_search or audit_search results, cite facts with
     [^N] and end your answer with a "[^N]: <source_rel>" list.
  3. ha_call_service: ONLY for domains in {light, switch, scene, cover,
     climate, media_player, script, automation, fan, vacuum,
     input_*}. Other domains will be refused; don't try them.
  4. If a tool returns "code": "...", surface that to the user
     verbatim. Do not retry the same call without changes.
  5. Prefer one targeted tool call over many broad ones. A search with
     a specific query beats five general ones.
  6. Routing hints:
       - "homelab", "container", "service", "audit" → likely needs
         system_status or audit_search or rag_search(homelab_docs).
       - "Guardian Cloud", "GC", "evidence", "recovery", "chunk upload"
         → rag_search(guardian_cloud).
       - "Ensambla2", "ensambla", "RBAC", "multitenancy"
         → rag_search(ensambla2).
       - "MyFreeTour" → tell the user the corpus is not yet indexed.
       - "what changed", "what was applied", "Phase 0/1", "R-XX"
         → audit_search.
       - "is the X on?", "what's the temperature in Y", "set the Z"
         → ha_get_state / ha_call_service.
```

## What is NOT a tool in v1

| Wanted-but-deferred | Why |
|---------------------|-----|
| `web_search` | No SearXNG / Brave integration; assistant is intentionally homelab-internal |
| `email_send` / `notify_send` | Out of scope; HA can already notify; no need for the assistant to do it directly |
| `git_pull` / `git_status` | Ingest service already handles its corpora; LLM should not control git |
| `shell_exec` | Hard veto — never |
| `eval_python` | Same — never |
| `read_file` / `write_file` | Same — the assistant reads via RAG, never via raw filesystem |

This list is in the design package on purpose: if a future you is
tempted to add a `shell_exec` tool because "it would be so handy", you
have the record of the decision to say no.
