---
id: entrance-plant
name: Entrance Plant
region: home
kind: device
status: active
schema_version: 1
priority: low
archetype: zigbee-device
baseline: { conditions: [ "water_warning == none", "soil_moisture >= 20" ] }
binding:
  water_warning: { ha_entity: sensor.sensor_planta_entrada_water_warning }
  soil_moisture: { ha_entity: sensor.sensor_planta_entrada_soil_moisture }
aliases:
  water_warning: [ "aviso de riego", "riego de la planta", "plant water warning", "water warning" ]
  soil_moisture: [ "humedad de la planta", "humedad del suelo", "plant moisture", "soil moisture" ]
collector: ha-states
anomaly_rules:
  - { token: plant_water_warning, condition: "water_warning != none" }
  - { token: plant_soil_dry, condition: "soil_moisture < 20" }
---

## Purpose

The monitored entrance plant — soil / water health. Aurora reasons about *"the entrance plant
needs water"*, not about raw sensor numbers.

## Reasoning

Two complementary signals: the device's own water-warning flag (`water_warning`, categorical) and
a numeric soil-moisture floor (`soil_moisture`). `plant_water_warning` fires when
`water_warning != none`; `plant_soil_dry` fires when `soil_moisture < 20` (%). Both are `low`
(maintenance / care). An `unavailable` / `unknown` reading never raises (D7) — the categorical
`!= none` test is understood against a present value only, and the numeric test needs a real
number. Depends on `zigbee-mesh` (archetype).

Note the threshold asymmetry (reality wins): the plant dry floor is **strictly** `< 20`, whereas
the `battery` aspect's percentage floor is `<= 20`.

**Implementation surface (informational, not anomaly-tracked):** `temperature` / `humidity` /
`illuminance` sensors exist but are not tracked. Battery is covered by the **`battery`** aspect
via `sensor.sensor_planta_entrada_battery_state` (categorical; `middle` at authoring).

## Suggested operator actions

*Recommendations only.* Water the plant; if a reading looks implausible, verify the sensor.
