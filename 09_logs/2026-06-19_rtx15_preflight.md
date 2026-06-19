# RTX-1.5 Preflight Validation

## Context

Preparation for migrating Ollama on the RTX node (Torre) from a user tray process to a persistent Windows service managed by NSSM.

## Completed checks

### Baseline validation
- OLLAMA_HOST machine scope verified.
- OLLAMA_MODELS machine scope verified.
- RTX-1.4 firewall rules validated.
- Tailscale connectivity validated.
- GPU baseline recorded.

### Tray shutdown
- Startup shortcut disabled by rename:
  - Ollama.lnk → Ollama.lnk.rtx15-disabled
- Ollama tray process stopped.
- Listener on TCP 11434 removed.
- GPU returned to idle state.

### NSSM staging
- NSSM 2.24 (64-bit) installed at:
  - C:\Tools\nssm\nssm.exe
- SHA256 recorded.
- Log directory created:
  - D:\ai\ollama\logs

### Security validation
- LocalSystem write access to log directory validated.
- AppLocker/SRP/WDAC reviewed.
- Weak ACL detected on C:\Tools\nssm.

### ACL remediation
Issue:
- Authenticated Users had Modify permissions on the NSSM directory.

Risk:
- Potential privilege escalation through service binary replacement.

Remediation:
- Inheritance removed.
- Explicit permissions applied:
  - SYSTEM: Full Control
  - Administrators: Full Control
  - Users: Read & Execute

Rollback:
- ACL backup stored at:
  D:\ai\ollama\logs\acl-backup_C-Tools-nssm_pre-2.7.txt

## Current state

- Ollama stopped.
- No listener on TCP 11434.
- NSSM staged.
- Security checks passed.
- Ready for RTX-1.5 Step 3 (service creation).