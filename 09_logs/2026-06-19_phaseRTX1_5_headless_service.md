# RTX-1.5 — Headless Ollama Service (NSSM)

**Status:** IN PROGRESS — NOT closed.

- Date: 2026-06-19 · Node: Torre (Windows 11 Pro + RTX 5070) · Ecosystem: AMAROLAB · Assistant: AURORA
- PASS: G-1.5-1, G-1.5-2, G-1.5-3, G-1.5-4, UM790 cross-check, **G-1.5-8 (teardown / VRAM — critical)**
- PENDING: G-1.5-5 (logoff), G-1.5-6 (reboot without login), G-1.5-7 (firewall re-check), G-1.5-9 (restart throttle), G-1.5-10 (production integrity)
- Persistence across logoff/reboot is **not yet proven**. No UM790 endpoint swap (RTX-1.6). Torre-only; no Open WebUI / Home Assistant / Guardian Cloud / Cloudflare change.

## Context

RTX-1.5 migrates Ollama on the RTX node from the interactive tray application to a persistent Windows service.

Goals:

- survive user logoff
- survive reboot without login
- keep RTX-1.4 network posture
- preserve GPU acceleration
- prevent orphaned llama-server processes
- provide deterministic restart behavior

## Initial State

Before RTX-1.5:

- Ollama running through tray application
- Startup shortcut located in:

C:\Users\<USERNAME>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\Ollama.lnk

- Tailscale-only exposure already validated by RTX-1.4
- LAN access blocked by Windows Firewall
- GPU serving validated through interactive session

The startup shortcut was disabled by renaming it to `Ollama.lnk.rtx15-disabled` (reversible; restored on rollback). No Run keys were present (HKCU/HKLM).

## Security Hardening

### NSSM binary

Installed:

C:\Tools\nssm\nssm.exe

Version:

- NSSM 2.24 64-bit

SHA256:

F689EE9AF94B00E9E3F0BB072B34CAAF207F32DCB4F5782FC9CA351DF9A06C97

Authenticode:

- NotSigned (expected for the nssm 2.24 release)
- trusted by SHA256 match to the canonical nssm 2.24 win64 binary + official download origin

### ACL hardening

Issue discovered:

Authenticated Users inherited Modify permissions on:

C:\Tools\nssm

Risk:

- service binary replacement
- privilege escalation to LocalSystem

Mitigation:

- inheritance removed
- explicit permissions applied

Final ACL (folder and binary):

- Administrators: FullControl
- SYSTEM: FullControl
- Users: ReadAndExecute
- Authenticated Users: (removed)

Backup created (restore with `icacls "C:\Tools" /restore <file>`):

D:\ai\ollama\logs\acl-backup_C-Tools-nssm_pre-2.7.txt

### LocalSystem access

Confirmed (read + write probe executed in SYSTEM context):

- D:\ai\ollama\models — readable
- D:\ai\ollama\logs — writable

### Execution policy

No policy blocks service execution from C:\Tools:

- SRP not enforcing (no DefaultLevel / TransparentEnabled, no path rules)
- AppLocker: no effective rules
- WDAC usermode Code Integrity = audit (non-blocking)
- nssm.exe executes successfully

## Service Configuration

Service:

OllamaService

Identity:

LocalSystem

Startup:

Automatic

Application:

C:\Users\<USERNAME>\AppData\Local\Programs\Ollama\ollama.exe

Arguments:

serve

Working directory:

C:\Users\<USERNAME>\AppData\Local\Programs\Ollama

Environment:

OLLAMA_HOST=0.0.0.0:11434
OLLAMA_MODELS=D:\ai\ollama\models

Logs:

D:\ai\ollama\logs\server.log
D:\ai\ollama\logs\server-err.log

Process tree handling:

AppKillProcessTree=1

Restart handling:

AppExit Default Restart
AppRestartDelay=10000
AppThrottle=10000

Provenance:

- core parameters (Application, AppParameters, AppDirectory, AppEnvironmentExtra, AppKillProcessTree=1, Start, Identity, log paths) re-verified via `nssm get` after Step 3.1
- auto-restart behavior confirmed empirically by G-1.5-8
- a full `nssm dump OllamaService` capture to lock every parameter (incl. restart/throttle/rotation) is a closeout item

## Incident — Initial Service Misconfiguration (Step 3)

During the first service creation, the install command used a PowerShell variable (`$ollama`) that expanded **empty** in that session.

Effect:

- `nssm install OllamaService "$ollama" serve` became `nssm install OllamaService serve`
- NSSM stored **Application = "serve"** (AppParameters / AppDirectory / AppEnvironmentExtra empty)
- the service never reached the Ollama binary
- on start it entered **SERVICE_STOPPED** immediately

Diagnosis:

- read-only inspection with `nssm get` revealed Application = "serve" and the empty parameters
- root cause confirmed: empty variable expansion — not GPU, not LocalSystem, not D: permissions

Correction (Step 3.1):

- all parameters re-set using **literal values** (no variables)
- re-verified with `nssm get` (Application = full ollama.exe path, AppParameters = serve, AppDirectory set, AppEnvironmentExtra = both vars, AppKillProcessTree = 1)
- service then started cleanly (see Validation Results)

Candidate lesson (to add to lessons_learned.md at RTX-1 closeout): after `nssm install`, always verify `Application` with `nssm get` / `nssm dump`; an empty variable corrupts it silently. Do not string-compare `nssm get` output programmatically (it is emitted as UTF-16).

## Validation Results

### G-1.5-1

PASS

Service status:

Running

Startup:

Automatic

### G-1.5-2

PASS

Environment variables detected in service startup logs.

### G-1.5-3

PASS

Single listener:

0.0.0.0:11434

Tray application not running.

API version:

0.30.10

### G-1.5-4

PASS

GPU placement validated.

Evidence:

- qwen2.5:7b-instruct loaded
- size_vram = size
- VRAM increased from ~1.6 GB to ~6.3 GB
- offloaded 29/29 layers
- CUDA0 selected
- RTX 5070 detected
- throughput: 111.6 tokens/sec

LocalSystem detected the RTX 5070 in Session 0 — the session-0 / LocalSystem CUDA failure hypothesis is discarded.

### UM790 Cross Check

PASS

- Tailscale: reachable (torre 100.91.154.124, direct)
- /api/version, /api/tags, /api/generate: all succeeded (end-to-end inference from the UM790 over Tailscale)
- LAN path (192.168.178.21:11434): blocked (curl exit 28)

Note: read-only probe directly against Torre's API. The UM790 Ollama endpoint was NOT repointed (endpoint swap is RTX-1.6).

## G-1.5-8 Critical Validation

Objective:

Validate NSSM process tree cleanup and VRAM recovery.

### Stop Test

Result:

PASS

Observed:

- service stopped
- no ollama process
- no llama-server process
- port 11434 closed
- VRAM returned to idle (~1.5 GB)

### Restart Test

Result:

PASS

Observed:

- service restarted successfully
- no duplicated runners
- single llama-server instance
- VRAM returned to ~6.2 GB after warmup

### Crash Test

Method:

Forced termination of ollama.exe.

Observed:

- NSSM restarted service automatically
- previous llama-server process disappeared
- no orphan process remained
- VRAM returned to idle before restart
- listener restored successfully

Result:

PASS

Evidence summary:

- Stop → VRAM returns to idle (~1.5 GB)
- Restart → clean tree (single ollama.exe, no leftover runner)
- Warmup → VRAM ~6.3 GB (single llama-server)
- Crash test → no orphaned llama-server
- Auto-restart correct (NSSM relaunched the service)
- VRAM recovery confirmed (idle before restart)

Conclusion:

AppKillProcessTree=1 successfully prevents orphaned llama-server processes and VRAM retention after service crashes. This validates the NSSM-over-WinSW decision on the teardown criterion (safe-by-default recursive process-tree cleanup covering stop, restart, and crash).

## Final State

The RTX node serves Ollama as a headless Windows service (NSSM, LocalSystem, Automatic startup).

Validated posture:

- Tailscale-only exposure (reachable from the UM790)
- LAN blocked (Windows Firewall, RTX-1.4 rules)
- Automatic startup
- GPU acceleration active (29/29 layers, ~111 tok/s)
- Process-tree cleanup validated (G-1.5-8): no orphan llama-server, VRAM recovered on stop / restart / crash

Not yet proven (pending gates):

- survival across user logoff (G-1.5-5)
- survival across reboot without login (G-1.5-6)
- firewall group re-check (G-1.5-7)
- restart throttle behavior (G-1.5-9)
- production integrity (G-1.5-10)

RTX-1.5 is **IN PROGRESS** — not closed. Persistence across logoff/reboot — the core objective — is not yet demonstrated.

## Remaining RTX-1.5 Gates

Pending:

- G-1.5-5 logoff validation (login → confirm tray does not start → logoff → still serving)
- G-1.5-6 reboot without login (the core persistence proof)
- G-1.5-7 firewall revalidation (reachability differential already confirmed by the UM790 cross-check; Torre-side `Get-NetFirewallRule -Group Amarolab-RTX-1.4` group re-check pending)
- G-1.5-9 restart throttle validation
- G-1.5-10 production integrity validation (UM790 endpoint not swapped; Open WebUI / HA / Guardian Cloud / Cloudflare unchanged)

After the pending gates pass: RTX-1.5 closeout, then RTX-1.6 (security delta doc `06_security/rtx_node_security.md` + UM790 endpoint swap). Per the RTX-1 documentation convention, the overview triad, architecture docs, and `security_posture.md` are amended only at RTX-1 closeout — not per sub-step.

## Documentation Convention / Security Note

- Always-on listener increases LAN exposure duration vs the manual tray app; the Windows Firewall is the sole control isolating port 11434 from the LAN. Periodic firewall-rule integrity checks recommended — input for `06_security/rtx_node_security.md` (RTX-1.6).
- Private LAN (192.168.178.x) and Tailscale (100.x) addresses appear here as operational detail, not secrets; consistent with existing RTX docs and the repo-wide IP-hygiene follow-up tracked in the ROADMAP.

## Related Documents

- [`./2026-06-19_phaseRTX1_4_remote_exposure.md`](./2026-06-19_phaseRTX1_4_remote_exposure.md) — RTX-1.4 secure remote exposure (prior step)
- [`./2026-06-18_phaseRTX1_local_validation.md`](./2026-06-18_phaseRTX1_local_validation.md) — RTX-1 local GPU validation
- [`../04_ai_system/amarolab-v1/phase-rtx/RTX1_validation_summary.md`](../04_ai_system/amarolab-v1/phase-rtx/RTX1_validation_summary.md) — phase-level rollup (update at RTX-1.5 closeout)
- [`../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md`](../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md) — node design rules / invariants
- [`../07_operations/lessons_learned.md`](../07_operations/lessons_learned.md) — candidate lessons L-RTX-3 / L-RTX-4 (add at closeout)
