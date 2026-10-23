"""
Step 1: Install System Packages
"""

import asyncio
from typing import Callable, List
from pathlib import Path
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
        "nginx",          # serves the .ovpn download page
        "sqlite3",

        # Tools
        "curl",
        "ca-certificates",
        "iptables-persistent",
        "net-tools",
    ]

    def _apt_env(self) -> dict:
        """Environment for non-interactive apt runs (no debconf prompts, keeps PATH)."""
        import os
        env = dict(os.environ)
        env["DEBIAN_FRONTEND"] = "noninteractive"
        return env

    async def is_already_done(
        self,
        config: InstallConfig,
    ) -> bool:
        """Check if key packages are already installed."""
        critical = ["haproxy", "openvpn", "easy-rsa", "sqlite3", "python3"]
        missing = []
        for pkg in critical:
            result = self._run_cmd(["dpkg", "-s", pkg], check=False)
            if result.returncode != 0:
                missing.append(pkg)
        return len(missing) == 0

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

        env = self._apt_env()

        log("Updating package lists...")
        self._run_cmd(["apt-get", "update", "-y"], env=env)

        log("Installing required packages...")
        # Install in batches to show progress
        batch_size = 5
        for i in range(0, len(self.PACKAGES), batch_size):
            batch = self.PACKAGES[i:i+batch_size]
            log(f"Installing: {', '.join(batch)}")
            self._run_cmd(
                ["apt-get", "install", "-y", "--no-install-recommends"] + batch,
                env=env, timeout=900,
            )

        # Install 3X-UI
        log("Installing 3X-UI panel...")
        await self._install_xui(log)

        # Verify installations
        log("Verifying installations...")
        for pkg, path in [
            ("haproxy", "haproxy"),
            ("openvpn", "openvpn"),
            ("easy-rsa", "/usr/share/easy-rsa/easyrsa"),
            ("sqlite3", "sqlite3"),
        ]:
            if path.startswith("/"):
                ok = Path(path).exists()
                found = path
            else:
                result = self._run_cmd(["which", pkg], check=False)
                ok = result.returncode == 0
                found = result.stdout.strip()
            if not ok:
                raise RuntimeError(f"Package {pkg} not found after installation")
            log(f"  ✓ {pkg}: {found}")

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