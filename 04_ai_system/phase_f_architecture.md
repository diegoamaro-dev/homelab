# Phase F — Architecture Document

- **Status:** Approved. Governs all Phase F implementation decisions.
- **Phase:** F — Operational Intelligence.
- **Mission alignment:** [`AURORA_VISION.md`](AURORA_VISION.md) — read first.
- **Authored:** F-0 pre-work, 2026-06-28.
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

### Running components

| Component | Status | Notes |
|---|---|---|
| `rag_search` (5 collections) | Production | homelab_docs 4049 pts, guardian_cloud 872, ensambla2 419, infra_audits 280, myfreetour 0 (disabled) |
| `ha_get_state` | Production | Reads any HA entity; curated attribute allowlist |
| `ha_call_service` | Production | 12 allowed domains; gate-validated |
| `audit_search` | Production | Open WebUI tool-call audit log |
| `time_now` | Production | Trivial |
| Ollama proxy | Production | Torre RTX 5070 ~101 tok/s primary; UM790 CPU fallback ~6 tok/s |
| `health.json` | Production | Ingest + audit health signal at `ai-stack/ingest/logs/health.json` |
| Whisper / Piper / WakeWord | Production | HA voice pipeline operational; Spanish quality gap (base-int8) |
| Open WebUI system prompt | Production | 822 tokens; stale; does not reflect current tool surface accurately |

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

The Filter contains no domain logic. It reads one file. Its only job is
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

`bin/aurora-context` produces `aurora-context.md` and also writes a compact
variant to a path readable by the HA voice system prompt refresh process.
The voice surface does not get a separate awareness mechanism — it gets the
same context document at the same cadence. Voice and chat context divergence
is resolved architecturally, not accepted as a known limitation.

### AD-06: Conversational context (session continuity) is explicitly deferred to Phase G.

`AURORA_VISION.md §5` distinguishes operational history from conversational
context. Phase F delivers operational history (the digest corpus). Session-
to-session conversational continuity requires a separate mechanism (Open
WebUI memory, or a custom approach) that is not designed in Phase F.
Implementing conversational memory in Phase F by indexing session content
into `homelab_docs` is explicitly rejected — it would pollute a knowledge
corpus with noise and solve the wrong problem.

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
requires a Filter update. The Filter should be dumb — it reads one file and
prepends it. Context construction belongs in `bin/aurora-context`, where it
can serve all consumers. Schema changes are handled in one place.

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
| `ai-stack/ingest/logs/backup_status.json` | `homelab-backup.sh` (modified) | 03:00 | `schema_version`, `run_at`, `exit_code`, `status`, `snapshot_id`, `files_new`, `files_changed`, `data_added_mb`, `duration_seconds`, `prune_removed` |
| `ai-stack/ingest/logs/container_status.json` | new host-side probe script | nightly (04:00) or scheduled (≤30 min) | `generated_at`, `containers: [{name, status, running}]` |

`backup_status.json` and `container_status.json` are new signals that must
be created as part of Phase F (F-2). Until they exist, the context
generation script operates with reduced data and must communicate the gap
honestly.

### 6.2 Context Generation

`bin/aurora-context` is the only component that reads signal files and knows
their schema. It reads all available signal files, constructs a structured
context, and writes two output artifacts.

```
ai-stack/ingest/logs/
├── health.json           ─┐
├── backup_status.json    ─┤──▶  bin/aurora-context  ──▶  ai-stack/aurora/
└── container_status.json ─┘                               ├── aurora-context.json
                                                           └── aurora-context.md
```

**`aurora-context.json`** — structured, machine-readable. Fields:

```json
{
  "schema_version": 1,
  "generated_at": "2026-06-28T04:15:00Z",
  "overall_status": "ok | degraded | unknown",
  "ingest": { "status": "ok", "last_run_end": "...", "last_run_rc": 0 },
  "backup": { "status": "ok", "snapshot_id": "...", "run_at": "...", "exit_code": 0 },
  "audit": { "status": "ok", "age_days": 0 },
  "containers": { "all_running": true, "degraded": [] },
  "home": { "anomalies": [] },
  "signals_missing": []
}
```

**`aurora-context.md`** — LLM-formatted, human-readable. This is what the
Filter prepends and what the voice system prompt reads. Format: compact,
timestamped, honest about missing signals and their age. Example:

```
[Aurora context — 2026-06-28 04:15 UTC]
Platform: OK — ingest ok (02:30), backup ok (03:00, snapshot 228e4183,
+2.1 MB), audit ok, all 17 containers running. Torre: not probed (live
probe available via system_status). Home: no anomalies.
```

If a signal file is missing, `aurora-context` notes it: "backup: signal
missing — check ai-stack/ingest/logs/backup_status.json". Graceful
degradation means saying less, not guessing.

### 6.3 Runtime Directory

`ai-stack/aurora/` is Aurora's runtime artifacts home. It is distinct from
`ai-stack/ingest/` (the knowledge platform service). Files in this directory
are generated artifacts — never committed to git.

Add to `.gitignore`:
```
ai-stack/aurora/aurora-context.json
ai-stack/aurora/aurora-context.md
```

Bind-mount into the `openwebui` container (new, read-only):
```
ai-stack/aurora:/opt/aurora:ro
```

This makes context files available at `/opt/aurora/aurora-context.md` and
`/opt/aurora/aurora-context.json` inside the container, accessible to both
the Filter and the `system_status` tool.

---

## 7. Consumer Model

All consumers are dumb. They read; they do not reconstruct.

| Consumer | What it reads | When | How |
|---|---|---|---|
| Open WebUI Filter | `/opt/aurora/aurora-context.md` | Message 1 of each conversation | Prepends content as a system message block; fires on inlet; silent-fails if file missing |
| HA voice system prompt | `aurora-context.md` (compact variant) | Nightly refresh (04:20, after context generation) | Script writes compact context into HA voice LLM config via HA REST API or direct config write |
| `system_status` tool | `/opt/aurora/aurora-context.json` + live probes | On demand | Reads context JSON for pre-generated state; adds live Torre probe + fresh health.json read |
| Future consumers | `/opt/aurora/aurora-context.md` (or JSON) | At session start | Same pattern — read the file |

**Filter behaviour contract:**
- Fires on inlet (user message), not outlet.
- Checks if this is message 1 (conversation history length == 0 or 1).
- Reads `/opt/aurora/aurora-context.md`.
- If file exists and is ≤24h old: prepends content.
- If file is missing, unreadable, or stale (>36h): prepends a minimal fallback ("Context file unavailable — use system_status for current state.") and continues. Never crashes the conversation.
- Does not fire on messages 2, 3, etc.

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
 │      │      │
 │      │      └──▶ F-4 (Operational Digest + Memory Corpus)
 │      │
 │      └──▶ F-5 (Home Intelligence)
 │              └── depends on F-3 for home anomaly context block
 │
 └──▶ F-6 (Voice Quality)  ◀── parallel track; no dependency on F-2..F-5
```

**Critical path:** F-0 → F-1 → F-2 → F-3 → F-4 → F-5

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

### F-3 — Situational Awareness Filter

**Objective:** Opening a conversation gives Aurora current lab state without
any tool call.

**Scope:**
- Write the Open WebUI Filter: Python Function (Filter type); inlet fires on
  first message of each conversation; reads `/opt/aurora/aurora-context.md`;
  prepends content as a system message; fails silently (fallback message) if
  file missing or stale (>36h). Silent-fail is validated behavior, not a
  degraded state.
- Write the HA voice context refresh script (the F-1 voice prompt update
  becomes nightly): after `bin/aurora-context` runs at 04:15, a follow-on
  step (04:20) writes a compact context line into the HA voice LLM
  configuration. Mechanism: HA REST API service call or direct config file
  write, whichever is simpler and stable.
- Validate Filter behavior: message 1 receives context; messages 2+ do not;
  conversation performance is not degraded; missing context file produces
  fallback, not an error.

**Success criterion:** Opening a conversation with "how is the lab?" produces
an accurate answer from the injected context, without any tool call in the
Open WebUI tool-call log. Aurora's response references the `generated_at`
timestamp. HA voice correctly reflects the latest context on the first voice
exchange of the day.

**Dependencies:** F-2 (context files must exist for the Filter to read);
F-1 (system prompt must correctly reference and interpret the context block).

---

### F-4 — Operational Digest and Memory Corpus

**Objective:** Aurora answers "what happened three nights ago?" from
structured operational history retrieved via RAG.

**Scope:**
- Write `bin/generate-digest`: runs at 04:20 (after `bin/aurora-context`);
  reads `aurora-context.json` (current nightly cycle data); writes
  `09_ops/YYYY-MM-DD_ops_digest.md` to the homelab repo. The digest is
  committed to the repo on the same nightly cycle (or written to a path
  already watched by `homelab_docs`) so the following night's ingest sync
  picks it up automatically.
- Digest schema (stable — do not change without updating all existing
  digests or accepting a retrieval inconsistency): date header, ingest
  summary (per-corpus: points before/after, files changed, errors),
  backup summary (snapshot ID, size, exit code, duration, prune count),
  health summary (`overall_status` at generation time), notable events
  (collection grew or shrank by >5%), generated_at timestamp.
- Add `09_ops/*.md` to the `homelab_docs` corpus `include:` pattern if not
  already covered by the existing `**/*.md` glob.
- Validate: after two nightly cycles, "what happened on the night of
  [date]?" answered from RAG with the correct digest content.

**Success criterion:** After two nightly cycles: two dated digest files exist
in `09_ops/`; both are indexed in `homelab_docs`; `rag_search` against
"homelab_docs" retrieves the correct digest for a specific date query;
digest content is accurate (matches signals from that night's cycle); Aurora
correctly communicates that same-night digests are not yet retrievable via
RAG and offers system_status instead.

**Dependencies:** F-2 (`bin/generate-digest` reads `aurora-context.json`,
which F-2 creates); the 22-hour indexing lag is known and accepted (AD-04).

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
  generation cycle, call `ha_get_state` for key entities; compare to
  expected baseline; include any anomalies in `aurora-context.json`
  (`home.anomalies` array) and in `aurora-context.md`. The Filter then
  surfaces home anomalies automatically at conversation start.
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
approved device surface.

**Dependencies:** F-3 (anomaly detection requires the Filter's context
block; home anomalies are injected the same way as platform health);
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
│  ├─ inventories HA entities (AF-06)
│  └─ measures voice quality gap

├──▶ F-1 System Prompt
│       Prerequisite for: F-2 (tool referenced), F-3 (prompt must interpret
│       context block), F-5 (home model described), F-6 (voice prompt)
│
├──▶ F-6 Voice Quality (parallel — starts after F-0)
│
└──▶ F-2 Signal Layer + Context Generation
        │  Prerequisite for: F-3 (Filter reads context files),
        │                    F-4 (digest reads context JSON)
        │
        ├──▶ F-3 Awareness Filter
        │       Prerequisite for: F-5 (home anomaly injection uses
        │                         the same Filter mechanism)
        │
        ├──▶ F-4 Operational Digest
        │
        └──▶ F-5 Home Intelligence
```

---

## 11. Architectural Risks — Finding Register

Pre-identified findings for F-0 to validate. Each finding is either
confirmed, disproved, or superseded by F-0's behavioral audit. No finding
is assumed closed until F-0 explicitly closes it.

| ID | Description | Severity | Pre-mitigation |
|---|---|---|---|
| AF-01 | Open WebUI Filter mechanism not validated. The inlet/outlet behavior, message-1 detection, and file-not-found handling must be confirmed in the running version before committing to the architecture. | High | Validate in F-0 with a minimal test Filter before building the production Filter. |
| AF-02 | `backup_status.json` does not exist. No structured backup signal is available until `homelab-backup.sh` is modified. Both `bin/aurora-context` and `bin/generate-digest` depend on it. | High | First deliverable of F-2. Confirm gap in F-0. `aurora-context` must degrade gracefully until F-2 is complete. |
| AF-03 | `container_status.json` does not exist. Docker container health is unavailable to the context layer without a new probe script. | Medium | Part of F-2. Until it exists, context document omits container health; `aurora-context` logs the missing signal. |
| AF-04 | Digest indexing lag. Same-night digest is not retrievable via RAG for ~22 hours. Aurora must not claim RAG-retrieved operational history for the current night's cycle. | Medium | Accepted per AD-04. System prompt and Filter content must communicate this clearly. |
| AF-05 | HA voice system prompt update mechanism. The method for updating the HA voice LLM system prompt from a nightly script (REST API vs. config file write) has not been validated. If the mechanism is not stable or requires HA restart, the nightly refresh cannot be automated reliably. | Medium | Validate in F-0 or early F-1. If automated refresh is not feasible, the voice system prompt is updated manually each phase; document as a known manual step. |
| AF-06 | Home model is undefined. F-5 cannot begin until the HA entity inventory is complete and the home model document is written. F-0's HA entity audit is a prerequisite. | Low | F-0 produces the entity inventory. F-5 formalises it. Not blocking until F-5. |
| AF-07 | Torre reachability probe from inside openwebui container. The live Torre HTTP probe in `system_status` requires network connectivity from inside the openwebui container to Torre's Tailscale address. This is not validated. | Low | Validate in F-0. If container-to-Tailscale routing does not work, the probe must run on the host and write a `torre_status.json` signal file instead. |

---

## 12. Success Criteria — Phase F Complete

Phase F is complete when all of the following are true. These are
observable behaviours, not technical metrics (per `AURORA_VISION.md §3`).

**Briefing works.** Diego opens a conversation after any absence. Without
running any command or explicitly calling a tool, Aurora gives an accurate
and honest status: ingest result, backup result, service health, home
anomalies (if any). The answer references when the context was generated.
If Torre is offline, Aurora says so or acknowledges uncertainty.

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
| `aurora-context.json` / `aurora-context.md` | Generated runtime artifacts. Must not be committed. Add to `.gitignore` before the first `bin/aurora-context` run. |
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
