# F-0 Finding — AF-07: Torre Ollama Live Probe Reachability

**Date:** 2026-06-28  
**Phase:** F-0 Behavioral Audit  
**Finding reference:** AF-07 (from `04_ai_system/phase_f_architecture.md` §11)  
**Status:** VALIDATED — direct container probe confirmed; no fallback required

---

## Context

AF-07 validates the reachability assumption for the `system_status` tool's live Torre probe. The Phase F architecture specifies that `system_status` performs a live HTTP probe of the Torre Ollama endpoint and returns Torre reachability as part of its structured response. This probe runs inside the `openwebui` container, which is not on the host network. The question is whether the container can reach Torre's Tailscale IP directly, or whether a host-side intermediary (e.g., a `torre_status.json` file written by a host cron job) is required.

---

## Endpoint identification

From `03_services/ollama-proxy/nginx.conf`:

```
upstream ollama_pool {
    server 100.91.154.124:11434 max_fails=1 fail_timeout=10s;  # Torre (primary)
    server ollama:11434 backup;                                  # UM790 (fallback)
}
```

**Torre Ollama endpoint: `http://100.91.154.124:11434`**  
`100.91.154.124` is Torre's Tailscale IP. This is a Tailscale VPN address reachable only via the Tailscale mesh.

---

## Network topology

The `openwebui` container is on the `ai-local_default` bridge network:
- Container IP: `172.18.0.10` (eth0, `ai-local_default`)
- Also on `proxy_default`: `172.19.0.3` (eth1)
- Default gateway: `172.18.0.1` = the UM790 Docker bridge = UM790 host kernel

The UM790 host has a `tailscale0` interface:
```
tailscale0 — inet 100.68.180.69/32
```

Host routing table (table 52) includes:
```
100.91.154.124 dev tailscale0
```

**Routing path: container → docker bridge (172.18.0.1) → UM790 host kernel → tailscale0 → Torre**

The container inherits the host's Tailscale routing transparently via the bridge. No Tailscale client inside the container is required. No `--network host` is required.

---

## Reachability probes

### Host → Torre

```
curl -s -o /dev/null -w "HTTP %{http_code} — connect_time=%{time_connect}s total=%{time_total}s" \
  --max-time 10 http://100.91.154.124:11434/
```
Result: **HTTP 200 — connect_time=0.000905s total=0.001568s**

### Container (openwebui) → Torre

```
docker exec openwebui curl -s -o /dev/null \
  -w "HTTP %{http_code} — connect_time=%{time_connect}s total=%{time_total}s" \
  --max-time 10 http://100.91.154.124:11434/
```
Result: **HTTP 200 — connect_time=0.000899s total=0.001660s**

Container latency is indistinguishable from host latency — the docker bridge adds no measurable overhead.

### Probe endpoint characterisation

| Endpoint | Response body | HTTP | Size | Total time |
|---|---|---|---|---|
| `GET /` | `Ollama is running` (plaintext) | 200 | 17 B | 1.5 ms |
| `GET /api/version` | `{"version":"0.30.10"}` (JSON) | 200 | 21 B | 1.3 ms |
| `GET /api/tags` | JSON model list | 200 | ~300 B | ~1.7 ms |

### Probe tool availability in container

```
docker exec openwebui which curl
→ /usr/bin/curl (curl 7.88.1)

docker exec openwebui which python3
→ /usr/local/bin/python3
```

Both `curl` (shell probe) and `requests` (Python probe) are available inside the `openwebui` container. The `system_status` tool is a Python Open WebUI Tool; it will use the `requests` library already available in the container.

---

## Recommended probe design for `system_status` tool

**Endpoint:** `GET http://100.91.154.124:11434/api/version`

Rationale:
- Returns structured JSON (`{"version": "..."}`) — confirms Ollama is actually serving responses, not just accepting TCP connections
- 21-byte response — the lightest meaningful structured probe
- Sub-2ms round-trip — adds negligible latency to `system_status` tool call
- No model enumeration — no I/O to the model file system

**Probe implementation pattern (Python / requests):**

```python
import requests

TORRE_URL = "http://100.91.154.124:11434"
PROBE_TIMEOUT = 5  # seconds

def probe_torre() -> dict:
    try:
        r = requests.get(f"{TORRE_URL}/api/version", timeout=PROBE_TIMEOUT)
        if r.status_code == 200:
            return {"reachable": True, "version": r.json().get("version"), "latency_ms": round(r.elapsed.total_seconds() * 1000, 1)}
        return {"reachable": False, "reason": f"HTTP {r.status_code}"}
    except requests.exceptions.ConnectTimeout:
        return {"reachable": False, "reason": "connect_timeout"}
    except requests.exceptions.ConnectionError:
        return {"reachable": False, "reason": "connection_error"}
```

The 5-second timeout is conservative — actual latency is ~1 ms when Torre is up. On Torre offline, the `ollama-proxy` nginx config uses `proxy_connect_timeout 5s` and marks Torre down after 1 failure for 10s. A 5-second `system_status` probe timeout matches this window and will not make the tool call feel hung.

---

## Fallback assessment

The architecture specified a contingency:

> If container-to-Torre reachability fails, document the required fallback: host-side `torre_status.json` producer instead of direct container probe.

**Fallback is not required.** The `openwebui` container reaches `100.91.154.124:11434` directly and successfully. The routing is transparent: Docker bridge → UM790 kernel → `tailscale0`. This routing is unconditional — it does not require Torre to be the active Ollama upstream in the proxy, and it does not depend on the `ollama-proxy` container at all. The probe goes directly to Torre's Ollama, bypassing the proxy.

---

## Important distinction: probe target vs. proxy

The `system_status` live probe connects **directly to Torre at `100.91.154.124:11434`**, not to `ollama-proxy`. This is intentional:
- The probe's purpose is to determine whether Torre itself is reachable.
- Probing `ollama-proxy` would return a 200 even when Torre is offline (the proxy would return a 200 from the UM790 fallback, masking the Torre outage).
- The `system_status` tool should clearly distinguish "Torre up" from "Torre down, UM790 fallback active."

---

## AF-07 disposition

**VALIDATED.** The `openwebui` container can reach `http://100.91.154.124:11434` directly via the Docker bridge → UM790 host → Tailscale routing path. A host-side intermediary is not required.

**`system_status` tool probe spec (confirmed):**
- Target: `http://100.91.154.124:11434/api/version`
- Timeout: 5 seconds
- Method: `requests.get()` inside the Tool (Python)
- Response: JSON `{"version": "..."}` — confirms Ollama is serving
- Error handling: `ConnectTimeout` → `{"reachable": false, "reason": "connect_timeout"}`

---

## Cleanup confirmation

Read-only audit. No containers modified. No network changes. No files created in homelab repo. No git operations performed.
