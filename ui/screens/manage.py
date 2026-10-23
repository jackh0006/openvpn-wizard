"""
Management Screen - User management menu (add/remove/change/rename/list).
"""

import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.align import Align

from ui.theme import get_console, COLORS
from ui.components import InfoBox, CreditsFooter, SectionHeader
from core.config import InstallConfig
from management.user_mgr import UserManager


class ManageScreen:
    """User management menu."""

    def __init__(self, console: Console, user_mgr: UserManager, config: InstallConfig):
        self.console = console
        self.user_mgr = user_mgr
        self.config = config

    async def run(self):
        """Run management menu loop."""
        while True:
            self._show_menu()
            choice = await self._get_choice()

            if choice == "exit":
                break
            elif choice == "add":
                await self._add_user()
            elif choice == "remove":
                await self._remove_user()
            elif choice == "change_pass":
                await self._change_password()
            elif choice == "rename":
                await self._rename_user()
            elif choice == "export":
                await self._export_profile()
            elif choice == "list":
                await self._list_users()
            elif choice == "refresh":
                continue  # Just refresh

    def _show_menu(self):
        """Display management menu."""
        self.console.clear()
        self.console.print(SectionHeader(6, 7, "User Management", "👥").render())

        # Get users
        users = self.user_mgr.list_users()

        # User table
        table = Table(show_header=True, header_style="primary", box=None, padding=(0, 1))
        table.add_column("#", width=3, justify="right")
        table.add_column("Name", style="text", width=20)
        table.add_column("Username", style="text", width=20)
        table.add_column("Created", style="text", width=18)
        table.add_column("Status", width=15)

        for i, user in enumerate(users, 1):
            status = "[success]🟢 Active[/success]" if not user.get("revoked") else "[error]🔴 Revoked[/error]"
            table.add_row(
                str(i),
                user.get("name", ""),
                user.get("username", ""),
                user.get("created_at", "")[:19],
                status,
            )

        if not users:
            table.add_row("", "[dim](no users)[/dim]", "", "", "")

        self.console.print(Panel(
            table,
            title=f"[primary]Users ({len([u for u in users if not u.get('revoked')])} active, {len([u for u in users if u.get('revoked')])} revoked)[/primary]",
            border_style="primary",
            padding=(1, 2),
        ))

        # Menu options
        self.console.print()
        self.console.print("[primary]Actions:[/primary]")
        self.console.print("  [primary]1.[/primary] [bold]➕ Add User[/bold]")
        self.console.print("  [primary]2.[/primary] [bold]🗑️ Remove User[/bold]")
        self.console.print("  [primary]3.[/primary] [bold]🔑 Change Password[/bold]")
        self.console.print("  [primary]4.[/primary] [bold]✏️ Rename User[/bold]")
        self.console.print("  [primary]5.[/primary] [bold]📄 Export Profile[/bold]")
        self.console.print("  [primary]6.[/primary] [bold]📋 List All Users (detailed)[/bold]")
        self.console.print("  [primary]7.[/primary] [bold]🔄 Refresh[/bold]")
        self.console.print("  [primary]b.[/primary] [bold]Back to Main[/bold]")
        self.console.print("  [primary]q.[/primary] [bold]Exit[/bold]")

        self.console.print()
        self.console.print(CreditsFooter.render())

    async def _get_choice(self) -> str:
        """Get user choice."""
        while True:
            try:
                choice = self.console.input("\n[primary]Choice: [/primary]").strip().lower()
                if choice in ("1", "a", "add"):
                    return "add"
                elif choice in ("2", "r", "remove", "del", "delete"):
                    return "remove"
                elif choice in ("3", "p", "pass", "password", "change"):
                    return "change_pass"
                elif choice in ("4", "n", "name", "rename"):
                    return "rename"
                elif choice in ("5", "e", "export", "profile"):
                    return "export"
                elif choice in ("6", "l", "list", "ls"):
                    return "list"
                elif choice in ("7", "refresh", "reload"):
                    return "refresh"
                elif choice in ("b", "back"):
                    return "exit"
                elif choice in ("q", "quit", "exit"):
                    return "exit"
                else:
                    self.console.print("[error]Invalid choice.[/error]")
            except (KeyboardInterrupt, EOFError):
                return "exit"

    async def _add_user(self):
        """Add a new user."""
        self.console.print()
        self.console.print(Panel("[bold]Add New VPN User[/bold]", border_style="primary"))

        # Get name
        name = Prompt.ask("[primary]Profile name (e.g., 02-Alice)[/primary]", console=self.console)
        if not name:
            return

        # Get username
        username = Prompt.ask("[primary]VPN username (alphanumeric)[/primary]", console=self.console)
        if not username:
            return

        # Get password
        import getpass
        self.console.print("[primary]VPN password (min 12 chars, strong)[/primary]", end=" ")
        password = getpass.getpass("")
        if not password:
            return

        # Confirm password
        self.console.print("[primary]Confirm password[/primary]", end=" ")
        confirm = getpass.getpass("")
        if password != confirm:
            self.console.print("[error]Passwords don't match.[/error]")
            await asyncio.sleep(1)
            return

        try:
            with self.console.status("[primary]Creating user...[/primary]"):
                profile_path = self.user_mgr.add_user(name, username, password)

            self.console.print(f"[success]✅ User '{name}' created successfully![/success]")
            self.console.print(f"[primary]Profile:[/primary] [path]{profile_path}[/path]")
            self.console.print(f"[primary]Web download:[/primary] [url]http://{self.config.server_ip}/{name}.ovpn[/url]")

        except Exception as e:
            self.console.print(f"[error]Failed to add user: {e}[/error]")

        await self._pause()

    async def _remove_user(self):
        """Remove a user."""
        users = self.user_mgr.list_users()
        active_users = [u for u in users if not u.get("revoked")]

        if not active_users:
            self.console.print("[warning]No active users to remove.[/warning]")
            await self._pause()
            return

        self.console.print()
        self.console.print("[primary]Select user to remove:[/primary]")
        for i, u in enumerate(active_users, 1):
            self.console.print(f"  [primary]{i}.[/primary] {u['name']} ({u['username']})")

        try:
            choice = Prompt.ask("[primary]Number (Enter to cancel)[/primary]", console=self.console, default="")
            if not choice:
                return

            idx = int(choice) - 1
            if 0 <= idx < len(active_users):
                user = active_users[idx]
                confirm = Confirm.ask(
                    f"[warning]Really remove '{user['name']}' ({user['username']})? This revokes their certificate.[/warning]",
                    console=self.console,
                    default=False,
                )
                if confirm:
                    with self.console.status("[primary]Removing user...[/primary]"):
                        self.user_mgr.remove_user(user["name"])
                    self.console.print(f"[success]✅ User '{user['name']}' removed.[/success]")
        except (ValueError, IndexError):
            self.console.print("[error]Invalid selection.[/error]")

        await self._pause()

    async def _change_password(self):
        """Change user password."""
        users = self.user_mgr.list_users()
        active_users = [u for u in users if not u.get("revoked")]

        if not active_users:
            self.console.print("[warning]No active users.[/warning]")
            await self._pause()
            return

        self.console.print()
        self.console.print("[primary]Select user:[/primary]")
        for i, u in enumerate(active_users, 1):
            self.console.print(f"  [primary]{i}.[/primary] {u['name']} ({u['username']})")

        try:
            choice = Prompt.ask("[primary]Number (Enter to cancel)[/primary]", console=self.console, default="")
            if not choice:
                return

            idx = int(choice) - 1
            if 0 <= idx < len(active_users):
                user = active_users[idx]

                import getpass
                self.console.print("[primary]New password (min 12 chars, strong)[/primary]", end=" ")
                new_pass = getpass.getpass("")
                if not new_pass:
                    return

                self.console.print("[primary]Confirm new password[/primary]", end=" ")
                confirm = getpass.getpass("")
                if new_pass != confirm:
                    self.console.print("[error]Passwords don't match.[/error]")
                    await self._pause()
                    return

                with self.console.status("[primary]Changing password...[/primary]"):
                    self.user_mgr.change_password(user["name"], new_pass)

                self.console.print(f"[success]✅ Password changed for '{user['name']}'.[/success]")
        except (ValueError, IndexError):
            self.console.print("[error]Invalid selection.[/error]")

        await self._pause()

    async def _rename_user(self):
        """Rename a user (profile name only)."""
        users = self.user_mgr.list_users()
        active_users = [u for u in users if not u.get("revoked")]

        if not active_users:
            self.console.print("[warning]No active users.[/warning]")
            await self._pause()
            return

        self.console.print()
        self.console.print("[primary]Select user to rename:[/primary]")
        for i, u in enumerate(active_users, 1):
            self.console.print(f"  [primary]{i}.[/primary] {u['name']} ({u['username']})")

        try:
            choice = Prompt.ask("[primary]Number (Enter to cancel)[/primary]", console=self.console, default="")
            if not choice:
                return

            idx = int(choice) - 1
            if 0 <= idx < len(active_users):
                user = active_users[idx]

                new_name = Prompt.ask(f"[primary]New profile name (current: {user['name']})[/primary]", console=self.console)
                if not new_name or new_name == user["name"]:
                    return

                with self.console.status("[primary]Renaming user...[/primary]"):
                    self.user_mgr.rename_user(user["name"], new_name)

                self.console.print(f"[success]✅ User renamed to '{new_name}'.[/success]")
        except (ValueError, IndexError):
            self.console.print("[error]Invalid selection.[/error]")

        await self._pause()

    async def _export_profile(self):
        """Export user profile."""
        users = self.user_mgr.list_users()
        active_users = [u for u in users if not u.get("revoked")]

        if not active_users:
            self.console.print("[warning]No active users.[/warning]")
            await self._pause()
            return

        self.console.print()
        self.console.print("[primary]Select user to export:[/primary]")
        for i, u in enumerate(active_users, 1):
            self.console.print(f"  [primary]{i}.[/primary] {u['name']} ({u['username']})")

        try:
            choice = Prompt.ask("[primary]Number (Enter to cancel)[/primary]", console=self.console, default="")
            if not choice:
                return

            idx = int(choice) - 1
            if 0 <= idx < len(active_users):
                user = active_users[idx]

                with self.console.status("[primary]Generating profile...[/primary]"):
                    profile_path = self.user_mgr.export_profile(user["name"])

                self.console.print(f"[success]✅ Profile exported to:[/success] [path]{profile_path}[/path]")
                self.console.print(f"[primary]Web download:[/primary] [url]http://{self.config.server_ip}/{user['name']}.ovpn[/url]")
        except (ValueError, IndexError):
            self.console.print("[error]Invalid selection.[/error]")

        await self._pause()

    async def _list_users(self):
        """Show detailed user list."""
        users = self.user_mgr.list_users()

        self.console.print()
        table = Table(show_header=True, header_style="primary", box=None, padding=(0, 1))
        table.add_column("Name", width=20)
        table.add_column("Username", width=20)
        table.add_column("Created", width=20)
        table.add_column("Revoked", width=10)
        table.add_column("Cert Serial", width=20)

        for u in users:
            table.add_row(
                u.get("name", ""),
                u.get("username", ""),
                u.get("created_at", "")[:19],
                "Yes" if u.get("revoked") else "No",
                u.get("cert_serial", "")[:20],
            )

        self.console.print(Panel(table, title="[primary]All Users[/primary]", border_style="primary"))
        await self._pause()

    async def _pause(self):
        """Pause for user to read output."""
        self.console.print()
        self.console.print("[dim]Press Enter to continue...[/dim]")
        try:
            self.console.input()
        except (KeyboardInterrupt, EOFError):
            pass