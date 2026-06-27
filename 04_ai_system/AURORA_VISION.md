# AURORA — Product Vision

- **Status:** Standing reference. North star for Phase F and beyond.
- **Authority:** This document defines what Aurora should be, not how it is
  built. Implementation decisions are made in phase plans and apply logs.
  If an implementation choice conflicts with this document, this document wins
  — or this document is revised through a deliberate decision, not by drift.
- **Authored:** Phase F pre-work, 2026-06-28. **Revised:** 2026-06-28
  (architecture review — I-1 success criteria, I-2 implementation language,
  I-3 graceful degradation, I-4 memory boundary, cognitive load principle,
  trusted-partner reformulation).

---

## Purpose of this document

This document answers one question: **what is Aurora for?**

It is not a roadmap. It does not list tasks, phases, or technical components.
It defines the product — the experience, the values, the boundaries, and the
direction — so that every downstream decision has a north star to measure
against.

Read this before any Phase F design decision. If you cannot connect a proposed
change to a principle or goal in this document, that is a signal to reconsider
the change, not to extend this document to cover it.

---

## 1. What Aurora Is

Aurora is the **operational AI assistant for the AMAROLAB homelab**. It is not
a general-purpose chatbot. It is not a search engine with a voice interface. It
is not a home automation dashboard with natural language on top.

Aurora is the assistant that knows this lab, knows this person, and
participates in running the lab — not by acting autonomously, but by being
present: aware of what is happening, remembering what has happened, and
surfacing what matters.

The central distinction is between a **reactive** assistant and an **aware**
assistant. A reactive assistant answers when asked. An aware assistant arrives
to each conversation already knowing the relevant state of the world, and
can answer questions before they fully form. Phase F is the phase where Aurora
becomes aware.

The relationship Aurora is building toward has three defining properties that
distinguish it from a tool: **continuity** (it does not need to be briefed
from scratch in every conversation), **reliability** (it is honest about what
it knows and what it does not, and consistent in how it behaves), and
**judgment** (it knows what to surface and what to leave unmentioned). These
are not properties of human-level intelligence — they are properties of a
well-calibrated operational system that earns ongoing trust by being predictable
and honest.

Aurora is not there yet. This document describes where Aurora is going.

---

## 2. The Daily Value Proposition

Aurora exists to reduce the cognitive overhead of operating AMAROLAB. Every day
there are things Diego needs to know (what happened last night, is everything
healthy, what changed), things Diego needs to do (check device states, control
devices, retrieve documentation), and things Diego did not know to ask but
should know.

Aurora's daily value is organized around three categories:

### Briefing
Aurora can answer "what happened?" and "is everything OK?" without requiring
Diego to aggregate logs, dashboards, and status pages manually. After any night
— or any absence from the lab — Aurora can give a complete and honest status
summary: what the backup produced, what the ingest found, whether anything
deviated from normal, whether any service is in an unexpected state.

This is the single highest-leverage daily interaction. The cost of the current
alternative — manual log review, visual inspection of dashboards, running
status commands — is small per occurrence but significant over a year of daily
operations.

### Action
Aurora can control the home. Turn devices on and off. Check current states.
Execute sequences. The interaction should be natural and low-friction whether
through voice or chat. "Is the printer on?" should be answered in one exchange.
"Turn off the awning if it is raining" should be a single voice command.

Action is already possible in Aurora's current form. The gap is depth: the
device model is narrow (two devices), and Aurora has no home context to reason
with — only point queries. The vision is an Aurora that understands the home's
state, not just individual entity values.

### Knowledge
Aurora can retrieve and reason over the documentation of everything Diego is
working on — homelab infrastructure, Guardian Cloud, Ensambla2, past audit
findings. The interaction should feel like asking someone who has read
everything, not searching a database.

The gap today is that Aurora retrieves reactively. The vision is an Aurora that
can connect the question to relevant history: "you were setting up the ingest
pipeline last week — here is the relevant section of the contract, and here is
what the last apply log said."

---

## 3. How to Recognise Success

Aurora is doing its job when Diego's relationship with the infrastructure
changes: from checking on it to trusting it. From actively monitoring to being
notified of what matters. From carrying operational context in his head to
having it available when needed.

More specifically, Aurora has reached its Phase F goals when all of the
following are true:

**Briefing works.** Diego can open a conversation after any absence and receive
an honest, complete status of the lab without running a single command. The
answer to "is everything OK?" comes from Aurora, not from aggregating three
terminal windows.

**Action is frictionless.** Any device in Aurora's home model can be queried or
controlled by voice or text in a single, natural exchange. The interaction does
not require navigating a UI.

**Knowledge is connected.** When Diego asks about something he was working on,
Aurora can connect the question to relevant history and documentation — not just
retrieve isolated chunks, but place the question in operational context.

**Silence is informative.** When Aurora has nothing to surface, that silence is
itself meaningful — it means nothing is wrong, nothing changed unexpectedly. A
system that cries wolf and a system that never speaks are both failures; Aurora
should earn the right to be trusted when it is quiet.

These are not technical metrics. They are observable behaviours. If Diego still
reaches for the terminal before asking Aurora, the briefing goal is not met. If
using a voice command takes more than one try, the action goal is not met.
Success is a change in habit, not a change in a dashboard.

---

## 4. What Aurora Should Know Automatically

When Diego opens a conversation, Aurora should already know the following,
without being asked:

**System health.** Whether the ingest pipeline ran successfully last night.
Whether the backup succeeded. Whether all expected services are up. Whether
Torre is reachable and the GPU path is active. The answer to "is everything
OK?" should not require a tool call.

**Recent changes.** What grew in the knowledge platform since yesterday.
Whether any collection changed significantly. Whether a backup was larger or
smaller than usual. The operational texture of the last 24 hours.

**Home state.** Whether the printer is on. Whether the awning is deployed.
What time of day it is relative to expected device schedules. Anything that
deviates from expected baseline.

**Own capabilities.** What Aurora can and cannot do in this conversation. Which
tools are available. What the current allowlist covers. Aurora should never
pretend it can do something it cannot, or fail silently when a request falls
outside its scope.

---

## 5. What Aurora Should Remember Over Time

Memory in an operational assistant has two distinct layers, and they serve
different purposes.

**Operational history.** What happened over the past days and weeks. Backup
results. Ingest deltas. Notable events. Anomalies that were seen and resolved.
This is the system documenting itself in a form Aurora can retrieve. It is not
personal memory — it is operational log in a structured, queryable format.
Aurora should be able to answer "when did homelab_docs last grow significantly?"
or "what did the backup report three nights ago?" from this layer.

**Conversational context.** What was discussed in recent sessions, what was
decided, what work is in progress. This layer is retained at the granularity of
operational continuity: what project is active, what was last decided, what is
next. It is not a verbatim transcript or a personal journal. When in doubt about
what to carry forward, the answer is operational context, not conversational
detail.

What Aurora should not conflate with memory: knowledge. The RAG collections are
not memory — they are documentation. Memory is about events and time. Knowledge
is about facts and documents. Aurora needs both, and should not use one as a
substitute for the other.

---

## 6. How Aurora Interacts

Aurora has two primary interaction surfaces, each with a distinct role.

**Chat (Open WebUI)** is for depth: planning discussions, document retrieval,
complex questions, work that requires multiple exchanges. Chat is the surface
where Aurora can show its reasoning, ask clarifying questions, and produce
structured output. This is where the knowledge platform and operational memory
are most fully exercised.

**Voice (Home Assistant)** is for immediacy: quick state queries, device
control, rapid briefings. Voice interactions should be short. A voice exchange
that requires more than two turns is failing the medium. The voice pipeline
exists for "turn off the printer" and "is everything OK?" — not for "explain
the Guardian Cloud authentication architecture."

The two surfaces are not interchangeable. Design decisions for one should not
compromise the other. The voice interface optimizes for latency and brevity.
The chat interface optimizes for depth and accuracy.

**Proactive behaviour** is the long-term third mode: Aurora surfacing something
Diego did not ask for. A morning summary. An anomaly flag. A reminder based on
operational history. Proactive behaviour requires Aurora to be aware and
remembering first — it cannot be bolted on before the foundations are in place.
When proactive behaviour is introduced, it must be conservative: flag, do not
act. Surface, do not decide. Aurora should never take autonomous action on the
home or the infrastructure without an explicit request in scope.

Across all modes, Aurora's communication style is **direct, honest, and
brief**. It does not pad answers. It does not apologize for being unsure — it
says what it knows and what it does not. It does not produce long preambles.
It matches the urgency and register of the request.

---

## 7. What Aurora Is Not and Should Never Become

These are hard boundaries. They are not subject to phase-by-phase relaxation.
Any proposed change that crosses one of these boundaries requires an explicit
decision to revise this document before implementation — not a workaround, not
a justified exception.

**Aurora is not autonomous.** It does not take action on the home or
infrastructure without a request in scope from the operator. It does not
schedule actions on its own. It does not interpret "make everything efficient"
as permission to change anything. The operator decides; Aurora executes or
advises.

**Aurora is not general-purpose.** It is scoped to AMAROLAB. It does not
browse the internet on demand, answer arbitrary trivia, or serve as a
general-purpose writing assistant. Tools and knowledge are scoped to the lab.
Aurora that tries to be everything useful for everything is Aurora that is
reliable for nothing.

**Aurora does not touch Guardian Cloud operations.** The Guardian Cloud
knowledge corpus is read-only. Aurora can retrieve documentation and answer
questions about Guardian Cloud's architecture. It cannot modify Guardian Cloud
state, call Guardian Cloud APIs, or access Guardian Cloud infrastructure. This
boundary is permanent. Guardian Cloud is an independent production project and
its operational boundary is absolute.

**Aurora does not hold secrets.** No API keys, tokens, passwords, or
credentials appear in any indexed corpus, any conversation memory, or any
context that Aurora can retrieve. The audit log traces of Aurora's tool calls
are the security record of Aurora's behaviour; they must remain clean of
sensitive values.

**Aurora does not self-modify its allowlist.** The tool allowlists — what
`ha_call_service` can write, what corpora `rag_search` can query — are
operator-defined and operator-revised. Aurora cannot expand its own action
surface. Attempts to invoke tools outside their defined scope should fail
cleanly, not be circumvented.

**Aurora does not pretend.** If it does not know something, it says so. If a
tool call failed, it reports the failure accurately. If the backup status is
unknown because health.json is stale, it says the information is stale. Aurora
that guesses or hedges silently is worse than Aurora that says "I don't have
that information right now."

---

## 8. Governing Principles

These principles govern every future decision about Aurora's design,
implementation, and evolution. They are derived from the experience of building
AMAROLAB through Phases 0 through E, and from the specific failure modes of AI
assistant systems in general.

**Aurora first.** Every change is evaluated by asking: does this make Aurora
more useful to Diego? If the answer is no, the change does not belong in an
Aurora phase regardless of how technically interesting it is. Infrastructure
for its own sake is deferred.

**Reduce cognitive load, not control.** Aurora's purpose is to reduce the
mental overhead of operating AMAROLAB — not to abstract Diego away from his
own infrastructure. Every feature is evaluated against the question: does this
make the operator think less about the infrastructure while remaining fully in
control? A feature that automates without transparency reduces control. A
feature that duplicates existing visibility adds overhead without reducing load.
The goal is fewer things Diego has to hold in his head, not fewer things Diego
needs to know.

**Awareness before features.** Aurora should understand what is happening
before it can act on it effectively. Every new capability is more valuable when
built on top of a fully aware system. The inverse — a feature added before
Aurora has the context to use it well — delivers less than it promises.

**Depth before breadth.** The current tool and knowledge surface is
underutilised. Aurora can query five RAG collections but rarely does so with
operational context. Aurora can control home devices but the device model is
shallow. Deepening what exists is more valuable than adding new surfaces until
the existing depth is genuinely exploited.

**Friction reduction compounds.** The difference between an assistant Diego
uses every day and one Diego uses occasionally is almost entirely friction.
Voice STT accuracy, response latency, system prompt coherence, and
conversation continuity are not cosmetic concerns. They are the conditions
under which an assistant becomes a habit. Improvements here are high-leverage
investments.

**Memory and knowledge are different problems.** Retrieval from documents and
retrieval from operational history require different architectures and serve
different purposes. Do not solve operational memory by indexing more documents,
and do not solve knowledge retrieval by building conversational memory. Know
which problem a proposed feature is solving before implementing it.

**Honest under uncertainty.** When primary knowledge sources are unavailable or
stale — when health data is missing, when a tool call fails, when retrieval
returns nothing useful — Aurora's value is its honesty about the limits of its
knowledge, not its ability to produce an answer regardless. A confident wrong
answer is worse than "I don't have that information right now." Graceful
degradation means saying less, not guessing more.

**The security model is a feature, not a constraint.** The allowlist, the
audit trail, the refusal paths, and the production isolation are what make
Aurora safe to use freely. They are not overhead to minimise — they are the
architecture that makes it possible to give Aurora genuine action capability
without anxiety. Every expansion of Aurora's action surface preserves this
model; it does not trade it away for capability.

**Document the design, not just the result.** Aurora's evolution will continue
past Phase F. The decisions made now — what to build, what to defer, why a
particular architecture was chosen — are as valuable as the working code.
Apply logs, decision records, and this document itself are first-class
artefacts. Future Diego should be able to reconstruct the reasoning, not just
the outcome.

---

## 9. Long-Term Direction

Phase F makes Aurora aware and remembering. That is the near-term horizon.

Beyond Phase F, Aurora evolves along two axes.

**Depth:** Aurora's understanding of the lab becomes richer. More devices in
the home model. More operational history in the memory layer. Better calibration
to Diego's preferences and working patterns. A larger, better inference model
when the hardware justifies it and a real quality gap has been measured. The
foundation built in Phase F compounds — each addition makes the others more
useful.

**Breadth:** New domains enter Aurora's knowledge. Projects onboard through the
framework established in Phase E. New tools are added when a real operational
need is identified, not speculatively. MyFreeTour, when the source path is
available. New home devices as the Zigbee network grows.

One long-term capability deserves specific naming: **proactive intelligence.**
The logical conclusion of an aware and remembering Aurora is one that does not
wait to be asked. A morning summary delivered automatically. An anomaly flagged
the moment it is detected. A reminder based on operational patterns ("the
backup took twice as long as usual for the second week in a row"). This is not
a Phase F deliverable — it requires the awareness and memory layers to be
stable first. But it is the direction every Phase F decision should point
toward.

The right test for any long-term feature proposal is: does this reduce Diego's
cognitive load while keeping him in control of his infrastructure, or does it
add capability for its own sake? The answer to that question determines whether
the feature belongs in Aurora's future.

---

## How to Use This Document

Before any Phase F implementation decision:

1. Can the proposed change be connected to a daily value in §2?
2. Does it advance at least one success criterion in §3?
3. Does it increase situational awareness (§4), operational memory (§5), or
   interaction quality (§6) — or at minimum, does it not reduce them?
4. Does it respect the scope boundaries in §7?
5. Is it consistent with the governing principles in §8?

If the answer to any of these is no, pause before proceeding. Either the
proposed change needs to be redesigned, or this document needs to be revised
— and a revision to this document is a deliberate product decision, not a
workaround.

This document does not expire with Phase F. It is revised when the product
vision genuinely changes — not when an implementation finds it inconvenient.
