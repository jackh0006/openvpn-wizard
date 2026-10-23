"""
Core configuration dataclasses for the installer.
"""

from dataclasses import dataclass, field
from typing import Optional
import re


@dataclass
class InstallConfig:
    """All configuration parameters for the installation."""

    # Server info (required, no defaults)
    server_ip: str
    admin_user: str
    admin_pass: str
    vpn_user: str
    vpn_pass: str
    client_name: str

    # Domains for SNI routing (REQUIRED - user must provide)
    domain1: str  # VLESS-TLS + xhttp (e.g., yourdomain.com)
    domain2: str  # VLESS-TLS + xhttp (e.g., another.yourdomain.com)
    reality_domain: str  # VLESS-Reality (e.g., popular-site.com)

    # Paths (auto-generated, with defaults)
    openvpn_dir: str = "/etc/openvpn"
    pki_dir: str = "/etc/openvpn/pki"
    haproxy_cfg: str = "/etc/haproxy/haproxy.cfg"
    xui_db: str = "/etc/x-ui/x-ui.db"
    xui_cert: str = "/etc/x-ui/cert.pem"
    xui_key: str = "/etc/x-ui/key.pem"
    user_db: str = "/etc/openvpn/users.db"
    profiles_dir: str = "/etc/openvpn/profiles"
    web_dir: str = "/var/www/vpn-profiles"
    reality_key_path: str = "/etc/x-ui/reality_private.key"

    # Network (with defaults)
    openvpn_port: int = 1194
    haproxy_port: int = 443
    xui_inbound1_port: int = 10000      # VLESS-TLS + xhttp, domain1 (loopback)
    xui_tls2_port: int = 10004          # VLESS-TLS + xhttp, domain2 (loopback)
    xui_inbound2_port: int = 443        # VLESS-Reality (loopback, routed via HAProxy)
    vpn_subnet: str = "10.8.0.0/24"
    vpn_gateway: str = "10.8.0.1"
    dns1: str = "1.1.1.1"
    dns2: str = "8.8.8.8"

    # Optional/derived fields (with defaults)
    server_ip_confirmed: bool = False
    wan_interface: str = ""

    def __post_init__(self):
        """Validate and normalize configuration."""
        self.server_ip = self.server_ip.strip()
        self.admin_user = self.admin_user.strip().lower()
        self.vpn_user = self.vpn_user.strip().lower()
        self.client_name = self.client_name.strip()
        self.domain1 = self.domain1.strip().lower()
        self.domain2 = self.domain2.strip().lower()
        self.reality_domain = self.reality_domain.strip().lower()

    @property
    def client_ovpn_path(self) -> str:
        return f"{self.profiles_dir}/{self.client_name}.ovpn"

    @property
    def web_ovpn_url(self) -> str:
        return f"http://{self.server_ip}/{self.client_name}.ovpn"


def validate_fqdn(domain: str) -> bool:
    """Validate a fully qualified domain name."""
    if not domain or len(domain) > 253:
        return False
    # Allow localhost for testing
    if domain == "localhost":
        return True
    pattern = r'^(?=.{1,253}$)(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    return bool(re.match(pattern, domain))


def validate_ip(ip: str) -> bool:
    """Validate IPv4 address."""
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(p) <= 255 for p in parts)
    except ValueError:
        return False


def validate_username(username: str) -> bool:
    """Validate username (alphanumeric, underscore, dash)."""
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', username)) and 1 <= len(username) <= 32


def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength. Returns (valid, message)."""
    if len(password) < 12:
        return False, "Password must be at least 12 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
        return False, "Password must contain at least one special character"
    return True, "Strong password"


def validate_client_name(name: str) -> bool:
    """Validate client profile name."""
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', name)) and 1 <= len(name) <= 64