### Opción 1: ZHA (Zigbee Home Automation)

**Ventajas:**
- Integración nativa en Home Assistant
- Configuración rápida
- Menor complejidad inicial

**Desventajas:**
- Menor control sobre dispositivos
- Compatibilidad limitada en algunos casos
- Menor visibilidad y capacidad de debugging
- Menor flexibilidad para integraciones avanzadas

---

### Opción 2: Zigbee2MQTT

**Ventajas:**
- Amplia compatibilidad (Sonoff, Aqara, Tuya, etc.)
- Control detallado de cada dispositivo
- Sistema desacoplado (MQTT)
- Mayor visibilidad y logs
- Mejor integración con sistemas externos (IA, automatización avanzada)

**Desventajas:**
- Mayor complejidad de instalación
- Requiere MQTT broker adicional
- Configuración manual

---

## Decisión

Se adopta **Zigbee2MQTT + MQTT (Mosquitto)** como solución principal.

## Justificación

La elección se basa en:

- Necesidad de control total del sistema
- Compatibilidad amplia de dispositivos
- Arquitectura desacoplada y escalable
- Mejor integración futura con IA local
- Mayor capacidad de diagnóstico y mantenimiento

ZHA se descarta por limitaciones en control y escalabilidad.

---

## Arquitectura resultante


Dispositivos Zigbee
↓
Dongle Zigbee (USB)
↓
Zigbee2MQTT (Docker)
↓
MQTT Broker (Mosquitto)
↓
Home Assistant
↓
IA local (Ollama / OpenWebUI)


---

## Notas de seguridad

- El acceso a Home Assistant se realiza únicamente a través de VPN
- No se exponen puertos de MQTT a internet
- Se evitará el uso de integraciones cloud innecesarias

---

## Estado actual

Decisión de arquitectura definida.

## Próximos pasos

- Despliegue de Mosquitto (MQTT)
- Despliegue de Zigbee2MQTT
- Integración con Home Assistant
- Migración de dispositivos Zigbee