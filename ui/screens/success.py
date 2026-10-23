"""
Success Screen - Completion with client profile and QR code.
"""

import asyncio
import io
import base64
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.columns import Columns

# Optional QR code support
try:
    import qrcode
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False

from ui.theme import get_console, COLORS
from ui.components import InfoBox, CreditsFooter, SectionHeader
from core.config import InstallConfig
from core.state import InstallState


class SuccessScreen:
    """Success screen with client profile delivery."""

    def __init__(self, console: Console, config: InstallConfig, state: InstallState):
        self.console = console
        self.config = config
        self.state = state

    async def run(self):
        """Display success screen."""
        self.console.clear()
        self.console.print(SectionHeader(5, 7, "Installation Complete!", "🎉").render())

        # Success banner
        banner = Panel(
            Align.center(
                "[bold success]✅ VPN Stack Successfully Deployed![/bold success]\n\n"
                "[primary]Your stealthy, multiplexed VPN is ready on port 443.[/primary]"
            ),
            border_style="success",
            padding=(1, 2),
        )
        self.console.print(banner)

        # Client profile info
        profile_info = InfoBox(
            "file",
            "📄 Client Profile Generated",
            f"Profile: [path]{self.config.client_ovpn_path}[/path]",
            [
                f"Contains: CA cert, client cert, client key, TLS-crypt key",
                f"Ready to import into OpenVPN Connect, V2rayNG, etc.",
                f"Web download: [url]{self.config.web_ovpn_url}[/url]",
            ]
        )
        self.console.print()
        self.console.print(profile_info.render())

        # Connection test
        test_info = InfoBox(
            "tip",
            "🧪 Test Your Connection",
            "Run this on your client device after importing the .ovpn:",
            [
                "[code]openvpn --config your-profile.ovpn[/code]",
                "",
                "Or use OpenVPN Connect app (iOS/Android) → Import profile",
                "",
                "Verify: [code]curl -I https://example.com[/code] (should show 200)",
                "Check IP: [code]curl ifconfig.me[/code] (should show VPS IP)",
            ]
        )
        self.console.print()
        self.console.print(test_info.render())

        # What's running
        running_info = InfoBox(
            "server",
            "🖥️ Services Running",
            "All services are active and managed by systemd:",
            [
                "✅ HAProxy - Listening on 0.0.0.0:443 (SNI router)",
                "✅ OpenVPN - Listening on 127.0.0.1:1194 (TCP)",
                "✅ 3X-UI - VLESS inbounds on 10000, 10004, 443 (local)",
            ]
        )
        self.console.print()
        self.console.print(running_info.render())

        # QR Code for mobile
        if self._has_qrcode():
            qr_panel = self._generate_qr_panel()
            self.console.print()
            self.console.print(qr_panel)

        # Next steps
        next_info = InfoBox(
            "info",
            "📋 What's Next?",
            "Your VPN is ready. Here's what you can do:",
            [
                "1. Download the .ovpn file to your device",
                "2. Import into OpenVPN client",
                "3. Connect with your VPN username/password",
                "4. Run 'vpn-installer manage' to add more users",
                "5. Run 'vpn-installer validate' to verify everything",
            ]
        )
        self.console.print()
        self.console.print(next_info.render())

        # Credits
        self.console.print()
        self.console.print(CreditsFooter.render())

        # Wait for user
        self.console.print()
        self.console.print("[dim]Press Enter to continue...[/dim]")
        try:
            self.console.input()
        except (KeyboardInterrupt, EOFError):
            pass

    def _has_qrcode(self) -> bool:
        """Check if qrcode library is available."""
        return HAS_QRCODE

    def _generate_qr_panel(self) -> Panel:
        """Generate QR code for .ovpn download URL."""
        if not HAS_QRCODE:
            return Panel(
                "[dim]QR code generation not available (install 'qrcode' package)[/dim]",
                title="[primary]📱 QR Code[/primary]",
                border_style="primary",
                padding=(1, 2),
            )
        try:
            qr = qrcode.QRCode(version=1, box_size=2, border=1)
            qr.add_data(self.config.web_ovpn_url)
            qr.make(fit=True)

            # Render as ASCII
            from io import StringIO
            f = StringIO()
            qr.print_ascii(out=f)
            qr_ascii = f.getvalue()

            return Panel(
                f"[bold]Scan to download .ovpn on mobile:[/bold]\n\n{qr_ascii}\n[dim]{self.config.web_ovpn_url}[/dim]",
                title="[primary]📱 QR Code[/primary]",
                border_style="primary",
                padding=(1, 2),
            )
        except Exception:
            return Panel(
                "[dim]QR code generation failed[/dim]",
                title="[primary]📱 QR Code[/primary]",
                border_style="primary",
                padding=(1, 2),
            )