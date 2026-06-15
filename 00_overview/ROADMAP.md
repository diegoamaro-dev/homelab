# ROADMAP

## Phase 0

Completed

* Audit
* Remediation
* Documentation consolidation
* Security review
* Backup implementation
* RAG foundation

---

## Phase A

Current

### Goal

Assistant brain layer

Tasks:

* Evaluate qwen2.5:7b
* Compare against llama3
* Select default model
* Document findings

Success criteria:

Stable local model selected.

---

## Phase B

Tool Layer

Tasks:

* rag_search()
* time_now()
* system_status()

Success criteria:

Assistant can retrieve knowledge.

---

## Phase C

Home Assistant Integration

Tasks:

* ha_get_state()
* ha_call_service()

Security:

Allowlist only.

Never allow:

* homeassistant.*
* hassio.*
* recorder.*

Success criteria:

Read and limited control of the house.

---

## Phase D

Voice

Tasks:

* Whisper
* Piper
* Home Assistant Assist

Success criteria:

Voice interaction through the house.

---

## Phase E

Unified Knowledge

Tasks:

* Add MyFreeTour
* Improve RAG
* Continuous indexing

Success criteria:

Single assistant with access to all project knowledge.

---

## Long-Term Vision

One assistant.

Two front doors:

* Open WebUI (chat)
* Home Assistant (voice)

Shared brain:

* Ollama
* Qdrant
* Amarolab knowledge base

Everything local.

Everything documented.

Everything recoverable.
