# ER-1.4a — v0.1.0 baseline + `ha_get_state` v0.2.0 (applied 2026-07-17)

- **Phase:** ER-1.4a — the first cutover. The read path resolves natural language.
- **Spec:** [`../04_ai_system/entity_resolution_layer.md`](../04_ai_system/entity_resolution_layer.md) (Rev 3) §4, §5, §6
- **Prior:** [`2026-07-17_ER1_3_projection_applied.md`](2026-07-17_ER1_3_projection_applied.md)
- **Blast radius: the read path only.** `ha_get_state` now accepts natural names; a
  canonical `entity_id` behaves **byte-identically to v0.1.0** (proven, §2). `ha_call_service`
  is **untouched at v0.1.0** — the 13 historical unverified writes would still be reported as
  successful today. **ER-1 changes that at ER-1.4b**, when ER-1-C1 lands.

---

## 1. Implementation

**Step 0 — the v0.1.0 baseline, captured before the cutover** (spec §6.2.1: equivalence cannot
be demonstrated against a version already replaced). Two facts were established first:

- The repo source, inlined, is **byte-identical to the installed `webui.db` row** (modulo the
  dry-run's own trailing newline). The baseline is therefore reproducible from git, not merely
  observed once.
- The corpus was executed against the **installed row**, not the source file — the baseline is
  what Aurora actually ran.

**New — `ai-stack/openwebui-tools/lib/entity_resolver.py`** (inline-only, mirroring
`lib/audit_helper.py`'s convention because Open WebUI 0.8.10 executes each Tool in its own
`tool_{id}` namespace where imports do not resolve). Owns the D-ER-8 frozen normalization, the
closed alias lookup over `/opt/aurora/aurora-entities.json`, and the bounded candidate list.
Symbols are `_amarolab_er_`-prefixed so they cannot collide with the audit helper's in the
shared namespace.

Three properties are load-bearing:

- **A broken projection can never break a direct `entity_id`.** Every method degrades to
  "unavailable" rather than raising, so D-ER-9's pass-through holds unconditionally. Only the
  alias path depends on the resolver.
- **The projection is refused, not guessed at.** `projection_version` and the D-ER-8
  `normalization` stamp are hard pins. The loader stamps that string precisely "so a consumer
  can assert it shares this spec"; resolving against keys normalized under a *different* spec
  would return wrong ids silently — the exact class of quiet wrongness ER-1 exists to remove.
- **Cache keyed on `(mtime_ns, size)`.** The `openwebui` process is long-lived, so a cached
  copy would outlive a regeneration; re-reading when the stat key moves makes a manual
  `emit-entity-projection` run visible without a container restart.

**`tools/ha_get_state.py` → v0.2.0.** The spec §4 ladder, minus step 8 (reads need no C1 — HA
already answers 404 → `not_found` honestly):

| Step | Behaviour |
|---|---|
| 3 | Bounded/type check — **unchanged**, still first, still `bad_entity_id` |
| 4 | **Id-shaped ⇒ continue to HA exactly as today** (D-ER-9). Registry consulted for **observability only** (`modelled`), never to gate |
| 5 | Else ⇒ normalize (D-ER-8) → closed lookup → hit substitutes the real id |
| 6 | Miss ⇒ `unknown_entity` + bounded candidates, **zero HTTP calls** |

Resolution slots **exactly where the old id-shape rejection sat**, so every preceding check is
untouched and the rate limiter sees precisely the inputs it saw before: an input that never
reached HA never reached the limiter at v0.1.0 either.

**Root cause #2 fixed.** The docstring's `light.kitchen` / `climate.lounge` examples taught
English-style guesses at a device really named `impresora_3d`. v0.2.0 teaches the *shape*
(pass the name the user said; a canonical id also works) and names the failure mode
explicitly. It deliberately does **not** enumerate the alias set — that would duplicate the
registry in prose and go stale; the `unknown_entity` + `candidates` loop is the design's own
corrective feedback (root cause #3).

**`bin/install_tool` — generalised.** A single hardcoded `audit_helper` marker became name
resolution: `# @@AMAROLAB_INLINE:<name>@@` → `lib/<name>.py`, several per Tool. Substitution
uses a replacement **function**, never a replacement string: helper blocks contain backslashes
(regex literals, the D-ER-8 spec string) that `re.sub` would otherwise read as group
references.

**`lib/audit_helper.py` — additive `extra`.** Spec §4 mandates the audit line record
`modelled`, and the helper is the only audit writer. `extra` merges **after** the fixed keys,
so names, values and serialized order are untouched and a caller passing no `extra` produces a
byte-identical line. `modelled` deliberately does **not** go in `args`, which is a snapshot of
what the caller passed and must stay that. *(An implementation-inventory correction — see §6.)*

---

## 2. Validation (real data)

All probes ran with `AMAROLAB_AUDIT_LOG` pointed at a scratch path via the helper's own
documented override. **The real `amarolab-audit.log` was not touched** — verified after all
work: 63 lines, last entry `2026-07-16T20:44`. That is not fastidiousness: the log is ER-1's
own evidence base (§1) and F-4's accruing digest evidence, and ~60 synthetic probes would have
polluted the corpus that G-ER-3b must re-measure at ER-1.4b.

**D-ER-8 parity — the core correctness claim.** The resolver's normalizer is **byte-identical**
to `_loader/resolution.py`'s across 46 real + adversarial cases (accents, case, `.`/`_`/`-`
separators, whitespace, empty). All **33** authored aliases resolve to the key the loader
emitted. The two normalization spec strings match exactly. This matters because the loader
produced the keys the resolver looks up: parity is what makes the lookup meaningful rather
than coincidental.

**G-ER-7 (read half) — PASS.** Baseline vs v0.2.0 over the §6.1 corpus, 18 cases. **Every
difference falls in an enumerated intentional-change class; there are no unenumerated
differences.**

| Class | v0.1.0 | v0.2.0 | Verdict |
|---|---|---|---|
| Real entities (`switch.impresora_3d`, `sun.sun`, `cover.toldo`, `binary_sensor.sensor_puerta_principal_contact`) | `ok` | `ok` | **byte-identical** |
| Id-shaped, non-existent (`switch.3d_printer`, `cover.awning`, `light.kitchen`) | `not_found` | `not_found` | **byte-identical** — the read path was already honest |
| Length bound (`x`) | `bad_entity_id` | `bad_entity_id` | **byte-identical** |
| Non-id-shaped (`coverawning`, `light.`, `not_a_valid_id_no_dot`, `LIGHT.KITCHEN`, `3dprinter.status`) | `bad_entity_id` | `unknown_entity` + 8 candidates | **enumerated intentional change** |
| Aliases (`toldo`, `impresora 3d`, `puerta principal`, `Conexión a Internet`, `3D printer`) | `bad_entity_id` | `ok`, resolved | **the new capability** |

Audit lines: no pre-existing key removed, `args` never polluted, `modelled` / `resolved_to`
purely additive. On the alias class `allowed` moves `false → true` — correct: v0.1.0 rejected
those inputs, v0.2.0 makes a real call.

**A wrong hypothesis, corrected by measurement.** The first comparison showed `sun.sun`'s
`last_updated` differing between the two runs. The reflex explanation — "the sun ticks every
~30 s" — was **tested and disproved**: two v0.1.0 runs 12 s apart returned the identical
value, and HA queried directly twice 90 s apart did too. The real cause was that HA updated
`sun.sun` once, at `13:09:35`, *between* two probe runs 6.5 minutes apart; querying HA
directly with the tool out of the loop returned exactly what v0.2.0 had reported. Settled
properly by a **paired A/B run** — v0.1.0 and v0.2.0 back-to-back per entity, milliseconds
apart, volatility controlled rather than argued: **byte-identical across the whole
backward-compat corpus, `sun.sun` included.** Recorded because an assumed explanation that
happens to reach the right verdict is still an unverified claim, which is the defect class
this phase exists to remove.

**G-ER-6 (consumer half, read side) — PASS.** Rehearsed against **scratch copies** via
`AMAROLAB_ENTITY_PROJECTION`; the real projection was never touched (verified byte-identical
afterwards). The primary assertion held in **every** scenario:

| Scenario | Direct `entity_id` | Alias |
|---|---|---|
| Control (good) | identical to v0.1.0 | `ok` → `cover.toldo` |
| Missing · corrupt · empty aliases | identical to v0.1.0 | `resolver_unavailable` |
| `projection_version` mismatch · normalization mismatch · non-id-shaped target | identical to v0.1.0 | `resolver_unavailable` |
| **Stale** | identical to v0.1.0 | `ok` — stale registry **used** |

The stale row is the honest one: per spec §9 a tool **cannot** compute freshness (the
container mounts only `/opt/aurora` and `/opt/ingest`; the artifact is not visible), so a
stale-but-valid projection is used and degrades **alias resolution only**. That is the
documented, accepted residual risk — not a gate failure. The write half of G-ER-6 closes at
ER-1.4b.

**End-to-end through Open WebUI's own loader.** Final confirmation ran via
`load_tool_module_by_id('ha_get_state')` — the production path, not a harness import:
frontmatter `0.2.0`, aliases resolving, `unknown_entity` offering candidates, `not_found` and
`bad_entity_id` preserved. `replace_imports` was checked and rewrites **nothing** in this
content, so the stored row is stable. No container restart is required: the loader builds a
fresh module per call.

**Printer baseline `off` throughout** — reads do not actuate. The §6.2.2 window constraint did
not bind (all work at ~15:00–15:15 CEST, outside `00:00–06:00`).

---

## 3. Decisions of record

- **`modelled` is omitted, never `false`, when the resolver is unavailable** *(ratified
  2026-07-17)*. "The registry does not list this id" and "the registry could not be read" are
  different facts; recording the second as the first would put an unverified claim in the
  audit log — precisely ER-1's defect class. `is_target()` returns `None` and the key is
  dropped.
- **`resolved_to` on an alias hit** *(implementation choice, not architectural)*. Without it
  `args.entity_id` reads `"toldo"` and no auditor could tell which entity was actually read —
  the §1.2 indistinguishability defect, reintroduced through the front door. Additive; the
  spec mandates `modelled` and is silent on this.
- **The docstring teaches the shape, not the alias set** *(implementation choice)*. Enumerating
  33 aliases in prose would duplicate the registry and go stale; `unknown_entity` + candidates
  is the design's own feedback loop.
- **Registry integrity guard** *(defence in depth)*. A resolved id is interpolated into an HA
  URL path, so a corrupted projection could smuggle traversal into it. Every alias target is
  id-shape-checked at load; a violation ⇒ `resolver_unavailable`. Unreachable against a
  projection this platform emits (the loader's check 12 validates ids long before the
  artifact), and kept regardless — the ER-1.3 precedent for `resolution.build()`'s guard.
- **`extra` merges after the fixed keys** *(implementation choice)*. Preserves byte-identity of
  pre-existing audit fields, including serialized order.

---

## 4. Discovered — recorded, not silently fixed

**F-ER14-1 — the audit field `modelled` asserts more than it verifies.** Spec §4 step 4 names
the field, and its own sentence scopes it ("Registry consulted … audit records `modelled`"),
so this implementation is faithful to the freeze. But the **name** claims *"the World Model
models this entity"* while the field actually answers *"this id is a target in the resolution
registry"* — and those differ, provably:

> `sun.sun` → `modelled: false`, while `environment/daylight-time.md` line 9 reads
> `binding: { ha_entity: sun.sun }`. The World Model demonstrably models `sun.sun`; it is
> simply **unaliased**, so it is not a resolution target. The registry holds only the aliased
> signals of bound entities (**D-ER-6**).

Not cosmetic: ER-1 exists partly because *"the audit log cannot presently distinguish a real
actuation from an unverified write"* (§1.2). A field whose name overstates what was checked is
the same defect in a new place — a future auditor asking *"which calls hit entities we don't
model?"* would mis-classify `sun.sun`. The value is small today (one entity) and structural
tomorrow (every modelled-but-unaliased entity, and ER-1.4b will stamp this field on **writes**).

**Not fixed.** The name is in the frozen spec, and D-ER-11 / D-ER-12 / D-ER-13 set the
precedent exactly: implementation surfacing a gap in a frozen rule is **recorded** for
operator ratification, never self-approved (ER-1.3: *"recorded it instead of self-approving a
change to a frozen check"*). Options at ratification: rename (`registry_target`,
`resolvable`), or keep `modelled` and define it precisely in §4. **A decision is wanted before
ER-1.4b**, because that is when the field starts describing actuation rather than reads. The
precise scope is documented at the point of use in `lib/entity_resolver.py`
(`is_target.__doc__`), so the trap is stated where a reader meets it.

*(The user-facing `"is not an entity I model"` string is out of this finding's scope: it is
AD-21 §7's own ratified phrasing, and for a name miss no entity of that name is resolvable.)*

---

## 5. Rollback

Reinstall the committed v0.1.0 source + `install_tool` (single `webui.db` row — the **D-WM5-5**
pattern); no restart needed. **Honest note: this restores root cause #2** — v0.1.0 is the
known-bad baseline whose docstring teaches invented ids. The v0.1.0 row is reproducible from
git (proven in §1), so the rollback target is exact rather than remembered.

`lib/` and `bin/` changes are inert on their own: the other four tools carry their own inlined
snapshot in `webui.db` and are unaffected until re-installed, and `extra` defaults to `None`.
No database migration, no container change, no cron change, no awareness path touched, no
projection or artifact write. `ha_call_service` is untouched.

---

## 6. Documentation reconciliation

Spec §10 inventory corrected against the implementation — an **implementation-inventory
correction, not an architectural decision** (the ER-1.2 precedent; §3's register is unchanged):

- **`lib/audit_helper.py` added** — the `modelled` field §4 mandates has no other writer.
- **`lib/entity_resolver.py`, `bin/install_tool`, `tools/ha_get_state.py`** — as listed.
- `tools/ha_call_service.py` and `bin/install_tool`'s marker generalisation remain listed for
  ER-1.4b; the harness change lands here because `ha_get_state` is the first Tool to need two
  markers.

Triad reconciled: next milestone → **ER-1.4b**; G-ER-7 read half + G-ER-6 consumer half (read
side) recorded; F-ER14-1 added as a pending item. Per *Transient Operational Status*, the sweep
also clears the markers this commit's own publication would otherwise leave behind.

---

## 7. Status

**ER-1.4a COMPLETE (implementation + validation) — at the git gate.** **G-ER-7 read half PASS**
· **G-ER-6 consumer half (read side) PASS** — write halves open at ER-1.4b. G-ER-1 / G-ER-2 /
G-ER-5 / G-ER-6 producer half unchanged. **F-ER14-1 recorded, awaiting operator ratification
before ER-1.4b.**

**Aurora's read path now resolves natural language**; `ha_call_service` remains v0.1.0, so the
13 historical unverified writes would still be reported as successful today. **ER-1 changes
that at ER-1.4b**, when ER-1-C1 lands.

No `git commit` / `push` / `tag` without explicit operator approval requested immediately
beforehand (`PROJECT_RULES.md` → *Operator Git Approval*).
