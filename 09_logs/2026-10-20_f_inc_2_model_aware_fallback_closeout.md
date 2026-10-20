# F-INC-2 — Model-Aware Ollama Fallback — Closeout

**Date:** 2026-10-20
**Type:** Final implementation / validation closeout.
**Status:** **DONE.**
**Production changed:** **yes.** `03_services/ollama-proxy/nginx.conf`, the Deployment Source,
was changed and reloaded gracefully. The container was not restarted or recreated.
**Gates:** **G-F2-0 through G-F2-7 all PASS.**

**Supersedes** the provisional operational status ("F-INC-2 OPEN") of
[`2026-10-20_f_inc_2_model_aware_fallback_provisional.md`](2026-10-20_f_inc_2_model_aware_fallback_provisional.md).
That record is **not rewritten**: it remains the dated record of what was true when it was
written (`PROJECT_RULES.md` → *Historical Documentation*). It carries the detailed design and the
G-F2-0…4/-7 evidence. This document adds G-F2-5/-6 and closes the item.

**Evidence labels:**
- **OBSERVED** — read-only checks, proxy logs and Open WebUI metadata, from the UM790.
- **OPERATOR-REPORTED** — the operator's own observation.

---

## 1. Problem

The 2026-10-20 Aurora incident
([`2026-10-20_aurora_ollama_drive_letter_incident.md`](2026-10-20_aurora_ollama_drive_letter_incident.md),
RESOLVED) exposed a resilience defect in `ollama-proxy`:
- it already handled **transport-level** Torre failure (`error | timeout | 502 | 503 | 504`);
- but a Torre that was **reachable** and did not expose the required model could return a
  successful empty catalogue (`200`, no models), or a model-level `404`, without causing any
  functional fallback.

The consequence: Aurora could disappear from Open WebUI, even though Aurora's persistent state
and a compatible `qwen2.5:7b-instruct` were still available on the UM790.

## 2. Binding architecture invariant

> If the preferred Torre RTX provider is reachable but does not expose Aurora's required base
> model, it is functionally unavailable for that model and inference must fall back to the
> UM790. Aurora must remain available in Open WebUI.

- **UM790:** the persistent Aurora / control-plane node. Aurora's identity, configuration and
  persistent state live there.
- **Torre:** a replaceable, on-demand GPU inference accelerator.
- **`qwen2.5:7b-instruct`:** Aurora's base inference model, **not Aurora itself**. It exists on
  both nodes with the same digest. The fallback serves the same model id, never a different one
  (*Hardware-Agnostic Platform* rule 2).

## 3. Implemented solution

Deployed `nginx.conf` sha256 `cd9a966e…` (committed baseline before F-INC-2: `92ab5984…`).

- **Catalogue:** `GET /api/tags` uses a dedicated upstream with **the UM790 first**
  (`<UM790_INTERNAL_ENDPOINT>`) and **Torre as backup** (`<TORRE_TAILSCALE_IP>`). The
  always-on floor (`hardware_agnostic_compute_architecture.md` §7.2) is authoritative for what
  is listed.
- **Inference still prefers Torre** (`/api/chat`, `/api/generate`, `/api/show`, …).
- **Transport fallback is unchanged:** `error timeout http_502 http_503 http_504`,
  `non_idempotent`.
- **`http_404` is now a next-upstream condition** for inference and model requests: Ollama's
  "model not found" passes the same request to the UM790.
- **A `404` does not mark Torre down.** nginx never counts it as a failed attempt, so fallback is
  **per request and per model**. The next request for a model Torre has still goes to Torre.
- **Bounded:** `proxy_next_upstream_tries 2`, `proxy_next_upstream_timeout 15s`, unchanged.
- **`http_500` is deliberately not included** (operator decision O-1).
- **Observability:** `ustatus=$upstream_status` in the access log. `404, 200` = model-missing
  fallback; `504, 200` / `502, 200` = transport fallback.
- **Not introduced:** no njs, no sidecar, no proxy redesign, no new container.

## 4. Safe deployment

- **G-F2-0 first:** a disposable test container (the same image, the draft mounted read-only,
  no published ports, removed afterwards) validated the routing against the real providers,
  using metadata requests only.
- **Single-file bind-mount inode hazard** identified in advance. A write that replaces the inode
  would leave the container reading the old file.
- **Production `nginx.conf` overwritten in place**, which kept the **inode unchanged**. Host,
  container and tested draft were verified to hash identically.
- **`nginx -t`** passed in the live container, then **`nginx -s reload`** (graceful) was run.
- **No container restart or recreation.** Same container, same start time, `RestartCount 0`,
  health `healthy` throughout.

## 5. Gate matrix

| Gate | What it proved | Evidence | Result |
|---|---|---|---|
| **G-F2-0** | The draft routes correctly against the real providers before any production change | OBSERVED | **PASS** |
| **G-F2-1** | Production apply in place and graceful reload with no restart; inode, hashes, identity and health verified | OBSERVED | **PASS** |
| **G-F2-2** | Torre healthy with the model: catalogue from the UM790, qwen2.5 inference through Torre only, streaming intact; Aurora visible and fast | OBSERVED + OPERATOR-REPORTED | **PASS** |
| **G-F2-3** | Torre reachable, model absent (`llama3.2:latest` stand-in): Torre `404` → UM790 `200`, including real CPU inference; Torre not marked down | OBSERVED | **PASS** |
| **G-F2-4** | Model absent everywhere: honest `404` after exactly two attempts, no loop | OBSERVED | **PASS** |
| **G-F2-5** | Torre offline: catalogue from the UM790, transport fallback, a real qwen2.5 Aurora chat served by the UM790; Aurora visible and answering | OBSERVED + OPERATOR-REPORTED | **PASS** |
| **G-F2-6** | Torre returns: qwen2.5 automatically back to Torre only, with no proxy intervention; normal fast Aurora | OBSERVED + OPERATOR-REPORTED | **PASS** |
| **G-F2-7** | Regression: Home Assistant-facing path healthy, all 20 containers unchanged, no nginx errors | OBSERVED | **PASS** |

## 6. Key routing evidence

Times are CEST, 2026-10-20. Endpoints are sanitized to `<TORRE>` / `<UM790>`.

**Healthy preferred path — G-F2-2 (OBSERVED, 10:50):**
```
POST /api/chat  qwen2.5   upstream=<TORRE>           ustatus=200        85.1 tok/s
```

**Reachable Torre, model absent — G-F2-3 (OBSERVED, 10:50–10:51):**
```
POST /api/show  llama3.2  upstream=<TORRE>, <UM790>  ustatus=404, 200
POST /api/chat  llama3.2  upstream=<TORRE>, <UM790>  ustatus=404, 200   real CPU inference
POST /api/show  qwen2.5   upstream=<TORRE>           ustatus=200        immediately after — Torre not marked down
```

**Model absent everywhere — G-F2-4 (OBSERVED, 10:51):**
```
POST /api/show  f-inc-2-absent:latest  status=404  upstream=<TORRE>, <UM790>  ustatus=404, 404   exactly two attempts, no loop
```

**Torre offline — G-F2-5**

OBSERVED:
```
11:04:46  GET  /api/tags  status=200 upstream=<UM790>          ustatus=200
11:04:51  [error] upstream timed out (110) while connecting to upstream   (<TORRE>; Torre temporarily disabled)
11:04:51  GET  /api/ps    status=200 upstream=<TORRE>, <UM790> ustatus=504, 200
11:06:49  POST /api/chat  status=200 upstream=<UM790>          ustatus=200   ut=111.9 s
```
- The 11:06:49 chat was a real Open WebUI Aurora chat: started 11:04:57; Open WebUI metadata
  shows assistant model `qwen2.5:7b-instruct`.
- It went straight to the UM790 because Torre had been marked down 6 s earlier
  (`max_fails=1 fail_timeout=10s`). That is the designed transport behaviour.
- Duration was **≈ 111.9 s** on the CPU path.

OPERATOR-REPORTED: Torre was offline; Aurora remained visible and answered, with the expected
slower CPU behaviour.

**The exact Torre power-off instant is not observed.** The logs bound the outage at roughly
11:04:46 → 11:06:50, but do not prove when Torre actually went off or came back.

**Torre recovery — G-F2-6**

OBSERVED:
```
11:06:59  POST /api/chat  status=200 upstream=<TORRE>  ustatus=200  ut=8.675   first recovered request
11:06:59  POST /api/chat  status=200 upstream=<TORRE>  ustatus=200  ut=0.746
11:07:00  POST /api/chat  status=200 upstream=<TORRE>  ustatus=200  ut=0.380
11:24:05  POST /api/chat  status=200 upstream=<TORRE>  ustatus=200  ut=16.467  new qwen2.5 chat, Torre only
```
- The first recovered request took **≈ 8.7 s**; the next ones took **≈ 0.38–0.75 s**.
- Later qwen2.5 chats went to Torre only, with no UM790 fallback.
- **No manual intervention:** no nginx reload, restart or proxy change. The same nginx worker
  started by the G-F2-1 reload kept serving, and the config hash and container identity were
  unchanged.
- Only one error-level line appears in the proxy log after the reload: the expected Torre
  connect timeout above.

OPERATOR-REPORTED: Torre was brought back; Aurora returned to normal, fast, RTX-backed behaviour.

## 7. Final result

**Aurora's availability is no longer coupled to Torre's ability to publish or serve
`qwen2.5:7b-instruct`.**

Validated degradation model:

| Situation | Result |
|---|---|
| Torre healthy, model present | RTX-backed Aurora |
| Torre reachable, required model absent | UM790 fallback |
| Torre unavailable | UM790 fallback |
| Torre recovers | Automatic return to RTX |

The intended user-visible degradation is now **a loss of performance, not Aurora's
disappearance**.

## 8. Remaining limitations / technical debt

None of these blocks F-INC-2 closure, and F-INC-2 is not expanded to solve them.

- **Mid-stream failure** cannot move upstream once response data has started. This is
  unchanged nginx behaviour.
- **`http_500` is not a fallback condition** (O-1). A Torre-side `500` still reaches the client.
- **The catalogue is the UM790's.** `/api/tags` exposes the current UM790 catalogue, including
  the additional existing models accepted under D-2.
- **Torre-only models are not listed.** A future model present only on Torre would not appear in
  that catalogue.
- **Ollama version skew:** Torre and the UM790 run different Ollama versions. This is
  pre-existing debt, and every fallback serves from the UM790's version.
- **`system_status` is not model-aware.** It reports Torre "reachable" on any `2xx` from
  `/api/tags`, even with an empty model list. This is separate debt
  (`hardware_agnostic_compute_architecture.md` §15).

## 9. Rollback

Not required, and not executed. If ever needed:
1. Restore the committed baseline `nginx.conf` **in place**, keeping the inode.
2. Run `nginx -t` in the container.
3. `nginx -s reload` (graceful).

No restart or recreation is needed.

## 10. Closure

**F-INC-2 DONE.**

Validated on production:
- the implementation itself;
- model-missing fallback;
- full Torre-outage fallback;
- Aurora's continuity in Open WebUI throughout;
- automatic recovery to RTX.

F-INC-1 (drive-letter dependency) and F-INC-3 (Torre recovery runbook) remain **OPEN** and are
unaffected by this closure.
