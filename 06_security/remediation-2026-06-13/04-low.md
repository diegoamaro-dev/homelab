# 04 — Low priority fixes (when convenient)

Six items: cleanup, hygiene, and one investigation. Skipping any of them
won't materially affect availability or security; doing them tidies up
the host.

---

## R-15 — Remove the orphaned Chroma store from Open WebUI

**Risk — · Impact — · Time 1 m · Priority 🟢 Low**

### Current state

`/srv/homelab/data/openwebui/vector_db/chroma.sqlite3` (188 kB) is left
over from before `VECTOR_DB=qdrant`. Open WebUI doesn't read it any more;
it just adds confusion to backups and to any future debugger.

### Procedure (safe variant: rename first, delete later)

```bash
mv /srv/homelab/data/openwebui/vector_db \
   /srv/homelab/data/openwebui/vector_db.orphan-2026-06-13

# Confirm Open WebUI still starts cleanly
docker restart openwebui
docker logs --tail 30 openwebui

# After ~1 week with no regressions
rm -rf /srv/homelab/data/openwebui/vector_db.orphan-2026-06-13
```

### Validation

```bash
docker exec openwebui ls /app/backend/data | grep -c vector_db
# Expect: 1 (the renamed dir is still mounted) → then 0 after deletion
```

### Rollback

```bash
mv /srv/homelab/data/openwebui/vector_db.orphan-2026-06-13 \
   /srv/homelab/data/openwebui/vector_db
```

---

## R-16 — Delete the two dead Docker bridges

**Risk — · Impact — · Time 1 m · Priority 🟢 Low**

### Current state

```
br-19cdd483fddc  html_default        172.21.0.1/16  DOWN   (no containers)
br-5fb2ead55087  cloudflared_default 172.23.0.1/16  DOWN   (no containers)
```

### Procedure

```bash
docker network ls --format '{{.Name}}' | grep -E '^(html_default|cloudflared_default)$'
docker network rm html_default cloudflared_default
```

### Validation

```bash
docker network ls | grep -cE 'html_default|cloudflared_default'
# Expect: 0

ip -br a | grep -E 'br-19cdd483fddc|br-5fb2ead55087'
# Expect: no output
```

### Rollback

These bridges aren't referenced by any container, so they can simply be
recreated if a stack later needs them: `docker network create html_default`.

---

## R-17 — `diego` in the `docker` group (informational)

**Risk L · Impact (policy) · Time n/a · Priority 🟢 Low (informational)**

### Current state

```
groups diego
diego : diego adm cdrom sudo dip plugdev users lpadmin docker shared
```

`docker` group → effective root via `docker run -v /:/host …`. This is
intentional and standard for a single-admin homelab.

### Recommendation

No change today. Treat this as documentation:

- **Do not** add additional human users to the `docker` group.
- If a second person ever needs container management, gate it through
  Portainer (already running on `:9443`) with its own user accounts
  instead of a host shell.

### Validation

```bash
getent group docker
# Expect: docker:x:NNN:diego   (only diego)
```

---

## R-18 — Disable desktop services on a headless server

**Risk L · Impact L · Time 15 m + reboot · Priority 🟢 Low**

### Current state

`gdm`, `gnome-remote-desktop`, `cups`, `cups-browsed`, `bluetooth`,
`ModemManager`, `colord`, `power-profiles-daemon` are running on a machine
that you reach by SSH and Tailscale. Each is one more attack surface and
one more thing the boot sequence has to bring up cleanly.

### Caveat before you start

- **GDM disable means no GUI on the console.** If you ever sit at the
  physical machine with a monitor, you'll get a text-mode login only.
- Bluetooth disable affects HA's `bluetooth` integration (you have one
  paired device under that name). Don't disable it if you actually use
  BT-based discovery in HA.
- Modem Manager is irrelevant on this host (no cellular modem).

### Procedure — safe subset (no GUI impact)

```bash
sudo systemctl disable --now cups.service cups-browsed.service
sudo systemctl disable --now ModemManager.service
sudo systemctl disable --now colord.service
```

### Procedure — aggressive (kills GUI)

```bash
# Switch default boot target to console
sudo systemctl set-default multi-user.target

# Stop the display manager NOW (will close any tty7+ X session)
sudo systemctl disable --now gdm.service
sudo systemctl disable --now gnome-remote-desktop.service

# Bluetooth — only if HA's bluetooth integration is unused
docker exec homeassistant cat /config/.storage/core.config_entries | grep -c bluetooth
# If > 0, keep bluetoothd. Otherwise:
sudo systemctl disable --now bluetooth.service
```

### Validation

```bash
systemctl is-active gdm cups cups-browsed bluetooth ModemManager colord
# Each line: 'inactive' for the ones you disabled
```

### Rollback

```bash
sudo systemctl set-default graphical.target
sudo systemctl enable --now gdm gnome-remote-desktop
sudo systemctl enable --now cups cups-browsed bluetooth ModemManager colord
```

---

## R-19 — Qdrant `/metrics` and `/telemetry` reachable without auth

**Risk L · Impact L · Time covered by R-07 · Priority 🟢 Low**

### Current state

`http://homelab:6333/metrics` and `/telemetry` return collection counts
and timing info. With R-07 applied (`127.0.0.1` bind + API key), neither
endpoint is reachable from the LAN/tailnet any more, and `/telemetry` will
return 401 without the API key on the loopback path.

### Procedure

None. R-07 already closes this surface.

### Validation

```bash
# After R-07
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:6333/metrics
# Expect: 401 (with api-key) → 200
curl --connect-timeout 3 -s -o /dev/null -w '%{http_code}\n' http://192.168.178.79:6333/metrics
# Expect: 000 (connection refused / timeout)
```

---

## R-20 — Investigate the 2026-06-03 12:55 hard reset

**Risk (investigative) · Impact — · Time 30 m · Priority 🟢 Low**

### Current state

`last` and `home-assistant.log.fault` agree on a 2026-06-03 12:55 hard
reset. The current journal window (boot since 2026-06-08) no longer
contains the prior boot, but `journalctl --list-boots` will if persistent
storage was on.

### Procedure

```bash
# 1. List prior boots
sudo journalctl --list-boots
# Note the boot index (e.g. -1) for 2026-06-03

# 2. Tail errors from that boot
sudo journalctl -b -1 -p err --no-pager | tail -200
sudo journalctl -b -1 -p warning --no-pager | tail -200

# 3. Hunt for hard-failure keywords
sudo journalctl -b -1 --no-pager \
  | grep -iE 'oops|panic|segfault|killed process|out of memory|hardware error|MCE|thermal' \
  | tail -100

# 4. Recent dmesg ring (might still hold MCE / thermal logs)
sudo dmesg -T | grep -iE 'oops|panic|throttle|temperature|MCE|nvme|ata' | tail -100

# 5. Disk health
sudo smartctl -a /dev/nvme0n1 | head -60
sudo smartctl -a /dev/sda     | head -60

# 6. Memory
sudo dmidecode -t memory | head -30
# Optionally schedule a memtest86+ run on the next maintenance window.
```

### Likely lines worth looking for

| Pattern | Interpretation |
|---------|----------------|
| `Hardware Error` / `MCE` | CPU or RAM fault |
| `nvme nvme0: Disabling device` / `I/O error` | NVMe failure |
| `thermal throttle` / `Critical temperature` | Cooling / dust |
| `Out of memory: Killed process` | systemd-oomd kicked in (load avg 12.4 today suggests bursts are possible) |
| `watchdog: BUG: soft lockup` | Kernel scheduler stall |
| `ext4-fs error` | Filesystem corruption |

### Output capture

```bash
# Bundle findings into the audit folder for future reference
( sudo journalctl -b -1 -p err --no-pager
  echo "---"
  sudo dmesg -T | grep -iE 'oops|panic|throttle|MCE|nvme|ata'
  echo "---"
  sudo smartctl -a /dev/nvme0n1
  echo "---"
  sudo smartctl -a /dev/sda
) > /home/diego/server-audit-2026-06-13/crash-2026-06-03.txt 2>&1
```

### Rollback

N/A — read-only investigation.

---

## Closing notes

- The fix files in this folder describe **what** to do, not what was done.
  Once you run a procedure, record the run date inline (e.g. flip the
  heading to `R-NN — … (applied 2026-06-DD)`).
- Add a `phase2-remediation/CHANGELOG.md` if you start spreading the fixes
  across several sessions; that becomes the canonical "what state is the
  host in right now" doc.
- Re-run the original Phase 1 audit on a cadence — quarterly is realistic
  for a homelab. Many of the findings here (image age, mosquitto config,
  unused bridges) reappear naturally over time.
