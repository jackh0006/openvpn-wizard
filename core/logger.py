"""
Structured logging for the installer.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from rich.logging import RichHandler
from rich.console import Console
from rich.text import Text


def setup_logger(
    name: str = "vpn-installer",
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """Set up and return a configured logger."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()

    # Console handler with Rich
    console = Console(stderr=True)
    console_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=False,
        markup=True,
        rich_tracebacks=True,
        tracebacks_show_locals=False,
    )
    console_handler.setLevel(level)
    console_format = logging.Formatter(
        "%(message)s",
        datefmt="[%X]"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler if requested
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "vpn-installer") -> logging.Logger:
    """Get the logger instance."""
    return logging.getLogger(name)


class StepLogger:
    """Context manager for logging step execution."""

    def __init__(self, step_name: str, logger: Optional[logging.Logger] = None):
        self.step_name = step_name
        self.logger = logger or get_logger()
        self.start_time = None

    def __enter__(self):
        self.start_time = __import__('time').time()
        self.logger.info(f"[bold cyan]▶ Starting:[/bold cyan] {self.step_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = __import__('time').time() - self.start_time
        if exc_type:
            self.logger.error(f"[bold red]✗ Failed:[/bold red] {self.step_name} ({elapsed:.1f}s) - {exc_val}")
        else:
            self.logger.info(f"[bold green]✓ Completed:[/bold green] {self.step_name} ({elapsed:.1f}s)")
        return False  # Don't suppress exceptions

    def info(self, msg: str):
        self.logger.info(f"  {msg}")

    def warning(self, msg: str):
        self.logger.warning(f"  [yellow]⚠[/yellow] {msg}")

    def error(self, msg: str):
        self.logger.error(f"  [red]✗[/red] {msg}")

    def debug(self, msg: str):
        self.logger.debug(f"  {msg}")


def log_command(cmd: list, logger: Optional[logging.Logger] = None):
    """Log a command being executed."""
    log = logger or get_logger()
    log.debug(f"$ {' '.join(str(c) for c in cmd)}")


def log_output(output: str, logger: Optional[logging.Logger] = None, level: int = logging.DEBUG):
    """Log command output."""
    log = logger or get_logger()
    for line in output.strip().split('\n'):
        if line.strip():
            log.log(level, f"  └─> {line}")