"""
Step 10: Store User Record in SQLite Database
"""

import asyncio
import sqlite3
import hashlib
import time
from typing import Callable
from pathlib import Path
from core.config import InstallConfig
from steps.base import BaseStep
from core.logger import get_logger


class UserDBStep(BaseStep):
    """Store user record in SQLite database for management."""

    @property
    def name(self) -> str:
        return "user_db"

    @property
    def display_name(self) -> str:
        return "Store User Record in Database"

    @property
    def description(self) -> str:
        return "Save user info, certs, and keys to SQLite for add/remove/change operations"

    async def is_already_done(
        self,
        config: InstallConfig,
    ) -> bool:
        """Check if user database already exists."""
        db_path = Path(config.user_db)
        return db_path.exists()

    async def execute(
        self,
        config: InstallConfig,
        output_callback: Callable[[str], None] = None,
    ) -> bool:
        """Execute user database storage."""

        def log(msg: str):
            if output_callback:
                output_callback(msg)
            self.logger.info(msg)

        db_path = Path(config.user_db)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        log("Initializing user database...")
        self._init_db(db_path)

        log("Storing user record...")
        self._store_user(db_path, config)

        log("User record stored successfully")
        return True

    def _init_db(self, db_path: Path):
        """Initialize SQLite database schema."""
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                client_cert TEXT,
                client_key TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                revoked BOOLEAN DEFAULT 0,
                cert_serial TEXT
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_name ON users(name)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)
        """)

        conn.commit()
        conn.close()

        # Secure permissions
        db_path.chmod(0o600)

    def _store_user(self, db_path: Path, config: InstallConfig):
        """Store user record in database."""
        pki_dir = Path(config.pki_dir)

        # Read cert and key
        client_cert = (pki_dir / "issued" / f"{config.vpn_user}.crt").read_text()
        client_key = (pki_dir / "private" / f"{config.vpn_user}.key").read_text()

        # Get cert serial
        import subprocess
        result = subprocess.run([
            "openssl", "x509", "-in", str(pki_dir / "issued" / f"{config.vpn_user}.crt"),
            "-noout", "-serial"
        ], capture_output=True, text=True)
        cert_serial = result.stdout.strip().replace("serial=", "") if result.returncode == 0 else ""

        # Hash password (SHA-512 crypt format like chpasswd)
        import crypt
        password_hash = crypt.crypt(config.vpn_pass, crypt.mksalt(crypt.METHOD_SHA512))

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO users (name, username, password_hash, client_cert, client_key, cert_serial, revoked)
                VALUES (?, ?, ?, ?, ?, ?, 0)
            """, (
                config.client_name,
                config.vpn_user,
                password_hash,
                client_cert,
                client_key,
                cert_serial,
            ))
            conn.commit()
        finally:
            conn.close()

    async def rollback(self, config: InstallConfig, rollback_data: dict) -> bool:
        """Mark user as revoked in database."""
        db_path = Path(config.user_db)
        if not db_path.exists():
            return True

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET revoked=1 WHERE name=?", (config.client_name,))
            conn.commit()
        finally:
            conn.close()
        return True