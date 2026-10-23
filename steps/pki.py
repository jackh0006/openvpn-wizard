"""
Step 4: Bootstrap Easy-RSA PKI
"""

import asyncio
import subprocess
from typing import Callable
from pathlib import Path
from core.config import InstallConfig
from steps.base import BaseStep
from core.logger import get_logger


class PKIStep(BaseStep):
    """Bootstrap Easy-RSA PKI for OpenVPN."""

    @property
    def name(self) -> str:
        return "pki"

    @property
    def display_name(self) -> str:
        return "Bootstrap Easy-RSA PKI"

    @property
    def description(self) -> str:
        return "Create CA, server cert, client cert, DH params, and TLS-crypt key"

    async def execute(
        self,
        config: InstallConfig,
        output_callback: Callable[[str], None] = None,
    ) -> bool:
        """Execute PKI bootstrap."""

        def log(msg: str):
            if output_callback:
                output_callback(msg)
            self.logger.info(msg)

        pki_dir = Path(config.pki_dir)
        openvpn_dir = Path(config.openvpn_dir)

        # Ensure directories exist
        openvpn_dir.mkdir(parents=True, exist_ok=True)
        pki_dir.mkdir(parents=True, exist_ok=True)

        # Check if PKI already exists
        if (pki_dir / "ca.crt").exists() and (pki_dir / "ta.key").exists():
            log("PKI already exists, skipping bootstrap")
            await self._copy_runtime_assets(config)
            return True

        log("Initializing Easy-RSA PKI...")
        await self._run_easyrsa(config, ["init-pki"])

        log("Building CA (Certificate Authority)...")
        await self._run_easyrsa(config, ["--batch", "build-ca", "nopass"])

        log("Generating server certificate...")
        await self._run_easyrsa(config, ["--batch", "build-server-full", "server", "nopass"])

        log("Generating client certificate...")
        await self._run_easyrsa(config, ["--batch", "build-client-full", config.vpn_user, "nopass"])

        log("Generating DH parameters (2048-bit)...")
        await self._run_easyrsa(config, ["gen-dh"])

        log("Generating TLS-crypt v1 key...")
        self._run_cmd(["openvpn", "--genkey", "--secret", str(pki_dir / "ta.key")])

        # Copy runtime assets to /etc/openvpn/
        await self._copy_runtime_assets(config)

        # Set permissions
        log("Setting secure permissions...")
        self._run_cmd(["chmod", "600", str(pki_dir / "ta.key")])
        self._run_cmd(["chmod", "600", str(pki_dir / "private" / "server.key")])
        self._run_cmd(["chmod", "600", str(pki_dir / "private" / f"{config.vpn_user}.key")])

        log("PKI bootstrap complete")
        return True

    async def _run_easyrsa(self, config: InstallConfig, args: list):
        """Run easyrsa command in PKI directory."""
        cmd = ["./easyrsa"] + args
        self._run_cmd(cmd, cwd=config.pki_dir)

    async def _copy_runtime_assets(self, config: InstallConfig):
        """Copy PKI assets to OpenVPN runtime directory."""
        pki_dir = Path(config.pki_dir)
        openvpn_dir = Path(config.openvpn_dir)

        files_to_copy = [
            ("ca.crt", "ca.crt"),
            ("issued/server.crt", "server.crt"),
            ("private/server.key", "server.key"),
            ("dh.pem", "dh.pem"),
            ("ta.key", "ta.key"),
        ]

        for src, dst in files_to_copy:
            src_path = pki_dir / src
            dst_path = openvpn_dir / dst
            if src_path.exists():
                self._run_cmd(["cp", str(src_path), str(dst_path)])
                self.logger.debug(f"Copied {src} -> {dst}")

        # Create empty CRL (required by verify-client-cert require)
        crl_path = openvpn_dir / "crl.pem"
        crl_path.touch(mode=0o644)

    async def rollback(self, config: InstallConfig, rollback_data: dict) -> bool:
        """Rollback PKI (remove generated files)."""
        self.logger.warning("PKI rollback not fully implemented - manual cleanup may be needed")
        return True