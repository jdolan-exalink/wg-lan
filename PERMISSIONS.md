# Permisos y rutas de NetLoom

## Transporte y autorización

Las rutas indican por dónde viaja un paquete. Los permisos determinan si el hub lo puede reenviar. No deben confundirse: un cliente puede tener una ruta hacia una red y tener el acceso denegado por el firewall del servidor.

En split tunnel se distribuyen las redes registradas y el segmento de túneles, excluyendo las LAN propias de la sucursal. Una nueva red requiere actualizar la configuración de los clientes existentes; los cambios de permisos sobre rutas ya distribuidas se aplican en el servidor.

## Firewall

Con el firewall desactivado, el tráfico WireGuard está permitido. Las políticas guardadas pueden consultarse en la vista previa de Policies, pero no restringen el tráfico hasta activar el firewall. Revisar esa matriz antes de activarlo en una instalación existente.

Con el firewall activo se evalúan todos los peers habilitados, incluso aquellos que no tienen grupos. Sin grupos ni asignaciones explícitas se deniega el acceso. Las redes sin propietario requieren permisos explícitos y no se agregan automáticamente a todos los grupos.

Se combinan los grupos directos del peer y los asignados al usuario. Al gestionar explícitamente los grupos de un usuario se elimina la membresía All automática histórica de sus roadwarriors; los otros grupos directos del peer se conservan. Puede asignarse All al usuario de forma explícita si ése es el acceso deseado.

## Precedencia

Toda denegación explícita tiene prioridad sobre una concesión:

1. Denegación individual del peer (override).
2. Denegación por usuario.
3. Denegación por asignación de red al grupo.
4. Denegación por política de grupo o IP.
5. Concesiones por usuario, grupo, peer o política, para destinos no denegados.
6. Sin concesiones: sin acceso.

Una denegación de IP se resta del rango permitido, aunque exista una concesión para toda la LAN. Una concesión de IP no elude una denegación para la red que la contiene. Las posiciones de las políticas son de presentación; no cambian la prioridad de las denegaciones.

Las políticas salientes permiten a miembros del grupo origen acceder a las redes de los miembros del grupo destino. Las entrantes invierten esa relación, y ambas direcciones combinan los dos sentidos. Las asignaciones directas de red por usuario, grupo o peer no requieren crear una política entre grupos.

## Aplicación y observabilidad

Los cambios de grupo, usuario, asignaciones directas y overrides reaplican las reglas mediante el mismo servicio. Si falla la aplicación, la API informa que la configuración quedó guardada y pendiente; no devuelve un éxito de aplicación ficticio.

NetLoom administra NETLOOM-FWD y NETLOOM-POST. Valida las reglas antes de reemplazarlas, conserva las cadenas de otros servicios y revoca únicamente conexiones de los rangos origen/destino que perdieron acceso. Los commits de filter y NAT son independientes.

La pantalla Rutas compara redes y gateways con Linux. Las rutas propias usan protocolo 242 y se reconcilian al aplicar configuración y periódicamente. Al agregar una LAN detrás de una sucursal también se actualizan los AllowedIPs del peer en el hub. Una red sin gateway ni conexión directa queda pendiente.

## Confirmación del cliente

Cada peer tiene una revisión deseada. Descargar una configuración no significa haberla aplicado y un handshake sólo prueba que hay un túnel.

Un cliente compatible informa applied_revision en su reporte de estado después de aplicar AllowedIPs y rutas del sistema. Los routers manuales pueden confirmarse desde el diálogo de configuración del peer después de aplicar la revisión. Verde significa revisión actual confirmada; amarillo significa descarga realizada y aplicación pendiente o desactualizada; rojo significa que falta descargar/aplicar. Un heartbeat actualiza last_seen_at y no modifica la fecha de descarga.

Los clientes anteriores deben implementar la confirmación. Mientras tanto aparecerán pendientes y pueden actualizarse manualmente. No se envían claves privadas en el historial de deltas.
