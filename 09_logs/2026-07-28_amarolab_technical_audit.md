# AMAROLAB — Full Technical Audit

**Date:** 2026-07-28 (02:28–02:50 CEST)
**Method:** Read-only verification of the running system against the documented
architecture. The running system was treated as the source of truth.
**Production changed:** **NO.** No service restarted, no file modified, no commit, no push.
**Scope:** host, Docker, backups, Home Assistant, Zigbee, Aurora/AI stack, networking,
monitoring, automation, git workflow, repository hygiene.

> **Publication note (added at publication, 2026-07-28).** This document was produced during
> the audit session and published into the repository unmodified except for one sanitization:
> the Guardian Cloud tunnel token value in **H-7** is rendered `<TOKEN>` per
> `PROJECT_RULES.md` → *Security Rules*. Nothing else was altered — no finding, severity,
> evidence block or count.
>
> This is a **dated historical record** (`PROJECT_RULES.md` → *Historical Documentation*). It
> states what was true at 02:28–02:50 CEST on 2026-07-28 and is **never rewritten** as
> remediation advances. Live finding status is tracked in
> [`2026-07-28_amarolab_remediation_roadmap.md`](2026-07-28_amarolab_remediation_roadmap.md)
> and, once reconciled at I-7, in the overview triad. Corrections belong in later documents —
> two already exist: [`2026-07-28_backup_retention_incident.md`](2026-07-28_backup_retention_incident.md)
> corrects the H-1 diagnosis, and the remediation roadmap records C-1's service resolution.

**Baseline read:** `00_overview/START_HERE.md` → `PROJECT_RULES.md` →
`04_ai_system/amarolab-v1/AMAROLAB_HANDOFF.md` → sub-project `CURRENT_STATE.md` /
`ROADMAP.md` (both pointers) → the authoritative overview triad →
`09_logs/2026-07-28_phaseF_F6_1_step2_handoff.md`.

**Note on authority.** The two sub-project files named in the reading order are
deliberate pointers carrying no live state. Live state is the overview triad
(`00_overview/`), which is what this audit verifies against.

---

## 0. Executive summary

The platform is **substantially healthy and unusually well documented**, and several
architectural investments proved themselves under real conditions during this audit
(see §9). Three things need attention:

1. **A live outage nobody noticed.** Zigbee2MQTT has been down since 00:10 CEST tonight;
   both Zigbee devices are `unavailable`. It did not self-recover, and nothing alerted.
2. **Backup retention has been silently failing for ~30 days**, and the probe that is
   supposed to watch backups reports `ok` throughout.
3. **The infrastructure has no complete declarative definition.** The compose file for
   the running Zigbee stack does not exist on disk, and the stored definition of the AI
   stack would, if redeployed, silently undo RTX-1.6 and disable Aurora's awareness,
   RAG and Home Assistant tools.

Findings 1 and 3 share a root cause with the current phase: the F6.1 corpus-recording
session on 2026-07-28 used a USB microphone, and the resulting bus re-enumeration took
the Zigbee coordinator with it.

**Counts:** 1 Critical · 8 High · 10 Medium · 11 Low.

---

## 1. Verified environment

| Item | Observed |
|---|---|
| Host | `homelab`, Ubuntu 24.04.4 LTS, kernel 7.0.0-28-generic, up 2d 2h |
| CPU/RAM | 29 GiB RAM, 16 GiB used, load 0.09 |
| Root disk | `/dev/nvme0n1p2` 468 G, 183 G used (42 %) |
| Bulk disk | `/dev/sda1` → `/mnt/storage` 1.8 T, 11 G used (1 %) |
| Containers | 17 defined, **16 running, 1 exited** |
| Docker | 27 images, 84.6 GB; 29.4 GB build cache |
| Tailscale | `homelab` 100.68.180.69; `torre` active (direct) |
| Open WebUI | 0.8.10, image built 2026-03-09, pulled 2026-06-28 |
| Home Assistant | 2026.3.1 |

---

## 2. CRITICAL

### C-1 — Zigbee2MQTT is down; the entire Zigbee/home-control surface is offline

**Severity:** Critical
**Category:** reliability / operational / infrastructure drift

**Evidence**

```
zigbee2mqtt   Exited (2)   finished 2026-07-27T22:10:22Z (= 00:10:22 CEST 2026-07-28)
              StartedAt    2026-07-25T21:50:55Z   RestartCount 1   policy unless-stopped
```

Container log at exit:

```
[2026-07-28 00:10:22] info:  zh:zstack:znp: Port closed
[2026-07-28 00:10:22] error: z2m: Adapter disconnected, stopping
[2026-07-28 00:10:22] info:  z2m: Stopping Zigbee2MQTT (restart=false, code=2)
```

Kernel, same minute:

```
jul 28 00:10:22 kernel: br-0f11495b815d: port 2(veth4e9f913) entered disabled state
jul 28 00:11:11 kernel: usb 1-2.2.2: Product: Sonoff Zigbee 3.0 USB Dongle Plus
jul 28 00:11:11 kernel: usb 1-2.2.2: cp210x converter now attached to ttyUSB0
```

Live Home Assistant state (queried during this audit):

```
switch.impresora_3d = unavailable   since 2026-07-27T22:10:22Z
cover.toldo         = unavailable   since 2026-07-27T22:10:22Z
```

Host device is present and healthy again: `/dev/ttyUSB0` re-created `jul 28 00:11`,
same stable `by-id` path the container binds. **Only the container is down.**

**Root cause.** *Fact:* a USB hub re-enumeration at 00:10–00:12 removed and re-added the
CP210x bridge; Zigbee2MQTT treats adapter loss as fatal and exits `code=2` by design.
*Established link:* the F6.1 handoff §8 independently records the same event —
"the USB device resets to its hardware default … observed once mid-session (`card2`
recreated `2026-07-28 00:10:14`)". The F6.1 microphone work and this outage are the
same USB event, eight seconds apart. *Hypothesis (unverified without root):* the
container did not restart despite `unless-stopped` because it is bound to
`--device /dev/serial/by-id/usb-ITead_…`, which was absent during the ~49 s
re-enumeration window; Docker's start attempt then fails at device resolution rather
than the process exiting, and Docker abandons retry after its backoff budget.

**Impact.** No Zigbee control or telemetry. `switch.impresora_3d` and `cover.toldo` are
dead to both front doors. Aurora's home awareness will render `Home State: Unavailable`
or a degraded verdict at the next 04:15 cycle. The G-D4/G-D5 voice canary device path is
unavailable, which also blocks F6.1 Step 7 as written.

**Recommendation.** Restart the container (`docker start zigbee2mqtt`), then verify the
two entities return to `off` / a real cover state. Structurally: move the Zigbee
coordinator to a USB port on a hub that is not shared with hot-plugged peripherals, and
add a device-loss recovery path (a systemd `udev`-triggered restart unit, or a healthcheck
plus supervision that tolerates transient device absence). Add the Zigbee coordinator's
presence to the signal layer so this class of failure is detected in minutes, not hours.

**Documentation must be updated:** Yes — `CURRENT_STATE.md` currently states Zigbee2MQTT
"Operational" and Home Assistant "Operational".
**Production should change:** Yes — with operator approval (restart is a production
action and is explicitly out of scope for this audit).

---

## 3. HIGH

### H-1 — Restic retention/prune has failed every night for ~30 days; the backup probe reports `ok`

**Severity:** High
**Category:** backup / monitoring

**Evidence** — `/var/log/homelab-backup.log`, both retained runs:

```
snapshot 7715bf6a saved
repo already locked, waiting up to 0s for the lock
unable to create lock in backend: repository is already locked by PID 226801 on homelab by root
lock was created at 2026-06-27 12:30:52 (710h29m12s ago)
storage ID 06c1fdfa
the `unlock` command can be used to remove stale locks
```

The `restic backup` step succeeds; the subsequent `restic forget --keep-daily 7
--keep-weekly 4 --keep-monthly 6 --prune` fails on the stale exclusive lock. 710 h ≈
**29.6 days** of unenforced retention. Meanwhile `backup_status.json` reports:

```json
{"status": "ok", "snapshot_id": "7715bf6a", "snapshot_time": "2026-07-27T01:00:02Z"}
```

**Root cause.** A dead restic process (PID 226801) left an exclusive lock on
2026-06-27 12:30 — the same day as the E5-b restore drill and the E4-b consistency spike.
It was never cleared. Compounding it, `bin/backup-probe` only evaluates *newest snapshot
age against a 4 h window*; it has no visibility into the exit status of the retention
step, so the failure is invisible to `aurora-context`, to the digest, and to the operator.

**Impact.** Snapshots accumulate without bound (currently modest — restic dedup keeps
each night to ~20 MiB stored — so this is not yet a capacity emergency). The real damage
is the monitoring blind spot: the one automated signal that watches backups has reported
`ok` for a month while half the backup job failed nightly.

**Recommendation.** Clear the stale lock (`restic unlock`) after confirming no restic
process is running, then run one manual `forget --prune` and confirm the retention shape.
Then extend `bin/backup-probe` to consume the **exit status of the whole backup script**,
not just snapshot age — a probe that cannot observe failure is not a probe. This is the
same "fail-loud" lesson already applied to the ingest pipeline at E2-a (finding F-01);
the backup path never received it.

**Documentation must be updated:** Yes — `CURRENT_STATE.md` → Backups says "Operational".
**Production should change:** Yes, with approval.

---

### H-2 — Backup coverage excludes the material needed to actually rebuild the platform

**Severity:** High
**Category:** backup / recoverability

**Evidence** — `PATHS` in `/usr/local/bin/homelab-backup.sh` covers `openwebui`,
`homeassistant`, `npm`, `qdrant`, zigbee/mosquitto data, `/home/diego/webs`,
`09_ops/runtime`, three `/etc` files. **Not covered:**

| Excluded | Why it matters |
|---|---|
| `portainer_data` volume (`/var/lib/docker/volumes/portainer_data/_data`) | Holds `/data/compose/1,2,4` — the **only** copies of the Home Assistant, AI-stack and proxy stack definitions |
| `ai-stack/.env` (mode 0600) | `WEBUI_SECRET_KEY`, `HA_LLAT`, `QDRANT__SERVICE__API_KEY`. Not in git by policy, not in backup → **single copy on one disk** |
| `/home/diego/.secrets/` | Cloudflare connector token, MQTT credentials — same single-copy exposure |
| `/etc/cron.d/aurora-signals` | The entire Aurora signal schedule |
| `/srv/homelab/data/whisper`, `/srv/homelab/data/piper` | Model caches (474 MB). Already known for whisper (F6.1 handoff §8) but not generalised |
| `/srv/homelab/data/openedai-speech/voice_to_speaker.yaml` | The Aurora TTS voice mapping |

**Root cause.** The path list was authored at Phase 0 (2026-06-13, R-12) and has been
extended per-service rather than re-derived from "what does a rebuild need?". Secrets
were correctly excluded from git and then never given a second home.

**Impact.** A loss of the root NVMe is currently **not** recoverable to a running state
from the restic repository alone: the stack definitions, every secret, and the signal
schedule would all be gone. This contradicts the stated principle *Recoverability over
cleverness* and the *Everything recoverable* long-term vision.

**Recommendation.** Add the Portainer volume, `/etc/cron.d/aurora-signals` and the
openedai voice map to `PATHS`. Handle secrets separately and deliberately — an encrypted
secrets bundle (age/gpg) written to a path inside the backup set, or an explicit
documented decision that secrets live only on an offline medium. Do not simply add
`.env` in plaintext to the repository backup without deciding that consciously.

**Documentation must be updated:** Yes — a backup-coverage table belongs in
`07_operations/` and should be referenced from `CURRENT_STATE.md` → Backups.
**Production should change:** Yes, with approval.

---

### H-3 — Most of the running infrastructure has no declarative definition

**Severity:** High
**Category:** infrastructure drift / recoverability / documentation

**Evidence** — compose project labels versus the filesystem:

```
zigbee-stack  → /home/diego/homelab/03_services/zigbee-stack/docker-compose.yml   MISSING
ai-local      → /data/compose/2/docker-compose.yml        (inside portainer_data only)
homeassistant → /data/compose/1/docker-compose.yml        (inside portainer_data only)
proxy         → /data/compose/4/docker-compose.yml        (inside portainer_data only)
ollama-proxy  → 03_services/ollama-proxy/docker-compose.yml   EXISTS (in git)
```

Containers with **no compose labels at all** — i.e. created by bare `docker run` and
reproducible only by reverse-engineering `docker inspect`:

```
openwebui  qdrant  portainer
aurora-whisper  aurora-piper  aurora-wakeword
aurora-whisper-http  aurora-piper-http
```

`03_services/zigbee-stack/` on disk contains only `mosquitto/`, `zigbee2mqtt/` and
`zigbee2mqtt_first_devices.md` — the compose file the running containers name is gone.

**Root cause.** The estate grew through three different mechanisms (Portainer stacks,
hand-run `docker run`, and one properly version-controlled compose project) without a
convention. The `ollama-proxy` project shows the intended pattern was understood; it just
was not applied retroactively.

**Impact.** Rebuilding after host loss is a manual archaeology exercise for 8 of 17
containers, and impossible-as-written for the Zigbee stack. This is precisely the risk the
F6.1 baseline capture log mitigated for *one* container by deriving an exact `docker run`
from the live inspect (§3.2) — the technique is proven, just not systematised.

**Recommendation.** Capture the live configuration of every unmanaged container into
version-controlled compose files under `03_services/`, generated from `docker inspect` and
validated against the running state field-by-field before adoption. Do not recreate any
container to adopt the file — write the file to match reality, verify, and only converge
later under a normal gated change. Restore `03_services/zigbee-stack/docker-compose.yml`
from git history if a version exists there.

**Documentation must be updated:** Yes.
**Production should change:** Not immediately — the capture is documentation-only.
Convergence is a separate, later, gated change.

---

### H-4 — The stored AI-stack definition would silently revert RTX-1.6 and disable Aurora's awareness, RAG and HA tools

**Severity:** High
**Category:** configuration drift / reliability

**Evidence** — Portainer stack 2 (`ai-local`), as stored:

```yaml
openwebui:
  environment:
    - OLLAMA_BASE_URL=http://ollama:11434
    - VECTOR_DB=qdrant
    - QDRANT_URI=http://qdrant:6333
  volumes:
    - /srv/homelab/data/openwebui:/app/backend/data
```

The **running** `openwebui`:

```
OLLAMA_BASE_URL=http://ollama-proxy:11434      ← RTX-1.6
QDRANT_API_KEY=<set, 64 chars>                 ← RAG auth
HA_BASE_URL / HA_LLAT                          ← ha_get_state / ha_call_service
AMAROLAB_AUDIT_LOG=/app/backend/data/amarolab-audit.log
mounts: /srv/homelab/data/openwebui, /home/diego/homelab/ai-stack/aurora → /opt/aurora (ro),
        /home/diego/homelab/ai-stack/ingest → /opt/ingest (ro)
```

A redeploy of that stack from the Portainer UI would drop: the `ollama-proxy` endpoint
(Torre GPU path reverts to the ~6 tok/s CPU Ollama), `/opt/aurora` (the F-3a awareness
Filter and `system_status` both read from it), `/opt/ingest`, the Qdrant API key (RAG
returns 401), `HA_LLAT` (both HA tools break), and the audit-log path (D-07/D-21).

**Root cause.** RTX-1.6, F-2, F-3a and the ER-1 tool work all modified the live container
without updating the stored stack definition — an inevitability of H-3, made worse by the
fact that the stored definition is invisible (inside a Docker volume) and therefore never
reviewed.

**Impact.** A single well-intentioned click reverts eleven gates' worth of validated
behaviour, and does so *quietly* — every service stays "up".

**Recommendation.** Treat this as the highest-value item in the H-3 capture work: bring
the `ai-local` definition to match reality first. Until then, record the hazard
explicitly in `CURRENT_STATE.md` so no future session redeploys that stack.

**Documentation must be updated:** Yes — this is an operational trap and belongs in the
triad, not only in an audit report.
**Production should change:** No. Do **not** redeploy the stack to "fix" it; correct the
definition to match the running state.

---

### H-5 — Ollama is exposed unauthenticated on the LAN

**Severity:** High
**Category:** security

**Evidence**

```
ollama   0.0.0.0:11434->11434/tcp
$ curl -o /dev/null -w '%{http_code}' http://192.168.178.79:11434/api/tags   → 200
models: qwen2.5:7b-instruct, llama3.2, phi3, llama3
```

**Root cause.** The Phase-0-era stack 2 definition publishes `11434:11434` without a bind
address. Nothing in the architecture requires host-level publication: Open WebUI reaches
Ollama over the `ai-local_default` docker network, and Home Assistant reaches the proxy on
`127.0.0.1:11435`. The publication is vestigial.

**Impact.** Any device on `192.168.178.0/24` can run inference, and the Ollama API also
exposes `/api/pull`, `/api/create` and `/api/delete` — model store manipulation, not just
free compute.

**Recommendation.** Bind to loopback (`127.0.0.1:11434:11434`) or drop the publication
entirely. Verify the two documented consumers keep working — neither should notice.
Note this interacts with H-3: the change must land in a definition that survives.

**Documentation must be updated:** Yes — `06_security/` and `CURRENT_STATE.md`.
**Production should change:** Yes, with approval.

---

### H-6 — `homelab-tools.service`: an unauthenticated Flask dev server on 0.0.0.0 serving Docker logs, undocumented, contradicting D-18

**Severity:** High
**Category:** security / obsolete service / documentation drift

**Evidence**

```
● homelab-tools.service - Homelab AI Tools API   enabled; active (running) since 2026-07-25
  ExecStart=/home/diego/homelab/ai-tools/venv/bin/python .../docker_status.py
  WARNING: This is a development server. Do not use it in a production deployment.
  * Running on all addresses (0.0.0.0)  http://…:5050
```

```
$ curl http://192.168.178.79:5050/docker/containers
[{"name":"openwebui","status":"Up 11 hours (healthy)"}, …]     ← unauthenticated, from the LAN
```

`docker_status.py` also serves `/docker/logs?container=…&lines=…` for an allowlist of six
containers (`openwebui`, `ollama`, `qdrant`, `homeassistant`, `nginx-proxy-manager`,
`portainer`), returning up to 200 lines of raw container log.

**Root cause.** A pre-AURORA "Jarvis"-era service that was never retired. Decision **D-18**
explicitly chose path C — *"No bare-metal Flask call in A.2/A.3; the Tool is not implemented
until the containerized `homelab-tools` + `docker-socket-proxy` are built"* — and
`AMAROLAB_HANDOFF.md` records `system_status` as "a legacy Jarvis tool, not the
originally-planned containerized service". Both statements are true of the *Open WebUI
Tool*; neither mentions that the **bare-metal Flask service D-18 forbade is enabled and
running**, and has been since at least the last boot.

**Impact.** Unauthenticated LAN read access to container logs. Open WebUI and Home
Assistant logs routinely contain request URLs, entity ids and error payloads; treating
them as public is a poor default. The Flask development server is also not a hardened
listener. No consumer of port 5050 was found — the live `system_status` tool (v0.3.0) reads
`/opt/aurora/aurora-context.json` and probes Torre directly, not this API.

**Recommendation.** Confirm there is no remaining consumer, then disable and mask the unit.
If a use is found, bind it to `127.0.0.1` at minimum. Either way, document the outcome —
a running service that the architecture says does not exist is the exact failure mode
*"If it is not documented, it does not exist"* is meant to prevent.

**Documentation must be updated:** Yes.
**Production should change:** Yes, with approval.

---

### H-7 — Guardian Cloud tunnel token stored in plaintext in a group-readable compose file, inside the backup set

**Severity:** High
**Category:** security

**Evidence**

```
$ ls -l /home/diego/webs/cloudflared/docker-compose.yml
-rw-rw-r-- 1 diego diego 491 may  1 22:54

  environment:
    - TUNNEL_TOKEN=<TOKEN>         ← plaintext, inline (value redacted at publication)
```

The sibling `cloudflared-amarolab` does it correctly:

```yaml
    env_file:
      - /home/diego/.secrets/cloudflared-amarolab.env      # mode 0600
```

`/home/diego/webs` is inside the restic `PATHS`, so the plaintext token is in **every
nightly snapshot**.

**Root cause.** The Guardian Cloud tunnel predates Lesson 008 and the `.secrets` convention
introduced for the AMAROLAB tunnel on 2026-06-17. It was never retrofitted. This is the
substance behind the long-standing pending item **R-01** ("Cloudflare Tunnel token
rotation") — the item is tracked, but as a rotation task rather than as a live plaintext
credential.

**Impact.** A Cloudflare tunnel token grants the ability to serve traffic for the tunnel's
hostnames — here, Guardian Cloud production (`app.guardiancloud.app`,
`api.guardiancloud.app`). File mode `0664` means any local account can read it, and it is
replicated into ~30 backup snapshots.

**Recommendation.** Rotate the token, move it to `/home/diego/.secrets/cloudflared.env`
(mode 0600) with `env_file`, and `chmod 0600` the compose file. Rotation must come first —
the old value persists in existing snapshots regardless of what happens to the file.
Guardian Cloud is production; this needs explicit approval and a maintenance window.

**Documentation must be updated:** Yes — reframe R-01 from "rotation pending" to the actual
finding, and record the resolution.
**Production should change:** Yes, with approval (touches Guardian Cloud).

---

### H-8 — No host firewall is enforcing; broad LAN service exposure

**Severity:** High
**Category:** security

**Evidence**

```
/etc/ufw/ufw.conf  →  ENABLED=no          (service is active+enabled but installs no rules)
```

`iptables`/`nft` could not be read directly (no passwordless sudo), so enforcement is
asserted from `ufw.conf` and from the fact that every published port answered from the LAN
address during this audit. Listening on all interfaces:

| Port | Service | Auth |
|---|---|---|
| 11434 | Ollama | **none** (H-5) |
| 5050 | homelab-tools | **none** (H-6) |
| 6333 | Qdrant | API key enforced (verified 401) |
| 3000 | Open WebUI | app login |
| 81 | Nginx Proxy Manager admin | single admin account |
| 9443 / 8000 | Portainer | app login |
| 1883 | Mosquitto | authenticated + ACLs (hardened 2026-06-17) |
| 8123 | Home Assistant | app login |
| 8085 | guardian-web | — |
| 3001 | guardian-cloud-backend (pm2) | app |
| 8088 | Apache WebDAV | Basic auth (401 verified) |
| 139/445 | Samba (`projects` → `/mnt/storage/projects`) | `valid users = smbuser` |
| 22 | SSH | password auth **enabled by default** (M-9) |

**Root cause.** UFW was installed and enabled as a unit but never actually turned on. The
posture has been "trust the LAN" by default rather than by decision.

**Impact.** The LAN is the security boundary for twelve services, two of which have no
authentication at all. The homelab's own documented posture ("everything local, single
user") is a *trust* statement, not an *enforcement* one.

**Recommendation.** Decide the posture explicitly and document it. If the LAN is trusted,
say so in `06_security/` and fix only the unauthenticated listeners (H-5, H-6). If not,
enable UFW with a default-deny inbound policy and an explicit allowlist — and test SSH
access before enabling, since this is a lock-yourself-out change.

**Documentation must be updated:** Yes — `06_security/security_posture.md`.
**Production should change:** Yes, with approval and careful sequencing.

---

## 4. MEDIUM

### M-1 — Aurora's awareness is nightly-batch only; there is no alerting anywhere

**Severity:** Medium (systemic — it is why C-1 went unnoticed)
**Category:** monitoring / operational

**Evidence.** The whole signal chain runs once per night: `backup-probe` 03:30,
`container-probe` 04:00, `aurora-context` 04:15, `push-voice-context` 04:20,
`generate-digest` 04:25. Zigbee2MQTT died at 00:10; the next observation is 04:00 —
**3 h 50 m later** — and the only "notification" is text inside a context file the model
reads if asked. Current live artifacts still assert `"all_running": true, "count": 17` and
the HA voice helper still says `17/17 running`.

Mean time to detection for any failure is up to ~24 h, and mean time to *notification* is
unbounded — nothing pages, emails, or pushes.

**Root cause.** By design: Phase F built an *awareness* layer (state Aurora can describe
when asked), not a *monitoring* layer (state that reaches a human when it changes). That
was the right scope for F-2/F-3. The gap is that nothing else fills the monitoring role.

**Recommendation.** Do not bolt alerting onto the digest. Home Assistant is already the
natural place: it holds live entity state, has notification transports, and is already the
voice front door. A small set of HA automations (container-down, backup-stale,
context-stale, coordinator-missing) would give minutes-scale detection without disturbing
the Phase F architecture. The Health Aggregator already in the architectural backlog is
the right home for the producer side when a third producer appears.

**Documentation must be updated:** Yes — as a roadmap item, not a claim of current state.
**Production should change:** Not yet — this is a design decision for the operator.

---

### M-2 — Open git gate: the F6.1 handoff is committed but unpushed, and the document contradicts the repository

**Severity:** Medium
**Category:** git workflow / documentation drift

**Evidence**

```
$ git log --oneline -1      2a185cb1 docs: add F6.1 Step 2 handoff
$ git status                main [origin/main: adelante 1]   working tree clean
$ git rev-list --left-right --count origin/main...main   → 0  1
```

The handoff document §9 states:

```
HEAD        458dda679804e1a22c209249310fb844dc7ffcee
origin/main 458dda679804e1a22c209249310fb844dc7ffcee
divergence  0 / 0
```

and §12 states "**Not committed, not pushed**".

**Root cause.** The classic *Transient Operational Status* failure the project already
codified after Phase ER-1: a document that asserts its own pending state is false the
moment it lands. Here it went false at commit time — the commit that carries the claim is
the commit that falsifies it.

**Impact.** Low functional risk, but a future session reading §9 will believe the repo is
synchronized when one commit is unpublished, and will believe the handoff is uncommitted
when it is not. The `PROJECT_RULES` rule exists precisely to prevent this.

**Recommendation.** Push `2a185cb1` (**requires fresh operator approval per
`PROJECT_RULES` → Operator Git Approval**), then correct §9/§12 in a *later* document —
`09_logs/` entries are historical and must not be rewritten. A short note in the next
F6.1 apply log is the right vehicle.

**Documentation must be updated:** Yes (in a later log, not by rewriting the handoff).
**Production should change:** No.

---

### M-3 — `system_status` violates the D-23/D-25 source-of-truth contract, and `CURRENT_STATE.md` states the wrong version

**Severity:** Medium
**Category:** documentation drift / technical debt

**Evidence**

```
webui.db tool 'system_status'   →  version: 0.3.0
canonical location per D-23     →  ai-stack/openwebui-tools/tools/system_status.py   ABSENT
actual tracked source           →  ai-stack/ingest/docs/system_status_tool.py  (v0.3.0, tracked)
                                   differs from the installed row by one blank line
stale duplicate                 →  ai-stack/openwebui-tools/tmp/system_status.dumped.py
                                   (tracked, no version header, 369 diff lines from live)
CURRENT_STATE.md:369            →  "`system_status` (v0.2.0)"
ROADMAP.md WM-5                 →  "system_status v0.3.0 installed … verified 2026-07-14"
```

**Root cause.** `system_status` originated outside the AURORA tool package and was never
migrated into it when D-23/D-25 established the pattern. The triad then drifted apart: the
ROADMAP was updated at WM-5, `CURRENT_STATE.md` was not — and `CURRENT_STATE.md` is the
declared source of truth.

**Impact.** The one tool that reports Aurora's operational status has the weakest
provenance story of the six. A reader following D-23 to find its source finds nothing;
a reader following `CURRENT_STATE.md` gets the wrong version.

**Recommendation.** Move the canonical source to
`ai-stack/openwebui-tools/tools/system_status.py`, delete the stale `tmp/` dump, correct
`CURRENT_STATE.md` to v0.3.0, and re-stamp the content hash the way ER-1.5 §3 did for
`ha_get_state` / `ha_call_service`.

**Documentation must be updated:** Yes.
**Production should change:** No — the installed tool is correct and working; this is
provenance only.

---

### M-4 — A Python virtualenv is committed to the repository

**Severity:** Medium
**Category:** repository hygiene

**Evidence**

```
$ git ls-files ai-tools/       → 1335 files
$ git ls-files ai-tools/venv/  → 1333 files      (pip vendored libs, certifi cacert.pem,
                                                  __pycache__, python symlinks)
$ du -sh .git                  → 300 M
$ git count-objects -vH        → size-pack 284.71 MiB
```

`.gitignore` excludes `ai-stack/ingest/venv/` but **not** `ai-tools/venv/`. Also tracked:
`ai-stack/openwebui-tools/tmp/*.dumped.py` (four stale dumps).

**Root cause.** The `ai-tools/` directory predates the gitignore discipline applied to
`ai-stack/`, and the exclusion was written per-path rather than as a pattern.

**Impact.** Clone/fetch cost, noise in every `git grep` and RAG-adjacent search (the ingest
corpus already excludes it, correctly), and a supply-chain surface committed as source.
Note the repository history was force-rewritten on 2026-07-10 — removing these now would
*not* require another rewrite, since deletion going forward is sufficient for hygiene; the
blobs would remain in history either way.

**Recommendation.** Add `ai-tools/venv/` and `ai-stack/openwebui-tools/tmp/` to
`.gitignore`, `git rm -r --cached` both, and record the decision. If `homelab-tools` is
retired per H-6, `ai-tools/` may be removable entirely.

**Documentation must be updated:** Yes (a short hygiene log).
**Production should change:** No.

---

### M-5 — Voice-exposure ACL does not match documentation, and the documented canary is not exposed

**Severity:** Medium
**Category:** configuration drift / documentation drift — **blocks F6.1 Step 7**

**Evidence** — `homeassistant.exposed_entities`:

```json
"assistants": { "conversation": { "expose_new": false } },
"exposed_entities": {
  "conversation.home_assistant": { "conversation": { "should_expose": false } },
  "zone.home":                   { "conversation": { "should_expose": false } },
  "sun.sun":                     { "conversation": { "should_expose": false } }
}
```

`CURRENT_STATE.md:478` states: *"Voice-exposure ACL: exactly **one** entity exposed —
`input_boolean.aurora_voice_canary`."* In reality **zero** entities are exposed, and the
canary does not appear in the file at all.

**Root cause.** Most likely the exposure was removed during a later gate cleanup (the ACL
was tightened repeatedly through G-D5/G-D6) without a corresponding triad update. Reality
is *stricter* than documented, so this has been operationally harmless.

**Impact.** Directly blocks the F6.1 plan: Step 7 requires "G-F6-01a…f on the live path
incl. G-D4 canary", and the canary cannot toggle through voice while unexposed. Combined
with C-1 (both Zigbee devices unavailable), **F6.1 currently has no working live voice
acceptance path** — worth knowing before Step 3 begins.

**Recommendation.** Decide whether the canary should be re-exposed for F6.1 Step 7 and
record the decision; then reconcile `CURRENT_STATE.md` to whatever is true.

**Documentation must be updated:** Yes.
**Production should change:** Only if F6.1 Step 7 needs it — operator's call.

---

### M-6 — 58 pending OS updates including the container runtime; unattended-upgrades covers security origins only

**Severity:** Medium
**Category:** security / operational

**Evidence**

```
$ apt list --upgradable | wc -l   → 58
  docker-ce         5:29.4.1 → 5:29.6.2
  containerd.io     2.2.3    → 2.2.6
  docker-buildx-plugin, docker-compose-plugin, apparmor, cloud-init, apport, …
unattended-upgrades: enabled; APT::Periodic::Unattended-Upgrade "1"
last run 2026-07-27 06:55 → "No packages found that can be upgraded unattended"
no /var/run/reboot-required
```

**Root cause.** Working as configured: unattended-upgrades is limited to
`o=Ubuntu,a=noble-security` and ESM origins. Docker packages come from the Docker
repository, which is not an allowed origin, so the container runtime is never patched
automatically. The other 58 are `-updates`, not `-security`.

**Impact.** The container runtime — the component with the largest blast radius on this
host — is two patch releases behind and has no automatic path forward.

**Recommendation.** Schedule a manual maintenance window for the Docker packages
specifically (a runtime upgrade restarts containers; that is a production action needing
approval and a rollback plan). Decide separately whether to widen unattended-upgrades to
`-updates`, weighing unattended restarts against patch currency.

**Documentation must be updated:** Yes — patch policy belongs in `07_operations/`.
**Production should change:** Yes, in a planned window with approval.

---

### M-7 — Production containers run mutable `:latest` / `:main` tags

**Severity:** Medium
**Category:** reliability / reproducibility

**Evidence**

```
ollama/ollama:latest                qdrant/qdrant:latest        koenkk/zigbee2mqtt:latest
portainer/portainer-ce:latest       jc21/nginx-proxy-manager:latest
cloudflare/cloudflared:latest       ghcr.io/open-webui/open-webui:main
ghcr.io/home-assistant/home-assistant:stable
```

Correctly pinned: `rhasspy/wyoming-whisper:3.2.0`, `rhasspy/wyoming-piper:2.2.2`,
`rhasspy/wyoming-openwakeword:2.1.0`, `ghcr.io/matatonic/openedai-speech:0.18.2`,
`fedirz/faster-whisper-server:0.6.0-rc.3-cpu`, `eclipse-mosquitto:2`, `nginx:alpine`.

**Root cause.** The voice stack was built later, under Phase D discipline, and pinned. The
older services were not.

**Impact.** Any `docker pull` on an unpinned service can change behaviour with no
corresponding change in the repository — the failure mode `PROJECT_RULES` → *Reality always
wins* is hardest to reason about, because reality changed without anyone acting. Open WebUI
is the sharpest case: 0.8.10 is a documented runtime contract (D-24/D-25/D-35 all depend on
its loader behaviour), yet the tag is `:main`.

**Recommendation.** Pin every production image to a digest or explicit version, starting
with `open-webui` (record the current digest `sha256:…` for 0.8.10 before anything pulls).
Fold this into the H-3 capture work — the pins belong in the same recovered definitions.

**Documentation must be updated:** Yes.
**Production should change:** No immediate change — pin at the definition level; adopt on
the next planned recreate.

---

### M-8 — 33 GB of reclaimable Docker storage, including 24.8 GB of Voice Lab images

**Severity:** Medium
**Category:** operational hygiene

**Evidence**

```
Images        27 total   84.63 GB   24.56 GB reclaimable (29 %)
Build Cache   33 entries 29.42 GB    8.94 GB reclaimable

vl-chatterbox:latest 11.1 GB  ·  vl-kokoro:latest 9.29 GB
vl-xtts:latest 3.3 GB         ·  vl-piper:latest 1.14 GB       = 24.83 GB
plus: hello-world, qdrant:v1.17.0 (E5-b drill), python:3.12-slim,
      busybox, curlimages/curl, alpine:3.20, linuxserver/ffmpeg
```

**Root cause.** Voice Lab Round 1 completed 2026-07-27 and is documented as repo-external
with no production change — correctly. But "not committed" was applied to the repository
and not to the host: the build artifacts stayed.

**Impact.** Not urgent (root disk is at 42 %), but 33 GB is ~7 % of the root volume held by
work that is finished. `qdrant:v1.17.0` from the E5-b restore drill is worth keeping only
if the drill is meant to be repeatable at that version.

**Recommendation.** Decide which Voice Lab images Round 2 needs (Kokoro at minimum, as the
reference candidate), remove the rest, and prune the build cache. Note the retention
decision in the Voice Lab record so a future session does not re-download 20 GB.

**Documentation must be updated:** Yes (a line in the Voice Lab record).
**Production should change:** No — none of these images backs a running container.

---

### M-9 — SSH password authentication is enabled by default

**Severity:** Medium
**Category:** security

**Evidence** — no `PasswordAuthentication` or `PermitRootLogin` directive is set in
`/etc/ssh/sshd_config` or `sshd_config.d/`; both remain commented, so Ubuntu's defaults
apply (`PasswordAuthentication yes`, `PermitRootLogin prohibit-password`). SSH listens on
`0.0.0.0:22`. `/home/diego/.ssh` exists and is `0700`.

**Root cause.** Default configuration never hardened.

**Impact.** Password-guessing surface on the LAN and over Tailscale. Lower than it looks
(no public exposure found, no port forward observed), which is why this is Medium rather
than High.

**Recommendation.** Set `PasswordAuthentication no` and `PubkeyAuthentication yes`
explicitly in a `sshd_config.d/` drop-in — **after** confirming key-based access works for
`diego` from every device that needs it. Consider `AllowUsers diego`.

**Documentation must be updated:** Yes — `06_security/`.
**Production should change:** Yes, with approval and a verified key path first.

---

### M-10 — The Open WebUI STT shim runs an unmaintained 18-month-old image (R-D-13 still open)

**Severity:** Medium
**Category:** technical debt / reliability

**Evidence** — `aurora-whisper-http` runs `fedirz/faster-whisper-server:0.6.0-rc.3-cpu`,
image created **18 months ago**; `aurora-piper-http` runs
`ghcr.io/matatonic/openedai-speech:0.18.2`, **23 months old**. `CURRENT_STATE.md` already
tracks this as **R-D-13** ("migrate away from the unmaintained
`fedirz/faster-whisper-server`", post-Phase-D maintenance).

**Root cause.** Correctly deferred at D-1.7; simply never scheduled since.

**Impact.** Both shims sit on the Open WebUI voice path. A release-candidate build of an
abandoned project has no security-fix path. The debt is honestly tracked — this finding
raises its visibility rather than reporting anything new.

**Recommendation.** Fold R-D-13 into F-6 scope. F-6 is already the voice-quality phase and
already touches the STT path; migrating the shim under the same measurement protocol
(single-variable isolation, laboratory gate) is markedly cheaper than a standalone effort.
Note this would be a **second** variable relative to D-F6-1, so it must be a distinct
sub-phase after F6.1 closes, never inside it.

**Documentation must be updated:** No new documentation — R-D-13 already exists; only its
scheduling changes.
**Production should change:** No, not in F6.1.

---

## 5. LOW

| # | Finding | Evidence | Recommendation | Docs? | Prod? |
|---|---|---|---|---|---|
| L-1 | System-prompt size drift | `params.system` for `qwen2.5` is **5138** chars; `CURRENT_STATE.md:331` says 4 478; two other places still say 3 342 | Reconcile to the measured value; re-measure the cold-cache cost claim | Yes | No |
| L-2 | HA Piper voice drift | Container runs `--voice es_ES-sharvard-medium --speaker F`; `CURRENT_STATE.md:557` says `es_ES-davefx-medium` | Correct the doc — both paths use sharvard, matching C-D-08 | Yes | No |
| L-3 | Qdrant counts stale; two collections undocumented | Live: `homelab_docs` 2875 (doc 2088), `knowledge_history` 3780 (3132), `ops_digests` 75 (3); `guardian_cloud`/`ensambla2`/`infra_audits`/`myfreetour` exact. `open-webui_files` + `open-webui_knowledge` exist but are unlisted | Doc already says counts grow nightly; add the two Open WebUI-internal collections | Yes | No |
| L-4 | `CURRENT_STATE.md` pending item 9 (F-ER13-1) is stale | Item says "deliberately not fixed"; `bin/aurora-context` now uses `path.with_name(f".{path.name}.{os.getpid()}.tmp")` + a `flock` run-lock (commit `6525b0d2`) | Mark F-ER13-1 resolved | Yes | No |
| L-5 | Empty `QDRANT_API_KEY` in the authoritative env file | `ai-stack/.env` has `QDRANT_API_KEY=` (len 0); the working key is `QDRANT__SERVICE__API_KEY` (len 64), which matches the running container byte-for-byte | Remove the empty entry or set it; it is a recreation trap | Yes | No |
| L-6 | ~2.5 GB of pre-sanitization repo copies retained | `homelab_backup_before_rewrite` 1.9 G · `homelab-sanitize-backup-2026-07-10` 587 M · `homelab-sanitize-work` 25 M · `homelab-rewrite.git` 13 M | Decide retention; these predate the 2026-07-10 sanitization and hold the un-rewritten history | Yes | No |
| L-7 | Nginx Proxy Manager: stale hosts, no TLS forcing | `homeassistant.local`, `jarvis.local` (legacy name → Open WebUI), `ai.homelab`, `portainer.homelab`; all `ssl_forced=0` | Remove stale hosts; decide whether internal TLS matters | Yes | No |
| L-8 | Home Assistant log noise from undocumented integrations | 53 ERROR/WARNING lines: `pychromecast` connect failures, `async_upnp_client` resubscribe failures, `dlna_dmr` >10 s updates | Either document Cast/DLNA as in-scope integrations or remove them; noise hides real errors | Yes | No |
| L-9 | Every restic backup is a full re-scan | "no parent snapshot found, will read all files" on every run; `SNAP_DIR=/tmp/homelab-backup-snapshots/$(date +%F)` changes the path set nightly, so restic cannot match a parent | Use a fixed staging path so parent-snapshot matching works | Yes | Yes (with H-1) |
| L-10 | Voice context asserts a false container count | `input_text.aurora_voice_context` = "…17/17 running…"; actual 16/17 | Self-corrects at 04:15; consequence of M-1, no separate action | No | No |
| L-11 | Known documentation debt still open | `world_model_architecture.md` freeze record still says "not committed, not pushed" (it is `b43e8aad`) and "implementation not started" (true through WM-6); `phase_f_architecture.md:1042` still calls F3.3 "current" | Both are already recorded in ROADMAP → *Documentation Hygiene* and deferred by operator decision; re-confirm or schedule | Yes | No |

---

## 6. Verified correct — no action

These were checked against documentation and **match reality**:

- **D-35 preserved** — `base_model_id` is NULL for all three model rows.
- **`meta.toolIds`** on `qwen2.5:7b-instruct` is exactly
  `["time_now","rag_search","audit_search","ha_get_state","ha_call_service","system_status"]`.
- **D-20 scoping holds** — `llama3` / `llama3.2` see only
  `docker_containers`, `docker_logs`, `system_status`; never the AURORA tools.
- **Tool versions match the record** — `time_now` 0.1.0, `rag_search` 0.2.0,
  `audit_search` 0.1.0, `ha_get_state` **0.2.1**, `ha_call_service` **0.2.0**.
- **ER-1.5 §3 hash stamps verify** — `ha_get_state.py` `b35570c458…` and
  `ha_call_service.py` `aea2bec3b9…` reproduce exactly at HEAD. No drift since 2026-07-21.
- **Entity projection is content-fresh** — `emit-entity-projection --check` →
  `OK — projection current (resolution_sha256 4848e57a62fb…)`.
- **`aurora_context` Filter** is `active + global` in `webui.db.function`; `/opt/aurora`
  and `/opt/ingest` are mounted read-only as specified.
- **Audio surface matches D-1.7** — STT/TTS both `openai` engine at the two shims;
  `voice_to_speaker.yaml` routes every OpenAI slot to `es_ES-sharvard-medium` speaker F.
- **Assist pipeline `AURORA v1`** is preferred; `stt_language: es` confirmed live — which
  independently re-verifies the F6.1 handoff §5 finding that production pins `es` and never
  auto-detects.
- **HA reverse-proxy trust** is exactly `172.18.0.0/16, 127.0.0.1, ::1`; the LAN is
  deliberately not trusted.
- **Mosquitto hardening holds** — `allow_anonymous false`, password file + ACLs.
- **Qdrant authentication is enforced** — unauthenticated requests return 401 from both
  loopback and the LAN address.
- **Torre GPU path is live** — proxy access log shows
  `upstream=100.91.154.124:11434 ut=0.001`; failover config intact.
- **Guardian Cloud is untouched** — clean working tree, last commit 2026-05-18, well
  before all AMAROLAB phase work.
- **Repository sanitization holds** — no AI/vendor co-authorship anywhere; all 30 recent
  commits authored `Diego Vázquez Amaro <diego@diegoamaro.dev>`. The few keyword matches
  are legitimate technical references (the `es_MX-claude-high` Piper voice, a `chatgpt-linux`
  snap inventory entry, and a deliberate "no external LLM" policy statement).
- **Log rotation is live** — `/etc/logrotate.d/homelab-ingest` present and rotating
  `ingest.log`, `aurora-signals.log` and `amarolab-audit.log` on schedule.
- **`ai-stack/.env` is `0600`; `/home/diego/.secrets/` is `0700`** with both files `0600`.
- **No failed systemd units.**

### F6.1 phase state — intact

The active phase's frozen assets were verified because the next session depends on them:

```
production aurora-whisper  matches handoff §8 byte-for-byte:
  image sha256:966e1b0967f3…  cmd ["--model","base-int8","--language","auto",
  "--beam-size","1","--compute-type","int8"]  started 2026-07-25T21:50:55Z  restarts 0
  port 127.0.0.1:10300  mount /srv/homelab/data/whisper/wyoming  --cpus 4 --memory 4g

corpus: 30/30 files re-hashed against manifest entries → 0 mismatches, status FROZEN
        manifest.reference_sha256 788b2dea41072cc6…  MATCH
        manifest.manifest_sha256  b8973451cf4e7694…  MATCH
no aurora-whisper-lab container exists; no /srv/homelab/data/whisper/lab staging dir
```

Steps 3–5 have not started, production is unchanged, and the corpus is byte-intact. The
one caveat for the next session is **M-5 + C-1**: Step 7's live acceptance path
(G-D4 canary, real devices) is currently unavailable.

### ER-1-C1 proved itself in production during this outage

Worth recording as gate evidence. At 01:19 CEST — 69 minutes after Zigbee2MQTT died — two
`ha_call_service` writes were issued against the printer:

```
2026-07-27T23:19:34Z  switch turn_on switch.impresora_3d
                      allowed=True  rc=applied_unverified  verified=False  state_after=unavailable
2026-07-27T23:20:00Z  switch turn_on impresora_3d          ← via alias
                      allowed=True  rc=applied_unverified  verified=False  state_after=unavailable
```

Before ER-1.4b both would have returned `result_code: "ok"` and Aurora would have told the
operator the printer was on. Instead the write failed **honestly**, against a real
unplanned fault the design was never rehearsed against. Compare the same entity earlier the
same day, while Zigbee was healthy: `rc=ok, verified=True, state_after=on`.

This is exactly the failure class ER-1 was built for, and it worked unprompted.

---

## 7. Prioritized remediation plan

Ordered by risk-reduction per unit of change. Every item is proposed only —
**nothing here was executed.** Stability first: P0 is a single restart, P1 is
mostly documentation and file capture, and no item recreates a container.

### P0 — Tonight (restore service)

| # | Action | Finding | Approval |
|---|---|---|---|
| 1 | `docker start zigbee2mqtt`; verify `switch.impresora_3d` and `cover.toldo` leave `unavailable` | C-1 | Service start |
| 2 | Confirm no restic process is running, then `restic unlock`; run one manual `forget --prune`; confirm the retention shape | H-1 | Root command |

Both are small, reversible, and each closes an active degradation.

### P1 — This week (stop the bleeding; documentation-only, zero production risk)

| # | Action | Finding |
|---|---|---|
| 3 | Capture every unmanaged container's live config into version-controlled compose files under `03_services/`, generated from `docker inspect`. **Write files to match reality; do not recreate anything.** Start with `ai-local` | H-3, H-4 |
| 4 | Record the H-4 redeploy hazard in `CURRENT_STATE.md` so no session redeploys the Portainer AI stack before the definition is corrected | H-4 |
| 5 | Extend `bin/backup-probe` to consume the backup script's exit status, not only snapshot age — apply the E2-a fail-loud lesson to the backup path | H-1 |
| 6 | Add the Portainer volume, `/etc/cron.d/aurora-signals` and the openedai voice map to backup `PATHS`; decide the secrets-backup approach deliberately | H-2 |
| 7 | Reconcile the triad: M-3 (`system_status` v0.3.0), M-5 (voice ACL), L-1, L-2, L-3, L-4, L-5, L-11 | drift block |
| 8 | Push `2a185cb1` and note the §9/§12 correction in the next F6.1 log — never by rewriting the handoff | M-2 |

### P2 — Next two weeks (security posture; needs a maintenance window)

| # | Action | Finding |
|---|---|---|
| 9 | Decide and document the LAN trust posture in `06_security/security_posture.md` — this decision gates 10–13 | H-8 |
| 10 | Bind Ollama to loopback or drop the host publication | H-5 |
| 11 | Retire `homelab-tools.service` after confirming no consumer; otherwise bind to `127.0.0.1` | H-6 |
| 12 | Rotate the Guardian Cloud tunnel token, move it to `.secrets` with `env_file`, `chmod 0600` — **rotation first**, since old snapshots retain the value | H-7 |
| 13 | Disable SSH password authentication after verifying key access from every device | M-9 |
| 14 | Patch `docker-ce` / `containerd.io` in a planned window with a rollback plan | M-6 |

### P3 — Backlog (schedule deliberately)

| # | Action | Finding |
|---|---|---|
| 15 | Design minutes-scale alerting in Home Assistant — container-down, backup-stale, context-stale, coordinator-missing. **Design decision, not a quick fix** | M-1 |
| 16 | Harden the Zigbee coordinator against USB re-enumeration: dedicated port off the hot-plug hub, plus a udev-triggered recovery path | C-1 (structural) |
| 17 | Pin all production images to digests inside the P1 captured definitions | M-7 |
| 18 | Repo hygiene: untrack `ai-tools/venv/` and `openwebui-tools/tmp/`; extend `.gitignore` | M-4 |
| 19 | Reclaim ~33 GB: Voice Lab images not needed for Round 2, plus build cache | M-8 |
| 20 | Schedule R-D-13 (STT shim migration) as a distinct F-6 sub-phase **after** F6.1 closes — it is a second variable and must never enter F6.1 under D-F6-1 | M-10 |
| 21 | Decide retention for the ~2.5 GB pre-sanitization repository copies | L-6 |
| 22 | Fix the restic staging path so parent-snapshot matching works | L-9 |
| 23 | Clean stale NPM hosts; resolve HA Cast/DLNA integration noise | L-7, L-8 |

---

## 8. Cross-cutting observations

**The documentation is unusually accurate, and its errors cluster in one place.** Every
architectural decision (D-01…D-35, AD-*, D-ER-*, INV-*) that could be checked against the
running system held. The drift is concentrated in *operational status* — versions, counts,
ACL contents, sizes — which is exactly the class `PROJECT_RULES` → *Transient Operational
Status* was written to govern. The rule is right; it is being applied to the ROADMAP more
consistently than to `CURRENT_STATE.md`, which is the declared source of truth (M-3 and
M-5 are both cases where the ROADMAP is correct and `CURRENT_STATE.md` is not).

**Verification discipline is strong where a gate exists, and absent where none does.**
Everything with a gate — tool hashes, projection freshness, the ER-1 write path, the F6.1
corpus — verified perfectly. Everything without one — backup retention, the exposure ACL,
the stored stack definitions, the Zigbee coordinator — drifted silently. The differentiator
is not care; it is whether something checks.

**The single largest structural risk is not any one finding — it is that the platform's
declarative definition is incomplete (H-3/H-4).** Aurora's *logic* is exemplary:
version-controlled, hash-stamped, gate-validated, reproducible. Aurora's *substrate* is
not: eight of seventeen containers exist only as running processes. The AI system is
recoverable; the machine it runs on is not.

**Awareness is not monitoring, and the gap has now cost something real.** Phase F built a
genuinely good awareness layer, and it was never intended to page anyone. But nothing else
does either — so a coordinator failure at 00:10 was still invisible at 02:50, and the
system's own artifacts asserted `17/17 running` throughout. This is the highest-value
architectural item in the backlog (M-1).

---

## 9. Audit method and limits

**Read-only.** No container was started, stopped or recreated; no file in the repository or
in `/srv/homelab` was modified; no commit, push or tag. One helper container
(`alpine:latest`, `--rm`, read-only mount) was run to read the Portainer volume, which
`diego` cannot read directly. Live HA queries were `GET` only. `emit-entity-projection
--check` is a read-only freshness check by design (ER-1.3, D-ER-5).

**Limits.**
- `diego` has no passwordless sudo, so `iptables`/`nft` rules, `/etc/restic/`, the restic
  repository contents and `dmesg` could not be read directly. Firewall enforcement (H-8) is
  inferred from `ufw.conf` plus observed LAN reachability, not from the rule set.
- Restic snapshot count and repository size could not be enumerated; H-1's impact is
  therefore assessed from the log evidence and dedup rates, not a snapshot listing.
- The Zigbee2MQTT non-restart mechanism is stated as a hypothesis; confirming it needs the
  Docker daemon log (root).
- The 04:15 awareness cycle had not yet run for 2026-07-28 at audit time, so the artifacts
  inspected are the 2026-07-27 generation (~22 h old, within the ≤26 h AD-10 window).
- Two listeners (`*:18555`, `127.0.0.1:18554`) could not be attributed to a process without
  root; neither answered HTTP. Not raised as findings.
