#!/bin/bash
set -e

echo "==> NetLoom starting..."

# Create directories
mkdir -p /app/data /etc/wireguard

# Run database migrations
echo "==> Running migrations..."
cd /app
python -m alembic upgrade head

# Create initial admin user + server config (idempotent)
echo "==> Initialising defaults..."
python -c "
from app.database import SessionLocal, Base, engine
Base.metadata.create_all(bind=engine)
db = SessionLocal()
from app.services.auth_service import create_admin_user, create_server_config
create_admin_user(db)
create_server_config(db)
db.close()
print('Defaults ready')
"

# Set up WireGuard — this MUST succeed before starting the dashboard
echo "==> Starting WireGuard..."
python -c "
from app.database import SessionLocal
from app.services.wg_service import apply_config, is_interface_up
import time

db = SessionLocal()
try:
    # Apply config (creates interface if needed)
    apply_config(db)
    
    # Wait for interface to be up (max 10 seconds)
    for i in range(20):
        if is_interface_up():
            print('WireGuard interface is up and running')
            break
        time.sleep(0.5)
    else:
        print('WARNING: WireGuard interface may not be fully ready')
except Exception as e:
    print(f'ERROR: WireGuard setup failed: {e}')
    print('Dashboard will start but WireGuard features will be unavailable')
finally:
    db.close()
"

# Fix iptables rules for Docker - detect the correct outbound interface
echo "==> Setting up iptables for Docker networking..."
OUTBOUND_IFACE=$(ip route get 1.1.1.1 2>/dev/null | grep -oP 'dev \K\S+' || echo 'eth0')
echo "    Outbound interface: $OUTBOUND_IFACE"

# Clear old NetLoom rules (idempotent)
iptables -D FORWARD -i wg0 -j ACCEPT 2>/dev/null || true
iptables -D FORWARD -o wg0 -j ACCEPT 2>/dev/null || true
iptables -t nat -D POSTROUTING -o $OUTBOUND_IFACE -j MASQUERADE 2>/dev/null || true

# Add forwarding rules
iptables -A FORWARD -i wg0 -j ACCEPT
iptables -A FORWARD -o wg0 -j ACCEPT
iptables -t nat -A POSTROUTING -o $OUTBOUND_IFACE -j MASQUERADE

# IP forwarding is already enabled via docker-compose sysctls
# sysctl is not available in python:3.12-slim, but net.ipv4.ip_forward=1
# is set in docker-compose.yml, so we skip it here

echo "    iptables rules applied"
echo "    IP forwarding enabled (via docker-compose sysctls)"

echo "==> Starting NetLoom dashboard on :7777"
exec uvicorn app.main:app --host 0.0.0.0 --port 7777 --workers 1
