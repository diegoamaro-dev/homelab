---
id: internet-uplink
name: Internet Uplink
region: home
kind: service
status: active
schema_version: 1
priority: high
baseline: { state: on }
binding: { ha_entity: binary_sensor.rooter_estado_wan }
aliases: [ "internet", "conexión a internet", "internet uplink", "internet connection", "wan", "uplink" ]
collector: ha-states
anomaly_rules:
  - { token: wan_down, condition: "state == off" }
---

## Purpose

Internet / WAN connectivity (router integration). A clean binary up/down signal for whether the
lab can reach the internet. Kept in the `home` region for WM-2 (D-WM2-5); an `infrastructure`
placement may be revisited in a future phase.

## Reasoning

Loss of WAN affects remote access and cloud-dependent functions. The rule fires on `off` **only**
— an `unavailable` / `unknown` reading never raises (D7), matching the live detector. The
router's external-IP and speed sensors are **deliberately unmodelled**: the IP value never enters
any artifact (AD-18).

## Suggested operator actions

*Recommendations only.* Check the router / ISP; power-cycle the router if needed. Remote access is
unavailable until connectivity is restored.
