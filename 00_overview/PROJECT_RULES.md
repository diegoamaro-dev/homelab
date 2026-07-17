# PROJECT_RULES

Last updated: 2026-07-17

---

# Purpose

This document defines the permanent operating rules for the AMAROLAB project.

Unlike CURRENT_STATE.md, this file is intentionally stable.
It contains principles, constraints and working rules that
apply across all project phases.

Operational status belongs in CURRENT_STATE.md.

---

# Core Principle

Reality always wins.

If reality and documentation disagree:

1. Reality is correct.
2. Documentation must be updated.
3. Never force reality to match outdated documentation.

---

# Documentation Rules

Documentation is part of the implementation.

Implementation is not considered complete until it is:

1. Working
2. Understood
3. Sanitized
4. Documented

If it is not documented, it does not exist.

---

# Validation Rules

Never assume.

Every significant change must be validated using:

- Real commands
- Real logs
- Real outputs
- Real state changes

Documentation follows validation.

Never the opposite.

---

# Security Rules

Never expose:

- Passwords
- Tokens
- API Keys
- Cookies
- Private Keys
- Live .env files
- Secrets of any kind

Always sanitize documentation before committing.

Examples:

```
<PASSWORD>
<TOKEN>
<PRIVATE_IP>
<TAILSCALE_IP>
<HOSTNAME>
```

---

# Git Rules

Always inspect before committing.

Minimum workflow:

```bash
git status
git diff
git add <specific files>
git commit
git push
```

Never use:

```bash
git add .
```

unless every modified file has been reviewed.

Commits are operational documentation.

---

## Operator Git Approval

No AI assistant may run any of the following commands without
**explicit operator approval immediately before the command**:

```bash
git commit
git push
git tag
```

Approval is per-command and per-moment. Approval of one
command does **not** authorize the next, and approval given in
a previous step, phase or session **never** carries over. Each
of the three commands requires its own fresh approval,
requested immediately beforehand.

### Required workflow

1. Plan
2. Implementation
3. Validation
4. Documentation
5. Documentation audit
6. Git review
7. **STOP** — request operator approval before commit
8. Commit only after approval
9. **STOP** — request operator approval before push
10. Push only after approval
11. **STOP** — request operator approval before tag
12. Tag only after approval
13. Push tag only after approval
14. Confirm remote synchronization

This rule is binding on every AI assistant
acting on this repository.

---

# Architecture Rules

Architecture documents describe deployed reality.

Future ideas belong in:

- ROADMAP.md
- DRAFT documents

Never document future architecture as if it already exists.

---

# Hardware-Agnostic Platform

**AMAROLAB is a hardware-agnostic platform.**

```
Aurora must never depend on specific hardware.
Aurora depends on capabilities.
Hardware provides capabilities.
```

A **capability** is something Aurora needs done (generate a reply, transcribe speech, embed
a document). A **provider** is a thing that does it. Aurora names the first and never the
second.

Rules:

1. **Aurora requests capabilities, never hardware.** No hostname, IP, GPU vendor,
   accelerator name or machine nickname belongs in a tool, a prompt, the World Model, or an
   awareness artifact. Hardware identity is legitimate in exactly two places: the provider
   selection layer, whose job is to know, and documentation, whose job is to describe.

2. **Hardware is an interchangeable implementation provider.** Providers may differ in
   **speed, availability and cost**. They must **never differ in meaning**. Two
   providers are interchangeable only if their outputs are equivalent for Aurora's purpose —
   established on real data before use, never assumed from a shared API. A substitution that
   changes what Aurora *means* is not a fallback; it is a silent behaviour change.

3. **Infrastructure upgrades must extend Aurora, never redesign Aurora.** New infrastructure
   is added by **registering a capability provider** — never by modifying Aurora. Migration
   is a policy change; rollback is repointing selection. **If a hardware change forces an
   edit to a tool, a prompt, the World Model or a schema, the architecture is wrong, not the
   hardware** — that edit is the defect signal.

4. **Provider selection must support automatic evolution.** Selection must be able to take
   advantage of better hardware without Aurora being told: an equivalent, local, faster
   provider should simply be preferred once registered. **Bounded to one fidelity tier** —
   selection may automatically become *faster*, never automatically *different*. A
   materially better or worse model is an operator decision on measured evidence, never a
   side-effect of a machine appearing.

5. **No provider, no invention.** Where an equivalent provider is unavailable, degrade
   honestly or fail loud. Never substitute across fidelity tiers to manufacture an answer —
   that trades a visible outage for an invisible behaviour change. Every capability Aurora
   depends on has an always-on provider, or Aurora does without it honestly.

6. **This rule grants hardware independence, not trust-boundary independence.** The two are
   different axes; this rule moves only the first. **Compute providers may evolve freely;
   they must remain inside the AMAROLAB trust boundary.** Aurora is **local-first** and this
   rule does not touch that: *Everything local. No external LLM calls.* stands unaffected.
   Inside the boundary: operator-controlled nodes — UM790, RTX workstation, NAS AI nodes,
   Jetson, Ryzen AI, Apple Silicon, future NPUs, and operator-controlled remote nodes reached
   over the AMAROLAB private network (VPN / Tailscale). **Excluded: third-party cloud
   inference providers** — not because they are unanticipated hardware, but because they are
   **not a hardware question at all**. The trust boundary is the **first filter on
   candidates, never a preference**, and is never traded for speed. **Changing the trust
   boundary is a separate architectural decision; this rule must never be cited as its
   justification.**

**Why.** Hardware is the most volatile layer AMAROLAB has; Aurora's tools, prompts, World
Model and knowledge are the most durable. Coupling them lets the volatile layer destabilise
the durable one, and makes every upgrade a risk to behaviour that took real gates and real
evidence to establish. Aurora's design cost must scale with **capabilities**, not with
**machines** — hardware growth is O(1) on Aurora, indefinitely.

**The rule codifies existing practice.** RTX-1.6 already ran the experiment: a **≈17.6×**
compute change (UM790 CPU → Torre RTX 5070) reached Aurora as an **endpoint change** — zero
tools, prompts or model entries touched — validated across eleven gates. The `ollama-proxy`
is the deployed instance: two providers, automatic fallback, the same model id on both sides.
This is the same instinct as **AD-01** (awareness is a platform capability, not a UI plugin),
applied at the opposite end: AD-01 decouples Aurora from its **consumers**; this decouples
Aurora from its **providers**.

**This rule authorizes no implementation.** It creates no phase, gate or backlog item. A
capability with one provider needs no abstraction, and building one before a second provider
exists is the overengineering *Infrastructure Philosophy* forbids. The principle is
permanent; the machinery stays proportionate to the real provider count.

Full architecture, capability contract, selection criteria, fallback states, migration
recipe, risks and consequences:
[`../01_architecture/hardware_agnostic_compute_architecture.md`](../01_architecture/hardware_agnostic_compute_architecture.md).

**Origin:** operator direction, 2026-07-17, generalizing the RTX-1.6 endpoint swap
(2026-06-27) from a one-off migration into a standing constraint.

---

# Current-State Rules

CURRENT_STATE.md is the operational source of truth.

If another document disagrees with CURRENT_STATE.md:

CURRENT_STATE.md is assumed correct until reconciliation.

---

# Transient Operational Status

Operational status is **transient metadata, not durable documentation**.

Phrases such as:

- "at the git gate"
- "not committed" / "not yet pushed"
- "pending"
- "implemented, not yet validated"
- "Next: <sub-phase>"

describe a **moment**, not a fact. They go false the instant the state advances — most
often the moment the very commit carrying them is published. A statement that was true
when written and is false now is **drift**, and drift inside a source of truth is a
defect, not a cosmetic issue.

Rules:

1. **The triad must never knowingly contain false operational status.**
   `CURRENT_STATE.md`, `ROADMAP.md` and `AMAROLAB_HANDOFF.md` are operational sources of
   truth. Leaving a known-false status in them is not permitted, however narrow the
   current change is.

2. **Every reconciliation sweeps for stale transient status.** After a commit is
   published, the next documentation reconciliation **must** update or remove the
   transient markers that commit left behind — **including in triad documents the
   current change would not otherwise touch**. Sweep for the phrases above; do not
   rely on noticing them.

3. **Prefer durable phrasing.** Record the **fact** — `committed + pushed <hash>`,
   `PASS <date> on real evidence` — not the **moment** ("at the git gate"). Where a
   transient marker is genuinely needed, it is a **debt**, cleared at the next
   reconciliation.

4. **Historical documents are exempt — and must stay exempt.** A dated apply, freeze or
   closeout log in `09_logs/` records what was true **at that time**. Its transient
   status is **not** drift — it is evidence. Never rewrite it to match the present (see
   *Historical Documentation*). Corrections belong in **later** documentation: a new
   closeout log, plus the triad.

5. **Accuracy outranks commit purity.** If a commit's theme is narrow but the triad
   would be left knowingly false, reconcile the status **in that same commit**. A tidy
   commit boundary is never a reason to publish a false operational claim.

**Origin:** Phase ER-1 (2026-07-16/17). "At the git gate" survived publication **three
times** across all three triad documents — at one point `AMAROLAB_HANDOFF.md` pointed a
future session at `Next: ER-1.1` when ER-1.1 was already complete and pushed. The pattern
is structural, not carelessness: a document that asserts its own pending state is false
the moment it lands.

---

# Historical Documentation

Historical documents are never rewritten.

They capture:

- what happened
- when it happened
- why it happened

Corrections belong in later documentation, not by rewriting history.

Note: this rule and *Transient Operational Status* are complements, not exceptions to
each other. **Live state documents** (the triad) are reconciled to reality; **historical
records** (`09_logs/`) are left exactly as written and corrected only by later
documents.

---

# Content Provenance over Repository Chronology

**Content provenance has priority over repository chronology.**

A derived artifact is **fresh** when its content matches the content it was derived
from — never when its timestamps or commit references merely look recent.

Rules:

1. **Canonical content hashes are the authority for freshness.** Whether a derived
   artifact is current is decided by comparing a hash of the content it was derived
   from against that source's content as it now stands. Nothing else decides it.

2. **Commit hashes are traceability metadata only.** A commit reference records
   *where a thing came from*, never *whether it is current*. It must **never** be used
   as a freshness indicator. An artifact that carries one states that limit in place,
   next to the field — a reader must not have to remember this rule to avoid the trap.

3. **Hash the content that matters, not the container.** A hash is an authority only
   if it moves when the meaning moves and stays still when it does not. A hash taken
   over a whole file that also carries generation timestamps or unrelated sections
   reports false staleness on every regeneration — that is chronology wearing a
   content-hash disguise.

4. **Freshness is only ever proven for the link that was checked.** A derivation chain
   has one link per generation step. A check proves the link it compares and no other:
   a stale-but-internally-consistent pair passes. Where a chain has more than one link,
   each check states its scope, and full-chain freshness requires every link.

**Why.** Chronology answers *when something ran*; content answers *what it says*. Only
the second is what a consumer depends on. A chronological freshness signal goes false
the moment any unrelated change lands, so it reports as stale the artifacts that are
correct — and a check that cries wolf is ignored, which is worse than no check at all.

This is the same insight as *Transient Operational Status*, expressed in metadata rather
than prose. There, a document that asserts its own pending state is false the moment it
lands; here, a stamp that asserts its own currency is false the moment the next commit
lands. Both are a record claiming a truth it is not in a position to know.

**The rule codifies existing practice.** `ai-stack/ingest` already decides re-indexing by
per-chunk `content_sha`; the World Model loader already stamps per-entity
`provenance.sha256` — and ER-1.1 proved its alias sets inert by observing that a fresh
compile differed from the on-disk artifact **only** in those hashes. The rule names what
the platform was already doing, and forbids the one shortcut that was about to break it.

**Origin:** Phase ER-1.3, 2026-07-17. The compiled World Model artifact stamped
`docs_commit: f983a04f` while `HEAD` was `f146683a` — two commits behind — yet its content
was provably current: a fresh compile produced a byte-identical `resolution` block. Had
`docs_commit` been taken as the freshness signal for the derived entity projection, that
projection would have been **born stale**, and gone stale again at every subsequent commit,
while being correct throughout. Chronology reported stale; content proved current.

---

# Guardian Cloud

Guardian Cloud is production.

Never modify it without explicit approval.

Experimental work must never impact production services.

---

# Infrastructure Philosophy

Prefer:

- Simple
- Recoverable
- Documented
- Observable

Avoid:

- Clever
- Fragile
- Hidden
- Overengineered

---

# AI Assistant Behaviour

When acting on this repository, every AI assistant should:

- Read START_HERE.md first.
- Follow the mandatory reading order.
- Preserve documentation consistency.
- Detect documentation drift.
- Prefer reconciliation over assumptions.
- Never invent implementation details.
- Distinguish clearly between:
  - facts
  - hypotheses
  - recommendations

---

# Concurrent Phase Progression

An implementation-complete phase whose only open items are long-running
**passive validation gates** — gates that close on real time / operational
accrual, not on more implementation — does **not** block the start of the
next independent phase, provided all of the following hold:

1. The remaining gates require real time/accrual, not more implementation.
2. The next phase has no dependency on those gates.
3. The open gates remain tracked honestly (the phase is not declared complete).
4. No completion tag is created prematurely.
5. The next phase does not regress the still-accruing evidence.

If any condition fails, the next phase stays blocked until it holds. The open
gates continue as passive operational validation and close on their own real
evidence; the phase earns its completion tag only when they pass for real.

Origin: the F4 → F5 sequencing decision, 2026-06-30
(`04_ai_system/phase_f_architecture.md` → AD-19).

---

# Phase Closeout Checklist

A phase is only considered complete when all of the following are true:

- Implementation finished
- Validation passed
- Documentation updated
- Security review completed
- Secrets sanitized
- Git committed
- Git pushed
- Tag created (when appropriate)

---
## AI Assistant Session Preservation

Before any operation that may interrupt an AI assistant session
(reboot, logout, shutdown, terminal closure, context switch,
machine change or update), the assistant must:

- Stop the workflow.
- Ask whether the session handoff has been prepared.
- Ensure any required continuation document has been saved.
- Ensure the AI assistant is running inside tmux.
- Confirm the session can be resumed without losing context.

Session preservation is a mandatory checkpoint.
# Project Philosophy

AMAROLAB is built according to these principles:

1. Documentation first.
2. Reality beats documentation.
3. Validate before claiming success.
4. Security before convenience.
5. Recoverability over cleverness.
6. Production requires discipline.
7. Simplicity scales.
8. Every change leaves evidence.
9. Every phase ends with reconciliation.
10. If it is not documented, it does not exist.