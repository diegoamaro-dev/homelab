# Phase RTX-1 — Retrospective

- **Phase:** RTX-1 — Torre GPU compute node bring-up and AI endpoint migration.
- **Status:** **CLOSED — 2026-06-27.**
- **Ecosystem:** AMAROLAB — Personal Innovation Lab and Digital Infrastructure Ecosystem.
- **Assistant:** AURORA — the AMAROLAB Personal AI Assistant.
- **Document type:** Permanent retrospective (maintenance reference + professional portfolio). **Not** an implementation log — the chronological evidence lives in the apply logs referenced at the end.

---

## 1. Executive summary

Phase RTX-1 turned a freshly-formatted Windows workstation (**Torre**, RTX 5070,
12 GB VRAM) into an on-demand, GPU-accelerated LLM compute node for AURORA, and
then migrated AURORA's two front doors (Open WebUI chat and Home Assistant voice)
to consume it — **without moving any production service off the always-on UM790
and without ever touching Guardian Cloud**.

The result: `qwen2.5:7b-instruct` runs on Torre's GPU at **~105 tok/s**,
**≈ 17.6×** the ~6 tok/s UM790 CPU baseline. Both front doors now reach it
through a small **`ollama-proxy`** failover front end that prefers Torre when it
is awake and **automatically falls back** to the UM790 CPU when Torre sleeps —
so an on-demand GPU node became a performance upgrade with **no availability
regression**. End-to-end, a Home Assistant conversation dropped from **24.1 s
(CPU) to 3.9 s (GPU)**.

The phase was executed as six gated sub-steps (RTX-1.1 → RTX-1.6), each validated
with real commands, real logs and real state changes before being documented. No
production outage occurred; Guardian Cloud was untouched throughout.

---

## 2. Initial objectives

1. Stand up GPU-accelerated local LLM serving on dedicated hardware.
2. Make it securely reachable by the UM790 — **private network only**, no public
   exposure.
3. Make it survive logoff and reboot **without an interactive login** (a true
   headless service, not a tray app).
4. Let the UM790 front doors consume it **with automatic fallback**, so the
   on-demand node never becomes a hard dependency.
5. Keep everything **simple, recoverable, documented and observable** — and keep
   **production and Guardian Cloud fully segregated**.

---

## 3. Scope

**In scope:** Torre hardware/OS audit; Ollama install and GPU validation; model
storage placement; secure remote exposure; headless persistence; the security
delta document; the UM790 endpoint swap via a failover proxy; and the supporting
documentation.

**Explicitly out of scope (honoured throughout):** no migration of Home
Assistant, Open WebUI, Qdrant, Mosquitto, Zigbee2MQTT, Cloudflare or backups off
the UM790; no Guardian Cloud change; no always-on AURORA component (wake-word,
Piper, small Whisper) moved to Torre; Wake-on-LAN power automation deferred.

---

## 4. Architecture evolution

**Before (single node, all CPU):**

```text
Open WebUI ─┐
            ├─▶ UM790 CPU Ollama ─▶ qwen2.5:7b-instruct  (~6 tok/s)
HA Assist ──┘
```

**After (two nodes, GPU primary + CPU fallback):**

```text
Open WebUI ─┐                    ┌─▶ Torre RTX 5070 GPU  ~105 tok/s  [primary]
            ├─▶ ollama-proxy ────┤
HA Assist ──┘   (nginx failover) └─▶ UM790 CPU Ollama    ~6 tok/s    [fallback]
```

- **UM790** (`homelab`) stays the 24/7 node: Home Assistant, Open WebUI, Qdrant,
  Mosquitto/Z2M, Cloudflare, backups, Guardian Cloud, and its own CPU Ollama
  (now the fallback).
- **Torre** (`torre`) is on-demand GPU compute only — it hosts exactly one
  network service (Ollama) and nothing that must be highly available.
- The **`ollama-proxy`** is the load-bearing new component: one stable internal
  endpoint, Torre primary, UM790 backup, transparent failover for both
  consumers.

---

## 5. Major technical milestones (RTX-1.1 → RTX-1.6)

| Step | Milestone | Outcome |
|---|---|---|
| RTX-1.0 | Read-only post-format audit | Clean baseline; no surprise software on Torre |
| RTX-1.1 | Install Ollama; pre-stage `D:\ai\ollama\models` | Ollama 0.30.10; model store on NVMe `D:` |
| RTX-1.2 | GPU validation | `qwen2.5:7b-instruct` 29/29 layers on GPU; **105.3 tok/s** (3-pass 105.5/105.5/104.9) |
| RTX-1.3 | Storage remediation | Model store corrected `C:` → `D:`; `OLLAMA_MODELS` in the server's own env |
| RTX-1.4 (2026-06-19) | Secure remote exposure | `OLLAMA_HOST=0.0.0.0:11434` + **host-scoped /32** Windows Firewall allowlist; Tailscale-only, LAN blocked, no public path |
| RTX-1.5 (2026-06-27) | Headless persistence | `OllamaService` NSSM service (LocalSystem, Automatic); survives logoff + reboot-without-login; GPU offload restored at cold boot; safe process-tree teardown |
| RTX-1.6 (2026-06-27) | Security doc + endpoint swap | `rtx_node_security.md` + `ollama-proxy` (Torre primary + UM790 fallback); both front doors consuming Torre |

---

## 6. Validation milestones

Every sub-step closed against explicit gates with captured evidence:

- **RTX-1.2** — GPU placement and benchmark: `ollama ps` 100% GPU, 29/29 layers,
  `nvidia-smi` compute process, ~105 tok/s.
- **RTX-1.4 (G-1…G-4)** — local bind on `0.0.0.0:11434`; GPU load; Tailscale
  reachability from the UM790; **LAN-direct blocked** (curl exit 28).
- **RTX-1.5 (G-1.5-1…G-1.5-10)** — service Running/Automatic; single listener;
  GPU 29/29; **teardown/VRAM (critical)** no orphan `llama-server`; firewall
  re-check; logoff with PID continuity; **reboot-without-login (core)** with GPU
  offload restored; restart throttle back-off; production integrity.
- **RTX-1.6 (G-1.6-1…G-1.6-11)** — proxy primary→Torre; **live failover→UM790**;
  Open WebUI + Home Assistant chat through the proxy; tool-calling;
  **101.3 tok/s** end-to-end; full GPU offload (`size_vram == size`); RAG/Qdrant
  intact; voice-pipeline wiring unchanged; 17 containers up; Guardian Cloud
  untouched.

---

## 7. Security improvements

- **Tailscale-only exposure** — Ollama is reachable only over the WireGuard
  tailnet; no LAN reach, no public path (NAT, no port-forward, no tunnel on
  Torre).
- **Host-scoped /32 firewall allowlist** — inbound TCP 11434 allowed from the
  UM790's Tailscale IP **only** (`100.68.180.69/32`), LAN explicitly blocked,
  Windows default-deny underneath. Tighter than a tailnet-wide (`100.64.0.0/10`)
  allow.
- **Headless service hardening** — `OllamaService` runs as LocalSystem; the NSSM
  wrapper binary/folder were **ACL-locked** (removed `Authenticated Users`
  modify), closing a service-binary-replacement → privilege-escalation path. NSSM
  binary integrity pinned by SHA256.
- **Safe teardown** — NSSM process-tree termination prevents orphaned GPU
  processes and VRAM retention on stop/restart/crash.
- **New permanent security document** — `06_security/rtx_node_security.md`
  (trust boundaries, attack surface, accepted/mitigated risks, recovery,
  rollback).
- **Proxy with no new exposure** — `ollama-proxy` publishes on **loopback only**
  for Home Assistant; Open WebUI reaches it over the docker network. No new
  public surface, no new secrets.
- **Production segregation preserved** — Guardian Cloud absent from Torre and
  untouched; the UM790 production stack verified unchanged at every gate.

---

## 8. Documentation improvements

- **New:** `06_security/rtx_node_security.md`; the RTX-1.6 apply log; this
  retrospective; the repo-tracked `03_services/ollama-proxy/` (compose +
  `nginx.conf`), which also addresses R-14 (un-versioned containers) for this
  component.
- **Merged:** the RTX architecture amendment (previously a DRAFT) into the live
  `01_architecture/amarolab_architecture.md` — the two-node model is now
  documented as deployed, with Torre in the hardware inventory and the failover
  inference path drawn out.
- **Updated:** the overview triad (`CURRENT_STATE.md`, `ROADMAP.md`,
  `AMAROLAB_HANDOFF.md`), `06_security/security_posture.md`, and this phase's
  `RTX1_validation_summary.md` — all reconciled to "Phase RTX-1 CLOSED".
- **Governance:** the **Operator Git Approval** rule was added to
  `PROJECT_RULES.md` (and surfaced in the handoff) so future sessions stop for
  explicit approval before `git commit` / `push` / `tag`.

---

## 9. Process improvements

- **Read-only baseline ("Step 0") before every mutation** — each gate began by
  capturing current reality, so changes were made against known state.
- **Gate-based validation with captured evidence** — nothing was marked done
  without a real command, log line, or state transition.
- **Rollback artifacts captured first** — full `docker inspect`, config backups,
  and exact pre-change values recorded before touching production.
- **Reality-wins reconciliation** — where documented intent diverged from the
  running system (e.g., the NSSM restart parameters), the documentation was
  corrected to match reality rather than the reverse.
- **Operator-gated, reversible changes** — production mutations were small,
  validated, and immediately reversible; the failover proxy was proven in
  isolation before any consumer was repointed.

---

## 10. Lessons learned

Canonical (recorded in `07_operations/lessons_learned.md`):

- **L-RTX-1** — a process keeps the environment it was started with. Set
  `OLLAMA_MODELS` in the **server's own** environment and verify it on the
  running process, not just the shell.
- **L-RTX-2** — a 12 GB GPU needs VRAM headroom; GUI apps can starve the model
  (2/29 offload + a CUDA crash vs 29/29 at ~105 tok/s). A dedicated GPU node must
  run **lean / headless**.

Candidate (surfaced this phase; queued for `lessons_learned.md`):

- **L-RTX-3** — after `nssm install/set`, always verify with `nssm get`. An empty
  PowerShell variable silently corrupted the service's `Application`, and
  documented configuration intent (`AppRestartDelay/AppThrottle 10000`) had
  silently **never been applied**.
- **L-RTX-4** — match validation tooling to the installed version: NSSM 2.24 has
  no `dump`, its restart back-off is `0 → 2000 → 4000 ms`, and process-tree kill
  is the **default** (not a set parameter).
- **L-RTX-5** — a Docker **single-file bind mount** does not track host-side
  inode replacement; editing a bind-mounted config on the host and reloading
  serves the **old** file. Config changes require a container **recreate**, not a
  reload. (Same family as L-RTX-1: the running process keeps what it started
  with.)

---

## 11. Problems encountered and how they were solved

| # | Problem | Resolution |
|---|---|---|
| 1 | First model pull landed on `C:` instead of `D:` | Moved the store and restarted Ollama with `OLLAMA_MODELS` in the server env (L-RTX-1) |
| 2 | VRAM contention → 2/29 offload + CUDA crash | "Run lean / headless while serving" discipline; headless service keeps VRAM free (L-RTX-2) |
| 3 | NSSM service stored `Application = "serve"` (empty variable) | Re-set all parameters with literal values; verified via `nssm get` (L-RTX-3) |
| 4 | Documented NSSM restart params never applied | Reconciled docs to the real defaults; validated sufficient by the restart-throttle gate |
| 5 | Open WebUI multi-URL load-balances (no priority); HA integration has no native fallback | Chose a **failover proxy** so both consumers get true Torre-primary + UM790-fallback |
| 6 | Failover test served the old config (bind-mount inode trap) | Force-recreated the proxy so the bind mount re-resolved; re-ran the test correctly (L-RTX-5) |
| 7 | Uncertain whether a bridge container could reach Torre's tailnet IP | Tested first — a bridge container **can** reach it — so a simple bridge proxy sufficed |
| 8 | Home Assistant is host-network, single-endpoint, config in `.storage` | Edited the config entry via a transient `--volumes-from` helper while HA was stopped (no live-overwrite risk) |

---

## 12. Final architecture achieved

```text
            Internet
               │   (FRITZ!Box — no inbound port-forward)
               ▼
      Home LAN 192.168.178.0/24
   ┌───────────────────────────────────────────────┐
   │  UM790 (homelab) — 24/7                         │
   │   Open WebUI ─┐                                 │
   │   HA Assist ──┴─▶ ollama-proxy (nginx)          │
   │                       │                         │
   │            ┌──────────┴───────────┐             │
   │            ▼                      ▼              │
   │   UM790 CPU Ollama        (Tailscale /32)       │
   │   ollama:11434  ◀ fallback     │                │
   └────────────────────────────────┼───────────────┘
                                     ▼
                         Torre (torre) — on-demand
                         RTX 5070 GPU · Ollama 0.30.10
                         100.91.154.124:11434  ◀ primary
                         host-scoped /32 firewall; LAN blocked
```

- Open WebUI → `ollama-proxy:11434` (docker network).
- Home Assistant → `127.0.0.1:11435` (loopback).
- Proxy → Torre primary (~105 tok/s) / UM790 CPU fallback (~6 tok/s).
- Torre security unchanged from RTX-1.4/1.5 (Tailscale-only, /32 firewall,
  headless NSSM service).

---

## 13. Remaining work intentionally deferred to Phase E (and beyond)

None of the following blocked RTX-1 closure; they are deliberate follow-ups:

- **Phase E — Unified Knowledge** (the next phase): add the MyFreeTour
  collection, improve RAG, continuous indexing.
- **Wake-on-LAN** power automation for Torre (owned by Home Assistant) —
  design deferred; not required while Torre is operator-woken.
- **Streaming TTS** in Open WebUI; **STT model-size bump** (`small` /
  `medium-int8`); **system-prompt trim** (cold-cache cost).
- **Candidate lessons L-RTX-3/4/5** → fold into `lessons_learned.md`.
- **Repo-wide IP-hygiene decision** (accept LAN/Tailscale IPs as non-secret, or
  sanitise consistently) — tracked in the ROADMAP.
- **Carried items** independent of RTX-1: R-01 Cloudflare tunnel token rotation
  (Guardian Cloud); `cloudflared-amarolab` standalone apply log; R-D-13 (migrate
  the Open WebUI STT shim off the unmaintained image); optional adoption of
  Open WebUI into a checked-in compose file (R-14).

---

## 14. References to the main documentation

- [`../06_security/rtx_node_security.md`](../06_security/rtx_node_security.md) — RTX node security (permanent).
- [`../04_ai_system/amarolab-v1/phase-rtx/RTX1_validation_summary.md`](../04_ai_system/amarolab-v1/phase-rtx/RTX1_validation_summary.md) — phase validation rollup.
- [`./2026-06-18_phaseRTX1_local_validation.md`](./2026-06-18_phaseRTX1_local_validation.md) — RTX-1.0…1.3 local GPU validation.
- [`./2026-06-19_phaseRTX1_4_remote_exposure.md`](./2026-06-19_phaseRTX1_4_remote_exposure.md) — RTX-1.4 secure remote exposure.
- [`./2026-06-19_phaseRTX1_5_headless_service.md`](./2026-06-19_phaseRTX1_5_headless_service.md) — RTX-1.5 headless NSSM service.
- [`./2026-06-27_phaseRTX1_6_endpoint_swap_applied.md`](./2026-06-27_phaseRTX1_6_endpoint_swap_applied.md) — RTX-1.6 endpoint swap.
- [`../01_architecture/amarolab_architecture.md`](../01_architecture/amarolab_architecture.md) — live architecture (RTX amendment merged).
- [`../06_security/security_posture.md`](../06_security/security_posture.md) · [`../00_overview/CURRENT_STATE.md`](../00_overview/CURRENT_STATE.md) · [`../00_overview/ROADMAP.md`](../00_overview/ROADMAP.md) — posture + overview triad.
- [`../03_services/ollama-proxy/`](../03_services/ollama-proxy/) — proxy compose + nginx config.
- [`../07_operations/lessons_learned.md`](../07_operations/lessons_learned.md) — L-RTX lessons.

---

## 15. Final conclusion

Phase RTX-1 delivered a **17.6× inference speedup** to AURORA's two front doors
by introducing a dedicated GPU compute node, while preserving every property
that makes AMAROLAB maintainable: the 24/7 node and production were never
disrupted, Guardian Cloud was never touched, the new node is private-only and
hardened, and a failover proxy means an on-demand GPU node carries **no
availability cost**. Each step was validated against real evidence and
reconciled into the documentation set.

**Phase RTX-1 is CLOSED.** The next phase is **Phase E — Unified Knowledge.**
