"""Core module for the VPN installer."""

from core.config import InstallConfig, validate_fqdn, validate_ip, validate_username, validate_password, validate_client_name
from core.state import InstallState, StepState, StateManager
from core.logger import setup_logger, get_logger, StepLogger, log_command, log_output
from core.exceptions import (
    InstallerError, UserInputError, ValidationError, SystemError,
    NetworkError, ConfigError, ServiceError, CryptoError,
    RollbackError, StateError, UserAbortError, format_error,
    ERROR_TITLES,
)

__all__ = [
    "InstallConfig",
    "validate_fqdn",
    "validate_ip",
    "validate_username",
    "validate_password",
    "validate_client_name",
    "InstallState",
    "StepState",
    "StateManager",
    "setup_logger",
    "get_logger",
    "StepLogger",
    "log_command",
    "log_output",
    "InstallerError",
    "UserInputError",
    "ValidationError",
    "SystemError",
    "NetworkError",
    "ConfigError",
    "ServiceError",
    "CryptoError",
    "RollbackError",
    "StateError",
    "UserAbortError",
    "format_error",
    "ERROR_TITLES",
]