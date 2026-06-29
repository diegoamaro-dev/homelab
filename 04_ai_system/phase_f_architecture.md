# Phase F — Architecture Document

- **Status:** Approved — revised at F3.0; **F-3 implemented + closed at F3.3
  (2026-06-29)**. Governs all Phase F implementation decisions. The F-3
  architecture, acceptance gates, and milestones were **FROZEN** at F3.0 (see
  §4A and §9 → F-3) and **delivered** at F3.1/F3.2 (G-F3-1…G-F3-8 pass).
  **F-4 architecture FROZEN at F4.0 (2026-06-30)** — review + refinement (see
  §4B and §9 → F-4); awaiting operator approval before F4.1; **not implemented**.
- **Phase:** F — Operational Intelligence.
- **Mission alignment:** [`AURORA_VISION.md`](AURORA_VISION.md) — read first.
- **Authored:** F-0 pre-work, 2026-06-28.
- **Revised:** F3.0 Architecture Refinement, 2026-06-29 — F-1/F-2 drift
  reconciled (backup-probe decision, AF-05 voice mechanism, runtime details);
  F-3 split into F-3a/F-3b; F-3 gates and milestones frozen. **F3.3
  (2026-06-29):** F-3a/F-3b marked implemented + closed; G-F3-1 `# Context`
  precedence note recorded. **F4.0 (2026-06-30):** F-4 reviewed, refined
  (AD-14…AD-18, §4B) and frozen — architecture only, no implementation. See §15
  (Revision Log).
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
picked up by an `fs` corpus on the next nightly ingest cycle because the corpus
walks the host filesystem directly — it does not require files to be git-tracked.
Untracked, gitignored files in the corpus path are indexed identically to committed
files. **(F-4 routes digests to the dedicated `ops_digests` collection, not
`homelab_docs` — AD-14; the gitignored-runtime delivery mechanism here is unchanged.)**

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

### AD-14: Operational memory lives in a dedicated `ops_digests` collection — not `homelab_docs`, not `knowledge_history`.

**Refines AD-07 and supersedes the §9-F-4 "indexed by `homelab_docs`" routing.**
The digest *delivery mechanism* of AD-07 is retained in full (gitignored runtime
`.md` under `09_ops/runtime/`, picked up by an `fs` corpus on the next nightly
sync, no git operation). What changes is the **target collection**: digests are
indexed into a new dedicated `ops_digests` Qdrant collection (384-dim / Cosine),
created via the E-6 onboarding framework, with its own `corpora.yaml` entry
(`type: fs`, `path: 09_ops/runtime`).

Rationale: `AURORA_VISION.md §8` — "memory and knowledge are different problems …
require different architectures." `homelab_docs` is the *living-docs* corpus and
§6.5 deliberately excludes `09_logs/**` from it ("historical records →
knowledge_history") precisely so dated history does not outrank current docs;
routing dated digests into `homelab_docs` reintroduces the exact pollution F-1
fixed. `knowledge_history` is the *curated human* history corpus; ~365 low-entropy
machine digests/year would swamp it and is not its retrieval intent. A dedicated
collection isolates the memory layer, keeps both knowledge corpora clean, and makes
rollback fully self-contained. It is not "breadth" (no new knowledge *domain*) — it
is the correct *architecture* for the memory layer the Vision mandates as distinct.

Considered + rejected: **(A) `homelab_docs`** — pollutes living docs (above); the
inherited design chose it only because it was the one history-capable corpus already
wired to `rag_search`. **(B) `knowledge_history`** — semantically closer, but swamps
curated logs and its path (`09_logs`) does not cover `09_ops/runtime`, so it needs
the same `corpora.yaml` + enum work as a dedicated collection with none of the
isolation benefit.

### AD-15: The digest schema is limited to fields the F-2 signal layer actually produces.

The inherited §9-F-4 schema (per-corpus points before/after, backup
size/duration/prune count, ">5% collection delta" notable events) demands data **no
current signal produces**: `aurora-context.json` and `health.json` carry
status/timestamps/ids only, `backup_status.json.data_added_mb` is `null` by design
(AD-12), and nothing records per-corpus point counts over time. The frozen F-4
digest records only what exists (see §9-F-4 data model) plus one generated `notable`
deviation line. The "what grew in the platform" sub-feature (`AURORA_VISION.md §4`)
requires a small future signal — per-corpus counts emitted by `ingest-nightly` — and
is an **optional F-4 enrichment**, not a core dependency. **Supersedes the §9-F-4
digest schema.**

### AD-16: Operational-memory digests are durable, not regenerable — they are backed up.

§6.3 excludes `09_ops/runtime/` from the restic backup on the rationale that runtime
artifacts are "regenerated on the next nightly cycle." That holds for
`ai-stack/aurora/` (today's context) but is **false for digests**: a given night's
digest cannot be regenerated — its source signals are gone. Worse, the fs-corpus GC
(contract §4) drops points whose source file is missing, so a restore that loses
`09_ops/runtime/` would **wipe the `ops_digests` collection on the next sync**. F-4
therefore adds `09_ops/runtime/` to the restic backup set, keeping the raw source and
the embedded vectors consistent. **Supersedes §6.3 as applied to `09_ops/runtime/`.**

### AD-17: Retrieval is date-anchored.

`rag_search` performs dense (e5-small) retrieval + bge-reranker over a whole
collection and exposes **no payload date-filter** (verified in the deployed tool).
Because most nights are nominal, digests are near-identical and the **ISO date is the
primary discriminator** — so every digest embeds its date prominently in the filename,
the H1 title, and a header line, and the `notable` line (AD-15) gives abnormal nights
a distinct semantic signature. Same-night queries are served by `system_status`
(AD-04); digests answer queries ≥~1 day old. If exact-date retrieval degrades as
digests accumulate, the remedy is a payload date-filter or a dedicated digest tool —
**deferred** unless G-F4-05 fails at scale.

### AD-18: The digest is built only from typed signal fields, never from raw log text.

To keep an indexed, Aurora-retrievable corpus free of secrets (`AURORA_VISION.md §7`,
§13), `bin/generate-digest` reads only the curated, typed fields of
`aurora-context.json` / `health.json`. It never scrapes free-form log files, container
environment, or error output into the digest. No signal field carries a secret today
(status, timestamps, snapshot ids, counts); this AD makes that a binding construction
rule so a future signal change cannot silently leak a credential into RAG.

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

## 4B. F4.0 Architecture Refinement — Decision Register

F4.0 (2026-06-30) reviewed the inherited F-4 design (§9-F-4 + AD-04, AD-07) against
the running system and `AURORA_VISION.md`. Findings are evidence-grounded in the live
system (corpora.yaml, the deployed `rag_search` enum, `aurora-context.json` /
`health.json` schemas, the F-0 AF-08 result). Outcomes:

| # | Question / inherited assumption | Decision | Captured in |
|---|---|---|---|
| Q1 | Where do digests get indexed? (inherited: `homelab_docs`) | **Dedicated `ops_digests` collection** | AD-14 |
| Q2 | Digest schema with per-corpus deltas / backup size / >5% events | **Cut to available signal fields + a `notable` line**; growth-delta is an optional future enrichment | AD-15 |
| Q3 | Are digests backed up? (inherited §6.3: no) | **Yes — `09_ops/runtime/` joins the restic set** (digests are not regenerable) | AD-16 |
| Q4 | Is semantic RAG suited to date-keyed retrieval? | **Date-anchored digests**; payload date-filter deferred | AD-17 |
| Q5 | Secret-safety of an indexed memory corpus | **Typed signal fields only; no raw-log scraping** | AD-18 |
| Q6 | `04:20` cron slot collides with `push-voice-context` (F-3b) | **`generate-digest` moves to `04:25`** | §6.4 |
| Q7 | Is F-4 still the correct next step after F-3? | **Yes — unblocked (F-2 ✓, AF-08 ✓), correctly sequenced.** Its *daily* value is lower than F-5/F-6, so F-4 is kept deliberately lean (Q2). | §9-F-4 |
| Q8 | `knowledge_history` is absent from the deployed `rag_search` enum (pre-existing §6.5 drift — populated nightly but unqueryable) | **Recorded as finding R-F4-A.** Adding it to the enum is adjacent (the enum is edited in F4.1 anyway); operator's choice — not a core F-4 dependency. | §6.5 |

These refinements **supersede** the inherited F-4 routing (AD-07 "indexed by
`homelab_docs`" → AD-14), digest schema (§9-F-4 → AD-15), and backup posture (§6.3 →
AD-16). The F-4 architecture, acceptance gates (G-F4-01…G-F4-09), and milestones
(F4.1→F4.3) are **FROZEN** as of F4.0. No code, collection, corpus, prompt, container,
DB or git change was made in F4.0.

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

Two runtime directories are created by Phase F. Both are gitignored.
`ai-stack/aurora/` is **not** backed up by restic (today's context, regenerated on
the next nightly cycle; no state lost). **`09_ops/runtime/` IS backed up from F-4
onward** (AD-16) — digests are historical records that cannot be regenerated, and an
un-backed-up source would be GC-erased from `ops_digests` on restore.

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
| 04:20 | `bin/push-voice-context` (F-3b) | `input_text.aurora_voice_context` set via HA REST (AD-13) |
| 04:25 | `bin/generate-digest` (F-4) | `09_ops/runtime/YYYY-MM-DD_ops_digest.md` (AD-14…AD-18) |

`bin/push-voice-context` (F-3b, 04:20) is live. `bin/generate-digest` (F-4) is added at
**04:25** — F4.0 moved it off the 04:20 slot that `push-voice-context` already occupies
(§4B Q6). It reads the 04:15 `aurora-context.json`; ordering after the voice push is not
critical. It never runs git (AD-07).

### 6.5 Knowledge Layer Routing

The knowledge layer is split into semantically distinct corpora. Aurora
reasons in terms of knowledge domains; collection names are an
implementation detail confined to the tool layer.

**Corpus inventory**

| Corpus | Source path | Knowledge type | Access |
|---|---|---|---|
| `homelab_docs` | `/home/diego/homelab/**` (excl. `09_logs/`) | Living docs — current state of AMAROLAB | `rag_search` |
| `knowledge_history` | `/home/diego/homelab/09_logs/` (seed; expandable) | Historical records — what happened, why, which phase | `rag_search` (see R-F4-A) |
| `ops_digests` | `09_ops/runtime/` (F-4) | Operational memory — machine-generated nightly lab digests; what happened on a given night | `rag_search` (F-4) |
| `infra_audits` | `/home/diego/server-audit-2026-06-13/` | Phase 0/1 infrastructure audit reports; R-XX remediation records | `audit_search` (hardcoded) |
| `guardian_cloud` | `/mnt/storage/projects/guardian-cloud/` | Guardian Cloud project documentation | `rag_search` |
| `ensambla2` | `/mnt/storage/projects/ensambla2/` | Ensambla2 project documentation | `rag_search` |
| `myfreetour` | TBD | Placeholder | disabled |

**Collection-level routing policy**

| Query intent | Domain label | Collection | Tool |
|---|---|---|---|
| Current state, config, living docs | Current documentation | `homelab_docs` | `rag_search` |
| Past events, decisions, phase history | Historical records | `knowledge_history` | `rag_search` (see R-F4-A) |
| What happened on a specific night | Operational history | `ops_digests` | `rag_search` (F-4) |
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

**Known drift (R-F4-A):** `knowledge_history` is populated nightly (live point count
~3029) but is **absent from the deployed `rag_search` `collection` enum**
(`{homelab_docs, guardian_cloud, ensambla2, infra_audits, myfreetour}`, verified
2026-06-30). The routing row above ("historical records → `knowledge_history` via
`rag_search`") is therefore **currently unqueryable** — the corpus is write-only from
Aurora's perspective. This is a pre-existing F-1/§6.5 drift, not introduced by F-4. F-4
edits the same enum to add `ops_digests`; adding `knowledge_history` there is a
one-line adjacent fix that may be folded into F4.1 at the operator's discretion (§4B
Q8). It is not a core F-4 dependency.

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

### F-3 — Situational Awareness (FROZEN at F3.0; IMPLEMENTED + CLOSED 2026-06-29, F3.3)

**Objective:** Opening a conversation gives Aurora current lab state without
any tool call.

F-3 is split into **F-3a (chat Filter)** and **F-3b (HA voice)** (AD-08). The
Filter behaviour contract in §7 is the authoritative mechanism spec; the
decisions AD-08…AD-13 are binding. This sub-phase, its acceptance gates, and
its milestones are **frozen** as of F3.0 — changes require a recorded revision
(§15), not drift.

> **As built (F3.3, 2026-06-29) — IMPLEMENTED + CLOSED.** F-3a and F-3b are
> validated; **all gates G-F3-1…G-F3-8 pass**. F-3a is published as
> `phase-f3a-complete` (commit `96217e52`); F-3b + this reconciliation are staged
> for the F3.3 publication. Apply logs:
> [`../09_logs/2026-06-29_phaseF_F3_1_applied.md`](../09_logs/2026-06-29_phaseF_F3_1_applied.md) (F3.1),
> [`../09_logs/2026-06-29_phaseF_F3_2_applied.md`](../09_logs/2026-06-29_phaseF_F3_2_applied.md) (F3.2);
> closeout [`../09_logs/2026-06-29_phaseF_F3_closeout.md`](../09_logs/2026-06-29_phaseF_F3_closeout.md).
>
> **G-F3-1 note (required by F-3a reality):** the frozen plan assumed the injected
> block + the F-1 prompt would yield a no-tool-call status answer; in practice the
> 7B needed an explicit `# Context`-over-`# Routing` precedence directive in
> `params.system` (operator-approved, + an `openwebui` reload) before G-F3-1 passed
> with tools offered. **F-3b note:** only the AD-13 Jinja line was appended to the
> **stock** HA voice prompt — the F-1 voice identity was found absent and is tracked
> as a separate maintenance item (out of F-3b scope).

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
| **F3.0** | Architecture refinement & freeze (this revision) | docs — **DONE (frozen)** |
| **F3.1** | F-3a: entry-verify (installed F-1 prompt references the block; smoke-re-confirm AF-01 on the running 0.8.10 build; confirm `/opt/aurora/aurora-context.md` fresh in-container) → implement committed Filter → install → validate G-F3-1…G-F3-7 | build + validate — **DONE** (G-F3-1…7 pass; tag `phase-f3a-complete`) |
| **F3.2** | F-3b: `input_text` helper + Jinja2 prompt ref + 04:20 `set_value` push + HA token in `.env` → validate G-F3-8 | build + validate — **DONE** (G-F3-8 pass) |
| **F3.3** | Reconciliation & closeout: update the overview triad + this doc's F-3 status to complete; closeout log; STOP at git gate | docs + git — **current** (triad + doc reconciled; STOP at git gate) |

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

### F-4 — Operational Digest and Memory Corpus (FROZEN at F4.0, 2026-06-30 — NOT IMPLEMENTED)

**Objective:** Aurora answers "what happened on the night of <date>?" and "when
did <X> last deviate?" from structured operational history retrieved via RAG —
distinct from the live/same-night path (`system_status`, AD-03/AD-04) and from the
knowledge corpora (`homelab_docs` / `knowledge_history`).

This sub-phase, its data model, acceptance gates, and milestones are **frozen** as of
F4.0. Changes require a recorded revision (§15), not drift. F4.0 refined the inherited
design — see §4B and AD-14…AD-18. **No code, collection, corpus, prompt, container, DB
or git change has been made; F-4 is architecture-only until operator approval of F4.1.**

#### Operational-memory architecture (refined)

```
nightly signals ──▶ bin/generate-digest ──▶ 09_ops/runtime/YYYY-MM-DD_ops_digest.md
(aurora-context.json,                            │  (gitignored AD-07; restic-backed AD-16)
 health.json — typed                             │
 fields only, AD-18)                             ▼
                                    next 02:30 ingest sync (fs corpus, ~22h lag AD-04)
                                                 │
                                                 ▼
                                   Qdrant collection  ops_digests   (AD-14, 384/Cosine)
                                                 │
                                                 ▼
                              rag_search(collection="ops_digests", …)   (date-anchored AD-17)
```

#### What Aurora should remember (the memory layer's content)

Per-night operational outcome, retrievable for weeks: ingest result, backup result
(snapshot id/time/status), audit liveness, container health (count + any degraded),
home anomalies (once F-5 populates them), `overall_status`, missing signals, and the
deviation summary. Enough to answer "what happened on night X" and "when did Y last
deviate". This is `AURORA_VISION.md §5`'s *operational history* layer — "the system
documenting itself in a queryable form".

#### What Aurora must never remember (hard boundaries — Vision §5/§7)

- **Secrets** — no token/key/password ever enters a digest (AD-18; §13). The digest is
  built from typed signal fields, never raw logs/env.
- **Conversational content / verbatim transcripts** — explicitly out of F-4 and
  deferred to Phase G (AD-06). Indexing session content into any corpus is rejected.
- **Guardian Cloud internal state** — the digest is AMAROLAB-infra only (Vision §7).
- **Live/same-night state asserted as history** — same-night is `system_status`, not a
  digest (AD-04).

#### Data model — digest file

One **immutable** markdown file per operational night,
`09_ops/runtime/YYYY-MM-DD_ops_digest.md`. The date is the retrieval key and appears in
the filename, the H1 title, and a header line (AD-17). Schema (AD-15 — only fields the
F-2 signal layer produces):

| Field | Source | Notes |
|---|---|---|
| `date` (YYYY-MM-DD) | derived | operational night; retrieval key; filename + H1 + header |
| `generated_at` | aurora-context.json | ISO timestamp of context generation |
| `overall_status` | aurora-context.json | ok \| degraded \| unknown |
| `ingest` | health.json / aurora-context.json | status, last_run_rc, last_run_end, last_successful_run_end |
| `backup` | aurora-context.json | status, snapshot_id, snapshot_time (size/duration/prune = **n/a**, AD-12) |
| `audit` | aurora-context.json | status, age_days |
| `containers` | aurora-context.json | count, all_running, degraded[] (names) |
| `home.anomalies[]` | aurora-context.json | empty until F-5 populates it |
| `signals_missing[]` | aurora-context.json | honest record of absent signals |
| `notable` | generated | one line summarising deviations from nominal; "Nominal — no deviations." on a clean night. The abnormal-night semantic fingerprint (AD-17). |

The Qdrant payload is the platform-standard schema (contract §3) — no bespoke fields.

#### Scope (F-4 builds)

- **`ops_digests` collection** — create at 384-dim / Cosine via the E-6 onboarding
  framework; `corpora.yaml` entry (`name: ops_digests`, `type: fs`,
  `path: /home/diego/homelab/09_ops/runtime`, `include: ["**/*.md"]`, `enabled: true`).
- **`rag_search` enum** — extend the `collection` `Literal[…]` + docstring with
  `ops_digests` ("operational history — nightly lab digests; what happened on a given
  night"); reinstall via `bin/install_tool` (no container recreate — contract §6).
- **`bin/generate-digest`** — reads `aurora-context.json` + `health.json` (typed fields
  only, AD-18); writes the dated digest (AD-15 schema, date-anchored AD-17); idempotent
  overwrite. Committed as source (AD-09 discipline) with an install/recovery note.
- **Cron** — add `generate-digest` at **04:25** (after `push-voice-context` 04:20;
  §6.4). Never runs git (AD-07).
- **Durability** — add `09_ops/runtime/` to the restic backup set (AD-16).

#### Out of scope / cut (AD-15)

Per-corpus growth deltas, backup size/duration/prune count, and ">5% collection change"
notable events — no signal produces them. "What grew in the platform" is an **optional**
later enrichment (emit per-corpus counts from `ingest-nightly`), not frozen F-4.

#### Acceptance gates (FROZEN)

- **G-F4-01** — One nightly cycle produces a schema-correct digest (AD-15) in
  `09_ops/runtime/` from real signals; `notable` reflects that night.
- **G-F4-02** — Digest is gitignored; the nightly cron runs **no** `git` command;
  `git status` stays clean after a cycle (AD-07).
- **G-F4-03** — `ops_digests` exists (384/Cosine); `corpora.yaml` entry present;
  nightly sync indexes the digest; re-sync is idempotent (no duplicate points).
- **G-F4-04** — `rag_search(collection="ops_digests", …)` returns digest hits;
  empty-collection behaviour is clean before the first digest (D-22).
- **G-F4-05** — *Date-anchored retrieval (key gate).* With **≥7** digests present
  (real or backfilled dated fixtures), "what happened on the night of <date>?" retrieves
  the **correct** digest top-k. Failure at scale → AD-17 remedy.
- **G-F4-06** — *Same-night honesty.* "what happened last night?" asked the same morning
  is answered from `system_status`, and Aurora states the digest is not yet
  RAG-retrievable (AD-04).
- **G-F4-07** — *Degraded night.* A night with a real deviation (e.g. a stopped
  non-critical container or a forced ingest rc≠0) yields a digest whose `notable` line
  captures it and which is retrievable by that description.
- **G-F4-08** — *Durability.* `09_ops/runtime/` is in the restic set; a restore-drill
  spot-check confirms a missing-source GC does **not** wipe `ops_digests` (AD-16).
- **G-F4-09** — *No secrets.* The generated digest contains no secret values (scan
  against the token/var names in §13); only typed signal fields appear (AD-18).
- **Repro gate** — `bin/generate-digest` source, the `corpora.yaml` entry, and the
  `rag_search` enum change are committed with an install/recovery note (AD-09).

#### Frozen implementation milestones

| Milestone | Content | Type / gates |
|---|---|---|
| **F4.0** | Architecture review, refinement & freeze (this revision; §4B, AD-14…AD-18) | docs — **DONE (frozen); awaiting operator approval** |
| **F4.1** | Retrieval substrate: create `ops_digests` (E-6 framework) + `corpora.yaml` entry + extend `rag_search` enum + reinstall + validate empty-collection/enum | build + validate — **G-F4-03 (partial), G-F4-04** |
| **F4.2** | Generator: `bin/generate-digest` (AD-15/17/18) + 04:25 cron + restic durability (AD-16) + validate one nightly cycle | build + validate — **G-F4-01, G-F4-02, G-F4-08, G-F4-09** |
| **F4.3** | Retrieval validation + closeout: backfill ≥7 dated fixtures, validate date-anchored / degraded-night / same-night gates; reconcile triad + this doc; closeout log; **STOP at git gate** | build + docs — **G-F4-05, G-F4-06, G-F4-07, repro gate** |

#### Rollback

Fully self-contained (the dedicated collection's main operational virtue): remove the
`generate-digest` cron line; set `ops_digests` `enabled: false` (nightly sync skips it
cleanly per the F-01 exit-code contract); optionally drop the Qdrant collection and
revert the `rag_search` enum + reinstall; delete `09_ops/runtime/*.md` (gitignored).
**No production corpus is touched** — `homelab_docs` and `knowledge_history` are never
written to by F-4. Each step is independently reversible. (Contrast: the inherited
`homelab_docs` routing interleaves digest points into the production living-docs
collection and cannot be cleanly disabled.)

**Dependencies:** F-2 (`aurora-context.json` + `health.json`) — **complete**; AF-08
(runtime-path fs-corpus indexing) — **CONFIRMED 2026-06-28**; the ~22h indexing lag is
known and accepted (AD-04). Independent of F-3 / F-5 / F-6.

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
| Digest files (`09_ops/runtime/`) | Runtime artifacts. Must not be committed automatically. The nightly cron cycle never runs `git commit`, `git push`, or `git tag`. Digest files are gitignored and indexed by the dedicated `ops_digests` fs corpus without git involvement (AD-07 + AD-14). |
| Digest source durability (F-4) | `09_ops/runtime/` IS in the restic backup set (AD-16). Digests are not regenerable; an un-backed-up source is GC-erased from `ops_digests` on restore. |
| Digest construction (F-4) | `bin/generate-digest` reads only typed signal fields (`aurora-context.json` / `health.json`); it never scrapes raw logs, container env, or error text into the indexed digest (AD-18). |
| Operational memory corpus (F-4) | Digests are indexed into the dedicated `ops_digests` collection only. `homelab_docs` and `knowledge_history` are never written to by F-4 (AD-14). |
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
| 2026-06-29 | **F3.3 — F-3 closeout / reconciliation** | Recorded F-3 as IMPLEMENTED + CLOSED: F-3a Open WebUI Filter (`aurora_context`, active+global) + F-3b HA voice awareness (`input_text.aurora_voice_context` + Jinja2 + 04:20 `push-voice-context`); all gates G-F3-1…G-F3-8 pass. Added the §9 "as built" note + milestone statuses (F3.0→F3.3 done) + status header, and recorded the **G-F3-1 `# Context` precedence** requirement (for G-F3-1 with tools offered) and the **F-1 HA-voice-identity-absent** finding (separate item). Overview triad reconciled in parallel. No code/prompt/DB/container changes in F3.3. Apply logs: F3_1, F3_2; closeout `2026-06-29_phaseF_F3_closeout.md`. STOP at git gate (operator review before publication). |
| 2026-06-30 | **F4.0 — F-4 Architecture Review & Freeze** | Reviewed the inherited F-4 design against the running system + `AURORA_VISION.md`. Recorded the decision register (§4B) and AD-14…AD-18. **Re-routed operational memory** from `homelab_docs` to a dedicated `ops_digests` collection (AD-14 — resolves the §6.5/§9-F-4 self-contradiction and the Vision §8 "memory ≠ knowledge" principle). **Cut the digest schema** to fields the F-2 signal layer actually produces + a `notable` line (AD-15; the inherited per-corpus-delta / backup-size / >5%-event schema is unbuildable from current signals). Made digests **durable** (restic-backed `09_ops/runtime/`, AD-16 — they are not regenerable and would otherwise be GC-erased on restore). Made retrieval **date-anchored** (AD-17) and the digest **secret-safe by construction** (AD-18). Moved `generate-digest` to the **04:25** cron slot (§6.4). Recorded the pre-existing `knowledge_history`-not-in-`rag_search`-enum drift as finding R-F4-A (§6.5). **Froze** the F-4 architecture, acceptance gates (G-F4-01…G-F4-09), and milestones (F4.1→F4.3). No code/collection/corpus/prompt/container/DB/git change. Next: operator approval before F4.1. |
