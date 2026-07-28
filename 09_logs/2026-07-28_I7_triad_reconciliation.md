# I-7 — Triad Reconciliation after the 2026-07-28 Infrastructure Audit — APPLIED

**Date:** 2026-07-28
**Type:** Documentation only. **No production change.** No container, service, Docker
configuration, backup, cron, monitoring or security setting was touched. No historical
document was rewritten.
**Scope:** remediation item I-7. Program D of the 2026-07-28 remediation roadmap.
**Source register:** [`2026-07-28_amarolab_technical_audit.md`](2026-07-28_amarolab_technical_audit.md).

---

## 1. Purpose

The 2026-07-28 audit found that the project's documentation is unusually accurate and that
**its errors cluster in one place: operational status** — versions, counts, ACL contents,
sizes. It also found that the rule governing exactly this (`PROJECT_RULES.md` → *Transient
Operational Status*) was being applied to `ROADMAP.md` more consistently than to
`CURRENT_STATE.md`, which is the declared source of truth.

I-7 closes that gap and records the completion of Program A capture, so that a new session
reading `START_HERE.md` reconstructs the project correctly without conversation history.

## 2. Method

**Every value was re-measured against the running system before it was written.** The audit's
figures were treated as a list of things to check, never as a source to copy — several are
time-varying (Qdrant counts grow nightly) and the audit was ~10 hours old at reconciliation
time. Where a measurement is a dated observation rather than a fixed fact, the document now
says so in place.

## 3. Drift closed, with measured evidence

| Finding | Was documented | Measured 2026-07-28 | Where |
|---|---|---|---|
| **M-3** | `system_status` v0.2.0 | **v0.3.0** in `webui.db`; D-23 canonical path absent; stale `tmp/` dump tracked | `CURRENT_STATE.md` → Open WebUI tools |
| **M-5** | "exactly **one** entity exposed — the canary" | **ZERO exposed**; `expose_new: false`; canary **not in the ACL at all** | `CURRENT_STATE.md` → Home Assistant |
| **L-1** | system prompt 4 478 chars | **5 138 chars** | `CURRENT_STATE.md` → Open WebUI model |
| **L-2** | `aurora-piper` voice `es_ES-davefx-medium` | **`es_ES-sharvard-medium`, speaker F** | `CURRENT_STATE.md` → Voice stack |
| **L-3** | 6 RAG collections listed | 7 AMAROLAB + 2 Open WebUI-internal; counts refreshed | `CURRENT_STATE.md` → Qdrant, Ingest |
| **L-4** | F-ER13-1 "deliberately not fixed" | **RESOLVED** — `with_name` + pid temp (line 107) **and** `flock` run-lock (line 252) | `CURRENT_STATE.md` → pending item 9 |
| **N-1** | "first devices joined" | **10 devices paired** | `CURRENT_STATE.md` → Zigbee2MQTT |
| **H-1 / H-2** | Backups "Operational" unqualified | **Backup PASS, retention DEFECTIVE** — inert since 2026-06-13; anchor unprotected; coverage incomplete; probe blind | `CURRENT_STATE.md` → Backups |
| **C-1** | Zigbee2MQTT "Operational" | Operational, **after an unnoticed 2 h 39 m outage**; structural half open as S-9 | `CURRENT_STATE.md` → Zigbee2MQTT |

**L-5 was recorded, not fixed.** `ai-stack/.env` carries `QDRANT_API_KEY=` (length 0)
alongside the working `QDRANT__SERVICE__API_KEY` (length 64). New evidence from I-3: the
running `openwebui` `QDRANT_API_KEY` and the running `qdrant` `QDRANT__SERVICE__API_KEY` have
**identical sha256 digests**, so the live path is correct and the `.env` entry contradicts the
running system. Changing `.env` is a configuration change and outside I-7.

**Not carried into the triad:** L-6, L-7, L-8, L-11 and M-4 are Low-severity and affect no
operational claim; they went to `ROADMAP.md` → *Documentation Hygiene*. **L-10 needs no
action** — the voice-context container count self-corrects at the next 04:15 cycle and was a
symptom of M-1.

## 4. Structural additions

- `CURRENT_STATE.md` → new section **Infrastructure audit — 2026-07-28**: program table,
  completed items, the **Recovery Artifact doctrine status**, and an explicit warning that the
  two published audit documents are dated records whose own status columns do not track
  execution.
- `ROADMAP.md` → new section **Infrastructure Remediation — 2026-07-28 audit**: five
  programs, a full item ledger (P0 … L-E), and four standing constraints.
- `AMAROLAB_HANDOFF.md` → ***Next Immediate Task* rewritten.** It still opened with *"Current:
  Phase ER-1"*, a phase closed since 2026-07-21 — the single worst reconstruction defect in
  the triad. It now states the two live workstreams (F-6/F6.1, infrastructure remediation) and
  the three standing constraints up front, with the prior content preserved below under
  *Historical — prior "next task" entries*.
- `AMAROLAB_HANDOFF.md` → *Important Rules* gains **Recovery Artifacts** and **Reality always
  wins**.

## 5. M-2 — correction of record (the purpose of this section)

**This section is the new dated record that resolves M-2.** The historical document is **not**
modified, per `PROJECT_RULES.md` → *Historical Documentation*.

[`2026-07-28_phaseF_F6_1_step2_handoff.md`](2026-07-28_phaseF_F6_1_step2_handoff.md) contains
three statements about its own repository state that were true when drafted and false the
moment the commit carrying them landed:

| Location | Statement in the historical document | Correct fact |
|---|---|---|
| Line 6 | *"Repository state at handoff: clean, `458dda67`, synchronized with `origin/main`."* | The document was committed as **`2a185cb1`**, which made the tree one commit ahead of `origin/main` |
| §9 (lines 357–359) | `HEAD 458dda679804…` / `origin/main 458dda679804…` / `divergence 0 / 0` | At the moment of commit, `HEAD` became `2a185cb1` and divergence became **0 / 1** |
| §12 (line 498) | *"Documentation-only. **Not committed, not pushed**"* | **Committed `2a185cb1`** 2026-07-28, **pushed** 2026-07-28 in range `458dda67..319b2c58` |

**Current fact of record:** the F6.1 Step 2 handoff is committed as `2a185cb1` and published
on `origin/main`. The repository was synchronized at `319b2c58`; verify the current tip with
git rather than trusting any hash written here.

**Why this happened, and why the rule exists.** This is the exact failure *Transient
Operational Status* was written to prevent after Phase ER-1: *a document that asserts its own
pending state is false the moment it lands* — the commit carrying the claim is the commit that
falsifies it. It survived publication three times across the triad during ER-1; here it
recurred in a `09_logs/` entry, where the correct remedy is not a rewrite but a later record.
This is that record.

**The handoff's §9 and §12 must be read as evidence of what was true while drafting, never as
current repository state.** Nothing in it is to be edited.

## 6. What I-7 deliberately did not do

- **No configuration change of any kind.** L-5 (`.env`), M-5 (re-exposing the canary) and M-3
  (moving the `system_status` source to its D-23 path) are all recorded and left to their own
  gated items — S-11 and the M-3 provenance fix respectively.
- **No historical document rewritten.** The F6.1 handoff, the audit, the roadmap and the
  backup incident record are untouched.
- **No gate reopened.** Every closed gate's closure stands.
- **No new remediation item invented.** The ledger reflects the published roadmap plus the
  R-I3-1…7 items already recorded at I-3.

## 7. Verification

- Every figure in §3 re-measured live before writing; commands and outputs are in the session
  record.
- Production unchanged: 17/17 containers running; `aurora-whisper`
  `StartedAt=2026-07-25T21:50:55.349910391Z`, `RestartCount=0` — **D-F6-1 holds.**
- Reconciliation is confined to `00_overview/{CURRENT_STATE,ROADMAP,AMAROLAB_HANDOFF}.md`
  plus this log.

## 8. Rollback

Documentation-only. `git checkout` the three triad files and delete this log. No production
state to revert.

## 9. Git gate

**Not committed, not pushed** — both require explicit operator approval immediately before the
command (`PROJECT_RULES.md` → *Operator Git Approval*). Author as
`Diego <diego@diegoamaro.dev>`.

**STOP at git gate.**
