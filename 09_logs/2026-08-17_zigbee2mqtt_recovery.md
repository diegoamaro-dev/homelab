# Zigbee2MQTT — Operational Recovery — 2026-08-17

**Date:** 2026-08-17
**Type:** Dated operational record. Service recovery, not a remediation item and not a phase.
**Production changed by this document:** **yes, deliberately and minimally** — one container was
started. Nothing else was modified.
**Command executed:** `docker start zigbee2mqtt` (one command, operator-approved immediately
beforehand).
**Result:** **Recovery successful.** All six validation checks PASS.
**What this does NOT do:** it does **not** fix **S-9**, and it establishes **no** claim about
long-term stability.

> Dated record. States what was true on 2026-08-17 and is **not** rewritten as the situation
> advances (`PROJECT_RULES.md` → *Historical Documentation*).

Companion record — the outage itself, its mechanism and its evidence:
[`2026-08-17_operational_reconciliation.md`](2026-08-17_operational_reconciliation.md) §3.

---

## 1. Context

`zigbee2mqtt` exited `code=2` at **2026-08-17 13:12:24 CEST** — the third C-1 recurrence, this
time with no observable trigger. The container was deliberately left `exited` while the outage
was documented and the triad reconciled (commit `c8a931a0`). Recovery was then authorized as a
**separate** intervention.

**Total downtime: 8 h 02 m 49 s** (13:12:24 → 21:15:13 CEST).

---

## 2. Pre-checks — read-only, before any action

All four preconditions were verified before the command was proposed.

| # | Check | Evidence | Result |
|---|---|---|---|
| 1 | Coordinator present | `lsusb`: Bus 001 Device 008, `10c4:ea60` Silicon Labs CP210x; bound to `cp210x`, `/dev/ttyUSB0` present | **PASS** |
| 2 | Configured path resolves | Container `PathOnHost` = `/dev/serial/by-id/usb-ITead_Sonoff_Zigbee_3.0_USB_Dongle_Plus_<DEVICE_ID>-if00-port0`; symlink exists and resolves to **`/dev/ttyUSB0`**, the expected node | **PASS** |
| 3 | Nothing holding the device | `fuser /dev/ttyUSB0` → exit 1 (no process); `lsof` → no process rows; **no running container maps any device** (`HostConfig.Devices` enumerated across all 16 running containers) | **PASS** |
| 4 | Container state recorded | `exited`, `ExitCode 2`, `FinishedAt 2026-08-17T11:12:24.946Z`, `RestartCount 1`, policy `unless-stopped` | recorded |

Supporting conditions: **bus stable** — zero USB disconnect or enumeration events between
13:12:26 and the recovery, roughly 7 h 50 m quiet; **MQTT broker available** — `mosquitto` up.

**Limitation stated at the time and repeated here:** `fuser` / `lsof` ran unprivileged, so a
root-owned holder could in principle have been invisible. The container enumeration closes that
gap for practical purposes, since the only plausible holders are containers.

### Baseline captured before recovery

| Entity | State before |
|---|---|
| `switch.impresora_3d` | `unavailable`, `last_changed 2026-08-17T11:12:24.921966Z` |
| `cover.toldo` | `unavailable`, `last_changed 2026-08-17T11:12:24.921458Z` |

Both went unavailable at the exact instant of the crash.

---

## 3. The change

```bash
docker start zigbee2mqtt
```

Executed **2026-08-17 21:15:13 CEST**. This starts the **existing** container, re-resolving the
`--device` mapping at start — the step that failed at 13:12:25 when the device node returned
101 ms too late.

**Deliberately not used:** `docker compose up` in `03_services/zigbee-stack/`. That compose file
is a **Recovery Artifact, not a Deployment Source** (`PROJECT_RULES.md` → *Recovery Artifacts*),
it carries redacted device paths, and it could recreate the container.

**Not touched:** compose files, Docker restart policy, USB topology, Home Assistant configuration,
the voice-exposure ACL, and anything belonging to S-9 or I-5.

---

## 4. Validation — six checks, all PASS

### Check 1 — container running · **PASS**

```
Status=running  Running=true  StartedAt=2026-08-17T19:15:13.356680804Z  RestartCount=0
```

`FinishedAt` remains the old `2026-08-17T11:12:24.946Z` — no new exit. Container count returned
to **17/17**.

*Note:* a manual start resets `RestartCount` to 0. The pre-recovery value of `1` is preserved in
the companion record and in `ROADMAP.md`; no evidence was lost.

### Check 2 — normal startup · **PASS**

```
[2026-08-17 21:15:13] z2m: Logging to console, file (filename: log.log)
[2026-08-17 21:15:13] z2m: Starting Zigbee2MQTT version 2.9.1 (commit #85875aee…)
```

Clean banner; no `Refusing to start`, no configuration error, no early exit.

### Check 3 — coordinator connected · **PASS**

```
[2026-08-17 21:15:14] z2m: zigbee-herdsman started (resumed)
[2026-08-17 21:15:14] z2m: Coordinator firmware version: {"type":"ZStack3x0", revision 20210708…}
[2026-08-17 21:15:14] z2m: Currently 10 devices are joined.
```

**10 devices joined** matches the documented network size (measured at I-7, 2026-07-28). The
Zigbee network re-formed intact; no device was lost.

### Check 4 — MQTT connected · **PASS**

```
[2026-08-17 21:15:14] z2m: Connected to MQTT server
[2026-08-17 21:15:14] z2m:mqtt: MQTT publish: topic 'zigbee2mqtt/bridge/state', payload '{"state":"online"}'
```

The bridge moved from `offline` (published at 13:12:24) to `online`.

### Check 5 — Home Assistant entities recovered, no unintended actuation · **PASS**

| Entity | Before | After | `last_changed` |
|---|---|---|---|
| `switch.impresora_3d` | `unavailable` | **`off`** | `2026-08-17T19:15:14.246972Z` |
| `cover.toldo` | `unavailable` | `closed` | `2026-08-17T19:15:14.246666Z` |

**No unintended actuation.** The printer returned to **`off`** — its documented baseline. No
service was called, no state was commanded; the plug's own telemetry reported `state:"OFF"`,
`power:0`, `current:0` continuously before and after. Recovery restored *visibility*, not
*action*.

### Check 6 — no immediate repeat failure · **PASS**

Evidence collected at **21:25:27 CEST**, **614 s** after start (threshold 600 s):

| Signal | Observed |
|---|---|
| Container | still `running`, `RestartCount` still 0, `FinishedAt` unchanged |
| Failure markers **after** the restart | **0** (`Adapter disconnected` / `Stopping Zigbee2MQTT` / `code=2`) |
| Kernel USB events since 21:15 | **0** disconnects, 0 re-enumerations |
| Device telemetry | publishing continuously; latest at 21:25:22 |
| Containers running | 17 |

**Method note.** The raw marker count over the log tail was **2**, and both lines are timestamped
**13:12:24** — the original crash, still inside the `--tail` window. Scoped from the restart
banner forward, the post-restart failure count is **0**. The distinction was verified explicitly
rather than assumed.

---

## 5. Conclusion — stated precisely

**Recovery is successful.** All six validation checks pass on real evidence: the service is
running, the coordinator and MQTT are connected, all 10 Zigbee devices rejoined, both Home
Assistant entities recovered from `unavailable` to real states with no actuation, and nothing
failed again within the observation window.

**Three things this does not establish:**

1. **S-9 is not fixed.** The structural cause — a coordinator three hubs deep on a shared external
   hub, plus Docker resolving `--device` once at start and making exactly one restart attempt — is
   untouched. **S-9 remains Open**, and no part of it is designed, scoped or authorized here.
2. **No stability claim.** A 10-minute quiet window rules out a startup loop or an immediately
   recurring disconnect. It says nothing about tomorrow. The container ran **five days** before
   this failure and 2 h 22 m before the July one; the 2026-08-17 disconnect had **no trigger at
   all**, so the recurrence interval is unpredictable by construction.
3. **The notification gap is unchanged.** **M-1 / M-A remain Open.** This outage was again found
   by inspection, not by monitoring, and a fourth recurrence would be found the same way.

**Expected recurrence.** On the evidence of three occurrences in three weeks, another is likely.
The remedy is S-9, and it is a separate, gated decision.

---

## 6. Rollback

Not applicable in the usual sense — the change is a service start, and the pre-change state was
an outage. Should the container fail again, the correct response is **not** to restart it blindly:
capture the kernel and `dockerd` evidence first, exactly as §3 of the companion record does, so the
fourth occurrence adds to the S-9 case instead of being erased by a reflex restart.

---

## 7. Git gate

Documentation-only from here. **Not committed, not pushed** — both require explicit operator
approval immediately before the command (`PROJECT_RULES.md` → *Operator Git Approval*). Author as
`Diego <diego@diegoamaro.dev>`.

**STOP at git gate.**
