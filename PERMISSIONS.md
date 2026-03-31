# NetLoom — Modelo de Permisos y Ruteo

## Visión General

NetLoom usa un modelo de **permisos declarativos** basado en **Zonas**, **Grupos** y **Políticas** que se compilan automáticamente en las rutas de WireGuard (`AllowedIPs`).

### Filosofía: Allow-All por Defecto

- **Peers sin grupos** → acceso total a todas las zonas y redes
- **Peers con grupos** → solo acceden a lo que sus políticas permiten
- **Para restringir**: sacar del grupo "All", meter en grupos específicos

---

## Conceptos Clave

### 1. Zonas (Zones)

Una **Zona** es un conjunto de redes de destino accesibles por VPN.

```
Ejemplo:
  Zona "LAN Server" → 192.168.1.0/24
  Zona "Ventas"     → 10.10.20.0/24
  Zona "Planta"     → 10.10.10.0/24
```

Cada zona puede tener múltiples redes (CIDRs).

### 2. Grupos (Groups)

Un **Grupo** es un perfil de acceso. Los peers se asignan a grupos.

```
Ejemplo:
  Grupo "All"       → Acceso total (default para todos)
  Grupo "soporte"   → Acceso a Planta + Ventas
  Grupo "gerencia"  → Acceso a todo
```

### 3. Políticas (Policies)

Una **Política** conecta un Grupo con una Zona: `Grupo → Zona = allow/deny`

```
Ejemplo:
  soporte → Planta  = allow
  soporte → Ventas  = allow
  soporte → Gerencia = deny
```

### 4. Peer Overrides (Excepciones por Peer)

Permiten dar o quitar acceso a un peer específico, sin importar sus grupos.

```
Ejemplo:
  Juan → Zona Gerencia = allow (override manual)
```

---

## Precedencia (Deny-First)

Cuando se compilan los `AllowedIPs` para un peer, el orden de prioridad es:

| Prioridad | Tipo | Descripción |
|-----------|------|-------------|
| 1 | `deny_manual` | Override manual del peer = deny (siempre gana) |
| 2 | `allow_manual` | Override manual del peer = allow |
| 3 | `deny_group` | Política deny del grupo |
| 4 | `allow_group` | Política allow del grupo |
| 5 | `allow_all` | **Default**: si el peer NO tiene grupos, accede a TODO |

---

## Flujo de Onboarding

Al primer login, después de cambiar la contraseña, se ejecuta el wizard:

### Paso 1: Bienvenida
Explica el modelo de permisos y los 3 pasos del setup.

### Paso 2: Configurar LAN del Servidor
Se ingresa el CIDR de la red local del servidor (ej: `192.168.1.0/24`).

### Paso 3: Creación Automática
El sistema crea:

1. **Zona "LAN Server"** con el CIDR ingresado
2. **Grupo "All"** con descripción explicativa
3. **Política**: All → LAN Server = `allow`
4. Marca `onboarding_completed = True` en el usuario

### Resultado
Todos los peers nuevos tienen acceso completo a la LAN del servidor por defecto.

---

## Cómo Restringir Acceso

### Escenario: Juan solo debe acceder a Planta

1. Ir a **Peers** → clic en el ícono Shield (🛡️) de Juan
2. **Desmarcar** el grupo "All"
3. **Marcar** el grupo "soporte" (que tiene política allow → Planta)
4. Guardar
5. **Re-descargar** el `.conf` de Juan (los AllowedIPs se actualizan)

### Escenario: Agregar una nueva red restringida

1. Ir a **Zones** → crear zona "RRHH" → agregar red `10.10.30.0/24`
2. Ir a **Groups** → crear grupo "rrhh"
3. Ir a **Policies** → crear política rrhh → RRHH = `allow`
4. Asignar peers al grupo "rrhh"

---

## Ruteo entre Peers (NetMaker-Style)

### RoadWarrior → Branch Office LAN

Cuando un branch office tiene `remote_subnets` configurados (ej: `192.168.67.0/24`), esos CIDRs se incluyen automáticamente en los `AllowedIPs` de los peers que tienen acceso.

```
Branch "Salamines":
  VPN IP: 100.169.0.3/32
  Remote Subnets: 192.168.67.0/24

Juan (roadwarrior) AllowedIPs:
  100.169.0.3/32,        # IP VPN de Salamines
  192.168.1.0/24,        # LAN Server
  192.168.67.0/24        # LAN de Salamines
```

### Server → Peer LAN

El servidor siempre conoce las rutas de todos los peers porque su `wg0.conf` incluye los `AllowedIPs` de cada peer:

```
[Peer]
# Salamines
PublicKey = ...
AllowedIPs = 100.169.0.3/32, 192.168.67.0/24
```

---

## Arquitectura de Compilación

```
┌─────────────────────────────────────────────────────────┐
│                    Policy Compiler                       │
│                                                          │
│  compile_client_allowed_ips(peer_id)                     │
│  ├── compile_allowed_cidrs(peer_id)  → zonas permitidas  │
│  └── compile_peer_routes(peer_id)    → rutas a branches  │
│                                                          │
│  Resultado: lista de CIDRs para AllowedIPs del cliente   │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│              Client Config (.conf)                       │
│                                                          │
│  [Interface]                                             │
│  PrivateKey = ...                                        │
│  Address = 100.169.0.2/32                                │
│                                                          │
│  [Peer]                                                  │
│  PublicKey = <server>                                    │
│  Endpoint = vpn.example.com:51820                        │
│  AllowedIPs = 192.168.1.0/24, 192.168.67.0/24           │
└─────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### Peer no puede hacer ping a una red

1. Verificar que la red esté en una **Zona**
2. Verificar que el peer esté en un **Grupo** con política `allow` a esa zona
3. **Re-descargar** el `.conf` del peer (los AllowedIPs cambian)
4. Re-importar la config en el cliente WireGuard

### Peer tiene `0.0.0.0/32` en AllowedIPs

Significa que no tiene zonas asignadas. Soluciones:
- Si no se completó el onboarding: completar el wizard
- Si ya se completó: asignar el peer a un grupo con políticas

### Cambios en grupos/políticas no se reflejan

Los `AllowedIPs` se calculan al momento de generar el `.conf`. Después de cambiar grupos o políticas:
1. Ir a **Peers**
2. Descargar nuevamente el `.conf` del peer
3. Re-importar en el cliente WireGuard

---

## Endpoints de Onboarding

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/api/onboarding/complete` | Completa el wizard (crea zona, grupo, política) |
| `GET` | `/api/onboarding/status` | Verifica si el onboarding fue completado |

### Request Body (POST /api/onboarding/complete)

```json
{
  "server_lan_cidr": "192.168.1.0/24",
  "server_lan_name": "LAN Server"
}
```

### Response

```json
{
  "success": true,
  "message": "Onboarding completed. All peers will have full access by default.",
  "zone_id": 1,
  "group_id": 1,
  "policy_id": 1
}
```
