# Operational Drift Reconciliation — 2026-10-20

**Date:** 2026-10-20 (observations taken 00:30–01:05 CEST)
**Type:** Dated reconciliation record. Read-only fact reconstruction, taken before the Location
Portability work and before S-7. Not a remediation item and not a phase.
**Production changed by this document:** **no.** No container, network, Docker, Zigbee2MQTT,
Mosquitto, Home Assistant, Cloudflare, Tailscale, backup, retention or cron change. No host
reboot. A pending `/var/run/reboot-required` (dated 2026-10-10) was observed and **not** acted on.
**Commands executed:** read-only only — `docker ps` / `docker inspect` / `docker network
inspect` / `docker logs`, `journalctl` (per boot, kernel, `dockerd`), `sha256sum`, file reads,
`git` read commands, two unauthenticated `HEAD`-style `GET`s against the public hostnames, and
authenticated read-only `GET /api/states` / `GET /api/history` against Home Assistant. The only
change in the working tree before this record was the operator-approved file restore in §6.
**Result:** five drift items reconciled against observed reality:
- four OPERATOR-REPORTED unclean stops, three of them also evidenced in the journal;
- a runtime inventory larger than documented;
- two hosted services absent from the inventory;
- a backup-coverage discrepancy;
- one restored documentation file.

A fifth C-1 recurrence was found along the way and has its own record:
[`2026-10-20_zigbee2mqtt_c1_fifth_recurrence.md`](2026-10-20_zigbee2mqtt_c1_fifth_recurrence.md).
**I-10 stays CLOSED. C-1, S-9, M-1, M-A, M-D and S-10 are unchanged. S-7 and S-8 are not
started.**

> Dated record. States what was true on 2026-10-20 and is **not** rewritten as the situation
> advances (`PROJECT_RULES.md` → *Historical Documentation*). No earlier record is modified; this
> document is the correction.

---

## 1. Why this reconciliation was opened

A read-only Location Portability audit on 2026-10-20 found that the triad no longer matched the
running system. The operator directed a documentation-only reconciliation **before** any
Location Portability documentation is written.

---

## 2. Clean Host Shutdown — four operator-reported unclean stops after 2026-09-18

### 2.1 OBSERVED

Method as in the 2026-09-18 record §4.2: per-boot journal matches of
`systemd-shutdown|Reached target.*(Power-Off|Reboot|System Shutdown)|Powering off|Rebooting`,
plus `Power key pressed`. The second source is Zigbee2MQTT's per-session logs: a clean stop ends
with `Stopped Zigbee2MQTT`, and an abrupt one ends without it, sometimes with trailing NUL bytes.

| Boot | Started (CEST) | Last journal entry (CEST) | Shutdown markers | Power key | Zigbee2MQTT session end |
|---|---|---|---|---|---|
| *(not visible)* | — | — | — | — | `2026-09-02.13-36-54`: last line **2026-09-22 10:57:08**, no stop line |
| −4 | 2026-09-22 10:57:58 | **2026-09-27 23:40:01** | **0** | 0 | last line 23:40:44, no stop line, NUL tail |
| −3 | 2026-09-27 23:41:18 | **2026-09-27 23:50:15** | **0** | 0 | last line 23:51:24, no stop line, NUL tail |
| −2 | 2026-09-27 23:51:55 | 2026-09-29 01:45:18 | **3** | 1 | `Stopped Zigbee2MQTT`, `code=0` — **clean** |
| −1 | 2026-09-29 01:45:43 | **2026-10-07 22:10:18** | **0** | 0 | ended by C-1 on 2026-09-30, see the fifth-recurrence record |
| 0 | 2026-10-07 23:55:08 | *(current)* | — | — | running |

- **2026-09-22 ~10:57 — the host stop itself is NOT observed.** The evidence boundary:
  - **OBSERVED:** the Zigbee2MQTT session `2026-09-02.13-36-54` ended at 10:57:08 **without a
    graceful-stop indication**.
  - **OBSERVED:** the next Zigbee2MQTT session began at 10:58:20. The earliest visible journal
    entry, 10:57:58, is the start of the next boot.
  - **NOT AVAILABLE:** the journal of the boot that ended then cannot be read from the
    inspection context used here (§2.3). Whether that boot ended with or without shutdown markers
    is therefore **not established technically**.
  - The unclean character and the cause of this event rest on the **operator's report** (§2.2),
    not on technical evidence.
- **2026-09-27 ~23:40, 23:50 and 2026-10-07 22:10** are OBSERVED in the journal, each with zero
  shutdown markers.
- **2026-09-29 01:45 is the positive control.** Shutdown markers, a power-key event, and a
  graceful `code=0` Zigbee2MQTT stop are all present.
- Where a Zigbee2MQTT session outlives the boot's last journal entry, entries that the journal
  never flushed are the likely reason (INFERRED). This changes no classification.

### 2.2 OPERATOR-REPORTED

The operator states that **all four** unclean stops were caused by the operator:

- 2026-09-22 ~10:57;
- 2026-09-27 ~23:40;
- 2026-09-27 23:50;
- 2026-10-07 22:10.

**The mechanism was not stated, and it is not inferred here.** For the three journal-visible stops,
the journal shows that no OS-initiated shutdown occurred. It does **not** show what physically
stopped the host. For 2026-09-22 there is no journal evidence either way (§2.1). That event is
documented as operator-caused **on the strength of this OPERATOR-REPORTED statement**, not on
technical evidence.

### 2.3 Journal visibility — a limit, not a finding

On 2026-10-20 the non-root `journalctl --list-boots` view starts at **2026-09-22 10:57:58**
(five boots). The 2026-09-18 record counted 31 boots back to 2026-05-19. Journal files dated
from May are still present on disk (1.5 GB total). **No loss of journal data is claimed.** The
difference may come from reader access, and it was not investigated. The 2026-09-18 → 2026-09-22
interval cannot be checked from this view. The Zigbee2MQTT session `2026-09-02.13-36-54`
continues unbroken across it, which indicates no host stop in that interval (INFERRED).

### 2.4 Status

- **I-10 stays CLOSED as a host-fault finding.** Its reopen condition is an unclean stop the
  operator did **not** cause. Every unclean stop identified here is OPERATOR-REPORTED as
  operator-caused, so the condition is not met.
- **Procedural / documentation drift under `PROJECT_RULES.md` → *Clean Host Shutdown*.**
  - Rule 5 requires every exceptional forced stop to be documented in `09_logs/` with its date and
    reason. None of these four was recorded at the time. This section is the late record.
  - **Reason: not stated.**
  - Whether any of the four was a genuine emergency (rule 4) is not stated either.

---

## 3. Runtime inventory

**OBSERVED 2026-10-20 01:04 CEST: 20 containers, all `running`, none stopped.** At 00:30 there
were 19. The twentieth, `qr-public-edge`, was **created at 01:03:30 during this
reconciliation**. It carries the QR project's compose label (`generador-qr`, service
`public-edge`) and belongs to the QR deployment that is in progress (§5). This reconciliation
did not create it and did not touch it.

| Group | Containers | Count | Documented before |
|---|---|---|---|
| Captured at I-3 (`03_services/`) | `openwebui`, `qdrant`, `ollama`, `aurora-whisper`, `aurora-piper`, `aurora-wakeword`, `aurora-whisper-http`, `aurora-piper-http`, `portainer`, `nginx-proxy-manager`, `homeassistant`, `zigbee2mqtt`, `mosquitto`, `ollama-proxy` | 14 | yes |
| Hosted, outside I-3 scope | `guardian-web`, `cloudflared`, `cloudflared-amarolab` | 3 | yes |
| **Company website** | `amarolab-portfolio` | 1 | **no** |
| **QR/NFC application — in deployment** | components observed at 01:04: `qr-amarolab`, `qr-public-edge` | 2 at 01:04 | **no** |

The documented "17/17" was the first two groups. **Both newer services are intentional
(operator-confirmed), not unknown or accidental**, and their absence from the inventory is
documentation drift.

**The total of 20 is a timestamped observation, not a target.** The QR deployment is changing,
and its component set is expected to change with it. AMAROLAB documentation does **not** track
every QR deployment container. It also assumes **no** fixed number of QR containers on the
host.

**D-F6-1 holds.** `aurora-whisper` keeps the creation time `2026-06-17T14:21:14Z` and image
`sha256:966e1b09…`. Only `StartedAt` moved, to the 2026-10-07 boot.

### 3.1 Docker networks not recorded in `03_services/README.md`

| Network | Subnet | Created (CEST) | Members at 01:04 |
|---|---|---|---|
| `html_default` | 172.21.0.0/16 | 2026-05-01 | none |
| `guardian-cloud_default` | 172.22.0.0/16 | 2026-05-01 | `guardian-web` |
| `cloudflared_default` | 172.23.0.0/16 | 2026-05-01 | none |
| `cloudflare-net` | 172.24.0.0/16 | 2026-05-01 | `cloudflared`, `guardian-web` |
| `voicelab_net` | 172.25.0.0/16 | 2026-07-26 | none |
| `generador-qr_qr-interna` | 172.26.0.0/16 | 2026-10-19 | `qr-amarolab`, `qr-public-edge` |
| `qr-edge` (internal) | 172.27.0.0/16 | **2026-10-20 01:03** | `qr-public-edge` |

**Relevant to R-I3-1.** At 00:30 `172.27.0.0/16` belonged to a network named `qr-g7_test`. By
01:04 that network was gone and `qr-edge` held the same subnet. This is direct evidence that
subnets are assigned by creation order **and reused**. Home Assistant's `trusted_proxies` still
depends on `ai-local_default` keeping `172.18.0.0/16`.

---

## 4. `amarolab-portfolio` — the Amarolab company website

Intentional production infrastructure (operator-confirmed).

- **What it serves:** the site's canonical URL is `https://amarolab.es/`, and it answered **200**
  through Cloudflare on 2026-10-20.
- **Image:** `nginx:alpine`. The content directory `/home/diego/webs/amarolab-portfolio` is
  bind-mounted **read-only**. The content was last changed 2026-10-08.
- **Network:** only `ai-local_default`, with no published port. Every request in the last 2000
  access-log lines comes from the `cloudflared-amarolab` container. The site is therefore served
  through the AMAROLAB tunnel by Docker DNS (OBSERVED). The tunnel ingress itself is remote,
  token-managed configuration and could not be read (§7).
- **Created** 2026-09-25 09:36 CEST, `restart: unless-stopped`.
- **Deployment definition: NOT FOUND.**
  - The container's compose label names `/home/diego/webs/amarolab-portfolio/docker-compose.yml`,
    and **no such file exists**.
  - The content directory is not a git repository.
  - No source repository was found under `/home/diego`.
  - The running container can be inspected, but **nothing found reproduces it**. This is the gap
    I-3 closed for other services.
  - **Recorded, not fixed. No remediation identifier is assigned**, following the R-I3-1…7 /
    F-S1-1 precedent.
- **Backup:** its content directory sits under `/home/diego/webs`, which is in the restic path
  set. Covered **by path configuration**, but snapshot contents were not verified (§6.2). No
  restore has been tested.

---

## 5. `qr-amarolab` — the Amarolab QR/NFC application, in deployment

Intentional infrastructure **hosted on the UM790** and **currently being deployed**
(operator-confirmed). **The QR project's own repository is authoritative for its detailed
application and deployment state, including its topology.** This section records:
- the runtime components observed at the reconciliation timestamp;
- the infrastructure dependencies and risks AMAROLAB can observe.

It does not describe the deployment's final shape.

- **`qr-amarolab`.**
  - Created 2026-10-19 14:20 CEST, `healthy`, image `qr-amarolab:v1.0.0-rc.1` (built locally).
  - Compose project `generador-qr`; its definition lives in the QR project's private repository
    under `/home/diego/webs/generador-qr`.
  - Published on **`127.0.0.1:18000` only** (loopback). Its network is `generador-qr_qr-interna`.
    It is **not** on `ai-local_default`.
  - Runs as a non-root user.
- **`qr-public-edge`.** Created 2026-10-20 01:03 CEST (§3), with no published port. Its
  networks are `generador-qr_qr-interna` and the internal `qr-edge`.
- **Public publication: NOT established.**
  - `https://qr.amarolab.es/` returned **HTTP 521** from the Cloudflare edge at about 00:35 and
    again at 01:04.
  - The QR project's own current-state document says that public ingress, DNS and the reverse
    proxy have not been done, and that the service is reachable from the host only.
  - **This record does not describe `qr.amarolab.es` as published.**
- **Data.**
  - The production SQLite database is at `/srv/homelab/data/qr-amarolab` (NVMe).
  - The application's own backups go to `/mnt/storage/backups/qr-amarolab` (USB HDD).
- **Backup and restore state.**
  - **Neither path is in the AMAROLAB restic path set** (§6.1).
  - Per the QR project's own documentation:
    - backup and restore are implemented and exercised outside production;
    - one manual production backup was created and verified;
    - **there is no backup scheduler**;
    - **no restore against the production database has been tested.**
  - **Restore is not validated.**
- **Storage dependency (preserved from the portability audit).** `/mnt/storage` is mounted
  `nofail`, and its mount point exists on the root filesystem. If the USB disk is absent, writes
  to the backup path would land on the internal disk without warning. The QR project records the
  same risk as open.

---

## 6. Backups and documentation recovery

### 6.1 Path configuration — OBSERVED

- **The backup mechanism is unchanged since I-8.**
  - The installed `homelab-backup.sh` is `330df064…` and the cron file is `976aa694…`.
  - Both are byte-identical to the tracked copies under `07_operations/backups/`.
- **Path set.** It still holds the 16 static paths:
  - `/home/diego/webs` is in it;
  - **no path for `qr-amarolab`'s data or backups is in it.**

### 6.2 Discrepancy — VERIFICATION REQUIRED

- **What the configuration implies.** `/home/diego/webs` is backed up as a whole. By file name,
  the tree contains **secret-bearing files**: an environment file in the QR project directory, and
  the compose files of both Cloudflare tunnels. Per R-01, one of those compose files has held a
  tunnel token in plaintext. The script's exclusions do not exclude such files. So the path
  configuration implies restic **would read them if present at backup time**.
- **What was not verified.**
  - **Whether any snapshot actually contains them** was not checked. That needs root and a restic
    listing, and no restic command was run.
  - **No secret value was read** for this record.
- **Why it matters.** It contrasts with the framing of **M-D**, which lists secret stores as
  excluded from the backup. **This record does not state that secrets exist inside snapshots.** It
  records a **discrepancy between path configuration and the M-D framing**, to be verified by the
  operator.
- **M-D is unchanged. No backup, retention or prune action was taken.**

### 6.3 Documentation recovery — `zigbee2mqtt_first_devices.md`

- **What was found.** On 2026-10-20 the working tree was missing the tracked file
  `03_services/zigbee-stack/zigbee2mqtt_first_devices.md`, which two live documents link to.
- **Evidence about the deletion.**
  - The directory's mtime/ctime is **2026-09-25 21:35:18 CEST**, consistent with the deletion
    time.
  - No commit removes the file, the reflog shows no git operation in that window, and no shell
    history or assistant session record references it.
  - A remote editor server session started about 90 seconds earlier. That is **a temporal
    coincidence only — the deletion is not attributed to any person, tool or session.**
  - **Cause: UNKNOWN.**
- **Restore.**
  - On 2026-10-20 00:50, with operator approval, it was restored with
    `git restore --worktree -- <path>`.
  - The source was the index, which held the HEAD blob `56230907…`. The result is byte-identical
    to HEAD (sha256 `153febc2…`). Nothing was staged.
  - **This was documentation recovery, not a Zigbee repair.** No container, configuration or
    device was touched.

---

## 7. Observed, not reconciled

- **The AMAROLAB tunnel's current ingress cannot be read from the host.**
  - `docker logs cloudflared-amarolab` returns nothing after 2026-07-21, although the container
    restarted on 2026-10-07. This fits the `docker logs` caveat in the 2026-08-31 record §6. It is
    **not** evidence about the tunnel's behaviour.
  - The last ingress the logs show (2026-07-20) lists `ha.amarolab.es` and `ai.amarolab.es` only.
    The apex site is served now (§4), so the ingress has changed since then.
  - `CURRENT_STATE.md` → *Cloudflare* therefore states the hostname targets as **last logged**,
    pending a read of the Cloudflare dashboard.
- **No new LAN-reachable listener.** Portfolio publishes no port, and `qr-amarolab` is bound to
  loopback. The S-1 conformance table is unaffected.

---

## 8. What is unchanged

- **C-1** — it now has five recorded occurrences. **S-9 Open, M-1 Open, M-A Open.**
- **I-10 CLOSED** as a host-fault finding (§2.4).
- **M-D Open**, unchanged (§6.2).
- **S-10** Open and unapproved. Retention is still `--dry-run`. The anchor `42506e44` was not
  touched.
- **S-7 not started. S-8 not started, and still gated on S-7.**
- **Location Portability: not started.**

---

## 9. Documentation changed in the same change

- New: this record, and
  [`2026-10-20_zigbee2mqtt_c1_fifth_recurrence.md`](2026-10-20_zigbee2mqtt_c1_fifth_recurrence.md).
- `00_overview/CURRENT_STATE.md` — container count and Zigbee2MQTT status (both stale since the
  fifth recurrence), the internal *Last updated* header (stale since 2026-08-19), *Cloudflare*
  (apex site; QR not published), and *Backups* (QR outside coverage; §6.2 discrepancy).
- `00_overview/ROADMAP.md` — *Last updated*, the I-10 row, the S-9 and M-A rows, and a pointer
  to the fifth occurrence.
- `00_overview/AMAROLAB_HANDOFF.md` — *Last updated*, the superseded Zigbee status paragraph,
  and standing constraint 4.
- `03_services/README.md` — hosted services that are not captured, and the full network list.

---

## 10. Method and limits

- **Operator statements are not converted into evidence.** OBSERVED means journal, log, inspect
  or file evidence. OPERATOR-REPORTED means the operator's statement.
- **The QR deployment was changing during the observation window** (§3). Counts are given with
  their timestamps.
- **What was not read.** No secret value was read. Environment variable *names* were read where
  needed, never their values.

---

## 11. Git gate

Documentation only. **Not committed, not pushed.** Both require explicit operator approval
immediately before the command (`PROJECT_RULES.md` → *Operator Git Approval*).
`ai-stack/ingest/conf/corpora.yaml` is out of scope and is not staged.

**STOP at git gate.**
