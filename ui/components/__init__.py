"""
UI Components - Reusable components with "Explain Like I'm 5" style.
"""

from typing import Optional, Callable, List, Dict, Any
from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.columns import Columns
from rich.align import Align
from rich.padding import Padding
from rich.rule import Rule
from rich.markdown import Markdown

from ui.theme import get_console, COLORS


console = get_console()


class ExplainedPanel:
    """A panel that explains a concept like teaching a 5-year-old."""

    def __init__(
        self,
        title: str,
        simple_explanation: str,
        technical_details: str = None,
        analogy: str = None,
        what_you_see: List[str] = None,
        what_you_dont_see: List[str] = None,
        icon: str = "💡",
    ):
        self.title = title
        self.simple = simple_explanation
        self.technical = technical_details
        self.analogy = analogy
        self.sees = what_you_see or []
        self.doesnt_see = what_you_dont_see or []
        self.icon = icon

    def render(self) -> Panel:
        """Render the explained panel."""
        items = []

        # Simple explanation (always shown)
        items.append(Text.from_markup(f"[bold]{self.icon} {self.simple}[/bold]"))

        # Analogy (if provided)
        if self.analogy:
            items.append(Text())
            items.append(Text.from_markup(f"[dim]💭 Think of it like: {self.analogy}[/dim]"))

        # What you see / don't see (if provided)
        if self.sees or self.doesnt_see:
            table = Table(show_header=True, header_style="primary", box=None, padding=(0, 1))
            table.add_column("✅ Sees / Knows", style="success", width=40)
            table.add_column("❌ Doesn't See / Know", style="error", width=40)

            max_rows = max(len(self.sees), len(self.doesnt_see))
            for i in range(max_rows):
                see = self.sees[i] if i < len(self.sees) else ""
                dont = self.doesnt_see[i] if i < len(self.doesnt_see) else ""
                table.add_row(see, dont)

            items.append(table)
            items.append(Text())

        # Technical details (collapsed by default, but we'll show inline)
        if self.technical:
            items.append(Text.from_markup(f"[muted]🔧 Technical: {self.technical}[/muted]"))

        return Panel(
            Group(*items),
            title=f"[primary]{self.title}[/primary]",
            border_style="primary",
            padding=(1, 2),
        )


class ConfirmAction:
    """Standardized confirmation dialog with explanation."""

    def __init__(
        self,
        console: Console,
        title: str,
        what: str,
        why: str,
        files_affected: List[str] = None,
        rollback_info: str = None,
        estimated_time: str = None,
        warning: str = None,
        show_skip: bool = False,
        show_back: bool = True,
    ):
        self.console = console
        self.title = title
        self.what = what
        self.why = why
        self.files = files_affected or []
        self.rollback = rollback_info
        self.time = estimated_time
        self.warning = warning
        self.show_skip = show_skip
        self.show_back = show_back

    def render(self) -> Panel:
        """Render the confirmation panel."""
        lines = []

        lines.append(f"[bold]📝 WHAT:[/bold] {self.what}")
        lines.append(f"[bold]🎯 WHY:[/bold] {self.why}")

        if self.files:
            lines.append(f"[bold]📁 FILES:[/bold]")
            for f in self.files:
                lines.append(f"  • [path]{f}[/path]")

        if self.rollback:
            lines.append(f"[bold]🔄 ROLLBACK:[/bold] {self.rollback}")

        if self.time:
            lines.append(f"[bold]⏱️  TIME:[/bold] {self.time}")

        if self.warning:
            lines.append(f"\n[warning]⚠️  {self.warning}[/warning]")

        return Panel(
            "\n".join(lines),
            title=f"[primary]{self.title}[/primary]",
            border_style="primary",
            padding=(1, 2),
        )

    def ask(self) -> str:
        """Show dialog and get user choice."""
        self.console.print(self.render())

        choices = []
        if self.show_back:
            choices.append(("back", "← Back", "Go back to previous step"))
        if self.show_skip:
            choices.append(("skip", "⏭ Skip", "Skip this step (advanced)"))
        choices.append(("confirm", "✓ Confirm & Execute", "Proceed with this step"))
        choices.append(("exit", "🚪 Exit", "Exit installer (state saved)"))

        # Display choices
        self.console.print()
        for i, (key, label, desc) in enumerate(choices):
            style = "primary" if key == "confirm" else "muted"
            self.console.print(f"  [{style}]{i+1}.[/{style}] {label} [dim]- {desc}[/dim]")

        while True:
            try:
                choice = self.console.input("\n[primary]Your choice [1-{}]: [/primary]".format(len(choices))).strip()
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(choices):
                        return choices[idx][0]
                # Also accept first letter
                for key, label, _ in choices:
                    if choice.lower() == key[0].lower():
                        return key
                self.console.print("[error]Invalid choice. Try again.[/error]")
            except (KeyboardInterrupt, EOFError):
                return "exit"


class ProgressStep:
    """Individual step display for progress screen."""

    def __init__(
        self,
        step_id: str,
        display_name: str,
        status: str = "pending",  # pending, running, done, failed, skipped
        sub_steps: List[str] = None,
        current_sub: int = 0,
        error: str = None,
    ):
        self.step_id = step_id
        self.display_name = display_name
        self.status = status
        self.sub_steps = sub_steps or []
        self.current_sub = current_sub
        self.error = error

    ICONS = {
        "pending": "[step.pending]○[/step.pending]",
        "running": "[step.running]◐[/step.running]",
        "done": "[step.done]✓[/step.done]",
        "failed": "[step.failed]✗[/step.failed]",
        "skipped": "[step.skipped]⊘[/step.skipped]",
    }

    def render(self) -> Text:
        """Render as a Text object."""
        icon = self.ICONS.get(self.status, "?")
        name = self.display_name

        if self.status == "running" and self.sub_steps:
            sub = self.sub_steps[self.current_sub] if self.current_sub < len(self.sub_steps) else ""
            return Text.from_markup(f"{icon} {name} [dim]→ {sub}[/dim]")
        elif self.status == "failed":
            return Text.from_markup(f"{icon} {name} [error]({self.error})[/error]")
        else:
            return Text.from_markup(f"{icon} {name}")


class InfoBox:
    """Informational box with icon and styled content."""

    ICONS = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
        "tip": "💡",
        "security": "🔒",
        "privacy": "🔐",
        "network": "🌐",
        "file": "📁",
        "time": "⏱️",
        "user": "👤",
        "key": "🔑",
        "server": "🖥️",
        "shield": "🛡️",
    }

    def __init__(self, type_: str, title: str, content: str, details: List[str] = None):
        self.type = type_
        self.title = title
        self.content = content
        self.details = details or []

    def render(self) -> Panel:
        icon = self.ICONS.get(self.type, "ℹ️")
        border_color = {
            "info": "info",
            "success": "success",
            "warning": "warning",
            "error": "error",
            "tip": "primary",
            "security": "success",
            "privacy": "primary",
        }.get(self.type, "primary")

        lines = [f"[bold]{self.content}[/bold]"]
        if self.details:
            lines.append("")
            for d in self.details:
                if d:
                    lines.append(f"  • {d}")

        return Panel(
            "\n".join(lines),
            title=f"[bold {border_color}]{icon} {self.title}[/bold {border_color}]",
            border_style=border_color,
            padding=(1, 2),
        )


class CreditsFooter:
    """Standard credits footer for all screens."""

    @staticmethod
    def render() -> Panel:
        return Panel(
            Align.center(
                "[primary]Made by jackh0006[/primary] • [url]jackh109867@gmail.com[/url]\n"
                "[dim]Open source • No tracking • No telemetry • For digital freedom[/dim]"
            ),
            border_style="divider",
            padding=(0, 1),
        )


class SectionHeader:
    """Section header with icon and progress indicator."""

    def __init__(self, number: int, total: int, title: str, icon: str = "📋"):
        self.number = number
        self.total = total
        self.title = title
        self.icon = icon

    def render(self) -> Panel:
        progress = f"[primary]{self.number}/{self.total}[/primary]"
        bar_width = 20
        filled = int(bar_width * self.number / self.total)
        bar = "█" * filled + "░" * (bar_width - filled)

        return Panel(
            Align.center(f"[bold]{self.icon} {self.title}[/bold]\n[dim]{bar}[/dim] {progress}"),
            border_style="primary",
            padding=(0, 2),
        )