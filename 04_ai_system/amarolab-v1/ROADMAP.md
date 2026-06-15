# ROADMAP — Amarolab Assistant v1

Last updated: 2026-06-15

Phase plan for the Amarolab Assistant v1 sub-project. For the
homelab-wide roadmap see
[`../../00_overview/ROADMAP.md`](../../00_overview/ROADMAP.md).

The canonical phase-by-phase plan with full exit criteria lives in
[`05-implementation-roadmap.md`](05-implementation-roadmap.md). This
file is the **status overlay** on top of that plan: what's done, what's
current, what's next, what's blocked, what's decided.

---

## Completed phases

### Phase 0 — Audit and remediation
- Outcome: R-04 (Mosquitto), R-05 (`WEBUI_SECRET_KEY`), R-06 (docker
  socket removed from openwebui), R-07.1 (Qdrant API key enforced),
  R-12 (Restic backups) all complete.
- Still open from the audit (queued, not blocking v1): R-01, R-07.2,
  R-09, R-10, R-11, R-13, R-14.
- Evidence: `/home/diego/server-audit-2026-06-13/**` and Phase 0
  application logs.

### Phase 1 — RAG foundation
- Outcome: ingest service shipped at `ai-stack/ingest`; 4 Qdrant
  collections populated with 1 377 chunks total; nightly cron at
  02:30; `multilingual-e5-small` embedder cached.
- Evidence:
  [`../../09_logs/2026-06-14_phase1-rag-foundation-applied.md`](../../09_logs/2026-06-14_phase1-rag-foundation-applied.md).

### Phase 1.5 — Reranker benchmark
- Outcome: `BAAI/bge-reranker-v2-m3` integrated into the eval harness;
  top-6 lifted from 80 % to ≥ 95 % on the `guardian_cloud` benchmark.
- Evidence: `04_ai_system/rag-audits/` (reranker benchmark report).

### Phase A.1 — Tool-calling LLM pull
- Date applied: 2026-06-15.
- Outcome: `qwen2.5:7b-instruct` (Q4_K_M, 4.7 GB) pulled into Ollama;
  roadmap smoke test PASS — model emits valid native `tool_calls`.
- Evidence:
  [`../../09_logs/2026-06-15_phaseA1-tool-calling-llm-applied.md`](../../09_logs/2026-06-15_phaseA1-tool-calling-llm-applied.md).

---

## Current phase

### Phase A.2 — Tool layer design (in review)

Three tools designed as the first implementation set:

| Tool | Role | Status |
|---|---|---|
| `time_now` | Canary for the entire Functions pipeline; also a real utility tool | Design delivered |
| `rag_search` | Dense retrieval + cross-encoder rerank over indexed corpora | Design delivered |
| `system_status` | Live containers / ports / volumes / disk introspection | Design delivered (backing-service path is an open question) |

Tools **deferred** out of this phase: `audit_search` (waits for
`infra_audits` corpus in Phase B), `ha_get_state`, `ha_call_service`
(Phase C, Home Assistant).

Phase A.2 status: **awaiting user approval and resolution of 5 open
questions** (see `Blockers` below). The design report lives in the
conversation transcript dated 2026-06-15; if durable storage is
desired it should be committed as
`09_logs/2026-06-15_phaseA2-tool-layer-design.md`.

---

## Next phases

The numbering matches
[`05-implementation-roadmap.md`](05-implementation-roadmap.md) where
applicable, with the Phase A subdivided into A.1 … A.4 to match how
work has actually been sequenced.

### Phase A.3 — Functions scaffold + canary
- Create `/srv/homelab/data/openwebui/functions/` on host.
- Drop `amarolab_common.py` (audit helper, redaction, RateLimiter).
- Implement `time_now()` (zero external deps).
- Exit: in Open WebUI chat, `"what time is it?"` produces a
  `time_now` tool call, the Function returns the JSON payload, the
  audit log accumulates a JSON line per call.

### Phase A.4 — Open WebUI default + system prompt v0
- Set the workspace default model to `qwen2.5:7b-instruct` in Open
  WebUI admin.
- Draft a v0 system prompt with the tool-composition rules from
  [`03-tools.md`](03-tools.md), trimmed to the three Phase A.2 tools.
- Exit: default model is qwen2.5; system prompt is loaded.

### Phase B — Knowledge tool + audit corpus
- Add `infra_audits` corpus to `ingest/conf/corpora.yaml` and create
  the Qdrant collection.
- One-shot backfill from `/home/diego/server-audit-2026-06-13/**/*.md`.
- Bind-mount the ingest tree read-only into the openwebui container at
  `/opt/ingest`.
- Implement `rag_search.py` reusing `ingest.embedder.Embedder` and
  `ingest.reranker.Reranker`.
- Implement `audit_search.py` as sugar over
  `rag_search(collection="infra_audits", …)`.
- Exit: the Phase 1.5 reranker benchmark reproduces when routed
  through the Function path (top-6 ≥ 95 % on guardian_cloud).

### Phase C — Home Assistant integration
- Create dedicated HA user `assistant`; issue Long-Lived Access Token
  in the HA UI.
- Populate `HA_BASE_URL` and `HA_LLAT` in
  `/home/diego/homelab/ai-stack/.env`.
- Implement `ha_get_state` (read) and `ha_call_service` (write,
  12-domain allowlist).
- Run the refusal test: a prompt like *"please call recorder.purge"*
  returns the polite refusal logged with `allowed=false`.
- Exit: read + bounded write of HA via tools; refusal path tested.

### Phase D — `system_status` backing service
- If A.2 question 1 chooses **Path A** (recommended): build the
  `homelab-tools` container (FastAPI) + `tecnativa/docker-socket-proxy`
  on the `ai-local_default` network, no host port published.
- Add per-scope endpoints (`/containers`, `/ports`, `/volumes`,
  `/disk`, `/healthz`) — see contract in [`03-tools.md`](03-tools.md).
- Implement `system_status.py` as a thin HTTP client of the container.
- Disable the bare-metal `homelab-tools.service`. Closes audit R-02.
- Exit: live system data readable from chat; bare-metal Flask service
  is gone.

### Phase E — Acceptance + hardening
- Run the six acceptance questions from
  [`README.md`](README.md) against the live assistant; require
  correct, cited answers on each.
- `/etc/logrotate.d/amarolab-audit` written; 12-week rotation.
- Refusal-test script in `bin/amarolab-health` (or equivalent).
- Walk the security checklist in
  [`04-security-and-permissions.md`](04-security-and-permissions.md).
- Exit: v1 declared "live".

### Phase F — Voice (deferred from v1)
- Wyoming Whisper + Piper containers; HA Assist integration. Out of
  scope for v1 per [`02-target-architecture.md`](02-target-architecture.md).

### Phase G — Unified knowledge (deferred from v1)
- Resolve MyFreeTour corpus source path; index it.
- Continuous-ingest improvements (Open WebUI Knowledge feed,
  per-corpus chunking refinements).

---

## Blockers

Active blockers (resolution required before the phase listed in "phase
blocked" can start):

| # | Blocker | Phase blocked | Owner | Notes |
|---|---|---|---|---|
| B-01 | Phase A.2 design unapproved | A.3 onward | user | Design delivered 2026-06-15; awaiting sign-off |
| B-02 | A.2 question 1: `system_status` backing path (A / B / C) | D (or A.2 if Path A) | user | A.2 recommendation: Path C (defer to D); avoids reintroducing R-02 |
| B-03 | A.2 question 2: `time_now` default timezone (Europe/Madrid vs UTC) | A.3 | user | A.2 recommendation: `Europe/Madrid` for `human`, ISO + Unix always present |
| B-04 | A.2 question 3: Function visibility scope (all models vs qwen2.5 only) | A.3 | user | A.2 recommendation: all models |
| B-05 | A.2 question 4: confirm audit-log host path | A.3 | user | A.2 recommendation: `/srv/homelab/data/openwebui/amarolab-audit.log` (matches v1 security model — no deviation) |
| B-06 | A.2 question 5: `myfreetour` enum treatment | B | user | A.2 recommendation: leave in enum, return `empty_collection` |
| B-07 | HA Long-Lived Access Token not issued | C | user | Must be created in HA UI; not automatable |
| B-08 | MyFreeTour source path unknown | G | user | Phase 1 placeholder corpus stays empty until decided |

Non-blocking carry-overs (do not stop any v1 phase, listed for
visibility):

| # | Item | Notes |
|---|---|---|
| C-01 | R-07.2 — Ollama bound to `0.0.0.0:11434` | Acceptable on trusted LAN; deferred per [`01-current-state-review.md`](01-current-state-review.md) |
| C-02 | R-14 — most containers still ad-hoc `docker run` | Will become a soft blocker when Phase D adds new containers; queued for batch fix |
| C-03 | R-09 / R-10 / R-11 / R-13 | System-hardening sweep, do after v1 is stable |
| C-04 | Off-site backup mirror | Out of scope for v1 |
| C-05 | Containerise the ingest service | Cleaner backup story; targeted for v1.1 |

---

## Decisions taken (locked)

These are the binding decisions made for v1. Reversing one requires an
explicit user decision and a new design entry.

| # | Decision | When | Source |
|---|---|---|---|
| D-01 | Primary tool-calling LLM = `qwen2.5:7b-instruct` (Q4_K_M) | 2026-06-15 | Phase A architecture review |
| D-02 | `llama3:latest` (Llama 3.0 8B Q4_0) retained as fallback non-tool chat | 2026-06-15 | same |
| D-03 | Do **not** pull `llama3.1:8b-instruct` in Phase A | 2026-06-15 | same |
| D-04 | Open WebUI Functions are the tool runtime (no separate tool server) | Pre-A (v1 design) | [`02-target-architecture.md`](02-target-architecture.md) |
| D-05 | `amarolab_common.py` is the single shared helper (audit + rate limit + redact) | v1 design | [`03-tools.md`](03-tools.md) |
| D-06 | Trust model: LLM is adversarial; allowlists are file-level constants; no `eval`, `subprocess`, or path-from-arg | v1 design | [`04-security-and-permissions.md`](04-security-and-permissions.md) |
| D-07 | Audit-log path: `/srv/homelab/data/openwebui/amarolab-audit.log` (host) | v1 design | [`04-security-and-permissions.md`](04-security-and-permissions.md) |
| D-08 | Embedder = `intfloat/multilingual-e5-small` (384-dim); reranker = `BAAI/bge-reranker-v2-m3`; not swapped in v1 | Phase 1 / 1.5 | Phase 1.5 benchmark |
| D-09 | Guardian Cloud is production; RAG read-only over its docs; never call its backend API | Pre-existing | top-level homelab rule |
| D-10 | First three tools to implement = `time_now`, `rag_search`, `system_status` | 2026-06-15 | Phase A.2 scope as set by user |
| D-11 | HA tools (`ha_get_state`, `ha_call_service`) deferred to Phase C; no HA-related changes before then | 2026-06-15 | user |
| D-12 | HA control allowlist = 12 domains (`light`, `switch`, `scene`, `cover`, `climate`, `media_player`, `script`, `automation`, `fan`, `vacuum`, `input_boolean`, `input_select`, `input_number`); explicitly deny `homeassistant`, `recorder`, `hassio`, `system_log`, `backup`, `auth`, etc. | v1 design | [`04-security-and-permissions.md`](04-security-and-permissions.md) |
| D-13 | `infra_audits` corpus included in v1 (Phase B), single-user posture makes it safe | v1 design | [`02-target-architecture.md`](02-target-architecture.md) |
| D-14 | No voice in v1 (Whisper/Piper deferred to Phase F) | v1 design | user request |
| D-15 | No public exposure of the assistant via Cloudflare in v1; LAN/tailnet only | v1 design | [`02-target-architecture.md`](02-target-architecture.md) |
| D-16 | No conversation memory across sessions in v1; in-session only via Open WebUI's webui.db | v1 design | [`02-target-architecture.md`](02-target-architecture.md) |
| D-17 | Out-of-band: VSCode Remote machine settings written with `search.followSymlinks: false` + Steam Proton excludes | 2026-06-15 | Investigation report (outside repo) |
