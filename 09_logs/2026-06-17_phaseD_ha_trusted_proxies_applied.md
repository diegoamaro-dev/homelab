# Phase D — Home Assistant reverse-proxy trust patch — APPLIED

- **Date:** 2026-06-17
- **Ecosystem:** **AMAROLAB** — Personal Innovation Lab and Digital
  Infrastructure Ecosystem.
- **Assistant:** **AURORA** — Personal AI Assistant for the AMAROLAB
  ecosystem.
- **Independent project on AMAROLAB infrastructure:** **Guardian Cloud**
  — not affected by this work.
- **Status:** **APPLIED.** Home Assistant now trusts the
  `cloudflared-amarolab` connector as a reverse proxy, accepts the
  `ha.amarolab.es` host, and serves the login frontend over HTTPS.
- **Scope:** Single file edit on `configuration.yaml` adding `http:`
  reverse-proxy-trust block and `homeassistant.external_url`; one
  container restart of `homeassistant`. No other container, no other
  config, no secrets, no DNS, no tunnel ingress, no Open WebUI
  changes.
- **Driver:** Unblock Phase D-1.5 → G-D4. Before this patch,
  `https://ha.amarolab.es` (newly fronted by the `amarolab` tunnel)
  returned `HTTP 400 Bad Request` from HA — HA rejected the unfamiliar
  Host header / proxied request because no proxy was trusted and no
  external URL matched.

---

## 1. Pre-state

| Item | Value |
|---|---|
| `configuration.yaml` size | 265 bytes |
| `configuration.yaml` md5 | `90b21192bcd3043efdd67b6e4d9d4e36` |
| `configuration.yaml` content | Minimal default — `default_config`, `frontend`, includes for `automations`/`scripts`/`scenes`. **No `http:` block. No `homeassistant:` block override.** |
| `.storage/http` | `use_x_frame_options=true`, `ip_ban_enabled=true`, `server_port=8123`, `ssl_profile="modern"`, `cors_allowed_origins=["https://cast.home-assistant.io"]`, `login_attempts_threshold=-1` |
| `.storage/core.config` | `external_url=null`, `internal_url=null` |
| HA container | `Up`, `StartedAt=2026-06-17T00:19:32`, `restarts=0` |
| HA reachable via LAN | `http://192.168.178.79:8123/` → `HTTP 200` |
| HA reachable via Cloudflare | `https://ha.amarolab.es/` → **`HTTP 400 Bad Request`** |
| Aurora v1 pipeline | exists, set as preferred (per D-1.5 apply log) |
| `input_boolean.aurora_voice_canary` | exists, voice-exposed |

Pre-patch behaviour confirms the diagnosis from
[`./2026-06-17_phaseD_voice_pipeline.md`](2026-06-17_phaseD_voice_pipeline.md)
§2.4 and the read-only verification performed earlier this
session: HA was not configured to trust any reverse proxy, so the
HA frontend rejected the Cloudflare-fronted request.

---

## 2. Pre-change anchor

| Field | Value |
|---|---|
| Backup file | `/srv/homelab/homeassistant/configuration.yaml.bak.20260617-233516` |
| Backup md5 | `90b21192bcd3043efdd67b6e4d9d4e36` (matches pre-state) |
| Backup size | 265 bytes |
| Backup mode | `-rw-r--r--` (`0644`), owner `diego:diego` |

Per Lesson 005 — "make it work, validate, harden, document" — the
backup is the rollback anchor for this single-file change. Restic
snapshot `63c072f4` from D-1.5 remains the broader HA-state anchor.

---

## 3. What was changed

Single file: `/srv/homelab/homeassistant/configuration.yaml`.

Added two new top-level blocks, inserted after `default_config:` and
before `frontend:`. No existing lines were modified or removed.

```yaml
# Trust the Cloudflare-fronted reverse proxy for ha.amarolab.es.
# Trusted subnets:
#   172.18.0.0/16 — ai-local_default Docker bridge (cloudflared-amarolab egress)
#   127.0.0.1     — Docker userland-proxy loopback path
#   ::1           — IPv6 loopback equivalent
http:
  use_x_forwarded_for: true
  trusted_proxies:
    - 172.18.0.0/16
    - 127.0.0.1
    - ::1

# Canonical external URL fronted by Cloudflare.
homeassistant:
  external_url: https://ha.amarolab.es
```

### 3.1 Trusted subnets — rationale

| Subnet | Rationale |
|---|---|
| `172.18.0.0/16` | Subnet of the `ai-local_default` Docker bridge. The `cloudflared-amarolab` container egresses to HA from this subnet via the bridge gateway, so HA sees the connection as originating here. Verified in the new connector's audit log (this session). |
| `127.0.0.1` | If Docker's userland-proxy is enabled (default in this install), some flows present as coming from loopback rather than the bridge IP. Included defensively. |
| `::1` | IPv6 loopback equivalent of the above. |

The host LAN subnet (`192.168.178.0/24`) is **intentionally not
included** in `trusted_proxies` — the only reverse proxy that should
ever talk to HA is `cloudflared-amarolab` on `ai-local_default`.
Trusting the LAN broadly would let any LAN-side client spoof
`X-Forwarded-For`.

### 3.2 `external_url` — rationale

Setting `homeassistant.external_url: https://ha.amarolab.es` does
three things:

1. Tells HA the canonical external origin so it can validate the
   incoming `Host` header against an expected value (eliminating the
   400).
2. Causes HA to generate absolute URLs (e.g., companion-app push
   targets, webhook URLs surfaced in the UI) using the new HTTPS
   origin.
3. Locks `external_url` to the YAML value so it cannot be silently
   overridden by a UI edit (HA shows the value as YAML-managed).

`internal_url` is **deliberately left null** so HA continues to
auto-discover and use the LAN URL for LAN clients. The Restic
anchor + LAN test confirms LAN access stays functional.

---

## 4. Post-state

| Item | Value |
|---|---|
| `configuration.yaml` size | 740 bytes |
| `configuration.yaml` md5 | `888bef176fbc7e655f76302e529480e8` |
| HA container | restart issued via `docker restart homeassistant`; StartedAt advanced from `2026-06-17T00:19:32` → `2026-06-17T21:36:08`; `restarts=0` (clean restart, not crash); `running=true` |
| HA reachable via LAN | `http://192.168.178.79:8123/` → **`HTTP 200`**, title `Home Assistant` |
| HA reachable via Cloudflare | `https://ha.amarolab.es/` → **`HTTP 200`** (was 400), title `Home Assistant` |
| Aurora v1 pipeline | survived restart — still listed in `.storage/assist_pipeline.pipelines` |
| `input_boolean.aurora_voice_canary` | survived restart — still listed in `.storage/input_boolean` |
| Other YAML files | `automations.yaml`, `scenes.yaml`, `scripts.yaml` unchanged (size 2 / 0 / 0 bytes) |

Validation evidence captured this session:

- YAML parse-check with `PyYAML` (HA-tag-tolerant loader) confirms
  the new keys exist with the expected types and values.
- `docker logs --since 2m homeassistant` shows **zero**
  `ERROR / CRITICAL / Traceback / Invalid config / Setup failed`
  lines after the restart.
- `docker logs --since 2m homeassistant` shows **zero** warnings
  matching `http / proxy / external_url / trusted`.
- HTML content sniff on both LAN and HTTPS responses returns
  `<title>Home Assistant</title>` — the actual frontend, not an
  error page or a startup splash.

---

## 5. What this did NOT change

- Open WebUI, Ollama, Qdrant, Mosquitto, Zigbee2MQTT.
- The `aurora-whisper`, `aurora-piper`, `aurora-wakeword` containers.
- The Wyoming integrations inside HA (Whisper / Piper / openWakeWord).
- The HA Ollama integration.
- The `AURORA v1` Assist pipeline configuration (slot bindings,
  default-pipeline status).
- The `input_boolean.aurora_voice_canary` entity (state still
  `off`).
- The HA voice-exposure ACL — only the canary remains exposed.
- `webui.db` (Tools, model entry, system prompt, `meta.toolIds`).
- The existing `cloudflared` container (Guardian Cloud tunnel).
- `app.guardiancloud.app` and `api.guardiancloud.app` — both
  verified `HTTP 200` and `HTTP 404` (upstream-served) respectively
  at every checkpoint.
- The new `cloudflared-amarolab` container — running, 4/4 edges,
  unaffected by HA restart.
- The Cloudflare DNS records or tunnel ingress.
- Any secret. `secrets.yaml` not touched. `.secrets/` not touched.
- `internal_url` (deliberately left `null`).

---

## 6. Decisions implicitly closed

| ID | Outcome |
|---|---|
| HA-proxy-trust-deferred | **Closed.** The earlier decision (this session) to defer the HA reverse-proxy trust patch is **revoked** because `https://ha.amarolab.es` was returning `HTTP 400` from the HA-side rejection, blocking G-D4 in a different way than the original "Secure Context" block. Applied here to unblock G-D4. |
| HA `external_url` source of truth | YAML-managed (in `configuration.yaml`), not UI-managed (`.storage/core.config` still has `external_url=null`; HA prefers the YAML value). |
| HA `internal_url` posture | Auto-discover (left `null`). LAN access continues to work. |

---

## 7. Rollback

If anything regresses (e.g., HA logs surface a setup error not
caught above, or LAN access breaks under load):

```bash
# 1. Restore the pre-patch configuration.yaml
cp /srv/homelab/homeassistant/configuration.yaml.bak.20260617-233516 \
   /srv/homelab/homeassistant/configuration.yaml

# 2. Restart HA
docker restart homeassistant

# 3. Verify
curl -sS -o /dev/null -w "LAN  %{http_code}\n" --max-time 8 http://192.168.178.79:8123/
curl -sS -o /dev/null -w "HTTPS %{http_code}\n" --max-time 10 https://ha.amarolab.es/
```

After rollback, LAN returns `HTTP 200` and HTTPS returns to
`HTTP 400` — the pre-patch baseline. Restic snapshot `63c072f4`
remains the deeper rollback path.

---

## 8. Open / deferred items (unchanged from D-1.5)

| ID | Item | Carried to |
|---|---|---|
| **G-D4 over HTTPS** | End-to-end Read/Write/Verify/Restore against `input_boolean.aurora_voice_canary` from `https://ha.amarolab.es` from a Chromium browser (Secure Context now confirmable) | Next step after this patch |
| **G-D4 latency measurement** | Pipeline timeout tuning based on measured G-D4 latency | After G-D4 |
| `ai.amarolab.es` Public Hostname | Not yet bound to the `amarolab` tunnel | Operator action (not on the G-D4 critical path) |
| `cloudflared-amarolab` apply log | This deployment is not yet documented in its own apply log | Suggested next companion log |
| Amendments to `02_infrastructure/cloudflare/amarolab_dns_architecture.md` and `cloudflared_audit_2026-06-17.md` | Architecture shifted from "attach existing cloudflared to ai-local_default" to "separate amarolab tunnel + container" | Documentation sync, pre-D-1.9 |
| Overview triad (`00_overview/CURRENT_STATE.md` / `AMAROLAB_HANDOFF.md` / `ROADMAP.md`) | Will be updated at D-1.9 closeout per Lesson 005 | D-1.9 |

---

## 9. Reproducibility

To re-apply on a clean HA install behind the same `cloudflared-amarolab`
tunnel:

1. Confirm `cloudflared-amarolab` is on `ai-local_default` (172.18.0.0/16).
2. Back up `/srv/homelab/homeassistant/configuration.yaml`.
3. Insert the `http:` and `homeassistant:` blocks shown in §3 after
   the existing `default_config:` line.
4. `docker restart homeassistant`.
5. Run the verification block in §4 (LAN 200, HTTPS 200, no errors).

---

## 10. Related documents

- [`./2026-06-17_phaseD_voice_pipeline.md`](2026-06-17_phaseD_voice_pipeline.md)
  — D-1.5 apply log (DRAFT, pending G-D4); §2.5 describes this
  unblock path.
- [`../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md`](../04_ai_system/amarolab-v1/phase-d/05-validation-gates.md)
  — G-D4 gate definition.
- [`../02_infrastructure/cloudflare/amarolab_dns_architecture.md`](../02_infrastructure/cloudflare/amarolab_dns_architecture.md)
  — DNS architecture (now superseded in part by the separate-tunnel
  decision; see §8 of this log).
- [`../02_infrastructure/cloudflare/cloudflared_audit_2026-06-17.md`](../02_infrastructure/cloudflare/cloudflared_audit_2026-06-17.md)
  — Guardian Cloud tunnel audit (unchanged).
- [`../07_operations/lessons_learned.md`](../07_operations/lessons_learned.md)
  — Lessons 002 ("Validate before documenting"), 005 ("Make it
  work, validate, harden, document"), 015 ("Slow is smooth.
  Smooth is fast.").
