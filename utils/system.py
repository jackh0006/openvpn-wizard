"""
System Utilities - IP detection, interface detection, system info.
"""

import subprocess
import socket
import requests
from typing import Optional
from core.logger import get_logger


def get_public_ip() -> Optional[str]:
    """Get public IP address from multiple sources."""
    logger = get_logger()

    # Try multiple IP detection services
    services = [
        "https://api.ipify.org",
        "https://ifconfig.me/ip",
        "https://icanhazip.com",
        "https://ident.me",
    ]

    for service in services:
        try:
            response = requests.get(service, timeout=5)
            if response.status_code == 200:
                ip = response.text.strip()
                # Validate IPv4
                parts = ip.split('.')
                if len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
                    logger.info(f"Detected public IP: {ip} (via {service})")
                    return ip
        except Exception as e:
            logger.debug(f"Failed to get IP from {service}: {e}")
            continue

    # Fallback: try to get from local interface
    try:
        # Get default route interface
        result = subprocess.run(["ip", "route", "show", "default"], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if line.startswith("default"):
                parts = line.split()
                if "dev" in parts:
                    idx = parts.index("dev")
                    if idx + 1 < len(parts):
                        iface = parts[idx + 1]
                        # Get IP on that interface
                        result2 = subprocess.run(
                            ["ip", "-4", "addr", "show", "dev", iface],
                            capture_output=True, text=True
                        )
                        for l in result2.stdout.split('\n'):
                            if "inet " in l and "scope global" in l:
                                ip = l.strip().split()[1].split('/')[0]
                                logger.info(f"Detected public IP from {iface}: {ip}")
                                return ip
    except Exception as e:
        logger.debug(f"Failed to get IP from local interface: {e}")

    return None


def get_wan_interface() -> Optional[str]:
    """Get the WAN interface (used for default route)."""
    try:
        result = subprocess.run(["ip", "route", "show", "default"], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if line.startswith("default"):
                parts = line.split()
                if "dev" in parts:
                    idx = parts.index("dev")
                    if idx + 1 < len(parts):
                        return parts[idx + 1]
    except Exception:
        pass
    return None


def get_system_info() -> dict:
    """Get system information."""
    info = {}

    try:
        # OS info
        with open("/etc/os-release") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    info[k.lower()] = v.strip('"')
    except Exception:
        pass

    try:
        # Kernel
        result = subprocess.run(["uname", "-r"], capture_output=True, text=True)
        info["kernel"] = result.stdout.strip()
    except Exception:
        pass

    try:
        # CPU
        result = subprocess.run(["nproc"], capture_output=True, text=True)
        info["cpu_cores"] = result.stdout.strip()
    except Exception:
        pass

    try:
        # Memory
        result = subprocess.run(["free", "-h"], capture_output=True, text=True)
        info["memory"] = result.stdout.strip()
    except Exception:
        pass

    try:
        # Disk
        result = subprocess.run(["df", "-h", "/"], capture_output=True, text=True)
        info["disk"] = result.stdout.strip()
    except Exception:
        pass

    return info