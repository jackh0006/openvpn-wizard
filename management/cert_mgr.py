"""
Certificate Manager - Certificate lifecycle management.
"""

import subprocess
from pathlib import Path
from core.config import InstallConfig
from core.logger import get_logger


class CertManager:
    """Manage certificate lifecycle (issue, revoke, CRL)."""

    def __init__(self, config: InstallConfig):
        self.config = config
        self.logger = get_logger()
        self.pki_dir = Path(config.pki_dir)

    def issue_client_cert(self, username: str) -> tuple[str, str]:
        """Issue a new client certificate. Returns (cert, key)."""
        # Generate via Easy-RSA
        self._run_easyrsa(["--batch", "build-client-full", username, "nopass"])

        # Read generated files
        cert = (self.pki_dir / "issued" / f"{username}.crt").read_text()
        key = (self.pki_dir / "private" / f"{username}.key").read_text()

        return cert, key

    def revoke_cert(self, username: str):
        """Revoke a client certificate and regenerate CRL."""
        self._run_easyrsa(["--batch", "revoke", username])
        self._run_easyrsa(["gen-crl"])

        # Copy CRL to OpenVPN
        subprocess.run(["cp", str(self.pki_dir / "crl.pem"), "/etc/openvpn/crl.pem"], check=False)

        # Reload OpenVPN
        subprocess.run(["systemctl", "reload", "openvpn@server"], check=False)

    def get_cert_info(self, username: str) -> dict:
        """Get certificate information."""
        cert_path = self.pki_dir / "issued" / f"{username}.crt"
        if not cert_path.exists():
            return {}

        result = subprocess.run([
            "openssl", "x509", "-in", str(cert_path), "-noout", "-subject", "-dates", "-serial"
        ], capture_output=True, text=True)

        info = {}
        for line in result.stdout.split('\n'):
            if '=' in line:
                key, val = line.split('=', 1)
                info[key.strip()] = val.strip()

        return info

    def list_certs(self) -> list:
        """List all issued certificates."""
        issued_dir = self.pki_dir / "issued"
        if not issued_dir.exists():
            return []

        certs = []
        for cert_file in issued_dir.glob("*.crt"):
            username = cert_file.stem
            info = self.get_cert_info(username)
            info["username"] = username
            certs.append(info)

        return certs

    def _run_easyrsa(self, args: list):
        """Run easyrsa command."""
        cmd = ["./easyrsa"] + args
        subprocess.run(cmd, cwd=str(self.pki_dir), check=True, capture_output=True, text=True)