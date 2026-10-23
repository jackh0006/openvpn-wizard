#!/usr/bin/env bash
# Quick install script for OpenVPN-Wizard
# Made by jackh0006 • jackh109867@gmail.com

set -euo pipefail

echo "🚀 OpenVPN-Wizard - Quick Install"
echo "=================================="
echo ""

# Check root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root (use sudo)"
   exit 1
fi

# Check Ubuntu
if ! grep -q "Ubuntu" /etc/os-release; then
   echo "⚠️  This installer is designed for Ubuntu. Continue anyway? (y/N)"
   read -r response
   if [[ ! "$response" =~ ^[Yy]$ ]]; then
       exit 1
   fi
fi

# Helper: check if a command exists
cmd_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Helper: check if a deb package is installed
pkg_installed() {
    dpkg -s "$1" >/dev/null 2>&1
}

# Helper: ask before continuing if something exists
ask_continue() {
    local item="$1"
    echo ""
    echo "⚠️  $item is already installed."
    read -r -p "   Continue anyway? (y/N): " response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "   Skipping $item."
        return 1
    fi
    return 0
}

# ── Step 1: Python 3 ──────────────────────────────────────────────
echo "📦 Checking Python 3..."
if cmd_exists python3; then
    PYTHON_VER=$(python3 --version 2>&1)
    echo "   ✓ Python 3 found: $PYTHON_VER"
    # Check Python version (need >= 3.10)
    PYTHON_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)" 2>/dev/null || echo "0")
    PYTHON_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)" 2>/dev/null || echo "0")
    if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]; }; then
        echo ""
        echo "❌ ERROR: Python 3.10+ is required, but found $PYTHON_VER"
        echo "   Please upgrade Python or use a newer Ubuntu version (22.04+ has 3.10)"
        exit 1
    fi
    if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]; then
        echo ""
        echo "⚠️  NOTE: Python $PYTHON_MAJOR.$PYTHON_MINOR detected (minimum 3.10 required)"
        echo "   Some features may be limited. Continuing anyway..."
        echo ""
    fi
    if ! ask_continue "Python 3"; then
        SKIP_PYTHON=1
    fi
else
    echo "   Installing Python 3..."
    apt-get update -qq
    apt-get install -y -qq python3
fi

# ── Step 2: pip ───────────────────────────────────────────────────
echo ""
echo "📦 Checking pip..."
if cmd_exists pip3 || cmd_exists pip; then
    PIP_VER=$(pip3 --version 2>&1 || pip --version 2>&1)
    echo "   ✓ pip found: $PIP_VER"
    if ! ask_continue "pip"; then
        SKIP_PIP=1
    fi
else
    echo "   Installing pip..."
    apt-get install -y -qq python3-pip
fi

# ── Step 3: python3-venv ──────────────────────────────────────────
echo ""
echo "📦 Checking python3-venv..."
if pkg_installed python3-venv; then
    echo "   ✓ python3-venv found"
    if ! ask_continue "python3-venv"; then
        SKIP_VENV_PKG=1
    fi
else
    echo "   Installing python3-venv..."
    apt-get install -y -qq python3-venv
fi

# ── Step 4: git ───────────────────────────────────────────────────
echo ""
echo "📦 Checking git..."
if cmd_exists git; then
    echo "   ✓ git found"
    if ! ask_continue "git"; then
        SKIP_GIT=1
    fi
else
    echo "   Installing git..."
    apt-get install -y -qq git
fi

# ── Step 5: Virtual Environment ───────────────────────────────────
VENV_DIR="/opt/vpn-installer"
echo ""
echo "🐍 Checking virtual environment at $VENV_DIR..."
if [[ -d "$VENV_DIR" ]]; then
    echo "   ✓ Virtual environment found"
    if ! ask_continue "virtual environment"; then
        SKIP_VENV=1
    fi
fi

if [[ "${SKIP_VENV:-0}" -ne 1 ]]; then
    echo "   Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install --upgrade pip
fi

# ── Step 6: Clone Repository ──────────────────────────────────────
REPO_URL="https://github.com/jackh0006/openvpn-wizard.git"
CLONE_DIR="/tmp/openvpn-wizard"

echo ""
echo "📥 Cloning repository..."
echo "   From: $REPO_URL"

if [[ -d "$CLONE_DIR" ]]; then
    echo "   ⚠️  Clone directory $CLONE_DIR already exists."
    read -r -p "   Remove and re-clone? (y/N): " response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        rm -rf "$CLONE_DIR"
        git clone "$REPO_URL" "$CLONE_DIR"
    else
        echo "   Using existing clone."
    fi
else
    git clone "$REPO_URL" "$CLONE_DIR"
fi

cd "$CLONE_DIR"

# ── Step 7: Install Package ───────────────────────────────────────
echo ""
echo "📥 Installing OpenVPN-Wizard..."
if cmd_exists vpn-installer; then
    echo "   ⚠️  vpn-installer command already found."
    read -r -p "   Reinstall anyway? (y/N): " response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        "$VENV_DIR/bin/pip" install -e .
    else
        echo "   Skipping package install."
    fi
else
    "$VENV_DIR/bin/pip" install -e .
fi

# ── Step 8: Create Command Wrapper ─────────────────────────────────
echo ""
echo "🔗 Creating command wrapper..."
# Find the venv site-packages directory dynamically
VENV_SITE_PACKAGES=$("$VENV_DIR/bin/python" -c "import site; print(site.getsitepackages()[0])")
cat > /usr/local/bin/vpn-installer << WRAPPER_EOF
#!/usr/bin/env python3
import sys
sys.path.insert(0, '$VENV_SITE_PACKAGES')
sys.path.insert(0, '$CLONE_DIR')
from cli import app
app()
WRAPPER_EOF
chmod +x /usr/local/bin/vpn-installer
echo "   ✓ Created /usr/local/bin/vpn-installer"

# ── Step 9: Verify ────────────────────────────────────────────────
echo ""
echo "🔍 Verifying installation..."
if cmd_exists vpn-installer; then
    echo "   ✓ vpn-installer command available"
    vpn-installer --version 2>&1 || echo "   ⚠️  Version check failed (may need --help instead)"
else
    echo "   ❌ vpn-installer command NOT found! Installation may have failed."
    exit 1
fi

# ── Done ──────────────────────────────────────────────────────────
echo ""
echo "✅ Installation complete!"
echo ""
echo "Run the installer:"
echo "  sudo vpn-installer install"
echo ""
echo "Or run management:"
echo "  sudo vpn-installer manage"