#!/bin/bash
# Reset the admin user password to a new value.
# Usage: ./scripts/reset-admin-password.sh [new_password]
# If no password is provided, a random one will be generated.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

NEW_PASSWORD="${1:-}"

if [ -z "$NEW_PASSWORD" ]; then
    NEW_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))")
    echo "No password provided. Generated: $NEW_PASSWORD"
fi

python3 - "$NEW_PASSWORD" <<'PYEOF'
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath('.')))

from app.database import SessionLocal
from app.models.user import User
from app.services.auth_service import hash_password

new_password = sys.argv[1]
db = SessionLocal()
try:
    admin = db.query(User).filter(User.username == 'admin').first()
    if not admin:
        print('ERROR: admin user not found in database')
        sys.exit(1)
    
    admin.password_hash = hash_password(new_password)
    admin.must_change_password = False
    db.commit()
    
    print('========================================')
    print('  Admin password reset successfully')
    print('========================================')
    print(f'  Username: admin')
    print(f'  Password: {new_password}')
    print('========================================')
    print('  The user will NOT be required to change')
    print('  the password on next login.')
    print('========================================')
finally:
    db.close()
PYEOF
