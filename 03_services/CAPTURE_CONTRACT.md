# I-3 Capture Contract

**Ratified:** 2026-07-28 (the field set approved in the I-3 execution package)
**Gate:** G-I3-02
**Applies to:** every `docker-compose.yml` under `03_services/` produced by I-3.

This document defines what *"the file matches reality"* means. Without it, a parity
claim is unfalsifiable — a reader cannot tell whether an absent field was verified
equal or simply never checked.

---

## 1. Method

**Reality is `docker inspect`.** Nothing else is consulted. The Portainer-stored stack
definitions under `/data/compose/` are **not read** — they are known-divergent (H-4) and
have no authority here.

**A compose file expresses what was specified at container creation.** Everything else
comes from the image. The two are separated mechanically, not by judgement:

```
creation-time override  =  container Config.<field>  ≠  image Config.<field>
```

Fields equal to the image default are **not** written into the compose file. Writing them
would invent specification that does not exist and would pin values the image owns.

**Consequence, stated rather than hidden:** every in-scope image except four is consumed
at its default `entrypoint`/`cmd`/`user`. Six of the twelve images are mutable tags
(`:latest`, `:main`, `:stable`), so a future `docker pull` can change a default this
contract deliberately does not capture. That exposure is **M-7/M-C** (digest pinning) and
is out of I-3 scope by doctrine.

## 2. Fields in the contract

Each must be reproduced, or its absence explained.

| Field | Source | Notes |
|---|---|---|
| image tag | `Config.Image` | recorded as-is; **not** pinned to a digest (M-C) |
| image digest | `Image` | recorded in the bundle as capture evidence only |
| `container_name` | `Name` | always written — see §4 |
| restart policy | `HostConfig.RestartPolicy.Name` | |
| networks | `NetworkSettings.Networks` | declared `external: true` with explicit `name:` |
| published ports | `HostConfig.PortBindings` | **including `HostIp`** — loopback vs all-interfaces is a security property |
| mounts | `Mounts[]` | source, destination, type, `ro`/`rw` |
| environment | `Config.Env` minus image `Config.Env` | creation-time only; secret values redacted per §3 |
| `command` | `Config.Cmd` | only when ≠ image default |
| `entrypoint` | `Config.Entrypoint` | only when ≠ image default |
| `user` | `Config.User` | only when ≠ image default |
| cpu limit | `HostConfig.NanoCpus` | `cpus:` |
| memory limit | `HostConfig.Memory` | `mem_limit:` |
| devices | `HostConfig.Devices` | host path redacted per §3 |
| `privileged`, `group_add`, `cap_add`, `security_opt` | `HostConfig` | all null/false across the estate; omitted |
| healthcheck | `Config.Healthcheck` | only when ≠ image default |
| labels | `Config.Labels` minus image labels minus compose's own | none exist; omitted |

## 3. Excluded, with reasons

| Excluded | Reason |
|---|---|
| `MemorySwap` | Docker's implicit 2× `mem_limit` default, not a passed flag. Precedent: F6.1 baseline capture §3.2 |
| Auto-assigned container IPs, MAC addresses | assigned at runtime, not specified |
| Container IDs, `Created`, `StartedAt` | identity and chronology, not configuration |
| Image-provided labels (`org.opencontainers.*`, vendor labels) | owned by the image |
| Compose's own labels (`com.docker.compose.*`) | written by compose at deploy time |
| `ExposedPorts` deltas caused by publishing | `-p` implies expose; not a separate specification |
| Network aliases equal to service/container name | added automatically by compose |
| `User: ""` vs image `null` | the same value in two encodings, not an override |

**Redaction.** Two value classes are redacted in the committed files:

1. **Secret env values** — replaced with `<REDACTED:sha256:…:len=N>`. The digest is
   recorded in the gitignored bundle, which is sufficient to prove parity without
   publishing the value.
2. **The Zigbee dongle host path** — the device serial is redacted `<DEVICE_ID>`, following
   the existing repository convention (`01_architecture/zigbee_network.md:34`,
   `06_security/remediation-2026-06-13/03-medium.md:566`).

**Redaction is a publication measure, not a mechanism change.** No running container was
altered, no variable renamed, no secret moved. The direct consequence is recorded as a
remediation item: **the committed files are not directly deployable** until a supply
mechanism is chosen (R-I3-2, R-I3-5).

## 4. Artifact status and inertness

Every file produced by I-3 is a **Recovery Artifact**, not the production deployment
source. Git becomes the deployment source of truth only after a future convergence project
validates these files.

Two mechanical guards enforce that:

1. **Distinct project names.** Files describing containers that carry no compose labels use
   an `amarolab-` prefixed `name:`, which cannot match any running container's
   `com.docker.compose.project` label. No compose invocation against these files can adopt
   or recreate a running container. `zigbee-stack` is the deliberate exception — its
   containers *are* labeled `zigbee-stack` and its file is restored at the exact path they
   name, which is the point of restoring it.
2. **Explicit `container_name`.** An accidental `up` fails on a name collision instead of
   silently creating a duplicate.

The project-name prefix is a property of a new artifact, not a rename of anything that
exists: `openwebui`, `qdrant`, `portainer` and the five `aurora-*` containers belong to no
compose project today. `ollama` is the single container whose real project label
(`ai-local`) differs from the artifact's name; that deviation is recorded here, in the file
header, and in the apply log.
