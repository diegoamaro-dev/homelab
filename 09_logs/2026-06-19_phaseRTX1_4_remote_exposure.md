# Phase RTX-1.4 — Secure Remote Exposure (Tailscale-only) — APPLIED

- **Date:** 2026-06-19
- **Phase step:** RTX-1.4 — secure remote exposure of Torre's Ollama (Tailscale-only).
- **Ecosystem:** AMAROLAB — Personal Innovation Lab and Digital Infrastructure Ecosystem.
- **Assistant:** AURORA — Personal AI Assistant for the AMAROLAB ecosystem.
- **Independent project on AMAROLAB infrastructure:** Guardian Cloud — not present on Torre; not modified.
- **Node:** Torre — Windows 11 Pro + RTX 5070 (AI compute node).
- **Status:** **APPLIED.** Gates G-1…G-4 PASS. Torre's Ollama is reachable from the UM790 over Tailscale only; LAN blocked; no public exposure. **RTX-1.5 (headless service) and RTX-1.6 (endpoint swap) NOT executed.**
- **Scope:** Torre only — Machine-scope env vars, Windows Firewall rules, Ollama restart. UM790 verification was **read-only curl**. No UM790 / production / Guardian Cloud change.

---

## 1. Context

RTX-1 local validation (2026-06-18,
[`./2026-06-18_phaseRTX1_local_validation.md`](./2026-06-18_phaseRTX1_local_validation.md))
left Torre's Ollama working on the RTX 5070 (~105 tok/s, 29/29 layers on GPU)
but bound to `127.0.0.1:11434` — not reachable by the UM790. RTX-1.4 opens that
path securely. The UM790 remains the 24/7 production node and continues to serve
its own (CPU) Ollama; **no production consumption changes here.** Prior state and
blockers:
[`../04_ai_system/amarolab-v1/phase-rtx/RTX1_validation_summary.md`](../04_ai_system/amarolab-v1/phase-rtx/RTX1_validation_summary.md).

## 2. Objective

Make Torre's Ollama reachable by the UM790 **over Tailscale only** — no LAN
exposure, no public/Cloudflare exposure, no port forwarding — and set
**Machine-scope** env so the future RTX-1.5 service inherits it. Prove
reachability (UM790 → Tailscale) and isolation (LAN blocked) by gates. Do **not**
swap the UM790 endpoint (RTX-1.6) or add persistence (RTX-1.5).

## 3. Decisions

- **D-RTX-1.4-A** — `OLLAMA_HOST=0.0.0.0:11434` (listen on all interfaces). LAN
  isolation is enforced by **Windows Firewall + Tailscale**, **not** by interface
  binding. Rationale: robust for the RTX-1.5 service (no Tailscale-up-before-Ollama
  ordering constraint, no dependency on a specific Tailscale IP).
- **D-RTX-1.4-B** — Least privilege: **ALLOW** inbound TCP 11434 from
  `100.68.180.69/32` (UM790 Tailscale IP only); **BLOCK** from `192.168.178.0/24`
  (LAN); default-deny everything else. **Not** `100.64.0.0/10`.
- Both locked by the operator on 2026-06-19 before execution.

## 4. Implementation

Executed gate-by-gate from **Torre elevated PowerShell** (operator-driven); UM790
steps were read-only curl.

- **Step 0 (read-only baseline) — PASS.** Elevated; Windows Firewall enabled on
  Domain/Private/Public; no pre-existing 11434 or Ollama rule; `OLLAMA_HOST` empty
  (Machine+User); `OLLAMA_MODELS` User=`D:\ai\ollama\models`; Ollama 0.30.10;
  listener `127.0.0.1:11434`; model on D:, C: store empty. UM790 Tailscale peer
  `100.68.180.69` confirmed from Torre's `tailscale status`.
- **Step 1 — Machine-scope env.** `setx /M OLLAMA_HOST "0.0.0.0:11434"`;
  `setx /M OLLAMA_MODELS "D:\ai\ollama\models"`. Verified via
  `[Environment]::GetEnvironmentVariable(...,"Machine")`. User scope untouched.
- **Step 2 — Firewall (group `Amarolab-RTX-1.4`).** `Ollama-Tailscale-Only`
  (Allow, TCP 11434, Remote `100.68.180.69/32`, Profile Any); `Ollama-Block-LAN`
  (Block, TCP 11434, Remote `192.168.178.0/24`, Profile Any). No allow-all rule
  existed to remove. Verified scoping; confirmed these are the only two inbound
  rules on 11434.
- **Step 3 — Restart + local verify.** Stopped all Ollama processes; refreshed the
  session env from Machine scope (**L-RTX-1** — env freezes at launch); relaunched
  the Ollama tray app so the server inherited the new env. Verified the
  `0.0.0.0:11434` bind, the `server.log` config banner, and the local API.
  - *Methodology note:* the first local generate via `curl.exe -d '{…}'` failed
    with `invalid character 'm' looking for beginning of object key string` —
    PowerShell 5.1 stripped the inner quotes from the JSON. Re-run via
    `Invoke-RestMethod` (`ConvertTo-Json`) / `ollama run` succeeded. The server and
    config were correct throughout; only the test payload was malformed.
    (Candidate lesson for RTX-1 closeout.)
- **Step 4 — UM790 read-only reachability (G-3/G-4).** `ip route get` confirmed the
  differential: Tailscale target via `tailscale0` (src `100.68.180.69`), LAN target
  via the LAN interface (src `192.168.178.79`).

## 5. Validation Gates

| Gate | Result | Evidence |
|---|---|---|
| **G-1 Local bind** | PASS | `netstat` → `0.0.0.0:11434`; `server.log` shows `OLLAMA_HOST=0.0.0.0:11434` + `OLLAMA_MODELS=D:\ai\ollama\models`; `/api/version` = 0.30.10 |
| **G-2 GPU placement** | PASS | `/api/generate` → "OK"; **101.9 tok/s**; `ollama ps` PROCESSOR = 100% GPU; `server.log` `offloaded 29/29 layers`, `CUDA0 (RTX 5070)`; `nvidia-smi` `llama-server.exe` type C; ~6.5 GB VRAM |
| **G-3 Tailscale reachability** | PASS | From UM790 → `100.91.154.124:11434`: `/api/version`, `/api/tags` (`qwen2.5:7b-instruct`), `/api/generate` ("OK") all succeed |
| **G-4 LAN blocked** | PASS | From UM790 → `192.168.178.21:11434`: curl timeout, **exit 28** (firewall silent drop; socket listening, packet dropped). Same host as G-3, opposite path |
| **G-5 No public exposure** | Not formally tested | No Cloudflare tunnel; no port forwarding configured; public exposure not expected. Formal confirmation (off-tailnet probe + FRITZ!Box port-forward read) deferred to pre-RTX-1.6 |
| **G-6 Production untouched** | PASS | RTX-1.4 made zero UM790/production changes (all changes Torre-only; UM790 contact was read-only curl). UM790 still serves its own local Ollama; Guardian Cloud, Open WebUI, HA, Qdrant, Mosquitto, Docker, Cloudflare unchanged |

## 6. Rollback

Fully reversible on Torre; nothing to undo off-box (no data moved, no
UM790/production change). **Fast containment** if a LAN/public leak is ever
detected: stop all Ollama processes first (kills the `0.0.0.0` listener), then:

```powershell
Remove-NetFirewallRule -Group "Amarolab-RTX-1.4"
[Environment]::SetEnvironmentVariable("OLLAMA_HOST",  $null, "Machine")
[Environment]::SetEnvironmentVariable("OLLAMA_MODELS",$null, "Machine")   # User-scope D: remains
# refresh session env, relaunch Ollama, confirm: netstat → 127.0.0.1:11434 only; UM790 curl now fails
```

Result = the RTX-1.3 end-state (loopback-only, GPU-validated).

## 7. Final State

| Item | State |
|---|---|
| Ollama bind | `0.0.0.0:11434` (Tailscale-reachable; LAN firewall-blocked) |
| `OLLAMA_HOST` / `OLLAMA_MODELS` | Machine scope = `0.0.0.0:11434` / `D:\ai\ollama\models` |
| Firewall (group `Amarolab-RTX-1.4`) | Allow `100.68.180.69/32`; Block `192.168.178.0/24`; default-deny otherwise |
| Reachability | UM790 → Tailscale `100.91.154.124:11434` OK; LAN `192.168.178.21:11434` blocked; no public path |
| Model | `qwen2.5:7b-instruct` on D:, RTX 5070, 29/29 GPU, ~102 tok/s |
| Persistence | **manual tray app — NOT a service** (RTX-1.5 pending) |
| UM790 | unchanged — still on its local Ollama (RTX-1.6 endpoint swap pending) |

## 8. Security Notes

- **Network-layer is the only access control.** Ollama has no built-in
  authentication; the security boundary is entirely **Windows Firewall** (host) +
  **Tailscale** (encrypted transport + tailnet identity). Acceptable for a
  single-user, Tailscale-only posture.
- **Residual risk (consequence of D-RTX-1.4-A `0.0.0.0` bind):** the Windows
  Firewall is the **sole** control isolating port 11434 from the LAN. Disabling the
  firewall, or adding an inbound allow-all rule for 11434, **re-exposes the LAN.**
  Mitigations in place: explicit LAN block (block wins over allow); least-privilege
  allow (UM790 `/32`); periodic re-check of firewall state and the 11434 rule set.
- **No public path:** behind NAT, no port-forward, no Cloudflare tunnel on Torre.
- **Guardian Cloud untouched** (not present on Torre).
- **Secrets:** none introduced, printed, or committed. Private LAN
  (`192.168.178.x`) and Tailscale (`100.x`) addresses appear here as operational
  detail — not secrets; consistent with existing RTX docs and the repo-wide
  IP-hygiene follow-up tracked in the ROADMAP.
- A dedicated security delta doc (`06_security/rtx_node_security.md`) is **required
  before the RTX-1.6 endpoint swap** (node-bridge §4); recommended to author at the
  RTX-1.4 close while the configuration is fresh.

## 9. Next Steps

- **RTX-1.5** — headless persistence (Windows service) so Ollama survives
  logoff/reboot (currently manual tray app — L-RTX-5). NOT executed.
- **RTX-1.6** — author `06_security/rtx_node_security.md`, then swap the UM790
  `ollama` endpoint (Torre primary + UM790 fallback). NOT executed.
- Optional formal **G-5** (off-tailnet probe + router port-forward read).
- **Documentation scope (operator decision, 2026-06-19):** the overview triad
  (`00_overview/`), the architecture docs, and `06_security/security_posture.md`
  are **intentionally not updated for this sub-step.** RTX-1 remains an active
  phase, so **phase-rtx documentation is the source of truth for RTX execution
  state**, and those layers are amended only at **RTX-1 closeout** (overview triad
  + architecture RTX-amendment DRAFT merge + `security_posture.md` RTX subsection).
- Related:
  [`./2026-06-18_phaseRTX1_local_validation.md`](./2026-06-18_phaseRTX1_local_validation.md),
  [`../04_ai_system/amarolab-v1/phase-rtx/RTX1_validation_summary.md`](../04_ai_system/amarolab-v1/phase-rtx/RTX1_validation_summary.md),
  [`../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md`](../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md),
  [`../01_architecture/remote-access-tailscale.md`](../01_architecture/remote-access-tailscale.md).
