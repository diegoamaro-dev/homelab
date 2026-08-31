# Zigbee2MQTT — C-1 Fourth Recurrence — occurred 2026-08-22, discovered 2026-08-31

**Date:** 2026-08-31 — investigation opened 23:46 CEST; record written 2026-09-01, shortly
after midnight CEST.
**Type:** Dated operational record. Read-only investigation. Not a remediation item and not a
phase.
**Production changed by this document:** **no.** No container was started, stopped, restarted
or recreated. No compose file, USB mapping, restart policy, Zigbee2MQTT configuration,
Mosquitto configuration or Docker setting was modified. No host reboot, no restic operation,
no cron change.
**Commands executed:** read-only inspection only — `docker ps` / `docker inspect` /
`docker logs` / `docker top`, `journalctl`, `lsusb`, `ls`, `ss`, file reads, and one
authenticated read-only `GET /api/states` against Home Assistant.
**Result:** the **fourth** C-1 recurrence is confirmed. It occurred on **2026-08-22**, not on
2026-08-31. The service was **already healthy** when the investigation began.
**What this does NOT do:** it does **not** fix **S-9**, it does **not** close **M-1** or
**M-A**, and it establishes **no** stability claim.

> Dated record. States what was true on 2026-08-31 / 2026-09-01 and is **not** rewritten as the
> situation advances (`PROJECT_RULES.md` → *Historical Documentation*).

Companion records — the previous occurrence, its mechanism and its recovery:
[`2026-08-17_zigbee2mqtt_recovery.md`](2026-08-17_zigbee2mqtt_recovery.md) and
[`2026-08-17_operational_reconciliation.md`](2026-08-17_operational_reconciliation.md) §3.
Live tracking: `ROADMAP.md` → *C-1 recurrence 2026-08-22 21:35*.

---

## 1. Why this investigation was opened

The operator reported that the main server had unexpectedly powered off and rebooted, that
Zigbee2MQTT had not recovered correctly, and that the Zigbee devices were disconnected. A
read-only diagnosis was requested before any recovery action.

**The reported premise did not hold, in two separate ways.** Both are evidenced in §2:

1. The Zigbee outage **did not begin with the 2026-08-31 reboot**. It began on **2026-08-22**
   and had been running for nine days.
2. Zigbee2MQTT was **already running and healthy** when the investigation started. The reboot
   had restored it approximately eight minutes earlier.

The operator's report was accurate for the nine days preceding the reboot and became stale
roughly one minute after it.

---

## 2. OBSERVED

### 2.1 The fourth C-1 recurrence occurred 2026-08-22 at 21:35:11 CEST

Reconstructed nine days after the fact from the kernel journal, the `dockerd` journal and
Zigbee2MQTT's own session log. Same-second ordering preserved.

| Timestamp (CEST) | Source | Event |
|---|---|---|
| 21:35:11 | kernel | `cp210x ttyUSB0: usb_serial_generic_read_bulk_callback - urb stopped: -32` |
| 21:35:11 | kernel | `usb 1-2.2.2: USB disconnect, device number 6` |
| 21:35:11 | kernel | `cp210x converter now disconnected from ttyUSB0` — the `by-id` symlink ceases to exist |
| 21:35:11 | zigbee2mqtt | `zh:zstack:znp: Port closed` → `error: Adapter disconnected, stopping` |
| 21:35:11 | zigbee2mqtt | `Stopping Zigbee2MQTT (restart=false, code=2, signal=undefined)` |
| 21:35:11 | dockerd | `restarting container … exitCode=2 restartCount=1 restartPolicy="{unless-stopped 0}"` — the single restart attempt |
| 21:35:11 | dockerd | `restartmanger wait error: error gathering device information while adding custom device "/dev/serial/by-id/usb-ITead_Sonoff_Zigbee_3.0_USB_Dongle_Plus_<DEVICE_ID>-if00-port0": no such file or directory` |
| 21:35:11 | kernel | `usb 1-2.2.2: new full-speed USB device number 8` — the coordinator re-enumerates |
| 21:35:11 | kernel | `cp210x converter now attached to ttyUSB0` — the symlink returns, after the restart had already failed |
| **21:35:14** | kernel | `usb 1-2.2.2: USB disconnect, device number 8` — **the device drops off the bus a second time, three seconds later** |

Container exit is recorded as `FinishedAt 2026-08-22T19:35:11.392083034Z` (UTC).

The session that failed had started **2026-08-21 17:54:37 CEST**, after the 2026-08-21 boot.
It ran approximately **27 h 40 m** before exiting.

### 2.2 The service was unavailable for approximately nine days

| Anchor | Value |
|---|---|
| Exit | 2026-08-22 21:35:11 CEST |
| Container restarted | 2026-08-31 23:38:37 CEST (by Docker at boot) |
| Service operational (MQTT online, devices joined) | 2026-08-31 23:38:46 CEST |
| **Total unavailability** | **9 d 02 h 03 m 35 s** |

For comparison, the third occurrence lasted **8 h 02 m 49 s**. This one is longer by roughly a
factor of 27.

Exactly **one** restart attempt exists in the Docker journal for this occurrence. After it
failed, the container remained `exited` and Docker did not try again.

### 2.3 The failure was not detected operationally during that interval

No alert, no notification and no operator awareness occurred between 2026-08-22 21:35 and the
2026-08-31 reboot. The outage was not discovered while it was in progress; it was reconstructed
**after** it had already ended, during an investigation opened for a different reason.

The nightly signal layer runs 04:00–04:25 and is awareness by design, not a monitor — the same
condition recorded as **M-1** at the previous two occurrences.

### 2.4 The 2026-08-31 host reboot incidentally restored the service

| Timestamp (CEST) | Event |
|---|---|
| 2026-08-31 23:37:42 | Previous boot's journal ends abruptly; no shutdown markers present |
| 2026-08-31 23:38:28 | Host boots |
| 2026-08-31 23:38:29 | `cp210x converter now attached to ttyUSB0` — coordinator re-enumerated cleanly |
| 2026-08-31 23:38:37 | Docker starts the container under its `unless-stopped` policy |
| 2026-08-31 23:38:42 | Zigbee2MQTT 2.9.1 banner; `Serialport opened` |
| 2026-08-31 23:38:46 | `zigbee-herdsman started (resumed)`; 10 devices joined; MQTT connected; bridge `online` |

The boot re-enumerated the USB device before Docker resolved the `--device` mapping, which is
precisely the step that had failed on 2026-08-22. **The restoration was a side effect of an
unrelated host event, not a recovery action.**

The host event itself is recorded separately — see
[`2026-08-31_unclean_host_shutdowns_finding.md`](2026-08-31_unclean_host_shutdowns_finding.md).
**No causal relationship between that event and C-1 is asserted here.**

### 2.5 Current Zigbee state is healthy

Verified 2026-09-01 00:03:34 CEST, 24 minutes after the container start.

| Check | Observed |
|---|---|
| Container | `running`, `RestartCount 0`, no `restarting` state |
| Startup | clean 2.9.1 banner, `zigbee-herdsman started (resumed)` — resumed, not reset |
| Coordinator | `Serialport opened`; firmware `ZStack3x0`, revision 20210708 |
| Zigbee network | **10 of 10 devices joined**, all enumerated by name, **no re-pairing required** |
| MQTT | `Connected to MQTT server`; `zigbee2mqtt/bridge/state` → `{"state":"online"}` |
| Home Assistant | `binary_sensor.zigbee2mqtt_bridge_connection_state` = `on`; `switch.impresora_3d` = **`off`** (its documented baseline, **no actuation**); `cover.toldo` = `closed`; occupancy and contact sensors reporting |
| Container fleet | **17/17 running**, 0 stopped, 0 restarting |
| Failure markers in the current session log | **0** |
| Kernel USB disconnects since the container start | **0** |

The device count matches the network size documented at I-7 (2026-07-28) and re-confirmed at
the 2026-08-17 recovery.

**Entities reading `unknown` are not faults and were checked individually:**
`button.zigbee2mqtt_bridge_restart` has no state until pressed; the `number.*` timeout and
`select.*` sensitivity entities are published by Zigbee2MQTT as `null`. Home Assistant also
reports several `media_player.*` entities as `unavailable` — these are Google Cast devices,
**not Zigbee**, and are unrelated to this record.

### 2.6 No recovery command was required or executed on 2026-08-31

Because the service was already healthy when the investigation began, **no recovery action was
proposed and none was executed.** Starting or restarting the container would have been an
intervention without a cause, and would have re-resolved the `--device` mapping unnecessarily.

This is the first C-1 occurrence that ended **without** an operator-approved recovery command.

### 2.7 This occurrence captured the failure mechanism with stronger evidence

The 2026-08-17 record characterised the mechanism as Docker resolving `--device` once at start
and making exactly one restart attempt, losing a **101 ms** race against udev recreating the
`by-id` symlink. That characterisation is unchanged. This occurrence adds three things the
previous one did not have:

1. **A kernel-level trigger is present and logged.** `urb stopped: -32` followed by an explicit
   `USB disconnect`. The 2026-08-17 occurrence was recorded as having **no observable trigger**.
2. **A second disconnect three seconds later** (`device number 8`), indicating the device did
   not simply drop once and settle.
3. **Nine days of post-failure quiescence** confirming that Docker's `unless-stopped` policy
   makes exactly one attempt and then stops permanently — previously inferred from a single
   journal entry, now demonstrated over a nine-day interval.

The evidence was captured from the journal **before** any restart, satisfying the instruction
the 2026-08-17 entry left for a future session — though by circumstance rather than by
discipline, since no restart was ever performed.

---

## 3. INTERPRETATION

Stated as interpretation, not as observation.

1. **This is the same documented C-1 failure mode.** The evidence supports the classification:
   identical exit signature (`Adapter disconnected, stopping`, `code=2`, `restart=false`),
   identical single-restart behaviour, and the identical `restartmanger` device-resolution
   error naming the same `by-id` path. This is the **fourth** occurrence.

2. **This materially strengthens the case for S-9.** The structural condition — a coordinator
   whose device node can disappear, combined with Docker resolving the mapping once and
   retrying once — is unchanged and has now produced four outages. The fourth demonstrates the
   worst property of the mechanism: **the failure is silent and permanent until something
   unrelated restarts the container.** **S-9 remains Open. Stronger evidence is not
   remediation.**

3. **The nine-day undetected outage materially strengthens M-1 / M-A.** The previous entry
   recorded seven hours unnoticed. This one records nine days, and was found only because an
   unrelated incident prompted an inspection. The acceptance criterion is unchanged — a
   critical service failure must notify the operator within a defined time budget — and nothing
   in this record satisfies it. **M-1 and M-A remain Open.**

4. **The prediction the previous entry carried was correct.** It stated that on three
   occurrences in three weeks a fourth was expected, and that a fourth would be found by
   inspection rather than by monitoring. Both held. The dated record is not rewritten
   (`PROJECT_RULES.md` → *Historical Documentation*); this is the confirmation.

---

## 4. UNKNOWN

Recorded explicitly so that no reader infers more than the evidence supports.

1. **The root physical cause of the USB disconnect is unknown.** A kernel-level disconnect was
   observed. *Why* the device left the bus was not determined.

2. **Whether the dongle, the hub, the USB path, power delivery or any other hardware factor
   caused it is unknown.** No hardware diagnosis was performed, no component was swapped,
   isolated or tested. **No hardware root cause is claimed by this record**, and none may be
   inferred from it.

3. **Whether the second disconnect three seconds later indicates device instability, hub
   instability or a transient condition is unknown.** It is recorded because it is evidence,
   not because it has been explained.

4. **Whether the 2026-08-31 host event and the 2026-08-22 coordinator disconnect share any
   common cause is unknown**, and no such link is asserted. They are separated by nine days and
   are tracked as separate findings.

---

## 5. Secondary observation — Mosquitto log file (out of scope, not fixed)

`mosquitto` logs `Error: Unable to open log file /mosquitto/log/mosquitto.log for writing` at
every start. The broker operates normally: its configuration declares both a file destination
and `stdout`, and the `stdout` fallback works — the broker restored 92 retained messages, is
listening, and Zigbee2MQTT connects to it without error.

**Recorded for later triage only. Not diagnosed, not fixed, out of scope for this incident.**
It is pre-existing and unrelated to C-1.

---

## 6. Method and limits

**Sources of truth used.** Zigbee2MQTT's own per-session log files under the data bind mount
(`log/<session>/log.log`), the kernel and `dockerd` journals, `docker inspect`, and one
read-only Home Assistant `GET /api/states`.

**A method caveat worth preserving.** `docker logs zigbee2mqtt --since <time>` returned **zero
lines** for windows that demonstrably contained log entries, verified by contrast with
`docker logs --tail N --timestamps`, which returned current entries from the same window. The
container's json log has accumulated since 2026-04-01 with no rotation configured. Taken at
face value, the empty result would have supported the false conclusion that the container was
running but producing no output. **It was not used as evidence.** Every timeline in this record
derives from Zigbee2MQTT's own session logs and the systemd journal. The cause of the `--since`
behaviour was not investigated and is unknown.

**Limits.** The reconstruction is nine days after the fact and depends on journal retention,
which was sufficient for the relevant boots. Kernel and `dockerd` evidence for the failure
instant exists and is quoted. No evidence was captured *at* the moment of failure, because
nothing observed the failure.

---

## 7. Git gate

Documentation only. **Not committed, not pushed** — both require explicit operator approval
immediately before the command (`PROJECT_RULES.md` → *Operator Git Approval*). Author as
`Diego <diego@diegoamaro.dev>`.

**STOP at git gate.**
