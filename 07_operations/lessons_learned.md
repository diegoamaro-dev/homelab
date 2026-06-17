# Lessons Learned

Last updated: 2026-06-17

---

# Purpose

This document captures operational lessons learned during the development of Amarolab.

The goal is to avoid repeating mistakes, preserve troubleshooting knowledge and accelerate future recovery.

This file intentionally records practical experience rather than architecture.

---

# Rule #1

If it is not documented, it does not exist.

---

# Rule #2

Validate before documenting.

Never assume a system works because configuration appears correct.

Always validate using:

* Real commands
* Real logs
* Real outputs
* Real state changes

---

# Rule #3

Documentation follows reality.

Reality does not follow documentation.

If reality and documentation disagree:

```text
Reality wins.
Documentation must be updated.
```

---

# Docker

## Lesson 001

### docker restart does not reload environment variables

Date:

```text
2026-06-17
```

Problem:

Open WebUI continued using an old Home Assistant token after `.env` was updated.

Assumption:

```text
docker restart would reload .env
```

Reality:

```text
docker restart only restarts the existing container.
```

Environment variables remain frozen from container creation.

Solution:

```text
Recreate the container.
```

Impact:

Several hours of troubleshooting were lost because the wrong assumption remained unverified.

Reference:

```text
07_operations/docker/docker_env_reload_behavior.md
```

---

# Home Assistant

## Lesson 002

### Validate real state changes

Date:

```text
2026-06-17
```

Reading states is not sufficient.

A Home Assistant integration is only considered validated when:

```text
Read
Write
Verify
Restore
```

are all successful.

Gate G-5 established this rule.

---

## Lesson 003

### Always restore baseline state

After any automation test:

```text
Return device to original state.
```

Benefits:

* Safer testing
* Predictable behaviour
* Easier troubleshooting

Example:

```text
switch.impresora_3d

OFF
→ ON
→ OFF
```

Baseline restored.

---

# MQTT

## Lesson 004

### Anonymous access is acceptable only during validation

Temporary:

```text
allow_anonymous true
```

is acceptable when bringing up a new service chain.

Permanent production posture:

```text
allow_anonymous false
```

with:

```text
password_file
acl_file
```

---

## Lesson 005

### Harden only after validation

Correct order:

```text
Make it work
Validate
Harden
Document
```

Wrong order:

```text
Harden
Guess
Break everything
```

---

# Git

## Lesson 006

### Never blindly use git add .

Before every commit:

Review:

```bash
git status
```

Then add only intended files.

Reason:

Secrets, backups and temporary files may accidentally enter Git.

---

## Lesson 007

### Git history is infrastructure

Commits are operational documentation.

Good commits explain:

```text
What changed
Why it changed
What was validated
```

Bad commits:

```text
fix
update
misc
changes
```

---

# Security

## Lesson 008

### Secrets do not belong in documentation

Never document:

```text
Passwords
Tokens
Private keys
API keys
Cookies
```

Always use placeholders.

---

## Lesson 009

### GitHub is public forever

Assume:

```text
Anything committed can eventually become public.
```

Act accordingly.

---

# Backups

## Lesson 010

### Backups are only real after restoration testing

A backup is not proven because:

```text
The backup job succeeded.
```

A backup is proven when:

```text
Data can be restored.
```

---

# Infrastructure

## Lesson 011

### Simplicity scales

Complexity feels productive.

Simplicity is maintainable.

Prefer:

```text
Simple
Documented
Recoverable
```

over:

```text
Clever
Complex
Fragile
```

---

## Lesson 012

### Every service needs an owner

For every service answer:

```text
Why does it exist?
Who uses it?
What depends on it?
Can it be removed?
```

If those questions cannot be answered:

The service probably should not exist.

---

# AI Systems

## Lesson 013

### Tools must be validated individually

Never assume:

```text
If one tool works,
all tools work.
```

Validate independently:

```text
time_now
rag_search
audit_search
ha_get_state
ha_call_service
```

---

## Lesson 014

### Production and experimentation must remain separate

Guardian Cloud is production.

Experimental work must not impact:

```text
Guardian Cloud
Backups
Critical infrastructure
```

without explicit approval.

---

# Personal Lessons

## Lesson 015

### Slow is smooth. Smooth is fast.

Most operational mistakes come from:

```text
Skipping validation
Skipping documentation
Skipping backups
```

Taking a few extra minutes usually saves hours.

---

# Amarolab Principles

1. Documentation first.
2. Validate before claiming success.
3. Security before convenience.
4. No secrets in Git.
5. Backups before major changes.
6. Recoverability matters.
7. Simplicity beats complexity.
8. Production requires discipline.
9. Learning is part of the project.
10. If it is not documented, it does not exist.

---

# Future Entries

Add new lessons whenever:

* a mistake was made
* a significant incident occurred
* a root cause was identified
* a new operational rule emerged
* a troubleshooting process revealed something non-obvious

The value of this document increases over time.
