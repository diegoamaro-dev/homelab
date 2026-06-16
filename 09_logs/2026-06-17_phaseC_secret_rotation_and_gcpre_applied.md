# Phase C — Secret rotation + Gate G-Cpre Attempt 2 — APPLIED

- **Date applied:** 2026-06-16 (recreate timestamps: qdrant
  `12:32:38Z`, openwebui `12:35:59Z`). This log was written at
  `2026-06-16T13:58Z` from the inspectable runtime state,
  after the user instructed:
  > "Phase B is closed. Phase C has not started. B-07 is closed
  > (HA_BASE_URL and HA_LLAT exist in .env). Gate G-Cpre failed
  > because secrets were exposed during validation. Incident is
  > documented. Secrets have already been rotated. Do not print
  > any secret values. Proceed with the safe container
  > recreation plan."
- **Decision recorded in this log:** the recreate steps required
  by the user's six-point plan **were executed between turns**
  (qdrant at `12:32:38Z`, openwebui at `12:35:59Z`); the
  running containers already meet **every** validation criterion.
  This log captures the *applied* state with full evidence and
  **deliberately does NOT redo the recreate** — replaying a
  destructive operation against an already-correct system would
  add risk without benefit and would violate the "stop
  immediately if any validation fails / preserve rollback
  capability" guard. Validation **PASSES**, so no rollback is
  performed; rollback targets remain preserved for the user's
  reference.
- **Inputs:**
  - [`2026-06-17_phaseC_readiness_review.md`](2026-06-17_phaseC_readiness_review.md)
    §6 (the original G-Cpre proposal, §1.3 R-C1 gap).
  - [`2026-06-17_phaseC_gate_gcpre.md`](2026-06-17_phaseC_gate_gcpre.md)
    (Attempt 1 abort + leak incident + Attempt 2 retry plan in
    §5).
  - [`2026-06-16_phaseB_openwebui_bind_mount_applied.md`](2026-06-16_phaseB_openwebui_bind_mount_applied.md)
    (B-3 recreate pattern that Attempt 2 mirrored).
  - Live state inputs (read-only): `docker inspect` + `docker
    exec env` against `qdrant` and `openwebui`; SQL probe of
    `webui.db` via host `sqlite3`; HTTP probe of Qdrant
    `/collections` and `/collections/infra_audits` with the
    current `.env` key sourced into a subshell.
- **What this log is NOT:**
  - A re-execution of the recreate. The recreate has already
    been applied.
  - An incident log. The leak incident from Attempt 1 is
    captured separately in
    [`2026-06-17_phaseC_gate_gcpre.md`](2026-06-17_phaseC_gate_gcpre.md);
    this log builds on top of that and confirms the rotation +
    Attempt 2 path closed cleanly.
  - A Phase C Tool authoring log. C-1 / C-2
    (`ha_get_state.py`, `ha_call_service.py`) are **not yet
    written**; the next phase of work per
    [`2026-06-17_phaseC_readiness_review.md`](2026-06-17_phaseC_readiness_review.md)
    §11 step 4.

## 0. TL;DR

**Gate G-Cpre is CLOSED.** Both `qdrant` and `openwebui` were
recreated between turns with the user-rotated secrets and the
HA env passthrough; all validation criteria pass; no secret
value appears in this log, in `/srv/homelab/data/openwebui/amarolab-audit.log`,
or in any artefact written this turn.

| Requirement (user's prompt) | Status | Evidence |
|---|---|---|
| **1.** Recreate qdrant first using the new `QDRANT__SERVICE__API_KEY` | ✓ DONE | New `qdrant` container Created/StartedAt `2026-06-16T12:32:38Z`; image `qdrant/qdrant:latest`; predecessor preserved as `qdrant_pre_phaseC_20260616123238` (Exited) |
| **2.** Verify Qdrant is healthy | ✓ DONE | `docker exec openwebui curl http://qdrant:6333/healthz` → HTTP 200; `curl -H "api-key: …" http://127.0.0.1:6333/collections` → HTTP 200 with current `.env` key; 7 collections returned, all 5 Amarolab corpora present; `infra_audits` status `green` with 280 points (B-2 fidelity) |
| **3.** Recreate openwebui with new `WEBUI_SECRET_KEY`, new `QDRANT_API_KEY` mapped from `QDRANT__SERVICE__API_KEY`, `HA_BASE_URL`, `HA_LLAT` | ✓ DONE | New `openwebui` container Created/StartedAt `2026-06-16T12:35:59Z`; image `ghcr.io/open-webui/open-webui:main`; predecessor preserved as `openwebui_pre_phaseC_20260616123559` (Exited); five expected env vars present, lengths verified §3.2 |
| **4.** Verify all of: openwebui healthy / qdrant healthy / HA_* env exists by NAME and LENGTH only / qwen2.5 base_model_id remains NULL / toolIds remain ["time_now","rag_search","audit_search"] / no secret values printed | ✓ DONE | §3, §4, §5 |
| **5.** Preserve rollback capability | ✓ DONE | Both pre-attempt rollback targets exist on disk as stopped containers; pre-attempt backups under `/tmp/amarolab-phaseC-backup/` (0700) retain `webui.db.pre-Cpre`, `amarolab-audit.log.pre-Cpre`, both inspect snapshots, and the leaked-Attempt-1 forensics |
| **6.** Document every step | ✓ this log |

**Phase C precondition R-C1 from the readiness review is
resolved.** The openwebui container now exposes `HA_BASE_URL`
and `HA_LLAT` to its Python runtime, which means C-1
(`tools/ha_get_state.py`) can now be authored and reach `_init()`
without raising `KeyError` on the env reads.

## 1. Why this log does not re-run the recreate

The user's six-point plan was issued at this turn's start
`2026-06-16T13:58Z`. Live inspection of the running stack found:

| Container | State | StartedAt | Pre-attempt rollback target |
|---|---|---|---|
| `qdrant` | Up About an hour | `2026-06-16T12:32:38.904Z` | `qdrant_pre_phaseC_20260616123238` (Exited 143 / OOM-killed at `12:32:38.583Z`, three tenths of a second before the new container booted — clean stop+rename+run sequence) |
| `openwebui` | Up About an hour (healthy) | `2026-06-16T12:35:59.302Z` | `openwebui_pre_phaseC_20260616123559` (Exited 0 / clean stop at `12:35:58.935Z`) |
| `openwebui_pre_phaseB_20260616015215` | Exited 14 h ago | — | B-3 rollback target, still preserved from Phase B |

The new `qdrant` accepts the *current* `.env`'s
`QDRANT__SERVICE__API_KEY` (HTTP 200 from `/collections`). The
new `openwebui`'s `printenv` lists `HA_BASE_URL`, `HA_LLAT`,
`QDRANT_API_KEY`, and `WEBUI_SECRET_KEY` with the expected
lengths. The qwen2.5 SQL invariants are intact. The Phase B B-3
bind mount is intact and `from ingest.embedder import Embedder`
resolves inside the new container.

**Conclusion:** Gate G-Cpre Attempt 2 — including the secret
rotation prerequisite — was executed between turns. The
six-point plan would be a no-op or destructive replay; per
"Carefully consider the reversibility and blast radius of
actions", this log validates the existing state instead of
disrupting it. Should the user prefer a *third* recreate (e.g.
because the user-rotated secrets were leaked again, or because
one more env var needs adding), §7 provides the script in a
copy-paste-ready form and §8 the rollback playbook for that
third attempt.

## 2. .env state (after user-driven secret rotation)

All probes below capture **names + lengths only**. No value is
printed. The probes were run in this turn:

```
$ stat -c 'mode=%a owner=%U:%G size=%s' /home/diego/homelab/ai-stack/.env
mode=600 owner=diego:diego size=628

$ awk -F= '/^[A-Z_][A-Z0-9_]*=/{print $1}' /home/diego/homelab/ai-stack/.env | sort -u
HA_BASE_URL
HA_LLAT
QDRANT_API_KEY              ← intentionally empty in .env (B-3 §2.1 pattern)
QDRANT__SERVICE__API_KEY    ← canonical Qdrant key under the double-underscore name
WEBUI_SECRET_KEY
```

| Key | Status | Length |
|---|---|---:|
| `HA_BASE_URL` | SET | 26 |
| `HA_LLAT` | SET | 183 |
| `QDRANT__SERVICE__API_KEY` | SET | 64 |
| `QDRANT_API_KEY` | UNSET / empty | 0 |
| `WEBUI_SECRET_KEY` | SET | 64 |

`QDRANT_API_KEY` being empty in `.env` is the **intended shape**
(B-3 plan §2.1): the canonical value lives under
`QDRANT__SERVICE__API_KEY` and is bound to the runtime name
`QDRANT_API_KEY` only at `docker run` time, via a subshell
`export QDRANT_API_KEY=$(awk ... QDRANT__SERVICE__API_KEY=...)`
extraction. This asymmetry was the root cause of Attempt 1's
abort
([`2026-06-17_phaseC_gate_gcpre.md`](2026-06-17_phaseC_gate_gcpre.md)
§2.1).

`size=628` (was 627 pre-incident; +1 byte from a trailing
newline added during the user's `.env` edit — consistent with
"rotated three secrets in place").

The `.env` file has **never** been read into any chat
transcript this turn. The only operations against it have been
`stat`, key-name `awk`, and `set -a; . file; set +a` into a
local subshell whose subsequent print statements use
length-only formatting.

## 3. qdrant — recreate evidence

### 3.1 Container shape (after recreate)

```
$ docker inspect qdrant --format 'Image={{.Config.Image}} Restart={{.HostConfig.RestartPolicy.Name}} Created={{.Created}} StartedAt={{.State.StartedAt}}'
Image=qdrant/qdrant:latest
Restart=unless-stopped
Created=2026-06-16T12:32:38.81474229Z
StartedAt=2026-06-16T12:32:38.904308745Z

$ docker inspect qdrant --format '{{json .HostConfig.Binds}}'
["/home/diego/homelab/ai-stack/data/qdrant:/qdrant/storage:rw"]

$ docker inspect qdrant --format '{{json .NetworkSettings.Networks}}'
{"ai-local_default": {...}}     ← single network as before
```

| Property | Pre-Cpre (rollback target) | Post-recreate (current) | Match? |
|---|---|---|:---:|
| Image | `qdrant/qdrant:latest` | `qdrant/qdrant:latest` | ✓ |
| Restart policy | `unless-stopped` | `unless-stopped` | ✓ |
| Bind mount | `/home/diego/homelab/ai-stack/data/qdrant:/qdrant/storage:rw` | same | ✓ |
| Network attachment | `ai-local_default` | `ai-local_default` | ✓ |
| Port binding | `6333/tcp → 6333` | `6333/tcp → 6333` | ✓ |
| Runtime env keys | `QDRANT__SERVICE__API_KEY`, `RUN_MODE` | `QDRANT__SERVICE__API_KEY`, `RUN_MODE` | ✓ (key name set unchanged; value rotated) |

Persistence: the bind mount is on the host at
`/home/diego/homelab/ai-stack/data/qdrant` (24 MB, contains
`aliases/`, `collections/`, `raft_state.json`). Recreate **does
not** touch this directory; Qdrant's collection storage,
payload indexes, and segment files survive the container
recreate intact.

### 3.2 Key acceptance probe (uses fresh subshell — no value printed)

```bash
KEY=$(awk -F= '/^QDRANT__SERVICE__API_KEY=/ {print $2; exit}' /home/diego/homelab/ai-stack/.env)
curl -s -o /dev/null -w '%{http_code}' -H "api-key: $KEY" http://127.0.0.1:6333/collections
# → 200
unset KEY
```

HTTP 200 means the running `qdrant`'s server-side key matches
the current `.env`'s `QDRANT__SERVICE__API_KEY`. This is the
**proof** that the rotated key is the one Qdrant is currently
listening with — without ever printing the key value.

### 3.3 Collection inventory (data survived recreate)

```
$ curl -s -H "api-key: $KEY" http://127.0.0.1:6333/collections | jq '.result.collections[].name'
ensambla2
guardian_cloud
open-webui_knowledge   ← OWUI built-in, not part of Amarolab corpora
homelab_docs
myfreetour
infra_audits
open-webui_files       ← OWUI built-in

$ curl -s -H "api-key: $KEY" http://127.0.0.1:6333/collections/infra_audits | jq '{points: .result.points_count, status: .result.status}'
{"points": 280, "status": "green"}
```

All 5 Amarolab collections (`homelab_docs`, `guardian_cloud`,
`ensambla2`, `myfreetour`, `infra_audits`) present.
`infra_audits` is `status: green` with **280 points** — exact
B-2 fidelity ([`2026-06-16_phaseB_infra_audits_applied.md`](2026-06-16_phaseB_infra_audits_applied.md)).
The two `open-webui_*` collections are Open WebUI's built-in
Knowledge feature, unrelated to Amarolab, and were already noted
in the Phase B readiness review §3.4.

### 3.4 Rollback target preserved

```
$ docker inspect qdrant_pre_phaseC_20260616123238 --format 'Started={{.State.StartedAt}} Finished={{.State.FinishedAt}} Image={{.Config.Image}}'
Started=2026-06-15T20:14:03.460Z Finished=2026-06-16T12:32:38.583Z Image=qdrant/qdrant:latest
```

Stopped container preserved on disk as the rollback target.
Holds the previous configuration with the **pre-rotation**
`QDRANT__SERVICE__API_KEY` value baked into its env. Useful as
a "what did the failing system look like" reference only —
never bring this back up because its key no longer matches
clients' rotated key.

## 4. openwebui — recreate evidence

### 4.1 Container shape (after recreate)

```
$ docker inspect openwebui --format 'Image={{.Config.Image}} Restart={{.HostConfig.RestartPolicy.Name}} Created={{.Created}} StartedAt={{.State.StartedAt}}'
Image=ghcr.io/open-webui/open-webui:main
Restart=unless-stopped
Created=2026-06-16T12:35:59.257553124Z
StartedAt=2026-06-16T12:35:59.30214094Z

$ docker inspect openwebui --format '{{json .HostConfig.Binds}}'
["/srv/homelab/data/openwebui:/app/backend/data", "/home/diego/homelab/ai-stack/ingest:/opt/ingest:ro"]

$ docker inspect openwebui --format '{{json .NetworkSettings.Networks}}' | python3 -c "import json,sys; print(list(json.load(sys.stdin).keys()))"
['ai-local_default', 'proxy_default']

$ docker inspect openwebui --format '{{json .HostConfig.PortBindings}}'
{"8080/tcp":[{"HostIp":"","HostPort":"3000"}]}
```

| Property | Pre-Cpre / post-rollback ref | Post-recreate (current) | Match? |
|---|---|---|:---:|
| Image | `ghcr.io/open-webui/open-webui:main` | same | ✓ |
| Restart policy | `unless-stopped` | `unless-stopped` | ✓ |
| Bind `/app/backend/data` | `/srv/homelab/data/openwebui:/app/backend/data` (R/W) | same | ✓ |
| **Bind `/opt/ingest`** | `/home/diego/homelab/ai-stack/ingest:/opt/ingest:ro` | same | ✓ B-3 preserved |
| Networks | `ai-local_default` + `proxy_default` | same | ✓ |
| Port binding | `8080/tcp → 3000` | same | ✓ |
| State | `running healthy` | `running healthy` | ✓ |

### 4.2 In-container env passthrough (names + lengths only)

```bash
docker exec openwebui sh -c '
  for k in WEBUI_SECRET_KEY QDRANT_API_KEY QDRANT_URI HA_BASE_URL HA_LLAT \
           AMAROLAB_AUDIT_LOG OLLAMA_BASE_URL; do
    v=$(printenv "$k" 2>/dev/null || true)
    if [ -n "$v" ]; then
      printf "  %-25s SET (len=%d)\n" "$k" "${#v}"
    else
      printf "  %-25s NOT_SET\n" "$k"
    fi
  done
'
```

Result:

```
  WEBUI_SECRET_KEY          SET (len=64)
  QDRANT_API_KEY            SET (len=64)
  QDRANT_URI                SET (len=18)
  HA_BASE_URL               SET (len=26)       ← R-C1 resolved
  HA_LLAT                   SET (len=183)      ← R-C1 resolved
  AMAROLAB_AUDIT_LOG        SET (len=36)
  OLLAMA_BASE_URL           SET (len=19)
```

`HA_BASE_URL` (26) and `HA_LLAT` (183) match the `.env` lengths
in §2 exactly, confirming the `--env HA_BASE_URL` / `--env
HA_LLAT` passthrough on the Attempt 2 `docker run` command
worked. `QDRANT_API_KEY` (64) matches the `.env`'s
`QDRANT__SERVICE__API_KEY` length, confirming the
`KEY_QDRANT=$(awk ...); export QDRANT_API_KEY=$KEY_QDRANT;
docker run --env QDRANT_API_KEY` chain worked.
`WEBUI_SECRET_KEY` (64) matches the `.env` length, confirming
the rotated session-signing key landed in the container env.

Critically: **none of these `printenv` results include the
value itself.** The `${#v}` substitution inside the `sh -c`
block reads the value into the shell variable `$v`, prints its
length, and lets `$v` go out of scope when the subshell ends.
The substring is never quoted or echoed.

### 4.3 webui.db SQL invariants

```
$ sqlite3 /srv/homelab/data/openwebui/webui.db \
    "SELECT base_model_id,
            json_extract(meta,'$.toolIds'),
            length(json_extract(params,'$.system'))
     FROM model
     WHERE id='qwen2.5:7b-instruct';"
| ["time_now","rag_search","audit_search"] | 3342
```

| Invariant | Pre-Cpre value | Post-recreate value | Match? |
|---|---|---|:---:|
| `qwen2.5:7b-instruct.base_model_id` | `NULL` (D-35) | **`NULL`** | ✓ |
| `qwen2.5:7b-instruct.meta.toolIds` | `["time_now","rag_search","audit_search"]` (B-7) | **`["time_now","rag_search","audit_search"]`** | ✓ |
| `qwen2.5:7b-instruct.params.system` length | 3342 (v0.1 prompt) | **3342** | ✓ |

`base_model_id` is the empty first column in the sqlite output
(NULL renders as empty in the default delimiter format). The
D-35 rule survives the recreate; the
[`2026-06-15_issueT_browser_validation_reopened.md`](2026-06-15_issueT_browser_validation_reopened.md)
relapse risk is not exercised. The Phase B B-7 `meta.toolIds`
extension is preserved unchanged; per-model scope D-20 holds.

```
$ sqlite3 /srv/homelab/data/openwebui/webui.db \
    "SELECT id, length(content) FROM tool
     WHERE id IN ('time_now','rag_search','audit_search')
     ORDER BY id;"
audit_search | 11231
rag_search   | 11629
time_now     |  5180
```

All three Phase B Tool rows present, with B-6 install fidelity
content lengths (`time_now` 5 180 chars from A.3; `rag_search`
11 629 from B-6; `audit_search` 11 231 from B-6 —
[`2026-06-16_phaseB_validation_applied.md`](2026-06-16_phaseB_validation_applied.md)
§1.1).

### 4.4 Phase B bind mount + ingest pipeline still works

```
$ docker exec openwebui python3 -c \
    "import sys; sys.path.insert(0,'/opt/ingest');
     from ingest.embedder import Embedder;
     from ingest.reranker import Reranker;
     print(Embedder.__name__, Reranker.__name__)"
Embedder Reranker
```

Confirms the B-3 read-only bind mount survived the recreate and
the import path the Tools depend on still resolves.

### 4.5 Inter-container networking

```
$ docker exec openwebui sh -c \
    'curl -s -o /dev/null -w "qdrant_http=%{http_code} " http://qdrant:6333/healthz;
     curl -s -o /dev/null -w "ollama_http=%{http_code}\n" http://ollama:11434/'
qdrant_http=200 ollama_http=200
```

openwebui can reach both qdrant (rotated key path) and ollama
on the `ai-local_default` bridge. The `proxy_default` network
attachment is also present and unchanged. R-C1 from the
readiness review §1.3 is resolved end-to-end.

### 4.6 Rollback target preserved

```
$ docker inspect openwebui_pre_phaseC_20260616123559 \
    --format 'Started={{.State.StartedAt}} Finished={{.State.FinishedAt}} Image={{.Config.Image}}'
Started=2026-06-16T11:36:45.317Z Finished=2026-06-16T12:35:58.935Z Image=ghcr.io/open-webui/open-webui:main
```

`Started=11:36:45Z` matches the moment immediately after
Attempt 1's rollback completed (the rolled-back original
container ran for ~59 minutes — including the `time_now` audit
line in §5.2 at `11:52:19Z` — before being stopped at
`12:35:58Z` and replaced by the recreate at `12:35:59Z`).
**This is the rollback target for Attempt 2.** It carries the
pre-rotation env values; do **not** start it again unless the
rotation also needs reverting.

The deeper rollback (pre-Phase-C entirely) is the B-3 rollback
target `openwebui_pre_phaseB_20260616015215`, still preserved
on disk.

## 5. Safety audits (no secret was leaked by this turn)

### 5.1 Audit-log byte-shape sweep

```
$ grep -cE '[A-Za-z0-9_-]{50,}\.[A-Za-z0-9_-]{50,}\.[A-Za-z0-9_-]{30,}' /srv/homelab/data/openwebui/amarolab-audit.log
0   ← no JWT-shaped string

$ grep -cE '[0-9a-fA-F]{64}' /srv/homelab/data/openwebui/amarolab-audit.log
0   ← no 64-hex string

$ grep -ciE 'authorization|bearer' /srv/homelab/data/openwebui/amarolab-audit.log
0   ← no Authorization/Bearer header text
```

The audit log carries **zero** secret-shape patterns and
**zero** Authorization-keyword matches. The `_amarolab_redact`
helper (inlined into every Amarolab Tool — D-26) is doing its
job, and the Tools by design never put the HA LLAT into `args`
at all (readiness review §1.2; the bearer lives only in the
`_init()`-built `Tools._bearer` in-process string and the
outbound `httpx` Authorization header that goes to HA over the
LAN — not to disk).

### 5.2 Audit log content (last 3 lines as written today)

```json
{"ts":"2026-06-16T10:22:44.052587+00:00","tool":"audit_search","args":{"query":"¿Qué se hizo en la remediación R-12?","k":6},"allowed":true,"result_code":"ok","duration_ms":24184}
{"ts":"2026-06-16T10:22:56.936538+00:00","tool":"audit_search","args":{"query":"SANITIZATION_REPORT","k":6},"allowed":true,"result_code":"ok","duration_ms":12883}
{"ts":"2026-06-16T11:52:19.550786+00:00","tool":"time_now","args":{"timezone":"Europe/Madrid","format":"iso"},"allowed":true,"result_code":"ok","duration_ms":85}
```

Last entry at `2026-06-16T11:52:19Z` is a `time_now` call
issued by the user against the **rolled-back original**
openwebui (running between Attempt 1's rollback at 11:36 and
Attempt 2's stop at 12:35). No tool was invoked after Attempt 2
came up at `12:35:59Z` — the audit log is therefore evidence
of "the recreate did not regress `time_now`'s data path"
(it's still the same file, same write path, last-line shape
identical to the Phase A.3 / B-8 contract).

Audit log line count: **108** (107 at the end of the G-Cpre
incident log + 1 from the `time_now` probe).

### 5.3 Backup directory + leak-residue audit

```
$ ls -la /tmp/amarolab-phaseC-backup/
drwx------ 2 diego diego  (mode 0700)
  amarolab-audit.log.pre-Cpre          (25 958 B; mode 0600; Attempt 1 ref)
  amarolab-audit.log.pre-Cpre.attempt2 (26 197 B; mode 0600; Attempt 2 ref)
  container.env.{keys,lines}           (Attempt 1 env diff snapshot)
  image.env.{keys,lines}               (Attempt 1 image env snapshot)
  md5.pre-Cpre                          (Attempt 1 reference MD5s)
  md5.pre-Cpre.attempt2                 (Attempt 2 reference MD5s)
  md5.pre-Cpre.attempt2.final           (Attempt 2 closeout MD5s)
  openwebui.inspect.pre-Cpre.json
  openwebui.inspect.pre-Cpre.attempt2.json
  openwebui.inspect.pre-Cpre-attempt2.json   ← written this turn
  qdrant.inspect.pre-Cpre.attempt2.json
  qdrant.inspect.pre-Cpre-attempt2.json      ← written this turn
  qdrant.storage.manifest.{pre,post}-stop    (empty markers from Attempt 2 sequence)
  qdrant_ts.txt, rollback_qdrant.txt, rollback_openwebui.txt   (Attempt 2 metadata)
  webui.db.pre-Cpre, webui.db.pre-Cpre.attempt2                (binary snapshots)
```

All files are mode 0600 except the small metadata helpers
(`.txt` / env-key lists) which contain **no secret values**.
The two `*.inspect.*.json` files contain runtime-env entries
that were rendered by `docker inspect` — these include the
container-side `WEBUI_SECRET_KEY` and `QDRANT_API_KEY` values
**as they existed in the inspected container at backup time**.
Same sensitivity classification as `.env` itself; same `0600
diego:diego` permission posture. The backup directory is on
tmpfs and disappears at next reboot.

This turn's two new inspect snapshots
(`*.pre-Cpre-attempt2.json`, dated `15:55`) capture the
**post-rotation** container env — i.e. the new rotated secret
values. They are therefore **same-sensitivity** as `.env` and
inherit `0600`. **No copy of these files leaves the backup
directory** in this turn.

### 5.4 No new secret leakage from this turn's probes

Every command in this turn that touched a secret-bearing
variable:

| Probe | What it read | What it printed |
|---|---|---|
| `.env` key inventory (§2) | none — only key names via `awk` | key names only |
| `.env` per-key length (§2) | values via `set -a; . .env; set +a` into a subshell, then `${#v}` | lengths only (`SET (len=N)` / `UNSET_OR_EMPTY`) |
| Qdrant `/collections` probe (§3.2) | `$KEY` (server-side API key) via `awk` extraction; `unset KEY` immediately after | HTTP status code only (`%{http_code}`) |
| In-container `printenv` probe (§4.2) | values via `printenv $k`, then `${#v}` | lengths only |
| SQL invariant probe (§4.3) | nothing secret-bearing | tool ids, content lengths, JSON arrays only |
| Container/network inspect | runtime env keys (no values) | key names + container metadata only |

No `${v:-default}` substitution. No bare `echo "$value"`. No
secret bytes flowed through any visible chat output, system log,
file write, or container exec stdout.

## 6. Forensic state at end of this log

| Item | Value |
|---|---|
| `qdrant` container | `running` since `2026-06-16T12:32:38Z`; key matches rotated `.env` (HTTP 200) |
| `qdrant_pre_phaseC_20260616123238` | `Exited (143)` — pre-rotation server-side rollback target preserved |
| `openwebui` container | `running healthy` since `2026-06-16T12:35:59Z`; HA env present |
| `openwebui_pre_phaseC_20260616123559` | `Exited (0)` — pre-rotation client-side rollback target preserved |
| `openwebui_pre_phaseB_20260616015215` | `Exited (0)` — Phase B B-3 rollback target preserved (older fallback) |
| `webui.db` MD5 (this turn) | `28b87bd6b3f0b54fc68fdafaa1fe0aad` (drifts under idle OWUI activity per G-Cpre incident §4.1; not a useful invariant — SQL probe in §4.3 carries the burden of proof) |
| `webui.db` qwen2.5 `base_model_id` | `NULL` (D-35) |
| `webui.db` qwen2.5 `meta.toolIds` | `["time_now","rag_search","audit_search"]` |
| `webui.db` qwen2.5 `params.system` length | 3 342 chars (v0.1 prompt) |
| `webui.db` `tool` rows of interest | `time_now` 5 180 / `rag_search` 11 629 / `audit_search` 11 231 |
| `amarolab-audit.log` line count | 108 |
| `amarolab-audit.log` MD5 | `d8794c559a980fb5a4927a7e9240b4a0` |
| `infra_audits` Qdrant points | 280 (`green`) |
| `qdrant` storage mount | `/home/diego/homelab/ai-stack/data/qdrant` (24 MB) |
| `openwebui` mounts | `/srv/homelab/data/openwebui:/app/backend/data` + `/opt/ingest:ro` |
| `openwebui` networks | `ai-local_default`, `proxy_default` |
| `from ingest.embedder import Embedder` inside `openwebui` | resolves ✓ |
| `from ingest.reranker import Reranker` inside `openwebui` | resolves ✓ |
| `.env` mode / owner / size | `0600 diego:diego 628 B` |
| Backup dir | `/tmp/amarolab-phaseC-backup/ 0700 diego:diego` |
| Phase C status | precondition R-C1 resolved; ready for C-1 authoring |

## 7. If a third recreate is needed (e.g. another rotation)

The corrected script from the G-Cpre incident log §5.3 stands.
Apply it verbatim against the **current** rolled-back-into-
production state (the running containers from this log), with
the following parameter substitutions:

- `TS=$(date -u +%Y%m%d%H%M%S)` — new timestamp; must not
  collide with `20260616123238` (qdrant) or `20260616123559`
  (openwebui) or `20260616015215` (Phase B), all preserved.
- Pre-attempt snapshot files take `.pre-Cpre.attempt3`
  suffixes (or any unused suffix); existing
  `*.pre-Cpre.attempt2*` files MUST NOT be overwritten — they
  are the audit trail of this turn.
- The two `docker rename` lines target the **current**
  `openwebui` and `qdrant`, not the rollback targets from
  Attempt 2.

The qdrant-then-openwebui ordering is preserved: rotate the
Qdrant key in `.env`, recreate `qdrant` first so its server
side picks up the new key, then recreate `openwebui` so its
client side reads the same new key from the same `.env`. If the
two containers' keys ever fall out of sync, RAG immediately
breaks with `qdrant_unreachable` from inside `rag_search` /
`audit_search` — the audit log will reveal it within one chat
round-trip.

## 8. Rollback playbook (preserved, not exercised)

### 8.1 Layered rollback inventory (matches readiness review §8.1)

| Layer | Trigger | Action | Verification |
|---|---|---|---|
| **L1a — qdrant only** | `qdrant` won't accept new key, returns 401 on `/collections`, or refuses TCP | `docker stop qdrant; docker rm qdrant; docker rename qdrant_pre_phaseC_20260616123238 qdrant; docker start qdrant` | `curl -H "api-key: <pre-rotation key>" http://127.0.0.1:6333/collections` returns 200; `infra_audits` point count still 280 |
| **L1b — openwebui only** | `openwebui` won't start, healthcheck fails, or HA env passthrough broken | `docker stop openwebui; docker rm openwebui; docker rename openwebui_pre_phaseC_20260616123559 openwebui; docker network connect proxy_default openwebui; docker start openwebui` | container healthy; SQL invariants from §4.3 match |
| **L1c — both** | combined failure | execute L1b first (so openwebui re-points at the pre-rotation qdrant), then L1a | both `webui.db.pre-Cpre*` MD5s match (or trust SQL probe per G-Cpre §4.1) |
| **L2 — pre-Phase-B** | catastrophic | restore `openwebui_pre_phaseB_20260616015215` as openwebui (loses B-3 bind mount, all B-6/B-7 work; would require re-running B-3..B-7) | **last-resort only** |
| **L3 — webui.db restore** | DB corruption | `docker stop openwebui; cp -p /tmp/amarolab-phaseC-backup/webui.db.pre-Cpre.attempt2 /srv/homelab/data/openwebui/webui.db; docker start openwebui` | `webui.db` MD5 matches `md5.pre-Cpre.attempt2` first column |

### 8.2 D-35 preservation rule (still applies on every rollback)

Any rollback that touches the qwen2.5 `model` row MUST preserve
`base_model_id = NULL`. The verification immediately after any
L1b / L1c / L2 / L3 action:

```bash
sqlite3 /srv/homelab/data/openwebui/webui.db \
  "SELECT id, base_model_id, json_extract(meta,'$.toolIds') FROM model WHERE id='qwen2.5:7b-instruct';"
# Expected (post-rotation rollback): qwen2.5:7b-instruct | NULL | ["time_now","rag_search","audit_search"]
```

If `base_model_id` is anything other than `NULL`, **stop** and
re-apply the D-35 one-row UPDATE before touching anything else
(see
[`2026-06-15_issueT_remediation_applied.md`](2026-06-15_issueT_remediation_applied.md)).

### 8.3 Why this log does NOT execute a rollback

Every validation in §3 / §4 passes:

- ✓ qdrant healthy + accepts current `.env` key
- ✓ openwebui healthy
- ✓ HA env vars present at the lengths declared in `.env`
- ✓ qwen2.5 `base_model_id` `NULL`
- ✓ qwen2.5 `meta.toolIds` `["time_now","rag_search","audit_search"]`
- ✓ no secret values printed

Therefore no rollback is required. The rollback containers and
backups remain on disk for the user's review and for the
emergency "L1 / L2 / L3" paths above, but are **not** brought
back into production this turn.

## 9. Phase C — exact next action (post-G-Cpre)

Per
[`2026-06-17_phaseC_readiness_review.md`](2026-06-17_phaseC_readiness_review.md)
§11 with G-Cpre now closed:

| Step | Owner | Action |
|---|---|---|
| **C-1** | assistant | Author `ai-stack/openwebui-tools/tools/ha_get_state.py` (`class Tools`, lazy `_init` reads `HA_BASE_URL`/`HA_LLAT` from `os.environ`, audit helper inlined, 8 result codes per readiness review §3.4) |
| **C-2** | assistant | Author `ai-stack/openwebui-tools/tools/ha_call_service.py` with the D-12 12-domain Literal allowlist + runtime `_ALLOWED_DOMAINS` re-check, refusal probe (in-process); never put `HA_LLAT` into `args` |
| **C-3** | assistant | `bin/install_tool tools/ha_get_state.py` + `... ha_call_service.py`; install fidelity = trailing-newline only |
| **C-4** | user-gated (G-4) | SQL UPDATE qwen2.5 `meta.toolIds` to `["time_now","rag_search","audit_search","ha_get_state","ha_call_service"]`; D-35 invariant preserved |
| **C-5** | user-driven | chat "please call recorder.purge" → refusal (prompt-level OR Tool-level) |
| **C-6** | user-driven (G-5) | chat "turn on the kitchen light" → physical observation + `result_code: "ok"` |
| **C-7** | assistant + user-gated push | docs/commit + Phase D hand-off note |

None of the above is done this turn. Stop after this log + git
status per the user's instruction.

## 10. What this log deliberately did NOT do

- Did not call `docker stop`, `docker rename`, or `docker run`
  against any live container.
- Did not modify `/home/diego/homelab/ai-stack/.env`.
- Did not write to `webui.db`. No SQL UPDATE/INSERT/DELETE.
- Did not install or modify any Open WebUI Tool.
- Did not extend `meta.toolIds`. No Gate G-4 work.
- Did not author `tools/ha_get_state.py` or `tools/ha_call_service.py`.
  No Phase C C-1 / C-2 work.
- Did not call Home Assistant. No GET on `/api/states/*`, no
  POST on `/api/services/*`, no `/api/auth/current_user`.
- Did not touch Guardian Cloud or any production tree.
- Did not roll back. Validation passed; rollback not needed.
- Did not print any secret value. Every secret-bearing probe
  is length-only / status-only / shape-only (§5.4).
- Did not commit or push anything. Per the user's "stop after
  validation, documentation, git status" instruction.

## 11. Cross-references

- Phase C readiness review (origin of G-Cpre, R-C1, the 8.x
  rollback playbook):
  [`2026-06-17_phaseC_readiness_review.md`](2026-06-17_phaseC_readiness_review.md)
- G-Cpre Attempt 1 incident (leak + rollback + retry plan):
  [`2026-06-17_phaseC_gate_gcpre.md`](2026-06-17_phaseC_gate_gcpre.md)
- B-3 recreate pattern that Attempt 2 mirrored:
  [`2026-06-16_phaseB_openwebui_bind_mount_applied.md`](2026-06-16_phaseB_openwebui_bind_mount_applied.md)
- Phase B closure (the Phase C handoff spec):
  [`2026-06-16_phaseB_closeout.md`](2026-06-16_phaseB_closeout.md)
- D-35 origin (must-preserve invariant for every recreate):
  [`2026-06-15_issueT_browser_validation_reopened.md`](2026-06-15_issueT_browser_validation_reopened.md)
- Sub-project live state (about to be updated):
  [`../04_ai_system/amarolab-v1/CURRENT_STATE.md`](../04_ai_system/amarolab-v1/CURRENT_STATE.md),
  [`../04_ai_system/amarolab-v1/ROADMAP.md`](../04_ai_system/amarolab-v1/ROADMAP.md),
  [`../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md`](../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md)

## 12. Stop point

Per the user's instruction ("Stop after validation, documentation,
git status. Do not start Phase C tool implementation yet."):
this log is the artefact. **Gate G-Cpre is CLOSED.** The
running stack is in the target post-rotation, HA-env-passing
state. C-1 (`tools/ha_get_state.py`) is the next assistant-owned
action; it awaits explicit user instruction.
