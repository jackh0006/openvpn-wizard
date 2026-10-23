"""
Goodbye Screen - Exit with summary and next steps.
"""

import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.columns import Columns

from ui.theme import get_console, COLORS, SMALL_LOGO
from ui.components import InfoBox, CreditsFooter, SectionHeader
from core.config import InstallConfig
from core.state import InstallState


class GoodbyeScreen:
    """Exit screen with summary."""

    def __init__(self, console: Console, config: InstallConfig = None):
        self.console = console
        self.config = config

    async def run(self):
        """Display goodbye screen."""
        self.console.clear()

        # Small logo
        self.console.print(f"[primary]{SMALL_LOGO}[/primary]")

        if self.config:
            # Installation summary
            summary = InfoBox(
                "success",
                "🎉 Installation Complete",
                "Your VPN stack is deployed and ready.",
                [
                    f"🌐 Server: {self.config.server_ip}:443",
                    f"👤 VPN User: {self.config.vpn_user}",
                    f"📄 Profile: {self.config.client_name}.ovpn",
                    f"🔐 Domains: {self.config.domain1}, {self.config.domain2}, {self.config.reality_domain}",
                ]
            )
            self.console.print(summary.render())

            # Important files
            files_info = InfoBox(
                "file",
                "📁 Important File Locations",
                "Keep these paths for reference:",
                [
                    f"[path]/etc/openvpn/server.conf[/path] - OpenVPN config",
                    f"[path]/etc/haproxy/haproxy.cfg[/path] - HAProxy config",
                    f"[path]/etc/x-ui/x-ui.db[/path] - 3X-UI database",
                    f"[path]/etc/openvpn/pki/[/path] - PKI (CA, certs, keys)",
                    f"[path]/etc/openvpn/users.db[/path] - User database",
                    f"[path]/etc/openvpn/profiles/{self.config.client_name}.ovpn[/path] - Your profile",
                    f"[path]/var/www/vpn-profiles/{self.config.client_name}.ovpn[/path] - Web download",
                ]
            )
            self.console.print()
            self.console.print(files_info.render())

            # Management commands
            mgmt_info = InfoBox(
                "info",
                "🛠️ Management Commands",
                "Run these anytime to manage your VPN:",
                [
                    "[code]vpn-installer manage[/code] - Add/remove/change users",
                    "[code]vpn-installer validate[/code] - Run validation checklist",
                    "[code]vpn-installer install --resume[/code] - Resume interrupted install",
                    "[code]systemctl status haproxy openvpn@server x-ui[/code] - Check services",
                    "[code]journalctl -u openvpn@server -f[/code] - Follow OpenVPN logs",
                ]
            )
            self.console.print()
            self.console.print(mgmt_info.render())

            # Connection guide
            conn_info = InfoBox(
                "tip",
                "🔌 How to Connect",
                "1. Download your .ovpn profile:",
                [
                    f"   [url]http://{self.config.server_ip}/{self.config.client_name}.ovpn[/url]",
                    f"   Or copy from: [path]/etc/openvpn/profiles/{self.config.client_name}.ovpn[/path]",
                    "",
                    "2. Import into OpenVPN Connect (iOS/Android) or OpenVPN GUI (Windows/Mac/Linux)",
                    "",
                    "3. Enter your VPN credentials:",
                    f"   Username: [bold]{self.config.vpn_user}[/bold]",
                    f"   Password: [bold](your VPN password)[/bold]",
                    "",
                    "4. Connect! Verify with: [code]curl ifconfig.me[/code] (should show {self.config.server_ip})",
                ]
            )
            self.console.print()
            self.console.print(conn_info.render())

        # Final message
        final = Panel(
            Align.center(
                "[bold primary]Thank you for choosing privacy.[/bold primary]\n\n"
                "[dim]Your traffic is now yours alone.[/dim]\n\n"
                "[primary]Made by jackh0006[/primary] • [url]jackh109867@gmail.com[/url]\n"
                "[dim]Open source • No tracking • No telemetry • For digital freedom[/dim]"
            ),
            border_style="primary",
            padding=(1, 2),
        )
        self.console.print()
        self.console.print(final)

        self.console.print()
        self.console.print("[dim]Goodbye! 👋[/dim]")