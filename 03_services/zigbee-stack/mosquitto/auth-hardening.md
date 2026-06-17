# Mosquitto authentication hardening

- **Status:** **APPLIED.** Mosquitto is running with
  `allow_anonymous false`, two authenticated users
  (`homeassistant`, `zigbee2mqtt`), and a per-user ACL
  file that scopes each principal to its required topic
  namespaces. End-to-end demonstration: Gate G-5
  re-executed post-hardening — full
  `off → turn_on → on → turn_off → off` sequence against
  `switch.impresora_3d` (Sonoff S60ZBTPF) with all
  Home-Assistant-to-Mosquitto-to-Zigbee2MQTT MQTT
  round-trips traversing the authenticated brokers.
- **Posture before hardening:**
  `allow_anonymous true`, no password file, no ACLs.
  This was the Phase C bring-up posture, intentional
  while the Zigbee2MQTT ↔ Mosquitto ↔ Home Assistant
  chain was being validated and called out explicitly
  in [`../../../00_overview/CURRENT_STATE.md`](../../../00_overview/CURRENT_STATE.md)
  and [`../../../00_overview/AMAROLAB_HANDOFF.md`](../../../00_overview/AMAROLAB_HANDOFF.md)
  as a temporary state. The pre-hardening config is
  preserved on disk at
  `config/mosquitto.conf.pre-hardening` for diff
  reference.
- **Pre-Phase-D blocker:** lifted. Voice (Phase D) is
  no longer gated on MQTT auth hardening per the
  ROADMAP §"Phase D — Voice / Pre-Phase-D blocker".

---

## 1. Architecture

```
Zigbee2MQTT  --(zigbee2mqtt user, TCP 1883)-->  Mosquitto
Home Assist  --(homeassistant user, TCP 1883)--> Mosquitto
```

Both clients connect to Mosquitto over the
`ai-local_default` Docker network. No client connects
anonymously; anonymous connects are explicitly refused
by the broker (`Connection Refused: not authorised`).

### 1.1 Users

| User            | Purpose                                         |
| --------------- | ----------------------------------------------- |
| `homeassistant` | HA's MQTT integration — discovery + entity I/O. |
| `zigbee2mqtt`   | Z2M bridge process — device traffic + status.   |

Passwords were generated locally (32-char random
strings), hashed by `mosquitto_passwd` into
`config/passwords` (mode `0600`, owned by the
`mosquitto` uid inside the container), and the
plaintext values are stored **outside the repo** at
`/home/diego/.secrets/mqtt-credentials.env`.

Open WebUI / the assistant **does not** read MQTT
credentials. The credentials file is consumed by:

- the Home Assistant MQTT integration (configured
  inside HA's UI; the secret never appears in the
  versioned `configuration.yaml`),
- the Zigbee2MQTT process (`configuration.yaml`
  references `!secret mqtt_user` / `!secret
  mqtt_password`; the populated `secret.yaml` lives in
  the Z2M data volume and is not in the repo).

### 1.2 ACLs

`config/acls` (mode `0664`, owned by the host user):

```
user homeassistant
topic readwrite homeassistant/#
topic readwrite zigbee2mqtt/#

user zigbee2mqtt
topic readwrite zigbee2mqtt/#
topic write homeassistant/#
topic read homeassistant/status
```

Design notes:

- Default is **deny-all** (the file lists only the
  grants; Mosquitto's default-deny semantics apply to
  anything not listed).
- `homeassistant` gets both namespaces because it both
  consumes discovery messages on `zigbee2mqtt/#`
  (forwarded by HA's MQTT integration) and produces
  its own state on `homeassistant/#`.
- `zigbee2mqtt` is read-only on `homeassistant/status`
  (it watches HA's birth/will to decide when to
  re-publish retained discovery payloads) and
  write-only on `homeassistant/#` (it publishes
  discovery messages there for HA to consume), and
  read-write on `zigbee2mqtt/#` (its own bridge
  namespace).

### 1.3 `mosquitto.conf`

The hardened broker config
(`config/mosquitto.conf` — 6 effective lines,
non-comment / non-blank, full file checked in to the
repo):

```
persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/log/mosquitto.log
log_dest stdout
listener 1883 0.0.0.0
allow_anonymous false
password_file /mosquitto/config/passwords
acl_file /mosquitto/config/acls
```

Diff from `mosquitto.conf.pre-hardening`:

- `allow_anonymous true` → `allow_anonymous false`
- two new lines: `password_file`, `acl_file`

The listener is bound to `0.0.0.0` *on the docker
network* (the container does not publish 1883 to the
host); the broker is reachable only by sibling
containers attached to `ai-local_default`.

---

## 2. Secrets handling

| File                                              | Where             | In repo? |
| ------------------------------------------------- | ----------------- | -------- |
| `/home/diego/.secrets/mqtt-credentials.env`       | Host, mode `0600` | **No.**  |
| `config/passwords` (hashed)                       | Mosquitto config volume | **No.** Untracked; ignored from versioning. |
| Z2M `secret.yaml` (populated)                     | Z2M data volume   | **No.**  |
| `config/mosquitto.conf` (no secrets)              | Repo              | Yes.     |
| `config/acls` (no secrets)                        | Repo              | Yes.     |

Versioning rules:

- The hashed `passwords` file **must not** be
  committed even though it contains only hashes —
  hashes are still a credential artefact and live in
  the operator's local config volume.
- Plaintext secrets are never written into the repo
  in any form, including in dated session logs (which
  may reference variable names + lengths only).
- Rotation: regenerate via
  `mosquitto_passwd -b -c config/passwords <user>
  <new-pass>`; update
  `/home/diego/.secrets/mqtt-credentials.env`;
  reload the broker (`docker exec mosquitto
  kill -HUP 1` or container restart); update HA's MQTT
  integration password and Z2M's `secret.yaml`.

---

## 3. Verification protocol

Done at hardening apply time and repeatable any time.

### 3.1 Static config checks

```bash
docker exec mosquitto sh -c '
  grep -vE "^\s*#|^\s*$" /mosquitto/config/mosquitto.conf
'
```

Must show `allow_anonymous false`, `password_file
/mosquitto/config/passwords`, `acl_file
/mosquitto/config/acls`.

```bash
docker exec mosquitto sh -c '
  awk -F: "{print \$1}" /mosquitto/config/passwords
'
```

Must list **exactly** `homeassistant` and
`zigbee2mqtt`. Hashes themselves are not printed.

### 3.2 Anonymous probe — must fail

```bash
docker exec mosquitto mosquitto_sub \
  -h 127.0.0.1 -p 1883 \
  -t 'amarolab/probe' -C 1 -W 2
```

Expected: `Connection Refused: not authorised`.

### 3.3 Authenticated probes — must succeed

```bash
set -a; . /home/diego/.secrets/mqtt-credentials.env; set +a
docker exec mosquitto mosquitto_sub \
  -h 127.0.0.1 -p 1883 \
  -u zigbee2mqtt -P "$MQTT_ZIGBEE2MQTT_PASSWORD" \
  -t 'zigbee2mqtt/bridge/state' -C 1 -W 4
docker exec mosquitto mosquitto_pub \
  -h 127.0.0.1 -p 1883 \
  -u homeassistant -P "$MQTT_HOMEASSISTANT_PASSWORD" \
  -t 'homeassistant/amarolab/probe' -m '{"k":"probe"}' -q 1
```

Expected: bridge state returns
`{"state":"online"}`; `homeassistant` publish returns
exit 0 with no auth error on stderr.

### 3.4 End-to-end via Gate G-5

```bash
# inside openwebui container
python3 /tmp/g5.py
```

Where `/tmp/g5.py` is the closed-loop sequence
documented in
[`../../../09_logs/2026-06-17_phaseC_gate_g5_applied.md`](../../../09_logs/2026-06-17_phaseC_gate_g5_applied.md)
and re-exercised in
[`../../../09_logs/2026-06-17_mosquitto_auth_hardening_applied.md`](../../../09_logs/2026-06-17_mosquitto_auth_hardening_applied.md).

Expected: 5 audit lines, all
`allowed=True, result_code="ok"`, baseline restored.

---

## 4. Operational notes

- **Reload** after a credential change:
  `docker exec mosquitto kill -HUP 1`. A SIGHUP picks
  up `passwords` and `acls` without dropping
  established sessions. A full restart is safe but
  causes brief Z2M disconnect (Z2M auto-reconnects).
- **ACL changes** require the same SIGHUP. The deny
  semantics are strict; mistyped topics on the read
  side fail silently from the publisher's POV — debug
  with `mosquitto_sub` as the affected user and watch
  for absence of expected messages.
- **TLS** is **not** enabled. The broker only listens
  on the `ai-local_default` Docker network; no host
  port is exposed for 1883. If a future service needs
  to publish from outside the Docker bridge (e.g., a
  voice front-end on a different VLAN), TLS should be
  introduced before opening the listener.

---

## 5. Related documents

- Apply log:
  [`../../../09_logs/2026-06-17_mosquitto_auth_hardening_applied.md`](../../../09_logs/2026-06-17_mosquitto_auth_hardening_applied.md)
- Z2M first-devices import:
  [`../zigbee2mqtt_first_devices.md`](../zigbee2mqtt_first_devices.md)
- Phase C Gate G-5 (the pre-hardening end-to-end
  baseline that this work preserves):
  [`../../../09_logs/2026-06-17_phaseC_gate_g5_applied.md`](../../../09_logs/2026-06-17_phaseC_gate_g5_applied.md)
- Phase C closeout (where the pre-hardening posture is
  recorded as the working state at Phase C exit):
  [`../../../09_logs/2026-06-17_phaseC_closeout.md`](../../../09_logs/2026-06-17_phaseC_closeout.md)
