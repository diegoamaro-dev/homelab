# 05 — Resource requirements

The host has plenty of headroom; the assistant is well within budget for
single-user use, but the numbers below are worth knowing for capacity
planning.

## Current baseline (snapshot from Phase 1 idle audit)

| Resource | Total | In use idle | Free for assistant |
|----------|------:|-----:|-----------:|
| RAM | 30.0 GiB | ~6 GiB | **~24 GiB** |
| Swap | 8.0 GiB | 0 | 8.0 GiB |
| CPU | 16 threads, AVX-512 | <1 % | 16 threads |
| Disk (NVMe `/`) | 468 GB | 98 GB | 346 GB |
| Disk (HDD `/mnt/storage`) | 1.8 TB | 9.7 GB | 1.7 TB |
| GPU | AMD Radeon 780M (no NVIDIA) | — | CPU-only path |

## Per-component sizing (incremental — what Phase 3 adds)

### LLM serving (Ollama)

| Model | Disk | RAM (loaded) | tok/s on this CPU (estimate) |
|-------|-----:|------------:|-----------------------------:|
| `qwen2.5:7b-instruct` Q4_K_M (primary) | ~4.7 GB | ~5.5 GB | 4–7 |
| `qwen2.5:3b-instruct` Q4_K_M (fast fallback) | ~2.0 GB | ~2.5 GB | 12–20 |
| `intfloat/multilingual-e5-small` (embedding) | ~120 MB | ~150 MB | n/a (batch) |
| Whisper `base` (already cached) | ~150 MB | ~250 MB | (only when STT active) |

**Recommended steady-state in RAM:** one LLM at a time, kept warm by
`OLLAMA_KEEP_ALIVE`. With `qwen2.5:7b` warm + Open WebUI + HA + Qdrant +
ingestion idle: ~7–8 GB resident. Headroom for a second model only if
you swap (Ollama unloads on idle by default).

Disk for models: **+4.7 GB** for qwen2.5:7b on top of the 8.3 GB already
present. Dropping unused `llama3:8b` (4.66 GB) and `phi3:3.8b` (2.18 GB)
nets ~2 GB free.

### Vector DB (Qdrant)

Per 384-dim point: ~2 kB on disk (vector + payload + overhead). Plus
per-collection HNSW index overhead once `indexed_vectors_count` crosses
`indexing_threshold` (default 10 000).

| Corpus | Source size | Est. chunks (~600 t) | Est. points | Est. disk |
|--------|-------------|---------------------:|------------:|----------:|
| `homelab_docs` | 5–10 MB | 1 000–2 000 | 1 500 | ~3 MB |
| `guardian_cloud` | 50 MB (docs subset) | 5 000–10 000 | 7 000 | ~14 MB |
| `ensambla2` | 20 MB (docs subset) | 2 000–5 000 | 3 500 | ~7 MB |
| `myfreetour` | unknown | (assume 5 000) | 5 000 | ~10 MB |
| **Total** | ~85 MB raw | ~17 000 chunks | ~17 000 | **~35 MB** |

Add ~30 % for HNSW index after the corpora grow past the indexing
threshold. **Budget: <100 MB** for the vector DB even at 2× growth.

RAM for Qdrant: already running at ~300 MiB; +50 MiB for the four new
collections. Plenty of headroom.

### Ingestion service

| Run mode | RAM peak | CPU | Wall clock (full sync, all 4 corpora, cold cache) |
|---------|---------:|----:|--------------------------------------------------:|
| Initial ingest | ~600 MB (model + batch buffers) | 4 threads at 100 % | 5–15 min |
| Incremental nightly | ~300 MB | 1–2 threads | <1 min (hash-skip path) |

CPU time is dominated by embedding (which is single-threaded per
sentence-transformer call, parallel across the batch). Run during
the existing 03:00 backup window (start at 02:30, finish well before
restic kicks in).

Disk:
- Embedding model cache: ~120 MB once, shared with Open WebUI.
- Code + venv: ~200 MB.
- Logs: capped at 50 MB by logrotate.

### Open WebUI (existing, marginal increase)

Adding the two new tools and a system prompt:

- Tools: ~5 kB of Python code each.
- Per chat round, additional latency:
  - `ha_get_state`: HA REST call, ~50 ms LAN.
  - `rag_search`: embed (~30 ms) + Qdrant search (~10 ms) = ~40 ms.
  - Allow ~150 ms per tool round trip overall (jitter, JSON).
- A multi-tool round adds ~500 ms before the second LLM pass, plus
  whatever the LLM takes to generate.

### Voice (only if enabled)

| Container | RAM | Disk | Notes |
|-----------|----:|-----:|-------|
| `rhasspy/wyoming-whisper` | ~500 MB (medium model) | ~1.5 GB | choose `base` (~150 MB) on CPU |
| `rhasspy/wyoming-piper` | ~250 MB | ~300 MB | one voice per language |
| `rhasspy/wyoming-openwakeword` | ~150 MB | ~50 MB | optional, for wake word |

CPU during STT: ~3 cores for ~1× real-time on `base`. Acceptable for a
single household but not lots of concurrent voices.

## Combined target steady state

| Component | RAM (running, warm) | CPU idle | Disk delta |
|-----------|--------------------:|---------:|-----------:|
| Existing services (Phase 1 baseline) | 6.0 GiB | <1 % | 0 |
| Ollama serving qwen2.5:7b | +5.5 GiB | 0 % idle, 80 % during gen | +4.7 GB |
| Qdrant (4 new collections) | +0.05 GiB | <1 % | +0.1 GB |
| Ingestion (idle between runs) | +0.0 GiB (exits) | 0 % | +0.4 GB |
| Open WebUI tools (in-process) | negligible | negligible | <0.01 GB |
| (Optional) Wyoming stack | +1.0 GiB | <1 % idle | +2 GB |
| **New total** | **~12 GiB warm** | leaves 24 GiB free | **+5 GB minimum, +7 GB with voice** |

## Network

LAN traffic during a typical question:

- HA REST: 1–2 kB request, 5–50 kB response (full `/api/states` is
  ~50 kB on a small home).
- Qdrant: 5–10 kB query, 5–30 kB response (top-k payloads).
- LLM stream: 200–800 B in, 1–5 kB streaming response.

Total per conversation turn: **<100 kB**. The 2.5 Gb LAN is overkill.

Tailnet: same volume, fewer ms thanks to the direct path between trusted
devices.

## What would push us past budget

| Trigger | Effect |
|---------|--------|
| Multiple concurrent users on the LLM | Need GPU or smaller model |
| `bge-m3` instead of `multilingual-e5-small` | Embedding cost ×6, RAM ×5, indexing slower |
| Whisper `large-v3` | +3 GB RAM, ~6 cores during STT |
| RAG corpus > 200 k chunks | Qdrant HNSW build time grows; consider switching `on_disk: true` for vectors |
| Voice + concurrent chat | RAM spike to ~16 GiB; still OK but swap risk |

## When to consider GPU

A discrete GPU (e.g. RX 7600 8 GB or AMD GPU with ROCm) would:

- Roughly **5–10× the LLM token rate** for a 7 B model.
- Enable a 13–14 B model with comfortable headroom.
- Move STT/TTS off the CPU during voice usage.

Not justified for v1 (single user, async chat). Re-evaluate if voice
becomes daily-driver and the LLM is the bottleneck.

## Disk pressure forecast

Before:
```
/        468 G  98 G used (23 %)
/mnt/storage 1.8 T 9.7 G used (1 %)
```

After Phase 3 + R-12 + first 30 days of backups (rough):
```
/        468 G  ~110 G used (24 %)
/mnt/storage 1.8 T  ~30 G used (2 %)   ← restic repo + RAG sources
```

Both well below 50 %. No disk pressure expected.
