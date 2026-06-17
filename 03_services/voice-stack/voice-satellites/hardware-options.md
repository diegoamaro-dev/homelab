# Voice Satellites — Hardware Options

- **Scope:** Hardware that lets AURORA (Amarolab
  Personal AI Assistant) be heard and respond to in a
  given room.
- **Status:** D-1.1 skeleton.

---

## 1. Phase D-1 — primary path (no new hardware)

| Item | Notes |
|---|---|
| Operator's workstation PC | Existing mic + speakers. Used via browser. **Sufficient for the entire Phase D-1 validation set (G-D1 through G-D6).** |
| HA UI in browser | Voice via the Assist panel — push-to-talk button. |
| Open WebUI in browser | Voice via the mic button — push-to-talk. |

This is the path on which Phase D-1 closes. No new
hardware is required to satisfy the ROADMAP success
criterion ("Voice interaction through the house") at
the level of one room and one operator.

---

## 2. Phase D-2 — future hardware options

D-2 introduces always-listening voice satellites for
rooms where the workstation is not present. **None of
these are Phase D-1 requirements.** They are
documented here so the architecture stays portable
and so the operator can plan procurement when ready.

### 2.1 Home Assistant Voice Preview Edition

| Field | Value |
|---|---|
| Maker | Home Assistant (official) |
| Price | ≈ €/$59 |
| Form factor | Pre-built unit with mic array + speaker + LED ring |
| Wake-word | Runs on-device (XMOS chip handles it) |
| HA integration | Auto-discovery; first-class support |
| Strengths | Lowest friction; documented; supported upgrade path |
| Weaknesses | Single voice; price point |

**Recommended D-2 starter satellite** for the room
where AURORA is primary.

### 2.2 M5Stack ATOM Echo

| Field | Value |
|---|---|
| Maker | M5Stack |
| Price | ≈ €/$15 |
| Form factor | Thumb-sized ESP32 with mic + small speaker |
| Wake-word | Streamed to UM790 `aurora-wakeword` |
| HA integration | Via `wyoming-satellite` firmware (community) |
| Strengths | Very cheap; easy to scatter across rooms |
| Weaknesses | Lower-quality mic and speaker; software flash required |

**Recommended D-2 expansion** for additional rooms
once the primary satellite proves out.

### 2.3 ESP32-S3-BOX-3

| Field | Value |
|---|---|
| Maker | Espressif |
| Price | ≈ €/$50 |
| Form factor | Compact box with touchscreen, mic, speaker |
| Wake-word | On-device (Espressif's wake engine) or streamed |
| HA integration | ESPHome voice assistant firmware |
| Strengths | Display for visual feedback; better mic than ATOM |
| Weaknesses | Software setup more involved |

**Alternative D-2 satellite** for high-traffic
locations (kitchen, living room) where a small
display improves UX.

### 2.4 Comparison

| Criterion | D-1 PC mic | HA Voice PE | M5 ATOM Echo | ESP32-S3-BOX-3 |
|---|---|---|---|---|
| Cost | Free (existing) | €59 | €15 | €50 |
| Wake-word on-device | n/a | Yes | No (streamed) | Yes (optional) |
| Always-listening | No | Yes | Yes | Yes |
| Mic quality | Operator-dependent | High | Medium | High |
| Speaker quality | Operator-dependent | Medium | Low | Medium |
| Visual feedback | Browser UI | LED ring | None | Display |
| Setup effort | None | Plug + add to HA | Flash + Wyoming satellite | ESPHome flash |

---

## 3. Decision criteria for moving to D-2

D-2 hardware bring-up should happen only when **all**
of the following hold:

- Phase D-1 closed (all six G-D gates documented).
- A specific room and use case justifies always-on
  voice (vs. always-near-the-workstation).
- The operator has time to set up flashing /
  firmware (M5 / ESP32) or budget for the HA Voice
  PE.

---

## 4. Privacy and security considerations

| Concern | Mitigation |
|---|---|
| Always-on mic in a room | Wake-word runs on satellite (when supported); only post-wake audio leaves the device. |
| Hardware key compromise | Each satellite has its own ESPHome API key, stored under `/home/diego/.secrets/`. |
| LAN-only traffic | Satellites speak to HA over LAN; no WAN exposure. |
| Firmware updates | Pinned firmware version recorded per device in the apply log when added. |

---

## 5. Phase D-1 ↔ D-2 transition

When a D-2 satellite is added:

1. Apply log records device, firmware version, MAC,
   ESPHome API key (in operator secrets, not repo),
   and HA discovery evidence.
2. HA Assist pipeline is reused — the satellite
   simply selects the existing "AURORA v1" pipeline.
3. Wake-word transitions from "deployed but not
   exercised" to "always-listening, validated per
   satellite."
4. `voice_privacy.md` (security delta doc) is updated
   with the new device and its mic always-on
   semantics.

---

## 6. Related documents

- [`../../../04_ai_system/amarolab-v1/phase-d/02-target-architecture.md`](../../../04_ai_system/amarolab-v1/phase-d/02-target-architecture.md) §5
- [`../wakeword/openwakeword-deployment.md`](../wakeword/openwakeword-deployment.md)
- [`../../../06_security/voice_privacy.md`](../../../06_security/voice_privacy.md)
