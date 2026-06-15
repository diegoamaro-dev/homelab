# PHASE_B_EXECUTION_PLAN — Amarolab Assistant v1

Last updated: 2026-06-15 (drafted at Phase A closure; not yet executed)

## Purpose

Concrete, ordered, reversible execution plan for **Phase B —
Knowledge Tool + audit corpus**. This document is the next-action
map. It does *not* duplicate the design package; it composes the
locked decisions from
[`01-current-state-review.md`](01-current-state-review.md),
[`02-target-architecture.md`](02-target-architecture.md),
[`03-tools.md`](03-tools.md),
[`04-security-and-permissions.md`](04-security-and-permissions.md),
[`05-implementation-roadmap.md`](05-implementation-roadmap.md) and
the Phase A closeout
[`../../09_logs/2026-06-15_phaseA_closeout.md`](../../09_logs/2026-06-15_phaseA_closeout.md)
into a step-by-step playbook that another session can execute.

## Phase B scope

Two parallel tracks, three deliverables:

| Track | Deliverable | Where |
|---|---|---|
| **Corpus** | `infra_audits` Qdrant collection populated from `/home/diego/server-audit-2026-06-13/**/*.md` | Qdrant + `ingest/conf/corpora.yaml` |
| **Tools (1)** | `rag_search` Open WebUI Tool — dense + reranked search over the five corpora | `openwebui-tools/tools/rag_search.py`, `webui.db` |
| **Tools (2)** | `audit_search` Open WebUI Tool — sugar over `rag_search(collection="infra_audits", …)` | `openwebui-tools/tools/audit_search.py`, `webui.db` |

Exit (binding, from sub-project ROADMAP):
- The Phase 1.5 reranker benchmark reproduces when routed through
  the Tool path. Top-6 ≥ 95 % on `guardian_cloud`.
- One audit-log line per Tool call with the same 8-field schema as
  `time_now`.
- Per-model scoping (D-20) preserved — only `qwen2.5:7b-instruct`
  sees the new Tools.

## What Phase B explicitly does **not** do

- No `system_status` (still Phase D per D-18).
- No Home Assistant tools (Phase C).
- No prompt v0.2 (carry-over; not blocking).
- No `homelab-tools` container (Phase D).
- No filesystem-write tools.
- No conversation-memory work (D-16).
- No Cloudflare exposure of the assistant (D-15).
- No change to `time_now` source or behaviour.
- No change to ingest cron schedule (still 02:30 daily).
- No change to embedder / reranker model identities (D-08 locked).

## Pre-flight checks (must all be true before B-0 starts)

These are read-only; running them does not commit Phase B.

| # | Check | Pass criterion | How |
|---|---|---|---|
| P-1 | Phase A closed | Closeout log present at `09_logs/2026-06-15_phaseA_closeout.md`; CURRENT_STATE, ROADMAP, AMAROLAB_HANDOFF all reference Phase B as current | `ls` + `grep -l 'Phase B' 04_ai_system/amarolab-v1/{CURRENT_STATE,ROADMAP,AMAROLAB_HANDOFF}.md` |
| P-2 | qwen2.5 Model entry still scoped to `["time_now"]` | `meta.toolIds == ["time_now"]` in `webui.db` | sqlite SELECT of model row |
| P-3 | Ingest service runnable | `bin/ingest --help` exits 0 from the venv | `/home/diego/homelab/ai-stack/ingest/venv/bin/python -m ingest.cli --help` |
| P-4 | Qdrant API key reachable from host | `curl -H "api-key: $KEY" http://127.0.0.1:6333/collections` returns 200 | inline curl |
| P-5 | Audit corpus source present | `find /home/diego/server-audit-2026-06-13 -name '*.md' | wc -l` ≥ 6 | inline find |
| P-6 | Embedder model already cached on host | `/srv/homelab/data/openwebui/cache/embedding/models/` contains `multilingual-e5-small` checkpoint | `ls` |
| P-7 | Reranker model already cached on host | same cache dir contains `bge-reranker-v2-m3` | `ls` |
| P-8 | Pre-flight backup of `webui.db` | `/tmp/amarolab-phaseB-backup/webui.db.pre-B` exists | `mkdir -p && cp` |
| P-9 | Pre-flight `tar` of `webui.db` + `amarolab-audit.log` for restore | `/tmp/amarolab-phaseB-backup/state.tar.gz` exists | `tar czf` |
| P-10 | The host `.env` carries `QDRANT_API_KEY` and `WEBUI_SECRET_KEY` | both present, mode 0600 | `stat` + `grep -c` |

P-3 must succeed because the Tool will use the same `Embedder` and
`Reranker` modules at runtime. If P-3 fails, fix the ingest
environment before Phase B starts.

## Gated decisions (user approval required before the named step)

| Gate | What | Step it gates | Why |
|---|---|---|---|
| **G-1** | Recreate the `openwebui` container with an additional read-only bind mount: `/home/diego/homelab/ai-stack/ingest:/opt/ingest:ro`. Per the homelab-wide safety rule, this is a container change. | **B-3** (mount the ingest tree) | The `rag_search` Tool imports `from ingest.embedder import Embedder` and `from ingest.reranker import Reranker`. These cannot be inlined into a Tool file (sentence-transformers + bge-reranker drag in transformers, torch, etc.). The cleanest path is the bind mount; alternative paths are documented in §"Alternatives to G-1" below |
| **G-2** | Update `meta.toolIds` on the qwen2.5 Model entry from `["time_now"]` to `["time_now","rag_search","audit_search"]`. | **B-7** (per-model scope update) | This is the canonical D-20 mechanism. Single `webui.db` UPDATE; reversible by reverting to the previous list |
| **G-3** | Permit the first end-to-end chat probe to run against the live `qwen2.5:7b-instruct` + the new tools. | **B-8** (validation) | The probe makes real calls; the audit log will gain real entries. Benign by design — same shape as Probe E in the Issue T analysis — but worth flagging |

No other irreversible action is required. Tool source can be
created and installed in `webui.db` via the same workflow as A.3
(`install_tool` → `POST /api/v1/tools/create`), which is fully
reversible by `DELETE /api/v1/tools/id/{id}/delete`.

## Step plan

Steps are numbered B-0..B-10. Each step has:
- **Action** — what is done.
- **Verification** — what must be true after.
- **Rollback** — how to undo.

Run sequentially. Do not start B-1 until B-0's verifications pass,
etc. Most steps are independently rollable back; the openwebui
container recreate in B-3 is the only step that touches a running
service.

### B-0 — Pre-flight (no state change)

**Action:** run all P-1..P-10 checks; take the two backups. Confirm
each pass criterion. Stop and report if any fail.

**Verification:**
- All P-1..P-10 checks PASS.
- `/tmp/amarolab-phaseB-backup/webui.db.pre-B` exists; size matches
  live `webui.db`.
- `/tmp/amarolab-phaseB-backup/state.tar.gz` exists.

**Rollback:** none needed; nothing has been modified.

### B-1 — Add `infra_audits` to `ingest/conf/corpora.yaml`

**Action:** append the corpus stanza per
[`05-implementation-roadmap.md`](05-implementation-roadmap.md) §Phase B:

```yaml
  - name: infra_audits
    type: fs
    path: /home/diego/server-audit-2026-06-13
    include:
      - "**/*.md"
    exclude:
      - "**/inspect-snapshots/**"
      - "**/*.json"
    enabled: true
```

Commit the YAML change to the homelab git repo (no push yet —
push happens after the corpus is populated and validated).

**Verification:**
- `yq '.corpora[] | select(.name == "infra_audits")'
  ai-stack/ingest/conf/corpora.yaml` returns the new entry.
- `git status` shows only `corpora.yaml` modified.

**Rollback:**
- `git checkout -- ai-stack/ingest/conf/corpora.yaml`.

### B-2 — Create the `infra_audits` Qdrant collection

**Action:** per
[`05-implementation-roadmap.md`](05-implementation-roadmap.md) §Phase B:

```bash
KEY=$(awk -F= '/^QDRANT__SERVICE__API_KEY=/ {print $2; exit}' \
      /home/diego/homelab/ai-stack/.env)
curl -X PUT -H "api-key: $KEY" -H "Content-Type: application/json" \
     "http://127.0.0.1:6333/collections/infra_audits" \
     -d '{"vectors":{"size":384,"distance":"Cosine"},"on_disk_payload":true}'
for f in collection source_kind source_rel; do
  curl -X PUT -H "api-key: $KEY" -H "Content-Type: application/json" \
       "http://127.0.0.1:6333/collections/infra_audits/index" \
       -d "{\"field_name\":\"$f\",\"field_schema\":\"keyword\"}"
done
```

Run the first sync:

```bash
/home/diego/homelab/ai-stack/ingest/bin/ingest sync \
    --collection infra_audits
```

Spot-check:

```bash
/home/diego/homelab/ai-stack/ingest/bin/ingest search \
    --collection infra_audits \
    --query "what was applied in Phase 0" --k 5
```

**Verification:**
- `GET /collections/infra_audits` returns 200; `points_count > 100`.
- Spot-check top-1 hit points at a Phase 0 application section.
- Embedder + reranker did not need a network re-download (cache
  hit confirmed in ingest logs).

**Rollback:**
- `bin/ingest drop --collection infra_audits --yes`.
- Then `curl -X DELETE` the Qdrant collection.

### B-3 — Mount the ingest tree into `openwebui` *(gated G-1)*

**Action:** **after explicit user approval**, recreate the
`openwebui` container with the read-only bind mount added. Per
[`05-implementation-roadmap.md`](05-implementation-roadmap.md)
§Phase D's `docker run` template, adapted to the current env vars:

```bash
KEY_QDRANT=$(awk -F= '/^QDRANT__SERVICE__API_KEY=/ {print $2; exit}' \
              /home/diego/homelab/ai-stack/.env)
KEY_WEBUI=$( awk -F= '/^WEBUI_SECRET_KEY=/ {print $2; exit}' \
              /home/diego/homelab/ai-stack/.env)

docker stop openwebui
docker rename openwebui openwebui_pre_phaseB_$(date +%Y%m%d%H%M%S)
docker run -d --name openwebui --restart unless-stopped \
  --network ai-local_default \
  -p 3000:8080 \
  -v /srv/homelab/data/openwebui:/app/backend/data \
  -v /home/diego/homelab/ai-stack/ingest:/opt/ingest:ro \
  -e ENV=prod -e PORT=8080 \
  -e OLLAMA_BASE_URL=http://ollama:11434 \
  -e QDRANT_URI=http://qdrant:6333 \
  -e QDRANT_API_KEY="$KEY_QDRANT" \
  -e VECTOR_DB=qdrant \
  -e WEBUI_SECRET_KEY="$KEY_WEBUI" \
  -e WEBUI_API_KEYS_ENABLED=true \
  -e AMAROLAB_AUDIT_LOG=/app/backend/data/amarolab-audit.log \
  -e USE_OLLAMA_DOCKER=false -e USE_CUDA_DOCKER=false -e USE_SLIM_DOCKER=false \
  -e OPENAI_API_BASE_URL= -e OPENAI_API_KEY= \
  -e SCARF_NO_ANALYTICS=true -e DO_NOT_TRACK=true -e ANONYMIZED_TELEMETRY=false \
  ghcr.io/open-webui/open-webui:main
# (existing networks the legacy container was on: re-attach if needed)
```

**Verification:**
- `docker inspect openwebui | jq '.[0].HostConfig.Mounts'` lists
  `/home/diego/homelab/ai-stack/ingest` → `/opt/ingest`, RO.
- `docker exec openwebui ls /opt/ingest/ingest` shows the module
  layout (`embedder.py`, `reranker.py`, `store.py`, …).
- `docker exec openwebui python3 -c "import sys; sys.path.insert(0,'/opt/ingest'); from ingest.embedder import Embedder; print(Embedder)"`
  prints a class reference — no import error.
- `time_now` Tool still loads and returns correct output (Probe E
  pattern; audit log delta +1).
- `webui.db` and `amarolab-audit.log` byte-identical to pre-B-3
  state (the bind mount on `/srv/homelab/data/openwebui` preserves
  these).

**Rollback:**
- `docker stop openwebui && docker rm openwebui`.
- `docker rename openwebui_pre_phaseB_<ts> openwebui`.
- `docker start openwebui`.
- Verify `webui.db` mtime unchanged and `time_now` still answers.

### B-4 — Author `tools/rag_search.py`

**Action:** create
`/home/diego/homelab/ai-stack/openwebui-tools/tools/rag_search.py`
following the `class Tools` shape from D-24 and the implementation
outline in [`03-tools.md`](03-tools.md) §"Tool 1 — rag_search".
Inline the audit helper from `lib/audit_helper.py` via the same
`@@AMAROLAB_INLINE:audit_helper@@` directive used by `time_now.py`
(D-26).

Key shape requirements (binding):
- `class Tools` with `__init__(self) -> None`.
- Method `rag_search(self, collection: Literal[…5 names…], query: str, k: int = 6) -> str`.
- Returns JSON-encoded string; docstring before the first `:param`
  describes the tool for the LLM.
- Lazy-init pattern for `_emb`, `_rer`, `_qdr` per the
  implementation outline.
- `Valves` model defines `max_per_minute` (default 30, ≤ 600 ge 1)
  and any tunable thresholds.
- Audit calls on every entry/exit, error path, and rate-limit
  refusal (D-26).
- Error codes: `rate_limited`, `bad_collection` (defensive, even
  though pydantic Literal already filters), `qdrant_unreachable`,
  `empty_collection`. See [`03-tools.md`](03-tools.md) failure-mode
  table.

**Verification:**
- `python3 -c "import ast, sys; ast.parse(open('rag_search.py').read())"`
  succeeds (no syntax errors).
- Local module-load smoke from inside the openwebui container:
  ```bash
  docker exec openwebui python3 - <<'PY'
  import sys; sys.path.insert(0,'/opt/ingest')
  import importlib.util as u
  spec = u.spec_from_file_location("rs","/srv/openwebui-tools/tools/rag_search.py")
  # (or copy into /tmp inside the container if /srv mount isn't available)
  PY
  ```
  loads without ImportError.

**Rollback:**
- `rm` the file.

### B-5 — Author `tools/audit_search.py`

**Action:** create
`/home/diego/homelab/ai-stack/openwebui-tools/tools/audit_search.py`
as the thin sugar over `rag_search(collection="infra_audits", …)`,
per [`03-tools.md`](03-tools.md) §"Tool 2 — audit_search".
Important: it is a **separate Tool file with its own `class Tools`
and its own inlined audit helper** (D-26: cross-Tool imports do
not work; the helper is duplicated per Tool).

`audit_search` must not import or call `rag_search` from a separate
Tool file at runtime — Tool modules are loaded in isolated
namespaces (D-26). The simplest in-spec path is:

- Copy the same dense + rerank pipeline body from `rag_search.py`
  into `audit_search.py`, hard-coding `collection="infra_audits"`
  (about ~30 LoC of duplication, acceptable per D-26's
  duplication-is-fine policy for v1).

**Verification:**
- Syntax parse succeeds.
- Loads in the openwebui container same as B-4.

**Rollback:**
- `rm` the file.

### B-6 — Install both Tools via the Open WebUI API

**Action:** use the same `bin/install_tool` helper that A.3 used to
install `time_now`. For each new Tool:

```bash
/home/diego/homelab/ai-stack/openwebui-tools/bin/install_tool \
    /home/diego/homelab/ai-stack/openwebui-tools/tools/rag_search.py
/home/diego/homelab/ai-stack/openwebui-tools/bin/install_tool \
    /home/diego/homelab/ai-stack/openwebui-tools/tools/audit_search.py
```

The helper mints a JWT from `WEBUI_SECRET_KEY` and POSTs the
inlined source to `/api/v1/tools/create` (or `/update` if the id
already exists). `webui.db` gains two new `tool` rows.

**Verification:**
- `GET /api/v1/tools/` lists `rag_search` and `audit_search`
  alongside `time_now`.
- `GET /api/v1/tools/id/rag_search` returns a single spec with
  the three params (`collection` enum, `query`, `k`) and the
  correct docstring fragment.
- `GET /api/v1/tools/id/audit_search` returns a single spec with
  `query` and `k`.
- `dump_tools` round-trip diff = clean (modulo trailing newline,
  same as A.3's V-8).

**Rollback:**
- `DELETE /api/v1/tools/id/rag_search/delete`.
- `DELETE /api/v1/tools/id/audit_search/delete`.

### B-7 — Update qwen2.5 Model entry `meta.toolIds` *(gated G-2)*

**Action:** **after explicit user approval**, fetch the qwen2.5
Model entry, mutate `meta.toolIds` from `["time_now"]` to
`["time_now","rag_search","audit_search"]`, POST the full record
back. Same GET → mutate → POST pattern used for A.4 v0/v0.1.

Preserve `meta.description`, `meta.capabilities`,
`params.system`, all other fields unchanged.

**Verification:**
- `GET /api/v1/models/model?id=qwen2.5:7b-instruct` → `meta.toolIds`
  is the three-element list.
- `params.system` length still 3 342 chars (v0.1 prompt unchanged).
- `meta.description` unchanged.
- `llama3:latest` and `llama3.2:latest` Model entries untouched
  (per D-20).

**Rollback:**
- Repeat the GET → mutate (set back to `["time_now"]`) → POST.
- Or restore `webui.db` from `/tmp/amarolab-phaseB-backup/webui.db.pre-B`
  (also reverts B-6).

### B-8 — End-to-end validation *(gated G-3)*

**Action:** run a validation harness that probes the three
qwen2.5-scoped Tools through `POST /api/chat/completions`. Encode
**the Issue T lesson**: every probe includes `tool_ids:["time_now","rag_search","audit_search"]`
in the request body (the validator's chat path mimics the
browser-UI path).

Probes:

| ID | Question | Expected `tool_calls` | Expected audit-log delta |
|---|---|---|---|
| W-1 | `¿qué hora es?` | `time_now` | +1 line, `tool=time_now`, `result_code=ok` |
| W-2 | `Find mosquitto configuration notes in the homelab docs.` | `rag_search` with `collection="homelab_docs"` | +1 line, `tool=rag_search`, `result_code=ok` |
| W-3 | `What was applied in Phase 0?` | `audit_search` (Phase B corpus) | +1 line, `tool=audit_search`, `result_code=ok` |
| W-4 | `Search guardian_cloud for recovery flow.` | `rag_search` with `collection="guardian_cloud"`; top-1 rerank score in the Phase 1.5 benchmark range | +1 line |
| W-5 | `Search myfreetour for tours.` | `rag_search` with `collection="myfreetour"`; tool returns `{"error":"empty_collection","code":"empty_collection"}` (D-22) | +1 line, `result_code="empty_collection"` |
| W-6 | `Please turn on the kitchen light.` | refusal naming Phase C (carry-over D-30) | no audit-log delta |

Reranker-benchmark reproduction (binding exit criterion):

| ID | Action | Pass criterion |
|---|---|---|
| W-7 | Re-run the Phase 1.5 reranker benchmark against `guardian_cloud` via the Tool path (i.e., feed the same query set to `rag_search(collection="guardian_cloud", query=…)`) | Top-6 ≥ 95 % matches the off-Tool benchmark within ±2 pp |

Browser-UI smoke (uses BX workaround per §3.2 of the JSON-parse
error analysis):

| ID | Action | Pass criterion |
|---|---|---|
| W-8 | In a browser tab over LAN/Tailnet, hard-refresh, wait for the connection indicator, ask `"What was applied in Phase 0?"`, confirm the rendered reply cites `audit_search` results with `[1] <source_rel>` footer | reply has real sources; audit-log shows the call; no `Unexpected token 'd'` toast |

**Verification:**
- All seven programmatic probes (W-1..W-7) PASS.
- W-8 PASSES via the documented workaround.
- Audit log gains exactly six new lines for W-1..W-6 (W-7's
  benchmark runs may add many more — counted separately).
- No `time_now` regression (W-1 still works).
- No leak to `llama3*` models (probe one of them with the same
  questions; expect refusal / generic answer without tool calls).

**Rollback:**
- B-7 reversal (`meta.toolIds` back to `["time_now"]`) hides the
  new Tools from chat.
- B-6 reversal (`DELETE` the two Tools) clears `webui.db`.
- B-3 reversal (rename legacy container back) removes the bind
  mount.
- B-2 reversal drops the corpus.
- B-1 reversal removes the corpora.yaml entry.

### B-9 — Documentation update + git commit

**Action:** write the Phase B applied log
`09_logs/2026-06-15_phaseB-knowledge-tools-applied.md` (or
appropriate date) and update the live state files:
- `CURRENT_STATE.md` — promote `rag_search` + `audit_search` to
  "shipped"; bump corpus count to 5; mark Phase B as the latest
  completed milestone; note Phase C as next current.
- `ROADMAP.md` — move Phase B from "Current phase" to "Completed
  phases"; promote Phase C to current.
- `AMAROLAB_HANDOFF.md` — update "Current phase" pointer.

Commit and push to GitHub (sanitised — no secrets).

**Verification:**
- `git diff --stat` shows only docs + the new Tool source files +
  `corpora.yaml`.
- `git push` succeeds; GitHub view shows the new Phase B log
  rendered.

**Rollback:**
- `git revert` the doc-update commit if needed; the live state
  remains correct.

### B-10 — Hand-off to Phase C

**Action:** confirm that Phase B's exit criterion is met (W-7 top-6
≥ 95 % on guardian_cloud). Note Phase C's first prerequisite (B-07,
HA Long-Lived Access Token) in the closeout summary so the next
session can pick up.

**Verification:**
- B-9 docs reflect "Phase C — Home Assistant" as the new current
  phase.
- B-07 carries over into Phase C planning.

**Rollback:** none — Phase B is complete at this point.

## Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Embedder / reranker first-load times exhaust openwebui Tool-call timeout | Med | Med — first `rag_search` call may time out | Lazy-init pattern keeps cold cost on the first user call only; warm up by curl-calling `rag_search` once after B-3 succeeds, before W-1 |
| Bind-mount adds module-import surface qwen2.5 doesn't expect | Low | Low — Open WebUI just `exec`s the Tool source | Tool source is repo-tracked; reversible by renaming legacy container back |
| `infra_audits` corpus pulls in transient files | Low | Low — only six `.md` matched in pre-flight check | Exclude `**/inspect-snapshots/**` and `**/*.json` per spec |
| qwen2.5 over-routes between `rag_search` and `audit_search` | Med | Low — prompt-quality issue, not correctness | Validate both via W-2 and W-3; v0.2 prompt iteration can tighten the routing examples |
| User opens a browser chat before WebSocket connects (BX) | Med | Low — toast error, no state damage | Document workaround in B-8 validation (W-8 explicit step) |
| Phase 1.5 reranker benchmark drifts due to module-load differences inside the container | Low | Med — could miss the 95 % exit bar | Compare ±2 pp tolerance; if outside, hold Phase B open and root-cause; do not push exit to "close enough" |

## Alternatives to G-1 (bind-mount)

For completeness, the two paths considered for getting `Embedder`
and `Reranker` into the Tool runtime:

| Path | Action | Pros | Cons |
|---|---|---|---|
| **A. Bind-mount the ingest tree** (chosen) | `-v /home/diego/homelab/ai-stack/ingest:/opt/ingest:ro` + `sys.path.insert(0,"/opt/ingest")` at the top of `rag_search.py` | Zero duplication; ingest cron and Tool runtime always see the same code | Requires openwebui container recreate (gate G-1) |
| **B. Inline a slimmed embedder + reranker into the Tool file** | Copy the minimal classes into `rag_search.py` with no `from ingest.*` imports | No container recreate | Duplicates ~200 LoC; cron and Tool can drift; sentence-transformers code is not trivially slimmable |
| **C. HTTP call to a side-car container** | Build a small FastAPI wrapper around `Embedder` + `Reranker` + `QdrantClient`; the Tool becomes an HTTP client | Modeled on the Phase D `homelab-tools` pattern | New container, more complexity, more surface |

A is the chosen path per
[`05-implementation-roadmap.md`](05-implementation-roadmap.md) §Phase D
Option 1 and the sub-project ROADMAP entry. B is documented in
case G-1 is denied; in that case Phase B would need a design log
explaining the inline approach before B-4 / B-5.

## Safety rules carry-over (re-stated for the Phase B executor)

From [`AMAROLAB_HANDOFF.md`](AMAROLAB_HANDOFF.md):

- Guardian Cloud RAG is read-only over its docs; never call its
  backend.
- Home Assistant is out of scope until Phase C.
- The LLM is adversarial input; Tool argument allowlists are
  file-level constants; no `eval`, no `subprocess`, no
  path-from-arg, no shell building from arguments.
- No new Open WebUI Tools without explicit user approval per
  sub-phase (each Tool install is a gated decision).
- Default model in Open WebUI must not be changed.
- Container changes are gated (G-1 here is the only Phase B
  container change).
- Secrets stay in `/home/diego/homelab/ai-stack/.env`; never paste
  values into design docs or status files.
- Audit-log path is fixed:
  `/srv/homelab/data/openwebui/amarolab-audit.log`.

## Cross-references

- Phase A closeout:
  [`../../09_logs/2026-06-15_phaseA_closeout.md`](../../09_logs/2026-06-15_phaseA_closeout.md)
- Issue T resolution:
  [`../../09_logs/2026-06-15_issueT_root_cause_analysis.md`](../../09_logs/2026-06-15_issueT_root_cause_analysis.md)
- BX (UI WebSocket race) workaround:
  [`../../09_logs/2026-06-15_openwebui_json_parse_error_analysis.md`](../../09_logs/2026-06-15_openwebui_json_parse_error_analysis.md)
- Sub-project live state: [`CURRENT_STATE.md`](CURRENT_STATE.md)
- Sub-project status overlay: [`ROADMAP.md`](ROADMAP.md)
- Sub-project handoff: [`AMAROLAB_HANDOFF.md`](AMAROLAB_HANDOFF.md)
- Design package (immutable):
  [`01-current-state-review.md`](01-current-state-review.md),
  [`02-target-architecture.md`](02-target-architecture.md),
  [`03-tools.md`](03-tools.md),
  [`04-security-and-permissions.md`](04-security-and-permissions.md),
  [`05-implementation-roadmap.md`](05-implementation-roadmap.md)
- Open WebUI 0.8.10 runtime contract:
  [`../../FUNCTIONS_COMPATIBILITY_REPORT.md`](../../FUNCTIONS_COMPATIBILITY_REPORT.md)
- Phase A.3 applied log (canonical Tool install pattern):
  [`../../09_logs/2026-06-15_phaseA3-tool-canary-applied.md`](../../09_logs/2026-06-15_phaseA3-tool-canary-applied.md)
- Ingest service:
  `/home/diego/homelab/ai-stack/ingest/` (Phase 1, Phase 1.5)
- Tool source tree:
  `/home/diego/homelab/ai-stack/openwebui-tools/` (Phase A.3)
- Audit log:
  `/srv/homelab/data/openwebui/amarolab-audit.log`
- Audit corpus source:
  `/home/diego/server-audit-2026-06-13/`

## Status at the time of this draft

- Phase B work: **not started**.
- Tool source files: not written.
- `infra_audits` Qdrant collection: not created.
- `corpora.yaml`: unchanged.
- `webui.db`: unchanged.
- openwebui container: original mounts only (no `/opt/ingest`).
- Gates G-1, G-2, G-3: **awaiting user approval before B-3 starts**.

This plan is the next-action map. The Phase B applied log will be
written at B-9 once execution is approved and runs.
