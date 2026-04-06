# Storage Foundation Setup

## Context
The homelab server required a stable and centralized storage layer to support project data, backups, and shared resources across devices (desktop, laptop, and future services).

Initially, an external SSD was used through the router (FRITZ!Box) as a basic NAS solution, which proved to be limited and not suitable for a scalable infrastructure.

## Objective
Establish a reliable, Linux-native storage system directly connected to the homelab server, ensuring stability, performance, and compatibility with future services such as Samba and containerized applications.

## Hardware
- External SSD (~2TB)
- Connected directly to the homelab server via USB

## Initial State
- Disk formatted as NTFS
- Mounted automatically under `/media/...`
- Dependent on user session
- Not suitable for server-grade usage

## Approach
The disk was fully reinitialized and converted to a Linux-native filesystem.

### Steps Performed
1. Unmounted existing NTFS partition
2. Wiped existing filesystem signatures
3. Created new GPT partition table
4. Created primary partition
5. Formatted disk as ext4
6. Mounted disk at `/mnt/storage`
7. Configured persistent mount using `/etc/fstab`

## Mount Configuration

Mount point:

/mnt/storage


Filesystem:

ext4


Fstab entry (sanitized):

UUID=<DISK_UUID> /mnt/storage ext4 defaults,nofail 0 2


## Validation

- Disk successfully mounted using `mount -a`
- Verified with `df -h`
- Write test performed (`test.txt` created successfully)
- Mount persists across reload tests

## Directory Structure


/mnt/storage
├── projects
├── backups
├── personal
└── shared


### Purpose of each directory

- `projects` → source code, repositories, development work
- `backups` → critical backups and snapshots
- `personal` → non-critical personal data
- `shared` → temporary or cross-device shared files

## Permissions

Ownership:

diego:diego


Permissions:

775


## Key Decisions

### ext4 instead of NTFS
- Native Linux support
- Better performance
- Proper permission handling
- More reliable for server environments

### Dedicated mount point (`/mnt/storage`)
- Avoids dependency on user sessions
- Ensures predictable paths for services
- Required for Docker and Samba stability

## Security Notes
- Disk is locally attached to the server
- No direct external exposure
- Future access will be controlled via VPN and authenticated services

## Result
The homelab now has a stable and persistent storage foundation, independent of user sessions and compatible with Linux services and network sharing.

## Next Steps
- Configure Samba for network access
- Define backup strategy
- Integrate storage with Docker services
- Evaluate future migration to a dedicated NAS system