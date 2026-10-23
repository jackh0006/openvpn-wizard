"""
Installation state management with rollback support.
"""

import json
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from core.config import InstallConfig


@dataclass
class StepState:
    """State of a single installation step."""
    name: str
    display_name: str
    completed: bool = False
    failed: bool = False
    skipped: bool = False
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    error: Optional[str] = None
    rollback_data: Dict[str, Any] = field(default_factory=dict)
    output: List[str] = field(default_factory=list)


@dataclass
class InstallState:
    """Complete installation state for resume/rollback."""
    # Configuration
    config: Optional[InstallConfig] = None

    # Progress flags
    welcome_done: bool = False
    privacy_done: bool = False
    params_done: bool = False
    confirm_done: bool = False
    install_done: bool = False
    completed: bool = False

    # Step states
    steps: Dict[str, StepState] = field(default_factory=dict)

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    version: str = "1.0.0"

    # Rollback
    backup_dir: str = "/var/backups/vpn-installer"
    rollback_points: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.config and not isinstance(self.config, InstallConfig):
            # Reconstruct from dict
            self.config = InstallConfig(**self.config)

    @property
    def current_step(self) -> Optional[str]:
        """Get the current step being executed."""
        for step_id, step in self.steps.items():
            if step.start_time and not step.end_time:
                return step_id
        return None

    @property
    def completed_steps(self) -> List[str]:
        """Get list of completed step IDs."""
        return [sid for sid, s in self.steps.items() if s.completed]

    @property
    def failed_steps(self) -> List[str]:
        """Get list of failed step IDs."""
        return [sid for sid, s in self.steps.items() if s.failed]

    def mark_step_start(self, step_id: str, rollback_data: Dict[str, Any] = None):
        """Mark a step as started."""
        if step_id not in self.steps:
            self.steps[step_id] = StepState(name=step_id, display_name=step_id)
        self.steps[step_id].start_time = time.time()
        self.steps[step_id].rollback_data = rollback_data or {}
        self.updated_at = datetime.now().isoformat()

    def mark_step_complete(self, step_id: str, output: List[str] = None):
        """Mark a step as completed."""
        if step_id in self.steps:
            self.steps[step_id].completed = True
            self.steps[step_id].end_time = time.time()
            if output:
                self.steps[step_id].output = output
        self.updated_at = datetime.now().isoformat()

    def mark_step_failed(self, step_id: str, error: str):
        """Mark a step as failed."""
        if step_id in self.steps:
            self.steps[step_id].failed = True
            self.steps[step_id].end_time = time.time()
            self.steps[step_id].error = error
        self.updated_at = datetime.now().isoformat()

    def mark_step_skipped(self, step_id: str):
        """Mark a step as skipped."""
        if step_id in self.steps:
            self.steps[step_id].skipped = True
            self.steps[step_id].end_time = time.time()
        self.updated_at = datetime.now().isoformat()

    def add_rollback_point(self, description: str):
        """Add a rollback point description."""
        self.rollback_points.append(f"{datetime.now().isoformat()}: {description}")
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Handle config specially
        if self.config:
            data['config'] = asdict(self.config)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InstallState':
        """Create from dictionary."""
        config_data = data.pop('config', None)
        state = cls(**data)
        if config_data:
            state.config = InstallConfig(**config_data)
        # Reconstruct step states
        steps = {}
        for sid, sdata in data.get('steps', {}).items():
            steps[sid] = StepState(**sdata)
        state.steps = steps
        return state


class StateManager:
    """Manages installation state persistence."""

    def __init__(self, state_file: str = "/var/lib/vpn-installer/state.json"):
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

    def save(self, state: InstallState):
        """Save state to disk."""
        state.updated_at = datetime.now().isoformat()
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state.to_dict(), f, indent=2)
        except Exception as e:
            # Don't fail installation if state save fails
            print(f"[yellow]Warning: Could not save state: {e}[/yellow]")

    def load(self) -> Optional[InstallState]:
        """Load state from disk."""
        if not self.state_file.exists():
            return None
        try:
            with open(self.state_file, 'r') as f:
                data = json.load(f)
            return InstallState.from_dict(data)
        except Exception as e:
            print(f"[yellow]Warning: Could not load state: {e}[/yellow]")
            return None

    def clear(self):
        """Clear saved state."""
        if self.state_file.exists():
            self.state_file.unlink()

    def backup(self, suffix: str = None) -> Path:
        """Create a backup of current state."""
        if not self.state_file.exists():
            return None
        suffix = suffix or datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.state_file.with_suffix(f".bak.{suffix}.json")
        backup_path.write_text(self.state_file.read_text())
        return backup_path