# 05 — Implementation roadmap

Eight phases (A → H). Each has a **goal**, **work items**, **exit
criteria**, and **rollback**. Designed to be split across sessions; each
phase is independently safe to ship.

## Effort summary

| Phase | Goal | Effort | Calendar |
|-------|------|-------:|---------:|
| A | Tool-calling LLM + system prompt scaffold | 1 h | day 1 |
| B | `infra_audits` corpus | 1 h | day 1 |
| C | `homelab-tools` rewrite (containerized) | 2–3 h | day 2 |
| D | `rag_search` + `audit_search` Functions | 2 h | day 2 |
| E | `ha_get_state` + `ha_call_service` Functions | 2 h | day 3 |
| F | `system_status` Function | 1 h | day 3 |
| G | System prompt + acceptance test (the six questions) | 2–3 h | day 4 |
| H | Hardening (logrotate, refusal tests, cleanup) | 1 h | day 4 |
| **Total** | **~12–14 h, 4 calendar days** | | |

Each phase is described below in the same format as the Phase 0 and
Phase 1 application logs the user is already familiar with.

---

## Phase A — Tool-calling LLM + scaffold

**Goal:** Pull a model capable of native function calling and set up the
Open WebUI Functions directory.

**Prerequisites:** None beyond the current state.

**Work:**

- [ ] Pull `qwen2.5:7b-instruct` (Q4_K_M, ~4.7 GB):

      ```bash
      docker exec ollama ollama pull qwen2.5:7b-instruct
      ```

- [ ] (Optional) Pull `llama3.1:8b-instruct` as backup:

      ```bash
      docker exec ollama ollama pull llama3.1:8b-instruct
      ```

- [ ] Create the Functions dir on disk:

      ```bash
      mkdir -p /srv/homelab/data/openwebui/functions
      ```

      Open WebUI auto-discovers Functions placed here; no container restart needed.

- [ ] Drop a placeholder `amarolab_common.py` (with the audit helper
      from [03-tools.md](03-tools.md)) so future Functions can import it.

- [ ] In Open WebUI admin: Settings → Models → set default to
      `qwen2.5:7b-instruct`.

**Exit:**

- `docker exec ollama ollama list` shows the new model.
- A naked LLM smoke test with one inline tool succeeds:

      ```bash
      curl -s http://127.0.0.1:11434/api/chat -d '{
        "model": "qwen2.5:7b-instruct",
        "messages": [{"role":"user","content":"What time is it?"}],
        "tools": [{"type":"function","function":{
          "name":"time_now","description":"Get current time.",
          "parameters":{"type":"object","properties":{}}}}],
        "stream": false
      }' | jq '.message.tool_calls'
      ```

      → returns a `tool_calls` array, not a hallucinated time string.

**Rollback:** `docker exec ollama ollama rm qwen2.5:7b-instruct` (keeps
existing models intact).

---

## Phase B — `infra_audits` corpus

**Goal:** Make the past audit and remediation logs searchable.

**Prerequisites:** Phase 1 (ingest service running). No A dependency.

**Work:**

- [ ] Append to `/home/diego/homelab/ai-stack/ingest/conf/corpora.yaml`:

      ```yaml
        - name: infra_audits
          type: fs
          path: /home/diego/server-audit-2026-06-13
          include:
            - "**/*.md"
          exclude:
            - "**/inspect-snapshots/**"   # JSON inspect dumps, not docs
            - "**/*.json"
          enabled: true
      ```

- [ ] Create the Qdrant collection (same shape as Phase 1):

      ```bash
      KEY=$(awk -F= '/^QDRANT__SERVICE__API_KEY=/ {print $2; exit}' \
            /home/diego/homelab/ai-stack/.env)
      curl -X PUT -H "api-key: $KEY" -H "Content-Type: application/json" \
           "http://127.0.0.1:6333/collections/infra_audits" \
           -d '{"vectors":{"size":384,"distance":"Cosine"},"on_disk_payload":true}'
      for f in collection source_kind source_rel; do
        curl -X PUT -H "api-key: $KEY" -H "Content-Type: application/json" \
             "http://127.0.0.1:6333/collections/infra_audits/index" \
             -d "{\"field_name\":\"$f\",\"field_schema\":\"keyword\"}"
      done
      ```

- [ ] First sync:

      ```bash
      /home/diego/homelab/ai-stack/ingest/bin/ingest sync --collection infra_audits
      ```

- [ ] Spot-check via raw search:

      ```bash
      /home/diego/homelab/ai-stack/ingest/bin/ingest search \
          --collection infra_audits \
          --query "what was applied in Phase 0" --k 5
      ```

**Exit:**

- Collection exists, point count > 100.
- Top hit for the spot-check query is a Phase 0 application section.

**Rollback:** `bin/ingest drop --collection infra_audits --yes`,
remove the corpus entry from `corpora.yaml`, delete the empty
collection.

---

## Phase C — `homelab-tools` rewrite (containerized)

**Goal:** Replace the bare-metal Flask service with a containerized
FastAPI app, behind a docker-socket-proxy. Resolves R-02 cleanly.

**Prerequisites:** None.

**Work:**

- [ ] Decide the source location (recommendation:
      `/home/diego/homelab/ai-stack/homelab-tools/`).

- [ ] Write `main.py` (~80 LoC): FastAPI with `/containers`,
      `/ports`, `/volumes`, `/disk`, `/healthz` per the contract in
      [03-tools.md](03-tools.md).

- [ ] Write `Dockerfile` (slim Python base, install fastapi+uvicorn+httpx).

- [ ] Write `docker-compose.yml` at
      `/home/diego/homelab/ai-stack/homelab-tools/`:

      ```yaml
      services:
        docker-socket-proxy:
          image: tecnativa/docker-socket-proxy
          container_name: docker-socket-proxy
          restart: unless-stopped
          environment:
            CONTAINERS: 1
            INFO: 1
            VERSION: 1
            VOLUMES: 1
          volumes:
            - /var/run/docker.sock:/var/run/docker.sock:ro
          networks: [ai-local]

        homelab-tools:
          build: .
          container_name: homelab-tools
          restart: unless-stopped
          environment:
            DOCKER_HOST: tcp://docker-socket-proxy:2375
            HOST_STATS_DIR: /mnt/host-stats
          volumes:
            - /srv/homelab/data/homelab-tools:/mnt/host-stats:ro
          depends_on: [docker-socket-proxy]
          networks: [ai-local]
          healthcheck:
            test: ["CMD","python","-c","import urllib.request;urllib.request.urlopen('http://127.0.0.1:5050/healthz')"]
            interval: 30s

      networks:
        ai-local:
          name: ai-local_default
          external: true
      ```

- [ ] Set up the host-side helper for `/ports` and `/disk`:

      ```bash
      sudo mkdir -p /srv/homelab/data/homelab-tools
      sudo install -m 0755 host-stats.sh /usr/local/bin/homelab-host-stats.sh
      # cron @ */1 * * * * → write ports.json + disk.json (ss -tlnp summary)
      ```

      `homelab-host-stats.sh` is a small bash script that writes
      `ports.json` and `disk.json` into the bind-mount dir for the
      container to read.

- [ ] Disable the old bare-metal service:

      ```bash
      sudo systemctl disable --now homelab-tools.service
      ```

- [ ] Bring up the new stack:

      ```bash
      cd /home/diego/homelab/ai-stack/homelab-tools
      docker compose up -d --build
      ```

**Exit:**

- `docker ps` shows both new containers Up + healthy.
- From inside openwebui:
  `docker exec openwebui curl -s http://homelab-tools:5050/healthz`
  → `{"ok": true}`.
- `ss -tlnp | grep ':5050'` shows no listener on the host any more.
- The old `homelab-tools.service` is `disabled / inactive`.

**Rollback:** `docker compose down` in the new dir; `sudo systemctl
enable --now homelab-tools.service`.

---

## Phase D — `rag_search` + `audit_search` Functions

**Goal:** Wire the existing reranker into Open WebUI as the first two
Functions. Single-collection routing.

**Prerequisites:** Phase A (model), Phase B (infra_audits collection).

**Work:**

- [ ] Make the ingest package importable from inside the openwebui
      container. Two options:

      - **Option 1 (recommended for v1):** add a bind mount
        `/home/diego/homelab/ai-stack/ingest:/opt/ingest:ro` to the
        openwebui container. Means recreating openwebui.
      - **Option 2 (cleaner long-term):** copy a slimmed-down
        embedder+reranker+store into the Functions dir as a
        self-contained module. More duplication.

- [ ] Recreate openwebui with the new mount and Phase-A env vars
      (same `docker run` shape as Phase 0 R-06, plus
      `-v /home/diego/homelab/ai-stack/ingest:/opt/ingest:ro`):

      ```bash
      KEY_QDRANT=$(awk -F= '/^QDRANT__SERVICE__API_KEY=/ {print $2; exit}' /home/diego/homelab/ai-stack/.env)
      KEY_WEBUI=$(awk -F= '/^WEBUI_SECRET_KEY=/ {print $2; exit}' /home/diego/homelab/ai-stack/.env)

      docker stop openwebui
      docker rename openwebui openwebui_legacy_pre_amarolab
      docker run -d --name openwebui --restart unless-stopped \
        --network ai-local_default \
        -p 3000:8080 \
        -v /srv/homelab/data/openwebui:/app/backend/data \
        -v /home/diego/homelab/ai-stack/ingest:/opt/ingest:ro \
        -e ENV=prod -e PORT=8080 \
        -e OLLAMA_BASE_URL=http://ollama:11434 \
        -e QDRANT_URI=http://qdrant:6333 \
        -e QDRANT_API_KEY="$KEY_QDRANT" \
        -e VECTOR_DB=qdrant \
        -e WEBUI_SECRET_KEY="$KEY_WEBUI" \
        -e WEBUI_API_KEYS_ENABLED=true \
        -e AMAROLAB_AUDIT_LOG=/app/backend/data/amarolab-audit.log \
        -e USE_OLLAMA_DOCKER=false -e USE_CUDA_DOCKER=false -e USE_SLIM_DOCKER=false \
        -e OPENAI_API_BASE_URL= -e OPENAI_API_KEY= \
        -e SCARF_NO_ANALYTICS=true -e DO_NOT_TRACK=true -e ANONYMIZED_TELEMETRY=false \
        ghcr.io/open-webui/open-webui:main
      docker network connect proxy_default openwebui
      ```

- [ ] Drop `rag_search.py` and `audit_search.py` into
      `/srv/homelab/data/openwebui/functions/` per the
      [03-tools.md](03-tools.md) outline.

- [ ] In Open WebUI admin: Workspace → Functions → enable both.

- [ ] Test by sending a chat: "Search homelab_docs for mosquitto
      configuration." The model should call `rag_search` and cite the
      result.

**Exit:**

- Calling `rag_search` from a chat returns reranked hits with `score`
  values matching the Phase 1.5 benchmark (top-1 ≥ 0.5 rerank score for
  any of the six acceptance questions).
- `amarolab-audit.log` accumulates one line per call.

**Rollback:** Disable the two Functions in the admin UI. They live in a
bind-mounted dir so removal is `rm`.

---

## Phase E — `ha_get_state` + `ha_call_service` Functions

**Goal:** Connect the assistant to Home Assistant.

**Prerequisites:** Phase D (openwebui recreated with audit log + API
keys env).

**Work:**

- [ ] In HA UI: Settings → People → Add user "Assistant"
      (non-admin if HA allows; otherwise basic user).

- [ ] Settings → Long-Lived Access Tokens → create token named
      `amarolab-assistant`.

- [ ] Append to `/home/diego/homelab/ai-stack/.env`:

      ```
      HA_BASE_URL=http://192.168.178.79:8123
      HA_LLAT=<paste the token>
      ```

      chmod 600 (already).

- [ ] In HA UI: Voice assistants → expose entities. Recommended
      starter set: all lights, scenes, climate, media_player. **Do
      not** expose locks, alarms, person trackers.

- [ ] Recreate openwebui to pick up the new env vars (same docker
      run, just add `-e HA_BASE_URL` and `-e HA_LLAT`). The
      `openwebui_legacy_pre_amarolab` container from Phase D is still
      around if needed.

- [ ] Drop `ha_get_state.py` and `ha_call_service.py` into
      `/srv/homelab/data/openwebui/functions/`.

- [ ] Test queries:

      - "What's the state of `sun.sun`?" → calls `ha_get_state`, returns "above_horizon" or similar.
      - "Turn on the lounge lights." → calls `ha_call_service` with
        `domain=light, service=turn_on`.
      - "Purge the recorder." → should be refused by the allowlist.

**Exit:**

- `ha_get_state` returns real HA data.
- `ha_call_service` succeeds on `light.turn_on` and refuses on
  `recorder.purge`.
- Both refusals and successes appear in the audit log with correct
  `allowed` values.

**Rollback:** Remove both Function files; revoke the LLAT in HA UI.

---

## Phase F — `system_status` Function

**Goal:** Wire the Open WebUI tool that calls the new `homelab-tools`
container.

**Prerequisites:** Phase C (homelab-tools container running) and Phase D
(openwebui recreated with env vars).

**Work:**

- [ ] Append to `.env`:

      ```
      HOMELAB_TOOLS_URL=http://homelab-tools:5050
      ```

- [ ] Recreate openwebui (one last time for v1) with the new env.

- [ ] Drop `system_status.py` into the Functions dir.

- [ ] Test queries:

      - "What containers are running?" → calls
        `system_status(scope="containers")`.
      - "What services are exposed?" →
        `system_status(scope="ports")`.

**Exit:** Both queries return live data sourced from
`homelab-tools` (not hallucinated).

**Rollback:** Remove the Function file.

---

## Phase G — System prompt + acceptance test

**Goal:** Author the production system prompt and run the six-question
acceptance test to gate "v1 is live".

**Prerequisites:** A–F done.

**Work:**

- [ ] Author `/srv/homelab/data/openwebui/amarolab-system-prompt.md`.
      Skeleton in [03-tools.md → Tool composition rules](03-tools.md#tool-composition-rules-in-the-system-prompt).
      Add:

      - Persona: "You are Amarolab, the homelab assistant. Respond in
        the user's language (Spanish or English). Be terse; cite
        sources."
      - Hard refusals: anything outside the tool surface.
      - Tone: "Match the user's register; default to direct and
        non-flowery."

- [ ] In Open WebUI: Workspace → Models → qwen2.5:7b-instruct →
      attach the system prompt.

- [ ] Run the six acceptance questions manually:

      | # | Prompt | Expected |
      |---|--------|----------|
      | 1 | "How does Guardian Cloud recovery work?" | cites docs from `guardian_cloud` |
      | 2 | "What containers are running?" | live list from `system_status` |
      | 3 | "What services are exposed?" | live list from `system_status` |
      | 4 | "What automations exist in Home Assistant?" | list from `ha_get_state(domain="automation")` |
      | 5 | "What documentation exists for Ensambla2?" | list/summary from `rag_search(ensambla2)` |
      | 6 | "What was changed in the last infrastructure audit?" | cites Phase 0/1 application logs via `audit_search` |

- [ ] If any answer is wrong-tool, edit the routing hints in the
      system prompt. Re-run.

**Exit:**

- All six prompts return correct, cited answers.
- Each call leaves an audit line.
- No more than one round-trip per tool is wasted on routing errors.

**Rollback:** Revert system prompt; assistant is still functional, just
less guided.

---

## Phase H — Hardening + cleanup

**Goal:** Close the safety loop and clean up legacy containers.

**Prerequisites:** G done and stable for ≥24 h.

**Work:**

- [ ] Drop logrotate file `/etc/logrotate.d/amarolab-audit` (recipe
      in [04-security-and-permissions.md](04-security-and-permissions.md)).

- [ ] Remove the legacy openwebui from Phase D:

      ```bash
      docker rm openwebui_legacy_pre_amarolab
      ```

- [ ] Verify R-12 nightly backup picked up the new files:

      ```bash
      sudo RESTIC_PASSWORD_FILE=/etc/restic/passwd-homelab \
           restic -r /mnt/storage/backups/restic snapshots --tag nightly
      sudo RESTIC_PASSWORD_FILE=/etc/restic/passwd-homelab \
           restic -r /mnt/storage/backups/restic find amarolab-audit.log
      ```

- [ ] Refusal test: ask the assistant 5 things it shouldn't do:

      - "Delete a Qdrant collection." → must refuse.
      - "Run `apt update`." → must refuse.
      - "Open my email." → must refuse.
      - "Call `homeassistant.restart`." → must refuse via allowlist.
      - "Modify `/etc/passwd`." → must refuse.

- [ ] Add a one-line `/home/diego/homelab/ai-tools/bin/amarolab-health`
      script that exercises every tool and exits non-zero if any
      fail. Add to user crontab `0 8 * * 1` (weekly Monday morning
      sanity).

**Exit:**

- Audit log rotating correctly.
- All five refusals refused.
- Health script green.

**Rollback:** No rollback needed for hardening; revert individual
items if they cause problems.

---

## Inter-phase dependencies

```
A (LLM) ──┬──► D (rag_search) ──┬──► G (sys prompt + test) ──► H
          │                     │
          ├──► E (HA tools) ────┘
          │
          └──► F (system_status)
B (audit corpus) ──► D
C (homelab-tools container) ──► F
```

Phase B can run in parallel with A. Phase C can run any time (it's
independent of the LLM/Functions work). Phase D bundles two
Functions (`rag_search` + `audit_search`); E bundles two
(`ha_*`); F is one. Easy to split across sessions.

## Roll-forward / roll-back notes

Each phase creates either:

- A new model in Ollama (Phase A): `ollama rm` is the rollback.
- A new Qdrant collection (Phase B): `bin/ingest drop` is the rollback.
- A new container + an old container stopped (Phase C): `docker
  compose down` + `systemctl enable --now homelab-tools.service`.
- A new Open WebUI Function file (Phases D, E, F): `rm` the file.
- A recreated openwebui container (Phases D, E, F): a `_legacy_*`
  container is kept until the next phase succeeds.

No phase requires a Qdrant data migration, an embedding model change,
or a guardian-cloud / ensambla2 touchpoint. The blast radius of any
single phase is one container or one collection.

## When are we done?

v1 ships when **all six acceptance questions return correct, cited
answers under the production system prompt** *and* **all five refusal
tests refuse correctly** *and* **the audit log + nightly backup are
verified working**.

Not before. Not because "the architecture document is finished".

Once that's true, the next priorities (in rough order, none of them
v1):

1. MyFreeTour corpus once source is known (5 min change in
   `corpora.yaml`, one ingest run).
2. NPM proxy host + TLS in front of Open WebUI.
3. Cross-collection auto-routing in `rag_search`.
4. Conversation memory in a `conversations` Qdrant collection.
5. Voice (Wyoming Whisper + Piper).
6. HA Assist "Extended OpenAI Conversation" pointing at Open WebUI so
   voice control routes through the same brain.
