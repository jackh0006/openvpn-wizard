"""
Parameter Collection Screen - Input validation with inline explanations.
"""

import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.columns import Columns
from rich.rule import Rule

from ui.theme import get_console, COLORS
from ui.components import InfoBox, CreditsFooter, SectionHeader
from core.config import (
    InstallConfig, validate_fqdn, validate_ip, validate_username,
    validate_password, validate_client_name
)
from utils.system import get_public_ip, get_wan_interface
from core.exceptions import ValidationError

# The 9 editable fields, in display order (menu numbers 1-9 map to this list)
EDITABLE_FIELDS = [
    "server_ip", "admin_user", "admin_pass", "vpn_user", "vpn_pass",
    "client_name", "domain1", "domain2", "reality_domain",
]


class ParameterScreen:
    """Parameter collection with real-time validation."""

    def __init__(self, console: Console = None):
        self.console = console or get_console()
        self.fields = {}
        self.errors = {}

    async def run(self) -> InstallConfig | None:
        """Run parameter collection. Returns config or None if back/exit."""
        # Pre-fill with auto-detected values
        await self._auto_detect()

        # Seed sensible defaults for optional-edit fields so the user only
        # edits what they want to change (validation uses self.fields, and
        # these defaults are shown in the form).
        self.fields.setdefault("admin_user", "admin")
        self.fields.setdefault("vpn_user", "vpnuser")
        self.fields.setdefault("client_name", "01-JH")

        while True:
            self._show_form()
            choice = await self._get_action()

            if choice == "validate":
                if await self._validate_all():
                    return self._build_config()
            elif choice == "back":
                return None
            elif choice == "exit":
                return None
            elif choice in EDITABLE_FIELDS:
                await self._edit_field(choice)

    async def _auto_detect(self):
        """Auto-detect server IP and interface."""
        self.console.print("[dim]Auto-detecting server IP...[/dim]")
        ip = get_public_ip()
        if ip and validate_ip(ip):
            self.fields["server_ip"] = ip
            self.fields["server_ip_confirmed"] = False

        iface = get_wan_interface()
        if iface:
            self.fields["wan_interface"] = iface

        # No default domains - user MUST provide their own

    def _show_form(self):
        """Display the parameter form."""
        self.console.clear()
        self.console.print(SectionHeader(2, 7, "Configuration", "⚙️").render())

        # Server IP (special - needs confirmation)
        self._render_field(
            "server_ip",
            "🌐 Server IP Address",
            "Your VPS public IPv4 address",
            self.fields.get("server_ip", ""),
            required=True,
            validator=validate_ip,
            show_confirm=not self.fields.get("server_ip_confirmed", False),
        )

        # Admin credentials
        self._render_field(
            "admin_user",
            "👤 Admin Username",
            "For 3X-UI panel login (alphanumeric, 1-32 chars)",
            self.fields.get("admin_user", "admin"),
            required=True,
            validator=validate_username,
        )

        self._render_field(
            "admin_pass",
            "🔐 Admin Password",
            "Panel password - use a STRONG passphrase (min 12 chars, mixed case, numbers, symbols)",
            self.fields.get("admin_pass", ""),
            required=True,
            validator=lambda p: validate_password(p)[0],
            is_password=True,
        )

        # VPN credentials
        self._render_field(
            "vpn_user",
            "🔑 VPN Username",
            "Your VPN login name (alphanumeric, 1-32 chars)",
            self.fields.get("vpn_user", "vpnuser"),
            required=True,
            validator=validate_username,
        )

        self._render_field(
            "vpn_pass",
            "🔐 VPN Password",
            "Your VPN password - DIFFERENT from admin! (min 12 chars, mixed case, numbers, symbols)",
            self.fields.get("vpn_pass", ""),
            required=True,
            validator=lambda p: validate_password(p)[0],
            is_password=True,
        )

        # Client profile name
        self._render_field(
            "client_name",
            "📄 Client Profile Name",
            "Display name in OpenVPN app (e.g., '01-JH', alphanumeric + dash)",
            self.fields.get("client_name", "01-JH"),
            required=True,
            validator=validate_client_name,
        )

        # Domains
        self.console.print()
        self.console.print(Rule("[primary]SNI Domains (for VLESS routing)[/primary]"))
        self.console.print("[dim]These domains route to different backends via HAProxy SNI matching.[/dim]\n")

        self._render_field(
            "domain1",
            "🌐 Domain 1 (VLESS-TLS)",
            "SNI for first VLESS-TLS+xhttp inbound (port 10000) — e.g., vpn1.yourdomain.com",
            self.fields.get("domain1", ""),
            required=True,
            validator=validate_fqdn,
        )

        self._render_field(
            "domain2",
            "🌐 Domain 2 (VLESS-TLS)",
            "SNI for second VLESS-TLS+xhttp inbound (port 10004) — e.g., vpn2.yourdomain.com",
            self.fields.get("domain2", ""),
            required=True,
            validator=validate_fqdn,
        )

        self._render_field(
            "reality_domain",
            "🕵️ Reality Domain",
            "SNI for VLESS-Reality inbound (use a popular site like example.com, google.com, etc.)",
            self.fields.get("reality_domain", ""),
            required=True,
            validator=validate_fqdn,
        )

        # Show errors
        if self.errors:
            self.console.print()
            error_panel = Panel(
                "\n".join(f"[error]✗ {field}: {msg}[/error]" for field, msg in self.errors.items()),
                title="[error]Validation Errors[/error]",
                border_style="error",
                padding=(1, 2),
            )
            self.console.print(error_panel)

        # Credits
        self.console.print()
        self.console.print(CreditsFooter.render())

    def _render_field(
        self,
        field_id: str,
        label: str,
        help_text: str,
        value: str,
        required: bool = True,
        validator=None,
        is_password: bool = False,
        show_confirm: bool = False,
    ):
        """Render a single form field."""
        # Check for error
        error = self.errors.get(field_id)
        border_style = "error" if error else "border"

        # Display value
        display_value = value
        if is_password and value:
            display_value = "•" * len(value)
        elif not value:
            display_value = "[dim](empty)[/dim]"

        # Required indicator
        req_marker = " [error]*[/error]" if required else ""

        # Build content
        content = []
        content.append(f"[bold]{label}{req_marker}[/bold]")
        content.append(f"[dim]{help_text}[/dim]")
        content.append(f"[primary]Current:[/primary] {display_value}")

        if error:
            content.append(f"[error]Error: {error}[/error]")

        if show_confirm and value:
            content.append("[warning]⚠️  Select this field (choice 1) and press Enter to confirm — or type a new IP[/warning]")

        panel = Panel(
            "\n".join(content),
            title=f"[primary]{field_id}[/primary]",
            border_style=border_style,
            padding=(1, 2),
        )
        self.console.print(panel)

    async def _get_action(self) -> str:
        """Get user action."""
        self.console.print()
        self.console.print("[primary]Actions:[/primary]")
        self.console.print("  [primary]1-9.[/primary] Edit field (number corresponds to field)")
        self.console.print("  [primary]v.[/primary] [bold]Validate & Continue[/bold]")
        self.console.print("  [primary]b.[/primary] [bold]Back[/bold]")
        self.console.print("  [primary]q.[/primary] [bold]Exit[/bold]")

        while True:
            try:
                choice = self.console.input("\n[primary]Choice: [/primary]").strip().lower()
                if choice in ("v", "validate", "continue", "done"):
                    return "validate"
                elif choice in ("b", "back"):
                    return "back"
                elif choice in ("q", "quit", "exit"):
                    return "exit"
                elif choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(EDITABLE_FIELDS):
                        return EDITABLE_FIELDS[idx]
                    self.console.print(f"[error]Invalid number. Use 1-{len(EDITABLE_FIELDS)}.[/error]")
                elif choice in EDITABLE_FIELDS:
                    return choice
                else:
                    self.console.print(f"[error]Invalid choice. Use 1-{len(EDITABLE_FIELDS)}, field name, or v/b/q.[/error]")
            except (KeyboardInterrupt, EOFError):
                return "exit"

    async def _edit_field(self, field_id: str):
        """Edit a specific field."""
        validators = {
            "server_ip": validate_ip,
            "admin_user": validate_username,
            "admin_pass": lambda p: validate_password(p)[0],
            "vpn_user": validate_username,
            "vpn_pass": lambda p: validate_password(p)[0],
            "client_name": validate_client_name,
            "domain1": validate_fqdn,
            "domain2": validate_fqdn,
            "reality_domain": validate_fqdn,
        }

        help_texts = {
            "server_ip": "Your VPS public IPv4 address",
            "admin_user": "3X-UI panel login (alphanumeric)",
            "admin_pass": "Panel password - STRONG passphrase (min 12 chars)",
            "vpn_user": "VPN login name (alphanumeric)",
            "vpn_pass": "VPN password - DIFFERENT from admin!",
            "client_name": "OpenVPN app display name (e.g., '01-JH')",
            "domain1": "SNI for VLESS-TLS inbound 1",
            "domain2": "SNI for VLESS-TLS inbound 2",
            "reality_domain": "SNI for Reality inbound (popular site)",
        }

        is_password = field_id in ("admin_pass", "vpn_pass")
        validator = validators.get(field_id)
        help_text = help_texts.get(field_id, "")

        # Special handling for server_ip confirmation
        # Enter = confirm the current (auto-detected) IP; typing a new IP replaces and confirms it
        if field_id == "server_ip":
            cur = self.fields.get("server_ip", "")
            if self.fields.get("server_ip_confirmed"):
                self.console.print(f"[dim]Current IP: {cur}[/dim]")
            new_val = await self._prompt_input(
                f"[primary]IP (Enter to confirm '{cur}', or type new): [/primary]",
                is_password=False,
            )
            if not new_val:
                # Enter pressed -> this IS the confirmation
                self.fields["server_ip_confirmed"] = True
                self.errors.pop("server_ip", None)
                self.console.print(f"[success]✓ Server IP confirmed: {cur}[/success]")
                return
            if not validate_ip(new_val):
                self.console.print("[error]Invalid IPv4 address. Try again (e.g. 203.0.113.10).[/error]")
                return
            self.fields["server_ip"] = new_val
            self.fields["server_ip_confirmed"] = True
            self.errors.pop("server_ip", None)
            self.console.print(f"[success]✓ Server IP set and confirmed: {new_val}[/success]")
            return

        while True:
            prompt_text = f"[primary]Enter {field_id}: [/primary]"
            if self.fields.get(field_id):
                prompt_text = f"[primary]New {field_id} (Enter to keep '{self.fields[field_id]}'): [/primary]"

            new_val = await self._prompt_input(prompt_text, is_password)

            if not new_val and self.fields.get(field_id):
                # Keep existing value
                return

            if not new_val and field_id in ("server_ip", "admin_user", "admin_pass", "vpn_user", "vpn_pass", "client_name"):
                self.console.print("[error]This field is required.[/error]")
                continue

            # Validate
            if validator and new_val:
                valid = validator(new_val)
                if not valid:
                    if field_id in ("admin_pass", "vpn_pass"):
                        _, msg = validate_password(new_val)
                        self.console.print(f"[error]{msg}[/error]")
                    else:
                        self.console.print(f"[error]Invalid format for {field_id}.[/error]")
                    continue

            # Special: confirm server IP
            if field_id == "server_ip":
                self.fields[field_id] = new_val
                self.fields["server_ip_confirmed"] = False
                self.console.print(f"[warning]Please confirm this IP on the main form.[/warning]")
            else:
                self.fields[field_id] = new_val

            # Clear error for this field
            self.errors.pop(field_id, None)
            return

    async def _prompt_input(self, prompt: str, is_password: bool) -> str:
        """Prompt for input with password masking."""
        if is_password:
            # Use getpass-like behavior
            import getpass
            self.console.print(prompt, end="")
            try:
                return getpass.getpass("")
            except (KeyboardInterrupt, EOFError):
                return ""
        else:
            try:
                return Prompt.ask(prompt, console=self.console, default="")
            except (KeyboardInterrupt, EOFError):
                return ""

    async def _validate_all(self) -> bool:
        """Validate all fields."""
        self.errors.clear()

        required = ["server_ip", "admin_user", "admin_pass", "vpn_user", "vpn_pass", "client_name", "domain1", "domain2", "reality_domain"]
        validators = {
            "server_ip": validate_ip,
            "admin_user": validate_username,
            "admin_pass": lambda p: validate_password(p)[0],
            "vpn_user": validate_username,
            "vpn_pass": lambda p: validate_password(p)[0],
            "client_name": validate_client_name,
            "domain1": validate_fqdn,
            "domain2": validate_fqdn,
            "reality_domain": validate_fqdn,
        }

        for field in required:
            value = self.fields.get(field, "")
            if not value:
                self.errors[field] = "This field is required"
            elif field in validators:
                if not validators[field](value):
                    if field in ("admin_pass", "vpn_pass"):
                        _, msg = validate_password(value)
                        self.errors[field] = msg
                    else:
                        self.errors[field] = "Invalid format"

        # Check admin != vpn password
        if self.fields.get("admin_pass") == self.fields.get("vpn_pass") and self.fields.get("admin_pass"):
            self.errors["vpn_pass"] = "VPN password must be different from admin password"

        # Check admin != vpn username
        if self.fields.get("admin_user") == self.fields.get("vpn_user"):
            self.errors["vpn_user"] = "VPN username must be different from admin username"

        # Confirm server IP
        if not self.fields.get("server_ip_confirmed"):
            self.errors["server_ip"] = "Please confirm the server IP on the form"

        if self.errors:
            return False
        return True

    def _build_config(self) -> InstallConfig:
        """Build InstallConfig from fields."""
        return InstallConfig(
            server_ip=self.fields["server_ip"],
            server_ip_confirmed=True,
            admin_user=self.fields["admin_user"],
            admin_pass=self.fields["admin_pass"],
            vpn_user=self.fields["vpn_user"],
            vpn_pass=self.fields["vpn_pass"],
            client_name=self.fields["client_name"],
            domain1=self.fields["domain1"],
            domain2=self.fields["domain2"],
            reality_domain=self.fields["reality_domain"],
            wan_interface=self.fields.get("wan_interface", ""),
        )