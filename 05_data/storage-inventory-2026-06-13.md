# 11 — Storage

## Block devices

| Device | Size | Role | Filesystem | Mount | UUID |
|--------|------|------|------------|-------|------|
| `nvme0n1p1` | 1 GB | EFI System | vfat | `/boot/efi` | `A0FE-2591` |
| `nvme0n1p2` | 475.9 GB | root | ext4 | `/` | `1bf79dc1-2169-422e-a43b-bea5d00cf789` |
| `sda1` | 1.8 TB | bulk storage | ext4 | `/mnt/storage` | `2a351e9b-c70d-4e35-a8e1-f4c33e927b08` |
| `/swap.img` | 8 GB | swap (file) | swap | (system) | — |

`smartctl` requires root and was skipped — wear / health unknown for both
drives.

## Filesystem usage

| Mount | Type | Size | Used | Avail | Use% |
|-------|------|------|------|-------|------|
| `/` | ext4 | 468 G | 98 G | 346 G | 23 % |
| `/mnt/storage` | ext4 | 1.8 T | 9.7 G | 1.7 T | 1 % |
| `/boot/efi` | vfat | 1.1 G | 6.2 M | 1.1 G | 1 % |
| `/dev/shm` | tmpfs | 15 G | 0 | 15 G | 0 % |
| `/run` | tmpfs | 3.0 G | 7.5 M | 3.0 G | 1 % |
| `/run/lock` | tmpfs | 5.0 M | 12 k | 5.0 M | 1 % |
| `/run/user/1000` | tmpfs | 3.0 G | 132 k | 3.0 G | 1 % |

> The 1.8 TB HDD is **largely empty** (~9.7 GB used). Adopting it as the
> primary backup target would be straightforward.

## `/etc/fstab`

```
UUID=…cf789  /             ext4  defaults                  0 1
UUID=A0FE-…  /boot/efi     vfat  defaults                  0 1
/swap.img    none          swap  sw                        0 0
UUID=…27b08  /mnt/storage  ext4  defaults,nofail           0 2
```

No additional mounts — no NFS, no SMB client, no encrypted volumes.

## Directory layout (workload-relevant)

### `/` (root, NVMe) — 98 GB used

| Path | Size | What |
|------|------|------|
| `/srv/homelab/data/ollama` | 8.3 GB | Ollama model blobs |
| `/srv/homelab/data/openwebui` | 903 MB | Open WebUI DB + caches + uploads |
| `/srv/homelab/data/npm` | 292 kB | NPM config + Let's Encrypt |
| `/srv/homelab/homeassistant` | 12.4 MB working files | HA config + DB |
| `/srv/homelab/data/portainer` | empty placeholder dir |
| `/srv/homelab/data/proxy` | empty placeholder dir |
| `/srv/homelab/data/steam` | empty placeholder dir |
| `/srv/homelab/data/homeassistant` | empty (the real HA dir is one level up) |
| `/srv/homelab/backups` | **empty** |
| `/srv/homelab/compose` | **empty** |
| `/srv/homelab/scripts` | **empty** |
| `/home/diego/homelab/03_services/zigbee-stack/{mosquitto,zigbee2mqtt}` | Zigbee stack bind mounts |
| `/home/diego/homelab/ai-stack/data/qdrant` | 2.8 MB | Qdrant storage |
| `/home/<USERNAME>/<AI_ASSISTANT_HOME>` | (working dir for the AI assistant CLI) |
| `/var/lib/docker` | Default Docker root — overlay images, the `portainer_data` volume |

### `/mnt/storage` (HDD) — 9.7 GB used / 1.8 TB capacity

| Path | Size | What |
|------|------|------|
| `projects/` | 9.7 GB | Shared via Samba (`[projects]` share) |
| `backups/` | empty | Designated backup target — unused |
| `personal/` | empty | |
| `shared/` | empty | |
| `lost+found/` | 16 kB | fsck recovery (system) |

Ownership: `smbuser:shared` with `2775` (`setgid`), so files inherit the
`shared` group — both `diego` and `smbuser` can read/write.

## Network filesystems served

- **Samba share `[projects]`** on `/mnt/storage/projects`. Port 445 + 139.
  `valid users = smbuser`, `force user = diego`, `force group = shared`.
  Browsable, read/write.
- **WebDAV** vhost at `webdav.local:8088` (Apache, Basic auth, no TLS).
  Document root `/var/www/webdav`. 1 password entry in
  `/etc/apache2/webdav.passwd`. (Confirming password contents needs root.)
- **rpcbind / portmapper** on TCP/UDP 111 — exposed but with no NFS server
  registered (`rpcinfo -p` only shows `portmapper` itself).

## Snapshots / RAID / redundancy

- No LVM, no MD RAID, no Btrfs/ZFS — both filesystems are plain ext4 on a
  single device.
- No snapshotting in place.
- Single point of failure per disk. Loss of `nvme0n1` would take down the
  entire homelab stack; loss of `sda` would take down the Samba share and
  (intended) backup target.
