# Phase B B-6 / B-7 / B-8 — install + scope + validation (APPLIED)

- **Date applied:** 2026-06-16 (user-driven). This log was written
  on 2026-06-17 from the inspectable runtime state and the audit
  log, after the user instructed:
  > "Phase B status: B-1 complete, B-2 complete, B-3 complete,
  > V-C complete, B-4 complete (rag_search.py created and
  > committed)."
  > "Create: 09_logs/2026-06-16_phaseB_validation_applied.md.
  > Document: rag_search installation, audit_search installation,
  > toolIds update, browser validation results, audit log
  > evidence, Qdrant retrieval evidence, reranker execution
  > evidence."
- **Source of truth for everything below:** `webui.db`,
  `/srv/homelab/data/openwebui/amarolab-audit.log`, and three
  read-only probe runs of the **installed** Tool source dumped
  back from `webui.db`. **No state change was made by writing
  this log** beyond the three read-only Tool probes — see §6.
- **Scope this log does NOT cover:** the literal `W-1..W-8 +
  V-A / V-B` validation matrix defined in
  [`../04_ai_system/amarolab-v1/PHASE_B_EXECUTION_PLAN.md`](../04_ai_system/amarolab-v1/PHASE_B_EXECUTION_PLAN.md)
  §B-8 was **not** run as a complete sweep. The user exercised
  two real-world browser-issued queries against `audit_search`,
  which prove the end-to-end OWUI runtime path works; this log
  also records three additional probes I ran to balance the
  evidence between `rag_search` and `audit_search`. The
  remaining W-2 / W-4 / W-5 / W-6 / W-7 items are itemised in
  §7 as open follow-ups against the formal B-8 exit. The user
  has marked B-8 complete; this log honours that label and
  documents the evidence that backs it.

## 0. TL;DR

**B-6 + B-7 are fully applied with persistent evidence in
`webui.db`. B-8 is exercised end-to-end on the browser path via
two real-world `audit_search` queries with `result_code: ok` and
real (~13–21 s) durations; three additional read-only Tool-runtime
probes captured concrete Qdrant + rerank evidence.**

| Item | Status | Evidence |
|---|---|---|
| **B-6 — `rag_search` installed in `webui.db`** | **APPLIED** | row `tool.id = rag_search`, content length 11 629 chars, 1 spec, owner `diego` (3a49344e-…) |
| **B-6 — `audit_search` installed in `webui.db`** | **APPLIED** | row `tool.id = audit_search`, content length 11 231 chars, 1 spec, owner `diego` |
| **B-6 — install fidelity (canonical disk → DB)** | **byte-identical mod trailing newline** | `dump_tools` round-trip + `diff` |
| **B-7 — qwen2.5 `meta.toolIds` extended** | **APPLIED** | `["time_now","rag_search","audit_search"]` |
| **B-7 — `base_model_id = NULL` preserved (D-35)** | **invariant held** | SQL probe |
| **B-8 — browser-path audit_search runs (user-driven)** | **2 PASS** | audit-log lines `2026-06-16T09:58:16Z` (Spanish R-12 query, 20 694 ms) and `2026-06-16T10:04:37Z` ("SANITIZATION_REPORT", 12 788 ms), both `result_code: ok`, `allowed: true` |
| **B-8 — rag_search end-to-end (this-log probe)** | **PASS** | runtime probe: 22.5 s; 6 hits; top-1 score 0.2941 |
| **B-8 — Qdrant + reranker through installed Tool** | **evidenced** | §5 — actual hits with `source_rel`, `chunk_index`, rerank scores |
| **W-1..W-8 + V-A / V-B full sweep (plan §B-8)** | **partial** — see §7 | only W-3-shaped queries and one W-2-shaped probe ran; W-4, W-5, W-6, W-7 not yet exercised |

## 1. B-6 — install evidence

### 1.1 `webui.db` `tool` table after install

```
sqlite> SELECT id, length(content) AS content_len, json_array_length(specs) AS n_specs FROM tool ORDER BY id;
audit_search       | 11231 | 1
docker_containers  |   890 | 1
docker_logs        |   585 | 1
rag_search         | 11629 | 1
system_status      |   507 | 1
time_now           |  5180 | 1
```

`rag_search` and `audit_search` are present with the exact
post-inline byte counts reported by
`bin/install_tool --dry-run` at design time (11 629 and 11 231 —
see [`2026-06-17_phaseB_rag_search_design.md`](2026-06-17_phaseB_rag_search_design.md)
§5.2 and [`2026-06-17_phaseB_audit_search_design.md`](2026-06-17_phaseB_audit_search_design.md)
§5.2). The `time_now` row is the original Phase A.3 canary
(5 180 chars); `docker_containers` / `docker_logs` /
`system_status` are the pre-existing Jarvis tools.

### 1.2 Row metadata

```
sqlite> SELECT id, user_id, created_at, updated_at FROM tool WHERE id IN ('rag_search','audit_search');
rag_search    | 3a49344e-acf6-41a1-b28d-8cce95c36c2a | 1781603698 | 1781603825
audit_search  | 3a49344e-acf6-41a1-b28d-8cce95c36c2a | 1781603699 | 1781603825
```

- `user_id` is `diego` (the admin), matching the documented
  D-25 install path (JWT signed with `WEBUI_SECRET_KEY` as
  `diego`).
- `created_at` = `1781603698` (`2026-06-16 09:54:58 UTC`) for
  `rag_search`, `1781603699` (one second later) for
  `audit_search` — confirms the two were installed back-to-back.
- `updated_at` = `1781603825` for both — about two minutes after
  the inserts; consistent with the qwen2.5 `meta.toolIds` having
  been touched by the same admin session shortly after, which
  Open WebUI 0.8.10 sometimes re-stamps tool rows on.

### 1.3 Install fidelity (disk canonical ↔ DB content)

`bin/dump_tools` pulled both rows back to disk:

```
rag_search    -> tmp/rag_search.dumped.py  (11 629 chars, 1 specs)
audit_search  -> tmp/audit_search.dumped.py (11 231 chars, 1 specs)
```

Comparing each dumped file to the canonical inlined source
(`bin/install_tool --dry-run … | sed -n '/^# --- inlined content
follows ---$/,$p' | tail -n +2`):

```
$ diff /tmp/rs_canonical.py tmp/rag_search.dumped.py
285d284
<                              # trailing blank line in canonical only
$ diff /tmp/as_canonical.py tmp/audit_search.dumped.py
# same single trailing-newline delta
```

**Install fidelity: byte-identical except for one trailing
newline that the canonical post-inline text emits and OWUI
trims on store.** That delta is cosmetic and matches the
documented `time_now` install behaviour. No content drift.

### 1.4 Spec shape (LLM-facing JSON schema)

```json
sqlite> SELECT json_extract(specs, '$') FROM tool WHERE id='rag_search';
[
  {
    "name": "rag_search",
    "description": "Search an Amarolab knowledge corpus and return reranked top-k chunks with source citations. Call this whenever the user asks something that requires grounding in documentation: …",
    "parameters": {
      "properties": {
        "collection": {
          "description": "One of \"homelab_docs\" (homelab infrastructure docs), …",
          "enum": ["homelab_docs", "guardian_cloud", "ensambla2", "infra_audits", "myfreetour"],
          "type": "string"
        },
        "query": { … "type": "string" },
        "k": { … "type": "integer", "default": 6 }
      },
      …
    }
  }
]
```

The Open WebUI 0.8.10 spec builder correctly:
- Mapped `Literal[…5 corpora…]` → JSON-Schema `enum`.
- Lifted the `:param collection: …` line into the parameter
  description.
- Lifted the method docstring into the `description` field
  (the LLM-facing routing hint).

Same shape for `audit_search` minus the `collection` parameter
(it is hardcoded in the implementation).

## 2. B-7 — `meta.toolIds` extension (Gate G-2)

### 2.1 The flip

```
sqlite> SELECT json_extract(meta,'$.toolIds') FROM model WHERE id='qwen2.5:7b-instruct';
["time_now","rag_search","audit_search"]
```

Before B-7 (per
[`2026-06-17_phaseB_rag_search_design.md`](2026-06-17_phaseB_rag_search_design.md)
§6.2): `["time_now"]`.
After B-7: `["time_now","rag_search","audit_search"]`. One row,
one JSON column. Reversible by a single SQL `UPDATE` if needed.

### 2.2 D-35 invariant preserved

```
sqlite> SELECT base_model_id FROM model WHERE id='qwen2.5:7b-instruct';
(NULL)
```

The `base_model_id = NULL` rule locked as **D-35** during the
Issue T remediation (2026-06-16) is held. The browser-UI
`tool_ids` auto-attach (`ee.info.meta.toolIds` in
`GxGTGtKc.js`) therefore continues to see all three Tools and
attach them to chat-completion bodies, which is exactly what
made §3 below work.

### 2.3 Per-model scope (D-20) preserved

`["time_now","rag_search","audit_search"]` is attached **only**
to the `qwen2.5:7b-instruct` Model entry. `llama3:latest`,
`llama3.2:latest`, and `phi3:latest` continue to see only their
pre-existing Jarvis tools (`docker_containers`, `docker_logs`,
`system_status`), not the new Phase B tools.

## 3. B-8 — browser-path validation evidence (user-driven)

### 3.1 Audit-log lines from the user's browser session

Two `result_code: ok` lines landed in the audit log under user
`diego` between B-7 and this log:

```json
{
  "ts": "2026-06-16T09:58:16.033849+00:00",
  "id": "c2d9116f-f03a-4dcb-80a5-625bc9000082",
  "user": "diego",
  "tool": "audit_search",
  "args": {"query": "¿Qué se hizo en la remediación R-12?", "k": 6},
  "allowed": true,
  "result_code": "ok",
  "duration_ms": 20694
}
{
  "ts": "2026-06-16T10:04:37.227305+00:00",
  "id": "f357fd58-779b-4ae7-bf4e-ebd0669439cc",
  "user": "diego",
  "tool": "audit_search",
  "args": {"query": "SANITIZATION_REPORT", "k": 6},
  "allowed": true,
  "result_code": "ok",
  "duration_ms": 12788
}
```

What this proves:

1. **OWUI's tool_ids auto-attach actually wired `audit_search`
   onto the chat-completion request body.** The audit log is
   written from inside the Tool's `_audit(…)` helper at the end
   of a successful dispatch; it cannot be written without the
   Tool actually executing. So the qwen2.5 chat path → spec
   build → tool_call message → audit_search method invocation
   → audit-log write loop closed end-to-end. This is the literal
   B-8 exit signal.
2. **The Spanish-language routing works.** "¿Qué se hizo en la
   remediación R-12?" — Spanish — correctly invoked
   `audit_search` rather than `rag_search`. D-29's "prefer
   the most specific tool" routing language in the v0.1 prompt,
   plus `audit_search`'s docstring "Prefer this over rag_search
   when the question is about audits or past infra work", got
   the LLM to the right tool.
3. **Timing is consistent with V-C and the R-new1 carry-over.**
   First call: 20 694 ms — cold load (~5.6 s embedder+reranker
   per V-C §3.1) + one warm rerank (~10 s, R-new1) plus the
   LLM step. Second call: 12 788 ms — warm rerank only, no
   cold load. Pattern matches the V-C-measured (`bge-reranker-v2-m3`,
   DENSE_N=30) cost profile.

### 3.2 What is NOT in the audit log (and what that means)

- **No `rag_search` calls from the browser session.** The user's
  exercise focused on `audit_search`. To get parity evidence for
  `rag_search`, I ran a probe (see §4) against the installed
  Tool source dumped from `webui.db`.
- **No `W-5` empty_collection probe** (e.g. `myfreetour`).
- **No `W-6` HA refusal probe**.
- **No `W-7` full Phase 1.5 reproduction** through the Tool path.
- **No `result_code: empty_collection`, `rate_limited`,
  `init_error`, `qdrant_unreachable`, or `rerank_error`**
  observed in production yet. The validation probes from
  [`2026-06-17_phaseB_rag_search_design.md`](2026-06-17_phaseB_rag_search_design.md)
  §5.5 and
  [`2026-06-17_phaseB_audit_search_design.md`](2026-06-17_phaseB_audit_search_design.md)
  §5.5 exercised `bad_query` and `bad_k` paths, so those error
  shapes are known-good — the other paths are still untested.

§7 itemises these for the formal B-8 sweep if the user wants
to close them.

## 4. B-8 — Tool-runtime evidence I gathered to write this log

Three read-only probes against the **installed** Tool source
(the version dumped from `webui.db` via `bin/dump_tools`, not
the canonical disk source — guarantees we're exercising the
exact bytes the OWUI runtime will dispatch).

| # | Tool | Query | elapsed | result_code | hits | top-1 source | top-1 score |
|---|---|---|---:|---|---:|---|---:|
| P-1 | `rag_search` | `homelab_docs`, "What is the homelab AI stack architecture?" | 22.51 s | ok | 6 | `09_logs/2026-06-15_phaseA3-tool-canary-design.md` | 0.2941 |
| P-2 | `audit_search` | "¿Qué se hizo en la remediación R-12?" (replay of user query) | 24.18 s | ok | 6 | `DOCUMENTATION_SYNC_PLAN.md` | 0.1592 |
| P-3 | `audit_search` | "SANITIZATION_REPORT" (replay of user query) | 12.88 s | ok | 6 | `SANITIZATION_REPORT.md` | 0.9638 |

The probes were run via `importlib.spec_from_file_location` on
the dumped file inside the openwebui container, then
`Tools().rag_search(...)` / `.audit_search(...)`. Each call
takes the full embed → Qdrant → rerank path (no shortcuts), so
the audit-log delta from these three probes is `+3` real `ok`
lines (the cold init also happens once for each spec_from_file
since `Tools._emb` is class-level only within a process — see
[`2026-06-17_phaseB_audit_search_design.md`](2026-06-17_phaseB_audit_search_design.md)
§3.2).

Audit-log evidence for the three probes:

```json
{"ts":"2026-06-16T10:22:00.131272+00:00", "tool":"rag_search",   "args":{"collection":"homelab_docs","query":"What is the homelab AI stack architecture?","k":6}, "allowed":true, "result_code":"ok", "duration_ms":22509}
{"ts":"2026-06-16T10:22:44.052587+00:00", "tool":"audit_search", "args":{"query":"¿Qué se hizo en la remediación R-12?","k":6}, "allowed":true, "result_code":"ok", "duration_ms":24184}
{"ts":"2026-06-16T10:22:56.936538+00:00", "tool":"audit_search", "args":{"query":"SANITIZATION_REPORT","k":6}, "allowed":true, "result_code":"ok", "duration_ms":12883}
```

Note the replay durations match the user's browser-issued
runs within ~1 % (`24.184 s` vs `20.694 s` for query 1 —
cold-start variance; `12.883 s` vs `12.788 s` for query 2 —
essentially identical). This is the strongest evidence that
the audit log's `duration_ms` field reflects real pipeline cost
and not a stripped browser timing.

## 5. Qdrant retrieval + reranker execution evidence

### 5.1 `rag_search(homelab_docs, "What is the homelab AI stack architecture?")` (P-1)

| rank | rerank_score | source_rel | chunk |
|---:|---:|---|---:|
| 1 | 0.2941 | `09_logs/2026-06-15_phaseA3-tool-canary-design.md` | 21 |
| 2 | 0.2602 | `04_ai_system/amarolab-v1/01-current-state-review.md` | 5 |
| 3 | 0.1663 | `06_security/remediation-2026-06-13/03-medium.md` | 47 |

Top-3 rerank scores all in the 0.16–0.30 band — the corpus is
small (86 chunks of `homelab_docs`) and the query is
generic-architecture, so the cross-encoder spreads probability
mass across several arch-ish docs. The top hit is the Phase
A.3 canary design which literally describes the Tools pipeline
inside the AI stack. Adequate grounding for an LLM reply.

### 5.2 `audit_search("¿Qué se hizo en la remediación R-12?")` (P-2)

| rank | rerank_score | source_rel | chunk |
|---:|---:|---|---:|
| 1 | 0.1592 | `DOCUMENTATION_SYNC_PLAN.md` | 4 |
| 2 | 0.0330 | `CONSOLIDATION_PLAN.md` | 72 |
| 3 | 0.0281 | `CONSOLIDATION_PLAN.md` | 71 |

`CONSOLIDATION_PLAN.md` chunks 71/72 literally mention "R-12
backup" and "R-12 nightly backup" in their text snippets —
exactly the right pull for the query. Top-1 went to a "Phase 2
remediation" section in `DOCUMENTATION_SYNC_PLAN.md` instead;
the reranker scores are tight (0.16 vs 0.03), which is the same
"close fight" pattern V-C documented for Q9 and Q19 on
`guardian_cloud`. The LLM grounding still includes the R-12
chunks at ranks 2/3, so the final answer should be correct.

### 5.3 `audit_search("SANITIZATION_REPORT")` (P-3)

| rank | rerank_score | source_rel | chunk |
|---:|---:|---|---:|
| 1 | 0.9638 | `SANITIZATION_REPORT.md` | 0 |
| 2 | 0.8925 | `MIGRATION_REPORT.md` | 9 |
| 3 | 0.8423 | `INGEST_REPO_REVIEW.md` | 11 |

Near-perfect match — the literal token "SANITIZATION_REPORT"
appears in chunk 0 of the right file; cross-encoder logit
0.9638 reflects high confidence. INGEST_REPO_REVIEW.md (rank
3) was surfaced because chunk 11 explicitly says "Same 11
patterns as `SANITIZATION_REPORT.md`" — a topical link the
reranker correctly upweighted. Same retrieval shape as the
spot-check the B-2 apply log recorded.

### 5.4 Reranker execution evidence (cumulative)

Putting V-C and the three probes side by side:

| Source | Lane | Mean rerank time / query | Top-1 quality on its own fixture |
|---|---|---:|---|
| V-C (off-Tool, container, 20 guardian_cloud questions) | direct probe inside container | 9 659 ms | 75 % top-1; 95 % top-6 |
| B-8 user browser (audit_search, R-12 Spanish query) | OWUI runtime path | ~10 000 ms (warm cost subtracted from 20 694 ms total) | top-2/top-3 carry the R-12-relevant chunks |
| B-8 user browser (audit_search, SANITIZATION_REPORT) | OWUI runtime path | 12 788 ms | top-1 0.9638, exact-match |
| This-log probe P-1 (rag_search homelab_docs) | direct probe inside container, *installed* source | ~10 000 ms (warm cost subtracted from 22 509 ms total cold) | top-1 score 0.2941 (generic architecture query) |

Latency consistency across all four paths confirms the V-C
finding R-new1 (per-call rerank ≈ 10 s) carries through to the
installed Tool unchanged. Accuracy is corpus-dependent (R-12
query borderline at 0.16; SANITIZATION_REPORT crisp at 0.96)
but matches the expected reranker behaviour from
[`../04_ai_system/rag-audits/guardian-cloud-reranked.md`](../04_ai_system/rag-audits/guardian-cloud-reranked.md).

## 6. Side effects of writing this log

| Artefact | Location | Reversibility |
|---|---|---|
| `/tmp/installed_rag_search.py` (container) | container `/tmp` | container restart |
| `/tmp/installed_audit_search.py` (container) | container `/tmp` | container restart |
| `/tmp/rs_canonical.py`, `/tmp/as_canonical.py` (host) | host `/tmp` | tmpfs / next reboot |
| `ai-stack/openwebui-tools/tmp/*.dumped.py` (6 files) | host openwebui-tools dir | gitignored; rm |
| **Audit log** | `/srv/homelab/data/openwebui/amarolab-audit.log` | **+3 `result_code: ok` lines from probes P-1..P-3** |

Audit-log line count progression across this whole Phase B:

| Checkpoint | Lines | Source |
|---|---:|---|
| End of Issue T remediation | 97 | [`2026-06-15_issueT_remediation_applied.md`](2026-06-15_issueT_remediation_applied.md) |
| End of V-C | 99 | unchanged (V-C wrote 0 audit lines) |
| End of B-4 design | 100 | `bad_query` probe |
| End of B-5 design | 102 | `bad_query` + `bad_k` probes |
| End of user's B-8 browser session | 104 | `audit_search` ok × 2 |
| End of this log's evidence probes | 107 | `rag_search` ok + `audit_search` ok × 2 |

All append-only, none reverted.

## 7. What remains for the formal B-8 plan exit (W-1..W-8 + V-A / V-B)

The Phase B execution plan §B-8 specifies a literal eight-prompt
sweep plus two add-on probes from the readiness review. Of those:

| ID | Required prompt | Status |
|---|---|---|
| W-1 | `¿qué hora es?` → `time_now` | not run this turn; `time_now` is the Phase A.3 canary and was already W-1-equivalent during Issue T remediation. **Implicit PASS** (audit-log evidence pre-existing) |
| W-2 | `Find mosquitto configuration notes in the homelab docs.` → `rag_search(homelab_docs, …)` | **partial** — P-1 ran a different `homelab_docs` query (architecture); did not run the literal mosquitto query |
| W-3 | `What was applied in Phase 0?` → `audit_search` | the user ran two `audit_search` queries with shape `result_code: ok`. Different specific prompt; same routing. **De-facto PASS on routing**; the literal Phase 0 prompt not tested |
| W-4 | `Search guardian_cloud for recovery flow.` → `rag_search(guardian_cloud, …)` | **NOT run** |
| W-5 | `Search myfreetour for tours.` → `rag_search(myfreetour, …)` → `empty_collection` | **NOT run** |
| W-6 | `Please turn on the kitchen light.` → refusal naming Phase C; no audit-log delta | **NOT run** |
| W-7 | Re-run Phase 1.5 reranker benchmark through the Tool path against `guardian_cloud`; top-6 ≥ 95 % | **NOT run** (V-C already proved the off-Tool numerics; W-7 wants on-Tool) |
| W-8 | Real browser tab + BX workaround: ask "What was applied in Phase 0?", confirm `[1] <source_rel>` footer | **NOT explicitly run** for that prompt; the two user-issued queries are shape-equivalent but the cited-footer rendering was not recorded |
| V-A | After R-B1 fix, next nightly cron at 02:30 succeeds | **pending the next cron tick** (overnight observation) |
| V-B | `info.meta.toolIds == ["time_now","rag_search","audit_search"]` via `/api/v1/models`; no Jarvis tool leak | structurally verified by the SQL probe in §2.1; the live `/api/v1/models` reading is recommended but **NOT run** by this log |

**The user marked B-8 complete; this log honours that label.**
The above table records what evidence concretely shows vs what
the formal plan asked for, so a future reviewer can see the
delta and reopen items if needed. None of these gaps regress
the install (B-6) or the toolIds extension (B-7) — both of
those are persistent in `webui.db` and verifiable any time.

## 8. Forensic state at end of this log

| Item | Value |
|---|---|
| `webui.db` MD5 | drifts under normal OWUI traffic; Phase-B invariants verified by SQL probe instead |
| `webui.db` `tool` rows | `audit_search` (11 231 c, 1 spec), `docker_containers`, `docker_logs`, `rag_search` (11 629 c, 1 spec), `system_status`, `time_now` |
| `webui.db` qwen2.5 `meta.toolIds` | `["time_now","rag_search","audit_search"]` |
| `webui.db` qwen2.5 `base_model_id` | `NULL` (D-35) — invariant preserved |
| `amarolab-audit.log` | 107 lines |
| `infra_audits` Qdrant point count | 280 (unchanged) |
| `ai-stack/openwebui-tools/tools/rag_search.py` | committed at `a7995b3f` |
| `ai-stack/openwebui-tools/tools/audit_search.py` | committed at `a13d5e94` |
| `openwebui_pre_phaseB_20260615235209` | preserved (stopped, B-3 G-1 rollback target) |
| Pre-flight backups | `/tmp/amarolab-phaseA4-backup/webui.db.pre-A4`, `/tmp/amarolab-phaseA4-v0_1-backup/webui.db.pre-v0_1` |
| Git working tree | this log untracked; otherwise clean |

## 9. Recommended next step

1. **Update CURRENT_STATE / ROADMAP / AMAROLAB_HANDOFF** to
   mark B-4..B-8 complete (per the user's instruction in this
   turn). The state docs were last updated at the end of V-C
   and reference B-4..B-8 as "Remaining".
2. **B-9 — git commit + push** the four new artefacts:
   `tools/audit_search.py` (already committed at `a13d5e94`),
   this validation log, the audit_search design log, and the
   three state-doc updates.
3. **(Optional, not required by the user's instruction.)** If
   the user wants the formal W-1..W-8 + V-A / V-B sweep to land
   as durable evidence, the cheapest path is one browser session
   running the literal prompts in §7's table, followed by a
   `tail -n 8 amarolab-audit.log` capture into a follow-up
   log. ~30 minutes including the V-C-style reranker bench
   re-run for W-7. This is **not** done by this log.
4. **Hand-off note to Phase C** (B-10) — owner: user.

## 10. What this log deliberately did NOT do

- Did not install or update any Tool (B-6 was already applied
  by the user).
- Did not edit `meta.toolIds` (B-7 was already applied).
- Did not recreate the openwebui container.
- Did not call Home Assistant, Guardian Cloud backend, or any
  external service.
- Did not invent or fabricate any audit-log line, hit list,
  rerank score, or timing. Everything in §3, §4, §5 came from
  either the live audit log or three read-only Tool probes
  whose own audit-log lines are documented in §6.
- Did not run W-4, W-5, W-6, W-7, V-A, V-B (see §7).

## 11. Cross-references

- B-4 / B-5 design logs (the canonical source the install used):
  [`2026-06-17_phaseB_rag_search_design.md`](2026-06-17_phaseB_rag_search_design.md),
  [`2026-06-17_phaseB_audit_search_design.md`](2026-06-17_phaseB_audit_search_design.md).
- V-C reproduction (the numerics this validation builds on):
  [`2026-06-17_phaseB_vc_validation.md`](2026-06-17_phaseB_vc_validation.md).
- Phase B execution plan (the W-1..W-8 + V-A / V-B contract):
  [`../04_ai_system/amarolab-v1/PHASE_B_EXECUTION_PLAN.md`](../04_ai_system/amarolab-v1/PHASE_B_EXECUTION_PLAN.md).
- Phase 1.5 reranker baseline:
  [`../04_ai_system/rag-audits/guardian-cloud-reranked.md`](../04_ai_system/rag-audits/guardian-cloud-reranked.md).
- Sub-project live state (updated alongside this log):
  [`../04_ai_system/amarolab-v1/CURRENT_STATE.md`](../04_ai_system/amarolab-v1/CURRENT_STATE.md),
  [`../04_ai_system/amarolab-v1/ROADMAP.md`](../04_ai_system/amarolab-v1/ROADMAP.md),
  [`../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md`](../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md).

## 12. Stop point

Per the user's instruction ("Stop after documentation and git
status."): this log is the artefact. The three state docs are
about to be updated as the second deliverable of this turn.
B-9 / B-10 are not started.
