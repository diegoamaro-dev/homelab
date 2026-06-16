# Phase C C-4 — Gate G-4 — qwen2.5 `meta.toolIds` extension — APPLIED

- **Date:** 2026-06-17 (executed wall-clock `2026-06-16T15:32:33Z` UTC,
  consistent with the wall-clock-vs-filename convention used in
  the earlier Phase C logs).
- **Status:** **APPLIED.** qwen2.5:7b-instruct `meta.toolIds`
  extended additively from
  `["time_now","rag_search","audit_search"]` to
  `["time_now","rag_search","audit_search","ha_get_state","ha_call_service"]`
  via a single `json_set` SQL UPDATE. **D-35 invariant
  preserved** (`base_model_id` still `NULL`). **D-20 per-model
  scope preserved** (llama3.2 / llama3 rows unchanged, including
  `updated_at`). `params.system` length unchanged (3 342 chars,
  v0.1 prompt). The 8 `webui.db.tool` rows are byte-identical
  to the C-3 post-install state. No HA call made. No container
  recreate. No Open WebUI restart required (per the Phase B B-7
  precedent — Model rows are read at chat-completion time;
  `/api/models` reflects the new `info.meta.toolIds` on the next
  request).
- **Scope:** Gate G-4 only. **Does not call Home Assistant.
  Does not test lights. Does not continue to C-5.**
- **Inputs:**
  - [`2026-06-17_phaseC_tool_install_applied.md`](2026-06-17_phaseC_tool_install_applied.md)
    (C-3 — the install that put the two new Tool rows into
    `webui.db.tool` with the expected content lengths).
  - [`2026-06-17_phaseC_ha_get_state_design.md`](2026-06-17_phaseC_ha_get_state_design.md)
    (C-1 — Tool source + LLAT defense-in-depth posture).
  - [`2026-06-17_phaseC_ha_call_service_design.md`](2026-06-17_phaseC_ha_call_service_design.md)
    (C-2 — Tool source + canonical refusal probe).
  - [`2026-06-17_phaseC_secret_rotation_and_gcpre_applied.md`](2026-06-17_phaseC_secret_rotation_and_gcpre_applied.md)
    (G-Cpre — container env passthrough enabling the HA Tools to
    reach HA at C-5 / C-6, when those steps are exercised).
  - [`2026-06-17_phaseC_readiness_review.md`](2026-06-17_phaseC_readiness_review.md)
    §7 C-4 row (the SQL update spec) + §8 (rollback playbook
    with the D-35 preservation rule) + §11 step 7 (the explicit
    next action this turn fulfils).
  - [`2026-06-16_phaseB_closeout.md`](2026-06-16_phaseB_closeout.md)
    §6.3 step 8 (the Phase C handoff spec for C-4, including the
    D-35 invariant).
  - [`2026-06-16_phaseB_validation_applied.md`](2026-06-16_phaseB_validation_applied.md)
    §2 (B-7 / Gate G-2 — the same kind of toolIds extension on
    the same row; documented precedent for "no container restart
    required").
  - [`2026-06-15_issueT_browser_validation_reopened.md`](2026-06-15_issueT_browser_validation_reopened.md)
    §2.4 (origin of D-35 — the rule that this UPDATE preserves
    by not touching `base_model_id`).

## 0. TL;DR

| Requirement | Status | Evidence |
|---|---|---|
| **1.** Update only `qwen2.5:7b-instruct` | ✓ | `WHERE id='qwen2.5:7b-instruct'` in the UPDATE statement; SQL probes confirm one row touched, `updated_at` changed only on the qwen2.5 row |
| **2.** Preserve D-35: `base_model_id` remains `NULL` | ✓ | Pre `NULL` / post `NULL` — see §2.2. The UPDATE statement does not reference `base_model_id`, so SQLite preserves its prior value |
| **3.** Preserve D-20: `llama3*` rows unchanged | ✓ | `llama3.2:latest` and `llama3:latest` `meta.toolIds`, `base_model_id`, and `updated_at` all byte-identical to pre-C-4 — see §2.3 |
| **4.** Verify resulting `toolIds` | ✓ | `json_array_length = 5`; full list = `["time_now","rag_search","audit_search","ha_get_state","ha_call_service"]` — see §2.1 |
| **5.** Restart openwebui only if required | n/a | Not required (B-7 precedent; Model rows are read per chat completion; container uptime preserved from G-Cpre `2026-06-16T12:35:59Z`) — see §3 |
| **6.** Verify model row after update | ✓ | §2 in full |

**Phase C Gate G-4 is APPLIED and CLOSED.** The qwen2.5 row now
addresses 5 Amarolab Tools (3 Phase A/B + 2 Phase C). The two
new HA Tools (`ha_get_state`, `ha_call_service`) are now
addressable by the LLM via the OWUI 0.8.10 `info.meta.toolIds`
auto-attach path. C-5 (user-driven canonical refusal test) and
C-6 (user-driven happy-path test, Gate G-5) are the next
phases and are **deliberately not exercised this turn** per
the user's stop instruction.

## 1. Execution

### 1.1 Pre-flight backup

```bash
$ cp -p /srv/homelab/data/openwebui/webui.db \
       /tmp/amarolab-phaseC-backup/webui.db.pre-C4
$ chmod 600 /tmp/amarolab-phaseC-backup/webui.db.pre-C4
$ md5sum /tmp/amarolab-phaseC-backup/webui.db.pre-C4 \
         /srv/homelab/data/openwebui/webui.db
6405bd700712ff1fb969c925b65586ac  /tmp/amarolab-phaseC-backup/webui.db.pre-C4
6405bd700712ff1fb969c925b65586ac  /srv/homelab/data/openwebui/webui.db
```

Backup file is bit-identical to the source at backup time
(both MD5s match). Backup mode is `0600`. Backup directory
mode remains `0700 diego:diego` (preserved from earlier
Phase C work).

A companion JSON snapshot of the pre-update `meta` field was
also captured for later diff:

```bash
$ sqlite3 webui.db \
    "SELECT meta FROM model WHERE id='qwen2.5:7b-instruct';" \
    > /tmp/amarolab-phaseC-backup/qwen2.5.meta.pre-C4.json
```

Pre-state content (single line, 244 chars):

```json
{"profile_image_url":"/static/favicon.png",
 "description":"Amarolab primary tool-calling LLM. Tools scoped to this model only (D-20).",
 "capabilities":{"vision":false,"usage":true,"citations":true},
 "toolIds":["time_now","rag_search","audit_search"]}
```

(Pretty-printed here for readability; on disk it is a single
JSON line.)

### 1.2 The SQL UPDATE

Single statement, run with the openwebui container live (no
stop required):

```sql
UPDATE model
SET meta = json_set(meta, '$.toolIds',
                    json('["time_now","rag_search","audit_search","ha_get_state","ha_call_service"]')),
    updated_at = strftime('%s', 'now')
WHERE id='qwen2.5:7b-instruct';
```

Properties of this statement that uphold the invariants:

1. **D-35 preservation.** `base_model_id` is not in the `SET`
   list, so SQLite leaves it at its prior value (`NULL`).
   Verified post-update by direct SQL probe (§2.2).
2. **Sibling fields preservation.** `json_set` operates on the
   `meta` JSON document and replaces *only* the
   `$.toolIds` value. `profile_image_url`, `description`, and
   `capabilities` remain byte-identical (§2.1).
3. **D-20 per-model scope preservation.** The `WHERE`
   clause is anchored on `id='qwen2.5:7b-instruct'`. Other
   `model` rows are not addressed and not touched (§2.3).
4. **No restart required.** The Phase B B-7 / Gate G-2
   precedent is identical in shape (same column, same
   `WHERE`, same JSON-set semantics applied to the same row,
   no container restart), and the post-update probe of
   `/api/models` at that time confirmed Open WebUI reads the
   new value on the next request. C-4 inherits the same
   behaviour.

The statement returned exit code 0 with no stdout — SQLite's
canonical silent-success.

### 1.3 SQL UPDATE timing

| Field | Value |
|---|---|
| Pre-update `updated_at` (unix) | `1781562649` |
| Pre-update `updated_at` (UTC) | `2026-06-15T22:30:49Z` (Issue T remediation 2026-06-15 / D-35 origin) |
| Post-update `updated_at` (unix) | `1781623953` |
| Post-update `updated_at` (UTC) | `2026-06-16T15:32:33Z` (this C-4 turn) |
| Current wall-clock UTC | `2026-06-16T15:33:07Z` (≈ 34 s after the UPDATE) |

The `updated_at` jump is the canonical timestamping pattern
inherited from B-7. The `strftime('%s','now')` SQLite
built-in emits a Unix epoch integer, matching the column's
storage format.

## 2. Post-update verification

### 2.1 qwen2.5 — `meta.toolIds` extended; sibling fields preserved

```bash
$ sqlite3 webui.db \
    "SELECT id, base_model_id,
            json_extract(meta,'$.toolIds'),
            length(json_extract(params,'$.system')),
            updated_at
     FROM model WHERE id='qwen2.5:7b-instruct';"
qwen2.5:7b-instruct|(NULL)|["time_now","rag_search","audit_search","ha_get_state","ha_call_service"]|3342|1781623953
```

| Field | Pre-C-4 | Post-C-4 | Match? |
|---|---|---|:---:|
| `id` | `qwen2.5:7b-instruct` | `qwen2.5:7b-instruct` | ✓ |
| `base_model_id` | `NULL` (D-35) | **`NULL`** | ✓ **D-35 preserved** |
| `meta.toolIds` | `["time_now","rag_search","audit_search"]` | **`["time_now","rag_search","audit_search","ha_get_state","ha_call_service"]`** | ✓ extended additively, original 3 entries preserved at indices [0..2] |
| `meta.toolIds` cardinality | 3 | **5** | ✓ |
| `params.system` length | 3 342 chars (v0.1 prompt) | **3 342** | ✓ unchanged |
| `updated_at` | `1781562649` (2026-06-15T22:30:49Z) | `1781623953` (2026-06-16T15:32:33Z) | ✓ expected delta |

Cardinality probe:

```bash
$ sqlite3 webui.db \
    "SELECT json_array_length(json_extract(meta,'$.toolIds')),
            json_extract(meta,'$.toolIds')
     FROM model WHERE id='qwen2.5:7b-instruct';"
5|["time_now","rag_search","audit_search","ha_get_state","ha_call_service"]
```

Sibling-field preservation probe:

```bash
$ sqlite3 webui.db \
    "SELECT json_extract(meta,'$.profile_image_url'),
            json_extract(meta,'$.description'),
            json_extract(meta,'$.capabilities')
     FROM model WHERE id='qwen2.5:7b-instruct';"
/static/favicon.png|Amarolab primary tool-calling LLM. Tools scoped to this model only (D-20).|{"vision":false,"usage":true,"citations":true}
```

All three sibling fields are byte-identical to the pre-C-4
snapshot in §1.1.

Full meta-diff (pre vs post):

```
--- /tmp/amarolab-phaseC-backup/qwen2.5.meta.pre-C4.json
+++ /tmp/amarolab-phaseC-backup/qwen2.5.meta.post-C4.json
@@ -1 +1 @@
-{"profile_image_url":"/static/favicon.png","description":"Amarolab primary tool-calling LLM. Tools scoped to this model only (D-20).","capabilities":{"vision":false,"usage":true,"citations":true},"toolIds":["time_now","rag_search","audit_search"]}
+{"profile_image_url":"/static/favicon.png","description":"Amarolab primary tool-calling LLM. Tools scoped to this model only (D-20).","capabilities":{"vision":false,"usage":true,"citations":true},"toolIds":["time_now","rag_search","audit_search","ha_get_state","ha_call_service"]}
```

**Exactly one change**: the `toolIds` array grew by two
trailing entries (`ha_get_state`, `ha_call_service`). No
other field touched. No reordering of the original three.

### 2.2 D-35 invariant — `base_model_id` is still `NULL`

The SQL probe in §2.1 renders `base_model_id` as an empty
column between the first two `|` delimiters (SQLite's default
formatting for `NULL`). Independent direct probe:

```bash
$ sqlite3 webui.db \
    "SELECT CASE WHEN base_model_id IS NULL THEN 'NULL'
                 ELSE 'NOT_NULL:' || base_model_id END
     FROM model WHERE id='qwen2.5:7b-instruct';"
NULL
```

**D-35 is preserved.** The OWUI 0.8.10 `get_all_models`
(`utils/models.py:159–175`) skip-branch trap does **not** fire
on this row, so the LLM-facing `/api/models` will continue to
expose `info.meta.toolIds` to the browser's auto-attach in
`GxGTGtKc.js` (the chain that the Issue T re-investigation
documented end-to-end).

### 2.3 D-20 invariant — per-model scope unchanged

```bash
$ sqlite3 webui.db \
    "SELECT id, base_model_id,
            json_extract(meta,'$.toolIds'), updated_at
     FROM model WHERE id LIKE 'llama%' OR id LIKE 'phi%'
     ORDER BY id;"
llama3.2:latest||["docker_logs","docker_containers","system_status"]|1773442892
llama3:latest||["docker_containers","system_status","docker_logs"]|1775031217
```

| Row | `meta.toolIds` | `updated_at` |
|---|---|---|
| `llama3.2:latest` | `["docker_logs","docker_containers","system_status"]` (Jarvis set) | `1773442892` (unchanged) |
| `llama3:latest` | `["docker_containers","system_status","docker_logs"]` (Jarvis set, order-differs) | `1775031217` (unchanged) |

**Neither row was touched by the UPDATE.** `updated_at` is
identical to the C-3 closeout snapshot
([`2026-06-17_phaseC_tool_install_applied.md`](2026-06-17_phaseC_tool_install_applied.md)
§4.2). `meta.toolIds` carries only the Jarvis-era tool ids;
**neither `ha_get_state` nor `ha_call_service` appears**.
D-20 per-model scope holds — only qwen2.5 sees the HA Tools.

`phi3:latest` is present in Ollama's model inventory (per
`CURRENT_STATE.md` §"Models in Ollama") but has **no** row in
`webui.db.model`, so it has no `meta.toolIds` at all and
cannot see Amarolab Tools (D-20 by absence). No row was
created for `phi3` by this UPDATE.

### 2.4 `tool` table — byte-identical to C-3 post-install

```bash
$ sqlite3 webui.db \
    "SELECT id, length(content), json_array_length(specs)
     FROM tool ORDER BY id;"
audit_search       | 11231 | 1
docker_containers  |   890 | 1
docker_logs        |   585 | 1
ha_call_service    | 18494 | 1
ha_get_state       | 14982 | 1
rag_search         | 11629 | 1
system_status      |   507 | 1
time_now           |  5180 | 1
```

All 8 rows present. Content lengths and spec counts are
byte-identical to the C-3 closeout
([`2026-06-17_phaseC_tool_install_applied.md`](2026-06-17_phaseC_tool_install_applied.md)
§2.1). The UPDATE did not touch any `tool` row.

### 2.5 Audit log unchanged — no Tool was invoked

```bash
$ wc -l /srv/homelab/data/openwebui/amarolab-audit.log
119 /srv/homelab/data/openwebui/amarolab-audit.log
$ md5sum /srv/homelab/data/openwebui/amarolab-audit.log
4a451cddbf367187448c01b1ecf28d1a  amarolab-audit.log
```

| Metric | Pre-C-4 | Post-C-4 | Match? |
|---|---|---|:---:|
| Line count | 119 | 119 | ✓ |
| MD5 | `4a451cddbf367187448c01b1ecf28d1a` | `4a451cddbf367187448c01b1ecf28d1a` | ✓ |

**Audit-log delta = 0.** Expected: a SQL UPDATE on the
`model` table is an administrative operation; the inlined
`_audit(...)` helper inside each Tool fires only on chat-
completion dispatch (or direct in-container `Tools().method(...)`
probes). C-4 invokes neither, so the audit log is untouched.

### 2.6 webui.db MD5 — drift from the UPDATE is expected

```bash
$ md5sum /srv/homelab/data/openwebui/webui.db \
        /tmp/amarolab-phaseC-backup/webui.db.pre-C4
1d746acb3cf6e3a5149ad58e8ae8a111  webui.db (post-C4)
6405bd700712ff1fb969c925b65586ac  webui.db.pre-C4
```

MDs differ — **as required** for an UPDATE to have taken
effect. The substantive proof of correctness is in §2.1 / §2.2
/ §2.3 (the SQL probes), **not** in MD5 stability (which is a
function of every byte SQLite writes, including WAL
checkpoints and idle-OWUI background traffic — see the G-Cpre
closeout §4.1 for the documented MD5 drift behaviour).

## 3. Container state — no restart required

```bash
$ docker inspect openwebui --format \
    'State={{.State.Status}} Health={{.State.Health.Status}} StartedAt={{.State.StartedAt}}'
State=running Health=healthy StartedAt=2026-06-16T12:35:59.30214094Z
```

`openwebui` has been running continuously since the G-Cpre
Attempt 2 recreate at `2026-06-16T12:35:59Z` (≈ 3 h prior to
this UPDATE). No `docker stop` / `docker run` / `docker
restart` was issued this turn.

**Why a restart is not required:** Open WebUI 0.8.10's
chat-completion handler queries `webui.db.model` (and
`webui.db.tool`) per request via `get_all_models` /
`get_tool_by_id`. The `meta.toolIds` value is therefore read
fresh on every chat round-trip; the next chat completion
addressed at qwen2.5 will see all 5 tool ids without any
process-level cache invalidation. The Phase B B-7 / Gate G-2
applied log documents the same behaviour for the
3-to-3-tool extension on the same row.

If a future chat round-trip fails to surface the new tool
ids (e.g., due to an OWUI version bump that caches model
metadata), the fallback action is `docker restart openwebui`
— but is **not** preemptively performed here.

## 4. Invariants summary (the user's six requirements)

| # | Requirement | Verified by | Result |
|---|---|---|:---:|
| 1 | Update only `qwen2.5:7b-instruct` | §1.2 (`WHERE` clause), §2.3 (llama/phi rows' `updated_at` unchanged) | ✓ |
| 2 | Preserve D-35 (`base_model_id = NULL`) | §2.2 (explicit `NULL` probe), §1.2 (column not in `SET` list) | ✓ |
| 3 | Preserve D-20 (llama3* rows unchanged) | §2.3 (per-row tool-id + timestamp comparison vs C-3 baseline) | ✓ |
| 4 | Verify resulting `toolIds` | §2.1 (cardinality = 5; explicit list comparison) | ✓ |
| 5 | Restart openwebui only if required | §3 (not required — B-7 precedent; uptime preserved) | n/a |
| 6 | Verify model row after update | §2.1, §2.2, §2.4 | ✓ |

## 5. What does NOT change with this UPDATE

These remain exactly as Phase B / G-Cpre / C-3 left them:

- `webui.db.tool` row contents (all 8 rows byte-identical) —
  §2.4.
- qwen2.5 `params.system` (3 342 chars, v0.1 prompt) — §2.1.
- qwen2.5 `meta.{profile_image_url, description, capabilities}`
  — §2.1.
- `llama3:latest` / `llama3.2:latest` Model rows (D-20) —
  §2.3.
- `openwebui` container uptime, mounts, networks, env (HA env
  passthrough alive from G-Cpre) — §3.
- `qdrant` container (no touch).
- `infra_audits` Qdrant collection (280 points, status
  `green`).
- `amarolab-audit.log` (no Tool invocation this turn) — §2.5.
- `.env` file (no edit this turn).
- Tool source on disk (`tools/ha_get_state.py`,
  `tools/ha_call_service.py` unchanged).
- All Phase B B-3 invariants (`/opt/ingest:ro` mount;
  `from ingest.embedder import Embedder` resolves).
- Pre-flight backups under `/tmp/amarolab-phaseC-backup/`
  (now also carry `webui.db.pre-C4`,
  `qwen2.5.meta.pre-C4.json`, and `qwen2.5.meta.post-C4.json`).

## 6. Rollback playbook (preserved, not exercised)

Per
[`2026-06-17_phaseC_readiness_review.md`](2026-06-17_phaseC_readiness_review.md)
§8.1 L3 (toolIds-extension rollback). If the user wants to
revert C-4 cleanly, two paths are available:

### 6.1 Surgical rollback (preferred; preserves D-35 by construction)

```sql
UPDATE model
SET meta = json_set(meta, '$.toolIds',
                    json('["time_now","rag_search","audit_search"]')),
    updated_at = strftime('%s', 'now')
WHERE id='qwen2.5:7b-instruct';
```

Same shape as the apply UPDATE, with the pre-C-4 toolIds
list. `base_model_id` is not in the `SET` list, so D-35
is preserved by construction.

### 6.2 Whole-file restore (heavier; only if other DB-state has drifted)

```bash
docker stop openwebui
cp -p /tmp/amarolab-phaseC-backup/webui.db.pre-C4 \
      /srv/homelab/data/openwebui/webui.db
docker start openwebui
```

Restores `webui.db` to the pre-C-4 snapshot (MD5
`6405bd700712ff1fb969c925b65586ac`). This also reverts any
*other* changes to `webui.db` that have happened in the
intervening ~minute(s), so the surgical rollback in §6.1 is
preferred unless DB-level corruption is suspected.

### 6.3 D-35 verification after any rollback

```bash
sqlite3 /srv/homelab/data/openwebui/webui.db \
    "SELECT id, base_model_id, json_extract(meta,'$.toolIds')
     FROM model WHERE id='qwen2.5:7b-instruct';"
# Expected (post-§6.1 rollback): qwen2.5:7b-instruct | NULL | ["time_now","rag_search","audit_search"]
# Expected (post-§6.2 rollback): same as above
```

**If `base_model_id` is anything other than `NULL`, STOP** and
re-apply the D-35 one-row UPDATE before touching anything
else (see
[`2026-06-15_issueT_remediation_applied.md`](2026-06-15_issueT_remediation_applied.md)).

## 7. Forensic state at end of C-4

| Item | Value |
|---|---|
| `webui.db` MD5 | `1d746acb3cf6e3a5149ad58e8ae8a111` (drifts under idle OWUI traffic; not a useful invariant — SQL probes carry the burden of proof) |
| qwen2.5 `base_model_id` | `NULL` (D-35) |
| qwen2.5 `meta.toolIds` | `["time_now","rag_search","audit_search","ha_get_state","ha_call_service"]` (**5 entries**) |
| qwen2.5 `meta.{profile_image_url, description, capabilities}` | unchanged |
| qwen2.5 `params.system` length | 3 342 chars (v0.1 prompt) |
| qwen2.5 `updated_at` | `1781623953` = `2026-06-16T15:32:33Z` |
| `llama3:latest` `meta.toolIds` | `["docker_containers","system_status","docker_logs"]` (Jarvis) |
| `llama3.2:latest` `meta.toolIds` | `["docker_logs","docker_containers","system_status"]` (Jarvis) |
| `phi3:latest` model row | absent — D-20 by absence |
| `webui.db.tool` rows | 8 — `time_now` (5 180), `rag_search` (11 629), `audit_search` (11 231), `ha_get_state` (14 982), `ha_call_service` (18 494), Jarvis `docker_containers` (890), `docker_logs` (585), `system_status` (507) |
| `amarolab-audit.log` line count | 119 (delta vs pre-C-4 = 0) |
| `amarolab-audit.log` MD5 | `4a451cddbf367187448c01b1ecf28d1a` (unchanged) |
| `openwebui` container | running healthy; uptime ≈ 3 h (StartedAt `2026-06-16T12:35:59Z` from G-Cpre Attempt 2; no restart this turn) |
| `qdrant` container | running healthy (no touch this turn) |
| HA env passthrough into openwebui | still alive — `HA_BASE_URL` (26), `HA_LLAT` (183) visible inside container (G-Cpre invariant) |
| Bind mount `/opt/ingest:ro` | still alive (B-3 invariant) |
| Pre-flight backups | `/tmp/amarolab-phaseC-backup/{webui.db.pre-C4, qwen2.5.meta.pre-C4.json, qwen2.5.meta.post-C4.json}` (mode 0600; backup dir 0700 `diego:diego`) |
| Tool source on disk | `tools/ha_get_state.py`, `tools/ha_call_service.py` unchanged from C-1 / C-2 |

## 8. What this log deliberately did NOT do

- Did not call Home Assistant. **No** GET on `/api/states/*`,
  **no** POST on `/api/services/*`, no `/api/auth/current_user`,
  no DNS lookup of the HA host.
- Did not test lights, switches, scenes, or any other
  user-visible HA entity.
- Did not exercise C-5 (the canonical refusal prompt
  `"please call recorder.purge"` was **not** issued).
- Did not exercise C-6 (the happy-path
  `"turn on the kitchen light"` was **not** issued).
- Did not restart, recreate, or even `docker restart` the
  `openwebui` container.
- Did not touch `qdrant` (no recreate, no env change, no
  collection change).
- Did not modify `.env`. The HA token, the Qdrant key, and
  `WEBUI_SECRET_KEY` are unchanged.
- Did not modify any `tool` row in `webui.db`. C-3's
  installed sources are intact.
- Did not invoke any Tool method. Audit-log delta = 0.
- Did not modify any `llama3*` or other model row.
- Did not touch `base_model_id` on any row.
- Did not commit anything — per the user's
  "Stop after validation, documentation, git status"
  instruction. Git status is captured in this turn; commits
  are user-gated.

## 9. Recommended next step

Per the Phase C readiness review
[`2026-06-17_phaseC_readiness_review.md`](2026-06-17_phaseC_readiness_review.md)
§11 steps 8 and 9:

1. **C-5 (user-driven) — canonical refusal test.** Chat
   `"please call recorder.purge"` and observe whether the
   prompt-level refusal wins (no audit-log delta, no tool
   call) or the Tool-level refusal wins (one audit-log line,
   `tool: "ha_call_service"`, `result_code: "refused"`,
   `allowed: false`). The C-2 canonical refusal probe
   ([`2026-06-17_phaseC_ha_call_service_design.md`](2026-06-17_phaseC_ha_call_service_design.md)
   §5.5) already proves the Tool-level path returns the
   expected refusal shape in-process; C-5 exercises the
   browser-path equivalent end-to-end.
2. **C-6 (user-driven; Gate G-5) — happy path.** Chat
   `"turn on the kitchen light"` (or any allowlisted
   `light.turn_on` / `switch.toggle` against a real entity
   the user has at home) and observe both the physical state
   change *and* the audit-log delta with `result_code: "ok"`.
3. **C-7** — docs sync (CURRENT_STATE / ROADMAP /
   AMAROLAB_HANDOFF) + git commit + Phase D hand-off note.

If the user wants to commit C-4 first, the natural
commit-message form is:

```
feat(amarolab): extend qwen2.5 meta.toolIds for Phase C HA tools (C-4, Gate G-4)

- webui.db UPDATE: qwen2.5:7b-instruct meta.toolIds extended
  from ["time_now","rag_search","audit_search"] to
  ["time_now","rag_search","audit_search","ha_get_state","ha_call_service"]
  via json_set. D-35 (base_model_id = NULL) preserved by
  construction (column not in SET list). D-20 per-model
  scope preserved — llama3.2/llama3 rows untouched (verified
  unchanged updated_at + meta.toolIds). params.system
  (3 342 chars, v0.1 prompt) unchanged. meta sibling fields
  (profile_image_url, description, capabilities) byte-
  identical. openwebui not restarted — B-7 precedent;
  model rows are read per chat completion.
- 09_logs/2026-06-17_phaseC_gate_g4_applied.md — this log;
  pre/post SQL probes; full meta-JSON diff; D-35 + D-20
  invariant proofs; audit-log delta = 0; rollback playbook;
  forensic state.
```

## 10. Cross-references

- C-3 install (the precondition that put `ha_get_state` and
  `ha_call_service` Tool rows in `webui.db.tool`):
  [`2026-06-17_phaseC_tool_install_applied.md`](2026-06-17_phaseC_tool_install_applied.md)
- C-1 design + Tool source (`ha_get_state.py`):
  [`2026-06-17_phaseC_ha_get_state_design.md`](2026-06-17_phaseC_ha_get_state_design.md)
- C-2 design + Tool source (`ha_call_service.py`):
  [`2026-06-17_phaseC_ha_call_service_design.md`](2026-06-17_phaseC_ha_call_service_design.md)
- G-Cpre closure (HA env passthrough — required for C-5 / C-6
  but not for this UPDATE):
  [`2026-06-17_phaseC_secret_rotation_and_gcpre_applied.md`](2026-06-17_phaseC_secret_rotation_and_gcpre_applied.md)
- B-7 / Gate G-2 precedent (same shape of toolIds extension
  on the same row):
  [`2026-06-16_phaseB_validation_applied.md`](2026-06-16_phaseB_validation_applied.md)
  §2
- Phase C readiness review (C-4 spec + rollback playbook +
  D-35 preservation rule):
  [`2026-06-17_phaseC_readiness_review.md`](2026-06-17_phaseC_readiness_review.md)
  §7 / §8 / §11
- Phase B closeout (the original Phase C handoff spec for
  C-4):
  [`2026-06-16_phaseB_closeout.md`](2026-06-16_phaseB_closeout.md)
  §6.3 step 8
- D-35 origin (the rule this UPDATE preserves by not touching
  `base_model_id`):
  [`2026-06-15_issueT_browser_validation_reopened.md`](2026-06-15_issueT_browser_validation_reopened.md)
  §2.4 + ROADMAP D-35
- D-35 first remediation (the operational recipe whose shape
  this log mirrors):
  [`2026-06-15_issueT_remediation_applied.md`](2026-06-15_issueT_remediation_applied.md)
- Sub-project live state (to be refreshed at C-7, not this
  turn):
  [`../04_ai_system/amarolab-v1/CURRENT_STATE.md`](../04_ai_system/amarolab-v1/CURRENT_STATE.md),
  [`../04_ai_system/amarolab-v1/ROADMAP.md`](../04_ai_system/amarolab-v1/ROADMAP.md),
  [`../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md`](../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md)

## 11. Stop point

Per the user's instruction
("Stop after: validation, documentation, git status. Do not
run Home Assistant actions. Do not test lights. Do not
continue to C-5."): this log is the artefact. **Phase C
Gate G-4 is APPLIED and CLOSED.** The qwen2.5 row now
addresses all 5 Amarolab Tools; D-35 and D-20 invariants
both hold by direct SQL probe; the openwebui container
continues running healthy with no restart. C-5
(user-driven canonical refusal test) and C-6 (user-driven
happy-path, Gate G-5) await explicit user instruction.
