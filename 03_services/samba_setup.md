# Samba Setup – Network Storage Access

## Context
After establishing a persistent storage layer on the homelab server (`/mnt/storage`), it became necessary to enable access from external devices (desktop and laptop) through the local network and VPN.

The goal was to expose the `projects` directory as a network drive to centralize development workflows.

## Objective
Provide secure and authenticated access to server storage from external devices using Samba, allowing seamless file management and development across systems.

## Architecture


Windows (Client)
↓
Samba (SMB Protocol)
↓
Linux Permissions
↓
/mnt/storage/projects


## Implementation

### 1. Install Samba

```bash
sudo apt update
sudo apt install samba -y
2. Create dedicated Samba user
sudo adduser smbuser
3. Set Samba password
sudo smbpasswd -a smbuser
sudo smbpasswd -e smbuser
4. Configure shared directory permissions
sudo chown -R smbuser:smbuser /mnt/storage/projects
sudo chmod -R 775 /mnt/storage/projects
5. Configure Samba share

Edit:

sudo nano /etc/samba/smb.conf

Add at the end:

[projects]
   path = /mnt/storage/projects
   browseable = yes
   read only = no
   writable = yes
   valid users = smbuser
   force user = smbuser
   create mask = 0660
   directory mask = 0770
6. Improve compatibility with Windows

Inside [global]:

server signing = auto
client min protocol = SMB2
7. Validate configuration
testparm
8. Restart Samba
sudo systemctl restart smbd
sudo systemctl enable smbd
Client Connection (Windows)
Option 1 – File Explorer
\\<SERVER_LAN_IP>\projects
Option 2 – Map network drive
net use Z: \\<SERVER_LAN_IP>\projects /user:smbuser
Validation
Samba service running (active)
Port 445 listening
Share visible from Windows
Network drive successfully mapped (Z:)
Read/write operations working correctly
Problems Encountered
1. Attempted access via browser
Samba is not HTTP-based
Must be accessed via file explorer or SMB client
2. Permission denied on write
Root cause: Linux filesystem ownership mismatch
Solution: assign ownership to smbuser
3. Initial connection failure
Caused by missing Samba installation/configuration
Resolved by proper setup and service restart
Security Notes
Samba is only exposed to local network / VPN
No external port forwarding configured
Authentication required (valid users)
Result

The homelab server now provides centralized, persistent, and network-accessible storage, allowing all development work to be performed directly on the server.

This establishes a unified data layer across devices.

Next Steps
Migrate all development projects to /mnt/storage/projects
Configure automatic network drive mounting on client devices
Implement backup strategy
Integrate storage with Docker services