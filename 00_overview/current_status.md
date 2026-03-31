# Current System Status – Homelab

## Contexto

Este documento define el estado actual del homelab en el momento en que se establece la base del proyecto documentado y versionado en GitHub.

Se ha pasado de una fase inicial de pruebas a una fase estructurada con control mediante Git, documentación y acceso remoto consolidado.

---

## Infraestructura base

### Red y acceso

* Acceso remoto mediante Tailscale
* SSH operativo desde múltiples dispositivos (portátil, torre, móvil)
* VS Code conectado al servidor mediante Remote SSH
* No se utilizan puertos abiertos en el router para acceso externo

---

### Servidor

* Mini PC ejecutando Linux (Ubuntu)
* Acceso principal mediante SSH
* Gestión mediante terminal y VS Code remoto

---

## Servicios activos (Docker)

Contenedores actualmente en ejecución:

* `openwebui` → puerto 3000 (interno 8080)
* `ollama` → puerto 11434
* `qdrant` → puerto 6333
* `nginx-proxy-manager` → puertos 80, 81, 443
* `portainer` → puertos 8000, 9443
* `homeassistant` → en ejecución (puerto no verificado)

---

## Estado de arquitectura

### Actual

* Servicios expuestos directamente mediante puertos
* Acceso manual mediante `http://homelab:PORT`
* Nginx Proxy Manager instalado pero no utilizado como punto central de entrada

---

### Objetivo

* Centralizar acceso mediante reverse proxy
* Eliminar dependencia de puertos en el acceso
* Usar nombres internos:

  * `ai.homelab`
  * `portainer.homelab`
  * otros servicios

---

## Documentación

* Repositorio creado en GitHub: `homelab`
* Estructura base de carpetas creada
* Primer documento técnico:

  * `01_architecture/remote-access-tailscale.md`

---

## Identidad profesional

* Username GitHub actualizado: `diegoamaro-dev`
* Dominio adquirido: `diegoamaro.dev`
* Inicio de construcción de portfolio técnico

---

## Problemas detectados

* Uso excesivo de puertos expuestos
* Falta de reverse proxy activo
* Posible desorganización de redes Docker
* Servicio Home Assistant sin visibilidad clara de red

---

## Decisiones técnicas tomadas

* Uso de Tailscale como red principal
* Uso de SSH como acceso base
* Uso de VS Code como entorno de control
* Uso de GitHub como sistema de documentación y versionado

---

## Próximos pasos

1. Verificar redes Docker
2. Integrar OpenWebUI con Nginx Proxy Manager
3. Implementar acceso sin puertos (`ai.homelab`)
4. Documentar arquitectura de red Docker
5. Revisar exposición de servicios
6. Mejorar seguridad (SSH keys, segmentación)

---

## Nota importante

Este documento representa un punto de control del sistema.

A partir de aquí, cualquier cambio relevante debe:

1. implementarse
2. validarse
3. documentarse
4. versionarse en Git

---

## Principio operativo

Si no está documentado, no existe.
