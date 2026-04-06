# Shared Group Permissions for Central Storage

## Context
After enabling Samba access to `/mnt/storage/projects`, Linux terminal access became inconsistent because the storage path was owned by the dedicated Samba user only.

## Problem
The Samba user (`smbuser`) could read and write through SMB, but the main server user (`diego`) could not access or manage the same directories reliably from the terminal.

## Objective
Create a shared permission model so both Samba-based access and direct terminal access work consistently.

## Implementation

### 1. Create shared group
```bash
sudo groupadd shared
2. Add users to group
sudo usermod -aG shared diego
sudo usermod -aG shared smbuser
3. Change group ownership of storage
sudo chown -R smbuser:shared /mnt/storage
4. Apply directory permissions with setgid
sudo chmod -R 2775 /mnt/storage
5. Refresh current shell group membership
newgrp shared
Result

Both diego and smbuser can now access the same storage paths consistently, and new files/directories inherit the shared group.

Security Notes
Access remains limited to local server users and authenticated Samba users
Group-based permissions are more maintainable than assigning ownership to a single user only
Next Steps
Keep all project directories under the shared group model
Validate Docker integration with the same permission strategy