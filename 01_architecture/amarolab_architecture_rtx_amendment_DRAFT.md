# AMAROLAB Architecture — RTX Node Amendment (DRAFT)

- **Status:** **DRAFT — not yet merged.** Proposed amendment to
  [`amarolab_architecture.md`](amarolab_architecture.md), to be merged into
  that document at **RTX-1 closeout**.
- **Date drafted:** 2026-06-18
- **Reason:** The "Future Distributed Architecture / AI Compute Node"
  section of the live architecture doc describes the RTX tower as *planned*.
  As of 2026-06-18 the node physically exists, runs Ollama on the GPU, and
  has been validated locally (see
  [`../09_logs/2026-06-18_phaseRTX1_local_validation.md`](../09_logs/2026-06-18_phaseRTX1_local_validation.md)).
  This draft promotes it from "planned" to "provisioned (local-only)".
- **Boundary note:** This is a documentation draft only. It records what was
  built on **Torre**. It does **not** move any production service. The UM790
  remains the 24/7 infrastructure node. Guardian Cloud is untouched.

> Merge guidance: when applied, this replaces the **"Future Distributed
> Architecture → AI Compute Node"** subsection of
> [`amarolab_architecture.md`](amarolab_architecture.md) and adds Torre to
> the hardware inventory. The "Permanent Node = UM790" subsection is
> unchanged.

---

## 1. Two-node model — current status

```text
┌────────────────────────────┐        ┌──────────────────────────────┐
│ UM790 Pro  (homelab)       │        │ Torre  (Windows + RTX)       │
│ PERMANENT — runs 24/7      │        │ ON-DEMAND GPU compute        │
│ Tailscale 100.68.180.69    │        │ Tailscale 100.91.154.124     │
│ LAN 192.168.178.79         │        │ LAN 192.168.178.21           │
│                            │        │                              │
│  • Home Assistant          │        │  • Ollama (GPU) ◀ NEW        │
│  • Open WebUI             │        │      qwen2.5:7b-instruct      │
│  • Ollama (CPU, small)     │        │      105 tok/s on RTX 5070    │
│  • Qdrant                  │        │  • (future) large Whisper     │
│  • Mosquitto / Z2M         │        │  • (future) large LLMs        │
│  • aurora-whisper (CPU)    │        │  • (future) vision models     │
│  • aurora-piper (CPU)      │        │                              │
│  • aurora-wakeword         │        │  NOT hosted here:             │
│  • Guardian Cloud          │        │   HA, Open WebUI, Qdrant,     │
│  • Cloudflared / Restic    │        │   Mosquitto, Z2M, Cloudflare, │
│                            │        │   Guardian Cloud, backups     │
└────────────────────────────┘        └──────────────────────────────┘
        always available                  opportunistic / GPU only
```

Invariants carried from
[`../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md`](../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md)
and re-affirmed by this amendment:

1. **AURORA keeps working with Torre off.** The RTX node is opportunistic;
   the UM790 CPU path remains the always-on fallback.
2. **No always-on AURORA component runs on Torre.** Wake-word, Piper, and
   the small CPU Whisper stay on the UM790.
3. **No Guardian Cloud surface runs on Torre.** Production stays on the
   UM790 per [`../06_security/security_posture.md`](../06_security/security_posture.md).
4. **Torre is GPU compute only.** Its role is large/fast model serving on
   demand — nothing that must be highly available.

---

## 2. Hardware inventory addition

Proposed new entry under **# Hardware**:

### AI Compute Node (provisioned 2026-06-18, local-only)

| Component | Specification |
|---|---|
| Name | Torre |
| Model | Custom Windows tower |
| OS | Windows 11 Pro (build 26100) |
| CPU | Intel Core i5-10600K (6c / 12t) |
| RAM | 32 GB |
| GPU | NVIDIA GeForce RTX 5070, 12 GB VRAM |
| NVIDIA driver | 610.62 (CUDA UMD 13.3) |
| Model store | `D:\ai\ollama\models` (WD Black SN850X 8 TB NVMe, ~6.9 TB free) |
| LAN | 192.168.178.21 (1 Gbps) |
| Tailscale | 100.91.154.124 (node `torre`) |
| Runtime | Ollama 0.30.10 (GPU) |
| Availability | On-demand (not 24/7) |

---

## 3. AI compute path (current vs. with Torre)

```text
TODAY (Phase D-1 closed — all inference on UM790 CPU):

  Open WebUI ─┐
              ├─▶ Ollama (UM790 CPU) ─▶ qwen2.5:7b-instruct  (~6 tok/s)
  HA Assist ──┘

WITH TORRE (target after RTX-1.4 remote exposure + endpoint swap):

  Open WebUI ─┐                       ┌─▶ Ollama (Torre RTX) ─▶ qwen2.5  (~105 tok/s)   [preferred when awake]
              ├─▶ ollama endpoint ────┤
  HA Assist ──┘    (Tailscale)        └─▶ Ollama (UM790 CPU) ─▶ qwen2.5  (~6 tok/s)     [always-on fallback]
```

Only the **`ollama` endpoint target** changes on the UM790 side. No
voice-stack container is moved. The endpoint swap is a **separate, gated
step** (post RTX-1.4) and is **not** part of the local validation.

---

## 4. Interconnection (updated)

The live architecture doc shows Wake-on-LAN → RTX node. This amendment
records the transport actually provisioned:

```text
UM790  ──Tailscale mesh (direct path, same LAN segment)──▶  Torre
            100.68.180.69            100.91.154.124
```

- **Transport:** Tailscale (WireGuard) between `homelab` and `torre`. A
  direct path is already established on the shared `192.168.178.0/24`
  segment.
- **Wake-on-LAN:** still the intended power-management trigger, owned by
  Home Assistant (per node-bridge §3.5). WoL design is deferred; it is not
  required for the local validation and not configured.
- **Access control (target, RTX-1.4):** Ollama on Torre will be reachable
  **only** from the Tailscale range `100.64.0.0/10`, enforced by a Windows
  Firewall inbound rule. LAN-direct access to `192.168.178.21:11434` will be
  blocked. **As of this draft, Ollama binds loopback only and is not yet
  remote-reachable.**

---

## 5. What is NOT changing in the live architecture

- **Permanent Node = UM790** subsection — unchanged. The UM790 still hosts
  Home Assistant, Open WebUI, Qdrant, Guardian Cloud, backups, automation
  and infrastructure services, 24/7.
- **MQTT / Home Automation / Storage / Backup / Security** architecture
  sections — unchanged.
- **Architecture Principles** — unchanged and reinforced: "Production stays
  on UM790; AI compute can move to dedicated hardware."

---

## 6. Open items before this draft is merged

| Item | Gate |
|---|---|
| Remote exposure (OLLAMA_HOST + firewall + Machine-scope env) | RTX-1.4 |
| Headless persistence (Windows service) | RTX-1.5 |
| Security delta doc `06_security/rtx_node_security.md` | before endpoint swap |
| UM790 `ollama` endpoint swap to Torre (primary + UM790 fallback) | separate gated step |

Until RTX-1.4 lands, the live architecture doc should keep the AI compute
node described as **"provisioned, local-only — not yet consumed by the
UM790."**

---

## 7. Related documents

- [`amarolab_architecture.md`](amarolab_architecture.md) — live architecture (merge target).
- [`remote-access-tailscale.md`](remote-access-tailscale.md) — Tailscale posture.
- [`../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md`](../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md) — node design rules / invariants.
- [`../09_logs/2026-06-18_phaseRTX1_local_validation.md`](../09_logs/2026-06-18_phaseRTX1_local_validation.md) — local validation evidence.
- [`../06_security/security_posture.md`](../06_security/security_posture.md) — production segregation.
