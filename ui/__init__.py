"""UI package for the VPN installer."""

from ui.theme import get_console, COLORS, LOGO, SMALL_LOGO
from ui.screens.welcome import WelcomeScreen
from ui.screens.privacy import PrivacyScreen
from ui.screens.parameters import ParameterScreen
from ui.screens.confirm import ConfirmScreen
from ui.screens.progress import ProgressScreen
from ui.screens.success import SuccessScreen
from ui.screens.manage import ManageScreen
from ui.screens.goodbye import GoodbyeScreen
from ui.components import (
    ExplainedPanel, ConfirmAction, ProgressStep, InfoBox,
    CreditsFooter, SectionHeader,
)

__all__ = [
    "get_console",
    "COLORS",
    "LOGO",
    "SMALL_LOGO",
    "WelcomeScreen",
    "PrivacyScreen",
    "ParameterScreen",
    "ConfirmScreen",
    "ProgressScreen",
    "SuccessScreen",
    "ManageScreen",
    "GoodbyeScreen",
    "ExplainedPanel",
    "ConfirmAction",
    "ProgressStep",
    "InfoBox",
    "CreditsFooter",
    "SectionHeader",
]