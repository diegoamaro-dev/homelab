# Phase RTX-1 — Local GPU node validation — APPLIED

- **Date:** 2026-06-18
- **Phase step:** RTX-1.1 (Ollama install) + GPU validation + storage remediation (local-only).
- **Ecosystem:** **AMAROLAB** — Personal Innovation Lab and Digital
  Infrastructure Ecosystem.
- **Assistant:** **AURORA** — Personal AI Assistant for the AMAROLAB ecosystem.
- **Independent project on AMAROLAB infrastructure:** **Guardian Cloud** —
  not present on this node and not modified by this work.
- **Node:** **Torre** — Windows + RTX workstation. The "Future: Windows + RTX
  tower / on-demand AI compute" node anticipated in
  [`../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md`](../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md).
- **Status:** **APPLIED (local-only).** Ollama installed on Torre, GPU
  inference of `qwen2.5:7b-instruct` validated on the RTX 5070 at
  **105.3 tok/s** (≈ **17.6×** the UM790 CPU baseline of ~6 tok/s), model
  store relocated to `D:\ai\ollama\models` and verified. The node is **not
  yet reachable by the UM790** — Ollama still binds loopback only, no
  firewall rule, no persistence. Remote exposure is **RTX-1.4** (planned,
  not executed).
- **Scope:** Torre only. **No UM790 change. No Guardian Cloud change. No
  infrastructure change.** No Python, no OpenSSH, no firewall modification,
  no network reconfiguration. Boundaries from the session brief honoured in
  full (§7).

---

## 1. Hardware detected (post-format read-only audit)

| Component | Value |
|---|---|
| Hostname | `Torre` |
| OS | Windows 11 Pro, build `26100` |
| CPU | Intel Core i5-10600K @ 4.10 GHz — 6 cores / 12 threads |
| RAM | 32 GB (`34,277,302,272` bytes) |
| GPU | NVIDIA GeForce RTX 5070 |
| VRAM | 12,227 MiB (~12 GB) |
| GPU power cap | 250 W |
| NVIDIA driver | `610.62` (KMD `610.62`, CUDA UMD `13.3`) |
| CUDA Toolkit (`nvcc`) | not installed (not required for Ollama) |
| LAN | Ethernet `192.168.178.21` (1 Gbps) |
| Tailscale | up — `100.91.154.124`, node `torre` |

Storage detected:

| Drive | Device | Size | Free |
|---|---|---|---|
| C: | WD Black SN850X 8 TB (partition) | 3.7 TB | 3,159 GB |
| D: | WD Black SN850X 8 TB (partition) | 7.5 TB | 6,898 GB |
| E: | Samsung SSD 840 EVO 250 GB | 233 GB | 228 GB |
| P: | XPG SPECTRIX S40G 4 TB | 1.9 TB | 1,858 GB |

`D:\projects` present and populated (`Ensambla2`, `guardian-cloud`,
`MyFreeTour`, others) — pre-existing, untouched by this work.

Tailscale mesh confirms the UM790 (`homelab`, `100.68.180.69`) reachable on
a **direct** path (`192.168.178.79`), same LAN segment as Torre.

Software baseline at audit time: Git `2.54.0`, VS Code `1.125.0` present;
**Python, Ollama, Docker, WSL, OpenSSH server — all absent** before this
work. Only Ollama was installed.

---

## 2. Ollama installation (RTX-1.1)

| Field | Value |
|---|---|
| Installer | `OllamaSetup.exe` (~1.33 GB) from `https://ollama.com/download/OllamaSetup.exe` |
| Install mode | `/SILENT` |
| Install path | `C:\Users\diego\AppData\Local\Programs\Ollama\` |
| Ollama version | `0.30.10` (`/api/version`) |
| Server binary | `…\Programs\Ollama\ollama.exe` |
| Inference engine | `…\Programs\Ollama\lib\ollama\llama-server.exe` |
| Tray app | `…\Programs\Ollama\ollama app.exe` |

Pre-first-run configuration:

- Created `D:\ai\ollama\models`.
- Set `OLLAMA_MODELS = D:\ai\ollama\models` at **User** scope (`setx`).
  Machine scope was **not** writable from the unprivileged session and is
  deferred to RTX-1.4 (needs an elevated shell).

---

## 3. Model storage migration to D:

### 3.1 Symptom

The first `ollama pull qwen2.5:7b-instruct` wrote the blob to **C:**
(`C:\Users\diego\.ollama\models\blobs`, 4,466 MB) despite the User-scope
`OLLAMA_MODELS=D:` being set.

### 3.2 Root cause

The **running Ollama tray server** was launched by the installer process,
whose environment block did not carry `OLLAMA_MODELS`. Ollama fixes its
model path at **server-process launch**; it does not re-read the registry
afterward. This is the same class of failure as
[Lesson 001](../07_operations/lessons_learned.md) (a process freezes its
environment at launch). See §6, L-RTX-1.

### 3.3 Remediation (executed)

1. Stopped all Ollama processes (`ollama app`, `ollama`, `llama-server`);
   confirmed port 11434 released.
2. `Move-Item` of `blobs` + `manifests` from
   `C:\Users\diego\.ollama\models` → `D:\ai\ollama\models`.
3. Restarted the server with `OLLAMA_MODELS=D:\ai\ollama\models` present in
   the launching shell's environment.

### 3.4 Verification

| Check | Result |
|---|---|
| Server's active `OLLAMA_MODELS` (startup log) | `D:\ai\ollama\models` |
| Models discovered from D: at startup | `models=1` |
| `ollama list` | `qwen2.5:7b-instruct  845dbda0ea48  4.7 GB` |
| Blob path in load log | `model=D:\ai\ollama\models\blobs\sha256-2bada8a7450677…` |
| D: blob store | 5 files, 4.36 GB in `D:\ai\ollama\models\blobs` |
| Manifests on D: | present under `D:\ai\ollama\models\manifests` |
| C: model directory | **empty — 0 files** |

Model identity anchor: `qwen2.5:7b-instruct`, ID `845dbda0ea48`, primary
blob `sha256-2bada8a7450677000f678be90653b85d364de7db25eb5ea54136ada5f3933730`.

---

## 4. GPU validation results

Captured with the model resident in VRAM after a clean restart reading from
D::

| Check | Result |
|---|---|
| `ollama ps` PROCESSOR | **`100% GPU`** |
| Layer offload (load log) | **`offloaded 29/29 layers to GPU`** |
| Device (load log) | `using device CUDA0 (NVIDIA GeForce RTX 5070) (0000:01:00.0)` |
| GPU compute process | `llama-server.exe`, nvidia-smi type **`C`** (compute) |
| VRAM idle (no model) | 1,702 MiB |
| VRAM model resident | **6,474 MiB** / 12,227 MiB (model buffer 4,168 MiB + KV 224 MiB + compute 136 MiB) |
| VRAM free with model up | 5,470 MiB |

The placement evidence (100% GPU, 29/29 layers, a CUDA-compute
`llama-server.exe`, ~6.5 GB VRAM resident) independently rules out a CPU
fallback. See §6, L-RTX-3.

---

## 5. Benchmark results

Standardised prompt, `num_predict=256`, `temperature=0`, warm model,
3 passes (clean re-validation, model on D:):

| Run | Tokens | Time | tok/s |
|---|---|---|---|
| 1 | 256 | 2.43 s | 105.5 |
| 2 | 256 | 2.43 s | 105.5 |
| 3 | 256 | 2.44 s | 104.9 |
| **Average** | | | **105.3** |

A corroborating earlier 3-pass run (same prompt, model still on C: before
the move) averaged **94.9 tok/s**; the clean post-move run is faster
because VRAM was uncontended (see §6, L-RTX-2).

### 5.1 Comparison against the UM790 baseline

| Node | Hardware | `qwen2.5:7b-instruct` |
|---|---|---|
| UM790 (`homelab`) | Ryzen 9 7940HS — CPU | ~6 tok/s |
| **Torre** (this node) | RTX 5070 — GPU | **105.3 tok/s** |
| | | **≈ 17.6× faster** |

This is the performance ceiling that
[`../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md`](../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md)
and the Phase D-1 closeout deferred to the RTX node. The voice-stack
architecture is already GPU-ready: once RTX-1.4 exposes this endpoint over
Tailscale, only the `ollama` endpoint target on the UM790 side changes.

---

## 6. Lessons learned

Proposed for merge into
[`../07_operations/lessons_learned.md`](../07_operations/lessons_learned.md)
at RTX-1 closeout (not merged by this log).

| ID | Lesson |
|---|---|
| **L-RTX-1** | **Ollama freezes `OLLAMA_MODELS` at server launch.** Setting the variable after the server is running does nothing; the model store only follows the variable if the server is (re)started with it in its process environment. Mirrors Lesson 001 (Docker env freeze). |
| **L-RTX-2** | **GPU VRAM is a contended resource on a workstation.** Desktop / browser GUI apps (Chrome, Edge, Electron apps) consumed ~10.7 GB of the 12 GB VRAM mid-session, leaving ~1.2 GB free. The 7B model then offloaded only 2/29 layers and `llama-server` crashed in a CUDA flash-attention kernel (`0xc0000409`). With VRAM free (~11 GB) the identical model ran 29/29 layers at 105 tok/s. **A dedicated compute node must run lean / headless.** |
| **L-RTX-3** | **Validate GPU placement, not "it generated."** A CPU fallback still produces correct text at ~6 tok/s and would silently mask a broken GPU path. Proof requires the conjunction of `ollama ps = 100% GPU`, nvidia-smi VRAM delta, the 29/29 layer-offload line, and tok/s. Mirrors Lessons 002 / 013. |
| **L-RTX-4** | **Trust one authoritative query over interleaved console output.** PowerShell `Write-Host` (unbuffered) and formatted object output (buffered) can render out of order; this initially produced a wrong read that the model was on D: when it was on C:. Reality wins — verify with a single explicit query (Lesson 003). |
| **L-RTX-5** | **A foreground `ollama serve` launched from automation is not a service.** It can hit CUDA-init failures detached from the interactive desktop session and does not survive logoff/reboot. Headless persistence requires a Windows service (RTX-1.5); the interactive tray app is the working manual path. |

---

## 7. What this work did NOT do (boundary compliance)

- **No UM790 change** — `homelab` was only read over Tailscale (mesh status);
  nothing was written, restarted, or reconfigured on it.
- **No Guardian Cloud change** — not present on Torre; untouched.
- **No infrastructure change** — Home Assistant, Open WebUI, Qdrant,
  Mosquitto, Zigbee2MQTT, Cloudflare, backups all untouched (they do not run
  on Torre and were not contacted).
- **No Python install.**
- **No OpenSSH server install.**
- **No firewall modification** — no rule created, deleted, or edited.
- **No network reconfiguration** — `OLLAMA_HOST` untouched; Ollama still
  binds `127.0.0.1:11434` (loopback only). Tailscale state unchanged.
- No secret introduced, printed, or committed. Tailscale `100.x` addresses
  are internal mesh addresses, not secrets.

---

## 8. State at stop point

| Item | State |
|---|---|
| Ollama | installed, `0.30.10`, operational on RTX 5070 |
| Model | `qwen2.5:7b-instruct` on `D:\ai\ollama\models`, GPU-validated |
| Bind address | `127.0.0.1:11434` — **loopback only** (not yet remote-reachable) |
| `OLLAMA_MODELS` | User scope = `D:\ai\ollama\models`; **Machine scope unset** |
| `OLLAMA_HOST` | unset (default loopback) |
| Firewall | unchanged — no Ollama rule |
| Persistence | none — manual start only |

### 8.1 Blockers before the UM790 can consume this node remotely

1. Ollama binds loopback only → must bind the Tailscale interface
   (`OLLAMA_HOST`). *(RTX-1.4)*
2. No firewall rule scoping 11434 to the Tailscale range
   `100.64.0.0/10`. *(RTX-1.4)*
3. `OLLAMA_MODELS` is User scope only → a service under another account
   would fall back to C:; needs Machine scope. *(RTX-1.4, elevated)*
4. No persistent/headless service → does not survive logoff/reboot.
   *(RTX-1.5)*
5. VRAM-headroom discipline → node should run lean/headless so the model
   reliably gets its ~6 GB (L-RTX-2). *(operational)*

---

## 9. Next step (planned, not executed)

**RTX-1.4 — Secure remote exposure (Tailscale-only).** Set `OLLAMA_HOST`
and `OLLAMA_MODELS` at Machine scope, create the `Ollama-Tailscale-Only`
inbound firewall rule (`TCP 11434`, remote `100.64.0.0/10`, all profiles),
remove any allow-all Ollama rule, restart, and verify from the UM790 over
Tailscale plus a LAN-blocked differential test. Full runbook with rollback
prepared separately. **RTX-1.5** then runs Ollama as a headless Windows
service. Security delta doc `06_security/rtx_node_security.md` is required
before the UM790 actually points at this endpoint (per the node-bridge
doc §4).

---

## 10. Related documents

- [`../04_ai_system/amarolab-v1/phase-rtx/RTX1_validation_summary.md`](../04_ai_system/amarolab-v1/phase-rtx/RTX1_validation_summary.md)
  — RTX-1 validation summary (phase-level rollup).
- [`../01_architecture/amarolab_architecture_rtx_amendment_DRAFT.md`](../01_architecture/amarolab_architecture_rtx_amendment_DRAFT.md)
  — architecture amendment draft (Torre as AI compute node).
- [`../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md`](../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md)
  — forward-looking RTX node design rules and invariants.
- [`../01_architecture/remote-access-tailscale.md`](../01_architecture/remote-access-tailscale.md)
  — Tailscale remote-access posture.
- [`../00_overview/CURRENT_STATE.md`](../00_overview/CURRENT_STATE.md)
  — overview triad (to be amended at RTX-1 closeout, not now).
- [`../07_operations/lessons_learned.md`](../07_operations/lessons_learned.md)
  — Lessons 001 / 002 / 003 / 013 underpin §6.

---

## 11. Stop point

Per the operator instruction, this step stops at **documentation of the
local validation**. RTX-1.4 (remote exposure) is **planned but not
executed**. No system modification was performed by this log. The overview
triad will be amended at **RTX-1 closeout**, not now (per Lesson 005 —
overview docs reflect the closed phase, not intermediate milestones).
