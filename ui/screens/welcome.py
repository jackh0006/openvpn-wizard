"""
Welcome Screen - Hero screen with philosophy and credits.
"""

import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.columns import Columns
from rich.text import Text

from ui.theme import get_console, LOGO, SMALL_LOGO, COLORS
from ui.components import InfoBox, CreditsFooter


class WelcomeScreen:
    """Welcome/hero screen."""

    def __init__(self, console: Console = None):
        self.console = console or get_console()

    async def run(self) -> bool:
        """Run the welcome screen. Returns True to continue, False to exit."""
        self._show_welcome()
        return await self._get_choice()

    def _show_welcome(self):
        """Display the welcome screen."""
        self.console.clear()

        # Main logo
        self.console.print(f"[primary]{LOGO}[/primary]")

        # Philosophy box
        philosophy = InfoBox(
            "tip",
            "Our Philosophy",
            "We build tools that respect your privacy. No tracking. No phones home. Ever.",
            [
                "🔒 Your data stays on YOUR server",
                "🔍 Zero telemetry, zero analytics",
                "📖 Completely open source (MIT licensed)",
                "🛡️ Designed for maximum stealth & security",
                "⚡ Optimized for speed & reliability",
            ]
        )
        self.console.print()
        self.console.print(philosophy.render())

        # What this installs
        features = InfoBox(
            "info",
            "What This Installs",
            "A stealthy, multiplexed VPN stack on a single port (443)",
            [
                "🎯 HAProxy - Single public listener on port 443",
                "🔐 OpenVPN - TLS-crypt v1, AES-256-GCM, TLS 1.3 only (no SNI)",
                "🌐 VLESS-TLS + xhttp - 2 domains with realistic paths",
                "🕵️ VLESS-Reality - Mimics Cloudflare, indistinguishable from HTTPS",
                "👤 PAM authentication - System users, secure passwords",
                "🔑 Easy-RSA PKI - RSA-4096 certs, per-client certificates",
                "📦 SQLite user database - Add/remove/rename users anytime",
                "🧱 Hardened kernel & firewall - IPv4 only, NAT, no leaks",
            ]
        )
        self.console.print(features.render())

        # Architecture diagram
        arch = Panel(
            Align.center(
                "[bold]Client[/bold] → [primary]:443[/primary] → [bold]HAProxy[/bold] (SNI Router)\n\n"
                "    ├─ No SNI → [success]OpenVPN[/success] (127.0.0.1:1194)\n"
                "    ├─ your-domain1.com → [info]VLESS-TLS[/info] (127.0.0.1:10000)\n"
                "    ├─ your-domain2.com → [info]VLESS-TLS[/info] (127.0.0.1:10004)\n"
                "    └─ popular-site.com → [warning]VLESS-Reality[/warning] (127.0.0.1:443)\n\n"
                "[dim]Only HAProxy binds to public 0.0.0.0:443. Everything else → 127.0.0.1[/dim]"
            ),
            title="[primary]🏗️ Architecture[/primary]",
            border_style="primary",
            padding=(1, 2),
        )
        self.console.print()
        self.console.print(arch)

        # Credits
        self.console.print()
        self.console.print(CreditsFooter.render())

    async def _get_choice(self) -> bool:
        """Get user choice to continue or exit."""
        self.console.print()
        self.console.print("[primary]1.[/primary] [bold]Continue[/bold] [dim]- Start installation[/dim]")
        self.console.print("[primary]2.[/primary] [bold]Exit[/bold] [dim]- Quit installer[/dim]")

        while True:
            try:
                choice = self.console.input("\n[primary]Your choice [1-2]: [/primary]").strip()
                if choice in ("1", "c", "C", "continue"):
                    return True
                elif choice in ("2", "e", "E", "exit", "quit"):
                    self.console.print("\n[dim]Goodbye! Your privacy matters.[/dim]")
                    return False
                else:
                    self.console.print("[error]Invalid choice. Enter 1 or 2.[/error]")
            except (KeyboardInterrupt, EOFError):
                return False