"""Privacy package for the VPN installer."""

from privacy.explanations import PRIVACY_EXPLANATIONS, get_entity_explanation
from privacy.display import render_privacy_report

__all__ = [
    "PRIVACY_EXPLANATIONS",
    "get_entity_explanation",
    "render_privacy_report",
]