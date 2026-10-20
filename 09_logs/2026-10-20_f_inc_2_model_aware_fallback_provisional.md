# F-INC-2 — Model-aware fallback in `ollama-proxy` (provisional)

**Date:** 2026-10-20
**Type:** Provisional implementation/evidence record.
- This is **NOT a closeout document**.
- It is a dated record: later results go in later documents, and this one is not rewritten
  (`PROJECT_RULES.md` → *Historical Documentation*).

**Status:** **F-INC-2 OPEN.**
- G-F2-0, -1, -2, -3, -4 and -7 PASS.
- **Remaining gates: G-F2-5 and G-F2-6**, both passive (§9).

**Production changed:** **yes.** `03_services/ollama-proxy/nginx.conf`, the Deployment Source,
was changed and reloaded gracefully. The container was not restarted or recreated.

**Git:** the `nginx.conf` change and this record are **uncommitted** at the time of writing.

**Evidence labels:**
- **OBSERVED** — read-only checks or proxy logs, from the UM790.
- **OPERATOR-REPORTED** — the operator's own observation.

---

## 1. Context

On 2026-10-20 Aurora disappeared from Open WebUI. Torre's Ollama was **reachable** but served an
empty model catalogue, because its model volume had moved off its drive letter
([`2026-10-20_aurora_ollama_drive_letter_incident.md`](2026-10-20_aurora_ollama_drive_letter_incident.md),
RESOLVED).

**The resilience defect behind it:** `ollama-proxy` failed over only on **transport** failure
(`error | timeout | 502 | 503 | 504`). Torre's `200` with an empty `/api/tags`, and its `404`
for the model, both counted as success. So:
- the catalogue hid Aurora's base model, and
- inference was never offered to the UM790.

ROADMAP tracks the fix as **F-INC-2** (HIGH) under *Post-RTX-1 follow-ups*.

## 2. Objective — binding invariant

> If the preferred Torre RTX provider is reachable but does not expose Aurora's required base
> model, it must be treated as functionally unavailable for that model and inference must fall
> back to the UM790. Aurora must remain available in Open WebUI.

The fallback must serve the **same model id**, never a different one (*Hardware-Agnostic
Platform* rule 2; `hardware_agnostic_compute_architecture.md` §4.3, §7.1).

## 3. Architecture (unchanged)

- **UM790:** the persistent Aurora / control-plane node. Aurora's identity, configuration and
  persistent state live there.
- **Torre:** a replaceable, on-demand GPU inference accelerator.
- **`qwen2.5:7b-instruct`:** Aurora's base inference model, **not Aurora itself**. It exists on
  both nodes with the same digest (OBSERVED 2026-10-20).

## 4. Implementation

All changes are in `03_services/ollama-proxy/nginx.conf`.
- Committed baseline: sha256 `92ab5984…`.
- Deployed: sha256 `cd9a966e…`.

| Change | Behaviour |
|---|---|
| New `upstream ollama_catalogue`: `<UM790_INTERNAL_ENDPOINT>` (`ollama:11434`) first, `<TORRE_TAILSCALE_IP>:11434` as `backup` | The UM790 — the always-on floor (`hardware_agnostic_compute_architecture.md` §7.2) — is authoritative for the model catalogue. Torre answers the catalogue only if the UM790 Ollama is unavailable |
| New `location = /api/tags` → `ollama_catalogue` | Exact match. Every model listed is servable by the floor. A reachable-but-empty Torre can no longer hide Aurora's base model |
| `http_404` added to `proxy_next_upstream` in `location /` | Inference and metadata (`/api/chat`, `/api/generate`, `/api/show`, …) **still prefer Torre**. Ollama's "model not found" `404` passes the same request, with the same model id, to the UM790 |
| Unchanged | Transport-error fallback, `non_idempotent`, `proxy_next_upstream_tries 2`, `proxy_next_upstream_timeout 15s`, `proxy_buffering off`, all timeouts, `/healthz` |
| Deliberately **not** added | `http_500` (operator decision O-1) |
| `ustatus=$upstream_status` added to `log_format` | Each attempt's status is logged. `404, 200` = model-missing fallback; `502, 200` / `504, 200` = transport fallback |
| Not introduced | No proxy redesign, no sidecar, no njs, no new container |

**Why a 404 does not mark Torre down.**
- nginx never counts a `404` as an unsuccessful attempt, so `max_fails` / `fail_timeout` are not
  touched.
- Fallback is therefore **per request and per model**. A request for a model Torre lacks goes to
  the UM790, while the next request for a model Torre has still goes to Torre.
- A transport failure, by contrast, marks Torre down for `fail_timeout=10s`, as before.

The design followed operator decisions D-1 (plain nginx), D-2 (UM790-authoritative catalogue
accepted), D-3 (`llama3.2:latest` as the missing-model stand-in), O-1 (no `http_500`) and O-2
(`$upstream_status`).

## 5. Deployment method

- **Single-file bind-mount hazard.** `nginx.conf` is bind-mounted as a single file. A write that
  replaces the inode (rename-on-save, `sed -i`) would leave the container reading the old file,
  and a reload would then silently keep the old configuration.
- **Applied in place:** `cat <tested draft> > 03_services/ollama-proxy/nginx.conf` (truncate +
  write).
- **Checks, all OBSERVED:**
  - host and container inode `3956437` both before and after: **unchanged**;
  - host, container and tested-draft sha256 all `cd9a966e…`: **equal**;
  - `nginx -t` inside the live container: `syntax is ok` / `test is successful`;
  - `nginx -s reload` (graceful, 2026-10-20 10:47:44 CEST): rc 0. The master process stayed
    PID 1 and a new worker replaced the old one;
  - the container was **not** restarted or recreated: same id, same start time,
    `RestartCount 0`, `healthy`;
  - the new log format was active from the first request after the reload.

## 6. Validation evidence

Requests went through the production proxy's host-published endpoint (the path Home Assistant
uses), unless noted otherwise. IPs are replaced by `<TORRE>` / `<UM790>`.

### G-F2-0 — disposable pre-production test — PASS (OBSERVED, 10:44 CEST)

- **Setup:** the identical image, on `ai-local_default`, with the draft mounted read-only and no
  published ports. Container `f-inc-2-g0`, removed afterwards.
- **Requests:** metadata only.
- **Results:**
  - `nginx -t` succeeded;
  - routing was identical to G-F2-2…4 below;
  - the live proxy was byte-identical before and after.

### G-F2-1 — production apply — PASS (OBSERVED, 10:47 CEST)

As in §5.

### G-F2-2 — Torre healthy, base model present — PASS

**OBSERVED, 10:50 CEST:**
```
GET  /api/tags            status=200 upstream=<UM790>   ustatus=200   (4 models incl. qwen2.5:7b-instruct)
POST /api/show  qwen2.5   status=200 upstream=<TORRE>   ustatus=200
POST /api/chat  qwen2.5   status=200 upstream=<TORRE>   ustatus=200   streamed, 85.1 tok/s (GPU), no fallback
```

**OPERATOR-REPORTED:** after the change, Aurora was visible in Open WebUI, and a short chat
streamed normally at fast, RTX-backed speed.

### G-F2-3 — Torre reachable, requested model absent — PASS (OBSERVED, 10:50–10:51 CEST)

`llama3.2:latest` exists only on the UM790, so it is a real model, absent on Torre (D-3).
```
POST /api/show  llama3.2  status=200 upstream=<TORRE>, <UM790>  ustatus=404, 200
POST /api/chat  llama3.2  status=200 upstream=<TORRE>, <UM790>  ustatus=404, 200   real CPU inference, num_predict 8, 25.7 tok/s
POST /api/show  qwen2.5   status=200 upstream=<TORRE>           ustatus=200        immediately afterwards — Torre NOT marked down
```

### G-F2-4 — model absent on both nodes — PASS (OBSERVED, 10:51 CEST)

```
POST /api/show  f-inc-2-absent:latest  status=404 upstream=<TORRE>, <UM790>  ustatus=404, 404
```

The client received `404` with `{"error":"model '…' not found"}`. Exactly two attempts, no loop.
This is the fail-loud state 3 of `hardware_agnostic_compute_architecture.md` §7.1.
**No chat or generate was run for this model.**

### G-F2-7 — regression — PASS (OBSERVED, 10:51 CEST)

- **Health:** the Home Assistant-facing `/healthz` returns `200`, and the proxy is `healthy`.
- **Catalogue:** `/api/tags` returns `200`. `/api/show qwen2.5` returns `200` through Torre.
- **Open WebUI's network path:** one read-only `GET /api/tags` from inside the `openwebui`
  container listed `qwen2.5:7b-instruct`.
- **Containers:** all 20 have an id, status, start time and `RestartCount` byte-identical to a
  snapshot taken before the gates.
- **Errors:** zero `error`/`crit`/`alert`/`emerg` lines in the proxy log since the reload.

## 7. Known limitations / risks

1. **G-F2-5 and G-F2-6 remain OPEN** (§9).
2. **Mid-stream failure cannot fail over.** nginx can pass a request on only before any response
   data has been sent. This is unchanged from before. A `404` always arrives before any data.
3. **A `500` from Torre is not a fallback condition** (O-1). For example, a GPU out-of-memory
   failure (`07_operations/lessons_learned.md` → *L-RTX-2*) still reaches the client.
4. **The catalogue now shows the UM790's models**, currently including `llama3.2:latest`,
   `llama3:latest` and `phi3:latest`. Their legacy Open WebUI entries are therefore permanently
   visible. Accepted under D-2; no filtering is part of F-INC-2.
5. **Ollama version skew — pre-existing debt, not addressed here.** Torre and the UM790 run
   different Ollama versions. Any fallback, transport or model-missing, sends the request to the
   older UM790 version. Out of F-INC-2 scope.
6. **A model present only on Torre would not appear** in the UM790-authoritative catalogue.
   This is an accepted current limitation, to be revisited only if such a deployment becomes
   real.

## 8. Rollback (designed, NOT executed)

1. Restore the committed baseline **in place**, keeping the inode:
   `git show HEAD:03_services/ollama-proxy/nginx.conf > 03_services/ollama-proxy/nginx.conf`.
2. Verify the host and container sha256 are `92ab5984…`.
3. Run `nginx -t` inside the container.
4. `nginx -s reload`.

No restart or recreation is needed.

## 9. Remaining validation

Both gates are **passive**: they need Torre to go offline and come back, either by its normal
on-demand use or by a clean, operator-initiated shutdown. They are not to be forced.

**G-F2-5 — Torre unavailable / offline.** Required proof:
- `/api/tags` remains available from the UM790;
- `qwen2.5:7b-instruct` inference falls back to the UM790, logged as `ustatus=504, 200` or
  `502, 200`;
- Aurora remains visible in Open WebUI;
- the operator confirms that Aurora answers, at the expected slower CPU performance.

**G-F2-6 — Torre returns.** Required proof:
- `qwen2.5:7b-instruct` requests automatically return to Torre (`upstream=<TORRE>`,
  `ustatus=200`);
- no manual proxy intervention;
- the operator confirms normal, fast, RTX-backed Aurora behaviour.

## 10. Final closeout requirements

F-INC-2 may move to **DONE** only after all of:
1. **G-F2-5 PASS**;
2. **G-F2-6 PASS**;
3. final documentation reconciliation (a closeout record plus the triad);
4. an approved Git commit and push.
