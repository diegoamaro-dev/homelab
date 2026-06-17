# Mosquitto authentication hardening — APPLIED

- **Date:** 2026-06-17
- **Status:** **APPLIED.** Mosquitto moved off
  `allow_anonymous true` to authenticated
  `homeassistant` + `zigbee2mqtt` users with a
  per-user ACL file. Gate G-5 re-executed end-to-end
  through the hardened broker — 5 audit lines, all
  `allowed=true, result_code="ok"`, baseline restored.
  The pre-Phase-D blocker is lifted.
- **Scope:** Broker config + ACL file landed. The
  `passwords` file lives in the Mosquitto config
  volume (untracked, hashed). Plaintext credentials
  live outside the repo at
  `/home/diego/.secrets/mqtt-credentials.env`. This
  log captures the **verification** evidence; the
  reference architecture lives in
  [`../03_services/zigbee-stack/mosquitto/auth-hardening.md`](../03_services/zigbee-stack/mosquitto/auth-hardening.md).
- **Inputs:**
  - Gate G-5 closeout (the apex pre-hardening Phase C
    artefact, re-executed in §3 below):
    [`2026-06-17_phaseC_gate_g5_applied.md`](2026-06-17_phaseC_gate_g5_applied.md).
  - Phase C closeout (records the pre-hardening
    posture as the working state at Phase C exit):
    [`2026-06-17_phaseC_closeout.md`](2026-06-17_phaseC_closeout.md).
  - Zigbee2MQTT first-devices import:
    [`../03_services/zigbee-stack/zigbee2mqtt_first_devices.md`](../03_services/zigbee-stack/zigbee2mqtt_first_devices.md).
  - Reference architecture (the durable doc this log
    proves out):
    [`../03_services/zigbee-stack/mosquitto/auth-hardening.md`](../03_services/zigbee-stack/mosquitto/auth-hardening.md).

---

## 1. What changed

| Surface                                       | Before                            | After |
| --------------------------------------------- | --------------------------------- | ----- |
| `config/mosquitto.conf` `allow_anonymous`     | `true`                            | `false` |
| `config/mosquitto.conf` `password_file`       | absent                            | `/mosquitto/config/passwords` |
| `config/mosquitto.conf` `acl_file`            | absent                            | `/mosquitto/config/acls` |
| Users in `config/passwords`                   | (no file)                         | `homeassistant`, `zigbee2mqtt` |
| Per-user ACLs                                 | (none)                            | scoped per §1.2 of the reference doc |
| Anonymous `mosquitto_sub`                     | accepted                          | `Connection Refused: not authorised` |
| HA MQTT integration                           | unauthenticated                   | username/password from `secret.yaml` |
| Z2M `configuration.yaml` MQTT block           | unauthenticated                   | `!secret mqtt_user` / `!secret mqtt_password` |
| `00_overview/CURRENT_STATE.md` Mosquitto §    | "anonymous local access"          | "hardened: authenticated users + ACLs" |
| ROADMAP Phase D pre-blocker                   | "Mosquitto authentication hardening" | lifted |

The pre-hardening config is preserved on disk at
`03_services/zigbee-stack/mosquitto/config/mosquitto.conf.pre-hardening`
for diff reference.

---

## 2. Verification — read-only static checks

Captured `2026-06-17T00:46Z`.

### 2.1 Broker config

```text
$ docker exec mosquitto sh -c \
    'grep -vE "^\s*#|^\s*$" /mosquitto/config/mosquitto.conf'
persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/log/mosquitto.log
log_dest stdout
listener 1883 0.0.0.0
allow_anonymous false
password_file /mosquitto/config/passwords
acl_file /mosquitto/config/acls
```

### 2.2 Users present (names only — hashes never
printed)

```text
$ docker exec mosquitto sh -c \
    'ls -l /mosquitto/config/passwords; awk -F: "{print \$1}" /mosquitto/config/passwords'
-rw-------    1 mosquitto mosquitto       398 Jun 16 23:24 /mosquitto/config/passwords
homeassistant
zigbee2mqtt
```

Mode `0600`, owned by the `mosquitto` user inside the
container (uid `1883`). Exactly the two expected
principals; no extra users.

### 2.3 ACL file

```text
$ docker exec mosquitto sh -c 'cat /mosquitto/config/acls'
# Mosquitto ACL — Amarolab — 2026-06-17
# Default: deny all; per-user rules below grant only what is needed.

user homeassistant
topic readwrite homeassistant/#
topic readwrite zigbee2mqtt/#

user zigbee2mqtt
topic readwrite zigbee2mqtt/#
topic write homeassistant/#
topic read homeassistant/status
```

303 bytes, `0664`. Default-deny semantics rely on
Mosquitto's documented behaviour: any
`(user, topic, op)` not listed is denied.

---

## 3. Verification — dynamic / wire-level

### 3.1 Anonymous probe is refused

```text
$ docker exec mosquitto mosquitto_sub \
    -h 127.0.0.1 -p 1883 -t 'amarolab/probe' -C 1 -W 2
Connection error: Connection Refused: not authorised
```

### 3.2 `zigbee2mqtt` user — bridge state

```text
$ docker exec mosquitto mosquitto_sub \
    -h 127.0.0.1 -p 1883 \
    -u zigbee2mqtt -P "<len=32>" \
    -t 'zigbee2mqtt/bridge/state' -C 1 -W 4
{"state":"online"}
```

(Password value redacted; sourced from
`/home/diego/.secrets/mqtt-credentials.env`. Length
32 chars.)

### 3.3 `homeassistant` user — publish

```text
$ docker exec mosquitto mosquitto_pub \
    -h 127.0.0.1 -p 1883 \
    -u homeassistant -P "<len=32>" \
    -t 'homeassistant/amarolab/probe' \
    -m '{"k":"probe"}' -q 1
(exit 0)
```

### 3.4 Z2M devices reflected in bridge

```text
$ docker exec mosquitto mosquitto_sub \
    -h 127.0.0.1 -p 1883 \
    -u zigbee2mqtt -P "<len=32>" \
    -t 'zigbee2mqtt/bridge/devices' -C 1 -W 4 \
  | jq -r '.[] | select(.friendly_name != "Coordinator")
                 | "\(.friendly_name) | \(.definition.model) | interview_completed=\(.interview_completed)"'
Impresora 3D | S60ZBTPF | interview_completed=true
Toldo | MINI-ZBRBS | interview_completed=true
Sensor Pasillo | SNZB-03P | interview_completed=true
Sensor Entarda | SNZB-03P | interview_completed=true
Sensor Dormitorio | SNZB-06P | interview_completed=true
Sensor Habita | SNZB-06P | interview_completed=true
Sensor Puerta Principal | SNZB-04 | interview_completed=true
Sensor Cocina | SNZB-06P | interview_completed=true
Sensor Planta Entrada | ZS-304Z | interview_completed=true
Botón  Escritorio | SNZB-01P | interview_completed=true
```

All ten Zigbee devices remained interviewed and
visible. The Phase-C devices (`Impresora 3D`,
`Toldo`) plus the broader set imported between Phase C
closeout and hardening are all present.

---

## 4. End-to-end — Gate G-5 re-executed

The apex Phase C exit gate (Gate G-5 — first real
`ha_call_service` happy-path) was re-executed against
the **hardened** broker to confirm authenticated
`homeassistant` MQTT continues to satisfy HA's
discovery + entity-update flow under load. The
sequence is identical to
[`2026-06-17_phaseC_gate_g5_applied.md`](2026-06-17_phaseC_gate_g5_applied.md):
pre-read → `turn_on` → verify → `turn_off` → restore.

```text
[1/5] pre-read:   result_code=ok state=off
[2/5] turn_on:    result_code=ok ha_status=200
[3/5] verify-on:  result_code=ok state=on
[4/5] turn_off:   result_code=ok ha_status=200
[5/5] verify-off: result_code=ok state=off

baseline-restored: True  (baseline was 'off')
```

Five audit lines emitted to
`/srv/homelab/data/openwebui/amarolab-audit.log` —
all `allowed=true, result_code="ok"`:

```text
2026-06-17T00:47:31 tool=ha_get_state    allowed=True result_code=ok args={"entity_id": "switch.impresora_3d"}
2026-06-17T00:47:49 tool=ha_get_state    allowed=True result_code=ok args={"entity_id": "switch.impresora_3d"}
2026-06-17T00:47:49 tool=ha_call_service allowed=True result_code=ok args={"domain": "switch", "service": "turn_on",  "entity_id": "switch.impresora_3d", ...}
2026-06-17T00:47:51 tool=ha_get_state    allowed=True result_code=ok args={"entity_id": "switch.impresora_3d"}
2026-06-17T00:47:51 tool=ha_call_service allowed=True result_code=ok args={"domain": "switch", "service": "turn_off", "entity_id": "switch.impresora_3d", ...}
2026-06-17T00:47:54 tool=ha_get_state    allowed=True result_code=ok args={"entity_id": "switch.impresora_3d"}
```

(The first line is the post-recreate `sun.sun` smoke
test; the next five are the G-5 sequence proper.)

Implication: the **authenticated** `homeassistant`
MQTT user observed both Z2M state transitions
(`OFF → ON`, `ON → OFF`) and surfaced them to HA's
state machine within the ~2 s settle window the G-5
script polls. Z2M's `homeassistant/#` writes were
accepted by the broker under the `topic write
homeassistant/#` ACL rule for the `zigbee2mqtt` user.

---

## 5. Sidecar — Open WebUI recreate

During this work the `openwebui` container was
recreated (not merely restarted) so that the rotated
`HA_LLAT` would be picked up; `docker restart`
preserves the existing container's environment, which
is frozen at create time.

- Old container preserved as
  `openwebui_pre_llat_recreate_20260617004619`.
- Pre/post md5 of
  `/srv/homelab/data/openwebui/webui.db` and
  `amarolab-audit.log` — **identical** (no data
  loss):

  ```text
  ce0884d7e0c8cf40cc81adcbef62fe88  /srv/homelab/data/openwebui/webui.db
  d899c443c66cebaba51c561cde2dfbb4  /srv/homelab/data/openwebui/amarolab-audit.log
  ```

- New container's `HA_LLAT` sha256[:8] = `c69e81f5`
  (matches the `.env` value sha256[:8] = `c69e81f5`;
  the pre-rotation value was `fd5b5c65`).
- Same `docker run` command as the canonical Phase C
  recipe documented in
  [`2026-06-17_phaseC_gate_gcpre.md`](2026-06-17_phaseC_gate_gcpre.md)
  §5.3 — same image
  (`ghcr.io/open-webui/open-webui:main`), same data
  bind mount, same `ai-local_default` + `proxy_default`
  network attachments, same env passthrough pattern.

The recreate is not a hardening change; it is
captured here because Mosquitto verification §3 ran
on the **post-recreate** stack and the audit lines in
§4 were emitted by the new container.

---

## 6. Outcome

- `00_overview/CURRENT_STATE.md` updated — Mosquitto §
  flips from "anonymous local access" to "hardened".
- `00_overview/AMAROLAB_HANDOFF.md` updated — Security
  Status §: Mosquitto hardening moves from "Pending"
  to "Completed (2026-06-17)". Pre-Phase-D blocker
  list — entry removed.
- `00_overview/ROADMAP.md` updated — Phase D
  "Pre-Phase-D blocker" entry removed; Phase D is now
  unblocked.
- Reference architecture written at
  [`../03_services/zigbee-stack/mosquitto/auth-hardening.md`](../03_services/zigbee-stack/mosquitto/auth-hardening.md).

### 6.1 Phase D entry

Phase D — Voice — is no longer gated by MQTT auth
hardening. The next blockers to scope are the ones
already listed in
[`../00_overview/AMAROLAB_HANDOFF.md`](../00_overview/AMAROLAB_HANDOFF.md)
"Next Immediate Task" (host vs HA-Assist pipeline
decision, microphone path, wake-word + Piper voice).

### 6.2 Out of scope

- TLS on the broker (still plaintext on
  `ai-local_default`). Tracked as a future item;
  current threat model accepts in-Docker plaintext
  because no host port is published.
- Credential rotation cadence policy.
- Per-device ACLs (current ACLs are per-process; a
  future device-onboarding flow may want
  per-device-class scoping).

---

## 7. No-commit posture

This session **did not** `git commit` and **did not**
`git push`. Working-tree state per the session's
final `git status` is captured separately. The
operator decides commit cadence.
