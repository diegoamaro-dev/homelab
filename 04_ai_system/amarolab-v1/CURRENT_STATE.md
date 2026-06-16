# CURRENT_STATE — Amarolab Assistant v1

Last updated: 2026-06-17 (Phase B B-4..B-8 applied 2026-06-16; `rag_search` + `audit_search` installed in `webui.db`, qwen2.5 `meta.toolIds = ["time_now","rag_search","audit_search"]`, two browser-path `audit_search` runs `result_code: ok`; only B-9 docs/commit + B-10 hand-off remaining)

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

From the v1 design, the following is now in place:
- Phase A.3 (2026-06-15): one Open WebUI Tool installed in `webui.db`
  (`time_now`), scoped to `qwen2.5:7b-instruct` only via a custom Model
  entry, audit log writing one JSONL line per call to
  `/srv/homelab/data/openwebui/amarolab-audit.log`.
- Phase B B-1 + B-2 (2026-06-16): `infra_audits` corpus populated in
  Qdrant (280 chunks from 6 markdown files under
  `/home/diego/server-audit-2026-06-13`).
- Phase B B-3 (2026-06-16, Gate G-1 approved): `openwebui` container
  recreated with the read-only bind mount
  `/home/diego/homelab/ai-stack/ingest:/opt/ingest:ro`; pre-Phase B
  container preserved as `openwebui_pre_phaseB_20260615235209` as the
  G-1 rollback target. `from ingest.embedder import Embedder` and
  `from ingest.reranker import Reranker` both resolve inside the
  container.
- Phase B V-C (2026-06-17): the container's
  `sentence-transformers 5.2.3` reproduces the Phase 1.5 reranker
  benchmark on `guardian_cloud` exactly (0 pp drift; see
  [`../../09_logs/2026-06-17_phaseB_vc_validation.md`](../../09_logs/2026-06-17_phaseB_vc_validation.md)).

- Phase B B-4 + B-5 (2026-06-17): canonical Tool source authored —
  `ai-stack/openwebui-tools/tools/rag_search.py` (committed
  `a7995b3f`) and `ai-stack/openwebui-tools/tools/audit_search.py`
  (committed `a13d5e94`).
- Phase B B-6 (2026-06-16, applied by user via `bin/install_tool`):
  both Tools installed into `webui.db` (`rag_search`: 11 629 chars,
  1 spec; `audit_search`: 11 231 chars, 1 spec); install fidelity
  byte-identical to canonical source modulo a trailing newline.
- Phase B B-7 (2026-06-16, Gate G-2 approved): qwen2.5 Model entry
  `meta.toolIds` extended from `["time_now"]` to
  `["time_now","rag_search","audit_search"]`. `base_model_id` still
  `NULL` (D-35 invariant preserved).
- Phase B B-8 (2026-06-16, user-driven browser path): two real-world
  `audit_search` queries logged `result_code: ok` with realistic
  durations (20 694 ms cold, 12 788 ms warm) — see
  [`../../09_logs/2026-06-16_phaseB_validation_applied.md`](../../09_logs/2026-06-16_phaseB_validation_applied.md).
  Tool-runtime evidence for `rag_search` end-to-end gathered via a
  read-only probe against the installed source (22.5 s, 6 hits).

Still missing: **the full literal W-1..W-8 sweep** (only W-3-shaped
queries were exercised; W-4, W-5, W-6, W-7 are pending — see the
validation log §7), **no** HA tools (Phase C), **no** `homelab-tools`
container or `docker-socket-proxy` (Phase D), **no** containerized
ingest service (deferred).

## What is implemented

### Models in Ollama
| Model | ID | Size | Role |
|---|---|---:|---|
| `qwen2.5:7b-instruct` | `845dbda0ea48` | 4.7 GB | **primary** (tool-calling) — pulled Phase A.1 |
| `llama3:latest` (Llama 3.0 8B Q4_0) | `365c0bd3c000` | 4.7 GB | fallback non-tool chat |
| `llama3.2:latest` | `a80c4f17acd5` | 2.0 GB | leftover from earlier experiments |
| `phi3:latest` | `4f2222927938` | 2.2 GB | leftover from earlier experiments |

Disk for the models cache: 8.3 GB of /srv/homelab/data/ollama/models.

### Qdrant collections (5 active, 1 placeholder)
| Collection | Source | Chunks | Files | Status |
|---|---|---:|---:|---|
| `homelab_docs` | `/home/diego/homelab` | 86 | 15 | Active |
| `guardian_cloud` | `/mnt/storage/projects/guardian-cloud` | 872 | 56 | Active |
| `ensambla2` | `/mnt/storage/projects/ensambla2` | 419 | 48 | Active |
| `myfreetour` | TBD | 0 | 0 | Placeholder, disabled |
| `infra_audits` | `/home/diego/server-audit-2026-06-13` | 280 | 6 | **Active** (created 2026-06-16, Phase B B-1/B-2) |

Dimensionality: 384 (multilingual-e5-small). Distance: cosine.
Payload indexes on `collection`, `source_kind`, `source_rel`.

### Tool layer
**`time_now` shipped** (Phase A.3, 2026-06-15). Canonical source at
`/home/diego/homelab/ai-stack/openwebui-tools/tools/time_now.py`;
runtime copy in `webui.db` (5180 chars, 1 spec). Scoped to
`qwen2.5:7b-instruct` only (D-20) via a Model entry with
`meta.toolIds=["time_now"]`. End-to-end smoke + error + concurrency
validated.

**Browser-UI end-to-end path validated 2026-06-16** after the Issue T
re-opening — see
[`../../09_logs/2026-06-15_issueT_remediation_applied.md`](../../09_logs/2026-06-15_issueT_remediation_applied.md).
Until that date, the Phase A.3 end-to-end claim was true only for
API requests that manually attached `tool_ids:["time_now"]`; the
browser path was broken by the qwen2.5 Model entry's
`base_model_id` value (now `NULL` — see new row in
*Environment / configuration* below and **D-35** in
[`ROADMAP.md`](ROADMAP.md)).

Phase A.2 designed tools status, refreshed at end of B-7:
`rag_search` + `audit_search` are **live** (B-6 install + B-7
scope). `system_status`, `ha_get_state`, `ha_call_service` are
**designed only** — see Phase A.2 design log
([`../../09_logs/2026-06-15_phaseA2-tool-layer-design.md`](../../09_logs/2026-06-15_phaseA2-tool-layer-design.md))
and Phase A.3 applied log
([`../../09_logs/2026-06-15_phaseA3-tool-canary-applied.md`](../../09_logs/2026-06-15_phaseA3-tool-canary-applied.md)).

**Phase B runtime readiness validated 2026-06-17 (V-C).** The
openwebui container can host `rag_search` from the bind-mounted
ingest tree; embedder + reranker reproduce the Phase 1.5
`guardian_cloud` benchmark on the container's `sentence-transformers
5.2.3` exactly (top-1/3/6 = 15/17/19, identical to the documented
3.x baseline). Evidence:
[`../../09_logs/2026-06-17_phaseB_vc_validation.md`](../../09_logs/2026-06-17_phaseB_vc_validation.md).

**`rag_search` + `audit_search` installed 2026-06-16 (B-6) and
visible to qwen2.5 (B-7).** Source files
`tools/rag_search.py` (committed `a7995b3f`) and
`tools/audit_search.py` (committed `a13d5e94`) inlined and POSTed
to `/api/v1/tools/create`; rows present in `webui.db` with the
expected post-inline byte counts. `meta.toolIds` on the qwen2.5
Model entry now
`["time_now","rag_search","audit_search"]`. Browser-path
end-to-end exercised for `audit_search` (Spanish R-12 query +
English `SANITIZATION_REPORT` query, both `result_code: ok`);
runtime evidence for `rag_search` gathered via a read-only probe
against the installed source. Evidence:
[`../../09_logs/2026-06-17_phaseB_rag_search_design.md`](../../09_logs/2026-06-17_phaseB_rag_search_design.md),
[`../../09_logs/2026-06-17_phaseB_audit_search_design.md`](../../09_logs/2026-06-17_phaseB_audit_search_design.md),
[`../../09_logs/2026-06-16_phaseB_validation_applied.md`](../../09_logs/2026-06-16_phaseB_validation_applied.md).
`ha_get_state`, `ha_call_service`, `system_status` remain
designed-only — see Phase A.2 design log
([`../../09_logs/2026-06-15_phaseA2-tool-layer-design.md`](../../09_logs/2026-06-15_phaseA2-tool-layer-design.md)).

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
| `qwen2.5:7b-instruct` per-model `params.system` | **v0.1 prompt, 3 342 chars** | `model.params.system` in `webui.db`; persona + tool routing + refusals. Prompt-cosmetic v0.2 carry-overs documented in [`../../09_logs/2026-06-15_phaseA_closeout.md`](../../09_logs/2026-06-15_phaseA_closeout.md) §3.1. |
| `qwen2.5:7b-instruct` `meta.toolIds` | **`["time_now","rag_search","audit_search"]`** (was `["time_now"]` until 2026-06-16) | `model.meta` in `webui.db`. Gate G-2 approved. D-20 per-model scope preserved (the three Tools remain attached only to qwen2.5). See [`../../09_logs/2026-06-16_phaseB_validation_applied.md`](../../09_logs/2026-06-16_phaseB_validation_applied.md) §2. |
| `qwen2.5:7b-instruct` Model-entry `base_model_id` | **`NULL`** (was `"qwen2.5:7b-instruct"` until 2026-06-16) | `model.base_model_id` in `webui.db`. Required for OWUI 0.8.10's `get_all_models` to expose `info.meta.toolIds` via `/api/models` — see [`../../09_logs/2026-06-15_issueT_browser_validation_reopened.md`](../../09_logs/2026-06-15_issueT_browser_validation_reopened.md) §2.4 and locked decision **D-35** in [`ROADMAP.md`](ROADMAP.md). |
| `openwebui` container mounts | `/srv/homelab/data/openwebui:/app/backend/data` (R/W) **+ `/home/diego/homelab/ai-stack/ingest:/opt/ingest:ro` (added Phase B B-3, 2026-06-16)** | `docker inspect openwebui`. Gate G-1 approved. Rollback target preserved as `openwebui_pre_phaseB_20260615235209` (stopped). See [`../../09_logs/2026-06-16_phaseB_openwebui_bind_mount_applied.md`](../../09_logs/2026-06-16_phaseB_openwebui_bind_mount_applied.md). |
| Ingest package install in `ai-stack/ingest/venv` | Editable (`pip install -e .`) since 2026-06-16; `pyproject.toml` added; `bin/ingest --help` exits 0 from any CWD | Fixes R-B1 from the Phase B readiness review. Nightly 02:30 cron is now unblocked. See [`../../09_logs/2026-06-16_ingest_cli_remediation_applied.md`](../../09_logs/2026-06-16_ingest_cli_remediation_applied.md). |

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
| Browser-UI chat invokes `time_now` end-to-end | `POST /api/chat/completions` with the post-fix browser body shape (`tool_ids:["time_now"]` auto-attached) | **PASS** — reply contains real wall-clock time; audit-log delta `+1`; `result_code: "ok"`; `duration_ms: 10` | 2026-06-16 |
| Ingest CLI runnable from any CWD (R-B1 fix) | `bin/ingest --help` + `bin/ingest status` from `/home/diego` | exit 0; status returns the 4 active corpora with documented counts | 2026-06-16 |
| `infra_audits` corpus created + populated | `bin/ingest sync --collection infra_audits` + Qdrant probe | 280 chunks; test rerank query top-1 0.8809 on `SANITIZATION_REPORT.md`-related chunk | 2026-06-16 |
| `/opt/ingest` read-only bind mount inside `openwebui` | `docker exec` import smoke test | `from ingest.embedder import Embedder` and `from ingest.reranker import Reranker` resolve; `webui.db` + audit-log md5 unchanged across recreate | 2026-06-16 |
| Container reranker reproduction (V-C) | 20-question `guardian_cloud` benchmark, `class Tools`-shaped probe run inside container | **PASS** — top-1 / top-3 / top-6 = 15 / 17 / 19 (75 % / 85 % / 95 %); 0 pp drift vs Phase 1.5 baseline; all 20 per-question ranks identical | 2026-06-17 |
| `sentence-transformers` major-version compatibility | side-by-side host (3.4.1) vs container (5.2.3) on real `guardian_cloud` payloads | accuracy: 0 drift; latency: 11 124 ms vs 11 174 ms / query — within 0.5 % | 2026-06-17 |
| `rag_search` + `audit_search` installed in `webui.db` (B-6) | `sqlite3 webui.db "SELECT id, length(content), json_array_length(specs) FROM tool"` | both rows present; content 11 629 / 11 231 chars; 1 spec each; install-fidelity diff vs canonical = trailing-newline only | 2026-06-16 |
| qwen2.5 `meta.toolIds` extended (B-7, Gate G-2) | SQL probe of `model.meta` | `["time_now","rag_search","audit_search"]`; `base_model_id` still `NULL` (D-35 preserved) | 2026-06-16 |
| Browser-path `audit_search` end-to-end (B-8, user-driven) | Browser chat → audit-log delta | two `result_code: ok` lines: Spanish R-12 query `duration_ms = 20 694`, `SANITIZATION_REPORT` `duration_ms = 12 788` | 2026-06-16 |
| `rag_search` Tool-runtime end-to-end | this-log probe vs installed source dumped from `webui.db` | `result_code: ok`; 6 hits; top-1 score 0.2941 on `09_logs/2026-06-15_phaseA3-tool-canary-design.md`; `duration_ms = 22 509` (cold) | 2026-06-16 |

## What is pending

### Phase A (closed 2026-06-15)
- **Phase A is formally CLOSED.** See
  [`../../09_logs/2026-06-15_phaseA_closeout.md`](../../09_logs/2026-06-15_phaseA_closeout.md)
  for the durable decision + criteria check.
- All sub-phase deliverables are live: A.1 (qwen2.5 in Ollama), A.2
  (three-tool design + D-18..D-22), A.3 (`time_now` canary in
  `webui.db` + scoping + audit log), A.4 v0 (`DEFAULT_MODELS` set),
  A.4 v0.1 (system prompt 3 342 chars on qwen2.5 Model entry +
  D-32..D-34).
- **Issue T (B-09)** — initially diagnosed 2026-06-15 as a
  validator-shape artefact, **REOPENED 2026-06-16** when a live
  browser test reproduced the failure, and **RE-RESOLVED
  2026-06-16** after a one-row SQL UPDATE. Real root cause: the
  qwen2.5 Model entry was created with
  `base_model_id = "qwen2.5:7b-instruct"` (same as its `id`),
  which sends it to OWUI 0.8.10's `elif … continue` skip branch
  in `utils/models.py:159–175`. The custom entry was silently
  dropped from `/api/models`, so the browser's auto-attach
  (`ee.info.meta.toolIds` in `GxGTGtKc.js`) had nothing to read
  and `tool_ids` never made it into the request body. Fix: one
  SQL UPDATE setting `base_model_id = NULL`. The model, the
  prompt, the Tool, and Ollama all behave correctly. Evidence:
  [`../../09_logs/2026-06-15_issueT_browser_validation_reopened.md`](../../09_logs/2026-06-15_issueT_browser_validation_reopened.md)
  (root-cause investigation),
  [`../../09_logs/2026-06-15_issueT_remediation_plan.md`](../../09_logs/2026-06-15_issueT_remediation_plan.md)
  (plan), and
  [`../../09_logs/2026-06-15_issueT_remediation_applied.md`](../../09_logs/2026-06-15_issueT_remediation_applied.md)
  (apply log, including browser-equivalent validation and the
  `+1` audit-log line).
- **New known carry-over BX — Open WebUI 0.8.10 browser-UI
  WebSocket race.** When the WebSocket / socket.io handshake hasn't
  completed before the first send, `session_id` is omitted from the
  request body, Open WebUI falls through to a streaming SSE
  response, and the frontend helper `A()` in `C2Mvb_V1.js` calls
  `.json()` on it — producing
  `Unexpected token 'd', "data: {"id"... is not valid JSON`. **Not
  caused by anything in Phase A.** Workaround: open the UI over
  LAN/Tailnet (`http://192.168.178.x:3000`), hard-refresh, wait for
  the connection indicator before the first send. Durable fix
  belongs upstream. Evidence:
  [`../../09_logs/2026-06-15_openwebui_json_parse_error_analysis.md`](../../09_logs/2026-06-15_openwebui_json_parse_error_analysis.md).
- Prompt-cosmetic carry-overs (Issue L — short English greeting
  defaults to Spanish; Issue B — `rag_search` refusal doesn't name
  "Phase B"; `[1]` self-contradiction in the no-tools fallback) are
  tracked for a v0.2 prompt iteration. **Not Phase B blockers.**

### Phase B (current — B-1..B-8 applied; B-9/B-10 remaining)
- Plan: [`PHASE_B_EXECUTION_PLAN.md`](PHASE_B_EXECUTION_PLAN.md).
- Status: **operationally functional** (both Tools live in
  `webui.db`, qwen2.5 sees them, browser-path `audit_search`
  end-to-end PASS), **not formally closed** — B-9 (this docs
  sync + commit/push) and B-10 (Phase C hand-off note) still
  pending; the literal W-4 / W-5 / W-6 / W-7 prompts from the
  formal B-8 sweep remain open follow-ups (see the validation
  log §7).

**Applied this phase:**
- Out-of-band: ingest CLI remediation (R-B1) — `pyproject.toml`
  added, `pip install -e .` in `install.sh`,
  `bin/ingest --help` exits 0 from any CWD; nightly 02:30 cron
  unblocked. See
  [`../../09_logs/2026-06-16_ingest_cli_remediation_applied.md`](../../09_logs/2026-06-16_ingest_cli_remediation_applied.md).
- B-1 — added `infra_audits` stanza to
  `ingest/conf/corpora.yaml`.
- B-2 — Qdrant collection `infra_audits` created (384 d cosine,
  payload indexes on `collection` / `source_kind` / `source_rel`);
  one-shot backfill of `/home/diego/server-audit-2026-06-13/**/*.md`
  ingested 280 chunks. See
  [`../../09_logs/2026-06-16_phaseB_infra_audits_applied.md`](../../09_logs/2026-06-16_phaseB_infra_audits_applied.md).
- B-3 — `openwebui` container recreated with the read-only
  bind mount `/home/diego/homelab/ai-stack/ingest:/opt/ingest:ro`
  (Gate **G-1** approved). Pre-Phase B container preserved as
  `openwebui_pre_phaseB_20260615235209` as the rollback target.
  See
  [`../../09_logs/2026-06-16_phaseB_openwebui_bind_mount_applied.md`](../../09_logs/2026-06-16_phaseB_openwebui_bind_mount_applied.md).
- V-C (readiness pre-empt) — container's
  `sentence-transformers 5.2.3` reproduces the Phase 1.5
  reranker benchmark on `guardian_cloud` exactly (0 pp drift on
  top-1/3/6). **R-M1 resolved.** Side observation: rerank cost
  is ~10 s / query at DENSE_N = 30 on this hardware; this is
  the same on host (ST 3.4.1) and container (ST 5.2.3), so it
  is a property of the locked (`bge-reranker-v2-m3`,
  DENSE_N=30) tuple — not a regression. See
  [`../../09_logs/2026-06-17_phaseB_vc_validation.md`](../../09_logs/2026-06-17_phaseB_vc_validation.md).

**Applied (cont.):**
- B-4 (2026-06-17) — authored `tools/rag_search.py`
  (committed `a7995b3f`); `class Tools`, lazy `_init()`,
  inlined audit helper per D-26. Local validation: pre/post
  inline `py_compile`, AST shape, in-container module load
  + bad_query probe. See
  [`../../09_logs/2026-06-17_phaseB_rag_search_design.md`](../../09_logs/2026-06-17_phaseB_rag_search_design.md).
- B-5 (2026-06-17) — authored `tools/audit_search.py`
  (committed `a13d5e94`); mirrors `rag_search.py` with
  `collection = "infra_audits"` hardcoded. Same local
  validation battery. See
  [`../../09_logs/2026-06-17_phaseB_audit_search_design.md`](../../09_logs/2026-06-17_phaseB_audit_search_design.md).
- B-6 (2026-06-16) — both Tools installed via
  `bin/install_tool` → `POST /api/v1/tools/create`. Rows
  present in `webui.db` with the expected content lengths;
  install-fidelity diff vs canonical = trailing-newline only.
- B-7 (2026-06-16, Gate **G-2** approved) — qwen2.5
  `meta.toolIds` extended to
  `["time_now","rag_search","audit_search"]`. D-35
  invariant (`base_model_id = NULL`) preserved.
- B-8 (2026-06-16, partial — Gate **G-3** approved) — two
  user-issued browser queries against `audit_search`
  returned `result_code: ok` (durations 20.7 s cold,
  12.8 s warm); this-log probes captured Qdrant + rerank
  evidence for `rag_search` end-to-end. See
  [`../../09_logs/2026-06-16_phaseB_validation_applied.md`](../../09_logs/2026-06-16_phaseB_validation_applied.md).
  **Open items vs the formal W-1..W-8 + V-A/V-B sweep**:
  the literal W-2 / W-4 / W-5 / W-6 / W-7 prompts were not
  exercised; tracked in the validation log §7. User has
  marked B-8 complete.

**Remaining in Phase B:**
- B-9 — git commit + push of B-4 / B-5 / B-6 / B-7 / B-8
  artefacts and these state-doc updates (this turn).
- B-10 — hand-off note to Phase C.

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

**Phase B B-4..B-8 — applied 2026-06-16 / 2026-06-17.** Both
Phase B Tools (`rag_search`, `audit_search`) are authored,
committed, installed in `webui.db`, attached to the
`qwen2.5:7b-instruct` Model entry's `meta.toolIds`, and
exercised end-to-end on the browser path for `audit_search`
plus the Tool-runtime path for `rag_search`. Phase B is
operationally functional; the remaining steps are documentation
sync (B-9) and the Phase C hand-off note (B-10).

What is live (Phase B progress, newest first):

- **B-8 (partial — user marked complete)** — browser-path
  `audit_search` returned `result_code: ok` for two
  real-world queries (Spanish R-12, English
  `SANITIZATION_REPORT`); Tool-runtime `rag_search` probe
  PASS. Formal W-2 / W-4 / W-5 / W-6 / W-7 sweep not exercised;
  tracked in the validation log §7.
- **B-7 (Gate G-2)** — qwen2.5 `meta.toolIds` =
  `["time_now","rag_search","audit_search"]`. D-35
  `base_model_id = NULL` invariant preserved.
- **B-6** — `rag_search` (11 629 chars, 1 spec) and
  `audit_search` (11 231 chars, 1 spec) installed in
  `webui.db` via `bin/install_tool`. Install fidelity diff vs
  canonical disk source = trailing-newline only.
- **B-5** — `tools/audit_search.py` committed (`a13d5e94`).
- **B-4** — `tools/rag_search.py` committed (`a7995b3f`).
- **V-C** — container `sentence-transformers 5.2.3` reproduces
  the Phase 1.5 reranker benchmark on `guardian_cloud` exactly
  (0 pp drift on top-1/3/6 = 15/17/19; all 20 per-question
  ranks identical). R-M1 (ST drift) **resolved**. R-M3 (cold
  load) recalibrated downwards. New observation R-new1
  (~10 s / query rerank cost) is a property of the locked
  (`bge-reranker-v2-m3`, DENSE_N=30) tuple, not a regression
  introduced by the container migration — host and container
  measured identically (11.12 s vs 11.17 s / query). Evidence:
  [`../../09_logs/2026-06-17_phaseB_vc_validation.md`](../../09_logs/2026-06-17_phaseB_vc_validation.md).
- **B-3** — `/opt/ingest:ro` bind mount on `openwebui`;
  rollback target preserved as
  `openwebui_pre_phaseB_20260615235209`; `webui.db` +
  `amarolab-audit.log` md5s unchanged across recreate; Gate
  **G-1** approved.
- **B-2** — `infra_audits` Qdrant collection populated with
  280 chunks from `/home/diego/server-audit-2026-06-13/**/*.md`.
- **B-1** — `infra_audits` stanza added to
  `ingest/conf/corpora.yaml`.
- **R-B1 remediation** (out-of-band, prerequisite for B-2) —
  ingest package now editable-installed in its own venv;
  `bin/ingest --help` exits 0 from any CWD; nightly 02:30
  cron unblocked.

What is live (Phase A — for reference):

- A.1 — `qwen2.5:7b-instruct` resident in Ollama (ID
  `845dbda0ea48`, ~4.6 GB warm); native `tool_calls` confirmed
  via direct-Ollama probes A–D in
  [`../../09_logs/2026-06-15_issueT_root_cause_analysis.md`](../../09_logs/2026-06-15_issueT_root_cause_analysis.md).
- A.2 — three-tool design locked (D-18..D-22).
- A.3 — `time_now` Tool installed in `webui.db`; per-model
  scoping; audit log writing. Full end-to-end run via Probe E
  in the Issue T analysis (audit log delta +1; reply contains
  the real time).
- A.4 v0 — `DEFAULT_MODELS = "qwen2.5:7b-instruct"`.
- A.4 v0.1 — system prompt (3 342 chars) attached to qwen2.5
  Model entry; D-32 / D-33 / D-34 added.
- Issue T re-opening (2026-06-16) — **REMEDIATED** the same
  day with a one-row SQL UPDATE setting `base_model_id = NULL`;
  browser-UI tool-calling path verified end-to-end. See
  [`../../09_logs/2026-06-15_issueT_remediation_applied.md`](../../09_logs/2026-06-15_issueT_remediation_applied.md);
  rule captured in **D-35**.

Open carry-overs (non-blocking):

- **R-new1 — per-call rerank latency ≈ 10 s** on this hardware
  at DENSE_N=30. Tracked for Phase B B-4 design consideration;
  not a Phase B blocker (W-7 exit is correctness, not UX).
  Detail in
  [`../../09_logs/2026-06-17_phaseB_vc_validation.md`](../../09_logs/2026-06-17_phaseB_vc_validation.md)
  §4.3.
- **v0.2 prompt iteration** for Issue L (short English
  greeting), Issue B (refusal phase pointer), and the `[1]`
  self-contradiction in the no-tools fallback. Tracked in the
  closeout log §3.1.
- **BX — browser-UI WebSocket race.** Open WebUI 0.8.10
  frontend bug. Workaround in
  [`../../09_logs/2026-06-15_openwebui_json_parse_error_analysis.md`](../../09_logs/2026-06-15_openwebui_json_parse_error_analysis.md)
  §7.1.

Pre-flight backups retained:

- `/tmp/amarolab-phaseA4-backup/webui.db.pre-A4` (pre-A.4 state)
- `/tmp/amarolab-phaseA4-v0_1-backup/webui.db.pre-v0_1` (post-v0,
  pre-v0.1 state)
- `openwebui_pre_phaseB_20260615235209` (stopped container,
  pre-B.3 state, Gate G-1 rollback target)
