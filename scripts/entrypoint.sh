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

echo "==> Starting NetLoom dashboard on :7777"
exec uvicorn app.main:app --host 0.0.0.0 --port 7777 --workers 1
