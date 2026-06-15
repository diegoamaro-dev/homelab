# 02 — Operating system

## Distribution

| Field | Value |
|-------|-------|
| Distro | Ubuntu 24.04.4 LTS (Noble Numbat) |
| Codename | noble |
| Kernel | Linux 6.17.0-35-generic (HWE) |
| Architecture | x86_64 |
| Hostname | `homelab` (static) |
| Time zone | Europe/Madrid (`TZ` inherited via `/etc/localtime`) |
| Locale | `es_ES.UTF-8` (Spanish error messages observed) |

## Boot / uptime

| Field | Value |
|-------|-------|
| Boot ID | `<REDACTED-BOOT-ID>` |
| Boot time | 2026-06-08 10:03 |
| Uptime | 5 days 2 hours (snapshot at 12:12 on 2026-06-13) |
| Load avg | **12.41 / 7.58 / 3.28** (1 m / 5 m / 15 m) |
| Logged-in users | 3 sessions |

> The 1-minute load average is high relative to the 16-thread CPU. The 15 m
> average is healthy, so this looks like a transient burst (consistent with
> running the audit itself).

The prior boot ended in a **crash** on 2026-06-03 12:55 (visible in
`last`; `home-assistant.log.fault` of size 0 from the same date). No oops
fragment is present in the live `dmesg` ring buffer.

## User accounts (interactive)

Filtered `/etc/passwd` to non-service users:

| User | UID | Shell | Notes |
|------|-----|-------|-------|
| root | 0 | /bin/bash | system |
| diego | 1000 | /bin/bash | primary admin, member of `sudo` |
| smbuser | 1001 | /bin/bash | Samba access user |

`diego` groups: `adm, cdrom, sudo, dip, plugdev, users, lpadmin, docker, shared`.
`smbuser` groups: `users, shared`.

> `diego` is in the `docker` group, which grants effective root via container
> escape — standard for a single-admin homelab but worth flagging.

The `/etc/sudoers` file requires root to read. `getent group sudo` shows only
`diego` as a member.

## Login history (host)

`last` shows only console (`tty2` / `seat0`) logins by `diego` since
2026-03-11, plus the system boots. No SSH login records visible in `wtmp`
without root, but `sshd` is running and listening on TCP/22 (see
[13-exposed-ports.md](13-exposed-ports.md)).

`lastb` (failed-login DB) requires root and was not collected.

## Automatic updates

- `apt` periodic config in `/etc/apt/apt.conf.d/20auto-upgrades`:
  - `APT::Periodic::Update-Package-Lists "1"` (daily)
  - `APT::Periodic::Unattended-Upgrade "1"` (daily)
- `unattended-upgrades.service` is loaded and active.
- `APT::Periodic::Download-Upgradeable-Packages "0"` — packages are upgraded
  on schedule but the downloads themselves are not pre-staged.

> Container images are **not** covered by this and will not auto-update. See
> [03-docker-containers.md](03-docker-containers.md) for image ages.

## Init / orchestration

- `systemd` (PID 1, with `systemd-oomd` userspace OOM-killer active).
- 42 active service units; the workload-bearing ones are listed in
  [06-running-services.md](06-running-services.md).

## Snap packages

`/var/lib/snapd` is populated with: `chatgpt-linux`, `firefox` (×2),
`firmware-updater` (×2), `core18/20/22/24` runtimes, `gnome-3-28-1804`,
`gnome-42-2204`, `gnome-46-2404`, `gaming-graphics-core24`, `mesa-2404`,
`ngrok` (×2), `snap-store`, `snapd`, `snapd-desktop-integration`, `steam`,
`tailscale`, `thunderbird` (×2).

> This is a *desktop* install (GDM, GNOME, Firefox, Steam, Thunderbird) being
> used as a server. The desktop session is consuming RAM and a public seat
> login on tty2.
