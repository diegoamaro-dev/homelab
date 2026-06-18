# AMAROLAB_HANDOFF — Amarolab Assistant v1 (AURORA)

Last updated: 2026-06-19 (reconciled — live-state sections replaced with
pointers to the overview triad; durable sub-project context retained).

## Purpose

Rebuilds **Amarolab Assistant v1 / AURORA sub-project** context for a future
AI session without conversation history. This file no longer carries live
state — for that, always defer to the overview triad:

- Live state: [`../../00_overview/CURRENT_STATE.md`](../../00_overview/CURRENT_STATE.md)
- Phase plan + status: [`../../00_overview/ROADMAP.md`](../../00_overview/ROADMAP.md)
- Homelab-wide rebuild: [`../../00_overview/AMAROLAB_HANDOFF.md`](../../00_overview/AMAROLAB_HANDOFF.md)

## Current phase — tracked in the overview

This file does not state the current phase (that is what went stale before).
See [`../../00_overview/ROADMAP.md`](../../00_overview/ROADMAP.md).

> Historical note: earlier revisions of this file declared "Phase B CLOSED /
> Phase C NEXT PHASE" and treated Voice as a deferred "Phase F". That framing
> is **obsolete** — Phase C (Home Assistant) closed 2026-06-17 and Voice
> shipped as Phase D-1 (closed 2026-06-18). Don't reconstruct phase state from
> a cached prior like that; use the overview ROADMAP.

## Project purpose (durable)

A fully local AI assistant grounded by:
- Indexed homelab + product documentation (RAG over Qdrant).
- Live infrastructure state (`system_status` remains a legacy Jarvis tool, not
  the originally-planned containerized service).
- Home Assistant entity state + bounded control — **delivered in Phase C**
  (was: "Phase C, deferred").

Two front doors, **both live** (was: "planned long-term"): Open WebUI
(chat + voice, `ai.amarolab.es`) and Home Assistant (voice, `ha.amarolab.es`).

Constraints (non-negotiable):
- Single user (`diego`).
- Read-mostly; write surface is narrow and per-tool allowlisted.
- Guardian Cloud is **production** — read-only RAG over its docs only; never
  call its backend, never modify its source tree.
- Everything local. No external LLM calls.

## v1 design package — reading map (durable)

For anyone implementing or auditing AURORA's tool layer:
1. [`README.md`](README.md) — design-package overview.
2. [`01-current-state-review.md`](01-current-state-review.md)
3. [`02-target-architecture.md`](02-target-architecture.md)
4. [`03-tools.md`](03-tools.md) — full tool catalog **and** the Open WebUI
   0.8.10 runtime contract (`class Tools`, JSON-Schema build, install path,
   valves). (The former standalone `FUNCTIONS_COMPATIBILITY_REPORT.md` is no
   longer in the repo; its contract lives here + in decisions D-23–D-26 / D-35.)
5. [`04-security-and-permissions.md`](04-security-and-permissions.md) — trust
   model, allowlists, audit.
6. [`05-implementation-roadmap.md`](05-implementation-roadmap.md) — design-intent
   phase plan (not executed status).
7. Locked decisions D-01…D-35 — [`ROADMAP.md`](ROADMAP.md).
8. Phase closeouts in [`../../09_logs/`](../../09_logs/): `*_phaseA_closeout.md`
   → `2026-06-18_phaseD1_closeout.md`, plus
   `2026-06-18_phaseRTX1_local_validation.md`. (These supersede the long
   per-log reading list from earlier revisions — each closeout summarizes its
   phase.)
9. Voice + HA design under [`phase-d/`](phase-d/) (01–06, incl.
   [`06-rtx-node-bridge.md`](phase-d/06-rtx-node-bridge.md)); RTX node under
   [`phase-rtx/`](phase-rtx/).

## Safety rules (Amarolab-specific, durable)

The homelab-wide rules in
[`../../00_overview/AMAROLAB_HANDOFF.md`](../../00_overview/AMAROLAB_HANDOFF.md)
apply. Sub-project additions:

- **Guardian Cloud is production.** RAG read-only over its docs. Never write to
  `/mnt/storage/projects/guardian-cloud`; never call its backend API.
- **The LLM is adversarial input.** Tool argument allowlists are file-level
  Python constants. No `eval`, no `subprocess`, no path-from-arg, no shell
  building from arguments.
- **Home Assistant control is bounded by the D-12 allowlist** (12 domains;
  explicit deny on `homeassistant.*`, `recorder.*`, `hassio.*`, etc.), enforced
  at the Tool boundary with audit logging and refusal paths. (was: "HA out of
  scope until Phase C — no HA token/calls/code" — obsolete; Phase C shipped.)
- **No new Open WebUI Tools** in `webui.db` without explicit per-tool approval.
  Live AURORA tools: `time_now`, `rag_search`, `audit_search`, `ha_get_state`,
  `ha_call_service`. Legacy Jarvis tools (`system_status`, `docker_*`) stay
  scoped to `llama3*` per D-20.
- **Default model, `meta.toolIds`, and `base_model_id = NULL` (D-35) are not
  changed** without explicit approval.
- **Secrets stay in `/home/diego/homelab/ai-stack/.env` (mode 0600) and
  `/home/diego/.secrets/*`.** Reference by env-var name only.
- **Audit-log path is fixed:** `/srv/homelab/data/openwebui/amarolab-audit.log`
  (host) → `/app/backend/data/amarolab-audit.log` (container).
- **Container / infra changes are gated** — no recreates, no compose changes,
  no new containers without explicit approval.
- **RTX node** is governed by [`phase-d/06-rtx-node-bridge.md`](phase-d/06-rtx-node-bridge.md):
  the UM790 stays the 24/7 node; Torre runs lean / headless (Lesson L-RTX-2).

## Documentation rules (durable)

- **If it's not documented, it doesn't exist.**
- **Live state is the overview triad** (`00_overview/`). The sub-project
  `CURRENT_STATE.md` (pointer) and `ROADMAP.md` (decisions overlay) are **not**
  rewritten per-phase anymore. (was: "Three files at this directory's root are
  live state … rewritten in place whenever facts change".)
- **Design documents 01–05 are immutable for v1.**
- **Application logs are immutable and dated:** `YYYY-MM-DD_phaseX_name-applied.md`
  in [`../../09_logs/`](../../09_logs/).
- **No secrets in any file. Sanitize before pushing to GitHub. Cross-link with
  relative paths.**
