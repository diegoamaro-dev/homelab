## Implementación real

### Mosquitto
- Imagen: `eclipse-mosquitto:2`
- Puerto: `1883`
- Estado: operativo
- Configuración inicial: acceso anónimo solo para fase de validación local

### Zigbee2MQTT
- Imagen: `koenkk/zigbee2mqtt:latest`
- Puerto web: `8080`
- Estado: operativo
- MQTT: conectado correctamente al broker Mosquitto
- Integración Home Assistant: autodiscovery activo

### Dongle Zigbee
- Detectado en: `/dev/serial/by-id/<ZIGBEE_DONGLE_ID>`
- Mapeado en contenedor como: `/dev/ttyUSB0`

## Estado actual
Stack base desplegado y operativo:
- Mosquitto levantado
- Zigbee2MQTT levantado
- Coordinador Zigbee detectado
- Frontend accesible en red local/VPN
- Sin dispositivos Zigbee emparejados todavía

## Problemas encontrados
- Inicialmente se intentó levantar el stack antes de crear la estructura de directorios y archivos de configuración.
- Se corrigió creando la carpeta `zigbee-stack`, el `docker-compose.yml` y las configuraciones mínimas de Mosquitto y Zigbee2MQTT.

## Próximos pasos
- Validar acceso al frontend web
- Confirmar integración MQTT en Home Assistant
- Emparejar dispositivos Zigbee de forma controlada
- Endurecer seguridad de MQTT eliminando acceso anónimo