# Phase 1 — RAG Foundation — APPLIED

- **Date applied:** 2026-06-13 / 2026-06-14
- **Phase 0 prerequisites:** all five complete (R-12, R-04, R-07 key,
  R-05, R-06).
- **Scope of this phase:** ingestion service + 3 of 4 corpora populated
  in Qdrant. HA Assist integration and voice intentionally deferred.

## Decisions made (from the user)

| Knob | Value |
|------|-------|
| Embedding model | `intfloat/multilingual-e5-small` (384 dim, 100+ languages) |
| Primary LLM | `qwen2.5:7b-instruct` (not yet pulled — for Phase 4) |
| Secondary LLM | `llama3.1:8b-instruct` (not yet pulled — for Phase 4) |
| Voice | deferred |
| MyFreeTour | held pending source path |

## What now exists on the host

```
/home/diego/homelab/ai-stack/ingest/
├── README.md
├── bin/ingest                    # CLI wrapper
├── conf/corpora.yaml             # 4 corpora defined (myfreetour disabled)
├── install.sh                    # idempotent venv + deps installer
├── requirements.txt
├── ingest/                       # Python package
│   ├── cli.py                    # argparse: sync, status, search, drop, init
│   ├── config.py                 # corpus + runtime config + .env loader
│   ├── chunker.py                # markdown-aware + recursive splitter
│   ├── connectors/{fs,git}.py    # file walker + optional git pull
│   ├── embedder.py               # multilingual-e5-small wrapper
│   ├── pipeline.py               # per-corpus orchestration
│   └── store.py                  # Qdrant client wrapper
├── logs/                         # cron output lands here (empty until 02:30)
└── venv/                         # ~1.4 GB venv (torch CPU + sentence-transformers + qdrant-client + langchain-text-splitters)
```

Plus:

- Four Qdrant collections (`homelab_docs`, `guardian_cloud`, `ensambla2`,
  `myfreetour`) at 384-dim cosine, payload indexes on `collection`,
  `source_kind`, `source_rel`.
- Embedding model cached at
  `/srv/homelab/data/openwebui/cache/embedding/models/` (shared with
  openwebui).
- User crontab entry at 02:30 daily, logging to
  `/home/diego/homelab/ai-stack/ingest/logs/ingest.log`.

## Ingest results (first full sync, 2026-06-14)

| Collection | Source root | Files seen | Chunks upserted | Elapsed |
|------------|-------------|-----------:|----------------:|--------:|
| `homelab_docs` | `/home/diego/homelab` | 15 | 86 | 1.1 s¹ |
| `guardian_cloud` | `/mnt/storage/projects/guardian-cloud` | 56 | 872 | 14.5 s |
| `ensambla2` | `/mnt/storage/projects/ensambla2` | 48 | 419 | 10.5 s |
| `myfreetour` | TBD | — | — | (disabled) |
| **Total** | | **119** | **1 377** | |

¹ Wall-clock for the homelab_docs run was ~29 s including the one-time
download of `multilingual-e5-small` (~120 MB) and venv warm-up.

Notes from the run:

- The `guardian_cloud` git pull picked up a new file
  (`docs/future/NATIVE_AUDIO_SPIKE.md`) — connector works.
- The `ensambla2` working tree was dirty (1 338 changed files); the git
  connector correctly skipped the pull and proceeded with the on-disk
  state (local edits win). No silent failure.
- One bug found and fixed during the dry-run gate: `fnmatch.fnmatch`
  doesn't treat `**` as a recursive-glob marker, so `**/*.md` was
  missing top-level files. The matcher in `connectors/fs.py` now also
  tries the pattern with the leading `**/` stripped. Test case:
  homelab_docs's `README.md` is now indexed.

## Retrieval validation (k=3 per query)

Sample of the queries that were run after each ingest. All top-1
results were the correct document. Scores cluster between 0.81 and 0.89
for relevant hits.

### `homelab_docs`

| Query (lang) | Top-1 source | Score |
|--------------|--------------|-------|
| `"cómo se configura mosquitto"` (es) | `03_services/zigbee2mqtt_setup.md` | 0.8872 |
| `"storage and samba setup"` (en) | `03_services/samba_setup.md` | 0.8890 |
| `"tailscale remote access"` (en) | `01_architecture/remote-access-tailscale.md` | 0.8432 |
| `"zigbee dongle"` (en) | `03_services/zigbee2mqtt_setup.md` | 0.8472 |

### `guardian_cloud`

| Query | Top-1 source | Score |
|-------|--------------|-------|
| `"rebuild plan and architecture"` | `docs/PLAN.md` | 0.8128 |
| `"mobile app structure"` | `docs/ARCHITECTURE.md` (App móvil §) | 0.8368 |
| `"deployment workflow"` | `playbook/WORKFLOW.md` | 0.8455 |

### `ensambla2`

| Query | Top-1 source | Score |
|-------|--------------|-------|
| `"authentication flow"` | `AUTH_SYSTEM.md` | 0.8733 |
| `"multitenancy"` | `ADMIN_PANEL.md` (Multitenancy §) | 0.8644 |
| `"RBAC permissions model"` | `PERMISSIONS_RBAC.md` | 0.8830 |

Cross-language retrieval works: Spanish queries successfully match
English content and vice versa, confirming the choice of
`multilingual-e5-small` over `all-MiniLM-L6-v2`.

## Scheduling

User crontab entry (no sudo required because everything reads/writes
files diego owns):

```
30 2 * * * /home/diego/homelab/ai-stack/ingest/bin/ingest sync \
   >> /home/diego/homelab/ai-stack/ingest/logs/ingest.log 2>&1
```

Runs 30 minutes before the existing 03:00 restic backup so the new
vector state lands in that night's snapshot.

The cron-installed sync uses the **incremental** path: each file's per-
chunk `content_sha` is compared against the value stored in Qdrant; only
changed/new chunks get re-embedded. Expected nightly runtime: <30 s
unless the corpora churn heavily.

## What is NOT yet wired

- **Open WebUI Tools** to call `rag_search` — Phase 4.
- **HA Assist Extended OpenAI Conversation** integration — Phase 5.
- **Voice (Wyoming Whisper/Piper)** — deferred indefinitely per user.
- **MyFreeTour corpus** — placeholder in `corpora.yaml`, `enabled: false`.
  When the source location is known: flip the flag, set the `path`, then
  `./bin/ingest sync --collection myfreetour`. The Qdrant collection
  already exists and is empty.
- **`qwen2.5:7b-instruct` and `llama3.1:8b-instruct`** are not yet
  pulled into Ollama. The current `llama3:8b` / `llama3.2:3b` / `phi3`
  models remain. Phase 3 work, not Phase 1.

## Operational notes (for the next session)

- The Qdrant client warns `Api key is used with an insecure connection.`
  every run. Benign — qdrant is HTTP-bound on `0.0.0.0:6333`. Will go
  away when R-07's port-rebind half (R-14 follow-up) lands.
- The shared HF cache means `bin/ingest` and `openwebui` both keep
  models warm in the same dir. Don't `rm -rf` either independently.
- If `ensambla2` ever stays dirty for long, that's a soft warning —
  the indexed content won't match the latest pushed state. Worth a
  recurring "is ensambla2 clean?" check in any operational dashboard.
- Disk usage so far: vector storage is small (~4–5 MB added to qdrant's
  on-disk size); the venv is ~1.4 GB (mostly torch). Both well within
  the resource forecast in `05-resource-requirements.md`.

## Quick reference

```bash
# Status across all collections
/home/diego/homelab/ai-stack/ingest/bin/ingest status

# Force re-sync everything (incremental — fast)
/home/diego/homelab/ai-stack/ingest/bin/ingest sync

# Sync one
/home/diego/homelab/ai-stack/ingest/bin/ingest sync --collection guardian_cloud

# Ad-hoc retrieval check
/home/diego/homelab/ai-stack/ingest/bin/ingest search --collection ensambla2 \
    --query "authentication flow" --k 5

# Nuke a collection (requires --yes)
/home/diego/homelab/ai-stack/ingest/bin/ingest drop --collection myfreetour --yes
```
