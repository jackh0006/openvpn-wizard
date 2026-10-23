"""
Step-by-Step Confirmation Screen - Ask before doing anything.
"""

import asyncio
from typing import List, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.rule import Rule

from ui.theme import get_console, COLORS
from ui.components import ConfirmAction, CreditsFooter, SectionHeader, ProgressStep
from core.config import InstallConfig


class ConfirmScreen:
    """Step-by-step confirmation with explanations."""

    STEP_DETAILS = {
        "packages": {
            "what": "Install required system packages (HAProxy, OpenVPN, Easy-RSA, 3X-UI, etc.)",
            "why": "These are the building blocks. Without them, nothing works.",
            "files": [
                "/etc/apt/sources.list (package sources)",
                "/var/lib/dpkg/ (package database)",
            ],
            "rollback": "Packages can be removed with apt-get purge",
            "time": "~30-60 seconds",
            "warning": "Requires internet access to download packages",
        },
        "haproxy": {
            "what": "Write HAProxy config with SNI routing rules for all 4 backends",
            "why": "HAProxy is the ONLY public listener on port 443. It decides where traffic goes based on SNI.",
            "files": [
                "/etc/haproxy/haproxy.cfg (main config)",
                "/etc/haproxy/haproxy.cfg.backup (auto-backup)",
            ],
            "rollback": "Automatic restore from backup on failure",
            "time": "~3 seconds",
            "warning": "This will REPLACE existing HAProxy config",
        },
        "xui": {
            "what": "Deploy 3X-UI panel with 2 inbounds (VLESS-TLS+xhttp on 10000, VLESS-Reality+xhttp on 443)",
            "why": "3X-UI manages VLESS users and inbounds. We configure it via SQLite database directly.",
            "files": [
                "/etc/x-ui/x-ui.db (SQLite database with inbound configs)",
                "/etc/x-ui/cert.pem, key.pem (TLS certificates for VLESS-TLS)",
                "/usr/local/x-ui/ (3X-UI binary and assets)",
            ],
            "rollback": "Database backup restored, certs preserved",
            "time": "~10 seconds",
            "warning": "Installs 3X-UI from official GitHub release",
        },
        "pki": {
            "what": "Bootstrap Easy-RSA PKI: CA, server cert, client cert, DH params, TLS-crypt key",
            "why": "PKI provides the cryptographic foundation. Every client gets a unique certificate.",
            "files": [
                "/etc/openvpn/pki/ (entire PKI directory)",
                "/etc/openvpn/ca.crt, server.crt, server.key, dh.pem, ta.key (runtime copies)",
            ],
            "rollback": "PKI directory can be deleted and recreated",
            "time": "~15-30 seconds (DH params take time)",
            "warning": "Generates 2048-bit DH parameters - may take 10-20s",
        },
        "pam": {
            "what": "Create PAM system user for VPN authentication",
            "why": "OpenVPN uses PAM (plugable auth) to verify username/password against system accounts.",
            "files": [
                "/etc/passwd, /etc/shadow (user account)",
                "/etc/openvpn/users.db (SQLite record)",
            ],
            "rollback": "User can be deleted with userdel",
            "time": "~1 second",
            "warning": "Creates a system user with /usr/sbin/nologin shell",
        },
        "openvpn": {
            "what": "Write OpenVPN server config (TCP 1194, TLS-crypt v1, AES-256-GCM, TLS 1.3 only)",
            "why": "This is the OpenVPN server configuration. Maximum stealth & performance settings.",
            "files": [
                "/etc/openvpn/server.conf (main config)",
            ],
            "rollback": "Config file restored from backup",
            "time": "~2 seconds",
            "warning": "Binds ONLY to 127.0.0.1:1194 (not public)",
        },
        "kernel_fw": {
            "what": "Enable IPv4 forwarding, configure iptables NAT for VPN subnet",
            "why": "Kernel forwarding + NAT allows VPN clients to reach the internet through the VPS.",
            "files": [
                "/etc/sysctl.d/99-openvpn.conf (IP forwarding)",
                "/etc/iptables/rules.v4 (persistent NAT rules)",
            ],
            "rollback": "sysctl reverted, iptables rules flushed",
            "time": "~3 seconds",
            "warning": "Modifies kernel parameters and firewall rules",
        },
        "services": {
            "what": "Enable and start all services: HAProxy, OpenVPN, 3X-UI",
            "why": "Services must be running for the VPN to work. systemd manages them.",
            "files": [
                "/etc/systemd/system/ (service units)",
            ],
            "rollback": "Services stopped and disabled",
            "time": "~5 seconds",
            "warning": "Restarts services if already running",
        },
        "client_profile": {
            "what": "Generate client .ovpn file with embedded certs, keys, CA, and TLS-crypt",
            "why": "Single-file profile contains everything needed to connect. Import into any OpenVPN client.",
            "files": [
                f"/etc/openvpn/profiles/{{client_name}}.ovpn (client profile)",
                f"/var/www/vpn-profiles/{{client_name}}.ovpn (web download)",
            ],
            "rollback": "Profile files deleted",
            "time": "~2 seconds",
            "warning": "Contains sensitive certificates - handle securely",
        },
        "user_db": {
            "what": "Store user record in SQLite database for management",
            "why": "Enables add/remove/change-password/rename operations later.",
            "files": [
                "/etc/openvpn/users.db (SQLite database)",
            ],
            "rollback": "Database record marked revoked",
            "time": "~1 second",
            "warning": "Stores password hash (SHA-512 crypt)",
        },
    }

    def __init__(self, console: Console, steps: List[Tuple[str, str, object]], config: InstallConfig):
        self.console = console
        self.steps = steps
        self.config = config
        self.skipped = set()

    async def run(self) -> bool:
        """Run confirmation flow. Returns True to proceed, False to back/exit."""
        while True:
            self._show_overview()
            choice = await self._get_choice()

            if choice == "proceed":
                return True
            elif choice == "back":
                return False
            elif choice == "exit":
                return False
            elif choice.startswith("toggle_"):
                step_id = choice.split("_")[1]
                if step_id in self.skipped:
                    self.skipped.remove(step_id)
                else:
                    self.skipped.add(step_id)
            elif choice.startswith("detail_"):
                step_id = choice.split("_")[1]
                await self._show_detail(step_id)

    def _show_overview(self):
        """Show all steps with status."""
        self.console.clear()
        self.console.print(SectionHeader(3, 7, "Confirm Installation Steps", "✅").render())

        intro = Panel(
            "[bold]Review each step below.[/bold] Each shows what it does, why it's needed, what files change, and rollback info.\n"
            "[dim]Press the step number to see details. Type 'skip' to toggle skip (for re-runs).[/dim]",
            title="[primary]Instructions[/primary]",
            border_style="primary",
            padding=(1, 2),
        )
        self.console.print(intro)

        # Steps table
        table = Table(show_header=True, header_style="primary", box=None, padding=(0, 1))
        table.add_column("#", width=3, justify="right")
        table.add_column("Step", style="text", width=35)
        table.add_column("Status", width=12)
        table.add_column("Time", width=12)

        for i, (step_id, display_name, _) in enumerate(self.steps, 1):
            skipped = step_id in self.skipped
            status = "[step.skipped]⊘ SKIP[/step.skipped]" if skipped else "[step.pending]○ PENDING[/step.pending]"
            time_est = self.STEP_DETAILS.get(step_id, {}).get("time", "~?s")
            table.add_row(str(i), display_name, status, time_est)

        self.console.print()
        self.console.print(table)

        # Summary
        pending_count = len(self.steps) - len(self.skipped)
        self.console.print()
        summary = f"[bold]{pending_count}/{len(self.steps)} steps will execute[/bold]"
        if self.skipped:
            summary += f" [warning]({len(self.skipped)} skipped)[/warning]"
        self.console.print(Align.center(summary))

        self.console.print()
        self.console.print(CreditsFooter.render())

    async def _get_choice(self) -> str:
        """Get user choice."""
        self.console.print()
        self.console.print("[primary]Actions:[/primary]")
        self.console.print("  [primary]1-10.[/primary] View step details")
        self.console.print("  [primary]s <num>.[/primary] Toggle skip for step (e.g., 's 3')")
        self.console.print("  [primary]p.[/primary] [bold]Proceed with Installation[/bold]")
        self.console.print("  [primary]b.[/primary] [bold]Back[/bold]")
        self.console.print("  [primary]q.[/primary] [bold]Exit[/bold]")

        while True:
            try:
                choice = self.console.input("\n[primary]Choice: [/primary]").strip().lower()
                if choice in ("p", "proceed", "continue", "go", "y", "yes"):
                    return "proceed"
                elif choice in ("b", "back"):
                    return "back"
                elif choice in ("q", "quit", "exit"):
                    return "exit"
                elif choice.startswith("s "):
                    try:
                        num = int(choice.split()[1]) - 1
                        if 0 <= num < len(self.steps):
                            return f"toggle_{self.steps[num][0]}"
                    except (ValueError, IndexError):
                        pass
                elif choice.isdigit():
                    num = int(choice) - 1
                    if 0 <= num < len(self.steps):
                        return f"detail_{self.steps[num][0]}"
                else:
                    self.console.print("[error]Invalid choice.[/error]")
            except (KeyboardInterrupt, EOFError):
                return "exit"

    async def _show_detail(self, step_id: str):
        """Show detailed confirmation for a step."""
        detail = self.STEP_DETAILS.get(step_id, {})
        step_name = next((name for sid, name, _ in self.steps if sid == step_id), step_id)

        confirm = ConfirmAction(
            self.console,
            title=f"Step: {step_name}",
            what=detail.get("what", "Unknown"),
            why=detail.get("why", "Unknown"),
            files_affected=detail.get("files", []),
            rollback_info=detail.get("rollback", "Manual rollback required"),
            estimated_time=detail.get("time", "Unknown"),
            warning=detail.get("warning"),
            show_skip=True,
            show_back=True,
        )

        # We don't use the confirm's ask() since we're in a sub-menu
        # Just display it
        self.console.clear()
        self.console.print(confirm.render())
        self.console.print()
        self.console.print("[dim]Press Enter to return...[/dim]")
        try:
            self.console.input()
        except (KeyboardInterrupt, EOFError):
            pass