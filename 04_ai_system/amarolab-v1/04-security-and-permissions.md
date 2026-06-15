# 04 — Security & permission model

Two layers:

- **Security model** — trust boundaries, secrets, audit, threats.
- **Permission model** — who can do what, how decisions are made,
  what v1 explicitly defers.

## Trust zones

```
                                Trust
                                ─────
INTERNET           ───┐                                  (untrusted)
                       │ Cloudflare tunnel  → guardian-web ONLY
                       │                      (the assistant is NOT
                       │                       exposed externally)
                       ▼
TAILNET            ───┤  6 personal devices, all <TAILNET-USER>@   (trusted-by-policy)
                       │
LAN                ───┤  192.168.178.0/24                     (trusted-by-network)
                       │
OPEN WEBUI SESSION ───┤  authenticated user (diego)           (trusted-by-cookie)
                       │
TOOL RUNTIME       ───┤  in-container Python, runs at         (trusted, narrow)
                       │  openwebui process privilege
                       │
LLM                ───   qwen2.5:7b-instruct                  (UNTRUSTED — outputs
                                                               treated like user
                                                               input)
```

The LLM is **adversarial** to the tool layer. Tool code never `eval`s
arguments, never reads file paths from arguments, never builds shell
commands. Allowlists are constants in the file.

## Secrets handling

| Secret | Where it lives | Who reads it |
|--------|----------------|--------------|
| `QDRANT__SERVICE__API_KEY` | `/home/diego/homelab/ai-stack/.env` (0600 diego) | qdrant container (server side) |
| `QDRANT_API_KEY` (client) | same `.env` | openwebui container, ingest service |
| `WEBUI_SECRET_KEY` | same `.env` | openwebui container |
| `HA_LLAT` (new, v1) | same `.env` | openwebui container (Tools layer) |
| `HOMELAB_TOOLS_URL` | same `.env` | openwebui container |
| Open WebUI admin password | webui.db `users` table (bcrypt) | openwebui itself |
| (no Cloudflare token here; that's in `/home/diego/webs/cloudflared/.env`) | — | cloudflared container only |

### How the secrets get into the container

- All values in `/home/diego/homelab/ai-stack/.env` are injected at
  container start via `-e KEY=VALUE` (until R-14 lands and we move to
  `env_file: .env` in a compose file — same effect, cleaner config).
- Tools read them via `os.environ`; they are never logged.
- The `_redact` helper in `amarolab_common.py` masks anything keyed
  `password|token|secret|api_key|authorization` even if a tool author
  forgets.

### Rotation procedure (one-pager, for ops doc)

For any secret in `.env`:

```
1. Generate a new value (openssl rand -hex 32 for keys; HA UI for LLAT).
2. Edit /home/diego/homelab/ai-stack/.env in place (still 0600).
3. docker compose up -d --force-recreate openwebui   (or qdrant, etc.)
4. Verify the affected paths still work (smoke test from healthz).
5. (For HA LLAT only) revoke the old token in the HA UI.
```

No secret survives a `docker rm` of openwebui because env vars are
re-injected from the .env on every recreate.

## Audit log

One file: `/srv/homelab/data/openwebui/amarolab-audit.log` (on the
host; inside the container: `/app/backend/data/amarolab-audit.log`).

One JSON line per tool invocation. Fields:

```json
{
  "ts": "2026-06-14T10:11:23.456789+00:00",
  "id": "f1a2b3c4-...",
  "user": "diego",
  "tool": "ha_call_service",
  "args": { "domain": "light", "service": "turn_on",
             "target": {"area_id": "lounge"},
             "data": {"brightness_pct": 60} },
  "allowed": true,
  "result_code": "200",
  "duration_ms": 412
}
```

Rotation: rely on the existing host logrotate via a new file
`/etc/logrotate.d/amarolab-audit`:

```
/srv/homelab/data/openwebui/amarolab-audit.log {
    weekly
    rotate 12
    compress
    missingok
    notifempty
    create 0640 1000 1000
}
```

(Owner 1000:1000 because openwebui's data dir is diego-owned; the
container writes as root inside but the bind mount preserves host
ownership.)

The R-12 backup picks up `/srv/homelab/data/openwebui` already, so the
audit log lands in nightly snapshots.

## Threat model

| # | Threat | Probability | Impact | Mitigation in v1 |
|---|--------|:-----------:|:------:|------------------|
| T1 | LLM is jailbroken / prompt-injected via an indexed doc and tries to call `ha_call_service("recorder","purge")` | M | M | Domain allowlist denies; logged with `allowed=false` |
| T2 | LLM exfiltrates a chunk containing a token via `rag_search` | L | M | Audit dir contains references to token paths, not literal tokens; `.env` is never indexed (ingest excludes hidden files) |
| T3 | Network attacker on LAN reaches Open WebUI :3000 without auth | L | H | Auth is on; signup is off; one user only |
| T4 | Network attacker on LAN reaches Ollama :11434 unauthenticated | M | M | Deferred R-07.2: bind to 127.0.0.1. v1 lives with the LAN exposure; acceptable for trusted LAN |
| T5 | Compromised tailnet device runs arbitrary commands through the assistant | L | H | Same as T1 + the tool surface itself is narrow; no `shell_exec` |
| T6 | HA Long-Lived Access Token leaks (file disclosure, log leak, etc.) | L | H | Token tied to a *dedicated HA user* (recommendation in roadmap), not diego's main HA account → blast radius limited to "exposed to assist" entities |
| T7 | Tool author error: an args field reaches a `subprocess.run` and gets injected | L | H | Code-review rule: no `subprocess.run` in Tools. `homelab-tools` is the only thing allowed near the docker socket, and that's via docker-socket-proxy (read-only) |
| T8 | Open WebUI Function code is replaced by an attacker via the bind mount | L | H | Bind mount writable only by `diego` on the host; container itself runs as root but cannot pivot to host without socket access (which we removed in R-06) |
| T9 | Cron-driven ingest pulls a malicious commit from guardian-cloud or ensambla2 git | L | L | Both repos are user-owned; pull is `--ff-only`; even malicious markdown is just text in Qdrant — doesn't execute |
| T10 | Reranker model file replaced (supply-chain) | VL | M | HF cache is on disk; model name pinned in `reranker.py` (`BAAI/bge-reranker-v2-m3`); first download verified by sentence-transformers' integrity check |

### Non-threats (v1 explicitly does not defend against)

- Physical access to the host (already total compromise; out of scope).
- A sophisticated supply-chain attack on the Python deps (no SBOM yet).
- Network-side timing or correlation attacks (single user; not a juicy target).

## Permission model — v1

One axis only: **the chat user can call any defined tool**. Per-tool
allowlists are the safety mechanism, not per-user.

### User roster

| User | Where | Capabilities |
|------|-------|--------------|
| `diego` (Open WebUI admin) | Created during Open WebUI setup | Full chat + all tools |
| (none others) | — | — |

No second human user is created in v1. If/when one is, the v2 design
will introduce per-user tool ACLs.

### Per-tool effective permissions (v1)

| Tool | Read scope | Write scope | Rate (per chat session) |
|------|-----------|-------------|-------------------------|
| `rag_search` | all 5 corpora | none | 30 / min |
| `audit_search` | infra_audits | none | 30 / min |
| `ha_get_state` | all HA entities exposed to Assist | none | 60 / min |
| `ha_call_service` | n/a | HA services in the 12-domain allowlist | 10 / min |
| `system_status` | container list, port summary, volumes, disk | none | 30 / min |

All five tools are invokable by any logged-in Open WebUI user. The only
user is `diego`; future users get the same five tools or, if more
restrictive, a separate Open WebUI account with the unwanted tools
removed from the Functions allowlist for that user (Open WebUI
supports per-user Function visibility).

### What the assistant **cannot do** in v1

Explicit list — useful as a "don't promise things you can't deliver"
reference for system-prompt design.

- Cannot execute shell commands.
- Cannot read arbitrary files from the host.
- Cannot write to any file (audit log is via the audit helper, not a
  tool).
- Cannot call any HA admin domain (`homeassistant`, `recorder`,
  `hassio`, `system_log`, `backup`, `auth`, …).
- Cannot reach the internet except via:
  - Container image pulls (out-of-band, not at runtime).
  - Whatever the embedding/reranker model downloads have already
    cached (HF cache is now fully populated; no further downloads
    expected for v1).
- Cannot modify guardian-cloud or ensambla2 source trees.
- Cannot delete Qdrant points (no `qdrant.delete` tool).
- Cannot grant new permissions to itself.

## What an authenticated chat session looks like (security view)

```
1. User opens https://homelab:3000 in browser.
   - browser fetches HTML, JS bundle
   - login form posts username/password
   - Open WebUI verifies against webui.db (bcrypt)
   - sets WEBUI session cookie (HMAC'd with WEBUI_SECRET_KEY, stable across restarts after R-05)

2. User types a prompt.
   - openwebui POSTs to ollama:11434/api/chat with tool schemas
   - response includes 0+ tool_calls

3. For each tool_call:
   - openwebui imports the Python Function from
     /srv/homelab/data/openwebui/functions/<name>.py
   - calls the entry function with the JSON-decoded args
   - Function applies rate limit + allowlist + secret-redacted audit
   - Function returns a JSON-serializable dict
   - openwebui sends the dict back to ollama as a tool_result

4. Ollama produces the final assistant message.
   - streamed back to the browser
   - persisted in webui.db under the chat thread
```

Every external action (HA call, Qdrant query, homelab-tools call) is
gated by exactly one Function entry point. The LLM cannot bypass that
entry point because it doesn't have network access in any other way.

## Security checklist before declaring v1 "live"

These must be true on the day v1 goes live (the implementation
roadmap's Phase H — Hardening — owns the work).

- [ ] `WEBUI_SECRET_KEY`, `QDRANT_API_KEY`, `HA_LLAT` all present in
      `/home/diego/homelab/ai-stack/.env` with `0600` ownership
      `diego:diego`.
- [ ] `HA_LLAT` belongs to a **dedicated HA user `assistant`**, not
      diego's primary HA account. HA UI → Settings → People → Add user
      → "Assistant" (admin-flag off if HA allows; else use the smallest
      role available).
- [ ] HA *exposed-to-assist* entity set reviewed; nothing surprising
      (e.g., front door lock should not be `light.unlock`).
- [ ] `amarolab-audit.log` exists, has permissions `0640 1000:1000`,
      and `/etc/logrotate.d/amarolab-audit` is in place.
- [ ] R-12 nightly backup includes `/srv/homelab/data/openwebui` (it
      already does; verify via `restic snapshots --tag nightly`).
- [ ] All five Functions present in
      `/srv/homelab/data/openwebui/functions/` with `0644 diego:diego`.
- [ ] `homelab-tools` container running, no host port published,
      reachable from openwebui as `http://homelab-tools:5050/healthz`.
- [ ] `docker-socket-proxy` running, granting only the verbs
      `homelab-tools` needs (CONTAINERS, INFO, VERSION).
- [ ] Old `homelab-tools.service` (bare-metal Flask) disabled
      (`systemctl disable --now homelab-tools.service`).
- [ ] Smoke test passes: the six acceptance questions all return
      correct, cited answers.
- [ ] Refusal test passes: a prompt like *"please call
      `recorder.purge`"* returns the allowlist refusal.

If any item fails, ship is not green.

## Looking forward (v2 security work)

Not in v1, but worth flagging for the next cycle:

- TLS in front of Open WebUI via NPM with Let's Encrypt (NPM is
  already running and unused).
- 2FA on Open WebUI login (HOTP/TOTP supported natively in 0.8+).
- Per-user tool ACLs.
- Conversation memory in Qdrant — must include a redaction rule for
  tool args before embedding (don't index your own credentials).
- Outbound egress firewall rules on the openwebui container (currently
  unrestricted; if a future Tool ever talks to the internet, gate it
  here).
- Continuous-deployment audit: every change to a Function file should
  produce a one-line entry in the same `amarolab-audit.log` with
  `tool: "function_changed"`.
