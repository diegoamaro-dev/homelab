# Phase B — execution readiness REVIEW — INVESTIGATION ONLY

- **Date:** 2026-06-16.
- **Goal:** determine whether Amarolab Assistant v1 is ready to
  implement `rag_search` (and its sugar tool `audit_search`).
  Identify prerequisites, risks, missing dependencies, validation
  criteria. **Do not implement.**
- **Inputs:**
  [`04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md`](../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md),
  [`04_ai_system/amarolab-v1/CURRENT_STATE.md`](../04_ai_system/amarolab-v1/CURRENT_STATE.md),
  [`04_ai_system/amarolab-v1/ROADMAP.md`](../04_ai_system/amarolab-v1/ROADMAP.md),
  [`04_ai_system/amarolab-v1/PHASE_B_EXECUTION_PLAN.md`](../04_ai_system/amarolab-v1/PHASE_B_EXECUTION_PLAN.md),
  the Phase A closeout, the Issue T re-investigation + remediation
  logs, plus live read-only probes of `webui.db`, the ingest tree,
  the openwebui container, Qdrant, the audit log, and the model
  cache.
- **What this log is NOT:** an apply log; no code, prompt, env,
  container, DB, or filesystem change was made. Two side-effect
  classes admitted: (a) one read-only Qdrant `GET /collections`
  via the admin API key already configured by Phase 0; (b) one
  in-container Python import probe to enumerate installed
  packages. No Tool was invoked, no audit log entry added.

## 0. Verdict — TL;DR

**Phase B is mostly ready. One real blocker, one real risk, two
gated decisions, and a small list of housekeeping items.**

| Item | Verdict |
|---|---|
| **Design completeness** (Phase A.2 design + D-18..D-22 + D-24..D-26 + D-35 + 03-tools.md outline) | **Complete.** No further design questions need answering before writing `rag_search.py`. |
| **Source tooling** (`bin/install_tool`, `lib/audit_helper.py`, `class Tools` shape, frontmatter convention, JWT minting flow) | **Complete and proven by Phase A.3 / Issue T remediation.** |
| **Runtime dependencies in the openwebui container** (sentence-transformers, transformers, torch, qdrant-client, pydantic, numpy, huggingface_hub) | **All present** — see §3.4. Container Python is **not** the brake. |
| **Model cache on disk** (multilingual-e5-small + bge-reranker-v2-m3) | **Both present and bind-mounted** at the container's HF_HOME (§3.5). No download needed at first call. |
| **Audit corpus source data** (`/home/diego/server-audit-2026-06-13/**/*.md`, 6 files) | **Present** (§3.6). |
| **Issue T remediation in place** (qwen2.5 Model entry `base_model_id = NULL`) | **In place** since 2026-06-16; browser auto-attach of `tool_ids` now verified end-to-end (§3.7). |
| **`infra_audits` corpus** (`corpora.yaml` entry, Qdrant collection) | **Not present** — expected for Phase B (B-1, B-2). |
| **`tools/rag_search.py`, `tools/audit_search.py` source files** | **Not present** — expected (B-4, B-5). |
| **`/opt/ingest` bind mount** in openwebui container | **Not present** — gated by **G-1** (B-3). |
| **`meta.toolIds` update** on the qwen2.5 Model entry | **Pending** — gated by **G-2** (B-7). |
| **Ingest CLI runnable** (P-3) | **❌ FAILING.** `bin/ingest` and `python -m ingest.cli` both raise `ModuleNotFoundError: No module named 'ingest'` because the package is not pip-installed in its venv and the wrapper does not set PYTHONPATH or `cd` to the package root. The nightly cron has been **silently failing since at least 2026-06-15 02:30** (the only log entry on disk is this error). Detail in §4.1. |
| **sentence-transformers major-version drift** (ingest tested against `>=3.0,<4`; openwebui container has `5.2.3`) | **Material risk** for the W-7 reranker-benchmark exit criterion. Detail in §4.2. |
| **Git push gap** (local commit `2081965a` ahead of `origin/main`) | **Documentation hygiene** — needs to land before B-9 from a credentialed environment. Detail in §4.7. |

**Recommendation:** before running the Phase B execution plan,
the **one mandatory remediation** is to fix the ingest CLI
brokenness (R-B1, §4.1). Everything else is either already true,
explicitly gated and expected, or a risk to manage during
validation.

If the user approves the §6 minimum-prep sequence (≈10 minutes,
zero state change beyond fixing one shell script + one
`pip install -e .`), Phase B can start with confidence on the
existing PHASE_B_EXECUTION_PLAN.md path.

## 1. Phase B in one paragraph (what we're being asked to build)

`rag_search(collection, query, k)` is the **dense-retrieval +
cross-encoder-rerank** Tool that lets the assistant ground answers
in the four already-indexed corpora (`homelab_docs`,
`guardian_cloud`, `ensambla2`, `myfreetour` placeholder) plus the
new `infra_audits` corpus this phase creates. `audit_search` is
sugar over `rag_search(collection="infra_audits", …)`. Both run
inside the existing `openwebui` Tools runtime as
`class Tools`-shaped Python modules installed in `webui.db` via
the supported API (D-24, D-25). They import `Embedder` and
`Reranker` from the existing `ai-stack/ingest` package via a
read-only bind mount that B-3 adds, lazily instantiate the
sentence-transformers models on first call, and audit every
invocation to
`/srv/homelab/data/openwebui/amarolab-audit.log` (D-07, D-21).
Per-model scoping (D-20) routes both Tools to
`qwen2.5:7b-instruct` only; the Jarvis llama3 entries continue to
see their own pre-existing tools and nothing else.

The exit bar (binding, from `05-implementation-roadmap.md` and
the ROADMAP) is **the Phase 1.5 reranker benchmark reproduced via
the Tool path: top-6 ≥ 95 % on `guardian_cloud`, within ±2 pp of
the off-Tool baseline**.

## 2. Source-of-truth crosswalk

What the design says vs where the implementation will live:

| Concern | Source of truth | Implementation site |
|---|---|---|
| Tool input schema | [`03-tools.md`](../04_ai_system/amarolab-v1/03-tools.md) §"Tool 1 — rag_search → Input" | `tools/rag_search.py` `class Args(BaseModel)` + method signature |
| Tool output shape | same §"Output" | return JSON dict shaped `{collection, query, hits:[…]}` |
| Routing description in prompt | [`03-tools.md`](../04_ai_system/amarolab-v1/03-tools.md) §"Routing guidance" + system prompt v0.1 §"# Tools" | v0.1 prompt already mentions `rag_search(collection, query, top_k?) — NOT YET WIRED (Phase B)`. After install, qwen2.5 sees the spec via the resolved tools array; the prompt does not need to be re-applied for this. v0.2 may tighten routing examples (carry-over, not a Phase B blocker). |
| Trust model + LLM-as-adversary rule | [`04-security-and-permissions.md`](../04_ai_system/amarolab-v1/04-security-and-permissions.md) (D-06) | `Args(BaseModel)` with `Literal[…5 names…]` for `collection`; no `eval`, no `subprocess`, no path-from-arg |
| Tool runtime shape | [`FUNCTIONS_COMPATIBILITY_REPORT.md`](../FUNCTIONS_COMPATIBILITY_REPORT.md) §3 (D-24) | `class Tools` with type-hinted methods, no module-level functions |
| Tool install workflow | same §5 (D-25) | reuse `bin/install_tool` (mint JWT, POST `/api/v1/tools/create`) |
| Helper handling | same §7 (D-26) | inline `lib/audit_helper.py` into the Tool source via `# @@AMAROLAB_INLINE:audit_helper@@` marker |
| Per-model scope | (D-20) | update `meta.toolIds` on qwen2.5 entry (G-2 gates this) |
| Audit-log path | (D-07, D-21) | inlined helper writes JSONL to `/app/backend/data/amarolab-audit.log` (= `/srv/homelab/data/openwebui/amarolab-audit.log` on host) |
| Model-entry shape rule | (D-35, new since Issue T re-investigation) | qwen2.5 row already corrected (`base_model_id = NULL`); update preserves it |
| `myfreetour` collection enum behaviour | (D-22) | Tool returns `{"error":"empty_collection","code":"empty_collection"}` |
| Embedder / reranker identity | (D-08) | unchanged — `intfloat/multilingual-e5-small`, `BAAI/bge-reranker-v2-m3` |

**No new design decisions are blocked** by anything left of
Phase B. The plan composes locked decisions; no D-36 is needed
to start.

## 3. Pre-flight live state (P-1..P-10 from PHASE_B_EXECUTION_PLAN §"Pre-flight checks")

Read-only probes against the live system at apply-review time.

### 3.1 P-1 — Phase A closed, all three state docs reference Phase B

```
grep -l 'Phase B' .../{CURRENT_STATE,ROADMAP,AMAROLAB_HANDOFF}.md
  → CURRENT_STATE.md, ROADMAP.md, AMAROLAB_HANDOFF.md   (all three)
```

ROADMAP.md "Current phase" section says `### Phase B — Knowledge
Tool + audit corpus`. AMAROLAB_HANDOFF.md "Current phase" says
`**Phase B — Knowledge Tool + audit corpus.** Not started`.

**PASS.**

### 3.2 P-2 — qwen2.5 Model-entry scope is `["time_now"]`

```
sqlite> SELECT json_extract(meta,'$.toolIds') FROM model
        WHERE id='qwen2.5:7b-instruct';
["time_now"]
```

Also confirmed: `base_model_id` is the empty/NULL value left by
the 2026-06-16 Issue T remediation (D-35).

**PASS.**

### 3.3 P-3 — ingest service runnable from the venv

```
$ /home/diego/homelab/ai-stack/ingest/venv/bin/python -m ingest.cli --help
/.../python: Error while finding module specification for 'ingest.cli'
            (ModuleNotFoundError: No module named 'ingest')

$ /home/diego/homelab/ai-stack/ingest/bin/ingest --help
/.../python: Error while finding module specification for 'ingest.cli'
            (ModuleNotFoundError: No module named 'ingest')

# But this works:
$ cd /home/diego/homelab/ai-stack/ingest \
  && PYTHONPATH=. ./venv/bin/python -m ingest.cli status
collection         points   enabled
homelab_docs       86       True
guardian_cloud     872      True
ensambla2          419      True
myfreetour         0        False
```

**FAIL.** The package is not pip-installed in its own venv
(`pip show ingest` returns empty; `site-packages/` has no
`ingest*` directory). The cron wrapper `bin/ingest` activates the
venv but does *not* `cd $ROOT` or set `PYTHONPATH`, so
`python -m ingest.cli` cannot locate the package. The nightly
cron has been **silently failing since at least 2026-06-15
02:30** — the only entry in `ingest/logs/ingest.log` is this
identical traceback. Detail and fix in §4.1.

### 3.4 P-4 — Qdrant API key reachable from host

```
$ curl -s -H "api-key: $KEY" http://127.0.0.1:6333/collections | jq '.result.collections[].name'
"open-webui_files"
"guardian_cloud"
"myfreetour"
"open-webui_knowledge"
"ensambla2"
"homelab_docs"
```

HTTP 200. Six collections present.

Two are **OWUI-internal** (`open-webui_files`,
`open-webui_knowledge`) — created by Open WebUI's built-in
Knowledge feature, **not part of the Amarolab v1 design**. They
are harmless for Phase B (rag_search's `collection` parameter is
a `Literal[…]` of the five Amarolab corpora; the OWUI-internal
ones cannot be selected). They are documented here for
traceability and will be a side-cleanup item later — see §4.6.

**PASS** for Phase B purposes. Note in §4.6.

### 3.5 P-5 — Audit corpus source files present

```
$ find /home/diego/server-audit-2026-06-13 -name '*.md' | wc -l
6

# files:
SANITIZATION_REPORT.md
INGEST_REPO_REVIEW.md
MIGRATION_REPORT.md
CONSOLIDATION_PLAN.md
DOCUMENTATION_SYNC_PLAN.md
GITHUB_COMMIT_PLAN.md
```

**PASS.** (Plan: `≥ 6` markdowns.)

### 3.6 P-6 / P-7 — Embedder + reranker cache on host

```
$ ls /srv/homelab/data/openwebui/cache/embedding/models/hub/
  models--intfloat--multilingual-e5-small        # embedder, ✓
  models--BAAI--bge-reranker-v2-m3               # reranker, ✓ (2.2 GB)
  models--sentence-transformers--all-MiniLM-L6-v2 # OWUI built-in, not used by Amarolab

$ ls .../models--BAAI--bge-reranker-v2-m3/snapshots/<sha>/
config.json
model.safetensors
sentencepiece.bpe.model
special_tokens_map.json
tokenizer_config.json
```

Both Amarolab-required snapshots are fully populated. The host
cache is bind-mounted into the container at
`/app/backend/data/cache/embedding/models` (and the container's
`HF_HOME` env points at exactly that path).

**PASS.**

### 3.7 P-8 / P-9 — Pre-flight backups

Neither exists yet. These are part of **B-0** (pre-flight) of the
execution plan, not part of this review.

**Not yet — expected.** Take during B-0.

### 3.8 P-10 — .env carries the required keys

```
$ stat -c '%a %U' /home/diego/homelab/ai-stack/.env
600 diego

$ grep -cE '^(QDRANT_API_KEY|WEBUI_SECRET_KEY|QDRANT__SERVICE__API_KEY)=' .env
3
```

`QDRANT_API_KEY`, `WEBUI_SECRET_KEY`, and
`QDRANT__SERVICE__API_KEY` all present, mode 0600, owner `diego`.

**PASS.**

### 3.9 Issue T remediation still in place (live verification)

Not in the plan's P-1..P-10 set, but added by this review.

```
sqlite> SELECT base_model_id, json_extract(meta,'$.toolIds'),
                length(params)
        FROM model WHERE id='qwen2.5:7b-instruct';
(NULL)|["time_now"]|3514

$ docker exec openwebui python3 -c "..."
=== qwen2.5 in merged /api/models ===
has info : True
info.meta.toolIds : ['time_now']
```

**PASS.** The browser-UI auto-attach path the Issue T remediation
restored is still working; whatever Phase B adds will inherit it.

## 4. Risks, blockers, and missing dependencies

Three categories:
- **R-B** (real Phase B blockers — must clear before the named step),
- **R-M** (material risks — likely to surface during validation; need a mitigation),
- **R-O** (operational housekeeping — should land but does not block).

### 4.1 R-B1 — Ingest CLI is broken; nightly cron has been silently failing

**Severity:** blocker for B-2 (corpus creation + first sync).
Soft warning for B-4 (Tool will likely work despite this).

**What's wrong:**
- `bin/ingest` is a `bash` wrapper that does
  ```
  . "$ROOT/venv/bin/activate"
  exec python -m ingest.cli "$@"
  ```
  It does **not** `cd "$ROOT"` and does not set `PYTHONPATH=$ROOT`.
- `install.sh` runs `pip install -r requirements.txt` but does
  **not** `pip install -e .` (and there is no `pyproject.toml` /
  `setup.py` so it couldn't have anyway). The package source
  exists only as a directory on disk; it is never importable
  through the venv's normal `sys.path`.
- Cron job `30 2 * * * /home/diego/homelab/ai-stack/ingest/bin/ingest sync` runs in `/home/diego`; `python -m ingest.cli` from that CWD does not see the package.
- The on-disk log
  `/home/diego/homelab/ai-stack/ingest/logs/ingest.log` contains
  exactly one repeating line (the `ModuleNotFoundError`
  traceback) — no successful sync since the last manual run.

**Why the Qdrant collections still have data:** they were
populated by the original Phase 1 / Phase 1.5 work, when the CLI
was invoked from inside the package root (likely via
`./venv/bin/python -m ingest.cli sync` while `cd`'d to the
ingest directory). The collections survive because Qdrant
persists; the ingest service itself has been broken at the CLI
level since.

**Fix options** (smallest first):

| Path | Action | Pro | Con |
|---|---|---|---|
| **F-1 (smallest)** | Add `cd "$ROOT"` to `bin/ingest` *before* the `exec` line | One-line change to one file | Still no proper packaging; future change to invocation path risks regressing |
| **F-2** | Add `export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"` *before* the `exec` line in `bin/ingest` | Two-line change; CWD-independent | Same as F-1; still no proper packaging |
| **F-3** | Add a minimal `pyproject.toml` to the ingest tree, then `pip install -e .` from inside the venv. Cron and bin/ingest then "just work" | Proper packaging; future-proof | A few more lines of yaml/toml; requires one extra `pip install -e .` step |

**Recommendation:** **F-3** (proper packaging) for v1.1; **F-2**
as the minimal Phase B unblock if F-3 is out of scope this turn.
Either way, **B-2 cannot run until this is fixed** — its
"Spot-check via `bin/ingest search`" command would simply error.

**Side-effect of fixing:** the next 02:30 cron run will start
succeeding. That's a desirable outcome. No new state change is
implied.

### 4.2 R-M1 — `sentence-transformers` major-version drift between ingest venv (`>=3.0,<4`) and openwebui container (`5.2.3`)

**Severity:** material risk for **W-7** (reranker-benchmark
reproduction).

**What's at risk:**
- The ingest venv installs `sentence-transformers>=3.0,<4` per
  `requirements.txt`. Inside `bin/ingest sync`, this is the
  version that produced the Phase 1.5 benchmark numbers.
- The openwebui container ships with **`sentence-transformers
  5.2.3`** (verified by `docker exec openwebui python3 -c
  "import sentence_transformers; print(sentence_transformers.__version__)"`).
- The `rag_search` Tool runs **inside the container**, so it uses
  5.2.3 — *not* the 3.x the benchmark used.
- `Embedder` (`SentenceTransformer(MODEL_NAME)`) and `Reranker`
  (`CrossEncoder(MODEL_NAME)`) are stable APIs across 3.x → 5.x,
  but there are documented changes in tokenization, pooling
  defaults, and quantization behaviour. **A small but non-zero
  drift in rerank scores is plausible.**

**Mitigation candidates:**

| Path | Pro | Con |
|---|---|---|
| **M-1** | Accept ±2 pp tolerance in W-7 (already in the plan). | No extra work. | Could miss the 95 % bar if drift is larger than tolerance. |
| **M-2** | Pin `sentence-transformers<4` *inside the container* (env override or wheels mounted in). | Eliminates drift. | Requires touching the openwebui container's Python env — invasive; affects OWUI's own RAG path. **Not recommended in v1.** |
| **M-3** | Pre-validate W-7 with a one-shot script that runs `Embedder()` + `Reranker()` against the existing benchmark fixture **inside the container**, before installing the Tool. Confirms the rerank output bytes match the Phase 1.5 numbers to within tolerance. | Catches drift early without touching state. | Adds a probe step before B-4. |

**Recommendation:** **M-3**. Run a one-shot probe step (no
state change) right after B-3 succeeds, before authoring
`rag_search.py`, to confirm the container's
`sentence-transformers 5.2.3` reproduces the benchmark within
tolerance. If it does not, escalate to M-2 or hold Phase B and
root-cause.

### 4.3 R-M2 — qwen2.5 over- or under-routing between `rag_search` and `audit_search`

**Severity:** already in the plan's risk register (medium
likelihood, low impact). Not a blocker.

**Note added by this review:** the v0.1 prompt currently
describes `rag_search(collection, query, top_k?)` as *NOT YET
WIRED (Phase B). Do not call it.* After B-7, that line is wrong —
the prompt instructs the model to *not* call a tool that is now
attached. The model will probably honour the spec's docstring
over the prompt's stale "Do not call it", but it's a contradiction
worth removing.

**Recommendation:** before declaring B-8 green, refresh the
two lines under `# Tools` in the system prompt to mark
`rag_search` and `audit_search` as APPLIED. This is a tiny edit
(swap "NOT YET WIRED (Phase B). Do not call it." → "APPLIED.")
on the qwen2.5 Model entry. *Not* a full v0.2 prompt iteration
— that remains a separate carry-over for Issue L / Issue B /
the `[1]` literal contradiction.

### 4.4 R-M3 — Lazy-init cold-load timeout on first `rag_search` call

**Severity:** already in the plan's risk register. Confirmed
viable concern.

**Note added by this review:** `Reranker` constructor calls
`CrossEncoder("BAAI/bge-reranker-v2-m3")`, which loads
**~2.2 GB** of model weights from disk into CPU RAM. Even with
the cache hit and a fast NVMe, this takes 8–25 s on a Zen 4 host.
The first `rag_search` invocation will *block* for that duration.

Open WebUI's chat-completion HTTP request has its own timeout;
the underlying Tool call inside the OWUI Tools runtime does
**not** appear to have a hard timeout in the 0.8.10 source, but
the user-facing socket.io path can give up. The result is
visible as either "the model gave up and answered without tool
output" or as a frontend timeout toast.

**Mitigation:** the plan already specifies "warm up by
curl-calling `rag_search` once after B-3 succeeds, before W-1".
This review reaffirms that step as mandatory, and adds: do the
warm-up against **both** corpora that W-2 and W-4 test
(`homelab_docs` and `guardian_cloud`), and against
`infra_audits` once B-2 populates it, so the cold cache hit
happens off the user-facing path.

### 4.5 R-O1 — `system_status` Tool name collision with Phase D

**Severity:** **not a Phase B blocker.** Phase B does not
install or touch `system_status`. Worth keeping flagged.

**State:** `webui.db` already contains a `tool` row with id
`system_status` (the pre-existing Jarvis `psutil`-based tool, ~507
char content, scoped to `llama3:latest` and `llama3.2:latest`).
Phase D's planned `system_status` will collide by id when its
install workflow tries `POST /api/v1/tools/create` (HTTP 409
expected, or silent overwrite via `/update`).

**Recommendation:** decide between (a) rename the Jarvis tool
(`docker_system_status`?), or (b) accept that Phase D's install
will replace it, before Phase D starts. **Out of scope for this
review**; was flagged in the Issue T re-investigation §5.5 and is
restated here for traceability.

### 4.6 R-O2 — OWUI-internal Qdrant collections (`open-webui_files`, `open-webui_knowledge`)

**Severity:** not a Phase B blocker.

**State:** Open WebUI's built-in Knowledge feature has created
two collections in the same Qdrant instance that the Amarolab
ingest service uses. They are not in the Amarolab corpus list
and the `rag_search` Tool's `collection` parameter is a
`Literal[…5 Amarolab names…]` — they cannot be selected by the
LLM. They share storage and quota.

**Recommendation:** revisit in v1.1 if/when storage pressure
appears. No Phase B action.

### 4.7 R-O3 — Git push lag from the Issue T remediation

**Severity:** documentation hygiene; does not block code work.

**State:** local commit
`2081965a6fe7372af844771f941e5621785034a2` (Issue T remediation
+ D-35) is ahead of `origin/main`. The previous turn's `git
push` failed because the CLI environment has no usable GitHub
credentials. The user said the homelab repo is synchronized to
GitHub; the divergence will be visible to anyone fetching from
`origin/main`.

**Recommendation:** push the existing commit from a
credentialed environment (VS Code GitHub extension is the
documented path) **before** Phase B B-9 — so that B-9's commit
chain has a clean history. No code change.

### 4.8 R-O4 — `time_now` Tool source duplication: canonical vs `tmp/*.dumped.py`

**Severity:** none. Mentioned only because it confused this
review for a few seconds.

**State:** `openwebui-tools/tools/time_now.py` is the
canonical, version-controlled Tool source (D-23). The
`openwebui-tools/tmp/{docker_containers,docker_logs,system_status,time_now}.dumped.py`
files are `dump_tools` output, dumped from `webui.db` for diff
purposes. They are not the source of truth and should not be
edited. The README explains this.

**Recommendation:** no change.

## 5. Validation criteria (what "Phase B is done" means, with additions)

The Phase B execution plan defines W-1..W-8. This review
**adopts them all unchanged** and adds three:

| ID | Source | Action | Pass criterion |
|---|---|---|---|
| W-1 | plan | `¿qué hora es?` → `time_now` invocation (no regression from Issue T fix) | +1 audit-log line, reply has real wall-clock time |
| W-2 | plan | `Find mosquitto configuration notes in the homelab docs.` → `rag_search(collection="homelab_docs", …)` | +1 audit-log line, `result_code="ok"`, top-1 hit references mosquitto-related docs |
| W-3 | plan | `What was applied in Phase 0?` → `audit_search(query=…)` | +1 audit-log line, `result_code="ok"`, top-1 hit references Phase 0 application logs in `/home/diego/server-audit-2026-06-13/**/*.md` |
| W-4 | plan | `Search guardian_cloud for recovery flow.` → `rag_search(collection="guardian_cloud", …)` | top-1 rerank score in Phase 1.5 benchmark range |
| W-5 | plan | `Search myfreetour for tours.` → `rag_search(collection="myfreetour", …)` | `{"error":"empty_collection","code":"empty_collection"}` (D-22), `result_code="empty_collection"` in audit log |
| W-6 | plan | `Please turn on the kitchen light.` | refusal naming Phase C; **no audit-log delta** |
| W-7 | plan | Re-run the Phase 1.5 reranker benchmark via the Tool path against `guardian_cloud` | Top-6 ≥ 95 % within ±2 pp of off-Tool baseline |
| W-8 | plan | Real browser tab + BX workaround: ask `"What was applied in Phase 0?"`, confirm `[1] <source_rel>` footer | reply cites real sources, audit log shows the call, no `Unexpected token 'd'` toast |
| **V-A** *(new)* | this review | After fixing R-B1, run `bin/ingest status` and confirm the next nightly cron at 02:30 succeeds (next-day check) | `ingest.log` last line is not the ModuleNotFoundError; collection counts unchanged or `+infra_audits` |
| **V-B** *(new)* | this review | With qwen2.5 selected, inspect `/api/v1/models` for qwen2.5's `info.meta.toolIds` | exactly `["time_now","rag_search","audit_search"]`; **no leak of `docker_containers` / `docker_logs` / `system_status` from the Jarvis Model entries** |
| **V-C** *(new)* | this review | After B-3 mount and *before* B-4 (R-M1 pre-empt), run the Phase 1.5 reranker benchmark *inside the openwebui container* against `guardian_cloud` using `sentence-transformers 5.2.3` | Top-6 within ±2 pp of the 3.x baseline. If outside tolerance, escalate per R-M1 M-2/M-3 before authoring `rag_search.py` |

V-A and V-C are early-warning probes — running them off the
critical path catches the two issues most likely to invalidate
W-7 *after* the Tool source is written. Cheap to run; high
information value.

## 6. Minimum prep before kicking off PHASE_B_EXECUTION_PLAN

This section enumerates the work needed **between this review
and B-0**. None of it is design work; none requires new
decisions; none touches `webui.db` or the running tools.

| Step | Action | Touches | Reversibility |
|---|---|---|---|
| **Prep-1** *(R-B1)* | Fix `bin/ingest` so `bin/ingest --help` exits 0. Smallest path: `pip install -e .` after adding a minimal `pyproject.toml` to the ingest tree. Alternative: `cd $ROOT` line in `bin/ingest`. | `ai-stack/ingest/` only; no DB, no container, no Tool | full — git revert |
| **Prep-2** *(R-B1 confirmation)* | Run `bin/ingest status` and confirm the four expected corpora come back with the counts already in `CURRENT_STATE.md` (homelab_docs 86, guardian_cloud 872, ensambla2 419, myfreetour 0) | read-only against Qdrant | n/a |
| **Prep-3** *(R-O3, hygiene)* | Push the existing `2081965a` commit from a credentialed environment so `origin/main` is current before Phase B starts | git remote | git push --force-with-lease if needed (but main is fast-forward, so normal push) |
| **Prep-4** *(R-M3)* | Skim the lazy-init pattern in `time_now.py` to ensure the planned `_init()` in `rag_search.py` will follow the same shape | source-of-truth only | n/a |
| **Prep-5** *(R-M2)* | Add a one-line edit to the qwen2.5 system prompt (v0.1.1) flipping `rag_search`'s status line from "NOT YET WIRED (Phase B). Do not call it." → "APPLIED.". **Optional**; the model will likely behave with the docstring alone, but tighter routing helps W-2 and W-4. Can be deferred to v0.2 if user prefers. | one column of one DB row, reversible | full |

Prep-1 is mandatory. Prep-3 should land before B-9. Prep-2, 4, 5
are quick verification steps; none touches Tool source or the
qwen2.5 meta beyond the optional prompt status line.

## 7. Gate status summary

| Gate | What | Where it lives | Recommended timing |
|---|---|---|---|
| **G-1** | Recreate `openwebui` container with read-only bind mount `/home/diego/homelab/ai-stack/ingest:/opt/ingest:ro` (see PHASE_B_EXECUTION_PLAN §B-3) | container recreate, host network mount only | Approve **after** Prep-1 + Prep-2 are green and the user has reviewed the new compose / docker-run command |
| **G-2** | `meta.toolIds` on qwen2.5 Model entry: `["time_now"]` → `["time_now","rag_search","audit_search"]` | `webui.db` one row, one column, reversible | Approve **after** B-6 succeeds (both tools installed and `dump_tools` round-trip clean) |
| **G-3** | Run the first end-to-end chat probe (W-1..W-8) against qwen2.5 with the new tools live | benign — same as a normal user chat; audit log gains real entries | Approve **alongside G-2** — there is no useful waypoint between |

All three gates are documented and reversible. None creates
durable cross-system state outside `webui.db` + the audit log
+ one optional container recreate (G-1 is reversible by the
`docker rename openwebui_pre_phaseB_<ts> openwebui` step in
the plan §B-3 rollback).

## 8. Recommendation

**Phase B is ready in plan and in design. It is ~85 % ready in
execution. The remaining 15 % is dominated by R-B1.**

Concrete next steps in the order this review recommends:

1. **Apply Prep-1** (fix `bin/ingest` so it actually runs;
   ~10 minutes; smallest fix is `cd "$ROOT"` line in the
   wrapper, but `pip install -e .` after adding a tiny
   `pyproject.toml` is preferred). Confirm with Prep-2.
2. **Apply Prep-3** (push the local Issue T remediation commit
   to GitHub from a credentialed environment) so Phase B's
   apply log lands on a clean origin/main.
3. **Walk PHASE_B_EXECUTION_PLAN.md B-0..B-2** to take the
   pre-flight backups and create the `infra_audits` corpus.
4. **Approve gate G-1** to add the `/opt/ingest` bind mount,
   run B-3, then **run V-C** (the pre-empt for R-M1) before
   touching `rag_search.py`.
5. If V-C passes, **proceed B-4..B-6** to author and install
   the two Tools (with the inlined audit helper, per D-26),
   then **approve gate G-2** to extend qwen2.5's
   `meta.toolIds`.
6. **Approve gate G-3** and run W-1..W-8 plus V-A and V-B as
   the canonical Phase B validation set.
7. **B-9** docs update + commit + push as the closeout (this
   review's contribution is a one-line addendum to
   `ROADMAP.md`'s "Completed phases" once W-7 is green).

If V-C in step 4 fails (the container's `sentence-transformers
5.2.3` drifts the reranker scores out of the ±2 pp window),
**hold Phase B at B-3**, document the divergence in a fresh
`*-design.md` log, and pick from R-M1's M-2 / M-3 mitigations
with the user before authoring the Tool source.

## 9. What this review deliberately did not do

- No code, no source-file edit, no DB write, no env-var
  change, no container restart, no service touch.
- No JWT minting, no API call against `/api/chat/completions`,
  no Tool invocation. (Audit-log delta from this turn: **0**.)
- No prompt edit. The v0.1 prompt remains as-is; the optional
  status-line refresh (Prep-5) is a recommendation, not an
  applied change.
- No filesystem write outside this single log file.
- No git commit, no git push, no remote operation.

## 10. Forensic state at end of review

| Item | Value |
|---|---|
| `webui.db` mtime | `2026-06-16 00:34:55 CEST` (unchanged since the Issue T remediation; matches `2026-06-15_issueT_remediation_applied.md` §10) |
| `webui.db` size | 2 347 008 bytes (unchanged) |
| qwen2.5 `base_model_id` | `NULL` (D-35) |
| qwen2.5 `meta.toolIds` | `["time_now"]` |
| `webui.db` tool rows | 4 (`time_now`, `docker_containers`, `system_status`, `docker_logs`) |
| Audit log line count | **97 (unchanged from end of Issue T apply)** |
| `infra_audits` Qdrant collection | not created |
| `infra_audits` in `corpora.yaml` | not added |
| `tools/rag_search.py`, `tools/audit_search.py` | do not exist |
| openwebui container | Up healthy; mounts = `/srv/homelab/data/openwebui → /app/backend/data` only (no `/opt/ingest` yet) |
| `bin/ingest --help` | **broken** (R-B1) |
| Last `ingest.log` line | `ModuleNotFoundError: No module named 'ingest'` from the 2026-06-15 02:30 cron |
| Git working tree | clean |
| Local vs origin/main | local is one commit ahead (`2081965a`, Issue T remediation) |

## 11. Cross-references

- Phase B execution plan (the next-action map):
  [`../04_ai_system/amarolab-v1/PHASE_B_EXECUTION_PLAN.md`](../04_ai_system/amarolab-v1/PHASE_B_EXECUTION_PLAN.md)
- Tool design — full catalog incl. `rag_search` outline:
  [`../04_ai_system/amarolab-v1/03-tools.md`](../04_ai_system/amarolab-v1/03-tools.md)
- Security / trust model (LLM-as-adversary, allowlist constants):
  [`../04_ai_system/amarolab-v1/04-security-and-permissions.md`](../04_ai_system/amarolab-v1/04-security-and-permissions.md)
- Implementation roadmap (canonical exit criteria, container
  templates):
  [`../04_ai_system/amarolab-v1/05-implementation-roadmap.md`](../04_ai_system/amarolab-v1/05-implementation-roadmap.md)
- Open WebUI 0.8.10 runtime contract (Tool shape, install
  workflow, namespace isolation):
  [`../FUNCTIONS_COMPATIBILITY_REPORT.md`](../FUNCTIONS_COMPATIBILITY_REPORT.md)
- Phase A closeout:
  [`2026-06-15_phaseA_closeout.md`](2026-06-15_phaseA_closeout.md)
- Issue T re-investigation (root cause behind D-35):
  [`2026-06-15_issueT_browser_validation_reopened.md`](2026-06-15_issueT_browser_validation_reopened.md)
- Issue T remediation apply (what's currently live):
  [`2026-06-15_issueT_remediation_applied.md`](2026-06-15_issueT_remediation_applied.md)
- BX (browser-UI WebSocket race; W-8 workaround):
  [`2026-06-15_openwebui_json_parse_error_analysis.md`](2026-06-15_openwebui_json_parse_error_analysis.md)
- Sub-project live state:
  [`../04_ai_system/amarolab-v1/CURRENT_STATE.md`](../04_ai_system/amarolab-v1/CURRENT_STATE.md)
- Sub-project status overlay:
  [`../04_ai_system/amarolab-v1/ROADMAP.md`](../04_ai_system/amarolab-v1/ROADMAP.md)
- Sub-project handoff:
  [`../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md`](../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md)
- Ingest service (R-B1 target):
  `/home/diego/homelab/ai-stack/ingest/`
- Tool source tree (Phase B will add `rag_search.py` and
  `audit_search.py` here):
  `/home/diego/homelab/ai-stack/openwebui-tools/tools/`
- Audit log:
  `/srv/homelab/data/openwebui/amarolab-audit.log`
- Audit-corpus source data:
  `/home/diego/server-audit-2026-06-13/`

## 12. Stop point

Per the user's instruction ("Do not implement yet. … Stop after
the review."): this log is the artifact. No applied work, no
code, no DB write, no container change. The minimum prep
recommended in §6 — most importantly the R-B1 fix — is a
proposal awaiting explicit instruction before any execution.
