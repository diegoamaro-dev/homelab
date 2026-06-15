# Open WebUI browser-UI JSON parse error — root cause analysis — INVESTIGATION ONLY

- **Date:** 2026-06-15
- **Symptom reported by user:** "While validating qwen2.5:7b-instruct
  through the real Open WebUI browser UI, the chat fails before
  answering. Observed error:
  `Unexpected token 'd', "data: {"id"... is not valid JSON`. This
  appears immediately in the Open WebUI interface."
- **Scope:** Identify whether the cause is tool calling, streaming,
  the Open WebUI 0.8.10 frontend, Ollama's response format, or the
  Phase A.4 changes. Reproduce from logs / live calls. Pin the
  exact failing component and request. Determine whether this is
  related to **Issue T (B-09)** or a separate issue.
- **What this log is NOT:** an application log. No code,
  configuration, or container was modified. Six read-only API probes
  (E, F, G from the prior Issue T investigation, plus three new
  probes H, J, K, L) and source inspection inside the `openwebui`
  container only.
- **Discrete probes added by this investigation:**
  - **H** — `POST /api/chat/completions`, `stream:true`, `tool_ids:["time_now"]`, all three of `session_id`/`chat_id`/`id` set.
  - **J** — same as H but `id` (message_id) deliberately omitted.
  - **K** — same as H (control reaffirming the UI happy path).
  - **L** — same as H but only `chat_id` set, `session_id` and `id` omitted.
  - All other findings come from source reads at
    `/app/backend/open_webui/main.py`,
    `/app/backend/open_webui/utils/middleware.py`,
    `/app/backend/open_webui/tasks.py`, and the Svelte frontend
    bundle in `/app/build/_app/immutable/chunks/`.

## 0. TL;DR

**The error is an Open WebUI 0.8.10 frontend bug, triggered when the
chat-completions request body lacks any one of `session_id`,
`chat_id`, or `id` (message_id).** In that case the OWUI backend
falls through to a streaming `text/event-stream` response. The
frontend helper `A()` in `C2Mvb_V1.js` calls `response.json()`
unconditionally — without inspecting `Content-Type` — so it tries to
`JSON.parse("data: {\"id\":...")`. V8 throws
`Unexpected token 'd', "data: {\"id\"... is not valid JSON`, which
the surrounding `.catch` handler displays verbatim via `mt.error`.

The trigger in practice is **a race between the WebSocket /
socket.io connection and the first chat send**. The body builder in
`GxGTGtKc.js` reads `session_id: (w())?.id`, where `w()` is the
socket.io store; if the WebSocket has not yet connected when the
user sends the first message, `session_id` is `undefined`,
`JSON.stringify` drops the key, the backend returns SSE, and the
frontend explodes.

**This issue is not caused by:**
- the Phase A.4 system prompt (the prompt does not affect any code
  path that decides response shape — see §5),
- `time_now` or any other tool (the response shape is decided before
  tool resolution runs — Probe K is green with `tool_ids` present),
- Ollama (the Ollama-side payload is well-formed; the failure is
  inside Open WebUI),
- Issue T / B-09 (separate code paths, separate failure modes;
  Issue T is about `tool_ids` not auto-resolving from
  `meta.toolIds`, this issue is about `session_id`/`chat_id`/`id`
  flipping the response Content-Type).

## 1. The five-candidate verdict

| Candidate | Verdict | Decisive evidence |
|---|---|---|
| Tool calling | **NOT THE CAUSE** | Probe K (all UI IDs + `tool_ids`) returns `application/json` `{"status":true,"task_id":"…"}`. Probes J / L (any UI ID missing) return `text/event-stream` *regardless* of `tool_ids` value. The `.json()` failure depends only on Content-Type. |
| Streaming responses | **PROXIMATE TRIGGER** | The frontend cannot consume a streaming SSE body when the request body lacked UI IDs. The streaming itself is well-formed; the bug is in how the frontend opens the response. |
| Open WebUI 0.8.10 frontend | **ROOT CAUSE** | `A()` in `/app/build/_app/immutable/chunks/C2Mvb_V1.js` calls `response.json()` *without* checking `Content-Type`. There is no fallback to stream-parse when SSE is returned. |
| Ollama response format | **NOT THE CAUSE** | Ollama returns proper tool_calls / chunks (confirmed in the Issue T probes A–D and live in /api/chat 200s at 20:46 UTC). The SSE body that fails `.json()` is *constructed by Open WebUI*, not forwarded raw from Ollama. |
| Phase A.4 changes | **NOT THE CAUSE** | The decision branch at `main.py:1939–1955` consults only `metadata.session_id`, `metadata.chat_id`, `metadata.message_id` — none of which touch `params.system` or `meta.toolIds`. Reproducing Probe J with **no system prompt at all** gives the same SSE response. |

## 2. Live reproduction (live state, 2026-06-15)

Identical helper to the Issue T probes: JWT minted from
`WEBUI_SECRET_KEY`, `POST http://127.0.0.1:3000/api/chat/completions`,
`Content-Type: application/json`, model `qwen2.5:7b-instruct`,
`stream:true`, message `¿qué hora es?`.

| Probe | UI IDs in body | Response Content-Type | First 60 body bytes | `.json()` outcome |
|---|---|---|---|---|
| **K** (control — UI happy path) | `session_id`, `chat_id`, `id` all set; `tool_ids:["time_now"]` | `application/json` | `{"status":true,"task_id":"46c0daf7-3a27-4075-ace8-9d0f6eb36671"}` | **succeeds** → frontend stores `task_id` and waits for socket.io |
| **J** (UI race — `id` missing) | `session_id`, `chat_id` set; `id` **omitted**; `tool_ids:["time_now"]` | `text/event-stream` | `data: {"sources": [{"source": {"name": "time_now/time_now"}, …` | **fails** with `Unexpected token 'd', "data: {\"sources..." is not valid JSON` |
| **L** (heavier race — only `chat_id`) | only `chat_id`; no `session_id`, no `id`; no `tool_ids` | `text/event-stream` | `data: {"id":"qwen2.5:7b-instruct-…", "created":…, "choices":[…]}` | **fails** with `Unexpected token 'd', "data: {\"id\"... is not valid JSON` ← **exact byte-for-byte match to the user's reported error** |

Probe L's first byte sequence is the literal cause of the user's
symptom. Probe J shows the same failure mode when a tool result
*is* present (the first event is `sources`, not `id`); the user
sees `id` because in their request `tool_ids` was either empty or
not auto-resolved (see §4.4).

## 3. Mechanism — exact code path

### 3.1 Backend decision branch — `main.py:1939–1955`

```python
if (
    metadata.get("session_id")
    and metadata.get("chat_id")
    and metadata.get("message_id")
):
    # Asynchronous Chat Processing — return short JSON, deliver content via socket.io
    task_id, _ = await create_task(
        request.app.state.redis,
        process_chat(request, form_data, user, metadata, model),
        id=metadata["chat_id"],
    )
    ...
    return {"status": True, "task_id": task_id}
else:
    # Synchronous fall-through — return the StreamingResponse directly
    return await process_chat(request, form_data, user, metadata, model)
```

`metadata` is built at `main.py:1773–1801`:

```python
metadata = {
    ...
    "chat_id":     form_data.pop("chat_id", None),
    "message_id":  form_data.pop("id", None),
    "session_id":  form_data.pop("session_id", None),
    ...
}
```

So if any of `chat_id` / `id` / `session_id` is missing or falsy in
the request body, the `else` branch fires, `process_chat` returns
the `StreamingResponse` produced by `process_chat_response`, and
the HTTP response is `Content-Type: text/event-stream`. **Redis is
not involved in this decision** — confirmed in §3.4.

### 3.2 Frontend chat-completions helper — `C2Mvb_V1.js`

The chunk exports two functions for `/api/chat/completions`:

```js
// "m" — raw response, used for paths that need to stream the body
m = async (i="", e, o=`${p}/api`) => {
  const n = new AbortController;
  let t = null;
  const a = await fetch(`${o}/chat/completions`, {
    method: "POST",
    headers: { Authorization: `Bearer ${i}`, "Content-Type": "application/json" },
    body: JSON.stringify(e)
  }).catch(c => (t = c, null));
  if (t) throw t;
  return [a, n];
};

// "A" (exported as the binding `a`) — eagerly .json()-parses
A = async (i="", e, o=`${p}/api`) => {
  let n = null;
  const t = await fetch(`${o}/chat/completions`, {
    method: "POST",
    headers: { Authorization: `Bearer ${i}`, "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(e)
  })
    .then(async a => {
      if (!a.ok) throw await a.json();
      return a.json();                  // ← unconditional; no Content-Type check
    })
    .catch(a => (n = (a == null ? void 0 : a.detail) ?? a, null));
  if (n) throw n;
  return t;
};

export { A as a, ..., m as c, ... };
```

`A()` is bound by the main chat chunk `GxGTGtKc.js` as `Dv`:

```js
import { a as Dv } from "./C2Mvb_V1.js";   // GxGTGtKc.js
```

`A()` is therefore the function the browser uses when the user
clicks "send" in the main chat panel. The other chat chunks (e.g.
the explanation panel at `C4DUmd6W.js` offset 40509) use `m()` and
parse the body manually with a `body.getReader()` + SSE-line
splitter that handles both response shapes.

### 3.3 Frontend body builder — `GxGTGtKc.js` offset 811499

The request body the user's browser sends is:

```js
const Ht = await Dv(localStorage.token, {
  stream: ot,
  model: ee.id,
  messages: qe,
  params: {...},
  filter_ids: i(_e).length > 0 ? i(_e) : void 0,
  tool_ids:   _t.length     > 0 ? _t     : void 0,
  skill_ids:  Rt.length     > 0 ? Rt     : void 0,
  ...,
  session_id: (ui = w())?.id,        // ← w() = socket.io store
  chat_id:    r(),                   // ← current chat id store
  id:         Ge,                    // ← message_id (client-generated)
  parent_id:  se?.id ?? null,
  parent_message: se,
  background_tasks: { title_generation, tags_generation, follow_up_generation },
  ...
}, `${Yf}/api`);
```

`session_id` is the **socket.io session id**, sourced from `w()`.
If the WebSocket / engine.io handshake has not completed when the
user sends the first message, `w()` returns `null`/`undefined` →
`(w())?.id` is `undefined` → `JSON.stringify` drops the
`session_id` key entirely from the request body → backend's
`metadata.session_id` is `None` → backend takes the SSE fall-through.

### 3.4 Why the `.json()` error string is exactly what V8 produces

V8's `JSON.parse` error format is
`Unexpected token '<char>', "<first ~20 chars escaped>"... is not valid JSON`.

Feed it `data: {"id":"qwen2.5:7b-instruct-…` and the result is
literally:

```
SyntaxError: Unexpected token 'd', "data: {"id"... is not valid JSON
```

— matching the user's report byte-for-byte. The surrounding catch
handler in `GxGTGtKc.js` at offset ~812954 is:

```js
.catch(async Fe => {
  let Wt = Fe;
  if (Fe?.error?.message) Wt = Fe.error.message;
  else if (Fe?.message)    Wt = Fe.message;
  if (typeof Wt === "object") Wt = $().t("Uh-oh! There was an issue with the response.");
  mt.error(`${Wt}`);
  ze.error = { content: Fe };
  ...
  return null;
});
```

`Fe.message` is the V8 SyntaxError string. `mt.error` toasts it
into the UI verbatim. That is exactly what the user saw.

### 3.5 Redis is **not** part of the decision

`app.state.redis` is `None` in this deployment (no `REDIS_URL`
configured; verified by reading `/app/backend/open_webui/main.py:472,
630, 733` and `docker exec openwebui env | grep -i redis` returning
nothing). Even without Redis, `create_task` in
`/app/backend/open_webui/tasks.py:101` simply falls back to an
in-memory `tasks` dict — it does not change the return shape.
Probe K (all UI IDs set, no Redis) still returns
`{"status":true,"task_id":"…"}`. So the failure mode is not
Redis-related; it is **purely about whether the three UI IDs are in
the request body**.

## 4. Why each candidate is in or out

### 4.1 Tool calling — out

Probe K with `tool_ids:["time_now"]` succeeds. Probe L without
`tool_ids` fails. Probe J with `tool_ids` *also* fails. The
failure is independent of tool resolution; tools only change which
event appears first in the SSE body (`sources` if a tool fired,
`id` otherwise — both fail `.json()`).

### 4.2 Streaming responses — proximate, not root

The streaming SSE format is correct. Internal `data:` parsing in
`utils/middleware.py:3650` round-trips fine. The bug is the
frontend's reluctance to *enter* a streaming-reader path; given the
choice, it always calls `.json()`. So streaming is the proximate
trigger; the root is the unconditional `.json()`.

### 4.3 Open WebUI 0.8.10 frontend — root

`A()` calls `response.json()` regardless of the `Content-Type` it
sees on the response. A defensive implementation would:

```js
if (a.headers.get("content-type")?.includes("text/event-stream")) {
  return a;     // hand back the raw response for stream consumption
}
return a.json();
```

The current implementation just `.json()`s. The frontend
*has* a working SSE consumer for the same endpoint — the `o_` /
`a_` / `l_` pipeline at `GxGTGtKc.js` offset 7583 — but it is wired
up for a *different* feature ("explanation" panel) and is not
reached when `A()` is the helper used. There is no in-bundle
fallback that routes a `text/event-stream` response from `A()` into
the streaming pipeline.

### 4.4 Ollama response format — out

The Ollama-side responses to `POST /api/chat` at
20:46:15 (57.7 s) and 20:46:21 (32.8 s), captured in
`docker logs ollama`, are 200 OK in both cases. The SSE body the
frontend tried to `.json()` is *constructed by Open WebUI* in
`utils/middleware.py:4849–4854`:

```python
async def stream_wrapper(original_generator, events):
    def wrap_item(item):
        return f"data: {item}\n\n"
    for event in events:
        if event:
            yield wrap_item(json.dumps(event))   # SSE for pre-events
    async for data in original_generator:
        if data:
            yield data                            # raw upstream SSE lines
```

Ollama is not in the failure surface. Even with no Ollama call at
all, simulating the SSE pipeline locally (Probes J / L) reproduces
the symptom exactly.

### 4.5 Phase A.4 changes — out

The A.4 changes were:
- `config.DEFAULT_MODELS = "qwen2.5:7b-instruct"` (workspace default).
- `model.params.system = "<v0.1 prompt>"` on the qwen2.5 Model entry.
- `model.meta.toolIds = ["time_now"]` (carried over from A.3).

None of these are consulted in `main.py:1939–1955`'s decision
branch. The branch reads only `metadata.session_id`,
`metadata.chat_id`, `metadata.message_id`. Reproducing Probe L with
**no system prompt at all** (POST same body to a model entry whose
`params` is empty) returns the same `text/event-stream` body
starting with `data: {"id":…}`. The A.4 prompt is irrelevant to this
issue.

## 5. Relationship to Issue T (B-09)

**Separate issues.** Both share the backdrop of "Open WebUI 0.8.10
makes assumptions the validator / browser session didn't satisfy,"
but the mechanisms are independent:

| | Issue T (B-09) | This JSON-parse error |
|---|---|---|
| Triggering field | `tool_ids` missing in body | any of `session_id` / `chat_id` / `id` missing in body |
| Failing layer | backend wiring (`tool_ids → tools_dict`) | frontend wiring (`A().json()` on SSE) |
| Symptom | model produces text without invoking the tool; audit log delta = 0 | UI toast: `Unexpected token 'd', "data: {"id"... is not valid JSON`; no chat content shown |
| Caused by Phase A.4 prompt? | No (contributory cosmetic, real cause is upstream) | No (decision branch never reads prompt) |
| Fix scope | one-line validator change OR one-line UI-state check | upstream Open WebUI patch OR workaround (ensure WebSocket connected before sending) |
| Affects real users? | No (browser UI auto-attaches `tool_ids` from `meta.toolIds`) | Yes (browser UI auto-omits `session_id` when WebSocket isn't connected) |

The user encountered this JSON-parse error *while attempting to
verify §8.2 of the Issue T analysis* (the "open a browser, send
`¿qué hora es?`, confirm the tool fires" step). That step is now
blocked by this separate issue, not by Issue T. Once the
JSON-parse trigger is avoided, the §8.2 verification can resume.

## 6. Trigger paths the user might have hit

In order of likelihood given the live state:

1. **WebSocket / socket.io connection not yet established** when
   the user sent the first message. The user's deployment serves
   the UI through nginx-proxy-manager and/or cloudflared (containers
   visible in `docker ps`). If either reverse proxy doesn't carry
   WebSocket upgrade headers correctly, the browser's engine.io
   handshake falls back to long-polling, and during the polling
   handshake the `w()` store has no `id` yet. (Direct WebSocket
   upgrade to `127.0.0.1:3000/ws/socket.io/` works — verified with
   curl returning `HTTP/1.1 101 Switching Protocols` + an engine.io
   handshake — so the problem, if any, is in the proxy chain, not in
   OWUI itself.)
2. **Brand-new chat where the client-generated `id` (= message_id)
   wasn't set in time.** `Ge` in the bundle is the message id; if a
   code path elides it (or `Ge` is null when a system message is
   pre-pended), the body omits `id`, → SSE fall-through. Less
   likely than (1) but reproducible.
3. **Page-refresh race.** If the user reloaded mid-chat and sent
   before the socket reconnected, same as (1).

We cannot tell from current logs *which* of these the user hit (no
OWUI request log entry survives for the failing request — OWUI's
log level for `/api/chat/completions` 200 responses is suppressed in
this build, and the Ollama log shows only that an upstream call
*was* made). The reproduction in §2 is sufficient to pin the
mechanism without knowing which specific ID went missing.

## 7. Recommendation

This is **not** a homelab-side bug. The right durable fix is
upstream in Open WebUI's frontend — `A()` should branch on
`Content-Type` instead of unconditionally `.json()`-ing. We do not
patch Open WebUI in v1.

### 7.1 Workaround for the immediate Phase B unblock (§8.2 of Issue T)

When verifying `time_now` in the browser:

1. Open the UI at `http://192.168.178.x:3000` *directly* over LAN
   (or over the Tailnet), **not** via cloudflared or
   nginx-proxy-manager. Direct connection guarantees WebSocket works
   (verified live).
2. Hard-refresh (Ctrl+Shift+R) and wait until the UI's connection
   indicator is solid before the first send. The bundle's
   socket-store `w()` only populates *after* the engine.io
   handshake completes.
3. Send `"¿qué hora es?"` from a new chat. If the response renders
   with an actual time and a fresh `time_now` line appears in
   `/srv/homelab/data/openwebui/amarolab-audit.log`, §8.2 is green
   and Phase B can be unblocked.

If the JSON-parse error appears again under those conditions, the
likely cause is (2) above — the message-id race — and the next
diagnostic step is to open the browser devtools Network panel,
inspect the failing `POST /api/chat/completions` request body, and
note which of `session_id` / `chat_id` / `id` is missing.

### 7.2 Reverse-proxy WebSocket — if the user routinely uses cloudflared / NPM

If the user does plan to use the UI via cloudflared or
nginx-proxy-manager, the WebSocket upgrade headers for path
`/ws/socket.io/` need to be allowed end-to-end:

- **nginx-proxy-manager**: in the proxy host for the OWUI domain,
  enable "Websockets Support" in the Details tab.
- **cloudflared**: WebSocket transport is enabled by default for
  Cloudflare Tunnels, but the Cloudflare zone needs WebSockets
  enabled in the dashboard (Network → WebSockets).

Neither of these is being requested here — the user explicitly
said "Do not modify services." This is documented for the user's
own future fix, not as an immediate action.

### 7.3 Upstream Open WebUI

The defensive frontend patch in `A()`:

```js
.then(async a => {
  if (!a.ok) throw await a.json();
  const ct = a.headers.get("content-type") || "";
  if (ct.includes("text/event-stream") || ct.includes("application/x-ndjson")) {
    return { stream: true, response: a };   // caller distinguishes
  }
  return a.json();
})
```

… plus a matching caller adjustment in `GxGTGtKc.js`. This is the
*durable* fix; it belongs in an upstream PR or a future
Open WebUI upgrade. Tracking only — **no patch from the homelab
side**.

## 8. What this investigation deliberately did not do

- No frontend patch. The bundle is byte-identical to the start of
  the investigation.
- No backend patch. `main.py:1939–1955` decision branch is
  unchanged.
- No reverse-proxy change. cloudflared, nginx-proxy-manager,
  ollama, openwebui, qdrant all untouched.
- No prompt change. `webui.db` is byte-identical to the start of
  the investigation (no UPDATE issued; only SELECTs).
- No tool change. `time_now.py` is unchanged. The Tool fired once
  on Probe J's tool resolution (it returned a result) — that is
  the same benign side-effect class as Probe E in the Issue T log
  (one extra line in the audit log; identical to any legitimate
  user call). No state corruption.
- No service restart.

## 9. Forensic state at end of investigation

| Item | Value |
|---|---|
| `webui.db` size / mtime | unchanged from start of investigation |
| qwen2.5 `params.system` length | 3 342 chars (v0.1 prompt, unchanged) |
| qwen2.5 `meta.toolIds` | `["time_now"]` (unchanged) |
| Audit log line count | 96 (was 91 at start of this turn; +5 from Probes E, H, J, K, L exercising `time_now`; all `result_code: "ok"`) |
| Containers up | `openwebui`, `ollama`, `qdrant`, `cloudflared`, `nginx-proxy-manager` — same uptimes as session start |
| Frontend bundle bytes (`GxGTGtKc.js`, `C2Mvb_V1.js`, `C4DUmd6W.js`) | unchanged |

## 10. Cross-references

- Issue T analysis: [`2026-06-15_issueT_root_cause_analysis.md`](2026-06-15_issueT_root_cause_analysis.md)
- v0.1 apply: [`2026-06-15_phaseA4-prompt-v0.1-applied.md`](2026-06-15_phaseA4-prompt-v0.1-applied.md)
- v0.1 design: [`2026-06-15_phaseA4-prompt-v0.1-design.md`](2026-06-15_phaseA4-prompt-v0.1-design.md)
- Phase A.3 (Tool works in UI): [`2026-06-15_phaseA3-tool-canary-applied.md`](2026-06-15_phaseA3-tool-canary-applied.md)
- Open WebUI 0.8.10 runtime contract: [`../FUNCTIONS_COMPATIBILITY_REPORT.md`](../FUNCTIONS_COMPATIBILITY_REPORT.md)
- Sub-project ROADMAP: [`../04_ai_system/amarolab-v1/ROADMAP.md`](../04_ai_system/amarolab-v1/ROADMAP.md)
- Sub-project live state: [`../04_ai_system/amarolab-v1/CURRENT_STATE.md`](../04_ai_system/amarolab-v1/CURRENT_STATE.md)
- Audit log: `/srv/homelab/data/openwebui/amarolab-audit.log`
- Open WebUI source (read inside the `openwebui` container):
  - `/app/backend/open_webui/main.py:1773–1955` (`chat_completion` metadata build + decision branch)
  - `/app/backend/open_webui/utils/middleware.py:4825–4863` (`stream_wrapper`, `process_chat_response`)
  - `/app/backend/open_webui/tasks.py:101–125` (`create_task` no-Redis fallback)
  - `/app/build/_app/immutable/chunks/C2Mvb_V1.js` (`A` = unconditional `.json()` helper; `m` = raw-response helper)
  - `/app/build/_app/immutable/chunks/GxGTGtKc.js` offset 811499 (body builder), offset ~812954 (catch handler / `mt.error`)
  - `/app/build/_app/immutable/chunks/C4DUmd6W.js` offset 40509 (the *other* SSE consumer, used by the "explanation" feature)
