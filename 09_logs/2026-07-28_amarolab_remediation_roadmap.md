# AMAROLAB — Remediation Roadmap

**Date:** 2026-07-28
**Source:** Full technical audit 2026-07-28 (30 findings) + 8 findings derived during P0
execution.
**Status baseline:** reflects the system **after** tonight's P0 work, not the original audit
snapshot.
**Scope:** planning only. No system modification, no commits.

> **Publication note (added at publication, 2026-07-28).** Published into the repository
> unmodified — no item, dependency, ordering or risk rating was altered. Sanitization scan
> found nothing requiring redaction.
>
> This is a **dated planning record** stating the plan as of 2026-07-28. Per
> `PROJECT_RULES.md` → *Transient Operational Status*, **execution status does not live
> here** — the item table below is the plan, not a live tracker. Live status belongs in the
> overview triad and is reconciled at **I-7**, which has not run yet. A reader must therefore
> treat every status in this document as *"as of 2026-07-28"* and verify current state
> against the triad and the running system.
>
> Source register: [`2026-07-28_amarolab_technical_audit.md`](2026-07-28_amarolab_technical_audit.md).
> H-1's corrected diagnosis: [`2026-07-28_backup_retention_incident.md`](2026-07-28_backup_retention_incident.md).

---

## 0. Position after P0

| Finding | Original | Now |
|---|---|---|
| **C-1** Zigbee2MQTT down | Critical | **Service RESOLVED** 02:49 CEST. Structural half → **S-9** |
| **H-1** Backup retention | High | **Stage A done** (lock cleared). Diagnosis corrected — see below |
| **L-9** Parent-snapshot matching | Low | **Promoted to High** — it is the actual cause of H-1 |

The H-1 correction matters for planning: the stale lock was masking a retention policy that
has **never** removed a snapshot since 2026-06-13. Clearing the lock restored the mechanism
but changed no outcome. The real work moved from "unlock and prune" to "fix the grouping
defect, then decide a policy."

**Totals:** 38 findings — 1 resolved, 1 partially resolved, 36 open.

---

## 1. The five programs

Thirty-six open findings are not thirty-six independent tickets. They cluster into five
programs, and treating them as programs is what makes the sequencing tractable.

| | Program | Findings | Core problem |
|---|---|---|---|
| **A** | **Declarative substrate** | H-3, H-4, M-7, N-5 | 8 of 17 containers exist only as running processes. The platform cannot be rebuilt |
| **B** | **Observability & alerting** | H-1c, M-1, N-3, N-7 | Nothing observes anything in real time. Three separate failures went unnoticed for hours-to-weeks |
| **C** | **Security posture** | H-5, H-6, H-7, H-8, M-6, M-9, N-6 | The LAN is the security boundary by default, not by decision |
| **D** | **Documentation truth** | M-2, M-3, M-5, L-1…L-5, L-7, L-8, L-11, N-1 | Operational status drift in the declared source of truth |
| **E** | **Backup lifecycle** | H-1a, H-1b, H-2, N-2 | Retention inert; coverage incomplete; no anchor protection |

Two observations that shape the whole plan:

**Program A is the keystone.** H-4 (the stack definition that would revert RTX-1.6), H-5
(binding Ollama), and M-7 (image pinning) all require a definition that survives — which
does not exist. Doing A first makes three other items cheap; doing them first means doing
them twice.

**Program B is why everything else was invisible.** A container down 2h39m, retention
broken 30 days, five missing backups — none detected by automation. Every other program
ships fixes; B ships the ability to know whether they held.

---

## 2. IMMEDIATE — this week

Zero or near-zero operational risk. Mostly documentation and capture. Unblocks everything
downstream.

| ID | Item | Findings | Complexity | Op risk | Depends on |
|---|---|---|---|---|---|
| **I-1** | Publish pending documentation — F6.1 handoff `2a185cb1` + tonight's incident record | M-2, N-8 | Trivial | **None** | Operator git approval (per command) |
| **I-2** | Record the H-4 redeploy hazard in `CURRENT_STATE.md` so no session redeploys the `ai-local` stack | H-4 | Trivial | **None** | — |
| **I-3** | **Capture live container configs into version-controlled compose files.** Generated from `docker inspect`, written to match reality. **No container recreated** | H-3, H-4 | Medium | **None** | — |
| **I-4** | Fix the backup grouping defect (stable staging path + `--group-by host,tags`) | H-1a, L-9→High | Low | Low | — |
| **I-5** | Extend backup coverage: Portainer volume, `/etc/cron.d/aurora-signals`, openedai voice map | H-2 (partial) | Low | Low | — |
| **I-6** | Give `63c072f4` real protection — distinct tag or explicit exclusion | N-2 | Low | Low | I-4 |
| **I-7** | Triad reconciliation sweep | M-3, M-5, L-1…L-5, L-11, N-1 | Low | **None** | — |
| **I-8** | Track `/usr/local/bin/homelab-backup.sh` in the repository | N-5 | Trivial | **None** | — |

### Critical constraint on I-3

**Nothing in I-3 may recreate `aurora-whisper`.** F6.1's D-F6-1 requires single-variable
isolation, and the frozen baseline is pinned to the currently-running container (image
`sha256:966e1b09…`, started 2026-07-25T21:50:55Z, restarts 0). Recreating it voids the
Step 2 baseline and forces a re-measurement. I-3 is **write-files-to-match-reality only**;
convergence is a later, separately-gated change.

### I-7 contents

`system_status` v0.3.0 not v0.2.0 · voice-exposure ACL is zero-exposed not one ·
system prompt 5138 chars · `aurora-piper` runs `es_ES-sharvard-medium` not `davefx` ·
Qdrant counts + two undocumented collections · F-ER13-1 already fixed in `6525b0d2` ·
empty `QDRANT_API_KEY` in `.env` · 10 Zigbee devices not 3 · the two known WM/phase-F
doc-debt items.

---

## 3. SHORT TERM — 2 to 4 weeks

Decisions first, then the changes they gate. Most operational risk in the roadmap sits here.

| ID | Item | Findings | Complexity | Op risk | Depends on |
|---|---|---|---|---|---|
| **S-1** | **Decide and document the LAN trust posture** in `06_security/` | H-8 | Low (decision) | **None** | — |
| **S-2** | Bind Ollama to loopback / drop the host publication | H-5 | Low | Low | S-1, I-3 |
| **S-3** | Retire `homelab-tools.service` (or bind to `127.0.0.1`) after confirming no consumer | H-6 | Low | Low | S-1 |
| **S-4** | Rotate the Guardian Cloud tunnel token → `.secrets` + `env_file` + `chmod 0600` | H-7 | Medium | **Medium** — touches production | S-1 |
| **S-5** | Disable SSH password auth after verifying key access from every device | M-9 | Low | **Medium** — lockout risk | S-1 |
| **S-6** | Patch `docker-ce` / `containerd.io` in a planned window | M-6 | Low | **Medium** — restarts containers | I-3 (definitions must exist first) |
| **S-7** | **Decide: Health Aggregator now, or accept a third health writer** | N-7 | Low (decision) | **None** | — |
| **S-8** | Close the backup monitoring blind spot — `bin/backup-nightly` wrapper on the `ingest-nightly` pattern | H-1c, N-3 | Medium | Low | I-4, S-7 |
| **S-9** | Zigbee coordinator USB hardening + device-loss recovery path | C-1 structural | Medium | Low | — |
| **S-10** | Retention: post-fix dry-run → policy decision → attended prune | H-1b | Medium | **High** — irreversible deletion | I-4, I-6, one nightly cycle |
| **S-11** | Decide whether to re-expose the voice canary for F6.1 Step 7 | M-5 | Trivial | Low | I-7 |

### S-1 is a gate, not a task

S-2, S-3, S-4 and S-5 are all downstream of one question: *is the LAN a trust boundary or
not?* Answer it once, in writing, and the four changes become mechanical. Skip it and each
gets re-litigated.

### S-10 ordering is strict

`I-4` → observe **one** nightly cycle → fresh `forget --dry-run --group-by host,tags` →
policy decision → **`I-6` anchor protection** → attended prune after `restic check`.
Going straight to `7/4/6` on a repository that has never pruned removes ~25 of 42 snapshots
in one step; a conservative first pass then tightening is the lower-risk path.

---

## 4. MEDIUM TERM — 1 to 3 months

Structural work. Larger, but each is now unblocked and low-drama.

| ID | Item | Findings | Complexity | Op risk | Depends on |
|---|---|---|---|---|---|
| **M-A** | **Design and build real alerting** — container-down, backup-stale, context-stale, coordinator-missing | M-1 | **High** | Low | S-7, S-8 |
| **M-B** | Converge the `ai-local` stack definition with reality (recreate under a gated change) | H-4 | Medium | **Medium** | I-3, F6.1 closed |
| **M-C** | Pin every production image to a digest inside the captured definitions | M-7 | Low | Low | I-3 |
| **M-D** | Secrets-backup strategy — deliberate design, not an ad-hoc path addition | H-2 (remainder) | Medium | Medium | S-1 |
| **M-E** | Repository hygiene — untrack `ai-tools/venv/` (1333 files) and `openwebui-tools/tmp/` | M-4 | Low | **None** | S-3 (may remove `ai-tools/` entirely) |
| **M-F** | Reclaim ~33 GB — Voice Lab images not needed for Round 2, plus build cache | M-8 | Trivial | Low | Voice Lab Round 2 scope decision |
| **M-G** | Resolve HA integration noise (Cast/DLNA) and stale NPM hosts | L-7, L-8 | Low | Low | — |
| **M-H** | Fix mosquitto log-write failure | N-4 | Low | Low | — |
| **M-I** | Harden the backup staging directory to `0700` outside `/tmp` | N-6 | Trivial | Low | I-4 (same edit) |

**M-A is the largest single item in the roadmap** and deliberately sits here rather than
earlier: it is a design decision about what Aurora's operational role should be, not a
patch. Phase F built awareness — state Aurora can *describe when asked*. Alerting is state
that *reaches a human unasked*. That is a genuine architectural extension and deserves the
same gated treatment as any other phase.

---

## 5. LONG TERM — 3 months and beyond

| ID | Item | Findings | Complexity | Op risk | Depends on |
|---|---|---|---|---|---|
| **L-A** | Migrate the Open WebUI STT shim away from `fedirz/faster-whisper-server` | M-10 / R-D-13 | Medium | Medium | **F6.1 CLOSED** (D-F6-3) |
| **L-B** | Decide retention for ~2.5 GB of pre-sanitization repository copies | L-6 | Trivial | Low | — |
| **L-C** | Health Aggregator implementation, if chosen at S-7 | N-7 | High | Low | S-7, M-A |
| **L-D** | Dedicated NAS procurement + data migration | existing item 3 | High | Medium | — |
| **L-E** | Full disaster-recovery rehearsal — rebuild from backup into isolated hardware | validates A + E | High | **None** (isolated) | I-3, I-5, M-D |

**L-E is the real acceptance test for this entire roadmap.** Programs A and E claim the
platform becomes recoverable. Only a rehearsal proves it — and the project already has the
pattern: E5-b restored Qdrant into a disposable container, and G-F4-08 empirically proved
digest recovery. This is the same discipline applied to the whole platform.

**L-A must not enter F6.1.** D-F6-3 fixes a single candidate; the shim is a second variable.
It becomes eligible only once F6.1 closes.

---

## 6. Optimal execution order

Not severity order. Ordered by **leverage** — what unblocks the most, at the least risk.

### Wave 1 — Capture and decide (week 1) · risk: none

```
I-3  capture container definitions        ← highest leverage item in the roadmap
I-7  triad reconciliation
I-2  record the H-4 hazard
I-8  track the backup script
I-1  publish pending docs
S-1  decide the LAN trust posture         ← gates four security items
S-7  decide Health Aggregator vs 3rd writer ← gates the monitoring build
```

Nothing here changes a running service. Everything here removes ambiguity that would
otherwise be paid for twice.

### Wave 2 — Backup lifecycle (weeks 1–2) · risk: low, one high-risk gate at the end

```
I-4  grouping fix          →  observe one nightly cycle
I-5  coverage extension
I-6  anchor protection
S-8  backup observability
S-10 retention decision + attended prune  ← the only irreversible step
```

Strictly sequential. S-10 stays operator-gated per execution.

### Wave 3 — Security posture (weeks 2–4) · risk: medium

```
S-2 → S-3 → S-6 → S-5 → S-4
```

Ordered by blast radius, ascending. S-2 and S-3 are self-contained. S-6 restarts containers
— hence after I-3. S-5 carries lockout risk. S-4 touches Guardian Cloud production and goes
last, with its own window.

### Wave 4 — Resilience (weeks 3–6) · risk: low

```
S-9  Zigbee USB hardening
S-11 voice canary decision (before F6.1 Step 7)
M-C  image pinning
M-H, M-G, M-I  small fixes
```

### Wave 5 — Structural (months 2–3) · risk: low–medium

```
M-A  alerting              ← the largest item; the one that changes operational posture
M-B  stack convergence     (only after F6.1 closes)
M-D  secrets backup
M-E, M-F  hygiene
```

### Wave 6 — Long horizon

```
L-A (post-F6.1)  ·  L-C  ·  L-B  ·  L-D  ·  L-E (acceptance rehearsal)
```

---

## 7. Interaction with the active phase

**F-6 / F6.1 continues in parallel and is not blocked by this roadmap.** Steps 3–5 change
nothing in production.

Three interactions to respect:

1. **Do not recreate `aurora-whisper`** until F6.1 closes — D-F6-1. Constrains I-3 and M-B.
2. **F6.1 Step 7 needs a live acceptance path.** Zigbee is restored, but the voice canary is
   currently unexposed (M-5/S-11). Decide before reaching Step 7, not at it.
3. **L-A (STT shim) is post-F6.1** — D-F6-3.

---

## 8. Complexity and risk summary

| Complexity | Count | Items |
|---|---|---|
| Trivial | 6 | I-1, I-2, I-8, S-11, M-F, M-I, L-B |
| Low | 13 | I-4, I-5, I-6, I-7, S-1, S-2, S-3, S-5, S-6, S-7, M-C, M-E, M-G, M-H |
| Medium | 10 | I-3, S-4, S-8, S-9, S-10, M-B, M-D, L-A |
| High | 4 | M-A, L-C, L-D, L-E |

| Operational risk | Items |
|---|---|
| **None** | I-1, I-2, I-3, I-7, I-8, S-1, S-7, M-E, L-E |
| **Low** | I-4, I-5, I-6, S-2, S-3, S-8, S-9, S-11, M-A, M-C, M-F, M-G, M-H, M-I, L-B |
| **Medium** | S-4, S-5, S-6, M-B, M-D, L-A, L-D |
| **High** | **S-10 only** — irreversible snapshot deletion |

**Exactly one item in the entire roadmap destroys data.** Everything else is additive,
reversible, or documentation. That is worth stating plainly: this is not a dangerous
remediation programme, it is a large but low-risk one, with a single gated exception.

---

## 9. What the roadmap does not resolve

Stated so it is a decision rather than an omission:

- **Single-host architecture.** Every service runs on one machine with one root disk.
  Nothing here changes that; L-D (NAS) is the only structural mitigation queued.
- **`ai-stack/.env` remains a single-copy secret store** until M-D. This is the largest
  unmitigated recoverability gap and it stays open through Waves 1–4 by design, because
  fixing it badly (plaintext secrets into backups) is worse than fixing it late.
- **No change-management process.** The audit found configuration drift in the Portainer
  stack, the exposure ACL, and the Piper voice — all changes made correctly at the time and
  never reflected anywhere. Programs A and D fix the current instances; nothing yet prevents
  the next one. Worth considering as a rule in `PROJECT_RULES.md` once A lands.

---

## 10. Recommended immediate next action

**I-3 — capture the container definitions.** Zero operational risk, purely additive, and it
is the prerequisite for H-4, S-2, S-6, M-B and M-C. It is also the single item that moves
the platform from "not rebuildable" to "rebuildable", which is the largest structural gap
the audit found.

Second: **S-1 and S-7**, because they are decisions, they cost nothing to make, and seven
downstream items are waiting on them.
