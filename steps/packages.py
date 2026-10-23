"""
Step 1: Install System Packages
"""

import asyncio
from typing import Callable, List
from core.config import InstallConfig
from steps.base import BaseStep
from core.logger import get_logger


class PackagesStep(BaseStep):
    """Install required system packages."""

    @property
    def name(self) -> str:
        return "packages"

    @property
    def display_name(self) -> str:
        return "Install System Packages"

    @property
    def description(self) -> str:
        return "Install HAProxy, OpenVPN, Easy-RSA, 3X-UI, and dependencies"

    PACKAGES = [
        # Core
        "haproxy",
        "openvpn",
        "easy-rsa",
        "libpam-radius-auth",

        # Database & tools
        "sqlite3",
        "python3",
        "python3-pip",
        "curl",
        "gnupg2",
        "ca-certificates",
        "iptables-persistent",
        "net-tools",

        # Build tools (for 3X-UI)
        "build-essential",
        "golang-go",
    ]

    XUI_DEPS = [
        # 3X-UI will be installed via official script
    ]

    async def execute(
        self,
        config: InstallConfig,
        output_callback: Callable[[str], None] = None,
    ) -> bool:
        """Execute package installation."""

        def log(msg: str):
            if output_callback:
                output_callback(msg)
            self.logger.info(msg)

        log("Updating package lists...")
        self._run_cmd(["apt-get", "update", "-y"])

        log("Installing required packages...")
        # Install in batches to show progress
        batch_size = 5
        for i in range(0, len(self.PACKAGES), batch_size):
            batch = self.PACKAGES[i:i+batch_size]
            log(f"Installing: {', '.join(batch)}")
            self._run_cmd(["apt-get", "install", "-y", "--no-install-recommends"] + batch)

        # Install 3X-UI
        log("Installing 3X-UI panel...")
        await self._install_xui(log)

        # Verify installations
        log("Verifying installations...")
        for pkg in ["haproxy", "openvpn", "easyrsa", "sqlite3"]:
            result = self._run_cmd(["which", pkg], check=False)
            if result.returncode != 0:
                raise RuntimeError(f"Package {pkg} not found after installation")
            log(f"  ✓ {pkg}: {result.stdout.strip()}")

        log("All packages installed successfully")
        return True

    async def _install_xui(self, log):
        """Install 3X-UI via official script."""
        # Check if already installed
        result = self._run_cmd(["which", "x-ui"], check=False)
        if result.returncode == 0:
            log("  ✓ 3X-UI already installed")
            return

        # Download and run official install script
        log("Downloading 3X-UI installer...")
        self._run_cmd([
            "bash", "-c",
            "curl -fsSL https://raw.githubusercontent.com/MHSanaei/3x-ui/master/install.sh | bash -s -- --version v2.5.3"
        ])

        # Verify
        result = self._run_cmd(["which", "x-ui"], check=False)
        if result.returncode != 0:
            raise RuntimeError("3X-UI installation failed")
        log("  ✓ 3X-UI installed")

    async def rollback(self, config: InstallConfig, rollback_data: dict) -> bool:
        """Rollback package installation (optional - packages stay)."""
        self.logger.warning("Package rollback not implemented - packages remain installed")
        return True