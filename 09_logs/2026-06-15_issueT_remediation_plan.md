# Issue T (B-09) — remediation PLAN — NOT YET APPLIED

- **Date drafted:** 2026-06-16 (filename keeps the `2026-06-15` UTC
  prefix to chain with the prior Issue T documents).
- **Status:** **PLAN ONLY. No state is modified by this document.**
  Each numbered step below is a *proposed* action; nothing is
  executed until the user issues an explicit "apply" instruction in
  a separate turn.
- **Goal:** Restore the browser-UI tool-calling path for
  `qwen2.5:7b-instruct` so that the `time_now` Tool actually fires
  end-to-end from a real browser chat. After this plan is applied,
  Phase B can resume from a fully-working A.3 baseline.
- **Root cause being remediated:** the qwen2.5 Model entry has
  `base_model_id = "qwen2.5:7b-instruct"` (same string as its `id`),
  which sends it to the `elif … continue` skip branch in
  `utils/models.py:159–175`. The custom entry is silently dropped
  from the merged `/api/models`, so the browser's auto-attach
  cannot read `info.meta.toolIds`, so `tool_ids` is omitted from
  the chat-completion body, so OWUI never offers `time_now` to the
  model. Full evidence in
  [`2026-06-15_issueT_browser_validation_reopened.md`](2026-06-15_issueT_browser_validation_reopened.md)
  §2.4 / §2.5.
- **Out of scope for this plan** (tracked separately, see §10):
  the three undocumented Tools (`docker_containers`,
  `system_status`, `docker_logs`) scoped to `llama3:latest`; the
  v0.2 prompt iteration; the BX browser-UI WebSocket race; any new
  Tool implementation; Phase B kick-off.

## 0. TL;DR — the five required steps, in order

| # | Step | Estimated time | Reversible? |
|---|---|---|---|
| 1 | **Backup `webui.db`** to `/tmp/amarolab-issueT-reopen-backup/` | < 1 s | n/a (read-only) |
| 2 | **Apply the smallest possible fix:** one SQL UPDATE setting `base_model_id = NULL` on the qwen2.5 row | < 1 s | yes — restore from §1 backup |
| 3 | **Force the OWUI in-memory model cache to refresh** (one curl with admin JWT, or container restart) | 1–3 s | n/a (cache rebuild) |
| 4 | **Browser validation:** open `http://localhost:3000`, send `"¿qué hora es?"`, confirm the rendered reply contains a real wall-clock time and no literal `time_now(` | ~30 s | n/a (read-only chat) |
| 5 | **Audit-log verification + documentation updates:** confirm `+1` line in `amarolab-audit.log` with `tool: "time_now"` / `result_code: "ok"`; then update three live state docs and write the apply log | 10–15 min | reversible via git revert / restore from backup |

**Total active wall-clock time:** ~15 minutes, of which ~14 are
documentation. The change itself is one SQL statement.

## 1. Preconditions before applying

All of these must be true at apply time. Verify with the
**Pre-flight check** snippet in §2.

| Precondition | Why it matters |
|---|---|
| `openwebui` container is **Up (healthy)** | the cache-refresh step (§4) goes through the live app |
| `ollama` container is **Up** with `qwen2.5:7b-instruct` warm-loadable | the post-fix browser turn (§5) must reach Ollama |
| Audit log line count is **96** (matches end of [`2026-06-15_issueT_browser_validation_reopened.md`](2026-06-15_issueT_browser_validation_reopened.md) §7) | establishes the **+1** baseline for §6 |
| `webui.db` mtime matches the value recorded in [`…browser_validation_reopened.md`](2026-06-15_issueT_browser_validation_reopened.md) §7 (`2026-06-15 23:45:04 CEST`) or has only legitimate intervening writes | no surprise DB activity between investigation and remediation |
| qwen2.5 Model entry still has `base_model_id = "qwen2.5:7b-instruct"`, `meta.toolIds = ["time_now"]`, and `params.system` = v0.1 prompt (3 342 chars) | confirms we are fixing the same row the investigation diagnosed |
| `time_now` Tool row still present, content length 5 180 chars | the fix is irrelevant if the Tool isn't installed |
| User has `sudo` access **OR** can read `WEBUI_SECRET_KEY` from `/home/diego/homelab/ai-stack/.env` (mode 0600) | needed to mint the admin JWT for §4's cache-refresh call **only if** that path is chosen (the container-restart alternative does not need it) |
| Browser available on the host (`localhost:3000`) with a logged-in admin session | for §5 |
| **No active Open WebUI chat session in progress** by another human/automation against `qwen2.5:7b-instruct` | avoids racing with our cache refresh |

## 2. Pre-flight check (run BEFORE any change)

Read-only. Confirms every precondition in §1.

```bash
# 1. container health
docker ps --filter name=openwebui --filter name=ollama \
  --format 'table {{.Names}}\t{{.Status}}'

# 2. audit log line count + last line
wc -l /srv/homelab/data/openwebui/amarolab-audit.log
tail -1 /srv/homelab/data/openwebui/amarolab-audit.log

# 3. webui.db mtime + size
stat -c 'size=%s mtime=%y' /srv/homelab/data/openwebui/webui.db

# 4. qwen2.5 Model-entry shape (the row we are about to change)
sqlite3 /srv/homelab/data/openwebui/webui.db \
  "SELECT id, base_model_id, length(params), length(meta),
          json_extract(meta,'\$.toolIds')
   FROM model WHERE id='qwen2.5:7b-instruct';"

# 5. time_now Tool presence + content length
sqlite3 /srv/homelab/data/openwebui/webui.db \
  "SELECT id, length(content) FROM tool WHERE id='time_now';"
```

**Expected output (must match before proceeding):**

```
NAMES         STATUS
openwebui     Up X hours (healthy)
ollama        Up X hours

96 /srv/homelab/data/openwebui/amarolab-audit.log
{... "tool": "time_now", "result_code": "ok", ...}   ts ≤ 2026-06-15T20:58:22Z

size=2347008 mtime=2026-06-15 23:45:04.... +0200
# (mtime is allowed to be the same OR later if you have benign reads
# in between; size must be 2 347 008 to ensure no in-between writes)

qwen2.5:7b-instruct|qwen2.5:7b-instruct|<~3514>|<~231>|["time_now"]

time_now|5180
```

If **any** field diverges from the above:
- a value indicates DB drift since the investigation closed → stop
  and re-run the investigation steps in §2 of
  [`…browser_validation_reopened.md`](2026-06-15_issueT_browser_validation_reopened.md)
  before applying.
- container not healthy → fix that first; do not proceed.

## 3. Step 1 — Backup `webui.db`

**Action:**

```bash
sudo mkdir -p /tmp/amarolab-issueT-reopen-backup
sudo cp -a /srv/homelab/data/openwebui/webui.db \
           /tmp/amarolab-issueT-reopen-backup/webui.db.pre-base_model_id-fix
sudo chown -R diego:diego /tmp/amarolab-issueT-reopen-backup
```

**Verification:**

```bash
ls -la /tmp/amarolab-issueT-reopen-backup/
sha256sum /tmp/amarolab-issueT-reopen-backup/webui.db.pre-base_model_id-fix
sha256sum /srv/homelab/data/openwebui/webui.db
# two hashes must be identical at this moment
```

**Why `cp -a`:** preserves mode, owner (root:root inside container,
diego:diego on host — already 0644 / diego:diego per the prior
investigation), atime/mtime, so a future restore is byte-identical.

**Where the existing pre-flight backups live (do not delete):**

| Backup file | When taken | Why kept |
|---|---|---|
| `/tmp/amarolab-phaseA4-backup/webui.db.pre-A4` | pre-A.4 v0 apply | rollback reference for Phase A.4 work |
| `/tmp/amarolab-phaseA4-v0_1-backup/webui.db.pre-v0_1` | pre-A.4 v0.1 apply | rollback to v0 prompt state |
| `/tmp/amarolab-issueT-reopen-backup/webui.db.pre-base_model_id-fix` | **(this step)** | rollback for this fix |

The three live independently; none is overwritten by this step.

## 4. Step 2 — Apply the smallest possible fix

**The change:** one column on one row of one table.

```sql
UPDATE model
SET    base_model_id = NULL,
       updated_at    = CAST(strftime('%s','now') AS INTEGER)
WHERE  id = 'qwen2.5:7b-instruct';
```

`updated_at` is bumped so a later forensic read can correlate this
change with this log's date. Setting it is optional (the Model
entry's `updated_at` was already stale per the investigation §2.7)
but recommended for cleanliness.

**Two ways to issue the UPDATE — pick ONE:**

### 4.A SQL directly against the SQLite file (preferred — smallest)

```bash
# Stop briefly to avoid SQLite write contention with the live app.
# The 1-line UPDATE finishes in <10 ms; the stop window is ~3 s.
docker stop openwebui

sqlite3 /srv/homelab/data/openwebui/webui.db <<'SQL'
BEGIN IMMEDIATE;
UPDATE model
SET    base_model_id = NULL,
       updated_at    = CAST(strftime('%s','now') AS INTEGER)
WHERE  id = 'qwen2.5:7b-instruct';
SELECT changes() AS rows_updated;
COMMIT;
SQL

docker start openwebui
```

- `BEGIN IMMEDIATE` takes the reserved lock atomically; without it
  a concurrent reader can transiently see the partial state.
- `SELECT changes()` must return `1`. If `0`, the WHERE didn't
  match — abort, restore from §3 backup, re-check preconditions.
- Docker `stop` + `start` makes the openwebui container re-read
  `webui.db` cleanly on boot and rebuild `app.state.MODELS` from
  scratch. **This also satisfies §5 (cache refresh) and §10's
  "no separate restart needed" simplification.**

**Trade-off:** ~3 seconds of UI downtime. Acceptable.

### 4.B Live SQL with the container running (no stop, slightly riskier)

```bash
sqlite3 /srv/homelab/data/openwebui/webui.db <<'SQL'
PRAGMA busy_timeout = 5000;
BEGIN IMMEDIATE;
UPDATE model
SET    base_model_id = NULL,
       updated_at    = CAST(strftime('%s','now') AS INTEGER)
WHERE  id = 'qwen2.5:7b-instruct';
SELECT changes();
COMMIT;
SQL
```

Then **must** run §5 separately (cache refresh) for the change to
take effect.

**Trade-off:** zero downtime, but if `busy_timeout` runs out
because the live app is in the middle of a long write, the UPDATE
fails — retry. Lower-risk to just take 3 s of downtime via §4.A.

### 4.C API-based update (not recommended for this fix)

Open WebUI exposes `POST /api/v1/models/model/update/{id}`. Using
it for one column requires (a) minting a WEBUI_SECRET_KEY JWT,
(b) GETting the current model record, (c) merging
`base_model_id: null` and posting it back. **More moving parts,
same effect.** Recommended only if the user wants to avoid sqlite3
entirely. Not detailed here.

**Recommendation:** **§4.A.** Smallest, atomic, self-verifying via
`SELECT changes()`.

## 5. Step 3 — Force the model cache to refresh

Only needed if §4.B was used (live SQL without container stop). If
§4.A was used, the cache is already cold-rebuilt by the
`docker stop` + `docker start` — **skip this step**.

If §4.B was used:

```bash
# Mint an admin JWT (same pattern install_tool already uses)
SECRET=$(grep '^WEBUI_SECRET_KEY=' /home/diego/homelab/ai-stack/.env \
         | cut -d= -f2)

TOKEN=$(python3 -c "
import jwt, uuid
print(jwt.encode(
    {'id':'3a49344e-acf6-41a1-b28d-8cce95c36c2a','jti':str(uuid.uuid4())},
    '$SECRET', algorithm='HS256'))")

# Force-refresh
curl -fsS -H "Authorization: Bearer $TOKEN" \
  'http://127.0.0.1:3000/api/v1/models?refresh=true' \
  | python3 -c 'import json,sys;
d=json.load(sys.stdin);
m=[x for x in d.get("data",[]) if x["id"]=="qwen2.5:7b-instruct"]
print("info.meta.toolIds:", m[0].get("info",{}).get("meta",{}).get("toolIds"))'
```

**Expected:** `info.meta.toolIds: ['time_now']`. If `None` or the
key is missing, the refresh didn't take effect — fall back to
`docker restart openwebui`.

**Post-cache verification (independent — works after either §4.A
or §4.B):**

```bash
# In-container Python eval — same shape as the investigation's
# probe in §2.4 of the reopened log; this one is read-only.
docker exec openwebui python3 -c "
import asyncio, sys
sys.path.insert(0,'/app/backend')
from open_webui.utils.models import get_all_models
from open_webui.models.users import Users
from unittest.mock import MagicMock
async def main():
    user = Users.get_user_by_email('diego_va_amaro@hotmail.com')
    from open_webui.main import app
    req = MagicMock(); req.app = app
    models = await get_all_models(req, refresh=True, user=user)
    qwen = [m for m in models if m.get('id')=='qwen2.5:7b-instruct'][0]
    print('has info :', 'info' in qwen)
    print('toolIds  :', qwen.get('info',{}).get('meta',{}).get('toolIds'))
asyncio.run(main())
" 2>&1 | tail -3
```

**Expected:**
```
has info : True
toolIds  : ['time_now']
```

**Failure mode:** if `has info` is still `False`, the SQL UPDATE
didn't land. Re-run §4 inspection (`SELECT base_model_id FROM
model WHERE id='qwen2.5:7b-instruct';` must now print empty/null).

## 6. Step 4 — Browser validation (the test that originally failed)

This is the exact step the prior closeout claimed was done but
wasn't, and that the user ran today and saw fail.

### 6.1 Environment

- Browser: any modern Chrome / Firefox / Safari on the host or LAN.
- URL: `http://localhost:3000` (or `http://192.168.178.<host>:3000`
  if testing from another LAN device).
- **Apply BX workaround** from
  [`2026-06-15_openwebui_json_parse_error_analysis.md`](2026-06-15_openwebui_json_parse_error_analysis.md)
  §7.1 to avoid the unrelated WebSocket-race JSON parse error:
  1. Hit the URL directly (do **not** route via cloudflared or
     nginx-proxy-manager for this test).
  2. Hard-refresh: Ctrl+Shift+R.
  3. Wait until the UI's connection indicator is solid green
     before sending anything.

### 6.2 Test 1 — Spanish, the canonical user query

1. Open a new chat. Confirm the active model is
   `qwen2.5:7b-instruct` (the workspace default since
   Phase A.4 v0).
2. Confirm the tool chip / picker in the composer shows
   `time_now` selected. If it shows the dropdown empty,
   `info.meta.toolIds` is not flowing — go back to §5.
3. Send: `¿qué hora es?`
4. **Expected reply shape:** prose starting with
   `"Soy Amarolab Assistant ..."` (first-turn intro per D-32),
   then a sentence containing a real wall-clock time like
   `"son las 00:32 CEST"` or
   `"Son las 12:32 (UTC: 10:32) del martes 16 de junio de 2026."`,
   ending with a `[1] time_now (...)` footer line **if** the model
   chooses to cite.
5. **Pass conditions** (all three must hold):
   - reply contains an HH:MM digit pattern matching the wall
     clock at send time ± 2 minutes,
   - reply does **NOT** contain the literal substring `time_now(`
     anywhere outside the optional `[1]` citation footer,
   - reply does **NOT** contain a strftime format string like
     `%Y-%m-%d` or `%H:%M:%S`.

### 6.3 Test 2 — English, second-turn (no intro)

Still in the same chat, immediately follow with:

`and in Tokyo right now?`

**Expected:** an English reply (no Spanish), no second
"I am Amarolab Assistant" line (per D-32 "first turn only"),
with an `Asia/Tokyo` wall-clock time.

### 6.4 Test 3 — Devtools confirmation (one-time, optional but recommended)

In a fresh chat:
1. Open browser DevTools → Network tab → filter `chat/completions`.
2. Send `¿qué hora es?`.
3. Click the `POST /api/chat/completions` request → Payload (or
   Request).
4. **Confirm the JSON body contains** `"tool_ids": ["time_now"]`.

This is the single observation that would have short-circuited
the entire prior Issue T misdiagnosis. Doing it once after the
fix lands closes the loop permanently.

### 6.5 Failure handling

If Test 1 fails with the SAME pre-fix symptom (reply contains
`time_now("Europe/Madrid", format=...)` and audit log unchanged):

1. Verify §5 actually refreshed the cache — re-run the eval.
2. Verify `webui.db` actually has `base_model_id = NULL` for
   qwen2.5 (a single `SELECT`).
3. If both look right but the browser still misbehaves, capture
   the failing request body from Test 3's devtools panel and
   reopen B-09 again with the captured body.

If Test 1 fails with a DIFFERENT symptom (e.g., JSON parse error,
WebSocket disconnect, model timeout), that is **not** this fix's
concern — see BX (browser-UI WebSocket race) or the relevant
log.

## 7. Step 5a — Audit-log execution verification

```bash
# Before Test 1 (note the line count from §2 — should be 96)
WC_PRE=$(wc -l < /srv/homelab/data/openwebui/amarolab-audit.log)
echo "pre:  $WC_PRE"

# Run Test 1 (browser send "¿qué hora es?")
# Then:

WC_POST=$(wc -l < /srv/homelab/data/openwebui/amarolab-audit.log)
echo "post: $WC_POST"
echo "delta: $((WC_POST - WC_PRE))"

tail -1 /srv/homelab/data/openwebui/amarolab-audit.log \
  | python3 -c "import json,sys; d=json.loads(sys.stdin.read());
print(' ts:        ', d['ts']);
print(' tool:      ', d['tool']);
print(' user:      ', d['user']);
print(' allowed:   ', d['allowed']);
print(' result_code:', d['result_code']);
print(' duration:  ', d.get('duration_ms'), 'ms')"
```

**Pass criteria** (all must hold):

| Field | Expected |
|---|---|
| delta after Test 1 | `1` (or `2` if the user also ran Test 2 immediately — each successful Test adds one line) |
| `tool` | `"time_now"` |
| `user` | `"diego"` |
| `allowed` | `true` |
| `result_code` | `"ok"` |
| `duration_ms` | a small integer (typically 5–100 ms) |
| `ts` | within ±10 s of when the browser send was clicked |

If `delta == 0` even though the browser reply was correct, that is
a **serious red flag** — it means the model is somehow getting the
right answer without invoking the Tool. Stop and re-investigate
before declaring success; this would imply the model is
hallucinating a correct time, not actually calling.

## 8. Step 5b — Documentation updates (after §7 passes)

All edits below are **rewrites in place** to the three live state
files, plus a single new application log. No design doc (`01..05`,
`README.md`) is touched — those are immutable for v1.

### 8.1 Write the apply log (new file)

Path: `09_logs/2026-06-15_issueT_remediation_applied.md`

Mirror the structure of `2026-06-15_phaseA3-tool-canary-applied.md`
and `2026-06-15_phaseA4-prompt-v0.1-applied.md`. Sections:

- Date applied (the actual apply date — likely
  `2026-06-16`).
- Pre-flight diffs (output of §2 vs. expected; backup hash).
- Apply action (SQL + path chosen — §4.A or §4.B).
- Post-apply DB state (`SELECT * FROM model WHERE id='qwen2.5:7b-instruct'`
  with the new `base_model_id IS NULL`, new `updated_at`).
- Cache-refresh evidence (either container start log
  showing `app.state.MODELS` rebuilt, or the curl response from
  §5 confirming `info.meta.toolIds`).
- §6 browser validation results — actual reply text, devtools
  body snippet (Test 3), pass/fail per §6.5.
- §7 audit-log delta with the new JSONL line(s).
- Forensic state at end of apply (mirrors the table in
  [`…browser_validation_reopened.md`](2026-06-15_issueT_browser_validation_reopened.md)
  §7).
- "What this apply did NOT change" boilerplate (no prompt change,
  no new Tool, no env var, no container compose change, etc.).

### 8.2 Update `04_ai_system/amarolab-v1/CURRENT_STATE.md`

| Section | Edit |
|---|---|
| `## What is implemented → Tool layer` | Append: *"Browser-UI end-to-end path validated 2026-06-16 after the Issue T re-opening — see [`../../09_logs/2026-06-15_issueT_remediation_applied.md`](../../09_logs/2026-06-15_issueT_remediation_applied.md). Until that date, the Phase A.3 end-to-end claim was true only for API requests that manually attached `tool_ids:["time_now"]`; the browser path was broken by the qwen2.5 Model entry's `base_model_id` value (now `NULL`)."* |
| `### Environment / configuration` table | Add a new row: <code>qwen2.5:7b-instruct `base_model_id`</code> / `NULL` (was `qwen2.5:7b-instruct` until 2026-06-16) / `model.base_model_id` in `webui.db`. Required for OWUI 0.8.10 to expose `info.meta.toolIds` via `/api/models` — see [`../../09_logs/2026-06-15_issueT_browser_validation_reopened.md`](../../09_logs/2026-06-15_issueT_browser_validation_reopened.md) §2.4 |
| `## What is validated` table | Add a row: *"Browser UI fires `time_now` end-to-end"* / Method: *"Manual: open `http://localhost:3000`, ask `¿qué hora es?`, check audit log +1"* / Result: *"PASS"* / Date: `2026-06-16`. |
| `## What is pending → Phase A (closed 2026-06-15)` | Edit the *"Issue T (B-09) — RESOLVED"* paragraph: replace "Resolved" with "Reopened 2026-06-16 due to live browser failure; re-resolved same day after the `base_model_id` fix landed. Root cause: qwen2.5 Model entry created with `base_model_id` equal to its own id, which OWUI 0.8.10 silently drops from the merged model list (see [`…browser_validation_reopened.md`](../../09_logs/2026-06-15_issueT_browser_validation_reopened.md) §2.4). Fix: one-row SQL UPDATE." Keep the link to the new applied log. |
| `## Latest completed milestone` | Replace *"Phase A — CLOSED 2026-06-15"* with *"Phase A — CLOSED 2026-06-15; Issue T re-opening REMEDIATED 2026-06-16."* |

### 8.3 Update `04_ai_system/amarolab-v1/ROADMAP.md`

| Section | Edit |
|---|---|
| Top header date | Bump *"Last updated: 2026-06-15 (Phase A formally closed; …; B-09 resolved; BX added)"* to *"Last updated: 2026-06-16 (Phase A formally closed; B-09 re-opened 2026-06-16 due to browser-path failure, then remediated same day; BX still open)."* |
| Phase A closure paragraph in `## Completed phases → Phase A — formally CLOSED` | Add a sentence: *"On 2026-06-16, a live browser test reproduced the V-10 / V-12 failure, B-09 was re-opened, the root cause was traced to the qwen2.5 Model entry's `base_model_id` value, and a one-row SQL UPDATE remediation was applied — see [`../../09_logs/2026-06-15_issueT_browser_validation_reopened.md`](../../09_logs/2026-06-15_issueT_browser_validation_reopened.md) and [`../../09_logs/2026-06-15_issueT_remediation_applied.md`](../../09_logs/2026-06-15_issueT_remediation_applied.md)."* Do not move Phase A out of "Completed". |
| `## Blockers → Resolved blockers` table, row for B-09 | Rewrite the *"Resolution"* cell: *"On 2026-06-15 initially diagnosed as a validator-shape artefact; **re-opened 2026-06-16** when live browser UI test reproduced the failure. True root cause: qwen2.5 Model entry's `base_model_id = id` causes OWUI 0.8.10 to silently drop the custom entry in `get_all_models`, so `/api/models` lacks `info.meta.toolIds` and the browser cannot auto-attach `tool_ids`. Remediated 2026-06-16 with a one-row SQL UPDATE setting `base_model_id = NULL`. Evidence: [`…browser_validation_reopened.md`](../../09_logs/2026-06-15_issueT_browser_validation_reopened.md), [`…remediation_applied.md`](../../09_logs/2026-06-15_issueT_remediation_applied.md)."* |
| `## Decisions taken (locked)` | Add **D-35**: *"v1 custom Model entries that override an existing base model id MUST set `base_model_id = NULL` (not `= id`). OWUI 0.8.10's `get_all_models` (`utils/models.py:159–175`) silently drops same-id custom rows whose `base_model_id` is non-NULL. Applies to: `qwen2.5:7b-instruct` row (fixed 2026-06-16); any future Model entry created via API/UI/script in this sub-project."* |
| `## Decisions taken (locked)` | Note that the duplicated D-23..D-26 entries at the bottom of the existing ROADMAP table are pre-existing and unrelated to this fix; leave them as-is (deduplication is a separate cleanup task). |

### 8.4 Update `04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md`

| Section | Edit |
|---|---|
| `Last updated:` | Bump to `2026-06-16`. |
| `## Current phase` bullet list of Phase A subdivisions | Replace the *"**Issue T (B-09)** — **RESOLVED**"* bullet with: *"**Issue T (B-09)** — RESOLVED 2026-06-15 → REOPENED 2026-06-16 → RE-RESOLVED 2026-06-16. Real root cause: qwen2.5 Model entry created with `base_model_id = id`, which OWUI 0.8.10's `get_all_models` silently drops from `/api/models`. Browser auto-attach therefore had no `info.meta.toolIds` to read. Fix: one-row SQL UPDATE setting `base_model_id = NULL`. Evidence: [`../../09_logs/2026-06-15_issueT_browser_validation_reopened.md`](../../09_logs/2026-06-15_issueT_browser_validation_reopened.md), [`../../09_logs/2026-06-15_issueT_remediation_applied.md`](../../09_logs/2026-06-15_issueT_remediation_applied.md)."* |
| `## Mandatory reading order` | Insert two new entries after the existing item 11 (Phase A closure & current state) and renumber: *"12. [`…browser_validation_reopened.md`](2026-06-15_issueT_browser_validation_reopened.md) — the corrected B-09 root cause."* and *"13. [`…remediation_applied.md`](2026-06-15_issueT_remediation_applied.md) — the apply that lands the fix."* |

### 8.5 Optional — add a Tools-API amendment note to FUNCTIONS_COMPATIBILITY_REPORT.md

Out of scope for this remediation, but worth flagging in the
apply log as a follow-up: add a single line to the compatibility
report's Model-entry section saying *"To override a same-id base
model, set `base_model_id = NULL`."* — see §5.5-equivalent of the
reopened log §8. Track separately.

## 9. Rollback plan

If §6 fails for any reason and we need to revert:

```bash
docker stop openwebui

sudo cp -a \
  /tmp/amarolab-issueT-reopen-backup/webui.db.pre-base_model_id-fix \
  /srv/homelab/data/openwebui/webui.db
sudo chown 1000:1000 /srv/homelab/data/openwebui/webui.db   # owner pre-fix

docker start openwebui

# verify revert
sqlite3 /srv/homelab/data/openwebui/webui.db \
  "SELECT base_model_id FROM model WHERE id='qwen2.5:7b-instruct';"
# expected: qwen2.5:7b-instruct (pre-fix value)

wc -l /srv/homelab/data/openwebui/amarolab-audit.log
# expected: original 96 + any lines added during the failed Test
```

**Rollback recovery time:** under 10 seconds.

If the rollback itself fails (e.g., backup file corrupt — should
not happen if §3 verified hashes), the next fallback is to
restore from the most recent Restic snapshot (per the R-12
homelab backup config). That is a homelab-level rollback path,
not Amarolab-specific.

## 10. Out-of-scope for this remediation (deferred)

These are real items but explicitly NOT part of this fix. Each
needs its own task / log when the user is ready.

| # | Item | Why deferred |
|---|---|---|
| 10.1 | Three undocumented Tools (`docker_containers`, `system_status`, `docker_logs`) installed in `webui.db`, scoped to `llama3:latest` — see [`…browser_validation_reopened.md`](2026-06-15_issueT_browser_validation_reopened.md) §2.3 / §5.5 | Independent of the Issue T fix; no overlap with the qwen2.5 path; needs a separate audit + decision (keep / retire / reconcile with Phase D) |
| 10.2 | `system_status` name collision with the planned Phase D Tool (D-18) | Resolution depends on what 10.1 decides |
| 10.3 | v0.2 prompt iteration (Issue L, Issue B, `[1]` self-contradiction) | Cosmetic carry-over from Phase A closeout §3.1; independent of B-09 |
| 10.4 | BX — Open WebUI browser-UI WebSocket race — `Unexpected token 'd', "data: ..."` | Upstream OWUI frontend bug; workaround documented; the remediation here does not touch it |
| 10.5 | The duplicated D-23..D-26 entries currently visible in the ROADMAP `## Decisions taken (locked)` table | Pre-existing duplication, unrelated to this fix |
| 10.6 | `Models.get_model_by_id` returning the entry with the v0.1 prompt **even when the row is dropped from `/api/models`** — should the API surface this inconsistency more clearly? | Open WebUI 0.8.10 design quirk; out of v1 scope |
| 10.7 | Phase B kick-off (`PHASE_B_EXECUTION_PLAN.md`) | Explicitly blocked by this remediation; will become unblocked once §6 passes and §8 docs land |

## 11. Success criteria — the apply is "done" when all of these hold

1. §3 backup exists and its sha256 matches the pre-apply
   `webui.db`.
2. §4 SQL `SELECT changes()` returned `1`.
3. §5 cache verification shows `has info: True` and
   `toolIds: ['time_now']` for the qwen2.5 model.
4. §6 Test 1 reply contains a real time and does not contain
   `time_now(` or strftime format strings.
5. §6.4 Test 3 devtools panel shows `"tool_ids": ["time_now"]`
   in the request body.
6. §7 audit log delta is `1` per Test, with
   `tool: "time_now"`, `result_code: "ok"`.
7. §8.1 apply log exists at
   `09_logs/2026-06-15_issueT_remediation_applied.md` and is
   linked from §8.2, §8.3, §8.4.
8. The three live state files reflect §8.2, §8.3, §8.4 edits.
9. `webui.db` size is the same or +0/+1 page; only the
   `base_model_id` and `updated_at` of the qwen2.5 row have
   changed (`sqlite3` diff against the §3 backup confirms).

If any of 1–9 is false, the apply is **not yet complete** —
diagnose and either continue or roll back.

## 12. Estimated impact of NOT applying this fix

- The user-facing browser chat against `qwen2.5:7b-instruct`
  remains broken: model writes the function signature instead of
  invoking the Tool, no audit-log entry, no live time.
- Phase B's `rag_search` and `audit_search` Tools will fail the
  same way the moment they are installed and scoped to qwen2.5 —
  the broken `meta.toolIds` exposure is generic, not Tool-specific.
- The current `CURRENT_STATE.md` and `ROADMAP.md` claim B-09 is
  resolved; this remains incorrect until §8 edits land.
- `time_now` will continue to work via API requests that manually
  set `tool_ids`, masking the real failure surface (this is what
  enabled Phase A.3's misleading "end-to-end" claim).

Phase B should **not start** until §11.4–§11.8 pass.

## 13. Cross-references

- Root-cause investigation (the diagnosis this plan remediates):
  [`2026-06-15_issueT_browser_validation_reopened.md`](2026-06-15_issueT_browser_validation_reopened.md)
- Prior, partially-incorrect Issue T analysis (preserved for
  traceability):
  [`2026-06-15_issueT_root_cause_analysis.md`](2026-06-15_issueT_root_cause_analysis.md)
- Phase A closeout (which prematurely declared B-09 resolved):
  [`2026-06-15_phaseA_closeout.md`](2026-06-15_phaseA_closeout.md)
  — §2.1 needs revision per §8 edits.
- Browser-UI WebSocket race workaround (relied on by §6):
  [`2026-06-15_openwebui_json_parse_error_analysis.md`](2026-06-15_openwebui_json_parse_error_analysis.md)
  §7.1.
- Open WebUI 0.8.10 runtime contract (unchanged by this fix):
  [`../FUNCTIONS_COMPATIBILITY_REPORT.md`](../FUNCTIONS_COMPATIBILITY_REPORT.md)
- Audit log (the `+1` target):
  `/srv/homelab/data/openwebui/amarolab-audit.log`
- The single source file being changed:
  `/srv/homelab/data/openwebui/webui.db` — `model` table, row
  `id = 'qwen2.5:7b-instruct'`, column `base_model_id`.
- Sub-project ROADMAP (recipient of §8.3 edits):
  [`../04_ai_system/amarolab-v1/ROADMAP.md`](../04_ai_system/amarolab-v1/ROADMAP.md)
- Sub-project CURRENT_STATE (recipient of §8.2 edits):
  [`../04_ai_system/amarolab-v1/CURRENT_STATE.md`](../04_ai_system/amarolab-v1/CURRENT_STATE.md)
- Sub-project HANDOFF (recipient of §8.4 edits):
  [`../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md`](../04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md)

## 14. Stop point

Per the user's instruction ("Do not apply changes yet. Stop after
producing the plan."): this document is the artifact for this
turn. No DB writes, no service restarts, no documentation edits.
The plan is **proposed**, awaiting an explicit "apply" instruction
in a subsequent turn before any step in §3–§8 is executed.
