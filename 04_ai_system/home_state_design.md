# home_state_design.md — AURORA Home State (Phase F-5, G-F5-07 design)

Phase: **F-5 — Home Intelligence**. Gate: **G-F5-07** (system prompt references
the home model; Aurora answers about any in-model object in a single exchange).
Status: **Layer A (the §5 `# Home` frame) — IMPLEMENTED + verified 2026-06-30
(G-F5-07); apply log
[`../09_logs/2026-06-30_phaseF_F5_G-F5-07_applied.md`](../09_logs/2026-06-30_phaseF_F5_G-F5-07_applied.md).
Layer B (the §4 `Home State` block) — IMPLEMENTED 2026-06-30 (F5.2; apply log
[`../09_logs/2026-06-30_phaseF_F5_2_applied.md`](../09_logs/2026-06-30_phaseF_F5_2_applied.md)).** This
document itself makes no runtime change; Layers A and B were implemented separately per their apply logs.
Last updated: 2026-06-30.
Sources of record: [`home_model.md`](home_model.md) · [`phase_f_architecture.md`](phase_f_architecture.md)
(§9-F-5, AD-01/02/11, **AD-20**) · [`AURORA_VISION.md`](AURORA_VISION.md) (§3, §4, §6, §7, §8).

> **Governing principle: the Home State is cognitive context, not an alert feed.**
> It exists so Aurora *understands* the home well enough to answer and reason — not
> to stream notifications. It is read at conversation start, framed by severity, and
> silent when nothing needs attention.

---

## 1. Purpose

Design the **Home State** — the layer that represents the **current operational
state of the home** and lets Aurora answer, without aggregating raw entities:

- Is the home healthy?
- What requires attention?
- Which anomalies exist (and how serious)?
- What context matters for reasoning right now?
- What should Aurora keep in mind while answering?

It is **not a Home Assistant dump**, and it is **not an alert feed**. It is
cognitive context, consistent with the `home_model.md` core principle — *AURORA
reasons about the home, not about Home Assistant; HA is only the implementation
layer* — and with VISION §4 ("Home state … anything that deviates from expected
baseline") and §3 ("silence is informative").

---

## 2. Architecture placement — two coordinated layers

A single static prompt cannot contain tonight's anomalies (they change nightly),
and the dynamic awareness channel is, by architecture, the F-3a Filter over a
pre-generated file (AD-01/AD-02/AD-11). So the Home State is delivered in **two
layers** that must be designed together:

| Layer | Where | Lifecycle | Delivered by |
|---|---|---|---|
| **A. Home frame** (static) | `# Home` section in the F-1 system prompt (`params.system`) | Stable; changes only when the object set changes | **G-F5-07** (this design → a later prompt install) |
| **B. Home State block** (dynamic) | a `Home State:` block inside `aurora-context.md` | Regenerated nightly | **F5.2** renders it; the F-3a Filter injects it **unchanged** (AD-11/AD-20) |

The frame (A) teaches Aurora the objects, their baselines, the severity order, and
the rule "surface, never act." The block (B) carries the actual current state.
Aurora reads B through the lens of A. The 3 worked examples (§6) are layer B; the
proposed prompt text (§7) is layer A.

> **Design decision (confirmed at architecture approval):** live state stays out of
> the static prompt (delivered via the Filter, not baked into A) — the only form
> consistent with AD-02/AD-11 and with the F-1 principle that the prompt names
> domains *by intent*, not by implementation. Implementation of A (prompt install)
> and B (`aurora-context` render) are **separate later steps** (G-F5-07 install;
> F5.2) — neither is done here.

---

## 3. Design principles (from VISION + home_model.md)

- **Cognitive context, not an alert feed.** The Home State is read to *understand*
  and answer, not to notify. It is pulled at conversation start, not pushed.
- **Cognitive, not raw.** Object-level meaning ("3D printer on overnight"), never
  entity dumps or attribute values.
- **Silence is informative** (VISION §3). A healthy home renders `Attention: Nothing requiring operator action`
  — the absence of items *is* the message; no per-object roll-call.
- **Severity-first** (home_model.md §7 priorities). The most serious item is read
  first; low-priority maintenance never buries a critical signal.
- **Brief & honest** (VISION §6, §8). One clause per item; if the data is
  stale/unavailable, say so — never guess.
- **Surface, never act** (VISION §7). The Home State frames *what to tell Diego*,
  not *what to do*. Control happens only on an explicit in-scope request.
- **Privacy-aware.** Only the `home_model.md` operational core — no
  presence/occupancy, persons, or media/TV; no IPs or raw payloads (AD-18).
- **Deterministic & stable.** The same state always renders identical text; new
  objects slot in without changing the structure.

---

## 4. Layer B — the dynamic `Home State` block (F5.2 — implemented 2026-06-30)

### 4.1 Structure & ordering

A **stable two-level block** appended to the `[Aurora context — …]` block. Level 1
is the verdict; level 2 is the detail. The verdict is exactly one of **Healthy**,
**Degraded**, or **Unavailable**:

```
Home State:
<Healthy | Degraded | Unavailable>

<Attention: | Reason:>
<Nothing requiring operator action | bulleted items | one-line reason>
```

**Severity ordering (deterministic).** When `Degraded`, the `Attention:`
items are sorted by tier `critical → high → medium → low`; within a tier, the fixed
`home_model.md` §7 token order. Identical inputs ⇒ byte-identical output.

### 4.2 Empty-state behaviour (Healthy)

The healthy state is explicit and minimal (VISION §3 — silence made legible):

```
Home State:
Healthy

Attention:
Nothing requiring operator action.
```

No object is listed when healthy. The frame (§7) tells Aurora that `Healthy` /
`Attention: Nothing requiring operator action` means there is nothing to surface.

### 4.3 Degradation (Unavailable — RF5-3 / VISION §8)

If HA was unreachable at generation time, the state is honest and is **not** a
device anomaly:

```
Home State:
Unavailable

Reason:
Home Assistant unreachable at last context generation.
```

The frame instructs Aurora to say so plainly and offer `ha_get_state` for live
state. (Whole-context staleness is already handled by the Filter's 24–26 h
graduation; the Home State block needs no separate staleness logic.)

### 4.4 Anomaly presentation — token → human phrase (rendering map)

The JSON side stays the **AD-20 typed-token contract**
(`home.anomalies[]` = short snake_case tokens). The `Home State` block is the
**human rendering** of those tokens. F5.2 owns this 1:1 map (tokens from
`home_model.md` §7 — **unchanged**):

| Token | Tier | Rendered `Attention:` item |
|---|---|---|
| `zigbee_bridge_down` | critical | `[critical] Zigbee mesh down — Zigbee devices unavailable` |
| `wan_down` | high | `[high] internet (WAN) down` |
| `zigbee_permit_join_on` | high | `[high] Zigbee pairing left open (security)` |
| `printer_on_overnight` | medium | `[medium] 3D printer on overnight` |
| `awning_left_extended` | medium | `[medium] awning left extended overnight` |
| `door_open_extended` | medium | `[medium] main door open >15 min` |
| `plant_water_warning` | low | `[low] entrance plant needs water` |
| `plant_soil_dry` | low | `[low] entrance plant soil dry (<20%)` |
| `device_battery_low` | low | `[low] low battery: <device>` |
| `ha_unavailable` | n/a | (whole-block `Unavailable` — §4.3) |

`firmware_*` is intentionally **absent** — firmware is silent maintenance and
raises no token (home_model.md §6.9). The map is the single place a wording change
happens; tokens never change for wording.

---

## 5. Layer A — the static `# Home` prompt frame (G-F5-07 — installed 2026-06-30)

Compact (≈ 90–110 tokens added to the ~370-token F-1 prompt), placed adjacent to
`# Context`. Names objects **by intent + baseline** only — **no entity_ids** (same
principle as the F-1 corpus split: implementation names live in `home_model.md`,
not the prompt). **Installed text (G-F5-07, 2026-06-30) — applied byte-for-byte to
`params.system` as a new section after `# Context`; verified live in `webui.db` (see
the apply log):**

```
# Home

You monitor a defined set of home objects (full model: home_model.md).
Baselines: 3D printer off; awning retracted; Zigbee mesh connected;
main door closed; entrance plant watered; internet up. Answer about any
of these from baseline in one exchange; for live device state, ha_get_state.

The injected context block carries a "Home State:" section:
- "Healthy" (Attention: Nothing requiring operator action) → everything at baseline; nothing to surface.
- "Degraded" → the Attention list names each issue, most serious
  first. Surface what needs attention, briefly and by severity.
- "Unavailable" → say so plainly (a Reason is given); do not guess; offer
  ha_get_state for live state.

The Home State is cognitive context, not an alert feed. Surface home issues;
never act on them. Control the home only on an explicit in-scope request
(today: the 3D printer plug). The awning and the rest are read-only. Decide
nothing autonomously.
```

This satisfies G-F5-07: the prompt references the home model, carries the
baselines for single-exchange answers, and tells Aurora how to read layer B.

---

## 6. Worked examples (layer B)

### 6.1 Healthy home

`aurora-context.json` → `"home": {"anomalies": []}`

Injected block (full, for context):

```
[Aurora context — 2026-06-30 02:15 UTC]

Status:      ok

Ingest:      ok — last run 2026-06-30 00:30 UTC (1.7h ago, rc=0)
Backup:      ok — snapshot 2282b02e at 2026-06-30 01:00 UTC (1.3h ago)
Audit:       ok — last entry age 0 days
Containers:  17/17 running

Home State:
Healthy

Attention:
Nothing requiring operator action.
```

### 6.2 One anomaly

`"home": {"anomalies": ["printer_on_overnight"]}`

```
Home State:
Degraded

Attention:
- [medium] 3D printer on overnight
```

### 6.3 Multiple anomalies (severity-ordered)

`"home": {"anomalies": ["zigbee_bridge_down","wan_down","door_open_extended","plant_soil_dry"]}`

```
Home State:
Degraded

Attention:
- [critical] Zigbee mesh down — Zigbee devices unavailable
- [high] internet (WAN) down
- [medium] main door open >15 min
- [low] entrance plant soil dry (<20%)
```

### 6.4 Unavailable (degradation)

`"home": {"anomalies": ["ha_unavailable"]}`

```
Home State:
Unavailable

Reason:
Home Assistant unreachable at last context generation.
```

---

## 7. How the quality properties are met

| Property | How |
|---|---|
| **Compact** | fixed two-level block; healthy = verdict + `Attention: Nothing requiring operator action`; one short bullet per issue; no roll-call; no entity_ids in the prompt |
| **Deterministic** | one of three verdicts; fixed tier order + fixed within-tier token order; same input ⇒ identical text; fixed token→phrase map |
| **Privacy-aware** | only the operational core; no presence/occupancy, persons, media; no IPs/payloads (AD-18) |
| **Human-readable** | plain verdict words (Healthy / Degraded / Unavailable); natural object phrases ("entrance plant needs water") |
| **LLM-friendly** | a stable, labelled two-level block in the context Aurora already reads; easy to parse and summarise |
| **Stable across phases** | object-centric; new objects/tokens extend the §4.4 map and §5 baseline list without changing the block structure |

---

## 8. Future extensibility (reserved — not in F-5)

The two-level structure leaves room for the `home_model.md` §13 evolution
**without** breaking the layer A/B shape:

- **Relationships** — a down mesh can annotate dependent items ("(stale — mesh
  down)") instead of listing each separately.
- **Temporal / seasonal** — windows/thresholds change in `home_model.md`; the block
  structure is untouched.
- **Confidence scoring** — an optional suffix (e.g. `[medium·likely]`) can be added
  to an item without changing the parser.
- **Volume control** — if item counts ever grow large, a "top N + N more" collapse
  can be introduced under `Attention:`; out of scope now.

Any such change is gated future work and must not alter tokens, the
`home.anomalies[]` schema, or any AD without its own freeze.

---

## 9. Validation against AD-20, home_model.md, F5 architecture

| Contract | Check |
|---|---|
| **AD-20** — `home.anomalies[]` stays short typed tokens; schema preserved; no Filter change | ✅ tokens unchanged (§4.4 renders them; JSON carries tokens, §6); the block is human prose the existing Filter already injects verbatim — no Filter edit |
| **home_model.md** | ✅ objects, baselines, severity tiers and the 10 tokens are taken 1:1 from §5/§6/§7; firmware stays silent (§6.9); cover/toldo read-only (only the printer is controllable) |
| **§9-F-5** | ✅ "include any anomalies in `aurora-context.json` (`home.anomalies` array) and in `aurora-context.md`" — layer B; "system prompt … home model summary" — layer A (G-F5-07) |
| **AD-01/02/11** | ✅ dynamic awareness via the Filter over the pre-generated file; static frame in the prompt; no new awareness channel |
| **AURORA_VISION** | ✅ §3 silence informative (`Attention: Nothing requiring operator action`); §4 home state at baseline-deviation; §6 brief; §7 surface-not-act; §8 honest when Unavailable/stale |
| **Secret-safety (AD-18)** | ✅ no IPs, payloads, or credentials; object-level phrasing only |

---

## 10. Scope boundary of this document

**Design only.** Not changed here: the system prompt (`params.system`),
`bin/aurora-context`, the Filter, any tool, any code. Implementation is two later
gated steps — **G-F5-07** (install the §5 `# Home` frame) and **F5.2** (render the
§4 `Home State` block + `home.anomalies[]`). This document is the spec both must
match.

> **Status (2026-06-30):** the **G-F5-07** step (Layer A — install the §5 `# Home`
> frame into `params.system`) is **DONE + verified** — apply log
> [`../09_logs/2026-06-30_phaseF_F5_G-F5-07_applied.md`](../09_logs/2026-06-30_phaseF_F5_G-F5-07_applied.md).
> **F5.2** (Layer B — render the §4 block) is **implemented 2026-06-30** — apply log
> [`../09_logs/2026-06-30_phaseF_F5_2_applied.md`](../09_logs/2026-06-30_phaseF_F5_2_applied.md).
