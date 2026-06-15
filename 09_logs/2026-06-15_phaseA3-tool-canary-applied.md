# Phase A.3 — Open WebUI Tools scaffold + `time_now` canary — APPLIED

- **Date applied:** 2026-06-15
- **Implements:** the revised plan in
  [`2026-06-15_phaseA3-tool-canary-design.md`](2026-06-15_phaseA3-tool-canary-design.md).
- **Driven by:** locked decisions D-18 … D-26.
- **Scope:** the canary Tool only (`time_now`). No `rag_search`,
  no `system_status`, no Home Assistant, no Guardian Cloud, no
  Open WebUI default-model change.

## What now exists on the host

### Source tree (homelab git repo, version-controlled)

```
/home/diego/homelab/ai-stack/openwebui-tools/
├── README.md                            # workflow doc
├── tools/
│   └── time_now.py                      # Open WebUI Tool, class Tools shape
├── lib/
│   └── audit_helper.py                  # canonical helper text, inlined at install
└── bin/
    ├── install_tool                     # inline + JWT mint + POST /api/v1/tools/create|update
    └── dump_tools                       # GET each Tool from webui.db → ./tmp/<id>.dumped.py
```

Modes: 0664 for `.py` and `.md`, 0755 for `bin/*`. Owner `diego:diego`.

### Runtime state inside `webui.db`

- Tool row: `id="time_now"`, `name="Amarolab time_now"`,
  `user_id=3a49344e-acf6-41a1-b28d-8cce95c36c2a` (diego), content
  length 5180 chars (helper inlined), specs count 1.
- Spec built by Open WebUI's `get_tool_specs`: one function `time_now`
  with two parameters (`timezone` string default `Europe/Madrid`,
  `format` enum `["iso","human","unix"]` default `iso`).

### Per-model scoping (D-20)

- New Model entry created in `webui.db`:
  `id=qwen2.5:7b-instruct`, `base_model_id=qwen2.5:7b-instruct`,
  `meta.toolIds=["time_now"]`, `meta.description="Amarolab primary
  tool-calling LLM. Tools scoped to this model only (D-20)."`,
  `is_active=true`.
- No Model entries exist for `llama3:latest`, `llama3.2:latest`,
  or `phi3:latest` — they remain unscoped pass-through models, and
  inherit no Tools.

### Audit log on host

- Path: `/srv/homelab/data/openwebui/amarolab-audit.log` (D-21).
- Created on first Tool call (2026-06-15 17:24 CEST).
- Final state at end of A.3 validation: 90 JSONL lines, 21 767 bytes.
- Owner `root:root` (container writes as root via the bind mount).
  Group/mode hardening + logrotate is Phase E.

### Authentication path used by `install_tool`

`install_tool` reads `WEBUI_SECRET_KEY` from
`/home/diego/homelab/ai-stack/.env`, mints a JWT
(`{"id": "<diego user_id>", "jti": "<uuid>"}`, HS256, same algorithm
Open WebUI itself uses in `utils/auth.py:create_token`), and posts
Bearer-authenticated to `/api/v1/tools/create` (or `.../update`). No
interactive password prompt; no Open WebUI API-key feature flag
required.

## Validation outcomes

All 21 criteria from the design plan ran. Summary:

| # | Check | Result |
|---|---|---|
| V-1 | Directory tree created | PASS |
| V-2 | Files present, modes correct | PASS |
| V-3 | `tools/time_now.py` + `lib/audit_helper.py` parse cleanly | PASS |
| V-4 | `bin/install_tool` + `bin/dump_tools` parse cleanly | PASS |
| V-5 | Install round-trip: `install_tool` POSTs, returns `id=time_now action=create` | PASS |
| V-6 | Tool visible in `GET /api/v1/tools/` list | PASS |
| V-7 | `GET /api/v1/tools/id/time_now` returns 1 spec with correct shape (params `timezone` + `format`, enum `[iso,human,unix]`, default `Europe/Madrid`) | PASS |
| V-8 | `dump_tools` round-trip diff against inlined source = clean (modulo one trailing newline stripped by Open WebUI) | PASS |
| V-9 | Per-model scoping (D-20): only `qwen2.5:7b-instruct` has `toolIds=["time_now"]`; other models have no Model entry | PASS |
| V-10 | Happy path: *"What time is it?"* → `"The current time is 17:24 CEST on Monday, 15 June 2026 [1]."` — correct real date, citation marker present | PASS |
| V-11 | Non-default timezone: *"What time is it in Tokyo?"* → `"Tuesday 16 June 2026, 00:25 JST"` (correct CEST→JST conversion) | PASS |
| V-12 | Format variant: *"Use time_now with format unix"* → `1781537160` (correct epoch) | PASS |
| V-13 | Scoping: same prompt to `llama3:latest` with no `tool_ids` → no tool call, model answered from memory ("I don't have a physical presence…") | PASS |
| V-14 | Bad timezone (`Atlantis/Lost`): tool returned `{"error":"unknown timezone","code":"bad_tz",...}` and the LLM surfaced the JSON verbatim | PASS |
| V-15 | Rate limit: 80 direct invocations in a tight loop → exactly 60 OK, 20 `rate_limited` (matches `Valves.max_per_minute=60`) | PASS |
| V-16 | Audit log file created at the expected host path | PASS |
| V-17 | First audit line has all 8 fields (`ts`, `id`, `user`, `tool`, `args`, `allowed`, `result_code`, `duration_ms`) | PASS |
| V-18 | Redaction (D-26 helper): synthetic call with `password="hunter2"` + nested `{"token":"shhh"}` → both rendered as `"<redacted>"` in the audit line | PASS |
| V-19 | Concurrent writes: 5 parallel chat completions produced 5 new audit lines, zero malformed JSON | PASS |
| V-20 | openwebui container RSS went from ~26 MiB idle to ~400 MiB after ~10 chat completions + 80 direct calls. Dominated by chat-handling buffers and Open WebUI's caches — the Tool itself adds ~10–20 MiB (pydantic already loaded; `zoneinfo`/stdlib are negligible). Well within the 29 GiB envelope | INFO (no regression) |
| V-21 | Static check of the inlined Tool source for network imports (`socket`, `urllib`, `httpx`, `requests`, `aiohttp`, `http.client`, …) → none found | PASS |

End-to-end timing observations (informational):

| Path | Latency |
|---|---|
| Cold load on first tool-calling chat (Ollama loads qwen2.5 from disk) | ~29 s |
| Warm tool-calling chat (model resident) | ~5–7 s for a one-line answer |
| Tool method itself (excl. LLM) | 10–14 ms median (see audit `duration_ms`) |

## Notes from the run

- The first `install_tool` invocation surfaced `specs=0` in its
  stdout, which initially looked wrong; this is a side effect of the
  `POST /api/v1/tools/create` response using `ToolResponse` (which
  omits `specs`) rather than `ToolUserResponse`. A subsequent
  `GET /api/v1/tools/id/time_now` confirmed `specs` were generated
  and stored.
- Open WebUI's tool-call execution does not surface a `tool_calls`
  array in the final chat-completions response payload — by the
  time the response returns, the tool has already been run and the
  LLM has produced its natural-language answer based on the tool
  result. The audit log is the canonical record that a tool fired.
- The Phase 1.5 `[N]` citation marker mechanism in Open WebUI
  surfaced automatically without us having to enable it. This is a
  pleasant side effect; we'll lean on it for `rag_search` in Phase B.
- `zoneinfo` ships with Python 3.11; the openwebui container has
  Python 3.11. No external `tzdata` package needed.
- Per-process rate limiter is exact (60/min → exactly 60 ok). Will
  reset on openwebui container restart; documented in
  `lib/audit_helper.py`.
- Audit log ownership is `root:root` because the openwebui container
  process runs as root and the bind mount preserves uid 0 inside.
  Hardening (mode 0640, logrotate, ownership remap) is Phase E.

## What is **not** done in A.3

- No `rag_search.py` (Phase B).
- No `audit_search.py` (Phase B).
- No `system_status.py` and no `homelab-tools` container (Phase D, per D-18).
- No Home Assistant tools (Phase C).
- No Open WebUI default-model change (Phase A.4 — currently the user
  still has to explicitly pick `qwen2.5:7b-instruct` from the model
  dropdown).
- No system prompt for the assistant (Phase A.4).
- No logrotate for `amarolab-audit.log` (Phase E).
- No new env var in `.env` (the JWT mint reads `WEBUI_SECRET_KEY`,
  which was already present from Phase 0).

## Rollback (untested but trivial)

Source side:

```bash
rm -rf /home/diego/homelab/ai-stack/openwebui-tools/
```

DB side:

```bash
TOKEN=$(python3 -c "import jwt,uuid;
secret=open('/home/diego/homelab/ai-stack/.env').read().split('WEBUI_SECRET_KEY=')[1].split()[0]
print(jwt.encode({'id':'3a49344e-acf6-41a1-b28d-8cce95c36c2a','jti':str(uuid.uuid4())}, secret, algorithm='HS256'))")
curl -s -X DELETE -H "Authorization: Bearer $TOKEN" \
  http://127.0.0.1:3000/api/v1/tools/id/time_now/delete
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  http://127.0.0.1:3000/api/v1/models/model/delete?id=qwen2.5:7b-instruct
```

Audit log: leave for forensics, or `rm
/srv/homelab/data/openwebui/amarolab-audit.log` if rolling back
fully.

## Acceptance status

- V-1..V-19 all PASS; V-20 informational (no regression); V-21 PASS.
- Live-state docs updated in the same turn that wrote this log
  (`AMAROLAB_HANDOFF.md`, `CURRENT_STATE.md`, `ROADMAP.md`).
- **Phase A.3 is complete.** Next sub-phase per
  [`../04_ai_system/amarolab-v1/ROADMAP.md`](../04_ai_system/amarolab-v1/ROADMAP.md):
  **A.4 — Open WebUI default model + system prompt v0**.
