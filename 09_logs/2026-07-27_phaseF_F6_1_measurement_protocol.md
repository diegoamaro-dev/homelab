# Phase F — F6.1 — Pre-Registered Measurement Protocol & Stopping Criterion

**Date:** 2026-07-27
**Type:** Protocol. **Pre-registered — written before any candidate model exists on this host and
before any measurement has been taken.** No production change. Nothing executed.
**Status:** Operator-ratified constraints (§1). Binding on F6.1 execution.
**Precedent:** `09_logs/2026-07-17_ER1_4b_c1_measurement_protocol.md` — the decision rules are
fixed in advance and the outcome is read against them, never the reverse.

**Revision 2 — 2026-07-27, operator-directed, pre-measurement.** Corpus expanded **N = 20 → 30**
with a four-tier distribution better representing daily usage (§3). Consequential edit: Rule P4
becomes `T1_c = 10/10` because Tier 1 resized from 8 to 10 — the predicate ("100 % of Tier 1") is
unchanged. Every other clause — normalization, correctness definition, determinism precondition,
Rules N/P/H/S/V and their thresholds, execution order, rollback — is **unchanged**. Amended
**before any corpus was recorded and before any measurement was taken**, so pre-registration
integrity is intact.

---

## 1. Operator-ratified constraints (2026-07-27)

### D-F6-1 — Single-variable isolation

F6.1 changes **exactly one production variable: `--model`.**

| Parameter | F6.1 status |
|---|---|
| `--model` | **ALLOWED** — the variable under test |
| `--language` | **FROZEN** at `auto` |
| `--beam-size` | **FROZEN** at `1` |
| `--compute-type` | **FROZEN** at `int8` |
| Every other decoder parameter | **FROZEN** |
| Image tag, caps, ports, mount, network, restart policy | **FROZEN** (baseline capture §3.2) |

The laboratory container is byte-identical to production except `--model`. Any result produced
under a different decoder configuration is **inadmissible** for the promotion decision.

Consequence, recorded deliberately: the diagnostic arms A1 (`language=es`) and A2 (`beam 5`)
proposed earlier are **withdrawn from F6.1**. They manipulate frozen variables and would confound
the single-variable comparison. They are re-proposable at architectural review.

### D-F6-2 — The laboratory is the mandatory promotion gate

Production is **not** touched unless the port-`10399` laboratory clearly outperforms the baseline
under §5 Rule P. There is no path from "candidate looks promising" to a production cutover that
bypasses the laboratory.

### D-F6-3 — Single-candidate stopping criterion

`small-int8` is the **only** candidate F6.1 will evaluate. If it does not clear Rule P, F6.1
**stops** — it does not escalate to `medium-int8`, does not retune, and does not retry with a
different corpus. The outcome is documented and returned for architectural review.

**Consequence, stated plainly:** any outcome other than Rule P leaves **G-F6-01 open**, therefore
**F-6 open**, therefore **Phase F open**. That is the accepted cost of not letting a reliability
milestone drift into open-ended model shopping.

---

## 2. What is being measured

**Claim under test:** upgrading the HA Wyoming STT model from `base-int8` to `small-int8`, with
every other parameter unchanged, meaningfully improves Spanish short-utterance transcription.

**Evidence the claim rests on** (G-D4 / G-D6 apply logs, 2026-06-17/18): `base-int8` rendered
`enciende el voice canary` as *"Enfiinde el canario de voz"*, *"Enfiende, voy a hacer canal"*,
*"Enfiende, Voice Canary"*, *"y fiende voz canadi"*, *"En fiende, boys"*; and `canario→canal`,
`apaga→apara`. Counter-evidence: G-D5 transcribed *"Enciende la impresora 3D"* and *"Apaga la
impresora 3D"* with zero slop. **No audio from any of these events was retained**, which is why
the corpus must be recorded fresh and frozen.

---

## 3. Corpus specification (frozen before any candidate runs)

**N = 30** utterances, Spanish, 16 kHz mono 16-bit WAV, one phrase per file, recorded by the
operator in normal daily-use conditions (same room, same microphone, no re-takes for quality —
re-takes only for recording faults such as clipping or truncation).

| Tier | n | # | Utterance |
|---|---|---|---|
| **T1 — Production control commands** | 10 | 1 | `enciende la impresora 3D` |
| | | 2 | `apaga la impresora 3D` |
| | | 3 | `enciende la impresora` |
| | | 4 | `apaga la impresora` |
| | | 5 | `abre el toldo` |
| | | 6 | `cierra el toldo` |
| | | 7 | `sube el toldo` |
| | | 8 | `baja el toldo` |
| | | 9 | `para el toldo` |
| | | 10 | `apaga la impresora 3D por favor` |
| **T2 — Information / status queries** | 10 | 11 | `¿está encendida la impresora?` |
| | | 12 | `¿está abierto el toldo?` |
| | | 13 | `¿cómo está la casa?` |
| | | 14 | `¿qué tal el laboratorio?` |
| | | 15 | `¿hay alguna anomalía?` |
| | | 16 | `¿cómo están los servicios?` |
| | | 17 | `¿funciona la conexión a Internet?` |
| | | 18 | `¿qué estado tiene la impresora 3D?` |
| | | 19 | `¿hay copias de seguridad recientes?` |
| | | 20 | `¿qué ha pasado esta noche?` |
| **T3 — Short confirmations / cancellations** | 5 | 21 | `sí` |
| | | 22 | `no` |
| | | 23 | `vale` |
| | | 24 | `cancela` |
| | | 25 | `para` |
| **T4 — Historically difficult phrases** | 5 | 26 | `enciende el voice canary` |
| | | 27 | `apaga el voice canary` |
| | | 28 | `enciende aurora voice canary` |
| | | 29 | `enciende voice canary` |
| | | 30 | `enciende el canario de voz` |

**Tier provenance.** T1 and T2 exercise the real action and awareness surface —
`switch.impresora_3d`, `cover.toldo`, `binary_sensor.rooter_estado_wan`, the World Model regions,
the backup probe and the nightly digest. T4 is verbatim the phrasing class that `base-int8`
failed at G-D4 / G-D6 (*"Enfiinde el canario de voz"*, *"y fiende voz canadi"*, *"En fiende,
boys"*, `canario→canal`, `apaga→apara`).

**Known-hard scoring case, recorded in advance:** #21 `sí` differs from `si` only by the accent,
and §4.1 preserves accents. Under strict scoring a transcript of `si` is **incorrect**. This is
intentional and applies identically to both models; the secondary accent-folded score (§4.3) will
show its isolated effect.

Each file carries: filename, ground-truth text, sha256, duration. The corpus manifest is frozen
and hashed **before** the candidate model is downloaded.

**Frozen means frozen.** After the baseline is measured, no utterance may be added, removed,
re-recorded, or re-transcribed as ground truth. Audio is stored outside the repository (same
policy as the Voice Lab); only the manifest and results are committed.

## 4. Scoring specification (pre-registered)

### 4.1 Normalization, applied identically to hypothesis and reference

1. Unicode NFC, then lowercase
2. Trim, collapse internal whitespace
3. Strip `. , ; : ! ? ¡ ¿ " ' « » – —` and trailing periods
4. **Accents and `ñ` are preserved** (strict scoring)
5. Canonical map, fixed now: `3 d` / `3d` / `tres de` / `tres d` → `3d`

### 4.2 An utterance is CORRECT iff

- the normalized hypothesis equals the normalized reference exactly, **and**
- it exhibits no **repetition**, defined as: any contiguous n-gram (n ≥ 2) occurring more times
  than in the reference, **or** a token count > 2× the reference.

Repetition is scored as incorrect even if the text otherwise matches — G-F6-01 requires
"without repetition".

### 4.3 Metrics

| Symbol | Definition |
|---|---|
| `B` | baseline correct count (`base-int8`), out of N |
| `C` | candidate correct count (`small-int8`), out of N |
| `F` | **fixes** — incorrect at baseline, correct at candidate |
| `R` | **regressions** — correct at baseline, incorrect at candidate |
| `T1_c` | candidate correct count within Tier 1 |
| `RTF_c` | candidate real-time factor (median over corpus) |
| `L_max` | candidate worst-case STT latency on the corpus |
| `WER_en` | word error rate on `jfk.flac` (sha256 `63a4b1e4c1dc655ac70961ffbf518acd249df237e5a0152faae9a4a836949715`) |

Secondary, reported but **not** decision-driving: accent-folded accuracy, corpus-level WER,
per-tier breakdown.

### 4.4 Determinism precondition

`--beam-size 1` is greedy decoding: identical audio through an identical container must yield an
identical transcript. Each utterance is transcribed **3×** on each model. If any utterance is not
byte-identical across its 3 runs, the comparison is **void** — the run is discarded, the
non-determinism is recorded as a finding, and F6.1 stops for architectural review. This is a
precondition, not a metric.

## 5. Decision rules — fixed before measurement

Read the outcome against these rules in order. The first rule whose conditions hold is the
outcome. **No rule may be reinterpreted after the numbers are known.**

### Rule N — NULL RESULT (the defect does not reproduce)

**Condition:** `B / N ≥ 0.90` at baseline.

The premise of F6.1 fails: `base-int8` already meets the G-F6-01 bar on a fair corpus, so a model
bump has nothing to fix. This is a live possibility — G-D5 showed clean transcription on exactly
the phrases G-F6-01 names.

**Action:** **STOP F6.1. Do not download any candidate.** Document that the daily-use voice
problem lies elsewhere — candidates being HA intent-matching (`HA-VOICE-001`), end-to-end latency
(F6.3), or wake-word behaviour. Return for architectural review.

### Rule P — PROMOTE (all six must hold)

| # | Condition | Rationale |
|---|---|---|
| P1 | `C / N ≥ 0.90` | The G-F6-01 bar, measured |
| P2 | `F ≥ ⌈(N − B) / 2⌉` | **This is "meaningful": the candidate fixes at least half of the baseline's failures.** Not "any improvement" |
| P3 | `R = 0` | A reliability milestone must not break what already worked |
| P4 | `T1_c = 10/10` | The daily control commands are non-negotiable. Scoped to T1 only: a misheard **control command** actuates or fails on a real device, whereas a misheard **query** (T2) merely returns a wrong answer |
| P5 | `RTF_c ≤ 0.35` **and** `L_max ≤ 1.5 s` | Latency stays inside daily-use tolerance (baseline RTF = 0.055) |
| P6 | `WER_en ≤ WER_en(baseline)` | No English regression (G-F6-01) |

**Action:** proceed to the Step 6 production cutover — **after** a fresh operator approval at the
moment of execution.

### Rule H — HOLD (improvement, but not clearly outperforming)

**Condition:** `C > B`, but any of P1–P6 fails.

The candidate helps but does not clear the bar — for example it fixes failures while introducing a
regression (`R ≥ 1`), or clears accuracy but breaches latency (P5).

**Action:** **Production is not touched.** Document the full result table including which
predicate failed. **Do not escalate to `medium-int8`** (D-F6-3). Return for architectural review.

### Rule S — STOP (no improvement)

**Condition:** `C ≤ B`.

**Action:** **Production is not touched.** Document. Return for architectural review with the
finding that STT model capacity is not the binding constraint on Spanish reliability.

### Rule V — VOID

**Condition:** the §4.4 determinism precondition fails, or the laboratory container differs from
production in any parameter other than `--model`, or the corpus was modified after baseline.

**Action:** discard the run. No promotion decision may be made from void data.

---

## 6. Execution order (binding)

| Step | Action | Touches production? |
|---|---|---|
| 1 | Record + freeze the N=30 corpus (§3); hash the manifest | No |
| 2 | Baseline `base-int8` over Wyoming, 3× per utterance; compute `B`, `WER_en`, RTF | No — read-only against the live container |
| **2a** | **Evaluate Rule N.** If it fires, stop here | No |
| 3 | Confirm accepted `--model` values (`--help` on the already-present image) | No — transient container, no pull |
| 4 | Stage `rhasspy/faster-whisper-small-int8` into a **staging path**; never into the live cache | No |
| 5 | Laboratory container on `127.0.0.1:10399`, identical to production except `--model`; 3× per utterance; compute `C`, `F`, `R`, `T1_c`, `RTF_c`, `L_max`, `WER_en` | No |
| **5a** | **Evaluate Rules V → P → H → S** in that order | No |
| 6 | **Only on Rule P, and only after fresh operator approval:** stop / rm / recreate `aurora-whisper` per baseline-capture §3.2 with the new `--model` | **YES** |
| 7 | G-F6-01a…f on the live path incl. the G-D4 canary round-trip; canary restored to `off` | Validation |
| 8 | Documentation; **STOP at git gate** (separate approvals for commit, then push) | No |

The baseline (Step 2) is measured **before** the candidate is downloaded (Step 4), so the baseline
cannot be tuned to the candidate.

## 7. Rollback

Unchanged from the baseline capture, `09_logs/2026-07-27_phaseF_F6_1_baseline_capture.md` §5:
recreate from the captured recipe with `--model base-int8`. Weights remain cached
(`MODEL_DIR_SHA256 = 2f8d05357575312f25b9a76e71e16cff6b672b864e2b8cf30e3202bd1d6dfb4e`) and must
never be deleted — `/srv/homelab/data/whisper` is outside restic coverage. Allow ~25 s extra if
container egress to `huggingface.co` is down (the tokenizer fetch at every start; measured 23.1 s
of backoff on 2026-07-21, non-fatal).

## 8. Carried finding — not an F6.1 variable

**B4 remains open as a documentation question:** the Assist pipeline sets `stt_language: es`
while the container runs `--language auto`. Whether the per-request Wyoming language overrides
the container default determines what production is actually doing today. Under D-F6-1 this
**must not** be probed by manipulating the language variable. It is answerable by reading the
`wyoming_faster_whisper` handler inside the image — pure observation, no experiment. If the
answer is that `--language auto` is **not** overridden, that is a finding for architectural
review, not an F6.1 change.

## 9. Stop point

Nothing executed. No corpus recorded, no model downloaded, no container created, no production
change. This protocol is registered before the fact and is binding on F6.1 execution.

## 10. Git gate

Documentation-only. Committed 2026-07-27 on explicit operator approval per `PROJECT_RULES` →
Operator Git Approval. **Not pushed** — origin update is a separate operator decision requiring
its own fresh approval. **STOP at git gate.**
