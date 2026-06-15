# 12 — Backups

> **Status:** Resolved 2026-06-13 by Phase 2 / R-12.
> First snapshot ID: `cc73b4fd`.
> See [Phase 0 application log](#phase-0-application-2026-06-13) at the end of this file.

## Current state (pre-fix snapshot — kept for history): **no backups existed**

### Evidence

- `/srv/homelab/backups` — empty directory (created 2026-03-11, untouched
  since).
- `/mnt/storage/backups` — empty (created 2026-04-06, untouched since).
- `/var/backups` — contains only system-rotated files (apt history, shadow
  copies). Not a homelab backup target.
- `crontab -l` for `diego` — no jobs.
- `/etc/cron.{d,daily,hourly,weekly,monthly}` — only stock OS items
  (`apache2`, `apt-compat`, `dpkg`, `logrotate`, `man-db`, `sysstat`,
  `apport`, `anacron`).
- `/srv/homelab/scripts/` — empty (was intended for shell scripts, none
  written yet).
- `find / -name 'backup*'` — only the empty target directories above and
  AI assistant's `<AI_ASSISTANT_HOME>/backups` (irrelevant).
- No `restic`, `borg`, `rsnapshot`, `duplicity`, `rclone`, `kopia` binary
  installed.
- No `docker exec … pg_dump` or `sqlite3 .backup` style snapshot scripts
  anywhere on disk.

### What *would* be lost on a disk failure

| Component | Disk | Recovery effort |
|-----------|------|-----------------|
| Open WebUI users, chats, settings (`webui.db`) | NVMe | Re-create accounts and chat history; settings rebuild |
| Open WebUI uploads / RAG documents | NVMe | Re-upload from source if available |
| Qdrant collections (`open-webui_files`, `open-webui_knowledge`) | NVMe | Re-index after re-uploading the source docs |
| Ollama models | NVMe | Re-pull (~8 GB over internet; reproducible) |
| Home Assistant config + automations + recorder history | NVMe | Manual reconstruction (config is small but historical state is gone) |
| Zigbee2MQTT coordinator + paired-device DB | NVMe | Re-pair every Zigbee device (painful) |
| NPM database (proxy hosts, TLS certs) | NVMe | Re-issue Let's Encrypt certs + reconfigure each proxy host |
| `guardian-cloud` static site + backend | NVMe | Restorable from Git (assumed) |
| `/mnt/storage/projects` (Samba) | HDD | Restorable from clients if Git-tracked |

### Risk

The Home Assistant `home-assistant.log.fault` zero-byte file from
2026-06-03 12:55 and the matching `last` "crash" entry show this machine
already hard-resets. The next event that fails to recover cleanly will lose
state without a backup.

## Recommendation (not implemented — read-only audit)

The pieces are in place to bolt this on quickly:

1. The 1.8 TB HDD at `/mnt/storage` is essentially empty — already a
   dedicated, locally-attached backup target.
2. Containers' state lives in well-defined bind mounts under
   `/srv/homelab/data/`, `/srv/homelab/homeassistant/`, and
   `/home/diego/homelab/`. A nightly `restic` or `rsync --delete --link-dest`
   snapshot of those paths to `/mnt/storage/backups/$(date +%F)` would cover
   90 % of the loss surface for a one-screen shell script.
3. SQLite databases (`webui.db`, `home-assistant_v2.db`, NPM's
   `database.sqlite`) should be copied via `sqlite3 .backup`, not raw `cp`,
   to avoid WAL-corruption.
4. Off-site / cold storage is **not** present and would still be missing
   even after step 1–3. Tailscale to a second device, or `rclone` to an S3
   bucket, would close that gap.

> No changes were made. These notes are for the follow-up work, not the
> audit itself.

---

## Phase 0 application (2026-06-13)

Backups have been **stood up** as the first Phase 0 prerequisite for the
local AI assistant.

### What was installed

| Component | Path | Mode / owner |
|-----------|------|--------------|
| `restic` binary | `/usr/bin/restic` (0.16.4 from Ubuntu) | distro package |
| `sqlite3` binary | `/usr/bin/sqlite3` | distro package |
| Repository passphrase | `/etc/restic/passwd-homelab` | `0600 root:root` |
| Backup script | `/usr/local/bin/homelab-backup.sh` | `0755 root:root` |
| Cron schedule | `/etc/cron.d/homelab-backup` | `0644 root:root` — nightly 03:00 |
| Logrotate policy | `/etc/logrotate.d/homelab-backup` | `0644 root:root` — weekly × 8 |
| Restic repository | `/mnt/storage/backups/restic/` | on the 1.8 TB HDD |
| Run log | `/var/log/homelab-backup.log` | `0640 root:adm` |

### Coverage

The backup script snapshots:

- `/srv/homelab/data/openwebui` (excluding the `cache/` dir — re-downloadable)
- `/srv/homelab/homeassistant`
- `/srv/homelab/data/npm` (including Let's Encrypt)
- `/home/diego/homelab/ai-stack/data/qdrant`
- `/home/diego/homelab/03_services/zigbee-stack/zigbee2mqtt/data`
- `/home/diego/homelab/03_services/zigbee-stack/mosquitto/{data,config}`
- `/home/diego/webs`
- `/etc/systemd/system/homelab-tools.service`
- `/etc/apache2/sites-enabled`
- `/etc/samba/smb.conf`

SQLite databases (`webui.db`, `home-assistant_v2.db`, `database.sqlite`)
are snapshotted via `sqlite3 .backup` into a per-run temp directory
*before* restic walks them, so the captured copies are WAL-consistent.

### First run

- **Snapshot ID:** `cc73b4fd`
- **Triggered manually** with `sudo /usr/local/bin/homelab-backup.sh` on
  2026-06-13.
- **Retention policy:** keep 7 daily / 4 weekly / 6 monthly.

### Validation commands (re-run any time)

```bash
# List snapshots
sudo RESTIC_PASSWORD_FILE=/etc/restic/passwd-homelab \
     restic -r /mnt/storage/backups/restic snapshots

# Spot-restore a file to /tmp/restore-test
sudo RESTIC_PASSWORD_FILE=/etc/restic/passwd-homelab \
     restic -r /mnt/storage/backups/restic restore latest \
     --include /srv/homelab/data/npm/database.sqlite \
     --target /tmp/restore-test

# Disk pressure on the HDD
df -h /mnt/storage
```

### What is still missing

- **Off-site / cold copy.** The repo lives on the same physical host. A
  total-loss event (theft, fire) takes the backup with the source.
  Follow-up: mirror the repo to a tailnet peer or to B2 / S3 via
  `restic copy`, or run a second `restic backup` to a remote URL.
- **Encrypted off-site key escrow.** Once an off-site target exists, the
  `passwd-homelab` file needs a way to survive losing the host (printed
  copy in a fireproof safe, or sealed with a passphrase manager).
- **Restore drill.** A monthly automated restore-to-tempdir-and-diff
  would be the natural next hardening step.

