"""
Step 5: Create PAM User for VPN Authentication
"""

import asyncio
import subprocess
from typing import Callable
from core.config import InstallConfig
from steps.base import BaseStep
from core.logger import get_logger


class PAMStep(BaseStep):
    """Create PAM user for VPN authentication."""

    @property
    def name(self) -> str:
        return "pam"

    @property
    def display_name(self) -> str:
        return "Create PAM User"

    @property
    def description(self) -> str:
        return "Create system user for VPN authentication via PAM"

    async def is_already_done(
        self,
        config: InstallConfig,
    ) -> bool:
        """PAM always runs - it's fast, idempotent, and guarantees the
        password you typed in the wizard is the active VPN password
        (a pre-existing user may have an unknown old password)."""
        return False

    async def execute(
        self,
        config: InstallConfig,
        output_callback: Callable[[str], None] = None,
    ) -> bool:
        """Execute PAM user creation."""

        def log(msg: str):
            if output_callback:
                output_callback(msg)
            self.logger.info(msg)

        username = config.vpn_user
        password = config.vpn_pass

        # Check if user already exists
        result = self._run_cmd(["id", username], check=False)
        if result.returncode == 0:
            log(f"User {username} already exists, updating password...")
            self._run_cmd(["chpasswd"], input_data=f"{username}:{password}")
            log(f"Password updated for {username}")
            return True

        log(f"Creating PAM user: {username}...")
        # Create user with no login shell
        self._run_cmd(["useradd", "-M", "-s", "/usr/sbin/nologin", username])

        # Set password
        log(f"Setting password for {username}...")
        self._run_cmd(["chpasswd"], input_data=f"{username}:{password}")

        # Verify
        result = self._run_cmd(["id", username], check=False)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to create user {username}")

        log(f"PAM user {username} created successfully")
        return True

    async def rollback(self, config: InstallConfig, rollback_data: dict) -> bool:
        """Remove PAM user."""
        username = config.vpn_user
        self.logger.info(f"Removing PAM user: {username}")
        self._run_cmd(["userdel", "-f", username], check=False)
        return True