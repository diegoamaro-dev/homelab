# ER-1.4b — C1 read-back measurement protocol (pre-registered 2026-07-17)

- **Phase:** ER-1.4b, Step 2 — measure POST → state-visibility latency **before** implementing
  ER-1-C1 in `ha_call_service` v0.2.0.
- **Spec:** [`../04_ai_system/entity_resolution_layer.md`](../04_ai_system/entity_resolution_layer.md)
  §3.1 (after-only verification), §9 (latency), §6.2.2 (execution window).
- **Status:** **PRE-REGISTERED** — authored and committed **before any measurement is taken**.
  The immediate-read vs bounded-retry choice is decided **only** by the rules in §4 below,
  never from the observed outcome (operator direction, 2026-07-17). Results are recorded in
  the ER-1.4b apply log, which cites this document. Once committed this document is
  historical (`PROJECT_RULES.md` → Historical Documentation): it is not amended by results,
  and any protocol deviation must be recorded in the apply log as a deviation.

---

## 1. Question, and why it is asymmetric

ER-1-C1 is **after-only** (§3.1): the tool POSTs exactly as today, then reads back
`/api/states/<entity_id>` and compares against the D-ER-10 expected state. If HA's state
visibility lags the POST return — plausible for a Zigbee device behind Mosquitto + Z2M, where
state may confirm only after the device echoes — an immediate read-back sees the stale state
and reports **`applied_unverified` for a real actuation**. That is honest but fails **G-ER-4**
and the **G-ER-7 write half**: the 7 historical real `switch.impresora_3d` writes must remain
`ok`.

**The asymmetry, stated up front:** a too-short verification window can only **under-claim**
(`applied_unverified` for a write that really landed). It can never produce a false success —
`ok` + `verified` requires the expected state to have actually been read back. Measurement
therefore tunes the false-under-claim rate; **correctness does not depend on it**.

**Why measure instead of always retrying:** a retry budget must itself come from data — a
guessed budget is the same reflex the ER-1.4a log §2 records and disproves — and if Rule A
holds, the simpler mechanism wins (`PROJECT_RULES.md` → Infrastructure Philosophy: simple over
clever).

## 2. Subject and harness

- **Subject:** `switch.impresora_3d` (Sonoff S60ZBTPF via Mosquitto + Z2M) — the entity
  G-ER-4 / G-ER-7 actuate. **`cover.toldo` is not actuated:** no gate requires it, and cover
  travel time makes `open`/`closed` unreachable within any sane read-back window — C1 on
  covers will simply answer `applied_unverified` honestly if read-back lands mid-travel;
  recorded in the apply log as accepted behaviour, not measured here.
- **Harness:** direct REST against HA using the platform credentials (`HA_BASE_URL` /
  `HA_LLAT`), from the UM790 — the same LAN position as the tool's container (sub-ms
  difference). **The Tool is not in the loop:** no audit lines are produced and the real
  `amarolab-audit.log` is untouched. Raw per-sample records are preserved as scratch
  artifacts referenced by the apply log.
- **Constraints:** run outside `00:00–06:00 Europe/Madrid` (§6.2.2); printer baseline `off`
  restored at the end (G-5 pattern); **abort** on any non-2xx POST, or if any pre-read shows
  `unavailable` — an aborted run is investigated, not counted.

## 3. Samples

- **N = 10 cycles → 20 samples** (10 per direction).
- **Cycle:** pre-read confirming `off` → POST `switch.turn_on` → poll GET at **50 ms** until
  `on` → POST `switch.turn_off` → poll at 50 ms until `off` → **5 s settle** before the next
  cycle (kind to the relay and the attached printer PSU; total runtime ≈ 2–3 min).
- **Validity:** every sample must start from a **confirmed opposite state** — a no-op
  transition measures nothing. Observation window **10 s** per sample; expected state never
  observed within it ⇒ Rule C.
- **Per-sample record:** direction, `t_post_ms` (POST round-trip), `first_read_hit` (expected
  state on the **very first** GET, issued immediately on POST return — this is what an
  immediate-read C1 would see), `t_visible_ms` (POST return → first GET showing the expected
  state), poll count, and whether the POST's changed-states list carried the entity
  (secondary observable; the decision rules never read it).
- **Statistical power, stated honestly:** 20 samples detect a first-read-miss mechanism of
  ≥ 14 % incidence with ≥ 95 % confidence ((1 − 0.14)²⁰ < 0.05). Rarer misses are covered by
  the §1 asymmetry: the failure direction is an honest under-claim, never a false success.

## 4. Decision rules (predefined — the only admissible basis for the choice)

| Rule | Condition (measured) | Consequence (implemented) |
|---|---|---|
| **A — immediate read** | `first_read_hit` in **20/20** samples | C1 = single read-back, no retry loop |
| **B — bounded retry** | ≥ 1 first-read miss **and** max `t_visible` ≤ **2000 ms** | C1 = check immediately, then poll at **100 ms** within **budget = min(2000, max(500, 2 × max observed `t_visible`)) ms**; success on first match; budget exhausted ⇒ `applied_unverified` |
| **C — escalate** | any `t_visible` > 2000 ms, any 10 s non-observation, or qualitative inconsistency between the two directions | **STOP** — bring the data to the operator. A confirmation lag that large makes honest verification a latency/architecture decision, not an implementation choice |

Rule B constants, fixed now: **2×** is margin over the worst observed; the **500 ms floor**
guards against an unrepresentatively fast run; the **2000 ms cap** bounds worst-case added
tool latency well below the +5 s worst case §9 already accepts. Under Rule B the fast path is
identical to Rule A — the first check is immediate and the loop only waits when that check
misses.

Neither mechanism changes **when** the POST is issued (§3.1). Neither consults the registry to
gate (D-ER-9).

## 5. Interpretation boundary

This protocol characterises `switch.impresora_3d` — the only entity the write gates actuate.
The chosen mechanism applies to all D-ER-10 verifications; entities with intrinsically slow
confirmation (covers in travel) fall through to `applied_unverified` honestly, by
construction. No fabricated failures, no synthetic devices — the gates close on this real
device or not at all.
