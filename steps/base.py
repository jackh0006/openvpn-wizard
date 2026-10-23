"""
Base Step Class - Abstract base for all installation steps with rollback support.
"""

import asyncio
import shutil
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass

from core.config import InstallConfig
from core.logger import StepLogger, get_logger, log_command, log_output
from core.exceptions import SystemError, ConfigError, ServiceError


@dataclass
class StepResult:
    """Result of step execution."""
    success: bool
    output: List[str] = None
    error: str = None
    rollback_data: Dict[str, Any] = None


class BaseStep(ABC):
    """Abstract base class for installation steps."""

    def __init__(self):
        self.logger = get_logger()
        self.backup_suffix = ".vpn-installer-backup"

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique step identifier."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable step name."""
        pass

    @property
    def description(self) -> str:
        """Brief description of what this step does."""
        return ""

    @abstractmethod
    async def execute(
        self,
        config: InstallConfig,
        output_callback: Callable[[str], None] = None,
    ) -> bool:
        """Execute the step. Returns True on success."""
        pass

    async def rollback(self, config: InstallConfig, rollback_data: Dict[str, Any]) -> bool:
        """Rollback the step. Returns True on success."""
        self.logger.warning(f"Rollback not implemented for {self.name}")
        return False

    # Helper methods for subclasses

    def _backup_file(self, path: str) -> Optional[str]:
        """Create a backup of a file. Returns backup path or None."""
        src = Path(path)
        if not src.exists():
            return None
        backup_path = f"{path}{self.backup_suffix}"
        try:
            shutil.copy2(src, backup_path)
            self.logger.debug(f"Backed up {path} to {backup_path}")
            return backup_path
        except Exception as e:
            self.logger.error(f"Failed to backup {path}: {e}")
            return None

    def _restore_backup(self, path: str) -> bool:
        """Restore a file from backup."""
        backup_path = f"{path}{self.backup_suffix}"
        src = Path(backup_path)
        if not src.exists():
            self.logger.warning(f"No backup found for {path}")
            return False
        try:
            shutil.copy2(src, path)
            self.logger.info(f"Restored {path} from backup")
            return True
        except Exception as e:
            self.logger.error(f"Failed to restore {path}: {e}")
            return False

    def _remove_backup(self, path: str):
        """Remove backup file after successful completion."""
        backup_path = f"{path}{self.backup_suffix}"
        try:
            Path(backup_path).unlink(missing_ok=True)
        except Exception:
            pass

    def _run_cmd(
        self,
        cmd: List[str],
        capture: bool = True,
        check: bool = True,
        cwd: str = None,
        env: Dict[str, str] = None,
        timeout: int = 300,
    ) -> subprocess.CompletedProcess:
        """Run a command with logging."""
        log_command(cmd, self.logger)
        try:
            result = subprocess.run(
                cmd,
                capture_output=capture,
                text=True,
                check=check,
                cwd=cwd,
                env=env,
                timeout=timeout,
            )
            if capture and result.stdout:
                log_output(result.stdout, self.logger)
            if capture and result.stderr:
                log_output(result.stderr, self.logger, level=20 if result.returncode == 0 else 40)
            return result
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed: {' '.join(cmd)}")
            if e.stdout:
                log_output(e.stdout, self.logger)
            if e.stderr:
                log_output(e.stderr, self.logger, level=40)
            raise SystemError(
                f"Command failed: {' '.join(cmd)}",
                command=' '.join(cmd),
                fix_hint="Check logs above for details"
            ) from e
        except subprocess.TimeoutExpired as e:
            raise SystemError(
                f"Command timed out: {' '.join(cmd)}",
                command=' '.join(cmd),
                fix_hint="Increase timeout or check for hanging process"
            ) from e

    def _run_cmd_async(
        self,
        cmd: List[str],
        output_callback: Callable[[str], None] = None,
    ) -> asyncio.subprocess.Process:
        """Run a command asynchronously with streaming output."""
        log_command(cmd, self.logger)
        return asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

    async def _stream_output(
        self,
        process: asyncio.subprocess.Process,
        output_callback: Callable[[str], None] = None,
    ) -> tuple[str, str]:
        """Stream process output line by line."""
        stdout_lines = []
        stderr_lines = []

        async def read_stream(stream, prefix, lines_list):
            while True:
                line = await stream.readline()
                if not line:
                    break
                decoded = line.decode().rstrip()
                lines_list.append(decoded)
                if output_callback:
                    output_callback(f"{prefix}{decoded}")

        await asyncio.gather(
            read_stream(process.stdout, "", stdout_lines),
            read_stream(process.stderr, "ERR: ", stderr_lines),
        )

        await process.wait()
        return "\n".join(stdout_lines), "\n".join(stderr_lines)

    def _write_file(self, path: str, content: str, mode: int = 0o644, backup: bool = True) -> str:
        """Write content to file, optionally creating backup."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)

        backup_path = None
        if backup and p.exists():
            backup_path = self._backup_file(path)

        try:
            p.write_text(content)
            p.chmod(mode)
            self.logger.debug(f"Wrote {len(content)} bytes to {path}")
            return backup_path
        except Exception as e:
            if backup_path:
                self._restore_backup(path)
            raise ConfigError(
                f"Failed to write {path}: {e}",
                file=path,
                fix_hint="Check permissions and disk space"
            ) from e

    def _read_file(self, path: str) -> str:
        """Read file content."""
        try:
            return Path(path).read_text()
        except Exception as e:
            raise ConfigError(
                f"Failed to read {path}: {e}",
                file=path,
                fix_hint="Check file exists and is readable"
            ) from e

    def _ensure_dir(self, path: str, mode: int = 0o755):
        """Ensure directory exists."""
        Path(path).mkdir(parents=True, exist_ok=True, mode=mode)

    def _template_render(self, template_path: str, context: Dict[str, Any]) -> str:
        """Render a Jinja2 template."""
        try:
            from jinja2 import Environment, FileSystemLoader
            env = Environment(loader=FileSystemLoader(Path(template_path).parent))
            template = env.get_template(Path(template_path).name)
            return template.render(**context)
        except Exception as e:
            raise ConfigError(
                f"Failed to render template {template_path}: {e}",
                fix_hint="Check template syntax and context variables"
            ) from e

    def _systemctl(self, action: str, service: str, output_callback: Callable[[str], None] = None) -> bool:
        """Run systemctl command."""
        try:
            cmd = ["systemctl", action, service]
            result = self._run_cmd(cmd, capture=True, check=False)
            if output_callback:
                if result.stdout:
                    output_callback(result.stdout)
                if result.stderr:
                    output_callback(result.stderr)
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"systemctl {action} {service} failed: {e}")
            return False

    def _systemctl_enable_now(self, service: str) -> bool:
        """Enable and start a service."""
        return self._systemctl("enable", service) and self._systemctl("start", service)

    def _systemctl_disable_now(self, service: str) -> bool:
        """Stop and disable a service."""
        return self._systemctl("stop", service) and self._systemctl("disable", service)

    def _is_service_active(self, service: str) -> bool:
        """Check if service is active."""
        result = self._run_cmd(["systemctl", "is-active", service], check=False)
        return result.returncode == 0 and result.stdout.strip() == "active"