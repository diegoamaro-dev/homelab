### Instalación de Tailscale

Se instala Tailscale en todos los dispositivos y se inicia sesión con la misma cuenta.

---

### Verificación de red

Comando utilizado:

```bash
tailscale status
Acceso SSH al servidor

Desde Windows:

ssh diego@homelab
Acceso web a la IA
http://homelab:3000
Problemas encontrados
Confusión entre comandos de Windows y Linux
Falta inicial de configuración de claves SSH
Uso de nombres .local fuera de la red local
Solución aplicada
Uso de Tailscale como red privada principal
Uso de SSH para acceso remoto
Uso del hostname homelab mediante MagicDNS
VS Code conectado al servidor mediante Remote SSH
Resultado final
Acceso remoto funcional desde varios dispositivos
Acceso web a la IA desde fuera de la red local
No es necesario abrir puertos en el router
Riesgos y notas
Dependencia actual de Tailscale como servicio externo
WireGuard del FRITZ!Box se mantiene como alternativa o backup
Pendiente mejorar autenticación SSH y ordenar dominios internos
Próximos pasos
Configurar SSH por clave de forma consistente en todos los equipos
Definir reverse proxy y nombres internos (ai.homelab, portainer.homelab)
Documentar servicios y arquitectura de red