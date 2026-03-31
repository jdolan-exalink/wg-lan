#!/bin/bash
set -e

echo "==> WG-LAN starting..."

# Create directories
mkdir -p /app/data /etc/wireguard

# Run database migrations
echo "==> Running migrations..."
cd /app
python -m alembic upgrade head

# Create initial admin user (idempotent)
echo "==> Initialising admin user..."
python -c "
from app.database import SessionLocal, Base, engine
Base.metadata.create_all(bind=engine)
db = SessionLocal()
from app.services.auth_service import create_admin_user
create_admin_user(db)
db.close()
print('Admin user ready')
"

# Set up WireGuard if server config exists in DB
echo "==> Checking WireGuard state..."
python -c "
from app.database import SessionLocal
from app.models.server_config import ServerConfig
db = SessionLocal()
cfg = db.query(ServerConfig).first()
db.close()
if cfg:
    from app.services.wg_service import apply_config, bring_up, is_interface_up
    db2 = SessionLocal()
    try:
        apply_config(db2)
        if not is_interface_up():
            bring_up()
            print('WireGuard interface up')
        else:
            print('WireGuard already up')
    except Exception as e:
        print(f'WireGuard setup skipped: {e}')
    finally:
        db2.close()
else:
    print('No server config yet — WireGuard will start after first setup via dashboard')
"

echo "==> Starting WG-LAN dashboard on :5000"
exec uvicorn app.main:app --host 0.0.0.0 --port 5000 --workers 1
