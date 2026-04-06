#!/usr/bin/env python3
"""
Script to create branch office peers.
Run from the backend/ directory:
    python ../scripts/create-branch-offices.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import SessionLocal
from app.models.user import User
from app.schemas.peer import BranchOfficeCreate
from app.services import peer_service

BRANCH_OFFICES = [
    {"name": "Distribuidora",  "remote_subnets": ["192.168.200.0/24"]},
    {"name": "Carniceria 1",   "remote_subnets": ["192.168.201.0/24"]},
    {"name": "Carniceria 2",   "remote_subnets": ["192.168.202.0/24"]},
    {"name": "Carniceria 3",   "remote_subnets": ["192.168.203.0/24"]},
    {"name": "Carniceria 4",   "remote_subnets": ["192.168.204.0/24"]},
    {"name": "Carniceria 5",   "remote_subnets": ["192.168.205.0/24"]},
    {"name": "UNCOGA Feedlot", "remote_subnets": ["192.168.68.0/24"]},
]

db = SessionLocal()
try:
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        print("ERROR: admin user not found — run init-db.py first")
        sys.exit(1)

    for bo in BRANCH_OFFICES:
        existing = peer_service.list_peers(db, peer_type="branch_office")
        if any(p.name == bo["name"] for p in existing):
            print(f"    - {bo['name']} already exists, skipping")
            continue

        data = BranchOfficeCreate(
            name=bo["name"],
            device_type="router",
            remote_subnets=bo["remote_subnets"],
        )
        peer = peer_service.create_branch_office(db, data, created_by=admin.id)
        print(f"    ✓ {peer.name} created — VPN IP: {peer.assigned_ip}  subnet: {bo['remote_subnets'][0]}")

    print("\nDone.")
finally:
    db.close()
