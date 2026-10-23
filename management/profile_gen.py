"""
Profile Generator - Generate client .ovpn profiles.
"""

from pathlib import Path
from core.config import InstallConfig
from core.logger import get_logger


class ProfileGenerator:
    """Generate OpenVPN client profiles."""

    CLIENT_OVPN = """client
dev tun
proto tcp-client
remote {{server_ip}} 443
nobind
persist-key
persist-tun
remote-cert-tls server
cipher AES-256-GCM
auth SHA384
tls-version-min 1.3
tls-ciphersuites TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256
auth-user-pass
verb 3
mute 20
sndbuf 0
rcvbuf 0

<ca>
{{ca_crt}}
</ca>

<cert>
{{client_crt}}
</cert>

<key>
{{client_key}}
</key>

<tls-crypt>
{{ta_key}}
</tls-crypt>
"""

    def __init__(self, config: InstallConfig):
        self.config = config
        self.logger = get_logger()
        self.pki_dir = Path(config.pki_dir)

    def generate(self, name: str, username: str, client_cert: str, client_key: str) -> str:
        """Generate .ovpn profile content."""
        ca_crt = (self.pki_dir / "ca.crt").read_text()
        ta_key = (self.pki_dir / "ta.key").read_text()

        content = self.CLIENT_OVPN
        content = content.replace("{{server_ip}}", self.config.server_ip)
        content = content.replace("{{ca_crt}}", ca_crt.strip())
        content = content.replace("{{client_crt}}", client_cert.strip())
        content = content.replace("{{client_key}}", client_key.strip())
        content = content.replace("{{ta_key}}", ta_key.strip())

        return content

    def save_profile(self, name: str, content: str) -> Path:
        """Save profile to disk."""
        self.config.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.config.web_dir.mkdir(parents=True, exist_ok=True)

        profile_path = Path(self.config.profiles_dir) / f"{name}.ovpn"
        web_path = Path(self.config.web_dir) / f"{name}.ovpn"

        profile_path.write_text(content)
        profile_path.chmod(0o600)

        web_path.write_text(content)
        web_path.chmod(0o644)

        return profile_path