# Phase F — F3.2 Apply Log: F-3b HA Voice Awareness Refresh

- **Date:** 2026-06-29
- **Step:** F3.2 (F-3b only — HA voice awareness). F-3a / F3.1 untouched.
- **Authority:** Reality is source of truth (PROJECT_RULES). Frozen spec:
  [`../04_ai_system/phase_f_architecture.md`](../04_ai_system/phase_f_architecture.md)
  §7, §9-F-3b, AD-13, §6.4. Scope constraint (operator, this session): treat the
  current HA voice prompt as the production baseline — append **only** the frozen
  awareness/Jinja line; **no** F-1 voice-identity restore or redesign (D2, out of scope).
- **Status:** Helper + prompt line + push script + 04:20 cron implemented and installed.
  **G-F3-8 PASS.** No git operations performed.

---

## 1. Implementation

Two surfaces are HA runtime state (not git); two are git-tracked.

- **Helper (HA config — `/srv/homelab/homeassistant/configuration.yaml`):**
  `input_text.aurora_voice_context` (`max: 255`; no `initial:` → restores the last
  pushed value across restarts). Loaded by the operator via Developer Tools → YAML →
  Reload Input Text (admin; no restart).
- **Voice prompt (HA `.storage`, Ollama conversation subentry `01KVB0A3…`):** the
  baseline 3-line prompt preserved **verbatim**; appended exactly one line —
  `Recent lab status: {{ states('input_text.aurora_voice_context') }}` (AD-13). Live
  prompt now 212 chars. Edited by the operator via Settings → Devices & Services →
  Ollama → Configure (admin options flow; no restart).
- **Push script (git, new):**
  [`../ai-stack/ingest/bin/push-voice-context`](../ai-stack/ingest/bin/push-voice-context)
  — Python; reads `ai-stack/aurora/aurora-context-voice.txt`; writes the line into the
  helper via HA REST `input_text/set_value`; length-guarded ≤255; fail-soft (logs +
  non-zero rc, never affects HA); `--dry-run`; reads `HA_BASE_URL`/`HA_LLAT` from
  gitignored `ai-stack/.env`; token never printed.
- **Cron (git source + installed copy):** 04:20 `push-voice-context` line added to
  [`../ai-stack/ingest/etc/cron.d/aurora-signals`](../ai-stack/ingest/etc/cron.d/aurora-signals)
  (after 04:15 `aurora-context`, §6.4); installed to `/etc/cron.d/aurora-signals`
  (root:root 0644) by the operator (sudo). First live fire: 04:20 tomorrow.

## 2. Validation — G-F3-8

Validation drives `/api/conversation/process` against `conversation.ollama_conversation`
— the **same agent + rendered system prompt the HA voice pipeline uses**; STT/TTS are
orthogonal to the awareness injection and unchanged by F-3b. `/api/template` is
admin-gated (401 for the non-admin token), so the conversation test is the injection proof.

| Check | Result |
|---|---|
| Helper exists (`max=255`), loaded | ✅ |
| Prompt contains the frozen Jinja ref (len 212; baseline preserved verbatim) | ✅ |
| Manual push (Step 5) | ✅ `http=200`, `rc=0` |
| Helper state == `aurora-context-voice.txt` | ✅ matches (timestamp / ok / backup ok / 17-of-17 / no anomalies) |
| Agent reflects status — direct probe | ✅ recited the exact data (`2026-06-29 10:38`, `ok`, backup `ok`, `17` running, `no anomalies`) — only knowable from the injected helper |
| Agent reflects status — natural probe | ✅ "Sí, todo está bien … sin anomalías" |
| Cron installed (04:20, root:root 0644) | ✅ |
| Token hygiene: `HA_LLAT` by-name only; `.env` gitignored; no secrets/artifacts staged | ✅ |

→ The first voice exchange of the day reflects the latest `aurora-context-voice.txt`
via the helper + Jinja2 (G-F3-8). The nightly push command is proven end-to-end (the
manual run is the identical command the cron runs); the 04:20 cron entry is installed.

## 3. Reproduction (AD-09 parallel)

The helper YAML + prompt line are HA runtime state (like
[`../04_ai_system/openwebui_model_runtime_state.md`](../04_ai_system/openwebui_model_runtime_state.md));
recorded here for reproducibility. Git-tracked: `push-voice-context` + the cron source.
- `configuration.yaml`: `input_text: { aurora_voice_context: { name: Aurora voice context, max: 255 } }`
- Ollama voice prompt: baseline + `Recent lab status: {{ states('input_text.aurora_voice_context') }}`

## 4. Deviations / decisions

1. **Privileged steps performed by the operator (not autonomous).** `HA_LLAT` is a
   non-admin token (admin endpoints → 401), so `input_text.reload` and the config edits
   could not be done with it; and there is no passwordless `sudo`. Helper reload +
   prompt edit (admin UI) and cron install (sudo) were operator actions. Everything else
   (config staging, script, cron source, push, validation) was autonomous. No HA restart
   was used (UI reload / options flow only).
2. **Minimal English label on the awareness line.** AD-13 specifies the Jinja
   expression; a short `Recent lab status:` label precedes it to frame the value for the
   model (the expression itself is unchanged; baseline language matched). D2 honored — no
   identity redesign.
3. **No `initial:` / no `default()` guard.** Pre-first-push the helper is `unknown` (prompt
   renders "Recent lab status: unknown"); resolved by the immediate Step-5 push. Residual:
   after an HA restart where state-restore fails, the line shows `unknown` until the next
   04:20 push — honest degradation; the value is self-timestamped. Accepted.
4. **F-1 HA voice identity remains the stock baseline** — separate maintenance item, out
   of F-3b scope per D2.

## 5. Rollback

- **Disable awareness (immediate, no restart):** operator removes the `Recent lab status:`
  line from the Ollama prompt (UI) → voice prompt returns to baseline; no injection.
- **Helper:** remove the `input_text` block from `configuration.yaml` + Reload Input Text.
- **Cron + script:** revert `ai-stack/ingest/etc/cron.d/aurora-signals` (git) and re-install
  the prior copy; `rm ai-stack/ingest/bin/push-voice-context` (untracked).
- No container / compose / `/opt/aurora` / Qdrant changes were made; nothing to revert there.

## 6. Next

F-3b implemented + G-F3-8 validated. **STOP — no git commit / push / tag** (operator gate).
Not started: **F3.3** (reconcile the overview triad + this doc's F-3 status to complete +
closeout log). Cron's first live fire is 04:20 tomorrow.
