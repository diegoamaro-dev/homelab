# 14 — Security risks

Risks are scored on **impact × likelihood** in the context of this homelab:
single user, behind a router with no inbound forwarding, accessible from the
LAN and from a tailnet of 6 personal devices. Severity assumes the LAN /
Tailscale boundary holds. Several items become **Critical** if that
assumption is ever broken (e.g. a guest device on the LAN, or a Tailscale
account compromise).

Legend: 🔴 high · 🟠 medium · 🟡 low · ℹ️ informational

---

## 🔴 R-01 — Cloudflare tunnel token committed in plaintext

**Where:** [`/home/diego/webs/cloudflared/docker-compose.yml`](../webs/cloudflared/docker-compose.yml)

```yaml
environment:
  - TUNNEL_TOKEN=<REDACTED-CLOUDFLARE-TUNNEL-TOKEN>
```

The token decodes to `{accountTag, tunnelID, tunnelSecret}`. Anyone with the
file (including any future Git commit that includes this directory) can take
over the tunnel and re-publish it pointing at arbitrary upstreams.

**Fix direction:** move the token to a `.env` file referenced by
`env_file:` in compose, add `.env` to `.gitignore`, rotate the token in
Cloudflare Zero Trust so the current value is invalidated.

---

## 🔴 R-02 — Unauthenticated Flask "homelab-tools" API on `0.0.0.0:5050`

**Where:** `homelab-tools.service` →
[`/home/diego/homelab/ai-tools/docker_status.py`](../homelab/ai-tools/docker_status.py)

- Endpoints: `GET /docker/containers`, `GET /docker/logs?container=<name>&lines=<n>`
- Allowlist of containers: `openwebui, ollama, qdrant, homeassistant,
  nginx-proxy-manager, portainer`.
- No auth, no TLS, no rate-limit, runs under the Flask dev server.
- Bound to **all interfaces** including `tailscale0`.

Container logs frequently contain secrets, tokens, or session identifiers.
A LAN / tailnet attacker can scrape them at will.

**Fix direction:** bind to `127.0.0.1`, put it behind NPM with auth, or kill
the service entirely (Portainer already exposes the same data, gated).

---

## 🔴 R-03 — NPM private key + admin DB readable to non-root host users

**Where:** [`/srv/homelab/data/npm/keys.json`](../../srv/homelab/data/npm/keys.json) (mode `0644`,
world-readable) and `/srv/homelab/data/npm/database.sqlite`.

`keys.json` contains the RSA-2048 keypair NPM uses for JWT signing. Anyone
with read access can forge admin sessions. The file is owned by `root` but
its mode is `0644`. SQLite DB is `0644` too.

**Fix direction:** `chmod 600` and ensure ownership stays `root:root`.
Better: move to a Docker secret or out of the bind-mount entirely.

---

## ✅ R-04 — Mosquitto crash-looping (RESOLVED 2026-06-13)

**Where:** `mosquitto` container, every ~60 s:

```
Unable to open config file '/mosquitto/config/mosquitto.conf'
```

The bind-mount directory exists at
`/home/diego/homelab/03_services/zigbee-stack/mosquitto/config/` but is empty.
Zigbee2MQTT is up and (per its config) tries to publish to
`mqtt://localhost:1883` — every publish is failing silently.

**Impact:** any Zigbee device traffic is dropped. Once HA's MQTT integration
is wired up, it would also fail. Not directly a security risk, but a service
in an unrecoverable loop is a tail-risk for the rest of the host (log
volume, restart noise).

**Resolution:** restored `mosquitto.conf` with anonymous listener on
`:1883`, fixed `…/mosquitto/log` host-side ownership to `1883:1883`, and
repointed `zigbee2mqtt`'s `configuration.yaml` to
`mqtt://mosquitto:1883`. End-to-end MQTT round trip validated with a
fresh `mosquitto_pub` probe on `zigbee-stack_default`. Details in
[phase2-remediation/01-critical.md → Phase 0 application](phase2-remediation/01-critical.md#phase-0-application-2026-06-13).

---

## ✅ R-05 — Open WebUI `WEBUI_SECRET_KEY` is empty (RESOLVED 2026-06-13)

Container env shows `WEBUI_SECRET_KEY=` (empty). Open WebUI then generates a
fresh signing key at boot, which means every container restart invalidates
all sessions and any user-created API keys. It also makes session-replay
debugging harder.

**Fix direction:** generate a long random value, store in a `.env` file
referenced by the (not yet existing) compose file for Open WebUI.

**Phase 0 status (2026-06-13):** 64-hex value generated and stored at
`/home/diego/homelab/ai-stack/.env` (`0600`). `openwebui` recreated with
the value injected via `-e WEBUI_SECRET_KEY=…`. Stability verified by
`sha256` of the value being identical before and after a `docker
restart`. Details in
[phase2-remediation/03-medium.md → Phase 0 application](phase2-remediation/03-medium.md#phase-0-application-2026-06-13).

---

## ✅ R-06 — Open WebUI has read/write access to the host Docker socket (RESOLVED 2026-06-13)

Mount: `/var/run/docker.sock` → `/var/run/docker.sock` (rw).

Open WebUI's Tools / Functions / Pipelines features can execute commands
inside containers, and with the socket attached they can `docker run`
arbitrary containers — i.e., trivially get host root.

**Fix direction:** remove the socket mount unless a current feature needs
it; if it must stay, pair with Open WebUI's `auth` enabled (already on) and
keep `enable_signup` off (already on). Consider a socket proxy
(`tecnativa/docker-socket-proxy`) to limit which API verbs are exposed.

**Phase 0 status (2026-06-13):** Socket mount **removed**. Open WebUI
recreated without `/var/run/docker.sock`; pre-flight confirmed no
in-container process was holding it open. The 3 user tools in the DB
were inspected — none use the socket; the two `docker_*` tools call
the LAN Flask `homelab-tools` API and are unaffected. Details in
[phase2-remediation/02-high.md → Phase 0 application](phase2-remediation/02-high.md#phase-0-application-2026-06-13).

---

## 🟠 R-07 — Ollama and Qdrant expose unauthenticated APIs on LAN/tailnet  *(Qdrant half ✅ resolved 2026-06-13; Ollama still open)*

Both listen on `0.0.0.0` with no API key. Anyone on the LAN or tailnet can:

- Ollama 11434: list / pull / delete models, chat (CPU spike), run arbitrary
  prompts including those that hit RAG content.
- Qdrant 6333: read / write / drop collections, including the live
  Open WebUI vector store.

**Fix direction:** either bind to `127.0.0.1` (and let Open WebUI keep the
existing container-network path), or stand up NPM with an auth layer. For
Qdrant, set `QDRANT__SERVICE__API_KEY` and configure Open WebUI to send it.

**Phase 0 status (2026-06-13):**

- ✅ Qdrant `QDRANT__SERVICE__API_KEY` set; Open WebUI passes
  `QDRANT_API_KEY` on every request; unauthenticated probes return
  401. See [phase2-remediation/02-high.md → Phase 0 application](phase2-remediation/02-high.md#phase-0-application-2026-06-13).
- ⏭ Port rebind to `127.0.0.1` deferred until Phase 3 / R-14 (avoids
  a second recreate of the same container).
- ⏭ Ollama untouched; still 0.0.0.0:11434 unauthenticated.

---

## 🟠 R-08 — WebDAV on Apache port 8088 — HTTP only, Basic auth

`/etc/apache2/sites-enabled/webdav.conf` uses `AuthType Basic` with no
`<Location>`-level `SSLRequireSSL`. Credentials traverse the LAN/tailnet
in plain text on every request.

**Fix direction:** turn off the vhost if unused; if used, front it with NPM
TLS, or move it behind Tailscale Funnel / Cloudflare Access. Confirm whether
the WebDAV target `/var/www/webdav` actually has live content first.

---

## 🟠 R-09 — `rpcbind` (portmapper) listening on `0.0.0.0:111`

`rpcbind` is up (`rpcinfo -p` confirms only portmapper itself registered, no
NFS). It serves no purpose on this host but historically exposes a UDP
amplification surface and an information-disclosure vector.

**Fix direction:** `systemctl disable --now rpcbind.service
rpcbind.socket` and remove `rpcbind` / `nfs-common` if not needed.

---

## 🟠 R-10 — No host firewall

UFW is installed but inactive (its status is only readable as root, but no
`ufw` interface or rules are visible and no DROP/REJECT chains are obvious
from listening-socket coverage). The host relies entirely on the router /
Tailscale ACLs.

**Fix direction:** enable UFW with a default-deny inbound policy and allow
only what the LAN / tailnet actually need (22, 80, 443, 8123, 3000, 445,
plus 111/137/138 if Samba browse must stay).

---

## 🟠 R-11 — Three months of pending image updates

Image pull dates from 2026-02-09 to 2026-04-15. Open WebUI, Home Assistant,
Ollama, and Mosquitto in particular ship security and feature fixes weekly.

**Fix direction:** Watchtower or a `cron`-driven `docker compose pull && up`
on a per-stack basis. If automation is too aggressive, at minimum schedule
a monthly manual review of new releases.

---

## ✅ R-12 — No backups (RESOLVED 2026-06-13)

Covered in detail in [12-backups.md](12-backups.md). Severity stays "low"
only because the loss surface here is small (mostly recoverable from
external sources except the Zigbee coordinator DB and HA history).

**Applied as the first Phase 0 prerequisite:** nightly restic to
`/mnt/storage/backups/restic`, retention 7d/4w/6m, first snapshot
`cc73b4fd`. See [12-backups.md → Phase 0 application](12-backups.md#phase-0-application-2026-06-13)
for the install map and validation commands.

---

## 🟡 R-13 — Apache and NPM contending for port 80

Both bind `tcp/80`. Today they co-exist because Apache's `000-default.conf`
inherits `ServerName 127.0.1.1` and only binds the loopback alias. Any
configuration change to Apache (e.g. `ServerName *` or a new vhost on
`*:80`) will collide with NPM and break public HTTP.

**Fix direction:** decide which one owns port 80. NPM is the documented
"central entry point" goal in `00_overview/current-status.md`; the Apache
default vhost is unused. Disable `000-default.conf`.

---

## 🟡 R-14 — Eight Docker containers have no checked-in declarations

Only `cloudflared` and `guardian-web` have `docker-compose.yml` files on
disk. The other 8 containers (including Open WebUI, Ollama, Qdrant, Home
Assistant, NPM, Portainer, Zigbee2MQTT, Mosquitto) were created with
ad-hoc `docker run` and would have to be rebuilt from shell history.

**Fix direction:** capture each container's `docker inspect` into a
compose file under `/srv/homelab/compose/` (the directory already exists
for this purpose).

---

## 🟡 R-15 — Open WebUI ships an obsolete local Chroma store

`/srv/homelab/data/openwebui/vector_db/chroma.sqlite3` is left over from
before `VECTOR_DB=qdrant` was set. Not actively read, but takes disk space
and confuses future debugging.

---

## 🟡 R-16 — Multiple Docker bridges, two are stale

`html_default` and `cloudflared_default` networks have no containers and
the bridges are DOWN. `bridge` (default) only carries Portainer. No
functional harm; just `ip a` noise and IP-range allocation pressure if more
networks are added.

---

## 🟡 R-17 — `diego` is in the `docker` group

Membership confers effective root via `docker run -v /:/host …`. Standard
on a single-admin host but worth being explicit about — any future second
account should not get it.

---

## 🟡 R-18 — Desktop services on a server

`gdm`, `gnome-remote-desktop`, `cups`, `cups-browsed`, `bluetoothd`,
`ModemManager`, `colord`, `power-profiles-daemon` and friends are all
running. Each is one more attack surface, one more thing logging at boot,
and one more thing that can wedge during a crash recovery.

**Fix direction:** if the box is truly headless on the network, switch to
a server install or disable `gdm.target` and the related units.

---

## 🟡 R-19 — Telemetry endpoints reachable without auth

Qdrant `/metrics` and `/telemetry` return collection counts and timing info
unauthenticated. Combined with Ollama's `/api/tags`, an unauthenticated LAN
client gets a useful capability map of the AI stack.

---

## ℹ️ R-20 — System crashed on 2026-06-03

`last` and `home-assistant.log.fault` both show 2026-06-03 12:55 as a hard
reset. No kernel oops captured in the current journal window. Worth
correlating with `journalctl -b -1` (requires root) to identify the cause
before adding redundancy.

---

## Items considered and **not** treated as risks

- SSH on port 22 with no public Internet exposure (Tailscale + LAN only).
- Tailscale account hosting six personal devices (operationally correct).
- Home Assistant on host network (intentional — needed for mDNS
  discovery).
- `unattended-upgrades` enabled (good baseline; covers host packages only).
- Avahi mDNS exposure (intentional; required by Home Assistant cast/Thread
  integrations).
- Samba `[printers]` / `[print$]` entries (read-only stock shares; no
  printer attached).
