"""
User Manager - Add, remove, change password, rename, export profiles.
"""

import sqlite3
import subprocess
import crypt
import uuid
from pathlib import Path
from typing import List, Dict, Optional
from core.config import InstallConfig
from core.logger import get_logger


class UserManager:
    """Manage VPN users."""

    def __init__(self, config: InstallConfig):
        self.config = config
        self.logger = get_logger()
        self.db_path = Path(config.user_db)
        self.pki_dir = Path(config.pki_dir)
        self.profiles_dir = Path(config.profiles_dir)
        self.web_dir = Path(config.web_dir)

    def list_users(self) -> List[Dict]:
        """List all users from database."""
        if not self.db_path.exists():
            return []

        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def add_user(self, name: str, username: str, password: str) -> str:
        """Add a new VPN user."""
        # Check if user exists
        users = self.list_users()
        if any(u["name"] == name for u in users):
            raise ValueError(f"User with name '{name}' already exists")
        if any(u["username"] == username for u in users):
            raise ValueError(f"User with username '{username}' already exists")

        # Create PAM user
        self._create_pam_user(username, password)

        # Generate client certificate
        self._generate_client_cert(username)

        # Read generated cert/key
        client_cert = (self.pki_dir / "issued" / f"{username}.crt").read_text()
        client_key = (self.pki_dir / "private" / f"{username}.key").read_text()

        # Get cert serial
        result = subprocess.run([
            "openssl", "x509", "-in", str(self.pki_dir / "issued" / f"{username}.crt"),
            "-noout", "-serial"
        ], capture_output=True, text=True)
        cert_serial = result.stdout.strip().replace("serial=", "") if result.returncode == 0 else ""

        # Hash password
        password_hash = crypt.crypt(password, crypt.mksalt(crypt.METHOD_SHA512))

        # Store in database
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO users (name, username, password_hash, client_cert, client_key, cert_serial, revoked)
                VALUES (?, ?, ?, ?, ?, ?, 0)
            """, (name, username, password_hash, client_cert, client_key, cert_serial))
            conn.commit()
        finally:
            conn.close()

        # Generate and save .ovpn profile
        profile_path = self._generate_profile(name, username, client_cert, client_key)

        self.logger.info(f"Added user: {name} ({username})")
        return profile_path

    def remove_user(self, name: str):
        """Remove a VPN user (revoke cert, delete PAM user)."""
        user = self._get_user(name)
        if not user:
            raise ValueError(f"User '{name}' not found")

        username = user["username"]

        # Revoke certificate
        self._revoke_cert(username)

        # Delete PAM user
        self._run_cmd(["userdel", "-f", username], check=False)

        # Mark revoked in database
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET revoked=1 WHERE name=?", (name,))
            conn.commit()
        finally:
            conn.close()

        # Remove profile files
        for path in [self.profiles_dir / f"{name}.ovpn", self.web_dir / f"{name}.ovpn"]:
            if path.exists():
                path.unlink()

        self.logger.info(f"Removed user: {name} ({username})")

    def change_password(self, name: str, new_password: str):
        """Change user's VPN password."""
        user = self._get_user(name)
        if not user:
            raise ValueError(f"User '{name}' not found")

        username = user["username"]

        # Update PAM password
        self._run_cmd(["chpasswd"], input_data=f"{username}:{new_password}")

        # Update database
        password_hash = crypt.crypt(new_password, crypt.mksalt(crypt.METHOD_SHA512))
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET password_hash=? WHERE name=?", (password_hash, name))
            conn.commit()
        finally:
            conn.close()

        self.logger.info(f"Changed password for: {name} ({username})")

    def rename_user(self, old_name: str, new_name: str):
        """Rename user (profile name only, not username)."""
        user = self._get_user(old_name)
        if not user:
            raise ValueError(f"User '{old_name}' not found")

        # Check new name not taken
        users = self.list_users()
        if any(u["name"] == new_name for u in users):
            raise ValueError(f"User with name '{new_name}' already exists")

        # Update database
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET name=? WHERE name=?", (new_name, old_name))
            conn.commit()
        finally:
            conn.close()

        # Rename profile files
        for src, dst in [
            (self.profiles_dir / f"{old_name}.ovpn", self.profiles_dir / f"{new_name}.ovpn"),
            (self.web_dir / f"{old_name}.ovpn", self.web_dir / f"{new_name}.ovpn"),
        ]:
            if src.exists():
                src.rename(dst)

        self.logger.info(f"Renamed user: {old_name} -> {new_name}")

    def export_profile(self, name: str) -> str:
        """Export user profile (regenerate .ovpn)."""
        user = self._get_user(name)
        if not user:
            raise ValueError(f"User '{name}' not found")

        profile_path = self._generate_profile(
            name, user["username"], user["client_cert"], user["client_key"]
        )
        return profile_path

    def _get_user(self, name: str) -> Optional[Dict]:
        """Get user by name."""
        users = self.list_users()
        for u in users:
            if u["name"] == name:
                return u
        return None

    def _create_pam_user(self, username: str, password: str):
        """Create PAM system user."""
        # Check if exists
        result = self._run_cmd(["id", username], check=False)
        if result.returncode == 0:
            # Update password
            self._run_cmd(["chpasswd"], input_data=f"{username}:{password}")
            return

        self._run_cmd(["useradd", "-M", "-s", "/usr/sbin/nologin", username])
        self._run_cmd(["chpasswd"], input_data=f"{username}:{password}")

    def _generate_client_cert(self, username: str):
        """Generate client certificate via Easy-RSA."""
        self._run_cmd(["./easyrsa", "--batch", "build-client-full", username, "nopass"], cwd=str(self.pki_dir))

    def _revoke_cert(self, username: str):
        """Revoke client certificate and regenerate CRL."""
        self._run_cmd(["./easyrsa", "--batch", "revoke", username], cwd=str(self.pki_dir))
        self._run_cmd(["./easyrsa", "gen-crl"], cwd=str(self.pki_dir))

        # Copy CRL to OpenVPN directory
        self._run_cmd(["cp", str(self.pki_dir / "crl.pem"), "/etc/openvpn/crl.pem"])

        # Reload OpenVPN to pick up new CRL
        self._run_cmd(["systemctl", "reload", "openvpn@server"], check=False)

    def _generate_profile(self, name: str, username: str, client_cert: str, client_key: str) -> str:
        """Generate .ovpn profile for user."""
        from steps.client_profile import ClientProfileStep
        step = ClientProfileStep()

        ovpn_content = step.CLIENT_OVPN
        ovpn_content = ovpn_content.replace("{{server_ip}}", self.config.server_ip)

        ca_crt = (self.pki_dir / "ca.crt").read_text()
        ta_key = (self.pki_dir / "ta.key").read_text()

        ovpn_content = ovpn_content.replace("{{ca_crt}}", ca_crt.strip())
        ovpn_content = ovpn_content.replace("{{client_crt}}", client_cert.strip())
        ovpn_content = ovpn_content.replace("{{client_key}}", client_key.strip())
        ovpn_content = ovpn_content.replace("{{ta_key}}", ta_key.strip())

        # Ensure directories exist
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.web_dir.mkdir(parents=True, exist_ok=True)

        # Write profile
        profile_path = self.profiles_dir / f"{name}.ovpn"
        profile_path.write_text(ovpn_content)
        profile_path.chmod(0o600)

        # Copy to web
        web_profile = self.web_dir / f"{name}.ovpn"
        web_profile.write_text(ovpn_content)
        web_profile.chmod(0o644)

        return str(profile_path)

    def _run_cmd(self, cmd: list, check: bool = True, cwd: str = None, input_data: str = None):
        """Run command with logging."""
        from steps.base import BaseStep
        step = BaseStep()
        return step._run_cmd(cmd, check=check, cwd=cwd)