"""
Step 6: Write OpenVPN Server Configuration
"""

import asyncio
from typing import Callable
from pathlib import Path
from core.config import InstallConfig
from steps.base import BaseStep
from core.logger import get_logger


class OpenVPNStep(BaseStep):
    """Write OpenVPN server configuration."""

    @property
    def name(self) -> str:
        return "openvpn"

    @property
    def display_name(self) -> str:
        return "Write OpenVPN Server Config"

    @property
    def description(self) -> str:
        return "Create server.conf with TLS-crypt v1, AES-256-GCM, TLS 1.3 only, PAM auth"

    SERVER_CONF = """port 1194
proto tcp4
local 127.0.0.1
dev tun
user nobody
group nogroup
persist-key
persist-tun
keepalive 10 60
cipher AES-256-GCM
auth SHA384
tls-version-min 1.3
tls-ciphersuites TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256
tls-crypt /etc/openvpn/ta.key
ca /etc/openvpn/ca.crt
cert /etc/openvpn/server.crt
key /etc/openvpn/server.key
dh /etc/openvpn/dh.pem
plugin /usr/lib/x86_64-linux-gnu/openvpn/plugins/openvpn-plugin-auth-pam.so login
username-as-common-name
verify-client-cert require
server 10.8.0.0 255.255.255.0
topology subnet
push "redirect-gateway def1 bypass-dhcp"
push "dhcp-option DNS 1.1.1.1"
push "dhcp-option DNS 8.8.8.8"
push "block-outside-dns"
reneg-sec 0
explicit-exit-notify 0
log-append /var/log/openvpn.log
verb 3
mute 20
# Performance / stealth
sndbuf 0
rcvbuf 0
push "sndbuf 0"
push "rcvbuf 0"
"""

    async def execute(
        self,
        config: InstallConfig,
        output_callback: Callable[[str], None] = None,
    ) -> bool:
        """Execute OpenVPN server config creation."""

        def log(msg: str):
            if output_callback:
                output_callback(msg)
            self.logger.info(msg)

        log("Backing up existing OpenVPN config...")
        backup_path = self._backup_file(config.openvpn_dir + "/server.conf")

        log("Writing OpenVPN server configuration...")
        self._write_file(config.openvpn_dir + "/server.conf", self.SERVER_CONF, mode=0o644)

        # Verify config syntax
        log("Testing OpenVPN configuration syntax...")
        result = self._run_cmd([
            "openvpn", "--config", config.openvpn_dir + "/server.conf",
            "--verb", "4", "--dry-run"
        ], check=False)

        if result.returncode != 0:
            if backup_path:
                self._restore_backup(config.openvpn_dir + "/server.conf")
            raise RuntimeError(f"OpenVPN config test failed: {result.stderr}")

        log("OpenVPN configuration test passed")
        return True

    async def rollback(self, config: InstallConfig, rollback_data: dict) -> bool:
        """Restore OpenVPN config from backup."""
        backup_path = rollback_data.get("backup_path")
        if backup_path and Path(backup_path).exists():
            self.logger.info("Restoring OpenVPN config from backup...")
            return self._restore_backup(config.openvpn_dir + "/server.conf")
        return False