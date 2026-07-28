# HAZARD — Do not redeploy the Portainer `ai-local` stack

**Status:** ACTIVE — the hazard is live right now.
**Recorded:** 2026-07-28 (remediation item I-2)
**Source finding:** H-4 — [`../../09_logs/2026-07-28_amarolab_technical_audit.md`](../../09_logs/2026-07-28_amarolab_technical_audit.md) §3
**Removed by:** **M-B** (converge the stored definition with reality), which depends on **I-3**
(capture) and on **F6.1 being closed**.
**Type:** standing operational hazard. Unlike `09_logs/` records, this document **is**
maintained — it is deleted or marked resolved when M-B lands, not left as history.

---

## 1. The prohibition

> **Do not redeploy, update, re-pull or "restart stack" the Portainer stack `ai-local`
> (stack 2, `/data/compose/2/docker-compose.yml`).**
>
> Do not use Portainer's *Update the stack*, *Pull and redeploy*, or *Editor → Deploy*
> on it. Do not run `docker compose` against `/data/compose/2/`.

Reading the stack in Portainer is safe. Deploying it is not.

The same caution applies to stacks **1** (`homeassistant`) and **4** (`proxy`): their
definitions have never been reviewed either, and they are equally invisible. `ai-local` is
singled out here because its divergence is **measured**, not suspected.

## 2. Why

The stored stack definition and the running containers have diverged. Every AMAROLAB change
since Phase RTX-1 — RTX-1.6, F-2, F-3a, and the ER-1 tool work — was applied to the **live
containers** and never written back to the stored definition, which sits inside the
`portainer_data` Docker volume where nothing reviews it.

Stored definition for `openwebui`, as recorded by the audit:

```yaml
openwebui:
  environment:
    - OLLAMA_BASE_URL=http://ollama:11434
    - VECTOR_DB=qdrant
    - QDRANT_URI=http://qdrant:6333
  volumes:
    - /srv/homelab/data/openwebui:/app/backend/data
```

What the running `openwebui` actually carries (verified live 2026-07-28):

| Live configuration | Purpose | Lost if the stored definition is applied |
|---|---|---|
| `OLLAMA_BASE_URL=http://ollama-proxy:11434` | RTX-1.6 endpoint swap | Torre GPU path reverts to the ~6 tok/s CPU Ollama |
| `QDRANT_API_KEY` (set) | Qdrant authentication | `rag_search` returns 401 — RAG dead |
| `HA_BASE_URL`, `HA_LLAT` | Home Assistant tools | `ha_get_state` **and** `ha_call_service` both break |
| `AMAROLAB_AUDIT_LOG=/app/backend/data/amarolab-audit.log` | D-07 / D-21 audit trail | Audit logging stops; `audit_search` goes blind |
| mount `ai-stack/aurora → /opt/aurora` (ro) | F-3a awareness Filter, `system_status` | Awareness renders `Unavailable`; World Model consumers blind |
| mount `ai-stack/ingest → /opt/ingest` (ro) | Ingest tooling | Ingest-side tooling unavailable to the container |

That is eleven gates' worth of validated behaviour, reachable by one click.

## 3. The failure mode is worse than a silent revert

The audit assessed this as a *quiet* revert — every service stays "up". Live verification on
2026-07-28 refines that, and the refinement makes the hazard **more** dangerous, not less.

**Fact.** Only `ollama` still carries the compose project labels
(`com.docker.compose.project=ai-local`). **`openwebui` and `qdrant` carry no compose labels
at all** — they were recreated by hand during the RTX-1.6 / F-2 / F-3a / ER-1 work and left
the compose project entirely.

**Fact.** The Portainer-managed containers are named `ollama`, `homeassistant` and
`nginx-proxy-manager`. The last one carries `com.docker.compose.service=npm` while being
named `nginx-proxy-manager` — compose would have produced `proxy-npm-1`. The stored
definitions therefore **set `container_name` explicitly**.

**High-confidence inference** (same authoring hand, same naming pattern): stack 2 sets
`container_name: openwebui` and `container_name: qdrant`.

**Hypothesis — not verified.** The stored file's full content has not been read; doing so
requires a helper container to reach the `portainer_data` volume, which `diego` cannot read
directly. On that basis, a redeploy would most likely:

1. **recreate `ollama` cleanly** — it is still labelled and owned by the project; then
2. **fail on `openwebui` and `qdrant`** with a container-name conflict, because containers
   with those names exist but are not owned by the project.

**This is the trap.** The natural response to a name conflict is to remove the conflicting
container and redeploy — and *that* produces the full revert in the table above, this time
initiated deliberately by the operator, who now believes they are cleaning up a stale
container rather than destroying the entire AMAROLAB configuration.

**If a redeploy has already been started and a name conflict appears: stop. Do not remove
the conflicting container.** The running `openwebui` and `qdrant` are the source of truth;
the stored definition is the stale artifact.

## 4. What removes the hazard

| Step | Item | State |
|---|---|---|
| Capture the live configuration into version-controlled compose files | **I-3** | Approved for planning; not implemented |
| Converge the stored definition with reality under a gated change | **M-B** | Blocked on I-3 **and** on F6.1 being closed |

The correct repair direction is fixed by `PROJECT_RULES.md` → *Reality always wins*:
**the definition is corrected to match the running containers.** The containers are never
changed to match the definition.

## 5. Related constraint

`aurora-whisper` must not be recreated while F6.1 is open — **D-F6-1** pins the frozen Step 2
baseline to the currently-running container. It is not part of the `ai-local` stack, but it
shares the `ai-local_default` network and sits in the same blast radius as any careless
project-wide compose operation.
