# Phase F — F5.3 Apply Log: Home-anomaly validation (real induced anomaly)

- **Date:** 2026-07-01 (validation window 00:00–06:00 Europe/Madrid)
- **Milestone:** F5.3 — real induced home anomaly (G-F5-03) + automatic Filter
  surfacing (G-F5-04), per
  [`../04_ai_system/phase_f_architecture.md`](../04_ai_system/phase_f_architecture.md)
  §9-F-5 and [`../04_ai_system/home_model.md`](../04_ai_system/home_model.md)
  §6.3 / §7.
- **Gates:** **G-F5-03 = PASS. G-F5-04 = FAIL (real validation).** Optional
  G-F5-08 (`cover` write) **not attempted** (out of scope).
- **Method:** **manual induction** (operator switched `switch.impresora_3d`
  on/off via Home Assistant; operator decision — keeps the test on the
  detection pipeline, not the control path). Aurora performed **no** control
  actuation.
- **Scope guard:** validation only. **No code, prompt, tool, or
  architecture-design change.** The frozen F-5 design, the F-1 `params.system`,
  and the `system_status` tool were **not modified**.

---

## 1. Procedure (real evidence only — no fabrication)

Pre-flight (read-only, 2026-06-30 ~23:10 CEST): HA reachable; non-window anomaly
surface clean (Zigbee/WAN/permit-join/door/plant/battery all nominal);
`switch.impresora_3d = off`; `cover.toldo = open`.

Window entry 2026-07-01 00:00 CEST. Operator set the canonical scenario:
- **Awning closed** — `cover.toldo = closed` (negative control; if left open it
  would also raise `awning_left_extended`).
- **Printer on** — `switch.impresora_3d = on` (00:00:05 CEST), manual.

Detection path (host `bin/aurora-context`, Europe/Madrid window per `home_model.md` §6.3):
- **Guarded `--dry-run` (00:16 CEST, writes nothing):** `home.anomalies =
  ["printer_on_overnight"]`; no awning token; `ha_unreachable=False`. Reality
  matched the prediction → authorised the real run.
- **Real run (00:17 CEST):** wrote `aurora-context.{json,md}`;
  `home.anomalies = ["printer_on_overnight"]`; markdown `Home State: Degraded →
  Attention: - [medium] 3D printer on overnight`; `overall_status = ok` (home
  anomalies do not change platform status — D2). `generate-digest --dry-run`
  produced a valid digest (`Notable: home anomalies: printer_on_overnight`) →
  **no F-4 regression** (AD-20 schema preserved).

## 2. G-F5-03 — PASS

The detector read live `/api/states`, compared to `home_model.md` baselines, and
wrote **exactly the single expected token** `printer_on_overnight` to
`home.anomalies[]` plus the Degraded `Home State` block. Negative control held
(awning closed → no `awning_left_extended`); clean background → single-token
result. The container bind-mount delivered the Degraded markdown to the Filter
input (`/opt/aurora/aurora-context.md`).

## 3. G-F5-04 — FAIL (real validation)

With the Degraded context live, the operator opened a fresh Open WebUI
conversation. The **F-3a Filter injected correctly**
(`event:inject, fallback:false, chars:331, reason:ok:0.0h` @ 00:20:30 CEST), and
Open WebUI **preserved** the block in the model system message (non-destructive
merge — `add_or_update_system_message` → `update_message_content`; the model
received the full Degraded context). Despite correct, present context, Aurora
did **not** surface the anomaly:

- *"¿Está todo bien en el laboratorio?"* → called **`system_status`** (reply
  cited Torre — `system_status`-only, AD-03) → returned `ok` → *"todo bien, no
  hay alertas"*; **the printer was omitted.**
- *"¿Cómo está la casa?"* → `ha_get_state` on **invented** entity_ids
  (`binary_sensor.awning`, `sensor.internet_connection_status` → both
  `not_found`) → a **wrong** answer ("internet unavailable").

**Root cause (read-only investigation, this session):**
1. **Prompt routing precedence (primary).** `params.system` `# Routing` sends
   lab-health → `system_status` and HA-state → `ha_get_state`; at 7B scale these
   out-compete the later `# Context`/`# Home` "answer from the block, no tool"
   exception. The injected context was correct, present, and well-positioned —
   it lost the routing contest.
2. **`system_status` is home-blind (integration gap).** v0.2.0 reads only the
   platform sections of `aurora-context.json`; it never reads `home.anomalies`,
   and `overall_status` stays `ok` (D2). The tool path **cannot** surface a home
   anomaly.
3. **`ha_get_state` entity-id hallucination (secondary).** `# Home` names
   objects/baselines in prose but not real entity_ids; the model guessed
   non-existent ids and answered from `not_found`.

**Vision impact:** violates `AURORA_VISION.md` §4 ("'is everything OK?' should
not require a tool call") and §7 ("Aurora does not pretend") — a
falsely-reassuring "todo bien" while a real, correctly-injected overnight
anomaly was live. Awareness **delivery** (Filter) works; awareness
**consumption** (model routing + `system_status`) does not.

## 4. Decision — new architecture issue, deferred (no fix this session)

Logged as **R-F5-A — Awareness-consumption gap** (routing/context precedence +
`system_status` home-blindness; secondary `ha_get_state` id grounding). Per
operator instruction: **no fix, no redesign, no prompt/tool change.** The remedy
is an architecture-level decision (it touches the frozen F-1 `params.system`
and/or the F-2 `system_status` tool) and is **deferred to a future gated phase**.
Reconciling `phase_f_architecture.md` (§9-F-5 status + §11 finding register) is
part of that gated phase; this log + the triad carry the current reality
(CURRENT_STATE.md is the source of truth).

**F-5 is not complete.** G-F5-04 is a real, open failure.

## 5. Baseline restore (confirmed)

Operator switched `switch.impresora_3d` **off** (00:38:51 CEST). Guarded restore:
`--dry-run` → `home.anomalies=[]`; real `bin/aurora-context` (00:39 CEST) →
`overall_status=ok`, `home.anomalies=[]`, `Home State: Healthy`; container view
Healthy; `generate-digest --dry-run` → `Home: no anomalies`. Awning stayed
closed throughout. The brief, attended induction was reverted immediately; **no
degraded operational night was recorded** (tonight's 04:15/04:25 cron runs clean).

## 6. Secret & git safety

No secret in this log or the change set. `HA_LLAT` / `HA_BASE_URL` are read at
runtime from gitignored `ai-stack/.env`, never printed (AD-18). Runtime
artifacts (`aurora-context.*`) are gitignored. Entity_ids and device states are
not secrets (already in `home_model.md`); no token, no IP. **No git operation
performed — STOPPED at the git approval gate.**

## 7. Status

- **G-F5-03 = PASS · G-F5-04 = FAIL (R-F5-A, deferred to a future gated phase).**
- **F-5 remains open.** No fix attempted; frozen design / prompt / tools untouched.
- Triad (CURRENT_STATE / ROADMAP / AMAROLAB_HANDOFF) reconciled in this change set.
