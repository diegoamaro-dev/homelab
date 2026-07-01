# Apply Log — WM-1: World Model `_schema/` foundation

- **Date:** 2026-07-01
- **Phase:** WM-1 (World Model implementation, per **AD-21** —
  [`../04_ai_system/world_model_architecture.md`](../04_ai_system/world_model_architecture.md)
  §9 / §6-M1).
- **Scope:** schema documentation only — **no entities, no loader, no runtime.** Conforms to
  the frozen architecture (§4 format, §4.7 validation, §5 versioning). `schema_version: 1`.
- **Authoring model:** architect = an AI reasoning assistant; executor/documenter = an AI coding assistant.

---

## 1. What was created

| File | Purpose |
|---|---|
| `04_ai_system/world_model/README.md` | model index + Phase WM status |
| `04_ai_system/world_model/_schema/entity.schema.md` | **single operative contract** (fields, grammar, 11-check validation, versioning) — cites the frozen doc (R-WM1-1) |
| `04_ai_system/world_model/_schema/tokens.md` | canonical 10-token + severity registry (single source) |
| `04_ai_system/world_model/_schema/windows.md` | named windows (`overnight` = 00:00–06:00 Europe/Madrid) |
| `04_ai_system/world_model/_schema/archetypes/zigbee-device.md` | shallow archetype (`depends_on: [zigbee-mesh]`) |

Modified: `.gitignore` (ignore `world_model/**/*.generated.json` — the WM-3 artifact).

## 2. Validation (review-based — no loader yet)

| Gate | Result |
|---|---|
| **G-WM1-1** schema complete + no conflict with frozen §4/§4.7/§5 | ✅ all fields/enums, grammar (incl. duration), composition/archetype, versioning, 11 validation checks authored; cites the freeze |
| **G-WM1-2** token fidelity vs live source | ✅ the 10 tokens + tiers **exactly match** `home_state_design §4.4` and the live `HOME_RULES` in `bin/aurora-context` (read-only cross-check) |
| **G-WM1-3** window | ✅ `overnight` = 00:00–06:00 Europe/Madrid == live `0 <= hour < 6` |
| **G-WM1-4** archetype | ✅ shallow, one-level; `depends_on: [zigbee-mesh]`; firmware-silent + battery-per-device documented |
| **G-WM1-5** frozen §4.6 example conforms | ✅ `printer-3d` passes structural/grammar/token/window/enum checks; the `depends_on: zigbee-mesh` **referential** edge resolves at WM-3 once WM-2 authors `zigbee-mesh` (no loader/entities in WM-1) |
| **G-WM1-6** scope guard | ✅ no entities, no loader/code, no runtime; `.gitignore` ignores only the generated artifact |

## 3. Decisions

- **R-WM1-1 (operator-confirmed):** `entity.schema.md` is the **single operative schema
  contract**; it **cites** `world_model_architecture.md` (frozen) as authority and does **not**
  edit it. The frozen doc wins on any conflict.
- **Archetype reality-note (reality wins):** `unavailable → down` is **bridge-specific**
  (`zigbee-mesh` sets it), **not** a zigbee-device default (D7: ordinary devices never raise on
  `unavailable`). The frozen §4.4 illustration is a *format example*, not a normative archetype
  spec; the real archetype is authored faithfully. No frozen-doc edit.
- `schema_version: 1` established as the initial contract era.

## 4. Findings (deferred, not scope-crept)

- **F-WM1-a — collector registry.** The schema's validation check #7 ("every referenced
  `collector` exists") needs an enumerated set of valid collector ids (e.g. `ha-states`,
  `backup_status`, `container_status`, `health`). WM-1's operator-scoped deliverables did not
  include one; it is required before WM-3's coverage validation can run. **Deferred to WM-2/WM-3**
  (author a `_schema/collectors.md` or equivalent). Flagged, not created (in-scope discipline).

## 5. Scope guard — NOT done

No entity files (WM-2), no loader (WM-3), no `world_model.generated.json`. **Untouched:**
`world_model_architecture.md` (frozen), `home_model.md`, `HOME_RULES`/`bin/aurora-context`,
and all runtime, prompts, tools, containers, and collections. No secret in any artifact
(AD-18) — ids/tokens/window bounds are not secrets.

## 6. Rollback

Documentation-only, fully git-revertable: remove the `04_ai_system/world_model/` tree, revert
the `.gitignore` addition and the triad edits. No runtime state exists to unwind (no artifact
generated).

## 7. Next

**WM-2** — migrate `home_model.md`'s 9 objects → literate `home/` entities (frontmatter + prose
1:1; battery/firmware → aspects; no new facts), plus the `collectors.md` registry (F-WM1-a).
Planning-gated, as before.

## 8. Git

**STOPPED at the git gate.** No `git add`, commit, push, or tag. Reality always wins.
