# Zigbee2MQTT - Despliegue inicial

## Contexto
Se despliega Zigbee2MQTT como capa de integración Zigbee del homelab, conectada a Home Assistant mediante MQTT.

## Objetivo
Centralizar dispositivos Zigbee con control local, compatibilidad amplia y capacidad de depuración avanzada.

## Arquitectura
Dispositivos Zigbee → Dongle USB → Zigbee2MQTT → Mosquitto → Home Assistant

## Requisitos previos
- Home Assistant operativo
- Dongle Zigbee detectado en `/dev/serial/by-id/...`
- Docker y Docker Compose operativos

## Implementación
### Mosquitto
### Zigbee2MQTT
### Integración con Home Assistant

## Problemas encontrados
(Pendiente)

## Estado actual
(Pendiente)

## Próximos pasos
- Emparejar dispositivos
- Crear zonas y entidades
- Diseñar automatizaciones