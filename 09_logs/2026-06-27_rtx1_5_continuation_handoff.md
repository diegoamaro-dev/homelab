# RTX-1.5 — Continuation Handoff (G-1.5-6 PASS → next G-1.5-9)

**Status:** RTX-1.5 IN PROGRESS — not closed.

- Date: 2026-06-27 · Validation node: UM790 (`homelab`, read-only cross-checks) · Target node: Torre (Windows 11 Pro + RTX 5070) · Ecosystem: AMAROLAB · Assistant: AURORA
- Purpose: durable continuation handoff so RTX-1.5 can resume exactly at **G-1.5-9 (restart throttle)** if working context is lost. The Torre reboot does **not** affect the UM790 SSH session or the assistant conversation — this file is insurance only.
- This document is **uncommitted by instruction** (see *Git State*). It does **not** modify any existing RTX documentation; the overview triad, `RTX1_validation_summary.md`, `security_posture.md`, and architecture docs remain frozen until RTX-1.5 closeout.

## Discipline (unchanged)

- One step at a time · validate before documenting · reality wins · no unnecessary configuration changes.
- No rewrite of existing documentation and no commit until RTX-1.5 is officially complete (all required gates pass).
- All UM790 checks are read-only. Windows commands are executed by the operator at Torre.

## Current Validated State

### Node / network

- **UM790** (`homelab`): Tailscale `100.68.180.69`, LAN `192.168.178.79/24`. Sole allowlisted Tailscale host for the RTX node.
- **Torre** (`torre`): Tailscale `100.91.154.124` (direct), LAN `192.168.178.21`.
- **Firewall** (Torre, group `Amarolab-RTX-1.4`) — host-scoped /32 allowlist, NOT CGNAT-wide:
  - `Ollama-Tailscale-Only`: Allow / Inbound / TCP 11434 / RemoteAddr `100.68.180.69/32` (UM790 only)
  - `Ollama-Block-LAN`: Block / Inbound / TCP 11434 / RemoteAddr `192.168.178.0/24`

### Service (NSSM wrapper)

- `OllamaService` — LocalSystem, Automatic startup. SCM `Win32_Service.ProcessId` points at the **nssm.exe wrapper**, which launches `ollama.exe serve` as a managed child (expected NSSM architecture, not stale metadata).
- Pre-reboot baseline (now superseded by boot-time PIDs after G-1.5-6): nssm.exe PID 4516 (Session 0, started 2026-06-26 15:05:28) → ollama.exe PID 6788 (serve, Parent 4516, Session 0). No `ollama app.exe` tray (startup shortcut renamed `Ollama.lnk.rtx15-disabled`, reversible).
- Environment: `OLLAMA_HOST=0.0.0.0:11434`, `OLLAMA_MODELS=D:\ai\ollama\models`. Logs: `D:\ai\ollama\logs\server.log` / `server-err.log`.
- Restart handling (ACTUAL — NSSM 2.24 `nssm get`, verified 2026-06-27): `AppExit Default`=`Restart`; `AppRestartDelay`=**0** (default, immediate restart); `AppThrottle`=**1500** (default fail-fast window); process-tree kill = NSSM **default behavior** (ON) — the `AppKillProcessTree` opt-out is not exposed via `nssm get` in this 2.24 build. The frozen phase log's `AppRestartDelay=10000` / `AppThrottle=10000` / `AppKillProcessTree=1` were **never applied** — see *Configuration Reconciliation*.
- Model: `qwen2.5:7b-instruct` (Q4_K_M, 7.6B). Ollama version `0.30.10`.
- GPU: RTX 5070, CUDA0, 29/29 layers offloaded, `size_vram == size`, ~111.6 tok/s. VRAM idle ~1.5 GB / warm ~6.3 GB.

### Evidence captured this cycle

- **G-1.5-7** firewall re-check — UM790 differential re-confirmed (`/api/version`=0.30.10, `/api/tags`=qwen2.5:7b-instruct, `/api/generate`→`RTX157-OK`; LAN `192.168.178.21:11434` curl exit 28); Torre group re-check confirmed rules present + Enabled, host-scoped /32 allowlist.
- **G-1.5-5** logoff — UM790-side 8/8 availability probes over ~40 s, 0 failures, while the operator was signed out; end-to-end inference `RTX155-LOGOFF-OK` (done_reason=stop). PID continuity proven — after-relogin snapshot matched baseline exactly (nssm 4516 @ 2026-06-26 15:05:28, ollama.exe 6788 / Parent 4516 / Session 0, CreationDate unchanged). No silent restart across logoff.
- **G-1.5-6** reboot without login — **PASS (core persistence proof).**
  - Operator-reported (Torre): Windows rebooted; no interactive user login; service answered over Tailscale before any login.
  - UM790 independent confirmation (read-only, 2026-06-27): `/api/version`=0.30.10; `/api/tags`=qwen2.5:7b-instruct; `/api/generate`→`RTX156-NOLOGIN-OK`, done_reason=stop; LAN `192.168.178.21:11434` curl exit 28 (blocked).
  - **GPU offload restored at cold boot (no login):** `/api/ps` → `size_vram` 4748056984 == `size` 4748056984 (full offload); throughput proxy ~89.5 tok/s on an 11-token gen (GPU range; short-gen understates vs ~111 tok/s warm benchmark). Confirms CUDA initialized in Session 0 at boot — no CPU fallback.

## Configuration Reconciliation — phase log vs actual NSSM 2.24 (reality wins)

G-1.5-9 Step 1 (`nssm get`) revealed the frozen phase log documents restart/kill values that were **never actually applied**. Verified against NSSM docs (nssm.cc/usage + changelog mirrors).

| Parameter | Phase log claim | Actual (`nssm get`) | Notes |
|---|---|---|---|
| Application / AppParameters / AppDirectory / AppEnvironmentExtra | as documented | MATCH | correct |
| AppExit Default | Restart | Restart | match (also the NSSM default) |
| AppRestartDelay | 10000 | **0** | NSSM default (immediate restart); 10000 never applied |
| AppThrottle | 10000 | **1500** | NSSM default fail-fast window; 10000 never applied |
| AppKillProcessTree | `=1` | **not set / not exposed in 2.24** | tree-kill is the NSSM *default*; see below |

- **Process-tree kill (Q3):** NSSM terminates the **entire process tree by default**. `AppKillProcessTree` is the *opt-out* (set to `0` to apply stop methods only to the named process). This 2.24 build does not expose it via `nssm get`; with it unset, the default (tree-kill ON) is in effect. There is no meaningful "=1" to set — the protective behavior is the default. Stop granularity in 2.24 is otherwise governed by `AppStopMethodSkip` (bitmask) and the `AppStopMethodConsole/Window/Threads` timeouts.
- **Impact on G-1.5-8:** the empirical PASS (no orphan llama-server; VRAM recovered on stop/restart/crash) **stands** — it was observed against this real config. Only the *attribution* is wrong: the no-orphan result is due to NSSM 2.24's **default** tree termination, not an explicitly set `AppKillProcessTree=1`. Reword at closeout.
- **Functional verdict:** the actual defaults already provide automatic restart (`AppExit=Restart`), busy-loop protection (`AppThrottle=1500`), and process-tree kill — covering RTX-1.5's restart goals, and already validated by G-1.5-8.
- **Open decision (operator):** (1) keep actual defaults + redefine G-1.5-9 against them; (2) apply full documented intent (`nssm set AppRestartDelay 10000` + `AppThrottle 10000`); or (3) hybrid (`AppThrottle 10000` only). Crash test PAUSED until decided.

## Completed Gates

| Gate | Result | Evidence |
|---|---|---|
| G-1.5-1 | PASS | Service Running, Automatic |
| G-1.5-2 | PASS | Env vars present in startup logs |
| G-1.5-3 | PASS | Single listener `0.0.0.0:11434`, no tray, version 0.30.10 |
| G-1.5-4 | PASS | GPU placement: RTX 5070, CUDA0, 29/29, size_vram==size, ~111.6 tok/s; LocalSystem sees GPU in Session 0 |
| UM790 cross-check | PASS | RTX-1.4 posture (Tailscale reachable, LAN blocked) |
| G-1.5-8 (critical) | PASS | Teardown/VRAM: stop/restart/crash → no orphan llama-server, VRAM recovers, single listener |
| **G-1.5-7** | PASS | Firewall re-check, both halves (see Evidence above) |
| **G-1.5-5** | PASS | Logoff persistence + PID continuity (see Evidence above) |
| **G-1.5-6** | PASS | Reboot without login: serves over Tailscale pre-login + GPU offload restored at cold boot (see Evidence above) |
| **G-1.5-9** | PASS | Restart throttle: NSSM Event Log shows 0→2000→4000 ms back-off (event 1034, doubling per spec); tree-kill logged (1023/1027); clean recovery. `restart#3=0s` was a poller artifact (child PID 16340, not a fresh restart). |
| **G-1.5-10** | PASS | Production integrity: Open WebUI `OLLAMA_BASE_URL=http://ollama:11434` (local v0.17.7, serving); Torre IP absent from all 16 container envs (no swap); all containers Up; HA endpoint local. Host rebooted ~1h20m ago (UM790 event, not RTX-1.5); stack recovered. Caveat: Open WebUI `webui.db` (UI-added endpoints) not inspected — outside compose/env scope. |

## Pending Gates (all in scope — kept in RTX-1.5 per operator decision)

| Gate | Status | Notes |
|---|---|---|
| _(none)_ | — | **All RTX-1.5 gates PASS.** Remaining: RTX-1.5 closeout (single doc pass + one commit). |

## Next Exact Step — G-1.5-9 restart throttle

> **STATUS (2026-06-27):** Step 1 complete — config mismatch found (see *Configuration Reconciliation*). **G-1.5-9 PASS** (validated against actual NSSM 2.24 config; no config change). NSSM Event Log proves the throttle: consecutive fast-exits delayed restart by **0 → 2000 → 4000 ms** (doubling, exactly per spec; event ID 1034). Process-tree kill directly logged (event IDs 1023/1027). End-state recovered: Running, single instance `11364` (parent = nssm wrapper `5124`), UM790 serving + `size_vram==size`. The earlier `restart#3=0s` was a measurement artifact — the PID poller caught Ollama's child `ollama.exe` (PID `16340`, logged as a child in PID `7340`'s tree), not a fresh restart; the real restart#3 = PID `11364` after the 4000 ms throttle. Deferred `AppThrottle=10000` remains a post-closeout hardening option.

Goal: prove NSSM restart behavior matches the *actual* config — after an unexpected exit the child restarts **promptly** (`AppRestartDelay=0`); under rapid repeated fail-fast exits (< `AppThrottle`=1500 ms) NSSM **backs off** instead of busy-looping; the process tree is cleaned (NSSM default tree-kill) with no orphaned llama-server; the nssm wrapper PID stays stable while the child cycles; service stabilizes to Running with a single listener; UM790 confirms functional recovery + GPU offload.

### Step 1 — Torre: confirm configuration via `nssm get` (read-only)

NSSM 2.24 has **no `dump` subcommand** (it only prints usage) — use per-parameter `nssm get`. This also serves as the full parameter-lock capture the frozen phase log flagged as a closeout item.

```powershell
$n="C:\Tools\nssm\nssm.exe"; $s="OllamaService"
& $n get $s Application
& $n get $s AppParameters
& $n get $s AppDirectory
& $n get $s AppEnvironmentExtra
& $n get $s AppExit Default
& $n get $s AppRestartDelay
& $n get $s AppThrottle
& $n get $s AppKillProcessTree
```
Expect: Application = `…\Ollama\ollama.exe`, AppParameters = `serve`, AppDirectory = `…\Ollama`, AppEnvironmentExtra = `OLLAMA_HOST=0.0.0.0:11434` + `OLLAMA_MODELS=D:\ai\ollama\models`, AppExit Default = `Restart`, AppRestartDelay = `10000`, AppThrottle = `10000`, AppKillProcessTree = `1`. Note: `nssm get` emits UTF-16 — read by eye, do not string-compare programmatically.

### Step 2 — Torre: single-crash restart-delay test

```powershell
Get-Date -Format o
Get-CimInstance Win32_Process -Filter "Name='ollama.exe'" | Select ProcessId,CreationDate
Stop-Process -Name ollama -Force                      # crash the managed child
# poll until a NEW ollama.exe appears; AppRestartDelay=0 -> prompt (elapsed = Ollama startup, not a 10s delay)
1..20 | % { Start-Sleep 1; $p=Get-CimInstance Win32_Process -Filter "Name='ollama.exe'"; if($p){ "restarted PID $($p.ProcessId) at $(Get-Date -Format o)"; break } else { "waiting $_" } }
```

### Step 3 — Torre: throttle / back-off test + logs

```powershell
# crash again immediately after restart, 2-3 times, to exercise the throttle window
Stop-Process -Name ollama -Force
# inspect NSSM / service events for restart + throttle messages
Get-WinEvent -LogName Application -MaxEvents 40 |
  ? { $_.ProviderName -like '*nssm*' -or $_.Message -like '*OllamaService*' } |
  Format-Table TimeCreated, Id, Message -Auto
Get-Service OllamaService | Select Name,Status,StartType
```

### Step 4 — UM790: confirm recovery (read-only)

```bash
T=100.91.154.124
curl -s --connect-timeout 5 --max-time 10 http://$T:11434/api/version
curl -s --connect-timeout 5 --max-time 60 http://$T:11434/api/generate \
  -d '{"model":"qwen2.5:7b-instruct","prompt":"Reply with exactly: RTX159-THROTTLE-OK","stream":false}'
curl -s --connect-timeout 5 --max-time 10 http://$T:11434/api/ps | grep -o '"name":"[^"]*"\|"size":[0-9]*\|"size_vram":[0-9]*'
```

### G-1.5-9 PASS criteria (actual config)

- Config confirmed: `AppExit Default=Restart`, `AppRestartDelay=0`, `AppThrottle=1500`, process-tree kill = NSSM default (Step 1 ✅).
- **Test A — normal crash** (child ran > 1500 ms): NSSM auto-restarts **promptly** (no long stall); nssm wrapper PID unchanged; new ollama.exe PID; single instance; service Running.
- **Test B — rapid fail-fast**: NSSM **throttles/backs off** (no busy-loop / CPU spin); Event Log shows restart/throttle; service self-stabilizes to Running.
- Process tree cleaned each cycle: no orphan ollama/llama-server; VRAM recovers; single listener (re-confirms G-1.5-8 mechanism, now correctly attributed to NSSM default tree-kill).
- UM790 confirms endpoint recovers, inference `RTX159-THROTTLE-OK`, GPU offload restored (`size_vram==size`).

## Documentation Still Pending (frozen until RTX-1.5 closeout)

- `09_logs/2026-06-19_phaseRTX1_5_headless_service.md` — committed, IN PROGRESS; still lists G-1.5-9/10 pending (and now-passed 5/6/7 to fold in at closeout).
- `00_overview/CURRENT_STATE.md` (line ~178) — still reads `RTX-1.5 … Not started` (stale; update at closeout).
- `04_ai_system/amarolab-v1/phase-rtx/RTX1_validation_summary.md` — not yet updated for RTX-1.5.
- `06_security/security_posture.md` — pending host-scoped /32 allowlist note.
- `01_architecture/amarolab_architecture_rtx_amendment_DRAFT.md` — draft amendment exists; promote at RTX-1 closeout.
- **Corrections to apply at closeout:** (1) firewall is a host-scoped /32 allowlist (UM790 only), NOT a CGNAT-wide range; (2) record the G-1.5-9/10 reconciliation outcome (kept in scope per operator decision); (3) restart/kill config — phase log's `AppRestartDelay=10000` / `AppThrottle=10000` / `AppKillProcessTree=1` were never applied (actual: 0 / 1500 / default tree-kill); reword the G-1.5-8 conclusion to attribute no-orphan behavior to NSSM 2.24's default process-tree termination — now directly evidenced by the G-1.5-9 NSSM Event Log (events 1023/1027 "Killing process tree of process …").

## Git State

- Repo `/home/diego/homelab`, branch `main`, remote `origin git@github.com:diegoamaro-dev/homelab.git`.
- HEAD: `e887b59e docs(rtx-1.5): document NSSM service migration progress`.
- This handoff file is **untracked and intentionally NOT staged, committed, or pushed** per instruction. RTX-1.5 closeout remains a single future commit after all required gates pass.

## Documentation Convention / Security Note

- Private LAN (192.168.178.x) and Tailscale (100.x) addresses appear here as operational detail, not secrets — consistent with existing RTX docs and the repo-wide IP-hygiene follow-up tracked in the ROADMAP.

## Where RTX-1.5 Stands

Service built, GPU-accelerated, network-isolated (host-scoped /32), teardown-safe (G-1.5-8), firewall-revalidated (G-1.5-7), logoff-resilient with PID continuity (G-1.5-5), and **persistent across reboot without login with GPU offload restored at cold boot (G-1.5-6) — the core RTX-1.5 objective is now proven.** RTX-1.5 remains OPEN pending **G-1.5-9 (restart throttle)** and **G-1.5-10 (production integrity)** — both kept in scope. After those pass (or 9/10 are explicitly reconciled as covered): RTX-1.5 closeout (single doc pass + one commit). No endpoint swap (RTX-1.6); Open WebUI / Home Assistant / Guardian Cloud / Cloudflare untouched.
