# Phase D — RTX Node Bridge (Forward-looking)

- **Assistant:** **AURORA** (Amarolab Personal AI
  Assistant).
- **Status:** D-1.1 skeleton. **Forward-looking
  reference only.** No RTX node exists at Phase D-1
  entry. This document captures the design rules that
  keep the D-1 implementation portable so that future
  RTX bring-up is configuration, not redesign.

---

## 1. Two-node model (from
   `01_architecture/amarolab_architecture.md`)

```
┌────────────────────────────┐     ┌──────────────────────────────┐
│ UM790 Pro                  │     │ Future: Windows + RTX tower  │
│ Permanent infrastructure   │     │ On-demand AI compute         │
│ Runs 24/7                  │     │ Wake-on-LAN                  │
│                            │     │                              │
│  • Home Assistant          │     │  • Large LLMs                │
│  • Open WebUI              │     │  • Large Whisper             │
│  • Ollama (small models)   │     │  • Vision models             │
│  • Qdrant                  │     │  • Experimental workloads    │
│  • Mosquitto / Z2M         │     │                              │
│  • aurora-whisper (CPU)    │     │                              │
│  • aurora-piper (CPU)      │     │                              │
│  • aurora-wakeword         │     │                              │
│  • Guardian Cloud          │     │                              │
└────────────────────────────┘     └──────────────────────────────┘
```

Architectural invariants:

1. **AURORA must keep working with the RTX node off.**
   The RTX is opportunistic.
2. **No always-on AURORA component runs on the RTX.**
   Wake-word, Piper, and a small CPU Whisper stay on
   UM790.
3. **No Guardian Cloud surface migrates to the RTX.**
   Production stays on UM790 per
   [`../../../06_security/security_posture.md`](../../../06_security/security_posture.md).

---

## 2. What the RTX node will host (Phase D-3+)

| Component | UM790 today | RTX tomorrow |
|---|---|---|
| Wake word (always-on) | UM790 | UM790 (no change) |
| Piper TTS (always-on) | UM790 | UM790 (no change) |
| Small Whisper (`base-int8`) | UM790 | UM790 — fallback when RTX asleep |
| Large Whisper (`large-v3-int8` or `large-v3`) | n/a | RTX (preferred when awake) |
| Large LLM (e.g., 70B-class) | n/a | RTX (Phase E+ scope) |
| Vision models | n/a | RTX (out of Phase D scope) |
| HA Assist | UM790 | UM790 (no change — HA never moves) |

---

## 3. Design rules adopted in Phase D-1 to enable D-3 migration

### 3.1 Address indirection

HA's Wyoming endpoint URLs reference **Docker network
aliases**, not IPs:

```
STT primary:   aurora-whisper:10300       (UM790 small)
STT fallback:  -- (D-1 single source)
```

When the RTX node is added:

```
STT primary:   aurora-whisper-rtx:10300   (Tailscale alias to RTX)
STT fallback:  aurora-whisper:10300       (UM790 small, always-on)
```

The HA pipeline configuration changes; nothing else.

### 3.2 Wyoming on TCP, not on a Unix socket

Wyoming over TCP is location-agnostic. UM790 and the
RTX node can host Wyoming endpoints interchangeably
because the transport does not assume same-host.

### 3.3 Model files are bind-mount-portable

`aurora-whisper` mounts `/srv/homelab/data/whisper/`.
When migrating to RTX, the same model directory
shape (or its GPU-optimised counterpart) lives at
the equivalent path on the RTX host. No HA-side
change.

### 3.4 No state in containers

All Wyoming containers are stateless: model files
on the bind mount, no per-container persisted state.
Re-creating on the RTX is a `docker run` with the
same env.

### 3.5 Wake-on-LAN trigger lives in HA

HA already runs the house; the WoL automation lives
in HA, not in AURORA's tooling. The trigger criteria
will be documented at D-3 design time. **Forbidden
trigger:** "wake on every utterance" — boot latency
makes UX worse.

Likely D-3 trigger (TBD):

- Time-of-day active window (e.g., 07:00–23:00) AND
- Workstation present on LAN (DHCP lease active) AND
- A "AURORA needs power" input_boolean toggled by
  the operator.

### 3.6 Sleep behaviour

When the RTX node sleeps:

- HA detects loss of Wyoming connectivity (heartbeat
  timeout).
- Pipeline failover to UM790's small Whisper happens
  automatically (HA Assist supports primary/fallback
  per integration).
- Piper and openWakeWord continue uninterrupted.

---

## 4. Security delta when RTX comes online

| Concern | Phase D-1 (UM790 only) | Phase D-3 (RTX added) |
|---|---|---|
| Audio in transit (HA → STT) | Docker network on UM790 | Tailscale tunnel UM790 ↔ RTX (LAN segment), TLS at the Tailscale layer |
| Model integrity | Bind-mount on local SSD | Bind-mount on RTX local SSD; checksums recorded per model file |
| Authentication HA ↔ RTX Wyoming | None (Docker net) | Tailscale identity; Wyoming itself stays unauthenticated within the tunnel |
| Operator access | SSH to UM790 | SSH to UM790 + SSH/RDP to RTX |
| Secrets | None new | Tailscale auth key per node, stored at `/home/diego/.secrets/` |

Phase D-3 will require a security delta document
(`06_security/rtx_node_security.md`) before bring-up.
**Not** a Phase D-1 deliverable.

---

## 5. What Phase D-1 must **not** do

To keep the D-3 migration cheap, Phase D-1 must not:

- Hard-code UM790 IPs in HA Assist configuration.
- Run Wyoming over a Unix domain socket.
- Make `aurora-whisper` stateful.
- Couple Piper to a Whisper instance.
- Couple openWakeWord to a Whisper instance.
- Introduce a single point of failure that depends on
  any future RTX state.

Each is a tested-against-now invariant. The
component-spec doc
([`03-component-spec.md`](03-component-spec.md))
already enforces these via TCP-only Wyoming, bind
mounts, and image pins.

---

## 6. Related documents

- [`../../../01_architecture/amarolab_architecture.md`](../../../01_architecture/amarolab_architecture.md) — Future Distributed Architecture
- [`02-target-architecture.md`](02-target-architecture.md) — current architecture
- [`03-component-spec.md`](03-component-spec.md) — component specs (must remain portable)
- [`../../../06_security/security_posture.md`](../../../06_security/security_posture.md) — production segregation
