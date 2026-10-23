"""
Step 9: Generate Client .ovpn Profile
"""

import asyncio
from typing import Callable
from pathlib import Path
from core.config import InstallConfig
from steps.base import BaseStep
from core.logger import get_logger


class ClientProfileStep(BaseStep):
    """Generate client .ovpn profile with embedded certificates."""

    @property
    def name(self) -> str:
        return "client_profile"

    @property
    def display_name(self) -> str:
        return "Generate Client .ovpn Profile"

    @property
    def description(self) -> str:
        return "Create single-file .ovpn with embedded CA, cert, key, and TLS-crypt"

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

    async def is_already_done(
        self,
        config: InstallConfig,
    ) -> bool:
        """Check if client profile already exists."""
        profile_path = Path(config.profiles_dir) / f"{config.client_name}.ovpn"
        if not profile_path.exists():
            return False
        content = profile_path.read_text()
        return "<ca>" in content and "<cert>" in content and "<key>" in content and "<tls-crypt>" in content

    async def execute(
        self,
        config: InstallConfig,
        output_callback: Callable[[str], None] = None,
    ) -> bool:
        """Execute client profile generation."""

        def log(msg: str):
            if output_callback:
                output_callback(msg)
            self.logger.info(msg)

        pki_dir = Path(config.pki_dir)
        profiles_dir = Path(config.profiles_dir)
        web_dir = Path(config.web_dir)

        # Ensure directories exist
        profiles_dir.mkdir(parents=True, exist_ok=True)
        web_dir.mkdir(parents=True, exist_ok=True)

        log("Reading certificates and keys...")
        ca_crt = (pki_dir / "ca.crt").read_text()
        client_crt = (pki_dir / "issued" / f"{config.vpn_user}.crt").read_text()
        client_key = (pki_dir / "private" / f"{config.vpn_user}.key").read_text()
        ta_key = (pki_dir / "ta.key").read_text()

        log("Generating .ovpn profile...")
        ovpn_content = self.CLIENT_OVPN
        ovpn_content = ovpn_content.replace("{{server_ip}}", config.server_ip)
        ovpn_content = ovpn_content.replace("{{ca_crt}}", ca_crt.strip())
        ovpn_content = ovpn_content.replace("{{client_crt}}", client_crt.strip())
        ovpn_content = ovpn_content.replace("{{client_key}}", client_key.strip())
        ovpn_content = ovpn_content.replace("{{ta_key}}", ta_key.strip())

        # Write to profiles directory
        profile_path = profiles_dir / f"{config.client_name}.ovpn"
        log(f"Writing profile to {profile_path}...")
        profile_path.write_text(ovpn_content)
        profile_path.chmod(0o600)

        # Copy to web directory for download
        web_profile = web_dir / f"{config.client_name}.ovpn"
        log(f"Copying profile to web directory {web_profile}...")
        web_profile.write_text(ovpn_content)
        web_profile.chmod(0o644)

        # Also copy to a simple web server location
        # Ensure nginx or simple HTTP server can serve it
        self._ensure_web_server(config)

        log(f"Client profile generated: {profile_path}")
        log(f"Web download: http://{config.server_ip}/{config.client_name}.ovpn")
        return True

    def _ensure_web_server(self, config: InstallConfig):
        """Ensure a simple web server is available for profile download."""
        # Check if nginx is installed
        result = self._run_cmd(["which", "nginx"], check=False)
        if result.returncode == 0:
            # Configure nginx to serve /var/www/vpn-profiles
            self._configure_nginx(config)
        else:
            # Install nginx
            self.logger.info("Installing nginx for profile downloads...")
            self._run_cmd(["apt-get", "install", "-y", "nginx"])
            self._configure_nginx(config)

    def _configure_nginx(self, config: InstallConfig):
        """Configure nginx to serve profile files."""
        nginx_conf = f"""server {{
    listen 80;
    server_name {config.server_ip};

    location / {{
        root /var/www/vpn-profiles;
        autoindex off;
        try_files $uri $uri/ =404;
    }}
}}"""

        self._write_file("/etc/nginx/sites-available/vpn-profiles", nginx_conf)

        # Enable site
        self._run_cmd(["ln", "-sf", "/etc/nginx/sites-available/vpn-profiles", "/etc/nginx/sites-enabled/"], check=False)
        self._run_cmd(["rm", "-f", "/etc/nginx/sites-enabled/default"], check=False)

        # Test and reload
        self._run_cmd(["nginx", "-t"], check=False)
        self._systemctl("reload", "nginx")

    async def rollback(self, config: InstallConfig, rollback_data: dict) -> bool:
        """Remove generated profile files."""
        profiles_dir = Path(config.profiles_dir)
        web_dir = Path(config.web_dir)

        for path in [profiles_dir / f"{config.client_name}.ovpn", web_dir / f"{config.client_name}.ovpn"]:
            if path.exists():
                path.unlink()
                self.logger.info(f"Removed {path}")

        return True