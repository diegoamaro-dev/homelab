# Phase F — F2-0 Pre-conditions and AF-07 Validation

- **Date:** 2026-06-28
- **Phase step:** F-2 — Signal Layer and Context Generation
- **Sub-step:** F2-0 — Pre-conditions validation (read-only)
- **Status:** COMPLETE

---

## 1. AF-07 — Torre probe from inside openwebui container

**Finding:** CONFIRMED PASS

```
HTTP 200 in 3ms  →  http://100.91.154.124:11434/api/tags
```

Torre's Tailscale IP (`100.91.154.124:11434`) is directly reachable from inside
the `openwebui` container. The Docker network (`ai-local_default`) has access to
the host's Tailscale interface; no special routing or host-side workaround is
required.

**Architecture implication:** The `system_status` tool (F2-5) will perform the
Torre probe live from inside the container, not via a host-side signal file. AF-07
is **closed**.

---

## 2. Signal file paths inside the container

| Path inside container | Status | Notes |
|---|---|---|
| `/opt/ingest/logs/health.json` | **exists, readable** | schema_version 1; overall_status ok; updated_at 2026-06-28T01:30:01Z |
| `/opt/aurora/aurora-context.json` | **does not exist** | bind-mount not yet added (F2-6) |

`/opt/ingest` is bind-mounted read-only from `/home/diego/homelab/ai-stack/ingest`.
`/opt/aurora` will require a new bind-mount from `/home/diego/homelab/ai-stack/aurora`
added in F2-6.

---

## 3. Container inventory

**17 containers confirmed running:**

| Container | Status |
|---|---|
| openwebui | Up (healthy) |
| qdrant | Up (healthy) |
| ollama-proxy | Up (healthy) |
| ollama | Up |
| homeassistant | Up |
| nginx-proxy-manager | Up |
| portainer | Up |
| guardian-web | Up |
| zigbee2mqtt | Up |
| mosquitto | Up |
| cloudflared | Up |
| cloudflared-amarolab | Up |
| aurora-piper | Up |
| aurora-piper-http | Up |
| aurora-whisper | Up |
| aurora-whisper-http | Up |
| aurora-wakeword | Up |

This count is the baseline for `container_status.json` validation in F2-3 and F2-9.

---

## 4. openwebui stack management — Portainer-managed

**Finding:** The `ai-local` compose stack (which contains openwebui) is managed by
Portainer, not by a local file in the homelab repository. The compose definition
lives inside the Portainer data volume (`portainer_data`), not at a path accessible
by editing local files.

Current openwebui bind-mounts:
```
/srv/homelab/data/openwebui           →  /app/backend/data   (rw)
/home/diego/homelab/ai-stack/ingest   →  /opt/ingest          (ro)
```

**Architecture implication:** F2-6 (adding the `/opt/aurora` bind-mount) must be
applied through the **Portainer web UI** by editing the `ai-local` stack definition
and redeploying. It cannot be done by editing a local `docker-compose.yml` in the
repository. The bind-mount line to add:
```yaml
- /home/diego/homelab/ai-stack/aurora:/opt/aurora:ro
```

---

## 5. homelab-backup.sh

**homelab-backup.sh remains untouched.** The script at `/usr/local/bin/homelab-backup.sh`
(root-owned) is not readable without sudo and will not be modified as part of Phase F.

Backup signal generation will come from a separate `backup-probe` script (F2-2) that
reads the restic repository via `restic snapshots --latest 1 --json` using the existing
passphrase at `/etc/restic/passwd-homelab`. This runs as root via `/etc/cron.d/aurora-signals`
at 03:30 (after the 03:00 backup window), independent of the backup script itself.

**Freshness validation:** `backup-probe` will compare the latest snapshot timestamp
against the expected nightly window (03:00 ± configurable tolerance) rather than
assuming the backup ran. If no snapshot was created tonight, `status` is
`"no_snapshot_tonight"` rather than guessing success.

**Backup log:** `/var/log/homelab-backup.log` is readable by diego (group `adm`,
mode `0640`). The log contains raw restic output. Log parsing is not used by
`backup-probe` — restic's JSON snapshot API is the authoritative source.

**Pre-existing note:** The backup log from 2026-06-28 03:00 contains a stale-lock
error from the E5-b restore drill (2026-06-27). This is not caused by F-2 and does
not affect backup integrity — the snapshot `d6c12657` was saved successfully.

---

## 6. 09_ops/ directory

`/home/diego/homelab/09_ops/` **did not exist** at the start of F2-0. It was created
as part of F2-1a alongside `09_ops/runtime/`. The `runtime/` subdirectory is gitignored
(operational digest files are runtime artifacts per AD-07). The parent `09_ops/`
directory is tracked and will be committed when it has content.

---

## 7. F2-1a completion record

Completed immediately after F2-0 validation.

**`.gitignore` additions (end of `/home/diego/homelab/.gitignore`):**
```
# Aurora runtime artifacts (F-2) — generated nightly, never committed
ai-stack/aurora/
09_ops/runtime/
```

**Directories created:**
- `/home/diego/homelab/ai-stack/aurora/` — context artifact home; gitignored
- `/home/diego/homelab/09_ops/runtime/` — operational digest home (F-4); gitignored

**Verified:** Both paths confirmed gitignored via `git check-ignore -v`. Only `.gitignore`
appears as a changed file in `git status`. No other working tree changes.

---

## 8. Open items entering F2-2

| Item | Status |
|---|---|
| `backup-probe` script | **Not yet implemented** — next step |
| `/etc/cron.d/aurora-signals` | **Not yet created** |
| `container-probe` script | Pending F2-3 |
| `aurora-context` script | Pending F2-4 |
| `system_status` tool | Pending F2-5 |
| `/opt/aurora` bind-mount | Pending F2-6 (via Portainer UI) |
| `signals_contract.md` | Pending F2-1b (before F2-2 implementation) |

---

*F2-0 and F2-1a complete. Awaiting approval to proceed to F2-1b (signals_contract.md).*
