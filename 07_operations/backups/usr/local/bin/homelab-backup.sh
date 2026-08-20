#!/usr/bin/env bash
# /usr/local/bin/homelab-backup.sh
# Nightly homelab backup. Idempotent; safe to re-run by hand.
# Installed by Phase 0 R-12 on 2026-06-13.

set -euo pipefail

export RESTIC_REPOSITORY=/mnt/storage/backups/restic
export RESTIC_PASSWORD_FILE=/etc/restic/passwd-homelab

# I-4 (2026-07-28): this path MUST NOT contain a date.
# restic groups snapshots by host+paths (default --group-by host,paths). A
# dated path changed the recorded path set on every run, so each snapshot
# landed in a group of one: the retention policy below became structurally
# inert (no snapshot deleted since 2026-06-13) and no parent snapshot was
# ever found, forcing a full ~4.1 GiB re-scan every night.
SNAP_DIR=/tmp/homelab-backup-snapshots
mkdir -p "$SNAP_DIR"
trap 'rm -rf "$SNAP_DIR"' EXIT

# Consistent SQLite snapshots via .backup (respects WAL).
# Each file may not exist on first run — keep going on individual errors.
if [ -f /srv/homelab/data/openwebui/webui.db ]; then
  sqlite3 /srv/homelab/data/openwebui/webui.db ".backup '$SNAP_DIR/openwebui-webui.db'" || \
    echo "WARN: openwebui sqlite backup failed" >&2
fi
if [ -f /srv/homelab/homeassistant/home-assistant_v2.db ]; then
  sqlite3 /srv/homelab/homeassistant/home-assistant_v2.db ".backup '$SNAP_DIR/homeassistant.db'" || \
    echo "WARN: homeassistant sqlite backup failed" >&2
fi
if [ -f /srv/homelab/data/npm/database.sqlite ]; then
  sqlite3 /srv/homelab/data/npm/database.sqlite ".backup '$SNAP_DIR/npm.sqlite'" || \
    echo "WARN: npm sqlite backup failed" >&2
fi

# Workload roots
PATHS=(
  /srv/homelab/data/openwebui
  /srv/homelab/homeassistant
  /srv/homelab/data/npm
  /home/diego/homelab/ai-stack/data/qdrant
  /home/diego/homelab/03_services/zigbee-stack/zigbee2mqtt/data
  /home/diego/homelab/03_services/zigbee-stack/mosquitto/data
  /home/diego/homelab/03_services/zigbee-stack/mosquitto/config
  /home/diego/webs
  /home/diego/homelab/09_ops/runtime 
  /etc/systemd/system/homelab-tools.service
  /etc/apache2/sites-enabled
  /etc/samba/smb.conf
  # I-5 (2026-08-18): H-2 coverage. Static paths only -- no date, timestamp
  # or variable component may enter this array (the I-4 defect class).
  # Secrets are deliberately excluded and deferred to M-D.
  /var/lib/docker/volumes/portainer_data/_data
  /etc/cron.d/aurora-signals
  /srv/homelab/data/openedai-speech/voice_to_speaker.yaml
  "$SNAP_DIR"
)

restic backup \
  --tag nightly \
  --exclude '/srv/homelab/data/openwebui/cache/**' \
  --exclude '**/node_modules/**' \
  --exclude '**/.git/objects/**' \
  "${PATHS[@]}"

# I-4 (2026-07-28): --dry-run is DELIBERATE, not a leftover.
# With grouping fixed the policy is live again and would begin deleting
# snapshots unattended once this group spans more than 7 days -- before the
# retention policy has been decided (remediation item S-10) and before the
# D-1.5 anchor 63c072f4 has any protection (I-6).
# Re-enabling deletion is S-10: attended, operator-approved per execution.
# Do not remove --dry-run or restore --prune without it.
restic forget \
  --tag nightly \
  --keep-daily 7 \
  --keep-weekly 4 \
  --keep-monthly 6 \
  --dry-run
