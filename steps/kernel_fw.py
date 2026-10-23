"""
Step 7: Kernel Tuning & Firewall NAT
"""

import asyncio
from typing import Callable
from pathlib import Path
from core.config import InstallConfig
from steps.base import BaseStep
from core.logger import get_logger


class KernelFWStep(BaseStep):
    """Configure kernel parameters and iptables NAT."""

    @property
    def name(self) -> str:
        return "kernel_fw"

    @property
    def display_name(self) -> str:
        return "Kernel Tuning & Firewall NAT"

    @property
    def description(self) -> str:
        return "Enable IPv4 forwarding, configure NAT for VPN subnet"

    SYSCTL_CONF = """# VPN Installer - IPv4 Forwarding
net.ipv4.ip_forward=1
# Disable IPv6 (we're IPv4 only)
net.ipv6.conf.all.disable_ipv6=1
net.ipv6.conf.default.disable_ipv6=1
net.ipv6.conf.lo.disable_ipv6=1
"""

    async def is_already_done(
        self,
        config: InstallConfig,
    ) -> bool:
        """Done only when forwarding is on AND our NAT rule exists."""
        try:
            result = self._run_cmd(["cat", "/proc/sys/net/ipv4/ip_forward"], check=False)
            if "1" not in result.stdout:
                return False
            # NAT masquerade rule for the VPN subnet must exist too
            nat = self._run_cmd(
                ["iptables", "-t", "nat", "-L", "POSTROUTING", "-n"], check=False
            )
            return config.vpn_subnet in nat.stdout and "MASQUERADE" in nat.stdout
        except Exception:
            return False

    async def execute(
        self,
        config: InstallConfig,
        output_callback: Callable[[str], None] = None,
    ) -> bool:
        """Execute kernel and firewall configuration."""

        def log(msg: str):
            if output_callback:
                output_callback(msg)
            self.logger.info(msg)

        # Detect WAN interface if not set
        if not config.wan_interface:
            config.wan_interface = self._detect_wan_interface()
            log(f"Auto-detected WAN interface: {config.wan_interface}")

        # Enable IPv4 forwarding
        log("Enabling IPv4 forwarding...")
        self._write_file("/etc/sysctl.d/99-openvpn.conf", self.SYSCTL_CONF)
        self._run_cmd(["sysctl", "--system"])

        # Verify
        result = self._run_cmd(["cat", "/proc/sys/net/ipv4/ip_forward"])
        if "1" not in result.stdout:
            raise RuntimeError("Failed to enable IPv4 forwarding")
        log("  ✓ IPv4 forwarding enabled")

        # Configure iptables NAT
        log("Configuring iptables NAT...")
        await self._setup_iptables(config)

        # Save iptables rules (base._run_cmd takes a list - use bash -c for the redirect)
        log("Saving iptables rules...")
        self._run_cmd(["bash", "-c", "iptables-save > /etc/iptables/rules.v4"])

        # Ensure iptables-persistent is configured
        self._run_cmd(["systemctl", "enable", "netfilter-persistent"], check=False)

        log("Kernel and firewall configuration complete")
        return True

    def _detect_wan_interface(self) -> str:
        """Detect the default WAN interface."""
        try:
            # Get interface used for default route
            result = self._run_cmd(["ip", "route", "show", "default"])
            for line in result.stdout.split('\n'):
                if line.startswith("default"):
                    parts = line.split()
                    if "dev" in parts:
                        idx = parts.index("dev")
                        if idx + 1 < len(parts):
                            return parts[idx + 1]
        except Exception:
            pass
        # Fallback
        return "eth0"

    async def _setup_iptables(self, config: InstallConfig):
        """Setup iptables NAT rules."""
        subnet = config.vpn_subnet  # e.g., 10.8.0.0/24
        iface = config.wan_interface

        # Flush existing rules (careful!)
        # We only add our rules, don't flush everything

        # NAT rule for VPN subnet
        nat_rule = [
            "iptables", "-t", "nat", "-C", "POSTROUTING",
            "-s", subnet, "-o", iface, "-j", "MASQUERADE"
        ]
        result = self._run_cmd(nat_rule, check=False)
        if result.returncode != 0:
            # Rule doesn't exist, add it
            add_rule = ["iptables", "-t", "nat", "-A", "POSTROUTING", "-s", subnet, "-o", iface, "-j", "MASQUERADE"]
            self._run_cmd(add_rule)
            self.logger.info(f"  ✓ Added NAT rule for {subnet} via {iface}")
        else:
            self.logger.info(f"  ✓ NAT rule already exists")

        # Forward rules
        for rule in [
            ["iptables", "-C", "FORWARD", "-s", subnet, "-j", "ACCEPT"],
            ["iptables", "-C", "FORWARD", "-d", subnet, "-j", "ACCEPT"],
        ]:
            result = self._run_cmd(rule, check=False)
            if result.returncode != 0:
                add_rule = rule.copy()
                add_rule[2] = "-A"
                self._run_cmd(add_rule)

        self.logger.info("  ✓ Forward rules configured")

    async def rollback(self, config: InstallConfig, rollback_data: dict) -> bool:
        """Rollback kernel and firewall changes."""
        self.logger.info("Rolling back kernel and firewall changes...")

        # Disable IPv4 forwarding
        self._run_cmd(["sysctl", "-w", "net.ipv4.ip_forward=0"], check=False)

        # Remove iptables rules
        subnet = config.vpn_subnet
        iface = config.wan_interface

        for rule in [
            ["iptables", "-t", "nat", "-D", "POSTROUTING", "-s", subnet, "-o", iface, "-j", "MASQUERADE"],
            ["iptables", "-D", "FORWARD", "-s", subnet, "-j", "ACCEPT"],
            ["iptables", "-D", "FORWARD", "-d", subnet, "-j", "ACCEPT"],
        ]:
            self._run_cmd(rule, check=False)

        # Restore sysctl
        sysctl_file = Path("/etc/sysctl.d/99-openvpn.conf")
        if sysctl_file.exists():
            sysctl_file.unlink()
        self._run_cmd(["sysctl", "--system"], check=False)

        return True