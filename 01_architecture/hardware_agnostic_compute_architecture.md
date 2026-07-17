# Hardware-Agnostic Compute Architecture

- **Status:** **PERMANENT — architectural principle.** Directed by the operator 2026-07-17.
  This document defines a standing constraint on all future AMAROLAB work. It is not a
  phase, not a backlog item, and not a work order.
- **Scope:** how AURORA obtains compute. It governs the relationship between Aurora and the
  machines that run it — nothing else.
- **Introduces no change:** this document adds **no** runtime, tool, prompt, container,
  schema, collection or DB change. It constrains future work; it does not perform any.
- **Sources of record:**
  [`amarolab_architecture.md`](amarolab_architecture.md) (deployed two-node model, RTX-1.6) ·
  [`../04_ai_system/AURORA_VISION.md`](../04_ai_system/AURORA_VISION.md) (§7 boundaries, §8
  governing principles, §9 direction) ·
  [`../04_ai_system/phase_f_architecture.md`](../04_ai_system/phase_f_architecture.md) (AD-01) ·
  [`../04_ai_system/world_model_architecture.md`](../04_ai_system/world_model_architecture.md)
  (AD-21, FROZEN) · [`../03_services/ollama-proxy/`](../03_services/ollama-proxy/) (the
  deployed instance of this principle) ·
  [`../00_overview/PROJECT_RULES.md`](../00_overview/PROJECT_RULES.md) → *Hardware-Agnostic
  Platform* (the rule this document justifies).
- **Governing rule:** *Reality always wins.* Hardware is the most volatile layer AMAROLAB
  has. Aurora is the least volatile thing built on it. The architecture must reflect that
  ordering, not fight it.

---

## 1. The principle

### 1.1 Statement

```text
Aurora must never depend on specific hardware.
Aurora depends on capabilities.
Hardware provides capabilities.
```

A **capability** is something Aurora needs done — *generate a reply*, *transcribe speech*,
*embed a document*. A **provider** is a thing that does it. Aurora names the first and must
never name the second.

The operational form of the principle:

> **Aurora must never require changes because hardware changes.**
> New infrastructure extends Aurora by **registering a capability provider**, never by
> **modifying Aurora**.

**Scope — ratified by the operator, 2026-07-17:**

> **This principle is about hardware independence, not trust-boundary independence.**

The two are separate axes, and this document moves exactly one of them. **Compute providers
may evolve freely; they must remain inside the AMAROLAB trust boundary.** Aurora is
**local-first**, and this principle does not touch that: *"Everything local. No external LLM
calls."* remains a non-negotiable constraint
([`../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md`](../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md)
→ *Constraints (non-negotiable)*).

**Inside the boundary** — operator-controlled nodes, whether on the LAN or reached over the
AMAROLAB private network (VPN / Tailscale):

```text
UM790 · RTX workstation · NAS AI nodes · Jetson devices · Ryzen AI systems ·
Apple Silicon · future NPUs · operator-controlled remote nodes (VPN / Tailscale)
```

**Outside the boundary — excluded from this principle:** third-party cloud inference
providers. Not because they are *hardware* the principle failed to anticipate, but because
they are **not a hardware question at all** (§12, R-1).

**Changing the trust boundary is a separate architectural decision and is out of scope
here.** It is not blocked by this document, and it is not enabled by it. It would require its
own gated, operator-ratified decision — this principle must never be cited as its
justification.

### 1.2 The sharp line

This is the distinction that makes the principle testable rather than decorative:

| Change | Does Aurora change? |
|---|---|
| **New hardware** for a capability Aurora already has | **No.** Register a provider; adjust selection policy. Zero Aurora change. |
| **New capability** Aurora does not have | **Yes** — and legitimately so. New capability means new tools, prompts, contracts. |
| **Hardware retired / unavailable** | **No.** Selection falls back or fails loud. Zero Aurora change. |
| **Fidelity tier change** (a materially better/worse model) | **Yes, deliberately** — an operator decision on measured evidence (§4.4). Never an automatic consequence of hardware. |

If a proposed hardware change forces an edit to a tool, a prompt, the World Model, or a
schema, **the architecture is wrong, not the hardware**. That edit is the defect signal.

### 1.3 Aurora's stable layer

The following must contain **no** hardware identity — no hostname, no IP, no GPU vendor, no
accelerator name, no machine nickname:

```text
Tools           (webui.db + openwebui-tools/)
Prompts         (params.system, the HA voice prompt)
World Model     (world_model/ — entities, baselines, bindings)
Awareness       (aurora-context.*)
Knowledge       (Qdrant corpora)
```

Hardware identity is legitimate in exactly two places: the **provider registry / selection
layer** (whose entire job is to know) and **documentation** (whose job is to describe).

---

## 2. Motivation

### 2.1 The problem

AMAROLAB's hardware is not stable and never will be. Over one month it went from a single
CPU box to a two-node model with a GPU workstation; a dedicated NAS is a known pending
purchase ([`../00_overview/CURRENT_STATE.md`](../00_overview/CURRENT_STATE.md) → *Known
pending items*); the main server carries an unused on-package NPU; and the accelerator
market changes faster than Aurora's design does.

Aurora is meant to last. Its tools, prompts, World Model and knowledge base are the
accumulated, validated product of Phases A→WM. If each hardware change forced a change to
that layer, then the most durable asset in AMAROLAB would be continuously destabilised by
its most volatile one — and every upgrade would carry the risk of regressing behaviour that
took real gates and real evidence to establish.

The inversion this principle enforces: **hardware serves Aurora; Aurora does not track
hardware.**

### 2.2 This is not aspirational — it is measured

RTX-1.6 (2026-06-27) already ran this experiment on real infrastructure:

| | Before RTX-1.6 | After RTX-1.6 |
|---|---|---|
| LLM inference | UM790 CPU, ~6 tok/s | Torre RTX 5070, **~101 tok/s end-to-end through the proxy** |
| HA conversation latency | 24.1 s | 3.9 s |
| Aurora tools changed | — | **none** |
| Aurora prompts changed | — | **none** |
| Aurora model entry changed | — | **none** |
| What actually changed | — | **the endpoint target only** |

A **≈17.6×** compute change (105.3 tok/s on Torre vs the ~6 tok/s UM790 baseline) reached
Aurora as a **configuration change**, validated by eleven gates (G-1.6-1…G-1.6-11, including
live fallback and production integrity). No service moved to Torre. The UM790 remained the
24/7 node and the always-on fallback.

That is the whole principle, already deployed, already validated on real evidence. This
document does not propose it — it **names what RTX-1.6 proved** and makes it binding, so the
next hardware change is required to be as cheap as that one was.

### 2.3 The pattern already exists in AMAROLAB

This principle is the third application of one architectural instinct — *the stable layer
must never name the volatile layer*:

| Existing decision | Stable layer | Must not name |
|---|---|---|
| **AD-01** — awareness is a platform capability, not a UI plugin | the awareness artifact | the **interface** (Open WebUI) |
| **Domain-based prompt routing** (AURORA_FOUNDATION) | the system prompt | the **corpus layout** (collection names) |
| **This decision** | Aurora's tools / prompts / model | the **hardware** |

AD-01 reached its conclusion by asking: *"if Open WebUI is replaced … does the architecture
serve them without re-implementation?"* This document asks the identical question at the
opposite end of the pipeline: **if Torre is replaced, does Aurora need re-implementation?**
AD-01 decoupled Aurora from its **consumers**. This decouples Aurora from its **providers**.

---

## 3. Design goals

1. **Zero-touch hardware evolution.** Adding, replacing or retiring a compute node requires
   no change to any tool, prompt, or model artifact.
2. **Semantic stability across providers.** Where Aurora runs must never change what Aurora
   means (§4.3). This is the safety goal, and it outranks performance.
3. **Availability floor.** A capability Aurora depends on must always have a reachable
   provider, or fail loud. Aurora never becomes unusable because one machine is asleep.
4. **Graceful, disclosed degradation.** Slower is acceptable. Silently different is not.
5. **Additive extension.** New hardware is registered, never integrated.
6. **Trust boundary preserved.** Hardware-agnostic must never become a loophole around
   *"everything local"* (§1.1, §12 R-1). **Providers evolve; the boundary does not.** This is
   a hard boundary, not a trade-off.
7. **Proportionality.** The principle is permanent; the machinery implementing it stays
   sized to the real provider count (§14).

---

## 4. Capability-based architecture

### 4.1 The capability contract

A capability is defined by what Aurora needs, expressed so that a provider can be judged
against it:

| Field | Meaning | Why it exists |
|---|---|---|
| **Capability** | what is being asked for (`llm.chat`, `stt.transcribe`) | the name Aurora uses |
| **Interface** | the wire contract (Ollama API, Wyoming, OpenAI-compatible HTTP) | makes providers pluggable |
| **Semantic identity** | the model + version + quantization that defines the *meaning* of the output | makes providers **substitutable** (§4.3) |
| **Fidelity tier** | the quality class the contract promises | separates *degradation* from *change* |
| **Availability class** | always-on · on-demand · best-effort | sets what may depend on it |
| **Trust boundary** | inside AMAROLAB: local, or operator-controlled via VPN / Tailscale — **never third-party** | enforces the hard boundary (§1.1) |

The critical field is **semantic identity**. A contract that pins only the *interface*
guarantees a provider will answer; it does not guarantee the answer means the same thing.

### 4.2 Aurora's capabilities today

Deployed reality, stated honestly — most capabilities have exactly one provider and no
abstraction at all:

| Capability | Provider(s) today | Abstraction | Availability |
|---|---|---|---|
| `llm.chat` | Torre GPU **+** UM790 CPU | **`ollama-proxy`** | always-on (via fallback) |
| `stt.transcribe` | UM790 (`aurora-whisper`, `aurora-whisper-http`) | none — pinned | always-on |
| `tts.synthesize` | UM790 (`aurora-piper`, `aurora-piper-http`) | none — pinned | always-on |
| `wake.detect` | UM790 (`aurora-wakeword`) | none — pinned | always-on |
| `embed.text` | UM790 (`multilingual-e5-small`, in `ingest`) | none — pinned | always-on |
| `rerank.text` | UM790 (`bge-reranker-v2-m3`, in `ingest`) | none — pinned | always-on |
| `vector.search` | UM790 (Qdrant) | none — pinned | always-on |

**Exactly one capability is abstracted today.** The other six are single-provider and
hardware-pinned. That is **not a violation** — a capability with one provider needs no
selection layer, and building one now would be overengineering (§14). It is stated here so
that no reader mistakes this document for a description of a general capability layer that
does not exist.

### 4.3 Semantic equivalence — the safety property

> Providers may differ in **speed, availability and cost**.
> They must never differ in **meaning** — and never in **trust** (§1.1).

This is why the deployed fallback is safe. Torre and the UM790 both serve
**`qwen2.5:7b-instruct`** — the same weights, the same quantization (D-01). When the proxy
fails over, Aurora gets the same brain, 17.6× slower. Nothing Aurora believes, says, or
decides changes.

Had the fallback served a *different* model, the proxy would be silently swapping Aurora's
reasoning mid-conversation on a network timeout — an invisible behaviour change triggered by
an unrelated event. That is not a fallback; it is a fault injected by the very layer meant to
provide resilience.

**Two providers are interchangeable only if their outputs are equivalent for Aurora's
purpose.** Equivalence is a claim about semantics that must be **established before
registration** (§8) — never assumed from the fact that both speak the same API.

This is the direct application of *Honest under uncertainty* (Vision §8): *"graceful
degradation means saying less, not guessing more."* A silent semantic swap is the system
guessing on Aurora's behalf.

### 4.4 Tiers: degradation vs. change

| | Same semantic identity | Different semantic identity |
|---|---|---|
| **Faster / slower** | **Degradation or improvement** — automatic, in-tier. Torre ⇄ UM790. | **Tier change** — operator decision. |
| **Better / worse output** | not possible by definition | **Tier change** — operator decision. |

- **In-tier movement is automatic.** Selection may freely prefer the fastest available
  equivalent provider. This is what "automatic evolution" means (§6.3).
- **Tier changes are never automatic.** Whisper `base-int8` → `medium` produces *different
  transcripts*. That is a deliberate quality decision, taken on measured evidence, never a
  side-effect of a machine appearing on the tailnet.

The Vision already sets this bar for exactly this case: a better model comes *"when the
hardware justifies it **and a real quality gap has been measured**"* (§9). Hardware may
**enable** a tier change. It may never **cause** one.

---

## 5. Compute provider abstraction

### 5.1 What a provider is

A provider is any addressable thing that satisfies a capability contract. It is **not**
necessarily a machine: a container on the UM790, a GPU box on the tailnet, an NPU on the
main server's own die, and a future accelerator are all just providers. **The unit of
abstraction is the capability, not the box.** One machine may provide many capabilities; one
capability may have many providers across many machines.

### 5.2 Provider attributes

A registered provider declares what it is, so selection can be a policy over facts:

```text
provider:
  capability          which contract it satisfies
  semantic identity   which model/version it actually serves   ← equivalence claim
  endpoint            where it is                              ← the only hardware fact
  fidelity tier       which quality class it belongs to
  availability        always-on | on-demand | best-effort
  trust boundary      inside AMAROLAB (local | operator-controlled via VPN/Tailscale)
  performance         measured, not claimed
```

The endpoint is the **only** place a hardware fact legitimately lives.

### 5.3 Obligations of the abstraction

An abstraction that hides which machine served a request must not hide **that** the answer
came from a degraded path. Aurora *does not pretend* (Vision §7) — and neither may the layer
beneath it. Any provider abstraction must:

1. **Record which provider served.** The deployed proxy already does this: its access log
   carries `upstream=$upstream_addr` per request. Which machine answered is always
   recoverable.
2. **Make degradation observable** to the operator — not necessarily in the answer, but never
   nowhere.
3. **Fail loud** when no equivalent provider exists (§7.1) — never substitute across tiers to
   manufacture an answer.
4. **Be simpler than what it hides** (§12, R-3).

### 5.4 Deployed today vs. principle — the honest boundary

Per *Architecture Rules* (`PROJECT_RULES.md`): architecture documents describe deployed
reality; future ideas belong in ROADMAP/DRAFT. This section is the boundary.

**Deployed (real, validated):**

```text
Open WebUI ─┐                         ┌─▶ Torre (RTX 5070)   ~101 tok/s  [primary]
            ├─▶ ollama-proxy ─────────┤
Home        │   (nginx failover)      │
Assistant ──┘                         └─▶ UM790 (CPU)        ~6 tok/s    [backup]
```

- One capability (`llm.chat`), two providers, static priority, passive health
  (`max_fails=1 fail_timeout=10s`), automatic fallback, per-request upstream logging.
- Both providers serve the same model id — equivalence holds **by operator discipline**.

**Principle, NOT deployed — does not exist and is not authorized by this document:**

```text
a capability registry
capability negotiation / discovery
provider abstraction for stt / tts / embed / rerank / vector / vision
dynamic or attribute-driven selection
enforced semantic-identity verification
```

Nothing above is built. Nothing above is scheduled. This document constrains **how** such
things must be shaped **if** a real need ever arises — it does not create the need (§14).

---

## 6. Provider selection

### 6.1 Selection is policy, not Aurora

Selection lives in the provider/selection layer. Today, for `llm.chat`, that layer is an
nginx upstream block — a config file, not code, and not inside Aurora. Aurora asks for
`llm.chat`; something else decides where that lands. Aurora must never contain the decision,
and must never contain a conditional over which hardware is present.

### 6.2 Criteria

In precedence order:

| # | Criterion | Rule |
|---|---|---|
| 1 | **Trust boundary** | Inside AMAROLAB only — local, or operator-controlled via VPN / Tailscale. **Non-negotiable** — never traded for speed (§1.1; §12, R-1). |
| 2 | **Fidelity** | The provider must satisfy the contract's semantic identity. A provider that does not is **not a candidate**, at any speed. |
| 3 | **Availability** | Is it actually reachable now? |
| 4 | **Performance** | Among equivalent, available candidates — prefer the best measured. |
| 5 | **Cost** | Power/wear. Torre is deliberately not 24/7. |

Trust boundary and fidelity are **filters**; performance and cost are **preferences**. A
preference may never override a filter. A provider outside the trust boundary is not a slow
candidate or an expensive one — **it is not a candidate.**

### 6.3 Automatic evolution

**Selection must be able to take advantage of better hardware without Aurora being told.**
When a provider that is equivalent (filter 2), local (filter 1) and faster (preference 4) is
registered, selection should prefer it — with no Aurora change, and no redesign. That is
precisely what happened at RTX-1.6, and what must remain true for every node that follows.

The bound: **automatic evolution operates within a fidelity tier only.** Selection may
automatically get *faster*; it may never automatically get *different* (§4.4).

### 6.4 Selection may never

- Route to a provider outside the AMAROLAB trust boundary.
- Substitute a provider from another fidelity tier to avoid an error.
- Change semantic identity as a side-effect of a failover.
- Require Aurora to know that any of this happened.

---

## 7. Fallback strategy

### 7.1 Three states, and only three

| State | Condition | Behaviour |
|---|---|---|
| **1 — Serve** | an equivalent provider is available | serve; prefer by policy |
| **2 — Degrade** | only a slower/costlier **equivalent** provider is available | **serve**, and make it observable |
| **3 — Fail loud** | **no equivalent** provider is available | **fail honestly.** Never substitute across tiers. Never fabricate. |

State 3 is the one that matters. The tempting failure is to answer *somehow* — a smaller
model, a different engine, a guess. That trades a **visible** outage for an **invisible**
behaviour change, which is strictly worse in a system whose value rests on being trusted.

### 7.2 The always-on floor

The UM790 runs 24/7 and is the always-on provider for every capability. On-demand hardware
(Torre) may make Aurora *faster*; it may never be the thing Aurora *needs*. Any capability
Aurora depends on must have an always-on provider, or Aurora must degrade honestly without
it. This is why RTX-1.6 kept the UM790 CPU path as `backup` rather than decommissioning it —
and why "production stays on UM790" remains architecture principle #1
([`amarolab_architecture.md`](amarolab_architecture.md)).

### 7.3 The precedent is validated, not theoretical

The three-state model is not new policy — it is the behaviour AMAROLAB already gated:

| Evidence | Behaviour | State |
|---|---|---|
| G-1.6-10 (live fallback) | Torre unreachable → UM790 serves; same model; slower | **2** |
| G-D6 §7.1 (Whisper down) | STT **fails closed**; no state change; no agent call | **3** |
| G-D6 §7.3 (Ollama unreachable) | clean error in seconds; **no partial action** | **3** |
| G-D6 §7.2 (Piper down) | intent lands; reply audibly silent; failure surfaced | **3**, disclosed |

This document generalizes those validated behaviours from voice and inference to **every**
capability.

---

## 8. Migration principles

Hardware migration is a **policy change**, never an Aurora change. The recipe is the one
RTX-1.6 already proved:

1. **Never migrate by editing Aurora.** If migration requires touching a tool, a prompt or
   the World Model, stop — the coupling is the defect (§1.2).
2. **Prove equivalence before switching.** The new provider must be shown to satisfy the
   contract's semantic identity on **real data** — never assumed from a shared API.
   Fabricated or synthetic validation does not close this
   (`PROJECT_RULES.md` → *Validation Rules*).
3. **Security posture before traffic.** RTX-1.6 required an approved security delta doc
   ([`../06_security/rtx_node_security.md`](../06_security/rtx_node_security.md)) *before* the
   endpoint swap. A new provider is a new attack surface first and a speedup second.
4. **Keep the old provider as fallback** until the new one is proven under real load. Retire
   deliberately, never as a side-effect of adding.
5. **Rollback = repoint selection**, never revert Aurora. If rollback requires reverting
   Aurora, principle 1 was violated.
6. **Gate it.** RTX-1.6 passed eleven gates including live fallback and production integrity.
   The bar for the next provider is the same bar.
7. **Document the provider, not just the machine.** Which capability, which semantic identity,
   which tier, which availability class. *If it is not documented, it does not exist.*

---

## 9. Scalability

The principle's payoff is asymmetric, and that asymmetry is the point:

| Axis | Cost to Aurora | Bound by |
|---|---|---|
| **+1 provider** for an existing capability | **zero** | provider registration + validation only |
| **+1 machine** hosting existing capabilities | **zero** | as above |
| **+1 consumer surface** | **zero** | AD-01 (already decoupled) |
| **+1 capability** | **real, and legitimate** | new tools/prompts/contracts |

Aurora's design cost scales with **capabilities**, not with **machines**. Machines are the
axis that will churn most; capabilities are the axis that reflects genuine growth in what
Aurora can do. Hardware growth is O(1) on Aurora — indefinitely.

This also bounds what "more hardware" can ever buy: adding a node makes Aurora *faster or
more available*, never *more capable*. New capability is design work, and this principle
neither provides nor disguises it.

---

## 10. Future hardware support

The contract must not assume the accelerator of the moment. Concretely: **it must not assume
CUDA.** Today's only GPU provider is an NVIDIA card, and it would be easy to let CUDA
assumptions leak into a contract and quietly re-couple Aurora to one vendor — the same
mistake as naming Torre, one abstraction level up.

A provider satisfying a capability contract is a valid provider regardless of vendor, ISA,
accelerator type, OS, or whether the silicon exists yet. The contract is the interface plus
the semantic identity — never the instruction set.

Support for future hardware therefore requires **no forecast**. AMAROLAB does not need to
predict which accelerator wins. It needs Aurora to be indifferent to the answer.

---

## 11. Examples

Compute providers may be — illustrative, not a roadmap; nothing below is planned work:

| Provider | Could provide | Availability | Status |
|---|---|---|---|
| **UM790** | everything; the always-on floor | always-on | **deployed** — 24/7 node, `llm.chat` fallback |
| **RTX workstation (Torre)** | fast `llm.chat`; large models; vision | on-demand | **deployed** — RTX-1.6, primary via proxy |
| **Jetson** | always-on low-power GPU inference; vision | always-on | hypothetical — would **raise the floor** |
| **NAS AI node** | `embed.text` / `rerank.text` beside the data | always-on | hypothetical — the NAS itself is a pending purchase |
| **Ryzen AI** | NPU inference for small/steady workloads | always-on | hypothetical — see below |
| **Apple Silicon** | large models on unified memory | on-demand | hypothetical |
| **Future NPUs** | unknown; vendor and interface unknown | unknown | hypothetical — the reason §10 exists |
| **Remote compute nodes** | any capability, over VPN / Tailscale | varies | **operator-controlled only**, inside the trust boundary — never third-party (§1.1; §12, R-1) |
| ~~Third-party cloud inference~~ | — | — | **Excluded.** Not a hardware question (§1.1; §12, R-1). Outside the trust boundary; outside this principle. |

**The Ryzen AI row is the sharpest illustration.** The UM790's own Ryzen 9 7940HS carries an
on-package NPU that AMAROLAB has never used. *(Unvalidated: whether it is usable under this
Linux install, and whether it would benefit any Aurora capability, is unmeasured. It is
listed as an illustration, not a claim.)* If it were ever used, **a new provider would appear
inside a machine that already exists** — no purchase, no new node, no topology change. A
principle scoped to "boxes" would miss it entirely. This is why §5.1 makes the unit of
abstraction the **capability**, not the machine.

**Worked example — a new GPU node arrives.**

```text
Under this principle          A new node is registered as an llm.chat provider,
                              proven equivalent on real data, added to selection.
                              Aurora: 0 lines changed.  Rollback: repoint selection.

Without this principle        Find every hardcoded endpoint. Edit tools. Re-validate
                              prompts. Re-gate awareness. Risk regressing WM-6 / G-F5-04.
                              Rollback: revert Aurora and re-validate again.
```

The second column is not hypothetical cost — it is the cost RTX-1.6 **avoided**, and it is
the cost `system_status` would incur today (§15).

---

## 12. Risks

**R-1 — The trust-boundary loophole. *(highest severity)*** "Hardware-agnostic" is one short
step from "compute-agnostic", and "remote compute nodes" (§11) can be misread as authorizing
a third-party inference API. **It does not.** *"Everything local. No external LLM calls."*
remains a non-negotiable constraint
([`../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md`](../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md);
[`../00_overview/ROADMAP.md`](../00_overview/ROADMAP.md) → *Long-Term Vision*). **"Remote"
here means operator-controlled hardware reached over the AMAROLAB private network (VPN /
Tailscale) — never a service someone else runs.**

**Why this is not an exception carved out of the principle.** This document makes *hardware*
interchangeable. It does not make **trust boundaries** interchangeable — those are a
different axis, and the principle never moved it (§1.1). A third-party provider is not
excluded because it is unusual hardware; it is excluded because **it is not a hardware
question at all.** Adding one would not extend the principle — it would **invert** it, by
falsifying the one guarantee the principle rests on: that swapping providers changes speed,
availability and cost, and **nothing else**. Concretely, it would change:

| Invariant | What a third-party provider does to it |
|---|---|
| *"The audit log traces of Aurora's tool calls are the security record of Aurora's behaviour"* (Vision §7) | ceases to be **complete** — the reasoning step happens off-premises |
| *"Aurora does not hold secrets"* (Vision §7) | acquires an API key |
| Prompt content (lab state, entity names, operational detail) | leaves the premises |
| Guardian Cloud corpus (read-only, **absolute** boundary) | becomes exposable via RAG context |
| The always-on floor (§7.2) | becomes contingent on a vendor's uptime, pricing and terms |

Mitigation: the trust boundary is a declared contract field and the **first filter** in
selection (§6.2) — a provider outside it is not a candidate at any speed. **Changing the
boundary is a separate architectural decision** (§1.1, §14); this principle must never be
cited as its justification.

**R-2 — Silent semantic drift on failover.** A failover that changes the model changes Aurora
invisibly, triggered by an unrelated network event. **This risk is live today**, not
hypothetical: the proxy pins the *interface*, not the *semantics*. nginx cannot verify that
Torre serves the same weights as the UM790 — it routes by address. Equivalence currently
holds **because the operator pulled the same model on both nodes**, not because anything
enforces it. Mitigation today: operator discipline, and the fact that both are documented as
`qwen2.5:7b-instruct`. Mitigation if the provider set grows: verify semantic identity at
registration (§8.2). Accepted for the current two-provider set; the risk scales with provider
count, and this document names it so it is never rediscovered by surprise.

**R-3 — The abstraction becomes the fragile thing.** An indirection layer concentrates risk.
CURRENT_STATE already records this honestly: the proxy is *"a single point of failure in front
of both front doors … only a proxy outage stops inference."* A Torre outage is survivable; a
*proxy* outage is not. Mitigation: the abstraction must be simpler than what it hides (nginx
config, not a service); the always-on floor stays directly reachable; rollback is repointing
consumers back to `ollama:11434`. **The abstraction must never become the most complex thing
in the path.** *Avoid: clever, fragile, hidden, overengineered.*

**R-4 — Overengineering ahead of need.** A general capability registry for a one-capability,
two-provider reality is exactly what `PROJECT_RULES.md` → *Infrastructure Philosophy* forbids
and what Vision §8 defers (*"infrastructure for its own sake is deferred"*). The principle is
permanent; the machinery must stay proportionate. Mitigation: §14 — this document authorizes
nothing.

**R-5 — Availability assumptions.** Remote providers add network failure modes and a
Tailscale dependency; on-demand providers add cold-start cost (Wake-on-LAN remains designed
but not configured). Mitigation: availability is a declared contract field; the always-on
floor (§7.2) absorbs it.

**R-6 — Contract rot.** Capability contracts are documentation, and documentation drifts from
reality. A contract asserting an equivalence that no longer holds is worse than no contract —
it converts R-2 from a known risk into a false assurance. Mitigation: *Reality always wins*;
contracts are validated on real data, and a contract that cannot be validated is a defect.

**R-7 — Hardware identity leaking back into Aurora.** The principle erodes one convenient
constant at a time. It is already breached once (§15). Mitigation: §1.3 makes the rule
checkable — hardware identity in a tool, prompt, or model artifact is a defect, and greppable
as one.

---

## 13. Consequences

**Aurora gains:**

- Hardware evolution costs zero Aurora change (§9) — indefinitely.
- Upgrades cannot regress validated behaviour, because they do not touch it. The WM-6 /
  G-F5-04 closure and the ER-1 work are insulated from every future node by construction.
- Migration and rollback are both configuration changes.
- Hardware decisions become **economic** (what to buy, when) rather than **architectural**
  (what to rewrite).

**AMAROLAB accepts:**

- **An indirection layer that is itself a SPOF** (R-3). This is a real, permanent cost, paid
  in exchange for the above.
- **Per-provider equivalence work.** Every new provider owes real-data validation (§8) and a
  security posture before traffic. The principle makes providers cheap for *Aurora*, not free
  for the *operator*.
- **Capability contracts as maintained documentation** — subject to rot (R-6), and to *if it
  is not documented, it does not exist*.

**This decision forbids:**

- Hostnames, IPs, GPU vendors or machine names inside tools, prompts, the World Model, or
  awareness artifacts (§1.3).
- Hardware-conditional logic inside Aurora.
- Silent substitution across fidelity tiers (§4.4, §7.1).
- Routing any capability to compute outside the AMAROLAB trust boundary (§1.1; R-1).
- Migrating by editing Aurora (§8.1).

**This decision does not:**

- Authorize any implementation (§14).
- Change any current behaviour, artifact, or gate.
- Justify buying hardware. *Aurora first*: hardware is bought when Aurora's usefulness needs
  it, and this principle only guarantees that when that day comes, the cost lands on the
  invoice rather than on the architecture.

---

## 14. Boundaries — what this document does not do

This is a **constraint on future work, not a work item.** It creates no phase, no gate, no
backlog entry, and no obligation to build anything.

Specifically, it does **not** authorize: building a capability registry; abstracting STT/TTS/
embedding/reranking/vector search; refactoring the proxy; or any purchase.

**It does not move the trust boundary, and must never be cited to move it.** This principle
grants hardware independence only (§1.1). Any proposal to place compute outside the AMAROLAB
trust boundary — a third-party inference API, or operator-rented compute on hardware the
operator does not physically control — is a **separate architectural decision** on a
different axis, requiring its own gated operator ratification against the *"everything local"*
constraint and its own security posture. Such a proposal is neither blocked nor enabled by
this document. **A future reader must not mistake "providers are interchangeable" for
"trust boundaries are interchangeable"** — that inference is exactly what §12 R-1 forbids.

The correct trigger for building any of that is a **real** one — a second provider genuinely
exists for a capability that has one today, and pinning is causing actual pain. Until then,
a pinned single-provider capability is **correct, not debt** (§4.2). The proxy exists because
Torre exists; had Torre not existed, building the proxy first would have been the error.

Compare the *Health Aggregator* backlog entry
([`../00_overview/ROADMAP.md`](../00_overview/ROADMAP.md)), which uses exactly this
discipline: the design is recorded, and the trigger is *"when a third health producer would
otherwise require a third writer."* Same shape here — **the principle is written down now so
that when the trigger arrives, the answer is already decided and the work is small.**

---

## 15. Identified debt — `system_status` names Torre

Recorded, **deliberately not fixed** — fixing runtime code is outside this document's
approved scope, and this document introduces no runtime change. Following the F-ER13-1
precedent (a defect found during ER-1.3, recorded and left for a scoped change).

**Finding.** [`../ai-stack/ingest/docs/system_status_tool.py`](../ai-stack/ingest/docs/system_status_tool.py)
(`system_status` v0.3.0) hardcodes a specific machine as file-level constants —
`TORRE_URL` (a literal Tailscale address, line 23) and `TORRE_TIMEOUT` — plus `_probe_torre()`
and the machine's name in its output and its docstring.

**Is it a violation?** Partly, and the distinction matters:

| | |
|---|---|
| **Describing hardware** | Legitimate. A status tool reporting "the GPU node is unreachable" is doing its job. |
| **Depending on hardware** | The defect. `system_status` cannot report on a *different* GPU node without a code edit. |

`system_status` is doing the first **by means of** the second. It is the one place where
"Aurora must never require changes because hardware changes" **does not currently hold**: a
second GPU node, or Torre's replacement, requires editing an Aurora tool and reinstalling it
in `webui.db`.

**Shape of the eventual fix** (not scheduled, not designed, not authorized here): report the
**provider set** for a capability — obtained from the selection layer, which already knows
which upstream served — rather than probing one hardcoded address. A new node would then
appear in the status report with no code change.

**Severity: low.** It is one tool, in the reporting path, with no effect on awareness,
actuation, or the World Model. It is recorded because a principle that cannot name its own
first violation is decoration — and because this is exactly the coupling §1.2 says should be
read as the defect signal.

---

## 16. Relationship to existing decisions

**Amends nothing.** No frozen decision, invariant, or gate is touched.

| Decision | Relationship |
|---|---|
| **AD-01** (awareness is a platform capability) | **Same instinct, opposite end.** AD-01 decouples Aurora from consumers; this decouples Aurora from providers (§2.3). |
| **AD-21 / World Model** (FROZEN) | **Untouched.** The World Model describes *meaning*, never *wiring* — it is already hardware-free and stays so. This principle is the reason it can remain so. |
| **ER-1** (in progress) | **Untouched.** ER-1 concerns entity resolution and write honesty; no overlap. INV-17 / D-12 are not affected: **D-12 remains the sole authorization authority.** |
| **D-01** (`qwen2.5:7b-instruct` Q4_K_M) | **Load-bearing here.** D-01 is the semantic identity that makes the deployed fallback safe (§4.3). |
| **INV-19 / AD-20** (awareness contract) | **Untouched** — no artifact, schema or consumer changes. |
| **RTX-1.6** | **The evidence base.** This document generalizes what RTX-1.6 proved (§2.2) and makes its migration recipe binding (§8). |
| **Vision §7–§9** | **Consistent.** *Aurora does not pretend* → §5.3, §7.1. *Honest under uncertainty* → §4.3. *Infrastructure for its own sake is deferred* → §14. Measured quality gaps → §4.4. |
| **"Everything local. No external LLM calls."** (`AMAROLAB_HANDOFF.md` → *Constraints (non-negotiable)*) | **Untouched and reinforced.** This principle moves the hardware axis only; the trust boundary is out of scope by operator ratification (§1.1) and defended as the first selection filter (§6.2) and the highest-severity risk (§12, R-1). |
| **`PROJECT_RULES.md` → Hardware-Agnostic Platform** | **The rule; this is its justification.** |

---

## 17. Summary

```text
Aurora depends on capabilities.
Hardware provides capabilities.
Hardware changes.  Aurora does not.

New hardware       →  register a provider.        Aurora: unchanged.
Hardware retired   →  fall back, or fail loud.    Aurora: unchanged.
New capability     →  Aurora changes. That is what capability means.

Providers may differ in speed, availability and cost.
They must never differ in meaning.

Compute providers may evolve freely —
inside the AMAROLAB trust boundary.

This principle grants hardware independence.
It does not grant trust-boundary independence.
Those are different decisions, and this is only the first one.
```
