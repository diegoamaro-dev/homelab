# F-INC-1 — Pre-Reboot Continuation Note

**Date:** 2026-10-23
**Type:** Provisional session-preservation record.
**Status:** F-INC-1 is OPEN.
**Do not treat this file as closeout documentation.**

## Current gate status

- G-F1-0 — PASS
- G-F1-1 — PASS
- G-F1-2 — PASS
- G-F1-3 — PASS
- G-F1-4 — PASS
- G-F1-5 — PASS
- G-F1-6 — PASS
- G-F1-7 — IN PROGRESS
- G-F1-8 — NOT STARTED

## Current validated state

The Windows RTX node no longer depends on the mutable `D:` drive letter for Ollama infrastructure.

Production Ollama now uses:

`C:\AmaroLab\Volumes\Contenedor\ai\ollama\models`

Validated facts:

- NSSM production configuration points Ollama models and logs to the stable NTFS mount path.
- Machine and user `OLLAMA_MODELS` persistent values point to the stable mount path.
- Production Ollama restarted successfully with the new configuration.
- `qwen2.5:7b-instruct` loaded and inferred successfully on the RTX GPU.
- GPU offload validated at 29/29 layers.
- The model store was not modified by validation inference.
- UM790 proxy → RTX primary inference was validated.
- Aurora / Open WebUI was operator-confirmed working normally.
- Removing `D:` did not affect the stable mount.
- Ollama restarted successfully while `D:` was absent.
- Model inference succeeded while `D:` was absent.
- `D:` was restored afterward to the same physical volume.
- Stable mount and `D:` currently resolve to the same volume.
- Ollama service is currently `Running`, configured `Auto`, under `LocalSystem`.

## G-F1-7 next action

Perform a controlled cold reboot of the RTX Windows node and validate:

1. Windows actually rebooted.
2. The stable NTFS mount exists before interactive user login is required.
3. `OllamaService` starts automatically.
4. Production Ollama uses the stable mount path.
5. Port `11434` has one listener owned by the production child.
6. API and model catalogue work.
7. `qwen2.5:7b-instruct` inference works on GPU.
8. UM790 proxy and Aurora continue to reach the RTX primary.

## Safety / rollback

- Do not use `mountvol /P`.
- Do not remove the stable mount directory while it is mounted.
- The physical volume identifier must remain sanitized in repository documentation as `<CONTENEDOR_VOLUME_GUID>`.
- No Git stage, commit, push, or tag has been authorized as part of this checkpoint.
