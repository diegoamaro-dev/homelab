# Phase F — F3.1 Apply Log: F-3a Open WebUI Awareness Filter

- **Date:** 2026-06-29
- **Step:** F3.1 (F-3a only — Open WebUI Awareness Filter). HA Voice (F-3b) and
  F3.2 untouched.
- **Authority:** Reality is source of truth (PROJECT_RULES). Frozen spec:
  [`../04_ai_system/phase_f_architecture.md`](../04_ai_system/phase_f_architecture.md)
  §7, §9-F-3, AD-08..AD-13.
- **Status:** Filter implemented, installed, active+global, validated. G-F3-1 was
  initially partial; **CLOSED PASS after the operator-approved `# Context`
  precedence change + Open WebUI reload (see §9).** **All 7 behavioral gates pass.**
  No git operations performed.

---

## 1. Implementation

- **Filter source (committed-to-tree, AD-09):**
  [`../ai-stack/openwebui-tools/filters/aurora_context.py`](../ai-stack/openwebui-tools/filters/aurora_context.py)
  — `class Filter`; `inlet` injects on message 1 only (`len(messages)==1`, AF-01);
  reads `/opt/aurora/aurora-context.json` for the freshness decision and injects
  `aurora-context.md` (AD-10); ≤24h plain, 24–26h graduated note, >26h/missing →
  one-line fallback (§7); idempotency guard on the `[Aurora context` marker;
  never raises; one JSON log line per inlet decision to stdout.
- **Installer (Functions API, not Tools):**
  [`../ai-stack/openwebui-tools/bin/install_function`](../ai-stack/openwebui-tools/bin/install_function)
  — JWT auth (same as `install_tool`); `POST /api/v1/functions/create` (auto-detects
  `type=filter`) then ensures `is_active` + `is_global` via the toggle endpoints.
- **Docs:**
  [`../ai-stack/openwebui-tools/filters/README.md`](../ai-stack/openwebui-tools/filters/README.md)
  — install/recovery path for Functions (distinct from Tools).
- **Prompt tightening (surgical, one sentence):** `qwen2.5` `params.system`
  `# Context` now reads "…use it **on the first turn** to answer questions about
  current platform state, **and proactively mention any non-ok status it shows**…".
  Applied via raw `sqlite3` params-only UPDATE (meta.toolIds + base_model_id
  preserved; pre-edit row backed up). **Not loaded into the running process** — no
  container restart was performed (scope: no container modification). Live-status:
  pending an Open WebUI reload.

## 2. Install result

`./bin/install_function filters/aurora_context.py` → `action=create`,
`is_active=true`, `is_global=true`, `type=filter`. No container restart required
(activation immediate on toggle, per AF-01). `/opt/aurora` bind-mount (F-2) serves
the context; real `aurora-context.json` `overall_status=ok`, gen-age ≈3–5h during
validation.

## 3. Validation — Part A (deterministic filter logic, in-container unit test)

Real source exercised against fixtures (container has `pydantic`):

| Check | Gate | Result |
|---|---|---|
| fresh ≤24h → inject md, no note | — | ✅ |
| 24–26h → graduated note appended verbatim | **G-F3-5** | ✅ `[context is 25 hours old — use system_status…]` |
| >26h → fallback only | §7 | ✅ |
| missing/unreadable → fallback, no exception | **G-F3-4** | ✅ |
| message 2+ (3-msg body) → no inject (`event=skip`) | **G-F3-2** | ✅ |
| already-injected marker → no double-inject | **G-F3-2** | ✅ |
| degraded context → degraded text injected | (G-F3-3 input) | ✅ |

## 4. Validation — Part B (live, `/api/chat/completions`, filter active)

Note: Open WebUI REST returns tool **intent** for explicitly-passed tools without
executing them (G-F1-01 — REST does not auto-forward `meta.toolIds`); routing is
read from `tool_calls`, audit-log delta was 0 throughout (production audit clean).

| Gate | Probe | Result |
|---|---|---|
| **G-F3-2** | tool-loop follow-ups | ✅ filter `event=skip first_turn=false` on n=5/n=7 turns; injects only the 1-msg turn |
| **G-F3-3** | degraded block → answer | ✅ "estado … degradado … `zigbee2mqtt` detenido … consultar `system_status`" |
| **G-F3-6** | "¿…todo sigue bien **ahora mismo**?" | ✅ `tool_intents=['system_status']` (defers to live) |
| **G-F3-7** | routing w/ block present | ✅ hora→`time_now`, embeddings→`rag_search`, impresora→`ha_get_state` (3/3); `system_status` reachable (G-F3-6) |
| **G-F3-1** | "¿cómo está el lab?" | ✅ **PASS after §9** (precedence change); partial on first pass — see below |

**G-F3-1 detail.** With **no** tools offered, the filter-injected real ok block is
used accurately by the model: *"Ingest: ok (10.1h)… Backup: ok… Containers: 17/17…
puedes solicitar `system_status`"* — delivery + comprehension proven, no tool call.
With tools **offered** (the real UI condition), the 7B prefers a `system_status`
tool call instead of answering from the block. **Diagnostic:** adding a 2-sentence
precedence directive ("answer routine status from the [Aurora context] block; call
`system_status` only on explicit live/now") flips the model to `tool_intents=None`
and a correct block answer. → The "no tool call" objective is achievable but needs a
**stronger `# Context` precedence over `# Routing`**, which is **more than the
surgical one-liner** applied here, and must be **loaded** (reload).

## 5. Repro gate (AD-09)

Filter source + `install_function` + `filters/README.md` are in the working tree
(git commit deferred to F3.3 / operator approval). Recovery: restore `webui.db`
(R-12 snapshot) **or** re-run `install_function` from git.

## 6. Deviations from the frozen architecture (operator decisions)

*(Items 1–2 were RESOLVED this session — operator approved the change + reload; see §9.)*

1. **G-F3-1 needs a prompt-precedence change (KEY).** The frozen plan assumed the
   block + existing prompt would yield a no-tool-call status answer; reality shows
   the 7B calls `system_status` unless `# Context` explicitly takes precedence over
   `# Routing` for routine status. Proven fix wording exists (diagnostic). This
   exceeds the authorized surgical one-liner → needs operator approval (and likely
   a small frozen-doc note, since it touches the F-1 prompt strategy G-F3-1 relies on).
2. **Prompt tightening not loaded** — applied to `webui.db` but no restart performed
   (no-container-modification scope). Activating it (and any precedence change)
   needs an Open WebUI reload/restart — operator approval.
3. **G-F3-6 tested via tool intent, no real fault induced** — inducing a fault means
   stopping a container, excluded by scope. The pass condition (invokes
   `system_status` on explicit live-confirm) is demonstrated.
4. **`install_function` fix** — Open WebUI returns 401 for a missing function on the
   by-id route; existence is now checked via the list endpoint.

## 7. Rollback

- **Filter:** `POST /api/v1/functions/id/aurora_context/toggle` (deactivate) or delete
  via the Functions API; `webui.db` change only, no container/file impact.
- **Prompt:** restore `params` from the pre-edit backup
  (`scratchpad/qwen_model_row.pre_f31.json` captured this session) via the same
  `sqlite3` method.
- No container, compose, or `/opt/aurora` changes were made; nothing to revert there.

## 8. Next

G-F3-1 closed (§9); **F-3a complete**. Next: **F3.3** (reconcile the overview triad +
this doc's F-3 status + closeout + git) — operator-gated. Frozen-doc note for F3.3:
record that G-F3-1 depends on the `# Context` precedence directive. **STOP — no git
commit/push (F3.1 scope).**

## 9. Update — G-F3-1 closed (operator-approved `# Context` precedence + reload)

Operator approved a **`# Context`-only** precedence change (no other prompt change),
shown as an exact diff before applying. Applied via params-only `sqlite3` UPDATE
(the 3135 bytes before `# Context` preserved verbatim; `meta.toolIds` + `base_model_id`
intact; backup `scratchpad/qwen_model_row.pre_f31_ctx.json`), then
**`docker restart openwebui`** (operator-authorized reload; came back healthy).

`# Context` now reads: *"…answer routine status questions ('¿cómo está el lab?', 'is
everything OK?') directly from that block and do not call a tool; … call
system_status only when the user explicitly asks for live or right-now confirmation."*
This supersedes the earlier surgical one-liner.

Re-validation (tools offered; filter injecting the real ok block, `inject ok:5.2h`):

| Gate | Result |
|---|---|
| **G-F3-1** ×3 ("¿cómo está el lab?" + variant) | ✅ `tool_intents=None` all 3 — answers from the block (ingest 10.1h, backup `c38ddcc1`, 17/17), **no tool call** |
| **G-F3-6** ("…ahora mismo?") | ✅ `system_status` — still defers to live; cited block `10:38 UTC` then offered the live check |
| **G-F3-7** ("¿qué hora es?") | ✅ `time_now` — routing intact; precedence change caused no regression |

**All 7 F-3a gates pass.** Rollback for this change: restore `params` from the §9
backup via the same `sqlite3` method, then reload.
