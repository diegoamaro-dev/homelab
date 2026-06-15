# CURRENT_STATE — Amarolab Assistant v1

Last updated: 2026-06-15 (Phase A.4 v0.1 application result)

Scope: live state of the Amarolab Assistant v1 sub-project. For
homelab-wide state see
[`../../00_overview/CURRENT_STATE.md`](../../00_overview/CURRENT_STATE.md).

## What is running

| Component | Container / process | Status | Endpoint |
|---|---|---|---|
| Open WebUI | `openwebui` | Up, healthy, 15h+ | `:3000` (host network) |
| Ollama | `ollama` | Up, 15h+; version 0.17.7 | `:11434` |
| Qdrant | `qdrant` | Up, 15h+; API key enforced | `:6333` |
| RAG ingest | host cron `02:30 *`, user `diego` | Active | bare-metal venv at `/home/diego/homelab/ai-stack/ingest/venv` |
| Embedding cache | (no process) | Populated | `/srv/homelab/data/openwebui/cache/embedding/models/` |

From the v1 design, the following is now in place after Phase A.3
(2026-06-15): one Open WebUI Tool installed in `webui.db`
(`time_now`), scoped to `qwen2.5:7b-instruct` only via a custom Model
entry, audit log writing one JSONL line per call to
`/srv/homelab/data/openwebui/amarolab-audit.log`. Still missing:
**no** `rag_search` or `audit_search` (Phase B), **no** HA tools
(Phase C), **no** `homelab-tools` container or `docker-socket-proxy`
(Phase D), **no** containerized ingest service (deferred).

## What is implemented

### Models in Ollama
| Model | ID | Size | Role |
|---|---|---:|---|
| `qwen2.5:7b-instruct` | `845dbda0ea48` | 4.7 GB | **primary** (tool-calling) — pulled Phase A.1 |
| `llama3:latest` (Llama 3.0 8B Q4_0) | `365c0bd3c000` | 4.7 GB | fallback non-tool chat |
| `llama3.2:latest` | `a80c4f17acd5` | 2.0 GB | leftover from earlier experiments |
| `phi3:latest` | `4f2222927938` | 2.2 GB | leftover from earlier experiments |

Disk for the models cache: 8.3 GB of /srv/homelab/data/ollama/models.

### Qdrant collections (4 active, 1 pending)
| Collection | Source | Chunks | Files | Status |
|---|---|---:|---:|---|
| `homelab_docs` | `/home/diego/homelab` | 86 | 15 | Active |
| `guardian_cloud` | `/mnt/storage/projects/guardian-cloud` | 872 | 56 | Active |
| `ensambla2` | `/mnt/storage/projects/ensambla2` | 419 | 48 | Active |
| `myfreetour` | TBD | 0 | 0 | Placeholder, disabled |
| `infra_audits` | `/home/diego/server-audit-2026-06-13` | — | — | **Phase B (not created)** |

Dimensionality: 384 (multilingual-e5-small). Distance: cosine.
Payload indexes on `collection`, `source_kind`, `source_rel`.

### Tool layer
**`time_now` shipped** (Phase A.3, 2026-06-15). Canonical source at
`/home/diego/homelab/ai-stack/openwebui-tools/tools/time_now.py`;
runtime copy in `webui.db` (5180 chars, 1 spec). Scoped to
`qwen2.5:7b-instruct` only (D-20) via a Model entry with
`meta.toolIds=["time_now"]`. End-to-end smoke + error + concurrency
validated.

`rag_search`, `audit_search`, `system_status`, `ha_get_state`,
`ha_call_service` are designed only — see Phase A.2 design log
([`../../09_logs/2026-06-15_phaseA2-tool-layer-design.md`](../../09_logs/2026-06-15_phaseA2-tool-layer-design.md))
and Phase A.3 applied log
([`../../09_logs/2026-06-15_phaseA3-tool-canary-applied.md`](../../09_logs/2026-06-15_phaseA3-tool-canary-applied.md)).

### Environment / configuration
| Knob | Value | Where |
|---|---|---|
| `QDRANT__SERVICE__API_KEY` | (64 hex) | `/home/diego/homelab/ai-stack/.env` (0600 diego:diego) |
| `QDRANT_API_KEY` | (same) | same file |
| `WEBUI_SECRET_KEY` | (64 hex) | same file |
| `HA_BASE_URL`, `HA_LLAT` | **not set** | reserved for Phase C |
| `HOMELAB_TOOLS_URL` | **not set** | reserved for system_status backing service |
| `AMAROLAB_AUDIT_LOG` | **set** (live since Phase A.3) | inlined in each Tool; on host at `/srv/homelab/data/openwebui/amarolab-audit.log` |
| Open WebUI workspace `DEFAULT_MODELS` | `"qwen2.5:7b-instruct"` | `config.DEFAULT_MODELS` in `webui.db` (set Phase A.4 v0 apply 2026-06-15) |
| `qwen2.5:7b-instruct` per-model `params.system` | **v0.1 prompt, 3 342 chars** | `model.params.system` in `webui.db`; persona + tool routing + refusals. See log set in §"Pending in Phase A" below for the open regression on this prompt. |

## What is validated

| Item | Method | Result | Date |
|---|---|---|---|
| `qwen2.5:7b-instruct` is present | `docker exec ollama ollama list` | ID `845dbda0ea48`, 4.7 GB | 2026-06-15 |
| `qwen2.5:7b-instruct` emits native `tool_calls` | Roadmap smoke test (curl with `time_now` inline tool, `stream:false`) | `.message.tool_calls = [{name:"time_now", arguments:{}}]`, `.message.content` empty | 2026-06-15 |
| `qwen2.5:7b-instruct` cold load time | First `/api/chat` call | `load_duration` 2.31 s; total 7 s end-to-end | 2026-06-15 |
| `qwen2.5:7b-instruct` warm path | Spanish prompt round-trip | "¡Hola! ¿Cómo estás?" in 1.85 s | 2026-06-15 |
| RAM forecast at peak | `free -h` with model warm | Model resident ~4.6 GB; 15 GiB free remaining | 2026-06-15 |
| RAG dense retrieval correctness | Phase 1 sample queries (top-1 expected) | All top-1 correct; scores 0.81–0.89 | 2026-06-14 |
| Reranker uplift on guardian_cloud benchmark | Phase 1.5 evaluation harness | Top-6 lifted from 80% to ≥ 95% | 2026-06-14 |
| Ingest scheduling | cron + log file | Daily 02:30 entries in `ingest.log` | 2026-06-14 |
| Audit-log format and path | **Designed**, not yet written by code | No on-disk validation possible until Phase A.3 | — |

## What is pending

### Pending in Phase A (current)
- Phase A.2 — **APPROVED 2026-06-15**. Five locked decisions
  (D-18..D-22 in [`ROADMAP.md`](ROADMAP.md)).
- Open WebUI 0.8.10 compatibility audit complete 2026-06-15;
  see [`../../FUNCTIONS_COMPATIBILITY_REPORT.md`](../../FUNCTIONS_COMPATIBILITY_REPORT.md).
- Phase A.3 — **APPLIED 2026-06-15**. `time_now` canary live in
  `webui.db`; per-model scoping in place; audit log writing.
  Evidence: [`../../09_logs/2026-06-15_phaseA3-tool-canary-applied.md`](../../09_logs/2026-06-15_phaseA3-tool-canary-applied.md).
- Phase A.4 v0 — **APPLIED 2026-06-15**. `DEFAULT_MODELS` set;
  persona-only system prompt landed on the qwen2.5 Model entry.
  13/17 validation PASS; 4 FAIL (V-5a, V-6a, V-6b, V-10) flagged a
  v0 prompt regression. Evidence:
  [`../../09_logs/2026-06-15_phaseA4-default-model-and-prompt-applied.md`](../../09_logs/2026-06-15_phaseA4-default-model-and-prompt-applied.md).
- Phase A.4 v0.1 — **PARTIALLY APPLIED 2026-06-15**. v0.1 prompt
  replaces v0 (3 342 chars); fixed Spanish-greeting persona (V-5a)
  and multi-turn language switch (V-11). **Issue T persists**:
  `time_now` tool is not invoked from chat — the model still
  hallucinates `[1]` and renders the function signature instead of
  issuing a real call. Audit log confirms 0 invocations during
  validation. 15/21 validation PASS. Evidence:
  [`../../09_logs/2026-06-15_phaseA4-prompt-v0.1-applied.md`](../../09_logs/2026-06-15_phaseA4-prompt-v0.1-applied.md).
- A.4 next sub-step: **diagnose Issue T** by hitting Ollama
  directly (`curl http://127.0.0.1:11434/api/chat`) with the v0.1
  system prompt + `time_now` tool definition + `"¿qué hora es?"`,
  to determine whether the regression is at the model layer or at
  Open WebUI's prompt+tools wiring. Then either a v0.2 prompt
  iteration or an Open WebUI configuration fix. **Phase B must not
  start until Issue T is resolved** — `time_now` is the canary for
  the very tool-calling muscle that `rag_search` and
  `system_status` will rely on.

### Pending in Phase B
- Add `infra_audits` corpus to `ingest/conf/corpora.yaml`.
- One-shot backfill of `/home/diego/server-audit-2026-06-13/**/*.md`
  into the new Qdrant collection.
- Implement `rag_search.py` and `audit_search.py`.
- Bind-mount `/home/diego/homelab/ai-stack/ingest` read-only into the
  openwebui container at `/opt/ingest`.

### Pending in Phase C (Home Assistant — gated)
- Create dedicated HA user `assistant`; issue Long-Lived Access Token.
- Populate `HA_BASE_URL`, `HA_LLAT` in `.env`.
- Implement `ha_get_state` and `ha_call_service` with the 12-domain
  allowlist.
- Run the refusal-test (e.g. `recorder.purge` → polite refusal).

### Pending in Phase D
- `homelab-tools` container + `docker-socket-proxy` (Path A from the
  A.2 design), or a different path if user chooses otherwise.
- Implement `system_status.py` as a thin HTTP client.
- Disable bare-metal `homelab-tools.service`. Closes audit R-02.

### Pending in Phase E and later
- Phase E: Acceptance test (six questions from `README.md`), logrotate
  for the audit log, refusal-test script, "v1 live" sign-off per the
  security checklist in [`04-security-and-permissions.md`](04-security-and-permissions.md).
- Phase F (voice): Wyoming Whisper + Piper, HA Assist wiring.
- Phase G (knowledge expansion): MyFreeTour corpus source path,
  continuous-ingest improvements.

### Out-of-band fixes already applied
- VSCode Remote `search.followSymlinks: false` and Steam Proton
  excludes — applied 2026-06-15. See
  [`../../INVESTIGATION_REPORT_VSCODE_MEMORY.md`](../../INVESTIGATION_REPORT_VSCODE_MEMORY.md).
  Outside Amarolab's scope but logged here because it was a
  prerequisite for the Phase A.1 smoke test to have safe RAM headroom.

## Latest completed milestone

**Phase A.4 v0.1 — Open WebUI default model + system prompt v0.1 —
PARTIALLY APPLIED 2026-06-15.**

What works (15/21 PASS):

- Workspace `DEFAULT_MODELS = "qwen2.5:7b-instruct"` (V-1).
- v0.1 system prompt landed on the qwen2.5 Model entry; preserves
  `meta.toolIds = ["time_now"]` and `meta.description` (V-2).
- `llama3:latest` (Jarvis) and `llama3.2:latest` untouched (V-3, V-4).
- Spanish greeting → *"¡Hola! Soy Amarolab Assistant…"* (V-5).
- HA control refused, naming Phase C (V-7).
- doc-search refused, explains tool not yet available (V-8 — but
  see open regression V-8b below).
- `llama3:latest` chat shows no Amarolab persona (V-9).
- Multi-turn language switch (ES turn 1 → explicit EN turn 2) works
  (V-11).

What is broken (6 FAILs, see
[`../../09_logs/2026-06-15_phaseA4-prompt-v0.1-applied.md`](../../09_logs/2026-06-15_phaseA4-prompt-v0.1-applied.md)):

- **Issue T (most serious):** `time_now` is not invoked from chat
  when the v0.1 system prompt is in scope; the model writes
  `[1] time_now("Europe/Madrid", "%H:%M:%S")` in plain text
  instead. Audit log: 0 invocations during V-10. V-10a, V-10b, V-12
  all FAIL on this single root cause.
- **Issue L:** English greeting on turn 1 (short `"hi there"`) still
  defaults to Spanish (V-6a, V-6b). Multi-turn explicit switch
  works (V-11).
- **Issue B:** `rag_search` refusal does not name "Phase B"
  explicitly (V-8b regressed from v0).

Prior milestones (still valid):

- Phase A.3 — Tool installed in `webui.db`; happy path proven
  *before any system prompt existed* (so Phase A.3 evidence isolates
  Issue T to the prompt+model interaction, not the Tool itself).
  See [`../../09_logs/2026-06-15_phaseA3-tool-canary-applied.md`](../../09_logs/2026-06-15_phaseA3-tool-canary-applied.md).
- Phase A.1 — `qwen2.5:7b-instruct` resident in Ollama
  (ID `845dbda0ea48`, ~4.6 GB warm). See
  [`../../09_logs/2026-06-15_phaseA1-tool-calling-llm-applied.md`](../../09_logs/2026-06-15_phaseA1-tool-calling-llm-applied.md).

Pre-flight backups retained:

- `/tmp/amarolab-phaseA4-backup/webui.db.pre-A4` (pre-A.4 state)
- `/tmp/amarolab-phaseA4-v0_1-backup/webui.db.pre-v0_1` (post-v0,
  pre-v0.1 state)
