# RTX-1.5 — Headless Ollama Service (NSSM)

**Status:** CLOSED — RTX-1.5 complete (2026-06-27). All gates PASS.

- Date: 2026-06-19 · Node: Torre (Windows 11 Pro + RTX 5070) · Ecosystem: AMAROLAB · Assistant: AURORA
- PASS (all): G-1.5-1, G-1.5-2, G-1.5-3, G-1.5-4, UM790 cross-check, **G-1.5-8 (teardown / VRAM — critical)**, **G-1.5-7 (firewall re-check)**, **G-1.5-5 (logoff + PID continuity)**, **G-1.5-6 (reboot without login — core persistence proof)**, **G-1.5-9 (restart throttle)**, **G-1.5-10 (production integrity)**
- Persistence across logoff and reboot-without-login is **PROVEN** (G-1.5-5 / G-1.5-6), GPU offload restored at cold boot. No UM790 endpoint swap (RTX-1.6 pending). Torre-only; Open WebUI / Home Assistant / Guardian Cloud / Cloudflare unchanged (verified G-1.5-10).
- Closeout 2026-06-27. Gate detail + reality reconciliations in *Closeout (2026-06-27)* below; full session evidence in [`2026-06-27_rtx1_5_continuation_handoff.md`](./2026-06-27_rtx1_5_continuation_handoff.md).

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

NSSM 2.24 **default** process-tree termination (kills the whole tree on stop). `AppKillProcessTree` is the opt-out (=0) and is not exposed via `nssm get` in 2.24; with it unset, tree-kill is ON by default. (Corrected at closeout — the earlier `AppKillProcessTree=1` was never a set parameter; see *Closeout*.)

Restart handling (actual NSSM 2.24 `nssm get` — corrected at closeout):

AppExit Default Restart
AppRestartDelay=0  (NSSM default — immediate restart)
AppThrottle=1500  (NSSM default fail-fast window)

The earlier `AppRestartDelay=10000` / `AppThrottle=10000` were documented intent that was **never applied**; the service has run on NSSM defaults throughout, validated sufficient by G-1.5-9. See *Closeout*.

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

NSSM 2.24's **default** process-tree termination prevents orphaned llama-server processes and VRAM retention after service crashes (corrected attribution — the result is the NSSM default, not a configured `AppKillProcessTree=1`, which was never set; see *Closeout*). This validates the NSSM-over-WinSW decision on the teardown criterion (safe-by-default recursive process-tree cleanup covering stop, restart, and crash). Directly evidenced at G-1.5-9 by NSSM Event Log entries 1023/1027 ("Killing process tree of process …").

## Final State

The RTX node serves Ollama as a headless Windows service (NSSM, LocalSystem, Automatic startup).

Validated posture:

- Tailscale-only exposure (reachable from the UM790)
- LAN blocked (Windows Firewall, RTX-1.4 rules)
- Automatic startup
- GPU acceleration active (29/29 layers, ~111 tok/s)
- Process-tree cleanup validated (G-1.5-8): no orphan llama-server, VRAM recovered on stop / restart / crash

Now proven (closeout 2026-06-27):

- survival across user logoff + PID continuity (G-1.5-5)
- survival across reboot without login, GPU offload restored at cold boot (G-1.5-6 — core objective)
- firewall group re-check, host-scoped /32 allowlist (G-1.5-7)
- restart throttle behavior, 0→2000→4000 ms back-off (G-1.5-9)
- production integrity, endpoint not swapped, stack unchanged (G-1.5-10)

RTX-1.5 is **CLOSED** — headless persistence demonstrated end-to-end. See *Closeout (2026-06-27)*.

## Closeout (2026-06-27)

All RTX-1.5 gates PASS. The RTX node serves Ollama as a LocalSystem NSSM service that survives logoff and reboot-without-login with GPU acceleration intact.

### Gate results (G-1.5-5/6/7/9/10)

- **G-1.5-7 firewall re-check — PASS.** UM790 differential re-confirmed (Tailscale `/api/version`=0.30.10, `/api/tags`, `/api/generate`→OK; LAN `192.168.178.21:11434` curl exit 28). Torre group `Amarolab-RTX-1.4` rules present + Enabled. **Firewall is a host-scoped /32 allowlist**: `Ollama-Tailscale-Only` allow `100.68.180.69/32` (UM790 only) + `Ollama-Block-LAN` block `192.168.178.0/24` — tighter than a CGNAT-wide allow.
- **G-1.5-5 logoff — PASS.** UM790-side 8/8 availability probes over ~40 s while signed out + end-to-end inference. PID continuity proven: nssm wrapper + ollama child PIDs unchanged across logoff (no silent restart).
- **G-1.5-6 reboot without login — PASS (core).** After reboot with no interactive login, the service served over Tailscale before any login; `/api/generate` OK; GPU offload restored at cold boot (`/api/ps` `size_vram==size`) — CUDA initialized in Session 0 at boot, no CPU fallback. LAN blocked.
- **G-1.5-9 restart throttle — PASS.** Validated against the ACTUAL NSSM defaults. NSSM Event Log (event 1034) shows fast-exit back-off `0 → 2000 → 4000 ms` (doubling, exactly per spec); process-tree kill logged (events 1023/1027); clean recovery to a single instance.
- **G-1.5-10 production integrity — PASS.** RTX-1.5 stayed Torre-scoped: UM790 Open WebUI endpoint still `http://ollama:11434` (local ollama v0.17.7), Torre IP absent from all container envs (no RTX-1.6 swap); all 16 production containers Up; HA / Guardian Cloud / Cloudflare untouched.

### Reality reconciliations (reality wins)

1. **NSSM restart params**: documented `AppRestartDelay=10000` / `AppThrottle=10000` were **never applied** — the service runs NSSM defaults (`0` / `1500`), validated sufficient (G-1.5-9). Any move to `AppThrottle=10000` is deferred to a separate post-closeout hardening change.
2. **Process-tree kill**: no configured `AppKillProcessTree=1`; NSSM 2.24 kills the tree **by default** (opt-out param not exposed in 2.24). G-1.5-8 conclusion + Service Configuration re-attributed above.
3. **NSSM 2.24 has no `dump`** — config captured via per-parameter `nssm get` (the parameter-lock capture this log flagged as a closeout item; recorded below).
4. **Firewall** is a host-scoped /32 allowlist (UM790 only), not a CGNAT-wide allow.
5. Local UM790 production ollama is **v0.17.7** (CPU), distinct from Torre **0.30.10** (GPU) — endpoint not swapped.

### Parameter lock (NSSM 2.24 `nssm get`)

`Application`=`C:\Users\diego\AppData\Local\Programs\Ollama\ollama.exe` · `AppParameters`=`serve` · `AppDirectory`=`…\Ollama` · `AppEnvironmentExtra`=`OLLAMA_HOST=0.0.0.0:11434` + `OLLAMA_MODELS=D:\ai\ollama\models` · `AppExit Default`=`Restart` · `AppRestartDelay`=`0` · `AppThrottle`=`1500` · process-tree kill = NSSM default.

### Candidate lessons (to add to `07_operations/lessons_learned.md`)

- **L-RTX-3**: after `nssm install/set`, always verify with `nssm get` — an empty PowerShell variable silently corrupts `Application` (Step 3 incident), and documented param intent can silently never-apply (the 10000/10000 drift).
- **L-RTX-4**: match validation tooling to the installed version — NSSM 2.24 lacks `dump`; throttle back-off is `0→2000→4000 ms` doubling (event 1034); process-tree kill is the 2.24 default (events 1023/1027), not a set parameter.

### Documentation scope at this closeout

Overview triad (CURRENT_STATE / AMAROLAB_HANDOFF / ROADMAP) refreshed to RTX-1.4 + RTX-1.5 complete (per operator direction, a deliberate refresh ahead of the usual RTX-1-closeout cadence). `security_posture.md` and the architecture amendment (DRAFT) remain **deferred to RTX-1.6**, where RTX node security lands in its own `06_security/rtx_node_security.md`. Next: **RTX-1.6** — security delta doc + UM790 `ollama` endpoint swap (Torre primary + UM790 fallback).

## Documentation Convention / Security Note

- Always-on listener increases LAN exposure duration vs the manual tray app; the Windows Firewall is the sole control isolating port 11434 from the LAN. Periodic firewall-rule integrity checks recommended — input for `06_security/rtx_node_security.md` (RTX-1.6).
- Private LAN (192.168.178.x) and Tailscale (100.x) addresses appear here as operational detail, not secrets; consistent with existing RTX docs and the repo-wide IP-hygiene follow-up tracked in the ROADMAP.

## Related Documents

- [`./2026-06-19_phaseRTX1_4_remote_exposure.md`](./2026-06-19_phaseRTX1_4_remote_exposure.md) — RTX-1.4 secure remote exposure (prior step)
- [`./2026-06-18_phaseRTX1_local_validation.md`](./2026-06-18_phaseRTX1_local_validation.md) — RTX-1 local GPU validation
- [`../04_ai_system/amarolab-v1/phase-rtx/RTX1_validation_summary.md`](../04_ai_system/amarolab-v1/phase-rtx/RTX1_validation_summary.md) — phase-level rollup (update at RTX-1.5 closeout)
- [`../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md`](../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md) — node design rules / invariants
- [`../07_operations/lessons_learned.md`](../07_operations/lessons_learned.md) — candidate lessons L-RTX-3 / L-RTX-4 (add at closeout)
