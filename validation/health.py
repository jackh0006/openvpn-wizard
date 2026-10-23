"""
Service Health Checks - Monitor service status.
"""

import subprocess
from typing import List, Dict
from core.config import InstallConfig
from core.logger import get_logger


def check_service_health(service: str) -> Dict:
    """Check health of a single service."""
    result = subprocess.run(
        ["systemctl", "status", service, "--no-pager"],
        capture_output=True, text=True
    )

    active = result.returncode == 0 and "active (running)" in result.stdout

    return {
        "service": service,
        "active": active,
        "status": "running" if active else "stopped",
        "details": result.stdout[:500] if result.stdout else result.stderr[:500],
    }


def check_all_services(config: InstallConfig) -> List[Dict]:
    """Check health of all VPN services."""
    services = [
        "haproxy",
        "openvpn@server",
        "x-ui",
        "nginx",
    ]

    results = []
    for svc in services:
        results.append(check_service_health(svc))

    return results


def get_service_logs(service: str, lines: int = 50) -> str:
    """Get recent logs for a service."""
    result = subprocess.run(
        ["journalctl", "-u", service, "-n", str(lines), "--no-pager"],
        capture_output=True, text=True
    )
    return result.stdout if result.returncode == 0 else result.stderr