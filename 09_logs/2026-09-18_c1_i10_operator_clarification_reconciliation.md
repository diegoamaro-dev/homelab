# C-1 / I-10 — Operator Clarification Reconciliation — 2026-09-18

**Date:** 2026-09-18
**Type:** Dated reconciliation record. Read-only fact reconstruction, before S-7. Not a
remediation item and not a phase.
**Production changed by this document:** **no.** No container was started, stopped, restarted
or recreated. No host reboot (a pending `/var/run/reboot-required` was observed and deliberately
**not** acted on). No Zigbee2MQTT, Mosquitto, Docker, restic, retention or cron change.
**Commands executed:** read-only only — `journalctl` (per boot, kernel, `dockerd`), `last -x`,
`docker inspect` / `docker ps`, file reads of the Zigbee2MQTT session logs and the Home
Assistant log files, the local assistant session transcript of 2026-08-31, the apt history, and
authenticated read-only `GET /api/states` / `GET /api/history` against Home Assistant.
**Result:** the 2026-08-31 Zigbee record is **confirmed** — no recovery command was executed. The
2026-08-31 I-10 record contains **one factual error** (journal retention), and **I-10 is closed as
a host-fault finding**: the operator reports having caused every unclean stop in the journal by
holding the power button. **C-1, S-9, M-1 and M-A are unchanged and stay Open.**

> Dated record. States what was true on 2026-09-18 and is **not** rewritten as the situation
> advances (`PROJECT_RULES.md` → *Historical Documentation*). The two 2026-08-31 records it
> corrects are **left exactly as written**; this document is the correction.

Records reconciled:
[`2026-08-31_zigbee2mqtt_c1_fourth_recurrence.md`](2026-08-31_zigbee2mqtt_c1_fourth_recurrence.md)
and [`2026-08-31_unclean_host_shutdowns_finding.md`](2026-08-31_unclean_host_shutdowns_finding.md).

---

## 1. Why this reconciliation was opened

Before starting S-7 the operator raised two clarifications that potentially conflicted with the
published 2026-08-31 records:

1. **The unclean shutdowns tracked as I-10 were not spontaneous** — the operator caused them.
2. **The operator did not remember precisely** whether, on 2026-08-31, the assistant had actually
   executed a recovery command for Zigbee2MQTT, or had only discovered during diagnosis that the
   service had already recovered. The published record states the latter.

The operator explicitly asked that neither their recollection nor the published record be
assumed correct, and that the facts be reconstructed first. This document keeps four categories
strictly apart: **OBSERVED** (evidence read on the host), **OPERATOR-REPORTED** (the operator's
statement, not independently verifiable per event), **INFERRED**, and **UNKNOWN**.

---

## 2. OPERATOR-REPORTED

Stated by the operator on 2026-09-18. **These are statements, not technical evidence**, and are
recorded as such.

| # | Statement |
|---|---|
| **O-1** | The unclean host stops were **caused manually by the operator**, by **holding the power button** (long press). |
| **O-2** | The scope of O-1 is **all** of them — including **2026-09-02** and the stops from **May to July 2026**. The operator confirms this as a class; it is not a per-boot recollection. |
| **O-3** | The operator's 2026-08-31 description, *"The UM790 unexpectedly powered off/rebooted"*, was a **misstatement**: that stop was caused by the operator. The operator states this with full certainty. |
| **O-4** | After the 2026-08-31 boot the operator saw the Zigbee devices as disconnected and asked for them to be reactivated. |

Not stated and therefore **UNKNOWN**: *why* the operator powered the host off on 2026-08-31 — in
particular, whether it was prompted by the (then nine-day) Zigbee outage.

---

## 3. Zigbee2MQTT on 2026-08-31 — did anything change production?

### 3.1 OBSERVED timeline (CEST)

| Time | Event | Source |
|---|---|---|
| 08-22 21:35:11 | Fourth C-1 exit; Docker's single restart attempt fails (`restartmanger … no such file or directory`) | `dockerd` journal |
| 08-22 → 08-31 | **No** container start for `zigbee2mqtt` in the rest of that boot (no `sbJoin`, see §3.2) | `dockerd` journal |
| 08-31 23:37:42 | Previous boot's journal ends on routine network-daemon traffic; **no** `Power key pressed`, **zero** shutdown markers | journal |
| 23:38:28 | Host boots (46 s gap) | journal |
| 23:38:35 | `dockerd` starts; `error unmounting container … layer not mounted` for **16** containers and `Removing stale sandbox` — Docker itself found the previous stop unclean | `dockerd` journal |
| **23:38:37.9** | **Docker starts `zigbee2mqtt` under `unless-stopped`** (`StartedAt`); network join `sbJoin` at 23:38:38 — the **only** one in that boot | `docker inspect`, `dockerd` |
| 23:38:42 | Zigbee2MQTT 2.9.1 banner, `Serialport opened` — **coordinator operational** | Zigbee2MQTT session log |
| **23:38:46** | `zigbee-herdsman started (resumed)`, **10 devices joined**, `Connected to MQTT server`, bridge `online`, `Zigbee2MQTT started!` | Zigbee2MQTT session log |
| 23:38:48 | First live device telemetry; then every ~10 s | Zigbee2MQTT session log |
| **23:38:51 → 23:39:28** | Home Assistant: bridge connection `on` (23:38:51), `switch.impresora_3d` `off` (23:38:58), sensors and `cover.toldo` (23:39:14–23:39:28) — **devices available in HA** | `GET /api/states` output saved in the session transcript |
| 23:45:50 | Operator asks for recovery, describing the devices as currently disconnected (O-4) | session transcript |
| 23:46:15 | First assistant command. At 23:46:37 `docker inspect` already reports `running`, `StartedAt 23:38:37`, `RestartCount 0` | session transcript |
| 23:56:11 | Assistant reports that the service had recovered on its own and that no action was needed | session transcript |

### 3.2 No production-changing command was executed — three independent sources

1. **Session transcript.** The 2026-08-31 session made **94** tool calls, all shell commands.
   A full-text scan of every command finds **zero** `docker start|restart|stop|kill|rm|run|update|compose`,
   **zero** `systemctl start|restart|stop|reload`, **zero** `sudo`, **zero** HTTP `POST`. The only
   call to a production service was one read-only `GET /api/states`. It is the only assistant
   session transcript on this host dated between 2026-08-31 and 2026-09-02.
2. **`dockerd` journal, with a positive control.** Every container start leaves one `sbJoin` line
   for `ep=zigbee2mqtt`. The two known manual `docker start` recoveries — 2026-07-28 02:49 and
   2026-08-17 21:15 — each left one. The 2026-08-31 boot contains **exactly one**, at 23:38:38,
   i.e. the start by Docker at boot. This also rules out a manual start by any other route
   (CLI, Portainer) during that boot.
3. **Zigbee2MQTT's own session logs.** One directory is created per process start. Between
   2026-08-31 and 2026-09-02 there is **exactly one** session, `2026-08-31.23-38-42`, and
   `RestartCount` stayed `0`.

**Conclusion (OBSERVED):** the operator asked for recovery at 23:45:50, when Zigbee2MQTT had
already been operational since 23:38:46 and visible in Home Assistant since 23:38:51. The
assistant discovered this during diagnosis and executed nothing. **The published statement
*"No recovery command was required or executed"* is correct.**

### 3.3 INFERRED / UNKNOWN about O-4

What the operator saw as "disconnected" is **UNKNOWN**. It is consistent with the evidence if it
was observed before 23:38:51, or if it reflected the nine-day C-1 outage before the power-off.
No claim is made either way.

### 3.4 What the operator's clarification changes for the Zigbee record

The 2026-08-31 record calls the reboot *"an unrelated host event"* and quotes the operator's
report of an unexpected power-off. Per O-3, the stop was **operator-initiated**. The core finding
is unaffected: **no Zigbee-specific recovery action ran**; the service was restored by Docker's
`unless-stopped` start at boot, after the coordinator had re-enumerated. Whether the power-off
was itself *meant* to recover Zigbee is UNKNOWN (§2).

---

## 4. Corrections and additions to the I-10 record

### 4.1 Correction — journal retention (factual error)

The I-10 record states that *"only the eleven retained boots were assessed"* and that *"earlier
boots are outside journal retention"*. **That is incorrect.** On 2026-09-18 the journal retains
**31 boots**, the earliest starting **2026-05-19 13:09:43** — 30 completed boots plus the current
one. Those boots existed on 2026-08-31 as well: the eleven came from a boot list truncated to its
twelve most recent entries in the 2026-08-31 session, not from retention.

### 4.2 Full retained history, same method

Method identical to the I-10 record: count case-insensitive journal matches of
`Powering Off|systemd-shutdown|Reached target.*(Power-Off|Reboot)` per boot; additionally count
`Power key pressed short` / `Power key pressed long` logged by `systemd-logind`.

| Boot | Started (CEST) | Last journal entry (CEST) | Markers | Power key (short) |
|---|---|---|---|---|
| −29 | 2026-05-19 13:09:43 | 2026-05-19 13:09:49 | 0 | 0 |
| −28 | 2026-05-19 13:14:39 | 2026-05-20 09:22:58 | **3** — `reboot.target` | 0 |
| −27 | 2026-05-20 09:23:13 | 2026-05-31 00:48:19 | 0 | 0 |
| −26 | 2026-05-31 00:49:09 | 2026-05-31 00:53:03 | 0 | 0 |
| −25 | 2026-05-31 00:53:23 | 2026-05-31 12:31:20 | 0 | 0 |
| −24 | 2026-05-31 12:32:13 | 2026-06-03 12:55:05 | **3** — `reboot.target` | 0 |
| −23 | 2026-06-03 12:55:21 | 2026-06-08 10:01:48 | 0 | **4** (2026-06-04 12:51, not acted on) |
| −22 | 2026-06-08 10:03:59 | 2026-06-13 23:38:06 | 0 | 0 |
| −21 | 2026-06-14 00:28:06 | 2026-06-14 15:04:15 | 0 | 0 |
| −20 | 2026-06-14 15:04:47 | 2026-06-14 21:03:09 | 0 | 0 |
| −19 | 2026-06-14 22:42:07 | 2026-06-15 01:02:25 | 0 | 0 |
| −18 | 2026-06-15 01:04:11 | 2026-06-15 21:46:40 | 0 | 0 |
| −17 | 2026-06-15 22:13:55 | 2026-06-17 02:06:34 | 0 | 0 |
| −16 | 2026-06-17 02:19:24 | 2026-06-20 18:35:01 | 0 | 0 |
| −15 | 2026-06-21 13:38:03 | 2026-06-27 01:22:40 | 0 | **1** (01:20:53, not acted on) |
| −14 | 2026-06-27 01:23:25 | 2026-06-29 18:32:02 | 0 | 0 |
| −13 | 2026-06-29 18:35:09 | 2026-07-02 22:30:32 | 0 | 0 |
| −12 | 2026-07-02 23:24:17 | 2026-07-04 13:31:38 | 0 | 0 |
| −11 | 2026-07-04 16:23:16 | 2026-07-17 12:40:10 | 0 | 0 |
| −10 | 2026-07-17 12:47:05 | 2026-07-17 13:09:12 | 0 | 0 |
| −9 | 2026-07-17 14:26:59 | 2026-07-20 20:28:57 | 0 | 0 |
| −8 | 2026-07-20 20:29:18 | 2026-07-21 19:44:23 | 0 | 0 |
| −7 | 2026-07-21 19:44:48 | 2026-07-21 19:51:22 | 0 | 0 |
| **−6** | 2026-07-21 19:51:52 | 2026-07-21 19:52:29 | **3** — power-off | **1** (19:51:57, **acted on**) |
| −5 | 2026-07-25 23:50:45 | 2026-07-28 13:28:48 | 0 | 0 |
| −4 | 2026-07-28 13:29:31 | 2026-08-12 09:24:12 | 0 | 0 |
| −3 | 2026-08-12 09:28:04 | 2026-08-21 17:52:08 | 0 | 0 |
| −2 | 2026-08-21 17:54:15 | 2026-08-31 23:37:42 | 0 | 0 |
| −1 | 2026-08-31 23:38:28 | 2026-09-02 13:36:07 | 0 | 0 |
| 0 | 2026-09-02 13:36:39 | *(current boot)* | — | 0 |

Boot indices are relative to 2026-09-18 and are **shifted by one** against the 2026-08-31 record
(its "−5 control case" is −6 here; its "−1" is −2 here). No `Power key pressed long` line exists in
any boot.

**Totals (OBSERVED):** of **30** completed boots, **27** ended with zero markers and **3** ended in
an ordered shutdown — two software reboots (−28, −24) and one power-button power-off (−6).

### 4.3 The power-key control case

Boot −6 (2026-07-21) records the full orderly path:

```
19:51:57 systemd-logind: Power key pressed short.
19:51:57 systemd-logind: Powering off...
19:51:57 systemd-logind: System is powering down.
```

followed by three shutdown markers. A short press handled by the OS **is logged and produces an
ordered shutdown** that the marker test detects.

**Short presses are not always acted on.** Boot −23 logs four short presses on 2026-06-04 12:51
and kept running until 2026-06-08; boot −15 logs one at 2026-06-27 01:20:53 and its journal ends
107 s later **without** markers. `logind.conf` carries no power-key override (defaults).
**INFERRED, not verified:** a graphical session holding a power-key inhibitor would explain this —
in −6 the press came five seconds after boot, before any desktop session existed.

**What the OS cannot see (INFERRED):** a power-button **hold** forces the machine off in firmware,
below the OS; nothing is logged. The same is true of removing power and of a spontaneous hardware
reset. The journal therefore **cannot distinguish** between these three, and this record does not
claim it can. What the evidence *does* establish is that **none of the 27 unclean stops was
initiated by the OS** — where a `Power key pressed` line exists in such a boot (−23, −15), the
press was not acted on and no shutdown sequence followed it.

### 4.4 Addition — the 2026-09-02 unclean stop (OBSERVED, previously unrecorded)

| Item | Observed |
|---|---|
| Last journal entry, boot −1 | 2026-09-02 13:36:07, routine network-daemon traffic |
| Shutdown markers / power-key lines | **0 / 0** |
| Next boot | 2026-09-02 13:36:39 (**32 s** gap); kernel unchanged (`7.0.0-30-generic`) |
| User sessions (`last -x`) | recorded as `crash` |
| `dockerd` at next start | `layer not mounted` for **17** containers, `Removing stale sandbox` ×17 |
| Zigbee2MQTT session `2026-08-31.23-38-42` | last line 2026-09-02 13:36:00, **no** `Stopping` line, file ends in **1591 NUL bytes** — a write in flight when power was lost |
| Home Assistant, 2026-09-02 13:36:58 | *"could not validate that the sqlite3 database … was shutdown cleanly"*; *"Ended unfinished session (id=83 from 2026-08-31 21:38:47 UTC)"* |

Per O-2 this stop is **operator-reported** as a forced power-off. `zigbee2mqtt` came back under
`unless-stopped` at 13:36:49 with no C-1 involvement and has run since (§6).

---

## 5. I-10 — reclassification

**Before:** repeated host shutdowns without normal shutdown markers, **cause unknown**, a possible
spontaneous host fault, investigation Open.

**Evidence (OBSERVED):** 27 of 30 retained boots ended without any OS-initiated shutdown; Docker,
Home Assistant and Zigbee2MQTT independently show the 2026-08-31 and 2026-09-02 stops as
unclean. The evidence is **compatible with** a forced power-off by power-button hold. It is **not
proof of it**: the same evidence would be produced by power removal or a spontaneous reset (§4.3).

**Explanation (OPERATOR-REPORTED):** O-1/O-2 cover **every** one of the 27 unclean stops,
including 2026-09-02 and May–July. **No retained unclean stop is left without an explanation**,
and **every such explanation rests on the operator's statement**, not on per-boot technical
proof. No boot is attributed to the operator individually from the evidence.

**New status: I-10 CLOSED 2026-09-18 as a host-fault finding — explained by operator-initiated
forced power-offs (OPERATOR-REPORTED).** No hardware, firmware, power-supply, thermal or software
fault is indicated, and none is investigated.

**What is not closed — the integrity risk is real, and it is procedural.** The I-10 record's
concern stands: forced stops leave SQLite databases unvalidated, container layers unmounted and
log files truncated, across the whole platform. The cause is now the shutdown *procedure*, and it
is addressed by the operating norm in §7, not by a hardware investigation.

**Reopen condition:** any unclean stop (zero markers, no `Power key pressed` acted on) that the
operator did **not** cause reopens I-10 as a host-fault finding.

---

## 6. What is unchanged

- **C-1 — the fourth recurrence stands** as recorded. Its evidence (2026-08-22 kernel disconnect,
  single failed restart, nine days `exited`) is independent of both clarifications.
- **S-9 Open, M-1 Open, M-A Open.** The fourth occurrence still demonstrates that the failure is
  silent and permanent until something restarts the container. Whether the 2026-08-31 power-off
  was prompted by the operator noticing Zigbee down is UNKNOWN; either way, **no monitor detected
  the outage** and the M-1 acceptance criterion is unmet.
- **No causal link** between the operator's power-offs and C-1 is asserted. The 2026-08-22 C-1
  exit occurred mid-boot, 27 h 40 m after that boot began, with a logged kernel USB disconnect.
- **Current state (verified 2026-09-18 12:03 CEST):** **17/17** containers running;
  `zigbee2mqtt` `running` since **2026-09-02 13:36:49** (Docker start at boot), `RestartCount 0`;
  **zero** failure markers (`Adapter disconnected`, `Stopping`, `error:`) across the retained
  files of the current session; **zero** kernel `USB disconnect` lines this boot; device
  telemetry flowing; Home Assistant bridge connection `on`.

---

## 7. Operating norm — shutting down the UM790

Adopted 2026-09-18 by operator direction and codified as a permanent rule in
`PROJECT_RULES.md` → *Clean Host Shutdown*, which is the normative text. The summary below
records the rule as adopted; the evidence behind it stays in this record, not in the rule.

1. **The UM790 is shut down or rebooted cleanly**, through the normal OS shutdown path:
   `sudo systemctl poweroff` / `sudo systemctl reboot` (or an equivalent normal shutdown), or a
   **short** press of the power button **that is observed to start a shutdown**.
2. **A short press is not guaranteed to act** on this host (§4.3: 2026-06-04, 2026-06-27). If it
   does not start a shutdown, **use the command — do not escalate to holding the button.**
3. **Do not hold the power button and do not cut power**, except in a genuine emergency (the
   host is unresponsive and cannot be reached by any means). Any forced stop is recorded in
   `09_logs/` with its reason.
4. `PROJECT_RULES.md` → *AI Assistant Session Preservation* continues to apply before any
   shutdown or reboot.

A kernel update is pending (`/var/run/reboot-required`, `7.0.0-30` installed 2026-08-22 and
running since 2026-08-31). It was **not** acted on by this reconciliation; the next reboot should
be the first one taken under this norm, and it should produce shutdown markers.

---

## 8. Documentation changed in the same change

- `CURRENT_STATE.md` → *Zigbee2MQTT* still read **"Operational — recovered 2026-08-17 21:15:13"**
  and described the **third** recurrence as **"current state (`RestartCount 1`)"**. Neither was
  updated by the 2026-08-31 reconciliation. Corrected.
- `AMAROLAB_HANDOFF.md` still carried the 2026-08-17 paragraph (*"`zigbee2mqtt` is RUNNING again —
  recovered 2026-08-17 … a fourth is expected"*) as live status. Marked superseded.
- I-10 status updated in all three triad documents.
- The operating norm (§7) added to `PROJECT_RULES.md` as *Clean Host Shutdown* — the rule
  only, without I-10's investigation, boot counts or incident history.

---

## 9. Method and limits

- **Session transcript.** The 2026-08-31 assistant session transcript is local to the operator's
  workstation account and is **not** in the repository. It was read, not modified.
- **Home Assistant history for 2026-08-31 and 2026-09-02 is no longer retained** by the recorder
  (`GET /api/history` returns no rows for those windows). HA timings in §3.1 come from the
  `GET /api/states` output captured in the transcript at 23:51 on 2026-08-31.
- **`docker logs` was not used as timeline evidence**, for the reason recorded in the 2026-08-31
  record §6. Zigbee2MQTT's own session logs, the journal and the HA log files were used.
- **Operator statements are not converted into evidence.** Where this record says *explained*, it
  means *explained by an operator statement consistent with the evidence*.

---

## 10. Git gate

Documentation only. **Not committed, not pushed** — both require explicit operator approval
immediately before the command (`PROJECT_RULES.md` → *Operator Git Approval*).
`ai-stack/ingest/conf/corpora.yaml` is out of scope and is not staged.

**STOP at git gate.**
