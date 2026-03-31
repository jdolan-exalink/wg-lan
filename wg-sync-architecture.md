# WG Sync Architecture

## Objetivo

Definir la arquitectura de sincronización de configuración para una futura versión del proyecto de gestión de túneles WireGuard, separando claramente:

- **Plano de datos VPN**: WireGuard
- **Dashboard web**: administración visual
- **Canal de sincronización**: distribución de cambios y estados de clientes

La meta es permitir administración simple para sysadmins, manteniendo compatibilidad con clientes estándar WireGuard y agregando una capa opcional de sincronización para clientes gestionados.

---

## Requisitos funcionales

1. El sistema debe permitir administrar túneles:
   - RoadWarrior
   - Branch Office

2. El sistema debe permitir sincronizar cambios de configuración con clientes gestionados.

3. El sistema debe seguir soportando clientes no gestionados:
   - WireGuard estándar por `.conf`
   - importación por QR
   - equipos donde no se instale agente

4. El dashboard debe poder detectar si un cliente está:
   - sincronizado
   - desactualizado
   - sin capacidad de sync
   - offline

5. En la lista de clientes debe mostrarse el **tipo de conexión/sincronización** utilizado.

6. El puerto de comunicación del canal de sincronización debe estar **separado** del dashboard.

7. Todos los puertos deben poder configurarse.

---

## Separación de puertos

Se propone separar los servicios de esta manera:

- **WireGuard UDP**: `51820/udp`
- **Dashboard HTTP/HTTPS**: `8080/tcp` o `8443/tcp`
- **Canal de comunicación de sync**: `51820/tcp` por defecto, configurable

> Nota: usar el mismo número `51820` en TCP y UDP es válido si se desea mantener una convención simple, porque son protocolos distintos. Aun así, debe ser configurable.

### Variables sugeridas

```env
WG_PORT_UDP=51820
DASHBOARD_PORT_TCP=8080
SYNC_PORT_TCP=51820
```

---

## Modos de cliente

El sistema debe clasificar los clientes en 3 modos operativos.

### 1. Cliente gestionado (Managed)
Cliente que tiene instalado un agente del proyecto.

Capacidades:
- recibe cambios de configuración
- reporta estado
- reporta versión aplicada
- puede aplicar cambios automáticamente

Ejemplos:
- Windows con agente
- Linux con agente
- Router Linux/OpenWrt con agente
- futuras integraciones con OPNsense o MikroTik si se desarrolla soporte

### 2. Cliente estándar manual (Standard Manual)
Cliente WireGuard clásico, sin agente.

Capacidades:
- recibe `.conf`
- recibe QR
- no sincroniza en caliente
- requiere reimportar o reemplazar la configuración cuando cambia

Ejemplos:
- app oficial WireGuard en iOS
- app oficial WireGuard en Android
- cliente WireGuard estándar en desktop sin agente

### 3. Cliente async / desalineado (Out of Sync)
Cliente cuyo estado esperado y aplicado no coincide.

Esto puede ocurrir en dos escenarios:
- cliente gestionado que no aplicó aún la última versión
- cliente manual cuya configuración fue regenerada y todavía no fue reimportada por el usuario

---

## Estados a mostrar en el dashboard

Cada peer debe mostrar al menos:

- **Estado de conexión**:
  - online
  - offline
  - unknown

- **Estado de sincronización**:
  - synced
  - pending
  - out_of_sync
  - manual
  - unsupported

- **Tipo de conexión**:
  - managed-agent
  - wireguard-manual
  - qr-mobile
  - branch-router
  - legacy-imported

- **Versión deseada**
- **Versión aplicada**
- **Último heartbeat**
- **Último handshake WireGuard**
- **Última actualización de config**

### Ejemplo de tabla de estados

| Peer          | Tipo conexión    | Estado VPN | Sync State   | Desired | Applied | Último heartbeat | Último handshake |
|---------------|------------------|------------|--------------|---------|---------|------------------|------------------|
| road1         | managed-agent    | online     | synced       | 12      | 12      | 10s              | 8s               |
| road2         | qr-mobile        | online     | manual       | 7       | 6       | n/a              | 1m               |
| branch-norte  | branch-router    | online     | pending      | 15      | 14      | 30s              | 12s              |
| road3         | wireguard-manual | offline    | out_of_sync  | 4       | unknown | n/a              | 3d               |

---

## Arquitectura propuesta

### Componentes

#### 1. Dashboard / API
Responsable de:
- login
- gestión de peers
- grupos y zonas
- generación de configuraciones
- visualización de estados
- emisión de eventos de sync

#### 2. Motor de configuración
Responsable de:
- traducir permisos/grupos en redes y `AllowedIPs`
- generar config WireGuard
- versionar configuración por peer
- almacenar desired/applied state

#### 3. Broker interno de eventos
Propuesta:
- usar MQTT interno con TLS/mTLS
- no expuesto a Internet
- usado para señalización y heartbeats

#### 4. Agente del cliente
Responsable de:
- autenticarse
- escuchar eventos de cambio
- descargar config desde la API
- aplicar config
- reportar estado y métricas

#### 5. WireGuard dataplane
Responsable solo del túnel:
- peers
- handshakes
- transferencias
- enrutamiento criptográfico

---

## Uso de MQTT

MQTT se propone como **bus interno de eventos**, no como canal principal para secretos completos.

### Uso recomendado
MQTT debe usarse para:
- `config_changed`
- `peer_revoked`
- `heartbeat`
- `apply_result`
- `agent_status`

### No recomendado
No se recomienda enviar por MQTT:
- claves privadas WireGuard
- configuración completa en texto plano
- secretos largos persistentes si no es necesario

### Patrón propuesto
1. El panel detecta un cambio
2. Incrementa `desired_config_version`
3. Publica evento MQTT para ese peer
4. El agente recibe el evento
5. El agente descarga la configuración desde la API HTTPS interna
6. El agente aplica la config
7. El agente confirma estado

---

## Flujo de sincronización

### Flujo base
1. Admin cambia permisos o rutas
2. Backend recalcula config efectiva
3. Se genera nueva versión
4. Se marca el peer como `pending`
5. Se emite evento de cambio
6. El cliente gestionado actualiza
7. El dashboard cambia a `synced`

### Flujo manual
1. Admin cambia permisos o rutas
2. Backend recalcula config efectiva
3. Se genera nueva versión
4. Peer queda marcado como `manual/out_of_sync`
5. Usuario debe descargar nuevo `.conf` o QR

---

## Detección de clientes async

El sistema debe detectar automáticamente desalineación entre estado deseado y estado real.

### Reglas sugeridas

#### Caso 1: cliente gestionado sincronizado
- `desired_version == applied_version`
- heartbeat reciente
- resultado de aplicación OK

Resultado:
- `sync_state = synced`

#### Caso 2: cliente gestionado pendiente
- `desired_version > applied_version`
- heartbeat reciente

Resultado:
- `sync_state = pending`

#### Caso 3: cliente gestionado fuera de sincronía
- `desired_version > applied_version`
- heartbeat antiguo o error de aplicación

Resultado:
- `sync_state = out_of_sync`

#### Caso 4: cliente manual
- cliente sin agente

Resultado:
- `sync_state = manual`

#### Caso 5: cliente no soportado para sync
- tipo de dispositivo no soportado

Resultado:
- `sync_state = unsupported`

---

## Ejemplo visual de etiqueta de estado

Se recomienda mostrar badges en la UI:

- **VPN**: Online / Offline
- **SYNC**: Synced / Pending / Manual / Out of Sync
- **MODE**: Managed / Manual / QR / Router

Ejemplo:

```text
road1
[ONLINE] [SYNCED] [MANAGED]
```

```text
road2
[ONLINE] [MANUAL] [QR-MOBILE]
```

---

## Modelo de datos sugerido

### Tabla `peers`
- id
- name
- peer_type (`roadwarrior`, `branch`)
- connection_mode (`managed-agent`, `wireguard-manual`, `qr-mobile`, `branch-router`)
- sync_supported (bool)
- created_at
- updated_at

### Tabla `peer_configs`
- id
- peer_id
- desired_version
- applied_version
- last_generated_at
- last_applied_at
- last_apply_result
- current_hash

### Tabla `peer_status`
- peer_id
- vpn_status
- sync_state
- last_heartbeat_at
- last_handshake_at
- rx_bytes
- tx_bytes
- last_endpoint

### Tabla `agents`
- id
- peer_id
- agent_version
- certificate_fingerprint
- last_seen_at
- last_error

### Tabla `audit_log`
- id
- peer_id
- action
- result
- created_at

---

## API sugerida

### Registro de agente
`POST /api/v1/agents/register`

Respuesta:
```json
{
  "peer_id": "road1",
  "token": "temporary-or-cert-bound-token",
  "desired_version": 12,
  "sync_mode": "managed-agent"
}
```

### Consultar configuración
`GET /api/v1/agents/me/config`

Headers:
- token/cert client auth
- current version

Respuesta:
- `304 Not Modified` o nueva config

### Confirmar aplicación
`POST /api/v1/agents/me/applied`

```json
{
  "applied_version": 12,
  "result": "ok",
  "details": "wg syncconf successful"
}
```

### Heartbeat
`POST /api/v1/agents/me/heartbeat`

```json
{
  "vpn_status": "online",
  "rx_bytes": 1234567,
  "tx_bytes": 987654,
  "last_handshake_at": "2026-03-31T18:00:00Z"
}
```

---

## Topics MQTT sugeridos

Por peer:

- `wgportal/peer/{peer_id}/config_changed`
- `wgportal/peer/{peer_id}/revoke`
- `wgportal/peer/{peer_id}/status`

Publicación del backend:
- `wgportal/peer/road1/config_changed`

Publicación del agente:
- `wgportal/peer/road1/status`

### ACL recomendada
Cada agente solo debe poder:
- **suscribirse** a sus propios topics de control
- **publicar** en sus propios topics de estado

Ejemplo:
- `road1` puede leer `wgportal/peer/road1/#`
- `road1` puede escribir `wgportal/peer/road1/status`

---

## Ejemplo de implementación: Windows gestionado

### Escenario
- Usuario `road1`
- Tipo `managed-agent`
- Permisos: Planta + Ventas
- Se cambia acceso y se quita Ventas

### Flujo
1. Admin modifica permisos en dashboard
2. Backend genera `desired_version = 13`
3. Backend publica `config_changed`
4. Agente en Windows recibe evento
5. Agente consulta API
6. API devuelve nueva config con solo Planta
7. Agente aplica config
8. Agente reporta `applied_version = 13`
9. UI muestra `Synced`

---

## Ejemplo de implementación: iPhone con QR

### Escenario
- Usuario `road2`
- Tipo `qr-mobile`
- Permisos actuales: Planta + Ventas
- Se quita Ventas

### Flujo
1. Admin modifica permisos
2. Backend genera `desired_version = 8`
3. Peer marcado como `manual`
4. UI muestra:
   - estado VPN actual según handshake
   - sync state = `manual`
   - applied_version = 7
   - desired_version = 8
5. Usuario debe escanear nuevo QR

---

## Ejemplo de implementación: Branch Office

### Escenario
- `branch-norte`
- router Linux con agente
- anuncia `192.168.50.0/24`
- obtiene nuevo permiso hacia red ERP

### Flujo
1. Se actualiza política
2. Se recalculan rutas
3. Se genera nueva versión
4. Agente recibe evento
5. Descarga nueva config
6. Aplica cambios de WireGuard
7. Reporta OK

---

## Aplicación de configuración

### Linux
Se puede usar:
- `wg syncconf`
- `wg setconf`
- regeneración controlada de archivo

### Windows
Opciones:
- integración con cliente WireGuard
- servicio helper
- reescritura controlada de túnel gestionado

### Routers
- integración específica por plataforma
- scripts
- API del vendor
- modo manual si no existe soporte gestionado

---

## Docker Compose de referencia

```yaml
version: "3.9"

services:
  dashboard:
    image: wgportal/dashboard:dev
    ports:
      - "${DASHBOARD_PORT_TCP:-8080}:8080"
    environment:
      - DATABASE_URL=sqlite:////data/app.db
      - SYNC_BROKER_HOST=broker
      - SYNC_BROKER_PORT=${SYNC_PORT_TCP:-51820}
    volumes:
      - ./data:/data

  broker:
    image: eclipse-mosquitto:2
    ports:
      - "${SYNC_PORT_TCP:-51820}:51820"
    volumes:
      - ./mosquitto:/mosquitto
    command: ["/usr/sbin/mosquitto", "-c", "/mosquitto/config/mosquitto.conf"]

  wireguard:
    image: lscr.io/linuxserver/wireguard:latest
    cap_add:
      - NET_ADMIN
      - SYS_MODULE
    ports:
      - "${WG_PORT_UDP:-51820}:51820/udp"
    volumes:
      - ./wireguard:/config
```

---

## Ejemplo de configuración Mosquitto

```conf
listener 51820
allow_anonymous false

cafile /mosquitto/certs/ca.crt
certfile /mosquitto/certs/server.crt
keyfile /mosquitto/certs/server.key

require_certificate true
use_identity_as_username true
acl_file /mosquitto/config/aclfile
```

---

## Ventajas de esta arquitectura

- mantiene WireGuard como dataplane simple
- agrega sync opcional sin romper compatibilidad
- soporta clientes manuales y gestionados
- da visibilidad clara del estado real
- permite escalar a futuro
- facilita operación por sysadmins

---

## Riesgos y mitigaciones

### Riesgo: cliente sin soporte de sync
Mitigación:
- modo manual
- reemisión de config
- estado visible en dashboard

### Riesgo: agente desactualizado
Mitigación:
- versión reportada
- alerta en UI
- compatibilidad mínima declarada

### Riesgo: inyección de mensajes en MQTT
Mitigación:
- TLS/mTLS
- ACL por topic
- broker interno
- MQTT solo para eventos

### Riesgo: configuraciones inconsistentes
Mitigación:
- desired vs applied version
- rollback
- auditoría
- hash de config

---

## Roadmap sugerido

### Fase 1
- dashboard
- peers manuales
- generación `.conf`
- QR
- desired/applied version
- estados básicos

### Fase 2
- agente gestionado Linux/Windows
- polling HTTP o sync simple
- estados `synced/pending/manual`

### Fase 3
- broker MQTT interno
- push de eventos
- métricas de agentes
- branch routers gestionados

### Fase 4
- soporte expandido a más plataformas
- mapas visuales
- políticas avanzadas
- observabilidad histórica

---

## Recomendación final

Para la próxima versión del proyecto, se recomienda implementar el sistema de sincronización como una **capa opcional de gestión**, con las siguientes decisiones clave:

1. **Puerto de sync separado del dashboard**
2. **WireGuard separado del canal de control**
3. **Compatibilidad con clientes gestionados y no gestionados**
4. **Detección explícita de clientes async**
5. **Visualización del tipo de conexión en la UI**
6. **Versionado desired/applied por peer**
7. **MQTT solo como bus seguro de eventos internos**

Esto permite una evolución ordenada del proyecto sin perder compatibilidad con WireGuard estándar y manteniendo una experiencia simple para administración diaria.
