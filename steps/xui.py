"""
Step 3: Deploy 3X-UI with 2 Inbounds
"""

import asyncio
import json
import sqlite3
import subprocess
import time
from typing import Callable
from pathlib import Path
from core.config import InstallConfig
from steps.base import BaseStep
from core.logger import get_logger
from core.exceptions import ConfigError


class XUIStep(BaseStep):
    """Deploy 3X-UI panel with VLESS inbounds."""

    @property
    def name(self) -> str:
        return "xui"

    @property
    def display_name(self) -> str:
        return "Deploy 3X-UI with 2 Inbounds"

    @property
    def description(self) -> str:
        return "Configure 3X-UI SQLite database with VLESS-TLS+xhttp and VLESS-Reality+xhttp inbounds"

    async def is_already_done(
        self,
        config: InstallConfig,
    ) -> bool:
        """Check if 3X-UI is already deployed."""
        db_path = Path(config.xui_db)
        if not db_path.exists():
            return False
        # Check if x-ui command exists
        result = self._run_cmd(["which", "x-ui"], check=False)
        return result.returncode == 0

    async def execute(
        self,
        config: InstallConfig,
        output_callback: Callable[[str], None] = None,
    ) -> bool:
        """Execute 3X-UI deployment."""

        def log(msg: str):
            if output_callback:
                output_callback(msg)
            self.logger.info(msg)

        # Ensure x-ui service is stopped for DB modification
        log("Stopping 3X-UI service...")
        self._systemctl("stop", "x-ui")

        # Wait for DB to be created by 3X-UI
        log("Waiting for 3X-UI database...")
        await self._wait_for_db(config.xui_db)

        # Backup existing DB
        log("Backing up existing 3X-UI database...")
        backup_path = self._backup_file(config.xui_db)

        # Generate inbound configurations
        log("Generating inbound configurations...")
        inbound1 = self._generate_inbound_10000(config)
        inbound2 = self._generate_inbound_443(config)

        # Update database
        log("Updating 3X-UI database...")
        self._update_xui_db(config.xui_db, inbound1, inbound2)

        # Ensure TLS certificates exist for VLESS-TLS
        log("Ensuring TLS certificates...")
        await self._ensure_certificates(config)

        # Restart 3X-UI
        log("Starting 3X-UI service...")
        self._systemctl("enable", "x-ui")
        self._systemctl("start", "x-ui")

        # Wait for service to be ready
        await asyncio.sleep(3)

        # Verify inbounds are active
        log("Verifying inbounds...")
        await self._verify_inbounds(config)

        log("3X-UI deployment complete")
        return True

    async def _wait_for_db(self, db_path: str, timeout: int = 30):
        """Wait for 3X-UI database to exist."""
        start = time.time()
        while not Path(db_path).exists():
            if time.time() - start > timeout:
                raise ConfigError(f"3X-UI database not found at {db_path}")
            await asyncio.sleep(1)

    def _generate_inbound_10000(self, config: InstallConfig) -> dict:
        """Generate VLESS-TLS + xhttp inbound for port 10000."""
        import uuid
        import secrets
        # Generate random path for stealth
        random_path = "/" + secrets.token_urlsafe(12) + "/"
        return {
            "port": config.xui_inbound1_port,
            "listen": "0.0.0.0",
            "protocol": "vless",
            "settings": json.dumps({
                "clients": [{"id": str(uuid.uuid4()), "flow": "xtls-rprx-vision"}],
                "decryption": "none",
            }),
            "streamSettings": json.dumps({
                "network": "xhttp",
                "security": "tls",
                "tlsSettings": {
                    "alpn": ["h2", "http/1.1"],
                    "certificates": [{
                        "certificateFile": config.xui_cert,
                        "keyFile": config.xui_key,
                    }],
                    "serverName": config.domain1,
                },
                "xhttpSettings": {
                    "host": "",
                    "path": random_path,
                    "mode": "auto",
                },
            }),
            "tag": "inbound-10000",
            "remark": "01",
            "enable": True,
        }

    def _generate_inbound_443(self, config: InstallConfig) -> dict:
        """Generate VLESS-Reality + xhttp inbound for port 443 (local)."""
        import uuid
        import secrets

        # Generate Reality keys if not present
        priv_key = self._get_or_generate_reality_key(config)
        short_id = secrets.token_hex(8)
        # Generate random spiderX and path for stealth
        spider_x = "/" + secrets.token_urlsafe(12)
        random_path = "/assets/v" + secrets.token_urlsafe(8)

        return {
            "port": config.xui_inbound2_port,
            "listen": "127.0.0.1",
            "protocol": "vless",
            "settings": json.dumps({
                "clients": [{"id": str(uuid.uuid4()), "flow": "xtls-rprx-vision"}],
                "decryption": "none",
            }),
            "streamSettings": json.dumps({
                "network": "xhttp",
                "security": "reality",
                "realitySettings": {
                    "show": False,
                    "dest": f"{config.reality_domain}:443",
                    "xver": 0,
                    "serverNames": [config.reality_domain],
                    "privateKey": priv_key,
                    "shortIds": [short_id],
                    "spiderX": spider_x,
                },
                "xhttpSettings": {
                    "host": config.reality_domain,
                    "path": random_path,
                    "mode": "auto",
                    "headers": {
                        "User-Agent": ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"],
                        "Accept": ["text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"],
                        "Accept-Language": ["en-US,en;q=0.5"],
                        "Accept-Encoding": ["gzip, deflate, br"],
                        "Upgrade": ["websocket"],
                        "Connection": ["keep-alive, Upgrade"],
                    },
                },
            }),
            "tag": "inbound-443",
            "remark": "02",
            "enable": True,
        }

    def _get_or_generate_reality_key(self, config: InstallConfig) -> str:
        """Get or generate X25519 private key for Reality."""
        key_file = Path("/etc/x-ui/reality_private.key")
        if key_file.exists():
            return key_file.read_text().strip()

        # Generate using xray
        result = self._run_cmd(["xray", "x25519"], check=False)
        if result.returncode == 0:
            # Output format: "Private key: xxx\nPublic key: yyy"
            for line in result.stdout.split('\n'):
                if line.startswith("Private key:"):
                    priv = line.split(":")[1].strip()
                    key_file.write_text(priv)
                    key_file.chmod(0o600)
                    return priv

        # Fallback: generate with Python
        from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
        private_key = X25519PrivateKey.generate()
        priv = private_key.private_bytes_raw().hex()
        key_file.write_text(priv)
        key_file.chmod(0o600)
        return priv

    async def _ensure_certificates(self, config: InstallConfig):
        """Ensure TLS certificates exist for VLESS-TLS."""
        cert_path = Path(config.xui_cert)
        key_path = Path(config.xui_key)

        if cert_path.exists() and key_path.exists():
            self.logger.info("TLS certificates already exist")
            return

        self.logger.info("Generating self-signed TLS certificate for VLESS-TLS...")
        # Generate self-signed cert for the domain
        cmd = [
            "openssl", "req", "-x509", "-newkey", "rsa:2048",
            "-keyout", str(key_path), "-out", str(cert_path),
            "-days", "365", "-nodes", "-subj", f"/CN={config.domain1}",
        ]
        self._run_cmd(cmd)
        cert_path.chmod(0o644)
        key_path.chmod(0o600)

    def _update_xui_db(self, db_path: str, inbound1: dict, inbound2: dict):
        """Update 3X-UI SQLite database with inbound configurations."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            # Check if inbounds table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inbounds'")
            if not cursor.fetchone():
                raise ConfigError("Inbounds table not found in 3X-UI database")

            # Delete existing inbounds with same tags
            cursor.execute("DELETE FROM inbounds WHERE tag IN (?, ?)", ("inbound-10000", "inbound-443"))

            # Insert new inbounds
            for inbound in [inbound1, inbound2]:
                cursor.execute("""
                    INSERT INTO inbounds (port, listen, protocol, settings, streamSettings, tag, remark, enable)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    inbound["port"],
                    inbound["listen"],
                    inbound["protocol"],
                    inbound["settings"],
                    inbound["streamSettings"],
                    inbound["tag"],
                    inbound["remark"],
                    1 if inbound["enable"] else 0,
                ))

            conn.commit()
        finally:
            conn.close()

    async def _verify_inbounds(self, config: InstallConfig):
        """Verify inbounds are listening."""
        import socket
        ports_to_check = [
            (config.xui_inbound1_port, "VLESS-TLS"),
            (config.xui_inbound2_port, "VLESS-Reality"),
        ]

        for port, name in ports_to_check:
            for attempt in range(10):
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex(("127.0.0.1", port))
                    sock.close()
                    if result == 0:
                        self.logger.info(f"  ✓ {name} listening on port {port}")
                        break
                except Exception:
                    pass
                await asyncio.sleep(1)
            else:
                self.logger.warning(f"  ⚠ {name} on port {port} not verified")

    async def rollback(self, config: InstallConfig, rollback_data: dict) -> bool:
        """Restore 3X-UI database from backup."""
        backup_path = rollback_data.get("backup_path")
        if backup_path and Path(backup_path).exists():
            self.logger.info("Restoring 3X-UI database from backup...")
            return self._restore_backup(config.xui_db)
        return False