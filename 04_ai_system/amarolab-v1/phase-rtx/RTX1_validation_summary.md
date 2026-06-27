# Phase RTX-1 — Validation Summary

- **Assistant:** **AURORA** — Personal AI Assistant for the AMAROLAB ecosystem.
- **Node:** **Torre** — Windows + RTX workstation (AI compute node).
- **Date:** 2026-06-18
- **Status:** **RTX-1.5 complete (2026-06-27) — headless NSSM service; persistence across logoff + reboot-without-login proven, GPU offload restored at cold boot, network posture preserved (host-scoped /32 allowlist). RTX-1.4 complete (2026-06-19). UM790 endpoint swap (RTX-1.6) pending.**
- **One-line:** `qwen2.5:7b-instruct` runs on Torre's RTX 5070 at
  **105.3 tok/s** from `D:\ai\ollama\models` — **17.6×** the UM790 CPU
  baseline — but is **not yet reachable by the UM790**.

This is the phase-level rollup. Full evidence and reproducibility live in the
apply log:
[`../../../09_logs/2026-06-18_phaseRTX1_local_validation.md`](../../../09_logs/2026-06-18_phaseRTX1_local_validation.md).

---

## 1. Goal of Phase RTX-1

Turn Torre into the on-demand GPU compute node anticipated by
[`../phase-d/06-rtx-node-bridge.md`](../phase-d/06-rtx-node-bridge.md):
GPU-accelerated local LLM serving that the UM790 can later consume over
Tailscale, **without moving any production service off the UM790**.

Hard boundaries (all honoured): UM790 stays the 24/7 node; no migration of
Home Assistant, Open WebUI, Qdrant, Guardian Cloud, Mosquitto,
Zigbee2MQTT, Cloudflare or backups; Torre is GPU compute only; no UM790,
Guardian Cloud, or infrastructure changes.

---

## 2. Sub-step ledger

| Step | Description | Status |
|---|---|---|
| RTX-1.0 | Read-only post-format workstation audit | **Done** |
| RTX-1.1 | Install Ollama; pre-stage `D:\ai\ollama\models` | **Done** |
| RTX-1.2 | GPU validation (pull, placement, VRAM, benchmark) | **Done** |
| RTX-1.3 | Storage remediation (model store C: → D:) | **Done** |
| RTX-1.4 | Secure remote exposure (OLLAMA_HOST + firewall, Tailscale-only) | **Completed (2026-06-19)** — [log](../../../09_logs/2026-06-19_phaseRTX1_4_remote_exposure.md) |
| RTX-1.5 | Headless persistence (Windows service) | **Complete (2026-06-27)** — [log](../../../09_logs/2026-06-19_phaseRTX1_5_headless_service.md) · [closeout](../../../09_logs/2026-06-27_rtx1_5_continuation_handoff.md) |
| RTX-1.6 | Security delta doc + UM790 endpoint swap | Not started |

> Numbering note: this session used **RTX-1.x**; the forward-looking
> node-bridge doc framed the same work as **Phase D-3+**. They refer to the
> same node. RTX-1 is the concrete bring-up of that anticipated node.

---

## 3. What was validated

### 3.1 Hardware
RTX 5070 (12 GB VRAM), i5-10600K (6c/12t), 32 GB RAM, Windows 11 Pro,
NVIDIA driver 610.62 / CUDA UMD 13.3. Tailscale up (`torre`,
100.91.154.124); UM790 (`homelab`, 100.68.180.69) reachable on a direct
path.

### 3.2 Ollama install
Ollama 0.30.10 → `C:\Users\diego\AppData\Local\Programs\Ollama\`. No other
software installed (no Python, Docker, WSL, OpenSSH).

### 3.3 Model storage on D:
`qwen2.5:7b-instruct` (ID `845dbda0ea48`, 4.7 GB) stored at
`D:\ai\ollama\models` (5 blobs, 4.36 GB + manifests). C: model directory
empty. Server startup log confirms `OLLAMA_MODELS:D:\ai\ollama\models` and
loads the blob from D:.

> A first pull mistakenly landed on C: because the installer-launched server
> did not inherit `OLLAMA_MODELS`. Corrected by moving the store and
> restarting with the variable in the server environment. → Lesson L-RTX-1.

### 3.4 GPU placement
`ollama ps` → **100% GPU**; load log → **29/29 layers offloaded**; compute
process `llama-server.exe` (nvidia-smi type **C**); VRAM idle 1,702 MiB →
resident **6,474 MiB**.

### 3.5 Benchmark
| Node | Hardware | tok/s |
|---|---|---|
| UM790 (`homelab`) | Ryzen 9 7940HS — CPU | ~6 |
| **Torre** | RTX 5070 — GPU | **105.3** |
| | | **≈ 17.6×** |

3-pass: 105.5 / 105.5 / 104.9 tok/s (256 tok, temp 0, model on D:).

---

## 4. Key finding — VRAM contention (L-RTX-2)

Desktop/browser GUI apps consumed ~10.7 GB of the 12 GB VRAM mid-session,
leaving ~1.2 GB free. The 7B model then offloaded only 2/29 layers and
`llama-server` crashed in a CUDA flash-attention kernel (`0xc0000409`). With
VRAM free (~11 GB), the same model ran 29/29 layers at 105 tok/s.

**Implication for the node role:** as a dedicated compute node, Torre must
run **lean / headless** so the GPU reliably has the ~6 GB the model needs.
This reinforces RTX-1.5 (headless Windows service) and an operational rule
to avoid running VRAM-heavy GUI apps while serving.

---

## 5. Current state & blockers to remote consumption

| Aspect | State |
|---|---|
| Ollama runtime | RTX 5070, 105 tok/s, model on D: — **working locally** |
| Bind address | `0.0.0.0:11434` — Tailscale-reachable; **LAN firewall-blocked** |
| `OLLAMA_MODELS` | Machine + User scope = `D:\ai\ollama\models` |
| `OLLAMA_HOST` | `0.0.0.0:11434` (Machine scope) |
| Firewall | 2 scoped inbound rules — allow `100.68.180.69/32`; block `192.168.178.0/24` |
| Persistence | **NSSM service (LocalSystem, Automatic)** — survives logoff + reboot-without-login (RTX-1.5, 2026-06-27) |

Blockers before the UM790 can consume Torre (all addressed by RTX-1.4 /
RTX-1.5):

1. ~~Loopback-only bind~~ → **RESOLVED 2026-06-19** (`OLLAMA_HOST=0.0.0.0:11434`, Machine scope).
2. ~~No firewall rule~~ → **RESOLVED 2026-06-19** (allow `100.68.180.69/32`; block LAN).
3. ~~`OLLAMA_MODELS` User scope only~~ → **RESOLVED 2026-06-19** (Machine scope set).
4. No headless service → won't survive logoff/reboot. *(1.5)*
5. VRAM-headroom discipline → run lean/headless. *(operational)*

---

## 6. RTX-1.4 — completed 2026-06-19

RTX-1.4 is complete — see [the apply log](../../../09_logs/2026-06-19_phaseRTX1_4_remote_exposure.md).
The steps below are retained as the record of what was executed.

Secure remote exposure, Tailscale-only:

1. `OLLAMA_MODELS` + `OLLAMA_HOST=0.0.0.0:11434` at **Machine** scope (elevated).
2. Windows Firewall inbound rule `Ollama-Tailscale-Only` — TCP 11434,
   remote `100.64.0.0/10`, all profiles; remove any allow-all Ollama rule.
3. Restart Ollama; verify locally (version, bind, D: path, GPU load).
4. Verify from UM790 over Tailscale (`/api/version`, `/api/generate`); confirm
   LAN-direct path to `192.168.178.21:11434` is blocked.

A security delta doc (`06_security/rtx_node_security.md`) is required before
the UM790 endpoint actually points at Torre (node-bridge §4). The UM790
`ollama` endpoint swap (Torre primary + UM790 fallback) is a separate gated
step, not part of RTX-1.

---

## 6.5 RTX-1.5 — headless persistence (completed 2026-06-27)

Ollama on Torre migrated from the interactive tray app to a **headless NSSM Windows service** (`OllamaService`, LocalSystem, Automatic). All gates PASS — full record in [the phase log](../../../09_logs/2026-06-19_phaseRTX1_5_headless_service.md) and [the closeout handoff](../../../09_logs/2026-06-27_rtx1_5_continuation_handoff.md).

| Gate | Result |
|---|---|
| G-1.5-1/2/3/4 | Service Running/Automatic; env vars; single listener `0.0.0.0:11434`; GPU 29/29, size_vram==size, ~111 tok/s |
| G-1.5-8 (critical) | Teardown/VRAM: stop/restart/crash → no orphan, VRAM recovered (NSSM 2.24 **default** tree-kill) |
| G-1.5-7 | Firewall re-check: host-scoped /32 allowlist (allow `100.68.180.69/32`, block LAN); UM790 reachable, LAN blocked |
| G-1.5-5 | Logoff: serves while signed out; PID continuity (no silent restart) |
| **G-1.5-6** | **Reboot without login (core): serves over Tailscale before any login; GPU offload restored at cold boot** |
| G-1.5-9 | Restart throttle: NSSM back-off `0→2000→4000 ms` (event 1034); clean recovery |
| G-1.5-10 | Production integrity: UM790 endpoint unchanged (`http://ollama:11434`, local v0.17.7); Torre IP absent from all containers; stack untouched |

**Reality reconciliations:** NSSM restart params are defaults (`AppRestartDelay=0`, `AppThrottle=1500`) — the documented `10000/10000` were never applied; no `AppKillProcessTree=1` (tree-kill is the NSSM 2.24 default); NSSM 2.24 has no `dump` (used `nssm get`); firewall is a host-scoped /32 allowlist (not CGNAT-wide). Local UM790 ollama (v0.17.7, CPU) is distinct from Torre (0.30.10, GPU); endpoint **not** swapped.

**Deferred to RTX-1.6:** `security_posture.md` + the architecture amendment, and the UM790 `ollama` endpoint swap. Security delta lands in its own `06_security/rtx_node_security.md`.

---

## 7. Related documents

- [`../../../09_logs/2026-06-18_phaseRTX1_local_validation.md`](../../../09_logs/2026-06-18_phaseRTX1_local_validation.md) — apply log / full evidence.
- [`../../../01_architecture/amarolab_architecture_rtx_amendment_DRAFT.md`](../../../01_architecture/amarolab_architecture_rtx_amendment_DRAFT.md) — architecture amendment draft.
- [`../phase-d/06-rtx-node-bridge.md`](../phase-d/06-rtx-node-bridge.md) — node design rules / invariants.
- [`../../../01_architecture/remote-access-tailscale.md`](../../../01_architecture/remote-access-tailscale.md) — Tailscale posture.
- [`../../../00_overview/CURRENT_STATE.md`](../../../00_overview/CURRENT_STATE.md) — overview triad (amend at RTX-1 closeout).
