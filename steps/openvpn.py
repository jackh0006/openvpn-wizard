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

    async def is_already_done(
        self,
        config: InstallConfig,
    ) -> bool:
        """Check if OpenVPN config already exists."""
        conf_path = Path(config.openvpn_dir) / "server.conf"
        if not conf_path.exists():
            return False
        content = conf_path.read_text()
        return "AES-256-GCM" in content and "tls-crypt" in content

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
        server_conf = self._build_server_conf(config)
        self._write_file(config.openvpn_dir + "/server.conf", server_conf, mode=0o644)

        # Validate: required directives present + referenced files exist
        log("Validating OpenVPN configuration...")
        self._validate_conf(config, server_conf, log)

        # Restart OpenVPN so the (possibly new) config takes effect
        # (on re-runs the services step may be skipped, so we restart here)
        log("Restarting OpenVPN...")
        if not self._systemctl("restart", "openvpn@server"):
            if backup_path:
                log("OpenVPN failed with new config - restoring backup...")
                self._restore_backup(config.openvpn_dir + "/server.conf")
                self._systemctl("restart", "openvpn@server")
            raise RuntimeError("Failed to restart OpenVPN - check 'journalctl -u openvpn@server'")
        await asyncio.sleep(2)
        if not self._is_service_active("openvpn@server"):
            raise RuntimeError("OpenVPN did not come back up after restart")
        log("  ✓ OpenVPN active")

        log("OpenVPN configuration valid")
        return True

    def _find_pam_plugin(self) -> str:
        """Locate the OpenVPN PAM auth plugin (arch-independent)."""
        import glob
        candidates = glob.glob("/usr/lib/*/openvpn/plugins/openvpn-plugin-auth-pam.so")
        if candidates:
            return candidates[0]
        return "/usr/lib/x86_64-linux-gnu/openvpn/plugins/openvpn-plugin-auth-pam.so"

    def _build_server_conf(self, config: InstallConfig) -> str:
        """Build server.conf with the detected PAM plugin path."""
        conf = self.SERVER_CONF.replace(
            "plugin /usr/lib/x86_64-linux-gnu/openvpn/plugins/openvpn-plugin-auth-pam.so login",
            f"plugin {self._find_pam_plugin()} login",
        )
        return conf

    def _validate_conf(self, config: InstallConfig, content: str, log):
        """Static validation of server.conf (OpenVPN has no --dry-run)."""
        required_directives = [
            "port ", "proto tcp", "dev tun", "tls-crypt", "ca ", "cert ",
            "key ", "dh ", "server ", "verify-client-cert require",
        ]
        missing = [d for d in required_directives if d not in content]
        if missing:
            raise RuntimeError(f"Generated config missing directives: {missing}")

        # Every referenced file must exist (PKI step runs before this one)
        import re
        for directive in ["ca", "cert", "key", "dh", "tls-crypt"]:
            m = re.search(rf"^{directive}\s+(\S+)$", content, re.MULTILINE)
            if m and not Path(m.group(1)).exists():
                raise RuntimeError(f"Config references missing file: {m.group(1)}")

        log("  ✓ All required directives present, referenced files exist")

    async def rollback(self, config: InstallConfig, rollback_data: dict) -> bool:
        """Restore OpenVPN config from backup."""
        backup_path = rollback_data.get("backup_path")
        if backup_path and Path(backup_path).exists():
            self.logger.info("Restoring OpenVPN config from backup...")
            return self._restore_backup(config.openvpn_dir + "/server.conf")
        return False