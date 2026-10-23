#!/usr/bin/env python3
"""
OpenVPN-over-HAProxy Installer
Made by jackh0006 • jackh109867@gmail.com

A world-class, open-source, educational installer for Ubuntu VPS
that deploys a stealthy, multiplexed VPN stack on port 443.
"""

import sys
import asyncio
from pathlib import Path

# Add installer to path
sys.path.insert(0, str(Path(__file__).parent))

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from ui.theme import THEME

from core.config import InstallConfig
from core.state import InstallState, StateManager
from core.logger import setup_logger
from ui.screens.welcome import WelcomeScreen
from ui.screens.privacy import PrivacyScreen
from ui.screens.parameters import ParameterScreen
from ui.screens.confirm import ConfirmScreen
from ui.screens.progress import ProgressScreen
from ui.screens.success import SuccessScreen
from ui.screens.manage import ManageScreen
from ui.screens.goodbye import GoodbyeScreen
from steps.packages import PackagesStep
from steps.haproxy import HAProxyStep
from steps.xui import XUIStep
from steps.pki import PKIStep
from steps.pam import PAMStep
from steps.openvpn import OpenVPNStep
from steps.kernel_fw import KernelFWStep
from steps.services import ServicesStep
from steps.client_profile import ClientProfileStep
from steps.user_db import UserDBStep
from management.user_mgr import UserManager
from validation.checklist import run_validation

app = typer.Typer(
    name="vpn-installer",
    help="OpenVPN-over-HAProxy Installer - Stealthy, multiplexed VPN on port 443",
    add_completion=False,
    no_args_is_help=True,
)
console = Console(theme=THEME)


def _version_callback(value: bool) -> None:
    """Print version and exit when --version is passed."""
    if value:
        try:
            from importlib.metadata import version as pkg_version
            v = pkg_version("vpn-installer")
        except Exception:
            v = "1.0.0"
        console.print(f"[bold]vpn-installer[/bold] [primary]{v}[/primary]")
        console.print("[dim]Made by jackh0006 • jackh109867@gmail.com • No tracking • No telemetry[/dim]")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
):
    """OpenVPN-over-HAProxy Installer - stealthy, multiplexed VPN on port 443."""


class Installer:
    """Main installer orchestration class."""

    def __init__(self):
        self.config: InstallConfig | None = None
        self.state: InstallState | None = None
        self.state_manager = StateManager()
        self.logger = setup_logger()
        self.steps = []
        self._init_steps()

    def _init_steps(self):
        """Initialize all installation steps in order."""
        self.steps = [
            ("packages", "Install System Packages", PackagesStep()),
            ("haproxy", "Configure HAProxy with SNI Routing", HAProxyStep()),
            ("xui", "Deploy 3X-UI with 2 Inbounds", XUIStep()),
            ("pki", "Bootstrap Easy-RSA PKI", PKIStep()),
            ("pam", "Create PAM User", PAMStep()),
            ("openvpn", "Write OpenVPN Server Config", OpenVPNStep()),
            ("kernel_fw", "Kernel Tuning & Firewall NAT", KernelFWStep()),
            ("services", "Enable & Start All Services", ServicesStep()),
            ("client_profile", "Generate Client .ovpn Profile", ClientProfileStep()),
            ("user_db", "Store User Record in Database", UserDBStep()),
        ]

    async def run_welcome(self) -> bool:
        """Show welcome screen. Returns True to continue, False to exit."""
        screen = WelcomeScreen(self.console)
        return await screen.run()

    async def run_privacy(self) -> bool:
        """Show privacy education screen. Returns True to continue, False to exit."""
        screen = PrivacyScreen(self.console)
        return await screen.run()

    async def run_parameters(self) -> bool:
        """Collect installation parameters. Returns True to continue, False to exit/back."""
        screen = ParameterScreen(self.console)
        result = await screen.run()
        if result:
            self.config = result
            self.state = InstallState(config=self.config)
            self.state_manager.save(self.state)
        return bool(result)

    async def run_confirmation(self) -> bool:
        """Show step-by-step confirmation. Returns True to proceed, False to exit/back."""
        screen = ConfirmScreen(self.console, self.steps, self.config)
        return await screen.run()

    async def run_installation(self, already_done: set = None) -> bool:
        """Run the installation with live progress. Returns True on success."""
        screen = ProgressScreen(self.console, self.steps, self.config, self.state, already_done=already_done or set())
        success = await screen.run()
        if success:
            self.state.completed = True
            self.state_manager.save(self.state)
        return success

    async def run_success(self):
        """Show success screen with client profile."""
        screen = SuccessScreen(self.console, self.config, self.state)
        await screen.run()

    async def run_management(self):
        """Run user management menu."""
        if not self.config:
            return
        user_mgr = UserManager(self.config)
        screen = ManageScreen(self.console, user_mgr, self.config)
        await screen.run()

    async def run_goodbye(self):
        """Show goodbye screen."""
        screen = GoodbyeScreen(self.console, self.config)
        await screen.run()

    async def run_validation(self):
        """Run post-install validation checklist."""
        if not self.config:
            return
        console.print("\n[bold cyan]🔍 Running Validation Checklist...[/bold cyan]\n")
        results = run_validation(self.config)
        for name, passed, details in results:
            status = "[green]✅ PASS[/green]" if passed else "[red]❌ FAIL[/red]"
            console.print(f"  {status} {name}")
            if details and not passed:
                console.print(f"    [dim]{details}[/dim]")
        passed_count = sum(1 for _, p, _ in results if p)
        console.print(f"\n[bold]{passed_count}/{len(results)} checks passed[/bold]")

    @property
    def console(self) -> Console:
        return console


@app.command()
def install(
    non_interactive: bool = typer.Option(False, "--non-interactive", "-n", help="Run without interactive prompts (for CI/CD)"),
    skip_validation: bool = typer.Option(False, "--skip-validation", help="Skip post-install validation"),
    resume: bool = typer.Option(False, "--resume", help="Resume from last saved state"),
):
    """Run the interactive installer."""
    installer = Installer()
    asyncio.run(installer._run_full_install(non_interactive, skip_validation, resume))


@app.command()
def manage():
    """Open user management menu for existing installation."""
    installer = Installer()
    # Load existing state
    state = installer.state_manager.load()
    if not state:
        console.print("[red]No existing installation found. Run 'install' first.[/red]")
        raise typer.Exit(1)
    installer.config = state.config
    installer.state = state
    asyncio.run(installer.run_management())
    asyncio.run(installer.run_goodbye())


@app.command()
def validate():
    """Run validation checklist on existing installation."""
    installer = Installer()
    state = installer.state_manager.load()
    if not state:
        console.print("[red]No existing installation found. Run 'install' first.[/red]")
        raise typer.Exit(1)
    installer.config = state.config
    asyncio.run(installer.run_validation())


@app.command()
def uninstall():
    """Uninstall all components (with confirmation)."""
    console.print(Panel(
        "[bold red]⚠️  This will REMOVE all VPN components:[/bold red]\n"
        "• HAProxy, OpenVPN, 3X-UI\n"
        "• All certificates, keys, user data\n"
        "• Firewall rules, kernel settings\n\n"
        "[yellow]This action CANNOT be undone.[/yellow]",
        title="Uninstall",
        border_style="red",
    ))
    if not typer.confirm("Are you absolutely sure?"):
        console.print("Cancelled.")
        raise typer.Exit(0)

    # TODO: Implement uninstall
    console.print("[yellow]Uninstall not yet implemented.[/yellow]")


@app.command()
def version():
    """Show version information."""
    console.print(Panel(
        "[bold]OpenVPN-over-HAProxy Installer[/bold]\n"
        "Version: 1.0.0\n"
        "Made by jackh0006 • jackh109867@gmail.com\n\n"
        "Open source • No tracking • No telemetry\n"
        "Dedicated to digital freedom and privacy",
        title="About",
        border_style="blue",
    ))


# Add the internal run method to Installer
async def _run_full_install(self, non_interactive: bool, skip_validation: bool, resume: bool):
    """Full installation flow."""
    # Resume from saved state if requested
    if resume:
        saved_state = self.state_manager.load()
        if saved_state:
            self.state = saved_state
            self.config = saved_state.config
            console.print("[green]✓ Resumed from saved state[/green]")

    # Step 0: Welcome
    if not self.state or not self.state.welcome_done:
        if not await self.run_welcome():
            await self.run_goodbye()
            return
        if self.state:
            self.state.welcome_done = True
            self.state_manager.save(self.state)

    # Step 1: Privacy Education
    if not self.state or not self.state.privacy_done:
        if not await self.run_privacy():
            await self.run_goodbye()
            return
        if self.state:
            self.state.privacy_done = True
            self.state_manager.save(self.state)

    # Step 2: Parameter Collection
    if not self.state or not self.state.params_done:
        if not await self.run_parameters():
            await self.run_goodbye()
            return

    # Step 3: Step-by-Step Confirmation
    already_done = set()
    if not self.state or not self.state.confirm_done:
        if not await self.run_confirmation():
            await self.run_goodbye()
            return
        # Get already-done steps from confirm screen
        # The confirm screen stores them in self.already_done, but we need to re-detect here
        # since the screen instance is local. Re-detect:
        for step_id, _, step_obj in self.steps:
            try:
                if await step_obj.is_already_done(self.config):
                    already_done.add(step_id)
            except Exception:
                pass
        if self.state:
            self.state.confirm_done = True
            self.state_manager.save(self.state)

    # Step 4: Installation
    if not self.state or not self.state.install_done:
        if not await self.run_installation(already_done=already_done):
            console.print("[red]Installation failed. Check logs for details.[/red]")
            await self.run_goodbye()
            return

    # Step 5: Validation
    if not skip_validation:
        await self.run_validation()

    # Step 6: Success
    await self.run_success()

    # Step 7: Offer Management
    if typer.confirm("\nOpen user management menu?"):
        await self.run_management()

    # Step 8: Goodbye
    await self.run_goodbye()


# Monkey-patch the method
Installer._run_full_install = _run_full_install


if __name__ == "__main__":
    app()