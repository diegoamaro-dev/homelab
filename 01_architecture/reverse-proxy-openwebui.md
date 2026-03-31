# Reverse Proxy – OpenWebUI (Nginx Proxy Manager)

## Contexto

Inicialmente, el acceso a OpenWebUI se realizaba mediante puerto expuesto:

```
http://homelab:3000
```

Este enfoque no es escalable ni limpio para una arquitectura de múltiples servicios.

---

## Objetivo

* Eliminar dependencia de puertos en el acceso
* Centralizar el acceso mediante reverse proxy
* Preparar el sistema para múltiples servicios con nombres propios

---

## Arquitectura previa

* `openwebui` en red: `ai-local_default`
* `nginx-proxy-manager` en red: `proxy_default`
* Acceso mediante puerto `3000`

Problema:

Los contenedores no compartían red, por lo que el proxy no podía resolver el servicio por nombre.

---

## Solución aplicada

### 1. Conectar contenedor a red del proxy

Se añade `openwebui` a la red `proxy_default`:

```bash
docker network connect proxy_default openwebui
```

Resultado:

El contenedor queda conectado a dos redes:

* `ai-local_default`
* `proxy_default`

---

### 2. Configuración en Nginx Proxy Manager

Se crea un Proxy Host con:

* **Domain**: `ai.homelab`
* **Scheme**: `http`
* **Forward Hostname**: `openwebui`
* **Forward Port**: `8080`

Opciones activadas:

* Websockets Support
* Block Common Exploits

---

### 3. Resolución DNS (temporal)

Se añade entrada manual en archivo `hosts` de Windows:

```
100.68.180.69 ai.homelab
```

Ruta del archivo:

```
C:\Windows\System32\drivers\etc\hosts
```

---

## Resultado final

Acceso a OpenWebUI mediante:

```
http://ai.homelab
```

* Sin uso de puerto explícito
* Acceso limpio y escalable
* Proxy funcional entre contenedores

---

## Ventajas obtenidas

* Separación entre acceso externo y servicios internos
* Preparación para múltiples servicios bajo mismo punto de entrada
* Arquitectura más mantenible

---

## Limitaciones actuales

* Resolución DNS basada en archivo local (no centralizada)
* Dependencia manual por dispositivo

---

## Próximos pasos

* Implementar DNS interno centralizado
* Añadir más servicios al proxy:

  * `portainer.homelab`
  * `home.homelab`
* Revisar exposición de puertos innecesarios
* Documentar redes Docker

---

## Nota técnica

El acceso entre contenedores se realiza mediante nombre de servicio (`openwebui`) dentro de la red Docker compartida, sin necesidad de exponer puertos al host.

---

## Principio aplicado

Primero funcional → luego limpio → luego escalable
