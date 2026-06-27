# RTX Node Security — Torre

Last updated: 2026-06-27

- **Scope:** Security architecture of the **Torre** RTX
  compute node as deployed after **RTX-1.5**.
- **Status:** Durable reference. Describes the
  **deployed reality** of RTX-1.4 (secure remote
  exposure, 2026-06-19) + RTX-1.5 (headless NSSM
  service, 2026-06-27). Companion to
  [`security_posture.md`](security_posture.md).
- **Node:** Torre — Windows 11 Pro + NVIDIA RTX 5070,
  on-demand GPU compute for **AURORA** (the AMAROLAB
  Personal AI Assistant).
- **Independent project:** Guardian Cloud is **not
  present on Torre** and is not touched by anything in
  this document.
- **RTX-1.6 update (2026-06-27):** the UM790 now consumes
  Torre via the `ollama-proxy` failover front end (Torre
  primary + UM790 CPU fallback). That swap is **UM790-side**
  and changes **no** Torre-node control described here.
  Proxy / consumer-side security:
  [`security_posture.md`](security_posture.md) +
  [RTX-1.6 apply log](../09_logs/2026-06-27_phaseRTX1_6_endpoint_swap_applied.md).

---

# Reading conventions

This document follows the AMAROLAB documentation rules
(see [`../00_overview/PROJECT_RULES.md`](../00_overview/PROJECT_RULES.md)).
To keep facts and intentions separate:

```text
Plain statement      → DEPLOYED, gate-validated reality
                       (RTX-1.4 + RTX-1.5).
Recommendation —     → Advisory. NOT yet deployed.
Out of scope —       → Belongs to RTX-1.6 or later;
                       deliberately not described here.
```

If anything here disagrees with
[`../00_overview/CURRENT_STATE.md`](../00_overview/CURRENT_STATE.md),
CURRENT_STATE.md is the operational source of truth
until the inconsistency is reconciled.

---

# Notation — network identifiers (non-secret)

This document reuses the LAN and Tailscale addresses
already recorded in
[`../00_overview/CURRENT_STATE.md`](../00_overview/CURRENT_STATE.md)
and the RTX apply logs. Per the ROADMAP IP-hygiene
follow-up, private (RFC 1918) and Tailscale (CGNAT)
addresses are **operational detail, not secrets**, and
their sanitisation is an explicit **repo-wide** decision
that has been deferred (sanitising one file in isolation
would be inconsistent). They are reproduced here for
consistency with the source of truth.

| Identifier | Role |
|---|---|
| `100.68.180.69` | UM790 (`homelab`) Tailscale IP — the **only** host allowed to reach Torre's Ollama |
| `100.91.154.124` | Torre (`torre`) Tailscale IP — the address the UM790 reaches over the tailnet |
| `192.168.178.21` | Torre LAN IP — the address that is **firewall-blocked** on port 11434 |
| `192.168.178.0/24` | Home LAN subnet — explicitly blocked on port 11434 |

No passwords, tokens, keys, or other secrets appear in
this document.

---

# Purpose

Define the security architecture of the Torre RTX node
as it actually exists after RTX-1.5: what it runs, what
it exposes, where its trust boundaries lie, what risks
are accepted versus mitigated, and how it recovers.

This document is the gate that RTX-1.6 depends on: the
node-bridge design rules require a security delta
document for the RTX node before the UM790 `ollama`
endpoint is allowed to point at Torre
([node-bridge §4](../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md)).
This document satisfies that requirement for the
**deployed** node.

It is **not** an apply log. The dated apply logs under
`09_logs/` remain the chronological record and the
evidence trail; this document is the durable, current
description of the security posture they produced.

---

# Scope

**In scope (deployed reality):**

- Torre as an on-demand GPU node serving Ollama.
- The Tailscale-only remote-exposure model (RTX-1.4).
- The host-scoped Windows Firewall policy (RTX-1.4,
  re-validated at RTX-1.5).
- The headless `OllamaService` NSSM service and its
  hardening (RTX-1.5).
- Trust boundaries, attack surface, accepted and
  mitigated risks, recovery, and rollback **for the
  node as deployed**.

**Out of scope (deliberately not described here):**

- **UM790-side (covered elsewhere) —** the UM790 `ollama`
  endpoint swap (RTX-1.6, deployed 2026-06-27): Open WebUI
  and Home Assistant reach Torre via the `ollama-proxy`
  (Torre primary + UM790 fallback). The proxy and consumer
  config are **UM790-side** and live in
  [`security_posture.md`](security_posture.md) and the
  [RTX-1.6 apply log](../09_logs/2026-06-27_phaseRTX1_6_endpoint_swap_applied.md);
  this document stays scoped to the **Torre node** itself.
- **Out of scope —** the future Wyoming / large-Whisper
  audio path on the RTX node anticipated by
  [node-bridge §2/§4](../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md).
  Torre serves the Ollama LLM endpoint only; no voice
  container runs on it.
- **Out of scope —** any change to the UM790,
  Guardian Cloud, Cloudflare, or the live architecture
  document.

---

# Responsibilities of the RTX node

```text
Torre IS:
  • A single-purpose, on-demand GPU compute node.
  • The host of one network service: Ollama (GPU),
    serving qwen2.5:7b-instruct.
  • Provisioned, headless, and Tailscale-reachable.

Torre IS NOT:
  • A 24/7 node. The UM790 remains the always-on node.
  • A host for any always-on AURORA component
    (wake-word, Piper, small Whisper stay on the UM790).
  • A host for any Guardian Cloud surface.
  • A hard production dependency. Since RTX-1.6 the front
    doors prefer Torre via the ollama-proxy, but the
    always-on UM790 CPU fallback means a Torre outage
    degrades performance — it does not break inference.
```

These map to the architectural invariants carried from
[node-bridge §1](../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md)
and the RTX amendment draft: production stays on the
UM790; AI compute can move to dedicated hardware; the
RTX node is opportunistic and nothing that must be
highly available depends on it.

---

# Trust boundaries

```text
        Internet
           │   (FRITZ!Box — NO inbound port-forward to Torre)
           ▼
   ┌───────────────────────────────────────────────┐
   │  Home LAN  192.168.178.0/24                    │
   │                                                │
   │   UM790 (homelab)            Torre (torre)     │
   │   192.168.178.79            192.168.178.21     │
   │        │                         ▲             │
   │        │   LAN → 11434  ✗ BLOCKED │            │
   │        └─────────────────────────┘            │
   └───────────────────────────────────────────────┘
            │                         ▲
            │  Tailscale (WireGuard)  │
            │  100.68.180.69 ────────▶ 100.91.154.124:11434
            │  ALLOWED (/32 only)     │
            ▼                         │
         tailnet ─────────────────────┘
```

Boundary statements (all gate-validated):

1. **The only inbound network path to Torre's Ollama is
   from the UM790, over Tailscale.** Enforced by a
   host-scoped Windows Firewall allow rule (`/32`).
2. **The LAN cannot reach Torre's Ollama.** The bind is
   `0.0.0.0:11434`, but the LAN is explicitly blocked
   (G-1.5-7: LAN probe `192.168.178.21:11434` → curl
   exit 28, silent drop).
3. **There is no public path.** Torre sits behind NAT
   with no port-forward and no Cloudflare tunnel.
4. **Network identity, not service identity, is the
   boundary.** Ollama itself is unauthenticated; the
   boundary is Windows Firewall (host) + Tailscale
   (encrypted transport + tailnet membership).
5. **The service runs as LocalSystem.** The trust placed
   in the on-disk service binary is therefore high; that
   trust is protected by ACL hardening of the NSSM
   binary (see *NSSM service architecture*).

---

# Security model

Torre follows the AMAROLAB practical model — *security
before convenience*, reasonable risk reduction,
recoverability, operational simplicity — applied to a
single-user GPU node:

```text
Access control = Network layer only.

  Windows Firewall (host)
        +
  Tailscale (encrypted transport + tailnet identity)
        +
  Default-deny inbound (Windows) with an explicit
  least-privilege /32 allow and an explicit LAN block.
```

Defence-in-depth, as deployed:

- **Least privilege at the network edge** — exactly one
  remote host (`100.68.180.69/32`) may reach exactly one
  port (TCP 11434).
- **Explicit deny on top of implicit deny** — the LAN is
  blocked by a dedicated Block rule even though the `/32`
  allow already excludes it. In Windows Firewall a Block
  rule wins over an Allow rule, so the LAN stays denied
  even if a broader allow were ever introduced.
- **Host hardening around the privileged service** — the
  NSSM service binary and folder are ACL-locked so the
  LocalSystem service cannot be hijacked by a
  lower-privileged user replacing the binary.
- **Safe teardown** — NSSM's process-tree termination
  prevents orphaned GPU processes and VRAM retention.

The model does **not** rely on Ollama authentication,
TLS termination on Torre, or LAN segmentation — none of
which are deployed. This is acceptable only because of
the load-bearing assumptions listed under *Security
assumptions*.

---

# Access architecture

## Tailscale-only access model

```text
UM790 (homelab) ──WireGuard via Tailscale──▶ Torre (torre)
  100.68.180.69                                100.91.154.124:11434
       (direct path on the shared 192.168.178.0/24 segment)
```

- Torre joins the same single-user tailnet as the UM790
  (node name `torre`). Tailscale provides the encrypted
  transport and the tailnet identity that the firewall
  allow rule is scoped to.
- The UM790 reaches Torre at its Tailscale address only.
  The LAN-direct address is blocked (next section).
- Remote administrative access to the UM790 itself stays
  as documented in
  [`security_posture.md`](security_posture.md)
  (VPN → SSH). This document does not change the UM790
  access model.
- **Design choice (RTX-1.4 D-RTX-1.4-A):** Ollama binds
  `0.0.0.0:11434` rather than a Tailscale-only interface.
  LAN isolation is delegated to the firewall, **not** to
  interface binding. Rationale: the headless service must
  not depend on Tailscale being up before Ollama starts,
  nor on a specific Tailscale interface IP. The
  consequence — the firewall becomes the sole LAN
  isolator — is an accepted risk (see *Accepted risks*).

## Host-scoped (/32) Windows Firewall policy

The access boundary is two inbound rules in the firewall
group **`Amarolab-RTX-1.4`**, on all profiles
(Domain/Private/Public):

| Rule | Action | Dir | Proto/Port | Remote address | Scope |
|---|---|---|---|---|---|
| `Ollama-Tailscale-Only` | **Allow** | Inbound | TCP 11434 | `100.68.180.69/32` (UM790 only) | Any profile |
| `Ollama-Block-LAN` | **Block** | Inbound | TCP 11434 | `192.168.178.0/24` (LAN) | Any profile |

```text
Effective policy on TCP 11434:
  • ALLOW   from 100.68.180.69/32  (UM790 Tailscale IP)
  • BLOCK   from 192.168.178.0/24  (home LAN)
  • DENY    everything else        (Windows default-deny)
```

Key properties (gate-validated):

- **Host-scoped, not range-scoped.** The allow is a
  single `/32` (the UM790), **not** the Tailscale CGNAT
  range `100.64.0.0/10`. This is tighter than a
  tailnet-wide allow: only the UM790 can reach the port,
  not every tailnet node.
- **Re-validated after the service migration.** G-1.5-7
  re-confirmed both halves: UM790 → Tailscale
  `/api/version`, `/api/tags`, `/api/generate` succeed;
  LAN → `192.168.178.21:11434` blocked (curl exit 28).
- **No allow-all rule exists.** RTX-1.4 confirmed there
  was no pre-existing broad Ollama/11434 allow rule to
  remove, and none was created.

> Reconciliation note: an earlier draft of the RTX
> architecture amendment described the target as the
> CGNAT range `100.64.0.0/10`. The **deployed** rule is
> the `/32` host scope above. Reality wins; the draft is
> corrected at merge time (RTX-1.6). See *Documentation
> drift*.

---

# NSSM service architecture (`OllamaService`)

RTX-1.5 migrated Ollama on Torre from the interactive
tray application to a headless Windows service so it
survives logoff and reboot-without-login while keeping
the RTX-1.4 network posture and GPU acceleration.

## Service definition (verified via `nssm get`)

```text
Service name : OllamaService
Wrapper      : NSSM 2.24 (64-bit)  →  C:\Tools\nssm\nssm.exe
Identity     : LocalSystem
Startup      : Automatic
Application  : C:\Users\<USERNAME>\AppData\Local\Programs\Ollama\ollama.exe
Arguments    : serve
Working dir  : C:\Users\<USERNAME>\AppData\Local\Programs\Ollama
Environment  : OLLAMA_HOST=0.0.0.0:11434
               OLLAMA_MODELS=D:\ai\ollama\models
Logs         : D:\ai\ollama\logs\server.log
               D:\ai\ollama\logs\server-err.log
```

Process and restart behaviour (the **actual** NSSM 2.24
configuration, reconciled at closeout — see *Lessons
learned*):

```text
AppExit Default   = Restart        (auto-restart on exit)
AppRestartDelay   = 0              (NSSM default — prompt restart)
AppThrottle       = 1500 ms        (NSSM default fail-fast window)
Process-tree kill = NSSM 2.24 DEFAULT (whole tree killed on stop)
```

- The SCM tracks the **nssm.exe wrapper** PID, which
  launches `ollama.exe serve` as a managed child — the
  expected NSSM architecture, not stale metadata.
- The interactive startup shortcut was disabled
  (renamed `Ollama.lnk.rtx15-disabled`, reversible). No
  HKCU/HKLM Run keys were present. There is exactly one
  listener on `0.0.0.0:11434`; the tray app is not
  running.

## Supply-chain and host hardening (RTX-1.5)

- **NSSM binary integrity.** `C:\Tools\nssm\nssm.exe` is
  NSSM 2.24, verified by SHA256 match to the canonical
  nssm 2.24 win64 binary (full hash recorded in the
  RTX-1.5 apply log). The binary is `NotSigned`
  (expected for the 2.24 release); trust is established
  by hash + official download origin.
- **ACL hardening of the service binary.** On discovery,
  `Authenticated Users` inherited **Modify** on
  `C:\Tools\nssm` — a service-binary-replacement /
  LocalSystem privilege-escalation path. Mitigated:

  ```text
  Inheritance      : removed
  Administrators   : FullControl
  SYSTEM           : FullControl
  Users            : ReadAndExecute
  Authenticated Users : (removed)
  ```

  A pre-change ACL backup was saved for restore
  (`icacls … /restore`).
- **LocalSystem data access** confirmed by read/write
  probe in SYSTEM context: `D:\ai\ollama\models`
  readable, `D:\ai\ollama\logs` writable.
- **Execution policy** does not block service execution
  from `C:\Tools` (SRP not enforcing, no effective
  AppLocker rules, WDAC user-mode CI in audit only).

## Validated service posture (RTX-1.5 gates — all PASS)

| Gate | What it proves |
|---|---|
| G-1.5-1/2/3 | Service Running, Automatic; env present; single listener `0.0.0.0:11434`; no tray; Ollama 0.30.10 |
| G-1.5-4 | GPU: RTX 5070, CUDA0, 29/29 layers, `size_vram == size`, ~111 tok/s; LocalSystem sees the GPU in Session 0 |
| **G-1.5-8** (critical) | Teardown/VRAM: stop / restart / crash → no orphan `llama-server`, VRAM recovered, single instance |
| G-1.5-7 | Firewall re-check: host-scoped `/32` allowlist intact; UM790 reachable, LAN blocked |
| G-1.5-5 | Logoff: serves while signed out; PID continuity (no silent restart) |
| **G-1.5-6** (core) | **Reboot without login: serves over Tailscale before any login; GPU offload restored at cold boot** |
| G-1.5-9 | Restart throttle: NSSM back-off `0 → 2000 → 4000 ms` (event 1034); tree-kill logged (events 1023/1027); clean recovery |
| G-1.5-10 | Production integrity: UM790 endpoint unchanged (`http://ollama:11434`, local Ollama v0.17.7); Torre IP absent from all 16 UM790 containers; stack untouched |

---

# Exposed services

```text
Network-exposed on Torre (by RTX-1.4/1.5 policy):

  TCP 11434  Ollama REST API   bind 0.0.0.0   no auth
             reachable ONLY from 100.68.180.69/32 over Tailscale
             LAN blocked · no public path

Not published to the tailnet by these rules:

  • Operator interactive access (local console) —
    not part of the 11434 serving policy.
  • Tailscale daemon — tailnet control/data plane,
    single-user tailnet.
  • No other AURORA service runs on Torre (no Wyoming,
    no Open WebUI, no Qdrant, no Mosquitto, no
    Cloudflare, no Guardian Cloud).
```

The runtime behind port 11434:

```text
Ollama 0.30.10 (GPU)
Model  : qwen2.5:7b-instruct  (Q4_K_M, 7.6B, ~4.7 GB)
Store  : D:\ai\ollama\models  (NVMe; C: store empty)
GPU    : RTX 5070, 29/29 layers offloaded
VRAM   : ~1.5 GB idle  →  ~6.3 GB warm
Speed  : ~105 tok/s benchmark / ~111 tok/s warm service
         (≈ 17.6× the UM790 CPU baseline)
```

> Note: the UM790 runs its **own** local Ollama
> (v0.17.7, CPU) on `http://ollama:11434` inside Docker.
> That instance is distinct from Torre's and is the one
> listed in
> [`exposed-ports.md`](exposed-ports.md). The two are
> not connected as of this document.

---

# Attack surface

| Entry point | Exposure | Control(s) | Residual |
|---|---|---|---|
| Ollama REST `:11434` | `0.0.0.0` bind, **no auth** | Firewall `/32` allow + LAN block + default-deny; Tailscale identity/encryption | If the firewall is disabled or an allow-all 11434 rule is added, the LAN is re-exposed (unauthenticated) |
| Tailnet reachability | UM790 `/32` only | Single-user tailnet; least-privilege allow | A compromised UM790 or tailnet key could reach `:11434` |
| Public Internet | None expected | NAT + no port-forward + no tunnel on Torre | Formal off-tailnet probe not yet run (G-5 deferred) |
| Service binary (LocalSystem) | On-disk `C:\Tools\nssm` | ACL hardening (no `Authenticated Users`) | Local admin compromise still implies host compromise |
| GPU process lifecycle | `llama-server` children | NSSM default process-tree kill | None observed (no orphans across stop/restart/crash) |

Surface intentionally **absent** on Torre: no public
HTTP surface, no reverse proxy, no database, no message
broker, no production application, no Guardian Cloud.

---

# Security assumptions

These are the load-bearing assumptions. If any breaks,
re-evaluate the posture.

1. **The home router forwards no inbound ports to
   Torre.** The FRITZ!Box does not expose `:11434` (or
   anything else) from the Internet. This is the same
   load-bearing assumption that underpins the UM790
   posture in [`exposed-ports.md`](exposed-ports.md).
2. **Windows Firewall stays enabled with both
   `Amarolab-RTX-1.4` rules intact and host-scoped.**
   The firewall is the sole control isolating `:11434`
   from the LAN.
3. **The tailnet is single-user and trusted.** Tailnet
   membership is the identity the `/32` allow trusts.
4. **Torre runs lean / headless while serving.** GPU
   VRAM headroom is preserved so the model keeps full
   GPU offload (lesson L-RTX-2).
5. **Torre holds no unique critical state.** The model
   is re-pullable; the service is reproducible from the
   recorded NSSM parameters. Torre is rebuildable from
   documentation.

---

# Risk register

## Accepted risks

| ID | Risk | Why accepted | Compensating control |
|---|---|---|---|
| RTX-SEC-1 | **Ollama is unauthenticated** on `:11434`. | Single-user, Tailscale-only posture; consistent with the existing UM790 Ollama posture (R-07). | Network layer is the only access path; `/32` allow + LAN block + default-deny. |
| RTX-SEC-2 | **`0.0.0.0` bind makes the firewall the sole LAN isolator.** | Robust headless-service start (no Tailscale-ordering / interface-IP dependency) — RTX-1.4 D-RTX-1.4-A. | Explicit LAN Block rule (block wins over allow); least-privilege `/32` allow; periodic firewall re-check (recommended). |
| RTX-SEC-3 | **Service runs as LocalSystem** (high privilege). | NSSM service must start at boot without a login. | ACL hardening of the NSSM binary/folder (no `Authenticated Users` modify) closes the binary-replacement escalation path. |
| RTX-SEC-4 | **Always-on listener increases LAN-exposure *duration*** vs the manual tray app. | Headless persistence is the RTX-1.5 objective. | Same firewall scope applies continuously; LAN remains blocked whether or not anyone is logged in (G-1.5-6). |
| RTX-SEC-5 | **No public-exposure probe yet** (G-5 not formally tested). | NAT + no port-forward + no tunnel make a public path not expected. | **Recommendation —** run an off-tailnet probe + a FRITZ!Box port-forward read before RTX-1.6 to confirm formally. |
| RTX-SEC-6 | **LAN / Tailscale IPs are recorded in docs.** | Treated repo-wide as non-secret operational detail; sanitisation is a deferred repo-wide decision (ROADMAP). | No credentials are exposed; addresses already exist in git history; **Recommendation —** include this file in any future repo-wide IP-sanitisation pass. |

## Mitigated risks

| ID | Risk | Mitigation (deployed) | Evidence |
|---|---|---|---|
| RTX-MIT-1 | Orphaned `llama-server` / VRAM retention after a crash. | NSSM 2.24 default process-tree termination kills the whole tree on stop/restart/crash. | G-1.5-8 (critical) PASS; tree-kill logged at G-1.5-9 (events 1023/1027). |
| RTX-MIT-2 | Service-binary replacement → LocalSystem escalation. | ACL hardening: inheritance removed; `Authenticated Users` removed; `Users` = ReadAndExecute. | RTX-1.5 *Security Hardening*. |
| RTX-MIT-3 | Model store landing on the `C:` system drive. | Store moved to `D:\ai\ollama\models`; `OLLAMA_MODELS` set in the **service** environment; C: store empty. | RTX-1.3; G-1.5-2; lesson L-RTX-1. |
| RTX-MIT-4 | VRAM contention crash (GUI apps starving the GPU → CUDA kernel crash, partial offload). | "Run lean / headless while serving" discipline; headless service keeps VRAM free. | L-RTX-2; G-1.5-4 (29/29 offload, `size_vram == size`). |
| RTX-MIT-5 | Loss of serving across logoff / reboot. | Headless NSSM service (LocalSystem, Automatic) survives logoff and reboot-without-login; GPU offload restored at cold boot. | G-1.5-5; **G-1.5-6** (core). |
| RTX-MIT-6 | LAN-direct reach to `:11434`. | Explicit firewall Block on `192.168.178.0/24`; `/32` allow excludes the LAN; Windows default-deny. | RTX-1.4 G-4; G-1.5-7 (curl exit 28). |

---

# Recovery model

```text
Crash of ollama.exe          → NSSM auto-restarts (AppExit=Restart),
                               prompt restart (AppRestartDelay=0),
                               process tree cleaned, VRAM recovered.
Rapid repeated fail-fast      → NSSM backs off 0 → 2000 → 4000 ms
                               (no busy-loop), then stabilises.
User logoff                   → service keeps serving; PID continuity.
Reboot without login          → service serves over Tailscale before
                               any login; GPU offload restored.
Loss of Torre entirely        → inference degrades to the UM790 CPU
                               path via the ollama-proxy fallback;
                               AURORA keeps working (no outage).
```

Rebuild-from-documentation (Torre holds no unique
critical state):

1. Re-pull `qwen2.5:7b-instruct` into
   `D:\ai\ollama\models` (or restore the model store).
2. Re-create `OllamaService` from the recorded NSSM
   parameters (Application / Arguments / Working dir /
   Environment / restart behaviour).
3. Re-apply the `Amarolab-RTX-1.4` firewall group (two
   rules above).
4. Re-validate with the RTX-1.5 gates (local API,
   GPU offload, UM790 Tailscale reach, LAN blocked).

> Torre's recoverability is by **rebuild**, not by
> backup, because it stores no unique critical state
> (the model is re-pullable; the service is reproducible
> from the recorded parameters). The UM790 backup
> posture in
> [`security_posture.md`](security_posture.md) is
> unchanged.

---

# Rollback considerations

Everything RTX-1.4/1.5 introduced is reversible **on
Torre**, with nothing to undo off-box (no data moved,
no UM790 / production / Guardian Cloud change).

**Fast containment** if a LAN or public leak is ever
detected — stop the listener first, then remove the
exposure:

```text
1. Stop all Ollama processes  → kills the 0.0.0.0 listener.
2. Remove-NetFirewallRule -Group "Amarolab-RTX-1.4"
3. Clear Machine-scope OLLAMA_HOST / OLLAMA_MODELS.
   → returns to loopback-only (the RTX-1.3 end state).
```

**Service rollback** (undo RTX-1.5, keep RTX-1.4):

```text
• Remove the OllamaService NSSM service.
• Restore the startup shortcut
  (Ollama.lnk.rtx15-disabled → Ollama.lnk).
• Restore the C:\Tools ACLs from the saved backup
  (icacls … /restore) if needed.
  → returns to the manual tray-app model.
```

**Out of scope —** rollback of the UM790 endpoint swap.
No endpoint change exists to roll back; that is RTX-1.6.

---

# Operational responsibilities

Confirmed operating rules for Torre as deployed:

1. **Keep Torre lean / headless while serving.** Do not
   run VRAM-heavy GUI apps on it during serving
   (L-RTX-2).
2. **Treat the firewall as load-bearing.** It is the
   sole LAN isolator for `:11434`.
   **Recommendation —** periodically verify the firewall
   is enabled and that the `Amarolab-RTX-1.4` group still
   contains exactly the two host-scoped rules (allow
   `100.68.180.69/32`, block `192.168.178.0/24`) and no
   allow-all 11434 rule has appeared.
3. **Keep the NSSM binary/folder ACL-hardened** (no
   `Authenticated Users` modify on `C:\Tools\nssm`).
4. **Keep the model store on `D:`** and confirm the
   service environment carries `OLLAMA_MODELS`.
5. **Validate after any change** with `nssm get` and the
   RTX-1.5 API/GPU/firewall probes — never assume
   configuration from intent (L-RTX-1, L-RTX-3).
6. **Keep Torre single-purpose.** Never host a
   production or Guardian Cloud surface on it.
7. **Preserve production segregation.** Any future
   consumption of Torre by the UM790 is gated on RTX-1.6
   and must not weaken the UM790 posture.

---

# Lessons learned from RTX-1.5

Canonical lessons already recorded in
[`../07_operations/lessons_learned.md`](../07_operations/lessons_learned.md):

- **L-RTX-1** — a process keeps the environment it was
  started with; set `OLLAMA_MODELS` in the **server's
  own** environment and verify on the running process,
  not just the shell.
- **L-RTX-2** — a 12 GB GPU needs VRAM headroom; GUI
  apps can starve the model (2/29 offload + CUDA crash
  vs 29/29 at ~105 tok/s). A dedicated GPU node must run
  lean / headless. This is the security-relevant driver
  behind the headless service (RTX-1.5).

RTX-1.5-specific lessons (**candidate —** flagged for
addition to `lessons_learned.md` at the RTX-1.5
closeout; recorded here because they shaped the deployed
posture):

- **L-RTX-3 (candidate)** — after `nssm install/set`,
  always verify with `nssm get`. An empty PowerShell
  variable silently corrupted `Application` (the service
  stored `Application = "serve"` and never reached the
  Ollama binary). Documented configuration **intent can
  silently never apply**: the phase log's
  `AppRestartDelay=10000` / `AppThrottle=10000` /
  `AppKillProcessTree=1` were **never set** — the
  service ran on NSSM defaults the whole time. Reality
  wins; the configuration was reconciled to the actual
  `nssm get` values at closeout.
- **L-RTX-4 (candidate)** — match validation tooling to
  the installed version. NSSM 2.24 has no `dump`
  (per-parameter `nssm get` was used); the restart
  back-off is `0 → 2000 → 4000 ms` (event 1034); and
  process-tree kill is the **2.24 default** (events
  1023/1027), not a set parameter. The G-1.5-8 no-orphan
  result is therefore attributable to the NSSM default,
  not to a configured `AppKillProcessTree=1`.

Security-relevant takeaway: the protective behaviours
this document relies on (auto-restart, throttle, and
process-tree cleanup) are the **validated NSSM 2.24
defaults**, confirmed empirically — not aspirational
settings. **Recommendation —** if stricter restart
damping is wanted, `AppThrottle=10000` is a deferred,
post-closeout hardening option; it is **not** deployed.

---

# Documentation drift

Findings from checking this document against the source
of truth and the related RTX documents:

1. **Architecture amendment (DRAFT) — firewall scope.**
   [`amarolab_architecture_rtx_amendment_DRAFT.md`](../01_architecture/amarolab_architecture_rtx_amendment_DRAFT.md)
   §4 still frames access control as the CGNAT range
   `100.64.0.0/10` and states "Ollama binds loopback
   only and is not yet remote-reachable" (true at draft
   time, 2026-06-18). **Deployed reality is the
   host-scoped `/32` allow + LAN block, and Ollama is
   remote-reachable from the UM790.** This is a *known,
   already-flagged* reconciliation to apply when the
   draft is merged at RTX-1.6 — not a new defect.
   **Resolved (RTX-1.6, 2026-06-27):** the draft is merged
   into the live architecture doc and marked `MERGED`,
   using the correct `/32` + `ollama-proxy` facts.
2. **`security_posture.md` RTX subsection.** It was dated
   2026-06-17 and predated the RTX node. **Resolved
   (RTX-1.6):** `security_posture.md` now carries the
   RTX node + `ollama-proxy` subsection pointing here.
3. **Node-bridge §4 scope vs deployed scope.**
   [node-bridge §4](../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md)
   anticipated the RTX security delta in terms of the
   **Wyoming / audio** path (HA → STT over Tailscale).
   The node actually brought up the **Ollama LLM**
   endpoint first, so this document covers that. The
   audio-path delta remains future and undeployed — not
   drift, but a scope note worth recording.
4. **No drift against `CURRENT_STATE.md`.** Torre
   addresses, firewall `/32` allow + LAN block, and
   `OllamaService` (LocalSystem, Automatic) all match.
   Since RTX-1.6 (2026-06-27) both documents agree the
   UM790 **now consumes** Torre via the `ollama-proxy`
   (Torre primary + UM790 fallback) — reconciled above.

---

# Cross references

Primary:

- [`security_posture.md`](security_posture.md) — overall
  AMAROLAB security posture (this document is the RTX
  companion; the posture doc's RTX subsection is a
  pending RTX-1.6 item).
- [`../00_overview/CURRENT_STATE.md`](../00_overview/CURRENT_STATE.md)
  — operational source of truth.
- [`../00_overview/ROADMAP.md`](../00_overview/ROADMAP.md)
  — phase plan; RTX-1.6 (endpoint swap) and the
  repo-wide IP-hygiene follow-up.

Supporting evidence (apply logs / specs):

- [`../09_logs/2026-06-19_phaseRTX1_4_remote_exposure.md`](../09_logs/2026-06-19_phaseRTX1_4_remote_exposure.md)
  — RTX-1.4 secure remote exposure.
- [`../09_logs/2026-06-19_phaseRTX1_5_headless_service.md`](../09_logs/2026-06-19_phaseRTX1_5_headless_service.md)
  — RTX-1.5 headless NSSM service.
- [`../09_logs/2026-06-27_rtx1_5_continuation_handoff.md`](../09_logs/2026-06-27_rtx1_5_continuation_handoff.md)
  — RTX-1.5 closeout evidence + configuration
  reconciliation.
- [`../04_ai_system/amarolab-v1/phase-rtx/RTX1_validation_summary.md`](../04_ai_system/amarolab-v1/phase-rtx/RTX1_validation_summary.md)
  — phase-level rollup.
- [`../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md`](../04_ai_system/amarolab-v1/phase-d/06-rtx-node-bridge.md)
  — node design rules / invariants (security delta
  requirement, §4).
- [`../01_architecture/amarolab_architecture_rtx_amendment_DRAFT.md`](../01_architecture/amarolab_architecture_rtx_amendment_DRAFT.md)
  — architecture amendment (DRAFT; merge at RTX-1.6).
- [`../07_operations/lessons_learned.md`](../07_operations/lessons_learned.md)
  — L-RTX-1 / L-RTX-2 (and candidate L-RTX-3 / L-RTX-4).
- [`exposed-ports.md`](exposed-ports.md) — UM790 host
  port snapshot (distinct local Ollama instance).
- [`voice_privacy.md`](voice_privacy.md) — companion
  durable security doc (style reference).
