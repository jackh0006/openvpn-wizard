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

    @property
    def name(self) -> str:
        return "haproxy"

    @property
    def display_name(self) -> str:
        return "Configure HAProxy with SNI Routing"

    @property
    def description(self) -> str:
        return "Write HAProxy config with SNI routing rules for OpenVPN, VLESS-TLS, VLESS-Reality"

    HAPROXY_CFG = """global
    log /dev/log local0
    maxconn 4096
    daemon
    tune.ssl.default-dh-param 2048

defaults
    mode tcp
    timeout connect 5s
    timeout client  30s
    timeout server  30s

frontend ft_443
    bind 0.0.0.0:443
    mode tcp
    tcp-request inspect-delay 5s
    tcp-request content accept if {{ req_ssl_hello_type 1 }}

    # SNI-less rule (OpenVPN)
    acl has_sni req.ssl_sni -m found
    use_backend bk_openvpn if !has_sni

    # VLESS-TLS backends
    use_backend bk_10000 if {{ req.ssl_sni -i {{domain1}} }}
    use_backend bk_10004 if {{ req.ssl_sni -i {{domain2}} }}

    # VLESS-Reality backend
    use_backend bk_443 if {{ req.ssl_sni -i {{reality_domain}} }}

backend bk_openvpn
    mode tcp
    server openvpn 127.0.0.1:1194 send-proxy-v2

backend bk_10000
    mode tcp
    server s10000 127.0.0.1:10000 send-proxy-v2

backend bk_10004
    mode tcp
    server s10004 127.0.0.1:10004 send-proxy-v2

backend bk_443
    mode tcp
    server s443 127.0.0.1:443 send-proxy-v2
"""

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
        # Render template
        rendered = self.HAPROXY_CFG
        rendered = rendered.replace("{{domain1}}", config.domain1)
        rendered = rendered.replace("{{domain2}}", config.domain2)
        rendered = rendered.replace("{{reality_domain}}", config.reality_domain)

        # Fix template syntax for HAProxy (double braces)
        rendered = rendered.replace("{{ req_ssl_hello_type 1 }}", "req_ssl_hello_type 1")
        rendered = rendered.replace("{{ req.ssl_sni -i {{domain1}} }}", f"req.ssl_sni -i {config.domain1}")
        rendered = rendered.replace("{{ req.ssl_sni -i {{domain2}} }}", f"req.ssl_sni -i {config.domain2}")
        rendered = rendered.replace("{{ req.ssl_sni -i {{reality_domain}} }}", f"req.ssl_sni -i {config.reality_domain}")

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