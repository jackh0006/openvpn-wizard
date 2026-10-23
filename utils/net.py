"""
Network Utilities - Port checking, listening ports.
"""

import socket
import subprocess
from typing import List, Tuple
from core.logger import get_logger


def check_port(host: str, port: int, timeout: float = 2.0) -> bool:
    """Check if a TCP port is open on host."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def get_listening_ports() -> List[Tuple[str, int, str]]:
    """Get all listening TCP ports. Returns list of (proto, port, process)."""
    try:
        result = subprocess.run(
            ["ss", "-ltnp"],
            capture_output=True, text=True
        )
        ports = []
        for line in result.stdout.split('\n')[1:]:  # Skip header
            parts = line.split()
            if len(parts) >= 5:
                proto = parts[0]
                local_addr = parts[3]
                process = parts[5] if len(parts) > 5 else ""
                if ":" in local_addr:
                    ip, port_str = local_addr.rsplit(":", 1)
                    try:
                        port = int(port_str)
                        ports.append((proto, port, process))
                    except ValueError:
                        pass
        return ports
    except Exception:
        return []


def is_port_in_use(port: int, host: str = "0.0.0.0") -> bool:
    """Check if a port is in use on the given host."""
    return check_port(host, port)


def get_default_gateway_interface() -> str:
    """Get the interface used for default gateway."""
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
    return "eth0"