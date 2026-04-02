#!/bin/bash
set -e

echo "==> NetLoom starting..."

# Validate required environment variables
REQUIRED_VARS="NETLOOM_SECRET_KEY NETLOOM_ADMIN_PASSWORD NETLOOM_SERVER_ENDPOINT NETLOOM_SERVER_PORT NETLOOM_SUBNET"
missing=""
for var in $REQUIRED_VARS; do
    [ -z "${!var}" ] && missing="$missing\n  - $var"
done
if [ -n "$missing" ]; then
    echo "ERROR: Missing required environment variables:$missing"
    echo "       Create a .env file based on .env.example before deploying."
    exit 1
fi

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
from app.services.auth_service import create_admin_user, create_server_config, create_vpn_server_peer
create_admin_user(db)
create_server_config(db)
create_vpn_server_peer(db)
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

# IP forwarding and WireGuard sysctls (host network mode gives us access)
echo "==> Configuring sysctls..."
sysctl -w net.ipv4.ip_forward=1 2>/dev/null || echo "    ip_forward already set or requires host config"
sysctl -w net.ipv4.conf.all.src_valid_mark=1 2>/dev/null || echo "    src_valid_mark already set or requires host config"
sysctl -w net.ipv4.conf.wg0.src_valid_mark=1 2>/dev/null || true

echo "    IP forwarding enabled"

# Generate TLS certificates if needed
if [ "${NETLOOM_TLS_ENABLED:-false}" = "true" ]; then
    echo "==> TLS is enabled, ensuring certificates exist..."
    python -c "
from app.config import settings
from app.utils.tls_cert_generator import ensure_certificates_exist

if settings.tls_auto_generate:
    ensure_certificates_exist(
        cert_path=settings.tls_cert_path,
        key_path=settings.tls_key_path,
        country=settings.tls_country,
        state=settings.tls_state,
        locality=settings.tls_locality,
        organization=settings.tls_organization,
        common_name=settings.tls_common_name,
        days_valid=settings.tls_cert_days,
    )
    print('==> TLS certificates ready')
else:
    print('==> TLS auto-generation disabled, using existing certificates')
"
fi

# Start NetLoom dashboard + Client API
echo "==> Starting NetLoom Client API on HTTP port ${NETLOOM_CLIENT_API_PORT:-7771}"
echo "==> Starting NetLoom Client API on HTTPS port ${NETLOOM_CLIENT_API_TLS_PORT:-7772}"
echo "==> Starting NetLoom dashboard on HTTP port ${NETLOOM_HTTP_PORT:-7777}"

if [ "${NETLOOM_TLS_ENABLED:-false}" = "true" ]; then
    echo "==> Starting NetLoom dashboard on HTTPS port ${NETLOOM_TLS_PORT:-7776}"
    exec python -c "
import uvicorn
import threading
from app.config import settings

# 1. Client API server (HTTP, dedicated port)
client_api_config = uvicorn.Config(
    'app.client_app:app',
    host=settings.host,
    port=settings.client_api_port,
    workers=1,
    loop='asyncio',
    log_config=None,
)

# 2. Client API server (HTTPS, dedicated port)
client_api_tls_config = uvicorn.Config(
    'app.client_app:app',
    host=settings.tls_host,
    port=settings.client_api_tls_port,
    workers=1,
    ssl_keyfile=settings.tls_key_path,
    ssl_certfile=settings.tls_cert_path,
    loop='asyncio',
    log_config=None,
)

# 3. Dashboard HTTP server
http_config = uvicorn.Config(
    'app.main:app',
    host=settings.host,
    port=settings.http_port,
    workers=1,
    loop='asyncio',
    log_config=None,
)

# 4. Dashboard HTTPS server
https_config = uvicorn.Config(
    'app.main:app',
    host=settings.tls_host,
    port=settings.tls_port,
    workers=1,
    ssl_keyfile=settings.tls_key_path,
    ssl_certfile=settings.tls_cert_path,
    loop='asyncio',
    log_config=None,
)

def run_server(config, name):
    server = uvicorn.Server(config)
    print(f'==> {name} started')
    server.run()

# Start Client API HTTP in background thread
client_thread = threading.Thread(target=run_server, args=(client_api_config, 'Client API HTTP'), daemon=True)
client_thread.start()

# Start Client API HTTPS in background thread
client_tls_thread = threading.Thread(target=run_server, args=(client_api_tls_config, 'Client API HTTPS'), daemon=True)
client_tls_thread.start()

# Start Dashboard HTTP in background thread
http_thread = threading.Thread(target=run_server, args=(http_config, 'Dashboard HTTP'), daemon=True)
http_thread.start()

# Run Dashboard HTTPS in main thread
https_server = uvicorn.Server(https_config)
https_server.run()
"
else
    exec python -c "
import uvicorn
import threading
from app.config import settings

# 1. Client API server (HTTP only, dedicated port)
client_api_config = uvicorn.Config(
    'app.client_app:app',
    host=settings.host,
    port=settings.client_api_port,
    workers=1,
    loop='asyncio',
    log_config=None,
)

# 2. Dashboard HTTP server
http_config = uvicorn.Config(
    'app.main:app',
    host=settings.host,
    port=settings.http_port,
    workers=1,
    loop='asyncio',
    log_config=None,
)

def run_server(config, name):
    server = uvicorn.Server(config)
    print(f'==> {name} started')
    server.run()

# Start Client API in background thread
client_thread = threading.Thread(target=run_server, args=(client_api_config, 'Client API'), daemon=True)
client_thread.start()

# Run Dashboard HTTP in main thread
http_server = uvicorn.Server(http_config)
http_server.run()
"
fi
