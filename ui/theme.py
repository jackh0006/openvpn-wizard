"""
UI Theme - Color scheme, styles, and animations.
"""

from rich.style import Style
from rich.theme import Theme
from rich.console import Console


# Color palette
COLORS = {
    # Primary brand colors
    "primary": "#00d4aa",      # Teal - main brand
    "primary_dark": "#00a080",
    "primary_light": "#40e8c0",

    # Semantic colors
    "success": "#00d47e",      # Green
    "warning": "#ffb800",      # Amber
    "error": "#ff4757",        # Red
    "info": "#3742fa",         # Blue

    # Neutral
    "bg": "#0d1117",           # Dark background
    "surface": "#161b22",      # Card/surface
    "border": "#30363d",       # Borders
    "text": "#e6edf3",         # Primary text
    "text_muted": "#8b949e",   # Muted text
    "text_dim": "#6e7681",     # Dim text

    # Accents
    "accent_purple": "#a855f7",
    "accent_orange": "#fb923c",
    "accent_pink": "#f472b6",
    "accent_cyan": "#22d3ee",
}

# Rich theme
THEME = Theme({
    # Basic styles
    "primary": f"bold {COLORS['primary']}",
    "success": f"bold {COLORS['success']}",
    "warning": f"bold {COLORS['warning']}",
    "error": f"bold {COLORS['error']}",
    "info": f"bold {COLORS['info']}",
    "muted": COLORS['text_muted'],
    "dim": COLORS['text_dim'],

    # UI components
    "panel.border": COLORS['border'],
    "panel.title": f"bold {COLORS['primary']}",
    "button": f"bold {COLORS['bg']} on {COLORS['primary']}",
    "button.hover": f"bold {COLORS['bg']} on {COLORS['primary_light']}",
    "button.disabled": f"{COLORS['text_dim']} on {COLORS['border']}",
    "input.border": COLORS['border'],
    "input.focus": COLORS['primary'],
    "progress.bar": COLORS['primary'],
    "progress.complete": COLORS['success'],
    "table.header": f"bold {COLORS['primary']}",
    "table.cell": COLORS['text'],
    "checkbox.checked": f"bold {COLORS['success']}",
    "checkbox.unchecked": COLORS['text_muted'],

    # Custom styles
    "step.pending": COLORS['text_muted'],
    "step.running": COLORS['warning'],
    "step.done": COLORS['success'],
    "step.failed": COLORS['error'],
    "step.skipped": COLORS['text_dim'],
    "highlight": f"bold {COLORS['accent_cyan']}",
    "code": f"{COLORS['accent_orange']} on {COLORS['surface']}",
    "path": f"underline {COLORS['accent_cyan']}",
    "url": f"underline {COLORS['info']}",
    "key": f"bold {COLORS['accent_purple']} on {COLORS['surface']}",
    "title": f"bold {COLORS['primary']}",
    "subtitle": f"{COLORS['text_muted']}",
    "divider": COLORS['border'],
    "border": COLORS['border'],
})


def get_console() -> Console:
    """Get a themed console instance."""
    return Console(theme=THEME, force_terminal=True)


# ASCII Art / Logo
LOGO = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ██████╗ ██████╗ ███████╗████████╗    ███████╗██╗  ██╗███████╗██╗     ██╗   ║
║   ██╔══██╗██╔══██╗██╔════╝╚══██╔══╝    ██╔════╝██║  ██║██╔════╝██║     ██║   ║
║   ██████╔╝██████╔╝█████╗     ██║       ███████╗███████║█████╗  ██║     ██║   ║
║   ██╔══██╗██╔══██╗██╔══╝     ██║       ╚════██║██╔══██║██╔══╝  ██║     ██║   ║
║   ██████╔╝██║  ██║███████╗   ██║       ███████║██║  ██║███████╗███████╗██║   ║
║   ╚═════╝ ╚═╝  ╚═╝╚══════╝   ╚═╝       ╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝   ║
║                                                                              ║
║        ███████╗███████╗██████╗ ██╗   ██╗███████╗██████╗                     ║
║        ██╔════╝██╔════╝██╔══██╗██║   ██║██╔════╝██╔══██╗                    ║
║        ███████╗█████╗  ██████╔╝██║   ██║█████╗  ██████╔╝                    ║
║        ╚════██║██╔══╝  ██╔══██╗██║   ██║██╔══╝  ██╔══██╗                    ║
║        ███████║███████╗██║  ██║╚██████╔╝███████╗██║  ██║                    ║
║        ╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝                    ║
║                                                                              ║
║              over HAProxy (Port 443) • SNI Multiplexing                      ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

SMALL_LOGO = """
┌──────────────────────────────────────────────────────────────────────────────┐
│  ██████╗ ██████╗ ███████╗████████╗    ███████╗██╗  ██╗███████╗██╗     ██╗    │
│  ██╔══██╗██╔══██╗██╔════╝╚══██╔══╝    ██╔════╝██║  ██║██╔════╝██║     ██║    │
│  ██████╔╝██████╔╝█████╗     ██║       ███████╗███████║█████╗  ██║     ██║    │
│  ██╔══██╗██╔══██╗██╔══╝     ██║       ╚════██║██╔══██║██╔══╝  ██║     ██║    │
│  ██████╔╝██║  ██║███████╗   ██║       ███████║██║  ██║███████╗███████╗██║    │
│  ╚═════╝ ╚═╝  ╚═╝╚══════╝   ╚═╝       ╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝    │
│                                                                              │
│        OpenVPN over HAProxy • Port 443 • SNI Multiplexing                    │
│              Made by jackh0006 • jackh109867@gmail.com                       │
└──────────────────────────────────────────────────────────────────────────────┘
"""

# Animations
SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
PROGRESS_CHARS = "█▉▊▋▌▍▎▏░"


def gradient_text(text: str, start_color: str, end_color: str) -> str:
    """Create a gradient text effect (approximate with Rich markup)."""
    # Simple approximation - alternate colors
    return f"[{start_color}]{text}[/{start_color}]"


def style_path(path: str) -> str:
    """Style a file path."""
    return f"[path]{path}[/path]"


def style_key(key: str) -> str:
    """Style a keyboard key."""
    return f"[key] {key} [/key]"


def style_url(url: str) -> str:
    """Style a URL."""
    return f"[url]{url}[/url]"