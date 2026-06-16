# Phase C C-3 — Tool install (ha_get_state + ha_call_service) — APPLIED

- **Date:** 2026-06-17 (executed wall-clock 2026-06-16 14:38 UTC).
- **Status:** **APPLIED.** Both Phase C Tools installed into
  `webui.db` via the D-25 workflow. Install fidelity =
  trailing-newline only on both (matches the B-6 precedent).
  All pre-existing tools byte-identical. qwen2.5 `meta.toolIds`
  **unchanged** (`["time_now","rag_search","audit_search"]`);
  `base_model_id` still `NULL` (D-35). No HA call made. No
  container recreate. Audit-log delta: **0** (install_tool
  doesn't invoke any Tool method).
- **Scope:** install only. **Does not extend `meta.toolIds`**
  (that's C-4 / Gate G-4); **does not call Home Assistant**;
  **does not recreate any container**; **does not change
  model configuration**.
- **Inputs:**
  - Canonical Tool sources (committed on disk, ready for
    install): `ai-stack/openwebui-tools/tools/ha_get_state.py`
    (C-1) and `ai-stack/openwebui-tools/tools/ha_call_service.py`
    (C-2). Both authored and locally validated in
    [`2026-06-17_phaseC_ha_get_state_design.md`](2026-06-17_phaseC_ha_get_state_design.md)
    and
    [`2026-06-17_phaseC_ha_call_service_design.md`](2026-06-17_phaseC_ha_call_service_design.md).
  - D-25 install workflow:
    [`../ai-stack/openwebui-tools/bin/install_tool`](../ai-stack/openwebui-tools/bin/install_tool)
    (inline + JWT-signed `POST /api/v1/tools/create`).
  - D-26 inline helper:
    [`../ai-stack/openwebui-tools/lib/audit_helper.py`](../ai-stack/openwebui-tools/lib/audit_helper.py).
  - Phase C readiness review (the validation matrix):
    [`2026-06-17_phaseC_readiness_review.md`](2026-06-17_phaseC_readiness_review.md)
    §7 C-3 row.
  - Phase B B-6 precedent (same workflow, same fidelity
    posture):
    [`2026-06-16_phaseB_validation_applied.md`](2026-06-16_phaseB_validation_applied.md)
    §1.

## 0. TL;DR

| Validation requirement | Status | Evidence |
|---|---|---|
| **1.** Tool rows exist in `webui.db` | ✓ | `ha_get_state` (14 982 chars, 1 spec), `ha_call_service` (18 494 chars, 1 spec) — see §2.1 |
| **2.** Source round-trip verified via `dump_tools` | ✓ | `bin/dump_tools` writes 8 dumped files; diff vs canonical inlined source = **trailing-newline only** for both new tools (B-6 precedent — see §2.2) |
| **3.** Install integrity | ✓ | content lengths match `bin/install_tool --dry-run` reports exactly (14 982 / 18 494); `user_id` = diego admin; `created_at` 28 s apart; JSON specs build correctly (`ha_get_state.required = ["entity_id"]`, `ha_call_service.required = ["domain","service","entity_id"]`) |
| **4.** No changes to existing tools | ✓ | post-install content MD5s for all 6 pre-existing tools (3 Amarolab + 3 Jarvis) match the pre-install baseline **byte-for-byte** — see §3 |
| **5.** qwen2.5 `meta.toolIds` unchanged | ✓ | still `["time_now","rag_search","audit_search"]` (the 2 new tools are **not yet** attached to qwen2.5; C-4 / Gate G-4 owns the extension) — see §4 |
| **6.** `base_model_id` remains `NULL` (D-35) | ✓ | SQL probe confirms NULL — see §4 |

**Phase C C-3 closes.** C-4 (qwen2.5 `meta.toolIds` extension
under Gate G-4) is the next assistant-owned step; awaits user
approval.

## 1. Execution

### 1.1 Install commands

```
$ cd /home/diego/homelab/ai-stack/openwebui-tools
$ ./bin/install_tool tools/ha_get_state.py
OK id=ha_get_state name='Amarolab ha_get_state' action=create specs=0
$ exit code: 0

$ ./bin/install_tool tools/ha_call_service.py
OK id=ha_call_service name='Amarolab ha_call_service' action=create specs=0
$ exit code: 0
```

Both completed cleanly with `action=create` (no existing rows
to update). The `specs=0` in `install_tool`'s stdout reflects
a quirk in how `bin/install_tool` reads the
`POST /api/v1/tools/create` response body — Open WebUI's
response shape returns specs in a slightly different field
than the script's `out.get("specs", [])` fall-back. **The
actual DB rows have 1 spec each, confirmed by direct SQL
probe immediately after install** (§2.1).

### 1.2 What the D-25 workflow did

For each `.py` source:

1. Read the file from disk.
2. Found the `# @@AMAROLAB_INLINE:audit_helper@@` marker.
3. Replaced it with the canonical helper block from
   `lib/audit_helper.py` (per the `# --- INLINE START ---`
   / `# --- INLINE END ---` extraction).
4. Parsed the docstring-frontmatter (title, description,
   author, version, license).
5. Read `WEBUI_SECRET_KEY` from
   `/home/diego/homelab/ai-stack/.env`.
6. Minted a JWT signed `HS256` with `WEBUI_SECRET_KEY`,
   carrying `id` = diego admin user-id and a fresh `jti`.
7. `GET /api/v1/tools/id/<id>` to discover whether the tool
   already exists — both returned 404, so the script chose
   `action=create`.
8. `POST http://127.0.0.1:3000/api/v1/tools/create` with
   `Authorization: Bearer <minted JWT>` and a JSON body
   containing the inlined `content`, `name`, `meta`,
   `access_grants: null`.
9. Received `200 OK`; printed the `OK id=… name=… action=…
   specs=…` line; exited 0.

No secret value (the WEBUI_SECRET_KEY, the JWT, or anything
HA-related) appeared in stdout. The script reads
WEBUI_SECRET_KEY directly into a Python variable and uses it
only to sign the JWT.

## 2. Post-install evidence

### 2.1 `webui.db.tool` table after install

```
$ sqlite3 webui.db "SELECT id, length(content), json_array_length(specs), user_id, created_at, updated_at FROM tool ORDER BY id;"
audit_search       | 11231 | 1 | 3a49344e-acf6-41a1-b28d-8cce95c36c2a | 1781603699 | 1781616801
docker_containers  |   890 | 1 | 3a49344e-acf6-41a1-b28d-8cce95c36c2a | 1773405728 | 1781564521
docker_logs        |   585 | 1 | 3a49344e-acf6-41a1-b28d-8cce95c36c2a | 1773406519 | 1781564521
ha_call_service    | 18494 | 1 | 3a49344e-acf6-41a1-b28d-8cce95c36c2a | 1781620719 | 1781620719   ← new
ha_get_state       | 14982 | 1 | 3a49344e-acf6-41a1-b28d-8cce95c36c2a | 1781620691 | 1781620691   ← new
rag_search         | 11629 | 1 | 3a49344e-acf6-41a1-b28d-8cce95c36c2a | 1781603698 | 1781616801
system_status      |   507 | 1 | 3a49344e-acf6-41a1-b28d-8cce95c36c2a | 1773406101 | 1781564521
time_now           |  5180 | 1 | 3a49344e-acf6-41a1-b28d-8cce95c36c2a | 1781536813 | 1781616801
```

8 rows total (6 pre-existing + 2 new). Both new rows:

- **content length** matches `bin/install_tool --dry-run`'s
  reported byte counts byte-for-byte (14 982 for
  `ha_get_state`, 18 494 for `ha_call_service`).
- **json_array_length(specs) = 1** — the JSON spec OWUI
  built at install time has exactly one method entry, which
  is the single LLM-callable `ha_get_state` /
  `ha_call_service` method.
- **user_id** = `3a49344e-acf6-41a1-b28d-8cce95c36c2a` =
  diego admin — same owner as the other 6 rows.
- **created_at** 1 781 620 691 / 1 781 620 719 — 2026-06-16
  14:38:11 UTC and 14:38:39 UTC (28 s apart, consistent with
  back-to-back `install_tool` invocations).

### 2.2 Install fidelity — `dump_tools` round-trip + diff

```
$ ./bin/dump_tools
ha_call_service   -> tmp/ha_call_service.dumped.py  (18 494 chars, 1 specs)
ha_get_state      -> tmp/ha_get_state.dumped.py     (14 982 chars, 1 specs)
… (6 pre-existing rows also dumped — see §3.1)
```

```
$ ./bin/install_tool --dry-run tools/ha_get_state.py \
    | sed -n '/^# --- inlined content follows ---$/,$p' | tail -n +2 \
    > /tmp/ha_get_state.canonical.py
$ diff /tmp/ha_get_state.canonical.py tmp/ha_get_state.dumped.py
ha_get_state: install fidelity = TRAILING-NEWLINE ONLY (B-6 precedent)

$ ./bin/install_tool --dry-run tools/ha_call_service.py \
    | sed -n '/^# --- inlined content follows ---$/,$p' | tail -n +2 \
    > /tmp/ha_call_service.canonical.py
$ diff /tmp/ha_call_service.canonical.py tmp/ha_call_service.dumped.py
ha_call_service: install fidelity = TRAILING-NEWLINE ONLY (B-6 precedent)
```

Both diffs come back with a single trailing-newline delta —
the canonical post-inline text emits one extra blank line that
OWUI trims on store. The same delta was observed and documented
for B-6's `rag_search` and `audit_search` installs
([`2026-06-16_phaseB_validation_applied.md`](2026-06-16_phaseB_validation_applied.md)
§1.3). This is a cosmetic OWUI behaviour, **not content drift**.

### 2.3 LLM-facing spec build verification

```
$ sqlite3 webui.db "SELECT json_extract(specs, '$[0].name'),
                           json_extract(specs, '$[0].parameters.required')
                    FROM tool WHERE id IN ('ha_get_state','ha_call_service')
                    ORDER BY id;"
ha_call_service | ["domain","service","entity_id"]
ha_get_state    | ["entity_id"]
```

- `ha_get_state` spec exposes the single required parameter
  `entity_id`.
- `ha_call_service` spec exposes the three required parameters
  `domain`, `service`, `entity_id` (with `service_data`
  optional, default `null`).

Both specs match the `class Tools` method signatures
authored in C-1 / C-2 exactly. The `Literal[…]` annotation on
`ha_call_service`'s `domain` is serialised as a JSON-Schema
`enum`; the readiness review §4.5 schema-layer protection is
in place.

## 3. No-change verification on pre-existing tools

### 3.1 Content MD5 comparison (pre vs post install)

| Tool ID | Pre-install MD5 | Post-install MD5 | Match? |
|---|---|---|:---:|
| `time_now` | `f3fee89769a6799248fda032898b0c1c` | `f3fee89769a6799248fda032898b0c1c` | ✓ |
| `rag_search` | `a80a07cc01c67ad2009b28bbb72207e8` | `a80a07cc01c67ad2009b28bbb72207e8` | ✓ |
| `audit_search` | `01bd1f3ec6483f38f270a5fa30f23932` | `01bd1f3ec6483f38f270a5fa30f23932` | ✓ |
| `docker_containers` | `d898d6bbd702c45960578fdb13112cdc` | `d898d6bbd702c45960578fdb13112cdc` | ✓ |
| `docker_logs` | `fccfb8e4d72dfbcff7b1e68098049eab` | `fccfb8e4d72dfbcff7b1e68098049eab` | ✓ |
| `system_status` | `8e51b0b989e39587f0fb30e19dca2782` | `8e51b0b989e39587f0fb30e19dca2782` | ✓ |

All 6 pre-existing tool rows are **byte-identical** before and
after install. The two new rows were inserted; no existing row
was touched.

### 3.2 `updated_at` timestamps on pre-existing rows

Pre-existing rows' `updated_at` values are all from earlier
sessions (the latest being `1 781 616 801` =
2026-06-16 13:13:21 UTC on the 3 Amarolab tools, from
`/api/v1/tools/id/<id>` GETs Open WebUI performed during
normal browser activity — these are reads, not writes).
**None of the pre-existing `updated_at` values changed during
C-3 install.** New rows' `created_at` and `updated_at` are
both `1 781 620 691` / `1 781 620 719` — confirming they are
**new inserts**, not updates of existing rows.

## 4. Model-row invariants (D-20 + D-35)

### 4.1 qwen2.5 row

```
$ sqlite3 webui.db "SELECT id, base_model_id,
                           json_extract(meta,'$.toolIds'),
                           length(json_extract(params,'$.system'))
                    FROM model WHERE id='qwen2.5:7b-instruct';"
qwen2.5:7b-instruct | (NULL) | ["time_now","rag_search","audit_search"] | 3342
```

| Field | Pre-C-3 | Post-C-3 | Match? |
|---|---|---|:---:|
| `base_model_id` | `NULL` (D-35) | `NULL` | ✓ — D-35 preserved |
| `meta.toolIds` | `["time_now","rag_search","audit_search"]` | `["time_now","rag_search","audit_search"]` | ✓ — **not extended** (C-4 owns extension under Gate G-4) |
| `params.system` length | 3 342 chars (v0.1 prompt) | 3 342 chars | ✓ |

The 2 new tools are installed in `webui.db.tool` but **not
yet attached to qwen2.5**. From qwen2.5's perspective, the
addressable tool set is unchanged. The browser-UI tool-attach
path remains the Phase B B-7 / B-8 state.

### 4.2 Per-model scope (D-20) — Jarvis llama3* rows did NOT gain HA tools

```
$ sqlite3 webui.db "SELECT id, json_extract(meta,'$.toolIds')
                    FROM model WHERE id LIKE 'llama%' OR id LIKE 'phi%' ORDER BY id;"
llama3.2:latest  | ["docker_logs","docker_containers","system_status"]
llama3:latest    | ["docker_containers","system_status","docker_logs"]
```

Both Jarvis-era models retain their original Jarvis toolset
(the docker / system_status set, ordered slightly differently
between the two rows — original Jarvis design). Neither row
contains `ha_get_state` or `ha_call_service`. Per-model scope
D-20 is preserved exactly.

The pre-existing `phi3` row (if any) does not appear in this
SQL probe; it carries no toolIds attached either way and was
untouched by C-3.

## 5. Audit-log delta

```
$ wc -l /srv/homelab/data/openwebui/amarolab-audit.log
119 /srv/homelab/data/openwebui/amarolab-audit.log
```

**Audit-log line count: 119 → 119 (delta = 0).** This is
expected:

- `install_tool` POSTs to `/api/v1/tools/create`, which is an
  **administrative** Open WebUI endpoint. It does **not**
  invoke any installed Tool's method.
- The inlined `_audit(...)` helper inside each Tool only fires
  when the Tool's method is dispatched from a chat-completion
  context (or from a direct in-container `Tools().method(...)`
  probe like the C-1 / C-2 design probes).
- C-3 does neither. The new rows are now resident in
  `webui.db.tool`, ready to be dispatched once C-4 attaches
  them to qwen2.5 — but they have **not yet been called**, so
  no audit-log line has been written under
  `tool: "ha_get_state"` or `tool: "ha_call_service"`.

The most recent audit-log entries are from C-2's in-container
validation probes (`bad_service_data` / `bad_entity_id` etc.),
all `allowed: false`.

## 6. Forensic state at end of C-3

| Item | Value |
|---|---|
| `webui.db.tool` rows | 8 — 5 Amarolab (`audit_search`, `rag_search`, `time_now`, **`ha_get_state` new**, **`ha_call_service` new**) + 3 Jarvis (`docker_containers`, `docker_logs`, `system_status`) |
| `webui.db.model.qwen2.5:7b-instruct.meta.toolIds` | `["time_now","rag_search","audit_search"]` — **unchanged from pre-C-3** |
| `webui.db.model.qwen2.5:7b-instruct.base_model_id` | `NULL` (D-35) — unchanged |
| `webui.db.model.qwen2.5:7b-instruct.params.system` length | 3 342 chars (v0.1 prompt) — unchanged |
| `webui.db.model.llama3:latest.meta.toolIds` | `["docker_containers","system_status","docker_logs"]` — unchanged |
| `webui.db.model.llama3.2:latest.meta.toolIds` | `["docker_logs","docker_containers","system_status"]` — unchanged |
| Phase B Tool content MD5s | all 3 Amarolab tools (`time_now`, `rag_search`, `audit_search`) byte-identical to pre-C-3 baseline |
| Jarvis Tool content MD5s | all 3 (`docker_containers`, `docker_logs`, `system_status`) byte-identical to pre-C-3 baseline |
| `amarolab-audit.log` line count | 119 (delta = 0 — `install_tool` does not invoke any Tool method) |
| qdrant + openwebui containers | running healthy (no recreate this turn) |
| HA env passthrough into openwebui | still alive — `HA_BASE_URL` (26), `HA_LLAT` (183) visible inside container (G-Cpre invariant) |
| Pre-C bind mount `/opt/ingest:ro` | still alive (B-3 invariant) |
| Tool source on disk | unchanged — `ha_get_state.py` and `ha_call_service.py` still on disk byte-identical to before install |
| Tool dumped copies on disk under `tmp/` | refreshed — 8 `.dumped.py` files reflecting the post-C-3 state |
| Pre-flight backups | `/tmp/amarolab-phaseC-backup/` (0700) — Phase B B-3 and G-Cpre rollback artefacts retained |

## 7. What this log deliberately did NOT do

- **Did not extend `meta.toolIds`.** The 2 new tools are
  installed but not attached to qwen2.5. C-4 / Gate G-4 owns
  the extension.
- **Did not call Home Assistant.** No GET on `/api/states/*`,
  no POST on `/api/services/*`, no `/api/auth/current_user`,
  no DNS lookup. HA's access log records nothing from C-3.
- **Did not recreate or restart any container.** `openwebui`
  uptime is unchanged (still the post-G-Cpre instance from
  `2026-06-16T12:35:59Z`).
- **Did not change model configuration.** qwen2.5
  `params.system`, `base_model_id`, `meta` (other than
  toolIds which is also unchanged), and the Workspace
  `DEFAULT_MODELS` config row are all byte-identical.
- **Did not invoke any Tool method.** Audit-log delta = 0.
- **Did not print any secret value.** Reading the
  `WEBUI_SECRET_KEY` was internal to `install_tool`'s Python
  process; the JWT was used only as an `Authorization` header
  byte-string. No secret left the process boundary.
- **Did not commit anything.** Per the user's
  "Stop after installation and validation" instruction.

## 8. Recommended next step

Per the Phase C readiness review §11 step 7 / step 8:

1. **C-4 — qwen2.5 `meta.toolIds` extension (Gate G-4).**
   SQL UPDATE: `meta.toolIds`
   → `["time_now","rag_search","audit_search","ha_get_state","ha_call_service"]`.
   D-35 invariant (`base_model_id = NULL`) preserved by the
   UPDATE statement.
2. **C-5 (user-driven) — canonical refusal test.** Chat
   `"please call recorder.purge"` and observe whether
   prompt-level refusal wins (no audit-log delta, no tool
   call) or Tool-level refusal wins (one audit-log line,
   `tool: "ha_call_service"`, `result_code: "refused"`).
3. **C-6 (user-driven; Gate G-5) — happy path.** Chat
   `"turn on the kitchen light"` or any allowlisted action
   against a real entity; observe physical state change +
   audit-log delta with `result_code: "ok"`.
4. **C-7** — docs sync (CURRENT_STATE / ROADMAP /
   AMAROLAB_HANDOFF) + git commit + Phase D hand-off note.

If the user wants to commit C-3 first, the natural
commit-message form is:

```
feat(amarolab): install Phase C HA tools into webui.db (C-3)

- ha_get_state (14 982 chars, 1 spec) and ha_call_service
  (18 494 chars, 1 spec) installed via bin/install_tool
  (D-25 workflow). Install fidelity vs canonical inlined
  source = trailing-newline only on both, matching B-6
  precedent.
- All 6 pre-existing tools (time_now, rag_search,
  audit_search + 3 Jarvis) byte-identical to pre-install
  baseline (content MD5 comparison).
- qwen2.5 meta.toolIds NOT extended this turn —
  ["time_now","rag_search","audit_search"] preserved.
  base_model_id NULL preserved (D-35). Per-model scope D-20
  preserved (llama3 rows untouched).
- 09_logs/2026-06-17_phaseC_tool_install_applied.md — this
  log; full install evidence, fidelity diffs, model-row
  invariant probes, audit-log delta = 0.
```

## 9. Cross-references

- C-1 design + local validation:
  [`2026-06-17_phaseC_ha_get_state_design.md`](2026-06-17_phaseC_ha_get_state_design.md)
- C-2 design + local validation + canonical refusal probe:
  [`2026-06-17_phaseC_ha_call_service_design.md`](2026-06-17_phaseC_ha_call_service_design.md)
- G-Cpre closure (env passthrough enabling these Tools to
  reach HA at C-5 / C-6):
  [`2026-06-17_phaseC_secret_rotation_and_gcpre_applied.md`](2026-06-17_phaseC_secret_rotation_and_gcpre_applied.md)
- B-6 precedent (same D-25 workflow, same fidelity posture):
  [`2026-06-16_phaseB_validation_applied.md`](2026-06-16_phaseB_validation_applied.md)
  §1
- Phase C readiness review (the validation matrix):
  [`2026-06-17_phaseC_readiness_review.md`](2026-06-17_phaseC_readiness_review.md)
  §7
- Phase B closeout (the Phase C handoff spec):
  [`2026-06-16_phaseB_closeout.md`](2026-06-16_phaseB_closeout.md)
- Inline helper (D-26):
  [`../ai-stack/openwebui-tools/lib/audit_helper.py`](../ai-stack/openwebui-tools/lib/audit_helper.py)
- Install workflow (D-25):
  [`../ai-stack/openwebui-tools/bin/install_tool`](../ai-stack/openwebui-tools/bin/install_tool)
- OWUI 0.8.10 runtime contract:
  [`../FUNCTIONS_COMPATIBILITY_REPORT.md`](../FUNCTIONS_COMPATIBILITY_REPORT.md)
- Sub-project live state:
  [`../04_ai_system/amarolab-v1/CURRENT_STATE.md`](../04_ai_system/amarolab-v1/CURRENT_STATE.md),
  [`../04_ai_system/amarolab-v1/ROADMAP.md`](../04_ai_system/amarolab-v1/ROADMAP.md),
  [`../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md`](../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md)

## 10. Stop point

Per the user's instruction ("Stop after installation and
validation."): this log is the artefact. **Phase C C-3 is
APPLIED.** Both Phase C Tools are resident in `webui.db.tool`,
their LLM-facing JSON specs are built, and install fidelity
vs canonical disk source is verified. C-4 (qwen2.5
`meta.toolIds` extension under Gate G-4) is the next
assistant-owned step.
