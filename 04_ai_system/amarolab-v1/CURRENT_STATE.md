# CURRENT_STATE — Amarolab Assistant v1

Last updated: 2026-06-15

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
| `AMAROLAB_AUDIT_LOG` | **not set** | will land with Phase A.3 helper |
| Open WebUI default model | unchanged from pre-Phase-A | not yet set to qwen2.5 |

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
- A.4 (next, not started): set Open WebUI default model to
  `qwen2.5:7b-instruct`.
- A.4: draft v0 system prompt with routing rules from
  [`03-tools.md`](03-tools.md), trimmed to the three A.2 tools (only
  `time_now` is wired so far; prompt should describe full routing so
  it survives B and D).

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

**Phase A.3 — Open WebUI Tools scaffold + `time_now` canary —
APPLIED 2026-06-15.**

Evidence:
[`../../09_logs/2026-06-15_phaseA3-tool-canary-applied.md`](../../09_logs/2026-06-15_phaseA3-tool-canary-applied.md).

Highlights:

- Source tree at `/home/diego/homelab/ai-stack/openwebui-tools/`
  (`README.md`, `tools/time_now.py`, `lib/audit_helper.py`,
  `bin/install_tool`, `bin/dump_tools`).
- `time_now` Tool row in `webui.db` (5180 char content, 1 spec).
- Custom Model entry for `qwen2.5:7b-instruct` with
  `meta.toolIds=["time_now"]`; per-model scoping (D-20) verified.
- Audit log live at `/srv/homelab/data/openwebui/amarolab-audit.log`.
- 19 of 21 validation checks PASS, 1 informational (V-20 RAM), 1
  PASS (V-21 static network check). End-to-end happy path returns
  correct real date/time with citation `[1]`.

Prior milestone (Phase A.1 — model pull) is still valid:
`qwen2.5:7b-instruct` resident in Ollama (ID `845dbda0ea48`), ~4.6 GB
warm. Evidence:
[`../../09_logs/2026-06-15_phaseA1-tool-calling-llm-applied.md`](../../09_logs/2026-06-15_phaseA1-tool-calling-llm-applied.md).
