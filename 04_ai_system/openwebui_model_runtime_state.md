# Open WebUI — Aurora Model Runtime State (`webui.db`)

- **Last updated:** 2026-06-29 (created in F2-9 as an operator safeguard:
  "no undocumented runtime state").
- **Scope:** the parts of Aurora's configuration that live in the Open WebUI
  runtime database `webui.db` and are **not** in git — what they are, how they
  are set, how they survive/recover, and whether they should be automated.

---

## 1. What is runtime state (not in git)

Open WebUI 0.8.10 stores model and tool configuration in
`/srv/homelab/data/openwebui/webui.db` (SQLite). The repository holds the
**sources**, the database holds the **live, applied configuration**:

| Item | Lives in | In git? |
|---|---|---|
| Tool **source** (`rag_search`, `ha_*`, `time_now`, `audit_search`) | `ai-stack/openwebui-tools/tools/*.py` | ✅ yes |
| `system_status` tool **source** (v0.2.0) | `ai-stack/ingest/docs/system_status_tool.py` | ✅ yes |
| Registered tool **rows** (`tool` table `content`) | `webui.db` | ❌ runtime |
| `qwen2.5:7b-instruct` **model row** — `base_model_id` (NULL, D-35), `meta.toolIds`, `params.system` | `webui.db` | ❌ runtime |
| F-1 **system prompt text** (~3,389 chars) | `webui.db` `params.system` (+ quoted in the F-1 apply log) | ❌ runtime |

**Canonical applied values (2026-06-29):**
- `qwen2.5:7b-instruct` → `base_model_id = NULL`;
  `meta.toolIds = ["time_now","rag_search","audit_search","ha_get_state","ha_call_service","system_status"]`;
  `params.system` = the F-1 prompt (domain-based routing, 6 tools).
- `system_status` is also attached to the legacy `llama3*` rows (pre-existing);
  `docker_containers`/`docker_logs` remain `llama3*`-only (D-20).

**Persistence:** `/srv/homelab/data/openwebui` is bind-mounted into the
`openwebui` container at `/app/backend/data`. `webui.db` therefore **survives
container restart and recreation** (e.g. the F2-6 `docker run` recreation and
the F2-9 restart both preserved it). It is lost only if that host directory /
database is deleted or a genuinely fresh deployment starts from an empty DB.

---

## 2. How the `system_status` attachment was performed (F2-9, exact)

The attachment is a **direct `sqlite3` UPDATE** of the model row (Python
`sqlite3` module), the same mechanism used to install the F-1 prompt
([`../09_logs/2026-06-28_phaseF_F1_system_prompt_installed.md`](../09_logs/2026-06-28_phaseF_F1_system_prompt_installed.md)).
It is **not** the admin-UI path documented in
[`../ai-stack/openwebui-tools/README.md`](../ai-stack/openwebui-tools/README.md)
("Per-model visibility"); a scripted UPDATE was used for precision, an exact
readback, and a reproducible record.

Steps performed:
1. Back up the current `qwen2.5:7b-instruct` row (`id, meta, params`) to a file.
2. `meta = json.loads(meta)`; append `"system_status"` to `meta["toolIds"]`
   (dedup, order preserved).
3. `params = json.loads(params)`; edit `params["system"]` (add `system_status`
   to the Tools list, add a LIVE-STATE routing line, add a Context note).
4. Parameterised write — `UPDATE model SET meta=?, params=? WHERE id=?` — then
   **readback-verify** (`system_status` present in `toolIds`; markers present in
   the prompt). `base_model_id` column is never written (D-35 preserved).
5. `docker restart openwebui` to reload the model config.

Minimal reproducible form (no shell quoting; run on the host):
```python
import sqlite3, json
db = "/srv/homelab/data/openwebui/webui.db"
con = sqlite3.connect(db); cur = con.cursor()
meta_s, params_s = cur.execute(
    "select meta, params from model where id=?", ("qwen2.5:7b-instruct",)).fetchone()
meta, params = json.loads(meta_s), json.loads(params_s)
if "system_status" not in meta["toolIds"]:
    meta["toolIds"].append("system_status")
# params["system"] = <F-1 prompt text incl. the system_status tool/routing lines>
cur.execute("update model set meta=?, params=? where id=?",
            (json.dumps(meta, ensure_ascii=False),
             json.dumps(params, ensure_ascii=False), "qwen2.5:7b-instruct"))
con.commit()
# then: docker restart openwebui
```
Validation that this was effective is in the F2-9 closeout
([`../09_logs/2026-06-29_phaseF_F2_9_closeout.md`](../09_logs/2026-06-29_phaseF_F2_9_closeout.md) §3):
DB readback, 4/4 model routing, live tool execution, and the real-browser
G-F1-01 pass.

---

## 3. Reproducibility after a fresh Open WebUI deployment

| Scenario | Recoverable? | How |
|---|---|---|
| Container restart / recreation | ✅ automatic | bind-mount preserves `webui.db` |
| `webui.db` lost → **restore from backup** | ✅ complete | restic recovers the full model config (toolIds + prompt + tool rows) intact — see below |
| Clean rebuild from an **empty** `webui.db` (no restore) | ⚠️ partial | tools reproducible from git; **model config (toolIds + prompt) is manual** |

**Backup / restore (primary DR path).** `webui.db` is in the nightly restic
backup two ways (`/usr/local/bin/homelab-backup.sh`): a WAL-consistent
`sqlite3 .backup` copy (`$SNAP_DIR/openwebui-webui.db`) **and** the live
`/srv/homelab/data/openwebui` directory. Restoring the latest snapshot recovers
the entire applied configuration — including this `system_status` attachment —
with no re-application needed. (Caveat: restic retention/`prune` is currently
blocked by a stale repo lock — tracked separately; backups still write.)

**Clean rebuild (no restore).**
- **Tool registrations** are reproducible from git:
  `cd ai-stack/openwebui-tools && ./bin/install_tool tools/<id>.py` for each tool;
  install `system_status` from `ai-stack/ingest/docs/system_status_tool.py`.
- **Model config is NOT reproducible from git by any committed script today.**
  After installing the tools you must re-apply, manually:
  - `meta.toolIds` for `qwen2.5:7b-instruct` (canonical list in §1) — via the
    admin UI (README "Per-model visibility") or the `sqlite3` snippet in §2;
  - `params.system` — the F-1 prompt, whose text exists only in `webui.db` and
    quoted in the F-1 apply log.

So: **recoverable from backup = yes (complete); reproducible from git without a
backup = partial** (tools yes, model config manual).

---

## 4. Should this be standard procedure or automated?

**Standard procedure (now).** This document *is* the procedure. Order of
preference on loss of `webui.db`:
1. **Restore `webui.db` from the latest restic snapshot** (complete, fastest).
2. If rebuilding clean: `install_tool` every tool, then re-apply the model
   config (toolIds + prompt) per §2/§3.

**Recommended automation (future — not required for F-2 closure).** The manual
model-config step is the one piece of Aurora's configuration not reproducible
from git. Close that gap by making the model config *code*:
- Commit the F-1 system prompt as a source file (e.g.
  `ai-stack/openwebui-tools/prompts/qwen2.5_system.md`) — today it lives only in
  `webui.db` + the apply log.
- Add an idempotent `configure-model` script (same `sqlite3` method + readback)
  that sets `qwen2.5` `meta.toolIds` (canonical list) and `params.system` (from
  the committed prompt file) in one command.

Result: the entire Aurora model config becomes reproducible from git
(`install_tool` ×N + `configure-model`), version-controlled, and diffable.
Suggested home: a near-term maintenance item, or folded into **F-3** (which
already touches the Open WebUI Function layer). Tracked as a follow-up; it does
not block F-2.

---

## 5. References

- F2-9 closeout: [`../09_logs/2026-06-29_phaseF_F2_9_closeout.md`](../09_logs/2026-06-29_phaseF_F2_9_closeout.md)
- F-1 prompt install (full prompt text): [`../09_logs/2026-06-28_phaseF_F1_system_prompt_installed.md`](../09_logs/2026-06-28_phaseF_F1_system_prompt_installed.md)
- Tool install workflow: [`../ai-stack/openwebui-tools/README.md`](../ai-stack/openwebui-tools/README.md)
- Backup script: `/usr/local/bin/homelab-backup.sh` (R-12)
- Live model/tool inventory: [`../00_overview/CURRENT_STATE.md`](../00_overview/CURRENT_STATE.md) → "Open WebUI"
