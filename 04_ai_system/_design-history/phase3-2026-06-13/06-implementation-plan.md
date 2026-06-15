# 06 — Implementation plan

Seven phases. Each one has an explicit **goal**, **work items**, **exit
criteria**, and **rollback**. Total estimated effort: 7–10 working days
spread across 2–3 weeks. Phases can be split across sessions.

> Nothing is built or installed by this document. Each phase becomes its
> own ticket / session when you decide to start.

## Phase 0 — Prerequisites (½ day)

**Goal:** Land Phase 2 fixes that the assistant *requires*. (Other Phase
2 work can be parallel.)

**Work:**
- [ ] R-04 Mosquitto config restored (so HA can talk to Zigbee2MQTT, so
      the assistant can see Zigbee entities).
- [ ] R-07 Qdrant rebound to `127.0.0.1` + API key set.
- [ ] R-05 `WEBUI_SECRET_KEY` pinned (so HA tokens stored in Open WebUI
      survive container restarts).
- [ ] R-14 partial: write the `ai-stack/docker-compose.yml` from the
      R-06 plan (without recreating yet, just file on disk).
- [ ] R-12 first nightly backup observed succeeding.

**Exit:**
- `docker ps` shows no restart loops.
- `curl -H "api-key: $KEY" http://127.0.0.1:6333/collections` succeeds.
- `docker exec openwebui printenv WEBUI_SECRET_KEY | wc -c` returns 65.
- `restic snapshots` shows ≥ 1 snapshot.

**Rollback:** Phase 2 fixes already have their own rollback steps.

---

## Phase 1 — RAG foundation (1–2 days) ✅ APPLIED 2026-06-13

> **Status:** Applied 2026-06-13 / 2026-06-14. See full application log
> in [PHASE-1-APPLIED.md](PHASE-1-APPLIED.md). 1 377 points indexed
> across three of four collections; nightly cron at 02:30 installed.

**Goal:** Stand up the new Qdrant collections + embedding model + minimal
ingestion CLI. End state: you can run `homelab-rag-ingest sync` once and
get answers via raw Qdrant queries.

**Work:**
- [ ] Confirm the four corpora paths. Resolve the MyFreeTour open
      question (see [README](README.md)). For now ingest 3 of 4 if
      MyFreeTour can't be pinned down.
- [ ] Create skeleton repo `/srv/homelab/compose/homelab-rag-ingest/` with
      `pyproject.toml`, `conf/corpora.yaml`, the four modules listed in
      [03-integrations.md §5](03-integrations.md).
- [ ] Pin embedding model: `intfloat/multilingual-e5-small` (~120 MB).
      Download once into the existing
      `/srv/homelab/data/openwebui/cache/embedding/models/` so Open
      WebUI and ingestion share it.
- [ ] Create the four Qdrant collections via curl (commands in
      [03-integrations.md §5](03-integrations.md)).
- [ ] Implement `connectors/fs.py` and `connectors/git.py` with the
      include/exclude rules.
- [ ] Implement markdown-aware chunker (`langchain_text_splitters` or
      hand-rolled).
- [ ] Implement embedder (in-process `sentence-transformers`, batch 32).
- [ ] Implement Qdrant store wrapper (upsert by deterministic point ID
      derived from `sha256(collection+source_rel+chunk_index)`).
- [ ] Implement `cli.py sync [--collection ...]`.
- [ ] First ingestion run; report in stdout: corpora → files → chunks.

**Exit:**
- `homelab-rag-ingest sync --collection homelab_docs` completes with no
  errors.
- `curl -H "api-key: $KEY" http://127.0.0.1:6333/collections/homelab_docs`
  reports `points_count > 1000`.
- Manual search returns relevant docs:

  ```bash
  # Embed a query and POST it to Qdrant; verify scores
  homelab-rag-ingest search --collection homelab_docs \
      --query "how is mosquitto configured" --k 5
  ```

**Rollback:** Drop the new Qdrant collections; uninstall the ingest
package. Existing Open WebUI collections are untouched.

---

## Phase 2 — External corpora wired (1 day) ✅ 3-of-4 APPLIED 2026-06-13

> **Status:** Folded into Phase 1 in practice. `guardian_cloud` and
> `ensambla2` are populated via the git connector. `myfreetour` left
> disabled in `conf/corpora.yaml` pending source path from user.

**Goal:** All four collections populated.

**Work:**
- [ ] Confirm MyFreeTour source path or git URL.
- [ ] Add `connectors/git.py` `git pull --ff-only` step in front of the
      filesystem walker.
- [ ] First full ingest of all four corpora.
- [ ] Capture run report; tune include/exclude as needed (typically:
      add language filter for `.html` if too noisy, skip large CSV
      dumps, etc.).
- [ ] Install cron entry at 02:30:

      ```
      30 2 * * * diego /opt/homelab-rag-ingest/bin/ingest sync >> /var/log/homelab-rag-ingest.log 2>&1
      ```

**Exit:**
- `points_count > 0` for all four collections.
- `tail /var/log/homelab-rag-ingest.log` after the cron fires shows a
  clean run.

**Rollback:** `homelab-rag-ingest drop --collection <name>` removes the
collection's points without affecting others.

---

## Phase 3 — Tool-calling LLM (½ day)

**Goal:** Switch the default Ollama model to a tool-capable one and
verify function calling end to end at the Ollama API level.

**Work:**
- [ ] `docker exec ollama ollama pull qwen2.5:7b-instruct`
- [ ] `docker exec ollama ollama pull qwen2.5:3b-instruct`
- [ ] (Optional) `docker exec ollama ollama rm llama3:latest phi3:latest`
      to free ~6.8 GB.
- [ ] Smoke test:

      ```bash
      curl -s http://127.0.0.1:11434/api/chat -d '{
        "model": "qwen2.5:7b-instruct",
        "messages": [{"role":"user","content":"what time is it?"}],
        "tools": [{
          "type":"function",
          "function":{
            "name":"time_now",
            "description":"Get current time in Europe/Madrid.",
            "parameters":{"type":"object","properties":{}}
          }
        }],
        "stream": false
      }' | jq '.message'
      ```

      Expected: assistant emits a `tool_calls` entry naming `time_now`.

- [ ] Update Open WebUI default model in admin settings.

**Exit:**
- Open WebUI new-chat default = `qwen2.5:7b-instruct`.
- Smoke-test curl shows tool call (not hallucinated time).

**Rollback:** Revert default model to `llama3.2:latest`. Models stay on
disk.

---

## Phase 4 — Open WebUI Tools (1–2 days)

**Goal:** Three working tools exposed to the LLM: `ha_get_state`,
`ha_call_service`, `rag_search`.

**Work:**
- [ ] Generate HA Long-Lived Access Token via the HA UI; store in
      `.env` (procedure in [03-integrations.md](03-integrations.md)).
- [ ] Open WebUI admin → Workspace → Tools/Functions → create three
      Python functions matching the contracts in
      [02-data-flow.md](02-data-flow.md). Test each independently.
- [ ] Add allowlists, rate limits, and audit-log writes
      (`/var/log/homelab-assistant-audit.log`, logrotate weekly,
      12-week retention).
- [ ] Author the system prompt outlined in
      [04-security-model.md](04-security-model.md).
- [ ] Iterative QA:
      - "what's the temperature in the office?" → uses `ha_get_state`.
      - "turn on the lounge lights" → uses `ha_call_service`.
      - "delete all my data" → refused (no matching tool).
      - "how is mosquitto configured?" → uses `rag_search`.
      - "rebuild ensambla2's auth flow" → cites
        `ensambla2/AUTH_SYSTEM.md`.

**Exit:**
- All four QA prompts above pass.
- Audit log records each tool call.
- No domain outside the allowlist can be called (test by asking it to
  call `recorder.purge` — must be refused).

**Rollback:** Disable the three functions in the admin UI; the LLM is
back to pure-chat mode.

---

## Phase 5 — HA Assist integration (1 day)

**Goal:** The same assistant accessible via HA Assist (voice optional in
this phase).

**Work:**
- [ ] Open WebUI admin → API keys → create `ha-assist` key.
- [ ] Install HACS in HA (if not already), then "Extended OpenAI
      Conversation".
- [ ] Configure the integration:
      - Base URL: `http://192.168.178.79:3000/openai/v1`
      - Model: `qwen2.5:7b-instruct`
      - API key: `<ha-assist>`
- [ ] HA → Settings → Voice assistants → Add pipeline "Assistant":
      Conversation agent = Extended OpenAI Conversation. Set as default.
- [ ] Expose entities to Assist:
      - All lights, switches, scenes, climate entities, media_player.
      - **Do not** expose: device_tracker, person, anything in
        `recorder` / `system_log` / `hassio`.

**Exit:**
- HA Assist debug shows the same tool calls the Open WebUI side sees.
- Voice prompt from the mobile HA app produces a sensible reply.

**Rollback:** Revert HA pipeline to the previous (`home_assistant`
built-in) conversation agent; remove HACS integration.

---

## Phase 6 — Voice (optional, 1 day)

**Goal:** Hands-free voice with local STT + TTS. Skip if you don't need
voice in v1.

**Work:**
- [ ] Add a new `voice` stack with two containers:

      ```yaml
      services:
        whisper:
          image: rhasspy/wyoming-whisper:latest
          container_name: wyoming-whisper
          restart: unless-stopped
          command: ["--model","base","--language","es"]
          volumes:
            - /srv/homelab/data/wyoming/whisper:/data
          networks: [ha-voice]

        piper:
          image: rhasspy/wyoming-piper:latest
          container_name: wyoming-piper
          restart: unless-stopped
          command: ["--voice","es_ES-sharvard-medium"]
          volumes:
            - /srv/homelab/data/wyoming/piper:/data
          networks: [ha-voice]

      networks:
        ha-voice:
          name: ha-voice_default
      ```

- [ ] In HA: install **Wyoming Protocol** integration; point at the two
      containers by hostname.
- [ ] In the HA Assist pipeline created in Phase 5, set STT = Whisper,
      TTS = Piper.

**Exit:**
- Pressing "talk" on the HA mobile app produces a transcribed query,
  routes through the assistant, and speaks the reply back.

**Rollback:** Switch STT/TTS in the pipeline back to "none"; the text
pipeline still works.

---

## Phase 7 — Hardening & operational tasks (½–1 day)

**Goal:** Backups cover new state, observability is good enough, and
the assistant fits the security model documented in
[04-security-model.md](04-security-model.md).

**Work:**
- [ ] Update the R-12 backup script to include:
      - `/srv/homelab/data/openwebui/functions/` (the tools)
      - `/opt/homelab-rag-ingest/` (the ingestion service)
      - `/var/log/homelab-assistant-audit.log*`
      - `/srv/homelab/data/wyoming/` (if voice enabled)
- [ ] Apply R-10 (UFW). Now is the right moment because the assistant's
      port layout is settled.
- [ ] Apply R-06 (Open WebUI docker socket): now that the assistant
      doesn't need it, the socket can be unmounted cleanly.
- [ ] Add a Grafana / Uptime-Kuma probe (optional) for:
      - `GET http://127.0.0.1:11434/api/version`
      - `GET http://127.0.0.1:6333/`
      - `GET http://127.0.0.1:3000/api/version`
      - `GET http://192.168.178.79:8123/api/`
- [ ] Document the assistant in `/home/diego/homelab/04_ai_system/` so
      it appears alongside the rest of the homelab docs (eat-your-own-
      dog-food: it'll be in `homelab_docs` next ingest run).

**Exit:**
- One full week of clean nightly backup + nightly RAG sync runs.
- Audit log non-empty, reviewed once.
- UFW status verbose shows only the documented allow rules.

**Rollback:** N/A — these are tightening steps only.

---

## Effort summary

| Phase | Effort | Calendar |
|-------|-------:|---------:|
| 0 — Prerequisites | ½ d | day 1 |
| 1 — RAG foundation | 1–2 d | days 2–3 |
| 2 — External corpora | 1 d | day 4 |
| 3 — Tool-calling LLM | ½ d | day 5 |
| 4 — Open WebUI Tools | 1–2 d | days 5–6 |
| 5 — HA Assist | 1 d | day 7 |
| 6 — Voice (optional) | 1 d | day 8 |
| 7 — Hardening | ½–1 d | day 9–10 |
| **Total** | **~7–10 days** | **2–3 weeks elapsed** |

## Decision points before starting

These are the choices you'll need to make at the start of Phase 1. The
defaults in this document are recommendations, not mandates:

1. **MyFreeTour source.** Path, git URL, or "skip for v1, add later".
2. **Embedding model.** Stay with `all-MiniLM-L6-v2` for now or switch
   to `multilingual-e5-small`? (Recommended: switch.)
3. **Default LLM.** `qwen2.5:7b-instruct` (recommended) or
   `llama3.1:8b-instruct`?
4. **Voice in v1?** Yes / no — affects Phase 6 inclusion.
5. **Where does the ingestion service live?** Bare-metal systemd unit
   or its own container? (Recommended: container, so it backs up and
   restarts cleanly with the rest of the stack.)

## What success looks like

A normal day-in-the-life:

- 02:30 — Cron triggers `homelab-rag-ingest sync`; ~30 s of CPU; the
  morning briefing reflects yesterday's repo changes.
- 03:00 — Restic backup includes new vector store and tool definitions.
- 08:15 — Voice: *"Hey assistant, what's the office like?"* →
  `ha_get_state(area=office)` → "23°C, lights on, motion detected
  2 minutes ago."
- 11:30 — Chat (laptop): *"How do I configure mosquitto auth?"* →
  `rag_search(collection=homelab_docs)` → answer cites
  `03_services/zigbee2mqtt_setup.md`.
- 14:00 — Chat (mobile): *"Refresh the ensambla2 RAG"* — no tool match,
  the assistant explains how to invoke the ingestion CLI.
- 22:00 — *"Goodnight."* → `ha_call_service(scene.turn_on, target=
  scene.goodnight)` → lights down, climate to night setpoints.

All decisions logged in `/var/log/homelab-assistant-audit.log`; nothing
leaves the LAN/tailnet.
