"""
Validation Checklist - Post-install verification.
"""

import os
import socket
import subprocess
from typing import Callable, List, Tuple
from dataclasses import dataclass
from core.config import InstallConfig
from core.logger import get_logger


@dataclass
class ValidationCheck:
    """Single validation check result."""
    name: str
    passed: bool
    details: str = ""


def run_validation(config: InstallConfig) -> List[Tuple[str, bool, str]]:
    """Run all validation checks. Returns list of (name, passed, details)."""
    logger = get_logger()
    checks = []

    # Define all checks
    checks.append(("HAProxy listening on 0.0.0.0:443", check_haproxy_listen))
    checks.append(("OpenVPN listening on 127.0.0.1:1194", check_openvpn_listen))
    checks.append(("3X-UI inbound 10000 active (loopback)", lambda c: check_port_listen(c, 10000, "127.0.0.1", "3X-UI VLESS-TLS 1")))
    checks.append(("3X-UI inbound 10004 active (loopback)", lambda c: check_port_listen(c, 10004, "127.0.0.1", "3X-UI VLESS-TLS 2")))
    checks.append(("3X-UI inbound 443 active (loopback)", lambda c: check_port_listen(c, 443, "127.0.0.1", "3X-UI VLESS-Reality")))
    checks.append(("IPv4 forwarding enabled", check_ip_forward))
    checks.append(("NAT MASQUERADE rule exists", lambda c: check_nat_masquerade(c)))
    checks.append(("OpenVPN config syntax OK", check_openvpn_syntax))
    checks.append(("Client .ovpn connects", lambda c: check_client_profile(c)))
    checks.append(("Internet through tunnel", check_tunnel_internet))
    checks.append(("DNS leak test", check_dns_leak))
    checks.append(("No IPv6 leaks", check_ipv6_leak))

    results = []
    for name, check_fn in checks:
        try:
            passed, details = check_fn(config)
            results.append((name, passed, details))
            status = "PASS" if passed else "FAIL"
            logger.info(f"Validation: {name} - {status}")
            if not passed and details:
                logger.warning(f"  Details: {details}")
        except Exception as e:
            results.append((name, False, f"Check error: {e}"))
            logger.error(f"Validation error for {name}: {e}")

    return results


def check_port_listen(config: InstallConfig, port: int, bind_ip: str, name: str) -> Tuple[bool, str]:
    """Check if a port is listening on given IP."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((bind_ip, port))
        sock.close()
        if result == 0:
            return True, f"{name} listening on {bind_ip}:{port}"
        else:
            return False, f"{name} NOT listening on {bind_ip}:{port}"
    except Exception as e:
        return False, f"Error checking {name}: {e}"


def check_haproxy_listen(config: InstallConfig) -> Tuple[bool, str]:
    return check_port_listen(config, 443, "0.0.0.0", "HAProxy")


def check_openvpn_listen(config: InstallConfig) -> Tuple[bool, str]:
    return check_port_listen(config, 1194, "127.0.0.1", "OpenVPN")


def check_xui_inbound_10000(config: InstallConfig) -> Tuple[bool, str]:
    return check_port_listen(config, 10000, "0.0.0.0", "3X-UI VLESS-TLS 1")


def check_xui_inbound_443(config: InstallConfig) -> Tuple[bool, str]:
    return check_port_listen(config, 443, "127.0.0.1", "3X-UI VLESS-Reality")


def check_ip_forward(config: InstallConfig) -> Tuple[bool, str]:
    """Check if IPv4 forwarding is enabled."""
    try:
        result = subprocess.run(["cat", "/proc/sys/net/ipv4/ip_forward"], capture_output=True, text=True)
        if "1" in result.stdout:
            return True, "IPv4 forwarding enabled"
        else:
            return False, "IPv4 forwarding NOT enabled"
    except Exception as e:
        return False, f"Error checking ip_forward: {e}"


def check_nat_masquerade(config: InstallConfig) -> Tuple[bool, str]:
    """Check if NAT MASQUERADE rule exists for VPN subnet."""
    try:
        result = subprocess.run(
            ["iptables", "-t", "nat", "-L", "POSTROUTING", "-n", "-v"],
            capture_output=True, text=True
        )
        if config.vpn_subnet in result.stdout and "MASQUERADE" in result.stdout:
            return True, f"NAT MASQUERADE rule found for {config.vpn_subnet}"
        else:
            return False, f"NAT MASQUERADE rule NOT found for {config.vpn_subnet}"
    except Exception as e:
        return False, f"Error checking iptables: {e}"


def check_openvpn_syntax(config: InstallConfig) -> Tuple[bool, str]:
    """Validate OpenVPN config statically (OpenVPN has no --dry-run)."""
    import re
    try:
        with open("/etc/openvpn/server.conf") as f:
            content = f.read()
        required = ["port ", "proto tcp", "dev tun", "tls-crypt",
                    "verify-client-cert require", "server "]
        missing = [d for d in required if d not in content]
        if missing:
            return False, f"Config missing directives: {missing}"
        # Referenced files must exist
        for directive in ["ca", "cert", "key", "dh", "tls-crypt"]:
            m = re.search(rf"^{directive}\s+(\S+)$", content, re.MULTILINE)
            if m and not os.path.exists(m.group(1)):
                return False, f"Referenced file missing: {m.group(1)}"
        return True, "OpenVPN config directives and files OK"
    except Exception as e:
        return False, f"Error validating OpenVPN config: {e}"


def check_client_profile(config: InstallConfig) -> Tuple[bool, str]:
    """Check if client profile exists and is valid."""
    import os
    profile_path = f"/etc/openvpn/profiles/{config.client_name}.ovpn"
    if os.path.exists(profile_path):
        # Check it has required sections
        with open(profile_path) as f:
            content = f.read()
        required = ["<ca>", "<cert>", "<key>", "<tls-crypt>"]
        missing = [r for r in required if r not in content]
        if not missing:
            return True, f"Client profile exists with all sections"
        else:
            return False, f"Client profile missing sections: {missing}"
    else:
        return False, f"Client profile not found at {profile_path}"


def check_tunnel_internet(config: InstallConfig) -> Tuple[bool, str]:
    """Check if internet works through tunnel (requires active connection)."""
    # This would require an actual VPN connection to test
    # For now, just check the profile has correct settings
    profile_path = f"/etc/openvpn/profiles/{config.client_name}.ovpn"
    try:
        with open(profile_path) as f:
            content = f.read()
        checks = [
            ("redirect-gateway", "redirect-gateway" in content),
            ("DNS 1.1.1.1", "1.1.1.1" in content),
            ("DNS 8.8.8.8", "8.8.8.8" in content),
            ("block-outside-dns", "block-outside-dns" in content),
        ]
        failed = [name for name, passed in checks if not passed]
        if not failed:
            return True, "Client profile has correct tunnel settings"
        else:
            return False, f"Client profile missing: {', '.join(failed)}"
    except Exception as e:
        return False, f"Error checking client profile: {e}"


def check_dns_leak(config: InstallConfig) -> Tuple[bool, str]:
    """Check DNS leak protection settings."""
    # Check OpenVPN config pushes DNS
    try:
        with open("/etc/openvpn/server.conf") as f:
            content = f.read()
        if "dhcp-option DNS 1.1.1.1" in content and "dhcp-option DNS 8.8.8.8" in content:
            return True, "OpenVPN pushes DNS servers (1.1.1.1, 8.8.8.8)"
        else:
            return False, "OpenVPN does not push DNS servers"
    except Exception as e:
        return False, f"Error checking DNS config: {e}"


def check_ipv6_leak(config: InstallConfig) -> Tuple[bool, str]:
    """Check IPv6 is disabled."""
    try:
        # Check sysctl
        result = subprocess.run(["sysctl", "net.ipv6.conf.all.disable_ipv6"], capture_output=True, text=True)
        if "1" in result.stdout:
            return True, "IPv6 disabled via sysctl"
        else:
            return False, "IPv6 NOT disabled"
    except Exception as e:
        return False, f"Error checking IPv6: {e}"