# F-INC-1 — Stable Ollama Model Store Closeout

**Date:** 2026-10-23
**Type:** Production change closeout
**Status:** **DONE**
**Scope:** Windows RTX compute node storage-path hardening for Ollama
**Production changed:** yes
**Git operations performed during implementation:** none

---

## Context

The 2026-10-20 Aurora incident exposed a structural weakness on the Windows RTX node: Ollama referenced its model store through a mutable Windows drive letter.

When disk enumeration changed, the physical model volume no longer appeared under the expected letter. Ollama remained reachable, but its required model was no longer visible through the configured path.

F-INC-2 independently hardened the UM790 `ollama-proxy` so this condition degrades Aurora to the CPU fallback instead of removing Aurora from the user-facing interfaces.

F-INC-1 addresses the underlying Windows storage dependency.

---

## Objective

Remove Ollama's infrastructure dependency on a mutable Windows drive letter while preserving:

- the existing physical model volume;
- the human-facing drive letter for normal workstation use;
- the existing model files without copying or moving them;
- NSSM headless service operation;
- RTX GPU acceleration;
- UM790 proxy behaviour;
- Aurora availability.

---

## Architecture Decision

The physical NTFS model volume keeps its normal drive letter for interactive use, but Ollama infrastructure no longer depends on that letter.

A stable NTFS volume mount is used instead:

```text
C:\AmaroLab\Volumes\Contenedor
```

Ollama production paths are now:

```text
OLLAMA_MODELS=C:\AmaroLab\Volumes\Contenedor\ai\ollama\models

stdout:
C:\AmaroLab\Volumes\Contenedor\ai\ollama\logs\server.log

stderr:
C:\AmaroLab\Volumes\Contenedor\ai\ollama\logs\server-err.log
```

The mount resolves directly to the physical volume identity:

```text
<CONTENEDOR_VOLUME_GUID>
```

The volume GUID is intentionally not recorded in shared documentation.

The workstation drive letter remains an alias to the same physical volume and is no longer a production dependency for Ollama.

---

## Google Drive Decision

The incident review also checked whether Google Drive virtual-drive behaviour could interfere with the model volume.

Observed state:

- one Google Drive account has an explicitly pinned drive letter;
- another account has no stored drive-letter preference and is intentionally left unpinned.

Operator decision:

- do not modify the unpinned account;
- do not manipulate drive letters solely to force Google Drive placement;
- do not edit Google Drive registry state directly;
- make Ollama independent of cloud-drive letter allocation instead.

After F-INC-1, Google Drive drive-letter allocation is not part of the Ollama storage architecture.

Account identities and addresses are intentionally omitted.

---

## Implementation

### Stable NTFS mount

A persistent NTFS mount folder was created:

```text
C:\AmaroLab\Volumes\Contenedor
```

Validation confirmed that the mount folder and the workstation drive letter resolve to the same physical NTFS volume.

The existing model data remained in place. No model blobs or manifests were copied or migrated.

### NSSM service

`OllamaService` remains:

```text
Startup  : Automatic
Identity : LocalSystem
Host     : 0.0.0.0:11434
```

The service environment now uses:

```text
OLLAMA_MODELS=C:\AmaroLab\Volumes\Contenedor\ai\ollama\models
```

NSSM stdout and stderr paths were also moved to the stable mount alias.

Machine- and user-scope persistent `OLLAMA_MODELS` values were reconciled to the same stable path.

### Network posture

No intended network exposure change was made.

The existing inbound Ollama firewall rule remained enabled and remotely scoped rather than open to `Any`.

The UM790 `ollama-proxy` configuration was not changed by F-INC-1.

---

## Validation

### G-F1-0 — PASS

Baseline and scope confirmed.

### G-F1-1 — PASS

The physical model volume was validated independently of its drive letter. The workstation drive letter and stable NTFS mount were proven to resolve to the same volume and the same model-store files.

### G-F1-2 — PASS

A child-only shadow Ollama instance was started on loopback using the stable model path.

Validation confirmed:

- isolated loopback listener;
- correct Ollama version;
- required model visible;
- successful deterministic inference;
- full RTX GPU offload;
- no model pull;
- no model-store mutation;
- no impact to production Ollama.

The shadow process and wrapper were fully removed afterward.

### G-F1-3 — PASS

Production persistent configuration was changed to the stable mount.

Exact readback confirmed:

- NSSM `AppEnvironmentExtra`;
- NSSM stdout path;
- NSSM stderr path;
- Machine-scope `OLLAMA_MODELS`;
- User-scope `OLLAMA_MODELS`.

### G-F1-4 — PASS

`OllamaService` was restarted.

The new production process confirmed effective runtime configuration on the stable model path.

Validation confirmed:

- service running;
- one production Ollama process;
- one listener on `11434`;
- Ollama `0.30.10`;
- required model catalogue entry;
- deterministic inference response;
- `29/29` model layers offloaded to GPU;
- full model residency in VRAM;
- stable model-store paths used by runtime;
- zero references to the former drive-letter model path in the validated startup/inference window;
- no model pull;
- no model-store mutation.

### G-F1-5 — PASS

UM790 end-to-end validation confirmed:

```text
Aurora / Open WebUI
        ↓
UM790 ollama-proxy
        ↓
RTX primary Ollama
```

A proxy inference request successfully loaded the required model on the primary RTX upstream while the UM790 CPU fallback remained unloaded.

The operator additionally confirmed Aurora / Open WebUI was visible and operating normally.

### G-F1-6 — PASS

This was the decisive drive-letter independence test.

The workstation drive letter was temporarily removed while leaving the stable NTFS mount intact.

With the drive letter absent:

- the stable model path remained accessible;
- Ollama remained healthy;
- `OllamaService` was restarted from zero;
- the required model catalogue remained available;
- deterministic inference succeeded;
- `29/29` layers were offloaded to the RTX GPU;
- runtime blob paths referenced the stable mount;
- zero runtime blob paths referenced the removed drive letter;
- the model store remained unchanged.

The workstation drive letter was restored to the same physical volume afterward.

### G-F1-7 — ACCEPTED WITH RESIDUAL LIMITATION

A real Windows reboot was observed during regression validation. Windows booted and `OllamaService` started automatically seconds later.

The exact condition "service available before interactive user login" was not directly captured during this F-INC-1 cycle. The operator chose not to repeat a reboot solely to reproduce that subcondition.

This does not invalidate F-INC-1's storage result. Headless reboot-without-login behaviour had already been validated historically during RTX-1.5.

### G-F1-8 — PASS

Regression checks confirmed:

- `OllamaService` remains `Automatic`;
- service identity remains `LocalSystem`;
- one production listener exists on `11434`;
- one production `ollama.exe` exists;
- NSSM model/log paths remain on the stable mount;
- inbound firewall access remains scoped and not `Any`;
- `ollama-proxy` host and container configuration hashes match;
- proxy configuration has no local Git modification;
- `openwebui` remains healthy;
- `ollama-proxy` remains healthy;
- UM790 local Ollama remains available;
- proxy API remains operational.

---

## Result

**F-INC-1 is complete.**

The RTX node's Ollama model store is now addressed by stable NTFS volume identity rather than by a mutable Windows drive letter.

The following invariant is now validated:

> Loss, reassignment, or temporary absence of the workstation drive letter must not prevent production Ollama from locating Aurora's model store.

The normal workstation drive letter remains available for human use, but it is no longer a load-bearing Ollama infrastructure dependency.

No model files were moved or duplicated.

---

## Security and Privacy Notes

- No credentials, tokens, private keys, QR codes, public addresses, real account emails, or cloud-account identifiers are recorded here.
- The physical NTFS volume GUID is represented only as `<CONTENEDOR_VOLUME_GUID>`.
- Network-specific identifiers must remain represented by repository placeholders where documentation is shared.
- `mountvol /P` must not be used for this architecture.
- Never recursively delete the stable mount directory while the volume is mounted.

---

## Rollback

If the stable mount must be removed deliberately:

1. stop dependent services;
2. verify the physical volume identity;
3. remove only the mount-folder association using the safe `/D` operation;
4. never use `/P` as a routine rollback;
5. do not delete the mount directory until it is confirmed unmounted and empty;
6. restore a validated stable mount before returning Ollama to production.

Reverting Ollama back to a mutable drive-letter path is not the preferred rollback because it reintroduces the failure mode that F-INC-1 removed.

---

## Problems Encountered

- The first `AppEnvironmentExtra` registry write used the wrong PowerShell value shape for `REG_MULTI_SZ`; the write failed safely and the original configuration remained intact. The change was retried using an explicit string array.
- The first attempt to restore the workstation drive letter used an incomplete `mountvol` target syntax. `mountvol` printed its help and made no change. The corrected root-path syntax restored the letter successfully.
- Proxy access logs did not initially provide useful upstream evidence. Upstream selection was instead proven by issuing an inference through the proxy and immediately checking model residency on the RTX primary and UM790 fallback.

No failed step caused model loss, service corruption, or persistent production outage.

---

## Follow-up

F-INC-2 is already complete.

The remaining incident follow-up is:

```text
F-INC-3 — Torre recovery runbook
```

F-INC-3 should document recovery of:

- stable NTFS storage mapping;
- `OllamaService` / NSSM configuration;
- Paused/orphaned service cases;
- port-bind conflicts;
- model-store verification;
- GPU validation;
- firewall validation;
- UM790 end-to-end validation.

---

## Documentation Reconciliation Required

Before Git closeout, reconcile at minimum:

- `00_overview/CURRENT_STATE.md`
- `00_overview/ROADMAP.md`
- `00_overview/AMAROLAB_HANDOFF.md`
- `01_architecture/amarolab_architecture.md`
- `06_security/rtx_node_security.md`
- `07_operations/lessons_learned.md` if the applied mitigation is not already recorded

Historical RTX-1 evidence must remain historical and must not be rewritten as though the stable mount existed during the original June validation.
