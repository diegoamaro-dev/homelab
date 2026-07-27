# AMAROLAB_HANDOFF
## Mandatory Reading Order

1. AMAROLAB_HANDOFF.md
2. CURRENT_STATE.md
3. ROADMAP.md
4. INITIAL_SYSTEM_STATUS.md (optional historical context)
Last updated: 2026-07-27 (**Voice Lab — Round 1 native TTS casting COMPLETE (repo-external)** — Kokoro `ef_dora` = native TTS reference candidate (~70% blind), Piper still production (no migration), Round 2 designed/not-started, next gate = Aurora voice identity (`09_logs/2026-07-27_voice_lab_round1.md`). Prior — Phase ER-1 — **ER-1.5 reconciliation + closeout: Phase ER-1 COMPLETE**; ER-1.0→ER-1.5 delivered, G-ER-1…7 closed on real evidence; ER-1.4b `ha_call_service` v0.2.0 + ER-1-C1 committed + pushed `5b502c96`; the write path now verifies before claiming success; closeout log `09_logs/2026-07-21_ER1_5_closeout.md`)

## Purpose

This document allows any future AI session to rebuild project context quickly and continue work without relying on conversation history.
This document is intentionally concise.

Detailed operational state lives in CURRENT_STATE.md.
---

## Project

**AMAROLAB** — Personal Innovation Lab and Digital
Infrastructure Ecosystem.

AMAROLAB provides infrastructure, automation,
knowledge systems, AI services and documentation. It
hosts **AURORA** (the personal AI assistant for the
AMAROLAB ecosystem) and independent projects such as
**Guardian Cloud**.

Focus areas:

* Local AI
* Home automation
* Learning infrastructure
* Documentation
* Portfolio development
* Hosting of independent projects (e.g., Guardian Cloud)
* AURORA — the AMAROLAB Personal AI Assistant

---

## Naming

**AMAROLAB**

Personal Innovation Lab and Digital Infrastructure
Ecosystem. Provides infrastructure, automation,
knowledge systems, AI services and documentation.

**AURORA**

Personal AI Assistant for the AMAROLAB ecosystem.

**Guardian Cloud**

Independent project currently hosted on AMAROLAB
infrastructure.

---

## Hardware

### Main Server

* Minisforum UM790 Pro
* AMD Ryzen 9 7940HS
* 32 GB DDR5
* 512 GB SSD
* Linux

### AI Compute Node (Torre) — Phase RTX-1 closed 2026-06-27

* Windows tower + NVIDIA RTX 5070 (12 GB VRAM)
* On-demand GPU compute (not 24/7)
* Runs Ollama as a **headless NSSM service** (LocalSystem,
  Automatic) — Tailscale-only (host-scoped /32 allowlist),
  persists across logoff + reboot-without-login (RTX-1.5).
* **Consumed by the UM790 since RTX-1.6** via the
  `ollama-proxy` (Torre primary + UM790 CPU fallback);
  ~101 tok/s end-to-end.

### Network

* FRITZ!Box 5690 Pro
* LAN connected server
* VPN access

---

## Running Core Services

### AI

* Open WebUI (chat + voice — `https://ai.amarolab.es`)
* Ollama (`qwen2.5:7b-instruct` shared by both front doors)
* Qdrant

### Voice (Phase D-1 — closed 2026-06-18)

Wyoming chain (HA Assist):

* `aurora-whisper` (STT, `base-int8`, D-1.2)
* `aurora-piper` (TTS, `es_ES-davefx-medium`, D-1.3)
* `aurora-wakeword` (`okay_nabu`, D-1.4)

Open WebUI HTTP shims (D-1.7):

* `aurora-whisper-http`
  (`fedirz/faster-whisper-server:0.6.0-rc.3-cpu`)
* `aurora-piper-http`
  (`ghcr.io/matatonic/openedai-speech:0.18.2`,
  voice mapped to `es_ES-sharvard-medium` speaker F)

HA Assist pipeline `AURORA v1` is the default /
preferred pipeline (language `es-ES`); voice surface
is exposed via `https://ha.amarolab.es`.

### Voice Lab — Round 1 (native TTS casting), COMPLETE 2026-07-27

Repo-external (code/models/images/audio **not** committed — evaluation tooling, not production).
Blind comparison of candidate native TTS engines on a fixed Spanish corpus → **Kokoro `ef_dora`
preferred (~70%), ahead of the incumbent Piper**. **Kokoro = native TTS reference candidate;
Piper stays the production voice (no migration).** Round 2 (voice cloning) designed, not started.
**Next gate: define Aurora's synthetic voice identity.**
Record: `09_logs/2026-07-27_voice_lab_round1.md`.

### Home Automation

* Home Assistant (HTTPS via `ha.amarolab.es`;
  reverse-proxy trust patch applied 2026-06-17)
* Mosquitto (authenticated + ACLs, hardened 2026-06-17)
* Zigbee2MQTT

### Infrastructure

* Docker
* PM2
* Cloudflared (**two separate tunnels**: existing
  `cloudflared` for Guardian Cloud; new
  `cloudflared-amarolab` on `ai-local_default` for
  AMAROLAB infrastructure surfaces — `ha.amarolab.es`,
  `ai.amarolab.es`)
* Restic Backups

### Hosted independent project

**Guardian Cloud** — independent project currently
hosted on AMAROLAB infrastructure.

IMPORTANT:

Guardian Cloud is considered production.

Do not modify Guardian Cloud without explicit approval.

---

## Current AI Architecture

Open WebUI (chat + voice)
↓
Ollama (`qwen2.5:7b-instruct`)
↓
Qdrant
↓
RAG Collections

In parallel:

Home Assistant Assist (`AURORA v1`)
↓
HA Ollama integration → same `qwen2.5:7b-instruct`

Collections:

* homelab_docs
* guardian_cloud
* ensambla2
* infra_audits

Future (consumer project — onboards after Phase E Foundation):

* myfreetour

---
## Current Operational Status

The Home Assistant integration is operational.

Validated capabilities:

- ha_get_state
- ha_call_service
- audit logging
- allowlist enforcement
- runtime secret loading
- Zigbee device control
- **voice control** through Aurora v1 Assist pipeline
- **operational awareness** — `system_status` tool + nightly signal
  layer (`aurora-context`), wired to `qwen2.5` (Phase F-2)
- **situational awareness** — Open WebUI `aurora_context` Filter (chat,
  F-3a) + HA voice `input_text.aurora_voice_context` rendered in the Ollama
  voice prompt (F-3b); Aurora reports lab state at conversation start with no
  tool call (Phase F-3)
- **operational memory** — nightly `09_ops/runtime/` digests indexed into the
  dedicated `ops_digests` collection (AD-14), retrievable via `rag_search`
  (Phase F-4; F4.1+F4.2 done + committed 2026-06-30; F4.3 implementation + reconciliation
  complete 2026-06-30 — G-F4-05/06/07 intentionally pending real operational evidence)

Verified device:

`switch.impresora_3d`

Real-world state changes have been executed via:

* Open WebUI chat → `ha_call_service` (2026-06-17, Gate G-5)
* Home Assistant voice → `AURORA v1` pipeline →
  Mosquitto → Z2M → Sonoff S60ZBTPF (2026-06-18, Gate G-D5)

Both paths restore the printer to its `off` baseline
after every gate.

Future assistants should treat Home Assistant tool
integration and the Aurora v1 voice pipeline as
**PRODUCTION READY**.

### Phase D-1 closure (2026-06-18)

Aurora v1 voice pipeline operational on both front
doors:

* `https://ha.amarolab.es` — Home Assistant Assist
  push-to-talk over the Wyoming chain.
* `https://ai.amarolab.es` — Open WebUI browser mic
  over the OpenAI-API-compatible HTTP shims.

All six Phase D-1 gates landed with dated apply logs
(G-D1 through G-D6). Failure-mode rehearsal (G-D6)
confirmed the voice surface fails predictably when
each of its critical dependencies fails (STT, TTS,
LLM). Closeout document:
[`../09_logs/2026-06-18_phaseD1_closeout.md`](../09_logs/2026-06-18_phaseD1_closeout.md).

Voice exposure ACL: exactly one entity exposed —
`input_boolean.aurora_voice_canary`. The printer
(`switch.impresora_3d`) is exposed only for the
duration of a voice gate and reverted to
`should_expose = false` immediately afterwards.

## Documentation Status

Documentation consolidated into:

/home/diego/homelab

Single source of truth.

Audit documentation merged.

Security documentation merged.

AI documentation merged.

Operations documentation merged.

GitHub synchronized.

---

## Security Status

Completed:

* R-04 Mosquitto crash-loop (resolved 2026-06-13)
* R-12 Backups
* Mosquitto authentication hardening (2026-06-17) —
  moved off `allow_anonymous true` to authenticated
  `homeassistant` + `zigbee2mqtt` users with per-user
  ACLs; Gate G-5 re-executed end-to-end through the
  hardened broker. See
  `03_services/zigbee-stack/mosquitto/auth-hardening.md`
  and
  `09_logs/2026-06-17_mosquitto_auth_hardening_applied.md`
* HA reverse-proxy trust (2026-06-17) — `cloudflared-amarolab`
  bridge subnet trusted; LAN intentionally not trusted
  broadly. See
  `09_logs/2026-06-17_phaseD_ha_trusted_proxies_applied.md`
* Voice-exposure default-deny posture (2026-06-17)
  — only `input_boolean.aurora_voice_canary` is
  exposed to voice assistants; `homeassistant.*`,
  `hassio.*`, `recorder.*`, and any Guardian Cloud
  entity are permanent denies. Maintained through
  G-D4 / G-D5 / G-D6.
* Voice failure-mode safety story (2026-06-18, G-D6)
  — Whisper down / Piper down / Ollama unreachable
  scenarios validated; each fails predictably with no
  partial action and baseline restored.

Pending:

* R-01 Cloudflare Tunnel Token Rotation (existing
  Guardian-Cloud tunnel)

---

## Important Rules

* If it's not documented, it doesn't exist.
* Documentation first.
* Sanitize before GitHub.
* Do not expose secrets.
* Guardian Cloud is production.
* **Operator Git Approval** — never run `git commit`,
  `git push` or `git tag` without explicit operator approval
  requested immediately before each command. Approval never
  carries over between commands or sessions. See
  `PROJECT_RULES.md` → "Operator Git Approval".

---

## Current Goal

Build **AURORA v1** — the AMAROLAB Personal AI
Assistant.

Current phase:

**Phase F — Operational Intelligence — IN PROGRESS (F-0/F-1/F-2/F-3
complete; F-3 closed 2026-06-29 (F3.3) — F-3a chat Filter + F-3b voice
awareness; F-4: F4.1+F4.2 done + committed 2026-06-30; F4.3 implementation +
reconciliation complete 2026-06-30 — G-F4-01/02/03/04/09 PASS, G-F4-08 config-verified
(empirical restic pending next backup), G-F4-05/06/07 intentionally pending real
operational evidence; F-4 not fully closed. F-5 Home Intelligence **CLOSED 2026-07-16 (at WM-6)** — F5.1/F5.2 done; **F5.3 (2026-07-01) G-F5-03 PASS, G-F5-04 FAIL (real validation)** → R-F5-A logged; **World Model remedy, closed at WM-6 — G-F5-04 PASS on real evidence (chat + voice); R-F5-A closed** (`09_logs/2026-07-16_WM6_G-F5-04_closeout.md`)). Phase D-1 (Voice) closed 2026-06-18.**

**World Model architecture FROZEN 2026-07-01 (AD-21, `04_ai_system/world_model_architecture.md`) — Aurora's semantic baseline and the R-F5-A remedy. Implementation = Phase WM (WM-1→WM-7); WM-1 `_schema/` foundation committed 2026-07-01 (`6e97c3fb`); WM-2 committed 2026-07-01 (`4c3e2a5d`, pushed); WM-3 loader implemented 2026-07-02 — real-data parity PASS, committed + pushed (`8d653fea`, git gate closed); WM-4 evaluator cutover implemented + validated 2026-07-13 — `_evaluator/` engine live in `bin/aurora-context`, `HOME_RULES` retired, AD-20/INV-18 preserved — committed + pushed (`476e0ae8`); **G-WM4-6 CLOSED 2026-07-14** (first unattended cycle); WM-5 done 2026-07-14 — committed + pushed (`b2b04670`); **WM-6 done 2026-07-16 — G-F5-04 CLOSED, R-F5-A / F-5 CLOSED** (`09_logs/2026-07-16_WM6_G-F5-04_closeout.md`). Hashes are the post-sanitization canonical hashes (history rewritten + republished 2026-07-10; see `09_logs/2026-07-10_repo_history_sanitization_reconciliation.md`).**

Active follow-on: **Phase RTX-1 — Torre GPU node — CLOSED
2026-06-27. RTX-1.4 (Tailscale-only) + RTX-1.5 (headless
NSSM service) + RTX-1.6 (UM790 endpoint swap via the
`ollama-proxy`, Torre primary + UM790 fallback) all
complete. The front doors now consume Torre's GPU
(≈17.6× the UM790 CPU).**

Phase status:

* Phase A — Completed. `qwen2.5:7b-instruct` selected as the
  primary tool-calling model.
* Phase B — Completed. Tool layer delivered:
  `time_now`, `rag_search`, `audit_search`.
* Phase C — Completed (2026-06-17). `ha_get_state` and
  `ha_call_service` installed, attached to qwen2.5, and
  validated end-to-end. Refusal path proven against
  `recorder.purge`; read path proven against `sun.sun`;
  Gate G-5 happy-path write proven against
  `switch.impresora_3d` with full Z2M MQTT round-trip and
  baseline restore.
* **Phase D-1 — Voice — Closed 2026-06-18.**
  * D-1.1 (documentation skeleton) — closed.
  * **D-1.2 (Whisper) — closed 2026-06-17.**
  * **D-1.3 (Piper) — closed 2026-06-17.**
  * **D-1.4 (openWakeWord) — closed 2026-06-17.**
  * **D-1.5 (AURORA v1 pipeline + voice canary +
    exposure lockdown) — closed 2026-06-17.**
  * HA reverse-proxy trust patch — closed 2026-06-17.
  * **G-D4 (canary end-to-end) — PASSED 2026-06-17.**
  * **D-1.6 / G-D5 (real-device voice round-trip on
    `switch.impresora_3d`) — closed / PASSED 2026-06-18.**
  * **D-1.7 (Open WebUI Audio shims + audio surface)
    — closed 2026-06-18.**
  * **D-1.8 / G-D6 (failure-mode rehearsal) —
    closed / PASSED 2026-06-18.**
  * **D-1.9 (Phase D-1 closeout) — closed 2026-06-18.**

Closeout document:
[`../09_logs/2026-06-18_phaseD1_closeout.md`](../09_logs/2026-06-18_phaseD1_closeout.md).

---

## Next Immediate Task

**Current: Phase ER-1 — Deterministic Entity Resolution — design FROZEN 2026-07-16
(operator-ratified), now Revision 4. Published:** defect record `c147e632` → architecture
freeze `38eb8262` → **Revision 2 amendment** `3ebf59d1` (D-ER-11 aliases mirror the `binding`
shape; D-ER-12 an alias may equal its own entity identifier, never another's) → **ER-1.1**
`f983a04f` (additive `aliases` contract + the six bound entities' alias sets) → **ER-1.2**
`b0fded73` (loader: D-ER-8 normalization, fail-loud check 12, the additive `resolution`
registry — 33 aliases → 8 targets; `LOADER_VERSION` 0.2.0, **`ARTIFACT_VERSION` still 1**).
**G-ER-1 CLOSED · G-ER-2 loader half PASS · G-ER-5 CLOSED 2026-07-17** — the first unattended
04:15 cycle after the artifact regeneration consumed the 0.2.0 artifact and produced awareness
**byte-equivalent to baseline**; Home State `Degraded`, never `Unavailable`; zero
`ArtifactError`. **ER-1.3 (projection emitter + `aurora-entities.json`) implemented + validated
2026-07-17** — consumer-side `bin/emit-entity-projection` (emit + the canonical `--check`
freshness mechanism) derives the gitignored projection (33 aliases → 8 targets; `resolution`
verbatim + provenance; reaches the ER-1.4 resolver through the read-only `/opt/aurora` mount);
**D-ER-13 ratified — freeze Revision 3** (an aliased signal must bind `ha_entity`, check 12a;
ratifies F-ER12-1) with **no behaviour change** (unreachable on the real tree; `resolution` hash
unmoved); **G-ER-6 producer half CLOSED**, consumer half open (ER-1.4); **G-ER-1 untouched — its
closure stands, gate history is not rewritten**; 43 loader + 36 evaluator green;
**`LOADER_VERSION` → 0.2.1** (patch — validation contract only; the live artifact keeps
`loader_version` 0.2.0, the version that generated it — ER-1.3 does not regenerate). New
permanent rule: `PROJECT_RULES.md` → **Content Provenance over Repository Chronology**.
**ER-1.3 committed + pushed (`ed7a149c`).**

**ER-1.4a — the first cutover — implemented + validated 2026-07-17** (log
`09_logs/2026-07-17_ER1_4a_ha_get_state_applied.md`; committed `3ad8779f`). **`ha_get_state`
is v0.2.1 in `webui.db` (0.2.0 at ER-1.4a; 0.2.1 = the Rev 4 D-ER-14 audit-field rename,
behaviour unchanged); the read path now resolves natural language** (`toldo` → `cover.toldo`,
`impresora 3d` → `switch.impresora_3d`, `Conexión a Internet` →
`binary_sensor.rooter_estado_wan`) via the new inline-only
`ai-stack/openwebui-tools/lib/entity_resolver.py`. **G-ER-7 read half PASS** (a canonical
`entity_id` is byte-identical to v0.1.0 — paired A/B run, volatility controlled) · **G-ER-6
consumer half PASS on the read side** (a broken projection leaves direct ids working exactly
as today; alias → `resolver_unavailable`). Root cause #2 fixed (the misleading `light.kitchen`
docstring examples). `bin/install_tool` now resolves multiple `# @@AMAROLAB_INLINE:<name>@@`
markers; `lib/audit_helper.py` gained an additive `extra` (spec §10 inventory corrected — an
implementation-inventory correction, **not** an architectural decision).

**Phase ER-1 — Deterministic Entity Resolution — COMPLETE at ER-1.5 (2026-07-21;** closeout
`09_logs/2026-07-21_ER1_5_closeout.md`). ER-1.0→ER-1.5 delivered; G-ER-1…7 closed on real
evidence; the triad carries no false ER-1 transient status. **ER-1.4b — `ha_call_service`
v0.2.0 (resolution + ER-1-C1, Rule B / 500 ms) — implemented + validated 2026-07-20, committed +
pushed `5b502c96`** (`09_logs/2026-07-20_ER1_4b_ha_call_service_applied.md`): the write path now
verifies before it claims success. G-ER-2/3a/3b/4 + G-ER-7 write half + G-ER-6 consumer half
(write side) all PASS; v0.2.0 installed to `webui.db` (attached to `qwen2.5`). **This was where
ER-1 changed reality.**
**F-ER14-1 is resolved — D-ER-14, freeze Revision 4 (ratified + applied 2026-07-17):** the
audit observability field is **`registry_target`** (`ha_get_state` → v0.2.1; zero real audit
lines ever carried `modelled`; behaviour proven byte-identical over the 18-case corpus —
`09_logs/2026-07-17_ER1_freeze_rev4.md`). **The ER-1.4b C1 measurement protocol is
PRE-REGISTERED** (`09_logs/2026-07-17_ER1_4b_c1_measurement_protocol.md`): 20 samples on
`switch.impresora_3d`, decision rules A (immediate read: 20/20 first-read hits) / B (bounded
retry: any miss with max visibility ≤ 2 s; budget formula fixed in advance) / C (escalate:
> 2 s or non-observation) — the mechanism is chosen by these predefined criteria, never from
the observed outcome. The protocol was executed as ER-1.4b Step 2, before implementing C1 (→ Rule B / 500 ms).
Logs:
[`../09_logs/2026-07-16_ER1_freeze_rev2.md`](../09_logs/2026-07-16_ER1_freeze_rev2.md) ·
[`../09_logs/2026-07-16_ER1_1_aliases_applied.md`](../09_logs/2026-07-16_ER1_1_aliases_applied.md) ·
[`../09_logs/2026-07-16_ER1_2_loader_applied.md`](../09_logs/2026-07-16_ER1_2_loader_applied.md) ·
[`../09_logs/2026-07-17_ER1_2_G-ER-5_operational_closeout.md`](../09_logs/2026-07-17_ER1_2_G-ER-5_operational_closeout.md) ·
[`../09_logs/2026-07-17_ER1_3_projection_applied.md`](../09_logs/2026-07-17_ER1_3_projection_applied.md) ·
[`../09_logs/2026-07-17_ER1_4a_ha_get_state_applied.md`](../09_logs/2026-07-17_ER1_4a_ha_get_state_applied.md) ·
[`../09_logs/2026-07-17_ER1_freeze_rev4.md`](../09_logs/2026-07-17_ER1_freeze_rev4.md) ·
[`../09_logs/2026-07-17_ER1_4b_c1_measurement_protocol.md`](../09_logs/2026-07-17_ER1_4b_c1_measurement_protocol.md).

**Aurora's read path changed at ER-1.4a; the write path changed at ER-1.4b (2026-07-20).**
`ha_get_state` is v0.2.1 and `ha_call_service` is now **v0.2.0** — both resolve natural
language, and `ha_call_service` runs ER-1-C1: **a write is claimed successful only when the
resulting HA state is verified** (Rule B: check immediately, then poll 100 ms within a 500 ms
budget), else honest `applied_unverified`. The 13 historical unverified writes across 7
non-existent ids can no longer be reported as successful (proven by G-ER-3b).

ER-1 closes the natural-language → `entity_id` gap **and** makes writes honest. Real audit
evidence: **13 unverified writes across 7 non-existent entity ids were reported as
successful** (`result_code:"ok"`; all 7 re-probed 2026-07-16 → HTTP 404). The read path is
**not** defective (`ha_get_state` already answers `not_found`), so reads cut over before
writes. ER-1 **amends no frozen decision** — AD-21 §7 already anticipates the entity registry;
ER-1 implements it. **Independent of Phase WM; not WM-5.5.** Decisions of record: **D-ER-9**
(no write-surface restriction — a valid `entity_id` follows the current path exactly as
today; **D-12 stays the sole authorization authority**; anything stronger is a future
architectural decision), **ER-1-C1** (mandatory after-only write verification — never claim
success unless the resulting HA state was verified; *when* a POST is issued does not change),
**D-ER-10** (closed expected-state map `turn_on→on` / `turn_off→off` / `open_cover→open` /
`close_cover→closed`; all other services → `applied_unverified`), **D-ER-7**
(`ARTIFACT_VERSION` stays 1 — a bump would silently degrade home awareness instead of failing
loud). Gates G-ER-1…7; **G-ER-3b**: historical unverified writes must never again be reported
as successful. Spec:
[`../04_ai_system/entity_resolution_layer.md`](../04_ai_system/entity_resolution_layer.md);
freeze log: [`../09_logs/2026-07-16_ER1_freeze.md`](../09_logs/2026-07-16_ER1_freeze.md);
roadmap: [`ROADMAP.md`](ROADMAP.md) → Phase ER-1.

**Prior: World Model architecture FROZEN 2026-07-01 (AD-21).** **Phase WM-1**
(`_schema/` foundation) **committed 2026-07-01** (`6e97c3fb`; apply log
`09_logs/2026-07-01_WM1_schema_foundation_applied.md`). **Phase WM-2** (migrate
`home_model.md` → 9 literate `home/`+`environment/` entities + `_schema/collectors.md`,
closing F-WM1-a; 1:1, no new facts) **committed 2026-07-01** (`4c3e2a5d`, pushed; apply log
`09_logs/2026-07-01_WM2_home_entities_applied.md`; G-WM2-1…10 pass). **Phase WM-3**
(loader/compiler `Parse → Resolve → Normalize → Validate → Emit` under `_loader/` + gitignored
`world_model.generated.json`; backend-agnostic AST INV-WM3-A) is **implemented 2026-07-02** —
real-data parity with `HOME_RULES` **PASS** (engine-equivalence 32/32 + live `/api/states` match;
apply log `09_logs/2026-07-02_WM3_loader_applied.md`) — **committed + pushed (`8d653fea`); the WM-3 git gate is closed**.
**Phase WM-4** (evaluator cutover) is **implemented + validated 2026-07-13** — the dedicated
`world_model/_evaluator/` engine (loader compiles / evaluator evaluates) consumes the compiled
artifact; `bin/aurora-context` renders home awareness from it (INV-19); **`HOME_RULES` + the
WM-3 parity harness retired** (32 snapshots → `_evaluator/tests/` regression suite);
`home_model.md` → redirect; `aurora-context.json` schema preserved (AD-20/INV-18);
`overall_status` platform-only until WM-5. **G-WM4-1…6 PASS — G-WM4-6 (first unattended
04:15+04:25 nightly cycle) closed 2026-07-14 on real evidence; WM-4 committed + pushed
(`476e0ae8`), complete** (apply log
`09_logs/2026-07-13_WM4_evaluator_cutover_applied.md`). **Phase WM-5** (consumer convergence)
is **implemented + validated 2026-07-14** — the §1.5 aggregate verdict lives in `_evaluator/`
(`evaluate_world` / `aggregate_verdict`; AD-WM5-1 unknown precedence); additive
`world.verdict` / `world.regions` (`home.anomalies` unchanged — AD-20/INV-18); home-aware
`system_status` v0.3.0 (**installed to `webui.db` + verified on the running assistant
2026-07-14** — G-WM5-3) + home-aware voice line (W-10 cap);
G-WM5-1…5 real-data PASS — **committed + pushed (`b2b04670`)** (apply log
`09_logs/2026-07-14_WM5_consumer_convergence_applied.md`). **WM-6 (reopen & close G-F5-04) is DONE 2026-07-16 — G-F5-04 CLOSED, PASS on real
evidence (chat @ ai.amarolab.es + voice @ ha.amarolab.es/AURORA v1); R-F5-A CLOSED; F-5 CLOSED**
(apply log `09_logs/2026-07-16_WM6_G-F5-04_closeout.md`; Run 1 aborted — wrong endpoint (HA Assist) —
then corrected; findings F-LOCALE/F-VOICE-CONTRADICT/F-PLANT-FLAP/F-ASSIST-BLIND recorded). Next:
WM-7+ (extend regions) and the recorded findings.
Freeze doc: `04_ai_system/world_model_architecture.md`; roadmap: `ROADMAP.md` → Phase WM.

Phase D-1 closed; **Phase RTX-1 closed 2026-06-27 —
RTX-1.4 + RTX-1.5 + RTX-1.6 all complete.** The UM790 front
doors consume Torre's GPU via the `ollama-proxy` (Torre
primary + UM790 fallback). **Phase E — Knowledge Platform
Foundation — CLOSED 2026-06-28.** All steps complete: E-0
(audit), E-1 (doc reconciliation), E-2 (fail-loud sync +
run-lock), E-3 (unified health.json), E-4 (log rotation +
backup-consistency decision), E-5 (drift measurement + restore
drill + audit-log check), E-6 (onboarding framework proven
end-to-end). All 13 E-0 findings resolved or accepted. Platform
health `overall_status=ok`. **Current phase: Phase F — Operational Intelligence — IN PROGRESS.**
F-0, F-1, F-2 and **F-3 (Situational Awareness) COMPLETE — F-3 closed
2026-06-29 (F3.3).** F-3a: the `aurora_context` Open WebUI Filter (active+global)
injects `aurora-context.md` on message 1 (G-F3-1…7). F-3b: the HA helper
`input_text.aurora_voice_context` + Jinja2 in the Ollama voice prompt +
04:20 `push-voice-context` give the voice surface the same nightly context
(G-F3-8). **F-4 — Operational Digest + Memory Corpus: F4.1 (substrate) + F4.2 (generator)
DONE + committed 2026-06-30; F4.3 implementation + doc reconciliation complete
2026-06-30** — the unattended 04:25 digest verified, `ops_digests` retrieves the
real 2026-06-29 digest top-1 (0.87), `generated_at` fidelity fix applied (AD-15).
G-F4-01/02/03/04/09 PASS; G-F4-08 config verified (empirical restic pending the next
backup); G-F4-05/06/07 **intentionally pending real operational evidence** (no synthetic
digests / fabricated degraded nights — operator decision). F-4 is not fully complete or
fully validated. F-4 closeout:
`09_logs/2026-06-30_phaseF_F4_3_closeout.md`.
F-3 closeout: `09_logs/2026-06-29_phaseF_F3_closeout.md`; F-2 closeout:
`09_logs/2026-06-29_phaseF_F2_9_closeout.md`. Architecture document:
[`04_ai_system/phase_f_architecture.md`](../04_ai_system/phase_f_architecture.md).
F-0 audit report:
[`../09_logs/2026-06-28_phaseF_F0_audit_report.md`](../09_logs/2026-06-28_phaseF_F0_audit_report.md).
Phase E closeout — E-0 report:
[`../09_logs/2026-06-27_phaseE_E0_operational_audit_report.md`](../09_logs/2026-06-27_phaseE_E0_operational_audit_report.md).

The overview triad, `06_security/rtx_node_security.md`,
`06_security/security_posture.md`, and the live architecture
doc (`01_architecture/amarolab_architecture.md`, RTX
amendment merged) all reflect RTX-1.6. Apply log:
[`../09_logs/2026-06-27_phaseRTX1_6_endpoint_swap_applied.md`](../09_logs/2026-06-27_phaseRTX1_6_endpoint_swap_applied.md).

Pending post-D-1 follow-ups (tracked in
[`CURRENT_STATE.md`](CURRENT_STATE.md) and the closeout
document — none of these are mandatory next steps):

* `cloudflared-amarolab` standalone apply log.
* DNS / Cloudflare architecture doc amendments to
  record the separate-tunnel decision and the
  `ai.amarolab.es` binding.
* ~~**RTX-1.6** — UM790 `ollama` endpoint swap~~ **DONE
  (2026-06-27)** via the `ollama-proxy` (Torre primary +
  UM790 fallback). Apply log:
  [`../09_logs/2026-06-27_phaseRTX1_6_endpoint_swap_applied.md`](../09_logs/2026-06-27_phaseRTX1_6_endpoint_swap_applied.md).
* STT model-size bump candidate (`small` or
  `medium-int8`).
* Streaming TTS in Open WebUI.
* System-prompt trim (3 342 chars → cold-cache cost).
* R-01 Cloudflare Tunnel token rotation (Guardian
  Cloud tunnel).

Pre-Phase-E blockers: **none open.**
