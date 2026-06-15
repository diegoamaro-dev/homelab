# 09 — Home Assistant

## Service

| Field | Value |
|-------|-------|
| Container name | `homeassistant` |
| Image | `ghcr.io/home-assistant/home-assistant:stable` |
| Image pulled | 2026-03-06 (~3 months stale) |
| Image size | 3.34 GB |
| Application version | **2026.3.1** (`/config/.HA_VERSION`) |
| Network mode | **host** (binds `:8123` on every host IP including Tailscale) |
| Privileged | no |
| Status | Up 5 days |
| Lock file | `/config/.ha_run.lock` last touched 2026-06-08 (boot) |

## Bind mounts

- `/srv/homelab/homeassistant` → `/config`
- `/etc/localtime` → `/etc/localtime` (read-only)

## Config (`/config/configuration.yaml`)

```yaml
default_config:

frontend:
  themes: !include_dir_merge_named themes

automation: !include automations.yaml
script: !include scripts.yaml
scene: !include scenes.yaml
```

`automations.yaml`, `scripts.yaml`, `scenes.yaml`, `secrets.yaml` exist but
are effectively empty (2 B and 161 B respectively).

## Core configuration

`/config/.storage/core.config`:

| Field | Value |
|-------|-------|
| Location | "Casa" |
| Latitude / longitude | 42.3438932, -7.8571792 (Ourense, Spain) |
| Time zone | Europe/Madrid |
| Country / locale | ES / `es` |
| Currency | EUR |
| Unit system | metric |
| Radius | 100 m |

## Integrations (`config_entries`)

10 entries enabled:

| Domain | Title |
|--------|-------|
| `sun` | Sun |
| `backup` | Backup |
| `bluetooth` | Unknown (`<REDACTED-BT-MAC>`) |
| `go2rtc` | go2rtc |
| `thread` | Thread |
| `cast` | Google Cast |
| `shopping_list` | Shopping list |
| `google_translate` | Google Translate TTS |
| `met` | Home (weather) |
| `radio_browser` | Radio Browser |

> No Zigbee2MQTT, MQTT, or Z-Wave integration is wired up. The Zigbee dongle
> and `zigbee2mqtt` container are running, but Home Assistant does not yet
> talk to them. `zigbee2mqtt`'s own HA-autodiscovery flag is off
> (`homeassistant.enabled: false` in its config).
> The Mosquitto broker required for that path is also currently crash-looping.

## Users

`/config/.storage/auth_provider.homeassistant`: 1 user — `diego`.

## Recorder DB

`home-assistant_v2.db` 8.4 MB + WAL 4.1 MB. Last modified during the audit
window — Home Assistant is actively recording state.

## Logs

`home-assistant.log` (23.9 kB, last write 2026-06-13 06:46),
`home-assistant.log.1` (16.8 kB, 2026-06-08 09:08), and
`home-assistant.log.fault` (0 B, 2026-06-03 12:55 — same date as the host
crash). The empty fault file is consistent with a hard reset rather than a
controlled crash.

## TTS

`/config/tts/` contains cached Google Translate TTS clips (last write
2026-04-01). Not large.

## External / internal URL

`external_url` and `internal_url` are both `null`. HA is reached by IP only —
or via Cloudflare/NPM if configured (no NPM proxy host inspection without
sudo, but no Cloudflared route targets HA either).
