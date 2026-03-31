#!/usr/bin/env python3
"""
CLI script to initialise the NetLoom database outside of Docker.
Run from the backend/ directory:
    python ../scripts/init-db.py
"""
import sys
import os

# Allow running from repo root or backend/ dir
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import Base, SessionLocal, engine
from app.services.auth_service import create_admin_user, create_server_config

print("==> Creating database tables...")
Base.metadata.create_all(bind=engine)

db = SessionLocal()
try:
    print("==> Initialising admin user...")
    create_admin_user(db)

    print("==> Initialising server config...")
    create_server_config(db)

    print("==> Done. Login with admin / (your NETLOOM_ADMIN_PASSWORD setting, default: admin123)")
finally:
    db.close()
