# Phase F — Architecture Document

- **Status:** Approved — **revised at F3.0 (2026-06-29)**. Governs all Phase F
  implementation decisions. The F-3 architecture, acceptance gates, and
  implementation milestones are **FROZEN** as of F3.0 (see §4A and §9 → F-3).
- **Phase:** F — Operational Intelligence.
- **Mission alignment:** [`AURORA_VISION.md`](AURORA_VISION.md) — read first.
- **Authored:** F-0 pre-work, 2026-06-28.
- **Revised:** F3.0 Architecture Refinement, 2026-06-29 — F-1/F-2 drift
  reconciled (backup-probe decision, AF-05 voice mechanism, runtime details);
  F-3 split into F-3a/F-3b; F-3 gates and milestones frozen. See §15 (Revision Log).
- **Authority:** This document defines *how* Phase F is built. If an
  implementation decision conflicts with it, this document wins — or is
  revised through a deliberate decision recorded here, not by drift.
  Conflicts with `AURORA_VISION.md` are resolved in favour of the Vision;
  revise this document to realign.

---

## 1. Mission

Phase F shifts Aurora from **reactive** to **aware**.

A reactive assistant answers when asked. An aware assistant arrives to each
conversation already knowing the current state of the lab, and can answer
questions before they fully form.

Phase F does not add breadth — it adds depth. The existing tool surface and
knowledge platform are underutilised. Phase F builds the foundation that
makes every existing capability more valuable: situational awareness,
operational memory, a defined home model, and an interface that is reliable
enough to become a habit.

Everything in Phase F is evaluated against one test: does this reduce
Diego's cognitive load while keeping him fully in control?

---

## 2. Current State

The baseline from which Phase F begins. This section records what is true
at the start of Phase F, not what will be true at the end.

*Pre-F baseline snapshot — intentionally not rewritten (PROJECT_RULES:
historical records are not rewritten). F-1 and F-2 are now complete; live
counts and runtime state are authoritative in
[`../00_overview/CURRENT_STATE.md`](../00_overview/CURRENT_STATE.md). The
reconciled forward design is §4A, §6, and §9.*

### Running components

| Component | Status | Notes |
|---|---|---|
| `rag_search` (5 collections) | Production | homelab_docs 1911 pts, knowledge_history 2918 pts, guardian_cloud 872, ensambla2 419, infra_audits 280, myfreetour 0 (disabled) |
| `ha_get_state` | Production | Reads any HA entity; curated attribute allowlist |
| `ha_call_service` | Production | 12 allowed domains; gate-validated |
| `audit_search` | Production | Searches `infra_audits` corpus (Phase 0/1 audit reports; R-XX records) |
| `time_now` | Production | Trivial |
| Ollama proxy | Production | Torre RTX 5070 ~101 tok/s primary; UM790 CPU fallback ~6 tok/s |
| `health.json` | Production | Ingest + audit health signal at `ai-stack/ingest/logs/health.json` |
| Whisper / Piper / WakeWord | Production | HA voice pipeline operational; Spanish quality gap (base-int8) |
| Open WebUI system prompt | Production | F-1 installed 2026-06-28; ~450 tokens; domain-based routing; no collection names |

### Known gaps entering Phase F

| Gap | Impact |
|---|---|
| No structured backup signal | Backup status unavailable to any tool or context layer |
| No container health signal | Docker state unknown to Aurora without a legacy HTTP endpoint (dead) |
| No situational awareness mechanism | Every conversation begins from zero |
| No operational memory | "What happened last night?" requires terminal inspection |
| Home model has 2 devices, no baseline state | Action capability exists; intelligence does not |
| STT base-int8 Spanish quality | Voice is unreliable for short Spanish utterances |

---

## 3. Architectural Domains

Phase F is organised into four coherent domains. Each domain has distinct
responsibilities and different build complexity.

```
┌─────────────────────────────────────────────────────────────────────┐
│  DOMAIN A — Situational Awareness                                   │
│  Aurora knows the current state of the lab at conversation start,  │
│  without requiring a tool call from the operator.                  │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  DOMAIN B — Operational Memory                                      │
│  Aurora retrieves what happened over the past days and weeks       │
│  from structured, machine-generated operational history.           │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  DOMAIN C — Home Intelligence                                       │
│  Aurora reasons about the home as a defined model with expected    │
│  states, not just as a collection of point queries.                │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  DOMAIN D — Interface Quality                                       │
│  Aurora becomes a habit: coherent identity, reliable voice,        │
│  correct routing, and a system prompt built for the current state. │
└─────────────────────────────────────────────────────────────────────┘
```

Domain D (system prompt) is both a prerequisite for A, B, and C (every
capability needs to be described correctly) and a beneficiary of them
(the prompt is more valuable once it can reference real awareness). The
sequencing constraint is resolved in §10.

---

## 4. Accepted Architectural Decisions

### AD-01: Situational awareness is a platform capability, not a UI plugin.

The mechanism that gives Aurora current state must exist at the platform
layer — as a generated artifact consumed by any interface — not inside a
specific UI's extension system. This decision was reached by asking: if
Open WebUI is replaced, if HA voice wants the same awareness, or if a
future agent calls the LLM directly, does the architecture serve them
without re-implementation?

A context generation script (`bin/aurora-context`) produces a canonical
context document consumed by all surfaces. Consumers are dumb: they read
the document; they do not reconstruct it.

### AD-02: Automatic awareness (no tool call) is delivered by a Filter over a pre-generated file.

`AURORA_VISION.md §4` is explicit: "The answer to 'is everything OK?' should
not require a tool call." This requires context to be present in the system
message before the model processes message 1. The mechanism is an Open WebUI
Filter that reads the pre-generated `aurora-context.md` and prepends it to
the system message on message 1 of each conversation.

The Filter contains no domain logic. It reads only pre-generated context
artifacts (no construction) — refined in AD-10 to read `aurora-context.json`
for the freshness decision and inject `aurora-context.md`. Its only job is
delivery, not construction.

### AD-03: Live state is delivered by the `system_status` tool.

The context document is generated nightly (04:15). It accurately reflects
"what was true at last context generation" and carries a `generated_at`
timestamp. For "is Torre reachable right now?" or "did the backup just
fail?" — that requires a live probe that the context document cannot
provide. The `system_status` tool performs on-demand probes and reads
fresh signal files. The two mechanisms are complementary: the context
document handles routine briefing; the tool handles live interrogation.

### AD-04: The operational digest serves historical retrieval, not same-night briefing.

Nightly digest files are generated at 04:15 and indexed by the
`homelab_docs` corpus the following night (02:30 cycle). This creates
approximately a 22-hour indexing lag. "What happened last night?" answered
the same morning relies on system_status (reads current signals reflecting
the nightly cycle), not on RAG. "What happened three nights ago?" is
answered by RAG. These are distinct retrieval paths and must not be
conflated in success criteria.

### AD-05: The HA voice surface receives awareness from the same context document.

`bin/aurora-context` produces three output files: the full context JSON, the
full context markdown (for the Open WebUI Filter), and a single-line compact
variant (`aurora-context-voice.txt`) for the HA voice LLM configuration.
The voice surface does not get a separate awareness mechanism — it gets the
same context document at the same cadence, trimmed for the voice medium's
brevity constraint. Voice and chat context divergence is resolved
architecturally, not accepted as a known limitation.

### AD-06: Conversational context (session continuity) is explicitly deferred to Phase G.

`AURORA_VISION.md §5` distinguishes operational history from conversational
context. Phase F delivers operational history (the digest corpus). Session-
to-session conversational continuity requires a separate mechanism (Open
WebUI memory, or a custom approach) that is not designed in Phase F.
Implementing conversational memory in Phase F by indexing session content
into `homelab_docs` is explicitly rejected — it would pollute a knowledge
corpus with noise and solve the wrong problem.

### AD-07: The operational digest is a runtime artifact, never a Git artifact.

Digest files generated by `bin/generate-digest` are written to
`09_ops/runtime/YYYY-MM-DD_ops_digest.md`. This directory is gitignored.
No cron job ever runs `git commit`, `git push`, or `git tag`. The files are
picked up by the `homelab_docs` fs corpus on the next nightly ingest cycle
because the corpus walks the host filesystem directly — it does not require
files to be git-tracked. Untracked, gitignored files in the corpus path are
indexed identically to committed files.

This is an architectural decision, not an implementation detail. It resolves
the direct conflict between automated digest generation and the operator git
approval constraint (§13). Any future proposal to commit digest files
automatically must explicitly revise this decision and update §13.

### AD-08: F-3 is delivered as two independent sub-milestones — F-3a (chat) and F-3b (voice).

The Open WebUI Filter (chat awareness) and the HA-voice context refresh share
only the context artifact; their mechanisms are unrelated (a `webui.db` Python
Function vs. an HA `input_text` helper + Jinja2 + a nightly REST push). They are
built and gated separately. F-3a is the headline objective and ships first; F-3b
follows. F-5 (home-anomaly injection) depends on **F-3a only**.

### AD-09: Awareness-delivery consumers are source-controlled code, not runtime-only state.

The Filter is `webui.db` runtime state, exactly like the model config and tool
rows flagged in
[`openwebui_model_runtime_state.md`](openwebui_model_runtime_state.md) §4. To
avoid widening that reproducibility gap, the Filter **source** is committed to git
(`ai-stack/openwebui-tools/filters/aurora_context.py`) with an install + recovery
note, and the HA voice prompt / `input_text` changes are documented. The broader
unified `configure-model` automator (one script re-applying prompt + tools +
filter) remains a **deferred** follow-up — F-3 commits the Filter source but does
not build the unified automator.

### AD-10: The Filter keys freshness on the JSON and injects the markdown; injected content is stable within a conversation.

The Filter reads `aurora-context.json` (`generated_at`, `overall_status`) for the
staleness decision — robust machine fields, not header-string parsing or file
mtime — and injects the prose of `aurora-context.md`. The injected block carries
no per-request live timestamp, so it is identical across turns of a conversation
and does not invalidate the KV cache. Live "right now" state remains the job of
`system_status` (AD-03).

### AD-11: The injected payload is the full compact `aurora-context.md` block (not a one-liner).

The generated markdown is ~6 lines; on Torre (~101 tok/s) the token cost is
negligible, and the full block answers routine briefing passively without a tool
call (the Vision target, AD-02). A minimal `overall_status`-only one-liner was
considered and **rejected**: it would force a `system_status` call for any detail.
Reversible — revisit only if prompt-eval latency becomes material.

### AD-12: The backup signal is produced by a standalone `bin/backup-probe`, not by modifying `homelab-backup.sh`.

**Supersedes the original §6.1 / §9-F-2 "modify `homelab-backup.sh`" approach.**
F-2 implemented `bin/backup-probe` (03:30), which reads restic snapshot metadata
and writes `backup_status.json` (`schema_version`, `probed_at`, `status`,
`snapshot_id`, `snapshot_time`; `files_new` / `files_changed` / `data_added_mb`
= `null`). Rationale: the production backup script stays untouched (safer); the
snapshot list lacks per-run deltas, accepted as sufficient for context /
`system_status`. Decision origin: F2-9 closeout §6.

### AD-13: HA-voice awareness is delivered via an `input_text` helper + Jinja2, refreshed nightly.

**Supersedes the original §7 "REST API or direct config write" wording (AF-05).**
F-0 validated and improved the mechanism: an HA `input_text.aurora_voice_context`
helper (max_length 255) holds the voice line; the HA Ollama voice prompt
references it with Jinja2 `{{ states('input_text.aurora_voice_context') }}`,
rendered per request with no integration reload. A nightly step (04:20, F-3b)
pushes `aurora-context-voice.txt` into the helper via the HA REST
`input_text/set_value` service. This requires an HA long-lived token in
`ai-stack/.env` (gitignored) — a dependency that therefore arrives at **F-3b**,
earlier than the F-5 statement in §13 / §9-F-5.

---

## 4A. F3.0 Architecture Refinement — Decision Register

F3.0 (2026-06-29) reviewed every recommendation from the F-3 design review.
Outcomes:

| # | Recommendation (F-3 review) | Decision | Captured in |
|---|---|---|---|
| R1 | Split F-3 into F-3a (chat Filter) / F-3b (voice) | **Accepted** | AD-08; §9 F-3 |
| R2 | Treat the Filter as source-controlled code | **Accepted** (narrow); unified `configure-model` automator **Deferred** | AD-09 |
| R3 | Freshness decision off the JSON; inject the MD | **Accepted** | AD-10 |
| R4 | Injected payload = full compact md | **Accepted**; one-liner **Rejected** | AD-11 |
| R5 | Stable injection within a conversation (KV cache) | **Accepted** | AD-10 |
| R6 | Separate mechanism vs behavioral validation | **Accepted** | §9 F-3 (G-F3-1 vs AF-01) |
| R7 | Explicit acceptance gates G-F3-1…G-F3-8 | **Accepted — FROZEN** | §9 F-3 |
| R8 | Reconcile F-1/F-2 doc drift | **Accepted — done in F3.0** | AD-12, AD-13; §6.1, §6.2, §6.4, §7 |
| R9 | HA token dependency arrives at F-3b, not F-5 | **Accepted** | AD-13; §9 F-3b |
| R10 | Verify F-1 prompt references the injected block | **Accepted** (F3.1 entry gate) | §9 F-3 milestones |
| R11 | Smoke-re-confirm AF-01 on the running 0.8.10 build | **Accepted** (F3.1 entry gate) | §9 F-3 milestones |
| R12 | Small milestone plan | **Accepted — FROZEN** as F3.0→F3.3 | §9 F-3 milestones |

Only two items are not carried into F-3 as work: the one-liner payload
(rejected, R4) and the unified `configure-model` automator (deferred, R2).

---

## 5. Rejected Alternatives

### RA-01: Tool call only (no Filter)

**Proposal:** Deploy `system_status` and instruct Aurora to call it at
conversation start. The operator runs no commands; Aurora calls one tool.

**Why rejected:** `AURORA_VISION.md §4` states the answer to "is everything
OK?" should not require a tool call. A tool call depends on the 7B model
reliably following a behavioral instruction — at 7B scale, reliability is
high but not guaranteed. When the model fails to follow the instruction,
Diego reaches for the terminal, and the habit never forms. The tool is
valuable for on-demand live state; it is not the right mechanism for
automatic awareness.

### RA-02: Scheduled system prompt regeneration via Open WebUI admin API

**Proposal:** A cron job reads signal files and updates the model's system
prompt via the Open WebUI admin API, keeping today's state always present
in the static prompt.

**Why rejected:** The Open WebUI admin API is not documented for external
automation and has no stability guarantee. A script that patches system
prompts via an internal API takes on an invisible dependency that will break
on Open WebUI upgrades. The Filter mechanism (AD-02) achieves the same
result using the officially supported Open WebUI Function system.

### RA-03: Filter reads signal files directly

**Proposal:** The Filter reads `health.json`, `backup_status.json`, and
`container_status.json` directly from `/opt/ingest/logs/` and constructs
the context block on the fly.

**Why rejected:** This couples context construction logic to a UI plugin.
Every signal schema change requires a Filter update. Adding a new signal
requires a Filter update. The Filter should be dumb — it reads the
pre-generated context and prepends it (AD-10). Context construction belongs in
`bin/aurora-context`, where it can serve all consumers. Schema changes are
handled in one place.

### RA-04: Single RAG collection for both operational history and same-night briefing

**Proposal:** Digest files are written to `09_ops/`, indexed by
`homelab_docs`, and retrieved via `rag_search` for all operational memory
queries including "what happened last night?"

**Why rejected:** The 22-hour indexing lag means the same-night digest is
not in RAG. Aurora would fail the "what happened last night?" query on the
morning it matters most. Same-night briefing is served by system_status
(current signals). Historical retrieval (≥22h old) is served by RAG.
Two different problems require two different retrieval paths.

---

## 6. Context Architecture

This is the central new component Phase F introduces. Everything in Domain A
depends on it.

### 6.1 Signal Layer

Raw operational signals. Each is written by its natural producer to its
natural location. They do not exist for Aurora's benefit — they are system
signals that Aurora happens to be able to read.

| Signal file | Written by | Schedule | Schema |
|---|---|---|---|
| `ai-stack/ingest/logs/health.json` | `ingest-nightly` (ingest section) + `check-audit-liveness` (audit section) | 02:30 + 03:30 | `overall_status`, `ingest.*`, `audit.*` — see contract |
| `ai-stack/ingest/logs/backup_status.json` | **`bin/backup-probe`** (standalone — reads restic snapshot metadata; **AD-12**, not `homelab-backup.sh`) | 03:30 | `schema_version`, `probed_at`, `status`, `snapshot_id`, `snapshot_time`; `files_new` / `files_changed` / `data_added_mb` = `null` |
| `ai-stack/ingest/logs/container_status.json` | new host-side `bin/container-probe` script | nightly at 04:00 | `generated_at`, `containers: [{name, status, running}]` |

`backup_status.json` and `container_status.json` were created in F-2
(`bin/backup-probe` at 03:30; `bin/container-probe` at 04:00). `bin/aurora-context`
degrades gracefully if any signal is missing or stale (≥26h): it omits or marks
the section and records the gap in `signals_missing` — it does not guess.

### 6.2 Context Generation

`bin/aurora-context` is the only component that reads signal files and knows
their schema. It reads all available signal files, constructs a structured
context, and writes three output artifacts.

```
ai-stack/ingest/logs/
├── health.json           ─┐
├── backup_status.json    ─┤──▶  bin/aurora-context  ──▶  ai-stack/aurora/
└── container_status.json ─┘                               ├── aurora-context.json
                                                           ├── aurora-context.md
                                                           └── aurora-context-voice.txt
```

**`aurora-context.json`** — structured, machine-readable. Fields:

```json
{
  "schema_version": 1,
  "generated_at": "2026-06-28T04:15:00Z",
  "overall_status": "ok | degraded | unknown",
  "ingest": { "status": "ok", "last_run_end": "...", "last_run_rc": 0 },
  "backup": { "status": "ok", "snapshot_id": "...", "snapshot_time": "...", "data_added_mb": null },
  "audit": { "status": "ok", "age_days": 0 },
  "containers": { "all_running": true, "count": 17, "degraded": [] },
  "home": { "anomalies": [] },
  "signals_missing": []
}
```

**`aurora-context.md`** — LLM-formatted, human-readable. Consumed by the
Open WebUI Filter. Format: compact, timestamped, honest about missing
signals and their age. Actual F-2 output (2026-06-29):

```
[Aurora context — 2026-06-29 10:38 UTC]

Status:      ok

Ingest:      ok — last run 2026-06-29 00:30 UTC (10.1h ago, rc=0)
Backup:      ok — snapshot c38ddcc1 at 2026-06-29 01:00 UTC (9.6h ago)
Audit:       ok — last entry age 0 days
Containers:  17/17 running
```

The block is multi-line labelled (not a single prose line) and carries no live
Torre line — live Torre reachability is `system_status` only (AD-03).

**`aurora-context-voice.txt`** — single-line compact variant for the HA
voice LLM configuration. Budget: ≤200 characters. Contains the timestamp,
overall_status, last backup result, container summary, and any anomalies.
Actual F-2 format:

```
2026-06-29 04:15 | ok | backup ok | 17/17 running | no anomalies
```

If a signal file is missing, `aurora-context` notes it in the appropriate
field: "backup: signal missing". Graceful degradation means saying less,
not guessing. The `signals_missing` array in the JSON records which signals
were absent at generation time.

### 6.3 Runtime Directories

Two runtime directories are created by Phase F. Both are gitignored. Neither
is backed up by restic (generated artifacts — lost on server failure and
regenerated on the next nightly cycle; no operational state is lost).

**`ai-stack/aurora/`** — Aurora's context artifacts home. Distinct from
`ai-stack/ingest/` (the knowledge platform service). Bind-mounted read-only
into the `openwebui` container as `/opt/aurora`. The Filter and
`system_status` tool read from this path inside the container.

**`09_ops/runtime/`** — operational digest home. Gitignored but within the
`homelab_docs` fs corpus path, so digest files are indexed by the next
nightly ingest sync without any git operation (see AD-07).

Add to repo `.gitignore`:
```
ai-stack/aurora/
09_ops/runtime/
```

Bind-mount addition for the `openwebui` container (requires `docker compose
up -d openwebui` to apply — brief container restart; do during low-activity
window):
```
ai-stack/aurora:/opt/aurora:ro
```

### 6.4 Nightly Cron Order

The complete nightly schedule after all Phase F sub-phases are implemented.
This is the committed ordering; changes require a deliberate decision.

| Time | Script | Writes |
|---|---|---|
| 02:30 | `ingest-nightly` | `health.json` (ingest section) |
| 03:00 | `homelab-backup.sh` | restic snapshot only — **does not** write `backup_status.json` (AD-12) |
| 03:30 | `check-audit-liveness` | `health.json` (audit section) |
| 03:30 | `bin/backup-probe` | `backup_status.json` (F-2; reads the 03:00 snapshot — AD-12) |
| 04:00 | `bin/container-probe` | `container_status.json` (F-2) |
| 04:15 | `bin/aurora-context` | `aurora-context.json`, `aurora-context.md`, `aurora-context-voice.txt` (F-2) |
| 04:20 | `bin/generate-digest` (F-4) + HA voice `input_text` push (F-3b) | `09_ops/runtime/YYYY-MM-DD_ops_digest.md`; `input_text.aurora_voice_context` set via HA REST (AD-13) |

`bin/generate-digest` and the HA voice refresh are sequential steps at 04:20.
They may be combined into one script or adjacent cron entries separated by
30 seconds; the ordering between them is not critical.

### 6.5 Knowledge Layer Routing

The knowledge layer is split into semantically distinct corpora. Aurora
reasons in terms of knowledge domains; collection names are an
implementation detail confined to the tool layer.

**Corpus inventory**

| Corpus | Source path | Knowledge type | Access |
|---|---|---|---|
| `homelab_docs` | `/home/diego/homelab/**` (excl. `09_logs/`) | Living docs — current state of AMAROLAB | `rag_search` |
| `knowledge_history` | `/home/diego/homelab/09_logs/` (seed; expandable) | Historical records — what happened, why, which phase | `rag_search` |
| `infra_audits` | `/home/diego/server-audit-2026-06-13/` | Phase 0/1 infrastructure audit reports; R-XX remediation records | `audit_search` (hardcoded) |
| `guardian_cloud` | `/mnt/storage/projects/guardian-cloud/` | Guardian Cloud project documentation | `rag_search` |
| `ensambla2` | `/mnt/storage/projects/ensambla2/` | Ensambla2 project documentation | `rag_search` |
| `myfreetour` | TBD | Placeholder | disabled |

**Collection-level routing policy**

| Query intent | Domain label | Collection | Tool |
|---|---|---|---|
| Current state, config, living docs | Current documentation | `homelab_docs` | `rag_search` |
| Past events, decisions, phase history | Historical records | `knowledge_history` | `rag_search` |
| Phase 0/1 audit, R-XX remediation | Infrastructure audit | `infra_audits` | `audit_search` |
| Guardian Cloud | Guardian Cloud docs | `guardian_cloud` | `rag_search` |
| Ensambla2 | Ensambla2 docs | `ensambla2` | `rag_search` |
| Live datetime | — | — | `time_now` |
| HA entity state | — | — | `ha_get_state` |
| HA action | — | — | `ha_call_service` |
| Live call log | _(not yet available)_ | — | _(future tool — not in F-2/F-3; deferred)_ |

**Separation rationale:** `homelab_docs` indexes living documentation that
describes current state. `knowledge_history` indexes historical records
(apply logs, closeout reports, gate results) that may contain quoted
wrong answers, documented failures, and negative examples. Mixing these
in a single corpus causes high-relevance historical chunks to outrank
authoritative living docs for factual queries (observed and fixed in
F-1, 2026-06-28). The two corpora serve different retrieval intents and
must not compete in the same collection.

**Prompt / tool layer boundary:** The system prompt describes knowledge
domains by intent only (current documentation, historical records). The
tool layer (`rag_search` docstring, `collection` Literal parameter)
maps domains to collection names. Collection names must not appear in
the system prompt; they may change without requiring a prompt update.

**Expandability of `knowledge_history`:** The corpus is seeded from
`09_logs/` but is not tied to it. Additional historical source paths
(e.g., past project retrospectives, archived architecture docs) can be
added to `corpora.yaml` as separate `knowledge_history` fs entries or
by broadening the include globs. The Qdrant collection name and routing
intent remain stable.

---

## 7. Consumer Model

All consumers are dumb. They read; they do not reconstruct.

| Consumer | What it reads | When | How |
|---|---|---|---|
| Open WebUI Filter | `/opt/aurora/aurora-context.json` (freshness) + `aurora-context.md` (payload) | Message 1 of each conversation | Reads JSON `generated_at` / `overall_status` for the staleness decision; prepends the markdown prose as a system-message block; fires on inlet; degrades gracefully if missing/stale (AD-10) |
| HA voice system prompt | `/opt/aurora/aurora-context-voice.txt` | Nightly refresh (04:20) | Nightly step pushes the single line into `input_text.aurora_voice_context` via HA REST `input_text/set_value`; the voice prompt renders it per-request with Jinja2 `{{ states('input_text.aurora_voice_context') }}` — no reload (AD-13; supersedes the original REST/config-write wording; F-0 AF-05) |
| `system_status` tool | `/opt/aurora/aurora-context.json` + live probes | On demand | Reads context JSON for pre-generated state; adds live Torre probe + fresh health.json read; returns per-field timestamps so data age is always visible |
| Future consumers | `/opt/aurora/aurora-context.md` or `.json` | At session start | Same pattern — read the file |

**Filter behaviour contract:**
- Fires on inlet (user message), not outlet.
- Checks if this is message 1 (conversation history length == 0 or 1).
- Reads `/opt/aurora/aurora-context.json` for `generated_at` / `overall_status` (freshness/decision) and `/opt/aurora/aurora-context.md` for the injected prose (AD-10).
- Age is computed from `generated_at` (not file mtime). If **≤26h**: prepends the markdown block. If age is between 24h and 26h, the block includes a note: "[context is N hours old — use system_status for current state]".
- If the files are **missing, unreadable, or older than 26h**: prepends a minimal fallback only: "Context file unavailable — use system_status for current state." Never crashes the conversation.
- Injected content is identical across turns of a conversation (no per-request timestamp) so the KV cache is preserved (AD-10).
- Does not fire on messages 2, 3, etc.

Note: 26h is a single threshold with a graduated response. There is no undefined behavior between 24h and 26h. The nightly generation at 04:15 ensures the file is always replaced well within the 26h window under normal operation; the threshold only activates during a nightly cycle failure.

**`system_status` tool contract:**
- Reads `/opt/aurora/aurora-context.json` for pre-generated signals.
- Reads `/opt/ingest/logs/health.json` fresh (live signal, not cached in context).
- Performs a live HTTP probe of Torre's Ollama endpoint (2-second timeout).
- Returns a structured summary with timestamps for every field so Aurora can communicate data age honestly.

---

## 8. Dependency Map

```
F-0 (Behavioral Audit — read-only, no build)
 │
 ├──▶ F-1 (System Prompt + Identity)
 │      │
 │      ├──▶ F-2 (Signal Layer + bin/aurora-context + system_status tool)
 │      │      │
 │      │      ├──▶ F-3 (Open WebUI Filter)
 │      │      │      │
 │      │      │      └──▶ F-5 (Home Intelligence)  ◀── also depends on F-2
 │      │      │               (extends bin/aurora-context from F-2)
 │      │      │
 │      │      └──▶ F-4 (Operational Digest + Memory Corpus)
 │      │
 │      └──▶ F-5 (system prompt home model reference)
 │
 └──▶ F-6 (Voice Quality)  ◀── parallel track; no dependency on F-2..F-5
```

**Critical path:** F-0 → F-1 → F-2 → F-3 (F-3a then F-3b) → F-5 (with F-4 branching from F-2 in parallel). F-5 depends on **F-3a** — the Filter mechanism (AD-08).

**Parallel track:** F-6 can begin after F-0 (behavioral audit validates the
voice gap) and run concurrently with F-2 through F-5.

**F-1 is a prerequisite for F-3:** The system prompt must be redesigned
before the Filter is deployed, because the Filter injects context that the
system prompt must reference correctly ("the following context was generated
at..."). Deploying the Filter against the current stale 822-token prompt
would produce incoherent results.

---

## 9. Phase F Sub-Phases

### F-0 — Behavioral Audit

**Objective:** Establish a validated baseline. No implementation.

**Scope:**
- 10-query behavioral test: correct tool routing, honesty about unknown
  state, voice accuracy sample
- System prompt audit: token count, stale claims, missing tool descriptions
- HA entity inventory: all entities, domains, current states, expected
  baseline states
- Open WebUI Filter mechanism validation: confirm inlet fires on message 1
  only; confirm file-not-found does not crash
- Signal gap confirmation: verify `backup_status.json` does not exist;
  verify `container_status.json` does not exist
- Torre probe validation: confirm live HTTP check from host and from inside
  the openwebui container reaches Torre's Ollama endpoint

**Output:** Finding register AF-01 through AF-N (see §11 for pre-identified
findings). Every Phase F implementation decision is grounded in an F-0
finding.

**Success criterion:** Finding register produced and complete. No
assumptions remain unvalidated. No implementation has begun.

---

### F-1 — System Prompt Redesign

**Objective:** Aurora has a coherent identity, knows its tools, and
communicates with appropriate style. Token budget is freed for context
injection.

**Scope:**
- Rewrite the Open WebUI system prompt (target: ≤400 tokens, down from 822)
- Content: Aurora's identity and scope; available tools with routing
  guidance (when to call what); communication principles (direct, brief,
  honest, no padding); capability self-awareness (what Aurora can and cannot
  do); explicit instruction to read the injected context block and
  acknowledge it in the first response if the context reveals a degraded
  state
- HA voice system prompt: separate, compact version for the voice surface
  (optimises for brevity; voice ≤2-turn interactions); reviewed and
  updated as part of F-1 (not deferred to F-6)
- Both prompts authored with F-3 in mind: they reference the context block
  that the Filter will inject

**What F-1 does not do:** F-1 does not deploy the Filter. It does not add
new signals. It is identity and routing only.

**Success criterion:** Cold-cache prompt evaluation latency reduced
(measured, baseline from F-0); Aurora routes correctly to each tool in a
10-query behavioral test matching F-0's baseline; no hallucinated
capabilities; Aurora voice prompt updated and validated on the HA surface.

**Dependencies:** F-0 findings (system prompt must address found gaps and
stale claims).

---

### F-2 — Signal Layer and Context Generation

**Objective:** All signals exist. `bin/aurora-context` runs. Context files
are generated and accessible to consumers. `system_status` tool is deployed.

> **As built (F3.0 reconciliation):** F-2 is **complete** (closed 2026-06-29,
> F2-9). One scope item changed: the backup signal was delivered as a standalone
> `bin/backup-probe` (03:30) reading restic snapshot metadata — `homelab-backup.sh`
> was **not** modified (AD-12). The "modify `homelab-backup.sh`" wording in the
> Scope and Dependencies below is superseded.

**Scope:**
- Modify `homelab-backup.sh`: add JSON result write to
  `ai-stack/ingest/logs/backup_status.json` immediately after the restic
  run completes (exit code, snapshot ID, size, duration, prune count)
- Write `bin/container-probe`: lightweight host-side script that calls the
  Docker API (or `docker inspect`) for all running containers and writes
  `ai-stack/ingest/logs/container_status.json`; scheduled at 04:00 or on
  a 30-minute interval
- Write `bin/aurora-context`: reads all three signal files; builds
  `ai-stack/aurora/aurora-context.json` and `ai-stack/aurora/aurora-context.md`;
  handles missing signal files gracefully (logs the gap, omits the section
  from output, does not error); scheduled at 04:15 (after `container-probe`)
- Create `ai-stack/aurora/` directory; add generated files to `.gitignore`
- Add `ai-stack/aurora:/opt/aurora:ro` bind-mount to the `openwebui`
  container (requires `docker compose up -d openwebui` to apply)
- Write `tools/system_status.py`: production tool that reads
  `/opt/aurora/aurora-context.json` for pre-generated state; reads
  `/opt/ingest/logs/health.json` fresh; performs live Torre HTTP probe;
  returns structured JSON with per-field timestamps. Install via
  `bin/install_tool` (no container recreate needed for tool-only changes)
- Validate one full nightly cycle with all three signal files present

**What F-2 does not do:** F-2 does not deploy the Filter (that is F-3).
The context files are generated and accessible; no consumer reads them yet
except the system_status tool.

**Success criterion:** After one nightly cycle: `backup_status.json` exists
with correct content; `container_status.json` exists with all 17 containers
listed; `aurora-context.json` and `aurora-context.md` exist with correct
content; `system_status` tool called from Open WebUI returns accurate
platform health, last backup result, container health, and Torre
reachability; degraded state (e.g., artificial backup failure) correctly
propagated through all layers.

**Dependencies:** F-1 (system prompt must reference system_status tool);
`homelab-backup.sh` runs at 03:00, must be modified before the next nightly
cycle after F-2 work begins.

---

### F-3 — Situational Awareness (FROZEN at F3.0, 2026-06-29)

**Objective:** Opening a conversation gives Aurora current lab state without
any tool call.

F-3 is split into **F-3a (chat Filter)** and **F-3b (HA voice)** (AD-08). The
Filter behaviour contract in §7 is the authoritative mechanism spec; the
decisions AD-08…AD-13 are binding. This sub-phase, its acceptance gates, and
its milestones are **frozen** as of F3.0 — changes require a recorded revision
(§15), not drift.

#### F-3a — Open WebUI Awareness Filter

**Scope:**
- Implement the Open WebUI Filter as **committed source** at
  `ai-stack/openwebui-tools/filters/aurora_context.py` (AD-09), installed via a
  documented path, with an install + recovery note. No new runtime-only state.
- Behaviour per §7: reads the JSON for freshness, injects the markdown payload,
  message-1-only, ≤26h graduated/fallback, stable injection (AD-10, AD-11).

**Acceptance gates (FROZEN):**
- **G-F3-1** — New conversation, "¿cómo está el lab?" → accurate answer **from
  the injected block**, **zero entries in the tool-call log**, response cites
  `generated_at`. *(Behavioral efficacy — distinct from AF-01's mechanism check.)*
- **G-F3-2** — Messages 2+ in the same conversation → no re-injection
  (no duplication; verified in inlet logs).
- **G-F3-3** — Degraded propagation → an artificially degraded context surfaces
  in the first answer and Aurora points to `system_status` for live confirmation.
- **G-F3-4** — Fallback → missing/unreadable/>26h file = minimal fallback line;
  conversation never crashes.
- **G-F3-5** — Graduated note appears for a 24–26h-old file.
- **G-F3-6** — Intra-day boundary. Setup: inject an "ok" block, then create a
  real fault after generation (e.g. stop a non-critical container). Trigger:
  "¿puedes confirmar que todo sigue bien ahora mismo?". **Pass:** Aurora invokes
  `system_status` (live) and answers from that result — it does **not** assert
  the stale "ok" block as current.
- **G-F3-7** — No routing regression: the 4/4 tool-routing baseline still passes
  with the block present.
- **Repro gate** — Filter source committed + install/recovery documented (AD-09).

#### F-3b — HA Voice Awareness Refresh

**Scope (AD-13):**
- Create `input_text.aurora_voice_context` (max_length 255, via YAML).
- One-time: add Jinja2 `{{ states('input_text.aurora_voice_context') }}` to the
  HA Ollama voice prompt.
- Add the 04:20 nightly push: write `aurora-context-voice.txt` into the helper
  via HA REST `input_text/set_value`. Requires an HA long-lived token in
  `ai-stack/.env` (gitignored) — **this dependency arrives at F-3b** (AD-13),
  not first at F-5.

**Acceptance gate (FROZEN):**
- **G-F3-8** — First voice exchange of the day reflects the latest
  `aurora-context-voice.txt` via the helper + Jinja2; the nightly push is
  verified end-to-end; the HA token never appears in any committed artifact.

#### Frozen implementation milestones

| Milestone | Content | Type |
|---|---|---|
| **F3.0** | Architecture refinement & freeze (this revision) | docs only — **current** |
| **F3.1** | F-3a: entry-verify (installed F-1 prompt references the block; smoke-re-confirm AF-01 on the running 0.8.10 build; confirm `/opt/aurora/aurora-context.md` fresh in-container) → implement committed Filter → install → validate G-F3-1…G-F3-7 | build + validate |
| **F3.2** | F-3b: `input_text` helper + Jinja2 prompt ref + 04:20 `set_value` push + HA token in `.env` → validate G-F3-8 | build + validate |
| **F3.3** | Reconciliation & closeout: update the overview triad + this doc's F-3 status to complete; closeout log; STOP at git gate | docs + git |

**Dependencies:** F-2 (context artifacts + `/opt/aurora` bind-mount +
`system_status`) — **complete/verified**; F-1 (prompt must reference and
interpret the block) — **verify at F3.1 entry**; F-0 AF-01 (Filter mechanism
CONFIRMED), AF-05 (voice mechanism CONFIRMED+SUPERSEDED → AD-13), AF-07 (Torre
probe CONFIRMED).

**Mechanism vs behavior (binding):** AF-01 validated *delivery* (inlet / file /
graceful degradation) against the old prompt. F-3a's gates validate *behavioral
efficacy* with the current F-1 prompt + a real block — these are not the same
check, and **G-F3-1 is not satisfied by AF-01**.

---

### F-4 — Operational Digest and Memory Corpus

**Objective:** Aurora answers "what happened three nights ago?" from
structured operational history retrieved via RAG.

**Scope:**
- Write `bin/generate-digest`: runs at 04:20 (after `bin/aurora-context`);
  reads `aurora-context.json` (current nightly cycle data); writes to
  `09_ops/runtime/YYYY-MM-DD_ops_digest.md`. This directory is gitignored
  (AD-07). The `homelab_docs` fs corpus picks up the file on the next
  nightly 02:30 ingest sync — no git operation is required or permitted.
  The nightly cron job never runs `git commit`, `git push`, or `git tag`.
- Digest schema (stable — do not change without updating all existing
  digests or accepting a retrieval inconsistency): date header, ingest
  summary (per-corpus: points before/after, files changed, errors),
  backup summary (snapshot ID, size, exit code, duration, prune count),
  health summary (`overall_status` at generation time), notable events
  (collection grew or shrank by >5%), generated_at timestamp.
- Confirm `09_ops/runtime/**/*.md` is covered by the existing `**/*.md`
  glob in the `homelab_docs` corpus include pattern (validate in AF-08).
- Validate: after two nightly cycles, "what happened on the night of
  [date]?" answered from RAG with the correct digest content.

**Success criterion:** After two nightly cycles: two dated digest files exist
in `09_ops/runtime/`; both are indexed in `homelab_docs`; `rag_search`
against "homelab_docs" retrieves the correct digest for a specific date
query; digest content is accurate (matches signals from that night's cycle);
Aurora correctly communicates that same-night digests are not yet
retrievable via RAG and offers system_status instead; no git commit has
run automatically.

**Dependencies:** F-2 (`bin/generate-digest` reads `aurora-context.json`,
which F-2 creates); AF-08 (runtime path indexing validated in F-0);
the 22-hour indexing lag is known and accepted (AD-04).

---

### F-5 — Home Intelligence

**Objective:** Aurora has a defined home model, reasons about expected
device states, and the Filter surfaces home anomalies automatically.

**Scope:**
- Write `04_ai_system/home_model.md`: complete inventory of all meaningful
  HA entities in the current home; per-entity: domain, object_id, purpose,
  read-only or writable, always-on or schedule-following, expected baseline
  state, anomaly definition (e.g., "printer on between 00:00 and 06:00 is
  anomalous"). This document is the source of truth for home context.
- Update system prompt (F-1 prompt) with home model summary: which entities
  Aurora knows, what their baseline states are, what to surface if an entity
  is in anomalous state.
- Extend `bin/aurora-context` to include a home state section: on each
  generation cycle, call the HA REST API directly for key entities (not
  the `ha_get_state` tool, which is an Open WebUI tool and not available
  from host cron scripts); compare results to expected baseline from
  `home_model.md`; include any anomalies in `aurora-context.json`
  (`home.anomalies` array) and in `aurora-context.md`. The Filter then
  surfaces home anomalies automatically at conversation start.
- **Prerequisite — HA credential surface:** `bin/aurora-context` requires a
  HA long-lived access token to call the HA REST API. This token must exist
  in `ai-stack/.env` (gitignored, consistent with other AMAROLAB secrets)
  before F-5 implementation begins. It is never committed. If HA is
  unreachable at 04:15 context generation time, the home section of
  `aurora-context.json` is set to `{"anomalies": ["ha_unavailable"]}` and
  the context markdown says "Home: HA unreachable at context generation —
  use ha_get_state for current state." Graceful degradation applies.
- Evaluate `ha_call_service` allowlist: if new home devices have been added
  since the last gate review, run per-domain gate validation and extend the
  allowlist for approved domains. No domain is added without gate validation.

**What F-5 explicitly does not do:** Aurora does not autonomously act on
anomalies. It surfaces them. The operator decides what to do. This boundary
is from `AURORA_VISION.md §7` ("Aurora is not autonomous") and does not
relax in Phase F.

**Success criterion:** `home_model.md` exists and is complete for the
current device inventory; Aurora answers questions about any entity in the
home model in a single exchange; a test anomaly (printer manually turned on
at midnight) surfaces in the Filter context block in the next conversation
after it is detected; `ha_call_service` allowlist reflects the current
approved device surface; HA credential is stored in `ai-stack/.env` and
never appears in any committed file or context artifact.

**Dependencies:** F-3 (anomaly detection requires the Filter's context
block; home anomalies are injected the same way as platform health);
F-2 (F-5 extends `bin/aurora-context`, which F-2 introduces);
F-1 (system prompt references the home model).

---

### F-6 — Voice Quality

**Objective:** Voice interactions are reliable enough in Spanish to become
a daily habit.

**Scope:**
- Upgrade `aurora-whisper` (HA voice pipeline) from `base-int8` to `small`
  or `medium-int8` Whisper model. Re-run G-D1 and G-D4 gate validation
  (accuracy and latency gates from Phase D).
- Migrate `aurora-whisper-http` (Open WebUI voice path) from
  `fedirz/faster-whisper-server` (unmaintained — R-D-13) to a maintained
  alternative. Re-validate Open WebUI voice transcription path.
- Establish end-to-end latency baseline: wake word to response audio
  complete, under Torre-primary and UM790-fallback inference paths.
  Document the baseline in `09_logs/`.
- Validate cold-cache prompt evaluation improvement from F-1's token
  reduction contributes to voice latency.

**Parallelism:** F-6 has no dependency on F-2 through F-5. After F-0
validates the voice quality gap (AF-voice in the finding register), F-6
can run concurrently with the awareness and memory build.

**Success criterion:** Spanish short utterances ("apaga la impresora",
"cierra el toldo") transcribed correctly ≥9/10 trials without repetition;
end-to-end latency baseline documented; R-D-13 resolved; no regression in
English accuracy.

**Dependencies:** F-0 (voice quality gap confirmed and measured); F-1
(HA voice system prompt updated — reduces total response latency).

---

## 10. Dependency Map (Detailed)

```
F-0 Behavioral Audit
│  ├─ validates Filter mechanism (AF-01)
│  ├─ confirms backup signal gap (AF-02)
│  ├─ validates digest fs-corpus indexing (AF-08)
│  ├─ inventories HA entities (AF-06)
│  └─ measures voice quality gap

├──▶ F-1 System Prompt
│       Prerequisite for: F-2 (tool referenced in prompt), F-3 (prompt must
│       interpret context block), F-5 (home model described in prompt),
│       F-6 (voice prompt authored)
│
├──▶ F-6 Voice Quality (parallel — starts after F-0)
│
└──▶ F-2 Signal Layer + Context Generation
        │  Prerequisite for: F-3 (Filter reads context files),
        │                    F-4 (digest reads aurora-context.json),
        │                    F-5 (extends bin/aurora-context from F-2)
        │
        ├──▶ F-3 Awareness  (F-3a Filter, then F-3b voice — AD-08)
        │       Prerequisite for: F-5 (home anomaly injection uses
        │                         the F-3a Filter mechanism)
        │
        ├──▶ F-4 Operational Digest (parallel with F-3)
        │
        └──▶ F-5 Home Intelligence
                Depends on: F-2 (code), F-3 (Filter mechanism), F-1 (prompt)
```

---

## 11. Architectural Risks — Finding Register

Pre-identified findings for F-0 to validate. Each finding is either
confirmed, disproved, or superseded by F-0's behavioral audit. No finding
is assumed closed until F-0 explicitly closes it.

> **Post-F-0 (2026-06-28):** F-0 is complete; the authoritative validation
> outcomes are in
> [`../09_logs/2026-06-28_phaseF_F0_audit_report.md`](../09_logs/2026-06-28_phaseF_F0_audit_report.md) §5.
> The pre-mitigation column below is the *pre-F-0 plan* and is not maintained —
> some items are superseded (e.g. AF-02's "until `homelab-backup.sh` is modified"
> → AD-12; AF-07's `torre_status.json` fallback was unnecessary — the container
> reaches Torre directly). **Caution:** the F-0 report reused IDs **AF-04** and
> **AF-06** for different items than this pre-F-0 register — cross-reference by
> description, not by number.

| ID | Description | Severity | Pre-mitigation |
|---|---|---|---|
| AF-01 | Open WebUI Filter mechanism not validated. The inlet/outlet behavior, message-1 detection, and file-not-found handling must be confirmed in the running version before committing to the architecture. | High | Validate in F-0 with a minimal test Filter before building the production Filter. |
| AF-02 | `backup_status.json` does not exist. No structured backup signal is available until `homelab-backup.sh` is modified. Both `bin/aurora-context` and `bin/generate-digest` depend on it. | High | First deliverable of F-2. Confirm gap in F-0. `aurora-context` must degrade gracefully until F-2 is complete. |
| AF-03 | `container_status.json` does not exist. Docker container health is unavailable to the context layer without a new probe script. | Medium | Part of F-2. Until it exists, context document omits container health; `aurora-context` logs the missing signal. |
| AF-04 | Digest indexing lag. Same-night digest is not retrievable via RAG for ~22 hours. Aurora must not claim RAG-retrieved operational history for the current night's cycle. | Medium | Accepted per AD-04. System prompt and Filter content must communicate this clearly. |
| AF-05 | HA voice system prompt update mechanism. The method for updating the HA voice LLM system prompt from a nightly script (REST API vs. config file write) has not been validated. If the mechanism is not stable or requires HA restart, the nightly refresh cannot be automated reliably. | Medium | Validate in F-0 or early F-1. If automated refresh is not feasible, the voice system prompt is updated manually each phase; document as a known manual step. |
| AF-06 | Home model is undefined. F-5 cannot begin until the HA entity inventory is complete and the home model document is written. F-0's HA entity audit is a prerequisite. | Low | F-0 produces the entity inventory. F-5 formalises it. Not blocking until F-5. |
| AF-07 | Torre reachability probe from inside openwebui container. The live Torre HTTP probe in `system_status` requires network connectivity from inside the openwebui container to Torre's Tailscale address. This is not validated. | Low | Validate in F-0. If container-to-Tailscale routing does not work, the probe must run on the host and write a `torre_status.json` signal file instead. |
| AF-08 | Runtime digest path not validated for fs-corpus indexing. AD-07 requires that untracked, gitignored files in `09_ops/runtime/` are picked up by the `homelab_docs` fs corpus. This is the assumed behavior of the `fs` corpus type but has not been confirmed in the running system. | Medium | Validate in F-0: write a test file to `09_ops/runtime/`, run `bin/ingest sync --collection homelab_docs`, confirm the file is indexed and retrievable via `bin/ingest search`. Close AF-08 only after retrieval is confirmed. |

---

## 12. Success Criteria — Phase F Complete

Phase F is complete when all of the following are true. These are
observable behaviours, not technical metrics (per `AURORA_VISION.md §3`).

**Briefing works.** Diego opens a conversation after any absence. Without
running any command or explicitly calling a tool, Aurora gives an accurate
and honest status of the most recent completed nightly cycle: ingest result,
backup result, service health, home anomalies (if any). The answer
references when the context was generated. If the context is from the
previous night's cycle, Aurora says so. Intra-day events that occur after
04:15 are surfaced by `system_status` on demand, not by the pre-generated
context; this is expected behavior, not a failure. If Torre is offline,
Aurora says so or acknowledges uncertainty.

**Action is frictionless.** Any device in the defined home model can be
queried or controlled by voice or text in a single, natural exchange. A
voice command for a known device works on the first attempt ≥9/10 trials.

**Knowledge is connected.** When asked about a recent operational event
("what happened to the backup three nights ago?"), Aurora retrieves the
correct operational digest via RAG and answers from it, not from
hallucination.

**Silence is informative.** When Aurora's context block says everything is
OK, Diego trusts that assessment enough to not verify it independently. This
is a habit change, not a technical milestone. It is evaluated subjectively
after four weeks of daily use.

**Voice is reliable.** Spanish short utterances work. Voice is used daily
without frustration.

---

## 13. Implementation Constraints

These constraints govern all Phase F implementation. Violating them requires
an explicit decision recorded in the relevant apply log.

| Constraint | Rule |
|---|---|
| Operator git approval | Never run `git commit`, `git push`, or `git tag` without explicit operator approval immediately before each command. Approval does not carry over between commands or sessions. |
| No secrets in git | All sensitive values (API keys, tokens, passwords) use placeholder values in committed files. The `.env` files are gitignored and never staged. |
| No `git add .` | Stage files individually by name. |
| Production Qdrant | Must not be stopped, restarted, remounted, or modified outside of a planned procedure. |
| Guardian Cloud boundary | Read-only. Aurora may retrieve Guardian Cloud documentation. It may not call Guardian Cloud APIs, modify Guardian Cloud state, or access Guardian Cloud infrastructure. |
| `QDRANT__SERVICE__API_KEY` | The actual Qdrant API key variable is `QDRANT__SERVICE__API_KEY` (not `QDRANT_API_KEY`). Its value must never appear in documentation, context files, or any committed artifact. |
| `health.json` | Gitignored runtime state. Must not be committed. |
| `aurora-context.json` / `aurora-context.md` / `aurora-context-voice.txt` | Generated runtime artifacts. Must not be committed. Add `ai-stack/aurora/` to `.gitignore` before the first `bin/aurora-context` run. |
| Digest files (`09_ops/runtime/`) | Runtime artifacts. Must not be committed automatically. The nightly cron cycle never runs `git commit`, `git push`, or `git tag`. Digest files are gitignored and indexed by the `homelab_docs` fs corpus without git involvement (AD-07). |
| HA REST API token (F-3b + F-5) | First required at **F-3b** for the voice `input_text/set_value` push (AD-13), then by `bin/aurora-context` at F-5 for the home-state section. Stored in `ai-stack/.env` (gitignored). Never committed. Never appears in any context artifact, apply log, or documentation. Managed identically to other AMAROLAB secrets. |
| Embedding model | `intfloat/multilingual-e5-small` (384-dim) is locked per D-08. Do not change without a full re-embed migration of every collection. |
| Allowlist discipline | `ha_call_service` domain allowlist is expanded only through per-domain gate validation (same process as Phase C). No domain is added speculatively. |
| Aurora does not self-modify | Aurora cannot expand its own action surface. Tool allowlists are operator-defined and operator-revised. |
| `homelab-backup.sh` is production | Modification requires care. The script runs at 03:00 nightly. Changes must be validated before the next nightly cycle. Backup must continue to function correctly after F-2 modification. |

---

## 14. What Phase F Does Not Build

Explicit deferrals. These are not forgotten — they are named here so they
are not accidentally implemented in Phase F.

| Deferred | Why | Target phase |
|---|---|---|
| Conversational context (session continuity) | Different architecture from operational history; Phase F delivers operational history first | Phase G |
| Proactive behaviour (morning summaries, anomaly push notifications) | Requires awareness and memory layers to be stable first | Phase G+ |
| Dynamic system prompt regeneration via Open WebUI admin API | API stability risk; the Filter architecture achieves the same result safely | Phase G (re-evaluate) |
| Torre always-on reachability monitoring | Reactive probe (on demand) is sufficient for Phase F | Phase G |
| Larger inference model (e.g., qwen2.5:14b or equivalent) | Real quality gap must be measured first; Torre upgrade path may change the tradeoffs | Phase G |
| MyFreeTour knowledge corpus | Source path unknown (B-08 blocker) | When blocker resolves |
| Multi-user Aurora | AMAROLAB is a single-operator system; no requirement exists | Future |

---

## 15. Revision Log

| Date | Revision | Summary |
|---|---|---|
| 2026-06-28 | Authored (F-0 pre-work) | Original approved Phase F architecture. |
| 2026-06-29 | **F3.0 — Architecture Refinement** | Reviewed the F-3 design; recorded the decision register (§4A) and AD-08…AD-13. Reconciled F-1/F-2 drift: backup signal is `bin/backup-probe` at 03:30, not `homelab-backup.sh` (AD-12; §6.1/§6.4); HA-voice mechanism is `input_text` + Jinja2 (AD-13; §7); `aurora-context.md` example replaced with real F-2 output (§6.2); §2 marked as a pre-F baseline (live state in CURRENT_STATE.md). Split F-3 into F-3a/F-3b; **froze** the F-3 architecture, acceptance gates (G-F3-1…G-F3-8), and milestones (F3.0→F3.3). No code/prompt/container/DB/Open WebUI changes. Next: operator approval before F3.1. |
