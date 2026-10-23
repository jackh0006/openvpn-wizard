"""
Step 2: Configure HAProxy with SNI Routing
"""

import asyncio
from typing import Callable
from pathlib import Path
from core.config import InstallConfig
from steps.base import BaseStep
from core.logger import get_logger


class HAProxyStep(BaseStep):
    """Configure HAProxy with SNI-based routing."""

    TEMPLATE_PATH = Path(__file__).parent.parent / "templates" / "haproxy.cfg.j2"

    @property
    def name(self) -> str:
        return "haproxy"

    @property
    def display_name(self) -> str:
        return "Configure HAProxy with SNI Routing"

    @property
    def description(self) -> str:
        return "Write HAProxy config with SNI routing rules for OpenVPN, VLESS-TLS, VLESS-Reality"

    async def is_already_done(
        self,
        config: InstallConfig,
    ) -> bool:
        """Check if HAProxy is already configured."""
        cfg_path = Path(config.haproxy_cfg)
        if not cfg_path.exists():
            return False
        # Check if it has our SNI routing
        content = cfg_path.read_text()
        return "ft_443" in content and "bk_openvpn" in content

    async def execute(
        self,
        config: InstallConfig,
        output_callback: Callable[[str], None] = None,
    ) -> bool:
        """Execute HAProxy configuration."""

        def log(msg: str):
            if output_callback:
                output_callback(msg)
            self.logger.info(msg)

        log("Backing up existing HAProxy config...")
        backup_path = self._backup_file(config.haproxy_cfg)

        log("Generating HAProxy configuration...")
        rendered = self._template_render(
            str(self.TEMPLATE_PATH),
            {
                "domain1": config.domain1,
                "domain2": config.domain2,
                "reality_domain": config.reality_domain,
            },
        )

        log(f"Writing HAProxy config to {config.haproxy_cfg}...")
        self._write_file(config.haproxy_cfg, rendered, mode=0o644)

        log("Testing HAProxy configuration...")
        result = self._run_cmd(["haproxy", "-c", "-f", config.haproxy_cfg], check=False)
        if result.returncode != 0:
            # Restore backup on failure
            if backup_path:
                self._restore_backup(config.haproxy_cfg)
            raise RuntimeError(f"HAProxy config test failed: {result.stderr}")

        log("HAProxy configuration test passed")
        return True

    async def rollback(self, config: InstallConfig, rollback_data: dict) -> bool:
        """Restore HAProxy config from backup."""
        backup_path = rollback_data.get("backup_path")
        if backup_path and Path(backup_path).exists():
            self.logger.info("Restoring HAProxy config from backup...")
            return self._restore_backup(config.haproxy_cfg)
        return False