# Operational Reconciliation — 2026-08-17

**Date:** 2026-08-17
**Type:** Dated operational record + triad reconciliation. Not a phase, not a remediation item.
**Scope:** Reconcile the triad against seventeen days of unattended operation
(2026-07-31 → 2026-08-17).
**Production changed by this document:** **none.** Every observation below was read-only.
**Authorizes:** **nothing.** No remediation is designed, scoped or approved here.

> This is a dated record. It states what was true on 2026-08-17 and is **not** rewritten as the
> situation advances (`PROJECT_RULES.md` → *Historical Documentation*). Corrections belong in
> later documents.

Predecessor documents, each dated and authoritative for its own moment:

* Audit — [`2026-07-28_amarolab_technical_audit.md`](2026-07-28_amarolab_technical_audit.md)
* Backup diagnosis — [`2026-07-28_backup_retention_incident.md`](2026-07-28_backup_retention_incident.md)
* I-4 fix and its predictions — [`2026-07-31_I4_gate8_closeout.md`](2026-07-31_I4_gate8_closeout.md)
* F6.1 status — [`2026-07-28_phaseF_F6_1_step2_handoff.md`](2026-07-28_phaseF_F6_1_step2_handoff.md)

---

## 1. Why this record exists

The triad was last reconciled on 2026-07-31 at the I-4 Gate 8 closeout. Seventeen nightly
cycles have run unattended since, and the platform has been through a reboot and a second
service outage. Two triad claims had gone false in the interval:

| Triad claim (2026-07-31) | Reality on 2026-08-17 |
|---|---|
| `zigbee2mqtt` "down since 2026-07-28 15:52 … deliberately not restarted" | It restarted automatically at the 2026-08-12 reboot, ran five days, and **exited again today at 13:12:24 CEST** |
| Platform `degraded` because of the Zigbee outage | Platform `degraded` **for a different reason** since 2026-08-01 — an empty audit log (§6) |

`PROJECT_RULES.md` → *Transient Operational Status* names this exact failure: a document that
asserts a held state is false the moment the state moves without it. "Deliberately not
restarted" was true when written and was silently undone by a reboot four days later.

---

## 2. Host reboot — 2026-08-12 09:28 CEST

The previous boot (started 2026-07-28 13:29:31 CEST) **terminated at 2026-08-12 09:24:12 CEST
with no shutdown sequence recorded**; the journal's final entries are ordinary `tailscaled`
traffic. The system returned at **09:28:04 CEST**, a gap of approximately four minutes.

The absence of a shutdown sequence is consistent with an unclean power interruption — the same
signature as the 2026-07-28 13:28:48 event. **The cause is not established** from the evidence
available in this read-only pass, and no cause is asserted here.

Consequences that matter downstream:

* Every container restarted at boot — all seventeen, `zigbee2mqtt` included. Sixteen are
  running now; the seventeenth is the subject of §3.
* The 2026-08-12 nightly backup had already run at 03:00 (`c8e1bfaa`), so no backup was lost.
* `zigbee2mqtt` came back too — see §3.
* `aurora-whisper` was **restarted, not recreated** — see §7.

---

## 3. Zigbee2MQTT — third C-1 recurrence, 2026-08-17 13:12:24 CEST

### 3.1 The July outage ended without being recorded

`zigbee2mqtt` started at **2026-08-12T07:28:13Z (09:28:13 CEST)** — thirteen seconds after boot.
This is consistent with Docker restoring an `unless-stopped` container at daemon start; the
container had exited from a crash, not from `docker stop`, so the policy applied. No operator
action is required to explain it, and none is evidenced.

It then **ran healthily for five days**, publishing device telemetry every ten seconds until
13:12:21 today. The July outage therefore ended on 2026-08-12 and the triad was never told.

### 3.2 The new event

| Timestamp (CEST) | Source | Event |
|---|---|---|
| 13:12:24.914410 | kernel | `usb 1-2.2.2: USB disconnect, device number 6` — coordinator leaves the bus |
| 13:12:24.915391 | kernel | `cp210x ttyUSB0: cp210x converter now disconnected from ttyUSB0` |
| 13:12:24.946 | zigbee2mqtt | `Adapter disconnected, stopping` → `Stopping Zigbee2MQTT (restart=false, code=2)`; container exits `ExitCode 2` |
| 13:12:25.079889 | dockerd | `restarting container … restartCount=1 restartPolicy="{unless-stopped 0}"` |
| 13:12:25.091393 | kernel | `usb 1-2.2.2: new full-speed USB device number 8` — re-enumeration begins |
| **13:12:25.100290** | dockerd | `restartmanger wait error: error gathering device information while adding custom device "/dev/serial/by-id/usb-ITead_Sonoff_Zigbee_3.0_USB_Dongle_Plus_<DEVICE_ID>-if00-port0": no such file or directory` |
| **13:12:25.201401** | kernel | `cp210x converter now attached to ttyUSB0` — device node back, **101 ms after the restart had already failed** |

**Exactly one restart attempt exists in the Docker journal**, then and since (`RestartCount` 1).
The failure was a *start* error rather than a container exit, so the restart manager terminated
instead of backing off — identical to the 2026-07-28 behaviour, and confirming it a second time.

The margin is **101 ms**. On 2026-07-28 it was 80 ms. The race is being lost consistently by
roughly a tenth of a second.

### 3.3 What is new relative to 2026-07-28 — there was no trigger

The 2026-07-28 15:52 recurrence was triggered by a Bluetooth adapter being hot-plugged into the
hub shared with the coordinator. **Today there was no such event.**

* **Zero USB enumerations** occurred between 2026-08-17 00:00 and the disconnect at 13:12:24.
* The Realtek/ASUS Bluetooth Controller has been **resident since the 2026-08-12 boot**
  (enumerated 09:28:04 at port `1-2.2.4`) and was not touched today.

The topology is unchanged and still shared:

```
Bus 001 → Port 2 (2-port hub) → Port 2 (4-port external hub, 1-2.2)
                                   ├── Port 2 → Sonoff Zigbee 3.0 USB Dongle Plus (cp210x)
                                   └── Port 4 → Bluetooth Controller (btusb)
```

**This materially widens the failure mode.** The 2026-07-28 record could be read as "hot-plugging
into the shared hub resets it". Today shows the coordinator can drop off the bus **with no
observable external cause**, on a hub that nobody touched. Any future S-9 design must therefore
handle spontaneous disconnects, not only hot-plug-induced ones.

### 3.4 S-9 — supporting evidence

**Problem demonstrated.** A coordinator disconnect — this time unprovoked — permanently stops the
service, because Docker resolves `--device` once at container start and makes exactly one restart
attempt, which loses a ~100 ms race against udev.

**Acceptance criterion (unchanged from the 2026-07-31 entry).** Zigbee2MQTT must recover
automatically from a temporary coordinator disconnect without manual intervention, provided the
adapter returns.

**Status.** **S-9 remains Open.** This section is evidence only; it designs nothing.

### 3.5 M-1 / M-A — supporting evidence

**Problem demonstrated, for the second time.** The outage began at 13:12 and was still unknown to
any human seven hours later, when it was found by inspection at the start of this session — not
by monitoring.

Unlike the July recurrence, the signal layer has **not yet** recorded this one: the nightly chain
runs at 04:00–04:25 and the failure occurred at 13:12, so `container_status.json` and
`aurora-context.json` still describe a healthy Zigbee stack from this morning's cycle. The
awareness pipeline is nightly by design; it is not, and was never intended to be, a monitor.

That is the point M-1 makes. Aurora can *describe* the outage — tomorrow at 04:15. Nothing carries
it to a person today.

**Acceptance criterion (unchanged).** A critical service failure must notify the operator within a
defined time budget.

**Status.** **M-1 / M-A remain Open.** Evidence only.

### 3.6 Current state — untouched

The container is `exited (2)` and **has deliberately not been restarted**. The adapter is present
and free: `/dev/ttyUSB0` and the `by-id` symlink were recreated at 13:12:25 and both resolve; the
CP210x bridge is bound to `cp210x`; no process or container holds it; no further re-enumeration
has occurred since 13:12:25. The configured device path is correct and was never the problem.

Recovery is a **separate, operator-approved intervention** and is not performed by this document.

---

## 4. I-4 continues to hold — eighteen further nights

The grouping fix has now been exercised across **eighteen consecutive unattended nights**
(2026-07-31 → 2026-08-17) beyond the two that closed Gate 8.

| Check | Evidence |
|---|---|
| Nightly continuity | Snapshots on every date 2026-07-31 (`34def61f`) through 2026-08-17 (`fe0409fb`) — **no missed nights** |
| Parent detection | Working throughout; the current log shows the chain `17990ec0` → `c1707709` → `fe0409fb` |
| Installed script unchanged | sha256 `90e8eb91…a907a45f` — byte-identical to the Gate-8-validated version |
| `SNAP_DIR` | Still the undated `/tmp/homelab-backup-snapshots` |
| Reboot resilience | The 2026-08-12 reboot did not disturb the schedule; that night's backup had already run |

**G-I4-1 … G-I4-12 are not reopened.** They closed on 2026-07-31 and that closure is history
(`PROJECT_RULES.md` → gate closures are not re-litigated). This section records *continuing*
operational evidence, which is a different thing.

---

## 5. Retention dry-run evidence — the S-10 input

The I-4 closeout predicted the first would-remove report "on or shortly after **2026-08-04**" and
instructed a future session to check the nightly log. **Checked. The prediction was correct.**

The 2026-08-04 run produced no report. **The first report is dated 2026-08-05.**

| Backup date | Snapshot | Would-remove count |
|---|---|---|
| 2026-08-04 | `599d98f8` | — (none) |
| **2026-08-05** | `f41248e1` | **1** — first report, `{89966886}` |
| 2026-08-06 | `98bcc984` | 2 |
| 2026-08-07 | `9f37d45d` | 2 |
| 2026-08-08 | `5818569e` | 3 |
| 2026-08-09 | `82a8ca75` | 3 |
| 2026-08-10 | `9b50911b` | 4 |
| 2026-08-11 | `f889868d` | 5 |
| 2026-08-12 | `c8e1bfaa` | 6 |
| 2026-08-13 | `e26fd520` | 7 |
| 2026-08-14 | `a2d44417` | 8 |
| 2026-08-15 | `17990ec0` | 9 |
| 2026-08-16 | `c1707709` | 9 |
| **2026-08-17** | `fe0409fb` | **10** |

Latest reported set (2026-08-17):

```
106316a6  39c4f6fe  5818569e  599d98f8  89966886
98bcc984  9b50911b  9f37d45d  d03f0e19  f41248e1
```

### Nothing was removed

* **13 reports, all phrased `Would have removed the following snapshots:`** — restic's dry-run
  wording. Thirteen reports across thirteen nights, 2026-08-05 → 2026-08-17.
* **Zero real deletions anywhere in the log history** — no `removed snapshot`, no deletion of any
  kind, in the current log or any of the eight rotated predecessors.
* `--dry-run` is present in the installed script and was not touched.

### Two observations that belong to S-10 and I-6

1. **The would-remove set now includes `89966886` and `d03f0e19`** — the two post-fix snapshots
   that closed Gate 8. They are ordinary `nightly`-tagged snapshots with no protection, and the
   policy is correctly proposing them as it ages past `--keep-daily 7`. Expected, not a defect,
   but worth knowing before S-10 runs for real.
2. **The D-1.5 anchor `63c072f4` has appeared in no report — not once.** It survives because it
   sits in a legacy dated group of one that no future snapshot can join. That is **group shape,
   not protection**, and it is exactly the risk the I-4 closeout named: *never rely on group shape
   for protection*. **I-6 remains required before S-10.**

**Status.** **S-10 remains Open and unapproved.** This is the input it needs, not a decision.
Nothing here authorizes deletion.

---

## 6. Audit-liveness degradation since 2026-08-01

The platform reports `overall_status: degraded`, and **since 2026-08-01 the reason has been the
audit log, not the Zigbee outage**.

**Mechanism, established read-only:**

* `logrotate` rotates `/srv/homelab/data/openwebui/amarolab-audit.log` **monthly** (E4-a config,
  `rotate 12`, `create 0644 root root`).
* It rotated at **2026-08-01 00:00**, creating a new empty file. July's content is intact in
  `amarolab-audit.log.1`; its final entry is `2026-07-28T16:09:40Z` (a `rag_search` call).
* **No Aurora tool call has been made since**, so the new file is still **0 bytes**.
* `bin/check-audit-liveness` reads the last entry, finds none, and writes
  `audit: {last_entry_ts: null, age_days: null, status: "missing"}` into `health.json`.
* `overall_status` therefore computes to `degraded`, and `bin/aurora-context` has carried
  `degrades=['audit log missing']` on **every nightly cycle since 2026-08-01**.

**Assessment.** The underlying cause is benign — monthly rotation plus genuine non-use, not a
broken audit path. The code is present and worked as recently as 2026-07-28. But two things are
worth recording:

1. This is the **symptom shape of F-10** (audit log stale, closed at E5-c on 2026-06-27) returning
   through a *different* mechanism. The probe cannot distinguish "nobody used the tools" from "the
   audit path is broken", and answers `missing` for both.
2. It has pinned the platform at `degraded` on **every nightly cycle since 2026-08-01**. A
   permanently-degraded status is a status that stops being read — and it masked the fact that the
   Zigbee anomaly had *cleared* on 2026-08-12 and returned today. This is the S-8 / M-A concern
   showing up in a new place.

**No fix is applied and none is authorized here.** Recorded as an observation; it has no
remediation identifier, on the R-I3-1…7 and F-S1-1/F-S1-2 precedent.

---

## 7. F6.1 baseline survived the reboot — no container recreation

**D-F6-1 holds.** `aurora-whisper` was restarted by the reboot, not recreated:

| Property | F6.1 pin (2026-07-28 handoff) | Measured 2026-08-17 | Verdict |
|---|---|---|---|
| Container created | (original container) | `2026-06-17T14:21:14Z` | Unchanged — not recreated |
| Image id | `sha256:966e1b09…a58dd158` | `sha256:966e1b09…a58dd158` | **Identical** |
| Command | `--model base-int8 …` | `--model base-int8 --language auto --beam-size 1 --compute-type int8` | Unchanged |
| `RestartCount` | 0 | 0 | Unchanged |
| `StartedAt` | `2026-07-25T21:50:55Z` | `2026-08-12T07:28:13Z` | **Moved** (reboot) |

The handoff recorded `started 2026-07-25T21:50:55Z` as part of the baseline pin, and that value
has moved. The container identity, image and decoding parameters — the properties the
single-variable isolation of D-F6-1 actually protects — are all unchanged, so the Step 2 baseline
stands. The timestamp change is recorded here so a future session does not read the moved value as
evidence of recreation.

The repo-external corpus and tooling under `/home/diego/f6_1_corpus/` and `/home/diego/f6_1_baseline/`
are present and untouched. **F6.1 remains stopped after Step 2a**; nothing in this record advances it.

---

## 8. Triad corrections applied

| Document | Correction |
|---|---|
| `CURRENT_STATE.md` | Zigbee2MQTT section rewritten to the 2026-08-17 event; "down since 2026-07-28 / not restarted" removed as false. Overall health and Production restated. Backups section gains the retention dry-run trail. Audit-liveness observation added. Next milestone left at **I-5** |
| `ROADMAP.md` | New dated subsection under *Infrastructure Remediation* for the 2026-08-17 recurrence and the retention evidence. S-9 / M-A / S-10 / I-6 entries gain pointers to it; **all four remain Open** |
| `AMAROLAB_HANDOFF.md` | Header and *Next Immediate Task* reconciled: I-5 is still next; the Zigbee paragraph corrected; the F6.1 constraint restated with the baseline-integrity finding |

The 2026-07-28 audit, the backup incident record and the I-4 Gate 8 closeout are **dated records
and are not rewritten**. §3 and §5 above are the corrections to their forward-looking statements.

---

## 9. What this document does not do

* It does **not** restart `zigbee2mqtt`, or design S-9.
* It does **not** touch `--dry-run`, `--prune`, `--group-by`, or any snapshot.
* It does **not** approve, scope or begin S-10, I-6, S-8 or M-A.
* It does **not** fix the audit-liveness degrade.
* It does **not** begin I-5, which remains the next remediation milestone.
* It does **not** advance F6.1.

---

## 10. Git gate

Documentation-only. **Not committed, not pushed** — both require explicit operator approval
immediately before the command (`PROJECT_RULES.md` → *Operator Git Approval*). Author as
`Diego <diego@diegoamaro.dev>`.

**STOP at git gate.**
