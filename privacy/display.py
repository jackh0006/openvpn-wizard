"""
Privacy Display - Render privacy reports beautifully.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.align import Align
from rich.text import Text

from privacy.explanations import get_all_explanations, EntityExplanation


def render_privacy_report(console: Console = None, expanded: dict = None) -> Panel:
    """Render complete privacy report as a panel."""
    if console is None:
        console = Console()

    if expanded is None:
        expanded = {}

    explanations = get_all_explanations()
    panels = []

    for entity_id, explanation in explanations.items():
        is_expanded = expanded.get(entity_id, False)
        panels.append(render_entity_panel(explanation, is_expanded))

    # Combine into columns or stack
    from rich.columns import Columns
    layout = Columns(panels, equal=True, expand=True)

    return Panel(
        layout,
        title="[primary]🔐 Privacy Report: What Each Entity Sees[/primary]",
        border_style="primary",
        padding=(1, 2),
    )


def render_entity_panel(explanation: EntityExplanation, expanded: bool = False) -> Panel:
    """Render a single entity explanation panel."""
    lines = []

    # Sees
    if explanation.sees:
        sees_table = Table(show_header=False, box=None, padding=(0, 1))
        sees_table.add_column("", style="success", width=3)
        sees_table.add_column("", style="text")
        for item in explanation.sees:
            sees_table.add_row("✅", item)
        lines.append("[bold success]✅ SEES:[/bold success]")
        lines.append(sees_table)

    # Doesn't see
    if explanation.doesnt_see:
        doesnt_table = Table(show_header=False, box=None, padding=(0, 1))
        doesnt_table.add_column("", style="error", width=3)
        doesnt_table.add_column("", style="text")
        for item in explanation.doesnt_see:
            doesnt_table.add_row("❌", item)
        lines.append("\n[bold error]❌ DOESN'T SEE:[/bold error]")
        lines.append(doesnt_table)

    # Expanded content
    if expanded:
        if explanation.technical_details:
            lines.append("\n[dim]🔧 Technical Details:[/dim]")
            for detail in explanation.technical_details:
                lines.append(f"  [dim]• {detail}[/dim]")

        if explanation.analogy:
            lines.append(f"\n[dim]💭 Analogy: {explanation.analogy}[/dim]")

    toggle = "▼ Show less" if expanded else "▶ Tell me more"
    lines.append(f"\n[dim]{toggle}[/dim]")

    border_style = "primary" if expanded else "border"

    return Panel(
        "\n".join(str(l) for l in lines),
        title=f"[primary]{explanation.icon} {explanation.name}[/primary]",
        border_style=border_style,
        padding=(1, 2),
    )


def render_summary_table(console: Console = None) -> Table:
    """Render a summary comparison table."""
    if console is None:
        console = Console()

    explanations = get_all_explanations()

    table = Table(show_header=True, header_style="primary", title="Privacy Summary")
    table.add_column("Entity", style="text", width=25)
    table.add_column("Sees", style="success", width=35)
    table.add_column("Doesn't See", style="error", width=35)

    for entity_id, exp in explanations.items():
        sees_summary = "; ".join(exp.sees[:2]) + ("..." if len(exp.sees) > 2 else "")
        doesnt_summary = "; ".join(exp.doesnt_see[:2]) + ("..." if len(exp.doesnt_see) > 2 else "")
        table.add_row(f"{exp.icon} {exp.name}", sees_summary, doesnt_summary)

    return table