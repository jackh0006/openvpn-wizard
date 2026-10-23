"""
Custom exception hierarchy for the installer.
"""


class InstallerError(Exception):
    """Base exception for all installer errors."""
    def __init__(self, message: str, code: str = "INSTALLER_ERROR", fix_hint: str = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.fix_hint = fix_hint


class UserInputError(InstallerError):
    """Error in user input."""
    def __init__(self, message: str, field: str = None, fix_hint: str = None):
        super().__init__(message, "USER_INPUT_ERROR", fix_hint)
        self.field = field


class ValidationError(InstallerError):
    """Configuration validation error."""
    def __init__(self, message: str, field: str = None, fix_hint: str = None):
        super().__init__(message, "VALIDATION_ERROR", fix_hint)
        self.field = field


class SystemError(InstallerError):
    """System-level error (missing packages, permissions, etc.)."""
    def __init__(self, message: str, command: str = None, fix_hint: str = None):
        super().__init__(message, "SYSTEM_ERROR", fix_hint)
        self.command = command


class NetworkError(InstallerError):
    """Network-related error (download, connectivity)."""
    def __init__(self, message: str, url: str = None, fix_hint: str = None):
        super().__init__(message, "NETWORK_ERROR", fix_hint)
        self.url = url


class ConfigError(InstallerError):
    """Configuration file error (syntax, conflicts)."""
    def __init__(self, message: str, file: str = None, fix_hint: str = None):
        super().__init__(message, "CONFIG_ERROR", fix_hint)
        self.file = file


class ServiceError(InstallerError):
    """Service management error (won't start, crashed)."""
    def __init__(self, message: str, service: str = None, fix_hint: str = None):
        super().__init__(message, "SERVICE_ERROR", fix_hint)
        self.service = service


class CryptoError(InstallerError):
    """Cryptography error (key generation, cert issues)."""
    def __init__(self, message: str, operation: str = None, fix_hint: str = None):
        super().__init__(message, "CRYPTO_ERROR", fix_hint)
        self.operation = operation


class RollbackError(InstallerError):
    """Error during rollback."""
    def __init__(self, message: str, step: str = None, fix_hint: str = None):
        super().__init__(message, "ROLLBACK_ERROR", fix_hint)
        self.step = step


class StateError(InstallerError):
    """State management error."""
    def __init__(self, message: str, fix_hint: str = None):
        super().__init__(message, "STATE_ERROR", fix_hint)


class UserAbortError(InstallerError):
    """User intentionally aborted the installation."""
    def __init__(self, message: str = "Installation aborted by user"):
        super().__init__(message, "USER_ABORT", "Run the installer again to continue")


# Error code to user-friendly title mapping
ERROR_TITLES = {
    "USER_INPUT_ERROR": "Input Error",
    "VALIDATION_ERROR": "Validation Failed",
    "SYSTEM_ERROR": "System Error",
    "NETWORK_ERROR": "Network Error",
    "CONFIG_ERROR": "Configuration Error",
    "SERVICE_ERROR": "Service Error",
    "CRYPTO_ERROR": "Cryptography Error",
    "ROLLBACK_ERROR": "Rollback Failed",
    "STATE_ERROR": "State Error",
    "USER_ABORT": "Aborted",
    "INSTALLER_ERROR": "Installation Error",
}


def format_error(error: InstallerError) -> str:
    """Format an installer error for display."""
    title = ERROR_TITLES.get(error.code, "Error")
    lines = [
        f"❌ [{error.code}] {title}",
        "─" * 50,
        f"What happened: {error.message}",
    ]
    if error.fix_hint:
        lines.append(f"How to fix: {error.fix_hint}")
    return "\n".join(lines)