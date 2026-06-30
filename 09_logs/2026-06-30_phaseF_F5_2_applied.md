# Phase F — F5.2 Apply Log: Layer B — dynamic Home State (`bin/aurora-context`)

- **Date:** 2026-06-30
- **Milestone:** F5.2 — extend `bin/aurora-context` to detect home anomalies
  (`home_model.md` §6/§7) and render the dynamic `Home State:` block
  ([`../04_ai_system/home_state_design.md`](../04_ai_system/home_state_design.md) §4).
- **Gates:** **G-F5-02 / G-F5-05 / G-F5-06 — validated on real data** (§2). G-F5-03 / G-F5-04
  + optional G-F5-08 are **F5.3**, not started.
- **Scope:** `ai-stack/ingest/bin/aurora-context` **only**. The Layer A prompt, the F-3a Filter,
  tools, `home_model.md`, **AD-20**, and the `aurora-context.json` **schema** are all **unchanged**.

---

## 1. Implementation (one file, additive)

Added a `# Home model — Layer B` section to `bin/aurora-context`:

- `read_env` + `fetch_ha_states` — read `HA_BASE_URL`/`HA_LLAT` from gitignored `ai-stack/.env`
  and `GET /api/states` (mirrors `push-voice-context`; token never printed; non-admin `states`).
- `HOME_RULES` — an in-script **machine transcription** of `home_model.md` §6/§7 (the 9 objects,
  baselines, thresholds, the 10 tokens), cited section by section. `home_model.md` stays the
  single source of truth (see the architecture note, `phase_f_architecture.md` §9-F-5).
- `detect_home` — pure function: HA snapshot + timestamp → ordered `[(token, md_phrase)]` in the
  fixed §7 severity order (deterministic). `render_home` → `home.anomalies[]` (plain string
  tokens) + the `Home State:` MD block, exactly one verdict **Healthy | Degraded | Unavailable**
  (home_state_design.md §4.1–§4.3 / §6).
- `main()` wiring: fail-soft HA fetch → `home.anomalies` populated + block appended after
  `Containers:`; `--dry-run` added (print, write nothing).

**Decisions honored:** D1 string tokens (device names MD-only) · D2 `overall_status` platform-only
· D3 voice line unchanged · D4 inline cited `HOME_RULES` · D5 `--dry-run` · D6 unit tests =
code-vs-spec only · D7 no-guess (zigbee `unavailable` excepted) · D8 Europe/Madrid window +
`last_changed`.

## 2. Validation (real data)

| Check | Result |
|---|---|
| `py_compile` | OK |
| Code-vs-spec unit tests (D6 — synthetic, **not** gate evidence) | **15/15**: §6.1–§6.4 byte-identical, severity order, window/threshold edges, D7, battery naming, determinism |
| **G-F5-02** — real HA cycle | dry-run + real run 2026-06-30: `/api/states` queried, **14/14 home entities present** (true Healthy, not a typo'd false-negative), baseline compared, `home.anomalies=[]` written. Attended run; the unattended nightly cron runs the identical path. |
| **G-F5-06** — no F-4 regression | JSON top-level keys unchanged, `schema_version=1`, `home.anomalies` = list of strings; `generate-digest --dry-run` exit 0, valid digest (`Home: no anomalies`). |
| **G-F5-05** — HA-unreachable | real closed-port → `ConnectionRefusedError` → `home.anomalies=["ha_unavailable"]`, **Unavailable** block, other sections intact, exit 0 (fail-soft). |

**Real-state note:** `cover.toldo` was `open` at validation time but correctly **not** flagged —
daytime is outside the 00:00–06:00 window (`home_model.md` §6.4). If the awning is left open
overnight, the nightly run will legitimately surface `awning_left_extended` — correct behaviour.

## 3. Live runtime

The real validation run **regenerated** `ai-stack/aurora/aurora-context.{json,md}` (gitignored),
which now carry the `Home State: Healthy` block; the F-3a Filter injects it on the next chat.
Because cron runs the working-tree script, F5.2 is effectively live for the next nightly cycle.

## 4. Carried follow-up (D3)

`aurora-context-voice.txt` still hard-codes `no anomalies` (HA voice surface). Reflecting home
anomalies in the voice line is a separate **F-3b / F5 follow-up** — out of F5.2 scope.

## 5. Rollback

`bin/aurora-context` is git-tracked; the change is purely additive and `home.anomalies` was
already `[]` in the schema. Rollback = restore the file from git + re-run → `home.anomalies`
reverts to `[]`, no block; `generate-digest` unaffected. Runtime artifacts regenerate nightly.

## 6. Secret & git safety

No secret in the diff or this log (`HA_LLAT` read at runtime from gitignored `ai-stack/.env`,
never printed; AD-18 — tokens carry no payloads/IPs). The regenerated `aurora-context.*` runtime
artifacts are gitignored.

## 7. Remaining scope

**F5.3** — G-F5-03 (real induced anomaly), G-F5-04 (Filter surfaces it), optional G-F5-08
(`cover` write) — **not started**. F-5 is **not complete** until F5.3.
