# Zigbee Network Architecture

## Context

This document describes the current Zigbee network state in the Amarolab homelab.

During Phase C of the Amarolab Assistant integration, the Home Assistant write validation was blocked because Zigbee devices were not visible inside Home Assistant. Investigation showed that the Zigbee stack itself was working, but Home Assistant MQTT Discovery was not enabled.

## Objective

Document the real Zigbee architecture, the issue found, the fix applied, and the resulting operational state.

## Architecture

Current Zigbee flow:

```text
Sonoff Zigbee devices
        ↓
Sonoff Zigbee 3.0 USB Dongle Plus
        ↓
Zigbee2MQTT
        ↓
Mosquitto MQTT Broker
        ↓
Home Assistant MQTT Integration
        ↓
Amarolab Assistant / Home Assistant Tools
Hardware
Coordinator
Device: Sonoff Zigbee 3.0 USB Dongle Plus
Host path: /dev/ttyUSB0
Stable detected path:
/dev/serial/by-id/usb-ITead_Sonoff_Zigbee_3.0_USB_Dongle_Plus_<DEVICE_ID>-if00-port0
Joined devices
Friendly name	Device type	Model	Vendor	Home Assistant role
Impresora 3D	Zigbee smart plug	S60ZBTPF	SONOFF	Smart plug / power monitoring
Toldo	Zigbee smart roller shutter switch	MINI-ZBRBS	SONOFF	Cover / roller shutter
Services
Zigbee2MQTT
Container: zigbee2mqtt
Image: koenkk/zigbee2mqtt:latest
Web UI: http://<SERVER_LAN_IP>:8080
Data path:
/home/diego/homelab/03_services/zigbee-stack/zigbee2mqtt/data
Mosquitto
Container: mosquitto
MQTT port: 1883
Current local validation posture:
listener 1883 0.0.0.0
allow_anonymous true

Security note: anonymous MQTT access is acceptable only for the current local validation phase. It should later be replaced by a dedicated MQTT user and allow_anonymous false.

Zigbee2MQTT Configuration

Current relevant configuration:

version: 5

mqtt:
  base_topic: zigbee2mqtt
  server: mqtt://mosquitto:1883

serial:
  port: /dev/ttyUSB0
  adapter: zstack
  baudrate: 115200
  rtscts: false

advanced:
  log_level: info
  channel: 20

frontend:
  enabled: true
  port: 8080

homeassistant:
  enabled: true

Sensitive values such as network_key, pan_id, and ext_pan_id are intentionally omitted from this document.

Problem Found

Home Assistant did not show the Zigbee devices even though Zigbee2MQTT showed them as available and controllable.

Initial assumption was that the Zigbee network had not been configured. This was incorrect.

The actual state was:

Zigbee2MQTT container was running.
Sonoff Zigbee dongle was detected.
Mosquitto was running.
The Zigbee devices were joined and operational.
Zigbee2MQTT frontend had been disabled.
Home Assistant MQTT Discovery had been disabled.

Relevant broken configuration:

frontend:
  enabled: false

homeassistant:
  enabled: false
Fix Applied
1. Enabled Zigbee2MQTT frontend

Changed:

frontend:
  enabled: false

to:

frontend:
  enabled: true
  port: 8080
2. Enabled Home Assistant discovery

Changed:

homeassistant:
  enabled: false

to:

homeassistant:
  enabled: true
3. Restarted Zigbee2MQTT
docker restart zigbee2mqtt
4. Added MQTT integration in Home Assistant

Home Assistant was connected to the MQTT broker:

Broker: <SERVER_LAN_IP>
Port: 1883
Username: empty
Password: empty

This matches the current Mosquitto validation configuration with anonymous access enabled.

Validation

After the fix, Home Assistant displayed:

MQTT
3 devices
28 entities

Detected devices:

Impresora 3D
Toldo
Zigbee2MQTT Bridge

This confirms that the discovery chain is working:

Zigbee2MQTT → Mosquitto → Home Assistant
Current Operational State
Working
Sonoff Zigbee coordinator detected.
Zigbee2MQTT starts successfully.
Mosquitto accepts connections.
Zigbee2MQTT connects to Mosquitto.
Home Assistant connects to Mosquitto.
MQTT Discovery works.
Zigbee devices appear in Home Assistant.
Devices can now be used by Amarolab Assistant through Home Assistant tools.
Not yet hardened
Mosquitto still allows anonymous access.
No dedicated MQTT user exists yet.
MQTT credentials are not yet enforced.
Zigbee2MQTT still uses /dev/ttyUSB0 instead of the stable /dev/serial/by-id/... path.
Security Notes

Do not commit real Zigbee network secrets.

Never document:

real network_key
real pan_id
real ext_pan_id
MQTT passwords
private tokens
screenshots showing secrets

Use placeholders:

<ZIGBEE_NETWORK_KEY>
<ZIGBEE_PAN_ID>
<ZIGBEE_EXT_PAN_ID>
<MQTT_USERNAME>
<MQTT_PASSWORD>
<SERVER_LAN_IP>
Risks
Anonymous MQTT

Current Mosquitto configuration allows anonymous LAN clients:

allow_anonymous true

Risk: any device with network access to the broker may publish or subscribe to MQTT topics.

Mitigation planned:

Create dedicated MQTT users.
Disable anonymous access.
Update Zigbee2MQTT credentials.
Update Home Assistant MQTT credentials.
Restart and validate.
Unstable serial path

Current Zigbee2MQTT config uses:

serial:
  port: /dev/ttyUSB0

Risk: device path may change after reboot or USB reordering.

Recommended future change:

serial:
  port: /dev/serial/by-id/usb-ITead_Sonoff_Zigbee_3.0_USB_Dongle_Plus_<DEVICE_ID>-if00-port0
Impact on Amarolab Assistant

This fix unblocks Phase C Home Assistant action validation.

Recommended first controllable entity:

switch.impresora_3d

Recommended first action:

domain: switch
service: turn_on
entity_id: switch.impresora_3d

Avoid using the roller shutter as the first write validation target.

The Toldo device should be tested later because it controls physical movement.

Next Steps
Confirm the exact Home Assistant entity IDs for:
Impresora 3D
Toldo
Run Amarolab read validation:
ha_get_state("switch.impresora_3d")
Run Amarolab write validation on the smart plug:
ha_call_service(
  domain="switch",
  service="turn_on",
  entity_id="switch.impresora_3d"
)
Document Phase C validation result.
Later harden MQTT:
create dedicated MQTT user
disable anonymous access
validate Zigbee2MQTT and Home Assistant reconnect cleanly
Result

The Zigbee stack is now operational and visible from Home Assistant.

The earlier assumption that Zigbee was not configured was wrong. The real issue was disabled Zigbee2MQTT frontend and disabled Home Assistant MQTT Discovery.

The corrected state is:

Zigbee devices visible in Zigbee2MQTT
        ↓
MQTT broker connected
        ↓
Home Assistant MQTT integration configured
        ↓
MQTT Discovery enabled
        ↓
Zigbee devices visible in Home Assistant