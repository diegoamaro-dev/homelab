# I-10 — Repeated host shutdowns without normal shutdown markers — finding, 2026-08-31

**Date:** 2026-08-31 — observed during the C-1 fourth-recurrence investigation; record written
2026-09-01, shortly after midnight CEST.
**Type:** Dated operational record. **Newly discovered operational finding, tracking only.**
Not a remediation item, not a phase, and nothing here is authorized for action.
**Production changed by this document:** **no.** Nothing was diagnosed, tested, swapped,
reconfigured or repaired. No host reboot was performed.
**Status:** **OPEN — investigation not started.**
**Identifier:** **I-10**, assigned as the next free Ledger identifier following the **I-9**
precedent (*"new tracking item I-9 (architecture-document drift)"*, raised 2026-07-28 as
tracking only). No numbering rule exists in `PROJECT_RULES.md`; this follows repository
precedent and is subject to operator ratification.

> Dated record. States what was true on 2026-08-31 / 2026-09-01 and is **not** rewritten as the
> situation advances (`PROJECT_RULES.md` → *Historical Documentation*).

**Why this is tracked separately.** It was discovered while investigating the fourth C-1
recurrence
([`2026-08-31_zigbee2mqtt_c1_fourth_recurrence.md`](2026-08-31_zigbee2mqtt_c1_fourth_recurrence.md)),
but it is **not** a Zigbee finding. Repeated shutdowns without a clean unmount can threaten
filesystem consistency, SQLite databases and service integrity across the whole platform —
Home Assistant's recorder, the Open WebUI database, Qdrant, and any in-flight write. Its blast
radius is wider than Zigbee and it needs its own record.

---

## 1. OBSERVED

### 1.1 Ten of the eleven retained boots ended without normal shutdown markers

Method: for each retained boot, count journal occurrences of `Powering Off`,
`systemd-shutdown` and `Reached target … Power-Off/Reboot`.

| Boot | Started (CEST) | Last journal entry (CEST) | Shutdown markers |
|---|---|---|---|
| −11 | 2026-07-02 23:24:17 | 2026-07-04 13:31:38 | **0** |
| −10 | 2026-07-04 16:23:16 | 2026-07-17 12:40:10 | **0** |
| −9 | 2026-07-17 12:47:05 | 2026-07-17 13:09:12 | **0** |
| −8 | 2026-07-17 14:26:59 | 2026-07-20 20:28:57 | **0** |
| −7 | 2026-07-20 20:29:18 | 2026-07-21 19:44:23 | **0** |
| −6 | 2026-07-21 19:44:48 | 2026-07-21 19:51:22 | **0** |
| **−5** | 2026-07-21 19:51:52 | 2026-07-21 19:52:29 | **3** |
| −4 | 2026-07-25 23:50:45 | 2026-07-28 13:28:48 | **0** |
| −3 | 2026-07-28 13:29:31 | 2026-08-12 09:24:12 | **0** |
| −2 | 2026-08-12 09:28:04 | 2026-08-21 17:52:08 | **0** |
| −1 | 2026-08-21 17:54:15 | **2026-08-31 23:37:42** | **0** |

The **four most recent** boots (−4, −3, −2, −1) all ended with zero markers.

### 1.2 Boot −5 is a control case, and it validates the method

Boot −5 ended with **3** shutdown markers. The same test, over the same journal, on the same
host, **does** detect an ordered shutdown when one occurs. The absence of markers elsewhere is
therefore **evidence**, not a limitation of the test.

### 1.3 The 2026-08-31 event in detail

| Item | Observed |
|---|---|
| Last journal entry, boot −1 | 2026-08-31 23:37:42, ordinary network-daemon activity, no anomaly preceding it |
| Shutdown markers | **0** |
| Next boot | 2026-08-31 23:38:28 |
| Gap | **46 seconds** |
| Kernel across the boundary | `7.0.0-29-generic` → `7.0.0-30-generic` |
| User sessions | recorded as `crash` rather than a normal logout |

### 1.4 Corroborated independently by Home Assistant

At 2026-08-31 23:38:47 CEST, on its first start after the boot, Home Assistant logged:

```
WARNING (Recorder) [homeassistant.components.recorder.util]
  The system could not validate that the sqlite3 database at
  //config/home-assistant_v2.db was shutdown cleanly
WARNING (Recorder) [homeassistant.components.recorder.util]
  Ended unfinished session (id=82 from 2026-08-21 15:54:42.863988)
```

The unfinished recorder session begins at the start of boot −1. This is a **second, independent
subsystem** reporting that the previous shutdown was not clean, and it corroborates the journal
evidence for the 2026-08-31 event specifically.

### 1.5 The pattern was observed once before, but never tracked

[`2026-08-17_operational_reconciliation.md`](2026-08-17_operational_reconciliation.md) §2
already recorded, of the 2026-08-12 boot, that the previous boot ended *"with no shutdown
sequence recorded"* and that this was *"consistent with an unclean power interruption"*, cause
not established. That observation was correct and is **not** superseded here.

**What is new is not the observation — it is that it has now happened repeatedly, and that it
is being given a tracking identifier for the first time.** The 2026-08-17 record noted a single
instance in passing while documenting something else; this record establishes that ten of
eleven retained boots share the property, and opens it as its own finding.

### 1.6 Intervals between the recent events

2026-07-25 → 2026-07-28 (≈ 2.6 d) · 2026-07-28 → 2026-08-12 (≈ 14.8 d) ·
2026-08-12 → 2026-08-21 (≈ 9.4 d) · 2026-08-21 → 2026-08-31 (≈ 10.2 d).

Recorded as measurements only. **No periodicity, cadence or trend is claimed.**

---

## 2. UNKNOWN

**The cause is unknown.** Nothing in this record identifies why the host stopped.

The following are **explicitly not claimed**, and may not be inferred from this record:

- **no** power-supply fault;
- **no** thermal event;
- **no** BIOS, firmware or microcode fault;
- **no** mains-power interruption;
- **no** hardware failure of any kind;
- **no** software, kernel or driver fault;
- **no** distinction established between an unexpected power loss, a spontaneous reset, a
  watchdog action and an ordered reboot whose journal was not flushed.

No diagnosis has been performed. No hypothesis has been tested. No component has been
inspected, swapped or instrumented.

**No causal link to C-1 is asserted.** The fourth C-1 recurrence occurred on 2026-08-22 and
this host event occurred on 2026-08-31, nine days apart. The 2026-08-31 event *incidentally
restored* Zigbee2MQTT, which is a consequence, not a cause, and the earlier C-1 occurrences are
not attributed to host shutdowns. The two findings are tracked separately and independently.

---

## 3. Method and limits

**Sources.** The systemd journal per boot (`journalctl --list-boots`, `journalctl -b <n>`),
`last -x`, and the Home Assistant container log.

**Limits, stated so the evidence is not over-read:**

1. **Marker absence is not proof of an unclean stop.** An ordered shutdown whose final journal
   entries were never flushed would present identically. Boot −5 shows flushing *can* work on
   this host, which weakens but does not eliminate this alternative.
2. **Only the eleven retained boots were assessed.** Earlier boots are outside journal
   retention and say nothing either way.
3. **The 2026-08-31 event has independent corroboration (§1.4); the earlier ten do not.**
   Their classification rests on the marker test alone.
4. **No hardware-level telemetry was collected** — no thermal history, no power-event log, no
   firmware log was read. Such sources may or may not exist on this platform; that was not
   established.

---

## 4. Status and what happens next

**OPEN. Tracking only.** No investigation is scheduled, scoped or authorized by this record.
No remediation is designed. This document exists so the pattern is preserved rather than
rediscovered, per `PROJECT_RULES.md` → *Documentation Rules* (*if it is not documented, it does
not exist*).

A future investigation, when authorized, would need to start by distinguishing the alternatives
listed in §2 — which this record deliberately leaves open.

---

## 5. Git gate

Documentation only. **Not committed, not pushed** — both require explicit operator approval
immediately before the command (`PROJECT_RULES.md` → *Operator Git Approval*). Author as
`Diego <diego@diegoamaro.dev>`.

**STOP at git gate.**
