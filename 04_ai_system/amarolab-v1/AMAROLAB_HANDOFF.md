# AMAROLAB_HANDOFF — Amarolab Assistant v1

Last updated: 2026-06-15

## Purpose

This file rebuilds **Amarolab Assistant v1 sub-project** context for any
future AI session without conversation history. For homelab-wide
context, see [`../../00_overview/AMAROLAB_HANDOFF.md`](../../00_overview/AMAROLAB_HANDOFF.md).

## Project purpose

Build a fully local AI assistant grounded by:

- Indexed homelab and product documentation (RAG over Qdrant).
- Live infrastructure state (containers, ports, volumes, disk).
- Home Assistant entity state and bounded control (Phase C, deferred).

Two front doors planned long-term: Open WebUI (chat) and Home Assistant
(voice). v1 is chat-only.

Constraints (non-negotiable):

- Single user (`diego`).
- Read-mostly. Write surface is narrow and per-tool allowlisted.
- Guardian Cloud is **production** — read-only RAG over its docs only.
  Never call its backend, never modify its source tree.
- Everything local. No external LLM calls. No public exposure of the
  assistant via Cloudflare in v1.

## Architecture summary

```
USER (LAN 192.168.178.0/24 / Tailnet)
   │
   ▼
Open WebUI :3000      ◄── chat UI + Tools runtime (Python)
   │
   ▼
Ollama :11434
   ├─ qwen2.5:7b-instruct  (primary, tool-calling, pulled 2026-06-15)
   └─ llama3:latest        (fallback non-tool chat)
   │
   ▼ (Open WebUI Tools — partial; scoped to qwen2.5:7b-instruct per D-20)
   ┌──────────────────────────────────────────────────────────────┐
   │ time_now()           — APPLIED (Phase A.3, 2026-06-15)       │
   │ rag_search()         — designed (Phase A.2); wired in Phase B│
   │ system_status()      — designed (Phase A.2); wired in Phase D│
   │ audit_search()       — Phase B                               │
   │ ha_get_state()       — Phase C                               │
   │ ha_call_service()    — Phase C (12-domain allowlist)         │
   └──────────────────────────────────────────────────────────────┘
   │
   ▼
Qdrant :6333  (API key enforced)
   ├─ homelab_docs     (86 chunks)
   ├─ guardian_cloud   (872 chunks)
   ├─ ensambla2        (419 chunks)
   ├─ myfreetour       (empty placeholder)
   └─ infra_audits     (Phase B)

Embedder:  intfloat/multilingual-e5-small  (384-dim, cached on host)
Reranker:  BAAI/bge-reranker-v2-m3         (top-6 ≥ 95% on bench)

Ingest: bare-metal venv, cron 02:30 daily, writes to Qdrant only.
```

## Current phase

**Phase A.4 — Open WebUI default model + system prompt v0
(design approved; no UI changes applied).**

- Phase A.1 (model pull + tool-calling smoke test) — **APPLIED**
  2026-06-15. See
  [`../../09_logs/2026-06-15_phaseA1-tool-calling-llm-applied.md`](../../09_logs/2026-06-15_phaseA1-tool-calling-llm-applied.md).
- Phase A.2 (three-tool design lock-in: `time_now`, `rag_search`,
  `system_status`) — **APPROVED** 2026-06-15 with 5 locked decisions
  (D-18..D-22 in [`ROADMAP.md`](ROADMAP.md)). See
  [`../../09_logs/2026-06-15_phaseA2-tool-layer-design.md`](../../09_logs/2026-06-15_phaseA2-tool-layer-design.md).
- Open WebUI 0.8.10 Tools API audit — **APPROVED** 2026-06-15. See
  [`../../FUNCTIONS_COMPATIBILITY_REPORT.md`](../../FUNCTIONS_COMPATIBILITY_REPORT.md).
  Four additional decisions locked (D-23..D-26).
- Phase A.3 (Open WebUI Tools scaffold + `time_now` canary) —
  **APPLIED** 2026-06-15. Source tree at
  `/home/diego/homelab/ai-stack/openwebui-tools/` (5 files);
  `time_now` Tool installed in `webui.db` (5180 chars, 1 spec);
  per-model scoping wired (`qwen2.5:7b-instruct` Model entry with
  `meta.toolIds=["time_now"]`); audit log live at
  `/srv/homelab/data/openwebui/amarolab-audit.log`. 19/21 V- checks
  PASS, 1 informational, 1 PASS. See
  [`../../09_logs/2026-06-15_phaseA3-tool-canary-applied.md`](../../09_logs/2026-06-15_phaseA3-tool-canary-applied.md).
- Phase A.4 (default model + system prompt v0) — **design APPROVED**
  2026-06-15 with 5 new locked decisions (D-27..D-31). No UI changes
  applied yet; default model still unchanged; system prompt not yet
  loaded. See
  [`../../09_logs/2026-06-15_phaseA4-default-model-and-prompt-design.md`](../../09_logs/2026-06-15_phaseA4-default-model-and-prompt-design.md).
- Phase B+ — not started.

## Mandatory reading order

For a future session resuming work, read in this order:

1. This file (`AMAROLAB_HANDOFF.md`).
2. [`CURRENT_STATE.md`](CURRENT_STATE.md) — live state of the sub-project.
3. [`ROADMAP.md`](ROADMAP.md) — phases, blockers, decisions taken.
4. [`README.md`](README.md) — design package overview.
5. [`01-current-state-review.md`](01-current-state-review.md) — pre-design state snapshot.
6. [`02-target-architecture.md`](02-target-architecture.md) — v1 target shape.
7. [`03-tools.md`](03-tools.md) — full tool catalog (superset of Phase A.2). **Read with the amendments banner at the top in mind**; Open WebUI 0.8.10's actual runtime contract is captured in §11 below.
8. [`04-security-and-permissions.md`](04-security-and-permissions.md) — trust model, allowlists, audit.
9. [`05-implementation-roadmap.md`](05-implementation-roadmap.md) — phase-by-phase plan with exit criteria.
10. [`../../FUNCTIONS_COMPATIBILITY_REPORT.md`](../../FUNCTIONS_COMPATIBILITY_REPORT.md) — **MANDATORY** for anyone implementing Tools. Source-grounded Open WebUI 0.8.10 contract: `class Tools`, JSON-Schema build, install path, valves, frontmatter.
11. Most recent log in [`../../09_logs/`](../../09_logs/) matching `*phase*-applied*.md` (applied work) and `*phase*-design*.md` (design lock-ins).

## Safety rules (Amarolab-specific)

The homelab-wide rules in
[`../../00_overview/AMAROLAB_HANDOFF.md`](../../00_overview/AMAROLAB_HANDOFF.md)
apply. The following are **sub-project additions**:

- **Guardian Cloud is production.** RAG read-only over its docs.
  Never write to `/mnt/storage/projects/guardian-cloud`. Never call its
  backend API.
- **Home Assistant is out of scope until Phase C.** No HA token, no HA
  calls, no HA tool code, no changes to HA configuration until Phase C
  is explicitly approved.
- **The LLM is adversarial input.** Tool argument allowlists are
  file-level Python constants. No `eval`, no `subprocess`, no
  path-from-arg, no shell building from arguments.
- **No new Open WebUI Tools are created** in `webui.db` until the
  user explicitly approves each sub-phase. As of 2026-06-15 the only
  Amarolab Tool installed is `time_now` (Phase A.3); canonical source
  at `/home/diego/homelab/ai-stack/openwebui-tools/tools/time_now.py`.
  `rag_search`, `audit_search`, `system_status`, `ha_get_state`,
  `ha_call_service` are designed only — not on disk as Tool files,
  not in `webui.db`. (Note: the v1 design package uses "Functions"
  loosely — Open WebUI 0.8.10's runtime term is **Tools**; see
  [`../../FUNCTIONS_COMPATIBILITY_REPORT.md`](../../FUNCTIONS_COMPATIBILITY_REPORT.md).)
- **Default model in Open WebUI must not be changed** without explicit
  user approval. Phase A.1 pulled `qwen2.5:7b-instruct` but did not
  set it as default.
- **Container changes are gated.** No new containers, no recreates of
  existing ones (openwebui, ollama, qdrant), no compose-file changes
  in this sub-project without explicit approval.
- **Secrets stay in `/home/diego/homelab/ai-stack/.env`** (mode 0600).
  Never paste secrets into design docs or status files; reference by
  env-var name only.
- **Audit-log path is fixed.**
  `/srv/homelab/data/openwebui/amarolab-audit.log` on host,
  `/app/backend/data/amarolab-audit.log` in container. Do not relocate
  without a security model update.

## Documentation rules

- **If it's not documented, it doesn't exist.** Inherited from the
  homelab-level rule.
- **Three files at this directory's root are live state:**
  `AMAROLAB_HANDOFF.md` (this file), `CURRENT_STATE.md`,
  `ROADMAP.md`. They are rewritten in place whenever facts change.
- **Design documents (01–05) are immutable for v1.** They describe
  what v1 *is*. Changes to that design go into a v1.1 / v2 package or
  into a new application log explaining the divergence.
- **Application logs are immutable and dated**:
  `YYYY-MM-DD_phaseX_name-applied.md` in
  [`../../09_logs/`](../../09_logs/). One per applied sub-phase.
- **Design reports (review-only, no application)** that occur between
  phases may live in the conversation only, or be committed as
  `YYYY-MM-DD_phaseX-design.md` if the user requests durability.
- **No secrets in any file in this directory.** References only
  (env-var names, paths to `.env`, never the value).
- **Sanitize before pushing to GitHub.** The homelab repo is
  synchronized; nothing under this directory should contain LLATs,
  API keys, or internal IPs that are not already in the design docs.
- **Cross-link with relative paths.** All references between docs in
  this sub-project use relative paths (e.g. `[`02-target-architecture.md`](02-target-architecture.md)`).
  Links to the rest of the homelab use `../../` prefixes.
