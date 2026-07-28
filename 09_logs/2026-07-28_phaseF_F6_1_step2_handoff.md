# Phase F — F6.1 — Step 2 Complete — SESSION HANDOFF

**Date:** 2026-07-28
**Type:** Continuation handoff. F6.1 is **IN PROGRESS**, stopped after Step 2a.
**Production changed:** **NO.** `aurora-whisper` still runs `base-int8`, untouched.
**Repository state at handoff:** clean, `458dda67`, synchronized with `origin/main`.

> **Read this first, then `04_ai_system/phase_f_architecture.md` §9-F-6 and
> `09_logs/2026-07-27_phaseF_F6_1_measurement_protocol.md` (Revision 2, FROZEN).**
> The protocol is binding. Do not amend it without operator ratification.

---

## 1. Where F6.1 stands

| Step | Content | Status |
|---|---|---|
| 1 | Record + freeze the N=30 corpus | **DONE** |
| 2 | Baseline `base-int8`, 3 runs/utterance | **DONE** |
| **2a** | **Evaluate Rule N** | **DONE — Rule N did NOT fire** |
| 3 | Confirm accepted `--model` values (`--help`, no pull) | **NOT STARTED** |
| 4 | Stage `rhasspy/faster-whisper-small-int8` to a staging path | **NOT STARTED** |
| 5 | Laboratory container on `127.0.0.1:10399`, 3 runs/utterance | **NOT STARTED** |
| 5a | Evaluate Rules V → P → H → S | **NOT STARTED** |
| 6 | Production cutover — **only on Rule P + fresh operator approval** | **NOT STARTED** |
| 7 | G-F6-01a…f on the live path incl. G-D4 canary | **NOT STARTED** |
| 8 | Documentation; STOP at git gate | **NOT STARTED** |

**Rule N required `B/N ≥ 0.90`. Measured `B/N = 14/30 = 0.467`.** The defect
reproduces on a fair corpus, so F6.1's premise holds and the phase continues.

### Binding constraints (operator-ratified, protocol §1)

- **D-F6-1 — single-variable isolation.** `--model` is the ONLY variable.
  `--language`, `--beam-size`, `--compute-type`, image tag, caps, ports, mount,
  network and restart policy are FROZEN. The laboratory container must be
  byte-identical to production except `--model`. Any result produced under a
  different decoder configuration is **inadmissible**.
- **D-F6-2 — the laboratory is the mandatory promotion gate.** No path from
  "looks promising" to a cutover that bypasses port 10399.
- **D-F6-3 — single candidate.** `small-int8` ONLY. If it does not clear Rule P,
  F6.1 **stops** — no escalation to `medium-int8`, no retuning, no second corpus.
  Any outcome other than Rule P leaves G-F6-01 open, therefore F-6 open,
  therefore Phase F open. That cost is accepted.

---

## 2. Artifacts and exact paths

All F6.1 working artifacts are **repo-external** by protocol §3 (audio is not
committed). Only this handoff and the protocol live in the repository.

| Path | Content |
|---|---|
| `/home/diego/f6_1_corpus/` | Corpus + tooling |
| `/home/diego/f6_1_corpus/audio/u01.wav … u30.wav` | **Frozen corpus, 30 files, immutable** |
| `/home/diego/f6_1_corpus/manifest.json` | Frozen manifest |
| `/home/diego/f6_1_corpus/manifest_reference.json` | Ground-truth reference set |
| `/home/diego/f6_1_corpus/record_corpus.sh` | Guided recorder (Step 1, done) |
| `/home/diego/f6_1_corpus/finalize_manifest.py` | Validator / freezer (done) |
| `/home/diego/f6_1_corpus/wyoming_probe.py` | **Probe — used for Step 2 and Step 5** |
| `/home/diego/f6_1_corpus/anchor/jfk.flac` | English anchor, sha256-verified |
| `/home/diego/f6_1_baseline/baseline_base-int8.json` | **Step 2 raw probe output** |
| `/home/diego/f6_1_baseline/score_base-int8.json` | **Step 2 scored report** |
| `/home/diego/f6_1_baseline/score.py` | Scorer implementing protocol §4 |

### Canonical hashes

```
reference_sha256   788b2dea41072cc6b27715b2282a3556075e48934e320591cc432f684352db14
manifest_sha256    b8973451cf4e76947070dbe3a1e3a7d01ead96e0bf338849e945180420124bd6
jfk.flac sha256    63a4b1e4c1dc655ac70961ffbf518acd249df237e5a0152faae9a4a836949715
```

Corpus: 30 files, 70.25 s total audio, all 30 re-hashed against the manifest with
**0 mismatches** at handoff time.

Tooling hashes at handoff:

```
fda5d7d9…  f6_1_corpus/record_corpus.sh
21efc25c…  f6_1_corpus/finalize_manifest.py
a645c74d…  f6_1_corpus/wyoming_probe.py
a1e02fd3…  f6_1_baseline/score.py
```

**The corpus is immutable (protocol §3).** No utterance may be added, removed,
re-recorded or re-transcribed. The Step 5 candidate must run against the **same**
`manifest_sha256`; the probe refuses a non-`FROZEN` manifest and the scorer
refuses a `manifest_sha256` mismatch.

---

## 3. Execution environment — the probe does NOT run on the host

`ModuleNotFoundError: No module named 'wyoming'` on the host is expected. The
probe runs **inside a transient container** on `ai-local_default`.

**Do not** install `wyoming` on the host, and **do not** add it to
`ai-stack/ingest/venv` — that venv serves the knowledge platform and backs the
nightly 02:30 ingest.

The chosen image is `rhasspy/wyoming-whisper:3.2.0`, which already ships
`wyoming 1.9.0` at `/usr/src/.venv/bin/python`. **Zero installs, zero network,
image already on disk.** (The probe's own docstring still says
`python:3.12-slim`; that image is present but has no `wyoming` and would need
PyPI egress — the same network path that failed DNS to `huggingface.co` on
2026-07-21. **The docstring should be corrected at Step 8.**)

### Step 2 command, verbatim (reproduces the baseline)

```bash
docker run --rm --network ai-local_default \
  -v /home/diego/f6_1_corpus:/corpus:ro \
  -v /home/diego/f6_1_baseline:/out \
  --entrypoint /usr/src/.venv/bin/python \
  rhasspy/wyoming-whisper:3.2.0 \
  /corpus/wyoming_probe.py \
    --host aurora-whisper --port 10300 \
    --runs 3 --language es \
    --out /out/baseline_base-int8.json
```

The corpus mount is **read-only** by design; results are written outside the
corpus directory. `--language es` is not a free choice — see §5.

### Scoring command, verbatim

```bash
python3 /home/diego/f6_1_baseline/score.py \
  /home/diego/f6_1_baseline/baseline_base-int8.json \
  /home/diego/f6_1_corpus/manifest.json \
  /home/diego/f6_1_baseline/score_base-int8.json
```

---

## 4. Probe and tooling fixes applied (all pre-baseline except where noted)

Five defects were found and fixed. **All are implementation fixes; none altered
the protocol, the manifest, the filenames or the corpus order.**

| # | File | Defect | Fix |
|---|---|---|---|
| 1 | `record_corpus.sh` | **Python `SyntaxError`.** The parser ran as `python3 -c '…'` inside bash single quotes but escaped its dict keys (`f"{e[\"id\"]}"`). Single quotes are literal, so Python received a backslash inside an f-string expression → `unexpected character after line continuation character`. | Heredoc with a **quoted** delimiter (`<<'PY'`) so the body reaches Python verbatim; f-string replaced by `"\t".join([...])`. |
| 2 | `record_corpus.sh` | **Silent no-op.** Because of #1 the parser emitted nothing, `mapfile` succeeded reading **zero** lines, the `for` loop iterated zero times, every `read -rp` was unreachable, and the script printed "Recording pass complete" having recorded **nothing**. It looked like an stdin/EOF fault; it was not. | Assertion: exit **3** unless exactly 30 rows parse. Plus a TTY guard (exit **2**) — without it, a non-interactive run would default every prompt to `k` and keep 30 empty files. Plus `\|\| abort` on all three `read`s and `</dev/null` on backgrounded `arecord` and `aplay`. |
| 3 | `record_corpus.sh` | `printf '%.2f'` on ffprobe's `1.125000` errored under a comma-decimal locale on every take. | `%s`. |
| 4 | `wyoming_probe.py` | **`StatisticsError`** — `statistics.median()` on an empty generator when no RTF value existed. Crashed *after* all 30 transcriptions succeeded. | RTF is now optional: `"rtf_median": null` when unavailable, plus an `"rtf_available": "n/30"` counter; `latency_ms_max` guarded identically. |
| 5 | `wyoming_probe.py` | **Wrong RTF (0.0 for all 30).** `duration_ms` read **67108864** because `getnframes()` returned 2³⁰. `arecord` is terminated with SIGINT by `record_corpus.sh` and never rewrites the RIFF header, leaving a placeholder chunk size. `ffprobe` ignores it (so the manifest durations are correct); Python's `wave` trusts it. | Duration derived from the bytes **actually read**, never the header. |

**Fix #5 matters for anyone re-reading the corpus with Python `wave`:** the
frozen WAV headers carry a bogus data-chunk length. This is **not** a corpus
defect for our purposes — `readframes()` stops at EOF, so the real samples were
always sent, and the manifest durations came from `ffprobe`. **Do not "repair"
the WAVs**: rewriting headers changes the bytes and breaks every hash in the
frozen manifest.

### Also added — recording guardrail

`record_corpus.sh` asserts the frozen microphone calibration **before every
utterance** (volume 448, switch `on`, AGC `off`), exits **4** on mismatch,
records nothing and **never writes an ALSA control**. This exists because the USB
device resets to its hardware default (496 / +31 dB) on **every re-enumeration**
— observed once mid-session (`card2` recreated `2026-07-28 00:10:14`).

---

## 5. `--language es` is verified, not assumed (protocol §8 / B4 — RESOLVED)

Traced through source, not inferred:

| Hop | Location | Code |
|---|---|---|
| Pipeline resolves | `assist_pipeline/pipeline.py:913` | `metadata.language = self.pipeline.stt_language or self.language` |
| HA sends | `wyoming/stt.py:95` | `client.write_event(Transcribe(language=metadata.language).event())` |
| Whisper consumes | `wyoming_faster_whisper/dispatch_handler.py:142` | `self._language = transcribe.language or self._loader.preferred_language` |

`Aurora v1` has `stt_language: "es"`, so **HA sends `Transcribe(language="es")`**
and the handler's `or` takes the request value. The container's
`--language auto` becomes `preferred_language=None` (`__main__.py:164-166`) and
is only a fallback.

**Production transcribes with `language="es"`; it does not auto-detect.**
`--language auto` is dead config on the HA path. The probe must therefore send
`--language es` — omitting it would test a configuration production never uses.

**Consequence:** the G-D4/G-D6 Spanish failures occurred with `es` already
pinned, so they are not language-misdetection artifacts. The language hypothesis
is retired; model capacity is the remaining candidate. Step 5 must use
`--language es` identically.

---

## 6. Step 2 baseline results — `base-int8`

### Primary

| | |
|---|---|
| **B = 14 / 30** | **46.7 %** |
| Baseline failures | **16** |
| **Rule N** (`B/N ≥ 0.90`) | **NOT met** (0.467) → F6.1 proceeds |

### WER / CER

| Metric | Value |
|---|---|
| **Corpus WER** | **0.2885** |
| **Corpus CER** | **0.1086** |
| WER mean per utterance | 0.3217 |
| CER mean per utterance | 0.1213 |
| Correct, accent-folded | **14 — identical to strict** |
| Excluded by repetition | **0** |

No utterance failed on accents alone, including `sí` (#21), flagged as a
known-hard case at pre-registration. The repetition predicate is **vacuous under
exact-match scoring** — an exact match has identical n-gram counts by
construction. It would only do work under fuzzy matching.

### Per tier

| Tier | Correct | Rate |
|---|---|---|
| T1 — production control commands | 5/10 | 50.0 % |
| T2 — information / status queries | 5/10 | 50.0 % |
| T3 — short confirmations | 3/5 | 60.0 % |
| **T4 — historically difficult** | **1/5** | **20.0 %** |

T4 at 20 % reproduces the G-D4/G-D6 `voice canary` failure class on fresh audio.

### Latency (ms) and RTF

| | All 30 | Excluding u08 |
|---|---|---|
| min | 455.1 | 455.1 |
| median | 540.3 | 538.3 |
| mean | 584.3 | **533.2** |
| max | **2065.7** | **588.9** |
| stdev | 282.0 | **35.7** |

RTF — min 0.1515 · **median 0.2235** · mean 0.2606 · max 0.7869 · available 30/30.

u08 alone produces the entire latency tail; the other 29 are extremely
consistent (35.7 ms stdev).

### The 16 baseline failures (ids)

`4, 5, 6, 7, 8, 11, 15, 17, 18, 19, 23, 25, 26, 27, 29, 30`

The 14 correct: `1, 2, 3, 9, 10, 12, 13, 14, 16, 20, 21, 22, 24, 28`.

---

## 7. Utterance 08 — documented finding, operator-ratified

**Determinism: 29/30. Non-deterministic: id 8 only.**

**Operator ratification (2026-07-28): treat as a documented model-quality
finding, NOT an instrumentation failure. u08 is scored INCORRECT. Rule V is NOT
triggered. The protocol is unchanged.**

### Evidence

10 consecutive runs of `u08.wav` (`baja el toldo`) against the live endpoint:

| Distinct transcript | Count |
|---|---|
| `' Me ha hecho todo'` | 4 |
| `' Me ha halltoldo.'` | 2 |
| `' ¿Me ha hecho el tolado?'` | 2 |
| `' ¿Me ha hecho el tolo?'` | 2 |

Latency min/median/max **1505.7 / 1650.6 / 2997.6 ms** versus ~520 ms typical.
**None of the four is correct.**

- **Bytes unchanged** — sha256 `57664969b07cd923e2429d06604a1374fd32b5fb95f0ea56b38ab3664b3cc188`
  identical before and after; matches the frozen manifest.
- **Audio is not faulty** — peak −10.34 dBFS, RMS −28.01, flat factor 0.000000
  (no clipping), noise floor −35.27, duration 2.625 s; indistinguishable from
  neighbours u06/u07/u09/u10.
- **Server-side confirmed** — `aurora-whisper` logs the same variation and
  `Processing audio with duration 00:02.625` on every decode. Zero errors.
- **Isolated** — controls u07, u09, u29 each returned **1 distinct transcript
  across 10 runs**. Both full baseline passes (3×30, twice) flagged only id 8.
  u29 is *badly wrong yet perfectly deterministic*, so wrongness does not imply
  non-determinism.

### Cause — model decoding (temperature fallback)

`wyoming_faster_whisper` passes only `beam_size`, `language`, `initial_prompt`,
`vad_filter`, `vad_parameters` to `faster_whisper 1.2.1`. It **never overrides
`temperature`**, so the library default ladder stays active:

```
temperature                 = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
compression_ratio_threshold = 2.4
log_prob_threshold          = -1.0
no_speech_threshold         = 0.6
```

With `--beam-size 1` the first pass is greedy and deterministic. When
`avg_logprob < -1.0` (or compression ratio > 2.4) faster-whisper retries at
temperature > 0 — i.e. **sampling** — and each retry is another full decode,
which is why latency rises 3–5×.

**`--beam-size 1` guarantees determinism only while the model is confident.**

Excluded: **VAD** (container has no `--vad-filter`; handler sets
`vad_filter = vad_parameters is not None` → False), **endpoint state** (controls
interleaved in the same session were 10/10 deterministic), **probe behaviour**
(identical sha256 and identical server-logged duration on all 10 decodes).

**Do not "fix" this by pinning `temperature=0.0` in the probe** — that would make
the measurement diverge from production, which decodes exactly as tested.

---

## 8. Production state — unchanged

```
container   aurora-whisper
image       rhasspy/wyoming-whisper:3.2.0
image id    sha256:966e1b0967f398b81fa2273a96b2b940004fa1b77754f9ffda6b5689a58dd158
cmd         ["--model","base-int8","--language","auto","--beam-size","1","--compute-type","int8"]
started     2026-07-25T21:50:55.349910391Z     restarts 0
ports       127.0.0.1:10300 -> 10300/tcp        (MANDATORY — HA targets 127.0.0.1:10300)
mount       /srv/homelab/data/whisper/wyoming -> /data
caps        --cpus 4  --memory 4g
model dir   sha256 2f8d05357575312f25b9a76e71e16cff6b672b864e2b8cf30e3202bd1d6dfb4e
```

Rollback reference: `09_logs/2026-07-27_phaseF_F6_1_baseline_capture.md` §3.2
(exact `docker run` derived from the live inspect) and §5 (procedure).
`/srv/homelab/data/whisper` is **outside restic coverage** — never delete the
`models--rhasspy--faster-whisper-base-int8` blobs.

### Microphone calibration — NOT persistent

```
device   plughw:CARD=Micpro,DEV=0        (USB 0c76:1734 JMTek Micpro, card 2)
volume   numid=3 = 448   (90%, +28.00 dB)
switch   numid=2 = on
AGC      numid=4 = off
geometry fixed, ~10-15 cm
```

**A USB re-enumeration resets volume to 496 / +31 dB.** At +31 dB a firm short
command peaked at −1.46 dBFS, 1.5 dB from clipping. `record_corpus.sh` asserts
these values before every utterance and refuses to record on mismatch. Only
relevant if the corpus were ever re-recorded — which the freeze forbids.

---

## 9. Repository state

```
HEAD        458dda679804e1a22c209249310fb844dc7ffcee
origin/main 458dda679804e1a22c209249310fb844dc7ffcee
divergence  0 / 0      working tree clean (0 entries)
```

Published for F-6:

| Commit | Content |
|---|---|
| `6b090679` | F-6 architecture (§9-F-6), AD-22, Voice Lab separation ADR |
| `f453c8f4` | Pre-registered F6.1 protocol (Rev 2) + baseline capture |
| `458dda67` | Voice Test Suite recorded as proposed future capability |

**This handoff is uncommitted.** Committing and pushing each require **separate,
fresh operator approval** immediately before the command
(`PROJECT_RULES` → Operator Git Approval). Author as
`Diego <diego@diegoamaro.dev>`; **no `Co-Authored-By` trailers, no AI or vendor
attribution anywhere.**

---

## 10. Exact next step — `small-int8`

### Promotion thresholds, now fixed by measurement

| Predicate | Requirement | Derivation |
|---|---|---|
| **P1** | `C ≥ 27` of 30 | `C/N ≥ 0.90` |
| **P2** | `F ≥ 8` | `F ≥ ⌈(N−B)/2⌉ = ⌈16/2⌉` |
| **P3** | `R = 0` | no regression among the 14 currently correct |
| **P4** | T1 = 10/10 | daily control commands |
| **P5** | RTF ≤ 0.35 **and** `L_max ≤ 1.5 s` | |
| **P6** | `WER_en ≤ baseline` | English no-regression |

**P1 is the binding constraint.** Reaching C ≥ 27 from B = 14 requires fixing at
least **13 of 16** failures while regressing none — well beyond P2's 8.

Decision order at Step 5a is **V → P → H → S**, first match wins, and no rule may
be reinterpreted after the numbers are known.

### Two items to resolve BEFORE the candidate runs

1. **P6 has no baseline.** `WER_en` is unmeasured. `jfk.flac` is fetched and
   sha256-verified but is FLAC 44.1 kHz **stereo**, and the probe reads WAV only.
   It needs conversion and a one-off invocation (it is not in the corpus
   manifest, so it needs its own tiny manifest or a separate code path):
   ```bash
   ffmpeg -i /home/diego/f6_1_corpus/anchor/jfk.flac -ar 16000 -ac 1 \
          -c:a pcm_s16le /home/diego/f6_1_corpus/anchor/jfk_16k_mono.wav
   ```
   Ground truth: *"and so my fellow americans ask not what your country can do
   for you ask what you can do for your country"*. The D-1.2 reference result was
   WER 0.000, RTF 0.055.
2. **P5's `L_max ≤ 1.5 s` may be unreachable.** The **baseline's own max is
   2065.7 ms** — u08's fallback tail. If `small-int8` triggers fallback anywhere,
   P5 fails on latency regardless of accuracy. Excluding u08 the baseline max is
   588.9 ms. **Operator decision required:** is `L_max` measured across all
   utterances, or does it exclude fallback events? **This is a protocol question
   — do not self-amend.**

### Step 3 — confirm accepted `--model` values (no pull)

```bash
docker run --rm --entrypoint /usr/src/.venv/bin/python \
  rhasspy/wyoming-whisper:3.2.0 -m wyoming_faster_whisper --help
```

Cache naming (`models--rhasspy--faster-whisper-base-int8`) implies
`small-int8` → `rhasspy/faster-whisper-small-int8`, but that is **inference, not
verification**. Confirm before staging.

### Step 4 — stage the candidate to a STAGING path

Never into the live cache `/srv/homelab/data/whisper/wyoming`. Use a separate
directory, e.g. `/srv/homelab/data/whisper/lab`. Requires HuggingFace egress from
the container network — **this failed once on 2026-07-21** (`Temporary failure in
name resolution` for `huggingface.co`), so verify egress immediately beforehand.
Note the container also fetches `openai/whisper-tiny/tokenizer.json` on **every**
start; it is non-fatal but cost 23.1 s of retry backoff when egress was down.

Repo doc estimate for `small-int8` is ≈480 MB, but the same table over-estimated
`base-int8` at ≈150 MB against **76 MB actual** — treat as a conservative
ceiling and record the measured size.

### Step 5 — laboratory container, byte-identical except `--model`

```bash
docker run -d --name aurora-whisper-lab --restart no \
  --network ai-local_default \
  -p 127.0.0.1:10399:10300 \
  -v /srv/homelab/data/whisper/lab:/data \
  --cpus 4 --memory 4g \
  rhasspy/wyoming-whisper:3.2.0 \
  --model small-int8 \
  --language auto \
  --beam-size 1 \
  --compute-type int8
```

`--language auto`, `--beam-size 1`, `--compute-type int8`, image tag and caps are
**frozen by D-F6-1** and must match production exactly. Only `--model`, the
container name, the published port and the staging mount differ.

Then run the probe against it:

```bash
docker run --rm --network ai-local_default \
  -v /home/diego/f6_1_corpus:/corpus:ro \
  -v /home/diego/f6_1_baseline:/out \
  --entrypoint /usr/src/.venv/bin/python \
  rhasspy/wyoming-whisper:3.2.0 \
  /corpus/wyoming_probe.py \
    --host aurora-whisper-lab --port 10300 \
    --runs 3 --language es \
    --out /out/candidate_small-int8.json
```

Score it with the same command as §3, substituting the candidate file. **Remove
the lab container afterwards** — it is not production and must not linger.

---

## 11. Hard invariants for the next session

1. **Never modify the frozen corpus, its manifest, or the WAV bytes.** Verify
   `manifest_sha256 = b8973451cf4e…` before trusting any result.
2. **Never touch production `aurora-whisper` before Rule P AND fresh operator
   approval** (Step 6). Steps 3–5 change nothing in production.
3. **The laboratory container differs from production in `--model` only.**
   Anything else voids the comparison (Rule V).
4. **Do not amend the protocol.** Rules N/P/H/S/V and their thresholds are frozen
   at Revision 2. Findings that appear to require an amendment are recorded and
   ratified by the operator — the D-ER-11/12/13 precedent.
5. **`git commit`, `git push`, `git tag` each need fresh, immediate operator
   approval.** Never inherited across steps or sessions.
6. **Do not escalate to `medium-int8`** under any non-Rule-P outcome (D-F6-3).

---

## 12. Git gate

Documentation-only. **Not committed, not pushed** — both require explicit
operator approval per `PROJECT_RULES` → Operator Git Approval. **STOP at git
gate.**
