# Phase A.1 — Tool-calling LLM pull — APPLIED

- **Date applied:** 2026-06-15
- **Scope of this sub-phase:** Pull the primary Amarolab Assistant
  model into Ollama and validate that it can emit native
  `tool_calls`. Nothing else from Phase A is done here — no Functions
  directory, no `amarolab_common.py`, no default-model setting in Open
  WebUI, no system prompt, no Home Assistant token. Strictly the model
  pull and its two exit criteria from
  [`../04_ai_system/amarolab-v1/05-implementation-roadmap.md`](../04_ai_system/amarolab-v1/05-implementation-roadmap.md)
  (Phase A, first work item).

## Decisions confirmed (from the user in this session)

| Knob | Value | Source |
|---|---|---|
| Primary tool-calling LLM | `qwen2.5:7b-instruct` (Q4_K_M, 4.7 GB) | Phase A architecture review delivered 2026-06-15 |
| Llama-3.0 (`llama3:latest`) | kept on disk as fallback general-chat model | same |
| Llama-3.1 / 8B-instruct backup pull | **not** done in A.1 | "Only complete Phase A.1" |
| Open WebUI default model | **not** changed in A.1 | "Do not modify Open WebUI Functions yet" |
| HA / Guardian Cloud | untouched | explicit rule each turn |

## What now exists on the host

```
/srv/homelab/data/ollama/models
└── qwen2.5:7b-instruct  (ID 845dbda0ea48, 4.7 GB on disk)
```

`docker exec ollama ollama list` after the pull:

```
NAME                   ID              SIZE      MODIFIED
qwen2.5:7b-instruct    845dbda0ea48    4.7 GB    10 minutes ago
llama3.2:latest        a80c4f17acd5    2.0 GB    3 months ago
phi3:latest            4f2222927938    2.2 GB    3 months ago
llama3:latest          365c0bd3c000    4.7 GB    3 months ago
```

Disk on `/` is 105 GB / 468 GB used (24 %). No other state was
modified: no containers recreated, no Open WebUI Functions directory
created, no environment variables added, no Qdrant collections
touched, no ingest config changed.

## Pre-conditions verified before the pull

| Check | Result |
|---|---|
| Ollama container `Up`, version `0.17.7` | yes |
| Disk free on `/` | 340 GB free, plenty for 4.7 GB pull |
| No model currently loaded | confirmed via `ollama ps` (empty) |
| RAM headroom for later smoke test | ~19 GiB available pre-pull (after resolving the unrelated VSCode EH bloat — see [`../INVESTIGATION_REPORT_VSCODE_MEMORY.md`](../../INVESTIGATION_REPORT_VSCODE_MEMORY.md)) |

## Pull execution

Command (verbatim from the roadmap):

```bash
docker exec ollama ollama pull qwen2.5:7b-instruct
```

Run in the background; completed cleanly (exit code 0). Pulled six
layers, largest is the 4.7 GB weights blob `2bada8a74506`. Manifest
written, `success` reported. Model immediately visible in
`ollama list`.

## Exit criteria from the roadmap

### Criterion 1 — model present

`docker exec ollama ollama list` shows `qwen2.5:7b-instruct` with ID
`845dbda0ea48`. ✓

### Criterion 2 — tool-calling smoke test

Sent the roadmap's canonical test prompt to Ollama with one inline
tool definition (`time_now`, no parameters). Stream off, sync JSON
response.

```bash
curl -s http://127.0.0.1:11434/api/chat -d '{
  "model": "qwen2.5:7b-instruct",
  "messages": [{"role":"user","content":"What time is it?"}],
  "tools": [{"type":"function","function":{
    "name":"time_now","description":"Get current time.",
    "parameters":{"type":"object","properties":{}}}}],
  "stream": false
}'
```

`.message.tool_calls`:

```json
[
  {
    "id": "call_xuqveg3e",
    "function": {
      "index": 0,
      "name": "time_now",
      "arguments": {}
    }
  }
]
```

`.message.content`: empty (model returned a tool call, not a
hallucinated time string). ✓

Timing:

| Phase | Value |
|---|---:|
| Cold load (`load_duration`) | 2.31 s |
| Prompt eval (139 tokens, system+tool+user) | small fraction |
| Generation (`eval_count` 16 tokens for the JSON tool call) | small fraction |
| **End-to-end wall clock** | **7 s** |
| Warm round-trip on a follow-up Spanish prompt | 1.85 s |

`ollama ps` immediately after:

```
NAME                   ID              SIZE     PROCESSOR    CONTEXT   UNTIL
qwen2.5:7b-instruct    845dbda0ea48    4.6 GB   100% CPU     4096      4m
```

CPU-only inference (no GPU on this host), `OLLAMA_KEEP_ALIVE` default
of 5 min holding the model warm.

## Memory observations

| Moment | Available RAM | Notes |
|---|---:|---|
| Before EH restart | 1.6 GiB | masked by the unrelated VSCode/ripgrep runaway (see investigation report) |
| After EH restart + VSCode settings fix | 20 GiB | clean baseline |
| With qwen2.5:7b warm | 15 GiB | model resident ~4.6 GB; matches design forecast (~5 GiB) |
| Headroom for reranker (Phase D) | ~14 GiB at peak | matches the [`01-current-state-review.md`](../04_ai_system/amarolab-v1/01-current-state-review.md) forecast |

Swap usage unchanged at ~1.4 GB pre-existing; no swap pressure
introduced by loading the model.

## Notes from the run

- The Spanish warm-path probe (`"Greet me in Spanish in one sentence."`
  → `"¡Hola! ¿Cómo estás?"`) renders inverted punctuation correctly
  and lands in 1.85 s. Independent confirmation of qwen2.5's
  multilingual quality — the architecture-review prediction held.
- Ollama loaded the model with `CONTEXT=4096` (its `num_ctx`
  default). The model itself supports much more (32 K natively, up to
  128 K with YaRN). For the v1 turn shape (system prompt + 5 tool
  schemas + reranked RAG chunks + chat history) 4 K will be tight.
  This is **not a Phase A.1 issue** — `num_ctx` can be raised
  per-request when tools are wired in Phases D–F, or set via a
  Modelfile. Flagging for future phases.
- No model currently has `tools` listed under "Capabilities" in
  `ollama show` for qwen2.5 either, but **native tool calling works
  end-to-end via the JSON `tools=[]` field on `/api/chat`** — the
  smoke test proves this. The "Capabilities" listing is informational
  and not authoritative for Qwen.
- The pull and the smoke test together took under one wall-clock
  minute of compute time (most of the elapsed time was the network
  download of the 4.7 GB blob).

## What is deliberately NOT done in A.1

- No Open WebUI Functions directory creation
  (`/srv/homelab/data/openwebui/functions/`).
- No `amarolab_common.py` helper drop.
- No Open WebUI admin change of default model.
- No `llama3.1:8b-instruct` backup pull.
- No system prompt drafting.
- No Home Assistant LLAT, no `.env` additions.
- No Qdrant collection changes.
- No `homelab-tools` container work.

These are the remaining items of Phase A and Phase B+ in the
implementation roadmap.

## Out-of-band fix landed alongside A.1

Resolved an unrelated VSCode Remote extension-host RAM bloat
(documented in
[`../../INVESTIGATION_REPORT_VSCODE_MEMORY.md`](../../INVESTIGATION_REPORT_VSCODE_MEMORY.md))
by writing
[`~/.vscode-server/data/Machine/settings.json`](../../.vscode-server/data/Machine/settings.json)
with `search.followSymlinks: false` plus `~/snap/**` and Steam Proton
`compatdata`/`dosdevices` excludes. Reclaimed ~7 GB at restart;
prevents recurrence. Outside the homelab repo and outside Amarolab's
scope, but documented here because it was a prerequisite for the
smoke test to have safe RAM headroom.

## Acceptance status

| Item | Status |
|---|---|
| Model pulled and present in `ollama list` | **PASS** |
| Tool-calling smoke test returns `tool_calls`, not hallucinated text | **PASS** |
| No untouched-area drift (HA, Guardian Cloud, Open WebUI Functions, Qdrant, ingest, repo) | **PASS** |
| Memory stays within forecast (~5 GiB model + ~14 GiB free) | **PASS** |

**Phase A.1 is complete.** Phase A continues with: Functions directory
+ `amarolab_common.py` scaffold + Open WebUI default-model setting
(remaining roadmap items in Phase A). Per the user's instruction, the
remaining Phase A items are **not** started in this session.

## Rollback

If qwen2.5 needs to be removed:

```bash
docker exec ollama ollama rm qwen2.5:7b-instruct
```

Removes only the weights; the other three models stay intact and
Ollama keeps running.
