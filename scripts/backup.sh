#!/bin/bash
# Simple backup script for SQLite DB and WireGuard configs
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./data/backups"
mkdir -p "$BACKUP_DIR"

if [ -f "./data/wg-lan.db" ]; then
  cp "./data/wg-lan.db" "$BACKUP_DIR/wg-lan_$TIMESTAMP.db"
  echo "DB backed up: $BACKUP_DIR/wg-lan_$TIMESTAMP.db"
fi

if [ -d "./config" ]; then
  tar -czf "$BACKUP_DIR/wg-config_$TIMESTAMP.tar.gz" ./config/
  echo "WG configs backed up: $BACKUP_DIR/wg-config_$TIMESTAMP.tar.gz"
fi
