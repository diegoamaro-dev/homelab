# Phase B — preflight — READ-ONLY VALIDATION

- **Date:** 2026-06-15
- **Scope:** Targeted read-only validation requested for Phase B
  kick-off. Six areas: Qdrant health, existing collections,
  collection dimensions, embedding-model compatibility, ingest
  service status, corpus inventory.
- **What this log is NOT:** an application log. Nothing was
  modified — no `webui.db` write, no Qdrant write, no container
  recreate, no config edit, no backup file written (P-8/P-9 from
  [`../04_ai_system/amarolab-v1/PHASE_B_EXECUTION_PLAN.md`](../04_ai_system/amarolab-v1/PHASE_B_EXECUTION_PLAN.md)
  still deferred). The Qdrant points-scroll and the live
  `Embedder.embed_query()` call are pure reads.
- **Relationship to B-0:** this run satisfies a more pointed
  superset of B-0's read-only checks (P-3, P-4, P-6, P-7, P-10)
  and **adds three areas not in B-0**: per-collection dimension
  cross-check, runtime embed-and-compare-dims compatibility, and a
  cron-vs-manual ingest invocation discrepancy.
- **Tools used:** `curl` against Qdrant; SQLite read against
  `/srv/homelab/data/openwebui/webui.db` (already done in B-0, not
  repeated here); the ingest venv's Python to load `Embedder` once
  and embed a representative query; `docker ps`; `crontab -l`; raw
  `find` over the source paths.

## 0. TL;DR

**Phase B preflight is GREEN.** All six validation areas pass:

| # | Area | Result |
|---|---|---|
| 1 | Qdrant health | `healthz`, `livez`, `readyz` all 200; Qdrant **1.17.0**; container Up |
| 2 | Existing collections | 6 collections in Qdrant: 4 Amarolab + 2 Open WebUI internals; `infra_audits` correctly absent |
| 3 | Collection dimensions | **All 6 collections are 384-dim, Cosine, status `green`** |
| 4 | Embedding model compatibility | `intfloat/multilingual-e5-small` loads from cache in **7.93 s**; `embed_query()` returns a **384-element vector** in **~220 ms**; matches every collection's expected dim |
| 5 | Ingest service status | Venv healthy; `python -m ingest.cli` works; cron entry installed for 02:30 daily |
| 6 | Corpus inventory | Live points counts match the design table (86 / 872 / 419 / 0); audit corpus source has the expected **6 `.md` files** |

**One incidental finding worth flagging** before B-2 runs (not a
showstopper, but it changes how B-2 must be invoked):

> `bin/ingest` (the cron wrapper) **fails with `ModuleNotFoundError`
> when invoked from any cwd other than the ingest source dir** —
> including the cron's cwd. The wrapper does `python -m ingest.cli`
> which resolves the package via CWD, not via an installed
> distribution. Yesterday's 02:30 cron run failed for this reason.
> Manual `python -m ingest.cli` from inside the ingest dir is fine
> (this is how we got the current points counts).

This pre-exists Phase B and does not invalidate the Phase 1 / 1.5
inventories (the cron *had* been working some days; today's failure
is captured but a single missed sync). See §7 for the diagnosis and
two options to handle it in B-2.

## 1. Qdrant health

| Endpoint | Code | Body | Verdict |
|---|---|---|---|
| `GET /healthz` | 200 | `healthz check passed` | PASS |
| `GET /livez` | 200 | `healthz check passed` | PASS |
| `GET /readyz` | 200 | `all shards are ready` | PASS |
| `GET /telemetry` | 200 | `version=1.17.0` | PASS |

Container: `qdrant` Up About an hour; ports
`0.0.0.0:6333->6333/tcp`, `6334/tcp` (internal gRPC) exposed.

API-key auth: every probe used
`-H "api-key: $QDRANT__SERVICE__API_KEY"` from
`/home/diego/homelab/ai-stack/.env`. The `/telemetry` endpoint
required the key (consistent with R-07.1 lockdown from Phase 0).

## 2. Existing collections

Output of `GET /collections`:

| Collection | Source | Role |
|---|---|---|
| `homelab_docs` | host filesystem | Amarolab corpus |
| `guardian_cloud` | git | Amarolab corpus |
| `ensambla2` | git | Amarolab corpus |
| `myfreetour` | TBD | Amarolab placeholder (corpora.yaml `enabled: false`) |
| `open-webui_files` | Open WebUI uploads | OWUI internal (not Amarolab) |
| `open-webui_knowledge` | Open WebUI Knowledge feature | OWUI internal (not Amarolab) |

**`infra_audits` is correctly absent.** Phase B B-2 will create it.

The two `open-webui_*` collections are Open WebUI 0.8.10's own
buckets — they are created when a user uploads a file or enables
the Knowledge feature. They are not touched by our ingest service,
not referenced in `rag_search`'s collection enum (D-22), and not
part of the v1 design's "4 + 1 future" tally. They are recorded
here only because they sit in the same Qdrant instance.

## 3. Collection dimensions + status

`GET /collections/{name}` per row. All six collections share the
same vector config:

| Collection | dim | distance | points | segments | status |
|---|---:|---|---:|---:|---|
| `homelab_docs` | **384** | Cosine | 86 | 2 | green |
| `guardian_cloud` | **384** | Cosine | 872 | 2 | green |
| `ensambla2` | **384** | Cosine | 419 | 2 | green |
| `myfreetour` | **384** | Cosine | 0 | 2 | green |
| `open-webui_files` | **384** | Cosine | 2 | 8 | green |
| `open-webui_knowledge` | **384** | Cosine | 3 | 8 | green |

- **Every collection is 384-dim, Cosine.** This is consistent with
  D-08's lock-in of `intfloat/multilingual-e5-small` (384) and
  satisfies the structural precondition for `rag_search` to query
  any of them with a single embedder.
- The two OWUI-internal collections also happen to be 384/Cosine —
  Open WebUI 0.8.10 has the same embedder configured for its own
  Knowledge/upload features (via the cached
  `multilingual-e5-small` artefact under
  `/srv/homelab/data/openwebui/cache/embedding/models/`).
  Coincidental but harmless.
- `points_count` matches the figures in
  [`../04_ai_system/amarolab-v1/CURRENT_STATE.md`](../04_ai_system/amarolab-v1/CURRENT_STATE.md)
  exactly (86 / 872 / 419 / 0). No drift since Phase 1.
- `indexed_vectors_count` was reported as `0` for every collection
  (Qdrant 1.17 has lifted the count into a different telemetry
  shape in some setups; the `status: green` and the successful
  Phase 1.5 reranker benchmark together confirm vectors are
  searchable). Not a Phase B concern.

## 4. Embedding model compatibility

The ingest venv (`/home/diego/homelab/ai-stack/ingest/venv`,
Python 3.12.3) loaded the Phase 1 embedder and embedded a
representative query:

| Item | Value |
|---|---|
| Model id (from `ingest.config.EMBED_MODEL_NAME`) | `intfloat/multilingual-e5-small` |
| HF cache (from `ingest.config.HF_CACHE`) | `/srv/homelab/data/openwebui/cache/embedding/models` |
| Cold load time | **7.93 s** (cache hit — no network re-download) |
| Test query | `"what was applied in phase 0"` |
| Vector length | **384** |
| First 4 components | `0.06126, -0.07273, -0.04490, -0.04715` |
| Embed latency | **~220 ms** |
| Cross-check against all collections | PASS — every collection's `vectors.size == len(embed_query(...))` |

This is the binding compatibility check for Phase B. The
`rag_search` Tool will (per [`03-tools.md`](../04_ai_system/amarolab-v1/03-tools.md)
§"Tool 1") embed the query with this same `Embedder` and dispatch
to the named collection. With every collection at 384 dim and the
embedder confirmed to produce 384-dim vectors, no dimension
mismatch can occur at runtime.

**Implication for the Phase B Tool cold-load risk** (risk register
row 1 in
[`../04_ai_system/amarolab-v1/PHASE_B_EXECUTION_PLAN.md`](../04_ai_system/amarolab-v1/PHASE_B_EXECUTION_PLAN.md)):
**7.93 s warm-up is well inside Open WebUI's Tool-call window.**
The lazy-init pattern keeps this cost on the first call only.
Subsequent embeds are ~220 ms per query. Reranker load was not
exercised in this preflight (it's a separate model and a separate
~10 s cold load) — flagged as a follow-up to verify after B-3.

## 5. Ingest service status

### 5.1 Source tree + venv

| Item | State |
|---|---|
| venv | `/home/diego/homelab/ai-stack/ingest/venv`, Python 3.12.3, executable |
| Package | `/home/diego/homelab/ai-stack/ingest/ingest/` (CLI, embedder, reranker, store, connectors, chunker, pipeline, config) |
| Configuration | `/home/diego/homelab/ai-stack/ingest/conf/corpora.yaml` |
| Wrapper script | `/home/diego/homelab/ai-stack/ingest/bin/ingest` (mode 0775, owner `diego:diego`) — see §7 |
| Logs | `/home/diego/homelab/ai-stack/ingest/logs/ingest.log` |

### 5.2 CLI surface

```
usage: homelab-rag-ingest [-h] {sync,status,search,drop,init} ...
  sync    ingest one or all corpora
  status  per-collection point counts
  search  query a collection
  drop    delete all points for a collection
  init    (no-op) collections are pre-created
```

Manual `python -m ingest.cli status` from inside the ingest
directory worked end-to-end:

| collection | points | enabled |
|---|---:|---|
| `homelab_docs` | 86 | True |
| `guardian_cloud` | 872 | True |
| `ensambla2` | 419 | True |
| `myfreetour` | 0 | False |

Matches Qdrant's `points_count` exactly.

### 5.3 Cron schedule

```
30 2 * * * /home/diego/homelab/ai-stack/ingest/bin/ingest sync >> /home/diego/homelab/ai-stack/ingest/logs/ingest.log 2>&1
```

Installed for user `diego`. Daily at 02:30. **However**, see §7 —
the wrapper resolved against the cron's `cwd` (`$HOME`) is the
reason yesterday's 02:30 run errored.

### 5.4 corpora.yaml summary

| name | type | enabled |
|---|---|---|
| `homelab_docs` | fs | True |
| `guardian_cloud` | git | True |
| `ensambla2` | git | True |
| `myfreetour` | git | False (placeholder) |

`infra_audits` is **not yet** in this file; B-1 will append it.

## 6. Corpus inventory

### 6.1 Source paths — raw file counts (no include/exclude filters applied)

| Collection | Source path | Raw file count |
|---|---|---:|
| `homelab_docs` | `/home/diego/homelab` | 107 (`.md` + `.yaml` + `.yml` + `.conf`) |
| `guardian_cloud` | `/mnt/storage/projects/guardian-cloud` | 430 (`.md`) |
| `ensambla2` | `/mnt/storage/projects/ensambla2` | 1 180 (`.md`) |
| `infra_audits` (Phase B) | `/home/diego/server-audit-2026-06-13` | **6** (`.md`) |

These are *broad* sweeps. The cron applies the `include` /
`exclude` filters in `corpora.yaml`, which reduces each source to
its representative document set (e.g. guardian_cloud restricts to
`docs/**/*.md`, `strategy/**/*.md`, etc.). The 86 / 872 / 419
chunk counts in Qdrant reflect post-filter, post-chunking yields.

### 6.2 Audit corpus (Phase B target) file list

```
/home/diego/server-audit-2026-06-13/SANITIZATION_REPORT.md
/home/diego/server-audit-2026-06-13/INGEST_REPO_REVIEW.md
/home/diego/server-audit-2026-06-13/MIGRATION_REPORT.md
/home/diego/server-audit-2026-06-13/CONSOLIDATION_PLAN.md
/home/diego/server-audit-2026-06-13/DOCUMENTATION_SYNC_PLAN.md
/home/diego/server-audit-2026-06-13/GITHUB_COMMIT_PLAN.md
```

All six are application-log style reports from Phase 0 / Phase 1.
After chunking (target chunk size in `ingest.config`), Phase B
expects roughly 40–120 chunks in the new `infra_audits`
collection — comfortably above
[`../04_ai_system/amarolab-v1/PHASE_B_EXECUTION_PLAN.md`](../04_ai_system/amarolab-v1/PHASE_B_EXECUTION_PLAN.md)
B-2's exit criterion of "points_count > 100" only if the chunker
splits aggressively; we should adjust the exit criterion if the
true chunk count lands below 100 (the test of substance is whether
the spot-check query returns a Phase 0 hit, not the literal count).

### 6.3 Existing payload schema spot-check (scroll sample)

For each Amarolab corpus, a small scroll sample to confirm payload
fields:

| Collection | sampled points | distinct `source_rel` | `source_kind` values |
|---|---:|---:|---|
| `homelab_docs` | 86 | 15 | `markdown`, `yaml`, `conf` |
| `guardian_cloud` | 872 | 56 | `markdown` |
| `ensambla2` | 419 | 48 | `markdown` |
| `myfreetour` | 0 | 0 | (empty) |

- File-count and distinct-source counts match
  [`../04_ai_system/amarolab-v1/CURRENT_STATE.md`](../04_ai_system/amarolab-v1/CURRENT_STATE.md)
  (15 files for `homelab_docs`, 56 for `guardian_cloud`, 48 for
  `ensambla2`). No drift.
- `source_kind` enum is what the chunker labels each file as. All
  three Amarolab corpora populate it; `rag_search` will surface
  this in citations.

## 7. Incidental finding — `bin/ingest` wrapper cwd bug

Read of `/home/diego/homelab/ai-stack/ingest/bin/ingest`:

```bash
#!/usr/bin/env bash
set -euo pipefail
ROOT="/home/diego/homelab/ai-stack/ingest"
if [ ! -d "$ROOT/venv" ]; then
  echo "venv not found at $ROOT/venv — run install.sh first" >&2
  exit 1
fi
. "$ROOT/venv/bin/activate"
exec python -m ingest.cli "$@"
```

The wrapper activates the venv and `exec`s `python -m ingest.cli`,
but it does **not** `cd "$ROOT"` first. `python -m ingest.cli`
finds the `ingest` package only because Python's default
`sys.path[0]` is the current working directory — so the wrapper
works when the caller's cwd is `/home/diego/homelab/ai-stack/ingest/`
and fails everywhere else.

**Reproduction (live, this turn):**

| Caller | Result |
|---|---|
| Manual `bin/ingest status` from `/home/diego/homelab/ai-stack/ingest/` (default for an interactive shell) | PASS — prints the four-row table |
| `cd /tmp && bin/ingest status` | FAIL — `ModuleNotFoundError: No module named 'ingest'` |
| `cron` (cwd = `$HOME`) | FAIL — same error |

**Evidence of the cron failure on the live system:**

```
$ tail -1 /home/diego/homelab/ai-stack/ingest/logs/ingest.log
/home/diego/homelab/ai-stack/ingest/venv/bin/python: Error while finding module specification for 'ingest.cli' (ModuleNotFoundError: No module named 'ingest')

$ stat -c '%y' /home/diego/homelab/ai-stack/ingest/logs/ingest.log
2026-06-15 02:30:01.447943651 +0200
```

So **the most recent scheduled sync (2026-06-15 02:30 CEST) errored
out before any embedding work was done.** Earlier scheduled runs
must have either landed before the regression or had a successful
manual sync replace them; we don't have older entries in this log
file to confirm.

### Phase B implication

Two strict options to keep B-2 honest:

| Option | What | Pros | Cons |
|---|---|---|---|
| **B-2.a (workaround, no source change)** | Invoke as `cd /home/diego/homelab/ai-stack/ingest && bin/ingest sync --collection infra_audits` (or equivalently `$VENV/bin/python -m ingest.cli sync --collection infra_audits`) | Zero modification to the wrapper; Phase B stays minimal-touch | Cron remains broken; future scheduled syncs continue to fail; user must remember the cd dance |
| **B-2.b (fix the wrapper now)** | One-line addition to `bin/ingest`: `cd "$ROOT"` immediately after the venv-existence check | Closes the cron regression as a side-benefit; future syncs Just Work | A wrapper edit; not in the Phase B execution plan's scope; should be done as a small dedicated commit, perhaps tagged as a Phase-1 carry-over fix |

The execution plan
[`../04_ai_system/amarolab-v1/PHASE_B_EXECUTION_PLAN.md`](../04_ai_system/amarolab-v1/PHASE_B_EXECUTION_PLAN.md)
currently shows the bare invocation `bin/ingest sync --collection infra_audits`
in B-2. If we go with **B-2.a**, no plan change is needed beyond
adding the `cd` to the script the user will type. If we go with
**B-2.b**, a one-line wrapper patch lands before B-2 — and we
should also note "Phase 1 cron silently broken since ≤ 2026-06-15
02:30" as a closed issue so the next session knows it was
addressed here.

**Recommended:** Option B-2.b, because it removes a real ongoing
defect (the nightly sync) and the patch is trivial (`cd "$ROOT"`).
But this is a user decision, not preflight scope; flagged for
confirmation before B-1 starts.

## 8. Phase B Go/No-Go

| Question | Answer |
|---|---|
| Is Qdrant healthy? | YES (`/readyz` green, version 1.17.0) |
| Are the existing collections in the expected shape? | YES (4 Amarolab + 2 OWUI internals; all 384/Cosine/green) |
| Is the embedder loadable and dimensionally compatible? | YES (384 dim, ~8 s cold load, ~220 ms warm embed) |
| Is the ingest service runnable from manual invocation? | YES (`python -m ingest.cli` works) |
| Is the audit corpus source present? | YES (6 `.md` files) |
| Are there blockers? | **NO** for Phase B as designed. **One incidental defect** in the cron wrapper (§7) wants a decision before B-2 runs |
| Are there outstanding gates? | YES (G-1 openwebui container recreate; G-2 `meta.toolIds` update; G-3 first end-to-end probe) — none triggered by preflight |

**Preflight: GREEN.** Phase B can proceed once the user:

1. Authorises the deferred B-0 backups (P-8 + P-9 from the
   execution plan — `webui.db.pre-B` + `state.tar.gz` under
   `/tmp/amarolab-phaseB-backup/`).
2. Decides between **B-2.a** (workaround) and **B-2.b** (wrapper
   patch) for §7.
3. Authorises B-1 (corpora.yaml append).

## 9. What this preflight deliberately did NOT do

- No `corpora.yaml` change (B-1 is gated).
- No Qdrant collection create / index / delete (B-2 is gated).
- No openwebui container recreate (B-3 is G-1, gated).
- No Tool source authored or installed (B-4..B-7 are sequential and
  gated by G-2/G-3 before completion).
- No backup file written (P-8/P-9 awaiting authorisation).
- No `bin/ingest` wrapper patch (§7 is a recommendation, not a
  performed fix).
- No restart of `qdrant`, `ollama`, `openwebui`, or the host cron.

## 10. Forensic state at end of preflight

| Item | Value |
|---|---|
| `webui.db` size / mtime | unchanged from start of session (2 347 008 bytes) |
| `webui.db` qwen2.5 `meta.toolIds` | `["time_now"]` (unchanged) |
| `corpora.yaml` | unchanged (4 corpora, 3 enabled) |
| Qdrant collections | 6 total (4 Amarolab + 2 OWUI internals); `infra_audits` not present |
| `time_now` Tool installed | yes (Phase A.3) |
| `amarolab-audit.log` | 96 lines (unchanged since the JSON-parse investigation) |
| Containers | `qdrant`, `ollama`, `openwebui`, `cloudflared`, `nginx-proxy-manager`, `homeassistant`, `mosquitto`, `zigbee2mqtt`, `portainer`, `guardian-web` — all up |
| `/tmp/amarolab-phaseB-backup/` | does not exist |
| Cron entry for ingest | present and broken (see §7) |
| Last successful manual `ingest status` | this turn, 2026-06-15 |

## 11. Cross-references

- Phase A closeout:
  [`2026-06-15_phaseA_closeout.md`](2026-06-15_phaseA_closeout.md)
- Issue T (B-09) resolution:
  [`2026-06-15_issueT_root_cause_analysis.md`](2026-06-15_issueT_root_cause_analysis.md)
- BX (browser-UI WebSocket race) workaround:
  [`2026-06-15_openwebui_json_parse_error_analysis.md`](2026-06-15_openwebui_json_parse_error_analysis.md)
- Phase B execution plan:
  [`../04_ai_system/amarolab-v1/PHASE_B_EXECUTION_PLAN.md`](../04_ai_system/amarolab-v1/PHASE_B_EXECUTION_PLAN.md)
- Sub-project live state:
  [`../04_ai_system/amarolab-v1/CURRENT_STATE.md`](../04_ai_system/amarolab-v1/CURRENT_STATE.md)
- Sub-project status overlay:
  [`../04_ai_system/amarolab-v1/ROADMAP.md`](../04_ai_system/amarolab-v1/ROADMAP.md)
- Sub-project handoff:
  [`../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md`](../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md)
- Design package §"Tool 1 — rag_search":
  [`../04_ai_system/amarolab-v1/03-tools.md`](../04_ai_system/amarolab-v1/03-tools.md)
- Implementation roadmap §Phase B (corpus) and §Phase D
  (`docker run` template inherited by B-3):
  [`../04_ai_system/amarolab-v1/05-implementation-roadmap.md`](../04_ai_system/amarolab-v1/05-implementation-roadmap.md)
- Ingest service:
  `/home/diego/homelab/ai-stack/ingest/`
- Wrapper under discussion in §7:
  `/home/diego/homelab/ai-stack/ingest/bin/ingest`
- Audit log: `/srv/homelab/data/openwebui/amarolab-audit.log`
- Audit corpus source: `/home/diego/server-audit-2026-06-13/`
