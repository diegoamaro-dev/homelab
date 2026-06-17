# HA ↔ Voice Stack — Network Topology Decision

- **Scope:** How the `homeassistant` container reaches
  the AURORA voice-stack Wyoming endpoints
  (`aurora-whisper:10300`, `aurora-piper:10200`,
  `aurora-wakeword:10400`) plus the Ollama
  conversation agent (`ollama:11434`) when D-1.5
  configures the HA Assist pipeline.
- **Status:** **Decision recorded; application
  deferred** to D-1.5 prep.
- **Author of record:** D-1.3 readiness assessment.
- **Companion docs:**
  [`pipeline-spec.md`](pipeline-spec.md),
  [`../wyoming/overview.md`](../wyoming/overview.md),
  [`../../../06_security/voice_privacy.md`](../../../06_security/voice_privacy.md),
  [`../../../04_ai_system/amarolab-v1/phase-d/04-security-and-permissions.md`](../../../04_ai_system/amarolab-v1/phase-d/04-security-and-permissions.md).

---

## 1. Problem statement

The HA Assist pipeline reaches its STT / TTS /
wake-word slots over the Wyoming protocol as
`host:port` pairs. The pipeline-spec lists those
endpoints by Docker DNS name
(`aurora-whisper:10300`, `aurora-piper:10200`,
`aurora-wakeword:10400`) — which assumes HA can
resolve those names.

Live state on 2026-06-17 says otherwise:

| Container | Network mode | Reachable from where |
|---|---|---|
| `homeassistant` | **`host`** (`NetworkMode = host`) | Host namespace; no Docker DNS for user-defined bridges |
| `aurora-whisper` | bridge `ai-local_default` (172.18.0.0/16) | other containers on `ai-local_default` |
| `aurora-piper` | bridge `ai-local_default` (172.18.0.6) | other containers on `ai-local_default` |
| `aurora-wakeword` *(not yet deployed)* | bridge `ai-local_default` (planned) | other containers on `ai-local_default` |
| `ollama` | bridge `ai-local_default` **and** host-published `:11434` | both |
| `mosquitto` | host-published `:1883` | both |

Verified by:

```
$ docker exec homeassistant getent hosts aurora-piper
   (returns nothing — confirms no DNS for ai-local_default names from HA)
$ docker inspect homeassistant --format '{{.HostConfig.NetworkMode}}'
host
```

So as it stands today, **`homeassistant` cannot
resolve `aurora-piper:10200` by name**, and the
pipeline-spec's slot URIs do not work unmodified.

---

## 2. Why HA runs in host mode

This is not a free choice. `--network host` is the
common HA deployment mode because:

- mDNS / SSDP / Bonjour broadcasts for device
  autodiscovery (HomeKit, AirPlay, Sonos, Plex,
  Spotify Connect, ESPHome, many Z-Wave/Zigbee
  gateways) require Layer-2 access to the host LAN.
  Bridged containers do not see those broadcast
  domains.
- HA's frontend reaches `localhost:11434` (Ollama)
  and `localhost:1883` (Mosquitto) directly through
  the host loopback — no extra config.
- A migration to bridge mode would have to either
  (a) move all those discovery integrations into
  separate add-ons / sidecars or (b) accept losing
  them.

The recommendation below treats HA's host network
mode as **architecturally load-bearing** and not
something to be reverted lightly.

---

## 3. Options under evaluation

### Option A — Attach HA to `ai-local_default`

Pull HA out of `host` mode, run it on the
`ai-local_default` bridge alongside Whisper / Piper /
wakeword. The pipeline-spec slot URIs work
unchanged because Docker DNS resolves the names.

| Priority | Assessment |
|---|---|
| No public exposure | ✅ — nothing published to the LAN |
| Minimal blast radius | ❌ — **breaks HA discovery integrations**; potentially breaks LAN-facing HA frontend (depends on whether the frontend needs LAN reachability) |
| Maintainability | ❌ — every future LAN-discovery integration has to be re-architected (per-device static config, ESPHome → MQTT bridge, etc.) |
| Docker DNS simplicity | ✅ — clean DNS-based addressing |
| HA Wyoming integration compatibility | ✅ — `aurora-piper:10200` works directly |

**Verdict:** Disqualified. The cost to HA's working
device-discovery surface is far higher than the
benefit of clean DNS for three new endpoints.

### Option B — Publish Wyoming ports on UM790, bind to loopback

Add `-p 127.0.0.1:<port>:<port>` to the docker run
of `aurora-whisper`, `aurora-piper`, and (at D-1.4)
`aurora-wakeword`. HA reaches them via
`127.0.0.1:10300` / `127.0.0.1:10200` /
`127.0.0.1:10400`.

Critical detail: **`127.0.0.1` binding, not `0.0.0.0`.**
The port is publishable to HA (which shares the host
namespace) **without** being reachable from the LAN.

| Priority | Assessment |
|---|---|
| No public exposure | ✅ — loopback binding; no LAN, no WAN. Stronger than the current posture of `mosquitto`/`ollama`, which are published on `0.0.0.0`. |
| Minimal blast radius | ✅ — only the voice-stack containers are recreated; bind-mounted voice caches survive; HA untouched; nothing else affected |
| Maintainability | ✅ — one extra flag per voice-stack container; HA Wyoming integration takes host+port, no DNS dependency |
| Docker DNS simplicity | ➖ — HA uses `127.0.0.1` instead of a DNS name. Trivial; loopback addressing is simpler than DNS for a host-local consumer. |
| HA Wyoming integration compatibility | ✅ — host + port input directly accepts `127.0.0.1` + port |
| Coexistence with Open WebUI consumers | ✅ — Open WebUI does **not** consume the Wyoming endpoints at all; it reaches the future HTTP shims on different ports (`aurora-whisper-http:8000/v1`, `aurora-piper-http:8001/v1`) over `ai-local_default`. The Wyoming endpoints (`10200`/`10300`/`10400`) have **HA as their sole consumer** once D-1.5 lands. Option B's loopback binding does not touch Open WebUI's path. |

**Side effects:**

- [`voice_privacy.md`](../../../06_security/voice_privacy.md)
  §4 currently states "No new host port is published
  by Phase D-1." That sentence will need a small
  clarification at D-1.5 prep: published to host
  loopback only, not to LAN. The privacy intent
  (no LAN/WAN exposure) is preserved.
- `aurora-whisper` and (today) `aurora-piper` were
  deployed without host publishing. Adopting Option B
  requires recreating both containers — bind-mounted
  caches preserve the model weights, so recreation
  cost is just container-level (a few seconds).

**Verdict:** **Recommended.**

### Option C — Direct bridge-IP access from host namespace

The `ai-local_default` bridge gateway is `172.18.0.1`,
host-reachable. HA in host mode can reach
`172.18.0.6:10200` directly — no port publishing
needed, no HA network change.

| Priority | Assessment |
|---|---|
| No public exposure | ✅ — bridge subnet stays internal |
| Minimal blast radius | ✅ if IPs are pinned via `--ip`; ❌ if not (any container restart can re-IP) |
| Maintainability | ❌ — IP-based config is brittle; new containers need static-IP allocation discipline; documentation lives in IPs not names; HA UI shows raw IPs |
| Docker DNS simplicity | ❌ — there is **no** DNS from host namespace into a user-defined bridge. Names like `aurora-piper` do not resolve. IPs only. |
| HA Wyoming integration compatibility | ✅ if IPs are pinned (host+port accepts IPs); fragile otherwise |

**Verdict:** Disqualified. Loses Docker DNS
simplicity (priority on the user's list), trades
the "publish a loopback port" cost of B for a
"manage static bridge IPs forever" cost.

### Option D — Migrate HA to a sidecar Wyoming proxy

Hypothetical: deploy a small Wyoming-aware proxy
attached to both `ai-local_default` and host
network, terminate HA's connection there. Not
considered in detail because (a) it adds a moving
part with no clear payoff over B, (b) no
maintained off-the-shelf component exists for this
exact purpose. Mentioned only for completeness.

---

## 4. Recommendation

**Adopt Option B at D-1.5 prep, with strict
loopback binding.**

Concrete change set (applied at D-1.5 prep, not now):

1. Recreate `aurora-whisper` with
   `-p 127.0.0.1:10300:10300` appended to the
   existing D-1.2 docker run. Bind mount and CLI
   args unchanged; cache preserved.
2. Recreate `aurora-piper` with
   `-p 127.0.0.1:10200:10200` appended to the
   existing D-1.3 docker run. Bind mount, voice
   cache (now 256 MB after the C-D-08 exercise),
   and CLI args unchanged.
3. At D-1.4, deploy `aurora-wakeword` with
   `-p 127.0.0.1:10400:10400` from the start —
   no second recreation needed.
4. Update
   [`voice_privacy.md`](../../../06_security/voice_privacy.md)
   §4 to read "no new LAN-published port" and add
   a sentence acknowledging loopback binding for
   HA Assist's consumption.
5. Update
   [`pipeline-spec.md`](pipeline-spec.md) §2 slot
   table to record the actual HA-side URIs as
   `127.0.0.1:<port>` rather than the Docker DNS
   names. Open WebUI's HTTP-shim consumers at D-1.7
   are unaffected — they live on different ports
   (`8000`/`8001`) in **separate** containers
   (per C-D-06 + C-D-09: the Piper HTTP shim is a
   distinct OpenAI-compatible TTS container, not a
   built-in mode on `aurora-piper`).
6. Take a Restic snapshot of `/srv/homelab/data/`
   before the container recreations (Lesson 005
   "backups before major changes" + the
   readiness-assessment Risk 6 catch-up).

Open WebUI's Audio surface at D-1.7 continues to
reach the Wyoming endpoints by Docker DNS over
`ai-local_default` — Option B does not remove that
path; it adds a parallel loopback surface for HA's
consumption.

---

## 5. Consequences and tracked changes

- [`pipeline-spec.md`](pipeline-spec.md) §2 slot
  table will move to `127.0.0.1:*` at D-1.5
  configuration time.
- [`voice_privacy.md`](../../../06_security/voice_privacy.md)
  §4 will get a one-paragraph clarification at the
  same time.
- C-D-05 (pipeline timeout) and D-D3-VOICE-SWAP
  (AURORA voice identity reconciliation) are
  unaffected by this decision — both are pure HA
  pipeline configuration at D-1.5.
- This decision does **not** change any container
  in D-1.3 scope. `aurora-whisper` and
  `aurora-piper` remain on their current docker run
  recipes until D-1.5 prep.

---

## 6. Rejected on principle

- **Publish Wyoming ports on `0.0.0.0`** (LAN-wide):
  violates "no public exposure" and adds attack
  surface for no benefit — HA is the only consumer
  for these endpoints in Phase D-1.
- **Disable HA's host network mode** to make
  Option A work: cost to HA's existing device
  discovery is too high.
- **Cloudflared route to Wyoming endpoints**:
  voice traffic on WAN is explicitly forbidden by
  [`voice_privacy.md`](../../../06_security/voice_privacy.md)
  §1 ("No audio crosses WAN") and the AMAROLAB
  architecture principles. Not considered.

---

## 7. Stop point

This is a decision note only. No container is
recreated, no port is published, no
`voice_privacy.md` or `pipeline-spec.md` edit is
made by this document. Application happens at
D-1.5 prep, after D-1.4 closes and before HA
Assist is wired up.
