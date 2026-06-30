# Phase F — G-F5-07 Apply Log: static `# Home` prompt frame (Layer A)

- **Date:** 2026-06-30
- **Gate:** G-F5-07 — the system prompt references the home model; Aurora answers
  about any in-model object in a single exchange (baseline from the model; live via
  `ha_get_state`).
- **Scope:** **Layer A only** — install the static `# Home` frame defined in
  [`../04_ai_system/home_state_design.md`](../04_ai_system/home_state_design.md) §5
  into the Open WebUI `qwen2.5:7b-instruct` system prompt. **Layer B** (the dynamic
  `Home State:` block + `home.anomalies[]`) is **F5.2 — not started here.**
- **Authoritative design:** `home_state_design.md` §5 (installed byte-for-byte).
- **Runtime-state procedure:**
  [`../04_ai_system/openwebui_model_runtime_state.md`](../04_ai_system/openwebui_model_runtime_state.md).

---

## 1. Runtime change applied

The F-1 system prompt lives in **`webui.db` `params.system`** for the
`qwen2.5:7b-instruct` model row (Open WebUI 0.8.10 runtime state — **not** in git;
DB at `/srv/homelab/data/openwebui/webui.db`, bind-mounted into `openwebui`).

A new **`# Home`** section was added as the new final section **after `# Context`**,
copied byte-for-byte from `home_state_design.md` §5. The change is **append-only**:
the existing 3 532 chars are untouched — nothing reordered or reworded.

- **Placement:** after `# Context` (operator-approved). Rationale: `# Home` refers to
  the injected context block that `# Context` introduces, so it reads as a
  specialization; a pure append moves no existing section.
- **Size:** **3 532 → 4 478 chars (+946, +26.8 %).** ~99 on the design's own
  word-scale (§5 "≈90–110 tokens"); ~230–260 BPE tokens.
- **Section order (final):** Identity → Language → Tools → Routing →
  Behavioural policy → Style → Boundaries → Context → **Home**.

## 2. Backup

The full pre-change model row (`id, base_model_id, meta, params`) was captured to the
session scratchpad before the write:
`…/scratchpad/qwen_model_row.pre_g_f5_07.json` (session-ephemeral). Durable recovery
does **not** depend on it — see §6 (append-only reversal + nightly restic of
`webui.db`).

## 3. Params-only update

Mechanism: direct `sqlite3` `UPDATE model SET params=? WHERE id='qwen2.5:7b-instruct'`
(Python `sqlite3`, parameterised) — the same mechanism as F2-9 / F3.1.
**`meta` and `base_model_id` columns were never written**, so `meta.toolIds` (6 tools,
order preserved) and `base_model_id = NULL` (D-35) are preserved by construction.

Pre-write guards (abort on any surprise): live `params.system` == the analysed
3 532-char prompt; no pre-existing `# Home`; rebuilt prompt == the operator-approved
text. All three held.

## 4. Readback verification (on-disk, pre-restart)

| Check | Result |
|---|---|
| `params.system` == approved proposed text | PASS |
| `# Home` appears exactly once | PASS |
| `# Context` still present | PASS |
| `meta.toolIds` unchanged (6 tools, order preserved) | PASS |
| `base_model_id` remains NULL | PASS |
| Existing 3 532 chars preserved (append-only) | PASS |

## 5. Open WebUI restart + health check

- `docker restart openwebui` (operator-authorised reload).
- Container: `running`, **`health=healthy`**, `RestartCount=0` (clean, no crash loop),
  started `2026-06-30T13:53:38Z`. Startup logs clean (the `embeddings.position_ids
  UNEXPECTED` line is a benign, self-described "can be ignored" note).
- API probe: **`GET /api/version → HTTP 200`** (host `127.0.0.1:3000` → container `8080`).
- Post-restart DB readback (persistence across restart): `params.system` 4 478 chars,
  `# Home` ×1, `# Context` present, `base_model_id` NULL, `toolIds` unchanged.

## 6. Rollback

The change is append-only, so rollback is trivial and durable:

1. Set `params.system` back to the 3 532-char prefix (everything before the trailing
   `\n\n# Home`), or restore the full row from the §2 scratchpad backup, then
   `docker restart openwebui`.
2. DR fallback: restore `webui.db` from the nightly restic snapshot
   (`openwebui_model_runtime_state.md` §3) — recovers the entire model config.

## 7. Secret & git-tracking safety

- **No git-tracked runtime artifact committed.** `webui.db` is outside the repo
  (`/srv/homelab/data/openwebui/…`, not trackable by this repo); Aurora runtime
  artifacts (`ai-stack/aurora/`, `09_ops/runtime/`) are gitignored. The runtime change
  is confined to `webui.db`.
- **No secret committed.** The `# Home` text carries no IPs, tokens, or payloads
  (AD-18 — object-level phrasing only; `home_state_design.md` §9). This log quotes no
  secret and does not reproduce the full prompt (runtime state).

## 8. Remaining scope

- **F5.2 — Layer B (dynamic `Home State:` block + `home.anomalies[]`) — NOT STARTED.**
- `bin/aurora-context`, the F-3a Filter, and all tools — **unchanged**.
  **AD-20 unchanged.**
- This step installs + verifies **Layer A** (the prompt frame). The full G-F5-07
  behavioural acceptance (Aurora answering about in-model objects in one exchange,
  reading live `Home State`) completes once Layer B (F5.2) renders the block.

---

**Status:** G-F5-07 **Layer A implemented + verified.** Documentation reconciled
(`home_state_design.md`, `CURRENT_STATE.md`, `phase_f_architecture.md`).
**STOP at git gate** — operator review before any commit/push.
