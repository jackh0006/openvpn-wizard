"""
Privacy Education Screen - What each entity sees/doesn't see.
Teaches like a 5-year-old with visual explanations.
"""

import asyncio
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.text import Text
from rich.align import Align
from rich.rule import Rule

from ui.theme import get_console, COLORS
from ui.components import InfoBox, CreditsFooter, SectionHeader


class PrivacyScreen:
    """Privacy education screen - explains what ISP, DPI, Websites, VPS see."""

    def __init__(self, console: Console = None):
        self.console = console or get_console()
        self.expanded = {}  # Track which sections are expanded

    async def run(self) -> bool:
        """Run the privacy screen. Returns True to continue, False to exit/back."""
        while True:
            self._show_privacy()
            choice = await self._get_choice()
            if choice == "continue":
                return True
            elif choice == "back":
                return False
            elif choice == "exit":
                return False
            elif choice.startswith("expand_"):
                entity = choice.split("_")[1]
                self.expanded[entity] = not self.expanded.get(entity, False)

    def _show_privacy(self):
        """Display the privacy education screen."""
        self.console.clear()

        # Header
        self.console.print(SectionHeader(1, 7, "Privacy Education", "🔍").render())

        # Intro
        intro = InfoBox(
            "tip",
            "Why This Matters",
            "Understanding what each party sees helps you trust the system. We explain it simply — like teaching a 5-year-old.",
            [
                "No jargon. No hand-waving. Just clear facts.",
                "Each section shows ✅ what they SEE and ❌ what they DON'T.",
                "Click 'Tell me more' for technical details.",
            ]
        )
        self.console.print(intro.render())

        # Four entities
        entities = [
            ("isp", "🏠 Your ISP (Internet Provider)", self._isp_content()),
            ("dpi", "🎯 DPI / Firewalls (Deep Packet Inspection)", self._dpi_content()),
            ("web", "🌐 Websites You Visit", self._website_content()),
            ("vps", "🖥️ Your VPS Provider", self._vps_content()),
        ]

        for entity_id, title, content in entities:
            is_expanded = self.expanded.get(entity_id, False)
            self.console.print(self._render_entity(entity_id, title, content, is_expanded))

        # Summary
        summary = InfoBox(
            "success",
            "The Bottom Line",
            "Your traffic looks like normal HTTPS web browsing to everyone.",
            [
                "✅ ISP sees only: Encrypted connection to your VPS on port 443",
                "✅ DPI sees only: Standard TLS 1.3 handshake (no VPN signatures)",
                "✅ Websites see only: Your VPS IP (not your home IP)",
                "✅ VPS provider sees only: Encrypted traffic volume",
                "🔒 Your actual browsing, DNS, and data are invisible to all of them.",
            ]
        )
        self.console.print()
        self.console.print(summary.render())

        # Credits
        self.console.print()
        self.console.print(CreditsFooter.render())

    def _render_entity(self, entity_id: str, title: str, content: dict, expanded: bool) -> Panel:
        """Render an entity panel with expand/collapse."""
        icon = "▼" if expanded else "▶"
        toggle_text = f"[primary]{icon} {'Show less' if expanded else 'Tell me more'}[/primary]"

        # Renderables (strings AND tables mixed - use Group, never str())
        renderables = []

        # Sees table
        if content["sees"]:
            renderables.append(Text.from_markup("[bold success]✅ What They SEE:[/bold success]"))
            sees_table = Table(show_header=False, box=None, padding=(0, 1))
            sees_table.add_column("", style="success", width=3)
            sees_table.add_column("", style="text")
            for item in content["sees"]:
                sees_table.add_row("✅", item)
            renderables.append(sees_table)

        # Doesn't see table
        if content["doesnt_see"]:
            renderables.append(Text())  # blank line
            renderables.append(Text.from_markup("[bold error]❌ What They DON'T See:[/bold error]"))
            doesnt_table = Table(show_header=False, box=None, padding=(0, 1))
            doesnt_table.add_column("", style="error", width=3)
            doesnt_table.add_column("", style="text")
            for item in content["doesnt_see"]:
                doesnt_table.add_row("❌", item)
            renderables.append(doesnt_table)

        # Expanded content
        if expanded and content.get("details"):
            renderables.append(Text())
            renderables.append(Text.from_markup("[dim]🔧 Technical Details:[/dim]"))
            for detail in content["details"]:
                renderables.append(Text.from_markup(f"  [dim]• {detail}[/dim]"))

        if expanded and content.get("analogy"):
            renderables.append(Text())
            renderables.append(Text.from_markup(f"[dim]💭 Analogy: {content['analogy']}[/dim]"))

        renderables.append(Text())
        renderables.append(Text.from_markup(toggle_text))

        return Panel(
            Group(*renderables),
            title=f"[primary]{title}[/primary]",
            border_style="primary" if expanded else "border",
            padding=(1, 2),
        )

    def _isp_content(self) -> dict:
        return {
            "sees": [
                "Encrypted TLS connection to YOUR VPS IP on port 443",
                "How much data you transfer (volume)",
                "When you connect and for how long (timing)",
                "That you're using port 443 (HTTPS port)",
            ],
            "doesnt_see": [
                "What websites you visit",
                "Your DNS queries (they go through the tunnel to 1.1.1.1/8.8.8.8)",
                "The actual content of your traffic",
                "That you're using a VPN (looks exactly like HTTPS)",
            ],
            "details": [
                "SNI is encrypted in TLS 1.3 with ECH (Encrypted Client Hello)",
                "OpenVPN packets are wrapped inside TLS - indistinguishable from HTTPS",
                "No VPN protocol signatures visible on the wire",
            ],
            "analogy": "Like mailing a sealed steel box via a courier. The courier (ISP) knows the destination address (VPS IP) and box weight (data volume), but cannot open the box to see what's inside.",
        }

    def _dpi_content(self) -> dict:
        return {
            "sees": [
                "TLS 1.3 ClientHello packet (standard handshake)",
                "SNI (Server Name Indication) if not using ECH",
                "Packet sizes and timing patterns",
                "Certificate exchange (public keys only)",
            ],
            "doesnt_see": [
                "OpenVPN protocol packets (hidden inside TLS)",
                "VLESS / VMess / Trojan / Shadowsocks signatures",
                "Reality handshake (looks exactly like Cloudflare TLS)",
                "Any application-layer data (fully encrypted)",
            ],
            "details": [
                "TLS 1.3 encrypts almost all handshake data after ServerHello",
                "Reality uses X25519 key exchange + short IDs - mimics real Cloudflare",
                "xhttp transport makes VLESS look like HTTP/2 traffic",
                "No packet fingerprinting can distinguish this from normal web traffic",
            ],
            "analogy": "Like a security guard checking IDs at a building entrance. They see people enter (TLS handshake) but can't read their private conversations inside (encrypted payload).",
        }

    def _website_content(self) -> dict:
        return {
            "sees": [
                "Your VPS IP address as the source (not your home IP)",
                "Standard browser headers (we spoof Chrome)",
                "Normal TLS connection to their server",
                "Request paths, headers, cookies (if you send them)",
            ],
            "doesnt_see": [
                "Your real home IP address",
                "Your ISP or geographic location",
                "That your traffic is tunneled through a VPN",
                "Any correlation to your real identity",
            ],
            "details": [
                "VLESS Reality inbound spoofs Chrome User-Agent and headers exactly",
                "xhttp transport uses realistic paths like /assets/v3/sync",
                "Websites see Cloudflare's IP if using Reality with Cloudflare SNI",
            ],
            "analogy": "Like wearing a perfect mask. The website sees the mask (VPS IP) and hears a normal voice (Chrome headers), but never sees your real face (home IP).",
        }

    def _vps_content(self) -> dict:
        return {
            "sees": [
                "Encrypted traffic on port 443 (volume, timing)",
                "Resource usage: CPU, RAM, disk, network",
                "Config files on disk (but keys are protected)",
                "System logs (connection counts, errors)",
            ],
            "doesnt_see": [
                "Your decrypted traffic content (TLS terminates in memory)",
                "Your browsing history or DNS queries",
                "Your passwords or encryption keys",
                "Client certificates (optionally encrypted at rest)",
            ],
            "details": [
                "Private keys stored with 600 permissions, owned by root",
                "TLS session keys exist only in memory, never written to disk",
                "OpenVPN runs as 'nobody' user, chrooted",
                "HAProxy runs chrooted in /var/lib/haproxy",
            ],
            "analogy": "Like a hotel manager. They know which room you're in (VPS) and how much water/electricity you use (resources), but they don't have a key to your room and can't see what you're doing inside.",
        }

    async def _get_choice(self) -> str:
        """Get user choice."""
        self.console.print()
        self.console.print("[primary]1.[/primary] [bold]I Understand, Continue[/bold] [dim]- Proceed to configuration[/dim]")
        self.console.print("[primary]2.[/primary] [bold]Back[/bold] [dim]- Return to welcome screen[/dim]")
        self.console.print("[primary]3.[/primary] [bold]Exit[/bold] [dim]- Quit installer[/dim]")

        while True:
            try:
                choice = self.console.input("\n[primary]Your choice [1-3]: [/primary]").strip()
                if choice in ("1", "c", "C", "continue", "i", "I", "understand"):
                    return "continue"
                elif choice in ("2", "b", "B", "back"):
                    return "back"
                elif choice in ("3", "e", "E", "exit", "quit"):
                    return "exit"
                elif choice.startswith("expand_") or choice in ("isp", "dpi", "web", "vps"):
                    # Handle expand clicks (if we add clickable links later)
                    return choice
                else:
                    self.console.print("[error]Invalid choice. Enter 1, 2, or 3.[/error]")
            except (KeyboardInterrupt, EOFError):
                return "exit"