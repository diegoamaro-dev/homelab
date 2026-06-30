# PROJECT_RULES

Last updated: 2026-06-27

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

# Current-State Rules

CURRENT_STATE.md is the operational source of truth.

If another document disagrees with CURRENT_STATE.md:

CURRENT_STATE.md is assumed correct until reconciliation.

---

# Historical Documentation

Historical documents are never rewritten.

They capture:

- what happened
- when it happened
- why it happened

Corrections belong in later documentation, not by rewriting history.

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