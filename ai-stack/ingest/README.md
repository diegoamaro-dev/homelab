# homelab-rag-ingest

Per-corpus ingestion service that feeds the assistant's Qdrant index.

Built as Phase 1 of the
[server-audit-2026-06-13/phase3-ai-assistant](../../server-audit-2026-06-13/phase3-ai-assistant)
plan.

## Layout

```
ingest/
├── bin/ingest                # CLI wrapper (activates venv, runs cli.py)
├── conf/corpora.yaml         # corpus definitions
├── install.sh                # one-shot venv setup
├── requirements.txt
├── ingest/                   # python package
│   ├── cli.py
│   ├── config.py
│   ├── chunker.py
│   ├── connectors/{fs,git}.py
│   ├── embedder.py
│   ├── pipeline.py
│   └── store.py
├── logs/                     # cron output lands here
└── venv/                     # created by install.sh
```

## Install

```bash
cd /home/diego/homelab/ai-stack/ingest
./install.sh
```

This creates a Python venv and installs `qdrant-client`,
`sentence-transformers`, `langchain-text-splitters`, `PyYAML`, and a
CPU-only build of `torch`. ~1.4 GB total.

## Commands

```bash
# Status of every collection
./bin/ingest status

# Sync one or all corpora
./bin/ingest sync                       # all enabled corpora
./bin/ingest sync --collection homelab_docs
./bin/ingest sync --dry-run             # walk & chunk; do not embed or write

# Search a collection
./bin/ingest search --collection homelab_docs --query "how do I rebuild zigbee" --k 6

# Drop all points (requires --yes)
./bin/ingest drop --collection myfreetour --yes
```

## Exit codes

`sync` distinguishes expected operational states from real failures so the exit
code is a trustworthy signal (Phase E, finding F-01 / step E2-a):

| rc | Meaning |
|---:|---|
| 0  | Completed; no **enabled** corpus failed. A **disabled** corpus (`enabled: false`, e.g. the `myfreetour` placeholder) is an *expected* state — it is reported as a skip (`skipped_reason` in the run report) and does **not** affect the exit code. |
| 1  | At least one **enabled** corpus reported a real error (e.g. its `path` does not exist). |
| 2  | Usage error (unknown `--collection`; `drop` without `--yes`). |

`status`, `search`, `init` return 0. The nightly cron does not yet *act* on the
exit code (wiring a run-health signal is Phase E step E3-b).

## How idempotency works

- Point IDs are deterministic: `uuid(sha256(collection|source_rel|chunk_index))`.
- For each file we compute per-chunk `content_sha`s and compare against the
  payloads already stored. Chunks whose `content_sha` is unchanged are
  skipped — no embedding call, no write.
- If a file shrank, its old chunk indexes are deleted before re-upserting.
- Files that no longer exist on disk get their points garbage-collected at
  the end of the run.

## Sensitive config

Reads `QDRANT_API_KEY` from `/home/diego/homelab/ai-stack/.env` (Phase 0 /
R-07 placed it there with mode `0600`). Falls back to the env variable of
the same name.

## Scheduling

Invoked nightly by cron at 02:30 (before the 03:00 restic backup so the new
vector state lands in the snapshot). The cron entry is **installed** in the
`diego` user crontab (verified live 2026-06-27, Phase E E-0 audit):

    30 2 * * * /home/diego/homelab/ai-stack/ingest/bin/ingest sync >> /home/diego/homelab/ai-stack/ingest/logs/ingest.log 2>&1
