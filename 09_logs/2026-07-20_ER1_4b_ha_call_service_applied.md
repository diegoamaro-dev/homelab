# ER-1.4b — `ha_call_service` v0.2.0 (resolution + ER-1-C1) applied (2026-07-20)

- **Phase:** ER-1.4b — the write cutover. **This is where ER-1 changes reality:**
  until now the 13 historical unverified writes would still be reported as
  successful. As of v0.2.0 they cannot be.
- **Spec:** [`../04_ai_system/entity_resolution_layer.md`](../04_ai_system/entity_resolution_layer.md) (Rev 4) §3.1, §4, §4.1, §5, §6.
- **Pre-registered protocol:** [`2026-07-17_ER1_4b_c1_measurement_protocol.md`](2026-07-17_ER1_4b_c1_measurement_protocol.md).
- **Prior:** [`2026-07-17_ER1_4a_ha_get_state_applied.md`](2026-07-17_ER1_4a_ha_get_state_applied.md).
- **Blast radius: the write path only.** A canonical `entity_id` reaches HA
  byte-identically to v0.1.0 (proven, §2); the resolver and C1 are additive.
  Nothing on the awareness path, loader, evaluator, artifact, or voice path is
  touched.

---

## 0. Rule B — ratified from the pre-registered measurement (2026-07-20)

The C1 measurement protocol was executed as ER-1.4b Step 2 (before implementing
C1), by direct REST against HA with the Tool out of the loop (real
`amarolab-audit.log` untouched). **N = 20 samples on `switch.impresora_3d`:**

| metric | value |
|---|---|
| first_read_hit (immediate read) | **0 / 20** |
| non-observation (> 10 s) | 0 |
| t_visible_ms  min / median / max | 52.3 / 53.7 / **158.7** |
| t_post_ms (POST round-trip) | 1.4 / 1.6 / 2.3 |

**Rule B applies** (predefined §4 table): not Rule A (0/20 immediate hits, never
20/20); not Rule C (max t_visible 158.7 ms « 2000 ms, zero non-observation, both
directions qualitatively identical). Mechanism, fixed in advance: check
immediately, then poll at **100 ms** within **budget = min(2000, max(500, 2 ×
158.7)) = 500 ms**; success on first match; budget exhausted ⇒
`applied_unverified`. The immediate read is stale because HA returns the POST in
~1.6 ms, before the Zigbee device echoes its new state back through Z2M → MQTT →
HA. Raw per-sample records: session scratch (`c1_samples.json` / `RESULTS.md`),
per the protocol §2.

## 1. Implementation

**Step 1 — v0.1.0 baseline captured** from the installed `webui.db` row before
the cutover (spec §6.2.1): `version 0.1.0`, sha256
`3ba8808e8729d878fd0a4e1d65f54bd76ee0dfb3e9bed2fe75e5ce095c526ab9`. See §4 for a
finding about that row.

**`tools/ha_call_service.py` → v0.2.0.** Both helpers inlined
(`# @@AMAROLAB_INLINE:audit_helper@@` + `# @@AMAROLAB_INLINE:entity_resolver@@`).
The spec §4 ladder, now with step 8:

| Step | Behaviour |
|---|---|
| 1 | D-12 domain allowlist — **UNCHANGED, first**, `refused` |
| 2 | Service validation — **UNCHANGED**, `bad_service` |
| 3 | entity_id bounded/type check — **UNCHANGED**, precedes resolution, `bad_entity_id` |
| 4 | Id-shaped ⇒ continue to HA exactly as today (D-ER-9). Registry consulted for **observability only** (`registry_target`, D-ER-14), never to gate |
| 5 | Else ⇒ normalize (D-ER-8) → closed lookup → hit substitutes the real id |
| 6 | Miss ⇒ `unknown_entity` + bounded candidates, **zero HTTP calls** |
| 7 | POST — **UNCHANGED** (spec §3.1: ER-1 changes neither when nor how a POST is issued) |
| 8 | **ER-1-C1** — after-only read-back (Rule B / 500 ms) → `ok`+`verified`/`state_after`, or `applied_unverified` |

Resolution slots exactly where the old id-shape rejection sat, so every preceding
check is untouched and the rate limiter sees the same inputs it saw before. New
private `_read_state()` performs the C1 read-back (underscore-prefixed, so Open
WebUI does not expose it as a tool — confirmed: the loaded row exposes only
`ha_call_service`). D-ER-10 closed expected-state map
(`turn_on→on`/`turn_off→off`/`open_cover→open`/`close_cover→closed`); every other
service (incl. `toggle`) ⇒ `applied_unverified`. `ha_response` is returned
verbatim but **no longer interpreted** (§3.1) — success is decided solely by the
read-back, so the empty-changed-list ambiguity is never entered. Root cause #2
fixed (the `light.kitchen`/`climate.lounge` docstring examples that taught
English-style guesses). `lib/audit_helper.py` / `lib/entity_resolver.py` are the
ER-1.4a versions, unchanged.

Installed to `webui.db` via `bin/install_tool` (`action=update`); the stored row
is byte-identical to the validated inlined artifact (modulo the dump's trailing
newline) and loads clean via Open WebUI's own `load_tool_module_by_id`.
`qwen2.5` `meta.toolIds` unchanged (still lists `ha_call_service`).

## 2. Validation (real evidence)

All probes ran with `AMAROLAB_AUDIT_LOG` at a scratch path; the real
`amarolab-audit.log` was **not touched** (verified 64 lines, last entry
`2026-07-17T14:53:37Z` — before this run — both before and after all probes). Logic /
byte-identity gates used a deterministic mock HTTP layer (incl. the defect's
"HTTP 200 + empty changed-list for a non-existent id"); G-ER-4 ran against real
HA. Paired v0.1.0 ↔ v0.2.0 where equivalence is asserted.

| Gate | Result | Evidence |
|---|---|---|
| **G-ER-2** determinism | **PASS** | 10 es+en phrases resolve, stable across 5 runs; 8 targets byte-stable |
| **G-ER-3a** unknown_entity | **PASS** | 5 non-id-shaped misses → `unknown_entity` + candidates, **zero HTTP**, audit line |
| **G-ER-3b** historical writes honest | **PASS** | all **7** non-existent ids (§1 defect): v0.1.0 `ok` (defect reproduced) → v0.2.0 `applied_unverified` |
| **G-ER-4** happy path (real HA) | **PASS** | `switch.impresora_3d` via exact id **and** alias `"impresora 3d"` → `ok`+`verified`, live C1 read-back (`state_after` on/off); baseline `off` restored; refusal + rate-limit unchanged |
| **G-ER-6** consumer half (write) | **PASS** | missing / corrupt projection ⇒ direct id works exactly as today; alias ⇒ `resolver_unavailable`, **zero HA calls** |
| **G-ER-7** write half | **PASS** | refusal / `bad_service` / `bad_service_data` / `bad_entity_id` / `entity_not_found` returns byte-identical; POST request byte-identical; audit pre-existing keys identical; successful write → `ok` + additive `verified`/`state_after` |
| G-ER-5 (no WM/awareness regression) | **confirmed** | untouched by ER-1.4b; loader **43** + evaluator **36** suites green |

## 3. Decisions of record

- **`applied_unverified` carries `ok: false`** *(implementation choice)*. v0.1.0's
  non-success returns omit `ok`; C1's honest non-claim states it explicitly so no
  reader mistakes it for success, alongside `result_code:"applied_unverified"` and
  a plain message.
- **`verified` + `state_after` are additive on both the return and the audit
  line** *(implementation choice; spec §4.1 mandates the code, is silent on these)*.
  They are the evidence G-ER-3b needs — an `ok` audit line now records *what state
  was actually confirmed*, ending the §1.2 indistinguishability at the source.
- **Non-mapped services (incl. `toggle`) ⇒ `applied_unverified` with no read-back**
  *(D-ER-10, faithful)*. Honest by construction: after-only verification has no
  expected state for them. On the real tree every actuatable entity
  (`switch.impresora_3d`, `cover.toldo`) uses a mapped service, so this is a
  theoretical path here.
- **C1 read-back reuses the initialised class client** and degrades to
  `applied_unverified` on any read failure — it never raises, never actuates, and
  never feeds awareness (INV-19).
- **`registry_target` threaded through every post-resolution audit line** (mirrors
  ER-1.4a) — additive; pre-existing keys stay byte-identical.

## 4. Discovered — recorded, not silently fixed

**The installed v0.1.0 `ha_call_service` row was a pre-2026-07-10 snapshot.** Its
`ha_call_service()` method body is byte-identical to the git source, but the row
carried (a) the **old** `audit_helper` (no `extra`) and (b) the pre-sanitization
comment `future Claude` (git: `future AI assistant`) — `ha_call_service` had not
been reinstalled since `lib/audit_helper.py` was updated at ER-1.4a nor since the
2026-07-10 history sanitization (`webui.db` is gitignored runtime state, not
rewritten by the git-history sanitization). **Not a deviation from the spec** —
the spec never claims git-reproducibility of the baseline; consistent with the
ER-1.4a rollback note. **Consequence, now resolved by the v0.2.0 install:** the
v0.1.0 → v0.2.0 diff legitimately includes the audit_helper old→new swap
(**required** — C1 stamps `registry_target`/`verified`/`state_after` via `extra`)
and the sanitization comment; G-ER-7 equivalence is therefore asserted on
**behaviour** (pre-existing result codes + HA-facing request byte-identical) — as
the gate is worded — and passed on that basis, not on raw file bytes.

## 5. Rollback

Reinstall the committed v0.1.0 source + `install_tool` (single `webui.db` row, the
**D-WM5-5** pattern); no restart needed. **Honest note: this restores the defect**
— v0.1.0 is the known-bad baseline whose writes claim unverified success. The
v0.1.0 row is reproducible from git as its method body (the audit_helper/comment
deltas of §4 are the ER-1.4a-current versions). `lib/`/`bin/` unchanged. No
database migration, container, cron, awareness, projection or artifact change.

## 6. Documentation reconciliation

Spec §10 updated: `ha_call_service.py` → **v0.2.0 (ER-1.4b, applied)**. Triad
reconciled: next milestone → **ER-1.5** (reconciliation + closeout); G-ER-2/3a/3b/4
+ G-ER-7 write half + G-ER-6 consumer-half write side recorded PASS; the write path
now reports honestly. Per *Transient Operational Status*, the sweep also clears the
markers this change's own publication leaves behind.

## 7. Status

**ER-1.4b COMPLETE (implementation + validation) — at the git gate (not
committed).** **Aurora's write path now verifies before it claims success:** the
13 historical unverified writes across 7 non-existent ids can no longer be reported
as successful (G-ER-3b), and a real actuation is confirmed by read-back
(G-ER-4). `ha_get_state` unchanged at v0.2.1. Remaining: **ER-1.5** (closeout).

No `git commit` / `push` / `tag` without explicit operator approval requested
immediately beforehand (`PROJECT_RULES.md` → *Operator Git Approval*).
