# Zigbee2MQTT — C-1 Fifth Recurrence — occurred 2026-09-30, discovered 2026-10-20

**Date:** 2026-10-20 — found during the read-only drift reconciliation recorded in
[`2026-10-20_operational_drift_reconciliation.md`](2026-10-20_operational_drift_reconciliation.md).
**Type:** Dated operational record. Read-only reconstruction. Not a remediation item and not a
phase.
**Production changed by this document:** **no.** No container was started, stopped, restarted
or recreated. No compose file, USB mapping, restart policy, Zigbee2MQTT configuration,
Mosquitto configuration or Docker setting was modified. No host reboot, no restic operation, no
cron change.
**Commands executed:** read-only only — `docker ps` / `docker inspect`, `journalctl` (kernel and
`dockerd`, per boot), file reads of the Zigbee2MQTT session logs and `database.db`, and
authenticated read-only `GET /api/states` / `GET /api/history` against Home Assistant.
**Result:** a **fifth** C-1 recurrence occurred on **2026-09-30 at 23:44:30 CEST**. Zigbee2MQTT
was down for approximately **seven days**, nothing detected it, and it came back **incidentally**
with the 2026-10-07 boot. It was healthy when found.
**What this does NOT do:** it does **not** fix **S-9**, it does **not** close **M-1** or
**M-A**, and it establishes **no** stability claim.

> Dated record. States what was true on 2026-10-20 and is **not** rewritten as the situation
> advances (`PROJECT_RULES.md` → *Historical Documentation*).

Previous occurrence:
[`2026-08-31_zigbee2mqtt_c1_fourth_recurrence.md`](2026-08-31_zigbee2mqtt_c1_fourth_recurrence.md),
with the correction in
[`2026-09-18_c1_i10_operator_clarification_reconciliation.md`](2026-09-18_c1_i10_operator_clarification_reconciliation.md).
Live tracking: `ROADMAP.md` → *C-1 recurrence 2026-09-30 23:44*.

---

## 1. OBSERVED — timeline (CEST)

| Time | Source | Event |
|---|---|---|
| 2026-09-29 01:45:43 | journal | Boot starts. The previous boot ended cleanly (the positive control in the drift record §2). Coordinator attached as `ttyUSB0` |
| 2026-09-30 23:38:37 | kernel | `cp210x ttyUSB0: usb_serial_generic_read_bulk_callback - urb stopped: -32` (×2) |
| 2026-09-30 23:44:30 | kernel | `usb 1-2.2.2: USB disconnect` on the coordinator; `cp210x converter now disconnected from ttyUSB0` |
| 2026-09-30 23:44:30 | Zigbee2MQTT | `error: z2m: Adapter disconnected, stopping` → `Stopping Zigbee2MQTT (restart=false, code=2)` → `Stopped Zigbee2MQTT` |
| 2026-09-30 23:44:31 | kernel | Coordinator re-enumerated, disconnected again within the same second, re-enumerated again and attached as `ttyUSB0` |
| 2026-09-30 23:44:31.041 | `dockerd` | `restarting container … exitCode=2 … restartPolicy="{unless-stopped 0}"` |
| 2026-09-30 23:44:31.061 | `dockerd` | `restartmanger wait error: error gathering device information while adding custom device "/dev/serial/by-id/usb-ITead_Sonoff_Zigbee_3.0_USB_Dongle_Plus_<DEVICE_ID>-if00-port0": no such file or directory` |
| 2026-10-06 14:38:00 | kernel | The coordinator disconnects and re-enumerates once more. Zigbee2MQTT was already stopped |
| 2026-10-07 22:10:18 | journal | Last entry of the boot, with **zero** shutdown markers. This is an unclean stop that the operator reports causing (drift record §2) |
| 2026-10-07 23:55:08 | journal / kernel | New boot; coordinator attached as `ttyUSB0` |
| 2026-10-07 23:55:17 | `docker inspect` | `zigbee2mqtt` `StartedAt`: Docker started it at daemon start under `unless-stopped` |

**Exactly one** `restarting container` entry exists in that boot after 23:44. Docker did not try
again. **No Zigbee2MQTT session was started between 2026-09-30 23:44:30 and the 2026-10-07
boot**: the session directories go from `2026-09-29.01-45-57` straight to
`2026-10-07.23-55-21`.

**Downtime:** 2026-09-30 23:44:30 → 2026-10-07 23:55:17 = **7 d 00 h 10 m 47 s**, measured from
the exit to the next container start.

## 2. OBSERVED — detection and recovery

- **Nothing detected the outage.** It was found on 2026-10-20 by a read-only documentation
  reconciliation, twelve days after it had already ended.
- **Recovery was incidental to the 2026-10-07 boot.** Docker started the container at daemon
  start, as at the fourth occurrence.
- Home Assistant recorder history for 2026-09-30 is **no longer retained**
  (`GET /api/history` returns zero rows for that window). The entities' state during the outage
  was therefore not reconstructed.

## 3. OBSERVED — current state, 2026-10-20 ~01:00 CEST

- `zigbee2mqtt` is `running` since 2026-10-07 23:55:17, with `RestartCount 0`.
- The current session log is being written (last write 2026-10-20 01:03).
- **Zero** coordinator disconnects this boot. The kernel shows only the boot-time `attached`
  line.
- `database.db` holds **10 devices** plus the coordinator.
- `switch.impresora_3d` = `off`, its documented baseline. `cover.toldo` = `closed`, changed at
  2026-10-07 23:56:08, one minute after the container started.
- **No actuation** was performed by this investigation.

## 4. Additional observed context — no causal claim

Recorded because it is evidence, not because it explains anything:

- Six minutes before the disconnect, the kernel logged `urb stopped: -32` on `ttyUSB0`. The
  fourth occurrence also logged `urb stopped: -32`.
- At 23:44:31 a second device on the same hub branch (`1-2.2.4`) disconnected. At 23:44:43 a
  device on `1-1.2` disconnected. At 23:45:33 a USB mass-storage device enumerated on `1-2.2.4`.
- **No relationship between these events and the coordinator disconnect is established or
  asserted.**

## 5. INTERPRETATION

1. **This is the same documented C-1 failure mode, and this is the fifth occurrence.** The
   signature is identical: `Adapter disconnected, stopping` with `code=2` / `restart=false`; one
   Docker restart attempt; and the same `restartmanger` device-resolution error on the same
   `by-id` path.
2. **S-9 stays Open.** The structural condition is unchanged, and the failure was again **silent
   and permanent** until an unrelated event restarted the container.
3. **M-1 and M-A stay Open.** A seven-day undetected outage leaves the M-1 acceptance criterion
   unmet.

## 6. UNKNOWN

1. **The physical cause of the USB disconnect is unknown.** No hardware root cause is claimed.
2. **Whether the hub activity in §4 is related is unknown.**
3. **Whether the operator was aware of the outage before 2026-10-07 is unknown.** So is whether
   the 2026-10-07 stop was prompted by it.
4. **Whether any recovery was attempted between 2026-09-30 and 2026-10-07 is unknown.** The
   evidence shows only that **no** Zigbee2MQTT session started in that window.

## 7. Method and limits

- Timelines come from Zigbee2MQTT's own session logs and the systemd journal. `docker logs` was
  not used as timeline evidence, for the reason in the fourth-occurrence record §6.
- The coordinator's serial number appears in the journal and is redacted here as `<DEVICE_ID>`.
- The non-root journal view used here starts at 2026-09-22 (drift record §2.3). That was
  sufficient for every boot in this timeline.

## 8. Git gate

Documentation only. **Not committed, not pushed.** Both require explicit operator approval
immediately before the command (`PROJECT_RULES.md` → *Operator Git Approval*).
`ai-stack/ingest/conf/corpora.yaml` is out of scope and is not staged.

**STOP at git gate.**
