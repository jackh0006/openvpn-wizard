"""
Step 8: Enable & Start All Services
"""

import asyncio
from typing import Callable
from core.config import InstallConfig
from steps.base import BaseStep
from core.logger import get_logger


class ServicesStep(BaseStep):
    """Enable and start all services."""

    @property
    def name(self) -> str:
        return "services"

    @property
    def display_name(self) -> str:
        return "Enable & Start All Services"

    @property
    def description(self) -> str:
        return "Enable and start HAProxy, OpenVPN, and 3X-UI via systemd"

    SERVICES = [
        ("haproxy", "HAProxy"),
        ("openvpn@server", "OpenVPN Server"),
        ("x-ui", "3X-UI Panel"),
    ]

    async def is_already_done(
        self,
        config: InstallConfig,
    ) -> bool:
        """Check if all services are already active."""
        for service_name, _ in self.SERVICES:
            if not self._is_service_active(service_name):
                return False
        return True

    async def execute(
        self,
        config: InstallConfig,
        output_callback: Callable[[str], None] = None,
    ) -> bool:
        """Execute service startup."""

        def log(msg: str):
            if output_callback:
                output_callback(msg)
            self.logger.info(msg)

        # Enable and start each service
        for service_name, display_name in self.SERVICES:
            log(f"Enabling {display_name}...")
            self._systemctl("enable", service_name)

            log(f"Starting {display_name}...")
            if not self._systemctl("start", service_name):
                # Try restart if already running
                log(f"  {display_name} may already be running, restarting...")
                self._systemctl("restart", service_name)

            # Wait a moment for service to start
            await asyncio.sleep(2)

            # Verify
            if self._is_service_active(service_name):
                log(f"  ✓ {display_name} is active")
            else:
                # Get status for debugging
                result = self._run_cmd(["systemctl", "status", service_name, "--no-pager"], check=False)
                log(f"  ✗ {display_name} failed to start")
                log(f"  Status: {result.stdout}")
                raise RuntimeError(f"Service {service_name} failed to start")

        # Final verification
        log("Verifying all listeners...")
        await self._verify_listeners(config)

        log("All services started successfully")
        return True

    async def _verify_listeners(self, config: InstallConfig):
        """Verify services are listening on expected ports."""
        import socket

        listeners = [
            (443, "0.0.0.0", "HAProxy"),
            (1194, "127.0.0.1", "OpenVPN"),
            (10000, "0.0.0.0", "3X-UI VLESS-TLS"),
            (10004, "0.0.0.0", "3X-UI VLESS-TLS 2"),
            (443, "127.0.0.1", "3X-UI VLESS-Reality"),
        ]

        for port, bind_ip, name in listeners:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((bind_ip, port))
                sock.close()
                if result == 0:
                    self.logger.info(f"  ✓ {name} listening on {bind_ip}:{port}")
                else:
                    self.logger.warning(f"  ⚠ {name} NOT listening on {bind_ip}:{port}")
            except Exception as e:
                self.logger.warning(f"  ⚠ Could not verify {name}: {e}")

    async def rollback(self, config: InstallConfig, rollback_data: dict) -> bool:
        """Stop and disable services."""
        self.logger.info("Stopping services...")
        for service_name, _ in reversed(self.SERVICES):
            self._systemctl("stop", service_name)
            self._systemctl("disable", service_name)
        return True