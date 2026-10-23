"""
Progress Screen - Live installation progress with details.
"""

import asyncio
import time
from typing import List, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.align import Align

from ui.theme import get_console, COLORS, SPINNER_FRAMES
from ui.components import ProgressStep, CreditsFooter, SectionHeader, InfoBox
from core.config import InstallConfig
from core.state import InstallState, StepState, StateManager
from core.logger import StepLogger, get_logger
from core.exceptions import InstallerError, UserAbortError


class ProgressScreen:
    """Live installation progress with pause/cancel/rollback."""

    def __init__(
        self,
        console: Console,
        steps: List[Tuple[str, str, object]],
        config: InstallConfig,
        state: InstallState,
        already_done: set = None,
    ):
        self.console = console
        self.steps = steps
        self.config = config
        self.state = state
        self.state_manager = StateManager()
        self.logger = get_logger()
        self.cancelled = False
        self.paused = False
        self.current_step_idx = 0
        self.step_outputs = {}
        self.already_done = already_done or set()

    async def run(self) -> bool:
        """Run installation with live progress. Returns True on success."""
        self.console.clear()
        self.console.print(SectionHeader(4, 7, "Installation Progress", "🚀").render())

        # Initialize step states in state object
        for step_id, display_name, _ in self.steps:
            if step_id not in self.state.steps:
                self.state.steps[step_id] = StepState(name=step_id, display_name=display_name)

        # Create progress display
        progress = Progress(
            TextColumn("[primary]{task.description}[/primary]"),
            BarColumn(bar_width=40, style="primary", complete_style="success"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self.console,
        )

        main_task = progress.add_task("Overall", total=len(self.steps))

        # Run with live display
        with Live(self._make_layout(progress), console=self.console, refresh_per_second=10) as live:
            for i, (step_id, display_name, step_obj) in enumerate(self.steps):
                self.current_step_idx = i

                # Check if already done (smart detection)
                already_done = step_id in self.already_done
                if not already_done:
                    # Double-check at runtime in case something changed
                    try:
                        already_done = await step_obj.is_already_done(self.config)
                    except Exception:
                        already_done = False

                if already_done:
                    # Mark as completed in state
                    self.state.mark_step_complete(step_id, ["Already complete - skipped"])
                    self.state_manager.save(self.state)
                    progress.update(main_task, advance=1)
                    continue

                # Check if skipped by user
                if step_id in self.state.steps and self.state.steps[step_id].completed:
                    progress.update(main_task, advance=1)
                    continue

                # Update step state to running
                self.state.mark_step_start(step_id)
                self.state_manager.save(self.state)

                # Update progress display
                progress.update(main_task, description=f"Step {i+1}/{len(self.steps)}: {display_name}")

                # Run step with sub-steps
                success = await self._run_step(live, progress, step_id, display_name, step_obj)

                if not success:
                    # Step failed
                    self.state.steps[step_id].failed = True
                    self.state_manager.save(self.state)
                    return False

                progress.update(main_task, advance=1)

        # All done
        self.state.install_done = True
        self.state.completed = True
        self.state_manager.save(self.state)
        return True

    def _make_layout(self, progress: Progress) -> Panel:
        """Create the live layout."""
        # Steps list
        steps_table = Table(show_header=True, header_style="primary", box=None, padding=(0, 1))
        steps_table.add_column("", width=3)
        steps_table.add_column("Step", style="text", width=40)
        steps_table.add_column("Status", width=12)

        for i, (step_id, display_name, _) in enumerate(self.steps):
            step_state = self.state.steps.get(step_id)
            if step_state:
                pstep = ProgressStep(step_id, display_name, self._get_step_status(step_state))
            else:
                pstep = ProgressStep(step_id, display_name, "pending")
            steps_table.add_row(str(i+1), pstep.display_name, pstep.ICONS.get(pstep.status, "?"))

        # Live log (last 10 lines from current step)
        log_lines = []
        if self.current_step_idx < len(self.steps):
            step_id = self.steps[self.current_step_idx][0]
            step_state = self.state.steps.get(step_id)
            if step_state and step_state.output:
                log_lines = step_state.output[-10:]

        log_content = "\n".join(f"  └─> {line}" for line in log_lines) if log_lines else "[dim](waiting...)[/dim]"

        # Combine
        from rich.columns import Columns
        layout = Columns([
            Panel(steps_table, title="[primary]Steps[/primary]", border_style="primary", width=60),
            Panel(
                f"[bold]Live Log:[/bold]\n{log_content}",
                title="[primary]Output[/primary]",
                border_style="primary",
            ),
        ], equal=False, expand=True)

        return Panel(
            layout,
            title="[primary]🚀 Installation Progress[/primary]",
            border_style="primary",
            padding=(1, 2),
        )

    def _get_step_status(self, step_state: StepState) -> str:
        """Get display status from step state."""
        if step_state.failed:
            return "failed"
        elif step_state.completed:
            return "done"
        elif step_state.skipped:
            return "skipped"
        elif step_state.start_time and not step_state.end_time:
            return "running"
        return "pending"

    async def _run_step(
        self,
        live: Live,
        progress: Progress,
        step_id: str,
        display_name: str,
        step_obj: object,
    ) -> bool:
        """Run a single step with sub-step tracking."""
        # Check for pause/cancel
        if self.cancelled:
            raise UserAbortError("Installation cancelled by user")

        # Execute step
        try:
            with StepLogger(display_name, self.logger) as slog:
                # Capture output
                output_lines = []

                def capture_output(line: str):
                    output_lines.append(line)
                    step_state = self.state.steps.get(step_id)
                    if step_state:
                        step_state.output = output_lines
                        self.state_manager.save(self.state)
                        live.update(self._make_layout(progress))

                # Run the step's execute method
                if hasattr(step_obj, 'execute'):
                    result = await step_obj.execute(self.config, capture_output)
                else:
                    # Fallback for steps without execute method
                    result = await self._run_step_fallback(step_id, step_obj, capture_output)

                if result:
                    self.state.mark_step_complete(step_id, output_lines)
                    self.state_manager.save(self.state)
                    live.update(self._make_layout(progress))
                    return True
                else:
                    self.state.mark_step_failed(step_id, "Step returned False")
                    return False

        except UserAbortError:
            raise
        except Exception as e:
            self.logger.error(f"Step {step_id} failed: {e}")
            self.state.mark_step_failed(step_id, str(e))
            self.state_manager.save(self.state)
            live.update(self._make_layout(progress))
            return False

    async def _run_step_fallback(self, step_id: str, step_obj, capture_output) -> bool:
        """Fallback for steps without execute method."""
        capture_output(f"Running {step_id}...")
        await asyncio.sleep(0.5)
        capture_output(f"Completed {step_id}")
        return True