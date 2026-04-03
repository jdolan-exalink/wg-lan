"""add cascade delete to connection_logs peer_id

Revision ID: k4l5m6n7o8p9
Revises: j3k4l5m6n7o8
Create Date: 2026-04-02
"""
from alembic import op
import sqlalchemy as sa

revision = "k4l5m6n7o8p9"
down_revision = "j3k4l5m6n7o8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("PRAGMA foreign_keys = OFF")
    op.execute("ALTER TABLE connection_logs RENAME TO connection_logs_old")
    op.execute("""
        CREATE TABLE connection_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            peer_id INTEGER REFERENCES peers(id) ON DELETE CASCADE,
            peer_name TEXT,
            peer_ip TEXT,
            event_type TEXT NOT NULL,
            severity TEXT NOT NULL DEFAULT 'info',
            message TEXT NOT NULL,
            details TEXT,
            source_ip TEXT,
            duration_ms INTEGER
        )
    """)
    op.execute("INSERT INTO connection_logs SELECT * FROM connection_logs_old")
    op.execute("DROP TABLE connection_logs_old")
    op.execute("PRAGMA foreign_keys = ON")


def downgrade() -> None:
    op.execute("PRAGMA foreign_keys = OFF")
    op.execute("ALTER TABLE connection_logs RENAME TO connection_logs_old")
    op.execute("""
        CREATE TABLE connection_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            peer_id INTEGER,
            peer_name TEXT,
            peer_ip TEXT,
            event_type TEXT NOT NULL,
            severity TEXT NOT NULL DEFAULT 'info',
            message TEXT NOT NULL,
            details TEXT,
            source_ip TEXT,
            duration_ms INTEGER,
            FOREIGN KEY (peer_id) REFERENCES peers(id)
        )
    """)
    op.execute("INSERT INTO connection_logs SELECT * FROM connection_logs_old")
    op.execute("DROP TABLE connection_logs_old")
    op.execute("PRAGMA foreign_keys = ON")