# I-3 — Declarative Substrate — Reality Capture — APPLIED

**Date:** 2026-07-28
**Type:** Read-only capture. **No production change.** No container created, recreated,
started, stopped or modified; no image pulled; no secret moved or renamed; no backup, cron
or monitoring path touched.
**Scope:** I-3.0 – I-3.6, as approved. Programs A capture only — convergence is a later,
separately-gated project.
**Source finding:** H-3 / H-4 — `2026-07-28_amarolab_technical_audit.md`.

---

## 1. What was produced

| Artifact | Path |
|---|---|
| Field contract | `03_services/CAPTURE_CONTRACT.md` |
| Directory doctrine + inventory | `03_services/README.md` |
| Captured definitions (6 projects, 14 services) | `03_services/{ai-local,aurora-voice,portainer,proxy,home-assistant,zigbee-stack}/docker-compose.yml` |
| Capture bundle (gitignored) | `09_ops/runtime/i3_capture_2026-07-28/` — 55 files, `MANIFEST.txt` + per-file sha256 |
| Permanent rule — *Recovery Artifacts* | `00_overview/PROJECT_RULES.md` |
| Triad pointer to the H-4 hazard | `00_overview/CURRENT_STATE.md` → *Known pending items* 11 |

`03_services/ollama-proxy/docker-compose.yml` was **verified**, and one comment block was
added at the final review declaring it the **Deployment Source** — the only such file in
`03_services/`. No behavioural change: it was authored, not captured, and already follows
the intended pattern.

## 2. Method

Reality is `docker inspect`. The Portainer-stored definitions under `/data/compose/` were
**not read** — no helper container was run — because they are known-divergent (H-4) and
carry no authority. This removed the audit's assumed dependency on reading the
`portainer_data` volume.

Creation-time overrides were separated from image defaults mechanically, by differencing
container `Config` against image `Config`. Fields equal to the image default are absent
from the captured files rather than invented into them. Result: only four services override
anything — `aurora-whisper`, `aurora-piper`, `aurora-wakeword` (command) and
`aurora-piper-http` (entrypoint + command). No service overrides `user` or `workdir`.

## 3. Validation

**G-I3-04 — field-by-field parity: PASS. 103 checks, 103 match, 0 differences.**
Every field in `CAPTURE_CONTRACT.md` §2, across all 14 services, compared between the
rendered compose config and `docker inspect`. Report:
`09_ops/runtime/i3_capture_2026-07-28/verification/parity_report.txt`.

Redacted values were verified by **sha256 digest** against the live container environment,
so parity is proven without the plaintext ever being written to disk or to the repository.

**G-I3-05 — inertness and non-mutation: PASS.** `docker compose up --dry-run` on all six
projects reports `Creating` for every service — none matches a running container, which is
the intended property. Report: `verification/dry_run_report.txt`.

`aurora-whisper` verified unchanged before and after the entire exercise:
`StartedAt=2026-07-25T21:50:55.349910391Z`, `RestartCount=0`,
`Image=sha256:966e1b0967f398b81fa2273a96b2b940004fa1b77754f9ffda6b5689a58dd158`.
**D-F6-1 holds; the F6.1 Step 2 baseline is intact.** 17/17 containers running at close,
identical to the state at open.

## 4. Decisions

**D-I3-1 — Recovery artifacts are inert by construction.** All six captured projects use an
`amarolab-` prefixed `name:`, which cannot match any running container's compose project
label, and every service sets `container_name` so an accidental `up` fails on collision.

This deviates from reality in exactly one place: `ollama` carries the live project label
`ai-local` while the artifact is named `amarolab-ai-local`. The deviation is a property of a
new artifact, not a rename of a running thing — the other seven captured containers belong
to no compose project at all. Project name affects only labels and default network naming,
and every network here is declared `external` with an explicit `name:`, so nothing is
functionally derived from it.

**D-I3-2 — `zigbee-stack` is inert too, and deliberately so.** The original plan was to
restore that file at the labeled path with its real project name and require a no-op
dry-run, which would have restored real manageability. That was rejected on discovery that
the dongle host path must be redacted per repository convention: a live-matching file
carrying a redacted device path invites an `up` that recreates `zigbee2mqtt` with an invalid
coordinator and reproduces the C-1 outage. Uniform inertness was chosen over one testable
gate. Parity is proven by G-I3-04 instead, which is the stronger evidence anyway.

**D-I3-3 — redaction is a publication measure, not a mechanism change.** Secret env values
and the dongle path are redacted in the committed files; nothing about how the running
containers obtain them was altered. The direct consequence — the files are not deployable
as written — is recorded as remediation, not fixed here.

## 5. Remediation items discovered (NOT implemented — I-3 doctrine)

| ID | Item | Severity |
|---|---|---|
| **R-I3-1** | Docker network subnets are auto-assigned by creation order; HA `trusted_proxies` is `172.18.0.0/16` = `ai-local_default`. A rebuild in a different order silently breaks reverse-proxy trust while everything reports healthy. Pin subnets | High |
| **R-I3-2** | Secret supply mechanism for the captured definitions — required before they are deployable. Feeds M-D | High |
| **R-I3-3** | `03_services/zigbee-stack/docker-compose.yml` was **never** in git history (`git log --all`). The audit's "restore from git history if a version exists" was not an available path; the file was reconstructed from live state | Informational — corrects H-3 |
| **R-I3-4** | `openwebui` and `qdrant` carry **no** compose labels — they left the `ai-local` project entirely. Refines H-4: a redeploy half-fails on name conflict rather than reverting silently, and the natural "clean up the conflict" response produces the full revert. Already recorded in the H-4 hazard | High |
| **R-I3-5** | The Zigbee dongle host path is redacted; substitution is required before deployment. Same class as R-I3-2 | Medium |
| **R-I3-6** | `portainer` uses `restart: always` while the rest of the estate uses `unless-stopped`. Captured as found; the inconsistency is unexplained | Low |
| **R-I3-7** | `ollama`'s model store `/srv/homelab/data/ollama` is outside the restic path set. Large and re-downloadable, so possibly deliberate — but undocumented either way. Extends H-2 | Low |

Confirmation of an existing finding, with new evidence: **L-5** — the running `openwebui`
`QDRANT_API_KEY` and the running `qdrant` `QDRANT__SERVICE__API_KEY` have **identical
sha256 digests**, so RAG auth is correct on the live path. The empty `QDRANT_API_KEY=` in
`ai-stack/.env` therefore contradicts the running system, not merely itself. Not resolved
here, per instruction.

## 6. Final documentation review

A review pass over all seven files in `03_services/` produced six adjustments, all
comment-only. Parity re-verified afterwards: **103/103, 0 differences**, and all seven files
still parse.

| # | Adjustment | Reason |
|---|---|---|
| 1 | Uniform `Status / Captured / Contract / Evidence` header block on all six captured files | No file pointed at its own parity evidence; a reader arriving by `grep` could not find the proof |
| 2 | `ollama-proxy` declares itself the **Deployment Source** | Six files declared their status and the seventh said nothing — the ambiguity ran in the dangerous direction |
| 3 | Relative paths in comments corrected (`../CAPTURE_CONTRACT.md`, `../../07_operations/…`, `../../01_architecture/…`) | Four references did not resolve from the file's own directory |
| 4 | D-F6-1 warning converted from a box-drawing frame to plain text | Alignment-dependent ASCII art breaks silently on edit; *Infrastructure Philosophy* prefers simple over clever |
| 5 | `aurora-whisper` image digest written in full, plus the constraint's source document | The digest was truncated with an ellipsis, so it could not be compared |
| 6 | "not deployable" → "**NOT** deployable" in `ai-local` | Matches the emphasis used for the same claim elsewhere |

No adjustment touched a service field. The rendered configuration of every project is
unchanged, which the re-run parity check proves against the running system directly.

## 7. Rollback

Documentation-only. `git checkout` the added paths, or do not commit. The capture bundle is
gitignored runtime state and can be deleted. No production state to revert.

## 8. Git gate

**Not committed, not pushed** — both require explicit operator approval immediately before
the command (`PROJECT_RULES.md` → *Operator Git Approval*). Author as
`Diego <diego@diegoamaro.dev>`.

Triad scope is deliberately narrow. `CURRENT_STATE.md` gains **one** pending item — a
pointer to the H-4 hazard record, because a control no reader reaches is not a control. The
broader 2026-07-28 audit reconciliation remains with **I-7** and has not run.
`PROJECT_RULES.md` is not a triad document; it gains the *Recovery Artifacts* rule.

**STOP at git gate.**
